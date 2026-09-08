class Order:
    def __init__(self, order_id, item, quantity):
        self.order_id = order_id
        self.item = item
        self.quantity = quantity
        self.internal_id = "INT-" + str(order_id)
        self.status = "created"
    def as_json(self):
        return {
            "id": self.order_id,
            "item": self.item,
            "quantity": self.quantity,
            "status": self.status
        }
