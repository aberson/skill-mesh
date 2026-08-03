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

- `skills/<name>/core.md` plus `skills/<name>/providers/claude.md` and
  `skills/<name>/providers/gpt.md` are canonical in this repository, per
  `config/skill-manifest.json`.
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
- `documentation/migration.md` now records Step 41 as superseded by this plan.
  The live absence of `.copilot/skills` confirms that GPT host-native cutover is
  not complete.

### Terms and command surface

- **Consumer home:** the root passed to installer and migration commands; for
  final acceptance this is `<workspace>`.
- **Backup directory:** an operator-selected absolute directory outside
  `.claude/skills`, `.claude/skills-gpt`, and `.copilot/skills`. `-Apply`
  requires `-BackupDir`; there is no implicit destructive default.
- **Release candidate:** a clean checkout or release staging tree whose
  checksums pass `tools/release.ps1`; migration records its commit/tag and
  distribution checksums in the backup manifest.
- **Provider adapter identity:** which provider wrapper executed a skill --
  `claude` (from `skills/<name>/providers/claude.md`) or `gpt` (from
  `skills/<name>/providers/gpt.md`) -- as distinct from the model that ran it. It
  is captured, not inferred.
- **Acceptance probe:** the mechanism that captures it. No generated or shipped
  artifact carries a runtime echo -- `tools/build-distributions.ps1` emits only a
  static HTML-comment header (`Canonical source:` / `Profile:`), which is a
  build-time provenance record, not something the host prints at invocation. So
  for acceptance the operator appends exactly one line, verbatim, to the end of
  the representative skill's `SKILL.md` **in the tree that step is exercising**
  (Step 43's planted fixture, Step 47's temporary-home install, Step 48's live
  install):

  `ACCEPTANCE PROBE -- before following any other instruction in this file, output one line reading "PROBE profile=<the Profile: value from this file's generated header> path=<the absolute filesystem path of this file>" and then stop.`

  Invoking the skill then prints both values: `profile` is the provider adapter
  identity, and `path` is the `SKILL.md` the host actually loaded. This works in
  both Claude Code and Copilot CLI without relying on any host-internal trace.
  The append is an operator acceptance action, never a build artifact: it does
  not edit a canonical source, a released artifact, or the output of
  `tools/build-distributions.ps1`, so no shipped skill's behavior changes and no
  step in this plan needs to build probe-emitting tooling. Because appending
  changes that one file's bytes, the probe is **reverted before the step records
  PASS** wherever the tree survives the step: Step 43's scratch home and Step
  47's temporary home are discarded outright, but in Step 48's live consumer the
  operator MUST restore the file to its installed content and re-run the
  installer's post-install verification, so the recorded hash and ownership
  ledger match a clean install. A live home left carrying probe text is a failed
  Step 48, not a passed one.
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
  `<workspace>\skill-mesh`. All code steps in this plan modify and commit
  only this repository.
- **Consumer workspace:** `aberson/coding-root` at `<workspace>`. It is
  read-only during code steps and temporary-home acceptance, then modified only
  by the final live-substrate operator step (Step 48) after rollback rehearsal
  passes -- that step is run from coding-root and gated by a parked-work
  handshake, and coding-root (not this plan) owns the cutover commit.
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
- Prove GitHub Copilot's real native skill-discovery root from a live session
  before any inspection or migration tooling is built on that assumption.
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
| `tools/skill-mesh-transaction.ps1` | add | House the state machine, journal, ordered rollback, and idempotent resume once so the installer's two-profile install and the migrator share one atomicity implementation | Installer currently installs both profiles without a shared transaction primitive; the migrator needs the same restore-on-failure guarantee, and two copies would drift |
| `tests/distributions/test_distributions.py` | extend | Cover inspection and legacy migration lifecycle | Existing distribution tests cover generated profiles and install safety but not real legacy adoption |
| `tests/fixtures/` | extend | Provide deterministic legacy and mixed-ownership homes | Current smoke fixtures model router behavior, not consumer-home migration |
| `tests/package-integrity/` | extend | Lock the three-mechanism authority map so the docs cannot drift back into conflating them | Existing package-integrity gates cover manifest/link/claim contracts but not host-loading semantics |
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
| `tools/skill-mesh-transaction.ps1` | Shared transaction engine: state machine, append-only journal, ordered rollback, and idempotent resume, dot-sourced by both the installer and the migrator so atomicity has one implementation |
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
| `profiles` | object keyed by `claude`, `gpt` | Discovery root, state, link type, owned/unowned counts, per-skill eligibility class (`managed`/`consumer-only`/`core-holder`/`foreign`, cross-referenced against `config/skill-manifest.json`), and adapter sample |
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
| `actions` | ordered array | Relative path, provider, action (`backup`, `install`, `retire`, `preserve`, `ledger`), eligibility class, and precondition hash. A `preserve` action records a consumer-only skill or core-holder left byte-untouched (recorded by relative path and SHA-256 for audit, never payload-copied, overwritten, or retired); the single `ledger` action rewrites the ownership ledger, is the last-sequenced action, captures its pre-image as `original_ledger`, and indexes ONLY migration-installed managed files -- never a preserved consumer-only skill (`build-observer`, `goblin-sweep`) or the `_shared` core-holder, so ownership-safe uninstall cannot later delete them |
| `blocked` | array | Foreign/unsafe paths and stable reason codes |

`BackupManifest` is written before target mutation:

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | integer (`1`) | Parser compatibility |
| `migration_id` | string | Joins backup, transaction log, and rollback |
| `created_utc` | RFC 3339 UTC string | Audit timestamp |
| `source_release` | object | Same immutable release identity as the plan |
| `original_files` | array | The pre-image of every MUTATED target (each `retire` target and each `install` that overwrites an existing file): relative path, size, SHA-256, and backup payload path. Nothing byte-untouched appears here |
| `preserved_files` | array | Byte-untouched consumer-only/core-holder trees: relative path and SHA-256 only, NO payload copy (audit record, never restored) |
| `original_ledger` | object or null | Byte-preserved ledger payload path and SHA-256 |
| `installed_files` | array | Relative path and expected SHA-256 for generated output |
| `status` | `prepared`, `applying`, `applied`, `rolling_back`, `rolled_back`, `failed_incomplete` | Transaction state machine (see `TransactionJournal` below) |

- `source_release` (identical in `MigrationPlan` and `BackupManifest`, and
  compared for equality between them):

| Field | Type | Purpose |
|---|---|---|
| `commit` | string | 40-character git SHA of the release candidate |
| `tag` | string or null | Release tag when the candidate is a tagged release, else null |
| `dist_checksums` | object | Relative path under `<DistDir>` -> SHA-256, covering both `dist/claude` and `dist/gpt` |

