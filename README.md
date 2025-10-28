# bank_api

A Python toolkit and service layer that wraps the comdirect REST API. The project ships with:

- A reusable `bank_api` package that models comdirect banking resources and handles authenticated HTTP calls.
- A FastAPI application with an HTML dashboard for configuring credentials, reviewing cached account balances, managing local orders, and inspecting a depot overview.
- A Typer-based CLI for logging in, fetching balances, and exporting transactions.
- A persistence layer backed by SQLite for cached data, configuration, and locally tracked orders.

The repository can be used as a starting point for building automation around the comdirect APIs or as a reference implementation when exploring the documentation stored in `comdirect_docu/`.

## Repository layout

```
.
├── docs/                   # Additional design notes and diagrams
├── src/bank_api/           # Python package source code
│   ├── api/                # FastAPI routers, dependencies, and HTML templates
│   ├── cli/                # Typer CLI entry point and commands
│   ├── client/             # HTTP clients that speak to comdirect endpoints
│   ├── persistence/        # SQLAlchemy models and repositories
│   └── services/           # Business logic used by the API, CLI, and UI
├── tests/                  # Unit tests and optional live sandbox tests
└── comdirect_docu/         # Official API documentation for quick reference
```

## Requirements

- Python 3.10 or later
- SQLite (bundled with Python, used by default for persistence)
- (Optional) Access to the comdirect sandbox for running the live test suite

## Installation

It is recommended to work inside a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

The editable install exposes the `bank_api` package, CLI entry point, and development tooling such as `pytest`, `ruff`, and `mypy`.

## Configuration

### FastAPI service

The web application reads a handful of environment variables at startup:

| Variable | Purpose | Default |
| --- | --- | --- |
| `BANK_API_SESSION_SECRET` | Key used by the session middleware that powers the HTML dashboard. | `insecure-development-secret` |
| `BANK_API_KEY` | API key required by the REST endpoints (passed via `X-API-Key`). | *(not set — API requests will fail until configured)* |

A SQLite database file named `bank_data.db` is created in the project root the first time the app or services run. Override the location by instantiating `DatabaseConfig(url="sqlite:///path/to/db.sqlite")` and passing it to the relevant services.

### CLI

The CLI persists its configuration beneath the OS-specific application directory (for example `~/.config/bank_api/config.json`). Commands respect the following environment variables when present:

| Variable | Purpose |
| --- | --- |
| `BANK_API_URL` | Override the base URL used for HTTP calls. |
| `BANK_API_KEY` or `BANK_API_CLI_KEY` | Provide the API key without storing it on disk. |

Run `bank-api login` once to interactively store the API URL and key.

### Live sandbox tests

The optional smoke tests under `tests/live/` hit the comdirect sandbox. Set these variables to enable the suite:

- `COMDIRECT_SANDBOX_USER`
- `COMDIRECT_SANDBOX_TOKEN`
- `COMDIRECT_SANDBOX_BASE_URL` (optional, defaults to `https://sandbox-api.comdirect.de/api/`)

If any variable is missing the tests are skipped automatically.

## Running the FastAPI server

Launch the development server with uvicorn:

```bash
uvicorn bank_api.api.app:app --reload
```

Navigate to `http://localhost:8000/login` to enter your comdirect user ID, account ID, and API key. After authentication you can:

- Review a dashboard summarising cached balances and recent orders.
- Update stored configuration values on the *Configuration* page.
- Create, list, and update locally tracked orders under *Orders*.
- Inspect the depot overview showing account totals grouped by currency.

The REST endpoints remain available under `/accounts` and `/transactions` for programmatic access, protected by the configured API key.

## Using the CLI

The CLI becomes available as the `bank-api` command after installation. Common workflows include:

```bash
# Store the API base URL and key (prompts interactively)
bank-api login

# Fetch balances for a user and display a chart
bank-api balances <USER_ID> --show-chart

# Export transactions for an account to CSV
bank-api export-transactions <ACCOUNT_ID> --output-csv my_transactions.csv
```

Use `bank-api --help` or `bank-api balances --help` to explore additional options.

## Running tests

Run the unit test suite with:

```bash
pytest
```

All live sandbox tests are marked with `pytest -m live`. To exercise only the mocked tests (no external dependencies), use:

```bash
pytest -m "not live"
```

Ensure you reinstall the project (`pip install -e .[dev]`) after modifying dependencies so that the test environment picks up the changes.

## Further reading

Detailed API specifications, including authentication requirements and schema definitions, are available inside the `comdirect_docu/` directory. These documents underpin the models and workflows implemented in this repository.
