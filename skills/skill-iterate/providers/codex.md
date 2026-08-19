# skill-iterate - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The lock file, kill-switch, budgets, outcome taxonomy, and ship gate stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Codex has no workflow primitive and no isolated fresh-context agent primitive, and this core documents NO single-context fallback for its render/grade split: keeping render and grade as separate agents is non-negotiable, and no task grades its own output. Halt visibly with `required_tool_missing`, naming the score-loop dispatch as the core step that could not run. Never self-grade a render, and never serialize the brainstorm arm, render tasks, and grader tasks into this session.
- The deterministic scoring helpers and the root-only `skill-iterate/scripts/` package are plain shell/python and keep their script-home exception; worktree lifecycle operations are real `git worktree` / `git -C` shell work when the loop can run.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback where one is defined; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never record an iteration outcome the graded loop did not actually produce.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
