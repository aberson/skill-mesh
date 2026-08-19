# user-learn - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The two-phase shape (interactive setup, then parallel authoring) and the grounding rule -- project applications come from the named real workspace projects, never invented -- stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- The interactive setup (topic, scope confirmation, project grounding) runs natively in this session through Codex's file tools.
- Codex has no isolated fresh-context agent primitive, and this core's Step 4 requires one background sub-agent per file -- notebook agents author AND execute their own notebook until it runs clean -- dispatched in waves, with NO documented single-context fallback. Halt visibly with `required_tool_missing`, naming the Step 4 per-file authoring dispatch as the core step that could not run. Do not author the ramp serially in this session in its place; report what the setup produced and stop.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never claim a notebook executed green without the exit-0 run that proves it.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
