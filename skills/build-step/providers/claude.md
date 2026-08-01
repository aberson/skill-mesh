---
name: build-step
description: Claude provider entry point for build-step; loads the canonical shared core.
user-invocable: true
---

# build-step ? Claude entry point

Core: ../core.md
Model: Claude model selected by `.claude/references/model-tiering.md`

## Provider-specific instructions
- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Keep the verdict path/run id and parent-local HMAC key out of developer/reviewer contexts. The key is private orchestration state, never a recorded skill argument. Atomically authenticate every terminal verdict and write PASS only after ship gates, cleanup, and stash restoration succeed; issue closure is subsequent best-effort bookkeeping.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where this wrapper can supply them and core requests the corresponding abstraction.

## Output normalization
- Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities
- If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
