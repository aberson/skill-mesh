# Skill pipeline — the routing web

> **Vendored into skill-mesh.** This is a copy of the workspace reference document of the
> same name, vendored into the shared payload (`_shared`) so that the skill cores citing it
> resolve inside a host discovery root rather than against a workspace directory no
> consumer home has.
> Two adaptations apply throughout: citations to workspace documents that are **not** part
> of this payload are rendered as plain names rather than links (their targets do not ship
> here), and the private *values* of three classes (operator-specific identifiers, issue
> and cron references, and harness-configuration paths) were removed or replaced with a
> de-identified description. That is what this notice claims and the whole of it: some
> references to those artifacts survive deliberately in de-identified form where the
> surrounding contract needs them, no class is certified exhaustively absent, and a
> residual is a defect to report rather than a contradiction of this notice. The per-file
> sign-off, recorded with the full list of link dispositions in this repository's Step 66
> decision record, is the only class-level authority.

This file is the routing web: the rails an operator fragment can land on (entry
condition + skill chain), the re-route edges between them, the re-route contract, and the
catalog skills that are deliberately not vent targets.
It is the ONE owner of the rails and of the `re-route:` line format — `/user-gateway` consults this web to route intake fragments, and rail
skills cite this section; no skill hardcodes its own routing table.

---

## The rails

Entry condition = what the operator's fragment sounds like. Every catalog skill is either
named in this table or listed under § Not vent targets, never both
(`tests/package-integrity/test_routing_web_coverage.py` checks it).

