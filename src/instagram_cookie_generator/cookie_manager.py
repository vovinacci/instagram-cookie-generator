"""
Cookie Manager Module.

Handles browser automation to log into Instagram, manage cookies, and save them to file.
"""

import datetime
import os
import time
from typing import Optional, Sequence, Tuple, cast

from selenium import webdriver
from selenium.common import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.firefox import GeckoDriverManager

from .logger import get_logger
from .retry import retry

logger = get_logger()

# Load environment variables
INSTAGRAM_USERNAME = cast(str, os.getenv("INSTAGRAM_USERNAME"))
INSTAGRAM_PASSWORD = cast(str, os.getenv("INSTAGRAM_PASSWORD"))

COOKIES_FILE = os.getenv("COOKIES_FILE", "instagram_cookies.txt")

INSTAGRAM_LOGIN_URL = "https://www.instagram.com/accounts/login/"
INSTAGRAM_HOME_URL = "https://www.instagram.com/"

Locator = Tuple[str, str]


@retry(max_attempts=3, delay_seconds=3)
def setup_browser(headless: bool = True, lightweight: bool = True) -> WebDriver:
    """
    Set up a headless Firefox browser instance.

    Args:
        headless (bool): Run in headless mode if True.
        lightweight (bool): Disable loading of images, stylesheets, etc.

    Returns:
        WebDriver: A configured Firefox WebDriver instance.
    """
    options = Options()
    if headless:
        options.add_argument("-headless")
    if lightweight:
        options.set_preference("permissions.default.image", 2)
        options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", "false")
        options.set_preference("permissions.default.stylesheet", 2)
        options.set_preference("permissions.default.subdocument", 2)
        options.set_preference("permissions.default.object", 2)

    try:
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        return driver
    except WebDriverException:
        logger.exception("Failed to initialize Firefox WebDriver.")
        raise


def _dismiss_cookie_banner(driver: WebDriver) -> None:
    """Attempt to close Instagram's GDPR/consent banner if present."""
    candidate_buttons: Tuple[Locator, ...] = (
        (By.XPATH, "//button[contains(., 'Allow essential')]"),
        (By.XPATH, "//button[contains(., 'Allow all')]"),
        (By.XPATH, "//button[contains(., 'Accept')]"),
        (By.CSS_SELECTOR, "button[title='Only allow essential cookies']"),
        (By.CSS_SELECTOR, "button[aria-label='Only allow essential cookies']"),
    )

    for by, value in candidate_buttons:
        try:
            button = driver.find_element(by, value)
            button.click()
            time.sleep(1)
            return
        except NoSuchElementException:
            continue
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("Unable to click cookie banner button {}: {}", value, exc)


def _find_first_element(driver: WebDriver, locators: Sequence[Locator], wait_seconds: int = 15) -> Optional[WebElement]:
    """
    Try multiple locators until one is found or timeout expires.

    Uses repeated find_element calls to avoid brittle single-selector failures
    when Instagram tweaks its markup.
    """
    deadline = time.time() + wait_seconds
    last_exc: Optional[Exception] = None

    while time.time() < deadline:
        for by, value in locators:
            try:
                return driver.find_element(by, value)
            except NoSuchElementException as exc:
                last_exc = exc
                continue
        time.sleep(0.5)

    if last_exc:
        logger.debug("Elements not found for selectors: {}", [value for _, value in locators], exc_info=last_exc)
    return None


def load_cookies(driver: WebDriver, filename: str) -> None:
    """
    Load cookies from a file into the browser session.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        filename (str): Path to the cookies file.
    """
    if os.path.exists(filename):
        logger.info(f"Loading existing cookies from {filename}")
        try:
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines:
                if not line.startswith("#") and line.strip():
                    domain, _, path, secure, expiry, name, value = line.strip().split("\t")
                    cookie = {
                        "domain": domain,
                        "path": path,
                        "secure": secure == "TRUE",
                        "expiry": int(expiry),
                        "name": name,
                        "value": value,
                    }
                    try:
                        driver.add_cookie(cookie)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid cookie format for {name}: {e}")
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        # For unexpected exceptions, log full stack trace
                        logger.exception(f"{type(e)}: Unexpected error while adding cookie: {name}: {e}")
        except OSError as e:
            logger.exception(f"{type(e)}: Failed to read cookies file {filename}: {e}")


