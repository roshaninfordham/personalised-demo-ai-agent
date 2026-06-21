"""Async database engine/session factory for the agent runtime."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from live_demo_agent_runtime.config import get_settings


@lru_cache(maxsize=1)
def get_async_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
    )


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=get_async_engine(), expire_on_commit=False, autoflush=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as session:
        yield session


async def ping_database() -> bool:
    async with get_sessionmaker()() as session:
        result = await session.execute(text("select 1"))
        return bool(result.scalar_one() == 1)


async def dispose_database_engine() -> None:
    if get_async_engine.cache_info().currsize == 0:
        return
    engine = get_async_engine()
    await engine.dispose()
    get_async_engine.cache_clear()
    get_sessionmaker.cache_clear()
