# Phase BR - First baseline releases and operating discipline

## 1. What This Feature Does

**Scope approved by the operator in the September 13, 2026 conversation; preparation
started on the subsequent instruction to get started.**

> Establish the first releases from the current Skill Mesh toolkit and experimental lab.
> Record their contents, demonstrated capabilities, known gaps, and existing external
> dependencies. Use those releases as the starting point for development/production
> separation, then connect the utility portfolio in a later milestone.

**Objective:** Retain the current toolkit and lab baselines, then establish a
reversible daily-release split with compact monitoring and scoped hygiene.

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
- The preparation commit removed obsolete execution status from toolkit MEMORY.md.
  Root plan.md owns the parked PROD track and unfinished M1; neither historical
  run is resumed by this plan.

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
| Lab tools/emit_skills.py, emit_antigravity.py, editor_workflow.py | read only; summarize in toolkit packaging notes | Record experimental emission and setup requirements | Read emitters and their assigned-consumer checks; do not import old orchestration into lab |

Future shared signature/schema changes require a fresh all-callers search in their
own step. This plan proposes none to existing installer, inspector, telemetry, or
lab run-record interfaces. Catalog changes follow the catalog-lifecycle guide.

## 5. New Components

- A small release entry and release record: source commit/tree, artifact hashes,
  provider scope, checks/review locators, environment, known gaps and predecessor.
  Reuse existing build/install code; concrete interfaces and files follow below.
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

### 6.1 Concrete implementation contracts (agent defaults within approved scope)

These are new interfaces to build, not commands available during preparation.
Use Python standard library for packaging/report projection, PowerShell 5.1 for
activation and the existing installer. No service, database or new runtime package
is introduced. Run subprocesses as argument arrays, never executable task prose.
All paths are explicit arguments; examples use private variables/placeholders.

**Release store and record.** `tools/baseline_release.py` accepts positional
`toolkit|lab` and required `--source-root`, `--source-commit`, `--version`, `--store`,
`--python-exe`, plus optional `--proofs <private-json>` for attributable existing
check/review evidence. Proofs use the same checks/reviews/environment shapes as
the release record; resolve and verify their referenced files and source IDs, and
record missing proof as incomplete. Resolve full commit and tree using Git, create a clean disposable
checkout, verify index/tree/HEAD agreement, and keep the working source unchanged.
The helper's own commit is recorded separately from the product's selected commit.
A release is stored at `<store>/<product>/<version>/` with `source.zip`,
`release.json`, `SHA256SUMS`, and `release-notes.md`; toolkit additionally has
`dist/{claude,gpt,codex}/` and the original normalized `CHECKSUMS.txt` produced by
`release.ps1`. Whole-archive/raw-file SHA-256 is separate from normalized payload
checksums. ZIP metadata need not reproduce byte-for-byte; extracted contents must.

`release.json` version 1 has these required fields:

| Field | Type / meaning |
|---|---|
| schema_version | integer `1` |
| product, version | `skill-mesh|skill-mesh-lab`; explicit version string |
| source_commit, source_tree, builder_commit | full lowercase Git object IDs (40 or 64 hex); source IDs are resolved by Git, builder ID identifies the packaging implementation |
| created_at, predecessor | UTC ISO-8601 string; previous release ID string or null |
| qualification | `INCOMPLETE|BLOCKED|QUALIFIED`; default INCOMPLETE |
| providers | array of packaged profile strings; empty for lab source-only archive |
| artifacts | array of `{path: relative string, sha256: 64 lowercase hex}`; excludes the record itself and SHA256SUMS to avoid recursive hashing |
| environment | object with OS, PowerShell, Git, Python and installed test dependency versions as strings |
| checks | array of `{argv: string[], exit_code: integer|null, cwd: relative string, source_commit: string, evidence: relative string}` |
| reviews | array of `{source_commit: string, requested_model: string|null, resolved_model: string|null, resolution_status: string, identity_waiver: string|null, conversation_id: string, independent: boolean, verdict: string, evidence: relative string}` |
| known_gaps, dependencies | arrays of explicit strings; empty only after inspection |

`<product>/<version>` is the release ID, allocated by the caller. Version must be
one safe path segment (`[A-Za-z0-9][A-Za-z0-9._-]*`); reject traversal, absolute
artifact paths and linked/reparse-point output ancestors. The two initial versions
are fixed defaults in this plan. Example identity: `skill-mesh/v0.1.0-baseline.1`.
A repeated request verifies identical recorded inputs and hashes or refuses a
collision; it never overwrites a retained release. Stage under a unique sibling,
then publish the complete directory once. Failed toolkit qualification stays in
`<store>/.attempts/<uuid>/` with its diagnostics and does not reserve the version
name; retry uses a new attempt, preserving previous evidence. Lab incomplete
experimental archives may publish locally with that status. No automatic deletion.

