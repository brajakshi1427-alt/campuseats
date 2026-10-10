"""Extra tests for Assignment 5 (methods, headers, caching) and 6 (errors)."""
import gzip
import json

import app as app_module
import payments_client
from conftest import AUTH, GOOD


def make_order(client, **extra):
    return client.post("/orders", json=GOOD, headers={**AUTH, **extra})


# ---------------- A5: headers, caching, preconditions ----------------
def test_etag_then_304(client, payments):
    make_order(client)
    first = client.get("/orders/1", headers=AUTH)
    tag = first.headers["ETag"]
    assert "max-age" in first.headers["Cache-Control"]
    again = client.get("/orders/1", headers={**AUTH, "If-None-Match": tag})
    assert again.status_code == 304 and again.data == b""


def test_stale_if_match_returns_412(client, payments):
    make_order(client)
    old = client.get("/orders/1", headers=AUTH).headers["ETag"]
    ok = client.patch("/orders/1", json={"address": "Library gate"},
                      headers={**AUTH, "If-Match": old})
    assert ok.status_code == 200 and ok.headers["ETag"] != old    # ETag changed
    stale = client.patch("/orders/1", json={"address": "Hostel C"},
                         headers={**AUTH, "If-Match": old})
    assert stale.status_code == 412
    assert client.get("/orders/1", headers=AUTH).get_json()["address"] == "Library gate"


def test_progression_requires_if_match(client, payments):
    make_order(client)
    r = client.post("/orders/1/progression", headers=AUTH)
    assert r.status_code == 428
    tag = client.get("/orders/1", headers=AUTH).headers["ETag"]
    r = client.post("/orders/1/progression", headers={**AUTH, "If-Match": tag})
    assert r.status_code == 200 and r.get_json()["status"] == "preparing"
    again = client.post("/orders/1/progression", headers={**AUTH, "If-Match": tag})
    assert again.status_code == 412                               # blind retry is refused


def test_missing_token_returns_401(client):
    for headers in ({}, {"Authorization": "Bearer "}, {"Authorization": "Bearer"}):
        r = client.get("/orders", headers=headers)
        assert r.status_code == 401
        assert "Bearer" in r.headers["WWW-Authenticate"]


def test_unsupported_accept_returns_406(client, payments):
    r = client.get("/orders", headers={**AUTH, "Accept": "text/html"})
    assert r.status_code == 406


def test_options_lists_allowed_methods_and_cors(client):
    r = client.options("/orders/1")
    assert r.status_code == 204
    for m in ("GET", "PATCH", "DELETE", "OPTIONS"):
        assert m in r.headers["Allow"]
    assert r.headers["Access-Control-Allow-Origin"]
    assert "Idempotency-Key" in r.headers["Access-Control-Allow-Headers"]


def test_method_override_fallback(client, payments):
    make_order(client)
    r = client.post("/orders/1", json={"address": "Gate 2"},
                    headers={**AUTH, "X-HTTP-Method-Override": "PATCH"})
    assert r.status_code == 200 and r.get_json()["address"] == "Gate 2"


