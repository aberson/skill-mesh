# user-fermize - Codex entry point

See [../core.md](../core.md) for the full specification. Load the core in full before acting.

## Codex invocation differences

- Use Codex's structured file and shell tools for the local read-only inspection permitted by the core. Use an available clock for its inspection bound.
- This workflow requires no subagent dispatch, named-skill dispatch, browser, or Claude-specific UI action. Follow the core's existing evidence/time fallbacks when tools or sources are unavailable; never simulate a missing capability or claim an inspection that did not occur.
- Keep the core's scope, gates, and advisory boundary unchanged. Return its plain-language Markdown report, source references, and optional text tree.

The generated discovery frontmatter is owned by Skill Mesh's distribution builder, using the authoritative manifest description. This source adapter is not an installed profile.
