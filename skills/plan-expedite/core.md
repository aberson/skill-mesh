# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

# plan-expedite core

## Purpose and complete operating contract

`/plan-expedite --plan <path>` runs the full plan -> sync -> handoff pipeline as one
autonomous step. Default output is the plan's validated explicit initial handoff when one
is declared, otherwise TWO inferred continue commands in order — first a `/goal
"<condition>"` line that arms the Stop hook over the agent-completable span, then the
`/build-phase --plan <path>` command — both to run **in the same window** — no forced
`/compact`, because auto-compaction handles
context on its own when it fills and the `SessionStart` re-inject hook reloads `current.md`
afterward. (A focused `/compact` before the long build is optional — see step 4.) Add
`--new-window` to hand off to a fresh window instead: a durable `current.md` write
(`task-handoff --next-task`), then `/session-wrap --end` renders the handoff to disk
(`.claude/task-state/handoff-prompt.md`) and prints the Pick-up-here block.

---

## Execution model — autonomous, invoke sub-skills through the host's skill-invocation adapter (HEAVY)

This skill's whole reason to exist is that the operator does not want to type `/plan-review` → wait → `/plan-wrap` → wait → `/repo-sync` → wait → handoff. They invoked `/plan-expedite` to have every stage for the selected handoff mode happen as one autonomous run. Therefore:

1. **Execute, do not advise.** When invoked, you MUST invoke each sub-skill through the host's skill-invocation adapter in the order specified in the "Sub-skill chain" section. Do NOT respond by emitting the chain as text (e.g. "Next: `/plan-review` → `/plan-wrap` → `/repo-sync` → `/session-wrap` → `/build-phase`"). That listing-the-steps response is the single most common failure mode for this skill — if you find yourself about to type that sentence, stop and call the `Skill` tool instead.

2. **No mid-run confirmations.** Do not ask "Should I run /plan-review now?", "Apply autofixes?", "Proceed to /plan-wrap?", "Ready to sync issues?", or any other (y/n) gate. The operator opted into the chain by invoking `/plan-expedite`. Halt only on the cases the "Halt template" section enumerates — sub-skill non-zero exit, genuine ambiguity surfaced under "Needs your input:" requiring operator judgment, or missing sub-skill. Everything else proceeds.

3. **Minimal between-step narration.** Between sub-skill invocations, one brief sentence is enough ("plan-review returned READY with 3 autofixes applied; invoking plan-wrap"). Do not re-describe what the next sub-skill is going to do — its SKILL.md handles that.

4. **Final output is the continue command(s) (or, with `--new-window`, the Pick-up-here block), verbatim.** On default success, the final output is the `/clear`-first recycle shape. If the plan declares a valid `plan-expedite-initial-handoff-v1` block, preserve that block's command lines byte-for-byte; never reconstruct its `/goal`, drop a selector such as `--steps`, or broaden it to a bare full-plan invocation. A declared dry-run is a separate fenced observation block before the fenced `/goal` + actionable `/build-phase` pair. If no explicit block exists, use the inferred pair scoped to the agent-completable automated span per Step 4 of the chain. No summary, paraphrase, or "here's what to do next" preamble. With `--new-window`, the Pick-up-here block that `/session-wrap --end` prints (exact next command + digest + pointer to the rendered `handoff-prompt.md`) IS the final output; emit it as-is.

---

## When to use

- After `/plan-init` or `/plan-feature` produces a plan.md, before `/build-phase` runs.
- When you want one command instead of remembering plan-review -> plan-wrap -> repo-sync -> task-handoff (and, for `--new-window`, session-wrap) in order.
- Re-running is safe: each sub-skill is idempotent on already-applied state (per autofix-applied markers from Steps 7-8) and `/plan-expedite` skips already-completed sub-skills (per `.plan-expedite-state` resume detection).

## When NOT to use

- Mid-build-phase (this skill is a PRE-build prep; /build-phase has its own flow).
- For ad-hoc plan edits without intent to ship (use individual skills directly).
- If you want to manually review autofix changes before applying (use individual skills with --no-autofix).

