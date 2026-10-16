"""Tests for reproducible prediction logs."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from efl_points.live.prediction_log import write_prediction_log

AS_OF = datetime(2026, 10, 14, 23, 0, tzinfo=UTC)


def _predictions(*rows: tuple[int, int, float, int]) -> pd.DataFrame:
    """Rows: game_id, player_id, expected_points, n_appearances."""
    return pd.DataFrame(
        rows, columns=["game_id", "player_id", "expected_points", "n_appearances"]
    ).astype(
        {
            "game_id": "int64",
            "player_id": "int64",
            "expected_points": "float64",
            "n_appearances": "int64",
        }
    )


def _write(predictions: pd.DataFrame, path: Path, as_of: datetime = AS_OF) -> str:
    return write_prediction_log(
        predictions, path, model_version="b0-test", as_of=as_of, round_id=10
    )


def test_write_prediction_log_writes_expected_text(tmp_path: Path) -> None:
    path = tmp_path / "log.csv"
    # Midnight BST on 15 October is 23:00 UTC on 14 October.
    london_as_of = datetime(2026, 10, 15, 0, 0, tzinfo=ZoneInfo("Europe/London"))

    _write(_predictions((200, 8, 4.0, 5), (100, 7, 2 / 3, 3)), path, london_as_of)

    assert path.read_text(encoding="utf-8") == (
        "model_version,as_of,round_id,game_id,player_id,expected_points,n_appearances\n"
        "b0-test,2026-10-14T23:00:00+00:00,10,100,7,0.6667,3\n"
        "b0-test,2026-10-14T23:00:00+00:00,10,200,8,4.0000,5\n"
    )


def test_write_prediction_log_is_byte_identical_across_runs(tmp_path: Path) -> None:
    predictions = _predictions((200, 8, 4.0, 5), (100, 7, 2 / 3, 3))

    _write(predictions, tmp_path / "first.csv")
    _write(predictions, tmp_path / "second.csv")

    assert (tmp_path / "first.csv").read_bytes() == (
        tmp_path / "second.csv"
    ).read_bytes()


def test_write_prediction_log_sorts_rows_regardless_of_input_order(
    tmp_path: Path,
) -> None:
    ordered = _predictions((100, 7, 1.0, 1), (100, 8, 2.0, 2), (200, 6, 3.0, 3))
    shuffled = ordered.iloc[[2, 0, 1]]

    _write(ordered, tmp_path / "ordered.csv")
    _write(shuffled, tmp_path / "shuffled.csv")

    assert (tmp_path / "ordered.csv").read_bytes() == (
        tmp_path / "shuffled.csv"
    ).read_bytes()


def test_write_prediction_log_returns_sha256_of_file(tmp_path: Path) -> None:
    path = tmp_path / "log.csv"

    returned = _write(_predictions((100, 7, 2 / 3, 3)), path)

    assert returned == hashlib.sha256(path.read_bytes()).hexdigest()


def test_write_prediction_log_rejects_naive_as_of(tmp_path: Path) -> None:
    path = tmp_path / "log.csv"
    naive = datetime(2026, 10, 14, 23, 0)  # noqa: DTZ001

    with pytest.raises(ValueError, match="timezone-aware"):
        _write(_predictions((100, 7, 4.0, 5)), path, naive)

    assert not path.exists()


def test_write_prediction_log_rejects_duplicate_predictions(tmp_path: Path) -> None:
    path = tmp_path / "log.csv"

    with pytest.raises(ValueError, match="duplicate"):
        _write(_predictions((100, 7, 4.0, 5), (100, 7, 6.0, 3)), path)

    assert not path.exists()


def test_write_prediction_log_rejects_missing_prediction(tmp_path: Path) -> None:
    path = tmp_path / "log.csv"

    with pytest.raises(ValueError, match="missing"):
        _write(_predictions((100, 7, float("nan"), 0)), path)

    assert not path.exists()
