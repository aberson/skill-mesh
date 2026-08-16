# Codex parity delivery plan (Phase CP)

- **Written:** 2026-08-16
- **Status:** READY — plan-review PASS, plan-redline accepted (P1–P9, D-CP1–D-CP15), plan-wrap READY, all 2026-08-16; next: /repo-sync
- **Issue phase label:** `Phase CP Step N:` (fresh namespace; the Goal NP parity plan's Steps 1–41 were never repo-synced, so no collisions; next issues mint at #117+)
- **Supersedes:** the Goal NP two-approval publication path for delivery sequencing. The
  detailed parity plan (`documentation/native-claude-codex-skill-parity-plan.md`, parity branch)
  remains the reference for Codex format/placement research; its execution contract is
  superseded by this plan per the four operator ratifications of 2026-08-16 (recorded in §6).

## 1. What This Feature Does

Proposal: https://claude.ai/code/artifact/a32fd48f-6f3b-4a49-84c8-111898fdac89
(standalone copy: `documentation/codex-parity-delivery-proposal.html`)

Deliver every portable skill-mesh skill as a generated, self-contained **Codex-native**
package discoverable from `$CODEX_EFFECTIVE_HOME\.agents\skills`, from the same authored
`core.md` per skill that already serves the `claude` and `gpt` providers — making skill usage
robust across a second model family, with pipelines that behave *materially similarly* (close,
not byte-exact; differences are recorded, not gated). Delivery is **additive and cohort-based**:
skills become usable on Codex at the first milestone rather than after an exhaustive
qualification program. It also closes out the two dirty worktrees left by the Goal NP
recovery effort (Publication 8 candidate; Step-4 installer-hardening WIP) so the repo has one
clean line of history before new work begins. It also delivers the utility-wiring outcome:
the seven dev-observatory portfolio utilities (heads-up, tripwire, same-page, changed-check,
paper-trail, find-again, mesh-lens) wired into the canonical pipeline skill cores as
fail-open advisory calls, with the wiring visible through dev-observatory as part of UAT.

## 2. Existing Context

All citations are from producing files, verified 2026-08-16 by read-only survey.

- **Two-provider architecture already exists and is the pattern to extend.** 50 canonical
  skills under `skills/<name>/` (47 portable with `core.md` + `providers/{claude,gpt}.md`;
  3 Claude-native with `providers/claude.md` only: claude-oauth-auth, context-slim,
  judge-motion). Inventory is owned by `config/skill-manifest.json` (schema_version 1,
  50 entries, `providers` dict currently `{claude, gpt}`).
- **Deterministic generation:** `tools/build-distributions.ps1 -Provider claude|gpt|both`
  generates `dist/<provider>/<skill>/{SKILL.md, core.md}` + `dist/<provider>/_shared/` from
  the manifest; canonical files never rewritten; GENERATED provenance header on every emitted
  file; byte-identical reruns; UTF-8 no BOM, LF (header, lines 1–70).
- **Install/transaction machinery exists:** `tools/install-skill-mesh.ps1` (transactional,
  ledger-scoped destructive authority via `<Home>/.skill-mesh-install.json`; claude →
  `<Home>/.claude/skills/<skill>/`, gpt → `<Home>/.github/skills/<skill>/`),
  `tools/migrate-legacy-install.ps1` (journaled reversible cutover),
  `tools/skill-mesh-discovery.ps1` (single owner of the provider→discovery-root map;
  currently recognizes `.agents/skills` as a Copilot *active-alternate* root that skill-mesh
  never installs into, lines 39–56), `tools/skill-mesh-transaction.ps1` (shared transaction
  engine).
- **Zero Codex product code exists today:** no `providers/codex.md` anywhere; no codex hits
  in `skills/ tools/ config/ src/`. The Codex surface is a clean delta.
- **Codex format/placement research (parity branch,
  `documentation/native-claude-codex-skill-parity-plan.md`):** Codex's documented unit is a
  skill directory containing `SKILL.md` (YAML frontmatter between `---` delimiters) plus
  co-located assets (lines 98, 121–124); placement `$CODEX_EFFECTIVE_HOME\.agents\skills\<name>`
  (lines 16, 35, 139); `$CODEX_EFFECTIVE_HOME` resolved once, HOME and USERPROFILE must agree
  on Windows, disagreement stops before mutation (lines 147–150); metadata serialization cap
  7,500 UTF-8 chars per skill, whole-catalog initial-list budget = 2% of model context or
  8,000 chars when unknown (lines 175–181).
- **Related parked plan (no conflict):** `documentation/provider-expansion-plan.md` is
  **Gemini + local lanes** (Phase 8, Steps 51–61; issues #70–#82 parked as history) — a
  different provider set. It stays PARKED; this plan's Step 3 provider surface is what that
  plan would later build on. Fresh `Phase CP` issue labels avoid its sibling-plan
  step-collision warning.
- **What is proven vs. not:** `codex exec` + `--output-schema` (draft 2020-12) works — the
  Goal A cross-family probe performed a real Codex review detecting 3/3 seeded defects
  (`plan.md` Goal A journal; cross-family-report.md lines 17–19, 32, 36). **Codex skill
  *discovery* from `.agents/skills` is UNVERIFIED on this machine** — the cross-family runs
  deliberately disabled skills; the only on-machine `.agents/skills` discovery proof is
  Copilot CLI v1.0.77 (`documentation/providers/gpt.md` lines 24–35). This plan front-loads
  that check (M1).
- **Repo state:** linear history `main@50fb9a3 → plan/native-codex-skill-parity +7 →
  docs/goal-np-journey +2`; recovery/goala-* branches at-or-behind main. Two dirty
  worktrees: the parity worktree holds the 9-file uncommitted Publication 8 candidate
  (verified byte-identical to its 2026-08-16 worklog snapshot); the main worktree holds the
  4-file Step-4 installer-hardening WIP (+1,843/−277, issue #116, one unidentified failing
  test in `tests/distributions/test_distributions.py` per
  `step-4-checkpoint-2026-08-13.md` lines 73–102). No CI; the DONE gate is repo-root
  `python -m pytest` with no path argument (CLAUDE.md:31–89 — a path argument misses 3
  root-only test roots).
- **Operator ratifications (2026-08-16):** (a) Terra executor amendment reverted — Claude-led
  implementation; (b) Publication 8 closed unapproved, launcher parked; (c) the exhaustive
  113-cell matrix downgraded from gate to backlog — representative smokes + a parity delta
  log are the gates; (d) additive/destructive track separation — additive installs under
  scoped approvals; destructive legacy retirement/cutover is OUT of this plan's scope.

## 3. Scope

**In scope**
- Stage 0 close-out: commit + merge the Publication 8 candidate as historical record with a
  course-change note; land the 4 maintenance fixes; finish the Step-4 installer hardening
  (#116); unify history on `main`.
- `codex` as a third provider: manifest schema, generation, frontmatter contract, discovery
  root, installer support, inspect support.
- `providers/codex.md` for all 47 portable skills, delivered in cohorts (pilot 5 →
  pipeline family → build/review family → remainder).
- Bring-up verification in a real Codex session (M1), an end-to-end workflow parity pass
  (M2), and a parity delta log as the running record of Claude↔Codex behavioral differences.
- Promotion of the 7 workspace custom skills (build-observer, citation-distill,
  citation-review, citation-sweep, citation-triage, goblin-sweep, repo-wrap) into the
  canonical catalog with all three providers.
- Utility advisory-call wiring: reconcile the dev-side utility-hookup output (its Steps 1–3
  edits to installed cores) into the **canonical** `skills/<skill>/core.md` files per the
  advisory-call convention, regenerate all providers, and make the wiring visible through
  dev-observatory as an explicit UAT gate (M4). Live-home reinstall of the wired profiles
  is operator-driven (M4), never automated.

**Out of scope**
- Destructive legacy retirement, live Claude-home cutover, junction retargeting, retiring
  the Copilot-managed profile (future plan with its own heavy approval packet).
- The Terra bootstrap launcher (`tools/run-goal-np-terra-bootstrap.ps1`) — parked, not
  deleted; not invoked by any step.
- The exhaustive per-skill × per-host qualification matrix (backlog, not gate).
- skill-ablation and the neutral evaluation substrate (D09 — the old Goal NP decision that
  ablation work waits for a neutral evaluation substrate; both stay deferred).
- Any new always-on/scheduled behavior: **none exists and none is added.** Skills are
  invoked interactively; generation and install are one-shot CLI runs that complete and
  return. The autonomous-behavior observation trigger does not fire for this plan.

## 4. Impact Analysis

| File | Change Type | Reason | Verified |
|---|---|---|---|
| `config/skill-manifest.json` | extend | `providers.codex` entry; per-skill `providers.codex` paths; counts block gains codex tallies | survey read: top-level keys incl. `providers` (2 keys), `counts` (7), 50 skill entries; consumers grep'd: `gen_manifest.py`, `build-distributions.ps1`, `frontmatter_contract.py`, manifest tests |
| `tools/gen_manifest.py` | modify | hermetic regen must emit/validate codex provider paths | named in CLAUDE.md:31–89 as manifest owner; re-grep at build time per key-shape rule |
| `tools/build-distributions.ps1` | extend | `-Provider codex` in ValidateSet; codex SKILL.md template/emission rules; provider-native skills stay absent from dist/codex | header lines 64–70 param block read; `-Provider claude\|gpt\|both` confirmed current |
| `tests/package-integrity/frontmatter_contract.py` | extend | add `CODEX_KEYS` (today only `GPT_KEYS={name,description}`, `CLAUDE_KEYS` +`user-invocable/argument`, lines 131–141) | file read at cited lines; no codex key-set exists |
| `tools/skill-mesh-discovery.ps1` | modify | codex → `.agents/skills` as an *installable* root; today `.agents/skills` is Copilot active-alternate, never installed into (lines 39–56) | file read at cited lines; consumers: install/inspect/migrate + `tests/distributions` discovery tests — step must grep all before landing |
| `tools/install-skill-mesh.ps1` | extend | `-Provider codex` install path + ledger semantics identical to claude/gpt | lines 9–12, 21, 34–48, 103 read (provider map, ledger, uninstall gating); file is also Step-4 WIP — extension lands AFTER Step 2 commits it |
| `tools/inspect-host-install.ps1` | extend | report codex root state + AGENTS.md evidence class | lines 12, 484 read (instruction-file reporting) |
| `tests/distributions/*` | extend | provider-set assumptions (two-provider tallies, dist tree shape, discovery-root tests) must learn codex | suite = 269 test fns; exact call sites enumerated in-step per grep-all-consumers rule |
| `tests/package-integrity/expected_inventory.json` | regenerate + commit | pinned inventory generated by `tools/gen_manifest.py` (gen_manifest.py:1, :582); manifest schema change invalidates it | grep'd: `test_manifest_contract.py:4-9` asserts committed pin against manifest |
| `tests/package-integrity/test_manifest_contract.py` | extend | asserts manifest ↔ pinned inventory ↔ documented command contract; learns the codex provider | file read: header lines 4–9 |
| `skills/inventory.json` + `tools/gen_skill_tree.py` | regenerate / verify | `gen_skill_tree.py:81` owns `skills/inventory.json` enumerating per-skill files; new `providers/codex.md` files change it | grep'd: gen_skill_tree.py:16, :81, :639 |
| `tools/release.ps1` | extend | `-Provider` defaults `'both'` (release.ps1:102) and forwards to the staged build (:213); must include codex or redefine 'both'→'all' | file grep'd at cited lines |
| `config/model-mapping.json` (+ `config/model-tier-map.json`) | verify/extend | top-level keys include `providers` + `skills` (dict read); codex provider entry likely needed for tier resolution — confirm at Step 4 | `python -c json.load` structure check; exact need is TBD at build (read producing file in-step) |
| `README.md` | modify | Providers & installation section (README.md:459–472) says "47 of 50 skills run on both hosts" + two-row provider table; codex row + counts update | grep'd at cited lines |
| `CLAUDE.md` | modify | Commands section (CLAUDE.md:64–72) lists build/install commands per provider; codex variants added | grep'd at cited lines |
| `plan.md` (parity branch → main) | modify | Progress rows: `Goal NP plan → CLOSED UNAPPROVED (course change 2026-08-16)`, `Goal NP implementation → SUPERSEDED — see codex-parity-delivery-plan.md`; journal entry | committed structure verified: Progress table at line 61, rows at 63–67 incl. `Provider expansion \| PARKED` at line 66 — **that exact row string is load-bearing** (`tests/package-integrity/test_recovery_plan_hygiene.py:72`) and must be preserved |
| `experiments/recovery/cross-family-fixture/{create_fixture.py, probe.py}`, `tests/experiments/test_cross_family_probe.py`, `tests/distributions/test_path_choke_point.py` | commit as-is | the 4 maintenance fixes (CRLF/LF canonicalization, sealed-inventory identity, production-route regression, launcher path-choke exemption) — content already reviewed across P8 generations A–E + independent audit | current bytes byte-verified against the 2026-08-16 worklog snapshot (all SHA-256 match) |
| `tools/run-goal-np-terra-bootstrap.ps1` | commit as-is, park | P8 candidate content becomes historical record; never invoked by this plan | hash-verified; path-choke exemption is keyed to this exact path (`test_path_choke_point.py:169–177`) — do not rename |
| 4 Step-4 WIP files (`install-skill-mesh.ps1`, `migrate-legacy-install.ps1`, `tests/distributions/test_distributions.py`, `tests/distributions/test_legacy_migration.py`) | finish + commit | write-ahead authority hardening, closes #116; one failing test to identify and fix | hash-verified recovery copies at `Recovery/skill-mesh-step-4-20260814T021546Z-73e9e215` (manifest.json, base 111fc2ba); live diff M on all four in main worktree |
| `skills/{judge-ui, plan-feature, plan-init, plan-review, repo-update, review-deep, review-gauntlet, review-proof, skill-evolve, skill-iterate, tier-escalate, tier-offload, user-afterparty, user-gateway, user-uat, user-wrap}/core.md` | extend | utility advisory-call blocks per the convention; authoritative hookup map read from the owning docs at Step 11 | working set = the 16 modified installed cores in the dev root (`git status`, dev repo); authoritative sources: `dev/.claude/references/advisory-call-convention.md` (ONE owner) + the utility-hookup owning plan — read at build time |
| dev repo (read/coordinate only): `.claude/observatory/registry.toml`, `dev-observatory/*` | verify/coordinate | wiring visibility surface for M4; dev-observatory Steps 32–42 dirty + Step 43 planned are owned by ITS plan — this plan coordinates, never rebuilds | cross-repo boundary per working-directory rule; Step 12 reads the observatory producing sources to determine the visibility mechanism |

## 5. New Components

- `skills/<skill>/providers/codex.md` × 47 (+7 promoted): Codex provider wrapper per skill —
  same role as the existing `providers/gpt.md`: load `core.md` in full, map host
  abstractions, preserve core gates verbatim. Codex-specific mappings: no Claude
  Agent/Workflow tools → use the core's documented single-context fallback; no Artifact
  tool → file outputs; session/scratchpad identity per Codex conventions.
- Codex SKILL.md generation template + emission rules inside `build-distributions.ps1`
  (frontmatter: `name`, `description` — the `CODEX_KEYS` contract; generated SKILL.md
  requires the co-located `core.md`).
- `tools/probe-codex-skills.ps1`: read-only-by-default bring-up probe — resolves
  `$CODEX_EFFECTIVE_HOME` with the HOME/USERPROFILE agreement check, reports the
  `.agents/skills` tree and ledger state; `-Home <path>` override for disposable-home
  rehearsal.
- `documentation/parity-deltas.md`: the parity delta log. One row per observed Claude↔Codex
  behavioral difference: `skill | delta | severity | disposition (accept/fix/wontfix)`.
  M-step verdicts (`M1: PASS/FAIL`) are recorded here and gate the conditional cohort steps.
- New tests: codex profile determinism + tree shape; `CODEX_KEYS` frontmatter contract;
  per-skill 7,500-char metadata cap; whole-catalog initial-list budget estimate vs the
  8,000-char floor; temp-home install/inspect/uninstall round-trip.
- Promoted skills: `skills/{build-observer, citation-distill, citation-review,
  citation-sweep, citation-triage, goblin-sweep, repo-wrap}/` with `core.md` + three
  provider files each.

## 6. Design Decisions

**D-CP1 — Codex is a third provider on the existing rails, not a new system.** The
manifest/generator/installer/discovery machinery is extended exactly the way `gpt` exists
today. Alternative rejected: a separate codex-specific generator (duplicates the
one-source-of-truth manifest and the deterministic-emission guarantees for no benefit).

**D-CP2 — Additive-only writes; the destructive track is out of scope.** Automated steps
write only to the repo, `dist/`, and disposable temp homes. The **only** step that touches a
real consumer home is M1 (operator-driven), and running M1 *is* the scoped approval for that
first write, per ratification (d). No step modifies `.claude/skills`, `.github/skills`,
junction targets, or legacy roots.

**D-CP3 — Publication 8 is committed as-is, unapproved, as historical record** (ratification
b). Its 9-file content already absorbed five review generations + an independent boundary
audit; re-reviewing it would restart the treadmill this course change ends. The build-step
committing it runs `--reviewers auto` (gates only) for exactly this reason; the course-change
note added to `plan.md` is the only new prose.

**D-CP4 — Close-not-exact parity, recorded not gated.** Per the product charter
("materially consistent … visible differences allowed") and ratification (c): representative
smokes + the parity delta log are the gates; the exhaustive matrix is backlog. A delta only
blocks when the operator marks it `fix` in triage.

**D-CP5 — Cohort rollout gated on M1 evidence.** Codex skill discovery is unverified
(Existing Context). Authoring 47 provider files before one skill is proven discoverable
would be waste; cohorts B–D are `Type: conditional` on `M1: PASS` in the delta log.

**D-CP6 — Shared `.agents/skills` root: decide after evidence.** `.agents/skills` is also
Copilot's recognized active-alternate root. M1 records whether Copilot sees codex packages;
the policy (accept vs guard) is decided in M1 triage and recorded in the delta log,
not pre-built.

**D-CP7 — Version stance: parity targets the *installed* Codex CLI.** The 0.147.0 pin +
binary hash belonged to the parked launcher's frozen-host identity. Live skill usage runs
whatever Codex the operator has installed; the delta log records the CLI version per M-step
run. Format assumptions (frontmatter, placement, budgets) came from 0.147.0-pinned research
and get re-verified by M1 on the installed version.

**D-CP8 — Step-4 hardening lands before installer extension** (Step 2 before Step 5), so the
codex install path is built on the write-ahead-hardened installer rather than creating a
merge headache across the same 1,765-line file.

**D-CP13 — Utility wiring lives in canonical cores and fails open everywhere.** Advisory
calls land in `skills/<skill>/core.md` (so all three providers generate them), following the
8-point convention owned by `dev/.claude/references/advisory-call-convention.md`: advisory,
fails open, NEVER blocks; tools root from `DEV_UTILITIES_ROOT`; absent → silent skip. On a
Codex host without the utilities the calls vanish harmlessly — no host-specific forks.
Alternative rejected: keeping the wiring as hand-edits to installed copies (generated-file
headers say those are overwritten on every reinstall; the drift is exactly what Step 11
reconciles upstream).

**D-CP14 — Live-home reinstall is operator-gated (M4), consistent with D-CP2.** Rolling the
wired cores out over the existing live install overwrites the drifted installed copies —
correct once Step 11 has adopted the drift upstream, but it is a real consumer-home write,
so it happens in M4 by your hand, on the Step-2-hardened installer, ledger-verified.

**D-CP15 — Observatory visibility is UAT evidence, not new machinery.** M4's check is that
the wiring is visible through dev-observatory's existing/planned surfaces (mesh-lens,
registry hookups). dev-observatory's own dirty Steps 32–42 and planned Step 43 belong to its
plan; this plan adds a coordination note, not observatory features.

## 7. Build Steps

Three-pass structure: **pass 1** = Steps 1–5, then M1; **pass 2** = Steps 6–8 (conditions
read M1's verdict), then M2; **pass 3** = Steps 9–12 (Step 9's condition reads M2's
findings; Steps 11–12 are unconditional — utility wiring is Claude/Copilot value regardless
of the codex verdict), then M3 + M4. Run `/build-phase` per pass; conditional steps skip
harmlessly when their evidence file is absent.

### Automated Steps
(These run unattended via /build-phase.)

<!-- autofix-applied: 2026-08-16 -->
### Step 1: Close out Goal NP and unify history
- **Problem:** Two dirty worktrees block clean work. In the parity worktree
  (`%LOCALAPPDATA%\SkillMesh\Worktrees\native-codex-skill-parity-plan`, branch
  `plan/native-codex-skill-parity`, HEAD 40d671d): first re-verify the 10-file candidate
  hashes against the snapshot table in the goal-np worklog
  (`goal-np-publication-journey/documentation/goal-np-publication-journey.md` §"Current
  uncommitted Publication 8 snapshot"); preserve the 9-file delta as a patch file outside
  all worktrees; then commit in two scoped commits — (1) the 4 maintenance fixes
  (create_fixture.py, probe.py, test_cross_family_probe.py, test_path_choke_point.py),
  (2) the P8 docs + launcher as closure record, adding the course-change note to `plan.md`
  (Progress rows: `Goal NP plan | CLOSED UNAPPROVED (course change 2026-08-16)`;
  `Goal NP implementation | SUPERSEDED — documentation/codex-parity-delivery-plan.md`;
  preserve the exact `Provider expansion | PARKED` row — it is asserted by
  `test_recovery_plan_hygiene.py:72`; journal entry naming the four ratifications). Commit
  the untracked worklog on `docs/goal-np-journey`. Merge
  `plan/native-codex-skill-parity` into `main` (history is linear; use `git -C` with
  absolute paths per worktree; no rebase/history rewrite — ever). Work
  direct-in-tree across the existing worktrees; do NOT create a new isolation worktree
  (this step IS git choreography), and use path-scoped `git add` only.
- **Type:** code
- **Issue:** #118
- **Flags:** --reviewers auto
- **Files:** plan.md, documentation/native-claude-codex-skill-parity-plan.md,
  documentation/native-claude-codex-skill-parity-terra-amendment.md,
  documentation/native-claude-codex-skill-parity-proposal.html,
  tools/run-goal-np-terra-bootstrap.ps1,
  experiments/recovery/cross-family-fixture/create_fixture.py,
  experiments/recovery/cross-family-fixture/probe.py,
  tests/experiments/test_cross_family_probe.py,
  tests/distributions/test_path_choke_point.py
- **Produces:** commits on parity + journey branches; merge commit on `main`; patch-file
  backup outside worktrees; updated `plan.md`
- **Done when:** `git status --porcelain` is empty in the parity and main worktrees;
  `main` contains the maintenance fixes and closure record; one uninterrupted repo-root
  `python -m pytest` (no path argument) passes on merged `main` with the terminal summary
  saved to `documentation/findings/cp-step1-root-gate.txt`
- **Depends on:** none

<!-- autofix-applied: 2026-08-16 -->
### Step 2: Finish Step-4 installer hardening (#116)
- **Problem:** The 4-file write-ahead-authority delta (+1,843/−277) sits uncommitted in the
  main worktree with one unidentified failing test
  (`step-4-checkpoint-2026-08-13.md:73–102`; hash-verified recovery copies at
  `%LOCALAPPDATA%\SkillMesh\Recovery\skill-mesh-step-4-20260814T021546Z-73e9e215`). Identify
  the failing test in `tests/distributions/test_distributions.py`, fix root-cause (not the
  assertion), and land the delta: `tools/install-skill-mesh.ps1`,
  `tools/migrate-legacy-install.ps1`, `tests/distributions/test_distributions.py`,
  `tests/distributions/test_legacy_migration.py`. Closes #116.
- **Type:** code
- **Issue:** #119
- **Flags:** --reviewers deep
- **Files:** tools/install-skill-mesh.ps1, tools/migrate-legacy-install.ps1,
  tests/distributions/test_distributions.py, tests/distributions/test_legacy_migration.py
- **Produces:** committed hardened installer/migrator + their test suites
- **Done when:** `tests/distributions/` fully green including both write-ahead tests;
  one uninterrupted repo-root `python -m pytest` passes; #116 referenced in the commit
- **Depends on:** 1

<!-- autofix-applied: 2026-08-16 -->
### Step 3: Codex provider generation surface
- **Problem:** Add `codex` to the generation rails. Extend `config/skill-manifest.json`
  schema (`providers.codex`, per-skill `providers.codex` path, counts) + `tools/gen_manifest.py`;
  extend `tools/build-distributions.ps1` (`-Provider codex` in the ValidateSet; codex
  SKILL.md emission: YAML frontmatter `name` + `description`, generated SKILL.md requires
  co-located `core.md`, provenance header, provider-native skills absent from dist/codex);
  add `CODEX_KEYS` to `tests/package-integrity/frontmatter_contract.py:131–141`; add budget
  tests (per-skill 7,500-char metadata cap; whole-catalog initial-list serialization
  estimate asserted under 8,000 chars). **Grep every consumer of the provider set before
  landing** (manifest `counts`, `providers` dict readers, dist-tree-shape tests,
  two-provider tallies like `Counter({portable:47, provider-native:3})`) and list each call
  site with a verdict in the step report, per the key-shape rule. Regenerate + commit the
  pinned `tests/package-integrity/expected_inventory.json` (owned by `gen_manifest.py`, per
  its module docstring) and `skills/inventory.json` (owned by `tools/gen_skill_tree.py:81`);
  extend `tools/release.ps1` `-Provider` handling (default `'both'` at release.ps1:102,
  forwarded at :213) to cover codex.
- **Type:** code
- **Issue:** #120
- **Flags:** --reviewers deep
- **Files:** config/skill-manifest.json, tools/gen_manifest.py, tools/build-distributions.ps1,
  tests/package-integrity/frontmatter_contract.py, tests/package-integrity/expected_inventory.json,
  tests/package-integrity/test_manifest_contract.py, tools/release.ps1, skills/inventory.json,
  tools/gen_skill_tree.py
- **Produces:** manifest schema v-next + regen support; `-Provider codex` generation; codex
  frontmatter contract + budget tests; a fixture skill generating under dist/codex
- **Done when:** `powershell -File tools/build-distributions.ps1 -Provider codex` emits a
  deterministic tree for a fixture skill (rerun byte-identical); regenerated dist/claude and
  dist/gpt are byte-identical to pre-step output (regression compare); focused suites green
  (`python -m pytest tests/`)
- **Depends on:** 1

<!-- autofix-applied: 2026-08-16 -->
### Step 4: Author pilot providers/codex.md + delta log scaffold
- **Problem:** Author `providers/codex.md` for the 5 pilot skills — task-handoff,
  user-orient, lesson-harvest, plan-review, session-wrap — following the existing
  `providers/gpt.md` pattern (load core in full; preserve gates, retry limits, filesystem
  safety, exact output contracts; map host abstractions: Claude Agent/Workflow →
  core's documented single-context fallback; Artifact → file outputs; halt visibly with
  `required_tool_missing` where core requires an unavailable host tool). Add the 5 manifest
  entries; generate dist/codex. Scaffold `documentation/parity-deltas.md` (columns:
  `skill | delta | severity | disposition`; M-verdict header lines). Read
  `config/model-mapping.json` + `config/model-tier-map.json` (producing files) and decide
  whether a codex provider entry is required for tier resolution; add it if so.
- **Type:** code
- **Issue:** #121
- **Flags:** --reviewers code
- **Files:** skills/task-handoff/providers/codex.md, skills/user-orient/providers/codex.md,
  skills/lesson-harvest/providers/codex.md, skills/plan-review/providers/codex.md,
  skills/session-wrap/providers/codex.md, config/skill-manifest.json,
  config/model-mapping.json, documentation/parity-deltas.md
- **Produces:** 5 × `providers/codex.md`; manifest entries; `documentation/parity-deltas.md`
  scaffold; generated `dist/codex/<5 skills>/`
- **Done when:** dist/codex holds exactly the 5 pilot skills with provenance headers;
  frontmatter + budget tests green; focused suites green
- **Depends on:** 3

<!-- autofix-applied: 2026-08-16 -->
### Step 5: Codex install path + bring-up probe kit
- **Problem:** Make codex installable and inspectable without touching any real home.
  Extend `tools/skill-mesh-discovery.ps1` (codex → `.agents/skills` as installable root —
  today it is Copilot's never-install active-alternate, lines 39–56; grep all discovery-map
  consumers first), `tools/install-skill-mesh.ps1 -Provider codex` (identical ledger
  semantics, built on Step 2's hardened base), `tools/inspect-host-install.ps1` codex
  reporting. Author `tools/probe-codex-skills.ps1` (resolve `$CODEX_EFFECTIVE_HOME` with
  HOME/USERPROFILE agreement check — disagreement reports and stops; report tree + ledger;
  `-Home` override). Add the smoke gate: automated temp-home round-trip test — install the
  pilot profile into a disposable home, inspect verifies every file + ledger, uninstall
  removes cleanly, path-guard proves zero writes outside the temp home. No codex invocation
  anywhere in this step.
- **Type:** code
- **Issue:** #122
- **Flags:** --reviewers deep
- **Files:** tools/skill-mesh-discovery.ps1, tools/install-skill-mesh.ps1,
  tools/inspect-host-install.ps1, tools/probe-codex-skills.ps1, tests/distributions/
- **Produces:** codex install/inspect/discovery support; probe script; temp-home round-trip
  test (the pipeline smoke gate)
- **Done when:** round-trip test green; discovery-map consumer grep table in step report;
  one uninterrupted repo-root `python -m pytest` passes (pass-1 exit gate)
- **Depends on:** 2, 4

<!-- autofix-applied: 2026-08-16 -->
### Step 6: Cohort B — pipeline family
- **Problem:** Author `providers/codex.md` + manifest entries for the pipeline skills used
  by real workflows: remaining plan-* (plan-init, plan-feature, plan-expedite, plan-merge,
  plan-redline, plan-trim, plan-wrap — plan-review shipped in pilot), repo-init, repo-sync,
  repo-update, task-handoff adjacents user-wrap and user-project. Generate; extend budget
  test to the enlarged catalog. Record any per-skill authoring deltas in the delta log.
- **Type:** conditional
- **Condition:** grep -qi "M1: PASS" documentation/parity-deltas.md
- **Issue:** #123
- **Flags:** --reviewers code
- **Files:** skills/{plan-init,plan-feature,plan-expedite,plan-merge,plan-redline,plan-trim,plan-wrap,repo-init,repo-sync,repo-update,user-wrap,user-project}/providers/codex.md,
  config/skill-manifest.json, tests/package-integrity/expected_inventory.json,
  skills/inventory.json
- **Produces:** 12 provider files; regenerated dist/codex; delta log rows
- **Done when:** frontmatter/budget/determinism tests green over the enlarged set; focused
  suites green
- **Depends on:** 5

<!-- autofix-applied: 2026-08-16 -->
### Step 7: Cohort C — build/review/skill/tier families
- **Problem:** Author `providers/codex.md` + manifest entries for build-phase, build-step,
  build-queue, review-deep, review-gauntlet, review-proof, review-uat, skill-iterate,
  skill-evolve, skill-eval-setup, tier-escalate, tier-offload, judge-ui, test-prune,
  goblin-do, goblin-suggest. These are the heaviest host-abstraction consumers (subagent
  spawns, worktrees) — map each to the core's documented fallback and record every
  degradation as a delta-log row.
- **Type:** conditional
- **Condition:** grep -qi "M1: PASS" documentation/parity-deltas.md
- **Issue:** #124
- **Flags:** --reviewers code
- **Files:** skills/{build-phase,build-step,build-queue,review-deep,review-gauntlet,review-proof,review-uat,skill-iterate,skill-evolve,skill-eval-setup,tier-escalate,tier-offload,judge-ui,test-prune,goblin-do,goblin-suggest}/providers/codex.md,
  config/skill-manifest.json, tests/package-integrity/expected_inventory.json,
  skills/inventory.json
- **Produces:** 16 provider files; regenerated dist/codex; delta log rows
- **Done when:** same test bar as Step 6
- **Depends on:** 6

<!-- autofix-applied: 2026-08-16 -->
### Step 8: Cohort D — remainder of the portable catalog
- **Problem:** Author `providers/codex.md` + manifest entries for the exact 14 remaining
  portable skills: memory-distill, observatory-doctor, research-prospect, user-afterparty,
  user-brainstorm, user-debug, user-draft, user-gateway, user-lavishify, user-learn,
  user-pm, user-shakedown, user-uat, user-walkthrough — bringing all 47 portable skills to
  a codex provider. Whole-catalog budget test now asserts the full 47-name initial list
  serializes under the 8,000-char floor with no truncation. Update the docs that pin
  provider counts and commands: README.md Providers & installation section
  (README.md:459–472, "47 of 50 … both hosts" prose + provider table gains the codex row)
  and CLAUDE.md Commands (CLAUDE.md:64–72 gains the codex build/install variants).
- **Type:** conditional
- **Condition:** grep -qi "M1: PASS" documentation/parity-deltas.md
- **Issue:** #125
- **Flags:** --reviewers code
- **Files:** skills/{memory-distill,observatory-doctor,research-prospect,user-afterparty,user-brainstorm,user-debug,user-draft,user-gateway,user-lavishify,user-learn,user-pm,user-shakedown,user-uat,user-walkthrough}/providers/codex.md,
  config/skill-manifest.json, tests/package-integrity/expected_inventory.json,
  skills/inventory.json, README.md, CLAUDE.md
- **Produces:** remaining 14 provider files; full dist/codex catalog; updated README/CLAUDE.md
- **Done when:** 47/47 portable skills in dist/codex; whole-catalog budget test green; one
  uninterrupted repo-root `python -m pytest` passes (pass-2 exit gate)
- **Depends on:** 7

<!-- autofix-applied: 2026-08-16 -->
### Step 9: Fix worst M2 deltas
- **Problem:** Address the deltas the operator marked `fix` during the M2 end-to-end
  workflow parity pass (findings file
  `documentation/findings/codex-parity-m2-deltas.md`). Root-cause fixes in cores or codex
  providers; a core change must keep claude/gpt outputs byte-identical unless the delta
  log row says otherwise.
- **Type:** conditional
- **Condition:** test -s documentation/findings/codex-parity-m2-deltas.md
- **Issue:** #126
- **Flags:** --reviewers code
- **Files:** skills/*/core.md and skills/*/providers/codex.md (delta-dependent),
  documentation/parity-deltas.md, documentation/findings/codex-parity-m2-deltas.md
- **Produces:** targeted fixes; updated delta log dispositions
- **Done when:** every `fix` row from M2 resolved or re-dispositioned with rationale;
  focused suites green
- **Depends on:** 8

<!-- autofix-applied: 2026-08-16 -->
### Step 10: Promote the 7 workspace custom skills
- **Problem:** Promote build-observer, citation-distill, citation-review, citation-sweep,
  citation-triage, goblin-sweep, repo-wrap from workspace-custom (.claude/skills) into the
  canonical catalog: author `core.md` + `providers/{claude,gpt,codex}.md` each, following
  the established promotion pattern; manifest entries; generate all three dists. Read each
  skill's current SKILL.md as the producing source.
- **Type:** conditional
- **Condition:** grep -qi "M1: PASS" documentation/parity-deltas.md
- **Issue:** #127
- **Flags:** --reviewers code
- **Files:** skills/{build-observer,citation-distill,citation-review,citation-sweep,citation-triage,goblin-sweep,repo-wrap}/,
  config/skill-manifest.json, tests/package-integrity/expected_inventory.json,
  skills/inventory.json, README.md
- **Produces:** 7 promoted skill dirs; manifest at 57 entries; regenerated dists
- **Done when:** catalog counts updated everywhere the count is asserted (grep first);
  budget tests green at 54 codex names; one uninterrupted repo-root `python -m pytest`
  passes (pass-3 exit gate)
- **Depends on:** 8

<!-- redline-applied: 2026-08-16 -->
### Step 11: Wire the 7 utility advisory calls into canonical cores
- **Problem:** The dev-side utility-hookup effort (Steps 1–3 DONE) wired advisory calls
  into INSTALLED skill copies — 16 modified `.github/skills/*/core.md` files in the dev
  root, which every reinstall would overwrite (their generated-file headers say so).
  Reconcile that wiring upstream: read the owning sources — the advisory-call convention
  (`dev/.claude/references/advisory-call-convention.md`, the ONE owner: cheap gate →
  bounded synchronous call with tree cleanup → zero-or-one advisory line → fail-open →
  never block → no new caller state) and the utility-hookup owning plan — then port the
  advisory-call blocks into the canonical `skills/<skill>/core.md` for the authoritative
  hookup map (working set: judge-ui, plan-feature, plan-init, plan-review, repo-update,
  review-deep, review-gauntlet, review-proof, skill-evolve, skill-iterate, tier-escalate,
  tier-offload, user-afterparty, user-gateway, user-uat, user-wrap). Regenerate all three
  dists (claude/gpt byte-changes are DELIBERATE here — the regression expectation updates
  with rationale). Add mechanical tests: each wired core carries its advisory block; a
  fails-open test asserts absent `DEV_UTILITIES_ROOT` produces zero behavior change and a
  malformed opt-in config produces exactly one advisory line, never a halt.
- **Type:** code
- **Issue:** #128
- **Flags:** --reviewers deep
- **Files:** skills/{judge-ui,plan-feature,plan-init,plan-review,repo-update,review-deep,review-gauntlet,review-proof,skill-evolve,skill-iterate,tier-escalate,tier-offload,user-afterparty,user-gateway,user-uat,user-wrap}/core.md,
  tests/package-integrity/ (new hookup-presence + fails-open tests)
- **Produces:** 16 wired canonical cores; regenerated dists; hookup tests
- **Done when:** hookup-presence + fails-open tests green; focused suites green; the
  advisory blocks match the convention's 8 points verbatim where the convention locks
  wording; delta log notes the codex-host behavior (silent skip without utilities root)
- **Depends on:** 2, 3

<!-- redline-applied: 2026-08-16 -->
### Step 12: Make the wiring observatory-visible
- **Problem:** The M4 UAT gate is "see the wiring through dev-observatory." Read the
  observatory producing sources (dev repo: `.claude/observatory/registry.toml`,
  `dev-observatory/src/dev_observatory/` — view_sources/registry/model modules) to
  determine the actual visibility mechanism (registry hookups table vs. scrape-derived
  from cores), then make the Step-11 wiring discoverable through it: update the registry
  hookups entries if that is the mechanism, or verify the scrape picks up the canonical
  blocks if derivation is automatic. Cross-repo boundary: this step touches the dev repo
  read-mostly and path-scoped; dev-observatory feature work (its dirty Steps 32–42, planned
  Step 43) stays in ITS plan — if the visibility mechanism turns out to require unbuilt
  Step-43 surfaces, record that as a named cross-plan dependency in the delta log and in
  this step's report instead of building it here.
- **Type:** code
- **Issue:** #129
- **Flags:** --reviewers code
- **Files:** dev repo: .claude/observatory/registry.toml (if hookups are registry-borne);
  documentation/parity-deltas.md (cross-plan dependency rows if any)
- **Done when:** the wiring for the 16 skills is resolvable through an observatory surface
  (registry entries verified by `observatory doctor`/scrape, or scrape-derivation confirmed
  against the canonical cores), OR a named cross-plan dependency on dev-observatory Step 43
  is recorded with exactly what M4 will and won't be able to see
- **Depends on:** 11

### Manual Steps
(These run after the corresponding /build-phase pass completes. Operator drives.)

### Step M1: Pilot bring-up in a real Codex session
- **Source step:** Step 5 (pass 1)
- **Issue:** #130
- **Commands:**
  ```powershell
  # 1. Probe (read-only): confirm effective home + current root state
  powershell -File tools\probe-codex-skills.ps1

  # 2. Rehearse against a disposable home first
  powershell -File tools\install-skill-mesh.ps1 -Provider codex -Home "$env:TEMP\codex-pilot-home"
  powershell -File tools\inspect-host-install.ps1 -Provider codex -Home "$env:TEMP\codex-pilot-home"

  # 3. Real install (THIS is the scoped-approval write, per D-CP2)
  powershell -File tools\install-skill-mesh.ps1 -Provider codex
  powershell -File tools\inspect-host-install.ps1 -Provider codex
  ```
  Then in a normal interactive Codex session: ask it to list available skills; invoke
  task-handoff and plan-review on a toy target. Afterwards, if Copilot CLI is present, run
  its skill listing to record shared-root visibility.
- **What to look for:**
  | Check | Expected outcome |
  |---|---|
  | Probe resolves `$CODEX_EFFECTIVE_HOME` | HOME/USERPROFILE agree; single home reported |
  | All 5 pilot skills listed by Codex | names + descriptions visible, no truncation (budget) |
  | Invoking task-handoff | SKILL.md loads, core.md followed, output contract honored |
  | Invoking plan-review | runs via single-context fallback; gates preserved; verdict rendered |
  | Writes confined | only `.agents/skills/*` + ledger touched (inspect confirms) |
  | Copilot shared-root visibility | recorded either way in delta log (feeds D-CP6 decision) |
  | Codex CLI version | recorded in delta log header (D-CP7) |

  Record rows + verdict line `M1: PASS` (or `M1: FAIL — <reason>`) in
  `documentation/parity-deltas.md`. **If FAIL on discovery itself:** stop — cohorts B–D
  stay skipped; investigate placement/format against the installed CLI before any further
  authoring.

### Step M2: End-to-end workflow parity pass
- **Source step:** Step 8 (pass 2)
- **Issue:** #131
- **Commands:**
  ```powershell
  # Ensure full catalog is installed
  powershell -File tools\install-skill-mesh.ps1 -Provider codex
  powershell -File tools\inspect-host-install.ps1 -Provider codex
  ```
  In a real Codex session, run one representative workflow end-to-end on a toy project:
  plan-feature → plan-review → plan-wrap → session-wrap. Note every material behavioral
  difference vs the same flow on Claude.
- **What to look for:**
  | Check | Expected outcome |
  |---|---|
  | Each pipeline skill invocable | loads core, walks its phases, honors output contracts |
  | Workflow chains end-to-end | artifacts produced where cores demand them |
  | Deltas | recorded as rows; anything blocking marked `fix` |

  Write `fix`-severity findings to `documentation/findings/codex-parity-m2-deltas.md`
  (this file's non-emptiness triggers Step 9) and add `M2: PASS/FAIL` to the delta log.

### Step M3: Acceptance + delta triage
- **Source step:** Steps 9–10 (pass 3)
- **Issue:** #132
- **Commands:**
  ```powershell
  powershell -File tools\inspect-host-install.ps1 -Provider codex
  ```
  Use Codex-hosted skills in normal daily work for a few sessions. Then triage every open
  delta-log row to a final disposition (accept / fix-later-issue / wontfix).
- **What to look for:**
  | Check | Expected outcome |
  |---|---|
  | Daily-use quality | pipelines behave materially similarly; no unrecorded surprises |
  | Delta log | zero rows without a disposition; `fix-later` rows have GitHub issues |
  | Plan completion | operator declares Phase CP complete; /repo-update runs |

### Step M4: Wired-profile rollout + observatory wiring UAT
- **Source step:** Steps 11–12 (pass 3)
- **Issue:** #133
- **Commands:**
  ```powershell
  # Reinstall the wired profiles over the live install (the D-CP14 operator-gated write).
  # This intentionally overwrites the drifted installed cores — Step 11 adopted that
  # drift upstream; inspect confirms installed bytes = generated bytes, ledger updated.
  powershell -File tools\install-skill-mesh.ps1 -Provider claude
  powershell -File tools\install-skill-mesh.ps1 -Provider gpt
  powershell -File tools\install-skill-mesh.ps1 -Provider codex
  powershell -File tools\inspect-host-install.ps1 -Provider claude
  ```
  ```powershell
  # Then, from the dev repo: launch dev-observatory and open the wiring surface
  # (mesh-lens / registry hookups view per Step 12's report).
  uv run --project dev-observatory observatory launch
  ```
- **What to look for:**
  | Check | Expected outcome |
  |---|---|
  | Reinstall clean | ledger-verified; drifted cores adopted, not stranded; no foreign files touched |
  | Wiring visible in observatory | the 16 wired skills' utility hookups resolvable in the UI, per Step 12's mechanism |
  | Advisory behavior live | one wired skill run with `DEV_UTILITIES_ROOT` set shows its advisory line; unset shows zero behavior change |
  | Cross-plan gaps | anything M4 can't see is already a named dependency row from Step 12, not a surprise |

  Record `M4: PASS/FAIL` + rows in the delta log. M4 and M3 together close the plan.

## 8. Risks and Open Questions

| Item | Risk | Mitigation |
|---|---|---|
| Codex may not discover skills at `.agents/skills` | The core placement assumption is unverified on this machine — highest-impact unknown | M1 runs after only 5 skills are authored; cohorts B–D conditional on `M1: PASS`; total sunk cost on FAIL ≈ one authoring step |
| Installed Codex CLI ≠ 0.147.0 research base | Frontmatter/placement/budget behavior may differ from the pinned research | D-CP7: M1 records installed version; format re-verified on real host before rollout |
| Initial-list budget (8,000 chars) with 47–54 skills | Catalog could truncate in Codex's skill list | Budget tests from Step 3 onward estimate serialization; M1/M2 verify no truncation on the real host; worst case: trim descriptions (they're authored, not derived) |
| Shared root with Copilot | Copilot may load codex-profile packages | D-CP6: evidence gathered in M1, policy decided in triage; guard work only if needed |
| Host-abstraction gaps (no Agent/Workflow/Artifact on Codex) | Heavy skills (build-*, review-*) degrade on Codex | Cores already define fallbacks + `required_tool_missing` halts; degradations are delta-log rows, not silent behavior changes |
| Step-4 failing test root cause unknown | Could be a real installer defect, not a test artifact | Step 2 requires root-cause fix, full distributions suite + full-root gate before anything builds on the installer |
| Step 1 merge disturbs frozen evidence expectations | P3–P7 evidence/absence predicates live outside git and must stay untouched | Step 1 touches only git worktrees; no Evidence/ or Staging/ paths; launcher parked not invoked |
| `plan.md` edits redden hygiene tests | `test_recovery_plan_hygiene.py` asserts exact strings (e.g. `Provider expansion \| PARKED`) | Impact table names the constraint; Step 1's Done-when includes the full-root gate that runs those tests |
| Two sessions editing shared worktrees | Parallel-session sweeps could disturb Step 1's choreography | Step 1 runs single-session, path-scoped adds only, verifies hashes immediately before committing |
| Dev-root drifted cores as wiring source | The 16 modified installed cores are uncommitted working-tree state in another repo; a sweep or reinstall before Step 11 could lose the utility-hookup Steps 1–3 output | Step 11 reads them early in pass 3 and ports to canonical; M4's overwriting reinstall happens only AFTER Step 11 adopted the drift |
| Advisory call regresses into a blocker | A wired call that halts a pipeline skill violates the convention's safety-critical rule | Step 11's fails-open tests (absent root → zero change; malformed config → one advisory line); --reviewers deep on the wiring diff |
| Observatory can't show the wiring yet | dev-observatory Step 43 is planned/unbuilt; Steps 32–42 are dirty in its own plan | Step 12 either verifies an existing surface or records a named cross-plan dependency stating exactly what M4 can and cannot see — no silent gap |

## 9. Testing Strategy

- **Per-step:** focused suites (`python -m pytest tests/`) during iteration — narrowest
  first is fine for iterating, per the change-scope charter.
- **DONE/merge gates:** every pass-exit step (1, 2, 5, 8, 10) requires one uninterrupted
  repo-root `python -m pytest` **with no path argument** (three root-only test roots
  otherwise escape collection — CLAUDE.md:31–89), terminal summary saved. This is the
  workspace full-suite DONE-gate rule; no subset counts as gate evidence.
- **New automated coverage:** codex dist determinism (byte-identical rerun); dist/claude +
  dist/gpt byte-regression whenever the generator changes; `CODEX_KEYS` frontmatter
  contract; per-skill metadata cap (7,500) + whole-catalog budget floor (8,000); temp-home
  install/inspect/uninstall round-trip with path-guard (the smoke gate — real components,
  no mocks, no model calls).
- **Existing tests that may break (expected, enumerated in Step 3's consumer grep):**
  provider-set tallies, manifest `counts` assertions, dist-tree shape tests,
  discovery-root map tests. Each gets extended-not-weakened; any test diff that *relaxes*
  an assertion is treated as suspect per the wire-shape audit rule.
- **End-to-end verification:** M1 (real Codex session, pilot), M2 (real workflow chain),
  M3 (daily-use acceptance) — real-host evidence replaces the retired 113-cell matrix as
  the parity gate, with the delta log as the durable record.

## Appendix — Decision Inventory

IDs are stable and append-only; reversals keep their ID with `changed <date>`.

| ID | P/D | Choice | Status |
|---|---|---|---|
| P1 | P | Revert Terra executor amendment — Claude-led implementation | accepted 2026-08-16 |
| P2 | P | Close Publication 8 unapproved; park launcher | accepted 2026-08-16 |
| P3 | P | Exhaustive 113-cell matrix downgraded to backlog; smokes + delta log gate | accepted 2026-08-16 |
| P4 | P | Additive/destructive split; destructive cutover out of scope | accepted 2026-08-16 |
| P5 | P | Close on parity branch, merge to main; new work on main | accepted 2026-08-16 |
| P6 | P | Finish Step-4 installer WIP as early plan step (#116) | accepted 2026-08-16 |
| P7 | P | Pilot cohort = mixed probe (3 simple + 2 pipeline) | accepted 2026-08-16 |
| P8 | P | Shared .agents/skills root policy decided on M1 evidence | accepted 2026-08-16 |
| D-CP1 | D | Codex = third provider on existing manifest/generator/installer rails | accepted 2026-08-16 |
| D-CP2 | D | Additive-only writes; M1 real-root install is the scoped-approval write | accepted 2026-08-16 |
| D-CP3 | D | P8 content committed as-is; Step 1 runs --reviewers auto | accepted 2026-08-16 |
| D-CP4 | D | Close-not-exact parity; deltas recorded, gate only on operator `fix` | accepted 2026-08-16 |
| D-CP5 | D | Cohorts B–D conditional on `M1: PASS` in the delta log | accepted 2026-08-16 |
| D-CP6 | D | Shared-root guard work only if M1 evidence demands it | accepted 2026-08-16 |
| D-CP7 | D | Parity targets the installed Codex CLI, not the 0.147.0 pin | accepted 2026-08-16 |
| D-CP8 | D | Step-4 hardening lands before installer extension (Step 2 → Step 5) | accepted 2026-08-16 |
| D-CP9 | D | Step 9 keeps --reviewers code (byte-regression tests guard core edits) | accepted 2026-08-16 |
| D-CP10 | D | Steps 2/3/5 escalated to --reviewers deep; build passes run in an Opus window | accepted 2026-08-16 |
| D-CP11 | D | Issue label `Phase CP Step N:`; steps 1–10 + M1–M3; issues mint at #117+ | accepted 2026-08-16 |
| D-CP12 | D | Pilot five = task-handoff, user-orient, lesson-harvest, plan-review, session-wrap | accepted 2026-08-16 |
| P9 | P | Utility wiring + observatory-visible UAT are in scope (redline feedback) | accepted 2026-08-16 |
| D-CP13 | D | Advisory calls live in canonical cores; fail open on every host | accepted 2026-08-16 |
| D-CP14 | D | Live-home reinstall of wired profiles is operator-gated (M4) | accepted 2026-08-16 |
| D-CP15 | D | Observatory visibility = UAT evidence; dev-observatory features stay in its plan | accepted 2026-08-16 |
