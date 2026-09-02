# Phase PROD — Stable production utility toolchain

**Status:** AUTHORIZED FOR PLANNING AND AUTOMATED BUILD. Revised Steps 1–5 may run through fresh
Terra `build-step` contexts under the fixed-scope lineage of the operator-authorized code-review
bootstrap exception below. Step 6 is an attended production cutover and may use only the exact
retained candidate produced by Step 5. Step 7 runs after that cutover. Phase RD is paused while a
Phase PROD build-step is active;
its preserved #178 worktree is evidence and salvage, not a merge source.

**Path notation:** `<dev-root>` and `<prod-root>` are runtime-resolved absolute roots. Their initial
host shapes are `%USERPROFILE%\dev` and `%USERPROFILE%\prod`; committed contracts never bind a
private account name. `<skill-mesh-root>` means `<dev-root>\skill-mesh`.

**Planning gates:** the original `plan-review --autofix` and `plan-wrap --autofix` READY verdicts
were superseded after the first Step-1 build-step exhausted 3/3 iterations and exposed an
authority-scope contradiction. On 2026-09-01 the operator selected the declarative-only repair:
Step 1 defines record grammar and pure consistency only, while revised Steps 2, 3, 5, and 6
independently verify the runtime authorities available at their boundaries. Fresh plan-review and
plan-wrap returned READY on content SHA-256
`84f3c9c725836d7df42d05b88419542840940d7d5315efb24f3fdf8bc2d7983b`; repo-sync then created
Step-3 issue #190, mechanically filled that Issue field, and updated #183–#189 to the seven-step
topology. Step 1 subsequently shipped from a fresh worktree at
`2e8e4f3e516c7069d07364ab5438e7f810675290`; Step 2 is the next implementation unit.

## 1. What This Feature Does

Create a stable production copy of Skill Mesh and the utility portfolio under
`<prod-root>` so ordinary project work consumes commit-pinned, reviewed utility code while
development continues under `<dev-root>`. Production code, the live development workspace,
and mutable utility state become separate authorities. A new release is staged beside the active
release, verified, and then selected through an explicit environment/profile cutover with a retained
rollback release.

This detour prevents future Skill Mesh or utility development work from taking otherwise-working
tools offline. It does **not** claim that the currently incomplete Codex `review-deep` package is
restored: Phase RD issues #178–#181 remain the only authority for that repair. Until Phase RD Step 4
passes, projects whose plans require `--reviewers deep` remain blocked even after Phase PROD is live.

## 2. Existing Context

### 2.1 Verified starting state

- Planning orientation used Skill Mesh `main` at
  `52af1d7ee19ff3bafd00d96d269b8ea1d93891bd`, clean and `0/0` against the existing local
  `origin/main` tracking ref. A builder must reverify and record the actual source identities before
  staging; this orientation SHA is not a release selector.
- `<dev-root>` is itself the `aberson/coding-root` Git repository. Its working tree contains
  unrelated tracked and untracked changes, so recursively copying it would mix canonical files,
  nested repositories, task state, caches, evidence, and unfinished work.
- The central portfolio registry is
  `<dev-root>\.claude\observatory\registry.toml`. Its 13 `category = "utility"`
  projects are the default production membership authority. `dev-observatory` and `switchboard`
  are tracked subprojects of `coding-root`; the other registered utilities are nested repositories.
- Existing installed Skill Mesh cores still contain relative utility invocations such as
  `uv run --project dev-observatory ...` and `uv run --project citation-needed ...`. Therefore a
  source bundle alone is not a hookup: the canonical cores must resolve production code separately
  from the workspace or project the utility operates on.
- The pre-existing cross-repository plan at `../documentation/utility-hookup-plan.md` uses
  `DEV_UTILITIES_ROOT` as both code and workspace/state authority. Phase PROD narrows that remaining
  contract before its Step 5 or later hookup implementation resumes; it does not redo its completed
  Steps 1–4 or claim that its seven advisory integrations are built.
- `documentation/phase-rd-review-deep-restoration-plan.md` owns restoration and active proof of the
  complete Codex `review-deep` package. Phase PROD must not edit the frozen Phase IS UAT, C2V/C2A
  artifacts, the Phase IS plan, or the rejected #178 donor worktrees.

### 2.2 Authority roots

| Authority | Initial value | Meaning |
|---|---|---|
| Production base | `<prod-root>` | Stable releases, retained artifacts, cutover records, and backups |
| Production utility code | `%DEV_UTILITIES_ROOT%` = one exact `<prod>\releases\<bundle-id>\workspace` | Executable code and per-release dependency environments |
| Live development workspace | `%DEV_WORKSPACE_ROOT%` = `<dev-root>` | Registry, project repositories, and targets utilities inspect or update |
| Persistent utility data | `<prod>\data` plus existing externally configured stores | Ledgers, indexes, databases, telemetry, credentials, and run history; never cloned into a release |
| Active Skill Mesh profile | Existing provider discovery home and ownership ledger | Updated only by the reviewed installer from Step 5's retained distribution |

`<bundle-id>` has the exact form `prod-YYYYMMDDTHHMMSSZ-<skill-mesh-sha12>`, where the timestamp is
UTC and `<skill-mesh-sha12>` is the first 12 lowercase hexadecimal characters of the selected Skill
Mesh commit. A bundle ID is a directory label, not immutable proof; `bundle.json` binds the full
commit, tree, and artifact hashes.

### 2.3 Release-1 portfolio policy

The policy resolves every registry entry whose exact category is `utility`, then adds the two
explicit entries below. It preserves sibling checkout names because `measure-twice` resolves
`../switchboard` as a local dependency.

| Project | Production state | Repository identity rule |
|---|---|---|
| `b2_project_goblin` | active | Independent pushed repository commit |
| `dev-observatory` | active | `coding-root` tracked subtree |
| `switchboard` | active | `coding-root` tracked subtree |
| `on-brand` | active | Independent pushed repository commit |
| `measure-twice` | active | Use pushed `origin/master`; never consume an unpushed blocked-checkpoint commit |
| `citation-needed` | active | Independent pushed repository commit |
| `tripwire` | active | Independent pushed repository commit |
| `paper-trail` | active | Independent pushed repository commit |
| `changed-check` | active | Independent pushed repository commit |
| `heads-up` | active | Independent pushed repository commit |
| `find-again` | active | Independent pushed repository commit |
| `same-page` | active | Independent pushed repository commit |
| `mesh-lens` | active | Independent pushed repository commit |
| `skill-mesh` | active, explicit flagship addition | Independent pushed repository commit and retained all-provider release |
| `utility-project-standard` | active, explicit optional addition accepted for release 1 | Pushed commit only; working-tree plan status is excluded |
| `pocket-relay` | embedded but inactive | Travels only as a tracked `coding-root` subtree; no command or health claim until implemented |
| `code-stencil` | deferred: `NO_REMOTE_AND_PLACEHOLDER` | No remote/upstream, dirty, and placeholder implementation |
| `jurys-out` | deferred: `DOCUMENTATION_ONLY` | Pushed documentation-only repository with no executable package yet |
| `uat_sentinel` | deferred: `NO_REMOTE_AND_NOT_IMPLEMENTED` | No remote/upstream and production entry points still raise `NotImplementedError` |

