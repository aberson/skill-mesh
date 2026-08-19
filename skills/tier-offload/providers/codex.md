# tier-offload - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The LOCAL/PRIMARY/SCRIPT verdict enum, the `offload-config.json` schema, the standing `build-step-style: false`, and the gate-precondition rule (an unmet strong-tier-final-judge precondition emits `false`, never `true`) stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Codex has no isolated fresh-context agent primitive, and this core's classification constraint -- read-only fresh-context task invocations, every arm applying the SAME rules -- documents NO single-context fallback. Halt visibly with `required_tool_missing`, naming the Phase 2 classification fan-out as the core step that could not run. Do not classify the catalog in this session in its place.
- `--inventory-only` and `--dry-run` keep their exact core meanings; the `python -m switchboard config` line in the Next block is portable shell and is reproduced verbatim.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never emit an inventory or config the classification fan-out did not actually produce.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
