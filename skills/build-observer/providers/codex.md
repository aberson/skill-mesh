# build-observer - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Preserve the read-only contract exactly: no write to `registry.toml` or `snapshot.json`, no `registry.upsert_entry`, and no `observatory scan`/`status`. Pasting the block stays an operator action after this skill returns.
- Run the Step 5 `uv run --project dev-observatory python ...` validation call through Codex's shell tool, preserving the PowerShell-5.1-safe backtick continuation shape or its single-line equivalent, and capture stdout and stderr SEPARATELY. Relay stderr's `KEPT`/`DROPPED`/`OMITTED` lines close to verbatim.
- Never pass `--public` without `--public-reason` quoting the operator's own instruction; never let the wrapper supply the reason.
- Codex needs no Agent/Workflow primitive here: the skill is single-context reading plus one script call, so there is no isolated-agent fallback to document.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: the TOML snippet, the verbatim `KEPT`/`DROPPED`/`OMITTED` redline lines, any `[project.launch]` follow-up, and the nothing-was-written reminder. Preserve locked strings, field names, and ordering exactly; reject missing required fields instead of inferring success.
