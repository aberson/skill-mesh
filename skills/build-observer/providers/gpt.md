# build-observer - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve capability tiers with `config/model-tier-map.json`; explicit router overrides win.
- Preserve the read-only contract exactly: no write to `registry.toml` or `snapshot.json`, and no `observatory scan`/`status` invocation.
- Run the core's Step 5 launcher through a Windows PowerShell shell action as one command. Preserve its fixed offline flags, absolute paths, literal argument encoding, cwd restoration, and separate stdout/stderr capture. Relay every `[build-observer]` stderr line verbatim (`KEPT`/`DROPPED`/`OMITTED`, truncation notices, and registry and snapshot notes); stdout is the TOML snippet. Report both streams separately -- collapsing them loses the confident-vs-guessed distinction the redline exists to show. If the host lacks Windows PowerShell, return HELD rather than adding another dialect.
- Never pass `--public` without `--public-reason` quoting the operator's own instruction.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined four-part operator-facing output: the TOML snippet, the redline (every `[build-observer]` stderr line verbatim plus the core's other Step 6 redline items, including the one-line note on values that are not mechanically validated), any `[project.launch]` follow-up, and the nothing-was-written reminder. Preserve locked strings, field names, and ordering exactly; reject missing required fields instead of inferring success.
