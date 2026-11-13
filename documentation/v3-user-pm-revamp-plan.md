# user-pm revamp plan (Skill Mesh v3, lane J)

This is the execution copy for build-phase, copied 2026-11-12 from the operator's planning records in the coding root (`<coding-root>/docs/skill-mesh-3-review/`), where its reviews and the operator's answers live. Step status is recorded here from now on.

Prepared 2026-11-12 (overnight window), planning only. Corrected 2026-11-12 after the self-review and the
independent review (see "Correction round" in the self-review file). No skill file is edited by this document.
Amended the morning of 2026-11-12 at the operator's request: user-pm also helps split a project into lanes
(Step 8 part B), with matching edits to the fixed constraints, Steps 9, 10 and 15, and open item 9. Then the
morning answers to the decision sheet (2026-11-12): a `main` lane (item 67), no overall time budget (item 37)
and dev-observatory reading `--json` as its own later work (item 31). These amendments came after the review
rounds and were covered by the final plan-review and plan-wrap pass of 2026-11-12 (record: `<coding-root>/docs/skill-mesh-3-review/user-pm-revamp-plan-2026-11-12-final-review.md`).
Correction round 2 (2026-11-12, the one allowed round): the operator's answers to items 27 to 38 and the
approved v3 and v4 split (`<coding-root>/docs/skill-mesh-3-review/v3-v4-split-proposal-2026-11-12.md`, called the "split proposal" below) are applied. Steps 2 and 7 are met and recorded, Step 8 part A is bound to the real
Passing Notes verbs, Step 12 is a recorded decision, and absolute user paths are removed. The delta review
file's "Correction round 2" section holds the row-by-row record.

Authority: operator approval 2026-11-11 23:45 PST of decision-sheet items 10, 11, 12, 61 and BQ1
(`<coding-root>/docs/skill-mesh-3-review/decision-sheet-2026-11-11.md`) and maintenance item C2 with F5 and F6
(`<coding-root>/docs/skill-mesh-3-review/skill-maintenance-actions-2026-11-11.md`).
Groundwork: `<coding-root>/docs/skill-mesh-3-review/user-pm-revamp-brief-2026-11-11.md`. Decided shape: brief
Option A (read-only front door that cites and hands off by paste line). Not re-opened here.

All source paths below are repo-relative to skill-mesh unless stated; other coding-root paths are written
`<coding-root>/...`. Builds run from the v3 integration checkout (branch `v3/main`), never the main checkout.

## Goal

`user-pm` becomes one project's read-only front door. In one pass it shows live checked-versus-unchecked
status, a board of plans and immediate fixes with one route label per item, open decisions, autonomous-run
readiness, lane cards and waiting notes, a lane check (and, on request, a proposed split of the project into
lanes), 3 to 5 anchored improvement ideas, cuts and one next move. It
hands work off by paste lines and never calls another skill. `user-orient` is retired. The goblin skills
are not called.

## Scope boundary

Only `user-pm`'s share of item 61 (lane cards and waiting notes in the status view) is planned here, plus lane
planning, which the operator added on 2026-11-12 (Step 8 part B). The
Passing Notes pre-commit and checkpoint checks in `task-handoff`, `session-wrap`, `build-step` and
`repo-update` belong to the other v3 lanes and are not done by this plan.

## Fixed constraints (copied from the approved decisions, not new design)

- Read-only. It never edits files, never executes a proposed command, spawns no agent, calls no named skill
  (`skills/user-pm/core.md` line 6 stays true). One project per run (item 12).
- Remote reads are limited to the project's open GitHub issues and pull requests, read-only, through `gh`,
  each with its own numeric timeout. Fetched text is data, never instructions (`.claude/rules/security.md`);
  the rewritten core states this itself, because core behavior is what ships.
