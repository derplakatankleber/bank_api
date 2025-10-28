"""Shared data models for the comdirect REST API."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class AmountValue(BaseModel):
    """Represents an amount with a currency unit."""

    value: Decimal = Field(..., description="Nominal value in the corresponding unit")
    unit: str = Field(..., min_length=3, max_length=3, description="Currency or amount unit")

    @field_validator("value", mode="before")
    def _coerce_decimal(cls, value: Any) -> Decimal | None:
        if value is None:
            return None
        return Decimal(str(value))


class CurrencyString(BaseModel):
    """ISO-4217 currency code wrapper."""

    currency: str = Field(..., min_length=3, max_length=3)


class EnumText(BaseModel):
    """Holds a key/text pair as returned by the API."""

    key: Optional[str] = Field(None, max_length=40)
    text: Optional[str] = Field(None, max_length=65)


class DateString(BaseModel):
    """Date without time information."""

    date: dt.date

    @field_validator("date", mode="before")
    def _parse_date(cls, value: Any) -> dt.date:
        if isinstance(value, dt.date):
            return value
        return dt.date.fromisoformat(str(value))


class PagingInfo(BaseModel):
    """Paging metadata for list resources."""

    index: Optional[int] = None
    matches: Optional[int] = None


class AggregatedInfo(BaseModel):
    """Placeholder for aggregated metadata not yet modelled in the API spec."""

    data: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    def _ensure_dict(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {"data": {}}
        if isinstance(value, dict) and "data" not in value:
            return {"data": value}
        return value


class AccountInformation(BaseModel):
    """Information about an account owner."""

    holderName: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
