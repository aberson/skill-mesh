# Phase RD — Restore review-deep calibration and resume the Codex capability slice

## 1. What This Is

This is the executable bridge between the blocked review-deep package work in issue #177,
the paused capability-conditioned Codex adapter slice in issue #165, and the already-approved
pre-provider C2E build. It restores the mandatory review-deep calibration package safely, closes
the proof gaps that stopped the rejected candidate, and then resumes only the review-deep adapter
slice needed by C2E's declared `--reviewers deep` gates.

This plan is a remediation overlay, not a new Phase IS product unit. It does not amend the accepted
Phase IS completion plan or edit the frozen user acceptance test (UAT). Steps 1-3 never install a
real provider profile.
Step 4 is a separate operator gate that may activate only the reviewed Codex profile after its
disposable rehearsal and a fresh, target-specific approval; the plan itself does not grant that
approval. No step authorizes any certificate, Code Integrity/App Control/AppLocker, Secure Boot,
boot configuration, SDK/WDK, driver, provider-resource, or genuine driver-test-host action.

## 2. Authority and Verified Starting State

- Repository: the checkout returned by `git rev-parse --show-toplevel` (remote
  `aberson/skill-mesh`), branch `main`; never persist its machine-specific absolute path.
- Initial reviewed planning baseline: `6a9847a4d87edb9eaea9f2bb017527389d41bd08`; execution must
  reverify HEAD, cleanliness, and `HEAD...origin/main` immediately before dispatch.
- Parent remediation: issue #177, including stop comment
  `https://github.com/aberson/skill-mesh/issues/177#issuecomment-5475661626`.
- Parent adapter audit: issue #165. The broader audit remains open after this plan; only the
  review-deep slice is in scope.
- Rejected package donor, retained read-only and resolved only through
  `git worktree list --porcelain`: branch
  `build-step-review-deep-calibration-assets-20260830224727`, frozen changed-path digest
  `1c5b3650b7073e9d4ce4d660a354dfe426ea30e0e8b7f12ef4cc217561d2d033`.
- Paused adapter donor, retained read-only and resolved through the same worktree registry: branch
  `build-step-review-deep-capability-20260830220844`.
- Trusted legacy source: the local `aberson/coding-root` repository (resolve its Git root with
  `git -C .. rev-parse --show-toplevel` from the canonical workspace, then verify its remote),
  immutable commit `3a7ae33d09b9b26edb291e2db0cdaca1022ed643`.

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
current byte SHA-256. Thirty-six current files remain byte-identical to the pinned source. Three
rows are explicit derivatives: `scripts/lint_prepass.sh` records its option-injection,
stdin-preservation, and exit-0 help invariants; `scripts/auth_gate_probe.sh` records its exit-0 help
invariant; and `scripts/README.md` records the matching help contracts. Each derivative retains the
upstream blob/hash facts and separately records its current hash and exact reason. Only
`lint_prepass.sh` is a security derivative. No document or test may claim that all 39 current files
equal their pinned blobs or retain the superseded 38+1 split.

`config/model-tier-map.json` remains the repository-wide authoritative model-tier map. Because a
host loads `review-deep` from a self-contained installed skill directory, Step 1 also creates the
package-local snapshot `skills/review-deep/config/model-tier-map.json`. Its bytes and parsed JSON
must equal the authoritative file at the same candidate commit. The manifest declares that snapshot
as the fortieth exact raw `review-deep` package asset, and emitted instructions define
`config/model-tier-map.json` relative to the directory containing the loaded `SKILL.md`/`core.md`.
This is a narrow `review-deep` repair, not a claim that every installed skill now receives a global
configuration tree. A mismatch or missing snapshot fails generation and package validation.

The attended activation uses three closed issue records: a disposable rehearsal, a new
target-specific approval, and a final activation seal. The sole schema, canonical-byte, digest,
REST reread/selection, command, and cleanup authority is
`documentation/phase-rd-review-deep-activation-runbook.md`; the Step 4 executor reads it in full.
In summary, the rehearsal binds the reviewed candidate, 166-path distribution, disposable results,
and a non-disclosing active-home ID; the approval repeats that tuple plus the returned rehearsal
comment ID; and the seal repeats both predecessors plus the installed closure, inspector, help,
calibration, capability, protected-blob, and root-gate results. No record contains a credential,
private path, or mutable staging locator.

