# plan-redline core

## Purpose
Render a plan into an operator-facing proposal that maps requests to deliverables, labels operator-picked (`P`) and agent-defaulted (`D`) decisions with stable IDs, accepts terse ID-referenced feedback, and folds accepted changes back into the plan without changing its role as source of truth.

## Inputs and prerequisites
- Optional `--plan <path>` and optional prior proposal locator.
- A canonical plan (`plan.md`, `master_plan.md`, or the plan authored in the current session).
- Read/write access to the plan and a provider renderer capable of producing a standalone review surface.
- The house style reference at `skills/plan-redline/reference-proposal.html` when present.

Bare invocation never blocks: resolve the current-session plan first, then the cwd canonical plan. If neither exists, report that in one line and stop.

## Procedure
1. Read the plan and available planning conversation. Build a decision inventory: `P` for explicit operator choices and `D` for agent defaults. When conversation state is unavailable, use the plan's canonical Decision Inventory; if none exists, derive only `D` items from Key Design Decisions and Open Questions and persist them immediately.
2. Preserve ID stability across every publication. Append new IDs; mark reversed entries `changed <date>`; never renumber or delete IDs.
3. Render these sections in order, adapting depth but never inventing filler: header; What I heard; optional Why this shape; phase timeline with ?Afterwards? commands; operator choices; agent defaults with what/why/tweak; Not in v1; risks; feedback grammar and source paths.
4. Use a token-driven light/dark HTML design with accessible semantic structure, stable IDs, real content, and no placeholders. The provider wrapper selects the publication mechanism.
5. At every publication, write or refresh: (a) `### Decision Inventory` in the plan Appendix with `ID | P/D | choice | status`; and (b) `Proposal: <stable locator>` in `## 1. What This Is`. The provider wrapper returns a URL when available or a repository-relative standalone HTML path otherwise.
6. Report the locator, a 5?8 line guide, the 2?3 most important D-IDs, and the reply grammar. Do not paste the full proposal into chat.
7. On feedback, detect populated Issue fields and warn about repo-sync N+1 edits; apply the smallest plan edits; update inventory status; ask at most one batched clarification; republish the same target; report one line per applied change. Silence means the plan stands.

## Output contract
- A stable proposal URL or standalone HTML file.
- Updated plan Decision Inventory and Proposal locator.
- Feedback grammar such as `D1 -> band [10,90]`.
- On republish, the same locator and incremented publication label/version.

## Gates and halt conditions
- The plan remains the source of truth; the proposal is only a view.
- Every D item includes what, why, and a tweak axis.
- IDs are append-only and stable.
- No placeholder or fabricated operator choices.
- Missing publication capability is non-blocking only when a standalone HTML fallback can be written; otherwise report the unsupported capability explicitly.
- External issue mutations follow workspace git/GitHub safety rules and require repo-sync after post-sync plan changes.
