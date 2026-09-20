#!/usr/bin/env python3
"""چک‌لیست پذیرش ALEMS نسخه ۲ — doc 15 (V2-B01..05, T01..05, R01..04, P01..04, A01..02, U01..04, S01..02).

اجرا روی سرور زنده (پیش‌فرض http://127.0.0.1:8010) + بازرسی منبع برای آیتم‌های UI:
    python3 scripts/v2_acceptance.py
    ALEMS_BASE=http://127.0.0.1:8010 python3 scripts/v2_acceptance.py

هر ردیف دقیقاً همان تست doc 15 است؛ خروجی جدول ✓/✗ و کد خروج ۰ یعنی همه پذیرفته شدند.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path


from zoneinfo import ZoneInfo

_TEHRAN = ZoneInfo("Asia/Tehran")


def _tehran_today() -> dt.date:
    """«امروز» بر مبنای Asia/Tehran — همان ساعت محصول (NFR منطقه زمانی).

    dt.date.today() تاریخ محلیِ ماشین را می‌گیرد (در sandbox = UTC) و در
    پنجرهٔ نیمه‌شب تهران (۲۰:۳۰ تا ۰۰:۰۰ UTC) یک روز از محصول عقب می‌افتد؛
    نتیجه: override روی «دیروز» و انتظارات یک روز شیفت‌شده.
    """
    return dt.datetime.now(_TEHRAN).date()


BASE = os.environ.get("ALEMS_BASE", "http://127.0.0.1:8010").rstrip("/")
API = BASE + "/api/v1"
PASS = "pass1234"
ROOT = Path(__file__).resolve().parents[1]
FE = ROOT / "frontend"
TOC_SAMPLE = ROOT / "examples" / "toc-only-book.json"

RESULTS: list[tuple[str, str, bool, str]] = []  # (id, desc, ok, detail)


def check(cid: str, desc: str, cond: bool, detail: str = "") -> bool:
    RESULTS.append((cid, desc, bool(cond), detail))
    print(f"{'✓' if cond else '✗'} {cid} — {desc}" + (f" | {detail}" if detail else ""))
    return bool(cond)


def req(method: str, path: str, body=None, token: str | None = None, base: str = API):
    r = urllib.request.Request(base + path, method=method)
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


def register(tag: str) -> tuple[str, str]:
    email = f"v2acc-{tag}-{uuid.uuid4().hex[:8]}@example.com"
    st, r = req("POST", "/auth/register", {"email": email, "password": PASS})
    assert st == 200, (st, r)
    return email, r["data"]["access_token"]


def workbook(tag: str, tok: str) -> dict:
    """کتاب کار: topic1 = ۱۲ سوال، topic2 = ۶ سوال، فصل آزمون = ۴ سوال."""
    book = {
        "title": f"کتاب پذیرش {tag} ({uuid.uuid4().hex[:6]})",
        "chapters": [
            {
                "title": "فصل ۱",
                "topics": [
                    {"title": "موضوع الف", "questions": [{"number": i, "answer": str((i % 4) + 1)} for i in range(1, 13)]},
                    {"title": "موضوع ب", "questions": [{"number": i, "answer": "2"} for i in range(1, 7)]},
                ],
            },
        ],
    }
    st, r = req("POST", "/resources/import-book", book, tok)
    assert st == 200, (st, r)
    return r["data"]["resource"]


def tree_topics(tok: str, rid: str) -> list[dict]:
    st, r = req("GET", f"/resources/{rid}/tree", None, tok)
    out: list[dict] = []

    def walk(n):
        out.append(n)
        for c in n.get("children") or []:
            walk(c)

    for root in (r.get("data") or {}).get("tree") or []:
        walk(root)
    return out


# --- B: کتاب و Import ------------------------------------------------------------------------------

def section_books():
    print("\n[کتاب و Import]")
    _, tok = register("books")

    # B01 + B02 + B04 با نمونه TOC-only
    toc = json.loads(TOC_SAMPLE.read_text(encoding="utf-8"))
    st, r = req("POST", "/resources/import-book", toc, tok)
    counts = ((r.get("data") or {}).get("resource") or {}).get("counts") or {}
    check("V2-B01", "Import TOC-only بدون questions موفق است",
          st == 200 and counts.get("questions") == 0 and counts.get("topics", 0) > 0,
          f"{fa(counts.get('topics', 0))} موضوع، {fa(counts.get('questions', 0))} سوال")

    rid = ((r.get("data") or {}).get("resource") or {}).get("id")
    topics = tree_topics(tok, rid)
    sub_only = [t for t in topics if (t.get("children") and t.get("question_count", 0) == 0)]
    check("V2-B02", "topic فقط با subtopics و بدون سوال مستقیم موفق است",
          len(sub_only) >= 1, f"{fa(len(sub_only))} نمونه (مثلاً «{sub_only[0]['title'] if sub_only else '-'}»)")

    konkur = [t for t in topics if t.get("block_type") == "konkur"]
    exams = [t for t in topics if t.get("block_type") == "chapter_exam"]
    check("V2-B04", "block_type از عنوان آزمون/کنکور استنتاج می‌شود",
          len(konkur) >= 1 and len(exams) >= 1,
          f"konkur={fa(len(konkur))} · chapter_exam={fa(len(exams))}")

    # B03 — سوال بدون answer
    bad = {"title": f"کتاب ناقص {uuid.uuid4().hex[:6]}",
           "chapters": [{"title": "فصل", "topics": [{"title": "موضوع", "questions": [{"number": 1}]}]}]}
    st, r = req("POST", "/resources/import-book", bad, tok)
    msg = (r.get("error") or {}).get("message") or ""
    persian = bool(msg) and any("\u0600" <= ch <= "\u06FF" for ch in msg)
    check("V2-B03", "سوال بدون answer رد می‌شود با پیام فارسی", st == 422 and persian, msg[:60])

    # B05 — کتاب تکراری
    st2, _ = req("POST", "/resources/import-book", toc, tok)
    check("V2-B05", "کتاب تکراری 409", st2 == 409, f"status={st2}")


# --- T: تست ------------------------------------------------------------------------------------------

def section_tests() -> tuple[str, str]:
    print("\n[تست]")
    _, tok = register("tests")
    res = workbook("T", tok)
    rid = res["id"]
    topics = [t for t in tree_topics(tok, rid) if t.get("question_count", 0) > 0]
    t1 = topics[0]

    # T01 — Range + odd
    st, r = req("POST", "/test-sessions",
                {"mode": "untimed", "resource_id": rid, "from_number": 1, "to_number": 9, "parity": "odd"}, tok)
    qs = (r.get("data") or {}).get("questions") or []
    nums = [q.get("number") for q in qs]
    check("V2-T01", "Range + odd فقط فردها",
          st == 200 and len(nums) >= 3 and all(n is not None and n % 2 == 1 and 1 <= n <= 9 for n in nums),
          f"شماره‌ها: {sorted(set(nums))}")

    # T05 — history append-only برای تکرار سوال (اول غلط، بعد درست)
    sid = r["data"]["session"]["id"]
    q_repeat = qs[0]
    q_wrong = qs[1]
    req("POST", f"/test-sessions/{sid}/records",
        {"items": [{"question_id": q_repeat["question_id"], "status": "answered", "result": "wrong"}]}, tok)
    req("POST", f"/test-sessions/{sid}/records",
        {"items": [{"question_id": q_repeat["question_id"], "status": "answered", "result": "correct"}]}, tok)
    st, r = req("GET", f"/test-sessions/{sid}", None, tok)
    attempts = [a for a in (r.get("data") or {}).get("attempts") or [] if a["question_id"] == q_repeat["question_id"]]
    check("V2-T05", "history append-only برای تکرار سوال",
          len(attempts) == 2 and {a["result"] for a in attempts} == {"wrong", "correct"},
          f"{fa(len(attempts))} رکورد برای یک سوال")

    # T02 — finish ایدمپوتنت
    st1, r1 = req("POST", f"/test-sessions/{sid}/finish", {}, tok)
    st2, r2 = req("POST", f"/test-sessions/{sid}/finish", {}, tok)
    s1 = (r1.get("data") or {}).get("session") or {}
    s2 = (r2.get("data") or {}).get("session") or {}
    check("V2-T02", "finish ایدمپوتنت",
          st1 == 200 and st2 == 200 and (r2.get("data") or {}).get("idempotent") is True
          and s1.get("correct_count") == s2.get("correct_count"),
          f"idempotent={((r2.get('data') or {}).get('idempotent'))}")

    # T04 — درصد کنکوری نمونه استاندارد: (C − k·W)/Total با k=0.33
    st, r = req("POST", "/test-sessions", {"mode": "untimed", "resource_id": rid, "topic_ids": [t1["id"]], "count": 4}, tok)
    sid2 = r["data"]["session"]["id"]
    qq = r["data"]["questions"]
    marks = [("correct", qq[0]), ("correct", qq[1]), ("wrong", qq[2]), ("unanswered", qq[3])]
    items = [{"question_id": q["question_id"], "status": "unanswered"} if m == "unanswered"
             else {"question_id": q["question_id"], "status": "answered", "result": m} for m, q in marks]
    req("POST", f"/test-sessions/{sid2}/records", {"items": items}, tok)
    st, r = req("POST", f"/test-sessions/{sid2}/finish", {}, tok)
    s = (r.get("data") or {}).get("session") or {}
    c, w, total, k = s.get("correct_count", 0), s.get("wrong_count", 0), s.get("total_count", 4), s.get("penalty_k", 0.33)
    exp_konkur = round((c - k * w) / total * 100, 1)
    exp_raw = round(c / total * 100, 1)
    check("V2-T04", "درصد کنکوری نمونه استاندارد",
          abs((s.get("percent_konkur") or -1) - exp_konkur) < 0.6 and abs((s.get("percent_no_penalty") or -1) - exp_raw) < 0.6,
          f"{fa(s.get('percent_konkur'))}٪ کنکوری در برابر {fa(s.get('percent_no_penalty'))}٪ خام (k={k})")

    # T03 — past import با not_entered (ثبت‌نشده ≠ غلط)
    st, r = req("POST", "/tests/past-import", {
        "resource_id": rid, "topic_id": t1["id"], "label": "کنکور پارسال",
        "items": [
            {"number": 40, "status": "answered", "answer": "1", "correct_answer": "1"},
            {"number": 41, "status": "not_entered"},
            {"number": 42, "status": "not_entered"},
        ],
    }, tok)
    ps = (r.get("data") or {}).get("session") or {}
    st_ov, r_ov = req("GET", "/analytics/overview", None, tok)
    acc = (r_ov.get("data") or {}).get("accuracy") or {}
    check("V2-T03", "past import با not_entered",
          st == 200 and ps.get("not_entered_count") == 2 and acc.get("not_entered", 0) >= 2
          and acc.get("wrong", 0) == 1,  # not_entered هرگز به‌عنوان غلط شمرده نمی‌شود
          f"not_entered={fa(ps.get('not_entered_count'))} · wrong کل={fa(acc.get('wrong'))}")

    # R01/R03 — غلط وارد صف می‌شود؛ غلط دوم → critical
    st, r = req("GET", "/reviews/queue", None, tok)
    items = (r.get("data") or {}).get("items") or []
    wrong_item = next((i for i in items if i["question_id"] == q_wrong["question_id"]), None)
    check("V2-R01", "غلط وارد صف می‌شود", wrong_item is not None,
         f"{fa(len(items))} آیتم در صف" if not wrong_item else "")

    # R03: همان سوال در جلسهٔ دوم هم غلط → wrong_count≥2 → critical
    st, r = req("POST", "/test-sessions", {"mode": "untimed", "resource_id": rid, "topic_ids": [t1["id"]], "count": 4}, tok)
    sid3 = r["data"]["session"]["id"]
    q3 = next((q for q in r["data"]["questions"] if q["question_id"] == q_wrong["question_id"]), None)
    rec_items = []
    if q3 is None:  # اگر در انتخاب نبود، با شمارهٔ مستقیم ثبت می‌کنیم
        rec_items.append({"number": q_wrong["number"], "status": "answered", "result": "wrong"})
    else:
        rec_items.append({"question_id": q3["question_id"], "status": "answered", "result": "wrong"})
    # یک غلط تازهٔ دیگر — برای تست postpone (complete نشده)
    q_post = next((q for q in r["data"]["questions"] if q["question_id"] not in (q_repeat["question_id"], (q3 or {}).get("question_id"))), None)
    if q_post:
        rec_items.append({"question_id": q_post["question_id"], "status": "answered", "result": "wrong"})
    req("POST", f"/test-sessions/{sid3}/records", {"items": rec_items}, tok)
    req("POST", f"/test-sessions/{sid3}/finish", {}, tok)
    st, r = req("GET", "/reviews/queue", None, tok)
    items = (r.get("data") or {}).get("items") or []
    crit = next((i for i in items if i["question_id"] == q_wrong["question_id"]), None)
    check("V2-R03", "critical برای غلط ≥۲", crit is not None and crit.get("critical") is True and crit.get("wrong_count", 0) >= 2,
         f"wrong_count={fa((crit or {}).get('wrong_count'))}")

    # R02 — چرخه ۱ سپس ۳
    first_cycle = (crit or {}).get("next_interval_days")
    st, r = req("POST", f"/reviews/{(crit or {}).get('id')}/complete", {}, tok)
    after = r.get("data") or {}
    check("V2-R02", "چرخه ۱ سپس ۳",
          first_cycle == 1 and st == 200 and after.get("next_interval_days") == 3,
          f"interval قبل={fa(first_cycle)} → بعد={fa(after.get('next_interval_days'))}")

    # R04 — postpone روی آیتم تازه (complete نشده)
    st, rq = req("GET", "/reviews/queue", None, tok)
    fresh = (rq.get("data") or {}).get("items") or []
    target = next((i for i in fresh if q_post and i["question_id"] == q_post["question_id"]), None) \
        or next((i for i in fresh if i.get("status") != "done"), None)
    if target is None:
        check("V2-R04", "postpone", False, "آیتمی برای postpone نبود")
        return tok, rid
    st, r = req("POST", f"/reviews/{target['id']}/postpone", {"days": 2}, tok)
    new_sched = (r.get("data") or {}).get("scheduled_date") or ""
    expected = (_tehran_today() + dt.timedelta(days=2)).isoformat()
    check("V2-R04", "postpone", st == 200 and new_sched.startswith(expected),
         f"schedule جدید: {new_sched}")

    # A01/A02 با همان داده‌ها
    st, r = req("GET", "/analytics/overview", None, tok)
    ov = r.get("data") or {}
    sep = all(k in ov for k in ("coverage", "accuracy", "volume"))
    distinct = (ov.get("coverage", {}).get("questions_ratio") is not None
                and ov.get("accuracy", {}).get("answered_accuracy") is not None
                and ov.get("volume", {}).get("attempts") is not None)
    check("V2-A01", "overview هر سه متریک را جدا دارد", st == 200 and sep and distinct,
          f"coverage={ov.get('coverage', {}).get('questions_ratio')} · accuracy={ov.get('accuracy', {}).get('answered_accuracy')} · attempts={ov.get('volume', {}).get('attempts')}")

    st, r = req("GET", "/export/json", None, tok)
    ex = r.get("data") or {}
    check("V2-A02", "export json شامل کتاب و attempt",
          st == 200 and len(ex.get("books") or []) >= 1 and len(ex.get("attempts") or []) >= 1,
          f"{fa(len(ex.get('books') or []))} کتاب · {fa(len(ex.get('attempts') or []))} attempt")
    return tok, rid


# --- P: برنامه -----------------------------------------------------------------------------------------

def section_planning():
    print("\n[برنامه]")
    _, tok = register("plan")
    res = workbook("P", tok)
    rid = res["id"]
    topics = [t for t in tree_topics(tok, rid) if t.get("question_count", 0) > 0]
    req("PUT", "/students/me/taught-topics",
        {"items": [{"topic_id": topics[0]["id"], "taught": True}]}, tok)
    req("POST", "/students/me/checkin",
        {"energy": 4, "focus": 4, "motivation": 4, "stress": 2, "fatigue": 2}, tok)

    # یک غلط → آیتم مرور تا planner منبع داشته باشد
    st, r = req("POST", "/test-sessions", {"mode": "untimed", "resource_id": rid, "count": 3}, tok)
    sid = r["data"]["session"]["id"]
    qs = r["data"]["questions"]
    req("POST", f"/test-sessions/{sid}/records", {"items": [
        {"question_id": qs[0]["question_id"], "status": "answered", "result": "wrong"},
        {"question_id": qs[1]["question_id"], "status": "answered", "result": "correct"},
    ]}, tok)
    req("POST", f"/test-sessions/{sid}/finish", {}, tok)

    # P01 — Today حداقل ۵ بخش سند ۷
    st, r = req("GET", "/today", None, tok)
    d = r.get("data") or {}
    sections = [k for k in ("greeting", "checkin", "capacity", "plan_items", "review_due_count",
                            "upcoming_exams", "recommendation", "week_sparkline") if k in d]
    check("V2-P01", "Today حداقل ۵ بخش سند ۷", st == 200 and len(sections) >= 5, f"{fa(len(sections))} بخش حاضر")

    # P02 — school override ظرفیت را عوض می‌کند
    today_iso = _tehran_today().isoformat()
    st, r0 = req("GET", "/capacity", None, tok)
    before = (r0.get("data") or {}).get("available_minutes")
    st, r = req("POST", "/school-override",
                {"date": today_iso, "school_off": False,
                 "blocks": [{"kind": "school", "start": "08:00", "end": "14:00", "title": "مدرسه"}]}, tok)
    st, r1 = req("GET", "/capacity", None, tok)
    after = (r1.get("data") or {}).get("available_minutes")
    check("V2-P02", "school override ظرفیت را عوض می‌کند",
          st == 200 and before is not None and after is not None and after < before,
          f"{fa(before)} → {fa(after)} دقیقه")

    # P03 — task قفل‌شده بعد از regenerate می‌ماند
    st, g = req("POST", "/plans/generate-week", {}, tok)
    week_start = (g.get("data") or {}).get("week_start") or today_iso
    ws = dt.date.fromisoformat(week_start)
    st, r = req("GET", f"/plans/{today_iso}", None, tok)
    tasks = (r.get("data") or {}).get("tasks") or []
    if not tasks:  # امروز خالی بود → دیگر روزهای هفتهٔ جاری
        # allocate ممکن است کار را در هر روزِ هفته گذاشته باشد (مثلاً امروز با
        # override ظرفیت صفر دارد و کارها به روزهای دیگر هفته رفته‌اند)؛ اول
        # امروز به بعد، بعد روزهای گذشتهٔ همان هفته — معیار V2-P03 خودِ
        # «ماندن قفل بعد از regenerate» است، نه روزِ خاصی.
        week_days = [(ws + dt.timedelta(days=i)).isoformat() for i in range(7)]
        ordered = [d for d in week_days if d > today_iso] + [d for d in week_days if d < today_iso]
        for day in ordered:
            st, r = req("GET", f"/plans/{day}", None, tok)
            tasks = (r.get("data") or {}).get("tasks") or []
            if tasks:
                today_iso = day
                break
    ok3 = False
    detail3 = "کاری برای قفل وجود نداشت"
    if tasks:
        t0 = tasks[0]
        st, _ = req("POST", f"/plans/tasks/{t0['id']}/lock", {"locked": True}, tok)
        req("POST", "/plans/generate-week", {}, tok)
        st, r = req("GET", f"/plans/{today_iso}", None, tok)
        after_tasks = (r.get("data") or {}).get("tasks") or []
        locked = next((t for t in after_tasks if t["id"] == t0["id"]), None)
        ok3 = locked is not None and locked.get("locked") is True
        detail3 = "قفل بعد از regenerate ماند" if ok3 else "قفل گم شد!"
    check("V2-P03", "task قفل‌شده بعد از regenerate می‌ماند", ok3, detail3)

    # P04 — recovery همه را به فردا نمی‌ریزد
    st, r = req("POST", "/plans/recover", {}, tok)
    tomorrow = (_tehran_today() + dt.timedelta(days=1)).isoformat()
    st2, r2 = req("GET", f"/plans/{tomorrow}", None, tok)
    tom_tasks = (r2.get("data") or {}).get("tasks") or []
    recovered = [t for t in tom_tasks if t.get("source") == "recovered"]
    # پخش شدن: یا هیچی به فردا نریخته (همه در همان روز/قبل انجام شده) یا تعداد معقول است
    week_counts = []
    for i in range(0, 7):
        day = (_tehran_today() + dt.timedelta(days=i)).isoformat()
        _, rr = req("GET", f"/plans/{day}", None, tok)
        week_counts.append(len([t for t in ((rr.get("data") or {}).get("tasks") or []) if t.get("source") == "recovered"]))
    total_recovered = sum(week_counts)
    # dump یعنی: بیش از ۳ کار بازیافتی و همهٔ آن‌ها فقط روی فردا
    dump_all = len(recovered) > 3 and total_recovered == len(recovered)
    check("V2-P04", "recovery همه را به فردا نمی‌ریزد",
          st == 200 and not dump_all,
          f"فردا {fa(len(recovered))} بازیافتی · کل پخش هفته {fa(total_recovered)} {week_counts}")


# --- U: UI (بازرسی منبع) -----------------------------------------------------------------------------

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def section_ui():
    print("\n[UI — بازرسی منبع frontend]")
    page = _read(FE / "src/components/Page.tsx")
    layout = _read(FE / "src/app/layout.tsx")
    check("V2-U01", "Framer Motion در page transition فعال",
          "motion" in page and "page" in page and 'AnimatePresence mode="wait"' in layout,
          "Page.tsx + AnimatePresence mode=wait در layout")

    app = _read(FE / "src/app/App.tsx")
    variants = _read(FE / "src/motion/variants.ts")
    check("V2-U02", "prefers-reduced-motion حرکت را کم می‌کند",
          'MotionConfig reducedMotion="user"' in app and "reduced motion" in variants.lower(),
          "MotionConfig reducedMotion=user")

    theme = _read(FE / "src/app/theme.tsx")
    tokens = _read(FE / "src/styles/tokens.css") + _read(FE / "src/styles/globals.css")
    tw = _read(FE / "tailwind.config.js")
    check("V2-U03", "dark mode کامل",
          "classList" in theme and "'dark'" in theme and ".dark" in tokens
          and "darkMode: 'class'" in tw and "ThemeToggle" in layout,
          "toggle کلاس dark + توکن‌های .dark در tokens.css + darkMode:class")

    vite = _read(FE / "vite.config.ts")
    check("V2-U04", "پورت API پیش‌فرض 8010 در پروکسی",
          "8010" in vite and "/api" in vite and "5173" in vite,
          "vite proxy → http://127.0.0.1:8010")


# --- S: Backup ------------------------------------------------------------------------------------------

def section_backup():
    print("\n[Backup]")
    email_a, tok_a = register("bkA")
    res = workbook("S", tok_a)

    st, r = req("POST", "/backup/create", {"label": "پذیرش S01"}, tok_a)
    bid = (r.get("data") or {}).get("id")
    check("V2-S02", "restore بدون confirm رد می‌شود",
          req("POST", "/backup/restore", {"id": bid, "confirm": False}, tok_a)[0] == 422
          and "confirm" in ((req("POST", "/backup/restore", {"id": bid}, tok_a)[1].get("error") or {}).get("message") or ""))

    email_b, _ = register("bkB")
    st, r = req("POST", "/backup/restore", {"id": bid, "confirm": True}, tok_a)
    st_b, _ = req("POST", "/auth/login", {"email": email_b, "password": PASS})
    st_a, r_a = req("POST", "/auth/login", {"email": email_a, "password": PASS})
    books_ok = False
    if st_a == 200:
        stx, rx = req("GET", "/resources", None, r_a["data"]["access_token"])
        books_ok = any(b["id"] == res["id"] for b in (rx.get("data") or {}).get("items") or [])
    check("V2-S01", "backup/restore دور کامل",
          st == 200 and bid and st_b == 401 and st_a == 200 and books_ok,
          "داده بعد از snapshot حذف و داده قبل از آن سالم بازگشت")


def main() -> int:
    print(f"چک‌لیست پذیرش doc 15 — {BASE}")
    st, health = req("GET", "/health", base=BASE)
    if st != 200 or (health.get("data") or {}).get("status") != "ok":
        print("سرور زنده نیست — backend را روی 8010 بالا بیاور (scripts/run.sh) و دوباره اجرا کن.")
        return 1
    print(f"نسخه {(health.get('data') or {}).get('version')} · alembic {(health.get('data') or {}).get('alembic_revision')}")

    section_books()
    section_tests()
    section_planning()
    section_ui()
    section_backup()

    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r[2])
    print(f"\n=== پذیرش: {fa(passed)} از {fa(total)} ===")
    fails = [r for r in RESULTS if not r[2]]
    if fails:
        print("ناموفق‌ها:")
        for cid, desc, _, detail in fails:
            print(f"  ✗ {cid} — {desc} {detail}")
        return 1
    ids = sorted({r[0] for r in RESULTS})
    print("همهٔ ردیف‌های doc 15 پاس شدند:", ", ".join(ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
