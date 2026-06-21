"""Process-level dependencies for the learner worker."""

from __future__ import annotations

from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from live_demo_backend_common.ai.embeddings.fake import FakeEmbeddingProvider
from live_demo_backend_common.policy.redaction import RedactionConfig, RedactionEngine
from live_demo_learner_worker.browser.browser_runtime_client import FakeBrowserRuntimeClient
from live_demo_learner_worker.config import LearnerWorkerSettings
from live_demo_learner_worker.events.learner_event_publisher import LearnerEventPublisher


@dataclass(slots=True)
class LearnerDependencies:
    settings: LearnerWorkerSettings
    redis: Redis[bytes]
    db_engine: AsyncEngine
    db_sessionmaker: async_sessionmaker[AsyncSession]
    browser_client: FakeBrowserRuntimeClient
    event_publisher: LearnerEventPublisher
    redaction_engine: RedactionEngine
    embedding_provider: FakeEmbeddingProvider


def build_dependencies(settings: LearnerWorkerSettings, redis: Redis[bytes]) -> LearnerDependencies:
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
    )
    redaction = RedactionEngine(
        RedactionConfig(
            hash_secret=settings.redaction_hash_secret.get_secret_value() or None,
            customer_name_list=tuple(
                item.strip()
                for item in settings.redaction_customer_name_list.split(",")
                if item.strip()
            ),
            max_text_chars=settings.redaction_max_text_chars,
            max_json_depth=settings.redaction_max_json_depth,
            max_json_keys=settings.redaction_max_json_keys,
        )
    )
    return LearnerDependencies(
        settings=settings,
        redis=redis,
        db_engine=engine,
        db_sessionmaker=async_sessionmaker(engine, expire_on_commit=False),
        browser_client=FakeBrowserRuntimeClient(),
        event_publisher=LearnerEventPublisher(redis, settings.redis_event_stream_maxlen),
        redaction_engine=redaction,
        embedding_provider=FakeEmbeddingProvider(dimensions=settings.ai_embedding_dimensions),
    )
