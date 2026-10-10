"""errors.py - ONE error shape for the whole service (RFC 9457 Problem Details).

Every failure, from every endpoint, goes through problem() so the client always
sees the same four members: type, title, status, detail (+ optional errors[]).
"""

BASE = "https://campuseats.example/problems/"

# key -> (HTTP status, human title).  The key is the stable "type" string.
CATALOGUE = {
    "malformed-body":         (400, "Malformed request body"),
    "unauthorized":           (401, "Authentication required"),
    "order-not-found":        (404, "Order not found"),
    "route-not-found":        (404, "Resource not found"),
    "method-not-allowed":     (405, "Method not allowed"),
    "not-acceptable":         (406, "Not acceptable"),
    "illegal-transition":     (409, "Illegal state transition"),
    "request-in-progress":    (409, "Request already in progress"),
    "precondition-failed":    (412, "Precondition failed"),
    "unsupported-media-type": (415, "Unsupported media type"),
    "validation-failed":      (422, "Validation failed"),
    "empty-cart":             (422, "Cart is empty"),
    "item-unavailable":       (422, "Item unavailable"),
    "payment-declined":       (422, "Payment declined"),
    "idempotency-key-reuse":  (422, "Idempotency key reused with a different request"),
    "precondition-required":  (428, "Precondition required"),
    "rate-limited":           (429, "Too many requests"),
    "internal-error":         (500, "Internal server error"),
    "upstream-error":         (502, "Bad gateway"),
    "payment-unavailable":    (503, "Payments temporarily unavailable"),
}


def problem(key, detail, instance=None, errors=None):
    """Build the one and only error body."""
    status, title = CATALOGUE[key]
    body = {"type": BASE + key, "title": title, "status": status, "detail": detail}
    if instance:
        body["instance"] = instance
    if errors:
        body["errors"] = errors
    return body


class ApiError(Exception):
    """Raise this anywhere; app.py turns it into a Problem Details response."""

    def __init__(self, key, detail, errors=None, headers=None):
        super().__init__(detail)
        self.key = key
        self.status = CATALOGUE[key][0]
        self.detail = detail
        self.errors = errors
        self.headers = headers or {}