There are 15 active project slugs in release 1 but only 14 Git repository identities because
`dev-observatory` and `switchboard` share `coding-root`. Deferred entries remain machine-visible in
the policy so a future reconciliation cannot silently forget them. Moving a deferred entry to active
requires a remote/upstream, a pushed commit, a real non-placeholder entry point, a passing project
gate, and an explicit policy change reviewed through its own build step.

### 2.4 Bundle record shapes

`config/production-portfolio-policy.json` is the committed selection policy. Its locked v1 shape is:

| field | type | constraint |
|---|---|---|
| `schema` | string | exact `skill-mesh/production-portfolio-policy/v1` |
| `registry_categories` | array of strings | exactly one value, `utility` |
| `required_projects` | array of strings | exactly `skill-mesh` |
| `additional_active_projects` | array of strings | exactly `utility-project-standard` |
| `embedded_inactive_projects` | array of strings | exactly `pocket-relay` |
| `deferred_projects` | array of objects | unique `slug`, `reason_code` enum `NO_REMOTE_AND_PLACEHOLDER` / `DOCUMENTATION_ONLY` / `NO_REMOTE_AND_NOT_IMPLEMENTED`, and non-empty human-readable `evidence` |
| `repository_overrides` | object | project slug to repository-owner slug for shared repositories; includes `dev-observatory` and `switchboard` → `coding-root` |
| `repository_sources` | ordered array | exact 14-owner declarative allowlist: owner slug, checkout path, canonical remote identity, represented project slugs, and allowed upstream ref; `measure-twice` is fixed to `origin/master` |
| `additionalProperties` | schema rule | false at every object boundary |

`bundle.json` is generated inside an absent release directory and validated against
`schemas/production-bundle-v1.schema.json`. It records:

| field | type | constraint |
|---|---|---|
| `schema` | string | exact `skill-mesh/production-bundle/v1` |
| `bundle_id` | string | exact format defined above |
| `created_utc` | string | UTC RFC 3339 timestamp |
| `policy_sha256` and `registry_sha256` | 64-character lowercase hexadecimal strings | hashes of the exact consumed bytes |
| `repositories` | ordered array | unique repository owner and checkout path; canonical remote URL, full commit, `HEAD^{tree}`, branch/upstream observation, and represented project slugs |
| `workspace_relative_path` | string | exact `workspace` |
| `skill_mesh_release` | object | retained relative path, provider closures, `CHECKSUMS.txt` SHA-256, source commit/tree, and manifest blob |
| `gates` | ordered array | command, exit code, evidence-relative path, and SHA-256; no prose-only PASS |
| `previous_bundle_id` | string or null | exact prior selected bundle, if one exists |

`current.json` is mutable selection state under the production base. It records exact schema
`skill-mesh/production-current/v1`, active and previous bundle IDs and absolute paths, the two
environment values, activation UTC, installer result path/hash, inspector result path/hash, and the
active Skill Mesh distribution closure. It never contains credentials or mutable utility data.

`activation-plan.json` is generated outside the repository and validates against
`schemas/production-activation-plan-v1.schema.json`. It records exact schema
`skill-mesh/production-activation-plan/v1`; bundle ID/path and `bundle.json` SHA-256; provider fixed
to `codex`; resolved active home; old and new Process/User values for `DEV_UTILITIES_ROOT` and
`DEV_WORKSPACE_ROOT` (each old value is an absolute path or null); retained distribution path and
Codex closure SHA-256; installer/inspector script paths and tracked hashes; absent backup root;
ordered install, inspect, environment, fresh-process smoke, and rollback actions; creation UTC. Every
object rejects additional properties, every action uses an argument array, and no field contains a
credential or command string for shell evaluation.

These four records have a strict authority boundary. `production-portfolio-policy` is normative
declarative policy. `bundle.json`, `current.json`, and `activation-plan.json` are declarative records
and evidence indexes, not capabilities. Schema or pure-consistency validation proves only grammar and
relationships derivable from supplied record values. Every runtime consumer must reopen and
independently verify the Git objects, filesystem objects, exact bytes, executed evidence, active
state, and rollback pre-image it consumes. No Step-1 return value, `validated` token, record hash, or
matching caller-supplied bytes may substitute for that verification. Passing activation-plan schema
validation never authorizes execution.

### 2.4.1 Declarative and runtime authority ownership

| Claimed fact | Step 1 records or checks | First independent owner | Required later recheck |
|---|---|---|---|
| Canonical Git remote and allowed ref | Exact owner allowlist and lexical ref shape | Step 2 | Fetch/clone the allowed remote/ref, prove reachability and selected commit/tree/blob identities; Step 5 repeats on the real release |
| Installer and inspector identity | Relative path, role, and digest field grammar | Step 2 | Derive paths and bytes from the verified Skill Mesh Git objects; Step 6 reopens and hashes the retained scripts before use |
| Gate command | Closed project/role/argument-array declaration | Step 2 | Construct complete non-shell argv from the real supported interface |
| Gate execution and evidence | Exit/evidence/hash fields as declarations | Step 5 | Execute the exact argv, capture the exit sentinel and exact evidence bytes, require one unique row per active project, and hash reopened evidence |
| Bundle predecessor | Nullable ID and internal non-self grammar | Step 5 | Read and hash the actual pre-stage selector, or prove its absence, and derive `previous_bundle_id` |
| Current predecessor lineage | Joint-null/present record shape | Step 6 | Compare the live preflight selector with the certified predecessor and sibling retained release |
| Retained distribution closure | Provider/checksum/closure field grammar | Step 5 | Build with `-Provider all`, reproduce and hash every retained output, then disposable-install those exact bytes; Step 6 rehashes before install |
| Release filesystem identity | Lexical path grammar | Step 2 | Prove final-path, reparse, case/alias, containment, and no-hardlink behavior on real disposable objects; Step 5 repeats on the real release |
| Active-home and backup identity | Lexical path fields | Step 6 | Re-resolve the real home, ledger, backup roots, parents, and targets immediately before mutation |
| Activation operations | Complete argv or closed typed-operation grammar | Step 2 | Step 3 builds and integration-tests the executable engine against the real installer/inspector interfaces; Step 5 freezes and Step 6 revalidates it |
| Exact active profile closure | Desired closure fields | Step 3 | Build the retained-dist/ledger/installed-file comparator against disposable homes; Step 6 reopens real bytes and runs it immediately before and after mutation |
| Rollback pre-image | Typed rollback descriptor | Step 3 | Prove exact disposable pre-image restoration; Step 6 opens and hashes the actual old environment, selector, ledger, owned files, and restorable distribution immediately before mutation |

