Reviewing as: feature plan. Sections 17–21 apply.

# Codex deep restoration: plan review

Target: `documentation/codex-deep-review-restoration-plan.md`. Source baseline:
`92f082118b695b9275cae6b06e0cb64b808ba0db`. Review performed after source-audit
corrections, before proposal rendering and plan-wrap. This report reviews a plan;
it does not certify implementation, a model invocation, or host acceptance.

The source audit corrected five drafting defects before this final pass: a
nonexistent reader-guide path, the Step-122 selection of the qualified adapter,
shared runtime/full schemas, valid absence-of-thing evidence, and native timeout
failure-reason compatibility. The final plan also explicitly resolves the current
core/reducer uncertainty mismatch. Its D3/D4 scheduling and bootstrap choices
remain visible proposal decisions, not historical operator approvals.

## Checklist

- §1 Data persistence — pass: existing sidecar plus a local host receipt; unique directories and immutable prior records are specified.
- §2 External dependencies and integrations — pass: explicit pinned local source dependency and existing host tools; no new remote service.
- §3 Authentication and secrets — pass: no new credentials; private build-step channel stays with the parent.
- §4 Async and concurrency — pass: fixed independent lens set, bounded capacity, cancellation before retry, unique output directories.
- §5 Error handling and user feedback — pass: missing capability/calibration, invalid records, uncertainty, mutation, and deadline failures are visible and nonpassing.
- §6 Build and toolchain — pass: install/rehearsal, build, tests, environment and dependency prerequisites are named; development server, project lint, and typecheck are explicitly inapplicable.
- §7 Unresolved decisions — pass: D1–D6 are selected proposal defaults, with their tradeoffs visible; no implementation placeholder remains. Blank issue numbers are expected before repo-sync.
- §8 Missing setup documentation — pass: two local source variables, immutable commit format, profile/source matching, and Step-122 acceptance preparation are explicit.
- §9 Deduplication and idempotency — pass: duplicate inputs fail closed, rule 7 is preserved, and prior-sidecar selection is exact rather than newest-file inference.
- §10 Integration seams — pass: actual lens/reducer/caller schemas, metadata CLI addition, source/consumer cwd distinction, and authenticated terminal channel are separated.
- §11 Scope creep and over-engineering — pass: no installer/WAL redesign, new scheduler, runtime-deep expansion, or old RD resumption.
- §12 Security — pass: diff and findings are data, structured argv, parent-only authority, mutation auditing, and explicit trusted source selection.
- §13 Testing strategy — pass: real aggregate CLI negatives, shared-lane nonregressions, caller/distribution checks, and a live installed-host observation are distinct.
- §14 Operational concerns — pass: explicit source/profile pair, matched upgrade/rollback preparation, failure preservation, and finite retry behavior.
- §15 End-to-end validation strategy — pass: Step 123 observes actual independent lenses, aggregation, caller consumption, and a second review with prior-sidecar input. No always-on claim.
- §15.5 Smoke-gate strategy for data pipelines — pass: Step 121 exercises the real caller chain before the attended step; Step 120 round-trips metadata and previous sidecars.
- §16 Clean-context readiness — pass: schemas, IDs, source identity, host limits, scope, commands, and execution order are inline.
- §17 Feature plan — existing-code validation — pass: source table cites the actual adapter, loader, reducer, CLI, calibration resolver, emitter, installer and deep consumer. New files are explicitly marked new.
- §18 Feature plan — impact completeness — pass: canonical/legacy script pair, mirrored lens enum, shared runtime/full consumers, installed wrappers, capability pins and docs are included.
- §19 Feature plan — conflict detection — pass: DS-D3 is amended through a new plan; CL Step 111 and the unmerged handoff branch stay separate. Bootstrap/scheduling amendments are explicit. Steps 120–123 do not overlap the current maximum, 119.
- §20 Feature plan — context sufficiency — pass: existing architecture and producer failures are summarized with concrete consequences.
- §21 Feature plan — scope appropriateness — pass: four units cover safe aggregation, normal invocation, acceptance preparation, and attended observation.
- §22 Step shape — operator/code split (Blocker if violated) — pass: code/preparation lives in 120–122; 123 is an attended wait producing observations.
- §23 Conditional steps must declare a Condition: predicate (Blocker) — N/A: no conditional steps.
- §24 Reviewer flag matches step shape (Significant Gap) — pass: code-deep review needs no runtime URL; no full/runtime gauntlet flag is introduced.
- §25 Plan format readiness for /build-phase (Blocker if table-only) — pass: heading-based Steps 120–123 contain Problem, Type, Issue, Files, Produces and Done when; issue fields await repo-sync.
- §26 Substrate-smoke step required when the plan touches deployment seams (Significant Gap) — pass: Step 123 observes the actual Codex installed host after the prepared procedure.
- §27 Stakes-aware review routing — high-stakes step declares plain --reviewers code (Significant Gap) — pass: all three code units retain deep routing; D4 explicitly preserves six-lens depth during bootstrap. See `skills/review-deep/core.md`'s high-stakes trigger paragraph.

## Blockers

None.

## Significant gaps

None remaining in the selected proposal. The D3 completion deadline can reject a
healthy slow review; D4 is a new bounded bootstrap exception. These are disclosed
decisions to assess in the proposal, not hidden equivalence claims.

## Missing items

None. Proposed implementation artifacts intentionally do not exist yet.

## Nice-to-haves

None. Issue numbers are intentionally blank until the reviewed plan is selected
for repo-sync; no issues or consumer flags were mutated by this review.

Auto-applied 0 fixes. Plan is ready for `/plan-wrap` and `/repo-sync` after proposal
review. Readiness does not authorize an unqualified host to execute a missing gate.
