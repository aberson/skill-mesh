# tier-offload - GPT entry point

Load [../core.md](../core.md) in full before acting.

## GPT bindings

- Unless `--skills-dir` is explicit, set `discovery_root` to the parent of this loaded package: the active `.github/skills` discovery root. Do not hard-code Claude discovery.
- Map `isolated_readonly_task` to fresh no-history GPT action/task calls with read-only filesystem access. Pin the ordinary fan-out capability through the router/tier map, dispatch independent arms in parallel batches, and consolidate in the parent. Children never spawn graders.
- Read the complete generated behavior package: entrypoint plus linked core and adapter bodies. Do not classify launcher prose alone.
- Accept `EVIDENCED` only after parent verification that a fresh independent non-local primary-provider reviewer at its configured tier always runs and alone controls the gate, as defined in the core. `ABSENT` and `CONFLICTING` emit false; `build-step-style` is always false.
- Validate candidate JSON only with a prepared Switchboard source loader and `PYTHONDONTWRITEBYTECODE=1`. Do not install dependencies, inspect live config, or invoke a local model.
- Requested/configured model identity is not a receipt; report `UNKNOWN` absent a host execution receipt.

Claude Agent/Workflow syntax and session facilities are unavailable. Use GPT task APIs and standalone files. Preserve the mode matrix, verdict enum, config schema, validator limitations, and exact closing line. Missing fresh isolated actions return `required_tool_missing: classification-fan-out`.
