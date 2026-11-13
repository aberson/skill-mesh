---
name: task-handoff
description: Claude provider entry point for task-handoff; loads the canonical shared core.
user-invocable: true
---

# task-handoff ? Claude entry point

Core: ../core.md
Model: Claude model selected by `.claude/references/model-tiering.md`

## Provider-specific instructions
- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where this wrapper can supply them and core requests the corresponding abstraction.
- Lane inbox (`<repo>/_shared/lane-inbox-hooks.md`): fill the core's `lane-inbox-call` block with `--host claude`, and pass `--window` only the harness session UUID resolved for this session's identity. Never read `COPILOT_AGENT_SESSION_ID` or another host's variable. Run the block as one shell call with a timeout of at least 60 seconds (the helper bounds itself to 30 seconds).

## Output normalization
- Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities
- If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
