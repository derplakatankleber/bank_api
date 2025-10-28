"""Application factory for the FastAPI service."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .routers import accounts, transactions
from .web import router as web_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(title="bank-api", version="0.1.0")

    session_secret = os.getenv("BANK_API_SESSION_SECRET", "insecure-development-secret")
    app.add_middleware(SessionMiddleware, secret_key=session_secret)

    static_path = Path(__file__).resolve().parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    @app.get("/health", tags=["health"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(web_router)
    app.include_router(accounts.router)
    app.include_router(transactions.router)

    return app


def get_app() -> FastAPI:
    """Compatibility alias for create_app."""

    return create_app()


app = create_app()
