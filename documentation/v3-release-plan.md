# Release v3.0.0 (plan)

This is the execution copy for build-phase, copied 2026-11-12 from the operator's planning records in the coding root (`<coding-root>/docs/skill-mesh-3-review/`), where its reviews and the operator's answers live. Step status is recorded here from now on.

Date: 2026-11-12. Status: PLAN ONLY, nothing built, tagged, published or installed.
Covers row 8 of the approved v3 and v4 split (`<coding-root>/docs/skill-mesh-3-review/v3-v4-split-proposal-2026-11-12.md`): "Release v3.0.0 and check
that installed equals released. The GPT adapters ship one last time under their deprecation note."

**Roots.** Skill-mesh paths are repo-relative. `<coding-root>` is the workspace folder that holds the skill-mesh
checkouts and the other projects. `<user-home>` is the operator's home folder. `<evidence>` means
`<coding-root>/docs/skill-mesh-3-review/builds/release-v3.0.0`: evidence, the release notes draft, the zip and the
comparison outputs live there, outside the skill-mesh repo, and none of them is committed into it. Builds run from
the integration checkout `<coding-root>/skill-mesh-wt/v3-main` (branch `v3/main`), never from the main checkout. Helper scripts cited as `builds/...` (the v2.0.4 zip recipe, `rc-compare.py`,
`rc-classify.py`, `rc-garbage-anchor.py` and `release-notes-v2.0.4.md`) live in
`<coding-root>/docs/skill-mesh-3-review/builds/`, outside the skill-mesh repo.
This plan is meant to be committed to a public repository, so it carries no absolute user paths.

## What this release is

The release waits for rows 1 to 7 of the split. When they have all landed, `v3/main` holds:

- the merged reviewed branches (the build-route rebase, the review-deep lint fixes, docs housekeeping);
- test-gate part 1 (low-memory check, faster installer) and the catalog gate;
- the over-building and over-testing guard;
- the catalog cleanup batch (five skills retired, one folded, two moved to dev-observatory, `user-fermize`
  promoted, `plan-trim` merged into `plan-merge`, `user-afterparty` changed, `user-project` replaced by a script);
- the `user-pm` revamp and the skill inbox hooks.

It is the first release since v2.0.4 (tag `v2.0.4`, 2026-11-11). Every earlier release was cut the same way: a
`release/<name>` branch from the release commit, `tools/release.ps1 -Provider all`, a hand-built zip with its SHA-256
file, a tag, a GitHub release carrying the zip and notes, then the staged `dist/` installed into the live profiles.
This plan keeps that shape. It changes no tool and weakens no gate.

## Decisions already made

- **D5 (2026-11-11, restated in the split proposal, row 8):** Copilot is deprecated. The GPT profile ships
  unchanged in this release with a deprecation note and is dropped in the next one. The release after this one is
  governed by the "Planned catalog change: Copilot deprecation" section of `docs/plans/master_plan.md` and is not
  part of this plan.
- **Version number: `3.0.0`, tag `v3.0.0`.** Skills are retired and replaced, which changes what users have
  installed. That is a major version. Earlier tags are `v2.0.0` to `v2.0.4`; there is no version field in the
  manifest or the tools, so the number lives in the tag, the zip name, the release notes and the docs that name the
  current release.
- **The done gate** is the catalog gate (its command and selector are specified in `catalog-gate-plan-2026-11-12.md` in
  `<coding-root>/docs/skill-mesh-3-review/`) once it has landed, otherwise the full repo-root `python -m pytest`. The
  gate's own rule still applies: a change that touches `tools/`, `runtime/`, `_shared` code or test infrastructure
  selects the full suite. The release range touches those (the installer and the gate itself), so expect the
  selector to say `full` (Step 4).
- **Publication and install each need explicit operator authority.** They are Steps 9 and 10. Nothing before Step 9
  pushes a branch, creates a tag or touches a GitHub release, and nothing before Step 10 writes into a live profile.

## Steps

<!-- autofix-applied: 2026-11-12 -->
### Step 1: Entry check (rows 1 to 7 are done and the tree is clean)

