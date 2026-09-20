#!/usr/bin/env python3
"""سناریوی «روز اول دانش‌آموز» — ALEMS نسخه ۲ (فاز ۸، doc 14/16).

یک دانش‌آموز تازه از ثبت‌نام تا پایان روز اول:
   ۱. ثبت‌نام + پروفایل کنکوری             ۲. import کتاب TOC-only (بدون سوال — بی‌صدا موفق)
   ۳. import کتاب کار با سوال              ۴. علامت‌گذاری موضوع‌های تدریس‌شده
   ۵. check-in انرژی/تمرکز                 ۶. ظرفیت امروز (≠ وقت آزاد)
   ۷. جلسه تست سریع + نمره‌گذاری           ۸. صف مرور (غلط وارد صف می‌شود)
   ۹. ثبت آزمون آزمایشی نزدیک            ۱۰. ساخت برنامه هفته (با منبع واقعی: مرور+آزمون)
  ۱۱. نقش امروز (Today Hub — doc 07.6)   ۱۲. پیوستگی و امتیاز
  ۱۳. پشتیبان‌گیری پایان روز

اجرا:
    python3 scripts/day_one_scenario.py            # روی http://127.0.0.1:8010
    ALEMS_BASE=http://127.0.0.1:8010 python3 scripts/day_one_scenario.py
خروجی: گام‌های فارسی با ✓/✗ و خلاصه پایانی؛ کد خروج ۰ یعنی همه گام‌ها موفق.
"""
from __future__ import annotations

import datetime as dt


from zoneinfo import ZoneInfo

_TEHRAN = ZoneInfo("Asia/Tehran")


def _tehran_today() -> dt.date:
    """«امروز» بر مبنای Asia/Tehran — همان ساعت محصول (NFR منطقه زمانی).

    dt.date.today() تاریخ محلیِ ماشین را می‌گیرد (در sandbox = UTC) و در
    پنجرهٔ نیمه‌شب تهران (۲۰:۳۰ تا ۰۰:۰۰ UTC) یک روز از محصول عقب می‌افتد؛
    نتیجه: override روی «دیروز» و انتظارات یک روز شیفت‌شده.
    """
    return dt.datetime.now(_TEHRAN).date()

import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE = os.environ.get("ALEMS_BASE", "http://127.0.0.1:8010").rstrip("/") + "/api/v1"
PASSWORD = os.environ.get("ALEMS_PASSWORD", "pass1234")
ROOT = Path(__file__).resolve().parents[1]
TOC_SAMPLE = ROOT / "examples" / "toc-only-book.json"

FAILS: list[str] = []


def step(no: int, title: str, cond: bool, detail: str = "") -> None:
    mark = "✓" if cond else "✗"
    print(f"{mark} گام {no} — {title}" + (f" | {detail}" if detail else ""))
    if not cond:
        FAILS.append(f"{no}. {title} {detail}")


