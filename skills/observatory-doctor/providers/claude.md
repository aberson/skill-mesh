---
name: observatory-doctor
description: Relay the real Dev Observatory launcher health check through a prepared, static, no-sync runtime.
user-invocable: true
---

# observatory-doctor - Claude entry point

Load [../core.md](../core.md) in full before acting. The core owns behavior and safety; this adapter only maps its shell operation to Claude's local shell tool.

Run the core's prepared `uv run` command from the coding root. Preserve command, stdout, stderr, and exit code. Keep `--no-probe` even when a caller asks for a live probe; explain the core's status-override hazard instead. Keep the fixed `--no-sync --frozen --offline --no-python-downloads` launcher flags. If the runtime is unavailable or stale, diagnose it and stop without installing, syncing, retrying through a different executable, or simulating the report.

Relay only the core-defined operator report. Never edit a project or registry, run a fix command, select a probe, or claim health beyond the rows the CLI measured. If the shell capability is unavailable, return `required_tool_missing`.
