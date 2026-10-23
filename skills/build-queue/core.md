# NOTE: This is the canonical provider-independent contract. All provider wrappers must load it in full.

# build-queue core

## Intent continuity (drift-ranger)

Follow the intent continuity contract at `<repo>/_shared/intent-continuity.md`.
Carry each project intent and actual entry point into its delegated phase. Preserve its no-progress streak across queue switches. Reassess stalled supporting work within existing authorization; do not create a new review campaign or treat a new worktree as a reset.


## Purpose and complete operating contract

`/build-queue --queue <path>` runs an unattended overnight orchestration of multiple phase plans. Each queue item gets the full `/plan-expedite` -> `/build-phase` chain. Halts are converted to GitHub issues, not retries — the operator triages in the morning from the summary report.

---

## Constraints

Execution model: autonomous, queue-driven, halt-then-proceed (HEAVY). This skill exists so the operator can stage 3-5 pending phase plans, kick off `/build-queue` before bed, and wake up to a triage list. The whole point is that no halt — even a reviewer-gate failure on a code step — pulls the operator out of bed. Therefore:

1. **Halt-then-proceed, not halt-then-retry.** This is the load-bearing design choice. When any queue item halts (via the `/build-phase` halt contract — see `.claude/rules/code-quality.md` § "Build-phase halt contract"), this skill does NOT auto-retry, does NOT mutate the plan, does NOT try a different approach. It captures the halt context, files a single GitHub issue on the plan's repo titled `[build-queue parked] <plan name>: <halt class>`, marks the queue item as `PARKED`, and proceeds to the next item. Auto-retry would fight the halt contract (5 legitimate halts, anything else is a defect) and burn tokens on undiagnosable failures. The operator's morning triage IS the retry decision.

2. **Sequential, never parallel.** Queue items run one at a time. Parallel `/build-phase` on different plans has burned tokens in the past (memory: `feedback_parallel_buildphase_same_plan`). The queue's whole value is honest, sequential, surviveable execution. Each item's `/plan-expedite` and `/build-phase` run in this queue's own session through the host's skill-invocation adapter, never inside a sub-agent: `/build-phase` must be the parent orchestration context that keeps `/build-step`'s verdict key in private parent state and dispatches its isolated agents (`build-phase` core § "2b. Run build-step").

3. **Kill-switch is the only mid-run control.** Between queue items, this skill checks for a `.build-queue-killswitch` file in the queue file's directory. If present (any contents, any size), it stops cleanly after the current item: writes a partial morning summary noting the kill-switch was hit, persists state for resume, and exits. The operator creates it with `New-Item -ItemType File <queue-dir>/.build-queue-killswitch` (PowerShell) or `touch <queue-dir>/.build-queue-killswitch` (POSIX shell). The skill never asks "should I continue?" — the file is the answer.

4. **Final output is the morning summary, verbatim.** When the queue drains (or the kill-switch stops it), the morning summary IS the final output. It is also written to `.build-queue-report-<timestamp>.md` next to the queue file for later reference.

This is by strong operator preference; treat any deviation as a defect.

---

## When to use

- 3+ phase plans are staged across one or more projects and can ship overnight unattended.
- The operator has time to triage parked items in the morning but does not want to babysit reviewer gates at 3am.
- Plans have already been through `/plan-expedite` once (issues minted) OR are fresh and want the full prep chain — `/build-queue` calls `/plan-expedite` per item, so either is fine.

## When NOT to use

- Single phase: use `/build-phase` directly (or `/plan-expedite` + `/build-phase` if not yet prepped).
- Plans with `Type: wait` steps as the only remaining work — `/build-phase` will halt on wait steps and `/build-queue` will park them; nothing useful happens overnight.
- Mid-day interactive work where the operator wants to react to each halt — the park-then-proceed posture is wrong for that mode.
- When the queue's plans are not yet through `/plan-review` and `/plan-wrap` — let `/plan-expedite` (invoked per-item by this skill) handle it.

