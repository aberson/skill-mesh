<!-- BAD OUTPUT - DEFECT: RECYCLE WINDOW invokes /session-wrap --end instead of bare /session-wrap - -->
<!-- the window gets a full end-of-day wrap (fresh-window opener, memory pass) when the correct action -->
<!-- is the clear-next recycle ending in /clear -->
<!-- Violates user-wrap SKILL.md Step 4: RECYCLE WINDOW -> invoke bare /session-wrap -->
<!-- Scenario: scenario_recycle_boundary (mutation of good_recycle_window.md) -->

Resuming build-phase | toybox plan, step 12 of 14: IN_PROGRESS
Next Action: /build-step --plan docs/plans/toybox-plan.md --step 13
git: toybox master @ a7c22b1 — 3 dirty, 0 ahead

triage: advise (would route clear-next) | context: 141,200 tokens (~71% assuming a 200k window) | boundary: at boundary (toybox step 12 of 14 flipped DONE) | git: toybox 3 dirty, 0 ahead | goal: none

## RECYCLE WINDOW
Already durable: checkpoint committed @ a7c22b1; own session file Last written 2026-07-13T23:05:00Z (fresh, 55 min ago), Session SHA a7c22b1 matches HEAD.
Dies with this window: 3 dirty files in toybox (`app/propose.py`, `app/judge.py`, `tests/test_propose.py`); the heavy-context window itself — a fresh window picks up step 13 clean.

Wrapping — invoking /session-wrap --end.

triage: end-window | context: 141,200 tokens (~71% assuming a 200k window) | boundary: at boundary (toybox step 12 of 14 flipped DONE) | git: toybox 3 dirty, 0 ahead | goal: none

read MEMORY.md fully (182 lines); existing entry for toybox was current — no change.

## Pick up here
route end-window | context 141,200 tokens (~71% assuming a 200k window)
git: toybox master clean ? committed 4 files + pushed 1 commit(s) @ e9b4f07
memory: toybox entry current, no change
Full handoff (owner <session-id>): .claude/task-state/handoff-prompt.md

Step 1 ? continue in a fresh window:
```text
Read <dev-root>\toybox\.claude\task-state\handoff-prompt.md fully; require Owner session <session-id>, otherwise execute nothing and re-orient from the expected owner session file; then verify git state per its first instruction and execute its Next Action.
```
