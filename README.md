# bank_api

A dependency-light Node.js service layer that wraps parts of the comdirect REST API.

The project ships with:

- a reusable comdirect client with OAuth password-grant support and retry/backoff handling,
- an Express REST API for cached balances and transactions,
- an HTML dashboard for configuration, local orders and depot overview,
- SQLite persistence for cached data, configuration, sync logs and local orders,
- a small CLI for login, balance listing and transaction CSV export,
- Node's built-in test runner.

## Repository Layout

```text
.
├── node/                   # Node.js implementation
│   ├── bin/                # CLI entry point
│   ├── public/             # Static assets
│   ├── src/                # API, client, services, persistence and jobs
│   ├── test/               # Node tests
│   └── views/              # EJS templates
├── comdirect_docu/         # comdirect API reference material
├── migration.md            # Migration history and remaining follow-up notes
├── package.json
└── Dockerfile
```

## Requirements

- Node.js 18.19 or later
- npm
- SQLite support through `better-sqlite3`
- comdirect OAuth credentials: `client_id`, `client_secret`, `username`, `password`

## Installation

```bash
npm install
```

## Configuration

The Node service reads these environment variables:

| Variable | Purpose | Default |
| --- | --- | --- |
| `PORT` | HTTP port for the Express server. | `3000` |
| `BANK_API_DB` | SQLite database path. | `bank_data.db` |
| `BANK_APP_KEY` | Optional override for the generated app key required by REST endpoints via `X-App-Key`. | generated on first start |
| `BANK_API_SESSION_SECRET` | Secret for signed dashboard session cookies. | `insecure-development-secret` |
| `BANK_API_URL` | comdirect API base URL used by banking endpoints. | `https://api.comdirect.de/api/` |
| `COMDIRECT_OAUTH_URL` | comdirect OAuth token host. | `https://api.comdirect.de` |
| `COMDIRECT_CLIENT_ID` | comdirect OAuth client ID. | from dashboard config |
| `COMDIRECT_CLIENT_SECRET` | comdirect OAuth client secret. | from dashboard config |
| `COMDIRECT_USERNAME` | comdirect username / Zugangsnummer. | from dashboard config |
| `COMDIRECT_PASSWORD` | comdirect password/PIN. | from dashboard config |

A local SQLite file is created on first start. It is ignored by git. If `BANK_APP_KEY` is not set, the app creates and stores a random app key automatically.

You can enter comdirect credentials in `http://localhost:3000/login` or provide them through environment variables. Environment variables take precedence over stored dashboard values for OAuth.

## Running The Server

```bash
npm start
```

Open `http://localhost:3000/login` to configure:

- local `App Key`, generated automatically on first start,
- comdirect `Client ID`,
- comdirect `Client Secret`,
- comdirect `Username`,
- comdirect `Password/PIN`,
- optional `Account ID` returned as `accountId` from balances.

Balances use the comdirect literal user path by default:

```text
/banking/clients/user/v2/accounts/balances
```

REST endpoints are protected with `X-App-Key`:

```bash
curl -H "X-App-Key: $BANK_APP_KEY" http://localhost:3000/accounts/user/balances
curl -H "X-App-Key: $BANK_APP_KEY" http://localhost:3000/accounts/<ACCOUNT_ID>/transactions
```

## CLI

The CLI is exposed as `bank-api-node` from `package.json`.

```bash
# Store REST API URL and app key locally
node node/bin/bank-api.js login --app-key <APP_KEY> --api-url http://localhost:3000

# Fetch balances for the current authenticated comdirect user
node node/bin/bank-api.js balances user --refresh

# Export transactions after you know the accountId
node node/bin/bank-api.js export-transactions <ACCOUNT_ID> --refresh --output-csv transactions.csv
```

The CLI reads `BANK_API_URL` and `BANK_APP_KEY` when present. Otherwise it uses `~/.config/bank_api/config.json`.

## Tests

```bash
npm test
```

The current Node tests cover the comdirect client behavior plus configuration and order services. Live sandbox tests are still listed as an open migration item in `migration.md`.

## Docker

```bash
docker compose up --build
```

The container exposes port `3000` and stores SQLite data in the `bank-api-data` volume.

## Further Reading

Detailed comdirect API specifications are available inside `comdirect_docu/`.
