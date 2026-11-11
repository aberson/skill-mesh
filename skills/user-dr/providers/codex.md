# user-dr - Codex entry point

See [../core.md](../core.md) for the full specification.

## Codex invocation differences

- Load the core in full before acting and follow it verbatim. This wrapper only maps host abstractions; it never weakens a gate the core defines. The plain-language rules, theme-first questions, conflict checks, recording limits and closing shape stay exactly as the core states them.
- Use Codex structured filesystem and shell calls for discovery and read-only live-state checks. This skill uses no model tier and no router hop.
- Fresh-context dispatch is a runtime host capability, not a provider-wide constant: a host that passes the separate build-step agent-isolation contract may map the core's parallel read-only source readers onto fresh sibling children; on a host that does not pass it, read the same batches in this session, write the same briefs and say so in the closing report, as the core documents. A missing required filesystem or shell tool returns `required_tool_missing`.
- Ask for the project when the core's resolution does not yield exactly one. Do not inspect the Skill Mesh checkout as a silent default.

## Known Codex limitations

- Claude session JSONL, scratchpad paths, Artifact actions, Claude Agent/Workflow tools, and Claude-only deep links are unavailable and are never simulated. Write reader briefs to a temporary directory outside the project.
- On a tool failure, preserve the actual error and mark dependent register rows unverified. Do not switch providers and never infer an operator answer.

## Output normalization

Return only the core's register tables, consequence analysis, questions, document locator and closing report. Do not reveal hidden chain-of-thought. Preserve the closing shape exactly.
