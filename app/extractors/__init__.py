import hashlib
from typing import Optional

def extrair_chave_do_texto(texto: str) -> Optional[str]:
    import re
    sem_espacos = re.sub(r'[\s.\/\-]', '', texto)
    m = re.search(r'(?:NFe)?(\d{44})', sem_espacos)
    if m:
        return m.group(1)
    m = re.search(r'CHAVE\s*(?:DE\s*)?ACESSO[:\s]*([^\n]+)', texto, re.IGNORECASE)
    if m:
        ch = re.sub(r'\D', '', m.group(1))
        if len(ch) == 44:
            return ch
    return None

def normalizar_valor(valor) -> float:
    if isinstance(valor, (int, float)):
        return float(valor)
    if not valor:
        return 0.0
    v = str(valor).replace('R$', '').replace(' ', '').strip()
    if ',' in v and '.' in v:
        v = v.replace('.', '')
        v = v.replace(',', '.')
    else:
        v = v.replace(',', '.')
    try:
        return float(v)
    except ValueError:
        return 0.0

def normalizar_data(valor: str) -> Optional[str]:
    from datetime import datetime
    if not valor or not valor.strip():
        return None
    valor = valor.strip()
    formatos = [
        ('%d/%m/%Y %H:%M:%S', False),
        ('%Y-%m-%dT%H:%M:%S', False),
        ('%Y-%m-%d %H:%M:%S', False),
        ('%d/%m/%Y', True),
        ('%Y-%m-%d', True),
    ]
    for fmt, is_date in formatos:
        try:
            dt = datetime.strptime(valor, fmt)
            return dt.strftime('%Y-%m-%dT%H:%M:%S' if not is_date else '%Y-%m-%d 00:00:00')
        except ValueError:
            continue
    return valor
