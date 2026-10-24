# citation-triage - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem and shell operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Never infer an operator decision from rank, from model output, or from a citation alone; present the queue as decision support and wait for the operator.
- Recheck the displayed row identity immediately before invoking exactly one of `--keep` / `--cut` / `--rewrite` through a shell action. Add `--by <operator>` only when supplied.
- On cancel, make no further resolve calls; preserve and report earlier durable resolutions. Never edit or apply a target artifact.

## Known GPT limitations

- Claude Artifact actions, session JSONL paths, and Claude-only deep links are unavailable and are not required by this core.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code without retrying. Never silently omit a core gate.

## Output normalization

The closing output is the core's Report or HELD form; the presentation and row-bound operator questions remain required interactive output. Preserve exact row identities, receipts, states, and command ordering; reject missing fields instead of inferring success.