### 2.5 Toolchain and commands

- Install/dependency preparation: Python projects use `uv sync --frozen`; `on-brand` uses
  `npm ci`. Dependencies may populate ignored `.venv`/`node_modules` runtime directories inside the
  release workspace, but tracked-source verification ignores no tracked byte.
- Development command: N/A. The production manager is a one-shot CLI and has no server or watch
  process; invoke its subcommands directly from the repository root.
- Skill Mesh build: `powershell -NoProfile -File tools\build-distributions.ps1 -Provider all
  -OutputDir <absent-dist>` and `powershell -NoProfile -File tools\release.ps1 -Provider all
  -StageDir <absent-release-stage>`.
- Focused tests: `python -m pytest tests/production-toolchain` plus affected package-integrity and
  distribution tests.
- Typecheck/syntax gate: `python -m compileall -q tools/production-toolchain.py`; the repository has
  no configured static type checker.
- Lint/format gate: `git diff --check`; the repository has no configured source linter or formatter.
- Full test gate: repository-root `python -m pytest` with separately captured exit status.
- This is a one-shot release/cutover pipeline, not a daemon or scheduled process. The long-running
  observation trigger does not fire; the real producer→consumer smoke and attended substrate cutover
  are still mandatory in Steps 5 and 6.

### 2.6 Terms, prerequisites, and execution quickstart

- **Production bundle:** one immutable, versioned set of repository checkouts, prepared dependencies,
  retained Skill Mesh distributions, and evidence.
- **CLI:** command-line interface. **JSON:** JavaScript Object Notation. **UAT:** user acceptance
  test. **UTC:** Coordinated Universal Time. **SHA-256:** Secure Hash Algorithm with a 256-bit digest.
- **`HEAD^{tree}`:** Git's tree object for the exact tracked directory content of a commit; it binds
  content independently of branch names and timestamps.
- **Reparse point:** a Windows filesystem redirect such as a junction or symbolic link. Output-root
  checks reject one that could redirect a mutation outside the production base.
- **Ownership ledger:** `.skill-mesh-install.json`, the installer's record of provider-owned paths and
  exact installed hashes. It—not a generated marker alone—authorizes replacement/removal.
- **Fresh Codex process:** a newly started host process that rereads User environment and installed
  discovery roots; a new child conversation inside an already-running process does not satisfy it.
- **SDK/WDK/BCD:** software development kit, Windows Driver Kit, and Boot Configuration Data. They are
  named only as prohibited workstation surfaces in this phase.

Required local tools are Git, authenticated GitHub CLI (`gh`) for plan/issue administration,
Python 3.12, `pytest`, `uv` (Python project/dependency runner), Node.js matching `on-brand`'s committed
engine range, npm, and Windows PowerShell 5.1 or PowerShell 7. A missing tool stops before production
mutation; this phase performs no workstation-wide dependency installation. Require at least 5 GiB free
under `<prod-root>` before Step 5.

Fresh-context execution sequence:

1. In `<skill-mesh-root>`, run `git status --short`, `git rev-parse HEAD`, and
   `git rev-list --left-right --count HEAD...origin/main`; stop on unexpected dirt/divergence.
2. Read this plan in full and reverify the external registry/project identities named in Section 2.3.
3. Step 1 is complete. Run the remaining automated Steps 2–5 in order through
   `/build-phase --plan documentation/production-toolchain-separation-plan.md --steps 2,3,4,5`, or
   run the next single step through `/build-step` with that step's exact Problem, Issue, Done-when,
   Flags, and plan-step reference.
4. Stop before Step 6 unless Step 5's retained activation plan and bundle verify byte-for-byte. Step 6
   is attended even though the operator has authorized the production detour.
5. After Step 6 passes, execute Step 7 and hand Phase RD #178 to a fresh Terra context based on the
   actual new `main`.

## 3. Scope

### In scope

- A versioned, commit-pinned production workspace under `<prod-root>\releases`.
- A committed policy, strict schemas, fail-closed planner/stager/verifier, and external evidence.
- Independent Git clones created with no shared object hardlinks; no linked worktrees.
- Exact separation of utility executable code, live workspace, and mutable state.
- Updating existing canonical Skill Mesh utility invocation sites to honor both roots, regenerating
  all provider outputs, and documenting the provider-neutral contract.
- Retaining the exact Skill Mesh all-provider distribution that passed disposable verification.
- An attended activation using the existing installer and ownership ledger, environment persistence,
  a fresh Codex host process, representative real utility smokes, and tested rollback.
- Machine-visible deferral of the four named unfinished/embedded projects.
- Reorienting the preserved Phase RD #178 worktree against the new main after production activation.

### Out of scope

- Completing or activating `code-stencil`, `jurys-out`, `pocket-relay`, or `uat_sentinel`.
- Claiming all 13 utility projects are wired into Skill Mesh workflows; the existing utility-hookup
  plan retains ownership of advisory-call implementation.
- Restoring, bypassing, or weakening `--reviewers deep`; Phase RD remains authoritative.
- Editing frozen Phase IS UAT bytes, C2V/C2A records, the accepted Phase IS plan, C2N–C5 artifacts,
  certificates, Code Integrity/App Control/AppLocker policy, Secure Boot, BCD/boot configuration,
  drivers, SDK/WDK state, or the disposable-environment plan.
- Copying credentials, databases, ledgers, telemetry, task state, caches, evidence directories,
  donor worktrees, `.git` internals, or active installed-profile directories into a release.
- Directly copying generated Skill Mesh files into a host profile or using installer `-Force`.
- Mutating the live Claude or GPT profiles in release 1. All three distributions are built and
  disposable-tested; the attended live activation targets only Codex.

## 4. Impact Analysis

