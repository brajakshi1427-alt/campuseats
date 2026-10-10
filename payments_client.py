"""payments_client.py - the ONE outbound call from Orders to the Payments service.

Hardening (Assignment 4, part D):
  * address comes from the PAYMENTS_URL environment variable (never hard-coded)
  * every attempt has a timeout
  * retries use exponential backoff with full jitter
  * only transient failures are retried (network error, 429, 502, 503, 504)
  * a 4xx is NEVER retried
  * the create carries an Idempotency-Key, so a retry cannot charge twice
"""
import json
import os
import random
import time
import urllib.error
import urllib.request

RETRYABLE = {429, 502, 503, 504}
BASE_DELAY = 0.2     # seconds
MAX_DELAY = 2.0

_sleep = time.sleep  # tests replace this so they run instantly


class PaymentDeclined(Exception):
    """Payments said no (card declined, insufficient funds...)."""


class PaymentsUnavailable(Exception):
    """Payments could not be reached / kept failing after the retries."""


class UpstreamError(Exception):
    """Payments answered with something we did not expect (our bug or theirs)."""


def _backoff(attempt):
    """Full jitter: random wait between 0 and min(MAX, BASE * 2^attempt)."""
    return random.uniform(0, min(MAX_DELAY, BASE_DELAY * (2 ** attempt)))


def _parse(raw):
    try:
        return json.loads(raw.decode("utf-8")) if raw else {}
    except ValueError:
        return {}


def _send(url, payload, headers, timeout):
    """One HTTP POST. Returns (status, json_body). Network errors raise OSError."""
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, _parse(resp.read())
    except urllib.error.HTTPError as exc:      # got an HTTP answer (4xx/5xx)
        return exc.code, _parse(exc.read())


def charge(reference, amount, idempotency_key):
    """Charge `amount` rupees. Returns {"payment_id": ...} or raises one of the
    three exceptions above."""
    base = os.environ.get("PAYMENTS_URL")
    if not base:
        raise PaymentsUnavailable("PAYMENTS_URL is not set")
    url = base.rstrip("/") + "/payments"
    timeout = float(os.environ.get("PAYMENTS_TIMEOUT", "2"))
    attempts = int(os.environ.get("PAYMENTS_ATTEMPTS", "3"))
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Idempotency-Key": idempotency_key,
    }
    payload = {"reference": reference, "amount": amount, "currency": "INR"}

    last_problem = "no attempt made"
    for attempt in range(attempts):
        try:
            status, body = _send(url, payload, headers, timeout)
        except OSError as exc:                       # timeout, refused, DNS...
            last_problem = f"network error: {exc}"
        else:
            if status in (200, 201):
                return {"payment_id": str(body.get("id", ""))}
            if status in (402, 422):                 # a real "no" - do not retry
                raise PaymentDeclined(f"payments refused the charge ({status})")
            if status in RETRYABLE:
                last_problem = f"payments answered {status}"
            else:                                    # other 4xx/5xx: never retry
                raise UpstreamError(f"payments answered unexpected status {status}")
        if attempt < attempts - 1:
            _sleep(_backoff(attempt))
    raise PaymentsUnavailable(last_problem)
