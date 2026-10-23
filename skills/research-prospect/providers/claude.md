---
name: research-prospect
description: Claude provider entry point for research-prospect; loads the canonical shared core.
user-invocable: true
---

# research-prospect - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Map Step 2 to one read-only Explore agent per resolved project, pin every arm to Sonnet, and dispatch all arms in one parallel call. The parent alone validates JSON, drops topics, and renders the menu.
- Resolve workspace and per-project memory through Claude's project-memory convention. Pass a literal `none` for an absent project memory exactly as the core specifies.
- Render high-depth lines as `/deep-research-pinned` commands for a fresh Claude window and medium-depth lines as narrow research prompts. This skill annotates the session model choice; it never launches either path.
- For `--session-wrap`, derive the stable ID only from this executing Claude session's scratchpad/session identity. Park only in that own-session file, never in `current.md`, then call the task-state derive helper. A missing ID or failed park takes the core's visible no-wrap stop.
- Invoke bare `/session-wrap` only after every rendered topic is present in the owned session file. The invoked skill owns triage and every git verb.

## Output normalization

Return the core's grounded menu, skipped line, context line, and mandatory QUICK COPY block. Preserve the exact no-topic and no-wrap messages.

## Unsupported capabilities

If read-only parallel Explore dispatch is unavailable, return `required_tool_missing` for Step 2. Do not serialize project scans or synthesize them in the parent.
