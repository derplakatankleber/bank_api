"""Shared pytest configuration for the project."""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run tests marked as live that hit the comdirect sandbox API.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "mocked: tests that rely on mocked HTTP responses")
    config.addinivalue_line("markers", "live: tests that call the comdirect sandbox API")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-live"):
        return

    skip_live = pytest.mark.skip(reason="need --run-live option to run live sandbox tests")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
