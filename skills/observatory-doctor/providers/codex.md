# observatory-doctor - Codex entry point

Load [../core.md](../core.md) in full before acting. The core owns behavior and safety; this adapter only maps its shell operation to Codex's local shell tool.

Run the core's prepared `uv run` command from the coding root. Preserve command, stdout, stderr, and exit code. Keep `--no-probe` even when a caller asks for a live probe; explain the core's status-override hazard instead. Keep the fixed `--no-sync --frozen --offline --no-python-downloads` launcher flags. If the runtime is unavailable or stale, diagnose it and stop without installing, syncing, retrying through an ambient executable, or simulating the report.

Return only the core-defined operator report and evidence. Never edit a project or registry, run a fix command, select a probe, or claim health beyond the rows the CLI measured. If Codex has no local shell capability, return `required_tool_missing`.
