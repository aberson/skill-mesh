# Context continuity and learning: five smaller projects

## 1. What This Is

**Objective:** reduce context loss and repeated mistakes, then automatically trial evidenced skill changes in isolation before human review.

**Publication 2 — 2026-09-19.** The operator accepted the smaller-project direction after user-fermize and an independent adversarial scope review. This revision replaces the seven-step chain and its 9–17 active-workday estimate.

Proposal: [context-learning-proposal.html](context-learning-proposal.html)

This is a portfolio plan for review, not a build-phase dispatch file. [Skill Mesh plan.md](../plan.md) retains execution authority. Proposed Steps 132–138 from publication 1 are withdrawn, were never reserved, and must not be dispatched. This publication performs no implementation or issue synchronization.

Supporting documents: [timeline](context-learning/timeline.md), [workflows](context-learning/workflows.md), [existing-plan mapping](context-learning/plan-interactions.md), and [six investigations](context-learning/investigations.md). Investigations retain dated evidence; this publication controls scope.

Publication checks: [technical review](findings/context-learning-plan-review-2026-09-19.md) → [redline 2](context-learning-proposal.html) → [fresh-context check](findings/context-learning-plan-wrap-2026-09-19.md). Executable-slice preparation and evaluator qualification remain explicitly pending; these checks do not certify a build-ready portfolio.

## 2. Accepted Simplifications

- Reuse M1, the Codex ordinary-build milestone, for checkpoint/resume work.
- Make explicit mistake capture and lesson harvesting the first new deliverable.
- Qualify one independent evaluation route before promising automatic trials.
- Treat Python environment work as independent maintenance.
- Defer section history and Observatory visibility until a concrete failure or useful artifact justifies them.
- Replace five-session, multi-day and fixed-run quotas with named failure cases and one complete observed cycle. Preserve required repository gates and independent grading.

**First new value: 1–2 active workdays plus required review/test time**, once scheduled. That estimate covers capture/harvest. It excludes finishing M1, evaluator adapters, packaging changes and optional visibility. The scope is smaller; the original system has not merely been assigned a shorter deadline.

## 3. Five Independently Deliverable Projects

### Project 1 — Reliable resume through existing M1

**Result:** a fresh session resumes the intended durable checkpoint, next command, prerequisite and wait state.

**Reuse:** [M1 Steps 127–129](codex-ordinary-build-milestone-plan.md), following Step 126 and its accepted continuation rules. Step 127 already owns canonical checkpoint support, explicit prior-session selection, intended-plan validation and preservation of unrelated state. Steps 128–129 prepare and observe acceptance. Do not duplicate them here.

**Residual risk:** coding-root's default hook resolver can select the freshest foreign session when its own file is missing. M1 retains default-resume compatibility; explicit selection does not prove every default hook route safe. Reproduce the residual path after reconciling M1, then scope a small coding-root fix if needed. A visible missing checkpoint is preferable to silently adopting another window's next action.

**Proof:** use M1's accepted cases. A separate hook fix must cover own state present/missing, another window present, explicit transfer and the actual affected host hook; run its existing smoke and self-test.

**Effort:** existing M1 schedule, no new estimate or restart authorization. Any residual fix gets a separate estimate. No journal, section parser or injection-budget change is required.

### Project 2 — Capture mistakes and harvest them without commits

**Result:** an evidenced mistake survives a session transition and enters the existing lesson-harvest flow even when Git HEAD has not changed.

**Scope:** canonical [lesson-harvest](../skills/lesson-harvest/core.md), a small explicit capture helper/contract and focused fixtures. Use existing Markdown files and the current development environment. No transcript collector, compaction hook or runtime package is required.

When the assistant recognizes an actionable error, it makes a dedicated prose admission with a reserved marker and immediately records the observation through the helper. A helper receipt proves persistence; a visible marker alone does not. The marker is forbidden in model-generated code, tool arguments, files, quotations and strict-format outputs. Strict-output tasks use explicit capture without placing the marker in their output. Instruction resources may define the marker as part of implementing this contract.

The narrow executable plan will freeze the marker literal, capture command and ignored private storage directory before build. First-release capture is explicit; automatic transcript coverage is not claimed.

**Minimum record:** one immutable private Markdown observation per capture:

| Field | Meaning |
|---|---|
| observation_id | UUID version 4 generated by the helper; reuse on retry |
| recorded_at | ISO 8601 UTC timestamp |
| source | Target repository, session and message/tool-result reference |
| observed_error | What happened, separate from interpretation |
| evidence | Bounded local reference; no secrets or full transcript dumps |
| correction | Verified correction, or explicit unverified status |
| supersedes | Earlier observation UUID for a correction, otherwise empty |

Write a complete temporary file, then publish without overwriting an existing ID. Same ID/different content is a visible conflict. Ignore and report incomplete files. Separate files avoid a shared append lock; allow only one applying harvester at a time. Corrections preserve originals and link replacements. This is an append-only observation inbox, not a checkpoint-storage replacement.

