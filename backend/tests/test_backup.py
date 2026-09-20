"""Phase 8 — Backup & Restore (doc 04، doc 03 §3.6، doc 06 §Backup، doc 15 V2-S01/S02).

- V2-S01: چرخه کامل — userA+book → backup → userB ثبت‌نام → restore → userB می‌پرد،
  userA و کتابش سالم (بدون از دست رفتن داده)
- V2-S02: restore بدون confirm=true → 422 با پیام فارسی
- AES اختیاری (pyzipper): list بدون باز کردن zip، رمز غلط → 422، درست → موفق
- retention: نگه‌داشتن MAX_BACKUPS مورد آخر
- path traversal در restore/download → رد می‌شود
- download: فایل خام zip (PK header)
- auto_backup: settings کلید + maybe_auto_backup در startup
"""
from __future__ import annotations

import io
import zipfile

from app.modules.backup import domain

PASS = "pass1234"


def _user(client, email: str) -> dict:
    r = client.post("/api/v1/auth/register", json={"email": email, "password": PASS})
    assert r.status_code == 200, r.text
    return {"email": email, "token": r.json()["data"]["access_token"]}


def _h(u):
    return {"Authorization": f"Bearer {u['token']}"}


def _book(title="زیست پایه"):
    return {
        "title": title,
        "chapters": [
            {
                "title": "فصل ۱",
                "topics": [
                    {
                        "title": "گوارش",
                        "questions": [{"number": i, "answer": "1"} for i in range(1, 6)],
                    }
                ],
            }
        ],
    }


def _create(client, u, **kw):
    r = client.post("/api/v1/backup/create", json=kw, headers=_h(u))
    assert r.status_code == 200, r.text
    return r.json()["data"]


def _ids(client, u) -> list[str]:
    r = client.get("/api/v1/backup/list", headers=_h(u))
    assert r.status_code == 200, r.text
    return [i["id"] for i in r.json()["data"]["items"]]


# --- V2-S01 — چرخه کامل پشتیبان/بازیابی -----------------------------------------------------------

def test_backup_full_cycle(client):
    a = _user(client, "bk-a@example.com")
    r = client.post("/api/v1/resources/import-book", json=_book(), headers=_h(a))
    assert r.status_code == 200, r.text

    meta = _create(client, a, label="قبل از تغییرات")
    assert meta["encrypted"] is False
    assert meta["alembic_revision"] == "0008_rewards"
    assert meta["label"] == "قبل از تغییرات"
    assert meta["id"] in _ids(client, a)

    # دادهٔ جدید بعد از backup — باید با restore از بین برود
    b = _user(client, "bk-b@example.com")
    assert client.post("/api/v1/auth/login", json={"email": b["email"], "password": PASS}).status_code == 200

    r = client.post("/api/v1/backup/restore", json={"id": meta["id"], "confirm": True}, headers=_h(a))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["data"]["alembic_revision"] == "0008_rewards"
    assert "بازیابی کامل" in body["data"]["message_fa"]

    # userB دیگر وجود ندارد؛ userA و کتابش سالم‌اند
    assert client.post("/api/v1/auth/login", json={"email": b["email"], "password": PASS}).status_code == 401
    r = client.post("/api/v1/auth/login", json={"email": a["email"], "password": PASS})
    assert r.status_code == 200, r.text
    a2 = {"token": r.json()["data"]["access_token"]}
    r = client.get("/api/v1/resources", headers=_h(a2))
    assert r.status_code == 200, r.text
    assert any(bk["title"] == "زیست پایه" for bk in r.json()["data"]["items"])


# --- V2-S02 — تایید دو مرحله‌ای --------------------------------------------------------------------

def test_restore_requires_confirm(client):
    a = _user(client, "bk-c@example.com")
    meta = _create(client, a)

    r = client.post("/api/v1/backup/restore", json={"id": meta["id"], "confirm": False}, headers=_h(a))
    assert r.status_code == 422
    assert r.json()["error"]["message"] == domain.MSG_CONFIRM_REQUIRED

    # confirm حذف شده (پیش‌فرض False) هم رد می‌شود
    r = client.post("/api/v1/backup/restore", json={"id": meta["id"]}, headers=_h(a))
    assert r.status_code == 422

    # با تایید، همان پشتیبان موفق است
    r = client.post("/api/v1/backup/restore", json={"id": meta["id"], "confirm": True}, headers=_h(a))
    assert r.status_code == 200, r.text


# --- AES (doc 03 §3.6) -----------------------------------------------------------------------------