- **Problem:** The release must not be cut from a tree that is missing a row, carries unreviewed work, or sits on a
  machine that cannot run the gates. Skipping this check is how an earlier release candidate went out half-wrapped.
- **Type:** code
- **Issue:** #
- **Flags:** `--reviewers code`
- **Files:** `<evidence>/entry-check.md` (new; reads `plan.md`, `config/skill-manifest.json`, `tests/package-integrity/test_codex_budgets.py`)
- **Produces:** `<evidence>/entry-check.md`, a read-only record (no repository change) holding:
  - for each of rows 1 to 7, the plan that owns it, the merge commit on `v3/main`, and the phase's recorded
    independent-review verdict (read from `plan.md` and the plan files; a row with no verdict is a blocker);
  - `git status --porcelain` for the integration checkout (must be empty) and the count of commits since `v2.0.4`;
  - the catalog counts from `config/skill-manifest.json` (skills, portable, Claude-only, Codex-adapted) and the Codex
    initial-list headroom (the `tests/package-integrity/test_codex_budgets.py` figure; it was 421 characters at the
    last record and retiring five skills raises it);
  - whether `user-orient` is deleted (the cleanup plan removes it in the same batch as its row 5; the release notes
    name it only if it is);
  - a list of every file under `skills/` that is untracked (release staging uses `git ls-files`, so an untracked
    skill file would silently be left out);
  - free memory (`Available MBytes`) at the time of reading, and whether another test run is active.
- **Done when:** the record shows all seven rows landed with a verdict, an empty `git status`, no untracked
  skill file, and counts that match the release notes inputs. Any gap stops the plan with the gap named; it is a
  finding, not something to patch inside this plan.

<!-- autofix-applied: 2026-11-12 -->
### Step 2: Version references, deprecation note and the release-candidate report

- **Problem:** Several documents name v2.0.4 as the current release, and the GPT profile must carry a deprecation
  note a user sees before they rely on it. The release-candidate report is a generated file that goes stale
  whenever one of its four representative skills changes. The recorded rule is to regenerate it in the same change,
  before the slow gate, not after.
- **Type:** code
- **Issue:** #
- **Flags:** `--reviewers code`
- **Files:** `README.md`, `documentation/v2-installation.md`, `documentation/providers/gpt.md`, `documentation/release-candidate-report.md`, `docs/workflows/README.md`, `docs/workflows/intro.md`, `plan.md` (only the hits the grep table marks `update`)
- **Produces:** one commit on `v3/main`, content only, containing:
  - `grep` of the whole repository for `2.0.4`, with one row per hit and a verdict (`current-release statement:
    update` or `historical record: leave`). Only the first kind changes. Known hits to check: `README.md`,
    `documentation/v2-installation.md`, `docs/workflows/README.md`, `docs/workflows/intro.md`,
    `documentation/skill-catalog-lifecycle.md`, `plan.md`. Release records for v2.0.x are history and stay as they
    are. The README release link is **not** updated here, because the tag does not exist yet (Step 12 does it);
  - the deprecation note, worded as in "Release notes draft" below, in `README.md` (near the install section),
    `documentation/providers/gpt.md` (top of file) and `documentation/v2-installation.md` (GPT install paragraph).
    No adapter, build row or tool changes: the profile ships as it is;
  - `documentation/release-candidate-report.md` regenerated with `python tests/smoke/gen_release_candidate_report.py`
    and committed even if the diff is empty (an empty diff is recorded as "no change"). If any of the four
    representative skills (`build-phase`, `plan-init`, `review-gauntlet`, `session-wrap`) changed since `v2.0.4`,
    expect hash rows to move. The generator's GPT rows stay, because the GPT profile still ships.
- **Done when:** the grep table is complete with a verdict for each row, the report regenerates with no further diff
  on a second run, `git diff v2.0.4..HEAD -- documentation/release-candidate-report.md` is explained in the commit
  message, and a fresh-context reviewer has confirmed that no gate, test or tool changed in this commit and that the generator (`tools/render-workflow-cards.py`) does not overwrite the
  `docs/workflows` edits.

