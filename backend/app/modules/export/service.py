"""سرویس خروجی — PDF، Excel و JSON کامل (Export Module + مالکیت داده)."""
from __future__ import annotations

import io
import json
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.jalali import format_jalali, format_jalali_long, week_end
from app.core.jalali import week_start as to_week_start
from app.modules.academic.models import Chapter, Question, Resource, Subject, Topic
from app.modules.activity.models import (
    ErrorNote,
    LearningActivity,
    QuestionMark,
    ReviewItem,
    TestRecord,
)
from app.modules.academic.service import question_payload, resource_payload, subject_payload
from app.modules.activity.service import review_item_payload, test_record_payload
from app.modules.exam.models import Exam, ExamAnswer, ExamQuestion, ExamResult
from app.modules.identity.models import User
from app.modules.planning.models import Goal, Plan, TimeBlock
from app.modules.report.service import daily_report, monthly_report, weekly_report
from app.modules.student.models import StudentProfile, StudentState
from app.shared.exceptions import ValidationError


# ---------- PDF ----------

def _fmt_minutes(minutes: dict) -> str:
    if not minutes:
        return "—"
    return " · ".join(f"{k}: {v} دقیقه" for k, v in minutes.items())


def _fmt_tests(tests: dict) -> str:
    if not tests or not tests.get("total"):
        return "تستی ثبت نشده"
    return (f"کل: {tests['total']} · درست: {tests['correct']} · غلط: {tests['wrong']} · "
            f"نزده: {tests['blank']} · درصد کنکوری: {tests.get('percent_konkur', '—')}")


def export_pdf(db: Session, user: User, type_: str, week_start: date | None,
               report_date: date | None, jy: int | None, jm: int | None) -> tuple[bytes, str]:
    """خروجی PDF گزارش (AT-25). خروجی: (bytes، نام فایل)."""
    if type_ == "daily":
        day = report_date or date.today()
        data = daily_report(db, user.id, day)
        title = f"گزارش روزانه — {data['date_label']}"
        sections = [
            {"heading": "خلاصه تست", "rows": [[_fmt_tests(data["tests"])]]},
            {"heading": "فعالیت‌ها", "rows": [[_fmt_minutes(data["activities_minutes"])]]},
            {"heading": "مرور", "rows": [[f"مرور شده: {data['review']['reviewed']} · در انتظار: {data['review']['pending']}"]]},
        ]
        if data.get("state"):
            s = data["state"]
            sections.append({"heading": "وضعیت روز", "rows": [[
                f"انرژی: {s['energy_level']}/5 · حال: {s.get('mood') or '—'} · شرایط: {s.get('study_condition') or '—'}"
            ]]})
        filename = f"alems-daily-{day.isoformat()}.pdf"
    elif type_ == "weekly":
        ws = to_week_start(week_start or date.today())
        data = weekly_report(db, user.id, ws)
        title = f"گزارش هفتگی — {data['week_start_label']} تا {data['week_end_label']}"
        rows = [[d["date_label"], d["tests"]["total"], d["tests"]["correct"],
                 d["tests"]["wrong"], d["tests"]["blank"],
                 d["tests"].get("percent_konkur") or "—", sum(d["activities_minutes"].values())]
                for d in data["per_day"]]
        sections = [
            {"heading": "روند روزانه", "header_row": ["روز", "کل", "درست", "غلط", "نزده", "درصد", "دقیقه فعالیت"],
             "rows": rows},
            {"heading": "خلاصه هفته", "rows": [[_fmt_tests(data["tests"])],
                                               [_fmt_minutes(data["activities_minutes"])]]},
        ]
        if data.get("by_subject"):
            sections.append({
                "heading": "عملکرد به تفکیک درس",
                "header_row": ["درس", "کل", "درست", "غلط", "نزده", "درصد کنکوری"],
                "rows": [[s["subject"], s["total"], s["correct"], s["wrong"], s["blank"],
                          s.get("percent_konkur") if s.get("percent_konkur") is not None else "—"]
                         for s in data["by_subject"]],
            })
        if data.get("mistakes"):
            sections.append({
                "heading": "نوع اشتباهات",
                "header_row": ["نوع", "تعداد", "سهم"],
                "rows": [[m["label"], m["count"], f"{m['share']}٪"] for m in data["mistakes"]],
            })
        filename = f"alems-weekly-{ws.isoformat()}.pdf"
    elif type_ == "monthly":
        if not jy or not jm:
            raise ValidationError("برای گزارش ماهانه، «year» و «month» جلالی الزامی است.")
        data = monthly_report(db, user.id, jy, jm)
        title = f"گزارش ماهانه — {jy}/{jm:02d}"
        sections = [
            {"heading": "خلاصه ماه", "rows": [[_fmt_tests(data["tests"])],
                                              [_fmt_minutes(data["activities_minutes"])]]},
        ]
        if data.get("by_subject"):
            sections.append({
                "heading": "عملکرد به تفکیک درس",
                "header_row": ["درس", "کل", "درست", "غلط", "نزده", "درصد کنکوری"],
                "rows": [[s["subject"], s["total"], s["correct"], s["wrong"], s["blank"],
                          s.get("percent_konkur") if s.get("percent_konkur") is not None else "—"]
                         for s in data["by_subject"]],
            })
        filename = f"alems-monthly-{jy}-{jm:02d}.pdf"
    else:
        raise ValidationError("نوع گزارش نامعتبر است. مقادیر مجاز: daily، weekly، monthly")

    from app.modules.export.pdf import fa_num, build_pdf

    return build_pdf(title, sections), filename


