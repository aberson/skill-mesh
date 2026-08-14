# Skill Mesh recovery and completion plan

**Status:** FINAL PLAN — ready for Abraham's execution approval; no phase has started

**Approved by:** Abraham Robison, 2026-08-13 (`Approve D1-D15 as written`)

**Recommendation:** make targeted changes, then proceed

**Decision source:** `documentation/skill-mesh-course-correction-plan.md`

**Product charter:** `documentation/product-charter.md`

**Communication profile:** `documentation/operator-communication-profile.md`

**Communication decision:** recommended early pilot; Abraham may accept, refine, or decline it during user acceptance testing

**Deferred Omnigent seed:** `documentation/omnigent-revisit-seed.md`

## Terms used in this plan

| Term | Meaning in this plan |
|---|---|
| Decision spine | The approved direction and decisions D1-D15 |
| Gate | A point where Abraham must approve the next kind of work |
| Lifecycle owner | The system that manages install, update, enable, disable, and uninstall |
| Materiality budget | The accepted limit on files, behavior, and effort before work must stop for review |
| Cross-family review seam | The method that lets a Claude-family workflow get a GPT-family review, or the reverse |
| Immutable evidence identity | The exact commit, environment, and configuration that produced evidence |
| Golden case | A saved test case with an expected result |
| Projection | A redacted copy of a run record for display |
| Step 4 disposition | What Abraham decides to do with the frozen installer work |
| Work in progress (WIP) | Changed files that are not complete or committed |
| Commit hash (SHA) | The Git identifier for exact repository content |
| User acceptance testing (UAT) | Abraham uses the tool and checks whether it meets his needs |
| Host | The program that runs a workflow, such as Claude Code or Codex |
| Adapter | A thin host-specific instruction or execution layer |
| Coding-root repository | The outer Git repository that contains the nested `skill-mesh` repository. A step must resolve and record its root and selected base commit before it writes there. |
| Run record or receipt | A saved record of what ran, what it produced, and what remains unknown |
| Nit | A non-blocking review suggestion |
| Block | A review finding that prevents the step from advancing |
| STE-inspired | Uses selected clarity principles from Simplified Technical English without claiming compliance |
| Correction attempt | A change made after a completed experiment attempt to correct its fixture, runner, host configuration, or command |

## Operator summary

1. Preserve the current Step 4 work before any other action.
2. Run two focused experiments. One tests install and update. One tests cross-family review.
3. Abraham then chooses the architecture. After control repairs, Abraham approves the exact product steps.
4. The final build stops again before any live install.

## 1. What this plan does

This plan does not continue the current installer work by inertia. It first preserves that work and tests two important architecture assumptions. It then repairs the build controls. Only Abraham's selected architecture proceeds to Claude Code and Codex proof.

The plan also keeps utility hookups as an independent board-completion track. That track cannot block the Skill Mesh architecture release.

## 2. Goal

Deliver a Skill Mesh release that:

- Gives Abraham materially consistent workflows in Claude Code and Codex
- Makes requested and resolved model identity, fallback, evidence, and important host differences visible
- Runs at least one real cross-family review
- Uses representative end-to-end proof instead of an exhaustive host/model/skill matrix
- Uses native host lifecycle where the experiments prove it safe and Abraham approves it
- Exposes one bounded run record to Dev Observatory without making Observatory a runtime dependency
- Preserves a recoverable path through any live cutover
- Pilots plain operational English for operator-facing communication

The approved product boundary and anti-goals are in `documentation/product-charter.md`. They are requirements for this plan, not optional background.

## 3. Current factual state

- The frozen Step 4 tracked diff has base commit `111fc2b`, as recorded in the checkpoint. `plan.md` owns moving execution status after this plan is committed.
- Four Step 4 implementation files are modified and unstaged:
  - `tools/install-skill-mesh.ps1`
  - `tools/migrate-legacy-install.ps1`
  - `tests/distributions/test_distributions.py`
  - `tests/distributions/test_legacy_migration.py`
- The checkpoint and second-opinion prompt are untracked planning evidence.
- The Step 4 work adds a recovery record before file changes and a lock around home-directory operations. It is an architecture option, not accepted production design.
- The bytes are frozen in place but are not durably preserved outside the worktree.
- The exact failure that produced `F` in the distribution suite remains unknown because the run stopped before the traceback.
- The existing GPT host layer is GitHub Copilot-specific. It is not native Codex support.
- Claude Code and Copilot can substantially find the same packaged skills. Equivalent behavior across Claude Code and Codex is not proven.
- The current system does not guarantee a different-family judge. Exact per-run model provenance is incomplete.
- Dev Observatory currently reports 5 wired and 8 unwired utility projects. A static at-a-glance page is not runtime proof.

## 4. Authority and gate rules

### 4.1 Gate states

`plan.md` is the sole mutable status and evidence index. This detailed plan is the approved contract. `plan.md` records its commit, current gate, step status, issues, candidate commits, evidence locators, commands, and Abraham's decision locator. A journal entry can record authority; it cannot create or broaden authority.

Each gate is `LOCKED`, `READY_FOR_OPERATOR`, or `APPROVED`. Evidence can move a gate to `READY_FOR_OPERATOR`. Only Abraham's explicit response can approve it. Before later work starts, the next manual bootstrap commits Abraham's exact choices and message locator to an ordinary Markdown decision record. This recovery does not need a custom gate-decision protocol or writer.

An approved execution contract is identified by its Git blob hash. Progress and evidence go to its separate journal. A change to the problem, accepted outcome, allowed paths, forbidden effects, or authority requires a new contract and renewed approval.

### 4.2 What this approval authorizes

Approval of D1-D15 authorized this final plan only. It did not authorize Goal A, product implementation, Step 4 integration, Omnigent, Gemini/local expansion, utility hookups, or live mutation.

Separate Goal A approval authorizes Steps 72-78 only. This includes preservation, Step 73's named plan/status/thin-instruction commits and named issue parking notes, disposable fixtures, the two experiments, reports, and Gate A preparation. It does not authorize a product, installer, migrator, skill-core, or live-home change. Gate A can authorize control repair. Gate B can authorize the exact repository-local product plans. Gate D alone can authorize live mutation.

### 4.3 Change control

Classify every proposed or actual scope change:

1. **Log and allow:** adjacent tests, fixtures, or documentation inside the accepted behavior and authority boundary.
2. **Quick plan amendment:** bounded work in the same subsystem with no new durable state, dependency, destructive authority, or product acceptance.
3. **Stop and redline:** a new state, schema, protocol, state machine, writer, dependency, destructive authority, target host, provider family, or product acceptance change.

Every code step declares expected production files, test files, artifacts, and an effort or surface range. Alert near 20 percent growth. Stop at two times the accepted estimate unless the plan states another limit.

Before Gate A, do not create a production schema, registry, evidence service, gate-decision format, general runner framework, receipt writer, or persistent control state. Goal A may create disposable fixtures, bounded runners, Markdown reports, and SHA-256 manifests. If an experiment shows that new infrastructure is necessary, put that choice in the Gate A packet.

### 4.4 Test and review evidence

- Use focused tests during development.
- Review immutable `BASE_SHA..CANDIDATE_SHA` bytes.
- Stage only declared candidate paths and the exact plan or status file changed.
- Run one authoritative full gate for each exact final SHA, declared environment, and relevant configuration.
- Reuse that result only for the same evidence identity. Any byte or relevant configuration change invalidates it.
- A Nit never causes an automatic correction or review cycle.
- A failed acceptance criterion, failed deterministic gate, Block, or unknown/uncertain verdict prevents advancement.

