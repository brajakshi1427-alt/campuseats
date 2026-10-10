"""make_transcript.py - runs REAL curl commands against your running service and
saves everything to transcript.txt (the file the assignment asks for).

  python make_transcript.py v      -> curl -v   (Assignment 5 / 6: shows request + response)
  python make_transcript.py i      -> curl -i   (Assignment 4)

Before running: start payments_stub.py and app.py (see README.md).
"""
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime

MODE = sys.argv[1] if len(sys.argv) > 1 else "v"
BASE = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:5000"
CURL = shutil.which("curl.exe") or shutil.which("curl") or "curl"
FLAG = "-v" if MODE == "v" else "-i"
TOKEN = "Bearer student-1"
out = []


def run(title, method, path, headers=(), body=None, show=True):
    """Run one curl call, append the exact command + output to the transcript."""
    cmd = [CURL, "-s", FLAG, "-X", method, BASE + path]
    shown = f"curl {FLAG} -X {method} {BASE}{path}"
    for h in headers:
        cmd += ["-H", h]
        shown += ' -H "' + h.replace('"', '\\"') + '"'
    if body is not None:
        data = body if isinstance(body, str) else json.dumps(body)
        cmd += ["-d", data]
        shown += f" -d '{data}'"
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = res.stdout.decode("utf-8", "replace")
    if show:
        out.append(f"\n{'=' * 78}\n## {title}\n$ {shown}\n{'-' * 78}\n{text}")
        print(f"done: {title}")
    return text


def etag(text):
    m = re.search(r'(?i)^[<\s]*etag:\s*("[^"]+")', text, re.M)
    return m.group(1) if m else '"missing"'


J = "Content-Type: application/json"
auth = f"Authorization: {TOKEN}"
good = {"items": [{"item_id": "dosa", "qty": 2}, {"item_id": "tea", "qty": 1}],
        "address": "Hostel B, Room 12"}

out.append(f"CampusEats Orders - curl transcript ({datetime.now():%Y-%m-%d %H:%M})\nmode: curl {FLAG}")

# ---- success paths --------------------------------------------------------
run("1. SUCCESS: create an order (201 + Location)", "POST", "/orders",
    [J, auth, "Idempotency-Key: demo-key-001"], good)
run("2. IDEMPOTENT REPEAT: same body + same Idempotency-Key returns the original",
    "POST", "/orders", [J, auth, "Idempotency-Key: demo-key-001"], good)
read = run("3. READ one order (200 + ETag + Cache-Control)", "GET", "/orders/1", [auth])
tag = etag(read)
run("4. CONDITIONAL GET: If-None-Match with current ETag -> 304 Not Modified", "GET", "/orders/1",
    [auth, f"If-None-Match: {tag}"])
run("5. CONDITIONAL WRITE: PATCH with current ETag -> 200, new ETag", "PATCH", "/orders/1",
    [J, auth, f"If-Match: {tag}"], {"address": "Library gate"})
run("6. CONDITIONAL WRITE with the OLD ETag -> 412 Precondition Failed", "PATCH", "/orders/1",
    [J, auth, f"If-Match: {tag}"], {"address": "Canteen"})
run("7. LIST with query string (filter + sort + page)", "GET",
    "/orders?status=placed&sort=-total&limit=5&offset=0", [auth])
run("8. CONTENT NEGOTIATION: Accept: application/xml", "GET", "/orders/1",
    [auth, "Accept: application/xml"])
run("9. OPTIONS: Allow header lists the methods", "OPTIONS", "/orders/1", [])
run("10. CORS PREFLIGHT from another origin", "OPTIONS", "/orders",
    ["Origin: http://localhost:3000", "Access-Control-Request-Method: POST",
     "Access-Control-Request-Headers: authorization, content-type, idempotency-key"])
run("11. METHOD OVERRIDE fallback: POST + X-HTTP-Method-Override: PATCH", "POST", "/orders/1",
    [J, auth, "X-HTTP-Method-Override: PATCH"], {"address": "Gate 2"})

# ---- failure paths --------------------------------------------------------
run("12. FAILURE 400: malformed JSON", "POST", "/orders", [J, auth], '{"items": [')
run("13. FAILURE 422: two bad fields at once (field-level errors[])", "POST", "/orders",
    [J, auth], {"items": [{"item_id": "dosa", "qty": 0}], "address": ""})
run("14. FAILURE 422: empty cart", "POST", "/orders", [J, auth], {"items": [], "address": "Hostel B"})
run("15. FAILURE 422: item unavailable", "POST", "/orders", [J, auth],
    {"items": [{"item_id": "pizza", "qty": 1}], "address": "Hostel B"})
run("16. FAILURE 422: payment declined (Payments said no, mapped to our error)", "POST",
    "/orders", [J, auth], {"items": [{"item_id": "thali", "qty": 20}], "address": "Hostel B"})
run("17. FAILURE 404: unknown order id", "GET", "/orders/999", [auth])
run("18. FAILURE 401: no Authorization header", "GET", "/orders", [])
run("19. FAILURE 406: Accept: text/html", "GET", "/orders/1", [auth, "Accept: text/html"])
run("20. FAILURE 428: progression without If-Match", "POST", "/orders/1/progression", [auth])
latest = etag(run("(read for ETag)", "GET", "/orders/1", [auth], show=False))
run("21. STATE CHANGE: progression with If-Match (placed -> preparing)", "POST",
    "/orders/1/progression", [auth, f"If-Match: {latest}"])
run("22. FAILURE 409: cancel an order that is already being prepared (illegal-transition)",
    "POST", "/orders/1/cancellation", [auth])
run("23. FAILURE 422: Idempotency-Key reused with a DIFFERENT body", "POST", "/orders",
    [J, auth, "Idempotency-Key: demo-key-001"], {"items": [{"item_id": "tea", "qty": 1}], "address": "X"})

# ---- delete flow ----------------------------------------------------------
run("24. create a second order", "POST", "/orders", [J, auth], good)
run("25. cancel it (200)", "POST", "/orders/2/cancellation", [auth])
run("26. DELETE it (204, no body)", "DELETE", "/orders/2", [auth])
run("27. FAILURE 404: it is gone", "GET", "/orders/2", [auth])

# ---- rate limit (separate client so it does not disturb the rest) ---------
first = run("28. RATE LIMIT: first request of a fresh client (note the X-RateLimit headers)",
            "GET", "/orders", ["Authorization: Bearer burst-client"])
for _ in range(60):
    text = run("rate", "GET", "/orders", ["Authorization: Bearer burst-client"], show=False)
    if "HTTP/1.1 429" in text:
        out.append(f"\n{'=' * 78}\n## 29. FAILURE 429: budget exceeded (note Retry-After)\n"
                   f"$ curl {FLAG} -X GET {BASE}/orders -H \"Authorization: Bearer burst-client\"\n"
                   f"{'-' * 78}\n{text}")
        print("done: 29. 429")
        break

with open("transcript.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) + "\n")
print("\nSaved transcript.txt")
