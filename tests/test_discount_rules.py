"""Discount boundary tests.

These are the tests that intentionally fail if the discount rule is changed
from `subtotal >= 1000` to `subtotal > 1000`, which is used to demonstrate
pipeline failure blocking.
"""

from decimal import Decimal

import pytest

from app.pricing import calculate_price


def test_subtotal_below_threshold_has_no_discount(client):
    response = client.post("/orders", json={"product_name": "Widget", "quantity": 5, "unit_price": 100})
    assert response.status_code == 201
    body = response.json()
    assert Decimal(body["subtotal"]) == Decimal("500.00")
    assert body["discount_applied"] is False
    assert Decimal(body["discount_amount"]) == Decimal("0.00")
    assert Decimal(body["total"]) == Decimal("500.00")


def test_subtotal_exactly_at_threshold_gets_discount(client):
    """BOUNDARY TEST: subtotal == 1000 must receive the 10% discount."""
    response = client.post("/orders", json={"product_name": "Widget", "quantity": 10, "unit_price": 100})
    assert response.status_code == 201
    body = response.json()
    assert Decimal(body["subtotal"]) == Decimal("1000.00")
    assert body["discount_applied"] is True
    assert Decimal(body["discount_amount"]) == Decimal("100.00")
    assert Decimal(body["total"]) == Decimal("900.00")


def test_subtotal_above_threshold_gets_discount(client):
    response = client.post("/orders", json={"product_name": "Widget", "quantity": 10, "unit_price": 250})
    assert response.status_code == 201
    body = response.json()
    assert Decimal(body["subtotal"]) == Decimal("2500.00")
    assert body["discount_applied"] is True
    assert Decimal(body["discount_amount"]) == Decimal("250.00")
    assert Decimal(body["total"]) == Decimal("2250.00")


@pytest.mark.parametrize(
    ("quantity", "unit_price", "expected_total"),
    [
        (1, "999.99", "999.99"),
        (1, "1000.00", "900.00"),
        (1, "1000.01", "900.01"),
    ],
)
def test_discount_boundary_matrix(quantity, unit_price, expected_total):
    breakdown = calculate_price(quantity, Decimal(unit_price))
    assert breakdown.total == Decimal(expected_total)