Before Phase 2, evidence uses ordinary Markdown reports, raw logs outside Git, and SHA-256 manifests. A final-gate report records the candidate commit, working directory, command, relevant runtime and configuration identity, exit result, and output hash. Phase 2 may add the minimum tested automation needed to enforce D4; it must not become a general evidence service.

Phase 2 uses these minimum local artifact shapes. Step 79 must copy them, exact storage paths, retention, and atomic-write rules into its separately reviewed Phase 2 packet before any control-code step starts.

| Artifact | Minimum fields | Default locator |
|---|---|---|
| Execution journal | schema version, approved plan path and hash, step ID, status, start/end time, evidence locators, and UAT responses | `documentation/execution/<plan-id>/journal.json` |
| Full-gate record | schema version, candidate commit/tree, repository root, working directory, argument array, runtime versions, non-secret environment identity, configuration hashes, start/end time, exit code, output hash, and result | `.build-control-evidence/full-gates/<evidence-id>.json` (ignored raw evidence) |
| Acceptance cases | case ID, fixture, action, expected verdict, expected staged paths, and expected stop reason | `tests/fixtures/build-control/cases.json` |
| Acceptance index | schema version, subject commit, case ID, expected/actual result, raw-evidence manifest hash, full-gate-record hash, and redaction status | `documentation/evidence/build-control-acceptance-index.json` |

### 4.5 Issue synchronization

Goal A is manually orchestrated and creates no new GitHub issues. Step 72 may add one preservation note to frozen issue `#116`; it does not resume or close that issue.

After Gate A, Step 79 creates an exact Phase 2 packet from Steps 80-89. It runs plan-review, plan-redline, plan-wrap, and repo-sync in that order before any control code changes. Issue numbers live in the packet and `plan.md`; they do not modify this frozen master contract.

After control acceptance, Step 89 creates and synchronizes a separate product plan in each repository. Gate B approves those final contract hashes. Each later build writes progress only to its named journal. Never close parked provider-expansion issues merely to make this plan current.

## 5. Communication rule

Use the short rule from `documentation/operator-communication-profile.md` in operator-facing work:

> Lead with the result or required action. Use plain active sentences, one idea or action per sentence, and one term per concept. Define unfamiliar terms, use lists for complex material, and preserve exact code and error identifiers.

This is a STE-inspired profile. It is not ASD-STE100 compliance. The 20-word procedural and 25-word descriptive limits are soft review signals. They are not build gates.

The pilot is not yet a product release requirement. Steps 95-97 test whether it improves understanding. Phase 7 records Abraham's decision.

## 6. Experiment evidence contract

Goal A uses ordinary files, not a new evidence protocol. Step 73 generates the packet ID `GoalAId`, formats it as `goala-<UTC yyyyMMddTHHmmssZ>-<eight random lowercase hex>`, and records it in `plan.md`. Raw evidence goes under `%LOCALAPPDATA%\SkillMesh\Evidence\<GoalAId>\`, after path-overlap validation. That directory contains `bootstrap.md`, append-only `evidence-index.md`, and the later `gate-a-full-gate.md`. A lifecycle series ID is `lifecycle-<host>-<UTC>-<eight hex>`. A cross-family series ID is `cross-<direction>-<mechanism>-<UTC>-<eight hex>`. Keep raw evidence outside every Git worktree and live host home. Commit only redacted Markdown reports and SHA-256 manifests.

Every report records:

- run and attempt ID;
- host, direction, and mechanism;
- source commit and fixture hash;
- exact redacted command and exit code;
- requested and observed model identity plus `verified`, `provider-reported`, `unverified`, or `unavailable` status;
- observations, result, evidence-file hashes, and unresolved premises; and
- latency, token, and cost availability where the host exposes them.

Use `PASS` when all required observations have trustworthy evidence. Use `PARTIAL` when the mechanism works but a declared non-safety observation is unavailable or fails. Use `FAIL` when required behavior fails with enough evidence to identify it. Use `AMBIGUOUS` when evidence cannot distinguish plausible explanations, source identity is uncertain, or a run stops before a trustworthy result.

Attempt `a0` is the initial run. Corrected attempts are `a1` and `a2`. A single byte-identical rerun after any attempt is `<attempt>-r1`. Each series permits at most two corrected attempts and one rerun per attempt. Retain every attempt. Changing a reviewed runner or fixture returns to its preparation step and creates a new candidate commit. Step 78 writes its external full-gate report to `%LOCALAPPDATA%\SkillMesh\Evidence\<GoalAId>\gate-a-full-gate.md`.

## 7. Toolchain

This repository has no separate development server, dependency-install gate, linter, or type-check command. Python and Windows PowerShell are the execution tools. Focused checks use `python -m pytest <exact paths>`. Distribution builds use `powershell -File tools/build-distributions.ps1 -Provider claude` and `powershell -File tools/build-distributions.ps1 -Provider gpt`. The authoritative repository gate is `python -m pytest` from the repository root.

## 8. Execution map

| Phase | Purpose | Orchestration | Unlock condition |
|---|---|---|---|
| 0 | Preserve WIP and establish plan authority | Manual bootstrap | Abraham approves Goal A execution |
| 1 | Run lifecycle and cross-family experiments | Manual, isolated | Phase 0 complete |
| Gate A | Abraham selects the architecture | Human-only | Both reports complete |
| 2 | Repair and prove the build controls | Manual bootstrap | Gate A approves `proceed` |
| P | Pilot plain operational English | Separate code and operator steps; non-blocking | Gate A approved and Abraham opts in |
| Gate B | Abraham approves exact product steps | Human-only | Phase 2 acceptance passes |
| 3 | Implement selected lifecycle and native Codex host | Repaired build pipeline | Gate B approved |
| 4 | Implement run record and selected cross-family seam | Repaired build pipeline | Phase 3 complete |
| 5 | Qualify models and run representative evaluation | Repaired build pipeline + operator runs | Phase 4 complete |
| Gate C, if needed | Abraham approves a named model-identity exception | Human-only | A release lane cannot report actual model identity |
| 6 | Add the Dev Observatory consumer | Repaired build pipeline | Phase 5 evidence complete |
| 7 | Reconcile docs, run UAT, rehearse, and release | Mixed | Phases 3-6 complete |
| Gate D | Abraham authorizes live cutover | Human-only | UAT and rehearsal complete |
| U | Complete utility-hookup board goal | Separate plan and goal | Phase 2 controls pass; Phase 7 release pinned |
| L | Redesign large skill cores | Later project | Recovery complete |

Do not create one automated goal across Gate A or Gate B. Each gate ends the active goal and returns control to Abraham.

---

## Phase 0 — Safeguard and establish authority

**Phase status:** READY_FOR_OPERATOR — not started

**Phase goal:** Preserve the exact Step 4 work and establish one committed recovery authority without changing product behavior.

**Execution:** Manual bootstrap. Do not invoke the current `/build-phase` or `/build-step` pipeline.

### Step 72: Preserve the exact Step 4 work

- **Status:** LOCKED until Abraham approves Goal A execution
- **Problem:** The frozen Step 4 bytes are still uncommitted in `main`. A checkpoint does not reconstruct them.
- **Type:** operator
- **Issue:** N/A
- **Existing issue reference:** `#116`; preservation may add one evidence note after Goal A approval, but must not create, enrich, close, or resume implementation on that issue
- **Files:** read-only access to `tools/install-skill-mesh.ps1`, `tools/migrate-legacy-install.ps1`, `tests/distributions/test_distributions.py`, `tests/distributions/test_legacy_migration.py`, `plan.md`, `documentation/step-4-checkpoint-2026-08-13.md`, `documentation/step-4-second-opinion-prompt.md`, `documentation/skill-mesh-course-correction-plan.md`, `documentation/skill-mesh-course-correction-proposal.html`, `documentation/skill-mesh-recovery-plan.md`, `documentation/product-charter.md`, `documentation/operator-communication-profile.md`, `documentation/omnigent-revisit-seed.md`, `documentation/runbooks/preserve-step-4.md`, Git metadata, and the read-only worktree list
- **Produces:** an operator-private recovery directory outside all recorded Git worktrees containing a binary patch for tracked changes, exact copies of every listed untracked planning artifact, status, diff stat, base SHA, worktree inventory, and SHA-256 manifest
- **Materiality budget:** zero repository writes; one external recovery directory
- **Done when:** every tracked and untracked artifact hash verifies; an isolated copy of base `111fc2b` passes `git apply --check` for the tracked patch; authoritative byte copies from `working-files/` plus copied planning artifacts reconstruct every recorded working-file hash; the original worktree remains byte-unchanged
- **Depends on:** none
- **Forbidden:** edit, stage, commit, reset, restore, clean, install, push, or remove Step 4 files
- **Runbook:** use `documentation/runbooks/preserve-step-4.md`. Its default `RecoveryRoot` is `%LOCALAPPDATA%\SkillMesh\Recovery`. The runbook validates the resolved path, writes into a new `skill-mesh-step-4-<RunId>` directory, and never cleans the source worktree.
- **Stop:** any base mismatch, missing file, recovery-root overlap, patch failure, or hash mismatch

