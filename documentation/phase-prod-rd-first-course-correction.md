# Phase PROD course correction — restore review-deep first, then build the minimum viable split

**Status:** OPERATOR-APPROVED on 2026-09-03; Step-1 force boundary amended on 2026-09-04.

This decision supersedes the execution order in
`documentation/production-toolchain-separation-plan.md` after its completed Step 1.
The old plan remains a historical design and evidence index, but its Steps 2–7 are not an
executable queue. The active order is:

1. finish Phase RD and restore the reviewed `review-deep` package;
2. activate and prove that package through Phase RD's attended Step 4;
3. create and review a smaller Phase PROD MVP plan;
4. build and attend the production/development cutover from that replacement plan.

No part of this decision authorizes a production-root, active-profile, User/Process environment,
certificate, Code Integrity, Secure Boot, boot, SDK/WDK, driver, frozen-UAT, or Phase IS artifact
mutation.

## 1. What This Is

**Objective:** restore the unavailable deep-review rail first, then replace the oversized Phase PROD
design with the smallest production/development split that keeps daily-use tooling stable.

The operator selected route A on 2026-09-03: Phase RD first, then a minimum viable product (MVP)
Phase PROD. Route B (build the MVP before Phase RD) and route C (continue the full hardened PROD
plan) are not active execution authorities.

Terms used below:

- **Phase RD:** the four-step remediation that restores and activates the complete `review-deep`
  Codex package.
- **Phase PROD:** the production/development utility-root split. Only its declarative Step 1 shipped;
  its old Steps 2–7 are archived.
- **WAL:** the installer write-ahead log that preserves recovery authority across interruption.
- **Terra:** the `gpt-5.6-terra` implementation model used by `build-step`.
- **Opus:** the Claude Code high-tier model selected for the next Step-1 recovery after the
  credit-aware 2026-09-04 handoff; this changes the executor, not the build-step contract.
- **C2V/C2A/C2E:** sealed or parked Phase IS completion stages; none is modified here.
- **Verdict service and sidecar:** the caller-scoped parent authority and authenticated external
  result file used to keep developers/reviewers from awarding their own verdict.

### Why the course changed

The practical goal remains correct: ordinary project work should execute reviewed, commit-pinned
utility code from a stable production root while development continues independently under the
development root. The original detour was introduced after Phase RD blocked because the operator
could not afford to lose daily-use tooling during another long Skill Mesh repair.

The detour does not restore `review-deep`. Phase RD issues #178–#181 remain the only authority for
that repair, so completing Phase PROD first would not remove the immediate
`--reviewers deep` blocker.

The Phase PROD implementation also stopped converging:

- the first Step-1 build mixed declarative validation with runtime authority and exhausted 3/3
  iterations before the declarative-only boundary was selected;
- the replacement Step 1 shipped successfully at
  `2e8e4f3e516c7069d07364ab5438e7f810675290`;
- the original Step-2 candidate exhausted 3/3 iterations with High=6 and Medium=6;
- a fresh recovery candidate exhausted another 3/3 iterations with nonzero correctness,
  security, and test-quality findings;
- neither Step-2 candidate was merged, and no production directory or live host state was changed.

The high-tier decision and independent reproduction on 2026-09-03 found two plan-level causes:

1. `plan` was required to be read-only while the candidate fetched into source repositories and
   consumed `FETCH_HEAD`;
2. the trusted-executable boundary was unstated, so reviewers reasonably treated exact pushed
   first-party build code as hostile and demanded an implicit OS sandbox.

The terminal `GIT_COMMAND_FAILED: rev-parse` was also too generic. Independent reproduction proved
that `FETCH_HEAD` existed and resolved; the fixture supplied only three of the manager's nine
required Skill Mesh blobs. That fixture defect does not make fetch appropriate for a read-only
planner, but it explains why the last repair round was debugging the wrong immediate failure.

## 2. Authoritative state at the decision

- Main and `origin/main`: `c58222416c96947f5009d518e0507ebd293ff826`, clean, divergence
  `0/0`.
- Phase PROD Step 1/#184: DONE at
  `2e8e4f3e516c7069d07364ab5438e7f810675290`.
