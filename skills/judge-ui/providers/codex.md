# judge-ui - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. Apply `judge-core.md` unchanged: independent judge context, evidence on every retained verdict, mechanical gates first, and UNCERTAIN/escalation rather than an unsupported PASS.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- The driving leg is portable: Playwright capture, the parametrized flow spec, the project adapter (or the core's documented inline-flow fallback when no adapter exists), and the MANDATORY structured read-back all run through Codex's shell and file tools, with mechanical asserts first -- a mechanical failure stops the flow and is itself a FAIL, no vision call needed, exactly as the core states.
- The verdict leg is not: Codex has no isolated fresh-context agent primitive, and this core documents NO single-context fallback for its independent vision-judge dispatch -- the orchestrator that drove the browser never renders the verdict. Halt visibly with `required_tool_missing`, naming the vision-judge dispatch as the core step that could not run. Never view the screenshots and grade your own driving, and never auto-PASS through the missing judge.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never emit `VERDICT: PASS` without the independent judge and the evidence pair (screenshot path plus read-back value) the core requires.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
