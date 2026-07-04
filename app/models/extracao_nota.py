from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base

class ExtracaoNota(Base):
    __tablename__ = 'extracoes_nota'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_id = Column(Integer, ForeignKey('notas_fiscais.id', ondelete='CASCADE'), nullable=False)
    arquivo_nome = Column(String(255), nullable=True)
    arquivo_tipo = Column(String(10), nullable=True)
    arquivo_sha256 = Column(String(64), nullable=True)
    arquivo_tamanho = Column(Integer, default=0)
    texto_extraido = Column(Text, nullable=True)
    documento_interpretavel = Column(Text, nullable=True)
    dados_sistema = Column(Text, nullable=True)
    dados_llm = Column(Text, nullable=True)
    dados_consolidados = Column(Text, nullable=True)
    confianca = Column(Text, nullable=True)
    divergencias = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)
    llm_status = Column(String(20), nullable=True)
    criado_em = Column(DateTime, server_default=func.now())
