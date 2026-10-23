# NOTE: This is the canonical provider-independent contract. All provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/user-afterparty/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# user-afterparty

A THIN front door for the milestone-hygiene moment. The operator has just hit a
milestone — a phase shipped, a sprint closed, the month rolled over — and wants the
whole workspace-hygiene sweep run from one memorable place instead of remembering five
scattered skills. This skill composes existing contracts and owns ZERO hygiene logic of
its own; it only SEQUENCES the skills the workspace already has, via the Skill tool.

It promotes the monthly **sprint-wrap** ritual
(`../../../docs/seeds/seed_sprint_wrap.md` §B)
into an on-demand front door: afterparty is both what the `dev-sprint-wrap-monthly`
scheduled task fires AND what the operator runs at any milestone.

**The swept set** — each is an existing skill with its own owned contract; afterparty
never restates or reimplements it:

- **Autonomous (run unattended, in report mode, collected into ONE report):**
  - `tier-drift` — invoke [`/tier-escalate`](../tier-escalate/core.md) then
    [`/tier-offload`](../tier-offload/core.md) (both discovery-only; they write maps,
    never edit a skill), then diff the maps against live pins and report the deltas.
  - [`/lesson-harvest --dry-run`](../lesson-harvest/core.md) — un-codified regressions
    from recent history. **`--dry-run` is mandatory here:** bare lesson-harvest opens a
    draft PR (mutating); afterparty runs it report-only.
  - [`/context-slim`](../context-slim/providers/claude.md) — auto-loaded-context audit, bare
    (report-only by default).
  - `meta-tool-prune` — list the usage-logging meta-tools due for their periodic prune
    (workspace instructions, Working rules); report-first, each prune confirmed later.
