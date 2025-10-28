"""Authentication helpers for the REST API."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader


API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(slots=True)
class AuthSettings:
    """Runtime configuration for API authentication."""

    api_key: str


@lru_cache
def get_auth_settings() -> AuthSettings:
    """Return authentication settings sourced from the environment."""

    api_key = os.getenv("BANK_API_KEY", "")
    return AuthSettings(api_key=api_key)


def require_api_key(
    provided_key: str | None = Depends(API_KEY_HEADER),
    settings: AuthSettings = Depends(get_auth_settings),
) -> str:
    """Validate the caller supplied API key."""

    if not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured",
        )

    if not provided_key or not secrets.compare_digest(provided_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

    return provided_key
