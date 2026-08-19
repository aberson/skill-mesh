# user-project - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The SET/SHOW/CLEAR dispatch, registry validation, and fail-loud-on-bad-name behavior stay exactly as the core states them, and the pin stays advisory: it never blocks anything.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Run the core's PowerShell resolution snippets through Codex's shell tool preserving their PS-5.1-safe shapes and exact outputs (marker-based coding-root walk, registry parse, backslash-normalized absolute path). Never substitute bare `git rev-parse --show-toplevel` for the marker walk.
- Claude scratchpad paths are not portable. Obtain the stable session ID through the abstract session-I/O layer using Codex's own session conventions; when the host exposes one, the core proceeds unchanged (including creating the minimal schema-valid session file when absent). If no stable identity exists, follow the core's documented fallback to the freshest `sessions/*.md` -- never fabricate an identity or create a session file under a guessed ID. If no session file exists to carry the pin, report that in one line and write nothing: the pin is advisory, and honoring skills fall back to the cwd-derived repo.
- Preserve the write discipline exactly: read-merge-write with every other line kept verbatim, UTF-8 with no BOM, and never a repo-wide `git add` afterward -- the session file is gitignored.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never write a pin the operator cannot trace to a real session file.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
