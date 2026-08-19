# test-prune - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The evidence bar, the triage table, the confirmation gate, and the tests-only scope fence stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Codex has no isolated fresh-context agent primitive, and this core documents NO single-context fallback for its Phase 1 parallel Explore flagging arms -- never a serial in-line scan, even for small test suites. Halt visibly with `required_tool_missing`, naming the Phase 1 flagging dispatch as the core step that could not run. Do not substitute an in-session scan for the fan-out this wrapper cannot provide; a documented fallback is a core change, not a wrapper's call.
- The Phase 2 verify gate, Phase 3 quality gates, and Phase 4 report are grep, citation, and shell work that run unchanged when the flagging phase can run; the triage table remains the gate and deletions are never auto-executed.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never delete a test without the cited covering evidence the core requires.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