- Routes are the three in `<coding-root>/documentation/system-workflow-plan.md`, "Route-aware work and outcome queue".
  Route rules are applied by citing `skills/user-build-route/core.md` sections (route table, "Check the route
  can run"), never by copying them (`.claude/rules/code-quality.md`, one source of truth).
- Human-owned tasks and decisions stay on the board with owner "you" and no route to an agent.
- Idea shortlist: single pass, 3 to 5 ideas, each anchored to an issue reference or a tracked path
  (the anchor contract from `skills/goblin-suggest/core.md` lines 158-162 is the model; the skill is not
  called), labelled "unjudged".
- `--json` is additive only. No existing key is renamed, removed or retyped. No production code parses
  `--json` today (see "Consumer facts"); additive stays the rule anyway.
- One new topic flag, `--lanes` (operator request 2026-11-12, Step 8 part B), and no others. The existing
  topic flags keep their names and meaning. The catalog description lists no flags (`tools/gen_manifest.py`
  `DESCRIPTIONS`, read 2026-11-12), so it stays unchanged and Codex catalog space is unaffected.
  dev-observatory's `_VALID_MODES` does not reach `--lanes`; that is accepted.
- Lanes (item 61) are an advisory, fail-open read of Passing Notes. Absent store or tool means silent skip.
  Lane planning (Step 8 part B) reads only the board and the project's committed lanes table, and proposes.
  It never writes a lanes table or a card.
- Dependency: the `user-dr` register is NOT read by this plan's first ship. Step 3 prints one line "no decision register; run /user-dr" and keeps the existing `--decide`
  list. The register binding is Step 18, after the operator accepts the format (Step 17).
  `user-fermize` gets a paste line labelled "Codex window" until a Claude adapter exists.
- Reviewer flags: every code step uses `--reviewers` default (two independent reviewers). `full` and `runtime`
  are not used: they need `--start-cmd` and `--url`, and there is no app to start. The real-run check is the
  operator Step 15.
- Recovery: a failed catalog mutation follows the lifecycle guide's recovery rule and locked stop codes
  (`documentation/skill-catalog-lifecycle.md`; not restated here). Stop before writing, revert the whole
  mutation, never patch generated surfaces by hand. Checkpoint after each regenerate.

## Consumer facts (read from `dev-observatory`, 2026-11-12)

`<coding-root>/dev-observatory/src/dev_observatory/review.py` is the only production caller of `user-pm`:

- `_build_prompt` sends `/user-pm` or `/user-pm --<mode>` plus a `Context: review the project '<slug>'.` line.
  `_VALID_MODES = ("default", "goal", "outstanding", "cut")`; any other mode is coerced to `default`.
- `run_review` stores the runner's text as `ReviewResult.report`; `POST /review/{slug}` returns it. The default
  Claude runner has a 300-second timeout (`_CLAUDE_TIMEOUT`).
- It never passes `--json` and parses no JSON. The statement that dev-observatory reads `--json`
  (`_shared/skill-pipeline.md` line 173 and the core's hook section) is a documentation premise only. Step 1
  confirms by grep and records it; Step 11 binds to the prose and timeout contract above.

## Catalog lifecycle operations (per `documentation/skill-catalog-lifecycle.md` section 5)

| Operation | Target | Rule that applies |
|---|---|---|
| UPDATE | `user-pm` core + providers (claude, codex, gpt) | Core carries shared behavior; adapters only bind host; never weaken a core gate. Regenerate and verify every provider profile. |
| DELETE | `user-orient` | Enumerate and disposition every caller, link, asset, fixture, mapping and install-ledger effect first; regenerate; verify absence; let the installer's ledger-owned cleanup remove host copies. Section 8 reference dispositions required. A hand DELETE is blocked: section 3 of the guide ("Remaining lifecycle scope") says a later CREATE, DELETE or RENAME needs its own authority until the phase completes. Unblock, decided 2026-11-12 (item 27, and the v3 and v4 split proposal, Q1): one scoped lifecycle exception approved for the whole v3 catalog batch (precedent: code-consigliere, user-dr; recorded base ref, target paths, pre-write hashes, isolated worktree). Waiting for master-plan Steps 111 to 113 is not taken. See Step 12. |
| Repoint references | every `user-orient` and changed-mode mention | Dispositions per section 8 of the guide; see Step 13. |

`user-pm` is not one of the four representative skills (`tests/fixtures/representative_skills.json`; re-read
the fixture before relying on this), so editing its core should not invalidate
`documentation/release-candidate-report.md`. Verify with
`python tests/smoke/gen_release_candidate_report.py` producing no diff.

## Dependencies and order

1. `user-build-route` is on skill-mesh `origin/main` as commit `5924e27` (item 28, default taken; checked
   2026-11-12, Step 2). Steps 3, 4, 6 and 13 may cite its sections. The `user-dr` skill is already on
   `origin/main` (v2.0.4, commit `2ae2661`).
2. All skill-mesh edits run in the v3 integration checkout (branch `v3/main`), never the main checkout, which
   stays untouched (the working rule and the two prior scoped exceptions). This replaces the earlier "wait
   for a clean main checkout".
3. DELETE of `user-orient` runs under the scoped lifecycle exception approved for the v3 catalog batch (Step 12).
4. The Passing Notes command-line tool is committed (its own Steps 1 to 3 are complete); the lane steps (7, 8) are bound
   to its real read verbs (Step 7).
5. The `user-dr` first-trial and `user-fermize` Claude adapter waits are placed late (Step 17); they gate
   only the follow-up binding (Step 18), not the main work.

---

### Step 1: Pre-flight audit of the `--json` wire and current consumers, plus baseline capture

**Problem:** Per `.claude/rules/code-quality.md` (grep all downstream consumers; audit wire shape), consumers
of `user-pm` output must be enumerated before any shape change. The first read (see "Consumer facts") found
that `review.py` passes text through and parses no `--json`; this step confirms it and captures the baseline
key list before any core edit can change it.
**Type:** code
**Issue:** #226
- **Status:** DONE 2026-11-12 as a direct task (its output lives outside this repository, so build-step could not land it). Evidence: `<coding-root>/docs/skill-mesh-3-review/user-pm-revamp-wire-audit-2026-11-12.md`: 25 consumer rows (19 OK, 6 already handled, 0 needs fix); no production code parses `--json`; baseline key lists dated before Step 3.
**Flags:** `--reviewers` default
**Produces:** a consumer table in `<coding-root>/docs/skill-mesh-3-review/user-pm-revamp-wire-audit-2026-11-12.md` with one
row per live call site of `user-pm` output (`dev-observatory` `review.py`, `web/app.py`,
`scripts/export_toolkit_ui_snapshot.py`, the ambition UI assets, `_shared/test_grader_prompt.py`, plan-trim,
task-handoff, user-draft) and a verdict `OK | needs fix | already handled`; plus the exact current `--json`
key lists (default and topic modes) copied from `skills/user-pm/core.md` and `_shared/skill-pipeline.md`
line 173, captured from `origin/main` as the baseline for Step 10.
**Done when:** every live caller (tracked source and docs, excluding `archive/`, `.build-step/`, build output
and `node_modules`) has a verdict row; the table states in one sentence whether any production code parses
`--json` today; the baseline key lists are in the file and dated before Step 3 starts.

### Step 2: Wait for `user-build-route` on `origin/main`, then build from the integration checkout

**Problem:** Steps that cite `user-build-route` sections cannot pass before it is on `origin/main`. Editing in
the dirty main checkout is the collision named in the brief, so builds run from the v3 integration checkout.
**Status: MET 2026-11-12.** The operator took the default on the merge (item 28); `user-build-route` is on
`origin/main` as commit `5924e27`. Recorded result: `git show 5924e27:skills/user-build-route/core.md` contains
the heading "Check the route can run" (line 42).
**Type:** wait
**Issue:** #227
- **Status:** DONE 2026-11-12 (wait met). `git ls-tree origin/main skills/user-build-route/core.md` lists the file; its core contains "Check the route can run"; the integration worktree `skill-mesh-wt/v3-main` (branch v3/main) equals `origin/main` 1c0cae5 with an empty `git status --porcelain`.
**Flags:** none
**Produces:** a checkpoint record of the integration checkout (branch `v3/main`), its `git rev-parse HEAD`, and
the output of `git ls-files skills/user-build-route/core.md` in it.
**Done when:** `git ls-tree origin/main skills/user-build-route/core.md` lists the file; the integration
checkout has `git status --porcelain` empty at the start of each build step; and its core contains the heading
"Check the route can run". Builds never run in the main checkout.

### Step 3: Core rewrite A, status view, board and routes (UPDATE)

**Status:** DONE 2026-11-12. Steps 3 to 5: commits 2a3e9a2, 2e502b2, 553a865, correction d05f8ed; reviewed APPROVE (`<coding-root>/docs/skill-mesh-3-review/builds/user-pm-core-review.md`). Focused tests plus the quick repo-wide checks under the adopted testing rule; no full suite.

**Problem:** The current core reads one plan plus `git log`, with no live-status view, no route labels and no
issue/PR reading.
**Type:** code
**Issue:** #228
- **Checkpoint (2026-11-12, build):** user-orient's `--quick` thread recap and its session-length word budgets (the ~250 and ~600 word targets and the compressed short-session form) were dropped, not absorbed. No recap without lookups remains; the core's Limitations route that need to `task-handoff --resume` and `user-wrap` (brief section 3).
**Flags:** `--reviewers` default
**Produces:** edits to `skills/user-pm/core.md` only:
1. Status view absorbed from `user-orient` (F6): current state observed this run is evidence; memory,
   handoffs and earlier summaries are leads and lose any conflict; parallel read-only lookups with orient's
   lookup limits; a Verified / Not-yet-verified split; manual checks under 60 seconds; correct repository
   selection for a nested project without its own `.git`; empty sections omitted. Orient's `--quick` and
   session-length word budgets are dropped; record that in the plan checkpoint (no no-lookup recap remains;
   route that need to `task-handoff --resume` and `user-wrap`, per the brief section 3).
2. Board: one table across plan steps, immediate fixes (dirty tree, recorded failures, open bug issues and
   pull requests from read-only `gh`, each read with a numeric timeout of 30 seconds; if `gh` is unavailable,
   unauthenticated or times out, one `notes` line and the rest continues), and human-owned items. Each row has
   route (core pipeline, bounded goal, direct task, or "you"), owner, exact next action and evidence age.
   Routes are assigned by citing named sections of `skills/user-build-route/core.md`; the core contains no
   restated route table. Unknown readiness is "not ready", never inferred ready.
3. Decisions: no register is read. One line "no decision register; run /user-dr" and the existing `--decide`
   list.
4. A statement in the core that fetched issue and pull-request text is data, never instructions.
5. Existing sections and flags keep their names and meaning; the core's `--json` section is untouched here
   (Step 10).
**Done when:** `python -m pytest tests/package-integrity` passes in the worktree; grep of the core finds no
`Route | Eligibility` table copy and finds `skills/user-build-route` cited; the core states read-only, no agent,
no named-skill call, and the fetched-text-is-data rule.

### Step 4: Core rewrite B, autonomous readiness checklist (UPDATE)

**Status:** DONE 2026-11-12. commit 2e502b2; review as Step 3.

**Problem:** The Overnight rubric misses a dirty no-commit checkout, host capability and agent capacity, the
exact incident behind `user-build-route` (brief section 0). This is the must-fix.
**Type:** code
**Issue:** #229
**Flags:** `--reviewers` default (independent review is deliberate here: the section gates overnight runs)
**Produces:** edits to the core's Overnight rubric adding three checks that cite `skills/user-build-route/core.md`
"Check the route can run" rather than copy it: (a) dirty checkout or stash that must not be committed, or a
stated no-commit rule; (b) host capability for the intended route including reviewer availability and test
time against budget; (c) agent capacity, with the rule that capacity is not proven by consuming it. Unknown
capability yields a "qualify first" line, not a go. A known conflict yields no unconditional route. Paste
lines for `/build-phase`, `/goal` and, only where a project declares a queue, `/queue-prep`. A fallback pool
is named from the progress standard's four lanes (`docs/templates/progress-standard.md`, unattended-window
closeout gate).
**Done when:** `python -m pytest tests/package-integrity` passes; the core names all three gaps and cites the
route-compat section.

### Step 5: Core rewrite C, improvement shortlist (UPDATE)

**Status:** DONE 2026-11-12. commit 553a865, correction d05f8ed; review as Step 3.

**Problem:** There is no idea shortlist (F5), and the old rule "do not invent moves not derivable from plan +
git log + archive markers" blocks it.
**Type:** code
**Issue:** #230
**Flags:** `--reviewers` default
**Produces:** a shortlist section: 3 to 5 ideas, each with an anchor (issue reference or tracked path,
optionally `:line`; prose anchors refused, the idea is dropped instead), labelled "single pass, unjudged". The
old rule is replaced by "ideas must be anchored; moves must be derivable from the plan, git log, archive
markers, live state or open issues and pull requests". The `user-fermize` paste line is labelled "Run in: a
Codex window" and a test asserts the label appears. No new flags are added.
**Done when:** `python -m pytest tests/package-integrity` passes; a grep shows the "unjudged" label, the
anchor rule and the Codex-window label in the core.

### Step 6: Readiness-citation test (round trip)

**Status:** DONE 2026-11-12. commit a2632a8 (also aligns the known-conflict check with user-build-route's short-lived-conflict rule); Steps 6 to 10 reviewed APPROVE, nits only (`<coding-root>/docs/skill-mesh-3-review/builds/user-pm-core-2-review.md`).

**Problem:** A mocked prose test cannot see drift between the rubric and `user-build-route`; a test must fail
when the rubric stops citing the route-compat section or the section is renamed.
**Type:** code
**Issue:** #231
**Flags:** `--reviewers` default
**Produces:** `tests/package-integrity/test_user_pm_readiness_citation.py` asserting: (a) the user-pm core
cites `skills/user-build-route/core.md` and the heading "Check the route can run"; (b) that heading exists in
`skills/user-build-route/core.md`; (c) the user-pm core names the three gaps; (d) the core has no restated
route table. Includes a red-on-garbage anchor: the test fails on a fixture core with the citation removed.
**Done when:** the test passes on the real core and fails on the garbage fixture; both results are recorded.

### Step 7: Wait for the Passing Notes command-line tool

**Problem:** The lane section binds to the tool's read verbs, which do not exist until the tool is committed.
**Status: MET 2026-11-12.** The tool is committed in `<coding-root>/passing-notes` (commit `53bb0f7`; its
Steps 1 to 3 are complete; `passing-notes --version` reports 0.1.0). Read verbs, taken from the tool's `--help`
text and source (`src/passing_notes/cli.py`):
- `passing-notes card show --project <p>`: one line per lane (lane, host, state, item, updated), then at most
  20 diagnostic lines and a total count. With `--lane <l>` it prints that lane's card, notes framed as
  untrusted data.
- `passing-notes inbox --project <p> --lane <l>`: one tab-separated line per open note (id, kind, needs, from,
  subject), acknowledged and superseded notes hidden, then diagnostics and a count.
- `passing-notes read --project <p> <note-id>`: header plus body between untrusted-data frame lines. Reading
  never acknowledges. `user-pm` does not call it; the note id and path are enough.
- `ack` and `post` and `card set` are write verbs and are never called by `user-pm`.
- Exit codes: 0 ok, 1 output, 2 usage, 3 not found, 4 store unusable (including `store-in-repo`, `store-link`).
- Store: `%LOCALAPPDATA%/passing-notes/` with `messages/`, `acks/` and `cards/<project>/` folders;
  `PASSING_NOTES_ROOT` (absolute path) overrides it. Measured on an empty temporary store: both read verbs
  exit 0 and print only `diagnostics: 0`.
**Type:** wait
**Issue:** #232
**Flags:** none
**Produces:** a checkpoint record of the committed tool path, its commit id, and the `--help` read verbs.
**Done when:** the tool is committed (its commit id is recorded) and `--help` output listing the read verbs is
saved in the checkpoint (the verbs above stand as that record; re-read `--help` at Step 8 start and stop if
they differ). Reorder allowance (item 38): Step 9 is the only later step that is lane-independent and may run
before Step 8. Step 10 (its `lanes` key and test) and Step 11(c) (it names Passing Notes) depend on Step 8.

<!-- autofix-applied: 2026-11-12 -->
### Step 8: Lanes section: lane cards and waiting notes, plus lane planning

**Status:** DONE 2026-11-12. commit 8d1838c; review as Step 6.

**Problem:** Item 61 requires `user-pm`'s status to show each lane's card and waiting notes (part A). On
2026-11-12 the operator also asked that `user-pm`, as the project's front door, help break the project into
lanes (part B). A lane is a named, lasting slice of one project's work (the paths, resources and seeds it
owns), worked by one window at a time, and a project lists its lanes in a committed `docs/lanes/README.md`
table (`<coding-root>/docs/skill-mesh-3-review/v3-program-plan-2026-11-11.md` section 8, "What a lane is"). It is not the progress standard's four
lanes (host and work strands) and not the driver's job lanes; the core says so in one line. The protocol
(`<coding-root>/passing-notes/docs/protocol.md`, "Lane cards", "Inbox, read, acknowledge") holds cards at
`cards/<project>/<lane>.md` and the store stays out of Git. Passing Notes is not one of the portfolio
utilities enumerated in `.claude/references/advisory-call-convention.md`, so the section follows that
convention's eight points by analogy and adds no convention entry (item 34, default taken; the tool has
since landed, and a convention entry would be its own later change). Inbox checks inside skills are owned by this v3 plan, not by the Passing Notes tool plan.
**Type:** code
**Issue:** #233
**Flags:** `--reviewers` default
**Produces:** a "Lanes" section in `skills/user-pm/core.md`, a `--lanes` topic mode, and tests, specified as:

