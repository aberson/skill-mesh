# citation-distill - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem and shell operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Require the core's exact active-artifact, same completed-run, and scoped-readiness evidence before proposing anything. On missing or stale review evidence, return the HELD handoff; do not invoke review or calibration.
- Read `citation-needed/prompts/distill.v1.md` before drafting any refinement. Every cut or rewrite retains the cited evidence IDs, or the documented searched-but-not-found record; a proposal that drops its evidence basis is not a distillation.
- Run `uv run --project citation-needed cite ...` through Codex's shell tool with the proposal JSON on STANDARD INPUT, never on argv, and never invent a citation id.
- Propose only: never edit the target artifact, never change review scores, classifications, or citations, and never report a proposal as an applied edit.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, session JSONL paths, Agent/Workflow tools, and Claude-only deep links are unavailable and are not required by this core. Never simulate a missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code without retrying. Never silently omit a core gate.

## Output normalization

Return only the core's success or HELD Report. Preserve locked strings, schemas, command ordering, exact identities, and generated/refreshed/skipped outcomes; reject missing required fields instead of inferring success.
