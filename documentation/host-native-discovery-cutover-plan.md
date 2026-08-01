# Host-Native Discovery and Consumer Cutover Plan

## 1. What This Feature Does

**Proposal:** `documentation/host-native-discovery-cutover-proposal.html`

This feature closes the gap between the provider-neutral package shipped by
`aberson/skill-mesh` and the still-active legacy installation under
`coding-root/.claude`. It makes host instruction loading and skill discovery
explicit, adds a safe and reversible migration path for pre-existing unowned
skill trees, proves Claude and GitHub Copilot installations in isolated homes,
and produces a bounded operator handoff for the private `coding-root` consumer.
The result is that the `coding-root` consumer is migrated transactionally:
Claude discovers only its generated Claude profile, Copilot discovers only its
generated GPT profile, and neither host depends on the historical
`.claude/skills-gpt` source layout.

This plan supersedes the unexecuted acceptance intent of Step 41 in
`documentation/provider-neutral-skill-mesh-plan.md`; it does not reopen the
completed provider-neutral source, router, distribution, or release work from
Steps 33-40.

## 2. Existing Context

- `skills/<name>/core.md` plus `providers/claude.md` and `providers/gpt.md` are
  canonical in this repository, per `config/skill-manifest.json`.
- `tools/build-distributions.ps1` already emits host-native `SKILL.md` discovery
  trees under `dist/claude` and `dist/gpt`.
- `tools/install-skill-mesh.ps1` already installs Claude into
  `<Home>/.claude/skills` and GPT into `<Home>/.copilot/skills`, records an
  ownership ledger, refuses foreign-file collisions by default, and supports
  ownership-safe uninstall.
- `runtime/skill-router.ps1` is provider-neutral and defaults to trustworthy
  host metadata, while the consumer workspace still has the legacy
  `.claude/lib/skill-router.ps1` v1.2 implementation and no `.copilot/skills`
  installation.
- The current Copilot CLI runtime can inject the consumer workspace's
  `CLAUDE.md` and expose a host-side skill registry even without a root
  `AGENTS.md` or `.copilot/skills` tree. That behavior is host integration, not
  proof that native GPT discovery is installed correctly.
- The private consumer's `CLAUDE.md` says `.claude/skills` is a junction, but
  live inspection shows ordinary directories. It also reports the older
  Phase 1-4 / 35-test state. Those private facts must be corrected in
  `coding-root`, not copied into this public package.
- `documentation/migration.md` still describes Step 41 as not yet run. The live
  absence of `.copilot/skills` confirms that GPT host-native cutover is not
  complete.

### Terms and command surface

- **Consumer home:** the root passed to installer and migration commands; for
  final acceptance this is `C:\Users\abero\dev`.
- **Backup directory:** an operator-selected absolute directory outside
  `.claude/skills`, `.claude/skills-gpt`, and `.copilot/skills`. `-Apply`
  requires `-BackupDir`; there is no implicit destructive default.
- **Release candidate:** a clean checkout or release staging tree whose
  checksums pass `tools/release.ps1`; migration records its commit/tag and
  distribution checksums in the backup manifest.
- Angle-bracket tokens in existing path examples, such as `<Home>` and
  `skills/<name>`, are defined CLI/path metavariables, not unresolved design
  choices. New commands in this plan use concrete fixture paths or the defined
  consumer-home and backup-directory terms above.

Existing command surface:

```powershell
python -m pytest
powershell -File tools\build-distributions.ps1 -Provider both
powershell -File tools\install-skill-mesh.ps1 -Provider claude -Home "C:\path\to\consumer"
powershell -File tools\install-skill-mesh.ps1 -Provider gpt -Home "C:\path\to\consumer"
powershell -File tools\release.ps1
```

This repository has no separate dependency-install, development-server, lint,
or typecheck command. Python 3 with pytest and Windows PowerShell are required
for the existing tests; real acceptance additionally requires installed,
authenticated Claude Code and GitHub Copilot CLI hosts. Junction-specific tests
skip visibly when the host cannot create Windows junctions.

### Repository boundary

- **Build repository:** `aberson/skill-mesh` at
  `C:\Users\abero\dev\skill-mesh`. All code steps in this plan modify and commit
  only this repository.
