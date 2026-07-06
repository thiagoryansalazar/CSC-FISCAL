import re


def validar_cnpj(cnpj: str) -> bool:
    if not cnpj:
        return False
    cnpj = re.sub(r'\D', '', cnpj)
    if len(cnpj) != 14:
        return False
    if cnpj == cnpj[0] * 14:
        return False
    try:
        int(cnpj)
    except ValueError:
        return False

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    s1 = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    d1 = 11 - s1 % 11
    d1 = 0 if d1 > 9 else d1
    if int(cnpj[12]) != d1:
        return False

    s2 = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    d2 = 11 - s2 % 11
    d2 = 0 if d2 > 9 else d2
    if int(cnpj[13]) != d2:
        return False

    return True


def validar_chave_acesso(chave: str) -> bool:
    if not chave:
        return False
    chave = re.sub(r'\D', '', chave)
    if len(chave) != 44:
        return False
    try:
        int(chave)
    except ValueError:
        return False
    return True
