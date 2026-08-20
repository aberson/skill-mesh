---
name: build-observer
description: Claude provider entry point for build-observer; loads the canonical shared core.
user-invocable: true
---

# build-observer - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.
- Preserve the read-only contract exactly: never open `registry.toml` or `snapshot.json` for writing, never call `registry.upsert_entry`, and never run `observatory scan`/`status` (which would refresh the on-disk snapshot cache).
- Run the Step 5 `uv run --project dev-observatory python .claude/skills/build-observer/scaffold_portfolio.py ...` validation call through the Bash tool, and relay its stderr `KEPT`/`DROPPED`/`OMITTED` lines close to verbatim -- that stderr IS the redline report, not a debug stream.
- Never pass `--public` without `--public-reason` quoting the operator's own instruction. The script hard-refuses the pair; this wrapper never supplies a reason the prose invented.

## Output normalization

Return only the core's operator-facing report: the TOML snippet, the verbatim redline lines, any `[project.launch]` follow-up, and the nothing-was-written reminder. Preserve exact locked strings and field names.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken the read-only contract, and never emit a snippet the validator did not produce.