Record source checks independently of packaging success. For toolkit qualification,
require exact-source root `python -m pytest`, staged `release.ps1 -Provider all`,
artifact verification, and the charter's real representative cross-family review
with model-resolution evidence. No broad workflow claim follows from those checks.
For lab, capture its own root suite and attributable independent committed-source
review outcomes; missing current native acceptance remains an explicit capability
limit. Failure/missing evidence keeps the source archive and sets BLOCKED/INCOMPLETE;
it does not satisfy Step 147 qualification or authorize activation. Step 148 may
finish an explicitly incomplete experimental archive; it must not claim QUALIFIED
unless all applicable lab gates pass. No lab run-state writer is imported or invoked
merely to manufacture packaging proof. Evidence imports bind source/environment,
are copied as needed for local recovery, and never imply native execution occurred.

Prepare a sanitized public packet and release notes for the toolkit's existing
remote; actual tags and publication are a subsequent exact-packet operation.
The lab baseline stays local. Private consumer backups, raw host records and
user-specific paths are excluded from public artifacts. Secrets/credentials are
never inputs; dependency names and auth prerequisites are enough for release notes.

**Codex activation.** `tools/activate-codex-release.ps1` accepts `-Mode
inspect|preview|apply|rollback`, `-ReleaseDir`, `-TargetHome`, `-StateRoot`, and
`-OperationId` for apply/rollback. The entry owns only Codex activation metadata;
reuse installer/transaction mechanisms for owned files. Never pass force flags.
Preview computes exact raw owned-byte/ledger preconditions and the intended
add/update/remove/no-op set. Apply must match that saved preview, or require a new
preview after drift; the caller explicitly supplies the operation ID (UUID4 generated
by preview). Reject missing/malformed ownership, foreign collisions, linked target
paths, mismatched/unqualified artifacts, unresolved prior operations and lock contention.

Private `<state>/operations/<uuid>/` retains preview, owned preimage (including
absence and the entire ledger), postimage, journal references and final receipt.
Metadata writes use a unique sibling plus atomic replacement. One exclusive lock
per target home prevents concurrent changes by this entry; existing installer
compare-before-write protections remain in force against other writers.
`<state>/current-codex.json` contains `{schema_version: 1, release_id: string,
release_manifest_sha256: string, target_home: string, operation_id: UUID4,
verified_at: UTC string}` and is written LAST after installed bytes/ledger verify.
Selector publication failure leaves a recoverable incomplete operation; it never
reports successful adoption. This selector is provenance only; host discovery still
uses `<home>/.agents/skills`. It does not route the host to a mutable development tree.
Rollback checks each current byte against the recorded postimage before restoring
preimages, refuses intervening foreign edits, and restores the prior ledger and
selector including absence. Recovery must handle failure after each write boundary,
including a partially applied install with no selector publication. Preserve unrelated
ledger profiles and foreign files. Lock release uses verified ownership; stale locks
are reported, never silently broken. No host process control or credentials change.

**Report and summaries.** `tools/baseline_report.py --config <private-json>
--output-dir <private-report-dir>` reads explicit roots. Configuration version 1 is
`{schema_version: 1, toolkit_root: string, lab_root: string, home: string,
release_store: string, state_root: string, evidence_roots: string[],
stale_after_seconds: positive integer}`; the example uses placeholders and a
604800-second (seven-day) freshness default. No recursive workspace discovery.
Output directories must be separate from source inputs/consumer discovery roots.

Each report writes immutable `<output>/<observation-uuid>/observation.json` and
`report.md`, publishing the directory after both complete. JSON version 1 contains
`observation_id` (UUID4), `observed_at` (UTC), `products` (two rows keyed by product),
and `warnings` (strings). Each product row has `source_commit`, `release_id`,
`installed_identity` (all nullable strings), `milestone` (source plan locator plus
quoted outcome/status), `capabilities` (evidence-backed rows), `hygiene` (disposition
rows with locators), `runs` (projections below), and `evidence_status`. Capability rows are `{name: string, status:
"demonstrated|unproved|unsupported", source_commit: string|null, evidence: string|null,
evidence_at: UTC string|null}`. Hygiene rows are `{candidate: string, disposition:
"keep|archive|remove|propose-release", reason: string, evidence: string|null,
applied: boolean}`; suggestions have applied=false and the reader performs none.
The milestone row is `{plan: string, outcome: string|null, status: string|null}`.
Evidence status is `current|stale|missing|invalid`; installed drift is a separate
`match|drift|unknown` field. A stale PASS remains dated evidence, not a new failure
or present support. Include sample counts and separate unknowns in every aggregate.

