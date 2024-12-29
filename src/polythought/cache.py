"""Cache contacts to avoid Telegram rate limits."""

from diskcache import Cache

from polythought.settings import Settings

cache = Cache(Settings.DISK_CACHE_DIR)
