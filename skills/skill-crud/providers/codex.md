# skill-crud - Codex entry point

See [../core.md](../core.md) for the full specification. Load the core in full before acting.

## Codex invocation differences

- Use Codex structured filesystem and shell calls for the core's Git, helper, generator, build and test commands. Run each command in the foreground and branch on its exit code.
- This core requires no isolated fresh-context agent, no named-skill dispatch, no model-tier resolution and no router hop, so this wrapper maps none of them. A missing required filesystem or shell tool returns `required_tool_missing`.
- Write the request file and the pre-write hash record to a disposable directory outside the repository, such as the system temporary directory.
- Keep the core's gate order, stop codes, edit boundary and caller-owned commit boundary unchanged. Never weaken a core gate.

## Known Codex limitations

- Claude Agent/Workflow tools, scratchpad paths and Artifact actions are not used by this skill and are never simulated.
- On a tool failure, preserve the actual error, apply the core's failure rule, and do not switch providers.

## Output normalization

Return only the core's report. Do not reveal hidden chain-of-thought.

The generated discovery frontmatter is owned by Skill Mesh's distribution builder, using the authoritative manifest description. This source adapter is not an installed profile.
