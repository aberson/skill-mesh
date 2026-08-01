# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

# build-step core

## Purpose and complete operating contract

> **Judging doctrine:** the reviewer-gate invariants here (producer never grades itself, weak/local models never gate, a deterministic strong-provider gate consolidates) live in [`judge-core.md`](../../_shared/judge-core.md) §5–§6 — this skill instantiates them for the dev→review→merge loop.

Execute a single build step end-to-end: developer writes code, reviewer(s) gate it,
approved changes merge back to the project.

Three independent knobs control how it runs:

| Knob | Flag | Options | Default |
|---|---|---|---|
| Isolation | `--isolation` | `worktree`, `docker` | `worktree` |
| Review style | `--reviewers` | `auto`, `code`, `deep`, `runtime`, `full` | `auto` |
| UI evidence | `--ui` | flag (present = on) | off |

Any combination is valid. Examples:

```bash
/build-step --problem "Add user search endpoint" --issue 12
/build-step --problem "Fix login form" --isolation docker --reviewers code
/build-step --problem "Fix broken dashboard" --reviewers runtime --ui --start-cmd "npm run dev" --url http://localhost:3000
/build-step --problem "Refactor auth middleware" --reviewers full --ui --start-cmd "uv run python -m myapp" --url http://localhost:8000
```

---

## Arguments

| Arg | Required | Default | Description |
|---|---|---|---|
| `--problem` | yes | -- | What to build or fix |
| `--issue` | no | -- | GitHub issue number |
| `--acceptance` | no | -- | Optional acceptance target (the step's `Done when:`, forwarded by `/build-phase`'s Step 0 extract + Step 2 dispatch). `--acceptance` is forwarded to the developer prompt as advisory context only. It does not feed any verdict gate, reviewer lens, or pass/fail determination. If the deep-review prompt includes it, it is for developer orientation only — the reviewer must not treat it as a gate criterion. |
| `--max-iter` | no | 3 | Max developer-reviewer iterations |
| `--isolation` | no | `worktree` | `worktree` or `docker` |
| `--reviewers` | no | `auto` | `auto`, `code`, `deep`, `runtime`, or `full` |
| `--ui` | no | false | Enable Playwright evidence capture |
| `--start-cmd` | no | -- | Shell command to start the app (required when `--ui` or `--reviewers runtime`) |
| `--url` | no | -- | Base URL for Playwright (required with `--start-cmd`) |
| `--ready-url` | no | -- | URL to poll until 200 before evidence capture |
| `--pages` | no | `["<url>"]` | JSON array of URLs to screenshot |
| `--viewport` | no | `1920x1080` | Browser viewport size |
| `--stop-signal` | no | `process-group` | How to stop the app |
| `--record-video` | no | false | Enable video recording |
| `--record-har` | no | false | Enable HAR network recording |
| `--keep-evidence` | no | false | Preserve evidence directory on PASS |
| `--exercise-cmd` | no | -- | Absolute path to Playwright exercise script |
| `--exercise-timeout` | no | 30 | Max seconds for exercise script |
| `--verdict-path` | build-phase only | host temp path | Durable parent-owned verdict path outside the developer worktree |
| `--verdict-run-id` | build-phase only | generated UUID | Opaque parent-minted identity bound to the durable verdict |

---

## Review styles explained

### `auto` (default)
Automated quality gates only: typecheck, lint, test. Fastest option.
The reviewer is the test suite itself -- no sub-agent reviewers are spawned.

### `code`
Run five parallel code-review agents (the review-gauntlet engine includes all five):
1. **Correctness** -- does the diff match the intent?
2. **Bugs** -- does the diff introduce bugs?
3. **Security** -- does the diff introduce exploitable vulnerabilities or weaken trust boundaries?
4. **Test Quality** -- are tests focused? Any to delete?
5. **Style & Conventions** -- does it match surrounding code?

Run automated gates (typecheck/lint/test) first as a prerequisite.
If automated gates fail, the developer fixes them before code reviewers see the diff.

**Optional local-judge offload for the Style reviewer (switchboard — WIRED BUT INERT,
DISABLED BY DEFAULT).** Only the Style reviewer is cheap enough to consider routing to a
local model (tier-offload task_class `build-step-style`; Switchboard Decision 9). Correctness, Bugs, Security, and Test-Quality are deep-reasoning drift-catchers (`code-quality.md`) and ALWAYS stay on a router-authorized strong cloud reviewer tier. **This slice ships DISABLED** (`build-step-style: false` in the offload config) and
MUST stay disabled until the gate invariant below holds, because build-step's reviewers gate
the merge **directly** at Step 7 — routing Style local without a provider-selected deterministic final judge would make
the weak model the gate (forbidden — judge-core §5.7; Decision 3). The gated branch is present for symmetry:
when (and only when) `build-step-style` is enabled in config, route the Style reviewer through
`python -m switchboard judge --site build-step-style --prompt-file <style-reviewer-prompt-file>`
(prints one JSON object, always exits 0); use a **verdict** as the Style reviewer's ADVISORY
input and on a **defer** fall back to the selected-provider Style reviewer. Because the config default is
`false`, the entrypoint returns a defer immediately with NO network call, so `--reviewers code`
runs all five reviewers on the selected cloud provider **exactly as before** — this skill is fully inert today.
**Precondition to ever flip it to `true`:** Step 7 (Aggregate verdict) must be confirmed as the
provider-selected deterministic final judge that consolidates findings (it already is — see the note there), so the
local Style verdict only advises and never gates (the cascade pattern — judge-core §5.7).

### `deep`
Delegate the review to `/review-deep` (the full-depth engine behind review-gauntlet's lean
profile) **INSTEAD OF** the gauntlet's five arms — review-deep's code lenses, including
Security, superset the gauntlet's, so running both doubles cost for zero independence gain. Use for steps whose blast
surface matches the high-stakes classes per `review-deep` SKILL.md's header (the trigger-list
owner — cite it, never restate it); `/plan-review` §27 routes such steps here at plan time by
rewriting `--reviewers code` → `--reviewers deep` on the step's Flags line.

Code-lens-only: like `code`, requires NO `--start-cmd`/`--url`. Automated gates
(typecheck/lint/test) still run first as a prerequisite, exactly as for `code`.

