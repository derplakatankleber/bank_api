"""Live tests that can hit the comdirect sandbox environment."""

from __future__ import annotations

import os

import pytest

from bank_api import BankingClient

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def sandbox_settings() -> dict[str, str]:
    """Collect sandbox configuration from the environment or skip the suite."""

    base_url = os.getenv("COMDIRECT_SANDBOX_BASE_URL", "https://sandbox-api.comdirect.de/api/")
    required_vars = ["COMDIRECT_SANDBOX_USER", "COMDIRECT_SANDBOX_TOKEN"]
    missing = [name for name in required_vars if not os.getenv(name)]
    if missing:
        pytest.skip(
            "Environment variables %s must be defined to run sandbox smoke tests." % missing
        )

    settings = {name: os.environ[name] for name in required_vars}
    settings["COMDIRECT_SANDBOX_BASE_URL"] = base_url
    return settings


@pytest.fixture(scope="module")
def sandbox_client(sandbox_settings: dict[str, str]) -> BankingClient:
    client = BankingClient(base_url=sandbox_settings["COMDIRECT_SANDBOX_BASE_URL"])
    try:
        yield client
    finally:
        client.close()


def test_fetch_account_balances_smoke(
    sandbox_client: BankingClient, sandbox_settings: dict[str, str]
) -> None:
    """Ensure the sandbox responds with structured data for the configured user."""

    token = sandbox_settings["COMDIRECT_SANDBOX_TOKEN"]
    user = sandbox_settings["COMDIRECT_SANDBOX_USER"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    balances = sandbox_client.get_account_balances(user, headers=headers)

    assert balances.values is not None
    assert balances.paging is None or balances.paging.index >= 0
