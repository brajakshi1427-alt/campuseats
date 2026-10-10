"""payments_stub.py - a tiny stand-in Payments service so the demo runs alone.

Use your Tutorial 4 Payments service instead if you have it running.
  python payments_stub.py          (listens on port 5001)
Rules:  amount > 1000  -> 402 declined      same Idempotency-Key -> same payment
Env:    PAYMENT_DELAY=3  makes every call slow (to demonstrate the timeout).
"""
import os
import time
import uuid

from flask import Flask, jsonify, request

app = Flask(__name__)
seen = {}


@app.post("/payments")
def pay():
    time.sleep(float(os.environ.get("PAYMENT_DELAY", "0")))
    key = request.headers.get("Idempotency-Key", "")
    if key in seen:
        return jsonify(seen[key]), 200
    body = request.get_json(silent=True) or {}
    if not isinstance(body.get("amount"), int) or body["amount"] < 1:
        return jsonify({"error": "bad_request"}), 400
    if body["amount"] > 1000:
        return jsonify({"error": "card_declined"}), 402
    seen[key] = {"id": "pay_" + uuid.uuid4().hex[:10], "status": "succeeded"}
    return jsonify(seen[key]), 201


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
