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
| Goal A execution | DONE — AT GATE A | Steps 72-78 passed; no execution authority remains |
| Provider expansion | PARKED | A later operator decision must explicitly resume it |
| Phase 0 — preserve work in progress and establish authority | DONE | Steps 72-74 passed |
| Phase 1 — two architecture experiments | DONE | Step 78 packet and final gate passed |
| Gate A — select architecture | READY_FOR_OPERATOR | Abraham selects `stop` or the exact bounded follow-up |
| Phase 2 — repair build controls | LOCKED | Gate A selects `proceed` and authorizes Goal B |
| Goal P — communication pilot | OPTIONAL/LOCKED | Gate A approval and Abraham opts in |
| Gate B — approve exact product steps | LOCKED | Abraham after control acceptance |
| Phases 3-7 — implement, prove, and rehearse | LOCKED | Gate B approval |
| Gate D — live cutover | LOCKED | Abraham after user acceptance testing and rehearsal |
| Board Track U — utility hookups | INDEPENDENT/LOCKED | Re-redline after Phase 2; implement against the release |
| Later Track L — skill decomposition | NOT NOW | Recovery completion |

## Current instruction

Goal A Steps 72-78 are complete. No execution action is authorized. Gate A is ready for Abraham.
`Proceed` is invalid because every load-bearing result is `AMBIGUOUS`. Abraham can select `stop` or
approve the exact bounded follow-up in `documentation/decisions/gate-a.md`. Product implementation,
Step 4 use, Phase 2, and live-host mutation remain unauthorized.

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

**Status:** DONE

**Candidate commit:** `0c72392ec51da5201c4f3c17272e2b79a32a055d`

**Superseded candidates:** `3a17746fa1d04c24088effd8f3871afe10f1601f`,
`0d06c42916f8953ec37f1a96e89b8a37cf82a77b`

**Evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\evidence-index.md`

**Preflight evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\step75-preflight-timeout.md`

The first Step 75 command stopped before creating an evidence directory, disposable home, or host
process. A read-only diagnostic measured 141 seconds to hash 2.93 GB across 41,435 protected
records. Executed candidate `3a17746fa1d04c24088effd8f3871afe10f1601f` uses fixed 600-second
and 630-second bounds. It passed the exact 262-test focused and package-integrity gate plus three
independent reviews. After the Step 78 full gate exposed a structural mutation-containment gap, the
new candidate `0c72392ec51da5201c4f3c17272e2b79a32a055d` passed the 28-test lifecycle suite,
the 9-test path-choke suite, the ASCII and private-path gates, and two independent reviews. It has
not run against either live host. Full-root coverage and the 100,000-record limit remain unchanged.

### Step 75: Run the lifecycle experiment

**Status:** DONE — both host series returned `AMBIGUOUS` before host invocation

**Executed candidate:** `3a17746fa1d04c24088effd8f3871afe10f1601f`

**Claude evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\lifecycle\lifecycle-claude-20260814T065643Z-e1ea3dd1\a0\report.md`

**Codex evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\lifecycle\lifecycle-codex-20260814T065645Z-34c7074f\a0\report.md`

Protected Codex database files changed during both safety-preflight intervals; attribution is
unavailable. The runner retained valid reports and manifests, removed each disposable home, and
launched no host command. These runs do not support a native-lifecycle conclusion.

### Step 76: Prepare the cross-family fixture

**Status:** DONE

**Candidate commit:** `7b094897a0e7afc4ffecaeac15f20d2d875614c8`

**Superseded candidate:** `8db941720cccbdf28dc1eadb32d51bf3c8c91550`

**Evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\evidence-index.md`

The fixture uses one deterministic synthetic candidate for both directions. This isolates the review handoff. It does not claim that a live Claude-family or GPT-family builder authored the candidate.

The exact final bytes passed 41 focused tests, the private-path gate, PowerShell parsing, and `git diff --check`. Three independent read-only reviews passed each bounded correction. No reviewer host, model, or protected live-home scan ran during candidate preparation.

The first Step 77 `a0` attempt stopped before reviewer launch because its complete 41,437-record snapshot was 19,750,121 bytes, above the 16 MiB general evidence cap. The retained report is `AMBIGUOUS`. The replacement candidate gives only raw snapshot files a separate 64 MiB cap. All other evidence keeps the 16 MiB cap. The 100,000-record and 600-second safety bounds do not change.

The two manual `a1` attempts both started exactly one contained host and cleaned the disposable fixture. Codex refused its intentionally empty working directory because `--skip-git-repo-check` was absent. Claude rejected the standard schema's draft declaration before review. Neither attempt produced a model review. The final correction is limited to those two native CLI preflight mismatches; isolation, model selection, fallback, evidence, and snapshot rules do not change.

### Step 77: Run the cross-family experiment

**Status:** DONE — all four final series returned `AMBIGUOUS`

**Evidence root:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\`

**Retained `a0` report:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-claude-to-gpt-manual-saved-handoff-20260814T085608Z-cbbf95ed\a0\report.md`

**Retained Codex `a1` report, requested `gpt-5.6-terra`:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-claude-to-gpt-manual-saved-handoff-20260814T085608Z-cbbf95ed\a1\report.md`

**Retained Claude-host `a1` report, requested `sonnet`:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-gpt-to-claude-manual-saved-handoff-20260814T085608Z-ec7c31e9\a1\report.md`

**Final manual Codex report, requested `gpt-5.6-terra`:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-claude-to-gpt-manual-saved-handoff-20260814T085608Z-cbbf95ed\a2\report.md`

**Final manual Claude-host report, requested `sonnet`:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-gpt-to-claude-manual-saved-handoff-20260814T085608Z-ec7c31e9\a2\report.md`

**Final dispatcher Codex report, requested `gpt-5.6-terra`:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-claude-to-gpt-reviewer-only-dispatcher-20260814T085608Z-40b14e58\a0\report.md`

**Final dispatcher Claude-host report, requested `sonnet`:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-gpt-to-claude-reviewer-only-dispatcher-20260814T085608Z-c450d8b6\a0\report.md`

Both Codex runs requested `gpt-5.6-terra`, completed one real review, returned `NEEDS_WORK`, and
detected all three seeded defects. Codex exposed no allowlisted resolved-model field. Protected
database files changed during both intervals; attribution is unavailable. Both Claude-host runs
requested `sonnet` and returned `401` because the saved OAuth token had expired. All four attempts
proved Job Object containment and disposable cleanup. The correction-attempt budget is exhausted.

### Step 78: Prepare Gate A

**Status:** DONE

**Lifecycle summary:** `documentation/evidence/goal-a/goala-20260814T021737Z-1b5ec416/lifecycle-report.md`

**Cross-family summary:** `documentation/evidence/goal-a/goala-20260814T021737Z-1b5ec416/cross-family-report.md`

**Summary manifest:** `documentation/evidence/goal-a/goala-20260814T021737Z-1b5ec416/MANIFEST.sha256`

**Decision packet:** `documentation/decisions/gate-a.md`

**External full gate:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\gate-a-full-gate.md`

The two committed summaries are bound by SHA-256. Every recommendation cites the raw reports and
manifests. Focused experiment and package-integrity tests passed. Both distributions built. The
repository-root full gate passed on the final Goal A candidate recorded in the external report.

## Gate A journal

**Status:** READY_FOR_OPERATOR

**Proceed eligibility:** INVALID — every load-bearing result is `AMBIGUOUS`.

**Recommended action:** `bounded-follow-up-experiment` named
`goal-a-quiescent-qualification-v1` in `documentation/decisions/gate-a.md`.

**Alternative:** `stop`.

Only Abraham can choose. Phase 2, product implementation, Step 4 use, and live cutover remain locked.
