# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

# build-phase core

## Intent continuity (drift-ranger)

Follow the intent continuity contract at `<repo>/_shared/intent-continuity.md`.
Before dispatch and after each completed work unit, reconcile the private intent record with the actual user capability. After two units without observable advancement, reassess reuse, integration and scope before extending supporting work; preserve required safety gates. Report what the user can and cannot do, not only step/test counts.


## Purpose and complete operating contract

> **Judging doctrine:** the verifier/gate invariants behind this skill's quality gates and halt contract (mechanical checks gate first, deterministic gate verdicts) live in [`judge-core.md`](../../_shared/judge-core.md) §2/§5 — this skill instantiates the executable-verifier archetype between steps.

Thin orchestrator that reads step definitions from a plan document and runs
`/build-step` for each one in sequence. Does not classify steps or decide flags --
those are declared in the plan. Posts comprehensive progress updates to GitHub
issues so long-running builds are visible in real time.

## When to use

- When you have 2+ build steps to run sequentially from a plan
- When the user says "run all steps", "build phase N", or "run the whole phase"

## When NOT to use

- For a single step: use `/build-step` directly

---

## Operator preference — autonomous + bundled UI + parallel (HEAVY)

This skill's default posture, by strong operator preference:

1. **Autonomous end-to-end.** On parse-success the phase begins immediately — no operator confirmation prompt. The operator opted into autonomous execution by invoking `/build-phase`; if they wanted a preview, they would have used `--dry-run` (see Arguments table). build-phase then runs through dev → review → iterate → checkpoint without checking back in between code steps. Halts are reserved for the structural cases the skill already defines: BLOCKED verdicts, wait steps, broken conditional predicates, quality-gate failures, or test-count regressions. Operator steps never halt the run; their checks are deferred to the phase-end Manual UAT bundle. Do **not** insert "should I continue?" gates beyond those — wall-clock and context-window cost is real, and the operator has opted in to "let it run."

2. **Bundle UI verification with frontend-touching code.** Any step whose `Files` touch `frontend/`, change a `/api/...` endpoint shape consumed by the dashboard, or affect WebSocket payloads should declare `/build-step --ui` (or call out any project-specific UI/dashboard smoke command defined in the project's CLAUDE.md as part of the step's flags) at plan-authoring time. If the plan declares such a step without `--ui`, build-phase surfaces this as a **UI-MISSING** summary note during Step 0 parse — and again in the final phase report — but does **not** prompt and does **not** mutate the step's flags; the phase proceeds with the plan's declared flags. The operator is expected to review the note and rearrange `plan.md` for any future invocation. Code-only verification on UI work is a known gap the operator wants closed, but autonomy beats gating.

3. **Parallel work whenever it exists.** Within each step's execution: when build-phase is dispatching independent reads (gh status, baseline gates, plan parsing), batch them in one tool message. When posting GitHub comments to multiple issues with no ordering dependency, dispatch in parallel. When the plan's steps form an obvious DAG with independent leaves, surface this in the Step 0 parse output (and the final report) as a **PARALLELIZABLE** summary note — but do **not** prompt; the phase runs sequentially per the plan. Default to scanning for parallelism before starting any sequence so the operator has the information for the next invocation.

---

## Halt contract

The 5 conditions under which `/build-phase` is permitted to halt mid-run. Anything else is a defect — surface it as a finding upstream (`/plan-review`, `/plan-wrap`), not a mid-run halt. Long-form rationale + the workspace-wide source-of-truth lives in `dev/.claude/rules/code-quality.md § "Build-phase halt contract"`; this section inlines a 1-sentence summary per item so an operator reading SKILL.md cold doesn't have to navigate out. Reference investigation `02-halt-contract.md`.