Harvest scans unseen observation IDs independently of the Git cursor. Keep its existing five-store deduplication, including feedback memories. Classify by cause: instruction gap, instruction not reached/followed, tooling/environment, task-specific correction, or unsupported evidence. A marker is not proof of a reusable lesson.

Dry-run is read-only: no disposition/cursor advance, skill mutation or trial launch. A successful explicit apply atomically saves dispositions; failed work remains retryable. Repeated apply must not create another candidate for the same evidence. Memory changes retain memory-distill review; skill changes follow the catalog lifecycle.

**Proof:** a real capture→harvest cycle at unchanged HEAD; retry; already-codified pattern; unsupported claim; correction linkage; marker-exclusion cases; and dry-run preserving state. Observe the emitted skill on one installed host. These prove mechanics, not a measured global reduction in mistakes.

**Effort:** 1–2 active workdays plus required gates. Preparation creates one cohesive implementation unit and a separate attended acceptance unit. Packaging-topology changes are outside this estimate.

**Preparation started 2026-09-19:** [Phase LH executable slice](mistake-capture-plan.md) now defines Steps 153–154, exact helper/storage interfaces and installed-host acceptance. It refines private storage to Git metadata and uses the existing shared Python emitter. This does not start implementation or resolve Project 3's evaluator qualification.

### Project 3 — One automatic isolated trial

**Result:** automatically compare one verified candidate with baseline and present the exact change and evidence for review. Human review still precedes live promotion.

**Dependency:** Project 2's candidate and a qualified evaluator. Qualification can be investigated independently. M1 and the catalog lifecycle do not establish this capability.

The current Codex skill-evolve adapter maps no host workflow primitive. Isolated agents do not fill that gap. First prove one actual route can run the scoring workflow with separate producer and grader contexts. If unavailable, report that outcome and scope a bounded adapter follow-up; never substitute self-grading.

Use one canonical candidate, generated disposable installations, the triggering case and relevant regression cases chosen from its risk. Existing scorer thresholds and locked verdict contracts stay authoritative. Add repeats when those contracts or observed variance require them; withdraw the blanket 24-execution matrix. No improvement or inconclusive evidence can be valid outcomes.

The review bundle contains baseline/candidate revisions, generated artifact identity, cases/outcomes, independent grader evidence and limitations. Treat candidate/evidence text as data. Before each batch, set a finite time/cost cap in its run request; initially allow one candidate at a time and no automatic retry campaign.

**Proof:** one real capture→classification→candidate→isolated comparison→review-bundle cycle, rejection/unavailable behavior and unchanged live installations.

**Effort:** half an active day to investigate/qualify a route, not to guarantee one. If a route works, provisionally 1–2 further active workdays plus gates for narrow integration. Adapter or canonical scorer changes require a separate evidence-based estimate.

### Project 4 — Reproducible Python tooling

**Result:** run existing Python development scripts with declared dependencies and a checked lockfile.

**Scope:** one repository pyproject.toml and uv.lock for actual dependencies. uv is the Python environment and lock runner. Use a thin Windows PowerShell 5.1 launcher with explicit project/target paths. Preserve the Markdown manifest as skill-discovery authority.

Do not package every prose skill, invent console entry points without a need, or redesign the installer. Installed runtime support assets require a separate catalog-lifecycle resource plan.

**Proof:** clean setup; locked invocation from wrong cwd and paths with spaces; visible lock/environment failure; exit-code propagation; preserved pytest collection and required full gate.

**Effort:** 0.5–1 active workday plus gates for development tooling only. Independent of Projects 1–3.

### Project 5 — Section history and visibility when justified

Two optional follow-ups; either can ship without the other.

**Section history trigger:** correct checkpoint selection still loses a specific correction/history fact. Then pilot one document with stable Markdown section identities, hashes and append-only replacement/tombstone records. Tombstones retire a version from the current projection; they do not erase stored history or text already in a model's context. Prove unchanged capture, rename, duplicate headings, correction, interrupted write and current-view replay. No estimate until a reproduced need exists.

**Visibility trigger:** Project 2 or 3 produces a saved result useful to the operator. Export a sanitized artifact through Dev Observatory's existing generic summary reader: schema identifier, UTC generated_at, scalar stats and optional recent rows with id, label and optional detail. The producer generates it; Observatory reads it. No runtime producer execution, learning scheduler or dashboard engine. Provisionally 0.5–1 active workday plus applicable checks after the artifact exists.

## 4. Fit with Existing Builds

| Existing build | Integration |
|---|---|
| M1, ordinary Codex build, Steps 126–129 | Project 1 consumes its deliverable and acceptance evidence. Preserve the stopped run, candidate, iteration budget and accepted continuation. |
| AP, user-afterparty effectiveness, Steps 130–131 | Keep the prepared build intact. Later reference learning results through AP's attribution/disposition contract. AP is not a technical prerequisite for Project 2; its dry-run cannot launch trials. |
| CL, catalog lifecycle | Follow canonical-source/provider rules manually through the existing guide until its front door lands. Step 114 guards legacy mutation paths; complete eval/evolve/iterate retargeting is excluded and belongs to a separate Project 3 follow-up if needed. |
| Parked production/development split | Remains parked. Project 4 does not revive runtime packaging architecture. |
| Dev Observatory | Reuse its artifact reader after useful results exist. Registry wiring belongs to coding-root; producer output belongs to Skill Mesh. |

