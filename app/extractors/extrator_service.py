import os
import hashlib
from app.extractors.xml_extractor import processar_xml, extrair_texto_xml
from app.extractors.pdf_extractor import processar_pdf, extrair_texto_pdf
from app.extractors.xlsx_extractor import processar_xlsx, extrair_texto_xlsx

def detectar_tipo_arquivo(caminho: str) -> str:
    ext = os.path.splitext(caminho)[1].lower()
    mapa = {'.xml': 'xml', '.pdf': 'pdf', '.xlsx': 'xlsx', '.xls': 'xlsx'}
    return mapa.get(ext, 'desconhecido')

def processar_arquivo(caminho: str) -> dict:
    tipo = detectar_tipo_arquivo(caminho)
    extratores = {
        'xml': processar_xml,
        'pdf': processar_pdf,
        'xlsx': processar_xlsx,
    }
    extrator = extratores.get(tipo)
    if not extrator:
        return {'erro': f'Tipo de arquivo nao suportado: {tipo}'}
    return extrator(caminho)

def extrair_texto_puro(caminho: str) -> dict:
    tipo = detectar_tipo_arquivo(caminho)
    extratores = {
        'xml': extrair_texto_xml,
        'pdf': extrair_texto_pdf,
        'xlsx': extrair_texto_xlsx,
    }
    extrator = extratores.get(tipo)
    if not extrator:
        return {'erro': f'Tipo nao suportado: {tipo}'}
    return extrator(caminho)

def calcular_hash(caminho: str) -> str:
    h = hashlib.sha256()
    with open(caminho, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()
