"""Health probe endpoint used by the pipeline verification stage."""

from fastapi import APIRouter

from app import __version__
from app.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="healthy", service="order-management-service", version=__version__)