- **Consumer workspace:** `aberson/coding-root` at `C:\Users\abero\dev`. It is
  read-only during code steps and temporary-home acceptance, then modified only
  by the final live-substrate operator step after rollback rehearsal passes.
- **Private instruction content:** `coding-root/CLAUDE.md`, the future root
  `AGENTS.md`, workspace-specific rules, hooks, memories, and project
  instructions remain private consumer artifacts. This public repository owns
  their loading contract and migration guidance, not their content.
- **No cross-repository build step:** any permanent `coding-root` documentation
  or instruction refactor becomes a separate coding-root plan after this
  package proves the cutover mechanics and emits the exact consumer handoff.

## 3. Scope

### In scope

- Document the difference between workspace instructions, host-native skill
  discovery, and explicit router dispatch.
- Add a read-only inspection command that reports which instruction and skill
  roots exist, whether files are generated/owned, and which legacy surfaces
  still shadow the canonical package.
- Add a safe migration command for an existing foreign `.claude/skills` tree:
  dry-run by default, complete backup manifest, explicit apply, rollback, and
  no reliance on blind `-Force`.
- Preserve installer ownership guarantees and support independent Claude and
  GPT profiles in one consumer home.
- Add hermetic tests for clean install, legacy collision classification,
  migration, rollback, reinstall, and uninstall.
- Produce a consumer handoff that tells `coding-root` exactly how to add a root
  `AGENTS.md`, make `CLAUDE.md` and `AGENTS.md` thin adapters over one private
  shared instruction source, update stale status text, install both provider
  profiles, and retire legacy files only after native acceptance.
- Run real host-native acceptance for one representative skill in Claude Code
  and one in GitHub Copilot CLI before declaring the cutover complete.
- Apply the reviewed migration to `coding-root` as a separate live-substrate
  operator step, retain the rollback backup, and verify both real hosts there.

### Out of scope

- Publishing private `coding-root` instructions, rules, hooks, memory, or
  project adapters.
- Changing skill behavior, reviewer gates, model mappings, or transport
  authentication.
- Treating `AGENTS.md` as a skill catalog; it is a workspace instruction
  adapter, while skills live in provider discovery directories.
- Depending on undocumented runtime injection of `CLAUDE.md` as the GPT
  installation mechanism.
- Deleting the public repository's deprecated top-level skill directories.
- Automatically editing a dirty consumer worktree or using `-Force` to
  overwrite unknown files.
- Running a single `/build-phase` across both Git repositories.

## 4. Impact Analysis

| File or area | Change Type | Reason | Verified |
|---|---|---|---|
| `tools/install-skill-mesh.ps1` | extend | Expose migration-safe integration without weakening marker/ledger ownership rules | Read installer: provider roots are `.claude/skills` and `.copilot/skills`; foreign files are refused unless `-Force`; ledger is an index, marker is authority |
| `tools/inspect-host-install.ps1` | add | Give operators a read-only truth report before migration | Live inspection required separate commands for roots, link type, provenance, router version, and instruction files |
| `tools/migrate-legacy-install.ps1` | add | Back up, adopt, replace, and roll back a legacy unowned install without blind overwrite | Existing installer has no adoption path; `-Force` intentionally takes ownership but does not provide legacy backup/rollback |
| `tools/skill-mesh-provenance.ps1` | reuse | Keep one ownership-marker parser for installer, inspector, and migration without changing its public helper contract | Grep confirmed installer and distribution builder already dot-source this file |
| `tests/distributions/test_distributions.py` | extend | Cover inspection and legacy migration lifecycle | Existing distribution tests cover generated profiles and install safety but not real legacy adoption |
| `tests/fixtures/` | extend | Provide deterministic legacy and mixed-ownership homes | Current smoke fixtures model router behavior, not consumer-home migration |
| `documentation/host-discovery.md` | add | Explain instruction loading, skill discovery, and router dispatch as separate mechanisms | Live state showed these mechanisms were conflated by folder naming and missing `AGENTS.md` |
| `documentation/migration.md` | modify | Replace stale Step-41 wording with the safe cutover path and consumer handoff | File currently says Step 41 is not yet run and describes only the pre-cutover state |
| `documentation/providers/claude.md` | modify | Point Claude users to inspection/cutover and native acceptance | Current guide documents clean installation only |
| `documentation/providers/gpt.md` | modify | Explain `.copilot/skills`, `AGENTS.md`, and why current runtime injection is not native installation | Current guide documents target discovery but not the absent-live-install failure mode |
| `README.md` | modify | Add a concise inspect-before-install/cutover route | Current install section assumes a clean or already-owned target |
| `documentation/coding-root-cutover-handoff.md` | add | Bound the private follow-up without embedding private content | Repository boundary requires consumer-specific edits to happen in a separate coding-root change |
| `coding-root/CLAUDE.md` | consumer follow-up only | Become a thin host adapter over one private shared instruction source and remove stale topology/status claims | Read live file; not modified by this plan's code steps |
| `coding-root/AGENTS.md` | consumer follow-up only | Give GPT hosts an explicit root workspace instruction adapter | Bounded search found no applicable root `AGENTS.md`; not modified by this plan's code steps |
| `coding-root/.claude/skills`, `.claude/skills-gpt`, `.claude/lib/skill-router.ps1`, `.copilot/skills` | live-substrate operator step only | Replace legacy active implementation with generated provider-bound installs | Live inspection found ordinary legacy directories, v1.2 router, and no `.copilot/skills` |