def test_backup_aes_cycle(client):
    a = _user(client, "bk-aes@example.com")
    meta = _create(client, a, label="رمزدار", password="secret123")
    assert meta["encrypted"] is True

    # list بدون رمز کار می‌کند (sidecar)
    items = client.get("/api/v1/backup/list", headers=_h(a)).json()["data"]["items"]
    row = next(i for i in items if i["id"] == meta["id"])
    assert row["encrypted"] is True and row["label"] == "رمزدار"

    base = {"id": meta["id"], "confirm": True}
    r = client.post("/api/v1/backup/restore", json=base, headers=_h(a))
    assert r.status_code == 422
    assert r.json()["error"]["message"] == domain.MSG_PASSWORD_REQUIRED

    r = client.post("/api/v1/backup/restore", json={**base, "password": "wrong-pass"}, headers=_h(a))
    assert r.status_code == 422
    assert r.json()["error"]["message"] == domain.MSG_BAD_PASSWORD

    r = client.post("/api/v1/backup/restore", json={**base, "password": "secret123"}, headers=_h(a))
    assert r.status_code == 200, r.text


def test_backup_download_is_zip(client):
    a = _user(client, "bk-dl@example.com")
    meta = _create(client, a)
    r = client.get(f"/api/v1/backup/download/{meta['id']}", headers=_h(a))
    assert r.status_code == 200
    assert r.content[:2] == b"PK"
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        assert "alems.db" in z.namelist()


# --- امنیت و خطاها ------------------------------------------------------------------------------------

def test_restore_rejects_traversal(client):
    a = _user(client, "bk-sec@example.com")
    for bad in ("../etc/passwd", "20260920-120000-zzzz", "..%2f..", ""):
        r = client.post("/api/v1/backup/restore", json={"id": bad, "confirm": True}, headers=_h(a))
        assert r.status_code in (404, 422), (bad, r.status_code)
        if r.status_code == 404:
            assert r.json()["error"]["message"] == domain.MSG_NOT_FOUND
    # id معتبر ولی ناموجود → 404
    r = client.post("/api/v1/backup/restore", json={"id": "20260920-120000-abcd", "confirm": True}, headers=_h(a))
    assert r.status_code == 404


def test_backup_endpoints_require_auth(client):
    assert client.post("/api/v1/backup/create", json={}).status_code == 401
    assert client.get("/api/v1/backup/list").status_code == 401
    assert client.get("/api/v1/backup/download/20260920-120000-abcd").status_code == 401


# --- retention -----------------------------------------------------------------------------------------

def test_backup_retention_prunes_old(client, monkeypatch):
    a = _user(client, "bk-ret@example.com")
    monkeypatch.setattr(domain, "MAX_BACKUPS", 5)
    made = [_create(client, a, label=f"n{i}")["id"] for i in range(7)]
    ids = _ids(client, a)
    assert len(ids) == 5  # retention کل پوشه را روی ۵ نگه می‌دارد
    assert made[-1] in ids and made[-2] in ids  # جدیدترین‌ها می‌مانند
    assert made[0] not in ids  # قدیمی‌ترین ساخته‌شده حذف شده


# --- خودکار (doc 04) --------------------------------------------------------------------------------------

def test_auto_backup_setting_and_startup_hook(client):
    a = _user(client, "bk-auto@example.com")
    r = client.get("/api/v1/settings", headers=_h(a))
    assert r.status_code == 200
    assert r.json()["data"]["auto_backup"] is False

    r = client.put("/api/v1/settings", json={"auto_backup": "not-a-bool"}, headers=_h(a))
    assert r.status_code == 422  # pydantic رد می‌کند — پیام فارسی عمومی envelope
    assert r.json()["success"] is False and r.json()["error"]["message"]

    r = client.put("/api/v1/settings", json={"auto_backup": True}, headers=_h(a))
    assert r.status_code == 200
    assert r.json()["data"]["auto_backup"] is True

    before = len(_ids(client, a))
    from app.modules.backup import service as bsvc
    bsvc.maybe_auto_backup()
    ids = _ids(client, a)
    assert len(ids) == before + 1
    newest = next(i for i in client.get("/api/v1/backup/list", headers=_h(a)).json()["data"]["items"]
                  if i["id"] == ids[0])
    assert newest["label"] == "خودکار (startup)" and newest["encrypted"] is False

    # خاموش → بدون اثر
    client.put("/api/v1/settings", json={"auto_backup": False}, headers=_h(a))
    bsvc.maybe_auto_backup()
    assert len(_ids(client, a)) == before + 1


def test_backup_domain_helpers():
    bid = domain.make_backup_id(__import__("datetime").datetime(2026, 9, 20, 12, 0, 0))
    assert domain.is_safe_id(bid)
    assert domain.backup_filename(bid) == f"alems-backup-{bid}.zip"
    assert not domain.is_safe_id("../x")
    assert domain.prune_entries([(1.0, "a"), (2.0, "b"), (3.0, "c")], keep=2) == [(1.0, "a")]
    assert domain.prune_entries([(1.0, "a")], keep=2) == []
