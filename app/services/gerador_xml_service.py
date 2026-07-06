import os
import re
from datetime import datetime
from lxml import etree
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import STORAGE_XML
from app.models.nota_fiscal import NotaFiscal
from app.models.item_nota import ItemNota

NS = 'http://www.portalfiscal.inf.br/nfe'
NSMAP = {None: NS}


def _gerar_chave(nota: NotaFiscal) -> str:
    chave = re.sub(r'\D', '', nota.chave_acesso or '')
    if len(chave) == 44:
        return chave
    cnpj = re.sub(r'\D', '', nota.cnpj_emitente or '').zfill(14)[:14]
    uf = cnpj[:2]
    mes = ''
    if nota.data_emissao:
        mes = nota.data_emissao.strftime('%m')
    ano = ''
    if nota.data_emissao:
        ano = nota.data_emissao.strftime('%y')
    num = (nota.numero or '').zfill(9)[:9]
    serie = (nota.serie or '').zfill(3)[:3]
    tp_emis = '1'
    cNF = str(hash(f'{cnpj}{num}{serie}'))[-8:].zfill(8)
    base = f'{uf}{ano}{mes}{cnpj}{serie}{num}{tp_emis}{cNF}'
    if len(base) < 43:
        base = base.ljust(43, '0')
    dv = 0
    pesos = [4,3,2,9,8,7,6,5,4,3,2,9,8,7,6,5,4,3,2,9,8,7,6,5,4,3,2,9,8,7,6,5,4,3,2,9,8,7,6,5,4,3]
    s = sum(int(base[i]) * pesos[i] for i in range(len(base)))
    dv = 11 - s % 11
    dv = 0 if dv > 9 else dv
    return f'{base}{dv}'


def _formatar_data(dt) -> str:
    if not dt:
        return datetime.now().strftime('%Y-%m-%dT%H:%M:%S-03:00')
    if isinstance(dt, str):
        return dt
    return dt.strftime('%Y-%m-%dT%H:%M:%S-03:00')


def _criar_elemento(tag: str, texto: str = None):
    el = etree.Element(f'{{{NS}}}{tag}', nsmap=NSMAP)
    if texto is not None:
        el.text = str(texto)
    return el


