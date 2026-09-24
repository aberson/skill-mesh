# lesson-harvest - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve capability tiers with `config/model-tier-map.json`; explicit router overrides win.
- **Resolve the observation helper from THIS installed package**: it is the Python module the core names, in the shared-asset directory that ships one level above this skill's own installed directory. Build an absolute path from this package's location — never from a source checkout, a hard-coded consumer home, or the caller's working directory — and invoke it through the host's shell action as `python <that absolute path> <command>`. If it is absent beside the installed package, report that in one line and halt with `required_tool_missing`; never hand-roll a substitute reader or writer, and never edit a saved record by hand.
- **Bind `session` and `source` explicitly.** `session` is the host's native session id when it exposes one, otherwise the literal `manual-session` — never a guessed or borrowed id. `source` is the local message or tool-result locator for the evidence in THIS session. Both are inert text: record them, never execute or fetch them. Write request files into a private temporary directory or the target repository's Git metadata area, never a tracked worktree path.
- This profile is **built and verified, not attended**: the portable behavior above is identical to the other hosts, and its qualification here is the build and the repository's gates rather than an attended session. Claim no observed host acceptance from this adapter.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