### Step 73: Establish canonical plan and stable status authority

- **Status:** LOCKED until Step 72 passes
- **Problem:** Plan, issue, current instructions, and implementation currently describe different active scopes.
- **Type:** code, manually orchestrated with scoped staging in the dirty `main` worktree
- **Issue:** N/A
- **Flags:** `--reviewers code --max-iter 1`; manual scoped orchestration, not current `/build-phase`
- **Files:** `plan.md`, `documentation/skill-mesh-recovery-plan.md`, `documentation/product-charter.md`, `documentation/operator-communication-profile.md`, `documentation/skill-mesh-course-correction-plan.md`, `documentation/skill-mesh-course-correction-proposal.html`, `documentation/step-4-checkpoint-2026-08-13.md`, `documentation/step-4-second-opinion-prompt.md`, `documentation/omnigent-revisit-seed.md`, `documentation/runbooks/preserve-step-4.md`, `documentation/provider-expansion-plan.md`, `CLAUDE.md`, a new project-root `AGENTS.md`, and `tests/package-integrity/test_recovery_plan_hygiene.py`
- **Produces:** one committed canonical plan and charter on `main`; committed checkpoint, provenance prompt, approved redline view, and deferred Omnigent seed; `plan.md` as the sole mutable status owner and recorder of `GoalAId`; stale volatile state removed from always-loaded instructions; a thin project-root `AGENTS.md`; provider expansion marked parked; issues `#70` through `#82` receive parking notes; issue `#116` remains frozen; branch `recovery/<GoalAId>` and a clean isolated Goal A worktree at `%LOCALAPPDATA%\SkillMesh\Worktrees\<GoalAId>`; external `bootstrap.md` under the Goal A evidence root records the exact Step 73 commit after it exists
- **Materiality budget:** planning, status, and thin instruction-pointer files only; no skill core, runtime, installer, migrator, distribution, or live-home file
- **Done when:** `GoalAId`, branch, and planned worktree path are recorded in `plan.md` before the commit; the staged index is empty before scoped staging; `git diff --cached --name-only` exactly matches the Step 73 allowlist; the staged diff contains no Step 4 path; the commit is made directly on `main` and cites the external recovery manifest; Step 4 file hashes and unstaged status match before and after the commit; the branch and clean worktree are then created at that exact commit; external `bootstrap.md` records the commit, branch, path, and command without trying to put a commit hash inside its own bytes; the plan pointer and instructions agree; provider expansion is parked, not closed; `git diff --check` passes; `python -m pytest tests/package-integrity/test_recovery_plan_hygiene.py::test_recovery_authority_files_are_public_and_resolve tests/package-integrity/test_recovery_plan_hygiene.py::test_root_adapters_are_thin_and_point_to_stable_authority tests/package-integrity/test_recovery_plan_hygiene.py::test_parked_provider_plan_is_not_advertised_as_active -q` passes
- **Depends on:** 72
- **Stop:** any product or live-root file appears in the candidate diff

### Step 74: Prepare the disposable lifecycle fixture

- **Status:** LOCKED until Step 73 passes
- **Problem:** The lifecycle experiment needs a unique package that cannot pass by finding an existing installed skill.
- **Type:** code, manually orchestrated in the same clean isolated Goal A worktree
- **Issue:** N/A
- **Flags:** deterministic tests plus independent raw review; current aggregated verdict is not the sole gate
- **Files:** `experiments/recovery/lifecycle-probe/`, `experiments/recovery/run-lifecycle-probe.ps1`, `tests/experiments/test_lifecycle_probe.py`, `documentation/experiments/lifecycle-report-template.md`, and `documentation/experiments/lifecycle-runbook.md`
- **Produces:** a unique two-skill package with one shared reference and helper asset; isolated-home runner; Markdown report template; copy-paste runbook
- **Materiality budget:** the five listed paths; no production packaging abstraction, schema, evidence service, or Step 4 file
- **Done when:** the Goal A worktree starts at the exact Step 73 commit in external `bootstrap.md`; the fixture is deterministic and run-specific; one invocation covers one host and run ID; the runner takes explicit host, disposable home, both live-home locators, evidence directory, and run ID; it rejects overlap or linked overlap; `-WhatIf` reports every target; cleanup retains evidence; scoped staging matches the allowlist; focused tests and `git diff --check` pass; the fixture and runbook are committed, and their immutable candidate SHA is recorded in the external Goal A evidence index before Step 75 starts
- **Depends on:** 73
- **Stop:** the fixture needs a production framework, new durable service, or live discovery-root write

**Phase 0 exit:** Step 4 is recoverable, the accepted direction is committed, and the lifecycle experiment has a disposable fixture. No product design has been selected.

---

## Phase 1 — Two disposable architecture experiments

**Phase status:** LOCKED until Phase 0 passes

**Phase goal:** Produce evidence-complete package-lifecycle and cross-family execution reports without production implementation or live-host mutation.

**Execution:** One code-preparation step and two manual operator experiments in isolated homes and repositories. Section 6 defines the initial run, correction attempts, retention, and the limit of two corrections.

### Step 75: Run the native package-lifecycle experiment

- **Status:** LOCKED until Step 74 passes
- **Problem:** Documentation suggests native hosts can own lifecycle, but this Windows setup and package shape have not proved it.
- **Type:** operator
- **Issue:** N/A
- **Files:** exact disposable paths and command from `documentation/experiments/lifecycle-runbook.md`; output under its run-specific `EvidenceDir`
- **Produces:** one Markdown report per host and a raw-evidence SHA-256 manifest
- **Materiality budget:** disposable profiles only; zero production or live-home writes
- **Done when:** one exact reviewed runner command runs separately for each host with a unique host-series run ID; each host records package/source locator, v1 install, discovery without explicit path, shared asset load, v2 update, enable/disable behavior, uninstall, cleanup state, consumer-byte behavior, requested/resolved model status, and the Section 6 result; attempt `a0` and no more than two corrections per host series are retained; raw output, report, and SHA-256 manifest remain in the named evidence directory
- **Depends on:** 74
- **Stop:** credential ambiguity, unexplained discovery source, unexpected live-root write, or evidence that cannot distinguish stale discovery

### Step 76: Prepare the disposable cross-family fixture