async def gerar_xml(nota_id: int, db: AsyncSession) -> str:
    r = await db.execute(select(NotaFiscal).where(NotaFiscal.id == nota_id))
    nota = r.scalar_one_or_none()
    if not nota:
        raise ValueError(f'Nota #{nota_id} nao encontrada')

    r2 = await db.execute(
        select(ItemNota).where(ItemNota.nota_id == nota_id)
    )
    itens = r2.scalars().all()

    chave = _gerar_chave(nota)

    nfeProc = _criar_elemento('nfeProc')
    versao = _criar_elemento('versao')
    versao.text = '4.00'
    nfeProc.append(versao)

    NFe = _criar_elemento('NFe')
    infNFe = _criar_elemento('infNFe')
    infNFe.set('Id', f'NFe{chave}')
    infNFe.set('versao', '4.00')

    ide = _criar_elemento('ide')
    ide.append(_criar_elemento('cUF', chave[:2]))
    ide.append(_criar_elemento('cNF', chave[-8:]))
    ide.append(_criar_elemento('natOp', 'VENDA'))
    ide.append(_criar_elemento('mod', '55'))
    ide.append(_criar_elemento('serie', nota.serie or '1'))
    ide.append(_criar_elemento('nNF', nota.numero or '1'))
    ide.append(_criar_elemento('dhEmi', _formatar_data(nota.data_emissao)))
    ide.append(_criar_elemento('tpNF', '1'))
    ide.append(_criar_elemento('idDest', '1'))
    ide.append(_criar_elemento('cMunFG', '3550308'))
    ide.append(_criar_elemento('tpImp', '1'))
    ide.append(_criar_elemento('tpEmis', '1'))
    ide.append(_criar_elemento('cDV', chave[-1]))
    ide.append(_criar_elemento('tpAmb', '2'))
    ide.append(_criar_elemento('finNFe', '1'))
    ide.append(_criar_elemento('indFinal', '1'))
    ide.append(_criar_elemento('indPres', '1'))
    ide.append(_criar_elemento('procEmi', '0'))
    ide.append(_criar_elemento('verProc', 'CSC Fiscal 1.0'))
    infNFe.append(ide)

    emit = _criar_elemento('emit')
    emit.append(_criar_elemento('CNPJ', re.sub(r'\D', '', (nota.cnpj_emitente or '')).zfill(14)[:14]))
    emit.append(_criar_elemento('xNome', (nota.nome_fornecedor or 'FORNECEDOR')[:60]))
    emit.append(_criar_elemento('xFant', (nota.nome_fornecedor or 'FORNECEDOR')[:60]))
    enderEmit = _criar_elemento('enderEmit')
    enderEmit.append(_criar_elemento('xLgr', 'END'))
    enderEmit.append(_criar_elemento('nro', 'SN'))
    enderEmit.append(_criar_elemento('xBairro', 'BAIRRO'))
    enderEmit.append(_criar_elemento('cMun', '3550308'))
    enderEmit.append(_criar_elemento('xMun', 'MUNICIPIO'))
    enderEmit.append(_criar_elemento('UF', chave[:2]))
    enderEmit.append(_criar_elemento('CEP', '00000000'))
    enderEmit.append(_criar_elemento('cPais', '1058'))
    enderEmit.append(_criar_elemento('xPais', 'BRASIL'))
    emit.append(enderEmit)
    emit.append(_criar_elemento('IE', '0000000000000'))
    infNFe.append(emit)

    dest = _criar_elemento('dest')
    dest.append(_criar_elemento('CNPJ', '00000000000000'))
    dest.append(_criar_elemento('xNome', 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL'))
    enderDest = _criar_elemento('enderDest')
    enderDest.append(_criar_elemento('xLgr', 'END'))
    enderDest.append(_criar_elemento('nro', 'SN'))
    enderDest.append(_criar_elemento('xBairro', 'BAIRRO'))
    enderDest.append(_criar_elemento('cMun', '3550308'))
    enderDest.append(_criar_elemento('xMun', 'MUNICIPIO'))
    enderDest.append(_criar_elemento('UF', 'SP'))
    enderDest.append(_criar_elemento('CEP', '00000000'))
    enderDest.append(_criar_elemento('cPais', '1058'))
    enderDest.append(_criar_elemento('xPais', 'BRASIL'))
    dest.append(enderDest)
    dest.append(_criar_elemento('indIEDest', '9'))
    infNFe.append(dest)

    for i, item in enumerate(itens, 1):
        det = _criar_elemento('det')
        det.set('nItem', str(i))
        prod = _criar_elemento('prod')
        prod.append(_criar_elemento('cProd', item.codigo or str(i)))
        prod.append(_criar_elemento('cEAN', 'SEM GTIN'))
        prod.append(_criar_elemento('xProd', (item.descricao or f'ITEM {i}')[:120]))
        prod.append(_criar_elemento('NCM', (item.ncm or '84713000')[:8]))
        prod.append(_criar_elemento('CFOP', (item.cfop or '5102')[:4]))
        prod.append(_criar_elemento('uCom', 'UN'))
        prod.append(_criar_elemento('qCom', f'{item.quantidade:.4f}'))
        prod.append(_criar_elemento('vUnCom', f'{item.valor_unitario:.2f}'))
        prod.append(_criar_elemento('vProd', f'{item.valor_total:.2f}'))
        prod.append(_criar_elemento('cEANTrib', 'SEM GTIN'))
        prod.append(_criar_elemento('uTrib', 'UN'))
        prod.append(_criar_elemento('qTrib', f'{item.quantidade:.4f}'))
        prod.append(_criar_elemento('vUnTrib', f'{item.valor_unitario:.2f}'))
        prod.append(_criar_elemento('indTot', '1'))
        det.append(prod)
        det.append(_criar_elemento('imposto'))
        infNFe.append(det)

    total = _criar_elemento('total')
    ICMSTot = _criar_elemento('ICMSTot')
    vNF = nota.valor_total or 0
    ICMSTot.append(_criar_elemento('vBC', '0.00'))
    ICMSTot.append(_criar_elemento('vICMS', '0.00'))
    ICMSTot.append(_criar_elemento('vICMSDeson', '0.00'))
    ICMSTot.append(_criar_elemento('vFCP', '0.00'))
    ICMSTot.append(_criar_elemento('vBCST', '0.00'))
    ICMSTot.append(_criar_elemento('vST', '0.00'))
    ICMSTot.append(_criar_elemento('vFCPST', '0.00'))
    ICMSTot.append(_criar_elemento('vFCPSTRet', '0.00'))
    ICMSTot.append(_criar_elemento('vProd', f'{vNF:.2f}'))
    ICMSTot.append(_criar_elemento('vFrete', '0.00'))
    ICMSTot.append(_criar_elemento('vSeg', '0.00'))
    ICMSTot.append(_criar_elemento('vDesc', '0.00'))
    ICMSTot.append(_criar_elemento('vII', '0.00'))
    ICMSTot.append(_criar_elemento('vIPI', '0.00'))
    ICMSTot.append(_criar_elemento('vIPIDevol', '0.00'))
    ICMSTot.append(_criar_elemento('vPIS', '0.00'))
    ICMSTot.append(_criar_elemento('vCOFINS', '0.00'))
    ICMSTot.append(_criar_elemento('vOutro', '0.00'))
    ICMSTot.append(_criar_elemento('vNF', f'{vNF:.2f}'))
    ICMSTot.append(_criar_elemento('vTotTrib', '0.00'))
    total.append(ICMSTot)
    infNFe.append(total)

    transp = _criar_elemento('transp')
    transp.append(_criar_elemento('modFrete', '9'))
    infNFe.append(transp)

    pag = _criar_elemento('pag')
    detPag = _criar_elemento('detPag')
    detPag.append(_criar_elemento('tPag', '01'))
    detPag.append(_criar_elemento('vPag', f'{vNF:.2f}'))
    pag.append(detPag)
    infNFe.append(pag)

    infAdic = _criar_elemento('infAdic')
    infAdic.append(_criar_elemento('infCpl', 'DOCUMENTO EMITIDO COM BASE NOS DADOS EXTRAIDOS - SEM VALOR FISCAL'))
    infNFe.append(infAdic)

    NFe.append(infNFe)
    nfeProc.append(NFe)

    xml_str = etree.tostring(nfeProc, pretty_print=True, xml_declaration=True, encoding='UTF-8')

    os.makedirs(STORAGE_XML, exist_ok=True)
    nome_arquivo = f'gerado_{nota_id}_{chave}.xml'
    caminho = os.path.join(STORAGE_XML, nome_arquivo)
    with open(caminho, 'wb') as f:
        f.write(xml_str)

    nota.caminho_xml_gerado = caminho
    await db.flush()

    return caminho
