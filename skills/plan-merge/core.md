# NOTE: This is the canonical provider-independent contract. Both provider wrappers must load it in full.

# plan-merge core

## Purpose and complete operating contract

Merge two (or more) plan documents into one. The output is a single plan
where overlapping goals are resolved, phases are re-sequenced into a
coherent order, and the originals are archived — not deleted — so their
context remains inspectable.

This skill is **conversational**. It does not auto-merge. It surfaces the
decisions a human has to make (which plan is the spine, how to resolve
overlaps, how to order dependencies) and then writes the merged plan only
after those decisions are settled.

### Operating contract

- **Two modes.** Invoked with plan paths, this skill merges: everything in
  this core except **Trim mode (`--trim`)** describes the merge. Invoked as
  `/plan-merge --trim [<plan-path>]`, it trims one plan instead, under the
  complete contract in that section; none of the merge rules apply to a
  trim, and none of the trim rules apply to a merge.
- **Position.** An operator-interactive authoring skill, not one of the
  autonomous build-pipeline skills. It asks the operator only two things:
  the Step 5 questions, which are the consequential plan-content decisions
  the merge exists to force, and Step 8's approval before editing non-plan
  files. Neither is a `(y/n)` "Proceed?" confirmation; a safety stop
  reports and ends the turn. The merged plan is a newly authored plan, so
  `/plan-review` → `/plan-redline` → `/plan-wrap` run on it before
  `/repo-init` or `/repo-sync` (see Output format).
- **Turns.** The first turn runs Steps 1–5 and writes nothing, so
  repeating it is safe. After the operator answers, Steps 6–8 run and the
  summary closes the run. Non-plan files change only in a later turn,
  after the operator approves the listed edits (Step 8). If Step 6 or 7
  stops partway, the summary names what was written and moved; after it,
  outside its word count and before the source-issue block and the
  closer (Output format), print the exact remaining move commands in the
  host shell's non-clobbering form, `<dir>` being the file's directory
  (Step 7): `git -C <dir> mv <src> <dst>` without `-f` for a tracked
  file, in either shell; for an untracked file, `mv -n <src> <dst>` in a
  POSIX shell, or `Move-Item -LiteralPath <src> -Destination <dst>`
  without `-Force` in Windows PowerShell, whose `Move-Item` has no `-n`.
  A re-run never repeats a completed move: check only an input's newest
  Plan history merge entry, and only its originals whose former path is
  not that input's own path. When such an original is still at its
  former path and absent from its archive path, that input is an earlier
  merge that stopped partway, so print
  `plan-merge stopped: earlier merge incomplete` and its remaining move
  commands in that form, never one whose source is that input, and write
  nothing.
- **Allowed writes.** The merged plan at the confirmed target; moving
  each input into the archive (Step 7; `git mv` only stages the rename);
  and, after the operator approves them, the reference edits Step 8
  lists. Never: delete an input; overwrite an input before it is
  archived, an existing archive file, or any other existing file at the
  target; move an input above its project root or out of its repository
  (Step 7); run `gh` or change issues; commit or push; write the
  `### Decision Inventory` or the `Proposal:` locator, which
  `/plan-redline` owns.
- **Not run.** Invoked bare, or with fewer than two readable plan paths:
  do not guess. Print one line `plan-merge not run: <reason>`, list up to
  ten plan files found read-only, checking the current project's canonical
  `docs/plans/master_plan.md` first, then the legacy root, `plans/`, `docs/`,
  `documentation/` and `documentation/plans/` locations, and stop without writing.
- **No self-certification.** The summary never calls the merged plan
  reviewed, wrapped or ready to build.
- **Three or more inputs.** Read every "both" and "two" below as "every
  input"; Step 2's template repeats once per plan.

## When to use

- Two plans in `documentation/plans/` target related work and the team
  hasn't decided which one to execute.
- One plan describes a *capability* (e.g. "add feature X") and another
  describes the *infrastructure* that feature needs. They overlap at the
  seam and need reconciliation.
- A plan's phases reference work that is separately planned elsewhere.
- An old plan is partially superseded by a newer one and they need to
  be unified rather than left to rot in parallel.

Do NOT use this skill:

