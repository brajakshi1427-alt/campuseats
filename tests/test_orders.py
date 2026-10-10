"""The four tests required by Assignment 4 (C8)."""
from conftest import AUTH, GOOD


def test_create_returns_201_and_location(client, payments):
    r = client.post("/orders", json=GOOD, headers=AUTH)
    assert r.status_code == 201
    assert r.headers["Location"] == "/orders/1"
    body = r.get_json()
    assert body["total"] == 80 and body["status"] == "placed"
    assert "owner" not in body and "payment_id" not in body      # nothing internal leaks


def test_idempotent_repeat_returns_original(client, payments):
    h = {**AUTH, "Idempotency-Key": "abc-123"}
    first = client.post("/orders", json=GOOD, headers=h)
    again = client.post("/orders", json=GOOD, headers=h)
    assert again.status_code == 201
    assert again.get_json() == first.get_json()
    assert again.headers["Idempotent-Replayed"] == "true"
    assert len(payments) == 1                                    # charged only once


def test_bad_quantity_returns_422(client, payments):
    bad = {"items": [{"item_id": "dosa", "qty": 0}], "address": "Hostel B"}
    r = client.post("/orders", json=bad, headers=AUTH)
    assert r.status_code == 422
    assert r.headers["Content-Type"].startswith("application/problem+json")
    assert r.get_json()["errors"][0]["field"] == "items[0].qty"


def test_unknown_id_returns_404(client, payments):
    r = client.get("/orders/999", headers=AUTH)
    assert r.status_code == 404
    assert r.get_json()["type"].endswith("/order-not-found")
