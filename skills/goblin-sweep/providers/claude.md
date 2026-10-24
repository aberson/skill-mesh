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
- Run the three fail-loud prerequisite checks in order (uv on PATH, the engine project directory exists, `goblin sweep --help` exits 0); STOP on the FIRST failure exactly as the core specifies, naming the engine plan as remediation. Resolve `<workspace-root>` as the coding-root directory that holds the project directories and `b2_project_goblin` (the engine uses that same parent as its default workspace root). The core's snippets are PowerShell: run them with the PowerShell tool where it exists, or use equivalent checks in the Bash tool (`command -v uv`, `test -d`, the same `uv run --project <abs-path>` call). Shell variables do not persist between tool calls: set `$workspaceRoot` in the same command as each snippet, or substitute the resolved absolute path. Correct a malformed shell command and rerun that check. The check's own negative result (uv not found, directory absent, or `--help` nonzero) is the failed prerequisite: STOP, and do not search for uv off PATH or run `uv sync` to make the check pass.
- Parse the engine's `--json` output ONLY; never scrape its human-readable default output, and add no obligation-extraction, dedup, or atom-parsing logic. The wrapper shells one CLI command and renders text.
- Pass the dispatcher-supplied project as one literal argv element: use structured argv or safe literal quoting in the selected shell, never command-string interpolation or `eval`. Reject extra skill arguments and flags instead of forwarding them.
- Render exactly the seven locked fields per obligation, in the core's order, and never emit an empty or fabricated backlog in place of a real run.

## Output normalization

Return only the core's operator-facing output -- the seven locked fields per obligation and the closing `/goblin-do <obl-id>` next-rail line, plus any usage, fixed completeness notice, `Engine warnings:`, relayed engine stderr on a nonzero exit, malformed-output, empty-result, or stop line the core defines. Preserve exact locked strings, the `obl-<project>-<slug>` id shape, field order, and stop/exit behavior.

## Unsupported capabilities

If a required Claude host tool (shell or skill dispatch) is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken the prerequisite gate or emit a fabricated backlog.
