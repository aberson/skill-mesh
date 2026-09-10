# Complete build workflows on Codex and Claude

> **Execution superseded for first delivery, 2026-09-09.** The operator approved
> ordinary Codex workflow first, deferring deep review and Claude acceptance.
> `documentation/codex-ordinary-build-milestone-plan.md` is the controlling M1
> contract and current decision inventory; `plan.md` owns execution status.
> The publication-2 text below preserves the unfinished broader commitment.
> Its old bootstrap, dependency chain, repair-running snapshot and launch commands
> are historical, not M1 instructions. Its review/wrap reports do not certify M1.
> The stable proposal locator now renders publication 3 from the M1 plan.
>
> **Acceptance clarification, 2026-09-10 (P5):** the operator requires shared
> workflow obligations and valid results, allowing different model outputs and
> findings. This also governs the future refresh of the deferred two-host work.
> The historical planted-detection thresholds below are superseded, not future
> release requirements. See `documentation/codex-m1-conformance-amendment.md` and
> the controlling M1 plan for the revised functional-failure exercise. No deferred
> step is completed or activated by this clarification.

**Phase:** WF
**Umbrella:** #196

## 1. What This Is

**Objective:** demonstrate the same installed Skill Mesh release completing a real
`build-phase` workflow on both Codex and Claude: independent implementation, ordinary
full review, six-lens deep review, rejection and correction of a planted defect,
durable checkpoint, fresh-coordinator resume, and gated advancement to completion.

**Status:** REVISED BUILD PLAN, publication 2. On 2026-09-08 the operator authorized
revising the existing plan before building, preserving relevant repairs and making
successful execution on BOTH hosts the completion condition, then preparing an
overnight build. Numbered implementation has not started. This is a bounded new
plan under DS-D3, not a reopening of the cut RD/NP certification programs.
`plan.md` remains the execution-status owner. The historical filename and proposal
locator stay stable so existing links continue to reach this revision.

Proposal: `documentation/codex-deep-review-restoration-proposal.html`

Publication-2 review: `documentation/findings/codex-deep-plan-review-2026-09-08-v2.md`.
Fresh-context check: `documentation/findings/codex-deep-plan-wrap-2026-09-08-v2.md`.

The immediate consumer has deep reviews at Steps 61, 62, and 65. Those flags stay
`--reviewers deep`; their earlier full-review steps retain their existing flags.
The checkpoint/fresh-context repair at `92f082118b695b9275cae6b06e0cb64b808ba0db`
is a prerequisite, including its full root gate, landing, and Codex installation.
Its focused checks and live probes do not certify this workflow. That repair's
first root run has a visible distribution-test failure and is still running at
revision time. Preserve the run; a follow-up must resolve the failure and pass a
fresh exact-candidate gate before landing/install. Never reinterpret that run as green.

**Task completion is a conjunction:** Steps 120-123 are certified and the Codex
AND Claude acceptance records in Steps 124-125 pass every mandatory row in section
5 on the same certified release and fixture revision. A missing host, quota halt,
unsupported required route, skipped review, or incomplete resume leaves the task
IN_PROGRESS/BLOCKED, never COMPLETE. Plan-review READY means the instructions are
ready to execute; it is not compatibility evidence. No all-catalog parity claim
is made by this bounded workflow proof.

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
| `skills/build-step/core.md` and `skills/review-gauntlet/core.md` | Ordinary full review is five code reviewers plus three runtime reviewers; it is distinct from review-deep's runtime/full flags. The simultaneous-batch wording needs a measured-capacity mapping. |
| `skills/build-step/core.md`, legacy `build-step/scripts/capture_evidence.py` | Runtime capture references a helper not emitted in the installed profile. The root-app diff/start lifecycle also needs candidate identity checked when new files or generated frontend assets are present. |
| `documentation/parity-deltas.md:139` | M2's passing workflow was planning/review/wrap, with no build-step execution. M4's install evidence cannot stand in for either live host acceptance below. |

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

Complete the required build workflow on both hosts, preserving ordinary full
gauntlet review and code-deep review at the consumer's existing flag boundary.
Keep the aggregate and Codex deep repairs, and fix the concrete full-review and
checkpoint/resume integration gaps that prevent the acceptance scenario.

The selected setup is an installed profile PLUS an explicitly configured,
immutable local Skill Mesh checkout for non-emitted helpers and calibration data.
This is a declared runtime dependency for BOTH hosts, with one documented setup
and upgrade procedure; installed files alone remain insufficient. Both acceptance
runs start in fresh consumer repositories outside the source tree. No ambient
legacy package or the coordinator's remembered source paths may make them work.
Never search arbitrary parent directories or infer an asset root from consumer cwd.