No public function signature or manifest schema needs to change unless shared
provenance parsing cannot support the inspector/migrator. If a signature changes,
all call sites in `tools/build-distributions.ps1`,
`tools/install-skill-mesh.ps1`, and distribution tests must be updated together.

## 5. New Components

| Component | Purpose |
|---|---|
| `tools/inspect-host-install.ps1` | Read-only JSON/text inventory of workspace instruction files, Claude/GPT discovery roots, provenance ownership, link types, router version, ledger state, and legacy shadowing |
| `tools/migrate-legacy-install.ps1` | Dry-run-first migration with backup manifest, exact collision classification, explicit apply, post-install verification, and rollback |
| `tests/fixtures/legacy-install/` | Synthetic legacy, mixed-owned, foreign, and partially migrated consumer homes |
| `documentation/host-discovery.md` | Authority map for workspace instructions vs skill discovery vs router dispatch |
| `documentation/coding-root-cutover-handoff.md` | Copy-pasteable private-consumer follow-up, including the required `AGENTS.md`/`CLAUDE.md` shared-source design |

### Data contracts

`HostInstallReport` is the stable JSON output of the inspector:

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | integer (`1`) | Parser compatibility |
| `consumer_home` | string | `.` by default; absolute only when explicitly requested |
| `instruction_files` | array | Relative path, presence, and evidence class for root host instructions |
| `profiles` | object keyed by `claude`, `gpt` | Discovery root, state, link type, owned/unowned counts, and adapter sample |
| `ledger` | object | `absent`, `valid`, or `corrupt`; provider names only |
| `router` | object | Relative path, semantic version when parseable, and `canonical`, `legacy`, or `absent` classification |
| `legacy_shadows` | array of strings | Relative legacy paths that can still affect resolution |
| `warnings` | array of stable code/message objects | Actionable findings without credential values or file contents |

Instruction evidence classes are `observed` (the host exposes runtime
provenance), `host-convention` (a documented discovery convention plus a file
present at that path), and `unknown`. The inspector never upgrades
`host-convention` to `observed`.

`MigrationPlan` is the dry-run output consumed by `-Apply`:

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | integer (`1`) | Parser compatibility |
| `migration_id` | string | Stable transaction identifier |
| `source_release` | object | Commit/tag plus distribution checksums |
| `consumer_home` | string | Canonical absolute target used only in the local plan file |
| `backup_dir` | string | Canonical absolute operator-selected backup |
| `actions` | ordered array | Relative path, provider, action (`backup`, `install`, `retire`), and precondition hash |
| `blocked` | array | Foreign/unsafe paths and stable reason codes |

