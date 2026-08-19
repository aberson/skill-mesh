# user-afterparty - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The pinned posture is absolute here: afterparty is GLUE -- it sequences, collects, and reports, and any hygiene logic a swept skill owns that gets authored in this wrapper's session is a defect.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Chain every swept skill through Codex's named-skill dispatch, honoring each skill's own gate and the autonomous/conversational split. A swept item whose skill is unavailable on this host -- `context-slim` is Claude-native and absent from the codex profile, and `test-prune` plus the `tier-drift` pair halt `required_tool_missing` on this host -- lands in the ONE collected report as its reason code, exactly like any other per-item result. Never reimplement an unavailable skill's pass inline (SEQUENCE, DON'T REIMPLEMENT), and never let one unavailable item abort the rest of the sweep.
- The orphan-owner duties and the rollup commit/archive seam are afterparty's own shell/git work and run natively; report-first / apply-on-confirm and `--dry-run` semantics are unchanged, and afterparty still adds no bare `(y/n)` gate of its own.
- The `dev-sprint-wrap-monthly` scheduled-task framing is operator text about the workspace's scheduler; reproduce it, never claim this host armed it.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never report a swept item as clean because its skill could not run -- unavailable is its own result.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