Run projection: `{product, run_id, source_commit, host, reported_model, started_at,
finished_at, outcome, reason, evidence, category, tokens_in, tokens_out, cost_usd}`.
Each is string or null except usage (nonnegative number or null); category is
`fixture|source-check|project-work|unknown`. Source IDs/locators remain attributable;
no identity is inferred from an adapter or renamed across systems. Keep existing
lab `RUNNING|PASSED|BLOCKED|INCOMPLETE` outcomes and toolkit `pass|fail|stub` labels.
A saved RUNNING record proves only its last saved state. Existing lab `run_id` is
canonical UUID4 and task_id is a lowercase hyphenated slug, both allocated by the
lab coordinator; source/candidate Git IDs and oracle SHA-256 remain separate.
Toolkit telemetry lacks run/source/start-end/category fields: preserve nulls and
label usage from `stub` rows unknown, never count them as successful project work.
Where a new baseline operation supplies missing facts, its receipt is the capture;
do not expand the old telemetry producer or add an always-on agent. Optional unknown
retry/intervention counts remain null. Logging failure never upgrades a verdict.
Malformed/partial source records yield warnings with locators; retain the prior valid
report. No implicit retry loops and no writes to source/acceptance records.

**Errors and operational ownership.** New CLIs use exit 0 for a successfully
completed requested operation (report may contain explicit missing evidence), 2 for
bad input/preconditions, and 1 for execution/IO failures. Qualification failures
return nonzero while retaining diagnostic archive/receipt paths; successfully retaining an explicitly incomplete lab archive
is exit 0 with INCOMPLETE in its record (no qualification claim). Read-only inspection
never promotes a receipt. Each operation records argv, time, exit and evidence; no
shared append log. Reopen/hash verification and the tested rollback runbook are the
recovery path, with no scheduler, network endpoint, or remote service deployment.

**Build host and review stakes.** Steps 147-149 and 151 touch release provenance,
profile activation or producer/consumer evidence, so `--reviewers deep` is required
by the plan-review stakes rule. Deep review currently stops in the Codex adapter
(`skills/review-deep/providers/codex.md`, DS-D3); use Claude Code with its genuine
isolated reviewer dispatch for this build. Capability preflight must stop visibly if
unavailable, never self-review or lower the gate. A capable model is advisable;
no model override is imposed. Step 152 adds repeatable `--project-root <path>` selection to afterparty, with
explicit roots replacing broad discovery when supplied; existing no-argument
behavior remains as documented. `--dry-run` is report only. Reject contradictory
`--all-projects` plus explicit roots; pass each root to the owning skill, or record
unsupported without redirecting to another root. Step 152 is ordinary scoped
catalog prose and keeps
`--reviewers code`. This planning pass does not certify the old Codex build route.

### 6.2 Run and validation guide

From the toolkit repository, use Windows PowerShell 5.1, Git, Python and pytest,
with PyYAML, markdown-it-py and jsonschema installed as described in CLAUDE.md.
No lockfile is present; record actual versions. The lab uses its own virtual
environment and AGENTS.md. No development server, lint or typecheck command exists. Native acceptance
means observation in the actual host; deterministic source checks are a separate
evidence class. PS denotes PowerShell, CLI a command-line interface, SHA a Git or
SHA-256 identity as typed above, and PROD/M1 are historical tracks linked by root
plan.md. BR is this baseline-release phase; UUID4 is an independently generated
version-4 UUID, never a hash or a reused host session identity.
Install/activation means the explicitly targeted operation below, not setup of
credentials or global host settings. New CLIs must provide `--help`/PowerShell help
and fail on placeholder paths.

Existing commands (available now, run in the pinned disposable source checkout):

```powershell
python -m pytest
powershell -NoProfile -File tools/release.ps1 -Provider all -StageDir $releaseStage
```

After implementation, the runbook supplies these exact new entry points, with
private variables resolved before invocation:

```powershell
python tools/baseline_release.py toolkit --source-root $toolkitRoot --source-commit 79a985a38a2ca413da43014b8b50ae4dab67143c --version v0.1.0-baseline.1 --store $releaseStore --python-exe $pythonExe
python tools/baseline_release.py lab --source-root $labRoot --source-commit 700a71e84e5af9cd6914982ef8fa424d44e5dd9c --version v0.1.0-experimental.1 --store $releaseStore --python-exe $labPython
powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode preview -ReleaseDir $toolkitRelease -TargetHome $disposableHome -StateRoot $privateState
python tools/baseline_report.py --config $privateConfig --output-dir $reportOutput
```

