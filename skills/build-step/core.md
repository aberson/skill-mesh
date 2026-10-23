# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

# build-step core

> **Judging doctrine:** the gate invariants (the producer never grades itself, weak or local models
> never gate, a strong final judge consolidates) live in [`judge-core.md`](../../_shared/judge-core.md)
> sections 5-6. This skill instantiates them for one develop, review and land loop.

## Intent continuity (drift-ranger)

Follow [the intent continuity contract](../../_shared/intent-continuity.md).
Receive the parent intent and the specific journey gap this step advances. Return implemented/isolated/available status and evidence without claiming user delivery from component gates. The parent coordinator owns the project checkpoint; do not duplicate it for worker/reviewer subcalls.


## Purpose

Execute one already-planned code change end to end: an isolated developer makes the change,
mechanical gates and independent reviewers judge it, and only a fully gated change lands in the
project's working tree. On reviewer lanes the reviewers also judge the step's completion condition.
Under a parent orchestrator the result is also an authenticated machine verdict.

Use it for one planned change, invoked by `build-phase`, `user-debug` or the operator. Do not use it
for a multi-step phase (`build-phase`), for reviewing an existing diff (`review-deep`,
`review-gauntlet`), for operator, wait or conditional plan steps (the parent owns those), or for
exploratory work with no problem statement.

Zero-flag behavior: `/build-step --problem "<p>"` uses worktree isolation, the `auto` lane (mechanical
gates, no reviewer agents), a 10-round budget, no runtime evidence and no verdict sidecar, and lands
the change uncommitted in the invoking project. build-step never commits, pushes or publishes;
committing is the caller's job.

## Inputs

| Arg | Required | Default | Meaning |
|---|---|---|---|
| `--problem` | yes | - | The planned change. Becomes the developer's problem statement. |
| `--acceptance` | no | - | The step's completion condition (the plan's `Done when`). Absent or empty means none. The parent filters placeholder sentinels before forwarding. See "Completion condition". **[D-ACC]** |
| `--plan-step` | no | - | `<plan-path>:<step-id>`. Forwarded to review-deep on the `deep` lane only; reported as ignored on other lanes. build-step forwards only an explicit value. |
| `--issue` | no | - | GitHub issue number, closed best-effort after a PASS (Step 8). Also keys the round budget. |
| `--max-iter` | no | 10 | Positive integer: total developer rounds for this step, including the first (see "Round budget"). |
| `--reviewers` | no | `auto` | `auto`, `code`, `deep`, `runtime` or `full`. |
| `--isolation` | no | `worktree` | Only `worktree` is accepted; any other value, including `docker`, is refused. **[D-DOCKER]** |
| `--ui` | no | off | Runtime evidence. Implied by `runtime` and `full`; on `auto`, `code` or `deep` it is reported as ignored and nothing is captured. |
| `--start-cmd`, `--url` | with `runtime`/`full` | - | App start command and base URL. |
| `--ready-url` | no | - | URL polled until HTTP 200 before capture. |
| `--pages` | no | `["<url>"]` | JSON array of URLs to screenshot. |
| `--viewport` | no | `1920x1080` | Browser viewport. |
| `--exercise-cmd` | no | - | Absolute path to a Playwright script the capture script runs before the screenshots (for example to establish an authenticated session). |
| `--exercise-timeout` | no | 30 | Seconds allowed for the exercise script. |
| `--record-video`, `--record-har` | no | off | Extra evidence. |
| `--keep-evidence` | no | off | Keep the evidence after a PASS (Step 8). |
| `--verdict-path`, `--verdict-run-id` | build-phase only | - | Durable parent-owned verdict channel (Step 0). |

`--stop-signal` is accepted for compatibility, ignored, and reported as ignored. Optional project
input: when `PROJECT_CONTEXT.md` exists at the project root, its contents are appended to the developer
prompt as import and type reference.

### Round budget

The resolved limit and the rounds consumed are recorded per step in
`<platform temp>/skill-mesh/build-step-budget/<key>.json`. The step key is `GIT_ROOT`, plus
`--plan-step` when given, else `--issue`, plus a hash of `--problem`; a different problem under the
same issue (for example a user-debug fix delegation) is a different step. Re-invoking the same step
continues that count instead of resetting it or adopting a newer default; an explicit `--max-iter`
replaces the limit but not the consumed count, so resuming an exhausted step needs a limit above the
consumed count. A round is consumed only when a developer pass returns. A successful PASS verdict
write clears the record. Without `--issue` or `--plan-step` each invocation is its own step with a
fresh budget. Any enclosing time or cost budget still applies.

### Completion condition **[D-ACC]**

The completion condition is split into items numbered 1..N at semicolons and line breaks; without
`--acceptance` the single item is the problem statement. Only reviewers judge it, never the developer.
Each reviewer that records items uses these statuses:

| Status | Meaning | Recorded by |
|---|---|---|
| `CONFIRMED` | Evidence shows the item holds (code, patch, the Step 4 gate logs, or runtime evidence), cited | Correctness, runtime arms |
| `FAULTED` | Evidence shows the item does not hold; comes with a material finding | Correctness, runtime arms |
| `UNVERIFIABLE` | The arm's evidence can neither confirm nor fault the item | Correctness |
| `NOT OBSERVED` | The item is within the arm's evidence slice but was not seen; comes with a missing-evidence finding | runtime arms |
| `NOT APPLICABLE` | The arm's evidence slice cannot observe the item | runtime arms |

An item passes when at least one reviewer of the lane CONFIRMED it and none FAULTED it or reported it
NOT OBSERVED. On `full`, any arm's CONFIRMED counts, matched by item number. An item that no reviewer
could confirm (every arm `UNVERIFIABLE` or `NOT APPLICABLE`) becomes a deferred manual-UAT item
`verify: <item>`, not a failure. On `deep`, items go to review-deep's prompt as criteria, and
`--plan-step` adds its plan-conformance lens; review-deep's own threshold applies there, under which a
single Nit already makes a lens NEEDS-WORK. On `auto`, no reviewer exists: the condition is reported
`unchecked` and does not gate. A PASS on `auto` therefore leaves a declared `Done when` unverified, and
the parent's checkpoint and issue comment do not show that; choose a reviewer lane when the condition
matters.

The report and the verdict summary carry one acceptance label, the first that applies:
`not reached` (the run ended before review); `absent` (no `--acceptance`); `unchecked` (`auto`);
`checked-review (plan-conformance)` (`deep` with `--plan-step`, where both the correctness and
plan-conformance lenses passed); `checked-review` (on `code`, `runtime` and `full`, every item passed
or was deferred and at least one was CONFIRMED; on `deep`, the correctness lens passed); `deferred`
(every item was deferred); `not confirmed` (otherwise).

## Lanes

| Lane | Reviewers | Prerequisites |
|---|---|---|
| `auto` (default) | None. Mechanical gates decide. | A declared, recognized test command |
| `code` | Five arms: Correctness, Bugs, Security, Test Quality, Style | As `auto` |
| `deep` | One `/review-deep` invocation instead of the five arms | As `auto`; no `--start-cmd`/`--url` |
| `runtime` | Three arms: UI (blind-first), Backend, Frontend, on captured evidence | `--start-cmd`, `--url`, Playwright, the packaged capture script, an image-capable UI arm |
| `full` | All eight arms | As `runtime` |

`plan-review` routes high-stakes steps from `code` to `deep` at plan time; review-deep's own core owns
that trigger list. The Style arm's local-model offload (`build-step-style`) stays disabled; a weak or
local verdict may only advise and never gates (judge-core section 5.7). On the deep lane,
review-deep's own Style offload setting applies unchanged; tier-offload's policy keeps a local model
out of merge contexts, and that conflict is recorded for its owners. **[D4]**

