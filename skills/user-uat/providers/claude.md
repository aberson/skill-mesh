---
name: user-uat
description: Claude provider entry point for user-uat; loads the canonical shared core.
user-invocable: true
---

# user-uat - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Map the `--deep` assessor to a fresh Sonnet-tier Agent. Map the Visual PASS gate to a separate fresh Opus-tier strong-final Agent. Neither child may be the feature-producing session or the browser-driving runner, and the strong-final child receives the complete evidence bundle required by the core. If either Agent capability is unavailable, return the core's `required_tool_missing` escalation instead of assessing inline.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.

## Output normalization

Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