## Arguments

| Arg | Required | Default | Description |
|---|---|---|---|
| `--queue` | yes | -- | Path to queue file (see "Queue file format" below) |
| `--dry-run` | no | -- | Parse queue + print resolved item list + exit. No `/plan-expedite` or `/build-phase` calls. |
| `--resume` | no | -- | Resume from a prior partial run. Skips queue items already marked DONE or PARKED in `.build-queue-state`. |
| `--fresh` | no | -- | Explicitly archive an existing checkpoint and start a new run. Mutually exclusive with `--resume`; without this flag, an existing checkpoint is never reset. |

No other flags. Per-item flags (which `/build-phase` to run, phase number, etc.) live in the queue file, not on the `/build-queue` invocation.

Zero-flag behavior: a bare `/build-queue` (no `--queue`) runs nothing; see Step 0's queue argument check.

---

## Queue file format

Plain text. One queue item per non-blank, non-comment line. Comments start with `#`.

```text
# Each line: <plan-path-relative-or-absolute> [--phase N] [extra build-phase flags]
# Plan paths resolve relative to the queue file's directory if not absolute.

documentation/phase-g-plan.md
documentation/phase-2.1-plan.md --phase 1
../toybox/documentation/phase-n-plan.md
../alpha4gate/documentation/phase-4.7-plan.md --phase 2 --steps 1,2,3
```

Parse rules:

- Lines starting with `#` are comments; ignored.
- Blank lines ignored.
- First whitespace-separated token is the plan path; everything else is forwarded to `/build-phase` as flags.
- A plan path containing whitespace must be wrapped in double quotes (rare on this workspace).
- Order = execution order. No reordering.

At Step 0 pre-flight, resolve every plan path to an absolute path, verify the file exists, and resolve the plan's repository root. Any missing plan path, or a plan outside a git work tree, is a queue-level pre-flight error: print all such paths and exit without running anything. (Halting mid-queue on a typo would waste the night.)

---

## Steps

### Step 0: Pre-flight

Before invoking any sub-skill, do all of the following. Halt the entire run on any failure here — these are setup errors that compound if ignored.

**Queue argument check (first).** If `--queue` is absent (a bare invocation), has no path, or names a file that is missing or unreadable, or if `--resume` and `--fresh` are both present, print `Usage: /build-queue --queue <path> [--dry-run] [--resume | --fresh]` and a `Status: PRE-FLIGHT-FAILED` line, then exit. Never search for or guess a queue file. No sub-skill runs, and no state file or report is written or renamed.

1. **Strong-gate host check.** Establish through the active provider adapter that this invoking session satisfies `build-step`'s provider-selected strong final-judge binding. Record the adapter's configured identity and a host-reported observed identity when the host exposes one; an absent observation does not replace the configured check. If the adapter cannot establish the required binding, print `Status: PRE-FLIGHT-FAILED` with `required_tool_missing: strong_final_judge` and exit before any queue item, state rename, or report write. The producer never performs or substitutes this judgment.

2. **Kill-switch check.** If `.build-queue-killswitch` exists in the queue file's directory at startup, print `kill-switch present at startup; refusing to run. rm <path> to clear.` and exit. The operator may have forgotten it from a prior session.

3. **Parse and identify the queue.** Read the queue file as raw bytes and compute `queue_sha256` over those exact bytes (no newline, encoding or whitespace normalization). Apply the parse rules above and build the complete ordered `queue_items` identity list of `(item-index, abs-plan-path, forwarded-flags)`; preserve each forwarded flag string exactly as parsed for dispatch. Emit that list plus `repo-root` in the resolved table.

