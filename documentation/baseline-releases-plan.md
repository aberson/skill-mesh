# First baseline releases and operating discipline

## 1. What This Feature Does

**Scope approved by the operator in the September 13, 2026 conversation; preparation
started on the subsequent instruction to get started.**

> Establish the first releases from the current Skill Mesh toolkit and experimental lab.
> Record their contents, demonstrated capabilities, known gaps, and existing external
> dependencies. Use those releases as the starting point for development/production
> separation, then connect the utility portfolio in a later milestone.

This plan turns that scope into retained baseline releases, a narrow daily-profile
split, a compact report, explicitly scoped afterparty hygiene, and minimal telemetry.
The initial [baseline report](baseline-release-report.md) is delivered separately
from implementation and release certification. Root plan.md owns this track's status.

## 2. Existing Context

- `config/skill-manifest.json` owns 57 toolkit skills and provider eligibility.
  `tools/build-distributions.ps1` emits shared cores, wrappers and support payloads.
  Its observed all-provider build contains 128/125/125 files.
- `tools/release.ps1` stages the Git index, builds and checks the staged tree, then
  hashes distributions. It defaults to Claude+Copilot; first-baseline packaging uses
  explicit `-Provider all`. A clean isolated checkout at the selected commit binds
  the index to that commit; index content alone does not establish a release SHA.
- `tools/install-skill-mesh.ps1` owns a per-home ledger of file paths and hashes,
  without release identity. `tools/inspect-host-install.ps1` reports discovery and
  marker evidence; it does not establish byte identity or native execution.
- Lab `tools/emit_skills.py`, `tools/emit_antigravity.py` and
  `tools/editor_workflow.py` emit development instructions into assigned consumers.
  `tools/records.py` owns source/candidate/oracle identities and run outcomes.
  Lab development follows its own AGENTS.md, not the old toolkit build procedure.
- Toolkit main is `79a985a38a2ca413da43014b8b50ae4dab67143c`.
  Lab current source is `700a71e84e5af9cd6914982ef8fa424d44e5dd9c`; its Step 144
  candidate is unaccepted and unmerged. Earlier lab runtime proof is pinned to
  `0a56c672be3d56bc107f63421aa8100d3cf8e5a6`. These identities remain distinct.
- Toolkit MEMORY.md contains obsolete execution status. The current plan owns the
  parked PROD track and unfinished M1; neither historical run is resumed by this plan.

## 3. Scope

**Products.** skill-mesh remains an individually useful toolkit with explicit
dependencies and optional workflow composition. skill-mesh-lab develops the larger
Claude + Codex + Gemini + open-model workflow in independently useful increments.
Each product retains its own source, release identity, priorities, and support claims.

**First releases.** Preserve the two observed current source commits and package
what exists. Record unproved or incomplete capabilities; do not add features just
to turn a baseline snapshot into a broader support claim. A failed required release
gate preserves the snapshot and produces a specific qualification blocker; any
repair is separately attributable work, never a silent rewrite of the retained source.

**Split.** Development source, retained release code, selected daily installation,
and mutable data have distinct locations. Start daily-profile adoption with Codex:
its current installed payload already matches the toolkit baseline exactly.
Claude's development junction and foreign content require a later profile-specific
migration; the first Codex activation does not alter them. Lab remains experimental
in assigned consumers until its own supported installation mechanism exists.

**Supporting work.** One on-demand report for these two products, read-only
projections of existing evidence, and an explicitly targeted afterparty sweep.
One active milestone per product names its usable outcome, bounded work, and
completion evidence. Toolkit maintenance proceeds independently of lab milestones.

**Later.** Utility portfolio packaging, new model/host routes, a hosted dashboard,
scheduled monitoring, automatic retries, automatic lab promotion, and comprehensive
usage metering. Existing external integrations are documented as dependencies.

## 4. Impact Analysis

| File | Change Type | Reason | Verified |
|---|---|---|---|
| plan.md; MEMORY.md | modify | Point to this scope; remove duplicated obsolete execution status | Read both; PROD active/parked disagreement confirmed |
| tools/release.ps1; tools/build-distributions.ps1 | extend via separate release entry | Reuse packaging from a pinned clean checkout with an explicit provider set | Read parameter blocks and Git staging implementation; existing signatures stay unchanged |
| tools/install-skill-mesh.ps1; tools/inspect-host-install.ps1 | extend via separate activation entry | Use existing owned-file install and inspection boundaries | Read New-InstallEntry, owned hash-map handling and report assembly; no ledger/report schema change proposed |
| skills/user-afterparty/core.md and providers/{claude,gpt,codex}.md | modify | Explicit two-project targeting and bounded discovery of lab evidence | Read installed wrapper/core and canonical core; current nearest-CLAUDE.md scope excludes lab root |
| runtime/telemetry/telemetry-writer.ps1 and telemetry-summary.ps1 | extend through a report reader | Treat existing stub usage honestly without changing existing producers | Read writer and summary; stub records zero token/cost fields when an API key is absent |
| Lab tools/records.py; docs/run-record-contract.md | extend through an external read-only projection | Reuse accepted outcome and time fields | Read validate_shape/assess/finish contract; no function or record-field changes proposed |
| Lab tools/emit_skills.py, emit_antigravity.py, editor_workflow.py | extend via lab-owned packaging documentation | Record experimental emission and setup requirements | Read emitters and their assigned-consumer checks; do not import old orchestration into lab |

