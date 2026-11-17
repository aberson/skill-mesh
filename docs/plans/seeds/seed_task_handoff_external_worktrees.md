# Seed: task-handoff can't find its library from worktrees outside the coding root, so lanes there save no lessons on close

Captured: 2026-11-14, from the you-asked-for-it project (central coordinator, a Claude Code window). Status: seed only. It grants no change to the task-state schema or any skill.

## What happened

At the end of a session the operator asked every lane to close (`/lane-close --all`). Two Codex lanes work in worktrees outside `<coding-root>`:
- combat-abilities in `C:/yat-ca15`;
- enemy-ai in `C:/yat-eai`.

Both are linked worktrees of the you-asked-for-it repository, whose main checkout is `<coding-root>/you-asked-for-it`. Short paths like these are deliberate, because Unreal's build tool fails past 260 characters.

Lane-close's SELF step 6 calls `session-wrap --end`, which calls `task-handoff --loop --no-commit`. In both lanes the preflight returned:

    Checkpoint not written: required_tool_missing (schema)

So neither lane wrote a session checkpoint, and neither saved its lessons. Their handovers say "no lesson or memory file was written". The operator noticed, because they expected every lane to save its lessons on close. Central harvested the lessons by hand from the handovers.

## Cause

task-handoff's § Library resolution walks outward through enclosing Git roots only. From `C:/yat-eai`, `git rev-parse --show-toplevel` is `C:/yat-eai`, and its parent `C:/` is not inside a Git work tree, so the walk stops. It never reaches `<coding-root>/.claude/references/task-state-schema.md` or the derive helper. A linked worktree's main checkout, and the coding root above it, are invisible to that walk.

## Proposal (for the skill-mesh maintainer to shape)

- Extend library resolution: when the walk from `--show-toplevel` finds no base, try the main worktree, `git rev-parse --path-format=absolute --git-common-dir` minus `.git`, and walk outward from there. Keep the rule that the schema doc and the helper come from one base.
- Session files still go under the lane's own `$root/.claude/task-state/` (scoped departure 1: never redirect state into another live worktree). Or document clearly where state goes for an external linked worktree.
- When the preflight fails inside lane-close, say plainly in the handover's Lessons section that lessons were not saved, and why. Lanes already do this informally; make it a locked line, so the coordinator can find it.

## Acceptance hints

- `task-handoff --loop` from `C:/yat-<lane>` (a linked worktree of a project under `<coding-root>`) resolves the library and writes the session file.
- `lane-close` in such a lane saves lessons through `session-wrap --end`, or reports the exact failure in the locked line.
- The preflight fails exactly as before for a repository that is truly unrelated to the coding root.

## Evidence

- you-asked-for-it Passing Notes handovers 20261114T183624Z-combat-abilities-to-central-1755 and 20261114T183736Z-enemy-ai-to-central-944d; both quote the preflight line.
- You-asked-for-it uses short worktree paths (`C:/yat-*`) by design: its AGENTS.md says "Keep the checkout path short (UBT fails past 260 characters)".

## Related gap found the same day: build-step cannot recognise a PowerShell test runner

In you-asked-for-it the declared primary test command is `powershell -NoProfile -File scripts/test.ps1` (bridge pytest plus the Unreal automation suite). build-step's Step 0 test-count check returned `recognized:false, reason:'no recognized runner'`, so `/build-step --reviewers code` halts with `required_tool_missing` before any developer or reviewer arm runs. The same applies to build-phase. Evidence: Passing Notes `20261115T132154Z-hardware-to-central-2d4c`. Interim workaround: the project treats C++ items as Direct task plus coordinator review and gate (you-asked-for-it `docs/lanes/README.md`, 'How lanes build', commit 61f25c4). Proposal: let a project declare its primary runner and a count-line pattern (for example in its instruction file or a small manifest), so build-step can gate on custom suites without weakening the mandatory DONE gate.
