# Codex deep-review restoration

## 1. What This Is

**Objective:** let a capable Codex host complete `build-step --reviewers deep` with
the existing six-lens review depth, recorded calibration, deterministic aggregation,
and an audit sidecar that the build coordinator can safely consume.

**Status:** PROPOSAL. Preparation was requested on 2026-09-08; implementation has
not started. This is a new plan under descope decision DS-D3, not a reopening of
the cut Phase RD queue. `plan.md` remains the execution-status owner.

Proposal: `documentation/codex-deep-review-restoration-proposal.html`

The immediate consumer has deep reviews at Steps 61, 62, and 65. Those flags stay
`--reviewers deep`; their earlier full-review steps retain their existing flags.
The checkpoint/fresh-context repair at `92f082118b695b9275cae6b06e0cb64b808ba0db`
is a prerequisite, including its full root gate, landing, and Codex installation.
Its focused checks and live probes do not certify this restoration.

## 2. Existing Landscape

Source inspection used candidate `92f0821`, based on synchronized main `ee6ae71`.
Re-read current `plan.md`, this plan, and `documentation/descope-2026-09.md` before
execution. Refresh immutable commit identities and file locations if main changes.

| Producer | Verified behavior and consequence |
|---|---|
| `skills/review-deep/providers/codex.md:9` | Explicitly refuses lens dispatch under DS-D3. Availability of `spawn_agent` alone does not activate it. |
| `skills/review-deep/core.md:102` | Requires independent correctness, bugs, security, test-quality, style, and plan-conformance lenses. The last lens skips only when no plan step is supplied. |
| `skills/review-deep/core.md:624` | One same-tier retry after a 30-second backoff; 180-second first-token timeout. The current Codex collaboration schema does not expose first-token timing. |
| `skills/review-deep/core.md:779` | Calibration replays committed labels/scores; it does not exercise live model quality or the current aggregator. |
| `skills/review-deep/scripts/aggregate.py:205` | Loads files by lens ID into a dictionary; duplicates overwrite and an incomplete nonempty set can reach aggregation. |
| `skills/review-deep/scripts/aggregate.py:695` | The reducer does not account for `UNCERTAIN` or `NEEDS-CLARIFICATION`; direct six-entry reproductions returned `PASS` for both. |
| `skills/review-deep/scripts/aggregate.py:1919` | The CLI passes `plan_step=None` and `invocation=None` to aggregation, losing invocation metadata. Exit zero means the command ran, not that review passed. |
| `_shared/calibrate_judge.py:848` | RD-lite already resolves the canonical review-deep corpus in a source checkout. It also accepts an explicit `--skill-dir`. |
| `tools/build-distributions.ps1:545` | Emits adapters/cores and a supported shared-file closure; it does not emit review-deep's raw JSON/corpus/script tree. |
| `tools/install-skill-mesh.ps1:927` | Existing ownership is a generated-header plus installed-hash contract. Raw package assets would reopen the excluded installer-authority work. |
| `skills/build-step/core.md:470` | Calls deep review once per iteration, passes plan-step and previous sidecar, then consumes the aggregate rather than running the gauntlet too. |

The preserved rescue branches are evidence only. In particular,
`rescue/worktree_build-step-rd178-step1-20260904083357` at `bff8aa2` contains the
earlier package/installer attempt; its change spans 83 files and includes the raw
asset index and write-ahead-log machinery. DS-D3's other rescue branches remain
listed in the descope record. Read relevant findings surgically; do not merge a
rescue branch, copy its private reports into public files, or treat its tests as
acceptance evidence for new code. The already-imported canonical corpus is the
starting asset set.

The paused catalog Step 111 and the unmerged plan-expedite handoff branch are
separate tracks. This plan does not modify either worktree. A Claude reinstall
continues to depend on that handoff branch landing; running existing Claude tools
does not authorize reinstalling them.

## 3. Scope

Restore the **code lane** of Codex deep review, including the build-step caller.
Use an explicitly configured, immutable local skill-mesh checkout for the review
helpers and calibration corpus. This first version is checkout-backed; an
installed package alone remains insufficient. Never search arbitrary parent
directories, infer an asset root from the consumer's cwd, or silently substitute
the legacy compatibility tree.

