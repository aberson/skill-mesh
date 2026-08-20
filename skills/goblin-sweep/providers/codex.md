# goblin-sweep - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Run the three fail-loud prerequisite checks in order through Codex's shell tool (uv on PATH, the engine project directory exists under the resolved workspace root, `goblin sweep --help` exits 0). STOP on the FIRST failure exactly as the core specifies, naming the engine plan as remediation. Never continue past a failed check.
- Resolve `<workspace-root>` through Codex's own working-directory conventions and pin the invocation to the engine project by absolute path, so it runs from any cwd without a `cd`. Preserve the PowerShell-5.1-safe shapes of the core's snippets and their exact outputs.
- Parse the engine's `--json` output ONLY; never scrape its human-readable default output, and add no obligation-extraction, dedup, or atom-parsing logic -- all of that lives in the engine. On malformed JSON, stop with the core's malformed-output message rather than inventing obligations to fill the gap.
- Render exactly the seven locked fields per obligation, in the core's order, omitting the goal line entirely when `goal_condition` is null. An empty result is a valid engine answer and is reported plainly, distinct from a prerequisite failure.
- Codex needs no Agent/Workflow primitive here: the skill is one shell call plus a render.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate.

## Output normalization

Return only the core-defined operator-facing output: the seven locked fields per obligation and the closing `/goblin-do <obl-id>` next-rail line. Preserve locked strings, the `obl-<project>-<slug>` id shape, field order, and exit/stop behavior exactly; reject missing required fields instead of inferring success.
