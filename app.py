"""app.py - CampusEats Orders service (REST).

Covers Assignment 4 (resources, validation, idempotency, hardened call),
Assignment 5 (methods, headers, caching, ETag/If-Match, CORS, rate limit)
and Assignment 6 (honest status codes, Problem Details, 422 field errors, XML).

Run:  set PAYMENTS_URL=http://127.0.0.1:5001   then   python app.py
"""
import gzip
import hashlib
import json
import logging
import os
import uuid
from xml.etree import ElementTree as ET

from flask import Flask, Response, g, request
from werkzeug.exceptions import HTTPException

import payments_client
import store
from errors import ApiError, problem
from models import (NEXT_STATUS, price_items, validate, validate_patch,
                    validate_query)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "30"))       # requests per client...
RATE_WINDOW = int(os.environ.get("RATE_WINDOW", "60"))     # ...per this many seconds
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "*")
ALLOW_HEADERS = ("Authorization, Content-Type, Accept, Idempotency-Key, If-Match, "
                 "If-None-Match, X-HTTP-Method-Override")
EXPOSE_HEADERS = ("Location, ETag, Retry-After, X-RateLimit-Limit, "
                  "X-RateLimit-Remaining, Idempotent-Replayed, X-Request-ID")

app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = False


# --------------------------------------------------------------------------
# A5/A5: X-HTTP-Method-Override - a documented FALLBACK for clients that can
# only send GET/POST. Only a POST may be overridden, and only to PUT/PATCH/DELETE.
# --------------------------------------------------------------------------
class MethodOverride:
    ALLOWED = {"PUT", "PATCH", "DELETE"}

    def __init__(self, wsgi):
        self.wsgi = wsgi

    def __call__(self, environ, start_response):
        if environ.get("REQUEST_METHOD") == "POST":
            wanted = environ.get("HTTP_X_HTTP_METHOD_OVERRIDE", "").upper()
            if wanted in self.ALLOWED:
                environ["REQUEST_METHOD"] = wanted
        return self.wsgi(environ, start_response)


app.wsgi_app = MethodOverride(app.wsgi_app)


# --------------------------------------------------------------------------
# Content negotiation + rendering (JSON by default, XML on request, else 406)
# --------------------------------------------------------------------------
def negotiate(accept):
    """Return 'json', 'xml' or None (-> 406)."""
    if not accept:
        return "json"
    prefs = []
    for part in accept.split(","):
        pieces = [p.strip() for p in part.split(";")]
        q = 1.0
        for p in pieces[1:]:
            if p.startswith("q="):
                try:
                    q = float(p[2:])
                except ValueError:
                    q = 0.0
        prefs.append((pieces[0].lower(), q))

    def best(names):
        return max([q for mt, q in prefs if mt in names] or [0.0])

    q_json = best(("application/json", "application/problem+json", "application/*", "*/*"))
    q_xml = best(("application/xml", "text/xml", "application/problem+xml", "application/*", "*/*"))
    if q_json > 0 and q_json >= q_xml:
        return "json"
    if q_xml > 0:
        return "xml"
    return None


def _fill_xml(el, value):
    if isinstance(value, dict):
        for k, v in value.items():
            _fill_xml(ET.SubElement(el, str(k)), v)
    elif isinstance(value, list):
        for v in value:
            _fill_xml(ET.SubElement(el, "item"), v)
    elif isinstance(value, bool):
        el.text = "true" if value else "false"
    elif value is not None:
        el.text = str(value)


def render(body, status=200, root="order", headers=None, is_problem=False):
    """Serialise `body` as JSON or XML and label it with Content-Type + charset."""
    if g.get("fmt", "json") == "xml":
        el = ET.Element(root)
        _fill_xml(el, body)
        payload = b'<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(el, encoding="utf-8")
        ctype = "application/problem+xml; charset=utf-8" if is_problem else "application/xml; charset=utf-8"
    else:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        ctype = "application/problem+json; charset=utf-8" if is_problem else "application/json; charset=utf-8"
    resp = Response(payload, status=status, content_type=ctype)
    for name, value in (headers or {}).items():
        resp.headers[name] = value
    return resp