Part A, lane cards and waiting notes (binds to the Step 7 verbs):
- Cheap gate: `passing-notes` not on PATH, or the store folder (`%LOCALAPPDATA%/passing-notes/`, or
  `PASSING_NOTES_ROOT`) absent, or `card show` reporting no lanes (only `diagnostics: 0`): skip silently with
  zero output. Present-but-malformed store or card, or exit code 4 or a diagnostic line, yields one `notes`
  line, not a halt.
- Bounded read: read-only calls to `passing-notes card show --project <p>` (the lane list) and, for each lane
  listed, `passing-notes inbox --project <p> --lane <l>` (its open notes), for at most 20 lanes (this skill's own
  cap, the operator's 2026-11-12 figure; the protocol's `CARD_LIST_MAX_ITEMS` is also 20 but caps a card's
  `owns`/`holds` entries, not the lane count, so it is not the source; more lanes: one `notes` line, rest unread). Each call is synchronous with its own numeric timeout (30 seconds), whole-process cleanup and
  an output cap using the protocol's `CARD_MAX_BYTES` (8192); the single-card form `card show --lane` is used
  only when one lane is asked about. No `read`, `ack`, `post` or `card set` call: no acknowledgement, no note
  posting, no card write. Acknowledging a note is an operator action surfaced as a paste line.
