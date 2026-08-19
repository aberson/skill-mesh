# memory-distill - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The one-round-at-a-time walk, the seven-section round shape, the every-round-drafts-a-candidate rule ("no change" is an outcome, never a starting position), and mutate-on-approval stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- `<workspace-memory>` is a project-scoped directory of memory FILES (`MEMORY.md` index plus `feedback_*.md` bodies), not a Claude-only store: resolve it through the host's own project-memory convention, or take the directory the operator names. If no memory directory exists to review, report that in one line and stop -- never invent a memory store, never write one into a repo tree, and never review from recollection instead of the files.
- The skill is conversational by design: lineup confirmation, the theme-scan push-back window, and per-round approval are the core's own gates and run unchanged in this session. Edits land only in the memory files the round approved, quoted-not-paraphrased.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and report a round's evidence section as "no recent evidence" rather than fabricating a firing the session cannot cite.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