## Model roles

The core names capability tiers only; host adapters resolve identities.

| Role | Binding | Owner |
|---|---|---|
| Orchestrator, including the Step 7 strong final judge | The invoking session, which must be the provider-selected strong gate model **[D5]** | Host session configuration |
| Developer arm | Inherits the invoking session unless the host adapter pins a builder **[D1]** | Host adapter |
| Code and runtime reviewer arms | The reviewer tier (`sonnet` in the tier map, restoring the binding lost in `7e5db1a`), never an inherited escalated session; the UI arm must accept images **[D2, D3]** | Tier map via host adapter |
| Deep-lane lenses | review-deep's own per-lens tiers; build-step does not re-pin them | review-deep |
| Phone-a-friend diagnosis arm | `fable` tier, at most once per run, advisory | Workspace tier policy **[D6]** |

At Step 0 the orchestrator records its own requested, configured and observed model and effort. Every
dispatch records the arm's requested model and effort, the configured identity it would otherwise
inherit, and the host-reported identity (or `null`) in `<run-state>/dispatch.json`, which survives
every outcome. The report's `Models:` line prints `requested / configured / observed` per role.

## Outputs and side effects

| Write | Target | When, and lifetime |
|---|---|---|
| Verdict sidecar | `--verdict-path` (parent-owned, outside every worktree) | Parent channel only: initialized first, finalized on every terminal path |
| Deferred UAT file | `<verdict-path>.uat.md` under a channel, else `<platform temp>/skill-mesh/build-step-deferred/<branch>.md` | Only for a passing run with deferred items; written before the verdict; owned by the reader afterwards |
| Round budget | `<platform temp>/skill-mesh/build-step-budget/<key>.json` | Per step key (see Round budget); cleared by a successful PASS verdict write |
| Run state | `<run-state>` = `<platform temp>/skill-mesh/build-step-runs/<branch>/`: the run record (owner, token, heartbeat, stash state, `finalized` marker), snapshots, `leftovers/`, `payload.patch`, reviewer records, review-deep output, `dispatch.json` | Whole run; deleted by `cleanup` after a verified PASS, kept and marked finalized on every other outcome for `recover`; never holds the verdict path, run id or key |
| Locks | `<git-common-dir>/skill-mesh-stash.lock` and one `skill-mesh-tree-<hash of GIT_ROOT>.lock` per operator tree | Per the Run state machine: the stash lock around stash calls; the tree lock around stash calls and while a snapshot is `active`; released by the owning step, `finalize` or `recover`; `unlock` clears only a dead owner's lock that guards no `active` snapshot |
| Run archive | `<platform temp>/skill-mesh/build-step-archive/<branch>/`: developer report, gate logs, `payload.patch`, `landed-paths.json`, reviewer records, every round's review-deep sidecars (both of a retried round), `dispatch.json`, diagnosis | Written by `archive` before a PASS cleanup; kept |
| Scoped stash of the operator's uncommitted project changes | Git stash, recorded by object id | Step 0, only if project paths are dirty; restored by that id |
| Branch and child worktree | `build-step-<UTC>-<rand>` at `<dirname(GIT_ROOT)>/worktree_<branch>` | Name generated by `scope` (Step 0.3); created at Step 1; removed after a verified PASS, kept on every other outcome |
| Dependency install, gate logs, developer report, evidence, diagnosis, remaining findings | `<WORKTREE_PROJECT>/.build-step/` (every `.build-step/` path in this core is anchored there) and package caches | Steps 1-10 |
| Preview copy of the change | Operator project tree, snapshot-backed | Step 5 only; rolled back before any review decision |
| Database migrations | Operator project database | Step 5 only, framework-native, not rolled back, including on BLOCKED **[D-MIG]** |
| Landed change (uncommitted) | Operator project tree, snapshot-backed | Step 8; rolled back only if a gate fails before the landing is verified |
| Kept evidence | `<platform temp>/skill-mesh/build-step-evidence/<branch>/` | `--keep-evidence` only |
| App process | Host, inside a job object or process group the run owns | Step 5 |
| `git fetch origin` | Remote-tracking refs | Ship-gate checks |
| Task-state checkpoint | Via `task-handoff --loop` | Each round boundary after round 1 |
| Issue close with comment | GitHub | After a PASS with `--issue` |

build-step never commits, pushes, edits `.gitignore`, kills a process outside its own job or process
group, or edits task-state files directly.

## Mechanics helper **[P1, D-MECH]**

Stateful Git and process mechanics run through `<skill-dir>/scripts/build_step_tree.py`, where
`<skill-dir>` is the directory that contains the loaded core. Each subcommand is one tool call, reads
and writes `<run-state>/state.json` atomically (shell variables do not survive between agent tool
calls) and prints exactly one JSON object whose `status` field is authoritative: `ok`, `halt` (integrity
or merge halt), `scope-escape`, or `unavailable` (a check that cannot be performed). A call that does
not print exactly one parseable JSON object, whatever its exit code, is a helper failure. A `halt` or
`scope-escape` that the calling step does not map ends the run: as `rollback failed` for a rollback or
restore call, otherwise as `helper failure`; either way `tree=` comes from saved state (Run state
machine). All path handling is NUL-safe. Ported from `875de2a` and extended.

### Run state machine

Runs, locks, stashes and snapshots change only as the table below defines; the procedure steps call
these transitions and add none of their own. Terms:

- **Run record.** `scope` writes it: the branch name (which keys `<run-state>`), a random run token, the
  creation time, and the owner: the long-lived host agent process the adapter names, its start time,
  the host name and, when the host exposes one, the session id. Every later call of the run refreshes
  its heartbeat. The record also holds `stash` (`none`, `pending`, `saved` with object id and paths, or
  `restored`), the snapshots and, last, `finalized: <outcome>`.
- **Liveness.** A run is alive when it is not finalized and either its recorded process with that start
  time is running on this host or, for another host, its heartbeat is younger than 24 hours; otherwise
  it is dead. A lock's owner is alive exactly when the run it names is alive (a lock whose run state is
  missing is judged by its recorded process and heartbeat).
- **Locks.** Both live in the Git common directory: the stash lock `skill-mesh-stash.lock`, and one
  operator-tree lock per operator working tree, `skill-mesh-tree-<hash of GIT_ROOT>.lock`, shared by
  every `PROJECT_PREFIX` in that tree, so nested projects such as `extra-credit` (prefix `.`) and
  `extra-credit/frontend` (prefix `frontend/`) exclude each other. The tree lock is taken before the
  stash lock, and a run holds its tree lock for as long as it has an `active` snapshot. The owner file
  records the run's branch, token and owner fields. Taking a lock that is free, or already owned by the
  caller's run token, succeeds at once (held, not busy); a lock owned by an alive run is retried for up
  to 10 minutes; a lock owned by a dead run, or still owned after the wait, returns `halt` (`lock busy`)
  with the owner record and remedy. On the main path `lock busy` ends the run as
  `concurrent run active`; inside the finalizer it keeps the outcome already chosen (Step 10).
- **Remedy**, printed with `lock busy`, `concurrent run active` and `unfinished prior run`: for a dead
  owner, `recover <owner-branch>` (or `unlock <lock>` when its run state is missing); for an alive owner
  whose recorded process is the caller's own (same PID and start time),
  `recover <owner-branch> --abandon --by <this-branch>`; otherwise none, because the owner is working.
