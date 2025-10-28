"""Utilities for scheduling background data refresh jobs."""
from __future__ import annotations

from typing import Any, Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..persistence.database import DatabaseSessionManager
from ..persistence.repositories import SyncLogRepository
from ..services import AccountService, TransactionService


class DataRefreshScheduler:
    """Configure and run background jobs to keep data fresh."""

    def __init__(
        self,
        *,
        session_manager: DatabaseSessionManager | None = None,
        timezone: str = "UTC",
    ) -> None:
        self._session_manager = session_manager or DatabaseSessionManager()
        self._scheduler = BackgroundScheduler(timezone=timezone)

    def start(self) -> None:
        """Start the background scheduler."""

        if not self._scheduler.running:
            self._scheduler.start()

    def shutdown(self, *, wait: bool = False) -> None:
        """Stop the background scheduler."""

        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)

    def schedule_account_balance_refresh(
        self,
        *,
        service: AccountService,
        user_id: str,
        interval_minutes: int,
        headers: Optional[dict[str, str]] = None,
        without_attr: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> str:
        """Schedule periodic balance refreshes via the account service."""

        job_name = job_id or f"account-balance-refresh-{user_id}"
        trigger = IntervalTrigger(minutes=interval_minutes)

        def _job() -> None:
            self._run_with_logging(
                job_name,
                service.refresh_account_balances,
                user_id,
                headers=headers,
                without_attr=without_attr,
            )

        self._scheduler.add_job(_job, trigger=trigger, id=job_name, replace_existing=True)
        return job_name

    def schedule_transaction_refresh(
        self,
        *,
        service: TransactionService,
        account_id: str,
        interval_minutes: int,
        headers: Optional[dict[str, str]] = None,
        transaction_state: Optional[str] = None,
        transaction_direction: Optional[str] = None,
        paging_first: Optional[int] = None,
        with_attr: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> str:
        """Schedule periodic transaction refreshes via the transaction service."""

        job_name = job_id or f"transaction-refresh-{account_id}"
        trigger = IntervalTrigger(minutes=interval_minutes)

        def _job() -> None:
            self._run_with_logging(
                job_name,
                service.refresh_transactions,
                account_id,
                headers=headers,
                transaction_state=transaction_state,
                transaction_direction=transaction_direction,
                paging_first=paging_first,
                with_attr=with_attr,
            )

        self._scheduler.add_job(_job, trigger=trigger, id=job_name, replace_existing=True)
        return job_name

    def _run_with_logging(self, job_name: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        with self._session_manager.session_scope() as session:
            repo = SyncLogRepository(session)
            log = repo.create(job_name, "running")
            session.flush()
            log_id = log.id

        try:
            func(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - defensive logging
            with self._session_manager.session_scope() as session:
                repo = SyncLogRepository(session)
                stored = repo.get(log_id)
                if stored is not None:
                    repo.update(stored, "failed", detail=str(exc))
            raise
        else:
            with self._session_manager.session_scope() as session:
                repo = SyncLogRepository(session)
                stored = repo.get(log_id)
                if stored is not None:
                    repo.update(stored, "succeeded")
