"""Session models."""

from __future__ import annotations

from typing import Optional

from dataclasses import dataclass

from .common import ModelDumpMixin, _coerce_optional_str


@dataclass
class Session(ModelDumpMixin):
    """Model for the current session."""

    id: Optional[int] = None
    identifier: Optional[str] = None
    sessionTanActive: Optional[bool] = None
    activated2FA: Optional[bool] = None

    @classmethod
    def model_validate(cls, value: object) -> "Session":
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                id=value.get("id"),
                identifier=_coerce_optional_str(value.get("identifier")),
                sessionTanActive=value.get("sessionTanActive"),
                activated2FA=value.get("activated2FA"),
            )
        raise TypeError(f"Cannot convert {value!r} to Session")
