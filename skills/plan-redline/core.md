# plan-redline core

## Purpose
Render a plan into an operator-facing proposal that maps requests to deliverables, labels operator-picked (`P`) and agent-defaulted (`D`) decisions with stable IDs, accepts terse ID-referenced feedback, and folds accepted changes back into the plan without changing its role as source of truth.

## Inputs and prerequisites
- Optional `--plan <path>` and optional prior proposal locator.
- Optional `--local-only` (passed by orchestrating callers such as `/plan-expedite`): never publish or update a hosted copy; publish only the standalone HTML fallback. A recorded hosted `Proposal:` locator is treated as a locator this host cannot update (gates below) and reported as stale.
- A canonical plan (`plan.md`, `master_plan.md`, or the plan authored in the current session).
- Read/write access to the plan and a provider renderer capable of producing a standalone review surface.
- The house style reference `reference-proposal.html` beside this core when present; the fixed strings in step 4 apply either way.
- Pipeline position: after `/plan-review` and before `/plan-wrap` (order owned by the workspace plan-and-issue-flow rule). This skill does not verify that a review ran.

Bare invocation never blocks: resolve the current-session plan first, then the cwd canonical plan. If neither exists, report that in one line and stop without writing.

## Procedure
1. Read the plan and available planning conversation. Build a decision inventory: `P` for explicit operator choices and `D` for agent defaults. When conversation state is unavailable, use the plan's canonical Decision Inventory; if none exists, derive only `D` items from Key Design Decisions and Open Questions and persist them immediately. When conversation state is unavailable and the plan has no Decision Inventory but records decisions with a provenance column (for example plan-feature's Design Decisions table), map that column instead of deriving `D`-only items: `operator` becomes `P`; `agent default` or `inference` becomes `D`, with each inference-derived item flagged `(inference)` in its choice text; persist the mapped inventory immediately.
2. Preserve ID stability across every publication. Append new IDs; mark reversed entries `changed <date>`; never renumber or delete IDs. Every other row reads `stands`; publication sets any other incoming status (for example an upstream `proposed`) to `stands`, and the report names each ID it normalized.
3. Render these sections in order, adapting depth but never inventing filler: header; What I heard; optional Why this shape; phase timeline with an `Afterwards:` runnable command per phase; operator choices; agent defaults with what/why/tweak (`Tweak: none recommended` only with a reason); Not in v1; risks; feedback grammar with an ID-referenced example, the note that anything unmentioned lands as written, and source paths.
4. Use a token-driven light/dark HTML design (`prefers-color-scheme: dark` plus `:root[data-theme=...]` overrides) with accessible semantic structure, stable IDs, real content, and no placeholders. Title the page `<project> — proposal`; the header eyebrow includes `awaiting your tweaks`. The provider wrapper selects the publication mechanism.
5. At every publication, write or refresh: (a) `### Decision Inventory` in the plan Appendix with `ID | P/D | choice | status`; and (b) `Proposal: <stable locator>` in `## 1. What This Is`. When no locator is recorded, the provider wrapper returns a URL when available or a repository-relative standalone HTML path otherwise; a recorded locator follows the locator gates below. These two writes and operator-requested tweaks are the only plan edits.
6. Report the locator, a 5-8 line guide, the 2-3 most important D-IDs, the reply grammar, and the next step: `/plan-wrap`, preceded by `/plan-review` if it has not run on this plan. Do not paste the full proposal into chat.
7. On feedback, detect populated Issue fields and warn about repo-sync N+1 edits; apply the smallest plan edits; update inventory status; ask at most one batched clarification; republish the same target; report one line per applied change (`<ID> -> <what changed, where>`) and each item not applied with its reason. Name `/repo-sync` as required when Issue fields are populated, and `/plan-review` then `/plan-wrap` when a wrap already ran and the fold changed plan content materially. Silence means the plan stands.

## Output contract
- A stable proposal URL or standalone HTML file.
- Updated plan Decision Inventory and Proposal locator; no other plan edit except operator-requested tweaks.
- Feedback grammar such as `D1 -> band [10,90]`.
- On republish, the same locator and incremented publication label/version, unless a locator gate below changes the locator.
- A chat report: locator, guide, key D-IDs, reply grammar and next step, plus any normalized status IDs and any locator change; on feedback, one line per change plus required follow-ups.

## Gates and halt conditions
- The plan remains the source of truth; the proposal is only a view.
- Every D item includes what, why, and a tweak axis.
- IDs are append-only and stable.
- No placeholder or fabricated operator choices.
- A recorded `Proposal:` locator takes precedence over the wrapper's default mechanism: republish to it, recovering it from the plan's `Proposal:` line in a new session, and never mint a second hosted copy. Move a recorded repository-relative HTML locator to a hosted surface only when the operator asks.
- Missing publication capability, including a recorded locator this host cannot update, is non-blocking only when a standalone HTML fallback can be written; then update the `Proposal:` line. Otherwise report the unsupported capability explicitly.
- Report every `Proposal:` locator change, in either direction, in the publish or fold report; when the prior locator was hosted, state that the prior copy remains published and is now stale.
- External issue mutations follow workspace git/GitHub safety rules and require repo-sync after post-sync plan changes.