Also fix the aggregate's unsafe uncertainty/incomplete-input cases before making
the lane available, and preserve actual plan/invocation metadata in the sidecar.
Run the entire prepared workflow on real installed Codex AND Claude hosts before
claiming task completion. This includes automatic native discovery, actual developer
dispatch, real runtime evidence, review-driven correction, and fresh-session resume.

Out of scope: raw package distribution, manifest `package_assets`, package indexes,
installer or write-ahead-log redesign, source imports from the old upstream,
changed gold labels or timestamps, review-deep runtime/full modes, model-quality
benchmarking, local-model review, a new scheduler, and completing the external
consumer's product feature. Acceptance uses its required workflow modes in a small
real consumer app; the actual dev-observatory build resumes separately afterward.
No consumer deep flag is downgraded. Runtime/full requests to this bounded Codex
adapter continue to return a specific missing-mapping explanation; they never
silently become code-only. Ordinary `build-step --reviewers full` IS in scope on
both hosts. This distinction appears in the final support statement, beside the
result rather than hidden in a separate limitations document.

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
| `documentation/operator/build-workflow-acceptance.md` (**new**) | Concrete live acceptance and rollback procedure | Prepared before the attended step |

Additional verified producers required by the connected workflow:

| File | Change Type | Reason | Verified |
|---|---|---|---|
| `skills/build-step/core.md`, `skills/review-gauntlet/core.md`, both Claude/Codex adapters | modify | Capacity-aware ordinary review, exact-candidate runtime startup, required evidence completion, concrete private authority | Source audit: build-step lines 334-373, 444, 563, 611-613; full route has eight reviewers and currently overlays tracked diffs into the main project |
| `build-step/scripts/capture_evidence.py`; new `skills/build-step/scripts/capture_evidence.py` | canonicalize then mechanically synchronize | Supply the actual runtime producer and stop on failed exercise | Tracked legacy producer imports Playwright, accepts async exercise.run(page), currently catches exercise failures as warnings and exits zero; canonical and Codex installed copies absent |
| `skills/task-handoff/core.md`, `skills/build-phase/core.md`, both Claude/Codex adapters | modify | Explicit prior-checkpoint selection, durable root, source-backed rollup helper, fresh trusted session identity | task-handoff resume around line 77 and build-phase startup around line 928 use own/newest rollup paths; neither guarantees selection of the requested prior session |
| new `skills/task-handoff/scripts/task-state-derive.ps1` | add from pinned producer | Eliminate an undeclared coding-root-only runtime dependency | Producer is coding-root `.claude/hooks/lib/task-state-derive.ps1` at `6b05baba19a28b7a4a713fd89460d391fe9281af`; self-contained PowerShell/.NET, import exact Git bytes with provenance and public-path check |
| new `tests/calibration/test_build_workflow_contract.py`; distribution/duplication tests | add/extend | Exercise actual capture exits, caller rejection, source binding, durable resume and canonical/legacy byte agreement | Consumers above are source-checked; new tests must invoke actual producers rather than assert only adapter prose |
| new `tests/fixtures/build-workflow/`; new `documentation/operator/build-workflow-acceptance.md` | add | One executable consumer and two-host procedure | Existing `experiments/recovery/cross-family-fixture/seed/` offers reusable small business-rule fixtures, but no HTTP/UI/build/resume proof; do not revive its retired launcher |

Before changing a helper signature, search its actual callers again and record the
complete result in the developer report. Canonical capture callers are the build-step
core and its emitted copies; shared task-state callers are task-handoff/build-phase.
Do not independently edit generated copies. Representative build-phase/review-gauntlet
core changes regenerate the release-candidate report in the same candidate.

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
| `SKILL_MESH_WORKFLOW_ROOT` | Absolute directory, kept in local configuration only | Explicit trusted skill-mesh checkout for both hosts and review routes |
| `SKILL_MESH_WORKFLOW_COMMIT` | Full lowercase 40-hex Git commit ID | Immutable approved source version; branches and moving refs are rejected |

These replace v1's unimplemented `SKILL_MESH_REVIEW_DEEP_*` proposal names; no
installed interface has used either proposed pair. The support checkout must provide
the canonical deep corpus/scripts/config, canonical runtime capture script, and
the imported canonical task-state helper by Step 122. Readiness is capability-scoped:
deep checks deep assets, full checks runtime assets, and checkpointing checks its
helper; common source/profile identity checks always apply. Step 121 never requires
Step 122's not-yet-authored runtime/checkpoint assets. Its source identity is the same release used
to build the installed profiles. Both hosts resolve the identical documented pair.
The generated skill tree must not depend on helper files left in a mixed legacy
Claude home. The setup procedure verifies Python/Bash/PowerShell, Playwright import
AND a real Chromium launch, and the consumer's actual dependency/build command.

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