- **Status:** LOCKED until Step 74 passes
- **Problem:** The cross-family experiment needs one immutable seeded candidate and bounded mechanism adapters before any live reviewer is called.
- **Type:** code, manually orchestrated in the same clean isolated Goal A worktree
- **Issue:** N/A
- **Flags:** deterministic tests plus independent raw review; current aggregated verdict is not the sole gate
- **Files:** `experiments/recovery/cross-family-fixture/`, `experiments/recovery/run-cross-family-probe.ps1`, `tests/experiments/test_cross_family_probe.py`, `documentation/experiments/cross-family-report-template.md`, and `documentation/experiments/cross-family-runbook.md`
- **Produces:** deterministic seeded-repository creator; expected defect inventory; immutable-candidate runner; Markdown report template; copy-paste runbook
- **Materiality budget:** the five listed paths; no production router, transport, schema, or reviewer-panel change
- **Done when:** repeated fixture creation produces the same seed state and defect inventory; one invocation covers one direction, mechanism, and run ID; the runner takes explicit direction, mechanism, fixture root, candidate SHA, evidence directory, run ID, and both live-home locators; it rejects repository or live-home overlap and mutable candidate bytes; `-WhatIf`, scoped staging, focused tests, and `git diff --check` pass; the fixture and runbook are committed, and their immutable candidate SHA is recorded in the external Goal A evidence index before Step 77 starts
- **Depends on:** 74
- **Stop:** preparation requires a production transport change, general dispatcher, or Step 4 file

### Step 77: Run the cross-family execution-seam experiment

- **Status:** LOCKED until Step 76 passes
- **Problem:** Host packaging does not choose how a Claude-family builder obtains a GPT-family review, or the reverse.
- **Type:** operator
- **Issue:** N/A
- **Files:** exact disposable paths and command from `documentation/experiments/cross-family-runbook.md`; output under its run-specific `EvidenceDir`
- **Produces:** comparison of manual saved handoff, reviewer-only dispatcher, and manual-now/automation-deferred; viable directions and identity evidence
- **Materiality budget:** one seeded diff, two directions where credentials permit, three named mechanism options; no universal router or reviewer-panel redesign
- **Done when:** the exact reviewed runner command runs separately for each declared direction-mechanism pair with a unique series run ID; each attempt records host, direction, mechanism, source SHA, requested/resolved model and status, reviewer role, verdict, evidence locator, latency, tokens/cost availability, and failure reason; attempt `a0` and no more than two corrections per series are retained; adapter names are never used as model proof; raw output, report, and SHA-256 manifest remain in the named evidence directory
- **Depends on:** 76
- **Stop:** candidate bytes change, model identity is inferred, or the experiment proposes a fourth mechanism without redline

### Experiment cleanup and evidence

| Experiment | Remove after review | Retain |
|---|---|---|
| Lifecycle | Only the named disposable Claude/Codex homes and unique probe package | All attempts, commands, source locators, reports, and SHA-256 manifest |
| Cross-family | Only the named disposable fixture and temporary handoff copies | Seeded candidate SHA, defect inventory, all attempts, reports, and SHA-256 manifest |

Cleanup must use the reviewed runner and exact run directory. An interrupted run retains its partial evidence and receives `AMBIGUOUS`; it is never silently replaced.

### Step 78: Prepare the Gate A decision packet

- **Status:** LOCKED until Steps 75 and 77 complete
- **Problem:** Experiment results must inform an operator choice without authorizing their own recommendation.
- **Type:** code, manually orchestrated in the same clean isolated Goal A worktree
- **Issue:** N/A
- **Flags:** independent raw review of exact report commit; current aggregated verdict is not the sole gate
- **Files:** redacted reports and SHA-256 manifest under `documentation/evidence/goal-a/<GoalAId>/`; `documentation/decisions/gate-a.md`; `plan.md`
- **Produces:** committed lifecycle and cross-family reports; one evidence-hash manifest; a Gate A table separating fact, inference, recommendation, unresolved premise, smallest options, cost, and Step 4 effect
- **Materiality budget:** evidence synthesis only
- **Done when:** every recommendation cites report and evidence hashes; `AMBIGUOUS` recommends only stop or one bounded follow-up; scoped staging contains no Step 4 or product path; focused experiment and package-integrity tests pass; both distributions build; one repository-root `python -m pytest` runs on the final Goal A candidate; an external Markdown gate report records the commit, working directory, command, relevant runtime/configuration identity, exit result, and output hash; `plan.md` marks Gate A `READY_FOR_OPERATOR`
- **Depends on:** 75, 77
- **Stop:** report/evidence identity mismatch, private data in a committed report, a product-file diff, or a recommendation that treats ambiguity as architecture authority

## Gate A — Select the architecture

**Journal state:** see `plan.md`

For `proceed`, Abraham must select every architecture field. For `bounded-follow-up-experiment`, `deferred-by-follow-up` is allowed in every remaining architecture field, and the decision names the exact new experiment, paths, attempt limit, and exit evidence. No field can be blank. A follow-up decision authorizes only that experiment.

| Field | Allowed values |
|---|---|
| Gate action | `proceed`, `bounded-follow-up-experiment`, or `stop` |
| Lifecycle owner for Claude Code | `native`, `bounded-compatibility`, `rechartered-installer`, or `deferred-by-follow-up` |
| Lifecycle owner for Codex | `native`, `bounded-compatibility`, `rechartered-installer`, or `deferred-by-follow-up` |
| Step 4 disposition | `archive-only`, `one-time-manual-cutover`, `bounded-legacy-utility`, `candidate-input-to-rechartered-installer`, or `deferred-by-follow-up`; the packet defines each action and recovery effect |
| Cross-family mechanism | `manual-saved-handoff`, `reviewer-only-dispatcher`, `manual-now-automation-deferred`, `stop`, or `deferred-by-follow-up`; the packet defines operator work, automation, and failure behavior |
| Permitted cross-family direction | exact direction or directions, with any asymmetry stated; or `deferred-by-follow-up` |
| Copilot disposition | `quarantine`, `compatibility-only`, or `deferred-by-follow-up`; never a release target |
| Resolved-identity waiver | `none`, exact host/lane/reason/expiry, or `deferred-by-follow-up` |
| Existing control branch | `reference-only`, `park`, `bounded-adoption-plan`, `stop`, or `deferred-by-follow-up` for `fix/plan-expedite-explicit-handoff@875de2a`; no silent merge |
| Goal B authorization | `yes` or `no`; Phase 2 starts only with `proceed` and `yes` |
| Live cutover | must remain `not-authorized` |

If a load-bearing result is `AMBIGUOUS`, `proceed` is invalid. A follow-up choice must name exact scope and exit evidence. Product implementation remains locked.

The approved Gate A record must cite both experiment report SHAs. `stop` ends Goal A. `bounded-follow-up-experiment` authorizes only its named experiment and keeps Phase 2 locked. Only Gate action `proceed` plus Goal B authorization `yes` unlocks Phase 2.

---

## Phase 2 — Minimum build-control repair

**Phase status:** LOCKED until Gate A is approved

**Phase goal:** Repair and prove the minimum controls, then materialize exact Gate A-selected product steps for Abraham's approval.

**Execution:** Manual scoped commits. This phase repairs the automation, so it cannot trust that automation until Step 88 passes.

### Step 79: Establish the Phase 2 base and issue authority

