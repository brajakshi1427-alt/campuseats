from app import app

def test_create_order():
    client = app.test_client()

    r = client.post(
        "/orders",
        json={
            "studentId": 1,
            "itemId": 5,
            "quantity": 2
        }
    )

    assert r.status_code == 201

def test_idempotent_repeat():
    client = app.test_client()

    headers = {"Idempotency-Key": "abc123"}

    client.post(
        "/orders",
        json={
            "studentId": 1,
            "itemId": 5,
            "quantity": 2
        },
        headers=headers
    )

    r2 = client.post(
        "/orders",
        json={
            "studentId": 1,
            "itemId": 5,
            "quantity": 2
        },
        headers=headers
    )

    assert r2.status_code == 201

def test_bad_request():
    client = app.test_client()

    r = client.post(
        "/orders",
        json={"studentId": 1}
    )

    assert r.status_code == 400

def test_not_found():
    client = app.test_client()

    r = client.get("/orders/999")

    assert r.status_code == 404