## Arguments

| Arg | Required | Default | Description |
|---|---|---|---|
| `--plan` | yes | -- | Path to the plan.md file (e.g., `documentation/foo-plan.md`) |
| `--new-window` | no | false | Fresh-window handoff: run `task-handoff --next-task` (durable `current.md` write) FIRST, then `/session-wrap --end` — the handoff is rendered to `.claude/task-state/handoff-prompt.md` and the screen shows the Pick-up-here block (exact next command + <=6-line digest + pointer; no word floor). Use when you want the next step in a fresh window. |

## Flow

### Stale-plan check (per BPA plan section 5 D9)

Check `plan.md`'s mtime before invoking any sub-skill. If >30 days old, print a warning but CONTINUE — do not bail:

```text
warning: plan.md was last modified <N> days ago (<date>). Autofix may reshape stale plans significantly. Continuing — review the auto-applied fixes before /build-phase if drift is a concern.
```

### Resume detection

Resolve and validate the handoff bundle before trusting resume state. Capture the absolute
invocation directory before any `cd`, resolve the requested plan against it, and canonicalize the
plan file. Then derive `HANDOFF_RUN_DIR` by walking upward from the plan's parent to the nearest
directory containing a project marker: `.project-root`, `CLAUDE.md`, `AGENTS.md`,
`pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`,
`settings.gradle`, `.plan-expedite-state`, or `.git` (a worktree `.git` file counts). The selected
directory must contain the canonical plan and must be at or below its Git root. The nearest marked
ancestor is authoritative. The captured invocation directory may be reused only when its canonical
path equals that nearest directory; a marked containing repository never outranks a nearer nested
project marker. Fail closed on no marker, an ambiguous result, or a plan outside the selected
directory. Never silently equate a containing Git root with a nested project's run directory.

Resolve every relative handoff `--plan` value against `HANDOFF_RUN_DIR`. This makes a plan at
`documentation/foo-plan.md` resolve correctly from its project root while a project-root
`plan.md` continues to work. `HANDOFF_RUN_DIR` is also the exact directory shown in the final
execution-context line and persisted through task-handoff.

Before consulting state, compute `plan_digest` as lowercase SHA-256 over the canonical plan's exact
bytes. This content digest, not the filesystem timestamp, is the security identity of the reviewed
plan. After the initial explicit-block validation (or legacy inference) below, compute
`handoff_digest` as lowercase SHA-256 over the UTF-8 bytes of these five fields joined by one NUL
byte, in order: schema literal `task-handoff-next-action-v1`, canonical `HANDOFF_RUN_DIR`, preview
or the empty string, goal, actionable command. NUL is forbidden in every field, so this framing is
unambiguous.

Check for `.plan-expedite-state` JSON in `HANDOFF_RUN_DIR`. Version 2 schema:

```json
{
  "schema_version": 2,
  "plan_path": "C:/absolute/project/documentation/foo-plan.md",
  "plan_mtime": 1779167384.42,
  "plan_digest": "sha256:<64-lowercase-hex>",
  "handoff_mode": "in-window",
  "handoff_digest": "sha256:<64-lowercase-hex>",
  "completed": [
    {"skill": "plan-review", "verdict": "READY", "timestamp": "..."},
    {"skill": "plan-wrap", "verdict": "READY", "timestamp": "..."}
  ],
  "halted_at": null
}
```

`handoff_mode` is `"in-window"` (default — `task-handoff --next-task`) or `"new-window"`
(`--new-window` flag — `task-handoff --next-task` then `session-wrap --end`). Recorded at
run start; used by resume logic to invoke the correct final sub-skill(s) on re-entry.

`plan_mtime` is a numeric float — seconds since the Unix epoch, as returned by `os.path.getmtime(plan_path)` or `stat -c %Y`. No timezone, no string parsing. It is diagnostic only. Resume identity requires exact `plan_digest` equality, so timestamp precision can never hide a content edit.

Logic:
- If the file does not exist: initialize version 2 state and execute every stage in the selected
  mode's ordered stage list.