Also fix the aggregate's unsafe uncertainty/incomplete-input cases before making
the lane available, and preserve actual plan/invocation metadata in the sidecar.
Run a real installed Codex invocation before claiming host acceptance.

Out of scope: raw package distribution, manifest `package_assets`, package indexes,
installer or write-ahead-log redesign, source imports from the old upstream,
changed gold labels or timestamps, Codex runtime/full deep lanes, model-quality
benchmarking, local-model review, a new scheduler, and resuming the consumer build.
No consumer deep flag is downgraded. Runtime/full requests to this bounded Codex
adapter continue to return a specific missing-mapping explanation; they never
silently become code-only.

## 4. Impact Analysis

Paths marked **new** are proposed outputs, not claims that they already exist.

| File or consumer | Change | Reason / verified source |
|---|---|---|
| `skills/review-deep/scripts/aggregate.py` | Strict input-set validation, complete blocking ladder, metadata CLI | Existing loader, reducer, and CLI cited above |
| `skills/review-deep/scripts/README.md` | Match the executable CLI and failure behavior | Existing helper contract |
| `review-deep/scripts/aggregate.py`, `review-deep/scripts/README.md` | Mechanically synchronize canonical changes | Existing duplication gate; never independently author legacy copies |
| `skills/review-deep/core.md` | Correct reducer documentation; explicit host scheduling/timing mappings and source-asset abstraction | Invariants remain unchanged; shared semantics affect every provider |
| `skills/review-deep/providers/codex.md` | Conditional code-lane mapping, source readiness and fresh siblings | Replaces the DS-D3 unconditional halt only for the proved lane |
| `skills/build-step/providers/codex.md` | Same-parent named-skill mapping and deep-result validation | Prevents a nested producer/parent context or invented skill-dispatch dependency |
| `skills/build-step/core.md` | Explicit no-advance handling of uncertain deep reports, if needed at the shared caller | Deep normalization at lines 582 onward; no new passing terminal enum |
| `_shared/calibrate_judge.py`, `_shared/test_calibrate_judge.py` | Keep documented lens enum in sync if the aggregate contract changes | The calibration module mirrors the lens enum at line 120 |
| `tests/calibration/test_review_deep_aggregate_contract.py` (**new**) | Real aggregate CLI regressions and prior-sidecar round trip | No existing dedicated CLI contract test found in this directory |
| `tests/package-integrity/test_codex_capability_claims_honesty.py` | Replace only the DS-D3 unconditionality pin with conditional capability cases | Existing named pin at line 1758 |
| `tests/package-integrity/test_codex_agent_isolation_contract.py` | Cross-skill probe/caller coverage where the adapter contract changes | Existing isolation gates |
| `tests/package-integrity/test_review_deep_scripts_duplication.py` | Existing gate runs unchanged | Canonical/legacy normalized-byte agreement |
| `tests/distributions/test_distributions.py` | Check emitted code-lane instructions and disposable install behavior | Real builder/installer callers; no raw-asset expectation |
| `documentation/providers/codex.md`, `documentation/troubleshooting.md`, `documentation/providers/README.md` | Explain checkout-backed support and remaining gaps | Existing DS-D3 known-gap descriptions |
| `documentation/descope-2026-09.md`, `plan.md` | Append the bounded new decision and execution/evidence pointer | Preserve historical DS-D3; status has one owner |
| `documentation/release-candidate-report.md` | Regenerate when representative cores change | `build-step` is not representative; verify the actual fixture list if scope expands |
| `documentation/operator/codex-deep-review-smoke.md` (**new**) | Concrete live acceptance and rollback procedure | Prepared before the attended step |

