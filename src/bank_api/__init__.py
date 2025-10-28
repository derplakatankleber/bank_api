"""Client and data models for the comdirect REST API."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Dict

from .client.banking import BankingClient
from .client.base import RetryConfig
from .client.session import SessionClient
from .exceptions import ComdirectAPIError


def create_app(*args: Any, **kwargs: Any) -> Any:
    """Create the FastAPI application without importing FastAPI at module import time."""

    from .api import create_app as _create_app

    return _create_app(*args, **kwargs)


_LAZY_IMPORTS: Dict[str, str] = {
    "AccountService": "bank_api.services",
    "TransactionService": "bank_api.services",
    "DataRefreshScheduler": "bank_api.jobs",
    "DatabaseConfig": "bank_api.persistence",
    "DatabaseSessionManager": "bank_api.persistence",
    "TransactionRepository": "bank_api.persistence",
    "PositionRepository": "bank_api.persistence",
    "SyncLogRepository": "bank_api.persistence",
    "Transaction": "bank_api.persistence",
    "Position": "bank_api.persistence",
    "SyncLog": "bank_api.persistence",
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module = import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_LAZY_IMPORTS.keys()))


__all__ = [
    "BankingClient",
    "SessionClient",
    "RetryConfig",
    "ComdirectAPIError",
    "AccountService",
    "TransactionService",
    "DataRefreshScheduler",
    "DatabaseConfig",
    "DatabaseSessionManager",
    "TransactionRepository",
    "PositionRepository",
    "SyncLogRepository",
    "Transaction",
    "Position",
    "SyncLog",
    "create_app",
]