Use the declared durable consumer Git root for orchestration and checkpoint state;
developer worktrees are children of the run lifecycle, never checkpoint owners.
Extend task-handoff with `--resume-from <absolute-session-file>`: parse and validate
the source under that consumer's `.claude/task-state/sessions/`, match its plan
identity, preserve the source file, and write resumed state only under the NEW
trusted native session ID. The default resume behavior remains compatible. Pass
the chosen checkpoint through the new coordinator's initial task, then invoke
normal installed task-handoff and build-phase. Build-phase honors that explicitly
selected task state before its ambient-rollup fallback. An unrelated newer rollup
must not change the selected plan or replay a completed step.

### Required connected acceptance on each host

Prepare a tiny real loopback web application in a disposable consumer Git repository,
with a local bare origin, real Python tests, a browser interaction with an observable
backend effect, and frontend assets under a nonstandard `web-client/` subdirectory.
Build a new runtime asset as part of the first step so an old-root/tracked-only
overlay cannot accidentally satisfy the scenario. The app binds an available
loopback port selected once per run; preparation writes the concrete start command
and URL into the fixture plan before invocation. Check Chromium by launching it.
No mocks replace the developer, native host, reviewers, app, capture helper,
aggregate, checkpoint helper, Git lifecycle, or advancement authority.

| Row | Required observation on BOTH Codex and Claude |
|---|---|
| W1 Setup/discovery | A fresh native coordinator discovers the installed build-phase/build-step/review/task-handoff packages; records their hashes, release/support commit, dependencies and trusted native session identity while cwd is outside the source checkout |
| W2 Full implementation/rejection | Actual build-phase fixture Step 1 uses `--reviewers full --isolation worktree --ui`. A fresh developer produces a runnable change including a new frontend asset and a planted business-rule defect that the fixture's normal tests do not cover. Five code and three runtime reviewers run on that exact candidate. A real independent reviewer cites the defect; no merge, DONE or authenticated advancement occurs while it remains |
| W3 Full correction/advance | A fresh developer iteration corrects the cited defect; gates and runtime evidence rerun against the corrected candidate; all required reviewers complete; normal parent authority accepts and merges Step 1, then actual task-handoff writes its checkpoint |
| W4 Fresh coordinator resume | End coordinator A after the completed Step-1 checkpoint. Create an unrelated newer synthetic session record as routing stimulus; it never supplies a native identity. Start a NEW native coordinator B with only the intended durable checkpoint locator and normal task instructions, not the old transcript. It selects the intended plan, does not repeat Step 1, preserves unrelated state, and rebuilds private per-step authority before continuing |
| W5 Deep rejection/correction | Fixture Step 3 uses `--reviewers deep --isolation worktree`, an actual plan-step and six independent lenses. Its first candidate contains a mechanically green ownership/admin bypass. The native deep invocation produces an evidence-backed Block and no advancement. A fresh developer fixes it; the next deep invocation receives the exact prior sidecar and passes after new mechanical gates |
| W6 Finish | Normal build-phase cleanup, successful merges, final task checkpoint and authenticated advancement complete with no stale runtime process or lost/unrelated session writes. Every row has retained evidence and both hosts used the same certified release and fixture revision |

Concrete fixture interface: `GET /health` returns JSON `{"status":"ok","build_id":
"<candidate-id>"}`; `GET /` serves the interaction page and `GET /assets/app.js`
serves the newly built frontend asset. `POST /quote` accepts integer `subtotal_cents`
and returns integer `shipping_cents` and `total_cents`; shipping is 500 cents below
5000 and zero at or above 5000. Step 1's imperfect candidate mishandles equality,
while normal fixture tests cover values below and above the boundary. Its browser
exercise submits 5000 and captures the actual displayed and backend totals.
Step 3 adds an order owner/admin check exercised through `GET /order?actor=...`:
the fixture has one fixed fake owner and one fake outsider, no real accounts or
credentials; outsider access must return 403. The imperfect candidate returns
200 to the outsider while normal tests cover owner/admin. Correct intended rules
stay in Problem/Done-when, and expected-defect data stay outside reviewer payloads.
This is a review challenge with deliberately incomplete fixture tests, not a
weakening of the Skill Mesh production suite.

The frontend has a declared `python web-client/build.py` build producing ignored
`web-client/dist/app.js`; record the generated bytes and candidate identity at
startup. Fixture install has no new runtime framework dependency: Python standard
library app plus the already-required Playwright/Chromium capture environment.
Step 123 authors these exact components and commands before either live run.

