from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.nota_service import NotaService
from app.services.comparador_service import ComparadorService

router = APIRouter(prefix='/api/dashboard', tags=['dashboard'])

@router.get('')
async def dashboard(db: AsyncSession = Depends(get_db)):
    nota_svc = NotaService(db)
    dados = await nota_svc.obter_dashboard()
    comp_svc = ComparadorService(db)
    comp_resumo = await comp_svc.resumo()
    dados['extracoes'] = comp_resumo
    return dados

@router.get('/pendencias')
async def pendencias(db: AsyncSession = Depends(get_db)):
    nota_svc = NotaService(db)
    return await nota_svc.listar_pendencias()

@router.get('/divergencias')
async def divergencias(db: AsyncSession = Depends(get_db)):
    comp_svc = ComparadorService(db)
    return await comp_svc.listar_divergencias()

@router.get('/relatorio')
async def relatorio(db: AsyncSession = Depends(get_db)):
    nota_svc = NotaService(db)
    dados = await nota_svc.obter_dashboard()
    return dados
