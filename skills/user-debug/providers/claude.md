---
name: user-debug
description: Claude provider entry point for user-debug; loads the canonical shared core.
user-invocable: true
---

# user-debug - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Bind write-as-you-go only to the harness UUID from this session's scratchpad path. Never borrow a child UUID or another host's environment variable.
- Before Step 4, resolve the current Claude session model through the workspace tier map. A `fable` session may perform the hard diagnosis but must not launch build-step's inherited developer: offer a switch to the default model (then re-check the accepted selection) or the core's `HANDOFF` stop with `Run in: fresh window @ <project> · Model: Opus (default)`. Record requested, accepted/configured and runtime-reported model separately; self-description is not runtime evidence.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.

## Output normalization

Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