- Phase PROD Steps 2–7: unshipped and superseded for execution by this decision.
- Phase RD Step 1/#178: RETRY AUTHORIZED from a fresh `build-step` worktree based on actual
  synchronized main. The preserved later candidate proved the pending-WAL addition and retirement
  junction boundary with a controlled RED and repaired `2 passed in 229.20s` GREEN. Its actual
  terminal gate was `180 passed, 3 failed`: two stale whole-corpus provenance assumptions and one
  missing legacy package-index self-seed authority.
- Phase RD Steps 2–3: remain strictly dependent on the preceding RD step.
- Phase RD Step 4: remains an attended wait gate requiring its own disposable rehearsal and
  target-specific active-profile approval.
- Phase IS C2V/C2A records, accepted plan, and frozen UAT remain immutable.

Subsequent boundary on 2026-09-04: a fresh Step-1 attempt exhausted its authorized three-iteration
window and stopped unmerged. A read-only Opus forensic pass proved that the candidate had added an
ungranted forced-preimage/WAL certificate subsystem and had no qualifying repository-root gate.
The operator chose the narrower force boundary recorded in
`documentation/phase-rd-force-boundary-decision.md`. Step 1 is recovery-ready but no replacement
build has been dispatched.

## 3. Preserved evidence — read-only

Do not edit, merge wholesale, delete, prune, or treat any of these worktrees as acceptance
evidence. Resolve them through `git worktree list --porcelain` rather than assuming a path.

| Branch | HEAD | Status entries | Working-snapshot SHA-256 | Purpose |
|---|---|---:|---|---|
| `build-step-prod2-20260902-1836` | `ca3f5f8f3eb4ce1fb74a7bb0d30cb3ea7c167eb7` | 3 | `b7c90506f746a4150db0c5a25640fea33cfd6f3215241888d7dc08b9bfada021` | First exhausted PROD Step-2 candidate |
| `build-step-prod2-recovery-20260903` | `c58222416c96947f5009d518e0507ebd293ff826` | 3 | `3a944fb5b54d97aaf23188ca68d2e5bedcf138be8a0be6d430171bd9abc1b460` | Second exhausted PROD Step-2 candidate |
| `build-step-phase-rd-178` | `b36635891e657c859823b28e39f493f9feecff4f` | 56 | `36e1c03171f60dd325485ef5eb785c6416b825de30f1511fb53d4b115e5d0c45` | Earlier blocked Phase RD Step-1 candidate |
| `build-step-rd178-wal-20260831195206` | `52af1d7ee19ff3bafd00d96d269b8ea1d93891bd` | 56 | `89d8853ac932a32abd3b5071f80515aed9b8c2063dd1639f8008bfcb58f20359` | Latest Phase RD Step-1 evidence; WAL junction fixed, three integration failures remain |
| `build-step-rd178-step1-20260903150041` | `59a9b269b298d1564db168c9de809ca270969d4a` | 59 | `446f4fda4764684b474e24619be9fe6e67c9097a3047dc76ceed17032342eb9f` | Rejected Step-1 force-boundary candidate; no root-gate evidence; issue #178 comment `5536682273` |
| `build-step-review-deep-calibration-assets-20260830224727` | `4b9b0aa065ac57f9b70a0cb1773e2d6c3e43d420` | 53 | `b8a77d35815a1b10dc8442682982d08a693bb76a7ffc13dad7d3a0a5751e6588` | Rejected package-assets donor |
| `build-step-review-deep-capability-20260830220844` | `4b9b0aa065ac57f9b70a0cb1773e2d6c3e43d420` | 4 | `00aa910f5c5bb60a0ce181cd8d1d256bfc630a727435e7276e28c4bc1273f1e2` | Paused capability-adapter donor |

The working-snapshot digest is SHA-256 over ordinally sorted UTF-8/LF records of
`<two-character porcelain status> TAB <repository-relative path> TAB <raw-file SHA-256> LF`, using
`git status --porcelain=v1 --untracked-files=all`. It is a preservation alarm, not acceptance
evidence. Resolve each worktree by branch through the Git registry before recomputing it.

The status field is exactly two characters. In particular, the leading ASCII space in ` M` is
significant and must not be trimmed. Run this Windows PowerShell 5.1-compatible recipe once for
each resolved worktree; the final line is the lowercase working-snapshot digest:

```powershell
param([Parameter(Mandatory = $true)][string]$EvidenceRoot)

$records = @()
$statusLines = @(git -C $EvidenceRoot status --porcelain=v1 --untracked-files=all)
if ($LASTEXITCODE -ne 0) { throw 'git status failed' }

foreach ($line in $statusLines) {
    if ($line.Length -lt 4) { throw "invalid porcelain record: $line" }
    $status = $line.Substring(0, 2) # Preserve both characters, including a leading space.
    $relativePath = $line.Substring(3)
    $fileHash = (Get-FileHash -LiteralPath (Join-Path $EvidenceRoot $relativePath) -Algorithm SHA256).Hash.ToLowerInvariant()
    $records += "$status`t$relativePath`t$fileHash"
}

[Array]::Sort($records, [StringComparer]::Ordinal)
$payload = [String]::Join("`n", $records) + "`n"
$bytes = (New-Object Text.UTF8Encoding($false)).GetBytes($payload)
$sha256 = [Security.Cryptography.SHA256]::Create()
try {
    ([BitConverter]::ToString($sha256.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
}
finally {
    $sha256.Dispose()
}
```

The two PROD candidates each contain only these three untracked candidate-relative paths (plain text
because the first two do not exist on current `main`):

- tools/production-toolchain.py
- tests/production-toolchain/test_bundle_manager.py
- documentation/production-toolchain-operations.md

Candidate SHA-256 values:

| Candidate | Tool | Test | Operations doc |
|---|---|---|---|
| First | `36D0C6980631B00C20A823930B151CE228F142B092C0013725D7AD40339CCA16` | `ECE71D0F093DB5C809FA0B2D56F6F22F03BCB98648290E7C84A1D2BBC8FCB37A` | `0CBC3F769B16AB4D2A452D8AF314B8582B82F35A9F53604E3D91B11509D3C425` |
| Recovery | `FF0FE4D5CCE0BD14C9A5317BDA7107A0C9701C5459CD68CEAEAD16CDE1AFBBE5` | `A0D055C63D287AEC5465D9558225580499927681F0A651C1DF5143A4300204BB` | `9D99534959F893298FF5B6BA21D9E73986825D54B9219038316C8A5E3B8C9E19` |

For the latest RD evidence candidate, `.build-step/dev-report.md` has SHA-256
`5DB921387C23DE9CBE0A636C2948D160D6DDE8891B28ED1144DFB338A441941F`. Its current installer and
distribution-test hashes are respectively
`33C914D2AAA28A6CFAC907C24A5B0E135C0954DA8DBE45F01EE6842FEC5CE279` and
`4BC617B02D8F679A2CA60F62D34063166BB87C6D7C8EEE3FA68D5EFFAED985E8`.

## 4. What worked and must survive

- One provider-neutral behavior core plus thin host adapters.
- Explicit parent-only verdict authority and fresh producer/reviewer contexts.
- Separate production-code, development-workspace, and persistent-data authorities.
- Exact pushed Git commits as release inputs; never recursive-copy a dirty coding root.
- Two-root utility routing: executable code below `DEV_UTILITIES_ROOT`, targets and registries
  below caller input or `DEV_WORKSPACE_ROOT`.
- A retained exact Codex distribution installed through the existing ownership ledger without
  `-Force` or direct copy.
- Immediate pre-image capture, external backup, rollback, and selector-last publication.
- Final-path/reparse and containment protection on paths that can actually be mutated.
- Fresh-process proof after an attended cutover.

## 5. What failed or became a rabbit hole

- A declarative record validator was asked to prove runtime facts.
- Step 2 bundled four commands, fourteen repository identities, Git provenance, dependency
  execution, Windows path defenses, publication, verification, and activation-plan generation into
  one build-step.
- The plan did not name its trusted executable boundary. Review iterations oscillated between
  pathname guards, post-hoc scans, and permanent refusal instead of converging.
- The recovery candidate's `stage` path ultimately refused every execution while its operations
  document described a functioning stager.
- Generic command errors hid the exact failed object and sent the final iteration toward
  `FETCH_HEAD` rather than the incomplete fixture.
