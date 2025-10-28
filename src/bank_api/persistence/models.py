"""SQLAlchemy models for persisted data."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    """Persisted representation of a bank transaction."""

    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("external_id", name="uq_transactions_external_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    account_id: Mapped[str | None] = mapped_column(String(255), index=True)
    booking_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    amount: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(16))
    raw: Mapped[Any | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Position(Base):
    """Persisted representation of an account balance/position."""

    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("account_id", name="uq_positions_account_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str | None] = mapped_column(String(255), index=True)
    balance_amount: Mapped[float | None] = mapped_column(Numeric(16, 4))
    currency: Mapped[str | None] = mapped_column(String(16))
    raw: Mapped[Any | None] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)


class SyncLog(Base):
    """Log entries for background jobs and data refreshes."""

    __tablename__ = "sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_name: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32))
    detail: Mapped[str | None] = mapped_column(String(1024))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
