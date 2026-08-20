<!-- Salvaged from a session scratchpad at the Phase CP pass-3 wrap (2026-08-20).
     Machine-specific absolute paths were generalized to <coding-root>/, <repo>/ and <home>/
     on the way in; this is a public repository. -->

# Re-resolved utility hookup map (Phase CP Step 11 pre-planning)

**Status: reference only. This is NOT a skill-mesh work item.** Phase CP Step 11 was DROPPED
on 2026-08-20 and the work re-owned by `<coding-root>/documentation/utility-hookup-plan.md`
Steps 6-23, whose decision D12 already assigned those edits. This document is kept here
because `documentation/parity-deltas.md` cites its conclusions, and because re-deriving the
per-skill anchors would otherwise cost the next executor the same work twice.

The summary conclusions -- the 11 ratified skills, the two moments with no live anchor, the
two soft spots needing a plan decision, and the sizing flag -- are recorded in
`documentation/parity-deltas.md` and are the authoritative short form. What follows is the
detail behind them.

---

# Phase CP Steps 11 & 12 — pre-planning investigation

Read-only. Nothing was modified. No tests were run.
Produced 2026-08-20.

Sources read:
- `<coding-root>/docs/investigations/utility-hookup/README.md` (the map — §3 is authoritative)
- `<repo>/skills/<name>/core.md` (12 live canonical cores)
- `<coding-root>/dev-observatory/plans/utility-project-surfaces-plan.md`
- `<coding-root>/dev-observatory/src/dev_observatory/{model,registry,view_sources,snapshot,templates}.py`
- `<coding-root>/.claude/observatory/registry.toml`

---

# Question 1 — Re-resolved hookup map onto canonical cores

## 1.1 The ratified skill count: **11**, and the prior analysis is CORRECT

The "11" figure is confirmed, and it is not the same 11 that the map's §3 scope note
implies. Two different countings both land on 11 by coincidence — worth being explicit
so the plan does not inherit the wrong one.

**Where 11 actually comes from.** §5 "Coding-root skill edits (the build plan this README
seeds)" fixes the first-wave scope verbatim:

> heads-up 1-3 (+4-5 second wave), tripwire 1-3 (+4), same-page 1-3, changed-check 1-3,
> paper-trail 1-3, find-again 1-3, mesh-lens 1.

Resolving those moments to landing skills yields exactly 11 distinct skills:

| # | Skill | Utilities landing here |
|---|---|---|
| 1 | `plan-expedite` | heads-up m1, tripwire m1, same-page m3, changed-check m2 |
| 2 | `build-phase` | heads-up m2, tripwire m2 |
| 3 | `build-step` | changed-check m1 |
| 4 | `session-wrap` | heads-up m3 (4 legs), tripwire m3, same-page m2, changed-check m3, paper-trail m2, mesh-lens m1 |
| 5 | `repo-update` | same-page m1, paper-trail m3 |
| 6 | `plan-redline` | paper-trail m1 |
| 7 | `plan-feature` | find-again m1 |
| 8 | `plan-review` | find-again m1 |
| 9 | `user-debug` | find-again m2 |
| 10 | `lesson-harvest` | find-again m3 |
| 11 | `memory-distill` | find-again m3 |

**The near-miss counting to avoid.** The §3 scope note and Open Decision 11 describe the
scope as "the 5 pipeline cores + six out-of-5-core skills" = 11 — but that arithmetic only
works because it counts `lesson-harvest/memory-distill` as ONE entry, and it includes
`repo-sync` (one of the 5 named cores) which has **zero first-wave moments**. Every
repo-sync moment in the map is second-wave, deferred, or "additive candidate":
heads-up m4, same-page m4 (explicitly "deferred, filed not built"), changed-check m4.

So: **11 ratified skills, and `repo-sync` is not one of them.** The total distinct skill
name count across *all* §3 moments including second-wave is **12** (the 11 above plus
`repo-sync`).

