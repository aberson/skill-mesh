# Guard against over-building and over-testing (v3 row 4): plan

This is the execution copy for build-phase, copied 2026-11-12 from the operator's planning records in the coding root (`<coding-root>/docs/skill-mesh-3-review/`), where its reviews and the operator's answers live. Step status is recorded here from now on.

Date: 2026-11-12. Status: PLAN ONLY, nothing built. Lane P-og of the v3 day window.
Authority: v3/v4 split row 4; morning item 65 ("it's big issue, especially for Astra"). Astra is the operator's name for the `gpt-6-astra` Codex coordinator model. "The 10/29 session" is a Codex session on 2026-10-29 whose request was: add a worktree-cleanup step to `repo-wrap` and/or `user-wrap`, ship it to production, bump the version; it turned into a 48-minute release with a repo-root suite started on a patch release. Diagnosis: `<coding-root>/docs/skill-mesh-3-review/builds/og-report.md` (5 root causes, 6 candidate steps).
Place in the release: row 4 comes after the catalog gate (row 3), because the gate's class table is part of the fix. This plan does not edit the catalog gate plan. It either depends on it or names where it covers a candidate.

Roots: skill-mesh paths are repo-relative. Every other path is `<coding-root>/...`. Builds run from the integration checkout `<coding-root>/skill-mesh-wt/v3-main` (branch `v3/main`). Evidence for this plan lives in `<evidence>` = `<coding-root>/docs/skill-mesh-3-review/builds/guard`, outside the repo.

## What the diagnosis found, in short

An agent that is asked to make a small skill change reads one test rule, "the full suite is the DONE gate", and runs it. It does not say that the suite takes 3 to 4.5 hours, and it does not ask. The rules that would have stopped it (ask before a full suite; wait quietly on long jobs) exist only where Claude loads them. Codex does not. So the cause is mostly what Codex is told, not how it treats an explicit instruction (on 10/29 it obeyed "don't over test" within 4 seconds).

## How a Codex session sees each change (verified in the v3-main checkout, read-only)

- **Inside skill-mesh:** `AGENTS.md` is an eight-line adapter (`tests/package-integrity/test_recovery_plan_hygiene.py` fails it above eight lines). Its first instruction, on line 3, says "Load and follow `CLAUDE.md` in full". So Codex gets `CLAUDE.md` plus anything written in `AGENTS.md` itself. Nothing else is loaded automatically.
- **At the coding root:** `<coding-root>/AGENTS.md` says "Load and follow `.claude/workspace-instructions.md` in full", and carries a few rules of its own (its own header calls it a Copilot adapter; Codex reads the same file). The rules under `<coding-root>/.claude/rules/` are not loaded by Codex; only `workspace-instructions.md` is, and only because `AGENTS.md` points at it.
- **Global file:** `~/.codex/AGENTS.md` does not exist on this machine. Nothing is inherited from there.
- **Codex skill adapters (`skills/*/providers/codex.md`):** these load only when a skill is invoked. The diagnosed sessions were ordinary edit-and-release requests, not skill runs, so no adapter text could have reached them. No adapter is changed in this plan.
- **Pinning:** `AGENTS.md` and `CLAUDE.md` are read by `tests/package-integrity/test_instruction_contract_single_owner.py`, `test_host_discovery.py` and `test_cutover_handoff.py` (for sweeps, pointer shape and the "adapter, not registry" role), so any edit to them runs those files. They do not pin the new wording. A fourth file, `test_recovery_plan_hygiene.py`, does pin two things that bear on this plan: `AGENTS.md` may be at most 8 lines (it is 8 now), and neither `AGENTS.md` nor `CLAUDE.md` may contain an absolute user-home path. The 8-line cap is what decides where Step 3's text can live (Step 3, Open item 6).

