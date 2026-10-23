# user-shakedown - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The load-before-derive ledger rule, the one-disposition-per-row closure loop, the zero-open termination check, and the STOP-not-guess escape hatch stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured native Codex host actually provides. Use native host dispatch and its configured model selection; a GPT/Copilot router override is not a native Codex capability or authentication route. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Slug and ledger resolution (`git rev-parse --show-toplevel` per the engine reference), verification runs, quick fixes in the live tree with the NARROWEST test, and evidence capture are shell and file work that run natively. Every `satisfied`/`fixed` flip carries its concrete evidence; a bare flip is a defect.
- The `/goal` arming the core recommends is a Claude-window primitive: reproduce it as operator text for a host that supports it, and on this host simply keep driving the closure loop in-session until the engine's zero-open check returns 0 -- the termination condition is the check, not the arming.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable. This core does not require them for ordinary operation. If a future core step explicitly requires one, use only its documented fallback or return `required_tool_missing`; never simulate the missing tool.
- On timeout, rate limit, provider failure, malformed tool output, or a missing required adapter, report the actual native-host failure and follow the core's action-specific failure path. Missing required capability is `required_tool_missing`. Do not invent a router reason, retry through another provider, or treat a cross-cloud allowance as authorization for a native Codex fallback. Never silently omit a core gate; where the core permits the STOP-not-guess path, park the row `logged` with the judgment question instead of guessing.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve the core's locked strings, schemas, paths, command ordering, and action-specific failure behavior exactly; reject missing required fields instead of inferring success.
