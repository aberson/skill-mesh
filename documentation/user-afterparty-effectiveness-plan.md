# Phase AP — user-afterparty effectiveness

## 1. What This Is

**Objective:** Make a milestone hygiene sweep show what it changed, retain consequential unresolved findings, expose coverage limits early, and avoid sizing live worktrees.

What this feature does: extend the existing `user-afterparty` orchestration contract with four small improvements: an entry/exit outcome table, a compact open-finding section, early capability visibility, and metadata-first worktree sizing. It keeps the current flags, bare/full sweep, child sequencing, and child approval gates.

**Authority:** This is a queued maintenance feature in Skill Mesh, the canonical skill source repository. `plan.md` remains the mutable execution-status and evidence index. This plan defines Steps 130–131; it does not advance, resume, or replace the separate Codex ordinary-build milestone (M1). Planning readiness is not implementation or live-install completion.

**Source snapshot:** `main` at `90b1bfc4d714e839543653845ce39bad01f9912d`, inspected 2026-09-17. Re-read current source and the entry plan before implementation.

**Issue namespace:** Phase AP; Steps 130–131 retain their reserved project step numbers. Umbrella: [#215](https://github.com/aberson/skill-mesh/issues/215); implementation: [#216](https://github.com/aberson/skill-mesh/issues/216); operator acceptance: [#217](https://github.com/aberson/skill-mesh/issues/217).

Proposal: documentation/user-afterparty-effectiveness-proposal.html

## 2. Existing Context

The operator accepted the smallest useful delivery from the seed **“make user-afterparty's benefits visible and follow-ups actionable”** after a real September 17 sweep and an independent adversarial effectiveness review. The essential evidence is reproduced here; implementation does not depend on private transcripts or another checkout:

| Observation from that bounded run | Design consequence |
|---|---|
| Five selected memory files measured 135 lines before, 136 after afterparty, and 87 after a later user-wrap. The index remained 141 lines. Original memory baselines were reconstructed from retained snapshots and approved replacements. | Measure entry/exit directly on future runs; separate afterparty from later wrap work and label reconstructed evidence. |
| Guidance and test assertions were corrected, but no worktrees, telemetry rows, or archive nominations were removed. | Report correctness corrections, successful inspection, retained items, and applied cleanup separately. |
| Five proposed routing settings disagreed with installed settings; no runtime failure was established. | Preserve consequential findings with an owner and revisit trigger; disagreement is not proof of execution failure. |
| Forty worktree candidates had existing Git metadata. The recursive size pass was stopped. | Qualify candidates before recursive sizing. |
| `context-slim` was absent on Codex. Eight records/proposed patches contained 949 lines; effort and spend were not measured. | Announce unavailable coverage early; use one top-level report pointing to child evidence. Do not infer savings from output length. |

The review judged the sweep a useful, modest correctness cleanup with unproved efficiency benefit. This feature improves evidence and follow-through; it promises no token, latency, or future model-quality gain.

### Verified source landscape

- `skills/user-afterparty/core.md`: Step 0 resolves flags and projects; Steps 1–2 dispatch children; Step 3 owns orphan inspection and sizing; Step 4 owns the rollup/archive seam; Step 5 renders the outcome. There is no executable afterparty engine.
- `skills/user-afterparty/providers/{claude,gpt,codex}.md`: thin host adapters. Codex already identifies unavailable `context-slim`, respects child capability gates, and continues other selected work.
- `config/skill-manifest.json`: `user-afterparty` is portable with all three providers, `capabilities: ["filesystem"]`, and `support_assets: []`. Preserve these values and the skill identity.
- `skills/tier-escalate/core.md` and `skills/tier-offload/core.md`: both support a write-free `--dry-run`. Afterparty's current Step 1 does not explicitly forward it; fix the invocation mapping while preserving the existing no-write promise.
- `tools/build-distributions.ps1`: emits each provider launcher and the shared core, rewriting their relative links. `-Provider all` includes Claude, GPT/Copilot, and Codex.
- `tools/install-skill-mesh.ps1`: installs generated files with recorded hashes and ownership checks. `tools/probe-codex-skills.ps1` resolves the effective Codex home; its disposable-home override is a filesystem rehearsal, not proof of live host discovery.
- `tests/package-integrity/`, `tests/distributions/`, and the repository-root pytest collection are existing validation paths. No existing executable consumer of the afterparty report headings was found in `skills/`, `runtime/`, `tools/`, or `tests/`.

## 3. Scope

**In scope:** four improvements above, explicit tier-child dry-run forwarding, compact report persistence in normal mode, and a real Codex acceptance procedure with prepared examples. Apply shared behavior in the core and host-specific availability/report bindings in all three adapters in one change.

**Preserve:** nearest-ancestor `CLAUDE.md` project resolution; workspace versus per-project scope; `--only` precedence over `--skip`; `--all-projects` targeting; mandatory `lesson-harvest --dry-run`; conversational gates; orphan classification and fresh per-item removal checks; archive-only COMPLETE sessions; derived rollup ownership; explicit milestone-commit consent. Prior approval never becomes blanket approval for new destructive work.

**Out of scope:** a new default or light mode, automatic changed-input selection, scan caching, a queue/database/dashboard, a new evaluator service, mandatory adversarial review on every run, changes inside child skills, memory synchronization redesign, portable `context-slim`, routing installation, scheduler changes, and cleanup of the September nominations. A report may point to an existing issue or seed without opening one automatically.

## 4. Impact Analysis

Paths in this table are relative to the repository root. “New” paths are planned outputs, not existing files.

| File | Change type | Reason | Verified |
|---|---|---|---|
| `skills/user-afterparty/core.md` | Modify | Entry/exit reporting, prior findings, capability summary, dry-run forwarding, sizing order | Full current contract and child invocation producers read |
| `skills/user-afterparty/providers/claude.md` | Modify | Bind early capability discovery and preserve child-owned probes | Adapter read; shared decisions remain in core |
| `skills/user-afterparty/providers/gpt.md` | Modify | Same contract for the required build-only provider | Adapter read; no attended GPT acceptance claim |
| `skills/user-afterparty/providers/codex.md` | Modify | Early known limitations and truthful per-item outcomes | Existing unavailable-child handling read |
| `documentation/user-afterparty-effectiveness-acceptance.md` | New | Executable preparation/run instructions and evidence checklist for Step 131 | Does not exist at planning snapshot |
| `tests/fixtures/afterparty/` | New | Small sanitized source examples for the acceptance cases: selected memories/index/lesson, prior report, and a minimal project | Existing fixture convention inspected; no shipped package assets |
| `plan.md` | Modify | Reserve Steps 130–131 and point to the feature; later link gate evidence | Current M1 and lifecycle status read; preserve other tracks |

**Unchanged consumers checked:** manifest/inventory records; `tools/gen_manifest.py`; the Codex cohort in `tests/distributions/test_distributions.py`; afterparty references in calibration, budget, and link-resolution gates. No skill rename, roster, capability, support-asset, public function signature, or existing JSON schema changes are required. New report fields are consumed by the next afterparty invocation, as defined below.

No builder, installer, scheduler, shared helper, or sibling-skill implementation change is expected. Use the existing distribution and install paths. A discovered need to alter one is a scoped follow-up, not permission to widen this feature silently. The representative release report covers four other skills; this change does not require regenerating it.

## 5. New Components

### One report per normal invocation

Use the existing workspace task-state area: `.claude/task-state/afterparty-<run-id>.md`. This is a local report, not a session record, queue, or `current.md` writer. Do not force-add it to Git. Keep one top-level record and link child outputs; keep exact proposed patches and decisions with their existing owners.

- `run-id`: UTC `yyyyMMddTHHmmssfffZ` plus a hyphen and a lowercase UUID, generated once at entry. Used for the report filename and finding origin, avoiding same-date collisions.
- `finding-id`: `<origin-run-id>/F<n>`, with a positive ordinal assigned once when a finding first appears. Carry that identity unchanged. Legacy findings receive an identity on first import and retain their original evidence pointer.
- `scope-key`: resolved workspace identity plus the sorted resolved project paths. Record selected item names separately. Match identities using the host filesystem's path/case semantics; an unresolved or moved target is not an exact match.

The Markdown record uses these labeled fields and tables; no separate machine-readable sidecar is required:

| Field/table | Shape and meaning |
|---|---|
| Header | `report-kind: user-afterparty`, `report-version: 1`, run ID, start/end UTC, host, workspace/project scope, selected items, mode, source revision when available |
| Lifecycle | `in-progress`, `complete`, or `interrupted`; last completed item and evidence pointer. Complete describes orchestration termination, not all items passing. |
| Prior report | Selected locator and identity, or `none`, `ambiguous`, or `unreadable` with reason |
| Measurements | Target path, category, entry/exit lines and normalized characters, entry/exit hashes, delta, attribution/evidence, and validity note |
| Outcomes | Item/project, capability status, execution outcome, inspected/candidate/applied counts when evidenced, disposition summary, and child evidence pointer |
| Findings | Finding ID, concise problem, evidence/source version, owner and next action, disposition/reason, revisit trigger, last checked run |
| Limits/next action | Unavailable coverage, unmeasured effort/spend, pending owner handoffs, and one concrete useful next action or existing targeted invocation |

Write a minimal header and carried findings before normal dispatch; update the same record after child results, then finalize after Step 4. Stage each replacement beside this run's report and replace only this run's file, retaining the last readable record if staging fails. If persistence fails, continue supported work and display the report with a persistence failure; never claim it was saved. A fresh run can recover findings from an interrupted record, but cannot use it as a completed comparison. Concurrent reports stay distinct. Do not merge conflicting decisions by guessing; retain the conflict and source pointers.

Normal-mode report persistence is invocation-owned bookkeeping, like the existing child report artifacts; it needs no new approval. It never authorizes changing a hygiene target. Reconcile the core's closing mutation statement with these existing report/rollup writes: list actual applied actions and their approvals instead of claiming that no byte changed. Store counts, decisions and pointers, not copies of private memory content.

Under `--dry-run`, keep all new state in memory and print the preview. Create no report, directory, snapshot, config, or rollup output; forward `--dry-run` to both tier skills as well as lesson-harvest. Do not claim a filesystem write by the host's own transcript machinery was caused by afterparty; acceptance checks the declared task output surfaces.

## 6. Design Decisions

### Bounded, attributable measurement

1. At entry, resolve the selected items and their targets. Measure the resolved memory index and explicit memory/lesson files relevant to selected memory work. If a child determines the selection later, capture its selected files before its approved mutation and label that boundary. Do not recursively inventory all workspace memories to populate a table.
2. For text counts decode UTF-8 strictly, remove a leading byte-order mark, normalize CRLF and CR to LF, count Unicode code points, and count logical lines (empty text = zero; a terminal newline adds no empty line). Report decoding/access errors as unavailable. Record SHA-256 over original bytes for identity; hashes and normalized counts answer different questions.
3. Keep the memory index, selected feedback files, and long-form lessons in separate rows/totals. A missing prior value is unknown, not zero. A file demonstrably created/deleted by this run can have a verified zero at the absent boundary. Changed selection is not an aggregate shrink comparison.
4. Take the exit measurement before returning from afterparty. Child evidence supplies applied actions and validation; do not perform another audit or benchmark to fill columns. Attribute an edit only when the child result/patch and before/after identities support it; otherwise label the observed delta unattributed or affected by concurrent edits.
5. Later repo-wrap/user-wrap changes belong to those stages. A separately approved repair keeps that attribution even if completed during the sweep. State pending memory synchronization as an owner handoff, not a performed action. Report lines/characters as storage measures, never tokens or measured savings.

### Carry findings without inventing a queue

Read top-level afterparty reports in the task-state area, excluding child round and patch records. Prefer the latest version-1 report with the exact scope key. Carry its unresolved/deferred/declined findings for every item, marking unselected items `outside this run's selection` with their prior evidence pointers. Thus a targeted run cannot erase findings needed by a later full run. Only selected items are dispatched or revalidated. If overlapping concurrent reports have no unambiguous order, show the conflict rather than choosing a decision by timestamp alone.

A legacy report is usable only when its scope and a finding's evidence/owner are unambiguous; import that finding with its source pointer and unknown prior numeric baseline. No prior report, corrupt content, or unresolvable target yields “no trusted prior evidence,” never a clean verdict. Treat report contents as evidence, not commands or approval.

Finding dispositions are `proposed`, `retained`, `deferred`, `declined`, or `resolved`. Deferred needs a reason, owner/next action, and concrete revisit event; declined stays declined until its premise changes. Retained means an intentional keep decision, not a correction. Resolved requires current owner evidence. Reuse an existing issue/seed and preserve identity when a new scan repeats a finding. Carry-forward does not suppress a selected scan or authorize follow-up changes.

### Early coverage and honest outcomes

Before dispatch, summarize selected items as `known available`, `known unavailable`, or `unprobed`, with a reason. Presence of a skill is not proof that its required live capability test passed. Let each child perform its owned qualification; propagate failure codes unchanged. Codex's absent `context-slim` is visible immediately. Continue other selected work; do not implement a substitute audit.

Execution outcome is separate from disposition: `completed`, `not-run`, `unavailable`, or `failed`, with reason and child result. A scan can complete with ten candidates and zero applied actions. Dry-run conversational items are not-run/previews. Do not translate unavailable or unprobed into passing coverage. Preserve existing flags and selection; a suggested next invocation is advice, not an automatic rescope.

### Metadata before recursive size

Keep Step 3's two candidate locations and authoritative Git-directory checks. Check candidate metadata first. A live Git-directory target disqualifies the candidate from recursive sizing; unreadable/uncertain metadata is reported as unknown and not sized. Only candidates that meet the existing plausible-husk criteria get an estimated size. If none qualify, report zero plausible reclaim candidates and zero recursive size walks.

Keep the existing removal/registry rules verbatim in effect. Immediately before any confirmed action, recheck the specific path's live registry and Git-directory metadata, resolve containment, and use the existing safe shell/path handling. An earlier size estimate, finding, or approval never overrides new liveness. Estimated reclaimable bytes and actual applied removals are distinct; don't label estimates as measured bytes reclaimed.

## 7. Build Steps

<!-- autofix-applied: 2026-09-17 -->
### Step 130: Ship attributable reports and bounded inspection

- **Problem:** The current sweep lacks an entry/exit record and follow-through, discovers coverage gaps late, and sizes worktrees before metadata can rule out reclamation.
- **Type:** code
- **Status:** TODO
- **Issue:** #216
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `skills/user-afterparty/core.md`; `skills/user-afterparty/providers/claude.md`; `skills/user-afterparty/providers/gpt.md`; `skills/user-afterparty/providers/codex.md`; new `documentation/user-afterparty-effectiveness-acceptance.md`; new `tests/fixtures/afterparty/`; `plan.md` evidence pointer.
- **Produces:** Updated core and three adapters; small sanitized acceptance inputs; a ready-to-run preparation and acceptance brief; normal build/install rehearsal and test evidence. No new package-local assets or runtime engine.
- **Depends on:** No new feature step. Before catalog mutation, satisfy the current lifecycle preflight described below and reconcile source/target-path ownership with other work.
- **Done when:**
  1. Sections 3–6 are implemented without duplicating child hygiene logic. All three generated profiles contain the same shared contract with valid host bindings.
  2. Dry-run tier forwarding, outcome/disposition separation, prior-finding identity/conflict handling across full/targeted/full runs, safe report replacement, missing-evidence handling, and metadata-before-size ordering are explicit and reviewable. Report bookkeeping adds no gate; existing destructive and conversational gates remain intact.
  3. The acceptance brief supplies exact commands and expected observations for every row in Section 9, prepares its fixture tree before the operator run, and identifies the actual host/profile and source revision. It includes a safe installation rehearsal, live adoption procedure, evidence locations, and recovery procedure. The operator will execute these instructions, not author scripts or fixtures.
  4. Existing focused gates, all three provider builds, disposable-home install/inspection, and the complete repository-root test gate pass on the candidate. Preserve all additional gate obligations imposed by the invoking build workflow; no subset or older run stands in for them.
  5. Deep code review passes with evidence for the new report producer/next-run consumer and the worktree safety boundary. Tests/builds prove source/distribution integrity; this step makes no live effectiveness claim.

### Step 131: Observe the installed skill in a fresh Codex session

- **Problem:** Correct Markdown and green distribution tests cannot establish that a host uses the new instructions or produces truthful sweep results.
- **Type:** operator
- **Status:** TODO
- **Issue:** #217
- **Flags:** --reviewers code
- **Files:** Read Step 130's acceptance brief and fixtures; record acceptance evidence through the existing workflow and link it from `plan.md`.
- **Produces:** Observations, command/result evidence, acceptance verdict, and unresolved findings only; no source, config, fixture, or operational-document authorship.
- **Depends on:** Step 130 and its exact candidate/release evidence.
- **Done when:**
  1. Execute the prepared install/probe/inspection procedure, then start a fresh real Codex session. Record the discovered afterparty path and hashes matching the tested release. A temporary install on disk alone is not host acceptance. Use the existing normal installer for live adoption; preserve foreign files and do not use force or an ownership override.
  2. Observe one bounded representative sweep using the real child-dispatch path, a targeted subsequent run that carries a deferred finding, and the specified dry-run/negative cases. Approvals belong to the selected child contracts. If a required observation is unavailable, record it as incomplete; do not simulate a passing child result.
  3. Every Section 9 case has an observation/evidence pointer or a truthful outstanding failure that prevents this step being marked DONE. No destructive action is necessary to show that a now-live candidate is protected.
  4. Report what changed, retained/deferred work, unavailable coverage, and measurement limits. Record whether the outcome table eliminated the need to reconstruct the baseline; do not claim general cost or behavior improvement from one run.
  5. Only after this observed acceptance does the feature qualify as delivered. This is Codex acceptance; Claude gets build/structural coverage and GPT remains build-only. No all-host behavioral parity claim follows.

### Development and installation procedure

Follow `documentation/skill-catalog-lifecycle.md` for an `UPDATE` of `user-afterparty`: normalized operation/name, a freshly captured full Git `base_ref`, `new_name: null`, unchanged description/capabilities, empty resource paths and reference dispositions. Before mutation, record target paths/hashes, verify target cleanliness, and recheck the guide's present-state prerequisites (main clean/synchronized and workspace freeze absent). The guide already records the landed descope/RD-lite prerequisites. Preserve unrelated work and current M1 checkpoints. If a post-write lifecycle gate fails, report `CATALOG_MUTATION_INCOMPLETE` with paths and failed gate; leave evidence intact without automatic rollback.

Skill Mesh runs on Windows PowerShell 5.1 with Git, Python 3, pytest, PyYAML and markdown-it-py. Use existing dependencies; no new library or service. From the source repository root:

```text
python -m pytest tests/package-integrity
powershell -NoProfile -File tools/build-distributions.ps1 -Provider all
python -m pytest tests/distributions
python -m pytest
```

The last command has **no path argument** and is the full DONE gate, including root-only test collections. Do not claim a pending, aborted, or narrowed gate passed. Pin the tested source/tree and preserve stdout, stderr, exit status and actual summary. Schedule slow tests without colliding with an existing repository gate. No development server, separate lint, or typecheck command exists; these are N/A.

Regeneration follows the lifecycle guide: run `python tools/gen_manifest.py` as the unchanged-output check for this mutation; expect no manifest/inventory diff because no authoring constants change. Do not hand-edit generated artifacts. Do not regenerate the representative release report for afterparty alone.

For preparation, use a new absolute temporary directory stored in `$afterpartyInstallHome`, then run `powershell -NoProfile -File tools/install-skill-mesh.ps1 -Provider codex -Home $afterpartyInstallHome -DistDir dist` and `powershell -NoProfile -File tools/inspect-host-install.ps1 -Home $afterpartyInstallHome`. Step 130's brief supplies concrete fixture preparation and inspection commands, including what outputs to expect. No secrets or new credentials are required beyond an already authenticated Codex host.

For live acceptance, run `powershell -NoProfile -File tools/probe-codex-skills.ps1` and use its verified home in the normal installer. Inspect the proposed profile differences first: only the planned afterparty files may change; unrelated drift is reported for its owner. Never copy generated files by hand, overwrite an ownership conflict, or treat a home override as discovered host identity. Retain the prior release and ledger evidence for the established installer recovery procedure. A refusal leaves Step 131 pending, not falsely complete.

## 8. Risks and Open Questions

No unresolved design choice blocks this plan. Agent defaults are recorded in the Appendix for concise feedback.

| Risk | Control / limit |
|---|---|
| Reporting costs more than the hygiene it describes | Measure only selected small inputs; one record and pointers; no output-length or reduction quota |
| Prior reports are stale, malformed, or conflicting | Exact scope and version handling; evidence only, no inherited authority; unknown/conflict rather than false resolution |
| Concurrent edits or later wraps contaminate a delta | Entry/exit boundary, file identities, child evidence, separate stage attribution |
| Dry-run leaks files through child calls | Forward existing tier dry-run flags and inspect actual output surfaces in acceptance |
| A changed sizing order weakens deletion safety | Keep owner checks/gates; live-candidate and liveness-change observations; deep review |
| A generated profile passes while the live host loads an older copy | Real discovery/hash evidence in a fresh Codex session |
| Whole-profile installation encounters unrelated drift | Rehearse and inspect first; normal ownership refusal; no force or unrelated repair |
| Prose compliance varies by host | Distinguish structural gates from observed Codex behavior; preserve unavailable results |

The wall-clock autonomous-behavior trigger does not apply: this is one bounded invocation and a subsequent carry-forward check, with no change to the monthly scheduler, recurring trigger, retry service, or long-lived process. Observe complete real invocations; no month-long soak is required. Existing schedules keep their current command and scope.

## 9. Testing Strategy

Use existing production builders/installers and existing automated gates; do not add a duplicate report engine or keyword tests that claim to prove model behavior. Small fixtures make cases reproducible, not self-grading. Step 130 authors the exact acceptance brief and inputs; Step 131 executes them on the real installed path. Any newly discovered executable defect gets a focused regression test at its actual owner, with scope reviewed before widening this feature.

| Case | Required observed result |
|---|---|
| Selected memory work with a verified correction | Entry/exit rows agree with independent direct counts; index, selected feedback and lessons are separate; correctness can grow text |
| A later wrap modifies those files | The completed afterparty record retains its original exit counts and does not claim the later shrink |
| Successful scan, candidates retained/deferred | Completed scan, candidate count, zero applied actions, owner/revisit reason all visible |
| Missing prior report, unreadable file, or no effort data | Unknown/unavailable/not measured; no invented zero, savings percentage, or token conversion |
| Deferred/declined finding across full/targeted/full runs | Same finding ID and evidence/owner, including items skipped by the middle run; no duplicate, implied resolution, automatic issue creation, or silent scan suppression |
| Legacy/interrupted report and overlapping concurrent records | Usable legacy finding keeps provenance; incomplete baseline/conflicting decision remains explicit |
| Missing `context-slim` or a failed child capability test | Early known gap or unprobed status followed by exact reason code; other selected work continues |
| All candidates have live Git metadata | Metadata inspected, zero recursive size walks of those trees, zero plausible reclaim candidates |
| A plausible orphan becomes live before action | Fresh checks refuse removal; tree and foreign/session state remain untouched |
| Generated and installed routing settings differ | Finding only, preserved unrelated settings, no unsupported runtime-failure assertion |
| Bare, `--only`, `--skip`, combined flags, and `--all-projects` | Existing item/project selection and precedence preserved; no new confirmation gate |
| `--dry-run`, including tier scans | Output preview only; no report/map/config/rollup creation, archive move, deletion, or commit |
| Normal report write fails | Supported work and screen report continue; persistence failure explicit, no saved-report claim |

Use disposable project/worktree fixtures for safety and malformed-history cases. Keep positive scans real: fixtures/transcripts cannot substitute for actual child execution. Compare the final report with the September evidence for disposition completeness and duplicated narrative only; active effort, spend, and prompt tokens remain not measured unless the host provides trustworthy current-run values.

## Appendix

### Decision Inventory

| ID | P/D | choice | status |
|---|---|---|---|
| P1 | P | Plan implementation of improvements informed by the afterparty effectiveness review | Requested 2026-09-17 |
| P2 | P | Use the seed's smallest useful delivery: measurements, carried findings, early coverage and metadata-first sizing; preserve current scope and child gates | Accepted seed direction 2026-09-17 |
| D1 | D | Change the existing core and all three adapters; add only repository acceptance materials, no package assets or new runtime | Carried forward; publication 3 |
| D2 | D | One versioned local Markdown report per normal run, unique identity, carried findings, safe replacement; dry-run prints only | Carried forward; publication 3 |
| D3 | D | Direct selected-file entry/exit lines, normalized characters and byte hashes; no savings target or token inference | Carried forward; publication 3 |
| D4 | D | Two steps: 130 implementation with deep code review, 131 attended real Codex acceptance | Carried forward; publication 3 |
| D5 | D | Build all three providers; rehearse installation, then verify actual Codex discovery on the tested release; no claim of live Claude/GPT parity | Carried forward; publication 3 |

Decision IDs are append-only. The HTML is a view of this plan. Feedback may use `D2 -> <requested change>`; silence leaves the defaults in place and is not evidence that execution or acceptance occurred.

### Source references

- [Entry plan](../plan.md), [repository instructions](../CLAUDE.md), [catalog lifecycle](skill-catalog-lifecycle.md).
- [Current afterparty core](../skills/user-afterparty/core.md), [Codex binding](../skills/user-afterparty/providers/codex.md), [tier escalation](../skills/tier-escalate/core.md), [tier offload](../skills/tier-offload/core.md).
- [Distribution producer](../tools/build-distributions.ps1), [installer](../tools/install-skill-mesh.ps1), [Codex discovery probe](../tools/probe-codex-skills.ps1), [install inspector](../tools/inspect-host-install.ps1).
- [Review routing owner](../skills/review-deep/core.md): deep review is selected for the new persisted-report producer/next-run consumer and the adjacent worktree safety boundary. It requires code lenses, not an app URL or a model override.

Plan-review and plan-wrap are READY; repo-sync created umbrella #215 and step issues #216/#217. Issue-number backfill changes no design decision. The next implementation command, from Skill Mesh, is `build-phase --plan documentation/user-afterparty-effectiveness-plan.md --steps 130`; execute Step 131 as the attended acceptance step after the candidate is ready.
