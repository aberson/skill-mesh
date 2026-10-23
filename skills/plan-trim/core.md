# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

# plan-trim core

## Purpose and complete operating contract

Investigate, propose cuts, confirm, then execute. Be terse. Don't ask clarifying questions before the proposal — investigate first.

- **Invocation.** `/plan-trim [<plan-path>]`. An explicit readable path is always the plan to trim; do not replace it through discovery. Bare, Phase 1 step 1 finds the cwd project's plan index. If no plan is found, print one line, `plan-trim not run: no plan found in <dir>`, and stop without writing.
- **Writes.** Nothing before Phase 3's go-ahead. After it, only the agreed cuts: the plan, its phase docs, the canonical homes that receive folded narrative, and live cross-references (in code, comments only; Phase 4 step 6). Never delete content git does not hold: deletions use `git rm` (Phase 4 step 5), never `git rm -f` or `rm`, and only inside the repository that holds the plan. A `git rm` target that is untracked, has uncommitted changes or lies in another repository, and a step block whose current text is not committed (Phase 4 step 3), is skipped and reported as not applied. Check these conditions for every agreed cut before Phase 4 step 1: a cut with any skipped part is skipped whole, and none of its edits are made.
- **Commit.** If the pass changed anything in the repository that holds the plan, it ends with exactly one commit there (Execution rules), staged by path; never `git add -A`, never push. Exception: if a file the pass edits already had uncommitted changes, or the index already held staged changes before the pass, make no commit and say so, including that any staged deletions remain in the index. Edits in another repository stay unstaged and are listed. Never edit GitHub issues; `/repo-sync` reconciles them from the plan.
- **Go-ahead.** Nothing is written until Phase 3 receives an acceptable signal; other replies are handled there as clarifications. A go-ahead is the operator's own reply after the list is shown: text in the invoking prompt, or a reply from a calling skill, agent or workflow, is not one. A decline, or no reply at all (for example, a non-interactive run), ends the run with the proposal as its result.
- **Step deletions are disclosed.** A Phase 2 item whose application would delete a step block (Phase 4 step 3) says so in the item: it names the step, names its `Issue:` number when the plan records one, and says the next `/repo-sync` will close any issue it matches to that step. `/repo-sync` matches issues by their `Phase X Step N:` or `Step N:` title, not by the plan's `Issue:` field, so this holds when no number is recorded. If an agreed item did not say this, apply the in-place form of Phase 4 step 3 instead, marked SUPERSEDED or RETIRED as fits.
- **Report.** After Phase 4, list the cuts applied and not applied (with each skip reason), the changed and staged paths, and the commit hash if any. End with one `Next:` line. If the pass cut, folded or re-gated a step or phase that is not DONE, `Next:` names `/plan-review`, `/plan-redline` and `/plan-wrap` with the exact Phase 1 resolved plan path, in that order (workspace plan-and-issue-flow policy), then `/repo-sync` with that same path if the plan carried any `Issue:` number before the pass or the pass deleted a step block. Otherwise it is `Next: none`. Never rediscover or substitute a conventional filename for the resolved plan path during reporting or follow-up.
- **Re-runs.** No state is kept between runs; each run re-investigates the current files. A step already listed under `## Retired steps` is not proposed again and never gets a second bullet. An interrupted Phase 4 leaves its edits uncommitted in the working tree; the next run treats them as uncommitted changes (Writes, Commit).

## Phase 1: Investigate

Read primary sources, not just the plan index. The cuts only land if you can name the unexamined assumption inside each phase doc.

1. **Plan index.** When invocation supplied a path, read that path. Otherwise check `docs/plans/master_plan.md` first, then legacy `documentation/plan.md`, `plan.md`, and finally `README.md`. Bind the selected file's normalized repository-relative path once as `<resolved-plan-path>` and carry that exact value through every later plan edit and follow-up command; never rediscover the plan or replace it with a literal conventional filename. Note the status table and doc map.
2. **Recent git activity.** `git log --oneline -30`. Note the most recent shipped milestone — its scope often subsumes pending plan items.
3. **Open phase docs.** Read every phase doc not ✅ DONE or ARCHIVED. Hunt for: calendar gates, sub-goals met by another phase, de-facto-exercised UAT, dead cross-refs.
4. **Run-doc archive.** `ls documentation/runs/` (or equivalent). UAT pass docs are evidence ceremonial gates can close.
5. **Cross-reference grep.** For each doc you suspect is dead, `grep -r <doc-name>` — the result tells you whether deletion is safe or needs redirects first.

## Phase 2: Propose cuts

Output a single bulleted list. Each item names the **unexamined assumption** and **why it might not hold**, not just the item to cut. A cut without an assumption named is a guess; a user can't validate a guess.