`package_assets` is an exact-file manifest contract distinct from migration-only
`support_assets`. It never accepts directory globs. Distribution generation validates the entire
declared set before mutating an existing output and emits a deterministic, marker-bearing
`package-assets.index.md` that binds provider, skill, each raw relative path, and each raw SHA-256.

The installer owns a raw asset only when the exact manifest/index/ledger path and byte-hash chain
authorizes it. Write-ahead log (WAL) version 2 binds raw path, hash, provider, skill, index path, and
index hash.
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
- Live install/substrate smoke: Steps 1-3 use only explicit disposable homes and staging paths; real
  host profiles are forbidden targets. Step 4 supplies the separately authorized active-profile
  smoke needed by current downstream `review-deep` consumers. It may run only after all code steps
  are reviewed and pushed, and only after its own explicit operator approval.

Before Step 1, the build-phase parent must pass the Codex acceptance probe for explicit no-history
sibling dispatch, parent-private state, caller-scoped verdict service, authenticated outside-worktree
sidecar, and parent-only verdict classification. A missing or inconclusive capability stops visibly
with `required_tool_missing` before any developer dispatch.

## 5. Build Steps

### Step 1: Securely land the review-deep package-asset capability

- **Status:** PENDING
- **Problem:** Add planted regressions for interrupted pure raw-asset deletion, both
  `lint_prepass.sh` defects, exit-0 help for both shell helpers, and installed tier-map resolution;
  then implement the smallest complete calibration package, manifest/index, deterministic builder,
  and installer state machine that makes those regressions pass atomically.
- **Type:** code
- **Issue:** #178
- **Files:** `.gitattributes`; `documentation/review-deep-calibration-provenance.json`;
  `skills/review-deep/evals/**`; `skills/review-deep/scripts/**`;
  `skills/review-deep/config/model-tier-map.json`;
  `_shared/calibrate_judge.py`; `_shared/test_calibrate_judge.py`;
  `skills/review-deep/core.md`; `config/skill-manifest.json`; `tools/gen_manifest.py`;
  `tests/package-integrity/expected_inventory.json`;
  `tests/package-integrity/test_manifest_contract.py`; `tools/build-distributions.ps1`;
  `tools/install-skill-mesh.ps1`; `tests/distributions/test_distributions.py`;
  `documentation/architecture.md`; `documentation/providers/gpt.md`;
  `documentation/providers/codex.md`; `documentation/providers/README.md`.
- **Existing context:** issue #177 owns the complete requirement. Import only the 39 Git objects
  at the pinned coding-root commit. Preserve the accepted Phase IS plan, frozen UAT, C2V/C2A
  artifacts, current real profiles, and both donor worktrees. The raw corpus, manifest declaration,
  emitted index, builder, and installer authority land together because any smaller production split
  creates either undistributable payload or unsafe ownership semantics.
- **Produces:** exact `package_assets` declarations for the 39 imported leaves plus the hash-bound
  package-local tier-map snapshot; provenance with 36 byte-identical imports and three explicit
  derivatives; deterministic package index/output; backward-compatible calibration
  package-directory resolution through an explicit `--skill-dir <path>` option (while retaining
  the existing `--skill <name>` interface); safe raw-asset WAL lifecycle; fixed lint prepass with
  argument terminators and an stdin-preserving parser; exit-0 usage entry points for both shell
  helpers; targeted planted-negative tests.
- **Done when:** the pure-removal, diff-filename option-injection, and piped-output regressions are
  demonstrated against the defective shape and pass after the repair; frozen-source provenance is
  recomputed from Git objects with the exact 36+3 disposition; `python aggregate.py --help`,
  `bash lint_prepass.sh --help`, and `bash auth_gate_probe.sh --help` print usage and exit 0 from the
  canonical package, every emitted profile, and every disposable installed profile; the tier-map
  snapshot is byte- and JSON-equal to the authoritative root map and resolves from those same
  package shapes; canonical, emitted, and disposable installed calibration calls use the exact
  `--skill-dir` package root rather than relying on repository-relative discovery;
  missing/forged/misbound index, foreign markerless peer, pending changed-source,
  and pending uninstall refuse before mutation; disposable Claude/GPT/Codex
  install/reinstall/uninstall paths pass; PowerShell/Bash parsers, focused suites, repo-root
  `python -m pytest`, and `git diff --check` pass without an unexplained count regression.
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
  path/hash closure with no extras, including Claude/GPT/Codex counts `169/166/166` for the candidate
  this plan creates: frozen baseline `128/125/125` plus 40 raw assets (39 imported corpus leaves and
  one tier-map snapshot) plus one generated package index. The prior `168/165/165` estimate omitted
  the tier-map snapshot and is deliberately superseded rather than silently tolerated.
