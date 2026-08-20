# citation-distill - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Require a fresh COMMITTED review for the target before proposing anything. An open run, a mock, or an uncommitted payload is a draft, not evidence -- dispatch `/citation-review <path>` through Codex's named-skill action first.
- Read `citation-needed/prompts/distill.v1.md` before drafting any refinement. Every cut or rewrite retains the cited evidence IDs, or the documented searched-but-not-found record; a proposal that drops its evidence basis is not a distillation.
- Run `uv run --project citation-needed cite ...` through Codex's shell tool with the proposal JSON on STANDARD INPUT, never on argv, and never invent a citation id.
- Propose only: never edit the target artifact, never change review scores, classifications, or citations, and never report a proposal as an applied edit.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: proposal IDs, ranks, evidence basis, and the `/citation-triage` handoff. Preserve locked strings, schemas, paths, and command ordering exactly; reject missing required fields instead of inferring success.
