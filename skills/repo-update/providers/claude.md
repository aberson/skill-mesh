---
name: repo-update
description: Claude provider entry point for repo-update; loads the canonical shared core.
user-invocable: true
---

# repo-update - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Step 12 tour: write the HTML file with the host's file-write tool at the core's document output contract path (`<repo>/_shared/document-output.md`) and load the `artifact-design` skill first for page craft. Never publish the tour as a Claude Artifact, even though this host has the Artifact tool.
- Use Claude session JSONL, scratchpad identity, or VS Code deep links only where available and requested by the core.
- Lane inbox (`<repo>/_shared/lane-inbox-hooks.md`): fill the core's Step 9 `lane-inbox-call` block with `--host claude`. The call is read-only and passes no window token. Never read `COPILOT_AGENT_SESSION_ID` or another host's variable. Run the block as one shell call with a timeout of at least 60 seconds (the helper bounds itself to 30 seconds).

## Output normalization

Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
