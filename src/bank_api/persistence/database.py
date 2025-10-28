"""Database helpers for persistence layer."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


@dataclass(slots=True)
class DatabaseConfig:
    """Configuration for database connections."""

    url: str = "sqlite:///./bank_data.db"
    echo: bool = False
    future: bool = True


class DatabaseSessionManager:
    """Factory for SQLAlchemy sessions with context manager support."""

    def __init__(self, config: Optional[DatabaseConfig] = None) -> None:
        self._config = config or DatabaseConfig()
        self._engine = create_engine(
            self._config.url,
            echo=self._config.echo,
            future=self._config.future,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=self._config.future,
        )
        Base.metadata.create_all(self._engine)

    @property
    def engine(self) -> Engine:
        return self._engine

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """Provide a transactional scope around a series of operations."""

        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def create_default_engine() -> Engine:
    """Create and return the default SQLAlchemy engine."""

    config = DatabaseConfig()
    manager = DatabaseSessionManager(config)
    return manager.engine