1. **Conditional-step predicate errored or returned non-binary.** A `Type: conditional` step's `Condition:` shell expression exited with a code build-phase cannot interpret as run-or-skip (command-not-found ≥126, syntax error, signal-terminated ≥128, or a predicate that outputs but never exits). See "Conditional step handling" below for the dispatch table.
2. **Quality-gate hard fail.** typecheck error count > 0, test count regressed below baseline, lint produced a blocker-class finding — OR (per Step 1's race-condition defense in sections 2d/2e) `origin` advanced with commits overlapping the step's modified file set. All four are integrity-class failures: the worktree's claim that "this step ships these changes against this baseline" no longer holds. The race-condition extension is documented as a sub-case of this halt class, NOT a new (6th) halt class — preserves the 5-item allowlist.
3. **Stop-and-audit triggered.** Third instance of the same bug-shape in this session, per `/build-step`'s stop-and-audit rule. Whack-a-mole is wasting time; STOP iterating, audit the codebase for siblings, and fix the shared structural invariant in one refactor rather than re-patching each named line.
4. **Wait-type step reached.** A step declared `Type: wait` is long-running observation work (a soak test, a benchmark run). The orchestrator halts intentionally so wall-clock waiting doesn't burn context window. Resume in a fresh session via `--resume <next-step>` after the wait completes.
5. **Worktree merge conflict.** A surgical-edit conflict from earlier steps overlapping the current step's files. Requires human resolution before continuing.

**Defect-of-input class** (Step 0 pre-flight Blockers — caught BEFORE any step execution, so technically not "mid-run"):

- Plan has `Type: conditional` step without `**Condition:**` field (caught at Step 0 sub-bullet 6; upstream catches: `/plan-review` §23 + `/plan-wrap` §12).
- Plan has `Type: operator` step with code-shaped `Produces:` but plan-review/plan-wrap autofix didn't run (caught at Step 0 sub-bullet 7's runtime safety net).
- Plan step declares `--reviewers full|runtime` without `--start-cmd`+`--url` (caught at Step 0 sub-bullet 8's Step-flags pre-flight validation, per Step 2 of BP plan).
- Plan file at the `--plan` path missing or unreadable (caught at build-phase Step 0 sub-bullet 1's fail-loud existence check, mirroring build-queue Step 0).

Mid-run halts outside this list are defects to fix upstream — examples that are NOT in the allowlist: mid-run `(y/n)` confirmation prompts, "Should I continue?" gates, and any mid-phase operator-step halt — every `Type: operator` step (pure-observation, or the operator half of an auto-split) is deferred to the phase-end Manual UAT bundle instead. See `dev/.claude/rules/code-quality.md § "Build-phase halt contract"` for the full anti-pattern list and the upstream-defect framing.

## Constraints

See `## Halt contract` above for the 5 halt classes + 4 defect-of-input classes. Autonomous-by-default per workspace `plan-and-issue-flow.md § "Autonomous-by-default skills"` — no mid-run prompts; preview-only behavior via `--dry-run`.

---

## Arguments

| Arg | Required | Default | Description |
|---|---|---|---|
| `--plan` | yes | -- | Path to plan doc (plan.md or documentation/*-plan.md) |
| `--phase` | no | -- | Phase number/name to run (if plan has multiple phases) |
| `--steps` | no | all | Comma-separated step numbers to run (e.g., `2,3,5`) |
| `--resume` | no | -- | Resume from step N (skip already-completed steps) |
| `--dry-run` | no | -- | Print parsed step list and summary notes, then exit without pre-flight or step execution (preview only) |

---

## Plan document format

`build-phase` expects each step in the plan to include:

```markdown
### Step 1: <name>
- **Problem:** <what to build or fix>
- **Type:** code (optional -- defaults to "code")
- **Condition:** <shell-expression> (required for `Type: conditional` steps)
- **Issue:** #<N> (optional -- created by /repo-init or manually)
- **Flags:** --isolation worktree --reviewers code (optional -- defaults to build-step defaults; see Step 0 sub-bullet 8 "Step-flags pre-flight validation" for required-combinations checks — `--reviewers full|runtime` requires `--start-cmd`+`--url` or Step 0 halts as a Blocker)
```

If `Flags` is omitted, `build-step` defaults apply (worktree + auto).
If `Issue` is omitted, no GitHub updates are posted for that step.

**Worked example — conditional step with `Condition:`:**

```markdown
### Step 5: Fix blockers and re-soak
- **Problem:** Address blockers found in Step 4 triage
- **Type:** conditional
- **Condition:** test -s documentation/findings/step-4-blockers.md
- **Issue:** #65
```

The shell-expression in `Condition:` is run from the project root at conditional-step dispatch time. Exit 0 means run; non-zero means skip. Steps with `Type: conditional` lacking a `Condition:` field are pre-flight Blockers (see Step 0 pre-flight detection).

### Step types

The `Type:` field tells build-phase what shape of work the step represents.
**Default is `code`** if omitted, preserving prior behavior. Valid values:

| Type | What it means | What build-phase does |
|---|---|---|
| `code` | Default. A normal coding step — write/modify source files, run tests. | Spawns `/build-step` with the step's flags. Standard reviewer/iteration loop. |
| `operator` | The work is observation, configuration, smoke testing, or other manual investigation that does not produce a code diff. Common for "verify X is wired" or "smoke test Y" steps. | **Does NOT spawn /build-step and does NOT halt.** The step's commands and checks are deferred to the phase-end Manual UAT bundle (see "Deferred-UAT bundling — phase end"); the operator runs them after the phase. A step whose `Produces:` names a code artifact is first auto-split so its code-prep half runs as a code step. |
| `wait` | Long-running observation. The step is mostly idle wall-clock time — a soak test, a benchmark run, a data-collection window. The deliverable is a run log or observation document, not a code diff. | **Halts orchestration entirely.** Prints the step problem and stops. The user runs the wait period manually and the orchestrator does not resume; instead a future build-phase invocation picks up at the next step via `--resume`. Burning context window on a 4-hour wait is wasteful — hand off cleanly. |
| `conditional` | The step only runs if a predicate from a prior step is true. Common shape: "Step 5: fix blockers (only if Step 4 found any)." Requires a `**Condition:** <shell-expression>` field. | **Evaluates the `Condition:` predicate.** Exit code 0 → run the step as a code step; non-zero (≤125) → skip with `Status: SKIPPED (condition false)` and continue; ≥126 or predicate errored → halt as a pre-flight defect. No y/n prompt — the predicate is the decision. |

**Why this exists:** prior to this field, build-phase blindly tried to run every step
through `/build-step`, which wastes time and context on operator/wait steps and produces
nonsense output for conditional steps. Phases that mix code and non-code work (validation
phases, soak-test phases, refactor-then-measure phases) need to declare the shape so the
orchestrator can do the right thing per step.

**Example mixed-type phase:**

```markdown
### Step 1: Document the procedure
- **Problem:** Write documentation/soak-test.md
- **Type:** code
- **Issue:** #61

### Step 2: Verify the daemon mode is wired
- **Problem:** Smoke-test the daemon CLI for 60 seconds, observe state transitions, document findings
- **Type:** operator
- **Issue:** #62

### Step 3: Run the 4-hour soak
- **Problem:** Execute the procedure from Step 1 unattended; capture observations
- **Type:** wait
- **Issue:** #63

### Step 4: Triage findings into a backlog
- **Problem:** Process Step 3 findings into actionable categories
- **Type:** code
- **Issue:** #64

### Step 5: Fix blockers and re-soak
- **Problem:** Only run if Step 4 found blockers
- **Type:** conditional
- **Issue:** #65
```

---

## Steps

build-phase walks 4 outer steps: Step 0 (parse), Step 1 (pre-flight), Step 2 (dispatch each plan step), Step 3 (final verification), Step 4 (report). See `## Flow` below for the full procedure.

## Flow

### Step 0 -- Parse plan

1. Read the plan document at `--plan` path. **Fail-loud existence check first:** resolve the path to absolute; if the file does not exist or is unreadable, halt with the fenced pre-flight Blocker below (defect-of-input class, same shape as the missing-`Condition:` and Step-flags Blockers; mirrors build-queue Step 0's "verify plan files exist" check). Do NOT proceed to Step 1 pre-flight.

   ```
   build-phase: pre-flight Blocker — plan file not found (or unreadable) at <abs-plan-path>.
   This must be fixed before /build-phase can proceed: verify the --plan path (relative
   paths resolve against cwd; a concurrent session may have moved the plan) and re-invoke.
   Nothing was dispatched.
   ```
2. If `--phase` is specified, extract only that phase's steps.
3. If `--steps` is specified, filter to those step numbers.
4. If `--resume` is specified, mark earlier steps as already done.
5. Scan for existing `- **Status:** DONE` lines — treat those steps as already done
   (so `--resume` is not required if previous runs already checkpointed).
6. For each step, extract: name, problem statement, **type** (default `code`),
   issue number, build-step flags, the optional `Done when:` acceptance target, and
   (for `Type: conditional` steps) the `Condition:` shell-expression.
   - **`Done when:` acceptance is optional and non-halting.** Extract the step's `Done when:` value when present. Treat it as ABSENT if the field is missing OR its value exactly matches a deferred sentinel in `<repo>/_shared/step-authoring.md` §3 (`<TBD — operator fills in>` / `<how to verify the step is done>` / `<specific test or verification>`). A present, non-sentinel value is forwarded to `/build-step` as `--acceptance` at Step 2 dispatch (2b); a missing or sentinel value forwards nothing. This widens only what Step 0 reads and what Step 2 forwards — it adds no parse-halt, touches no gate, and leaves the 5-item halt contract and §2f gate text byte-unchanged.
   - **Conditional-step `Condition:` field is required.** If any parsed step has `Type: conditional` but no `**Condition:**` field (or the field is present but whitespace-only), halt Step 0 with the pre-flight Blocker message described under "Conditional step handling" below. Do not transition to step execution. This is a pre-flight defect-of-input — `/plan-review` §23 and `/plan-wrap` §12 should catch it before this point so the halt is rare. The legitimate-halt allowlist is owned by `.claude/rules/code-quality.md` § "Build-phase halt contract"; the text here mirrors it, and the class-2 git-race sub-case is the extension ratified in `.claude/references/advisory-call-convention.md`.
7. **Classify each `Type: operator` step (runtime safety net + deferred-UAT triage).** For each parsed step with `Type: operator`, examine its `Produces:` field. The scan branches:

   - **Code-Produces branch (auto-split).** If any `Produces:` item ends with a code-shaped extension (`.py`, `.ts`, `.tsx`, `.js`, `.sh`, `.rs`, `.go`), is a shipped config (`.json`, `.yaml`, `.toml`) under `src/`, `scripts/`, or any package directory the project's build tooling reads, or is a code-dependent ops doc (`.md` under `documentation/operator/` or similar whose content depends on reading code), flag the step for **auto-split** per "Operator step auto-split — runtime safety net" in Step 2. The split's operator half (`N`) is then flagged `defer-to-uat=true` exactly like a pure-observation step, so it never halts inline.
   - **Pure-observation branch (`defer-to-uat=true`).** If `Produces:` contains NO code-shaped artifact (e.g., "operator verifies dashboard responsiveness", "operator confirms screenshot looks right"), flag the step with `defer-to-uat=true`. During Step 2 dispatch, build-phase SKIPS the step (no started/result issue comment, no inline halt). The step's metadata (name, issue, commands extracted from the `Problem:`, expected-outcome table) is collected into an in-memory deferred-UAT bundle for the phase-end Manual UAT emit per "Deferred-UAT bundling — phase end" below and Step 4's final-report assembly.
   - **Missing `Produces:` field.** Treated as pure-observation (same as the second branch) — no split fires, the step gets `defer-to-uat=true`, and an audit-note line is added to the final report's `Manual UAT to run after build-phase` sub-block as a leading observability line so the inferred classification is visible right next to the deferred bundle the step contributed to (see "Operator step auto-split — runtime safety net" Edge cases for exact wording).

   The code-Produces branch is the runtime safety net complementary to `/plan-review` §22 and `/plan-wrap` §11, which catch the same shape at plan-time (Blocker class). The split only fires here if those upstream checks were skipped or their findings overridden. The pure-observation branch is the runtime counterpart to plan §5 D4's "Bundled UAT handling": observation work the operator must do is collected once at phase end rather than interrupting the autonomous run mid-phase. Cross-ref: `.claude/rules/plan-and-issue-flow.md` § "Operator-type steps must not produce code artifacts".

   This detection runs BEFORE the `--dry-run` exit (sub-bullet 9) so that the dry-run preview includes the Auto-split notes line AND the Deferred-UAT count line with accurate content (a `--dry-run` invocation against a plan containing a code-Produces operator step must show the would-be split in its summary, and a plan containing pure-observation operator steps or auto-split operator halves must show the would-be deferred-UAT count, not "(none detected)" on either line).
8. **Step-flags pre-flight validation.** For each parsed step, validate the `Flags:` line against `/build-step` requirements BEFORE dispatch:

   - **`--reviewers full` requires `--start-cmd` AND `--url`.** If either is missing, surface as a pre-flight **Blocker** (NOT a runtime halt — surface BEFORE Step 1 pre-flight begins) using the same multi-line fenced format as sub-bullet 6's conditional-step Blocker:

     ```
     build-phase: pre-flight Blocker — Step N (#<issue>) declares --reviewers full without --start-cmd and --url.
     This must be fixed in plan.md before /build-phase can proceed: either change to --reviewers code (no UI/runtime needed) OR add --start-cmd <cmd> --url <url>.
     ```

     Do NOT proceed to Step 1 pre-flight or step execution. This is a defect-of-input Blocker (same class as the conditional-step missing-Condition Blocker in sub-bullet 6); the format match means an operator reading the halt template only learns one shape.
   - **`--reviewers runtime` requires `--start-cmd` AND `--url`.** Same check, same Blocker shape (runtime reviewers need a running app to capture evidence against).
   - **Flag inheritance defaults.** If a step's `Flags:` line is omitted entirely, `/build-step` defaults apply: `--isolation worktree --reviewers auto`. Surface this flag inheritance behavior as a one-line note in Step 0 output (after the step list) so the operator can see what each unflagged step will inherit — silent inheritance has bitten plans that assumed `--reviewers code` was the default. Per `/build-step` Arguments table.
   - **UI-AUTH note.** If a step's `--url` value points at an auth-gated route (default heuristic: naive URL-string substring match on `/admin` or `/dashboard`; the heuristic is intentionally narrow per plan §8 Q3 resolution and will false-positive on URLs containing those substrings as non-path segments — projects extend the list via their `CLAUDE.md`, per-project enumeration is a follow-up), emit a **UI-AUTH** summary note (informational, NOT a Blocker) suggesting the operator either (a) provide a `--start-cmd` that sets up an auth bypass OR (b) downgrade to `--reviewers code` if the UI portion is incidental. UI-AUTH is one of the always-print operator-preference checks (see the Step 0 output block below).

   This detection runs BEFORE the `--dry-run` exit (sub-bullet 9) so dry-run output includes any Blocker findings (with halt-style error message and non-zero exit) AND any UI-AUTH notes. The dry-run path is not a "preview anyway" escape from Blockers — a sub-bullet-8 Flag-Blocker halts Step 0 before the dry-run summary is even printed. Cross-reference workspace memory `feedback_plan_reviewer_flags` (the source incident: a `--reviewers full` step missing `--start-cmd` was failing deep in /build-step Step 2, wasting one full step's worth of context that pre-flight validation would have saved). Reference investigation `19-step-flags-inheritance.md`.
9. **If `--dry-run` is set:** after printing the step list, operator-preference summary notes (UI-MISSING, PARALLELIZABLE, Auto-split notes from sub-bullet 7, UI-AUTH notes from sub-bullet 8), and any detected step-type warnings, exit with status 0 and a single line: `Dry-run complete. No steps executed.` Do NOT proceed to Step 1 pre-flight. The dry-run path's only side effects are reads (plan parse, git status if shown); no commits, no dispatches, no GitHub posts.

Print the step list, showing each step's type. **Apply the operator-preference checks** as part of the Step 0 output:

- Scan each step's declared `Files`. If any step touches `frontend/`, alters a `/api/...` route shape consumed by the dashboard, or modifies WebSocket payloads AND its `Flags` line lacks `--ui`, flag it as **UI-MISSING** and emit a UI-MISSING summary note (no prompt).
- Scan step dependencies. If the plan declares no `Depends on` between two adjacent steps and their `Files` don't overlap, flag the pair as **PARALLELIZABLE** and emit a PARALLELIZABLE summary note (no prompt); the phase runs sequentially per the declared plan order.

```text
build-phase: 5 steps parsed from documentation/plan.md (Phase 4.5)
Already-done detection: scanned plan for `Status: DONE` lines -- found 0 (none to skip).

  Step 1: Document soak procedure   [code]         #61  --reviewers code
  Step 2: Verify daemon wiring      [operator]     #62  (deferred to Manual UAT)
  Step 3: Run 4-hour soak           [wait]         #63  (4h wall clock)
  Step 4: Triage findings           [code]         #64  --reviewers code
  Step 5: Fix blockers              [conditional]  #65  (if Step 4 found any)

Mixed-type phase detected. build-phase will:
  - Run code steps via /build-step
  - Defer operator checks to the phase-end Manual UAT bundle (no mid-run prompt;
    a code-Produces operator step first runs its code-prep half)
  - Halt entirely on wait steps (resume with --resume after the wait)
  - Evaluate the `Condition:` predicate on conditional steps (run if exit 0, skip if non-zero)

Operator-preference checks (autonomous + UI-bundle + parallel):
  - UI-MISSING:        (none detected)   [or: "UI-MISSING: Steps N, M touch frontend/ but lack --ui. Continuing without it. Operator should review whether --ui flag is appropriate for the next phase invocation."]
  - PARALLELIZABLE:    (none detected)   [or: "PARALLELIZABLE pairs detected: (N, M). Running sequentially per plan; operator can rearrange in plan.md for future runs."]
  - Auto-split notes:  (none detected)   [or: "Step N (operator+code-Produces) will auto-split into N-prep + N for this run; backport to plan.md for symmetry."]
  - Deferred-UAT count: 0                [or: "2 operator steps (pure-observation or auto-split operator halves) will be deferred to a phase-end Manual UAT bundle."]
  - UI-AUTH notes:     (none detected)   [or: "Step N: --url <url> matches auth-gated heuristic (/admin or /dashboard). Consider --start-cmd with auth bypass OR --reviewers code. Projects extend list via CLAUDE.md."]
  All five checks always print -- '(none detected)' / '0' is the explicit no-op output.
  Non-empty notes are repeated in the final phase report so the
  operator sees them after the run without scrolling Step 0 output.

Provider capability guard: The following applies to Claude/Copilot hosts that support session hooks
and `/goal`. GPT hosts without this capability should use an external loop monitor or skip this
optimization.

Goal-drive (uninterrupted run) — emit ONE line for the operator to paste (build-phase cannot set
/goal itself; it is user-typed). Scope to the AGENT-COMPLETABLE span only: code, conditional and
auto-split steps up to the next wait step, listing only steps that will receive a `Status:` line
(deferred pure-observation operator steps never receive one, and a conditional step may end
SKIPPED; a goal naming a deferred step or spanning a wait step busy-loops). Emit a fresh goal
after each wait boundary:
  To run this phase to completion without pausing, set:
    /goal "<plan-name> steps <listed step numbers> each have a Status: DONE or Status: SKIPPED line in <plan-path>"
  Once set, the native /goal evaluator re-drives the session past any discretionary pause to the
  next step; pause otherwise only for the 5 halt-contract reasons.
```

After printing the step list and any summary notes, transition directly to Step 1 pre-flight with a one-line message like: `Starting Step 1 (#N) — <step name>.`

### Step 1 -- Pre-flight

1. **Detect project context:** language, test/lint/typecheck commands.
2. **Run baseline quality gates:**
   ```bash
   <typecheck_command> && <lint_command> && <test_command>
   ```
3. **Record baseline test count.**
4. **Resolve the commit scope, persist it, and record pre-existing state.** The invocation
   directory is the project root: `PROJECT_ROOT=$(pwd -P)`, the same directory `/build-step`'s
   `scope` resolves as its `PROJECT_ROOT`; it accepts and lands only changes below that
   directory's repository prefix. A plan below `documentation/plans/`,
   `docs/` or any other subdirectory does not move it, so the scope is only as good as the
   invocation directory: a run started in the plan's own directory scopes checkpoints to that
   directory (`PLAN-DIR-SCOPE`), and a run started at the root of a larger repository scopes them
   to the whole repository (`REPO-WIDE-SCOPE`); both are advisories below. `PROJECT_ROOT` and the
   repository root `GIT_ROOT` differ when the project lives inside a larger repository; never
   assume they are equal. Shell variables do not survive between tool calls, so this block writes
   a run-state record below the platform temp directory, outside every repository (like §2b's
   `VERDICT_PATH`). Mint a UUIDv4 `PHASE_RUN_ID` and retain the literal `SCOPE_DIR`,
   `PROJECT_ROOT` and the printed `RUN_UPSTREAM` in parent state. The record holds paths and
   commit ids only, never the verdict key.

   ```bash
   export LC_ALL=C   # one collation for every sort/comm over these records
   SCOPE_DIR="${TMPDIR:-${TEMP:-/tmp}}/skill-mesh/build-phase-scope/<PHASE_RUN_ID>"
   mkdir -p "$SCOPE_DIR"
   PROJECT_ROOT=$(pwd -P)
   GIT_ROOT=$(git -C "$PROJECT_ROOT" rev-parse --show-toplevel)
   PROJECT_PREFIX=$(git -C "$PROJECT_ROOT" rev-parse --show-prefix); PROJECT_PREFIX=${PROJECT_PREFIX%/}
   if [ -z "$PROJECT_PREFIX" ]; then PROJECT_SPEC="."; else PROJECT_SPEC=":(literal)$PROJECT_PREFIX"; fi
   PLAN_PATH="<absolute --plan path from Step 0>"
   PLAN_DIR=$(dirname "$PLAN_PATH")
   PLAN_GIT_ROOT=$(git -C "$PLAN_DIR" rev-parse --show-toplevel 2>/dev/null)
   PLAN_REL=""; PLAN_PREFIX=""   # repository-relative plan path and directory; empty when the plan is in another repository
   if [ "$PLAN_GIT_ROOT" = "$GIT_ROOT" ]; then
     PLAN_PREFIX=$(git -C "$PLAN_DIR" rev-parse --show-prefix); PLAN_PREFIX=${PLAN_PREFIX%/}
     PLAN_REL="${PLAN_PREFIX:+$PLAN_PREFIX/}$(basename "$PLAN_PATH")"
   fi
   # Scope-shape advisory (printed below; never a halt): started in the plan's own documentation
   # directory, or at the repository root for a plan that lives in a project subdirectory
   SCOPE_SHAPE=""
   if [ -n "$PROJECT_PREFIX" ] && [ "$PROJECT_PREFIX" = "$PLAN_PREFIX" ]; then
     case "${PROJECT_PREFIX##*/}" in plans|docs|documentation) SCOPE_SHAPE="PLAN-DIR-SCOPE" ;; esac
   elif [ -z "$PROJECT_PREFIX" ] && [ -n "$PLAN_PREFIX" ]; then
     case "${PLAN_PREFIX%%/*}" in plans|docs|documentation) ;; *) SCOPE_SHAPE="REPO-WIDE-SCOPE" ;; esac
   fi
   git -C "$GIT_ROOT" fetch --quiet origin 2>/dev/null || echo "note: origin absent or unreachable; upstream checks use the last-fetched state, if any"
   UPSTREAM=$(git -C "$GIT_ROOT" rev-parse --abbrev-ref '@{u}' 2>/dev/null)
   if [ -z "$UPSTREAM" ]; then
     UPSTREAM=$(git -C "$GIT_ROOT" symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/||')
     UPSTREAM=${UPSTREAM:-origin/master}  # Fallback if origin/HEAD isn't set (fresh clone without `git remote set-head`)
   fi
   RUN_UPSTREAM=$(git -C "$GIT_ROOT" rev-parse --verify --quiet "$UPSTREAM^{commit}")   # run-level upstream snapshot
   printf '%s=%q\n' PROJECT_ROOT "$PROJECT_ROOT" GIT_ROOT "$GIT_ROOT" PROJECT_SPEC "$PROJECT_SPEC" \
     PLAN_PATH "$PLAN_PATH" PLAN_REL "$PLAN_REL" UPSTREAM "$UPSTREAM" RUN_UPSTREAM "$RUN_UPSTREAM" > "$SCOPE_DIR/scope.env"
   # Pre-existing uncommitted paths under the project: NUL-delimited, repository-relative, unquoted
   { git -C "$GIT_ROOT" diff --no-renames --name-only -z HEAD -- "$PROJECT_SPEC"
     git -C "$GIT_ROOT" ls-files --others --exclude-standard -z -- "$PROJECT_SPEC"; } | sort -z -u > "$SCOPE_DIR/preflight-dirty.z"
   DIRTY_HERE=$(tr -cd '\0' < "$SCOPE_DIR/preflight-dirty.z" | wc -c)
   DIRTY_ALL=$( { git -C "$GIT_ROOT" diff --no-renames --name-only -z HEAD; git -C "$GIT_ROOT" ls-files --others --exclude-standard -z; } | sort -z -u | tr -cd '\0' | wc -c)
   BEHIND=0
   [ -n "$RUN_UPSTREAM" ] && BEHIND=$(git -C "$GIT_ROOT" rev-list --count "HEAD..$RUN_UPSTREAM" -- "$PROJECT_SPEC")
   echo "SCOPE: project=$PROJECT_ROOT repository=$GIT_ROOT plan=${PLAN_REL:-<outside $GIT_ROOT: $PLAN_GIT_ROOT>} upstream=$UPSTREAM@${RUN_UPSTREAM:-none}"
   echo "DIRTY: $DIRTY_HERE under the project, $((DIRTY_ALL - DIRTY_HERE)) elsewhere in the repository; BEHIND: $BEHIND; SCOPE-SHAPE: ${SCOPE_SHAPE:-none}"
   ```

   Print each line below that applies — one advisory line each, no prompt, no halt — and repeat
   it in the final report's `Git-scope notes:`:

   - `WRONG-DIR WARNING: plan repository <PLAN_GIT_ROOT> differs from commit repository <GIT_ROOT>; Status lines are written but not committed — run from the project's root inside <PLAN_GIT_ROOT> (the repository root when the project is its own repository)` when `PLAN_REL` is empty (`.claude/rules/working-directory.md` wrong-directory guard: name both, advisory, never a hard block). When `PLAN_GIT_ROOT` is empty, print `none (the plan is not in a git repository)` in its place and the remedy `move the plan into the project's repository`.
   - `DIRTY-TREE: <n> pre-existing uncommitted path(s) under <PROJECT_ROOT> (<m> elsewhere in <GIT_ROOT>); they stay out of checkpoint commits (the plan file excepted). /build-step stashes the uncommitted changes under its project prefix around each step and ends a step whose change touches one of these paths as a merge conflict (BLOCKED) before writing anything; commit or move them first for a clean run.` when either count is non-zero.
   - `BEHIND-UPSTREAM: <k> commit(s) on <UPSTREAM> touching the project are not in HEAD at run start. The race recheck ignores them (it compares only commits that land after this snapshot); /build-step's own ship-gate re-check uses merge-base semantics and can still halt a step that edits the same files.` when `<k>` is non-zero.
   - `PLAN-DIR-SCOPE: the run was started in the plan's own directory <PROJECT_ROOT>, so /build-step accepts and lands only changes below it (a change elsewhere ends that step as a scope escape, BLOCKED) and checkpoints contain only paths below it. Invoke from the project's root (the repository root <GIT_ROOT> when the project is its own repository).` when `SCOPE_SHAPE` is `PLAN-DIR-SCOPE`.
   - `REPO-WIDE-SCOPE: the plan is in <PLAN_PREFIX> but the run was started at the repository root <GIT_ROOT>, so /build-step accepts changes anywhere in the repository; checkpoint commits still take only the plan and each step's landed paths, and any other change made after this snapshot (for example another session's edit) stays uncommitted and is named UNATTRIBUTED.` when `SCOPE_SHAPE` is `REPO-WIDE-SCOPE`.

   build-phase never runs `git stash` itself, and its own git blocks never change directory: each
   addresses the repository with `git -C "$GIT_ROOT"` (§2b's return to `PROJECT_ROOT` before
   `/build-step` is the only directory change).

   **Scope record rule.** Every later git block — the per-step baseline capture, the §2d/§2e
   recheck, §2e staging and the race-halt comment — starts with
   `SCOPE_DIR='<retained literal>'; . "$SCOPE_DIR/scope.env"`. If the record cannot be loaded
   before a step starts, re-run this item from `PROJECT_ROOT` to recreate it. If it cannot be
   loaded mid-step, print `SCOPE-RECORD-MISSING: <SCOPE_DIR>` in the result comment and the
   report, skip that step's race comparison and say so, and (on `ADVANCE` only; a BLOCKED step
   commits nothing, 2e) stage and commit only the plan file plus the §2c `Files changed` paths
   under `PROJECT_ROOT` that still hold their landed state, as literal pathspecs — never an
   unscoped `git add -A` or a repository-root fallback. When the §2c list is `path list
   unavailable`, commit the plan file only, print `SCOPE-RECORD-MISSING` and `path list
   unavailable` together, and say that the step's landed changes stay uncommitted and count as
   pre-existing once the record is recreated. Recreate the record before the next step.
   Recreating takes a new upstream snapshot and a new pre-existing set, so upstream commits that
   landed during earlier steps and other sessions' edits made so far stop counting; print
   `SCOPE-RECORD-RECREATED: old=<retained RUN_UPSTREAM, or unknown> new=<new RUN_UPSTREAM>` in the
   next result comment and the report. No prompt, no halt. Remove `SCOPE_DIR` after the final or
   paused report (best-effort).
