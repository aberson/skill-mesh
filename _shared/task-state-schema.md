# Task State Schema — `current.md`

> **Vendored into skill-mesh.** This is a copy of the workspace reference document of the
> same name, vendored into the shared payload (`_shared`) so that the skill cores citing it
> resolve inside a host discovery root rather than against a workspace directory no
> consumer home has.
> Two adaptations apply throughout: citations to workspace documents that are **not** part
> of this payload are rendered as plain names rather than links (their targets do not ship
> here), and the private *values* of three classes (operator-specific identifiers, issue
> and cron references, and harness-configuration paths) were removed or replaced with a
> de-identified description. That is what this notice claims and the whole of it: some
> references to those artifacts survive deliberately in de-identified form where the
> surrounding contract needs them, no class is certified exhaustively absent, and a
> residual is a defect to report rather than a contradiction of this notice. The per-file
> sign-off, recorded with the full list of link dispositions in this repository's Step 66
> decision record, is the only class-level authority.

**Owned file:** `<project-root>/.claude/task-state/sessions/<session-id>.md`
**Derived orientation view:** `<project-root>/.claude/task-state/current.md`
**Template:** `.claude/task-state/current.md.template`

## Path resolution

Always resolve via `git rev-parse --show-toplevel` before reading or writing. Never use
cwd-relative paths — inside a build-step worktree, cwd points to the worktree directory,
which is deleted on cleanup. Writes inside a worktree are silently lost.

```powershell
$gitRoot = git rev-parse --show-toplevel
# sessionId must already be established by the current host session identity contract.
if (-not $sessionId) { throw "own session identity unavailable" }
$statePath = "$gitRoot/.claude/task-state/sessions/$sessionId.md"
```

---

## Session identity

Per-session state files (`sessions/<session-id>.md`, introduced by the write-race fix — see
`docs/current-md-race-fix-plan.md`) are keyed by the
**harness session UUID** — the single identifier every actor in a session agrees on.

- **Skills (the model)** read it from the scratchpad directory path they are handed:
  `…\<project-slug>\<session-id>\scratchpad` — the parent-dir name is the UUID.
- **Hooks** read it from the JSON payload Claude Code pipes to them on stdin: the `session_id`
  field, or equivalently the basename of `transcript_path` (which is `<session-id>.jsonl`).

**Verified identical (2026-07-14):** the scratchpad-dir UUID matched exactly the
basename of the session transcript the harness had written for that same session. Claude Code
names transcripts `<session_id>.jsonl`, so the scratchpad UUID, the transcript basename, and the
hook `session_id` are one value — the skill-side and hook-side keys resolve to the same identity
with **no mapping table needed**.

**Fallback resolution order (hooks):** `session_id` from stdin → else
`basename(transcript_path, ".jsonl")` → else (no stdin at all) fall back to the derived rollup /
freshest session file rather than a session-specific read. Skills that cannot see a scratchpad
path may read fallback state for orientation only. A fallback is never proof of this
session identity: execute no Next Action and write, close, archive or release no session
state based on it. Never promote fallback fields into a new own-session checkpoint.
A child must not use an inherited parent identifier as its own; unsupported host identity
resolution stays unavailable instead of minting or guessing an identifier.

---

## Per-session model (current.md write-race fix)

**The actual write target is `sessions/<session-id>.md`, never the shared `current.md`.** Each
session owns its file exclusively (keyed by the session UUID — see § Session identity), so
concurrent windows never clobber each other; the cross-session lost-update is structurally
impossible. `current.md` is a **DERIVED rollup** — the freshest session's content wholesale
plus a one-line listing of the other active sessions — regenerated from `sessions/*.md` by
the workspace's task-state derive hook library (`Write-DerivedRollup`). It is a pure function of the
session files: a lost or raced write to `current.md` loses nothing, because the next
regeneration reproduces it.

**Both `sessions/*.md` and `current.md` are gitignored** session-local state (like
`handoff-prompt.md`). A routine `--loop` checkpoint therefore commits nothing. A durable
snapshot, if ever wanted, is taken at a low-concurrency moment (a milestone / `/user-afterparty`),
never per-wrap — this dissolves the commit race that ~6 concurrent `user-wrap`s would otherwise
cause.

**Readers read their OWN session file, not the rollup.** The resume/nudge hooks and
`task-handoff --resume` each run inside one session and resolve `sessions/<their-id>.md`
directly (fallback: rollup → freshest). The rollup exists for provenance, external readers
(dev-observatory scrapes it from disk), and the fresh-window fallback — not the hot path.