4. **Verify plan files exist and resolve repository roots.** For each resolved plan path, check the file exists and is readable, then resolve its repository root with `git -C <plan-file-directory> rev-parse --show-toplevel` (the `repo-root` column). Collect all failures (missing or unreadable plan; plan not inside a git work tree); if any, print the full list under a `Status: PRE-FLIGHT-FAILED` line and exit. No sub-skill runs, and no state file or report is written or renamed.

5. **Read and plan the state transition without writing.** Read `.build-queue-state`, if present, but do not rename, repair, create or rewrite anything yet.
   - With `--resume`, require one parseable canonical state whose `queue_path`, `queue_sha256`, and complete ordered `queue_items` exactly match Step 3, and whose outcome entries have valid shapes. The item identity comparison includes every resolved absolute plan path and its exact forwarded flags, including `--phase`, `--steps`, and future flags. `queue_mtime` is informational only and never establishes identity. A state from the older schema that lacks `queue_sha256` or `queue_items`, or any missing, malformed, hash-mismatched, argument-mismatched, duplicate or ambiguous state, is classified `Status: STATE-RECOVERY-HOLD`. A dry run reports that classification at Step 6; an executing run prints the exact defect and stops at Step 7 before any item or state/report write. Never reinterpret `--resume` as a fresh run.
   - **Cross-validate outcome authority before deriving any skip set.** Every `items[]` outcome must map to exactly one `queue_items` element with the same `item` index and `plan`, at the same array position. Resume-valid outcomes are a unique ordered terminal prefix beginning with queue item 1: no duplicate index or plan mapping, gap, reorder, out-of-range entry, or outcome for a different plan is valid. A live atomic checkpoint may contain that terminal prefix plus at most one trailing IN_PROGRESS entry for the immediately next queue item; on resume, that IN_PROGRESS entry triggers the hold below. Any cross-reference or prefix violation is malformed/ambiguous authority and holds without writes.
   - A valid state containing an `IN_PROGRESS` entry is also `STATE-RECOVERY-HOLD`. Name its item, stage and timestamp and preserve every file and partial work for operator triage; do not replay it or later items.
   - Only after every identity, cross-reference, prefix and shape check succeeds may a valid resumable state derive its skip set from that validated terminal prefix's DONE and PARKED entries. Any other terminal value is an authority defect and holds.
   - Without `--resume`, an existing canonical state also holds unless `--fresh` was explicitly passed. `--fresh` plans to archive that exact state as `.build-queue-state.prior-<timestamp>` and start a new run after the dry-run boundary. This is the only state-reset path and may intentionally repeat prior side effects.
   - With no canonical state, a plain invocation or `--fresh` plans a new run.

6. **Dry-run exit — strict zero-write boundary.** If `--dry-run` was passed, print the resolved item list, the state classification, the DONE/PARKED skip set for a valid `--resume`, and the transition a real invocation would apply. Then exit without renaming, discarding, creating or rewriting state, reports, prior files or recovery artifacts. Malformed, stale and identity-mismatched bytes remain byte-identical. A preview followed by `--resume` therefore sees the same checkpoint and skip set.

7. **Apply the planned execution transition.** Only after Step 6:
   - If Step 5 classified a state-recovery hold, print it and stop without writing.
   - For a new run, archive an existing state only when `--fresh` authorized it, then create the initial canonical state.
   - For a valid resume, retain the canonical state and its skip set unchanged until the next atomic checkpoint.
   - Every canonical write uses the atomic checkpoint rule in "State file schema". If initialization or transition fails, emit `STATE-RECOVERY-HOLD` and run no item.

### Step 1: Per-item loop

For each queue item in order (skipping those already DONE or PARKED under `--resume`):

1. **Kill-switch poll (between items).** Check for `.build-queue-killswitch`. If present: write a partial morning summary noting the kill-switch was hit before item N, persist state, exit.