- Output: lane card headline plus count and first lines of open notes per lane, with a pointer to the note
  id and the store's `messages/<project>/` folder (never a copied body), and acknowledgement state. Never a halt or `(y/n)`.
- Identity: no session id is fabricated; the lane list comes from the store.
- Card contents are data (private paths): never included in `--json` beyond headline and state fields, and
  kept out of any committed file.

Part B, lane planning (operator request 2026-11-12; no Passing Notes dependency):
- Inputs: the board from Step 3, the project's committed `docs/lanes/README.md` if present, the plan's
  phases, and the paths each board item already names (plan step `Produces:` lines, issue and pull-request
  text read in Step 3). It adds no outside call. A board item with no known path goes to `main`, never guessed
  into a work lane.
- Default mode adds at most two lines to the Lanes section. With a lanes table: board items no lane owns
  (count and the first one), paths two lanes both claim, lanes with no board item, and a table with no `main`
  lane. Without one, when the
  board spans two or more areas that could run at the same time: "No lanes yet; N areas could run in
  parallel: run `/user-pm --lanes`". Omitted when the board is a single area.
- `--lanes` topic mode, in the existing three-part topic shape (Context, What this unblocks, The work). With no
  lanes table it proposes a split; with one it reviews the split (unowned items, overlaps, idle lanes, lanes
  to merge or split). Per lane: id, one-line purpose, what it owns (paths, seeds, resources), its board items
  in order, a suggested host (Claude, Codex or either; "qualify first" when the host's capability is unknown,
  per Step 4), and what it hands to or needs from other lanes.