`dev-observatory` (mesh-lens m2) is a registry/dashboard action, not a skill core —
correctly excluded from the count.

## 1.2 Core existence

All 12 candidate cores exist under `<repo>/skills/<name>/core.md`.
**11 / 11 ratified skills have a live canonical core.** No row is blocked on a missing file.

| Core | Lines |
|---|---|
| `plan-expedite/core.md` | 256 |
| `build-phase/core.md` | 1014 |
| `build-step/core.md` | 955 |
| `session-wrap/core.md` | 579 |
| `repo-update/core.md` | 438 |
| `plan-redline/core.md` | **35** |
| `plan-feature/core.md` | 371 |
| `plan-review/core.md` | 624 |
| `user-debug/core.md` | 426 |
| `lesson-harvest/core.md` | 200 |
| `memory-distill/core.md` | 247 |
| `repo-sync/core.md` (2nd wave only) | 748 |

## 1.3 Anchor drift, in general

The legacy `.claude/skills-gpt/<skill>/SKILL-core.md` line anchors are stale as paths but
mostly **still accurate as positions** — the content was ported near-verbatim into
skill-mesh. Measured drift, live vs the map's legacy line numbers:

- `plan-expedite` — **zero drift.** Stale-plan check :55, resume detection :63, sub-skill
  chain :94, repo-sync invocation :133, Limitations :252. Every legacy anchor is the live
  line.
- `repo-sync` — **zero drift** at Step 0 (:161).
- `session-wrap` — **~1-line offset** (Decisions log legacy :443 → live 442; invariants
  legacy :459 → live 458). Docs-staleness bullet is live at 162, exactly as cited.
- `repo-update` — small shift; the `[drift]` block moved from a standalone :151-171 window
  into the body of `### Step 5a — plan-wrap on the plan doc`.
- `build-phase` — **real drift** (~+8 at Step 1, ~+37 at the Step 0 table, ~+37 at Step 4).
- `build-step` — **large drift** (+112 at the dev-observatory hook: legacy :835-843 → live
  947-955).
- `plan-redline` — **structurally rewritten.** The legacy core the map measured no longer
  exists in that shape; the live core is a 35-line compressed contract.

Consequence for the plan: anchor every edit by **heading + numbered item**, never by line.

## 1.4 The re-resolved map — first wave (21 landings, 11 skills)

`Live anchor` is a heading + item, deliberately not a line number.

### heads-up

| # | Skill | Moment (map's words) | Core exists | Live anchor | Verdict |
|---|---|---|---|---|---|
| 1 | `plan-expedite` | "pre-flight CHECK — insert after resume detection, before :94, mirroring the stale-plan warn-continue template" | yes | `## Flow` → end of `### Resume detection`, immediately before `### Sub-skill chain`; warn-continue template to mirror is `### Stale-plan check (per BPA plan section 5 D9)` | **Unambiguous.** Both headings live, same order, zero line drift. Note ratified Open Decision 10 = (a) CLAIM, not check-only. |
| 2 | `build-phase` | "Step 1 pre-flight CLAIM + all-exit-path RELEASE — claim alongside 'verify git is clean'; release threaded through every halt-contract exit and Step 4 report" | yes | CLAIM: `### Step 1 -- Pre-flight` item 4 ("Verify git is clean (or stash)"). RELEASE: `## Halt contract` (its 5 classes) + `### Step 4 -- Report` | **Unambiguous.** |
| 3 | `session-wrap` | four legs: "(a) Step 0 triage fifth signal; (b) Git-verb router Step A check-1 upgrade; (c) RELEASE sweep after the git verb; (d) `--advise` loss-report line" | yes | (a) `## Step 0 — triage: collect, score, announce` → the "**Announce, then act.**" `triage:` line. (b) `## Git-verb router` → `**Step A — anomaly pre-flight**` → check `# 1. Foreign state file at the workspace root` (the literal `.plan-expedite-state.*` `Get-ChildItem` scan) and its trigger test "1. **Foreign state file**". (c) `## Route: clear-next` step 5 "Execute the git verb" (inherited by `## Route: end-window`). (d) `## --advise — verdict + loss report` → the `Dies with this window:` line | **Unambiguous, all four.** Leg (b)'s replacement target is present verbatim. |

