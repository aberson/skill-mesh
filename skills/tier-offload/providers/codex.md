# tier-offload - Codex entry point

Load [../core.md](../core.md) in full before acting.

## Codex bindings

- Unless `--skills-dir` is explicit, set `discovery_root` to the parent of this loaded package: the active `.agents/skills` discovery root. Never substitute `.claude/skills` or send native Codex through the GPT/Copilot router.
- Map `isolated_readonly_task` to fresh no-history sibling tasks with read-only access after applying the host's established agent-isolation contract. Dispatch within available slots in independent batches. There is no parent-context fallback.
- Resolve the ordinary fan-out capability through the loaded tier map and explicit host overrides. This is a role binding, not an actual-model receipt.
- Read every generated entrypoint with its linked installed core and adapter bodies. Launcher-only classification is invalid.
- Accept `EVIDENCED` only after parent verification that a fresh independent non-local primary-provider reviewer at its configured tier always runs and alone controls the gate, as defined in the core. `ABSENT` and `CONFLICTING` emit false; `build-step-style` is always false.
- Use only the prepared Switchboard config loader with `PYTHONDONTWRITEBYTECODE=1`. Never read a live home config, run `judge`/`inspect`, probe an endpoint, install anything, or invoke a local model.
- Report actual model as `UNKNOWN` unless the host supplies a distinct execution receipt.

Preserve the mode matrix, verdict enum, config schema, validator limitations, and exact closing line. Missing isolation or sibling-task capability returns `required_tool_missing: classification-fan-out` and emits no inventory or config.
