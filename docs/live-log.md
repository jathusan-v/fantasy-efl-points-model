# Live forward test

Predictions are committed as a SHA-256 hash before the first counted kickoff of each gameweek, and the predictions file itself is revealed after the gameweek is complete. The validity rules are in [decisions.md](decisions.md) ("Live-log validity").

## Before each gameweek

1. Take a snapshot of the Fantasy EFL data (private collector; raw data is not published).
2. Run B0 twice on the snapshot and confirm both runs give the same hash: `python -m efl_points.live.run_b0 --snapshot <dir> --round NN --kickoff-after <time> --out <csv>`
3. Check the run summary: information cutoff, excluded fixtures and why, players per fixture.
4. Write `predictions/gwNN.sha256` and verify it against the CSV with `shasum -c` before committing.
5. Commit and push the hash file; the commit message records the snapshot and arguments. The CI run's timestamp must come before the first counted kickoff.
6. Back up the predictions file and snapshot off-machine.

## After the gameweek is complete

1. Commit the predictions file to `predictions/`.
2. Confirm it matches the committed hash.

## Verifying a revealed gameweek

From `predictions/` in a clone of this repository:

```bash
shasum -a 256 -c gwNN.sha256
```

`OK` means the file is byte-identical to the one whose hash was committed before the gameweek started. The commit dates and CI runs on GitHub show when each hash was committed.
