---
name: user-pm
description: Claude provider entry point for user-pm; loads the canonical shared core.
user-invocable: true
---

# user-pm - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting and follow it. Its sources, sections, gates and output contract are the contract; this wrapper only binds Claude Code tools to them and never weakens a core gate.
- Read files with the Read, Grep and Glob tools. Run the core's git, `gh` and `passing-notes` commands through the Bash or PowerShell tool.
- Bind each numeric timeout the core names to that tool's `timeout` parameter, in milliseconds (30 seconds is `30000`), and run the call in the foreground, never with `run_in_background`, so the bound applies to it. Apply the core's output cap to the text the call returns.
- This skill uses no Skill, Agent or Workflow tool call. An agent-limit or dispatch error that this window has already reported is observed evidence for the core's agent capacity check.
- Use no Artifact action, session JSONL or scratchpad path: the core asks for none.

## Output normalization

Return only the core's operator-facing report, or its `--json` object. Preserve exact locked strings and enums.

## Unsupported capabilities

When a Claude tool the core's reads need is unavailable, use the core's documented one-line fallback for that input and continue. Never simulate a tool result.
