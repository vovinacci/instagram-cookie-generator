# Instagram Cookie Updater

Automatically refresh Instagram cookies using Selenium, save them in Netscape HTTP Cookie File format, and expose a healthcheck endpoint via Flask.
Designed for Dockerized, production-like deployments with Python.

Works well together with [ovchynnikov/load-bot-linux](https://github.com/ovchynnikov/load-bot-linux)

Features:

- Python 3.13 support
- Periodic auto-refresh of cookies
- Exports cookies compatible with cURL and other tools
- Uses headless Firefox browser
- Full Docker amd Docker Compose support
- Health monitoring via `/status` endpoint

## Local setup

- Dependencies:
  - [Python](https://www.python.org/) == 3.13
  - [Virtualenv](https://virtualenv.pypa.io/en/latest/)

- Create Python virtualenv (required during first run only)

  ```shell
  mkdir -p "${HOME}/.local/virtualenv" && \
    python3.13 -m venv ~/.local/virtualenv/instagram-cookie-generator && \
    source "${HOME}/.local/virtualenv/instagram-cookie-generator/bin/activate" && \
    pip install --upgrade pip
  ```

- Activate Python virtualenv

  ```shell
  source "${HOME}/.local/virtualenv/instagram-cookie-generator/bin/activate"
  ```

- Install packages

  ```shell
  pip install '.[dev,suite]'
  ```

- Check Python tool versions

  ```shell
  black --version && \
  echo -n "isort " && isort --version-number && \
  mypy --version && \
  pylint --version
  ```

### Running in Docker

- Build and run the Docker container:

  ```shell
  docker compose up --build
  ```

- Environment Variables
  Create a `.env` file with the following keys:

  ```shell
  INSTAGRAM_USERNAME=your_instagram_username
  INSTAGRAM_PASSWORD=your_instagram_password
  REFRESH_INTERVAL_SECONDS=3600
  COOKIES_FILE=instagram_cookies.txt
  ```

  Make sure to **mount your `.env`** when running Docker, if needed.

## Make targets

Make targets are self-documented, issue `make` or `make help` to show all available make targets with brief descriptions.

## Pre-Commit Hooks

This repo uses pre-commit to ensure code quality **before each commit**.

To install hooks:

```shell
make hooks-install
```

For the list of checks, please see [pre-commit configuration](.pre-commit-config.yaml)

## Flask Health Endpoint

Once running, the Flask server exposes a simple healthcheck:

| Endpoint      | Purpose                                                        |
|:--------------|:---------------------------------------------------------------|
| `GET /status` | Returns 200 if cookies file exists and is fresh, otherwise 503 |

Example:

```shell
curl http://127.0.0.1:5000/status
```

## Code Style

| Tool   | Purpose               |
|:-------|:----------------------|
| black  | Code formatting       |
| isort  | Import sorting        |
| mypy   | Static type checking  |
| pylint | Static linting        |

All tools are integrated via Makefile and pre-commit hooks.

## Notes

- Dockerfile uses unpinned apt packages for simplicity; pinning can be added for strict reproducibility.
