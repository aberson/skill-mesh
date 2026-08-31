# Phase RD — Restore review-deep calibration and resume the Codex capability slice

## 1. What This Is

This is the executable bridge between the blocked review-deep package work in issue #177,
the paused capability-conditioned Codex adapter slice in issue #165, and the already-approved
pre-provider C2E build. It restores the mandatory review-deep calibration package safely, closes
the proof gaps that stopped the rejected candidate, and then resumes only the review-deep adapter
slice needed by C2E's declared `--reviewers deep` gates.

This plan is a remediation overlay, not a new Phase IS product unit. It does not amend the accepted
Phase IS completion plan, edit the frozen UAT, install a provider profile, or authorize any
certificate, Code Integrity/App Control/AppLocker, Secure Boot, boot configuration, SDK/WDK,
driver, provider-resource, or genuine-host action.

## 2. Authority and Verified Starting State

- Repository: `C:\Users\abero\dev\skill-mesh`, branch `main`.
- Draft baseline: `4b9b0aa065ac57f9b70a0cb1773e2d6c3e43d420`; execution must reverify HEAD,
  cleanliness, and `HEAD...origin/main` immediately before dispatch.
- Parent remediation: issue #177, including stop comment
  `https://github.com/aberson/skill-mesh/issues/177#issuecomment-5475661626`.
- Parent adapter audit: issue #165. The broader audit remains open after this plan; only the
  review-deep slice is in scope.
- Rejected package donor, retained read-only:
  `C:\Users\abero\dev\skill-mesh-build-step-review-deep-calibration-assets-20260830224727`,
  branch `build-step-review-deep-calibration-assets-20260830224727`, frozen changed-path digest
  `1c5b3650b7073e9d4ce4d660a354dfe426ea30e0e8b7f12ef4cc217561d2d033`.
- Paused adapter donor, retained read-only:
  `C:\Users\abero\dev\skill-mesh-build-step-review-deep-capability-20260830220844`,
  branch `build-step-review-deep-capability-20260830220844`.
- Trusted legacy source: coding-root repository `C:\Users\abero\dev`, immutable commit
  `3a7ae33d09b9b26edb291e2db0cdaca1022ed643`.

The two donor worktrees are diagnostic evidence only. Every step starts from current `main` in a
fresh worktree and re-proves its behavior. Do not merge, cherry-pick, or treat either donor's tests,
reports, generated files, or untracked files as acceptance evidence.

## 3. Locked Inputs and Ownership Model

The trusted commit contains exactly 39 tracked paths below
`.claude/skills/review-deep/evals/**` and `.claude/skills/review-deep/scripts/**`. Import those
paths from Git object bytes, never from the coding-root working tree. Canonical destinations are
the corresponding paths below `skills/review-deep/`.

The provenance ledger records, for every imported path, the source repository identity, source
commit, source relative path, source Git blob ID, source byte SHA-256, canonical relative path, and
current byte SHA-256. Thirty-eight current files remain byte-identical to the pinned source. The
pinned `scripts/lint_prepass.sh` has known option-injection and stdin-loss defects, so it is the one
explicit security derivative: its ledger row retains the upstream blob/hash facts and separately
records the current derivative hash and the fixed invariants. No document or test may claim that
all 39 current files equal their pinned blobs.

`package_assets` is an exact-file manifest contract distinct from migration-only
`support_assets`. It never accepts directory globs. Distribution generation validates the entire
declared set before mutating an existing output and emits a deterministic, marker-bearing
`package-assets.index.md` that binds provider, skill, each raw relative path, and each raw SHA-256.

The installer owns a raw asset only when the exact manifest/index/ledger path and byte-hash chain
authorizes it. WAL version 2 binds raw path, hash, provider, skill, index path, and index hash.
Mutation ordering is:

1. validate incoming and prior authority completely;
2. publish the fail-closed WAL;
3. write incoming raw leaves;
4. remove stale raw leaves under frozen prior authority;
5. apply ordinary generated-header changes;
6. remove the old package index;
7. activate the new package index;
8. verify the complete target/index closure;
9. publish the normal ledger and remove the WAL.

Pending raw bytes authorize only an exact same-source retry. A changed-source retry or uninstall
before index activation is a true no-mutation refusal. Recovery may not publish a partial normal
ledger or remove the WAL while the active index still describes a different package state.

## 4. Development and Gate Commands

- Dependency install: none beyond the repository's existing Python/PowerShell/Bash toolchain;
  fresh worktrees use the existing environment and must not install workstation-wide software.
- Development server: N/A; this is a CLI/distribution change with no UI or network service.
- Distribution build:
  `powershell -NoProfile -NonInteractive -File tools/build-distributions.ps1 -Provider all`.
- Manifest generation/check: `python tools/gen_manifest.py`, followed by a no-unexpected-diff
  check of generated tracked artifacts.
