# citation-sweep - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve capability tiers with `config/model-tier-map.json`; explicit router overrides win.
- Preserve the calibration gate: `cite calibrate check` first, and STOP if it is invalid.
- Map each per-artifact review arm to a fresh-context GPT action/task call and dispatch independent arms in parallel. Each worker returns ONLY path, run id, band, number of choices, citation/absence summary, and blocker. If isolated actions are unavailable, run the reviews sequentially in this invocation under the SAME terse per-artifact return contract -- never widen the return, and never silently pass an unavailable review.
- Cluster genuinely near-duplicate decisions before fanning out.
- Never fabricate a corpus hit, an external verification, a calibrated verdict, or a completed review; stop instead.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: scope, clusters, completed and blocked reviews, queue rows, and any producer/API failure. Preserve locked strings, the per-artifact return fields, schemas, and command ordering exactly; reject missing required fields instead of inferring success.