<!-- autofix-applied: 2026-11-12 -->
### Step 3: Release notes draft and the numbers it quotes

- **Problem:** The notes are what a user reads to decide whether to upgrade. They must say, in plain language,
  what changed since v2.0.4, what disappears, and that GPT is on its way out. Every number in them must come from the
  tree, not from memory.
- **Type:** code
- **Issue:** #
- **Flags:** `--reviewers code`
- **Files:** `<evidence>/release-notes-v3.0.0.md` (new), `<evidence>/notes-numbers.md` (new)
- **Produces:** `<evidence>/release-notes-v3.0.0.md` (not committed into skill-mesh; it is the text of the GitHub
  release), and `<evidence>/notes-numbers.md` giving the source of each quoted number (manifest counts, the file
  count the staged `CHECKSUMS.txt` will cover, the zip entry count are filled in at Step 7 and re-checked at Step 8).
  The structure follows `release-notes-v2.0.4.md` from the v2.0.4 build folder: a one-paragraph summary, then a
  short list per kind of change, a "Validation" list stating exactly which gate ran (named suites and the real
  summary line), a "Known limits" line, and "Restart host sessions after upgrading."
- **Done when:** the draft contains every section in "Release notes draft", each retired or changed skill from the
  cleanup plan's final list is named once, every number has a source line, and no sentence claims a gate that did not
  run. The Validation list is left with marked blanks until Step 4 and Step 6 have results; Step 8 checks they were
  filled from the records.

<!-- autofix-applied: 2026-11-12 -->
### Step 4: Done gate on the release commit

- **Problem:** The release commit needs the project's own truth-check before it is staged. Per the rule in
  `CLAUDE.md`, the gate that flips a phase DONE is the full suite unless the catalog gate has landed and the selector
  chooses it. The full run is slow (hours) and sensitive to free memory, so it must run detached with a sentinel and
  must not share the machine with another heavy run.
- **Type:** wait
- **Issue:** #
- **Flags:** `--reviewers none`
- **Files:** `<evidence>/gate-record.md` (new) and the raw outputs beside it
- **Produces:** `<evidence>/gate-record.md` and the raw outputs beside it:
  1. the selector's answer for `git diff --name-only v2.0.4...HEAD` and for the delta since the last commit a full
     run passed on (if one is recorded), with the paths that decided it. If either range selects `full`, the full repo-root run on the release commit
     is required; the delta answer is informational only;
  2. the run itself: if the selector says `catalog`, the documented catalog gate command, with its printed collected
     count and class list; if it says `full`, the catalog set first as a fast pre-check, then the repo-root
     `python -m pytest` with no path argument, started detached (`Start-Process`, exit code written to a sentinel
     file), with free memory read at launch (hold if under 2 GB, per the recorded memory-starved-machine finding);
  3. the real summary line (passed, failed, skipped, collected) and the exit code.
- **Done when:** the sentinel exists and holds exit code 0 with 0 failed. A red run is **not** waved through and
  the gate is not narrowed to make it green. A stopped or incomplete run is recorded as INCOMPLETE and does not pass
  this step; only the operator can accept a different gate, in writing, as for v2.0.4 (see Open item 1). This step
  halts the orchestrator on purpose (wait type); resume with `--resume 5`.

<!-- autofix-applied: 2026-11-12 -->
### Step 5: Release branch and commit identity

- **Problem:** `release.ps1` stages only committed files (`git ls-files` and `git checkout-index`), so the release is
  exactly one commit. That commit has to be named and frozen before anything is built from it.
- **Type:** code
- **Issue:** #
- **Flags:** `--reviewers none`
- **Files:** `<evidence>/release-commit.md` (new)
- **Produces:** a local branch `release/v3.0.0` at the commit Step 4 tested (the same commit; if any commit landed
  after the gate ran, the gate is stale and Step 4 reruns). Recorded in `<evidence>/release-commit.md`: the commit
  hash, `git status --porcelain` empty, and `git ls-files -u` empty (an unmerged index makes `release.ps1` refuse).
  Nothing is pushed.
