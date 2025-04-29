"""
Unit tests for cookie_manager module.
"""

# pylint: disable=redefined-outer-name

import importlib
import os
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

import instagram_cookie_updater.cookie_manager as cm
from instagram_cookie_updater.cookie_manager import (
    already_logged_in,
    load_cookies,
    login_instagram,
    save_cookies,
    setup_browser,
)


@pytest.fixture()
def mock_driver() -> MagicMock:
    """Fixture for mocking WebDriver."""
    return MagicMock(spec=WebDriver)


@pytest.fixture()
def mock_geckodriver_manager(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Fixture for mocking GeckoDriverManager."""
    manager = MagicMock()
    manager.install.return_value = "/path/to/geckodriver"
    monkeypatch.setattr("instagram_cookie_updater.cookie_manager.GeckoDriverManager", lambda: manager)
    return manager


def test_setup_browser_creates_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup_browser creates a WebDriver instance."""
    driver_mock = MagicMock(spec=WebDriver)
    monkeypatch.setattr("instagram_cookie_updater.cookie_manager.webdriver.Firefox", lambda *a, **kw: driver_mock)

    driver = setup_browser()
    assert driver is not None
    assert isinstance(driver, MagicMock)


def test_already_logged_in_when_logged_in() -> None:
    """Test already_logged_in returns True when login URL is not present."""
    driver = MagicMock(spec=WebDriver)
    driver.current_url = "https://www.instagram.com/"
    assert already_logged_in(driver) is True


def test_already_logged_in_when_not_logged_in() -> None:
    """Test already_logged_in returns False when redirected to login page."""
    driver = MagicMock(spec=WebDriver)
    driver.current_url = "https://www.instagram.com/accounts/login/"
    assert already_logged_in(driver) is False


def test_load_cookies_from_file(tmp_path: Path) -> None:
    """Test load_cookies correctly reads cookies from file."""
    cookies_file = tmp_path / "cookies.txt"
    cookies_file.write_text(
        "# Netscape HTTP Cookie File\n.instagram.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\ttest_session\n"
    )

    driver = MagicMock(spec=WebDriver)
    load_cookies(driver, str(cookies_file))

    driver.add_cookie.assert_called_once()


def test_save_cookies_writes_file(tmp_path: Path, mock_driver: MagicMock) -> None:
    """Test save_cookies saves cookies to a file."""
    mock_driver.get_cookies.return_value = [
        {
            "domain": ".instagram.com",
            "path": "/",
            "secure": True,
            "expiry": int(time.time()) + 3600,
            "name": "sessionid",
            "value": "fake_value",
        }
    ]
    cookies_file = tmp_path / "cookies.txt"
    save_cookies(mock_driver, str(cookies_file))

    assert cookies_file.exists()
    contents = cookies_file.read_text()
    assert "sessionid" in contents
    assert "fake_value" in contents


def test_login_instagram_success(monkeypatch: pytest.MonkeyPatch, mock_driver: MagicMock) -> None:
    """Test login_instagram succeeds with valid username and password fields."""
    mock_username = MagicMock()
    mock_password = MagicMock()

    def find_element_side_effect(by: Any, value: Any) -> MagicMock:
        if by == By.NAME and value == "username":
            return mock_username
        if by == By.NAME and value == "password":
            return mock_password
        if by == By.XPATH and value == "//button[contains(text(), 'Not Now')]":
            return MagicMock()
        raise ValueError(f"Unexpected locator: {by}, {value}")

    mock_driver.find_element.side_effect = find_element_side_effect
    monkeypatch.setattr("instagram_cookie_updater.cookie_manager.already_logged_in", lambda driver: True)

    result = login_instagram(mock_driver)
    assert result is True
    mock_username.send_keys.assert_called()
    mock_password.send_keys.assert_called()


def test_login_instagram_failure(monkeypatch: pytest.MonkeyPatch, mock_driver: MagicMock) -> None:
    """Test login_instagram fails gracefully when elements are missing."""
    mock_driver.find_element.side_effect = Exception("Element not found")
    monkeypatch.setattr("instagram_cookie_updater.cookie_manager.already_logged_in", lambda driver: False)

    result = login_instagram(mock_driver)
    assert result is False


def test_cookie_manager_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test cookie_manager main flow does not crash under mocks."""
    # Patch env FIRST
    monkeypatch.setitem(os.environ, "INSTAGRAM_USERNAME", "dummyuser")
    monkeypatch.setitem(os.environ, "INSTAGRAM_PASSWORD", "dummypass")

    # Reload the module to pick up env
    importlib.reload(cm)

    driver = MagicMock(spec=WebDriver)
    monkeypatch.setattr(cm, "setup_browser", lambda: driver)
    monkeypatch.setattr(cm, "load_cookies", lambda driver, file: None)
    monkeypatch.setattr(cm, "save_cookies", lambda driver, file: None)
    monkeypatch.setattr(cm, "already_logged_in", lambda driver: True)

    cm.cookie_manager()


def test_load_cookies_failure(monkeypatch: pytest.MonkeyPatch, mock_driver: MagicMock) -> None:
    """Test load_cookies handles file read error."""
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("fail")))
    load_cookies(mock_driver, "dummy_path")


def test_save_cookies_failure(monkeypatch: pytest.MonkeyPatch, mock_driver: MagicMock) -> None:
    """Test save_cookies handles file write error."""
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("fail")))
    save_cookies(mock_driver, "dummy_path")