Step 147 includes a full vertical slice: pinned source -> actual existing build ->
artifact verification -> retained release record -> reopen. Step 149 supplies the disposable preflight
smoke: apply and rollback in a real disposable home with owned and foreign files,
including collision and controlled interruption. Step 150 is the operator substrate
smoke on the actual daily target, including fresh-session CLI/discovery evidence;
the phase cannot be complete before it passes. Step 151's real 60-second smoke
reads actual Git/installer/release/telemetry and lab receipts through the report,
records elapsed time and locators, and makes one controlled disposable drift. No
fixture-only claim may replace that smoke. This is a one-shot utility: no soak/wait
step or long-running autonomous observation window is applicable.

## 7. Build Steps

Step numbers 147-152 follow the inspected toolkit range through 129 and lab range
through 146. Issue fields are filled by plan-expedite after plan-review, plan-wrap and repo-sync.
These are Phase BR, not old Phase PROD Steps 2-7. All implementation files in
this plan belong to the toolkit. Step 148 packages a read-only, pinned external
lab source; it never edits lab code, its index, plan, or acceptance records.
Lab source qualification uses its own checks and separate review in a disposable
checkout, with one writer and a newly declared finite time allocation. Missing
qualification is recorded explicitly. If a lab repair is needed, preserve the
archive and route the repair to a separate lab-owned task; this plan does not
dispatch the old build-phase as the lab development procedure.

<!-- autofix-applied: 2026-09-14 -->
### Step 147: Qualify and retain the first toolkit baseline release
- **Problem:** Turn the retained toolkit source into an identifiable release using the existing toolchain.
- **Type:** code
- **Status:** PENDING
- **Issue:**
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `tools/baseline_release.py` (new); `documentation/baseline-release-runbook.md` (new); `tests/release/test_baseline_release.py` (new). Read/reuse `tools/release.ps1`, `tools/build-distributions.ps1`, `documentation/product-charter.md`; preserve their interfaces.
- **Existing context:** The existing release entry stages the Git index and checks the staged package; it does not attach a source commit or establish native workflow acceptance.
- **Produces:** Pinned source checkout, all-provider artifacts, release record/checksums, release notes, and a concrete public publication packet.
- **Done when:** The existing required release gates pass for the exact candidate/environment; all artifacts verify against the manifest; known workflow gaps and external dependencies are explicit; retained bytes can be reopened and rebuilt consistently. No live install changes.
- **Depends on:** none

- **Parallel-safe with:** none - the single build lane preserves shared release inputs, status writes and the Step 150 adoption boundary.

<!-- autofix-applied: 2026-09-14 -->
### Step 148: Retain the first experimental lab release
- **Problem:** Make the current lab reproducible without confusing incomplete current source with historical native acceptance.
- **Type:** code
- **Status:** PENDING
- **Issue:**
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `tools/baseline_release.py`, `documentation/baseline-release-runbook.md`, `tests/release/test_baseline_release.py` (extend Step 147). Read only: lab `AGENTS.md`, `plan.md`, `tools/emit_skills.py`, `tools/emit_antigravity.py`, `tools/editor_workflow.py`, `tools/records.py`, `docs/run-record-contract.md`.
- **Existing context:** The current lab source is incomplete for acceptance; historical 15/15 editor evidence belongs to a different source. Step 147 provides the shared archive/record writer; lab source remains independently owned.
- **Produces:** Experimental source package preserving the lab-owned source, environment/setup notes, check/review record, exact capability limits, and retained version identity.
- **Done when:** The archived file set and bytes match the selected Git objects; the lab's applicable source checks and separate review have recorded outcomes; any failed/missing gate prevents a qualified claim; historical proof is not relabeled as current-source proof. The source baseline remains recoverable without a remote.
- **Depends on:** 147 (shared release writer; packaging only)

- **Parallel-safe with:** none - the single build lane preserves shared release inputs, status writes and the Step 150 adoption boundary.