| File | Change Type | Reason | Verified |
|---|---|---|---|
| `config/production-portfolio-policy.json` | landed in Step 1 | Store category-driven membership, explicit additions, repository sharing, and deferred candidates | Shipped at `2e8e4f3`; registry membership is locked by the focused policy-contract suite |
| `schemas/production-portfolio-policy-v1.schema.json` | landed in Step 1 | Fail closed on policy drift | Shipped at `2e8e4f3`; Draft 2020-12 meta-validation and closed-boundary negatives pass |
| `schemas/production-bundle-v1.schema.json` | landed in Step 1 | Bind release identity, source trees, retained distribution, and gate evidence | Shipped at `2e8e4f3`; declarative shape and coherence negatives pass |
| `schemas/production-current-v1.schema.json` | landed in Step 1 | Bind active/previous selection and rollback evidence | Shipped at `2e8e4f3`; predecessor and selector-shape negatives pass |
| `schemas/production-activation-plan-v1.schema.json` | landed in Step 1 | Bind the sole attended host-mutation input and exact rollback actions | Shipped at `2e8e4f3`; provider and action-order negatives pass |
| `tools/production_record_contract.py` | landed in Step 1 | Strictly parse policy/records, reject duplicate JSON members, and perform reason-coded declarative consistency checks without minting runtime authority | Shipped at `2e8e4f3`; it remains a declaration checker, not runtime authority |
| `CLAUDE.md` | modified in Step 1 | Document the `jsonschema` dependency used by the strict record validator and its loud-at-call failure contract | Shipped at `2e8e4f3`; the dependency and failure contract are recorded |
| `tools/production-toolchain.py` | create | Implement `plan`, `stage`, `verify`, and activation-plan generation with argument-array subprocesses | `tools/` inventory has build/install/release scripts but no portfolio bundler |
| `tools/activate-production-toolchain.ps1` | create | Perform the attended, preflighted environment/profile switch and fail-closed rollback | Existing installer is `tools/install-skill-mesh.ps1`; no production-root activator exists |
| `_shared/utility-roots.md` | create | One owner for production-code versus live-workspace resolution | Existing generated shared-payload mechanism verified in `tools/build-distributions.ps1`; no utility-root shared contract exists |
| Existing utility-calling `skills/**/core.md` and provider adapters | modify | Replace bare relative executable lookup with the shared two-root contract while preserving target-root semantics | `rg` found active command sites for dev-observatory, citation-needed, b2_project_goblin, and switchboard; Step 4 must capture an exact before/after inventory and reject newly unclassified command sites |
| `documentation/providers/README.md`, `documentation/providers/claude.md`, `documentation/providers/gpt.md`, `documentation/providers/codex.md` | extend | Explain production root support, fresh-process inheritance, and unchanged provider authority | Files exist and are current provider documentation surfaces |
| `tests/production-toolchain/**` | created in Step 1; extend in later steps | Policy/schema, path safety, Git identity, no-copy, stage/verify, resolver, activation-plan, and rollback negatives | Step 1 shipped `test_policy_contract.py`; later manager, activation, resolver, and rollback suites remain prospective |
| `tests/package-integrity/expected_inventory.json`, focused `tests/package-integrity/**`, and `tests/distributions/**` | extend only where required | Record the new shared payload leaf, prove it ships in every relevant provider profile, and prevent direct relative calls from reappearing | Existing suites own generated closure and installed distribution behavior; shared assets are emitted transitively from canonical references |
| `README.md`, `plan.md`, `documentation/architecture.md` | modify narrowly | Publish the operating model and record the follow-up needed to supersede the remaining one-root assumption | Existing architecture separates canonical/generated/installed surfaces; the cross-repository utility-hookup plan remains a read-only dependency during this build and is updated only in its owning repository |
| `<prod-root>\**` | external create/mutate | Hold releases, data boundary, backups, retained artifacts, evidence, and selector | Path was absent during discovery; the selected volume had sufficient free capacity |
| Active Skill Mesh home and user environment | attended mutation | Install the exact retained candidate and select production code/live workspace roots | Existing installer/inspector own profile bytes; fresh-process boundary is already required by utility-hookup Step 5 |

## 5. New Components

### Production portfolio policy

The committed policy says which registry categories are included, which explicit projects are added,
which projects share a repository, and which known candidates are deferred. It does not pin release
commits; each generated `bundle.json` does that. The stager compares the live registry enumeration to
the policy before creating a release and reports added, missing, category-drifted, and unresolvable
entries.

### Declarative record contract

`tools/production_record_contract.py` is pure and non-mutating. It strictly decodes JSON with
duplicate-member rejection, validates all four Draft 2020-12 schemas through `jsonschema`, parses the
real singular `[[project]]` registry shape with `tomllib`, and reports stable reason codes for
membership, disposition, allowlist, grammar, lexical-path, and internal-coherence defects. It may
return ordinary declared values for display, but no `Validated*`, `Authorized*`, opaque token, or
other object accepted later as proof. Missing `jsonschema` fails loudly when validation is called;
the gate never skips or aborts unrelated test collection.

### Production bundle manager

`tools/production-toolchain.py` exposes four non-interactive commands:

1. `plan --source-root <dev> --prod-root <prod> --format json` performs no writes and returns the
   resolved repository/project inventory, eligibility, selected pushed commits, checkout layout,
   prospective bundle ID, and blockers.
2. `stage --source-root <dev> --prod-root <prod> --plan-file <captured-plan.json>` creates only a new,
   absent release directory. It clones local Git object stores with `--no-hardlinks`, checks out exact
   commits detached, resets each clone's origin to the canonical remote, prepares dependencies, builds
   a retained all-provider Skill Mesh release, and writes evidence plus `bundle.json` last.
3. `verify --bundle <release-dir>` reopens every clone and artifact, verifies commit/tree/remote,
   tracked cleanliness, policy and registry hashes, provider closure hashes, schema, forbidden-path
   absence, and smoke results. It is read-only.
4. `activation-plan --bundle <release-dir> --workspace-root <dev> --out <external-json>` validates
   the candidate and emits the exact old/new environment values, retained distribution, installer and
   inspector commands, rollback commands, and expected hashes. It does not mutate the host.

All filesystem inputs are resolved before mutation. A production output must be beneath the explicit
production root, a release path must be absent, and no reparse point may redirect a release or backup
outside that root. Git and subprocess commands use argument arrays, never interpolated shell strings.
Failures leave the prior active release and user environment unchanged.

### Shared utility-root contract

Every production utility call first requires an absolute, existing `DEV_UTILITIES_ROOT` that contains
the selected executable project and an absolute, existing `DEV_WORKSPACE_ROOT` for the target
portfolio. Executable lookup uses the former; `--root`, registry, project, ledger, index, or report
targets use the latter or a more specific caller-supplied target. Missing/relative roots halt with a
stable diagnostic before launching a utility. No fallback silently returns to a mutable sibling under
the current working directory once production mode is selected.

### Attended activator and rollback

The activator consumes the verified activation-plan JSON and exact retained distribution. It captures
the old user/process environment and active install inspector result to an external backup, performs
the existing installer transaction without `-Force`, inspects and hashes the resulting managed
closure, sets the two user environment variables, and writes `current.json` last. The operator then
opens a fresh Codex process and runs the representative smokes. Any pre-`current.json` failure restores
environment values and uses the installer-owned rollback route; changed owned bytes or foreign
collisions fail closed for manual recovery.

