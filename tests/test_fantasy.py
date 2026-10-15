"""Tests for loading Fantasy EFL snapshot files."""

import gzip
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from efl_points.data.fantasy import load_fixtures, load_player_results


def _write_gzip_json(path: Path, payload: Any) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle)


def _player(
    player_id: int,
    game_id: int,
    round_id: int,
    *,
    squad_id: int = 1,
    minutes: int = 90,
    points: int = 2,
) -> dict[str, int]:
    return {
        "playerId": player_id,
        "gameId": game_id,
        "squadId": squad_id,
        "roundId": round_id,
        "minutesPlayed": minutes,
        "points": points,
        "saves": 0,  # not a loader column: proves that extra fields are dropped
    }


def _game(
    game_id: int,
    date: str | None,
    *,
    status: str = "scheduled",
    home: int = 1,
    away: int = 2,
) -> dict[str, Any]:
    return {
        "id": game_id,
        "date": date,
        "status": status,
        "homeId": home,
        "awayId": away,
    }


def _write_rounds(path: Path, rounds: dict[int, list[dict[str, Any]]]) -> None:
    _write_gzip_json(
        path, [{"id": round_id, "games": games} for round_id, games in rounds.items()]
    )


def test_load_player_results_combines_rounds(tmp_path: Path) -> None:
    # As text, "10" sorts before "2"; the output must sort by round number.
    _write_gzip_json(
        tmp_path / "10.json.gz",
        {"players": [_player(7, 300, 10, squad_id=3, minutes=45, points=1)]},
    )
    _write_gzip_json(
        tmp_path / "2.json.gz",
        {
            "players": [
                _player(8, 200, 2, points=5),
                _player(7, 200, 2, minutes=0, points=0),
            ]
        },
    )

    expected = pd.DataFrame(
        {
            "player_id": [7, 8, 7],
            "game_id": [200, 200, 300],
            "squad_id": [1, 1, 3],
            "round_id": [2, 2, 10],
            "minutes_played": [0, 90, 45],
            "points": [0, 5, 1],
        }
    ).astype("int64")

    pd.testing.assert_frame_equal(load_player_results(tmp_path), expected)


def test_load_player_results_rejects_duplicate_records(tmp_path: Path) -> None:
    _write_gzip_json(tmp_path / "1.json.gz", {"players": [_player(7, 200, 1)]})
    _write_gzip_json(tmp_path / "2.json.gz", {"players": [_player(7, 200, 1)]})

    with pytest.raises(ValueError, match="duplicate"):
        load_player_results(tmp_path)


def test_load_player_results_rejects_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_player_results(tmp_path)


def test_load_fixtures_converts_kickoffs_to_utc(tmp_path: Path) -> None:
    path = tmp_path / "rounds.json.gz"
    _write_rounds(
        path,
        {
            1: [
                _game(200, "2026-11-07T15:00:00+00:00"),  # GMT: 15:00 UTC
                _game(100, "2026-10-03T15:00:00+01:00"),  # BST: 14:00 UTC
            ]
        },
    )

    fixtures = load_fixtures(path)

    assert list(fixtures["game_id"]) == [100, 200]
    assert list(fixtures["kickoff"]) == [
        pd.Timestamp("2026-10-03 14:00", tz="UTC"),
        pd.Timestamp("2026-11-07 15:00", tz="UTC"),
    ]
    assert str(fixtures["kickoff"].dt.tz) == "UTC"


def test_load_fixtures_maps_round_and_squad_ids(tmp_path: Path) -> None:
    path = tmp_path / "rounds.json.gz"
    _write_rounds(
        path,
        {
            3: [_game(100, "2026-10-03T15:00:00+01:00", home=5, away=6)],
            4: [_game(200, "2026-10-10T15:00:00+01:00", home=7, away=8)],
        },
    )

    fixtures = load_fixtures(path)

    assert list(fixtures["round_id"]) == [3, 4]
    assert list(fixtures["home_squad_id"]) == [5, 7]
    assert list(fixtures["away_squad_id"]) == [6, 8]


def test_load_fixtures_keeps_status(tmp_path: Path) -> None:
    path = tmp_path / "rounds.json.gz"
    _write_rounds(
        path,
        {
            1: [
                _game(200, "2026-11-07T15:00:00+00:00", status="postponed"),
                _game(100, "2026-10-03T15:00:00+01:00"),
            ]
        },
    )

    fixtures = load_fixtures(path)

    assert list(fixtures["status"]) == ["scheduled", "postponed"]


def test_load_fixtures_rejects_duplicate_game_ids(tmp_path: Path) -> None:
    path = tmp_path / "rounds.json.gz"
    _write_rounds(
        path,
        {
            1: [_game(100, "2026-10-03T15:00:00+01:00")],
            2: [_game(100, "2026-10-10T15:00:00+00:00")],
        },
    )

    with pytest.raises(ValueError, match="duplicate"):
        load_fixtures(path)


def test_load_fixtures_rejects_missing_kickoff(tmp_path: Path) -> None:
    path = tmp_path / "rounds.json.gz"
    _write_rounds(path, {1: [_game(100, None)]})

    with pytest.raises(ValueError, match="kickoff"):
        load_fixtures(path)
