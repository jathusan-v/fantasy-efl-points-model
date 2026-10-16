"""Generate B0 predictions for one gameweek and write the prediction log."""

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from efl_points.data.fantasy import load_fixtures, load_player_results
from efl_points.gameweeks import gameweek_window
from efl_points.live.prediction_log import write_prediction_log
from efl_points.models.baselines import b0_predictions

MODEL_VERSION = "b0-official-k5"
K = 5


def _aware_datetime(text: str) -> datetime:
    """Parse an ISO datetime argument, rejecting naive values."""
    value = datetime.fromisoformat(text)
    if value.utcoffset() is None:
        raise argparse.ArgumentTypeError("datetime must include a UTC offset")
    return value


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--kickoff-after", type=_aware_datetime, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def _exclusion_reason(
    kickoff: pd.Timestamp, status: str, kickoff_after: datetime
) -> str | None:
    """Return why a fixture is not a target, or None if it is one."""
    reasons = []
    if kickoff <= kickoff_after:
        reasons.append("kicks off at or before kickoff_after")
    if status != "scheduled":
        reasons.append(f"status is {status!r}")
    return "; ".join(reasons) or None


def main(argv: list[str] | None = None) -> None:
    """Run B0 for one gameweek and print a summary of the run."""
    args = _parse_args(argv)

    results = load_player_results(args.snapshot / "live_scores")
    fixtures = load_fixtures(args.snapshot / "rounds.json.gz")

    round_fixtures = fixtures.loc[fixtures["round_id"] == args.round]
    if round_fixtures.empty:
        raise SystemExit(f"no fixtures found for round {args.round}")

    earliest_kickoff = round_fixtures["kickoff"].min().to_pydatetime()
    as_of = gameweek_window(earliest_kickoff).start

    reasons = [
        _exclusion_reason(fixture.kickoff, fixture.status, args.kickoff_after)
        for fixture in round_fixtures.itertuples(index=False)
    ]
    targets = round_fixtures.loc[[reason is None for reason in reasons]]
    if targets.empty:
        raise SystemExit(f"no target fixtures in round {args.round}")

    predictions = b0_predictions(results, fixtures, targets, as_of, k=K)
    if predictions.empty:
        raise SystemExit("B0 produced no predictions")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    digest = write_prediction_log(
        predictions,
        args.out,
        model_version=MODEL_VERSION,
        as_of=as_of,
        round_id=args.round,
    )

    # Reindexing on the targets counts a fixture with no predictions as 0.
    players = (
        predictions.groupby("game_id").size().reindex(targets["game_id"], fill_value=0)
    )

    print(f"model:            {MODEL_VERSION}")
    print(f"round:            {args.round}")
    print(f"snapshot:         {args.snapshot}")
    print(f"as_of:            {as_of.astimezone(UTC).isoformat()}")
    print(f"kickoff_after:    {args.kickoff_after.astimezone(UTC).isoformat()}")
    print(f"round fixtures:   {len(round_fixtures)}")
    print(f"target fixtures:  {len(targets)}")
    for fixture, reason in zip(
        round_fixtures.itertuples(index=False), reasons, strict=True
    ):
        if reason is not None:
            print(
                f"  excluded {fixture.game_id} "
                f"({fixture.kickoff.isoformat()}, {fixture.status}): {reason}"
            )
    print(f"prediction rows:  {len(predictions)}")
    print(f"players/fixture:  min={players.min()}, max={players.max()}")
    if (players == 0).any():
        print(f"  no predictions: {players.index[players == 0].tolist()}")
    print(f"output:           {args.out}")
    print(f"sha256:           {digest}")


if __name__ == "__main__":
    main()
