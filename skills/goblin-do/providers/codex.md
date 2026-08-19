# goblin-do - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The mode-dispatch table, the safe-uat subset, the four-part auto-ship floor (any miss parks), FF-only landing, and the four output labels stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Codex has no Workflow primitive, so the session path is unavailable: the execute rail runs the core's documented CLI fallback (`uv run goblin do <id>`, which shells the `/build-step` dispatch to a `claude -p` subprocess) through Codex's shell tool. Where the `claude` CLI or its OAuth token is absent from the environment, halt visibly with `required_tool_missing` naming the execute rail -- never degrade to an unreviewed inline edit of the target.
- Preserve the write isolation exactly: goblin's own process never writes the target's source; its only authored write is the atom status flip in `brain/`. Hand-off, `--dry-run`, and provenance strings run natively through shell and file tools.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never report `shipped` for work the build rail did not actually gate.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
