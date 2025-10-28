"""Reusable dependencies for the FastAPI application."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from ..client.banking import BankingClient
from ..persistence.database import DatabaseSessionManager
from ..services.accounts import AccountService
from ..services.transactions import TransactionService


@lru_cache
def get_session_manager() -> DatabaseSessionManager:
    """Return a singleton database session manager."""

    return DatabaseSessionManager()


@lru_cache
def get_banking_client() -> BankingClient:
    """Return a singleton banking client."""

    return BankingClient()


def get_account_service(
    client: BankingClient = Depends(get_banking_client),
    session_manager: DatabaseSessionManager = Depends(get_session_manager),
) -> AccountService:
    """Provide an account service instance for request handlers."""

    return AccountService(client, session_manager=session_manager)


def get_transaction_service(
    client: BankingClient = Depends(get_banking_client),
    session_manager: DatabaseSessionManager = Depends(get_session_manager),
) -> TransactionService:
    """Provide a transaction service instance for request handlers."""

    return TransactionService(client, session_manager=session_manager)
