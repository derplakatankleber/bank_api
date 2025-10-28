from __future__ import annotations

import json
from typing import Any, Dict, List

import pytest

from bank_api import BankingClient, RetryConfig
from bank_api.client.session import SessionClient
from bank_api.exceptions import ComdirectAPIError


class FakeResponse:
    def __init__(
        self, status_code: int, json_data: Any = None, headers: Dict[str, str] | None = None
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.headers = headers or {}

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    def json(self) -> Any:
        if self._json_data is None:
            raise ValueError("No JSON payload configured")
        return self._json_data

    @property
    def text(self) -> str:
        if self._json_data is None:
            return ""
        return json.dumps(self._json_data)


class StubSession:
    def __init__(self, responses: List[FakeResponse]) -> None:
        self._responses = responses
        self.calls: List[Dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return self._responses.pop(0)

    def close(self) -> None:
        pass


@pytest.mark.mocked
def test_get_account_balances_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "paging": {"index": 0, "matches": 1},
        "aggregated": {"total": "1"},
        "values": [
            {
                "accountId": "account-1",
                "balance": {"value": "100.50", "unit": "EUR"},
                "account": {
                    "accountId": "account-1",
                    "currency": {"currency": "EUR"},
                },
            }
        ],
    }
    session = StubSession([FakeResponse(200, payload)])
    client = BankingClient(session=session)

    result = client.get_account_balances("user", without_attr="account")

    assert result.paging and result.paging.index == 0
    assert result.aggregated and result.aggregated.data["total"] == "1"
    assert len(result.values) == 1
    assert result.values[0].balance and result.values[0].balance.value == 100.50

    call = session.calls[0]
    assert call["method"] == "GET"
    assert call["url"].endswith("/banking/clients/user/v2/accounts/balances")
    assert call["params"] == {"without-attr": "account"}


@pytest.mark.mocked
def test_retry_on_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        FakeResponse(429, {"message": "slow down"}, headers={"Retry-After": "1"}),
        FakeResponse(200, {"paging": {}, "values": []}),
    ]
    session = StubSession(responses)
    client = BankingClient(session=session)

    sleeps: List[float] = []
    monkeypatch.setattr("bank_api.client.base.time.sleep", lambda duration: sleeps.append(duration))

    result = client.get_account_balances("user")

    assert result.values == []
    assert len(session.calls) == 2
    assert sleeps == [1.0]


@pytest.mark.mocked
def test_raises_error_after_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        FakeResponse(500, {"error": "fail"}),
        FakeResponse(500, {"error": "fail"}),
        FakeResponse(500, {"error": "fail"}),
    ]
    session = StubSession(responses)
    client = BankingClient(
        session=session, retry_config=RetryConfig(max_attempts=3, backoff_factor=0.5)
    )

    sleeps: List[float] = []
    monkeypatch.setattr("bank_api.client.base.time.sleep", lambda duration: sleeps.append(duration))

    with pytest.raises(ComdirectAPIError) as exc:
        client.get_account_balances("user")

    assert exc.value.status_code == 500
    assert len(session.calls) == 3
    assert sleeps == [0.5, 1.0]


@pytest.mark.mocked
def test_session_client_deserializes_list() -> None:
    payload = [
        {"id": 1, "identifier": "abc", "sessionTanActive": True, "activated2FA": False},
        {"id": 2, "identifier": "def", "sessionTanActive": False, "activated2FA": True},
    ]
    session = StubSession([FakeResponse(200, payload)])
    client = SessionClient(session=session)

    result = client.get_sessions("user")

    assert [item.identifier for item in result] == ["abc", "def"]
