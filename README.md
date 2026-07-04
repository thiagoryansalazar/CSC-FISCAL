# CSC Fiscal

Sistema de apoio fiscal com inteligência artificial para processamento, análise e consulta de documentos fiscais (NF-e, DANFE).

## Stack

- **Backend:** Python 3.14+, FastAPI, SQLAlchemy (async), SQLite/PostgreSQL
- **Frontend:** HTML/CSS/JS SPA (static, servido pelo FastAPI)
- **IA:** Ollama (LLaMA 3.2) + LangChain + ChromaDB (RAG)
- **Extração:** pdfplumber, lxml, openpyxl

## Requisitos

- Python 3.14+
- Ollama (opcional, para IA) com modelo like `llama3.2`

## Instalação

```bash
pip install -r requirements.txt
cp .env.example .env
# Edite .env se necessário
```

## Executar

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Acesse http://localhost:8000

## Estrutura

```
app/                   # Código Python
  models/              # SQLAlchemy models
  routers/             # FastAPI routers
  services/            # Lógica de negócio
  extractors/          # Parsers (XML, PDF, XLSX)
  llm/                 # Clientes LLM (Ollama)
  schemas/             # Pydantic schemas
frontend/              # SPA HTML/CSS/JS
  assets/              # CSS, JS
storage/               # Arquivos recebidos
  input/               # PDFs
  xml/                 # XMLs
  chroma_db/           # Vector store
docs/                  # Documentação
```

## API

- `GET /api/notas` - Listar notas
- `POST /api/notas` - Criar nota manual
- `GET /api/notas/{id}` - Detalhes
- `PUT /api/notas/{id}` - Atualizar
- `DELETE /api/notas/{id}` - Excluir
- `POST /api/upload` - Upload XML/PDF/XLSX
- `GET /api/dashboard` - Indicadores
- `GET /api/notas/{id}/historico` - Histórico
- `GET /api/notas/{id}/comparacao` - Comparação IA
- `POST /api/assistente/perguntar` - Pergunta RAG
- `GET /api/assistente/ping` - Status IA
