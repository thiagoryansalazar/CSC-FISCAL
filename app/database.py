from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import DATABASE_URL
import os

os.makedirs('storage', exist_ok=True)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    from app.models.nota_fiscal import NotaFiscal
    from app.models.item_nota import ItemNota
    from app.models.historico_nota import HistoricoNota
    from app.models.extracao_nota import ExtracaoNota
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
