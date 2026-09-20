"""Phase 1 — taught topics API + cascade domain (doc 05, doc 08 §8.8)."""
from __future__ import annotations

PASS = "pass1234"


def _user(client, email: str) -> dict:
    r = client.post("/api/v1/auth/register", json={"email": email, "password": PASS})
    assert r.status_code == 200, r.text
    return {"token": r.json()["data"]["access_token"]}


def _h(u):
    return {"Authorization": f"Bearer {u['token']}"}


def test_taught_put_get_roundtrip(client):
    u = _user(client, "taught1@example.com")
    r = client.put(
        "/api/v1/students/me/taught-topics",
        json={"items": [{"topic_id": "t-1", "taught": True}, {"topic_id": "t-2", "taught": False}]},
        headers=_h(u),
    )
    assert r.status_code == 200, r.text
    items = {i["topic_id"]: i for i in r.json()["data"]["items"]}
    assert items["t-1"]["taught"] is True
    assert items["t-2"]["taught"] is False

    g = client.get("/api/v1/students/me/taught-topics", headers=_h(u))
    got = {i["topic_id"]: i["taught"] for i in g.json()["data"]["items"]}
    assert got == {"t-1": True, "t-2": False}


def test_taught_put_is_upsert_not_duplicate(client):
    u = _user(client, "taught2@example.com")
    for val in (True, False, True):
        r = client.put(
            "/api/v1/students/me/taught-topics",
            json={"items": [{"topic_id": "same", "taught": val}]},
            headers=_h(u),
        )
        assert r.status_code == 200
    items = client.get("/api/v1/students/me/taught-topics", headers=_h(u)).json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["taught"] is True


def test_taught_requires_auth(client):
    assert client.get("/api/v1/students/me/taught-topics").status_code == 401


def test_taught_empty_items_422(client):
    u = _user(client, "taught3@example.com")
    r = client.put("/api/v1/students/me/taught-topics", json={"items": []}, headers=_h(u))
    assert r.status_code == 422


def test_cascade_domain_parent_to_children():
    from app.modules.student.domain import apply_taught, parent_state

    tree = {"a": ["b", "c"], "b": ["d"]}
    result = apply_taught({}, [("a", True)], tree)
    # parent taught=True cascades to all descendants (transitive)
    assert result == {"a": True, "b": True, "c": True, "d": True}

    # un-teaching parent never un-teaches children (doc 08 §8.8: taught cascade only)
    result2 = apply_taught(result, [("a", False)], tree)
    assert result2["a"] is False
    assert result2["b"] is True and result2["d"] is True

    # no tree (phase 1) => plain upsert
    assert apply_taught({}, [("x", True)]) == {"x": True}

    # parent indeterminate (doc 08 §8.8)
    assert parent_state([True, False]) == "partial"
    assert parent_state([True, True]) == "all"
    assert parent_state([False, False]) == "none"
