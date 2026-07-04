from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database import Base

class ItemNota(Base):
    __tablename__ = 'itens_nota'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_id = Column(Integer, ForeignKey('notas_fiscais.id', ondelete='CASCADE'), nullable=False)
    codigo = Column(String(50), nullable=True)
    descricao = Column(String(500), nullable=True)
    ncm = Column(String(10), nullable=True)
    cfop = Column(String(10), nullable=True)
    quantidade = Column(Float, default=0)
    valor_unitario = Column(Float, default=0)
    valor_total = Column(Float, default=0)
