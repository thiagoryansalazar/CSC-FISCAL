from sqlalchemy import Column, Integer, String, Float, Text, DateTime, func
from app.database import Base

class NotaFiscal(Base):
    __tablename__ = 'notas_fiscais'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chave_acesso = Column(String(44), unique=True, nullable=True)
    numero = Column(String(20), nullable=True)
    serie = Column(String(10), nullable=True)
    cnpj_emitente = Column(String(18), nullable=True)
    cpf_emitente = Column(String(14), nullable=True)
    nome_fornecedor = Column(String(255), nullable=True)
    data_emissao = Column(DateTime, nullable=True)
    valor_total = Column(Float, default=0)
    tipo_documento = Column(String(20), default='NF-e')
    qtd_itens = Column(Integer, default=0)
    origem = Column(String(20), nullable=True)
    caminho_xml = Column(String(500), nullable=True)
    caminho_pdf = Column(String(500), nullable=True)
    caminho_xml_gerado = Column(String(500), nullable=True)
    status = Column(String(20), default='ENTRADA')
    duplicada_de = Column(Integer, nullable=True)
    observacoes = Column(Text, nullable=True)
    data_entrada = Column(DateTime, server_default=func.now())
