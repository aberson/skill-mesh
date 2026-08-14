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
| Phase 0 — preserve work in progress and establish authority | IN PROGRESS | Step 72 passed; Step 73 is active |
| Phase 1 — two architecture experiments | LOCKED | Phase 0 completion |
| Gate A — select architecture | LOCKED | Abraham after both reports |
| Phase 2 — repair build controls | LOCKED | Gate A selects `proceed` and authorizes Goal B |
| Goal P — communication pilot | OPTIONAL/LOCKED | Gate A approval and Abraham opts in |
| Gate B — approve exact product steps | LOCKED | Abraham after control acceptance |
| Phases 3-7 — implement, prove, and rehearse | LOCKED | Gate B approval |
| Gate D — live cutover | LOCKED | Abraham after user acceptance testing and rehearsal |
| Board Track U — utility hookups | INDEPENDENT/LOCKED | Re-redline after Phase 2; implement against the release |
| Later Track L — skill decomposition | NOT NOW | Recovery completion |

## Current instruction

Goal A is active. Step 4 is durably preserved but remains frozen and unstaged. Execute only Steps 72-78 and stop at Gate A. Step 73 is the current action; product implementation and live-host mutation remain unauthorized.

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

**Status:** IN PROGRESS

**Completion procedure:** Commit the scoped authority candidate first. Add the named issue notes and record their URLs. Then make a `plan.md`-only terminal commit that marks Step 73 `DONE`, unlocks Step 74, and names the external `bootstrap.md` locator. Create `recovery/goala-20260814T021737Z-1b5ec416` and its clean worktree from that terminal commit. Write the terminal commit, branch, worktree, commands, and evidence hashes to `bootstrap.md`. If any post-commit action fails, mark Step 73 `BLOCKED` and do not start Step 74.

### Step 74: Prepare the lifecycle fixture

**Status:** LOCKED

### Step 75: Run the lifecycle experiment

**Status:** LOCKED

### Step 76: Prepare the cross-family fixture

**Status:** LOCKED

### Step 77: Run the cross-family experiment

**Status:** LOCKED

### Step 78: Prepare Gate A

**Status:** LOCKED

## Gate A journal

**Status:** LOCKED
