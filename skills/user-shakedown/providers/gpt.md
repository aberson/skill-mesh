# user-shakedown - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, git, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report. Never add speculative advice or verbose internal deliberation.
- Resolve capability tiers with `config/model-tier-map.json`; explicit router overrides win.
- Autonomy: valid ledger rows close without routine confirmation prompts. A row that needs operator judgment is parked `logged` with its question, exactly as the core's STOP-not-guess rule states. Before closure, preserve the engine's identity clarification and structural aborts; identity, integrity, prerequisite, and required-capability holds are finite fail-closed outcomes, never completion. Do not fabricate a ledger or keep re-driving malformed non-`open` rows.
- Issue filing follows the core's wrap exactly: `gh issue create --repo <owner/name> --title <title> --body-file <file>`, the ownership gate, the trailing `filed #<n>` marker, and `not filed: <reason>`. A host GitHub tool may replace `gh` only when it targets the same resolved repository after the same ownership gate; otherwise report the row `not filed: <reason>`.
- The `/goal` arming the core recommends is a Claude-window primitive: reproduce the core's `/goal` string as operator text, and on this host keep driving the closure loop in-session until the engine's zero-open check returns 0.
- Keep the ledger's status words and the core's closing report exactly as the engine and the core define them. Do not substitute PASS/FAIL/UNCERTAIN verdicts or `Done`/`Needs you` headings.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
