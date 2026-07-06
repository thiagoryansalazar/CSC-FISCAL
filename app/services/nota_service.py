from datetime import datetime
from sqlalchemy import select, func, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.nota_fiscal import NotaFiscal
from app.models.historico_nota import HistoricoNota
from app.schemas.nota_schema import NotaFiscalCreate, NotaFiscalUpdate

class NotaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def listar(self, status: str = None, search: str = None,
                     cnpj: str = None, data_inicio: str = None, data_fim: str = None,
                     offset: int = 0, limit: int = 50):
        q = select(NotaFiscal).order_by(NotaFiscal.data_entrada.desc())
        if status:
            q = q.where(NotaFiscal.status == status)
        if search:
            q = q.where(
                NotaFiscal.nome_fornecedor.ilike(f'%{search}%') |
                NotaFiscal.numero.ilike(f'%{search}%') |
                NotaFiscal.chave_acesso.ilike(f'%{search}%')
            )
        if cnpj:
            q = q.where(NotaFiscal.cnpj_emitente.ilike(f'%{cnpj}%'))
        if data_inicio:
            q = q.where(NotaFiscal.data_emissao >= data_inicio)
        if data_fim:
            q = q.where(NotaFiscal.data_emissao <= data_fim)
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

    async def obter_dashboard(self, data_inicio: str = None, data_fim: str = None,
                              status: str = None, fornecedor: str = None, cnpj: str = None):
        q = select(func.count(NotaFiscal.id))
        if data_inicio:
            q = q.where(NotaFiscal.data_emissao >= data_inicio)
        if data_fim:
            q = q.where(NotaFiscal.data_emissao <= data_fim)
        if status:
            q = q.where(NotaFiscal.status == status)
        if fornecedor:
            q = q.where(NotaFiscal.nome_fornecedor.ilike(f'%{fornecedor}%'))
        if cnpj:
            q = q.where(NotaFiscal.cnpj_emitente.ilike(f'%{cnpj}%'))
        total = await self.db.scalar(q)

        qs = select(NotaFiscal.status, func.count(NotaFiscal.id).label('total'))
        if data_inicio:
            qs = qs.where(NotaFiscal.data_emissao >= data_inicio)
        if data_fim:
            qs = qs.where(NotaFiscal.data_emissao <= data_fim)
        qs = qs.group_by(NotaFiscal.status)
        por_status = await self.db.execute(qs)

        qv = select(func.coalesce(func.sum(NotaFiscal.valor_total), 0))
        if data_inicio:
            qv = qv.where(NotaFiscal.data_emissao >= data_inicio)
        if data_fim:
            qv = qv.where(NotaFiscal.data_emissao <= data_fim)
        valor = await self.db.scalar(qv)

        qr = select(NotaFiscal).order_by(NotaFiscal.data_entrada.desc()).limit(5)
        recentes = await self.db.execute(qr)

        qd = select(func.count(NotaFiscal.id)).where(NotaFiscal.status == 'DUPLICADA')
        if data_inicio:
            qd = qd.where(NotaFiscal.data_emissao >= data_inicio)
        if data_fim:
            qd = qd.where(NotaFiscal.data_emissao <= data_fim)
        duplicadas = await self.db.scalar(qd)
        qe = select(func.count(NotaFiscal.id)).where(NotaFiscal.status == 'ERRO')
        if data_inicio:
            qe = qe.where(NotaFiscal.data_emissao >= data_inicio)
        if data_fim:
            qe = qe.where(NotaFiscal.data_emissao <= data_fim)
        erros = await self.db.scalar(qe)
        qp = select(func.count(NotaFiscal.id)).where(NotaFiscal.status == 'PROCESSADA')
        if data_inicio:
            qp = qp.where(NotaFiscal.data_emissao >= data_inicio)
        if data_fim:
            qp = qp.where(NotaFiscal.data_emissao <= data_fim)
        processadas = await self.db.scalar(qp)
        qesp = select(func.count(NotaFiscal.id)).where(NotaFiscal.status == 'EM_ESPERA')
        if data_inicio:
            qesp = qesp.where(NotaFiscal.data_emissao >= data_inicio)
        if data_fim:
            qesp = qesp.where(NotaFiscal.data_emissao <= data_fim)
        espera = await self.db.scalar(qesp)

        return {
            'total': total or 0,
            'por_status': {s: c for s, c in por_status.all()},
            'valor_total': float(valor or 0),
            'recentes': [n.id for n in recentes.scalars().all()],
            'processadas': processadas or 0,
            'em_espera': espera or 0,
            'erros': erros or 0,
            'duplicadas': duplicadas or 0,
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
            NotaFiscal.status.in_(['ERRO', 'EM_ESPERA', 'ENTRADA'])
        ).order_by(NotaFiscal.data_entrada.desc()).offset(offset).limit(limit)
        r = await self.db.execute(q)
        return r.scalars().all()

    async def buscar_por_chave(self, chave: str):
        r = await self.db.execute(
            select(NotaFiscal).where(NotaFiscal.chave_acesso == chave)
        )
        return r.scalar_one_or_none()

    async def atualizar_status(self, nota_id: int, novo_status: str, descricao: str = None):
        nota = await self.obter(nota_id)
        if not nota:
            return None
        old = nota.status
        nota.status = novo_status
        await self.db.flush()
        await self._adicionar_historico(
            nota_id, 'status',
            descricao or f'{old} -> {novo_status}'
        )
        return nota
