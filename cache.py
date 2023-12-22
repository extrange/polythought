"""
Cache contacts to avoid Telegram rate limits
"""
from diskcache import Cache
from pathlib import Path

_cache_dir = Path(__file__).parent / ".cache"
_cache_dir.mkdir(exist_ok=True, parents=True)

cache = Cache(_cache_dir)
