"""FastAPI application entry point."""

from fastapi import FastAPI

from app import __version__
from app.routers import health, orders


def create_app() -> FastAPI:
    application = FastAPI(
        title="Order Management Service",
        description="Creates and retrieves orders with volume-discount pricing.",
        version=__version__,
    )
    application.include_router(health.router)
    application.include_router(orders.router)
    return application


app = create_app()
