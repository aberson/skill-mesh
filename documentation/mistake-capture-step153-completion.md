# Step 153 bounded completion

Execution decision, 2026-09-23. The operator selected completion of the preserved
mistake-capture implementation with this Codex session coordinating and Sol or
Terra building. This record applies only to Step 153 / issue #219. Step 154 remains
attended acceptance; AP, BR, M1, installations and unrelated work are outside it.

## Candidate and remaining work

The previous candidate was based on `f7cfe9743ed8d8ae6141d2f4ea25c14d562b37fc`.
Its original dirty worktree and all prior reports remain preserved. Five developer
iterations and four deep reviews are historical cost, not reset attempts. Review
four retained one actionable Nit: an ancestor-path change during an entry read
could be reported as absence. The fifth developer iteration already added the
ancestor recheck. Its review and exact-candidate acceptance remain unfinished.

The complete preserved patch is applied with Git's three-way merge onto
`110d916df9d46916fa7aeee19fefc2847b9f5476`, preserving the intervening Phase CD
distribution changes. No implementation rewrite is authorized by this resumption.

The operator subsequently approved an explicit local-filesystem trust boundary:
Git metadata is operator-controlled; path checks do not defend against another
process replacing its directories concurrently. Correct the false race-proof
claim and document that limitation without changing runtime logic. Normal helper
capture/read concurrency, private placement, atomic no-overwrite publication,
bounded reads and sanitized publication remain required. The confirmed race and
historical security Block remain recorded in the
[completion checkpoint](findings/mistake-capture-closure-2026-09-23.md).

## Models, review and limits

- Coordinator: the current Codex session. Builder: a fresh Sol child.
- Independent review: installed `review-deep`, code lenses, bound to
  `documentation/mistake-capture-plan.md:153`; six fresh direct children, scheduled
  within available host slots. Resolve capability roles to available models and
  record actual selections. No producer grades its own change.
- Current closure begins with the already-produced iteration 5. At most two
  further repair/review rounds may follow: cumulative ceiling 7. Historical
  NEEDS-WORK reports remain unchanged. No automatic restart resets this ceiling.
- Session window: 2026-09-24 02:06 UTC through 08:06 UTC, including final cleanup.
  One root-suite attempt, at most four hours, admitted only if cleanup fits before
  the session deadline. No concurrent root suite or automatic full-suite retry.
- A repeated defect triggers the existing structural diagnosis rule. Extra
  improvement ideas are follow-ups; concrete defects in this candidate are not
  suppressed to obtain PASS. A failed or timed-out gate remains incomplete/failed.

## Single-owner validation exception

This is the selected implementation of the operator-approved bounded completion
approach. It overrides duplicated candidate, post-merge, after-step and final-wrap
root-suite executions for this one step. It changes neither the full-suite command
nor the product behavior required by the original plan.

1. Regenerate the manifest and all three provider profiles. Run the focused helper
   tests once on the integrated candidate and check the diff. Record commands,
   exit codes, elapsed time and file identities; old timestamp-only receipts are
   historical evidence, not proof of this candidate.
2. Complete mechanical review checks and independent deep review before the
   expensive final gate. Review iteration 5 closes the pending implementation;
   further reviews focus on any repair and its affected assumptions. Preserve
   prior raw reports and deterministic aggregation; do not rewrite a verdict.
3. Exercise the normal installer into a disposable Codex home and the emitted
   helper against a disposable Git repository without resolving the source helper.
   This proves packaging and helper behavior, not native skill acceptance.
4. Freeze the complete integrated candidate and run **`python -m pytest`**, with no
   path argument, once. Its collection includes the distribution suite and all
   three production test roots outside `tests/`; a second complete distribution
   run is not an additional prerequisite. Save the real exit code and summary.
5. Land only after passing review and the full gate. Reuse that receipt for merge
   and closeout only after verifying the integration preserves all tested code,
   tests, configuration and packaged skill inputs, with an unchanged relevant
   environment. Administrative status/receipt changes must be explicitly listed;
   the receipt continues to name the commit actually tested. Changed tested inputs
   invalidate reuse and require a new decision, not an automatic second root run.
6. On failure, preserve the candidate and the specific remaining defect or missing
   evidence. Do not mark Step 153 DONE or close #219. On success, update the plan
   and issue once; retain Step 154 / #220 as pending attended work.

The installed Codex route must pass its capability checks in this session. Prior
Phase CD qualification alone is not a substitute. This record replaces the old
Claude-only launch direction for this selected continuation; it does not claim
runtime/full review or support on another Codex host.

## Bounded attempt outcome (2026-09-24)

Round 7 closing review passed all six lenses. The single root-suite attempt on
`ab8284cb8b0796aee1301f719899efd3eceaefc0` was stopped after 3 hours 10 minutes
when a pre-existing status assertion failed and release tests repeated the same
package suite. It is failed/incomplete, not a full-suite PASS. No retry or merge
followed. The candidate, raw evidence and proposed narrow test-maintenance patch
are preserved in the [completion checkpoint](findings/mistake-capture-closure-2026-09-23.md).
Further repair or a changed acceptance gate requires a new bounded decision;
this outcome does not reset either ceiling or mark Step 153 complete.

## LH-E1: operator-approved narrow closeout (2026-09-24)

After receiving the failed/incomplete full-gate result and the drafted stale-test
repair, the operator approved a 30-minute narrow closeout, then explicitly asked
to perform it before moving to Baseline releases. This is a scoped acceptance
exception for Step 153 only, overriding the full-gate requirement in this record,
the Step 153 Done when clause, and the repository's default gate for this landing.
It does not reset historical review counts or change future steps' requirements.

Window: **07:07:15 through 07:37:15 UTC on 2026-09-24**, including closeout.
One Sol developer applies the narrow Phase CD status-test repair; run only
`python -m pytest tests/package-integrity/test_codex_agent_isolation_contract.py -q`
once, capped at five minutes. One fresh independent Terra reviewer checks this
delta and the acceptance exception after the focused check passes. No new six-lens
round, root suite, package-wide suite, release run, installation or feature work
is admitted. Failure or deadline exhaustion preserves the candidate unfinished;
there is no automatic retry.

Acceptance combines the recorded round 7 six-lens PASS, unchanged executable
implementation and packaged inputs, prior helper/installer/provider evidence,
the new passing contract-file check, and the narrow closing review. The stale
test repair must retain the host-specific qualification boundary and independent
Claude-route checks. Source/test/config identity at merge must match the accepted
candidate; list administrative status/receipt changes separately.

If those conditions pass within the window, mark Step 153 accepted under LH-E1,
merge and push its preserved candidate, and close #219. Keep Step 154/#220 pending.
The earlier root run remains **failed/incomplete**, with the release/tail checks
unfinished and other possible failures unexcluded. Do not claim a new full-suite
PASS or an authenticated ADVANCE for a restarted historical controller.
