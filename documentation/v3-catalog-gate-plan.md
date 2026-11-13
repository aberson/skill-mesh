# Test-gate scope, part 2: the catalog gate (plan)

This is the execution copy for build-phase, copied 2026-11-12 from the operator's planning records in the coding root (`<coding-root>/docs/skill-mesh-3-review/`), where its reviews and the operator's answers live. Step status is recorded here from now on.

> **Amended 2026-11-12 (evening), operator answer to afternoon sheet item 44:** "yes, the default
> is what I want here." The guard plan's section "Reconciliation with the catalog gate plan",
> points 1 to 6 (`documentation/v3-guard-plan.md` in skill-mesh), overrides this plan where they
> differ. In short: (1) the selector and class table stay, as the chooser of each change's focused
> set: `catalog` means the catalog tests, `full` means a larger named focused set, never the
> repo-root suite; (2) no step and no merge here is gated by a full suite: Phase 1 and Steps 2 to
> 7, 9 and 11 use their focused set plus the quick repo-wide checks, with saved evidence; (3) the
> full sweep is one per-release background check, and Step 1's `--durations=0` run is one
> background run, not a gate (it may count as that sweep); (4) the guard plan's rule wording lands
> first, and Steps 9 and 11 edit it to add the class table and selector instead of writing a second
> rule. Where a step below still names a full suite as its gate, read it this way. The step text is
> not rewritten.

> **Amended 2026-11-13, operator decision ("Step 8 now, rest to v3.1"):** Step 8 (item 51, option
> "remove") was done standalone on 2026-11-13, ahead of the rest of this plan, in commit `dd01309`.
> Steps 1 to 7 and 9 to 11 move to v3.1; they are deferred, not cancelled. Step 8's evidence (the
> measured headroom, the decision note and the differential run on a scratch copy) is in
> `<coding-root>/docs/skill-mesh-3-review/builds/catalog-gate/step8/`.

> **Final review (2026-11-12 10:55):** `plan-review` found one blocker, Condition paths that did not
> resolve from the build-phase project root; fixed in the roots paragraph and Steps 6 and 8 to 11. Record:
> `catalog-gate-plan-2026-11-12-final-review.md`.
>
> **Review status (2026-11-12):** Corrected a second time with the operator's answers to the morning
> sheet (items 14 to 26: the operator took every default, adopted the catalog gate as the standing done
> gate for content-only changes, and approved the path fix). The delta review
> (`catalog-gate-plan-2026-11-12-delta-review.md`) findings N1 to N7 are all applied here; the
> correction record is its "Correction round 2" section. The plan is ready for `plan-review` and
> `plan-wrap`; no further correction round is planned.

**Roots used in this plan.** `<coding-root>` is the operator's coding root (the dev workspace); every
non-skill-mesh path is written relative to it. Skill-mesh paths are repo-relative. `<evidence>` means
`<coding-root>/docs/skill-mesh-3-review/builds/catalog-gate`: the build's evidence, answers file and
condition scripts live there, **outside the skill-mesh repo**, and none of them is committed into
skill-mesh. Builds run from the integration checkout `<coding-root>/skill-mesh-wt/v3-main` (branch
`v3/main`), never from the main checkout `<coding-root>/skill-mesh`. `/build-phase` evaluates every
`Condition:` with `bash -c` **from the project root**, that is the root of the integration checkout
`<coding-root>/skill-mesh-wt/v3-main` (build-phase core, "Conditional step handling" step 2), not from
`<coding-root>`. So every Condition path (Steps 8 to 11) is written relative to that root:
`../../docs/skill-mesh-3-review/builds/catalog-gate/conditions/<script>.sh` (two levels up from
`skill-mesh-wt/v3-main` is `<coding-root>`). The scripts do not depend on the working directory: each
derives `<coding-root>` from its own location (five levels above its own directory) and uses
`git -C <coding-root>/skill-mesh-wt/v3-main` for git.

Date: 2026-11-12 (revised twice, same date). Status: PLAN ONLY, nothing built. Lane I of the 2026-11-12 overnight window.
Authority: decision sheet 2026-11-11 items 33, 45 to 51 (sections J and K), approved 23:45 PST; decision sheet 2026-11-12 (morning) section B, items 14 to 26, answered 2026-11-12.
Item 49 ranks this ahead of the next catalog create (`user-fermize`, the execution-queue skills).
Place in the release: the catalog gate is **v3 row 3** of the approved v3/v4 split. It waits on row 1 (merge the reviewed branches) and row 2 (test-gate part 1); row 4 (the over-building and over-testing guard) waits on this plan, because the gate's class table is part of that fix.

Inputs read (skill-mesh `origin/main`, which now includes `user-build-route`, pushed as `5924e27`, unless noted):
`docs/plans/seeds/seed_skill_create_pays_for_full_suite.md`; `docs/plans/seeds/seed_done_gate_too_slow_to_finish.md`
(now committed on `origin/main` as `f1759f3`; decision 8 below is closed); `CLAUDE.md` "Default DONE gate";
workspace `.claude/rules/code-quality.md` "Gate scope (full suite)"; `tests/package-integrity/test_codex_budgets.py`;
the test tree (65 `test_*.py` files at `v3/main` HEAD across `tests/`, `_shared/`, `skill-iterate/scripts/` and
`skill-eval-setup/scripts/`, plus conftest and fixture modules).

