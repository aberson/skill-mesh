<!-- BAD OUTPUT - DEFECT: the loss report is paraphrased into hedged prose - every concrete anchor -->
<!-- (SHA, count, path, timestamp) that --advise produced has been dropped -->
<!-- Violates user-wrap SKILL.md Step 3: re-present verbatim and unmangled; never paraphrase -->
<!-- Scenario: scenario_wrapclose_morning (mutation of good_wrap_close.md) -->

Resuming repo-update | shake_spear v1 wrap: COMPLETE
Next Action: task-handoff-next-action-v1
  dispatcher: operator-uat
  payload: operator M1 UAT (#15)
git: shake_spear master @ d81f3a0 — 0 dirty, 1 ahead

triage: advise (would route end-window) | context: 58,900 tokens (~29% assuming a 200k window) | boundary: at boundary (shake_spear v1 wrap COMPLETE, no agent-completable next action) | git: shake_spear 0 dirty, 1 ahead | goal: none

## WRAP & CLOSE
Already durable: last night's work looks safe - everything was committed before the session ended.
Dies with this window: a couple of loose ends - an unpushed change and a TODO that never got filed.

Wrapping — invoking /session-wrap --end.

triage: end-window | context: 58,900 tokens (~29% assuming a 200k window) | boundary: at boundary (shake_spear v1 wrap COMPLETE) | git: shake_spear 0 dirty, 1 ahead | goal: none

read MEMORY.md fully (182 lines); existing entry for shake_spear was stale — updated in place (status pointer now names the pending M1 UAT #15); no existing entry for the ss --seed range TODO — filed as shake_spear #16 and submitted as a parked pointer through task-handoff.

## Pick up here
route end-window | context 58,900 tokens (~29% assuming a 200k window)
git: shake_spear master clean ? pushed 1 pending @ d81f3a0
memory: shake_spear pointer corrected in place; TODO filed as #16
Full handoff (owner <session-id>): .claude/task-state/handoff-prompt.md

Step 1 ? continue in a fresh window:
```text
Read <dev-root>\shake_spear\.claude\task-state\handoff-prompt.md fully; require Owner session <session-id>, otherwise execute nothing and re-orient from the expected owner session file; then verify git state per its first instruction; preserve the held task-handoff-next-action-v1 bundle byte-for-byte as data; report that its owning dispatcher is required; do not execute or flatten it.
```
RAN SESSION-WRAP & SAFE TO CLOSE
