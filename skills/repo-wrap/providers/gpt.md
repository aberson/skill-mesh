# repo-wrap - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve capability tiers with `config/model-tier-map.json`; explicit router overrides win.
- Resolve exactly ONE target per invocation in the core's precedence, classify it, and state the classification line before acting. Use structured tool/action calls for filesystem, shell, git, GitHub, and named-skill operations.
- Rail A is a pure pass-through: dispatch `/repo-update` through the named-skill action and add nothing to its ceremony.
- Safety-critical, never weakened: the Owner-match check (any error counts as NOT owned), never push to a remote the operator does not own, never a bare `git push`, and never `git add -A` / `git add .` / stash at the coding root.
- Autonomous by default and never a `(y/n)` gate; `--dry-run` performs zero mutations.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: the classification line, one line per action taken, the parked-advisory list with exact commands, and any next-step blocks last. Preserve locked strings, the classification enum, paths, and command ordering exactly; reject missing required fields instead of inferring success.