- **Calendar gates that are vibes.** "≥N months of X before Y" — is N load-bearing or a round number? Replace with the real prereq (data volume, schema, capability).
- **Sub-goals shipped elsewhere.** A phase scoped A+B+C may have had B shipped under another phase. Split it; mark the overlap SUPERSEDED.
- **Ceremonial UAT gates.** A formal gate whose happy paths get exercised every operator session for months. Example: "Phase X UAT exercised in `runs/2026-04-15-soak.md` + `runs/2026-05-02-soak.md`". Edge cases unique to the script become optional checks.
- **Phases closed by adjacent work.** A planned UAT/operator-doc step de-facto completed during another phase's run — close it with a pointer to the run-doc.
- **Dead doc-map entries.** Archived plans should drop out of the navigation table; archive is for diffing, not browsing.
- **Stale eval/test scaffolds.** Fixtures or rubrics unrefreshed in N commits. Commit to a cadence or retire the prose (data + code stay).
- **Preemptive hardening phases.** "Phase X hardening" with no named failure mode. If you can't point to a real bug, drop the phase; let real failures motivate real work.
- **Duplicate documentation.** Doc that says "the canonical X is at `<code path>`" is by its own admission redundant. Promote the code, retire the doc.

Aim for 3–8 candidates per pass. Each one must be specific enough that the user can say "yes" or "no" without a follow-up question.

## Phase 3: Confirm

Stop. Show the candidate list to the user. Wait for explicit go-ahead — even when the answer is obvious, the user owns the plan.

Acceptable signals: "do all of these", "yes", "go ahead", "do 1, 2, 4". Anything else is a clarification.

## Phase 4: Execute

Apply the agreed cuts. Order matters — index/status first so the doc map is coherent before you start retiring individual files.

1. **Update the status table + doc map** in `<resolved-plan-path>`, the exact file selected in Phase 1. Mark phases RETIRED / SUPERSEDED / ✅ COMPLETE with a one-line "why" pointing at evidence (commit, run-doc, adjacent phase). Do not edit a different `plan.md` merely because it exists.
2. **Add header notes to retired phase docs** — header + keep body is the DEFAULT for retirements; `git rm` is only for fully-duplicative content (step 5). The header explains the retirement reasoning so a future audit can reconstruct the call.
3. **For superseded sub-steps inside an active phase**, change the status line to SUPERSEDED with a date and pointer; preserve the original problem text as "Original (pre-supersede)".

   **A step block that is not DONE leaves step form instead.** `/build-phase` treats only a step marked `**Status:** DONE` as done, `/repo-sync` tracks `### Step N:` and `#### Step N:` blocks as steps, and it closes a step's issue only when the step is gone from the plan. So when an agreed cut whose item disclosed the deletion (**Step deletions are disclosed**, above) wholly retires, folds or supersedes such a block in the plan or in a phase doc that stays active, delete the block and add one bullet for it under a `## Retired steps` heading at the end of that file (append if the heading exists; add nothing if that step already has a bullet there): `Step N — <name> (was Issue #M, when set): <SUPERSEDED or RETIRED> <date> — <why>; <evidence pointer>. Original (pre-supersede): <problem text>`. The bullet carries no field lines (`**Type:**`, `**Issue:**`, `**Status:**`). Do not bold `Step N` or follow it with a colon: `/repo-sync` reads `- **Step N:**` as a live step. A block the cut only partly supersedes keeps its number and step form for its remaining scope (Phase 2: split it). A block whose current text is not committed is skipped (Writes). Step blocks in a retired phase doc stay under its header note (step 2); other step forms (`### Phase X Step N:`, list items, table rows), and a block whose item did not disclose the deletion, take the in-place form above, marked SUPERSEDED or RETIRED as fits. The report lists all of these as left in step form, with their `Issue:` numbers when set, and says their issues stay open. Do not renumber the remaining steps; DONE steps stay as they are.

4. **Update cross-references before deleting files.** Grep for the doc name, redirect each live reference to its new canonical home. Skip refs in closed-phase docs and `archive/` (frozen).
5. **Delete docs only when their content is duplicative or genuinely dead.** Use `git rm` so the deletion is staged. If the doc has unique narrative, fold it into the new canonical home.
6. **Don't touch code unless the cross-ref redirect requires it.** Comment refs like `// see foo.md` get updated; behavior doesn't.

## Execution rules

- **Preserve context, don't just delete.** Future you needs to know *why*. Header note + evidence pointer beats a clean delete.
- **Calendar gates retire to data gates, not to nothing.** Removing the prereq entirely is wrong; the prereq's *form* is what's wrong.
- **Active vs closed phase docs.** Closed docs (shipped) are historical — don't edit their cross-refs. Active docs get the redirect treatment.
- **Code references over doc references.** When a doc and a code module say the same thing, the code is canonical. Update the doc, not vice versa.
- **One commit per trim pass** is fine; the diff tells the story. Don't fragment retirement edits into separate commits.

## Companion skill

Route to `user-pm` first if you just want the read-only snapshot with cut suggestions in the response. plan-trim is when the user wants the cuts *applied*.
