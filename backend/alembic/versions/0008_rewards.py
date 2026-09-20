"""rewards: points ledger (append-only) + streaks + badges + badge_awards

Revision ID: 0008_rewards
Revises: 0007_exams
Create Date: 2026-09-20

doc 13 (Points/Streak/Badges)، doc 05 §rewards، OD4 (۸ تا ۱۲ نشان seed —
seed در service.ensure_badge_seed انجام می‌شود، نه در migration).
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_rewards"
down_revision = "0007_exams"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "points_ledger",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_event", sa.String(length=40), nullable=False),
        sa.Column("ref_id", sa.String(length=80), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("active_date", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "source_event", "ref_id", name="uq_points_ledger_student_source_ref"),
        sa.CheckConstraint(
            "source_event IN ('plan_task.completed','review.completed','test_session.finished','checkin.submitted')",
            name="ck_points_ledger_source_event",
        ),
        sa.CheckConstraint("points > 0", name="ck_points_ledger_points_positive"),
    )
    op.create_index("ix_points_ledger_student_id", "points_ledger", ["student_id"])
    op.create_index("ix_points_ledger_student_id_active_date", "points_ledger", ["student_id", "active_date"])

    op.create_table(
        "streaks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("longest_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_active_date", sa.String(length=10), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", name="uq_streaks_student_id"),
        sa.CheckConstraint("current_streak >= 0", name="ck_streaks_current_nonneg"),
        sa.CheckConstraint("longest_streak >= 0", name="ck_streaks_longest_nonneg"),
    )
    op.create_index("ix_streaks_student_id", "streaks", ["student_id"])

    op.create_table(
        "badges",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("title_fa", sa.String(length=120), nullable=False),
        sa.Column("description_fa", sa.String(length=240), nullable=False, server_default=""),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("target", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code", name="uq_badges_code"),
        sa.CheckConstraint("target > 0", name="ck_badges_target_positive"),
    )

    op.create_table(
        "badge_awards",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("badge_id", sa.String(length=36), sa.ForeignKey("badges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "badge_id", name="uq_badge_awards_student_badge"),
    )
    op.create_index("ix_badge_awards_student_id", "badge_awards", ["student_id"])
    op.create_index("ix_badge_awards_badge_id", "badge_awards", ["badge_id"])


def downgrade() -> None:
    op.drop_table("badge_awards")
    op.drop_table("badges")
    op.drop_table("streaks")
    op.drop_table("points_ledger")