The aggregate top-level result keeps the existing passing-wire vocabulary
`PASS | NEEDS-WORK | DEFERRED-TO-UAT`. The build-step authenticated verdict helper
needs no new enum. A lens's uncertainty remains visible in its own record and
forces `NEEDS-WORK` with an explicit uncertainty rationale; the caller stops for
escalation rather than automatically iterating the developer. This explicitly
resolves the current core's contradictory four-value output ladder versus its
three-value sidecar/caller contract. The shared core and caller are updated together.
Search all consumers of `overall_verdict`,
`aggregated_verdict`, `load_lens_verdicts`, and CLI flags again before changing a
signature. Do not count updated assertions as proof that the old behavior was safe.

## 5. New Components and Interfaces

No new service or database. This is an adapter plus deterministic helper repair.
The consumer's diff and source are review data; instructions embedded in either
must not control tools, reviewer routing, or the verdict channel.

### Asset configuration

Two operator/session configuration values are introduced:

| Name | Shape | Meaning |
|---|---|---|
| `SKILL_MESH_REVIEW_DEEP_ROOT` | Absolute directory, kept in local configuration only | Explicit trusted skill-mesh checkout; never embedded in committed documentation or public receipts |
| `SKILL_MESH_REVIEW_DEEP_COMMIT` | Full lowercase 40-hex Git commit ID | Immutable approved source version; branches and moving refs are rejected |

Before execution, require that the root is a Git worktree at that commit, its
tracked files are clean, the canonical core/adapter correspond to the loaded
emitted package, and all helpers/corpus inputs exist. Compare generated package
text using the existing builder's normalization and repointing, not raw source
text versus an emitted file. A dedicated pinned worktree makes upgrades explicit.
Never fetch, checkout, reset, or mutate this root during a review. Recheck identity
and cleanliness after review; any change invalidates the result.

Run calibration against the source root using its existing helper and explicit
canonical skill directory. Run the lint pre-pass with the **consumer project** as
cwd and an explicit changed-path list, while addressing its script by the validated
source root. Run the aggregate with explicit lens/output/prior-sidecar paths. Use
structured argv; no executable string assembly from diff, JSON, or findings.

The existing core's missing-individual-linter warning still applies. Missing
calibration data, a failed calibration, or a missing aggregate helper prevents
review. Record requested and resolved model identity where the host exposes it;
never infer resolved identity from a tier label. Honor explicit run model pins.

### Review records

`LensVerdict` keeps these fields from the existing producer. The constraints below
describe the new **Codex code-lane envelope**, not a restriction on other hosts'
existing runtime/full lanes:

| Field | Type | Constraint |
|---|---|---|
| `lens_id` | string | One of the six code-lens IDs, in canonical order |
| `model_tier` | string | `haiku`, `sonnet`, or `opus`: capability role, not claimed actual model identity |
| `authority`, `coverage_claim` | string | Nonempty lens scope and coverage statements |
| `findings` | array | Each finding has severity, file_line, excerpt, and rationale; never null |
| `overall_verdict` | string | `PASS`, `NEEDS-WORK`, `UNCERTAIN`, `NO-EVIDENCE`, `FAILED`, `SKIPPED`, or `NEEDS-CLARIFICATION` |
| `failure_reason` | string, only on `FAILED` | Existing `model_overloaded` for native 529/first-token-timeout exhaustion; proposed `completion_timeout` for D3's completion deadline |

`Finding` fields: `severity` is `Block | Nit | FYI`; `file_line` is a repository
relative path plus a positive line number/range, or the existing explicit
absence-of-thing form such as `(absence -- no integration test for X)`;
`excerpt` and `rationale` are strings. Absence findings still require nonempty cited
supporting evidence; do not erase them with a path-only validator. Optional
anti-pattern and post-aggregation annotations retain the core's
existing semantics. Missing evidence is dropped as the core requires, while a
lens that saw no diff cannot become an inferred PASS.

`ReviewInvocation` carries `reviewers_flag`, `model_overrides`, `force_runtime`,
`url`, `start_cmd`, `runtime_downgraded`, and `runtime_downgrade_reason` with their
current types/defaults. Add `--invocation-json <file>` to the aggregate CLI. The
file has exactly two fields: `plan_step` (the real string or null) and `invocation`
(the object above). The Codex caller always supplies it. Legacy calls without the
new argument retain their documented code-lane/no-plan defaults; supplied metadata
must never be discarded. Unknown/malformed keys produce a named input error. The
JSON request is data, not a shell script; no credentials or private verdict-service
handles belong in it.

