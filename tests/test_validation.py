"""Validation tests for the POST /orders contract."""

import pytest


@pytest.mark.parametrize("quantity", [0, -1, -100])
def test_invalid_quantity_is_rejected(client, quantity):
    response = client.post(
        "/orders", json={"product_name": "Widget", "quantity": quantity, "unit_price": 10}
    )
    assert response.status_code == 422
    assert any("quantity" in str(err["loc"]) for err in response.json()["detail"])


@pytest.mark.parametrize("unit_price", [0, -0.01, -50])
def test_invalid_unit_price_is_rejected(client, unit_price):
    response = client.post(
        "/orders", json={"product_name": "Widget", "quantity": 1, "unit_price": unit_price}
    )
    assert response.status_code == 422
    assert any("unit_price" in str(err["loc"]) for err in response.json()["detail"])


def test_missing_product_name_is_rejected(client):
    response = client.post("/orders", json={"quantity": 1, "unit_price": 10})
    assert response.status_code == 422
    assert any("product_name" in str(err["loc"]) for err in response.json()["detail"])


@pytest.mark.parametrize("product_name", ["", "   "])
def test_blank_product_name_is_rejected(client, product_name):
    response = client.post(
        "/orders", json={"product_name": product_name, "quantity": 1, "unit_price": 10}
    )
    assert response.status_code == 422