- **Snapshot and rollback.** A snapshot (preview or landing) records, per destination, the prior state
  (tracked, tracked-deleted, untracked or absent, with bytes and index entry) and the state this run
  wrote (content hash, which for a landing is the Git blob id of Step 8.3, or absence, and index
  entry), and a lifecycle: `active`, then exactly one of
  `rolled-back` or `released`, each change written atomically. A rollback of an `active` snapshot
  restores a path only when its current state equals the state this run wrote, treats a path already at
  its prior state as done, and leaves any other path untouched as a leftover, saving its prior bytes
  and the bytes this run wrote under `<run-state>/leftovers/` and listing them; an index entry is
  restored only when the current entry equals the recorded one. With no leftover the snapshot becomes
  `rolled-back`; otherwise it stays `active` and the call returns `halt`. Rolling back a snapshot that
  is not `active` is an `ok` no-op. Only `active` snapshots count anywhere in this core.
- **`tree=`** (the summary field and the report's `Operator tree:` line) is computed at finalization
  from saved state, never from which call failed: `leftover` when this run has an `active` snapshot or a
  `pending` or `saved` stash, when `recover --check` lists another run's `active` snapshot in this
  operator tree, or when either cannot be read; otherwise `clean`. In the table, `clean*` means `clean`
  unless one of the last two conditions holds.

| # | State | Event (caller) | Guard | Action | Next state | Locks held after | `tree=` if finalized here | Report line |
|---|---|---|---|---|---|---|---|---|
| T1 | none | `scope` (Step 0.3) | - | Generate the branch name `build-step-<UTC>-<rand>` and the run token; write the run record with `stash: none` | `scoped` | none | `clean*` | - |
| T2 | `scoped` | `recover --check` (Step 0.3) | An alive run of this `GIT_ROOT` has an `active` snapshot or a `pending`/`saved` stash on paths under this `PROJECT_PREFIX` | None | finalizer | none | `clean*` | `concurrent run active`, with the owner record and remedy |
| T3 | `scoped` | `recover --check` (Step 0.3) | A dead run has an `active` snapshot anywhere in this operator tree (so it still holds the tree lock), or a `pending`/`saved` stash on paths under this `PROJECT_PREFIX` | List its paths; they are never stashed as operator work | finalizer | none | `clean*` | `unfinished prior run`, with its paths and `recover <branch>` |
| T4 | `scoped`, project paths dirty | `stash-save` (Step 0.6) | Tree lock, then stash lock | Write `stash: pending`; run `git stash push --include-untracked -m "build-step <branch>" -- <PROJECT_PREFIX>`; accept only if `refs/stash` changed and its subject carries the marker, recording `stash: saved` (object id, paths); release both locks | `stash: saved` | none | `leftover` | Still dirty: `stash failed` |
| T5 | `stash: pending` (a crash between the push and the state write) | The next `stash-restore` or `recover` | - | Find the stash entries whose subject is `build-step <branch>`: exactly one makes the stash `saved` with that object id, none makes it `none`, more than one returns `halt` | `stash: saved` or `none` | unchanged | `leftover` while `pending` | - |
| T6 | No `active` snapshot | `preview-apply` (Step 5.1) | Tree lock | Create the `active` preview snapshot, then write the payload | preview `active` | tree | `leftover` | - |
| T7 | Preview or landing `active` | `preview-rollback` or `land-rollback` (Steps 5.5 and 8.3-8.6, the finalizer, `recover`) | Tree lock (already held) | Roll back | No leftover: `rolled-back`; leftovers: stays `active`, `halt` | Tree lock released once not `active` | `leftover` while `active`, then as the stash decides | Leftovers: `rollback failed`, listing each path and its saved bytes |
| T8 | No `active` snapshot | `land` (Step 8.3) | The payload hash, recomputed from the worktree before any lock is taken, equals the reviewed one; then the tree lock; then the hash, recomputed again under that lock before the snapshot or any write, still equals it | Create the `active` landing snapshot, then land each path (Step 8.3), recording each written path's Git blob id | landing `active` | tree | `leftover` | Mismatch before the lock: `payload changed after review`, with no lock taken and nothing written; mismatch under the lock: the tree lock is released, then the same line, with nothing written |
| T9 | Landing `active` | `verify-landed` (Step 8.6) | Every path equals its written state | Mark the landing `released`; it is never rolled back | landing `released` | none | As the stash decides | Failure: Step 8.6 runs T7, `landing verification failed` |
| T10 | `stash: saved`, no `active` snapshot | `stash-restore` (Step 8.8, the finalizer, `recover`) | Tree lock, then stash lock | Apply the recorded object with `--index`; drop only the entry with that object id; release both locks | `stash: restored`; a failed apply leaves it `saved` | none | `clean*`; `leftover` after a failed apply | Failure (the apply fails): nothing is dropped or deleted and both locks are released; the line prints the entry and its object id and names `recover <branch>` (retry) and `recover <branch> --stash-resolved` (after the operator applies or drops the entry by hand, T20); Step 8.8 ends `restore failed`, the finalizer applies its outcome rule (Step 10), and inside `recover` it is T19 |
| T11 | Not finalized | `finalize <outcome>` (the finalizer's last helper call, Step 10) | - | Release every lock the run holds except the tree lock of a still-`active` snapshot; compute `tree=`; write `finalized: <outcome>` | finalized (dead for recovery) | Tree lock only while a snapshot is `active` | Computed here | `Operator tree:` and the summary's `tree=` |
| T12 | Finalized | Any call for this run other than `recover` | - | None | unchanged | unchanged | - | `halt` (`run finalized`) |
| T13 | Target dead | `recover <branch>` (operator) | - | Act with the target's run token, so its locks are held, not busy; `app-stop` any recorded supervisor; T7 for each `active` snapshot; T5 and T10 for its stash (a failed apply is T19); report a `released` landing as kept; release every lock; write `finalized: recovered` | `recovered`, or T15 or T19 when they apply | none, except as T15 | - | `recovered`; a failed stash restore is T19: not `recovered`, printing the entry and its object id and naming `recover <branch> --stash-resolved` |
| T14 | Target alive | `recover <branch>` without `--abandon` | - | Refuse | unchanged | unchanged | - | `halt` (owner alive), with the remedy |
| T15 | A T7 inside `recover` leaves leftovers | (T13, T16 or T17) | - | Restore no stash; do not mark `recovered`; print each leftover and its saved prior and written bytes; release the stash lock | snapshot stays `active` | Tree lock (target's token) | - | `recover halted`, naming `recover <branch> --keep-current <paths>` |
| T16 | Target dead; an `active` snapshot with listed leftovers | `recover <branch> --keep-current <paths>` (operator) | Every path is one of those listed leftovers | Keep each path's current bytes and drop it from the list; the snapshot becomes `rolled-back` when none remains; then continue as T13 | `recovered`, or T15 for paths still listed | As T13 or T15 | - | As T13 or T15 |
| T17 | Target alive, not finalized | `recover <branch> --abandon --by <caller-branch>` (operator) | The target's recorded process (PID and start time) is the caller's own; `<caller-branch>` is a run of that same process with a different run token, created after the target's last heartbeat; the target's heartbeat is older than 15 minutes (longer than any helper call, including its 10-minute lock wait) | Write `finalized: abandoned`, so T12 refuses the target's later calls; continue as T13 | `recovered`, or T15 | As T13 or T15 | - | `abandoned`, then as T13 or T15 |
| T18 | A lock whose owner is dead and has no `active` snapshot, or whose run state is missing | `unlock <lock>` (operator) | - | Clear the lock. A live owner's lock, or a tree lock guarding an `active` snapshot, is never cleared | - | - | - | - |
| T19 | A T10 inside `recover` fails | (T13, T16 or T17) | - | Delete nothing: no drop, checkout or reset, and any path the failed apply touched stays as Git left it; keep `stash: saved`; do not mark `recovered`; print the entry, its object id and its recorded paths; release every lock the target holds | stash stays `saved`, not `recovered` | none | - | `recover halted: stash restore failed`, printing the entry and its object id and naming `recover <branch> --stash-resolved` |
| T20 | Target dead; `stash: saved` (T5 first resolves a `pending` one) | `recover <branch> --stash-resolved` (operator) | No entry in `git stash list` has the recorded object id | Write `stash: restored` without applying or dropping anything (the operator's own resolution stands); then continue as T13 | As T13 | As T13 | - | `stash resolved by operator`, then as T13; while an entry with that object id remains: refused with `halt` (`stash entry remains`), naming it, and nothing changes; a target without a `saved` stash is refused with `halt` (`no saved stash`), with nothing changed |

Other subcommands:

- `scope`: resolve `PROJECT_ROOT` (the invocation directory, which owns project commands), `GIT_ROOT`
  (which owns Git commands) and the repository-relative `PROJECT_PREFIX` (`.` when the project is the
  repository). It never substitutes `GIT_ROOT` for `PROJECT_ROOT`. It writes the run record (T1).
- `recover --check`: list this `GIT_ROOT`'s runs that have an `active` snapshot or a `pending` or
  `saved` stash, with their paths and liveness, for T2, T3 and `tree=`. It changes nothing.
- `worktree-create`: record `WORKTREE_BASELINE` (current `HEAD`), create the recorded branch and the
  worktree at `<dirname(GIT_ROOT)>/worktree_<branch>` (refusing a path inside `GIT_ROOT`), and resolve
  `WORKTREE_PROJECT`.
- `changes`: the payload is `git diff <WORKTREE_BASELINE>` (commits, index and unstaged edits) plus
  `git ls-files --others --exclude-standard`. It first audits every changed path in the whole child
  worktree; any path outside `PROJECT_PREFIX` is a `scope-escape`. Orchestrator paths (`.build-step/**`,
  `.review-deep/**`) are then removed. It writes one binary-safe patch of the payload, new files
  included, to `<run-state>/payload.patch`, and records the payload hash. `git diff HEAD` is never used:
  it drops developer commits and untracked files.
- `tree-hash`: hash the Git-visible files (tracked plus untracked non-ignored) under `PROJECT_PREFIX`
  in the worktree, excluding orchestrator paths, plus the payload paths in the operator tree.
- `ship-gate`: Step 8.1.
- `app-start` and `app-stop`: start `--start-cmd` from `PROJECT_ROOT` under a supervisor that owns a
  Windows job object (kill-on-close) or a POSIX process group for the app's whole lifetime, recorded
  in run state, with the app log in the evidence directory; stop the job or group, then confirm the
  `--url` and `--ready-url` ports are free. A port still bound is reported with its process id; nothing
  outside the job or group is killed.
- `test-count`: resolve a declared test command to its runner by stripping `uv run`, `npx`,
  `pnpm exec` and `python -m`, and by following `npm [--prefix <dir>] test`, `npm run <script>`,
  `pnpm test` and `yarn test` through that package's `package.json` scripts (at most three hops); then
  extract collected and passed counts from a gate log in a recognized runner format (pytest,
  `node --test`, go test, cargo test, jest, vitest). `--check-runner <command>` reports the resolved
  runner and whether it is recognized.
- `budget`: read, advance and clear the round-budget record.
- `archive` and `cleanup`: Step 8.9.

## Procedure

### Step 0 -- Pre-flight

Validate before writing to the project, its Git state or the host. The only earlier writes are the
verdict initialization (0.1) and the run state that `scope` creates (0.3). In order:

1. **Verdict channel.** `--verdict-path` and `--verdict-run-id` are all-or-none and non-empty, and the
   path lies outside the project and any worktree. With a complete channel, atomically initialize the
   sidecar (replacing any existing file) with `write_verdict(..., terminal="NEEDS WORK",
   summary="run incomplete")` from `../../_shared/build_step_verdict.py` before anything else. From
   here every terminal path runs the Step 10 finalizer. The parent-local `VERDICT_KEY` is never a CLI
   or skill argument; it stays in the parent orchestration state that executes this core.
2. **Arguments.** Refuse a missing `--problem`, a non-positive `--max-iter`, an unknown `--reviewers`
   value, any `--isolation` other than `worktree`, and `runtime`/`full` without `--start-cmd` and
   `--url`. A refusal names every invalid input and makes no other write.
3. **Helper, scope and unfinished runs.** Confirm the helper exists (else `required_tool_missing`).
   Run `scope` (T1), then `recover --check`: another run's state ends this run as
   `concurrent run active` (T2) or `unfinished prior run` (T3), each with its paths and remedy, and that
   run's files are never stashed as operator work. `unavailable` from `recover --check` also halts, as
   `helper failure`.
4. **Commands.** Read the project's declared commands from its `CLAUDE.md`/`AGENTS.md`
   (`## Commands`, `## Key commands` or `## Package manager`), else the package manifest's scripts:
   the primary test command, any further DONE-gate suites the project declares, an optional narrower
   iteration test command (default: the primary test command), lint, typecheck, dependency install,
   and the shell (the project's declared Shell line, else the host default). Lint or typecheck declared
   "not configured" is skipped and reported. A primary test command that is missing, declared not
   configured, or whose resolved runner `test-count --check-runner` does not recognize is
   `required_tool_missing`, naming the resolved runner. Further DONE-gate suites are judged by exit code
   and may report `count unknown`. Never run a placeholder command.
5. **Host capabilities.** Apply the adapter's capability checks for the developer and reviewer arms
   (isolation, and any model the adapter pins). Runtime lanes also need an image-capable UI arm,
   Playwright importable, the packaged capture script `<skill-dir>/scripts/capture_evidence.py`, and
   nothing already listening on the `--url` or `--ready-url` port. Any missing capability is
   `required_tool_missing`. Record the orchestrator's identity (Model roles).
6. **Budget and operator changes.** Read the round budget; if it is already exhausted, the run ends
   `iteration budget exhausted` without a developer round. If project paths are dirty, run
   `stash-save` (T4); a `lock busy` halt is `concurrent run active`, and any other `halt` is
   `stash failed`.

### Step 1 -- Isolate

Run `worktree-create`, then the declared dependency-install command inside `WORKTREE_PROJECT` (fresh
worktrees carry no `.venv` or `node_modules`; include declared extras that hold gate tools). An
install failure is `environment setup failed`.

Verdict channel rules, all hosts:

- Standalone `/build-step` writes no sidecar; its report is for the invoking operator only.
- The parent-local `VERDICT_KEY`, the verdict path and the run id never appear in developer or
  reviewer prompts, arguments, environment variables, worktree or run-state files, or durable reports.
  Child agents neither own nor authenticate the channel.
- A host whose parent cannot keep the key out of every child context halts `required_tool_missing`.
  Where the parent's own transcript records the key, the host adapter states that as a proposed
  limitation pending decision D-KEY and the build-phase carve-out P3.

### Step 2 -- Developer agent pass

Spawn a sub-agent with fresh context (the host's isolated-agent primitive). A dispatch that times
out, is rate-limited or fails at the provider ends the run as `developer dispatch failed` without
consuming a round. When the developer returns, advance the round budget. Prompt:

```text
You are the developer agent for one build step. Make the change described below inside
WORKING DIRECTORY and nowhere else.

RULES:
- Change only files relevant to the problem. Read surrounding code first and follow its conventions.
- Every function you import must exist; search for it before using it.
- Write tests for new behavior. When new code must be reached from existing production code, add an
  integration test through the production entry point (route, CLI command, handler, dispatch site)
  that proves it is reached. Pure utilities with no caller in this step and schema-only changes are
  exempt.
- Commits, staged files and new untracked files are all captured; do not rely on any of them being
  ignored.
- Run formatters in check mode only. Fix findings in files you touched; report findings in files you
  did not touch as "pre-existing format debt in <files>" and leave them alone.
- Run these gates and fix failures before returning:
  <typecheck command or "not configured">
  <lint command or "not configured">
  <iteration test command>

WORKING DIRECTORY: <WORKTREE_PROJECT>

PROBLEM STATEMENT:
<problem>

COMPLETION CONDITION:                        (omit this block when there is no acceptance)
<numbered items>
Make the change satisfy every item. Reviewers, not you, decide whether it does.

PROJECT CONTEXT: <PROJECT_CONTEXT.md contents, or omit>

RETURN ONLY (details go to .build-step/dev-report.md):
1. DONE, or BLOCKED: <why>
2. the diff stat
3. the one-line test result, with the count
4. any pre-existing format debt note
5. the dev-report.md path
```

From round 2, append `PREVIOUS ROUND FINDINGS (address every one):` with every gate failure and
reviewer finding from Step 9. A developer `BLOCKED` return ends the run.

### Step 3 -- Capture the change set

Run `changes`. A `scope-escape` ends the run: nothing lands, the operator tree is restored, and the
worktree is kept. An empty payload ends the run as `no change produced`. Reviewers and every later step
use this payload and its patch, never a separate `git diff`.

### Step 4 -- Mechanical gates

In `WORKTREE_PROJECT`, run each configured gate with output redirected to `.build-step/gate-<name>.log`
and its exit code captured directly; judge on the exit code only, never through `tail` or another
filter. A nonzero exit is a gate failure whatever `test-count` can read. When the test gate exits 0,
run `test-count` on its log: zero collected tests fails the gate, and a count the helper cannot read
ends the run as `required_tool_missing`, never as a developer round.

Any other gate failure is that round's NEEDS WORK: go to Step 9 with the gate logs as findings.
Reviewers never see a change with failing gates.

### Step 5 -- Runtime evidence (`runtime` and `full` only)

1. `preview-apply` the payload into the operator tree. The app needs the project root's untracked
   runtime state, so it runs there, never from the worktree.
2. Migration pre-flight (framework-native, non-gating): from `PROJECT_ROOT`, run `uv run alembic
   upgrade head` when `alembic.ini` exists, else `npx prisma migrate deploy` for
   `prisma/schema.prisma`, else `npx drizzle-kit push` for `drizzle.config.ts`. An unreviewed developer
   migration therefore runs against the operator database and is not undone, even if the run ends
   BLOCKED. **[D-MIG]**
3. `app-start`, then poll `--ready-url` for up to 60 s and `--url` for up to 30 s.
4. Run `uv run --with playwright python <skill-dir>/scripts/capture_evidence.py` with `--url`,
   `--pages`, `--output-dir .build-step/evidence/run-<round>` (in the worktree), `--viewport`,
   `--exercise-timeout`, and `--exercise <exercise-cmd>`, `--record-video`, `--record-har` when given.
5. `app-stop`, then `preview-rollback`. Both always run, including after a readiness or capture
   failure. If the rollback leaves any path behind, the run ends `rollback failed` before any review.

If the app exited during startup, its log is that round's NEEDS WORK (Step 9). A readiness timeout
with the app still running, a capture failure, or a port still bound after `app-stop` ends the run as
`runtime environment unavailable`.

### Step 6 -- Spawn reviewer agents

Run the ship-gate check (Step 8.1) first, so no review is spent on a change a parallel session already
shipped. Run `tree-hash`.

Spawn every arm of the lane in parallel in one dispatch batch, each a fresh sibling context at the
reviewer tier, with the worktree as its working directory. Each arm's prompt contains: its lens
description below; the problem; the numbered completion items; the path `<run-state>/payload.patch`;
the touched files; the Step 4 gate logs as authorized evidence; its evidence slice; the round number
and payload hash; its record path `<run-state>/reviews/round-<n>/<lens>.json` (outside the
developer-writable worktree; the round directory starts empty); the record schema, the finding-class
table, the item-status table with the statuses its role may use, and the derivation rule from Step 7,
verbatim, so its own `verdict` field follows it. Reviewers are read-only everywhere else. Each returns
only its verdict, finding count and top finding.

Reviewer record (one JSON object):

```json
{"lens": "correctness", "round": 1, "payload_sha256": "...", "verdict": "PASS | NEEDS-WORK | UNCERTAIN",
 "incomplete": false, "auth_gated": false,
 "findings": [{"class": "material | advisory | missing-evidence", "title": "...", "file_line": "...", "evidence": "...", "fix": "..."}],
 "items": [{"id": 1, "status": "CONFIRMED | FAULTED | UNVERIFIABLE | NOT OBSERVED | NOT APPLICABLE", "evidence": "..."}]}
```

Correctness and the runtime arms record every item 1..N; Bugs, Security, Test Quality and Style record
an empty `items` list. Classify findings by what they do, not how large they feel:

| Finding | Class |
|---|---|
| Correctness defect, including a FAULTED item | material |
| Bug, at any blast radius | material |
| Security issue reachable from production input | material |
| Security weakness shown, with evidence, to be unreachable today | advisory |
| A test that would pass with the behavior removed, or a test to delete | material |
| A redundant or over-mocked test that can still fail | advisory |
| Style or convention deviation, at any count | advisory |
| Runtime misbehavior | material |
| Runtime presentation preference | advisory |
| An item reported NOT OBSERVED | missing-evidence |

Code arms, by lens: **Correctness** (logic against the problem and every completion item; edge cases;
inverted conditions; silent behavior breaks); **Bugs** (null access, leaks, races, type mismatches,
broken error propagation); **Security** (exploitable vulnerabilities, trust boundaries, injection,
authorization bypass, secret handling); **Test Quality** (goal is to trim: implementation-detail,
duplicate, tautological or over-mocked tests, and missing critical coverage); **Style** (deviations from
the surrounding code's actual conventions only).

Runtime arms: **UI** (screenshots), **Backend** (app log: tracebacks, crashes, and positive
confirmation of expected behavior), **Frontend** (console log and optional HAR: script errors, failed
requests). The UI arm reviews blind first:

```text
PHASE A - before reading anything below the divider, describe each screenshot exactly: visible text,
elements and their states, errors, empty or loading states, layout, and anything visibly broken.
---DIVIDER---
PHASE B - Problem: <problem>  Completion items: <numbered items>  Patch: <patch>
Compare Phase A with what should be visible. Every item status and finding must quote the Phase A
observation it rests on; if Phase A is too vague to support a status, set "incomplete": true. If every
screenshot shows an authentication gate (login form, PIN entry, sign-in) and none shows the feature,
write exactly: "auth_gated": true, "verdict": "UNCERTAIN", every item NOT APPLICABLE, and no findings.
```

After the arms return, run `tree-hash` again; any difference is `reviewer record invalid`. The same
before-and-after check brackets every later re-dispatch or re-invocation in Step 7.

Deep lane: create the empty directory `<run-state>/reviews/round-<n>/review-deep/` and invoke
`/review-deep` once with `--prompt` (the problem plus the numbered completion items as criteria),
`--diff` (the change-set patch), `--plan-step` when given, `--output-dir` set to that directory, and from
round 2 `--prior-sidecar` set to the previous round's final sidecar (Step 7). Do not spawn the five
arms; review-deep's lenses are a superset of them. Exactly one new `<timestamp>.json` must appear in
each invocation's output directory, whose `timestamp` field equals its filename stem and the basename
of review-deep's `Audit-trail JSON:` pointer (that pointer's directory is hard-coded and is not
compared); otherwise `reviewer record invalid`. Run `tree-hash` before and after every invocation,
including a Step 7 retry, as for the arms.

### Step 7 -- Aggregate verdict

The orchestrator is the strong final judge. It applies the rules below mechanically and cannot soften
them.

**Record validity.** For each arm record, derive a verdict: NEEDS-WORK if any finding is `material` or
`missing-evidence` or any item is `FAULTED` or `NOT OBSERVED`; otherwise UNCERTAIN if `verdict` is
UNCERTAIN or `incomplete` is true; otherwise PASS. A record is invalid when it is missing, duplicated or
unparseable for this round; when its `round` or `payload_sha256` differs from the current values; when
its `verdict` is not UNCERTAIN and differs from the derived verdict; when its item ids are not exactly
1..N (or not empty, for an arm that records no items); when an item uses a status its role may not
record (Completion condition table); when a `FAULTED` item has no material finding; or when a
`NOT OBSERVED` item has no missing-evidence finding. An invalid record ends the run as
`reviewer record invalid`. An `auth_gated` record written as the UI prompt specifies is valid.

`auto`: PASS when every configured gate passed.

`code`, `runtime`, `full`, in order:

1. Any invalid record: `reviewer record invalid`.
2. Any `auth_gated` record: `runtime environment unavailable`. The report names the remedies: an
   `--exercise-cmd` that establishes the session, a `--start-cmd` that bypasses authentication, or a
   plan-time change to `--reviewers code`.
3. Any record whose derived verdict is UNCERTAIN: re-dispatch that arm once, fresh, into the same round
   directory; if its new derived verdict is still UNCERTAIN, the run ends `reviewer uncertain`.
4. Any derived NEEDS-WORK: NEEDS WORK.
5. Otherwise apply the item rule (Completion condition): every item must pass or be deferred. An item
   with no CONFIRMED where at least one arm could observe it (not `NOT APPLICABLE` or `UNVERIFIABLE`)
   is NEEDS WORK. Advisory findings never gate, at any count; they are reported.

`deep`, in order. A round has one or two invocations, each with its own sidecar: the first, and the
retry when rule 3 runs. The round's verdict is computed over every final lens state of its sidecars.

1. **Validity.** The invocation's sidecar is bound as in Step 6 and has exactly one `lens_verdicts[]`
   entry for each `lens_id` among `correctness`, `bugs`, `security`, `test-quality`, `style` and
   `plan-conformance`; every `overall_verdict` is one of `PASS`, `NEEDS-WORK`, `UNCERTAIN`,
   `NEEDS-CLARIFICATION`, `NO-EVIDENCE`, `FAILED` or `SKIPPED`; and `SKIPPED` appears only for
   plan-conformance without `--plan-step`. Any violation is `reviewer record invalid`.
2. **No evidence.** Any lens `NO-EVIDENCE` is `reviewer record invalid`.
3. **One retry.** If any lens of the first sidecar is `FAILED`, `UNCERTAIN` or `NEEDS-CLARIFICATION`,
   whatever its aggregate says, re-invoke review-deep once for this round, fresh, with the same
   arguments, the same `--prior-sidecar` as the first invocation, and `--output-dir` set to the new
   empty directory `<run-state>/reviews/round-<n>/review-deep-retry/`. Apply 1 and 2 to the retry
   sidecar. The retry re-runs all six lenses, and every one of its lenses counts below, not only those
   that triggered it.
4. **Retry abstentions.** In the retry sidecar, any lens `FAILED` is `reviewer record invalid`;
   otherwise any lens `UNCERTAIN` or `NEEDS-CLARIFICATION`, including one that newly abstains after a
   `PASS` or `NEEDS-WORK` in the first sidecar, is `reviewer uncertain`, whatever
   `aggregated_verdict.result` says. When `FAILED` and `UNCERTAIN` or `NEEDS-CLARIFICATION` both
   remain, `FAILED` decides (`reviewer record invalid`). Both outcomes precede rule 5, as rule 3
   precedes rule 4 on the arm lanes.
5. **Lens evidence.** Any lens `NEEDS-WORK`, or any `Block` finding held by a lens whose verdict is
   `PASS` or `UNCERTAIN`, in either sidecar makes the round NEEDS WORK. Valid first-invocation
   evidence (a `NEEDS-WORK` lens, or a `Block` held by an `UNCERTAIN` or `PASS` lens) stays evidence
   even when the retry is clean, so a clean retry never outvotes a recorded `Block`. A
   `NEEDS-CLARIFICATION` lens's inputs-gathering `Block` is not counted here: rules 3 and 4 govern
   that lens, as they do `FAILED` and `SKIPPED`.
6. **Result.** Otherwise apply the final sidecar's `aggregated_verdict.result`: `PASS` passes,
   `NEEDS-WORK` is NEEDS WORK, `DEFERRED-TO-UAT` passes, and any other value is
   `reviewer record invalid`.

The round's final sidecar is the retry sidecar when rule 3 ran, otherwise the first; it is the next
round's `--prior-sidecar` (none in round 1, and a retry never receives its own round's first sidecar).
The round's deferred items are the union of its sidecars' `deferred_uat_items[]`. Its Step 9
findings are the union of the `lens_verdicts[].findings[]` of the lenses rule 5 counts, every
`PASS`, `NEEDS-WORK` or `UNCERTAIN` lens in either sidecar; for Step 9 a lens `Block` is material and
`Nit`/`FYI` are advisory, so every `Block` that makes a round NEEDS WORK by rule 5 reaches the
developer. Findings of a `NEEDS-CLARIFICATION`, `FAILED` or `SKIPPED` lens are not Step 9 findings.
`archive` keeps both sidecars of a retried round whole (Step 8.9), uncounted findings included.

Deferred items accumulate across rounds, including NEEDS WORK rounds, deduplicated by their
verification text. A passing run with any deferred item ends `DEFERRED-TO-UAT`; otherwise `PASS`
(`APPROVED` on `auto`). Nothing durable is written yet.

#### Machine verdict

The durable record is `verdict.json`-shaped schema v2, written only through `write_verdict` in
`../../_shared/build_step_verdict.py`, which owns the schema, atomic write and default-deny consume
rule. It is never written inside a worktree. Terminal strings translate as:

| build-step terminal string | verdict `result` |
|---|---|
| `PASS` | `PASS` |
| `APPROVED` (`auto`) | `PASS` |
| `DEFERRED-TO-UAT` | `DEFERRED-TO-UAT` |
| `NEEDS WORK` (a SPACE) | `NEEDS-WORK` (a HYPHEN) |
| `REJECTED` (`auto`) | `NEEDS-WORK` |

`halt` is `POST_MERGE_HALT` or `SHIP_GATE_HALT` (no colon) only when that sentinel drove the outcome;
otherwise `null`. The `summary` is one line of at most 512 characters: `<STATUS>: <reason>;
files=<n>; tests=<count> (<suites>); acceptance=<label>; deferred_uat=<n>; shipgate=<checked |
not-checked>; tree=<clean | leftover>`. Control characters become spaces; if the line is too long,
`<suites>` and then `<reason>` are truncated with `...`. Example:

```json
{"schema_version":2,"timestamp":"2026-06-22T10:15:30Z","run_id":"550e8400-e29b-41d4-a716-446655440000","writer":"build-step-orchestrator","result":"PASS","halt":null,"summary":"PASS: gates and review passed; files=3; tests=42 (tests/); acceptance=checked-review; deferred_uat=0; shipgate=checked; tree=clean","signature":"<64 lowercase hex>"}
```

The prose report is human-facing only; a parent that supplied the channel never parses it for the
verdict. The one report-derived input a parent uses is the `landed-paths.json` file that the
`Landed paths:` line names, read after authenticated classification and only to scope its checkpoint
(Step 8.10; design notes P3).

### Step 8 -- Land (verdict passed)

1. **Ship gate.** Run `ship-gate`: fetch `origin`; if the default branch advanced since
   `WORKTREE_BASELINE` and an advanced path overlaps the payload, print `SHIP_GATE_HALT:` with the new
   commits and overlapping paths and end the run. No developer round can fix an upstream race. Only
   `unavailable` here (no remote or default branch resolves) is reported as `shipgate=not-checked` with
   the reason and does not stop the run.
2. **Stash overlap.** If the run stashed operator changes and any stashed path is in the payload, end
   the run as a merge conflict before writing anything.
3. **Land.** Run `land` (T8). Before taking any lock it recomputes the payload hash from the worktree (a
   mismatch ends the run as `payload changed after review`, with no lock taken and nothing written);
   then it takes the operator-tree lock, held until Step 8.6 releases the landing or `land-rollback`
   ends the snapshot, and recomputes the hash once more under that lock, before the snapshot or any
   write, because the lock wait can last up to 10 minutes (a mismatch releases the lock and ends the run
   the same way, with nothing written). Only then does it snapshot every payload destination and land
   each path from `WORKTREE_BASELINE`, recording each written path's Git blob id (what
   `git -C <GIT_ROOT> hash-object -- <path>` reports right after the write, under the lock):
   - a tracked path the operator tree also changed since the baseline is merged with
     `git merge-file` (operator file, baseline blob, worktree file) without touching the index; a
     conflict is a merge conflict;
   - an untracked path that collides with an operator-tree change is a merge conflict;
   - any other path is copied with its bytes, or deleted when the change deleted it.

   Never use `merge --squash` (it drops uncommitted and untracked work), `git apply --3way` (it writes
   the index), or a full-file copy over a shared file. On a merge conflict: `land-rollback` and end
   the run.
4. **DONE gate.** In `PROJECT_ROOT`, run the primary test command and every further suite the project
   declares, not the iteration subset, judging each on its exit code. Record which suites ran and their
   counts. A nonzero exit from any suite is a failure whatever its count. When the primary command
   exits 0, `test-count` must read its count: zero fails, and an unreadable count is
   `required_tool_missing`; further suites may report `count unknown`. If the full suite is too slow
   here, say so instead of reporting a subset as the gate. On failure print `POST_MERGE_HALT:` with the
   failing tests, `land-rollback`, and end the run.
5. **Final ship gate.** Run `ship-gate` again; on overlap, `land-rollback` and end the run.
6. **Verify.** Run `verify-landed` against the recorded written states. On failure, `land-rollback`
   (which restores only paths still holding this run's bytes) and end the run as `landing verification
   failed`. On success the landing snapshot is marked `released`: **from here the landing is never
   rolled back.**
7. **Deferred items.** If any exist, write the deferred UAT file with a `## Manual UAT` heading and one
   line per item: `- [ ] <needs_verification> (reason: <reason>; check: <recommended_commands>)`, or
   `- [ ] verify: <item>` for an unconfirmable completion item. A write failure ends the run as
   `deferred items not persisted`.
8. **Restore.** Confirm this run has no `active` preview snapshot (Step 5 rolled it back; one still
   active ends the run as `rollback failed`), then `stash-restore` (T10). A restore failure is
   `restore failed`: the landing and the stash entry are kept, nothing is deleted, and the report
   prints the entry and its object id and names `recover <branch>` (retry) and
   `recover <branch> --stash-resolved` (once the operator has applied or dropped the entry by hand;
   T20).
9. **Archive and clean up.** `archive` copies `.build-step/` (reports, gate logs, diagnosis),
   `payload.patch`, the reviewer records, every round's review-deep sidecars (both of a retried round,
   Step 7) and `dispatch.json` into the run archive; writes there `landed-paths.json` from the
   `released` landing, one entry per landed path with its repository-relative path and its written
   state (the Git blob id recorded at Step 8.3, or `deleted`); and copies the evidence
   to the kept-evidence path when `--keep-evidence`. Then `cleanup` checks the exact worktree path and
   branch recorded in run state and runs `git -C <GIT_ROOT> worktree remove --force <path>` and
   `git -C <GIT_ROOT> branch -D <branch>`, then removes `<run-state>`. A failure is `cleanup failed`:
   the landing is kept and the leftover path named.
10. **Finalize.** Write PASS only after every merge, post-merge, ship-gate, cleanup and restoration
    operation succeeded: `write_verdict` with the parent path, run id and key and the terminal string
    from Step 7. The summary's `tree=` is computed as the Run state machine defines, with
    `recover --check` after cleanup; on PASS only another run's `active` snapshot can make it
    `leftover`. A PASS or `DEFERRED-TO-UAT` with `tree=leftover` therefore means that another run's
    unreviewed bytes may sit in the operator tree beside this landing: the parent's checkpoint must
    then commit exactly the plan document plus each `landed-paths.json` path that still holds its
    listed state, never the whole tree (design notes P3). The list narrows the parent's commit; it
    never authorizes advancement, which only the authenticated verdict does. Clear the round
    budget only after that write succeeds (standalone: after cleanup). If
    the write fails, report `verdict write failed`; the landing and the budget record stay, and the
    parent reads the initialized `run incomplete` record as BLOCKED.
11. **Issue.** With `--issue`, close it best-effort: `gh issue close <N> --comment "Completed via
    build-step. Changes landed uncommitted in the working tree; <summary>"`. A failed close is a
    warning and changes nothing else.

### Step 9 -- NEEDS WORK

Compile the round's findings: failing gate logs (or the startup log), every reviewer record, or on
`deep` the round's Step 7 findings (the union over both sidecars of the `PASS`, `NEEDS-WORK` and
`UNCERTAIN` lenses' `lens_verdicts[].findings[]`, including every `Block` rule 5 counted). A failing
test or gate error counts as a material finding for the checks below. Then, in order:

1. **Stop and audit.** If the same material bug shape (same invariant violated, same anti-pattern,
   same producer and consumer drift, same duplicated constant) was flagged in three consecutive
   rounds, even at different locations, stop: search the codebase for every site of that shape and
   report one audit finding with a structural regression-test proposal. The run ends `audit
   required`. Advisory findings never arm this.
2. **Re-scope.** If the same material defect survived two fix rounds, or two consecutive rounds
   oscillate (each new finding sits in the hunk that closed the previous one, or review-deep printed an
   `OSCILLATION:` line), the next round's prompt leads with structural-invariant diagnosis and one
   refactor of the shared invariant, not another line patch. This stays inside the budget and is not a
   halt.
3. **Phone-a-friend** (at most once per run). At the first re-scope, if a round remains and
   `.build-step/diagnosis.md` does not exist: before dispatching the re-scoped round, spawn one
   read-only, fresh-context diagnosis arm at the `fable` tier. Feed it the defect verbatim, every
   attempted fix and why it failed, and the worktree path. It returns user-debug's Diagnosis Block
   (Symptom, Reproduction, Primary sources, Suspected root cause, Confidence, Memory entries that
   apply), written to `.build-step/diagnosis.md` and prepended to the re-scoped prompt as a hypothesis
   the developer must verify against primary source. It never gates. On any dispatch error print
   `phone-a-friend: diagnosis arm skipped (<reason>)` and continue unchanged.
4. **Next round or budget exhausted.** If the budget has rounds left, go to Step 2 in the same
   worktree. Otherwise end the run `iteration budget exhausted` (terminal `REJECTED` on `auto`,
   `NEEDS WORK` otherwise). If the diagnosis arm has not run, run it once in report-only mode, also
   feeding it the per-round finding counts, the cross-round trend (non-monotonic counts and the
   round with the fewest findings, the revert candidate) and any oscillation note, and mark its Block
   UNVERIFIED in the report. Exhaustion never becomes PASS.

At each round boundary after round 1, checkpoint through `task-handoff --loop`, the task-state owner;
build-step never edits task-state files itself.

### Step 10 -- Terminal outcomes, finalizer and report

| Outcome | Report status | `write_verdict` terminal | `halt` | Parent build-phase halt class |
|---|---|---|---|---|
| Passed | PASS | `PASS` / `APPROVED` | null | - |
| Passed with deferred items | PASS (deferred UAT) | `DEFERRED-TO-UAT` | null | - |
| `audit required` | BLOCKED | `NEEDS WORK` | null | 3 stop-and-audit |
| Merge conflict (Step 8.2-8.3) | BLOCKED | `NEEDS WORK` | null | 5 merge conflict |
| Post-merge DONE gate failed | BLOCKED | `NEEDS WORK` | `POST_MERGE_HALT` | 2 quality gate |
| Ship-gate overlap | BLOCKED | `NEEDS WORK` | `SHIP_GATE_HALT` | 2 (race sub-case) |
| `iteration budget exhausted` | BLOCKED | `NEEDS WORK` (`REJECTED` on `auto`) | null | Not in the allowlist: a BLOCKED finding |
| Invalid input, `required_tool_missing`, `unfinished prior run`, `concurrent run active`, `environment setup failed` | BLOCKED | `NEEDS WORK` | null | Not in the allowlist: a BLOCKED finding |
| `developer dispatch failed`, developer BLOCKED, `no change produced` | BLOCKED | `NEEDS WORK` | null | Not in the allowlist: a BLOCKED finding |
| `runtime environment unavailable`, `reviewer record invalid`, `reviewer uncertain` | BLOCKED | `NEEDS WORK` | null | Not in the allowlist: a BLOCKED finding |
| Scope escape, `stash failed`, `helper failure`, `payload changed after review`, `landing verification failed`, `deferred items not persisted`, `restore failed`, `cleanup failed`, `rollback failed` | BLOCKED | `NEEDS WORK` | null | Not in the allowlist: a BLOCKED finding (integrity) |
| `verdict write failed` | BLOCKED | none possible | - | Parent reads `run incomplete` |

The halt classes are owned by the workspace build-phase halt contract (`code-quality.md`); this table
only maps onto them. Rows outside the allowlist stop the parent as BLOCKED findings to fix upstream.
`helper failure` covers any helper call that prints no single JSON object or reports `unavailable`
outside the ship gate's documented case.

**Finalizer.** Every outcome other than PASS runs the finalizer. It acts on saved run state, not on
which call failed, and runs once, in order, each action that state still calls for: `app-stop` for a
recorded supervisor; `land-rollback` for an `active` landing snapshot; `preview-rollback` for an
`active` preview snapshot; `stash-restore` for a `pending` or `saved` stash. A rollback that crashed or
returned `unavailable` earlier is therefore attempted once more here (a rollback touches only paths
still holding this run's bytes, so repeating it is safe); an action that fails inside the finalizer is
not retried, and its state stays as recorded. The outcome then becomes `rollback failed` when this run
still has an `active` snapshot, or a stash whose restore failed other than by `lock busy`, unless the
outcome already names the failed action (such as `restore failed`); a `lock busy` keeps the outcome
already chosen and adds the lock's owner record and remedy to the report. Then, when a worktree
exists, the finalizer writes `.build-step/remaining-findings.md` there (the last round's findings per
reviewer and gate, at most 200 lines); it keeps the worktree and `<run-state>`; it calls
`finalize <outcome>` (T11), which releases every lock except the tree lock of a still-`active`
snapshot, computes `tree=` and marks the run `finalized: <outcome>`; and with a channel it then calls
`write_verdict` with that `tree=` (`leftover` if `finalize` failed). An outcome reached before `scope`
has no run record: the finalizer skips the helper actions and `finalize`, and `tree=` rests on
`recover --check` alone. The report lists every leftover path with its saved bytes and the stash
entry, with T10's object id and remedies when its restore failed. No terminal path inherits the
`run incomplete` initialization except `verdict write failed`.

Report:

The first lines keep the baseline shapes that build-phase and user-debug read (`build-step complete`,
`Verdict: ... (iteration N/M)`, `build-step BLOCKED after N/M iterations`, `Reason:`, `Files changed:`,
`Tests: X/Y passing`, `Worktree:`, `Branch:`):

```text
build-step complete                                  | build-step BLOCKED after <n>/<limit> iterations
  Verdict: <PASS | PASS (deferred UAT)> (iteration <n>/<limit>)   | Reason: <outcome>
  Isolation: worktree   Reviewers: <auto | code (5) | deep (/review-deep delegate) | runtime (3) | full (8)>
  Files changed: <n> (landed uncommitted in <PROJECT_ROOT> | not landed)
  Tests: <passed>/<collected> passing (<suites>) | not run
  Gates: typecheck <ok|failed|not configured|not run>, lint <...>
  Acceptance: <label>
  Review: <per-arm derived verdicts | review-deep result and archived sidecar paths | none>
  Models: <role: requested / configured / observed, per arm>
  Ship gate: <checked | not checked: reason>
  Issue: <#N closed | #N left open (BLOCKED) | close failed (warning) | none>
  Ignored inputs: <--ui | --plan-step | --stop-signal | none>
  Operator tree: <clean | leftover: paths>
  Landed paths: <run archive>/landed-paths.json (<n> paths) | not archived
  Worktree: <removed | kept at path>
  Branch: <name>
  Run state: <removed | kept at path>   Diagnosis: <path, if the arm ran>
```

A BLOCKED report then prints `Remaining findings:` with the per-reviewer summary from
`.build-step/remaining-findings.md`. A passing run with deferred items appends its `## Manual UAT`
block; under a channel it prints "deferred file: parent-derived" instead of the path, standalone it
prints the path.

A BLOCKED report on a code-defect outcome ends with a handoff, preceded by its execution line:

```text
Run in: fresh window @ <project dir> - Model: Fable (hard root-cause diagnosis, per the tier policy)
/user-debug --symptom "<failing test or finding, verbatim>" --repro "<failing command>"
State pin: <git rev-parse HEAD> on <branch>; if it differs on arrival, re-orient first.
Deliverable: a verified diagnosis and fix design or plan revision, not another fix round.
History: one line per round (fix attempted -> why it failed). Prior diagnosis: UNVERIFIED.
Out of scope: merge, repo-sync, issue posts without operator approval.
```