- **Status:** LOCKED until Gate A approves `proceed`
- **Problem:** Phase 2 overlaps an unmerged control branch, and its issue numbers must exist before control code changes.
- **Type:** code, manually orchestrated across dirty `main` and one clean Phase 2 worktree
- **Issue:** N/A
- **Flags:** manual immutable review; current pipeline is not yet trusted
- **Files:** exact Goal A candidate integration; `documentation/decisions/gate-a-approved.md`, `documentation/issues/skill-mesh-recovery/goal-b.md`, and `plan.md`
- **Produces:** a durable Gate A decision record; `main` fast-forwarded to the exact Goal A candidate without changing Step 4 bytes; an issue-numbered Phase 2 packet containing Steps 80-89; one clean Phase 2 worktree
- **Materiality budget:** one verified fast-forward plus decision, issue, and status files; no edited runtime/control file, cherry-pick, non-fast-forward merge, worktree removal, or product implementation
- **Done when:** Abraham's exact choices and message locator are committed; `main` has an empty index and fast-forwards to the Goal A candidate without conflict; Step 4 hashes and dirty status match before and after; `reference-only` imports no bytes, `park` excludes the old branch, and `bounded-adoption-plan` permits later reimplementation only; the Phase 2 packet copies Steps 80-89 exactly, completes plan-review, plan-redline, plan-wrap, and repo-sync, then receives its own clean worktree
- **Depends on:** Gate A
- **Stop:** `main` moved from the recorded Step 73 commit, fast-forward is unavailable, Step 4 status changes, branch `875de2a` moved, its disposition is absent, issue mapping is incomplete, or an edited runtime/control file enters the Step 79 commit

**Phase 2 working rule:** Steps 80-89 use one clean, isolated Skill Mesh candidate chain based on Step 79. Every commit stages only its listed paths. The frozen Step 4 paths remain absent from every Phase 2 diff. Until Step 81 repairs verdict aggregation, deterministic tests and independent raw review lenses are adjudicated with the PASS rule in this plan; the code under repair is not its own sole gate.

### Step 80: Make acceptance sources mandatory

- **Status:** LOCKED until Step 79 passes
- **Problem:** Current inline acceptance is advisory and can be ignored.
- **Type:** code
- **Issue:** TBD
- **Flags:** manual immutable review; `--max-iter 1`
- **Files:** `skills/build-step/core.md`, `skills/build-phase/core.md`, `_shared/build_step_acceptance.py`, `_shared/test_build_step_acceptance.py`, and `tests/package-integrity/test_build_control_contract.py`
- **Produces:** exactly one acceptance source: a committed plan step or a hashed standalone Markdown snapshot with fixed `Problem`, `Done when`, `Allowed paths`, `Forbidden effects`, and `Base SHA` headings
- **Materiality budget:** five maintained paths plus generated distributions; no verdict or reviewer-semantics change
- **Done when:** neither prompt prose nor legacy inline `--acceptance` can satisfy or override the gate; supplying zero or two sources blocks; the standalone file contains every fixed heading and is retained with its SHA-256; focused tests cover both valid sources, missing source, conflicting sources, and tampering
- **Depends on:** 79
- **Stop:** a third acceptance source, plan parser redesign, or unrelated orchestration change is proposed

### Step 81: Repair Nit and uncertainty semantics

- **Status:** LOCKED until Step 80 passes
- **Problem:** One Nit can block and `UNCERTAIN` is not implemented consistently.
- **Type:** code
- **Issue:** TBD
- **Flags:** deterministic goldens plus independent raw lenses; do not use the pre-fix aggregate as the sole gate
- **Files:** `skills/review-deep/core.md`, `skills/review-gauntlet/core.md`, `review-deep/scripts/aggregate.py`, `review-deep/scripts/README.md`, `_shared/build_step_verdict.py`, `_shared/test_build_step_verdict.py`, `_shared/calibrate_judge.py`, `_shared/test_calibrate_judge.py`, `tests/fixtures/review-verdict/cases.json`, and `tests/package-integrity/test_review_verdict_contract.py`
- **Produces:** Nits are advisory only; failed acceptance, Blocks, and unknown or `UNCERTAIN` results cannot advance
- **Materiality budget:** the ten listed maintained paths plus generated distributions; no new verdict value or reviewer architecture
- **Done when:** clean, one-Nit, many-Nit, failed-acceptance, missing-evidence, and unknown/uncertain cases agree across deep review, gauntlet review, aggregator, calibrator, build-step consumer, and generated profiles; no Nit triggers an automatic loop
- **Depends on:** 80
- **Stop:** more than twelve maintained paths change, a new verdict ontology appears, or review routing enters scope

### Step 82: Review one immutable candidate

- **Status:** LOCKED until Step 81 passes
- **Problem:** Reviewing a mutable worktree can grade stale or changing bytes.
- **Type:** code
- **Issue:** TBD
- **Flags:** `--reviewers deep --max-iter 1`; manual outer orchestration
- **Files:** `skills/build-step/core.md`, `_shared/candidate_evidence.py`, `_shared/test_candidate_evidence.py`, and `tests/package-integrity/test_build_control_contract.py`
- **Produces:** required `BASE_SHA` and `CANDIDATE_SHA`; read-only candidate materialization; before-and-after tree verification
- **Materiality budget:** four maintained paths plus generated distributions; no staging, merge, journal, or gate-cache change
- **Done when:** the developer returns one candidate commit; all reviewers inspect only a read-only materialization; rejection leaves target bytes and refs unchanged; tests catch shared-worktree mutation and mutation between review and integration
- **Depends on:** 81
- **Stop:** review requires a mutable target or a general artifact store

### Step 83: Make staging and integration exact

- **Status:** LOCKED until Step 82 passes
- **Problem:** Broad staging and pre-review target writes can include unrelated work.
- **Type:** code
- **Issue:** TBD
- **Flags:** `--reviewers deep --max-iter 1`; manual outer orchestration
- **Files:** every executable checkpoint, staging, merge, and commit path in `skills/build-phase/core.md`; `tests/package-integrity/test_build_control_contract.py`
- **Produces:** exact-path staging and integration of only the accepted candidate after review passes
- **Materiality budget:** one core and one test file plus generated distributions; no evidence writer or plan-status redesign
- **Done when:** every executable `git add -A` is removed; dirty unrelated tracked and untracked files remain unstaged and uncommitted at every checkpoint; the target changes only after acceptance; integrated tree equals the reviewed candidate tree
- **Depends on:** 82
- **Stop:** a checkpoint cannot name its exact paths or integration changes a non-candidate byte

### Step 84: Separate approved contracts from execution status

- **Status:** LOCKED until Step 83 passes
- **Problem:** `/build-phase` currently edits its approved plan, invalidating the approval after the first step.
- **Type:** code
- **Issue:** TBD
- **Flags:** `--reviewers deep --max-iter 1`; manual outer orchestration
- **Files:** `skills/build-phase/core.md`, `_shared/execution_journal.py`, `_shared/test_execution_journal.py`, and `tests/package-integrity/test_build_control_contract.py`
- **Produces:** an immutable plan-contract hash and a separate tracked execution journal named by each plan packet
- **Materiality budget:** four maintained paths plus generated distributions; no plan-schema or observer redesign
- **Done when:** build-phase never changes the approved plan bytes; only status, evidence locators, timestamps, and UAT responses enter the journal; acceptance, files, scope, and authority cannot be changed through the journal; resume uses the journal; tests reject a changed plan hash and semantic fields in a journal
- **Depends on:** 83
- **Stop:** the journal becomes a second plan, or observer integration enters scope

### Step 85: Reuse one full gate only for identical evidence

