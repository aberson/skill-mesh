# user-wrap - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. user-wrap owns ZERO triage logic: the orientation shape, the verdict, and the loss report stay owned by the contracts the core cites.
- Tier names in inherited procedures name capability ROLES. `config/model-tier-map.json` maps Claude tiers onto GPT peers and declares no Codex peer, so resolve a tier to the closest capability the configured Codex model actually provides; an explicit session model selection wins. If a required capability is unavailable, return `required_tool_missing` rather than weakening a gate.
- Invoke `session-wrap --advise`, bare `session-wrap`, `session-wrap --end`, and, on KEEP GOING, a plain Next Action only where the core's Step 4 allows it, exactly where the core's verdict table calls for them. A locked `task-handoff-next-action-v1` bundle is printed and held, never executed. A named-skill call here means resolving the installed `SKILL.md` and its referenced core, reading both in full, and following them in this session; the absence of a separate named-skill tool or slash-command API is not a missing capability. Re-present the `--advise` report verbatim and unmangled: triage line, banner, then loss report, with nothing inserted between and nothing paraphrased.
- Steps 1-3 stay read-only: read this session's task state as core Step 1 resolves it, plus quick git state, through Codex's shell/file tools; mutate nothing, and defer every mutation to the delegated skill per the verdict table. If the delegated run fails, report the failure and stop -- never fall back to a self-computed verdict.
- Session identity and context signals come only through the abstract session-I/O layer using Codex's own session conventions (the delegated session-wrap codex adapter owns that mapping); an unavailable signal is reported, not assumed benign. If the host exposes no stable session identity, Step 1 reads the schema fallback and KEEP GOING runs no Next Action (core Step 4); never fabricate or guess an identity to unlock it.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, preserve and report the actual error, then stop. Do not retry implicitly and do not switch providers. Never silently omit a core gate, and never compute a verdict locally because the delegated skill was unavailable.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
