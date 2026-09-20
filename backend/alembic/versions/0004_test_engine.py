"""test engine: test_sessions, attempt_results, error_notes

Revision ID: 0004_test_engine
Revises: 0003_books_topics
Create Date: 2026-09-20

doc 05 (test_sessions + attempt_results با status/result/answer_key_version/
duration_seconds + ایندکس حیاتی attempts(student_id, solved_at))، doc 09 §9.2-9.4
(session/records/finish، past import با not_entered، time tracking)،
doc 02 FR-T5 (history append-only: بدون unique روی session+question؛ FKها
SET NULL تا تاریخچه با حذف/replace کتاب از بین نرود)، doc 04 (Error Notebook).
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_test_engine"
down_revision = "0003_books_topics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "test_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mode", sa.String(length=10), nullable=False),
        # SET NULL: حذف/replace کتاب تاریخچه جلسه را از بین نمی‌برد (append-only)
        sa.Column("resource_id", sa.String(length=36), sa.ForeignKey("resources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resource_title", sa.String(length=200), nullable=True),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="ui"),
        sa.Column("exam_id", sa.String(length=36), nullable=True),  # FK در فاز ۶ (exams)
        sa.Column("filters", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("selected_question_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("planned_duration", sa.Integer(), nullable=True),
        sa.Column("actual_duration", sa.Integer(), nullable=True),
        sa.Column("penalty_k", sa.Float(), nullable=True),
        sa.Column("correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wrong_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unanswered_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("not_entered_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("percent_konkur", sa.Float(), nullable=True),
        sa.Column("percent_no_penalty", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("mode IN ('timed','untimed','past')", name="ck_test_sessions_mode"),
    )
    op.create_index("ix_test_sessions_student_id", "test_sessions", ["student_id"])
    op.create_index("ix_test_sessions_resource_id", "test_sessions", ["resource_id"])

    op.create_table(
        "attempt_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("test_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.String(length=36), sa.ForeignKey("questions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("topic_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
        # snapshotها — «تاریخچه attempt نسخه زمان خودش را نگه می‌دارد» (doc 05)
        sa.Column("question_number", sa.Integer(), nullable=True),
        sa.Column("topic_title", sa.String(length=200), nullable=True),
        sa.Column("answer", sa.String(length=40), nullable=True),
        sa.Column("correct_answer", sa.String(length=40), nullable=True),
        sa.Column("answer_key_version", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=15), nullable=False),
        sa.Column("result", sa.String(length=10), nullable=False, server_default="unknown"),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("solved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('answered','unanswered','not_entered')", name="ck_attempt_results_status"),
        sa.CheckConstraint("result IN ('correct','wrong','blank','unknown')", name="ck_attempt_results_result"),
        sa.CheckConstraint("duration_seconds >= 0", name="ck_attempt_results_duration_nonneg"),
    )
    op.create_index("ix_attempt_results_session_id", "attempt_results", ["session_id"])
    op.create_index("ix_attempt_results_student_id", "attempt_results", ["student_id"])
    op.create_index("ix_attempt_results_question_id", "attempt_results", ["question_id"])
    # doc 05 — ایندکس حیاتی attempts (student_id, solved_at)
    op.create_index("ix_attempt_results_student_id_solved_at", "attempt_results", ["student_id", "solved_at"])

    op.create_table(
        "error_notes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_result_id", sa.String(length=36), sa.ForeignKey("attempt_results.id", ondelete="SET NULL"), nullable=True, unique=True),
        sa.Column("question_id", sa.String(length=36), sa.ForeignKey("questions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("test_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("topic_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("book_title", sa.String(length=200), nullable=True),
        sa.Column("topic_title", sa.String(length=200), nullable=True),
        sa.Column("question_number", sa.Integer(), nullable=True),
        sa.Column("your_answer", sa.String(length=40), nullable=True),
        sa.Column("correct_answer", sa.String(length=40), nullable=True),
        sa.Column("error_type", sa.String(length=20), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "error_type IN ('careless','concept','method','memory','other')",
            name="ck_error_notes_error_type",
        ),
    )
    op.create_index("ix_error_notes_student_id", "error_notes", ["student_id"])
    op.create_index("ix_error_notes_question_id", "error_notes", ["question_id"])
    op.create_index("ix_error_notes_session_id", "error_notes", ["session_id"])
    op.create_index("ix_error_notes_attempt_result_id", "error_notes", ["attempt_result_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_error_notes_attempt_result_id", table_name="error_notes")
    op.drop_index("ix_error_notes_session_id", table_name="error_notes")
    op.drop_index("ix_error_notes_question_id", table_name="error_notes")
    op.drop_index("ix_error_notes_student_id", table_name="error_notes")
    op.drop_table("error_notes")
    op.drop_index("ix_attempt_results_student_id_solved_at", table_name="attempt_results")
    op.drop_index("ix_attempt_results_question_id", table_name="attempt_results")
    op.drop_index("ix_attempt_results_student_id", table_name="attempt_results")
    op.drop_index("ix_attempt_results_session_id", table_name="attempt_results")
    op.drop_table("attempt_results")
    op.drop_index("ix_test_sessions_resource_id", table_name="test_sessions")
    op.drop_index("ix_test_sessions_student_id", table_name="test_sessions")
    op.drop_table("test_sessions")
