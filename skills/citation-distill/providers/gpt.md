# citation-distill - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve capability tiers with `config/model-tier-map.json`; explicit router overrides win.
- Require a fresh COMMITTED review before proposing anything; an open run, a mock, or an uncommitted payload is not evidence. Dispatch `/citation-review <path>` through the named-skill action first.
- Send the `cite distill propose` JSON on standard input through a shell action, never on argv, and never invent a citation id.
- Propose only. Never edit the target artifact, and never report a proposal as an applied edit.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: proposal IDs, ranks, evidence basis, and the `/citation-triage` handoff. Preserve locked strings, schemas, paths, and command ordering exactly; reject missing required fields instead of inferring success.