### tripwire

| # | Skill | Moment | Core exists | Live anchor | Verdict |
|---|---|---|---|---|---|
| 4 | `plan-expedite` | "pre-flight — same insertion region as heads-up moment 1 … one shared pre-flight block should host both calls" | yes | Same anchor as row 1 | **Unambiguous.** |
| 5 | `build-phase` | "Step 1 pre-flight (the arm said 'Step 0' — wrong anchor) … include `TW-WTR-002`" | yes | `### Step 1 -- Pre-flight` | **Unambiguous.** The map's own correction holds against the live core: `### Step 0 -- Parse plan` really is the parse/always-print-table step (the five always-print checks + "All five checks always print"), and Step 1 really is the pre-flight. |
| 6 | `session-wrap` | "fold `[tripwire: <rule_id> <sev>]` into the existing per-repo git signal in Step 0 triage" | yes | `## Step 0 — triage: collect, score, announce` → the `git: <n dirty, m ahead[, per-repo]>` segment of the announce line | **Unambiguous.** |

### same-page

| # | Skill | Moment | Core exists | Live anchor | Verdict |
|---|---|---|---|---|---|
| 7 | `repo-update` | "`[drift]` block fold-in (highest value) — insert after :167: the block already hand-greps for exactly this drift class; same-page becomes its mechanical backend" | yes | `## Step 5 — Run drift checks` → `### Step 5a — plan-wrap on the plan doc` → the paragraph "**`[drift]` spec↔code check (advisory — NEVER blocks the push, INV-1).**"; insert after its third bullet (the grep-CURRENT-STATE-docs bullet), before the closing "These are one more advisory input…" paragraph. Severity ceiling is live verbatim: "`[drift]` findings are Gap/Minor only, never Blocker." | **Unambiguous**, with one structural note: the `[drift]` check is now explicitly "folded into this same plan-wrap pass (not a standalone sub-step)", so it is a block inside Step 5a, not the standalone :151-171 window the map measured. |
| 8 | `session-wrap` | "Docs-staleness bullet gets a mechanical pre-check per touched repo (touched-repo loop already exists)" | yes | `## Route: end-window` → the "**Docs staleness.**" bullet | **Unambiguous for the bullet.** The "touched-repo loop" sub-anchor is the one soft spot: there is no standalone loop; the live equivalent is the Git-verb router's scoping sentence "Multi-project sessions run Steps A-C independently PER TOUCHED REPO". Adjacent legs cited by pipeline-moments are both live and unambiguous: `## The six behavioral invariants` (invariant #2's SHA anchor) and `## --advise` → "un-checkpointed or git-inconsistent `current.md` state". |
| 9 | `plan-expedite` | "pre-repo-sync — immediately before the repo-sync invocation (:133); one narration line, existing style" | yes | `### Sub-skill chain` → numbered item **3. "Invoke `repo-sync` through the host's skill-invocation adapter"** — live at line 133, identical to the legacy anchor | **Unambiguous.** |

### changed-check