`BackupManifest` is written before target mutation:

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | integer (`1`) | Parser compatibility |
| `migration_id` | string | Joins backup, transaction log, and rollback |
| `created_utc` | RFC 3339 UTC string | Audit timestamp |
| `source_release` | object | Same immutable release identity as the plan |
| `original_files` | array | Relative path, size, SHA-256, and backup payload path |
| `original_ledger` | object or null | Byte-preserved ledger payload path and SHA-256 |
| `installed_files` | array | Relative path and expected SHA-256 for generated output |
| `status` | `prepared`, `applied`, `rolled_back` | Transaction state |

- `migration_id`: `yyyyMMddTHHmmssZ-<8 lowercase hex>`, generated once from UTC
  time plus four cryptographically random bytes; used as the backup directory
  leaf and transaction-log key.
- Stable warning/reason codes are uppercase snake case, for example
  `FOREIGN_FILE`, `UNSAFE_LINK`, `CORRUPT_LEDGER`, and `PROFILE_MISSING`.

### New CLI contracts

Read-only inspection:

```powershell
powershell -File tools\inspect-host-install.ps1 `
  -Home "C:\path\to\consumer" `
  [-Format text|json] `
  [-AbsolutePaths]
```

- `-Home` is required.
- `-Format` defaults to `text`; `json` emits exactly one
  `HostInstallReport`.
- `-AbsolutePaths` is opt-in and affects path display only.
- The command never prompts, mutates, authenticates, or calls a cloud service.

Migration planning and apply:

```powershell
# Dry-run: emits MigrationPlan, no mutation
powershell -File tools\migrate-legacy-install.ps1 `
  -Home "C:\path\to\consumer" `
  -DistDir "C:\path\to\release\dist" `
  -BackupDir "C:\path\to\private-backups"

# Apply exactly the validated plan
powershell -File tools\migrate-legacy-install.ps1 `
  -Home "C:\path\to\consumer" `
  -DistDir "C:\path\to\release\dist" `
  -BackupDir "C:\path\to\private-backups" `
  -Apply

# Roll back one applied transaction
powershell -File tools\migrate-legacy-install.ps1 `
  -Home "C:\path\to\consumer" `
  -BackupDir "C:\path\to\private-backups" `
  -Rollback `
  -MigrationId "20260731T210000Z-a1b2c3d4"
```

- `-Home`, `-DistDir`, and `-BackupDir` are required for dry-run and apply.
- `-Apply` consumes the freshly recomputed plan; it aborts if any precondition
  hash differs from the dry-run/backup state.
- `-Rollback` is mutually exclusive with `-Apply`, requires `-MigrationId`,
  and reads release identity and payload locations from `BackupManifest`.
- No interactive confirmation exists. Omitting `-Apply` is the safe preview.
- Exit codes are `0` success, `1` operational failure with no incomplete
  rollback, `2` blocked/unsafe precondition, and `3` rollback failure requiring
  manual recovery from the retained backup.

## 6. Design Decisions

### Public package owns mechanics; consumer owns private instructions

`skill-mesh` will document and test how hosts load instructions and skills, but
will not ship the contents of `coding-root/CLAUDE.md` or a personalized
`AGENTS.md`. The handoff prescribes one private shared instruction source with
thin host adapters. Alternative rejected: copying `CLAUDE.md` into this public
repository, which would leak workspace-specific paths, policies, and memory
references.

### Host binding is the normal path

Claude loads generated files from `.claude/skills`; Copilot loads generated
files from `.copilot/skills`. The router remains an explicit cross-provider and
headless execution path, not the prerequisite for native skill invocation.
Alternative rejected: relying on the current Copilot runtime's ability to
inject `CLAUDE.md` and expose `.claude` skills, because that obscures which
provider adapter executed and is not a portable installation contract.

### `AGENTS.md` and `CLAUDE.md` are instruction adapters, not skill registries

The consumer follow-up will use one private shared instruction document and
thin root adapters for each host. Neither adapter enumerates or embeds skill
implementations. Alternative rejected: duplicating the full workspace contract
in both files, which guarantees drift.

### Migration is not `-Force`