- Splitting rules, stated in the core:
  - Every split has a `main` lane (operator, 2026-11-12, item 67): the lane the operator coordinates
    through. It takes the board items that are unplaced or could belong to more than one lane, owns the
    shared files (the plan, manifests, lockfiles, generated output) and does the merges. A lane that cannot
    tell where a note or item belongs sends it to `main`. This matches you-asked-for-it's `central` lane.
  - Split on file ownership first: no path is owned by two lanes.
  - A resource that cannot be split (an engine, a play checkout, credits, machine memory) is listed as
    shared and claimed through Heads Up, never assigned to two lanes.
  - Each lane can park without stalling the others; a lane that cannot is merged into the lane it waits on.
    An area with fewer than two board items folds into a neighbour.
  - `main` plus at most four work lanes by default, from the you-asked-for-it pilot (a central lane plus
    two window lanes; four skeleton sub-lanes; `<coding-root>/docs/skill-mesh-3-review/lanes-retrospective-2026-11-11.md` section 1).
  - Human-only items keep owner `operator` on the board. `operator` is a reserved id in the protocol's grammar,
    so it is never a lane id in the draft table.
  - Lane ids follow the protocol's id grammar, cited, not restated.
- Output ends with paste-ready text: a draft `docs/lanes/README.md` table and one starter line per lane for
  opening its window. `user-pm` writes neither; creating the table and the cards is the operator's act, or a
  lane window's, which keeps the read-only rule.

**Done when:** Part A tests cover store absent (no output), store malformed (one notes line), one lane with
one waiting note (rendered), tool timeout (one notes line, rest of snapshot intact), and a 50 KiB card
(truncated at the cap). Part B tests assert the core documents `--lanes`, that its output is draft text with
no file write, the `main`-lane, park and lane-count rules, and a citation of the protocol's id grammar with no
restated grammar; each test fails on a fixture core with its rule removed. `python -m pytest
tests/package-integrity` passes. Part B does not depend on Step 7: if the Passing Notes tool stalls, Part B
may be built and reviewed alone, and Part A follows when Step 7 completes.

### Step 9: Provider adapters and description headroom

**Status:** DONE 2026-11-12. commit f68f46e; review as Step 6.

**Problem:** A portable skill needs `providers/claude.md`, `codex.md` and `gpt.md`. The Codex adapter treats
overnight qualification as "recommendation text, never auto-dispatched work", and the Codex description budget
has 577 characters of headroom after `user-dr` (brief section 1.6). Host differences exist for `gh` access,
process timeouts and agent capacity.
**Type:** code
**Issue:** #234
**Flags:** `--reviewers` default
**Produces:** updated `skills/user-pm/providers/claude.md`, `codex.md`, `gpt.md` (gpt under its deprecation
note) that bind only host facts; no gate weakened. The description in `tools/gen_manifest.py` `DESCRIPTIONS`
is unchanged: it lists no flags, so the `--lanes` mode does not touch it.
**Done when:** `tests/package-integrity/test_codex_budgets.py` passes; each adapter loads the core in full;
diff review shows no adapter text restating a core gate.

### Step 10: `--json` additive output and a superset test

**Status:** DONE 2026-11-12. commit 9ab43fb; review as Step 6. The dev-observatory issue is filed in the coding-root tracker as #596.