5. **Check the verdict-channel capability before any step executes.** This applies when the
   selection contains a `code` step, or an auto-split `N-prep` half, before its first `wait`
   step — a step that reaches §2b unless an earlier step halts first. Conditional steps are left
   to §2b's backstop, because a false predicate never reaches §2b. Where the provider adapter
   documents a capability check (on Codex, its non-mutating host acceptance probe), run it now;
   a failed or inconclusive result halts `required_tool_missing` here, before Step 2 dispatches
   anything. Where the adapter documents no check (the Claude and GPT adapters), print
   `capability: adapter-asserted, no probe` and continue; §2b's own check remains the backstop.
   This item settles neither the open Claude transcript-key question (build-step D-KEY) nor a GPT
   probe (P-GPT-PROBE). It halts only runs that would also halt at that step's §2b, and adds no
   halt condition; it can pre-empt a class-1 predicate halt from an earlier conditional step.

### Step 2 -- Run each step

For each step in order, **dispatch on the step's type**:

- **`code`** — proceed with the standard 2a-2g flow below.
- **`operator`** (code-Produces, flagged by Step 0 sub-bullet 7): apply "Operator step auto-split — runtime safety net": run `N-prep` through the standard 2a-2g flow, then defer the `N` half to the deferred-UAT bundle exactly like a pure-observation step (no /build-step, no issue comment, no inline halt).
- **`operator`** (pure-observation, `defer-to-uat=true` flag from Step 0 sub-bullet 7): SKIP this step during execution. Do NOT post a started/result comment to the issue. Do NOT halt or wait for an operator response. Collect the step's metadata (name, issue, problem-statement-extracted commands, expected-outcome table) into the in-memory deferred-UAT bundle for Step 4's "Deferred-UAT bundling — phase end" assembly. Continue to the next step without prompting.
- **`wait`** — see "Wait step handling" below. Halts the phase.
- **`conditional`** — see "Conditional step handling" below. Evaluates the `Condition:` shell predicate.

#### Operator step auto-split — runtime safety net

A `Type: operator` step flagged in Step 0 detection (sub-bullet 7) as having a code-shaped `Produces:` artifact is split in-memory before dispatch into TWO adjacent steps:

1. **`N-prep` (`Type: code`)** — authors the code artifact via the standard `/build-step` flow (2a–2g below). The `Problem:` for this prep step is auto-generated from the original step's brief, focused on the code artifact (e.g., "Author the script that step N runs"). All Files from the original step's `Files:` are carried over. The `Issue:` is the same as the original step (a single GitHub issue covers both halves — comments on the issue explain the split). N-prep's 2a "started" comment and 2d result comment carry a `> Auto-split: Part 1 of 2 — code-prep half of Step N; the operator half is deferred to the phase-end Manual UAT bundle.` preamble line so issue archaeology shows both halves clearly; the N half posts no comment of its own.
2. **`N` (`Type: operator`)** — deferred to the phase-end Manual UAT bundle ("Deferred-UAT bundling — phase end"); its M-item content follows "Operator step content" below. The `Problem:` retains the manual portion of the original brief.

The split is **in-memory only** — `plan.md` is NOT modified. The phase's final report (Step 4) includes an `Auto-split notes:` line listing every split that fired with the original step's name, the code artifact path(s) detected, and a backport recommendation so the operator can mirror the structural split into `plan.md` for future runs.

Example: a Step M2 declared `Type: operator` with `Produces: scripts/generate_element_sprites.py + 14 canonical sprites + .gitignore update` is detected (sub-bullet 7) and split in-memory into:

- Step M2-prep (`Type: code`): "Author `scripts/generate_element_sprites.py`. Files: `scripts/generate_element_sprites.py`."
- Step M2 (`Type: operator`): "Run the script and spot-check 14 sprites; update `.gitignore`." Deferred to the Manual UAT bundle.

**Edge cases:**

- **Mixed Produces (some items code-shaped, some not):** N-prep takes only the code artifact(s); the N-half's brief preserves references to non-code items only (PDFs, run logs, spot-checks, config files outside `src/`/`scripts/`, etc.). The auto-generated N-prep `Files:` entry lists only the code artifacts. Example: `Produces: scripts/foo.py + 14 PDF reports` → N-prep authors `scripts/foo.py`; N-half's brief retains the "operator generates 14 PDF reports" portion only.
- **Missing `Produces:` field:** treat the step as pure-observation (no split, no error, no halt). Add an audit-note line to the final report's `Manual UAT to run after build-phase` sub-block, as a leading observability paragraph BEFORE the M<N> item list, with this wording: `Note: Step N (Type: operator) has no Produces: field — treated as pure-observation, no split fired. Review whether the step actually produces code; if so, plan needs a Produces: field for the runtime safety net to detect it.` This stays consistent with sub-bullet 7's "pure-observation operator steps are NOT flagged here" rule while making the inferred classification visible AND co-locating it with the deferred bundle the step contributed to (Auto-split notes is for splits that fired; this case fires no split, so routing the note there is misleading).
- **Path-less filenames (`foo.py` with no directory prefix):** use the bare name verbatim as the auto-generated N-prep `Files:` entry. `/build-step` decides placement based on project conventions (e.g., `foo.py` → `scripts/foo.py` for shell-script-shaped names, or `src/<package>/foo.py` for module-shaped names). build-phase does NOT invent a path during the split.

