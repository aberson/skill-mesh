# Descope decision record — 2026-09

**Status:** OPERATOR-APPROVED 2026-09-05 (Abraham Robison, in-session: "Approve A1-6").
**Authority:** This document supersedes `documentation/phase-prod-rd-first-course-correction.md`
as the active execution authority for skill-mesh. Where this record is silent, standing repo
rules (CLAUDE.md, the workspace rule files, the product charter) continue to apply unchanged.

## 1. Why

The product the operator wants — one set of skills authored once, running on Claude Code and
the Codex CLI, with CRUD(R) rules for the catalog — already works except for the CRUD rail.
The codex profile is proven on the real consumer home (M1/M2/M4 PASS in
`documentation/parity-deltas.md`, independently re-reproduced from the live install ledger on
2026-09-05: 125 files, 0 stale, 0 unledgered, all hashes matching). What has consumed two
months (286 commits, ~65% of them docs/plan/checkpoint) is a certification program that kept
growing: the CRUD rail (Phase CL) was parked at the end of a chain running through an
installer-authority redesign that consumed at least six candidate build windows (Phase RD
Step 1; four of those worktrees still hold dirty state on disk) and a
disposable kernel-driver containment environment (the Phase IS tail) that no functional
component consumes. The operative freeze stalls external projects. This record replaces that
chain with the shortest path that preserves the core want, recording every cut as a decision
rather than drift.

## 2. Verified basis

Facts checked against primary sources on 2026-09-05 (adversarial verification pass):

1. The freeze is enforced solely by the dev workspace's `.claude/task-state/freeze.json`.
   No hook, test, or scheduled task references its seal condition. Amending it is purely an
   operator-authority act.
2. The 39 review-deep calibration-corpus paths are byte-exact recoverable from the local
   source repository the restoration plan's §3 names (that plan owns the exact source
   spelling), at immutable commit `3a7ae33d09b9b26edb291e2db0cdaca1022ed643` (reachable
   from its origin/master; spot-checked SHA-256s match the donor worktree). The preserved calibration-assets evidence branch
   (tip `4b9b0aa`) carries only 4 of the 39 — the legacy top-level `review-deep/scripts/`
   copies, byte-identical to the source and also tracked on main — so the source commit
   above is the import source for the full set.
3. On main@`70520aa`, `skills/review-deep/evals/` and `scripts/` are empty untracked
   directories with no ignore rule. The calibration blocker is
   `_shared/calibrate_judge.py` (lines ~841-846) resolving `--skill` against the legacy
   repo-root tree; a root-aware resolution (or `--skill-dir`) fix is required. review-deep
   currently calibrates nowhere — on Claude as well as Codex.
4. The full repo-root `python -m pytest` DONE gate is ~2.5 hours (last certified
   1380 passed / 1 skipped in 2:30:30 at `6d14626`; sole count owner
   `documentation/phase-75-baseline.md`). The suite now collects 1544, including
   `tests/production-toolchain` (119 tests, added at `2e8e4f3`; green in that step's own
   gates at 1543 passed / 1 skipped but not yet recorded by the baseline owner), so the next
   gate runs longer than the recorded baseline.
