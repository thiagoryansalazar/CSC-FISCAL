import pytest
from app.extractors import normalizar_valor, normalizar_data, extrair_chave_do_texto
from app.models.nota_fiscal import NotaFiscal
from app.models.item_nota import ItemNota
from app.models.historico_nota import HistoricoNota
from app.models.extracao_nota import ExtracaoNota


@pytest.fixture
def xml_nfe_valido():
    return '''<?xml version="1.0" encoding="UTF-8"?>
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