- To merge a plan with its own code — that's `/repo-update` or direct editing.
- To refine a single plan — that's `/plan-review`.
- To split a plan into smaller phases — write a new plan.

## Inputs

- Paths to two or more plan files (bare or short: see Not run above).
- Or `--trim [<plan-path>]`, which selects trim mode: at most one plan path,
  never a merge (see **Trim mode (`--trim`)**).
- Optionally, the target path for the merged plan. Default, confirmed in
  Step 5 question 6: when an input is the project's canonical entry plan
  (`docs/plans/master_plan.md` first; legacy fallback is `plan.md`, then
  `master_plan.md`, searched in the project root defined in Step 7, then
  its `plans/`, `docs/`, `documentation/` and `documentation/plans/`), that
  same path, so the project keeps one discoverable entry plan; otherwise
  `<descriptive-name>-master-plan.md` in the spine plan's directory (for
  example `documentation/plans/<descriptive-name>-master-plan.md`).

## Process

### 1. Read both plans in full

Do not skim. The overlap that matters is rarely in the introduction — it
hides in phase-level details, schemas, contracts, and kill criteria.

### 2. Surface the overlap

For each plan, extract **all five** of the following fields. The output
MUST include every field for every plan — if a field is empty in the
source, write `(none found)` explicitly rather than omitting the line.
Dropping any of the five fields makes Step 2 invalid and Step 4's spine
proposal unsound.

- **Vision / goal** — what problem does it solve?
- **Phase list with one-line summaries**
- **Data contracts** (DB schemas, file formats, APIs)
- **External dependencies** (branches, PRs, other plans, skills)
- **Kill criteria and rollbacks**

Render the extraction using this exact template, once per plan (do NOT
collapse fields, do NOT drop the External dependencies or Kill criteria
lines even if they feel redundant):

```text
#### Plan: <name>
- Vision / goal: <...>
- Phase list: <...>
- Data contracts: <...>
- External dependencies: <...>
- Kill criteria and rollbacks: <...>
```

Then compare: where do the two plans touch the same concept?

Each overlap MUST be classified by exactly one of these four catalog
patterns, prefixed verbatim as `[PATTERN: <name>]` in lowercase:

- `[PATTERN: same-goal-different-fidelity]` — Plan A describes a
  feature abstractly; Plan B describes the infrastructure that
  implements it concretely. (Most common case.)
- `[PATTERN: same-data-different-schema]` — Both plans add storage for
  related information in different formats (SQLite vs JSONL vs JSON).
- `[PATTERN: implicit-prerequisites]` — Plan A's Phase N requires
  infrastructure that Plan B's Phase M builds.
- `[PATTERN: conflicting-invariants]` — Plan A declares "append-only
  X"; Plan B implicitly violates that invariant.

Do not invent new pattern names — if a detected overlap doesn't fit any
of the four, pick the closest match and note the imperfect fit in
parentheses after the bullet. Ad-hoc phrasing without a `[PATTERN: ...]`
tag is a defect.

### 3. Check for self-inconsistency

A plan is self-inconsistent if its own later phases would break its
earlier phases. This is easy to miss when reading linearly. Look for
this pattern: **does plan A's later phase invalidate an assumption its
own earlier phase makes?** When you find one, name BOTH the offending
later phase AND the earlier phase it breaks.

### 4. Propose a spine

One plan usually reads as the *substrate* (infrastructure, foundational)
and the other as the *capability* (features built on top). The substrate
is the spine; the capability plan's phases slot in as work that happens
inside the substrate.

State the proposed spine explicitly, with justification. Be direct: "I
propose Plan B as the spine because it's the substrate; Plan A's phases
become per-substrate work."

Alternatives worth calling out:

- Capability-as-spine (when the infrastructure is lightweight and
  exists mainly to support one capability).
- Neither-as-spine (when both plans are equal partners — then the merged
  plan has two tracks that run in parallel and synchronize at named
  points).

### 5. Ask the hard questions before writing

Do NOT write the merged plan body yet — phase contents, decision graph,
baseline, kill criteria, etc. stay unwritten until the user has answered
the questions below.

BEFORE listing the questions, the first-turn response MUST preview the
structure of the eventual merged plan so the user can see what they're
signing up for. Render this preview inline in the response, verbatim, in
this order:

