"""Transaction related API routes."""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from fastapi import APIRouter, Depends, Header, Query

from ...models.banking import AccountTransaction
from ..auth import require_api_key
from ..dependencies import get_transaction_service
from ..schemas import TransactionAmount, TransactionListResponse, TransactionRecord
from ...services.transactions import TransactionService

router = APIRouter(
    prefix="/accounts",
    tags=["transactions"],
    dependencies=[Depends(require_api_key)],
)


def _collect_forward_headers(
    authorization: str | None = Header(default=None, convert_underscores=False),
    x_http_request_info: str | None = Header(default=None, alias="x-http-request-info"),
    x_http_session_info: str | None = Header(default=None, alias="x-http-session-info"),
) -> dict[str, str]:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    if x_http_request_info:
        headers["x-http-request-info"] = x_http_request_info
    if x_http_session_info:
        headers["x-http-session-info"] = x_http_session_info
    return headers


def _coerce_transaction(raw: AccountTransaction | dict[str, Any]) -> AccountTransaction:
    if isinstance(raw, AccountTransaction):
        return raw
    return AccountTransaction.model_validate(raw)


def _to_amount(transaction: AccountTransaction) -> TransactionAmount:
    if transaction.amount and transaction.amount.value is not None:
        return TransactionAmount(
            value=float(transaction.amount.value),
            currency=transaction.amount.unit,
        )
    return TransactionAmount()


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if hasattr(value, "date"):
        return value.date  # DateString compatibility
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _to_record(transaction: AccountTransaction) -> TransactionRecord:
    amount = _to_amount(transaction)
    booking_date = _parse_date(transaction.bookingDate)
    valuta_date = _parse_date(transaction.valutaDate)
    return TransactionRecord(
        reference=transaction.reference,
        booking_date=booking_date,
        valuta_date=valuta_date,
        remittance_info=transaction.remittanceInfo,
        transaction_type=(transaction.transactionType.text if transaction.transactionType else None),
        amount=amount,
    )


def _map_transactions(transactions: Iterable[AccountTransaction | dict[str, Any]]) -> list[TransactionRecord]:
    return [_to_record(_coerce_transaction(item)) for item in transactions]


@router.get("/{account_id}/transactions", response_model=TransactionListResponse)
def list_transactions(
    account_id: str,
    *,
    refresh: bool = Query(False, description="Fetch latest transactions before returning data"),
    transaction_state: str | None = Query(default=None),
    transaction_direction: str | None = Query(default=None),
    paging_first: int | None = Query(default=None, ge=1),
    with_attr: str | None = Query(default=None),
    transaction_service: TransactionService = Depends(get_transaction_service),
    forward_headers: dict[str, str] = Depends(_collect_forward_headers),
) -> TransactionListResponse:
    """Return transactions for the requested account."""

    refreshed = False
    if refresh:
        transactions = transaction_service.refresh_transactions(
            account_id,
            headers=forward_headers or None,
            transaction_state=transaction_state,
            transaction_direction=transaction_direction,
            paging_first=paging_first,
            with_attr=with_attr,
        ).values
        refreshed = True
    else:
        transactions = transaction_service.list_cached_transactions(account_id)
        if not transactions:
            transactions = transaction_service.refresh_transactions(
                account_id,
                headers=forward_headers or None,
                transaction_state=transaction_state,
                transaction_direction=transaction_direction,
                paging_first=paging_first,
                with_attr=with_attr,
            ).values
            refreshed = True

    records = _map_transactions(transactions)
    return TransactionListResponse(data=records, refreshed=refreshed)


@router.post("/{account_id}/transactions/refresh", response_model=TransactionListResponse)
def refresh_transactions(
    account_id: str,
    *,
    transaction_state: str | None = Query(default=None),
    transaction_direction: str | None = Query(default=None),
    paging_first: int | None = Query(default=None, ge=1),
    with_attr: str | None = Query(default=None),
    transaction_service: TransactionService = Depends(get_transaction_service),
    forward_headers: dict[str, str] = Depends(_collect_forward_headers),
) -> TransactionListResponse:
    """Trigger a refresh and return the updated transactions."""

    transactions = transaction_service.refresh_transactions(
        account_id,
        headers=forward_headers or None,
        transaction_state=transaction_state,
        transaction_direction=transaction_direction,
        paging_first=paging_first,
        with_attr=with_attr,
    ).values
    records = _map_transactions(transactions)
    return TransactionListResponse(data=records, refreshed=True)
