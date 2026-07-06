# Status do Projeto — CSC Fiscal

**Última atualização:** 06/07/2026

## Resumo

| Item | Status |
|------|--------|
| Backend (FastAPI) | ✅ Completo |
| Frontend (SPA) | ✅ Completo |
| Extractors (XML/PDF/XLSX) | ✅ Corrigido |
| LLM + RAG | ✅ Implementado |
| Testes | ✅ 31 testes passando |
| Migrations (Alembic) | ✅ Configurado |
| Docker | ✅ Dockerfile + compose |
| CI | ✅ GitHub Actions |

## Estatísticas

- **Testes:** 31/31 passando
- **Endpoints:** 15+
- **Modelos:** 4 tabelas (notas_fiscais, itens_nota, historico_nota, extracoes_nota)
- **Cobertura de extractors:** XML, PDF, XLSX

## Como Executar

```bash
# Desenvolvimento
uvicorn main:app --reload --port 8000

# Testes
python -m pytest tests/ -v

# Migrations
alembic upgrade head

# Docker
docker-compose up --build
```