The fixture plan includes an explicit `Type: wait` transition after the full code
step and before the deep code step. Its job is the deliberate coordinator
transition: coordinator A writes the real checkpoint with an exact next command
for the remaining deep step and ends normally at the wait boundary. The checkpoint
retains Step 2 as PENDING/WAIT and Step 1 as completed. Fresh native coordinator B
verifies A ended and the intended checkpoint is durable, records that observed
transition, marks fixture Step 2 DONE, and retains this evidence before resuming
only Step 3. The `--resume 3` command alone never establishes transition completion.
The procedure assigns concrete numbers and commands before use; it never assumes
that `--steps 1` leaves an unfinished phase or kills a model during a state write.
W2/W5 name code steps by role; concrete fixture numbers are 1 (full), 2 (wait),
and 3 (deep).

The first-iteration developer receives a fixed imperfect patch as a fixture-only
producer challenge and must implement that candidate exactly. The correct business
rules remain in the separate plan/problem passed to reviewers. The parent does
not edit the candidate behind the developer or feed the mutation recipe to reviewers.
This explicit challenge exception applies only to the disposable acceptance app.

The planted initial candidate is specified as an acceptance challenge, never as a
desired production requirement or a fabricated reviewer verdict. Reviewers receive
the real plan and candidate, without expected findings, answer keys, or each other's
reports. The challenge is successful only when a real reviewer independently
rejects it. No retry of unchanged live input to hunt a favorable verdict. One first
attempt and up to the ordinary three development/review iterations per fixture step;
missed detection, missing evidence, or an exhausted limit is a failed acceptance.

Fixture steps omit `--issue` and use a local bare origin because build-step's issue
tracking is optional; the acceptance setup must verify that the normal caller honors
that optional path. Actual Skill Mesh implementation Steps 120-125 have real tracking
issues created by repo-sync. This is a fixture-only exception to the workspace's
plan-before-issue-before-build policy; it does not apply to Skill Mesh implementation.
Do not manufacture public issues for planted defects. Provision the bare origin,
its default branch, origin/HEAD and the local upstream explicitly. The no-issue
caller omits `--issue` entirely and captures BASELINE_HEAD unconditionally before
integrity checks (currently the source text nests that capture under the issue arm).

Runtime startup runs from the exact candidate worktree after its declared build,
not a partial overlay onto the main project. New/deleted files and generated assets
are covered by a recorded startup/evidence identity. An exercise exception, missing
required UI/backend/frontend artifact, failed readiness, or stale evidence prevents
the ordinary full route from advancing. Amend both the producer and normal consumer;
an extra assertion only in the acceptance harness does not repair the workflow.

Before live reviews, a short mechanical smoke wires actual setup, app, capture,
aggregate fixtures and checkpoint helper. Deterministic negatives cover missing or
duplicate lens output, uncertainty, failed calibration, changed source/install
hashes, missing runtime artifacts and tampered sidecars. Record those separately
from the live rejection/correction observations above. Runtime capture may have its
existing bounded timeout; do not require a full LLM review to finish in 60 seconds.

Receipts retain host/version, fresh native coordinator IDs, requested/observed model
and effort, release/support/fixture IDs, package hashes, all developer/reviewer
attempts, exact candidate and runtime evidence identities, gate exits, raw reviewer
outputs, sidecar/prior-sidecar locators, checkpoint selection, merge history and
cleanup. A public acceptance note contains redacted evidence locators and one row
per W1-W6 per host. Never publish keys, protected canaries, service handles,
credentials, raw private transcripts, or absolute user paths. If shared workflow
code changes after one host passes, requalify both against the new release; append
old evidence as history rather than relabel it.

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
- **P3:** Revise the plan around the actual complete build workflow; successful
  execution on BOTH installed hosts is the task-completion condition. Preserve
  useful repairs, and prepare bounded overnight progress without weakening that bar.
- **D1:** Initially require an explicit pinned source checkout. This addresses the
  two-host workflow while keeping raw-file installer ownership outside the change.
  Changed in publication 2: one explicit support dependency now covers deep,
  runtime capture and checkpointing on both hosts. This remains an agent-selected
  design default, not an attributed operator packaging choice.
- **D2:** Fix uncertainty, incomplete/duplicate input, and metadata loss in the
  canonical aggregate before lifting the adapter halt. Preserve its seven
  deterministic aggregation rules and existing terminal-result vocabulary.