- **Status:** LOCKED until Step 84 passes
- **Problem:** Repeated full suites added hours, while vague reuse could accept a different tree or environment.
- **Type:** code
- **Issue:** TBD
- **Flags:** `--reviewers deep --max-iter 1`; manual outer orchestration
- **Files:** `skills/build-step/core.md`, `skills/build-phase/core.md`, `_shared/full_gate_evidence.py`, `_shared/test_full_gate_evidence.py`, and `tests/package-integrity/test_build_control_contract.py`
- **Produces:** create-new atomic gate records keyed by commit/tree, working directory, argument array, runtime versions, non-secret environment identity, and configuration hashes
- **Materiality budget:** five maintained paths plus generated distributions; no dependency manager or remote cache
- **Done when:** focused tests run during iteration; one final full gate is owned by one layer; an identical PASS record is reused; any changed identity rejects reuse; interruption and collision are visible; secrets are never recorded or hashed
- **Depends on:** 84
- **Stop:** reuse needs an undeclared input, remote service, or credential value

### Step 86: Add bounded change control

- **Status:** LOCKED until Step 85 passes
- **Problem:** Current phone-a-friend logic reacts after churn and misses first-pass scope expansion.
- **Type:** code
- **Issue:** TBD
- **Flags:** `--reviewers deep --max-iter 1`; manual outer orchestration
- **Files:** `skills/build-step/core.md`, `skills/build-phase/core.md`, `_shared/change-control.md`, `documentation/evidence/change-control-pilot.md`, optional `_shared/change_control.py`, optional `_shared/test_change_control.py`, and `tests/package-integrity/test_build_control_contract.py`
- **Produces:** manual pre-dispatch and post-candidate three-lane classification; a usefulness report; optional deterministic sentinel only after the manual rule passes its usefulness criteria; optional read-only advice only for uncertain diagnosis
- **Materiality budget:** the named paths plus generated distributions; no model-based classifier, routing framework, or new persistent state
- **Done when:** saved cases cover adjacent test/docs, bounded amendment, new protocol/state, and a two-times materiality breach; deterministic stops occur before review or another developer pass; advice cannot waive a stop; the pilot report says whether the manual rule detected every planted stop, allowed adjacent test/docs, and gave an understandable reason and next action; if useful, the deterministic sentinel and tests are implemented in the optional named files before Step 87; if not useful, the report records the evidence-based D6 deferral and no automation file is created
- **Depends on:** 85
- **Stop:** automation starts before the usefulness result, attempts to infer ambiguous intent, or introduces a routing framework

### Step 87: Calibrate requirement strength in planning

- **Status:** LOCKED until Step 86 passes
- **Problem:** Planning can turn preferences and experiments into universal requirements without exposing cost.
- **Type:** code
- **Issue:** TBD
- **Flags:** `--reviewers deep --max-iter 1`; manual outer orchestration
- **Files:** `_shared/requirement-calibration.md`, `skills/plan-init/core.md`, `skills/plan-feature/core.md`, `skills/plan-review/core.md`, `skills/plan-redline/core.md`, and `tests/package-integrity/test_requirement_calibration.py`
- **Produces:** `hard | preferred | experiment | not-now` commitments; provenance; stated harm for hard requirements; external-assumption spike and anti-goal prompts
- **Materiality budget:** six maintained paths plus generated distributions; no skill decomposition or planning state machine
- **Done when:** saved cases cover all commitments, agent-defaulted hard requirements, experiments promoted to architecture, and preferences that create subsystems; conflicting universal and extra-gate guidance is removed
- **Depends on:** 86
- **Stop:** a persistent planning store or unrelated planning feature appears

### Step 88: Prove the repaired control path

- **Status:** LOCKED until Steps 80-87 pass
- **Problem:** Product work must not resume until the repaired path proves the failures that caused this delay.
- **Type:** code
- **Issue:** TBD
- **Flags:** `--reviewers deep --max-iter 1`; manual outer orchestration
- **Files:** `tests/fixtures/build-control/cases.json`, `tests/package-integrity/test_build_control_acceptance.py`, `documentation/evidence/build-control-acceptance.md`, `documentation/evidence/build-control-acceptance-index.json`, and `.gitignore`
- **Produces:** a disposable-repository acceptance report and redacted evidence-hash manifest
- **Materiality budget:** five acceptance paths; no product implementation
- **Done when:** cases prove happy path, Nit-only no-loop, failed acceptance, uncertainty, scope expansion, adjacent docs/tests, immutable review, scoped staging, immutable plan plus journal, and exact full-gate reuse; both distributions build from the candidate; focused acceptance passes
- **Depends on:** 80, 81, 82, 83, 84, 85, 86, 87
- **Stop:** any case lacks raw evidence, private data enters Git, or candidate distributions differ from canonical sources

### Step 89: Materialize product plans and prepare Gate B

- **Status:** LOCKED until Step 88 passes
- **Problem:** Architecture-specific product work cannot be exact until Gate A and the repaired controls exist.
- **Type:** code
- **Issue:** TBD
- **Flags:** `--reviewers deep --max-iter 1`; manual cross-repository orchestration
- **Files:** Skill Mesh `documentation/skill-mesh-product-plan.md`, `documentation/decisions/gate-a-approved.md`, `documentation/issues/skill-mesh-recovery/goal-c.md`, and `plan.md`; coding-root `documentation/skill-mesh-observatory-consumer-plan.md`
- **Produces:** one immutable, issue-numbered plan contract and separate journal path per repository; exact launch blocks using only supported `/build-phase` arguments; disposable Claude Code and Codex execution homes loaded from the final candidate distribution
- **Materiality budget:** plan, decision, issue, journal-template, and status files in the two named repositories; no product code
- **Done when:** every plan has exact paths, acceptance, rollback, issue, base, materiality, and stop conditions; each repository runs plan-review, plan-redline, plan-wrap, and repo-sync in order; the coding-root repository's resolved root, fixed base, clean isolated worktree, and exact staging allowlist are recorded before its first write; its live dirty worktree status and tracked-file hashes remain unchanged before and after; each launch block sets and verifies its working directory and base, then uses only `--plan`, `--phase`, `--steps`, `--resume`, or `--dry-run`; model policy and gate ownership stay in the contract; the Gate A-selected lifecycle runbook assembles a disposable, non-product Codex bootstrap package from candidate sources and records its source SHA; this proves source loading only, not final native-Codex behavior; the final Skill Mesh `python -m pytest` and coding-root `python -m pytest` each run once on their final candidate; Gate B cites both plan hashes and both gate records
- **Depends on:** 88
- **Stop:** a plan contains an unresolved field; the selected coding-root base omits or overlaps unresolved user work; a host loads stale live bytes; a full gate runs before the final planning commit; or a new authority appears

## Optional Goal P - communication pilot

### Step 95: Prepare the Skill Mesh communication profile

- **Status:** LOCKED until Gate A approves a proceed choice and Abraham approves Goal P
- **Problem:** Agent jargon and model-dependent phrasing make operational output hard to read.
- **Type:** code
- **Issue:** N/A
- **Flags:** `--reviewers code --max-iter 1`; separate clean Skill Mesh worktree
- **Files:** `documentation/operator-communication-profile.md`, `tests/fixtures/operator-communication/success.md`, `tests/fixtures/operator-communication/blocked.md`, `tests/fixtures/operator-communication/options.md`, and `tests/package-integrity/test_operator_communication_profile.py`
- **Produces:** one detailed reference and three representative evaluation cases
- **Materiality budget:** the five listed paths; no linter, skill-wide rewrite, or compliance claim
- **Done when:** the base is pinned; scoped staging contains only these paths; exact technical strings remain unchanged; the short rule works without the detailed reference; focused tests pass
- **Depends on:** 73 and Gate A
- **Stop:** the profile changes an exact token or becomes a formal-compliance claim

### Step 96: Bind the short rule in coding-root instructions

