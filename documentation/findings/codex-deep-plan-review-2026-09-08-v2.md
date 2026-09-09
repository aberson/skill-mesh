Reviewing as: feature plan. Sections 17–21 apply.

# Complete build workflows: publication 2 technical review

Target: `documentation/codex-deep-review-restoration-plan.md`, publication 2.
The historical filename now contains the operator-authorized two-host workflow
objective. This supersedes publication 1's narrow readiness judgment for execution;
neither report is evidence that the tools have completed the intended workflow.

Source baseline: `92f0821` over main `ee6ae71`; checkpoint follow-up `25b54a5`
is prepared, with its root gate pending. Independent source audits and parent
review found and corrected missing runtime/checkpoint producers, full-review
capacity and evidence gaps, stale candidate startup, checkpoint routing and
bootstrap, an accidental unsupported shared-PS1 emission path, asset ordering,
fixture issue/transition rules, and common-release acceptance identity. The final
bounded consistency pass also resolved the wait-boundary checkpoint write and
the separately pinned checkpoint-schema bootstrap dependency. The deep timer
amendment is explicitly scoped; ordinary review keeps its existing timing policy.

## Checklist

- §1 Data persistence — pass: durable consumer-root checkpoints, immutable sidecars and per-host W1-W6 evidence; unrelated state preservation explicit.
- §2 External dependencies and integrations — pass: both profiles plus an explicit support checkout; canonical deep/runtime/checkpoint producers and native prerequisites named.
- §3 Authentication and secrets — pass: private parent authority on each host, no keys/handles in child payloads or public evidence; fixture actors are fake.
- §4 Async and concurrency — pass: fixed independent reviewer sets run in measured-capacity waves; serial gates and finite overnight execution.
- §5 Error handling and user feedback — pass: incomplete runtime evidence, uncertainty, unavailable host, quota and source drift prevent advancement or acceptance.
- §6 Build and toolchain — pass: existing PowerShell/Python/Bash tooling, declared fixture build/server and real Chromium probe; no invented repository lint/typecheck.
- §7 Unresolved decisions — pass: P/D inventory selects concrete defaults; unavailable host capability has an explicit stop action, never an implicit fallback.
- §8 Missing setup documentation — pass: source variables, canonical helpers, durable root, local origin/upstream and generated concrete start/resume commands specified.
- §9 Deduplication and idempotency — pass: strict lens set, exact prior sidecar and checkpoint selection; one-shot job sentinels prevent blind relaunch.
- §10 Integration seams — pass: changes repair actual runtime/caller/checkpoint paths rather than adding an acceptance-only assertion.
- §11 Scope creep and over-engineering — pass: one connected consumer scenario per host; no universal catalog matrix, installer/WAL redesign or retired launcher revival.
- §12 Security — pass: diff and fixture challenge are data; reviewers receive intended rules without answer keys; both hosts prove parent authority.
- §13 Testing strategy — pass: actual producer/CLI negatives and short connected smoke precede real native build/review/resume observations.
- §14 Operational concerns — pass: paired source/profile upgrade, handoff reconciliation, finite job evidence and sentinel-first morning recovery.
- §15 End-to-end validation strategy — pass: BOTH hosts must complete implementation, full/deep rejection/correction, checkpoint, fresh native resume and final advancement; component success cannot close the task.
- §15.5 Smoke-gate strategy for data pipelines — pass: Step 123 wires the actual app, capture, aggregate and checkpoint producers before live observation.
- §16 Clean-context readiness — pass: records, IDs, configuration, fixture API/rules, phases and evidence ownership summarized inline.
- §17 Feature plan — existing-code validation — pass: build-step runtime/dispatch/reducer around 334-373,444,563,611-613; task-handoff resume/phase startup; legacy capture and shared closure/emitter were source-checked. New files are labeled new.
- §18 Feature plan — impact completeness — pass: both adapters/shared cores, actual helper callers, canonical/legacy synchronization, distribution checks and representative release report listed.
- §19 Feature plan — conflict detection — pass: Step 111 and handoff worktrees protected; common release includes handoff reconciliation; bootstrap exceptions have named expiry.
- §20 Feature plan — context sufficiency — pass: failure mechanisms, source/consumer roots, transport boundaries and execution prerequisites specified.
- §21 Feature plan — scope appropriateness — pass: six units cover aggregate safety, deep/setup, full/checkpoint integration, acceptance prep and two native observations.
- §22 Step shape — operator/code split (Blocker if violated) — pass: 120-123 author code/procedure; 124-125 run the prepared procedure and record observations.
- §23 Conditional steps must declare a Condition: predicate (Blocker) — N/A: no conditional implementation step.
- §24 Reviewer flag matches step shape (Significant Gap) — pass: implementation uses code-deep; the ordinary full fixture has actual URL/start/UI evidence; deep-runtime/full excluded from the claim.
- §25 Plan format readiness for /build-phase (Blocker if table-only) — pass: heading-based steps carry Problem/Type/Files/Produces/Done-when; issue fields are ready for repo-sync.
- §26 Substrate-smoke step required when the plan touches deployment seams (Significant Gap) — pass: both native installed hosts execute every W1-W6 row.
- §27 Stakes-aware review routing — high-stakes step declares plain --reviewers code (Significant Gap) — pass: implementation retains six-lens deep review with explicit bounded bootstrap.

## Blockers

None remaining in the plan instructions. Execution prerequisites still include
repair certification, exact native overnight-host qualification and the Claude
availability/install boundary. Planning readiness does not satisfy those gates.

## Significant gaps

None within the declared ordinary-full/code-deep workflow. Installed-only operation
and review-deep runtime/full remain outside the support claim and are named beside it.

## Missing items

None beyond explicitly assigned future implementation artifacts and issue backfill.

## Nice-to-haves

None.

The findings above were resolved in the plan before this final checklist. The plan
is ready for `/plan-wrap` and `/repo-sync` after the
publication-2 redline. READY is not permission to dispatch an unqualified host or
skip a failed code gate.