| # | Skill | Moment | Core exists | Live anchor | Verdict |
|---|---|---|---|---|---|
| 10 | `build-step` | "quality-gate dispatch (highest value, effort M) — between developer diff and reviewer dispatch … print the narrowed set as a suggestion alongside, never replacing, the full gate" | yes | Between `### Step 3 -- Capture diff` and `### Step 6 -- Spawn reviewer agents`; concretely at `### Step 4 -- Run automated gates`, alongside the always-run typecheck/lint/test block | **Unambiguous.** The "never replacing" constraint is load-bearing here: Step 4's `*_RC` exit-code contract is what halt-class #2 reads. |
| 11 | `plan-expedite` | "pre-flight informational line (S) — same call, once per phase, in the existing pre-flight summary" | yes | Same shared pre-flight block as rows 1/4 | **Unambiguous.** |
| 12 | `session-wrap` | "end-window staged-changes advisory (S) — `--staged`, scoped to the pinned project" | yes | Two plausible hosts: `## Route: end-window` route body, or `## Git-verb router` → **Step C additive recommendation** | **AMBIGUOUS (mild).** The map gave no legacy line for this leg. Step C is the better fit (it is already the "additive recommendation" surface), but the plan should decide explicitly rather than leave it to the build agent. |
| — | `repo-sync` | m4 Flags enrichment — *second wave, see §1.5* | yes | — | — |

### paper-trail

| # | Skill | Moment | Core exists | Live anchor | Verdict |
|---|---|---|---|---|---|
| 13 | `plan-redline` | "fold-back (highest value, S) — after folding operator P/D replies, emit (not run) a templated `paper-trail add ...` suggested command for each P-item passing the qualifying threshold" | yes | `## Procedure` → numbered item **7** ("On feedback, … apply the smallest plan edits; update inventory status; … report one line per applied change") | **Unambiguous as a position**, but flag loudly for the plan: this core was **rewritten and compressed to 35 lines** since the map was measured. The legacy fold-back prose the map budgeted an S-effort edit against no longer exists in that form. Re-read before sizing. |
| 14 | `session-wrap` | m2, two legs (Open Decision 4 = suggested-command only): stale-review advisory on end-window + the Decisions log leg | yes | Decisions-log leg: `## Decisions log + salvage sweep (clear-next + end-window)` → item **1. "Decisions log."** (which already enumerates decisions *and* rejected alternatives — the content constraint is satisfied at that exact point). Stale-review leg: `## Route: end-window` | **Unambiguous.** |
| 15 | `repo-update` | "pre-commit audit-and-warn (S) — `paper-trail audit --root <resolved-root>`; exit 1 → 'decision-graph integrity warning', never fails the commit" | yes | Immediately before `## Step 9 — Commit` (i.e. after `## Step 8 — Update memory`); Step 9 already carries the wrong-directory advisory-never-blocks precedent to mirror | **Unambiguous.** |

### find-again

| # | Skill | Moment | Core exists | Live anchor | Verdict |
|---|---|---|---|---|---|
| 16 | `plan-feature` | m1 "pre-draft 'existing context' search — mechanizes `plan-and-issue-flow.md § Read producers before drafting`" | yes | `## Before the conversation — auto-discovery` → append as item 8 after item 7 ("Memory — check project memory files"); surfaces in `### Phase 1 — Existing landscape` | **Unambiguous.** The live section is literally the read-producers-first moment, item 1 of it cites the same rule. |
| 17 | `plan-review` | m1, same moment, shared with plan-feature | yes | No pre-draft moment exists. Closest live candidates: `### 17. Feature plan — existing-code validation` or `### 20. Feature plan — context sufficiency` | **AMBIGUOUS — no clear live equivalent.** plan-review reviews an *already-drafted* plan; a "pre-draft existing-context search" has no home in its 27-check structure. The map itself warned these find-again moments "have no pipeline-moments anchors and need their own insertion-point verification at build time". This is the row that needs a decision, not a re-anchor. |
| 18 | `user-debug` | m2 "symptom intake — same shape, `--type incident --type memory`, before reproduction; pointer only" | yes | `### Step 0 — Pre-flight & memory citation` → item **2. "Cite relevant memory"** (already reads MEMORY.md + all `project_*.md` before Step 1, with an explicit "Do not defer this scan into Step 1") | **Unambiguous — the cleanest anchor in the whole map.** The step is already a keyword-and-path-driven retrieval pass; find-again mechanizes it in place. |
| 19 | `lesson-harvest` | m3 "duplicate check (S-M) — mechanizes knowledge-placement.md's 'grep for an existing owner before adding'" | yes | `## Phase 3 — Dedup against ALL FIVE codification stores (the load-bearing fix)` — the five-store search loop | **Unambiguous.** Near-perfect fit; find-again becomes the mechanical backend for stores 1-2 and 5. |
| 20 | `memory-distill` | m3, same moment, shared with lesson-harvest | yes | No dedup phase exists. Closest live candidates: `### Step 2.5 — Lineup theme scan (before any per-round work)`, `#### 3. Recent evidence` inside a round, or `### Step 4 — Look for latent principles` | **AMBIGUOUS — no clear live equivalent.** memory-distill reviews *existing* memories one at a time; it has no add-a-new-entry moment where "grep for an existing owner" would fire. Decide or drop. |

