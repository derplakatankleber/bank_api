"""Command line interface for interacting with the REST API."""
from __future__ import annotations

import contextlib
import csv
import json
import os
from pathlib import Path
from typing import Any, Iterable

import requests
import typer
from rich import box
from rich.bar import Bar
from rich.console import Console
from rich.table import Table

APP_NAME = "bank_api"
CONFIG_PATH = Path(typer.get_app_dir(APP_NAME)) / "config.json"
DEFAULT_API_URL = "http://localhost:8000"

console = Console()
app = typer.Typer(help="Utility commands for the bank-api service.")


class CLIError(Exception):
    """Error raised for CLI specific issues."""


def _ensure_secure_permissions(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except PermissionError:
        console.print(
            "[yellow]Warning:[/] Unable to restrict permissions on configuration file.",
            style="yellow",
        )


def save_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = CONFIG_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(config, indent=2))
    _ensure_secure_permissions(temp_path)
    os.replace(temp_path, CONFIG_PATH)
    _ensure_secure_permissions(CONFIG_PATH)


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text())


def resolve_api_url(explicit: str | None = None) -> str:
    if explicit:
        return explicit.rstrip("/")
    env_url = os.getenv("BANK_API_URL")
    if env_url:
        return env_url.rstrip("/")
    config = load_config()
    url = config.get("api_url", DEFAULT_API_URL)
    return str(url).rstrip("/")