2. **`cd` to the plan's repository root.** This is the `repo-root` resolved in Step 0, not the directory containing the plan file: `/build-step` lands repository-relative paths into its working directory (`build-step` core § "Worktree (default)": `PROJECT="$(pwd)"`), so a plan under `documentation/` run from its own directory would land code under `documentation/`. All subsequent `gh`, worktree and sub-skill calls run from here, not from the queue file's directory. (`gh` repo context — see `.claude/rules/windows-shell.md` and `.claude/rules/working-directory.md`.)

3. **Checkpoint the action boundary.** Before the first mutating sub-skill, atomically add this item as `{"verdict":"IN_PROGRESS","stage":"plan-expedite",...}`. If that checkpoint fails, hold without invoking the sub-skill. This marker remains authoritative through any interruption.

4. **Invoke `/plan-expedite` through the host's skill-invocation adapter** with `args: "--plan <abs-plan-path>"` (never `--new-window`).
   - Success: `/plan-expedite` returned its continue output and no `/plan-expedite halted at:` block. Its continue commands (`/clear`, `/goal "<condition>"`, `/build-phase --plan <path>`) are operator-facing: do not execute or relay them; proceed to step 5, which runs `/build-phase` directly.
   - Halt: anything else (the halt template, an error, a question for the operator, or no recognizable output). Park this item (see "Park procedure" below). Proceed to next item.

5. **Invoke `/build-phase` through the host's skill-invocation adapter.** First atomically change the IN_PROGRESS stage to `build-phase`; on checkpoint failure, hold without dispatch. Then invoke with `args: "--plan <abs-plan-path> <forwarded-flags>"`.
   - Success: DONE only when `/build-phase` ends with its `build-phase complete` report AND that report's parseable `Quality gates:` block shows every configured gate actually ran and passed, every unconfigured gate is explicitly marked `not configured`, the full configured test suite has every test passing, and its test count is not below the stated start count. Append the DONE entry below to `.build-queue-state`'s `items[]`. Proceed to next item.
   - Final-gate failure: a `build-phase complete` report whose `Quality gates:` block shows a failing, incomplete, timed-out, unsafe, or otherwise unrun configured gate; treats an unconfigured gate as passing rather than explicitly unconfigured; reports a test-count regression; or is missing or unparseable is NOT DONE. Park it with `halt_reason` `Quality-gate hard fail (final verification)` (halt-contract class 2): build-phase's Step 3 final verification has no failure branch, so a red final full-suite run can still print `build-phase complete`.
   - Halt: anything else — the `build-phase paused` report, a pre-flight Blocker, `required_tool_missing`, a wait-step or operator-step stop, an error, or no recognizable report. Park this item (PARKED entry shape below). Proceed to next item.
   - A sub-skill instruction to stop and wait for the user, or a request for an operator reply, ends that item as a halt. The queue never waits for a reply and never answers on the operator's behalf.
   - `halt_reason` names the halt-contract class when one applies (one of the five classes, or `defect-of-input: <item>`); otherwise `plan-expedite: <stage>` for a prep halt, or `non-allowlisted: <first line of the halt output>`, so morning triage can route defects upstream.

