import os
import shutil
import json
import logging
from fastapi import APIRouter, UploadFile, File, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import STORAGE_INPUT, STORAGE_XML
from app.services.nota_service import NotaService
from app.services.extracao_service import ExtracaoService
from app.services.rag_service import RagService
from app.services.validacao_service import validar_chave_acesso
from app.llm.cliente_ollama import ClienteOllama
from app.schemas.nota_schema import NotaFiscalCreate, NotaFiscalResponse
from app.models.nota_fiscal import NotaFiscal
from app.config import LLM_ENABLED, OLLAMA_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/upload', tags=['upload'])

async def _extrair_chave_previa(caminho: str, ext: str):
    if ext != '.xml':
        return None
    try:
        from lxml import etree
        import re
        tree = etree.parse(caminho)
        root = tree.getroot()
        for elem in root.iter():
            elem.tag = etree.QName(elem).localname
        infNFe = root.find('.//infNFe')
        if infNFe is not None:
            id_attr = infNFe.get('Id', '')
            if id_attr:
                ch = re.sub(r'[^0-9]', '', id_attr.replace('NFe', ''))
                if len(ch) == 44:
                    return ch
    except Exception:
        pass
    return None

async def _processar_upload(file: UploadFile, db: AsyncSession):
    ext = os.path.splitext(file.filename)[1].lower()
    logger.info('Processando upload: %s (tipo: %s)', file.filename, ext)

    if ext == '.xml':
        destino = os.path.join(STORAGE_XML, file.filename)
    else:
        destino = os.path.join(STORAGE_INPUT, file.filename)

    with open(destino, 'wb') as f:
        shutil.copyfileobj(file.file, f)

    nota_svc = NotaService(db)

    chave_previa = await _extrair_chave_previa(destino, ext)
    if chave_previa:
        existente = await nota_svc.buscar_por_chave(chave_previa)
        if existente:
            nota = NotaFiscal(
                chave_acesso=chave_previa,
                origem='xml' if ext == '.xml' else 'pdf',
                status='DUPLICADA',
                duplicada_de=existente.id,
                tipo_documento='NF-e',
                caminho_xml=destino if ext == '.xml' else None,
                caminho_pdf=destino if ext == '.pdf' else None,
            )
            db.add(nota)
            await db.flush()
            await nota_svc._adicionar_historico(nota.id, 'duplicada',
                f'Duplicata da nota #{existente.id} - chave {chave_previa}')
            logger.info('Nota #%d e duplicata da #%d', nota.id, existente.id)
            return nota, None

    dados_iniciais = NotaFiscalCreate(
        origem='xml' if ext == '.xml' else 'pdf',
        caminho_xml=destino if ext == '.xml' else None,
        caminho_pdf=destino if ext == '.pdf' else None,
        tipo_documento='NF-e',
    )
    nota = await nota_svc.criar(dados_iniciais)
    await nota_svc.atualizar_status(nota.id, 'EM_PROCESSAMENTO', 'Iniciando extracao')
    logger.info('Nota #%d criada a partir de %s', nota.id, file.filename)

    llm = ClienteOllama(OLLAMA_URL, OLLAMA_MODEL) if LLM_ENABLED else None
    extracao_svc = ExtracaoService(db)
    extracao = None
    try:
        extracao = await extracao_svc.extrair(nota.id, destino, file.filename, llm)
        logger.info('Extracao #%d concluida para nota #%d', extracao.id, nota.id)
    except Exception as e:
        logger.error('Erro na extracao da nota #%d: %s', nota.id, e)
        await nota_svc.atualizar_status(nota.id, 'ERRO', str(e)[:200])
        await db.flush()
        return nota, None

    if extracao and extracao.dados_sistema:
        dados_sistema = json.loads(extracao.dados_sistema)
        dados_sistema['caminho_xml'] = destino if ext == '.xml' else None
        dados_sistema['caminho_pdf'] = destino if ext == '.pdf' else None

        chave = dados_sistema.get('chave_acesso') or chave_previa
        if chave:
            existente = await nota_svc.buscar_por_chave(chave)
            if existente and existente.id != nota.id:
                await nota_svc.atualizar_status(nota.id, 'DUPLICADA',
                    f'Duplicata da nota #{existente.id}')
                nota.duplicada_de = existente.id
                if chave:
                    nota.chave_acesso = chave
                await db.flush()
                return nota, extracao

        update = NotaFiscalCreate(
            chave_acesso=chave,
            numero=dados_sistema.get('numero'),
            serie=dados_sistema.get('serie'),
            cnpj_emitente=dados_sistema.get('cnpj_emitente'),
            cpf_emitente=dados_sistema.get('cpf_emitente'),
            nome_fornecedor=dados_sistema.get('nome_fornecedor'),
            data_emissao=dados_sistema.get('data_emissao'),
            valor_total=dados_sistema.get('valor_total', 0),
            qtd_itens=dados_sistema.get('qtd_itens', 0),
            origem='xml' if ext == '.xml' else 'pdf',
        )
        await nota_svc.atualizar(nota.id, update)

        if dados_sistema.get('itens'):
            from app.models.item_nota import ItemNota
            for item_data in dados_sistema['itens']:
                item = ItemNota(nota_id=nota.id, **item_data)
                db.add(item)
            logger.info('%d itens adicionados para nota #%d', len(dados_sistema['itens']), nota.id)

        await nota_svc.atualizar_status(nota.id, 'PROCESSADA', 'Extracao concluida com sucesso')
    else:
        await nota_svc.atualizar_status(nota.id, 'ERRO', 'Falha na extracao dos dados')

    try:
        rag = RagService(db, llm)
        await rag.indexar_extracao(nota.id)
    except Exception as e:
        logger.warning('Falha ao indexar nota #%d no RAG: %s', nota.id, e)

    return nota, extracao

@router.post('')
async def upload_arquivo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    os.makedirs(STORAGE_INPUT, exist_ok=True)
    os.makedirs(STORAGE_XML, exist_ok=True)

    nota, extracao = await _processar_upload(file, db)
    await db.commit()

    return {
        'nota': NotaFiscalResponse.model_validate(nota),
        'extracao_id': extracao.id if extracao else None,
        'arquivo': file.filename,
    }


@router.post('/batch')
async def upload_multiplo(
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    os.makedirs(STORAGE_INPUT, exist_ok=True)
    os.makedirs(STORAGE_XML, exist_ok=True)

    resultados = []
    erros = []
    for file in files:
        try:
            nota, extracao = await _processar_upload(file, db)
            resultados.append({
                'arquivo': file.filename,
                'nota_id': nota.id,
                'status': 'ok',
            })
        except Exception as e:
            erros.append({
                'arquivo': file.filename,
                'erro': str(e),
            })

    await db.commit()
    return {
        'processados': len(resultados),
        'erros': len(erros),
        'resultados': resultados,
        'falhas': erros,
    }