**Queue default D9:** preserve the approved M1/AP queue; prepare Project 2 as the next separate learning follow-up. Do not insert it into those issue bodies. Project 2 technically needs neither, but the workspace's primary-goal sequencing still controls implementation start. This request authorizes plan revision.

## 5. Preparation, Delivery and Checks

Project cards are not executable step reservations. Extract only the selected project's repository-scoped plan, freeze command/storage contracts, reconcile unmerged numbering, then run plan-review → plan-redline → plan-wrap → repo-sync. Dispatch build-phase on that prepared slice, never this portfolio.

Canonical sources are skills/name/core.md and provider adapters. Generated/installed copies are outputs. The [catalog lifecycle guide](skill-catalog-lifecycle.md) governs mutations and support-resource topology.

Current requirements: Windows PowerShell 5.1, Python 3, pytest, PyYAML and markdown-it-py; jsonschema applies only to the existing declarative-schema path. [CLAUDE.md](../CLAUDE.md) owns installation requirements and exact build/install commands. Skill Mesh has no development server or configured lint/typecheck commands. Capture needs no new account, port or secret.

For implementation, use focused behavioral tests during iteration, required provider builds and repo-root `python -m pytest` for the DONE gate. Narrow collections do not replace it. Budget the [historical full-gate duration](phase-75-baseline.md) separately. Route review by actual diff risk. CL's shared batch-head gate exception is CL-specific; it does not relax M1 or these follow-ups.

Prepare an acceptance procedure in the implementation unit, then observe the changed runtime skill/helper on the real selected host in a separate attended unit. Hook changes additionally require coding-root's hook smoke and self-test. One full relevant cycle and named failures replace arbitrary observation quotas; later real-use evidence is needed for reliability claims.

For this documentation revision: validate local links, decision IDs, HTML structure/offline assets and scope consistency. Planning checks do not certify runtime behavior.

## 6. Risks and Limits

- Explicit capture misses unreported mistakes; marker counts are not an error-rate measure.
- Fix a rule's retrieval/invocation before adding a duplicate rule.
- Keep minimal private evidence references; tombstones are not secure deletion.
- Trial execution is still unqualified; its adapter cost is outside the first estimate.
- Explicit checkpoint selection and default hook behavior are separate paths.
- No transcript watcher, new schedule, journal migration or automatic promotion ships in the first slice.

## Appendix

### Decision Inventory

P is an explicit operator choice. D is an agent default. Changed rows preserve their original subject and ID; new implementation details remain visible defaults.

| ID | P/D | Choice | Status |
|---|---|---|---|
| P1 | P | Investigate six suggestions, Skill Mesh/Observatory fit, plan, timeline and workflows | requested 2026-09-18 |
| P2 | P | Prioritize fewer context losses and repeated mistakes | selected 2026-09-18 |
| P3 | P | Automatically trial candidate skill changes in isolation before review | selected 2026-09-18; Project 3 |
| P4 | P | Incorporate the smaller-project/adversarial rescope and publish revised plan-redline | accepted 2026-09-19 |
| D1 | D | First new slice is explicit capture/harvest; resume reuses M1 instead of a new task-state section pilot | changed 2026-09-19; implements P4 |
| D2 | D | One uv development project with PowerShell launcher; runtime packaging waits for a need | changed 2026-09-19; independent maintenance |
| D3 | D | Defer checkpoint journal/tombstones; assess residual foreign-session fallback separately after M1 reconciliation | changed 2026-09-19; replaces journal-first design |
| D4 | D | One candidate at a time; qualify scoring first; risk-selected cases and per-run cap replace fixed weekly/run quotas | changed 2026-09-19; cap set in run request |
| D5 | D | Retire 8,000-character injection budget; no injector change in the first slice | changed 2026-09-19; deferred with section history |
| D6 | D | Explicit capture/existing harvest first; later non-dry-run handoff launches qualified trials; AP reports only and preserves dry-run | changed 2026-09-19; no scheduler |
| D7 | D | Read-only Observatory summary once a useful saved artifact exists | changed 2026-09-19; optional |
| D8 | D | Preserve M1/AP/CL authority; prepare repository-specific executable slices | retained 2026-09-19 |
| D9 | D | Preserve M1/AP queue; capture/harvest is the next separate learning follow-up | proposed 2026-09-19 |
| D10 | D | Private immutable Markdown observations, stable IDs and linked corrections; explicit receipt and separate harvest progress | proposed 2026-09-19; precise command/path frozen in slice preparation |

Feedback: `D9 -> prepare capture alongside AP`, `D4 -> cap the first trial at 30 minutes`, or `D6 -> add transcript capture later`.
