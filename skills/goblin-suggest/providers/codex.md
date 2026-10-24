# goblin-suggest - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The anchor contract (an issue reference or one tracked repo-relative path), the grading contract (per-axis median, composite mean, partial-verdict DROP), the tie-to-needs-human default, the `--uat` hold, and the atom paths/frontmatter stay exactly as the core states them.
- This wrapper maps no Workflow primitive, and the goblin CLI makes no model calls (a bare `uv run goblin suggest <project>` exits 1 with `goblin suggest: no LLM boundary`), so the generator and isolated judge arms have no route through this wrapper: after the core's usage checks, halt visibly with `required_tool_missing` naming the suggest rail before running any goblin command. Never generate and judge candidates inside this one session, never hand-write graded JSON for `--from-candidates-json`, and never shell to `claude -p` as a substitute.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- The switchboard local-model offload keeps its core contract and status: inert by default, a defer always falls back to the normal judge for that vote, and the median/rank/persist logic is never gated by the local model. This wrapper never consults it.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never score a candidate on a partial verdict set -- it is dropped, exactly as the core states.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
