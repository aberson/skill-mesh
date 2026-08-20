---
name: citation-review
description: Claude provider entry point for citation-review; loads the canonical shared core.
user-invocable: true
---

# citation-review - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.
- Preserve the calibration gate: run `cite calibrate check` and STOP on a fingerprint mismatch or a stale gate unless the operator explicitly authorized `--accept-aged`. Never claim calibration passed without the CLI's own PASS result.
- Treat the Citation Needed CLI as the only database writer. Send every review-commit and calibrate-commit payload on standard input via the Bash tool -- never on argv, and never through a host abstraction that would truncate it.
- Never modify the reviewed artifact, and never report a failed commit as a review result.

## Output normalization

Return only the core's operator-facing report: breakdown location, band, citations, and any documented absence. Preserve exact locked strings and the run id.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken the calibration gate and never fabricate a citation.