| Step | Changes what Codex/Astra reads? | How a Codex session sees it |
|---|---|---|
| 1 | Yes (shared) | New sentences in `CLAUDE.md`, loaded through `AGENTS.md` line 2 |
| 2 | Yes (shared) | One sentence in `CLAUDE.md`; the lifecycle guide is read only when a catalog edit follows its pointer |
| 3 | Yes (Codex only) | A paragraph in `AGENTS.md` itself, in every session started inside skill-mesh (needs the 8-line cap raised, Open item 6) |
| 4 | No code; checks 1 and 3 | A fresh Codex session reads the merged files |
| C1, C2 | Yes (coding root) | Through `<coding-root>/AGENTS.md` and the file it loads |

## Covered by the catalog gate (no step here)

- **Candidate 1, end state:** the scoped gate rule in `CLAUDE.md`, the lifecycle guide and the workspace rule is written by catalog gate Steps 9 and 11. Step 1 below is only the interim version. Catalog gate decision 7 (operator answer item 20) ends the interim ask-first rule at Step 11, not earlier. Catalog Step 9 rewrites the "Default DONE gate" text in `CLAUDE.md`; nothing in the catalog plan removes Step 1's paragraph, so the findings note (Open item 1) names who does.
- **Candidate 5, selector and moved roster check:** covered by catalog gate Steps 3 and 4, once its owners take the two findings in Open item 1.
- **Owner-table gap** (`<coding-root>/.claude/workspace-instructions.md` line 24, the Testing bullet, is the "Testing bullet (stub)" that catalog gate Step 9 could not find): routed with the two gaps, Open item 1.

## Phase: the guard (skill-mesh)

Order: 1, 2, 3 land on one branch off `v3/main` (they edit different files and may merge in any order); 4 follows the merge. Catalog gate Phase 2 may land before or after. If it lands first, Step 1 is marked "covered by catalog gate Step 9" and skipped; Steps 2 and 3 stay (they cover other causes).
Gate: these steps edit only `CLAUDE.md`, `AGENTS.md` and `documentation/`. Each step's Done-when names its focused tests. The phase's merge gate is the repo-root full suite, run once at phase end (not per step), priced beforehand as 3 to 4.5 hours per `documentation/phase-75-baseline.md`, unless the catalog gate has been adopted by then and the selector returns `catalog` for the change set. No required release or safety gate is weakened by any step.

### Step 1: State where the full suite applies, and ask before using it elsewhere (interim)

- **Problem:** The only test rule Codex reads calls the multi-hour repo-root suite "the DONE gate", with no scope and no ask-first. Astra ran about 7.5 hours of it to add one skill (11/03). The 10/29 session started it on a patch release, four minutes before the operator said stop.
- **Type:** code
- **Issue:** #
- **Flags:** `--reviewers code`.
- **Files:** `CLAUDE.md`.
- **Produces:** in `CLAUDE.md`, directly after the `python -m pytest` block, a short paragraph that says four things. The full suite is the gate for a plan step or phase. A change made outside a plan step, including a release, uses focused tests while editing and, at release, the staged checks inside `tools/release.ps1`. The full suite stays the default for a merge to the main project: before starting it for such a change, say how long it takes (the figure is owned by `documentation/phase-75-baseline.md`), offer the scoped set, and ask; the operator's answer decides, and the agent never narrows the gate on its own. If the operator limits testing, drop optional checks but never the release script's staged checks or the installer's safety checks, and record which suites ran. No number is restated in `CLAUDE.md`. The paragraph is marked as interim, to be retired with the catalog gate's rule (decision 7, Step 11).
- **Done when:**
  - The paragraph is present, `CLAUDE.md` restates no wall-clock figure (grep for `hour` in the added text is empty), and the existing "Default DONE gate" sentence and Phase CD exception paragraph are unchanged (diff shows only added lines).
  - These pass, with the suites that ran named: `test_instruction_contract_single_owner.py`, `test_manifest_contract.py`, `test_skill_catalog_lifecycle.py` and `test_recovery_plan_hygiene.py` under `tests/package-integrity/` (the last bars absolute user paths in `CLAUDE.md`).
  - No test is added: new wording tests are the pattern this plan is trying to stop. Red-on-garbage does not apply.

