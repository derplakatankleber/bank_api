"""Tests for shared model utilities."""

from __future__ import annotations

import datetime as dt
import json
from decimal import Decimal

import pytest

from bank_api.models.banking import AccountTransaction, AmountValue
from bank_api.models.common import DateString


def _example_transaction() -> AccountTransaction:
    return AccountTransaction(
        bookingDate=DateString.model_validate({"date": "2024-03-01"}),
        amount=AmountValue.model_validate({"value": "123.45", "unit": "EUR"}),
        reference=None,
    )


def test_model_dump_python_mode_preserves_types() -> None:
    transaction = _example_transaction()

    data = transaction.model_dump()

    assert data["amount"]["value"] == Decimal("123.45")
    assert data["bookingDate"]["date"] == dt.date(2024, 3, 1)


def test_model_dump_json_mode_serialises_values() -> None:
    transaction = _example_transaction()

    data = transaction.model_dump(mode="json", exclude_none=True)

    assert data["amount"]["value"] == "123.45"
    assert data["bookingDate"]["date"] == "2024-03-01"
    assert "reference" not in data


def test_model_dump_include_and_exclude_filter_fields() -> None:
    transaction = _example_transaction()

    included = transaction.model_dump(include={"amount"})
    assert set(included.keys()) == {"amount"}

    excluded = transaction.model_dump(exclude={"amount"})
    assert "amount" not in excluded


def test_model_dump_json_helper_returns_string() -> None:
    transaction = _example_transaction()

    json_payload = transaction.model_dump_json(exclude_none=True, indent=2)
    parsed = json.loads(json_payload)

    assert parsed["amount"]["value"] == "123.45"
    assert parsed["bookingDate"]["date"] == "2024-03-01"


def test_model_dump_rejects_unknown_arguments() -> None:
    transaction = _example_transaction()

    with pytest.raises(TypeError):
        transaction.model_dump(unknown_option=True)  # type: ignore[arg-type]


def test_model_dump_rejects_invalid_mode() -> None:
    transaction = _example_transaction()

    with pytest.raises(ValueError):
        transaction.model_dump(mode="unsupported")  # type: ignore[arg-type]
