"""Phase 0 — health endpoint + envelope (doc 06, doc 14 phase 0)."""
from __future__ import annotations


def test_health_envelope_shape(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    # envelope keys exactly as doc 06
    assert set(body.keys()) == {"success", "data", "error", "meta"}
    assert body["success"] is True
    assert body["error"] is None
    assert isinstance(body["data"], dict)


def test_health_data(client):
    data = client.get("/health").json()["data"]
    assert data["status"] == "ok"
    assert data["app"] == "ALEMS"
    assert data["version"] == "2.0.0"
    assert data["app_version"] == "2.0.0"
    assert data["schema_version"] == "2.0.0"
    assert data["db"]["type"] == "sqlite"
    # version management recorded via alembic + app_metadata
    assert data["alembic_revision"] == "0004_test_engine"
    assert data["timezone"] == "Asia/Tehran"
    assert data["week_start"] == "saturday"
    # Jalali today (doc 03 §3.5) — 2026-09-20 in Tehran is 1405/06/29
    assert data["today_jalali"].startswith("1405/")
    assert data["today_jalali_fa"]


def test_api_v1_health_same_envelope(client):
    """phase-0 spec: GET /api/v1/health must answer like /health."""
    a = client.get("/health").json()
    b = client.get("/api/v1/health").json()
    assert b["success"] is True
    assert b["error"] is None
    assert set(b["data"].keys()) == set(a["data"].keys())
    assert b["data"]["app"] == "ALEMS"
    assert b["data"]["version"] == "2.0.0"


def test_api_v1_base_exists(client):
    # doc 06: base /api/v1 — no endpoints yet in phase 0, so 404 with envelope
    r = client.get("/api/v1/nothing")
    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"]["message"]
