"""Retrieval and 404 handling tests."""


def test_existing_order_is_retrieved(client):
    created = client.post(
        "/orders", json={"product_name": "Widget", "quantity": 2, "unit_price": 25}
    ).json()

    response = client.get(f"/orders/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_missing_order_returns_404(client):
    response = client.get("/orders/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order '00000000-0000-0000-0000-000000000000' not found"


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "order-management-service"
