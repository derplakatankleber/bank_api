# Operations Guide

This document describes how to run the `bank-api` service securely in different environments and how to work with the accompanying automation.

## Table of contents

1. [Local development](#local-development)
2. [Test strategy](#test-strategy)
3. [Continuous integration](#continuous-integration)
4. [Containerisation](#containerisation)
5. [Infrastructure as Code](#infrastructure-as-code)
6. [Security practices](#security-practices)
7. [Operational playbooks](#operational-playbooks)

## Local development

### Prerequisites

- Python 3.11 or newer
- `pip` and `virtualenv`
- Docker (for container workflows)
- Terraform 1.5+ (for IaC workflows)

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .[dev]
```

Run the mocked test suite:

```bash
pytest -m "mocked"
```

To execute the optional live sandbox suite you must supply valid comdirect sandbox credentials and pass `--run-live`:

```bash
export COMDIRECT_SANDBOX_USER=your-user
export COMDIRECT_SANDBOX_TOKEN=your-token
pytest --run-live -m "live"
```

## Test strategy

- **Mocked tests** simulate HTTP responses for deterministic, fast feedback.
- **Live tests** (opt-in) reach the comdirect sandbox. They are skipped unless `--run-live` is set or the CI workflow is triggered manually with the `run_live` input. The tests expect:
  - `COMDIRECT_SANDBOX_USER`
  - `COMDIRECT_SANDBOX_TOKEN`
  - optional `COMDIRECT_SANDBOX_BASE_URL` (defaults to the documented sandbox endpoint)

## Continuous integration

GitHub Actions workflow [`ci.yml`](../.github/workflows/ci.yml) runs on pushes and pull requests:

1. **Lint**: `ruff check .` and `black --check .`
2. **Type check**: `mypy src`
3. **Tests**: `pytest -m "mocked"`
4. **Live sandbox** (manual opt-in): `pytest --run-live -m "live"` with secrets injected via repository settings. Trigger the workflow manually and set the `run_live` input to `true` to enable this job.

All jobs install dependencies using the `dev` extra defined in `pyproject.toml`.

## Containerisation

A hardened [`Dockerfile`](../Dockerfile) builds a non-root image that runs the FastAPI application via Uvicorn. A companion [`docker-compose.yml`](../docker-compose.yml) file orchestrates the API with a PostgreSQL database:

- Secrets (database password, API keys) are injected through environment variables. Use an `.env` file locally and set them as secrets in production orchestrators.
- The API container publishes port `8000` by default and exposes a `/health` endpoint used for health checks.
- Volumes persist application artefacts and database state. Consider storing the database volume on encrypted storage in production.

To run locally:

```bash
cp .env.example .env  # create a file with POSTGRES_PASSWORD, BANK_API_SECRET_KEY, etc.
docker compose up --build
```

## Infrastructure as Code

Terraform configuration in [`infra/terraform`](../infra/terraform) provisions the same topology via the Docker provider:

```bash
cd infra/terraform
terraform init
terraform apply \
  -var="comdirect_user=$COMDIRECT_SANDBOX_USER" \
  -var="comdirect_token=$COMDIRECT_SANDBOX_TOKEN" \
  -var="secret_key=$(openssl rand -hex 32)"
```

The module:

- Builds the container image from the repository `Dockerfile`.
- Creates an isolated Docker network and a persistent PostgreSQL volume.
- Launches hardened API and database containers with the supplied secrets.

For production deployments substitute the Docker provider with the target platform (e.g. AWS ECS) while retaining the variable naming to keep secrets handling consistent.

## Security practices

- **Secret management**: never commit secrets to version control. Use GitHub Action secrets, Docker secret stores, or cloud vaults.
- **Network**: expose only the API port required by clients and restrict ingress via firewalls or reverse proxies.
- **TLS**: terminate TLS using a reverse proxy (e.g. Traefik, Nginx) or a managed load balancer. The sample Compose file assumes TLS termination upstream.
- **Least privilege**: the Docker image runs as a non-root user. Extend this by configuring read-only root filesystems or seccomp profiles where possible.
- **Dependency hygiene**: CI runs `ruff`, `black`, and `mypy` on every change. Add dependency scanning (e.g. Dependabot) for automated updates.

## Operational playbooks

- **Health monitoring**: poll `/health` and add synthetic transactions against the sandbox environment as part of observability dashboards.
- **Backups**: snapshot the PostgreSQL volume regularly. When using cloud databases, configure automated backups and PITR.
- **Incident response**: revoke compromised sandbox tokens immediately and rotate the `BANK_API_SECRET_KEY`. Update Terraform variables or Compose `.env` files accordingly and redeploy.
- **Disaster recovery**: keep Terraform state in a remote backend (S3 + DynamoDB or Terraform Cloud) and store Docker images in a secure registry. Re-apply the Terraform module or redeploy via Compose to restore service.
