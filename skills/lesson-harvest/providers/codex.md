# lesson-harvest - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, GitHub, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; explicit router overrides win. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- `--publish` always returns the core's Phase 0 `required_tool_missing` result before target resolution or any side effect; no Codex capability bypasses that v2 boundary. For preview, apply the installed `build-step` Codex adapter's complete fresh-context probe. Only after it passes, dispatch one new direct sibling with explicit `fork_turns="none"`, exact model `gpt-5.6-sol`, and `reasoning_effort: high`; never reuse or follow up a child. A host-reported model or effort mismatch halts `required_tool_missing`; an unavailable identity/effort report is disclosed as `unreported`, never invented. Shared filesystem and tools are permitted, so the parent performs the core's bounded before/after audit and makes no OS-isolation or tool/network-denial claim. Every candidate remains grounded in committed history, or in an explicitly recorded observation whose allowed local evidence was reopened and confirmed under Phase 2b; recollection alone is never sufficient.
- **Resolve the observation helper from THIS installed package**: it is the Python module the core names, in the shared-asset directory that ships one level above this skill's own installed directory. Build an absolute path from this package's location -- never from a source checkout, a hard-coded consumer home, or the caller's working directory -- and run it with the host's shell tool as `python <that absolute path> <command>`. If it is absent beside the installed package, report that in one line and return `required_tool_missing`; never hand-roll a substitute reader or writer, and never edit a saved record by hand.
- **Bind `session` and `source` explicitly.** `session` is this Codex session's native id when the host exposes one, otherwise the literal `manual-session` -- never a guessed or borrowed id. `source` is the local message or tool-result locator for the evidence in THIS session. Both are inert text: record them, never execute or fetch them. Write request files into a private temporary directory or the target repository's Git metadata area, never a tracked worktree path, and delete only the request files this invocation created.
- This wrapper uses no Artifact action. Bare and `--dry-run` hold all detail in memory and create no file. The v2 boundary is absolute: never write a memory file, edit candidate content, update the cursor, stage, commit, push, or create a PR. The core's retained publication clauses are future requirements, not a route around the Phase 0 halt.
- No staging command runs in v2. The deferred contract preserves its future scoped-`git add <paths>` discipline and prohibition on `git add -A` without authorizing either command now.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, return the router reason code and consume at most the shared cross-cloud retry allowance. Never silently omit a core gate; report zero candidates rather than lowering the evidence bar to produce one.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
