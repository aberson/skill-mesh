---
name: citation-sweep
description: Claude provider entry point for citation-sweep; loads the canonical shared core.
user-invocable: true
---

# citation-sweep - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.
- Preserve the calibration gate: `cite calibrate check` first, and STOP if it is invalid. An uncalibrated sweep produces numbers, not evidence.
- Dispatch the per-artifact reviews as isolated fresh-context Agent invocations, one per artifact, each carrying the `/citation-review` contract. Each worker returns ONLY path, run id, band, number of choices, citation/absence summary, and blocker -- the terse return is the bound, and widening it defeats the sweep.
- Cluster genuinely near-duplicate decisions BEFORE fanning out, so equivalent claims do not get independent citation searches or duplicate durable keys.
- Never fabricate a corpus hit, an external verification, a calibrated verdict, or a completed review; stop instead. Never edit a target artifact in any rail.

## Output normalization

Return only the core's operator-facing report: scope, clusters, completed and blocked reviews, queue rows, and any producer/API failure. Preserve exact locked strings and per-artifact field order.

## Unsupported capabilities

If isolated Agent invocations are unavailable, run the reviews sequentially under the same terse per-artifact return contract rather than widening it; if a required Claude host tool is unavailable, halt visibly with `required_tool_missing`. Never weaken the calibration gate and never emit a synthetic sweep.
