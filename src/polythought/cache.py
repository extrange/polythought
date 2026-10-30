"""In-memory TTL cache for data that is rate limited to fetch."""

import time
from collections.abc import Hashable


class TTLCache[K: Hashable, V]:
    """Mapping whose entries all expire a fixed number of seconds after being set."""

    def __init__(self, ttl: float) -> None:
        """Expire every entry `ttl` seconds after it is set."""
        self._ttl = ttl
        self._expires_at: dict[K, float] = {}
        self._values: dict[K, V] = {}

    def get(self, key: K, default: V | None = None) -> V | None:
        """Return the value for `key`, or `default` if it is missing or expired."""
        if self._expires_at.get(key, 0.0) <= time.monotonic():
            self._values.pop(key, None)
            self._expires_at.pop(key, None)
            return default
        return self._values[key]

    def set(self, key: K, value: V) -> None:
        """Store `value` under `key`, replacing any previous entry."""
        self._values[key] = value
        self._expires_at[key] = time.monotonic() + self._ttl
