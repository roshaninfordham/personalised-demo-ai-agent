from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from psycopg import connect, sql
from sqlalchemy.engine import make_url

from live_demo_api.config import get_settings

pytestmark = pytest.mark.integration


REQUIRED_TABLES = {
    "organizations",
    "users",
    "products",
    "product_guidance",
    "demo_recipes",
    "demo_steps",
    "demo_sessions",
    "browser_sessions",
    "screen_snapshots",
    "ui_elements",
    "demo_graph_edges",
    "transcript_events",
    "action_events",
    "knowledge_chunks",
    "lead_insights",
    "lead_summaries",
    "crm_exports",
    "model_invocations",
    "audit_logs",
    "artifact_objects",
    "event_outbox",
}


@pytest.fixture
def migrated_database(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    settings = get_settings()
    sync_url = make_url(settings.database_sync_url)
    database_name = f"demo_agent_test_{uuid4().hex}"
    admin_url = sync_url.set(drivername="postgresql", database="postgres").render_as_string(
        hide_password=False
    )
    test_sync_url = sync_url.set(database=database_name).render_as_string(hide_password=False)
    test_async_url = sync_url.set(
        drivername="postgresql+asyncpg", database=database_name
    ).render_as_string(hide_password=False)

    with connect(admin_url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    monkeypatch.setenv("DATABASE_SYNC_URL", test_sync_url)
    monkeypatch.setenv("DATABASE_URL", test_async_url)
    get_settings.cache_clear()

    try:
        yield test_sync_url
    finally:
        get_settings.cache_clear()
        with connect(admin_url, autocommit=True) as connection:
            connection.execute(
                sql.SQL(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = {}"
                ).format(sql.Literal(database_name))
            )
            connection.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(database_name))
            )


def _alembic_config() -> Config:
    config = Config("services/api/alembic.ini")
    config.set_main_option("script_location", "services/api/alembic")
    return config


def test_alembic_config_loads() -> None:
    config = _alembic_config()
    assert config.get_main_option("script_location") == "services/api/alembic"


def test_migration_upgrade_downgrade_upgrade(migrated_database: str) -> None:
    config = _alembic_config()
    command.upgrade(config, "head")

    engine = sa.create_engine(migrated_database)
    try:
        inspector = sa.inspect(engine)
        assert REQUIRED_TABLES.issubset(set(inspector.get_table_names()))

        with engine.connect() as connection:
            extensions = set(
                connection.execute(sa.text("select extname from pg_extension")).scalars().all()
            )
            assert {"pgcrypto", "vector"}.issubset(extensions)

            indexes = {
                row[0]
                for row in connection.execute(
                    sa.text("select indexname from pg_indexes where schemaname = 'public'")
                )
            }
            assert "ix_demo_sessions_organization_id_status_created_at" in indexes
            assert "ix_knowledge_chunks_embedding_hnsw" in indexes

        command.downgrade(config, "base")
        assert "organizations" not in sa.inspect(engine).get_table_names()

        command.upgrade(config, "head")
        assert REQUIRED_TABLES.issubset(set(sa.inspect(engine).get_table_names()))
    finally:
        engine.dispose()
