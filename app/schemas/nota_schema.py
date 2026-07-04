from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class NotaFiscalCreate(BaseModel):
    chave_acesso: Optional[str] = None
    numero: Optional[str] = None
    serie: Optional[str] = None
    cnpj_emitente: Optional[str] = None
    cpf_emitente: Optional[str] = None
    nome_fornecedor: Optional[str] = None
    data_emissao: Optional[str] = None
    valor_total: float = 0
    tipo_documento: str = 'NF-e'
    qtd_itens: int = 0
    origem: Optional[str] = None
    caminho_xml: Optional[str] = None
    caminho_pdf: Optional[str] = None
    observacoes: Optional[str] = None

class NotaFiscalUpdate(BaseModel):
    nome_fornecedor: Optional[str] = None
    status: Optional[str] = None
    numero: Optional[str] = None
    serie: Optional[str] = None
    cnpj_emitente: Optional[str] = None
    cpf_emitente: Optional[str] = None
    data_emissao: Optional[str] = None
    valor_total: Optional[float] = None
    tipo_documento: Optional[str] = None
    qtd_itens: Optional[int] = None
    observacoes: Optional[str] = None

class NotaFiscalResponse(BaseModel):
    id: int
    chave_acesso: Optional[str] = None
    numero: Optional[str] = None
    serie: Optional[str] = None
    cnpj_emitente: Optional[str] = None
    cpf_emitente: Optional[str] = None
    nome_fornecedor: Optional[str] = None
    data_emissao: Optional[str] = None
    valor_total: float = 0
    tipo_documento: str = 'NF-e'
    qtd_itens: int = 0
    origem: Optional[str] = None
    caminho_xml: Optional[str] = None
    caminho_pdf: Optional[str] = None
    caminho_xml_gerado: Optional[str] = None
    status: str = 'NAO_PROCESSADA'
    observacoes: Optional[str] = None
    data_entrada: Optional[str] = None

    class Config:
        from_attributes = True

class ItemNotaResponse(BaseModel):
    id: int
    nota_id: int
    codigo: Optional[str] = None
    descricao: Optional[str] = None
    ncm: Optional[str] = None
    cfop: Optional[str] = None
    quantidade: float = 0
    valor_unitario: float = 0
    valor_total: float = 0

    class Config:
        from_attributes = True

class HistoricoResponse(BaseModel):
    id: int
    nota_id: int
    acao: str
    descricao: Optional[str] = None
    data_hora: Optional[str] = None

    class Config:
        from_attributes = True
