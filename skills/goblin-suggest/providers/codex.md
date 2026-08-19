# goblin-suggest - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The anchor schema (repo-relative file path resolvable by `git ls-files`), the grading math (per-axis median, composite mean, partial-verdict DROP), the tie-to-needs-human default, and the atom paths/frontmatter stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Codex has no Workflow primitive, so the session path is unavailable: run the core's documented CLI fallback (`uv run goblin suggest <project>`, which shells generator and judge calls to `claude -p` subprocesses with a ThreadPoolExecutor per candidate) through Codex's shell tool -- judge independence and parallelism live in those subprocesses, unchanged. Where the `claude` CLI or its OAuth token is absent from the environment, halt visibly with `required_tool_missing` naming the suggest rail; never generate-and-judge candidates inside this one session.
- The switchboard local-model offload keeps its core contract: inert by default, a defer always falls back to the normal judge for that vote, and the median/rank/persist logic is never gated by the local model.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never score a candidate on a partial verdict set -- it is dropped, exactly as the core states.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
