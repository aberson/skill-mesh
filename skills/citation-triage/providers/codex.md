# citation-triage - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Never infer an operator decision from rank, from model output, or from a citation alone. The queue is decision support, not a command to edit anything, and this wrapper never resolves a row the operator did not decide.
- Run `uv run --project citation-needed cite queue ...` through Codex's shell tool, invoking exactly ONE of `--keep` / `--cut` / `--rewrite` per decision and passing `--by <operator>` when the operator identity is supplied. `--keep` records a rejected proposal; `--cut` and `--rewrite` record accepted ones.
- Neither state edits or applies the target: hand accepted work to the appropriate existing editing workflow and retain the queue record as evidence.
- On cancel, write nothing -- no partial resolution, no placeholder row.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: the presented queue rows and the recorded decisions. Preserve locked strings, proposal IDs, the keep/cut/rewrite enum, and command ordering exactly; reject missing required fields instead of inferring success.
