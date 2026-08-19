# repo-sync - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, GitHub, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Run every git/gh operation in the repository the core's pre-flight resolves and verifies (including any session-active project pin the core's transition contract honors) via Codex's shell tool. Preserve command order and exit codes, use body files for non-trivial GitHub issue text, and verify repository identity before writes. Never infer command success from prose.
- Autonomous by default: never insert a mid-run `(y/n)` gate or an apply-changes confirmation that the core does not define.
- Codex has no Agent/Workflow primitive: where the core asks for an isolated fresh-context agent, use its documented single-context fallback and run the work in this session.
- Codex has no Artifact tool: anything the core marks durable is written as a FILE and reported by path.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate; never mint or edit a GitHub issue the core did not order, and report a sync step as unverified rather than assuming it succeeded.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