- Every oversized retry paid reviewer cost, while every prospective code step also carried a
  measured two-to-three-hour repository-root gate.
- Production activation was sequenced before the independently testable two-root routing change.
- The plan repeated immutable-byte proofs at several layers and required first-release
  Claude/GPT lifecycle certification even though the live cutover targets Codex.
- A stale #178 status continued naming the pending-WAL junction after a later candidate had proved
  that junction fixed, which risked paying for the same investigation again.
- Phase RD Step 3 required the unavailable `review-deep` lane to review the adapter that enables
  that lane. The corrected plan uses the same bounded five-lens bootstrap exception as Steps 1–2,
  then proves the installed capability at the attended Step 4 boundary.
- The next Step-1 candidate introduced four force/WAL persistence fields, expanded an external
  backup-record schema, and added production corruption seams without plan or decision authority.
  Three patch iterations then optimized conflicting force-retry policies instead of the granted raw
  package boundary. The durable correction is an early fail-closed boundary, not a fourth patch.
- A cumulative `.pytest_cache` was briefly treated as run evidence. Cache membership and mtime do
  not certify which command produced a candidate; only an owned sidecar or observed command/result
  does. The rejected candidate has no `.build-step` sidecar and therefore no root-gate evidence.
- The pre-existing forced stale-removal reparse weakness is split to #192. Phase RD Step 1 neither
  absorbs nor ignores it: raw force refuses before mutation, while #192 owns general installer
  hardening after `review-deep` is restored unless the operator separately reprioritizes it.

## 6. Rules for the replacement Phase PROD plan

The post-RD plan must start from the operator outcome, not from the old four-command API.

1. **One executable boundary per build step.** Do not combine source selection, staging,
   verification, activation, and live cutover in one developer/reviewer loop.
2. **Write the threat model before tests.** Exact allowlisted, reviewed, pushed first-party commits
   are trusted executable product inputs. Protect against drift, dirty bytes, redirection, and
   accidental mutation. A hostile-code sandbox is a separate feature requiring an explicit
   AppContainer/VM/service plan.
3. **Route before activation.** Land and prove the two-root contract before building machinery that
   selects a production release.
4. **Protect real mutation boundaries.** Keep reparse/containment checks for release roots, profile
   roots, backups, selectors, and installed files; do not demand handle-pinning of Git internals.
5. **Codex-first cutover.** Defer Claude/GPT install/reinstall/uninstall certification unless the
   replacement plan explicitly activates those profiles.
6. **Publish completion last.** A failed stage leaves no selectable completion marker; a failed
   cutover restores the exact pre-image.
7. **Stop review oscillation early.** A second round that introduces the same unresolved authority
   family triggers a plan/trust-model review before a third line-level patch.
8. **Budget the real gate.** Each code step must justify its own repository-root gate; documentation-
   only reconciliation should not be a standalone multi-hour build-step.
9. **Use exact diagnostics.** Errors name the repository, ref/blob/path, operation, and failed
   invariant without exposing secrets or private paths.
10. **Report observed async state.** Use `DISPATCHED`, `PREFLIGHT CLEARED`,
    `BUILDING STEP N`, `BLOCKED/EXITED`, and `COMPLETE` only after evidence reaches that
    boundary.

## 7. Minimum viable production/development split seed

After Phase RD is active and proven, run `/plan-feature` using this section as the seed.
The replacement plan should contain the smallest independently testable sequence:

1. **Two-root routing.** Update executable utility call sites and generated Codex output so code
   resolves below an absolute `DEV_UTILITIES_ROOT` while target projects, registry, and state
   resolve from explicit arguments or `DEV_WORKSPACE_ROOT`.
2. **Fixed-policy release-1 stager/verifier.** Materialize independent clean checkouts at exact
   pushed commits, install locked dependencies, build one retained Codex distribution, and write a
   concise completion manifest last. This is a release-1 path, not a generic release platform.
3. **Narrow reversible activation implementation.** Wrap the existing installer/inspector with
   pre-image capture, backup, exact closure comparison, environment updates, selector-last
   publication, and rollback. Tests use disposable homes only.