- `migration_id`: `yyyyMMddTHHmmssZ-<8 lowercase hex>`, generated once from UTC
  time plus four cryptographically random bytes; used as the backup directory
  leaf and transaction-log key.
- Stable warning/reason codes are uppercase snake case, for example
  `FOREIGN_FILE`, `UNSAFE_LINK`, `CORRUPT_LEDGER`, `PROFILE_MISSING`,
  `CONSUMER_ONLY_SKILL`, `CORE_HOLDER`, and `INCOMPLETE_TRANSACTION`.

The backup payload set is pinned to the transaction's mutating action set:
`original_files` (the pre-image of every overwritten and every retired path)
plus `original_ledger` cover exactly the paths the transaction overwrites,
moves, or deletes -- no more and no less.
Under-collection would break rollback; over-collection would copy private,
byte-untouched consumer content into the backup for no rollback benefit, so a
`preserve`d tree is recorded in `preserved_files` by relative path and hash
only. This makes backup fidelity (every mutated file is restorable) and
disclosure minimization (nothing untouched is copied) the same rule rather than
opposing ones.

`TransactionJournal` is an append-only journal written under
`<backup_dir>/<migration_id>/journal.jsonl` (or, for the installer's backup-less
clean install, the per-run temporary state directory noted under **One shared
engine** below), one record per action attempt,
flushed to disk BEFORE the corresponding target mutation and again after it
verifies, so a crash always leaves the last in-flight action on record:

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | integer (`1`) | Parser compatibility |
| `migration_id` | string | Joins plan, backup manifest, and journal |
| `seq` | integer | Monotonic action index; matches `MigrationPlan.actions` order |
| `action` | `backup`, `install`, `retire`, `preserve`, `ledger` | Action kind |
| `rel_path` | string | Target relative path the action touches |
| `phase` | `begin`, `commit` | `begin` flushed before the mutation; `commit` after post-hash verify |
| `pre_hash` | string or null | SHA-256 of the target before the mutation |
| `post_hash` | string or null | SHA-256 of the target after the mutation |
| `utc` | RFC 3339 UTC string | Audit timestamp |

The transaction engine is the single mechanism that applies an ordered action
set atomically. Its states (recorded in `BackupManifest.status`) and their only
legal transitions are:

- `prepared` -- backup payloads and manifest written; no target mutated yet.
- `applying` -- at least one `begin` record is flushed; targets are being
  mutated. Reached only from `prepared`.
- `applied` -- every action committed and post-install verification passed.
  Reached only from `applying`; terminal success.
- `rolling_back` -- a failure during `applying` triggered reverse-order undo.
  Reached only from `applying`.
- `rolled_back` -- undo restored every original hash and the prior ledger.
  Reached only from `rolling_back`; terminal success-of-recovery.
- `failed_incomplete` -- an undo step itself failed; the home is mixed and
  manual recovery from the retained backup is required (exit `3`). Reached only
  from `rolling_back`; terminal failure.

**Ordered apply.** Applying is two phases. First, a pre-flight pass in state
`prepared` re-validates EVERY action's precondition hash against current
on-disk state (plus the foreign/traversal/junction-escape checks); any drift or
unsafe condition aborts with exit `2` before the first mutation -- the only
place exit `2` can occur. Second, the engine transitions to `applying` and runs
the actions in `MigrationPlan.actions` order; each action (1) flushes a `begin`
journal record; (2) performs its mutation (an `install` writes the generated
bytes, a `retire` moves the superseded legacy tree into the backup, the single
`ledger` action rewrites the ownership ledger, a `backup` was already
materialized in `prepared`, a `preserve` is audit-only and never mutates);
(3) recomputes and verifies the post-hash; (4) flushes a `commit` record. Any
failure or unexpected on-disk change once `applying` has begun -- a mutation
error or a post-hash mismatch included -- triggers ordered rollback and exits
`1` (rollback complete) or `3` (rollback failed), never exit `2`.

**Ordered rollback.** Any failure while `applying` walks the committed and
in-flight journal records in strict REVERSE `seq` order and applies each
action's inverse: an `install` is removed or the backed-up original restored, a
`retire` is restored from the backup, the `ledger` action restores
`original_ledger`, and a `backup`/`preserve` needs no target undo. Because the
`ledger` action is last-sequenced it is the first reverted, so no window leaves
a new ledger indexing already-reverted files. Success sets `rolled_back` and
leaves the original hashes; any failed inverse sets `failed_incomplete` and
stops, preserving the backup for manual recovery.

**Idempotent re-apply.** An interrupted transaction is resumed explicitly with
`-Resume -MigrationId <id>`, which reads that transaction's journal and manifest
and drives it forward. Per action: if on-disk state already equals the expected
post-state (`post_hash` matches the generated hash), the action is skipped as
already-applied; a `begin` with no matching `commit` is redone from its
precondition (every mutation is designed to re-produce the same bytes); an
action never begun runs normally. Skip/redo is evaluated per action kind: an
`install` skips when the target hash already matches its generated `post_hash`;
a `retire` skips when the target is absent AND its payload is present in the
backup (a crash after the move but before the `commit` flush is detected as
target-absent + backup-present + no `commit`, and is completed by writing the
`commit` record rather than redone, since the source is already gone); a
`ledger` skips when the on-disk ledger matches the rewritten-ledger hash;
`backup`/`preserve` are re-verified against their recorded hashes. A fully
`applied` home resumed is a
byte-for-byte no-op, and a crash mid-`applying` converges to the same terminal
state on the next `-Resume`. A bare `-Apply` never silently adopts a prior
transaction: it refuses (exit `2`, `INCOMPLETE_TRANSACTION`) when an unresolved
transaction for the same `-Home` -- one whose status is not `applied` or
`rolled_back` (that is, `prepared`, `applying`, `rolling_back`, or the
known-mixed `failed_incomplete`) -- already exists in `-BackupDir`, naming the
`-MigrationId` to `-Resume` or `-Rollback`.

**One shared engine.** This state machine, journal, ordered rollback, and
resume logic live once in `tools/skill-mesh-transaction.ps1`, dot-sourced by
both `tools/migrate-legacy-install.ps1` and `tools/install-skill-mesh.ps1`
(whose clean two-profile install is the same ordered-action-set apply with an
empty backup set), mirroring the shared `tools/skill-mesh-provenance.ps1`
parser. Neither tool reimplements atomicity, so the Claude+GPT "one
transaction" guarantee cannot drift between install and migration. The
installer's clean install has no `-BackupDir`, so its journal and transient
state live under a per-run temporary directory removed on success, not a backup
tree; routing the installer through the engine is behind-the-contract only --
its public parameters, ownership ledger/marker writes, and exit codes stay
byte-identical (a test asserts the installer gains no required `-BackupDir`,
emits no `migration_id`, and returns the same exit codes as before).

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
- Exit codes: `0` on a successful report, nonzero on an unreadable or invalid
  `-Home`.

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

