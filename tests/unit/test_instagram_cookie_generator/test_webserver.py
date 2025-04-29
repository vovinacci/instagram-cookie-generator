"""
Unit tests for webserver module.
"""

# pylint: disable=redefined-outer-name

import importlib
from pathlib import Path
from typing import Any

import pytest

from instagram_cookie_generator import cookie_manager, webserver


@pytest.fixture()
def patch_env_and_reload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Prepare environment and reload webserver."""
    # Create dummy cookies file
    dummy_file = tmp_path / "cookies.txt"
    dummy_file.write_text("dummy cookies content")

    # Patch os.getenv to return our dummy cookies path
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
    assert response.json == {"fresh": True, "message": "Cookies file found."}


def test_webserver_health(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test /status when cookies file is missing or empty."""
    # No file created = missing
    monkeypatch.setenv("COOKIES_FILE", str(tmp_path / "nonexistent_cookies.txt"))
    monkeypatch.setenv("INSTAGRAM_USERNAME", "dummyuser")
    monkeypatch.setenv("INSTAGRAM_PASSWORD", "dummypass")

    importlib.reload(cookie_manager)
    importlib.reload(webserver)

    client = webserver.app.test_client()
    response = client.get("/status")

    assert response.status_code == 503
    assert response.json == {"fresh": False, "message": "Cookies file missing or empty."}


def test_webserver_health_file_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test webserver status when os.path.getsize raises OSError."""
    monkeypatch.setattr("os.path.getsize", lambda *a, **kw: (_ for _ in ()).throw(OSError("fail")))
    importlib.reload(webserver)

    client = webserver.app.test_client()
    response = client.get("/status")

    assert response.status_code == 503
    assert response.json is not None
    assert response.json["fresh"] is False
