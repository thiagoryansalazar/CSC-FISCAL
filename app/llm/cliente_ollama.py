import httpx
from typing import Optional
from app.config import OLLAMA_URL, OLLAMA_MODEL

class ClienteOllama:
    def __init__(self, url: str = OLLAMA_URL, modelo: str = OLLAMA_MODEL):
        self.url = url.rstrip('/')
        self.modelo = modelo

    async def gerar(self, prompt: str, sistema: Optional[str] = None) -> str:
        payload = {'model': self.modelo, 'prompt': prompt, 'stream': False}
        if sistema:
            payload['system'] = sistema
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f'{self.url}/api/generate', json=payload)
            resp.raise_for_status()
            return resp.json().get('response', '')

    async def extrair_dados_nfe(self, texto_documento: str) -> dict:
        sistema = "Voce e um especialista em documentos fiscais brasileiros. Extraia os dados da NF-e fornecida."
        prompt = f"""Extraia os seguintes dados DESTE documento fiscal em formato JSON:
- chave_acesso (44 digitos)
- numero
- serie
- cnpj_emitente (apenas digitos)
- nome_fornecedor
- data_emissao
- valor_total
- itens: lista com codigo, descricao, ncm, cfop, quantidade, valor_unitario, valor_total

Documento:
{texto_documento[:8000]}

Responda APENAS com o JSON, sem explicacoes."""
        try:
            resp = await self.gerar(prompt, sistema)
            import json, re
            m = re.search(r'\{.*\}', resp, re.DOTALL)
            if m:
                return json.loads(m.group(0))
        except Exception:
            return {"erro": "Falha ao extrair dados via LLM"}

    async def perguntar(self, pergunta: str, contexto: str) -> str:
        sistema = "Voce e um assistente especializado em documentos fiscais brasileiros."
        prompt = f"""Contexto do documento fiscal:
{contexto[:6000]}

Pergunta: {pergunta}

Responda de forma clara e objetiva com base no contexto fornecido."""
        try:
            return await self.gerar(prompt, sistema)
        except Exception:
            return "Falha ao processar pergunta via LLM."

    async def ping(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f'{self.url}/api/tags')
                return resp.status_code == 200
        except Exception:
            return False
