from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from live_demo_api.config import get_settings
from live_demo_api.db import models as _models  # noqa: F401
from live_demo_api.db.base import Base
from live_demo_api.db.migrations import to_sync_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_migration_url() -> str:
    settings = get_settings()
    if settings.app_env == "production" and not settings.allow_production_migrations:
        raise RuntimeError(
            "Refusing to run migrations with APP_ENV=production unless "
            "ALLOW_PRODUCTION_MIGRATIONS=true."
        )
    return settings.database_sync_url or to_sync_database_url(settings.database_url)


def run_migrations_offline() -> None:
    context.configure(
        url=get_migration_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_migration_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
