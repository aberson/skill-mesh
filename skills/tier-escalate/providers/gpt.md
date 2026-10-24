# tier-escalate - GPT entry point

Load [../core.md](../core.md) in full before acting.

## GPT bindings

- Unless `--skills-dir` is explicit, set `discovery_root` to the parent of this loaded package: the active `.github/skills` discovery root. Do not hard-code or scan Claude's discovery tree.
- Map `isolated_readonly_task` to a fresh no-history GPT action/task call with read-only filesystem access. Pin the ordinary fan-out capability through the current router/tier map, dispatch independent arms in parallel batches, and keep consolidation in the parent. Child actions never spawn graders.
- Locate policy by walking cwd ancestors for `.claude/references/model-tiering.md`; an explicit `--policy` wins. A Claude-named policy file may govern workspace roles, but it does not prove GPT changed models. Report policy/source disagreement rather than translating it away.
- Read the full generated package behavior: entrypoint plus linked core and adapter bodies. Do not classify discovery metadata or launcher prose alone.
- Requested model, router choice, and tier-map resolution are not actual-model receipts. Report `UNKNOWN` absent a host execution receipt.

Claude Agent/Workflow syntax, session JSONL, Artifact actions, and model-switch commands are not portable. Use GPT task APIs and standalone files only. Preserve zero-write dry-run, evidence verification, verdict enums, artifact shape, and the exact closing line. If fresh isolated actions are unavailable, return `required_tool_missing: classification-fan-out`.