def req(method: str, path: str, body=None, token: str | None = None):
    r = urllib.request.Request(BASE + path, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(r, data, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def fa(n) -> str:
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def main() -> int:
    print(f"سناریوی روز اول دانش‌آموز — {BASE}")
    # health در ریشه است (نه زیر /api/v1)
    try:
        with urllib.request.urlopen(BASE.replace("/api/v1", "") + "/health", timeout=10) as resp:
            body = json.loads(resp.read())
            health = body.get("data") or body  # envelope → data
            st = 200 if health.get("status") == "ok" else 0
    except Exception as e:
        health, st = {"error": str(e)}, 0
    step(0, "سرور زنده است", st == 200,
         f"نسخه {health.get('version', '?')} — امروز {health.get('today_jalali', '?')}")
    if st != 200:
        print("سرور در دسترس نیست — backend را روی پورت 8010 اجرا کن (scripts/run.sh).")
        return 1

    suffix = uuid.uuid4().hex[:8]
    email = f"day-one-{suffix}@example.com"

    # ۱) ثبت‌نام + پروفایل
    st, r = req("POST", "/auth/register", {"email": email, "password": PASSWORD})
    token = (r.get("data") or {}).get("access_token")
    step(1, "ثبت‌نام", st == 200 and bool(token), email)
    if not token:
        return 1
    st, r = req("PUT", "/students/me", {"grade": "دوازدهم", "track": "تجربی", "target": "کنکور سراسری"}, token)
    step(1, "پروفایل کنکوری", st == 200 and (r.get("data") or {}).get("track") == "تجربی")

    # ۲) کتاب TOC-only — بدون هیچ سوال، بی‌صدا موفق (قید کاربر: بدون خطای «حداقل یک سوال»)
    toc = json.loads(TOC_SAMPLE.read_text(encoding="utf-8"))
    st, r = req("POST", "/resources/import-book", toc, token)
    data = r.get("data") or {}
    counts = ((data.get("resource") or {}).get("counts")) or {}
    step(2, "import کتاب TOC-only (بدون سوال)", st == 200 and counts.get("questions", -1) == 0,
         f"{fa(counts.get('topics', 0))} موضوع، {fa(counts.get('questions', 0))} سوال — بدون خطای «حداقل یک سوال»")

    # ۳) کتاب کار با سوال
    book = {
        "title": f"ریاضی تجربی — دفتر کار روز اول ({suffix})",
        "publisher": "نمونه",
        "subject": "ریاضی",
        "chapters": [
            {
                "title": "فصل ۱ — تابع",
                "topics": [
                    {
                        "title": "مفهوم تابع",
                        "questions": [{"number": i, "answer": str((i % 4) + 1), "difficulty": (i % 3) + 2} for i in range(1, 13)],
                    },
                    {"title": "انواع توابع", "questions": [{"number": i, "answer": "2"} for i in range(1, 7)]},
                ],
            },
            {"title": "آزمون فصل ۱", "topics": [{"title": "کاربرگ آزمون", "questions": [{"number": i, "answer": "1"} for i in range(1, 5)]}]},
        ],
    }
    st, r = req("POST", "/resources/import-book", book, token)
    data = r.get("data") or {}
    res = data.get("resource") or {}
    rid = res.get("id") or data.get("resource_id") or data.get("id")
    counts = res.get("counts") or {}
    step(3, "import کتاب کار با سوال", st == 200 and bool(rid), f"{fa(counts.get('questions', 0))} سوال")

    # ۴) موضوع‌های تدریس‌شده (taught ≠ learned — doc 02)
    st, r = req("GET", f"/resources/{rid}/tree", None, token)
    topics: list[dict] = []

    def _walk(node):
        for t in node.get("children", []) or []:
            topics.append(t)
            _walk(t)

    tdata = r.get("data") or {}
    for root in tdata.get("tree") or []:
        topics.append(root)
        _walk(root)
    topics = [t for t in topics if not t.get("is_structural")]
    with_q = [t for t in topics if t.get("question_count", 0) > 0]
    taught_ids = [t["id"] for t in (with_q[:2] or topics[:2]) if t.get("id")]
    st, r = req("PUT", "/students/me/taught-topics", {"items": [{"topic_id": i, "taught": True} for i in taught_ids]}, token)
    step(4, "علامت «تدریس شده»", st == 200 and len(taught_ids) > 0, f"{fa(len(taught_ids))} موضوع")

    # ۵) check-in
    st, r = req("POST", "/students/me/checkin",
                {"energy": 4, "focus": 3, "motivation": 4, "stress": 2, "fatigue": 2}, token)
    step(5, "check-in انرژی/تمرکز", st == 200, (r.get("data") or {}).get("date_jalali", ""))

    # ۶) ظرفیت (وقت آزاد ≠ ظرفیت)
    st, r = req("GET", "/capacity", None, token)
    cap = r.get("data") or {}
    step(6, "ظرفیت امروز محاسبه شد", st == 200 and "available_minutes" in cap,
         f"{fa(cap.get('available_minutes', '?'))} دقیقه (ضریب حالت {cap.get('state_factor', '?')})")

    # ۷) جلسه تست سریع: ۴ درست، ۱ غلط، ۱ نزده (نزده ≠ غلط — doc 02)
    st, r = req("POST", "/test-sessions", {"mode": "untimed", "resource_id": rid, "count": 6, "label": "جلسه روز اول"}, token)
    sess = (r.get("data") or {}).get("session") or {}
    qs = (r.get("data") or {}).get("questions") or []
    sid = sess.get("id")
    results = ["correct", "correct", "wrong", "correct", "blank", "correct"]
    items = []
    for q, res_ in zip(qs, results):
        if res_ == "blank":
            items.append({"question_id": q["question_id"], "status": "unanswered"})
        else:
            items.append({"question_id": q["question_id"], "status": "answered", "result": res_})
    st1, _ = req("POST", f"/test-sessions/{sid}/records", {"items": items}, token)
    st2, r = req("POST", f"/test-sessions/{sid}/finish", {"actual_duration": 6 * 60}, token)
    fin = (r.get("data") or {}).get("session") or {}
    step(7, "جلسه تست + نمره‌گذاری", st == 200 and st1 == 200 and st2 == 200,
         f"درست {fa(fin.get('correct_count', '?'))} · غلط {fa(fin.get('wrong_count', '?'))} · نزده {fa(fin.get('blank_count', fin.get('unanswered_count', '?')))}")

    # ۸) صف مرور — غلط وارد صف شد (V2-R01)
    st, r = req("GET", "/reviews/queue", None, token)
    q_items = (r.get("data") or {}).get("items") or []
    step(8, "صف مرور — غلط تازه در صف", st == 200 and len(q_items) >= 1, f"{fa(len(q_items))} آیتم")

    # ۹) آزمون آزمایشی ۷ روز دیگر
    exam_date = (_tehran_today() + dt.timedelta(days=7)).isoformat()
    st, r = req("POST", "/exams", {"title": "آزمون آزمایشی قلم‌چی", "kind": "mock",
                                   "scheduled_date": exam_date, "subjects": ["زیست شناسی", "ریاضی"]}, token)
    step(9, "ثبت آزمون نزدیک", st == 200, (r.get("data") or {}).get("scheduled_date_jalali", exam_date))

    # ۱۰) برنامه هفته — حالا منبع واقعی هست (مرور + آمادگی آزمون)
    st, r = req("POST", "/plans/generate-week", {}, token)
    gw = r.get("data") or {}
    created = gw.get("created", gw.get("tasks_created", "?"))
    step(10, "ساخت برنامه هفته (pipeline)", st == 200, f"{fa(created)} کار جدید")

    # ۱۱) Today Hub — همه بخش‌های doc 07.6 + آزمون نزدیک
    st, r = req("GET", "/today", None, token)
    d = r.get("data") or {}
    has_all = all(k in d for k in ("greeting", "checkin", "capacity", "plan_items", "review_due_count",
                                   "upcoming_exams", "recommendation", "week_sparkline", "week"))
    up = d.get("upcoming_exams") or []
    step(11, "نقش امروز — همه بخش‌های doc 07.6", st == 200 and has_all,
         f"{fa(len(d.get('plan_items', [])))} کار امروز")
    step(11, "آزمون در «آزمون نزدیک» Today نشست", st == 200 and any(e.get("title") == "آزمون آزمایشی قلم‌چی" for e in up))

    # ۱۲) پیوستگی و امتیاز
    st, r = req("GET", "/rewards/summary", None, token)
    s = r.get("data") or {}
    pts = s.get("points_total", 0)
    streak = (s.get("streak") or {}).get("current", 0)
    step(12, "امتیاز و پیوستگی فعال شد", st == 200 and pts > 0 and streak >= 1,
         f"{fa(pts)} امتیاز · پیوستگی {fa(streak)} روز")

    # ۱۳) پشتیبان پایان روز
    st, r = req("POST", "/backup/create", {"label": "پایان روز اول"}, token)
    bid = (r.get("data") or {}).get("id")
    step(13, "پشتیبان‌گیری پایان روز", st == 200 and bool(bid), bid or "")

    print()
    if FAILS:
        print(f"✗ سناریو کامل نشد — {fa(len(FAILS))} گام ناموفق:")
        for f in FAILS:
            print("   •", f)
        return 1
    print("✓ روز اول کامل شد — دانش‌آموز از ثبت‌نام تا پشتیبان‌گیری:")
    print(f"   کتاب TOC-only + کتاب کار، {fa(len(taught_ids))} موضوع تدریس‌شده، جلسه ۶ سوالی،")
    print(f"   {fa(pts)} امتیاز، پیوستگی {fa(streak)} روز، آزمون ۷ روز دیگر در تقویم، پشتیبان «{bid}».")
    return 0


if __name__ == "__main__":
    sys.exit(main())
