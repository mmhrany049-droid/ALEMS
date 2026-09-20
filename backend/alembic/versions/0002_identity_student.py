"""identity & student: users, students, checkins, taught_topics

Revision ID: 0002_identity_student
Revises: 0001_initial
Create Date: 2026-09-20

doc 04 (Identity/Session/Permission/Student Profile/State/Taught),
doc 05 (taught_topics yektaei student_id+topic_id; UUID string PK),
doc 13 §13.6 (state dimensions self-report, 1..5).
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_identity_student"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="student"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "students",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("grade", sa.String(length=20), nullable=True),
        sa.Column("track", sa.String(length=40), nullable=True),
        sa.Column("target", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_students_user_id"),
    )
    op.create_index("ix_students_user_id", "students", ["user_id"], unique=True)

    op.create_table(
        "checkins",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("energy", sa.Integer(), nullable=False),
        sa.Column("focus", sa.Integer(), nullable=False),
        sa.Column("motivation", sa.Integer(), nullable=False),
        sa.Column("stress", sa.Integer(), nullable=False),
        sa.Column("fatigue", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "date", name="uq_checkins_student_id_date"),
        sa.CheckConstraint("energy BETWEEN 1 AND 5", name="ck_checkins_energy_range"),
        sa.CheckConstraint("focus BETWEEN 1 AND 5", name="ck_checkins_focus_range"),
        sa.CheckConstraint("motivation BETWEEN 1 AND 5", name="ck_checkins_motivation_range"),
        sa.CheckConstraint("stress BETWEEN 1 AND 5", name="ck_checkins_stress_range"),
        sa.CheckConstraint("fatigue BETWEEN 1 AND 5", name="ck_checkins_fatigue_range"),
    )
    op.create_index("ix_checkins_student_id", "checkins", ["student_id"])

    # doc 05: taught_topics — یکتایی (student_id, topic_id)
    # FK به academic.topics در فاز ۲ (مهاجرت books) اضافه می‌شود
    op.create_table(
        "taught_topics",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", sa.String(length=36), nullable=False),
        sa.Column("taught", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "topic_id", name="uq_taught_topics_student_id_topic_id"),
    )
    op.create_index("ix_taught_topics_student_id", "taught_topics", ["student_id"])
    op.create_index("ix_taught_topics_topic_id", "taught_topics", ["topic_id"])


def downgrade() -> None:
    op.drop_index("ix_taught_topics_topic_id", table_name="taught_topics")
    op.drop_index("ix_taught_topics_student_id", table_name="taught_topics")
    op.drop_table("taught_topics")
    op.drop_index("ix_checkins_student_id", table_name="checkins")
    op.drop_table("checkins")
    op.drop_index("ix_students_user_id", table_name="students")
    op.drop_table("students")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
