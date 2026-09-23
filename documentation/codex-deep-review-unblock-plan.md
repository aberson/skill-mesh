# Phase CD — Codex code-deep review unblock plan

**Status:** Step 155 source accepted under the bounded amendment below; Step 156's
single installed-proof attempt is in progress. Main `2e7f325` contains the exact
17 non-plan files from reviewed candidate `4a967f0`. The earlier source workflow's
signed terminal PASS was not established; this is source acceptance under an
explicit changed criterion, not a replayed workflow PASS. Installed capability
still requires its own observed proof and normal activation.

**Historical stop, 2026-09-23:** Independent code review passed in amended round
2/3 and focused checks passed, but the full-root suite was operator-stopped after
101.7 minutes (27% last reported progress). It remains INCOMPLETE/deferred, with
no passing or failing test verdict. Reviewed `4a967f0` is preserved on the
[paused candidate branch](https://github.com/aberson/skill-mesh/tree/paused/cd155-operator-stop-20260923)
and in its local worktree. The earlier exhausted 3/3 attempt is also preserved.
Phase CD #221, Step 155/#222 and Step 156/#223 retain their identities.

**Bounded resumption amendment (2026-09-23):** The operator subsequently requested
that Agent Advocate's build invocation become usable without repeating the testing
overrun. That request supersedes the pause for this prerequisite only. The agent
selects the narrow validation exception below; it is not an operator-selected test
waiver or a passing full-suite result. Reuse unchanged candidate
`4a967f0705fdbde98694d9eaf4808b66169345af`, its focused receipts and five final
independent PASS reviews. Do not restart implementation, reviews or the root suite.
Step 156 gets **one 20-minute total attempt**, including disposable setup, native
proof, normal profile refresh and cleanup. A failure, timeout, unavailable capability
or ownership conflict stops this attempt without a repair/retest loop. Agent
Advocate implementation remains for a subsequent invocation.

## 1. What This Feature Does

Provide a capability-conditioned Codex mapping for the existing `review-deep` code lane so a host that proves fresh sibling dispatch and parent-only verdict authority can perform the six required independent lenses. The operator requested that this recurring prerequisite failure be addressed before continuing Agent Advocate. This remains the owning restoration plan required by DS-D3; reuse it rather than create another adapter in a consumer project. It unblocks capable Codex consumers, including Agent Advocate Steps 1/3 and Phase LH Step 153, only after actual installed-host proof. A separately qualified Claude route remains distinct.

Proposal: [codex-deep-review-unblock-proposal.html](codex-deep-review-unblock-proposal.html)

## 2. Existing Context

`skills/review-deep/core.md` owns the six-lens, evidence-backed, deterministic review contract. Its Codex adapter intentionally refuses every invocation today, even though build-step/build-phase already define a capability-conditioned fresh-child and parent-private verdict-service contract. `review-deep`'s deterministic audit sidecar is not a signed build verdict: build-phase's existing parent-owned service authenticates the enclosing build-step verdict.

The September 23 source audit found two additional blockers. First, `support_assets` in the manifest describes legacy-to-canonical migration; the distribution builder does not emit those files. Both generated and installed review-deep packages contain only SKILL.md and core.md. Second, the core demands six reviewers in a single parallel batch, while the inspected host has four total agent slots. The repair must ship the code-lane helpers and permit capacity-limited batches without changing reviewer independence or lens completeness.

### Terms and existing contract

- **Phase CD** means this narrowly-scoped Codex deep-review unblock phase. Its Step 155 and Step 156 numbers follow the active Phase LH range without changing Phase LH's product interface.
- **DS-D3** is the operator-approved descope decision that left Codex `review-deep` fail-closed and requires a separate reviewed plan before restoring it; this plan is that proposal, not a rewrite of the historical record.
- **Consumers** include Agent Advocate Steps 1/3 and Phase LH Step 153. Their required deep gates remain intact. A separately qualified Claude route is outside this Codex proof's dependency chain; model or host changes require existing authorization, not an automatic fallback.
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

In: code-only `review-deep` on a Codex host that passes the existing fresh-context/parent-authority probe; explicit code-lane resource packaging; capacity-aware independent dispatch; generated-profile coverage; installed-host qualification; and normal Codex profile refresh after proof. The source mapping remains unqualified until Step 156 records successful native proof. This is the scoped packaging plan required by the catalog lifecycle's `PACKAGE_RESOURCE_PLAN_REQUIRED` boundary.

Out: a provider-wide Codex-support claim, runtime/full review qualification, a general resource/plugin framework, new canonical helper code, manifest schema or installer redesign, Claude parity, model benchmarking, and any change to Phase LH's product interface. Existing in-repository calibration remains unchanged; this plan does not claim an installed calibration command.

## 4. Impact Analysis

| File | Change type | Reason | Verified |
|---|---|---|---|
| `skills/review-deep/providers/codex.md` | modify | Replace the wrapper's unconditional DS-D3 refusal with a fail-closed mapping for a capable host. | Current adapter explicitly says it maps no fresh-context fan-out. |
| `skills/review-deep/providers/gpt.md` | modify resource reference only | Point installed readers at the emitted tier-map document without changing GPT gate behavior. | Line 9 reads the same tier-map resource; all-provider generation must not leave that reference stale. |
| `skills/review-deep/core.md` | modify narrowly | Resolve resources from the loaded package, and allow available-slot batches of independent lenses. | Lines 5/104 bind a Claude root and a single six-agent batch; sections Model strategy, Aggregation and Tools consume the named resources. Severity and reducer semantics remain unchanged. |
| `tools/build-distributions.ps1` | extend | Emit the existing code-lane resource closure for every generated provider that includes review-deep. | Current emission handles launcher/core, shared prose and the build verdict helper, but never consumes manifest support_assets as installed resources. |
| `tools/skill-mesh-provenance.ps1` | extend shell syntax only | Keep the existing provenance block valid in an executable shell file and recognized by the existing installer. | Existing preamble recognition accepts Markdown, JS and Python placements only; the installer rejects unrecognized generated resources. No raw-JSON provenance protocol is introduced. |
| `skills/review-deep/scripts/{aggregate.py,lint_prepass.sh,README.md}`, `skills/review-deep/config/model-tier-map.json` | verify source unchanged; emit derived resources | These four existing inputs are the explicit code-lane allowlist; the map emits as `config/model-tier-map.md` with a single fenced JSON payload. | Core sections Model strategy, Aggregation and Tools reference them; the map has no runtime machine consumer in this package. The existing snapshot drift tests remain intact. |
| `tests/package-integrity/test_codex_capability_claims_honesty.py` | modify | Move `review-deep` from its special unconditional-refusal assertion to a capability-conditioned positive contract. | The test names `review-deep`'s DS-D3 halt as a pinned exception. |
| `tests/package-integrity/test_codex_agent_isolation_contract.py` | extend | Prove the review-deep mapping cites and preserves the existing child-freshness and parent-authority boundary. | The current gate validates those boundaries for build-step/build-phase only. |
| `tests/distributions/test_distributions.py` | extend | Exercise emitted helpers from installed paths, map parity and references, valid shell syntax/provenance, missing-resource negatives, and normal install/reinstall/uninstall ownership. | The suite already enumerates emitted packages and provenance; source-file existence alone cannot prove distribution closure or safe lifecycle handling. |
| `documentation/providers/codex.md`, `documentation/providers/README.md`, `documentation/troubleshooting.md`, `documentation/architecture.md`, `documentation/skill-catalog-lifecycle.md`, `plan.md` | modify relevant current statements | Describe source mapping versus qualification, the narrow resource-packaging exception, and the continued unsupported-host outcome. | Architecture describes support_assets as migration ownership; the lifecycle guide currently says package-local support files are never emitted. Historical DS-D3 and historical review receipts remain unchanged. |
| `documentation/codex-deep-review-unblock-acceptance.md` | create | Provide the exact disposable install and fresh-host proof used before Phase LH relies on the lane. | No narrow acceptance procedure exists for this scope. |

## 5. New Components

No new runtime helper, dependency, manifest record, or installer behavior is introduced. Existing canonical resources are copied by the normal builder and owned by the existing install ledger. The acceptance document is authored during Step 155; Step 156 only executes it and records results.

## 6. Design Decisions

1. **Reuse the existing capability boundary.** The Codex mapping may dispatch six direct, fresh sibling lenses only after the parent has passed the same no-history conversation challenge used by build-step/build-phase. A failed or inconclusive probe returns `required_tool_missing`.
2. **Keep verdict authority in the parent.** Lenses write evidence/recommendations only; the review-deep parent runs the mechanical pre-pass and deterministic aggregator. When build-phase invokes the lane, its existing parent-only verdict service separately authenticates the enclosing build-step verdict. The review-deep audit sidecar is never represented as that signed verdict channel. Shared filesystem access is not treated as isolation.
3. **Use a one-time ordinary code-review bootstrap.** The adapter that restores deep review cannot grade itself. Step 155 therefore uses the existing independent `--reviewers code` lane, with a fixed three-round limit; it is not a downgrade for Phase LH.
4. **Match scheduling to real capacity.** Retain all six distinct fresh sibling lenses, launched directly by the review parent with explicit no-history dispatch. Run as many as current slots permit, then launch fresh siblings for the remaining lenses. Every lens receives the same immutable diff/intent snapshot and its own lens instructions, never another lens's output or producer reasoning. Aggregate only after the full required set returns. Capacity changes scheduling, not gate strength; no new scheduler service is needed.
5. **Ship a narrow resource closure.** The builder uses the four-input allowlist in section 4, with paths resolved and checked inside the canonical review-deep package. Missing resources fail the build; no arbitrary glob, out-of-tree lookup or consumer-file hand edit is allowed. Emit the map as Markdown with the existing provenance header and one fenced JSON object; parse it in tests and compare exactly with the source mapping. Update the core/GPT/Codex resource instructions to distinguish canonical JSON from the loaded package's Markdown representation. The standalone router continues reading its original root JSON unchanged. For `lint_prepass.sh`, preserve the shebang and wrap the existing verbatim provenance header in a quoted no-expansion shell no-op heredoc; extend the shared provenance emitter/recognizer together for that exact legal placement, including termination validation. Reject ordinary in-body quotations and malformed wrappers. Prove shell syntax, header recognition and normal ledger-owned install/reinstall/uninstall; provenance remains only one guard alongside path/ledger/current-byte checks. Runtime-only auth probing and calibration assets are not qualified by this change; in-repository source calibration remains unchanged.
6. **Qualify generated bytes, then refresh normally.** Step 156 first installs into a disposable home and demonstrates the actual nested route in a fresh capable host. Prefer a safe snapshot of already pending useful work as the review subject; a tiny harmless fixture is acceptable solely to exercise the signed workflow boundary. No productivity benchmark is required. Check the six-lens audit and enclosing authenticated verdict separately. Then refresh the intended Codex profile through the normal installer, verify installed ownership/hashes, and require the next consumer session to load those bytes and perform its own session capability check. Preserve foreign/local changes; do not force overwrite or claim support on a host that fails the probe.

## 7. Build Steps

<!-- autofix-applied: 2026-09-19 -->
### Step 155: Implement a capability-conditioned Codex code-deep mapping

- **Problem:** Codex `review-deep` refuses unconditionally although this host exposes an independently testable fresh-child and parent-authority contract.
- **Type:** code
- **Status:** DONE (source accepted under CD-D5; full suite INCOMPLETE/deferred; no signed source-workflow PASS claimed)
- **Issue:** #222
- **Flags:** --reviewers code --isolation worktree --max-iter 3
- **Files:** `skills/review-deep/providers/codex.md`; `skills/review-deep/providers/gpt.md`; `skills/review-deep/core.md`; `tools/build-distributions.ps1`; `tools/skill-mesh-provenance.ps1`; `tests/package-integrity/test_codex_capability_claims_honesty.py`; `tests/package-integrity/test_codex_agent_isolation_contract.py`; `tests/distributions/test_distributions.py`; `tests/package-integrity/test_skill_catalog_lifecycle.py` (only assertions affected by the explicit packaging exception); `documentation/providers/codex.md`; `documentation/providers/README.md`; `documentation/troubleshooting.md`; `documentation/architecture.md`; `documentation/skill-catalog-lifecycle.md`; `plan.md`; `documentation/codex-deep-review-unblock-acceptance.md`. Verify the four canonical helper/config source files, manifest, installer, standalone router and shared verdict helper remain unchanged.
- **Produces:** A Codex adapter that dispatches all six code lenses as direct fresh siblings after the inherited capability probe passes, using available-slot batches; generated code-lane resources with installed-path execution coverage; and the exact acceptance/install/resume procedure.
- **Done when:** The source and emitted adapter preserve parent-only aggregation; all six lens prompts are read-only and receive no private verdict material or sibling findings; missing/duplicate/malformed/incomplete lens sets and unsupported capability fail closed; uncertainty follows the unchanged reducer and cannot become PASS; missing declared helper sources fail generation; emitted helpers execute outside the source checkout; installed map payload equals the source JSON and all three provider references resolve; shell syntax/provenance and normal install/reinstall/uninstall preserve ownership and refuse foreign edits; the unsigned audit remains distinct from the signed build-step verdict; documentation keeps the mapping unqualified until Step 156. For the exact unchanged candidate identified above, reuse section 9's focused checks, all-provider builds and independent reviews, verify source identity and `git diff --check`, and explicitly retain the root suite as INCOMPLETE/deferred. This narrow acceptance does not certify the full repository or any live host.
- **Depends on:** none

The preserved candidate also includes the affected link-inventory assertion in
`tests/package-integrity/test_link_resolution.py` and the clarified installed
package locator in the existing plan-wrap receipt. This amendment additionally
updates `CLAUDE.md`, this plan and its proposal to make the scoped validation
exception discoverable to the next coordinator.

<!-- autofix-applied: 2026-09-19 -->
### Step 156: Qualify and activate the generated Codex code-deep mapping

- **Problem:** Source tests cannot prove a fresh installed Codex host runs the complete review, and a working disposable copy does not repair the consumer's old profile.
- **Type:** operator
- **Status:** TODO
- **Issue:** #223
- **Files:** `documentation/codex-deep-review-unblock-acceptance.md` (read-only procedure); `plan.md` (qualified-state result only); and this plan's Step 156 status only.
- **Produces:** Observed verdict, sanitized evidence, and a normal installer refresh of the intended Codex profile after successful disposable proof; no source, helper, or runbook authorship.
- **Done when:** A fresh capable host loads the generated disposable install and completes `build-phase -> build-step --reviewers deep -> review-deep`: the existing conversation and parent-authority probes pass; six distinct fresh lenses run in capacity-limited batches on identical review inputs; the packaged reducer writes its deterministic audit; the parent separately authenticates the enclosing build-step verdict. Then the normal installer refreshes the intended profile without overwriting foreign changes, and an ownership/hash check proves that profile contains the same qualified bytes. Record exactly which host/entry points were exercised and provide a fresh-session consumer resume prompt. Missing capability, incomplete lenses, invalid artifacts or installation conflicts leave the step incomplete; no switch to another host/model is implied.
- **Depends on:** 155

The enclosing 20-minute deadline applies to every action in Step 156, even if an
embedded fixture normally permits more rounds. Record start/deadline before setup;
check remaining time before each dispatch or install. Reserve time for cleanup and
do not begin a live-profile mutation without enough time to finish its ownership
check. Cleanup may finish after the deadline solely to release owned resources;
no further proof or installation work may start. A failed attempt stays incomplete.

## 8. Risks and Open Questions

| Risk | Mitigation |
|---|---|
| The current session retains the old adapter | Qualify a fresh installed session and verify the normal profile refresh; require consumer session preflight before resume. |
| A host exposes child spawn but not parent-private verdict authority | Reuse the full capability probe and fail closed before lens dispatch. |
| The new adapter self-certifies | Bootstrap Step 155 with the independent ordinary code-review lane and require fresh-host evidence afterward. |
| Documentation overstates support | Keep the mapping host-conditioned and retain the ordinary-CLI `required_tool_missing` outcome. |
| Six lenses exceed available slots | Explicit fresh-sibling batches, same sealed inputs, no cross-lens feedback, complete-set check before aggregation. |
| Source helpers never reach installed package | Execute generated/installed helpers outside the source checkout; verify ledger ownership rather than source-file existence. |
| Existing consumer work gets overwritten during unblock | Reconcile its worktree, latest review receipts and consumed rounds; preserve the candidate and resume its current repair, never restart or reset the budget. |

## 9. Testing, Setup, and First Run

This one-candidate exception replaces the former full-suite prerequisite; it does
not relabel a subset as the full suite. Existing private receipts under
`.build-step/cd155-amended-20260923/candidate-evidence/` record:

- `dev-report.md`: 109 affected integrity checks passed; 28 distribution checks
  passed; four parser/provenance/build-determinism checks passed; all three provider
  distributions built. The initial broader integrity run had four failures and is
  not a passing receipt; its fixes were checked by the named focused run.
- `dev-report-round2.md`: the planted negative failed on the old recipe as intended;
  the final distribution selection passed 20 checks and affected package selection
  passed nine. Only the adapter guard and its test changed after round 1; the other
  17 candidate files retained their identity.
- `review-r2-{correctness,bugs,security,test-quality,style}`: five independent PASS
  reviews, zero findings, frozen diff SHA-256
  `5b3bed17370a356d6f1bbae176be31378f58d9582d847442724adb0a827f78e2`.
- The final repo-root `python -m pytest` was stopped after 101.7 minutes and remains
  **INCOMPLETE/deferred**. It produced no failing-test verdict before interruption.

Verify unchanged source identity when integrating the preserved candidate. Plan,
proposal and instruction changes that document this exception do not invalidate
unchanged executable-source receipts. Any code change invalidates this exception
and requires a separately scoped decision, not an automatic new test campaign.
Run `git diff --check` once for the final amendment. No tests are required for its
prose. No dependency install, dev server, lint or typecheck is introduced.

Step 156 follows the already-reviewed acceptance document's exact setup, native
proof, evidence, normal installation and safe-cleanup commands under the single
20-minute total deadline. It builds the distribution needed for that actual proof;
it does not repeat distribution tests, the root suite, a soak or a benchmark.

After Step 156 passes, the consumer coordinator reloads the qualified profile, performs its session preflight and resumes the preserved candidate with its real retry history. Keep Agent Advocate's deep flags unchanged. This one-shot mapping repair does not start Phase LH or the broader Skill Mesh backlog, and cannot qualify an independently different host by analogy.

## 10. Appendix

### Decision Inventory

| ID | P/D | Choice | Status |
|---|---|---|---|
| CD-P1 | P | Restore a Codex-native deep lane without downgrading consumer gates | existing approved Phase CD direction |
| CD-P2 | P | Address recurring review unavailability before continuing Agent Advocate | requested 2026-09-23 |
| CD-P3 | P | Make the Agent Advocate build invocation usable without repeating endless testing | requested after the operator stop, 2026-09-23 |
| CD-D1 | D | Reuse the existing capability probe and parent verdict service | retained |
| CD-D2 | D | Permit fresh independent reviewer batches bounded by host capacity | selected 2026-09-23; six lenses retained |
| CD-D3 | D | Emit four existing code-lane inputs through the normal builder; Markdown map and shell-safe provenance | selected 2026-09-23; scoped packaging exception, no JSON protocol or installer redesign |
| CD-D4 | D | Disposable proof followed by normal profile refresh and consumer-session preflight | changed 2026-09-23 to repair the actual installed consumer |
| CD-D5 | D | Accept unchanged reviewed candidate using existing focused evidence; defer incomplete full suite for this repair only | agent-selected bounded validation exception, 2026-09-23 |
| CD-D6 | D | One 20-minute total proof/activation attempt; stop on failure without repair/retest loops | agent-selected execution bound, 2026-09-23 |