def save_cookies(driver: WebDriver, filename: str) -> None:
    """
    Save cookies from the browser session into a file.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        filename (str): Path to the cookies file.
    """
    logger.info(f"Saving cookies to file {filename}")

    try:
        cookies = driver.get_cookies()
        now = datetime.datetime.now()

        with open(filename, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# This file was generated by a script.\n")
            f.write("# http://curl.haxx.se/docs/http-cookies.html\n\n")

            for c in cookies:
                domain = c["domain"]
                flag = "TRUE" if domain.startswith(".") else "FALSE"
                path = c["path"]
                secure = "TRUE" if c.get("secure", False) else "FALSE"
                expiry = c.get("expiry", int(time.time()) + 3600)
                name = c["name"]
                value = c["value"]

                # Save cookie line
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")

                # Display human-readable expiration
                readable_expiry = datetime.datetime.fromtimestamp(expiry)
                delta = readable_expiry - now
                days = delta.days
                hours, remainder = divmod(delta.seconds, 3600)
                minutes, _ = divmod(remainder, 60)

                remaining = (
                    f"{days}d {hours}h {minutes}m"
                    if days > 0
                    else (f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m")
                )
                warning = (
                    " \u2757 Expiring soon!"
                    if delta.total_seconds() <= 24 * 3600
                    else (" \u26a0\ufe0f Less than 7 days" if delta.total_seconds() <= 7 * 24 * 3600 else "")
                )

                rexp: str = readable_expiry.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Cookie {name} expires at {rexp} (Time left: {remaining}){warning}")
    except OSError as e:
        logger.exception(f"{type(e)}: Failed to save cookies to file")


@retry(max_attempts=2, delay_seconds=2)
def already_logged_in(driver: WebDriver) -> bool:
    """
    Check if already logged into Instagram based on current page.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.

    Returns:
        bool: True if already logged in, False otherwise.
    """
    try:
        driver.get(INSTAGRAM_HOME_URL)
        time.sleep(3)
        return "accounts/login" not in driver.current_url
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception(f"{type(e)}: Error while checking login status.")
        return False


@retry(max_attempts=3, delay_seconds=5)
def login_instagram(driver: WebDriver) -> bool:
    """
    Perform Instagram login using provided credentials.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.

    Returns:
        bool: True if login succeeded, False otherwise.
    """
    driver.get(INSTAGRAM_LOGIN_URL)
    time.sleep(5)
    _dismiss_cookie_banner(driver)

    try:
        username_input = _find_first_element(
            driver,
            [
                (By.CSS_SELECTOR, "input[name='username']"),
                (By.NAME, "username"),
                (By.CSS_SELECTOR, "input[aria-label='Phone number, username, or email']"),
                (By.XPATH, "//input[contains(@aria-label, 'username') or contains(@name, 'username')]"),
            ],
        )
        password_input = _find_first_element(
            driver,
            [
                (By.CSS_SELECTOR, "input[name='password']"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[aria-label='Password']"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ],
        )

        if not username_input or not password_input:
            logger.error("Login page structure changed, username/password fields not found after waiting.")
            return False

        username_input.send_keys(INSTAGRAM_USERNAME)
        password_input.send_keys(INSTAGRAM_PASSWORD)
        password_input.send_keys(Keys.RETURN)

        time.sleep(8)

        try:
            driver.find_element(By.XPATH, "//button[contains(text(), 'Not Now')]").click()
            time.sleep(2)
        except NoSuchElementException:
            pass

        return already_logged_in(driver)
    except NoSuchElementException:
        logger.error("Login page structure has changed, username/password fields not found.")
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception(f"{type(e)}: Unexpected error during login flow.")
        return False


def cookie_manager() -> None:
    """
    Main function to refresh Instagram cookies.

    Handles loading existing cookies, login if needed, and saving new cookies.
    """
    if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
        raise ValueError("INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD must be set in environment variables")

    logger.info("Starting headless Firefox...")

    @retry()
    def do_work() -> None:
        driver = setup_browser()
        try:
            driver.get(INSTAGRAM_HOME_URL)
            time.sleep(3)

            if os.path.exists(COOKIES_FILE):
                load_cookies(driver, COOKIES_FILE)
                driver.refresh()
                time.sleep(5)

                if already_logged_in(driver):
                    logger.info("Logged in using existing cookies.")
                    save_cookies(driver, COOKIES_FILE)
                    return

                logger.info("Existing cookies invalid, logging in manually...")

            if login_instagram(driver):
                save_cookies(driver, COOKIES_FILE)

        finally:
            driver.quit()

    logger.info("Starting cookie manager with retry mechanism...")
    do_work()
    logger.info("Cookie manager task completed.")
