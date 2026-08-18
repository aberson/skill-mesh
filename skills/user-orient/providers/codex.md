# user-orient - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Codex has no Agent/Workflow primitive: where the core asks for an isolated fresh-context agent, use its documented single-context fallback and run the work in this session.
- Step 1's asides are a SET of lookups, not a concurrency requirement. If the host cannot issue them in one batch, run them in the order the core lists and still withhold every finding until Step 2 -- the ordering gate ("do not output the findings yet") is the contract; parallelism is only an optimization.
- Codex has no Artifact tool: the orientation is operator-facing output, and anything the core marks durable is written as a FILE and reported by path. The skill stays read-only by default -- it mutates no memory, plan, or code.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report. Keep the six sections in the core's fixed order and its word-count targets.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and report a section as unverified rather than filling it from assumption.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
