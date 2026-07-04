import os
import shutil
import json
from fastapi import APIRouter, UploadFile, File, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import STORAGE_INPUT, STORAGE_XML
from app.services.nota_service import NotaService
from app.services.extracao_service import ExtracaoService
from app.services.rag_service import RagService
from app.llm.cliente_ollama import ClienteOllama
from app.schemas.nota_schema import NotaFiscalCreate, NotaFiscalResponse
from app.config import LLM_ENABLED, OLLAMA_URL, OLLAMA_MODEL

router = APIRouter(prefix='/api/upload', tags=['upload'])

@router.post('')
async def upload_arquivo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    os.makedirs(STORAGE_INPUT, exist_ok=True)
    os.makedirs(STORAGE_XML, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower()
    nome_base = os.path.splitext(file.filename)[0]

    if ext == '.xml':
        destino = os.path.join(STORAGE_XML, file.filename)
    else:
        destino = os.path.join(STORAGE_INPUT, file.filename)

    with open(destino, 'wb') as f:
        shutil.copyfileobj(file.file, f)

    nota_svc = NotaService(db)
    dados_iniciais = NotaFiscalCreate(
        origem='xml' if ext == '.xml' else 'pdf',
        caminho_xml=destino if ext == '.xml' else None,
        caminho_pdf=destino if ext == '.pdf' else None,
        tipo_documento='NF-e',
    )
    nota = await nota_svc.criar(dados_iniciais)

    llm = ClienteOllama(OLLAMA_URL, OLLAMA_MODEL) if LLM_ENABLED else None
    extracao_svc = ExtracaoService(db)
    extracao = await extracao_svc.extrair(nota.id, destino, file.filename, llm)

    if extracao.dados_sistema:
        dados_sistema = json.loads(extracao.dados_sistema)
        dados_sistema['caminho_xml'] = destino if ext == '.xml' else None
        dados_sistema['caminho_pdf'] = destino if ext == '.pdf' else None
        update = NotaFiscalCreate(
            chave_acesso=dados_sistema.get('chave_acesso'),
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

    try:
        rag = RagService(db, llm)
        await rag.indexar_extracao(nota.id)
    except Exception:
        pass

    await db.commit()
    return {
        'nota': NotaFiscalResponse.model_validate(nota),
        'extracao_id': extracao.id,
        'arquivo': file.filename,
    }