- Reuse `completed[]` only when `schema_version == 2`, canonical `plan_path`, handoff mode,
  exact `plan_digest`, and a non-null valid `handoff_digest` all match. Start at the first
  uncompleted sub-skill. A matching mtime is never accepted in place of matching content.
- A missing/older schema version, missing or mismatched plan/handoff digest, different plan/mode,
  or changed plan content
  is stale state: archive it as `.plan-expedite-state.stale-<timestamp>`, initialize version 2
  state, and rerun the chain. In particular, never reuse an old completed `task-handoff`; it may
  contain the former bare full-plan command.
- **Malformed state file:** invalid JSON, missing version-2 keys (`schema_version`, `plan_path`,
  `plan_mtime`, `plan_digest`, `handoff_mode`, `handoff_digest`, `completed`, `halted_at`), or a wrong shape is
  renamed `.plan-expedite-state.malformed-<timestamp>` for forensics and treated as a fresh run.
  Do not halt.
- Validate `completed` as an exact unique prefix of the mode's stage list: `plan-review`,
  `plan-wrap`, `repo-sync`, `task-handoff` for in-window, with `session-wrap` appended for
  new-window. Every entry has exactly `skill`, `verdict`, and UTC-ISO-8601 `timestamp` keys.
  Normalize successful results before persistence: `READY` for plan-review; `READY` or
  `READY_WITH_GAPS` for plan-wrap; and `SUCCESS` for repo-sync, task-handoff, and session-wrap.
  Any unknown, duplicate, out-of-order, skipped, extra-key, or wrong-verdict entry makes the state
  malformed; archive and restart rather than skipping a stage.
- `halted_at: "initial-handoff"` is a validation pseudo-stage, not a sub-skill. On the next run,
  validate first. An invalid explicit handoff is the only state shape allowed to use
  `handoff_digest: null`; it must also use `completed: []`. If still invalid, rewrite that same
  fail-closed shape. Once valid, require a fresh 64-hex handoff digest and restart the chain; never
  clear the pseudo-stage by trusting the former null identity or try to invoke a skill named
  `initial-handoff`.

After every successful validation or derivation, reread the plan and refresh `plan_mtime`, exact
`plan_digest`, `handoff_digest`, and the canonical plan path before writing state. Update
`completed[]` after each successful sub-skill. For an invalid initial handoff, persist the null,
empty-prefix shape above. On any other halt, set `halted_at` to the failing sub-skill and persist.

### Explicit initial handoff contract

A plan whose first safe build is non-contiguous, requires a preview, or is otherwise narrower
than the first inferred automated span MAY declare one authoritative initial handoff. Its lexical
form is deliberately narrow so every provider parses the same data. Use this exact structure:

````markdown
### Plan-expedite initial handoff
<!-- plan-expedite-initial-handoff-v1 -->
```text
/goal "<non-empty finish condition>"
/build-phase --plan <this-plan> [selectors] --dry-run
/build-phase --plan <this-plan> [the-same-selectors]
```
````

The preview line is optional; the actionable line is required. This is plan data, never a shell
script. Parse without executing, then preserve each accepted command line byte-for-byte.

1. **Structural grammar.** The marker literal occurs zero or one times in the entire plan. When
   present, its enclosing bundle is, in order: the exact heading line; zero or more empty lines;
   the exact marker line; zero or more empty lines; an opening line of three backticks followed by
   `text`; either two or three non-empty command lines; and a closing line of exactly three
   backticks. No other heading, comment,
   prose, indentation, or non-empty line may occur inside that sequence. Two lines mean goal then
   action. Three mean goal, preview, then action. A marker anywhere else is invalid, including in
   an example fence.
