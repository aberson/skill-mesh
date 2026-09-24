---
name: lesson-harvest
description: Claude provider entry point for lesson-harvest; loads the canonical shared core.
user-invocable: true
---

# lesson-harvest - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.
- **Resolve the observation helper from THIS installed package**, not from a source checkout and not from the caller's working directory: it is the Python module the core names, in the shared-asset directory that ships one level above this skill's own installed directory. Build an absolute path from this package's location and invoke it with the host's shell tool as `python <that absolute path> <command>`. If the module is not present beside the installed package, say so in one line and halt with `required_tool_missing` — never substitute a hand-rolled reader or writer for it, and never edit a saved record by hand.
- **Bind `session` and `source` explicitly.** `session` is this Claude Code session's native id when the host exposes one (the session JSONL identity); when it does not, use the literal `manual-session` — never a guessed, borrowed, or fabricated id. `source` is the local message or tool-result locator for the evidence in THIS session (for example the assistant turn and the tool result that show the error). Both are inert text: record them, never execute or fetch them.
- Write every record/complete request file into the host's private temporary area or the target repository's own Git metadata area — never into a tracked worktree path — and delete only the request files this invocation created.

## Output normalization

Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
