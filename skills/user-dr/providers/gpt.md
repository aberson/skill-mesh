# user-dr - GPT entry point

See [../core.md](../core.md) for the full specification.

## GPT invocation differences

- Load the core in full before acting and preserve its plain-language rules, theme-first questions, conflict checks, recording limits and closing shape.
- Use structured filesystem and shell actions for discovery and read-only live-state checks. Where the host offers isolated read-only action children, run the core's source readers on them in parallel; otherwise use the core's in-session reading and say so.
- Ask for the project when the core's resolution does not yield exactly one.

## Known GPT limitations

- Claude session state, scratchpad paths and Artifact actions are unavailable unless an explicit adapter supplies them. Write reader briefs to a temporary directory outside the project, and never publish a hosted copy of the register.
- On a tool failure, preserve the actual error and mark dependent register rows unverified. Never infer an operator answer.

## Output normalization

Return only the core's register tables, consequence analysis, questions, document locator and closing report. Do not reveal hidden chain-of-thought. Preserve the closing shape exactly.
