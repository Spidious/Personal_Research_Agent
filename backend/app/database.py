"""Async SQLAlchemy engine, session factory, and shared declarative base."""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Shared declarative base inherited by all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a scoped async database session."""
    async with AsyncSessionLocal() as session:
        yield session