6. **State file update and acceptance capture.** After each item (DONE or PARKED), atomically replace its IN_PROGRESS entry with the terminal entry BEFORE moving to the next item. The full `items[]` array must remain present. Each terminal entry includes `item`, `plan`, `verdict`, `timestamp`, `acceptance`, and `next_action`. DONE entries additionally include `commits` and `issues_closed`; PARKED entries additionally include `halt_reason` and `issue` (number or null), and include the counts when `/build-phase` ran. `commits` (integer) and `issues_closed` (list of issue numbers) come only from the report's count lines; absent lines produce `null`.

   `acceptance.status` is `DEFERRED` when the upstream report supplies a "Manual UAT to run after build-phase" or other explicit open-acceptance block, `COMPLETE` only when that report explicitly states acceptance completed, otherwise `UNKNOWN`. Quality gates and automated DONE never imply acceptance. `acceptance.handoff` copies the complete upstream acceptance block and its concrete cue (for example `Please run M5 next.`) verbatim, or is `null` when absent. `next_action` copies the upstream final operator-action line verbatim, or is `null`; do not synthesize either field. JSON-escape newlines, quotes and backslashes when writing state so parsing recovers the exact original text.

   DONE entry appended to `.build-queue-state`:

   ```json
   {"item": 1, "plan": "C:/.../phase-g-plan.md", "verdict": "DONE", "timestamp": "2026-05-23T22:47:00Z", "commits": 7, "issues_closed": [41, 42, 43], "acceptance": {"status": "DEFERRED", "handoff": "<verbatim Manual UAT block and cue>"}, "next_action": "Please run M5 next."}
   ```

   PARKED entry appended to `.build-queue-state`:

   ```json
   {"item": 2, "plan": "C:/.../phase-2.1-plan.md", "verdict": "PARKED", "timestamp": "2026-05-23T23:18:00Z", "halt_reason": "Quality-gate hard fail", "issue": 99, "commits": 2, "issues_closed": [44], "acceptance": {"status": "UNKNOWN", "handoff": null}, "next_action": null}
   ```

   When narrating per-item completion in the run output, refer to the state file as `.build-queue-state` (exact filename — not "the state file" or "state was updated") and include the appended JSON entry verbatim, so the appended shape and the filename are both visible per item.

### Park procedure (on any halt)

When `/plan-expedite` or `/build-phase` halts for any reason — halt contract, autofix failure, missing plan field, anything:

