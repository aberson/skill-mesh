# lesson-harvest - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, GitHub, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Codex has no Agent/Workflow primitive: where the core asks for an isolated fresh-context agent, use its documented single-context fallback and run the scan in this session, holding the same evidence bar -- every candidate is grounded in committed history, never in recollection.
- Codex has no Artifact tool: the draft PR is created through the host's shell/GitHub tooling, and any longer detail is written as a FILE and reported by path. The DETECT-AND-DRAFT boundary is absolute: never write a memory file or a lessons/friction/rules document, and never merge the skill's own PR.
- Preserve the staging discipline exactly: scoped `git add <paths>` only, never `git add -A`, and confirm with `git diff --cached --stat` before committing. Out-of-repo memory text goes in the PR body as ready-to-apply text, never staged.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate; report zero candidates rather than lowering the evidence bar to produce one.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