> Once you've answered the questions below, I will write the merged
> plan to the target path with these fifteen canonical sections in this
> order:
>
> 1. **Source** — names the two archived originals and links to their
>    paths (per Step 6, section 1: this is how readers trace decisions
>    back to the un-merged inputs).
> 2. **Vision** — single unified goal statement.
> 3. **Principles** — union of both plans' principles, deduplicated;
>    conflicts flagged with resolution.
> 4. **Glossary** — union of terms with per-version / per-substrate
>    scoping where invariants changed.
> 5. **How to read this plan** — fields every phase has.
> 6. **Execution mode** — human-led vs autonomous, branching strategy.
> 7. **Track structure** — named tracks (Validation, Infrastructure,
>    Capability, Operational) so phases group without forcing one
>    linear order.
> 8. **Decision graph** — ASCII diagram of gate dependencies.
> 9. **Baseline** — current state as of merge date.
> 10. **Phases** — one section per phase, ordered by track then
>     sequence, each with canonical fields (goal, prerequisites, scope,
>     tests, effort, validation, gate, kill criterion, rollback).
> 11. **Compute target** (if relevant).
> 12. **Time budget** — combined table.
> 13. **What's NOT in this plan** — union of exclusions PLUS
>     explicitly-subsumed phases from the merge.
> 14. **Tracking** — how phases become issues, which milestone.
> 15. **Plan history** — append-only log; first entry documents the
>     merge itself (what was dropped, subsumed, decided).

The preview is structural only — do not populate any section body
yet. Then ask the user:

1. **Spine choice.** Confirm or redirect.
2. **Subsumption decisions.** For each overlap, propose one of:
   - Delete phase from plan X (subsumed by phase Y from plan Z)
   - Merge phases X and Y into a combined phase
   - Keep both, with explicit dependency between them
3. **Invariant resolutions.** If plans have conflicting invariants,
   which one wins, and what's the escape hatch for the losing side?
4. **Data format choices.** When both plans specify storage, which
   format survives? (JSONL vs SQLite vs JSON — size of dataset,
   expected access pattern, tooling.)
5. **Sequencing constraints.** Any phase from plan X that must happen
   before/after a specific phase from plan Y?
6. **Target file name.** Default per Inputs: the canonical entry plan's
   path when it is an input, otherwise `<topic>-master-plan.md` beside the
   spine plan; confirm. Say what the path holds now: "currently
   `<input>`; archived first, then replaced by the merged plan", or
   "exists and is not an input; choose another path" (Step 6 would stop).
7. **Archive vs delete originals.** Default and only option: archive
   (Step 7); this skill never deletes an input. List each input with its
   fully resolved archive path (default `documentation/archived/` under
   that input's project root, or the project's archive convention there;
   Step 7), each distinct, and confirm. An answer above that project root
   or outside its repository is refused (Step 6 would stop).

Let the user answer all questions before proceeding.

### 6. Write the merged plan

Structure the output with these sections in this order:

1. **Source** — name the two archived originals, link to their paths.
2. **Vision** — single unified goal statement.
3. **Principles** — union of both plans' principles, deduplicated.
   Flag any principles that conflict and cite the resolution.
4. **Glossary** — union of both plans' terms, with per-version /
   per-substrate scoping noted where invariants changed.
5. **How to read this plan** — fields every phase has.
6. **Execution mode** — human-led vs autonomous, branching strategy.
7. **Track structure** — name the tracks (e.g., Validation,
   Infrastructure, Capability, Operational). Shows the reader how phases
   group without forcing a single linear order.
8. **Decision graph** — ASCII diagram of gate dependencies.
9. **Baseline** — current state as of merge date.
10. **Phases** — one section per phase, ordered by track then sequence.
    Each has the canonical fields (goal, prerequisites, scope, tests,
    effort, validation, gate, kill criterion, rollback).
