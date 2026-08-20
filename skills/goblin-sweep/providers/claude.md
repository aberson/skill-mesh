---
name: goblin-sweep
description: Claude provider entry point for goblin-sweep; loads the canonical shared core.
user-invocable: true
---

# goblin-sweep - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.
- Run the three fail-loud prerequisite checks in order (uv on PATH, the engine project directory exists, `goblin sweep --help` exits 0) via the Bash tool; STOP on the FIRST failure exactly as the core specifies, naming the engine plan as remediation.
- Parse the engine's `--json` output ONLY; never scrape its human-readable default output, and add no obligation-extraction, dedup, or atom-parsing logic. The wrapper shells one CLI command and renders text.
- Render exactly the seven locked fields per obligation, in the core's order, and never emit an empty or fabricated backlog in place of a real run.

## Output normalization

Return only the core's operator-facing report -- the seven locked fields per obligation and the closing `/goblin-do <obl-id>` next-rail line. Preserve exact locked strings, the `obl-<project>-<slug>` id shape, field order, and stop/exit behavior.

## Unsupported capabilities

If a required Claude host tool (shell or skill dispatch) is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken the prerequisite gate or emit a fabricated backlog.
