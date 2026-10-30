"""Pydantic request/response models for the Order Management Service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderCreateRequest(BaseModel):
    """Inbound payload for creating an order."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    product_name: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(..., gt=0, description="Must be greater than 0")
    unit_price: Decimal = Field(..., gt=0, description="Must be greater than 0")

    @field_validator("product_name")
    @classmethod
    def product_name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("product_name must not be blank")
        return value


class OrderResponse(BaseModel):
    """Outbound representation of a stored order."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    discount_applied: bool
    discount_amount: Decimal
    total: Decimal
    created_at: datetime


class HealthResponse(BaseModel):
    """Outbound representation of the service health probe."""

    status: str
    service: str
    version: str


class ErrorResponse(BaseModel):
    """Uniform error envelope."""

    detail: str