- **Done when:** the branch exists locally at the gated commit and the record shows both checks empty.

<!-- autofix-applied: 2026-11-12 -->
### Step 6: Stage and build the release with `release.ps1 -Provider all`

- **Problem:** The release builds from the staged tree, with the integrity gate run inside it, and then checksums
  every generated file. The default provider set is `both` (Claude and GPT); the Codex profile ships only when asked
  for, so the release needs `-Provider all` (Claude, GPT and Codex). GPT is included on purpose (D5).
- **Type:** code
- **Issue:** #
- **Flags:** `--reviewers none`
- **Files:** `<evidence>/stage/` (new), `<evidence>/release-run.txt` (new); runs `tools/release.ps1`
- **Produces:** the staged tree at `<evidence>/stage` and its `CHECKSUMS.txt`, from this command run at the
  repository root on `release/v3.0.0`:

```
powershell -File tools/release.ps1 -Provider all -StageDir <evidence>/stage
```

  plus `<evidence>/release-run.txt` (its output) and the count of `dist/` files it checksummed. The stage directory
  must be empty or carry the script's own marker; the script refuses anything else. Staged package-integrity must
  report its own summary line.
- **Done when:** exit code 0; the output shows the staged package-integrity run with 0 failed; `CHECKSUMS.txt` is
  written and its file count is recorded; and the three profile folders `dist/claude`, `dist/gpt` and `dist/codex`
  all exist in the stage. A failed integrity run aborts the release and is a stop, never a rerun with a narrower path.

<!-- autofix-applied: 2026-11-12 -->
### Step 7: Build the release zip by the existing recipe, with checksums

- **Problem:** `release.ps1` makes no archive. The zip for every release so far was built by a small script kept
  with the v2.0.4 build evidence (`builds/user-dr-v2.0.4/build_zip.py`). It orders entries by a case-insensitive
  path key that reproduces the previous release's order, excludes only the stage marker file, verifies that every
  entry matches the stage byte for byte, checks that `CHECKSUMS.txt` is covered, and writes the SHA-256 file with the
  same line ending as the previous release's file. Its arguments are `ref_zip stage out_dir version`.
- **Type:** code
- **Issue:** #
- **Flags:** `--reviewers none`
- **Files:** `<evidence>/zip/skill-mesh-v3.0.0.zip` (new), `<evidence>/zip/skill-mesh-v3.0.0.sha256` (new), `<evidence>/zip-record.md` (new)
- **Produces:** `<evidence>/zip/skill-mesh-v3.0.0.zip` and `<evidence>/zip/skill-mesh-v3.0.0.sha256`, built by a
  **copy** of the recipe kept in `<evidence>` (the original v2.0.4 evidence is not edited). The copy differs from the
  original in one way only: the original reads the reference checksum file under the fixed name
  `skill-mesh-v2.0.3.sha256`, so the copy takes that name from the reference zip instead. The reference zip is the
  v2.0.4 release zip (its hash is recorded in `plan.md`; see Open item 3 for where the file is held; download the v2.0.4 `.sha256` asset into the same folder as the zip). Run it with
  `python -I`. The record states the entry count, the number of `CHECKSUMS.txt` lines, and that the number of
  unmatched checksum paths is 0.
- **Done when:** the recipe's three assertions pass (the ordering rule reproduces the reference zip's order; the
  entry list equals the stage; every entry's bytes equal the stage's), `testzip()` is clean, the `.sha256` file
  matches an independent `Get-FileHash -Algorithm SHA256` of the zip, and the zip and its hash are recorded in
  `<evidence>/zip-record.md`. The zip is not uploaded anywhere yet.

<!-- autofix-applied: 2026-11-12 -->
### Step 8: Independent review of the release package

- **Problem:** The author of a release package should not be the only one to read it. The reviewer checks the whole
  package against the plan, not just the parts the builder looked at.
