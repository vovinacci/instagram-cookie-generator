"""
Unit tests for cookie_manager module.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from instagram_cookie_updater.cookie_manager import (
    already_logged_in,
    load_cookies,
    setup_browser,
)


@pytest.fixture()
def mock_geckodriver_manager(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Fixture for mocking GeckoDriverManager."""
    manager = MagicMock()
    manager.install.return_value = "/path/to/geckodriver"
    monkeypatch.setattr(
        "instagram_cookie_updater.cookie_manager.GeckoDriverManager",
        lambda: manager,
    )
    return manager


def test_setup_browser_creates_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup_browser creates a WebDriver instance."""
    driver_mock = MagicMock(spec=WebDriver)
    monkeypatch.setattr(
        "instagram_cookie_updater.cookie_manager.webdriver.Firefox", lambda *args, **kwargs: driver_mock
    )
    driver = setup_browser()

    assert driver is driver_mock


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
    # Prepare fake cookies file
    cookies_file = tmp_path / "cookies.txt"
    cookies_file.write_text(
        "# Netscape HTTP Cookie File\n.instagram.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\ttest_session\n"
    )

    driver = MagicMock(spec=WebDriver)
    load_cookies(driver, str(cookies_file))

    driver.add_cookie.assert_called_once()