2. **Exact lexer.** Tabs, leading/trailing whitespace, CR/LF/NUL inside a field, control
   characters, and repeated spaces between tokens are invalid. The goal grammar is exactly
   `/goal "<condition>"`, where `<condition>` is non-empty after trimming and contains no `"`, CR,
   LF, NUL, or control character. Each build line is `/build-phase` followed by single-space
   separated tokens. A token is either an unquoted non-empty sequence excluding whitespace,
   quotes, control characters, `;`, `&`, `|`, `<`, `>`, `#`, the backtick character, `$(`, and
   `)`, or a double-quoted non-empty value
   with the same exclusions except spaces are allowed. Quotes delimit a value and are not escape
   syntax; backslash is literal, so a quoted Windows path is deterministic.
3. **Argument grammar.** Require exactly one `--plan <value>`. Allow each of `--phase <value>`,
   `--steps <value>`, and `--resume <value>` at most once, plus valueless `--dry-run` on the preview
   only. No other flag, positional token, or `--flag=value` form is accepted. `--steps` is exactly
   `[1-9][0-9]*(,[1-9][0-9]*)*` with no duplicate number; `--resume` is `[1-9][0-9]*`.
   Resolve `--plan` from `HANDOFF_RUN_DIR`, canonicalize it, and require equality with the plan
   passed to plan-expedite.
4. **Effective-set safety.** Apply build-phase's selector order (`--phase`, then `--steps`, then
   `--resume`) and its already-DONE filtering to compute the final effective executable step set;
   do this even when no selector is present. Require a non-empty set, every selected number to
   exist, and every selected step to be numeric `Type: code` or `Type: conditional`. Reject
   operator, Manual-UAT, and wait steps. For every selected step, each declared dependency must
   also be selected or already `Status: DONE`. Thus a marker can never make a bare full-plan
   invocation bypass an operator/wait boundary.
5. **Preview equality.** Parse into ordered flag/value pairs, then compare maps after removing the
   preview's sole `--dry-run`; flag order may differ, but every other decoded value must be equal.
   The actionable command must not contain `--dry-run`. Preserve the original validated strings;
   normalization is for comparison only and never reconstructs output.
6. **Fail-close timing.** Validate before `plan-review`, immediately after `plan-review` before
   invoking `plan-wrap`, immediately after `plan-wrap` before `repo-sync`, and once more after
   `repo-sync` before task-handoff. Plan autofixes and issue-field sync are the only mutations
   allowed between checks; no task-state handoff or emitted build command occurs until the final
   validation succeeds. A missing marker is valid and uses legacy inference. A present-but-invalid,
   unsafe, changed-to-invalid, or ambiguous block is a plan completeness defect: set `halted_at`
   to `initial-handoff`, persist version-2 state, emit the halt template with the exact validation
   error, and halt before the next stage. Every defect found in the first three checks must halt before `repo-sync`;
   a defect first introduced/detected by repo-sync halts before task-handoff.
   Never guess or fall back from an invalid declared block.
7. On success, retain the exact goal, optional preview, actionable command, canonical plan path,
   `HANDOFF_RUN_DIR`, and digest. Selectors remain inside the opaque build command; never append
   them to task-handoff's task label or re-derive them after the final validation.

If no explicit initial handoff is declared, preserve the existing behavior below: derive the goal
and actionable command from the first contiguous automated (`code`/`conditional`) span.

### Sub-skill chain