### mesh-lens

| # | Skill | Moment | Core exists | Live anchor | Verdict |
|---|---|---|---|---|---|
| 21 | `session-wrap` | m1 "end-window — `mesh-lens ingest` + `report`, one informational line; exceptions downgrade to 'skipped (error)'. Single owner on purpose: the store is single-writer" | yes | `## Route: end-window` — among "these passes inserted after step 3 (before the render, so their outcomes are renderable)" | **Unambiguous.** |

## 1.5 Second wave / deferred (not first-wave scope)

| Utility | Moment | Skill | Core exists | Live anchor | Verdict |
|---|---|---|---|---|---|
| heads-up | m4 "repo-sync Step 0 claim — closes the one genuinely check-free gap … the Step 6 `gh issue` mutation loop has no parallel-session protection of any kind" | `repo-sync` | yes | `### Step 0 — Pre-flight: resolve and verify target repo` (live at 161 — zero drift); the unprotected loop is `### Step 6 — Execute (one tool call per gh action)` | Unambiguous |
| heads-up | m5 "build-step Step 1 claim / Step 5.5 corroborating check / Step 8 release … a conflict at Step 5.5 folds into the existing `SHIP_GATE_HALT` message" | `build-step` | yes | `### Step 1 -- Create isolated environment`; `### Step 5.5 -- Ship-gate re-check (canonical)`; `### Step 8 -- On PASS`. `SHIP_GATE_HALT` is live (sentinel, exit-code contract, verdict row, and `halt` field) | Unambiguous |
| tripwire | m4 "build-step Step 1 worktree creation … optionally re-host the hand-coded reviewer-hazards warning" | `build-step` | yes | `### Step 1 -- Create isolated environment` → `#### Worktree (default)`; the re-host target is `### Step 0 -- Pre-flight` item **6. "Reviewer hazards"** (live verbatim, incl. the Toybox K17 provenance) | Unambiguous |
| same-page | m4 "repo-sync Step 3.1 parser replacement … refactor-class" (explicitly *deferred, filed not built*) | `repo-sync` | yes | `#### 3.1 — Cross-plan collision check` | Unambiguous |
| changed-check | m4 "repo-sync Step 8 Flags enrichment … additive candidate" | `repo-sync` | yes | `### Flags (recommended)` in the step body template, plus `### Step 8 — Report` | Unambiguous |
| mesh-lens | m3 plan-expedite / build-phase post-run summary — **DEFERRED** until Phase 8 Step 60 | `plan-expedite`, `build-phase` | yes | n/a — deferred | n/a |
| mesh-lens | m2 dashboard `compare` verb | *not a skill* — `.claude/observatory/registry.toml` | n/a | n/a | Observatory work, not a core edit |

## 1.6 Scorecard