Model tiers are review-deep's own per-lens defaults — do NOT re-pin arms here (review-deep
owns its lens-to-tier map). Conditional high-tier escalation stays an operator call per
the workspace tier policy — never auto-set it.

### `runtime`
Run three parallel evidence-based reviewers:
1. **UI Reviewer** -- screenshots match expected visual state
2. **Backend Reviewer** -- server logs clean, expected behavior confirmed
3. **Frontend Reviewer** -- no JS errors, network requests succeed

Requires `--start-cmd` and `--url`. Implies `--ui`.

### `full`
Use all 8 reviewers: 5 code + 3 runtime. Maximum scrutiny.

Requires `--start-cmd` and `--url`. Implies `--ui`.

---

## Steps

### Step 0 -- Pre-flight

1. **Validate flags:**
   - If `--reviewers runtime` or `--reviewers full`: require `--start-cmd` and `--url`
   - `--reviewers deep` requires nothing beyond `code`'s prerequisites — code lenses only,
     no `--start-cmd`/`--url` (do NOT halt a deep step for missing runtime fields)
   - If `--ui`: require `--start-cmd` and `--url`
   - If `--isolation docker`: verify Docker is running (`docker info`)

2. **Detect project context** from the working directory:
   - Language/stack (Python, TypeScript, Go, etc.)
   - Test command (`uv run pytest`, `npm run test`, `go test ./...`)
   - Lint command (`uv run ruff check .`, `npm run lint`, `golangci-lint run`)
   - Typecheck command (`uv run mypy src`, `npm run typecheck`, `go vet ./...`)
   - Dependency install command (`uv sync`, `npm install --silent`, etc.)

3. **Playwright check** (if `--ui` or `--reviewers runtime|full`):
   ```bash
   uv run --with playwright python -c "import playwright" 2>/dev/null
   ```
   If unavailable, stop with install instructions.

4. **Stash uncommitted changes:**
   ```bash
   git status --porcelain
   # If changes exist:
   git stash push -m "build-step pre-run state" --include-untracked
   ```

5. **Gitignore** (if `--ui`): add `.ui-review-evidence/` if missing.

6. **Reviewer hazards** — warn before runtime reviewers spawn against an auth-gated `--url`:
   When `--url` sits behind an auth gate (PIN, login form, session-bound token), runtime
   reviewers produce silent false-passes because a fresh Playwright context can't satisfy
   the auth — every screenshot shows the gate, not the feature. Remediations:
   1. Downgrade to `--reviewers code` (skip runtime evidence).
   2. Pair runtime/full with `--exercise-cmd` running a Playwright script that injects
      auth state (e.g. `localStorage.setItem('PIN', '1234')`) before evidence capture.
   3. Supply a non-auth-gated `--url` (debug route, or a logged-in deep link with a
      session token in the URL).
   Source: Toybox K17 — `--reviewers full --url http://127.0.0.1:4000/child` produced 4
   screenshots all showing "Enter parent PIN". UI reviewer passed verifying zero K17
   sub-steps. 50 min wasted before the kiosk PIN gate was identified.

### Step 1 -- Create isolated environment

Before spawning the developer, establish the verdict channel:

1. `--verdict-path` and `--verdict-run-id` are an all-or-none set. When
   supplied by build-phase, require both and reject empty values. The path MUST
   be outside the developer worktree. The parent-local `VERDICT_KEY` is never a
   CLI/skill argument: the same parent orchestration context retains it in
   private state while executing this core. If a host runs build-step in a
   distinct context and cannot carry private parent metadata without recording
   it in the transcript, halt `required_tool_missing`.
2. Standalone `/build-step` does not create a machine verdict sidecar; its prose
   report is for the invoking operator only. All write requirements below apply
   only when the parent supplied the complete channel.
3. For a parent-supplied channel, delete any pre-existing target, then
   atomically initialize it with
   `write_verdict(... terminal="NEEDS WORK", summary="run incomplete")` from
   `../../_shared/build_step_verdict.py`, using the parent key.
   A crash therefore fails closed.
4. Never include the verdict path, run id, or parent-local `VERDICT_KEY` in
   developer/reviewer prompts, environment variables, worktree files,
   container mounts, or durable reports. Child agents do not own or authenticate
   this channel.

#### Worktree (default)

```bash
PROJECT="$(pwd)"
BRANCH="build-step-$(date +%s)"
git worktree add "../worktree_$BRANCH" -b "$BRANCH" HEAD
WORKTREE="../worktree_$BRANCH"
cd "$WORKTREE"

# Worktree dep rebuild -- required because `git worktree add` does NOT carry
# .venv/ (Windows: often binds the wrong Python) or node_modules/ (gitignored).
# Both commands are idempotent -- no-op on cached deps.

# Python: run if pyproject.toml or setup.py exists
if [ -f pyproject.toml ] || [ -f setup.py ]; then
  uv sync
fi

# Frontend: run if a frontend/ directory exists with package.json
if [ -d frontend ] && [ -f frontend/package.json ]; then
  (cd frontend && npm install --silent)
fi

# See [`feedback_worktree_venv_rebuild`](<workspace-memory>/feedback_worktree_venv_rebuild.md)
# -- skipping these has caused multiple Windows-bind-wrong-Python failures
# and silent missing-node-modules errors.
```

#### Docker

Build/start the container per the project's Docker config. Mount workspace.
Run the developer agent inside the container with the host adapter's non-interactive
workspace-write permission mode.
Read results from `workspace/results/`.

### Step 2 -- Developer agent pass

**Context injection:** Before spawning the developer, check if `PROJECT_CONTEXT.md`
exists in the project root. If it does, read it and append its contents to the
developer prompt as import/type reference material.

Spawn a sub-agent (host isolated-agent adapter). The developer arm deliberately carries
**no model pin** — build quality tracks the session tier by design; the router-selected
reviewer-tier array (Step 6) is the diversity layer:

