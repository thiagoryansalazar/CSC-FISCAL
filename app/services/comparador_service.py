import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.extracao_nota import ExtracaoNota

class ComparadorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def comparar(self, nota_id: int) -> dict:
        r = await self.db.execute(
            select(ExtracaoNota)
            .where(ExtracaoNota.nota_id == nota_id)
            .order_by(ExtracaoNota.criado_em.desc())
            .limit(1)
        )
        extracao = r.scalar_one_or_none()
        if not extracao:
            return {'erro': 'Nenhuma extracao encontrada'}

        resultado = {
            'nota_id': nota_id,
            'dados_sistema': json.loads(extracao.dados_sistema) if extracao.dados_sistema else None,
            'dados_llm': json.loads(extracao.dados_llm) if extracao.dados_llm else None,
            'divergencias': json.loads(extracao.divergencias) if extracao.divergencias else [],
            'confianca': json.loads(extracao.confianca) if extracao.confianca else None,
            'documento_interpretavel': extracao.documento_interpretavel,
            'observacoes': extracao.observacoes,
        }

        if resultado['dados_sistema'] and resultado['dados_llm']:
            resultado['campos_conferidos'] = self._conferir_campos(
                resultado['dados_sistema'], resultado['dados_llm']
            )
        return resultado

    def _conferir_campos(self, sistema: dict, llm: dict) -> dict:
        conferidos = {}
        for campo in ['numero', 'serie', 'cnpj_emitente', 'nome_fornecedor', 'data_emissao', 'valor_total', 'chave_acesso']:
            v1 = str(sistema.get(campo, '') or '')
            v2 = str(llm.get(campo, '') or '')
            if v1 or v2:
                conferidos[campo] = {'sistema': v1, 'llm': v2, 'ok': v1 == v2}
        return conferidos

    async def listar_divergencias(self, offset: int = 0, limit: int = 50):
        r = await self.db.execute(
            select(ExtracaoNota)
            .where(ExtracaoNota.divergencias.isnot(None))
            .where(ExtracaoNota.divergencias != '[]')
            .order_by(ExtracaoNota.criado_em.desc())
            .offset(offset).limit(limit)
        )
        return r.scalars().all()

    async def resumo(self):
        total_ext = await self.db.scalar(select(func.count(ExtracaoNota.id)))
        com_div = await self.db.scalar(
            select(func.count(ExtracaoNota.id))
            .where(ExtracaoNota.divergencias.isnot(None))
            .where(ExtracaoNota.divergencias != '[]')
        )
        com_llm = await self.db.scalar(
            select(func.count(ExtracaoNota.id)).where(ExtracaoNota.llm_status == 'ok')
        )
        return {
            'total_extracoes': total_ext or 0,
            'com_divergencias': com_div or 0,
            'com_llm_ok': com_llm or 0,
        }
