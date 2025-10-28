"""Shared data models for the comdirect REST API."""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, is_dataclass
from decimal import Decimal
from typing import Any, Dict, Literal, Optional, TypeVar, cast


TModelDumpMixin = TypeVar("TModelDumpMixin", bound="ModelDumpMixin")


class ModelDumpMixin:
    """Compatibility helpers mirroring the previous Pydantic ``BaseModel`` API."""

    def model_dump(
        self: TModelDumpMixin,
        *,
        mode: Literal["python", "json"] = "python",
        include: Any | None = None,
        exclude: Any | None = None,
        exclude_none: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Return a dict representation of the dataclass and any nested dataclasses.

        The implementation mirrors the subset of the Pydantic API used by the project
        so that existing persistence code can continue to operate unchanged.
        """

        if not is_dataclass(self):  # pragma: no cover - defensive programming
            raise TypeError("model_dump can only be used with dataclass instances")

        if kwargs:
            unexpected = ", ".join(sorted(str(key) for key in kwargs))
            raise TypeError(f"Unsupported model_dump arguments: {unexpected}")

        if mode not in {"python", "json"}:
            raise ValueError("mode must be 'python' or 'json'")

        include_map = _normalize_include_exclude(include)
        exclude_map = _normalize_include_exclude(exclude)

        data = cast(Dict[str, Any], asdict(self))
        data = cast(
            Dict[str, Any],
            _apply_include_exclude(data, include_map, exclude_map),
        )

        if exclude_none:
            data = cast(Dict[str, Any], _exclude_none(data))

        return cast(Dict[str, Any], _convert_for_mode(data, mode))

    def model_dump_json(
        self: TModelDumpMixin,
        *,
        exclude_none: bool = False,
        indent: int | None = None,
        **json_kwargs: Any,
    ) -> str:
        """JSON serialise the dataclass using ``model_dump`` semantics."""

        if "mode" in json_kwargs:
            raise TypeError("mode is not a supported argument for model_dump_json")

        data = self.model_dump(mode="json", exclude_none=exclude_none)

        if indent is not None:
            json_kwargs.setdefault("indent", indent)

        return json.dumps(data, **json_kwargs)


def _normalize_include_exclude(spec: Any | None) -> Dict[str, Any] | None:
    if spec is None:
        return None
    if isinstance(spec, Mapping):
        normalized: Dict[str, Any] = {}
        for key, value in spec.items():
            normalized[str(key)] = _normalize_include_exclude(value)
        return normalized
    if isinstance(spec, (set, frozenset, list, tuple)):
        return {str(item): {"__self__": True} for item in spec}
    if isinstance(spec, bool):
        return {"__self__": spec}
    return {str(spec): True}


def _apply_include_exclude(
    data: Dict[str, Any],
    include: Dict[str, Any] | None,
    exclude: Dict[str, Any] | None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    include_self = False
    if include and "__self__" in include:
        include_self = bool(include["__self__"])
        include = {k: v for k, v in include.items() if k != "__self__"}
    exclude_self = False
    if exclude and "__self__" in exclude:
        exclude_self = bool(exclude["__self__"])
        exclude = {k: v for k, v in exclude.items() if k != "__self__"}

    if exclude_self:
        return {}

    if include is not None and not include and not include_self:
        return {}

    for key, value in data.items():
        include_spec = include.get(key) if include is not None else None
        exclude_spec = exclude.get(key) if exclude is not None else None

        if include is not None and include_spec is None and not include_self:
            continue

        include_value = True
        nested_include: Dict[str, Any] | None = None
        if isinstance(include_spec, dict):
            if "__self__" in include_spec:
                include_value = bool(include_spec["__self__"])
                include_spec = {
                    k: v for k, v in include_spec.items() if k != "__self__"
                }
            nested_include = include_spec or None

        if not include_value and nested_include is None:
            continue

        exclude_value = False
        nested_exclude: Dict[str, Any] | None = None
        if isinstance(exclude_spec, dict):
            if "__self__" in exclude_spec:
                exclude_value = bool(exclude_spec["__self__"])
                exclude_spec = {
                    k: v for k, v in exclude_spec.items() if k != "__self__"
                }
            nested_exclude = exclude_spec or None

        if exclude_value and nested_exclude is None:
            continue

        result[key] = _filter_nested(value, nested_include, nested_exclude)

    return result


def _filter_nested(
    value: Any, include: Dict[str, Any] | None, exclude: Dict[str, Any] | None
) -> Any:
    if isinstance(value, dict):
        return _apply_include_exclude(value, include, exclude)
    if isinstance(value, list):
        return [
            _filter_nested(item, include, exclude)
            if isinstance(item, dict)
            else item
            for item in value
        ]
    if isinstance(value, tuple):
        return tuple(
            _filter_nested(item, include, exclude)
            if isinstance(item, dict)
            else item
            for item in value
        )
    if isinstance(value, set):
        return {
            _filter_nested(item, include, exclude)
            if isinstance(item, dict)
            else item
            for item in value
        }
    return value


def _exclude_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _exclude_none(nested)
            for key, nested in value.items()
            if nested is not None
        }
    if isinstance(value, list):
        return [_exclude_none(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_exclude_none(item) for item in value)
    if isinstance(value, set):
        return {_exclude_none(item) for item in value}
    return value


def _convert_for_mode(value: Any, mode: str) -> Any:
    if isinstance(value, dict):
        return {key: _convert_for_mode(item, mode) for key, item in value.items()}
    if isinstance(value, list):
        return [_convert_for_mode(item, mode) for item in value]
    if isinstance(value, tuple):
        converted = [_convert_for_mode(item, mode) for item in value]
        return converted if mode == "json" else tuple(converted)
    if isinstance(value, set):
        converted = [_convert_for_mode(item, mode) for item in value]
        return converted if mode == "json" else set(converted)
    if isinstance(value, Decimal):
        return str(value) if mode == "json" else value
    if isinstance(value, dt.datetime):
        return value.isoformat() if mode == "json" else value
    if isinstance(value, dt.date):
        return value.isoformat() if mode == "json" else value
    return value


def _coerce_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(str(value))


def _coerce_optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


@dataclass
class AmountValue(ModelDumpMixin):
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
class CurrencyString(ModelDumpMixin):
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
class EnumText(ModelDumpMixin):
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
class DateString(ModelDumpMixin):
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
class PagingInfo(ModelDumpMixin):
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
class AggregatedInfo(ModelDumpMixin):
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
class AccountInformation(ModelDumpMixin):
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
