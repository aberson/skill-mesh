---
name: judge-ui
description: Claude provider entry point for judge-ui; loads the canonical shared core.
user-invocable: true
---

# judge-ui - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Request `opus` for the fresh vision-judge role where model selection is available. Record the
  accepted selection and read runtime-reported model identity from the child task receipt or
  session JSONL `message.model`; never treat the child's own claim as identity evidence.
- Confirm both fresh isolation and child image access before any drive. If either is unavailable,
  return `required_tool_missing` as the core requires; do not let the driving session grade its
  own screenshots or replace the judge with an API or another provider.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.

## Output normalization

Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities

If a required Claude host capability is unavailable, halt visibly with `required_tool_missing`.
Use only optional utility fallbacks the core explicitly documents; never replace the independent
vision judge or weaken a core gate.
