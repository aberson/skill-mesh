<!-- GOLDEN OUTPUT - user-wrap - scenario_wrapclose_push_rejected -->

Resuming repo-update | project wrap: COMPLETE
Next Action: operator acceptance
git: project main @ a1b2c3d — 1 dirty, 0 ahead

triage: advise (would route end-window) | context: 61,000 tokens | boundary: complete | git: project 1 dirty, 0 ahead | goal: none

## WRAP & CLOSE
Already durable: setup commit pushed @ a1b2c3d.
Dies with this window: 1 dirty tracked file.

Wrapping — invoking /session-wrap --end.

## Pick up here
route end-window | context unavailable | checkpoint written
git: project main @ d4e5f6a ? commit created @ d4e5f6a; push failed: remote rejected (pre-receive hook declined)
Full handoff (owner <session-id>): .claude/task-state/handoff-prompt.md

Step 1 - continue in a fresh window after resolving the remote rejection:
```text
Read <dev-root>\project\.claude\task-state\handoff-prompt.md fully; require Owner session <session-id>, otherwise execute nothing and re-orient from the expected owner session file; then verify git state per its first instruction and execute its Next Action.
```

Wrap incomplete: commit created @ d4e5f6a; push failed: remote rejected (pre-receive hook declined)
