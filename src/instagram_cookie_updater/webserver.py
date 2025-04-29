"""
Flask server to expose a healthcheck endpoint for Instagram cookies.
"""

import os
from typing import Tuple

from flask import Flask, Response, jsonify

from .cookie_manager import COOKIES_FILE
from .logger import get_logger

logger = get_logger()

app = Flask(__name__)


@app.route("/status", methods=["GET"])
def status() -> Tuple[Response, int]:
    """
    Healthcheck endpoint to verify cookies file availability.

    Returns:
        JSON: Health status.
    """
    try:
        file_exists = os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0
    except OSError as e:
        logger.error(f"Healthcheck {type(e)}: Error accessing cookies file: e")
        file_exists = False

    if file_exists:
        logger.debug("Healthcheck: cookies file found.")
        return jsonify({"fresh": True, "message": "Cookies file found."}), 200

    logger.warning("Healthcheck: cookies file missing or empty.")
    return jsonify({"fresh": False, "message": "Cookies file missing or empty."}), 503


def start_server() -> None:
    """
    Start the Flask web server.
    """
    logger.info("Starting Flask server...")
    app.run(host="0.0.0.0", port=5000)
