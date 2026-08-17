<#
.SYNOPSIS
    migrate-legacy-install.ps1 -- reversible cutover of a legacy consumer home to
    the generated host profiles, as ONE journaled transaction with an external
    backup, ordered rollback, and idempotent crash-resume.

.DESCRIPTION
    The safe installer REFUSES a live legacy Claude tree (hand-authored SKILL.md
    files carry no provenance marker, so they are foreign), and -Force overwrites
    them with no backup and no undo. This command is the third option: classify
    every path, back up the pre-image of everything it will mutate, apply the
    Claude and GPT profiles as ONE transaction, and be able to put the home back.

    DRY RUN IS THE DEFAULT. With no -Apply/-Resume/-Rollback the command plans and
    prints a MigrationPlan and mutates NOTHING -- not the home, not the backup
    directory.

    CLASSIFICATION is the Step-46 inspector's manifest-driven cascade, reused
    verbatim so preserve/retire/install cannot diverge from what the read-only
    preflight reported:
        in config/skill-manifest.json      -> managed
        `_shared` with no SKILL.md         -> shared-payload (per-FILE, see below)
        has a SKILL.md                     -> consumer-only
        anything else                      -> foreign
    `managed` trees are migrated (their generated paths are installed over, with
    the pre-image backed up). A marker-bearing path the current distribution no
    longer emits is handled differently by LOCATION: under the retired
    `.copilot/skills` root it is retired; under an active discovery root it is left
    untouched and reported as ACTIVE_MANAGED_FILE_RETAINED. Content provenance alone
    never authorizes deletion from an active root.
    `consumer-only` trees are PRESERVED byte-for-byte -- never overwritten, never
    retired, never a block -- and are recorded in the backup manifest by relative
    path and SHA-256 ONLY, never payload-copied, so private consumer content is
    not duplicated into a backup it can never need.
    `foreign` BLOCKS before the first mutation.

    `shared-payload` IS CLASSIFIED PER FILE, NEVER PER DIRECTORY. The builder now
    emits a shared support payload at each profile root (dist/<p>/_shared/<asset>),
    so a `_shared` directory in a consumer home holds two populations that must not
    be conflated. A path the supplied distribution ships is managed, installed over,
    and indexed for the installer's ledger-scoped uninstall (whose separate
    installed-hash safety repair is a mandatory pre-live blocker). A non-shipped file bearing the
    provenance marker is a generated-looking candidate: under the retired root the
    root's independent positional signal authorizes retirement; under an active root
    it is retained with a named advisory. Every other file in that directory is the
    consumer's and is PRESERVED exactly like a consumer-only skill.
    A directory-wide claim would be silent data loss in the audit records rather
    than on disk: a consumer-authored `_shared` file would fall out of the preserve
    action set, out of BackupManifest.preserved_files, out of the precondition and
    post-install checks, and out of the rollback drift advisory -- all at once.

    Test-SkillMeshProvenance from tools/skill-mesh-provenance.ps1 is dot-sourced,
    never forked. Its result identifies generated-looking bytes, but may authorize a
    retire only together with residence under the retired `.copilot/skills` root.
    The only non-marker files this command ever writes over are the exact target
    paths of the generated distribution -- the legacy adoption this command exists
    to perform -- and every one of those has its pre-image in the backup first.

    THE INSTALL PATH CARRIES A PRE-IMAGE IDENTITY GUARD
    (Assert-InstallTargetAdoptable). The
    installer REFUSES any target that exists without the marker; this command adopts
    such a target on purpose, but only the ones its own plan already accounted for.
    The guard re-reads the target immediately before the copy and refuses when the
    bytes there are not the pre-image the plan recorded, regardless of whether they
    retain a generated-looking marker. That is the difference between an audited adoption and a silent
    clobber: an install action planned against an ABSENT target carries pre_hash
    $null and therefore NO backup payload, so a consumer file that appears at that
    path after planning would be destroyed with nothing to restore from. -Apply
    catches the wide window via Test-Preconditions; -Resume does not run
    preconditions at all, so without this guard the resume path had no check.

    ATOMICITY IS NOT IMPLEMENTED HERE. The state machine, append-only journal,
    ordered rollback, and resume live in tools/skill-mesh-transaction.ps1, shared
    with tools/install-skill-mesh.ps1, so the "both profiles or neither" guarantee
    has one implementation.

    PROVIDER VOCABULARY comes from the manifest's own top-level `providers`
    object (never a hardcoded {claude, gpt}); the per-provider discovery root comes
    from tools/skill-mesh-discovery.ps1, the ONE owner of that map, which the
    installer and the inspector also read (it is no longer mirrored per tool -- a
    duplicated shape constant always drifts). A manifest provider
    with no known discovery root BLOCKS rather than being silently skipped -- a
    silent skip would be a false-clean migration that half-migrated the home.

.PARAMETER Home
    Consumer PROJECT workspace root to migrate. Required in every mode. This is
    not the operator's personal home: `~/.copilot/skills` is an active Copilot
    personal discovery root and is outside this migrator's retirement authority.
    `-ProjectRoot` is the preferred spelling; `-Home` remains a compatibility
    alias. Backed by $TargetHome ($HOME is a protected automatic variable and
    cannot be bound as a parameter).

.PARAMETER BackupDir
    External backup root, OUTSIDE the consumer home. Required in every mode: it
    locates the transaction folder. -Apply without it FAILS before any mutation.

.PARAMETER DistDir
    Pre-built dist root (containing claude/ and gpt/) from
    tools/build-distributions.ps1. Required for dry-run, -Apply, and -Resume.

.PARAMETER Apply / -Resume / -Rollback
    Mutually exclusive. Omit all three for the safe preview. -Resume and -Rollback
    require -MigrationId.

.PARAMETER Format
    'text' (default) or 'json'. In dry run, 'json' emits exactly one MigrationPlan.