def empty(status, headers=None):
    """A response with no body (204, 304) - so no Content-Type either."""
    resp = Response(status=status)
    resp.headers.pop("Content-Type", None)
    for name, value in (headers or {}).items():
        resp.headers[name] = value
    return resp


# --------------------------------------------------------------------------
# Request pipeline: negotiate -> rate limit -> authenticate
# --------------------------------------------------------------------------
def bearer_token():
    parts = request.headers.get("Authorization", "").split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].strip():
        return parts[1].strip()
    return None


@app.before_request
def before():
    g.request_id = uuid.uuid4().hex[:12]
    g.fmt = "json"
    g.rl = None
    if request.method == "OPTIONS":          # CORS preflight / capability probe
        return None

    fmt = negotiate(request.headers.get("Accept"))
    if fmt is None:
        raise ApiError("not-acceptable",
                       "This service can produce application/json and application/xml.")
    g.fmt = fmt

    token = bearer_token()
    g.client = token or "ip:" + (request.remote_addr or "unknown")
    allowed, remaining, retry_after = store.rate_hit(g.client, RATE_LIMIT, RATE_WINDOW)
    g.rl = (RATE_LIMIT, remaining)
    if not allowed:
        raise ApiError("rate-limited", "Request budget used up; wait before retrying.",
                       headers={"Retry-After": str(retry_after)})

    if request.path.startswith("/orders") and not token:
        raise ApiError("unauthorized", "Send Authorization: Bearer <token>.",
                       headers={"WWW-Authenticate": 'Bearer realm="campuseats"'})


