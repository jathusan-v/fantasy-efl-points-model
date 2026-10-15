# Fantasy EFL scoring rules

Source: https://fantasy.efl.com/help/game-guidelines, retrieved 13 Oct 2026. Season 2026/27.

## Official rules (verbatim)

Players and clubs will be awarded points based on their actual performances during the 2026/2027 EFL season with players scoring differently depending on their position outlined in the tables below:

### All players

| Action | Points |
| --- | --- |
| Appearance (up to 59 minutes played) | +1 |
| Appearance (60+ minutes played) | +2 |
| Assist | +3 |
| Hat-trick (3 or more goals scored) | +5 |
| Missed penalty | -3 |
| Own goal | -3 |
| Yellow card | -1 |
| Red card* | -3 |

\*goals conceded after a player is sent off count towards clean sheet loss & goals conceded

### Goalkeepers

| Action | Points |
| --- | --- |
| Every 3 saves | +2 |
| Penalty saved | +5 |
| Goal scored (excl. own goals) | +10 |

### Goalkeepers & Defenders

| Action | Points |
| --- | --- |
| Clean sheet (must have played 60+ minutes) | +5 |
| Every 2 goals conceded | -1 |

### Defenders

| Action | Points |
| --- | --- |
| Every 4 clearances | +1 |
| Every 2 blocks | +1 |
| Every 2 tackles | +1 |
| Goal scored (excl. own goals) | +7 |

### Midfielders

| Action | Points |
| --- | --- |
| Every interception | +2 |
| Goal scored (excl. own goals) | +6 |

### Midfielders & Forwards

| Action | Points |
| --- | --- |
| Every 2 key passes | +1 |
| Every shot on target | +1 |

### Forwards

| Action | Points |
| --- | --- |
| Goal scored (excl. own goals) | +5 |

### Clubs

Clubs will score points based on the following metrics:

| Action | Points |
| --- | --- |
| Win | +5 |
| Draw | +3 |
| Away win | +2 |
| Clean sheet | +2 |
| 2+ goals scored | +2 |
| 4+ goals scored | +2 |

## Player scoring components

Club scoring is out of scope for v1.

| Component | Positions | Points | Type | API field |
|---|---|---|---|---|
| Appearance (up to 59 minutes played) | All | +1 | threshold | derived from `minutesPlayed` |
| Appearance (60+ minutes played) | All | +2 | threshold | derived from `minutesPlayed` |
| Goal | GK / DEF / MID / FWD | +10 / +7 / +6 / +5 | linear | `goalsScored` |
| Assist | All | +3 | linear | `assists` |
| Hat-trick | All | +5 | threshold | derived: `goalsScored` >= 3 (cross-check `hatTricks`) |
| Missed penalty | All | -3 | linear | `penaltyMisses` |
| Own goal | All | -3 | linear | `ownGoals` |
| Yellow card | All | -1 | linear | `yellowCards` |
| Red card | All | -3 | linear | `redCards` |
| Saves | GK | +2 per 3 | floor | `saves` |
| Penalty saved | GK | +5 | linear | `penaltySaves` |
| Clean sheet | GK, DEF | +5 | threshold | derived: `goalsConceded` = 0 and `minutesPlayed` >= 60 (cross-check `cleanSheet`) |
| Goals conceded | GK, DEF | -1 per 2 | floor | `goalsConceded` |
| Clearances | DEF | +1 per 4 | floor | `clearances` |
| Blocks | DEF | +1 per 2 | floor | `blocks` |
| Tackles | DEF | +1 per 2 | floor | `tackles` |
| Interceptions | MID | +2 each | linear | `interceptions` |
| Key passes | MID, FWD | +1 per 2 | floor | `keyPasses` |
| Shots on target | MID, FWD | +1 each | linear | `shotsOnTarget` |

Types:
- **linear**: the same points for every event.
- **floor**: points for each completed group of N events.
- **threshold**: points only if a condition on the match holds.

## Interpretations to verify

Expectations were written before checking. Spot checks compare individual records against the published rules; full verification comes from the reconstruction test, which recomputes points for every record.

