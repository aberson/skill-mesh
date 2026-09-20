# Phase CD — Codex code-deep review unblock plan

**Status:** BUILD READY — plan-review and plan-wrap passed on 2026-09-19; Phase CD #221, Step 155/#222, and Step 156/#223 are open; implementation remains unstarted.

## 1. What This Feature Does

Provide a capability-conditioned Codex mapping for the existing `review-deep` code lane so a host that proves fresh sibling dispatch and parent-only verdict authority can perform the six required independent lenses. This is the separate reviewed restoration plan required by DS-D3; it preserves the historical descope record, narrowly unblocks Phase LH Step 153 only after Step 156, and does not revive the superseded two-host/runtime workflow or claim support on an ordinary Codex CLI host.

## 2. Existing Context

`skills/review-deep/core.md` owns the six-lens, evidence-backed, deterministic review contract. Its Codex adapter intentionally refuses every invocation today, even though the active build-step/build-phase adapters already define a tested capability-conditioned fresh-child and parent-private verdict-service contract. `review-deep`'s deterministic audit sidecar is not itself a signed build verdict: when the lane is invoked by build-phase, the existing parent-owned service authenticates the enclosing build-step verdict. `review-deep` already has its emitted calibration and script support assets through the existing manifest row; no asset or installer topology is needed for this scope.

### Terms and existing contract

- **Phase CD** means this narrowly-scoped Codex deep-review unblock phase. Its Step 155 and Step 156 numbers follow the active Phase LH range without changing Phase LH's product interface.
- **DS-D3** is the operator-approved descope decision that left Codex `review-deep` fail-closed and requires a separate reviewed plan before restoring it; this plan is that proposal, not a rewrite of the historical record.
- **Phase LH Step 153** is the current explicit mistake-capture implementation step. Its `--reviewers deep` flag is the consumer this plan may unblock only after the native proof in Step 156.
- **`build-phase`** orchestrates plan steps and supplies parent-private verdict authority; **`build-step`** performs a code step in a worktree and invokes the requested review lane. The acceptance route is therefore `build-phase -> build-step --reviewers deep -> review-deep`.
- **`review-deep`** dispatches six isolated code lenses: correctness, bugs, security, test quality, style/conventions, and plan conformance. It aggregates their cited evidence into `.review-deep/<timestamp>.json`, whose relevant shape is a stable six-entry `lens_verdicts` list and an `aggregated_verdict` result. This audit file is deterministic but unsigned.
- The enclosing build-step verdict is a different temporary sidecar, authenticated with an HMAC (a keyed integrity signature) retained by the build-phase parent service. The key, verdict path, run id, and service handle never enter lens prompts, arguments, files, logs, or reports.

`review-deep` audit sidecar shape used by this plan:

| field | type | role |
|---|---|---|
| `lens_verdicts` | ordered list of 6 objects | one object per required code lens; each includes `lens_id`, `findings`, and `overall_verdict` |
| `aggregated_verdict` | object | deterministic `result` and rationale derived from retained cited findings |

Enclosing build-step verdict shape used by the parent service:

| field | type | role |
|---|---|---|
| `run_id` | parent-minted opaque random string | binds one code-step verdict; never passed to a lens |
| `result` / `halt` / `summary` | terminal fields | the normalized aggregate outcome, halt state, and bounded operator-facing reason |
| `signature` | HMAC-SHA256 string | authenticates the parent-written verdict; lenses cannot create it |

## 3. Scope

In: code-only `review-deep` on a Codex host that passes the existing fresh-context/parent-authority probe; generated-profile coverage; a disposable installed-host qualification; and the documentation/tests that prevent capability claims from drifting. The source mapping remains unqualified until Step 156 records successful native proof.

Out: a provider-wide Codex-support claim, runtime/full review lanes, new package assets, manifest or installer changes, a real daily-profile install, Claude parity, model benchmarking, and any change to Phase LH's capture/harvest interface.

## 4. Impact Analysis

