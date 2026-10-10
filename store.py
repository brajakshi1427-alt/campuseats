"""store.py - in-process storage for Orders. No other service imports this file."""
import math
import threading
import time
from datetime import datetime, timezone

from models import Order

_lock = threading.RLock()
_orders = {}
_idem = {}      # (client, key) -> {"fp": fingerprint, "order_id": id or None}
_rate = {}      # client -> [window_start, count]
_next_id = 1


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def reset():
    """Empty everything (used by tests)."""
    global _next_id
    with _lock:
        _orders.clear()
        _idem.clear()
        _rate.clear()
        _next_id = 1


def add(**fields):
    global _next_id
    with _lock:
        order = Order(id=_next_id, created_at=_now(), updated_at=_now(), **fields)
        _orders[order.id] = order
        _next_id += 1
        return order


def get(order_id):
    return _orders.get(order_id)


def update(order, **changes):
    with _lock:
        for name, value in changes.items():
            setattr(order, name, value)
        order.version += 1
        order.updated_at = _now()
        return order


def delete(order_id):
    with _lock:
        _orders.pop(order_id, None)


def list_orders(owner, status, sort, limit, offset):
    with _lock:
        rows = [o for o in _orders.values() if o.owner == owner]
    if status:
        rows = [o for o in rows if o.status == status]
    field = sort.lstrip("-")
    rows.sort(key=lambda o: (getattr(o, field), o.id), reverse=sort.startswith("-"))
    return rows[offset:offset + limit], len(rows)


# ---- idempotency ----------------------------------------------------------
def idem_begin(client, key, fingerprint):
    """Reserve a key. Returns (state, order): new | replay | in_progress | mismatch."""
    with _lock:
        rec = _idem.get((client, key))
        if rec is None:
            _idem[(client, key)] = {"fp": fingerprint, "order_id": None}
            return "new", None
        if rec["fp"] != fingerprint:
            return "mismatch", None
        if rec["order_id"] is None:
            return "in_progress", None
        return "replay", _orders.get(rec["order_id"])


def idem_finish(client, key, order_id):
    with _lock:
        _idem[(client, key)]["order_id"] = order_id


def idem_abort(client, key):
    """The create failed: free the key so the client can retry for real."""
    with _lock:
        _idem.pop((client, key), None)


# ---- rate limiting (per client, fixed window) -------------------------------
def rate_hit(client, limit, window, now=None):
    """Count one request. Returns (allowed, remaining, retry_after_seconds)."""
    now = time.time() if now is None else now
    with _lock:
        rec = _rate.get(client)
        if rec is None or now - rec[0] >= window:
            rec = [now, 0]
            _rate[client] = rec
        rec[1] += 1
        if rec[1] > limit:
            return False, 0, max(1, math.ceil(window - (now - rec[0])))
        return True, limit - rec[1], 0
