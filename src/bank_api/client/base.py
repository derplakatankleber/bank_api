"""Base client with retry/backoff handling."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Iterable, Mapping, Optional
from urllib.parse import urljoin

from ..exceptions import ComdirectAPIError

if TYPE_CHECKING:  # pragma: no cover - imported only for static analysis
    from requests import Response, Session  # type: ignore[import-untyped]
else:
    Response = Any  # type: ignore[assignment]
    Session = Any  # type: ignore[assignment]

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for retrying failed HTTP requests."""

    max_attempts: int = 3
    backoff_factor: float = 0.5
    status_forcelist: Iterable[int] = field(default_factory=lambda: (429, 500, 502, 503, 504))


class BaseComdirectClient:
    """Common functionality for concrete API clients."""

    def __init__(
        self,
        *,
        base_url: str = "https://api.comdirect.de/api/",
        session: Optional[Session] = None,
        retry_config: Optional[RetryConfig] = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/") + "/"
        if session is None:
            from requests import Session as RequestsSession

            session = RequestsSession()

        self._session = session
        self._retry_config = retry_config or RetryConfig()
        self._timeout = timeout

    def close(self) -> None:
        self._session.close()

    def _prepare_params(self, params: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        if not params:
            return {}
        return {key: value for key, value in params.items() if value is not None}

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        json: Any = None,
    ) -> Response:
        url = urljoin(self._base_url, path.lstrip("/"))
        attempt = 0
        last_response: Optional[Response] = None

        prepared_params = self._prepare_params(params)

        while attempt < self._retry_config.max_attempts:
            attempt += 1
            response = self._session.request(
                method,
                url,
                params=prepared_params,
                headers=headers,
                json=json,
                timeout=self._timeout,
            )
            last_response = response

            if not self._should_retry(response) or attempt == self._retry_config.max_attempts:
                break

            delay = self._calculate_delay(response, attempt)
            LOGGER.debug(
                "Retrying %s %s in %ss (attempt %s/%s)",
                method,
                url,
                delay,
                attempt,
                self._retry_config.max_attempts,
            )
            time.sleep(delay)

        assert last_response is not None  # for type checkers
        if not last_response.ok:
            raise self._build_error(last_response)
        return last_response

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        json: Any = None,
    ) -> Any:
        response = self._request(method, path, params=params, headers=headers, json=json)
        return response.json()

    def _should_retry(self, response: Response) -> bool:
        return response.status_code in set(self._retry_config.status_forcelist)

    def _calculate_delay(self, response: Response, attempt: int) -> float:
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after is not None:
                try:
                    return float(retry_after)
                except ValueError:
                    pass
        return self._retry_config.backoff_factor * (2 ** (attempt - 1))

    def _build_error(self, response: Response) -> ComdirectAPIError:
        message = f"HTTP {response.status_code} error calling comdirect API"
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        return ComdirectAPIError(
            message,
            status_code=response.status_code,
            response=payload,
        )

    def __enter__(self) -> "BaseComdirectClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
