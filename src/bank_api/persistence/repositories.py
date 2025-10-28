"""Repository classes wrapping SQLAlchemy sessions."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.banking import AccountBalance, AccountTransaction
from ..models.common import DateString
from .models import Order, Position, Setting, SyncLog, Transaction


class TransactionRepository:
    """Persist and retrieve account transactions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_transactions(
        self, transactions: Sequence[AccountTransaction], account_id: str
    ) -> None:
        for transaction in transactions:
            external_id = transaction.reference or transaction.endToEndReference
            existing = None
            if external_id:
                existing = self._session.scalar(
                    select(Transaction).where(Transaction.external_id == external_id)
                )
            amount_value = None
            amount = transaction.amount
            if amount and amount.value is not None:
                amount_value = float(amount.value)
            currency = amount.unit if amount and amount.unit else None
            if existing:
                existing.raw = transaction.model_dump()
                existing.amount = amount_value
                existing.currency = currency
                existing.booking_date = _parse_date(transaction.bookingDate)
            else:
                db_obj = Transaction(
                    external_id=external_id,
                    account_id=account_id,
                    booking_date=_parse_date(transaction.bookingDate),
                    amount=amount_value,
                    currency=currency,
                    raw=transaction.model_dump(),
                )
                self._session.add(db_obj)

    def list_transactions(self, account_id: str) -> list[Transaction]:
        stmt = select(Transaction).where(Transaction.account_id == account_id)
        return list(self._session.scalars(stmt))


class PositionRepository:
    """Persist account balances (positions)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_balances(self, balances: Sequence[AccountBalance]) -> None:
        for balance in balances:
            account_id = balance.accountId or balance.account.accountId if balance.account else None
            if not account_id:
                continue
            existing = self._session.scalar(
                select(Position).where(Position.account_id == account_id)
            )
            if existing:
                existing.balance_amount = _extract_amount(balance)
                existing.currency = _extract_currency(balance)
                existing.raw = balance.model_dump()
                existing.updated_at = datetime.utcnow()
            else:
                db_obj = Position(
                    account_id=account_id,
                    balance_amount=_extract_amount(balance),
                    currency=_extract_currency(balance),
                    raw=balance.model_dump(),
                )
                self._session.add(db_obj)

    def list_positions(self) -> list[Position]:
        return list(self._session.scalars(select(Position)))


class SyncLogRepository:
    """Persist logs for background jobs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, job_name: str, status: str, detail: str | None = None) -> SyncLog:
        entry = SyncLog(
            job_name=job_name, status=status, detail=detail, started_at=datetime.utcnow()
        )
        self._session.add(entry)
        return entry

    def update(self, log: SyncLog, status: str, detail: str | None = None) -> None:
        log.status = status
        log.detail = detail
        log.finished_at = datetime.utcnow()

    def get(self, log_id: int) -> SyncLog | None:
        return self._session.get(SyncLog, log_id)


class SettingsRepository:
    """Persist simple key/value configuration entries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, key: str) -> Setting | None:
        return self._session.scalar(select(Setting).where(Setting.key == key))

    def set(self, key: str, value: str | None) -> Setting:
        setting = self.get(key)
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            self._session.add(setting)
        return setting

    def list_all(self) -> list[Setting]:
        return list(self._session.scalars(select(Setting)))


class OrderRepository:
    """Manage lifecycle of locally stored orders."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_orders(self) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.desc())
        return list(self._session.scalars(stmt))

    def get(self, order_id: int) -> Order | None:
        return self._session.get(Order, order_id)

    def create(
        self,
        *,
        instrument: str,
        side: str,
        order_type: str,
        quantity: float,
        limit_price: float | None,
        notes: str | None = None,
    ) -> Order:
        order = Order(
            instrument=instrument,
            side=side,
            order_type=order_type,
            quantity=quantity,
            limit_price=limit_price,
            notes=notes,
        )
        self._session.add(order)
        self._session.flush()
        return order

    def update_status(self, order: Order, status: str) -> Order:
        order.status = status
        return order


def _parse_date(date_value: Any) -> datetime | None:
    if not date_value:
        return None
    if isinstance(date_value, DateString):
        return datetime.combine(date_value.date, datetime.min.time())
    try:
        return datetime.fromisoformat(str(date_value))
    except ValueError:
        return None


def _extract_amount(balance: AccountBalance) -> float | None:
    if balance.balance and balance.balance.value is not None:
        return float(balance.balance.value)
    if balance.availableCashAmount and balance.availableCashAmount.value is not None:
        return float(balance.availableCashAmount.value)
    return None


def _extract_currency(balance: AccountBalance) -> str | None:
    if balance.balance and balance.balance.unit:
        return balance.balance.unit
    if balance.availableCashAmount and balance.availableCashAmount.unit:
        return balance.availableCashAmount.unit
    return None
