# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

## Provider-neutral host abstractions

- Resolve supporting assets and relative script paths against `.claude/skills/user-uat/`; the canonical prose lives here while implementation assets remain with the compatibility launcher.
- A named skill call means the host's skill-dispatch primitive. An Agent, Explore agent, workflow, or sub-agent means an isolated task/action invocation with fresh context and the requested capability tier. Provider wrappers map these roles to their native APIs.
- Model tier names in inherited procedures describe capability roles. Resolve them through `config/model-tier-map.json`; an unavailable required capability returns `required_tool_missing` rather than weakening a gate.
- Never expose hidden chain-of-thought. Preserve only decisions, evidence, commands, structured artifacts, and operator-facing rationale required by this contract.

# User UAT

> **Judging doctrine:** the mechanical-gates-first, evidence-on-every-verdict, and low-confidence-escalates invariants behind this skill's partition live in [`_shared/judge-core.md`](../../_shared/judge-core.md) — this skill instantiates them for the UAT-execution case.

Execute an **already-clear** UAT block so the operator doesn't have to be the mechanical
relay (run command → eyeball output → paste it back). The skill runs each step, captures
the real result, and **auto-judges only the deterministically-checkable steps**; everything
that needs judgment is escalated with the evidence attached.

It does **two things deliberately NOT**: it does not *refine* a fuzzy script (that is
`/review-uat`), and it does not *replace the operator* for checks that genuinely need a
human. The win is the mechanical tier — which is most of the volume.

## When to use / not

- **Use:** a concrete UAT exists — a `Type: operator` plan M-step, a build-phase "Manual UAT"
  bundle, the "commands + what to look for" table from a handoff, or the operator pasting
  "run these and tell me what happens." Steps have commands and observable expectations.
- **Don't use** to write or refine a UAT. If steps are ambiguous (verb with no object, "expect
  X" with no observable, no pass criteria), **STOP and delegate to `/review-uat`** — do not
  guess what a step means. A run built on a guessed expectation is worse than no run.

## Invocation

```text
/user-uat                       # use the UAT block from the current conversation
/user-uat path/to/plan.md#M4    # run the M-step at this anchor
/user-uat --dry-run             # classify + print what WOULD run (mechanical / side-effectful / escalated); run nothing
/user-uat --deep                # also agent-JUDGE the judgment-class checks; each flagged 'agent-judged: <verdict> — confirm?'
/user-uat --ui                  # drive + vision-JUDGE the visual-tier steps (static → /judge-ui, transitions → /judge-motion) instead of escalating them to you
/user-uat --yes-side-effects    # auto-run side-effectful steps too (trusted flow); default gates them
```

## The partition (the load-bearing rule)

Operator UAT exists to catch what agent self-checks miss (agents grading agent-written work
codify regressions — toybox G2; the audit-wire-shape rule). So **never auto-PASS a check that
isn't deterministic.** Classify every step's *action* and *verify* (separately) into:

