# user-uat - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The tier partition (never auto-PASS a non-mechanical check), the side-effect confirmation gate, the mechanical-FAIL-stops-the-run rule, and the plain-text report with its exact `Needs you` heading stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Classification, grounding citations, and the mechanical tier run natively through the shell: capture stdout/stderr and exit codes, judge only against the step's concrete expectation, and show the observed value. Long-running actions go through the host's background/long-running shell facility with the readiness probe polled before any dependent verify; a probe that never comes up is the core's mechanical AUTO-FAIL with the log tail as evidence.
- `--deep` is the core's own in-session labeled assessment and runs unchanged; Human-tier steps always escalate. `--ui` delegates through named-skill dispatch to `/judge-ui` / `/judge-motion`; where the judge is unavailable on this host (`judge-motion` is Claude-native and absent from the codex profile; `/judge-ui` on this host halts at its vision-judge dispatch), surface `required_tool_missing` naming it and land the step in `Needs you` -- never view the screen yourself and render a visual verdict in its place.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never rationalize a side-effectful step as read-only to skip its confirmation.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