- **D3:** Treat fan-out as one fixed independent lens set. A host may execute that
  set in capacity-limited waves of fresh direct siblings; no results from earlier
  waves enter later prompts. This explicitly amends the core's single simultaneous
  batch wording and now also amends build-step/review-gauntlet's five/eight-reviewer
  batches. The following timer amendment applies to deep lenses; ordinary review
  keeps its existing timing policy. For a deep lens on a host without first-token telemetry, use a documented
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
- **D5:** Changed in publication 2: deliver ordinary full gauntlet AND code-deep
  workflows on both hosts. Review-deep's separate runtime/full modes stay outside
  the claimed support scope; ordinary full is explicitly repaired and exercised.
- **D6:** Record calibration replay separately from live review evidence. Do not
  bump corpus timestamps or relabel gold to obtain a green gate.
- **D7:** Use one two-code-step real consumer app, repeated per host on the same
  release. This bounds acceptance to the required workflow rather than a catalog-wide
  matrix. W1-W6 are mandatory, including rejection/correction in both review routes.
- **D8:** Overnight preparation/implementation has a finite eight-hour run budget,
  one coordinator, maximum three iterations per implementation step, serial full
  gates and no automatic relaunch. Preserve evidence on any halt. An active gate
  may finish after the model stops; no new model work starts after the deadline.
- **D9:** Claude live profile activation follows reconciliation/landing of the
  existing `875de2a` handoff fix, routine install without force, then native host
  acceptance. A quota-limited Claude row remains unobserved; Codex success cannot
  waive it. Overnight workers do not touch the protected handoff/Step-111 worktrees.
- **D10:** Astra coordinates and Terra/high implements in the Codex overnight run,
  preserving the existing run pins. For this initial run the coordinator is
  `gpt-6-astra` at xhigh, developers are `gpt-5.6-terra` at high, and Codex reviewers
  are independently dispatched `gpt-6-astra` at high with each lens's distinct
  capability role/scope preserved. These are per-run selections, not global
  tier-map changes. Claude acceptance uses its native core tier policy. Record
  requested and observed identities; never infer reviewer policy from a developer default.

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

**D4 checkpoint bootstrap, through Step 122 only:** the current Skill Mesh project
does not contain the workspace-local rollup helper required by the old checkpoint
entrypoint. Resolve the already-trusted coding-root checkout explicitly in the
private launch record; verify its helper Git blob at
`6b05baba19a28b7a4a713fd89460d391fe9281af` before invoking it. Run the installed
task-handoff core in the SAME parent with this explicit helper-locator mapping,
and pass the canonical Skill Mesh repository as the durable GitRoot. Native
session identity, append-only state and derived-rollup behavior remain unchanged.
No source/consumer dependency is inferred from cwd and no synthetic session ID is
used for a real checkpoint. Confirm the produced session files are ignored session
state and outside disposable developer worktrees. If that trusted producer cannot
be resolved byte-exactly, stop before Step 120. This separate checkpoint exception
expires when Step 122 qualifies the normal emitted mapping; Step 123 and both
final host runs use the newly canonical support helper. It is not permission to
call unavailable deep review or to claim installed-host acceptance.
Also map the old `.claude/references/task-state-schema.md` dependency to
`_shared/task-state-schema.md` from the pinned pre-implementation Skill Mesh
checkout. Record schema and helper identities separately. Both locator mappings
expire when Step 122 qualifies normal emitted checkpointing.

Place the canonical helper under `skills/task-handoff/scripts/`, not `_shared/`:
the existing shared-closure resolver follows bare sibling filenames from the
schema, while the emitter cannot stamp `.ps1` shared leaves. The selected support
checkout avoids that accidental installer expansion; check this boundary with a
real build of all profiles after adding the helper.

Step numbers continue after the current highest unit, 119. These steps are serial.
Every code step uses a fresh worktree, follows the catalog lifecycle guide for
canonical skill edits, receives independent review, and passes the full root gate
at its exact candidate commit before landing. Existing model pins remain in force;
an unavailable requested model or review host is a visible prerequisite failure.

### Step 120: Make deep-review aggregation fail closed

- **Status:** PLANNED
- **Problem:** A nonpassing or incomplete lens set can currently be reported as PASS.
- **Type:** code
- **Issue:** #197
- **Flags:** --reviewers deep --max-iter 3
- **Files:** `skills/review-deep/scripts/aggregate.py`, `skills/review-deep/scripts/README.md`, `skills/review-deep/core.md`, `skills/build-step/core.md`, mechanically synchronized legacy script copies, `_shared/calibrate_judge.py`, `_shared/test_calibrate_judge.py`, new `tests/calibration/test_review_deep_aggregate_contract.py`.
- **Produces:** A validated aggregate CLI preserving actual invocation metadata and a nonpassing result for unresolved lenses.
- **Done when:** Through the real aggregate CLI, complete code-lane six-lens input passes; UNCERTAIN, NEEDS-CLARIFICATION, missing/duplicate/unknown lens IDs, malformed records, and an illegitimate SKIPPED never produce PASS. A planless code review has exactly one legitimate plan-conformance SKIPPED. Existing shared runtime/full entries and legitimate skips remain supported, and runtime-only auth downgrade remains nonpassing. Plan-step/invocation metadata round-trips, prior-sidecar rule 6 and rule 7 remain effective (including valid absence findings), canonical/legacy copies match, and the full root gate passes.