## 6. Design Decisions

### PROD-D1 — sibling production root

Use `<prod-root>`, not a directory inside `<dev-root>`. The development root is itself a dirty Git
repository, and nesting production beneath it would pollute status, backup, and discovery boundaries.

### PROD-D2 — immutable releases, not editable copies or linked worktrees

Each release is an independent no-hardlink clone set at exact pushed commits. A recursive copy could
carry ignored state and a linked worktree still depends on development Git object storage. Release
source files are never edited in place; upgrades create a new release.

### PROD-D3 — registry category plus explicit policy additions

The central registry remains the default membership source. `skill-mesh` and
`utility-project-standard` are explicit additions. The four named unfinished projects remain visible
as inactive/deferred policy entries until they meet reproducibility and functionality gates.

### PROD-D4 — code root, workspace root, and data root are distinct

`DEV_UTILITIES_ROOT` selects stable executables. `DEV_WORKSPACE_ROOT` selects the live portfolio those
executables inspect. Mutable databases, indexes, credentials, telemetry, and evidence remain outside
versioned code. Reusing one root for all three would either run development code or fork operational
history on every release.

### PROD-D5 — exact pushed objects, never working-tree bytes

Dirty source worktrees are observable but never copied. The selected commit must equal a pushed
upstream object, and staging reads that object through an independent clone. This permits the dirty
outer coding-root and local task-state without consuming either. `measure-twice` release 1 selects its
pushed `origin/master`, not the local blocked-checkpoint commit.

### PROD-D6 — no generic `current` junction

User environment points directly to the selected immutable release workspace, while `current.json`
records active and previous identities. This avoids a reparse-point retarget race and makes a fresh
process's executable root auditable. Rollback restores the prior exact environment path.

### PROD-D7 — retain the tested distribution

Step 5 retains the exact all-provider Skill Mesh distribution that passed disposable install,
reinstall, inspect, and uninstall. Step 6 installs those bytes; it never rebuilds during activation.

### PROD-D8 — fixed-scope code-review bootstrap exception

The operator authorization attaches only to the implementation scope of original pre-split Steps
1–4. The Step-2 sizing split adds no behavior or authority: original Step 2 is represented by revised
Step 2 (the four-command Python bundle manager) and revised Step 3 (the PowerShell activation,
closure-comparison, and rollback engine). The same fixed scope is therefore represented after
renumbering by revised Steps 1–5: record contract, bundle manager, activation engine, utility
routing, and real-release certification. Each uses `--reviewers code` because the mandatory deep-
review package is the unavailable dependency this detour is designed to isolate from ordinary work,
and each still requires fresh producer/reviewer contexts, all code-review lenses, the parent-only
deterministic verdict, zero High/Medium findings, focused gates, and the repository-root
`python -m pytest` DONE gate. This decomposition is not authority for new behavior and does not
cover revised Step 6, revised Step 7, Phase RD, or any other plan.

### PROD-D9 — one active mutation owner

Only Step 6 may change user environment values or the active Codex Skill Mesh profile. Steps 1–5 use
new release directories and disposable homes only. Step 6 invokes the existing installer and
inspector with exact provider `codex`; it never copies profile files directly or mutates live Claude
or GPT profiles.

### PROD-D10 — Phase RD resumes from new main, not by blind merge

No Phase PROD build-step runs concurrently with #178. After Step 6, inspect the preserved #178
worktree, classify its still-useful commits and uncommitted evidence against the new main, and open a
fresh Terra build-step from that actual main with the classified evidence in its prompt. Never merge
or rebase the preserved branch wholesale.

### PROD-D11 — declarations never mint runtime authority

Step 1 is the normative owner of policy and closed record grammar only. It cannot authenticate
producer-supplied hashes, bytes, paths, evidence, predecessor state, or rollback state. Step 2 owns
runtime verification machinery over independently opened Git/filesystem sources; Step 3 owns the
disposable activation transaction, exact closure comparator, and reversible rollback behavior;
Step 5 owns real release and executed-evidence certification; Step 6 owns the live active-state and
rollback pre-image immediately before mutation. No public caller-constructible validation object may
bypass those observations. This decision supersedes the rejected three-iteration `ValidatedBundle`
approach; none of its product files may be copied wholesale into a fresh build.

## 7. Build Steps

### Step 1: Lock the production portfolio and record schemas

- **Status:** DONE (2026-09-02)
- **Completion evidence:** commit `2e8e4f3e516c7069d07364ab5438e7f810675290`; 119 focused
  policy-contract tests passed; the candidate and post-merge repository-root gates each passed
  1543 tests with 1 skip; compile, private-path, and diff checks exited 0; five fresh no-history
  review lenses aggregated High=0 and Medium=0. Issue #184 is closed. No `<prod-root>`, host,
  profile, Phase IS/UAT, or later Phase PROD mutation occurred.
- **Problem:** Turn the approved production membership, deferred-candidate rules, root separation,
  source allowlists, and immutable record grammar into one machine-checkable declarative contract
  before any external directory is created, without claiming runtime verification or activation
  authority.
- **Type:** code
- **Issue:** #184
- **Files:** `CLAUDE.md`; `config/production-portfolio-policy.json`;
  `schemas/production-portfolio-policy-v1.schema.json`;
  `schemas/production-bundle-v1.schema.json`; `schemas/production-current-v1.schema.json`;
  `schemas/production-activation-plan-v1.schema.json`; `tools/production_record_contract.py`;
  `tests/production-toolchain/test_policy_contract.py`; this plan where exact implementation facts
  require reconciliation.
- **Existing context:** Section 2.3 is the complete release-1 project disposition. The registry
  category resolves the 13 default utility slugs; `skill-mesh` and `utility-project-standard` are
  explicit additions. Deferred projects are visible but cannot enter an executable or smoke matrix.
  The preserved rejected worktree and its three review rounds are evidence/test-idea sources only;
  reauthor this slice and do not copy any rejected product file wholesale.
- **Produces:** the exact release-1 declarative policy, including the 14-owner source/ref allowlist;
  four strict closed schemas; one pure reason-coded consistency helper that returns no trusted or
  validated capability; and structural regressions for declarative membership, disposition,
  source-allowlist, record-shape, lexical-path, and internal-coherence defects.
- **Done when:** the committed policy resolves a fixture using the real singular `[[project]]`
  registry shape to 15 active slugs and 14 owners with the exact embedded/deferred dispositions; all
  four schemas pass Draft 2020-12 meta-validation and close every reachable object boundary;
  duplicate JSON members are rejected before schema validation; every named negative is an
  individually reported test that asserts a stable intended reason code; the helper exposes no
  `Validated*`/`Authorized*` token and makes no Git/filesystem/evidence/profile/rollback truth claim;
  the focused policy-contract suite, repository-root `python -m pytest`, and `git diff --check` each
  exit 0 with captured status.
