from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, MappedColumn, mapped_column
from sqlalchemy import DateTime, String, func
from typing import AsyncGenerator
import uuid
from datetime import datetime

from app.core.config import settings


_connect_args = {}
# psycopg3 + Neon pooled endpoint (pgbouncer): disable server-side prepared
# statements, which aren't compatible with transaction pooling.
if "+psycopg" in settings.DATABASE_URL:
    _connect_args["prepare_threshold"] = None

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,       # validate/replace connections dropped by Neon autosuspend
    pool_recycle=300,
    pool_timeout=30,
    connect_args=_connect_args,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