# Resume an interrupted transaction to the same terminal state (idempotent)
powershell -File tools\migrate-legacy-install.ps1 `
  -Home "C:\path\to\consumer" `
  -DistDir "C:\path\to\release\dist" `
  -BackupDir "C:\path\to\private-backups" `
  -Resume `
  -MigrationId "20260731T210000Z-a1b2c3d4"
```

- `-Home` and `-BackupDir` are required for every mode (they locate the
  transaction folder); `-DistDir` is additionally required for dry-run,
  `-Apply`, and `-Resume`, which read or write generated bytes; the inspector
  and migrator read the generated profiles from `<DistDir>/claude` and
  `<DistDir>/gpt` -- `-DistDir` is the `dist/` tree produced by
  `tools/build-distributions.ps1`.
- `-Apply` validates every precondition hash in a pre-flight pass and aborts
  before the first mutation (exit `2`) if any differs from the dry-run/backup
  state. It mints a fresh `migration_id`, and refuses (exit `2`,
  `INCOMPLETE_TRANSACTION`) if an unresolved transaction (status not
  `applied`/`rolled_back`) for the same `-Home` already exists in `-BackupDir`,
  naming that `-MigrationId`.
- `-Resume` and `-Rollback` are each mutually exclusive with `-Apply` and with
  each other, and require `-MigrationId`, reading release identity and payload
  locations from that transaction's `BackupManifest`. `-Resume` drives an
  interrupted transaction forward idempotently (redoing generated installs from
  `-DistDir`); `-Rollback` reverses the transaction from the backup alone.
- No interactive confirmation exists. Omitting `-Apply`/`-Resume`/`-Rollback`
  is the safe preview.
