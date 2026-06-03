# Operations

This project runs as a Node.js service.

## Local Development

Install dependencies:

```bash
npm install
```

Run tests:

```bash
npm test
```

Start the service:

```bash
npm start
```

The service listens on `http://localhost:3000` by default.

## Runtime Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `PORT` | HTTP port for Express. | `3000` |
| `BANK_API_DB` | SQLite database file. | `bank_data.db` |
| `BANK_APP_KEY` | Optional override for the generated app key. | generated on first start |
| `BANK_API_SESSION_SECRET` | Secret for signed dashboard cookies. | `insecure-development-secret` |
| `BANK_API_URL` | comdirect API base URL. | `https://api.comdirect.de/api/` |
| `COMDIRECT_OAUTH_URL` | comdirect OAuth token host. | `https://api.comdirect.de` |
| `COMDIRECT_CLIENT_ID` | comdirect OAuth client ID. | dashboard config |
| `COMDIRECT_CLIENT_SECRET` | comdirect OAuth client secret. | dashboard config |
| `COMDIRECT_USERNAME` | comdirect username / Zugangsnummer. | dashboard config |
| `COMDIRECT_PASSWORD` | comdirect password/PIN. | dashboard config |

The REST API requires `X-App-Key`. comdirect OAuth credentials can be entered in the dashboard or supplied via environment variables.

## Docker

Build and start:

```bash
docker compose up --build
```

The container exposes port `3000` and persists SQLite data in the `bank-api-data` volume.

Healthcheck endpoint:

```text
GET /health
```

Expected response:

```json
{"status":"ok"}
```

## CLI

Store API URL and app key:

```bash
node node/bin/bank-api.js login --app-key <APP_KEY> --api-url http://localhost:3000
```

Fetch balances for the authenticated comdirect user:

```bash
node node/bin/bank-api.js balances user --refresh
```

Export transactions after you know the accountId:

```bash
node node/bin/bank-api.js export-transactions <ACCOUNT_ID> --refresh --output-csv transactions.csv
```

## Remaining Operational Gap

A live comdirect sandbox smoke test still needs to be added for the Node implementation before production use.