### Step 121: Restore deep review and explicit support assets on both hosts

- **Status:** PLANNED
- **Problem:** A capable Codex host has no executable deep mapping; both installed hosts need explicit, reproducible access to the canonical review assets and parent authority.
- **Type:** code
- **Issue:** #198
- **Flags:** --reviewers deep --max-iter 3
- **Files:** `skills/review-deep/core.md`, `skills/review-deep/providers/{claude,codex}.md`, `skills/build-step/providers/{claude,codex}.md`, `skills/build-phase/providers/claude.md`, `skills/build-step/core.md`, capability and distribution tests in the impact table, provider/reader/troubleshooting documents, `documentation/descope-2026-09.md`, `plan.md`.
- **Produces:** A conditional Codex code-deep adapter, matching Claude asset/authority mapping, and explicit shared support-root and scheduling/timing contracts.
- **Done when:** Generated adapters in disposable profiles resolve the same explicit support contract without ambient legacy files. The qualified Codex adapter runs calibration, mechanical checks, all six required fresh sibling lenses, strict aggregation, actual deep-caller consumption and previous-sidecar forwarding. Missing readiness, unsupported flags, uncertainty and incomplete output cannot authenticate advancement. The Claude mapping names an executable private-authority mechanism to prove in Step 125, not an assumed private model variable. Record qualified emitted entrypoint/core/support hashes for Step 122. Actual producer/caller tests, all provider builds and the full exact-candidate root gate pass. This code qualification is not the final two-host acceptance.
- **Depends on:** 120

### Step 122: Complete full review and durable checkpoint integration

- **Status:** PLANNED
- **Problem:** Ordinary full review lacks a shipped capture dependency, overcommits reviewer capacity and can use incomplete/stale runtime evidence; fresh-session resume can select another task or lose a worktree-local checkpoint.
- **Type:** code
- **Issue:** #199
- **Flags:** --reviewers deep --max-iter 3
- **Files:** `skills/build-step/core.md`, `skills/review-gauntlet/core.md`, `skills/build-phase/core.md`, `skills/task-handoff/core.md`, affected Claude/Codex adapters, new canonical capture helper plus mechanical legacy synchronization, new `skills/task-handoff/scripts/task-state-derive.ps1`, new `tests/calibration/test_build_workflow_contract.py`, distribution/duplication tests, release-candidate report, provider/setup docs, `plan.md`.
- **Produces:** Actual normal-path full review with exact-candidate runtime startup and complete evidence requirements; explicit support helpers and deterministic durable checkpoint selection.
- **Done when:** The real capture producer fails on exercise failure and missing required artifacts; normal full-review consumption cannot advance on failed readiness, missing required reviewer coverage or stale candidate evidence. All five code/three runtime reviewers can run as fresh direct siblings in measured-capacity waves. Real app smoke includes a new asset and generated files from its declared nonstandard build directory. Explicit support resolution works outside the source checkout on both profiles. `task-handoff --resume-from` validates the intended prior checkpoint and durable consumer root, retains the original and unrelated session bytes, and writes under the new trusted session ID; a newer unrelated rollup cannot redirect build-phase. No-issue dispatch omits the flag and still captures BASELINE_HEAD. Actual producer/consumer and backwards-compatibility checks, all provider builds and the full root gate pass.
- **Depends on:** 121

Step 122 also updates the normal build-phase wait handler to invoke
`task-handoff --loop` before stopping. It saves the announced resume command and
the outstanding wait prerequisite, preserving the wait's PENDING/WAIT status.
The fixture's coordinator A saves `--resume 3` with the verified-transition
prerequisite; A does not mark Step 2 DONE. This repairs the actual wait/checkpoint
seam instead of relying on the previous code step's `next: Step 2` checkpoint.

For Step 122's review, the parent explicitly loads Step 121's qualified emitted
Codex `review-deep/SKILL.md` and its co-located core in the same parent context,
using the receipt's exact disposable-profile locator and source pin. Validate the
recorded hashes and corresponding build-step adapter locator first. This is the normal qualified adapter, not the expired
source-bootstrap exception and not the still-old active-home catalog entry. No
new build-step CLI flag or claimed temporary-host discovery API is introduced.
This proves explicit-entrypoint execution; native automatic discovery and
active-home activation remain Steps 124-125 observations.

