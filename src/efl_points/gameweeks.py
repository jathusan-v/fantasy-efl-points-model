"""Gameweek windows. Thursday 00:00 to Thursday 00:00 London time.

Windows are half-open, [start, end), with UTC-aware bounds.
Clock changes make a window 167, 168 or 169 hours long.
"""

from calendar import THURSDAY
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")


@dataclass(frozen=True)
class GameweekWindow:
    """A gameweek as a half-open UTC interval.

    Attributes
    ----------
    start : datetime
        Thursday 00:00 London time, as a UTC-aware datetime. Included.
    end : datetime
        The following Thursday 00:00 London time, as a UTC-aware datetime. Excluded.
    """

    start: datetime
    end: datetime


def gameweek_window(instant: datetime) -> GameweekWindow:
    """Return the gameweek window containing an instant.

    Parameters
    ----------
    instant : datetime
        Timezone-aware instant to locate.

    Returns
    -------
    GameweekWindow
        The window satisfying start <= instant < end.

    Raises
    ------
    ValueError
        If instant is naive.
    """
    if instant.utcoffset() is None:
        raise ValueError("instant must be timezone-aware")

    local = instant.astimezone(LONDON)
    days_since_thursday = (local.weekday() - THURSDAY) % 7
    start_date = local.date() - timedelta(days=days_since_thursday)
    end_date = start_date + timedelta(days=7)

    start = datetime.combine(start_date, time(0, 0), tzinfo=LONDON)
    end = datetime.combine(end_date, time(0, 0), tzinfo=LONDON)
    return GameweekWindow(start=start.astimezone(UTC), end=end.astimezone(UTC))
