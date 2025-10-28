"""Routes rendering the HTML management interface."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..dependencies import (
    get_account_service,
    get_configuration_service,
    get_order_service,
)
from ...models.banking import AccountBalance
from ...services import AccountService, ConfigurationService, OrderCreate, OrderService

router = APIRouter(include_in_schema=False)

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


def _ensure_authenticated(request: Request) -> bool:
    return bool(request.session.get("authenticated"))


def _balance_summary(balance: AccountBalance) -> dict[str, Any]:
    amount = None
    currency = None
    if balance.balance and balance.balance.value is not None:
        amount = float(balance.balance.value)
        currency = balance.balance.unit
    elif balance.availableCashAmount and balance.availableCashAmount.value is not None:
        amount = float(balance.availableCashAmount.value)
        currency = balance.availableCashAmount.unit

    account_id = balance.accountId
    if not account_id and balance.account:
        account_id = balance.account.accountId
    return {"account_id": account_id, "amount": amount, "currency": currency}


@router.get("/login", response_class=HTMLResponse)
def login(request: Request, config_service: ConfigurationService = Depends(get_configuration_service)):
    configuration = config_service.get_configuration()
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "configuration": configuration,
            "error": request.query_params.get("error"),
        },
    )


@router.post("/login")
def perform_login(
    request: Request,
    api_key: str = Form(...),
    user_id: str = Form(...),
    account_id: str = Form(...),
    config_service: ConfigurationService = Depends(get_configuration_service),
) -> RedirectResponse:
    config_service.update_configuration(api_key=api_key, user_id=user_id, account_id=account_id)
    request.session["authenticated"] = True
    request.session["user_id"] = user_id
    request.session["account_id"] = account_id
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    account_service: AccountService = Depends(get_account_service),
    order_service: OrderService = Depends(get_order_service),
    config_service: ConfigurationService = Depends(get_configuration_service),
):
    if not _ensure_authenticated(request):
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    configuration = config_service.get_configuration()
    balances = [_balance_summary(item) for item in account_service.list_cached_balances()]
    orders = order_service.list_orders()[:5]
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "configuration": configuration,
            "balances": balances,
            "orders": orders,
        },
    )


@router.get("/configuration", response_class=HTMLResponse)
def configuration(
    request: Request,
    config_service: ConfigurationService = Depends(get_configuration_service),
):
    if not _ensure_authenticated(request):
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    configuration = config_service.get_configuration()
    return templates.TemplateResponse(
        "configuration.html",
        {
            "request": request,
            "configuration": configuration,
            "saved": request.query_params.get("saved"),
        },
    )


@router.post("/configuration")
def update_configuration(
    request: Request,
    api_key: str = Form(None),
    user_id: str = Form(None),
    account_id: str = Form(None),
    config_service: ConfigurationService = Depends(get_configuration_service),
) -> RedirectResponse:
    if not _ensure_authenticated(request):
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    config_service.update_configuration(api_key=api_key, user_id=user_id, account_id=account_id)
    if user_id:
        request.session["user_id"] = user_id
    if account_id:
        request.session["account_id"] = account_id
    return RedirectResponse("/configuration?saved=true", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/orders", response_class=HTMLResponse)
def list_orders(
    request: Request,
    order_service: OrderService = Depends(get_order_service),
):
    if not _ensure_authenticated(request):
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    orders = order_service.list_orders()
    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "orders": orders,
        },
    )


@router.get("/orders/new", response_class=HTMLResponse)
def new_order(request: Request):
    if not _ensure_authenticated(request):
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse("order_form.html", {"request": request})


@router.post("/orders")
def create_order(
    request: Request,
    instrument: str = Form(...),
    side: str = Form(...),
    order_type: str = Form(...),
    quantity: float = Form(...),
    limit_price: float | None = Form(default=None),
    notes: str | None = Form(default=None),
    order_service: OrderService = Depends(get_order_service),
) -> RedirectResponse:
    if not _ensure_authenticated(request):
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    order_service.create_order(
        OrderCreate(
            instrument=instrument,
            side=side,
            order_type=order_type,
            quantity=quantity,
            limit_price=limit_price,
            notes=notes,
        )
    )
    return RedirectResponse("/orders", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/orders/{order_id}/status")
def change_order_status(
    order_id: int,
    request: Request,
    status_value: str = Form(..., alias="status"),
    order_service: OrderService = Depends(get_order_service),
) -> RedirectResponse:
    if not _ensure_authenticated(request):
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    order_service.update_order_status(order_id, status_value)
    return RedirectResponse("/orders", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/depot", response_class=HTMLResponse)
def depot(
    request: Request,
    account_service: AccountService = Depends(get_account_service),
):
    if not _ensure_authenticated(request):
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    balances = [_balance_summary(item) for item in account_service.list_cached_balances()]
    totals: dict[str, float] = {}
    for entry in balances:
        amount = entry.get("amount")
        currency = entry.get("currency")
        if amount is None or not currency:
            continue
        totals[currency] = totals.get(currency, 0.0) + float(amount)
    return templates.TemplateResponse(
        "depot.html",
        {
            "request": request,
            "balances": balances,
            "totals": totals,
        },
    )
