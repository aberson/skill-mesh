# user-afterparty acceptance inputs

Small, sanitized source examples for the user-afterparty acceptance run (plan Step 131).
The operator never uses this directory in place: the preparation section of
[`docs/user-afterparty-effectiveness-acceptance.md`](../../../docs/user-afterparty-effectiveness-acceptance.md)
copies it into a new temporary directory, fills in the two placeholders, and creates the
Git metadata that cannot be committed here.

These files are inputs only. Nothing here states an expected verdict, and no test reads
them to grade the skill; the acceptance brief owns the expected observations, and a real
Codex session produces the results.

| Path | Becomes | Used by |
|---|---|---|
| `workspace/CLAUDE.md` | the workspace root's instruction file | every run (workspace resolution) |
| `workspace/gitignore.fixture` | the workspace's `.gitignore` | keeps reports, maps and worktrees untracked |
| `workspace/demo-project/CLAUDE.md` | the current project | every run (project resolution) |
| `workspace/second-project/CLAUDE.md` | a second active project | the `--all-projects` case |
| `workspace/docs/lessons-learned.md` | the long-form lessons file | the measurement cases |
| `workspace/routing/installed-offload-config.json` | the installed routing settings | the routing-difference case |
| `memory/` | a project memory directory outside every repository: `MEMORY.md` plus three feedback memories | the measurement and correction cases |
| `later-wrap/feedback_quote_gate_commands.md` | a later wrap's shorter rewrite of one memory | the later-wrap case |
| `task-state/prior-v1/` | a complete version-1 prior report carrying deferred and declined findings | the full, targeted, full carry-forward cases |
| `task-state/legacy/` | a report in the pre-version-1 shape | the legacy case |
| `task-state/interrupted/` | a version-1 report left `in-progress` | the interrupted case |
| `task-state/concurrent/` | two version-1 reports from overlapping runs that disagree on one finding | the conflict case |

Placeholders: `{{WORKSPACE}}` is replaced with the prepared workspace path and
`{{MEMORY}}` with the prepared memory directory, both in forward-slash form. The run IDs
and UUIDs are synthetic. The task-state sets are stored without a leading dot because this
repository ignores every `.claude/` path; preparation copies them into
`<workspace>/.claude/task-state/`.
