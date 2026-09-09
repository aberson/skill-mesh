[!] Detected non-blank Issue fields — repo-sync appears to have already run. Findings applied to plan.md will require corresponding `gh issue edit` updates (N+1 rework). See `feedback_plan_review_before_repo_sync.md`.
Reviewing as: feature plan. Sections 17–21 apply.

# M1 technical plan review

Target: `documentation/codex-ordinary-build-milestone-plan.md`, publication 3,
with its `plan.md` status pointer and the historical-plan supersession banner.
Reviewed on 2026-09-09 after merging repaired main into the existing proposal
branch (`0763fcd31e267a6161ebd83dfab72e15c8c66b09`). This is a local plan
review, not native qualification or a code/test certificate.

## Blockers

None remaining in the plan. Native qualification and issue synchronization remain
explicit execution prerequisites, not observations of a running workflow.

## Significant gaps

Resolved: the first draft placed a new checkpoint step between existing numbers.
`skills/build-phase/core.md` wait handling announces `--resume <next-step-N+1>`;
the plan now uses contiguous Steps 126-129 and a historical issue/step mapping.

Stakes-aware review routing, section 27: Steps 126/127 affect producer/consumer and
session-state boundaries named by `skills/review-deep/core.md:31`. Ordinary source
review is an explicit M1 build-method amendment under the operator's P4 deferral
of deep execution. It retains five independent high-tier code reviewers, mechanical
negative checks, immutable predecessor authority and final full runtime proof.
This is a visible reduction from publication 2's six-lens deep implementation
review, not an assertion of equivalent defect-detection coverage. The scope choice
is not automatically reversed by a skill autofix. D11 records the agent-selected
method separately from the operator's scope choice; uncertainty remains a stop.

## Missing items

None unassigned. The capture helper, canonical checkpoint helper, workflow tests,
fixture and live procedure are explicitly marked future outputs with owning steps.
Step 127's blank Issue field is expected before repo-sync and blocks dispatch,
not plan drafting. Existing #199/#200/#201 must receive the new step definitions.

Resolved: the no-issue/BASELINE_HEAD repair belongs to build-phase's production
caller (`skills/build-phase/core.md:485`), so that source was added to Step 126's
Files field. Existing regression owners and concrete adapter paths were added to
the impact list rather than leaving an unexplained generic test/adapters reference.

## Nice-to-haves

None. A new scheduler, deep parity matrix, installer redesign and consumer feature
execution are explicitly excluded from M1.

## Checklist coverage and evidence

| Check | Result / evidence |
|---|---|
| 1 Persistence | Session files, durable root, explicit resume selection and atomic/append-only handling defined in section 4; task-handoff current producer read at lines 12-46. |
| 2 Dependencies | Windows/Python/Git, existing pytest dependencies and real Playwright/Chromium launch named; no new external service. |
| 3 Authentication/secrets | Native host auth retained; private parent verdict capability excluded from prompts, logs and saved resume state. |
| 4 Async/concurrency | Separate run directories, no competing pytest, fresh sibling waves, fixed candidate, durable gate sentinels and finite deadline. |
| 5 Errors | Missing identity/support/evidence/coverage is nonpassing; no silent runtime skip or implicit deep fallback. |
| 6 Toolchain | Install/build/test commands named; source-tree dev/lint/typecheck explicitly N/A. Fixture install/build/start are Step 128 deliverables before live execution. |
| 7 Decisions | P4 resolves first delivery. D1-D12 remain clearly attributed. No unresolved architecture placeholder; runtime locators/ports are generated and recorded by the named owner. |
| 8 Setup | Support pin, package identity, real Chromium check and concrete generated fixture commands defined in sections 4/6/7. |
| 9 Idempotence | New run directory, no blind relaunch, no completed-step replay, preserved prior checkpoints/evidence. |
| 10 Integration | Capture-to-full-review and checkpoint-to-build-phase callers identified; no-issue baseline owner corrected. |
| 11 Scope | Ordinary Codex first; deep/Claude and actual consumer remain deferred. |
| 12 Security | Loopback-only app/fake actors, structured inputs, native authority boundary, no raw secrets in public evidence; shared filesystem is not called a sandbox. |
| 13 Tests | Real producer/caller negatives plus existing production root gate; no narrowed DONE certificate. |
| 14 Operations | Finite run, checkpoint, native transition, normal cleanup and matched profile/support rollback. |
| 15 End-to-end | C1-C6 require installed native execution, real defect rejection/correction before and after native resume. |
| 15.5 Smoke | Actual app/capture/checkpoint chain and browser launch required before long acceptance. |
| 16 Context | New plan contains support/state shapes, concrete acceptance rules, ownership and build order. |
| 17 Existing code | Test-Path confirmed all 14 initial source/contract/tool paths; rg located capture/readiness, simultaneous review, wait, rollup and BASELINE_HEAD callers. Planned new paths are explicitly classified. |
| 18 Impact | Canonical/compatibility capture, source support, adapters, shared core, tests and representative report included; helper callers re-searched before signature changes. |
| 19 Conflicts | Historical publication 2 execution explicitly superseded for M1; main repair merged; protected Claude/consumer work stays parked. No competing builder found in process inspection (only the inspection shell matched). |
| 20 Architecture | Installed profile plus pinned source support explained; current capability and planned helpers distinguished. |
| 21 Step size | Full review, durable resume, acceptance preparation and live acceptance separated; no fractional helper-only ship step. |
| 22 Step shape | Three code units and one wait; code steps author artifacts, wait observes actual prepared procedure. |
| 23 Conditions | N/A: no conditional steps. |
| 24 Review flags | Headless source units declare code review; real fixture full/UI flags require generated Start-cmd/URL before invocation. |
| 25 Parseability | Four heading-format units, ordered 126-129, with Problem/Type/Issue/Files/Done when; issue 127 pending sync. |
| 26 Live substrate | Step 129 is a wait unit requiring native CLI execution, not a mock or static test count. |
| 27 Stakes | Explicitly surfaced above; no silent self-grading, downgrade or omitted runtime acceptance. |

Additional verified input: coding-root commit
`6b05baba19a28b7a4a713fd89460d391fe9281af` contains
`.claude/hooks/lib/task-state-derive.ps1`, Git blob
`3ac2def3e7ca86d99db8216cf4eafb45206e83a2`. `git cat-file -e` returned 0.
Consumer plan section 7 identifies Steps 56-60 as its first useful checkpoint;
its inspected steps retain `--reviewers full --isolation worktree --ui`.

Plan corrections above were applied during review. No user decision remains
unanswered; the accepted scope and agent defaults are rendered next in the stable
proposal, followed by the required plan-wrap check. No code implementation began.
