"""مدل‌های ماژول دانش‌آموز — پروفایل و وضعیت روزانه."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import JSON, UUID, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base, TimestampMixin, UUIDPk

GRADES = ("دهم", "یازدهم", "دوازدهم", "فارغ‌التحصیل")
FIELDS = ("ریاضی", "تجربی", "انسانی")


class StudentProfile(Base, UUIDPk, TimestampMixin):
    """پروفایل دانش‌آموز."""

    __tablename__ = "student_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(120))
    grade: Mapped[str] = mapped_column(String(32))       # دهم / یازدهم / دوازدهم / فارغ‌التحصیل
    field: Mapped[str] = mapped_column(String(32))       # ریاضی / تجربی / انسانی
    academic_year: Mapped[str | None] = mapped_column(String(16), nullable=True)
    target_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_major: Mapped[str | None] = mapped_column(String(64), nullable=True)


class StudentState(Base, UUIDPk):
    """وضعیت روزانه دانش‌آموز (انرژی، حال روحی، شرایط مطالعه)."""

    __tablename__ = "student_states"
    __table_args__ = (UniqueConstraint("student_id", "date", name="uq_student_state_date"),)

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)
    energy_level: Mapped[int] = mapped_column(Integer)   # ۱ تا ۵
    mood: Mapped[str | None] = mapped_column(String(64), nullable=True)
    study_condition: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