- **Ratified skills: 11.**
- **Live canonical core exists: 11 / 11.**
- **Every assigned moment lands on an unambiguous live anchor: 9 / 11.**
  Failures: `plan-review` (find-again m1) and `memory-distill` (find-again m3) — in both
  cases the legacy moment has **no clear live equivalent**, because neither skill has a
  pre-draft / pre-add moment at all. Both are find-again moments, which the map itself
  flagged as the ones lacking pipeline-moments anchors.
- **Soft spots that need a plan decision rather than a re-anchor (2):**
  changed-check m3 on `session-wrap` (end-window route body vs Git-verb router Step C);
  same-page m2's "touched-repo loop" sub-anchor (now the router's per-repo scoping
  sentence, not a loop).
- **Re-size before building (1):** `plan-redline` is now a 35-line compressed core — the
  legacy prose the S-effort estimate was measured against is gone.

---

# Question 2 — Does the observatory already own utility visibility?

## 2.1 What the plan covers, and its status

`<coding-root>/dev-observatory/plans/utility-project-surfaces-plan.md`
Header: **`Status: IN PROGRESS (reconciled 2026-08-12)`**. Steps 32-43.

Its own scope statement (§1): "Adds three reusable, project-customizable web surfaces to
dev-observatory: a two-level list/detail explorer, an at-a-glance activity page, and a
**transparency page showing purpose, mechanical callers, health, and recent evidence**."

Its own boundary, stated in §2: "`documentation/utility-hookup-plan.md` owns actual
pipeline wiring." And §3 **Out:** "duplicating project business logic, **claiming a tool
is wired before a caller exists**."

Per-step Status markers:

| Step | Title | Status |
|---|---|---|
| 32 | Add typed view and evidence contracts | `DONE (2026-08-08)` |
| 33 | Build bounded artifact loading and generic derivation | `DONE (2026-08-12; … Snapshot v8 …)` |
| 34 | Render shared summary, explorer, and transparency pages | `DONE (2026-08-09; served/static parity …)` |
| 35 | Migrate and harden utility launch semantics | `DONE (2026-08-12; launch hardening focused gates green …)` |
| 36 | Activate source-free UAT surfaces | `DONE (2026-08-12; 18 pages configured …)` |
| 37 | Finish utility-hookup evidence | **`BLOCKED ON UTILITY-HOOKUP STEP 4 (2026-08-13; … current evidence is 5 wired / 8 unwired)`** |
| 38 | Integrate on-brand rich surfaces | `DONE (2026-08-12; 14 real items, 9 specimens …)` |
| 39 | Repair and integrate switchboard rich surfaces | *(no Status marker)* |
| 40 | Clear and integrate citation-needed | *(no Status marker)* |
| 41 | Integrate deferred producers independently | *(no Status marker)* |
| 42 | Real-workspace UAT checkpoints | `CHECKPOINT ONE OPERATOR PASS (2026-08-12; final 13/13 … pending Steps 37-41)` |
| 43 | Integrate On Brand inspiration-to-implementation explorer | `READY (2026-08-13; On Brand producer Steps 23-27 are DONE …)` |

**6 DONE / 6 not-DONE.** The visibility *machinery* (32, 33, 34, 36) is entirely in the
DONE half. The not-DONE half is content integration for specific producers — plus
Step 37, which is blocked waiting for the hookup work itself.

## 2.2 Yes — the mechanism already exists, is built, and is already populated

**Mechanism: registry-declared literal wiring locators, resolved at snapshot scan time
into `wired` / `referenced` / `unwired` evidence, rendered on a per-project transparency
page.** Not a hookups table authored by hand, and explicitly **not** scrape-derivation
from skill cores.

Contract (§5, `New Components`):

> `WiringLocator`: a route-safe ID, explicit `caller`/`consumer`/`declaration` role, label,
> workspace-relative path, and literal text pattern. At most three representative locators
> are accepted per project… The snapshot resolves the current line and captures at most two
> bounded context lines on either side instead of storing a drifting line number.
> `WiringEvidence` is `wired` only for a found caller/consumer, `referenced` only for a
> found declaration, and `unwired` when proof is absent.

