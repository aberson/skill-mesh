---
name: build-step
description: Claude provider entry point for build-step; loads the canonical shared core.
user-invocable: true
---

# build-step - Claude entry point

Core: ../core.md
Model: Claude model selected by `.claude/references/model-tiering.md`

## Provider-specific instructions
- Load the core in full before acting. Use Claude Code's Skill tool for named-skill calls and Agent/Workflow tools for isolated agents where core requires those host abstractions. An Agent dispatch starts a fresh context, so the isolation part of the core's Step 0 host-capability check needs no further probe on this host; the core's other Step 0 checks (helper, Playwright, capture script, ports) still run.
- Tier binding: dispatch code and runtime reviewer arms with `model: sonnet` (the reviewer tier; image-capable, so it serves the UI arm), the phone-a-friend arm with `model: fable`, and the developer arm with no model override so it inherits the session. Record the requested model, effort and reported model per arm as the core requires; an unreported identity stays `null`.
- Run liveness: the owner process the helper records is the Claude Code CLI process hosting this session (the nearest ancestor of the helper process running the Claude Code executable), with its start time. `recover --abandon` resolves the caller's own process by the same rule, so it accepts only a call made from inside the session that owns the disrupted run.
- Preserve the core's gates, retry limits, filesystem safety, and exact output contracts.
- Verdict channel: normally follow build-phase's parent-local key contract. In the bounded Forge native lane, map every terminal core `write_verdict` call to the closed `write` operation on the host-owned `mcp__forge_verdict__verdict` connection, including blocked, failed and halt exits; the helper owns the rotating key. Send terminal `PASS` only after every ship gate, cleanup and stash-restoration operation has succeeded. The developer and every reviewer remain normal fresh `forge-worker` agents with no MCP, ToolSearch, nested Agent, inline MCP, fork or resume capability. They never receive a key, signature, service handle or verdict operation. The `forge-probe` type is canary-only, carries only the verdict tool, and is forbidden after the production channel opens. Structured tool errors block; prose never authorizes advancement. Issue closure remains subsequent best-effort bookkeeping.
- Use Claude session JSONL, scratchpad identity, Artifact actions, or VS Code deep links only where this wrapper can supply them and core requests the corresponding abstraction.

## Output normalization
- Return only the core's operator-facing report and structured artifacts. Preserve exact locked strings, verdict enums, and exit codes.

## Unsupported capabilities
- If a required Claude host tool is unavailable, use the core's documented fallback; otherwise halt visibly with `required_tool_missing`. Never weaken a core gate.