- **Named negatives:** root and nested duplicate JSON members; missing/duplicate/unknown singular-
  registry utilities; disposition overlap and wrong reason; owner/project/checkout duplication;
  wrong repository sharing; canonical-remote or allowed-ref drift including `measure-twice` not on
  `origin/master`; additional properties at every reachable object boundary; malformed commit/tree/
  SHA-256 and timestamp formats; lexical path escape, mixed separators, controls, reserved names,
  and trailing-dot/space aliases; bundle-ID/source-suffix mismatch; predecessor null-pair or
  self-reference; declared root collapse; provider/action-order drift; and shell-evaluation shapes.
- **Out of scope:** Git invocation/reachability, filesystem observation, tool/evidence-byte
  authentication, gate execution, retained-distribution proof, active-state inspection, activation
  execution, and rollback-pre-image authentication. These belong to Sections 2.4.1 and revised
  Steps 2/3/5/6.
- **Flags:** --isolation worktree --reviewers code --max-iter 3
- **Depends on:** none.
- **Review routing:** fixed-scope PROD-D8 exception (original Steps 1–4); zero High/Medium findings.

### Step 2: Build the fail-closed production bundle manager

- **Status:** PENDING / READY AFTER STEP 1
- **Problem:** Provide one four-command CLI whose release lifecycle derives candidates solely from
  independently reopened Git, filesystem, and tool authorities without changing the current
  production selection.
- **Type:** code
- **Issue:** #185
- **Files:** `tools/production-toolchain.py`;
  `tests/production-toolchain/test_bundle_manager.py`; manager/Git/filesystem fixtures under
  `tests/production-toolchain/fixtures/**`; the manager, staging, verification, and incomplete-
  release-recovery sections of `documentation/production-toolchain-operations.md`; this plan only
  for proven implementation-fact reconciliation. Step-1 policy, schemas, and
  `tools/production_record_contract.py` are read-only dependencies.
- **Existing context:** Section 5 defines the four commands and record order. Use Python 3.12 standard
  library plus repository test dependencies; parse TOML with `tomllib` and invoke Git/uv/npm/
  PowerShell with argument arrays. Step 1 supplies declarations only. Do not add a service, daemon,
  package manager, credential store, or caller-constructible runtime authority.
- **Produces:** the real `plan`, `stage`, `verify`, and `activation-plan` commands; independently
  derived Git/filesystem/tool observations; exact non-shell project-gate and activation action argv;
  bundle/evidence records written in the required order; and manager-side recovery guidance.
- **Done when:** tests invoke the real Python entry point and prove all four commands' declared
  behavior; `plan` and `verify` are read-only; `stage` writes only a new absent release directory and
  writes `bundle.json` last; `activation-plan` is non-mutating and emits complete typed operations or
  argv for the existing installer/inspector interfaces. Disposable repositories prove independent
  `--no-hardlinks` clones, detached exact commits, canonical remotes, allowed refs, fetched
  reachability, exact commit/tree/required-blob identities, sibling layout, dirty/untracked
  exclusion, and pushed-object eligibility. Policy/registry drift, case/path/reparse/collision,
  forbidden-state, repeated-output, alias/containment, tamper, and caller-supplied script-byte/hash
  plants fail closed; installer/inspector identity is derived from verified Skill Mesh Git objects;
  no Step-1 validation result is accepted as runtime proof; every failure leaves the prior
  `current.json` byte-identical. The focused bundle-manager suite, the compile check
  `python -m compileall -q tools/production-toolchain.py`, repository-root `python -m pytest`, and
  `git diff --check` each exit 0 with captured status.
- **Out of scope:** activation execution, active-profile mutation, the exact installed-closure
  comparator, rollback execution, real-release gate execution/evidence, and live-state authority.
- **Flags:** --isolation worktree --reviewers code --max-iter 3
- **Depends on:** Step 1.
- **Review routing:** fixed-scope PROD-D8 exception inherited from original Step 2; zero High/Medium
  findings.

### Step 3: Build the reversible production activation engine

- **Status:** PENDING / BLOCKED ON STEP 2
- **Problem:** Turn a declarative activation plan into one fail-closed transaction whose observable
  result is either the exact requested profile/environment/selector closure or the exact
  independently captured pre-image.
- **Type:** code
- **Issue:** #190
- **Files:** `tools/activate-production-toolchain.ps1`;
  `tests/production-toolchain/test_activation_contract.py`; activation/home/ledger/rollback fixtures
  under `tests/production-toolchain/fixtures/**`; the activation, closure-verification, rollback, and
  manual-recovery sections of `documentation/production-toolchain-operations.md`; this plan only for
  proven implementation-fact reconciliation. The Step-2 manager, four schemas, and existing build,
  release, installer, inspector, transaction, and path-guard tools are read-only dependencies unless
  a failing production-caller test returns a defect to their owning step.
- **Existing context:** Consume a valid activation plan emitted by the real Step-2 CLI, but treat that
  record as declarative. The existing inspector reports inventory/link/marker and ledger-provider
  state; it does not authenticate the exact installed-file closure. The activator must own that
  comparator and orchestrate the existing installer without force.
- **Produces:** the real PowerShell activator entry point; exact retained-dist/ledger/installed-file
  closure comparison; independent preflight; write-last selector publication; fail-closed rollback;
  and operator recovery guidance. This build step produces no live authority.
- **Done when:** end-to-end tests invoke the real PowerShell entry point against disposable homes and
  use a valid activation plan emitted by the real Step-2 `activation-plan` command. Immediately
  before fixture mutation, the activator independently reopens the plan, bundle, retained
  distribution, resolved home/backup/selector paths, installer/inspector bytes, current selector,
  ledger, installed owned bytes, and rollback pre-image. Schema, hash, provider, home, environment,
  script, argument, ordering, path/reparse, collision, and predecessor drift each fail before the
  first mutation. The install call matches `-Provider codex -Home <home> -DistDir <retained-dist>` and
  uses neither `-Force` nor `-ForceShared`; the inspector call matches `-Home <home> -Format json`.
  The activator-owned comparator derives the retained Codex file set, validates the ledger's exact
  `owned_files`/`owned_file_hashes` bijection, reopens installed bytes, and proves zero missing,
  stale, unledgered, foreign-at-managed-path, or hash-mismatched entries. Success publishes fixture
  `current.json` last. Planted failures after each mutation class restore the exact fixture Process/
  User environment, selector, ledger, and owned bytes; rollback refuses changed pre-image or target
  authority. Tests prove no real User environment, active host profile, or external production root
  changes. The focused activation-contract suite, a Windows PowerShell 5.1 parse check,
  repository-root `python -m pytest`, and `git diff --check` each exit 0 with captured status.
