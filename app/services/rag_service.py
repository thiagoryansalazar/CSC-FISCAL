import os
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.extracao_nota import ExtracaoNota
from app.models.nota_fiscal import NotaFiscal
from app.llm.cliente_ollama import ClienteOllama
from app.config import LLM_ENABLED, STORAGE_CHROMA

class RagService:
    def __init__(self, db: AsyncSession, llm: ClienteOllama = None):
        self.db = db
        self.llm = llm
        self._chroma = None

    def _get_chroma(self):
        if self._chroma is None:
            import chromadb
            os.makedirs(STORAGE_CHROMA, exist_ok=True)
            client = chromadb.PersistentClient(path=STORAGE_CHROMA)
            self._chroma = client.get_or_create_collection(
                name="notas_fiscais",
                metadata={"hnsw:space": "cosine"}
            )
        return self._chroma

    async def indexar_extracao(self, nota_id: int):
        r = await self.db.execute(
            select(ExtracaoNota)
            .where(ExtracaoNota.nota_id == nota_id)
            .order_by(ExtracaoNota.criado_em.desc())
            .limit(1)
        )
        extracao = r.scalar_one_or_none()
        if not extracao or not extracao.texto_extraido:
            return False

        r2 = await self.db.execute(select(NotaFiscal).where(NotaFiscal.id == nota_id))
        nota = r2.scalar_one_or_none()
        if not nota:
            return False

        texto = extracao.texto_extraido
        metadados = {
            'nota_id': str(nota_id),
            'numero': nota.numero or '',
            'fornecedor': nota.nome_fornecedor or '',
            'cnpj': nota.cnpj_emitente or '',
            'chave': nota.chave_acesso or '',
        }

        # Chunk the text
        chunks = self._chunk_text(texto)
        collection = self._get_chroma()

        # Remove existing docs for this nota_id
        existing = collection.get(where={"nota_id": str(nota_id)})
        if existing['ids']:
            collection.delete(ids=existing['ids'])

        ids = [f"nota_{nota_id}_chunk_{i}" for i in range(len(chunks))]
        collection.add(
            documents=chunks,
            metadatas=[metadados] * len(chunks),
            ids=ids,
        )
        return True

    def _chunk_text(self, texto: str, chunk_size: int = 1000, overlap: int = 100):
        if not texto:
            return []
        chunks = []
        start = 0
        while start < len(texto):
            end = min(start + chunk_size, len(texto))
            chunks.append(texto[start:end])
            start += chunk_size - overlap
        return chunks if chunks else [texto]

    async def perguntar(self, nota_id: int = None, pergunta: str = None) -> dict:
        if not LLM_ENABLED or not self.llm:
            return {'resposta': 'LLM nao configurado', 'docs': []}

        collection = self._get_chroma()

        if nota_id:
            results = collection.query(
                query_texts=[pergunta],
                n_results=5,
                where={"nota_id": str(nota_id)},
            )
        else:
            results = collection.query(
                query_texts=[pergunta],
                n_results=5,
            )

        if not results['documents'] or not results['documents'][0]:
            return {'resposta': 'Nenhum contexto encontrado.', 'docs': []}

        context = "\n\n".join(results['documents'][0])
        resposta = await self.llm.perguntar(pergunta, context)

        metadatas = results['metadatas'][0] if results['metadatas'] else []
        docs_info = [{'nota_id': m.get('nota_id', ''), 'fornecedor': m.get('fornecedor', '')}
                     for m in metadatas if m]

        return {
            'resposta': resposta,
            'docs': docs_info,
            'contexto': context[:500],
        }

    async def deletar_index(self, nota_id: int):
        collection = self._get_chroma()
        existing = collection.get(where={"nota_id": str(nota_id)})
        if existing['ids']:
            collection.delete(ids=existing['ids'])
        return True
