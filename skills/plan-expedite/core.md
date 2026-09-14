# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

# plan-expedite core

## Purpose and complete operating contract

`/plan-expedite --plan <path>` prepares a plan through review, wrap, issue sync
and durable handoff. With an explicitly established coordinator/caller, it returns
a ready work packet to that coordinator; no session reset or goal command is needed.
Standalone interactive use retains the existing continue-command handoff. Preparation
alone never starts a build or expands existing execution authorization.

---

## Execution model — autonomous, invoke sub-skills through the host's skill-invocation adapter (HEAVY)

This skill's whole reason to exist is that the operator does not want to type `/plan-review` → wait → `/plan-wrap` → wait → `/repo-sync` → wait → `/session-wrap`. They invoked `/plan-expedite` to have those four happen as one autonomous run. Therefore:

1. **Execute, do not advise.** When invoked, you MUST invoke each sub-skill through the host's skill-invocation adapter in the order specified in the "Sub-skill chain" section. Do NOT respond by emitting the chain as text (e.g. "Next: `/plan-review` → `/plan-wrap` → `/repo-sync` → `/session-wrap` → `/build-phase`"). That listing-the-steps response is the single most common failure mode for this skill — if you find yourself about to type that sentence, stop and call the `Skill` tool instead.

2. **No mid-run confirmations.** Do not ask "Should I run /plan-review now?", "Apply autofixes?", "Proceed to /plan-wrap?", "Ready to sync issues?", or any other (y/n) gate. The operator opted into the chain by invoking `/plan-expedite`. Halt only on the cases the "Halt template" section enumerates — sub-skill non-zero exit, genuine ambiguity surfaced under "Needs your input:" requiring operator judgment, or missing sub-skill. Everything else proceeds.

3. **Minimal between-step narration.** Between sub-skill invocations, one brief sentence is enough ("plan-review returned READY with 3 autofixes applied; invoking plan-wrap"). Do not re-describe what the next sub-skill is going to do — its SKILL.md handles that.

4. **Final output follows the selected handoff mode.** Coordinator mode returns the packet summary defined in Step 4; it never emits `/clear` or `/goal`. The following continue-command rules apply ONLY to interactive mode. **Interactive final output is the continue command(s) (or, with `--new-window`, the Pick-up-here block), verbatim.** On default success, the final output is the `/clear`-first recycle shape: a fenced `/clear` block, then a fenced pair — `/goal "<condition>"` (scoped to the agent-completable automated span, per Step 4 of the chain) followed by `/build-phase --plan <path>` — no summary, paraphrase, or "here's what to do next" preamble. With `--new-window`, the Pick-up-here block that `/session-wrap --end` prints (exact next command + digest + pointer to the rendered `handoff-prompt.md`) IS the final output; emit it as-is.

---

## When to use

- After `/plan-init` or `/plan-feature` produces a plan.md, before `/build-phase` runs.
- When you want one command instead of remembering plan-review -> plan-wrap -> repo-sync -> session-wrap in order.
- Re-running is safe: each sub-skill is idempotent on the plan's actual state (the autofix-applied markers from Steps 7-8 record which steps autofix touched; they never exempt a step from a check — per [`../plan-review/core.md`](../plan-review/core.md) § "Autofix marker") and `/plan-expedite` skips already-completed sub-skills (per `.plan-expedite-state` resume detection).

## When NOT to use

- Mid-build-phase (this skill is a PRE-build prep; /build-phase has its own flow).
- For ad-hoc plan edits without intent to ship (use individual skills directly).
- If you want to manually review autofix changes before applying (use individual skills with --no-autofix).

## Arguments

| Arg | Required | Default | Description |
|---|---|---|---|
| `--plan` | yes | -- | Path to the plan.md file (e.g., `documentation/foo-plan.md`) |
| `--handoff` | no | context | `coordinator` or `interactive`. Explicit flag wins; otherwise an established coordinator/calling orchestrator selects coordinator, and standalone use selects interactive. |
| `--new-window` | no | false | Fresh-window handoff: run `task-handoff --next-task` (durable `current.md` write) FIRST, then `/session-wrap --end` — the handoff is rendered to `.claude/task-state/handoff-prompt.md` and the screen shows the Pick-up-here block (exact next command + <=6-line digest + pointer; no word floor). Use when you want the next step in a fresh window. |

## Flow