build-phase auto-splits the code-Produces operator step in-memory, and the split never halts. The N-prep half (`Type: code`) runs autonomously through standard `/build-step` — the operator does NOT see the "halt and ask operator to write the script" scenario, even if `/plan-review` was skipped. The N half (`Type: operator`) joins the phase-end deferred-UAT bundle (BPA Step 4's design, which earlier text here described as pending), completing the autonomy contract for code-Produces operator steps. The allowlist in `.claude/rules/code-quality.md` § "Build-phase halt contract" names no operator-step halt, so neither half adds one.

#### Deferred-UAT bundling — phase end

Three kinds of manual work are deferred to a single bundled Manual UAT at phase end: pure-observation `Type: operator` steps (flagged by Step 0 sub-bullet 7 as having no code-shaped `Produces:` artifact), the operator halves of auto-split steps, and `/build-step` review deferrals (§2c). The autonomy contract: the orchestrator never halts mid-phase for a manual check; instead it accumulates them and surfaces the full list once when the code/conditional/wait-able steps have finished.

**Per-deferred-step in-memory collection (during Step 2 dispatch).** Build-phase extracts and stores:
- Kind: `operator` (pure-observation step or auto-split operator half) or `review deferral` (§2c)
- Source step name (from `### Step N: <name>`)
- Source step's `Issue:` number (if set; otherwise the `Issue:` field is omitted from the emitted entry)
- Commands to run: copy-paste-ready commands extracted from the step's `Problem:` statement, no prose mixed in (same extraction discipline as "Operator step content" Section 1)
- What you're looking for: rows mapping each command/check to its expected outcome (same shape as "Operator step content" Section 2; for a review deferral, one row per deferred item, verbatim)

**Final-report bundle assembly (at Step 4 final report).** Emit a `## Manual UAT` section listing each deferred step as `### M<N>:` (M1, M2, M3, ...). The numbering rule:

- **M-number continuation.** Parse `^### M(\d+):` headings under the `## Manual UAT` H2 section of `plan.md` (case-sensitive — `### M1:` matches, `### m1:` does not). Compute `max(N)` across those headings. The first newly-added item this run uses `max(N) + 1`; subsequent newly-added items increment from there. **Gaps are not filled** — if plan.md already has M1 and M3, a new item is M4, not M2. If no existing entries are found (no `## Manual UAT` section yet, or section present but empty of `### M<N>:` headings), numbering starts at M1.

**Plan.md write-back.** Append the same bundle to `plan.md` under a `## Manual UAT` section. Create the section if missing, with the canonical heading + the `*Generated by /build-phase on YYYY-MM-DD. Append-only; re-running the phase adds new items below, never modifies existing ones.*` italic preamble.

- **Plan.md placement.** The `## Manual UAT` section sits at H2 level (top-level), AFTER all `## Build Steps` / `## <other top-level>` sections and BEFORE any trailing single-line italic footer or horizontal rule. To locate the insertion point, find the last `## ` heading + its content; insert `## Manual UAT` immediately after it. If a trailing footer exists (e.g., `*Plan written YYYY-MM-DD...*` or a closing `---` rule), `## Manual UAT` sits BEFORE the footer so the footer remains the last thing in the doc. If plan.md has no `## Manual UAT` section yet, create one at this location. Within the section, new items go AFTER existing `### M<N>:` items (never before, never interleaved).
- **Idempotency (rename-stable).** BEFORE appending each `### M<N>:` entry, scan plan.md's `## Manual UAT` section for an existing entry whose `Source step Issue:` field (the `- **Issue:** #<N>` sub-field on the existing `### M<K>:` block) matches the current entry's source Issue AND whose kind matches. **The primary key is the pair (Issue, kind)** — step names can drift across phase runs (rename refactors, tightened phrasing), but Issue numbers are stable; the kind is `review deferral` when the entry's `Source step` value ends in `— review deferral` and `operator` otherwise, so an auto-split step's operator half and a review deferral from its code-prep half, which share one Issue, never suppress each other. If a match is found, SKIP that entry (do not overwrite, do not duplicate). If neither side has an `Issue:` (operator step had no issue number; rare), fall back to matching on `M-number + step-name`. New items continue numbering per "M-number continuation" above.

**Canonical block format (mirrored from the BPA plan's §5 D4 — `docs/archived-plans/build-phase-autonomy-plan.md` if cross-reference is needed):**

```markdown
## Manual UAT

*Generated by /build-phase on YYYY-MM-DD. Append-only; re-running the phase adds new items below, never modifies existing ones.*

### M1: <step name from original Type: operator step>
- **Source step:** Step N (from this plan's §6)
- **Issue:** #<step-issue-N>
- **Commands to run:**
  ```powershell
  <copy-paste-ready commands from the source step, preserved verbatim>
  ```
- **What you're looking for:**

  | Check | Expected outcome |
  |---|---|
  | <check 1> | <outcome 1> |
  | <check 2> | <outcome 2> |

### M2: <step name from next deferred step>
...
```

Each H3 item is one deferred step (or one step's review deferrals). For a review deferral, the `Source step` value is `Step N — review deferral`, and `Commands to run` is omitted unless a deferred item names a command. Sub-fields appear in FIXED order: `Source step`, `Issue`, `Commands to run`, `What you're looking for`. If a sub-field has no content (e.g., the step had no `Issue:`), omit that sub-field entirely rather than emitting an empty value.

**Final-report integration.** After the existing Step 4 final-report block (with `UI-MISSING notes:`, `PARALLELIZABLE notes:`, `Auto-split notes:`, `Quality gates:`, etc.), add a "Manual UAT to run after build-phase" sub-block. If the phase had any deferred steps, list each `M<N>:` entry there (name, issue, command count, check count). If none, omit the sub-block entirely.

**Final-line phrasing per workspace memory `feedback_name_manual_verification_handoff`:** when this phase run produces at least one newly-added deferred-UAT item (an `M<N>` not already in plan.md before this run — the (Issue, kind) idempotency check decides this), the phase-end final report's last line MUST name that newly-added item explicitly. Example: if this run adds M5 and M6, the final line reads `Please run M5 next.` If plan.md already contained M1–M4 from prior runs and this run adds no new items (all candidate items match an existing entry and are skipped per idempotency), the final line is the existing `Next: run /repo-update to commit, update docs, and push — run in <abs-target-dir>.` — no Manual UAT cue. The rule is "first NEWLY-ADDED item from this run", not "first item in plan.md"; this matters because the operator likely already ran M1–M4 from prior phase invocations and doesn't need to be re-cued to them.

#### Operator step content (deferred-UAT item format)

No `Type: operator` step halts the run. Every operator step — pure-observation, or the `N` half of an auto-split — is deferred (`defer-to-uat=true` per Step 0 sub-bullet 7): build-phase does not spawn `/build-step` for it, posts no started/result comment for it, does not wait for an operator response, and does not write its `Status:` line (an auto-split step's `Status:` line is written by its `N-prep` half per 2e; a pure-observation step keeps none). Its content is extracted once, in two sections, into the deferred-UAT bundle:

1. **Section 1 — Commands to run:** Extract every verifiable action from the
   step's problem statement and present them as copy-paste-ready commands with
   no prose mixed in. Use the user's preferred shell (PowerShell on Windows).
   Include setup/teardown (e.g., staging a temp file, then resetting it).

2. **Section 2 — What you're looking for:** A markdown table mapping each check
   to its expected outcome. One row per command/check from Section 1.

   Example rows: `| (a) X blocks | Error message mentioning "forbidden", exit code 1 |` and
   `| (b) Y passes | "Passed", exit code 0 |`.

If the step has no runnable commands (pure observation), the M-item omits Section 1 and its
check table restates the problem statement as the observation to make.

The operator runs the bundle after the phase and records outcomes in the plan or issue;
build-phase does not consume those outcomes during this run. Operator steps do NOT consume
/build-step worktrees, do NOT run reviewers, and do NOT iterate.

#### Wait step handling

For steps with `Type: wait`:

1. Post a "wait started" comment to the issue noting that orchestration is
   handing off and the user will resume the phase manually.
2. Print to the user:

   ```text
   ====================================
   build-phase: Step N is WAIT type — HALTING
   ====================================
   <step problem statement>

   ## Phase status so far

     Step 1 (<name>)   #<issue>  PASS  iter K/M  +X tests
     Step 2 (<name>)   #<issue>  DEFERRED (phase-end Manual UAT)
     Step N (<name>)   #<issue>  WAIT -- halting here
     Step N+1, ...     pending

   Quality gates after last code step:
     typecheck: PASS, lint: PASS, test: <count>/<count> (was <baseline>, +<delta>)

   ---

   This step is long-running observation work. The orchestrator is halting
   so you do not burn context window on wall-clock waiting.

   Run the work yourself per the procedure in the step. When done, capture
   the run log / artifacts as the step's deliverable, then resume the phase
   in a fresh session with:

     /build-phase --plan <path> --resume <next-step-N+1>

   This step is NOT marked done by the orchestrator. After you resume,
   build-phase will skip it (because --resume points past it). Mark it done
   manually in the plan when the wait completes.
   ====================================
   ```

3. **Write the deferred-UAT items collected so far** to plan.md per "Deferred-UAT bundling —
   phase end" and list the newly-added `M<N>` items under the banner. The bundle is in memory
   and `--resume` skips the steps that produced it, so stopping without this write loses them.
4. **Stop the orchestrator.** Do not continue to the next step in the same
   session. The whole point of the wait type is to avoid wasting context.

#### Conditional step handling

For steps with `Type: conditional`:

1. **Require `**Condition:**` field.** Conditional steps MUST declare a `**Condition:** <shell-expression>` field in the plan. If a `Type: conditional` step lacks `Condition:`, this is a **pre-flight Blocker**, NOT a runtime halt — `/plan-review` and `/plan-wrap` are responsible for catching this upstream. If the orchestrator detects it during Step 0 parse, halt with the error:

   ```text
   build-phase: pre-flight Blocker — Step N (`Type: conditional`) has no `**Condition:**` field.
   This must be fixed in plan.md before /build-phase can proceed.
   Run `/plan-review` (which has a §23 check for this) or `/plan-wrap` (which has a §12 check) to surface the fix.
   ```

   This is a legitimate halt: a defect-of-input the operator needs to see, not a "should I continue?" gate. (The legitimate-halt allowlist is owned by `.claude/rules/code-quality.md` § "Build-phase halt contract".)

2. **Evaluate the predicate.** When a conditional step is reached during execution, exec the `Condition:` shell expression via `bash -c "<expr>"` from the project root (bash is universally invoked, even on Windows; the workspace's `CLAUDE.md` notes Git Bash is routinely available). Capture exit code only; ignore stdout/stderr unless the predicate errored. If `bash` itself is unavailable, halt as a pre-flight defect (this is a setup problem, not a predicate problem).

3. **Dispatch on exit code:**
   `# Exit 2 with non-empty stderr = syntax error → treat as ≥126 halt, not skip`
   Capture stderr separately so the orchestrator can distinguish a predicate that evaluated false from a predicate that failed to parse.
   - **Exit 0:** the predicate is true — execute the step as a code step using the standard 2a-2g flow (same flags, same dev → review → merge cycle).
   - **Exit non-zero (but ≤ 125), except exit 2 with non-empty stderr:** the predicate evaluated false — mark the step `Status: SKIPPED (condition false)` in plan.md, no checkpoint commit (the skip itself is not a meaningful diff), no quality-gate run, continue to the next step. Post a brief skip comment to the GitHub issue if `Issue:` is set:
     ```
     ## build-phase: Step N skipped (condition false)

     Predicate: `<the Condition: expression>`
     Exit code: <code>
     Step skipped per Type: conditional handling.
     ```
   - **Exit ≥ 126 (command not found / not executable) OR predicate errored (unexpected behavior, e.g., signal, syntax error):** halt the phase with a `pre-flight-defect` style message — the predicate itself is broken (command-not-found, syntax error, or signal-terminated), which is a defect to surface, not a step to skip. Like the missing-Condition Blocker above, this is a legitimate halt: it represents a real defect the operator needs to see, not an autonomy gate. Stop per §2g.

#### Code step handling — standard flow

**Execution order (non-relaxable).** For every code step — including a conditional step whose
predicate passed and an auto-split `N-prep` half — run: record `BASELINE_HEAD` → 2a → 2b → 2c →
on `ADVANCE`: 2f, then 2d, then 2e; on `BLOCKED`: 2d, then 2e → 2g. When §2f fails after an
`ADVANCE`, post the failure to the issue (if any), do not mark `Status: DONE`, do not create the
checkpoint commit, and stop (halt class #2). The section numbers below are reference labels, not
execution order.

**Record the baseline for every code step.** Immediately before 2a — whether or not the step has
an issue — write `BASELINE_HEAD` to the scope record for the 2d/2e recheck (the run-level upstream
snapshot `RUN_UPSTREAM` was taken once, at Step 1 item 4). 2a only reports it.

```bash
SCOPE_DIR='<retained literal>'; . "$SCOPE_DIR/scope.env"   # missing record: Step 1 "Scope record rule"
git -C "$GIT_ROOT" rev-parse HEAD > "$SCOPE_DIR/baseline-head" && cat "$SCOPE_DIR/baseline-head"
```

If the step has an issue number, also record its state now (`gh issue view <N> --json state`,
best-effort) for the report's `Issues closed by build-step:` line.

#### 2a. Post start comment to GitHub issue

If the step has an issue number:

Include the `BASELINE_HEAD` captured at the start of the code step (see "Execution order" above) as `**Baseline HEAD:**` in the comment; do not recapture it here. The baseline HEAD is recorded so the recheck-git-state defense in sections 2d and 2e has deterministic reference points — both subsequent ship gates compare `origin`'s state against the run's Step 1 upstream snapshot (`RUN_UPSTREAM`) to detect parallel-session commits that landed during the run, and report commits made in this working tree since `BASELINE_HEAD`.

Heredoc note: this template uses `<<EOF` (unquoted) so `$BASELINE_HEAD` interpolates at issue-comment time; backticks in the body are escaped (`\``) to render literally. The 2d PASS/BLOCKED templates below use `<<'EOF'` (single-quoted) because they have no shell variables to expand. The 2d HALT template (race-condition path) uses `<<EOF` (unquoted) for the same reason as 2a — it reloads the scope record and interpolates `$UPSTREAM`, `$RUN_UPSTREAM`, `$NEW_COMMITS`, `$OVERLAP`.

```bash
BASELINE_HEAD=$(cat '<retained SCOPE_DIR literal>/baseline-head')
gh issue comment $ISSUE --body "$(cat <<EOF
## build-phase: Step N started

<!-- AUTO-SPLIT GUARD: prepend the next line ONLY if this step came from an auto-split; otherwise omit it entirely. -->
> Auto-split: Part 1 of 2 — code-prep half of Step N; the operator half is deferred to the phase-end Manual UAT bundle.

**Step:** <step_name>
**Phase:** <phase_number>
**Flags:** <build-step flags being used>
**Baseline tests:** <test_count>
**Baseline HEAD:** $BASELINE_HEAD
**Started:** <timestamp>

Running \`/build-step\` now...
EOF
)"
```

#### 2b. Run build-step

Before invoking `/build-step`, generate a UUIDv4 `VERDICT_RUN_ID`, a
cryptographically random parent-local `VERDICT_KEY` encoded as 64 lowercase hex
characters, and a durable `VERDICT_PATH` below the platform temp directory:
`skill-mesh/build-step-verdicts/<VERDICT_RUN_ID>.json`. Retain the key only in
the parent orchestration state; it MUST NOT be a skill argument, tool argument,
environment variable, prompt field, file, log, or report. If the host cannot
retain private parent state while executing build-step, halt
`required_tool_missing`.

**Optional Claude parent-private MCP binding.** In the bounded native Forge lane,
when the host exposes exactly `mcp__forge_verdict__verdict`, use that tool instead
of minting or transmitting `VERDICT_KEY`. Call `open` with only `verdict_path` and
`run_id`; call `write`, `classify`, `cleanup`, `close`, and the optional acceptance
`export` with the helper's closed fields. The key remains inside the MCP process.
Never place a key or signature in a command, prompt, transcript, file, environment
value, or report. `cleanup` destroys the active channel but keeps the same tool
connection available for a fresh `open`; `close` is terminal and is called only
when no later step needs that connection. Outside this explicitly configured lane,
the parent-local-key contract above is unchanged.

Immediately after creating the channel, wrap the entire per-step flow (§2a
through §2g) in unconditional finalization. On every return, exception, BLOCKED
verdict, overlap halt, quality-gate halt, or successful checkpoint, delete
`VERDICT_PATH`. Failure to delete is a warning; the unique run id/key prevent
reuse.

The same finalizer also deletes `<VERDICT_PATH>.uat.md`, build-step's deferred-UAT file, which
this parent owns once the verdict is written and which §2c reads first when it exists. Failure to
delete it is likewise a warning.

Invoke `/build-step` with the step's problem statement, flags, issue number (only
when the step declares `Issue:`; never an empty value), and durable verdict channel. When the step's `Done when:` was extracted in Step 0
sub-bullet 6 as a present, non-sentinel value, forward it as `--acceptance`. Always pass the
step's plan position as `--plan-step "<PLAN_PATH>:<N>"`: the absolute `--plan` path (`PLAN_PATH`,
Step 1 item 4) and the id from the step's `### Step N:` heading (an auto-split `N-prep` half passes
its original `N`). It keys build-step's cumulative round budget across `--resume`, also for a
step without an issue, and on the `deep` lane enables review-deep's plan-conformance lens. `/build-step`
resolves its project as `$(pwd)`, so first return the working directory to the retained literal
`PROJECT_ROOT` (Step 1 item 4).

```text
/build-step --problem "<problem>" [--issue <N>] <flags> [--acceptance "<done-when>"] --plan-step "<PLAN_PATH>:<N>" --verdict-path "<VERDICT_PATH>" --verdict-run-id "<VERDICT_RUN_ID>"
```

The `[--acceptance ...]` is optional. On reviewer lanes (`code`, `deep`, `runtime`, `full`)
build-step's reviewers judge each `Done when` item (build-step's completion condition); on `auto`
it reports `Acceptance: unchecked`, so a declared `Done when` stays unverified there. Either way
build-phase's own classification is unchanged: only the authenticated verdict (§2c) advances a
step, and `--acceptance` adds no build-phase gate or halt.

