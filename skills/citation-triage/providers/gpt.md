# citation-triage - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve capability tiers with `config/model-tier-map.json`; explicit router overrides win.
- Never infer an operator decision from rank, from model output, or from a citation alone; present the queue as decision support and wait for the operator.
- Invoke exactly ONE of `--keep` / `--cut` / `--rewrite` per decision through a shell action, adding `--by <operator>` when supplied.
- On cancel, write nothing. Never edit or apply a target artifact.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: the presented queue rows and the recorded decisions. Preserve locked strings, proposal IDs, the keep/cut/rewrite enum, and command ordering exactly; reject missing required fields instead of inferring success.
