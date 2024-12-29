import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

_HOUR_TO_SEND = 7


def get_seconds_to_7am(*, next_day: bool = False) -> int:
    """
    Return the number of seconds until 7am today, or if already past, tomorrow.

    `next_day`: whether to return for the next day's 7am instead
    """
    tz = ZoneInfo(os.environ["TZ"])
    now = datetime.now(tz)
    datetime_7am_today = datetime(
        year=now.year, month=now.month, day=now.day, hour=7, tzinfo=tz
    )
    if now.hour < _HOUR_TO_SEND and not next_day:
        # Time now is before 7am, so schedule for today
        return (datetime_7am_today - now).seconds
    # It's already past 7am
    return (datetime_7am_today + timedelta(days=1) - now).seconds