def resolve_api_key(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    env_key = os.getenv("BANK_API_CLI_KEY") or os.getenv("BANK_API_KEY")
    if env_key:
        return env_key
    config = load_config()
    key = config.get("api_key")
    if not key:
        raise CLIError(
            "No API key configured. Run `bank-api login` or set BANK_API_CLI_KEY.",
        )
    return key


def _headers(api_key: str) -> dict[str, str]:
    return {"X-API-Key": api_key}


def _request(
    method: str,
    endpoint: str,
    *,
    api_key: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = requests.request(
        method,
        endpoint,
        headers=_headers(api_key),
        params=params,
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - defensive programming
        detail = response.text
        with contextlib.suppress(ValueError):
            detail = response.json()
        raise CLIError(f"Request failed: {detail}") from exc
    except requests.RequestException as exc:  # pragma: no cover - defensive programming
        raise CLIError(f"Request failed: {exc}") from exc
    return response.json()


def _render_balances_table(data: Iterable[dict[str, Any]]) -> None:
    table = Table(title="Account Balances", box=box.SIMPLE_HEAD)
    table.add_column("Account ID", style="cyan")
    table.add_column("Amount", justify="right")
    table.add_column("Currency", justify="center")
    for item in data:
        amount = item.get("amount")
        amount_text = f"{amount:,.2f}" if amount is not None else "—"
        table.add_row(str(item.get("account_id") or "—"), amount_text, item.get("currency") or "—")
    console.print(table)


def _render_balances_chart(data: Iterable[dict[str, Any]]) -> None:
    amounts = [abs(item.get("amount") or 0) for item in data]
    if not any(amounts):
        console.print("No numerical data available for chart rendering.")
        return
    max_amount = max(amounts)
    console.print("\n[bold]Balance distribution[/bold]")
    for item in data:
        value = item.get("amount") or 0
        bar = Bar(size=30, begin=-max_amount, end=max_amount, value=value)
        console.print(f"{str(item.get('account_id') or '—'):>15} {bar} {value:,.2f}")


def _render_transactions_table(data: Iterable[dict[str, Any]]) -> None:
    table = Table(title="Transactions", box=box.SIMPLE_HEAD)
    table.add_column("Booking Date", style="cyan")
    table.add_column("Reference", overflow="fold")
    table.add_column("Amount", justify="right")
    table.add_column("Currency", justify="center")
    for item in data:
        amount = item.get("amount", {}).get("value")
        currency = item.get("amount", {}).get("currency")
        amount_text = f"{amount:,.2f}" if amount is not None else "—"
        table.add_row(
            str(item.get("booking_date") or "—"),
            item.get("reference") or item.get("remittance_info") or "—",
            amount_text,
            currency or "—",
        )
    console.print(table)


def _render_transactions_chart(data: Iterable[dict[str, Any]]) -> None:
    console.print("\n[bold]Transaction amounts[/bold]")
    amounts = [abs(item.get("amount", {}).get("value") or 0) for item in data]
    if not any(amounts):
        console.print("No numerical data available for chart rendering.")
        return
    max_amount = max(amounts)
    for item in data:
        value = item.get("amount", {}).get("value") or 0
        label = str(item.get("booking_date") or item.get("reference") or "—")
        bar = Bar(size=30, begin=-max_amount, end=max_amount, value=value)
        console.print(f"{label:>15} {bar} {value:,.2f}")


def _export_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows_list = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as csvfile:
        fieldnames = list(rows_list[0].keys()) if rows_list else []
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_list:
            writer.writerow(row)
    console.print(f"Exported data to [green]{path}[/green]")


@app.command()
def login(
    api_url: str = typer.Option(DEFAULT_API_URL, prompt=True, help="Base URL of the REST API"),
    store: bool = typer.Option(True, help="Persist credentials to disk"),
) -> None:
    """Store the API URL and key for future commands."""

    api_key = typer.prompt("API key", hide_input=True, confirmation_prompt=True)
    config = {"api_url": api_url.rstrip("/"), "api_key": api_key}
    if store:
        save_config(config)
        console.print("Credentials saved securely.")
    else:
        console.print("Credentials not persisted; they will be used for this session only.")


@app.command("balances")
def fetch_balances(
    user_id: str = typer.Argument(..., help="Comdirect user identifier"),
    refresh: bool = typer.Option(False, help="Refresh balances before returning data"),
    show_chart: bool = typer.Option(False, help="Display a bar chart of balances"),
    output_csv: Path | None = typer.Option(None, help="Optional path to export balances as CSV"),
    api_url: str | None = typer.Option(None, help="Override the configured API URL"),
    api_key: str | None = typer.Option(None, help="Override the configured API key"),
) -> None:
    """Fetch account balances and present them in multiple formats."""

    try:
        resolved_url = resolve_api_url(api_url)
        resolved_key = resolve_api_key(api_key)
        payload = _request(
            "GET",
            f"{resolved_url}/accounts/{user_id}/balances",
            api_key=resolved_key,
            params={"refresh": refresh},
        )
    except CLIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    data = payload.get("data", [])
    _render_balances_table(data)

    if show_chart:
        _render_balances_chart(data)

    if output_csv:
        _export_csv(output_csv, data)


@app.command("export-transactions")
def export_transactions(
    account_id: str = typer.Argument(..., help="Account identifier"),
    refresh: bool = typer.Option(False, help="Refresh transactions before returning data"),
    show_chart: bool = typer.Option(False, help="Display a chart of transaction amounts"),
    output_csv: Path = typer.Option(Path("transactions.csv"), help="File to write CSV output"),
    api_url: str | None = typer.Option(None, help="Override the configured API URL"),
    api_key: str | None = typer.Option(None, help="Override the configured API key"),
) -> None:
    """Export transactions to CSV and optionally visualise them."""

    try:
        resolved_url = resolve_api_url(api_url)
        resolved_key = resolve_api_key(api_key)
        payload = _request(
            "GET",
            f"{resolved_url}/accounts/{account_id}/transactions",
            api_key=resolved_key,
            params={"refresh": refresh},
        )
    except CLIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    data = payload.get("data", [])
    flattened = [
        {
            "booking_date": item.get("booking_date"),
            "reference": item.get("reference"),
            "remittance_info": item.get("remittance_info"),
            "transaction_type": item.get("transaction_type"),
            "amount": item.get("amount", {}).get("value"),
            "currency": item.get("amount", {}).get("currency"),
        }
        for item in data
    ]
    _render_transactions_table(data)
    _export_csv(output_csv, flattened)

    if show_chart:
        _render_transactions_chart(data)


def run_cli() -> None:
    """Entry point for console_scripts."""

    app()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    run_cli()
