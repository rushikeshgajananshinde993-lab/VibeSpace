"""VibeSpace - central configuration file.

Everything the app needs to know about itself lives here, so the
application can be renamed or adjusted from ONE place.
"""

import os
import secrets

# ---------------------------------------------------------------------------
# Application identity (single place to rename the app)
# ---------------------------------------------------------------------------
APP_NAME = "VibeSpace"
APP_TAGLINE = "AI-Assisted Real-Time Collaborative Coding Platform"
APP_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Paths (all relative to BASE_DIR -> fully portable on a pendrive)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = "database"
DB_NAME = "vibespace.db"
WORKSPACE_FOLDER = "workspace"
DATA_FOLDER = "data"
STATIC_FOLDER = os.path.join(BASE_DIR, "static")
TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")

# ---------------------------------------------------------------------------
# Server settings
# 0.0.0.0 = listen on all network interfaces, so friends on the same
# network can open your website too (share your PC's LAN IP + port).
# ---------------------------------------------------------------------------
HOST = "0.0.0.0"
DEFAULT_PORT = 5000


def lan_ip():
    """Best-effort guess of this PC's LAN IP for sharing the link."""
    try:
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# ---------------------------------------------------------------------------
# Code execution limits (student-project safe values)
# ---------------------------------------------------------------------------
CODE_TIMEOUT_SECONDS = 10
MAX_OUTPUT_CHARS = 4000
MAX_CODE_CHARS = 50000

# ---------------------------------------------------------------------------
# Version history
# ---------------------------------------------------------------------------
VERSION_SAVE_INTERVAL_SECONDS = 5

# ---------------------------------------------------------------------------
# Secret key: generated once and stored in data/secret.key
# Session survives server restarts because the key file persists.
# ---------------------------------------------------------------------------
def secret_key():
    folder = os.path.join(BASE_DIR, DATA_FOLDER)
    os.makedirs(folder, exist_ok=True)
    key_file = os.path.join(folder, "secret.key")
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            key = f.read().strip()
            if key:
                return key
    key = secrets.token_hex(32)
    with open(key_file, "w", encoding="utf-8") as f:
        f.write(key)
    return key


def db_path():
    folder = os.path.join(BASE_DIR, DB_FOLDER)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, DB_NAME)