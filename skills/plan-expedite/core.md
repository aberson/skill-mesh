# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

# plan-expedite core

## Purpose and complete operating contract

`/plan-expedite --plan <path>` runs the full plan -> review -> redline -> wrap -> sync ->
handoff pipeline as one autonomous step, in the order the workspace plan-and-issue-flow rule
owns (`.claude/rules/plan-and-issue-flow.md`: plan-review -> plan-redline -> plan-wrap ->
repo-sync). Default output: TWO continue commands in order — first a `/goal
"<condition>"` line that arms the Stop hook over the agent-completable span, then the
`/build-phase --plan <path>` command — both to run **in the same window** — no forced
`/compact`, because auto-compaction handles
context on its own when it fills and the `SessionStart` re-inject hook reloads `current.md`
afterward. (A focused `/compact` before the long build is optional — see step 5.) Add
`--new-window` to hand off to a fresh window instead: a durable `current.md` write
(`task-handoff --next-task`), then `/session-wrap --end` renders the handoff to disk
(`.claude/task-state/handoff-prompt.md`) and prints the Pick-up-here block.

---

## Execution model — autonomous, invoke sub-skills through the host's skill-invocation adapter (HEAVY)

This skill's whole reason to exist is that the operator does not want to type `/plan-review` → wait → `/plan-redline` → wait → `/plan-wrap` → wait → `/repo-sync` → wait → handoff. They invoked `/plan-expedite` to have every stage for the selected handoff mode happen as one autonomous run. Therefore:

1. **Execute, do not advise.** When invoked, you MUST invoke each sub-skill through the host's skill-invocation adapter in the order specified in the "Sub-skill chain" section. Do NOT respond by emitting the chain as text (e.g. "Next: `/plan-review` → `/plan-redline` → `/plan-wrap` → `/repo-sync` → `/session-wrap` → `/build-phase`"). That listing-the-steps response is the single most common failure mode for this skill — if you find yourself about to type that sentence, stop and invoke the next sub-skill through the adapter instead.

2. **No mid-run confirmations.** Do not ask "Should I run /plan-review now?", "Apply autofixes?", "Any feedback on the proposal before I continue?", "Proceed to /plan-wrap?", "Ready to sync issues?", or any other (y/n) gate, and do not wait for redline feedback. The operator opted into the chain by invoking `/plan-expedite`. Halt only on the cases the "Halt template" section enumerates — sub-skill non-zero exit, a result the "Reading a sub-skill result" rules do not accept (a remaining Blocker, genuine ambiguity requiring operator judgment, or no determinable success), a missing sub-skill, or a failed input check. Everything else proceeds.

3. **Minimal between-step narration.** Between sub-skill invocations, one brief sentence is enough ("plan-review returned READY with 3 autofixes applied; invoking plan-redline"). Do not re-describe what the next sub-skill is going to do — its own core handles that.

4. **Final output is the continue command(s) (or, with `--new-window`, the Pick-up-here block), verbatim.** On default success, the final output is the `/clear`-first recycle shape: on Claude, one `Run in:` execution-context line (other hosts omit it; see step 5), a fenced `/clear` block, then a fenced pair — `/goal "<condition>"` (scoped to the agent-completable automated span, per step 5 of the chain) followed by `/build-phase --plan <path>` — no summary, paraphrase, or "here's what to do next" preamble. With `--new-window`, the Pick-up-here block that `/session-wrap --end` prints (exact next command + digest + pointer to the rendered `handoff-prompt.md`) IS the final output; emit it as-is.

---

## When to use

- After `/plan-init` or `/plan-feature` produces a plan.md, before `/build-phase` runs.
- When you want one command instead of remembering plan-review -> plan-redline -> plan-wrap -> repo-sync -> task-handoff (and, with `--new-window`, session-wrap) in order.
- Re-running is safe: each sub-skill is idempotent on the plan's actual state (the autofix-applied markers from Steps 7-8 record which steps autofix touched; they never exempt a step from a check — per [`../plan-review/core.md`](../plan-review/core.md) § "Autofix marker"; plan-redline republishes to the plan's recorded `Proposal:` locator) and `/plan-expedite` skips already-completed sub-skills (per `.plan-expedite-state` resume detection).

## When NOT to use