- **Done when:** each new test has a non-vacuous planted-negative or mutation witness; every listed
  case passes; canonical, emitted, and disposable installed packages calibrate against the complete
  golden corpus using explicit package-directory resolution; installed tier-map/index/raw hashes and
  all three help entry points are re-proved; Step 1 behavior changes only where a test proves a
  defect; all five fresh code-review lenses report zero High/Medium findings; PowerShell/Bash
  parsers, focused suites, repo-root `python -m pytest`, manifest no-unexpected-diff, deterministic
  `-Provider all` rebuild, and `git diff --check` pass at the exact `169/166/166` closure.
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

### Step 4: Activate and prove the reviewed Codex package

- **Status:** PENDING — hard wait gate; Steps 1-3 do not authorize this install
- **Problem:** The reviewed canonical repair does not update the generated `review-deep` package in
  the active Codex discovery home, so current consumers still cannot run their mandatory deep lane.
- **Type:** wait
- **Issue:** #181
- **Existing context:** `Type: operator` is deliberately not used here: build-phase defers a
  non-code-producing operator step into its phase-end UAT bundle and continues. `Type: wait` is the
  required serialization barrier that halts after the reviewed code steps and leaves activation to
  a separately authorized attended run. The earlier Phase IS C0A (active-profile activation) stage
  is already `DONE` and binds a different C0R (source repair) commit/distribution, so it cannot
  authorize or certify these new bytes.
- **Files:** no production source file. Read-only inputs are the exact reviewed `main` commit,
  `config/skill-manifest.json`, `tools/probe-codex-skills.ps1`, and
  `tools/inspect-host-install.ps1`, plus the complete
  `documentation/phase-rd-review-deep-activation-runbook.md`; bounded writes are one proven-empty
  disposable staging root, one disposable home, the explicitly approved active Codex home through
  `tools/install-skill-mesh.ps1`, and the step issue's evidence comments. Only after the remotely
  reread seal may status-only edits mark this step in this plan and `plan.md` as `DONE`.
- **Prerequisites:** Steps 1-3 are `DONE`; their reviewed commits are pushed; `main` is clean and
  synchronized; a fresh root gate passes; the Phase IS plan, frozen UAT, and C2V/C2A artifacts match
  their pre-phase blobs; and the operator authorizes beginning the attended disposable rehearsal.
  Active-home approval is deliberately not a prerequisite: it is a second, target-specific decision
  taken only after the rehearsal record exists.
- **Actions:** read and execute §§2-8 of
  `documentation/phase-rd-review-deep-activation-runbook.md` exactly. In summary, bind the candidate
  commit/tree and create unique absent staging/home paths named
  `$rdStage` and `$rdDisposableHome` below the platform temp directory; build only that commit's
  Codex profile with `-Provider codex -OutputDir $rdStage`; verify the exact 166-path/index/hash
  closure and package-local tier map; install and reinstall against the disposable home through
  `tools/install-skill-mesh.ps1 -Provider codex -Home $rdDisposableHome -DistDir $rdStage` (the
  verified stage is mandatory; an on-the-fly rebuild is forbidden), inspect after each install, then
  uninstall; run package calibration plus all three help commands from both staged and installed
  packages; prove the disposable uninstall leaves no ledger-owned files; resolve the active home as
  `$rdActiveHome` with `tools/probe-codex-skills.ps1`; stop on any collision; publish and reread the
  bound rehearsal record; display the exact active path and request a new target-specific approval;
  publish and reread `PhaseRdActivationApprovalV1`; then install through
  `tools/install-skill-mesh.ps1 -Provider codex -Home $rdActiveHome -DistDir $rdStage` without
  `-Force` or `-ForceShared`; inspect and hash the active ledger/tree; start a fresh Codex context and
  repeat the non-mutating capability probe, calibration, and helper-entry-point checks; publish and
  reread `PhaseRdActivationSealV1`.