| # | Question | Expectation | Finding | Status | Evidence |
|---|---|---|---|---|---|
| 1 | Is a 60+ minute appearance worth +2 in total, or +1 plus +2? | +2 in total | +2 in total | spot-checked | Marriott |
| 2 | Do goals conceded count only while the player is on the pitch? | Yes | Yes, plus any goals conceded after the player is sent off | spot-checked | Buyabu (rule) / Tilt (red-card exception) |
| 3 | Do goals-conceded deductions require 60+ minutes? | No | No | spot-checked | Johnston |
| 4 | Is a second-yellow dismissal -1, -1, -3 or just -3? | -3 | -3 | spot-checked | Randell |
| 5 | Is a hat-trick 3 × goal points + 5? | Yes | Yes | spot-checked | Marriott |
| 6 | Does a penalty save also count towards saves? | Yes | Yes | spot-checked | Lo-Tutala |
| 7 | Does a goal also count as a shot on target? | Yes | Yes; own goals excluded | spot-checked | Marriott |
| 8 | Does an assist also count as a key pass? | Yes | Yes. Note: major data providers usually define key passes to *exclude* assists | spot-checked | Azaz |
| 9 | Does "tackles" mean all tackles or tackles won? | All tackles | All tackles | spot-checked | Neumann |
| 10 | Does a saved penalty count as a missed penalty for the taker? | Yes | Yes, and scoring the rebound does not cancel it | spot-checked | Drinan |
| 11 | Do stoppage-time minutes count towards the 60-minute threshold? | No | No | spot-checked | Mlacic |
| 12 | Does a team-mate's own goal count against the defence? | Yes | Yes | spot-checked | Pollock / Ravaglia |
| 13 | How are minutes recorded for a substitute who enters during stoppage time, and is the appearance point still awarded? | 1 minute, +1 appearance | 1 minute, +1 appearance. Minutes appear to be max(1, 90 - entry minute) | spot-checked | Akachukwu |

### Decisive examples

Each example tests several rules at once. Records list every non-zero count; anything not listed is zero.

| Player | Position | Record | Arithmetic | Points | IDs |
|---|---|---|---|---|---|
| Marriott | FWD | 65 min, 3 goals (hat-trick), 3 shots on target, 2 key passes | 2 + 3×5 + 5 + 3×1 + ⌊2/2⌋ | 26 | GW1, gameId 2647813, playerId 160996 |
| Buyabu | DEF | 64 min (subbed off), 1 yellow, 1 tackle; team's only goal conceded at 88', after he left, so clean sheet | 2 - 1 + ⌊1/2⌋ + 5 | 6 | GW3, gameId 2648386, playerId 601496 |
| Tilt | DEF | 83 min (sent off), 1 goal conceded before dismissal and 1 after, 6 clearances, 1 block, 1 tackle | 2 - 3 - ⌊2/2⌋ + ⌊6/4⌋ + ⌊1/2⌋ + ⌊1/2⌋ | -1 | GW3, gameId 2647832, playerId 210834 |
| Johnston | DEF | 45 min (subbed off), 2 goals conceded, 2 clearances | 1 - ⌊2/2⌋ + ⌊2/4⌋ | 0 | GW3, gameId 2647279, playerId 511066 |
| Randell | MID | 36 min (yellow at 23', second yellow at 36') | 1 - 3 | -2 | GW1, gameId 2647252, playerId 442246 |
| Lo-Tutala | GK | 90 min, 3 saves incl. 1 penalty save, 3 goals conceded | 2 + 2×⌊3/3⌋ + 5 - ⌊3/2⌋ | 8 | GW4, gameId 2648412, playerId 444307 |
| Azaz | MID | 89 min (subbed off), 1 assist, 1 interception; API: `keyPasses`=4, and a public match centre lists 4 chances created incl. the assist | 2 + 3 + 2 + ⌊4/2⌋ | 9 | GW2, gameId 2647269, playerId 232416 |
| Neumann | DEF | 90 min, clean sheet, 7 clearances, 2 tackles (1 won, per a public match centre) | 2 + 5 + ⌊7/4⌋ + ⌊2/2⌋ | 9 | GW1, gameId 2647257, playerId 229594 |
| Drinan | FWD | 90 min, 3 goals (hat-trick), 4 shots on target, 1 key pass; penalty saved before he scored the rebound | 2 + 3×5 + 5 + 4 + ⌊1/2⌋ - 3 | 23 | GW4, gameId 2648412, playerId 428683 |
| Mlacic | DEF | 59 min (subbed on at 31' and finished the match), 0 goals conceded while on pitch, 6 clearances, 1 tackle; match lasted to at least 94' (public match centre has an event at 94') | 1 + ⌊6/4⌋ + ⌊1/2⌋ | 2 | GW3, gameId 2647292, playerId 685714 |
| Pollock | DEF | 90 min, 1 own goal (so 1 goal conceded), 7 clearances, 2 blocks, 1 tackle | 2 - 3 - ⌊1/2⌋ + ⌊7/4⌋ + ⌊2/2⌋ + ⌊1/2⌋ | 1 | GW3, gameId 2647283, playerId 467311 |
| Ravaglia | GK | 90 min, team-mate Pollock's own goal was the only concession, so no clean sheet | 2 | 2 | GW3, gameId 2647283, playerId 235879 |
| Akachukwu | MID | 1 min (subbed on at 90+5'); API: `minutesPlayed`=1 | 1 | 1 | GW2, gameId 2647269, playerId 587645 |