# ---------- Excel ----------

def export_excel(db: Session, user: User) -> tuple[bytes, str]:
    """خروجی Excel شامل فعالیت‌ها، تست‌ها، مرور و عملکرد دروس."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()

    def sheet(name: str, header: list[str], rows: list[list]) -> None:
        ws = wb.create_sheet(name)
        ws.append(header)
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for row in rows:
            ws.append(row)

    # فعالیت‌ها
    acts = db.scalars(select(LearningActivity).where(LearningActivity.student_id == user.id)
                      .order_by(LearningActivity.started_at)).all()
    sheet("فعالیت‌ها", ["نوع", "شروع", "مدت (دقیقه)", "یادداشت"],
          [[a.type, a.started_at.isoformat(), a.duration_minutes, a.note or ""] for a in acts])

    # رکوردهای تست
    recs = db.scalars(select(TestRecord).where(TestRecord.student_id == user.id)
                      .order_by(TestRecord.solved_at)).all()
    sheet("تست‌ها", ["نتیجه", "زمان حل", "مدت (ثانیه)", "نوع اشتباه"],
          [[r.result, r.solved_at.isoformat(), r.duration_seconds or "",
            r.error_note.error_type if r.error_note else ""] for r in recs])

    # عملکرد دروس
    from app.modules.analytics.service import by_subject as subj_stats
    stats = subj_stats(db, user.id, None, None)
    sheet("عملکرد دروس", ["درس", "کل", "درست", "غلط", "نزده", "درصد کنکوری", "درصد بدون غلط"],
          [[s["subject"], s["total"], s["correct"], s["wrong"], s["blank"],
            s.get("percent_konkur") or "", s.get("percent_no_penalty") or ""] for s in stats])

    # صف مرور
    reviews = db.scalars(select(ReviewItem).where(ReviewItem.student_id == user.id)).all()
    sheet("مرور", ["علت", "اولویت", "تاریخ", "وضعیت"],
          [[r.reason, r.priority, r.scheduled_date.isoformat(),
            "انجام شده" if r.status == "done" else "در انتظار"] for r in reviews])

    buf = io.BytesIO()
    wb.remove(wb.active)
    wb.save(buf)
    return buf.getvalue(), "alems-export.xlsx"


# ---------- JSON کامل (مالکیت داده — NFR-06) ----------

def export_json(db: Session, user: User) -> tuple[bytes, str]:
    """خروجی کامل داده‌های کاربر در فرمت باز JSON (AT-26)."""
    import datetime as dt

    def _table(table, *conditions):
        stmt = select(table)
        if conditions:
            stmt = stmt.where(*conditions)
        return [dict(row._mapping) for row in db.execute(stmt)]

    my_exams = select(Exam.id).where(Exam.student_id == user.id)
    data = {
        "meta": {
            "app": settings.app_name,
            "version": settings.app_version,
            "exported_at": dt.datetime.utcnow().isoformat(),
            "owner": user.username,
        },
        "user": _table(User.__table__, User.id == user.id),
        "profile": _table(StudentProfile.__table__, StudentProfile.user_id == user.id),
        "states": _table(StudentState.__table__, StudentState.student_id == user.id),
        "activities": _table(LearningActivity.__table__, LearningActivity.student_id == user.id),
        "test_records": _table(TestRecord.__table__, TestRecord.student_id == user.id),
        "question_marks": _table(QuestionMark.__table__, QuestionMark.student_id == user.id),
        "review_queue": _table(ReviewItem.__table__, ReviewItem.student_id == user.id),
        "goals": _table(Goal.__table__, Goal.student_id == user.id),
        "time_blocks": _table(TimeBlock.__table__, TimeBlock.student_id == user.id),
        "plans": _table(Plan.__table__, Plan.student_id == user.id),
        "exams": _table(Exam.__table__, Exam.student_id == user.id),
        "exam_results": _table(ExamResult.__table__, ExamResult.exam_id.in_(my_exams)),
        "exam_answers": _table(ExamAnswer.__table__, ExamAnswer.exam_id.in_(my_exams)),
        "knowledge_base": {
            "subjects": _table(Subject.__table__),
            "chapters": _table(Chapter.__table__),
            "topics": _table(Topic.__table__),
            "resources": _table(Resource.__table__),
            "questions": _table(Question.__table__),
        },
    }
    payload = json.loads(json.dumps(data, default=str, ensure_ascii=False))
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"), "alems-backup.json"
