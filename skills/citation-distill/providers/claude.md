---
name: citation-distill
description: Claude provider entry point for citation-distill; loads the canonical shared core.
user-invocable: true
---

# citation-distill - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.
- Require real review evidence before proposing anything: a fresh COMMITTED review for the target. An open run, a mock, or an uncommitted payload is not evidence -- run `/citation-review <path>` via the Skill tool first.
- Send the `cite distill propose` JSON on standard input via the Bash tool, never on argv, and never invent a citation id.
- Propose only. Never edit the target artifact, and never report a proposal as an applied edit.

## Output normalization

Return only the core's operator-facing report: proposal IDs, ranks, evidence basis, and the `/citation-triage` handoff. Preserve exact locked strings and the run id.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken the committed-review gate and never apply a proposal.
