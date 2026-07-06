from app.services.validacao_service import validar_cnpj, validar_chave_acesso


def test_cnpj_valido():
    assert validar_cnpj('11.222.333/0001-81')


def test_cnpj_valido_somente_digitos():
    assert validar_cnpj('11222333000181')


def test_cnpj_invalido_tamanho():
    assert not validar_cnpj('11.222.333/0001-8')


def test_cnpj_invalido_digitos_iguais():
    assert not validar_cnpj('11111111111111')


def test_cnpj_vazio():
    assert not validar_cnpj('')


def test_cnpj_none():
    assert not validar_cnpj(None)


def test_cnpj_invalido():
    assert not validar_cnpj('11.222.333/0001-99')


def test_chave_valida():
    assert validar_chave_acesso('35200622525244000195550010000000011000000019')


def test_chave_valida_com_formatacao():
    assert validar_chave_acesso('3520 0622 5252 4400 1955 5001 0000 0001 1010 0000 0019')


def test_chave_tamanho_invalido():
    assert not validar_chave_acesso('1234567890')


def test_chave_com_letras():
    assert not validar_chave_acesso('35200622525244000195550010000000011000000abc')


def test_chave_vazia():
    assert not validar_chave_acesso('')