1. **Capture context.** Grab:
   - The halt message verbatim (from the sub-skill's final output).
   - The plan path (absolute).
   - The queue item index.
   - Current branch + last commit on the worktree, if a worktree exists (`git worktree list` shows it).
   - Timestamp.

2. **File a GitHub issue.** From the plan's repository root (cwd from Step 1.2), use `gh issue create` with `--body-file <tmp-file>` (NOT inline `--body` — workspace rule). Title: `[build-queue parked] <plan-filename>: <halt-class-or-first-line>`. Body:

   ```markdown
   ## Parked by /build-queue

   - Queue item: <N> of <total>
   - Plan: <abs-path>
   - Timestamp: <iso>
   - Worktree: <path or "none">
   - Branch: <branch or "n/a">
   - Last commit: <sha + subject, or "n/a">

   ## Halt output

   <verbatim halt message from /plan-expedite or /build-phase>

   ## Resume

   Triage this halt, then:
   - Resume the single plan with the resume command in "Halt output" above when it names one (for example build-phase's `--resume <N>` after a paused or wait-step halt). Otherwise fix and re-run it: `/plan-expedite --plan <abs-path>` then `/build-phase --plan <abs-path>`
   - If the overnight run stopped before draining (kill-switch, but no IN_PROGRESS item), remove `.build-queue-killswitch` first if present, then continue it with `/build-queue --queue <queue-path> --resume` WITHOUT editing the queue file: `--resume` skips DONE and PARKED items, while a queue identity change holds for triage instead of silently replaying.
   ```

   On `gh` failure (rate limit, auth, repo not found): print the captured context to stdout AND write it to `.build-queue-park-item-<N>.md` next to the queue file. The item still gets marked PARKED in state — the issue filing is best-effort observability, not a halt condition.

3. **State file update.** Before issue filing, atomically set the current IN_PROGRESS stage to `parking`. After the issue result, replace that entry with PARKED, the `halt_reason` defined above, issue/count fields, and the acceptance/next-action fields from Step 1.6. A crash before terminal replacement leaves IN_PROGRESS and forces a recovery hold rather than duplicate issue filing or replay.

4. **Proceed.** Continue the loop. Do NOT halt the overnight run on a park — that's the whole design.

### Step 2: Morning summary

After the loop drains (or the kill-switch stops it), emit the morning summary to stdout AND write it to `.build-queue-report-<timestamp>.md` in the queue file's directory.

```markdown
# /build-queue summary

Queue: <queue-path>
Started: <iso>
Ended: <iso>
Duration: <Hh Mm>
Status: <COMPLETE | KILL-SWITCH | PRE-FLIGHT-FAILED> <— ACCEPTANCE OPEN | — ACCEPTANCE UNKNOWN | omit only when every attempted item explicitly reports acceptance COMPLETE>

## Items

| # | Plan | Execution | Acceptance | Commits | Issues closed | Park issue |
|---|------|-----------|------------|---------|---------------|------------|
| 1 | phase-g-plan.md | DONE | DEFERRED | 7 | #41, #42, #43 | -- |
| 2 | phase-2.1-plan.md | PARKED | UNKNOWN | 2 | #44 | #99 |
| 3 | phase-n-plan.md | DONE | COMPLETE | 5 | #50, #51 | -- |
| 4 | phase-4.7-plan.md | SKIPPED (kill-switch) | UNKNOWN | -- | -- | -- |

## Acceptance and next actions

- Item 1 — `DEFERRED`

  <verbatim acceptance.handoff, including the concrete cue>

  Next action (verbatim): `Please run M5 next.`
- Item 2 — `UNKNOWN`: no upstream acceptance handoff was supplied.
- Item 3 — `COMPLETE`: upstream explicitly reported acceptance complete.

## Triage list (parked items)

- #99 (phase-2.1, item 2): <halt-class summary> — see issue for context.

## Numbers

- Items attempted: 3 of 4
- Automated executions DONE: 2
- Acceptance COMPLETE: 1
- Acceptance DEFERRED: 1
- Acceptance UNKNOWN: 1
- Items PARKED: 1
- Items SKIPPED: 1 (kill-switch)
- Total commits landed: 12
- Total issues closed: 5
- Total park issues filed: 1
```

A `commits` or `issues_closed` value recorded as `null` renders as `unknown` in the Items table. The two totals sum only stated values and append `(<K> items unknown)` when any item's value is `null`. The acceptance section is never omitted for an attempted item: print its verbatim handoff/action, or state that the upstream result supplied none. DONE means automated queue execution only; it never means accepted, delivered or published. When there are zero parked items, the "Triage list" section is omitted. When there are zero DONE items, surface `Status: COMPLETE (0 of N automated executions DONE — investigate)`.

---

## State file schema

`.build-queue-state` in the queue file's directory, JSON. Gitignored.

```json
{
  "queue_path": "queue.txt",
  "queue_mtime": 1779200000.0,
  "queue_sha256": "<sha256 of exact queue-file bytes>",
  "queue_items": [
    {
      "item": 1,
      "plan": "C:/.../phase-g-plan.md",
      "forwarded_flags": ""
    },
    {
      "item": 2,
      "plan": "C:/.../phase-2.1-plan.md",
      "forwarded_flags": "--phase 1 --steps 1,2,3"
    }
  ],
  "started": "2026-05-23T22:00:00Z",
  "items": [
    {
      "item": 1,
      "plan": "C:/.../phase-g-plan.md",
      "verdict": "DONE",
      "commits": 7,
      "issues_closed": [41, 42, 43],
      "acceptance": {
        "status": "DEFERRED",
        "handoff": "<verbatim Manual UAT block and cue>"
      },
      "next_action": "Please run M5 next.",
      "timestamp": "2026-05-23T22:47:00Z"
    },
    {
      "item": 2,
      "plan": "C:/.../phase-2.1-plan.md",
      "verdict": "PARKED",
      "halt_reason": "Quality-gate hard fail (test count regressed)",
      "issue": 99,
      "commits": 2,
      "issues_closed": [44],
      "acceptance": {
        "status": "UNKNOWN",
        "handoff": null
      },
      "next_action": null,
      "timestamp": "2026-05-23T23:18:00Z"
    }
  ],
  "kill_switch_hit_before_item": null
}
```

Resume identity uses exact `queue_sha256` and exact ordered `queue_items`; `queue_mtime`
is retained only as operator-facing metadata. Even when a filesystem reports the same mtime,
changing `--phase 1` to `--phase 2`, changing a `--steps` list, editing a plan token, or
changing any other queue byte changes the hash and holds. An older checkpoint without both
identity fields holds for explicit recovery or `--fresh`; it is never upgraded in place.

**Atomic checkpoint rule.** State is execution authority, not disposable observability. For every initialization, IN_PROGRESS transition and terminal transition, write the complete JSON—including the immutable `queue_sha256` and complete ordered `queue_items` captured at Step 3—to a unique same-directory temporary file, flush and close it, parse it back and validate its queue identity, entry shapes, same-index/same-plan cross-references, uniqueness and ordered-prefix invariant, then atomically replace the canonical path. A live write permits only a terminal prefix plus the one trailing next-item IN_PROGRESS entry described in Step 0.5; a terminal write permits only the terminal prefix. Preserve the prior valid canonical bytes as `.build-queue-state.previous` until the new canonical file is validated. Never expose a partially written canonical document. If any write/validation/replace step fails, leave the last valid canonical checkpoint and partial work untouched and emit `STATE-RECOVERY-HOLD`.

Missing, malformed, identity-mismatched or ambiguous canonical state under `--resume`, and every IN_PROGRESS entry, requires the same finite recovery hold. The operator may inspect the preserved canonical/previous/temp files and partial work, then explicitly select a verified checkpoint or choose a new `--fresh` run. The queue never makes that triage decision, silently renames evidence, or replays an item.

---

## Relationship to other skills

| Skill | Role |
|---|---|
| `/plan-expedite` | Invoked per-item in default mode (never `--new-window`) to run plan-review autofix → plan-redline `--local-only` → plan-wrap autofix → verified plan-to-repository target selection → the authorized repo-sync → `task-handoff --next-task build-phase`. The queue consumes its success result and invokes build-phase itself; it does not relay or execute plan-expedite's operator-facing continue commands. |
| `/build-phase` | Invoked per-item to execute the plan's build steps; the halt contract here is the source of truth for what halts mean |
| `/loop` | Different shape — `/loop` repeats one prompt on an interval; `/build-queue` drains a queue of distinct plans once |
| `/repo-update` | Not invoked by this skill; each `/build-phase` step closes its own issue, but the post-phase docs+README+commit pass is left for the operator to run per-project in the morning |

## Limitations

- One queue at a time per directory. Two `/build-queue` runs on the same queue file have undefined behavior (state file races). Don't do that.
- Per-item halts file an issue on the plan's repo — requires `gh auth status` to be valid for every distinct repo in the queue. Pre-flight does NOT verify `gh auth` per repo; first halt on a non-authed repo falls back to the local `.build-queue-park-item-N.md` file.
- No cross-item dependencies. If item 2's plan depends on item 1 landing first, that's an ordering responsibility of the operator (and the queue ordering preserves it). The skill does not detect dependency violations.
- No auto-rollback. If a `/build-phase` lands partial commits then halts mid-step, those commits remain on the branch. `/build-phase` itself does not roll back; `/build-queue` does not either. The morning triage owns rollback decisions.
- Each item's `/plan-expedite` runs `task-handoff --next-task build-phase`, which rewrites the session's Next Action to that item's `/build-phase`. After auto-compaction, queue continuation rests on `.build-queue-state` and the compaction summary, not on that Next Action.
- The morning summary's "commits landed" and "issues closed" counts come from count lines in `/build-phase`'s own final report, NOT a separate `git log` scan. If `/build-phase` lies or under-reports, the summary inherits that. A `/build-phase` report that states no such line yields `unknown`, never an inferred number.
