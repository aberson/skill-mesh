# Skill pipeline — the routing web

> **Vendored into skill-mesh.** This is a copy of the workspace reference document of the
> same name, vendored into the shared payload (`_shared`) so that the skill cores citing it
> resolve inside a host discovery root rather than against a workspace directory no
> consumer home has.
> Two adaptations apply throughout: citations to workspace documents that are **not** part
> of this payload are rendered as plain names rather than links (their targets do not ship
> here), and operator-specific identifiers, private issue/cron references and
> harness-configuration paths have been removed. The per-file sign-off and the full list of
> link dispositions are recorded in this repository's Step 66 decision record.

This file is the routing web: the 8 rails an operator fragment can land on (entry
condition + skill chain), the re-route edges between them, and the re-route contract.
It is the ONE owner of the rails and of the `re-route:` line format — `/user-gateway` consults this web to route intake fragments, and rail
skills cite this section; no skill hardcodes its own routing table.

---

## The 8 rails

Entry condition = what the operator's fragment sounds like.

| Rail | Sounds like | Chain |
|---|---|---|
| **bug** | "X is broken / erroring / behaving wrong" — a symptom in hand | `/user-debug --symptom '...'` |
| **do** | "just do X" — a resolved atom / small concrete task | `/goblin-do` (atoms come from `/goblin-suggest`) |
| **plan** | "add / build capability X" — multi-step work needing steps + review | `/plan-feature` (or `/plan-init` for a brand-new project) → `/plan-expedite` → `/build-phase` → `/repo-update` (the build rail — detail below) |
| **investigate** | "what's true about X? why does X happen?" — a question, not yet work | `/deep-research` via `Workflow({name: "deep-research-pinned"})` (never the built-in name — CLAUDE.md's dispatch rule) for external/multi-source; an Explore-agent sweep for codebase-local questions |
| **verify** | "does X actually work? / I don't trust X" — distrust without a reproducible symptom | `/review-uat` (refine a fuzzy block) / `/user-uat` (mechanical tier) / `/user-shakedown` (autonomous closure) / `/user-walkthrough` (attended) — four-mode detail below |
| **trim** | "the plan feels bloated / what can we cut" — plan-borne cruft-smell | `/plan-trim` (plan documents only; non-plan cruft-smell routes **investigate** first — assess, then `investigate→plan` or `investigate→do`) |
| **decide** | "should we do A or B?" — an operator-only choice | surfaced-only: parked with the open question stated; never ground through autonomously |
| **draft** | "here are rough thoughts" — wants a usable prompt or goal, not work done | `/user-draft` → `/goal` |

**Tiebreak:** when a fragment plausibly fits two rails, pick the rail with the cheaper
commitment and let a re-route edge correct it. The common tie — **bug vs verify** — splits
on evidence: a reproducible symptom in hand → **bug**; distrust without one → **verify**
(and `verify→bug` upgrades it the moment a check fails).

---

## Re-route edges (9)

A rail is a starting guess, not a cage. The sanctioned edges, each with its trigger:

- **do→plan** — the atom's scope grows past a small concrete task mid-execution.
- **do→bug** — the thing being improved turns out to be broken.
- **bug→plan** — diagnosis concludes the symptom is not a defect; the ask is designed, multi-step work.
- **investigate→plan** — findings imply real multi-step work.
- **investigate→do** — findings imply one small concrete action.
- **plan→trim** — the plan has accreted cruft; cut before building.
- **plan→do** — scoping collapses the "feature" to one small concrete action.
- **verify→bug** — verification fails; the failing check is now a symptom in hand.
- **any→decide** — an operator-only choice surfaces; park it, never ground through.

---

## Re-route contract (ONE owner: this section)

When a rail skill discovers mid-run that the work is on the wrong rail, it:

1. **Emits one standard line** — format (owned here; skills cite it, never restate it):
   `re-route: <from-rail> → <to-rail> — <one-clause reason>`
2. **Emits the seed for the correct rail** — the `/plan-feature` seed, the
   `/user-debug --symptom` line, the parked decision question, etc.
3. **Writes back to the intake ledger when one exists**
   ([`intake-engine.md`](./intake-engine.md)): the row's status stays
   `routed`, with a disposition note recording the re-route.
4. **STOPS** instead of grinding through on the wrong rail.

`/goblin-do`'s small→big handoff — a `big` atom gets the `/plan-feature` seed + the
build-rail next step printed, then the skill deliberately stops — is the codified
template for this contract.

---

## The build rail (plan) in detail

First-time setup: `/repo-init` once before first `/plan-expedite`.

```
[dev-root] /plan-init  or  /plan-feature   Plan: produce plan.md with build steps (planning is dev-root-fine — plan from anywhere)
        │                           └─ [dev-root] /plan-redline (auto at plan-init close; on-request after plan-feature/plan-merge): operator-facing proposal Artifact — P/D decision inventory, ID-referenced feedback folded back into the plan BEFORE issues are minted
        ▼
··· plan→repo context switch ··· /plan-expedite ANNOUNCES + PINS it here (between plan-wrap and repo-sync): plan-review/plan-wrap are dev-root-fine plan-doc ops; repo-sync onward targets the project repo
[dev-root → project] /plan-expedite   Autonomous prep: chains plan-review --autofix → plan-wrap --autofix → repo-sync → task-handoff --next-task as one unattended pre-flight before /build-phase (--new-window: durable task-handoff --next-task write, then /session-wrap --end renders handoff-prompt.md + the Pick-up-here block)
        │
        ▼   ◇ suggested /clear point — before /build-phase; NEVER mid-build (see below)
[project] /build-phase --plan <path>   Build: run each step via /build-step
        │                           └─ [project] /build-step (single step, configurable)
        ▼
[project] /repo-update            Ship: commit, update docs, push
        ▼   ◇ suggested /clear point — after this phase's build + ship, before the next phase / operator UAT; NEVER mid-build (see below)
```

**Home context + window-recycle points** (owner of the two-repo model: `working-directory.md`):

- **Homes.** `[dev-root]` = coding-root work — plan-doc skills (`/plan-init`, `/plan-feature`, `/plan-redline`, and plan-expedite's `plan-review`/`plan-wrap` legs) run from anywhere; planning is dev-root-fine. `[project]` = anchored to the project's own repo — everything from `repo-sync` / `/build-phase` / `/build-step` / `/repo-update` onward. `[dev-root → project]` on `/plan-expedite` is the ONE context-switch seam: it announces the switch and pins the project (`/user-project`) at the plan→repo boundary so build + ship target the right repo regardless of cwd.
- **Suggested window-recycle (`/clear`) points `◇` — SUGGESTIONS, never requirements, and NEVER mid-build:** (1) after `/plan-expedite`, before `/build-phase`; (2) after a phase's `/build-phase` + `/repo-update`, before the next phase or its operator UAT; (3) at a `Type: wait` handoff, where `/build-phase` halts anyway (halt-contract class #4). Each is a prompt you can ignore — auto-compaction + the armed `/goal` keep a `/build-phase` running continuously in one window, and interrupting mid-build strands it. **`/session-wrap` owns the actual `/clear` routing** (its `clear-next` route); this map only annotates where the clean boundaries are.

Task state schema (write-as-you-go): [`task-state-schema.md`](./task-state-schema.md) — field definitions, write discipline, path resolution contract, lifecycle.

---

## Review routing

`/review-gauntlet` is the **lean profile over `/review-deep`'s engine** — same code
lenses and deterministic aggregation, terse PASS / NEEDS-WORK verdict, no JSON sidecar.
`/build-step` carries a `--reviewers deep` lane that dispatches `/review-deep` directly
for high-stakes steps; `/plan-review` §27 routes those steps at plan time.

---

## Session transitions & orientation

- `/session-wrap` — the transition front door: triages (context signal, task boundary,
  git state, armed `/goal`), announces one of 3 routes, then acts: `continue` /
  `clear-next` / `end-window`. `--advise` is the read-only variant: verdict banner
  (adds `SAFE TO CLOSE`) + loss report, never acts. Owns the actual `/clear` mechanics;
  the build rail (§ The build rail) only annotates the *suggested* recycle boundaries where
  a `clear-next` is worth considering — never mid-build.
- `/user-wrap` — the return-moment front door ("sitting back down — keep going or
  close?"): orients, delegates the verdict to `/session-wrap --advise`, re-presents its
  banner + loss report, acts per verdict.
- `/task-handoff` — the checkpoint library orchestrators call (`--loop [--no-commit]`,
  `--next-task`, `--resume`; `--end` delegates to session-wrap).
- `/user-orient` — **session axis** (this thread's state; `--quick` tier = lightweight
  three-section summary) vs `/user-pm` — **project axis** (plan+git-derived shipped /
  planned / next / cuttable).
- `/user-debug` (formerly `/bug-fix`) and `/memory-distill` (formerly `/review-memories`) renamed this phase.

---

## Post-build operator acceptance (verify rail detail)

Four modes: `/user-uat` EXECUTES an already-clear UAT block; `/review-uat` REFINES a fuzzy one; `/user-walkthrough` lets the operator DRIVE exploration of a just-built feature (agent answers from source, fixes small, logs big, marks coverage); `/user-shakedown` AUTONOMOUSLY CLOSES the shared UAT ledger to zero open items (designed to run armed under `/goal`). The walkthrough/shakedown pair share one ledger contract: `shakedown-engine.md`.

Visual tier: `/user-uat --ui` delegates single-frame screen states to `/judge-ui` and transition-shaped steps (route change, modal open/close, … — full list: `/judge-motion`'s When-to-use) to `/judge-motion` — the static/motion vision-judge sibling pair.

---

## Supporting skills

`/review-proof`, `/test-prune`, `/skill-eval-setup`, `/skill-iterate`,
`/goblin-suggest` (produces the atoms `/goblin-do` consumes), `/memory-distill`,
`/user-brainstorm`, `/user-learn`, `/context-slim`, `/lesson-harvest`.

`/repo-wrap [<path-or-slug>] [--dry-run]` — the repo close-out router for targets `/repo-update`
doesn't fit: classifies ONE target and runs the matching rail (owned project → delegates to
`/repo-update` verbatim; dev coding-root → formalized dev-sync; third-party `owned=false` clone →
local-commit durability, never pushes to a remote the operator doesn't own; unregistered dir →
private off-machine backup). Repo-scoped, not session-scoped — safe outside any wrap moment. The
wrap-side seam (session-wrap's git-verb router delegating these repo classes so bare `/user-wrap`
covers them) is tracked as a coding-root issue sequenced with utility-hookup's session-wrap batch.

`/user-afterparty` — the milestone workspace-hygiene front door (also fired by the workspace's monthly hygiene cron). Report-first orchestrator that SEQUENCES the hygiene skills, owning
none of their logic: it runs the autonomous set into one report (`/lesson-harvest --dry-run`,
`/context-slim`, a tier-drift check, meta-tool-prune), then walks `/memory-distill` → `/test-prune` →
`/plan-trim` one at a time (yielding at each gate), and owns two orphans with no other home —
orphan-`worktree_*` cleanup and the derived-`current.md` rollup commit/archive seam. Flags:
`--only` / `--skip` / `--dry-run` / `--all-projects`.

`/build-queue --queue <path>` — meta-orchestrator: drains a queue of N pending plans, invokes `/plan-expedite` + `/build-phase` per item, parks halts as GitHub issues (does not retry), polls a kill-switch file between items, emits a morning summary.

`/skill-evolve --skill <name> --variants <path-or-inline>` — A/B-tests N variant mutations of a skill in parallel worktrees, scored against the skill's existing `evals/` suite. Winner branch is pushed and a `gh pr create` command is printed (no auto-PR); losers are cleaned up and analyzed under `docs/investigations/skill-evolve/`. Requires `/skill-eval-setup` to have set up the target skill's evals first.

dev-observatory hooks (additive, degradable — the control plane works on best-guess without them): `/plan-init` registers a new owned project (`observatory register`); `/repo-update` refreshes verbs/ports + tasks (`observatory sync`); `/build-step --ui` port pre-flight (`observatory ports`); `/user-pm` gains a `--json` mode; `/plan-review` + `/plan-wrap` check a scrapable goal + port collisions. Full contract: `descriptor-contract.md`.
