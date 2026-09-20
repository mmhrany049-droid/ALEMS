"""SQLAlchemy 2 declarative base.

doc 05: UUID string PK uniformly across the project; consistent naming
convention so Alembic autogenerate stays stable.
"""
from __future__ import annotations

import uuid

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def new_uuid() -> str:
    """UUID4 as string — uniform PK strategy (doc 05)."""
    return str(uuid.uuid4())