.NOTES
    Exit codes: 0 success; 1 operational failure with every verified file mutation
    reversed (empty directories created by the migration may remain because they
    carry no durable identity), or nothing was mutated; 2 blocked / unsafe precondition
    / refused incomplete transaction, always PRE-MUTATION; 3 rollback did not
    complete -- either a MUTATED path could not be restored (the home is mixed and
    the retained backup is the recovery source) or a PRESERVED path changed and
    carries no backup payload by design (every mutated path was restored; those
    bytes are the consumer's own and are already intact). The run's diagnostics
    say which -- see decision D2 in
    documentation/step-47-decomposition-decision.md.

    ASCII-only, no BOM (PowerShell 5.1 reads a no-BOM .ps1 as ANSI/cp1252).
#>

[CmdletBinding()]
param(
    # NOT [Parameter(Mandatory)]: a mandatory parameter PROMPTS when absent in an
    # interactive host. This command must never prompt, so every requirement is
    # validated manually and exits 2.
    [Alias('Home', 'Destination', 'ProjectRoot')]
    [string]$TargetHome = '',

    [string]$DistDir = '',

    [string]$BackupDir = '',

    [switch]$Apply,

    [switch]$Resume,

    [switch]$Rollback,

    [string]$MigrationId = '',

    [ValidateSet('text', 'json')]
    [string]$Format = 'text'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -- Path resolution ----------------------------------------------------------

$TOOLS_DIR = $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $TOOLS_DIR
$PATH_GUARD = Join-Path $REPO_ROOT 'runtime\path-guard.ps1'
$PROVENANCE = Join-Path $TOOLS_DIR 'skill-mesh-provenance.ps1'
$TRANSACTION = Join-Path $TOOLS_DIR 'skill-mesh-transaction.ps1'
$DISCOVERY = Join-Path $TOOLS_DIR 'skill-mesh-discovery.ps1'
$MANIFEST_REL = 'config/skill-manifest.json'
$MANIFEST_PATH = Join-Path $REPO_ROOT 'config\skill-manifest.json'

# Dot-source the four shared, single-source-of-truth libraries (no -Path, so only
# their functions load).
. $PATH_GUARD
. $PROVENANCE
. $TRANSACTION
. $DISCOVERY

$UTF8_NO_BOM = New-Object System.Text.UTF8Encoding($false)

$SCHEMA_VERSION = 1
$ROOT_ENCODING = 'canonical-realpath.v1'

# Provider -> discovery root, from the ONE shared owner
# (tools/skill-mesh-discovery.ps1) rather than a third hand-maintained mirror. The
# provider VOCABULARY still comes from the manifest; this map only says where a
# known provider's tree lives.
$DISCOVERY_SUBDIR = Get-SkillMeshDiscoveryRoots
# The pre-Step-44 GPT target. Copilot does not discover it, so any generated tree
# found here is superseded and gets RETIRED into the backup.
$RETIRED_ROOT_REL = Get-SkillMeshRetiredCopilotRoot

$LEDGER_NAME = '.skill-mesh-install.json'
$LEDGER_VERSION = 1

# The shared support payload the builder emits at each PROFILE ROOT, as a sibling of
# the per-skill directories (tools/build-distributions.ps1 $SHARED_DEST). One
# spelling, used by the dist walk, the home scan, and the eligibility cascade, so a
# rename cannot half-land.
$SHARED_DIR_NAME = '_shared'

# Stable diagnostic identifier for generated-looking paths the current distribution
# no longer emits inside an ACTIVE discovery root. These paths are never actions:
# content provenance is consumer-forgeable, so it may flag a candidate but cannot
# authorize deletion without the retired-root positional signal.
$ACTIVE_MANAGED_RETAIN_ADVISORY = 'ACTIVE_MANAGED_FILE_RETAINED'

# FIRST-SEGMENT ALLOWLIST for a built profile. Everything directly under
# dist/<provider>/ is a manifest skill directory EXCEPT the entries listed here.
# It is a CLOSED list, deliberately -- not a "not in the manifest -> allow"
# relaxation: an unmanifested skill directory must still block with FOREIGN_FILE.
$PROFILE_ROOT_DIRS = @($SHARED_DIR_NAME)

$PLAN_FILE = 'plan.json'
$BACKUP_MANIFEST_FILE = 'backup-manifest.json'
$JOURNAL_FILE = 'journal.jsonl'
$PAYLOAD_DIR = 'payload'

# -- Diagnostics / exits ------------------------------------------------------

function Write-Diag([string]$message) {
    [Console]::Error.WriteLine("migrate-legacy-install: $message")
}

function Write-Outcome([string]$message) {
    # The human-readable outcome line. Under -Format json it is routed to STDERR:
    # stdout must carry exactly ONE JSON document, and a Write-Host line prepended
    # to it makes the stream unparseable for the caller the json format exists for.
    if ($Format -eq 'json') {
        [Console]::Error.WriteLine("migrate-legacy-install: $message")
    } else {
        Write-Host "migrate-legacy-install: $message"
    }
}

function Exit-Blocked([string]$code, [string]$message) {
    # The ONLY exit-2 path: a blocked or unsafe precondition, always before the
    # first mutation.
    Write-Diag "BLOCKED [$code] $message"
    if ($Format -eq 'json') {
        Write-Output (New-ResultDocument 'blocked' $null @(New-Block $code '' $message) | ConvertTo-Json -Depth 6)
    }
    exit 2
}

$SAFE_LABEL_MAX = 64

function Get-SafeLabel([string]$value, [int]$max = $SAFE_LABEL_MAX) {
    # Bound ONE consumer-supplied path segment for display: the legal skill-name
    # charset, a length cap, and no separators, quotes, list commas, or control
    # characters. Same discipline (and same cap) as inspect-host-install.ps1's
    # Get-SafeLabel, added there for #84. Replacement rather than redaction keeps a
    # real directory identifiable while making it unable to corrupt the report.
    if ([string]::IsNullOrEmpty($value)) { return '<unnamed>' }
    $clean = [regex]::Replace($value, '[^A-Za-z0-9._-]', '_')
    if ($clean.Length -gt $max) { $clean = $clean.Substring(0, $max) + '~' }
    return $clean
}

function Get-SafeRelPathLabel([string]$relPosix) {
    # Bound every segment of a home-relative path for DISPLAY.
    #
    # Scope is deliberate. This is applied to `blocked[].rel_path` -- the
    # diagnostic channel an operator reads, pastes, and forwards -- and to the text
    # report built from it. It is NOT applied to `actions[].rel_path` or to the
    # backup manifest's original_files/preserved_files entries: those are
    # OPERATIONAL records. Undo resolves a target from the action's rel_path and
    # audit/restore fidelity requires the exact original bytes, so bounding them
    # would silently break rollback for any path the filter touched -- trading a
    # report-formatting nit for data loss.
    if ([string]::IsNullOrEmpty($relPosix)) { return '' }
    return ((($relPosix -split '/') | ForEach-Object { Get-SafeLabel $_ }) -join '/')
}

function New-Block([string]$code, [string]$relPath, [string]$message) {
    # rel_path is BOUNDED here, at the single construction point, so no blocked
    # finding can carry an unbounded or separator-injecting consumer directory name
    # into the report on any code path.
    return [PSCustomObject]@{
        code     = $code
        rel_path = (Get-SafeRelPathLabel $relPath)
        message  = $message
    }
}

function New-ResultDocument([string]$status, [string]$migrationId, $blocked) {
    return [PSCustomObject]@{
        schema_version = $SCHEMA_VERSION
        mode           = $script:RunMode
        migration_id   = $migrationId
        status         = $status
        blocked        = @($blocked)
    }
}

# -- THE PATH INVARIANT -------------------------------------------------------
#
#   No path may read or mutate a consumer-home target without re-resolving
#   containment, and no path may destroy or overwrite bytes without first proving
#   those bytes are ours.
#
# Both halves are enforced STRUCTURALLY, in one place each, because enforcing them
# per call site is what failed: three review rounds each found the guard missing at
# a NEW site whose sibling branch already had it.
#
#   Containment  -> Resolve-HomeTarget / Resolve-HomeTargetForRead (this section)
#                   and Resolve-TxPayloadPath for the transaction directory.
#   Byte identity -> Assert-OurBytesAtTarget (one function, called by every undo
#                   branch).
#
# The convention the structural gate keys off:
#   * every mutating primitive (Copy-Item / Remove-Item / Move-Item /
#     [IO.File]::Write*) takes its path from a variable named $safe*;
#   * a $safe* variable is only ever assigned from one of the resolvers above.
# tests/distributions/test_path_choke_point.py::
# test_every_mutating_primitive_resolves_through_the_choke_point walks every
# git-tracked .ps1 and fails on any violation it can parse. It is a best-effort
# tripwire over source TEXT, not a proof of completeness: see that module's
# KNOWN BLIND SPOTS section for the expression shapes it cannot see, and note it
# covers only the containment half -- byte identity is convention-guarded by the
# Assert-OurBytesAtTarget call in every destroying undo branch.

function Join-HomePathLexical([string]$relPosix) {
    # LEXICAL ONLY: no reparse-point resolution, no containment proof, nothing that
    # makes the result safe to hand to the filesystem.
    #
    # Its ONLY sanctioned caller is Resolve-HomeTarget below. It is named this way
    # on purpose -- the previous name (Join-HomePath) read like a safe path builder,
    # and a `Copy-Item -LiteralPath (Join-HomePath $a.rel_path)` in the backup
    # materialization loop survived a whole review round looking perfectly ordinary
    # while silently capturing a pre-image from OUTSIDE the home.
    return (Join-Path $script:HomeAbs ($relPosix -replace '/', '\'))
}

function Resolve-HomeTarget {
    <#
      THE choke point for every consumer-home path this tool touches -- read or
      write, mutate or undo, prepare or clean up.

      Re-resolves the parent AND the target through the path guard, which follows
      junctions and symlinks component by component, and asserts the real path is
      still inside the consumer home RIGHT NOW. Scan-time classification is not
      enough: a reparse point planted on an ancestor after the scan redirects the
      real path before the mutation runs, which is the whole TOCTOU window.

      Throws on escape. Returns the CANONICAL RESOLVED path -- never the lexical one
      it started from -- which callers assign to a $safe* variable and hand to the
      filesystem. Returning the lexical path would leave the TOCTOU window open: the
      OS would re-resolve it at operation time, following whatever reparse points
      exist then, which is exactly the race this function exists to close.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$RelPosix,
        [string]$Operation = 'touch it'
    )
    $abs = Join-HomePathLexical $RelPosix
    $parent = Split-Path -Parent $abs
    if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-ContainedInHome $parent)) {
        throw ("migrate-legacy-install: SECURITY -- the parent of '$RelPosix' resolves outside " +
               "the consumer home (junction or symlink escape); refusing to $Operation.")
    }
    $resolved = Get-ContainedHomePath $abs
    if ($null -eq $resolved) {
        throw ("migrate-legacy-install: SECURITY -- '$RelPosix' resolves outside the consumer " +
               "home (junction or symlink escape); refusing to $Operation.")
    }
    return $resolved
}

function Resolve-HomeTargetForRead([string]$relPosix) {
    # The read side of the SAME gate. Returns $null instead of throwing, because a
    # read is not a mutation: a redirected path simply has no readable content here,
    # and Get-SkillMeshFileSha256 $null yields $null -- which then fails whatever
    # hash comparison the caller was making. A read never silently succeeds against
    # a file outside the home.
    try {
        return (Resolve-HomeTarget -RelPosix $relPosix -Operation 'read it')
    } catch {
        return $null
    }
}

function Get-HomeRelHash([string]$relPosix) {
    # The one way this tool hashes a consumer-home path: gated, and $null for both
    # "absent" and "escapes the home".
    return (Get-SkillMeshFileSha256 (Resolve-HomeTargetForRead $relPosix))
}

function Assert-OurBytesAtTarget {
    <#
      THE content-identity rule, in one place, called by EVERY undo branch.

      Before destroying or overwriting bytes at a consumer-home path, the bytes
      that are there must be exactly the ones this transaction left there
      ($ExpectedHash, i.e. the action's post_hash) -- or nothing at all.

      An absent target is fine: there is nothing to destroy. Anything else means
      the content changed after this transaction wrote it, so undoing would destroy
      an edit this transaction did not make. That is never the lesser evil: the
      throw lands failed_incomplete with the backup retained, which tells the
      operator the truth instead of reporting `rolled_back` over a home that was
      silently clobbered.

      This lived as per-branch inline checks and predictably drifted: the `install`
      overwrite branch and the `ledger` branch each lacked the check their sibling
      branch had.
    #>
    param(
        [string]$SafePath,
        $ExpectedHash,
        [string]$RelPath,
        [string]$Operation
    )
    $exists = Test-Path -LiteralPath $SafePath
    if ($exists -and (-not (Test-Path -LiteralPath $SafePath -PathType Leaf))) {
        throw ("migrate-legacy-install: refusing to $Operation '$RelPath' -- the " +
               "target is now a directory or other non-file object. Treating its " +
               "null file hash as absence would let a copy write a nested file " +
               "that this transaction cannot account for.")
    }
    $current = Get-SkillMeshFileSha256 $SafePath
    if (-not $exists) { return }
    if ($null -eq $current) {
        throw ("migrate-legacy-install: refusing to $Operation '$RelPath' -- the " +
               "existing file's bytes could not be hashed, so content identity " +
               "cannot be established.")
    }
    if ([string]$current -eq [string]$ExpectedHash) { return }
    throw ("migrate-legacy-install: refusing to $Operation '$RelPath' -- the bytes there are no " +
           "longer the ones this migration wrote, so undoing would destroy content this " +
           "transaction did not create.")
}

function ConvertTo-HomeRel([string]$absPath) {
    $full = [System.IO.Path]::GetFullPath($absPath)
    if ($full.Equals($script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase)) { return '.' }
    $rel = $full.Substring($script:HomeAbs.Length).TrimStart('\', '/')
    return ($rel -replace '\\', '/')
}

function Get-ContainedHomePath([string]$absPath) {
    # Re-resolve through the path guard (which FOLLOWS junctions/symlinks) and
    # return the CANONICAL REAL PATH when it is still inside the home, else $null.
    #
    # Returning the resolved value -- rather than discarding it and answering a mere
    # boolean -- is the whole point. A caller that validates one string and then
    # hands a DIFFERENT (lexical) string to the filesystem has not closed the TOCTOU
    # window it thinks it closed: the OS re-resolves the lexical path at operation
    # time, following whatever reparse points exist THEN. Handing the filesystem the
    # already-canonicalized path is what makes the check load-bearing.
    #
    # Safe for targets that do not exist yet: Get-CanonicalRealPath appends a
    # non-existing tail verbatim to the resolved existing prefix (path-guard.ps1).
    try {
        return (Resolve-SafePath -Path $absPath -AllowedRoots @($script:HomeAbs))
    } catch {
        return $null
    }
}

function Test-ContainedInHome([string]$absPath) {
    # Boolean face of Get-ContainedHomePath, for the scan-time call sites that only
    # need the yes/no. Anything that goes on to TOUCH the path must use the resolved
    # path from Get-ContainedHomePath / Resolve-HomeTarget instead.
    return ($null -ne (Get-ContainedHomePath $absPath))
}

function Read-FileHead([string]$absPath, [int]$maxBytes = 8192) {
    $fs = [System.IO.File]::OpenRead($absPath)
    try {
        $len = [int][Math]::Min([long]$maxBytes, $fs.Length)
        if ($len -le 0) { return '' }
        $buf = New-Object byte[] $len
        $read = $fs.Read($buf, 0, $len)
        return [System.Text.Encoding]::UTF8.GetString($buf, 0, $read)
    } finally {
        $fs.Close()
    }
}

function Test-FileHasMarker([string]$absPath) {
    # Generated-looking candidate signal: the ANCHORED shared parser, never a
    # substring scan. A valid header is not current-byte authorship; location and
    # recorded hashes provide the independent authority for any mutation here.
    #
    # The empty guard is load-bearing, not defensive noise: callers now pass the
    # result of Resolve-HomeTargetForRead, which is $null when the path escapes the
    # home. A $null coerces to '' here, and `Test-Path -LiteralPath ''` THROWS a
    # ParameterBindingValidationException in PowerShell 5.1 -- so without this the
    # gated-read refactor would turn a refused path into a crash. An unresolvable
    # path is simply not a marker-bearing file.
    if ([string]::IsNullOrWhiteSpace($absPath)) { return $false }
    if (-not (Test-Path -LiteralPath $absPath -PathType Leaf)) { return $false }
    try {
        $head = Read-FileHead $absPath 8192
    } catch {
        return $false
    }
    return (Test-SkillMeshProvenance $head)
}

function New-DirectoryFor([string]$absFilePath) {
    # Callers always pass an already-resolved $safe* value; the empty guard keeps a
    # refused ($null) path from reaching Split-Path/Test-Path.
    if ([string]::IsNullOrWhiteSpace($absFilePath)) { return }
    $dir = Split-Path -Parent $absFilePath
    if (-not [string]::IsNullOrWhiteSpace($dir) -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

function Resolve-TxPath([string]$relPath) {
    # THE choke point for the transaction directory -- the sibling of
    # Resolve-HomeTarget for everything under <BackupDir>/<migration_id>: payloads,
    # plan.json, backup-manifest.json, journal.jsonl.
    #
    # Gated in ONE place so every caller (prepare, mutate, undo, the resume
    # predicate, the JSON writers) inherits it. On -Resume/-Rollback these paths are
    # read back out of plan.json, which lives in an operator-writable directory and
    # is therefore untrusted input: a tampered or traversal-shaped `backup_payload`
    # would otherwise let a restore read from -- or a backup write to -- any path on
    # the machine.
    if ([string]::IsNullOrWhiteSpace($script:TxDir)) {
        throw 'migrate-legacy-install: internal error -- transaction directory is not set.'
    }
    $abs = Join-Path $script:TxDir ($relPath -replace '/', '\')
    try {
        return (Resolve-SafePath -Path $abs -AllowedRoots @($script:TxDir))
    } catch {
        throw ("migrate-legacy-install: SECURITY -- transaction path '$relPath' resolves outside " +
               "the transaction directory; refusing to read or write it.")
    }
}

function Resolve-TxPayloadPath([string]$payloadRel) {
    # Backup payloads are transaction-directory paths like any other.
    return (Resolve-TxPath $payloadRel)
}

# -- Manifest -----------------------------------------------------------------

function Read-Manifest {
    # @{ skills = <name -> @{status; single_profile; providers = @(slug)}>;
    #    providers = @(slug) }.
    # `providers` is the CLOSED vocabulary, read from the manifest's own top-level
    # object rather than duplicated here, so a provider added in a later phase is
    # honored without editing this tool.
    if (-not (Test-Path -LiteralPath $MANIFEST_PATH -PathType Leaf)) {
        Exit-Blocked 'MANIFEST_UNREADABLE' "manifest not found at $MANIFEST_REL (relative to the skill-mesh checkout)"
    }
    try {
        $raw = [System.IO.File]::ReadAllText($MANIFEST_PATH, [System.Text.Encoding]::UTF8)
        $parsed = $raw | ConvertFrom-Json
    } catch {
        Exit-Blocked 'MANIFEST_UNREADABLE' "$MANIFEST_REL is unparseable ($($_.Exception.GetType().Name))"
    }
    $map = @{}
    foreach ($s in @($parsed.skills)) {
        $name = [string](Get-SkillMeshTxField $s 'name')
        if ([string]::IsNullOrWhiteSpace($name)) { continue }
        $status = [string](Get-SkillMeshTxField $s 'status')
        $coreValue = Get-SkillMeshTxField $s 'core'
        $single = ($status -eq 'provider-native') -or ($null -eq $coreValue)
        $adapters = @()
        $provObj = Get-SkillMeshTxField $s 'providers'
        if ($null -ne $provObj) {
            foreach ($p in @($provObj.PSObject.Properties)) {
                if (-not [string]::IsNullOrWhiteSpace([string]$p.Value)) { $adapters += $p.Name }
            }
        }
        $map[$name] = @{ status = $status; single_profile = $single; adapters = @($adapters) }
    }
    $providers = @()
    $provProp = $parsed.PSObject.Properties['providers']
    if ($null -ne $provProp -and $null -ne $provProp.Value) {
        $providers = @($provProp.Value.PSObject.Properties | ForEach-Object { $_.Name } | Sort-Object)
    }
    if ($providers.Count -eq 0) {
        Exit-Blocked 'MANIFEST_UNREADABLE' "$MANIFEST_REL declares no providers; discovery roots cannot be resolved"
    }
    return @{ skills = $map; providers = @($providers) }
}

function Resolve-KnownProvider([string]$value) {
    # Delegates to the SHARED normalizer in tools/skill-mesh-discovery.ps1 -- one
    # owner for provider-slug resolution across installer, inspector, and migrator.
    return (Resolve-SkillMeshProvider $value $script:KnownProviders)
}

function Get-DirEligibility([string]$name, [bool]$hasSkillMd) {
    # THE classification cascade, identical to inspect-host-install.ps1's
    # Get-RootAnalysis. Absence from the manifest is the SOLE criterion for
    # consumer-only, so a consumer's own skill can never be classified managed and
    # overwritten.
    #
    # `shared-payload` replaces the old `core-holder` verdict (D3). It is NOT a
    # directory-level ownership claim: it says only "this directory holds a mix, so
    # route its files through the PER-FILE rule in Get-RootScan". The twin change in
    # inspect-host-install.ps1's Get-RootAnalysis lands with it -- the two cascades
    # are one contract and a drift between them is exactly what makes a preflight
    # report disagree with what the migrator then does.
    if ($script:ManifestMap.ContainsKey($name)) { return 'managed' }
    if ($name -eq $SHARED_DIR_NAME -and (-not $hasSkillMd)) { return 'shared-payload' }
    if ($hasSkillMd) { return 'consumer-only' }
    return 'foreign'
}

function Test-PathHasUnresolvedReparsePoint([string]$absPath) {
    <#
      Fail closed when an existing component is a reparse point whose target the
      PowerShell 5.1 provider cannot expose. Get-CanonicalRealPath can follow known
      junctions/symlinks; treating an unknown mount/AppExec reparse as an ordinary
      directory would let it manufacture destructive containment authority.
    #>
    try {
        $full = [System.IO.Path]::GetFullPath($absPath)
        $root = [System.IO.Path]::GetPathRoot($full)
        $current = $root
        foreach ($segment in $full.Substring($root.Length).Split(
                [char[]]@('\', '/'),
                [System.StringSplitOptions]::RemoveEmptyEntries)) {
            $current = [System.IO.Path]::Combine($current, $segment)
            if (-not (Test-Path -LiteralPath $current)) { break }
            $item = Get-Item -LiteralPath $current -Force -ErrorAction Stop
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0) {
                continue
            }
            $targetMember = $item | Get-Member -Name Target -ErrorAction SilentlyContinue
            if (-not $targetMember -or $null -eq $item.Target -or
                @($item.Target).Count -eq 0 -or
                [string]::IsNullOrWhiteSpace([string]@($item.Target)[0])) {
                return $true
            }
        }
        return $false
    } catch {
        return $true
    }
}

function Get-SharedInstallRels($providerRoots, [string]$distAbs) {
    # The home-relative paths the SHIPPED shared payload will occupy, as one
    # case-insensitive set for the whole plan.
    #
    # Derived from the DISTRIBUTION's own layout (dist/<p>/_shared/<asset>), never a
    # hand-listed asset roster: a roster here would drift from the builder's
    # re-walked transitive closure and would silently start classifying the wrong
    # consumer files as skill-mesh's.
    #
    # This is the PER-FILE half of D3, computed BEFORE the home scan because the home
    # scan is what needs the answer. A distribution that ships no `_shared` payload
    # yields an empty set, which is exactly the pre-Step-64 behaviour: every
    # `_shared` file in the home stays preserved.
    $set = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($p in @($providerRoots.Keys)) {
        $sharedDir = Join-Path (Join-Path $distAbs $p) $SHARED_DIR_NAME
        if (-not (Test-Path -LiteralPath $sharedDir -PathType Container)) { continue }
        $sharedAbs = [System.IO.Path]::GetFullPath($sharedDir)
        foreach ($f in @(Get-ChildItem -LiteralPath $sharedAbs -Recurse -File)) {
            $leafRel = ($f.FullName.Substring($sharedAbs.Length).TrimStart('\', '/') -replace '\\', '/')
            [void]$set.Add("$($providerRoots[$p])/$SHARED_DIR_NAME/$leafRel")
        }
    }
    return $set
}

function Test-RelUnderSharedPayload([string]$rel) {
    # Does this home-relative path sit inside a `_shared` payload directory? Answered
    # from the PATH alone -- the classification cascade has already run by the time the
    # disclosure loops need this, and re-deriving eligibility here would give the
    # advisory a second opinion that could disagree with the plan it is describing.
    # Ordinal membership (Test-SkillMeshTxMember), like every other closed-vocabulary
    # comparison in this tool.
    if ([string]::IsNullOrWhiteSpace($rel)) { return $false }
    foreach ($seg in @($rel.Split('/'))) {
        if (Test-SkillMeshTxMember $PROFILE_ROOT_DIRS $seg) { return $true }
    }
    return $false
}

function Test-RelAtOrUnderRoot([string]$rel, [string]$rootRel) {
    # Exact home-relative root membership with a segment boundary. A raw prefix
    # check would treat `.copilot/skills-old` as if it were under
    # `.copilot/skills`, incorrectly granting the retired root's destructive
    # privilege to a sibling path.
    if ([string]::IsNullOrWhiteSpace($rel) -or
        [string]::IsNullOrWhiteSpace($rootRel)) { return $false }
    $root = $rootRel.TrimEnd('/')
    return ($rel.Equals($root, [System.StringComparison]::OrdinalIgnoreCase) -or
            $rel.StartsWith("$root/", [System.StringComparison]::OrdinalIgnoreCase))
}

function Test-AbsAtOrUnderRoot([string]$absPath, [string]$absRoot) {
    # Canonical absolute counterpart of Test-RelAtOrUnderRoot. Both arguments are
    # resolved paths already; this helper only applies the exact path boundary.
    if ([string]::IsNullOrWhiteSpace($absPath) -or
        [string]::IsNullOrWhiteSpace($absRoot)) { return $false }
    $path = ([System.IO.Path]::GetFullPath($absPath)).TrimEnd('\', '/')
    $root = ([System.IO.Path]::GetFullPath($absRoot)).TrimEnd('\', '/')
    return ($path.Equals($root, [System.StringComparison]::OrdinalIgnoreCase) -or
            $path.StartsWith($root + [System.IO.Path]::DirectorySeparatorChar,
                [System.StringComparison]::OrdinalIgnoreCase))
}

function Test-ReachableFromActiveDiscovery([string]$safeTarget) {
    <#
      Freshly prove whether any active project discovery path reaches $safeTarget.
      This is intentionally re-evaluated at every destructive boundary. A cached
      tree can become stale between copy and delete (or between two restores), and
      then an alias planted after the first check can redirect the later mutation.

      Any existing active root or entry that cannot be contained, enumerated, or
      canonicalized is uncertainty, so the answer is conservatively true. An absent
      active root remains distinguishable: its contained canonical tail is checked,
      but there is no child tree to enumerate.
    #>
    if ([string]::IsNullOrWhiteSpace($safeTarget)) { return $false }
    try {
        $target = ([System.IO.Path]::GetFullPath($safeTarget)).TrimEnd('\', '/')
        foreach ($rootRel in @(Get-SkillMeshActiveProjectDiscoveryRoots)) {
            $rootLexical = Join-HomePathLexical $rootRel
            if (Test-PathHasUnresolvedReparsePoint $rootLexical) { return $true }
            $rootCanonical = Get-ContainedHomePath $rootLexical
            if ($null -eq $rootCanonical) { return $true }
            if (Test-AbsAtOrUnderRoot $target $rootCanonical) { return $true }
            if (-not (Test-Path -LiteralPath $rootLexical -PathType Container)) {
                continue
            }
            foreach ($entry in @(Get-ChildItem -LiteralPath $rootLexical -Recurse `
                    -Force -ErrorAction Stop)) {
                if (Test-PathHasUnresolvedReparsePoint $entry.FullName) { return $true }
                $canonical = Get-ContainedHomePath $entry.FullName
                if ($null -eq $canonical) { return $true }
                if ($entry.PSIsContainer) {
                    if (Test-AbsAtOrUnderRoot $target $canonical) { return $true }
                } elseif ($target.Equals(
                        ([System.IO.Path]::GetFullPath($canonical)).TrimEnd('\', '/'),
                        [System.StringComparison]::OrdinalIgnoreCase)) {
                    return $true
                }
            }
        }
        return $false
    } catch {
        # Permission, cycle, transient reparse failure, or malformed path cannot
        # prove the target unreachable from an active host discovery tree.
        return $true
    }
}

function Test-SharedFileIsOurs([string]$rel, $sharedInstallRels) {
    # PER-FILE classification inside a `_shared` directory. Two possible yeses, each
    # about THIS file and never about its directory:
    #   * the supplied distribution ships this exact relative path -- it is an
    #     install target, so it is ours to write and (via the ledger) to uninstall;
    #   * the file on disk carries the provenance marker -- it is a generated-looking
    #     candidate. Under the retired root, position independently authorizes its
    #     retirement. Under an active root, it is retained and named by advisory;
    #     content alone never authorizes deletion there.
    # Anything else is consumer-authored and stays PRESERVED: hashed into the backup
    # manifest, precondition-checked, post-install-verified, and named by the
    # rollback drift advisory if it ever changes.
    if ($null -ne $sharedInstallRels -and $sharedInstallRels.Contains($rel)) { return $true }
    return (Test-FileHasMarker (Resolve-HomeTargetForRead $rel))
}

# -- Release identity ---------------------------------------------------------

function Get-GitValue([string[]]$GitArgs) {
    # Release identity is BEST-EFFORT: a checkout without git, or without a tag,
    # records $null rather than failing the migration. The value is only ever an
    # audit record and an equality check between the plan and the backup manifest,
    # so a null on both sides is still a correct comparison.
    # $ErrorActionPreference is function-scoped here: git legitimately writes to
    # stderr (e.g. `describe --exact-match` with no tag) and 'Stop' would turn that
    # into a terminating NativeCommandError.
    $ErrorActionPreference = 'Continue'
    try {
        $all = @('-C', $REPO_ROOT) + @($GitArgs)
        $out = & git @all 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
        $text = ([string](@($out) | Select-Object -First 1)).Trim()
        if ([string]::IsNullOrWhiteSpace($text)) { return $null }
        return $text
    } catch {
        return $null
    }
}

function Get-SourceRelease([string]$distAbs) {
    # commit/tag identify the release candidate; dist_checksums pin the exact bytes
    # the transaction will install. Recorded identically in the plan and in the
    # backup manifest and compared for equality on resume/rollback, so a backup can
    # never be replayed against a different build.
    $commit = Get-GitValue @('rev-parse', 'HEAD')
    if ($null -ne $commit -and $commit -notmatch '\A[0-9a-f]{40}\z') { $commit = $null }
    $tag = Get-GitValue @('describe', '--tags', '--exact-match')
    $checksums = [ordered]@{}
    foreach ($f in @(Get-ChildItem -LiteralPath $distAbs -Recurse -File | Sort-Object -Property FullName)) {
        $rel = ($f.FullName.Substring($distAbs.Length).TrimStart('\', '/') -replace '\\', '/')
        $checksums[$rel] = (Get-SkillMeshFileSha256 $f.FullName)
    }
    return [PSCustomObject]@{
        commit         = $commit
        tag            = $tag
        dist_checksums = [PSCustomObject]$checksums
    }
}

# -- Home scan ----------------------------------------------------------------

function Get-RootScan([string]$rootRel, $sharedInstallRels) {
    # Classify one discovery-root-shaped tree. Returns
    # @{ blocked; preserve; managed_files } where every entry is a home-relative
    # POSIX path. Purely read-only.
    #
    # $sharedInstallRels is the plan-wide set from Get-SharedInstallRels; it is only
    # consulted for files inside a `shared-payload` directory. The RETIRED root is
    # scanned with the same set: none of its paths can match (the set is keyed to the
    # live provider roots), so a `_shared` there is classified on the marker alone --
    # which is the right answer, since a marker-bearing file at the retired target is
    # a superseded copy of ours.
    $result = @{ blocked = @(); preserve = @(); managed_files = @() }
    # Gated resolve FIRST: $null means the root escapes the home, which is a block,
    # not an absence. Only a resolved path is ever handed to Test-Path.
    $rootAbs = Resolve-HomeTargetForRead $rootRel
    if ($null -eq $rootAbs) {
        $result.blocked += New-Block 'UNSAFE_LINK' $rootRel `
            'the discovery root resolves outside the consumer home (junction or symlink escape); refusing to migrate through it'
        return $result
    }
    if (-not (Test-Path -LiteralPath $rootAbs)) { return $result
    }
    if (-not (Test-Path -LiteralPath $rootAbs -PathType Container)) {
        $result.blocked += New-Block 'FOREIGN_FILE' $rootRel `
            'the discovery root path exists but is a FILE, not a directory'
        return $result
    }

    foreach ($child in @(Get-ChildItem -LiteralPath $rootAbs -Force | Sort-Object -Property Name)) {
        $childRel = "$rootRel/$($child.Name)"
        if (-not $child.PSIsContainer) {
            $result.blocked += New-Block 'FOREIGN_FILE' $childRel `
                'a loose file sits directly under the discovery root; skill-mesh only owns per-skill directories'
            continue
        }
        if (-not (Test-ContainedInHome $child.FullName)) {
            $result.blocked += New-Block 'UNSAFE_LINK' $childRel `
                'this directory resolves outside the consumer home (junction or symlink escape)'
            continue
        }
        $hasSkillMd = Test-Path -LiteralPath (Join-Path $child.FullName 'SKILL.md') -PathType Leaf
        $eligibility = Get-DirEligibility $child.Name $hasSkillMd
        if ($eligibility -eq 'foreign') {
            $result.blocked += New-Block 'FOREIGN_FILE' $childRel `
                ('an unknown directory: not a manifest skill, no SKILL.md, and not the _shared payload root. ' +
                 'It is never adopted, overwritten, or deleted -- remove or relocate it, then re-run.')
            continue
        }
        # Directory-level escape check INSIDE a classified tree. Get-ChildItem
        # -Recurse does not DESCEND into a reparse point, so a junction planted a
        # level down is never seen by the per-file loop below -- it would simply
        # vanish from the inventory. Enumerating directories lists the junction
        # itself (one level in), which is where the escape is detectable.
        foreach ($sub in @(Get-ChildItem -LiteralPath $child.FullName -Recurse -Directory -Force -ErrorAction SilentlyContinue |
                Sort-Object -Property FullName)) {
            if (-not (Test-ContainedInHome $sub.FullName)) {
                $result.blocked += New-Block 'UNSAFE_LINK' (ConvertTo-HomeRel $sub.FullName) `
                    'a directory inside this tree resolves outside the consumer home (junction or symlink escape)'
            }
        }
        foreach ($f in @(Get-ChildItem -LiteralPath $child.FullName -Recurse -File -Force |
                Sort-Object -Property FullName)) {
            # Convert the CANONICAL path, not the lexical path used to discover the
            # file. This distinction is destructive-policy authority: a junction
            # below the retired `.copilot/skills` tree may point at a file in an
            # ACTIVE discovery tree. Keeping the lexical `.copilot/...` spelling
            # would falsely grant that active file loop 1's retire privilege.
            $canonicalFile = Get-ContainedHomePath $f.FullName
            if ($null -eq $canonicalFile) {
                $result.blocked += New-Block 'UNSAFE_LINK' "$childRel/..." `
                    'a file inside this directory resolves outside the consumer home'
                continue
            }
            $rel = ConvertTo-HomeRel $canonicalFile
            # PER-FILE, not per-directory (D3). `managed` is a whole-tree verdict --
            # the directory name IS a manifest record -- but `shared-payload` is a
            # mixed tree, so each of its files is asked individually.
            $isOurs = $(if ($eligibility -eq 'managed') {
                $true
            } elseif ($eligibility -eq 'shared-payload') {
                Test-SharedFileIsOurs $rel $sharedInstallRels
            } else {
                $false
            })
            if ($isOurs) {
                $result.managed_files += $rel
            } else {
                # consumer-only, and every consumer-authored file inside a
                # shared-payload directory: byte-untouched, recorded by path and hash
                # only, NEVER payload-copied.
                $result.preserve += $rel
            }
        }
    }
    return $result
}

# -- Plan construction --------------------------------------------------------

function New-MigrationPlan([string]$distAbs, [string]$backupAbs, [string]$migrationId) {
    $blocked = @()
    $preserveRels = @()
    $managedRels = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)

    # -- Which providers does this migration bind? --
    $providerRoots = [ordered]@{}
    foreach ($p in $script:KnownProviders) {
        if (-not $DISCOVERY_SUBDIR.ContainsKey($p)) {
            $blocked += New-Block 'UNKNOWN_PROVIDER_ROOT' '' `
                ("the manifest declares provider '$p' but this tool knows no discovery root for it; " +
                 'migrating would leave that profile uninstalled')
            continue
        }
        $providerRoots[$p] = $DISCOVERY_SUBDIR[$p]
    }

    # -- What the shared payload will occupy, resolved BEFORE the home scan --
    # The home scan classifies `_shared` per FILE and needs this answer to do it.
    $sharedInstallRels = Get-SharedInstallRels $providerRoots $distAbs

    # -- Scan the consumer home --
    foreach ($p in @($providerRoots.Keys)) {
        $scan = Get-RootScan $providerRoots[$p] $sharedInstallRels
        $blocked += @($scan.blocked)
        $preserveRels += @($scan.preserve)
        foreach ($r in @($scan.managed_files)) { [void]$managedRels.Add($r) }
    }
    $retiredScan = Get-RootScan $RETIRED_ROOT_REL $sharedInstallRels
    $blocked += @($retiredScan.blocked)
    $preserveRels += @($retiredScan.preserve)
    $retiredManaged = @()
    # One active-tree walk for the whole plan classification. Never carry this
    # This planning check is repeated at precondition and mutation boundaries; no
    # planning observation is carried forward as destructive authority.
    foreach ($r in @($retiredScan.managed_files)) {
        # Get-RootScan returns canonical residence. An in-home junction may make a
        # file discoverable through the retired lexical root while it physically
        # resides in an active tree. Such a file has no retired-root positional
        # signal and belongs in loop 2's advisory-only population.
        $canonical = Resolve-HomeTargetForRead $r
        if ((Test-RelAtOrUnderRoot $r $RETIRED_ROOT_REL) -and
            ($null -ne $canonical) -and
            (-not (Test-ReachableFromActiveDiscovery $canonical))) {
            $retiredManaged += $r
        } else {
            [void]$managedRels.Add($r)
        }
    }

    # -- Generated install targets --
    $installs = @()
    $distSkills = @{}      # "<provider>/<skill>" -> $true
    foreach ($p in @($providerRoots.Keys)) {
        $profileDir = Join-Path $distAbs $p
        if (-not (Test-Path -LiteralPath $profileDir -PathType Container)) { continue }
        $profileAbs = [System.IO.Path]::GetFullPath($profileDir)
        foreach ($f in @(Get-ChildItem -LiteralPath $profileAbs -Recurse -File | Sort-Object -Property FullName)) {
            $relFromProfile = ($f.FullName.Substring($profileAbs.Length).TrimStart('\', '/') -replace '\\', '/')
            $skill = @($relFromProfile.Split('/'))[0]
            # FIRST-SEGMENT ALLOWLIST. A built profile root holds per-skill
            # directories AND the shared support payload the builder emits beside them
            # (dist/<p>/_shared/<asset>). The payload is not a manifest record, so
            # without the allowlist the FOREIGN_FILE stop below fires on skill-mesh's
            # OWN generated bytes and the whole migration blocks. The list is closed:
            # an unmanifested SKILL directory still blocks, which is the check this
            # branch exists for.
            $isProfileRootAsset = (Test-SkillMeshTxMember $PROFILE_ROOT_DIRS $skill)
            if (-not $isProfileRootAsset -and -not $script:ManifestMap.ContainsKey($skill)) {
                $blocked += New-Block 'FOREIGN_FILE' "$p/$relFromProfile" `
                    ("the supplied distribution contains skill directory '$skill', which is not a record in " +
                     "$MANIFEST_REL; refusing to install an unmanifested tree")
                continue
            }
            # Only real skills participate in the both-profile completeness check;
            # the payload has no adapter declaration to be complete against.
            if (-not $isProfileRootAsset) { $distSkills["$p/$skill"] = $true }
            $targetRel = "$($providerRoots[$p])/$relFromProfile"
            $targetAbs = Resolve-HomeTargetForRead $targetRel
            if ($null -eq $targetAbs) {
                $blocked += New-Block 'UNSAFE_LINK' $targetRel `
                    'the install target resolves outside the consumer home (junction or symlink escape)'
                continue
            }
            $installs += [PSCustomObject]@{
                provider  = $p
                skill     = $skill
                rel_path  = $targetRel
                source    = $f.FullName
                pre_hash  = (Get-SkillMeshFileSha256 $targetAbs)
                post_hash = (Get-SkillMeshFileSha256 $f.FullName)
            }
        }
    }

    # -- Both-profile completeness. A skill the manifest gives an adapter for MUST
    # be present in that provider's profile. A provider-native skill (core: null)
    # declares no gpt adapter, so its absence from the GPT profile can never fire
    # here -- that is the carve-out, expressed as a manifest fact rather than a
    # special case.
    $seenSkills = @($installs | ForEach-Object { $_.skill } | Sort-Object -Unique)
    foreach ($skill in $seenSkills) {
        # A profile-root asset (`_shared`) is not a manifest record, so it has no
        # adapter declaration and no both-profile obligation. Under
        # Set-StrictMode -Version Latest, $script:ManifestMap['_shared'] is $null and
        # reading .adapters off it THROWS PropertyNotFoundException -- a latent crash
        # that only became REACHABLE when the first-segment allowlist above stopped
        # `continue`-ing past the payload, which is why it never fired before.
        if (-not $script:ManifestMap.ContainsKey($skill)) { continue }
        foreach ($p in @($providerRoots.Keys)) {
            if (-not (Test-SkillMeshTxMember @($script:ManifestMap[$skill].adapters) $p)) { continue }
            if (-not $distSkills.ContainsKey("$p/$skill")) {
                $blocked += New-Block 'MISSING_PROFILE' "$p/$skill" `
                    ("the manifest declares a '$p' adapter for skill '$skill' but the supplied distribution " +
                     "has no $p profile for it; both profiles must migrate as one transaction")
            }
        }
    }

    # -- Collision guard: no relative path may be BOTH preserved and installed. --
    # D3's per-FILE rule makes the two sets disjoint by construction; this is the
    # control that proves it every run instead of trusting the construction.
    #
    # The failure it exists to catch is not a crash. A path in both sets gets a
    # preserve action recording the CONSUMER's bytes and an install action writing
    # skill-mesh's over them, so the rollback drift advisory (Write-PreserveDriftAdvisory)
    # would then name the operator's own untouched path as having "changed outside this
    # transaction" -- a false advisory that invites restoring a stale backup over newer
    # bytes. It misreports; it does not change an exit code (D3), which is exactly why
    # nothing downstream would have caught it.
    $preserveSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($rel in @($preserveRels)) { [void]$preserveSet.Add($rel) }
    foreach ($i in @($installs)) {
        if ($preserveSet.Contains($i.rel_path)) {
            $blocked += New-Block 'PRESERVE_INSTALL_COLLISION' $i.rel_path `
                ('this path is classified BOTH preserved and installed: one action would record the ' +
                 'consumer bytes as untouched while another overwrote them, and the rollback drift ' +
                 'advisory would then read skill-mesh own bytes as consumer drift. Refusing to ' +
                 'migrate a plan whose own action set disagrees about who owns a file.')
        }
    }

    # -- Disclosure: which of the consumer's OWN `_shared` bytes this run adopts. --
    # install-skill-mesh.ps1 REFUSES a marker-less collision outright and makes the
    # operator opt in with -ForceShared -BackupDir. This command adopts such a path by
    # design -- adoption is what a migration IS -- but it must not do so silently, so
    # every marker-less shared-payload target it is about to take over is NAMED in the
    # dry run, before -Apply, together with the payload that puts it back. Advisory
    # only: it changes no status, no exit code, and no blocked finding.
    foreach ($i in @($installs | Where-Object {
                $null -ne $_.pre_hash -and (Test-SkillMeshTxMember $PROFILE_ROOT_DIRS $_.skill) })) {
        if (Test-FileHasMarker (Resolve-HomeTargetForRead $i.rel_path)) { continue }
        $label = Get-SafeRelPathLabel $i.rel_path
        Write-Diag ("ADVISORY -- adopting '$label': it exists WITHOUT the skill-mesh provenance " +
                    "marker, so those are your own bytes at a path this distribution now ships. " +
                    "The pre-image is backed up to $PAYLOAD_DIR/$label and -Rollback restores it " +
                    "byte-for-byte. Files in that directory the distribution does NOT ship are " +
                    "preserved untouched.")
    }

    # -- Retire set: marker-bearing files under the RETIRED root only. --
    $installRels = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($i in $installs) { [void]$installRels.Add($i.rel_path) }

    $retires = @()
    $activeManagedRetained = @()
    foreach ($rel in @($retiredManaged)) {
        # Defence in depth: even if a future scan regression feeds a canonical
        # active path into this collection, loop 1 still cannot delete it.
        if (-not (Test-RelAtOrUnderRoot $rel $RETIRED_ROOT_REL)) {
            [void]$managedRels.Add($rel)
            continue
        }
        # The retired .copilot/skills target: every marker-bearing file there is a
        # pre-retarget install Copilot cannot see. A NON-marker file is operator
        # content and is left strictly alone.
        if (Test-FileHasMarker (Resolve-HomeTargetForRead $rel)) { $retires += $rel }
    }
    foreach ($rel in @($managedRels)) {
        if ($installRels.Contains($rel)) { continue }
        # LOOP 2 HAS NO DESTRUCTIVE PRIVILEGE. In an ACTIVE discovery root the only
        # available signal is file content, and a consumer can quote, preserve, or
        # forge that content exactly. It may identify a stale candidate for the
        # operator, but it can never prove that deletion is authorized.
        if (Test-FileHasMarker (Resolve-HomeTargetForRead $rel)) {
            $activeManagedRetained += $rel
        }
    }
    $retires = @($retires | Sort-Object -Unique)

    # -- Disclosure for loop-2 candidates retained in ACTIVE roots. --
    # Named, path-specific, advisory only: no action, status, exit-code, backup, or
    # live bytes change. The operator may remove a path manually after establishing
    # ownership; this tool will not infer that authority from forgeable content.
    $activeManagedRetained = @($activeManagedRetained | Sort-Object -Unique)
    foreach ($rel in $activeManagedRetained) {
        $label = Get-SafeRelPathLabel $rel
        Write-Diag ("ADVISORY [$ACTIVE_MANAGED_RETAIN_ADVISORY] -- retaining '$label': " +
                    "the path is inside an active managed discovery root, carries the " +
                    "skill-mesh provenance marker, and is not shipped by this " +
                    "distribution. It was left untouched because content provenance " +
                    "alone cannot safely authorize deletion. Inspect it and remove it " +
                    "manually only after confirming it is superseded skill-mesh output.")
    }

    # -- Disclosure, loop-1 retire side. The twin of the adoption disclosure above. --
    # A retire DELETES from the live location. Loop 1 retains that privilege because
    # residence under the retired `.copilot/skills` root is an independent positional
    # signal: no current profile installs there and no host reads it. Every `_shared`
    # path retired there is still named before -Apply, together with the payload that
    # puts it back. Advisory only: no status, exit code, or blocked finding.
    foreach ($rel in @($retires | Where-Object { Test-RelUnderSharedPayload $_ })) {
        $label = Get-SafeRelPathLabel $rel
        Write-Diag ("ADVISORY -- retiring '$label': it carries the skill-mesh provenance " +
                    "marker but no profile of this distribution ships that path, so it is " +
                    "read as a superseded skill-mesh asset and REMOVED from the live " +
                    "location. Its directory also holds consumer-authored files, which stay " +
                    "untouched. The pre-image is backed up to $PAYLOAD_DIR/$label and " +
                    "-Rollback restores it byte-for-byte. If those are YOUR bytes, stop here " +
                    "and move the file out of that directory before running -Apply.")
    }

    # -- Ledger rewrite --
    $ledgerRel = $LEDGER_NAME
    $ledgerAbs = Resolve-HomeTargetForRead $ledgerRel
    $createdDirs = Get-CreatedDirs $installs
    $ledgerJson = New-LedgerJson $installs $providerRoots $createdDirs (Get-PriorCreatedDirs $ledgerAbs)
    $ledgerPostHash = Get-SkillMeshStringSha256 $ledgerJson
    $providerRootsObj = [PSCustomObject]@{}
    foreach ($provider in @($providerRoots.Keys | Sort-Object)) {
        $providerRootsObj | Add-Member -NotePropertyName $provider `
            -NotePropertyValue ([string]$providerRoots[$provider]) -Force
    }

    # -- Assemble the ordered action set.
    # backup -> preserve -> retire -> install -> ledger. The ledger is
    # LAST-sequenced so reverse-order rollback reverts it FIRST: no window ever
    # leaves a new ledger indexing already-reverted files.
    $actions = @()
    $seq = 0

    # backup: the pre-image of every overwriting install, plus the prior ledger.
    # A retire produces its own payload during the move, so it needs no separate
    # backup action; both kinds are recorded in BackupManifest.original_files.
    foreach ($i in @($installs | Where-Object { $null -ne $_.pre_hash })) {
        $actions += [PSCustomObject]@{
            seq = $seq; action = 'backup'; rel_path = $i.rel_path; provider = $i.provider
            eligibility = 'managed'; pre_hash = $i.pre_hash; post_hash = $i.pre_hash
            source = ''; backup_payload = "$PAYLOAD_DIR/$($i.rel_path)"
        }
        $seq++
    }
    $ledgerPreHash = Get-SkillMeshFileSha256 $ledgerAbs
    if ($null -ne $ledgerPreHash) {
        $actions += [PSCustomObject]@{
            seq = $seq; action = 'backup'; rel_path = $ledgerRel; provider = ''
            eligibility = 'managed'; pre_hash = $ledgerPreHash; post_hash = $ledgerPreHash
            source = ''; backup_payload = "$PAYLOAD_DIR/$ledgerRel"
        }
        $seq++
    }

    foreach ($rel in @($preserveRels | Sort-Object -Unique)) {
        $h = Get-HomeRelHash $rel
        $actions += [PSCustomObject]@{
            seq = $seq; action = 'preserve'; rel_path = $rel; provider = ''
            eligibility = 'preserved'; pre_hash = $h; post_hash = $h
            source = ''; backup_payload = ''
        }
        $seq++
    }

    foreach ($rel in @($retires)) {
        $actions += [PSCustomObject]@{
            seq = $seq; action = 'retire'; rel_path = $rel; provider = ''
            eligibility = 'managed'; pre_hash = (Get-HomeRelHash $rel)
            post_hash = $null; source = ''; backup_payload = "$PAYLOAD_DIR/$rel"
        }
        $seq++
    }

    foreach ($i in $installs) {
        $actions += [PSCustomObject]@{
            seq = $seq; action = 'install'; rel_path = $i.rel_path; provider = $i.provider
            eligibility = 'managed'; pre_hash = $i.pre_hash; post_hash = $i.post_hash
            source = $i.source
            backup_payload = $(if ($null -ne $i.pre_hash) { "$PAYLOAD_DIR/$($i.rel_path)" } else { '' })
        }
        $seq++
    }

    $actions += [PSCustomObject]@{
        seq = $seq; action = 'ledger'; rel_path = $ledgerRel; provider = ''
        eligibility = 'managed'; pre_hash = $ledgerPreHash; post_hash = $ledgerPostHash
        source = ''; backup_payload = $(if ($null -ne $ledgerPreHash) { "$PAYLOAD_DIR/$ledgerRel" } else { '' })
    }

    return [PSCustomObject]@{
        schema_version = $SCHEMA_VERSION
        root_encoding  = $ROOT_ENCODING
        migration_id   = $migrationId
        source_release = (Get-SourceRelease $distAbs)
        consumer_home  = $script:HomeAbs
        backup_dir     = $backupAbs
        provider_roots = $providerRootsObj
        created_dirs   = @($createdDirs)
        ledger_json    = $ledgerJson
        actions        = @($actions)
        blocked        = @($blocked | Sort-Object -Property code, rel_path)
    }
}

function Get-SkillMeshStringSha256([string]$text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $sha.ComputeHash($UTF8_NO_BOM.GetBytes($text))
    } finally {
        $sha.Dispose()
    }
    return ([System.BitConverter]::ToString($bytes) -replace '-', '').ToLowerInvariant()
}

function Get-CreatedDirs($installs) {
    # ONLY-OWN-WHAT-YOU-CREATE: a directory is recorded only when it does not
    # already exist at plan time, so an operator-owned .claude/ or .github/ is
    # never adopted (and therefore never listed for later uninstall/dir cleanup).
    $set = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($i in @($installs)) {
        $segments = @($i.rel_path.Split('/'))
        $current = ''
        for ($k = 0; $k -lt $segments.Count - 1; $k++) {
            $current = $(if ($current -eq '') { $segments[$k] } else { "$current/$($segments[$k])" })
            # Read side of the choke point, not the lexical joiner: a junction on an
            # ancestor would otherwise make this existence probe answer about a
            # directory OUTSIDE the home, and the answer decides what the ownership
            # ledger claims to have created (and may later delete). A path that
            # resolves outside is $null here, which is correctly "not present" --
            # this run did not create it, so it is never recorded as ours.
            $probe = Resolve-HomeTargetForRead $current
            if ($null -ne $probe -and -not (Test-Path -LiteralPath $probe)) { [void]$set.Add($current) }
        }
    }
    return , @(@($set) | Sort-Object)
}

function Get-PriorCreatedDirs([string]$ledgerAbs) {
    # provider -> the created_dirs the PRIOR ledger already claimed. Read
    # defensively: a corrupt or old-shape ledger yields an empty map, never a throw.
    $map = @{}
    $parsed = Read-JsonFile $ledgerAbs
    if ($null -eq $parsed) { return $map }
    $installs = Get-SkillMeshTxField $parsed 'installs'
    if ($null -eq $installs -or -not ($installs -is [System.Management.Automation.PSCustomObject])) {
        return $map
    }
    if ([string](Get-SkillMeshTxField $parsed 'ledger_version') -ne [string]$LEDGER_VERSION) {
        return $map
    }
    foreach ($p in @($installs.PSObject.Properties)) {
        $slug = Resolve-KnownProvider $p.Name
        if ($null -eq $slug) { continue }
        $subdir = [string]$DISCOVERY_SUBDIR[$slug]
        $valid = New-Object 'System.Collections.Generic.HashSet[string]' `
            ([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($rawDir in @(Get-SkillMeshTxField $p.Value 'created_dirs' @())) {
            if (-not ($rawDir -is [string])) { continue }
            $dir = [string]$rawDir
            # Historical installer ledgers may contain exact '.' for the home
            # root. It is retained as an audit sentinel only; neither migrator nor
            # repaired installer removes directories. Every other retained entry
            # must be a normalized provider-root ancestor/descendant.
            if ($dir -ceq '.') {
                [void]$valid.Add($dir)
                continue
            }
            if (-not (Test-RecoveryRelPath $dir)) { continue }
            if ((Test-RelAtOrUnderRoot $dir $subdir) -or
                (Test-RelAtOrUnderRoot $subdir $dir)) {
                [void]$valid.Add($dir)
            }
        }
        $map[$slug] = @(@($valid) | Sort-Object)
    }
    return $map
}

function New-LedgerJson($installs, $providerRoots, $createdDirs, $priorCreatedDirs) {
    # The rewritten ownership ledger. It indexes ONLY the files this migration
    # INSTALLED, which scopes the set the installer uninstall examines.
    #
    # REWRITTEN FOR D3. The old contract read "no _shared core-holder ever appears
    # here" and that is no longer true, deliberately: the distribution now ships a
    # shared payload at the profile root, so `<root>/_shared/<asset>` IS an install
    # target and MUST be indexed -- an unindexed payload file is an orphan that
    # uninstall cannot remove. What still never appears here is any PRESERVED path:
    # no consumer-only skill, and no file inside a `_shared` directory that this
    # distribution does not ship. The distinction is per FILE, made once in
    # Get-RootScan, and the ledger simply reflects the install set it produced.
    #
    # The uninstall side needs no `_shared` special case: Remove-OwnedFiles in
    # install-skill-mesh.ps1 considers a ledger-listed path only when its current
    # bytes carry the provenance marker, so marker-less or non-ledger-listed consumer
    # files remain outside that operation. Those signals provide path scope plus
    # marker presence, not current-byte identity: a consumer customization retaining
    # a valid header at a listed path passes both. The Step 65 decision therefore
    # blocks live work on the separate installed-hash/current-byte repair across
    # overwrite, stale removal, uninstall, and corrupt-ledger fallback.
    #
    # Step 4 adds the current-byte authority the installer needs: every owned path
    # is paired with the exact post_hash of the install action that wrote it. The
    # key set is deliberately a bijection with owned_files -- missing or extra
    # entries would make the ledger ambiguous and must never be emitted. Keep the
    # ledger version at 1 for the additive field; old readers ignore it, while the
    # repaired installer treats an old/hashless entry as carrying no destructive
    # authority.
    #
    # Shape and serialization are byte-compatible with install-skill-mesh.ps1's
    # writer, so its uninstall path reads this ledger unchanged. Providers, owned
    # paths, and hash-map properties are inserted in sorted order so the same plan
    # produces byte-identical ledger JSON across Apply and Resume.
    $installsObj = [PSCustomObject]@{}
    foreach ($p in @($providerRoots.Keys | Sort-Object)) {
        $subdir = $providerRoots[$p]
        $providerInstalls = @($installs | Where-Object { $_.provider -eq $p } |
            Sort-Object -Property rel_path)
        $owned = @(@($providerInstalls | ForEach-Object { $_.rel_path }) |
            Sort-Object -Unique)
        $ownedHashes = [PSCustomObject]@{}
        foreach ($rel in $owned) {
            $matching = @($providerInstalls | Where-Object { $_.rel_path -ceq $rel })
            if ($matching.Count -ne 1 -or
                [string]::IsNullOrWhiteSpace([string]$matching[0].post_hash)) {
                throw ("migrate-legacy-install: internal error -- owned path '$rel' " +
                       "does not have exactly one recorded install post_hash.")
            }
            $ownedHashes | Add-Member -NotePropertyName $rel `
                -NotePropertyValue ([string]$matching[0].post_hash) -Force
        }
        $mine = @($createdDirs | Where-Object {
            $_ -eq $subdir -or $_.StartsWith("$subdir/") -or $subdir.StartsWith("$_/") })
        # UNIONED with the prior entry, exactly as install-skill-mesh.ps1 does, so a
        # RERUN produces a byte-identical ledger: the second run creates none of the
        # directories the first one did, and without the union its created_dirs
        # would silently shrink to empty (idempotency broken, and a later
        # later uninstall would leave the dirs it made behind).
        $prior = @()
        if ($null -ne $priorCreatedDirs -and $priorCreatedDirs.ContainsKey($p)) {
            $prior = @($priorCreatedDirs[$p])
        }
        $dirs = @(@($mine + $prior) | Sort-Object -Unique)
        $entry = [PSCustomObject]@{
            provider         = $p
            discovery_subdir = $subdir
            owned_files      = @($owned)
            owned_file_hashes = $ownedHashes
            created_dirs     = @($dirs)
        }
        $installsObj | Add-Member -NotePropertyName $p -NotePropertyValue $entry -Force
    }
    $ledger = [PSCustomObject]@{
        tool           = 'skill-mesh'
        ledger_version = $LEDGER_VERSION
        installs       = $installsObj
    }
    return ($ledger | ConvertTo-Json -Depth 8)
}

# -- Backup manifest ----------------------------------------------------------

function New-BackupManifest($plan) {
    $originals = @()
    foreach ($a in @($plan.actions)) {
        if ($a.action -ne 'retire' -and -not ($a.action -eq 'install' -and $null -ne $a.pre_hash)) { continue }
        $abs = Resolve-HomeTargetForRead $a.rel_path
        $size = 0
        # $abs is $null when the path resolves outside the home (a junction planted
        # since the scan). PS 5.1 coerces $null to '' for -LiteralPath and THROWS,
        # which would surface a raw ParameterBindingValidationException and exit 1,
        # preempting this tool's own PRECONDITION_DRIFT / exit-2 handling. Size 0 is
        # the honest answer: there is no readable original inside the home.
        if ($null -ne $abs -and (Test-Path -LiteralPath $abs -PathType Leaf)) {
            $size = (Get-Item -LiteralPath $abs -Force).Length
        }
        $originals += [PSCustomObject]@{
            rel_path       = $a.rel_path
            size           = $size
            sha256         = $a.pre_hash
            backup_payload = $a.backup_payload
        }
    }
    $preserved = @()
    foreach ($a in @($plan.actions | Where-Object { $_.action -eq 'preserve' })) {
        # Path + hash ONLY. Copying a byte-untouched consumer tree would duplicate
        # private content into a backup that can never need to restore it.
        $preserved += [PSCustomObject]@{ rel_path = $a.rel_path; sha256 = $a.pre_hash }
    }
    $installed = @()
    foreach ($a in @($plan.actions | Where-Object { $_.action -eq 'install' })) {
        $installed += [PSCustomObject]@{ rel_path = $a.rel_path; sha256 = $a.post_hash }
    }
    $ledgerAction = @($plan.actions | Where-Object { $_.action -eq 'ledger' })[0]
    $originalLedger = $null
    if ($null -ne $ledgerAction.pre_hash) {
        $originalLedger = [PSCustomObject]@{
            backup_payload = $ledgerAction.backup_payload
            sha256         = $ledgerAction.pre_hash
        }
    }
    return [PSCustomObject]@{
        schema_version = $SCHEMA_VERSION
        root_encoding  = $ROOT_ENCODING
        migration_id   = $plan.migration_id
        created_utc    = (Get-SkillMeshTxUtcNow)
        source_release = $plan.source_release
        consumer_home  = $plan.consumer_home
        backup_dir     = $plan.backup_dir
        original_files = @($originals)
        preserved_files = @($preserved)
        original_ledger = $originalLedger
        installed_files = @($installed)
        status         = 'prepared'
    }
}

function Write-TxJsonFile([string]$txRelName, $object) {
    # Takes a TRANSACTION-RELATIVE name and resolves it through Resolve-TxPath, so
    # a JSON writer cannot be handed a lexically-built absolute that escapes the
    # transaction directory. Atomic (temp + rename), as before.
    $safeTarget = Resolve-TxPath $txRelName
    New-DirectoryFor $safeTarget
    $json = ($object | ConvertTo-Json -Depth 12)
    $safeTmp = "$safeTarget.$PID.$([Guid]::NewGuid().ToString('N')).tmp"
    try {
        $stream = New-Object System.IO.FileStream(
            $safeTmp, [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        try {
            $bytes = $UTF8_NO_BOM.GetBytes($json)
            $stream.Write($bytes, 0, $bytes.Length)
            $stream.Flush()
        } finally {
            $stream.Dispose()
        }
        Move-Item -LiteralPath $safeTmp -Destination $safeTarget -Force
    } finally {
        if (Test-Path -LiteralPath $safeTmp -PathType Leaf) {
            Remove-Item -LiteralPath $safeTmp -Force
        }
    }
}

function Read-JsonFile([string]$absPath) {
    # Same empty guard as Test-FileHasMarker: a gated read can hand us $null, and
    # `Test-Path -LiteralPath ''` throws rather than returning false.
    if ([string]::IsNullOrWhiteSpace($absPath)) { return $null }
    if (-not (Test-Path -LiteralPath $absPath -PathType Leaf)) { return $null }
    try {
        return ([System.IO.File]::ReadAllText($absPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json)
    } catch {
        return $null
    }
}

# -- Transaction action handlers ----------------------------------------------

function Get-ActionTargetAbs($action) {
    # Gated READ resolve. $null when the path escapes the home, so a redirected
    # read yields no content rather than silently reading a file outside it.
    # EVERY write or delete goes through Assert-SafeActionTarget instead.
    return (Resolve-HomeTargetForRead $action.rel_path)
}

function Assert-SafeActionTarget($action, [string]$operation) {
    # Thin adapter: an action carries its target as a home-relative path, so the
    # gate is THE choke point (Resolve-HomeTarget) applied to that rel_path. It
    # exists only so call sites read naturally and holds no logic of its own --
    # which is the point: there is exactly ONE containment implementation.
    return (Resolve-HomeTarget -RelPosix $action.rel_path -Operation $operation)
}

function Assert-RetiredTargetDomain([string]$relPath, [string]$safePath) {
    <#
      THE MUTATION-TIME POSITIONAL-AUTHORITY GUARD for retire actions.

      Loop 1 may delete only because the file physically resides under the retired
      `.copilot/skills` root. Home containment alone is weaker: after planning or a
      crash, an in-home junction can redirect that lexical path into an ACTIVE
      discovery tree, possibly onto bytes with the same hash. Hash preconditions
      then pass while deletion targets the wrong authority domain.

      Require both the recorded spelling and the freshly resolved canonical target
      to be under the retired root, with exact segment boundaries. Call this beside
      every retire copy/delete/restore and from the resume skip predicate.
    #>
    if (-not (Test-RelAtOrUnderRoot $relPath $RETIRED_ROOT_REL)) {
        throw ("migrate-legacy-install: SECURITY -- refusing retire operation for " +
               "'$(Get-SafeRelPathLabel $relPath)': the recorded path is outside the " +
               "retired root '$RETIRED_ROOT_REL'.")
    }
    if ([string]::IsNullOrWhiteSpace($safePath)) {
        throw ("migrate-legacy-install: SECURITY -- refusing retire operation for " +
               "'$(Get-SafeRelPathLabel $relPath)': its target cannot be resolved " +
               "inside the retired root.")
    }
    $canonicalRel = ConvertTo-HomeRel $safePath
    if (-not (Test-RelAtOrUnderRoot $canonicalRel $RETIRED_ROOT_REL)) {
        throw ("migrate-legacy-install: SECURITY -- refusing retire operation for " +
               "'$(Get-SafeRelPathLabel $relPath)': it now resolves to " +
               "'$(Get-SafeRelPathLabel $canonicalRel)', outside the retired root. " +
               "An in-home junction or symlink cannot confer deletion authority.")
    }
    if (Test-ReachableFromActiveDiscovery $safePath) {
        throw ("migrate-legacy-install: SECURITY -- refusing retire operation for " +
               "'$(Get-SafeRelPathLabel $relPath)': an active host discovery path " +
               "currently resolves to this retired target. Host reachability removes " +
               "the retired root's positional deletion authority.")
    }
}

function Assert-RetireRestoreDomain([string]$relPath, [string]$safePath) {
    <#
      Current Step-65 retire actions keep the full retired-domain check during
      rollback. Older schema-v1 plans may instead name an active-root path; those
      actions are restorative-only, but containment alone is not enough because a
      newly planted in-home junction could redirect the restore to a different
      path. For that narrow compatibility case, require the freshly canonicalized
      home-relative spelling to remain exactly the recorded spelling.
    #>
    if (Test-RelAtOrUnderRoot $relPath $RETIRED_ROOT_REL) {
        Assert-RetiredTargetDomain $relPath $safePath
        return
    }
    if ([string]::IsNullOrWhiteSpace($safePath)) {
        throw ("migrate-legacy-install: SECURITY -- refusing legacy retire restore for " +
               "'$(Get-SafeRelPathLabel $relPath)': its target cannot be resolved safely.")
    }
    $canonicalRel = ConvertTo-HomeRel $safePath
    if (-not $canonicalRel.Equals($relPath,
            [System.StringComparison]::OrdinalIgnoreCase)) {
        throw ("migrate-legacy-install: SECURITY -- refusing legacy retire restore for " +
               "'$(Get-SafeRelPathLabel $relPath)': it now resolves to " +
               "'$(Get-SafeRelPathLabel $canonicalRel)'. A junction or symlink cannot " +
               "redirect a compatibility restore.")
    }
}

function Test-RecordedFileState([string]$safePath, $expectedHash) {
    <#
      The one definition of an action's recorded filesystem state. A null hash
      means TRUE nonexistence, never a directory/non-file/unreadable file. A
      non-null hash requires an existing regular file with exactly those bytes.
      This predicate is shared by resume classification, forward mutation, and
      rollback so those three faces cannot disagree about the same state.
    #>
    if ([string]::IsNullOrWhiteSpace($safePath)) { return $false }
    $exists = Test-Path -LiteralPath $safePath
    if ($null -eq $expectedHash) { return (-not $exists) }
    if (-not $exists -or -not (Test-Path -LiteralPath $safePath -PathType Leaf)) {
        return $false
    }
    return ([string](Get-SkillMeshFileSha256 $safePath) -eq [string]$expectedHash)
}

function Assert-RecordedFileState($action, [string]$safePath, $expectedHash,
        [string]$operation, [string]$stateName) {
    if (Test-RecordedFileState $safePath $expectedHash) { return }
    throw ("migrate-legacy-install: SECURITY -- refusing to $operation " +
           "'$(Get-SafeRelPathLabel $action.rel_path)': that path is NOT in the " +
           "$stateName state recorded by this transaction. A directory, non-file, " +
           "unreadable file, or mismatched hash cannot be treated as absence or " +
           "as bytes this transaction may overwrite.")
}

function Assert-BackupPayloadHash($action, $expectedHash, [string]$operation) {
    if ([string]::IsNullOrWhiteSpace([string]$action.backup_payload) -or
        $null -eq $expectedHash) {
        throw ("migrate-legacy-install: SECURITY -- refusing to $operation " +
               "'$(Get-SafeRelPathLabel $action.rel_path)': the action has no " +
               "recorded recovery payload identity.")
    }
    $safePayload = Resolve-TxPayloadPath $action.backup_payload
    if (-not (Test-RecordedFileState $safePayload $expectedHash)) {
        throw ("migrate-legacy-install: SECURITY -- refusing to $operation " +
               "'$(Get-SafeRelPathLabel $action.rel_path)': its backup payload is " +
               "missing, not a file, or does not match the recorded pre-image hash.")
    }
    return $safePayload
}

function Assert-InstallSource($action) {
    $source = [string](Get-SkillMeshTxField $action 'source')
    if ([string]::IsNullOrWhiteSpace($source) -or
        -not (Test-RecordedFileState $source $action.post_hash)) {
        throw ("migrate-legacy-install: SECURITY -- refusing to install " +
               "'$(Get-SafeRelPathLabel $action.rel_path)': the distribution source " +
               "is missing, not a file, or no longer matches the release hash in " +
               "the recorded plan.")
    }
    return $source
}

function Assert-InstallTargetAdoptable($action, [string]$safeTarget) {
    <#
      THE PRE-IMAGE IDENTITY GUARD on the install path -- the counterpart of
      install-skill-mesh.ps1's foreign-collision refusal (the `$foreign` pre-scan in
      Invoke-Install, gated on Test-FileHasMarker) and its TOCTOU recheck inside the
      copy loop, neither of which this tool had. Cited by NAME, not by line range:
      every other cross-file reference in these three tools does, so a shift in the
      installer cannot silently point this comment at unrelated code.

      The two commands make DIFFERENT decisions on purpose and this function is where
      that difference is written down. The installer refuses any existing target that
      lacks the provenance marker. This command ADOPTS such a target -- adopting a
      hand-authored legacy tree is the entire reason it exists, and unlike the
      installer it captures the pre-image into an external backup first and can put it
      back with -Rollback.

      What it will NOT do is adopt bytes its own plan never saw. An install action
      planned against an ABSENT target carries pre_hash $null and therefore has NO
      backup action and NO payload, so a consumer file that appears at that path
      between planning and the write would be destroyed with nothing to restore from.
      Same for a target whose bytes changed after the pre-image was captured: the
      payload no longer holds what is actually there.

      So: only a target whose bytes are exactly the recorded pre_hash may proceed.
      The marker is not an identity check: a consumer can retain or reproduce it while
      changing the rest of the file. An already-applied target is handled by
      Test-ActionAlreadyApplied before this mutate path; anything else throws and
      drives the ordered rollback.

      Reached on -Apply and -Resume alike because it lives in the shared mutate path;
      -Resume is the case that matters, since Invoke-Resume performs no
      Test-Preconditions pass.
    #>
    Assert-RecordedFileState $action $safeTarget $action.pre_hash `
        'install over' 'pre-image'
}

function Invoke-ActionMutate($action) {
    switch ($action.action) {
        'preserve' {
            # Audit-only: never mutates, so there is nothing to gate.
            #
            # A preserved path is checked TWICE, and neither check is kind-filtered.
            # The engine's per-action post-hash comparison runs for every action it
            # does not skip -- it branches on hashes, never on action kind -- and a
            # preserve action carries post_hash = pre_hash, so a preserved file edited
            # while the apply loop is still running fails THERE (decision D2 case 3:
            # advisory + rolled_back, never an escalation). Test-PostInstall then
            # re-checks it after the loop commits (D2 case 2).
            #
            # The one gap is a RESUME: an action whose post-state already holds is
            # skipped before the engine's comparison, so for an UNCHANGED preserved
            # path on a resume, post-install verification is the only remaining check.
            return
        }
        'backup' {
            $safePayload = Resolve-TxPayloadPath $action.backup_payload
            if (Test-RecordedFileState $safePayload $action.post_hash) { return }
            if (Test-Path -LiteralPath $safePayload) {
                throw ("migrate-legacy-install: SECURITY -- refusing to replace an " +
                       "unexpected backup payload for '$(Get-SafeRelPathLabel $action.rel_path)'.")
            }
            # The READ side of the copy is gated too: a redirected source would pull
            # a file from outside the home INTO the backup, corrupting the pre-image
            # that rollback depends on.
            $safeSource = Assert-SafeActionTarget $action 'back it up'
            Assert-RecordedFileState $action $safeSource $action.pre_hash `
                'back up' 'pre-image'
            New-DirectoryFor $safePayload
            Copy-Item -LiteralPath $safeSource -Destination $safePayload -Force
            [void](Assert-BackupPayloadHash $action $action.pre_hash 'complete the backup of')
            return
        }
        'retire' {
            # Copy-then-delete, never a bare move: at every instant the bytes exist
            # in at least one place, so a crash between the two is recoverable in
            # either direction. BOTH steps are separate mutation points, so both
            # re-resolve containment immediately before they run.
            $safePayload = Resolve-TxPayloadPath $action.backup_payload
            $payloadMatches = Test-RecordedFileState $safePayload $action.pre_hash
            if (-not $payloadMatches) {
                if (Test-Path -LiteralPath $safePayload) {
                    throw ("migrate-legacy-install: SECURITY -- refusing to retire " +
                           "'$(Get-SafeRelPathLabel $action.rel_path)': its recovery " +
                           "payload path already holds unexpected bytes or a non-file.")
                }
                $safeSource = Assert-SafeActionTarget $action 'retire it'
                Assert-RetiredTargetDomain $action.rel_path $safeSource
                Assert-RecordedFileState $action $safeSource $action.pre_hash `
                    'retire' 'pre-image'
                New-DirectoryFor $safePayload
                Copy-Item -LiteralPath $safeSource -Destination $safePayload -Force
            }
            [void](Assert-BackupPayloadHash $action $action.pre_hash 'retire')
            $safeTarget = Assert-SafeActionTarget $action 'delete it'
            Assert-RetiredTargetDomain $action.rel_path $safeTarget
            Assert-RecordedFileState $action $safeTarget $action.pre_hash `
                'delete' 'pre-image'
            [void](Assert-BackupPayloadHash $action $action.pre_hash 'delete')
            Remove-Item -LiteralPath $safeTarget -Force
            $safeAfter = Resolve-HomeTarget -RelPosix $action.rel_path `
                -Operation 'verify its retired post-state'
            Assert-RecordedFileState $action $safeAfter $action.post_hash `
                'accept the retirement of' 'post-image'
            return
        }
        'install' {
            # Gate BEFORE creating the parent chain and again AFTER, because
            # New-DirectoryFor materializes directories that did not exist at the
            # first check and the leaf write is a second mutation point.
            $safeTargetPreCreate = Assert-SafeActionTarget $action 'install over it'
            New-DirectoryFor $safeTargetPreCreate
            $safeTarget = Assert-SafeActionTarget $action 'install over it'
            # THE PRE-IMAGE IDENTITY GUARD, re-read immediately before the copy. See the
            # .DESCRIPTION note: -Apply's Test-Preconditions closes the wide window
            # but -Resume runs no precondition pass at all, so this is the only check
            # standing between a resumed transaction and a consumer file that
            # appeared at an install target while the transaction was interrupted.
            Assert-InstallTargetAdoptable $action $safeTarget
            if ($null -ne $action.pre_hash) {
                [void](Assert-BackupPayloadHash $action $action.pre_hash 'install over')
            }
            $verifiedSource = Assert-InstallSource $action
            Copy-Item -LiteralPath $verifiedSource -Destination $safeTarget -Force
            Assert-RecordedFileState $action $safeTarget $action.post_hash `
                'accept the installation of' 'post-image'
            return
        }
        'ledger' {
            $safeTargetPreCreate = Assert-SafeActionTarget $action 'rewrite the ledger'
            New-DirectoryFor $safeTargetPreCreate
            $safeTarget = Assert-SafeActionTarget $action 'rewrite the ledger'
            Assert-RecordedFileState $action $safeTarget $action.pre_hash `
                'rewrite' 'pre-image'
            if ($null -ne $action.pre_hash) {
                [void](Assert-BackupPayloadHash $action $action.pre_hash 'rewrite')
            }
            if ((Get-SkillMeshStringSha256 $script:LedgerJson) -ne $action.post_hash) {
                throw "migrate-legacy-install: SECURITY -- recorded ledger content does not match its planned post-image hash."
            }
            $safeTmp = "$safeTarget.$PID.$([Guid]::NewGuid().ToString('N')).tmp"
            try {
                $stream = New-Object System.IO.FileStream(
                    $safeTmp, [System.IO.FileMode]::CreateNew,
                    [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
                try {
                    $bytes = $UTF8_NO_BOM.GetBytes($script:LedgerJson)
                    $stream.Write($bytes, 0, $bytes.Length)
                    $stream.Flush()
                } finally {
                    $stream.Dispose()
                }
                if (-not (Test-RecordedFileState $safeTmp $action.post_hash)) {
                    throw "migrate-legacy-install: SECURITY -- staged ledger bytes failed hash verification."
                }
                $safeTarget = Assert-SafeActionTarget $action 'rewrite the ledger'
                Assert-RecordedFileState $action $safeTarget $action.pre_hash `
                    'rewrite' 'pre-image'
                Move-Item -LiteralPath $safeTmp -Destination $safeTarget -Force
            } finally {
                if (Test-Path -LiteralPath $safeTmp -PathType Leaf) {
                    Remove-Item -LiteralPath $safeTmp -Force
                }
            }
            Assert-RecordedFileState $action $safeTarget $action.post_hash `
                'accept the ledger rewrite of' 'post-image'
            return
        }
    }
    throw "migrate-legacy-install: unknown action kind '$($action.action)'."
}

function Invoke-ActionUndo($action) {
    <#
      EVERY branch obeys the same two rules, and neither is written inline:
        containment   -> Assert-SafeActionTarget (THE choke point)
        byte identity -> Assert-OurBytesAtTarget (THE content-identity rule)
      Both are called on every branch that destroys or overwrites, so a branch
      cannot drift from its siblings the way install-overwrite and ledger did.
    #>
    switch ($action.action) {
        'preserve' { return }
        'backup' { return }
        'retire' {
            $safeTarget = Assert-SafeActionTarget $action 'undo the retirement of'
            # Run the appropriate current/legacy restore-domain guard before even
            # the pre-state no-op. Otherwise an alias to same-hash bytes could
            # falsely certify rollback without restoring the recorded residence.
            Assert-RetireRestoreDomain $action.rel_path $safeTarget
            if (Test-RecordedFileState $safeTarget $action.pre_hash) { return }
            Assert-OurBytesAtTarget $safeTarget $action.post_hash `
                $action.rel_path 'restore over'
            Assert-RecordedFileState $action $safeTarget $action.post_hash `
                'restore over' 'post-image'
            $verifiedPayload = Assert-BackupPayloadHash $action $action.pre_hash `
                'restore retired'
            # Older schema-v1 transactions could retire active-root bytes before
            # Step 65 narrowed the rule. Resume may never delete there, but explicit
            # rollback may restore a verified pre-image only at the same canonical
            # recorded spelling (never through a newly planted alias).
            New-DirectoryFor $safeTarget
            $safeTarget = Assert-SafeActionTarget $action 'restore it'
            Assert-RetireRestoreDomain $action.rel_path $safeTarget
            Assert-RecordedFileState $action $safeTarget $action.post_hash `
                'restore over' 'post-image'
            [void](Assert-BackupPayloadHash $action $action.pre_hash 'restore retired')
            Copy-Item -LiteralPath $verifiedPayload -Destination $safeTarget -Force
            Assert-RecordedFileState $action $safeTarget $action.pre_hash `
                'accept the restore of' 'pre-image'
            return
        }
        'install' {
            $safeTarget = Assert-SafeActionTarget $action 'undo the install of'
            if (Test-RecordedFileState $safeTarget $action.pre_hash) { return }
            Assert-OurBytesAtTarget $safeTarget $action.post_hash `
                $action.rel_path 'undo the install of'
            Assert-RecordedFileState $action $safeTarget $action.post_hash `
                'undo the install of' 'post-image'
            if ($null -eq $action.pre_hash) {
                Remove-Item -LiteralPath $safeTarget -Force
                Assert-RecordedFileState $action $safeTarget $action.pre_hash `
                    'accept the undo of' 'pre-image'
                return
            }
            $verifiedPayload = Assert-BackupPayloadHash $action $action.pre_hash `
                'restore overwritten'
            New-DirectoryFor $safeTarget
            $safeTarget = Assert-SafeActionTarget $action 'restore it'
            Assert-RecordedFileState $action $safeTarget $action.post_hash `
                'restore over' 'post-image'
            [void](Assert-BackupPayloadHash $action $action.pre_hash 'restore overwritten')
            Copy-Item -LiteralPath $verifiedPayload -Destination $safeTarget -Force
            Assert-RecordedFileState $action $safeTarget $action.pre_hash `
                'accept the restore of' 'pre-image'
            return
        }
        'ledger' {
            $safeTarget = Assert-SafeActionTarget $action 'undo the ledger rewrite of'
            if (Test-RecordedFileState $safeTarget $action.pre_hash) { return }
            Assert-OurBytesAtTarget $safeTarget $action.post_hash `
                $action.rel_path 'undo the ledger rewrite of'
            Assert-RecordedFileState $action $safeTarget $action.post_hash `
                'undo the ledger rewrite of' 'post-image'
            if ($null -eq $action.pre_hash) {
                Remove-Item -LiteralPath $safeTarget -Force
                Assert-RecordedFileState $action $safeTarget $action.pre_hash `
                    'accept the undo of' 'pre-image'
                return
            }
            $verifiedPayload = Assert-BackupPayloadHash $action $action.pre_hash `
                'restore the prior ledger for'
            $safeTarget = Assert-SafeActionTarget $action 'restore the prior ledger'
            Assert-RecordedFileState $action $safeTarget $action.post_hash `
                'restore over' 'post-image'
            [void](Assert-BackupPayloadHash $action $action.pre_hash 'restore the prior ledger for')
            Copy-Item -LiteralPath $verifiedPayload -Destination $safeTarget -Force
            Assert-RecordedFileState $action $safeTarget $action.pre_hash `
                'accept the restore of' 'pre-image'
            return
        }
    }
    throw "migrate-legacy-install: unknown action kind '$($action.action)'."
}

function Test-ActionAlreadyApplied($action) {
    # Resume predicate: does this action's POST-state already hold on disk? The
    # answer is read from the filesystem, never from the journal, so a crash
    # between a mutation and its commit flush converges rather than being redone.
    $targetAbs = Get-ActionTargetAbs $action
    switch ($action.action) {
        'preserve' {
            # Preserve drift is deliberately handled by the shared failure path's
            # advisory policy, so it is not a destructive preimage assertion.
            return (Test-RecordedFileState $targetAbs $action.post_hash)
        }
        'backup' {
            $payload = Resolve-TxPayloadPath $action.backup_payload
            if (Test-RecordedFileState $payload $action.post_hash) { return $true }
            if (Test-Path -LiteralPath $payload) {
                throw ("migrate-legacy-install: SECURITY -- backup payload for " +
                       "'$(Get-SafeRelPathLabel $action.rel_path)' changed while the " +
                       "transaction was interrupted.")
            }
            Assert-RecordedFileState $action $targetAbs $action.pre_hash `
                'resume the backup of' 'pre-image'
            return $false
        }
        'retire' {
            # Resume may continue only in one of three fully-decided states:
            # pre/absent (copy then delete), pre/pre (delete), absent/pre (done).
            # Every directory, mismatched file, corrupt payload, or double absence
            # is ambiguous and therefore refused before another begin record.
            Assert-RetiredTargetDomain $action.rel_path $targetAbs
            $payload = Resolve-TxPayloadPath $action.backup_payload
            $targetPre = Test-RecordedFileState $targetAbs $action.pre_hash
            $targetPost = Test-RecordedFileState $targetAbs $action.post_hash
            $payloadPre = Test-RecordedFileState $payload $action.pre_hash
            $payloadAbsent = Test-RecordedFileState $payload $null
            if ($targetPost -and $payloadPre) { return $true }
            if ($targetPre -and ($payloadPre -or $payloadAbsent)) { return $false }
            throw ("migrate-legacy-install: SECURITY -- refusing to resume retirement of " +
                   "'$(Get-SafeRelPathLabel $action.rel_path)': target and recovery " +
                   "payload no longer match an accepted recorded state.")
        }
        'install' {
            if (Test-RecordedFileState $targetAbs $action.post_hash) { return $true }
            Assert-RecordedFileState $action $targetAbs $action.pre_hash `
                'resume installation over' 'pre-image'
            [void](Assert-InstallSource $action)
            if ($null -ne $action.pre_hash) {
                [void](Assert-BackupPayloadHash $action $action.pre_hash `
                    'resume installation over')
            }
            return $false
        }
        'ledger' {
            if (Test-RecordedFileState $targetAbs $action.post_hash) { return $true }
            Assert-RecordedFileState $action $targetAbs $action.pre_hash `
                'resume the ledger rewrite of' 'pre-image'
            if ($null -ne $action.pre_hash) {
                [void](Assert-BackupPayloadHash $action $action.pre_hash `
                    'resume the ledger rewrite of')
            }
            if ((Get-SkillMeshStringSha256 $script:LedgerJson) -ne $action.post_hash) {
                throw "migrate-legacy-install: SECURITY -- recorded ledger content no longer matches the planned post-image."
            }
            return $false
        }
    }
    throw "migrate-legacy-install: unknown action kind '$($action.action)' in resume predicate."
}

# -- Pre-flight ---------------------------------------------------------------

function Test-Preconditions($plan) {
    # Re-validate EVERY action's precondition hash against current on-disk state.
    # Runs in state `prepared`, before the first mutation, so drift since planning
    # aborts as a true no-op.
    # Uniform across every action kind: pre_hash always describes the same thing
    # (the current state of rel_path in the home), so no kind is exempt.
    # This is the post-plan, pre-mutation alias checkpoint. Mutation re-checks again
    # immediately before every destructive retire boundary.
    $drift = @()
    foreach ($a in @($plan.actions)) {
        if ($a.action -eq 'retire') {
            try {
                $safeRetire = Resolve-HomeTarget -RelPosix $a.rel_path -Operation 'validate its retire domain'
                Assert-RetiredTargetDomain $a.rel_path $safeRetire
            } catch {
                $drift += $a.rel_path
                continue
            }
        }
        $safeCurrent = Resolve-HomeTargetForRead $a.rel_path
        if ($null -eq $safeCurrent) {
            $drift += $a.rel_path
            continue
        }
        $exists = Test-Path -LiteralPath $safeCurrent
        $isFile = $exists -and (Test-Path -LiteralPath $safeCurrent -PathType Leaf)
        if ($null -eq $a.pre_hash) {
            if ($exists) { $drift += $a.rel_path }
            continue
        }
        if (-not $isFile) {
            $drift += $a.rel_path
            continue
        }
        $current = Get-SkillMeshFileSha256 $safeCurrent
        if ([string]$current -ne [string]$a.pre_hash) { $drift += $a.rel_path }
    }
    return , @($drift | Sort-Object -Unique)
}

function Test-PostInstall($plan) {
    # Post-install verification: every generated file is present with its expected
    # hash, and every retired path is gone.
    $bad = @()
    foreach ($a in @($plan.actions)) {
        $current = Get-HomeRelHash $a.rel_path
        if ($a.action -eq 'install' -or $a.action -eq 'ledger') {
            if ([string]$current -ne [string]$a.post_hash) { $bad += $a.rel_path }
        } elseif ($a.action -eq 'retire') {
            # A directory hashes to null just like an absent path, but the retire
            # post-state is true absence. Do not certify a replacement directory.
            $safeTarget = Resolve-HomeTargetForRead $a.rel_path
            if ($null -eq $safeTarget -or (Test-Path -LiteralPath $safeTarget)) {
                $bad += $a.rel_path
            }
        } elseif ($a.action -eq 'preserve') {
            if ([string]$current -ne [string]$a.pre_hash) { $bad += $a.rel_path }
        }
    }
    return , @($bad)
}

function Format-HashLabel($hash) {
    # $null is this codebase's "path does not exist" marker (Get-HomeRelHash), and a
    # bare empty string in a diagnostic reads like a bug rather than an absence.
    if ([string]::IsNullOrEmpty([string]$hash)) { return '<absent>' }
    return [string]$hash
}

function Write-PreserveDriftAdvisory($plan) {
    # ADVISORY ONLY. It never changes a status, an exit code, or the blocked set --
    # decision D2 case 3, and the reason the round-4/round-5 oscillation resolved this
    # way rather than by escalating.
    #
    # What `rolled_back` claims is narrow and provable: every byte this tool mutated
    # was restored from backup and every file it created was removed. It does NOT
    # claim the home is byte-identical on paths the tool never touched. A `preserve`
    # action carries no backup payload -- deliberate disclosure minimization, so a
    # byte-untouched consumer tree is never copied into the backup -- which makes the
    # broader claim structurally unprovable and therefore unenforceable. When a
    # preserved path has drifted, the honest move is to NAME it (with hashes, so the
    # operator can tell their own edit from corruption) and leave their bytes alone.
    #
    # Emitted on both rollback paths: the failure-triggered shared path (exit 1) and
    # the explicit -Rollback (exit 0). Neither exit code changes because of it.
    #
    # The per-action try/catch is what makes that last sentence STRUCTURAL rather than
    # aspirational. This runs AFTER the rollback has completed and the manifest is
    # durable, so an advisory that threw would convert a finished exit-0 rollback into
    # an unhandled error (exit 1, and zero JSON emitted under -Format json) over a
    # purely informational line. Two real triggers: Get-HomeRelHash opens the file, so
    # a preserved SKILL.md held by an editor or an AV scanner throws even though
    # Test-Path succeeded; and plan.json comes from an operator-writable directory, so
    # under Set-StrictMode a missing post_hash throws PropertyNotFoundException --
    # which is also why the field is read through Get-SkillMeshTxField here.
    foreach ($a in @(@($plan.actions) | Where-Object { $_.action -eq 'preserve' })) {
        try {
            $expected = Get-SkillMeshTxField $a 'post_hash'
            $observed = Get-HomeRelHash $a.rel_path
            if ([string]$observed -eq [string]$expected) { continue }
            Write-Diag ("ADVISORY -- preserved path '$(Get-SafeRelPathLabel $a.rel_path)' changed outside " +
                        "this transaction (expected $(Format-HashLabel $expected), observed " +
                        "$(Format-HashLabel $observed)). It carries no backup payload by design, so it was " +
                        "left exactly as found and nothing this tool restored depends on it. If that edit " +
                        "was yours, re-run -Apply: planning re-reads the file and converges.")
        } catch {
            # Deliberately swallowed: a diagnostic must never be the reason a completed
            # rollback reports failure. Say that the disclosure itself failed.
            Write-Diag ("ADVISORY UNAVAILABLE -- could not read preserved path " +
                        "'$(Get-SafeRelPathLabel $a.rel_path)' to check it for drift. The rollback " +
                        "itself is unaffected; this line reports only that the check did not run.")
        }
    }
}

# -- Transaction discovery ----------------------------------------------------

function Get-TransactionDirs([string]$backupAbs) {
    if (-not (Test-Path -LiteralPath $backupAbs -PathType Container)) { return , @() }
    return , @(Get-ChildItem -LiteralPath $backupAbs -Directory -Force |
        Where-Object { Test-SkillMeshMigrationId $_.Name } | Sort-Object -Property Name)
}

function Assert-LegacyRolledBackPrestate($plan, $records) {
    <#
      A pre-amendment rolled_back journal has no durable completion record. Its
      conservative compatibility proof is that every durably begun MUTATING
      action still holds its exact recorded pre-state. Current transactions use
      rollback_complete instead, so legitimate edits after rollback remain free.
    #>
    $begun = Get-SkillMeshTxBegunSeqs $records
    foreach ($action in @($plan.actions)) {
        $kind = [string](Get-SkillMeshTxField $action 'action')
        $seq = [int](Get-SkillMeshTxField $action 'seq' -1)
        if (-not $begun.Contains($seq) -or
            -not (Test-SkillMeshTxMember @('retire', 'install', 'ledger') $kind)) {
            continue
        }
        $safeTarget = Resolve-HomeTargetForRead ([string]$action.rel_path)
        if ($null -eq $safeTarget) {
            throw 'rolled-back action target cannot be resolved inside the project root.'
        }
        if (Test-SkillMeshTxMember @('retire') $kind) {
            Assert-RetireRestoreDomain ([string]$action.rel_path) $safeTarget
        }
        if (-not (Test-RecordedFileState $safeTarget $action.pre_hash)) {
            throw 'rolled-back transaction does not hold a recorded mutating pre-state.'
        }
    }
}

function Find-UnresolvedTransaction([string]$backupAbs) {
    # An unresolved transaction is one whose status is NOT applied and NOT
    # rolled_back -- prepared, applying, rolling_back, and the known-mixed
    # failed_incomplete all count. Scoped to THIS consumer home via the
    # transaction's own plan.json.
    # Assigned first, NOT wrapped in @(): Get-TransactionDirs comma-wraps its
    # return (so an empty result stays an array), and @() around such a call
    # produces a one-element array holding the array.
    $txDirs = Get-TransactionDirs $backupAbs
    foreach ($d in $txDirs) {
        $plan = Read-JsonFile (Join-Path $d.FullName $PLAN_FILE)
        if ($null -eq $plan) {
            # With no readable plan there is no safe way to prove this transaction
            # belongs to some other project. Do not layer a new Apply over possibly
            # mixed bytes merely because recovery metadata was damaged.
            return [PSCustomObject]@{ migration_id = $d.Name; status = 'corrupt' }
        }
        # NOT $home: $HOME is a protected PowerShell automatic variable and
        # assigning to it throws VariableNotWritable (the same trap
        # install-skill-mesh.ps1 documents for its -Home parameter).
        $planHome = [string](Get-SkillMeshTxField $plan 'consumer_home')
        $sameHome = $planHome.Equals(
            $script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase)
        if (-not $sameHome) {
            try {
                if (-not (Test-Path -LiteralPath $planHome -PathType Container)) {
                    # An old lexical/junction home that can no longer be resolved is
                    # ambiguous, not evidence that the transaction is unrelated.
                    return [PSCustomObject]@{ migration_id = $d.Name; status = 'corrupt' }
                }
                $canonicalPlanHome = (Get-CanonicalRealPath -InputPath $planHome).TrimEnd('\', '/')
                $sameHome = $canonicalPlanHome.Equals(
                    $script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase)
            } catch {
                return [PSCustomObject]@{ migration_id = $d.Name; status = 'corrupt' }
            }
        }
        if (-not $sameHome) { continue }
        $manifest = Read-JsonFile (Join-Path $d.FullName $BACKUP_MANIFEST_FILE)
        if ($null -eq $manifest) {
            return [PSCustomObject]@{ migration_id = $d.Name; status = 'corrupt' }
        }
        $status = [string](Get-SkillMeshTxField $manifest 'status')
        if (-not (Test-SkillMeshTxMember (Get-SkillMeshTxStates) $status)) {
            return [PSCustomObject]@{ migration_id = $d.Name; status = 'corrupt' }
        }

        # A terminal status is not, by itself, recovery authority. Validate the
        # complete plan/manifest/journal tuple before treating this transaction as
        # resolved; otherwise a missing journal or a relabelled partial transaction
        # could be hidden behind `applied` and a new Apply could layer over it.
        try {
            $planRootEncoding = [string](Get-SkillMeshTxField $plan 'root_encoding')
            $manifestRootEncoding = [string](Get-SkillMeshTxField $manifest 'root_encoding')
            $legacyRootEncoding = ([string]::IsNullOrEmpty($planRootEncoding) -and
                [string]::IsNullOrEmpty($manifestRootEncoding))
            if ($legacyRootEncoding -and
                -not $planHome.Equals(
                    $script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase)) {
                throw 'legacy transaction records an ambiguous project-root alias.'
            }
            $planBySeq = Assert-RecoveryMetadata $plan $manifest $backupAbs $d.Name
            $records = Read-SkillMeshTxJournal `
                (Join-Path $d.FullName $JOURNAL_FILE) `
                -AllowMissing:($status -eq 'prepared')
            Assert-RecoveryJournal $records $planBySeq $d.Name $status `
                -RequireRollbackComplete:($status -eq 'rolled_back' -and
                    -not $legacyRootEncoding)
            if ($status -eq 'rolled_back' -and
                -not (Test-RecoveryJournalHasRollbackComplete $records)) {
                # Pre-amendment journals have no durable rollback-completion record.
                # Their only safe compatibility proof is the conservative historical
                # rule: every begun mutating action must still be at exact pre-state.
                # Current encoded transactions must carry rollback_complete above,
                # which lets legitimate later consumer edits re-plan normally.
                Assert-LegacyRolledBackPrestate $plan $records
            }
        } catch {
            return [PSCustomObject]@{ migration_id = $d.Name; status = 'corrupt' }
        }
        if (-not (Test-SkillMeshTxTerminal $status)) {
            return [PSCustomObject]@{ migration_id = $d.Name; status = $status }
        }
    }
    return $null
}

# -- Reporting ----------------------------------------------------------------

function Write-PlanReport($plan) {
    if ($Format -eq 'json') {
        Write-Output ($plan | ConvertTo-Json -Depth 12)
        return
    }
    $counts = @{}
    foreach ($kind in @(Get-SkillMeshTxActionKinds)) {
        $counts[$kind] = @($plan.actions | Where-Object { $_.action -eq $kind }).Count
    }
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("skill-mesh migration plan (schema_version $SCHEMA_VERSION)")
    $lines.Add("migration_id: $($plan.migration_id)")
    $commit = $(if ($null -ne $plan.source_release.commit) { $plan.source_release.commit } else { '-' })
    $lines.Add("source_release: commit=$commit")
    $lines.Add('')
    $lines.Add('actions:')
    foreach ($kind in @(Get-SkillMeshTxActionKinds)) {
        $lines.Add("  $kind : $($counts[$kind])")
    }
    $lines.Add('')
    $lines.Add("blocked ($(@($plan.blocked).Count)):")
    foreach ($b in @($plan.blocked)) {
        $lines.Add("  [$($b.code)] $($b.rel_path) -- $($b.message)")
    }
    Write-Output ($lines -join [Environment]::NewLine)
}

# -- Modes --------------------------------------------------------------------

function Invoke-DryRun([string]$distAbs, [string]$backupAbs) {
    $plan = New-MigrationPlan $distAbs $backupAbs (New-SkillMeshMigrationId)
    Write-PlanReport $plan
    if (@($plan.blocked).Count -gt 0) {
        Write-Diag "the plan is BLOCKED by $(@($plan.blocked).Count) finding(s); nothing was written."
        exit 2
    }
    exit 0
}

function Invoke-Apply([string]$distAbs, [string]$backupAbs) {
    # A bare -Apply never silently adopts a prior transaction.
    $unresolved = Find-UnresolvedTransaction $backupAbs
    if ($null -ne $unresolved) {
        # The remedy is STATUS-SPECIFIC. `failed_incomplete` is unresolved (the home
        # is known-mixed, so a bare -Apply over it must still refuse) but it is also
        # TERMINAL: -Resume refuses it and -Rollback refuses it, both by design.
        # Printing the generic "resume or roll back" guidance for that status sent
        # the operator round two dead ends before they could discover the real
        # answer, in exactly the rare state where clear instructions matter most.
        if ($unresolved.status -eq 'corrupt') {
            $remedy = ("Its plan or backup manifest is missing, unreadable, or no longer " +
                       "scopable to a different project. Do not delete it until you have " +
                       "inspected the retained payloads and established whether recovery " +
                       "is still required. Repair or quarantine that transaction directory " +
                       "before starting a new Apply.")
        } elseif ($unresolved.status -eq 'failed_incomplete') {
            # `failed_incomplete` has TWO producers and they need different remedies, so
            # this text must not assert either one. (1) An undo genuinely failed and the
            # home IS mixed -- restore from the payloads. (2) D2 case 2: post-install
            # verification failed on a PRESERVED path, where every mutated path was
            # already restored and the only "unrestorable" bytes are the consumer's own.
            # Telling case 2 to recover manually from the backup is exactly the
            # destructive advice D2 removed from the escalation message itself, so the
            # remedy names both and points at the run's own diagnostics to disambiguate.
            $remedy = ("Its rollback did NOT complete, and neither -Resume nor -Rollback will act " +
                       "on it (both refuse a terminal transaction). Check that run's diagnostics: " +
                       "if a path this tool MUTATED could not be restored the home is mixed -- " +
                       "recover MANUALLY from the retained backup payloads under the transaction " +
                       "directory named below. If instead a PRESERVED path changed (it carries no " +
                       "backup payload by design), those bytes are yours and are already intact; " +
                       "nothing needs restoring. Either way, remove that directory to clear this block.")
        } else {
            $remedy = ("Re-run with -Resume -MigrationId $($unresolved.migration_id) to drive it " +
                       "forward, or -Rollback -MigrationId $($unresolved.migration_id) to reverse it.")
        }
        Exit-Blocked 'INCOMPLETE_TRANSACTION' `
            ("an unresolved transaction (MigrationId $($unresolved.migration_id), status " +
             "'$($unresolved.status)') already exists in the backup directory for this home. " +
             "$remedy Nothing was written.")
    }

    $migrationId = New-SkillMeshMigrationId
    $plan = New-MigrationPlan $distAbs $backupAbs $migrationId
    if (@($plan.blocked).Count -gt 0) {
        # The PLAN is the report on this path -- its `blocked` array already carries
        # every finding -- so Exit-Blocked's own result document is deliberately NOT
        # emitted here. Two JSON documents on one stdout stream is not parseable
        # output, and -Format json promises exactly one.
        Write-Diag ("BLOCKED [" + [string](@($plan.blocked)[0].code) + "] " +
                    "$(@($plan.blocked).Count) blocking finding(s); refusing to migrate. " +
                    'Nothing was written.')
        Write-PlanReport $plan
        exit 2
    }

    # The backup directory is created only NOW -- after the plan validated clean --
    # so a blocked -Apply is a true no-op in the backup tree as well as in the home.
    $script:TxDir = Join-Path $backupAbs $migrationId
    $script:LedgerJson = $plan.ledger_json
    # The transaction dir is created under the operator-supplied -BackupDir and then
    # re-resolved so every later Resolve-TxPath is anchored to its REAL path.
    New-Item -ItemType Directory -Path $script:TxDir -Force | Out-Null
    $script:TxDir = Resolve-SafePath -Path $script:TxDir -AllowedRoots @($backupAbs)

    # ---- PREPARED: materialize backup payloads + the manifest, mutate nothing --
    # No `exit` inside this try: a flow-control exit interacting with catch/finally
    # is exactly the kind of subtlety that hides a bug, so the failure is recorded
    # and acted on after the block.
    $prepError = $null
    try {
        foreach ($a in @($plan.actions | Where-Object { $_.action -eq 'backup' })) {
            # The pre-image READ is gated exactly like a write. Following a junction
            # here would capture a file from OUTSIDE the home as the "pre-image",
            # corrupting the one artifact rollback depends on -- and it would do so
            # silently, because the payload would still hash-verify against itself.
            $safeSource = Resolve-HomeTarget -RelPosix $a.rel_path -Operation 'back it up'
            $safePayload = Resolve-TxPayloadPath $a.backup_payload
            New-DirectoryFor $safePayload
            Copy-Item -LiteralPath $safeSource -Destination $safePayload -Force
            if ((Get-SkillMeshFileSha256 $safePayload) -ne $a.pre_hash) {
                throw "backup payload for '$($a.rel_path)' did not verify."
            }
        }
        Write-TxJsonFile $PLAN_FILE $plan
        Write-TxJsonFile $BACKUP_MANIFEST_FILE (New-BackupManifest $plan)
    } catch {
        $prepError = $_
    }
    if ($null -ne $prepError) {
        # Nothing in the HOME was touched; discard the half-built transaction so it
        # can never masquerade as an unresolved transaction blocking a retry.
        Remove-TransactionDir
        Write-Diag "preparation failed before any mutation: $($prepError.Exception.Message)"
        Complete-Run 'aborted' $migrationId 1
    }

    $drift = Test-Preconditions $plan
    if (@($drift).Count -gt 0) {
        $sample = ((@($drift) | Select-Object -First 5) -join ', ')
        Remove-TransactionDir
        Exit-Blocked 'PRECONDITION_DRIFT' `
            "$(@($drift).Count) path(s) changed between planning and apply: $sample. Nothing was written."
    }

    Invoke-TransactionRun $plan 'prepared' $false
}

function Remove-TransactionDir {
    if ([string]::IsNullOrWhiteSpace($script:TxDir)) { return }
    if (-not (Test-Path -LiteralPath $script:TxDir)) { return }
    # Re-resolved immediately before the recursive delete: this removes a whole tree,
    # so it is the single most destructive primitive in the tool.
    $safeTxDir = Resolve-SafePath -Path $script:TxDir -AllowedRoots @($script:BackupAbs)
    Remove-Item -LiteralPath $safeTxDir -Recurse -Force
}

function Invoke-TransactionRun($plan, [string]$startStatus, [bool]$isResume,
        $planBySeq = $null) {
    # The single apply path, shared by -Apply and -Resume.
    if ($null -eq $planBySeq) {
        $planBySeq = @{}
        foreach ($action in @($plan.actions)) {
            $planBySeq[[int]$action.seq] = $action
        }
    }
    $recoveryRecords = @()
    if ($isResume) {
        try {
            $recoveryRecords = Read-SkillMeshTxJournal `
                (Resolve-TxPath $JOURNAL_FILE) `
                -AllowMissing:($startStatus -eq 'prepared')
        } catch {
            Exit-Blocked 'INVALID_JOURNAL' `
                ("transaction $($plan.migration_id) cannot be resumed safely: " +
                 "$($_.Exception.Message) Nothing was written.")
        }
        try {
            if ($null -eq $planBySeq) {
                throw 'validated plan action index is unavailable.'
            }
            Assert-RecoveryJournal $recoveryRecords $planBySeq `
                ([string]$plan.migration_id) $startStatus
        } catch {
            Exit-Blocked 'INVALID_JOURNAL' `
                ("transaction $($plan.migration_id) has inconsistent journal " +
                 "records: $($_.Exception.Message) Nothing was written.")
        }
    }
    $manifestName = $BACKUP_MANIFEST_FILE
    $expectedMigrationId = [string]$plan.migration_id
    $statusWriter = {
        param($status)
        $manifestPath = Resolve-TxPath $manifestName
        if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
            throw "migrate-legacy-install: SECURITY -- authoritative backup manifest is missing or is not a file."
        }
        $m = Read-JsonFile $manifestPath
        if ($null -eq $m -or
            [string](Get-SkillMeshTxField $m 'migration_id') -ne $expectedMigrationId) {
            throw "migrate-legacy-install: SECURITY -- authoritative backup manifest is corrupt or names a different transaction."
        }
        $m.status = $status
        Write-TxJsonFile $manifestName $m
        $verified = Read-JsonFile $manifestPath
        if ($null -eq $verified -or
            [string](Get-SkillMeshTxField $verified 'migration_id') -ne $expectedMigrationId -or
            [string](Get-SkillMeshTxField $verified 'status') -ne $status) {
            throw "migrate-legacy-install: SECURITY -- authoritative backup manifest status did not persist."
        }
    }.GetNewClosure()

    $tx = New-SkillMeshTransaction -MigrationId $plan.migration_id `
        -JournalPath (Resolve-TxPath $JOURNAL_FILE) `
        -Status $startStatus -StatusWriter $statusWriter

    $completionPlanBySeq = $planBySeq
    $completionMigrationId = [string]$plan.migration_id
    $validateRollbackCompletion = {
        param($candidateActions, $currentRecords)
        Assert-RecoveryJournal @($currentRecords) $completionPlanBySeq `
            $completionMigrationId 'rolling_back'
        $durableBegins = Get-SkillMeshTxBegunSeqs @($currentRecords)
        $expectedSeqs = @($durableBegins | ForEach-Object { [int]$_ } | Sort-Object)
        $candidateSeqs = @(@($candidateActions) | ForEach-Object {
            [int](Get-SkillMeshTxField $_ 'seq' -1)
        } | Sort-Object -Unique)
        if (($candidateSeqs -join ',') -cne ($expectedSeqs -join ',')) {
            throw "rollback candidate set does not match durable begin authority."
        }
    }.GetNewClosure()

    $getPre = { param($a) Get-HomeRelHash $a.rel_path }
    $getPost = { param($a) Get-HomeRelHash $a.rel_path }
    $mutate = { param($a) Invoke-ActionMutate $a }
    $undo = { param($a) Invoke-ActionUndo $a }
    $skip = $null
    $priorBegunActions = @()
    $priorCommittedSeqs = @()
    if ($isResume) {
        $skip = { param($a) Test-ActionAlreadyApplied $a }
        # Seed rollback only from durable begin history. A legacy commit-only record
        # proves only that an older resume observed matching bytes; it does not prove
        # this transaction created them and cannot authorize destructive undo.
        $begun = Get-SkillMeshTxBegunSeqs $recoveryRecords
        $priorBegunActions = @(@($plan.actions) |
            Where-Object { $begun.Contains([int]$_.seq) })
        $committed = Get-SkillMeshTxCommittedSeqs $recoveryRecords
        $priorCommittedSeqs = @($committed | ForEach-Object { [int]$_ })
    }

    $applyError = $null
    try {
        Invoke-SkillMeshTxApply -Transaction $tx -Actions @($plan.actions) `
            -GetPreHash $getPre -Mutate $mutate -GetPostHash $getPost `
            -Undo $undo -ShouldSkip $skip `
            -PriorBegunActions $priorBegunActions `
            -PriorCommittedSeqs $priorCommittedSeqs `
            -ValidateRollbackCompletion $validateRollbackCompletion `
            -DeferAppliedStatus
    } catch {
        $applyError = $_
    }
    if ($null -ne $applyError) {
        Write-Diag "transaction FAILED: $($applyError.Exception.Message)"
        if ($tx.status -eq 'failed_incomplete') {
            Write-Diag ("ROLLBACK INCOMPLETE -- the consumer home is MIXED. The backup is retained at " +
                        "MigrationId $($plan.migration_id); recover from it manually.")
            Complete-Run 'failed_incomplete' $plan.migration_id 3
        }
        # Decision D2 case 3: a PRE-COMPLETION abort never escalates on preserve
        # drift. Because the engine's post-hash check is kind-blind, an edited
        # preserved file is typically the very thing that TRIGGERED this path -- and
        # the correct response is to disclose it, not to claim a mixed home. Rollback
        # never touched that file, and no backup payload exists that could.
        Write-PreserveDriftAdvisory $plan
        # Narrow claim only (D2). The old wording -- "restored to its pre-migration
        # state" -- overclaimed on preserved paths, which carry no payload to restore.
        #
        # Gated on `rolled_back` because that is the only status under which the claim
        # is PROVABLE. The engine sets it after every undo succeeded; a status still
        # reading `prepared`/`applying` here means the rollback never ran (its status
        # writer threw), and asserting a completed restore then would be the same
        # species of overclaim this line was rewritten to remove.
        if ($tx.status -eq 'rolled_back') {
            Write-Diag ("every verified file mutation this tool made was reversed: prior " +
                        "file bytes were restored and every file it created was removed " +
                        "(status $($tx.status)). Empty directories may remain because " +
                        "they carry no durable identity.")
        } else {
            Write-Diag ("the transaction did not reach a rolled-back state (status $($tx.status)); " +
                        "the backup is retained at MigrationId $($plan.migration_id).")
        }
        Complete-Run $tx.status $plan.migration_id 1
    }

    # TEST SEAM (inert unless exactly `1`): stop after the action loop but before
    # the wider post-install verification publishes the terminal `applied` status.
    if ([Environment]::GetEnvironmentVariable(
            'SKILL_MESH_MIGRATE_CRASH_BEFORE_POSTCHECK') -eq '1') {
        [Console]::Error.WriteLine(
            'migrate-legacy-install: TEST SEAM -- simulated crash before post-install verification.')
        [Environment]::Exit(9)
    }

    # TEST SEAM (inert unless set): corrupt one home-relative path AFTER the engine's
    # per-action loop has committed and BEFORE post-install verification runs. This is
    # the only way to reach Test-PostInstall's failure branch from outside.
    #
    # It does NOT model "the only check that covers a preserve action" -- the engine's
    # per-action post-hash check is kind-blind, so a preserved path edited while the
    # loop is still running already fails there (D2 case 3: advisory, rolled_back).
    # What this seam models is the one window the loop structurally cannot see: drift
    # that lands after the last action commits, which only post-install verification
    # catches, and which D2 case 2 escalates. See tools/skill-mesh-transaction.ps1's
    # TEST SEAMS note for the convention; like those, it can only affect a process the
    # caller already started.
    $tamper = [Environment]::GetEnvironmentVariable('SKILL_MESH_MIGRATE_TAMPER_AFTER_APPLY')
    if (-not [string]::IsNullOrWhiteSpace($tamper)) {
        $safeTamper = Resolve-HomeTargetForRead $tamper.Trim()
        if ($null -ne $safeTamper -and (Test-Path -LiteralPath $safeTamper -PathType Leaf)) {
            [Console]::Error.WriteLine(
                "migrate-legacy-install: TEST SEAM -- tampering with '$($tamper.Trim())' before post-install verification.")
            [System.IO.File]::AppendAllText($safeTamper, "`n# tampered by test seam`n", $UTF8_NO_BOM)
        }
    }

    # Re-read and bind the durable journal after the action loop. This one snapshot
    # is both the proof needed to publish `applied` and the only source of rollback
    # authority if the wider post-install check fails. Commit-only observations are
    # deliberately excluded from the undo set below.
    try {
        $postActionRecords = Read-SkillMeshTxJournal (Resolve-TxPath $JOURNAL_FILE)
        Assert-RecoveryJournal $postActionRecords $planBySeq `
            ([string]$plan.migration_id) 'applied'
    } catch {
        Write-Diag ("post-action journal verification FAILED; no recovery mutation was attempted: " +
                    "$($_.Exception.Message)")
        try {
            Set-SkillMeshTxStatus $tx 'rolling_back'
            Set-SkillMeshTxStatus $tx 'failed_incomplete'
        } catch {
            Write-Diag ("the failed_incomplete status could not be persisted: " +
                        "$($_.Exception.Message)")
        }
        $lastVerifiedStatus = [string]$tx.status
        Write-Diag ("the last verified persisted transaction status is " +
                    "'$lastVerifiedStatus'.")
        Complete-Run $lastVerifiedStatus $plan.migration_id 3
    }

    $bad = Test-PostInstall $plan
    if (@($bad).Count -gt 0) {
        Write-Diag "post-install verification FAILED for $(@($bad).Count) path(s); rolling back."
        # Decision D2 case 2 -- the ONE preserve-drift case that escalates. The
        # boundary is STRUCTURAL, not trigger-site-based: reaching here means the
        # transaction was FULLY APPLIED and this tool's own post-install acceptance
        # then failed on a path it holds no backup payload for (a `preserve` action
        # never copies a byte-untouched consumer tree into the backup -- disclosure
        # minimization). A pre-completion abort is case 3 and never arrives here.
        #
        # What it does NOT mean is a mixed home. Rollback walks strict reverse seq
        # order and New-MigrationPlan emits backup < preserve < retire < install <
        # ledger, so by the time this wrapper throws on a preserve action every
        # MUTATING action has already been undone; only backup actions remain below
        # it, and their undo touches nothing in the home. Saying MIXED here would
        # invite restoring a backup over the consumer's own newer bytes -- the exact
        # round-5 regression this branch was corrected to remove.
        $badSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($b in @($bad)) { [void]$badSet.Add([string]$b) }
        # Reference type, so the closure's Add is visible out here after the throw --
        # this is what lets the message below distinguish an unrestorable-but-clean
        # preserve remainder from a genuine undo failure that DID leave the home mixed.
        $unrestorable = New-Object 'System.Collections.Generic.List[string]'
        $verifyUndo = {
            param($a)
            Invoke-ActionUndo $a
            if ($a.action -eq 'preserve' -and $badSet.Contains([string]$a.rel_path)) {
                [void]$unrestorable.Add([string]$a.rel_path)
                throw ("migrate-legacy-install: preserved path '$($a.rel_path)' changed during " +
                       "the transaction and has no backup payload by design; it cannot be restored.")
            }
        }.GetNewClosure()
        $durableBegins = Get-SkillMeshTxBegunSeqs $postActionRecords
        $rollbackActions = @(@($plan.actions) |
            Where-Object { $durableBegins.Contains([int]$_.seq) })
        $failure = Invoke-SkillMeshTxRollback $tx @($rollbackActions) $verifyUndo `
            -ValidateCompletion $validateRollbackCompletion
        if ($null -ne $failure) {
            if ($unrestorable.Count -gt 0) {
                # Name EVERY unrestorable preserved path, not just the one that threw.
                # Rollback breaks on its first failure, so $unrestorable can only ever
                # hold one entry -- but Test-PostInstall's $bad set holds all of them,
                # and D2 bounds this escalation to exactly that set. Reporting one of
                # three drifted paths would be true and useless.
                $names = (@(@($plan.actions) |
                    Where-Object { $_.action -eq 'preserve' -and $badSet.Contains([string]$_.rel_path) } |
                    ForEach-Object { "'" + (Get-SafeRelPathLabel $_.rel_path) + "'" }) -join ', ')
                Write-Diag ("every verified file mutation this tool made was reversed: prior " +
                            "file bytes were restored and every file it created was removed. " +
                            "Empty directories may remain because they carry no durable identity. " +
                            "Preserved path(s) $names changed during the " +
                            "transaction and carry no backup payload by design, so this tool cannot " +
                            "restore them -- those bytes are yours and were left exactly as found. " +
                            "The backup is retained at MigrationId $($plan.migration_id).")
            } else {
                Write-Diag ("ROLLBACK INCOMPLETE -- $($failure.Exception.Message) The backup is retained " +
                            "at MigrationId $($plan.migration_id); recover from it manually.")
            }
            Complete-Run 'failed_incomplete' $plan.migration_id 3
        }
        Complete-Run 'rolled_back' $plan.migration_id 1
    }

    # The per-action loop intentionally leaves the durable status at `applying`.
    # Publish `applied` only after the wider cross-action verification succeeds, so
    # a crash in that window resumes and re-runs acceptance instead of no-oping.
    Set-SkillMeshTxStatus $tx 'applied'

    # Do not remove empty retired ancestors. A path in a retire action proves file
    # authority, not identity of a later empty directory an operator may create in
    # the same location after the action commits.
    Write-Outcome ("migration $($plan.migration_id) APPLIED " +
                "($(@($plan.actions | Where-Object { $_.action -eq 'install' }).Count) installed, " +
                "$(@($plan.actions | Where-Object { $_.action -eq 'retire' }).Count) retired, " +
                "$(@($plan.actions | Where-Object { $_.action -eq 'preserve' }).Count) preserved).")
    Complete-Run 'applied' $plan.migration_id 0
}

function Complete-Run([string]$status, [string]$migrationId, [int]$code) {
    if ($Format -eq 'json') {
        Write-Output (New-ResultDocument $status $migrationId @() | ConvertTo-Json -Depth 6)
    }
    exit $code
}

function Test-RecordedSha256($value, [switch]$AllowNull) {
    if ($null -eq $value) { return [bool]$AllowNull }
    return ([string]$value -cmatch '\A[0-9a-f]{64}\z')
}

function Test-RecoveryRelPath([string]$rel) {
    if ([string]::IsNullOrWhiteSpace($rel) -or $rel.Contains('\') -or
        $rel.StartsWith('/') -or $rel -match '\A[A-Za-z]:') { return $false }
    foreach ($segment in @($rel.Split('/'))) {
        if ([string]::IsNullOrEmpty($segment) -or
            (Test-SkillMeshTxMember @('.', '..') $segment)) { return $false }
    }
    return $true
}

function Convert-RecoveryEntriesToMap($entries, [string]$label,
        [bool]$withPayload) {
    $map = @{}
    foreach ($entry in @($entries)) {
        $rel = [string](Get-SkillMeshTxField $entry 'rel_path')
        $hash = Get-SkillMeshTxField $entry 'sha256'
        if (-not (Test-RecoveryRelPath $rel) -or
            -not (Test-RecordedSha256 $hash)) {
            throw "backup manifest $label contains an invalid path or SHA-256."
        }
        if ($map.ContainsKey($rel)) {
            throw "backup manifest $label contains duplicate path '$rel'."
        }
        $payload = ''
        if ($withPayload) {
            $payload = [string](Get-SkillMeshTxField $entry 'backup_payload')
            if (-not (Test-RecoveryRelPath $payload) -or
                -not (Test-RelAtOrUnderRoot $payload $PAYLOAD_DIR)) {
                throw "backup manifest $label contains an invalid recovery payload path."
            }
        }
        $map[$rel] = [PSCustomObject]@{ hash = [string]$hash; payload = $payload }
    }
    return $map
}

function Convert-RecoveryStringArray($property, [string]$label,
        [switch]$RequireRelPaths, [switch]$AllowHomeRootSentinel) {
    # ConvertFrom-Json preserves a JSON array as System.Array. Requiring that
    # shape prevents a scalar from being silently accepted as a one-element list.
    $raw = $property.Value
    if ($null -eq $raw -or -not ($raw -is [System.Array])) {
        throw "$label is missing or is not an array."
    }
    $values = @()
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' `
        ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($item in @($raw)) {
        if (-not ($item -is [string]) -or
            [string]::IsNullOrWhiteSpace([string]$item) -or
            ($RequireRelPaths -and
             -not ($AllowHomeRootSentinel -and [string]$item -ceq '.') -and
             -not (Test-RecoveryRelPath ([string]$item)))) {
            throw "$label contains an invalid relative path or non-string value."
        }
        if (-not $seen.Add([string]$item)) {
            throw "$label contains a duplicate path '$item'."
        }
        $values += [string]$item
    }
    $sorted = @($values | Sort-Object -Unique)
    if (($values -join "`n") -cne ($sorted -join "`n")) {
        throw "$label is not in deterministic sorted order."
    }
    return , @($values)
}

function Assert-RecoveryLedgerContract($plan, $ledgerAction,
        $expectedInstallsByProvider) {
    <#
      ledger_json is executable recovery input: Resume writes these exact bytes.
      Binding only its SHA-256 to a ledger action is circular because an operator-
      writable plan can change both together. Reconstruct its semantic authority
      from the independently validated install actions before journal history can
      authorize any mutation.
    #>
    $ledgerJson = Get-SkillMeshTxField $plan 'ledger_json'
    if (-not ($ledgerJson -is [string]) -or
        [string]::IsNullOrWhiteSpace([string]$ledgerJson) -or
        (Get-SkillMeshStringSha256 ([string]$ledgerJson)) -cne
            [string](Get-SkillMeshTxField $ledgerAction 'post_hash')) {
        throw "plan ledger_json does not match the ledger action post_hash."
    }
    try {
        $ledger = ([string]$ledgerJson | ConvertFrom-Json)
    } catch {
        throw "plan ledger_json is not valid JSON."
    }
    if (-not ($ledger -is [System.Management.Automation.PSCustomObject])) {
        throw "plan ledger_json is not an object."
    }
    $topFields = @($ledger.PSObject.Properties | ForEach-Object { $_.Name })
    if (($topFields -join "`n") -cne (@('tool', 'ledger_version', 'installs') -join "`n") -or
        [string](Get-SkillMeshTxField $ledger 'tool') -cne 'skill-mesh') {
        throw "plan ledger_json has an invalid top-level contract."
    }
    $ledgerVersion = Get-SkillMeshTxField $ledger 'ledger_version'
    if (-not ($ledgerVersion -is [int]) -or [int]$ledgerVersion -ne $LEDGER_VERSION) {
        throw "plan ledger_json has an unsupported ledger_version."
    }
    $ledgerInstalls = Get-SkillMeshTxField $ledger 'installs'
    if (-not ($ledgerInstalls -is [System.Management.Automation.PSCustomObject])) {
        throw "plan ledger_json installs is not an object."
    }

    # New plans record the complete provider-root set explicitly so a provider
    # with zero install actions still receives an empty ledger entry. Older plans
    # did not carry provider_roots; for those, accept only canonical providers
    # present in the semantically validated ledger itself.
    $providerRootsRaw = Get-SkillMeshTxField $plan 'provider_roots'
    $hasProviderRoots = $null -ne $providerRootsRaw
    if ($hasProviderRoots) {
        if (-not ($providerRootsRaw -is [System.Management.Automation.PSCustomObject])) {
            throw "plan provider_roots is not an object."
        }
        $providerRootProps = @($providerRootsRaw.PSObject.Properties)
        $sortedProviderNames = @($providerRootProps.Name | Sort-Object -Unique)
        if (($providerRootProps.Name -join "`n") -cne
            ($sortedProviderNames -join "`n")) {
            throw "plan provider_roots is not in deterministic sorted order."
        }
        foreach ($property in $providerRootProps) {
            $provider = [string]$property.Name
            $canonical = @($DISCOVERY_SUBDIR.Keys | Where-Object {
                [string]$_ -ceq $provider
            })
            if ($canonical.Count -ne 1 -or
                -not ($property.Value -is [string]) -or
                [string]$property.Value -cne [string]$DISCOVERY_SUBDIR[$provider]) {
                throw "plan provider_roots contains an unknown provider or discovery root."
            }
            if (-not $expectedInstallsByProvider.ContainsKey($provider)) {
                $expectedInstallsByProvider[$provider] = @{}
            }
        }
    } else {
        foreach ($property in @($ledgerInstalls.PSObject.Properties)) {
            $provider = [string]$property.Name
            $canonical = @($DISCOVERY_SUBDIR.Keys | Where-Object {
                [string]$_ -ceq $provider
            })
            if ($canonical.Count -ne 1) {
                throw "legacy plan ledger_json contains an unknown provider."
            }
            if (-not $expectedInstallsByProvider.ContainsKey($provider)) {
                $expectedInstallsByProvider[$provider] = @{}
            }
        }
    }

    $planCreatedProp = @($plan.PSObject.Properties | Where-Object {
        $_.Name -ceq 'created_dirs'
    })
    if ($planCreatedProp.Count -ne 1) {
        throw "plan created_dirs is missing or duplicated."
    }
    $planCreated = Convert-RecoveryStringArray $planCreatedProp[0] `
        'plan created_dirs' -RequireRelPaths
    $allExpectedRelPaths = @()
    foreach ($provider in @($expectedInstallsByProvider.Keys)) {
        $allExpectedRelPaths += @($expectedInstallsByProvider[$provider].Keys)
    }
    foreach ($dir in $planCreated) {
        if (@($allExpectedRelPaths | Where-Object {
                $_.StartsWith("$dir/", [System.StringComparison]::OrdinalIgnoreCase)
            }).Count -eq 0) {
            throw "plan created_dirs contains '$dir', which is not an install-path ancestor."
        }
    }

    $expectedProviders = @($expectedInstallsByProvider.Keys | Sort-Object)
    $actualProviderProps = @($ledgerInstalls.PSObject.Properties)
    if ($actualProviderProps.Count -ne $expectedProviders.Count) {
        throw "plan ledger_json provider set does not match the install actions."
    }
    $hashMode = $null
    foreach ($property in $actualProviderProps) {
        $entry = $property.Value
        if (-not ($entry -is [System.Management.Automation.PSCustomObject])) {
            throw "plan ledger_json contains a provider entry that is not an object."
        }
        $hasHashes = @($entry.PSObject.Properties | Where-Object {
            $_.Name -ceq 'owned_file_hashes'
        }).Count -eq 1
        if ($null -eq $hashMode) {
            $hashMode = $hasHashes
        } elseif ([bool]$hashMode -ne [bool]$hasHashes) {
            throw "plan ledger_json mixes hashed and legacy hashless provider entries."
        }
    }
    if ($hasProviderRoots -and -not $hashMode) {
        throw "a provider_roots plan cannot downgrade to legacy hashless ledger entries."
    }
    for ($providerIndex = 0; $providerIndex -lt $expectedProviders.Count;
            $providerIndex++) {
        $provider = [string]$expectedProviders[$providerIndex]
        $property = $actualProviderProps[$providerIndex]
        if ([string]$property.Name -cne $provider) {
            throw "plan ledger_json provider set/order does not match the install actions."
        }
        $entry = $property.Value
        if (-not ($entry -is [System.Management.Automation.PSCustomObject])) {
            throw "plan ledger_json provider '$provider' entry is not an object."
        }
        $entryFields = @($entry.PSObject.Properties | ForEach-Object { $_.Name })
        $expectedEntryFields = @('provider', 'discovery_subdir', 'owned_files')
        if ($hashMode) { $expectedEntryFields += 'owned_file_hashes' }
        $expectedEntryFields += 'created_dirs'
        if (($entryFields -join "`n") -cne ($expectedEntryFields -join "`n") -or
            [string](Get-SkillMeshTxField $entry 'provider') -cne $provider -or
            [string](Get-SkillMeshTxField $entry 'discovery_subdir') -cne
                [string]$DISCOVERY_SUBDIR[$provider]) {
            throw "plan ledger_json provider '$provider' metadata is invalid."
        }

        $ownedProp = @($entry.PSObject.Properties | Where-Object {
            $_.Name -ceq 'owned_files'
        })
        if ($ownedProp.Count -ne 1) {
            throw "plan ledger_json provider '$provider' owned_files is missing or duplicated."
        }
        $owned = Convert-RecoveryStringArray $ownedProp[0] `
            "plan ledger_json provider '$provider' owned_files" -RequireRelPaths
        $expectedMap = $expectedInstallsByProvider[$provider]
        $expectedOwned = @($expectedMap.Keys | Sort-Object -Unique)
        if (($owned -join "`n") -cne ($expectedOwned -join "`n")) {
            throw "plan ledger_json provider '$provider' owned_files does not match install actions."
        }

        if ($hashMode) {
            $ownedHashes = Get-SkillMeshTxField $entry 'owned_file_hashes'
            if (-not ($ownedHashes -is [System.Management.Automation.PSCustomObject])) {
                throw "plan ledger_json provider '$provider' owned_file_hashes is not an object."
            }
            $hashProps = @($ownedHashes.PSObject.Properties)
            if ($hashProps.Count -ne $owned.Count) {
                throw "plan ledger_json provider '$provider' hash keys do not match owned_files."
            }
            for ($hashIndex = 0; $hashIndex -lt $owned.Count; $hashIndex++) {
                $rel = [string]$owned[$hashIndex]
                $hashProp = $hashProps[$hashIndex]
                if ([string]$hashProp.Name -cne $rel -or
                    -not ($hashProp.Value -is [string]) -or
                    [string]$hashProp.Value -cne [string]$expectedMap[$rel]) {
                    throw "plan ledger_json provider '$provider' has an invalid hash for '$rel'."
                }
            }
        }

        $dirsProp = @($entry.PSObject.Properties | Where-Object {
            $_.Name -ceq 'created_dirs'
        })
        if ($dirsProp.Count -ne 1) {
            throw "plan ledger_json provider '$provider' created_dirs is missing or duplicated."
        }
        $dirs = Convert-RecoveryStringArray $dirsProp[0] `
            "plan ledger_json provider '$provider' created_dirs" `
            -RequireRelPaths -AllowHomeRootSentinel
        $providerRoot = [string]$DISCOVERY_SUBDIR[$provider]
        foreach ($dir in $dirs) {
            if ($dir -ceq '.') { continue }
            if (-not (Test-RelAtOrUnderRoot $dir $providerRoot) -and
                -not (Test-RelAtOrUnderRoot $providerRoot $dir)) {
                throw "plan ledger_json provider '$provider' created_dirs escapes its discovery root."
            }
            if ($expectedMap.ContainsKey($dir)) {
                throw "plan ledger_json provider '$provider' created_dirs names an installed file."
            }
        }
        $expectedPlanDirs = @($planCreated | Where-Object {
            $_ -eq $providerRoot -or $_.StartsWith("$providerRoot/") -or
            $providerRoot.StartsWith("$_/")
        })
        foreach ($dir in $expectedPlanDirs) {
            if (-not (Test-SkillMeshTxMember $dirs $dir)) {
                throw "plan ledger_json provider '$provider' omits planned created dir '$dir'."
            }
        }
    }
}

function Assert-RecoveryMetadata($plan, $manifest, [string]$backupAbs,
        [string]$expectedMigrationId = $MigrationId) {
    <#
      Bind every recovery authority document to this transaction before journal
      history or payload hashes can authorize a mutation. These files live in an
      operator-writable backup tree; valid JSON alone is not identity.
    #>
    foreach ($doc in @($plan, $manifest)) {
        $schema = Get-SkillMeshTxField $doc 'schema_version'
        if (-not ($schema -is [int]) -or [int]$schema -ne $SCHEMA_VERSION) {
            throw "plan/manifest schema_version is missing or unsupported."
        }
        if ([string](Get-SkillMeshTxField $doc 'migration_id') -cne $expectedMigrationId) {
            throw "plan/manifest migration_id does not match the transaction directory."
        }
    }
    $planRootEncoding = [string](Get-SkillMeshTxField $plan 'root_encoding')
    $manifestRootEncoding = [string](Get-SkillMeshTxField $manifest 'root_encoding')
    $legacyRootEncoding = ([string]::IsNullOrEmpty($planRootEncoding) -and
        [string]::IsNullOrEmpty($manifestRootEncoding))
    if (-not $legacyRootEncoding -and
        ($planRootEncoding -cne $ROOT_ENCODING -or
         $manifestRootEncoding -cne $ROOT_ENCODING)) {
        throw "plan/manifest root_encoding is inconsistent or unsupported."
    }
    $status = [string](Get-SkillMeshTxField $manifest 'status')
    if (-not (Test-SkillMeshTxMember (Get-SkillMeshTxStates) $status)) {
        throw "backup manifest contains an unknown transaction status."
    }
    $plannedBackup = [string](Get-SkillMeshTxField $plan 'backup_dir')
    if ([string]::IsNullOrWhiteSpace($plannedBackup) -or
        -not ([System.IO.Path]::GetFullPath($plannedBackup)).TrimEnd('\', '/').Equals(
            $backupAbs.TrimEnd('\', '/'),
            [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "plan backup_dir does not match the selected backup directory."
    }
    if (-not $legacyRootEncoding) {
        if ([string](Get-SkillMeshTxField $manifest 'consumer_home') -cne
                [string](Get-SkillMeshTxField $plan 'consumer_home') -or
            [string](Get-SkillMeshTxField $manifest 'backup_dir') -cne $plannedBackup) {
            throw "backup manifest canonical roots do not match the plan."
        }
    }

    $actions = @(Get-SkillMeshTxField $plan 'actions' @())
    if ($actions.Count -eq 0) { throw "plan contains no actions." }
    $bySeq = @{}
    $actionKeys = New-Object 'System.Collections.Generic.HashSet[string]' `
        ([System.StringComparer]::OrdinalIgnoreCase)
    $primaryRelKeys = New-Object 'System.Collections.Generic.HashSet[string]' `
        ([System.StringComparer]::OrdinalIgnoreCase)
    $expectedOriginals = @{}
    $expectedPreserved = @{}
    $expectedInstalled = @{}
    $expectedBackups = @{}
    $expectedSeparateBackups = @{}
    $expectedInstallsByProvider = @{}
    $ledgerAction = $null
    $kindRank = @{ backup = 0; preserve = 1; retire = 2; install = 3; ledger = 4 }
    $lastKindRank = -1
    for ($i = 0; $i -lt $actions.Count; $i++) {
        $a = $actions[$i]
        $seq = Get-SkillMeshTxField $a 'seq'
        $kind = [string](Get-SkillMeshTxField $a 'action')
        $rel = [string](Get-SkillMeshTxField $a 'rel_path')
        if (-not ($seq -is [int]) -or [int]$seq -ne $i) {
            throw "plan action seq values are not unique contiguous integers."
        }
        if (-not (Test-SkillMeshTxMember (Get-SkillMeshTxActionKinds) $kind) -or
            -not (Test-RecoveryRelPath $rel)) {
            throw "plan action $i has an invalid kind or relative path."
        }
        $rank = [int]$kindRank[$kind]
        if ($rank -lt $lastKindRank) {
            throw "plan actions do not preserve backup/preserve/retire/install/ledger order."
        }
        $lastKindRank = $rank
        if (-not $actionKeys.Add("$kind`n$rel")) {
            throw "plan contains a duplicate '$kind' action for '$rel'."
        }
        if ((Test-SkillMeshTxMember @('preserve', 'retire', 'install', 'ledger') $kind) -and
            (-not $primaryRelKeys.Add($rel))) {
            throw "plan contains contradictory primary actions for '$rel'."
        }
        $pre = Get-SkillMeshTxField $a 'pre_hash'
        $post = Get-SkillMeshTxField $a 'post_hash'
        if (-not (Test-RecordedSha256 $pre -AllowNull) -or
            -not (Test-RecordedSha256 $post -AllowNull)) {
            throw "plan action $i contains an invalid hash."
        }
        $payload = [string](Get-SkillMeshTxField $a 'backup_payload')
        $provider = [string](Get-SkillMeshTxField $a 'provider')
        if (-not [string]::IsNullOrEmpty($payload) -and
            (-not (Test-RecoveryRelPath $payload) -or
             -not (Test-RelAtOrUnderRoot $payload $PAYLOAD_DIR))) {
            throw "plan action $i contains an invalid recovery payload path."
        }
        switch ($kind) {
            'backup' {
                if ($null -eq $pre -or [string]$pre -cne [string]$post -or
                    [string]::IsNullOrEmpty($payload)) {
                    throw "backup action $i has an invalid state transition."
                }
                if ($rel -eq $LEDGER_NAME) {
                    if (-not [string]::IsNullOrEmpty($provider)) {
                        throw "ledger backup action $i has an invalid provider."
                    }
                } elseif (-not $DISCOVERY_SUBDIR.ContainsKey($provider) -or
                    -not (Test-RelAtOrUnderRoot $rel $DISCOVERY_SUBDIR[$provider])) {
                    throw "install backup action $i has an invalid provider or target root."
                }
                $expectedBackups[$rel] = [PSCustomObject]@{
                    hash = [string]$pre; payload = $payload
                }
            }
            'preserve' {
                if ($null -eq $pre -or [string]$pre -cne [string]$post -or
                    -not [string]::IsNullOrEmpty($payload) -or
                    -not [string]::IsNullOrEmpty($provider)) {
                    throw "preserve action $i has an invalid state transition."
                }
                $expectedPreserved[$rel] = [string]$pre
            }
            'retire' {
                if ($null -eq $pre -or $null -ne $post -or
                    [string]::IsNullOrEmpty($payload) -or
                    -not [string]::IsNullOrEmpty($provider)) {
                    throw "retire action $i has an invalid state transition."
                }
                if (-not $legacyRootEncoding -and
                    -not (Test-RelAtOrUnderRoot $rel $RETIRED_ROOT_REL)) {
                    throw "encoded plan retire action $i is outside the retired project root."
                }
                $expectedOriginals[$rel] = [PSCustomObject]@{
                    hash = [string]$pre; payload = $payload
                }
            }
            'install' {
                if ($null -eq $post -or
                    (($null -ne $pre) -ne (-not [string]::IsNullOrEmpty($payload)))) {
                    throw "install action $i has an invalid state transition."
                }
                $canonicalProvider = @($DISCOVERY_SUBDIR.Keys | Where-Object {
                    [string]$_ -ceq $provider
                })
                if ($canonicalProvider.Count -ne 1 -or
                    -not (Test-RelAtOrUnderRoot $rel $DISCOVERY_SUBDIR[$provider])) {
                    throw "install action $i has an invalid provider or target root."
                }
                $expectedInstalled[$rel] = [string]$post
                if (-not $expectedInstallsByProvider.ContainsKey($provider)) {
                    $expectedInstallsByProvider[$provider] = @{}
                }
                $expectedInstallsByProvider[$provider][$rel] = [string]$post
                if ($null -ne $pre) {
                    $expectedOriginals[$rel] = [PSCustomObject]@{
                        hash = [string]$pre; payload = $payload
                    }
                    $expectedSeparateBackups[$rel] = [PSCustomObject]@{
                        hash = [string]$pre; payload = $payload
                    }
                }
            }
            'ledger' {
                if ($null -ne $ledgerAction -or $i -ne ($actions.Count - 1) -or
                    $rel -cne $LEDGER_NAME -or $null -eq $post -or
                    (($null -ne $pre) -ne (-not [string]::IsNullOrEmpty($payload))) -or
                    -not [string]::IsNullOrEmpty($provider)) {
                    throw "plan ledger action is missing, duplicated, or not last."
                }
                $ledgerAction = $a
            }
        }
        $bySeq[$i] = $a
    }
    if ($null -eq $ledgerAction) { throw "plan contains no ledger action." }
    Assert-RecoveryLedgerContract $plan $ledgerAction $expectedInstallsByProvider

    foreach ($rel in @($expectedSeparateBackups.Keys)) {
        if (-not $expectedBackups.ContainsKey($rel) -or
            $expectedBackups[$rel].hash -cne $expectedSeparateBackups[$rel].hash -or
            $expectedBackups[$rel].payload -cne $expectedSeparateBackups[$rel].payload) {
            throw "plan has no exact backup action for original '$rel'."
        }
    }
    if ($null -ne $ledgerAction.pre_hash) {
        if (-not $expectedBackups.ContainsKey($LEDGER_NAME) -or
            $expectedBackups[$LEDGER_NAME].hash -cne [string]$ledgerAction.pre_hash -or
            $expectedBackups[$LEDGER_NAME].payload -cne [string]$ledgerAction.backup_payload) {
            throw "plan has no exact backup action for the prior ledger."
        }
    }
    $expectedBackupCount = $expectedSeparateBackups.Count + $(if ($null -ne $ledgerAction.pre_hash) { 1 } else { 0 })
    if ($expectedBackups.Count -ne $expectedBackupCount) {
        throw "plan contains an orphan or duplicate backup action."
    }

    # Materialize each collection before positional binding. An empty JSON array
    # comes back from Get-SkillMeshTxField as no pipeline output; embedding that
    # call directly in the argument list shifts the label into `$entries` under
    # PowerShell 5.1 and falsely reports an invalid preserved row.
    $manifestOriginalEntries = @(Get-SkillMeshTxField $manifest 'original_files' @())
    $manifestPreservedEntries = @(Get-SkillMeshTxField $manifest 'preserved_files' @())
    $manifestInstalledEntries = @(Get-SkillMeshTxField $manifest 'installed_files' @())
    $actualOriginals = Convert-RecoveryEntriesToMap `
        $manifestOriginalEntries 'original_files' $true
    $actualPreserved = Convert-RecoveryEntriesToMap `
        $manifestPreservedEntries 'preserved_files' $false
    $actualInstalled = Convert-RecoveryEntriesToMap `
        $manifestInstalledEntries 'installed_files' $false
    foreach ($pair in @(
        [PSCustomObject]@{ expected = $expectedOriginals; actual = $actualOriginals; label = 'original_files'; payload = $true },
        [PSCustomObject]@{ expected = $expectedPreserved; actual = $actualPreserved; label = 'preserved_files'; payload = $false },
        [PSCustomObject]@{ expected = $expectedInstalled; actual = $actualInstalled; label = 'installed_files'; payload = $false }
    )) {
        if ($pair.expected.Count -ne $pair.actual.Count) {
            throw "backup manifest $($pair.label) does not match the plan."
        }
        foreach ($rel in @($pair.expected.Keys)) {
            if (-not $pair.actual.ContainsKey($rel)) {
                throw "backup manifest $($pair.label) is missing '$rel'."
            }
            $expectedHash = $(if ($pair.payload) { $pair.expected[$rel].hash } else { $pair.expected[$rel] })
            if ($pair.actual[$rel].hash -cne [string]$expectedHash -or
                ($pair.payload -and
                 $pair.actual[$rel].payload -cne $pair.expected[$rel].payload)) {
                throw "backup manifest $($pair.label) disagrees with the plan for '$rel'."
            }
        }
    }
    $actualLedger = Get-SkillMeshTxField $manifest 'original_ledger'
    if ($null -eq $ledgerAction.pre_hash) {
        if ($null -ne $actualLedger) { throw "backup manifest invents a prior ledger." }
    } else {
        if ($null -eq $actualLedger -or
            [string](Get-SkillMeshTxField $actualLedger 'sha256') -cne [string]$ledgerAction.pre_hash -or
            [string](Get-SkillMeshTxField $actualLedger 'backup_payload') -cne [string]$ledgerAction.backup_payload) {
            throw "backup manifest original_ledger disagrees with the plan."
        }
    }
    return $bySeq
}

function Test-RecoveryJournalHasRollbackComplete($records) {
    return (@(@($records) | Where-Object {
        Test-SkillMeshTxMember @('rollback_complete') `
            ([string](Get-SkillMeshTxField $_ 'phase'))
    }).Count -eq 1)
}

function Assert-RecoveryJournal($records, $planBySeq, [string]$migrationId,
        [string]$status, [switch]$RequireRollbackComplete) {
    $begun = New-Object 'System.Collections.Generic.HashSet[int]'
    $committed = New-Object 'System.Collections.Generic.HashSet[int]'
    $openBegins = New-Object 'System.Collections.Generic.HashSet[int]'
    $rollbackComplete = $false
    foreach ($record in @($records)) {
        $schema = Get-SkillMeshTxField $record 'schema_version'
        $phase = [string](Get-SkillMeshTxField $record 'phase')
        if ($rollbackComplete) {
            throw "journal contains a record after rollback_complete."
        }
        if (Test-SkillMeshTxMember @('rollback_complete') $phase) {
            $actualFields = @($record.PSObject.Properties.Name | Sort-Object)
            $expectedFields = @(
                'begun_seqs', 'migration_id', 'phase', 'schema_version', 'utc'
            ) | Sort-Object
            if (($actualFields -join ',') -cne ($expectedFields -join ',')) {
                throw "rollback_complete record has an invalid field shape."
            }
            if (-not ($schema -is [int]) -or
                [int]$schema -ne (Get-SkillMeshTxSchemaVersion) -or
                [string](Get-SkillMeshTxField $record 'migration_id') -cne $migrationId) {
                throw "rollback_complete record has an invalid schema or transaction id."
            }
            $completionUtc = Get-SkillMeshTxField $record 'utc'
            if (-not ($completionUtc -is [string]) -or
                [string]::IsNullOrWhiteSpace([string]$completionUtc)) {
                throw "rollback_complete record has an invalid utc value."
            }
            # Fetch the raw property value directly. Get-SkillMeshTxField returns
            # through PowerShell's pipeline, which collapses [] to null and [0] to
            # scalar Int32 on Windows PowerShell 5.1; both are valid JSON arrays and
            # must retain their container identity for this authority check.
            $rawSeqProperty = $record.PSObject.Properties['begun_seqs']
            if ($null -eq $rawSeqProperty) {
                throw "rollback_complete record is missing begun_seqs."
            }
            $rawSeqValue = $rawSeqProperty.Value
            if (-not ($rawSeqValue -is [System.Array])) {
                throw "rollback_complete begun_seqs must be a JSON array."
            }
            $rawSeqs = @($rawSeqValue)
            $priorDeclared = -1
            foreach ($rawSeq in $rawSeqs) {
                if (-not ($rawSeq -is [int]) -or [int]$rawSeq -lt 0 -or
                    [int]$rawSeq -le $priorDeclared -or
                    -not $planBySeq.ContainsKey([int]$rawSeq)) {
                    throw "rollback_complete record contains an invalid begun seq."
                }
                $priorDeclared = [int]$rawSeq
            }
            $declared = @($rawSeqs | ForEach-Object { [int]$_ })
            $normalized = @($declared | Sort-Object -Unique)
            $expected = @($begun | ForEach-Object { [int]$_ } | Sort-Object)
            if ($declared.Count -ne $normalized.Count -or
                ($declared -join ',') -cne ($normalized -join ',') -or
                ($normalized -join ',') -cne ($expected -join ',')) {
                throw "rollback_complete record does not match durable begin authority."
            }
            $rollbackComplete = $true
            continue
        }
        $seq = Get-SkillMeshTxField $record 'seq'
        if (-not ($schema -is [int]) -or [int]$schema -ne (Get-SkillMeshTxSchemaVersion) -or
            [string](Get-SkillMeshTxField $record 'migration_id') -cne $migrationId -or
            -not ($seq -is [int]) -or -not $planBySeq.ContainsKey([int]$seq) -or
            -not (Test-SkillMeshTxMember @('begin', 'commit') $phase)) {
            throw "journal record has an invalid schema, transaction id, seq, or phase."
        }
        $action = $planBySeq[[int]$seq]
        if ([string](Get-SkillMeshTxField $record 'action') -cne [string]$action.action -or
            [string](Get-SkillMeshTxField $record 'rel_path') -cne [string]$action.rel_path) {
            throw "journal record does not match its plan action."
        }
        $pre = Get-SkillMeshTxField $record 'pre_hash'
        $post = Get-SkillMeshTxField $record 'post_hash'
        if (-not (Test-RecordedSha256 $pre -AllowNull) -or
            -not (Test-RecordedSha256 $post -AllowNull)) {
            throw "journal record contains an invalid hash."
        }
        # A non-mutating backup/preserve action may durably record drifted bytes it
        # observed before its verification refuses; its undo is a no-op and the
        # record grants no destructive authority. A mutating action's immutable
        # begin record is always plan-strict. Later consumer edits change current
        # disk state, never historical begin authority.
        $kind = [string]$action.action
        $allowObservedPre = Test-SkillMeshTxMember @('backup', 'preserve') $kind
        if ($phase -eq 'begin' -and
            ((-not $allowObservedPre -and
              [string]$pre -cne [string]$action.pre_hash) -or $null -ne $post)) {
            throw "journal begin record disagrees with the planned pre-image."
        }
        if ($phase -eq 'commit' -and
            [string]$post -cne [string]$action.post_hash) {
            throw "journal commit record disagrees with the planned post-image."
        }
        $n = [int]$seq
        if ($phase -eq 'begin') {
            [void]$begun.Add($n)
            [void]$openBegins.Add($n)
        } else {
            # Legacy commit-only records are tolerated as observation, but never
            # become rollback authority. A retry may add another begin/commit pair
            # for the same action, but a second commit without an intervening begin
            # is redundant/corrupt and is rejected.
            if ($committed.Contains($n) -and -not $openBegins.Contains($n)) {
                throw "journal contains a duplicate commit without an intervening begin."
            }
            [void]$committed.Add($n)
            [void]$openBegins.Remove($n)
        }
    }
    if ($status -eq 'prepared' -and @($records).Count -ne 0) {
        throw "a prepared transaction unexpectedly contains journal history."
    }
    if ($rollbackComplete -and
        -not (Test-SkillMeshTxMember @('rolling_back', 'rolled_back') $status)) {
        throw "rollback_complete record conflicts with transaction status '$status'."
    }
    if ($status -eq 'rolled_back' -and $RequireRollbackComplete -and
        -not $rollbackComplete) {
        throw "a current rolled_back transaction lacks durable rollback completion."
    }
    if ($status -eq 'applied') {
        foreach ($seq in @($planBySeq.Keys)) {
            if (-not $committed.Contains([int]$seq) -or
                $openBegins.Contains([int]$seq)) {
                throw "an applied transaction lacks complete committed history."
            }
        }
    }
}

function Read-ValidatedRecoveryJournal($plan, $manifest, $planBySeq,
        [string]$status, [switch]$AllowPreparedMissing) {
    <#
      The ONE explicit-recovery reader. Even a terminal manifest status is only a
      claim until its complete journal validates. Current rolled_back artifacts
      require durable rollback_complete; legacy markerless artifacts retain the
      conservative exact-pre-state compatibility proof.
    #>
    $records = Read-SkillMeshTxJournal `
        (Resolve-TxPath $JOURNAL_FILE) `
        -AllowMissing:$AllowPreparedMissing
    $planRootEncoding = [string](Get-SkillMeshTxField $plan 'root_encoding')
    $manifestRootEncoding = [string](Get-SkillMeshTxField $manifest 'root_encoding')
    $legacyRootEncoding = ([string]::IsNullOrEmpty($planRootEncoding) -and
        [string]::IsNullOrEmpty($manifestRootEncoding))
    Assert-RecoveryJournal $records $planBySeq `
        ([string](Get-SkillMeshTxField $plan 'migration_id')) $status `
        -RequireRollbackComplete:((Test-SkillMeshTxMember @('rolled_back') $status) -and
            -not $legacyRootEncoding)
    if ((Test-SkillMeshTxMember @('rolled_back') $status) -and
        -not (Test-RecoveryJournalHasRollbackComplete $records)) {
        Assert-LegacyRolledBackPrestate $plan $records
    }
    return , @($records)
}

function Get-TransactionContext([string]$backupAbs) {
    # Load one transaction's plan + backup manifest, validating the migration id
    # shape, the transaction's containment inside -BackupDir, that it belongs to
    # THIS home, and that the plan and manifest name the same release.
    if (-not (Test-SkillMeshMigrationId $MigrationId)) {
        Exit-Blocked 'INVALID_MIGRATION_ID' `
            '-MigrationId must have the form yyyyMMddTHHmmssZ-<8 lowercase hex>.'
    }
    $txDir = Join-Path $backupAbs $MigrationId
    try {
        # RESOLVED, not merely checked: the real path becomes $script:TxDir, so every
        # later Resolve-TxPath is anchored to it rather than to the lexical join.
        $txDir = Resolve-SafePath -Path $txDir -AllowedRoots @($backupAbs)
    } catch {
        Exit-Blocked 'UNSAFE_LINK' 'the transaction directory resolves outside -BackupDir.'
    }
    if (-not (Test-Path -LiteralPath $txDir -PathType Container)) {
        Exit-Blocked 'UNKNOWN_TRANSACTION' "no transaction $MigrationId exists in the backup directory."
    }
    $script:TxDir = $txDir
    $plan = Read-JsonFile (Resolve-TxPath $PLAN_FILE)
    $manifest = Read-JsonFile (Resolve-TxPath $BACKUP_MANIFEST_FILE)
    if ($null -eq $plan -or $null -eq $manifest) {
        Exit-Blocked 'UNKNOWN_TRANSACTION' "transaction $MigrationId is missing or has an unparseable plan/manifest."
    }
    $planRootEncoding = [string](Get-SkillMeshTxField $plan 'root_encoding')
    $manifestRootEncoding = [string](Get-SkillMeshTxField $manifest 'root_encoding')
    if ([string]::IsNullOrEmpty($planRootEncoding) -and
        [string]::IsNullOrEmpty($manifestRootEncoding)) {
        # Pre-Step65 schema-v1 artifacts recorded lexical roots with no encoding
        # discriminator. They are safely recoverable only when those spellings were
        # already canonical. Silently resolving an old alias now could redirect
        # historical begin authority into a replacement project.
        $legacyHome = [string](Get-SkillMeshTxField $plan 'consumer_home')
        $legacyBackup = [string](Get-SkillMeshTxField $plan 'backup_dir')
        try {
            $legacyHome = ([System.IO.Path]::GetFullPath($legacyHome)).TrimEnd('\', '/')
            $legacyBackup = ([System.IO.Path]::GetFullPath($legacyBackup)).TrimEnd('\', '/')
        } catch {
            Exit-Blocked 'LEGACY_ALIAS_ROOT_UNSUPPORTED' `
                "transaction $MigrationId has invalid legacy root spellings; automatic recovery is unsafe."
        }
        if (-not $legacyHome.Equals($script:HomeAbs,
                [System.StringComparison]::OrdinalIgnoreCase) -or
            -not $legacyBackup.Equals($backupAbs,
                [System.StringComparison]::OrdinalIgnoreCase)) {
            Exit-Blocked 'LEGACY_ALIAS_ROOT_UNSUPPORTED' `
                ("transaction $MigrationId predates canonical root encoding and records a " +
                 "Home or BackupDir alias. Automatic recovery cannot distinguish the original " +
                 "target from a retargeted junction; nothing was written.")
        }
    }
    try {
        $planBySeq = Assert-RecoveryMetadata $plan $manifest $backupAbs
    } catch {
        Exit-Blocked 'INVALID_TRANSACTION' `
            ("transaction $MigrationId has inconsistent recovery metadata: " +
             "$($_.Exception.Message) Nothing was written.")
    }
    $planHome = [string](Get-SkillMeshTxField $plan 'consumer_home')
    if (-not $planHome.Equals($script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase)) {
        Exit-Blocked 'HOME_MISMATCH' "transaction $MigrationId was planned for a different consumer home."
    }
    $planRel = ($plan.source_release | ConvertTo-Json -Depth 6 -Compress)
    $manRel = ($manifest.source_release | ConvertTo-Json -Depth 6 -Compress)
    if ($planRel -ne $manRel) {
        Exit-Blocked 'RELEASE_MISMATCH' "transaction $MigrationId has a plan and backup manifest naming different releases."
    }
    return @{ dir = $txDir; plan = $plan; manifest = $manifest; by_seq = $planBySeq }
}

function Update-ActionSources($plan, [string]$distAbs) {
    # A resume may run from a different -DistDir than the original apply (the
    # release tree can be re-staged), so an install's source is RE-DERIVED from the
    # current -DistDir rather than replayed from the recorded absolute path. Before
    # any target write, Assert-InstallSource requires an existing Leaf whose hash
    # equals the action's recorded post_hash; target post-verification then checks
    # the copy too. A changed/restaged source therefore refuses before mutation.
    foreach ($a in @($plan.actions | Where-Object { $_.action -eq 'install' })) {
        $provider = [string](Get-SkillMeshTxField $a 'provider')
        if (-not $DISCOVERY_SUBDIR.ContainsKey($provider)) { continue }
        $root = $DISCOVERY_SUBDIR[$provider] + '/'
        $rel = [string](Get-SkillMeshTxField $a 'rel_path')
        if (-not $rel.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) { continue }
        $fromProfile = $rel.Substring($root.Length)
        $a.source = (Join-Path (Join-Path $distAbs $provider) ($fromProfile -replace '/', '\'))
    }
}

function Invoke-Resume([string]$backupAbs, [string]$distAbs) {
    $ctx = Get-TransactionContext $backupAbs
    $script:TxDir = $ctx.dir
    $plan = $ctx.plan
    Update-ActionSources $plan $distAbs
    $script:LedgerJson = [string](Get-SkillMeshTxField $plan 'ledger_json')
    $status = [string](Get-SkillMeshTxField $ctx.manifest 'status')

    if (Test-SkillMeshTxMember @('applied', 'rolled_back', 'failed_incomplete') $status) {
        try {
            [void](Read-ValidatedRecoveryJournal $plan $ctx.manifest $ctx.by_seq $status)
        } catch {
            Exit-Blocked 'INVALID_JOURNAL' `
                ("transaction $MigrationId has invalid terminal journal authority: " +
                 "$($_.Exception.Message) Nothing was written.")
        }
    }
    if (Test-SkillMeshTxMember @('applied') $status) {
        Write-Outcome "migration $MigrationId is already applied (no-op)."
        Complete-Run 'applied' $MigrationId 0
    }
    if (Test-SkillMeshTxMember @('rolled_back') $status) {
        Exit-Blocked 'TRANSACTION_RESOLVED' `
            "migration $MigrationId has validated terminal status rolled_back; it cannot be resumed."
    }
    if (Test-SkillMeshTxMember @('failed_incomplete') $status) {
        # Same two-producer caveat as the INCOMPLETE_TRANSACTION remedy above: this
        # status means the rollback did not complete, which is a mixed home only when
        # the unrestorable path was one this tool MUTATED (D2 case 1). A preserved-path
        # failure (case 2) leaves the consumer's own bytes intact.
        Exit-Blocked 'TRANSACTION_RESOLVED' `
            "migration $MigrationId ended failed_incomplete; its rollback did not complete. See that run's diagnostics: a mutated path that could not be restored means the home is mixed and needs manual recovery from the retained backup, while a changed PRESERVED path (no backup payload by design) means those bytes are yours and are already intact."
    }
    if (-not (Test-SkillMeshTxMember @('prepared', 'applying') $status)) {
        Exit-Blocked 'TRANSACTION_RESOLVED' "migration $MigrationId has an unknown status '$status'."
    }
    Invoke-TransactionRun $plan $status $true $ctx.by_seq
}

function Invoke-Rollback([string]$backupAbs) {
    $ctx = Get-TransactionContext $backupAbs
    $script:TxDir = $ctx.dir
    $plan = $ctx.plan
    $script:LedgerJson = [string](Get-SkillMeshTxField $plan 'ledger_json')
    $status = [string](Get-SkillMeshTxField $ctx.manifest 'status')

    try {
        $recoveryRecords = Read-ValidatedRecoveryJournal `
            $plan $ctx.manifest $ctx.by_seq $status `
            -AllowPreparedMissing:(Test-SkillMeshTxMember @('prepared') $status)
    } catch {
        Exit-Blocked 'INVALID_JOURNAL' `
            ("transaction $($plan.migration_id) cannot be rolled back safely: " +
             "$($_.Exception.Message) Nothing was written.")
    }

    if (Test-SkillMeshTxMember @('rolled_back', 'failed_incomplete') $status) {
        Exit-Blocked 'TRANSACTION_RESOLVED' `
            "migration $MigrationId has validated terminal status '$status'; it cannot be rolled back again."
    }

    $manifestName = $BACKUP_MANIFEST_FILE
    $expectedMigrationId = [string]$plan.migration_id
    $statusWriter = {
        param($s)
        $manifestPath = Resolve-TxPath $manifestName
        if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
            throw "migrate-legacy-install: SECURITY -- authoritative backup manifest is missing or is not a file."
        }
        $m = Read-JsonFile $manifestPath
        if ($null -eq $m -or
            [string](Get-SkillMeshTxField $m 'migration_id') -ne $expectedMigrationId) {
            throw "migrate-legacy-install: SECURITY -- authoritative backup manifest is corrupt or names a different transaction."
        }
        $m.status = $s
        Write-TxJsonFile $manifestName $m
        $verified = Read-JsonFile $manifestPath
        if ($null -eq $verified -or
            [string](Get-SkillMeshTxField $verified 'migration_id') -ne $expectedMigrationId -or
            [string](Get-SkillMeshTxField $verified 'status') -ne $s) {
            throw "migrate-legacy-install: SECURITY -- authoritative backup manifest status did not persist."
        }
    }.GetNewClosure()
    $tx = New-SkillMeshTransaction -MigrationId $plan.migration_id `
        -JournalPath (Resolve-TxPath $JOURNAL_FILE) `
        -Status $status -StatusWriter $statusWriter

    $completionPlanBySeq = $ctx.by_seq
    $completionMigrationId = [string]$plan.migration_id
    $validateRollbackCompletion = {
        param($candidateActions, $currentRecords)
        Assert-RecoveryJournal @($currentRecords) $completionPlanBySeq `
            $completionMigrationId 'rolling_back'
        $durableBegins = Get-SkillMeshTxBegunSeqs @($currentRecords)
        $expectedSeqs = @($durableBegins | ForEach-Object { [int]$_ } | Sort-Object)
        $candidateSeqs = @(@($candidateActions) | ForEach-Object {
            [int](Get-SkillMeshTxField $_ 'seq' -1)
        } | Sort-Object -Unique)
        if (($candidateSeqs -join ',') -cne ($expectedSeqs -join ',')) {
            throw "rollback candidate set does not match durable begin authority."
        }
    }.GetNewClosure()

    # A process may stop after the durable completion record flushes but before the
    # manifest status is published. No inverse may run twice in that window: finish
    # the one remaining state transition and leave project bytes untouched.
    if ($status -eq 'rolling_back' -and
        (Test-RecoveryJournalHasRollbackComplete $recoveryRecords)) {
        Set-SkillMeshTxStatus $tx 'rolled_back'
        Write-PreserveDriftAdvisory $plan
        Write-Outcome "migration $($plan.migration_id) ROLLED BACK (durable completion recovered)."
        Complete-Run 'rolled_back' $plan.migration_id 0
    }

    # The undo set is what the journal says was BEGUN. A legacy commit-only record
    # is observational history, not proof that this transaction mutated the path.
    # Intersect with the plan in apply order; rollback then walks it in reverse.
    $begun = Get-SkillMeshTxBegunSeqs $recoveryRecords
    $undoSet = @(@($plan.actions) | Where-Object { $begun.Contains([int]$_.seq) })

    $undo = { param($a) Invoke-ActionUndo $a }
    $failure = Invoke-SkillMeshTxRollback $tx @($undoSet) $undo `
        -ValidateCompletion $validateRollbackCompletion
    if ($null -ne $failure) {
        Write-Diag ("ROLLBACK INCOMPLETE -- $($failure.Exception.Message). The backup is retained at " +
                    "MigrationId $($plan.migration_id).")
        Complete-Run 'failed_incomplete' $plan.migration_id 3
    }
    # Do not remove plan-time-created directories during rollback. Absence at plan
    # time is not durable identity: an operator may create an empty replacement
    # directory while a transaction is interrupted, and there is no byte hash with
    # which this tool can prove that empty directory is its own.
    Write-PreserveDriftAdvisory $plan
    # AUDITED against D2's narrow-claim rule (the second of the two status lines that
    # decision names): "N begun action(s) processed" states only what the undo pass inspected and
    # asserts nothing about paths this tool never mutated, so unlike the shared path's
    # old "restored to its pre-migration state" it needs no rewording. The advisory
    # above carries the preserve-drift disclosure; the exit code stays 0.
    Write-Outcome "migration $($plan.migration_id) ROLLED BACK ($(@($undoSet).Count) begun action(s) processed)."
    Complete-Run 'rolled_back' $plan.migration_id 0
}

function Test-IsEffectivePersonalHome([string]$candidateHome) {
    <#
      The retired root is PROJECT-relative only. Copilot actively discovers
      `~/.copilot/skills`, so treating the effective personal home as a project
      workspace would invert the positional authority on which every retire action
      rests. Compare against all PowerShell/.NET sources because hosts do not agree
      on which one supplies the profile path. Exact equality only: a normal project
      nested beneath the profile remains valid.

      This check is deliberately not used for -Rollback. A transaction created by
      an older unsafe invocation may need rollback to restore personal bytes; new
      planning, Apply, and Resume are the operations that must never acquire or
      continue retirement authority there.
    #>
    $personalCandidates = New-Object 'System.Collections.Generic.List[string]'
    if (-not [string]::IsNullOrWhiteSpace([string]$HOME)) {
        [void]$personalCandidates.Add([string]$HOME)
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$env:USERPROFILE)) {
        [void]$personalCandidates.Add([string]$env:USERPROFILE)
    }
    try {
        $special = [Environment]::GetFolderPath(
            [Environment+SpecialFolder]::UserProfile)
        if (-not [string]::IsNullOrWhiteSpace([string]$special)) {
            [void]$personalCandidates.Add([string]$special)
        }
    } catch {
        # The other two independent host sources remain available. Never turn a
        # read-only classification helper into a profile-path disclosure.
    }

    try {
        $candidateCanonical = (Get-CanonicalRealPath -InputPath $candidateHome).TrimEnd('\', '/')
    } catch {
        # The caller separately validates the project root. If canonical identity
        # cannot be established here, fail closed rather than grant retire authority.
        return $true
    }

    if ($personalCandidates.Count -eq 0) { return $true }
    $identitySourceResolved = $false
    foreach ($personal in @($personalCandidates | Select-Object -Unique)) {
        try {
            $personalFull = ([System.IO.Path]::GetFullPath($personal)).TrimEnd('\', '/')
            if ($candidateHome.Equals($personalFull,
                    [System.StringComparison]::OrdinalIgnoreCase)) {
                return $true
            }
            $personalCanonical = (Get-CanonicalRealPath -InputPath $personalFull).TrimEnd('\', '/')
            $identitySourceResolved = $true
            if ($candidateCanonical.Equals($personalCanonical,
                    [System.StringComparison]::OrdinalIgnoreCase)) {
                return $true
            }
        } catch {
            # A malformed/unresolvable personal-home candidate cannot prove exact
            # equality. Lexical equality was checked before canonicalization.
            continue
        }
    }
    return (-not $identitySourceResolved)
}

# -- Entry point --------------------------------------------------------------

$script:TxDir = ''
$script:BackupAbs = ''
$script:LedgerJson = ''
$script:RunMode = 'dry-run'
if ($Apply) { $script:RunMode = 'apply' }
if ($Resume) { $script:RunMode = 'resume' }
if ($Rollback) { $script:RunMode = 'rollback' }

$modeCount = @($Apply, $Resume, $Rollback | Where-Object { $_ }).Count
if ($modeCount -gt 1) {
    Exit-Blocked 'INVALID_MODE' '-Apply, -Resume, and -Rollback are mutually exclusive.'
}

if ([string]::IsNullOrWhiteSpace($TargetHome)) {
    Exit-Blocked 'INVALID_HOME' '-Home is required (path to the consumer home to migrate).'
}
try {
    $homeLexical = ([System.IO.Path]::GetFullPath($TargetHome)).TrimEnd('\', '/')
} catch {
    Exit-Blocked 'INVALID_HOME' "-Home is not a valid path ($($_.Exception.GetType().Name))."
}
if (-not (Test-Path -LiteralPath $homeLexical -PathType Container)) {
    Exit-Blocked 'INVALID_HOME' '-Home does not exist or is not a directory.'
}
try {
    $script:HomeAbs = (Get-CanonicalRealPath -InputPath $homeLexical).TrimEnd('\', '/')
} catch {
    Exit-Blocked 'INVALID_HOME' '-Home cannot be resolved to a stable project directory.'
}
if (-not (Test-Path -LiteralPath $script:HomeAbs -PathType Container)) {
    Exit-Blocked 'INVALID_HOME' '-Home does not resolve to a directory.'
}
if (-not $Rollback -and (Test-IsEffectivePersonalHome $script:HomeAbs)) {
    Exit-Blocked 'PERSONAL_HOME_UNSUPPORTED' `
        '-ProjectRoot/-Home must name a consumer project workspace, not the effective personal home. Copilot actively discovers ~/.copilot/skills; this migrator has no retirement authority there. Nothing was written. An existing transaction may still be recovered with explicit -Rollback.'
}

# -BackupDir is required in EVERY mode: it locates the transaction folder, and an
# -Apply without it is exactly the unbacked overwrite this command exists to
# replace. Validated here, before any scan, so the refusal is a true no-op.
if ([string]::IsNullOrWhiteSpace($BackupDir)) {
    Exit-Blocked 'BACKUP_DIR_REQUIRED' `
        '-BackupDir is required (an external backup directory OUTSIDE the consumer home). Nothing was written.'
}
try {
    $backupLexical = ([System.IO.Path]::GetFullPath($BackupDir)).TrimEnd('\', '/')
    $backupAbs = (Get-CanonicalRealPath -InputPath $backupLexical).TrimEnd('\', '/')
    $script:BackupAbs = $backupAbs
} catch {
    Exit-Blocked 'BACKUP_DIR_REQUIRED' "-BackupDir is not a valid path ($($_.Exception.GetType().Name))."
}
if ($backupAbs.Equals($script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase) -or
    $backupAbs.StartsWith($script:HomeAbs + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase)) {
    Exit-Blocked 'BACKUP_DIR_INSIDE_HOME' `
        '-BackupDir must be OUTSIDE the consumer home (a backup inside the tree being migrated is not a backup).'
}

if ($Rollback) {
    if (-not (Test-Path -LiteralPath $backupAbs -PathType Container)) {
        Exit-Blocked 'UNKNOWN_TRANSACTION' 'the backup directory does not exist.'
    }
    Invoke-Rollback $backupAbs
}

# Explicit rollback is deliberately independent of the current checkout's
# planning manifest: a valid older transaction must remain recoverable even if
# that file is unavailable or malformed. Every remaining mode plans or resumes
# generated bytes and therefore needs the current manifest.
$manifest = Read-Manifest
$script:ManifestMap = $manifest.skills
$script:KnownProviders = @($manifest.providers)

# Every remaining mode reads generated bytes.
if ([string]::IsNullOrWhiteSpace($DistDir)) {
    Exit-Blocked 'DIST_DIR_REQUIRED' '-DistDir is required (a dist root built by tools/build-distributions.ps1).'
}
$distAbs = ([System.IO.Path]::GetFullPath($DistDir)).TrimEnd('\', '/')
if (-not (Test-Path -LiteralPath $distAbs -PathType Container)) {
    Exit-Blocked 'DIST_DIR_REQUIRED' '-DistDir does not exist or is not a directory.'
}

if ($Resume) {
    if (-not (Test-Path -LiteralPath $backupAbs -PathType Container)) {
        Exit-Blocked 'UNKNOWN_TRANSACTION' 'the backup directory does not exist.'
    }
    Invoke-Resume $backupAbs $distAbs
}

if ($Apply) {
    Invoke-Apply $distAbs $backupAbs
}

Invoke-DryRun $distAbs $backupAbs
