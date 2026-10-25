---
name: session-wrap
description: Claude provider entry point for session-wrap; loads the canonical shared core.
user-invocable: true
---

# session-wrap ? Claude entry point

Core: ../core.md
Model: Claude model selected by `.claude/references/model-tiering.md`

## Provider-specific instructions
- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where this wrapper can supply them and core requests the corresponding abstraction.
- For model-side session identity, use only the current host-supplied scratchpad path as specified by the shared task-state schema. If it is absent, report identity unavailable and use orientation-only fallback. Do not substitute a PID metadata file, a matching prompt, a lone/newest transcript, or an inherited identifier. A transcript may supply context usage only after the permitted current-session binding is established; otherwise emit the core's exact unavailable-context signal. In --advise mode, still report the advisory result with unknown identity/context and never run a Next Action or write state.

## Output normalization
- Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.
- In `--advise` mode, return exactly four lines: the triage line (including raw Git counts
  and any unavailable identity/context signal), the verdict banner, `Already durable:`
  (including any proven-exclusion count and proof basis), and `Dies with this window:`
  (including every unknown-provenance path), then STOP. Append no reasons, methodology,
  foreign-state explanation, or action summary.

## Unsupported capabilities
- If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
