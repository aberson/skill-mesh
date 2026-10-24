# citation-distill - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem and shell operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Require the core's exact active-artifact, same completed-run, and scoped-readiness evidence before proposing anything. On missing or stale review evidence, return the HELD handoff; do not invoke review or calibration.
- Send the `cite distill propose` JSON on standard input through a shell action, never on argv, and never invent a citation id.
- Propose only. Never edit the target artifact, and never report a proposal as an applied edit.

## Known GPT limitations

- Claude Artifact actions, session JSONL paths, and Claude-only deep links are unavailable and are not required by this core.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code without retrying. Never silently omit a core gate.

## Output normalization

Return only the core's success or HELD Report. Preserve locked strings, schemas, command ordering, exact identities, and generated/refreshed/skipped outcomes; reject missing required fields instead of inferring success.
