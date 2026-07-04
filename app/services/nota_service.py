from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.nota_fiscal import NotaFiscal
from app.models.historico_nota import HistoricoNota
from app.schemas.nota_schema import NotaFiscalCreate, NotaFiscalUpdate

class NotaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def listar(self, status: str = None, search: str = None, offset: int = 0, limit: int = 50):
        q = select(NotaFiscal).order_by(NotaFiscal.data_entrada.desc())
        if status:
            q = q.where(NotaFiscal.status == status)
        if search:
            q = q.where(
                NotaFiscal.nome_fornecedor.ilike(f'%{search}%') |
                NotaFiscal.numero.ilike(f'%{search}%') |
                NotaFiscal.chave_acesso.ilike(f'%{search}%')
            )
        q = q.offset(offset).limit(limit)
        r = await self.db.execute(q)
        return r.scalars().all()

    async def obter(self, nota_id: int):
        r = await self.db.execute(select(NotaFiscal).where(NotaFiscal.id == nota_id))
        return r.scalar_one_or_none()

    async def criar(self, dados: NotaFiscalCreate) -> NotaFiscal:
        nota = NotaFiscal(**dados.model_dump(exclude_none=True))
        self.db.add(nota)
        await self.db.flush()
        await self._adicionar_historico(nota.id, 'recebida', 'Nota fiscal recebida')
        return nota

    async def atualizar(self, nota_id: int, dados: NotaFiscalUpdate):
        nota = await self.obter(nota_id)
        if not nota:
            return None
        old_status = nota.status
        for k, v in dados.model_dump(exclude_none=True).items():
            setattr(nota, k, v)
        await self.db.flush()
        if old_status != nota.status:
            await self._adicionar_historico(nota_id, 'status', f'Status alterado: {old_status} -> {nota.status}')
        return nota

    async def deletar(self, nota_id: int):
        nota = await self.obter(nota_id)
        if not nota:
            return False
        await self.db.execute(delete(HistoricoNota).where(HistoricoNota.nota_id == nota_id))
        await self.db.delete(nota)
        return True

    async def obter_dashboard(self):
        total = await self.db.scalar(select(func.count(NotaFiscal.id)))
        por_status = await self.db.execute(
            select(NotaFiscal.status, func.count(NotaFiscal.id).label('total'))
            .group_by(NotaFiscal.status)
        )
        valor = await self.db.scalar(select(func.coalesce(func.sum(NotaFiscal.valor_total), 0)))
        recentes = await self.db.execute(
            select(NotaFiscal).order_by(NotaFiscal.data_entrada.desc()).limit(5)
        )
        return {
            'total': total or 0,
            'por_status': {s: c for s, c in por_status.all()},
            'valor_total': float(valor or 0),
            'recentes': [n.id for n in recentes.scalars().all()],
        }

    async def _adicionar_historico(self, nota_id: int, acao: str, descricao: str = None):
        h = HistoricoNota(nota_id=nota_id, acao=acao, descricao=descricao)
        self.db.add(h)

    async def obter_historico(self, nota_id: int):
        r = await self.db.execute(
            select(HistoricoNota)
            .where(HistoricoNota.nota_id == nota_id)
            .order_by(HistoricoNota.data_hora.desc())
        )
        return r.scalars().all()

    async def listar_pendencias(self, offset: int = 0, limit: int = 50):
        q = select(NotaFiscal).where(
            NotaFiscal.status.in_(['ERRO', 'PENDENTE', 'NAO_PROCESSADA'])
        ).order_by(NotaFiscal.data_entrada.desc()).offset(offset).limit(limit)
        r = await self.db.execute(q)
        return r.scalars().all()
