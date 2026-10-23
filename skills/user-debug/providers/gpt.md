# user-debug - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve the Step 2 and Option 4 diagnosis role through `config/model-tier-map.json` and record requested, accepted/configured and runtime-reported model separately. Self-description is not runtime identity evidence.
- Fresh-context independence is required before Step 2. No calibrated no-history probe is documented for this native GPT/Copilot adapter, so stop with `required_tool_missing` before any Fix Design or code change. Never serialize parent and reproducer into one context or route the role through another provider.
- Bind write-as-you-go only to this Copilot host's `COPILOT_AGENT_SESSION_ID` supplied through its session-I/O layer. If absent, print the core's one skip line and write nothing; never read a Claude or Codex session identifier.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, preserve the actual native-host error and stop the affected arm. This adapter authorizes no API, router or cross-cloud retry. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
