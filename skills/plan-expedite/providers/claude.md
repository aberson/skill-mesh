---
name: plan-expedite
description: Claude provider entry point for plan-expedite; loads the canonical shared core.
user-invocable: true
---

# plan-expedite ? Claude entry point

Core: ../core.md
Model: Claude model selected by `.claude/references/model-tiering.md`

## Provider-specific instructions
- Honor the resolved coordinator/interactive handoff mode. Coordinator mode returns the shared ready packet to the existing coordinator with no goal/clear output or builder launch. Native session-reset commands apply only to the explicit interactive path; execution-host requirements do not select the coordinator host.
- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where this wrapper can supply them and core requests the corresponding abstraction.

## Output normalization
- Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities
- If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
