import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db
from app.logging_config import configurar_logging
from app.routers import notas, upload, dashboard, historico, assistente

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    configurar_logging()
    logger.info('Iniciando CSC Fiscal...')
    os.makedirs('storage', exist_ok=True)
    os.makedirs('storage/input', exist_ok=True)
    os.makedirs('storage/xml', exist_ok=True)
    os.makedirs('storage/chroma_db', exist_ok=True)
    await init_db()
    logger.info('Banco de dados inicializado')
    yield
    logger.info('Encerrando CSC Fiscal...')

app = FastAPI(title='CSC Fiscal', version='0.1.0', lifespan=lifespan)

@app.get('/api/health')
async def health():
    return {'status': 'ok', 'app': 'CSC Fiscal'}

app.include_router(notas.router)
app.include_router(upload.router)
app.include_router(dashboard.router)
app.include_router(historico.router)
app.include_router(assistente.router)

frontend_path = os.path.join(os.path.dirname(__file__), 'frontend')
if os.path.isdir(frontend_path):
    app.mount('/', StaticFiles(directory=frontend_path, html=True), name='frontend')
