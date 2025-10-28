"""Custom exceptions for the comdirect API client."""

from __future__ import annotations

from typing import Any, Optional


class ComdirectAPIError(RuntimeError):
    """Raised when the comdirect API responds with an error status."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return (
            f"{self.__class__.__name__}(status_code={self.status_code!r}, "
            f"message={self.args[0]!r})"
        )
