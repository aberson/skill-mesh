# Step 153 completion checkpoint

Initial reviewed candidate: `48c926f392a6a4b06212bd92037ffe637c5f3b2b`, based on
`110d916df9d46916fa7aeee19fefc2847b9f5476`. The preserved implementation was
integrated with current main without changing its behavior. The original dirty
worktree remains untouched. This is an unfinished build, not a release certificate.

## Initial checkpoint evidence (historical)

- Fresh Sol developer verification: existing ancestor-reparse repair is present;
  no implementation change needed. Intervening Phase CD distribution tests retained.
- Manifest generation: exit 0. All three provider builds: exit 0, 17.838 seconds.
- Focused helper suite: **100 passed in 173.08 seconds**, exit 0.
- Normal installer into a disposable Codex home, followed by the emitted helper's
  record/replay/pending/disposition cycle: **PASS in 94.15 seconds**; fixtures removed.
- Diff check: exit 0. No configured lint/typecheck gate; the installed mechanical
  pre-pass records unavailable ruff and unconfigured mypy, without inventing a PASS.
- Six independent fresh Terra lenses: correctness, bugs, test-quality, style and
  plan-conformance PASS. Security has one Block. Deterministic installed aggregation
  returned **NEEDS-WORK**. A malformed initial style response was preserved as
  invalid and replaced by one fresh, valid report; no verdict was rewritten.
- A 1.93-second synthetic Windows-junction reproduction confirmed the security
  finding. Only disposable fixture paths were affected and all were removed.

At this initial checkpoint the full repository-root suite had **not started**.
The final bounded attempt is recorded below. There is no full-suite PASS, merge,
issue closure, live profile activation or Step 154 acceptance.

## Approved decision: local filesystem trust

The guard in `_shared/lesson_observations.py` checks path components and resolved
containment, then publication opens a pathname. A process able to replace the
private inbox directory between those operations can redirect the write outside
the common Git directory. The module's statement that a swap between inspection
and opening still cannot move a record out of the clone is therefore false.

**Operator-approved first-version boundary (2026-09-23):**

> The helper operates in operator-controlled Git metadata. Its symlink/reparse
> and containment checks inspect the filesystem state before access; they are not
> a security boundary against another process replacing directories concurrently.
> Hostile concurrent mutation of Git metadata is outside this version's support.
> Concurrent capture and reading through the helper remain supported. Private
> storage placement, no-overwrite atomic publication, bounded reads and sanitized
> publication rules remain requirements.

The operator approved this boundary after reviewing the confirmed race and the
alternative of implementing race-resistant storage now. Correct the false claim
and document this boundary consistently, then obtain a closing review of the
changed assumptions. Preserve this historical Block and its reproduction; do not
relabel the historical review as passing. This is an accepted scope limitation,
not a claim that the directory-swap race was repaired.

The alternative is race-resistant filesystem access before first delivery. That
requires an explicit implementation decision and revised scope; it is not another
line-level recheck, which would merely move the same race window.

## Final bounded attempt (2026-09-24)

Final reviewed and tested candidate:
`ab8284cb8b0796aee1301f719899efd3eceaefc0`, on branch
`build/lh153-close-20260923`. The two approved correction passes changed comments,
docstrings and documentation only; executable logic is unchanged from the
initial candidate. All provider profiles were rebuilt after the final correction.
The earlier focused helper and installed-helper receipts were retained.

Round 6 stopped non-passing after a remaining wording Nit; its incomplete record
and an invalid context-contaminated response remain preserved. Final round 7 used
six fresh independent Terra reviewers: correctness, bugs, security, test-quality,
style and plan-conformance all PASS. The installed deterministic aggregate is
PASS. The accepted trust boundary does not repair or erase the historical race.

The single root command, `python -m pytest`, began at 03:40:37 UTC and ended at
06:51:11 UTC: **3 hours 10 minutes 33.831 seconds**. It collected 1,777 cases.
The coordinator stopped the owned test process tree after known failures rather
than allowing further release cases to repeat a known-failing package suite.
The wrapper recorded exit 1 / FAIL. Progress markers showed **1,657 passes and
two failures**, with no error markers. These are partial progress observations,
not a completed pytest summary; the interrupted run produced no final traceback.
All 612 tracked inputs remained unchanged during this attempt. All owned test
processes were stopped; there was no full-suite retry.

The identified package failure is
`test_cd_status_retains_the_pending_qualification_boundary` in
`tests/package-integrity/test_codex_agent_isolation_contract.py`. It still requires
the phrase `unqualified pending Step 156`, although the Phase CD plan correctly
records the observed host qualification as complete. Read-only comparison shows
both that test file and the Phase CD section are unchanged from starting main
`110d916df9d46916fa7aeee19fefc2847b9f5476`; the required obsolete phrase is absent
there too. This inconsistency predates Step 153.

The second failure occurred in `test_release_builds_stages_and_checksums`.
`tools/release.ps1` invokes the whole package-integrity suite, and its staged
status section and test were identical to the known-failing inputs. This supports
a cascading failure; without the final traceback it does not exclude another
release failure. Further release cases and the router/smoke/telemetry tail were
not completed.

The [bounded execution record](../mistake-capture-step153-completion.md) requires
both passing review and a passing full gate before landing. Its seven-round
ceiling and single-root-attempt allowance are exhausted. **Step 153 remains
unfinished and unmerged; #219 stays open.** Step 154/#220 remains pending. No
additional repair, review, installation, test cycle or gate waiver was performed.

Private evidence under `.build-step/closure-20260923/` includes the final
`review-r7/2026-09-24T03-40-25.json` aggregate, `full-gate-receipt.json`,
`full-gate.log`, `stop-on-known-failure.json`,
`qualification-status-diagnostic.json` and `process-audit.md`.

A private `proposed-status-test-fix.patch` is drafted but **not applied or tested**.
It removes the obsolete pending-status requirement while retaining checks that
qualification is host-specific and independent of the Claude route. A subsequent
decision can authorize this narrow test repair and define a short, explicit
acceptance budget. Targeted checks would be an exception to the current full-gate
requirement, not a retrospective full-suite PASS.

The process lesson is that one root invocation can still multiply work internally:
release cases launch the package suite again. The coordinator's admission plan
should have accounted for that duplication and arranged prompt failure reporting.
No extra feature scope was added in the closing passes, but repeated six-lens
reviews of wording changes also added ceremony. These are follow-up observations,
not authorization to expand this completion attempt into an infrastructure build.
