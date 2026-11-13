# Skill Mesh v3 catalog cleanup batch (plan, 2026-11-12)

This is the execution copy for build-phase, copied 2026-11-12 from the operator's planning records in the coding root (`<coding-root>/docs/skill-mesh-3-review/`), where its reviews and the operator's answers live. Step status is recorded here from now on.

Status: reviewed 2026-11-12 (plan-review and plan-wrap applied; findings in
`catalog-cleanup-plan-2026-11-12-review.md`). Planning only; nothing in the catalog has been changed.
Decided 2026-11-12 22:29: the operator's "BQ2 yes" takes the default of every item in "Open for redline" that was
still open (afternoon sheet items 6 to 11 and 34). Build base re-recorded at `4040eed` (see Base).

Path convention: skill-mesh paths are repo-relative. `<coding-root>` is the workspace folder that holds the
skill-mesh checkout and the other projects.

Decision references: "decision item N" means `decision-sheet-2026-11-11.md` (items 13, 14, 15, 50) except where a
step says "morning item N", which means `decision-sheet-2026-11-12-morning.md` (item 17: the Codex headroom upper
limit). "Q1" and "row 5" are in `v3-v4-split-proposal-2026-11-12.md`. "M1", "M2", "R1", "R2", "F1", "F2", "K1" and
"K2" are in `skill-maintenance-actions-2026-11-11.md`. All of these sit in `<coding-root>/docs/skill-mesh-3-review/`.

## What this plan does

One batch of catalog changes, approved 2026-11-12 (split proposal row 5, with Q1), built by hand through
`documentation/skill-catalog-lifecycle.md` (the guide; cited here, not restated). Q1 gave ONE scoped lifecycle
exception for every v3 catalog create, delete and update. The exception carries the code-consigliere and
user-dr safeguards: a recorded base ref, the target paths, pre-write hashes and an isolated worktree.

| Change | Operation | Steps |
|---|---|---|
| Retire `user-lavishify` | DELETE | 2 |
| Move `build-observer` and `observatory-doctor` to dev-observatory | copy out, then DELETE each | 3, 4, 7 |
| Promote `user-fermize` | CREATE (core, Claude, Codex; see open item 2 on the GPT adapter) | 5 |
| Retire `judge-motion` (provider-native) | DELETE | 6 |
| `plan-merge` gains `--trim`; `plan-trim` retires | UPDATE, then DELETE | 8, 13 |
| Fold `user-shakedown` into `user-walkthrough` as `--shakedown` | UPDATE, then DELETE | 9, 12 |
| `user-gateway` repoints its routes (decision item 14) | UPDATE | 11 |
| Retire `goblin-suggest`, `goblin-sweep`, `goblin-do` and their shared contract file | DELETE x3 | 14 |
| `user-project` becomes a script (decision item 15) | script create, then DELETE | 15, 16, 17 |
| `user-afterparty` runs monthly and owns usage telemetry | UPDATE | 18 |

Not in this batch: the tier skills (v4, model-pin path), the execution queue (v4, Forge), GPT adapter removal
(after v3 ships), and the `user-orient` DELETE (see Ordering dependencies; it landed on `v3/main` at `f369f97`,
before this build started).

## Base

- Integration checkout: branch `v3/main`, commit `1ee18b3a4b435e505eafca9e84247170bcda3e1f` at planning time.
  Step 1 re-records the full 40-hex base; every later step records its own base (the worktree head when the step
  starts) in its lifecycle request.
- **Build base (2026-11-12): `v3/main` at `4040eed`**, which equals `origin/main` and already carries the user-pm
  revamp (its Step 5 included) and the `user-orient` DELETE (`f369f97`). The catalog there is 59 skills
  (56 portable, 3 provider-native) and Codex headroom is 551 (re-measured; see Headroom). Every count below that
  says "from the build base" is stated from this commit.
- Catalog at planning time: 60 skills (57 portable, 3 provider-native). At the build base: 59 (56 portable,
  3 provider-native). After this batch: 50 (48 portable, 2 provider-native).
- Worktree: one isolated sibling worktree of the integration checkout on a new branch, created in Step 1 from the
  recorded base. The integration checkout stays read-only for this plan. Fresh worktrees do not inherit
  `node_modules` or a virtualenv: install what the gate needs before the first gate.

## Ordering dependencies (other plans)

| This plan's step | Waits on | Why |
|---|---|---|
| 11 (user-gateway), 14 (goblin) | user-pm revamp plan Step 5 (improvement shortlist) landed on `v3/main` | goblin's "what should I improve?" job moves to `user-pm`; that step also uses the goblin-suggest core's anchor contract as a model, so the goblin core must still exist until Step 5 lands. Step 10 checks it. |
| 13 (plan-trim DELETE) and later; 12 and later from the build base | catalog gate plan Step 8 (the Codex headroom upper limit removed) | see Headroom. Step 10 checks it. |
| 5 (user-fermize) | nothing | It must land before user-pm Steps 17 and 18, which need the Claude adapter. |
| user-pm Step 13 (`user-orient` DELETE) | this plan's Step 11 | Step 11 repoints every `user-orient` mention in user-gateway (decision item 14 owns that file), so Step 13 of the user-pm plan finds none there. The DELETE itself stays in the user-pm plan, after its core rewrite. It landed first, at `f369f97`; user-gateway carried no `user-orient` mention at that base, so Step 11 finds none to repoint. |
| Both plans | each other, on generated files | Both regenerate `config/skill-manifest.json`, `skills/inventory.json`, `tests/package-integrity/expected_inventory.json` and count pins. Never run in one worktree at once. Whichever lands second rebases and regenerates with `python tools/gen_manifest.py`, never hand-merges. |

## Headroom: the Codex catalog budget

`tests/package-integrity/test_codex_budgets.py` today requires `400 < headroom < 900` over the 57 codex-eligible
records. Measured on the base, headroom is **421** (total 7,579 against the 8,000 floor). Re-measured on the build
base `4040eed` (56 records, `user-orient` gone): total 7,449, headroom **551**; the per-skill sizes below are
unchanged there. Measured per-skill sizes
(name, description and path, as the test serializes them):

| Skill | Chars | Effect |
|---|---|---|
| user-lavishify | 138 | retire, frees |
| build-observer | 135 | move out, frees |
| observatory-doctor | 147 | move out, frees |
| user-shakedown | 129 | fold, frees |
| plan-trim | 125 | fold, frees |
| goblin-suggest / goblin-sweep / goblin-do | 131 / 133 / 126 | retire, frees 390 |
| user-project | 122 | script, frees |
| judge-motion | 0 | provider-native, not in the codex-eligible set |
| user-fermize | about 140 with a one-line manifest description | create, costs (Step 5 measures it) |

The "about 190 per create" figure in earlier notes is high: the catalog mean is 133. The prepared packet's long
description serializes to 308, so the manifest description must be a short one-liner like its neighbours (open
item 3).

Floor (`headroom > 400`): the only step that lowers headroom is the create. Step 5 runs after two retirements,
so headroom is about 694 before it and about 554 after, well clear of 400. The floor never fails. (From the build
base: 824 before it and about 686 after.)

