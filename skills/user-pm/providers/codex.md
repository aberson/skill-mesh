# user-pm - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines. The PM-lens report shape (shipped / planned / next / could-cut) and its evidence bar stay exactly as the core states them.
- This skill uses no model tier and spawns nothing, so no tier resolution or router override applies. If a lookup capability is unavailable, follow the core's one-line degrade behavior rather than weakening its evidence bar.
- The overview is read-only project-axis work -- the core's sources only (plan docs, git history, archive markers) through Codex's own shell and file tools -- and runs natively. It runs no tests or builds, and every command it proposes is for the operator. Overnight-qualification stays a heuristic rendered as recommendation text, never as auto-dispatched work.
- The dev-observatory hook is the core's additive `--json` output mode only: it changes the rendering, not the sources. Do not read the observatory registry or snapshot to fill the overview; every move stays derivable from the plan, git log, and archive markers.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, preserve and report the actual error, stop only that failed lookup, mark dependent claims unverified, and continue the core's degraded report from available inputs. Do not retry implicitly and do not switch providers. Never silently omit a core gate or fill a section from assumption.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
