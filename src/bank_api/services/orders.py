"""Services for managing locally persisted orders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..persistence.database import DatabaseSessionManager
from ..persistence.repositories import OrderRepository


@dataclass(slots=True)
class OrderCreate:
    """Data required to create a new order."""

    instrument: str
    side: str
    order_type: str
    quantity: float
    limit_price: float | None = None
    notes: str | None = None


@dataclass(slots=True)
class OrderRecord:
    """Representation of an order for presentation layers."""

    id: int
    instrument: str
    side: str
    order_type: str
    quantity: float
    limit_price: float | None
    status: str
    notes: str | None
    created_at: str


class OrderService:
    """High level operations around order persistence."""

    def __init__(
        self,
        *,
        session_manager: DatabaseSessionManager | None = None,
    ) -> None:
        self._session_manager = session_manager or DatabaseSessionManager()

    def list_orders(self) -> list[OrderRecord]:
        """Return persisted orders sorted by creation date."""

        with self._session_manager.session_scope() as session:
            repository = OrderRepository(session)
            orders = repository.list_orders()
            return [
                OrderRecord(
                    id=order.id,
                    instrument=order.instrument,
                    side=order.side,
                    order_type=order.order_type,
                    quantity=order.quantity,
                    limit_price=float(order.limit_price) if order.limit_price is not None else None,
                    status=order.status,
                    notes=order.notes,
                    created_at=order.created_at.isoformat(timespec="seconds"),
                )
                for order in orders
            ]

    def create_order(self, order_data: OrderCreate) -> OrderRecord:
        """Persist a new order and return its representation."""

        with self._session_manager.session_scope() as session:
            repository = OrderRepository(session)
            order = repository.create(
                instrument=order_data.instrument,
                side=order_data.side,
                order_type=order_data.order_type,
                quantity=order_data.quantity,
                limit_price=order_data.limit_price,
                notes=order_data.notes,
            )
            return OrderRecord(
                id=order.id,
                instrument=order.instrument,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                limit_price=float(order.limit_price) if order.limit_price is not None else None,
                status=order.status,
                notes=order.notes,
                created_at=order.created_at.isoformat(timespec="seconds"),
            )

    def update_order_status(self, order_id: int, status: str) -> OrderRecord | None:
        """Update the status of an existing order."""

        normalized = status.lower()
        allowed_statuses: Iterable[str] = {"pending", "placed", "executed", "cancelled"}
        if normalized not in allowed_statuses:
            raise ValueError(f"Unsupported order status '{status}'")

        with self._session_manager.session_scope() as session:
            repository = OrderRepository(session)
            order = repository.get(order_id)
            if not order:
                return None
            repository.update_status(order, normalized)
            return OrderRecord(
                id=order.id,
                instrument=order.instrument,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                limit_price=float(order.limit_price) if order.limit_price is not None else None,
                status=order.status,
                notes=order.notes,
                created_at=order.created_at.isoformat(timespec="seconds"),
            )
