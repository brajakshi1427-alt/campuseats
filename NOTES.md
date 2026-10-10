# CS 543 - Assignment 6 - NOTES

<!--TEAM-->
**Team ID:** TEAM-00

| Roll No | Name |
|---|---|
| ROLL-1 | Member One |
<!--/TEAM-->

Service: Orders (same service as Assignments 4 and 5, no new service). Folder: `Assignment6/`

---

## Answers

**1. Status map (every endpoint, success and each failure, with why).**

| Endpoint | Success | Failures |
|---|---|---|
| POST `/orders` | **201** + `Location` (a new order exists) | 400 body not JSON; 401 no token; 415 wrong Content-Type; 422 fields wrong / empty cart / item unavailable / payment declined / key reuse; 409 same key still running; 429 too many; 502 Payments answered oddly; 503 Payments down (nothing created) |
| GET `/orders` | **200** | 401; 422 bad query (`limit=0`); 429 |
| GET `/orders/{id}` | **200** (or **304** if the ETag still matches) | 401; 404 no such order (also for someone else's order); 406 cannot produce that Accept type |
| PATCH `/orders/{id}` | **200** | 400; 401; 404; 409 order no longer `placed`; 412 stale ETag; 422 bad field |
| DELETE `/orders/{id}` | **204** (no body) | 401; 404; 409 order not cancelled/delivered |
| POST `/orders/{id}/cancellation` | **200** | 401; 404; 409 order no longer `placed` |
| POST `/orders/{id}/progression` | **200** | 401; 404; 409 nothing further to do; 412 stale ETag; 428 If-Match missing |

The status IS the result: no failure is ever returned inside a `200`.

**2. Type catalogue** (`type` = `https://campuseats.example/problems/<key>`).

| Key | Status | Triggered by |
|---|---|---|
| `malformed-body` | 400 | body empty, not valid JSON, or not a JSON object |
| `unauthorized` | 401 | missing or empty bearer token |
| `order-not-found` | 404 | id does not exist (or belongs to another client) |
| `route-not-found` / `method-not-allowed` | 404 / 405 | unknown URL / unsupported method (adds `Allow`) |
| `not-acceptable` | 406 | `Accept` asks for a type we cannot produce |
| `illegal-transition` | 409 | cancel/edit/delete/advance in the wrong status |
| `request-in-progress` | 409 | same Idempotency-Key while the first call still runs |
| `precondition-failed` | 412 | `If-Match` ETag is stale |
| `unsupported-media-type` | 415 | body not sent as `application/json` |
| `validation-failed` | 422 | one or more fields invalid (`errors[]` lists each) |
| `empty-cart` | 422 | `items` is an empty list |
| `item-unavailable` | 422 | item unknown or sold out (e.g. `pizza`) |
| `payment-declined` | 422 | Payments refused the charge |
| `idempotency-key-reuse` | 422 | same key sent with a different body |
| `precondition-required` | 428 | `If-Match` missing on progression |
| `rate-limited` | 429 | per-client budget used up (adds `Retry-After`) |
| `internal-error` | 500 | unexpected crash (nothing internal shown) |
| `upstream-error` | 502 | Payments answered with an unexpected status |
| `payment-unavailable` | 503 | Payments unreachable after retries (adds `Retry-After`) |

**3. One Problem Details body, fields labelled.**

```json
{
  "type": "https://campuseats.example/problems/illegal-transition",
  "title": "Illegal state transition",
  "status": 409,
  "detail": "Only an order that is 'placed' can be cancelled (it is 'preparing').",
  "instance": "/orders/1/cancellation"
}
```
`type`: stable machine-readable id of the kind of problem. `title`: short human summary of that kind (same every time).
`status`: the HTTP status, repeated in the body. `detail`: explanation of this particular occurrence.
`instance`: the URL the problem happened on. Sent with `Content-Type: application/problem+json; charset=utf-8`.

**4. A field-level 422 with two bad fields.**
Request: `POST /orders` with `{"items": [{"item_id": "dosa", "qty": 0}], "address": ""}`

```json
{
  "type": "https://campuseats.example/problems/validation-failed",
  "title": "Validation failed",
  "status": 422,
  "detail": "2 field(s) failed validation.",
  "instance": "/orders",
  "errors": [
    {"field": "items[0].qty", "message": "must be an integer >= 1"},
    {"field": "address", "message": "must be a non-empty string"}
  ]
}
```
`validate()` collects every error first and returns them all in one response, not just the first.

**5. Which endpoints are safe to retry, and which statuses say so.**
Safe to retry: GET, HEAD, OPTIONS, PATCH, DELETE, POST cancellation (idempotent), and `POST /orders` *only with* the same
`Idempotency-Key`. Statuses that tell a client "transient, try again": **429** and **503** (both with `Retry-After`; 502 and
network timeouts too). A 4xx (400, 401, 404, 409, 422) must never be retried unchanged. 412 means "re-read the order first,
then retry". `POST .../progression` is retried only after re-reading (fresh ETag).

**6. Where an internal error became a clean client error, and what was hidden.**
* Any unexpected exception in a handler becomes `500 internal-error`; the stack trace and messages (e.g. a database error)
  are logged on the server with a `request id`, and the client only gets that id.
* Payments' own refusal (`card_declined`, status 402) becomes `422 payment-declined`; its vocabulary and status code never reach the student.
* Payments being down or timing out becomes `503 payment-unavailable`; the address and exception details stay in the log.
* Another student's order becomes `404 order-not-found`, hiding that it exists.

**7. The same order as JSON and as XML.** *(The question text in the handout stops mid-sentence after "and"; check the full wording and add what it asks.)*

`Accept: application/json` (the default):
```json
{"id": 1, "status": "placed", "items": [{"item_id": "dosa", "name": "Masala Dosa", "qty": 2, "unit_price": 40, "line_total": 80}, {"item_id": "tea", "name": "Masala Tea", "qty": 1, "unit_price": 10, "line_total": 10}], "address": "Hostel B, Room 12", "total": 90, "currency": "INR", "paid": true, "links": {"self": "/orders/1", "cancellation": "/orders/1/cancellation"}}
```
`Accept: application/xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?><order><id>1</id><status>placed</status><items><item><item_id>dosa</item_id><name>Masala Dosa</name><qty>2</qty><unit_price>40</unit_price><line_total>80</line_total></item><item><item_id>tea</item_id><name>Masala Tea</name><qty>1</qty><unit_price>10</unit_price><line_total>10</line_total></item></items><address>Hostel B, Room 12</address><total>90</total><currency>INR</currency><paid>true</paid><links><self>/orders/1</self><cancellation>/orders/1/cancellation</cancellation></links></order>
```
`Accept: text/html` returns `406 not-acceptable`.

## D4. No regressions

The Assignment 5 behaviours still hold: idempotency (`test_idempotent_repeat_returns_original`,
`test_same_key_different_body_is_422`), timeouts, retries and backoff (`tests/test_payments_client.py`).
`pytest -v` passes all tests.

---

## Evidence

* `transcript.txt` made with `python make_transcript.py v`: success path (201 + Location + body), every failure (empty cart, qty <= 0, unknown id, illegal transition, rate limit), and the XML request.
* `pytest -v` output: `pytest-output.txt` (all tests passed)
* `openapi.yaml` with the status codes and the Problem Details schema.
