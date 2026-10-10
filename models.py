"""models.py - what we STORE (Order) versus what we PUBLISH (Order.as_json).

Also holds validate(): the hand-written replacement for the XML Schema that used
to check requests before our code ran.
"""
from dataclasses import dataclass
from typing import Optional

from errors import ApiError

# Stand-in for Catalogue.checkItem(). In the full system the Catalogue service
# owns this data; Orders only keeps a copy here so the demo runs on its own.
MENU = {
    "dosa":     {"name": "Masala Dosa",   "price": 40, "available": True},
    "samosa":   {"name": "Samosa",        "price": 15, "available": True},
    "tea":      {"name": "Masala Tea",    "price": 10, "available": True},
    "thali":    {"name": "Veg Thali",     "price": 90, "available": True},
    "sandwich": {"name": "Veg Sandwich",  "price": 35, "available": True},
    "pizza":    {"name": "Cheese Pizza",  "price": 120, "available": False},
}

STATUSES = ("placed", "preparing", "ready", "delivered", "cancelled")
NEXT_STATUS = {"placed": "preparing", "preparing": "ready", "ready": "delivered"}
SORTS = ("created_at", "-created_at", "total", "-total")


@dataclass
class Order:
    # --- stored record: includes internal fields that must never be published ---
    id: int
    owner: str                               # internal: client that placed it
    items: list
    address: str
    total: int
    status: str = "placed"
    payment_id: str = ""                     # internal: reference at Payments
    idempotency_key: Optional[str] = None    # internal: stored with the record
    created_at: str = ""
    updated_at: str = ""
    version: int = 1                         # internal: drives the ETag

    def as_json(self):
        """The representation we publish. Differs from the record: no owner,
        payment_id, idempotency_key or version; adds paid, currency and links."""
        links = {"self": f"/orders/{self.id}"}
        if self.status == "placed":
            links["cancellation"] = f"/orders/{self.id}/cancellation"
        return {
            "id": self.id,
            "status": self.status,
            "items": [dict(i) for i in self.items],
            "address": self.address,
            "total": self.total,
            "currency": "INR",
            "paid": bool(self.payment_id),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "links": links,
        }


def _err(field, message):
    return {"field": field, "message": message}


def validate(body):
    """Check a POST /orders body. Returns a list of ALL problems (empty = valid).
    Must be called before touching any field of the body."""
    errors = []
    for key in body:
        if key not in ("items", "address"):
            errors.append(_err(key, "unexpected field"))

    if "items" not in body:
        errors.append(_err("items", "is required"))
    elif not isinstance(body["items"], list):
        errors.append(_err("items", "must be a list"))
    elif len(body["items"]) == 0:
        errors.append(_err("items", "must contain at least one item"))
    else:
        for i, item in enumerate(body["items"]):
            path = f"items[{i}]"
            if not isinstance(item, dict):
                errors.append(_err(path, "must be an object"))
                continue
            for key in item:
                if key not in ("item_id", "qty"):
                    errors.append(_err(f"{path}.{key}", "unexpected field"))
            item_id = item.get("item_id")
            if not isinstance(item_id, str) or not item_id.strip():
                errors.append(_err(f"{path}.item_id", "is required and must be a non-empty string"))
            qty = item.get("qty")
            if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
                errors.append(_err(f"{path}.qty", "must be an integer >= 1"))
            elif qty > 20:
                errors.append(_err(f"{path}.qty", "must be 20 or less"))

    if "address" not in body:
        errors.append(_err("address", "is required"))
    elif not isinstance(body["address"], str) or not body["address"].strip():
        errors.append(_err("address", "must be a non-empty string"))
    elif len(body["address"].strip()) > 200:
        errors.append(_err("address", "must be 200 characters or fewer"))
    return errors


def validate_patch(body):
    errors = []
    for key in body:
        if key != "address":
            errors.append(_err(key, "cannot be changed (only address is editable)"))
    if "address" not in body:
        errors.append(_err("address", "is required"))
    elif not isinstance(body["address"], str) or not body["address"].strip():
        errors.append(_err("address", "must be a non-empty string"))
    elif len(body["address"].strip()) > 200:
        errors.append(_err("address", "must be 200 characters or fewer"))
    return errors


def validate_query(args):
    """Validate ?status=&sort=&limit=&offset= for the list endpoint."""
    errors, params = [], {}
    status = args.get("status")
    if status is not None and status not in STATUSES:
        errors.append(_err("status", "must be one of: " + ", ".join(STATUSES)))
    params["status"] = status

    sort = args.get("sort", "-created_at")
    if sort not in SORTS:
        errors.append(_err("sort", "must be one of: " + ", ".join(SORTS)))
    params["sort"] = sort

    for name, default, low, high in (("limit", 10, 1, 50), ("offset", 0, 0, None)):
        raw = args.get(name)
        if raw is None:
            params[name] = default
            continue
        try:
            value = int(raw)
        except ValueError:
            errors.append(_err(name, "must be an integer"))
            continue
        if value < low or (high is not None and value > high):
            errors.append(_err(name, f"must be between {low} and {high}" if high else f"must be >= {low}"))
        params[name] = value
    return params, errors


def price_items(items):
    """Domain check: every item must exist and be available. Returns (lines, total)."""
    lines, bad, total = [], [], 0
    for i, item in enumerate(items):
        entry = MENU.get(item["item_id"].strip().lower())
        if entry is None or not entry["available"]:
            bad.append(_err(f"items[{i}].item_id", f"'{item['item_id']}' is not available"))
            continue
        line_total = entry["price"] * item["qty"]
        total += line_total
        lines.append({
            "item_id": item["item_id"].strip().lower(),
            "name": entry["name"],
            "qty": item["qty"],
            "unit_price": entry["price"],
            "line_total": line_total,
        })
    if bad:
        raise ApiError("item-unavailable", "One or more items cannot be ordered right now.", errors=bad)
    return lines, total
