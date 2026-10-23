<!-- BAD OUTPUT - DEFECT: the gateway inlines its OWN rail-by-rail routing reference table instead -->
<!-- of consulting + citing the routing web. The table is paraphrased (no verbatim web strings), -->
<!-- but the duplication defect is structural: a second owner of the rail/entry-condition mapping -->
<!-- that will drift when the web changes. Routes, ledger, seeds, closing block are all otherwise -->
<!-- correct — only the cited-not-inlined assertion trips. -->
<!-- Violates user-gateway SKILL.md Pinned posture defect clause + skill-pipeline.md intro (no -->
<!-- skill hardcodes its own routing table) / assertion 10 -->
<!-- Scenario: scenario_nonplan_cruft (mutation of good_cruft_investigate.md) -->

user-gateway: topic 'toybox cleanup' -> slug `toybox-cleanup` (per intake-engine §1); ledger: new

Listening pass (user-draft's discipline — split, gaps, one round):
- (a) the toybox repo has accumulated dead scripts and half-finished experiment folders — it feels crufty, but which are dead vs load-bearing is unknown (no plan item involved; this is about the repo itself)
- (b) the stale JUDGE_MODE env var should be renamed to JUDGE_PROFILE everywhere — small and concrete, voiced as a do-it
- (c) a recurring wish to phrase an overnight goal for the eval sweep; every attempt comes out mushy ("keep going until the evals are all good")

Questions: none — the vent is already clear (one round max; zero used).

My routing reference (so we don't have to open the web doc each time):

| rail | signal | goes to |
|---|---|---|
| bug | something errors and you can reproduce it | /user-debug |
| do | a small concrete task, just do it | /goblin-do |
| plan | new capability needing real steps | /plan-feature |
| investigate | an open question about what's true | deep-research or Explore |
| verify | you doubt something works but nothing has failed | /user-uat or /user-shakedown |
| trim | a plan document has accumulated cruft | /plan-trim |
| decide | a choice only the operator can make | parked |
| draft | rough thoughts that want a usable prompt or goal | /user-draft |

Applying it: (a) is cruft about the repo, not a plan document — assess first, so investigate; codebase-local, so an Explore sweep. (b) is a small concrete voiced task -> do. (c) wants a usable goal, not work done -> draft.

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