- Mid-build-phase (this skill is a PRE-build prep; /build-phase has its own flow).
- For ad-hoc plan edits without intent to ship (use individual skills directly).
- If you want to manually review autofix changes before applying (use individual skills with --no-autofix).
- If you want your redline feedback folded BEFORE issues are minted: run `/plan-review`, then `/plan-redline` and reply (it folds your feedback), then `/plan-expedite` — its run republishes the folded plan and continues.

## Arguments

| Arg | Required | Default | Description |
|---|---|---|---|
| `--plan` | yes | -- | Path to the plan.md file (e.g., `documentation/foo-plan.md`) |
| `--new-window` | no | false | Fresh-window handoff: run `task-handoff --next-task` (durable `current.md` write) FIRST, then `/session-wrap --end` — the handoff is rendered to `.claude/task-state/handoff-prompt.md` and the screen shows the Pick-up-here block (exact next command + <=6-line digest + pointer; no word floor). Use when you want the next step in a fresh window. |

## Flow

### Input check

Before anything else, confirm `--plan` was given and names a readable file. If not (including a
bare `/plan-expedite`), emit the halt template with `<sub-skill name>` = `input`, `Plan state:
unchanged` and `GitHub state: unchanged`; invoke no sub-skill and write no state file. Never
guess a plan: a guessed plan would flow into repo-sync's issue mutation.

### Stale-plan check (per BPA plan section 5 D9)

Check `plan.md`'s mtime before invoking any sub-skill. If >30 days old, print a warning but CONTINUE — do not bail:

```text
warning: plan.md was last modified <N> days ago (<date>). Autofix may reshape stale plans significantly. Continuing — review the auto-applied fixes before /build-phase if drift is a concern.
```

### Resume detection

Check for `.plan-expedite-state` JSON file in the project root (sibling to plan.md). Schema:

```json
{
  "plan_path": "documentation/foo-plan.md",
  "plan_mtime": 1779167384.42,
  "handoff_mode": "in-window",
  "completed": [
    {"skill": "plan-review", "verdict": "READY", "timestamp": "..."},
    {"skill": "plan-redline", "verdict": "PUBLISHED", "timestamp": "..."},
    {"skill": "plan-wrap", "verdict": "READY", "timestamp": "..."}
  ],
  "halted_at": null
}
```

`handoff_mode` is `"in-window"` (default — `task-handoff --next-task`) or `"new-window"`
(`--new-window` flag — `task-handoff --next-task` then `session-wrap --end`). Recorded at
run start; used by resume logic to invoke the correct final sub-skill(s) on re-entry.

The **stage list** for a mode is, in order: `plan-review`, `plan-redline`, `plan-wrap`,
`repo-sync`, `task-handoff`, with `session-wrap` appended for `new-window`. (`user-project` is an
advisory pin inside the plan→repo boundary, not a stage, and is never recorded.)

`plan_mtime` is a numeric float — seconds since the Unix epoch, as returned by `os.path.getmtime(plan_path)` or `stat -c %Y`. No timezone, no string parsing. Comparison uses a 1-second tolerance: `abs(current_mtime - state_mtime) <= 1.0`. The tolerance accommodates filesystems with different mtime precision (NTFS records to 100ns, FAT32 rounds to 2s) and avoids spurious "plan changed" detections from format-only round-trips.

Logic:
- If file does not exist: fresh run, execute every stage in the stage list, in order.
- If file exists AND `abs(current_mtime - state.plan_mtime) <= 1.0` AND the `skill` names in `completed[]` are, in order, an exact prefix of the stage list for the recorded `handoff_mode`: skip those stages. Start from the first stage after the prefix (or from where `halted_at` left off).
- If file exists BUT the mtime difference exceeds 1 second: plan was edited since last run; discard the resume state and start fresh.
- If `completed[]` is not an in-order prefix of the stage list — for example a state file written before plan-redline joined the chain, which lists `plan-wrap` without `plan-redline` — discard the resume state and start fresh. Never run a stage out of order, and never run plan-redline after plan-wrap without re-running plan-wrap.
- **Malformed state file:** if `.plan-expedite-state` exists but is invalid JSON, missing required keys (`plan_path`, `plan_mtime`, `completed`, `halted_at`), or has the wrong shape (e.g., `plan_mtime` not numeric, `completed` not a list), log a warning citing the malformation, rename the bad file to `.plan-expedite-state.malformed-<timestamp>` for forensics, and treat as a fresh run (proceed with every stage). Do NOT halt — an autonomous prep skill should self-heal from corrupted resume state, not require operator intervention to clear it.

