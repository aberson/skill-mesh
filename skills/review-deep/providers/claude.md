---
name: review-deep
description: Claude provider entry point for review-deep; loads the canonical shared core.
user-invocable: true
---

# review-deep - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.
- Lens dispatch follows the core's § Dispatch route ladder: Agent-tool siblings first; when the Agent tool is unavailable or its concurrency slots are exhausted, `claude -p` per lens (fresh process, read-only tools, `--model` per the tier table, no session resume); halt `required_tool_missing` only when neither exists.

## Output normalization

Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