- **Conversational (WALKED one at a time, yielding at each skill's own gate):**
  - [`/memory-distill`](../memory-distill/core.md) — post-mortem of recent feedback
    memories (**formerly `/review-memories`** — the swept set uses the new name).
  - [`/test-prune`](../test-prune/core.md) — redundant/mock-theater test triage.
  - [`/plan-trim`](../plan-trim/core.md) — cut/fold plan cruft.

It additionally owns two orphans with no other home — **orphan-owner duties** (workspace
stray / orphan-worktree cleanup) and the **current.md rollup commit/archive seam** — each
filled by a later build step (Steps 3-4 below).

**Pinned posture: SEQUENCE, DON'T REIMPLEMENT.** Per the workspace meta-tooling rule
(workspace instructions, Working rules: cheapest artifact that removes a named friction),
afterparty is glue. Any hygiene logic authored here that a swept skill already owns — a
lesson-detection heuristic, a test-triage rule, a plan-cut policy, a context-audit pass — is
a DEFECT. afterparty
invokes, collects, sequences, and reports; it decides nothing the chained skills decide.

**Report-first / apply-on-confirm.** Normal-mode report persistence is invocation-owned
bookkeeping; every change to a hygiene target still requires the operator's per-skill or
per-item go-ahead. The confirmation points in a run are the 3 conversational skills' OWN
gates plus the per-item go-aheads that afterparty's own Steps 3-4 already require before any
delete, archive move, or commit (each item is listed first and never acted on unasked).
afterparty adds no bare `(y/n)` gate of its own (autonomous-by-default); under `--dry-run`
there is nothing to confirm.

---

## When to use / when NOT to use

**Use** at a milestone or any time the workspace wants a tidy: "run the sweep", "milestone
hygiene", "workspace cleanup", "afterparty", "sprint wrap", "tidy up the workspace". Also
the target of the monthly `dev-sprint-wrap-monthly` scheduled task.

**Do NOT use:**

- **Wrapping a single session / a transition moment** (task boundary, heavy context, end
  of day) → bare [`/session-wrap`](../session-wrap/core.md). afterparty is workspace
  hygiene across projects, not this-session state.
- **The sit-back-down verdict** ("keep going or wrap up?") → [`/user-wrap`](../user-wrap/core.md).
- **One hygiene skill in isolation** → invoke that skill directly. afterparty earns its
  overhead only when you want the whole sweep.

---

## The swept set (interface map)

Verified invocation facts for the 5 skills afterparty chains — state them accurately so a
fresh-context model chains them correctly. Each skill owns its own behavior; this table is
afterparty's read of that contract, not a second copy of it.

| Skill | Invocation | Bare default | Interactivity | Scope | Output |
|---|---|---|---|---|---|
| `lesson-harvest` | `/lesson-harvest [--dry-run] [--since <sha>]` | MUTATE (opens draft PR); `--dry-run` = report-only | **autonomous** | workspace | draft PR `memory/harvest-<date>` + `.claude/task-state/.last-harvest-sha` |
| `context-slim` | `/context-slim [--project <p>] [--apply]` | **REPORT** only | **autonomous** | per-project | stdout report; `--apply` edits-in-tree |
| `memory-distill` | `/memory-distill` | mutate-on-approval, per round | **conversational** | per-project memory | edits `feedback_*.md` + `MEMORY.md` |
| `test-prune` | `/test-prune` | REPORT until confirm | **conversational** | per-project | triage table → edits-in-tree on confirm |
| `plan-trim` | `/plan-trim` | investigate → confirm → mutate | **conversational** | per-project | plan-doc edits + commit |

The two non-skill workspace items — `tier-drift` (runs `/tier-escalate` + `/tier-offload`,
both discovery-only) and `meta-tool-prune` (a list-what's-due pass) — are report-only and
carry no gate.

---

## Default scope and flags

**Default scope** (no flags):

- **Workspace-wide items — ALWAYS run, once:** `tier-drift`, `lesson-harvest`,
  `meta-tool-prune`, `orphan-cleanup` (Step 3), `rollup-commit` (Step 4).
- **Per-project items — the CURRENT project only:** `context-slim`, `memory-distill`,
  `test-prune`, `plan-trim`. **"Current project" = the nearest ancestor directory of cwd
  that contains a CLAUDE.md** — the same resolution `context-slim` itself already uses —
  NOT the cwd's git root. Monorepo sub-projects with no nested `.git` (`switchboard`,
  `dev-observatory`, `songs`) would resolve to the whole `dev/` workspace under a
  git-root definition; the CLAUDE.md-ancestor walk correctly isolates the sub-project.
- **Workspace root (`<workspace>`) — the anchor for every workspace-wide item.** From the
  current project, keep walking up while the parent directory also contains a CLAUDE.md;
  the topmost such directory is `<workspace>` (the same dev-root stop rule `context-slim`
  uses). Resolve it ONCE, in Step 0, as an absolute path. Workspace-wide items never use the
  ambient cwd: a run started inside a sub-project, or an `--all-projects` walk that has
  moved cwd, still scans, regenerates, and commits at `<workspace>`. If cwd has NO
  CLAUDE.md ancestor, `<workspace>` is `unresolved`: skip `orphan-cleanup` and
  `rollup-commit` with a one-line note each (`<item>: no CLAUDE.md ancestor -- workspace
  unresolved, skipped`) and never fall back to cwd or a drive root for them; the report-only
  workspace items (`tier-drift`, `lesson-harvest`, `meta-tool-prune`) run from cwd, as before.
- **Path form.** Bash blocks (Step 3) write `<workspace>`, `<path>`, `<wt>` and
  `<owning-repo>` as forward-slash absolute paths (`<drive>:/path/...`; in Git Bash `cygpath -m -a`
  converts and normalizes, elsewhere `realpath -m`), always inside double quotes, with any glob left OUTSIDE the quotes
  (`"<workspace>"/worktree_*`). Never paste a backslash Windows path into bash: it collapses
  (a backslash-form drive path loses separators) and a scan silently finds nothing. PowerShell blocks
  (Step 4) write the same absolute path inside single quotes.

**Flags:**

- **`--only <csv>`** — run only the named swept items (e.g. `--only lesson-harvest,context-slim`).
- **`--skip <csv>`** — run everything EXCEPT the named items (e.g. `--skip test-prune`).
  Item names are the swept-set identifiers: `tier-drift`, `lesson-harvest`, `context-slim`,
  `meta-tool-prune`, `memory-distill`, `test-prune`, `plan-trim`, `orphan-cleanup`,
  `rollup-commit`. `--only` and `--skip` are mutually exclusive; if both are given, `--only`
  wins and a one-line note says so.
- **`--dry-run`** — applies NOTHING anywhere. Forward `--dry-run` to both tier skills and
  to `lesson-harvest`; do not create their maps/config, the afterparty report, a directory,
  snapshot, rollup, archive move, deletion, or commit. The other autonomous items only report;
  the conversational items are teed up (afterparty lists what each WOULD review) but are
  never invoked into their apply/confirm phase; orphan-cleanup lists but never deletes; the
  rollup seam runs report-only (Step 4's detection + a `Get-DerivedRollup` preview + a
  listing of archive candidates — no regen-write, no archive move, no force-add/commit).
  Every selected autonomous result is printed in the preview, including truthful unavailable
  or failed outcomes; no durable report or child output is claimed.
- **`--all-projects`** — fans the per-project items (`context-slim`, `memory-distill`,
  `test-prune`, `plan-trim`) across the MEMORY.md active-project list instead of the
  current project only. Workspace-wide items still run once. Each item's targeting
  mechanism (there is no shared switch — use each skill's own contract; invocation detail
  lives in Step 1 / Step 2):
  - `context-slim` owns a `--project <name-or-path>` flag — invoke `/context-slim
    --project <p>` once per active project. NEVER bare in this loop: a bare call always
    re-audits the ambient cwd project regardless of loop position, so N bare calls
    silently produce N duplicate reports for the same project instead of N distinct ones.
  - `memory-distill` / `test-prune` / `plan-trim` own NO project flag (verified against
    each skill's canonical core) — they are cwd-scoped only. Target them by setting cwd to
    each project's root (the nearest ancestor with a CLAUDE.md, per the "current project"
    definition above) before invoking each via the Skill tool, once per active project.

---

## Steps

### Step 0 — resolve scope + flags, announce the plan

Resolve the swept set from the flags (default scope above; apply `--only`/`--skip`;
mutually-exclusive note if both). Resolve `<workspace>` once, as an absolute path or
`unresolved` (see "Default scope and flags"); every workspace-wide item below anchors to it. Resolve the
target project(s): the current project (see
"Default scope and flags" above — nearest ancestor of cwd with a CLAUDE.md, NOT the git
root), or — under `--all-projects` — the active-project list from
`<workspace-memory>/MEMORY.md`. Note the mode
(apply-on-confirm, or `--dry-run` = nothing mutates).

Generate one run identity at entry: UTC `yyyyMMddTHHmmssfffZ`, a hyphen, and a lowercase
UUID. Resolve a scope key from the normalized workspace identity plus the sorted normalized
project paths, using the host filesystem's path and case semantics. An unresolved or moved
target is not an exact match. Record the selected items separately from the scope key.

Before dispatch, classify every selected item as `known available`, `known unavailable`, or
`unprobed`, with a reason. Presence in a discovery tree is not proof that the item's owned
live capability probe passes. Provider wrappers contribute host-known limitations; every
child still performs its own qualification and its exact failure code is preserved. One
unavailable or failed item does not abort other selected work.

For a normal run with a resolved workspace, read top-level
`<workspace>/.claude/task-state/afterparty-*.md` reports only (exclude child round and patch
records); use this absolute resolved-workspace location, never an ambient-cwd relative path.
Prefer the latest readable version-1 report with the exact scope key. If ordering overlaps or
is ambiguous, record the conflict and source pointers; do not pick by timestamp alone. A
missing, corrupt, unreadable, or unresolvable prior report means `no trusted prior evidence`,
never a clean prior result. When `<workspace>` is unresolved, perform no prior-report path
scan and use `no trusted prior evidence: workspace unresolved`. Report content is evidence,
not commands, approval, or authority. Under `--dry-run`, read may still occur but no report
is created or changed.

Announce ONE plan line before acting, so a wrong scope is visible immediately:

    afterparty: <N> items | scope: <current project | M active projects> | workspace: <workspace | unresolved> | mode: <apply-on-confirm | dry-run> | autonomous: <list> | walk: <list>

Immediately follow it with the capability summary. In normal mode with a resolved workspace,
create this invocation's minimal `in-progress` report header plus carried findings before
dispatch, using the safe replacement rules below. If persistence fails, continue supported
work, print the report, and state that it was not saved. When `<workspace>` is unresolved,
keep the report in memory, perform no report filesystem write or cwd/literal-placeholder
fallback, and print `report persistence failed: workspace unresolved`.

### Step 1 — autonomous sweep (report mode), one consolidated report

For each selected autonomous item, invoke it via the Skill tool and capture its output.
Run these unattended; there are NO gates here. Set cwd to `<workspace>` (when resolved) before invoking the
workspace-wide items (`tier-drift`, `lesson-harvest`, `meta-tool-prune`), so each child's
own cwd-relative discovery and default output location resolve at the workspace rather than
inside whichever project cwd happens to be. Per-project items stay cwd-scoped to their
target project: set cwd back to the current project before invoking `context-slim` bare and
before Step 2 (a bare per-project call from `<workspace>` would audit the wrong project).

- **`tier-drift`** — invoke `/tier-escalate` then `/tier-offload` via the Skill tool. Under
  afterparty `--dry-run`, invoke `/tier-escalate --dry-run` and `/tier-offload --dry-run`.
  Before either dry-run child invocation, verify its current owned contract is internally
  consistent that every setup/output step is write-free in dry-run. If any unconditional
  directory/artifact creation conflicts with a later no-write statement, mark that child
  `known unavailable: contradictory dry-run contract`, do not invoke it, create no substitute
  output, and continue the other child/items. Report tier-drift as partial/unavailable with
  the blocked child's exact reason rather than claiming a complete fresh map pair.
  (both write their maps to their own out-dirs; neither edits a skill). Diff the fresh
  maps against the live pins and report the deltas (new/changed skills since the last
  cycle). Report-only — APPLYING any pin delta is a separate confirmed follow-up, never
  automatic.
- **`lesson-harvest`** — invoke `/lesson-harvest --dry-run` via the Skill tool. The
  `--dry-run` is load-bearing: it prints the report + the draft-PR body and creates
  nothing. Capture the candidate count and the report pointer.
- **`context-slim`** — invoke via the Skill tool: bare for the current project, or —
  under `--all-projects` — once per active project with `/context-slim --project <p>`
  (never bare inside the loop; see the `--all-projects` targeting mechanism above).
  Report-only. Capture the top-priority stub/extract/prune recommendations per project.
- **`meta-tool-prune`** — list the usage-logging meta-tools due for their periodic prune
  (workspace instructions, Working rules). Report which are due; each actual prune is
  confirmed later, never auto-run.

Collect all of the above into ONE consolidated hygiene report (shape below). Per
`<repo>/_shared/subagent-economy.md`: keep each captured
result to its load-bearing verdict + counts + a pointer to the skill's full output — do
not inline the full dumps.

### Step 2 — conversational walk (one skill at a time)

Walk the selected conversational items in order (`memory-distill` → `test-prune` →
`plan-trim`), ONE AT A TIME:

1. Invoke the skill via the Skill tool.
2. YIELD to the operator at that skill's own confirmation gate. Do NOT answer for them, do
   NOT force-decide, do NOT auto-confirm — the whole point of the autonomous/conversational
   split is that these three need the operator's judgment.
3. Resume to the next item only after the operator finishes the current one.

Never batch them and never collapse two gates into one. Under `--all-projects`, walk each
per-project item across each active project from the MEMORY.md list: none of the three
own a project flag (see the `--all-projects` targeting mechanism above), so set cwd to
that project's root (nearest ancestor with a CLAUDE.md) BEFORE invoking the skill via the
Skill tool, then move cwd to the next project before its turn — still one skill, one
project, one gate at a time. Under `--dry-run`, tee each up (state what it WOULD review)
but do NOT invoke it into its apply phase.

### Run report, measurement, and finding contract

Normal mode owns one local Markdown record at
`<workspace>/.claude/task-state/afterparty-<run-id>.md`. It is not a session record, queue,
or `current.md` writer and must never be force-added to Git. Keep one top-level record and
link child evidence rather than copying private memory content or full child dumps.

The record has labeled fields for `report-kind: user-afterparty`, `report-version: 1`, run
ID, start/end UTC, host, lifecycle (`in-progress`, `complete`, or `interrupted`), scope key,
workspace/project scope, selected items, mode, source revision when available, last completed
item/evidence pointer, and the selected prior report. A successful selection records both its
absolute locator and its report identity/run ID; otherwise record `none`, `ambiguous`, or
`unreadable` with reason. `complete` means orchestration terminated; it does not mean every
item passed.
Include four compact tables:

- **Measurements:** target path, category, entry/exit logical lines and normalized Unicode
  code points, entry/exit SHA-256, delta, attribution/evidence, and validity note.
- **Outcomes:** item/project, capability status, execution outcome, evidenced inspected /
  candidate / applied counts, disposition summary, reason, and child evidence pointer.
- **Findings:** stable finding ID, concise problem, evidence/source version, owner and next
  action, disposition/reason, revisit trigger, and last checked run.
- **Limits/next action:** unavailable coverage, unmeasured effort/spend, pending owner
  handoffs, and one useful existing targeted invocation or next action.

Execution outcome is one of `completed`, `not-run`, `unavailable`, or `failed`; disposition
is separately one of `proposed`, `retained`, `deferred`, `declined`, or `resolved`. A completed
scan can have candidates and zero applied actions. Dry-run conversational items are
`not-run` previews. Never convert unavailable/unprobed into passing coverage. `deferred`
needs a reason, owner/next action, and concrete revisit event; `declined` remains declined
until its premise changes; `retained` is an intentional keep; `resolved` requires current
owner evidence.

A new finding gets `<origin-run-id>/F<n>` with a positive ordinal. Carry that identity,
evidence, owner, and disposition unchanged when a later scan repeats it; reuse an existing
issue or seed and do not open one automatically. Carry unresolved/deferred/declined findings
for every prior item, marking an unselected item `outside this run's selection`. Only selected
items are dispatched or revalidated. A legacy finding is imported only when its scope,
evidence, and owner are unambiguous; retain its source pointer and use unknown for its prior
numeric baseline. Carry-forward never suppresses a selected scan or authorizes follow-up work.

Measure only the resolved memory index and explicit memory/lesson files relevant to selected
memory work. If a child selects files later, capture those files immediately before its
approved mutation and label that boundary. Do not recursively inventory workspace memories.
For each text file, read original bytes for SHA-256; separately decode UTF-8 strictly, remove
one leading BOM, normalize CRLF and CR to LF, count Unicode code points, and count logical
lines (empty text is zero; a terminal newline adds no empty line). Access/decoding failure is
`unavailable`. Keep the memory index, feedback files, and long-form lessons in separate rows
and totals. Missing prior data is unknown, except a file demonstrably created/deleted by this
run may use a verified zero at the absent boundary. Changed selection is not an aggregate
shrink comparison.

Take exit measurements before returning. Attribute an edit only when child result/patch and
before/after identities support it; otherwise label the delta unattributed or affected by
concurrent edits. Later wrap work belongs to that stage. Lines/characters are storage
measures, never tokens or savings, and absent trustworthy host data means effort/spend is
`not measured`.

For every normal-mode update, write complete candidate bytes beside this run's report, flush
and close them, then replace only this run's file. Never overwrite a prior run. On any staging
or replacement failure, retain the last readable version, continue supported work, and print
`report persistence failed: <reason>`; never claim a saved path. A fresh run may carry findings
from an interrupted record but cannot use it as a completed numeric comparison. Under
`--dry-run`, hold this entire structure in memory and print it only.

### Step 3 — orphan-owner duties (workspace stray / orphan-worktree cleanup)

Workspace-wide, report-first, anchored at `<workspace>` (never the ambient cwd).
Registry-checked detection of orphaned `worktree_*` dirs
(rule owned by `<repo>/_shared/worktree-hygiene.md`
§4) plus task-state stray triage; list for confirmation, never auto-`rm`. Note: the
command blocks in this step are POSIX/bash (Git Bash / the Bash tool) — `ls -d`,
`2>/dev/null`, `du -sh`, `cat <wt>/.git`, and `git check-ignore` are bash idioms, run them
there even though the operator's default shell is PowerShell. Write every path in the
"Path form" above (forward-slash absolute, double-quoted, globs outside the quotes). Before
any scan, confirm the anchor exists: if `test -d "<workspace>"` fails, report
`orphan-cleanup: workspace path not found (<workspace>) -- skipped`, never a zero-candidate
"no orphans" result.

**Duty 1 — orphaned `worktree_*` dirs (report-first, delete-on-confirm-only).** The
AUTHORITATIVE orphan signal is a per-candidate, format-independent GITDIR-METADATA check —
NOT a string-diff of `git worktree list` against an `ls` listing. The two print different
path formats (`git worktree list` prints normalized absolute forward-slash paths, e.g.
`~/worktree_foo`; the `ls -d` below prints the parent-level ones with the literal,
unnormalized `<workspace>/../` prefix), so comparing them as raw strings never matches and
will over-flag live worktrees as orphans (the per-item precondition below normalizes before
it compares). Treat `git worktree list` as
INFORMATIONAL context (git's own live registry, NOT the observatory `registry.toml` — do
not consult registry.toml here) alongside the on-disk candidates, never as the pass/fail
test itself. `/build-step` creates these one level ABOVE the dev/ root (`../worktree_*`,
i.e. `~\worktree_*`); §4 also sees them at the dev/ root (`dev/worktree_*`).
Scan BOTH locations:

    test -d "<workspace>" || echo "workspace path not found"   # guard: skip, never a false-clean scan
    git -C "<workspace>" worktree list             # git's own registry -- context only
    ls -d "<workspace>"/../worktree_* "<workspace>"/worktree_* 2>/dev/null   # on-disk candidates, BOTH locations
    git -C "<workspace>" worktree prune -n -v      # DRY-RUN listing; mutates nothing

`git worktree prune` reconciles the OPPOSITE direction from what this duty targets: it
removes registry entries whose on-disk dir is GONE. The husk case this duty targets is the
reverse (on-disk dir PRESENT, registry entry already gone), so prune typically has nothing
to act on for these candidates — it tidies dangling registry metadata, it does not remove
an on-disk husk. `rm -rf` (after corroboration below) is what reclaims a husk. afterparty
never runs a REAL (non-dry-run) `git worktree prune`: reconciling a registry entry is the
operator's manual action (Block A below), and nothing runs during this detection pass or
under `--dry-run`.

For EVERY on-disk `worktree_*` candidate, inspect authoritative metadata BEFORE any recursive
size walk. The `.git`
pointer names the candidate's OWNING repo: `<owning-repo>` is the path before
`/.git/worktrees/<name>`, and it is often a nested project repo rather than `<workspace>`
(a `/build-step` worktree belongs to the project it was cut from):

    cat "<wt>/.git" 2>/dev/null                               # gitdir line: <owning-repo>/.git/worktrees/<name>
    ls -d "<owning-repo>/.git/worktrees/<name>" 2>/dev/null   # absent output: gitdir metadata is gone
    # run du -sh "<wt>" only after the metadata rules below classify a plausible husk

A `<wt>/.git` that is a DIRECTORY (`test -d "<wt>/.git"`) marks an independent repository,
not a linked worktree: it is never a candidate here, whatever its name. Otherwise a
candidate is a confirmed ORPHAN HUSK iff it has NO `.git` file, OR its `.git` gitdir
pointer targets a `<owning-repo>/.git/worktrees/<name>` directory that no longer exists. A live
gitdir target disqualifies the candidate from recursive sizing. Unreadable or uncertain metadata
is `unknown` and is not sized. Only a plausible husk gets one `du -sh "<wt>"` estimate; if none
qualify, report zero plausible reclaim candidates and zero recursive size walks. LIST every
orphan candidate as one row — path, estimated size (or `unknown`), owner (`<owning-repo>`; `missing: <owning-repo>`
when the pointer names a repo directory that no longer exists; `unresolved` when there is no
`.git` file), reason (gitdir file absent, or gitdir target directory gone).
NEVER auto-`rm`; under `--dry-run` stop here (list only, touch nothing).

**Hard safety precondition — re-check per item, immediately before touching `<path>`.**
Re-run both checks fresh, for the SPECIFIC `<path>` about to be acted on, right before
acting on it:

- (a) is `<path>` ABSENT from EVERY registry in the scan set? The scan set is the
  `<workspace>` repo, every repository nested under it to the `find` bound below, and the
  row's `<owning-repo>` when that directory exists:

      find "<workspace>" -mindepth 1 -maxdepth 3 -name .git -type d -prune   # each hit's parent directory is a repo in the scan set; keep its exit status and stderr
      git -C "<repo>" worktree list --porcelain     # once per scan-set repo; collect its `worktree <abs-path>` lines
      cygpath -m -a "<path>"                        # the candidate's normalized absolute form (realpath -m outside Git Bash)

  Compare the normalized `<path>` with each `worktree` line's path exactly (trailing `/`
  trimmed, case-insensitive on Windows); never compare against `ls` output. Each of these
  commands fails toward "absent", so each failure below is an UNCLEAN reading, never
  "absent": STOP for this `<path>` with the verdict shown.
  - A registry command exits non-zero, prints no `worktree` line, or its first normalized
    porcelain `worktree` path does not equal the normalized `<repo>` path (Git may otherwise
    walk up from an invalid `.git` directory):
    `keep — registry unreadable: <repo> (manual)`.
  - The normalization exits non-zero or prints nothing:
    `keep — path not normalizable: <path> (manual)`.
  - The scan set is INCOMPLETE (`find` exits non-zero or reports a directory it could not
    read) and the row's owner is `missing` or `unresolved`:
    `keep — scan set incomplete: <dir> (manual)`, naming an unreadable directory from
    `find`'s stderr, or `find`'s exit status when it names none.

  A `missing` or `unresolved` owner contributes no authoritative registry reading of its own
  (never run `git -C` on a missing directory and read its empty output as "absent"). Such a
  row can NEVER pass (a) or reach Block B from a bounded negative scan: verdict
  `keep — owner missing or unresolved (manual recovery)`, even when the scan set is complete.
  Only a positively identified, existing owner whose registry reads cleanly can qualify for
  deletion. A row whose `<owning-repo>` exists is not stopped by an incomplete
  scan set: the repository its own `.git` pointer names, and `<workspace>`, are read
  directly rather than found by `find`, so the row is still checked against the repository
  that registered it; its outcome records `scan set incomplete: <dir>`. A repository
  outside the scan set (outside `<workspace>`, or nested deeper than the bound) is not
  consulted.