Update `completed[]` with the sub-skill name and write the file back after each successful sub-skill. On halt, set `halted_at` to the sub-skill name that failed and persist.

### Sub-skill chain

Call each sub-skill below through the host's skill-invocation adapter, in order. Before the first invocation, `cd` to the project root containing `<plan-path>` using the host shell. Between invocations, one brief progress sentence ("plan-review returned READY; invoking plan-redline") is enough — do NOT re-emit the chain as prose.

**Path-passing contract:** `/repo-sync` and `/plan-redline` document a `--plan` argument; `/plan-review`, `/plan-wrap`, and `/session-wrap` operate on the plan via conversation context (they read the plan path from the invoking turn's prose or from cwd). Pass the path in the invocation's `args` so the sub-skill picks it up.

**Reading a sub-skill result.** Read the exit code and the result after each invocation returns. When the report carries a `Verdict:` line, read that line wherever it appears in the report; otherwise read the sub-skill's documented closing lines or, for a sub-skill that documents none (task-handoff, session-wrap), its exit status and the durable write it documents. On success, append to `completed[]` in `.plan-expedite-state` and proceed to the next sub-skill. On halt, write the halt template (see below) and stop. These rules apply to every stage:
- **No inferred success.** A result with no determinable success (no verdict and no documented closing line) or a statement that the sub-skill did not run (for example `<skill> not run:` or `NOT REVIEWED`) halts.
- **A remaining Blocker always halts.** A `NEEDS WORK` verdict with at least one blocker, or a Blocker-tier finding the report's auto-applied block does not cover, is never auto-answerable.
- **Never answer for the operator.** plan-expedite writes no answer to a sub-skill's question into the plan and records no operator choice. An open input item lets the chain continue only when it is not a Blocker and its answer is already stated in the plan or in the source the item cites (a lookup, not a choice). An item that needs an operator choice is genuine ambiguity and halts. This open-input rule covers plan-review's items needing input and any `NEEDS WORK` result. Gap items under plan-wrap's `READY WITH GAPS: M gaps` are awareness-only by plan-wrap's contract (`/repo-sync` may proceed; Gaps are not halt-class) and never trigger it.

1. **Invoke `plan-review` through the host's skill-invocation adapter** with `args: "--autofix <plan-path>"`.
   - Success criteria: verdict READY or "READY (auto-fixed N items)" (or the closing line "Plan is ready for `/plan-wrap` and `/repo-sync`."), or open input items the rules above let continue.
   - Halt criteria: a result the rules above do not accept, OR sub-skill non-zero exit, OR sub-skill missing.

2. **Invoke `plan-redline` through the host's skill-invocation adapter** with `args: "--plan <plan-path> --local-only"` — the redline checkpoint: publish the review-corrected plan as a P/D proposal, then continue without waiting.
   - Success criteria: the report returns a proposal locator (URL or repository-relative HTML path) and the plan carries its `Proposal:` line and `### Decision Inventory`. Record `"verdict": "PUBLISHED"`.
   - Do not wait for, request, or simulate operator feedback in this run, and do not fold. plan-expedite never marks an item `P`, edits a `D` item, or changes an inventory status. Agent-defaulted items stand as written (plan-redline: anything unmentioned lands as written).
   - The proposal file plan-redline writes is not a code path for task-handoff's scoped commit in either handoff mode.
   - The one-sentence transition names the locator and the fold path, e.g. "plan-redline published `<locator>`; agent defaults stand unless you reply via /plan-redline (before the build starts, then re-run /plan-expedite); invoking plan-wrap".
   - Halt criteria: no locator returned, OR publication impossible with no standalone HTML fallback, OR the sub-skill asks a question instead of publishing, OR sub-skill non-zero exit, OR sub-skill missing.
   - Feedback after this run, **before `/build-phase` starts:** the operator replies through `/plan-redline`, which folds the edits into the plan. Re-running `/plan-expedite` then sees the edited plan (resume detection), re-runs plan-review → plan-redline → plan-wrap, and repo-sync updates any issues already minted — the pre-build re-run the plan-and-issue-flow rule names.
   - Feedback **after `/build-phase` has started** (at once under build-queue, or once the operator runs the continue pair): never re-run `/plan-expedite` (see "When NOT to use"). Fold through `/plan-redline`, then run `/plan-review` and `/plan-wrap` (the rule's re-run after a material fold), then `/repo-sync` for issues already minted.

3. **Invoke `plan-wrap` through the host's skill-invocation adapter** with `args: "--autofix <plan-path>"`.
   - Success criteria: verdict READY, "READY (auto-fixed N items)", or "READY WITH GAPS: M gaps" (plan-wrap-only — 0 Blockers, M≥1 Gaps, /repo-sync may proceed; its Gap items are awareness-only and never trigger the open-input rule).
   - Halt criteria: "NEEDS WORK: N blockers, M gaps" (always — plan-wrap requires Blockers fixed before /repo-sync), OR any other result the rules above do not accept, OR sub-skill non-zero exit, OR sub-skill missing.

   **Plan→repo boundary — announce + pin the context switch (`working-directory.md`).**
   Immediately BEFORE invoking `repo-sync` (whether `plan-wrap` just ran or was resumed-past — this
   block fires on the resume-to-repo-sync path too), make the plan→repo context switch
   VISIBLE — until now it was silent (`plan-review`/`plan-redline`/`plan-wrap` are plan-doc ops that are
   dev-root-fine; `repo-sync` is the first project-repo op). Emit exactly ONE signpost line (this
   is the one-sentence transition of rule 3; it sits mid-chain and never wraps the final `/goal` +
   `/build-phase` output). Resolve which repo the plan belongs to:
   - Compute `$planRepo` = walk up from the plan file's directory to the nearest `.git`; and
     `$codingRoot` = walk up for `.claude/observatory/registry.toml`.
   - **Nested project repo registered in the observatory registry** (`$planRepo` ≠ `$codingRoot`
     and its `slug`/`path` matches a registry entry): **auto-pin it** — invoke `/user-project` via
     the host skill-invocation adapter with `args: "<slug>"` — then emit:
     `-> repo phase for <slug> (<abs-repo>) - context pinned (repo-sync + downstream honor it regardless of cwd)`.
   - **Coding-root work** (`$planRepo` == `$codingRoot` — the plan lives in the coding-root repo,
     e.g. a `dev/...` plan): cwd is already coding-root, so do NOT pin; emit:
     `-> repo phase - coding-root work (<coding-root>); no project pin`.
   - **Unresolvable** (a nested repo whose basename is not a registry `slug`/`path`): do NOT guess
     or pin — emit the proactive switch-message and proceed:
     `this is <repo-basename> work; a switch might help (open its window, or register it + /user-project <name>)`.

   Never halt here — the pin is advisory; on any resolution error, log one line and continue to
   `repo-sync`. Nothing is recorded in `.plan-expedite-state` (the pin lives in task-state).

4. **Invoke `repo-sync` through the host's skill-invocation adapter** with `args: "--plan <plan-path>"` (autonomous default per Step 6 — no `--dry-run`).
   - Same success / halt criteria (the result rules above).

5. **Invoke the final sub-skill, then emit the continue command** — depends on `--new-window`:

   **Default (no `--new-window`):** Invoke `task-handoff` through the host's skill-invocation adapter with
   `args: "--next-task build-phase"` (it writes current.md + MEMORY + push — the durable
   handoff state).
   - Then emit the continue commands verbatim as the `/plan-expedite` final output — the
     **`/clear`-first recycle shape** (operator preference, folded 2026-07-21 from
     `feedback_plan_expedite_clear_before_build`): on Claude, one execution-context line, then
     TWO fenced blocks in order, no preamble, no summary. The execution-context line
     (`command-presentation.md`) is the Claude rendering: emit it only on the Claude host,
     where `/clear` is a window primitive and `model-tiering.md` owns the tier. It sits
     immediately above Block 1 and covers both blocks:
     `Run in: this window after /clear @ <target dir> · Model: <tier>`. `<target dir>` is the
     directory `/build-phase` runs from — the project folder name for a nested project repo,
     `dev` for coding-root work, an absolute path when the short name is ambiguous. `<tier>` is
     `Opus (default)` unless that tiering policy selects otherwise; never name a
     fable tier for this build-bearing pair. The line is control metadata, not a summary or
     preamble. Any other host omits the line and emits the two blocks alone (the canonical
     no-preamble output); it never describes its own session as `this window after /clear`
     and never names a Claude tier as its model. Block 1 is the fresh-context recycle — safe
     because `task-handoff --next-task` just wrote the durable state and the `SessionStart`
     hook (matcher `compact|resume|clear`) re-injects it after the clear:
     ```
     /clear
     ```
     Block 2 — pasted after the resume echo appears — is the pair (goal first: the `/goal`
     arms the Stop hook over the automated span and is user-typed, a skill cannot arm
     `/goal` itself, so it sits above `/build-phase`):
     ```
     /goal "<condition>"
     /build-phase --plan <plan-path>
     ```
     Two separate blocks, never one — the `/clear` is an observation point (wait for the
     resume echo) per `command-presentation.md`.
   - **Derive the `<condition>` from the plan, scoped to the AGENT-COMPLETABLE slice.**
     plan-expedite has already read the plan, so enumerate its steps. The agent-completable
     (automated) steps are the ones the agent builds end-to-end with its own tools:
     `Type: code` and `Type: conditional`. NOT agent-completable: every `Type: operator`
     step, every Manual M-step (M1/M2/M3), AND every `Type: wait` step — a `Type: wait`
     step is an intentional build-phase halt (halt-contract class #4: the orchestrator
     stops and the operator resumes in a fresh session after the clock-gated wait), so its
     finish line is not reachable by the agent in-session. Build the condition over ONLY
     the contiguous automated (`code`/`conditional`) steps up to the FIRST
     operator / Manual-M / wait boundary — a goal that spans an operator, Manual M-step,
     or wait step busy-loops forever, because the Stop hook re-fires against a finish line
     the agent's own tools cannot reach. Form:
     `"<plan-name> automated steps <N..M> are all marked Status: DONE in <plan-path>
     (issues #<a>-#<b> closed), and `<test-cmd>` / `<typecheck-cmd>` / `<lint-cmd>` exit 0
     — STOP before the operator/wait/Manual steps (M1/M2/M3, issues #<x>-#<y>); those are an
     operator handoff, not part of this goal"`. Cite the GitHub issue numbers for the
     automated steps and for the closing/quality-gate conditions wherever the plan makes
     them derivable; omit a clause only if the plan genuinely lacks it. If the plan is
     all-automated (no `Type: operator` steps, no `Type: wait` steps, and no Manual
     M-steps), target ALL steps and drop the STOP-before clause.
   - Record `handoff_mode: "in-window"` in `.plan-expedite-state`.
   - **Optional focused reset.** A proactive `/compact` before a long build-phase gives
     cleaner context than auto-compaction's best-guess summary — but it is the operator's
     choice, not the default, and is never auto-emitted as the mandated output (there is no
     way to trigger `/compact` programmatically). If they want it, they type it first:
     `/compact Focus on build-phase for [plan-name]: step list in plan.md, issue numbers
     filled, current.md has next action`.

   **`--new-window` mode:** TWO invocations, in this order — the durable write MUST land
   before session-wrap runs because `handoff-prompt.md` is a RENDERING of `current.md`:
   the render can only carry state already on disk. The default transition RECYCLES this
   window: `/clear` fires the SessionStart re-inject hook (matcher: `compact|resume|clear`),
   then the operator pastes the pair. The rendered handoff + fresh-window opener remain
   the closed-window alternative (the hook does not fire on plain startup):

   1. **Invoke `task-handoff` through the host's skill-invocation adapter** with `args: "--next-task build-phase"`
      — the durable `current.md` write (finished prep lands in Completed; WIP, Next
      Action, and Status repoint at the build; MEMORY.md updated; commit + push). Set the
      written Next Action to the SAME agent-completable `/goal "<condition>"` line
      (derived per the Default-branch bullet above) followed by the `/build-phase --plan
      <plan-path>` command, goal line first, so the rendered handoff carries the armed
      pair.
   2. **Invoke `session-wrap` through the host's skill-invocation adapter** with `args: "--end <plan-path>"` —
      `--end` explicitly, never bare: end-window is the route `--new-window` wants, and a
      bare invocation triages and may route `continue`. session-wrap renders the handoff
      to disk (`.claude/task-state/handoff-prompt.md`, a rendering of the `current.md`
      just written — one source of truth) and prints the Pick-up-here block per its
      screen contract: digest + pointer first, then numbered Step blocks — Step 1
      `/clear`, an optional `/model <pinned-default>` step when the session's model was
      explicitly overridden this session, and the FINAL fenced block carrying the
      `/goal` + `/build-phase` pair verbatim (goal line first). No word floor.
      session-wrap's route step 1 checkpoint must preserve step 1's Next Action
      verbatim (its no-regress clause) — the pair survives into the render and into
      the final Step block.
   - Emit session-wrap's Pick-up-here block verbatim as the `/plan-expedite` final
     output. Do not paraphrase, do not summarize, do not add a preamble. VERIFY the
     `/goal` + `/build-phase` pair is the block's final fenced Step — the last lines on
     screen are what the operator runs. If the block arrived without the pair
     (defensive), append a final Step carrying both lines in ONE fenced code block —
     never as bare indented lines.
   - Record `handoff_mode: "new-window"` in `.plan-expedite-state`.

   The `--new-window` flag is the escape hatch for users who want the next step in a
   fresh window instead of continuing in-window: durable state on disk plus a rendered
   handoff file, not a wall of copy-paste text.

### Halt template (per BPA plan section 5 D8 — generic, no per-skill enumeration)

Write the following template verbatim on any sub-skill non-success exit or failed input check:

```text
/plan-expedite halted at: <sub-skill name | input>
Reason: <captured stderr / verdict line / unaccepted result>
Plan state: <unchanged | edited by completed stages (cite which steps autofix touched per the autofix-applied markers in plan.md — the per-fix enumeration is the sub-skill's "Auto-applied N fixes" report block — and any Decision Inventory / Proposal: write)>
GitHub state: <unchanged | issues created/updated (cite count if repo-sync ran)>
To resume: fix the cited issue, then re-run /plan-expedite --plan <path>
           (already-completed sub-skills are skipped via state inference from .plan-expedite-state)
```

Stop without producing the final continue command / Pick-up-here block after printing. The `.plan-expedite-state` records `halted_at: <sub-skill name>` for resume (a failed input check writes no state).

Use the same five-line template regardless of which sub-skill fails (plan-review, plan-redline, plan-wrap, repo-sync, task-handoff, session-wrap) or whether the input check failed; per-sub-skill diagnostic detail belongs in the cited stderr, not in `/plan-expedite`'s template.

## Relationship to other skills

| Skill | Role |
|---|---|
| `/plan-init`, `/plan-feature` | Produce the plan.md `/plan-expedite` operates on |
| `/plan-review`, `/plan-wrap` | Autofix sub-skills (Steps 7-8 of BPA plan) |
| `/plan-redline` | Redline checkpoint between plan-review and plan-wrap: publishes the P/D proposal; the chain does not wait for feedback (the operator folds later via `/plan-redline`; before the build starts, then re-runs `/plan-expedite`; after it starts, runs `/plan-review` + `/plan-wrap`, then `/repo-sync`) |
| `/repo-sync` | Issue-sync sub-skill (Step 6) |
| `/user-project` | Advisory project pin at the plan→repo boundary (never a stage) |
| `/task-handoff` | Durable boundary write (`--next-task build-phase`) in both modes |
| `/session-wrap` | End-window handoff sub-skill (`--new-window` only, invoked `--end` AFTER the durable `task-handoff --next-task` write; renders `handoff-prompt.md` + prints the Pick-up-here block) |
| `/build-phase` | Continues in-window from the `/goal` + `/build-phase` commands /plan-expedite emits (the `/goal` arms the Stop hook over the automated span; or, with `--new-window`, the fresh window opens from the rendered handoff carrying both) |
| `/build-queue` | Invokes `/plan-expedite --plan <abs-path>` per queue item; a halt parks the item |

## Limitations

- Resume state lives in a single `.plan-expedite-state` file in the project root. Multiple concurrent `/plan-expedite` invocations on the same plan have undefined behavior — don't do that.
- Concurrent operator edits to `.plan-expedite-state` during a run have undefined behavior. Don't edit the file while `/plan-expedite` is running.
- Sub-skill failures halt the chain; resume requires manual operator inspection. By design — autofix's promise is to handle the boring cases, not the surprising ones.
- Redline feedback is asynchronous: the chain publishes the proposal and continues, so agent-defaulted items flow into wrap, issues and the build as written. Feedback that arrives after repo-sync costs issue edits (the N+1 cost): through a `/plan-expedite` re-run before the build starts, or through `/plan-review` + `/plan-wrap` + `/repo-sync` after it starts (never a `/plan-expedite` re-run mid-build). To fold feedback before issues are minted, use the review → redline → expedite path under "When NOT to use".
