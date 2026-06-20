"""Helpers for Alembic migration configuration."""

from sqlalchemy.engine import make_url


def to_sync_database_url(database_url: str) -> str:
    """Convert an async SQLAlchemy Postgres URL to a sync psycopg URL for Alembic."""
    url = make_url(database_url)
    if url.drivername == "postgresql+asyncpg":
        return url.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)
    return url.render_as_string(hide_password=False)
