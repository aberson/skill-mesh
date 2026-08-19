# user-lavishify - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem and shell operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The escalate-only posture (chat-first stays the default) and the propagate-back-to-source-of-truth closing step, including its grep-every-downstream-consumer rule, stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- The `lavish-axi` CLI runs through Codex's shell tool (`npx -y lavish-axi ...`). The Claude session scratchpad is not portable: write the HTML artifact under a durable host-local temporary directory's `.lavish/` folder -- never into any repo tree -- and report it by path.
- The poll is long-running: run it through the host's background/long-running shell facility; where only bounded foreground runs exist, re-run the poll in successive bounded stints -- the core's own rule ("just re-run it if the harness kills it; queued feedback is never lost") makes that the sanctioned shape. Never skip fixing fresh error-severity `layout_warnings` before involving the operator.
- The security gates are absolute and carried verbatim: `LAVISH_AXI_TELEMETRY=0` on every command, loopback only (never a wildcard `LAVISH_AXI_HOST`), and never run `lavish-axi share`.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never claim a decision was propagated to canonical state without the edit or issue that proves it.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
