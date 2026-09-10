[!] Detected non-blank Issue fields — repo-sync appears to have already run. Findings applied to plan.md will require corresponding `gh issue edit` updates (N+1 rework). See `feedback_plan_review_before_repo_sync.md`.
Reviewing as: feature plan. Sections 17–21 apply.

# M1 conformance amendment: technical plan review

Target: `documentation/codex-ordinary-build-milestone-plan.md`, revised under P5,
with the root status index, README clarification, deferred-plan banner and
`documentation/codex-m1-conformance-amendment.md`. Reviewed in the current session
using the installed plan-review contract. This is a planning review, not an
independent implementation review, native acceptance or a root-test certificate.

Base: `b8acf82924cc3166a078cc50caa26b08d1135321`. Source files were read at that
commit. The active candidate remains in its separate worktree; no source changes
are part of this amendment.

## Blockers

None remaining. The draft now preserves mechanical-check ordering: C2's invalid
candidate fails before reviewers run, and C3 runs actual full review only after
the correction passes. This matches `skills/build-step/core.md:72` ("If automated
gates fail, the developer fixes them before code reviewers see the diff") and
the real failure routing at `skills/build-step/core.md:325`.

## Significant gaps

None remaining. The original requirement "Missed detection fails the acceptance
attempt" made reviewer effectiveness an M1 workflow gate. P5 explicitly changes
that acceptance criterion. Section 6 now proves live mechanical rejection/fix,
retains actual independent full reviews and honors every real blocking finding.
Deterministic negative tests prove blocking-verdict routing at the caller seam;
they are expressly not passed off as native reviewer observations.

Section 27 routing was rechecked against `skills/review-deep/core.md:31`. The
already-approved D11 bootstrap still selects ordinary high-tier source reviewers
for Steps 126/127, retaining sensitive-boundary negatives and predecessor
authority. P5 does not change that method, model tier or any co-located flag.
Reinstating deferred deep execution would conflict with the operator's P4 scope.

## Missing items

None unassigned. New capture/checkpoint helpers, workflow tests, fixture and live
procedure remain owned by Steps 126-128. They are future outputs, not falsely
reported existing support. Step 129 remains the actual live observation gate.

## Nice-to-haves

None required. A separate model-quality campaign, output-equivalence benchmark
or test-frequency redesign would expand the requested amendment. The plan
explicitly separates those concerns without waiving existing test obligations.

## Checklist coverage and evidence

| Check | Result and evidence |
|---|---|
| 1 Data persistence | Pass: section 4 preserves append-only session records, durable consumer root and explicit selection. Actual producer contract read at `skills/task-handoff/core.md:12`. |
| 2 External dependencies and integrations | Pass: section 7 retains Windows PowerShell, Git, Python/pytest and actual Playwright/Chromium setup; no added service. |
| 3 Authentication and secrets | Pass: sections 3/6 retain parent-only authority, native identity and redacted publication; no secret is restored on resume. |
| 4 Async and concurrency | Pass: sections 3/7 preserve waves, pinned candidates, serial gates and deadlines; adoption waits for the existing controller to end. |
| 5 Error handling and user feedback | Pass: section 1 separates optional finding differences from mandatory valid receipts, missing capability and uncertainty. C2/C5 retain real failure exits. |
| 6 Build and toolchain | Pass: install/build/test commands in section 7; source-tree dev/lint/typecheck explicitly N/A per `CLAUDE.md`. Fixture install/build/dev commands are Step 128 outputs before acceptance. |
| 7 Unresolved decisions | Pass: P5 is operator-selected; D13/D14 are explicit methods. Generated locators/port are recorded runtime values, not undecided architecture. |
| 8 Missing setup documentation | Pass: sections 4/6/7 define profile/support pairing, normal install, generated commands and a real browser smoke. |
| 9 Deduplication and idempotency | Pass: prior records retained, no completed-step replay, no favorable-output fishing and no limit reset. |
| 10 Integration seams | Pass: review/capture and wait/checkpoint caller repairs stay assigned to 126/127; sections 4/6 bind evidence and outcomes. |
| 11 Scope creep and over-engineering | Pass: four existing M1 steps retained; prescribed findings removed as an extra completion threshold; no new parallel benchmark. |
| 12 Security | Pass: loopback fixture, fake actors, data-versus-authority boundary and private receipt redaction retained. No real authentication feature is introduced. |
| 13 Testing strategy | Pass: unchanged requirement tests reject invalid fixture candidates and pass corrections. Native review remains real; deterministic receipt negatives remain component evidence. |
| 14 Operational concerns | Pass: startup/cleanup, wait transition, finite runs and paired support/profile rollback retained. |
| 15 End-to-end validation strategy | Pass: C1-C6 observe installed native coordinators, real Git/app/capture, correction and a genuine session transition. |
| 15.5 Smoke-gate strategy for data pipelines | Pass: actual app/capture/checkpoint and browser smoke still precede live acceptance. |
| 16 Clean-context readiness | Pass: section 1 distinguishes conformance/correctness/identity/quality; section 7 states the adoption boundary. Full plan-wrap follows. |
| 17 Existing-code validation | Pass: `rg --files` confirms named existing source/adapters, test owners and build/install tools. `skills/review-deep/core.md:15-18` binds mechanical-before-model ordering and deterministic aggregation to identical normalized lens outputs, not identical generated findings. |
| 18 Impact completeness | Pass: plan, status index, README, deferred-plan banner and existing affected issues are identified. No source/fixture implementation is hidden in the docs amendment. |
| 19 Conflict detection | Pass: main and live remote at b8acf82; controller and candidate gate live. Separate branch prevents a main/head change. Original frozen proposal and run inputs are preserved; deferred-plan banner prevents revival of superseded detection criteria. |
| 20 Context sufficiency | Pass: sections 2-4 distinguish certified repair, planned support and current status ownership. Section 7 replaces the stale qualification-only next action with reconciliation. |
| 21 Scope appropriateness | Pass: 126 full-review support, 127 resume, 128 preparation and 129 observation remain separate vertical slices. |
| 22 Operator/code split | Pass: three code units produce artifacts; one wait unit runs the prepared procedure. |
| 23 Conditional predicate | N/A: no conditional steps. |
| 24 Reviewer flag and runtime fields | Pass: source steps remain code-only; generated fixture full/UI steps require concrete Start-cmd/URL before invocation. |
| 25 Heading-based plan format | Pass: ordered Steps 126-129 retain Problem, Type, Issue, Files and Done when. Issue identities remain #199/#204/#200/#201. |
| 26 Live deployment substrate | Pass: Step 129 explicitly requires actual installed native Codex; a static preparation PASS cannot satisfy it. |
| 27 Stakes-aware routing | Pass under retained P4/D11 method, discussed above; the user-authorized scope is not reversed by an automatic flag substitution. |

The control-plane goal and four parseable units remain discoverable. The fixture
chooses an available loopback port at provisioning; no fixed registry port is added.
Existing files were checked with `rg`/file reads; planned new paths and generated
runtime locators are explicitly owned and are not dangling required inputs.

Synchronize #196/#200/#201 with this reviewed amendment and an explicit pending
integration notice. Keep active #199 and unchanged #204 execution contracts pinned
until the safe adoption handoff; then refresh their plan links to the integrated
commit without changing their acceptance criteria. This sequencing avoids editing
the currently running step's issue input. No issue is closed by plan review.

Auto-applied 0 fixes. Plan is ready for `/plan-wrap` and `/repo-sync`.
