# user-debug - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The forced primary-source investigation, the Diagnosis Block shape, and the bug-vs-feature re-route contract stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Step 1's investigation and Diagnosis Block run natively and remain durable output. Codex has no isolated fresh-context agent primitive, and this core's Step 2 independent reproduction ("always") requires an arm that is given the symptom but NOT the suspected root cause -- a constraint this parent context cannot satisfy about itself, so no single-context substitute exists by construction and the core documents none. Halt visibly with `required_tool_missing`, naming the Step 2 independent-reproduction dispatch as the core step that could not run, before any fix design or code change. The same applies to the Option 4 tie-breaker arm. Never compare the orchestrator's diagnosis against itself and call it independent.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never ship a fix whose diagnosis the independence check did not actually corroborate.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