<!-- autofix-applied: 2026-09-14 -->
### Step 149: Prepare a reversible Codex daily-profile split
- **Problem:** Bind daily Codex use to the retained toolkit release with a concrete recovery route.
- **Type:** code
- **Status:** PENDING
- **Issue:**
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `tools/activate-codex-release.ps1` (new); `documentation/codex-release-adoption.md` (new); `tests/release/test_codex_release_activation.py` (new). Read/reuse `tools/install-skill-mesh.ps1`, `tools/skill-mesh-transaction.ps1`, `tools/inspect-host-install.ps1`; preserve their interfaces.
- **Existing context:** The current Codex ledger has 125 owned files matching the retained baseline. Ledger paths and raw hashes establish ownership; a generated header alone does not.
- **Produces:** Narrow activation entry, private release selector/record, owned-file preview, verified preimage and apply/rollback runbook.
- **Done when:** Disposable-home apply, no-op, collision, interruption and rollback cases preserve foreign files; restored owned bytes and ledger match exactly; selector publication follows successful verification; original source and unrelated profiles remain unchanged.
- **Depends on:** 147

- **Parallel-safe with:** none - the single build lane preserves shared release inputs, status writes and the Step 150 adoption boundary.

<!-- autofix-applied: 2026-09-14 -->
### Step 150: Adopt the reviewed daily Codex baseline
- **Problem:** Use the prepared exact artifact as the daily baseline.
- **Type:** operator
- **Status:** PENDING
- **Issue:**
- **Flags:** N/A - operator adoption after Step 149
- **Files:** Private adoption receipt under the configured state root; reference `documentation/codex-release-adoption.md`. No source-code authoring in this step.
- **Existing context:** Step 149 supplies tested mechanics and an exact artifact/target preview; a fresh host session supplies discovery evidence.
- **Produces:** Adoption decision and execution evidence for the selected artifact and target.
- **Done when:** The operator approves the concrete target/preview, the prepared operation completes, a fresh session confirms intended discovery, and the exact rollback route is retained. Mechanical preparation and checks are already complete in Step 149.
- **Depends on:** 149

- **Parallel-safe with:** none - the single build lane preserves shared release inputs, status writes and the Step 150 adoption boundary.

<!-- autofix-applied: 2026-09-14 -->
### Step 151: Deliver the compact report and minimal run summaries
- **Problem:** Show source, release, installation, capability and progress without a second status authority.
- **Type:** code
- **Status:** PENDING
- **Issue:**
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `tools/baseline_report.py` (new); `config/baseline-targets.example.json` (new, placeholders only); `documentation/baseline-monitoring.md` (new); `tests/telemetry/test_baseline_report.py` (new). Read existing toolkit telemetry, installer ledger, release records and lab run records; do not change their schemas.
- **Existing context:** The existing telemetry writer can emit stub rows with zero usage. Lab records distinguish source, candidate and oracle; none is interchangeable with an installed version.
- **Produces:** One-shot report reader, private target configuration, JSON observation, compact Markdown, and only missing per-run summary capture.
- **Done when:** A real 60-second producer-to-report smoke reads the two repositories and existing receipts; missing/stale evidence and stub usage stay explicit; a disposable installation drift is detected; reading changes no source, profile or acceptance record. A fresh run regenerates the report from its sources.
- **Depends on:** 147, 148

- **Parallel-safe with:** none - the single build lane preserves shared release inputs, status writes and the Step 150 adoption boundary.

<!-- autofix-applied: 2026-09-14 -->
### Step 152: Connect explicitly scoped milestone hygiene
- **Problem:** Reuse afterparty across the two products without wrong-root sweeps or losing valuable history.
- **Type:** code
- **Status:** PENDING
- **Issue:**
- **Flags:** --reviewers code --isolation worktree
- **Files:** `skills/user-afterparty/core.md`, `skills/user-afterparty/providers/claude.md`, `skills/user-afterparty/providers/gpt.md`, `skills/user-afterparty/providers/codex.md`; `documentation/baseline-monitoring.md`. Follow `documentation/skill-catalog-lifecycle.md`; generated/installed copies are build outputs.
- **Existing context:** Afterparty is routing glue. Its current nearest-CLAUDE.md discovery does not recognize the lab AGENTS.md boundary; owning hygiene skills may need an explicit root or may report unsupported.
- **Produces:** Catalog-consistent afterparty scope changes, report pointers and a short milestone routine.
- **Done when:** A report-only sweep names exactly the two roots, recognizes the lab's records, preserves active/unique material, and reports unavailable skill capabilities honestly; confirmed actions use the owning skills' existing boundaries. A before/after report records dispositions.
- **Depends on:** 151

- **Parallel-safe with:** none - the single build lane preserves shared release inputs, status writes and the Step 150 adoption boundary.

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
planning front door. Once READY, run this plan in Claude Code with the required isolated reviewer
capabilities available. Step 148 is toolkit packaging of read-only external input,
under the lab evidence rules above. No utility portfolio integration is required.
