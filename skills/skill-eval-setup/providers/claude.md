---
name: skill-eval-setup
description: Claude provider entry point for skill-eval-setup; loads the canonical shared core.
user-invocable: true
---

# skill-eval-setup - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Resolve the selected target and its owning repository
  before any write; an installed generated target stays read-only.
- Use Claude Code's isolated Agent/Workflow capability for the core's producer and grader roles.
  Keep each grader separate from the producer whose artifact it grades. If isolation is unavailable,
  return the core's HELD result before writing goldens.
- Invoke the shipped shared `grader_prompt.py` and `score_skill_absolute.py` from the installed
  profile's `_shared` directory. Do not recreate their prompt or score calculation.
- Preserve the core's catalog-lifecycle stop, three-trial decisions, retry limits, path-scoped
  writes, and exact output contracts.

## Output normalization

Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities

If a required Claude host tool or shipped shared scorer is unavailable, halt visibly with
`required_tool_missing`. Never weaken a core gate or use the unwired generator CLI as a fallback.
