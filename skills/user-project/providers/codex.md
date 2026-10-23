# user-project - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The SET/SHOW/CLEAR dispatch, registry validation, and fail-loud-on-bad-name behavior stay exactly as the core states them, and the pin stays advisory: it never blocks anything.
- This skill uses no model tier and spawns nothing (core: Provider-neutral host abstractions), so no tier resolution applies. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Run the core's PowerShell resolution snippets through Codex's shell tool preserving their PS-5.1-safe shapes and exact outputs (marker-based coding-root walk, registry parse, backslash-normalized absolute path). Never substitute bare `git rev-parse --show-toplevel` for the marker walk.
- Claude scratchpad paths are not portable. Use a session ID only when Codex's own session-I/O adapter supplies a stable per-session identifier; the core then proceeds unchanged (including creating the minimal session file when absent). When none is supplied (the Codex CLI exposes no stable per-session identifier today), follow the core's identity-unavailable outputs: SET and CLEAR write nothing and print its `Active project not changed: required_tool_missing (session identity). ...` line; SHOW prints its identity-unavailable line. Never use the freshest `sessions/*.md` or the `current.md` rollup as this session's file, never read another host's session variable such as `COPILOT_AGENT_SESSION_ID` (Copilot also scans this `.agents/skills` root) or the router's per-invocation `SKILL_ROUTER_SESSION_ID`, and never fabricate an identity or create a session file under a guessed ID. Honoring skills fall back to the plan/argument or cwd-derived repo.
- Preserve the write discipline exactly: read-merge-write with every other line kept verbatim, UTF-8 with no BOM, and never a repo-wide `git add` afterward -- the session file is gitignored.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, preserve and report the actual error, write nothing, and stop. Do not retry implicitly and do not switch providers. Never silently omit a core gate, and never write a pin the operator cannot trace to this session's own file.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
