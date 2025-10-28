"""Session models."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Session(BaseModel):
    """Model for the current session."""

    id: Optional[int] = None
    identifier: Optional[str] = None
    sessionTanActive: Optional[bool] = None
    activated2FA: Optional[bool] = None