Call each sub-skill below through the host's skill-invocation adapter, in order. Before the first
invocation, change directory to the already-resolved `HANDOFF_RUN_DIR`; do not derive cwd again
from the plan parent. Between invocations, one brief progress sentence ("plan-review returned
READY; invoking plan-wrap") is enough — do NOT re-emit the chain as prose.

**Path-passing contract:** only `/repo-sync` documents a `--plan` CLI flag in its Arguments table; `/plan-review`, `/plan-wrap`, and `/session-wrap` operate on the plan via conversation context (they read the plan path from the invoking turn's prose or from cwd). Pass the path via the `args` parameter of the `Skill` call so the sub-skill picks it up.

Read the exit code and final verdict line after each `Skill` call returns. On success, append to `completed[]` in `.plan-expedite-state` and proceed to the next sub-skill. On halt, write the halt template (see below) and stop.

1. **Invoke `plan-review` through the host's skill-invocation adapter** with `args: "--autofix <plan-path>"`.
   - Success criteria: verdict READY, or "READY (auto-fixed N items)", or NEEDS WORK with only clarifying questions auto-answerable.
   - Halt criteria: genuine ambiguity surfaced under "Needs your input:" requiring operator judgment, OR sub-skill non-zero exit, OR sub-skill missing.
   - On success, reparse/rederive the handoff, recompute its digest, refresh state, and halt at
     `initial-handoff` if invalid. Do this before invoking plan-wrap.

2. **Invoke `plan-wrap` through the host's skill-invocation adapter** with `args: "--autofix <plan-path>"`.
   - Success criteria: verdict READY, "READY (auto-fixed N items)", "READY WITH GAPS: M gaps" (plan-wrap-only — 0 Blockers, M≥1 Gaps, /repo-sync may proceed), or NEEDS WORK with only clarifying questions auto-answerable.
   - Halt criteria: same as plan-review (genuine ambiguity under "Needs your input:" requiring operator judgment, OR sub-skill non-zero exit, OR sub-skill missing).
   - On success, reparse/rederive the handoff, recompute its digest, refresh state, and halt at
     `initial-handoff` if invalid. Do this before the plan→repo transition or repo-sync.

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
   - On success, perform the final read-only handoff parse/derivation. Recompute its digest and
     refresh state before task-handoff. This retains legacy issue-number inference after repo-sync
     fills Issue fields and fails closed if repo-sync unexpectedly damaged an explicit bundle.

4. **Invoke the final sub-skill, then emit the continue command** — depends on `--new-window`:

   After final validation, create a unique JSON file outside every Git worktree with the host's
   secure temporary-file facility. Write UTF-8 JSON with exactly these keys and no others:

   ```json
   {
     "schema": "task-handoff-next-action-v1",
     "run_directory": "<canonical absolute HANDOFF_RUN_DIR>",
     "preview": "<exact preview command or null>",
     "goal": "<exact goal command>",
     "action": "<exact actionable build command>"
   }
   ```

   Write JSON escaping only; the decoded strings must equal the validated strings byte-for-byte.
   Pass its canonical absolute path as `--next-action-file`. Delete only that exact temporary file
   after task-handoff returns, whether it succeeds or fails. Never stage it, put it in the repo, or
   interpolate the JSON into a shell command line.

   **Default (no `--new-window`):** Invoke task-handoff with
   `args: "--next-task build-phase --next-action-file <absolute-temp-json>"`. It validates the
   payload and durably writes the locked multiline Next Action before any `/clear` is emitted.

   Emit one of these exact shapes, substituting the preserved strings and resolved context. The
   model value is the workspace-pinned build tier; preserve an explicit user model choice (for
   example Terra), and never recommend a seed/fable tier for build-bearing work. The context and
   observation lines are required control metadata, not a summary or preamble.

   With a preview:

   ````markdown
   ```
   /clear
   ```

   Run in: this window after /clear @ <absolute HANDOFF_RUN_DIR> · Model: <resolved build tier>

   ```
   <exact preview>
   ```

   Continue only after the preview exits 0 with `Dry-run complete. No steps executed.`:

   ```
   <exact goal>
   <exact action>
   ```
   ````

   Without a preview (explicit or legacy):

   ````markdown
   ```
   /clear
   ```

   Run in: this window after /clear @ <absolute HANDOFF_RUN_DIR> · Model: <resolved build tier>

   ```
   <exact goal>
   <exact action>
   ```
   ````

   `/clear`, preview, and action are separate observation points. The preview is rendered before
   the atomic goal/action pair even though the source data block lists goal first. This is the only
   permitted reordering; each command string remains byte-for-byte unchanged.
   - **Only when no explicit initial handoff exists, derive the `<condition>` from the plan,
     scoped to the AGENT-COMPLETABLE slice.**
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

   1. **Invoke `task-handoff` through the host's skill-invocation adapter** with
      `args: "--next-task build-phase --next-action-file <absolute-temp-json>"` — the durable
      write validates the same payload used by default mode and stores its locked multiline Next
      Action. Do not create a second representation or pass selectors in the task label.
   2. **Invoke `session-wrap` through the host's skill-invocation adapter** with `args: "--end <plan-path>"` —
      `--end` explicitly, never bare: end-window is the route `--new-window` wants, and a
      bare invocation triages and may route `continue`. session-wrap renders the handoff
      to disk (`.claude/task-state/handoff-prompt.md`, a rendering of the `current.md`
      just written — one source of truth) and prints the Pick-up-here block per its
      screen contract: digest + pointer first, then numbered Step blocks — Step 1
      `/clear`, an optional `/model <pinned-default>` step when the session's model was
      explicitly overridden this session, and the FINAL fenced block carrying the
      `/goal` + `/build-phase` pair verbatim (goal line first), with any preview in its own
      preceding fenced Step labelled with `(run in <HANDOFF_RUN_DIR>)`. No word floor.
      session-wrap's route step 1 checkpoint must preserve step 1's Next Action
      verbatim (its no-regress clause) — the pair survives into the render and into
      the final Step block.
   - Emit session-wrap's Pick-up-here block verbatim as the `/plan-expedite` final
     output. Do not paraphrase, do not summarize, do not add a preamble. VERIFY the
      `/goal` + `/build-phase` pair is the block's final fenced Step — the last lines on
      screen are what the operator runs. Because this route always uses the locked payload, a
      missing/mutated pair, preview, or run directory is a session-wrap integrity failure: halt
      instead of appending, reconstructing, or guessing a replacement.
   - Record `handoff_mode: "new-window"` in `.plan-expedite-state`.

   The `--new-window` flag is the escape hatch for users who want the next step in a
   fresh window instead of continuing in-window: durable state on disk plus a rendered
   handoff file, not a wall of copy-paste text.

### Halt template (per BPA plan section 5 D8 — generic, no per-skill enumeration)

Write the following template verbatim on any sub-skill non-success exit:

```text
/plan-expedite halted at: <sub-skill name | initial-handoff>
Reason: <captured stderr / verdict line>
Plan state: <unchanged | partially autofixed (cite which fixes applied per the autofix-applied markers in plan.md)>
GitHub state: <unchanged | issues created/updated (cite count if repo-sync ran)>
To resume: fix the cited issue, then re-run /plan-expedite --plan <path>
           (already-completed sub-skills are skipped via state inference from .plan-expedite-state)
```

Stop without producing the final continue command / Pick-up-here block after printing. The `.plan-expedite-state` records the sub-skill name or `initial-handoff` pseudo-stage for resume.

Use the same five-line template for initial-handoff validation and every sub-skill failure
(plan-review, plan-wrap, repo-sync, task-handoff, session-wrap); stage-specific diagnostic detail
belongs in the cited reason, not a new template.

## Relationship to other skills

| Skill | Role |
|---|---|
| `/plan-init`, `/plan-feature` | Produce the plan.md `/plan-expedite` operates on |
| `/plan-review`, `/plan-wrap` | Autofix sub-skills (Steps 7-8 of BPA plan) |
| `/repo-sync` | Issue-sync sub-skill (Step 6) |
| `/session-wrap` | End-window handoff sub-skill (`--new-window` only, invoked `--end` AFTER the durable `task-handoff --next-task` write; renders `handoff-prompt.md` + prints the Pick-up-here block) |
| `/build-phase` | Continues in-window from the `/goal` + `/build-phase` commands /plan-expedite emits (the `/goal` arms the Stop hook over the automated span; or, with `--new-window`, the fresh window opens from the rendered handoff carrying both) |

## Limitations

- Resume state lives in a single `.plan-expedite-state` file in the project root. Multiple concurrent `/plan-expedite` invocations on the same plan have undefined behavior — don't do that.
- Concurrent operator edits to `.plan-expedite-state` during a run have undefined behavior. Don't edit the file while `/plan-expedite` is running.
- Sub-skill failures halt the chain; resume requires manual operator inspection. By design — autofix's promise is to handle the boring cases, not the surprising ones.
