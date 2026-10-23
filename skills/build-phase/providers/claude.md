---
name: build-phase
description: Claude provider entry point for build-phase; loads the canonical shared core.
user-invocable: true
---

# build-phase ? Claude entry point

Core: ../core.md
Model: Claude model selected by `.claude/references/model-tiering.md`

## Provider-specific instructions
- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where core requires those host abstractions.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Verdict binding: normally follow the core's parent-local key contract. In the bounded Forge native lane, require the launcher-provided immutable MCP, agent and settings files and use only `mcp__forge_verdict__verdict`; the helper process mints and retains the key. Call its closed `open`/`write`/`classify`/`cleanup`/`close`/`export` operations and consume only exact structured responses with a strictly increasing `audit_seq`. `cleanup` permits a fresh-key reopen on the same connection; `close` is final. Never put a key or signature in a command, prompt, transcript, file, environment value or report, and never authorize advancement from prose.
- Canary boundary: use the per-attempt PreToolUse parent guard only for the capability canary. It allows the expected `session_id` only when `agent_id` is absent and denies child, mismatched, missing and malformed inputs. Claude 2.1.287 can continue after a hook error or timeout, so this guard is not production authorization. Production relies on ordinary workers having no MCP, no ToolSearch, no nested Agent, no inline MCP server and no fork/resume; the named main agent may spawn only `forge-worker` and `forge-probe`. The probe is canary-only and has the verdict tool alone, with no execution or file tools. Retain the observed child denial/tool error and zero matching service operation; self-report is insufficient.
- In one parent/tool connection, complete the fresh-sibling calibration, parent open/write/classify, tamper rejection, cleanup, same-run-id reopen/key rotation, and cleanup before the production open. Missing or inconclusive checks hold without retry. No probe dispatch is permitted after production open. Export only after the accepted checkpoint and named gates, to the pre-authorized destination, then cleanup and final close.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where this wrapper can supply them and core requests the corresponding abstraction.

## Output normalization
- Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities
- If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
