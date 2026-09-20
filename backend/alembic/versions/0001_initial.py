"""initial schema — app_metadata

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-20

Phase 0 (doc 14): version management table (doc 04 Foundation).
Business tables land in their phases (05_DATABASE_SPEC_V2).
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_metadata",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("app_metadata")
