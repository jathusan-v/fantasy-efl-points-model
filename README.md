# Fantasy EFL Points Model

[![CI](https://github.com/jathusan-v/fantasy-efl-points-model/actions/workflows/ci.yml/badge.svg)](https://github.com/jathusan-v/fantasy-efl-points-model/actions/workflows/ci.yml)

A walk-forward model of expected Fantasy EFL points per player per fixture across the Championship, League One and League Two. Event counts (goals, assists, minutes, defensive actions, goals conceded) are modelled as Poisson or negative binomial counts and converted to points using the game's scoring rules. The model is evaluated against baselines, against official points and on a live forward test.

> **Status:** in development. The repository does not yet produce model-based projections.

## Data Policy

This repository contains no third-party data: no match data, no data from the Fantasy EFL API and no betting odds. Real data stays on the author's machine, and `.gitignore` plus a pre-commit hook prevent data files from being committed.

The test suite needs no private data, so anyone can run it. Results that depend on real data cannot be reproduced from this repository alone.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pre-commit install
uv run pytest
```

## Licence

MIT; see [LICENSE](LICENSE). This project is not affiliated with the EFL or Fantasy EFL.
