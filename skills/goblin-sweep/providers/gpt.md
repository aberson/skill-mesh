# goblin-sweep - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve capability tiers with `config/model-tier-map.json`; explicit router overrides win.
- Run the three fail-loud prerequisite checks in order via shell actions before the invocation; STOP on the first failure exactly as the core specifies. Never emit an empty or fabricated backlog in place of a real run.
- Parse the engine's `--json` output ONLY; never scrape its human-readable default output. Add no obligation-extraction, dedup, or atom-parsing logic.
- If a required shell or named-skill action is unavailable, return `required_tool_missing`; do not weaken the prerequisite gate or the seven-field output contract.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: the seven locked fields per obligation and the closing `/goblin-do <obl-id>` next-rail line. Preserve locked strings, the `obl-<project>-<slug>` id shape, field order, and exit/stop behavior exactly; reject missing required fields instead of inferring success.