The migration command must classify every target, require an explicit
`-BackupDir`, create a byte-for-byte backup and manifest before the first
mutation, require explicit `-Apply`, verify both generated profiles, and
support rollback. Claude and GPT installation are one transaction: failure in
either profile restores the pre-migration home and ledger. Existing `-Force`
remains an expert override for isolated collisions, not the documented legacy
cutover. Unknown foreign files are never silently adopted, overwritten, or
deleted.

### The consumer repository remains a separate change

This plan produces the tested package and an exact handoff. Permanent changes
to `coding-root/CLAUDE.md`, new `coding-root/AGENTS.md`, and deletion of legacy
tracked files occur in a separate coding-root branch/plan after host acceptance.
This preserves repository ownership and prevents a skill-mesh build worktree
from committing unrelated dirty coding-root state.

## 7. Build Steps

### Step 42: Lock and test the host-loading authority map
- **Problem:** Operators cannot distinguish workspace instruction injection, host-native skill discovery, and router dispatch, so a GPT model running successfully can be mistaken for a correctly installed GPT profile.
- **Type:** code
- **Issue:** #
- **Flags:** --reviewers code --isolation worktree
- **Files:** `documentation/host-discovery.md`, `documentation/providers/claude.md`, `documentation/providers/gpt.md`, `tests/package-integrity/`
- **Produces:** A source-grounded authority map, explicit `AGENTS.md`/`CLAUDE.md` roles, discovery-root table, router role, and package-integrity assertions that the three mechanisms are never documented as interchangeable.
- **Done when:** Documentation states that model choice does not select a skill tree; Claude discovery resolves `.claude/skills`, GPT discovery resolves `.copilot/skills`, workspace instruction files do not contain skill implementations, and the router is explicit rather than implicit in native invocation; all package-integrity tests pass.
- **Depends on:** none

<!-- autofix-applied: 2026-07-31 -->
### Step 43: Add read-only host-install inspection
- **Problem:** The existing installer can act on a target home, but operators lack one deterministic preflight that explains whether the home is clean, generated, legacy, mixed, junction-backed, or missing a provider profile.
- **Type:** code
- **Issue:** #
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `tools/inspect-host-install.ps1`, `tests/distributions/`, `tests/fixtures/legacy-install/`
- **Produces:** Text and JSON reports covering root instruction files, `.claude/skills`, `.copilot/skills`, provenance ownership, link type/target, install ledger, router version/source, legacy `.claude/skills-gpt`, and actionable classifications.
- **Done when:** Fixtures for clean, generated, legacy, mixed-owned, junction, and absent-GPT homes produce stable classifications; the command is read-only under file-hash comparison; output uses consumer-home-relative paths by default, emits absolute paths only behind an explicit diagnostic flag, and never emits secret values; distribution tests pass.
- **Depends on:** 42

### Step 44: Implement reversible legacy-install migration
- **Problem:** The safe installer refuses the live legacy Claude tree, while `-Force` can overwrite it without the backup and rollback guarantees required for a workspace-wide cutover.
- **Type:** code
- **Issue:** #
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `tools/migrate-legacy-install.ps1`, `tools/install-skill-mesh.ps1`, `tests/distributions/`, `tests/fixtures/legacy-install/`
- **Produces:** Dry-run-default migration planning, collision inventory, required external backup directory, byte-preserving backup, source/target manifest and checksums, explicit `-Apply`, transactional Claude+GPT installation, post-install verification, and rollback.
- **Done when:** A synthetic legacy home migrates to generated `.claude/skills` and `.copilot/skills` as one transaction; `-Apply` without `-BackupDir` fails before mutation; the backup manifest records release identity plus every original and installed hash; unknown foreign files block before mutation; injected failure in either provider restores both profiles and the prior ledger; rerun is idempotent; rollback restores original hashes and removes only migration-owned files; installer ownership tests and the full distribution suite pass.
- **Depends on:** 43

