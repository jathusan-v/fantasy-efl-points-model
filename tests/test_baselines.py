"""Tests for historical-points baselines."""

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from efl_points.models.baselines import b0_predictions

AS_OF = datetime(2026, 10, 14, 23, 0, tzinfo=UTC)


def _results(*rows: tuple[int, int, int, int, int]) -> pd.DataFrame:
    """Rows: player_id, game_id, squad_id, minutes_played, points."""
    return pd.DataFrame(
        rows,
        columns=["player_id", "game_id", "squad_id", "minutes_played", "points"],
    ).astype("int64")


def _fixtures(*rows: tuple[int, int]) -> pd.DataFrame:
    """Rows: game_id, days before AS_OF (negative means after)."""
    return pd.DataFrame(
        {
            "game_id": [game_id for game_id, _ in rows],
            "kickoff": pd.to_datetime(
                [AS_OF - timedelta(days=days) for _, days in rows], utc=True
            ),
        }
    )


def _targets(*rows: tuple[int, int, int]) -> pd.DataFrame:
    """Rows: game_id, home_squad_id, away_squad_id."""
    return pd.DataFrame(
        rows, columns=["game_id", "home_squad_id", "away_squad_id"]
    ).astype("int64")


def test_b0_predictions_averages_last_k_appearances() -> None:
    results = _results(
        (7, 1, 10, 90, 1),
        (7, 2, 10, 90, 2),
        (7, 3, 10, 90, 3),
        (7, 4, 10, 90, 4),
        (7, 5, 10, 90, 5),
        (7, 6, 10, 90, 6),
    )
    # Oldest-first, so taking the first k rows without sorting gives the wrong mean.
    fixtures = _fixtures((1, 6), (2, 5), (3, 4), (4, 3), (5, 2), (6, 1))
    targets = _targets((100, 10, 20))

    actual = b0_predictions(results, fixtures, targets, AS_OF, k=5)

    assert len(actual) == 1
    # Latest five: (2 + 3 + 4 + 5 + 6) / 5 = 4.
    assert actual.loc[0, "expected_points"] == pytest.approx(4.0)
    assert actual.loc[0, "n_appearances"] == 5


def test_b0_predictions_ignores_zero_minute_records() -> None:
    results = _results(
        (7, 1, 10, 90, 2),
        (7, 2, 10, 90, 6),
        (7, 3, 10, 0, 0),
    )
    fixtures = _fixtures((1, 3), (2, 2), (3, 1))
    targets = _targets((100, 10, 20))

    actual = b0_predictions(results, fixtures, targets, AS_OF, k=2)

    # The zero-minute record must neither enter the mean nor consume a slot.
    assert actual.loc[0, "expected_points"] == pytest.approx(4.0)
    assert actual.loc[0, "n_appearances"] == 2


def test_b0_predictions_excludes_results_at_or_after_as_of() -> None:
    results = _results(
        (7, 1, 10, 90, 2),
        (7, 2, 10, 90, 6),
        (7, 3, 10, 90, 20),
        (7, 4, 10, 90, 40),
    )
    fixtures = _fixtures(
        (1, 2),
        (2, 1),
        (3, 0),  # exactly AS_OF: excluded.
        (4, -1),  # after AS_OF: excluded.
    )
    targets = _targets((100, 10, 20))

    actual = b0_predictions(results, fixtures, targets, AS_OF, k=5)

    assert actual.loc[0, "expected_points"] == pytest.approx(4.0)
    assert actual.loc[0, "n_appearances"] == 2


def test_b0_predictions_uses_available_appearances_when_fewer_than_k() -> None:
    results = _results(
        (7, 1, 10, 90, 3),
        (7, 2, 10, 45, 6),
    )
    fixtures = _fixtures((1, 2), (2, 1))
    targets = _targets((100, 10, 20))

    actual = b0_predictions(results, fixtures, targets, AS_OF, k=5)

    assert actual.loc[0, "expected_points"] == pytest.approx(4.5)
    assert actual.loc[0, "n_appearances"] == 2


def test_b0_predictions_assigns_player_to_latest_squad() -> None:
    results = _results(
        (7, 1, 10, 90, 2),
        (7, 2, 10, 90, 6),
        (7, 3, 20, 0, 0),  # unused substitute at his new club
        (7, 4, 30, 90, 30),  # after AS_OF: must not change his squad
    )
    fixtures = _fixtures((1, 3), (2, 2), (3, 1), (4, -1))
    targets = _targets((100, 10, 97), (200, 20, 98), (300, 30, 99))

    actual = b0_predictions(results, fixtures, targets, AS_OF, k=5)

    assert list(actual["game_id"]) == [200]
    # Appearances for his previous club still count towards his form.
    assert actual.loc[0, "expected_points"] == pytest.approx(4.0)
    assert actual.loc[0, "n_appearances"] == 2


def test_b0_predictions_predicts_each_target_fixture() -> None:
    results = _results(
        (8, 1, 10, 90, 6),
        (7, 1, 10, 90, 2),
    )
    fixtures = _fixtures((1, 1))
    # Squad 10 is away in game 200 and home in game 100.
    targets = _targets((200, 99, 10), (100, 10, 98))

    actual = b0_predictions(results, fixtures, targets, AS_OF, k=5)

    assert actual[["game_id", "player_id"]].values.tolist() == [
        [100, 7],
        [100, 8],
        [200, 7],
        [200, 8],
    ]
    assert list(actual["expected_points"]) == [2.0, 6.0, 2.0, 6.0]
    assert list(actual["n_appearances"]) == [1, 1, 1, 1]
    assert list(actual.index) == [0, 1, 2, 3]


def test_b0_predictions_omits_players_without_appearances() -> None:
    results = _results(
        (7, 1, 10, 0, 0),  # never came on
        (8, 2, 10, 90, 20),  # only appears after AS_OF
    )
    fixtures = _fixtures((1, 1), (2, -1))
    targets = _targets((100, 10, 20))

    actual = b0_predictions(results, fixtures, targets, AS_OF, k=5)

    assert actual.empty
    assert list(actual.columns) == [
        "game_id",
        "player_id",
        "expected_points",
        "n_appearances",
    ]


def test_b0_predictions_rejects_result_without_fixture() -> None:
    results = _results((7, 1, 10, 90, 2))
    fixtures = _fixtures((2, 1))
    targets = _targets((100, 10, 20))

    with pytest.raises(ValueError, match="fixture"):
        b0_predictions(results, fixtures, targets, AS_OF, k=5)


@pytest.mark.parametrize("k", [0, -1])
def test_b0_predictions_rejects_non_positive_k(k: int) -> None:
    results = _results((7, 1, 10, 90, 2))
    fixtures = _fixtures((1, 1))
    targets = _targets((100, 10, 20))

    with pytest.raises(ValueError, match="k must be"):
        b0_predictions(results, fixtures, targets, AS_OF, k=k)


def test_b0_predictions_rejects_naive_as_of() -> None:
    results = _results((7, 1, 10, 90, 2))
    fixtures = _fixtures((1, 1))
    targets = _targets((100, 10, 20))
    naive = datetime(2026, 10, 14, 23, 0)  # noqa: DTZ001

    with pytest.raises(ValueError, match="timezone-aware"):
        b0_predictions(results, fixtures, targets, naive, k=5)