- **Out of scope:** utility-call routing, staging a real portfolio release, writing the real
  production base, mutating a live host profile or User environment, fresh-host smoke, or claiming
  live rollback authority. Step 6 must recapture the real pre-image immediately before mutation.
- **Flags:** --isolation worktree --reviewers code --max-iter 3
- **Depends on:** Step 2.
- **Review routing:** fixed-scope PROD-D8 exception inherited from original Step 2; zero High/Medium
  findings.

### Step 4: Route Skill Mesh utility calls through production code

- **Status:** PENDING / BLOCKED ON STEP 3
- **Problem:** A stable bundle is ineffective while installed skills still launch utilities from
  cwd-relative development paths; make executable-root and target-workspace selection explicit across
  every current utility command without claiming unbuilt advisory hookups.
- **Type:** code
- **Issue:** #186
- **Files:** `_shared/utility-roots.md`; exact utility-calling `skills/**/core.md` and provider
  adapters found by the pre-change inventory; `documentation/providers/README.md`;
  `documentation/providers/claude.md`; `documentation/providers/gpt.md`;
  `documentation/providers/codex.md`; `documentation/architecture.md`;
  `tests/production-toolchain/test_utility_root_contract.py`; affected package-integrity and
  distribution tests.
- **Existing context:** Before editing, enumerate command-bearing references to dev-observatory,
  citation-needed, b2_project_goblin, and switchboard and classify executable, inert/example, or
  non-command. Edit only executable consumers plus the one shared contract. Preserve each utility's
  existing target-root and failure semantics. The utility-hookup plan retains ownership of new
  advisory calls.
- **Produces:** one shipped shared two-root contract, capability-equivalent provider wording,
  migrated current command sites, a checked command-site inventory, and generated-profile proof.
- **Done when:** every executable utility invocation resolves code below absolute
  `DEV_UTILITIES_ROOT`; every workspace/registry/project/data target resolves from caller input or
  absolute `DEV_WORKSPACE_ROOT`; missing/relative/wrong-shape roots stop before subprocess launch;
  tests plant bare-relative, same-root, cwd-fallback, deferred-project, and provider-output negatives;
  all three profiles contain the contract and representative migrated commands; focused suites,
  repository-root `python -m pytest`, and `git diff --check` each exit 0 with captured status.
- **Flags:** --isolation worktree --reviewers code --max-iter 3
- **Depends on:** Step 3.
- **Review routing:** fixed-scope PROD-D8 exception (original Steps 1–4); zero High/Medium findings.

### Step 5: Stage and certify the first production bundle

- **Status:** PENDING / BLOCKED ON STEP 4
- **Problem:** Freeze one exact release-1 bundle and Skill Mesh distribution with real-project and
  disposable-install evidence before any user environment or active profile changes.
- **Type:** code
- **Issue:** #187
- **Files:** no canonical product mutation beyond narrowly required test/operations corrections;
  external `<prod-root>\releases\<bundle-id>\**` and disposable homes only;
  `documentation/findings/production-toolchain-release-1.json` records redacted immutable evidence.
- **Existing context:** Reverify every remote/upstream and actual commit. Use the pushed
  `measure-twice` commit. Preserve source dirt by selecting Git objects, not by stashing or cleaning.
  Run the bundle manager from a clean Skill Mesh commit; the retained distribution must be produced
  with `-Provider all`, never the default `both`.
- **Produces:** initial versioned workspace, dependencies, complete `bundle.json`, retained Skill Mesh
  release/checksums, disposable install evidence, representative utility health results, and a
  non-mutating activation plan.
- **Done when:** all 15 active project slugs resolve at their exact selected objects; every clone is
  independent and tracked-clean; actual remote/ref/reachability/commit/tree/required-blob results are
  recorded for all 14 owners; `uv sync --frozen`/`npm ci` and each exact Step-2-owned CLI `--help`
  argv pass with one unique gate identity, captured exit sentinel, exact evidence bytes, and hashes;
  Skill Mesh all-provider build is reproducible; disposable Claude/GPT/Codex install, reinstall,
  inspect, and uninstall pass with exact closures and no residue; the repository-root
  `python -m pytest` and `git diff --check` exit 0 at the recorded commit; two fresh reviews of the
  release evidence report zero High/Medium findings; the actual pre-stage selector (or proven
  absence) derives `bundle.previous_bundle_id`; final-path/reparse/no-hardlink measurements cover the
  real release; retained provider closures plus Step-2 manager and Step-3 activator Git-blob/byte
  identities are frozen; `verify` reopens all authorities and rereads the retained bundle; the activation plan is
  called declaratively valid, never authorized; and no user environment or active profile byte
  changed.
- **Flags:** --isolation worktree --reviewers code --max-iter 3
- **Depends on:** Step 4.
- **Review routing:** fixed-scope PROD-D8 exception (original Steps 1–4); zero High/Medium findings plus
  the two release-evidence reviews.

### Step 6: Activate and smoke the production toolchain

- **Status:** PENDING / ATTENDED CUTOVER
- **Problem:** The certified source and distribution do not protect daily work until fresh host
  processes actually execute the production code while targeting the live development workspace.
- **Type:** operator
- **Issue:** #188
- **Existing context:** Consume only Step 5's exact declaratively valid activation-plan JSON and retained
  distribution. The operator approved the production detour and cutover; this step still fails closed
  on identity drift, active owned-byte drift, collision, or failed smoke. It does not alter any
  certificate, policy, boot, SDK/WDK, driver, Phase IS artifact, or frozen UAT.
- **Produces:** selected user environment roots, installer-owned active profile, external backup and
  cutover evidence, `current.json`, a fresh-process smoke report, and retained rollback authority.
- **Done when:** preflight reopens and hashes the bundle, retained distribution, tool scripts,
  activation record, old selector, Process/User environment, ledger, active owned bytes, and exact
  rollback pre-image; predecessor identity/path agree with Step 5 evidence; the old active profile
  and environment equal the activation plan;
  the existing installer consumes the Codex profile from the retained all-provider distribution via
  exact `-Provider codex` without `-Force`; the inspector reports inventory/link/marker and ledger-
  provider state, while the Step-3-owned exact closure comparator proves zero missing, stale,
  unledgered, foreign-at-managed-path, or hash-mismatched entries against the retained Codex
  distribution and current ledger; only the complete frozen argv is executed after those checks;
  user and process
  values select the exact production workspace and live development workspace; a fresh Codex process
  sees both values and runs installed Skill Mesh plus representative `observatory`, `goblin`, `cite`,
  `onbrand`, and `utility-standard` `--help` commands from production code, plus `observatory doctor
  --root <dev-root>`, against safe read-only development targets; `current.json` is written
  last as a declarative result record and verifies; rollback is derived from the independently
  captured live pre-image, rehearsed in a disposable home, and its exact command is retained.
  Any failure restores the old environment/profile
  or stops with the old release still selected.
