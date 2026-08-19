# repo-update - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, GitHub, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Run git/gh operations in the repository the core resolves through Codex's shell tool, preserve command order and exit codes, use body files for non-trivial GitHub text, and verify repository identity before writes. Never infer command success from prose.
- Codex has no Agent/Workflow primitive: where the core asks for an isolated fresh-context agent (the independent wiki/doc checks), use its documented single-context fallback and run both checks in this session, aggregating findings before fixing exactly as the core orders.
- Codex has no Artifact tool: when Step 12's substantive-wrap detection fires, author the self-contained guided-tour HTML as a FILE in the repository (or the operator-named output path) and put that path on the final report's `Tour:` line. A skipped tour stays the legal, common outcome exactly as the core states -- never a blocking gate, and never a simulated private artifact URL.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and report a push or wiki fix as unverified rather than assuming it succeeded.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
