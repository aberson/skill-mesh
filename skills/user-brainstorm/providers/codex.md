# user-brainstorm - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The exactly-10 seed, the gap-fill loop's stop conditions, the four-tier organization, and the explicit "Proceed?" confirmation before any file write stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- The interactive ideation phase (Steps 1-5) and the meta-file writes (Step 6: `topics.md`, `plan.md`) run natively in this session through Codex's file tools.
- Codex has no isolated fresh-context agent primitive, and this core's Step 7 requires one background sub-agent per investigation file (waves, retry-in-a-fresh-dispatch) with NO documented single-context fallback. Halt visibly with `required_tool_missing`, naming the Step 7 per-file investigation dispatch as the core step that could not run. Do not author the investigation set serially in this session in its place -- the meta files on disk are the durable record a capable host resumes from.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never mark `topics.md` links as written when the files behind them do not exist.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
