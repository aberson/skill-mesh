# review-gauntlet - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim, including review-deep's core for the lens definitions, which this core imports verbatim and never re-defines. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Codex has no isolated fresh-context agent primitive, and this core documents NO single-context fallback for its five per-lens reviewer invocations: the producer never grades itself, and the deep-reasoning lenses ALWAYS spawn fresh contexts. Halt visibly with `required_tool_missing`, naming the lens dispatch as the core step that could not run. Never serialize the five lenses into this session, never self-grade, and never emit the `**Verdict:**` line without the fan-out that feeds the deterministic reducer.
- The deterministic aggregation ladder, the no-sidecar/no-output-file invariant, and the closing prompt line stay exactly as the core states them.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never substitute an in-session opinion for a lens verdict the missing isolation primitive would have produced.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
