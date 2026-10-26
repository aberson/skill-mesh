# plan-redline core

## Purpose
Render a plan into an operator-facing proposal that maps requests to deliverables, labels operator-picked (`P`) and agent-defaulted (`D`) decisions with stable IDs, accepts terse ID-referenced feedback, and folds accepted changes back into the plan without changing its role as source of truth.

## Inputs and prerequisites
- Optional `--plan <path>` and optional prior proposal locator.
- Optional `--local-only` (passed by orchestrating callers such as `/plan-expedite`): accepted for compatibility and a no-op, because the standalone HTML file is now the only publication mechanism on every provider (document output contract below).
- A canonical plan (`plan.md`, `master_plan.md`, or the plan authored in the current session).
- Read/write access to the plan and the plan's repository, where the proposal file is written.
- Publication location and locator form are owned by the shared document output contract, `<repo>/_shared/document-output.md`: the proposal is one self-contained HTML file at `docs/plan-redline/<plan-slug>-proposal.html` inside the plan's repository, and the stable locator is that repository-relative path. No provider publishes a hosted copy (an Artifact or any other hosted URL). The plan's repository is the Git toplevel that contains the plan file (`git -C <plan-dir> rev-parse --show-toplevel`), never the cwd or a pinned project; `<plan-slug>` follows the contract's slug rule. When the plan file is outside any Git repository, report that in one line and make no plan edit.
- The house style reference `reference-proposal.html` beside this core when present; the fixed strings in step 4 apply either way.
- Pipeline position: after `/plan-review` and before `/plan-wrap` (order owned by the workspace plan-and-issue-flow rule). This skill does not verify that a review ran.

Bare invocation never blocks: resolve the current-session plan first, then the cwd canonical plan. If neither exists, report that in one line and stop without writing.

## Procedure
1. Read the plan and available planning conversation. Build a decision inventory: `P` for explicit operator choices and `D` for agent defaults. When conversation state is unavailable, use the plan's canonical Decision Inventory; if none exists, derive only `D` items from Key Design Decisions and Open Questions and persist them immediately. When conversation state is unavailable and the plan has no Decision Inventory but records decisions with a provenance column (for example plan-feature's Design Decisions table), map that column instead of deriving `D`-only items: `operator` becomes `P`; `agent default` or `inference` becomes `D`, with each inference-derived item flagged `(inference)` in its choice text; persist the mapped inventory immediately.
2. Preserve ID stability across every publication. Append new IDs; mark reversed entries `changed <date>`; never renumber or delete IDs. Every other row reads `stands`; publication sets any other incoming status (for example an upstream `proposed`) to `stands`, and the report names each ID it normalized.
3. Render these sections in order, adapting depth but never inventing filler: header; What I heard; optional Why this shape; phase timeline with an `Afterwards:` runnable command per phase; operator choices; agent defaults with what/why/tweak (`Tweak: none recommended` only with a reason); Not in v1; risks; feedback grammar with an ID-referenced example, the note that anything unmentioned lands as written, and source paths.
4. Use a token-driven light/dark HTML design (`prefers-color-scheme: dark` plus `:root[data-theme=...]` overrides) with accessible semantic structure, stable IDs, real content, and no placeholders. Title the page `<project> — proposal`; the header eyebrow includes `awaiting your tweaks`. Write the page to `docs/plan-redline/<plan-slug>-proposal.html` in the plan's repository, creating the directory when missing; the provider wrapper supplies only the host's file-write and page-design abstractions, never a different location or a hosted surface.
5. At every publication, write or refresh: (a) `### Decision Inventory` in the plan Appendix with `ID | P/D | choice | status`; and (b) `Proposal: <stable locator>` in `## 1. What This Is`. When no locator is recorded, the locator is the repository-relative path of the file just written; a recorded locator follows the locator gates below. These two writes and operator-requested tweaks are the only plan edits.
6. Report the locator (and that the file is uncommitted), a 5-8 line guide, the 2-3 most important D-IDs, the reply grammar, and the next step: `/plan-wrap`, preceded by `/plan-review` if it has not run on this plan. Do not paste the full proposal into chat.
7. On feedback, detect populated Issue fields and warn about repo-sync N+1 edits; apply the smallest plan edits; update inventory status; ask at most one batched clarification; republish the same target; report one line per applied change (`<ID> -> <what changed, where>`) and each item not applied with its reason. Name `/repo-sync` as required when Issue fields are populated, and `/plan-review` then `/plan-wrap` when a wrap already ran and the fold changed plan content materially. Silence means the plan stands.

## Output contract
- A standalone proposal HTML file at `docs/plan-redline/<plan-slug>-proposal.html` in the plan's repository, uncommitted; the chat report says so, and the file lands with whichever later git step stages `docs/` (repo-update Step 9 when `$STAGE_INCLUDE` covers it, or an operator commit).
- Updated plan Decision Inventory and Proposal locator; no other plan edit except operator-requested tweaks.
- Feedback grammar such as `D1 -> band [10,90]`.
- On republish, the same locator and incremented publication label/version, unless a locator gate below changes the locator.
- A chat report: locator, guide, key D-IDs, reply grammar and next step, plus any normalized status IDs and any locator change; on feedback, one line per change plus required follow-ups.

## Gates and halt conditions
- The plan remains the source of truth; the proposal is only a view.
- Every D item includes what, why, and a tweak axis.
- IDs are append-only and stable.
- No placeholder or fabricated operator choices.
- A recorded repository-relative `Proposal:` locator is the republish target: overwrite that same file, recovering the path from the plan's `Proposal:` line in a new session. A recorded path under another directory (for example the pre-v2.0.1 `documentation/<plan-slug>-proposal.html`) is kept as the target unless the operator asks for a move to the `docs/plan-redline/` location. A recorded hosted locator (a `https://claude.ai/artifact/...` or other URL) is stale: write the file at the contract path, replace the `Proposal:` line with that path, and never update or mint a hosted copy.
- When the proposal file cannot be written (read-only tree, unresolved repository), report the reason explicitly and make no plan edit; do not fall back to a hosted copy.
- Report every `Proposal:` locator change, in either direction, in the publish or fold report; when the prior locator was hosted, state that the prior copy remains published and is now stale.
- External issue mutations follow workspace git/GitHub safety rules and require repo-sync after post-sync plan changes.
