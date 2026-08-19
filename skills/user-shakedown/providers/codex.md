# user-shakedown - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The load-before-derive ledger rule, the one-disposition-per-row closure loop, the zero-open termination check, and the STOP-not-guess escape hatch stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Slug and ledger resolution (`git rev-parse --show-toplevel` per the engine reference), verification runs, quick fixes in the live tree with the NARROWEST test, and evidence capture are shell and file work that run natively. Every `satisfied`/`fixed` flip carries its concrete evidence; a bare flip is a defect.
- The `/goal` arming the core recommends is a Claude-window primitive: reproduce it as operator text for a host that supports it, and on this host simply keep driving the closure loop in-session until the engine's zero-open check returns 0 -- the termination condition is the check, not the arming.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and a guessed verdict is a contract violation -- park the row `logged` with the judgment question instead.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
