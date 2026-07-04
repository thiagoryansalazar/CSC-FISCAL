from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.nota_service import NotaService
from app.schemas.nota_schema import NotaFiscalCreate, NotaFiscalUpdate, NotaFiscalResponse, ItemNotaResponse, HistoricoResponse
from app.models.item_nota import ItemNota

router = APIRouter(prefix='/api/notas', tags=['notas'])

@router.get('')
async def listar_notas(
    status: str = None,
    search: str = None,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    svc = NotaService(db)
    notas = await svc.listar(status, search, offset, limit)
    return [NotaFiscalResponse.model_validate(n) for n in notas]

@router.get('/{nota_id}')
async def obter_nota(nota_id: int, db: AsyncSession = Depends(get_db)):
    svc = NotaService(db)
    nota = await svc.obter(nota_id)
    if not nota:
        return {'erro': 'Nota nao encontrada'}
    r = await db.execute(select(ItemNota).where(ItemNota.nota_id == nota_id))
    itens = r.scalars().all()
    return {
        'nota': NotaFiscalResponse.model_validate(nota),
        'itens': [ItemNotaResponse.model_validate(i) for i in itens],
    }

@router.post('', status_code=201)
async def criar_nota(dados: NotaFiscalCreate, db: AsyncSession = Depends(get_db)):
    svc = NotaService(db)
    nota = await svc.criar(dados)
    return NotaFiscalResponse.model_validate(nota)

@router.put('/{nota_id}')
async def atualizar_nota(nota_id: int, dados: NotaFiscalUpdate, db: AsyncSession = Depends(get_db)):
    svc = NotaService(db)
    nota = await svc.atualizar(nota_id, dados)
    if not nota:
        return {'erro': 'Nota nao encontrada'}
    return NotaFiscalResponse.model_validate(nota)

@router.delete('/{nota_id}')
async def deletar_nota(nota_id: int, db: AsyncSession = Depends(get_db)):
    svc = NotaService(db)
    ok = await svc.deletar(nota_id)
    return {'ok': ok}

@router.get('/{nota_id}/historico')
async def historico_nota(nota_id: int, db: AsyncSession = Depends(get_db)):
    svc = NotaService(db)
    historico = await svc.obter_historico(nota_id)
    return [HistoricoResponse.model_validate(h) for h in historico]

@router.get('/{nota_id}/comparacao')
async def comparar_nota(nota_id: int, db: AsyncSession = Depends(get_db)):
    from app.services.comparador_service import ComparadorService
    svc = ComparadorService(db)
    return await svc.comparar(nota_id)