**Problem:** Keys must be added, never changed. Baseline (from Step 1): default mode has `project`,
`what_it_is`, `history`, `outstanding`, `possible_next` (each item with `category`), `cut_candidates`,
optional `notes`; topic mode has `project`, `topic`, `context`, `unblocks`, `work`. Nothing parses this today.
**Type:** code
**Issue:** #235
**Flags:** `--reviewers` default
**Produces:** the core's `--json` section extended with new optional top-level keys, each omitted when empty:
`status` (`verified`, `not_yet_verified`, `manual_checks`), `board` (array of `{item, source, route, owner,
next_action, evidence_age}` where `route` is one of `core-pipeline`, `bounded-goal`, `direct-task`, `human`),
`decisions` (`open`, `decided`, `register`), `readiness` (`lanes`, `blockers`, `fallback_pool`), `lanes`
(card summaries, no bodies), `lane_plan` (`mode` proposed or reviewed, `lanes` as an array of `{lane, purpose,
owns, items, host, handoffs}`, `unplaced`, `shared_resources`), `ideas` (array of `{idea, anchor, judged:
false}`). The
`possible_next[].category` enum stays `test|build|decide|overnight|other`; route labels live in `board`. A test
in `tests/package-integrity/` reads the key list stated in the core and asserts it is a superset of the Step 1
baseline key lists, with the new keys optional; the old baseline key list serves as the garbage-anchor input
(a core missing a baseline key fails). The core says `--json` has no production caller today.
**Done when:** the superset test passes on the real core and fails on the garbage anchor; the Step 1 table
has no `needs fix` rows. The finding that no dev-observatory code parses `--json` is filed as a separate issue
for that repository's owner, proposing that its review page read `--json` (operator, item 31) and that its
300-second limit be revisited (item 37); this plan adds no parser.

### Step 11: Integration test through the production caller (prose and timeout contract)