### Step 45: Add consumer cutover handoff and release gates
- **Problem:** Even with migration mechanics, the private consumer can drift again unless the package emits an exact instruction-source, installation, retirement, and verification sequence.
- **Type:** code
- **Issue:** #
- **Flags:** --reviewers code --isolation worktree
- **Files:** `documentation/coding-root-cutover-handoff.md`, `documentation/migration.md`, `documentation/provider-neutral-skill-mesh-plan.md`, `README.md`, `tests/package-integrity/`, `tests/release/`
- **Produces:** A copy-pasteable handoff that creates one private shared instruction source with thin `CLAUDE.md` and `AGENTS.md` adapters, updates stale status/topology claims, runs inspector then migrator, validates both profiles, and retires `.claude/skills-gpt` plus the old router only after acceptance.
- **Done when:** Every command names its target repository and expected output; the previous plan's Step 41 is explicitly marked superseded by this plan, and issue #50 is closed as superseded with a link to this plan's new umbrella after `/repo-sync`; no private instruction content or absolute user path is embedded; release tests fail on a missing inspection, backup, rollback, host-acceptance, or separate-coding-root-commit step; package-integrity and release suites pass.
- **Depends on:** 42, 44

### Step 46: Run host-native acceptance against the release candidate
- **Problem:** Hermetic fixtures cannot prove that real Claude Code and GitHub Copilot CLI discover the generated profile and load the intended adapter in a consumer workspace.
- **Type:** operator
- **Issue:** #
- **Produces:** Acceptance observations only; no source-code artifact.
- **Done when:** From a clean temporary consumer home, the operator invokes one representative skill in Claude Code and one in GitHub Copilot CLI, records the discovered `SKILL.md` path and provider adapter for each, confirms GPT works without `OPENAI_API_KEY`, confirms explicit router override separately, exercises rollback, and approves the coding-root handoff; the real `coding-root` remains unchanged until this acceptance passes.
- **Depends on:** 45

### Step 47: Cut over the live coding-root consumer
- **Problem:** Temporary-home acceptance does not prove the generated profiles can replace the actual legacy coding-root installation without breaking its host hooks, instruction loading, or tracked workspace state.
- **Type:** operator
- **Issue:** #
- **Produces:** Live-substrate acceptance observations and retained rollback backup only; no authored source-code artifact.
- **Done when:** After parallel coding-root work is parked and the canonical consumer root is on a clean dedicated branch, the operator runs the inspector, verifies no unrelated dirty paths are in scope, applies the reviewed release candidate with an explicit backup directory outside the repository, opens fresh Claude Code and GitHub Copilot CLI sessions rooted at coding-root, invokes the representative skill in each, records `.claude/skills/<skill>/SKILL.md` for Claude and `.copilot/skills/<skill>/SKILL.md` for GPT, confirms the old v1.2 router and `.claude/skills-gpt` are no longer on an active resolution path, retains the rollback backup, and records PASS. Any failed check triggers rollback and marks the step BLOCKED rather than complete.
- **Depends on:** 46

## 8. Risks and Open Questions

| Item | Risk | Mitigation |
|---|---|---|
| Host instruction behavior | Copilot CLI may load `CLAUDE.md`, `AGENTS.md`, both, or runtime-injected instructions depending on version | Document only observed/official behavior; native skill proof comes from `.copilot/skills` path capture, not inferred instruction loading |
| Dirty consumer repository | Applying cutover in the current coding-root branch could sweep unrelated parallel work | Code steps are skill-mesh-only; final handoff requires a clean dedicated coding-root branch/worktree and scoped adds |
| Legacy foreign files | Existing `.claude/skills` files lack generated provenance | Inspector classifies first; migrator backs up and checksums before explicit apply; unknown files block |
| Junction and symlink behavior | A legacy junction may escape the intended home or change between scan and write | Reuse `Resolve-SafePath`; re-resolve immediately before mutation; test Windows junction cases |
| Rollback completeness | Partial migration could leave generated and legacy files mixed | Transaction log plus byte hashes; failure injection tests; rollback is mandatory acceptance |
| Backup disclosure | Legacy skills and instruction-adjacent files may contain private workspace details | Require a backup directory outside the repository and discovery roots; never upload it; record relative paths and hashes rather than file contents in reports; document retention and secure deletion |
| Instruction duplication | Full `CLAUDE.md` and `AGENTS.md` copies will drift | Consumer handoff mandates one private shared source and thin host adapters |
| Runtime registry masks missing GPT install | A GPT model can invoke skills through host injection even when `.copilot/skills` is absent | Acceptance records the actual discovered `SKILL.md` path and adapter identity |
| Stale migration docs | Existing Step-41 wording can imply cutover happened or is still safe as originally designed | Step 45 replaces it with current inspector/migrator workflow and links the superseding plan |
| Deprecated legacy tree retirement | Removing `.claude/skills-gpt` too early can break current sessions | Retire only in the separate coding-root change after both native acceptance checks and rollback rehearsal |
| Two-profile partial success | Claude replacement may succeed before GPT installation fails | Treat both providers as one migration transaction and restore both profiles plus the prior ledger on any failure |

