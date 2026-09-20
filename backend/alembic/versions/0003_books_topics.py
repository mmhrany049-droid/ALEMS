"""books & topics: resources, topics, questions, answer_keys

Revision ID: 0003_books_topics
Revises: 0002_identity_student
Create Date: 2026-09-20

doc 05 (block_type روی topics + is_structural + answer_keys نسخه‌دار +
ایندکس حیاتی topics(resource_id, block_type))، doc 08 §8.3 و doc 09 §9.1
(TOC-only import: هیچ NOT NULL روی questions نیست — سوال اختیاری است).
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_books_topics"
down_revision = "0002_identity_student"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        # publisher NOT NULL با default '' → یکتایی حتی وقتی ناشر غایب است
        sa.Column("publisher", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("subject", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "title", "publisher", name="uq_resources_student_title_publisher"),
    )
    op.create_index("ix_resources_student_id", "resources", ["student_id"])

    op.create_table(
        "topics",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("resource_id", sa.String(length=36), sa.ForeignKey("resources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("block_type", sa.String(length=20), nullable=False, server_default="topic"),
        sa.Column("is_structural", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "block_type IN ('topic','mixed','chapter_exam','checkup','konkur','other')",
            name="ck_topics_block_type",
        ),
    )
    op.create_index("ix_topics_resource_id", "topics", ["resource_id"])
    op.create_index("ix_topics_parent_id", "topics", ["parent_id"])
    # doc 05 — ایندکس حیاتی
    op.create_index("ix_topics_resource_id_block_type", "topics", ["resource_id", "block_type"])

    op.create_table(
        "questions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("topic_id", sa.String(length=36), sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=True),
        sa.Column("importance", sa.Integer(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("topic_id", "number", name="uq_questions_topic_id_number"),
        sa.CheckConstraint("difficulty BETWEEN 1 AND 5", name="ck_questions_difficulty_range"),
        sa.CheckConstraint("importance BETWEEN 1 AND 5", name="ck_questions_importance_range"),
    )
    op.create_index("ix_questions_topic_id", "questions", ["topic_id"])

    op.create_table(
        "answer_keys",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("question_id", sa.String(length=36), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("answer", sa.String(length=20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("question_id", "version", name="uq_answer_keys_question_id_version"),
    )
    op.create_index("ix_answer_keys_question_id", "answer_keys", ["question_id"])


def downgrade() -> None:
    op.drop_index("ix_answer_keys_question_id", table_name="answer_keys")
    op.drop_table("answer_keys")
    op.drop_index("ix_questions_topic_id", table_name="questions")
    op.drop_table("questions")
    op.drop_index("ix_topics_resource_id_block_type", table_name="topics")
    op.drop_index("ix_topics_parent_id", table_name="topics")
    op.drop_index("ix_topics_resource_id", table_name="topics")
    op.drop_table("topics")
    op.drop_index("ix_resources_student_id", table_name="resources")
    op.drop_table("resources")
