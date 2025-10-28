"""Configuration service backed by the persistence layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..persistence.database import DatabaseSessionManager
from ..persistence.repositories import SettingsRepository


@dataclass(slots=True)
class AppConfiguration:
    """Representation of the user managed application configuration."""

    api_key: str | None = None
    user_id: str | None = None
    account_id: str | None = None


class ConfigurationService:
    """Provide read/write helpers for persisted configuration values."""

    def __init__(
        self,
        *,
        session_manager: DatabaseSessionManager | None = None,
    ) -> None:
        self._session_manager = session_manager or DatabaseSessionManager()

    def get_configuration(self) -> AppConfiguration:
        """Return the stored application configuration."""

        with self._session_manager.session_scope() as session:
            repository = SettingsRepository(session)
            entries = {setting.key: setting.value for setting in repository.list_all()}
        return AppConfiguration(
            api_key=entries.get("api_key"),
            user_id=entries.get("user_id"),
            account_id=entries.get("account_id"),
        )

    def update_configuration(self, **kwargs: str | None) -> AppConfiguration:
        """Persist the provided configuration keys."""

        allowed_keys: Iterable[str] = {"api_key", "user_id", "account_id"}
        filtered = {key: value for key, value in kwargs.items() if key in allowed_keys}
        with self._session_manager.session_scope() as session:
            repository = SettingsRepository(session)
            for key, value in filtered.items():
                repository.set(key, value)
        return self.get_configuration()