## Relationship to part 1

Part 1 (branch `v3/test-gate-scope-1`: `tools/gate_preflight.py` and the faster installer; being finished
2026-11-12 and merging into `v3/main`) delivers the machine check before full gates and the installer
slow-path fix (S-SLOW). This plan starts after part 1 has merged into `v3/main`, because Step 1 needs its
machine check and a faster installer changes the durations that set the time target. Part 2 owns: the test
classes, the class-completeness test, the catalog gate, the proof, the time target, the item 51 decision,
and the written rule.

## Phases (the operator decision is a phase boundary, not a mid-run halt)

Adopting the catalog gate changes the DONE-gate rule, which only the operator can change. The closed
build-phase halt allowlist (`code-quality.md` "Build-phase halt contract") has no "operator decision" halt,
and `plan-and-issue-flow.md` says operator steps produce no code and pure-observation operator work goes to
the phase-end UAT. So the plan is one document with two phases:

- **Phase 1 (Steps 1 to 7): build and prove the gate.** Steps 1 to 6 are code and run to completion with no
  halt. Step 7 is the last step of the phase and is the phase-end operator step: it produces only the
  operator's recorded answers. The `/build-phase` run for Phase 1 ends there normally. **Phase 1 is merged
  into `v3/main` (after its full-suite gate) before Phase 2 starts**, because Phase 2 branches off `v3/main`
  and uses the Phase 1 gate tooling.
- **Phase 2 (Steps 8 to 11): write the rule.** Starts only in a later `/build-phase --resume 8` run, after
  Phase 1 is merged and `<evidence>/operator-answers.json` exists. Steps 8 to 11 are `Type: conditional`,
  so a "no" answer skips them. A missing or malformed answers file makes the predicate exit 2 **and write a
  one-line reason to stderr**: build-phase treats exit 2 with non-empty stderr as a predicate error, not a
  skip (exit 2 with empty stderr would be read as "condition false" and skip silently). That is halt class 1
  (predicate errored), the intended fail-closed signal. No rule or guard edit is made before the operator's answer.

