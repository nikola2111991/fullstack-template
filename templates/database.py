"""
Database: Async SQLAlchemy + Supabase connection, session dependency, transaction decorator
Usage:
    from app.db.database import get_db, transactional

    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()
"""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False
    class Config:
        env_file = ".env"


settings = DatabaseSettings()

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.db_echo,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a DB session, auto-closes after request."""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Standalone context manager for scripts, background jobs, etc."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def transactional(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator: wraps a service function in a DB transaction.
    The decorated function must accept `db: AsyncSession` as first arg.
    """
    @wraps(fn)
    async def wrapper(db: AsyncSession, *args: Any, **kwargs: Any) -> Any:
        async with db.begin():
            return await fn(db, *args, **kwargs)
    return wrapper


async def init_db() -> None:
    """Create all tables. Call once on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def close_db() -> None:
    """Dispose engine. Call on shutdown."""
    await engine.dispose()
    logger.info("Database connection closed")
