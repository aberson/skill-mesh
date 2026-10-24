# goblin-do - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The read-only boundary, the anchor-liveness refusal, the goal-able/seed render rule, the verbatim relay of CLI output, and the re-route contract citation stay exactly as the core states them.
- Run the core's command (`uv run --no-sync --frozen goblin do <id-or-text> [flags]`, from the `b2_project_goblin` directory) through Codex's shell tool. The flags require the already prepared environment and prevent environment synchronization or lock-file updates. No Workflow, sub-agent, or `claude` CLI is involved. If `uv`, the prepared environment, its frozen lock, or the `goblin` console script is unavailable, halt visibly with `required_tool_missing` naming the goblin CLI; never run `uv sync` or install as recovery. Never render a `/goal` block or seed by reading the atom by hand.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Preserve the write boundary exactly: neither goblin nor this wrapper writes to `brain/`, the target project, or git. On an ordinary invocation, the only permitted write is the core's intake-ledger write-back under the re-route contract. On `--dry-run`, print the same artifact, re-route, and next step but never perform that ledger write-back.
- `/goal` is a Claude Code window command with no Codex equivalent. Relay the emitted block verbatim as operator text for a window that supports it, and never claim a goal is armed or started. If the operator pursues the `goal_condition` in a Codex session instead, that session is implementation work selected under the workspace's native Codex builder policy; that is the operator's selection, not something this wrapper enforces. This wrapper does not start that session or choose its model.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. The core needs none of them; never simulate a missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never report an artifact the goblin CLI did not print.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
