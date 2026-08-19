# research-prospect - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The topic-quality bar ("informs" must name a real pending decision), the depth-scoped command forms, and the mandatory QUICK COPY block stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Codex has no isolated fresh-context agent primitive, and this core's Step 2 requires one Explore arm per project dispatched in parallel ("sequential dispatch is a defect") with NO documented single-context fallback. Halt visibly with `required_tool_missing`, naming the Step 2 per-project Explore fan-out as the core step that could not run. Do not sweep the projects in this session in its place -- a menu rendered from in-session skims is not the contract's output.
- Step 1's project-list resolution (flags, MEMORY.md, directory checks) is ordinary file reading and may run before the halt so the report can name exactly which per-project arms could not be dispatched.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never render a topic menu the fan-out did not actually produce.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
