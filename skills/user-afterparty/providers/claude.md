---
name: user-afterparty
description: Claude provider entry point for user-afterparty; loads the canonical shared core.
user-invocable: true
---

# user-afterparty - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Before dispatch, inspect the current host's actual skill discovery/callable tools and feed
  the core's early capability table. A discovered child is `unprobed` until its own contract
  qualifies it; a missing child is `known unavailable`. Preserve child reason codes and keep
  processing other selected items. Do not infer availability from this adapter or implement
  a missing child's work inline.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.

## Output normalization

Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
