# skill-evolve - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The verdict enum and thresholds, the per-variant result-object key set, the no-auto-push rule, and the four halts stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Codex has no workflow primitive, and this core's own halt contract governs that case: halt visibly (core halt #2, "Workflow unavailable") with `required_tool_missing` rather than falling back to a single self-grading agent -- the exact defect this skill was rebuilt to avoid. Never serialize mutator, render, and grader roles into this session, and never let anything grade output it produced.
- Brainstorm mode (`--brainstorm`) is pure reading and writing of variant proposals and runs unchanged through Codex's file tools, ending at the core's verbatim exit block.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never report a WINNER, NOISE, or REGRESSION verdict the fan-out did not actually measure.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
