"""Alembic environment. The URL is injected by app/utils/migrations.py via
config.attributes (the URL-encoded ODBC string contains '%', which ConfigParser
would mis-handle as interpolation). When invoked via the CLI it derives the URL
from the app config."""

from sqlalchemy import create_engine, pool
from alembic import context

config = context.config


def _get_url() -> str:
    url = config.attributes.get("sqlalchemy_url")
    if url:
        return url
    # CLI fallback so `alembic revision` etc. work too.
    from app.utils.migrations import get_sqlalchemy_url
    return get_sqlalchemy_url()


target_metadata = None  # raw-SQL migrations; no ORM metadata


def run_migrations_offline() -> None:
    context.configure(url=_get_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(_get_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
