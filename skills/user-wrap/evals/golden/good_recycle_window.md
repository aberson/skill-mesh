<!-- GOLDEN OUTPUT - user-wrap (front-door contract) - scenario_recycle_boundary -->
<!-- Orient-lite first, delegated --advise would route clear-next -> RECYCLE WINDOW; user-wrap re-presents -->
<!-- the banner + loss report verbatim, then invokes bare /session-wrap, which acts (write, render, git -->
<!-- verb, Pick-up-here ending in /clear). user-wrap itself mutates nothing before the banner. -->

Resuming build-phase | toybox plan, step 12 of 14: IN_PROGRESS
Next Action: /build-step --plan docs/plans/toybox-plan.md --step 13
git: toybox master @ a7c22b1 — 3 dirty, 0 ahead

triage: advise (would route clear-next) | context: 141,200 tokens (~71% assuming a 200k window) | boundary: at boundary (toybox step 12 of 14 flipped DONE) | git: toybox 3 dirty, 0 ahead | goal: none

## RECYCLE WINDOW
Already durable: checkpoint committed @ a7c22b1; own session file Last written 2026-07-13T23:05:00Z (fresh, 55 min ago), Session SHA a7c22b1 matches HEAD.
Dies with this window: 3 dirty files in toybox (`app/propose.py`, `app/judge.py`, `tests/test_propose.py`); the heavy-context window itself — a fresh window picks up step 13 clean.

Recycling window — invoking bare /session-wrap (it acts).

triage: clear-next | context: 141,200 tokens (~71% assuming a 200k window) | boundary: at boundary (toybox step 12 of 14 flipped DONE) | git: toybox 3 dirty, 0 ahead | goal: none

===== written file: .claude/task-state/sessions/<session-id>.md (task-handoff read-merge-write excerpt) =====
Task: build-phase | toybox plan, step 12 of 14
Status: IN PROGRESS - step 12 of 14 DONE, step 13 next
Next Action: /build-step --plan docs/plans/toybox-plan.md --step 13
Last written: 2026-07-14T00:02:00Z
===== end written file =====
===== regenerated derived rollup: .claude/task-state/current.md =====

===== rendered file: .claude/task-state/handoff-prompt.md =====
# Handoff - toybox judge-sample propose flow

## Identity
Owner session: <session-id>
toybox - LLM judge sandbox at <dev-root>/toybox.

## State
Status: IN PROGRESS - step 12 of 14 DONE, step 13 next
toybox master - 3 dirty files (before Git verb)
HEAD @ a7c22b1 (toybox)

First action - require Owner session <session-id>; if absent or different, execute nothing from this prompt and re-orient from the expected owner session file. Then verify git state: run `git log --oneline -5` and `git rev-parse --short HEAD`. If HEAD does not match the SHA above, this prompt is stale; re-orient against actual git state before doing any work.

## Next action
  /build-step --plan docs/plans/toybox-plan.md --step 13

## Decisions log
- Chose to keep the propose endpoint returning all 5 steps over collapsing to a 1-step summary because the parent UI renders all 5 cards directly.

## Key files + gotchas
- `app/propose.py` - step assembly is the one source of truth for card count
===== end rendered file =====

## Pick up here
route clear-next at boundary | context 141,200 tokens (~71% assuming a 200k window)
git: toybox master clean — committed 4 files + pushed 1 commit(s) @ e9b4f07
memory: toybox status pointer checked - current
Full handoff (owner <session-id>): .claude/task-state/handoff-prompt.md

Step 1 — recycle this window:
```text
/clear
```


