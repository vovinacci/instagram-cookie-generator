# Instagram Cookie Updater

Automatically refresh Instagram cookies using Selenium, save them in Netscape HTTP Cookie File format, and expose
healthcheck and readiness endpoints via Flask.
Designed for Dockerized, production-like deployments with Python.

Works well together
with [yt-dlp](https://github.com/yt-dlp/yt-dlp), [gallery-dl](https://github.com/mikf/gallery-dl/tree/master) or bots
like [ovchynnikov/load-bot-linux](https://github.com/ovchynnikov/load-bot-linux).

## Features

- Python 3.13 support
- Periodic auto-refresh of cookies
- Exports cookies compatible with cURL and other tools
- Uses headless Firefox browser
- Full Docker and Docker Compose support
- Health monitoring via `/status` and `/healthz` endpoints
- Manual PR-based image build via GitHub Actions for debugging

## Local Setup

- **Dependency**:
  [Python 3.13](https://www.python.org/)

- **Create Python virtualenv** (required during first run):

  ```shell
  mkdir -p "${HOME}/.local/virtualenv" && \
    python3.13 -m venv ~/.local/virtualenv/instagram-cookie-generator && \
    source "${HOME}/.local/virtualenv/instagram-cookie-generator/bin/activate" && \
    pip install --upgrade pip
  ```

- **Activate virtualenv**:

  ```shell
  source "${HOME}/.local/virtualenv/instagram-cookie-generator/bin/activate"
  ```

- **Install dependencies**:

  ```shell
  pip install -e '.[dev]'
  ```

- **Verify installed tools**:

  ```shell
  black --version && \
  echo -n "isort " && isort --version-number && \
  mypy --version && \
  pylint --version
  ```

## Running in Docker Compose

- **Prepare environment variables**:

  Copy `.env.example` to `.env` and edit your credentials:

  ```shell
  cp .env.example .env
  ```

- **Run the container**:

  ```shell
  docker compose up
  ```

- **Healthcheck integration**:

  Docker Compose is configured with a healthcheck using the `/healthz` endpoint:

  ```yaml
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5000/healthz"]
    interval: 2m
    timeout: 10s
    retries: 3
  ```

## Make Targets

Make targets are self-documented.

List all available targets:

```shell
make help
```

Typical examples:

- `make code-checks` — Run full code quality checks
- `make hooks-install` — Install pre-commit hooks

## Pre-Commit Hooks

This repository uses [pre-commit](https://pre-commit.com/) to enforce code quality **before each commit**.

To install hooks:

```shell
make hooks-install
```

See configured checks inside [.pre-commit-config.yaml](./.pre-commit-config.yaml).

## Flask Health Endpoints

After startup, the Flask server exposes two health endpoints:

| Endpoint       | Purpose                                                              |
|----------------|----------------------------------------------------------------------|
| `GET /status`  | Returns rich cookie metadata: TTL, names, updated timestamp, version |
| `GET /healthz` | Returns 200 only if cookies are valid and not expired                |

Example usage:

```shell
curl http://127.0.0.1:5000/status
curl http://127.0.0.1:5000/healthz
```

## GitHub Actions - Manual PR Docker Build

You can manually trigger a Docker image build and push to GHCR from any Pull Request.
Useful for **debugging changes before merging**.

The workflow can be run from the **Actions** tab by selecting `Manual PR Image Build` and clicking "Run workflow".

Tag format: `ghcr.io/vovinacci/instagram-cookie-generator:pr-<PR_NUMBER>`

## Code Style

| Tool     | Purpose              |
|:---------|:---------------------|
| `black`  | Code formatting      |
| `isort`  | Import sorting       |
| `mypy`   | Static type checking |
| `pylint` | Static linting       |

All tools are integrated via Makefile and pre-commit hooks.

## Notes

- Dockerfile uses unpinned apt packages for simplicity; pinning can be added for strict reproducibility if needed.
- Logger supports both **plain** and **JSON** formats (configurable via `.env`).