4. **Real release staging.** Create and verify one release candidate without changing the active
   profile or environment.
5. **Attended cutover and fresh-process smoke.** Activate only the frozen candidate, run
   representative read-only utility commands, and retain the exact rollback route.
6. **Lightweight closeout.** Record the active bundle and deferred backlog. Fold any remaining
   Phase-RD reconciliation into the owning phase rather than creating a prose-only full-gate step.

Deferred backlog:

- reusable multi-release/four-command management;
- hostile committed-code isolation;
- all-provider lifecycle certification;
- exhaustive exotic path variants outside actual mutation roots;
- duplicate evidence reviews over already immutable bytes;
- broad portfolio health claims not needed for the first Codex cutover.

## 8. Active critical path

The next execution authority is
`documentation/phase-rd-review-deep-restoration-plan.md`.

1. The package-asset decision and its force-boundary decision are complete. Ordinary pending raw WAL
   design is closed: exact force-free same-source retry only. Do not reintroduce the excluded
   forced-preimage certificate subsystem.
2. Reverify synchronized main plus all seven preservation rows above. Stop on drift.
3. After separate execution authorization, invoke one fresh Claude Code Opus `build-step` for Phase
   RD Step 1/#178 only. `build-step` alone creates and owns its isolated worktree. Do not patch the
   preserved candidate or start with `build-phase` while Step 1 remains unlanded.
4. Inspect preserved worktrees only for reproduction ideas and the specifically recorded ordinary
   WAL proof. Re-import the 39 package files from pinned coding-root Git objects, recreate the
   tier-map snapshot from current main, and re-derive every implementation byte. Never merge,
   cherry-pick, or copy a donor candidate wholesale.
5. Stop after Step 1. Only after it is reviewed, merged, pushed, issue-closed, and root-gate-qualified
   may a later fresh Opus coordinator invoke
   `/build-phase --plan documentation/phase-rd-review-deep-restoration-plan.md --steps 2,3`.
   Step 3 uses the explicit five-lens bootstrap review recorded in the Phase RD plan.
6. Stop at Phase RD Step 4. Its disposable rehearsal and exact active-home installation require
   the separate approvals already defined by that plan.
7. Do not run Phase PROD, C2E, C2N, C2P, C3, C4, C5, or Phase CL concurrently.

The copyable Git preflight, run from the repository root, is:

```powershell
git status --short
git rev-parse HEAD
git rev-list --left-right --count HEAD...origin/main
git worktree list --porcelain
```

The first command must be empty and the divergence must be `0 0`. Resolve preserved worktree paths
only from the final command; do not persist or assume a machine-specific path. Recompute each row's
working-snapshot digest with the algorithm in Section 3 and stop before `build-step` on any mismatch.

Progress labels are evidence-bound:

- `DISPATCHED`: the coordinator invocation was accepted; say separately whether preflight cleared.
- `PREFLIGHT ONLY — no build worker running`: reads/probes are active, but no developer exists.
- `PREFLIGHT CLEARED`: all mandatory probes passed; developer dispatch is not yet implied.
- `BUILDING STEP N`: a live developer worker for that step has been observed.
- `BLOCKED/EXITED`: the worker or orchestrator terminated without completing the authorized span.
- `COMPLETE`: every authorized code step is merged, pushed, and gate-qualified; never use this for
  dispatch or a merely passing focused test.

## 9. Fresh-context handoff contract

A fresh coordinator must:

- read `AGENTS.md`, `CLAUDE.md`, `plan.md`, this decision, and the full Phase RD plan;
- read both Step-1 authority decisions and issue #178 comment `5536682273`;
- verify actual Git and issue state before trusting any recorded SHA;
- enumerate issue #178 and its comments;
- report `PREFLIGHT ONLY — no build worker running` until the verdict-service and baseline probes
  qualify, then `PREFLIGHT CLEARED` until a developer is observed;
- invoke Step 1 through `build-step` from synchronized main and create exactly one fresh worktree;
- preserve every named evidence worktree;
- stop on the Phase RD plan's existing halt conditions;
- provide an update at each observed boundary and immediately when an asynchronous worker exits.

This document authorizes the RD-first sequence but does not weaken any RD review, gate, or attended
activation boundary.
