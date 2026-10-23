# user-uat - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The tier partition (never auto-PASS a non-mechanical check), the side-effect confirmation gate, the mechanical-FAIL-stops-the-run rule, and the plain-text report with its exact `Needs you` heading stay exactly as the core states them.
- Tier names in inherited procedures name capability roles. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so use the closest capability the configured Codex host actually provides. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Classification, grounding citations, and the mechanical tier run natively through the shell: capture stdout/stderr and exit codes, judge only against the step's concrete expectation, and show the observed value. Long-running actions go through the host's background/long-running shell facility with the readiness probe polled before any dependent verify; a probe that never comes up is the core's mechanical AUTO-FAIL with the log tail as evidence.
- `--deep` requires a fresh sibling task for the assessor; the invoking Codex session never supplies the assessment. A candidate Visual PASS requires another fresh sibling task at the workspace's Sol strong-final tier after `/judge-ui` or `/judge-motion`; the assessor and strong-final task are distinct. If the current host cannot prove fresh-context task isolation, report the core's `required_tool_missing` escalation. `--ui` delegates through named-skill dispatch; where a visual judge is unavailable on this host, land the step in `Needs you` and never view the screen or render the visual verdict in this session.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, provider failure, malformed child output, or a missing required adapter, use the core's fail-closed escalation and name the failed capability. Never silently omit a gate or rationalize a side-effectful step as read-only to skip confirmation.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
