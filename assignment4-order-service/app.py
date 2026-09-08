from flask import Flask, request, jsonify
app = Flask(__name__)
orders = []
@app.get("/")
def home():
    return {"message": "CampusEats Order Service"}
@app.get("/orders")
def get_orders():
    return jsonify(orders)
@app.post("/orders")
def create_order():
    data = request.get_json()
    order = {
        "id": len(orders) + 1,
        "studentId": data["studentId"],
        "itemId": data["itemId"],
        "quantity": data["quantity"],
        "status": "PLACED"
    }
    orders.append(order)
    return jsonify(order), 201
if __name__ == "__main__":
    app.run(debug=True)