And §6.4: "A prose reference is labeled `referenced`; only a mechanically verified caller
is `wired`."

**It is implemented, not just planned.** Verified in source:

- `src/dev_observatory/model.py` — `class WiringLocator` (:159), `class WiringEvidence`
  (:179, docstring "One scan-time transparency result for a declared `WiringLocator`"),
  and `Project.wiring` / `Project.wiring_evidence` (:239-240).
- `src/dev_observatory/registry.py` — `_parse_wiring()` (:383). Parses `wiring = [...]`
  rows with a closed key set `{id, role, label, path, pattern}`, enforces route-safe IDs,
  rejects duplicate IDs, rejects sensitive paths / `.env*` files, caps at 3 locators,
  and drops bad rows with a warning rather than failing.
- `src/dev_observatory/view_sources.py` — `resolve_wiring_evidence()` (:1093). Reads the
  file bounded, then matches per line with **`if locator.pattern in line`** — a **literal
  substring match on a single line**. Missing file / unreadable / absent literal all
  produce `unwired` evidence with the declaration preserved, "so a transparency page can
  say that no current mechanical proof was found rather than silently implying a working
  link."
- `src/dev_observatory/snapshot.py` (:259) calls it per project; `templates.py`
  (:1278-1284, :1581-1584) renders the rows and the wired/referenced/unwired tally;
  `render_static.py` (:142, :162, :239) does the static-output half.

**All seven portfolio utilities already have their locator declared** in
`<coding-root>/.claude/observatory/registry.toml` (13 projects carry a `wiring` block;
these are the seven that matter here):

| Utility | Declared caller path | Literal pattern | Label |
|---|---|---|---|
| tripwire | `.claude/skills/plan-expedite/core.md` | `tripwire check --root` | "Planned plan-expedite preflight" |
| heads-up | `.claude/skills/plan-expedite/core.md` | `heads-up claim` | "Planned plan-expedite claim caller" |
| same-page | `.claude/skills/repo-update/core.md` | `same-page check` | "Planned repo-update drift check" |
| paper-trail | `.claude/skills/repo-update/core.md` | `paper-trail --root` | "Planned repo-update decision audit" |
| changed-check | `.claude/skills/build-step/core.md` | `changed-check plan --root` | "Planned build-step advisory" |
| find-again | `.claude/skills/plan-feature/core.md` | `find-again --root` | "Planned find-again retrieval advisory" |
| mesh-lens | `.claude/skills/session-wrap/core.md` | `mesh-lens` | "Planned session-wrap telemetry caller" |

Every label reads "**Planned** …" — these are pre-declared, currently resolving `unwired`,
exactly as Step 37 reports (5 wired / 8 unwired across all 13 utility-category projects;
the 5 wired are the already-wired ones — goblin, dev-observatory, switchboard, on-brand,
citation-needed).

Step 37's Done-when includes, verbatim: "**the seven hookup locators resolve `wired`**."

## 2.3 Overlap with what Step 12 intended

