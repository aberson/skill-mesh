# judge-ui - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve capability tiers with `config/model-tier-map.json`; explicit router overrides win.
- Map each independent Agent/Explore/workflow arm to a fresh-context GPT action/task call. Dispatch independent arms in parallel. GPT action nesting may be depth-limited: orchestration stays in this parent invocation, and child actions never spawn graders. If isolated actions are unavailable, return `required_tool_missing`; do not self-grade or serialize roles into one context.
- Human-in-the-loop normalization: stop after the exact operator ask, separate `Done` from `Needs you`, and never add speculative advice or verbose internal deliberation. Preserve PASS/FAIL/UNCERTAIN or escalation enums exactly.
- Apply `judge-core.md` unchanged: independent judge context, evidence on every retained verdict, deterministic aggregation, mechanical gates first, and UNCERTAIN/escalation rather than an unsupported PASS.
- GPT-5.6 Sol consumes screenshots directly; do not invoke a separate vision model. Blind the judge to producer identity where possible and require screenshot-path plus read-back evidence for every stage verdict.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