@app.after_request
def after(resp):
    h = resp.headers
    h["X-Request-ID"] = g.get("request_id", "-")
    h["X-Content-Type-Options"] = "nosniff"
    h["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    h["Access-Control-Allow-Origin"] = CORS_ORIGIN
    h["Access-Control-Expose-Headers"] = EXPOSE_HEADERS
    h["Vary"] = "Accept, Accept-Encoding, Origin"
    if g.get("rl"):
        h["X-RateLimit-Limit"] = str(g.rl[0])
        h["X-RateLimit-Remaining"] = str(g.rl[1])
    if resp.status_code >= 400 and "Cache-Control" not in h:
        h["Cache-Control"] = "no-store"
    # gzip large successful bodies
    if (resp.status_code == 200 and not resp.direct_passthrough
            and "Content-Encoding" not in h
            and "gzip" in request.headers.get("Accept-Encoding", "")):
        data = resp.get_data()
        if len(data) >= 1024:
            resp.set_data(gzip.compress(data))
            h["Content-Encoding"] = "gzip"
    return resp


# --------------------------------------------------------------------------
# Error handlers: every failure leaves through ONE door
# --------------------------------------------------------------------------
@app.errorhandler(ApiError)
def handle_api_error(exc):
    body = problem(exc.key, exc.detail, instance=request.path, errors=exc.errors)
    return render(body, body["status"], root="problem", headers=exc.headers, is_problem=True)


@app.errorhandler(HTTPException)
def handle_http_exception(exc):
    if exc.code == 404:
        return handle_api_error(ApiError("route-not-found", f"No such resource: {request.path}"))
    if exc.code == 405:
        allow = ", ".join(sorted(exc.valid_methods or []))
        return handle_api_error(ApiError("method-not-allowed",
                                         f"{request.method} is not supported here.",
                                         headers={"Allow": allow}))
    body = {"type": "about:blank", "title": exc.name, "status": exc.code,
            "detail": exc.description, "instance": request.path}
    return render(body, exc.code, root="problem", is_problem=True)


@app.errorhandler(Exception)
def handle_unexpected(exc):
    # B4: log the detail on the server, send the client a clean message only.
    app.logger.exception("unhandled error (request %s)", g.get("request_id"))
    return handle_api_error(ApiError(
        "internal-error",
        f"Unexpected server error. Quote request id {g.get('request_id', '-')} to support."))


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def read_json_body():
    """Return the parsed JSON object, or raise 415 / 400."""
    raw = request.get_data()
    if request.mimetype != "application/json" and not request.mimetype.endswith("+json"):
        raise ApiError("unsupported-media-type", "Send the body as Content-Type: application/json.")
    if not raw.strip():
        raise ApiError("malformed-body", "The request body is empty; expected a JSON object.")
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise ApiError("malformed-body", "The request body is not valid JSON.")
    if not isinstance(body, dict):
        raise ApiError("malformed-body", "The JSON body must be an object, not a list or value.")
    return body


def get_owned(raw_id):
    """Look up an order; someone else's order looks exactly like a missing one."""
    order = store.get(int(raw_id)) if raw_id.isdigit() else None
    if order is None or order.owner != g.client:
        raise ApiError("order-not-found", f"No order with id '{raw_id}'.")
    return order


def etag_of(order):
    """Changes whenever the order changes (version is bumped on every update)."""
    return '"' + hashlib.sha1(f"{order.id}:{order.version}".encode()).hexdigest()[:16] + '"'


def etag_matches(header, tag, weak_ok):
    if not header:
        return False
    if header.strip() == "*":
        return True
    tags = [t.strip() for t in header.split(",")]
    if weak_ok:
        tags = [t[2:] if t.startswith("W/") else t for t in tags]
    return tag in tags


def check_if_match(order, required):
    header = request.headers.get("If-Match")
    if header is None:
        if required:
            raise ApiError("precondition-required",
                           "Send If-Match with the order's current ETag (GET the order first).")
        return
    if not etag_matches(header, etag_of(order), weak_ok=False):
        raise ApiError("precondition-failed",
                       "The order changed since you read it. GET it again and retry.")


def options_response(allow):
    resp = empty(204, {
        "Allow": allow,
        "Access-Control-Allow-Methods": allow,
        "Access-Control-Allow-Headers": ALLOW_HEADERS,
        "Access-Control-Max-Age": "600",
    })
    return resp


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.get("/health")
def health():
    return render({"status": "ok"}, root="health")


@app.route("/orders", methods=["OPTIONS"])
def orders_options():
    return options_response("GET, HEAD, POST, OPTIONS")


@app.route("/orders/<order_id>", methods=["OPTIONS"])
def order_options(order_id):
    return options_response("GET, HEAD, PATCH, DELETE, OPTIONS")


@app.post("/orders")
def create_order():
    body = read_json_body()

    # C4: validate FIRST, collect every error, before touching any field.
    errors = validate(body)
    if errors:
        key = "empty-cart" if body.get("items") == [] else "validation-failed"
        detail = ("The cart has no items." if key == "empty-cart"
                  else f"{len(errors)} field(s) failed validation.")
        raise ApiError(key, detail, errors=errors)

    # C7: idempotency. Same key + same body = same order, no second charge.
    idem_key = request.headers.get("Idempotency-Key")
    fingerprint = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    if idem_key is not None:
        idem_key = idem_key.strip()
        if not idem_key or len(idem_key) > 128:
            raise ApiError("validation-failed", "Idempotency-Key is invalid.",
                           errors=[{"field": "Idempotency-Key",
                                    "message": "must be 1-128 characters"}])
        state, original = store.idem_begin(g.client, idem_key, fingerprint)
        if state == "replay":
            return render(original.as_json(), 201, headers={
                "Location": f"/orders/{original.id}", "ETag": etag_of(original),
                "Cache-Control": "no-store", "Idempotent-Replayed": "true"})
        if state == "mismatch":
            raise ApiError("idempotency-key-reuse",
                           "This Idempotency-Key was already used with a different request body.")
        if state == "in_progress":
            raise ApiError("request-in-progress",
                           "A request with this Idempotency-Key is still being processed.",
                           headers={"Retry-After": "1"})

    try:
        lines, total = price_items(body["items"])                 # 422 item-unavailable
        pay_key = idem_key or uuid.uuid4().hex
        try:
            paid = payments_client.charge(reference=pay_key, amount=total,
                                          idempotency_key=pay_key)
        except payments_client.PaymentDeclined:
            raise ApiError("payment-declined",
                           "The payment was declined. Try a different payment method.")
        except payments_client.PaymentsUnavailable as exc:
            app.logger.error("payments unavailable: %s", exc)
            # D3 fallback: FAIL (no order is created) - see NOTES.md.
            raise ApiError("payment-unavailable",
                           "Payments are temporarily unavailable. No order was placed; retry shortly.",
                           headers={"Retry-After": "5"})
        except payments_client.UpstreamError as exc:
            app.logger.error("payments upstream error: %s", exc)
            raise ApiError("upstream-error", "A dependent service returned an unexpected answer.")

        order = store.add(owner=g.client, items=lines, address=body["address"].strip(),
                          total=total, payment_id=paid["payment_id"],
                          idempotency_key=idem_key)
    except Exception:
        if idem_key is not None:
            store.idem_abort(g.client, idem_key)                  # free the key on failure
        raise
    if idem_key is not None:
        store.idem_finish(g.client, idem_key, order.id)

    return render(order.as_json(), 201, headers={
        "Location": f"/orders/{order.id}", "ETag": etag_of(order), "Cache-Control": "no-store"})


@app.get("/orders")
def list_orders():
    params, errors = validate_query(request.args)
    if errors:
        raise ApiError("validation-failed", "Invalid query parameters.", errors=errors)
    rows, total = store.list_orders(g.client, **params)
    body = {"items": [o.as_json() for o in rows], "total": total,
            "limit": params["limit"], "offset": params["offset"]}
    return render(body, 200, root="orders", headers={"Cache-Control": "no-store"})


@app.get("/orders/<order_id>")
def get_order(order_id):
    order = get_owned(order_id)
    tag = etag_of(order)
    cache = "private, max-age=30, must-revalidate"
    if etag_matches(request.headers.get("If-None-Match"), tag, weak_ok=True):
        return empty(304, {"ETag": tag, "Cache-Control": cache})     # C1
    return render(order.as_json(), 200, headers={"ETag": tag, "Cache-Control": cache})


@app.patch("/orders/<order_id>")
def patch_order(order_id):
    order = get_owned(order_id)
    check_if_match(order, required=False)                             # C2 -> 412
    body = read_json_body()
    errors = validate_patch(body)
    if errors:
        raise ApiError("validation-failed", f"{len(errors)} field(s) failed validation.",
                       errors=errors)
    if order.status != "placed":
        raise ApiError("illegal-transition",
                       f"The address can only change while the order is 'placed' "
                       f"(it is '{order.status}').")
    store.update(order, address=body["address"].strip())
    return render(order.as_json(), 200, headers={"ETag": etag_of(order), "Cache-Control": "no-store"})


@app.delete("/orders/<order_id>")
def delete_order(order_id):
    order = get_owned(order_id)
    if order.status not in ("cancelled", "delivered"):
        raise ApiError("illegal-transition",
                       f"Only cancelled or delivered orders can be removed (it is '{order.status}').")
    store.delete(order.id)
    return empty(204)


@app.post("/orders/<order_id>/cancellation")
def cancel_order(order_id):
    order = get_owned(order_id)
    if order.status != "placed":
        raise ApiError("illegal-transition",
                       f"Only an order that is 'placed' can be cancelled (it is '{order.status}').")
    store.update(order, status="cancelled")
    return render(order.as_json(), 200, headers={"ETag": etag_of(order), "Cache-Control": "no-store"})


@app.post("/orders/<order_id>/progression")
def advance_order(order_id):
    """Move the order to its next status. Repeating it would skip a step, so
    If-Match is REQUIRED: a blind retry then fails with 412 instead of doing damage."""
    order = get_owned(order_id)
    check_if_match(order, required=True)
    nxt = NEXT_STATUS.get(order.status)
    if nxt is None:
        raise ApiError("illegal-transition",
                       f"An order that is '{order.status}' cannot move forward.")
    store.update(order, status=nxt)
    return render(order.as_json(), 200, headers={"ETag": etag_of(order), "Cache-Control": "no-store"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
