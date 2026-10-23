# user-orient - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. Use Codex's structured tool/action calls for filesystem, shell, git, and named-skill operations. This wrapper only maps host abstractions; it never weakens a gate the core defines.
- This skill uses no model tier and spawns nothing, so no tier resolution or router override applies. If a lookup capability is unavailable, follow the core's Not-yet-verified behavior rather than weakening its evidence bar.
- This wrapper maps no isolated fresh-context agent primitive: this core requires no isolated arm, so run the work in this session.
- Step 1's asides are a SET of lookups, not a concurrency requirement. If the host cannot issue them in one batch, run them in the order the core lists and still withhold every finding until Step 2 -- the ordering gate ("do not output the findings yet") is the contract; parallelism is only an optimization.
- The orientation is operator-facing output only. The skill stays read-only: it writes no artifact, memory, plan, code, or git state.
- Normalize verbosity: do not reveal hidden chain-of-thought; return only required decisions, evidence, artifacts, commands, questions, and the core's closing report. Keep the six sections in the core's fixed order and its word-count targets.

## Known Codex limitations

- Claude Artifact actions, Claude session JSONL/scratchpad paths, the Claude Agent/Workflow tools, and Claude-only deep links are unavailable unless an explicit adapter supplies them. Use the core's standalone-file or durable-state fallback; never simulate the missing tool.
- On timeout, rate limit, provider 5xx, parse failure, or missing required adapter, preserve and report the actual error, stop only that failed lookup, mark dependent claims unverified, and continue the core's degraded report from available inputs. Do not retry implicitly and do not switch providers. Never silently omit a core gate or fill a section from assumption.

## Output normalization

Return only the core-defined operator-facing output and durable artifacts. Preserve locked strings, verdict enums, schemas, paths, command ordering, and retry limits exactly; reject missing required fields instead of inferring success.
