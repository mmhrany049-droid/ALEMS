"""مدل‌های ماژول برنامه‌ریزی — goals, time_blocks, plans."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import JSON, Date, ForeignKey, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base, TimestampMixin, UUIDPk

GOAL_TYPES = ("long", "monthly", "weekly")
GOAL_STATUSES = ("active", "completed", "cancelled")
BLOCK_TYPES = ("school", "class", "study", "free")
PLAN_STATUSES = ("draft", "active", "done")


class Goal(Base, UUIDPk, TimestampMixin):
    """هدف بلندمدت / ماهانه / هفتگی."""

    __tablename__ = "goals"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(16))  # long/monthly/weekly
    title: Mapped[str] = mapped_column(String(200))
    target_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), default="active")


class TimeBlock(Base, UUIDPk):
    """زمان ثابت هفتگی — ۰=شنبه ... ۶=جمعه."""

    __tablename__ = "time_blocks"
    __table_args__ = (UniqueConstraint("student_id", "day_of_week", "start_time",
                                       "end_time", "block_type", name="uq_time_block"),)

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    day_of_week: Mapped[int] = mapped_column(Integer)  # ۰=شنبه ... ۶=جمعه
    start_time: Mapped[str] = mapped_column(Time)
    end_time: Mapped[str] = mapped_column(Time)
    block_type: Mapped[str] = mapped_column(String(16))  # school/class/study/free
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)


class Plan(Base, UUIDPk, TimestampMixin):
    """برنامه روزانه — آیتم‌ها در JSON."""

    __tablename__ = "plans"
    __table_args__ = (UniqueConstraint("student_id", "date", name="uq_plan_date"),)

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)
    items: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="draft")
