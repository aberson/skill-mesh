# citation-review - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve capability tiers with `config/model-tier-map.json`; explicit router overrides win.
- Preserve the calibration gate: `cite calibrate check` first, STOP on a fingerprint mismatch or a stale gate unless `--accept-aged` was explicitly authorized, and never claim a PASS the CLI did not print.
- Route every CLI call through a shell action with the payload on standard input, never on argv. The CLI is the only database writer; this wrapper adds no scoring, quote-verification, or DB logic.
- Never modify the reviewed artifact, and never report a failed commit as a review result.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: breakdown location, band, citations, and any documented absence. Preserve locked strings, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
