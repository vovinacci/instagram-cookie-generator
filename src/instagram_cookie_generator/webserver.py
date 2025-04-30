"""
Flask server to expose a healthcheck endpoint for Instagram cookies.
"""

import os
import time
from datetime import UTC, datetime
from typing import Any, Dict, Tuple

from flask import Flask, Response, jsonify

from .cookie_manager import COOKIES_FILE
from .logger import get_logger

logger = get_logger()

app = Flask(__name__)


def get_cookie_metadata() -> Dict[str, Any]:
    """
    Extract metadata from the cookies file for status reporting.

    Returns:
        dict: Dictionary containing TTL, cookie count, names, expiry, etc.
    """
    try:
        if not os.path.exists(COOKIES_FILE) or os.path.getsize(COOKIES_FILE) == 0:
            return {
                "valid": False,
                "cookie_count": 0,
                "cookie_names": [],
                "expires_in": 0,
                "earliest_expiry": None,
                "last_updated": None,
            }

        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        cookies = [line.strip().split("\t") for line in lines if line.strip() and not line.startswith("#")]

        cookie_names = [c[5] for c in cookies if len(c) >= 7]
        expiry_times = [int(c[4]) for c in cookies if len(c) >= 7]

        now_ts = int(time.time())
        if not expiry_times:
            return {
                "valid": False,
                "cookie_count": len(cookies),
                "cookie_names": cookie_names,
                "expires_in": 0,
                "earliest_expiry": None,
                "last_updated": None,
            }

        earliest_expiry = min(expiry_times)
        expires_in = max(0, earliest_expiry - now_ts)

        mtime = os.path.getmtime(COOKIES_FILE)
        last_updated = datetime.fromtimestamp(mtime, UTC).isoformat()

        return {
            "valid": expires_in > 0,
            "cookie_count": len(cookies),
            "cookie_names": cookie_names,
            "expires_in": expires_in,
            "earliest_expiry": datetime.fromtimestamp(earliest_expiry, UTC).isoformat(),
            "last_updated": last_updated,
        }

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception(f"{type(e)}Failed to read or parse cookies file: {e}")
        return {
            "valid": False,
            "cookie_count": 0,
            "cookie_names": [],
            "expires_in": 0,
            "earliest_expiry": None,
            "last_updated": None,
            "error": str(e),
        }


@app.route("/status", methods=["GET"])
def status() -> Tuple[Response, int]:
    """
    Extended healthcheck endpoint for diagnostics.

    Returns:
        JSON: Cookie health status and metadata.
    """
    cookie_info = get_cookie_metadata()
    status_code = 200 if cookie_info.get("valid") else 503

    return (
        jsonify(
            {
                "fresh": cookie_info.get("valid", False),
                "message": (
                    "Cookies file found and valid." if cookie_info.get("valid") else "Cookies invalid or expired."
                ),
                "cookies": cookie_info,
                "version": os.getenv("CONTAINER_IMAGE_VERSION", "unknown"),
            }
        ),
        status_code,
    )


@app.route("/healthz", methods=["GET"])
def healthz() -> Tuple[Response, int]:
    """
    Minimal readiness probe.

    Returns:
        JSON: Up/down readiness probe.
    """
    cookie_info = get_cookie_metadata()

    if not cookie_info.get("valid") or cookie_info.get("expires_in", 0) < 3600:
        logger.warning("/healthz: cookies invalid or expiring soon.")
        return jsonify({"status": "unhealthy"}), 503

    logger.debug("/healthz: healthy")
    return jsonify({"status": "healthy"}), 200


def start_server() -> None:
    """
    Start the Flask web server.
    """
    logger.info("Starting Flask server...")
    app.run(host="0.0.0.0", port=5000)