5. The Phase IS tail (Step 108P/#162, Step 109/#153, stages C2E-C5) serves only the five
   attended D10 behavioral rows and the out-of-tree portfolio instruction-file inversion.
   All Phase IS product behavior landed and was certified in Steps 100-108. Nothing
   functional breaks if the tail is parked.
6. Phase CL's park condition (Phase IS C5 + Phase CP M3) is a procedural baseline freeze
   (CL-D1/CL-D2 protect the frozen 57/54 candidate cardinalities), not a technical
   dependency; the rail builds only on the existing hermetic manifest/build/install/release
   toolchain.

## 3. Decisions

### DS-D1 — Adoption and supersession
The descope-first plan (S1-S9, section 5) is adopted. This record supersedes
`documentation/phase-prod-rd-first-course-correction.md` as execution authority. That
document's §3 preserved-evidence table (seven branches with binding SHA-256 digests) remains
in force and is carried forward by DS-D11.

### DS-D2 — Freeze lift
The freeze file's unfreeze condition is amended by this decision: **when this record lands on
main, run the applicable bookkeeping items of the dev workspace's
`docs/seeds/seed_post_freeze_cleanup.md` and delete the freeze file.** Phase RD Step 4's
`PhaseRdActivationSealV1` no longer gates the lift. The seed's migration-evidence-retirement
and parked-work items are NOT executed at lift time; they fold into S3 (worktree rescue) and
S5 (bookkeeping) with the preserved-evidence constraints of DS-D11. Before deletion, the
freeze file's protected-artifact enumeration is carried forward into section 7 of this
record, so the deletion loses no enumeration.

### DS-D3 — Phase RD as written is cut; RD-lite replaces it
Phase RD Steps 1-4 (#178-#181) are cut; those four issues close as superseded, citing this
record and the rescue branches (section 4). Umbrella **#177 stays open**, re-scoped by
comment to RD-lite, and serves as the S4 build-step's tracking issue. The replacement,
**RD-lite**, is one build-step with one executable boundary:

- Import the 39 corpus paths from the restoration plan §3's named source repository at
  commit `3a7ae33d09b9b26edb291e2db0cdaca1022ed643` (Git object bytes,
  never working-tree bytes) into `skills/review-deep/evals/**` and
  `skills/review-deep/scripts/**`, plus the package-local
  `skills/review-deep/config/model-tier-map.json` snapshot. Duplication hazard, named:
  4 of the 39 script leaves already exist byte-identical on main in the legacy top-level
  `review-deep/scripts/` package; the build-step must either keep the two locations
  byte-identical with a test asserting it, or retire the legacy copies within the standing
  deprecation window (one source of truth).
- Fix `_shared/calibrate_judge.py` skill resolution so
  `calibrate_judge.py` calibrates review-deep from the canonical `skills/` tree in-repo
  (exit 0), with regression tests.
- Exit-0 `--help` for the two shell helpers if cheap; otherwise defer.
- **Explicitly out of scope:** manifest `package_assets` declarations, package-index
  emission, builder changes, installer per-leaf raw ownership, WAL v2, the force-refusal
  boundary, and installed-tree distribution of the corpus.
- Pre-grep the imported corpus for absolute user paths before the slow gate (public repo).
- DONE gate: the full repo-root pytest, detached, under the standing admission rules.

**Codex review-deep remains a KNOWN GAP:** the codex adapter keeps its honest
fail-closed `required_tool_missing` halt. The gap's write-up in
`documentation/troubleshooting.md` and the codex provider documentation is S5 work (not yet
written as of this record; this sentence is the interim record). Any future
restoration of the codex deep lane starts from the rescue branches under a new reviewed plan
— it does not reopen Phase RD as written.

### DS-D4 — Phase IS tail parked, terminal-unless-recertified
Step 108P (#162), Step 109 (#153), and stages C2E-C5 are parked indefinitely. #143/#162/#153
receive PARK labels and comments and stay open. The frozen UAT blob and the sealed C2V/C2A
artifacts stay frozen and untouched. **Accepted one-way door:** the first CRUD catalog change
(Phase CL) alters the frozen 57/54 candidate cardinalities, making the parked Phase IS
certification permanently uncertifiable unless redone from scratch. The operator accepts
this. The out-of-tree portfolio inversion that Step 109 gates stays formally blocked until a
future operator decision re-prices it.

### DS-D5 — Production/development split parked as Track C (kept, not killed)
The Phase PROD MVP replan obligation is cut and umbrella #183 closes. The landed declarative
Step 1 (#184 at `2e8e4f3`, the production-record contract and its 119-test suite) stays on
main as the seed. **The dev+prod split is Track C: it re-enters after S9 (closeout) by a
fresh operator decision, seeded by the course-correction's §7 notes plus the Step-1
declarative records.** Nothing in the CRUD rail forecloses it; `tests/production-toolchain`
keeps running in every DONE gate so the seed cannot rot silently.

### DS-D6 — Goal NP affirmed terminal
Goal NP remains CLOSED UNAPPROVED with no successor. The parked launcher
(`tools/run-goal-np-terra-bootstrap.ps1`) is never invoked or renamed.

### DS-D7 — Phase CL amendments (the CRUD rail becomes the main track)
`documentation/skill-catalog-lifecycle-plan.md` is amended (S6) before building:

- (a) Steps 110-117 `Flags`: `--reviewers deep` → `--reviewers code`. Authority for this
  downgrade is this record itself; PROD-D8 is cited only as the prior instance of a recorded
  lane downgrade (precedent of form — its own text does not extend to other plans).
  Rationale: the codex deep package remains a known gap, the freshly restored Claude deep
  lane has no calibration track record, and the operator chooses the code lane for CL to cut
  stall risk.
- (b) Step 110 preflight: `PHASE_CL_PREREQUISITE_NOT_MET` (Phase IS C5 + CP M3) is retired,
  replaced by: this record on main + freeze deleted + clean synchronized main.
- (c) gpt/Copilot is demoted to a **mandatory build-only adapter** (all 54 portable skills
  keep `gpt.md`; the builder and release keep emitting `dist/gpt`), per product-charter
  anti-goals 2 and 9. Step 118's attended acceptance narrows to claude+codex.
- (d) #192 (installer `-Force` path-identity hardening) folds into whichever CL step touches
  the installer, as an explicit item.
- (e) #165 (codex adapter capability-claims honesty sweep) folds into CL as one small batched
  step. Because review-gauntlet is a representative skill, the release-candidate report is
  regenerated in the same change that edits it.
- (f) The plan's per-step root-gate budget ("a repository-root pytest after each code step;
  budget for eight root gates") is amended to permit the sanctioned shared-gate batching
  (the Steps 104-106 precedent): steps flipping DONE together must land in the same
  build-phase run and the shared gate runs at the batch head commit. This is a gate-CADENCE
  amendment recorded here; the full-suite DONE-gate definition itself is unchanged.

### DS-D8 — pta_finance resume condition amended, deep lane kept
The external consumer's Step 14 resume condition is amended from "all four Phase RD issues
DONE + `PhaseRdActivationSealV1`" to **"RD-lite landed on main"** (S4). Its
`--reviewers deep --isolation worktree` lane is NOT weakened. Non-deep lanes resume at the
freeze lift (S2). Contingency: if RD-lite slips materially (order of two weeks), the operator
may downgrade that lane to `--reviewers code` by a recorded follow-up decision.

### DS-D9 — CP M3 formal grading replaced by light proof + soak log
Phase CP's M3 daily-use grading is replaced by: (1) the attended light proof (S8) — build all
providers, install claude+codex into the real consumer home, one `/skill-crud` round-trip on
each host, one in-repo Claude review-deep calibration run, recorded in a one-page acceptance
note that states the accepted evidence bar; and (2) an ambient codex soak log — one line per
genuine Codex-hosted session in `plan.md`, closing after ~5 clean sessions. #131/#132/#133
close at S8.

### DS-D10 — Issue sweep
Authorized (S5), with this keep-list open: #165, #182, #192, #167-#176 (Phase CL), and
**#177** (re-scoped to RD-lite per DS-D3 — it stays open until S4 lands), plus any new track
umbrellas. Close as superseded, citing this record: #178-#181, #183, and the stale
early-phase step remnants (Phases 1-8 and 7.5). #143/#153/#162: PARK label + comment, stay
open (DS-D4). Standalone defect issues #134-#161 are triaged individually, never templated.

### DS-D11 — Standing constraints (restated, unchanged)
- The seven preserved evidence worktrees in the course-correction §3 table stay read-only
  with their binding digests. This record authorizes no rescue, edit, merge, deletion, or
  prune of those seven; any future change to that rule requires its own recorded operator
  decision.
- No force-push or history scrub anywhere.
- The full repo-root `python -m pytest` remains THE DONE/merge gate for every build-bearing
  step (S4, S7), under the standing admission rules (>=2 GB free memory, zero competing
  pytest, clean tree, exact HEAD). `documentation/phase-75-baseline.md` remains the sole
  owner of counts.
- No absolute user paths or private values in any committed file (public repository).
  Consequence for S3: rescue branches whose sidecar files carry machine paths are
  **local-only** — they are not pushed to the public origin; durability comes from the
  rescue commit plus, where warranted, a local bundle outside the repository.
- Workspace code-quality, worktree-hygiene, and plan-flow rules continue to apply.

## 4. Dispatch reconciliation (A6: ratified as evidence only)

Four Phase RD Step-1 windows hold dirty state at base `70520aa` that arose while the status
prose said "RECOVERY READY / NOT DISPATCHED":

- `worktree_build-step-rd178-step1-20260904` (~43 uncommitted entries) and
  `worktree_build-step-rd178-step1-20260904083357` (~57 uncommitted entries): the two
  2026-09-04 recovery attempts the freeze file itself flagged as live and NOT digest-bound.
- `worktree_build-step-rd178-step1-1788570966` (2026-09-04 → 09-05): exhausted 3/3
  iterations; iteration 3 implemented the diagnosis's total-classifier + closed-WAL design
  (~+1,687 lines in the installer) but its verification stalled and it is unreviewed.
- `worktree_build-step-1788653371` (2026-09-05): a further full-scope Step-1 window
  (`--reviewers code --max-iter 3`); iteration 1 implemented the same structural design; its
  detached full root gate was still running, with at least one failure already visible, when
  this record was written. Its final gate summary is appended to #177 when available.

**Operator disposition:** all four windows are ratified retroactively **as evidence only**.
No candidate merges wholesale. Their dirty states are rescued to local branches (S3) and
named on #177 (which stays open per DS-D3). Because `.build-step/` is gitignored, each
rescue commit must force-add that sidecar directory (`git add -f .build-step`) — rescue
branches are local-only (DS-D11), so the machine paths inside sidecars never reach the
public remote. The corpus-import machinery in the newest window
(`import_corpus.py`, `import-facts.json`, the provenance generator) is preferred donor
material for the RD-lite build, subject to verify-before-apply. The structural installer fix
the two newest windows implement is preserved for any future codex-deep restoration (DS-D3).
The stale "NOT DISPATCHED" status prose is corrected by this record.

## 5. Execution plan

| # | Step | Mode | Depends on | Estimate |
|---|---|---|---|---|
| S1 | This record: written, approved, committed | serial | — | 1 session |
| S2 | Freeze lift (DS-D2) + resume notices | serial | S1 | short, same day |
| S3 | Worktree rescue and prune (DS-D11 + section 7 discipline; skip any tree a live process holds) | parallel-ok | S1 | 1-2 sessions |
| S4 | RD-lite build-step (DS-D3) + detached DONE gate | serial | S2 | 1-2 sessions + gate |
| S5 | Bookkeeping: issue sweep (DS-D10), known-gap notes, plan.md status rewrite | parallel-ok | S1 | 1 session |
| S6 | Amend Phase CL plan (DS-D7) + plan-review/plan-wrap | serial | S1 | 1-2 sessions |
| S7 | Build the CRUD rail: CL Steps 110-117, shared DONE gates per DS-D7(f) | serial | S4, S6 | 3-4 sessions + gates |
| S8 | Light proof on both hosts + acceptance note (DS-D9) | serial | S7 | 1-2 sessions |
| S9 | Closeout repo-update; baseline re-own; close #167. Track C (DS-D5) may then be re-priced | serial | S8 | short |

Unfreeze point: S2. External consumers' deep lane: after S4.

## 6. What this record does not change

The frozen Phase IS UAT blob and sealed C2V/C2A artifacts; the seven preserved evidence
worktrees and their digests; the DONE-gate definition and its single count owner (gate
CADENCE for Phase CL is amended by DS-D7(f); the gate itself is not); the product charter;
the public-repository redaction rules. Historical plans stay in place as history — S5
annotates status, it does not rewrite the past.

## 7. Carried-forward protected artifacts

Enumeration carried forward from the freeze file before its DS-D2 deletion (all at the dev
root unless noted). S3 and every later cleanup must honor this list; it replaces the deleted
file's `protected_paths` as the enumeration of record:

- The seven digest-bound preserved evidence worktrees/branches — authoritative list and
  digests: course-correction §3 (DS-D11; read-only, no rescue authorized).
- `worktree_build-step-1786993911` — pinned by open issue #138 (legacy-migrator hardening);
  stays until #138 is resolved.
- The two donor worktrees `skill-mesh-build-step-review-deep-capability-20260830220844` and
  `skill-mesh-build-step-review-deep-calibration-assets-20260830224727` are among the seven
  §3 digest-bound trees: the first bullet governs them and this record authorizes no
  retirement.
- `skill-mesh-review-output-20260830/` and `review-deep-source.zip` (non-worktree artifacts)
  — retained until RD-lite (S4) has landed and its import has been byte-verified against the
  import source; they may then be retired via the seed checklist.
- The four dirty Step-1 windows of section 4 — rescue-then-remove per S3 (rescue branches
  local-only per DS-D11).
- `worktree_build-step-prod184-20260901071930` and
  `worktree_build-step-prod184-declarative-20260901093602` — the PROD Step-1 window pair the
  freeze file protected (dirty, branches merged): rescue-then-remove per S3.
- Catch-all: any other worktree holding uncommitted state is rescued (commit to a local
  branch, recount with `--untracked-files=all` first) before removal; clean+merged trees may
  be removed directly.
- Re-enumerate worktrees with `git worktree list` before any prune; this class of list
  drifts whenever a build-step runs.
