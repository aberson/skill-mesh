# Phase 7.5 test baseline

**This document is the ONE owner of the pytest gate contract for this repository:**
which invocation is the DONE gate, which invocations are iteration gates, and the
measured counts for each. `CLAUDE.md` and [`architecture.md`](architecture.md) name the
commands but deliberately restate no numbers — a count copied into a second document is
a count that drifts, and this repository already shipped that drift (a `tests/`-only
total was published as the repo-root command's total).

Every Phase 7.5 step whose Done-when reads "green at or above baseline" compares against
the numbers recorded here.

## The two invocations

**DONE gate — repo root, no path argument.** Run from the repository root:

```
python -m pytest
```

Collection reaches the eight suites under `tests/` **and** three test roots that a
`tests/`-scoped run never touches:

| Root-only test root | What it covers |
|---|---|
| `_shared/` | the shared build-step verdict engine and its graders |
| `skill-iterate/scripts/` | `adversarial_calibration` (mutation calibration, fleet aggregation) |
| `skill-eval-setup/scripts/` | `generate_bad_examples` (skill discovery, bad-example generation) |

These are production modules, not fixtures. A gate that cannot see them cannot see a
regression in them — the cross-suite blind spot the build-phase halt contract cites,
and the reason design decision D6 in
[`host-parity-repair-plan.md`](host-parity-repair-plan.md) makes the repo-root
invocation the DONE gate.

**Iteration gates.** Both are legitimate while developing and neither may flip a step or
a phase DONE:

```
python -m pytest tests/
```

```
python -m pytest tests/package-integrity
```

## Measured baseline

Measured 2026-08-10 on this repository at Step 62, after the three root-only failures
were fixed. The provenance of each row is stated explicitly rather than left implied —
a number that gates a decision has to say how it was obtained.

| Command | Collected | Passed | Failed | Skipped | Provenance |
|---|---|---|---|---|---|
| `python -m pytest` (DONE gate) | 912 | 909 | 0 | 3 | measured directly, 44m18s |
| `python -m pytest tests/` | 587 | 584 | 0 | 3 | collection measured; pass/skip derived (see below) |
| `python -m pytest _shared skill-iterate skill-eval-setup` | 325 | 325 | 0 | 0 | measured directly, 18.08s |

Rows 1 and 3 are observed summary lines from complete runs. Row 2's collection count is
an observed `--collect-only` figure; its pass/skip split is **derived**, not separately
observed: 587 + 325 = 912 accounts for every collected test exactly, so the two sets are
disjoint and exhaustive, and subtracting the measured row 3 from the measured row 1 gives
584 passed / 3 skipped. Anyone who needs row 2 observed end-to-end should run it and
replace this line — it costs another 44 minutes and changes no decision this phase makes,
which is why it was derived rather than re-run.

The three skips live under `tests/` and are environment-gated, not disabled tests; row 3
has none.

### Re-measured 2026-08-18 (Phase CP pass 1, Steps 4+5)

The Phase 7.5 rows above are a dated Step-62 record and are left intact. The pass-1
DONE-gate measurement, taken at commit `4bcbef5` (superseded as *current* by the pass-2
section below, retained as the dated pass-1 record):

| Command | Passed | Failed | Skipped | Provenance |
|---|---|---|---|---|
| `python -m pytest` (DONE gate) | 1312 | 0 | 1 | measured directly, 1h50m04s, uninterrupted |

Two things changed since Step 62 and both matter for `count >= baseline` comparisons.
**The suite grew**: 912 collected then, 1313 now, so the Step-62 numbers are a floor and
not a target. **The skip count fell from 3 to 1** — treat 1 as the healthy figure; a run
reporting 25 failures with 1 skip is the documented missing-PyYAML mode
(`CLAUDE.md` § "Environment requirements"), not a regression.

Wall clock also moved: 1h50m against the 31m48s–44m18s spread recorded above. That is
suite growth plus the same PowerShell-per-test cost, not a performance regression — the
variance warning above still applies, and nothing gates on these timings.

### Re-measured 2026-08-19 (Phase CP pass 2, Steps 6–8) — SUPERSEDED by pass 3 below

> **Superseded 2026-08-20.** The current figure is **1322 passed / 1 skipped** — see
> *Re-measured 2026-08-20 (Phase CP pass 3)* at the end of this section. The pass-2 numbers
> below are retained as the dated measurement they were, not as today's suite.

The pass-2 DONE-gate measurement, taken on merged `main` carrying the Step 8 payload:

| Command | Passed | Failed | Skipped | Provenance |
|---|---|---|---|---|
| `python -m pytest` (DONE gate) | 1318 | 0 | 1 | measured directly, 2h10m56s, uninterrupted; terminal summary retained at `documentation/findings/cp-step8-pass2-root-gate.txt` |

Trajectory across pass 2, with no regression at any step: **1312** (pass-1 baseline,
`4bcbef5`) → **1312** (Step 6) → **1314** (Step 7) → **1318** (Step 8). The skip count held
at 1 throughout, so 1 remains the healthy figure.

Provenance differs by step and the difference is worth naming. The Step 6 and Step 7 gates
were assembled from more than one process — `pytest tests/` plus the three root-only roots
invoked separately — which collects the same set but is not literally the command the
DONE-gate contract names. The pass-exit Step 8 gate **is** that command: one uninterrupted
repo-root `python -m pytest` with no path argument.

Wall clock moved again, to 2h10m56s. That is 42 codex adapters' worth of added
package-integrity and distribution cases paying the same PowerShell-per-test cost, not a
performance regression; nothing gates on these timings.

**Confirmed at the pass-2 documentation wrap.** The same gate was re-run end to end at commit
`2a8d2c1` (the `/repo-update` doc payload, docs only) and returned **1318 passed, 1 skipped,
exit 0** in 2h13m13s — identical counts at a later commit, which is the evidence that the wrap's
six-file documentation change altered no test outcome. Two independent full-root runs agreed
on 1318/1, and that pair was the current figure until pass 3 superseded it.

### Re-measured 2026-08-20 (Phase CP pass 3, Steps 9–10) — CURRENT

| Command | Passed | Failed | Skipped | Provenance |
|---|---|---|---|---|
| `python -m pytest` (DONE gate) | 1320 | 0 | 1 | Step 9 post-merge gate at `abf3522`; 1:58:39, detached and uninterrupted; summary retained at `documentation/findings/cp-step9-root-gate.txt` |
| `python -m pytest` (DONE gate) | **1322** | 0 | **1** | **CURRENT** — Step 10 post-merge gate at the merged Step 10 payload; 2:06:17, detached and uninterrupted; summary quoted in commit `c4a850c` |

Trajectory across pass 3, no regression at any step: **1318** (pass-2 exit) → **1320**
(Step 9, +2 = the two `test_autofix_marker_single_owner.py` cases) → **1322** (Step 10, +2).
The skip count held at **1** throughout, so 1 remains the healthy figure.

Both pass-3 gates are the literal DONE-gate command: one uninterrupted repo-root
`python -m pytest` with no path argument, each run detached with an exit-code sentinel
because the ~2h wall clock exceeds the orchestrator's per-call tool timeout.

**Collection reaches eight suites, not seven.** Verified against the Step 9 gate log:
`tests/` holds `calibration`, `distributions`, `experiments`, `package-integrity`,
`release`, `router`, `smoke` and `telemetry` — `experiments` (78 tests) was omitted from
this document and from `CLAUDE.md` until 2026-08-20. The three root-only roots (`_shared/`,
`skill-iterate/scripts/`, `skill-eval-setup/scripts/`) are unchanged, so the repo-root
invocation collects **eleven** roots in total.

Wall clock moved from 2h10m56s to 1:58:39 and 2:06:17 — inside the run-to-run variance this
document already documents, not a performance change. Nothing gates on these timings.

Wall clock: three full repo-root runs were timed on the same machine during this step —
**37m51s** (pre-fix baseline), **44m18s** (post-fix, in the build worktree), and
**31m48s** (post-merge, in the main checkout). Nearly all of that time is inside `tests/`
— the distributions, release, and smoke suites shell out to PowerShell once or more per
test. The 325 root-only tests are pure Python and finish in **18 seconds**.

Two things follow. First, **the DONE gate costs about 18 seconds more than the `tests/`
iteration gate it replaces** — a rounding error against a half-hour-plus run, so there is
no runtime argument for the narrower command. Second, run-to-run variance is *minutes,
not seconds*: the same 912 tests spanned 31m48s to 44m18s, a 39% spread, on one machine
in one afternoon. Budget for the high end, and do not treat any single figure here as a
benchmark or use these timings to detect a performance regression — they are too noisy
for that, and nothing in this phase depends on them.

### The three failures this baseline is clean of

Before Step 62 the repo-root invocation reported 912 collected / 906 passed / **3
failed** / 3 skipped. The three were fixed, not frozen, xfailed, or skipped — per the
plan's D6 caveat and its "DECIDED — red root gate" row, a frozen entry would poison
every later `count >= baseline` comparison in the phase. There is no known-failing set
and no step may introduce one.

1. `skill-iterate/scripts/test_adversarial_calibration.py::SkillsRootResolutionTest`
2. `skill-eval-setup/scripts/test_generate_bad_examples.py::SkillsRootResolutionTest`

   Both asserted `_SKILLS_ROOT.name == "skills"` and `_SKILLS_ROOT.parent.name ==
   ".claude"` — two directory names copied from the host workspace the modules were
   authored in. The resolver itself is correct here: `_SKILLS_ROOT` is the directory
   that holds the sibling skill packages the modules dereference. The names were the
   stale part, and they were wrong twice over — wrong for this repository, whose skill
   packages sit at the repo root, and wrong again inside any git worktree or renamed
   checkout. Each now asserts the structural property the guard existed for: that
   `_SKILLS_ROOT` is a real directory holding the module's *own* package (a round trip
   back to the module's directory, which is exactly what the original off-by-one broke)
   plus the sibling package it dereferences. Strictly stronger than the names: a
   `parents[]` drift to a directory that merely exists still fails.

3. `skill-iterate/scripts/test_adversarial_calibration.py::CalibrateFleetAutoDiscoverDefaultTest`

   Asserted `calibrate_fleet(...)["summary"]["total"] >= 1` with the default
   `skills_root`. Discovery requires `<root>/<skill>/evals/evals.json` and this
   repository ships no `evals.json` anywhere, so the assertion was really claiming that
   some other directory happened to hold eval fixtures. The test's stated intent — prove
   the default-arg path is reached and `_SKILLS_ROOT` is what gets used — is preserved
   without inventing fixture data: it asserts the cross-skill import target resolves from
   `_SKILLS_ROOT` and that the imported module is that file, then points `_SKILLS_ROOT`
   at a synthesized tree of scorable skills and proves, via a spy on the production
   discovery function, that omitting `skills_root` routes `_SKILLS_ROOT` into discovery
   and that its result is what the aggregate counts. Relaxing the assertion to `>= 0`
   would have been a tautology and was rejected.

Both repairs were verified against planted-defect anchors: with `_SKILLS_ROOT` forced to
the original bug shape (a nonexistent nested path) and again to a real-but-wrong-level
directory, all three tests go red.

## Rescued asset provenance

`config/skill-manifest.json` declares `skills/judge-ui/calibration-notes.md` as a
support-asset destination, but the file had never been committed — `git log --all` over
that name returned nothing, and the only copy on the cutover machine was in the
installed GPT discovery tree, where Step 64's take-ownership install would overwrite it.
Step 62 vendors it into the canonical tree.

| | sha256 | bytes |
|---|---|---|
| Source copy (installed GPT tree) | `4fea392ed1154c566bb6c4f1560c23be539240e4f0222527f1fc7d6f8471433d` | 2491 |
| Vendored `skills/judge-ui/calibration-notes.md` | `eadc1827b141faf2d3f81717518a480d92c7f86eb543600d634416054b377526` | 2484 |

**The two differ by exactly one path token, and they have to.** The source copy links
judge-core as `../../skills/_shared/judge-core.md`. That is the pre-migration spelling:
`skills/_shared/` is the manifest's *eventual* destination for the shared assets, the
directory does not exist yet, and the repository holds three standing gates against the
string — `test_skill_tree.py::test_global_asset_paths_fully_rewritten`,
`::test_shared_dest_divergence_is_intentional`, and `::test_intra_repo_refs_resolve`.
Committing the byte-identical file turns all three red and plants a fresh dangling
reference one step before Step 63 freezes the dangling-reference baseline, which D7
forbids from growing.

The vendored copy therefore carries the migration transform that
`tools/gen_skill_tree.py` applies to every other migrated reference — shared assets
resolve to the existing repo-root `_shared/` — so the link reads
`../../_shared/judge-core.md`, matching `skills/judge-ui/core.md` line for line in form.
Nothing else changed: every prose clause, heading, and blank line is byte-for-byte the
source copy, and the seven-byte delta is the removal of the `skills/` segment. When the
later global-support-asset migration creates `skills/_shared/`, this reference gets
re-pointed with all the others.
