# Roadmap — CSC Fiscal

## Fase 0 — Estrutura Inicial ✅
- [x] Models SQLAlchemy (NotaFiscal, ItemNota, HistoricoNota, ExtracaoNota)
- [x] Rotas FastAPI (notas, upload, dashboard, historico, assistente)
- [x] Services (NotaService, ExtracaoService, ComparadorService, RagService)
- [x] Extractors (XML, PDF, XLSX)
- [x] LLM (ClienteOllama + LangChain + ChromaDB RAG)
- [x] Frontend SPA (dashboard, upload, listagem, detalhes, chat IA)
- [x] Config (.env, config.py, database.py)

## Fase 1 — Correções Críticas ✅
- [x] Regex inválido `[[:ord:]]` no PDF extractor
- [x] `import re` no final do xml_extractor.py
- [x] Extração de nome_fornecedor, data_emissao e valor_total no PDF

## Fase 2 — Qualidade e Testes ✅
- [x] pytest configurado com 31 testes
- [x] Testes unitários para extractors (XML, helpers)
- [x] Testes de validação (CNPJ, chave de acesso)
- [x] Alembic configurado com migration inicial

## Fase 3 — Funcionalidades ✅
- [x] Endpoint de exportação CSV/JSON (`GET /api/notas/export`)
- [x] Upload múltiplo (`POST /api/upload/batch`)
- [x] Validação de CNPJ e chave de acesso

## Fase 4 — Infraestrutura ✅
- [x] Dockerfile (Python 3.13-slim)
- [x] docker-compose (app + Ollama)
- [x] Logging estruturado
- [x] CI básico (GitHub Actions)

## Próximos Passos (Sugestões)
- Autenticação/autorização
- Notificações em tempo real (WebSocket)
- Dashboard com gráficos
- Suporte a PostgreSQL via variável DATABASE_URL
- Deploy em produção (nginx + systemd ou cloud)
