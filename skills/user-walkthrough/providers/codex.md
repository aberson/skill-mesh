# user-walkthrough - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The answers-from-primary-source rule (read the actual code/artifact, cite `file:line`, never vibes), the fix-small/log-big split, and the operator-driven yield-each-turn cadence stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- The ledger is the shakedown-engine's own file contract (shared slug rule, read-merge-write): resolve and update it through Codex's file tools so a later `/user-shakedown` picks up the SAME file mid-stream. Small fixes land in the live tree with the narrowest test as evidence; anything bigger is logged, never rabbit-holed.
- The walkthrough is conversational by design and runs natively; coverage marks are earned by the exchange that demonstrated them, never granted wholesale.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never answer an operator question from recollection when the source is one read away.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
