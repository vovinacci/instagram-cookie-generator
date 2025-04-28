# Instagram Cookie Updater

Automatically refresh Instagram cookies using Selenium, save them in Netscape HTTP Cookie File format, and expose a healthcheck endpoint via Flask.
Designed for Dockerized, production-like deployments with Python.

Works well together with [ovchynnikov/load-bot-linux](https://github.com/ovchynnikov/load-bot-linux).

## Features

- Python 3.13 support
- Periodic auto-refresh of cookies
- Exports cookies compatible with cURL and other tools
- Uses headless Firefox browser
- Full Docker and Docker Compose support
- Health monitoring via `/status` endpoint

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
  pip install '.[dev]'
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

- **Build and run the container**:

  ```shell
  docker compose up --build
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

## Flask Health Endpoint

After startup, the Flask server exposes a simple healthcheck:

| Endpoint      | Purpose                                                        |
|:--------------|:---------------------------------------------------------------|
| `GET /status` | Returns 200 if cookies file exists and is fresh, otherwise 503 |

Example usage:

```shell
curl http://127.0.0.1:5000/status
```

## Code Style

| Tool     | Purpose               |
|:---------|:----------------------|
| `black`  | Code formatting       |
| `isort`  | Import sorting        |
| `mypy`   | Static type checking  |
| `pylint` | Static linting        |

All tools are integrated via Makefile and pre-commit hooks.

## Notes

- Dockerfile uses unpinned apt packages for simplicity; pinning can be added for strict reproducibility if needed.
- Logger supports both **plain** and **JSON** formats (configurable via `.env`).