- **Type:** code
- **Issue:** #
- **Flags:** `--reviewers code`
- **Files:** `<evidence>/release-review.md` (new)
- **Produces:** `<evidence>/release-review.md`, from a fresh-context reviewer given the frozen inputs (the release
  commit hash, the stage, the zip, both records, the notes draft and this plan) and no summary of the builder's
  conclusions. It must check:
  - the zip's file list equals the stage, and `CHECKSUMS.txt` covers every `dist/` file of all three profiles;
  - the zip contains no untracked-looking file, no scratch file, no absolute user path (a search of the zip's text
    files for the operator's user folder and name);
  - the catalog counts and retired skills in the notes match the manifest in the staged tree, and the Codex profile
    has an adapter for every portable skill;
  - the deprecation note appears in the notes and in the three documents of Step 2;
  - the Validation list in the notes names only gates that ran, with the real summary lines from Step 4 and Step 6.
- **Done when:** the verdict is PASS with 0 blocking findings. Findings are fixed and re-reviewed by the same
  reviewer, not argued past. A fix that changes the tree sends the plan back to Step 4 (the gate is stale).

<!-- autofix-applied: 2026-11-12 -->
### Step 9: Operator: authorize publication (push, tag, GitHub release)

- **Problem:** Pushing a branch, creating a public tag and publishing a release are visible to everyone and are
  hard to take back (a published tag and its download cannot be quietly replaced). They need your explicit go.
- **Type:** operator
- **Issue:** #
- **Flags:** none
- **Files:** `<evidence>/publish.md` (new)
- **Produces:** nothing in code. You read `<evidence>/release-review.md`, `<evidence>/gate-record.md` and the notes
  draft, and answer one question: publish v3.0.0 from the commit named in `<evidence>/release-commit.md`? If yes, the
  coordinator then does exactly this and nothing more, run from the skill-mesh repository (not the coding root),
  recording each command's output in `<evidence>/publish.md`:
  1. check `origin/main` has not moved since the release commit's base (if it has, stop and report);
  2. push `release/v3.0.0`; fast-forward `origin/main` to the release commit (no force);
  3. create an annotated tag `v3.0.0` on that commit and push it;
  4. create the GitHub release `v3.0.0` from the tag with title `Skill Mesh v3.0.0`, the notes file as the body, and
     `skill-mesh-v3.0.0.zip` plus `skill-mesh-v3.0.0.sha256` as assets. Not a draft, not a pre-release.
- **Done when:** the tag resolves to the release commit on origin, the release page lists both assets, and the
  downloaded zip's SHA-256 equals the recorded one (download it into its own new empty folder and hash it there). If
  you say no, or want a change, the plan returns to the step that owns it.

<!-- autofix-applied: 2026-11-12 -->
### Step 10: Operator: authorize the install, then install the Claude and Codex profiles

- **Problem:** The live profiles are what the operator's sessions actually run, and an install can replace or remove
  files. It needs your go. Three facts make this install different from v2.0.4's:
  - the installer removes a file it owns only when the file on disk still matches the hash it recorded, so retired
    skills' files are cleaned up only if nobody edited them; mismatches are reported, not forced;
  - the Codex home currently holds a **foreign** `user-fermize/SKILL.md` and an **empty** `user-build-route/`
    directory (11/12 measurement). The released catalog includes `user-fermize`, so the Codex install will refuse the
    collision. This plan never uses `-Force` (it takes over any colliding file); the one file is backed up and
    removed by hand, with your written approval naming that path;
  - the Claude home also holds foreign `meeting-sheet/SKILL.md` (tracked by the coding-root repo) and the host-owned
    `synced/` folder. Neither is touched and neither is in the release.
- **Type:** operator
- **Issue:** #
- **Flags:** none
- **Files:** `<evidence>/pre-install-inspect.txt` (new), `<evidence>/install-claude.txt` (new), `<evidence>/install-codex.txt` (new); runs `tools/inspect-host-install.ps1` and `tools/install-skill-mesh.ps1`
- **Produces:** nothing in code. Before you answer, the coordinator runs the read-only inspector on both homes and
  puts the result in `<evidence>/pre-install-inspect.txt`:

```
powershell -File tools/inspect-host-install.ps1 -Home <coding-root>
```

```
powershell -File tools/inspect-host-install.ps1 -Home <user-home>
```

  You then authorize, in writing, these installs from the staged dist of Step 6 (not from a rebuild):

```
powershell -File tools/install-skill-mesh.ps1 -Provider claude -Home <coding-root> -DistDir <evidence>/stage/dist
```

```
powershell -File tools/install-skill-mesh.ps1 -Provider codex -Home <user-home> -DistDir <evidence>/stage/dist
```

  Run the Codex install as written, with no `-Force`. Its validate-before-mutate refusal changes nothing and lists
  every foreign collision. If that list is exactly `user-fermize/SKILL.md`, you may approve in writing, naming that
  path only, that the coordinator copies that one file into `<evidence>/install-backup/`, removes it, and reruns the
  same command. Any other collision stops the plan and returns to you.
  If you would rather not give up that file, the Codex install is skipped and the check in Step 11 runs on Claude
  only (Open item 4). The GPT profile is **not** installed (Open item 2). The Claude install runs first; its output
  and exit code go to `<evidence>/install-claude.txt`, then Codex to `<evidence>/install-codex.txt`.
- **Done when:** each authorized install exits 0 and prints no refusal. A refusal is reported verbatim and the plan
  stops: `-Force` is never added. Then restart the host sessions (Claude and Codex) before
  trusting what they load.

<!-- autofix-applied: 2026-11-12 -->
### Step 11: Installed-equals-released check, with a known-garbage anchor

- **Problem:** "Installed equals released" can only be answered by rebuilding the release and comparing it with the
  installed files, because the install ledger records no version, tag or commit (11/12 finding). The 11/12 check
  (`builds/rc-compare.py`, `rc-classify.py`, `rc-garbage-anchor.py`) did this for v2.0.4 and returned 161 of 161
  Claude and 147 of 147 Codex files identical. This step repeats it for v3.0.0 with the same comparator. A check that
  has only ever been shown to pass on good data is not evidence, so the anchor comes first.
- **Type:** code
- **Issue:** #
- **Flags:** `--reviewers code`
- **Files:** `<evidence>/installed-equals-released.md` (new)
- **Produces:** `<evidence>/installed-equals-released.md`, built in this order:
  1. **Anchor first.** Run the known-garbage anchor (copied into `<evidence>`, with the install and ledger paths
     taken from arguments instead of fixed values) against the **new** Codex install, and a second copy of it for
     Claude. It builds a fake dist from the installed owned files, plants one altered file, one removed file and one
     added file, and must report differ 1, missing 1, the removed file as extra, and at least 1 raw defect. If it
     does not go red as expected, stop: the check cannot be trusted and no result below counts. Run with `python -B`. The anchor covers comparison (c) only, so also alter one byte in a scratch copy of the
     extracted zip `dist/` and confirm comparison (a) reports 1 differ, and do the same to a scratch copy of
     `CHECKSUMS.txt` for comparison (b).
  2. **Three-way comparison.** Rebuild the release independently in a new detached worktree at tag `v3.0.0` (or at the release commit if the tag was not authorized)
     (`build-distributions.ps1 -Provider claude`, then `-Provider codex`, with a free-memory check before each, as on
     11/12). Then compare: (a) the rebuild with the **zip's** `dist/` (extracted into its own new empty folder,
     read with `python -I`), (b) the rebuild with the **stage's** `CHECKSUMS.txt`, (c) the rebuild with each installed
     tree and ledger, through `rc-compare.py` with the arguments `provider dist_root install_root ledger_path
     worktree out_json`. Remove the worktree afterwards with plain `git worktree remove` after `status --porcelain`.
  3. **Classify extras** with `rc-classify.py`, using the 11/12 classes (runtime state, tool caches, coding-root
     tracked content, foreign top-level entries) and add one class: **retired-skill leftovers**, meaning files under
     a skill that v3.0.0 retired. These are real drift if the ledger no longer owns them and the files still exist.
  4. **Ledger integrity**: owned files, missing, hash mismatches, and built files not in the ledger.
