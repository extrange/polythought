"""Shared pytest configuration: isolate tests from real credentials and state."""

import os
import tempfile
from pathlib import Path

_TMP_DIR = tempfile.TemporaryDirectory(prefix="polythought-tests-")
_ROOT = Path(_TMP_DIR.name)

# Settings are validated at import time, so this must happen before any
# `polythought` module is imported.
os.environ.update(
    {
        "TZ": "Asia/Singapore",
        "SESSION_FILE": str(_ROOT / "session"),
        "DB_PATH": str(_ROOT / "links.db"),
        "API_ID": "12345",
        "API_HASH": "test-api-hash",
        "BOT_TOKEN": "12345:test-bot-token",
        "CHANNEL_ID": "-1001234567890",
        "MY_CHAT_ID": "123456789",
        "BROWSERLESS_TOKEN": "test-browserless-token",
    }
)
