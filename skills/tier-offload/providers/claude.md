---
name: tier-offload
description: Claude provider entry point for tier-offload; loads the canonical shared core.
user-invocable: true
---

# tier-offload - Claude entry point

Load [../core.md](../core.md) in full before acting.

## Claude bindings

- Unless `--skills-dir` is explicit, set `discovery_root` to the parent of this loaded package: the active `.claude/skills` discovery root. Do not scan another host profile.
- Map `isolated_readonly_task` to fresh no-history Claude Agent/Explore invocations with read-only tools. Pin classification arms to the ordinary fan-out capability; dispatch independent arms in parallel batches and never reuse them.
- Read each generated `SKILL.md` plus every linked installed core and adapter body. Frontmatter or launcher-only classification is invalid.
- Accept `EVIDENCED` only after parent verification that a fresh independent non-local primary-provider reviewer at its configured tier always runs and alone controls the gate, as defined in the core. `ABSENT` and `CONFLICTING` emit false; `build-step-style` is always false.
- Switchboard validation is config-only. Use a prepared source loader with `PYTHONDONTWRITEBYTECODE=1`; never invoke `judge`, `inspect`, the bare module smoke, or a local endpoint.
- Report actual model only from a host receipt; otherwise `UNKNOWN`.

Preserve the core's mode matrix, standing `build-step-style: false`, false-on-absent/conflicting gate evidence, config schema, and exact closing line. Missing isolated tasks return `required_tool_missing: classification-fan-out`.