| File | Change type | Reason | Verified |
|---|---|---|---|
| `skills/review-deep/providers/codex.md` | modify | Replace the wrapper's unconditional DS-D3 refusal with a fail-closed mapping for a capable host. | Current adapter explicitly says it maps no fresh-context fan-out. |
| `skills/review-deep/core.md` | verify unchanged | Keep host-specific orchestration in the Codex adapter; the core already requires six fresh-context lenses and deterministic aggregation. | The current core owns the needed review semantics and does not need a host-specific fallback. |
| `tests/package-integrity/test_codex_capability_claims_honesty.py` | modify | Move `review-deep` from its special unconditional-refusal assertion to a capability-conditioned positive contract. | The test names `review-deep`'s DS-D3 halt as a pinned exception. |
| `tests/package-integrity/test_codex_agent_isolation_contract.py` | extend | Prove the review-deep mapping cites and preserves the existing child-freshness and parent-authority boundary. | The current gate validates those boundaries for build-step/build-phase only. |
| `tests/distributions/test_distributions.py` | extend | Assert that the emitted Codex review-deep entry point carries the qualified mapping and its existing support closure. | The suite already enumerates emitted `review-deep` packages. |
| `documentation/providers/codex.md`, `documentation/providers/README.md`, `documentation/troubleshooting.md`, `plan.md` | modify | Replace the unconditional-halt wording with the precise source-mapping and qualification state: ordinary hosts still halt, and Phase LH remains blocked until Step 156 records native proof. | All currently document the unconditional halt. |
| `documentation/codex-deep-review-unblock-acceptance.md` | create | Provide the exact disposable install and fresh-host proof used before Phase LH relies on the lane. | No narrow acceptance procedure exists for this scope. |

## 5. New Components

No new runtime helper, dependency, package asset, manifest record, or installer behavior is introduced. The new acceptance document is an operator procedure, not a runtime artifact.

## 6. Design Decisions

1. **Reuse the existing capability boundary.** The Codex mapping may dispatch six direct, fresh sibling lenses only after the parent has passed the same no-history conversation challenge used by build-step/build-phase. A failed or inconclusive probe returns `required_tool_missing`.
2. **Keep verdict authority in the parent.** Lenses write evidence/recommendations only; the review-deep parent runs the mechanical pre-pass and deterministic aggregator. When build-phase invokes the lane, its existing parent-only verdict service separately authenticates the enclosing build-step verdict. The review-deep audit sidecar is never represented as that signed verdict channel. Shared filesystem access is not treated as isolation.
3. **Use a one-time ordinary code-review bootstrap.** The adapter that restores deep review cannot grade itself. Step 155 therefore uses the existing independent `--reviewers code` lane, with a fixed three-round limit; it is not a downgrade for Phase LH.
4. **Qualify only a disposable installed host.** Step 156 proves the exact generated `build-phase -> build-step --reviewers deep -> review-deep` route in a new host session against a harmless temporary Git fixture. It separately checks the six-lens audit sidecar and the enclosing authenticated build-step verdict. It never changes a daily profile, and passing it establishes only this code-lane mapping.

## 7. Build Steps

<!-- autofix-applied: 2026-09-19 -->
### Step 155: Implement a capability-conditioned Codex code-deep mapping

- **Problem:** Codex `review-deep` refuses unconditionally although this host exposes an independently testable fresh-child and parent-authority contract.
- **Type:** code
- **Status:** TODO
- **Issue:** #222
- **Flags:** --reviewers code --isolation worktree --max-iter 3
- **Files:** `skills/review-deep/providers/codex.md`; `tests/package-integrity/test_codex_capability_claims_honesty.py`; `tests/package-integrity/test_codex_agent_isolation_contract.py`; `tests/distributions/test_distributions.py`; `documentation/providers/codex.md`; `documentation/providers/README.md`; `documentation/troubleshooting.md`; `plan.md`; `documentation/codex-deep-review-unblock-acceptance.md`. Verify that `skills/review-deep/core.md`, the manifest, installer, and shared verdict helper remain unchanged.
- **Produces:** A Codex adapter that dispatches all six code lenses as direct fresh siblings only after the inherited capability probe passes; emitted-profile and planted-negative tests; and a precise disposable-host acceptance procedure for the nested build-phase route.
- **Done when:** The source and emitted adapter preserve parent-only aggregation authority; all six lens prompts are read-only and cannot see private verdict material; every missing, malformed, uncertain, incomplete, or unsupported state fails closed with `required_tool_missing` or `NEEDS-WORK`; the review-deep audit sidecar is kept distinct from build-phase's authenticated build-step verdict; documentation says the mapping remains unqualified until Step 156 and never claims provider-wide support; focused tests, all-provider builds, repository-root `python -m pytest`, and `git diff --check` pass for the exact candidate.
- **Depends on:** none