- **Status:** LOCKED until Step 95 passes
- **Problem:** The profile will not affect fresh consumer sessions unless the workspace layer loads it.
- **Type:** code
- **Issue:** N/A
- **Flags:** `--reviewers code --max-iter 1`; separate clean coding-root worktree
- **Files:** coding-root `.claude/workspace-instructions.md`; root `AGENTS.md` and `CLAUDE.md` remain unchanged
- **Produces:** one self-contained short rule and a separate coding-root candidate
- **Materiality budget:** one changed path
- **Done when:** a read-only materialization of the exact Step 95 SHA tests the coding-root candidate through an explicit candidate-path argument; neither repository stages another repository's path; fresh Claude Code and Codex sessions load the rule
- **Depends on:** 95
- **Stop:** another coding-root path changes or the rule needs a private absolute path

### Step 97: Run comprehension testing

- **Status:** LOCKED until Step 96 passes and Abraham joins the pilot
- **Problem:** Text checks do not prove that Abraham understands the result, next action, and choice.
- **Type:** operator
- **Issue:** N/A
- **Files:** read-only paired outputs; Skill Mesh communication branch `documentation/evidence/operator-communication-uat.md`
- **Produces:** one report with load evidence, Abraham's answers, mismatches, and accept/refine/decline result
- **Materiality budget:** one report and at most one return to Step 95 or 96
- **Done when:** for each paired output Abraham states what happened, what happens next, and what he must decide; every mismatch is recorded
- **Depends on:** 96
- **Stop:** a refinement is requested; record it before one bounded return

## Gate B - approve exact product plans

**Journal state:** see `plan.md`

After Step 89, Abraham reviews the Skill Mesh and coding-root plan hashes, gate records, disposable-host source proof, and launch blocks. He selects `proceed` or `stop` and names both plan hashes. A proceed decision authorizes only those immutable plan contracts. The first Goal C action records Abraham's choice and message locator without changing either contract. Gate B always records live cutover as `not-authorized`.

---

## Phase 3 — Selected lifecycle and native Codex host

**Phase status:** LOCKED until Gate B is approved

**Fixed outcomes for the Gate B appendix:**

1. Separate host adapter identity from model-family identity.
2. Audit and retarget Copilot-specific discovery roots, environment variables, transport, wrappers, documentation, and tests to native Codex.
3. Quarantine or label retained Copilot behavior as compatibility-only. Never relabel it as Codex.
4. The supported Codex plugin targets are Codex CLI and, where useful, ChatGPT desktop. The current Codex IDE extension is not a plugin target unless Abraham later approves an explicit compatibility requirement.
5. Recheck official surface support before Phase 3 because host capabilities can change.
6. Implement only the Gate A lifecycle owner for each host.
7. Apply only the approved Step 4 disposition. Frozen bytes are evidence or candidate input, not presumed production.
8. If `rechartered-installer` is selected, stop and approve a dedicated safety-subsystem subplan before installer implementation.

**Phase exit:** Claude Code and the approved Codex CLI/ChatGPT desktop surfaces discover the selected package from proved source locators. Install, update, disable, and uninstall behavior matches Gate A. The IDE extension is either explicitly out of scope or covered by a later approved compatibility requirement. No unapproved legacy subsystem remains.

## Phase 4 — Minimal run record and cross-family seam

**Phase status:** LOCKED until Phase 3 passes

**Fixed outcomes for the Gate B appendix:**

1. Freeze a minimal versioned `skill-mesh.run-receipt.v1` fixture, schema, producer-owned storage path, and atomic write behavior.
2. Record schema/workflow version, run ID/times, skill/version/source SHA, host/adapter/package, role, requested model, resolved model/status, provider family, transport, fallback, result, evidence locators, duration, and token/cost availability.
3. Keep optional enrichment non-blocking.
4. Produce one redacted same-version projection. Define the redaction policy and add fixture tests for prompts, secrets, private paths, and unapproved evidence content. Do not create a second Observatory protocol.
5. Implement only Gate A's cross-family mechanism:
   - `manual-saved-handoff`: hashed handoff, receipt, and runbook;
   - `reviewer-only-dispatcher`: one reviewer-role boundary with explicit identity, fallback, and receipt;
   - `manual-now-automation-deferred`: the manual mechanism remains release proof.
6. Do not restore a general router or redesign the reviewer panel by implication.
7. Give every run ID create-new semantics. A collision or concurrent claim fails visibly and does not overwrite a record.
8. Write through a temporary file and publish atomically. Define how readers handle an incomplete, corrupt, duplicate, or unknown-version record.
9. Make export and projection idempotent. Add tests for interruption, corruption, collision, concurrent writers, and repeated reads.

**Phase exit:** One real cross-family review can produce an honest run record. If no manual or dispatcher route works, release remains blocked.

## Phase 5 — Model policy and representative evidence

**Phase status:** LOCKED until Phase 4 passes

**Fixed outcomes for the Gate B appendix:**

1. Qualify `Fable -> Sol` and `Sonnet -> Terra` as candidate peers. Update `config/model-tier-map.json` only from evidence.
2. Use exact pins for release, evaluation, and high-risk runs where supported. Routine aliases remain qualified and visible.
3. Always record the requested identity and resolution status. Never copy the requested value into the resolved field by inference.
4. Run a preregistered same-family versus cross-family seeded-defect evaluation. Report unique detections, false positives, no-value results, latency, tokens, and cost.
5. Prove the mechanism even if marginal quality is zero. Keep any quality-uplift claim experimental.
6. Run three retained trials for each representative case and host unless Gate B approves another fixed count:
   - `plan-redline` in Claude Code and Codex
   - `build-step` in Claude Code and Codex, including a real Sonnet/Terra-family direction
   - `session-wrap` in Claude Code and Codex with external messaging and live-root mutation disabled
7. Retain failures. Do not replace a failed trial with an unreported retry.

**Gate C — model-identity exception, only if needed:** any release case with `resolved_status` `unavailable` or `unverified` requires Abraham's exact named waiver. All release cases unavailable cannot pass.

## Phase 6 — Dev Observatory consumer

**Phase status:** LOCKED until Phase 5 evidence passes

**Fixed outcomes for the Gate B appendix:**

1. Skill Mesh writes the full run record and its redacted projection without Observatory.
2. Dev Observatory consumes exactly `skill-mesh.run-receipt.v1`. Gate B names its repository, base SHA, exact loader paths, and repository gate.
3. A real Skill Mesh producer fixture must pass through the real Dev Observatory loader into an existing Snapshot, summary, or at-a-glance surface.
4. The loader bounds file size, count, and processing time. Malformed, oversized, corrupt, and unknown-version inputs fail visibly without affecting skill execution.
5. Dev Observatory uses an existing generic Snapshot/summary/at-a-glance surface where possible.
6. Transparency shows mechanical wiring only.
7. Consumer failure is visible and nonfatal to skill execution.
8. Utility Project Standard remains independent and off the release critical path.
9. Producer and consumer run in separate repository-pinned build phases. Each phase uses a plan packet committed inside its own repository. The Dev Observatory consumer currently lives in the coding-root repository, so its plan packet, status updates, commits, and declared full gate remain there.

**Phase exit:** Abraham can inspect one real Skill Mesh run in the appropriate Observatory view and trace it to the raw producer evidence.

## Phase 7 — Documentation, UAT, release, and cutover

**Phase status:** LOCKED until Phases 3-6 pass

**Fixed outcomes for the Gate B appendix:**

