---
name: build-phase
description: Claude provider entry point for build-phase; loads the canonical shared core.
user-invocable: true
---

# build-phase ? Claude entry point

Core: ../core.md
Model: Claude model selected by `.claude/references/model-tiering.md`

## Provider-specific instructions
- When --coordinator-packet is supplied, keep the controller in this coordinator context and honor the exact --steps span, packet boundary, allocation and reconciliation rules. Map only the builder/reviewer arms to verified isolated dispatch. Return the coordinator status instead of an interactive goal/clear or wait-session opener; no packet field bypasses the existing verdict/capability gates.
- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Mint the durable verdict path/run id/HMAC key in the parent context; never serialize the key into skill arguments or child-visible state. Require authenticated run-bound classification and unconditional sidecar cleanup. Never authorize advancement from prose.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where this wrapper can supply them and core requests the corresponding abstraction.

## Output normalization
- Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities
- If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