Runtime-provenance rule: when a host does not expose which instruction file it
loaded, the inspector records `host-convention` or `unknown`; it never claims
`observed`. Native adapter acceptance is proven independently by capturing the
discovered generated `SKILL.md` path.

## 9. Testing Strategy

### Static and package integrity

- Assert documentation gives separate, non-overlapping definitions for
  workspace instructions, skill discovery, and router dispatch.
- Assert all documented commands and local links resolve in the release tree.
- Assert no private absolute paths, instruction content, tokens, or consumer
  memory references enter the package.

### Inspector tests

- Build temporary homes for clean, generated, legacy, mixed-owned, missing-GPT,
  junction-backed, and corrupt-ledger states.
- Snapshot text and JSON classifications.
- Hash the entire fixture before and after inspection to prove read-only
  behavior.
- Plant credential-shaped environment values and verify only presence classes,
  never values, can appear.

### Migration tests

- Dry-run must be a byte-for-byte no-op.
- Apply must back up every replaced/deleted file and write checksums before the
  first target mutation.
- The backup directory is explicit, cannot be inside any discovery tree, and is
  path-canonicalized against symlink/junction escapes.
- Backup reports contain relative paths, size, and hashes only. Backup payloads
  remain local, are excluded from release/telemetry, and have documented
  retention and deletion commands.
- Unknown foreign collisions, path traversal, symlink/junction escape, and
  corrupt manifests must fail before mutation.
- Inject failures at backup, first copy, mid-copy, ledger write, and
  post-install verification; each path must leave either the original home or a
  rollback-complete home.
- Reinstall must be idempotent.
- Rollback must restore original hashes and preserve unrelated files.
- Existing distribution, router, package-integrity, release, telemetry,
  calibration, and smoke suites remain green.

### Host-native acceptance

- Use a clean temporary home rather than the live consumer for first
  acceptance.
- In Claude Code, invoke a representative portable skill and record the
  generated `.claude/skills/<skill>/SKILL.md` plus Claude adapter identity.
- In GitHub Copilot CLI, invoke the same skill and record the generated
  `.copilot/skills/<skill>/SKILL.md` plus GPT adapter identity.
- Keep `OPENAI_API_KEY` unset for the Copilot-native check.
- Run one explicit router override as a separate path so native discovery is
  not conflated with router dispatch.
- Rehearse rollback before approving the private coding-root follow-up.
- Repeat the same path-capture checks against the real coding-root substrate in
  Step 47; temporary-home success alone does not complete the plan.

This feature changes packaging and invocation but adds no scheduled, daemon, or
long-running autonomous behavior, so the long-running observation trigger does
not apply. Real host-native acceptance is still required because discovery
behavior cannot be proven by unit tests alone.

## Appendix: Decision Inventory

| ID | P/D | Choice | Status |
|---|---|---|---|
| P1 | P | `skill-mesh` is the canonical provider-neutral source | active |
| P2 | P | Claude and GPT use their own host-native discovery profiles | active |
| P3 | P | Private coding-root instructions must not be published | active |
| D1 | D | This plan supersedes the unexecuted Step-41 cutover intent with safe prep plus acceptance | active |
| D2 | D | Workspace instructions, skill discovery, and router dispatch are three separate mechanisms | active |
| D3 | D | `AGENTS.md` and `CLAUDE.md` become thin private adapters over one shared consumer instruction source | active |
| D4 | D | Legacy migration uses inspect, backup, explicit apply, verify, and rollback—not blind `-Force` | active |
| D5 | D | Product work and private consumer edits remain separate repository changes | active |