| Rail | Sounds like | Chain |
|---|---|---|
| **bug** | "X is broken / erroring / behaving wrong" — a symptom in hand | `/user-debug --symptom '...'` |
| **do** | "just do X" — a small concrete task | `/user-pm` (its board routes the task by `user-build-route`'s rules) |
| **plan** | "add / build capability X" — multi-step work needing steps + review | `/plan-feature` (or `/plan-init` for a brand-new project) → `/plan-expedite` → `/build-phase` → `/repo-update` (the build rail — detail below) |
| **investigate** | "what's true about X? why does X happen?" — a question, not yet work | `/deep-research` via `Workflow({name: "deep-research-pinned"})` (never the built-in name — CLAUDE.md's dispatch rule) for external/multi-source; an Explore-agent sweep for codebase-local questions |
| **verify** | "does X actually work? / I don't trust X" — distrust without a reproducible symptom | `/review-uat` (refine a fuzzy block) / `/user-uat` (mechanical tier) / `/user-walkthrough --shakedown` (autonomous closure) / `/user-walkthrough` (attended) — four-mode detail below |
| **trim** | "the plan feels bloated / what can we cut" — plan-borne cruft-smell | `/plan-merge --trim` (plan documents only; non-plan cruft-smell routes **investigate** first — assess, then `investigate→plan` or `investigate→do`) |
| **decide** | "should we do A or B?" — an operator-only choice | never decided for the operator: parked with the open question stated, and recorded with `/user-dr` (decision register: records, groups, checks conflicts); a complex scope or first-milestone choice → `/user-fermize` |
| **draft** | "here are rough thoughts" — wants a usable prompt or goal, not work done | `/user-draft` → `/goal` |
| **review** | "look this over / is this change OK / review PR #N" — judge a change before it lands | `/review-gauntlet` (default) / `/review-deep` (high stakes) / `/code-consigliere` (understand a project's workflows and agree a change before building) / `/review-proof` (an answer's claims need primary sources) |
| **research** | "what should we research? / are this doc's claims backed?" — pick topics or check evidence, not answer a question | `/research-prospect` (topics per project); LLM-facing artifact rigor: `/citation-review` (one artifact) or `/citation-sweep` (project-wide) → `/citation-triage` → `/citation-distill` |
| **tend** | "context feels bloated / tests are slow / we keep repeating mistakes / this skill misbehaves" — workspace care | context bloat → `/context-slim` (Claude host); slow or redundant tests → `/test-prune`; repeated mistakes → `/lesson-harvest`; messy memory → `/memory-distill`; a skill misbehaving → `/skill-iterate` (variants: `/skill-evolve`; no evals yet: `/skill-eval-setup`); model cost or weakness → `/tier-offload` / `/tier-escalate`; milestone cleanup → `/user-afterparty`; close out a repo → `/repo-wrap` (detail below) |
| **session** | "I'm back / keep going or close? / wrap up / where does this stand?" — the window or the project's state, not new work | `/user-wrap`; resume a saved task → `/task-handoff --resume`; "where does this project stand?" → `/user-pm` |
| **learn** | "teach me X / I want to learn X / let's explore an idea" — understanding, not delivery | `/user-learn` (a hands-on learning ramp); explore an idea → `/user-brainstorm` |

**Tiebreak:** when a fragment plausibly fits two rails, pick the rail with the cheaper
commitment and let a re-route edge correct it. The common tie — **bug vs verify** — splits
on evidence: a reproducible symptom in hand → **bug**; distrust without one → **verify**
(and `verify→bug` upgrades it the moment a check fails).
**review vs verify** splits on the object: a change or diff not yet accepted → **review**;
a built feature's behavior → **verify**.
**research vs investigate** splits on the ask: a question to answer → **investigate**;
choosing what to study, or checking an artifact's cited claims → **research**.

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

A seed handed off this way is paste-ready text for the window that will run it; the skill
that emits it stops after rendering and executes no work.

---

## The build rail (plan) in detail

First-time setup: `/repo-init` once before first `/plan-expedite`.

```
[dev-root] /plan-init  or  /plan-feature   Plan: produce plan.md with build steps (planning is dev-root-fine — plan from anywhere)
        │                           └─ [dev-root] /plan-redline (after /plan-review --autofix, before /plan-wrap; never auto-run by plan-init; on-request after plan-feature/plan-merge): operator-facing proposal file at `docs/plan-redline/<plan-slug>-proposal.html` — P/D decision inventory, ID-referenced feedback folded back into the plan BEFORE issues are minted
        ▼
··· plan→repo context switch ··· /plan-expedite ANNOUNCES + PINS it here (between plan-wrap and repo-sync): plan-review/plan-wrap are dev-root-fine plan-doc ops; repo-sync onward targets the project repo
[dev-root → project] /plan-expedite   Autonomous prep: chains plan-review --autofix → plan-redline --local-only → plan-wrap --autofix → repo-sync → task-handoff --next-task as one unattended pre-flight before /build-phase (--new-window: durable task-handoff --next-task write, then /session-wrap --end renders handoff-prompt.md + the Pick-up-here block)
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

`/build-queue --queue <path>` — meta-orchestrator: drains a queue of N pending plans, invokes `/plan-expedite` + `/build-phase` per item, parks halts as GitHub issues (does not retry), polls a kill-switch file between items, emits a morning summary.

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
- `/user-pm` — the **status door** for one project: live verified and not-yet-verified
  status, a board with one route per item, readiness, lanes, and the plan+git-derived
  shipped / planned / next / cuttable snapshot. It absorbed the retired orientation
  skill's view; that skill's thread-only `--quick` recap was dropped (pick up a saved task with
  `/task-handoff --resume`).
- `/user-debug` (formerly `/bug-fix`) and `/memory-distill` (formerly `/review-memories`) renamed this phase.

---

## Post-build operator acceptance (verify rail detail)

Four modes: `/user-uat` EXECUTES an already-clear UAT block; `/review-uat` REFINES a fuzzy one; `/user-walkthrough` lets the operator DRIVE exploration of a just-built feature (agent answers from source, fixes small, logs big, marks coverage); `/user-walkthrough --shakedown` AUTONOMOUSLY CLOSES the shared UAT ledger to zero open items (designed to run armed under `/goal`). The walkthrough's two modes share one ledger contract: `shakedown-engine.md`.

Visual tier: `/user-uat --ui` delegates single-frame screen states to `/judge-ui`. Transition-shaped steps (route change, modal open/close, loading-to-content swap, hover/focus animation) stay manual-check steps in `Needs you`; motion checks live in each project's own skills.

---

## Tend rail detail

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
`/plan-merge --trim` one at a time (yielding at each gate), and owns two orphans with no other home —
orphan-`worktree_*` cleanup and the derived-`current.md` rollup commit/archive seam. Flags:
`--only` / `--skip` / `--dry-run` / `--all-projects`.

`/skill-evolve --skill <name> --variants <path-or-inline>` — A/B-tests N variant mutations of a skill in parallel worktrees, scored against the skill's existing `evals/` suite. Winner branch is pushed and a `gh pr create` command is printed (no auto-PR); losers are cleaned up and analyzed under `docs/investigations/skill-evolve/`. Requires `/skill-eval-setup` to have set up the target skill's evals first.

---

## dev-observatory hooks

dev-observatory hooks (additive, degradable — the control plane works on best-guess without them): `/plan-init` registers a new owned project (`observatory register`); `/repo-update` refreshes verbs/ports + tasks (`observatory sync`); `/build-step --ui` port pre-flight (`observatory ports`); `/user-pm` gains a `--json` mode; `/plan-review` + `/plan-wrap` check a scrapable goal + port collisions. Full contract: `descriptor-contract.md`.

---

## Not vent targets

Catalog skills an operator vent never lands on directly: each is a chain member a rail
skill invokes, a session utility, or a reference. A fragment about one routes to the rail
that owns it.

| Skill | Why not a vent target |
|---|---|
| `build-step` | plan rail chain (build-phase runs it) |
| `build-queue` | plan rail chain, unattended batches |
| `plan-review` | plan rail chain (plan-expedite) |
| `plan-redline` | plan rail chain (plan-expedite) |
| `plan-wrap` | plan rail chain (plan-expedite) |
| `repo-init` | plan rail chain, first-time setup |
| `repo-sync` | plan rail chain (plan-expedite) |
| `judge-ui` | verify rail chain (user-uat --ui) |
| `user-build-route` | do rail chain (user-pm routes) |
| `session-wrap` | session rail chain (user-wrap delegates) |
| `user-project` | session setup, not work |
| `user-gateway` | the vent door itself |
| `claude-oauth-auth` | reference doc |

**Host commands, not catalog skills:** `/goal`, `/deep-research` — named in the rail table,
owned by the host.
