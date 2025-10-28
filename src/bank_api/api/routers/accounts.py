"""Account related API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, Query

from ...models.banking import AccountBalance
from ..auth import require_api_key
from ..dependencies import get_account_service
from ..schemas import BalanceSummary, BalanceSummaryResponse
from ...services.accounts import AccountService

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    dependencies=[Depends(require_api_key)],
)


def _derive_amount(balance: AccountBalance) -> tuple[Optional[float], Optional[str]]:
    if balance.balance and balance.balance.value is not None:
        return float(balance.balance.value), balance.balance.unit
    if balance.availableCashAmount and balance.availableCashAmount.value is not None:
        return float(balance.availableCashAmount.value), balance.availableCashAmount.unit
    return None, None


def _to_summary(balance: AccountBalance) -> BalanceSummary:
    amount, currency = _derive_amount(balance)
    account_id = balance.accountId
    if not account_id and balance.account:
        account_id = balance.account.accountId
    return BalanceSummary(account_id=account_id, amount=amount, currency=currency)


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


@router.get("/{user_id}/balances", response_model=BalanceSummaryResponse)
def list_balances(
    user_id: str,
    *,
    refresh: bool = Query(False, description="Fetch latest balances before returning data"),
    account_service: AccountService = Depends(get_account_service),
    forward_headers: dict[str, str] = Depends(_collect_forward_headers),
) -> BalanceSummaryResponse:
    """Return balances for the requested user."""

    refreshed = False
    if refresh:
        balances = account_service.refresh_account_balances(
            user_id,
            headers=forward_headers or None,
        ).values
        refreshed = True
    else:
        balances = account_service.list_cached_balances()
        if not balances:
            balances = account_service.refresh_account_balances(
                user_id,
                headers=forward_headers or None,
            ).values
            refreshed = True

    summaries = [_to_summary(balance) for balance in balances]
    return BalanceSummaryResponse(data=summaries, refreshed=refreshed)


@router.post("/{user_id}/balances/refresh", response_model=BalanceSummaryResponse)
def refresh_balances(
    user_id: str,
    *,
    account_service: AccountService = Depends(get_account_service),
    forward_headers: dict[str, str] = Depends(_collect_forward_headers),
) -> BalanceSummaryResponse:
    """Trigger a refresh and return the updated balances."""

    balances = account_service.refresh_account_balances(
        user_id,
        headers=forward_headers or None,
    ).values
    summaries = [_to_summary(balance) for balance in balances]
    return BalanceSummaryResponse(data=summaries, refreshed=True)
