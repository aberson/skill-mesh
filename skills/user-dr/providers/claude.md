---
name: user-dr
description: Claude provider entry point for user-dr; loads the canonical shared core.
user-invocable: true
argument: "Optional scope (a theme, a plan, or open only) and project path"
---

# user-dr - Claude entry point

See [../core.md](../core.md) for the full specification.

## Provider-specific instructions

- Load the core in full before acting and preserve its plain-language rules,
  theme-first questions, conflict checks, recording limits and closing shape.
- Use read-only file and shell tools for discovery and live-state checks. Use the
  Agent tool for the core's parallel read-only source readers; give each reader
  read-only tools and the scratchpad directory for its brief.
- Ask for the project when the core's resolution does not yield exactly one.
- Write only what the core's section 7 allows. Never commit, push, stage,
  publish a hosted Artifact, or start an item.

## Output normalization

Return only the core's register tables, consequence analysis, questions,
document locator and closing report. Do not reveal hidden chain-of-thought.

## Unsupported capabilities

If the Agent tool is unavailable, use the core's in-session reading and say so
in the closing report. Never weaken a core gate.
