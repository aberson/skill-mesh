---
name: test-prune
description: Claude provider entry point for test-prune; loads the canonical shared core.
user-invocable: true
---

# test-prune - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and read-only Explore/Agent invocations for the isolated Phase 1 arms. Each arm receives only its assigned files, must not receive write tools, and reports its actual model.
- Preserve the core's evidence, current-byte, recoverability, operator-confirmation, and quality gates. Never grant a Phase 1 arm mutation authority.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.

## Output normalization

Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
