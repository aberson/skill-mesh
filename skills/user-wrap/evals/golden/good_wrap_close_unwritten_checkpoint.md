<!-- GOLDEN OUTPUT - user-wrap - scenario_wrapclose_unwritten_checkpoint -->

Resuming repo-update | project wrap: COMPLETE
Next Action: operator acceptance
git: project main @ a1b2c3d — 0 dirty, 0 ahead

triage: advise (would route end-window) | context: unavailable | boundary: complete | git: project 0 dirty, 0 ahead | goal: none

## WRAP & CLOSE
Already durable: pushed through @ a1b2c3d.
Dies with this window: this turn's checkpoint is not written.

Wrapping — invoking /session-wrap --end.

Checkpoint not written: required_tool_missing (session identity).

## Pick up here
route end-window | checkpoint not written (Checkpoint not written: required_tool_missing (session identity).)
Full handoff: not rendered this turn (checkpoint not written)

Step 1 ? re-run in this window after session identity is available:
```text
/session-wrap --end
```
