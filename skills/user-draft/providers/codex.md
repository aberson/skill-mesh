# user-draft - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The checkpoint-before-drafting discipline, the goal-condition quality bar (concrete artifacts/criteria), and one-artifact-one-job stay exactly as the core states them.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- The task-state checkpoint reads and writes `<git-root>/.claude/task-state/current.md` as ordinary files through Codex's file tools, read-merge-write, exactly per the schema the core cites.
- The emitted draft is paste-ready TEXT for the window that will run it: reproduce its command lines verbatim -- including `/task-handoff --resume` and any host-window primitives the target window supplies -- and never rewrite them to claim this host arms or runs them. The artifact is chat output; anything the core marks durable is written as a file and reported by path.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate, and never emit a self-orienting preamble the checkpoint did not actually earn.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