Answers file shape (written in Step 7 from the operator's 2026-11-12 sheet answers, or by an operator-authorized edit):
`{"recorded":"YYYY-MM-DD","adopt":"yes|no","window_minutes":N,"item51":"remove|raise|keep","item50_ends":"yes|no"}`.

## Test classes (initial assignment, to be confirmed by Step 1 measurements)

Eight classes, as the operator listed them. "Gated by catalog gate" means the class runs in the catalog gate.
Router runtime tests and telemetry have no class of their own in the operator's list; they are runtime code
and go in the installer, release and runtime tooling class. The table below is the starting proposal only:
the owner of the assignment is `tests/gate-classes.json` (Step 2), which is keyed **per file**.

| Class | Gated by catalog gate | Test files |
|---|---|---|
| catalog content | yes | `package-integrity/`: autofix_marker_single_owner, build_phase_landed_paths_roundtrip, code_consigliere_contract, codex_agent_isolation_contract, codex_capability_claims_honesty, cutover_handoff, document_output_contract, frontmatter_yaml, host_discovery, instruction_contract_single_owner, lesson_observations, phase_is_route_decision, recovery_plan_hygiene, repo_wrap_worktree_cleanup, review_deep_config_snapshot, review_deep_fail_closed, shared_ledger_checks, skill_catalog_lifecycle, user_debug_codex_contract, v2_authoring_contract, v2_orientation_contract, v2_session_contract; `production-toolchain/test_policy_contract.py` |
| generator and count pins | yes | `package-integrity/`: manifest_contract, skill_tree, codex_budgets, release_gates; `smoke/test_release_candidate_report.py` (the v2.0.3 miss; it regenerates the report and diffs it) |
| repo-wide scans | yes | `router/test_no_claude_dependency.py` (the w3 miss), `package-integrity/test_link_resolution.py`, `package-integrity/test_build_step_scripts_duplication.py`, `package-integrity/test_review_deep_scripts_duplication.py`, `package-integrity/test_gate_classes.py` (Step 2) |
| installer and release tooling | no | `distributions/`: test_distributions, test_codex_install_path, test_path_choke_point, test_build_observer_resources; `release/test_release_script.py`; `smoke/test_cross_provider_smoke.py`; `telemetry/test_telemetry.py`; `router/`: gpt_transport_precedence, path_guard, provider_host_adapters, router_scenarios, shim_parity, spend_ledger_guard |
| legacy migration | no | `distributions/test_legacy_migration.py` (204 tests per the seed) |
| host inspection | no | `distributions/test_host_inspect.py` (163 tests per the seed) |
| build-step tree | no | `distributions/test_build_step_tree.py`, `test_build_step_tree_recovery.py` (61 tests per the seed) |
| shared engines | no | `_shared/test_*.py` (5), `skill-iterate/scripts/test_*.py` (6), `skill-eval-setup/scripts/test_generate_bad_examples.py`, `tests/calibration/`, `tests/experiments/` (listed by name in the map, not by directory) |

Known judgment calls the measurements must settle: `test_release_gates`, `test_host_discovery`,
`smoke/test_release_candidate_report` and `test_distributions` may each shell out to PowerShell, which
would make them slow. **A file that mixes a fast scan with slow installer tests is split into two files**
(Step 2 mechanism); it is never classed whole into the catalog gate by guess, and there is no test-level
class list.

## Phase 1: build and prove the gate

### Step 1: Measure per-test durations and the emit cost on a quiet machine

- **Problem:** The class assignment and the time target need real durations. The seeds say not to guess
  which suites are fast. Recorded full gates run 3 h 07 min to 4 h 41 min. The catalog gate must also decide
  whether it covers tree emission and staging (the `release.ps1` staged package checks), which needs a cost.
- **Type:** code
- **Issue:** #245
- **Flags:** `--reviewers code`. Starts only after part 1 (`v3/test-gate-scope-1`) has merged into `v3/main`,
  so the measurement reflects the S-SLOW installer fix. Run from a disposable worktree of `v3/main` (the
  integration checkout's branch); never from the main checkout. The full-suite run is 3 to 5 hours, so it is
  run **detached with an exit-code sentinel file** (a background process dies with a returned agent) and the
  step reads the sentinel and the summary line, not a live stream.
- **Produces:** `<evidence>/durations-full.txt` (raw `--durations=0`
  output) and `durations-by-file.tsv` (file, test count, total seconds, `powershell_marker`, `mixed`),
  written by a small script under that same folder. `powershell_marker` is derived, not judged: a static
  scan of the file for `subprocess`, `powershell`, `install-skill-mesh`, `build-distributions`, `release.ps1`
  (the same marker list Step 2 enforces). `mixed` is set when the file has both tests that exercise a
  marker and tests that do not (per-test seconds split by that scan of the test body, and any test over
  5 s counts as slow). Also `emit-cost.txt`: wall clock of (a) `build-distributions.ps1 -Provider claude`
  into a temp dir, (b) the `release.ps1` staged package checks, (c) a `git ls-files --others
  --exclude-standard skills/` untracked check, each three times.
- **Done when:** The part 1 machine check passed (at least 2 GB free memory, no other pytest running) and
  both its numbers are recorded beside the result; the run used the repo-root `python -m pytest
  --durations=0` with no path argument; the summary line shows the collected, passed, failed and skipped
  counts (collected within a few of the baseline part 1 records, any gap explained; the 11/11 figure was 2,161, and `documentation/phase-75-baseline.md` on `v3/main` still carries older figures around 1,300, so the step records the collected count it measures and names the baseline it compared against); every test file
  appears in the TSV; `emit-cost.txt` has the three measurements. If the machine check fails, the step
  stops and reports; it does not run.

### Step 2: Per-file class map and the "no class, no pass" test

- **Problem:** Any hand-listed selection silently drops a new repo-wide scan, which is exactly how the w3
  router scan was missed. A directory glob would repeat the failure: a new scan dropped into `tests/router/`
  would be classified by the glob and the completeness test would stay green.
- **Type:** code
- **Issue:** #246
- **Flags:** `--reviewers code`. Touches test infrastructure, so it is itself gated by the full suite.
- **Produces:**
  - `tests/gate-classes.json`: an object keyed by **exact file path** (no globs, no directory entries, the
    loader rejects any key containing `*`, `?` or ending in `/`). Each entry has `class` and, for any file
    in a non-catalog class, `exclude_reason` unless the file passes the marker check below. A class has a
    `catalog` flag and a reason line. A new file must be added by name, which is what forces the
    classification decision.
  - `tests/package-integrity/test_gate_classes.py`, which:
    1. enumerates every `test_*.py` under `tests/`, `_shared/`, `skill-iterate/scripts/` and
       `skill-eval-setup/scripts/` by walking the tree (not `git ls-files`, so an untracked new file is
       caught) and fails on any file with no map entry, any entry matching no file, and any file with more
       than one class;
    2. cross-checks the walked set against `pytest --collect-only -q` file ids (disagreement either way is a
       failure, so the walk and the collector cannot diverge);
    3. **non-catalog exclusion needs a reason**: a file in a non-catalog class must contain a PowerShell
       marker (static scan, same marker list as Step 1) or carry an explicit `exclude_reason`, so a fast
       scan cannot be excluded by default;
    4. **mixed files are split, not listed**: the check is **derived in the repo** from the static marker
       scan (the same scan Step 1 uses to define `mixed`: marker hits in some test bodies and not others).
       The committed test never reads `durations-by-file.tsv`, which is untracked build evidence outside the
       repo; in another checkout that read would fail or skip (a false green). A file the scan marks `mixed`
       must not appear in the map as a single entry; the step splits it into a catalog-class file and an
       installer-class file (file-level map stays derived). A mixed-looking new file fails the check until
       split or given an `exclude_reason` that the reviewer accepts;
    5. a duration budget check is **report-only** (it needs timings, which unit tests do not have): the Step 5
       timing guard flags a catalog-class file over the budget N and a non-catalog file under N seconds with
       no marker, and prints both lists beside each gate result.
  - **A root input.** The class-map test reads the tree root from the environment variable
    `GATE_CLASSES_ROOT` (default: the repository root), so the anchors and the Step 4 replays can point it at
    a temporary or old tree. A test shows the test honors the variable (it passes on a synthetic tree whose
    map matches and fails when the variable points at one whose map does not).
  - Red-on-garbage anchors, each run in a temporary tree: (a) a synthetic unclassified `test_*.py` dropped
    into `tests/router/` must fail (the glob case); (b) a synthetic unclassified file anywhere else must
    fail; (c) a synthetic file mapped non-catalog with no marker and no `exclude_reason` must fail; (d) a
    map entry for a deleted file must fail.
- **Done when:** Every test file after splitting (the Step 1 TSV files, with each `mixed` file replaced by its
  two halves) has exactly one class; the class assignment matches the measured durations (no catalog-gate
  class contains a file the TSV marks `powershell_marker`, and every `mixed` file has been split; the TSV is
  evidence for this check, not an input to the committed test); all four anchors show red in a temporary tree; the `GATE_CLASSES_ROOT` honoring test passes; the test is itself in the
  catalog-gate class (the gate guards its own completeness).

### Step 3: The selector, the catalog gate command, and the emit check

- **Problem:** The gate is chosen by what a change touches. Content-only changes run the catalog gate;
  `tools/`, `runtime/`, `_shared` code or test infrastructure still require the full suite. A content change
  can also break tree emission or leave a new skill file untracked (release staging uses `git ls-files`), which
  no catalog test sees.
- **Type:** code
- **Issue:** #247
- **Flags:** `--reviewers code`.
- **Produces:** `tests/gate/select_gate.py`, a deterministic function from a changed-path list (`git diff
  --name-only <base>...HEAD`) to `catalog` or `full`. It takes `--root <tree>` (default: the repository root)
  and reads the map and the diff from that tree, which is what Step 4's replays require. Rule: `catalog` only when every changed path is under
  `skills/*/` (content, not `scripts/` or other support-asset code), `documentation/`, `docs/`, `config/skill-manifest.json`
  and `config/model-mapping.json` (the generated catalog files, named exactly), `tools/gen_manifest.py`
  constants-only edits (verified by diff, not by path; decision 3), `skills/inventory.json`, `README.md`,
  or a test file whose class in `tests/gate-classes.json` is "generator and count pins" (derived from the map,
  no second list). Everything else returns `full`: `tools/` (other than the constants case), `runtime/`,
  `_shared/`, test infrastructure (`tests/gate*`, conftest, fixture modules, `tests/**/_*.py`), **any edit to
  `tests/gate-classes.json` itself**, any other `config/` file (including a new one such as
  `config/pin-ledger.json`), any newly added test file, and any path it does not recognise. Unknown means
  full. Skill DELETE and RENAME return `catalog` only when no `tools/` path is touched.
  Also produced:
  - a documented command that runs the catalog gate by selecting every file whose class has the catalog flag
    in `tests/gate-classes.json`, with its collected count printed and the class and suite names listed. It
    takes `--root <tree>` (default: the repository root), passes it to the selector and sets
    `GATE_CLASSES_ROOT` for the class-map test. When the selector returns `full`, the command runs the
    catalog set **first** as a fast pre-check, then hands over to the full suite (a cheap failure shows in
    seconds; the full suite is still the gate that flips DONE);
  - an **emit check** run by the same command after the pytest set: `build-distributions.ps1 -Provider claude`
    into a temp dir for the changed skills' tree, plus the untracked-file check
    (`git ls-files --others --exclude-standard` over the skill-owned paths must be empty). It is included only
    if Step 1's `emit-cost.txt` shows it fits the time budget; if not, the command prints that the staged
    `release.ps1` checks are a required release-time step instead, and the decision and cost are recorded in
    `<evidence>/catalog-gate-design.md`. The full `release.ps1` staged check stays a release-time step in
    either case (decision 5).
- **Done when:** Table-driven tests cover each rule, including a `tools/gen_manifest.py` edit touching only
  the authoritative constants (returns `catalog`) and the same file with any other edit (returns `full`), an
  unrecognised path (returns `full`), a
  mixed change (returns `full`), a skill `scripts/*.py` edit (returns `full`), a `tests/gate-classes.json`
  edit (returns `full`), a new `config/*.json` (returns `full`), a new test file (returns `full`), a skill
  DELETE and a skill RENAME with no `tools/` path (return `catalog`) and the same with a `tools/` path
  (return `full`); the catalog gate command collects exactly the files of the flagged classes (assert the set
  equality, not a count); its output names the classes and suites that ran, as `code-quality.md` requires of
  a gate checkpoint; the emit check is red on a synthetic untracked skill file; `--root` on both the selector and the gate command is shown by a test that runs them against a second synthetic tree and gets that tree's answer; a `full` selection runs the catalog pre-check first.

### Step 4: Prove the catalog gate fails on both known misses

- **Problem:** A gate adopted without a red anchor on the failures it exists to catch is unproven
  (measurement-validity rule: calibrate against known-good and known-garbage, and score the production
  artifact: run the production selector and production gate command, not a stand-in). The proof must fail on
  the real miss, not on the class-map test.
- **Type:** code
- **Issue:** #248
- **Flags:** `--reviewers code`. Disposable worktrees only; remove them with `git -C <root> worktree remove`
  after checking `status --porcelain`. Nothing is pushed.
- **Mechanism (how the replay stays attributable):** The selector, the catalog gate command and the
  class-map test are always run **from the new branch's files, pointed at the old commit's tree** with a
  `--root <replay worktree>` argument (the gate command and `select_gate.py` take it, per Step 3; the
  class-map test reads the root from `GATE_CLASSES_ROOT`, per Step 2, which the replay sets). The replay does not overlay the new
  branch's `gate-classes.json` unchanged onto the old tree. Instead, a small helper
  `tests/gate/derive_replay_map.py` builds a per-replay map: the current map **restricted to files that exist
  in the old tree**, plus an explicit additions file `replay-<miss>-additions.json` that classifies, by exact
  path, only the files in the old tree the current map does not know (for miss 2, the new
  `tests/package-integrity/test_pin_ledger.py`, classed the way a developer forced by the completeness test
  would have classed it). The helper exits non-zero on any unmapped file not named in the additions, so the
  map matches the tree and `test_gate_classes` is **green** in the replay: it cannot be the failing test.
  The change under test is the old commit itself (its own diff is the changed-path list fed to the selector),
  so nothing is applied on top and no behaviour of the miss is simulated. The assertion is on the exact red
  set, not "red naming X".
- **Produces:** `<evidence>/proof-replay.md` with raw outputs.
  - Miss 1, v2.0.3 stale release-candidate report: tree at `d9b6648` (the last commit before `dcfe927`,
    "Refresh inherited session wrap report hashes", which repaired the stale
    `documentation/release-candidate-report.md`; confirm at replay time that the report is stale there by
    running `python tests/smoke/gen_release_candidate_report.py` and diffing). Run the catalog gate with the
    per-replay map. Expected red set is exactly `test_release_candidate_report` and nothing else. Control:
    the same procedure at `dcfe927` has an empty red set, with the full pass list recorded.
  - Miss 2, `v3/w3-pin-ledger` router scan: tree at `8c22596` (adds `config/pin-ledger.json`). Run the gate
    with the per-replay map. Expected red set is exactly `test_no_claude_dependency`, naming
    `config/pin-ledger.json` as the offender (matches `<coding-root>/docs/skill-mesh-3-review/builds/w3-narrow-router.txt`). Control: `6ad9174` or
    current main, empty red set, full pass list recorded.
  - Selection-is-the-discriminator anchor: replay each miss again with the missed test's file reclassified
    to a non-catalog class in the per-replay map. The gate must be green (the miss escapes), which shows the
    class assignment is what catches it. The `test_gate_classes` test stays green in this run because the
    reclassification carries an `exclude_reason`; its non-catalog check does not fire only because the
    additions file supplies one for this anchor, and the file's recorded reason says "anchor".
  - Selector output on both replayed change sets, recorded as found and not adjusted. Expected: miss 1
    `catalog` (a content-shaped change). Expected: miss 2 `full` (new `config/*.json` and a new test file
    both fall through to full), so for miss 2 the proof is that the catalog gate, when run, would have caught
    the failure; the plan does not claim the selector alone routes that change to the cheap gate. The policy
    for whether a new `config/*.json` should route to `catalog` is decision 6 below.
- **Done when:** Both replays have exactly the expected red set, both controls have an empty red set with the
  pass list recorded, both reclassified anchors are green, the selector output is recorded, and the raw
  outputs are in the file. If a replay's red set differs, **investigate the extra or missing red test
  first**: the old tree can be red for unrelated reasons (for example `d9b6648` also touches
  `test_distributions`, a non-catalog file). Return to Step 2 only when the cause is classification; never
  adjust the replay to make it match.

### Step 5: Time target from the measurements

- **Problem:** "Fits a working window" needs a number set from data.
- **Type:** code
- **Issue:** #249
- **Flags:** `--reviewers code`.
- **Produces:** the catalog gate's measured wall clock (three runs, quiet machine, machine check passing
  each time) with median and worst case, written to `catalog-gate-timing.md` beside `proof-replay.md`; a
  proposed target (median plus margin, rounded up) against the operator's default window of **under 10
  minutes** (decision 2); a timing guard that
  records the wall clock next to every catalog gate result and prints the Step 2 duration-budget lists.
- **Done when:** Three recorded runs exist, each with its machine-check numbers; the target is derived from
  them and stated beside the window assumption (decision 2); if the catalog gate exceeds the window,
  the step reports which class dominates and proposes moving a class out rather than loosening the target.

### Step 6: Item 51 decision note and the Phase 2 condition scripts (read-only for the guard)

- **Problem:** `test_codex_budgets.py` requires `400 < headroom < 900`. The lower bound is the real early
  warning. The upper bound exists to catch an inflated `CATALOG_FLOOR` and an over-trim; the maintenance
  list retires about 11 portable skills and adds 3, freeing about 1,500 characters, which would push
  headroom past 900 and turn the guard red. It also drives the fan-out the create seed names: v2.0.4
  shortened 21 other skills' descriptions to stay above 400. This step only decides and evidences; it does
  not edit the guard, because the edit follows the operator's choice (Step 8).
- **Type:** code
- **Issue:** #250
- **Flags:** `--reviewers code`. The decision note and scripts are documentation and shell only. No file
  under `tests/package-integrity/` changes in this step.
- **Produces:** `<evidence>/item-51-decision.md` with measured current
  headroom (computed from `_catalog_estimate()` on current `origin/main`, not from the sheet's 577 and 420
  figures, which are guard-derived estimates) and the options table:
  - Keep 900: forces batching retirements with creates; keeps the over-trim warning; rejected as the default.
  - Raise it: needs a new magic number tied to the retirement batch; it will drift again.
  - Remove it (recommended): the two things it protects are covered more directly. The inflated-floor
    case by a pin that `CATALOG_FLOOR == 8_000` and that it is the single constant the gate uses (assert
    `is`, per the single-source rule), and the over-trim case is not a defect (a roomier catalog is
    harmless). The lower bound stays unchanged. Evidence attached: a differential run, in a scratch copy of
    the test and never the live file, that the proposed form still fails when `CATALOG_FLOOR` is raised and
    still fails when headroom drops to 400, and passes with 1,500 characters removed.
  Also the four Phase 2 condition scripts under `<evidence>/conditions/` (outside the skill-mesh repo; each
  runs through the Bash tool or as a script file, never PowerShell-quoted `bash -c`; each is invoked by build-phase from the `v3-main` project root as
  `bash ../../docs/skill-mesh-3-review/builds/catalog-gate/conditions/<script>.sh`, and is
  working-directory independent: it derives `<coding-root>` from its own location (`dirname "$0"`, five
  levels up) and reads the answers file and marker by that derived path; every exit 2 prints a one-line
  reason to stderr, because build-phase reads exit 2 with empty stderr as "condition false"): `adopted.sh`
  (exit 0 iff the answers file has `adopt` = yes, exit 1 on a valid `no`, exit 2 on a missing or malformed
  file), `item51_chosen.sh` (exit 0 iff `item51` is one of remove, raise, keep; exit 2 otherwise), and
  `no_inflight_build_skill_edit.sh` (every git command is `git -C <coding-root>/skill-mesh-wt/v3-main`, with
  `<coding-root>` derived as above;
  exit 0 iff `git diff --name-only origin/main...<branch>` over every unmerged remote branch from `git
  branch -r --no-merged origin/main` touches none of `skills/build-step/` and `skills/build-phase/`; exit 1
  otherwise), and `step10_ran.sh` (exit 0 iff the marker `<evidence>/step10-ran.marker`, which Step 10 writes
  when it completes, exists; exit 1 otherwise). Each is table-tested with a synthetic answers file, branch or
  marker.
- **Done when:** The decision note exists with the measured numbers; the guard's behavior under each option
  is shown by a differential run on the scratch copy; the live `test_codex_budgets.py` is byte-identical to
  `origin/main` (checked); each condition script exits as specified on its table cases, and each is shown to resolve and give the same answer when run **exactly as the Condition line writes it**, from the root of `<coding-root>/skill-mesh-wt/v3-main` (`bash ../../docs/skill-mesh-3-review/builds/catalog-gate/conditions/<script>.sh`), and also from a different working directory (proving the self-location); a missing answers file gives exit 2 with non-empty stderr.

### Step 7: Operator adoption decision (phase-end operator step)

- **Problem:** Adopting the catalog gate changes the DONE-gate rule, which the seeds say only the operator
  can change. No agent waives or redefines the gate. This is the last step of Phase 1: the `/build-phase`
  run ends here as a normal phase end, and Phase 2 is a separate run started after the answers exist. It is
  not a halt inside a run.
- **Type:** operator
- **Issue:** #251
- **Flags:** none. Produces no code; the operator (or an operator-authorized change) writes the answers file.
- **Produces:** `<evidence>/operator-answers.json` (shape above), dated, recording the operator's answers:
  adopt the catalog gate as a standing DONE gate for content-only changes (sheet item 14: **yes**, on the
  recorded condition that Step 4 shows both known misses red and Step 5 shows the target fits); the working
  window for the time target (item 15: **10** minutes); the item 51 option (item 17: **remove**); whether the
  interim item 50 rule (agent asks before a full suite) ends with Step 11 (item 20: **yes**). The file is
  written from those sheet answers; the operator confirms the item 14 condition against the Step 4 and
  Step 5 evidence, and sets `adopt` to "no" if it does not hold.
- **Done when:** All four answers are present and dated. If `adopt` is "no", Steps 9 to 11 skip (their
  predicate exits 1); Steps 1 to 6 remain as an iteration gate only, and Step 8 still runs if `item51` is
  set.

## Phase 2: write the rule (starts only after the operator's answers)

Phase 2 start: `/build-phase --resume 8` in a fresh run, after Phase 1 is merged into `v3/main` and Step 7's
file exists. Steps 8 to 11 ride one branch off `v3/main`; the branch is not merged until Step 11 passes, so
the four rule owners change together (`code-quality.md`: the wording is carried identically and must not
diverge). If Step 10 skips, Step 11 skips with it and the branch stays unmerged until a later resume runs
Step 10 and then Step 11.

### Step 8: Implement the operator-chosen item 51 option

**Status:** DONE 2026-11-13. Commit `dd01309`, standalone by operator decision (see the 2026-11-13 amendment at the top); review pending. Option "remove": the `headroom < 900` upper bound is gone, the `headroom > 400` lower bound is unchanged, and `CATALOG_FLOOR == 8_000` is pinned as the single constant the gate's predicate uses.

- **Problem:** The guard edit must follow the operator's choice and must be its own commit, never part of the
  Phase 1 branch.
- **Type:** conditional
- **Condition:** `bash ../../docs/skill-mesh-3-review/builds/catalog-gate/conditions/item51_chosen.sh` (run
  by build-phase from the `v3-main` project root; exit 0 run, exit 1 skip, exit 2 with stderr is a predicate defect).
- **Issue:** #252
- **Flags:** `--reviewers code`. A test edit to `tests/package-integrity/test_codex_budgets.py`, gated by the
  full suite (the selector returns `full` for it).
- **Produces:** the one edit the answers file names (remove / raise / keep), on its own commit.
- **Done when:** The guard passes on current main and on a synthetic catalog with 1,500 characters removed
  (the retirement case); the differential evidence from Step 6 holds against the real edit (still fails when
  `CATALOG_FLOOR` is raised and at headroom 400, for the "remove" option); the full suite named by its
  classes passes.

### Step 9: The rule in the lifecycle guide, skill-mesh CLAUDE.md, and the workspace draft

- **Problem:** The rule must be stated once where a CREATE reads it, so no scoped exception paragraph is
  needed.
- **Type:** conditional
- **Condition:** `bash ../../docs/skill-mesh-3-review/builds/catalog-gate/conditions/adopted.sh` (resolved
  from the `v3-main` project root; every Condition below uses that form).
- **Issue:** #253
- **Flags:** `--reviewers code`. Edits skill-mesh docs and tests on the Phase 2 branch; the workspace rule
  file lives outside the skill-mesh repo and is delivered as a diff for the operator to apply.
- **Produces:** (1) `documentation/skill-catalog-lifecycle.md`: a standing "Catalog gate" section holding the
  **one source gate sentence**, the selector rule, the class table by reference to `tests/gate-classes.json`
  (one owner, no restated list), the full-suite fallback, the emit-check decision from Step 3, and removal of
  the scoped code-consigliere and user-dr release exception paragraphs (lines 27 to 44 on origin/main) that
  the new section makes redundant; the lifecycle contract test (`test_skill_catalog_lifecycle.py`, which pins
  contract sentences) updated in the same change. (2) skill-mesh `CLAUDE.md` "Default DONE gate": the catalog
  gate for content-only changes and the full suite for the rest, the Phase CD scoped exception paragraph left
  as history, and the "Fast iteration gates" block extended with the measured fast repo-wide set (item 46).
  The step first locates the "CLAUDE.md Testing bullet (stub)" that `code-quality.md` names; the workspace
  `CLAUDE.md` in view has no such bullet, so the owner table records which file carries it, or that none
  does and the draft diff drops that claim. (3) a drafted replacement for the workspace
  `.claude/rules/code-quality.md` "Gate scope (full suite)" note, as a diff, with the non-conflict line kept
  (changed-check governs iteration, this rule governs the DONE gate).
- **Done when:** A table of the four owners (lifecycle guide, skill-mesh `CLAUDE.md`, workspace
  `code-quality.md`, `build-step` and `build-phase` cores) exists with the gate sentence status per owner;
  for the three owners this step changes, a grep finds the same sentence (stored once in the lifecycle guide,
  the others quote or point to it). The fourth is Step 10, and the all-four check is Step 11. The lifecycle
  contract test and the full suite pass (this step touches `tests/`); the representative-skill report check
  (`gen_release_candidate_report.py`) is run if any of the four representative cores changed (none should).

### Step 10: Update the build-step and build-phase gate prose

- **Problem:** `build-step` and `build-phase` carry the gate wording, and they are skills.
- **Type:** conditional
- **Condition:** `bash ../../docs/skill-mesh-3-review/builds/catalog-gate/conditions/adopted.sh && bash
  ../../docs/skill-mesh-3-review/builds/catalog-gate/conditions/no_inflight_build_skill_edit.sh` (a skip here
  means an in-flight build touches those skills; the step is re-evaluated at the next resume, and Step 11
  skips with it).
- **Issue:** #254
- **Flags:** `--reviewers code`. `build-phase` is a representative skill, so `release-candidate-report.md`
  must be regenerated in the same change. Goes through the catalog lifecycle guide's UPDATE operation. The
  change set includes provider adapters, so the gate is whichever the selector returns, with the suites that
  ran named; the selector's answer is recorded.
- **Produces:** updated `skills/build-step/core.md` and `skills/build-phase/core.md` gate prose, regenerated
  provider adapters and catalog files, regenerated release-candidate report, and the marker
  `<evidence>/step10-ran.marker` (written last, on completion).
- **Done when:** `<evidence>/step10-ran.marker` exists (written last, after the gates below hold; Step 11's
  Condition reads it); The gate sentence equals the Step 9 source sentence; no gate in either core weakens (a
  wrapper may never weaken a gate); the gate that flips this step DONE is whichever the selector returns,
  with the suites that ran named; the build-phase halt-contract allowlist is unchanged (a gate change adds
  no sixth halt class).

### Step 11: Four-owner consistency check and release of the diff

- **Problem:** The four owners must carry one sentence before anything lands.
- **Type:** conditional
- **Condition:** `bash ../../docs/skill-mesh-3-review/builds/catalog-gate/conditions/adopted.sh && bash
  ../../docs/skill-mesh-3-review/builds/catalog-gate/conditions/step10_ran.sh` (Step 11 skips whenever Step 10
  skipped, so a skipped Step 10 is never a mid-run failure).
- **Issue:** #255
- **Flags:** `--reviewers code`. Read-only check plus the hand-off of the workspace diff.
- **Produces:** one tabulated grep over all four owners (lifecycle guide, skill-mesh `CLAUDE.md`, workspace
  `code-quality.md` draft, `build-step` and `build-phase` cores) showing the same gate sentence, and the
  workspace `code-quality.md` diff for the operator to apply (decision 7: applied only after this step
  passes). If the `adopt` answer and `item50_ends` are both yes (the recorded answers), the diff also
  retires the interim item 50 ask-first wording, at the same time and not earlier.
- **Done when:** The table shows the identical sentence at all four owners (the exact sentence is stored once
  in the lifecycle guide and the other three quote or point to it); Step 10 has run (this step's Condition guarantees it); the full
  suite, named by its classes, passes on the Phase 2 branch; only then is the branch eligible to merge.

## Order and dependencies

Phase 1: 1 (needs part 1 merged into `v3/main`) -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 (phase-end operator step; the
run ends). Phase 1 then **merges into `v3/main`** (full-suite gate, since it touches test infrastructure).
Phase 2, a separate run after Phase 1 is merged and the answers file exists: 8 -> 9 -> 10 -> 11, with
Step 11 skipping when Step 10 skips. The Phase 1 steps may land on one branch off `v3/main`; each touches
test infrastructure so each uses the full suite until the catalog gate is adopted. The item 51 guard edit
is never on the Phase 1 branch.

## Decisions (answered 2026-11-12)

The operator answered every open item on the 2026-11-12 morning sheet (section B) by taking the stated
default, so none is open. Plan decision N is sheet item 13+N; the plan assumes the answer shown.

1. **Adopt the catalog gate as a standing DONE gate for content-only changes (Step 7). Sheet item 14.**
   Answer: yes, once Step 4 shows both misses red and Step 5 shows the time target fits. The operator
   confirms that condition in Step 7.
2. **Working window (sets the time target). Item 15.** Answer: the catalog gate target is under 10 minutes,
   confirmed against Step 5's measurement.
3. **A `tools/gen_manifest.py` constants edit counts as content. Item 16.** Answer: yes, only when the diff
   touches only the authoritative constants, verified by diff and not by path; otherwise `full`.
4. **Item 51. Item 17.** Answer: remove the 900 upper bound, with the pin that `CATALOG_FLOOR == 8_000` and
   is the single constant used.
5. **Emit and release scope. Item 18.** Answer: the catalog gate includes the bounded emit check and the
   untracked-skill-file check, with `release.ps1` as a release-time step, if Step 1's `emit-cost.txt` shows
   it fits the target; otherwise the whole emit check is release-time only and the rule text says so.
6. **New `config/*.json` and new test files (the w3 miss). Item 19.** Answer: `full` (fail closed), with the
   catalog gate run first as a fast pre-check whenever the selector returns `full` (Step 3 builds that).
   Routing new config files to `catalog` is not adopted: it weakens unknown-means-full.
7. **Workspace `.claude/rules/code-quality.md` diff (outside the repo) and the interim item 50 ask-first
   rule. Item 20.** Answer: apply the diff only after Step 11 passes, and end the item 50 rule at the same
   time, not earlier.
8. **Landing the untracked `seed_done_gate_too_slow_to_finish.md`. Item 21.** Answer: its owner commits it on
   `origin/main` before Phase 1 starts. Status: done (`f1759f3`).
9. **Path blocker (delta N1). Item 22.** Answer: the evidence, answers file and condition scripts live under
   `<coding-root>`, outside skill-mesh; predicates run with `<coding-root>` as the working directory; git
   commands inside them are `git -C <coding-root>/skill-mesh-wt/v3-main`. Review correction: build-phase
   runs a Condition from the project root, not from `<coding-root>`, so the Condition paths are
   `../../docs/...` from the `v3-main` root and the scripts locate `<coding-root>` from their own path.
   Applied in the roots paragraph and Steps 6 to 11.

The answers file records only decisions 1, 2, 4 and 7; decisions 3, 5, 6, 8 and 9 are plan text.
