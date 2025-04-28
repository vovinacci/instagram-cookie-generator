"""
Flask server to expose a healthcheck endpoint for Instagram cookies.
"""

import os
from typing import Tuple

from flask import Flask, Response, jsonify

from .cookie_manager import COOKIES_FILE

app = Flask(__name__)


@app.route("/status", methods=["GET"])
def status() -> Tuple[Response, int]:
    """
    Healthcheck endpoint to verify cookies file availability.

    Returns:
        JSON: Health status.
    """
    if os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
        return jsonify({"fresh": True, "message": "Cookies file found."}), 200
    return jsonify({"fresh": False, "message": "Cookies file missing or empty."}), 503


def start_server() -> None:
    """
    Start the Flask web server.
    """
    app.run(host="0.0.0.0", port=5000)