The qualified emitted-entrypoint rule above also governs Step 123's implementation
review after Step 122. Refresh the pin only through a newly certified predecessor;
never substitute the currently edited candidate as its own sole review authority.

### Step 123: Prepare the connected two-host acceptance procedure

- **Status:** PLANNED
- **Problem:** A review fixture alone cannot prove implementation, runtime review, rejection/correction, checkpoint/resume and final advancement through normal installed skills.
- **Type:** code
- **Issue:** #200
- **Flags:** --reviewers deep --max-iter 3
- **Files:** new `documentation/operator/build-workflow-acceptance.md`, new `tests/fixtures/build-workflow/`, existing distribution and workflow-contract tests, provider setup/support statement, `plan.md`.
- **Produces:** One executable real consumer application and exact two-host W1-W6 run procedure with setup, native fresh-session transition, defect challenge, evidence collection, routine upgrade and rollback.
- **Done when:** A fresh reader can create both consumer repositories, install or inspect the same certified release, configure its support root, provision the local origin and dependencies, and run concrete generated plan/start/resume commands without inventing paths or policies. A short real app/capture/checkpoint smoke and deterministic failure-path rehearsal pass. The fixture verifies normal gates pass on its deliberately uncovered initial defects, then retains separate expected findings for grading actual live reviews; no injected review verdict can satisfy W2/W5. Playwright/Chromium startup is checked, helper --help exits zero, model/host requirements and native session boundary are explicit, all provider builds and the full root gate pass. Neither host's live row is marked PASS by this prep step.
- **Depends on:** 122

### Step 124: Complete the installed Codex workflow

- **Status:** PLANNED
- **Problem:** Codex workflow compatibility remains unproved until a native installed-host build completes every W1-W6 obligation.
- **Type:** wait
- **Issue:** #201
- **Files:** Read Step 123's procedure and certified release/fixture evidence.
- **Produces:** Codex native execution observations and a row-by-row acceptance decision with retained evidence.
- **Done when:** Both fresh Codex coordinators execute the actual installed workflow and W1-W6 all pass, including eight ordinary/six deep reviewer entries, real rejection/correction, full runtime coverage and durable resume. Record source/install/fixture identities and model receipts. Missing capability or a failed row preserves evidence and leaves this step unready. Codex success alone does not complete this task.
- **Depends on:** 123

### Step 125: Complete the installed Claude workflow and accept both hosts

- **Status:** PLANNED
- **Problem:** Codex success cannot establish Claude compatibility, especially when the live Claude tree contains unmerged handoff hardening and quota previously prevented execution.
- **Type:** wait
- **Issue:** #202
- **Files:** Read Step 123's procedure, the certified release and Codex acceptance evidence; resolve the preserved handoff prerequisite before any live Claude reinstall.
- **Produces:** Claude native W1-W6 observations and the final two-host acceptance decision/support statement.
- **Done when:** Claude availability is observed, the existing handoff fix has landed/reconciled without discarding its behavior, routine profile setup matches the same certified release/support/fixture used by Codex, and two genuine native Claude coordinators complete W1-W6. Native parent-only authority is demonstrated rather than assumed. Every mandatory row on BOTH hosts passes before the task is COMPLETE. Record remaining out-of-scope modes beside the passing support statement. A quota or installation prerequisite leaves Claude unobserved and overall completion pending.
- **Depends on:** 123, 124

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

Before either Step 124 or 125 begins, reconcile the protected handoff prerequisite,
certify the resulting common release, and freeze its support and fixture identities.
If that reconciliation is not ready, code/fixture preparation can finish but neither
live host row is certified against an intentionally different release. Later changes
invalidate affected acceptance and require both hosts to be requalified on the new
common identity; no cross-version aggregation of passing rows.

Calibration replay can remain green despite live judge defects. Steps 124-125 supply
live connected evidence, while planted aggregate regressions cover deterministic failure
paths. Shared filesystem access is not an operating-system sandbox: snapshot and
audit reviewer mutations, keep parent-only verdict authority, and make only the
bounded conversation-isolation claim that the probe actually supports.

## 9. Testing and Execution

Windows PowerShell 5.1 (`powershell`), Git, Python, and the repository's installed
pytest dependencies are the existing toolchain. Bash is required for the current
shell helpers. The acceptance fixture adds one temporary loopback development
server per run, with an available port recorded in the generated fixture plan.
No external API, real service credential or new production service is introduced.
Check the existing Playwright/Chromium dependency explicitly. Skill Mesh still
has no configured lint/typecheck command; do not invent either.

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
task-handoff records the execution inputs. Use `build-phase --plan documentation/codex-deep-review-restoration-plan.md
--steps 120,121,122,123` only after the bootstrap host/readiness contract is satisfied.
Stop before Steps 124-125 until the exact live-host prerequisites and prepared
procedure are ready. Keep the overall task pending until BOTH pass; plan readiness
does not resume the external consumer.

