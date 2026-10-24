---
name: citation-distill
description: Claude provider entry point for citation-distill; loads the canonical shared core.
user-invocable: true
---

# citation-distill - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting and preserve its gates, no-retry rule, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.
- Require the core's exact active-artifact, same completed-run, and scoped-readiness evidence before proposing anything. On missing or stale review evidence, return the HELD handoff; do not invoke review or calibration.
- Send the `cite distill propose` JSON on standard input via the Bash tool, never on argv, and never invent a citation id.
- Propose only. Never edit the target artifact, and never report a proposal as an applied edit.

## Output normalization

Return only the core's success or HELD Report. Preserve exact path, artifact, run, choice, and queue identities and the generated/refreshed/skipped outcomes.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken the committed-review gate and never apply a proposal.
