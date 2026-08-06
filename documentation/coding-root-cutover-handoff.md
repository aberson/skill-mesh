# Coding-root cutover handoff

The copy-pasteable operator sequence that moves a private consumer workspace off its
hand-authored legacy skill trees and onto the two generated host profiles this package
builds — reversibly, with an external backup, and without ever deleting a skill the
consumer owns.

This is **Step 48** of
[`host-native-discovery-cutover-plan.md`](host-native-discovery-cutover-plan.md). It
*prepares* host acceptance; it does not perform it. Host acceptance is Steps 49 (a clean
temporary home) and 50 (the live consumer) — both operator steps, both producing evidence
this document cannot produce and this repository's tests must never claim.

Read [`host-discovery.md`](host-discovery.md) first if you have not. It is the authority on
the three host-loading mechanisms and the two discovery roots, and nothing below overrides it.
In particular: **a model answering correctly is not evidence of an installed profile.** Only a
captured `SKILL.md` path is.

---

## What this document is not

- **Not a script.** Every step is run and read by a human, in order, and every block below
  names the repository it runs in and the output that means it worked.
- **Not a lint or typecheck pass.** This repository has neither, by design
  (`documentation/architecture.md` §8.4). `pytest` is the only automated gate. Do not go
  looking for a linter, and do not report "0 lint violations" when wrapping.
- **Not interactive.** The inspector and the migrator declare *no* mandatory parameters
  precisely so they can never sit at a prompt — they validate their arguments manually and
  exit `2`. The installer's `-Provider` and `-Home` **are** mandatory, so always pass both:
  omitting either turns an unattended run into an interactive prompt.
- **Not a skill-mesh commit.** Everything this document changes in the consumer is owned,
  branched, committed, and merged by the consumer repository. This package is an external
  tool here.

### Command spelling

