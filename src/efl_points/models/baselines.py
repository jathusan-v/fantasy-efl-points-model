"""Simple historical-points baselines."""

from datetime import datetime
from typing import Final

import pandas as pd

_OUTPUT_COLUMNS: Final = ("game_id", "player_id", "expected_points", "n_appearances")


def b0_predictions(
    results: pd.DataFrame,
    fixtures: pd.DataFrame,
    targets: pd.DataFrame,
    as_of: datetime,
    k: int = 5,
) -> pd.DataFrame:
    """Predict each player's points as the mean of his latest k appearances.

    Parameters
    ----------
    results : pd.DataFrame
        Player results with ``player_id``, ``game_id``, ``squad_id``,
        ``minutes_played`` and ``points``.
    fixtures : pd.DataFrame
        Fixtures with ``game_id`` and UTC ``kickoff``, used to date results.
    targets : pd.DataFrame
        Fixtures to predict, with ``game_id``, ``home_squad_id`` and ``away_squad_id``.
    as_of : datetime
        Timezone-aware information cutoff. Only results kicking off strictly before it
        are used.
    k : int, default 5
        Maximum number of recent appearances to average.

    Returns
    -------
    pd.DataFrame
        One row per target fixture and player, sorted by game and player.

    Raises
    ------
    ValueError
        If `as_of` is naive, `k` is not positive, or a result has no fixture.
    """
    if as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    if k < 1:
        raise ValueError("k must be at least 1")

    dated = results.merge(
        fixtures[["game_id", "kickoff"]],
        on="game_id",
        how="left",
        validate="many_to_one",
    )

    if dated["kickoff"].isna().any():
        raise ValueError("result without a fixture kickoff")

    known = dated.loc[dated["kickoff"] < as_of].sort_values(
        ["player_id", "kickoff", "game_id"], ascending=[True, False, False]
    )
    appearances = known.loc[known["minutes_played"] > 0]
    if appearances.empty:
        return pd.DataFrame(columns=list(_OUTPUT_COLUMNS))

    # Squad comes from the latest record of any kind, so a new signing who has only been
    # an unused substitute is still assigned to his new club.
    squads = known.groupby("player_id", as_index=False)["squad_id"].first()
    form = (
        appearances.groupby("player_id")
        .head(k)
        .groupby("player_id", as_index=False)
        .agg(expected_points=("points", "mean"), n_appearances=("points", "size"))
    )
    players = form.merge(squads, on="player_id", validate="one_to_one")

    target_squads = pd.concat(
        [
            targets[["game_id", "home_squad_id"]].rename(
                columns={"home_squad_id": "squad_id"}
            ),
            targets[["game_id", "away_squad_id"]].rename(
                columns={"away_squad_id": "squad_id"}
            ),
        ],
        ignore_index=True,
    )
    predictions = target_squads.merge(players, on="squad_id")

    return predictions.loc[:, list(_OUTPUT_COLUMNS)].sort_values(
        ["game_id", "player_id"], ignore_index=True
    )
