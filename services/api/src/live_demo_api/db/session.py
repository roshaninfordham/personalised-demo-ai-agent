"""Async database engine and session factory."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from live_demo_api.config import get_settings


@lru_cache(maxsize=1)
def get_async_engine() -> AsyncEngine:
    settings = get_settings()
    connect_args = {
        "server_settings": {
            "statement_timeout": str(settings.database_statement_timeout_ms),
        },
    }
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
        connect_args=connect_args,
    )


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_async_engine(),
        expire_on_commit=False,
        autoflush=False,
    )


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as session:
        yield session


async def ping_database() -> bool:
    async with get_sessionmaker()() as session:
        result = await session.execute(text("select 1"))
        value = result.scalar_one()
        return bool(value == 1)
