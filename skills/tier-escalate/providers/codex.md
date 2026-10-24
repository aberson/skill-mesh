# tier-escalate - Codex entry point

Load [../core.md](../core.md) in full before acting.

## Codex bindings

- Unless `--skills-dir` is explicit, set `discovery_root` to the parent of this loaded package: the active `.agents/skills` discovery root. Never substitute `.claude/skills` or route native Codex through the GPT/Copilot transport.
- Map `isolated_readonly_task` to fresh no-history sibling tasks with read-only access. Before the first arm, apply the host's established agent-isolation contract. Dispatch within available slots in independent batches; capacity changes scheduling only. No single-context fallback exists.
- Resolve the ordinary fan-out capability from the loaded tier map and explicit host overrides. The map names capability roles; it does not establish a Codex model identity.
- Locate policy by walking cwd ancestors for `.claude/references/model-tiering.md`; an explicit `--policy` wins. Preserve Claude-specific policy text as cited policy and report host/source disagreement instead of pretending Codex can execute Claude model-switch commands.
- Read every generated entrypoint with its linked installed core and adapter bodies. Launcher-only classification is invalid.
- Actual model is `UNKNOWN` unless the host returns a distinct execution receipt. Configuration, requested model, and this adapter are not receipts.

Preserve zero-write dry-run, evidence verification, verdict enums, artifact shape, and the exact closing line. If the isolation contract or fresh sibling tasks are unavailable, return `required_tool_missing: classification-fan-out` and emit no map.
