from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base

class HistoricoNota(Base):
    __tablename__ = 'historico_nota'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_id = Column(Integer, ForeignKey('notas_fiscais.id', ondelete='CASCADE'), nullable=False)
    acao = Column(String(30), nullable=False, default='recebida')
    descricao = Column(Text, nullable=True)
    data_hora = Column(DateTime, server_default=func.now())