Future shared signature/schema changes require a fresh all-callers search in their
own step. This plan proposes none to existing installer, inspector, telemetry, or
lab run-record interfaces. Catalog changes follow the catalog-lifecycle guide.

## 5. New Components

- A small release entry and release record: source commit/tree, artifact hashes,
  provider scope, checks/review locators, environment, known gaps and predecessor.
  Reuse existing build/install code; exact output files are owned by Steps 147-149.
- A narrow Codex activation entry with inspect/preview/apply/rollback behavior,
  operating only on the selected profile's owned paths and external release records.
- A one-shot report reader with explicit toolkit/lab/home/evidence inputs held in
  private configuration. It produces Markdown plus a small JSON observation.
  Each repository remains the owner of its own source and acceptance evidence.
- Only missing telemetry fields need new capture. Prefer one atomic per-run summary
  over a shared file receiving concurrent appends. Raw records remain at their source.

## 6. Design Decisions

**Baseline selection.** The observed commits above are the initial inputs.
The lab's current source is released only with an experimental, incomplete-acceptance
description. Its earlier prepared-task proof remains historical evidence. The initial
snapshots already preserve this distinction. Proposed version defaults are
`v0.1.0-baseline.1` for toolkit and `v0.1.0-experimental.1` for lab; these names
are planning defaults, not tags already created.

**Release qualification and publication.** Build once from a pinned isolated checkout,
record the exact environment and existing required gate results, and retain those
bytes. Keep source snapshots, qualified packages, published releases and active
installations as different states. A faithful archive is not a passing release gate.
Use the existing toolkit remote; retain the lab release locally until a remote
destination is selected. Public publication uses only a reviewed public artifact;
private run records and consumer snapshots stay local.

**Daily-use changes.** First prepare and test the complete reversible Codex operation
in disposable homes. The selected artifact and owned-file change preview make live
adoption concrete. Credentials, unrelated host settings and consumer-only packages
remain outside the operation. Rollback needs observed restoration, not just a ZIP file.

**Monitoring.** On-demand, read-only, explicitly scoped to these two products.
Show installed/source/release identity, current milestone, exact acceptance scope,
host capability, evidence time, blockers, and hygiene disposition. Report unknown
and stale separately from failure. Read saved running states as recorded states;
never infer a live process or automatic resume permission from them. The reader
does not monitor or control autonomous execution, so no scheduled/always-on
observation step is introduced. A real producer-to-report smoke remains required.

**Telemetry.** Project task/run identity, product revision, host/reported model,
start/end, observed outcome, reason and evidence pointer. Retries/interventions
are optional where observable; tokens/cost are optional and unknown stays unknown.
Keep fixture trials, source checks, and real project work distinguishable when
summarizing outcomes. Logging failure cannot change the coordinator's verdict.

**Hygiene.** Keep afterparty as glue. Explicitly bind the two roots, recognize the
lab's AGENTS.md and ignored evidence layout, and reuse each owning hygiene skill.
Only positively identified inactive candidates enter a cleanup proposal. Retain
unique commits, dirty/untracked work, failed-run evidence and recovery material.
A milestone sweep records keep/archive/remove/propose-release dispositions; no
automatic age-based deletion or implicit graduation follows.

## 7. Build Steps

Step numbers 147-152 follow the inspected toolkit range through 129 and lab range
through 146. Issue fields stay blank until plan-review and plan-wrap complete.
These are not old Phase PROD Steps 2-7. Lab-owned execution must use the lab's
single-writer, finite-allocation and separate-review procedure; do not dispatch
the old build-phase across its repository.

### Step 147: Qualify and retain the first toolkit baseline release
- **Problem:** Turn the retained toolkit source into an identifiable release using the existing toolchain.
- **Type:** code
- **Issue:**
- **Flags:** --reviewers code --isolation worktree
- **Produces:** Pinned source checkout, all-provider artifacts, release record/checksums, release notes, and a concrete public publication packet.
- **Done when:** The existing required release gates pass for the exact candidate/environment; all artifacts verify against the manifest; known workflow gaps and external dependencies are explicit; retained bytes can be reopened and rebuilt consistently. No live install changes.
- **Depends on:** none

### Step 148: Retain the first experimental lab release
- **Problem:** Make the current lab reproducible without confusing incomplete current source with historical native acceptance.
- **Type:** code
- **Issue:**
- **Produces:** Lab-owned experimental source package, environment/setup notes, check/review record, exact capability limits, and retained version identity.
- **Done when:** The archived file set and bytes match the selected Git objects; the lab's applicable source checks and separate review have recorded outcomes; any failed/missing gate prevents a qualified claim; historical proof is not relabeled as current-source proof. The source baseline remains recoverable without a remote.
- **Depends on:** none

