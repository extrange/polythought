from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from polythought.util import get_seconds_to_7am

_TZ = ZoneInfo("Asia/Singapore")


def _at(hour: int) -> datetime:
    return datetime(2026, 1, 1, hour, tzinfo=_TZ)


def test_before_7am_returns_seconds_until_today() -> None:
    assert get_seconds_to_7am(now=_at(6)) == 3600


def test_at_7am_returns_seconds_until_tomorrow() -> None:
    assert get_seconds_to_7am(now=_at(7)) == 86_400


def test_after_7am_returns_seconds_until_tomorrow() -> None:
    assert get_seconds_to_7am(now=_at(8)) == 82_800


def test_next_day_returns_tomorrow_even_before_7am() -> None:
    assert get_seconds_to_7am(now=_at(6), next_day=True) == 90_000


def test_now_is_converted_to_configured_timezone() -> None:
    # 2025-12-31 22:00 UTC is 2026-01-01 06:00 in Singapore.
    now = datetime(2025, 12, 31, 22, 0, tzinfo=UTC)

    assert get_seconds_to_7am(now=now) == 3600