Predicted headroom after each step (re-measured and recorded in every step's Done-when; these are estimates):

| After step | 1 | 2 | 4 | 5 | 6 | 7 | 8-11 | 12 | 13 | 14 | 16 | 18-19 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Headroom | 421 | ~559 | ~694 | ~554 | ~554 | ~701 | ~701 | ~830 | ~955 | ~1345 | ~1467 | ~1467 |
| From the build base `4040eed` | 551 | ~689 | ~824 | ~686 | ~686 | ~833 | ~833 | ~962 | ~1087 | ~1477 | ~1599 | ~1599 |

From the build base the first predicted breach of `headroom < 900` moves from Step 13 to Step 12. Step 10 still
comes before it, so the ordering below is unchanged; only the step named as the first breach changes.

Upper limit (`headroom < 900`): this batch frees about 1,046 net, so it cannot stay inside the band; no create is
left to offset it. The first predicted breach is Step 13 (Step 12 from the build base). Catalog gate plan Step 8 (morning item 17) removes the
upper limit. This plan does **not** edit the guard; that plan owns it (one owner). Step 10 is a wait step placed
before the first breach: it passes when the upper limit is gone. If this plan runs before that plan lands, steps
1 to 9 stay inside the band and the build halts at Step 10 until it does (open item 4). Step 1 records whether the
limit is already gone; if so, Step 10 passes at once on resume.

## Gates (which gate applies where)

- **Catalog gate** (the catalog gate plan): if it has landed, it is the gate at every step that edits skill
  content, and its selector chooses what runs. Step 1 records which case holds (check for
  `tests/gate/select_gate.py`, which the catalog gate plan's Step 3 adds; it is absent on `v3/main` at planning
  time). Its selector returns `full` for any path under `tools/`, `_shared/` or `runtime/`, any edit to
  `tests/gate-classes.json`, and any newly added test file, so most steps of this batch will run the full suite
  even after it lands; the selector, not this plan, decides, and a `full` answer is never waived.
- **Else the full repo-root `python -m pytest`** is the done gate. It takes hours. Per decision item 50 the agent
  asks the operator before starting it and never waives it itself. To keep the build unattended, the default is the
  operator's recorded pre-approval, confirmed at redline (open item 1, decided 2026-11-12 by "BQ2 yes"): each step is gated by the item 50 scoped
  set (`tests/package-integrity`, `tests/distributions/test_distributions.py`, `tests/smoke`, `tests/release`,
  `tests/router`, `tests/telemetry`, the three root-only roots `_shared/`, `skill-iterate/scripts/` and
  `skill-eval-setup/scripts/`, and `tools/release.ps1`'s staged package checks), the step is recorded with the
  suites that ran named and the full gate marked INCOMPLETE, and the full repo-root run happens once, at Step 19.
  If the operator declines the pre-approval, every code step runs the full suite.
- Steps 1, 3, 17 and 20 touch no skill-mesh catalog bytes (3 and 17 are in other repos), so they take only the
  gate of the repository they change.
- `tests/fixtures/representative_skills.json` names `plan-init`, `review-gauntlet`, `build-phase` and
  `session-wrap`. No batch skill is representative, but Step 14 edits `session-wrap`'s core (a goblin-do pointer),
  which moves the recorded hashes. Step 14 regenerates `documentation/release-candidate-report.md` in the same
  change, before its gate (`python tests/smoke/gen_release_candidate_report.py`). Every other step must not touch
  those four cores; Step 19 regenerates the report once more and asserts no diff.

## Per-step method (applies to every catalog step: Steps 2, 4 to 9, 11 to 16 and 18; not Steps 1, 3, 10, 17, 19, 20)

1. Check the worktree is clean at the target paths and record: `base_ref` (full 40-hex), the target path set and
   each target's pre-write SHA-256, compared with Step 1's record. A target already changed stops the step
   before any write.
2. Normalize the request with the section 11 template of the guide. Provide `resource_paths` for every package
   file added or removed (evals, workflow scripts, scripts, fixtures); the exception covers the resource-plan stop.
3. Run the reference report: every case-sensitive old-name token at kebab-name boundaries in tracked and
   untracked-not-ignored text files, with `git grep`; a binary hit stops for manual review. Record
   the before and after counts per file. Disposition each occurrence exactly once (guide section 8):
   `must-update` for canonical bytes, runtime, config, generated files, current operator documentation, tests and
   fixtures; `historical-preserve` only for named immutable records (completed plans, parity and closure records,
   review evidence under `documentation/findings/`, `archive/v1/`), listed by path, line, column, pre-mutation
   `before_sha256` and rationale. `archive/v1/` is an inert zip plus manifest: preserve whole files by hash.
   Issue and PR text is evidence, never authority.
4. Edit canonical surfaces only. Never edit `dist/`, `release-stage/`, a consumer discovery root, or a legacy
   top-level package. Legacy root folders (`tier-offload/`, `tier-escalate/` samples) that name a retired skill
   are historical-preserve, listed by hash, never edited.
5. Update the count guard `EXPECTED_TOTAL, EXPECTED_PORTABLE, EXPECTED_NATIVE` in `tools/gen_manifest.py` (60, 57, 3
   at the base, near line 427, and the comment near line 82) for any step that changes a count. Then regenerate
   with `python tools/gen_manifest.py` (hermetic), re-render workflow cards for the changed skills
   (`tools/render-workflow-cards.py`), build all three profiles with `tools/build-distributions.ps1`, then the
   step's gate.
6. On any failure after the first write: stop with `CATALOG_MUTATION_INCOMPLETE`, print the changed paths and
   the failed gate, and leave the worktree as it is. No reset, clean, checkout, commit or push by the
   mutation. The reviewer's fix is a new commit.
7. One reviewable unit per skill, one commit per step, staged by path.

---

### Step 1: Record the scoped exception, create the isolated worktree, measure

**Status:** DONE 2026-11-13. records only (`<coding-root>/docs/skill-mesh-3-review/builds/cleanup/`). Steps 1 to 5 reviewed APPROVE with one correction round (`<coding-root>/docs/skill-mesh-3-review/builds/cleanup-1-review.md`); focused tests plus the per-change pack under the adopted testing rule.

**Problem:** Q1 approved one scoped exception for the whole batch. The guide requires the base ref, target paths and
pre-write hashes recorded before the first write, and nothing yet records them. The headroom estimates above come
from a planning-time read and must be re-measured on the real base.
**Type:** code
**Issue:** #257
**Flags:** `--reviewers` default
**Produces:**
- A sibling worktree on a new branch from `v3/main`, and a record file in
  `<coding-root>/docs/skill-mesh-3-review/builds/catalog-cleanup/` (kept outside the skill-mesh repository on
  purpose, so the retired names it lists never appear in the tree the absence checks scan):
  `exception-record.md` and `exception-record.json`, containing the full base ref, the exception's scope (the ten
  catalog operations above, the two UPDATEs, the resource plan, the count-guard edits, and the guide and pin-test
  edits Steps 2 to 16 name; plus the `user-orient` DELETE, which the user-pm plan's Step 13 executes under this
  same exception, so its Step 12 can cite this record), and per skill the target path set with a SHA-256 for every
  file, over: each skill folder involved, including `skills/user-orient/`; the shared files cited (`_shared/goblin-second-brain.md`, `_shared/intake-engine.md`,
  `_shared/shakedown-engine.md`, `_shared/skill-pipeline.md`, `_shared/routing-web-*.svg`, the ten files that use
  the user-project pin); `config/skill-manifest.json`, `config/model-mapping.json`, `skills/inventory.json`,
  `tests/package-integrity/expected_inventory.json`, `tools/gen_manifest.py`, `tools/build-distributions.ps1`,
  `tools/install-skill-mesh.ps1`, `tools/gen_skill_tree.py`; the tests that pin counts or names
  (`tests/package-integrity/test_codex_budgets.py`, `test_manifest_contract.py`, `test_skill_catalog_lifecycle.py`,
  `test_link_resolution.py`, `link_baseline.json`, `test_v2_authoring_contract.py`,
  `test_v2_orientation_contract.py`, `tests/distributions/test_distributions.py`,
  `tests/distributions/test_build_observer_resources.py`, `tests/calibration/phase-3-4-ports.json`);
  `README.md`, `CLAUDE.md`, `plan.md`, and the current-documentation pages that count skills or name them.
- A baseline reference report for every name in the batch (before any edit), a baseline of headroom
  (`_catalog_estimate()` total, headroom, per-skill sizes), and the per-step headroom table above re-computed.
- Which of the files in the target set are tracked in the mesh: at planning time only `user-gateway` has tracked
  `evals/`, `build-observer` has only `scaffold_portfolio.py`, `judge-motion` has its runtime package, and no
  goblin, `plan-trim`, `plan-merge`, `user-shakedown` or `user-walkthrough` skill has tracked `evals/` or
  `*.workflow.js` files (the manifest's `support_assets` entries name legacy coding-root paths only). Later steps
  list `resource_paths` from this record, never from the manifest.
- Recorded answers to four questions: which gate applies (catalog gate landed or not); whether the
  `headroom < 900` assertion still exists; whether user-pm Step 5 has landed; whether `user-dr` and
  `user-build-route` are in the tree (they are at planning time).
- The `user-fermize` packet checked against the base: its `create-request.json` `base_ref` is stale by design and
  is replaced; the packet's four files are re-hashed against its `preparation-check.json`.
**Done when:** the worktree exists and is clean at the recorded base; the record's hashes were produced by a script
that is re-run and returns an identical file; the record names the exception's scope in full and the operator's Q1
approval; nothing under the skill-mesh checkout other than the new worktree changed (verified by a clean
`git status` there); the headroom number is recorded and equals the planning-time 421 or the difference is
explained. No catalog gate runs here (no catalog bytes change).

### Step 2: DELETE `user-lavishify`

**Status:** DONE 2026-11-13. commit b090907. Steps 1 to 5 reviewed APPROVE with one correction round (`<coding-root>/docs/skill-mesh-3-review/builds/cleanup-1-review.md`); focused tests plus the per-change pack under the adopted testing rule.

**Problem:** The operator never used it and does not like it (decision log round 2). It is the smallest delete and
frees headroom ahead of the create, so it goes first.
**Type:** code
**Issue:** #258
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (`operation: DELETE`, `skill_name: user-lavishify`, one disposition per reported
occurrence), then: the skill folder removed; its rows removed from `tools/gen_manifest.py` constants (portable
roster, codex roster, descriptions, capability and local-capable lists) and `config/model-mapping.json`; regenerated
manifest, inventory and expected inventory; its workflow card removed; `skills/repo-update/core.md` (the tour
paragraph that says lavishify stays on-demand) rewritten to drop the name; count pins and count prose in
`README.md`, `CLAUDE.md`, `documentation/skill-reference.md`, `documentation/architecture.md`, the providers
pages and the tests re-pinned deliberately, not loosened. Expected occurrence files (re-run, do not trust):
`README.md`, `documentation/skill-reference.md`, `skills/repo-update/core.md`, `config/*`, generated files,
`tests/distributions/test_distributions.py`, `tests/package-integrity/test_codex_budgets.py`,
`tests/package-integrity/test_v2_authoring_contract.py`, `tests/calibration/phase-3-4-ports.json`. Historical
plans and closure records (`documentation/parity-deltas.md`, `documentation/v2-packet-closure.md`,
`documentation/codex-parity-delivery-plan.md`, `documentation/native-claude-codex-skill-parity-plan.md`) and
`archive/v1/*` are historical-preserve by explicit listing.
**Done when:** pre- and post-DELETE reports are recorded; the post report over tracked and untracked-not-ignored
text files, excluding the explicitly preserved occurrences (whose hashes are unchanged), finds zero
`user-lavishify`; manifest counts read 59 total, 56 portable (58 and 55 from the build base); all three profiles build; headroom is recorded and
is above 400 (predicted ~559; ~689 from the build base); the step's gate (see Gates) is green and named. The installed ledger effect (stale
cleanup removing the host profile) is left to Step 20.

### Step 3: Copy `build-observer` and `observatory-doctor` into dev-observatory (other repository)

**Status:** DONE 2026-11-13. coding-root commit 484f68c0 (local). Steps 1 to 5 reviewed APPROVE with one correction round (`<coding-root>/docs/skill-mesh-3-review/builds/cleanup-1-review.md`); focused tests plus the per-change pack under the adopted testing rule.

**Problem:** Both skills move to dev-observatory as project-local skills (maintenance M1, M2). The copy must land
and be committed there before the mesh deletes anything, or the move leaves a gap. This is not a catalog
operation on the mesh. `dev-observatory/` has no nested `.git` (its git top level is the coding-root repository,
checked at review time and re-checked here), so the commit lands in the coding-root repository: anchor git there
and use path-scoped `git add dev-observatory/...` only, never `git add -A`.
**Type:** code
**Issue:** #259
**Flags:** `--reviewers` default (gate: dev-observatory's own test command; the mesh gate does not apply)
**Produces:** in `<coding-root>/dev-observatory/.claude/skills/`: `build-observer/` (the skill assembled from the
mesh core and Claude adapter, plus `scaffold_portfolio.py` from the mesh and `sample-dry-run.md` and
`test_scaffold_portfolio.py` from the legacy coding-root skill folder `<coding-root>/.claude/skills/build-observer/`,
because the mesh does not track those two) and `observatory-doctor/` (assembled the same way); a note in dev-observatory's own docs saying these two now
live there. Both keep their current behavior; the only edits are path references that assumed a mesh install.
**Done when:** each skill runs its documented dry-run from the dev-observatory checkout; the moved
`test_scaffold_portfolio.py` passes there; the commit (in the coding-root repository, path-scoped to `dev-observatory/`) is recorded by hash;
the copied bytes differ from the mesh sources only where the step's notes say.

### Step 4: DELETE `build-observer` from the mesh

**Status:** DONE 2026-11-13. commit 291fe96. Steps 1 to 5 reviewed APPROVE with one correction round (`<coding-root>/docs/skill-mesh-3-review/builds/cleanup-1-review.md`); focused tests plus the per-change pack under the adopted testing rule.

**Problem:** After Step 3, the mesh copy is retired. It carries a reviewed packaging exception for its validator
script, special-cased in the build tooling, the guide and the tests.
**Type:** code
**Issue:** #260
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (`DELETE`, with `resource_paths` listing the one tracked resource,
`skills/build-observer/scaffold_portfolio.py`), then: the skill folder removed; the `build-observer` branch
removed from `tools/build-distributions.ps1` (resource list and emitter) and the resource declaration from
`tools/gen_manifest.py`; `tests/distributions/test_build_observer_resources.py` removed and its fixture lines in
`tests/distributions/legacy_install_fixtures.py` and `test_distributions.py` dispositioned; the `build-observer`
rows and the "reviewed packaging exception: the build-observer validator" paragraph in
`documentation/skill-catalog-lifecycle.md` (table row near line 127, paragraph near line 162) rewritten to say the
exception ended, with the matching pin in `tests/package-integrity/test_skill_catalog_lifecycle.py` and the
link baseline entries updated in the same change; `config/model-mapping.json` row removed; generated files and
count prose regenerated and re-pinned. The guide edit removes a statement about a retired skill only and
weakens no gate; the reviewer is told to check exactly that.
**Done when:** pre- and post-DELETE reports recorded; zero `build-observer` in the post report outside listed
historical-preserve occurrences; the three profiles build without the build-observer resource step; counts read
58 total, 55 portable (57 and 54 from the build base); headroom recorded (predicted ~694; ~824 from the build
base) and above 400; gate named and green.

### Step 5: CREATE `user-fermize`

**Status:** DONE 2026-11-13. commit 8b9b239. Steps 1 to 5 reviewed APPROVE with one correction round (`<coding-root>/docs/skill-mesh-3-review/builds/cleanup-1-review.md`); focused tests plus the per-change pack under the adopted testing rule.

**Problem:** `user-fermize` exists only as a personal Codex skill (19 uses in 6 weeks). The user-pm revamp needs it
on Claude. A prepared packet lives in `<coding-root>/docs/investigations/gates-and-drift/catalog-preparation/`
(core, three adapters, create request, model-mapping row, preparation check); it was checked at an older base and
is re-checked here, not trusted.
**Type:** code
**Issue:** #261
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (`CREATE`, `capabilities: ["filesystem"]`, `resource_paths: []`,
`reference_dispositions: []`, a one-line manifest `description`, fresh `base_ref`); preconditions checked first:
name absent at the base (no `CREATE_COLLISION`), the personal skill's bytes still match the packet's recorded
SHA-256, no dirty target path; then `skills/user-fermize/core.md` and `providers/claude.md`, `providers/codex.md`
(and `providers/gpt.md` per open item 2); the `config/model-mapping.json` row from the packet; the name added to
the portable and codex rosters, the description and the capability classification in `tools/gen_manifest.py`;
regenerated manifest, inventory and expected inventory; the count pins, count prose and roster lists in
`tests/package-integrity/test_codex_budgets.py` and the distribution tests updated; its workflow card added.
Because every other skill's adapters are validated by integration tests through their callers, add one test that
proves the Claude and Codex profiles load the core and carry the read-only, advice-only contract; there is no
production caller yet (user-pm Steps 17 and 18 add it), so no caller test applies and the reviewer is told so.
**Done when:** the post-create existence check passes (present in the worktree, absent at the base); the three
profiles build; the manifest description's serialized size and the new headroom are recorded and headroom is
above 400 (predicted ~554, a drop of about 140; ~686 from the build base); counts read 58 total, 55 portable
from the build base; the existing personal install file is untouched (the installer's
foreign-file handling is Step 20's job); the step's gate is green and named. From this step until the user-pm plan's
Step 18 (which drops the label), `skills/user-pm/core.md` still says user-fermize has no Claude adapter and labels its
deep-dive line "Run in: a Codex window"; that file belongs to the user-pm plan and this step does not edit it.

### Step 6: DELETE `judge-motion` (provider-native)

**Problem:** Retired by decision (2 uses in 6 weeks; motion checking now lives in the projects' own skills). It is
provider-native, so the guide's `PROVIDER_NATIVE_REVIEW_REQUIRED` stop applies to any request; the Q1 approval
names it in the batch and the exception record (Step 1) names it explicitly (open item 6). Its runtime package
(Playwright script folder, fixtures, tests, `package.json`, `package-lock.json`) is the largest resource removal
in the batch.
**Type:** code
**Issue:** #262
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (`DELETE`, native identity, `resource_paths` listing every file under
`skills/judge-motion/`); the skill folder removed; the `judge-motion` branch of `tools/build-distributions.ps1`
(runtime closure list, resource emitter), the three `package*.json` and fixture paths in
`tools/install-skill-mesh.ps1`, the reason string in `tools/gen_skill_tree.py` line near 88, the
`tools/gen_manifest.py` native roster, resources and description, and `config/model-mapping.json` removed or
updated; the asserts on `skills/judge-motion/package.json` and `scripts/` in
`tests/package-integrity/test_manifest_contract.py` and the link baseline removed; the guide's `judge-motion`
paragraph, table row and its native-skills list (and the "60 skills: 57 portable and 3 provider-native" sentence,
now 2 native) updated together with the pins in `tests/package-integrity/test_skill_catalog_lifecycle.py`, and
`CLAUDE.md`, `_shared/skill-pipeline.md`, `plan.md` (the status index: each mention dispositioned by line) and
`documentation/native3-provider-native-rebuild-plan.md` as current documentation (the rebuild
plan is historical-preserve where it records past authorization). Callers repointed: `skills/judge-ui/core.md`
(the motion-routing line and the sibling section), `skills/review-uat/core.md`, `skills/user-uat/core.md`
(the Visual-tier qualifier and sibling section) and `skills/user-uat/providers/codex.md` and `gpt.md`: transition
steps are reported as manual-check steps, not silently dropped (open item 10).
**Done when:** pre- and post-DELETE reports recorded; zero `judge-motion` outside listed historical-preserve
occurrences and the accepted exception below; the builder emits nothing for it, and the installer carries only
the ledger-removal paths named in the exception; counts read 58 total, 56 portable,
2 native (57, 55 and 2 from the build base); headroom unchanged at about 554 (~686 from the build base) (not codex-eligible); the three profiles build; gate named and green.
**Accepted exception (review `cleanup-2-review.md` S1, 2026-11-13):** the three markerless JSON paths of the retired
package in `tools/install-skill-mesh.ps1` (`MARKERLESS_JSON_OWNED_RELS`) and the `RETIRED_JSON_PACKAGE` constant in
`tests/distributions/test_distributions.py` stay, recorded as disposition class `retained-installed-ledger-effect`.
Reason: an install made before the retirement records those files in its ledger, and JSON cannot carry the
provenance marker, so without the exact paths a normal install refuses the whole run instead of removing them
(evidence: `<coding-root>/docs/skill-mesh-3-review/builds/cleanup/step6/stale-refusal-demo.txt`). Removal is a later,
separate decision, once no consumer home still records them.

### Step 7: DELETE `observatory-doctor` from the mesh

**Problem:** After Step 3 it lives in dev-observatory.
**Type:** code
**Issue:** #263
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (`DELETE`, no resources); folder, constants, mapping row, generated files,
workflow card and count pins updated as in Step 2; current documentation (`README.md`,
`documentation/skill-reference.md`, `documentation/migration.md`, providers pages) updated; the old plans and
records historical-preserve by listing.
**Done when:** pre- and post-reports recorded; zero `observatory-doctor` outside the preserved list; counts read
57 total, 55 portable (56 and 54 from the build base); headroom recorded (predicted ~701; ~833 from the build
base); gate named and green.

### Step 8: UPDATE `plan-merge` (add `--trim`)

**Problem:** `plan-trim` folds into `plan-merge` (decision item 13): one skill, a `--trim` mode, user-pm's board
routes plan clean-up there. The mode must exist, with the trim contract intact, before `plan-trim` is deleted.
**Type:** code
**Issue:** #264
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (`UPDATE`, `skill_name: plan-merge`); `skills/plan-merge/core.md` gains a
`--trim [<plan-path>]` mode that carries `skills/plan-trim/core.md`'s contract as written (investigate first,
propose, an operator-only go-ahead, `git rm` only, one path-scoped commit, step-deletion disclosure, the report
and `Next:` line) in the same shape as the merge mode's invocation section; the three adapters changed only for
host binding (`plan-merge` carries no `--trim` text in its core or adapters at the base: a grep of
`skills/plan-merge` for `trim` finds nothing, so the mode and its adapter lines are all new); the description in
`tools/gen_manifest.py` stays within its current length so headroom does not move. No `plan-trim` or `plan-merge`
evals are tracked in the mesh (Step 1's record), so there is nothing to fold and no `resource_paths`; carrying the
legacy coding-root evals is open item 13. A differential check: the old `plan-trim` core
and the new mode are compared clause by clause by the reviewer, and no gate the old core defines is weakened.
**Done when:** a table in the step's checkpoint maps every `plan-trim` contract clause to its `plan-merge --trim`
clause; `plan-merge`'s merge mode is unchanged (diff shows additions only to the invocation and a new section);
the profiles build; headroom unchanged; gate named and green. `plan-trim` still exists and works.

### Step 9: UPDATE `user-walkthrough` (add `--shakedown`)

**Problem:** `user-shakedown` folds into `user-walkthrough` as a flag (decision 11/11, F2). Both already share
`_shared/shakedown-engine.md`, the same ledger file and a hand-off between them. The flag must land before the delete.
**Type:** code
**Issue:** #265
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (`UPDATE`, `skill_name: user-walkthrough`); the core gains `--shakedown`, which
runs the engine's autonomous mode (the agent closes the ledger to zero open items) with `user-shakedown`'s
contract (its argument and ledger-slug rule, stop conditions, `/goal` string, report) preserved, replacing the
current "hands a half-filled ledger to `/user-shakedown`" text; the adapters (`providers/claude.md`, `codex.md`,
`gpt.md`) changed only for host binding. No `user-walkthrough` or `user-shakedown` evals are tracked in the mesh (Step 1's record), so no
evals are added or folded (open item 13). `_shared/shakedown-engine.md` is kept and is not renamed.
**Done when:** a clause map from `user-shakedown`'s core to the flag is recorded and no gate is weakened; no
`user-walkthrough` text still tells the reader to type `/user-shakedown` (this step reaches absence in its own
file only; the others are Step 12's); the profiles build; headroom unchanged; gate named and green.

### Step 10: Wait for the two outside prerequisites

**Problem:** Two things outside this plan must be true before the remaining steps. (a) The user-pm revamp plan's
Step 5 has landed on `v3/main`, so goblin's job has its new home. (b) The catalog gate plan's Step 8 has removed
the `headroom < 900` upper limit, because Step 13 is the first predicted breach. This plan never edits that guard.
**Type:** wait
**Issue:** #266
**Flags:** none (halting is the point of a wait step)
**Produces:** a checkpoint recording, with the date, the base the worktree is rebased onto, and the result of two
predicates, both read from `v3/main`: (a) `grep -c "single pass, unjudged" skills/user-pm/core.md` reports at
least 1 (the label user-pm Step 5's Done-when requires); (b) the upper limit is gone: `grep -nE "assert headroom <"
tests/package-integrity/test_codex_budgets.py` finds no line, or finds one whose bound exceeds this plan's
predicted peak headroom of 1,467 (1,599 from the build base `4040eed`; a "raise" outcome of catalog gate Step 8). A mention of the old bound in a comment
does not count. Resume with `--resume 11` after rebasing the isolated worktree onto `v3/main` and re-measuring
headroom.
**Done when:** both predicates hold; the worktree is rebased and regenerated (`python tools/gen_manifest.py`
produces no diff beyond the rebase), the Step 1 record is re-hashed for any target path the rebase moved, and the
new base ref is recorded. If `tests/gate-classes.json` arrived with the rebase, every test file this plan added
before the rebase (Steps 5 and 15) has a class entry and every one it removed (Step 4) has none, and the
class-map test passes; the same duty applies to the test files Steps 15 and 18 add after it.

### Step 11: UPDATE `user-gateway` (repoint its routes)

**Problem:** Decision item 14: keep `user-gateway` for people who do not know skill names, and repoint it. Its
"ideas" route points at `/goblin-suggest`; its "do it" route and the "voice a task, then run it" lines point at
`/goblin-suggest --small` and `/goblin-do`; it names `plan-trim`, `user-shakedown` and `user-orient`. This is the
single place all of that changes, so each later DELETE finds no gateway occurrence. Its evals and golden files
cite the old names in many files.
**Type:** code
**Issue:** #267
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (`UPDATE`, `skill_name: user-gateway`); core routes: ideas to `user-pm`;
"do it" to `user-pm`, which routes by `user-build-route`'s rules, with no queue wording because the queue is v4
(open item 5); finished intake handed to `user-pm`; `plan-trim` to `plan-merge --trim`; `user-shakedown` to
`user-walkthrough --shakedown`; every `user-orient` mention to `user-pm` (decision item 14's lane owns the
gateway file; the DELETE stays in the user-pm plan); the routing diagram files `_shared/routing-web-light.svg` and
`routing-web-dark.svg` regenerated to match (they name goblin-do, user-shakedown and plan-trim); the evals
(`evals.json`, `test_scenarios.json`, and the golden files that name an old skill) edited so each case still
tests the same behavior against the new target, with the case count unchanged or any removal listed with a
reason; the adapters changed only for host binding.
**Done when:** the gateway's own text and evals contain none of `goblin-suggest`, `goblin-do`, `goblin-sweep`,
`plan-trim`, `user-shakedown`, `user-orient` (grep recorded); each repointed route targets a skill that exists in
the worktree now (checked by a script, not by reading); no routing gate weakens (the reviewer is given the old
and new route tables side by side); the profiles build; headroom unchanged; gate named and green.

### Step 12: DELETE `user-shakedown`

**Problem:** Folded in Step 9, repointed in Step 11. Remaining callers: `skills/review-uat/core.md`,
`skills/user-uat/core.md`, `skills/user-walkthrough/` (core and Codex adapter prose), `_shared/skill-pipeline.md`,
`_shared/intake-engine.md` (no change expected), docs, tests and the calibration port list.
**Type:** code
**Issue:** #268
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (`DELETE`, no `resource_paths`: no `evals/` are tracked); folder, constants, mapping row, generated files, workflow card and count pins updated; callers repointed
to `user-walkthrough --shakedown`; `_shared/shakedown-engine.md` stays and its header text (names the two skills)
is updated; `tests/calibration/phase-3-4-ports.json`, `tests/package-integrity/test_skill_tree.py` and
`tools/gen_skill_tree.py` references dispositioned; user-project-pin reader text in other cores is not touched
here (Step 16).
**Done when:** pre- and post-reports recorded; zero `user-shakedown` outside the preserved list; counts read
56 total, 54 portable (55 and 53 from the build base); headroom recorded (predicted ~830, still under the old 900
limit; ~962 from the build base, over it, which Step 10 verified is gone); gate named and green.

### Step 13: DELETE `plan-trim` (and update `user-afterparty`'s chain)

**Problem:** Folded in Step 8; the gateway repoint is done (Step 11). `user-afterparty` chains `plan-trim`
(its hygiene list), and `plan-feature` and `_shared/skill-pipeline.md` name it. This is the first predicted
headroom-over-900 step (from the build base it is the second; Step 12 is the first), which is why Step 10 waits.
**Type:** code
**Issue:** #269
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (`DELETE`, no `resource_paths`: no `evals/` are tracked); folder,
constants, mapping row, generated files, workflow card, count pins; `skills/user-afterparty/core.md`'s chain and
`skills/plan-feature/core.md`, `_shared/skill-pipeline.md`, `_shared/routing-web-*.svg` repointed to
`plan-merge --trim`; `user-afterparty`'s change here is limited to replacing the chain entry (the monthly
cadence and telemetry are Step 18); `tier-escalate/` and `tier-offload/` legacy sample files that name it are
historical-preserve by listing.
**Done when:** pre- and post-reports recorded; zero `plan-trim` outside the preserved list; counts read
55 total, 53 portable (54 and 52 from the build base); headroom recorded (predicted ~955; ~1087 from the build
base) and above 400; if above 900 the guard must already be
the one the catalog gate plan left, which Step 10 verified; gate named and green.

### Step 14: DELETE `goblin-suggest`, `goblin-sweep`, `goblin-do`

**Problem:** Retired (maintenance R1). Their cores describe a removed execute path; "what should I improve?" moved
to `user-pm` (Step 5 of that plan, checked in Step 10), and the gateway was repointed in Step 11. This is one
retirement of one three-skill family and the three skills reference each other, so a single reviewable unit is
cleaner than three half-referencing ones. Callers: `skills/plan-feature/core.md` (near line 19),
`skills/session-wrap/core.md` (near line 596), `_shared/intake-engine.md` (near lines 273 and 304),
`_shared/skill-pipeline.md` (lines near 32, 76 and 151), `_shared/routing-web-*.svg`, `README.md`,
`documentation/architecture.md`, providers pages, `documentation/skill-reference.md`, tests
(`tests/package-integrity/test_cutover_handoff.py`, `tests/router/test_no_claude_dependency.py`,
`tests/distributions/legacy_install_fixtures.py` also name them at the base), and the legacy
`tier-offload/` sample files (historical-preserve).
**Type:** code
**Issue:** #270
**Flags:** `--reviewers` default
**Produces:** three lifecycle requests in one commit (each `DELETE`; no `resource_paths`: the goblin skills have
no tracked `evals/` or `*.workflow.js` files); `_shared/goblin-second-brain.md` removed after a grep shows no remaining
reader (the same occurrence report covers it); the three folders, constants, mapping rows, generated files,
workflow cards and count pins; callers repointed: "do the next small thing" now says to hand the item to
`user-pm` (and, in session-wrap, the plan or issue path it already names); `tests/package-integrity/
test_codex_capability_claims_honesty.py`, `test_manifest_contract.py` and the distribution tests that name the
goblin skills re-pinned; in `tests/package-integrity/test_codex_budgets.py`, `goblin-sweep` leaves
`STEP10_PROMOTIONS` and the fixed-cost pin (`assert fixed == 306`, set by Step 4 over the six promotions left then)
is re-derived over the five that remain (`fixed == 258`), with the comment above it updated; the same name leaves
`STEP10_PROMOTED_SKILLS` in `tests/distributions/test_distributions.py`. **Session-wrap is a representative skill**, so
`python tests/smoke/gen_release_candidate_report.py` runs in this step, and the regenerated
`documentation/release-candidate-report.md` is part of the change.
**Done when:** pre- and post-reports recorded for all four names (three skills and the shared file); zero
occurrences outside the preserved list; the release-candidate report test is green (it sits in the smoke suite
and is not collected by a package-integrity-only run, so run it explicitly); `goblin-sweep` is absent from both
Step 10 promotion rosters and the fixed-cost pin equals the recomputed sum over the remaining names; counts read 52 total, 50 portable
(plus 2 native; 51 and 49 from the build base); headroom recorded (predicted ~1345; ~1477 from the build base); gate named and green.

### Step 15: Create the `user-project` script (runtime, with its own test)

**Problem:** `user-project` stops being a skill (decision item 15). It is a deterministic PowerShell procedure
that writes a session pin; ten skills read the pin and several call it. The script must exist, be tested and be
wired before the skill goes, and must be listed in the manifest so it cannot quietly disappear. Location note
(measured at review time): `runtime/` is NOT emitted into the host profiles (`tools/build-distributions.ps1`
emits no `runtime/` file, and no installed skill cites `runtime/skill-router.ps1`), so a script there would be
unreachable from an installed caller. `_shared/` IS emitted (`dist/<p>/_shared/<leaf>`, harvested from each
`../_shared/<leaf>` reference, scripts such as `build_step_verdict.py` included) and already has a global
support asset entry, so the script lives at `_shared/user-project.ps1`, callers cite it as `../_shared/user-project.ps1`
and no new manifest field is invented.
**Type:** code
**Issue:** #271
**Flags:** `--reviewers` default
**Produces:** `_shared/user-project.ps1` (Windows PowerShell 5.1, ASCII only, no BOM; see the location note
below) implementing SET, SHOW and
CLEAR exactly as `skills/user-project/core.md` specifies: marker-based coding-root discovery, registry slug-or-path
validation with a fail-loud unknown-name message, the single-line pin format
`**Active project:** <slug> (<abs-repo-path>)`, the `[third-party]` suffix, and the identity rule: the session id
is a required parameter the caller's wrapper binds (Claude: the scratchpad parent directory name; Codex and
GPT: only an id that wrapper binds), never the freshest session file, never `current.md`, never another host's
variable; with no id, SET and CLEAR write nothing and print the identity-unavailable line. It takes no
interactive input. The `_shared/` global-support-asset entry already covers it, so the change in
`tools/gen_manifest.py` is only a note if the emitter's allow-list needs the leaf named; regenerate the manifest;
a test (`_shared/test_user_project.py`, beside the other `_shared/` tests, which the repo-root run collects) that
runs the script against a scratch coding-root
fixture and asserts the pin lines, the unknown-name failure, the identity-unavailable outputs and that nothing is
written without an id; a red-on-garbage anchor (a script that skips the id check must fail the test). Step 15
begins by proving the emitter ships a `.ps1` leaf from `_shared/` into all three profiles (build, then list
`dist/<p>/_shared/user-project.ps1`); if the emitter rejects it, the step makes the smallest emitter change that
carries it, as part of this step, rather than halting (open item 8 is decided). The existing
`skills/user-project/` stays until Step 16.
**Done when:** the script's outputs match the skill core's documented outputs for SET, SHOW, CLEAR and the three
failure modes (the table is in the checkpoint); the test is green and fails on the garbage anchor; the emitted
tree of all three profiles carries `_shared/user-project.ps1` at its documented path; the profiles build; gate
named and green. Headroom unchanged.

### Step 16: DELETE `user-project` and repoint its callers

**Problem:** After Step 15, the skill is deleted and its ten reading skills and the shared task-state schema point
at the script. Callers: `lesson-harvest`, `plan-expedite` (core and Codex adapter), `repo-init`, `repo-sync`,
`repo-update`, `repo-wrap` (core, Claude and Codex adapters), `task-handoff`, `user-afterparty`, `user-walkthrough`
(each core), `_shared/task-state-schema.md`, `_shared/skill-pipeline.md`, docs and tests
(`tests/package-integrity/test_v2_orientation_contract.py` reads the skill's core and Codex adapter, and must be
rewritten to read the script; `test_skill_tree.py` and the distribution tests name it). The pin file format and
the task-state field do not change.
**Type:** code
**Issue:** #272
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (`DELETE`); folder, constants, mapping row, generated files, workflow card, count
pins; callers changed from "run `/user-project`" to "run `../_shared/user-project.ps1` with the wrapper-bound session id" (a
mechanical edit per file, listed in one table in the checkpoint); no caller's gate weakens (each caller's
advisory-and-fail-open behavior on an unset or unavailable pin is untouched).
**Done when:** pre- and post-reports recorded; zero `user-project` as a slash name in skill bytes outside the
preserved list (the pin's own field name `Active project` is not the old name and is expected to remain); the
rewritten orientation test is green and red-on-garbage; counts read 51 total, 49 portable, 2 native (50, 48 and 2 from the build base);
headroom recorded (predicted ~1467; ~1599 from the build base); gate named and green.

### Step 17: Point coding-root references at the script (other repository)

**Problem:** The workspace working-directory rule and its reference say "use `/user-project <name>` to pin the
active project", and the statusline and hooks may name the slash command. They must name the script, with the
same wiring promise item 15 gave. This edits the coding-root repository, not skill-mesh, so anchor git to that
repository and add by path.
**Type:** code
**Issue:** #273
**Flags:** `--reviewers` default (gate: the coding-root repository's own checks)
**Produces:** edits in `<coding-root>/.claude/rules/working-directory.md`,
`<coding-root>/.claude/references/working-directory.md` and any other coding-root file the grep finds, naming the
script's installed path and invocation; the occurrence grep recorded before and after over the coding-root
repository (tracked files); no edit to historical lessons or memory files.
**Done when:** grep for the slash form finds no live instruction (historical records excepted, listed); a dry
invocation of the script from the coding-root works and prints the SHOW output; the commit is recorded by hash in
the coding-root repository.

### Step 18: UPDATE `user-afterparty` (monthly cadence and usage telemetry)

**Problem:** Decided 11/11 (K1, K2): afterparty runs monthly and owns the monthly usage snapshot, because Claude
keeps only about six weeks of transcripts so a monthly snapshot is the only lasting record. The survey scripts
(`scan_usage.py`, `aggregate.py` in the survey folder of `<coding-root>/docs/skill-mesh-3-review/
usage-survey-2026-11-11/`) already work by hand; they read transcripts from the user's home through
`os.path.expanduser("~")`, so no absolute path is embedded. `aggregate.py` is not location-free today: it derives
the repository as `../../../skill-mesh` from its own folder to read `config/skill-manifest.json`, and it reads
`events.jsonl` and writes `usage.json` beside itself. Packaged in a skill folder it would write into the installed
tree, so this step makes the manifest path, the events file and the output folder explicit parameters.
**Type:** code
**Issue:** #274
**Flags:** `--reviewers` default
**Produces:** a lifecycle request (`UPDATE`, `skill_name: user-afterparty`, `resource_paths` listing the files
to be added: `skills/user-afterparty/scripts/scan_usage.py`, `aggregate.py` and their test); the two scripts packaged as the
skill's support assets (declared in `tools/gen_manifest.py`), run with `python -I`; a test that runs both against a
small synthetic transcript fixture and asserts the columns and counts, and fails on a garbage fixture; the core
gains a telemetry section: run the survey, write a dated snapshot, show what changed since the last one, and print
a one-line nudge when the last snapshot is older than the cadence; the skill's description may change only within
its current serialized length (headroom must not move); the chain is otherwise as Step 13 left it (tier skills stay
until v4). Snapshots are private data, so they go to a gitignored `docs/user-afterparty/` folder in the coding-root
repository (the survey covers every project's transcripts, so one portfolio-wide location, not the repository the
run happens in), never into the skill-mesh repository (open item 9). Scheduling the
monthly run is the operator's; this step builds no scheduler.
**Done when:** the script test is green and red on the garbage fixture; a dry run on the real transcripts writes a
snapshot outside the skill-mesh tree and the numbers match the survey's published table within the noted
exclusions; core and adapters carry the telemetry section; profiles build with the new assets present; headroom
unchanged; gate named and green.

### Step 19: Regenerate, build and run the done gate

**Problem:** Every step regenerated for itself, but the batch needs one clean end-to-end proof: no drift between
canonical bytes and generated files, count pins and prose agree everywhere, the release-candidate report matches,
and the full gate has run once.
**Type:** code
**Issue:** #275
**Flags:** `--reviewers` default
**Produces:** a final `python tools/gen_manifest.py` (no diff expected; any diff is a defect in an earlier step);
`python tests/smoke/gen_release_candidate_report.py` (no diff expected after Step 14); a build of all three profiles;
the count check (51 total, 49 portable, 2 native, or 50 and 48 if the user-pm plan has landed Step 13 first; it
has, so from the build base the check is 50, 48 and 2);
a final repo-wide absence report for all retired names (the ten skills, the goblin shared file) with only the
listed historical-preserve occurrences remaining, whose hashes are re-verified unchanged; the final headroom
recorded; the done gate. At this step: **the catalog gate if it has landed, run in addition to the full gate if it
returns `full`**; otherwise **the full repo-root `python -m pytest`**, run once, detached, with its exit code
written to a sentinel file so a returned agent cannot report a gate it did not see. Before starting the full
run, check available memory (below 2 GB free reds random subprocess tests) and tell the operator it takes hours.
**Done when:** the final collected, passed, failed and skipped counts are recorded with the date; failed is zero
or each failure is attributed at the parent commit and fixed; the gate's report names the suites that ran; headroom
is above 400; no listed step is still marked INCOMPLETE. If this step reports a failure after the first write,
the recovery rule applies.

### Step 20: Install and verify the refreshed profiles

**Problem:** Installed must equal released for the changes to exist for the operator. This needs install authority
(a real consumer home), which a build step does not have. The installer removes retired skills by its ownership
ledger; nothing is hand-deleted. `user-fermize` already exists as a personal, unledgered Codex skill and will
collide with the generated one.
**Type:** operator
**Issue:** #276
**Flags:** none (operator step; produces no code)
**Produces:** the operator installs the Claude and Codex profiles from the merged result, in this order and with the
exact commands below, run separately and in the operator's window. The installer has no `-WhatIf` option
(afternoon sheet item 34, decided 2026-11-12 by "BQ2 yes"), so the first run of each profile is a normal install
without `-Force`: it refuses every foreign-file collision, lists each one, and changes nothing while any remains.

```
powershell -File tools/install-skill-mesh.ps1 -Provider claude -Home <install-home>
```

Read its collision list. Then the same command for `-Provider codex` with that profile's home. Foreign-file
collisions are inspected one by one; the personal `user-fermize` file is preserved and adopted through the
installer's backup procedure (never `-Force` across unrelated collisions, never a hand-edited ledger), and the
install is re-run without `-Force` once the list is empty. The operator then runs `tools/inspect-host-install.ps1`
for both profiles. Expected on the Claude home: the normal, non-`-Force` install removes the retired `judge-motion`
package's ledger-owned files, including its three markerless JSON files (Step 6's accepted exception), and leaves
the unowned `node_modules/`, `.judge-motion/` and `.pytest_cache/` in that folder. The leftover folder holds no
`SKILL.md`, so the skill is not discoverable; it is not a failed removal.
**Done when:** the inspection reports the installed catalog equals the released one; none of the ten retired
names, nor `user-orient` if its plan has landed, is discoverable in either host root; `user-fermize` loads from the
catalog on both hosts and the personal copy is retired as an authoring source; the two moved skills are
discoverable from the dev-observatory project and from nowhere else; a fresh Claude session and a fresh Codex
session both start without a skill-list truncation warning; the operator records the result with the date.

---

## Open for redline

Each item has a default the plan follows if you do not decide. Review 2026-11-12 triaged the list: items marked
"Decided 2026-11-12" are settled by an existing operator answer or rule and are kept only as a record. Items 1, 3,
9, 12 and 13, the last ones open, were decided at their defaults by the operator's "BQ2 yes" (2026-11-12 22:29,
afternoon sheet items 6 to 10); nothing in this list is open.

1. **Decided 2026-11-12 (BQ2 yes, default).** **Per-step gate.** The full repo-root suite takes hours and item 50 says the agent asks first. Default: you
   pre-approve the item 50 scoped set for Steps 2 to 18 (suites named in each checkpoint, full gate INCOMPLETE until
   Step 19), and the full suite runs once at Step 19. Changes if: you want the full suite at every step (about
   a dozen runs), or the catalog gate has landed and its selector chooses.
2. **Decided 2026-11-12 (by split proposal row 8, README Operator answers "the GPT provider per D5", and guide section 4: GPT adapters ship one last time in v3 under the deprecation note, and `gpt.md` is mandatory for a portable create).** **`user-fermize` GPT adapter.** You asked for core plus Claude and Codex. The guide (section 4) makes `gpt.md`
   mandatory for a portable create, v3 still ships the GPT profile under its deprecation note, and the prepared
   packet carries one. Default: include a thin `providers/gpt.md`, removed with the GPT removal pass after v3.
   Changes if: you want the guide's rule amended first, which is a plan change.
3. **Decided 2026-11-12 (BQ2 yes, default).** **`user-fermize` manifest description.** The packet's request description serializes to 308 characters
   against a catalog mean of 133. Default: a one-line manifest description of about 90 characters (name 12 plus
   path 36 plus 90 gives the 140 this plan's headroom table assumes; at 110 characters the cost is about 158 and
   every later headroom figure drops by about 18, still above 400). The long text stays in the core. Changes if: you want the longer text and a trim elsewhere.
4. **Decided 2026-11-12 (by morning item 17, default taken: remove the upper bound inside the catalog gate plan's Step 8; and 11/11 item 51, default: settle the guard's upper limit before the retirement batch).** **Upper limit not yet lifted when the build reaches Step 10.** Default: the build halts at the wait step until
   catalog gate plan Step 8 lands; this plan never edits the guard. Changes if: you would rather have this plan
   change the limit itself; that splits ownership with the catalog gate plan and I advise against it.
5. **Decided 2026-11-12 (by decision item 14 plus split proposal rows 5 and 6 and its v4 list, which place the execution queue in v4/Forge).** **user-gateway "do it" route.** Decision item 14 says "user-pm and the queue", but the queue is v4. Default:
   "do it" goes to `user-pm` (which routes through `user-build-route`); queue wording is added when the queue
   exists.
6. **Decided 2026-11-12 (by Q1, approved in the day-window record, plus README Operator answers "Retire ... judge-motion" and maintenance R2; the split proposal's row 5 names it).** **`judge-motion` is provider-native.** The guide says no request field grants native authority. Default: the
   Q1 approval plus the exception record naming `judge-motion` explicitly is the authority, and the reviewer
   checks that the record, not the request, carries it. Changes if: you want a one-line statement from you added
   to the record.
7. **Decided 2026-11-12 (by maintenance M1 and M2: moved as project-local skills; Codex parity stays with dev-observatory's owner).** **Form of the moved skills in dev-observatory.** Default: Claude-only project-local skills assembled from the
   mesh core and Claude adapter, with the validator script and its test; Codex parity is left to
   dev-observatory's owner.
8. **Decided 2026-11-12 (by decision item 15, approved 11/11: a script the same callers run, wired in, listed and tested; the location follows from the review's measurement that `runtime/` is not emitted but `_shared/` is).** **Where callers find the `user-project` script once installed.** Default: `_shared/user-project.ps1`, cited by callers as `../_shared/user-project.ps1`.
9. **Decided 2026-11-12 (BQ2 yes, default).** **Telemetry snapshots and the monthly trigger.** Default: dated snapshots in a gitignored `docs/user-afterparty/`
   folder in the coding-root repository; a nudge in afterparty's report when the last snapshot is over 35
   days old; scheduling the run is yours. Changes if: you want a scheduled routine built (a separate plan).
10. **Decided 2026-11-12 (by maintenance R2: the operator chose deprecation over a `judge-ui --motion` mode; README Operator answers keep `judge-ui` as is).** **Motion transitions after `judge-motion` goes.** Default: `user-uat` and `judge-ui` report transition-shaped
    steps as manual-check steps and say motion checks live in each project's own skills (as in
    you-asked-for-it). Changes if: you want `judge-ui` to gain a `--motion` mode, which you declined 11/11.
11. **Decided 2026-11-12 (by lifecycle guide section 8, which owns `historical-preserve`, and Q1's safeguards).** **Old plans and the v1 archive.** Default: every occurrence in completed plans, parity and closure records,
    review evidence and `archive/v1/` is `historical-preserve`, listed by path, line, column and hash; none is
    edited.
12. **Decided 2026-11-12 (BQ2 yes, default).** **Ordering of the two plans' shared generated files.** Default: this plan and the user-pm plan never share a
    worktree; whichever finishes second rebases and regenerates. Changes if: you would rather one plan be
    gated to start only after the other lands.
13. **Decided 2026-11-12 (BQ2 yes, default).** **Legacy evals for the folded and retired skills.** The manifest names `evals/` folders for `plan-trim`,
    `plan-merge`, `user-shakedown` and `user-walkthrough`, but none is tracked in the mesh (they exist only under
    the coding-root's legacy `.claude/skills/`). Default: carry none; Steps 8 and 9 rely on the clause-by-clause
    contract maps instead. Changes if: you want those eval cases added as new tracked resources to `plan-merge` and
    `user-walkthrough`, which adds a resource plan to Steps 8 and 9.
