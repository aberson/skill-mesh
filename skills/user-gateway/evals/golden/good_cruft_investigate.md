<!-- GOLDEN OUTPUT - user-gateway - scenario_nonplan_cruft -->
<!-- Clear three-fragment vent: cruft-smell about the REPO (not a plan document) -> investigate -->
<!-- first per the web's trim note (codebase-local -> Explore framing), a small concrete do, a -->
<!-- mushy goal -> draft. Zero questions (vent already clear; noted). All rows routed; the embedded -->
<!-- ledger scores 0 under the intake-engine zero-open check. -->

user-gateway: topic 'toybox cleanup' -> slug `toybox-cleanup` (per intake-engine §1); ledger: new

Listening pass (user-draft's discipline — split, gaps, one round):
- (a) the toybox repo has accumulated dead scripts and half-finished experiment folders — it feels crufty, but which are dead vs load-bearing is unknown (no plan item involved; this is about the repo itself)
- (b) the stale JUDGE_MODE env var should be renamed to JUDGE_PROFILE everywhere — small and concrete, voiced as a do-it
- (c) a recurring wish to phrase an overnight goal for the eval sweep; every attempt comes out mushy ("keep going until the evals are all good")

Questions: none — the vent is already clear (one round max; zero used).

Routes chosen by consulting the routing web (skill-pipeline.md § "The 8 rails" — cited, not restated): (a) is cruft-smell about the repo, not a plan document — the web's trim note routes it investigate first (assess, then the investigate->plan or investigate->do edge applies); the question is codebase-local, so an Explore sweep rather than a deep-research charter. (b) is a small concrete voiced task -> do. (c) wants a usable goal, not work done -> draft.

===== written file: .claude/task-state/intake-toybox-cleanup.md =====
# Intake ledger — toybox-cleanup

Seeded by /user-gateway 2026-07-13. Grammar + statuses per <repo>/_shared/intake-engine.md.

| id | fragment | route | status | disposition |
|----|----------|-------|--------|-------------|
| F1 | toybox repo cruft: dead scripts / experiment folders, live-vs-dead unknown | investigate | routed | seed: Explore sweep (codebase-local) — framing in gateway output; findings re-route per the web's edges |
| F2 | rename stale JUDGE_MODE env var to JUDGE_PROFILE everywhere | do | routed | seed: /goblin-suggest --small toybox then /goblin-do <JUDGE_MODE rename atom> — /goblin-do resolves persisted atoms only |
| F3 | overnight goal for the eval sweep keeps coming out mushy | draft | routed | seed: `/user-draft overnight goal for the toybox eval sweep` |
===== end written file =====

Per-row seeds (ready to paste):

F1 — investigate (codebase-local -> Explore framing; an external/multi-source question would instead get a deep-research charter for the receiving window to dispatch via Workflow({name: "deep-research-pinned"}), never the built-in name):
Explore (read-only, medium thoroughness): sweep toybox's top-level scripts and experiment folders; classify each path live (imported or invoked from production code, CI, or a skill) vs dead (no inbound references); return one row per path: path -> verdict -> evidence. Finding shape: a cut-candidate list — findings then re-route to plan or do per the web's edges.

F2 — do (two steps — /goblin-do resolves persisted atoms only, so the atom is persisted first):
1. /goblin-suggest --small toybox   (the voiced rename — JUDGE_MODE to JUDGE_PROFILE — should surface as a small atom; confirm it appears)
2. /goblin-do rename JUDGE_MODE to JUDGE_PROFILE across toybox

F3 — draft:
/user-draft overnight goal for the toybox eval sweep — rough thought: "keep going until the evals are all good"; needs a checkable stop condition

Closing block:
Ledger: <git-root>/.claude/task-state/intake-toybox-cleanup.md (3 rows: 3 routed — zero open)
/goal "intake ledger for toybox-cleanup has zero open items"

QUICK COPY
Explore (F1): classify toybox top-level scripts + experiment folders live-vs-dead; return path -> verdict -> evidence per row
/goblin-suggest --small toybox
/goblin-do rename JUDGE_MODE to JUDGE_PROFILE across toybox   (F2 step 2 — after step 1 persists the atom)
/user-draft overnight goal for the toybox eval sweep — rough: "keep going until the evals are all good"
