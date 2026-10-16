# Decisions

## 2026-10-16: Information cutoff

**Decision.** `as_of` is the start of the gameweek window, Thursday 00:00 Europe/London, stored in UTC (`gameweeks.gameweek_window`).
**Why.** It never falls in a clock-change hour, and no matches are played between it and the first kickoff.
**Open.** v2 status features may need `as_of` = snapshot retrieval time (before the first kickoff); to be decided before those features exist.

## 2026-10-16: Live B0

**Decision.** Live B0 = mean official points over a player's latest five appearances (`minutesPlayed > 0`) before `as_of`; squad taken from his latest record before `as_of`. Model version `b0-official-k5`.
**Why.** Uses only the game's own data, available before the historical pipeline exists.

## 2026-10-16: Live-log validity

**Decision.**
1. A prediction counts in the live evaluation only if its fixture kicks off after the CI timestamp of the commit containing the log's SHA-256.
2. Fixtures postponed after the commit have no result and drop out of the evaluation.
3. Target fixtures are chosen using fixture status from a snapshot taken after `as_of`. Status selects which fixtures to predict; it is never a model input.
**Why.** Rules based only on timestamps and outcomes, fixed before results are known, leave no room for selecting after seeing results.
**Consequence.** GW10's Thursday 15 October fixture is excluded (hash committed on 16 October).
