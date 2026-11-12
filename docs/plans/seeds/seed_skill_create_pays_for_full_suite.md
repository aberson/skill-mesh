# Seed: creating one skill pays for the whole test suite

Captured: 2026-11-11, from the `user-dr` release (v2.0.4). Status: seed only. It does not
change the DONE-gate rule in `CLAUDE.md` or grant any waiver.

Sibling: `seed_done_gate_too_slow_to_finish.md` (this folder) covers why the full suite
cannot finish in a working window and why the fast gate misses repo-wide scans. The
installer cause is `dev/docs/seeds/seed_skill_mesh_installer_slow_path_canonicalisation.md`.
This seed covers a different question: why a content-only skill change needs the full
suite at all.

## The problem

A catalog CREATE is mostly Markdown, but its only DONE gate is the repo-root
`python -m pytest`: 2,156 tests, three hours or more on this machine. Most of that time
goes to tests that each launch Windows PowerShell to build or install a skill tree. A large
share of them test code that a skill CREATE does not touch: legacy migration (204 tests),
host inspection (163), and the build-step tree tests (61).

The operator has waived or abandoned the full run several times. Each time the waiver was
written by hand, and each one picked its own subset:

- **v2.0.3 `code-consigliere`.** The full run failed one stale-report check. The operator
  accepted focused evidence instead of a rerun.
- **v2.0.4 `user-dr`.** The operator stopped the full run after about 80 minutes, at 690
  passed, 1 skipped and 0 failed of 2,156. They accepted a narrow set instead:
  `tests/distributions/test_distributions.py`, `tests/smoke`, `tests/release`,
  `tests/router` and `tests/telemetry`, plus the staged package checks in `release.ps1`.
- **Phase LH and Phase CD.** Both accepted focused evidence after full runs that were
  incomplete or stopped (see `plan.md` and the `CLAUDE.md` Phase CD exception).

A gate that is waived on almost every catalog change is not working as a gate.

## Why a skill CREATE is bigger than it looks

- **Count pins.** It moves the skill count. That number is pinned in the generator, the
  manifest, both inventories, five test files, and the count prose in five documents.
- **Other skills' descriptions.** The Codex catalog-headroom guard
  (`test_codex_budgets.py`) only allows a margin of 400 to 900 characters. To stay above
  400, v2.0.4 had to shorten 21 other skills' descriptions. `user-build-route` will leave
  only about 420, so the CREATE after it will have to shorten descriptions again. A
  "one-skill" change therefore keeps reaching into twenty others.

## Candidate directions (not designed here)

- **A gate chosen by what changed.** If a change touches only skill content, docs, the
  generated catalog files, generator constants and count pins, it gets a declared catalog
  gate. If it touches `tools/`, `runtime/`, or `_shared` code or test infrastructure, the
  full suite is still required.
- **Derive the selection; never hand-list it.** Assign every test file to a class, with a
  test that fails on any test file that has no class. Then a new repo-wide scan cannot drop
  out of the catalog gate silently. This is the sibling seed's router lesson.
- **Prove it catches known failures before adopting it.** The catalog gate must fail on the
  two known misses: the v2.0.3 stale release-candidate report, and the `w3` router-scan
  failure from the sibling seed. Measure per-test durations on a clean machine before
  setting a time target.
- **Make the gate standing, not per-release.** Put the catalog gate in
  `documentation/skill-catalog-lifecycle.md`, so a CREATE no longer needs its own scoped
  exception paragraph.
- **Revisit the headroom guard's upper bound.** Its 900-character maximum is what makes a
  CREATE edit other skills. Decide whether that early warning is worth the fan-out.

## Done when

- The next content-only skill CREATE runs one documented gate.
- That gate fails on both known misses.
- It finishes within a measured time that fits a working window.
- The full suite stays required for tool and runtime code changes.
- No scoped exception paragraph is needed.

## Not in scope

This seed does not change the gate rule without the operator. The rule has owners that
must change together: the `CLAUDE.md` "Default DONE gate", the workspace
`.claude/rules/code-quality.md` gate-scope note, the lifecycle guide, and the
build-step/build-phase gate prose. It does not delete or skip any test, and it does not
edit another session's uncommitted work.
