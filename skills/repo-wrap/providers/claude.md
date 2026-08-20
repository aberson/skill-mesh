---
name: repo-wrap
description: Claude provider entry point for repo-wrap; loads the canonical shared core.
user-invocable: true
---

# repo-wrap - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where the core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where available and requested by the core.
- Resolve exactly ONE target per invocation in the core's precedence (explicit positional arg, then the `/user-project` pin, then cwd), classify it, and state the classification line before acting.
- Rail A is a pure pass-through: invoke `/repo-update` via the Skill tool and add nothing to its ceremony. On failure, surface repo-update's own failure verbatim rather than improvising a fallback.
- Safety-critical, never weakened: apply the Owner-match check exactly as the core defines it (case-insensitive exact equality against `gh api user --jq .login`; any error counts as NOT owned), never push to a remote the operator does not own, and never rely on a configured upstream. Never `git add -A`, never `git add .`, and never stash at the coding root.
- Autonomous by default and never a `(y/n)` gate: execute the safe subset and PARK everything ambiguous or outward-facing as an advisory line carrying the exact command, printed and not run. `--dry-run` performs zero mutations.

## Output normalization

Return only the core's operator-facing report: the classification line, one line per action taken, the parked-advisory list with exact commands, and any next-step blocks last. Preserve exact locked strings and the classification enum.

## Unsupported capabilities

If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken the Owner-match check, the push safety rule, or the Rail D creation guard.
