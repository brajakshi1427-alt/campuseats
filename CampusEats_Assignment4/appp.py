from flask import Flask, request, jsonify
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


def check_auth():
    token = request.headers.get("Authorization")

    if not token or not token.startswith("Bearer "):
        return False

    return True


@app.post("/orders")
def create_order():
    global counter

    if not check_auth():
        return problem(401, "Unauthorized", "Missing bearer token")

    data = request.get_json()

    if not data:
        return problem(400, "Bad Request", "Missing JSON body")

    if not validate(data):
        return problem(400, "Bad Request", "Required field missing")

    key = request.headers.get("Idempotency-Key")

    if key and key in idempotency_keys:
        existing = idempotency_keys[key]

        response = jsonify(existing.as_json())
        response.status_code = 201
        response.headers["Content-Type"] = "application/json"

        return response

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
    response.headers["Content-Type"] = "application/json"

    counter += 1
    return response


@app.get("/orders/<int:order_id>")
def get_order(order_id):

    if not check_auth():
        return problem(401, "Unauthorized", "Missing bearer token")

    order = orders.get(order_id)

    if not order:
        return problem(404, "Not Found", "Order does not exist")

    etag = f'"{order_id}-{order.status}"'

    if request.headers.get("If-None-Match") == etag:
        response = jsonify({})
        response.status_code = 304
        response.headers["ETag"] = etag
        return response

    response = jsonify(order.as_json())

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "max-age=60"
    response.headers["Content-Type"] = "application/json"

    return response


@app.get("/orders")
def list_orders():

    if not check_auth():
        return problem(401, "Unauthorized", "Missing bearer token")

    status = request.args.get("status")

    result = []

    for order in orders.values():
        if status is None or order.status == status:
            result.append(order.as_json())

    response = jsonify(result)

    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = "99"
    response.headers["Content-Type"] = "application/json"

    return response


@app.put("/orders/<int:order_id>")
def update_order(order_id):

    if not check_auth():
        return problem(401, "Unauthorized", "Missing bearer token")

    order = orders.get(order_id)

    if not order:
        return problem(404, "Not Found", "Order does not exist")

    current_etag = f'"{order_id}-{order.status}"'

    if_match = request.headers.get("If-Match")

    if if_match and if_match != current_etag:
        return problem(
            412,
            "Precondition Failed",
            "ETag mismatch"
        )

    data = request.get_json()

    if not data:
        return problem(
            400,
            "Bad Request",
            "Missing JSON body"
        )

    if "quantity" in data:
        order.quantity = data["quantity"]

    return jsonify(order.as_json())


@app.delete("/orders/<int:order_id>")
def delete_order(order_id):

    if not check_auth():
        return problem(401, "Unauthorized", "Missing bearer token")

    if order_id not in orders:
        return problem(
            404,
            "Not Found",
            "Order does not exist"
        )

    del orders[order_id]

    return "", 204


@app.post("/orders/<int:order_id>/cancel")
def cancel_order(order_id):

    if not check_auth():
        return problem(401, "Unauthorized", "Missing bearer token")

    order = orders.get(order_id)

    if not order:
        return problem(404, "Not Found", "Order does not exist")

    if order.status == "CANCELLED":
        return problem(409, "Conflict", "Order already cancelled")

    order.status = "CANCELLED"

    return jsonify(order.as_json()), 202


@app.route("/orders/<int:order_id>", methods=["OPTIONS"])
def options_order(order_id):

    response = jsonify({})

    response.headers["Allow"] = \
        "GET,PUT,DELETE,OPTIONS"

    response.headers["Access-Control-Allow-Origin"] = "*"

    response.headers["Access-Control-Allow-Headers"] = \
        "Authorization, Content-Type, If-Match"

    response.headers["Access-Control-Allow-Methods"] = \
        "GET,PUT,DELETE,OPTIONS"
    return response, 204
if __name__ == "__main__":
    app.run(debug=True)