### Step 2: Name the release script's staged check as the release's package gate; fix the regenerate wording

- **Problem:** `tools/release.ps1` already runs `tests/package-integrity` on the staged tree, but nothing says so where agents look, so they run it first (697 tests, then 692, 7 to 9 minutes). The lifecycle guide says to "regenerate the derived in-repo artifacts", while `CLAUDE.md` says to re-run `tools/gen_manifest.py` only when its constants change. That caused an unneeded manifest run and a line-ending clean-up. Separately, the 10/29 first draft restated a shared contract in 40 lines and pinned it with a new wording-test file, then was rewritten 17 minutes later.
- **Type:** code
- **Issue:** #
- **Files:** `CLAUDE.md`, `documentation/skill-catalog-lifecycle.md`.
- **Flags:** `--reviewers code`. Depends on nothing. If catalog gate Step 9 has already merged, apply the first sentence by adding it to that step's rule text instead of adding a second paragraph; do not duplicate.
- **Produces:** three small edits, each one sentence or clause:
  1. `CLAUDE.md`, Release block: the staged run of `tests/package-integrity` inside `tools/release.ps1` is the release's package gate, so do not run that suite separately before it.
  2. `documentation/skill-catalog-lifecycle.md`, the regenerate line: "derived in-repo artifacts whose inputs changed (`tools/gen_manifest.py` only when its constants change)".
  3. `documentation/skill-catalog-lifecycle.md`, one paragraph placed after the operation table and outside the pinned UPDATE row: a prose-only update cites the shared contract it relies on instead of restating it, and adds no new test file; extend an existing contract test only when the update adds a rule that a later edit could silently drop.
- **Done when:**
  - The three edits are present. `test_skill_catalog_lifecycle.py` passes, and any contract sentence it pins that these edits move is updated in the same change (the diff shows which).
  - `test_instruction_contract_single_owner.py`, `test_manifest_contract.py` and `test_recovery_plan_hygiene.py` pass; the suites that ran are named.
  - `grep` shows the staged-check sentence exists once in `CLAUDE.md`.
  - No test is added.

### Step 3: A wait-and-report rule and the skill-creator boundary, for Codex only

- **Problem:** Codex waits by short polls and narrates each one, gives no estimate, and calls unfinished steps "final". Astra produced about 209 "still active" messages in one release; the 10/29 session sent 17 updates for 3 real changes while a 19-minute install ran. The host's built-in skill-creator is also loaded and run in a repo whose `CLAUDE.md` says it is not this repo's authority (duplicate validation, a false failure). Claude has the waiting rule in `.claude/rules/subagent-economy.md`; Codex never loads that file.
- **Type:** code
- **Issue:** #
- **Flags:** `--reviewers code`.
- **Files:** `AGENTS.md`, `tests/package-integrity/test_recovery_plan_hygiene.py` (the line cap only).
- **Produces:** two additions to `AGENTS.md` (the Codex-only file; `CLAUDE.md` is unchanged, so Claude's context does not grow), and one constant change: `test_root_adapters_are_thin_and_point_to_stable_authority` caps `AGENTS.md` at 8 lines and the file is already 8, so the cap is raised to the smallest value that fits the additions (still a cap, so a fat adapter still fails). Add no absolute user path to `AGENTS.md`:
  - A waiting paragraph of about four sentences. Before a command likely to run over two minutes, say once what it is and how long it usually takes, or that you do not know. While it runs, wait as long as the host allows between checks, and write only when something changes: a stage ends, a failure appears, or it runs past twice the estimate. Call a step final only if nothing follows it. Never stop a running install or release to save time.
  - One line: skill edits here follow `documentation/skill-catalog-lifecycle.md`; do not load or run the host's built-in skill-creator. (`CLAUDE.md` already says a host skill-creator is not this repository's authority; the line is the stronger, Codex-facing form of it, not a second owner.)
  - The existing "adapter does not enumerate skills, select models, or duplicate volatile project state" sentence stays true: the additions are behavior rules, not skills, models or state.
