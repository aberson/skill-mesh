# user-pm - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell and git operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The report's sections, its sources and its evidence bar stay exactly as the core states them.
- This skill uses no model tier and spawns nothing, so no tier resolution or router override applies. If a lookup capability is unavailable, follow the core's one-line degrade behavior rather than weakening its evidence bar.
- The overview is read-only work that runs natively, through Codex's own shell and file tools: every source the core's steps name, including its `gh` and Passing Notes reads. It runs no tests or builds, and every command it proposes is for the operator. Overnight qualification and lane planning are recommendation text, never auto-dispatched work.
- Give each `gh` and `passing-notes` call the shell tool's own timeout, set to the core's numeric limit. When this run's sandbox blocks network access, the `gh` reads fail: that is the core's `gh`-unavailable case, so add its note and do not ask for escalated permissions. The Passing Notes calls only read the store and need no writable sandbox root; a command or store folder the sandbox cannot see is the core's absent case.
- A thread-limit or dispatch error that this window has already reported is observed evidence for the core's agent capacity check.
- The dev-observatory hook is the core's additive `--json` output mode only: it changes the rendering, not the sources. Do not read the observatory registry or snapshot to fill the overview.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, preserve and report the actual error, stop only that failed lookup, mark dependent claims unverified, and continue the core's degraded report from available inputs. Do not retry implicitly and do not switch providers. Never silently omit a core gate or fill a section from assumption.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
