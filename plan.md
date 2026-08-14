# Skill Mesh plan

## Goal

Deliver materially consistent Skill Mesh workflows in Claude Code and Codex. Show model and fallback evidence, prove one real cross-family review, and keep cutover recoverable.

## Main execution plan

Use `documentation/skill-mesh-recovery-plan.md` for requirements, step contracts, operator gates, proof, and rollback.

The approved product boundary is `documentation/product-charter.md`. The proposed operator-facing communication pilot is `documentation/operator-communication-profile.md`.

## Progress

| Unit | Status | Who or what unlocks it |
|---|---|---|
| Decision redline D1-D15 | APPROVED 2026-08-13 | Recorded in the recovery plan |
| Communication profile D16 | PROPOSED PILOT | Optional Goal P Steps 95-97; Phase 7 records the final choice |
| Goal A execution | IN PROGRESS | Abraham approved normalized blob `d97b1960b01673ab8922adc806f7c0de76ba33a3` on 2026-08-13 |
| Provider expansion | PARKED | A later operator decision must explicitly resume it |
| Phase 0 — preserve work in progress and establish authority | DONE | Steps 72-74 passed |
| Phase 1 — two architecture experiments | IN PROGRESS | Steps 75 and 76 are ready |
| Gate A — select architecture | LOCKED | Abraham after both reports |
| Phase 2 — repair build controls | LOCKED | Gate A selects `proceed` and authorizes Goal B |
| Goal P — communication pilot | OPTIONAL/LOCKED | Gate A approval and Abraham opts in |
| Gate B — approve exact product steps | LOCKED | Abraham after control acceptance |
| Phases 3-7 — implement, prove, and rehearse | LOCKED | Gate B approval |
| Gate D — live cutover | LOCKED | Abraham after user acceptance testing and rehearsal |
| Board Track U — utility hookups | INDEPENDENT/LOCKED | Re-redline after Phase 2; implement against the release |
| Later Track L — skill decomposition | NOT NOW | Recovery completion |

## Current instruction

Goal A is active. Step 4 is durably preserved but remains frozen and unstaged. Execute only Steps 72-78 and stop at Gate A. Steps 75 and 76 are ready; product implementation and live-host mutation remain unauthorized.

## Goal A journal

This section records status and evidence only. Acceptance remains in `documentation/skill-mesh-recovery-plan.md`.

**GoalAId:** `goala-20260814T021737Z-1b5ec416`

**Approved contract blob:** `d97b1960b01673ab8922adc806f7c0de76ba33a3`

**Approval:** Abraham approved continuation against this normalized blob in the Goal A session on 2026-08-13.

**Planned branch:** `recovery/goala-20260814T021737Z-1b5ec416`

**Planned worktree:** `%LOCALAPPDATA%\SkillMesh\Worktrees\goala-20260814T021737Z-1b5ec416`

### Step 72: Preserve the exact Step 4 work

**Status:** DONE

**Evidence:** `%LOCALAPPDATA%\SkillMesh\Recovery\skill-mesh-step-4-20260814T021546Z-73e9e215\manifest.json`

The manifest records 14 files, `apply_check=PASS`, `hash_match=PASS`, and the unchanged source index hash. A pre-destination PowerShell stderr failure is retained under `%LOCALAPPDATA%\SkillMesh\Recovery\skill-mesh-step-4-preflight-failure-20260814T021521Z-64adbbf1\`.

### Step 73: Establish canonical plan authority

**Status:** DONE

**Authority commit:** `8d8b57a`

**Issue notes:** [#70](https://github.com/aberson/skill-mesh/issues/70#issuecomment-5288812441), [#71](https://github.com/aberson/skill-mesh/issues/71#issuecomment-5288812561), [#72](https://github.com/aberson/skill-mesh/issues/72#issuecomment-5288812663), [#73](https://github.com/aberson/skill-mesh/issues/73#issuecomment-5288812790), [#74](https://github.com/aberson/skill-mesh/issues/74#issuecomment-5288812922), [#75](https://github.com/aberson/skill-mesh/issues/75#issuecomment-5288813029), [#76](https://github.com/aberson/skill-mesh/issues/76#issuecomment-5288813128), [#77](https://github.com/aberson/skill-mesh/issues/77#issuecomment-5288813238), [#78](https://github.com/aberson/skill-mesh/issues/78#issuecomment-5288813348), [#79](https://github.com/aberson/skill-mesh/issues/79#issuecomment-5288813499), [#80](https://github.com/aberson/skill-mesh/issues/80#issuecomment-5288813627), [#81](https://github.com/aberson/skill-mesh/issues/81#issuecomment-5288813730), [#82](https://github.com/aberson/skill-mesh/issues/82#issuecomment-5288813810), and [#116](https://github.com/aberson/skill-mesh/issues/116#issuecomment-5288813896).

**Bootstrap evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\bootstrap.md`

### Step 74: Prepare the lifecycle fixture

**Status:** IN PROGRESS — returned after the first Step 75 preflight exceeded the reviewed snapshot bound

**Superseded candidate:** `0d06c42916f8953ec37f1a96e89b8a37cf82a77b`

**Evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\evidence-index.md`

The first Step 75 command stopped before creating an evidence directory, disposable home, or host process. A read-only diagnostic measured 141 seconds to hash 2.93 GB across 41,435 protected records. The reviewed 120-second combined limit was therefore invalid. Step 74 is making a bounded timeout and candidate-identity correction; full-root coverage remains required.

### Step 75: Run the lifecycle experiment

**Status:** LOCKED — Step 74 correction in progress

### Step 76: Prepare the cross-family fixture

**Status:** LOCKED — Step 74 correction in progress

### Step 77: Run the cross-family experiment

**Status:** LOCKED

### Step 78: Prepare Gate A

**Status:** LOCKED

## Gate A journal

**Status:** LOCKED
