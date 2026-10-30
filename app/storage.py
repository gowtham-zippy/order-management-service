"""Thread-safe in-memory order repository."""

from __future__ import annotations

import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional
from uuid import uuid4

from app.pricing import calculate_price


@dataclass(frozen=True)
class Order:
    id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    discount_applied: bool
    discount_amount: Decimal
    total: Decimal
    created_at: datetime

    def to_dict(self) -> dict:
        return asdict(self)


class OrderRepository:
    """In-memory store. Process-local by design; not durable across restarts."""

    def __init__(self) -> None:
        self._orders: Dict[str, Order] = {}
        self._lock = threading.Lock()

    def create(self, product_name: str, quantity: int, unit_price: Decimal) -> Order:
        breakdown = calculate_price(quantity, unit_price)
        order = Order(
            id=str(uuid4()),
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=breakdown.subtotal,
            discount_applied=breakdown.discount_applied,
            discount_amount=breakdown.discount_amount,
            total=breakdown.total,
            created_at=datetime.now(timezone.utc),
        )
        with self._lock:
            self._orders[order.id] = order
        return order

    def get(self, order_id: str) -> Optional[Order]:
        with self._lock:
            return self._orders.get(order_id)

    def clear(self) -> None:
        with self._lock:
            self._orders.clear()


repository = OrderRepository()
