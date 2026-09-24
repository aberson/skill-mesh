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

## Bounded repair outcome

Integration commit: `43764f0ef334435073dc4172177bcf884283bf6d`. Sol's privacy repair
is `d7897f359ab00378dd447f464e2b25f21c1b0521`; the narrow runbook correction is
`308083d77d1d3456848df061204d9eb67d58329c`. The retained source archive is private,
offered text and distribution files are scanned, and `PUBLIC-SHA256SUMS` describes
the publishable subset. The private retained manifest still covers the full archive.
There is no source repin, new dependency or change to qualification requirements.

One focused invocation selected nine named publication/checksum/claims checks in
`tests/release/test_baseline_release.py`: **8 passed, 1 failed**, exit 1, 17.881
seconds process time. The failure was an undispositioned explanatory comment in
the existing prose-claims inventory. The developer stopped as instructed. The
coordinator then admitted one specific mechanical follow-up within the same time
budget: remove the unnecessary comment, correct a checksum-description string,
and rerun only the failed inventory check. It reported **1 passed in 0.15 seconds**,
exit 0, 1.536 seconds process time. The initial failed receipt remains unchanged;
the eight successful checks were not repeated. This is focused evidence, not a
new nine-test aggregate or full-suite result.

One fresh Terra reviewer examined the three-file privacy delta. It identified one
stale public-copy verification command in runbook section 7; its initial
NEEDS_WORK report is preserved. The coordinator corrected only that instruction,
and the same reviewer confirmed the finding resolved with no remaining findings
on the narrow delta. No new review campaign or test run followed that Markdown
correction. All 622 tracked files were unchanged during the initial review; only
the identified runbook correction followed it. This review does not certify the
entire inherited Step 147 implementation or qualify a release.

Private receipts live in `.build-step/br147-resume-20260924/`: input identities,
`focused-public-packet.json`, `focused-claim-followup.json`,
`closing-review-initial.json`, `closing-review-mutation-audit.json` and
`closing-review-finding-disposition.json`. The candidate is retained on
`build/br147-resume-20260924`, separate from main. Step 147/#207 remains unfinished.

## Required next decisions and evidence

The operator was asked whether the first daily toolkit release should use current
main, including the Codex route repair and Step 153, while preserving the dated
September 13 snapshot, or keep the original pinned release source. **No answer or
repin is assumed.** Source selection precedes exact-source qualification.

The selected source still needs attributable representative cross-family review
and the existing qualification evidence. Admit one explicitly bounded real release
attempt only after that proof is available; its nested root/staged checks must be
included in the total budget. No full test suite or real release operation ran in
this resumption. Step 149 prepares the daily-profile split; Step 150 remains the
separate live-adoption decision after a concrete preview.
