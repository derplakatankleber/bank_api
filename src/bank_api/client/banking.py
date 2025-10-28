"""Client for banking related endpoints."""

from __future__ import annotations

from typing import Optional

from .base import BaseComdirectClient
from ..models import (
    ListResourceAccountBalance,
    ListResourceAccountTransaction,
)


class BankingClient(BaseComdirectClient):
    """Interact with the comdirect banking API."""

    def get_account_balances(
        self,
        user: str,
        *,
        without_attr: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> ListResourceAccountBalance:
        """Return account balances for the given user."""

        data = self._request_json(
            "GET",
            f"/banking/clients/{user}/v2/accounts/balances",
            params={"without-attr": without_attr},
            headers=headers,
        )
        return ListResourceAccountBalance.model_validate(data)

    def get_account_transactions(
        self,
        account_id: str,
        *,
        transaction_state: Optional[str] = None,
        transaction_direction: Optional[str] = None,
        paging_first: Optional[int] = None,
        with_attr: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> ListResourceAccountTransaction:
        """Return transactions for the given account."""

        params = {
            "transactionState": transaction_state,
            "transactionDirection": transaction_direction,
            "paging-first": paging_first,
            "with-attr": with_attr,
        }
        data = self._request_json(
            "GET",
            f"/banking/v1/accounts/{account_id}/transactions",
            params=params,
            headers=headers,
        )
        return ListResourceAccountTransaction.model_validate(data)
