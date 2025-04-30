"""
Unit tests for webserver module.
"""

# pylint: disable=redefined-outer-name

import importlib
import time
from pathlib import Path
from typing import Any

import pytest

from instagram_cookie_generator import cookie_manager, webserver


@pytest.fixture()
def patch_env_and_reload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Prepare environment and reload webserver."""
    # Create dummy cookies file
    dummy_file = tmp_path / "cookies.txt"
    expiry = int(time.time()) + 7200
    cookie_line = f".instagram.com\tTRUE\t/\tFALSE\t{expiry}\tsessionid\tdummyvalue"
    dummy_file.write_text(cookie_line)

    # Patch environment variables
    monkeypatch.setenv("COOKIES_FILE", str(dummy_file))
    monkeypatch.setenv("INSTAGRAM_USERNAME", "dummyuser")
    monkeypatch.setenv("INSTAGRAM_PASSWORD", "dummypass")

    importlib.reload(cookie_manager)
    importlib.reload(webserver)

    return webserver


def test_webserver_status(patch_env_and_reload: Any) -> None:
    """Test that /status endpoint is healthy when cookies file exists."""
    client = patch_env_and_reload.app.test_client()
    response = client.get("/status")

    assert response.status_code == 200
    assert response.json is not None

    # Base health fields
    assert response.json["fresh"] is True
    assert response.json["cookies"]["valid"] is True

    # New fields
    cookies = response.json["cookies"]
    assert cookies["cookie_count"] > 0
    assert isinstance(cookies["cookie_names"], list)
    assert cookies["expires_in"] > 0
    assert cookies["earliest_expiry"] is not None
    assert cookies["last_updated"] is not None

    # Version should always be a string (could be "unknown")
    assert isinstance(response.json["version"], str)


def test_webserver_status_version_fallback(patch_env_and_reload: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that fallback version is used if package version fails."""
    monkeypatch.setattr(
        "instagram_cookie_generator.webserver.dist_version", lambda name: (_ for _ in ()).throw(Exception("fail"))
    )

    client = patch_env_and_reload.app.test_client()
    response = client.get("/status")

    assert response.status_code == 200
    assert response.json["version"] == "unknown"


def test_webserver_health_healthy(patch_env_and_reload: Any) -> None:
    """Test that /healthz reports healthy when cookies are valid and fresh."""
    client = patch_env_and_reload.app.test_client()
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json == {"status": "healthy"}


def test_webserver_status_empty_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test /status when cookies file is missing or empty."""
    empty_file = tmp_path / "cookies.txt"
    empty_file.touch()

    monkeypatch.setenv("COOKIES_FILE", str(empty_file))
    monkeypatch.setenv("INSTAGRAM_USERNAME", "dummyuser")
    monkeypatch.setenv("INSTAGRAM_PASSWORD", "dummypass")

    importlib.reload(cookie_manager)
    importlib.reload(webserver)

    client = webserver.app.test_client()
    response = client.get("/status")

    assert response.status_code == 503
    assert response.json is not None
    assert response.json["fresh"] is False
    assert response.json["cookies"]["valid"] is False


def test_webserver_health_unhealthy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test /healthz reports unhealthy when no valid cookies are present."""
    empty_file = tmp_path / "cookies.txt"
    empty_file.touch()

    monkeypatch.setenv("COOKIES_FILE", str(empty_file))
    monkeypatch.setenv("INSTAGRAM_USERNAME", "dummyuser")
    monkeypatch.setenv("INSTAGRAM_PASSWORD", "dummypass")

    importlib.reload(cookie_manager)
    importlib.reload(webserver)

    client = webserver.app.test_client()
    response = client.get("/healthz")

    assert response.status_code == 503
    assert response.json is not None
    assert response.json == {"status": "unhealthy"}


def test_webserver_health_file_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test webserver status when os.path.getsize raises OSError."""
    monkeypatch.setattr("os.path.getsize", lambda *a, **kw: (_ for _ in ()).throw(OSError("fail")))
    importlib.reload(webserver)

    client = webserver.app.test_client()
    response = client.get("/status")

    assert response.status_code == 503
    assert response.json is not None
    assert response.json["fresh"] is False
