# Seed: the full DONE gate is too slow to finish, and the subset gate misses repo-wide checks

Captured: 2026-11-11. Status: seed only. It grants no gate waiver, no commit, and no
change to the DONE-gate rule in `CLAUDE.md`.

## What happened

Branch `v3/w3-pin-ledger` (commit `8c22596`) adds two files: `config/pin-ledger.json`
and `tests/package-integrity/test_pin_ledger.py`. On 2026-11-01 it passed the
`tests/package-integrity` iteration gate (704 passed). The full repo-root gate was
never run.

On 2026-11-11 the full repo-root gate (`python -m pytest`, no path argument) was started
in a clean worktree of that branch. The operator stopped it after 2 h 44 min at 28%:
614 passed, 1 skipped, 0 failed of 2,161 collected. At that pace it would have taken
roughly ten hours. Free memory was 2,316 MB at launch and 816 MB at the stop, and another
session's pytest run was active at launch.

A narrow follow-up then found a real failure in under two seconds:

- `tests/router/test_no_claude_dependency.py` scans every `.json`, `.py` and `.ps1`
  file under `runtime/`, `config/` and `tests/` for `.claude/<path>` references.
- On the branch it fails (1 failed, 2 passed). The only offender is
  `config/pin-ledger.json`: an `excluded[].surface` value names
  `.claude/references/model-tiering.md`, and `surface` is not one of the keys the scanner
  treats as a note (`description`, `note`, `notes`, `legacy_*`, `source`, `dest`).
- On main `6ad9174` the same test passes (3 passed). The failure is caused by the branch.

Raw output: `docs/skill-mesh-3-review/builds/w3-full-gate.txt`,
`w3-narrow-router.txt` and `w3-narrow-router-main.txt` in the dev root.

## The two problems

1. **The full gate cannot finish inside a working window.** Recorded full gates run
   3 h 07 min to 4 h 41 min on a healthy machine. Under memory pressure this one was
   on pace for about ten hours. Most of the time goes to the installer, which the
   existing seed `dev/docs/seeds/seed_skill_mesh_installer_slow_path_canonicalisation.md`
   traces to repeated path canonicalisation (S-SLOW).
2. **The fast gate is blind to repo-wide checks outside its folder.** The router scan
   is a repo-wide check that takes seconds and runs no installer, but it lives in
   `tests/router`, which the documented iteration gate never collects. A change can
   therefore be green at the iteration gate and red at a full gate nobody can finish.
   This is the same shape as the Phase 7 lesson in the build-phase halt contract.

## Candidate directions (not designed here)

- **Fix the branch first.** Reword the `surface` value so it names the workspace files
  without a `.claude/` path, or move the path into a `note` key. Then rerun the router
  test and `tests/package-integrity/test_pin_ledger.py`.
- **A fast check set.** List every test that scans the repository tree without calling
  the installer or release tooling, measure its wall clock, and add that set to the
  documented iteration gate. Measure from per-test durations on a clean machine; do not
  guess which suites are fast.
- **S-SLOW.** Memoise path canonicalisation in `tools/install-skill-mesh.ps1`, keeping
  the security checks identical. The target in the lane-R review: the full gate in
  60 min or less, with identical collected, passed and skipped counts.
- **Gate preflight.** Refuse to start the full gate below 2 GB free memory or while
  another pytest run is active on the machine, and record both numbers with the result.
- **Operator decision.** When the full gate cannot finish in a window, decide what
  counts as acceptable evidence. Today `CLAUDE.md` says the full suite is the DONE gate.
  This seed does not change that.

## Also stale

`documentation/phase-75-baseline.md` owns the suite counts, and its latest full-gate row
records 1,636 passed. This run collected 2,161. Re-measure before quoting any count.

## Done when

- `v3/w3-pin-ledger` has a recorded green full repo-root gate, or an explicit
  operator-approved scoped exception that names which suites ran.
- The documented iteration gate includes the measured fast check set.
- Separately, S-SLOW reaches its 60-minute target.

## Not in scope

No pin changes, no merges, no edits to main's working tree while another session owns
its uncommitted work, and no waiver of the full-gate rule.
