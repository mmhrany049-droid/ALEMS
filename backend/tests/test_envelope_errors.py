"""Envelope error shape + Persian messages (doc 06, user rule: Persian errors)."""
from __future__ import annotations


def test_404_has_persian_message_and_envelope(client):
    r = client.get("/api/v1/does-not-exist")
    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"] == "عناصر مورد نظر پیدا نشد."
    assert isinstance(body["error"]["details"], dict)


def test_422_validation_envelope():
    # a fresh app instance with one temporary endpoint (no mutation of the shared app)
    from fastapi.testclient import TestClient

    from app.main import create_app

    t_app = create_app()

    @t_app.post("/api/v1/_test_validation")
    def _t(x: int):  # pragma: no cover
        return {"x": x}

    with TestClient(t_app) as tc:
        r = tc.post("/api/v1/_test_validation", json={"x": "not-an-int"})
        assert r.status_code == 422
        body = r.json()
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["message"] == "ورودی‌ها درست نیستند."
        assert "errors" in body["error"]["details"]
