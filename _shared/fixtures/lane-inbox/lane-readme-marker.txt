Passing Notes project: `demo-proj`

# Lane notes: how the work lanes talk to each other

Synthetic lane README for the lane inbox hook tests, shaped like a real project's
`docs/lanes/README.md`: a lane table whose ids sit in backticks, and an
`operator` row that is never a lane.

## The lanes

| Lane id | Window | Owns |
|---|---|---|
| `central` | The central window (Claude) | The queue; merges to main |
| `art-lane` | The art lane (Claude) | Image generation only |
| `combat-design` | The combat-design lane (Codex) | Combat seeds by hand-off |
| `operator` | You | Every decision. A note never stands in for your word |

## Rules every lane keeps

| Rule | Why |
|---|---|
| `not-a-lane` | This second table is not the lane table |