#### 2c. Capture result

**Keep the orchestrator window slim** (per `dev/.claude/rules/subagent-economy.md`): `/build-step` returns a terse report and writes detail to its `.build-step/` files, which live in its child worktree (`<WORKTREE_PROJECT>/.build-step/`), never in the operator tree; a BLOCKED run keeps that worktree at the report's `Worktree:` path. Capture only the verdict + counts (below); read the `.build-step/*` detail files ONLY when a step BLOCKs and you need findings, starting with `remaining-findings.md` under the kept worktree's project directory. Do not re-`Read` `plan.md`/`current.md` you've already read this run, and do not paste full diffs or sub-agent reports into the window — anything that lands here stays resident for the rest of the phase (the dominant token cost).

**Only capture — read the durable verdict sidecar.** After `/build-step`
completes, read `VERDICT_PATH` and call
`classify_verdict(VERDICT_PATH, expected_run_id=VERDICT_RUN_ID,
expected_secret=VERDICT_KEY)`. The rule is
canonically specified and tested in
`../../_shared/build_step_verdict.py` and is
DEFAULT-DENY / FAIL-CLOSED:

- **ADVANCE** (treat as PASS, proceed to the next step) **only** when `result ∈ {PASS,
  DEFERRED-TO-UAT}` **and** `halt` is `null`.
- **BLOCKED** for everything else — mismatched/missing schema, writer, run id,
  or HMAC signature;
  `result == NEEDS-WORK`; any non-null `halt`
  (`POST_MERGE_HALT` / `SHIP_GATE_HALT`, which surface to the operator and do NOT trigger
  developer iteration), an unknown/missing `result`, an unrecognized halt sentinel, or a file that
  is **missing, unreadable, or malformed JSON** (fail closed — never ADVANCE on ambiguity).

Do not re-implement this branching by hand and do not parse prose as an
authorization fallback. Because build-phase always supplies the channel, a
missing sidecar is BLOCKED. Surface the human report only after classification.
On the optional Claude MCP binding, the tool's structured `classify` response is
the canonical call to this same implementation; require `ok: true`, the expected
monotonic `audit_seq`, and `classification` equal to `ADVANCE` or `BLOCKED`. An
error, missing field, repeated/out-of-order counter, or prose-only result is
BLOCKED. Do not read or reproduce the signed sidecar in the model transcript.

**Deferred review items.** When the classification is `ADVANCE`, read `<VERDICT_PATH>.uat.md`
if it exists — build-step writes it before the verdict for a passing run with deferred items
(review-deep deferrals on the `deep` lane, and completion items no reviewer could confirm) — and
fold its `## Manual UAT` lines verbatim into the deferred-UAT bundle as one `review deferral`
M-item for this step (see "Deferred-UAT bundling — phase end"), one check row per line. Read it
here, before the per-step finalizer (§2b) deletes it. This reads the file only after
authenticated classification; it never authorizes advancement. If the authenticated sidecar's
`result` is `DEFERRED-TO-UAT` (where the host exposes only the classification, as through the
Codex verdict service, the report's `Verdict: PASS (deferred UAT)` line stands in, because a
deferral only ever adds a check) but the file is missing or unreadable, emit the M-item anyway with
one check row naming the step and directing the operator to build-step's run archive
(`<platform temp>/skill-mesh/build-step-archive/<branch>/`, the branch from the report's
`Branch:` line) — a deferral is never dropped silently.