Resolve handoff mode before reading resume state. A coordinator means an explicit
role in the user instruction or calling workflow, not merely that subagents exist.
`--new-window` implies interactive when no handoff is supplied; reject it together
with `--handoff coordinator` before writes. Load
`<repo>/_shared/task-state-schema.md` section "Coordinator handoff packet (v1)"
only for coordinator mode. Its packet schema, ownership and reconciliation rules
are the shared owner; do not create another schema here.

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
    {"skill": "plan-wrap", "verdict": "READY", "timestamp": "..."}
  ],
  "halted_at": null
}
```

`handoff_mode` is `"coordinator"` for coordinator mode, with `packet_path` added after
the packet is saved. Interactive mode uses `"in-window"` (default — `task-handoff --next-task`) or `"new-window"`
(`--new-window` flag — `task-handoff --next-task` then `session-wrap --end`). Recorded at
run start; used by resume logic to invoke the correct final sub-skill(s) on re-entry.

`plan_mtime` is a numeric float — seconds since the Unix epoch, as returned by `os.path.getmtime(plan_path)` or `stat -c %Y`. No timezone, no string parsing. Comparison uses a 1-second tolerance: `abs(current_mtime - state_mtime) <= 1.0`. The tolerance accommodates filesystems with different mtime precision (NTFS records to 100ns, FAT32 rounds to 2s) and avoids spurious "plan changed" detections from format-only round-trips.

Logic:
- Compare canonical plan identity AND handoff mode as well as mtime. A different
  plan never reuses the state. A mode-only change preserves successful review/wrap/
  repo-sync entries for the unchanged plan but reruns task-handoff/session-wrap for
  the selected mode; it never skips the new packet write. Old states without a
  coordinator mode remain interactive. Mtime is only a prep skip hint: coordinator
  dispatch still verifies the packet's committed plan and current byte identity.
- If file does not exist: fresh run, execute all 4 sub-skills sequentially.
- If file exists AND `abs(current_mtime - state.plan_mtime) <= 1.0`: skip every sub-skill in `completed[]`. Start from the first uncompleted (or from where `halted_at` left off).
- If file exists BUT the mtime difference exceeds 1 second: plan was edited since last run; discard the resume state and start fresh.
- **Malformed state file:** if `.plan-expedite-state` exists but is invalid JSON, missing required keys (`plan_path`, `plan_mtime`, `completed`, `halted_at`), or has the wrong shape (e.g., `plan_mtime` not numeric, `completed` not a list), log a warning citing the malformation, rename the bad file to `.plan-expedite-state.malformed-<timestamp>` for forensics, and treat as a fresh run (proceed with all 4 sub-skills). Do NOT halt — an autonomous prep skill should self-heal from corrupted resume state, not require operator intervention to clear it.

Update `completed[]` with the sub-skill name and write the file back after each successful sub-skill. On halt, set `halted_at` to the sub-skill name that failed and persist.

### Sub-skill chain

Call each sub-skill below through the host's skill-invocation adapter, in order. Before the first invocation, `cd` to the project root containing `<plan-path>` (use the Bash tool). Between invocations, one brief progress sentence ("plan-review returned READY; invoking plan-wrap") is enough — do NOT re-emit the chain as prose.

**Path-passing contract:** only `/repo-sync` documents a `--plan` CLI flag in its Arguments table; `/plan-review`, `/plan-wrap`, and `/session-wrap` operate on the plan via conversation context (they read the plan path from the invoking turn's prose or from cwd). Pass the path via the `args` parameter of the `Skill` call so the sub-skill picks it up.

Read the exit code and final verdict line after each `Skill` call returns. On success, append to `completed[]` in `.plan-expedite-state` and proceed to the next sub-skill. On halt, write the halt template (see below) and stop.

1. **Invoke `plan-review` through the host's skill-invocation adapter** with `args: "--autofix <plan-path>"`.
   - Success criteria: verdict READY, or "READY (auto-fixed N items)", or NEEDS WORK with only clarifying questions auto-answerable.
   - Halt criteria: genuine ambiguity surfaced under "Needs your input:" requiring operator judgment, OR sub-skill non-zero exit, OR sub-skill missing.

2. **Invoke `plan-wrap` through the host's skill-invocation adapter** with `args: "--autofix <plan-path>"`.
   - Success criteria: verdict READY, "READY (auto-fixed N items)", "READY WITH GAPS: M gaps" (plan-wrap-only — 0 Blockers, M≥1 Gaps, /repo-sync may proceed), or NEEDS WORK with only clarifying questions auto-answerable.
   - Halt criteria: same as plan-review (genuine ambiguity under "Needs your input:" requiring operator judgment, OR sub-skill non-zero exit, OR sub-skill missing).

   **Plan→repo boundary — announce + pin the context switch (`working-directory.md`).**
   Immediately BEFORE invoking `repo-sync` (whether `plan-wrap` just ran or was resumed-past — this
   block fires on the resume-to-repo-sync path too), make the plan→repo context switch
   VISIBLE — until now it was silent (`plan-review`/`plan-wrap` are plan-doc ops that are
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

3. **Invoke `repo-sync` through the host's skill-invocation adapter** with `args: "--plan <plan-path>"` (autonomous default per Step 6 — no `--dry-run`).
   - Same success / halt criteria.

4. **Coordinator handoff (`--handoff coordinator`).** After repo-sync, backfill
   and verify exact Issue fields, save a committed preparation revision, and build
   the packet from the COMPLETE ordered plan under the shared contract. Record the
   existing authorization as preparation-only or build-authorized with its source.
   Resolve the coordinator host independently of required builder/reviewer hosts;
   unknown execution capabilities are reported, not silently inferred from a label.

   Invoke `task-handoff` with `args: "--next-task coordinate-build --coordinator-packet
   <absolute-packet-path>"`. It writes the validated private packet, records its pointer
   in this session's checkpoint and performs the normal durable boundary save. Next
   Action is `task-handoff --resume-coordinator <absolute-packet-path>`; no goal or
   clear command is inserted. Record handoff_mode=coordinator and packet_path in
   `.plan-expedite-state` only after the callee succeeds.

   Return this compact summary plus the packet locator to the calling coordinator:

   ```text
   Preparation: READY
   Automated span: <selected steps and issues, or none>
   First assignment: <step and issue, or none>
   Boundary: <operator/wait/manual step, or none>
   Build authorization: <build-authorized | preparation-only>
   Execution capabilities: <verified requirements and unresolved requirements>
   Next owner: coordinator
   Packet: <absolute path>
   ```

   An immediate boundary is reported as `Automated span: none` with packet status
   NEEDS_OPERATOR; preparation can still be READY. Missing execution capability is
   visible in the summary and prevents dispatch, not successful preparation. The
   coordinator continues within already-granted build authority after execution
   preflight, without another confirmation. Otherwise it retains the prepared packet.
   This skill never launches builders as a side effect of preparation and never
   clears, ends or relocates the coordinator session. All later interactive branches
   in this section are bypassed in coordinator mode.

