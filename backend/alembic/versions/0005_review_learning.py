"""review & learning: question_marks, review_queue, learning_states

Revision ID: 0005_review_learning
Revises: 0004_test_engine
Create Date: 2026-09-20

doc 05 (learning_states: coverage/accuracy/retention_est/recency_score/
repeated_error_score/exam_readiness/confidence + ایندکس‌های حیاتی
review_queue(student_id, status, scheduled_date) و
learning_states(student_id, topic_id))، doc 10 (صف مرور، چرخه، learning state)،
doc 04 (Question Marking — تیک‌ها).
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_review_learning"
down_revision = "0004_test_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "question_marks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.String(length=36), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("important", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hard", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "question_id", name="uq_question_marks_student_id_question_id"),
    )
    op.create_index("ix_question_marks_student_id", "question_marks", ["student_id"])
    op.create_index("ix_question_marks_question_id", "question_marks", ["question_id"])

    op.create_table(
        "review_queue",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.String(length=36), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
        # snapshotها — نمایش حتی اگر سوال/موضوع حذف شود
        sa.Column("question_number", sa.Integer(), nullable=True),
        sa.Column("topic_title", sa.String(length=200), nullable=True),
        sa.Column("book_title", sa.String(length=200), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False, server_default="pending"),
        sa.Column("critical", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("wrong_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cycle_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scheduled_date", sa.Date(), nullable=True),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "question_id", name="uq_review_queue_student_id_question_id"),
        sa.CheckConstraint(
            "source IN ('wrong','blank','mark_review','mark_important','mark_hard')",
            name="ck_review_queue_source",
        ),
        sa.CheckConstraint("status IN ('pending','scheduled','absorbed')", name="ck_review_queue_status"),
    )
    op.create_index("ix_review_queue_student_id", "review_queue", ["student_id"])
    op.create_index("ix_review_queue_question_id", "review_queue", ["question_id"])
    op.create_index("ix_review_queue_scheduled_date", "review_queue", ["scheduled_date"])
    # doc 05 — ایندکس حیاتی
    op.create_index(
        "ix_review_queue_student_id_status_scheduled_date",
        "review_queue",
        ["student_id", "status", "scheduled_date"],
    )

    op.create_table(
        "learning_states",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("coverage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("accuracy", sa.Float(), nullable=False, server_default="0"),
        sa.Column("retention_est", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recency_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("repeated_error_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("exam_readiness", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("weakness", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempted_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wrong_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "topic_id", name="uq_learning_states_student_id_topic_id"),
    )
    op.create_index("ix_learning_states_student_id", "learning_states", ["student_id"])
    op.create_index("ix_learning_states_topic_id", "learning_states", ["topic_id"])
    # doc 05 — ایندکس حیاتی
    op.create_index("ix_learning_states_student_id_topic_id", "learning_states", ["student_id", "topic_id"])


def downgrade() -> None:
    op.drop_index("ix_learning_states_student_id_topic_id", table_name="learning_states")
    op.drop_index("ix_learning_states_topic_id", table_name="learning_states")
    op.drop_index("ix_learning_states_student_id", table_name="learning_states")
    op.drop_table("learning_states")
    op.drop_index("ix_review_queue_student_id_status_scheduled_date", table_name="review_queue")
    op.drop_index("ix_review_queue_scheduled_date", table_name="review_queue")
    op.drop_index("ix_review_queue_question_id", table_name="review_queue")
    op.drop_index("ix_review_queue_student_id", table_name="review_queue")
    op.drop_table("review_queue")
    op.drop_index("ix_question_marks_question_id", table_name="question_marks")
    op.drop_index("ix_question_marks_student_id", table_name="question_marks")
    op.drop_table("question_marks")