### Step 149: Prepare a reversible Codex daily-profile split
- **Problem:** Bind daily Codex use to the retained toolkit release with a concrete recovery route.
- **Type:** code
- **Issue:**
- **Flags:** --reviewers code --isolation worktree
- **Produces:** Narrow activation entry, private release selector/record, owned-file preview, verified preimage and apply/rollback runbook.
- **Done when:** Disposable-home apply, no-op, collision, interruption and rollback cases preserve foreign files; restored owned bytes and ledger match exactly; selector publication follows successful verification; original source and unrelated profiles remain unchanged.
- **Depends on:** 147

### Step 150: Adopt the reviewed daily Codex baseline
- **Problem:** Use the prepared exact artifact as the daily baseline.
- **Type:** operator
- **Issue:**
- **Produces:** Adoption decision and execution evidence for the selected artifact and target.
- **Done when:** The operator approves the concrete target/preview, the prepared operation completes, a fresh session confirms intended discovery, and the exact rollback route is retained. Mechanical preparation and checks are already complete in Step 149.
- **Depends on:** 149

### Step 151: Deliver the compact report and minimal run summaries
- **Problem:** Show source, release, installation, capability and progress without a second status authority.
- **Type:** code
- **Issue:**
- **Flags:** --reviewers code --isolation worktree
- **Produces:** One-shot report reader, private target configuration, JSON observation, compact Markdown, and only missing per-run summary capture.
- **Done when:** A real 60-second producer-to-report smoke reads the two repositories and existing receipts; missing/stale evidence and stub usage stay explicit; a disposable installation drift is detected; reading changes no source, profile or acceptance record. A fresh run regenerates the report from its sources.
- **Depends on:** 147, 148

### Step 152: Connect explicitly scoped milestone hygiene
- **Problem:** Reuse afterparty across the two products without wrong-root sweeps or losing valuable history.
- **Type:** code
- **Issue:**
- **Flags:** --reviewers code --isolation worktree
- **Produces:** Catalog-consistent afterparty scope changes, report pointers and a short milestone routine.
- **Done when:** A report-only sweep names exactly the two roots, recognizes the lab's records, preserves active/unique material, and reports unavailable skill capabilities honestly; confirmed actions use the owning skills' existing boundaries. A before/after report records dispositions.
- **Depends on:** 151

## 8. Risks and Open Questions

| Item | Risk | Mitigation |
|---|---|---|
| Old toolkit workflow gaps | Release preparation becomes another M1 restart | Preserve existing capability limits; execute artifact work through its actual available tools; do not infer a completed build route |
| Toolkit release qualification | Historical certification is mistaken for a current full gate | Bind exact source, environment, command and result; focused inventory checks do not replace the root gate |
| Lab Step 144 | Latest committed work is presented as accepted | Keep `700a71e`, candidate `83c80459`, main `032da7d`, and historical proof distinct |
| Claude development link | Editing source changes daily discovery | Report the junction; defer its separate migration and preserve foreign content |
| Lab remote destination | Publication lacks a destination | Local retained release is sufficient initially; select remote before external publication |
| Ignored evidence | Git bundle mistaken for complete backup | Bundle covers Git history; back up private .local evidence separately before any destructive cleanup |
| Report growth | Monitoring becomes another runtime framework | Explicit inputs, one invocation, small projection; no scheduler or new acceptance authority |
| Long gates | Small changes acquire repeated multi-hour cycles | Use focused iteration, coherent source changes, and the existing exact-candidate full gate; do not add redundant prose-only implementation steps |

## 9. Testing Strategy

Initial inventory validation is limited to the checks in the baseline report:
fresh distribution emission, staged package integrity, exact Git-blob archive
comparison, Codex snapshot round-trip/stability, and lab bundle restoration.
No native workflow or full repository-root test pass is claimed by this document.

For toolkit source changes, run appropriate focused tests and the standing
repository-root `python -m pytest` DONE gate. Catalog edits also follow
`documentation/skill-catalog-lifecycle.md`. For lab source, use its virtual
environment, own root suite, separate review and exact-source native evidence as
applicable. Do not transfer toolkit gate procedures into the independent lab.

Release qualification uses existing source gates and exact artifact inspection.
Activation tests use disposable homes, verify foreign-file preservation and real
rollback. Report tests target stale/missing identities and meaningful drift;
the real smoke exercises existing producers without mocking the boundary.

Next preparation: plan-review, then plan-wrap, before repo-sync.
`/plan-expedite --plan documentation/baseline-releases-plan.md` is the toolkit
planning front door. Once READY, run the toolkit-owned steps with the applicable
build procedure and dispatch lab Step 148 separately under its own instructions.
