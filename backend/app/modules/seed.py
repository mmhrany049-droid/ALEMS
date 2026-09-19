"""مقادیر پیش‌فرض برنامه — درخت دروس پایه و اتصال رویدادها.

دروس پیش‌فرض نسخه ۱ (بر اساس رشته): ریاضی، حسابان، آمار و احتمال، هندسه،
فیزیک، شیمی، زیست و... — اجرای idempotent (در هر راه‌اندازی فقط موارد جاافتاده ساخته می‌شود).
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.events import event_bus
from app.modules.academic.models import Subject
from app.modules.activity.service import rebuild_review_queue

logger = logging.getLogger("alems.seed")

# درخت دروس پیش‌فرض — (نام درس، فصل‌های نمونه)
SUBJECT_TEMPLATES: dict[str, list[str]] = {
    "ریاضی": ["مجموعه", "نابرابری", "توان و ریشه", "عبارت‌های جبری"],
    "حسابان": ["تابع", "حد", "مشتق", "کاربرد مشتق"],
    "آمار و احتمال": ["آمار توصیفی", "احتمال", "متغیر تصادفی"],
    "هندسه": ["هندسه تحلیلی", "دایره", "تبدیل‌های هندسی"],
    "فیزیک": ["حرکت‌شناسی", "دینامیک", "نیرو", "انرژی", "الکتریسیته"],
    "شیمی": ["ساختار اتم", "پیوند شیمیایی", "استوکیومتری", "محلول‌ها"],
    "زیست": ["سلول", "بافت‌های گیاهی", "گوارش", "تنفس", "گردش خون"],
    "ادبیات": ["آرایه‌های ادبی", "دستور زبان", "بازنویسی"],
    "عربی": ["قواعد صرف", "قواعد نحو", "ترجمه"],
    "دینی": ["توحید", "نبوت", "معاد"],
    "زبان انگلیسی": ["Grammar", "Vocabulary", "Reading"],
}

FIELD_SUBJECTS: dict[str, list[str]] = {
    "ریاضی": ["حسابان", "هندسه", "آمار و احتمال", "فیزیک", "شیمی", "گسسته"],
    "تجربی": ["حسابان", "آمار و احتمال", "هندسه", "فیزیک", "شیمی", "زیست"],
    "انسانی": ["ریاضی", "آمار و احتمال", "اقتصاد", "روان‌شناسی", "جامعه‌شناسی", "فلسفه و منطق"],
}

COMMON_SUBJECTS = ["ادبیات", "عربی", "دینی", "زبان انگلیسی"]

GRADES = ["دهم", "یازدهم", "دوازدهم"]


def ensure_subjects(db: Session) -> int:
    """ساخت دروس پیش‌فرض برای همه رشته/پایه‌ها (اگر وجود نداشته باشند)."""
    created = 0
    rows = db.execute(select(Subject.name, Subject.field, Subject.grade)).all()
    existing = {(n, f, g) for n, f, g in rows}

    def add_subject(name: str, field: str, grade: str, order: int) -> None:
        nonlocal created
        if (name, field, grade) in existing:
            return
        db.add(Subject(name=name, field=field, grade=grade, order_index=order))
        existing.add((name, field, grade))
        created += 1

    for field, subjects in FIELD_SUBJECTS.items():
        for grade in GRADES:
            for order, name in enumerate(subjects):
                add_subject(name, field, grade, order)
            # دروس عمومی فقط در پایه دوازدهم برای کنکور
            if grade == "دوازدهم":
                for order, name in enumerate(COMMON_SUBJECTS):
                    add_subject(name, field, grade, 10 + order)

    if created:
        db.commit()
    return created


def ensure_fallback_subject(db: Session) -> None:
    """درس «عمومی» برای کتاب‌هایی بدون درس مشخص."""
    from app.modules.academic.models import Subject as S

    if db.scalar(select(S).where(S.name == "عمومی")) is None:
        db.add(S(name="عمومی", field="ریاضی", grade="دهم", order_index=999))
        db.commit()


def _on_question_marks_changed(payload: dict) -> None:
    """اتصال رویداد: تغییر تیک → به‌روزرسانی صف مرور (تیک مرور/مهم/سخت وارد صف می‌شوند)."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        import uuid as _uuid

        rebuild_review_queue(db, _uuid.UUID(payload["student_id"]))
        logger.debug("صف مرور پس از تغییر تیک سوال %s به‌روزرسانی شد", payload.get("question_id"))
    finally:
        db.close()


def _on_test_records_created(payload: dict) -> None:
    """اتصال رویداد: ثبت تست → به‌روزرسانی خودکار صف مرور."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        import uuid as _uuid

        rebuild_review_queue(db, _uuid.UUID(payload["student_id"]))
        logger.debug("صف مرور پس از ثبت %s تست به‌روزرسانی شد", payload.get("count"))
    finally:
        db.close()


def setup_events() -> None:
    """اتصال شنونده‌های رویداد (یک‌بار)."""
    event_bus.subscribe("test_records.created", _on_test_records_created)
    event_bus.subscribe("question_marks.changed", _on_question_marks_changed)


def ensure_defaults(db: Session) -> None:
    """اجرا در هر راه‌اندازی: دروس پیش‌فرض + رویدادها."""
    ensure_subjects(db)
    ensure_fallback_subject(db)
    setup_events()
