---
name: citation-review
description: Claude provider entry point for citation-review; loads the canonical shared core.
user-invocable: true
---

# citation-review - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full. Use the parent Claude context for OPEN, PREPARE, and COMMIT, and one fresh Agent sibling per JUDGE vote. A judge is read-only, receives one frozen choice/evidence input, and cannot spawn another Agent.
- The default judge id is the invoking session's exact model id. Under the workspace Opus pin that is the current Claude strong-judging model. An explicit operator choice or sweep caller binding overrides it. Select that exact id on every Agent call and record each native receipt; report UNKNOWN when no receipt exists.
- The preflight passes only when this parent can call Agent directly. A spawned Agent is a leaf for this contract. If direct fresh siblings are unavailable, return required_tool_missing before opening.
- Run every model-bound calibration check and review open exactly as the core states. Send commit payloads as UTF-8 standard input, never argv. The CLI remains the only database writer.
- Preserve truthful open-uncommitted state and every k=3/5/7 vote. Never modify the target, retry a judge implicitly, or report a failed commit as a review.

## Output normalization

Return the core report or its HELD/partial-state form with exact path and run id.

## Unsupported capabilities

Classification has no in-context fallback. Missing or inconclusive fresh Agent dispatch halts with required_tool_missing.
