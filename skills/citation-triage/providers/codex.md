# citation-triage - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem and shell operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Never infer an operator decision from rank, from model output, or from a citation alone. The queue is decision support, not a command to edit anything, and this wrapper never resolves a row the operator did not decide.
- Run `uv run --project citation-needed cite queue ...` through Codex's shell tool. Recheck the displayed row identity immediately before invoking exactly one of `--keep` / `--cut` / `--rewrite`; pass `--by <operator>` only when supplied.
- Neither accepted nor rejected status edits or applies the target. Retain the queue record; the operator chooses any subsequent editing workflow, which this skill neither selects nor invokes.
- On cancel, make no further resolve calls; preserve and report earlier durable resolutions.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, session JSONL paths, Agent/Workflow tools, and Claude-only deep links are unavailable and are not required by this core. Never simulate a missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code without retrying. Never silently omit a core gate.

## Output normalization

The closing output is the core's Report or HELD form; the presentation and row-bound operator questions remain required interactive output. Preserve exact row identities, receipts, states, and command ordering; reject missing fields instead of inferring success.
