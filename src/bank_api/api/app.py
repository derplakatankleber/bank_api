"""Application factory for the FastAPI service."""
from __future__ import annotations

from fastapi import FastAPI

from .routers import accounts, transactions


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(title="bank-api", version="0.1.0")

    @app.get("/health", tags=["health"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(accounts.router)
    app.include_router(transactions.router)

    return app


def get_app() -> FastAPI:
    """Compatibility alias for create_app."""

    return create_app()


app = create_app()
