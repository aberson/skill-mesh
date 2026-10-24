---
name: tier-escalate
description: Claude provider entry point for tier-escalate; loads the canonical shared core.
user-invocable: true
---

# tier-escalate - Claude entry point

Load [../core.md](../core.md) in full before acting.

## Claude bindings

- Unless `--skills-dir` is explicit, set `discovery_root` to the parent of this loaded package: the active `.claude/skills` discovery root. Do not search `.agents/skills`, `.github/skills`, or a consumer home unrelated to the loaded entrypoint.
- Map `isolated_readonly_task` to a fresh no-history Claude Agent/Explore invocation that has read-only tools. Pin every classification arm to the ordinary fan-out capability from the current workspace policy. Dispatch independent arms in parallel batches; never reuse a child or let it spawn graders.
- Locate policy by walking from cwd toward the filesystem root for the nearest `.claude/references/model-tiering.md`. An explicit `--policy` wins. Absence is reported, not repaired.
- Read each generated `SKILL.md` and its linked installed `core.md`; a launcher-only classification is invalid.
- Reproduce operator model-selection instructions as target-host instructions. Do not call `/model`, edit settings, or claim this invocation changed the model.
- Report an arm's actual model only from a host-supplied execution receipt. Otherwise report `UNKNOWN`.

Preserve the core's zero-write dry-run, evidence verification, verdict enums, artifact shape, and exact closing line. If isolated read-only agents are unavailable, return `required_tool_missing: classification-fan-out`.