def test_rate_limit_is_per_client(client, payments, monkeypatch):
    monkeypatch.setattr(app_module, "RATE_LIMIT", 3)
    codes = [client.get("/orders", headers=AUTH).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    r = client.get("/orders", headers=AUTH)
    assert int(r.headers["Retry-After"]) >= 1 and r.headers["X-RateLimit-Remaining"] == "0"
    other = client.get("/orders", headers={"Authorization": "Bearer someone-else"})
    assert other.status_code == 200 and other.headers["X-RateLimit-Limit"] == "3"


def test_security_headers_present(client, payments):
    r = client.get("/orders", headers=AUTH)
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert "Strict-Transport-Security" in r.headers
    assert r.headers["Content-Type"] == "application/json; charset=utf-8"


def test_gzip_for_large_lists(client, payments):
    for _ in range(8):
        make_order(client)
    r = client.get("/orders", headers={**AUTH, "Accept-Encoding": "gzip"})
    assert r.headers.get("Content-Encoding") == "gzip"
    assert json.loads(gzip.decompress(r.data))["total"] == 8


# ---------------- A6: honest errors ----------------
def test_malformed_json_is_400_but_bad_fields_are_422(client, payments):
    h = {**AUTH, "Content-Type": "application/json"}
    r = client.post("/orders", data='{"items": [', headers=h)
    assert r.status_code == 400 and r.get_json()["type"].endswith("/malformed-body")
    r = client.post("/orders", json={"items": [{"item_id": "dosa", "qty": 0}], "address": ""},
                    headers=AUTH)
    assert r.status_code == 422


def test_two_field_errors_in_one_422(client, payments):
    bad = {"items": [{"item_id": "dosa", "qty": -1}], "address": "  "}
    body = client.post("/orders", json=bad, headers=AUTH).get_json()
    assert {e["field"] for e in body["errors"]} == {"items[0].qty", "address"}
    assert set(body) >= {"type", "title", "status", "detail", "errors"}


def test_empty_cart_and_unavailable_item(client, payments):
    r = client.post("/orders", json={"items": [], "address": "x"}, headers=AUTH)
    assert r.status_code == 422 and r.get_json()["type"].endswith("/empty-cart")
    r = client.post("/orders", json={"items": [{"item_id": "pizza", "qty": 1}], "address": "x"},
                    headers=AUTH)
    assert r.status_code == 422 and r.get_json()["type"].endswith("/item-unavailable")
    assert payments == []                                        # nothing was charged


def test_illegal_transition_is_409(client, payments):
    make_order(client)
    tag = client.get("/orders/1", headers=AUTH).headers["ETag"]
    client.post("/orders/1/progression", headers={**AUTH, "If-Match": tag})
    r = client.post("/orders/1/cancellation", headers=AUTH)
    assert r.status_code == 409 and r.get_json()["type"].endswith("/illegal-transition")


def test_cancel_then_delete(client, payments):
    make_order(client)
    assert client.post("/orders/1/cancellation", headers=AUTH).get_json()["status"] == "cancelled"
    assert client.delete("/orders/1", headers=AUTH).status_code == 204
    assert client.get("/orders/1", headers=AUTH).status_code == 404


def test_same_key_different_body_is_422(client, payments):
    h = {**AUTH, "Idempotency-Key": "k1"}
    client.post("/orders", json=GOOD, headers=h)
    other = {"items": [{"item_id": "tea", "qty": 1}], "address": "Hostel B"}
    r = client.post("/orders", json=other, headers=h)
    assert r.status_code == 422 and r.get_json()["type"].endswith("/idempotency-key-reuse")


def test_someone_elses_order_looks_missing(client, payments):
    make_order(client)
    r = client.get("/orders/1", headers={"Authorization": "Bearer another-student"})
    assert r.status_code == 404


def test_list_filters_and_validates_query(client, payments):
    make_order(client)
    make_order(client)
    client.post("/orders/2/cancellation", headers=AUTH)
    r = client.get("/orders?status=cancelled&limit=5&sort=total", headers=AUTH).get_json()
    assert r["total"] == 1 and r["items"][0]["id"] == 2
    bad = client.get("/orders?limit=0&status=lost", headers=AUTH)
    assert bad.status_code == 422 and len(bad.get_json()["errors"]) == 2


def test_xml_when_asked(client, payments):
    make_order(client)
    r = client.get("/orders/1", headers={**AUTH, "Accept": "application/xml"})
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/xml; charset=utf-8"
    assert b"<order>" in r.data and b"<status>placed</status>" in r.data
    err = client.get("/orders/99", headers={**AUTH, "Accept": "application/xml"})
    assert err.headers["Content-Type"].startswith("application/problem+xml")


# ---------------- Payments dependency (D1-D3) ----------------
def test_payment_declined_maps_to_clean_422(client, monkeypatch):
    def declined(**kw):
        raise payments_client.PaymentDeclined("card_declined")
    monkeypatch.setattr(payments_client, "charge", declined)
    r = client.post("/orders", json=GOOD, headers=AUTH)
    assert r.status_code == 422 and r.get_json()["type"].endswith("/payment-declined")
    assert "card_declined" not in r.get_data(as_text=True)       # partner words do not leak
    assert client.get("/orders", headers=AUTH).get_json()["total"] == 0


def test_payments_down_fails_with_503_and_frees_the_key(client, monkeypatch):
    def down(**kw):
        raise payments_client.PaymentsUnavailable("connection refused")
    monkeypatch.setattr(payments_client, "charge", down)
    h = {**AUTH, "Idempotency-Key": "retry-me"}
    r = client.post("/orders", json=GOOD, headers=h)
    assert r.status_code == 503 and r.headers["Retry-After"] == "5"
    monkeypatch.setattr(payments_client, "charge", lambda **kw: {"payment_id": "pay_ok"})
    assert client.post("/orders", json=GOOD, headers=h).status_code == 201


def test_unexpected_crash_is_hidden_from_client(client, payments, monkeypatch):
    import store

    def boom(**kw):
        raise RuntimeError("DB password is hunter2")
    monkeypatch.setattr(store, "add", boom)
    r = client.post("/orders", json=GOOD, headers=AUTH)
    assert r.status_code == 500
    text = r.get_data(as_text=True)
    assert "hunter2" not in text and "Traceback" not in text
    assert r.get_json()["type"].endswith("/internal-error")
