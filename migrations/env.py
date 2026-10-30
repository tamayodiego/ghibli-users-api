"""Entorno de Alembic: se conecta a la base y conoce todas las tablas por Base.metadata."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.database import Base  # también carga el .env
from app.modules.users import models  # noqa: F401  (registra la tabla users en Base.metadata)
from app.modules.role_requests import models as role_request_models  # noqa: F401  (registra role_requests)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def database_url() -> str:
    return os.environ["DATABASE_URL"]


def run_migrations_offline() -> None:
    """``alembic upgrade head --sql``: imprime el SQL en lugar de ejecutarlo."""
    context.configure(url=database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
