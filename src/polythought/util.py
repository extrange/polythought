from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from polythought.settings import Settings

_HOUR_TO_SEND = 7


def get_seconds_to_7am(
    *,
    next_day: bool = False,
    now: datetime | None = None,
) -> int:
    """
    Return the number of seconds until 7am today, or if already past, tomorrow.

    `next_day`: whether to return for the next day's 7am instead
    `now`: inject the current time (must be timezone-aware; naive values use TZ)
    """
    tz = ZoneInfo(Settings.TZ)
    current = now or datetime.now(tz)
    current = (
        current.replace(tzinfo=tz) if current.tzinfo is None else current.astimezone(tz)
    )

    seven_am_today = datetime(
        year=current.year,
        month=current.month,
        day=current.day,
        hour=_HOUR_TO_SEND,
        tzinfo=tz,
    )
    if current.hour < _HOUR_TO_SEND and not next_day:
        # Time now is before 7am, so schedule for today
        return int((seven_am_today - current).total_seconds())
    # It's already past 7am
    return int(
        (seven_am_today + timedelta(days=1) - current).total_seconds(),
    )