- **Done when:**
  - Both additions are in `AGENTS.md` and the rest of the file is unchanged (diff shows only added lines); `AGENTS.md` still names `CLAUDE.md` as the shared source on line 3.
  - `test_recovery_plan_hygiene.py`, `test_host_discovery.py`, `test_instruction_contract_single_owner.py` and `test_cutover_handoff.py` pass; the suites that ran are named.
  - Red-on-garbage for the raised cap: in a scratch copy, append lines until `AGENTS.md` is one line over the new cap and confirm `test_root_adapters_are_thin_and_point_to_stable_authority` fails; then confirm it passes on the real file. Record both results.
  - No test is added and no installer behavior changes.

### Step 4: Operator replay with a fresh Codex session (operator step)

- **Problem:** The change is to what Codex is told, so the only honest evidence is what a fresh Codex session does with it. This is observation, so it runs after the merge and produces no code.
- **Type:** operator
- **Issue:** #
- **Flags:** none.
- **Files:** `<evidence>/replay.md` (outside the repo).
- **Produces:** `<evidence>/replay.md`, holding for one fresh `gpt-6-astra` session started inside the merged `v3/main` checkout, given the 10/29 request (as worded above) in plan-only mode ("list the checks you would run and the messages you would send; run nothing"):
  - the answer, side by side with the same request run once before the merge (from a checkout of the parent of the merge, so the baseline is real);
  - the first lines of the session's recorded instructions, showing whether the `AGENTS.md` paragraph was loaded.
- **Done when:**
  - The "after" answer states how long the full suite takes and asks before using it, plans one estimate up front, plans updates only on change, and does not mention the host skill-creator.
  - The "before" answer is recorded, even if it already behaves well. This is the known-bad anchor: if "before" and "after" are indistinguishable, the replay shows nothing about the change, and that is recorded rather than read as a pass.
  - A plan-only answer shows what the session intends, not what it does; the first-lines-of-instructions check is the load-bearing evidence and the answer comparison is supporting.
  - If the "after" answer misses any of the four, the miss is recorded and fed back as a redline of Step 1 or 3, not patched here.

## Coding-root changes (separate landing)

These edit workspace files outside skill-mesh. They are not build-phase steps for skill-mesh; the operator or a coding-root session applies them, each as its own small diff. C1 can land before the skill-mesh phase. C2 copies Step 3's wording, so it lands after Step 3 merges.

### C1: Add the scope word to the workspace Testing bullet

- **Problem:** `<coding-root>/.claude/workspace-instructions.md`, the Testing bullet, says "Gates that flip a step or phase DONE run the FULL suite". That is the one test rule Codex reads at the coding root, and it has no scope or release case. It is also the "Testing bullet (stub)" the workspace `code-quality.md` names.
- **Produces:** two changes in that bullet: "a step or phase" becomes "a plan step or phase", and one added sentence: a release or an unplanned change uses its project's stated release gate. No other bullet changes.
- **Done when:** a grep of that file finds both phrases once each; the "if too slow, the checkpoint names which suites ran" clause is unchanged (the existing rule is not weakened); `<coding-root>/.claude/rules/code-quality.md` is untouched. This text is retired by the diff catalog gate Step 11 hands over (same wording owner); the Step 11 author is told this bullet is one of the owners (Open item 1).

### C2: Give Codex sessions at the coding root the waiting rule

- **Problem:** A Codex session started at the coding root loads only `<coding-root>/AGENTS.md` and the workspace instructions it points to. Neither has a waiting rule, and the equivalent Claude rule (`.claude/rules/subagent-economy.md`) is not loaded.
- **Produces:** the same four-sentence waiting paragraph as Step 3, in `<coding-root>/AGENTS.md`. The wording is copied from Step 3 once it merges, so there is one wording.
- **Done when:** the paragraph is in the file; a fresh Codex session opened at the coding root shows it in its recorded instructions (recorded in `<evidence>/replay.md`, a second short section); `<coding-root>/.claude/workspace-instructions.md` is not edited by this item.

