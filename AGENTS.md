# Skill Mesh Codex adapter

Load and follow `CLAUDE.md` in full. It is the shared project instruction source.

Use `plan.md` for current execution status. This adapter does not enumerate skills, select models,
or duplicate volatile project state.

Only generated Skill Mesh v2 profiles may execute; v1 archives and legacy launchers are never fallbacks. See `CLAUDE.md`.

**Testing rule (adopted 2026-11-12).** Per change, run the focused tests for what the change touches plus the quick repo-wide checks, and save the command, the files it selected and its summary line to a file. One full sweep runs per release, in the background, and is never started per step. `CLAUDE.md` (Key commands) owns the rule; it is not restated here.

Before a command likely to run over two minutes, say once what it is and how long it usually takes, or that you do not know. While it runs, wait as long as the host allows between checks, and write only when something changes: a stage ends, a failure appears, or it runs past twice the estimate. Call a step final only if nothing follows it. Never stop a running install or release to save time.

Skill edits here follow `documentation/skill-catalog-lifecycle.md`; do not load or run the host's built-in skill-creator.
