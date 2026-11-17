---
name: skill-crud
description: Claude provider entry point for skill-crud; loads the canonical shared core.
user-invocable: true
argument: "Operation and skill name, for example: CREATE my-skill, or RENAME old-name new-name"
---

# skill-crud - Claude entry point

See [../core.md](../core.md) for the full specification. Load the core in full before acting.

## Provider-specific instructions

- Use Claude Code's file-reading, editing and shell tools for the core's Git, helper, generator, build and test commands. Run each command in the foreground and branch on its exit code.
- This core requires no Agent, Workflow or named-skill dispatch, no browser and no Artifact action.
- Write the request file and the pre-write hash record to a disposable directory outside the repository, such as the scratchpad directory.
- Keep the core's gate order, stop codes, edit boundary and caller-owned commit boundary unchanged. Never weaken a core gate.

## Output normalization

Return only the core's report. Do not reveal hidden chain-of-thought.