- **Done when:** the anchor was red as expected, and for each installed host: every built file is present and
  byte-identical to the rebuild, the rebuild equals the zip and the stage's checksums, 0 differ, 0 missing, 0 real
  extras, 0 retired-skill leftovers, and the ledger owns exactly the released file set. Any nonzero line is reported
  as drift with the file, the likely cause and the fix, and is not closed by editing the check.

<!-- autofix-applied: 2026-11-12 -->
### Step 12: Close-out records

- **Problem:** The release is not finished until the repository's own status record, the README and the documents
  that name the current release say so, and the evidence is in one place. Earlier releases did this after the tag in
  a separate commit.
- **Type:** code
- **Issue:** #
- **Flags:** `--reviewers code`
- **Files:** `plan.md`, `README.md`, the evidence folder's `SUMMARY.md`
- **Produces:** one docs-only commit on `v3/main` (then the same on `origin/main` by fast-forward only after a
  separate written yes from you, asked once you have read the close-out; Step 9's authority does not cover it):
  - `plan.md`: a "Release v3.0.0" section in the shape of the v2.0.4 one: commit, tag, the zip's name, entry count and
    SHA-256, the `CHECKSUMS.txt` file count, the gate evidence (suite names and real summary lines, and any
    incomplete run recorded as incomplete), which profiles were installed, and the Step 11 verdict;
  - `README.md`: the "is released" link and the "what's new" line updated to v3.0.0, now that the tag exists;
  - the lessons the release taught, as a seed file under `docs/plans/seeds/` only if there were any;
  - the evidence folder's `SUMMARY.md` row for this release.
- **Done when:** a docs-only gate (the catalog gate, or the selector's answer for this diff) is green, the commit is
  pushed only after that separate yes, and `git diff` shows no change to `skills/`, `tools/`, `runtime/`, `config/` or `tests/`.

## Release notes draft

Plain language, for the GitHub release body. Items in angle brackets are filled from the tree in Step 3.

> **Skill Mesh v3.0.0: a tidier catalog, a project-manager skill that plans lanes, and a test run that fits the change**
>
> This is the first release since v2.0.4 (which added `/user-dr`). It changes what is in the catalog, so it is a
> major version. The catalog now holds <N> skills (<P> portable, <C> Claude-only).
>
> **What changed for you**
> - **A project-manager skill that plans lanes.** `/user-pm` was rebuilt. <One sentence from the user-pm plan's
>   outcome, including the main lane and what it reads.>
> - **Skills see their notes.** Claude and Codex sessions now show the notes other sessions left for a lane (the
>   inbox hooks).
> - **A test run that fits the change.** A catalog-only change no longer needs the multi-hour full test run; the
>   catalog gate picks the right set. Changes to tools, the runtime or test code still run everything.
> - **A guard against over-building.** <One sentence from the guard plan's outcome.>
> - **Faster installer, and a low-memory check** before a long test run starts.
> - **`/user-build-route` and a plan-expedite routing fix**, written after v2.0.4 and now released.
> - **Review lint fix.** The review-deep lint pre-pass used to report zero findings every time; it now reports real
>   ones.
>
> **Skills that went away or moved**
> - Retired: `goblin-suggest`, `goblin-sweep`, `goblin-do`, `judge-motion`, `user-lavishify`; also `user-orient` if Step 1 recorded it deleted.
> - Folded in: `user-shakedown` is now a flag of `user-walkthrough`; `plan-trim` is now `plan-merge --trim`.
> - Moved to dev-observatory: `build-observer`, `observatory-doctor`.
> - Replaced by a script: `user-project`.
> - New in the catalog: `user-fermize`. Changed: `user-afterparty` now runs monthly and owns usage telemetry.
>
> **GitHub Copilot (GPT) support is deprecated**
> This is the last release that ships the GPT profile. It is included unchanged, so nothing breaks today, but the
> GPT adapters, the `.github/skills` install target and the GPT build will be removed in the next release. Skill Mesh
> will then support Claude Code and the OpenAI Codex CLI. If you use the GPT profile, plan to move to one of those.
>
> **Upgrading**
> Install the Claude and Codex profiles from the zip with the installer, then restart your sessions. The installer
> removes retired skills' files only if you have not edited them, and refuses to overwrite a file it does not own
> unless you tell it to (with a backup).
>
> **Checks run**
> <Named suites and the real summary lines from Step 4 and Step 6; anything that did not complete says so.>
> Installed files were compared with a rebuild of this release: <counts from Step 11>.
>
> **Download:** `skill-mesh-v3.0.0.zip`, with its SHA-256 in `skill-mesh-v3.0.0.sha256`. Restart host sessions after
> upgrading.

## Open for redline

Each item has a default that stands if you do not answer.

1. **If the full test run cannot finish, what then?** The full run took more than 4 hours at the last measurement,
   and was stopped before completing for v2.0.4 and v2.0.2. Default: this plan does **not** accept a narrower gate by
   itself. An incomplete run is recorded as incomplete, Step 4 stays unpassed, and you are asked once, in writing, for
   a named replacement set (as you did for v2.0.4), which the release notes then name as exactly that. Changes if you
   would rather pre-approve the replacement now.
2. **Install the GPT profile?** Default: no. The profile ships in the zip under the deprecation note, but your own
   GPT install is left as it is, since you no longer use Copilot. Your coding-root install ledger still carries a
   `gpt` entry (147 files under `.github/skills`); it will show as an older release and is outside the Step 11 check.
   Changes if you want it refreshed or uninstalled.
3. **Resolved by evidence 2026-11-12 (reviewer check): which zip is the ordering reference?** The zip is not held locally (the v2.0.4 build folder holds only the recipe and notes), but the GitHub release `v2.0.4` carries `skill-mesh-v2.0.4.zip` (7,777,781 bytes, SHA-256 `d06fde86...877d`, equal to the value recorded in `plan.md`) and `skill-mesh-v2.0.4.sha256`. Download both into one new empty folder. Remaining choice: only if you hold a local copy. Default: the v2.0.4 release zip from its GitHub release page, downloaded
   into its own empty folder and checked against the `d06fde86...` SHA-256 recorded in `plan.md` before use. The
   recipe needs a reference to prove its entry order reproduces earlier releases. Changes if you hold a local copy.
4. **The foreign Codex `user-fermize` file.** Default: back up and remove that one file by hand, naming that path only, then install normally
   without `-Force` (Step 10), so Codex gets the released skill. Changes if you want to keep your hand-written copy: then the
   Codex install is skipped and Step 11 covers Claude only.
5. **The empty `user-build-route/` folder in the Codex home.** Default: leave it. The installer writes into it; an
   empty directory is not a foreign file and causes no refusal. Changes if you want it removed first.
6. **A release stamp in the install ledger** (`README.md` priority 2: a build identity in the ledger plus one advisory
   line per drifted skill). Default: not in v3.0.0. It needs a decision on ledger versioning and changes
   `tools/`, which would send this release through the full gate again. The rebuild-and-compare check stands in for
   it. Changes if you want it first; it then becomes a row 8 prerequisite and the plan returns for a new step.
7. **Fast-forward `origin/main` or leave `main` behind the release branch?** Default: fast-forward, as for v2.0.1
   to v2.0.4. Changes if you want the release branch and tag only, with the merge to main after a soak.
8. **Decided 2026-11-12 (by split proposal row 8, "Release v3.0.0").** **Version label.** Default: `3.0.0` and tag `v3.0.0`. Changes if you would rather call the first release with
   retired skills `2.1.0`. (The split proposal and the README already say "v3".)
9. **Who runs Step 9 and Step 10 commands.** Default: the coordinator runs them after your written yes, and records
   output. Changes if you want to run the push, tag, release and install commands yourself from the prepared blocks.
10. **Decided 2026-11-12 (by split proposal row 8, "Waits on 1 to 7"), for the start condition.** **Timing.** Default: nothing in this plan starts until rows 1 to 7 are recorded as landed (Step 1), and the
    full gate runs on a quiet machine, not alongside another heavy run. Changes if you want a different order, for
    example publishing before install and a soak day before Step 10.