## Open for redline

Every item has a default; if the operator does not answer, the default applies.

1. **The two catalog-gate gaps, and where they go.** The gaps are: (a) its selector returns "full" for the diagnosed 10/29 change set (version links in `_shared/*.md`, the root `plan.md`, the root `CLAUDE.md` and `AGENTS.md`, and a new test file all fall through), and (b) the count check that failed Astra's first v2.0.3 run (`tests/distributions/test_distributions.py`, the declared-roster test) is in no catalog class. Also the owner-table gap for the workspace Testing bullet, and a fourth line: nothing in the catalog plan removes Step 1's interim `CLAUDE.md` paragraph when its rule lands (Step 9 rewrites the "Default DONE gate" text; Step 11 ends the ask-first wording only in the workspace diff). Part of gap (a) is already settled: a new test file is `full` by design (**Decided 2026-11-12 (by README "Morning sheet answers, 2026-11-12", sheet item 19 taken at its default)**), so the note asks only about the version-link, root `plan.md`, `CLAUDE.md` and `AGENTS.md` paths. **Default:** they are not folded into this plan and the catalog gate plan is not edited. A short findings note, `<coding-root>/docs/skill-mesh-3-review/builds/catalog-gate/findings-from-guard.md`, carries all three, with the evidence lines from `og-report.md` sections 7 and "Step 5". The catalog gate's Step 1 measurement reads it: its per-file TSV then says whether any non-catalog file reads `_shared/*.md`, and whether the roster check has a PowerShell marker. Its owner decides from those numbers whether Steps 2, 3, 4 and 9 change, by redline. This plan's steps do not wait for it.
2. **Apply C1 now, or wait for catalog gate Step 11.** **Default:** apply now as an interim; Step 11 replaces the bullet and this wording carries over.
3. **A global `~/.codex/AGENTS.md`.** **Default:** do not create one. Step 3 and C2 cover the two places Astra sessions start, and a new global file is a new owner for a rule that already has two.
4. **Installer start lines (candidate 6).** Printing one line when each provider starts would make the 19-minute install less silent. **Default:** not built. It touches `tools/install-skill-mesh.ps1`, so it would cost a full-suite gate of its own; Step 3's up-front estimate does most of the work. Reopen only if Step 4's replay shows Codex still polling during installs.
5. **Review findings implemented without asking whether the plan required them** (seen in two Astra sessions). **Default:** out of scope for this plan; it belongs in the review-skills work, not in a test-gate or instruction change.
6. **Where the waiting paragraph lives for skill-mesh sessions.** `AGENTS.md` is capped at 8 lines by `test_recovery_plan_hygiene.py` and is already 8, so the paragraph cannot go there without changing that test. **Default:** `AGENTS.md` only, raising the cap in that test to the smallest value that fits (Step 3), so Claude's context does not grow. Alternative: put the paragraph in `CLAUDE.md` (no test edit, but Claude sessions then carry a second copy of a rule the workspace already owns for them) and C2 shrinks to a pointer.
7. **Pin the new wording with a test.** **Default:** no. The diagnosis found the habit of pinning prose is itself a cause; the Done-when checks are greps and the existing suites.
8. **How strong the Step 4 evidence must be.** **Default:** one before-and-after replay, recorded. Repeated sampling of model behavior is not required for a wording change; a miss is a redline, not a gate.
9. **When the full suite runs for Steps 1 to 3.** The catalog-gate leg is **Decided 2026-11-12 (by README "Morning sheet answers, 2026-11-12", sheet item 14 taken at its default: adopt once catalog Steps 4 and 5 pass)**; what stays open is the interim, before it is adopted. **Default:** once at phase end, priced and confirmed first; or, if the catalog gate is adopted and returns `catalog` for this change set, the catalog gate instead. The operator can lower this with a recorded scope decision; this plan does not.
