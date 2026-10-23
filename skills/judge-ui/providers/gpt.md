# judge-ui - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting. Use structured tool/action calls for filesystem, shell, browser, GitHub, and named-skill operations.
- Normalize GPT verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.
- Resolve inherited capability tiers with `config/model-tier-map.json`. For this core's explicit
  vision-judge role, request native `gpt-5.6-sol` and record the accepted selection plus the
  runtime-reported model from host metadata. A router or cross-cloud override does not satisfy
  that native role.
- Map each independent Agent/Explore/workflow arm to a fresh-context GPT action/task call. Dispatch independent arms in parallel. GPT action nesting may be depth-limited: orchestration stays in this parent invocation, and child actions never spawn graders. If isolated actions are unavailable, return `required_tool_missing`; do not self-grade or serialize roles into one context.
- Human-in-the-loop normalization: stop after the exact operator ask, separate `Done` from `Needs you`, and never add speculative advice or verbose internal deliberation. Preserve PASS/FAIL/UNCERTAIN or escalation enums exactly.
- Apply `judge-core.md` unchanged: independent judge context, evidence on every retained verdict, deterministic aggregation, mechanical gates first, and UNCERTAIN/escalation rather than an unsupported PASS.
- A fresh GPT-5.6 Sol child consumes screenshots directly; do not invoke a separate vision
  service. Prove that the current child can open the supplied image files as well as being fresh;
  a model name alone is not that proof. Blind the judge to producer identity and require the
  core's structured screenshot/read-back record for every stage.

## Known GPT limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, preserve the
  actual host error and apply the core's fail/escalate mapping. Do not retry through another
  provider or silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
