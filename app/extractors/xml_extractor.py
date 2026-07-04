import hashlib
from typing import Optional
from lxml import etree
from app.extractors import normalizar_valor, normalizar_data, extrair_chave_do_texto

def processar_xml(caminho: str) -> dict:
    try:
        tree = etree.parse(caminho)
        root = tree.getroot()
    except Exception as e:
        return {'erro': f'XML invalido: {e}'}

    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    infNFe = root.find('.//nfe:infNFe', ns)
    if infNFe is None:
        infNFe = root.find('.//infNFe')
    if infNFe is None:
        return {'erro': 'Estrutura NF-e nao encontrada'}

    chave = ''
    id_attr = infNFe.get('Id', '')
    if id_attr:
        chave = re.sub(r'[^0-9]', '', id_attr.replace('NFe', ''))
    chave = chave if len(chave) == 44 else ''

    emit = infNFe.find('emit')

    dados = {
        'chave_acesso': chave or None,
        'numero': extrair_texto(infNFe, './/ide/nNF'),
        'serie': extrair_texto(infNFe, './/ide/serie'),
        'cnpj_emitente': limpar_digitos(extrair_texto(emit, 'CNPJ')),
        'cpf_emitente': limpar_digitos(extrair_texto(emit, 'CPF')),
        'nome_fornecedor': extrair_texto(emit, 'xNome'),
        'data_emissao': normalizar_data(extrair_texto(infNFe, './/ide/dhEmi') or extrair_texto(infNFe, './/ide/dEmi') or ''),
        'valor_total': normalizar_valor(infNFe.findtext('.//total/ICMSTot/vNF', '0')),
        'tipo_documento': 'NF-e',
        'origem': 'xml',
        'itens': [],
    }

    for det in infNFe.findall('.//det'):
        prod = det.find('prod')
        if prod is not None:
            dados['itens'].append({
                'codigo': extrair_texto(prod, 'cProd') or '',
                'descricao': extrair_texto(prod, 'xProd') or '',
                'ncm': extrair_texto(prod, 'NCM') or '',
                'cfop': extrair_texto(prod, 'CFOP') or '',
                'quantidade': float(extrair_texto(prod, 'qCom') or 0),
                'valor_unitario': float(extrair_texto(prod, 'vUnCom') or 0),
                'valor_total': float(extrair_texto(prod, 'vProd') or 0),
            })
    dados['qtd_itens'] = len(dados['itens'])

    return dados

def extrair_texto_xml(caminho: str) -> dict:
    try:
        with open(caminho, 'rb') as f:
            texto = f.read().decode('utf-8')
        return {'texto': texto}
    except Exception as e:
        return {'erro': str(e)}

def extrair_texto(element, path: str) -> str:
    if element is None:
        return ''
    el = element.find(path)
    return (el.text or '').strip() if el is not None else ''

def limpar_digitos(valor: str) -> str:
    import re
    return re.sub(r'\D', '', valor) if valor else ''

import re