The existing v3 sidecar keeps timestamp, plan_step, skill_version, invocation,
lens_verdicts, aggregated_verdict, model_tiers_used, and deferred_uat_items. Six
code entries are always present; plan-conformance SKIPPED is generated only when
no plan step was requested **in this Codex code lane**. Shared reducer validation
derives expected entries and skips from reviewers_flag and runtime_downgraded:
other hosts retain registered `ui`, `backend`, and `frontend` entries after the
six-code prefix, all six code SKIPPED entries in runtime-only mode, and the core's
nonpassing runtime-only downgrade behavior. Do not apply the Codex six-ID envelope
globally. Filename timestamp format is `YYYY-MM-DDTHH-MM-SS`.
Each invocation uses a unique output directory so simultaneous reviews cannot
overwrite a same-second filename. Parent-minted review-directory IDs are random
UUIDs. The caller retains each prior sidecar immutably and passes the exact previous
iteration's locator, never whichever JSON happens to be newest.

The separate local host receipt records `review_id` (UUID), `source_commit` and
`candidate_commit` (full Git IDs), `input_sha256` (64 lowercase hex), selected
entrypoint locator, per-lens requested role/model/effort and observed resolved
identity or explicit `unobserved`, child ID, attempt number, measured timing mode,
dispatch/completion/deadline timestamps, calibration result, and mutation-check
result. These fields are evidence, not secret channel configuration. Public
summaries omit absolute local locators and contain no credentials.

Raw child outputs are untrusted recommendations. The parent validates one result
per expected lens, duplicate JSON keys/IDs, schema, evidence, completion, and
unexpected filesystem mutation before aggregation. Missing, malformed, duplicate,
unknown, cancelled, or unsupported output cannot count as a completed lens. Only
the parent writes aggregate files and authenticates the separate build-step
terminal channel. The review sidecar is not itself that authenticated channel.

## 6. Key Design Decisions

- **P1:** Restore Codex deep review through a separate reviewed plan. Keep the
  consumer's planned review depth.
- **P2:** Repair checkpoint invocation and the calibrated context probe first.
- **D1:** Initially require an explicit pinned source checkout. This addresses the
  actual host while keeping raw-file installer ownership outside the change. This
  is an agent-selected proposal, not an attributed operator choice.
- **D2:** Fix uncertainty, incomplete/duplicate input, and metadata loss in the
  canonical aggregate before lifting the adapter halt. Preserve its seven
  deterministic aggregation rules and existing terminal-result vocabulary.
- **D3:** Treat fan-out as one fixed independent lens set. A host may execute that
  set in capacity-limited waves of fresh direct siblings; no results from earlier
  waves enter later prompts. This explicitly amends the core's single simultaneous
  batch wording. On a host without first-token telemetry, use a documented
  180-second total-completion deadline per attempt, a stricter bound, with the same
  one retry/30-second backoff. Report which timer was measured; never claim observed
  first-token timing. A cancelled child must terminate before its retry is spawned.
  Exhausting that deadline is `FAILED` with `failure_reason: completion_timeout`;
  add this explicit value to the core/reducer contract rather than fabricating a
  provider overload. Keep the legacy `model_overloaded` value for the existing
  native 529-or-first-token-timeout path after its retry is exhausted.
- **D4:** For Steps 120 and 121 only, replace build-step's named deep invocation
  with the source-driven bootstrap protocol below. This is an explicit plan-level
  exception, not a claim that today's installed adapter works. It preserves all
  six full-depth lenses and the sidecar; neither a gauntlet substitution nor an
  in-session re-read is authorized. The exception expires after Step 121's normal
  adapter is qualified and cannot be used for consumer Steps 61, 62, or 65.
- **D5:** Enable only Codex's code-deep lane. Runtime/full deep remain unsupported
  pending their own host mapping. Ordinary gauntlet runtime/full are unaffected.
- **D6:** Record calibration replay separately from live review evidence. Do not
  bump corpus timestamps or relabel gold to obtain a green gate.

