# Second-opinion prompt — Skill Mesh Step 4

## Provenance

- **Requested by:** Abraham Robison
- **Prepared by:** the Skill Mesh Step 4 build window
- **Source checkpoint:** `documentation/step-4-checkpoint-2026-08-13.md`
- **Prepared:** 2026-08-13

You are reviewing an in-progress **Skill Mesh Step 4 / issue #116** change in
the `skill-mesh` repository. This is a safety-critical installer/migrator
authority change. Do not assume the implementation is correct just because
some focused tests pass.

Start by reading `documentation/step-4-checkpoint-2026-08-13.md` in full. It is
the current factual checkpoint and names what was run, what passed, and what is
unknown.

## Scope and safety constraints

- Preserve the four intentional dirty files; inspect status and diff before
  editing.
- Do not reset, restore from `HEAD`, rebase, blanket-stage, push, close #116, or
  perform a staged/live install.
- Step 65 is already committed at `111fc2b`; do not reopen it.
- Do not advance to Step 5 or Dev Observatory Step 43 until Step 4 has a focused
  local commit and every Step 4 gate passes.

## Problem to review

Installer entries use exact `owned_files` ↔ `owned_file_hashes` SHA-256
authority. The remaining known flaw was this interruption window:

1. payload bytes change;
2. final normal-ledger publication fails; and
3. the catch-path recovery-ledger publication fails for the same CAS, reparse,
   or permission condition.

The current local attempt introduces an installer write-ahead record before the
first payload mutation. Assess whether it is the smallest sound fix, or replace
it only with a demonstrably safer design.

The non-negotiable invariant is: after every interruption, exactly one is true:

1. home and ledger are the verified exact pre-state; or
2. current payload bytes have durable exact post-hash authority that an ordinary
   retry can consume without `-Force`.

Never permit a sole recovery record to be removed before final authority is
durably verified; never baseline unexpected drift; never authorize deletion from
a marker alone; never report success while payload and authority disagree.

## Immediate diagnostic

The root suite emitted an `F` at 33% in the distribution suite, but its exact
test was not captured before the operator requested a clean stop. Run this first:

```powershell
python -m pytest tests/distributions/test_distributions.py -x -vv
```

Treat its traceback as the first evidence. Do not guess the failed test from the
progress marker. If it is unrelated pre-existing failure, establish that with
reproducible evidence; otherwise fix it narrowly.

## Required adversarial review

Read the complete diffs of:

- `tools/install-skill-mesh.ps1`
- `tools/migrate-legacy-install.ps1`
- `tests/distributions/test_distributions.py`
- `tests/distributions/test_legacy_migration.py`

Then prove or disprove the write-ahead recovery path for:

- record publication succeeds but no payload mutation happens;
- new or routine-owned overwrite mutation;
- stale deletion;
- backed `-Force` and scoped `-ForceShared` where a foreign preimage remains;
- normal ledger already written but write-ahead cleanup is interrupted;
- final ledger failure and catch-path recovery publication failure under the
  same failure condition;
- normal ledger corruption or changed hash while a valid write-ahead record
  exists;
- reparse/CAS/permission failure and concurrent retry;
- exact `owned_files` / `owned_file_hashes` bijection and no untracked orphan.

The installer must retain exact durable recovery authority, not merely a marker
or a scan-derived guess. The migrator must not downgrade genuine legacy-hashless
recovery or weaken its semantic plan validation.

## Gates before a local commit

Run parse, Python compilation, `git diff --check`, all relevant focused
installer/migrator authority and recovery tests together, relevant distribution
and migration suites, and finally from repository root:

```powershell
python -m pytest
```

Report real pass/fail/skipped counts and durations. Only after all gates pass:

1. perform a final read-only adversarial diff review;
2. update documentation and issue #116 with exact evidence (no private absolute
   paths);
3. make a focused local Step 4 commit;
4. do not push, close the issue, or install.

If you reach a genuine design ambiguity, stop and explain the conflicting safety
properties rather than making a silent policy choice.
