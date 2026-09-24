# Phase LH — explicit mistake capture and harvest

## 1. What This Is

**Current execution amendment (2026-09-23):** the operator selected a bounded
Codex-coordinated continuation of the preserved Step 153 candidate. The
[completion record](mistake-capture-step153-completion.md) owns this invocation's
route, cumulative retry ceiling, deadline and single-root-gate reuse exception.
It supersedes the older Claude-only launch directions below for this continuation.
All product acceptance requirements and Step 154's attended boundary remain.

**Closeout amendment (2026-09-24):** Step 153 is accepted under the operator-approved
LH-E1 exception in the completion record. That exception supersedes this step's
full-root-gate requirement for this landing only, retaining the failed/incomplete
historical run and the approved local-filesystem trust boundary. Step 154 remains
pending; no installed-host acceptance or daily-profile adoption is claimed.

**Objective:** preserve an evidenced in-session mistake and harvest it at unchanged Git HEAD, using lesson-harvest's existing five-store deduplication and draft-only boundary.

This is Project 2 of the accepted [context-learning portfolio](context-learning-plan.md). It reserves **Steps 153–154**: one implementation slice, then attended Codex acceptance. The September 19 scan covered 29 Skill Mesh worktrees; other plans reserve through 152, including baseline releases (BR, Steps 147–152). The abandoned portfolio Steps 132–138 remain withdrawn.

**Status:** on 2026-09-21 the operator moved Step 153 forward through a fresh
Claude Code deep-review route. Preserve M1 (ordinary Codex build) and
AP (user-afterparty effectiveness); their controlling plans and preserved
executions are unchanged. No automatic start follows from this planning verdict:
the selected Claude route must pass its own capability preflight before
implementation begins. Codex deep review remains an explicit unavailable route,
not a fallback or a reason to downgrade the review.

Proposal: [mistake-capture-proposal.html](mistake-capture-proposal.html)

Preparation checks: [plan-review](findings/mistake-capture-plan-review-2026-09-19.md) → [plan-redline](mistake-capture-proposal.html) → [plan-wrap](findings/mistake-capture-plan-wrap-2026-09-19.md). Their verdicts concern the executable specification; queue entry, review capability and implementation gates remain separate.