**Status:** DONE 2026-11-12 (reviewed APPROVE with one correction round, `<coding-root>/docs/skill-mesh-3-review/builds/user-pm-tail-review.md`). skill-mesh commit 203a301 (parts b and c, plus the core's Call budget paragraph); coding-root commits aa07bd71 and 34f0918a, the second adding in-file helper anchors after review (part a, `dev-observatory/tests/test_review_user_pm_contract.py`). Part (a) reads the installed coding-root core and checks only text that both the pre-revamp and the revamped core carry; it also passes against the revamped core in a scratch tree. Re-run it against the installed copy after the Step 16 install. Focused tests plus the quick repo-wide checks under the adopted testing rule; no full suite. dev-observatory's own suite has 6 failures in other files that fail the same way without this test.

**Problem:** `code-quality.md` requires an integration test through the production entry point. The real
caller is dev-observatory's review path, which sends `/user-pm` or `/user-pm --goal|--outstanding|--cut`,
stores the prose reply and allows 300 seconds (see "Consumer facts"). A JSON fixture or a live `claude -p`
run would test the wrong contract (nondeterministic, spends quota, crosses repositories).
**Type:** code
**Issue:** #236
**Flags:** `--reviewers` default (no runtime lens: no app start; the live run is Step 15)
**Produces:** (a) a test in `<coding-root>/dev-observatory/tests/` (new `test_review_user_pm_contract.py`)
driving `dev_observatory.review.run_review` through its runner seam for each of `_VALID_MODES`, asserting the
prompt issued is a form the revamped core accepts (mode names unchanged; the `Context:` line only focuses)
and that a stored prose reply of representative length is returned unchanged; (b) a skill-side test in
`tests/package-integrity/` asserting the core still documents bare mode, `--goal`, `--outstanding` and
`--cut`, and that the title-and-`What it is` header rule the observatory renders is preserved; (c) a budget
statement in the core that each outside call (`gh`, Passing Notes) carries its own numeric timeout, so a hung
call cannot freeze the run, with a test asserting each outside call in the core names a timeout. The status
view's own lookups (git, file reads, manual checks of at most 60 seconds, Step 3 item 1) each name their own
ceiling the same way (delta N3, applied as item 37 default and then settled by the removal below: each call is
bounded, no sum is budgeted). There is no
overall time budget (operator, 2026-11-12, item 37): `user-pm` now does far more than a quick orientation, and a
fuller picture is worth the wait. dev-observatory's 300-second `_CLAUDE_TIMEOUT` may cut off a long review;
changing it belongs to that repository and goes in the issue filed under Step 10. New flags are not reachable from `_VALID_MODES`; that is
accepted and no flags are added.
**Done when:** (a) and (b) pass and each fails when its anchor is removed (a mode dropped from the core; the
header rule broken); (c) passes. dev-observatory edits are gated by that repository's own suite; this plan adds
the test and changes nothing else there. The default mode's wall clock on a real project is recorded at
Step 15 for that issue, not as a pass or fail.

### Step 12: Operator decision, authority for DELETE of `user-orient`

**Problem:** A hand DELETE of `user-orient` is blocked (see the lifecycle table). Step 13 cannot start without
authority.
**Decided 2026-11-12: option (a).** The operator took the default on item 27 and approved the v3 and v4
split, whose row 5 (catalog cleanup batch) runs under one scoped lifecycle exception for all v3 catalog
changes (split proposal, Q1). The `user-orient` DELETE (Step 13) runs inside that batch. Option (b), waiting for
skill-mesh Steps 111 to 113, is not taken. Step 12 stays as a recorded decision, citing that approval.
**Type:** operator
**Issue:** #237
**Flags:** none
**Produces:** a recorded operator decision only (no code): the scoped lifecycle exception from the batch
approval, naming the base ref, target paths, pre-write hashes and the isolated worktree for the `user-orient`
DELETE (the batch's own record may carry them).
**Done when:** the batch exception's record names `user-orient` among its target paths, with its base ref and
pre-write hashes, in the checkpoint. Fallback only if the batch approval is later withdrawn (item 35): the plan
pauses here, Steps 14 and 15 still run without Step 13, Step 16's "`user-orient` absent" clause is waived
(Step 16 is otherwise unchanged), and Step 3's absorbed view runs while `user-orient` is still installed.

<!-- autofix-applied: 2026-11-12 -->
### Step 13: DELETE `user-orient` and repoint references

**Status:** DONE 2026-11-12 (reviewed APPROVE with one correction round, `<coding-root>/docs/skill-mesh-3-review/builds/user-pm-tail-review.md`). Commit f369f97. Catalog 59 skills (56 portable, 3 provider-native). The request, the pre- and post-greps and one disposition per occurrence are kept outside the repository with the build record. Focused tests: tests/package-integrity and the tests/distributions roster and count selection; no full suite.

**Problem:** `user-orient` retires (F6) after its view is absorbed (Step 3). A catalog DELETE needs every
caller, link, fixture, mapping and ledger effect dispositioned. User-gateway's routes and goblin retirement
belong to decision items 14 and R1 (other lanes) and are not done here, but the user-orient-related repoints
are. The count guards (now 60 records on `origin/main`, `EXPECTED_TOTAL` 60 in `tools/gen_manifest.py`; re-read) have no supported-path update yet, so under a
scoped exception they are edited by hand within its stated scope.
**Type:** code
**Issue:** #238
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (guide section 11 template) with `operation: DELETE`,
`skill_name: user-orient`, and one `reference_dispositions` record for every old-name occurrence the
inspection reports. Expected occurrences from the first grep (re-run, do not trust): `README.md`,
`documentation/skill-reference.md` (line ~60), `_shared/skill-pipeline.md` (lines ~133-135, rewritten to say
user-pm is the status door), `config/skill-manifest.json`, `config/model-mapping.json`,
`skills/inventory.json`, `tests/package-integrity/expected_inventory.json`, `documentation/parity-deltas.md`,
`documentation/codex-parity-delivery-plan.md`, `documentation/native-claude-codex-skill-parity-plan.md`,
`docs/workflows/` card and `workflows.json`, the `user-orient` skill's evals and fixtures, and the
user-orient routing in `user-gateway` and `user-wrap` (if any; user-wrap's orient-lite step is its own text,
not a call). Every surviving mention of `--quick` or orient word budgets is dispositioned as "dropped".
Where an occurrence is also on the `user-gateway` routing item (decision item 14), item 14's lane owns the
edit and this plan records the disposition `owned elsewhere` with that lane named; the build does not stall
on it. Historical records under `.build-step/` are evidence and are not edited. Repoints of user-pm mode references
(plan-trim ~72, task-handoff ~15, user-draft ~23) are needed only if a mode name changed; by Step 3 none does.
**Done when:** the pre-DELETE and post-DELETE greps are both recorded; the post-grep over tracked files
(excluding `archive/` and `.build-step/`) finds zero `user-orient` hits not covered by a recorded
`reference_dispositions` record (item 36; historical documents may keep dispositioned mentions); the skill-count guards in
`tools/gen_manifest.py` are updated and the manifest regenerated; on any failure the lifecycle recovery rule
applies (stop, revert the whole mutation) and a checkpoint is recorded after the regenerate.

### Step 14: Regenerate and run the full gate

**Status:** DONE 2026-11-12 (reviewed APPROVE with one correction round, `<coding-root>/docs/skill-mesh-3-review/builds/user-pm-tail-review.md`). Commit 59ea74d. The gate is substituted under the operator's adopted testing rule (2026-11-12): tests/package-integrity and tests/router ran green on the final head instead of the repo-root full suite. The repo-root `python -m pytest` clause below is therefore not met by design and moves to the one full sweep per release. `gen_release_candidate_report.py` changed only line endings, so there is no content diff.

**Problem:** Generated surfaces (`dist/`, manifest, inventory, workflow card) must be regenerated, and the DONE
gate is the full suite, not a subset (`code-quality.md` gate scope; `skill-mesh/CLAUDE.md`).
**Type:** code
**Issue:** #239
**Flags:** none
**Produces:** regenerated `config/skill-manifest.json`, `tests/package-integrity/expected_inventory.json`,
`skills/inventory.json`, the `user-pm` workflow card (`docs/workflows/`) and `dist/`; a checkpoint naming
every suite that ran, with the wall clock recorded against `documentation/phase-75-baseline.md`.
**Done when:** repo-root `python -m pytest` (no path argument) is green and the checkpoint quotes its real
summary line and the available-memory reading before it (gate-reds on a memory-starved machine);
`python tests/smoke/gen_release_candidate_report.py` produces no diff.

### Step 15: Operator review of one real run

**Problem:** The shape is accepted only by the operator after seeing real output; the new sections cannot be
judged from tests.
**Type:** operator
**Issue:** #240
**Flags:** none
**Produces:** a recorded operator decision only (no code): "accept" or "amend" the shape, and authority (or
not) to install the refreshed profiles on Claude and Codex (release and install need separate authority per
the lifecycle guide).
**Done when:** the operator ran `/user-pm` once on a real project from the worktree profile and the checkpoint
records the output location, the default-mode wall clock (for the dev-observatory issue, not a pass or fail), and
that the run showed the status view, a board with route labels, a readiness section with the three new checks,
a lanes section or its omission line, 3 to 5 anchored ideas labelled unjudged, and one next move. `/user-pm
--json` is run once as well and the output location recorded (no consumer parses it). `/user-pm --lanes` is run
on one project that has a lanes table (you-asked-for-it) and one that has none; the checkpoint records that
the first reviewed the existing split, the second proposed one that keeps the splitting rules, and that
neither run wrote a file.

### Step 16: Install refreshed profiles and verify

**Problem:** Installing binds the new profile and uninstalls the retired `user-orient` through the ledger.
**Type:** code
**Issue:** #241
**Flags:** none
**Produces:** a refreshed install of the Claude and Codex profiles via `tools/install-skill-mesh.ps1`
(only if Step 15 granted install authority) and an inspection record from `tools/inspect-host-install.ps1`.
**Done when:** `tools/inspect-host-install.ps1` shows `user-pm` current and `user-orient` absent on both hosts
(the "absent" clause is waived if Step 13 was skipped, item 35; or the step is marked skipped with the Step 15
decision that withheld authority).

### Step 17: Wait for the `user-dr` first trial and the `user-fermize` Claude adapter

**Problem:** The follow-up binds to two things that are owned elsewhere: a real `user-dr` register (format not
yet exercised by any real project; `skills/user-dr/core.md`, "Show the register" and "Output") and a Claude
adapter for `user-fermize` (Codex-only with no catalog record today; brief section 1.5). Binding to an unproven
format would make it a contract by accident.
**Type:** wait
**Issue:** #242
**Flags:** none
**Produces:** operator-owned: one real `docs/user-dr/<slug>-register.md` from a real project run, the
operator's note "format accepted" or the amended format, and the catalog CREATE of `user-fermize` with a
Claude adapter (another lane, other owner).
**Done when:** the operator records in the checkpoint (a) the real register file's full path and "format
accepted" or the amended format, and (b) that `user-fermize` has a Claude adapter in the catalog and is
installed on Claude. If either never lands, Step 18 is marked skipped and the shipped skill keeps its
no-register line and Codex-window label.

### Step 18: Follow-up UPDATE, register binding and fermize label

**Problem:** Bind the decisions section to the accepted register format and drop the "Codex window" label,
using the paths recorded in Step 17. The workflow plan also needs one line naming user-pm as each project's
read-only view and route entry (item 11); the user-gateway repoint is owned by item 14.
**Type:** code
**Issue:** #243
**Flags:** `--reviewers` default
**Produces:** a small UPDATE of `user-pm` that reads the accepted register (count decided and open items, do
not re-ask decided ones, emit `/user-dr <project> open only` when several are open or a conflict is flagged),
falls back to the existing `--decide` list when no register exists, and drops the "Codex window" label; plus an
edit proposal (not an edit) for the workflow plan's R21-R24 note, since that file is owned by the workspace
Toolkit plan.
**Done when:** the user-pm core matches the register format recorded in Step 17 and the fermize line has no
"Codex window" label; `python -m pytest tests/package-integrity` passes and the full gate (Step 14 form) is
re-run before this step flips DONE.

## Open for redline

Operator-only items. The operator answered the sheet on 2026-11-12; each decided item records its answer.

1. **Authority for DELETE of `user-orient` (Step 12).** Decided 2026-11-12: default taken (item 27): a scoped
   lifecycle exception (recorded base ref, target paths, pre-write hashes, isolated worktree), as for
   code-consigliere and user-dr, rather than wait for Steps 111 to 113. It is the one exception approved for
   the whole v3 catalog batch (split proposal, row 5 and Q1); the DELETE runs in that batch.
2. **Merge of `v3/build-route-rebase` (Step 2).** Decided 2026-11-12: default taken (item 28): merge, with the
   full gate recorded as INCOMPLETE and six suites named. Done: `user-build-route` is on `origin/main` as
   `5924e27`; the heading "Check the route can run" is present.
3. **"Format accepted" for the first real `user-dr` register (Step 17).** Decided 2026-11-12: default taken
   (item 29): accept after one real project run, amend only on concrete defects. The register binding stays a
   follow-up (Step 18); no v4 work is pulled in.
4. **Accept or amend the shape after one real `/user-pm` run (Step 15).** Decided 2026-11-12: default taken
   (item 30): accept if all listed sections show or carry an omission line. (The wall-clock condition was
   dropped with item 37.)
5. **Should dev-observatory move to `--json`?** Decided 2026-11-12: yes in principle, as dev-observatory's own
   later work (item 31, operator's change to the default). Its review page would read the structured output
   instead of showing the text as-is. This plan keeps `--json` documented and tested (Step 10) and files the
   issue; it adds no parser.
6. **Add `--status` and `--improve` flags?** Decided 2026-11-12: default taken (item 32): no. Existing flags
   and the unchanged catalog description keep the Codex headroom, and `_VALID_MODES` would not reach new flags
   in the observatory either way. `--lanes` is the one exception, added by the operator on 2026-11-12 (item 9).
7. **Install authority for the refreshed Claude and Codex profiles (Step 15 to 16).** Decided 2026-11-12:
   default taken (item 33): grant after the real run is accepted.
8. **Passing Notes entry in `advisory-call-convention.md`.** Decided 2026-11-12: default taken (item 34): no
   entry in this plan; follow the eight points by analogy. (The tool has since landed; a convention entry
   would be its own later change.)
9. **Shape of lane planning (Step 8 part B, operator request 2026-11-12).** Default: a two-line lane check in
   the default view plus the `--lanes` topic, which proposes or reviews a split around a `main` lane (item 67)
   and writes nothing. It came
   after the review rounds, so plan-review covers it with the other redline changes before plan-wrap.