## Appendix

### Overnight execution contract

This is a finite build session, not a new scheduler or monitoring product. Prepare
one immutable prompt and run directory with PID, start time, selected plan/source
commit, JSON status, full gate locators and final exit sentinel. Hash the launcher,
prompt and selected executable before dispatch. Preserve Astra/Terra pins and the
eight-hour deadline; never start a second model because a previous one went quiet.

First perform one bounded native Codex CLI qualification (at most twenty minutes)
with per-process feature/config overrides only. The CLI is a different host from
this API session. Available `multi_agent_v2`/`unified_exec` features do not prove
no-history children or caller-scoped handles. Inspect actual tool schemas, run
conversation v2 and private verdict-service checks, and demonstrate a Terra/high
child. On missing/inconclusive capability record `required_tool_missing` and stop.
A separate diagnostic PASS is not portable: the actual overnight coordinator
repeats the required probe before its first developer. No persistent settings edit.

The current root gate and finite completion job must finish before another pytest
or main/install mutation. The initial repair's observed failure requires a follow-up
candidate and fresh gate. A prepared OS runner may wait for old exit sentinels with
no model polling, then test the exact clean follow-up once; never overlap pytest
or reinterpret nonzero exit as retry permission. Any landing/install action is
scoped to that pinned repair and stops if main/remote/ownership changed.

Before numbered implementation: plan-review -> plan-redline -> plan-wrap ->
repo-sync; source/plan commits and issue bodies agree. If repair, qualification or
another concrete prerequisite remains blocked, report PREPARED/BLOCKED with the
exact next action; do not dispatch a builder to rediscover it. Once ready, build
Steps 120-123 serially, with D4 deep bootstrap only for 120/121 and its checkpoint bootstrap through 122. No independent main writes or
profile upgrades while a gate holds its candidate identity. Each code step keeps
its full root gate; no new shared-gate exemption is inferred from CL's amendment.
If the eight-hour budget expires during a detached gate, preserve its PID/logs and
let it finish while ending model work. Morning review starts from its sentinel.

Three iterations of the same implementation failure invoke stop-and-audit, not
another automatic window. Quota, unsupported host semantics or source-pin drift
are visible blocked results. Claude's latest observed weekly limit and unmerged
handoff prerequisite mean two-host completion cannot currently be promised
overnight. Certified code progress is not relabeled as W1-W6 acceptance.

### Decision Inventory

| ID | P/D | Choice | Status |
|---|---|---|---|
| P1 | P | Separate reviewed Codex deep restoration; preserve consumer depth | Requested 2026-09-08 |
| P2 | P | Checkpoint/probe repair precedes restoration | Requested 2026-09-08 |
| P3 | P | Complete actual workflow on both hosts; revise before building and prepare overnight | Authorized 2026-09-08 |
| D1 | D | One pinned support checkout for deep/runtime/checkpoint helpers on both hosts | Changed publication 2 |
| D2 | D | Fix aggregate validation/metadata before enabling dispatch | Proposed |
| D3 | D | Fresh capacity-limited waves for ordinary and deep review; observable deadlines | Changed publication 2 |
| D4 | D | Source-driven six-lens bootstrap for Steps 120 and 121 only | Proposed |
| D5 | D | Ordinary full plus code-deep on both hosts; deep runtime/full remain outside support claim | Changed publication 2 |
| D6 | D | Separate recorded calibration from live acceptance | Proposed |
| D7 | D | One real app, two code steps and a native coordinator transition; W1-W6 per host | Selected default publication 2 |
| D8 | D | Eight-hour serial build, three iterations per step, finite gates, no blind restart | Selected default publication 2 |
| D9 | D | Preserve handoff before Claude activation; quota leaves acceptance pending | Selected default publication 2 |
| D10 | D | Astra xhigh coordinator, Terra high developer, Astra high Codex reviewers; native Claude policy | Selected default publication 2 |
| P4 | P | Ordinary Codex first; deep and Claude acceptance deferred | Approved 2026-09-09; controlling M1 plan supersedes first-delivery scope |
| D11 | D | Ordinary independent source review and bounded checkpoint mapping | Changed 2026-09-09; see controlling M1 plan |
| D12 | D | New contiguous M1 Steps 126-129; separate full-review and checkpoint slices | Changed 2026-09-09; see controlling M1 plan |
