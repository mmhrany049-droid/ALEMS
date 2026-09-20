"""Alembic environment — URL from app config; metadata from all models.

doc 05: every schema change only via Alembic.
When a phase adds tables, import its models here so autogenerate sees them.
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.base import Base

# import all model modules so their tables register on Base.metadata
import app.core.versioning  # noqa: F401
import app.modules.identity.models  # noqa: F401
import app.modules.student.models  # noqa: F401
import app.modules.settings.models  # noqa: F401
import app.modules.academic.models  # noqa: F401
import app.modules.activity.models  # noqa: F401
import app.modules.review.models  # noqa: F401
import app.modules.planning.models  # noqa: F401
import app.modules.exam.models  # noqa: F401
import app.modules.analytics.models  # noqa: F401
import app.modules.report.models  # noqa: F401
import app.modules.export.models  # noqa: F401
import app.modules.rewards.models  # noqa: F401
import app.modules.backup.models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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