<!-- autofix-applied: 2026-09-19 -->
### Step 156: Qualify the generated Codex code-deep mapping in a disposable host

- **Problem:** Source tests cannot prove a fresh installed Codex host loads the revised adapter or actually runs six isolated lenses.
- **Type:** operator
- **Status:** TODO
- **Issue:** #223
- **Files:** `documentation/codex-deep-review-unblock-acceptance.md` (read-only procedure); `plan.md` (qualified-state result only); and this plan's Step 156 status only.
- **Produces:** A bounded acceptance verdict and sanitized evidence for the generated profile; no source or configuration artifacts.
- **Done when:** The normal installer writes only to a disposable home, a new Codex session loads the generated build-phase entry point, and a harmless temporary-Git fixture plan completes `build-phase -> build-step --reviewers deep -> review-deep`: the capability probe passes; all six fresh code lenses run; review-deep writes its deterministic audit sidecar; and the enclosing parent writes an authenticated build-step verdict through the existing verdict service. Cleanup leaves the real profile untouched. Any unavailable model, child-dispatch defect, audit-sidecar defect, verdict-service/authentication defect, or incomplete lens set is recorded as incomplete rather than treated as support.
- **Depends on:** 155

## 8. Risks and Open Questions

| Risk | Mitigation |
|---|---|
| The current session retains the old adapter | Require a fresh installed Codex session in Step 156; do not use a source edit as runtime proof. |
| A host exposes child spawn but not parent-private verdict authority | Reuse the full capability probe and fail closed before lens dispatch. |
| The new adapter self-certifies | Bootstrap Step 155 with the independent ordinary code-review lane and require fresh-host evidence afterward. |
| Documentation overstates support | Keep the mapping host-conditioned and retain the ordinary-CLI `required_tool_missing` outcome. |

## 9. Testing, Setup, and First Run

Toolchain coverage is explicit: no dependency install is needed because this changes no dependency; no dev server is applicable because the feature is a headless skill mapping; the build command is `powershell -NoProfile -File tools/build-distributions.ps1 -Provider all`; focused tests cover the two package-integrity contracts and Codex distribution closure; the DONE gate is repository-root `python -m pytest`; lint and typecheck are deliberately not configured in this repository; `git diff --check` is the final diff gate.

Step 155 adds source, generated-distribution, and planted-negative coverage for the conditional mapping. Run these commands from the Skill Mesh root in this order:

1. `python -m pytest tests/package-integrity/test_codex_capability_claims_honesty.py tests/package-integrity/test_codex_agent_isolation_contract.py`
2. `powershell -NoProfile -File tools/build-distributions.ps1 -Provider all`
3. `python -m pytest tests/distributions/test_distributions.py`
4. `python -m pytest`
5. `git diff --check`

The prepared acceptance document must give exact setup, fixture, invocation, evidence, and cleanup commands: create a temporary Git repository and disposable Codex home; install the generated Codex profile only into that home; start a new Codex session; invoke its `build-phase` entry point on a one-step harmless fixture plan that declares `--reviewers deep`; verify the six-lens review-deep audit sidecar and the distinct parent-authenticated build-step verdict; and remove only the disposable paths. Step 156 is the only native-host proof. This feature is a one-shot invocation path, not a background or scheduled system; no soak phase is required. Phase LH Step 153 resumes only after Step 156 passes and `plan.md` records that qualified state.
