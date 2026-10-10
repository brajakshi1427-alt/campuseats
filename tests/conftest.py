import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pytest

import app as app_module
import payments_client
import store


@pytest.fixture(autouse=True)
def clean_state():
    store.reset()
    yield


@pytest.fixture
def payments(monkeypatch):
    """Replace the real Payments call with a fake and record how it was called."""
    calls = []

    def fake_charge(reference, amount, idempotency_key):
        calls.append({"amount": amount, "key": idempotency_key})
        return {"payment_id": "pay_test"}

    monkeypatch.setattr(payments_client, "charge", fake_charge)
    return calls


@pytest.fixture
def client():
    return app_module.app.test_client()


AUTH = {"Authorization": "Bearer test-token"}
GOOD = {"items": [{"item_id": "dosa", "qty": 2}], "address": "Hostel B, Room 12"}