Phase CP Step 12's brief was to determine the visibility mechanism from scratch by reading
`.claude/observatory/registry.toml` and `dev_observatory/{view_sources,registry,model}`.
Those are precisely the four artifacts this plan already owns and has already changed
(§4 Impact Analysis lists all four: registry.toml modify, registry.py extend "parse
optional project views and wiring locators", model.py extend "typed view/action and
evidence shapes", view_sources.py new "bounded artifact reads and strict JSON decoding").

**Overlap: total. Conflict: none.** The two plans have a clean, explicitly-declared seam —
the observatory plan owns the *surface* and refuses to claim `wired` without a caller; the
hookup plan owns the *caller*. Appendix D6 of the observatory plan states the division as
a decision: "Reuse utility-hookup-plan as the owner of mechanical invocation proof."

## 2.4 Does Step 12 reduce to confirmation rather than design? — **YES**

Evidence, in order of weight:

1. The mechanism is **specified** (§5 `WiringLocator` / `WiringEvidence`), **built** (four
   modules, all four Steps 32-34/36 marked DONE), and **populated** (all seven locators
   already declared in the registry).
2. Step 37 already *is* Phase CP Step 12's deliverable, phrased from the other side:
   "the seven hookup locators resolve `wired`". It is blocked on the hookup work landing,
   not on any observatory design.
3. Nothing needs authoring. Once a Step-11 core edit lands a call, the next snapshot scan
   flips that locator to `wired` with no observatory change at all.

**The one thing that is not pure confirmation** — a real finding, not a design task:
`resolve_wiring_evidence` matches a **literal substring on one line**, and three of the
seven declared patterns will not match the call shapes §4 of the map ratifies:

| Utility | Declared pattern | Ratified call shape (README §3/§4) | Matches? |
|---|---|---|---|
| tripwire | `tripwire check --root` | `… tripwire check --root <path> --json` | **yes** |
| heads-up | `heads-up claim` | `… heads-up <verb> --resource-kind …` (verb = `claim`) | **yes** |
| same-page | `same-page check` | `same-page check --root <repo> --format json` | **yes** |
| mesh-lens | `mesh-lens` | `mesh-lens ingest` / `report` | **yes** |
| paper-trail | `paper-trail --root` | `… paper-trail <verb> --root <path>` → e.g. `paper-trail audit --root …` | **NO** — verb sits between the two tokens |
| changed-check | `changed-check plan --root` | `uv run changed-check plan --combined --json`, **cwd-based, no `--root` at all** | **NO** |
| find-again | `find-again --root` | `… find-again search "<topic>" --root <home>/dev …` | **NO** — verb + query sit between |

Also worth carrying into the plan: the locator `path` values point at the **installed
coding-root tree** `.claude/skills/<name>/core.md` (all three checked exist), **not** at
skill-mesh's canonical `skills/<name>/core.md`. Ratification Decision 12 puts the edits on
the canonical cores, so the locators will only resolve `wired` after an install/cutover
propagates the edited core into `.claude/skills/`. That is a sequencing fact Step 12 should
state, not a defect.

So Step 12 is: **confirm the built mechanism, reconcile three literal patterns against the
ratified call shapes, and note the canonical-vs-installed path dependency.** No design.

## 2.5 Does it depend on dev-observatory Step 43? — **NO**

Step 43 is **this plan's own step**, not an external dependency, and it is unrelated to
utility wiring visibility:

> `### Step 43: Integrate On Brand inspiration-to-implementation explorer`
> `**Status:** READY (2026-08-13; On Brand producer Steps 23-27 are DONE at producer commit e998e1e …)`
> `**Depends on:** 38 and On Brand Step 27 (both DONE)`

It adds an On Brand explorer view ("append `inspiration-to-implementation` between On
Brand's `brands` and `transparency` views as a non-main explorer"). Nothing about it gates
utility transparency.

Grounding on the numbering, since Step 12's brief treated "Step 43" as possibly unbuilt:
dev-observatory uses **one continuous step sequence across sibling plans** — `plans/plan.md`
holds Steps 1-18 (it ends at "Step 18: Own the switchboard WSL relay keep-alive" plus
M1-M4 and has **no Step 43**), `portfolio-pages-plan.md` holds 19-31, and this plan holds
32-43. So "dev-observatory Step 43" resolves unambiguously to the On Brand explorer step,
status `READY`.

The dependencies that *do* bind are the reverse direction: Step 37 depends on
`documentation/utility-hookup-plan.md` **Steps 4-26** (plus Skill Mesh Step 65, both
Step 70 rehearsals, and the shared Step 26 / Step 71 cutover). The observatory is waiting
on the hookup work — not the other way round.
