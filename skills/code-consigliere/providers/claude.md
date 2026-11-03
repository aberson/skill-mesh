---
name: code-consigliere
description: Claude provider entry point for code-consigliere; loads the canonical shared core.
user-invocable: true
argument: "Optional project path; otherwise use this session's project pin or one-project cwd"
---

# code-consigliere - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting and preserve its target resolution, evidence labels,
  signoff boundary, private/public split, helper discovery order, and seed handoff.
- Use structured filesystem and shell tools for reads and helper calls. This core requires no
  isolated agent and no provider router hop.
- Ask for the target only when the core's ordered resolution leaves a coding root or multiple
  plausible projects. Do not inspect the toolkit checkout as a silent default.

## Output normalization

Return only the core's attended findings, questions, durable artifact locators, and closing
report. Preserve the four evidence-status labels exactly.

## Unsupported capabilities

If the optional helper is unavailable, use the core's read-only orientation path. Never
simulate persistent collection, install the helper, or weaken the signoff boundary.