Tracking: [Phase LH #218](https://github.com/aberson/skill-mesh/issues/218), implementation [#219](https://github.com/aberson/skill-mesh/issues/219), attended acceptance [#220](https://github.com/aberson/skill-mesh/issues/220). [Preparation receipt](findings/mistake-capture-preparation-2026-09-19.md) records checks and the guarded next action.

Estimated implementation effort: **1–2 active workdays plus required gates and attended acceptance**. Stop scope growth if implementation requires new dependencies, an installer/resource-topology change, workspace hooks or evaluator work. Return a concrete follow-up instead.

## 2. Existing Context

The canonical [lesson-harvest core](../skills/lesson-harvest/core.md) reads Git history and skill-iterate logs, checks five codification stores and drafts changes for review. Its equal-HEAD early return currently prevents any later source from being scanned. Final dry-run clauses require no writes; earlier “both modes” marker prose conflicts and must be reconciled to that contract.

The [Codex adapter](../skills/lesson-harvest/providers/codex.md) currently says all evidence is committed history. Update this restriction to include explicit local observations whose cited evidence is verified; recollection alone remains insufficient. All three adapters ship together.

The [distribution builder](../tools/build-distributions.ps1) already discovers referenced root-shared assets, stamps Python provenance and ships the closure. Referencing one standard-library Python helper from the core uses that existing path. No package-local file or declared support-assets entry changes; the catalog lifecycle's resource-topology stop is therefore not bypassed or widened.

AP calls lesson-harvest with mandatory --dry-run. Preserve that call and its shape. BR's later report work can consume a saved outcome in a separate follow-up. This slice changes neither report owner.

## 3. Scope

In: explicit record mode, immutable private observations, source verification/classification, unchanged-HEAD pending observations, idempotent dispositions, read-only preview, provider bindings and a real installed-host acceptance procedure.

Out: automatic transcript mining, global marker injection into every skill, hooks, scheduling, task-state storage changes, uv/pyproject, automatic trials, automatic live skill/memory mutation, AP report changes and Observatory registration.

Capture is opt-in through the loaded lesson-harvest contract and its record mode. It does not claim every assistant error is observed. After loss of that instruction context, invoke the skill again; no undeclared host hook re-enables capture.

## 4. Impact Analysis

| File | Change type | Reason | Verified |
|---|---|---|---|
| skills/lesson-harvest/core.md | modify | Record mode, independent observation scan, provenance, five-store handling and one dry-run rule | Existing source read; equal-HEAD stop at line 48, five-store owner at 100–110, final dry-run rules at 170/190–191 |
| skills/lesson-harvest/providers/claude.md | modify | Resolve helper from emitted package; explicit source/session binding | Existing adapter read |
| skills/lesson-harvest/providers/gpt.md | modify | Same portable behavior, build-only qualification | Existing adapter read |
| skills/lesson-harvest/providers/codex.md | modify | Same binding; remove committed-history-only assumption for verified records | Existing adapter line 9 read |
| _shared/lesson_observations.py | create | Standard-library private persistence and deterministic CLI | No existing helper; builder's shared Python branch and closure read at lines 621–679 |
| tests/package-integrity/test_lesson_observations.py | create | Behavioral filesystem/CLI cases in existing root collection | Existing test root and repository DONE command verified |
| tests/distributions/test_distributions.py | extend | Generated helper present and runnable after source checkout is unavailable | Update EXPECTED_SHARED_PAYLOAD at line 78; preserve independent closure oracle at 461–485 and use current fixtures |
| documentation/mistake-capture-acceptance.md | create | Exact install/probe/capture/preview/retry procedure authored with code | New Step 153 output; Step 154 only executes it |
| skills/user-afterparty/core.md | read only | Preserve mandatory preview and attribution boundary | Calls at lines 30, 84 and 164; no signature change to legacy invocation |
| skill-iterate/scripts/morning_summary.py | read only | Check the core's claimed trigger without expanding collection | File exists; literal lesson-harvest search found no call. Canonical core's skills/skill-iterate/scripts path is stale; no trigger repair in this slice |

No existing Python function signature or key shape changes. The new helper API has no prior callers. Core/adapters are its only new runtime callers. Existing /lesson-harvest and --dry-run / --since behavior remain, except that new observations prevent an erroneous no-work early exit. Literal searches in session-wrap, repo-update and morning_summary.py found no lesson-harvest call; the core's trigger prose is not proof of wiring. The first slice is explicitly invoked, so no claimed trigger is a dependency.

## 5. New Components and Exact Contracts

### Helper and deployment

New source: _shared/lesson_observations.py. Use Python's standard library only and begin with a triple-double-quoted module docstring, as required by Add-PythonProvenance. The core references it using the repository's existing shared-asset convention, so emitted packages resolve ../_shared/lesson_observations.py relative to their own installed skill directory. Never resolve it from caller cwd or a hard-coded consumer home. Every command in the table below is prefixed by python followed by this resolved helper path; canonical development uses python _shared/lesson_observations.py.

Invoke Python directly in this slice. Build/install remain the existing PowerShell tools. Git is invoked with argument arrays, not a command string. No new server, lint/typecheck, cloud credential or environment variable is introduced.

### Private storage

For --repo, require an existing non-bare Git working tree. Resolve its root and common Git metadata directory using Git. Store under **the resolved common Git directory's lesson-harvest/**, outside versioned worktree content:

- observations/UUID.md: immutable UTF-8 Markdown observation.
- receipts/UUID.json: immutable final disposition for that observation.

Linked worktrees share this repository inbox; each observation retains its originating working-tree root. Never search parent repositories for observations. Read commands do not create directories. Reject symlink/reparse-point state paths before access; evidence locators are inert text and are never executed or automatically opened by the helper. The helper operates in operator-controlled Git metadata: symlink/reparse and containment checks inspect filesystem state before access, not against another process replacing directories concurrently. Hostile concurrent mutation of that metadata is outside this slice's supported boundary. Normal concurrent capture/read remains supported; private placement, atomic no-overwrite publication, bounded reads and sanitized publication remain required.

Use same-directory temporary files and an atomic no-overwrite publication primitive for observations/receipts. Identical ID/content is an idempotent replay; different content for an existing ID is an error. Ignore/report abandoned temporary files. No apply lock or stale-process recovery mechanism is introduced. Normal mutating harvest is limited to one invocation per target repository; concurrent capture/read is supported, concurrent candidate publication is outside this slice. Sequential retry reconciliation is not a claim of concurrent PR uniqueness.

This is a small append-only inbox, not a database or checkpoint migration. Original files stay immutable; a correction is a new record with supersedes pointing to an existing earlier observation in the same inbox. Before classification, harvest must inspect superseding records, including those outside the current page: originals with a correction are historical, never a source of a new candidate. The replacement remains eligible. Conflicting corrective branches are reported and left undecided, never resolved by newest timestamp. Pending exposes correction relationships in diagnostics so bounded paging cannot hide them; diagnostics may include related_observation_ids (UUID array). No automatic correction-conflict resolution is included.

Model-authored record/complete request files must also live in a private temporary directory or this Git metadata area, never a tracked worktree path. Clean up only the exact temporary requests this invocation created. Do not delete a caller-supplied input file.

### Input and saved observation

Input is one UTF-8 JSON object, at most 16 KiB. Unknown keys are errors. No YAML dependency or general Markdown parser is required.

| Field | Type / rule |
|---|---|
| observation_id | Required lowercase canonical UUID4; obtain from helper new-id, keep it in the request file for retries |
| session | Required opaque source session label, 1–256 characters; native ID when available, explicitly labeled manual-session when unavailable |
| source | Required local message/tool-result locator, 1–1024 characters; never executable |
| observed_error | Required nonblank string, at most 2000 characters; observed behavior rather than inferred cause |
| evidence | Required array of 1–5 nonblank locator strings, each at most 1024 characters |
| correction | Required nonblank string, at most 2000 characters; include “unverified” if not yet established |
| supersedes | UUID4 or null; cannot be self; existing observation must belong to this inbox |

Reject NUL and control characters other than LF/tab in narrative strings. The helper adds schema=lesson-observation-v1, recorded_at (UTC ISO 8601), and repo_root (resolved working-tree path).

The Markdown file has a fixed title followed by one JSON fence containing that exact closed envelope. It is human-readable Markdown but parsed as this fixed envelope, not arbitrary headings. The helper must serialize strings safely even if evidence contains backticks. Replaying the same request compares request fields, not a freshly generated timestamp. Correcting an observation creates a new ID; old receipts remain historical and do not hide its replacement.

### Commands and responses

Commands below are the Step 153 implementation contract, not commands that exist today.

| Command | Behavior |
|---|---|
| new-id | Print one UUID4; no repository access or writes |
| record --repo PATH --input FILE | Validate and persist one observation; print JSON schema=lesson-capture-receipt-v1, observation_id, status=recorded/replayed, and private path |
| pending --repo PATH --limit N --after UUID | Read-only; N=1..50, default 20; --after is optional. Print schema=lesson-pending-v1, observations, diagnostics, remaining and next_after (UUID or null). Sort by recorded_at then ID; continue strictly after the named existing observation, even if it already has a receipt. Unknown cursor is an error. No stored cursor or silent truncation |
| complete --repo PATH --input FILE | Persist one disposition receipt; never creates a PR, memory, rule or skill change |

A complete input is exactly observation_id, classification, disposition, evidence_refs and candidate_ref. classification is instruction-gap, instruction-not-used, tooling-environment, task-specific or unsupported. disposition is candidate-prepared, already-codified or rejected. evidence_refs is 1–5 bounded locator strings. candidate_ref is a verified draft PR URL for candidate-prepared, otherwise null. The model verifies PR existence/state and relevance before complete; the helper validates URL shape but performs no network requests. Completion of a new observation requires a new receipt even when it points to an existing candidate.

Saved receipts add schema=lesson-disposition-v1 and recorded_at. Complete returns schema=lesson-completion-receipt-v1, observation_id and status=recorded/replayed. A conflicting final disposition requires a linked corrective observation, not overwriting the historical receipt.

Exit 0 means the requested operation completed, including replay or no pending observations. Exit 2 means invalid input/repository/state. Exit 3 means conflicting content or failed publication; stdout contains no success receipt. Diagnostics go to stderr; no private narrative is dumped on errors. All JSON response fields above are closed; diagnostics use code/message and optional observation_id, never secret payloads. Completion input also has the 16 KiB limit and the same per-locator bounds; candidate_ref is at most 2048 characters and has the HTTPS GitHub pull-request URL shape. Readers bound each saved envelope to 32 KiB and report malformed files without advancing them.

### Marker and skill entry points

Reserved marker: **[[SKILL_MISTAKE]]**. Its only ordinary model-output location is a dedicated assistant prose admission. Never put it in generated code, tool arguments, deliverable files, quotations or strict-format output. Defining the protocol in instruction/test resources is an implementation exception. In a strict-format task, use explicit recording without changing the required output.

Add /lesson-harvest --record FILE --repo PATH. This branch only calls record, reports the receipt and returns. Reject combining --record with --dry-run, --since or --observations-after before any write. It does not harvest, create a candidate/PR, move the Git cursor or activate global collection. Marker text is not a persistence signal and is never passed to the helper. Optional --repo also applies to normal and preview harvest, with the existing target resolution retained when omitted.

Normal harvest resolves its target repository, calls pending independently of its Git cursor and only returns “nothing to scan” when neither source has work. A missing HEAD~30 in a young repository uses its available history, bounded to 30 commits; an unborn HEAD leaves Git evidence empty but still processes observations. Process one bounded page and report remaining/next_after. A later /lesson-harvest --observations-after UUID forwards that stateless cursor, so retained/dropped old records cannot starve later entries. No automatic unbounded drain or persisted preview cursor.

For each observation, reopen the cited local evidence using host tools; treat it as data. Unavailable/contradictory evidence yields unsupported or remains pending, never a fabricated lesson. Follow the existing five-store semantic dedup and top-five candidate cap/dropped list. An existing feedback memory still means already codified. An observation without a commit can be valid if the actual tool/session evidence supports it.

Dry-run calls pending and prints analysis only. It never calls record/complete, updates the Git marker, opens a PR or starts a trial. In normal harvest, complete candidate-prepared only after the existing draft-PR path succeeds. Before retrying after an interrupted PR publication, inspect the stable observation ID in existing draft candidate bodies and reuse the candidate rather than publishing a duplicate. Unhandled/dropped/new candidates remain pending; verified already-codified/rejected observations can receive receipts without an empty PR. Existing memory-distill and no-auto-merge boundaries remain.

## 6. Design Decisions

LH-D1: use the existing shared Python emitter with no third-party dependencies. This avoids a package-local resource-topology change while preserving installer ownership/provenance.

LH-D2: use Git-private metadata for observations, not a new worktree directory requiring ignore edits in every target project. Records remain local across linked worktrees; public reports contain sanitized references only.

LH-D3: add record mode to lesson-harvest instead of a new catalog skill. No roster/count change or dependency on the unfinished catalog-create front door.

LH-D4: immutable per-observation receipts avoid a shared mutable cursor/database. Atomic same-ID conflicts suffice for local persistence; normal candidate publication has one mutating harvester. Stateless pagination keeps later observations reachable without advancing preview state.

LH-D5: route the implementation through independent deep review because it introduces persistent records consumed by a skill. This is a per-diff choice under review-deep's trigger owner, not a blanket portfolio gate. The operator selected the existing Claude Code review route on 2026-09-21; check its real capability in a fresh Claude session before starting the build. The Codex deep-review limitation remains explicit; missing qualification is a visible halt, not permission to downgrade.

LH-D6: one implementation step and one attended acceptance step. One complete real cycle plus named failure cases; no multi-day soak or arbitrary example quota.

## 7. Build Steps

### Step 153: Ship explicit observations and unchanged-HEAD harvesting

- **Problem:** In-session mistakes can disappear without a commit, and equal HEAD currently suppresses the scan.
- **Type:** code
- **Status:** DONE (2026-09-24; scoped acceptance exception LH-E1)
- **Issue:** #219
- **Flags:** --reviewers deep --isolation worktree
- **Files:** canonical lesson-harvest core and all three adapters; new _shared/lesson_observations.py; new tests/package-integrity/test_lesson_observations.py; tests/distributions/test_distributions.py; new documentation/mistake-capture-acceptance.md. Preserve builder, manifest, installer, hooks, AP and other skills.
- **Existing context:** sections 2–5 define the new helper and existing source/consumer seams. Follow the catalog lifecycle as an UPDATE with empty resource_paths; a discovered package-local asset need takes its existing stop.
- **Produces:** deterministic helper, portable record/harvest behavior, behavioral tests, generated distributions and a concrete real-host acceptance procedure with all request files and commands authored ahead of Step 154.
- **Done when:** source preflight and independent review pass; record/replay/conflict/correction, correction-before-classification, stateless pagination past retained items, unchanged/unborn HEAD pending, completed exclusion, dry-run no-write, false evidence, codified pattern, foreign path and partial-publication cases pass; a real helper producer/consumer smoke uses a temporary Git repository and installed generated helper without the source checkout; derived-artifact regeneration and all provider builds pass; full repository-root python -m pytest passes for the exact candidate; diff check passes. Report actual gate summaries. The acceptance procedure is ready; no operator observation is claimed by this code step.
- **Depends on:** none within Phase LH; queue entry and qualified review capability are preflight requirements.
- **Parallel-safe with:** none in this phase — Step 154 consumes its emitted artifacts and acceptance procedure.

### Step 154: Observe capture and harvest in the installed Codex host

- **Problem:** Source and helper tests cannot prove a native host loads the revised contract and keeps evidence/dry-run boundaries.
- **Type:** operator
- **Status:** TODO
- **Issue:** #220
- **Files:** consumes documentation/mistake-capture-acceptance.md and Step 153's exact generated artifact.
- **Flags:** none — attended observation, not a code-review lane.
- **Existing context:** Codex is the selected first runtime host; GPT remains build-only and Claude runtime parity is not claimed.
- **Produces:** observed acceptance verdict and evidence only; no implementation/runbook/config artifacts.
- **Done when:** execute the prepared normal installer into a disposable host home, start a real fresh Codex session and verify discovery/artifact identity; capture a real evidenced correctable error, then harvest with unchanged HEAD; observe marker exclusions, replay, already-codified and unsupported cases, correction linkage and write-free dry-run; verify no live profile, memory, rules or evaluator changed. Explicitly record any unavailable native evidence as incomplete. No live daily-profile adoption is included.
- **Depends on:** 153.
- **Parallel-safe with:** none — observation must use the reviewed Step 153 artifact.

Initial automated selection, after queue/Claude deep-review capability preflight
and issue synchronization: `/build-phase --plan
documentation/mistake-capture-plan.md --steps 153`. Start it in the selected
fresh Claude Code session from a clean synchronized checkout; do not invoke it
through the Codex deep-review adapter. Stop before 154. Do not insert a goal
covering attended acceptance.

## 8. Risks and Open Questions

| Risk | Mitigation |
|---|---|
| Current queue has open M1/AP work | Preserve D9; preparation can finish now, implementation waits its slot or an explicit queue change |
| Codex deep review unavailable | Dispatch only on a qualified review route; no silent downgrade or self-grading |
| Private evidence leaks into draft PR | Publish minimal sanitized provenance; raw observation files remain Git-private and are never staged |
| Duplicate PR after crash | Stable observation ID in candidate body; reconcile existing draft before completion/retry |
| Shared Git metadata across worktrees | Record originating root; explicit target only; one mutating harvester, atomic per-ID publication; no parent repo scan |
| Lost receipt/partial file | Atomic no-overwrite publication, same-ID replay, visible conflict/incomplete diagnostics |
| Instruction exists but was missed | Five-store dedup; classify instruction-not-used before drafting another rule |

No unresolved product choice blocks preparation. Queue position and real review capability are operational prerequisites, not evidence supplied by this document.

## 9. Testing, Setup and First Run

Prerequisites: Windows PowerShell 5.1, Git, Python 3, pytest, PyYAML and markdown-it-py as in CLAUDE.md; jsonschema only for the repository's existing declarative-schema tests. No new dependency install, server, lint or typecheck command.

Build preparation uses a clean synchronized main and a separate worktree, retaining all unrelated work and the existing AP expedite state. Verify the catalog guide's current prerequisites and record base_ref/target hashes before canonical edits. Normalize the lifecycle request as operation=UPDATE, skill_name=lesson-harvest, the actual 40-hex base_ref, new_name/description=null, capabilities/resource_paths/reference_dispositions empty. Regenerate before verification; no manifest count or roster change is expected.

Implementation commands from Skill Mesh root:

1. python -m pytest tests/package-integrity/test_lesson_observations.py
2. python tools/gen_manifest.py
3. powershell -NoProfile -File tools/build-distributions.ps1 -Provider all
4. python -m pytest tests/distributions/test_distributions.py
5. python -m pytest
6. git diff --check

The first command/test file exists only after Step 153. Focused tests are iteration evidence, never the DONE gate. Existing independent distribution-closure tests must agree with the new helper without weakening their oracle. No release-candidate report regeneration is expected: lesson-harvest is not one of the four representative skills.

Prepared first-run procedure: create a disposable Git project/home; normal install the generated Codex profile; resolve the helper from that installed package; call new-id and persist the ID in the prepared JSON request; record it; confirm pending returns it; run lesson-harvest --dry-run on that repository with unchanged HEAD and snapshot private state before/after; then test explicit normal-mode disposition on the prepared non-candidate case. Candidate publication retry is tested with controlled fixtures and the existing draft-only flow, not by opening unsolicited remote PRs during attended acceptance.

This is a one-shot invocation, not a scheduler or autonomous background service. The helper smoke precedes installed-host acceptance; no time-based soak is warranted. Step 154's procedure must include exact setup/cleanup commands and preserve foreign files through the normal installer.

## Appendix

### Decision Inventory

| ID | P/D | Choice | Status |
|---|---|---|---|
| LH-P1 | P | Start the accepted smaller-project plan, prioritizing capture/harvest and preserving its queue | selected 2026-09-19 |
| LH-P2 | P | Keep future automatic isolated trials before human review | selected in portfolio P3; outside this slice |
| LH-D1 | D | One standard-library root-shared Python helper through existing emitter | proposed |
| LH-D2 | D | Git-private observations/receipts, shared across linked worktrees with source identity | proposed |
| LH-D3 | D | Record mode on lesson-harvest; no new catalog skill | proposed |
| LH-D4 | D | Immutable receipts, atomic per-ID publication, one mutating harvester and stateless pagination | revised during adversarial review |
| LH-D5 | D | Independent deep review for the persistent producer/consumer change | proposed |
| LH-D6 | D | Steps 153–154: implementation, then attended Codex acceptance | proposed |
