"""Tests for gameweek window calculation."""

from calendar import THURSDAY
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given
from hypothesis import strategies as st

from efl_points.gameweeks import GameweekWindow, gameweek_window

LONDON = ZoneInfo("Europe/London")
NEW_YORK = ZoneInfo("America/New_York")


@pytest.mark.parametrize(
    ("instant", "expected_start"),
    [
        pytest.param(
            datetime(2026, 10, 14, 19, 45, tzinfo=LONDON),
            datetime(2026, 10, 7, 23, 0, tzinfo=UTC),
            id="wednesday-evening-in-previous-week",
        ),
        pytest.param(
            datetime(2026, 10, 15, 0, 0, tzinfo=LONDON),
            datetime(2026, 10, 14, 23, 0, tzinfo=UTC),
            id="thursday-midnight-starts-new-week",
        ),
        pytest.param(
            datetime(2026, 10, 15, 0, 0, tzinfo=LONDON) - timedelta(microseconds=1),
            datetime(2026, 10, 7, 23, 0, tzinfo=UTC),
            id="microsecond-before-midnight-in-previous-week",
        ),
    ],
)
def test_gameweek_window_assigns_instant_to_correct_week(
    instant: datetime, expected_start: datetime
) -> None:
    assert gameweek_window(instant).start == expected_start


@pytest.mark.parametrize(
    ("instant", "expected_window", "expected_length"),
    [
        pytest.param(
            datetime(2026, 10, 24, 15, 0, tzinfo=LONDON),
            GameweekWindow(
                start=datetime(2026, 10, 21, 23, 0, tzinfo=UTC),
                end=datetime(2026, 10, 29, 0, 0, tzinfo=UTC),
            ),
            timedelta(hours=169),
            id="autumn-clocks-back",
        ),
        pytest.param(
            datetime(2027, 3, 27, 15, 0, tzinfo=LONDON),
            GameweekWindow(
                start=datetime(2027, 3, 25, 0, 0, tzinfo=UTC),
                end=datetime(2027, 3, 31, 23, 0, tzinfo=UTC),
            ),
            timedelta(hours=167),
            id="spring-clocks-forward",
        ),
    ],
)
def test_gameweek_window_handles_clock_changes(
    instant: datetime, expected_window: GameweekWindow, expected_length: timedelta
) -> None:
    window = gameweek_window(instant)
    assert window == expected_window
    assert window.end - window.start == expected_length


def test_gameweek_window_ignores_input_timezone() -> None:
    # Wednesday 21:00 in New York is Thursday 02:00 in London: a new gameweek.
    instant = datetime(2026, 10, 14, 21, 0, tzinfo=NEW_YORK)
    assert gameweek_window(instant).start == datetime(2026, 10, 14, 23, 0, tzinfo=UTC)


def test_gameweek_window_rejects_naive_datetime() -> None:
    naive = datetime(2026, 10, 14, 19, 40)  # noqa: DTZ001
    with pytest.raises(ValueError, match="timezone-aware"):
        gameweek_window(naive)


# Hypothesis needs naive bounds
any_instant = st.datetimes(
    min_value=datetime(2015, 1, 1),  # noqa: DTZ001
    max_value=datetime(2035, 12, 31),  # noqa: DTZ001
    timezones=st.just(UTC),
    allow_imaginary=False,
)


@given(any_instant)
def test_gameweek_window_contains_instant(instant: datetime) -> None:
    window = gameweek_window(instant)
    assert window.start <= instant < window.end


@given(any_instant)
def test_gameweek_window_is_unchanged_from_own_start(instant: datetime) -> None:
    window = gameweek_window(instant)
    assert gameweek_window(window.start) == window


@given(any_instant)
def test_gameweek_window_ends_where_next_window_starts(instant: datetime) -> None:
    window = gameweek_window(instant)
    assert gameweek_window(window.end).start == window.end


@given(any_instant)
def test_gameweek_window_starts_thursday_midnight_london(instant: datetime) -> None:
    start_london = gameweek_window(instant).start.astimezone(LONDON)
    assert start_london.weekday() == THURSDAY
    assert start_london.time() == time(0, 0)


@given(any_instant)
def test_gameweek_window_returns_utc_bounds(instant: datetime) -> None:
    window = gameweek_window(instant)
    assert window.start.tzinfo == UTC
    assert window.end.tzinfo == UTC