1. Reconcile README, architecture, host discovery, migration, troubleshooting, model configuration, and thin high-level adapters with observed behavior.
2. Keep volatile status out of always-loaded instructions.
3. Walk Abraham through:
   - a high-level architecture and evidence tour;
   - normal Claude Code and Codex use;
   - the full build-step cross-family case;
   - requested/resolved model evidence;
   - the Dev Observatory view;
   - install/update/uninstall or the approved compatibility path;
   - rollback.
4. Include communication-profile UAT. For each result, ask Abraham what happened, what happens next, and what he must decide. Record any difference between the intended and understood meaning. Abraham may approve, refine, or decline the profile without invalidating architecture evidence.
5. Run focused checks during development.
6. Run one full repository gate on the final merged release-candidate SHA for each declared environment/configuration.
7. Rehearse install, update, cross-family review, run-record projection, uninstall, and rollback in isolation.
8. Freeze the release artifact, checksums, recovery artifact, rehearsal evidence, and rollback instructions before Gate D.

## Gate D — Authorize live cutover

**Journal state:** see `plan.md`

Abraham reviews UAT, final gate evidence, release artifact identity, rehearsal, recovery, and rollback. He selects `proceed` or `stop` and, for `proceed`, names the release artifact hash, exact live targets, rollback method, and rollback-retention window. The journal remains `LOCKED` until his explicit response. Only that response authorizes a live install or cutover.

After Gate D, execute the approved cutover. Confirm one representative live invocation, one honest run record, and the Observatory view. Retain the Step 4 recovery artifact through the approved rollback window.

---

## Board Track U — Utility-hookup completion

**Status:** INDEPENDENT AND LOCKED

Track U starts its redline after Phase 2 controls pass. By default, implementation starts after Phase 7 and pins the released Skill Mesh package. No Skill Mesh release step depends on `U*`.

The current baseline is 5 wired and 8 unwired utilities. After Phase 2, create a separate Track U plan. Re-redline each proposed caller seam as keep, reduce, or retire. Do not inherit the old broad Steps 4-26 by default.

Track U is complete when Dev Observatory reports 13 of 13 mechanically wired, each shared hook has one real Claude Code and Codex invocation on the same package version, Measure Twice passes its project-local fixture, failure remains advisory and bounded, and the exact package SHA passes its full gate. Static transparency alone is not acceptance.

---

## Later Track L — Skill structure redesign

Track L is not part of recovery. It starts only after the release contracts and evaluations are correct.

Track L will shorten `build-step`, `build-phase`, and `review-deep` by keeping the main core as an executable state machine. Optional modes, examples, templates, and incident history move into references. Deterministic validation moves into tested scripts. The redesign receives forward tests before generated host packages change.

The current `skill-iterate` can help later with constrained, scorable single-file improvement. It cannot perform the multi-file canonical decomposition by itself.

## Approved-decision coverage

| Decisions | Implemented by |
|---|---|
| D1-D3 | Goal A experiments and Gate A |
| D4 | Steps 80-85 and 88 |
| D5-D7 | Step 86 |
| D8-D9 | Phase 5 and Gate C |
| D10 | Phases 4 and 6 |
| D11 | Independent Track U |
| D12 | Later Track L |
| D13 | Phase 3 Codex surfaces |
| D14 | Step 87 before product work |
| D15 | Gate A Step 4 choice and Phase 3 plan |

## Goal boundaries

Use separate goals:

### Goal A — Preservation and experiments

> Durably preserve the exact Step 4 work and produce evidence-complete package-lifecycle and cross-family execution reports plus a Gate A decision packet, without production implementation or live-host mutation.

Goal A covers Steps 72-78. It ends at Gate A and returns control to Abraham.

### Goal B — Control repair and exact branch

> After Gate A, implement and prove the minimum build-control repairs, then materialize exact Gate A-selected product steps for Abraham's approval.

Goal B covers Steps 79-89. Goal B ends at Gate B and returns control to Abraham.

### Goal C — Product release

> After Gate B, implement and prove the approved Claude Code/Codex Skill Mesh release, model evidence, run-record projection, UAT, and isolated cutover rehearsal. Stop before live mutation unless Abraham explicitly approves Gate D.

Use a separate repository-pinned build-phase for each Phase 3-7 and for each repository that a phase changes. Dev Observatory consumer work runs in its own repository and gate. Do not span Gate D with an automated goal.

### Goal P — Optional communication pilot

> After Gate A, prepare the proposed plain operational English profile, prove that fresh Claude Code and Codex sessions load it, and record Abraham's understanding of paired outputs without adding a compliance claim or blocking linter.

Goal P covers Steps 95-97. It is independent of Goal B and cannot delay Gate B or the product architecture release.

### Goal U — Utility board completion

> After the Skill Mesh release, connect one primary real caller for each unwired utility, prove the seven shared hooks in Claude Code and Codex, complete the project-local Measure Twice seam, and close the board with real-run and Observatory evidence.

Goal U is independent. Its failure does not reopen the Skill Mesh architecture release.

## Goal and build-phase launch contracts

No goal is active when this plan is published.

To start Goal A, Abraham cites the final recovery-plan Git blob hash supplied in the plan handoff. The plan cannot contain its own final blob hash. He can say:

> Approve Goal A execution for recovery-plan blob `<BLOB_SHA>`. Run Steps 72-78, including Step 73's scoped plan/status/thin-instruction commits and named issue notes. Stop at Gate A without product implementation or live-host mutation.

That approval creates only Goal A with the objective in the preceding section. Steps 72-78 use manual orchestration because the current build controls are not trusted.

After Gate A approves `proceed`, Goal B uses its stated objective and Steps 79-89. Goal B uses manual outer orchestration because it repairs the build controls. It ends with exact repository-local product plans and Gate B review.

Abraham can separately start Goal P by saying:

> Approve Goal P. Run optional communication Steps 95-97 and record my comprehension feedback without delaying Goal B.

Goal P uses separate repository candidates for Steps 95 and 96. It stops for Abraham's Step 97 participation. It does not authorize any product or live-host change.

Step 89 must generate one exact launch block for each approved Phase 3-7 repository slice. The block verifies the repository, base, and approved plan hash, then invokes only supported `/build-phase` arguments. The plan cannot safely provide those blocks before Gate A selects the architecture.

After Gate B approval, Goal C runs only those generated commands. It cannot cross Gate D. Goal U gets a separate plan, goal, and commands after the Skill Mesh release is pinned.

## Definition of complete

The Skill Mesh recovery is complete when:

- Phases 0-7 pass.
- Gate A and Gate B decisions are approved and cited.
- Gate D is either completed or the release is explicitly declared ready but not installed.
- Claude Code and Codex pass the representative proof on the same release version.
- At least one real cross-family review has honest model and evidence provenance.
- The README and high-level adapters match observed behavior.
- Abraham completes the high-level, normal, and end-to-end walkthroughs.
- The run record is visible in Dev Observatory without making Observatory a runtime dependency.
- Step 4 disposition and rollback evidence are explicit.

The board goal is complete only when independent Track U also passes. Track U completion is not required to call the Skill Mesh architecture release complete.

## Research sources to recheck at execution

- [ASD-STE100 Simplified Technical English, Issue 9](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf)
- [ASD-STE100 official FAQ](https://www.asd-ste100.org/STE_faq.html)
- [OpenAI: Package your plugin](https://developers.openai.com/plugins/build/plugins)
- [OpenAI: Plugins in ChatGPT and Codex](https://learn.chatgpt.com/docs/plugins)
- [Anthropic: Create plugins](https://code.claude.com/docs/en/plugins)
- [Anthropic: Discover and install plugins](https://code.claude.com/docs/en/discover-plugins)

Host products change quickly. Recheck first-party behavior before each live experiment. Documentation is evidence for a test design, not proof that the test will pass on this Windows setup.