- (b) is its gitdir metadata `<owning-repo>/.git/worktrees/<name>` absent (or the `.git`
  file itself absent; a `.git` DIRECTORY never counts as absent)?

BOTH must hold for `<path>` to be a confirmed husk. If (a) does NOT hold — a scan-set
registry still lists `<path>` (that registry's repo is its owner) — it is NOT an orphan
husk; it is at most a still-tracked, locked tree (the §4 failure mode where a prior
`git worktree remove` half-failed, e.g. a file lock). NEVER run `rm -rf` on it. If neither
reading is clean, STOP — do not remove anything for this `<path>`.

ONLY on explicit, per-item operator confirmation, act on `<path>`'s corroborated class from
the precondition above — never run Block B against a Block A row:

Block A — still-tracked tree (precondition (a) failed: a scan-set registry still lists
`<path>`, while (b) held). Destroying a registered worktree is governed IN FULL by
`<repo>/_shared/worktree-hygiene.md` §3. Its commit checks could run from the registering
repo, but its mandatory `git -C <worktree> status --porcelain` needs the tree's own `.git`
link to its metadata. A Block A row has no usable `.git` file — that is why Duty 1 listed
it — so `git -C "<path>"` walks up to a parent repo or errors, and the tree's uncommitted
state cannot be verified; a tree repaired since listing fails (b) and has already stopped
above. afterparty therefore never removes a registered tree. The row's verdict is
`keep — registered, not verifiable (manual)`; show the registering repo and that entry's
porcelain `HEAD`/`branch` (or `detached`) lines — the tree's own commit, never the
registering repo's main-checkout `HEAD` — and remove nothing. Reconciling the entry (§3
checks, rescue of any dirty state to a pushed branch, then `git -C "<owning-repo>" worktree
remove`/`prune`) is the operator's manual action; afterparty never commits, pushes, or
force-removes inside or for a registered worktree.