### Bootstrap protocol for Steps 120 and 121

Use a separate pinned checkout of the **pre-implementation main commit** as the
review engine. Record its full commit identity before developer dispatch. Read
its complete review-deep core and helpers, applying only this plan's explicit D3
scheduling/timing amendments. Do not use the candidate adapter or candidate
reducer as the sole judge of its own change. Do not call the shell router's Claude
stub (`runtime/skill-router.ps1:856-862`) as if it executed reviewers.

After existing mechanical checks, recorded calibration, and the repaired
build-step isolation probe pass, prepare six prompts from the same frozen
candidate. Include the full applicable lens scope, coverage/exclusions, severity
and evidence rules, relevant anti-pattern catalog, and adversarial framing. The
plan-conformance lens receives this numbered step and must run. The parent spawns
six distinct direct siblings with explicit no-history context, in waves of up to
the measured free capacity. Do not reuse a child, pass earlier findings into later
prompts, or disclose private verdict-service state. The producer is already done.

Before accepting any aggregate, the parent checks six unique expected IDs, legal
fields/enums/failure reasons, measured attempt completion, expected input and
candidate identities, evidence, and filesystem mutation audit. No bootstrap lens
may SKIP. A missing, duplicate, malformed, uncertain, failed, no-evidence, or
needs-clarification result prevents PASS, regardless of what the old reducer says.
Uncertainty is a visible escalation, not an automatic developer correction loop.
The validated raw reports are retained individually.

Invoke the pinned reducer's Python API with the real plan_step, invocation, lint
findings, and prior sidecar because its old CLI loses those values. The parent
validates the output against the same six-result envelope, then uses build-step's
existing terminal mapping and private authentication. Any reducer disagreement
with that envelope is a visible stop. Preserve source/candidate IDs, input hashes,
model/effort receipts (resolved identity only when observed), calibration, all six
raw outputs, mutation checks, final sidecar, and the exact prior-sidecar locator.
This protocol is bootstrap evidence; normal installed-host support is still proved
separately. If capability/timing/cancellation cannot be demonstrated, stop before
review. A real Claude native six-lens review is an available future route only
when its actual host prerequisites and allowance have been verified.

## 7. Build Steps

Step numbers continue after the current highest unit, 119. These steps are serial.
Every code step uses a fresh worktree, follows the catalog lifecycle guide for
canonical skill edits, receives independent review, and passes the full root gate
at its exact candidate commit before landing. Existing model pins remain in force;
an unavailable requested model or review host is a visible prerequisite failure.

### Step 120: Make deep-review aggregation fail closed

- **Status:** PLANNED
- **Problem:** A nonpassing or incomplete lens set can currently be reported as PASS.
- **Type:** code
- **Issue:** #
- **Flags:** --reviewers deep --max-iter 3
- **Files:** `skills/review-deep/scripts/aggregate.py`, `skills/review-deep/scripts/README.md`, `skills/review-deep/core.md`, `skills/build-step/core.md`, mechanically synchronized legacy script copies, `_shared/calibrate_judge.py`, `_shared/test_calibrate_judge.py`, new `tests/calibration/test_review_deep_aggregate_contract.py`.
- **Produces:** A validated aggregate CLI preserving actual invocation metadata and a nonpassing result for unresolved lenses.
- **Done when:** Through the real aggregate CLI, complete code-lane six-lens input passes; UNCERTAIN, NEEDS-CLARIFICATION, missing/duplicate/unknown lens IDs, malformed records, and an illegitimate SKIPPED never produce PASS. A planless code review has exactly one legitimate plan-conformance SKIPPED. Existing shared runtime/full entries and legitimate skips remain supported, and runtime-only auth downgrade remains nonpassing. Plan-step/invocation metadata round-trips, prior-sidecar rule 6 and rule 7 remain effective (including valid absence findings), canonical/legacy copies match, and the full root gate passes.

### Step 121: Restore the Codex code-deep invocation