- Focused tests: the touched package-integrity, distribution, and calibration suites named by each
  step.
- Full gate: `python -m pytest` from repository root for every step and again at phase end.
- Lint/typecheck: the repository declares no separate project-wide lint or typecheck command for
  this slice. Run PowerShell parser checks for both touched `.ps1` files, `bash -n` for touched shell
  scripts, and `git diff --check`.
- Live install/substrate smoke: deliberately deferred to the already-authoritative C3/C4 disposable
  host acceptance. All tests here use explicit disposable homes and staging paths; real host profiles
  are forbidden targets.

Before Step 1, the build-phase parent must pass the Codex acceptance probe for explicit no-history
sibling dispatch, parent-private state, caller-scoped verdict service, authenticated outside-worktree
sidecar, and parent-only verdict classification. A missing or inconclusive capability stops visibly
with `required_tool_missing` before any developer dispatch.

## 5. Build Steps

### Step 1: Securely land the review-deep package-asset capability

- **Status:** PENDING
- **Problem:** Add planted regressions for interrupted pure raw-asset deletion and both
  `lint_prepass.sh` defects, then implement the smallest complete calibration package, manifest/index,
  deterministic builder, and installer state machine that makes those regressions pass atomically.
- **Type:** code
- **Issue:** #178
- **Files:** `.gitattributes`; `documentation/review-deep-calibration-provenance.json`;
  `skills/review-deep/evals/**`; `skills/review-deep/scripts/**`;
  `_shared/calibrate_judge.py`; `_shared/test_calibrate_judge.py`;
  `skills/review-deep/core.md`; `config/skill-manifest.json`; `tools/gen_manifest.py`;
  `tests/package-integrity/expected_inventory.json`;
  `tests/package-integrity/test_manifest_contract.py`; `tools/build-distributions.ps1`;
  `tools/install-skill-mesh.ps1`; `tests/distributions/test_distributions.py`;
  `documentation/architecture.md`.
- **Existing context:** issue #177 owns the complete requirement. Import only the 39 Git objects
  at the pinned coding-root commit. Preserve the accepted Phase IS plan, frozen UAT, C2V/C2A
  artifacts, current real profiles, and both donor worktrees. The raw corpus, manifest declaration,
  emitted index, builder, and installer authority land together because any smaller production split
  creates either undistributable payload or unsafe ownership semantics.
- **Produces:** exact `package_assets` declarations; provenance with one explicit lint derivative;
  deterministic package index/output; calibration package-directory resolution; safe raw-asset WAL
  lifecycle; fixed lint prepass with argument terminators and an stdin-preserving parser; targeted
  planted-negative tests.
- **Done when:** the pure-removal, diff-filename option-injection, and piped-output regressions are
  demonstrated against the defective shape and pass after the repair; frozen-source provenance is
  recomputed from Git objects; missing/forged/misbound index, foreign markerless peer, pending
  changed-source, and pending uninstall refuse before mutation; disposable Claude/GPT/Codex
  install/reinstall/uninstall paths pass; PowerShell/Bash parsers, focused suites, repo-root
  `python -m pytest`, and `git diff --check` pass without a count regression.
- **Flags:** --isolation worktree --reviewers code --max-iter 3
- **Depends on:** none; this is the bootstrap that restores mandatory review-deep calibration.
- **Review routing:** deliberate bootstrap exception. This high-stakes installer step cannot invoke
  `--reviewers deep` because the missing package is the defect being repaired. Use all five fresh
  code-review lenses and the parent-only deterministic verdict gate; zero High/Medium findings are
  required before merge.

### Step 2: Close the package-asset proof matrix

- **Status:** PENDING
- **Problem:** Add every evidence-grade planted negative absent from the rejected candidate, using
  Step 1's landed contract. Change production code only when a new negative proves a concrete defect.
- **Type:** code
- **Issue:** #179
- **Files:** primarily `tests/distributions/test_distributions.py`,
  `tests/package-integrity/test_manifest_contract.py`, and `_shared/test_calibrate_judge.py`;
  production files from Step 1 only when a new planted negative proves a defect.
- **Existing context:** reviewers rejected the donor for incomplete proof of raw-only V4 removal,
  whole-tree no-mutation, unsafe/reparse/non-file inputs, installed target tamper, builder failure
  atomicity, emitted-profile calibration, and exact Codex output closure. File-only snapshots are
  insufficient because an erroneous empty directory is a mutation.
- **Produces:** planted negatives covering exact V4 raw-only removal in pending and post-activation
  states; directory-and-byte true no-mutation; unsafe/rooted/backslash/dot, duplicate/case-collision,
  reserved-output, missing/non-file/reparse, source-drift/emission/promotion failures; installed raw
  and index tamper; canonical plus all three emitted-profile calibration; deterministic exact output
  path/hash closure with no extras, including Claude/GPT/Codex counts `168/165/165` for the candidate
  this plan creates.
