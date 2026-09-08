from flask import Flask, request, jsonify, url_for
from models import Order
from store import orders, idempotency_keys
from errors import problem
app = Flask(__name__)
counter = 1
def validate(data):
    required = ["studentId", "itemId", "quantity"]
    for field in required:
        if field not in data:
            return False
    return True
@app.post("/orders")
def create_order():
    global counter
    data = request.get_json()
    if not data:
        return problem(400, "Bad Request", "Missing JSON body")
    if not validate(data):
        return problem(400, "Bad Request", "Required field missing")
    key = request.headers.get("Idempotency-Key")
    if key and key in idempotency_keys:
        existing = idempotency_keys[key]
        return jsonify(existing.as_json()), 201
    order = Order(
        counter,
        data["studentId"],
        data["itemId"],
        data["quantity"],
        internal_token=f"token-{counter}"
    )
    orders[counter] = order
    if key:
        idempotency_keys[key] = order
    response = jsonify(order.as_json())
    response.status_code = 201
    response.headers["Location"] = f"/orders/{counter}"
    counter += 1
    return response
@app.get("/orders/<int:order_id>")
def get_order(order_id):
    order = orders.get(order_id)
    if not order:
        return problem(404, "Not Found", "Order does not exist")
    return jsonify(order.as_json())
@app.get("/orders")
def list_orders():
    status = request.args.get("status")
    result = []
    for order in orders.values():
        if status is None or order.status == status:
            result.append(order.as_json())
    return jsonify(result)
@app.post("/orders/<int:order_id>/cancellation")
def cancel_order(order_id):
    order = orders.get(order_id)
    if not order:
        return problem(404, "Not Found", "Order does not exist")
    if order.status == "CANCELLED":
        return problem(409, "Conflict", "Order already cancelled")
    order.status = "CANCELLED"
    return jsonify(order.as_json()), 202
if __name__ == "__main__":
    app.run(debug=True)
