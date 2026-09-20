"""exams: Exam Center (mock/school_subject/free + scoring snapshot)

Revision ID: 0007_exams
Revises: 0006_planning
Create Date: 2026-09-20

doc 12 §12.2 (Exam Center)، doc 08 §8.1 (scoring کنکوری/بدون‌جریمه جدا)،
doc 05 (test_sessions.exam_id از قبل موجود است).
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0007_exams"
down_revision = "0006_planning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exams",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False, server_default="mock"),
        sa.Column("status", sa.String(length=12), nullable=False, server_default="planned"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("resource_id", sa.String(length=36), sa.ForeignKey("resources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=True),
        sa.Column("planned_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("subjects", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("planned_topic_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("actual_topic_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("session_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("actual_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scoring", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('mock','school_subject','free')", name="ck_exams_kind"),
        sa.CheckConstraint(
            "status IN ('planned','in_progress','finished','cancelled')", name="ck_exams_status"
        ),
    )
    op.create_index("ix_exams_student_id", "exams", ["student_id"])
    op.create_index("ix_exams_status", "exams", ["status"])
    op.create_index("ix_exams_student_date", "exams", ["student_id", "scheduled_date"])


def downgrade() -> None:
    op.drop_index("ix_exams_student_date", table_name="exams")
    op.drop_index("ix_exams_status", table_name="exams")
    op.drop_index("ix_exams_student_id", table_name="exams")
    op.drop_table("exams")
