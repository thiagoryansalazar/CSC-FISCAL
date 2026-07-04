from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.llm.cliente_ollama import ClienteOllama
from app.services.rag_service import RagService
from app.config import LLM_ENABLED, OLLAMA_URL, OLLAMA_MODEL

router = APIRouter(prefix='/api/assistente', tags=['assistente'])

class PerguntaRequest(BaseModel):
    pergunta: str
    nota_id: Optional[int] = None

class PerguntaResponse(BaseModel):
    resposta: str
    docs: list = []
    contexto: Optional[str] = None

@router.post('/perguntar')
async def perguntar(req: PerguntaRequest, db: AsyncSession = Depends(get_db)):
    if not LLM_ENABLED:
        return PerguntaResponse(resposta='LLM nao configurado. Habilite LLM_ENABLED=true no .env')
    llm = ClienteOllama(OLLAMA_URL, OLLAMA_MODEL)
    rag = RagService(db, llm)
    resultado = await rag.perguntar(req.nota_id, req.pergunta)
    return PerguntaResponse(**resultado)

@router.get('/ping')
async def ping():
    llm = ClienteOllama(OLLAMA_URL, OLLAMA_MODEL)
    ok = await llm.ping()
    return {'ok': ok, 'url': OLLAMA_URL, 'modelo': OLLAMA_MODEL}