Commands use `pwsh` (PowerShell 7+), matching the command contract in
`documentation/architecture.md` §8. Paths are written with `/`, matching the README's Quick
start; `documentation/architecture.md` spells the same commands with `\`. PowerShell accepts
either separator, so the two spellings are the same command.

---

## 1. Ownership map and placeholders

Substitute these before running anything. Nothing below contains a real path, and nothing
below should be committed with a real path in it.

| Placeholder | What it is | Who owns changes to it |
|---|---|---|
| `<skill-mesh-repo>` | A checkout of **this** repository at the reviewed release candidate | skill-mesh |
| `<consumer-home>` | The private consumer workspace being cut over (a separate git repository) | the consumer repository |
| `<backup-dir>` | External backup root — **outside** `<consumer-home>` and outside every discovery root | neither; local scratch |
| `<backup-dir-parent>` | The existing directory `<backup-dir>` sits in, on the same volume — used only by the free-space wipe in §14 | neither; local scratch |
| `<dist-dir>` | Build output holding `claude/` and `gpt/` | generated, never committed |
| `<work-dir>` | Scratch directory for reports and JSON | generated, never committed |
| `<cutover-branch>` | The dedicated consumer branch this cutover lands on | the consumer repository |
| `<migration-id>` | The migrator's transaction id, printed by the dry run; shape `yyyyMMddTHHmmssZ-<8 lowercase hex>`, matched **case-sensitively** | generated |

Two facts about the consumer's Claude root that change what "replace this directory" means:

- **`<consumer-home>/.claude/skills` may be a junction target.** A user-profile skills root can
  be a junction that points *at* it, which is what makes those skills globally discoverable.
  Writing into the directory is therefore correct and safe; **replacing the directory itself**
  changes what the profile junction resolves to. The migrator only ever writes files into the
  root — it never swaps the root — and this document never asks you to.
- **`<consumer-home>/.github` may not exist at all.** A consumer that has never installed a GPT
  profile has no `.github/skills` root, so the GPT install creates it from scratch with nothing
  to collide with. Foreign-file collision guidance below therefore applies to the Claude root
  in practice, not the GPT one.

Tool invocations run from `<skill-mesh-repo>` so their paths stay repository-relative, exactly
as `documentation/architecture.md` documents them. Every `git` command runs with
`git -C <consumer-home>`, so the resulting commit is unambiguously the consumer's and this
checkout is never staged.

---

## 2. Preconditions: the parked-work handshake

A hard gate, not advice. The consumer repository carries parallel session work; applying a
cutover into a dirty tree sweeps unrelated changes into the cutover commit.

**Run in:** `<consumer-home>` (the consumer repository)

```powershell
git -C '<consumer-home>' status --porcelain
git -C '<consumer-home>' worktree list
git -C '<consumer-home>' log --all --since='2 hours ago' --oneline
Get-ChildItem -LiteralPath '<consumer-home>' -Force -Filter '.plan-expedite-state.*'
```

**Expect:** `status --porcelain` prints **nothing** (a clean tree); `worktree list` prints only
the main worktree; `log --all --since` prints nothing (no other session is mid-write); the
`Get-ChildItem` prints nothing (no parallel expedite state file). Any non-empty result means
work is still in flight — land or park it and re-run. Do not proceed.

Then cut a dedicated branch off the known-clean base.

**Run in:** `<consumer-home>` (the consumer repository)

```powershell
git -C '<consumer-home>' switch -c '<cutover-branch>'
git -C '<consumer-home>' rev-parse --abbrev-ref HEAD
```

**Expect:** the second command prints `<cutover-branch>` exactly. If it prints anything else,
stop — a later `git add` would land on the wrong branch.

---

## 3. Build the release-candidate distribution

**Run in:** `<skill-mesh-repo>` (this repository)

```powershell
python -m pytest tests/package-integrity -q
pwsh -File tools/build-distributions.ps1 -Provider both -OutputDir '<dist-dir>'
```

**Expect:** pytest reports all tests passed with no failures; the build exits `0` and
`<dist-dir>` then contains a `claude/` subtree of 50 skills and a `gpt/` subtree of 47 (the
three provider-native skills — `claude-oauth-auth`, `context-slim`, `judge-motion` — have no
GPT adapter and are excluded by design, not missing).

`<dist-dir>` is generated output. It is gitignored in this repository and must never be
committed on either side.

---

## 4. Create one private shared instruction source and two thin adapters

One source of truth, two thin host adapters. Full copies in both `CLAUDE.md` and `AGENTS.md`
drift; that is the whole reason this step exists (cutover plan §6, "`AGENTS.md` and `CLAUDE.md`
are instruction adapters, not skill registries").

The **content** of the shared source is private to the consumer and is deliberately not in this
public repository. Only the shape is prescribed here:

- `<consumer-home>/<shared-instructions>` — the one private document holding the workspace
  contract. Its content is the consumer's; this package never ships it.
- `<consumer-home>/CLAUDE.md` — a thin Claude Code adapter that loads the shared source.
- `<consumer-home>/AGENTS.md` — a thin GitHub Copilot CLI adapter that loads the same source.

Each adapter is a few lines: a title naming its host, one sentence pointing at
`<shared-instructions>`, and an instruction to load it in full. **Neither adapter enumerates or
embeds skills** — skills live only in the two discovery roots, and an instruction file is not a
skill registry. A host that injects `CLAUDE.md` and exposes skills from it is doing host
integration; that is never evidence of an installed profile.

**Run in:** `<consumer-home>` (the consumer repository)

```powershell
Test-Path -LiteralPath '<consumer-home>/<shared-instructions>'
Test-Path -LiteralPath '<consumer-home>/CLAUDE.md'
Test-Path -LiteralPath '<consumer-home>/AGENTS.md'
```

**Expect:** three `True` lines. A `False` for `AGENTS.md` is the common case on a first cutover
(the file has never existed) — author it before continuing, since a GPT host with no root
instruction adapter has no workspace contract at all.

This adapter refactor is a consumer-owned content change. It may land in the same
`<cutover-branch>` commit as the mechanical cutover or in a follow-up commit; it is never made
by a skill-mesh worktree.

---

## 5. Inspect the consumer home (read-only preflight)

Nothing mutates until you have read this report. The inspector is read-only under full-tree
hash comparison, never authenticates, and never prompts.

**Run in:** `<skill-mesh-repo>` (this repository; it reads `<consumer-home>` and writes only `<work-dir>`)

```powershell
pwsh -File tools/inspect-host-install.ps1 -Home '<consumer-home>'
pwsh -File tools/inspect-host-install.ps1 -Home '<consumer-home>' -Format json | Set-Content -LiteralPath '<work-dir>/preflight.json' -Encoding utf8
```

**Expect:** exit `0` and a text report that begins
`skill-mesh host-install report (schema_version 1)`, followed by `consumer_home:`, the
`instruction files:` block, one block per discovery root, then `ledger:`, `router:`,
`legacy_shadows:` and a `warnings (N):` list. Exit `2` means the `-Home` was invalid or
unreadable, or the manifest could not be parsed — fix that before anything else. The JSON form
writes exactly one document to stdout; diagnostics go to stderr.

Read these five fields before continuing:

| Field | What to look for |
|---|---|
| `profiles.claude.state` / `.link_type` | `present` on a legacy consumer. If `link_type` is a junction, note its `link_target` — see §1. |
| `profiles.gpt.state` | Usually `absent` on a first cutover; the GPT root has never existed. |
| `legacy_skills_gpt.skills[].eligibility` | The classification the retirement in §12 is driven by. |
| `router.classification` / `.version` | `legacy` means the old router is still on a resolution path. |
| `warnings[]` | `LEGACY_CLAUDE_SKILLS_GPT_PRESENT` is expected here; a `foreign`-class finding in a discovery root is not, and will block the migrator in §7. |

**The classification vocabulary is a four-class cascade, and only `managed` is retirable:**
a name in `config/skill-manifest.json` is `managed`; a `_shared` directory with no `SKILL.md` is
`core-holder`; any other directory that has a `SKILL.md` is `consumer-only`; anything else is
`foreign`. In the legacy GPT core tree the entries carry `SKILL-core.md` and `SKILL-gpt.md`
rather than `SKILL.md`, so a consumer-only entry there classifies **`foreign`**, not
`consumer-only`. That is exactly why §12 retires on a positive `managed` allowlist and never on
a "not consumer-only" denylist — a denylist would delete the consumer's own skill.

---

## 6. Choose the external backup directory

`-BackupDir` is **required in every migrator mode**, including the dry run, and it must be
outside the consumer home. Omitting it fails with `BACKUP_DIR_REQUIRED`; putting it inside the
home fails with `BACKUP_DIR_INSIDE_HOME`. Both are exit `2` and both happen **before** any
mutation.

**Run in:** `<skill-mesh-repo>` (this repository; the path it checks is a local scratch location)

```powershell
New-Item -ItemType Directory -Path '<backup-dir>' -Force | Out-Null
Test-Path -LiteralPath '<backup-dir>'
"<backup-dir> inside home: " + ('<backup-dir>'.ToLowerInvariant().StartsWith('<consumer-home>'.ToLowerInvariant()))
```

**Expect:** `True`, then `<backup-dir> inside home: False`. A `True` on the second line means
you picked a path inside the home — pick another; the migrator would refuse it anyway.

What lands in `<backup-dir>`: the transaction plan, an append-only journal, a backup manifest
recording release identity plus every original and installed hash, and the **pre-image payload
of every path the migration mutates**. What never lands there: the bytes of anything the
migration only *preserves*. A preserved tree is recorded in `preserved_files` by relative path
and SHA-256 only — never payload-copied — so private consumer content is not duplicated into a
backup it can never need.

Treat `<backup-dir>` as sensitive. It holds pre-images of the consumer's own files. Never
upload it, never add it to a repository, and delete it per §14.

---

## 7. Dry-run the migration

Omitting `-Apply`, `-Resume`, and `-Rollback` **is** the dry run. It is the safe default, it
mutates nothing — not the home, not the backup directory — and it is where you learn the
`<migration-id>`.

**Run in:** `<skill-mesh-repo>` (this repository; it plans against `<consumer-home>`)

```powershell
pwsh -File tools/migrate-legacy-install.ps1 -Home '<consumer-home>' -DistDir '<dist-dir>' -BackupDir '<backup-dir>'
```

**Expect:** exit `0` and a plan that begins `skill-mesh migration plan (schema_version 1)`,
then `migration_id: <migration-id>`, `source_release: commit=...`, an `actions:` block counting
`backup`, `install`, `retire`, `preserve`, `ledger`, and finally `blocked (0):` with nothing
under it. **Record the `migration_id`** — `-Resume` and `-Rollback` both require it.

If the last line is `blocked (N):` with findings, exit is `2`, nothing was written, and each
finding prints as `[CODE] <rel_path> -- <message>`. The codes you may see:
`MANIFEST_UNREADABLE`, `UNSAFE_LINK`, `FOREIGN_FILE`, `UNKNOWN_PROVIDER_ROOT`,
`MISSING_PROFILE`, `INCOMPLETE_TRANSACTION`, `PRECONDITION_DRIFT`, `INVALID_MODE`,
`INVALID_HOME`, `BACKUP_DIR_REQUIRED`, `BACKUP_DIR_INSIDE_HOME`, `DIST_DIR_REQUIRED`,
`INVALID_MIGRATION_ID`, `UNKNOWN_TRANSACTION`, `HOME_MISMATCH`, `RELEASE_MISMATCH`,
`TRANSACTION_RESOLVED`. `FOREIGN_FILE` is the common one on a hand-maintained consumer: a file
in a discovery root that is neither generated nor a recognisable skill. Resolve it in the
consumer (move it out, or make it a real skill directory) and re-run the dry run. Do **not**
reach for `-Force` on the installer; that is the expert override this whole document exists to
replace.

Re-read the plan until the counts match your intent. `preserve` should cover every consumer-only
tree and the `_shared` core-holder; `retire` should cover only stale marker-bearing generated
files.

---

## 8. Apply the migration

**Run in:** `<skill-mesh-repo>` (this repository; it mutates `<consumer-home>`)

```powershell
pwsh -File tools/migrate-legacy-install.ps1 -Home '<consumer-home>' -DistDir '<dist-dir>' -BackupDir '<backup-dir>' -Apply
```

**Expect:** exit `0` and a final line of the form
`migrate-legacy-install: migration <migration-id> APPLIED (N installed, N retired, N preserved).`
Claude and GPT are installed as **one** transaction — a failure in either profile rolls the
whole set back in reverse order and restores the prior ownership ledger.

Other outcomes and what they mean:

| Exit | Meaning | What to do |
|---|---|---|
| `0` | Applied. | Continue to §9. |
| `1` | Operational failure, **home left clean** (rollback completed, or nothing was mutated). | Read the diagnostic, fix the cause, re-run the dry run. |
| `2` | Blocked / unsafe precondition, **always pre-mutation**. | Nothing changed. Resolve the named code and re-run. |
| `3` | Rollback did not complete. **Two distinct meanings — see §10 before acting.** | Read §10. Do not restore a backup reflexively. |

If a bare `-Apply` refuses with `INCOMPLETE_TRANSACTION` (exit `2`), the home already holds an
unresolved transaction. Nothing was written. The message names the `MigrationId` **and its
status**, and **the remedy differs by status** — the generic "resume it or reverse it" advice is a
dead end for one of them:

| Status in the message | What it is | What to do |
|---|---|---|
| `prepared`, `applying`, `rolling_back` | Mid-flight and still resolvable by the tool. | Drive it forward with `-Resume -MigrationId <migration-id>`, or reverse it with `-Rollback -MigrationId <migration-id>`. |
| `failed_incomplete` | A rollback that did not complete. **Unresolved** (so it blocks a bare `-Apply`) and **terminal** at the same time: `-Resume` refuses it with `TRANSACTION_RESOLVED` (exit `2`) and `-Rollback` refuses it with `TRANSACTION_RESOLVED` too. Both remedies in the row above are dead ends. | No tool mode clears it. Recover by hand per §10's exit-`3` table, then **remove that transaction directory** to clear the block — the exact sequence is §10's "Clearing a `failed_incomplete` transaction". |

`applied` and `rolled_back` are terminal *and* resolved; they never block a later `-Apply`.

If the process is interrupted mid-apply, resume it — do not re-run a bare `-Apply`.

**Run in:** `<skill-mesh-repo>` (this repository; it mutates `<consumer-home>`)

```powershell
pwsh -File tools/migrate-legacy-install.ps1 -Home '<consumer-home>' -DistDir '<dist-dir>' -BackupDir '<backup-dir>' -Resume -MigrationId '<migration-id>'
```

**Expect:** the same `APPLIED` line and exit `0`. Resume is precondition-hash driven and
idempotent: it converges to the same terminal state without double-applying.

---

## 9. Validate both profiles

**Run in:** `<skill-mesh-repo>` (this repository; it reads `<consumer-home>`)

```powershell
pwsh -File tools/inspect-host-install.ps1 -Home '<consumer-home>' -Format json | Set-Content -LiteralPath '<work-dir>/postflight.json' -Encoding utf8
pwsh -File tools/inspect-host-install.ps1 -Home '<consumer-home>'
```

**Expect:** exit `0`, and in the text report both roots now read `state=present`. The `owned=`
count on each block equals that profile's manifest total — read them from
`config/skill-manifest.json` rather than memorising them: `counts.total` for the Claude root
(50 today) and `counts.portable` for the GPT root (47 today; the three provider-native skills
have no GPT adapter). `ledger: state=` reports a present ledger naming both providers with
`unrecognized=0`. Every entry you expected preserved is still listed, and `unowned` counts only
the consumer's own trees.

This validates **installation**, not **discovery**. Two different mechanisms; proving one never
proves the other. Discovery proof is §11.

---

## 10. Roll back the migration

Read this section **before** running §11. Rollback is the escape hatch for a failed acceptance,
and knowing the command afterwards is too late.

**Run in:** `<skill-mesh-repo>` (this repository; it restores `<consumer-home>`)

```powershell
pwsh -File tools/migrate-legacy-install.ps1 -Home '<consumer-home>' -BackupDir '<backup-dir>' -Rollback -MigrationId '<migration-id>'
```

**Expect:** exit `0` and a final line
`migrate-legacy-install: migration <migration-id> ROLLED BACK (N action(s) reversed).`
Rollback restores original hashes, removes only migration-owned files, and removes only
directories the migration itself created and only while they are empty. `-DistDir` is **not**
required for `-Rollback`; `-BackupDir` and `-MigrationId` are.

### Exit `3` has two meanings. Do not collapse them.

The run's own diagnostics say which one you are in. Acting on the wrong one is destructive.

| Diagnostic | What actually happened | Correct response |
|---|---|---|
| `ROLLBACK INCOMPLETE -- the consumer home is MIXED. The backup is retained at MigrationId ...` | A path the tool **mutated** could not be restored. The home genuinely holds a mix of generated and original files. | Recover from the retained backup payloads in `<backup-dir>/<migration-id>`. |
| A message stating that **every path this tool mutated was restored** and that the failure set is a **preserved** path | A path the migration only *preserved* changed. It carries no backup payload **by design** — those bytes are the consumer's own and are already intact. Nothing the tool touched is outstanding. | Inspect the named path. **Do not restore a backup over it** — the backup has no copy of it, and treating this as the mixed case would overwrite the consumer's newer bytes with older ones. |

A preserved path that drifts during a *pre-completion* abort is neither of these: it lands
`rolled_back` with an advisory naming the path and its expected/observed hashes, and a follow-up
bare `-Apply` re-plans and succeeds.

`-Rollback` refuses a transaction already in a terminal state (`rolled_back`,
`failed_incomplete`) with `TRANSACTION_RESOLVED` and exit `2`.

### Clearing a `failed_incomplete` transaction

Exit `3` leaves the transaction in status `failed_incomplete`, and that status is a corner the
tool deliberately will not drive you out of: `-Resume` refuses it (`TRANSACTION_RESOLVED`, exit
`2`), `-Rollback` refuses it (`TRANSACTION_RESOLVED`, exit `2`), and a bare `-Apply` refuses it
(`INCOMPLETE_TRANSACTION`, exit `2`) because it is still counted unresolved. **There is no tool
mode that resolves it.** You recover by hand, then clear the block yourself.

Recover first, using the row of the table above that your run's diagnostics put you in:

- **Row 1, genuinely mixed home.** Restore the affected paths from the retained pre-image payloads
  under `<backup-dir>/<migration-id>/payload/`, then re-run §9 and confirm the report reads as you
  expect.
- **Row 2, changed preserved path.** There is nothing to restore. Those bytes are the consumer's
  own, they carry no backup payload by design, and they are already intact. **Do not restore a
  backup over them.** Read the named path, satisfy yourself it is what you want, and move on.

Only when recovery is done, clear the block. Removing the transaction directory destroys the only
copy of that run's pre-images — copy anything you still need out of it **first**.

**Run in:** any shell (the path is local scratch; no repository is touched)

```powershell
Get-ChildItem -LiteralPath '<backup-dir>/<migration-id>' -Recurse -File | Select-Object -First 20 FullName
Remove-Item -LiteralPath '<backup-dir>/<migration-id>' -Recurse -Force -Confirm:$false
```

**Expect:** the listing shows you what you are about to destroy (review it before running the
second line), then `Remove-Item` prints nothing. Only this one transaction directory is removed;
every other transaction under `<backup-dir>` is untouched.

**Run in:** `<skill-mesh-repo>` (this repository; it plans against `<consumer-home>`)

```powershell
pwsh -File tools/migrate-legacy-install.ps1 -Home '<consumer-home>' -DistDir '<dist-dir>' -BackupDir '<backup-dir>'
```

**Expect:** exit `0` and `blocked (0):` — the `INCOMPLETE_TRANSACTION` finding is gone and a fresh
`-Apply` is available again. If `[INCOMPLETE_TRANSACTION]` still prints, a *different* unresolved
transaction for this home exists; the message names its id.

---

## 11. Host-acceptance gate (Steps 49 and 50)

**This document stops here and hands off.** Everything above is mechanical and reproducible.
What follows is operator evidence that no test in this repository can stand in for, and no
release gate may claim.

Steps 49 and 50 of
[`host-native-discovery-cutover-plan.md`](host-native-discovery-cutover-plan.md) own it:

- **Step 49** — acceptance from a *clean temporary* consumer home installed by this same
  release-candidate migrator (not a hand-planted fixture): invoke one representative portable
  skill in Claude Code and the same skill in GitHub Copilot CLI, record the discovered
  `SKILL.md` path and the provider adapter identity for each, confirm the GPT path resolves the
  `.github/skills` root rather than `.claude/skills` shadowing or `CLAUDE.md` runtime injection,
  confirm GPT works with **no** `OPENAI_API_KEY` (Copilot subscription auth is the transport),
  confirm the explicit router override separately in its own environment, and exercise rollback.
- **Step 50** — the same acceptance against the live consumer on `<cutover-branch>`, plus the
  parked-work handshake of §2 and the retained rollback backup.

Nothing in §12 or §13 runs until acceptance has recorded PASS. A failed check triggers §10 and
marks the step BLOCKED — it never proceeds to retirement.

---

## 12. Retire the legacy GPT core tree and the old router — only after acceptance

Classify first, retire second, and only on a positive `managed` allowlist. A blanket directory
removal here would silently destroy consumer-only entries that exist *only* in the legacy GPT
tree and have no manifest record and no generated counterpart.

Run §12.1 and §12.2 in **one** PowerShell session: §12.2 uses the `$managed` set §12.1 computed.
If the session is lost, re-run §12.1 before §12.2 rather than reconstructing the set by hand.

### 12.1 Classify, and record what is preserved

**Run in:** `<consumer-home>` (the consumer repository; this command only reads and writes `<work-dir>`)

```powershell
$report = Get-Content -Raw -LiteralPath '<work-dir>/postflight.json' | ConvertFrom-Json
$legacy = @($report.legacy_skills_gpt.skills)
$managed = @($legacy | Where-Object { $_.eligibility -eq 'managed' })
$managedNames = @($managed | ForEach-Object { $_.name })
$legacyRoot = Join-Path '<consumer-home>' '.claude/skills-gpt'
$keepDirs = @(Get-ChildItem -LiteralPath $legacyRoot -Directory -Force | Where-Object { $managedNames -notcontains $_.Name })
$keepFiles = @($keepDirs | ForEach-Object { Get-ChildItem -LiteralPath $_.FullName -Recurse -File })
$keepFiles | Get-FileHash -Algorithm SHA256 | Export-Csv -NoTypeInformation -LiteralPath '<work-dir>/preserved-legacy-gpt.csv'
"managed (retire): $($managed.Count)"
"preserved (keep in place): $($keepDirs.Count) -- $(($keepDirs.Name) -join ', ')"
"preserved rows: $(@(Import-Csv -LiteralPath '<work-dir>/preserved-legacy-gpt.csv').Count) of $($keepFiles.Count)"
```

**Expect:** on the reference consumer, `managed (retire): 47`,
`preserved (keep in place): 1 -- goblin-sweep`, and `preserved rows: N of N` with **the two
numbers equal and both non-zero**. Your counts may differ; what must hold is that every name in
the preserved line is a skill the consumer authored, no name in it appears in
`config/skill-manifest.json`, and the row count matches the file count. A `preserved rows: 0 of
N` (or any mismatch) means the CSV is not the audit record it claims to be — **stop**, because a
later step treats it as one. `<work-dir>/preserved-legacy-gpt.csv` records **path and hash only,
never a copy of the payload**; keep it with the backup and do not commit it.

**Why the preserved set is derived from the directory listing, not from `rel_path`.** The
inspector display-sanitizes `name` and `rel_path` for any entry that is *not* in the manifest:
`Get-SafeLabel` replaces every `[^A-Za-z0-9._-]` character with `_` and truncates at 64
characters. A consumer directory whose name contains a space (or any other character outside that
class) is therefore reported under a path that **does not exist on disk**, and a `$keep` pipeline
built on `rel_path` would silently write a zero-row CSV while still printing a success-shaped
count line. Manifest names are a closed vocabulary and are never sanitized, so `$managedNames` is
safe to use as the allowlist — the sanitation hazard is confined to the non-managed side, which
is exactly the side this CSV is the audit record for.

Do not be alarmed that a preserved entry's `eligibility` reads `foreign` rather than
`consumer-only`: in this tree the entries carry `SKILL-core.md` and `SKILL-gpt.md` instead of
`SKILL.md`, and the inspector's cascade needs a `SKILL.md` to call something a consumer skill
(§5). `foreign` here means "not ours to touch", which is precisely the treatment it must get.
That is why the retire set is the positive `managed` allowlist and the preserved set is
*everything else that is actually on disk* — never an `-eq 'consumer-only'` filter, which in this
tree would match nothing and quietly preserve nothing.

Sanity-check the retire set before deleting anything: every `managed` name must already have a
generated GPT profile in place from §9.

**Run in:** `<consumer-home>` (the consumer repository; read-only)

```powershell
$missing = @($managed | Where-Object { -not (Test-Path -LiteralPath (Join-Path '<consumer-home>' (".github/skills/" + $_.name + "/SKILL.md"))) })
"managed entries with no generated counterpart: $($missing.Count)"
```

**Expect:** `managed entries with no generated counterpart: 0`. Any other number means a
generated profile is missing and that entry is **not** generated-superseded — stop and re-run
§9 rather than retiring it.

### 12.2 Retire only the managed entries

**Run in:** `<consumer-home>` (the consumer repository — this stages a deletion in git)

```powershell
foreach ($e in $managed) { git -C '<consumer-home>' rm -r -q -- $e.rel_path }
git -C '<consumer-home>' status --porcelain -- '.claude/skills-gpt'
```

**Expect:** the status listing shows `D` entries for the managed skill directories only. Every
preserved name from §12.1 is **absent** from that listing — if one appears, unstage it
immediately with `git -C '<consumer-home>' restore --staged --worktree -- <path>` and stop.

#### If the legacy tree is not tracked in the consumer repository

`git rm` then reports `did not match any files` and stages nothing, and a direct delete is
**irreversible**. Before you run one, understand that **there is no existing recovery source for
these bytes**:

- **The migrator's backup does not contain them.** It holds pre-images only of the paths *it*
  mutates, and it never touches `.claude/skills-gpt` at all — no install target, no retire target,
  no preserve payload. Nothing under `<backup-dir>` is a copy of this tree.
- **`<work-dir>/preserved-legacy-gpt.csv` does not contain them either.** It is built from the
  preserved (non-managed) set, so it has **zero rows for every directory this deletion removes**.
- **The bytes are hand-authored.** These entries carry `SKILL-core.md` and `SKILL-gpt.md` — a
  different artifact from the generated `SKILL.md`, with no counterpart in `<dist-dir>`. Any local
  drift in them exists nowhere else.

So copy the managed set into the backup **first**, verify the copy, and only then delete.

**Run in:** `<consumer-home>` (the consumer repository; this reads the home and writes `<backup-dir>`)

```powershell
$rescue = Join-Path '<backup-dir>' 'legacy-gpt-managed-preimage'
New-Item -ItemType Directory -Path $rescue -Force | Out-Null
foreach ($e in $managed) { Copy-Item -LiteralPath (Join-Path '<consumer-home>' $e.rel_path) -Destination (Join-Path $rescue $e.name) -Recurse -Force }
$srcCount = @($managed | ForEach-Object { Get-ChildItem -LiteralPath (Join-Path '<consumer-home>' $_.rel_path) -Recurse -File }).Count
$dstCount = @(Get-ChildItem -LiteralPath $rescue -Recurse -File).Count
"rescue copy: $dstCount file(s) of $srcCount"
```

**Expect:** `rescue copy: N file(s) of N` with the two numbers **equal and non-zero**. Any
mismatch, any error, or a zero means the copy is incomplete — **stop and delete nothing.**
(`$e.rel_path` is safe to use here: managed names come from `config/skill-manifest.json` and are
never display-sanitized. See §12.1.)

**Run in:** `<consumer-home>` (the consumer repository; this destroys files with no git record)

```powershell
foreach ($e in $managed) { Remove-Item -LiteralPath (Join-Path '<consumer-home>' $e.rel_path) -Recurse -Force -Confirm:$false }
@($managed | Where-Object { Test-Path -LiteralPath (Join-Path '<consumer-home>' $_.rel_path) }).Count
```

**Expect:** `0` — every managed directory is gone. An untracked deletion leaves no git record, so
the rescue copy under `<backup-dir>/legacy-gpt-managed-preimage` is now the **only** recovery
source for these directories. It is part of `<backup-dir>` and is covered by the §14 retention
window and the §14 secure deletion along with the rest of it.

### 12.3 Retire the old router

The consumer's instruction file references the router at its historical path
(`.claude/lib/skill-router.ps1`) — this is an instruction-file reference, not a hook wiring, so
the fix is a delegating shim at that exact path until the consumer's own reference refactor
lands.

**Run in:** `<skill-mesh-repo>` (this repository; it writes the shim into `<consumer-home>`)

```powershell
pwsh -File tools/gen-router-shim.ps1 -Destination '<consumer-home>'
```

**Expect:** exit `0`, and `<consumer-home>/.claude/lib/skill-router.ps1` is now a generated shim
that forwards every argument to this checkout's `runtime/skill-router.ps1` and returns its exit
code unchanged. The shim embeds an **absolute** path to `<skill-mesh-repo>/runtime/skill-router.ps1`,
so `<skill-mesh-repo>` must stay where it is (or the shim must be regenerated with
`-RuntimeRouter` pointed at the new location).

**Run in:** `<consumer-home>` (the consumer repository; read-only)

```powershell
git -C '<consumer-home>' grep -n -- 'skill-router.ps1'
```

**Expect:** every remaining hit is either the generated shim itself or an instruction-file
reference that the shim now satisfies. A live reference to any *other* retired router path is a
stop condition — shim it or refactor the reference before §13.

---

## 13. Commit the coding-root change on its own branch

This is a **consumer-owned** commit on the consumer's dedicated branch. The skill-mesh checkout
is never staged, and no skill-mesh worktree ever makes this commit.

**Run in:** `<consumer-home>` (the consumer repository)

```powershell
git -C '<consumer-home>' rev-parse --abbrev-ref HEAD
git -C '<consumer-home>' status --porcelain
```

**Expect:** `<cutover-branch>` on the first line, and a change list containing **only** the
installed profiles, the retired managed entries, the router shim, and the instruction adapters
from §4. Any unrelated path in that list is parallel work that escaped §2 — stop and park it.

**Run in:** `<consumer-home>` (the consumer repository)

```powershell
git -C '<consumer-home>' add -- '.claude/skills' '.github/skills' '.claude/skills-gpt' '.claude/lib' 'CLAUDE.md' 'AGENTS.md'
git -C '<consumer-home>' commit -m 'chore(skills): cut over to generated skill-mesh host profiles'
git -C '<consumer-home>' show --stat --oneline HEAD
```

**Expect:** the commit summary lists only the paths added above. Path-scoped `add` is
deliberate: a bare `git add -A` in a consumer workspace sweeps nested repositories and parallel
session artifacts into the cutover commit. The consumer repository's owner reviews and merges
this branch; this package does not.

Add the shared-instructions path from §4 to the `add` list if that refactor is landing in the
same commit.

---

## 14. Backup retention window and secure deletion

**Retention window: keep `<backup-dir>` until both of these are true.**

1. Host acceptance (§11) has recorded PASS for the live consumer, and
2. thirty days of normal use have passed with no rollback needed.

Until then the backup is the only recovery source for anything the migration mutated. Keep it
local: never upload it, never add it to a repository, never include it in a release artifact or
a telemetry payload. It contains pre-images of the consumer's own files.

Once both conditions hold, delete it — and only then.

**Run in:** any shell (the path is local scratch; no repository is touched)

```powershell
Remove-Item -LiteralPath '<backup-dir>' -Recurse -Force -Confirm:$false
Test-Path -LiteralPath '<backup-dir>'
cipher /w:'<backup-dir-parent>'
```

**Expect:** `False` from `Test-Path`, then `cipher` reports it is writing its three passes and
finishes without error. `Remove-Item` unlinks the files; `cipher /w:` overwrites the deallocated
space on that volume so the deleted pre-images are not trivially recoverable. `<backup-dir-parent>`
must be an existing directory on the same volume — `cipher` wipes the volume's free space, and
the pass can take a long time on a large disk. Neither command prompts.

Two caveats on the `cipher /w:` pass, both of which decide *when* and *whether* to run it:

- **It consumes the volume's entire free space while it runs.** `cipher /w:` fills the free space
  with its passes before releasing it, so for the duration the volume is effectively full. Any
  concurrent work writing to that volume — a build, a test run, a database, the pagefile — can
  fail on out-of-disk. Run it when nothing else is using the volume, not alongside a build.
- **On a TRIM-enabled SSD it does not deliver the overwrite guarantee it states.** The controller
  remaps and may have already discarded the physical blocks the deleted files occupied, so the
  passes overwrite logical space the old bytes no longer live in. Treat it as best effort on SSDs;
  where the pre-images genuinely must be unrecoverable, use full-volume encryption (so the deleted
  bytes were never plaintext at rest) or the drive's own secure-erase.

---

## See also

- [`host-discovery.md`](host-discovery.md) — the three host-loading mechanisms and the two
  discovery roots. The authority; nothing here overrides it.
- [`host-native-discovery-cutover-plan.md`](host-native-discovery-cutover-plan.md) — the design
  authority, and the home of Steps 49 and 50.
- [`migration.md`](migration.md) — what changed in the repackaging and what a pre-migration
  link, clone, or install should point at now.
- [`architecture.md`](architecture.md) §5, §8 — host-native binding versus router dispatch, and
  the command contract this document's spellings follow.
- [`providers/claude.md`](providers/claude.md), [`providers/gpt.md`](providers/gpt.md) — per-host
  binding and capabilities.
