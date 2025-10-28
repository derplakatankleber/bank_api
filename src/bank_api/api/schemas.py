"""Pydantic schemas exposed via the REST API."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class BalanceSummary(BaseModel):
    """Flattened view of an account balance."""

    account_id: Optional[str] = Field(default=None, description="Account identifier")
    amount: Optional[float] = Field(default=None, description="Current amount")
    currency: Optional[str] = Field(default=None, description="Currency code")


class BalanceSummaryResponse(BaseModel):
    """Envelope for balance responses."""

    data: list[BalanceSummary] = Field(default_factory=list)
    refreshed: bool = False


class TransactionAmount(BaseModel):
    """Normalized representation of a transaction amount."""

    value: Optional[float] = Field(default=None)
    currency: Optional[str] = Field(default=None)


class TransactionRecord(BaseModel):
    """Flattened transaction details."""

    reference: Optional[str] = Field(default=None)
    booking_date: Optional[date] = Field(default=None)
    valuta_date: Optional[date] = Field(default=None)
    remittance_info: Optional[str] = Field(default=None)
    transaction_type: Optional[str] = Field(default=None)
    amount: TransactionAmount = Field(default_factory=TransactionAmount)


class TransactionListResponse(BaseModel):
    """Envelope for transaction responses."""

    data: list[TransactionRecord] = Field(default_factory=list)
    refreshed: bool = False


class MessageResponse(BaseModel):
    """Generic message payload."""

    message: str
