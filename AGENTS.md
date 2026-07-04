# AGENTS.md - CSC Fiscal (Python)

## Regras

1. Nao modificar codigo do `sped-nfe` (projeto PHP antigo) sem necessidade.
2. Manter estrutura organizada (`app/`, `frontend/`, `storage/`, `docs/`).
3. Nao expor credenciais, certificados ou dados sensiveis.
4. Toda interface deve estar em pt-BR.
5. Toda alteracao de status deve gerar historico em `historico_nota`.
6. Documentar decisoes tecnicas em `docs/DECISOES_TECNICAS.md`.
7. Atualizar `docs/ROADMAP.md` ao concluir marcos.
8. Testar antes de commit: `uvicorn main:app --reload --port 8000`.
9. Nao commitar .env, database.sqlite nem chroma_db/.

## Stack

- Python 3.14+, FastAPI, SQLAlchemy async, SQLite
- Frontend SPA estatico (HTML/CSS/JS)
- Ollama + ChromaDB + LangChain para RAG
