# citation-review - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Preserve the calibration gate verbatim: `cite calibrate check` first; STOP on a fingerprint mismatch or a stale gate unless the operator explicitly authorized `--accept-aged`. A calibration PASS is the CLI's printed verdict, never this wrapper's impression of one.
- Run every `uv run --project citation-needed cite ...` call through Codex's shell tool with the payload on STANDARD INPUT. Large JSON on argv is a documented failure mode, not a style preference. Do not supply fetched page text or an API echo -- the CLI re-verifies those paths itself.
- Read both schemas under `citation-needed/docs/contracts/` before constructing any payload; construct against the schema, never against a remembered shape.
- Never modify the reviewed artifact. A failed commit means there is no review result -- report the failure rather than a partial run dressed as a verdict.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: breakdown location, band, citations, and any documented absence. Preserve locked strings, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