```text
You are the developer agent in a build step. Your job is to write code
that solves the problem statement below.

IMPORTANT RULES:
- Only create NEW files or modify files relevant to the problem statement.
- Do NOT modify unrelated files.
- Read surrounding code first to understand existing patterns and conventions.
- All functions you import must exist -- grep for them before using.
- Write tests for any new behavior.
- When adding a new module/class/function that must be called from existing production code, write an integration test that exercises
  the production entry point (HTTP route, CLI command, WS handler, dispatch site) and asserts the new component is reached end-to-end.
  Unit tests of the new module alone are insufficient -- they cannot detect silent wiring failures.
  Skip this rule for pure utilities with no callers in this step's scope, or for schema-only changes.

WORKING DIRECTORY: <worktree_path or container workspace>

PROBLEM STATEMENT:
<problem_statement>

ACCEPTANCE TARGET (your change should satisfy this; guidance, not a new gate): <acceptance — emit this line ONLY when --acceptance is present and non-sentinel; otherwise omit BOTH this line and the blank line immediately below it, leaving the developer prompt byte-identical to today>

PROJECT CONTEXT (import paths, types, exports -- use these, do not invent new ones):
<PROJECT_CONTEXT.md contents, or omit this section if the file does not exist>

After writing code, run these quality gates and fix any failures:
  <typecheck_command>
  <lint_command>
  <test_command>

Formatters MUST run in check mode (`ruff format --check`, `prettier --check`,
`gofmt -l`, `black --check`, `rustfmt --check`) -- never write mode, which
sweeps pre-existing format debt into the diff. If `--check` flags files you
touched, fix manually inside your diff scope; if it flags files you did NOT
touch, report "pre-existing format debt in <files>" -- do not auto-fix.

RETURN (keep it terse -- see dev/.claude/rules/subagent-economy.md): your final
message is the tool result and stays resident in the orchestrator's window for the
rest of the phase, so do NOT paste the diff or a long narrative. Write any detailed
write-up (full change rationale, per-file notes, raw gate output) to
`<worktree>/.build-step/dev-report.md` and return ONLY: (1) a one-line verdict
(DONE / BLOCKED + why), (2) the `git diff --stat` line(s), (3) the one-line test
result (e.g. `42 passed`), (4) any pre-existing-format-debt note, (5) the
`dev-report.md` path. The orchestrator reads `dev-report.md` only if it needs detail
(e.g. on iteration).
```

**Orchestrator-side `--check` follow-up.** On reported pre-existing format
debt outside the step's diff scope, do NOT auto-fix or expand the diff. On
violations in touched files, apply write-mode formatter post-review;
scope to touched files only -- never write-mode across the whole repo.

On retry (after rejection), append:

```text
PREVIOUS REVIEW FINDINGS (you must address all of these):
<findings_from_all_reviewers>
```

### Step 3 -- Capture diff

```bash
cd "$WORKTREE" && git diff HEAD
```

For Docker: extract results from `workspace/results/`.

### Step 4 -- Run automated gates

Always run, regardless of review style:

```bash
cd "$WORKTREE"  # or container
<typecheck_command> 2>&1 | tail -20
<lint_command> 2>&1 | tail -10
<test_command> 2>&1 | tail -15
```

If any fail and `--reviewers auto`: this IS the rejection. Pass errors back to
developer, go to Step 2. No reviewer agents needed.

If any fail and `--reviewers code|deep|runtime|full`: developer must fix before
reviewers see the diff. Pass errors back to developer, go to Step 2.

### Step 5 -- App lifecycle (when `--ui` or `--reviewers runtime|full`)

Skip entirely when no UI evidence is needed.

1. **Copy changes** from worktree to main project (app startup expects project root):
   ```bash
   cd "$WORKTREE"
   CHANGED=$(git diff HEAD --name-only)
   for f in $CHANGED; do
     mkdir -p "$(dirname "$PROJECT/$f")"
     cp "$WORKTREE/$f" "$PROJECT/$f"
   done
   echo "$CHANGED" > .ui-review-evidence/copied-files.txt
   ```

2. **Migration pre-flight** (auto-detect framework entrypoint; non-gating):
   ```bash
   cd "$PROJECT"
   # Framework-native commands only; no custom Python entrypoints.
   # Long-tail projects invoke their migration from --start-cmd.
   if [ -f alembic.ini ]; then
     uv run alembic upgrade head || true
     if [ -z "$(find . -maxdepth 3 -name '*.db' -print -quit 2>/dev/null)" ]; then
       echo "WARN: no *.db file found after alembic upgrade (SQLite path may be misconfigured)"
     fi
   elif [ -f prisma/schema.prisma ]; then
     npx prisma migrate deploy || true
   elif [ -f drizzle.config.ts ]; then
     npx drizzle-kit push || true
   fi
   ```
   If migration fails, the failure cascades into sub-step 4's readiness probe
   and surfaces in backend.log (e.g. `sqlite3.OperationalError: unable to open
   database file`, per Toybox Phase A Step 9 iter 1). The Backend Reviewer
   (Step 6) flags it as a finding through the normal reviewer pipeline.

3. **Start app:**
   ```bash
   cd "$PROJECT"
   mkdir -p .ui-review-evidence/run-$ITERATION
   bash -c '<start-cmd>' > .ui-review-evidence/run-$ITERATION/backend.log 2>&1 &
   APP_PID=$!
   ```

4. **Wait for readiness:** poll `--ready-url` (60s), then `--url` (30s).
   On timeout: kill app, print backend.log, skip runtime reviewers but still run
   code reviewers if applicable.

5. **Collect evidence** via `capture_evidence.py`:
   ```bash
   SKILL_DIR="<path to skills/build-step/core.md>"
   uv run --with playwright python "$SKILL_DIR/scripts/capture_evidence.py" \
     --url "$URL" --pages "$PAGES" \
     --output-dir ".ui-review-evidence/run-$ITERATION" \
     --viewport "$VIEWPORT" --exercise-timeout "$EXERCISE_TIMEOUT" \
     $( [ -n "$EXERCISE_CMD" ] && echo "--exercise $EXERCISE_CMD" ) \
     $( [ "$RECORD_VIDEO" = true ] && echo "--record-video" ) \
     $( [ "$RECORD_HAR" = true ] && echo "--record-har" )
   ```

