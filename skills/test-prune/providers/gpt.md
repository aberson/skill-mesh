# test-prune - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve capability tiers with `config/model-tier-map.json`; explicit router overrides win.
- Map each independent Agent/Explore/workflow arm to a fresh-context, read-only GPT action/task call with only its assigned files. Dispatch independent arms in parallel, deny write-capable tools, and record the model each arm actually ran. GPT action nesting may be depth-limited: orchestration stays in this parent invocation, and child actions never spawn graders. If isolation or read-only enforcement is unavailable, return `required_tool_missing`; do not serialize roles into one context.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, report the actual router failure and stop the affected arm or run. Never invent a retry allowance, cross-provider fallback, or successful core gate.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