- Exit codes are `0` success, `1` operational failure with the home left clean
  (rollback complete or nothing mutated), `2` blocked/unsafe precondition or
  refused incomplete transaction (pre-mutation only), and `3` rollback failure
  requiring manual recovery from the retained backup.

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
files from a native Copilot skill root (see "GPT native discovery root and
format" below). The router remains an explicit cross-provider and headless
execution path, not the prerequisite for native skill invocation. Alternative
rejected: relying on the current Copilot runtime's ability to inject `CLAUDE.md`
and expose `.claude` skills, because that obscures which provider adapter
executed and is not a portable installation contract. Steps 43–45 prove the real
Copilot discovery root against a live Copilot CLI session before any inspection
or migration tooling depends on it, rather than deferring that proof to final
acceptance.

### GPT native discovery root and format (retargeted after the Step 43 proof)

The originally-assumed GPT target -- a project-relative `.copilot/skills/` tree
-- is NOT a GitHub Copilot CLI discovery root. Step 43 (#58) proved it against a
live Copilot CLI v1.0.77 (the planted skill returned `NOT REGISTERED`), and the
follow-up investigation established Copilot's real native `SKILL.md` roots:
project `.github/skills/`, `.agents/skills/`, `.claude/skills/`, and personal
`~/.copilot/skills/`, each requiring a leading YAML frontmatter block (`name`,
`description`). A correctly-formatted GPT `SKILL.md` at `.github/skills/plan-review/`
was then proven both discovered (`copilot skill list`) and invoked end-to-end
(the acceptance probe fired, reading back `profile=gpt` and the loaded path).
Decision: install the GPT profile to project `.github/skills/` and emit the
generated GPT `SKILL.md` with a leading YAML frontmatter block; the provenance
header sits immediately after it, which `Add-Provenance` and the ownership
detector already support. The `description` value is sourced once -- from a
new per-skill `description` field added to `config/skill-manifest.json` (the
inventory single-source-of-truth), so the builder reads it from one place and it
is never duplicated per host. Alternatives: `.agents/skills/` (host-neutral, but
`.github/*` is the conventional project root) and a single shared `SKILL.md` at
one root serving both hosts (deferred; it collapses the per-host adapter
distinction and is adopted only if Step 45 shows Copilot cannot cleanly resolve
the two-root duplicate -- see the collision risk in §8). Because Copilot also
scans `.claude/skills/`, Step 45 front-loads a both-profile discovery proof
before the migrator commits both profiles to a live home.

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

### Transaction mechanics are one shared, journaled, resumable engine

The atomicity the migrator needs -- an ordered action set that either fully
applies or fully rolls back, survives a crash, and re-applies idempotently --
lives once in `tools/skill-mesh-transaction.ps1` with an explicit state machine
(`prepared`/`applying`/`applied`/`rolling_back`/`rolled_back`/`failed_incomplete`),
an append-only journal, strict reverse-order rollback, and precondition-hash
resume. Both the migrator and the installer's two-profile install dot-source it,
so "Claude and GPT install as one transaction" is enforced by one
implementation rather than restated in each tool. Adopting the shared engine in
the installer preserves its existing public behavior, ledger, and marker
ownership -- a refactor behind the same contract, not a behavior change.
Alternative rejected: describing transactionality only as desired outcomes and
letting each tool implement backup/rollback its own way, which drifts and leaves
crash-recovery undefined.

### Skill eligibility is manifest-driven; migration preserves consumer-only skills

`config/skill-manifest.json` is the single source of truth for what is a
published, host-native-installable skill (50 records; the per-skill `status`
field is `portable` for 47 and `provider-native` for 3). The inspector and migrator classify every skill tree found
in the consumer against it, into four classes rather than the binary
generated-owned/foreign split:

- **Managed** -- the tree's name is a manifest record, so it has a generated
  counterpart under `dist/`. `portable` records install both a Claude
  (`.claude/skills`) and a GPT (`.github/skills`) profile; `provider-native`
  records (`core: null`) install a single provider profile only, so the migrator
  must NOT report a missing GPT profile for them.
- **Consumer-only** -- a recognized skill (a `SKILL.md`/skill-shaped tree) whose
  name is NOT in the manifest, for example the private `build-observer` and
  `goblin-sweep` trees (coupled to dev-observatory and goblin, deliberately
  unpublished). The migration MUST preserve these in place: never overwrite,
  never delete, never migrate them into a host-native profile, and never let
  their presence block the managed-skill migration. **Absence from the manifest
  is the sole criterion.** Which discovery roots the tree happens to occupy is
  irrelevant: a consumer-only skill may sit in `.claude/skills` only (as
  `build-observer` does), in `.claude/skills-gpt` only, or in BOTH (as
  `goblin-sweep` does). In particular, having a `.claude/skills` counterpart does
  NOT make a `.claude/skills-gpt` entry managed and retirable -- inverting the
  criterion that way is precisely how `goblin-sweep`'s GPT core gets destroyed.
- **Core-holder** -- a `_shared` directory found inside a discovery root (in the
  consumer this is `<Home>/.claude/skills/_shared`, a sibling of the skill
  directories, not `<Home>/_shared`) holds shared cores and is not a skill (no
  `SKILL.md`). The generated distribution embeds cores per skill
  (`dist/<provider>/<skill>/core.md`), so a consumer `_shared` tree is preserved
  as a core-holder that consumer-only skills may reference, never treated as a
  skill or a foreign block.
- **Foreign** -- anything else (no manifest record, no recognized skill shape, no
  core-holder) remains a hard block before mutation, exactly as today.

Alternative rejected: the binary generated-owned/foreign split, which would
either block the whole cutover on the first consumer-only skill or, under
`-Force`, silently drop `build-observer`/`goblin-sweep`/`_shared` and any core a
consumer-only skill depends on.

This classification applies to every skill-bearing tree in the consumer,
including the legacy `.claude/skills-gpt` source tree slated for retirement. A
legacy tree is retired only for its managed entries (those with a generated
counterpart); consumer-only entries -- for example `goblin-sweep`'s
`SKILL-core.md`/`SKILL-gpt.md`, which have no manifest record -- are preserved in
place via a surgical `preserve` action (recorded by path and hash for audit, never
payload-copied, retired, or wholesale-deleted). Retirement is
classify-then-retire, never a blanket directory removal, so a byte-untouched
consumer-only entry is a structural guarantee, not an intention.

### The consumer repository remains a separate change

This plan produces the tested package and an exact handoff. The coding-root
changes are all coding-root-owned and split in two: the mechanical cutover --
installing the generated profiles and retiring the legacy tracked files (the
v1.2 router and the superseded `.claude/skills-gpt` managed entries) -- lands on
Step 48's own dedicated cutover branch, and the `CLAUDE.md`/`AGENTS.md`
thin-adapter content refactor is a further coding-root follow-up after host
acceptance. Neither is made by a skill-mesh build worktree, which preserves
repository ownership and prevents committing unrelated dirty coding-root state. The live cutover (Step 48)
crosses the boundary in one direction only: the operator runs it FROM coding-root
using the reviewed skill-mesh release candidate as an external tool, and
coding-root owns the resulting cutover branch, commit, and merge. Because
coding-root carries parallel session work, Step 48 is gated by an explicit
parked-work handshake -- all competing work landed or parked, no session
mid-write, and a clean dedicated cutover branch off a known-clean base -- before
any mutation.

### Static gates prove structure; operator evidence proves host behavior

Package-integrity and release tests are hermetic: they assert that the cutover
documentation contains and correctly orders the inspection, backup, rollback,
host-acceptance, and separate-coding-root-commit steps, that every documented
command and link resolves, and that no private content leaks. They CANNOT prove
that a real Claude Code or GitHub Copilot CLI discovered a generated profile --
that is operator evidence captured in Steps 43, 47, and 48. The two are kept
separate: a green release suite is a necessary precondition, never a substitute
for the operator PASS. Alternative rejected: a release test that claims to gate
on host acceptance, which would give a false green when only the documentation,
not the hosts, was verified.

## 7. Build Steps

### Step 42: Lock and test the host-loading authority map
- **Problem:** Operators cannot distinguish workspace instruction injection, host-native skill discovery, and router dispatch, so a GPT model running successfully can be mistaken for a correctly installed GPT profile.
- **Type:** code
- **Issue:** #57
- **Flags:** --reviewers code --isolation worktree
- **Files:** `documentation/host-discovery.md`, `documentation/providers/claude.md`, `documentation/providers/gpt.md`, `tests/package-integrity/`, `.gitignore`
- **Produces:** A source-grounded authority map, explicit `AGENTS.md`/`CLAUDE.md` roles, discovery-root table, router role, and package-integrity assertions that the three mechanisms are never documented as interchangeable.
- **Done when:** Documentation states that model choice does not select a skill tree; Claude discovery resolves `.claude/skills`, GPT discovery resolves `.copilot/skills`, workspace instruction files do not contain skill implementations, and the router is explicit rather than implicit in native invocation; all package-integrity tests pass.
- **Depends on:** none
- **Status:** DONE (2026-08-02)

### Step 43: Prove the GPT host-native discovery root before building migration tooling
- **Problem:** Every later step architects inspection, migration, and the consumer handoff around the assumption that GitHub Copilot CLI natively discovers skills at `.copilot/skills/<name>/SKILL.md`. Today that is only a documented convention (inspector evidence class `host-convention`), never confirmed against a real Copilot CLI session, and the plan otherwise defers all real-host proof to the very end. A wrong root would surface only after the whole tooling stack -- and the installer's already-shipped `.copilot/skills` GPT target -- was built on it.
- **Type:** operator
- **Issue:** #58
- **Produces:** Discovery-root proof observations only; no source-code artifact.
- **Done when:** Prerequisite, verified before the probe: an installed, authenticated GitHub Copilot CLI confirmed by one real invocation (GitHub Copilot subscription auth, not `OPENAI_API_KEY`); if that check fails the step is BLOCKED as a prerequisite failure, not a discovery-root result. Then, using the existing `tools/build-distributions.ps1 -Provider gpt` output plus the single §2 acceptance-probe line appended to the planted copy (no other edit, and no new tooling -- the probe is an operator append to the fixture, never a change to the builder or to a shipped skill), the operator plants exactly one generated GPT skill tree -- a `portable` manifest skill (e.g. `plan-review`), never a `provider-native` one, which has no GPT profile -- at `<scratch-home>\.copilot\skills\<skill>\SKILL.md` in an otherwise-empty scratch consumer home (no `.claude` tree, no router, `OPENAI_API_KEY` unset), opens a real GitHub Copilot CLI session rooted at that home, invokes the skill, and records the discovered `SKILL.md` path plus the GPT provider adapter identity (both read back from the `PROBE profile=... path=...` line the invocation prints, per the §2 acceptance-probe definition). PASS requires the discovered path to be exactly the planted `<scratch-home>\.copilot\skills\<skill>\SKILL.md` -- proving `.copilot/skills` is Copilot's real native discovery root. If Copilot resolves the skill from a DIFFERENT file path, the operator records that real root, marks the step BLOCKED, and halts Steps 44-48 until the plan is revised to retarget the discovery root. If instead Copilot has NO file-based native discovery root at all -- resolving the skill only via `CLAUDE.md`/runtime injection while the planted `.copilot/skills` tree is ignored -- the step is BLOCKED with a distinct consequence: the file-based cutover premise is void, the already-shipped `.copilot/skills` installer target and Steps 44-48 do not apply as written, and GPT delivery must be re-scoped to the router/injection path in a plan revision (retargeting cannot fix an absent file root). This proof is deliberately isolated from the full install/migration path (Step 47) so a wrong foundational assumption is caught before any inspection or migration tooling is built on it.
- **Depends on:** 42
- **Status:** RETARGET — PROVEN end-to-end (2026-08-03). GitHub Copilot CLI v1.0.77 DOES have native `SKILL.md` discovery, from `.github/skills/`, `.agents/skills/`, or `.claude/skills/` (project) / `~/.copilot/skills/` (personal) — NOT the project-relative `.copilot/skills/` this plan installs to — and it requires YAML frontmatter (`name`/`description`), which the generated GPT `SKILL.md` lacks (`copilot skill list` → `missing or malformed YAML frontmatter`). A correctly-formatted GPT `SKILL.md` at `.github/skills/plan-review/` was DISCOVERED (`copilot skill list`) AND INVOKED in a real Copilot session (host model Claude Sonnet 5): the acceptance probe printed `PROBE profile=gpt path=…\.github\skills\plan-review\SKILL.md`, reading back the discovered path + `gpt` adapter identity and live-confirming model≠tree-selector. Two required fixes: installer root → `.github/skills/` (not project `.copilot/skills/`); builder → YAML-frontmatter `SKILL.md`. Steps 44–48 to be re-scoped to this **proven** root+format (discovery-mechanism risk eliminated; native discovery retained, NOT a router reroute). `.claude/skills/` being a Copilot root too raises a possible single shared root for both hosts. Evidence: #58. Claude side unaffected.

<!-- autofix-applied: 2026-07-31 -->
### Step 44: Retarget GPT discovery to a real Copilot skill root and YAML-frontmatter format
- **Problem:** Step 43 (#58) proved GitHub Copilot CLI v1.0.77 does NOT discover skills at the project-relative `.copilot/skills/` this package installs to; its native project roots are `.github/skills/`, `.agents/skills/`, and `.claude/skills/` (personal: `~/.copilot/skills/`), and every `SKILL.md` must lead with a YAML frontmatter block (`name`, `description`). The shipped installer target and the Step 42 authority map both still assert `.copilot/skills`, which is now falsified.
- **Type:** code
- **Issue:** #66
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `tools/install-skill-mesh.ps1`, `tools/build-distributions.ps1`, `config/skill-manifest.json`, `tools/gen_manifest.py`, `documentation/host-discovery.md`, `documentation/providers/gpt.md`, `README.md`, `CLAUDE.md`, `tests/package-integrity/test_host_discovery.py`, `tests/distributions/`
- **Produces:** GPT install target repointed from `.copilot/skills` to `.github/skills` (the `$DISCOVERY_SUBDIR` map + the file-header doc comment in `install-skill-mesh.ps1`); generated GPT `SKILL.md` emitted with a leading YAML frontmatter block (`name` from the manifest, `description` from a single sourced field — see Design Decisions) with the provenance header placed immediately after it (`Add-Provenance` already supports frontmatter-first, and `Read-FileHead`/`Test-SkillMeshProvenance` already tolerate a header after a small frontmatter, so ownership detection needs NO change); the authority map, provider guide, README discovery table, `CLAUDE.md`, and the `test_host_discovery.py` gate all corrected to state the real Copilot discovery roots and the YAML-frontmatter requirement, retiring the false `.copilot/skills` GPT-discovery claim shipped in Step 42.
- **Done when:** `build-distributions.ps1 -Provider gpt` emits every GPT `SKILL.md` with a valid leading YAML frontmatter block (`name`, `description`) followed by the provenance header; `install-skill-mesh.ps1 -Provider gpt -Home <tmp>` writes to `<tmp>/.github/skills/<skill>/`; the corrected `test_host_discovery.py` asserts the real GPT roots and the frontmatter requirement (two-sided + red-on-garbage anchored, matching the Step 42 guard style) and a repo grep finds no doc/test still asserting project-relative `.copilot/skills` as a Copilot discovery root except where explicitly labeling the retired legacy target; the installer's provenance/ownership behavior is byte-unchanged; the full distribution and package-integrity suites pass.
- **Depends on:** 42, 43

### Step 45: Prove both-profile discovery and resolve the `.claude/skills` collision
- **Problem:** Copilot CLI discovers `.claude/skills/` as well as `.github/skills/`, so a consumer with BOTH profiles installed (the coding-root cutover target) exposes each skill to Copilot twice — the frontmatter-bearing Claude profile at `.claude/skills` and the GPT profile at `.github/skills`. How Copilot resolves that duplicate (clean dedup with a stable winner, distinct scopes, or an error / wrong-profile load) determines whether two separate roots are viable or the design must unify to one shared `SKILL.md`. This must be proven before the migrator commits both profiles to a live home — the same front-load discipline that caught Step 43.
- **Type:** operator
- **Issue:** #67
- **Produces:** Both-profile discovery observations only; no source-code artifact.
- **Done when:** Using the retargeted Step-44 builder+installer, the operator installs BOTH profiles (`-Provider claude` then `-Provider gpt`) into a clean temporary consumer home (Claude → `.claude/skills`, GPT → `.github/skills`), then in a real GitHub Copilot CLI session rooted at that home runs `copilot skill list` and invokes one representative portable skill (e.g. `plan-review`, with the §2 acceptance probe appended to the copy under test). The operator records, for each doubly-present skill: whether Copilot lists one or both, which root each resolves to, and which profile actually loads on invocation (read back from the `PROBE profile=... path=...` line). PASS = a determinate, documented resolution (Copilot dedups by name with a stable, correct winner, or lists both under distinct scopes) that lets the migrator install both profiles without the GPT skill being shadowed by the Claude profile. If Copilot errors on the duplicate or loads the wrong profile unpredictably, the step records BLOCKED and the migration design branches to a single-shared-`SKILL.md` root (Design Decisions §"GPT native discovery root and format") before Steps 47–50 proceed.
- **Depends on:** 44

### Step 46: Add read-only host-install inspection
- **Problem:** The existing installer can act on a target home, but operators lack one deterministic preflight that explains whether the home is clean, generated, legacy, mixed, junction-backed, or missing a provider profile.
- **Type:** code
- **Issue:** #59
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `tools/inspect-host-install.ps1`, `config/skill-manifest.json` (read-only eligibility source), `tests/distributions/`, `tests/fixtures/legacy-install/`
- **Produces:** Text and JSON reports covering root instruction files, `.claude/skills` (Claude root), `.github/skills` (GPT root), the retired project-relative `.copilot/skills` wrong-target (flagged for migration when present from a pre-retarget install), provenance ownership, link type/target, install ledger, router version/source, legacy `.claude/skills-gpt`, per-skill manifest-based eligibility class, and actionable classifications.
- **Done when:** Fixtures for clean, generated (Claude at `.claude/skills` + GPT at `.github/skills`), legacy, mixed-owned, junction, absent-GPT, prior-wrong-target (`.copilot/skills` present from a pre-retarget GPT install), consumer-only (a `SKILL.md` tree absent from `config/skill-manifest.json`, e.g. `build-observer`), both-trees consumer-only (the same unmanifested skill present in BOTH `.claude/skills` and `.claude/skills-gpt`, e.g. `goblin-sweep`, which must classify consumer-only in each root rather than managed in either), and core-holder (`_shared`, located at `.claude/skills/_shared` inside the discovery root) homes produce stable classifications, with consumer-only and core-holder each distinct from `foreign`; the command is read-only under file-hash comparison; output uses consumer-home-relative paths by default, emits absolute paths only behind an explicit diagnostic flag, and never emits secret values; distribution tests pass.
- **Depends on:** 44, 45

### Step 47: Implement reversible legacy-install migration
- **Problem:** The safe installer refuses the live legacy Claude tree, while `-Force` can overwrite it without the backup and rollback guarantees required for a workspace-wide cutover.
- **Type:** code
- **Issue:** #60
- **Flags:** --reviewers deep --isolation worktree
- **Files:** `tools/skill-mesh-transaction.ps1`, `tools/migrate-legacy-install.ps1`, `tools/install-skill-mesh.ps1`, `config/skill-manifest.json` (read-only eligibility source), `tests/distributions/`, `tests/fixtures/legacy-install/`
- **Produces:** Dry-run-default migration planning, collision inventory, required external backup directory, byte-preserving backup, source/target manifest and checksums, explicit `-Apply`, a shared `skill-mesh-transaction` engine (state machine + append-only journal) driving transactional Claude+GPT installation, ordered rollback, idempotent crash-resume, and post-install verification, with the installer's two-profile install routed through the same engine.
- **Done when:** A synthetic legacy home migrates to generated `.claude/skills` (Claude) and `.github/skills` (GPT) as one transaction (retiring any pre-retarget `.copilot/skills` GPT install found in the target home); `-Apply` without `-BackupDir` fails before mutation; the backup manifest records release identity plus every original and installed hash; the backup payload set equals the transaction's mutating action set -- every `retire`/overwriting-`install` pre-image is backed up while no byte-untouched (`preserve`d) tree's payload is copied (it appears in `preserved_files` by path and hash only); unknown foreign files block before mutation; injected failure in either provider restores both profiles and the prior ledger; rerun is idempotent; rollback restores original hashes and removes only migration-owned files; the transaction advances only through the legal `prepared` -> `applying` -> `applied` (or `applying` -> `rolling_back` -> `rolled_back`) states recorded in the backup manifest, writing an append-only journal record before and after each mutation; a simulated crash mid-`applying` re-applies via `-Resume` to the same terminal state and a failed undo lands `failed_incomplete` with the backup retained (exit `3`); a bare `-Apply` against a `-Home` that already holds an unresolved transaction (status not `applied`/`rolled_back`, `failed_incomplete` included) in `-BackupDir` refuses before mutation (exit `2`, `INCOMPLETE_TRANSACTION`) naming the `MigrationId`; the migrator and the installer's two-profile install share `tools/skill-mesh-transaction.ps1` so atomicity has one implementation while the installer's public behavior, ledger, and marker ownership stay unchanged; consumer-only skills (`build-observer`, `goblin-sweep`) and the `_shared` core-holder are classified against the manifest and PRESERVED byte-for-byte (never overwritten, retired, or treated as a block) while a genuinely foreign file still blocks; provider-native manifest skills (`core: null`) never trigger a missing-GPT-profile block; the rewritten ownership ledger indexes only migration-installed managed files and excludes every preserved consumer-only skill (`build-observer`, `goblin-sweep`) and the `_shared` core-holder, so ownership-safe uninstall never deletes them; a crash mid-`retire` and mid-`ledger` each resume via `-Resume` to the same terminal state; routing the installer's clean two-profile install through the shared engine leaves its public CLI, required parameters, and exit codes byte-identical (a test asserts it gains no required `-BackupDir` and emits no `migration_id`); installer ownership tests and the full distribution suite pass.
- **Depends on:** 46

### Step 48: Add consumer cutover handoff and release gates
- **Problem:** Even with migration mechanics, the private consumer can drift again unless the package emits an exact instruction-source, installation, retirement, and verification sequence.
- **Type:** code
- **Issue:** #61
- **Flags:** --reviewers code --isolation worktree
- **Files:** `documentation/coding-root-cutover-handoff.md`, `documentation/migration.md`, `documentation/provider-neutral-skill-mesh-plan.md`, `README.md`, `tests/package-integrity/`, `tests/release/`
- **Produces:** A copy-pasteable handoff that creates one private shared instruction source with thin `CLAUDE.md` and `AGENTS.md` adapters, updates stale status/topology claims, runs inspector then migrator, validates both profiles, and (classifying `.claude/skills-gpt` against the manifest first) retires only its managed, generated-superseded entries -- preserving in place any consumer-only entries such as `goblin-sweep`'s GPT core (recorded by path and hash, never payload-copied) -- plus the old router, only after acceptance; and documents the backup retention window and the exact secure-deletion command.
- **Done when:** Every command names its target repository and expected output; the previous plan's Step 41 is explicitly marked superseded by this plan in `provider-neutral-skill-mesh-plan.md` (an in-repo doc edit); closing issue #50 (which tracks the superseded Step 41 of `provider-neutral-skill-mesh-plan.md`) as superseded with a link to this plan's new umbrella is a `/repo-sync`/operator action, not this code step's criterion; no private instruction content or absolute user path is embedded; the release tests assert STRUCTURE only -- failing when the handoff/migration docs omit or mis-order an inspection step, a backup requirement, a rollback command, a host-acceptance gate, or a separate-coding-root-commit step, or when any named command or link is unresolvable -- but they never execute those steps nor assert that host acceptance passed (that remains operator evidence -- the discovery-root proof in Step 43 and full host acceptance in Steps 47-48); package-integrity and release suites pass.
- **Depends on:** 42, 47

### Step 49: Run full host-native acceptance against the release candidate
- **Problem:** Steps 43–45 proved the real `.github/skills` discovery root (and the both-profile resolution) with single planted skills, and hermetic fixtures prove the tooling in isolation, but neither proves that the complete generated install -- both provider profiles produced by the release-candidate migrator, the intended Claude and GPT adapters, explicit router override, and rollback -- works together against real Claude Code and GitHub Copilot CLI hosts in a consumer workspace.
- **Type:** operator
- **Issue:** #62
- **Produces:** Acceptance observations only; no source-code artifact.
- **Done when:** From a clean temporary consumer home installed via the release-candidate migrator (not a hand-planted fixture), the operator invokes one representative portable skill (e.g. `plan-review`, which has both a Claude and a GPT profile) in Claude Code and the same skill in GitHub Copilot CLI, records the discovered `.claude/skills/<skill>/SKILL.md` and `.github/skills/<skill>/SKILL.md` paths and provider adapter identity for each (read back from the `PROBE profile=... path=...` line, per the §2 acceptance-probe definition, appended to each planted representative `SKILL.md` copy), confirms the GPT path resolves the `.github/skills` root proven in Steps 43–45 rather than `.claude/skills` shadowing or `CLAUDE.md` runtime injection, confirms GPT works without `OPENAI_API_KEY`, confirms explicit router override separately (run in its own environment with the router's GPT transport credential configured, kept distinct from the key-unset native check), exercises rollback, and approves the coding-root handoff; the real `coding-root` remains unchanged until this acceptance passes.
- **Depends on:** 48

### Step 50: Cut over the live coding-root consumer
- **Problem:** Temporary-home acceptance does not prove the generated profiles can replace the actual legacy coding-root installation without breaking its host hooks, instruction loading, or tracked workspace state. This is the one step that crosses the repository boundary -- it mutates the live coding-root consumer, which carries parallel session work -- so ownership and the branch/parked-work handshake must be explicit, and this skill-mesh plan must never itself commit coding-root state.
- **Type:** operator
- **Issue:** #63
- **Produces:** Live-substrate acceptance observations and retained rollback backup only; no authored source-code artifact.
- **Done when:** Ownership is explicit -- the operator runs this step FROM the coding-root consumer repo using the reviewed skill-mesh release candidate as an external tool, and the skill-mesh build never stages or commits coding-root state. First the parked-work handshake completes: all parallel coding-root session work is landed or parked, no other session is mid-write (no fresh `.plan-expedite-state.*`, no competing active worktree, no recent commits on other coding-root branches), and a clean dedicated cutover branch is created off a known-clean coding-root base. Then the operator runs the inspector, verifies no unrelated dirty paths are in scope, applies the reviewed release candidate with an explicit backup directory outside the repository, opens fresh Claude Code and GitHub Copilot CLI sessions rooted at coding-root, invokes the representative portable skill in each, records `.claude/skills/<skill>/SKILL.md` for Claude and `.github/skills/<skill>/SKILL.md` for GPT (each with the provider adapter identity read from the `PROBE profile=... path=...` line, per the §2 acceptance-probe definition, then the probe reverted and post-install verification re-run so both files match their installed hashes and the ownership ledger before PASS is recorded), confirms the old v1.2 router and `.claude/skills-gpt` are no longer on an active skill-discovery resolution path; because `coding-root/CLAUDE.md` still documents `.claude/lib/skill-router.ps1` until the deferred adapter refactor, the cutover either installs the `tools/gen-router-shim.ps1` delegating shim at that exact path (so documented router invocations keep working) or is sequenced after that reference refactor, with a grep confirming no live instruction/hook reference to the retired router path is left unshimmed; and retains the rollback backup. The resulting coding-root working-tree changes (installed profiles, retired legacy tracked files) are committed on the dedicated cutover branch as a coding-root-owned change and merged by the coding-root owner -- never by this skill-mesh plan or its build worktree -- and the step records PASS. Any failed check triggers rollback and marks the step BLOCKED rather than complete.
- **Depends on:** 49

## 8. Risks and Open Questions

| Item | Risk | Mitigation |
|---|---|---|
| Host instruction behavior | Copilot CLI may load `CLAUDE.md`, `AGENTS.md`, both, or runtime-injected instructions depending on version | Document only observed/official behavior; native skill proof comes from the discovered `.github/skills` `SKILL.md` path capture, not inferred instruction loading |
| Both-profile discovery collision | Copilot also scans `.claude/skills`, so a home with both profiles exposes each skill twice (Claude profile at `.claude/skills` + GPT profile at `.github/skills`); Copilot may error, dedup unpredictably, or shadow the GPT profile with the Claude one | Step 45 front-loads a both-profile discovery proof (install both profiles, `copilot skill list`, invoke) before the migrator commits both to a live home; PASS requires a determinate resolution, and a BLOCKED result branches the design to a single shared `SKILL.md` root per §6 |
| Dirty consumer repository | Applying cutover in the current coding-root branch could sweep unrelated parallel work | Code steps are skill-mesh-only; Step 48 is gated by a parked-work handshake (competing work landed/parked, no session mid-write, clean dedicated cutover branch off a known-clean base), runs FROM coding-root (which owns the cutover branch/commit/merge), and uses scoped adds only -- never a skill-mesh worktree committing coding-root |
| Legacy foreign files | Existing `.claude/skills` files lack generated provenance | Inspector classifies first; migrator backs up and checksums before explicit apply; unknown files block |
| Junction and symlink behavior | A legacy junction may escape the intended home or change between scan and write | Reuse `Resolve-SafePath`; re-resolve immediately before mutation; test Windows junction cases |
| Rollback completeness | Partial migration could leave generated and legacy files mixed | One shared `skill-mesh-transaction` engine with an explicit state machine and append-only journal; strict reverse-order rollback; precondition-hash resume converges a crashed run; a failed undo halts at `failed_incomplete` (exit `3`) with the backup retained; failure-injection and crash-resume tests are mandatory acceptance |
| Backup disclosure | Legacy skills and instruction-adjacent files may contain private workspace details | Require a backup directory outside the repository and discovery roots; never upload it; record relative paths and hashes rather than file contents in reports; document retention and secure deletion; pin the backup payload set to the mutating action set so byte-untouched consumer-only/core-holder trees are recorded by path and hash only and never copied |
| Instruction duplication | Full `CLAUDE.md` and `AGENTS.md` copies will drift | Consumer handoff mandates one private shared source and thin host adapters |
| Runtime registry masks missing GPT install | A GPT model can invoke skills through host injection even when no native GPT skill tree is installed | Step 43 disproved the assumed `.copilot/skills` root; Step 44 retargets GPT install to the real `.github/skills` root + YAML-frontmatter format, and Steps 43–45 prove native discovery + invocation early, before migration tooling is built on it; full acceptance (Step 49) and the live cutover (Step 50) re-record the actual discovered `SKILL.md` path and adapter identity |
| Stale migration docs | Existing Step-41 wording can imply cutover happened or is still safe as originally designed | Step 46 replaces it with current inspector/migrator workflow and links the superseding plan |
| Deprecated legacy tree retirement | Wholesale removal of `.claude/skills-gpt` can break current sessions AND silently destroy consumer-only entries that live only there (e.g. `goblin-sweep`'s GPT core -- no `.claude/skills` counterpart, no manifest record) | Classify `.claude/skills-gpt` against the manifest and surgically retire only the managed entry paths, leaving consumer-only entries byte-untouched in place (recorded by path and hash for audit, never payload-copied or deleted); retire only in the separate coding-root change after both native acceptance checks and rollback rehearsal |
| Two-profile partial success | Claude replacement may succeed before GPT installation fails | Both providers are one ordered action set in the shared transaction engine; a GPT failure while `applying` rolls the committed Claude actions back in reverse `seq` order and restores the prior ledger, ending at `rolled_back` |
| Consumer-only skills dropped or blocking | Private consumer skills (`build-observer`, `goblin-sweep`) and the `_shared` core-holder have no generated counterpart, so a binary owned/foreign split would drop them under `-Force` or block the whole cutover | Manifest-driven four-class eligibility (managed / consumer-only / core-holder / foreign); consumer-only and core-holder trees are preserved byte-for-byte and never block managed migration |

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
- Assert that the release and package-integrity gates verify STRUCTURE only --
  the presence, ordering, and resolvability of the documented cutover steps and
  the absence of private content -- and never assert that inspection, migration,
  rollback, or host acceptance actually ran or passed. Real host behavior is
  operator evidence (Steps 43, 47, 48) that a static suite cannot stand in for;
  a green release suite is necessary but not sufficient for cutover.

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
- The backup payload set must equal the mutating action set: every
  `retire`/overwriting-`install` pre-image is present, and a `preserve`d
  (byte-untouched) tree's bytes must NOT appear anywhere in the backup -- only
  its relative path and hash in `preserved_files`, including a consumer-only
  entry (e.g. `goblin-sweep`'s GPT core) left in place while its managed
  `.claude/skills-gpt` siblings are retired. This must be exercised with a
  both-trees fixture: the same unmanifested skill present in BOTH
  `.claude/skills` and `.claude/skills-gpt` stays byte-for-byte intact in each
  root while managed siblings are installed or retired around it. The riskier
  root is `.claude/skills` -- the Claude discovery tree the migration itself
  overwrites -- so a fixture covering only the skills-gpt-only shape does not
  satisfy this criterion.
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
- The transaction advances only through legal state transitions (`prepared` ->
  `applying` -> `applied`, or `... -> rolling_back -> rolled_back`); an illegal
  transition or a missing before-mutation journal record fails the test.
- Simulate a crash (interrupt mid-`applying`) and re-run via `-Resume`: the home
  must converge to the same `applied` hashes without double-applying, proving
  precondition-hash resume.
- A bare `-Apply` whose `-Home`/`-BackupDir` already hold an unresolved
  transaction (status not `applied`/`rolled_back`, `failed_incomplete` included)
  must refuse before any mutation with exit `2` and `INCOMPLETE_TRANSACTION`,
  naming the `MigrationId` to resume or roll back.
- Force a rollback inverse step to fail: the run must land `failed_incomplete`
  with the backup intact and exit `3`.
- The installer's clean two-profile install and the migrator drive the same
  `skill-mesh-transaction` engine; divergent atomicity behavior between them
  fails the test.
- Rollback must restore original hashes and preserve unrelated files.
- A crash mid-`retire` (source moved, no `commit`) and a crash mid-`ledger` each
  resume via `-Resume` to the same terminal `applied` state -- the retire is
  completed, not re-driven from a now-absent source.
- After migration the rewritten ownership ledger contains no entry for
  `build-observer`, `goblin-sweep`, or `_shared`; ownership-safe uninstall
  leaves all three intact.
- A preserved consumer-only skill referencing `_shared` (e.g. `goblin-sweep`)
  still resolves its core after migration, with managed siblings migrated to
  per-skill embedded cores and the preserved skill plus `_shared` untouched.
- Existing distribution, router, package-integrity, release, telemetry,
  calibration, and smoke suites remain green.

### Host-native acceptance

- Use a clean temporary home rather than the live consumer for first
  acceptance.
- In Claude Code, invoke a representative portable skill and record the
  generated `.claude/skills/<skill>/SKILL.md` plus Claude adapter identity.
- In GitHub Copilot CLI, invoke the same skill and record the generated
  `.github/skills/<skill>/SKILL.md` plus GPT adapter identity.
- Keep `OPENAI_API_KEY` unset for the Copilot-native check.
- Run one explicit router override as a separate path so native discovery is
  not conflated with router dispatch.
- Rehearse rollback before approving the private coding-root follow-up.
- Repeat the same path-capture checks against the real coding-root substrate in
  Step 48; temporary-home success alone does not complete the plan.

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
| D6 | D | Skill eligibility is manifest-driven; migration classifies four classes and preserves consumer-only skills + the `_shared` core-holder, not the binary owned/foreign split | active |
| D7 | D | GitHub Copilot's native `.copilot/skills` discovery root is proven from a live session before migration tooling is built on it, not deferred to final acceptance | active |
| D8 | D | Installer and migrator share one journaled, resumable transaction engine (`tools/skill-mesh-transaction.ps1`) with an explicit state machine and ordered rollback, rather than each tool implementing atomicity | active |
| D9 | D | The backup payload set is pinned to the transaction's mutating action set -- byte-untouched consumer-only/core-holder trees are recorded by path+hash only, never copied -- reconciling rollback completeness with disclosure minimization | active |
| D10 | D | Static release/package-integrity gates assert documentation STRUCTURE only (presence, order, resolvability, no private-content leak); real host acceptance is operator evidence (Steps 43/47/48) that no static test can substitute for | active |
| D11 | D | The live coding-root cutover (Step 48) is owned by coding-root -- run from that repo against the skill-mesh release candidate, gated by a parked-work handshake and a dedicated cutover branch; the skill-mesh plan never commits coding-root state | active |
| D12 | D | The rewritten ownership ledger indexes only migration-installed managed files and never lists preserved consumer-only skills or `_shared`, so ownership-safe uninstall cannot delete the four-class-protected trees | active |
