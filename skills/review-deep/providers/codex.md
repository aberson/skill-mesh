# review-deep - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. Apply `judge-core.md` unchanged: independent judge context, evidence on every retained verdict, deterministic aggregation, mechanical gates first, and UNCERTAIN/escalation rather than an unsupported PASS.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Codex has no isolated fresh-context agent primitive, and this core documents NO single-context fallback for its per-lens reviewer fan-out: the producer never grades itself, and lens independence comes from context isolation. Halt visibly with `required_tool_missing`, naming the lens dispatch as the core step that could not run. Never serialize the lenses into this session, never self-grade the diff, and never emit a verdict the fan-out did not produce.
- The mechanical pre-pass, diff gathering, lint pre-pass, and auth-gate probe are plain shell and run unchanged through Codex's shell tool; a missing individual mechanical tool stays the core's `MISSING-TOOL` warning-and-skip, never a reason to skip the mechanical phase.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never downgrade or drop a finding because the isolation primitive that would have produced it is absent.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
