"""Account related service classes."""
from __future__ import annotations

from typing import Optional

from ..client.banking import BankingClient
from ..models.banking import AccountBalance, ListResourceAccountBalance
from ..persistence.database import DatabaseSessionManager
from ..persistence.repositories import PositionRepository


class AccountService:
    """High level operations for account data."""

    def __init__(
        self,
        client: BankingClient,
        *,
        session_manager: DatabaseSessionManager | None = None,
    ) -> None:
        self._client = client
        self._session_manager = session_manager or DatabaseSessionManager()

    def get_balance_summary(
        self,
        user_id: str,
        *,
        headers: Optional[dict[str, str]] = None,
        without_attr: Optional[str] = None,
    ) -> list[dict[str, object]]:
        """Return a simplified view of account balances for dashboards."""

        response = self._client.get_account_balances(
            user_id,
            without_attr=without_attr,
            headers=headers,
        )
        return [self._map_balance(balance) for balance in response.values]

    def refresh_account_balances(
        self,
        user_id: str,
        *,
        headers: Optional[dict[str, str]] = None,
        without_attr: Optional[str] = None,
    ) -> ListResourceAccountBalance:
        """Fetch account balances from the API and persist them."""

        response = self._client.get_account_balances(
            user_id,
            without_attr=without_attr,
            headers=headers,
        )
        with self._session_manager.session_scope() as session:
            repository = PositionRepository(session)
            repository.upsert_balances(response.values)
        return response

    def list_cached_balances(self) -> list[AccountBalance]:
        """Return balances stored in the persistence layer."""

        with self._session_manager.session_scope() as session:
            repository = PositionRepository(session)
            positions = repository.list_positions()
            return [AccountBalance.model_validate(position.raw) for position in positions if position.raw]

    @staticmethod
    def _map_balance(balance: AccountBalance) -> dict[str, object]:
        account_id = balance.accountId or (
            balance.account.accountId if balance.account and balance.account.accountId else None
        )
        currency = None
        amount = None
        if balance.balance and balance.balance.value is not None:
            amount = balance.balance.value
            currency = balance.balance.unit
        elif balance.availableCashAmount and balance.availableCashAmount.value is not None:
            amount = balance.availableCashAmount.value
            currency = balance.availableCashAmount.unit
        return {
            "account_id": account_id,
            "amount": amount,
            "currency": currency,
        }
