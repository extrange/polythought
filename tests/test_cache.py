from polythought.cache import TTLCache


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_missing_key_returns_default() -> None:
    cache: TTLCache[str, int] = TTLCache(ttl=10, clock=_FakeClock())

    assert cache.get("missing") is None
    assert cache.get("missing", 7) == 7


def test_value_is_available_before_ttl() -> None:
    clock = _FakeClock()
    cache: TTLCache[str, int] = TTLCache(ttl=10, clock=clock)
    cache.set("key", 1)

    clock.now = 9.999

    assert cache.get("key") == 1


def test_value_expires_at_ttl() -> None:
    clock = _FakeClock()
    cache: TTLCache[str, int] = TTLCache(ttl=10, clock=clock)
    cache.set("key", 1)

    clock.now = 10.0

    assert cache.get("key") is None


def test_set_replaces_value_and_extends_expiry() -> None:
    clock = _FakeClock()
    cache: TTLCache[str, int] = TTLCache(ttl=10, clock=clock)
    cache.set("key", 1)

    clock.now = 5.0
    cache.set("key", 2)
    clock.now = 12.0

    assert cache.get("key") == 2
