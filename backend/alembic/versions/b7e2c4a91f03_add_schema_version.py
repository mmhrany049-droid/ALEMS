"""افزودن جدول schema_version — Version Management Module

Revision ID: b7e2c4a91f03
Revises: 5a53d56efe9d
Create Date: 2026-09-19

جدول ثبت نسخه‌های schema (سند 05_DATABASE_SPEC §5.2):
    version     str  PK
    applied_at  datetime
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b7e2c4a91f03"
down_revision: Union[str, None] = "5a53d56efe9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "schema_version",
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("applied_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("version"),
    )


def downgrade() -> None:
    op.drop_table("schema_version")
