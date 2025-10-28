"""Shared data models for the comdirect REST API."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, Optional


def _coerce_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(str(value))


def _coerce_optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


@dataclass
class AmountValue:
    """Represents an amount with a currency unit."""

    value: Optional[Decimal] = None
    unit: Optional[str] = None

    @classmethod
    def model_validate(cls, value: Any) -> Optional["AmountValue"]:
        if value is None or isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                value=_coerce_decimal(value.get("value")),
                unit=_coerce_optional_str(value.get("unit")),
            )
        raise TypeError(f"Cannot convert {value!r} to AmountValue")


@dataclass
class CurrencyString:
    """ISO-4217 currency code wrapper."""

    currency: Optional[str] = None

    @classmethod
    def model_validate(cls, value: Any) -> Optional["CurrencyString"]:
        if value is None or isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(currency=_coerce_optional_str(value.get("currency")))
        return cls(currency=_coerce_optional_str(value))


@dataclass
class EnumText:
    """Holds a key/text pair as returned by the API."""

    key: Optional[str] = None
    text: Optional[str] = None

    @classmethod
    def model_validate(cls, value: Any) -> Optional["EnumText"]:
        if value is None or isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                key=_coerce_optional_str(value.get("key")),
                text=_coerce_optional_str(value.get("text")),
            )
        raise TypeError(f"Cannot convert {value!r} to EnumText")


@dataclass
class DateString:
    """Date without time information."""

    date: Optional[dt.date] = None

    @classmethod
    def model_validate(cls, value: Any) -> Optional["DateString"]:
        if value is None or isinstance(value, cls):
            return value
        if isinstance(value, dict):
            raw_value = value.get("date")
        else:
            raw_value = value

        if isinstance(raw_value, dt.date):
            parsed = raw_value
        else:
            parsed = dt.date.fromisoformat(str(raw_value))

        return cls(date=parsed)


@dataclass
class PagingInfo:
    """Paging metadata for list resources."""

    index: Optional[int] = None
    matches: Optional[int] = None

    @classmethod
    def model_validate(cls, value: Any) -> Optional["PagingInfo"]:
        if value is None or isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                index=value.get("index"),
                matches=value.get("matches"),
            )
        raise TypeError(f"Cannot convert {value!r} to PagingInfo")


@dataclass
class AggregatedInfo:
    """Placeholder for aggregated metadata not yet modelled in the API spec."""

    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def model_validate(cls, value: Any) -> Optional["AggregatedInfo"]:
        if value is None or isinstance(value, cls):
            return value or cls()
        if isinstance(value, dict):
            if "data" in value and isinstance(value["data"], dict):
                return cls(data=dict(value["data"]))
            return cls(data=dict(value))
        raise TypeError(f"Cannot convert {value!r} to AggregatedInfo")


@dataclass
class AccountInformation:
    """Information about an account owner."""

    holderName: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None

    @classmethod
    def model_validate(cls, value: Any) -> Optional["AccountInformation"]:
        if value is None or isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                holderName=_coerce_optional_str(value.get("holderName")),
                iban=_coerce_optional_str(value.get("iban")),
                bic=_coerce_optional_str(value.get("bic")),
            )
        raise TypeError(f"Cannot convert {value!r} to AccountInformation")
