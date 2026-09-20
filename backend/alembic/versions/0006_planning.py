"""planning & today: goals, time_blocks, capacity_snapshots, plan_tasks, plan_runs, priority_snapshots, recommendations

Revision ID: 0006_planning
Revises: 0005_review_learning
Create Date: 2026-09-20

doc 05 (capacity_snapshots/recommendations/priority_snapshots)، doc 11 (time blocks،
capacity، generate-week pipeline لاگ‌شده، manual override/lock، recovery)،
doc 08 §8.6-8.7 و §8.10.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_planning"
down_revision = "0005_review_learning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False, server_default="week"),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('long','month','week')", name="ck_goals_kind"),
    )
    op.create_index("ix_goals_student_id", "goals", ["student_id"])

    op.create_table(
        "time_blocks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("start_minutes", sa.Integer(), nullable=False),
        sa.Column("end_minutes", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.Column("source", sa.String(length=10), nullable=False, server_default="schedule"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('school','class','free')", name="ck_time_blocks_kind"),
        sa.CheckConstraint("source IN ('schedule','override')", name="ck_time_blocks_source"),
        sa.CheckConstraint("start_minutes >= 0 AND start_minutes < 1440", name="ck_time_blocks_start_range"),
        sa.CheckConstraint("end_minutes > start_minutes AND end_minutes <= 1440", name="ck_time_blocks_end_range"),
    )
    op.create_index("ix_time_blocks_student_id_date", "time_blocks", ["student_id", "date"])

    op.create_table(
        "capacity_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("school_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("class_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_study_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_capacity_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("suggested_session_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_rate", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("source", sa.String(length=10), nullable=False, server_default="computed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "date", name="uq_capacity_snapshots_student_id_date"),
        sa.CheckConstraint("source IN ('computed','override')", name="ck_capacity_snapshots_source"),
    )

    op.create_table(
        "plan_tasks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=True),
        sa.Column("kind", sa.String(length=10), nullable=False, server_default="study"),
        sa.Column("topic_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("topic_title", sa.String(length=200), nullable=True),
        sa.Column("book_title", sa.String(length=200), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False, server_default="45"),
        sa.Column("count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="pending"),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source", sa.String(length=10), nullable=False, server_default="generated"),
        sa.Column("reason_code", sa.String(length=40), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('study','test','review','goal')", name="ck_plan_tasks_kind"),
        sa.CheckConstraint("status IN ('pending','done','skipped')", name="ck_plan_tasks_status"),
        sa.CheckConstraint("source IN ('generated','manual','recovered')", name="ck_plan_tasks_source"),
        sa.CheckConstraint("minutes > 0", name="ck_plan_tasks_minutes"),
    )
    op.create_index("ix_plan_tasks_student_id_date", "plan_tasks", ["student_id", "date"])
    op.create_index("ix_plan_tasks_student_id_week_start", "plan_tasks", ["student_id", "week_start"])

    op.create_table(
        "plan_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="ok"),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("kept_locked_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("removed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_plan_runs_student_id", "plan_runs", ["student_id"])

    op.create_table(
        "priority_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "week_start", name="uq_priority_snapshots_student_id_week_start"),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="suggested"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('suggested','accepted','rejected','edited')", name="ck_recommendations_status"
        ),
    )
    op.create_index("ix_recommendations_student_id_date", "recommendations", ["student_id", "date"])


def downgrade() -> None:
    op.drop_index("ix_recommendations_student_id_date", table_name="recommendations")
    op.drop_table("recommendations")
    op.drop_table("priority_snapshots")
    op.drop_index("ix_plan_runs_student_id", table_name="plan_runs")
    op.drop_table("plan_runs")
    op.drop_index("ix_plan_tasks_student_id_week_start", table_name="plan_tasks")
    op.drop_index("ix_plan_tasks_student_id_date", table_name="plan_tasks")
    op.drop_table("plan_tasks")
    op.drop_table("capacity_snapshots")
    op.drop_index("ix_time_blocks_student_id_date", table_name="time_blocks")
    op.drop_table("time_blocks")
    op.drop_index("ix_goals_student_id", table_name="goals")
    op.drop_table("goals")