The `## File format` / `## Field definitions` / `## Write discipline` below describe the content
of a single state file; they apply verbatim to each `sessions/<id>.md`.

---

## File format

```markdown
# Task State — <task-type> <date>

**Task:** <skill-name> | <phase/step or bug description>
**Status:** IN_PROGRESS | BLOCKED | COMPLETE
**Session SHA:** <git short SHA at last write>
**Last written:** <ISO 8601 UTC timestamp — e.g. 2026-06-15T14:30:00Z>
**Active project:** <slug> (<abs-repo-path>)   <!-- optional; present only when /user-project has pinned. Preserve verbatim across every write. -->

## Completed
- [<sha>] <step or action>: <one-line result, test count if known>

## WIP
**Current:** <exact file:line or step being worked on>
**Approach:** <what is being tried right now>

## Dead Ends — Do Not Retry
- <approach in 5-10 words>: <why it failed — specific error or finding, not "didn't work">

## Critical Gotchas
- <fact>: <implication for current task — why it would take >10 min to re-derive>

## Key Files
- `<path>`: <why relevant to current task — what was learned>

## Parked
- <salvage pointer — TODO discovered but not filed, seed doc worth writing, finding not yet recorded>

## Next Action
<exact command or skill invocation — the single most important next step>
```

---

## Field definitions

