"""Write reproducible prediction logs and return their SHA-256 hashes."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import pandas as pd

_KEY: Final = ("game_id", "player_id")

_LOG_COLUMNS: Final = (
    "model_version",
    "as_of",
    "round_id",
    "game_id",
    "player_id",
    "expected_points",
    "n_appearances",
)


def write_prediction_log(
    predictions: pd.DataFrame,
    path: Path,
    *,
    model_version: str,
    as_of: datetime,
    round_id: int,
) -> str:
    """Write predictions as a byte-reproducible CSV and return its SHA-256.

    Rows are sorted by game and player, ``expected_points`` is written to four decimal
    places and `as_of` is written in UTC, so identical predictions always produce
    identical bytes.

    Parameters
    ----------
    predictions : pd.DataFrame
        Predictions with ``game_id``, ``player_id``, ``expected_points`` and
        ``n_appearances``.
    path : Path
        Destination of the CSV file. An existing file is overwritten.
    model_version : str
        Identifier of the model that produced the predictions.
    as_of : datetime
        Timezone-aware information cutoff used for the predictions.
    round_id : int
        Gameweek the predictions are for.

    Returns
    -------
    str
        Hexadecimal SHA-256 of the written file.

    Raises
    ------
    ValueError
        If `as_of` is naive, a ``(game_id, player_id)`` pair is duplicated, or a
        prediction is missing.
    """
    if as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    if predictions.duplicated(list(_KEY)).any():
        raise ValueError("duplicate (game_id, player_id) predictions")
    if predictions["expected_points"].isna().any():
        raise ValueError("missing expected_points")

    log = predictions.assign(
        model_version=model_version,
        as_of=as_of.astimezone(UTC).isoformat(),
        round_id=round_id,
    )
    log = log.loc[:, list(_LOG_COLUMNS)].sort_values(list(_KEY))
    log.to_csv(path, index=False, float_format="%.4f", lineterminator="\n")

    return hashlib.sha256(path.read_bytes()).hexdigest()