6. **Stop app:**
   ```bash
   taskkill /T /F /PID $APP_PID 2>/dev/null || kill $APP_PID 2>/dev/null || true
   ```
   On Windows: `taskkill /T` often misses uvicorn/vite children (the bash →
   PowerShell → child chain doesn't propagate signals reliably; PID tracks the
   wrapper, not the bound children — per `dev/.claude/rules/worktree-hygiene.md`).
   Follow up with a port-targeted kill driven by `$URL` and `$READY_URL`, then
   verify both are free. Pure bash + `netstat -ano` + `taskkill /F /PID` — same
   shell as the surrounding block, no PowerShell dispatch needed:
   ```bash
   for u in "$URL" "$READY_URL"; do
     [ -z "$u" ] && continue
     PORT="${u##*:}"; PORT="${PORT%%/*}"
     case "$PORT" in ''|*[!0-9]*) continue ;; esac
     for PID in $(netstat -ano 2>/dev/null | grep ":$PORT .*LISTENING" | awk '{print $NF}' | sort -u); do
       taskkill /F /PID "$PID" 2>/dev/null || true
     done
     curl --max-time 2 -sf "$u" >/dev/null && echo "WARN: $u still bound after cleanup" || true
   done
   ```

### Step 5.5 -- Ship-gate re-check (canonical)

Long runs can race: a parallel session may ship the same feature mid-flight, leaving
this run to discard ~50 min of work at merge time (Toybox K17 incident). Run this
block at each ship gate (Step 6 reviewer spawn, Step 8 merge, Step 8 issue close).
Related: `dev/.claude/rules/worktree-hygiene.md § 7` (merge default before validating).

```bash
# Ship-gate re-check (uses git merge-base for baseline -- no cross-block state needed)
git fetch origin --quiet
DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
DEFAULT="${DEFAULT:-master}"
NEW=$(git log --oneline "HEAD..origin/$DEFAULT" 2>/dev/null)
if [ -n "$NEW" ]; then
  BASE=$(git merge-base "origin/$DEFAULT" HEAD 2>/dev/null)
  OVERLAP=$(comm -12 <(git diff --name-only "HEAD..origin/$DEFAULT" | sort -u) <(git diff --name-only "$BASE..HEAD" | sort -u))
  if [ -n "$OVERLAP" ]; then
    echo "SHIP_GATE_HALT: origin/$DEFAULT advanced with overlapping files since merge-base $BASE. New commits:"
    echo "$NEW"
    echo "Overlap:"; echo "$OVERLAP"
    echo "Resolve the divergence (merge / rebase / re-plan) before proceeding. Do NOT auto-merge — let the operator decide."
    exit 2
  fi
  echo "Note: origin/$DEFAULT advanced ($NEW) but no file overlap — proceeding."
fi
```

**Exit-code contract.** A non-zero exit from this block (literal stdout prefix `SHIP_GATE_HALT:`) is a /build-step halt — surface verbatim to the operator and abort the step.
Do NOT pass to the developer agent as a fix-this finding; no developer fix can resolve an upstream race. This is distinct from Step 4's quality-gate non-zero exits (which DO trigger developer iteration).

### Step 6 -- Spawn reviewer agents

**Ship-gate re-check** (run the canonical block from Step 5.5): avoid spawning 10+ min of reviewer work on a diff a parallel session already shipped.

**Spawn ALL reviewers for the mode in ONE tool message** — a single assistant turn carrying N parallel host isolated-agent calls, never one-at-a-time. The reviewers are independent, so serial spawning only adds wall-clock (≈60–85% slower) for zero independence gain — independence comes from context isolation, not serial order (see `dev/.claude/rules/subagent-economy.md`).

**Reviewer returns are terse + file-backed** (per `dev/.claude/rules/subagent-economy.md`): instruct each reviewer to return ONLY `{verdict, finding-count, the single highest-severity finding}` and to write its full findings list to `<worktree>/.build-step/review-<lens>.{json,md}`. Step 7 reads those files to aggregate; the orchestrator window must not hold N full findings dumps resident for the rest of the run. (Workflow `schema:` reviewers already return bounded rows — keep them `{severity, title, file:line, fix}`, never re-quoted file bodies.)

Based on `--reviewers`:

#### `auto` -- no agents
Verdict comes from Step 4 automated gates. If all pass: APPROVED. Skip to Step 7.

#### `code` -- 5 parallel agents
Each receives: problem statement, full diff, content of touched files.
Dispatch all five with the router-selected reviewer-tier peer — reviewer *diversity* carries the
quality here; arms must never inherit an escalated session (tier policy, CLAUDE.md
model paragraph).

1. **Correctness Reviewer** -- logic vs intent, missing edge cases, inverted conditions,
   silent behavior breaks.
2. **Bug Reviewer** -- null access, resource leaks, race conditions, type mismatches,
   broken error propagation. Severity: high/medium/low.
3. **Security Reviewer** -- exploitable vulnerabilities, trust-boundary violations,
   injection, authorization bypass, unsafe secret handling. Severity: high/medium/low.
4. **Test Quality Reviewer** -- goal is to TRIM. Flags: implementation-detail tests,
   duplicates, tautological assertions, over-mocked tests, missing critical coverage.
5. **Style & Conventions Reviewer** -- only flags deviations from ACTUAL surrounding
   code conventions, not generic best practices.

#### `deep` -- delegate to /review-deep (no gauntlet arms)
Do NOT spawn the five gauntlet reviewers — review-deep's code lenses, including Security,
superset them (running both doubles cost for zero independence gain). Invoke `/review-deep`
once (host skill-invocation adapter) with:

- `--prompt` = the problem statement (plus the acceptance target when `--acceptance` is
  present, as developer-orientation context only; no reviewer lens or verdict gate may
  treat it as a criterion)
- `--diff` = the worktree diff captured at Step 3
- `--plan-step <plan-path>:<step-id>` when the orchestrator knows the plan file + step id
  (enables the plan-conformance lens; omit otherwise — the lens SKIPs cleanly)