- **Produces:** a commit-bound disposable rehearsal record, target-specific approval record, and
  active-profile activation seal in the step issue; one post-seal status-only commit; no product
  source artifact and no direct-copy installation path.
- **Done when:** the active ledger owns the exact reviewed 166-file Codex closure with zero stale,
  unledgered, missing, or hash-mismatched leaves; installed calibration passes against the complete
  golden corpus; all three installed help commands print usage and exit 0; a fresh Codex context
  returns the supported capability verdict and can enter `review-deep` without
  `required_tool_missing`; the approval record binds the returned rehearsal comment ID; and the
  final activation seal is remotely reread with the reviewed commit/tree, distribution and installed
  closure digests, active-home ID, approval comment ID, installer/inspector results, helper exit
  codes, calibration result, fresh-context result, and root-gate result unchanged.
- **Stop conditions:** missing operator approval; ambiguous or changed active home; dirty/diverged
  source; candidate/hash drift; non-empty staging path; malformed/mismatched package index or tier
  map; failed disposable install/reinstall/uninstall/calibration/help check; any foreign collision;
  any need for `-Force`, `-ForceShared`, direct copy, host restart, security-policy change, or real
  profile cleanup; ledger/tree drift; or an inconclusive fresh-context probe.
- **Operator action:** review the disposable evidence, approve or reject the exact active-home
  install, and open the fresh Codex context. Approval of this plan or of Steps 1-3 is not approval of
  this step.
- **Flags:** N/A — `Type: wait` halts build-phase and never dispatches build-step.
- **Depends on:** Step 3 complete and synchronized.

## 6. Serialization and Issue Lifecycle

The steps are strictly sequential:

```text
Step 1 package capability -> Step 2 proof closure -> Step 3 adapter resume -> Step 4 activation
```

No pair is parallel-safe. Step 2 consumes Step 1's emitted package and installer state model. Step 3
requires the calibration restored and proven by Steps 1-2 before its mandatory deep review can run.
Step 4 consumes the exact reviewed and pushed result of all three code steps.

Each step receives its own linked tracking issue during repo-sync. Passing a step may close that
step issue. After Step 2 passes, close parent #177 with links to both reviewed commits. Parent #165
remains open after Step 3 because it owns the remaining adapter inventory; add the Step 3 result as
a progress comment rather than closing #165. Step 4 has its own operator issue and cannot be closed
from code-step evidence alone.

## 7. Stop Conditions and Recovery

Before dispatch, stop for a missing pinned commit/path, unresolved 39-file provenance mismatch,
tier-map snapshot drift, required change to the accepted Phase IS plan or frozen UAT,
dirty/diverged main, or failed host acceptance probe.

During build-phase, use only its defined halt classes. In particular, preserve the fresh worktree and
stop on a blocked reviewer verdict, full-gate/count regression, overlapping upstream advancement,
same-bug-shape stop-and-audit trigger, or worktree merge conflict. Never patch or land the rejected
donor in place.

If a step fails after modifying only a fresh worktree, main and both donors remain unchanged. If a
post-merge root gate fails, write the authenticated fail-closed verdict before returning and do not
advance the plan status.

## 8. Phase Acceptance and Automatic Continuation

This remediation phase is complete only when all four step issues are closed, all four plan statuses
are `DONE`, parent #177 is closed, parent #165 remains open with the review-deep slice recorded, main
is clean and synchronized, the final repo-root suite passes, Step 4's fresh-context activation proof
passes, and no forbidden local-host surface or sealed Phase IS artifact changed.

The paused sibling consumer `../pta_finance`, issue #27 and
`documentation/treasurer-slides-plan.md` Step 14, may resume only after that complete Phase RD
condition is true and the remotely reread `PhaseRdActivationSealV1` is linked from the Step 4 issue.
Its existing command remains `/build-phase --plan
documentation/treasurer-slides-plan.md --resume 14` with `--reviewers deep --isolation worktree`;
no fallback, downgrade, bypass, or consumer-repository edit is authorized here.

Only after Step 4 passes, start a separate build-phase invocation for Steps 1-3 of
`documentation/phase-is-disposable-c2n-c4-environment-plan.md`. Those are the only pre-provider C2E
code steps. Stop at C2E Step 4, whose `Type: wait` contract requires the operator's provider,
Windows-license, artifact-retention, authentication, cost, and publication-broker selection. Do not
provision anything, install/restart hosts, or cross that wait in this run.
