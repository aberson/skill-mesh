---
name: build-queue
description: Claude provider entry point for build-queue; loads the canonical shared core.
user-invocable: true
---

# build-queue ? Claude entry point

Core: ../core.md
Model: Claude model selected by `.claude/references/model-tiering.md`

## Provider-specific instructions
- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where core requires those host abstractions.
- At core Step 0, establish that the configured invoking model is the strong gate selected by the current Claude model-tiering policy for build-step's orchestrator/final-judge role. Record configured and host-reported observed identities when available. If that binding cannot be established, return the core's `required_tool_missing: strong_final_judge` pre-flight failure; never let a producer grade its own work.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where this wrapper can supply them and core requests the corresponding abstraction.

## Output normalization
- Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities
- If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