Block B — confirmed true husk (precondition BOTH (a) and (b) held for this `<path>`; no
scan-set registry has an entry left, so `git worktree remove` here would be a no-op).
Reclaim directly, as its own separately-confirmed step, only after the husk corroboration
above passed for THIS `<path>`. Show any `scan set incomplete: <dir>` note beside this row's
go-ahead as well as in the final outcome. Resolve the candidate and workspace paths again at
action time, normalize them, and require the candidate to be contained by exactly one of the
two allowed roots: `<workspace>/worktree_*` or the sibling `<workspace>/../worktree_*` naming
pattern. Reject equality with either root, any parent traversal, root/drive target, symlink or
reparse escape, and any target outside those resolved roots. Re-run (a), (b), and the metadata
classification after containment.

The per-item approval must name the normalized path and bind the exact current evidence shown
to the operator: `.git` pointer bytes/hash or verified absence, resolved owner/metadata path,
registry readings, containment roots, and size estimate timestamp. If any bound byte or reading
changes before execution, the approval is stale: keep the path, show the new evidence, and ask
for a new item-specific go-ahead. Prior findings, estimates, or approvals never authorize the
new state.

    cd "<workspace>"
    rm -rf -- "<path>"

**Duty 2 — task-state stray triage (gitignore-vs-keep, report-first).** Per the shipped
current.md write-race fix, `.claude/task-state/current.md`, `sessions/`, and intake are
GITIGNORED and `current.md` is a DERIVED rollup (never hand-edited). Two stray classes
accumulate: leftover `.plan-expedite-state.*` files at the dev/ root (~14 old
completed/stale ones) and stale `sessions/*.md` from long-dead sessions. List them, and
confirm each is gitignored before proposing it (a match means removal loses no tracked
content):

    ls -la "<workspace>"/.plan-expedite-state.* 2>/dev/null
    ls -la "<workspace>"/.claude/task-state/sessions/*.md 2>/dev/null
    git -C "<workspace>" check-ignore -v "<path>"    # a match: gitignored, safe-to-archive class
    grep -l '^\*\*Status:\*\* COMPLETE' "<workspace>"/.claude/task-state/sessions/*.md 2>/dev/null   # COMPLETE-marked sessions

Classify each stray with a SUGGESTED verdict — never blind-delete. Delete vocabulary in this
duty applies ONLY to `.plan-expedite-state.*`; no path through `sessions/*.md` here is a
delete candidate:

- `.plan-expedite-state.*` — the filename encodes state: `.completed-*` / `.stale-*`
  markers are archival candidates (delete-eligible on confirmation); a name with no such
  marker, or one modified within the last few hours, is keep/inspect.
- `sessions/*.md` — respect the per-session model: a file written in the last few hours may
  be a LIVE concurrent window, so do NOT propose ANYTHING for another session's ACTIVE
  state. For files past the 8h staleness window, gate on `**Status:**`:
  - `COMPLETE` — ARCHIVE-ONLY, never delete. COMPLETE sessions are archived by the Step 4
    rollup seam (Duty 2), not deleted here; classify it `deferred-to-step-4`.
  - anything else (a dead, non-COMPLETE husk) — `archive-candidate`, still never a blind
    delete.

Present the triage list — one row per stray: path, suggested verdict (delete-candidate |
archive-candidate | deferred-to-step-4 | keep/active), and why. Under `--dry-run`, stop
here. `.plan-expedite-state.*` strays may be deleted on explicit operator confirmation;
`sessions/*.md` files are never deleted in this step — archive-candidate and
deferred-to-step-4 rows route to Step 4 Duty 2's archive move. Both duties fold into the
Step 5 `Orphan cleanup:` line; nothing is removed in this step without a per-item go-ahead.
Immediately before deleting a `.plan-expedite-state.*` row, resolve and normalize it again,
require it to remain a regular file directly under `<workspace>`, reject symlink/reparse or
parent/root escapes, re-run `check-ignore`, and re-read its current bytes and metadata. Show
the normalized path plus current SHA-256, length, and last-write time in the named per-item
go-ahead. Any change before deletion invalidates the approval and requires a new go-ahead;
never restore, replace, or delete a path that was not the exact approved current file.

### Step 4 — current.md rollup commit/archive seam

Workspace-wide. The low-concurrency commit/archive of the DERIVED `current.md` rollup
(the seam the current-md write-race fix left to afterparty). Degrade gracefully — skip
with a one-line note — when the `sessions/` system is absent, so afterparty is usable
before the race fix ships.

**Detection + graceful degrade (run first).** The active path only makes sense once the
per-session system exists. SKIP the whole step with a one-line note when EITHER the
`sessions/` dir is absent OR the `Write-DerivedRollup` helper is missing from the derive
lib (a pre-race-fix repo, so afterparty stays usable before the fix ships):

    Test-Path -LiteralPath (Join-Path '<workspace>' '.claude/task-state/sessions') -PathType Container
    Select-String -Quiet -Path (Join-Path '<workspace>' '.claude/hooks/lib/task-state-derive.ps1') -Pattern '^function Write-DerivedRollup'

If EITHER returns `$false` (a missing lib file counts as `$false`), report
`rollup-commit: sessions/ system not present (pre-race-fix repo) -- skipped` and move on.
(In THIS repo both are present, so the active path below runs.) Note the blocks in this
step are PowerShell — this seam is genuinely PowerShell work (the operator's default shell),
unlike Step 3's bash blocks.

**Every PowerShell block in this step is self-contained.** Host shell tools do not keep
variables or dot-sourced functions between invocations, and the per-item go-ahead puts
Duties 2-3 in later invocations than Duty 1. So each block sets `$root` to the absolute
`<workspace>` path and dot-sources the derive lib by that absolute path (dot-source with
`. <path>`, never `&` or `-File`: the lib only defines functions). Never rely on `$root` or a
lib function surviving from an earlier block.

**Duty 1 — regenerate the derived rollup (low-concurrency refresh).** afterparty IS the
low-concurrency moment the race fix reserved for the rollup (per the design doc §6.4: the
derived rollup is "the only candidate for commit, and only at a low-concurrency moment").
Use `<workspace>` as `$root` (not the cwd's git root: a run started inside a nested project
repo would otherwise look for task-state in that repo), dot-source the derive lib, and call
the helper (this block is the non-dry-run path; see `--dry-run` below):

    $root = '<workspace>'                                     # absolute path from Step 0
    . (Join-Path $root '.claude/hooks/lib/task-state-derive.ps1')
    if ($null -eq (Get-DerivedRollup -GitRoot $root)) { 'no sessions to roll up' } else { Write-DerivedRollup -GitRoot $root }

`Write-DerivedRollup` rewrites `.claude/task-state/current.md` atomically (temp-sibling +
move) from the `sessions/*.md` files and is idempotent — a lost/raced write reproduces on
the next call. **Under `--dry-run`, do NOT call it** — the regen is itself a local write and
dry-run must touch nothing. For a read-only preview under `--dry-run`, `Get-DerivedRollup
-GitRoot $root` (the pure function the writer wraps) returns the same text WITHOUT writing
to disk. If `Get-DerivedRollup` returns `$null` (zero parseable `sessions/*.md` files — e.g.
all already archived, or all fail the required-field check), report "no sessions to roll up"
and skip Duties 2-3 for this run; `current.md` is left untouched. The writer never throws:
when `Get-DerivedRollup` returned text but `Write-DerivedRollup` returns `$null`, the write
itself failed — report `rollup regen failed` and skip Duty 3 (never snapshot a stale
rollup).

**Duty 2 — archive completed session files (design doc §6.2 step 5, archive-on-completion).**
Reuse the Step 3 Duty 2 per-session safety discipline verbatim: a session file written
inside the 8h staleness window may be a LIVE concurrent window — NEVER archive an active
session. An archive candidate is a `sessions/<id>.md` whose `**Status:**` is the completion
marker `COMPLETE` AND whose `**Last written:**` is well past the 8h window. This is the
counterpart Step 3 Duty 2 defers COMPLETE sessions to (Step 3 lists + defers, Step 4
archives). Use the derive lib's parser — do NOT re-implement field/timestamp parsing (one
source of truth) — re-establishing `$root` and the dot-source in the same block:

    $root = '<workspace>'
    . (Join-Path $root '.claude/hooks/lib/task-state-derive.ps1')
    $cutoff = (Get-Date).ToUniversalTime().AddHours(-8)
    Get-SessionStates $root | Where-Object { $_.Status -eq 'COMPLETE' -and $_.LastWrittenUtc -lt $cutoff } | Select-Object Path, Status, LastWritten

`Get-SessionStates` is non-recursive, so it already excludes `sessions/archive/`. LIST the
candidates — one row per file: id, status, last-written, age. Never under `--dry-run`, resolve
the source and destination at action time, require the source to remain a regular non-link file
directly under `<workspace>/.claude/task-state/sessions/`, and require the destination to be a
new path directly under its `archive/` child. Re-read THAT file; it must still parse as
`COMPLETE` and still be past the cutoff (a resumed session rewrites both). Then show its
normalized source/destination plus current SHA-256, length, last-write time, status, and parsed
timestamp in the named per-item go-ahead. Move immediately only if those exact bytes and
metadata remain current; a change or destination collision invalidates approval and keeps the
source in place. Never overwrite an archive entry:

    $root = '<workspace>'
    . (Join-Path $root '.claude/hooks/lib/task-state-derive.ps1')
    $s = Read-SessionState -Path '<path>'
    if ($null -ne $s -and $s.Status -eq 'COMPLETE' -and $s.LastWrittenUtc -lt (Get-Date).ToUniversalTime().AddHours(-8)) {
        New-Item -ItemType Directory -Force -Path (Join-Path $root '.claude/task-state/sessions/archive') | Out-Null
        Move-Item -LiteralPath '<path>' -Destination '<new archive path>'
    } else { 'skipped: no longer an archive candidate' }

Because `sessions/` (and thus `sessions/archive/`) is GITIGNORED, archiving is a LOCAL tidy —
it moves a file out of the derive set (the next regen drops it from the rollup), not a git
action. Under `--dry-run`, list only and move nothing.

**Duty 3 — milestone provenance commit (OPTIONAL, confirm-gated).** Routine per-session
state stays UNCOMMITTED by design — that is the whole point of the write-race fix (design
doc §9 Q2), and the load-bearing durable actions of this step are Duties 1-2, both purely
LOCAL. The derived rollup is regenerable, so it needs no per-wrap commit. But a milestone is
a natural provenance anchor for external readers (dev-observatory, git history), so
afterparty MAY — on explicit operator confirmation only — commit a snapshot of the rollup.

Duty 1's regen ran BEFORE Duty 2 archived sessions, so the current.md it wrote can still
list a session Duty 2 just archived as active. Re-regenerate before staging, so the snapshot
reflects the post-archive session set — only when the operator has opted into the snapshot,
and never under `--dry-run`. If this call returns `$null`, STOP Duty 3: committing now would
snapshot the pre-archive rollup.

    $root = '<workspace>'
    . (Join-Path $root '.claude/hooks/lib/task-state-derive.ps1')
    Write-DerivedRollup -GitRoot $root

`current.md` is GITIGNORED, so a naive `git add .claude/task-state/current.md` is REFUSED —
git prints an ignored-path hint ("Use -f") and exits non-zero; `git add -f` forces past the
ignore ON PURPOSE. Commit in `<workspace>`'s own repo and scope the commit itself to
`current.md` (pathspec), so any other staged work already in the index is left staged,
uncommitted. When OFFERING the snapshot, run `git -C '<workspace>' rev-parse --show-toplevel`
(read-only); per the workspace working-directory rule, if the commit repo it reports is not
`<workspace>` itself, print a loud WARNING naming BOTH beside the offer (advisory; the opt-in
stays the operator's):

    git -C '<workspace>' add -f .claude/task-state/current.md
    git -C '<workspace>' commit -m "chore(task-state): milestone rollup provenance snapshot" -- .claude/task-state/current.md

This is optional and never automatic — skip it unless the operator asks for the snapshot. If
the regenerated current.md is byte-identical to the last committed snapshot, `git add -f`
stages no diff and `git commit` fails "nothing to commit" (non-zero) — this is expected and
benign; report "rollup unchanged since last snapshot; no commit" rather than treating the
non-zero exit as an error. Under `--dry-run`, commit nothing (no regen, no archive move, no
force-add).

Fold the outcome of all three duties into the Step 5 `Rollup commit:` line (e.g.
`rollup regenerated; N session(s) archived; provenance commit <sha | declined>`).

### Step 5 — the consolidated hygiene report

Present the consolidated report as the centerpiece of the output:

    ## afterparty sweep — <date>
    scope: <current project | M active projects> | mode: <apply-on-confirm | dry-run>

    Autonomous (report):
    - tier-drift:      <delta summary + map pointer>
    - lesson-harvest:  <N candidates (dry-run, nothing created) + report pointer>
    - context-slim:    <top recommendations + report pointer>
    - meta-tool-prune: <tools due, or none>

    Conversational (walked):
    - memory-distill:  <what the operator confirmed / deferred>
    - test-prune:      <same>
    - plan-trim:       <same>

    Orphan cleanup:    <one-line outcome (Step 3)>
    Rollup commit:     <one-line outcome (Step 4)>

    Report:            <saved path | persistence failed: reason | dry-run: not written>
    Applied actions:   <each action + approval pointer, or none>
    Limits/next action:<unavailable/unmeasured coverage + one concrete next action>

    No hygiene target changed without its owning per-skill or named per-item go-ahead.

Keep it terse and pointer-first — full skill outputs live behind their pointers, not
re-quoted inline. Take exit measurements, finalize the outcomes/findings/limits tables, set
the lifecycle/end time, and safely replace this run's normal-mode report before returning.
If that write fails, print the complete final report and persistence failure without a saved
claim. Reconcile every closing mutation statement with actual report/rollup bookkeeping and
the separately listed approved actions.

---

## Maintenance

afterparty owns NO hygiene logic — every swept item's behavior is owned by that item's own
canonical contract: its core, the provider file for provider-native `context-slim`, or, for
`tier-drift`/`meta-tool-prune`, the tier-scan skills + the workspace instructions' Working
rules. When a chained skill's **invocation or flags** change (e.g. a
rename like `review-memories` → `memory-distill`, or a new report-only flag), update the
swept-set interface map above and the Step 1/2 invocations in the same diff — never restate the
chained skill's internal contract here.

Evals are a deferred follow-up: run `/skill-eval-setup user-afterparty` to scaffold an
`evals/` suite once the flow has stabilized through a couple of real sweeps (the
"see it work, then react" iteration). Until then, correctness is behavioral — verified by
an end-to-end observation run (plan Step 5), not a unit suite.
