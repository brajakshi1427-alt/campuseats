"""D2: timeout / retry / backoff rules of the outbound call."""
import pytest

import payments_client as pc


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setenv("PAYMENTS_URL", "http://payments.invalid")
    monkeypatch.setattr(pc, "_sleep", lambda s: None)


def script(monkeypatch, outcomes):
    """Make _send return / raise the given outcomes in order; record the calls."""
    calls = []

    def fake_send(url, payload, headers, timeout):
        calls.append({"headers": headers, "timeout": timeout})
        outcome = outcomes[min(len(calls) - 1, len(outcomes) - 1)]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(pc, "_send", fake_send)
    return calls


def test_retries_transient_failures_then_succeeds(monkeypatch):
    calls = script(monkeypatch, [OSError("timed out"), (503, {}), (201, {"id": "pay_1"})])
    assert pc.charge("ref", 80, "key-1") == {"payment_id": "pay_1"}
    assert len(calls) == 3
    assert all(c["headers"]["Idempotency-Key"] == "key-1" for c in calls)   # same key every try
    assert calls[0]["timeout"] == 2.0


def test_4xx_is_never_retried(monkeypatch):
    calls = script(monkeypatch, [(402, {"error": "card_declined"})])
    with pytest.raises(pc.PaymentDeclined):
        pc.charge("ref", 80, "k")
    assert len(calls) == 1
    calls = script(monkeypatch, [(400, {})])
    with pytest.raises(pc.UpstreamError):
        pc.charge("ref", 80, "k")
    assert len(calls) == 1


def test_gives_up_after_all_attempts(monkeypatch):
    calls = script(monkeypatch, [OSError("refused")])
    with pytest.raises(pc.PaymentsUnavailable):
        pc.charge("ref", 80, "k")
    assert len(calls) == 3


def test_backoff_grows_and_is_capped():
    for attempt, ceiling in ((0, 0.2), (1, 0.4), (2, 0.8), (10, 2.0)):
        assert all(0 <= pc._backoff(attempt) <= ceiling for _ in range(50))


def test_url_comes_from_environment(monkeypatch):
    monkeypatch.delenv("PAYMENTS_URL")
    with pytest.raises(pc.PaymentsUnavailable):
        pc.charge("ref", 80, "k")
