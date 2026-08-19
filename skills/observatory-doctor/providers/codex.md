# observatory-doctor - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The skill stays a THIN wrapper: all button-health logic lives in the `observatory doctor` CLI subcommand, and this wrapper adds none.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Run `uv run --project dev-observatory observatory doctor` (plus any pass-through flags) through Codex's shell tool from the coding root, and relay the header line and the `BROKEN`/`WARN` sections verbatim -- they are already operator-facing. Use `--json` when another skill consumes the result. If the CLI or its workspace is not present on this machine, report that in one line and stop; never reimplement the checks.
- The read-only discipline is absolute: never auto-run a server/demo/confirm-gated verb, never `--probe` anything but a fast terminating button, and never edit a project to "fix" a button -- hand the operator the report's own `code "<path>"` open-repo command and let them decide.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never report button health the CLI did not actually measure.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
