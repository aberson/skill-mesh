# Phase RD Step 1 force-boundary decision

**Status:** DECIDED by the operator on 2026-09-04. This record closes the policy questions raised
by the preserved `build-step-rd178-step1-20260903150041` candidate. It authorizes a plan amendment,
not a new implementation window, merge, install, or host mutation.

## 1. Decision

Phase RD does **not** introduce a forced-preimage certificate or force-assisted raw-package WAL
recovery subsystem. The candidate-only fields `forced_preimage`, `force_backup_binding`,
`write_ahead_force_plan`, and `write_ahead_expected_ledger_hash` are outside the Phase RD grant and
must not be re-derived or shipped.

This decision does not remove or weaken the existing mainline force-backup protection used for
ordinary generated-file takeovers. `Write-ForceBackup` and `Assert-ForceBackupCertificate` remain at
their current mainline contract. Here, “forced-preimage certificate subsystem” means only the
candidate's proposed persistence and rebinding of force authority through a raw-package WAL; it does
not mean code-signing certificates or the existing generated-file backup manifest.

## 2. Locked raw-package force boundary

The installer classifies authority per path, then applies one atomic transaction verdict.

1. A generated file is governed by anchored generated provenance plus the normal ownership ledger.
2. A raw package leaf is governed by its exact provider/skill/path/hash-bound generated package
   index plus the normal ownership ledger.
3. One invalid or divergent raw leaf blocks the entire transaction before mutation, but it does not
   erase or widen the authority classification of its byte-identical peers.
4. WAL v2 may resume only an exact same-source raw transaction under the already-recorded raw/index
   tuple. It never turns force, a new backup directory, or a new backup record into retry authority.
5. `-Force` and `-ForceShared` may retain their existing behavior for generated files only when no
   raw package action depends on force authority and no raw WAL is pending.
6. Any raw package adoption, overwrite, stale removal, uninstall, or pending-WAL recovery that would
   depend on `-Force` or `-ForceShared` refuses before backup creation, WAL publication, payload
   mutation, ledger publication, or cleanup. The stable refusal prefix is:

   `install-skill-mesh: RAW_PACKAGE_FORCE_UNSUPPORTED --`

7. A pending raw WAL plus either force flag refuses with the same prefix even when the incoming
   source is otherwise byte-identical. The supported recovery is a force-free exact-same-source
   retry; changed-source retry and uninstall remain true no-mutation refusals.

The implementation may compute a per-leaf reason for the refusal, but no caller-constructible path,
hash, force flag, or backup directory can upgrade raw-package ownership.

## 3. Production-code and test boundary

A fresh Step 1 recovery starts from synchronized `main` and surgically re-derives only the package
asset, raw/index ownership, ordinary WAL v2, calibration, helper, and tier-map work already granted
by the Phase RD plan and the package-asset authority decision.

It must not:

- copy, merge, cherry-pick, or patch the preserved candidate in place;
- add the four candidate-only force/WAL fields named above;
- change the shape of the existing external `take-ownership-backup.json` record for Phase RD;
- add production `SKILL_MESH_INSTALL_TEST_*` environment seams beyond the two present on main at
  this decision (`SKILL_MESH_INSTALL_TEST_FAIL_LEDGER_PUBLISH` and
  `SKILL_MESH_INSTALL_TEST_HOLD_LOCK_MS`); or
- run any test seam that corrupts a real consumer home or non-disposable path.

Tests use disposable homes, ordinary subprocess interruption, existing seams, and explicit fixture
construction. They prove directory-and-byte no-mutation on every refusal. The fresh candidate must
also plant a v1 WAL compatibility regression so `Set-StrictMode -Version Latest` cannot encounter a
v2-only field on a v1 action.

## 4. Separate pre-existing hardening defect

The forced stale-deletion/uninstall path on current `main` can waive final path identity after a
reparse substitution. That defect predates Phase RD and is not repaired inside Step 1. Issue #192
owns the separate installer hardening.

This separation does not waive Phase RD safety. Step 1 must prove that raw package assets cannot
enter that forced stale-deletion path: a force-dependent raw action refuses before mutation under
Section 2. Routine ledger/index-authorized stale raw removal still retains literal, regular,
non-reparse path checks.

## 5. Preserved evidence and disposition

The rejected candidate remains read-only on branch
`build-step-rd178-step1-20260903150041`, based at
`59a9b269b298d1564db168c9de809ca270969d4a`, with 59 status entries and working-snapshot SHA-256
`446f4fda4764684b474e24619be9fe6e67c9097a3047dc76ceed17032342eb9f`. Its installer SHA-256 is
`5901228CE46B832CC3A2EAE9037920262B49560B973F7C66EA03998A60EACDAA`.

Issue #178 comment `5536682273` is the primary forensic record. It establishes that:

- the terminal focused reproduction was `5 passed, 1 failed, 130 deselected`;
- the failure was an ordering/policy contradiction around a fresh `-BackupDir`;
- the four force/WAL fields exist in neither main nor the named WAL donor;
- the forced stale reparse deletion is pre-existing;
- a candidate-introduced unguarded v1 read would fail under PowerShell StrictMode; and
- no `.build-step` sidecar or qualifying repository-root gate exists for the candidate.

Do not spend the repository-root gate on this rejected candidate. Its forensic value is frozen by
the branch, fingerprints, and issue record. The mandatory full gate runs only on the newly derived,
reviewable candidate.

## 6. Execution sequence and stop rules

After this decision, its plan amendments, review, issue reconciliation, commit, and push are
complete, a separately authorized fresh high-tier build-step may retry Phase RD Step 1 from actual
synchronized `main`. It stops after Step 1. Steps 2 and 3 resume through a later build-phase only
after Step 1 is reviewed, merged, pushed, issue-closed, and root-gate-qualified.

Stop without merge if work would require the excluded force/WAL fields, a new external backup-record
schema, a new production corruption seam, force authority over any raw package action, modification
of preserved evidence, a full gate on the rejected candidate, or any active-profile, certificate,
policy, boot, driver, provider-resource, frozen-UAT, C2V/C2A, Phase PROD, or host mutation.
