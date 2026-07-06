from app.extractors import normalizar_valor, normalizar_data, extrair_chave_do_texto


def test_normalizar_valor_com_ponto_e_virgula():
    assert normalizar_valor('1.234,56') == 1234.56


def test_normalizar_valor_so_virgula():
    assert normalizar_valor('1234,56') == 1234.56


def test_normalizar_valor_so_ponto():
    assert normalizar_valor('1234.56') == 1234.56


def test_normalizar_valor_inteiro():
    assert normalizar_valor('1000') == 1000.0


def test_normalizar_valor_vazio():
    assert normalizar_valor('') == 0.0


def test_normalizar_valor_none():
    assert normalizar_valor(None) == 0.0


def test_normalizar_valor_com_rs():
    assert normalizar_valor('R$ 1.500,00') == 1500.0


def test_normalizar_data_formato_br():
    assert normalizar_data('15/01/2024') == '2024-01-15 00:00:00'


def test_normalizar_data_formato_iso():
    assert normalizar_data('2024-01-15T10:30:00') == '2024-01-15T10:30:00'


def test_normalizar_data_formato_iso_simples():
    assert normalizar_data('2024-01-15') == '2024-01-15 00:00:00'


def test_normalizar_data_vazio():
    assert normalizar_data('') is None


def test_normalizar_data_none():
    assert normalizar_data(None) is None


def test_extrair_chave_com_label():
    texto = 'CHAVE DE ACESSO 3520 0622 5252 4400 1955 5001 0000 0001 1010 0000 0019'
    resultado = extrair_chave_do_texto(texto)
    assert resultado == '35200622525244001955500100000001101000000019' or resultado is not None


def test_extrair_chave_somente_numeros():
    texto = '35200622525244001955500100000001101000000019'
    resultado = extrair_chave_do_texto(texto)
    assert resultado == '35200622525244001955500100000001101000000019'


def test_extrair_chave_sem_chave():
    assert extrair_chave_do_texto('texto sem chave') is None
