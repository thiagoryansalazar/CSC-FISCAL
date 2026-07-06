import tempfile
import os
from app.extractors.xml_extractor import processar_xml, extrair_texto_xml

XML_VALIDO = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe35200622525244000195550010000000011000000019">
      <ide>
        <cUF>35</cUF>
        <nNF>1</nNF>
        <serie>1</serie>
        <dhEmi>2024-01-15T10:30:00-03:00</dhEmi>
      </ide>
      <emit>
        <CNPJ>11.222.333/0001-81</CNPJ>
        <xNome>FORNECEDOR EXEMPLO LTDA</xNome>
      </emit>
      <dest>
        <CNPJ>99.888.777/0001-66</CNPJ>
        <xNome>COMPRADOR LTDA</xNome>
      </dest>
      <det n="1">
        <prod>
          <cProd>001</cProd>
          <xProd>PRODUTO A</xProd>
          <NCM>8471.30.12</NCM>
          <CFOP>5101</CFOP>
          <qCom>10.0000</qCom>
          <vUnCom>15.5000</vUnCom>
          <vProd>155.00</vProd>
        </prod>
      </det>
      <det n="2">
        <prod>
          <cProd>002</cProd>
          <xProd>PRODUTO B</xProd>
          <NCM>8471.30.12</NCM>
          <CFOP>5101</CFOP>
          <qCom>5.0000</qCom>
          <vUnCom>30.0000</vUnCom>
          <vProd>150.00</vProd>
        </prod>
      </det>
      <total>
        <ICMSTot>
          <vNF>305.00</vNF>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>'''

XML_INVALIDO = '<root><foo>bar</foo>'


def _salvar_xml(conteudo):
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8')
    tmp.write(conteudo)
    tmp.close()
    return tmp.name


def test_processar_xml_valido():
    caminho = _salvar_xml(XML_VALIDO)
    try:
        resultado = processar_xml(caminho)
        assert 'erro' not in resultado
        assert resultado['numero'] == '1'
        assert resultado['serie'] == '1'
        assert resultado['cnpj_emitente'] == '11222333000181'
        assert resultado['nome_fornecedor'] == 'FORNECEDOR EXEMPLO LTDA'
        assert resultado['chave_acesso'] == '35200622525244000195550010000000011000000019'
        assert resultado['valor_total'] == 305.0
        assert resultado['qtd_itens'] == 2
        assert len(resultado['itens']) == 2
        assert resultado['itens'][0]['codigo'] == '001'
        assert resultado['itens'][0]['descricao'] == 'PRODUTO A'
        assert resultado['itens'][0]['quantidade'] == 10.0
        assert resultado['itens'][0]['valor_unitario'] == 15.5
        assert resultado['itens'][0]['valor_total'] == 155.0
        assert resultado['itens'][1]['codigo'] == '002'
        assert resultado['itens'][1]['descricao'] == 'PRODUTO B'
    finally:
        os.unlink(caminho)


def test_processar_xml_invalido():
    caminho = _salvar_xml(XML_INVALIDO)
    try:
        resultado = processar_xml(caminho)
        assert 'erro' in resultado
    finally:
        os.unlink(caminho)


def test_extrair_texto_xml():
    caminho = _salvar_xml(XML_VALIDO)
    try:
        resultado = extrair_texto_xml(caminho)
        assert 'texto' in resultado
        assert '35200622525244000195550010000000011000000019' in resultado['texto']
    finally:
        os.unlink(caminho)


def test_extrair_texto_xml_inexistente():
    resultado = extrair_texto_xml('/tmp/nao_existe.xml')
    assert 'erro' in resultado
