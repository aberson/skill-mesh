---
name: citation-sweep
description: Claude provider entry point for citation-sweep; loads the canonical shared core.
user-invocable: true
---

# citation-sweep - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full. Keep all artifact OPEN, PREPARE, and COMMIT phases in this parent context. Do not dispatch per-artifact workers.
- Resolve one exact judge id by citation-review's Claude rule and pass it unchanged to every phase. After the OPEN ALL barrier, map each vote to a fresh depth-1 Agent sibling selected for that id. A judge receives one frozen choice/evidence input and cannot spawn an Agent.
- Prove direct Agent dispatch before opening. If unavailable, return required_tool_missing; there is no nested-worker or in-context voting fallback.
- Preserve scoped overview semantics, the ordered open barrier, k=3/5/7 votes, exact run ids, and truthful partial states. Never calibrate or retry implicitly.

## Output normalization

Return only the core's scope, per-path states, queue results, failures, and next actions.

## Unsupported capabilities

Missing or inconclusive fresh Agent dispatch halts before the first open.