4. **Interactive handoff: invoke the final sub-skill, then emit the continue command** — depends on `--new-window`:

   If this session already carries a Coordinator packet header, add
   `--detach-coordinator` to the selected branch's single task-handoff invocation
   below (`--next-task build-phase`). Emit neither the
   interactive command pair nor a new-window opener until safe detachment succeeds.
   Preserve the prior packet and evidence for a later explicit resume.

   **Default (no `--new-window`):** Invoke `task-handoff` through the host's skill-invocation adapter with
   `args: "--next-task build-phase"` (it writes current.md + MEMORY + push — the durable
   handoff state).
   - Then emit the continue commands verbatim as the `/plan-expedite` final output — the
     **`/clear`-first recycle shape** (operator preference, folded 2026-07-21 from
     `feedback_plan_expedite_clear_before_build`): TWO fenced blocks in order, no preamble,
     no summary. Block 1 is the fresh-context recycle — safe because `task-handoff
     --next-task` just wrote the durable state and the `SessionStart` hook (matcher
     `compact|resume|clear`) re-injects it after the clear:
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

Write the following template verbatim on any sub-skill non-success exit:

```text
/plan-expedite halted at: <sub-skill name>
Reason: <captured stderr / verdict line>
Plan state: <unchanged | partially autofixed (cite which steps autofix touched per the autofix-applied markers in plan.md; the per-fix enumeration is the sub-skill's "Auto-applied N fixes" report block)>
GitHub state: <unchanged | issues created/updated (cite count if repo-sync ran)>
To resume: fix the cited issue, then re-run /plan-expedite --plan <path>
           (already-completed sub-skills are skipped via state inference from .plan-expedite-state)
```

Stop without producing the final continue command / Pick-up-here block after printing. The `.plan-expedite-state` records `halted_at: <sub-skill name>` for resume.

Use the same five-line template regardless of which sub-skill fails (plan-review, plan-wrap, repo-sync, task-handoff, session-wrap); per-sub-skill diagnostic detail belongs in the cited stderr, not in `/plan-expedite`'s template.

## Relationship to other skills

| Skill | Role |
|---|---|
| `/plan-init`, `/plan-feature` | Produce the plan.md `/plan-expedite` operates on |
| `/plan-review`, `/plan-wrap` | Autofix sub-skills (Steps 7-8 of BPA plan) |
| `/repo-sync` | Issue-sync sub-skill (Step 6) |
| `/session-wrap` | End-window handoff sub-skill (`--new-window` only, invoked `--end` AFTER the durable `task-handoff --next-task` write; renders `handoff-prompt.md` + prints the Pick-up-here block) |
| `/build-phase` | In coordinator mode consumes the selected packet via `--coordinator-packet` and explicit `--steps`; otherwise continues in-window from the `/goal` + `/build-phase` commands /plan-expedite emits (the `/goal` arms the Stop hook over the automated span; or, with `--new-window`, the fresh window opens from the rendered handoff carrying both) |

## Limitations

- Resume state lives in a single `.plan-expedite-state` file in the project root. Multiple concurrent `/plan-expedite` invocations on the same plan have undefined behavior — don't do that.
- Concurrent operator edits to `.plan-expedite-state` during a run have undefined behavior. Don't edit the file while `/plan-expedite` is running.
- Sub-skill failures halt the chain; resume requires manual operator inspection. By design — autofix's promise is to handle the boring cases, not the surprising ones.
