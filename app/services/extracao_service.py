import json
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.extracao_nota import ExtracaoNota
from app.extractors.extrator_service import processar_arquivo, extrair_texto_puro, calcular_hash
from app.llm.cliente_ollama import ClienteOllama
from app.config import LLM_ENABLED

class ExtracaoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def extrair(self, nota_id: int, caminho_arquivo: str, nome_arquivo: str = '', llm: ClienteOllama = None):
        nome_arquivo = nome_arquivo or os.path.basename(caminho_arquivo)
        ext = os.path.splitext(nome_arquivo)[1].lower().lstrip('.')
        hash_arquivo = calcular_hash(caminho_arquivo)
        tamanho = os.path.getsize(caminho_arquivo)

        extracao = ExtracaoNota(
            nota_id=nota_id,
            arquivo_nome=nome_arquivo,
            arquivo_tipo=ext,
            arquivo_sha256=hash_arquivo,
            arquivo_tamanho=tamanho,
        )
        self.db.add(extracao)
        await self.db.flush()

        texto_result = extrair_texto_puro(caminho_arquivo)
        if 'texto' in texto_result:
            extracao.texto_extraido = texto_result['texto'][:50000]
        elif 'erro' in texto_result:
            extracao.observacoes = texto_result['erro']
            await self.db.flush()
            return extracao

        if LLM_ENABLED and llm:
            try:
                dados_llm = await llm.extrair_dados_nfe(extracao.texto_extraido)
                if dados_llm and 'erro' not in dados_llm:
                    extracao.dados_llm = json.dumps(dados_llm, ensure_ascii=False)
                extracao.llm_status = 'ok'
            except Exception as e:
                extracao.llm_status = f'erro: {e}'
        else:
            extracao.llm_status = 'nao_disponivel'

        dados_sistema = processar_arquivo(caminho_arquivo)
        if 'erro' not in dados_sistema:
            dados_sistema.pop('texto_extraido', None)
            itens = dados_sistema.pop('itens', [])
            extracao.dados_sistema = json.dumps(dados_sistema, ensure_ascii=False)
            dados_consolidados = {**dados_sistema, 'qtd_itens': len(itens), 'itens': itens}
            if extracao.dados_llm:
                try:
                    llm_data = json.loads(extracao.dados_llm)
                    dados_consolidados['llm'] = llm_data
                    divergencias = self._comparar(dados_sistema, llm_data)
                    if divergencias:
                        extracao.divergencias = json.dumps(divergencias, ensure_ascii=False)
                    confianca = self._calcular_confianca(dados_sistema)
                    extracao.confianca = json.dumps(confianca, ensure_ascii=False)
                except json.JSONDecodeError:
                    pass
            extracao.dados_consolidados = json.dumps(dados_consolidados, ensure_ascii=False)
        else:
            if not extracao.observacoes:
                extracao.observacoes = dados_sistema['erro']

        await self.db.flush()
        return extracao

    def _comparar(self, sistema: dict, llm: dict) -> list:
        divergencias = []
        for campo in ['numero', 'serie', 'valor_total', 'cnpj_emitente', 'nome_fornecedor']:
            v1 = str(sistema.get(campo, '') or '').strip()
            v2 = str(llm.get(campo, '') or '').strip()
            if v1 and v2 and v1 != v2:
                divergencias.append({'campo': campo, 'valor_sistema': v1, 'valor_llm': v2})
        return divergencias

    def _calcular_confianca(self, dados: dict) -> dict:
        campos = ['chave_acesso', 'numero', 'cnpj_emitente', 'valor_total', 'nome_fornecedor']
        preenchidos = sum(1 for c in campos if dados.get(c))
        return {
            'score': round(preenchidos / len(campos) * 100, 1),
            'campos_preenchidos': preenchidos,
            'campos_total': len(campos),
        }

    async def obter_extracao(self, nota_id: int):
        r = await self.db.execute(
            select(ExtracaoNota)
            .where(ExtracaoNota.nota_id == nota_id)
            .order_by(ExtracaoNota.criado_em.desc())
            .limit(1)
        )
        return r.scalar_one_or_none()
