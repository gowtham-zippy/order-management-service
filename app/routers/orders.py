"""Order creation and retrieval endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.models import ErrorResponse, OrderCreateRequest, OrderResponse
from app.storage import repository

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": ErrorResponse}},
)
def create_order(payload: OrderCreateRequest) -> OrderResponse:
    order = repository.create(
        product_name=payload.product_name,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
    )
    return OrderResponse(**order.to_dict())


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_order(order_id: str) -> OrderResponse:
    order = repository.get(order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found",
        )
    return OrderResponse(**order.to_dict())
