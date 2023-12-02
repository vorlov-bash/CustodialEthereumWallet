from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import settings

async_engine = create_async_engine(
    url=settings.DATABASE_URI,
)

async_session = async_sessionmaker(async_engine, expire_on_commit=False)