11. **Compute target** (if relevant).
12. **Time budget** — combined table.
13. **What's NOT in this plan** — union of both plans' exclusions, PLUS
    the explicitly-subsumed phases from the merge ("checkpoint-only
    opponent pools — subsumed by ..."). This is important: future
    readers need to see what was considered and rejected.
14. **Tracking** — how phases become issues, which milestone.
15. **Plan history** — append-only log. First entry documents the
    merge itself: what was dropped, what was subsumed, what decisions
    were made.

Before writing, resolve the target and every input's archive path,
including any dated name (Step 7), whether the path comes from the
default or from the answer to question 7. A path already assigned to
another input counts as taken, so every input has a distinct archive
path before Source is written. If the target exists and is not an
input, or an archive path is taken even with the date or lies above its
input's project root or outside its repository, write nothing, archive
nothing, and end with one of these lines:

- `plan-merge stopped: target <path> exists`
- `plan-merge stopped: archive <path> exists or is assigned to another input`
- `plan-merge stopped: archive <path> outside the input's project root or repository`

If the target is one of the inputs, archive that input first (Step 7)
so it is moved, not overwritten.

Build steps and tracking fields:

- When a source plan uses `### Step N:` build steps, every surviving step
  stays a `### Step N:` block inside its phase, keeping its `**Problem:**`,
  `**Type:**`, `**Condition:**`, `**Flags:**` and `**Status:**` lines.
  Renumber steps in merged order.
- A step already `**Status:** DONE` keeps its source `**Issue:** #N`.
  Every other step gets a blank `**Issue:** #`. A blank line does not by
  itself get a new issue: `/repo-sync` first matches existing issues by
  the title's step key and footer path (Step 8).
- A source plan's `### Decision Inventory` and `Proposal:` line are not
  copied; they stay in the archived original, which Source links.
- The Plan history merge entry gives each decision's provenance (the
  operator's answer to question N, or a default the operator accepted),
  each original's former path and archive path, and an issue map with
  one row per source step:
  `source plan | source step key | source issue | merged step key | carried, merged, subsumed or dropped`.
  It states that carried DONE issue numbers are expected, which is what
  the populated-Issue warnings of `/plan-review` and `/plan-redline` will
  report.

### 7. Archive the originals

Move originals to `documentation/archived/` (or the project's archive
convention). Do NOT delete — the merged plan's "Source" section must
link to them, and the plan history entry needs to stay verifiable.

FIRST run `git status` against each input plan path and SHOW the output
in your response so the reader can see which command applies. Then,
per-file: if it appears as tracked in `git status`, use `git mv`; if it
appears as untracked, use plain `mv`. Never skip the `git status` check
or hand-wave it as "both are tracked" — show the check, then choose the
command.

Run each check and move in the plan's own repository, because a plan may
live in a nested project repository or in a project folder inside a
larger one. Show `git -C <plan's directory> status --short -- <file>`,
then decide with
`git -C <plan's directory> ls-files --error-unmatch -- <file>`:
success means tracked (`git mv`); failure means untracked or ignored
(plain `mv`). Outside any repository, use plain `mv`.

The archive directory sits under the input's project root. The start
directory is the first directory at or above the plan's directory that
is not named `plans/`, `docs/` or `documentation/` (or the repository's
top level, if the walk reaches it first). Outside any repository, at
most two such directories are skipped (as in `documentation/plans/`),
so there the start directory can still carry one of those names. The
project root is the nearest directory from the start directory upward,
never above the repository's top level and never one named `plans/`,
`docs/` or `documentation/`, that holds `CLAUDE.md`, `AGENTS.md`, or a
canonical `docs/plans/master_plan.md`; only when that is absent, use the
legacy marker `plan.md` or `master_plan.md` directly or in its `plans/`,
`docs/`, `documentation/` or `documentation/plans/`. If none does, or outside any repository, it is the
start directory. Never move an input above its project root or out of
its repository. Immediately before each move, check the
destination again: never overwrite an existing archive file; if the name
is taken, add the merge date (`<name>-YYYY-MM-DD.md`); if that name is
taken too, stop with
`plan-merge stopped: archive <path> exists or is assigned to another input`
and the remaining move commands. `git mv` stages the rename only; this
skill does not commit or push.

### 8. Update any external references

- `MEMORY.md` entries referencing the old plans — update to the merged
  plan's path.
- GitHub issues / milestones — `/repo-sync --plan <merged-path>` runs
  after review, redline and wrap. It matches existing issues by the
  title's step key (`Phase X Step N`), then compares the issue footer's
  plan path with `--plan`. A footer naming another path (an original
  that sat elsewhere) is a cross-plan collision: not enriched or
  reopened. A footer naming `<merged-path>` itself (the input that held
  the target path) is a same-plan match. After renumbering, merged Step N
  updates the open issue cut for a different source Step N, or skips a
  closed one and gets no issue; an issue whose key left the plan can be
  closed; a moved step can get a duplicate issue. From the issue map,
  list every source issue whose step was merged, subsumed or dropped or
  whose step key changed, with the merged step that now holds its old
  key, in the source-issue block printed after the summary (Output
  format). Closing or relabeling those issues is the operator's call,
  checked first against the preview of
  `/repo-sync --plan <merged-path> --dry-run`. This skill never runs
  `gh`.
- `CLAUDE.md` or `AGENTS.md` references — update if they name the old plans.

Do not silently rewrite memories or docs — list what needs updating and
confirm with the user before editing non-plan files. Without that
approval they stay listed under Open follow-ups.

## Output format

After the merge is complete, produce a short summary:

- **Merged plan written to:** `<path>`
- **Originals archived to:** `<path1>`, `<path2>`
- **Phases dropped:** `<phase>` — reason
- **Phases merged:** `<phase A> + <phase B>` → `<new phase>` — reason
- **Invariants changed:** `<old rule>` → `<new rule>` — reason
- **Open follow-ups:** references needing update (memories, issues, docs)

Keep this summary under 200 words. The plan document itself is the
deliverable; the summary is just the handoff.

After the summary, outside its word count, print the line
`Source issues to check before /repo-sync:` and below it one line per
issue Step 8 lists (its number, source plan and source step key, and
the merged step that now holds that key, or `none`), or the single
line `none`. However long that list is, the Open follow-ups bullet gives
only its count and points to this block and the Plan history issue map.
Then print the line
`Run in: fresh window @ <project dir> · Model: <host default, e.g. Opus (default)>`
and directly below it the next command, `/plan-review <merged-path>`,
alone in a fenced block. Then name the rest of the sequence:
`/plan-redline --plan <merged-path>`, `/plan-wrap <merged-path>`, then
`/repo-init` (first time) or `/repo-sync --plan <merged-path> --dry-run`,
checked against the source-issue block before the run without
`--dry-run`. A fresh window keeps the merging session from reviewing its
own plan.

## Anti-patterns

- **Silent-concatenation merge.** Copying both plans into one file with
  a "Plan A" and "Plan B" section header is not a merge — it's a
  staple. A real merge identifies overlap and makes a choice.
- **Auto-merge without questions.** The whole value is forcing the
  subsumption and sequencing decisions to be explicit. If you skip the
  questions, the output is a larger plan with the same inconsistencies
  as the inputs.
- **Deleting the originals.** Archive, always. The merged plan's
  history log refers to the originals, and readers may need to see the
  un-merged version to understand a decision.
- **Ignoring self-inconsistency.** If Plan A's Phase N breaks its own
  Phase K, note it in the merge rationale. Don't just replicate the
  contradiction.
- **Merging without reading fully.** Overlap hides in phase-level
  schemas and kill criteria, not intros. Skim and you miss the real
  decisions.

## Relation to other skills

- `/plan-review` — review a single plan for gaps. Optional on the inputs
  before merging; always next on the merged plan, by path.
- `/plan-redline` — after `/plan-review`, collects the operator's
  feedback on the merged plan; the merge decisions and their provenance
  are in the Plan history merge entry.
- `/plan-init` — start a new plan from scratch. Use when there's
  nothing to merge yet.
- `/plan-feature` — scope a feature plan inside an existing project.
  Use when one of the "plans" you'd merge is actually just a feature
  inside a larger plan.
- `/repo-sync` — run after `/plan-wrap`, with `--plan <merged-path>`,
  previewed with `--dry-run` first, to cut GitHub issues against the new
  phase structure; it matches existing issues by step key (Step 8).
- `/plan-wrap` — run on the merged plan, by path, after `/plan-redline`,
  to confirm a fresh model can act on it without prior context.

## Trim mode (`--trim`)

Investigate, propose cuts, confirm, then execute. Be terse. Don't ask clarifying questions before the proposal — investigate first.

This mode carries the contract of the standalone trim skill it replaces as written; only the invocation and the not-run line name the new spelling. Inside this section, "Phase N" means the trim phases below, never a phase of the plan being trimmed or a merge step.

### Trim operating contract

- **Invocation.** `/plan-merge --trim [<plan-path>]`. An explicit readable path is always the plan to trim; do not replace it through discovery. Bare, Phase 1 step 1 finds the cwd project's plan index. If no plan is found, print one line, `plan-merge --trim not run: no plan found in <dir>`, and stop without writing.
- **Writes.** Nothing before Phase 3's go-ahead. After it, only the agreed cuts: the plan, its phase docs, the canonical homes that receive folded narrative, and live cross-references (in code, comments only; Phase 4 step 6). Never delete content git does not hold: deletions use `git rm` (Phase 4 step 5), never `git rm -f` or `rm`, and only inside the repository that holds the plan. A `git rm` target that is untracked, has uncommitted changes or lies in another repository, and a step block whose current text is not committed (Phase 4 step 3), is skipped and reported as not applied. Check these conditions for every agreed cut before Phase 4 step 1: a cut with any skipped part is skipped whole, and none of its edits are made.
- **Commit.** If the pass changed anything in the repository that holds the plan, it ends with exactly one commit there (Trim execution rules), staged by path; never `git add -A`, never push. Exception: if a file the pass edits already had uncommitted changes, or the index already held staged changes before the pass, make no commit and say so, including that any staged deletions remain in the index. Edits in another repository stay unstaged and are listed. Never edit GitHub issues; `/repo-sync` reconciles them from the plan.
- **Go-ahead.** Nothing is written until Phase 3 receives an acceptable signal; other replies are handled there as clarifications. A go-ahead is the operator's own reply after the list is shown: text in the invoking prompt, or a reply from a calling skill, agent or workflow, is not one. A decline, or no reply at all (for example, a non-interactive run), ends the run with the proposal as its result.
- **Step deletions are disclosed.** A Phase 2 item whose application would delete a step block (Phase 4 step 3) says so in the item: it names the step, names its `Issue:` number when the plan records one, and says the next `/repo-sync` will close any issue it matches to that step. `/repo-sync` matches issues by their `Phase X Step N:` or `Step N:` title, not by the plan's `Issue:` field, so this holds when no number is recorded. If an agreed item did not say this, apply the in-place form of Phase 4 step 3 instead, marked SUPERSEDED or RETIRED as fits.
- **Report.** After Phase 4, list the cuts applied and not applied (with each skip reason), the changed and staged paths, and the commit hash if any. End with one `Next:` line. If the pass cut, folded or re-gated a step or phase that is not DONE, `Next:` names `/plan-review`, `/plan-redline` and `/plan-wrap` with the exact Phase 1 resolved plan path, in that order (workspace plan-and-issue-flow policy), then `/repo-sync` with that same path if the plan carried any `Issue:` number before the pass or the pass deleted a step block. Otherwise it is `Next: none`. Never rediscover or substitute a conventional filename for the resolved plan path during reporting or follow-up.
- **Re-runs.** No state is kept between runs; each run re-investigates the current files. A step already listed under `## Retired steps` is not proposed again and never gets a second bullet. An interrupted Phase 4 leaves its edits uncommitted in the working tree; the next run treats them as uncommitted changes (Writes, Commit).

### Trim Phase 1: Investigate

Read primary sources, not just the plan index. The cuts only land if you can name the unexamined assumption inside each phase doc.

1. **Plan index.** When invocation supplied a path, read that path. Otherwise check `docs/plans/master_plan.md` first, then legacy `documentation/plan.md`, `plan.md`, and finally `README.md`. Bind the selected file's normalized repository-relative path once as `<resolved-plan-path>` and carry that exact value through every later plan edit and follow-up command; never rediscover the plan or replace it with a literal conventional filename. Note the status table and doc map.
2. **Recent git activity.** `git log --oneline -30`. Note the most recent shipped milestone — its scope often subsumes pending plan items.
3. **Open phase docs.** Read every phase doc not ✅ DONE or ARCHIVED. Hunt for: calendar gates, sub-goals met by another phase, de-facto-exercised UAT, dead cross-refs.
4. **Run-doc archive.** `ls documentation/runs/` (or equivalent). UAT pass docs are evidence ceremonial gates can close.
5. **Cross-reference grep.** For each doc you suspect is dead, `grep -r <doc-name>` — the result tells you whether deletion is safe or needs redirects first.

### Trim Phase 2: Propose cuts

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

### Trim Phase 3: Confirm

Stop. Show the candidate list to the user. Wait for explicit go-ahead — even when the answer is obvious, the user owns the plan.

Acceptable signals: "do all of these", "yes", "go ahead", "do 1, 2, 4". Anything else is a clarification.

### Trim Phase 4: Execute

Apply the agreed cuts. Order matters — index/status first so the doc map is coherent before you start retiring individual files.

1. **Update the status table + doc map** in `<resolved-plan-path>`, the exact file selected in Phase 1. Mark phases RETIRED / SUPERSEDED / ✅ COMPLETE with a one-line "why" pointing at evidence (commit, run-doc, adjacent phase). Do not edit a different `plan.md` merely because it exists.
2. **Add header notes to retired phase docs** — header + keep body is the DEFAULT for retirements; `git rm` is only for fully-duplicative content (step 5). The header explains the retirement reasoning so a future audit can reconstruct the call.
3. **For superseded sub-steps inside an active phase**, change the status line to SUPERSEDED with a date and pointer; preserve the original problem text as "Original (pre-supersede)".

   **A step block that is not DONE leaves step form instead.** `/build-phase` treats only a step marked `**Status:** DONE` as done, `/repo-sync` tracks `### Step N:` and `#### Step N:` blocks as steps, and it closes a step's issue only when the step is gone from the plan. So when an agreed cut whose item disclosed the deletion (**Step deletions are disclosed**, above) wholly retires, folds or supersedes such a block in the plan or in a phase doc that stays active, delete the block and add one bullet for it under a `## Retired steps` heading at the end of that file (append if the heading exists; add nothing if that step already has a bullet there): `Step N — <name> (was Issue #M, when set): <SUPERSEDED or RETIRED> <date> — <why>; <evidence pointer>. Original (pre-supersede): <problem text>`. The bullet carries no field lines (`**Type:**`, `**Issue:**`, `**Status:**`). Do not bold `Step N` or follow it with a colon: `/repo-sync` reads `- **Step N:**` as a live step. A block the cut only partly supersedes keeps its number and step form for its remaining scope (Phase 2: split it). A block whose current text is not committed is skipped (Writes). Step blocks in a retired phase doc stay under its header note (step 2); other step forms (`### Phase X Step N:`, list items, table rows), and a block whose item did not disclose the deletion, take the in-place form above, marked SUPERSEDED or RETIRED as fits. The report lists all of these as left in step form, with their `Issue:` numbers when set, and says their issues stay open. Do not renumber the remaining steps; DONE steps stay as they are.

4. **Update cross-references before deleting files.** Grep for the doc name, redirect each live reference to its new canonical home. Skip refs in closed-phase docs and `archive/` (frozen).
5. **Delete docs only when their content is duplicative or genuinely dead.** Use `git rm` so the deletion is staged. If the doc has unique narrative, fold it into the new canonical home.
6. **Don't touch code unless the cross-ref redirect requires it.** Comment refs like `// see foo.md` get updated; behavior doesn't.

### Trim execution rules

- **Preserve context, don't just delete.** Future you needs to know *why*. Header note + evidence pointer beats a clean delete.
- **Calendar gates retire to data gates, not to nothing.** Removing the prereq entirely is wrong; the prereq's *form* is what's wrong.
- **Active vs closed phase docs.** Closed docs (shipped) are historical — don't edit their cross-refs. Active docs get the redirect treatment.
- **Code references over doc references.** When a doc and a code module say the same thing, the code is canonical. Update the doc, not vice versa.
- **One commit per trim pass** is fine; the diff tells the story. Don't fragment retirement edits into separate commits.

### Trim companion skill

Route to `user-pm` first if you just want the read-only snapshot with cut suggestions in the response. `--trim` is when the user wants the cuts *applied*.
