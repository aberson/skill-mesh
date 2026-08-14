# Step 4 checkpoint — 2026-08-13

## Status

**Step 4 is not complete.** Do not commit, push, install, or start Step 5 from
this checkpoint.

This is a deliberately clean stop for an independent second opinion. The four
intentional Step 4 working-tree files remain unstaged:

- `tools/install-skill-mesh.ps1`
- `tools/migrate-legacy-install.ps1`
- `tests/distributions/test_distributions.py`
- `tests/distributions/test_legacy_migration.py`

`main` remains at `111fc2b` (`fix(step 65): constrain retirement and harden
migration recovery`). The committed Step 65 work is not being reopened.

No commit, push, environment-setting change, staged install, or live install
occurred during this checkpoint.

## Work completed in the current checkpoint

The outstanding Step 4 integrity gap was addressed locally in the installer:

> If payload mutation succeeds but both final-ledger publication and the old
> catch-path recovery publication fail, the new bytes can be left without durable
> exact-hash authority.

The current uncommitted installer change adds a same-home, atomically written
write-ahead authority record (`.skill-mesh-install.write-ahead.json`) before a
payload mutation. It records the exact allowed pre/post transitions. A later
ordinary install or uninstall first consumes that record: it accepts only the
recorded pre-state or post-state hashes, publishes the exact recovered
`owned_files` / `owned_file_hashes` authority, verifies it, then removes the
record. It must not baseline a backed foreign preimage as owned.

Two deterministic installer regressions were added and passed together:

```text
python -m pytest tests/distributions/test_distributions.py -q -k
  "final_ledger_failure_keeps_write_ahead_authority_and_plain_retry_converges or
   write_ahead_recovery_does_not_baseline_an_unreplaced_force_preimage"

2 passed, 87 deselected in 34.40s
```

The first proves a final-ledger failure plus same-condition catch-path recovery
failure after a changed payload and stale deletion. It asserts that the
write-ahead record retains exact authority, ordinary retry converges without
`-Force`, stale content is not orphaned, and the final owned-file/hash-map keys
are bijective. The second proves a backed `-Force` preimage is not reclassified
as installed ownership during recovery.

The following pre-gate checks also passed after these local edits:

```text
PowerShell parser: PASS (tools/install-skill-mesh.ps1)
python -m py_compile tests/distributions/test_distributions.py \
  tests/distributions/test_legacy_migration.py: PASS
git diff --check: PASS
```

One focused migrator recovery subset also passed:

```text
python -m pytest tests/distributions/test_legacy_migration.py -vv -k \
  "resume_refuses_changed_ledger_or_retire_preimage"

5 passed, 198 deselected in 84.15s
```

## Full-gate failure and test-process history

The required root command was attempted twice:

```text
python -m pytest
```

1. The first invocation was manually stopped after about 67 minutes without a
   final pytest summary. Its remaining child was the migrator invocation for a
   parametrized `test_resume_refuses_changed_ledger_or_retire_preimage` case.
   That exact five-case subset was subsequently run in isolation and passed as
   recorded above. This attempt is **not** gate evidence.

2. The second invocation wrote its output to a temporary, non-repository log.
   It reached 33% while executing `tests/distributions/test_distributions.py`
   and emitted `................F.`. It was stopped immediately after the first
   failure marker so the precise failing assertion could be isolated. The
   process had not emitted a test name, traceback, or final count before it was
   stopped. Therefore **the exact failing test and root cause are unknown**.

A diagnostic rerun was started:

```text
python -m pytest tests/distributions/test_distributions.py -x -vv
```

It was stopped at the operator's request before it reached a final result. Do
not infer a failing test from the position of the `F`; re-run this command to
obtain the first traceback.

Only the checkpoint's own pytest processes and their direct PowerShell children
were stopped. No unrelated process was targeted.

## Review questions for the next model

1. Run the `-x -vv` diagnostic first and identify the actual failure before
   altering the write-ahead design.
2. Independently review whether the write-ahead contract meets this invariant:
   after interruption, either the exact verified pre-state remains, or current
   payload bytes have durable exact post-hash authority consumable by ordinary
   retry without `-Force`.
3. In particular, inspect these edge cases:
   - crash after write-ahead publication but before any payload mutation;
   - normal ledger already published but write-ahead cleanup interrupted;
   - final ledger and catch-path recovery ledger fail under the same condition;
   - backed `-Force` / `-ForceShared` targets that remain at their foreign
     preimage;
   - stale removals, stale commit-time drift, reparse/CAS failure, and corrupt
     normal ledger during write-ahead recovery;
   - no stale or new path can become an untracked orphan;
   - the owned-files/hash-map bijection remains exact after every partial path.
4. Preserve all existing dirty hunks. Do not reset, restore from `HEAD`,
   blanket-stage, push, or perform any consumer install.

## Required continuation gate

Before any local Step 4 commit, rerun and pass all required focused authority /
recovery tests, relevant distribution and migration suites, then the repository
root full suite. After that, perform a read-only adversarial diff review, update
the Step 4 documentation and issue #116 with exact evidence, and make only a
focused local commit. Do not close #116, push, or install.

Only after that local Step 4 commit may work switch to the separately owned Dev
Observatory Step 43. Manual UAT M3 remains preparation-only and must stop for
operator decisions; Skill Mesh Step 5 remains out of scope.