| Field | When set | Overwrite or append |
|-------|----------|---------------------|
| **Task** | On first write | Overwrite only when task changes |
| **Status** | On every write | Overwrite |
| **Session SHA** | On every write | Overwrite (current `git rev-parse --short HEAD`) |
| **Last written** | On every write | Overwrite (UTC ISO 8601) |
| **Completed** | After each discrete action completes | Append only — never rewrite existing entries |
| **WIP.Current** | At start of each loop or iteration | Overwrite |
| **WIP.Approach** | At start of each loop or iteration | Overwrite |
| **Dead Ends** | When an approach is ruled out | Append only — never remove |
| **Critical Gotchas** | When non-obvious fact is discovered | Append only |
| **Key Files** | When file read reveals relevant structure | Append only |
| **Parked** | When a salvage item is parked rather than written (session-wrap decisions/salvage sweep) | Append on park; remove an entry only when it has been filed or written |
| **Next Action** | On every write | Overwrite |
| **Active project** | On `/user-project` pin (optional header field) | Overwrite on re-pin; **preserve verbatim across every other write** (this is why `/user-project`'s pin survives a `task-handoff --loop` checkpoint); remove only on `/user-project clear` |

---

## Write discipline

**Sections omitted when empty.** Do not include a section header with no entries.

**Append-only sections:** Completed, Dead Ends, Critical Gotchas, Key Files.
Once written, entries in these sections are never removed or edited — they are the
investigation history. A wrong hypothesis goes in Dead Ends; it stays there even after
the bug is fixed. Git history is the audit trail for each entry's provenance.

**Overwrite sections:** WIP (Current + Approach), Next Action, Status, Session SHA,
Last written. These represent the current state, not history.

**Write format — Dead Ends:**
```
- [approach in 5-10 words]: [specific error or finding — not "didn't work", say WHY]
```

**Write format — Gotchas:**
```
- [fact in one sentence]: [implication for current task]
```

**Write format — Completed:**
```
- [<sha>] <step or action>: <one-line result>
```

---

## Lifecycle

| Event | Action |
|-------|--------|
| Task starts (first skill write) | Create file from template; set Status: IN_PROGRESS |
| Loop iteration completes | `task-handoff --loop` — write `sessions/<id>.md` (overwrite WIP + Next Action, append Completed if step done), then `Write-DerivedRollup`; NO commit (gitignored) |
| Compaction fires (PreCompact hook) | Append `## Compaction Marker` (UTC timestamp + git SHA) to the active session's `sessions/<id>.md`, then regen the rollup |
| Task completes | `task-handoff --loop` with Status: COMPLETE |
| Task switch (next task, same window) | `task-handoff --next-task [label]` — durable boundary write (`sessions/<id>.md` + regen rollup; commit + push MEMORY.md + code only, NOT gitignored state), then keep working in-window |
| Session transition (`/session-wrap` routes `clear-next` / `end-window`) | Read-merge-write this file FIRST, then render `handoff-prompt.md` from it + the session decisions log (render-on-wrap — the render never precedes the write) |
| Session resumes | Read Last written timestamp; if within 8 hours, output "Resuming [Task]: [Status]" + Next Action |
| Fresh window after `end-window` | Operator pastes the Pick-up-here opener; the new session reads `handoff-prompt.md` (self-contained render), verifies git state first, then executes Next Action |
| Build-step worktree context | Use `--no-commit` flag to avoid double-commit with build-phase Step 2e |

---

## Rendered handoff — `handoff-prompt.md`

**File:** `<git-root>/.claude/task-state/handoff-prompt.md` — written by `/session-wrap`'s
`clear-next` and `end-window` routes.

- **A rendering, not a source.** Render the verified own-session file plus that
  session's decisions log, never the derived rollup or a foreign file. Checkpoint
  through task-handoff first; only its successful own-session write authorizes the
  render. Facts learned later require another successful own-session checkpoint.
  When checkpointing fails, report findings in the current conversation as unsaved;
  do not bypass the failure with direct task-state writes.
- **Untracked-on-purpose.** Both the source session state and render are gitignored;
  neither is a committed durable project artifact.
- **Staleness and ownership:** compare against the same verified own-session source,
  not the freshest rollup. A newer source or mismatched owner invalidates a render.
- **Content contract** is owned by session-wrap: self-containment, its rendering
  contract and behavioral invariants. Retain the source session identity when
  rendering and when handing off; a path or matching Git SHA alone proves no owner.
  Atomically render the exact `Owner session: <session-id>` marker and bind every
  pointer/opener to that same expected owner. A missing or mismatched marker means
  execute nothing and re-orient from the explicitly expected source without
  treating foreign/fallback state as current-session write authority. The shared
  render pathname alone is never an executable handoff capability.
- **Resume paths:** a hook with retained, verified own identity resolves that file
  first after clear/resume. Missing or changed identity allows orientation-only
  fallback; it never authorizes another session's Next Action. An explicit operator
  handoff may identify its source, but a generic rollup injection cannot substitute
  for that handoff. Hook/render wiring must be verified on the host; this schema
  amendment does not itself deploy hooks or prove their behavior.

---

## Staleness threshold

A selected session file or fallback orientation view is considered **stale** if `Last written` is more than **8 hours** before the
current UTC time. The SessionStart hook (`session-resume.ps1`) computes this and injects a
stale-banner variant ("state is N hours old -- verify against git before trusting Next Action";
ASCII `--` verbatim — the hook is ASCII-only, so grep gates must match `--`, not an em-dash)
instead of the normal block. The model-side backstop (hook absent) outputs
"No active task state found — starting fresh." and asks what to work on.

8 hours covers overnight pauses. Adjust in CLAUDE.md if the project's session cadence differs.

### Model-side resume backstop (hook silent)

The `SessionStart` hook (`session-resume.ps1`, matcher `compact|resume|clear` in the harness settings file) is the primary path; it no-ops only on **no git root** or **no
resolvable session state**. When its injection is absent (a fresh `startup`, no git root), the
model runs this backstop after any compaction (`/compact` or automatic) or `/clear`:

1. Locate this session's state: `git rev-parse --show-toplevel` for the git root, then read
   `<git-root>/.claude/task-state/sessions/<session-id>.md` (session UUID from the scratchpad
   path — see § Session identity; fall back to the derived `current.md` rollup, then the
   freshest `sessions/*.md`). All timestamps are UTC ISO 8601 — compare against UTC now.
2. If the file exists and `Last written:` is within **8 hours** (UTC — see the threshold above),
   read it immediately.
3. Retain whether the selected source belongs to this session's verified identity.
   Emit the resume echo from that source, labeling fallback state as orientation-only.
   A fallback read grants neither execution nor write authority and must not be promoted
   into an own-session checkpoint. Report that no owned resumable action was found.
4. Proceed without renewed confirmation only for a fresh, verified own-session plain
   Next Action already authorized by the operator and permitted by its owning contract.
   Never execute a fallback action. Preserve a `task-handoff-next-action-v1` bundle as
   data, report that its owning dispatcher is required, and do not execute or flatten it.
   A pending approval or failed prerequisite stays pending; an echo cannot clear it.

If state is absent or stale (> 8 hours UTC), report `"No active task state found — starting
fresh."` and ask what to work on. This backstop and the resume-echo behavioral rule are stubbed
in `CLAUDE.md` § Session Resume, which points here.

---

## Multi-level projects

One session-state directory per Git root:
- Workspace-level skills write only their own `dev/.claude/task-state/sessions/<id>.md`.
- Project-level work writes only its own `<project-root>/.claude/task-state/sessions/<id>.md`.
- The derive library alone regenerates each root's `current.md` orientation view.

Path resolution (`git rev-parse --show-toplevel`) naturally returns the correct root for
the active project when called from inside a project directory. Workspace-level work
resolves to `dev/`.
