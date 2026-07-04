from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.nota_service import NotaService
from app.schemas.nota_schema import HistoricoResponse

router = APIRouter(prefix='/api/historico', tags=['historico'])

@router.get('/{nota_id}')
async def listar_historico(nota_id: int, db: AsyncSession = Depends(get_db)):
    svc = NotaService(db)
    historico = await svc.obter_historico(nota_id)
    return [HistoricoResponse.model_validate(h) for h in historico]
