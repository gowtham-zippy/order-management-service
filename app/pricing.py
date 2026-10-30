"""Pricing rules for the Order Management Service.

Business rule: a 10% discount applies when the subtotal is greater than or
equal to the discount threshold (1000). The boundary value itself qualifies.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import NamedTuple

DISCOUNT_THRESHOLD = Decimal("1000")
DISCOUNT_RATE = Decimal("0.10")
_CENTS = Decimal("0.01")


class PriceBreakdown(NamedTuple):
    subtotal: Decimal
    discount_applied: bool
    discount_amount: Decimal
    total: Decimal


def _money(value: Decimal) -> Decimal:
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


def qualifies_for_discount(subtotal: Decimal) -> bool:
    return subtotal >= DISCOUNT_THRESHOLD


def calculate_price(quantity: int, unit_price: Decimal) -> PriceBreakdown:
    """Return the subtotal, discount and final total for a line item."""
    subtotal = _money(Decimal(quantity) * Decimal(unit_price))

    if qualifies_for_discount(subtotal):
        discount_amount = _money(subtotal * DISCOUNT_RATE)
        return PriceBreakdown(subtotal, True, discount_amount, _money(subtotal - discount_amount))

    return PriceBreakdown(subtotal, False, _money(Decimal("0")), subtotal)
