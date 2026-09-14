---
name: task-handoff
description: Claude provider entry point for task-handoff; loads the canonical shared core.
user-invocable: true
---

# task-handoff ? Claude entry point

Core: ../core.md
Model: Claude model selected by `.claude/references/model-tiering.md`

## Provider-specific instructions
- Map --coordinator-packet and --resume-coordinator onto real filesystem/Git operations using the shared packet contract and actual host session/child identities. Preserve the explicit packet pointer and resolve its retained state root independently of builder cwd. Never substitute a newest-session guess or fabricated child exit; missing required identity/helper/bridge remains visible.
- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where this wrapper can supply them and core requests the corresponding abstraction.

## Output normalization
- Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities
- If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