- **Status:** PLANNED
- **Problem:** A capable Codex host has no executable mapping from deep review to independent lenses and the required source assets.
- **Type:** code
- **Issue:** #
- **Flags:** --reviewers deep --max-iter 3
- **Files:** `skills/review-deep/providers/codex.md`, `skills/review-deep/core.md`, `skills/build-step/providers/codex.md`, `skills/build-step/core.md` if its uncertainty branch needs clarification, `tests/package-integrity/test_codex_capability_claims_honesty.py`, `tests/package-integrity/test_codex_agent_isolation_contract.py`, `tests/distributions/test_distributions.py`, provider/reader/troubleshooting documents in the impact table, `documentation/descope-2026-09.md`, `plan.md`.
- **Produces:** A conditional Codex code-lane adapter using calibrated no-history dispatch and a pinned checkout, with explicit scheduling/timing semantics.
- **Done when:** The generated adapter used in a disposable installed profile resolves its explicit source pin and runs calibration, mechanical checks, all required fresh sibling lenses, strict aggregation, and the build-step deep consumer in order. Failed readiness/probes/unsupported flags stop before a lens starts; uncertain or incomplete reports cannot authenticate advancement. A second review forwards the first sidecar. The receipt records the qualified emitted entrypoint, core, source pin, and hashes for Step 122. Tests verify actual caller behavior rather than just matching words in Markdown, all provider builds succeed, and the full root gate passes.

### Step 122: Prepare reproducible installed-host acceptance

- **Status:** PLANNED
- **Problem:** Unit and adapter-contract checks cannot establish that the live Codex host completed the restored workflow.
- **Type:** code
- **Issue:** #
- **Flags:** --reviewers deep --max-iter 3
- **Files:** new `documentation/operator/codex-deep-review-smoke.md`, new `tests/fixtures/codex-deep-review/` benign and planted-defect consumer cases, `tests/distributions/test_distributions.py`, `tests/calibration/test_review_deep_aggregate_contract.py`, `plan.md`.
- **Produces:** A runnable acceptance procedure with fixed expected outcomes, evidence fields, install inspection, and rollback instructions prepared from the actual installer.
- **Done when:** A fresh reader can execute the procedure against an installed candidate without inventing paths or choosing a fixture. The deterministic rehearsal covers complete/PASS, planted defect/NEEDS-WORK, uncertainty/no-advance, failed calibration, source mismatch, caller-scoped verdict rejection, and prior-sidecar reuse. Any helper has exit-0 help and checked exits; the full root gate passes. No live activation is claimed by this prep step.

For Step 122's review, the parent explicitly loads Step 121's qualified emitted
Codex `review-deep/SKILL.md` and its co-located core in the same parent context,
using the receipt's exact disposable-profile locator and source pin. Validate the
recorded hashes and corresponding build-step adapter locator first. This is the normal qualified adapter, not the expired
source-bootstrap exception and not the still-old active-home catalog entry. No
new build-step CLI flag or claimed temporary-host discovery API is introduced.
This proves explicit-entrypoint execution; native automatic discovery and
active-home activation remain Step 123 observations.

The fixtures contain a small real consumer module, tests, numbered plan step, and
review diff. The benign case implements its stated behavior. The planted case
changes an ownership/admin authorization check to unconditional success while
leaving the plan's access restriction intact, requiring a cited security or
correctness Block. Include a valid prior-sidecar fixture for deterministic rule-6
replay. Keep live judgment outcomes distinct from injected reducer failures. One
live pass per case is the planned observation; a failed case is evidence to triage,
not permission to retry unchanged input until it passes.

### Step 123: Observe the restored deep lane on Codex

- **Status:** PLANNED
- **Problem:** The current installed-host gap remains unproved until real fresh reviewers complete the pipeline.
- **Type:** wait
- **Issue:** #
- **Files:** Read Step 122's acceptance procedure and the certified candidate evidence.
- **Produces:** Host acceptance observations, model-resolution record, sidecar locators, and the acceptance decision.
- **Done when:** The operator/attended coordinator runs the prepared procedure on the actual Codex host, observes the expected live benign/planted-defect outcomes with six independent lens entries and genuine plan-conformance, confirms nonpassing failure cases and round-two prior-sidecar handling, and records the result. Failure preserves evidence and leaves the affected consumer deep steps unready. Success names the installed source pin and permits resuming the consumer under its unchanged deep flags.

