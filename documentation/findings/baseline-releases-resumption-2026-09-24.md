# Baseline releases bounded resumption - 2026-09-24

The operator selected Baseline releases after Step 153 was accepted and pushed at
`7ae573bd1c610f8ba1d8e39d66f1f7a915973b36`. This checkpoint resumes Step 147/#207 only;
Steps 148-152 and live adoption remain pending.

## Preserved work and integration

- Historical BR planning/checkpoint branch: `3e01ea45d082b5b6a67079d00328986a6817c840`.
- Preserved run-2 iteration-3 candidate: `c88391ba776ad9293b153391db325b8915d82236`.
- Current-main integration base: `7ae573bd1c610f8ba1d8e39d66f1f7a915973b36`.
- All three candidate implementation/test/runbook Git blobs were carried over
  unchanged. The only merge conflict was plan status; both the current main
  milestones and the Baseline track are retained. Old worktrees remain untouched.
- The candidate adds 2,743 implementation lines, 3,355 test lines and a 537-line
  runbook. Size alone is not a defect, but this is a substantial qualification tool.

Earlier developer evidence reports `tests/release`: 205 passed in 1,002 seconds,
and `tests/package-integrity`: 420 passed in 59.43 seconds, plus mutation checks.
These are dated reports, not reruns on the integrated tree. No iteration-3 deep
review or completed root gate was found. Prior unsuccessful iterations remain
historical cost; this resumption does not reset them.

## Bounded read-only readiness review

A fresh Terra reviewer inspected the preserved candidate against the previous
findings. Named attestation, omitted cross-family evidence, Markdown escaping and
failed-stage retention repairs are present. This is advisory readiness evidence,
not a six-lens PASS or release qualification.

A concrete publication defect remains: `source.zip` is included in the public
packet, while its contents are not scanned for user-specific paths. The exact
retained toolkit source `79a985a38a2ca413da43014b8b50ae4dab67143c` contains such paths.
The public-packet promise therefore exceeds its checks. Preserve the archive and
its source identity; private retention and public distribution are separate.

Qualification evidence is also absent for the required independent representative
cross-family review of that exact source, with model-resolution evidence and a
named attestation. The tool correctly does not manufacture that proof.

## Next bounded implementation action

Within the operator's request to work on this plan, repair only public-packet
eligibility: retain the exact source archive privately and check the files offered
for publication. Keep the source commit, retention/checksum behavior and existing
qualification requirements. Use one Sol developer pass, focused publication tests,
and one fresh narrow Terra review, with a 15-minute ceiling and no automatic retry.
This repair does not by itself complete Step 147 or replace its required deep
review/root gate. Record a failure or deadline limit and preserve the candidate.

No root suite, whole release suite, real qualification invocation, publication,
profile activation or lab work is admitted in this bounded slice. The real release
entry already invokes source-root pytest plus staged release, and release tests
repeat package-integrity internally. Obtain missing review evidence and decide the
exact-source gate budget before launching those expensive commands. The old
automatic 147-149 span remains suspended.
