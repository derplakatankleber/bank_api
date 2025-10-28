"""Client for session endpoints."""

from __future__ import annotations

from typing import List, Optional

from .base import BaseComdirectClient
from ..models import Session


class SessionClient(BaseComdirectClient):
    """Interact with the session endpoints of the comdirect API."""

    def get_sessions(
        self,
        user: str,
        *,
        headers: Optional[dict[str, str]] = None,
    ) -> List[Session]:
        """Return the current sessions for the given user."""

        data = self._request_json(
            "GET",
            f"/session/clients/{user}/v1/sessions",
            headers=headers,
        )
        return [Session.model_validate(item) for item in data]