- **Done when:** each new test has a non-vacuous planted-negative or mutation witness; every listed
  case passes; Step 1 behavior changes only where a test proves a defect; all five fresh code-review
  lenses report zero High/Medium findings; PowerShell/Bash parsers, focused suites, repo-root
  `python -m pytest`, manifest no-unexpected-diff, deterministic `-Provider all` rebuild, and
  `git diff --check` pass without a count regression.
- **Flags:** --isolation worktree --reviewers code --max-iter 3
- **Depends on:** Step 1 checkpoint merged and its complete package-asset contract present.
- **Review routing:** use five fresh code-review lenses because issue #177 explicitly requires that
  evidence shape. The parent alone aggregates findings and owns the final verdict.

### Step 3: Capability-condition the Codex review-deep adapter

- **Status:** PENDING
- **Problem:** Replace the provider-wide claim that Codex lacks a fresh-context primitive with a
  runtime capability contract, while preserving visible `required_tool_missing` behavior on ordinary
  CLI hosts and every missing, failed, or inconclusive probe.
- **Type:** code
- **Issue:** #180
- **Files:** `skills/review-deep/providers/codex.md`;
  `documentation/providers/codex.md`; `documentation/providers/README.md`;
  `tests/package-integrity/test_review_deep_codex_contract.py`; generated provider output only as
  disposable verification evidence.
- **Existing context:** issue #165 owns the broader adapter audit and must remain open. The paused
  donor contains a proposed four-file slice, but it predates Steps 1-2 and is not landable authority.
  Re-derive the change from current main, using the donor only as read-only diagnostic evidence.
  `skills/review-deep/core.md` still owns the independent-lens and deterministic aggregation contract.
- **Produces:** capability-conditioned Codex adapter wording; non-mutating host probe contract;
  parent-captured complete candidate/worktree mutation baseline; fresh sibling lens dispatch;
  parent-only aggregation, sidecar, and final-verdict authority; planted negatives for absent or
  weakened boundaries; matching active provider documentation.
- **Done when:** the adapter requires explicit callable-schema inspection plus a non-mutating proof
  that a no-history child cannot read parent session state; all applicable lenses are parent-spawned
  fresh siblings and cannot receive earlier lens results; unexplained candidate/worktree mutation
  fails closed; no child can write or classify the final sidecar; ordinary/inconclusive hosts halt
  with `required_tool_missing`; focused contract, package-integrity, emitted Codex profile,
  mandatory calibration, repo-root `python -m pytest`, and `git diff --check` pass; a fresh
  review-deep run reports zero High/Medium findings.
- **Flags:** --isolation worktree --reviewers deep --max-iter 3
- **Depends on:** Step 2 complete, so canonical and emitted review-deep packages pass mandatory
  calibration.

## 6. Serialization and Issue Lifecycle

The steps are strictly sequential:

```text
Step 1 package capability -> Step 2 proof closure -> Step 3 adapter resume
```

No pair is parallel-safe. Step 2 consumes Step 1's emitted package and installer state model. Step 3
requires the calibration restored and proven by Steps 1-2 before its mandatory deep review can run.

Each step receives its own linked tracking issue during repo-sync. Passing a step may close that
step issue. After Step 2 passes, close parent #177 with links to both reviewed commits. Parent #165
remains open after Step 3 because it owns the remaining adapter inventory; add the Step 3 result as
a progress comment rather than closing #165.

## 7. Stop Conditions and Recovery

Before dispatch, stop for a missing pinned commit/path, unresolved 39-file provenance mismatch,
required change to the accepted Phase IS plan or frozen UAT, dirty/diverged main, or failed host
acceptance probe.

During build-phase, use only its defined halt classes. In particular, preserve the fresh worktree and
stop on a blocked reviewer verdict, full-gate/count regression, overlapping upstream advancement,
same-bug-shape stop-and-audit trigger, or worktree merge conflict. Never patch or land the rejected
donor in place.

If a step fails after modifying only a fresh worktree, main and both donors remain unchanged. If a
post-merge root gate fails, write the authenticated fail-closed verdict before returning and do not
advance the plan status.

## 8. Phase Acceptance and Automatic Continuation

This remediation phase is complete only when all three step issues are closed, all three plan statuses
are `DONE`, parent #177 is closed, parent #165 remains open with the review-deep slice recorded, main
is clean and synchronized, the final repo-root suite passes, and no forbidden local-host surface or
sealed Phase IS artifact changed.

After completion, start a separate build-phase invocation for Steps 1-3 of
`documentation/phase-is-disposable-c2n-c4-environment-plan.md`. Those are the only pre-provider C2E
code steps. Stop at C2E Step 4, whose `Type: wait` contract requires the operator's provider,
Windows-license, artifact-retention, authentication, cost, and publication-broker selection. Do not
provision anything, install/restart hosts, or cross that wait in this run.
