# review-uat - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. Refinement is file reads plus `file:line` grounding through Codex's own tools; never run the UAT yourself -- this skill never executes Setup/Verify blocks inline.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Keep the target-shell detection rules exactly: the OPERATOR'S shell, not Codex's, decides the authored syntax, and an ambiguous target defaults to PowerShell-safe forms.
- `--exec` delegates to `/user-uat` (and `--ui` routes visual checks to `/judge-ui`) via Codex's named-skill dispatch, mapping only flags both skills actually declare. If the downstream skill is unavailable on this host, halt visibly with `required_tool_missing` naming it -- never execute the steps inline in its place, and never silently drop the flag. Relay downstream results verbatim; do not re-judge, re-run, or summarize away the evidence.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and preserve PASS/FAIL/UNCERTAIN and escalation enums exactly.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
