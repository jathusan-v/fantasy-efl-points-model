"""Load Fantasy EFL snapshot files into tidy tables."""

import gzip
import json
from pathlib import Path
from typing import Any, Final

import pandas as pd

_PLAYER_COLUMNS: Final = {
    "playerId": "player_id",
    "gameId": "game_id",
    "squadId": "squad_id",
    "roundId": "round_id",
    "minutesPlayed": "minutes_played",
    "points": "points",
}

_FIXTURE_COLUMNS: Final = (
    "game_id",
    "round_id",
    "kickoff",
    "home_squad_id",
    "away_squad_id",
    "status",
)

_FIXTURE_INTEGER_COLUMNS: Final = (
    "game_id",
    "round_id",
    "home_squad_id",
    "away_squad_id",
)


def _read_gzip_json(path: Path) -> Any:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def load_player_results(live_scores_dir: Path) -> pd.DataFrame:
    """Load per-fixture player results from live-score snapshot files.

    Parameters
    ----------
    live_scores_dir : Path
        Directory containing one ``<round>.json.gz`` file per gameweek.

    Returns
    -------
    pd.DataFrame
        One row per player per fixture, sorted by round, game and player.

    Raises
    ------
    FileNotFoundError
        If the directory contains no ``.json.gz`` files.
    ValueError
        If a (player_id, game_id) pair appears more than once.
    """
    paths = sorted(live_scores_dir.glob("*.json.gz"))
    if not paths:
        raise FileNotFoundError(f"no .json.gz files in {live_scores_dir}")

    records = [
        {target: player[source] for source, target in _PLAYER_COLUMNS.items()}
        for path in paths
        for player in _read_gzip_json(path)["players"]
    ]
    results = pd.DataFrame(records, columns=list(_PLAYER_COLUMNS.values()))
    results = results.astype("int64")

    duplicated = results.duplicated(["player_id", "game_id"], keep=False)
    if duplicated.any():
        pairs = results.loc[duplicated, ["player_id", "game_id"]].drop_duplicates()
        raise ValueError(
            f"duplicate (player_id, game_id) pairs: {pairs.head().values.tolist()}"
        )

    return results.sort_values(["round_id", "game_id", "player_id"], ignore_index=True)


def load_fixtures(rounds_path: Path) -> pd.DataFrame:
    """Load every fixture with a timezone-aware UTC kickoff.

    Parameters
    ----------
    rounds_path : Path
        Path to the gzipped ``rounds.json`` snapshot.

    Returns
    -------
    pd.DataFrame
        One row per fixture, sorted by kickoff and game.

    Raises
    ------
    ValueError
        If a game_id appears more than once or a fixture has no kickoff time.
    """
    records = [
        {
            "game_id": game["id"],
            "round_id": round_record["id"],
            "kickoff": game["date"],
            "home_squad_id": game["homeId"],
            "away_squad_id": game["awayId"],
            "status": game["status"],
        }
        for round_record in _read_gzip_json(rounds_path)
        for game in round_record["games"]
    ]
    fixtures = pd.DataFrame(
        records,
        columns=list(_FIXTURE_COLUMNS),
    )
    fixtures = fixtures.astype(dict.fromkeys(_FIXTURE_INTEGER_COLUMNS, "int64"))
    fixtures["kickoff"] = pd.to_datetime(fixtures["kickoff"], utc=True)

    if fixtures["kickoff"].isna().any():
        raise ValueError("fixture without a kickoff time")

    duplicated = fixtures.duplicated("game_id", keep=False)
    if duplicated.any():
        game_ids = sorted(fixtures.loc[duplicated, "game_id"].unique().tolist())
        raise ValueError(f"duplicate game_ids: {game_ids[:5]}")

    return fixtures.sort_values(["kickoff", "game_id"], ignore_index=True)