- **Depends on:** Step 5.

### Step 7: Reconcile status and resume the review-deep critical path

- **Status:** PENDING / BLOCKED ON STEP 6
- **Problem:** Production activation must be durable in project documentation and the paused Phase RD
  repair must restart against the new main without losing or blindly merging preserved #178 evidence.
- **Type:** code
- **Issue:** #189
- **Files:** `README.md`; `plan.md`; this plan; `.claude/artifacts/phase-is-whats-next.html` if still
  present and authoritative as an operator view; task-state handoff surfaces. Treat
  `../documentation/utility-hookup-plan.md` as a read-only dependency and record a follow-up for its
  owning repository; do not edit it from a Skill Mesh build-step worktree.
- **Existing context:** Phase PROD does not satisfy Phase RD or unblock deep-dependent consumer plans.
  Inspect the preserved #178 worktree and branch, compare every changed path to the new main, retain
  evidence, and create a fresh transition prompt. Do not merge, close #178, or claim deep support in
  this administrative step.
- **Produces:** accurate production operating/rollback docs, reconciled plan statuses, recorded
  deferred-candidate backlog, and an evidence-backed fresh-Terra Phase RD transition.
- **Done when:** documentation identifies the exact active bundle and rollback, the owning-repository
  follow-up for the utility-hookup plan's one-root wording is recorded, all production issues/statuses
  agree, Git is clean and synchronized, and the next action is a fresh #178 build-step against actual
  main with its preserved salvage classified. The focused production-toolchain suite,
  repository-root `python -m pytest`, and `git diff --check` each exit 0 with captured status.
- **Flags:** --isolation worktree --reviewers code --max-iter 3
- **Depends on:** Step 6.
- **Review routing:** routine post-cutover code review with zero High/Medium findings; PROD-D8 applies
  only to the fixed original Steps 1–4 scope and is not authority for this step.

## 8. Risks and Open Questions

| Item | Risk | Mitigation |
|---|---|---|
| False immediate-unblock claim | A production copy is mistaken for restored deep review | Keep the limitation in the plan, active docs, and transition; #178–#181 remain mandatory |
| Dirty source contamination | Recursive copy captures unrelated work/state | Clone exact pushed objects with `--no-hardlinks`; never read working-tree payload bytes |
| Split-brain roots | Stable code writes into a versioned release or inspects the wrong registry | Require separate absolute utility/workspace roots and explicit data targets |
| Runtime dependency drift | `.venv` or `node_modules` changes beneath stable source | Use lockfile installs, record tool/lock hashes and smoke evidence, verify tracked closure independently |
| Registry drift | New utilities are silently absent from production | Stage compares the exhausted registry category set to policy and refuses unclassified changes |
| Deferred project misrepresentation | Skeleton projects appear as usable production commands | Machine-visible deferred/embedded states; active set and smoke matrix reject them |
| Active profile damage | Direct copies bypass ledger/current-byte authority | Existing installer/inspector only, retained exact dist, external backup, no `-Force`, fail-closed rollback |
| Release/source mismatch | Rebuild during cutover installs unreviewed bytes | Step 6 consumes Step 5's retained artifact and hashes; never rebuild |
| Phase RD overlap | Preserved #178 changes clobber or are clobbered by PROD | No concurrent build-step; post-cutover path-by-path salvage and fresh baseline |
| Mutable data loss/fork | Release switch strands databases/indexes/telemetry | Data stays outside releases; explicit existing paths or `<prod>\data`; cutover verifies continuity |
| Stale host environment | Current process sees new values but fresh hosts do not | Persist User values, open a genuinely fresh process, and verify exact paths there |
| Rollback schema evolution | Older installer cannot understand newer ledger/WAL | Retain the newer installer as rollback executor and record it in the activation plan |
| Declarative record mistaken for authority | Producer-controlled bytes/hashes or a forgeable validation object bypass independent observation | Enforce PROD-D11 and the Section 2.4.1 ownership table; every runtime consumer reopens its own authorities |

No unresolved operator choice remains for revised Steps 1–5. Step 6's release path, hashes, and
old/new environment values are derived from Step 5 evidence rather than chosen conversationally.

## 9. Testing Strategy

### Contract and unit tests

- Validate all four strict schemas and exact policy membership/dispositions/source allowlists.
- Plant individually named, reason-coded duplicate-member, missing, duplicate, unknown,
  category-drifted, shared-owner, additional-property, bad-hash, lexical-path, and active-deferred
  fixtures. Runtime reparse, reachability, byte-authentication, activation, evidence, active-state,
  and rollback negatives remain in their owning Steps 2, 3, 5, and 6.
- Test release-ID parsing, deterministic ordering, command argument arrays, exact record hashing,
  write-last behavior, and redaction/no-credential rules. Add a structural guard that Step 1 exposes
  no `Validated*`/`Authorized*` capability API.

### Git/filesystem integration

- Create disposable repositories with dirty tracked/untracked/ignored content and prove only exact
  commits appear in independent no-hardlink clones.
- Reject unpushed/non-remote active entries, origin/tree drift, repeated output directories,
  repository-sharing disagreement, case collisions, and tampered bundles.
- Snapshot the prior selector/environment fixtures across every failure and prove no mutation.

### Skill/distribution integration

- Inventory every canonical executable utility call before and after migration.
- Plant bare-relative and cwd-fallback regressions and verify they fail structurally.
- Build Claude, GPT, and Codex profiles; assert the shared root contract and representative commands
  exist with equivalent semantics.
- Install, reinstall, inspect, and uninstall each profile in disposable homes from the retained
  distribution, verifying exact file closure and no residue.

### Real release smoke

- Stage from the actual portfolio, prepare locked dependencies, and run each active CLI's non-mutating
  `--help`; additionally run `observatory doctor --root <dev-root>` as the portfolio health
  command.
- Run the full Skill Mesh repository gate at the exact candidate commit and retain exit sentinels and
  hashes outside the source tree.
- Rerun read-only bundle verification after evidence is frozen and immediately before activation.

### Attended substrate and rollback

- Capture pre-image environment/profile evidence, install only the retained candidate, start a fresh
  host, and prove representative installed skills launch production utilities against safe live-dev
  targets.
- Exercise rollback in disposable state first; retain the exact active rollback command and previous
  release until at least two later bundles have passed.
- A smoke failure is not patched live. Restore or remain on the prior bundle, return the defect to the
  owning code step, rebuild a new bundle ID, and repeat certification.
