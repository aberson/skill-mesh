# user-gateway - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The intake-ledger row grammar, the no-row-stays-open rule, and the parked-rows-are-never-answered rule stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Ledger reads and writes are ordinary file I/O per the intake-engine contract and run natively. Consult the routing web as the core directs -- cite it, never reproduce its table.
- Every per-row seed is paste-ready TEXT for the window that will run it, not a dispatch this skill makes: emit each seed verbatim in its rail's spelled shape -- including the investigate rail's `Workflow({name: "deep-research-pinned"})` charter line, which stays the pinned name for the target host -- and never rewrite a seed into a this-host form, substitute a built-in name, or execute a seed in this session.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and a fragment the gateway cannot safely route parks with the routing question stated -- never a guessed route.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
