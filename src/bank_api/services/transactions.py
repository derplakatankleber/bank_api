"""Transaction related service classes."""

from __future__ import annotations

from typing import Any, Optional

from ..client.banking import BankingClient
from ..models.banking import ListResourceAccountTransaction
from ..persistence.database import DatabaseSessionManager
from ..persistence.repositories import TransactionRepository


class TransactionService:
    """High level operations for account transactions."""

    def __init__(
        self,
        client: BankingClient,
        *,
        session_manager: DatabaseSessionManager | None = None,
    ) -> None:
        self._client = client
        self._session_manager = session_manager or DatabaseSessionManager()

    def refresh_transactions(
        self,
        account_id: str,
        *,
        headers: Optional[dict[str, str]] = None,
        transaction_state: Optional[str] = None,
        transaction_direction: Optional[str] = None,
        paging_first: Optional[int] = None,
        with_attr: Optional[str] = None,
    ) -> ListResourceAccountTransaction:
        """Fetch transactions from the API and persist them."""

        response = self._client.get_account_transactions(
            account_id,
            transaction_state=transaction_state,
            transaction_direction=transaction_direction,
            paging_first=paging_first,
            with_attr=with_attr,
            headers=headers,
        )
        with self._session_manager.session_scope() as session:
            repository = TransactionRepository(session)
            repository.upsert_transactions(response.values, account_id)
        return response

    def list_cached_transactions(self, account_id: str) -> list[dict[str, Any]]:
        """Return transactions stored in the persistence layer for the given account."""

        with self._session_manager.session_scope() as session:
            repository = TransactionRepository(session)
            transactions = repository.list_transactions(account_id)
            return [transaction.raw for transaction in transactions if transaction.raw]
