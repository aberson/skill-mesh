# user-draft - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The checkpoint-before-drafting discipline, the goal-condition quality bar (concrete artifacts/criteria), and one-artifact-one-job stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- The Step 1 checkpoint is a named-skill call: load task-handoff's installed `SKILL.md`, its core, and the shared task-state schema in full, then run `--loop` through that skill's Codex same-session path, which owns session identity and the rollup helper. Obtain this session's identity the same way for the Step 1 gate; with no stable identity, skip Step 1. Never read-merge-write `current.md` (a derived rollup) or any session file yourself. Any task-handoff result other than `Checkpoint written.` means no checkpoint, and the artifact is emitted bare.
- The emitted draft is paste-ready TEXT for the window that will run it. Preserve the core's identity-bound, orientation-only preamble and never substitute `/task-handoff --resume`, the rollup, or a freshest-session lookup. The artifact is chat output; anything the core marks durable is written as a file and reported by path.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- Native Codex has no router or cross-cloud retry. A missing required tool or adapter returns `required_tool_missing`. If the Step 1 named-skill call times out, errors, or returns anything other than `Checkpoint written.`, follow the core's bare-artifact branch and report that no checkpoint was written; never retry the checkpoint automatically. Never silently omit a core gate or emit a self-orienting preamble the checkpoint did not actually earn.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