## 8. Risks and Open Questions

The selected first-release boundary is checkout-backed support (D1). Switching to
installed files alone materially changes the plan and reopens asset-distribution
design. It cannot be implemented by silently copying raw files into a live home.

The two-step bootstrap exception and host scheduling/timing amendments (D3/D4)
are substantive proposal decisions. Without that bounded exception the current
Codex adapter cannot review its own restoration. The unchanged-contract route is
a real supported Claude host when its allowance is available; the current reported
reset is September 12, 23:00 local time, but the date alone proves no capability.

Checkout-backed support adds an explicit local dependency. Upgrade and rollback
must move the installed adapter and source pin as a matched pair. A missing or
changed pin is a named refusal, not a reason to use current main opportunistically.

Calibration replay can remain green despite live judge defects. Step 123 supplies
live evidence, while planted aggregate regressions cover deterministic failure
paths. Shared filesystem access is not an operating-system sandbox: snapshot and
audit reviewer mutations, keep parent-only verdict authority, and make only the
bounded conversation-isolation claim that the probe actually supports.

## 9. Testing and Execution

Windows PowerShell 5.1 (`powershell`), Git, Python, and the repository's installed
pytest dependencies are the existing toolchain. Bash is required for the current
shell helpers. No new global packages, external APIs, service credentials, ports,
development server, lint command, or typecheck command are introduced.

From the selected source worktree:

```text
python -m pytest tests/calibration/test_review_deep_aggregate_contract.py
python -m pytest tests/package-integrity
python _shared/calibrate_judge.py --skill review-deep --mode ci
powershell -NoProfile -File tools/build-distributions.ps1 -Provider claude
powershell -NoProfile -File tools/build-distributions.ps1 -Provider gpt
powershell -NoProfile -File tools/build-distributions.ps1 -Provider codex
python -m pytest
```

The first command applies after Step 120 creates that test. Use the existing
distribution tests for build/install/uninstall in disposable homes. Run changed
shell helpers through `bash -n`; retain `git diff --check`. Regenerate the manifest
only if its owning constants change, and regenerate the representative release
report if a covered core changes. Do not hand-edit dist or installed skills.

The final command is the DONE gate: repository root, no path filter. Check its
actual exit and summary against `documentation/phase-75-baseline.md` before
updating that baseline. Use a detached process, durable stdout/stderr, an exit
sentinel, exact commit/tree before and after, no concurrent pytest, and the standing
memory-admission rule (2 GiB free, or 20 minutes with a detached per-minute trace).
Do not occupy a coordinator window polling a long run; preserve the sentinel and
the finite landing checklist in task state.

Before the build queue: finish plan-review, plan-redline, and plan-wrap; settle any
remaining operator decisions; then repo-sync creates/backfills issue numbers and
task-handoff records the execution inputs. Issue creation is not performed during
this preparation. Use `build-phase --plan documentation/codex-deep-review-restoration-plan.md
--steps 120,121,122` only after the bootstrap host/readiness contract is satisfied.
Stop at Step 123's attended gate. Do not declare the consumer resumed merely because
this plan is ready.

## Appendix

### Decision Inventory

| ID | P/D | Choice | Status |
|---|---|---|---|
| P1 | P | Separate reviewed Codex deep restoration; preserve consumer depth | Requested 2026-09-08 |
| P2 | P | Checkpoint/probe repair precedes restoration | Requested 2026-09-08 |
| D1 | D | Explicit pinned source checkout for the first release | Proposed |
| D2 | D | Fix aggregate validation/metadata before enabling dispatch | Proposed |
| D3 | D | Fixed lens set with capacity-limited waves; stricter completion timer where necessary | Proposed |
| D4 | D | Source-driven six-lens bootstrap for Steps 120 and 121 only | Proposed |
| D5 | D | Code-deep only; runtime/full deep keep an explicit gap | Proposed |
| D6 | D | Separate recorded calibration from live acceptance | Proposed |