| Tier | The verify is… | Default behavior |
|---|---|---|
| **Mechanical** | exit code, "stdout contains X", "refuses with Y", a DB row / count, HTTP status, file on disk, a log line | **Auto-judge** PASS/FAIL — show the observed value as evidence |
| **Agent-judgeable** | "output looks grounded", "the ship-vs-park call was right", a diff reads sensibly | **Escalate** with evidence (default). With `--deep`: agent assesses too, labeled `agent-judged: <verdict> — confirm?` |
| **Visual** *(needs `--ui`)* | a **rendered screen state** visible in one browser frame — layout, a component, copy, a list/table, "the right screen showed" — or a **UI transition** between such states | **Without `--ui`: escalate (Human).** With `--ui`: drive + vision-judge via `/judge-ui` — read-back-cross-checked; `UNCERTAIN → escalate`, never auto-PASS. **Transition-shaped steps** (route change, modal open/close, … — full list: `/judge-motion`'s When-to-use) delegate to `/judge-motion` instead; single-frame static states stay with `/judge-ui` |
| **Human** | audio / sfx, real-device input, kid-facing feel, anything credentialed or physical the agent can't drive (transition-shaped motion → the Visual qualifier) | **Always escalate** — a crisp one-line ask, never a verdict |

**When classification is ambiguous, treat the verify as human and escalate.** A
mechanical-judgement applied to a judgment-class check is exactly how the blind spot leaks
back in. **Even with `--ui`, audio / feel stay Human** — the agent can't hear a sound or judge
kid-facing feel; transition-shaped motion routes to `/judge-motion` per the Visual qualifier,
not to a still-frame judge.

## Flow

1. **Ground + classify (no guessing).** For each step emit a classification line:
   `Step N (source: file:line / M-anchor) — action: <command>; verify: <expectation>; Tier: Mechanical / Agent-judgeable / Human`
   The source citation must appear on the per-step classification line, not just in a header.
   Valid tiers are **Mechanical**, **Agent-judgeable**, **Human** — plus, only when `--ui` is
   passed, **Visual** (a vision-judgeable subset carved out of Human: a rendered screen state or a
   UI transition — transition-shaped steps carry the tier table's `/judge-motion` qualifier;
   audio/feel stay Human). There is no "Ungroundable" category. If a step can't be grounded or is
   ambiguous → stop, report it, and point at `/review-uat`.
2. **Safety gate.** Tag each command read-only/preview vs **side-effectful** (mutates state,
   is outward-facing, or is hard to reverse — e.g. a real `goblin do` that auto-ships into a
   sibling repo, a deploy, an external send, a DB write/drop, a `git push`, starting a process
   that writes or sends anything). Auto-run the safe ones; **pause and confirm before each
   side-effectful one** (unless `--yes-side-effects`). **Never rationalize a side-effectful step
   as "probably read-only" to skip the confirmation gate.** If reversibility / outward-facing-ness
   is unclear, treat it as side-effectful and confirm (fail safe). Prefer the step's own
   `--dry-run`/preview when it has one.
3. **Run the auto-tier.** For each step, run its *action* (subject to the step-2 side-effect
   gate — the action may be agent-run, or a human/side-effectful one you've confirmed), capture
   stdout/stderr + exit code, then **auto-judge only the mechanical-tier verify** against its
   concrete expectation. Show the **actual observed value** inline — data, not editorializing. A
   mechanical **FAIL stops the run** (don't barrel past a failure into dependent steps), then
   still emit the step-5 report for the steps that ran + which step failed (observed-vs-expected).
   **Long-running actions** (a server start, a watcher): run them in the **background**, then poll
   a **readiness probe** (health endpoint, listening port, or an expected log line) before running
   any dependent verify — never block the run on a foreground server. A probe that never comes up
   within its budget is a mechanical **AUTO-FAIL** with the captured log tail as evidence, and
   stops the run like any other mechanical FAIL.
4. **Judgment tier.** For agent-judgeable / human steps: present the captured evidence + the
   expectation and **escalate** (default). With `--deep`, also give the agent's assessment for
   the agent-judgeable ones — flagged `agent-judged: <verdict> — confirm?`, with any uncertainty named.
   Human-tier steps always escalate regardless of `--deep`.
   **Visual-tier steps:** without `--ui`, escalate like Human. With `--ui`, delegate single-frame
   states to `/judge-ui` — it drives the screen, captures stage screenshots, and renders a vision
   verdict **cross-checked against an API/DB read-back** — and transition-shaped steps to
   `/judge-motion` (screencast + filmstrip vision verdict; mechanics live in its SKILL.md). Either
   judge's corroborated PASS lands in the step-5 report with its evidence (screenshot/filmstrip +
   read-back value), and an `UNCERTAIN`/`ESCALATE`/low-confidence/pixels-vs-
   read-back-disagree result falls back to the **`Needs you`** section. Use the project adapter for
   bring-up + auth (e.g. toybox `/uat-ui`); never drive an app instance you don't own.
5. **Report (terse).** One line per step — **plain text, not a markdown table**:
   `step → AUTO-PASS / AUTO-FAIL / ESCALATED → one-line evidence`
   Example: `M4 row 1 → AUTO-PASS → exit 0, stdout contains "shipped"`
   Then a **"Needs you"** section (use that exact heading) listing each escalated item as a
   **terse single-sentence ask** — no captured output blocks, no interpretive framing; an ask
   that has the operator run a command in a project repo names its target directory. End by
   naming what's left (e.g. "Please eyeball M4 row 3 and M4 row 5; the rest passed").

> Next-step / Pick-up-here commands name their target directory, and the proactive project-switch message fires on a cwd≠project mismatch with no pin, per transition-directory-contract.md.

## Safety + discipline

- **Never auto-PASS a non-mechanical check.** Mechanical = auto; agent-judgeable = escalate
  (or `--deep` + label); human = always escalate.
- **Gate side effects.** Read-only/dry-run/preview auto-run; destructive or outward-facing
  steps confirm first. `--yes-side-effects` only for a flow the operator has declared trusted.
- **Delegate, don't guess.** Fuzzy/ungroundable script → `/review-uat`, not a guessed run.
- **Push back on state mismatch.** If the operator (or `--deep`) calls something PASS but the
  mechanical check disagrees, surface the discrepancy verbatim (`observed X, expected Y`) plus
  ONE disambiguating question — don't rubber-stamp (per `feedback_uat_pushback_on_state_mismatch`).
- **Show the data.** Every verdict cites the observed value; a verdict with no evidence is a
  defect.
- **`--ui`: never drive an app instance you don't own.** A vision flow that logs in with a UAT
  PIN against the operator's real (or a parallel session's) app can lock out their account. Use
  the project adapter's isolated bring-up, and check port ownership before driving.

## Relationship to other skills

- **`/review-uat`** — the refinement partner. It tightens a fuzzy UAT, and its `--exec` delegates
  execution of the refined script HERE — `user-uat` is `/review-uat --exec`'s execution target, as
  well as the terse *run-an-already-clear-one* path that hands fuzzy input back to it. Refine with
  review-uat, then run with user-uat.
- **`/judge-ui`** — the visual-tier executor `--ui` delegates single-frame states to: drives a
  browser flow, captures stage screenshots, and renders a vision verdict cross-checked against a
  read-back (`UNCERTAIN → Human` fallback). Project adapters (e.g. toybox `/uat-ui`) supply its
  bring-up + auth. Pairs with `--deep` the way `judge-ui` pairs with this skill's Human-fallback.
- **`/judge-motion`** — the motion/transition sibling `--ui` delegates transition-shaped Visual
  steps to (full list: its When-to-use); its `ESCALATE` feeds the `Needs you` section the same
  way. Single-frame static states stay with `/judge-ui`.
- **`/verify`** — runs the app to confirm a code change works; `user-uat` runs a *defined UAT
  script*, partitioning auto-vs-human across its steps.
- **`/build-phase`, `/build-step`** — their `Type: operator` / "Manual UAT" outputs are exactly
  the blocks `user-uat` is built to execute.
- **`/user-walkthrough`, `/user-shakedown`** — the two operator-acceptance siblings for a
  just-built feature with no clear script yet. `/user-uat` EXECUTES an already-clear script;
  `/user-walkthrough` is operator-DRIVEN exploration (you drive, the agent answers from source /
  fixes small / logs big); `/user-shakedown` AUTONOMOUSLY CLOSES the resulting UAT ledger to zero
  open items. Poke a fresh build with a walkthrough/shakedown; run a defined block with user-uat.