After classifying, capture for the issue comment + checkpoint:
- Verdict (PASS / BLOCKED) — the consumed `ADVANCE`→PASS / `BLOCKED`→BLOCKED result above (an `ADVANCE` whose authenticated `result` is `DEFERRED-TO-UAT` reports as PASS with deferral)
- Iteration count (e.g., "iteration 2/3")
- Files changed — the landed path list: the repository-relative paths in the `landed-paths.json` that the report's `Landed paths:` line names (build-step's run archive; schema `build-step-landed-paths/1`, one entry per landed path with its written Git blob id or `deleted`), read only after authenticated classification by the landed-paths reader in §2d — not the `Files changed: N` count in its final report. Every §2c `Files changed` reference (Step 1's "Scope record rule", the 2d Git-scope notes, 2e) means this list. If the line says `not archived`, or the file is missing, unreadable or fails the reader's checks, write `path list unavailable` in those notes (beside the reader's `LANDED-LIST-UNREADABLE` note) and commit no landed path — never treat it as empty and never widen the commit to the project's change set.
- Test results (count, pass/fail)
- If BLOCKED: remaining findings (and `summary` / `halt` from the sidecar when present)
- If PASS after iteration > 1: what changed between iterations

Retain the durable verdict until the issue comment, §2f gate, and §2e
checkpoint/blocked handling finish. The unconditional per-step finalizer owns
deletion, including every early halt path.

For the bounded Forge lane only, after the accepted checkpoint exists and all
named suites, reviews, and final gates have passed, but before channel cleanup,
call MCP `export` once with the pre-authorized absolute destination and the exact
closed `swarm-forge/parent-acceptance-v1` fields. Require the structured success
shape `{ok, op, attempt_id, submission_id, verdict_run_id, destination,
receipt_sha256, audit_seq}` and exact correlation to this parent/session/attempt;
there is no prose fallback. The export must authenticate the live verdict as
`ADVANCE`. It grants no signing authority to Forge. A failed or inconclusive
export holds the attempt. Then clean up the channel; close the MCP connection only
at the final step of the native attempt.

#### 2d. Post result comment to GitHub issue

If the step has an issue number, post a comprehensive update:

**Recheck git state before posting result comment.** Before posting the result comment (and before the 2e checkpoint commit), recheck `origin` for new commits that landed on the upstream branch since the run's Step 1 snapshot (`RUN_UPSTREAM`). This is the **race-condition defense** against parallel `/build-phase` sessions both reaching ship gates on the same plan/issue. The Toybox K17 incident burned ~50 minutes of context after a parallel session's commit silently invalidated the local worktree's assumptions — see workspace memory `feedback_recheck_git_during_build_phase`.

**This halt is NOT a new halt class.** It extends existing halt class #2 (Quality-gate hard fail) per `dev/.claude/rules/code-quality.md § "Build-phase halt contract"` — git-state divergence from `origin` is a quality-gate failure in the integrity sense: the local worktree's claim that "this step ships these changes against this baseline" no longer holds. Treat the recheck like a typecheck or test-count regression — a measured value, surfaced as a defect.

Heuristic: refresh the remote view, then compare the upstream branch with `RUN_UPSTREAM`.
Divergence that predates the run is excluded (Step 1 item 4 reports it as `BEHIND-UPSTREAM`); a
commit that lands upstream during an earlier step and overlaps a later step's commit set halts
that later step. `/build-step` lands a passing step in the working tree **uncommitted**, so this
step's file set comes from the working tree — never `BASELINE_HEAD..HEAD`, which is empty for
an uncommitted landing and would leave the defense unable to fire. The overlap is computed over
the set 2e will commit, built by the landed-paths reader below (the conservative commit rule,
agent-defaulted): the plan file, plus each path build-step's `landed-paths.json` (§2c) lists
that is under the project, is not one of Step 1's pre-existing paths, and still holds the state
build-step landed (its current `git hash-object` equals the listed blob id, or it is absent for
`deleted`). It never takes a change build-step did not land, so another session's edit, or a
landed path changed since, stays uncommitted and is named in the notes below. The plan is always
in the set because 2e always writes its `Status:` line, and a concurrent commit to the same plan
is the parallel-session race this defense exists for. A BLOCKED step commits nothing (2e); for it
the set only feeds this comparison.
Commits made in this working tree since `BASELINE_HEAD` are reported as evidence, never used as
a trigger. This is the single copy of the recheck commands; 2e re-runs it verbatim.

```bash
SCOPE_DIR='<retained literal>'; . "$SCOPE_DIR/scope.env"   # missing record: Step 1 "Scope record rule"
export LC_ALL=C
git -C "$GIT_ROOT" fetch --quiet origin 2>/dev/null || echo "note: origin absent or unreachable; upstream comparison uses the last-fetched state, if any"
BASELINE_HEAD=$(cat "$SCOPE_DIR/baseline-head")

# Upstream commits since the run's Step 1 snapshot, and the files they changed. SINCE is always
# an upstream commit (RUN_UPSTREAM, or the merge base with HEAD once this run's own checkpoint
# commits reached upstream), which is what keeps this run's commits out of the comparison; three
# dots differ from two only if upstream history was rewritten after the snapshot.
NEW_COMMITS=""; : > "$SCOPE_DIR/new-files.z"
if [ -n "$RUN_UPSTREAM" ]; then
  SINCE=$RUN_UPSTREAM
  MERGE_BASE=$(git -C "$GIT_ROOT" merge-base HEAD "$UPSTREAM" 2>/dev/null)
  [ -n "$MERGE_BASE" ] && git -C "$GIT_ROOT" merge-base --is-ancestor "$RUN_UPSTREAM" "$MERGE_BASE" && SINCE=$MERGE_BASE
  NEW_COMMITS=$(git -C "$GIT_ROOT" log --oneline "$SINCE..$UPSTREAM" 2>/dev/null)
  git -C "$GIT_ROOT" diff --no-renames --name-only -z "$SINCE...$UPSTREAM" 2>/dev/null | sort -z -u > "$SCOPE_DIR/new-files.z"
fi

# Working-tree changes under the project (tracked plus untracked) minus Step 1's pre-existing
# paths: what the reader names UNATTRIBUTED when build-step did not land it
{ git -C "$GIT_ROOT" diff --no-renames --name-only -z HEAD -- "$PROJECT_SPEC"
  git -C "$GIT_ROOT" ls-files --others --exclude-standard -z -- "$PROJECT_SPEC"; } | sort -z -u \
  | comm -z -23 - "$SCOPE_DIR/preflight-dirty.z" > "$SCOPE_DIR/project-changes.z"

# The set 2e will commit, from the landed-paths reader (schema build-step-landed-paths/1).
# LANDED_LIST is the file the report's `Landed paths:` line names; leave it empty when that
# line says `not archived` or is absent. The reader writes commit-set.z (the plan plus each
# listed project path that still holds its landed state, minus pre-existing paths),
# files-changed.txt (the §2c `Files changed` list, or `path list unavailable`) and
# landed-notes.txt (the 2d notes it found). Any failure narrows the set to the plan alone.
LANDED_LIST='<path named by the report Landed paths: line, or empty>'
PROJECT_PREFIX=""; [ "$PROJECT_SPEC" = "." ] || PROJECT_PREFIX=${PROJECT_SPEC#":(literal)"}
if ! python - "$LANDED_LIST" "$GIT_ROOT" "$PROJECT_PREFIX" "$PLAN_REL" "$SCOPE_DIR" <<'PY'
import json, os, re, subprocess, sys
landed_list, git_root, prefix, plan_rel, scope_dir = sys.argv[1:6]
def read_z(name):
    try:
        with open(os.path.join(scope_dir, name), "rb") as fh:
            data = fh.read()
    except OSError:
        return set()
    return {p.decode("utf-8", "surrogateescape") for p in data.split(b"\0") if p}
def in_project(path):
    return not prefix or path == prefix or path.startswith(prefix + "/")
pre_dirty, changes = read_z("preflight-dirty.z"), read_z("project-changes.z")
entries, problem = [], None
try:
    if not landed_list:
        raise ValueError("no landed path list (not archived)")
    with open(landed_list, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not isinstance(doc, dict) or doc.get("schema") != "build-step-landed-paths/1":
        raise ValueError("schema is not build-step-landed-paths/1")
    if not isinstance(doc.get("branch"), str) or not doc["branch"]:
        raise ValueError("branch missing")
    root = doc.get("git_root")
    if not isinstance(root, str) or not os.path.samefile(root, git_root):
        raise ValueError("git_root is not this repository")
    if not isinstance(doc.get("paths"), list):
        raise ValueError("paths is not a list")
    for item in doc["paths"]:
        if not isinstance(item, dict):
            raise ValueError("entry is not an object")
        path, state = item.get("path"), item.get("state")
        if (not isinstance(path, str) or not path or "\\" in path or "\0" in path
                or path.startswith("/") or re.match(r"[A-Za-z]:", path)
                or any(seg in ("", ".", "..") for seg in path.split("/"))):
            raise ValueError("entry path is not repository-relative")
        if not isinstance(state, str) or not (
                state == "deleted" or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", state)):
            raise ValueError("entry state is not a blob id or deleted: " + path)
        if any(path == seen for seen, _ in entries):
            raise ValueError("duplicate entry: " + path)
        entries.append((path, state))
except (OSError, ValueError, TypeError, AttributeError) as exc:
    entries, problem = [], str(exc) or exc.__class__.__name__
listed = {path for path, _ in entries}
ok, changed, outside, touched = [], [], [], []
for path, state in entries:
    if not in_project(path):
        outside.append(path)
        continue
    if path in pre_dirty:
        touched.append(path)
        continue
    if state == "deleted":
        same = not os.path.lexists(os.path.join(git_root, *path.split("/")))
    else:
        run = subprocess.run(["git", "-C", git_root, "hash-object", "--", path],
                             capture_output=True)
        same = run.returncode == 0 and run.stdout.decode("ascii", "replace").strip() == state
    (ok if same else changed).append(path)
commit = set(ok) | ({plan_rel} if plan_rel else set())
unattributed = sorted(changes - pre_dirty - listed - {plan_rel})
notes = []
for label, paths in (("LANDED-CHANGED", changed), ("OUT-OF-SCOPE", outside),
                     ("PRE-DIRTY-TOUCHED", touched), ("UNATTRIBUTED", unattributed)):
    if paths:
        notes.append(label + ": " + ", ".join(sorted(paths)))
if problem:
    notes.insert(0, "LANDED-LIST-UNREADABLE: " + problem)
with open(os.path.join(scope_dir, "commit-set.z"), "wb") as fh:
    fh.write(b"".join(p.encode("utf-8", "surrogateescape") + b"\0" for p in sorted(commit)))
with open(os.path.join(scope_dir, "files-changed.txt"), "w", encoding="utf-8", errors="replace") as fh:
    fh.write("path list unavailable\n" if problem else "".join(p + "\n" for p in sorted(listed)))
with open(os.path.join(scope_dir, "landed-notes.txt"), "w", encoding="utf-8", errors="replace") as fh:
    fh.write("".join(note + "\n" for note in notes))
sys.stdout.buffer.write("".join(note + "\n" for note in notes).encode("utf-8", "replace"))
PY
then
  # The reader itself failed: the plan alone, never a wider set
  : > "$SCOPE_DIR/commit-set.z"; [ -n "$PLAN_REL" ] && printf '%s\0' "$PLAN_REL" > "$SCOPE_DIR/commit-set.z"
  echo 'path list unavailable' > "$SCOPE_DIR/files-changed.txt"
  echo 'LANDED-LIST-UNREADABLE: landed-paths reader failed' | tee "$SCOPE_DIR/landed-notes.txt"
fi
sort -z -u -o "$SCOPE_DIR/commit-set.z" "$SCOPE_DIR/commit-set.z"

# Overlap (the halt trigger) and pre-existing-path overlap (advisory only)
OVERLAP=$(comm -z -12 "$SCOPE_DIR/new-files.z" "$SCOPE_DIR/commit-set.z" | tr '\0' '\n')
PREDIRTY_OVERLAP=$(comm -z -12 "$SCOPE_DIR/new-files.z" "$SCOPE_DIR/preflight-dirty.z" | tr '\0' '\n')

# Commits made in this working tree since the step baseline (evidence only, never a trigger)
LOCAL_COMMITS=$(git -C "$GIT_ROOT" log --oneline "$BASELINE_HEAD..HEAD" -- "$PROJECT_SPEC")

printf '%s\n' "$NEW_COMMITS" > "$SCOPE_DIR/new-commits.txt"
printf '%s\n' "$OVERLAP" > "$SCOPE_DIR/overlap.txt"
printf 'NEW_COMMITS:\n%s\nOVERLAP:\n%s\nPREDIRTY_OVERLAP:\n%s\nLOCAL_COMMITS:\n%s\n' \
  "$NEW_COMMITS" "$OVERLAP" "$PREDIRTY_OVERLAP" "$LOCAL_COMMITS"
```

When `NEW_COMMITS` is empty there is nothing to compare; otherwise use `OVERLAP` below.

**Dispatch on overlap:**

- **OVERLAP non-empty → HALT** (extension of halt class #2). Preserve the worktree state for operator inspection. Post a halt comment to the issue naming the conflicting commits (the `git log --oneline` output above) and the overlapping files; cross-link to `dev/.claude/rules/code-quality.md § "Build-phase halt contract"`. Do NOT proceed to the PASS/BLOCKED ship comment. Do NOT proceed to 2e. Stop per §2g.

  ```bash
  SCOPE_DIR='<retained literal>'; . "$SCOPE_DIR/scope.env"
  NEW_COMMITS=$(cat "$SCOPE_DIR/new-commits.txt"); OVERLAP=$(cat "$SCOPE_DIR/overlap.txt")
  gh issue comment $ISSUE --body "$(cat <<EOF
  ## build-phase: Step N HALTED — race condition detected

  Recheck-git-state defense fired before the ship gate. New commits landed on \`origin\` ($UPSTREAM) since this run's upstream snapshot ($RUN_UPSTREAM) and they touch files this step also modified.

  **Halt class:** #2 (Quality-gate hard fail — git-state integrity) per \`dev/.claude/rules/code-quality.md § "Build-phase halt contract"\`. Not a new halt class.

  **Conflicting commits on origin:**
  \`\`\`
  $NEW_COMMITS
  \`\`\`

  **Overlapping files (this step ∩ new origin commits):**
  \`\`\`
  $OVERLAP
  \`\`\`

  **Worktree preserved.** Resolve the divergence (merge / rebase / re-plan) and re-run with \`/build-phase --plan <path> --resume N\`.

  Source: workspace memory \`feedback_recheck_git_during_build_phase\` (Toybox K17, ~50 minutes context burn).
  EOF
  )"
  ```

- **New commits exist but OVERLAP empty → informational note only, continue.** Emit a one-line note in the result comment ("Note: N new commits landed on `origin` since this run started but touched no files in this step's scope — no halt.") and proceed to the PASS/BLOCKED ship comment below per plan §8 risk-table line 228.

- **No new commits → silent, continue to ship comment.**

**Git-scope notes (advisory only, never a halt trigger).** Add each that applies to the result
comment as one line, and repeat it in the report's `Git-scope notes:`:
`PRE-DIRTY-UPSTREAM: <PREDIRTY_OVERLAP>` (upstream commits also changed pre-existing uncommitted
paths, which this checkpoint does not contain); `LOCAL-COMMITS: <LOCAL_COMMITS>` (commits made in
this working tree during the step — if they swept this step's files, this checkpoint does not
contain those files); `OUT-OF-SCOPE: <paths>` (§2c `Files changed` paths outside `PROJECT_ROOT`,
which 2e does not stage); `PRE-DIRTY-TOUCHED: <paths>` (§2c `Files changed` paths in Step 1's
pre-existing set, which stay uncommitted — see 2e); `UNATTRIBUTED: <paths>` (project changes made
after Step 1 that are neither the plan nor in §2c `Files changed` — for example another session's
edits made during the step; 2e leaves them uncommitted, so this note is how they are seen, and
2e's re-run of the recheck adds any new one to the report); `LANDED-CHANGED: <paths>` (§2c
`Files changed` paths whose current state no longer equals the state build-step landed; 2e leaves
them uncommitted); `LANDED-LIST-UNREADABLE: <reason>` (on `ADVANCE` only: the landed path list
was not archived, was unreadable or failed the reader's checks, so 2e commits the plan alone and
the step's landed changes stay uncommitted); and `SCOPE-RECORD-RECREATED` from Step 1's "Scope
record rule". The landed-paths reader in the recheck block writes `OUT-OF-SCOPE`,
`PRE-DIRTY-TOUCHED`, `UNATTRIBUTED`, `LANDED-CHANGED` and `LANDED-LIST-UNREADABLE` to
`landed-notes.txt`. Here §2c `Files changed` is §2c's landed path list, never a count.

The `**Verdict:** PASS/BLOCKED` line in both issue-comment templates below is **fed directly from
the result consumed in §2c** (`ADVANCE` → `PASS`, `BLOCKED` → `BLOCKED`) — it is not a separately
judged value. When `verdict.json` supplied a non-null `halt` or a `summary`, surface that text in
the BLOCKED comment's findings line so the operator sees the halt class. On PASS, the `**Gates:**`
line reports §2f's measured result; §2f runs before this comment (see "Execution order").

**On PASS:**

```bash
gh issue comment $ISSUE --body "$(cat <<'EOF'
## build-phase: Step N complete

<!-- AUTO-SPLIT GUARD: prepend the next line ONLY if this step came from an auto-split; otherwise omit it entirely. -->
> Auto-split: Part 1 of 2 — code-prep half of Step N; the operator half is deferred to the phase-end Manual UAT bundle.

**Verdict:** PASS (iteration M/K)
**Files changed:** <list>
**Tests:** X/Y passing (+Z new)
**Gates:** typecheck OK, lint OK, test OK
**Reviewers:** <which reviewers ran and their verdicts>

### Changes made
<summary of what the developer agent built>

### Review summary
<key findings addressed, if iteration > 1>

**Duration:** ~Nm
EOF
)"
```

**On PASS after multiple iterations:**

```bash
gh issue comment $ISSUE --body "$(cat <<'EOF'
## build-phase: Step N complete (required M iterations)

<!-- AUTO-SPLIT GUARD: prepend the next line ONLY if this step came from an auto-split; otherwise omit it entirely. -->
> Auto-split: Part 1 of 2 — code-prep half of Step N; the operator half is deferred to the phase-end Manual UAT bundle.

**Verdict:** PASS (iteration M/K)

### Iteration history
- **Iteration 1:** NEEDS WORK
  - Findings: <summary of reviewer feedback>
- **Iteration 2:** PASS
  - Changes from iter 1: <what was fixed to address findings>

**Files changed:** <list>
**Tests:** X/Y passing (+Z new)
**Gates:** typecheck OK, lint OK, test OK

**Duration:** ~Nm
EOF
)"
```

**On BLOCKED:**

```bash
gh issue comment $ISSUE --body "$(cat <<'EOF'
## build-phase: Step N BLOCKED

<!-- AUTO-SPLIT GUARD: prepend the next line ONLY if this step came from an auto-split; otherwise omit it entirely. -->
> Auto-split: Part 1 of 2 — code-prep half of Step N; the operator half is deferred to the phase-end Manual UAT bundle.

**Verdict:** BLOCKED after M/K iterations

### Iteration history
- **Iteration 1:** NEEDS WORK -- <findings summary>
- **Iteration 2:** NEEDS WORK -- <what changed, what still fails>

### Remaining findings
<per-reviewer breakdown>

### Worktree preserved
Path: <worktree_path>
Branch: <branch_name>

**Phase paused.** Steps N+1 through <last> are pending. The plan's `Status: BLOCKED` line is written but not committed.
<!-- RECOVERY GUARD: include the next line ONLY when build-step's Reason: is a run-state outcome listed under "Error recovery"; otherwise omit it entirely. -->
Before resuming, recover build-step's run: <the matching "Error recovery" action>.
Resolve findings and re-run with `/build-phase --plan <path> --resume N`.
EOF
)"
```

#### 2e. Update plan doc and checkpoint commit

**Gate order invariant:** Run quality gates (§2f) BEFORE marking `Status: DONE` and before the checkpoint commit. If gates fail, the step must NOT be marked DONE and the commit must NOT be created. This order is non-relaxable.

After capturing the result (PASS or BLOCKED), update the plan document and commit:

**Recheck git state before the checkpoint commit.** Re-run the same recheck-git-state defense described in section 2d (race-condition defense) immediately before staging the checkpoint. The window between 2d's recheck and 2e's commit is small but non-zero, and a parallel session that committed in that window must still be detected. Run the §2d recheck block verbatim (it is the single copy of these commands) before item 1 marks the plan; the plan is already in its commit set, so item 2 stages exactly the set this recheck compared.

If the recheck finds new commits AND a non-empty `OVERLAP` with this step's commit set, **halt before committing** as an extension of halt class #2 (Quality-gate hard fail) per `dev/.claude/rules/code-quality.md § "Build-phase halt contract"`. Preserve the worktree state for operator inspection — do NOT stage anything, do NOT create the checkpoint commit, and stop per §2g. The same halt comment template from section 2d (naming the conflicting commits via `git log --oneline` and listing overlapping files) is posted to the issue. Non-overlapping new commits proceed silently (informational note already emitted by 2d). See workspace memory `feedback_recheck_git_during_build_phase` (Toybox K17).

> Wrong-directory guard (complements the recheck above): the recheck catches a wrong-BASELINE (a parallel commit that moved the base); this guard catches a wrong-REPO. Before staging and committing, warn if the resolved target repo != the repo this lands in (advisory, never blocks) — per working-directory.md § Wrong-directory guard; reference impl `Test-WrongDirGuard`.

1. **Mark the step in plan.md.** Find the step's `### Step N:` heading and append a
   status line immediately after the existing metadata:

   - On PASS: `- **Status:** DONE (YYYY-MM-DD)`
   - On BLOCKED: `- **Status:** BLOCKED (YYYY-MM-DD)`
   - On PASS of an auto-split `N-prep` half, on the original `### Step N:` heading:
     `- **Status:** DONE (YYYY-MM-DD; operator checks deferred to the phase-end Manual UAT bundle)`
     (M-numbers are assigned at Step 4, so the status line does not name one)

   If a `Status` line already exists for the step, replace it.

2. **Create a checkpoint commit** (on PASS only) with this step's landed changes plus the plan
   doc update — never an unscoped `git add -A`. The commit set is the one the §2d landed-paths
   reader built (conservative commit rule, agent-defaulted): the plan plus each landed path under
   `PROJECT_ROOT` that still holds the state build-step landed, minus Step 1's pre-existing paths.
   Any other change, including another session's edit made during the step and a landed path
   changed since, stays uncommitted and is named in 2d's notes (`UNATTRIBUTED`,
   `LANDED-CHANGED`); an unreadable landed path list commits the plan alone
   (`LANDED-LIST-UNREADABLE`). The list narrows the commit; only the authenticated verdict (§2c)
   authorizes it:

   ```bash
   SCOPE_DIR='<retained literal>'; . "$SCOPE_DIR/scope.env"   # missing record: Step 1 "Scope record rule"
   # Stage and commit exactly the commit set the recheck above compared: the plan plus the
   # landed paths that still hold their landed state, minus Step 1's pre-existing paths. Literal
   # NUL-delimited pathspecs; committing with the same pathspecs leaves anything else already
   # staged out of this commit.
   if [ -s "$SCOPE_DIR/commit-set.z" ]; then
     git --literal-pathspecs -C "$GIT_ROOT" add -A --pathspec-from-file="$SCOPE_DIR/commit-set.z" --pathspec-file-nul
     git --literal-pathspecs -C "$GIT_ROOT" commit --pathspec-from-file="$SCOPE_DIR/commit-set.z" --pathspec-file-nul \
       -m "checkpoint: step N complete — <step_name>"
   fi
   ```

   On BLOCKED, create no checkpoint commit and stage nothing (conservative rule, agent-defaulted:
   no authenticated tree state is read, so nothing a BLOCKED run left in the tree is committed).
   Item 1's `Status: BLOCKED` line stays in the plan uncommitted; say so in the BLOCKED comment
   and the paused report.

   A §2c `Files changed` path that is also in Step 1's pre-existing set is not committed.
   Normally it never reaches 2e: `/build-step` stashes the uncommitted changes under its project
   prefix before each step (build-step core Step 0, item 6) and ends a step whose
   payload overlaps a stashed path as a merge conflict before writing anything (Step 8, item 2),
   which returns BLOCKED. Either way it is named as `PRE-DIRTY-TOUCHED` (see "Git-scope notes" in
   2d).

   These commits are intentionally small and frequent so that `--resume` can
   pick up cleanly and so progress is never lost if context runs out.

#### 2f. Verify quality gates

**Execution order:** This section runs before §2e marks `Status: DONE` or creates the checkpoint commit.

After each `ADVANCE` from §2c — before 2d's result comment, 2e's `Status:` line and the
checkpoint commit:

```bash
<typecheck_command> && <lint_command> && <test_command>
```

> Scope: `<test_command>` here runs the FULL suite — every test root/suite the project
> declares, not the subset the step iterated against. `count >= baseline` over a subset
> cannot see a cross-suite regression; the step report names WHICH suites ran, and if
> the full suite is too slow per-step, the checkpoint states that explicitly instead of
> quoting a subset count as the gate (see workspace memory
> `feedback_subset_gate_hides_cross_suite_regression`).

- If gates pass and test count >= baseline: update baseline, continue.
- If gates fail: post the failure to the issue (if any), leave the step without `Status: DONE`
  and uncommitted, stop (halt class #2), report which gate failed, suggest fix.
- If test count decreased: stop, report which tests were lost.

#### 2g. Stop conditions

- **BLOCKED** from build-step: update plan (uncommitted; no checkpoint commit, 2e), post to issue, stop, wait for user.
- **Quality gates fail after merge**: post to issue, stop, wait for user.
- **Test count decreased**: post to issue, stop, wait for user.

Every stop applies this paragraph — a BLOCKED verdict, any halt class 1-5 (including the class-2
race sub-case) and the Step 1 capability halt: report which steps completed and which are still
pending, and write the deferred-UAT items collected so far to plan.md (per "Deferred-UAT
bundling — phase end") — `--resume` skips the steps that produced them, so they would otherwise
be lost.

### Step 3 -- Final verification

After all steps complete:

```bash
<typecheck_command> && <lint_command> && <test_command>
```

> Scope: FULL suite, same rule as §2f — the final report names which suites ran.

### Step 4 -- Report

```text
========================================
build-phase complete
========================================

Plan: documentation/plan.md (Phase 3)
Steps completed: 5/5

  Step 1 (User search)     #44  PASS  iter 1/3  +4 tests
  Step 2 (Results page)    #45  PASS  iter 1/3  +6 tests
  Step 3 (Pagination)      #46  PASS  iter 2/3  +3 tests
  Step 4 (Filter sidebar)  #47  PASS  iter 1/2  +5 tests
  Step 5 (E2E tests)       #48  PASS  iter 1/3  +8 specs

Quality gates:
  typecheck: PASS (0 errors)
  lint:      PASS (0 violations)
  test:      173/173 passing (was 147 at start, +26 new)

Checkpoint commits: 5 (<first-sha>..<last-sha>)
Issues closed by build-step: #44, #45, #46, #47, #48   [or: "none"; "unknown: #N" when the state could not be read]

UI-MISSING notes:     (none detected)   [or: "Steps N, M touched frontend/ without --ui — review for next invocation"]
PARALLELIZABLE notes: (none detected)   [or: "Pairs (N, M) were independent — consider parallel worktrees for next invocation"]
Auto-split notes:     (none detected)   [or: "Step N (operator+code-Produces) auto-split into N-prep (code) + N (operator); artifact: path/to/file.py — backport to plan.md for future runs"]
Git-scope notes:      (none detected)   [or: one "; "-separated entry per WRONG-DIR WARNING, DIRTY-TREE, BEHIND-UPSTREAM, PLAN-DIR-SCOPE, REPO-WIDE-SCOPE, SCOPE-RECORD-MISSING, SCOPE-RECORD-RECREATED, PRE-DIRTY-UPSTREAM, LOCAL-COMMITS, OUT-OF-SCOPE, PRE-DIRTY-TOUCHED, UNATTRIBUTED, LANDED-CHANGED or LANDED-LIST-UNREADABLE line from Step 1 and 2d, with its step, paths or commits]

Manual UAT to run after build-phase (2 newly-added deferred items this run; M5–M6 — plan.md already contained M1–M4 from prior phase runs):
  Note: Step 7 (Type: operator) has no Produces: field — treated as pure-observation, no split fired. Review whether the step actually produces code; if so, plan needs a Produces: field for the runtime safety net to detect it.   [omit this Note line when every deferred step had an explicit Produces:; include one Note: line per missing-Produces case]
  M5: <step name>   #<issue>   commands: <count>, checks: <count>
  M6: <step name>   #<issue>   commands: <count>, checks: <count>

Full details: see plan.md `## Manual UAT` section (appended by this phase).

Please run M5 next.
========================================
```

`Checkpoint commits:` counts this run's 2e commits. `Issues closed by build-step:` lists each PASS step's issue that was OPEN when its state was recorded before 2a and that `gh issue view <N> --json state` reports CLOSED at report time (best-effort; `unknown: #N` when either read failed, never inferred), so an issue closed before the run is not attributed to build-step. `/build-queue` records these two lines as its `commits` and `issues_closed` state. Only bare `#N` entries are closures: an `unknown: #N` entry is not, so a consumer that records integer closures (`/build-queue`'s `issues_closed`) leaves it out.

The final-line cue names the first NEWLY-ADDED M<N> from this phase run, not literal M1. The example above shows the re-run case where plan.md already had M1–M4 from prior phases and this run added M5–M6, so the cue is `Please run M5 next.` — pick the lowest M-number among items this run actually appended (per the (Issue, kind) idempotency check). For a first-ever run where plan.md had no `## Manual UAT` section, the first newly-added item is M1 and the cue would read `Please run M1 next.`

If no deferred-UAT item was newly added this run (none deferred, OR all candidate items matched an existing entry and were skipped per idempotency), the "Manual UAT to run after build-phase" sub-block is omitted entirely and `Next: run /repo-update to commit, update docs, and push — run in <abs-target-dir>.` remains the final line of the success-path report.

> Next-step commands name their target directory, and the proactive project-switch message fires on a cwd≠project mismatch with no pin, per transition-directory-contract.md.

If any step was blocked:

```text
========================================
build-phase paused
========================================

Plan: documentation/plan.md (Phase 3)
Steps completed: 2/5

  Step 1 (User search)     #44  PASS     iter 1/3  +4 tests
  Step 2 (Results page)    #45  PASS     iter 1/3  +6 tests
  Step 3 (Pagination)      #46  BLOCKED  iter 3/3
  Step 4 (Filter sidebar)  #47  pending
  Step 5 (E2E tests)       #48  pending

Blocked on Step 3: <finding summary>
Worktree: <path>
Uncommitted: Step 3's `Status: BLOCKED` line in the plan (a BLOCKED step gets no checkpoint commit)

Checkpoint commits: 2 (<first-sha>..<last-sha>)
Issues closed by build-step: #44, #45   [or: "none"; "unknown: #N" when the state could not be read]

UI-MISSING notes:     (none detected)   [or: "Steps N, M touched frontend/ without --ui — review for next invocation"]
PARALLELIZABLE notes: (none detected)   [or: "Pairs (N, M) were independent — consider parallel worktrees for next invocation"]
Auto-split notes:     (none detected)   [or: "Step N (operator+code-Produces) auto-split into N-prep (code) + N (operator); artifact: path/to/file.py — backport to plan.md for future runs"]
Git-scope notes:      (none detected)   [or: one "; "-separated entry per WRONG-DIR WARNING, DIRTY-TREE, BEHIND-UPSTREAM, PLAN-DIR-SCOPE, REPO-WIDE-SCOPE, SCOPE-RECORD-MISSING, SCOPE-RECORD-RECREATED, PRE-DIRTY-UPSTREAM, LOCAL-COMMITS, OUT-OF-SCOPE, PRE-DIRTY-TOUCHED, UNATTRIBUTED, LANDED-CHANGED or LANDED-LIST-UNREADABLE line from Step 1 and 2d, with its step, paths or commits]

Manual UAT to run after build-phase (N newly-added deferred items collected before the block — deferred operator steps are not run, so they produced no worktree or commits):
  Note: Step 7 (Type: operator) has no Produces: field — treated as pure-observation, no split fired. Review whether the step actually produces code; if so, plan needs a Produces: field for the runtime safety net to detect it.   [omit this Note line when every deferred step had an explicit Produces:; include one Note: line per missing-Produces case]
  M<first-new>: <step name>   #<issue>   commands: <count>, checks: <count>
  ...

Full details: see plan.md `## Manual UAT` section (appended by this phase).

Resume after fixing: /build-phase --plan <path> --resume 3 — run in <abs-target-dir>
Please run M<first-new> next.
========================================
```

The Manual UAT bundle is NOT held back when the phase pauses — items deferred before the block still emit so the operator can run them in parallel with debugging the blocked step. `M<first-new>` is the lowest newly-added M-number from this run (same rule as success-path: per the (Issue, kind) idempotency check, items that already lived in plan.md from prior runs are skipped and not re-cued).

If no deferred-UAT item had been newly added before the block (none encountered, OR all candidates matched an existing entry and were skipped per idempotency), the "Manual UAT to run after build-phase" sub-block is omitted from the paused-path report and `Resume after fixing: ...` remains the final line.

---

## Error recovery

If a step fails and the user provides a fix:

1. User fixes the issue (in worktree or main project)
2. User runs `/build-phase --plan <path> --resume N`
3. build-phase re-runs step N, then continues with N+1, N+2, etc.
4. Already-completed steps are NOT re-run.

When build-step's `Reason:` is one of its run-state outcomes, recover that run before step 2 with
build-step's packaged mechanics helper (`build_step_tree.py` in the build-step skill's `scripts`
directory; build-step's report prints each remedy as a full helper invocation). These are operator
actions: build-phase never runs them and adds no halt for them.

- `unfinished prior run`: `recover <branch>` for the dead run the report names.
- `concurrent run active`: when the owner is alive in another session, wait for it. When the
  report's remedy names a disrupted run of your own session, run
  `recover <owner-branch> --abandon --by <this-branch>` from that same session once the owner's
  heartbeat is older than 15 minutes.
- `rollback failed` or `recover halted` (leftovers): inspect the listed leftover paths and their
  saved bytes, then `recover <branch>`, adding `--keep-current <paths>` for each leftover whose
  current bytes you keep.
- `restore failed` or `recover halted: stash restore failed`: `recover <branch>` to retry the
  restore, or apply or drop the named stash entry by hand and run
  `recover <branch> --stash-resolved`.
- `iteration budget exhausted`: the round budget is cumulative per step (keyed by `--plan-step`,
  §2b), so a resumed step gets no fresh rounds; raise the step's `--max-iter` in its `Flags:`
  above the consumed count, or revise the step.

---

## Task-state integration

build-phase integrates with `current.md` at 3 points during execution. This enables
crash recovery without `session-wrap` and preserves phase progress across compaction events.

**The existing halt contract is unchanged.** `task-handoff --loop` is called only after
successful step completion — it does not replace or affect the 5 halt conditions.

### Integration point 1 — Phase start (Step 0 parse)

After parsing the step list, before running pre-flight:

1. Resolve `<git-root>/.claude/task-state/current.md` via `git rev-parse --show-toplevel`
2. If the file exists AND its `Task:` field contains the current plan path:
   - Read `current.md`
   - Output: `"Resuming phase from step N per task state."` (where N comes from the WIP
     field — the step in progress at the last checkpoint)
   - Pre-flight runs from that step; steps already marked DONE in the plan doc are skipped
3. If `current.md` is absent or does not match the current plan: proceed normally

### Integration point 2 — After each step completes (Step 2e)

**Use `task-handoff --loop --no-commit`.** Per the current.md write-race fix, task-state is now
gitignored — a routine `--loop` commits nothing, so `--loop` and `--no-commit` are equivalent and
neither can double-commit. 2e's scoped staging commits the CODE + the plan's `Status: DONE` entry;
it does NOT pick up the gitignored `current.md` / `sessions/<id>.md` (nor should it). 2d/2e
race-detection is unaffected — it compares the tracked-code diff, which never includes the
gitignored task-state. `--no-commit` stays the correct call for clarity.

Call `task-handoff --loop --no-commit` immediately AFTER the 2e checkpoint commit, so
`<commit-sha>` is the real checkpoint SHA, with current.md reflecting:

```
## Completed
- [<commit-sha>] Step N <step-name>: PASS (<test-count> tests)

## WIP
**Current:** Step N+1: <next-step-name>
**Approach:** <next step's Problem field verbatim>

## Next Action
/build-phase --plan <plan-path> --resume N+1
```

Writing after the commit loses nothing: the checkpoint commit already carries the plan's
`Status:` line, and the session-file write is durable on disk immediately and gitignored, so it
is never part of a commit.

### Integration point 3 — Phase end (Step 4 report)

After the final report, call `task-handoff --loop` (task-state is gitignored, so this writes
the checkpoint and commits nothing):

```
## Completed
(all steps listed)

## Next Action
/repo-update — commit, update docs, push
```

Status: COMPLETE.

---

## Relationship to other skills

| Skill | Role |
|---|---|
| `/plan-init`, `/plan-feature` | Create the plan doc that build-phase reads |
| `/repo-init` | Create GitHub issues from plan steps (first time) |
| `/repo-sync` | Sync issues when plan evolves (create/update/close to match) |
| `/build-step` | Execute a single step (build-phase calls this) |
| `/repo-update` | Commit, update docs, push (run after build-phase completes) |
| `/build-queue` | Invokes build-phase per queue item; parks on any halt and records the final report's `Checkpoint commits:` / `Issues closed by build-step:` lines |
| `/review-gauntlet` | Code review (called by build-step when `--reviewers code\|full`) |
| `/task-handoff` | Task-state checkpoints (3 integration points — see Task-state integration above) |

---

## Limitations

- Does not create GitHub issues -- expects them to already exist (use `/repo-init` or `/repo-sync`)
- Creates checkpoint commits per step but does not push -- use `/repo-update` to push
- Does not infer step type -- the plan must declare `Type:` for non-code steps (defaults to `code` if omitted)
- Default execution is sequential, but parallelizable pairs are surfaced in Step 0 (operator preference). When the operator opts into parallel worktrees for an independent pair, dispatch the two `/build-step` calls in a single tool message. When in doubt about independence, stay sequential.
- **Provider capability guard:** The following lifecycle guidance applies to Claude/Copilot hosts that support session hooks and `/goal`. GPT hosts without this capability should use an external loop monitor or skip this optimization.
- **Run continuously — do NOT pause for "context budget."** On supported Claude/Copilot hosts, a long phase is safe end-to-end in one window: auto-compaction fires on its own at the threshold, the `PreCompact` hook stamps + backs up `current.md`, each step ends with a checkpoint commit, and the `SessionStart` (matcher `compact`) hook re-injects `current.md`'s Next Action afterward — so a compaction *between* steps loses nothing and the orchestrator resumes from `--resume N`. **Pause ONLY for the 5 halt-contract reasons — NEVER because "context might fill."** Splitting a code-step phase mid-run for budget is the discretionary-pause anti-pattern that stranded a real run after Step 1 (see `feedback_build_phase_continuous_via_goal`). Practical aids:
  - **Guaranteed no-pause via `/goal` (structural, not advisory):** prose can be overridden, so the real anti-pause is the native `/goal` evaluator — a Stop hook that re-drives the session until the condition holds, overriding any discretionary pause. Step 0 emits a scoped `/goal` line for the operator to set once. **Scope it to the agent-completable span only** (code, conditional and auto-split steps up to the next wait step, excluding deferred pure-observation operator steps) per `feedback_goal_mode_only_agent_completable` — a goal of "all steps DONE" on a plan with an operator/wait step busy-loops forever. `/goal` is user-typed (build-phase cannot set it itself); emit it, the operator pastes it once.
  - **Tee log from phase start:** invoke the phase with output capture so the orchestrator's prose survives session compaction. Bash example: `tee phase-<plan>-$(date +%Y%m%d).log`. PowerShell: `Tee-Object -FilePath phase-<plan>-2026-05-23.log`. Without this, the operator can't reconstruct what happened in a prior session beyond what reached GitHub issue comments — and the halt-comment audit trail (per the race-condition defense in sections 2d/2e + halt contract above) only covers ship-gate events, not mid-step reasoning.
  - **The ONLY budget split point is a `Type: wait` step** (halt class #4 — the orchestrator halts there anyway): resume the next session with `--resume <next-step-N+1>`. **Code steps do NOT split for budget — they run continuously.** Mid-step caveat: a compaction during a build-step's uncommitted worktree work can disrupt that one step; `--resume` is idempotent, so worst case re-run it (if build-step then reports `concurrent run active` or `unfinished prior run` for the disrupted run, apply "Error recovery" first).
  - **Resume recovery procedure (inline):** `/build-phase --plan <path> --resume N` skips any step whose `Status: DONE` is already in the plan AND any step before N. To explicitly skip a BLOCKED step on resume, mark it `Status: SKIPPED (manual)` in the plan before resuming. The orchestrator does NOT re-run already-DONE steps even without `--resume` (per Step 0 sub-bullet 5's already-done detection). See also the "Error recovery" section above.
- **Worktree hygiene.** `/build-phase` delegates worktree lifecycle to `/build-step`, but three hazards have each cost the workspace a session — see `dev/.claude/rules/worktree-hygiene.md` for the long-form rationale + recovery procedures:
  - **Windows removal-lock risk** (`worktree-hygiene.md` §2): `git worktree remove` returns `Permission denied` when any shell cwd is inside the worktree OR a Python process holds open `.pyc` handles. Cleanup must `cd <project_root> && git worktree remove <path>` in one compound command; the orchestrator avoids this by never cd'ing into worktrees.
  - **Dep-rebuild requirement** (`worktree-hygiene.md` §1): fresh worktrees do NOT inherit `.venv/` (Windows often binds the wrong Python) or `frontend/node_modules/` (gitignored). `/build-step`'s pre-flight runs `uv sync` and `npm install` when relevant, but a step whose `Files` include Python/Node sources should be expected to incur ~30s of dep-rebuild before the first quality gate fires. See workspace memory `feedback_worktree_venv_rebuild`.
  - **Shared-file overwrite risk** (`worktree-hygiene.md` §6): adjacent code steps touching the same file (routes module, config) overwrite each other on merge if the dev agent rewrote the whole file rather than applying surgical edits. After each step's merge, re-run the project's test gate before launching the next step. See workspace memory `feedback_buildphase_worktree_merge` (Alpha4Gate Phase 2 incident).
