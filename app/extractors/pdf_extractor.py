import re
from typing import Optional
import pdfplumber
from app.extractors import normalizar_valor, normalizar_data, extrair_chave_do_texto

def processar_pdf(caminho: str) -> dict:
    try:
        with pdfplumber.open(caminho) as pdf:
            texto_completo = ""
            for page in pdf.pages:
                texto_completo += (page.extract_text() or "") + "\n"
    except Exception as e:
        return {'erro': f'Erro ao ler PDF: {e}'}

    if not texto_completo.strip():
        return {'erro': 'Nenhum texto extraido do PDF'}

    linhas = texto_completo.split('\n')
    dados_base = _extrair_dados_basicos(linhas, texto_completo)
    dados_base['itens'] = _extrair_itens(linhas)
    dados_base['texto_extraido'] = texto_completo
    dados_base['origem'] = 'pdf'
    return dados_base

def _extrair_dados_basicos(linhas: list, texto: str) -> dict:
    chave = extrair_chave_do_texto(texto)

    numero = ''
    serie = ''
    cnpj = ''
    nome = ''
    data_emissao = ''
    valor_total = 0.0

    for linha in linhas:
        ls = linha.strip()

        m = re.search(r'NF[ea]\s*[Nn][[:ord:]]?\s*[.:]?\s*(\d+)', ls)
        if m and not numero:
            numero = m.group(1)

        m = re.search(r'S[ée]rie\s*[.:]?\s*(\d+)', ls)
        if m and not serie:
            serie = m.group(1)

        m = re.search(r'\b(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\b', ls)
        if m and not cnpj:
            cnpj = re.sub(r'\D', '', m.group(1))

        m = re.search(r'(?:DANFE|CHAVE)\s*(?:DE\s*)?ACESSO[:\s]*([\d\s.\/-]{44,})', ls, re.IGNORECASE)
        if m and not chave:
            c = re.sub(r'\D', '', m.group(1))
            if len(c) >= 44:
                chave = c[:44]

    if not cnpj:
        m = re.search(r'\b(\d{14})\b', texto)
        if m:
            cnpj = m.group(1)

    return {
        'chave_acesso': chave,
        'numero': numero,
        'serie': serie,
        'cnpj_emitente': cnpj,
        'cpf_emitente': None,
        'nome_fornecedor': nome,
        'data_emissao': data_emissao,
        'valor_total': valor_total,
        'tipo_documento': 'NF-e',
        'origem': 'pdf',
    }

def _extrair_itens(linhas: list) -> list:
    itens = []
    dentro_tabela = False

    for i, linha in enumerate(linhas):
        ls = linha.strip()

        if re.search(r'Código|Produto|Descrição|DESCRI', ls, re.IGNORECASE):
            dentro_tabela = True
            continue

        if dentro_tabela:
            if re.search(r'^Trib\b|Total|Frete|Seguro|Desp|ICMS|BASE|VALOR TOTAL', ls, re.IGNORECASE):
                dentro_tabela = False
                continue

            partes = re.split(r'\s{2,}', ls)
            if len(partes) >= 2:
                codigo = ''
                descricao = ''
                qtd = 0.0
                valor_unit = 0.0
                valor_total_item = 0.0

                partes_flat = [p for p in partes if p.strip()]

                if len(partes_flat) >= 3:
                    codigo = partes_flat[0].strip()
                    descricao = partes_flat[1].strip()
                    qtd_match = re.search(r'([\d.,]+)', partes_flat[-2] if len(partes_flat) >= 4 else '')
                    if not qtd_match:
                        qtd_match = re.search(r'([\d.,]+)', partes_flat[-3] if len(partes_flat) >= 4 else '')
                    valor_match = re.search(r'([\d.,]+)', partes_flat[-1] if len(partes_flat) >= 3 else '')
                    if qtd_match:
                        qtd = normalizar_valor(qtd_match.group(1))
                    if valor_match:
                        valor_total_item = normalizar_valor(valor_match.group(1))

                if descricao:
                    itens.append({
                        'codigo': codigo,
                        'descricao': descricao,
                        'ncm': '',
                        'cfop': '',
                        'quantidade': qtd,
                        'valor_unitario': valor_unit,
                        'valor_total': valor_total_item,
                    })

    return itens

def extrair_texto_pdf(caminho: str) -> dict:
    try:
        with pdfplumber.open(caminho) as pdf:
            texto = ""
            for page in pdf.pages:
                texto += (page.extract_text() or "") + "\n"
        return {'texto': texto}
    except Exception as e:
        return {'erro': str(e)}
