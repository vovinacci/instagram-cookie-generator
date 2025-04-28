"""
Main module to orchestrate cookie refreshing and Flask server.

Spawns a background thread to refresh Instagram cookies periodically,
and launches a Flask webserver for health monitoring.
"""

import logging
import os
import threading
import time

from dotenv import load_dotenv

from .cookie_manager import cookie_manager
from .logger import setup_logger
from .webserver import start_server

setup_logger()
logger = logging.getLogger(__name__)

load_dotenv()

REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL_SECONDS", "3600"))


def refresh_worker() -> None:
    """
    Background thread that refreshes cookies at a fixed interval.
    """
    while True:
        logger.info("Refreshing Instagram cookies...")
        try:
            cookie_manager()
            logger.info("Cookies refreshed successfully.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Intentionally catching all exceptions to prevent the refresh worker from crashing the entire service.
            logger.error(f"{type(e)}: Error refreshing cookies: {e}")
        logger.info(f"Sleeping for {REFRESH_INTERVAL} seconds...")
        time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    # Start refresh worker thread
    threading.Thread(target=refresh_worker, daemon=True).start()

    # Start Flask webserver (this blocks main thread)
    start_server()