- `--output-dir <worktree>/.review-deep/`
- on iteration ≥ 2, `--prior-sidecar <previous iteration's sidecar path>` (enables
  review-deep's persistent-disagreement aggregator rule)

review-deep runs its code lenses with its own per-lens model tiers (no `the router-selected reviewer-tier peer` re-pin
here), applies its deterministic aggregator, and returns a pre-aggregated verdict
(`PASS | NEEDS-WORK | DEFERRED-TO-UAT`) plus a JSON audit-trail sidecar at
`<worktree>/.review-deep/<timestamp>.json`. The sidecar replaces the per-lens
`review-<lens>.{json,md}` files the gauntlet arms would have written — Steps 7 and 9 read
findings from the sidecar's `lens_verdicts[].findings[]` instead.

#### `runtime` -- 3 parallel agents
Each receives: diff plus their evidence slice. Dispatch all three with explicit
`the router-selected reviewer-tier peer` (same arm pin as the `code` reviewers).

1. **UI Reviewer (blind-first)** -- screenshots (before/after exercise). Two-phase
   review in a single pass:
   - **Phase A (blind):** Describe exactly what is visible in each screenshot. Layout,
     text content, colors, element states, error messages, empty areas. Do NOT
     reference the problem statement. Pretend you have no idea what the app should do.
   - **Phase B (compare):** NOW read the problem statement. Compare your blind
     description against the expected outcome. Flag discrepancies as findings.
   This ordering prevents confirmation bias -- you describe what IS, then check
   what SHOULD BE. Severity: high/medium/low.
2. **Backend Reviewer** -- backend.log. Checks for tracebacks, expected log lines,
   crashes. Must CONFIRM expected behavior, not just report absence of errors.
3. **Frontend Reviewer** -- console logs, optional HAR. Checks for JS errors,
   failed requests, WebSocket issues.

**UI Reviewer prompt template:**

```text
You are reviewing screenshots of a running application.

PHASE A -- BLIND DESCRIPTION (do this FIRST, before reading the problem statement below the divider):

Look at each screenshot and describe what you see. Be specific and objective:
- What text is visible?
- What UI elements are present (buttons, inputs, tables, lists, modals)?
- What states are elements in (enabled/disabled, checked/unchecked, expanded/collapsed)?
- Are there error messages, empty states, loading indicators?
- What is the layout structure?
- Is anything visually broken (overlapping elements, clipped text, missing images)?

Write your description for EACH screenshot before proceeding.

---PROBLEM STATEMENT DIVIDER---

PHASE B -- COMPARISON (read this only after completing Phase A):

Problem statement: <problem_statement>
Diff: <diff>

Now compare your blind description against what the problem statement says should
be visible. Every verdict MUST cite the specific Phase A observation it is based on.

Report format (cite Phase A evidence inline):
- CONFIRMED: <expected outcome> — Evidence: Phase A, screenshot N: "<exact quote from your Phase A description>"
- NOT OBSERVED: <expected outcome> — Searched: Phase A screenshots [list which ones checked], element not described in any
- FINDING: <severity> <discrepancy> — Evidence: Phase A, screenshot N: "<exact quote>" vs expected "<what problem statement requires>"

Do NOT write a verdict without a Phase A citation. If your Phase A description
is too vague to support a verdict, say so and flag it as an incomplete review
rather than guessing.

AUTH-GATE CHECK (run during Phase B): if EVERY screenshot's Phase A description
mentions an authentication gate (login form, PIN entry, sign-in button, "Enter
parent PIN", "Sign in", "Log in", etc.) AND describes zero feature-area UI from
the problem statement, emit the literal phrase `NOT OBSERVED: auth-gated substrate`
and exit Phase B. Do not produce other verdicts in this pass — the evidence is
unreviewable. This catches the silent false-pass mode where a fresh Playwright
context can't satisfy the auth, every screenshot shows the auth gate, and the
feature under review is never exercised.
```

Runtime reviewers must end with one of:
- `CONFIRMED: <what was observed matching the problem statement>`
- `NOT OBSERVED: <what the problem statement expected but evidence lacks>`
- `FINDING: <severity> <issue>`

A `NOT OBSERVED` counts as a medium finding.

#### `full` -- 8 parallel agents
All of the above, simultaneously.

### Step 7 -- Aggregate verdict

**This step is the provider-selected deterministic final judge — the consolidating gate (Switchboard Decision 9), and
it ALWAYS runs on the selected cloud provider's strong gate model.** This is the deterministic consolidating gate (judge-core §5.6) and the
strong GATE that any weak/local verdict defers to (§5.7). It is the structural precondition that makes a future `build-step-style`
local offload safe: the five `code` reviewers ADVISE, and this normalize-findings + verdict pass
makes the single PASS / NEEDS-WORK call. If the Style reviewer's findings ever come from the
local-judge offload (only when `build-step-style` is flipped to `true` in config — `false`
today), they enter here as advisory input that the strong provider gate consolidates; the local model never sets
the verdict directly. Today, with the offload disabled, this is unchanged — all reviewers are
the selected provider and this step gate exactly as before.

**When `--reviewers auto`:**
- All gates pass: **APPROVED**
- Any fail: **REJECTED** -- pass errors to developer

**When `--reviewers deep`:** the verdict arrives PRE-AGGREGATED — review-deep's own
deterministic aggregator already consolidated the lenses, so do NOT re-normalize its findings
through the table below. The provider-selected final-judge framing still holds: this provider-selected gate reads
`aggregated_verdict.result` from the sidecar and owns the translation to the terminal verdict —
`PASS` → **PASS**, `NEEDS-WORK` → **NEEDS WORK** (findings from the sidecar feed Step 9's
iteration loop), `DEFERRED-TO-UAT` → **PASS with deferral** (surface the sidecar's
`deferred_uat_items[]` verbatim in the Step 10 report for the phase-end Manual UAT bundle; do
not iterate the developer on deferrals). The local-offload cascade note above is unaffected —
review-deep is a strong-provider-tier instrument, not a weak-model advisor.

**When `--reviewers code|runtime|full`:**

Read each reviewer's full findings from its `<worktree>/.build-step/review-<lens>.{json,md}` file (Step 6 had them return only a terse verdict + top finding). Normalize findings:

| Finding type | Normalized severity |
|---|---|
| Correctness issue | **high** (always) |
| Bug (as reported) | high / medium / low |
| Security issue (as reported) | high / medium / low |
| Test flagged for deletion | **medium** |
| Significant style deviation | **medium** |
| Minor style note | low |
| Runtime finding (as reported) | high / medium / low |
| `NOT OBSERVED: auth-gated substrate` (UI reviewer) | **high** (always — evidence is unreviewable; forces NEEDS WORK) |
| `NOT OBSERVED` (any other) | **medium** (always) |
| `POST_MERGE_HALT:` (Step 8 post-merge test gate) | **BLOCKED** (skip Step 9 iteration loop; surface to operator — merge mechanics broke, not a developer-fix scenario) |
| `SHIP_GATE_HALT:` (Step 5.5 ship-gate re-check) | **BLOCKED** (same — upstream race; surface to operator, do NOT iterate developer) |

Verdict:
- **PASS** -- zero high findings AND fewer than 2 medium findings AND (for runtime/full)
  at least one reviewer confirms expected behavior was observed
- **NEEDS WORK** -- any high finding, or 2+ medium findings, or coverage gate failed

#### Prepare the machine-readable verdict

Compute the Step 7 result in memory. Do **not** write a durable PASS yet:
merge and post-merge gates have not run. The durable verdict is finalized on
every terminal path using
`../../_shared/build_step_verdict.py::write_verdict`.

Write only to `--verdict-path`, never inside `<worktree>`. The canonical schema,
atomic writer, and default-deny consume rule live in
`../../_shared/build_step_verdict.py`; treat that module as the source of truth.

Schema: `{schema_version, timestamp, run_id, writer, result, halt, summary, signature}`
- `schema_version` — integer `2`.
- `timestamp` — ISO-8601 of when the terminal verdict was written.
- `run_id` — exact `--verdict-run-id`.
- `writer` — locked string `build-step-orchestrator`.
- `result` — enum `PASS | NEEDS-WORK | DEFERRED-TO-UAT`.
- `halt` — `POST_MERGE_HALT | SHIP_GATE_HALT | null`.
- `summary` — one-line human-readable rationale.
- `signature` — lowercase HMAC-SHA256 over every prior field using the
  parent-local `VERDICT_KEY`.

Translator mapping (terminal string → `result`):

| build-step terminal string | verdict.json `result` |
|---|---|
| `PASS` | `PASS` |
| `APPROVED` (`--reviewers auto`) | `PASS` |
| `NEEDS WORK` (a SPACE) | `NEEDS-WORK` (a HYPHEN) |
| `REJECTED` (`--reviewers auto`) | `NEEDS-WORK` |
| review-deep `aggregated_verdict.result` (`--reviewers deep`) | passes through unchanged (`PASS` / `NEEDS-WORK` / `DEFERRED-TO-UAT`) |

`halt` derivation: if the verdict was driven by a `POST_MERGE_HALT:` or `SHIP_GATE_HALT:` sentinel
(Step 8 post-merge gate / Step 5.5 ship-gate), set `halt` to that sentinel **without** the trailing
colon (`"POST_MERGE_HALT"` / `"SHIP_GATE_HALT"`); otherwise `halt` is `null`. A non-null `halt`
makes the consumer treat the step as BLOCKED regardless of `result`.

Example (PASS):

```json
{"schema_version":2,"timestamp":"2026-06-22T10:15:30Z","run_id":"550e8400-e29b-41d4-a716-446655440000","writer":"build-step-orchestrator","result":"PASS","halt":null,"summary":"post-merge gates passed","signature":"<64 lowercase hex>"}
```

Example (post-merge halt):

```json
{"schema_version":2,"timestamp":"2026-06-22T10:15:30Z","run_id":"550e8400-e29b-41d4-a716-446655440000","writer":"build-step-orchestrator","result":"NEEDS-WORK","halt":"POST_MERGE_HALT","summary":"main-project test gate red after merge","signature":"<64 lowercase hex>"}
```

The prose verdict remains human-facing only. A parent that supplied the durable
channel never parses prose for authorization.

### Step 8 -- On PASS

**Ship-gate re-check** (run the canonical block from Step 5.5): avoid clobbering a parallel session's ship.

> Wrong-directory guard: before merging/committing the worktree's changes into the project repo, warn if the resolved target repo != the repo this lands in (advisory, never blocks) — per working-directory.md § Wrong-directory guard; reference impl `Test-WrongDirGuard`.

1. Merge changes to main project. Compute baseline + classify each changed file INLINE
   (no cross-block state — capture vars in the same block where used):
   ```bash
   cd "$PROJECT"
   DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
   DEFAULT="${DEFAULT:-master}"
   BASELINE=$(git merge-base "origin/$DEFAULT" HEAD)
   ```
   For each file `f` in `git -C "$WORKTREE" diff HEAD --name-only`, classify by `git log --oneline "$BASELINE..HEAD" -- "$f"` in `$PROJECT`. Precedence (mutually exclusive — pick the first match): **Parallel-safe** → **Shared across steps** → **Step-exclusive**.
   - **Parallel-safe** (operator opted into concurrent worktrees): use `git -C "$PROJECT" merge --squash "$BRANCH"` — 3-way merge handles BOTH parallel-safety AND shared-file overlap. Skip the other categories.
   - **Shared across steps** (≥1 commit since `$BASELINE` touched `$f` — e.g. routes, `database.py`, `runner.py`, config): do NOT full-file copy. Apply only the worktree's diff hunks via `git -C "$PROJECT" apply --3way <(git -C "$WORKTREE" diff HEAD -- "$f")` — git's own 3-way merge engine, prior steps' changes survive. Full-file copy here is the Alpha4Gate Phase 2 incident (step 4 clobbered step 2's `action_probs` + step 3's `--no-reward-log` in `database.py`/`runner.py`; 6 tests failed).
   - **Step-exclusive** (zero commits since `$BASELINE` touched `$f`): safe to `cp "$WORKTREE/$f" "$PROJECT/$f"`.
   - Worktree-with-UI environment: Step 5's copy loop should ALSO apply this same classification (back-propagated; full-file `cp` in Step 5 is the known loophole — Step 5 sub-step 1 must honor shared-file Edit semantics or this gate is too late). For now, re-verify by sampling: if any shared file shows clobbered prior-step content, HALT.
   - Docker environment: classification predicate runs in `$PROJECT` against the worktree's branch regardless of whether the source is `$WORKTREE` or `workspace/results/`.
   See `dev/.claude/rules/worktree-hygiene.md § 5` (silent no-op when merge runs in wrong worktree — always use `git -C "$PROJECT"`) and `§ 6` (shared-file overwrite risk).
2. **Post-merge test gate (mandatory):** run the test suite IN the main project (`cd "$PROJECT" && <test_command>`), NOT just in the worktree. If it fails, atomically call `write_verdict` with `terminal="NEEDS WORK"`, `halt="POST_MERGE_HALT"`, and the parent run id/path/key **before returning**. Echo the literal sentinel `POST_MERGE_HALT:` followed by the failing tests, do NOT close the issue or declare PASS, exit non-zero. The orchestrator routes the halt to the operator, not developer iteration.
3. Run the final **ship-gate re-check**. Any `SHIP_GATE_HALT` atomically
   overwrites the durable verdict with `terminal="NEEDS WORK"` and
   `halt="SHIP_GATE_HALT"` before returning.
4. Clean up worktree/branch (or container), clean up evidence (unless
   `--keep-evidence`), and restore the stash. If any cleanup/restoration fails,
   atomically write `NEEDS WORK` before returning.
5. **Finalize PASS only after every merge, post-merge, ship-gate, cleanup, and
   restoration operation succeeds.** Atomically call `write_verdict` with the
   parent path/run id/key and the in-memory terminal result (`PASS`, `APPROVED`,
   or `DEFERRED-TO-UAT`).
6. Close the issue if `--issue` was provided. Issue closure is best-effort
   bookkeeping after the code verdict; if it fails, report a warning and leave
   the authenticated PASS unchanged:
   ```bash
   gh issue close $ISSUE --comment "Completed via build-step. All gates passing."
   ```

### Step 9 -- On NEEDS WORK

Compile findings from ALL reviewers into a single block — read each lens's full findings from its `<worktree>/.build-step/review-<lens>.{json,md}` file (Step 6), not from the terse spawn-time returns. On the `deep` lane, read findings from review-deep's JSON sidecar (`<worktree>/.review-deep/<timestamp>.json`, `lens_verdicts[].findings[]`) instead — there are no per-lens gauntlet files.

**Stop-and-audit check (run BEFORE iterating):** If the SAME bug-shape (same invariant violated, same anti-pattern, same producer/consumer drift, same constant duplicated) has been flagged in **three** iterations in a row -- even at different file locations -- STOP iterating, do NOT spawn the developer for another whack-a-mole fix. Instead, follow the Stop-and-audit rule below: grep the entire codebase for the bug-shape, enumerate every site, and report ONE comprehensive audit finding plus a structural regression-test proposal (e.g. assert single source of truth via CI grep, assert object identity not equality). Mark the run **BLOCKED (audit required)** and skip to the BLOCKED report.

If iterations remain AND the stop-and-audit check did not trigger:
1. If UI evidence was captured: revert copied files in main project
   ```bash
   while read f; do git checkout -- "$f"; done < .ui-review-evidence/copied-files.txt
   ```
2. Go to Step 2 with all findings appended to developer prompt
3. Developer works in the same worktree (cumulative fixes)

If max iterations exhausted: **BLOCKED**
1. Atomically call `write_verdict` with `terminal="NEEDS WORK"`, halt `null`,
   and a summary naming the terminal reason. This overwrites a planted or stale
   file.
2. Print remaining findings
3. Keep worktree alive for manual inspection
4. Restore stash if created
5. Report:
   ```text
   build-step BLOCKED after N/M iterations

   Remaining findings:
     <per-reviewer summaries>

   Evidence: .ui-review-evidence/run-N/   (if applicable)
   Worktree: <path>
   Branch: <branch>
   ```

When a parent-supplied channel exists, every other terminal BLOCKED path
(stop-and-audit, required tool missing,
reviewer parse failure, merge conflict, or ship-gate halt) MUST call
`write_verdict` before returning. No terminal path may inherit the initialized
`run incomplete` verdict or a provisional result. Standalone invocations return
the same human-facing result without writing a sidecar.

### Step 10 -- Final report

```text
build-step complete
  Isolation: worktree | docker
  Reviewers: auto | code (5) | deep (/review-deep delegate) | runtime (3) | full (8)
  Verdict: PASS (iteration N/M)
  Files changed: N
  Gates: typecheck OK, lint OK, test OK
  Code review: correctness OK, bugs OK, tests OK, style OK   (if applicable)
  Deep review: aggregated <PASS|NEEDS-WORK|DEFERRED-TO-UAT>; audit sidecar .review-deep/<timestamp>.json   (if applicable)
  Runtime: UI OK, backend OK, frontend OK                     (if applicable)
  Tests: X/Y passing
  Issue: #N closed | #N close failed (warning) | not supplied
```

> Next-step commands name their target directory, and the proactive project-switch message fires on a cwd≠project mismatch with no pin, per transition-directory-contract.md.

---

## Write-as-you-go

build-step MUST write to `current.md` at 6 specific trigger points during execution.
Writing is mandatory — same priority as running tests. Do not defer to step completion.

**Path resolution (MUST use the main worktree root — never current-worktree-relative):**
```powershell
param([Parameter(Mandatory = $true)][string]$ExplicitProjectPath)
$mainWorktreeRoot = (& git -C $ExplicitProjectPath rev-parse --show-toplevel).Trim()
$statePath = Join-Path $mainWorktreeRoot ".claude\task-state\current.md"
```
Worktree cwd (`../worktree_<branch>/`) is deleted on cleanup. Writes inside a worktree
are silently lost. State paths must be resolved against the main worktree root, never
against the current worktree. Use an explicit path parameter, not `git rev-parse` from cwd.

### Trigger points

| # | Trigger | What to write to current.md |
|---|---------|----------------------------|
| 1 | Start of each developer iteration | MUST overwrite `WIP.Approach` with the approach being tried |
| 2 | Any test failure | MUST append to `Dead Ends`: approach + specific error summary (1 line) |
| 3 | Any significant codebase discovery | MUST append to `Critical Gotchas`: the fact + why it matters |
| 4 | File read that reveals non-obvious structure | MUST append to `Key Files`: path + what was learned |
| 5 | After tests pass (step succeeds) | MUST append to `Completed`: step name + test count + commit SHA |
| 6 | Before starting iteration N≥2 | MUST call `task-handoff --loop --no-commit` (writes current.md; build-phase Step 2e commit picks it up — avoids double-commit) |

### Write formats

**Dead Ends** (trigger 2 — append):
```
- [approach in 5-10 words]: [specific error or finding — not "didn't work", say WHY]
```

**Critical Gotchas** (trigger 3 — append):
```
- [fact]: [implication for current task]
```

**Key Files** (trigger 4 — append):
```
- `<path>`: <what was learned — why non-obvious>
```

**Completed** (trigger 5 — append):
```
- [<sha>] <step name>: <result> (<test count> tests)
```

**WIP.Approach** (trigger 1 — overwrite):
```
**Approach:** <what is being tried right now — one line>
```

### Inline write — no extra tool call chain

The write MUST happen via direct Edit to `current.md` inline, not via a sub-skill
invocation or a separate tool call sequence. Trigger 6 (`task-handoff --loop --no-commit`)
is the only exception — it handles the git mechanics. All other triggers are direct Edits.

### Schema reference

Full field definitions, overwrite/append rules, and lifecycle:
`.claude/references/task-state-schema.md`

---

## Shared build-phase halt contract (verbatim)

## Halt contract

The 5 conditions under which `/build-phase` is permitted to halt mid-run. Anything else is a defect — surface it as a finding upstream (`/plan-review`, `/plan-wrap`), not a mid-run halt. Long-form rationale + the workspace-wide source-of-truth lives in `dev/.claude/rules/code-quality.md § "Build-phase halt contract"`; this section inlines a 1-sentence summary per item so an operator reading SKILL.md cold doesn't have to navigate out. Reference investigation `02-halt-contract.md`.

1. **Conditional-step predicate errored or returned non-binary.** A `Type: conditional` step's `Condition:` shell expression exited with a code build-phase cannot interpret as run-or-skip (command-not-found ≥126, syntax error, signal-terminated ≥128, or a predicate that outputs but never exits). See "Conditional step handling" below for the dispatch table.
2. **Quality-gate hard fail.** typecheck error count > 0, test count regressed below baseline, lint produced a blocker-class finding — OR (per Step 1's race-condition defense in sections 2d/2e) `origin` advanced with commits overlapping the step's modified file set. All four are integrity-class failures: the worktree's claim that "this step ships these changes against this baseline" no longer holds. The race-condition extension is documented as a sub-case of this halt class, NOT a new (6th) halt class — preserves the 5-item allowlist.
3. **Stop-and-audit triggered.** Third instance of the same bug-shape in this session, per `/build-step`'s stop-and-audit rule. Whack-a-mole is wasting time; STOP iterating and audit the codebase for siblings before continuing.
4. **Wait-type step reached.** A step declared `Type: wait` is long-running observation work (a soak test, a benchmark run). The orchestrator halts intentionally so wall-clock waiting doesn't burn context window. Resume in a fresh session via `--resume <next-step>` after the wait completes.
5. **Worktree merge conflict.** A surgical-edit conflict from earlier steps overlapping the current step's files. Requires human resolution before continuing.

**Defect-of-input class** (Step 0 pre-flight Blockers — caught BEFORE any step execution, so technically not "mid-run"):

- Plan has `Type: conditional` step without `**Condition:**` field (caught at Step 0 sub-bullet 6; upstream catches: `/plan-review` §23 + `/plan-wrap` §12).
- Plan has `Type: operator` step with code-shaped `Produces:` but plan-review/plan-wrap autofix didn't run (caught at Step 0 sub-bullet 7's runtime safety net).
- Plan step declares `--reviewers full|runtime` without `--start-cmd`+`--url` (caught at Step 0 sub-bullet 8's Step-flags pre-flight validation, per Step 2 of BP plan).

Mid-run halts outside this list are defects to fix upstream — examples that are NOT in the allowlist: mid-run `(y/n)` confirmation prompts, "Should I continue?" gates, operator-step halts for code-Produces steps (auto-split handles these), pure-observation operator-step halts mid-phase (deferred-UAT bundle handles these). See `dev/.claude/rules/code-quality.md § "Build-phase halt contract"` for the full anti-pattern list and the upstream-defect framing.

## Constraints

### Stop-and-audit rule

When fixing bugs across multiple iterations or steps, count instances of the same
bug shape:

- **First instance:** fix it. Add a regression test.
- **Second instance** (same shape, different location): fix it. Note the pattern out
  loud — "this is the second time I've seen X in this session." Add a regression
  test that asserts the invariant the bug violated.
- **Third instance: STOP and audit.** Do NOT keep fixing one-at-a-time. Three
  instances of the same shape is overwhelming evidence that more siblings exist.
  Grep the entire codebase for the bug-shape (the literal value, the function name,
  the code pattern), enumerate every match, and land ONE comprehensive fix that
  addresses all of them in one PR. Then add a structural regression test that makes
  re-introducing the pattern impossible (e.g., assert object identity instead of
  value equality, assert single source of truth via grep in CI, lint rule that bans
  the literal).

## Limitations

- Worktree: no full isolation from host (but separate working directory)
- Docker: slower startup, needs Docker Desktop running, and needs provider credentials
- Code reviewers: ~3-5 min per iteration (5 parallel agents)
- Deep lane: one /review-deep invocation per iteration (code lenses + deterministic
  aggregation + JSON sidecar; costlier than `code` — reserve for high-stakes steps
  per review-deep SKILL.md's header)
- Runtime reviewers: ~5-8 min per iteration (app startup + capture + 3 agents)
- Full: ~6-10 min per iteration (8 agents)
- Screenshots consume context window budget -- keep page count reasonable
- Windows-primary: uses `taskkill /T /F /PID` for process tree kill


---

## dev-observatory hook (additive; see `.claude/rules/descriptor-contract.md`)

When `--ui` is set, check the chosen bind port against the workspace's canonical map before binding:

```
uv run --project dev-observatory observatory ports
```

It flags accidental collisions; intentional shares (e.g. `void_furnace ↔ switchboard :8080`) are whitelisted.
