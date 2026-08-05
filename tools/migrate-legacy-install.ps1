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
        `_shared` with no SKILL.md         -> core-holder
        has a SKILL.md                     -> consumer-only
        anything else                      -> foreign
    `managed` trees are migrated (their generated paths are installed over, with
    the pre-image backed up; their STALE marker-bearing files are retired).
    `consumer-only` trees and the `core-holder` are PRESERVED byte-for-byte --
    never overwritten, never retired, never a block -- and are recorded in the
    backup manifest by relative path and SHA-256 ONLY, never payload-copied, so
    private consumer content is not duplicated into a backup it can never need.
    `foreign` BLOCKS before the first mutation.

    OWNERSHIP AUTHORITY IS FILE-CONTENT PROVENANCE, exactly as in the installer:
    Test-SkillMeshProvenance from tools/skill-mesh-provenance.ps1 (dot-sourced,
    never forked) decides whether a file is skill-mesh's to retire. The only
    non-marker files this command ever writes over are the exact target paths of
    the generated distribution -- the legacy adoption this command exists to
    perform -- and every one of those has its pre-image in the backup first.

    ATOMICITY IS NOT IMPLEMENTED HERE. The state machine, append-only journal,
    ordered rollback, and resume live in tools/skill-mesh-transaction.ps1, shared
    with tools/install-skill-mesh.ps1, so the "both profiles or neither" guarantee
    has one implementation.

    PROVIDER VOCABULARY comes from the manifest's own top-level `providers`
    object (never a hardcoded {claude, gpt}); the per-provider discovery root is
    mirrored from install-skill-mesh.ps1's $DISCOVERY_SUBDIR. A manifest provider
    with no known discovery root BLOCKS rather than being silently skipped -- a
    silent skip would be a false-clean migration that half-migrated the home.

.PARAMETER Home
    Consumer home to migrate. Required in every mode. Backed by $TargetHome
    ($HOME is a protected automatic variable and cannot be bound as a parameter).

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
    Exit codes: 0 success; 1 operational failure with the home left clean
    (rollback completed, or nothing was mutated); 2 blocked / unsafe precondition
    / refused incomplete transaction, always PRE-MUTATION; 3 rollback itself
    failed -- the home is mixed and the retained backup is the recovery source.

    ASCII-only, no BOM (PowerShell 5.1 reads a no-BOM .ps1 as ANSI/cp1252).
#>

[CmdletBinding()]
param(
    # NOT [Parameter(Mandatory)]: a mandatory parameter PROMPTS when absent in an
    # interactive host. This command must never prompt, so every requirement is
    # validated manually and exits 2.
    [Alias('Home', 'Destination')]
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
# tests/distributions/test_legacy_migration.py::
# test_every_mutating_primitive_resolves_through_the_choke_point walks every
# git-tracked .ps1 and fails on any violation, so a sixth site cannot appear.

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

      Throws on escape. Returns the verified absolute path, which callers assign to
      a $safe* variable and hand to the filesystem.
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
    if (-not (Test-ContainedInHome $abs)) {
        throw ("migrate-legacy-install: SECURITY -- '$RelPosix' resolves outside the consumer " +
               "home (junction or symlink escape); refusing to $Operation.")
    }
    return $abs
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
    $current = Get-SkillMeshFileSha256 $SafePath
    if ($null -eq $current) { return }
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

function Test-ContainedInHome([string]$absPath) {
    # Re-resolve through the path guard (which FOLLOWS junctions/symlinks) and
    # assert the real path is still inside the home. Used at scan time AND again
    # immediately before every write, so a junction planted on an ancestor between
    # the two cannot redirect a mutation out of the home.
    try {
        $null = Resolve-SafePath -Path $absPath -AllowedRoots @($script:HomeAbs)
        return $true
    } catch {
        return $false
    }
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
    # Ownership authority: the ANCHORED shared parser, never a substring scan.
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
    if ($script:ManifestMap.ContainsKey($name)) { return 'managed' }
    if ($name -eq '_shared' -and (-not $hasSkillMd)) { return 'core-holder' }
    if ($hasSkillMd) { return 'consumer-only' }
    return 'foreign'
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

function Get-RootScan([string]$rootRel) {
    # Classify one discovery-root-shaped tree. Returns
    # @{ blocked; preserve; managed_files } where every entry is a home-relative
    # POSIX path. Purely read-only.
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
                ('an unknown directory: not a manifest skill, no SKILL.md, and not the _shared core-holder. ' +
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
            if (-not (Test-ContainedInHome $f.FullName)) {
                $result.blocked += New-Block 'UNSAFE_LINK' "$childRel/..." `
                    'a file inside this directory resolves outside the consumer home'
                continue
            }
            $rel = ConvertTo-HomeRel $f.FullName
            if ($eligibility -eq 'managed') {
                $result.managed_files += $rel
            } else {
                # consumer-only / core-holder: byte-untouched, recorded by path and
                # hash only, NEVER payload-copied.
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

    # -- Scan the consumer home --
    foreach ($p in @($providerRoots.Keys)) {
        $scan = Get-RootScan $providerRoots[$p]
        $blocked += @($scan.blocked)
        $preserveRels += @($scan.preserve)
        foreach ($r in @($scan.managed_files)) { [void]$managedRels.Add($r) }
    }
    $retiredScan = Get-RootScan $RETIRED_ROOT_REL
    $blocked += @($retiredScan.blocked)
    $preserveRels += @($retiredScan.preserve)
    $retiredManaged = @($retiredScan.managed_files)

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
            if (-not $script:ManifestMap.ContainsKey($skill)) {
                $blocked += New-Block 'FOREIGN_FILE' "$p/$relFromProfile" `
                    ("the supplied distribution contains skill directory '$skill', which is not a record in " +
                     "$MANIFEST_REL; refusing to install an unmanifested tree")
                continue
            }
            $distSkills["$p/$skill"] = $true
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
        foreach ($p in @($providerRoots.Keys)) {
            if (-not (Test-SkillMeshTxMember @($script:ManifestMap[$skill].adapters) $p)) { continue }
            if (-not $distSkills.ContainsKey("$p/$skill")) {
                $blocked += New-Block 'MISSING_PROFILE' "$p/$skill" `
                    ("the manifest declares a '$p' adapter for skill '$skill' but the supplied distribution " +
                     "has no $p profile for it; both profiles must migrate as one transaction")
            }
        }
    }

    # -- Retire set: our OWN superseded generated files. --
    $installRels = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($i in $installs) { [void]$installRels.Add($i.rel_path) }

    $retires = @()
    foreach ($rel in @($retiredManaged)) {
        # The retired .copilot/skills target: every marker-bearing file there is a
        # pre-retarget install Copilot cannot see. A NON-marker file is operator
        # content and is left strictly alone.
        if (Test-FileHasMarker (Resolve-HomeTargetForRead $rel)) { $retires += $rel }
    }
    foreach ($rel in @($managedRels)) {
        if ($installRels.Contains($rel)) { continue }
        # A stale generated file inside a managed skill dir (a skill or file the
        # current distribution no longer emits). Only OUR files are retired; a
        # hand-authored file inside a managed dir is left untouched.
        if (Test-FileHasMarker (Resolve-HomeTargetForRead $rel)) { $retires += $rel }
    }
    $retires = @($retires | Sort-Object -Unique)

    # -- Ledger rewrite --
    $ledgerRel = $LEDGER_NAME
    $ledgerAbs = Resolve-HomeTargetForRead $ledgerRel
    $createdDirs = Get-CreatedDirs $installs
    $ledgerJson = New-LedgerJson $installs $providerRoots $createdDirs (Get-PriorCreatedDirs $ledgerAbs)
    $ledgerPostHash = Get-SkillMeshStringSha256 $ledgerJson

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
        migration_id   = $migrationId
        source_release = (Get-SourceRelease $distAbs)
        consumer_home  = $script:HomeAbs
        backup_dir     = $backupAbs
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
    # never adopted (and therefore never removed by an ownership-safe uninstall).
    $set = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($i in @($installs)) {
        $segments = @($i.rel_path.Split('/'))
        $current = ''
        for ($k = 0; $k -lt $segments.Count - 1; $k++) {
            $current = $(if ($current -eq '') { $segments[$k] } else { "$current/$($segments[$k])" })
            if (-not (Test-Path -LiteralPath (Join-HomePathLexical $current))) { [void]$set.Add($current) }
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
        $dirs = @(Get-SkillMeshTxField $p.Value 'created_dirs' @()) |
            Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }
        $map[$slug] = @($dirs)
    }
    return $map
}

function New-LedgerJson($installs, $providerRoots, $createdDirs, $priorCreatedDirs) {
    # The rewritten ownership ledger. It indexes ONLY migration-installed managed
    # files: no preserved consumer-only skill and no _shared core-holder ever
    # appears here, so a later ownership-safe uninstall cannot delete them.
    # Shape and serialization are byte-compatible with install-skill-mesh.ps1's
    # writer, so its uninstall path reads this ledger unchanged.
    $installsObj = [PSCustomObject]@{}
    foreach ($p in @($providerRoots.Keys)) {
        $subdir = $providerRoots[$p]
        $owned = @(@($installs | Where-Object { $_.provider -eq $p } | ForEach-Object { $_.rel_path }) |
            Sort-Object -Unique)
        $mine = @($createdDirs | Where-Object {
            $_ -eq $subdir -or $_.StartsWith("$subdir/") -or $subdir.StartsWith("$_/") })
        # UNIONED with the prior entry, exactly as install-skill-mesh.ps1 does, so a
        # RERUN produces a byte-identical ledger: the second run creates none of the
        # directories the first one did, and without the union its created_dirs
        # would silently shrink to empty (idempotency broken, and a later
        # ownership-safe uninstall would leave the dirs it made behind).
        $prior = @()
        if ($null -ne $priorCreatedDirs -and $priorCreatedDirs.ContainsKey($p)) {
            $prior = @($priorCreatedDirs[$p])
        }
        $dirs = @(@($mine + $prior) | Sort-Object -Unique)
        $entry = [PSCustomObject]@{
            provider         = $p
            discovery_subdir = $subdir
            owned_files      = @($owned)
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
        if (Test-Path -LiteralPath $abs -PathType Leaf) { $size = (Get-Item -LiteralPath $abs -Force).Length }
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
        migration_id   = $plan.migration_id
        created_utc    = (Get-SkillMeshTxUtcNow)
        source_release = $plan.source_release
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
    $safeTmp = "$safeTarget.$PID.tmp"
    [System.IO.File]::WriteAllText($safeTmp, $json, $UTF8_NO_BOM)
    Move-Item -LiteralPath $safeTmp -Destination $safeTarget -Force
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

function Invoke-ActionMutate($action) {
    switch ($action.action) {
        'preserve' {
            # Audit-only: never mutates, so there is nothing to gate. Its hash is
            # re-verified by post-install verification (Test-PostInstall), which is
            # the only check that covers a preserved tree -- the engine per-action
            # post-hash check sees mutating actions only.
            return
        }
        'backup' {
            $safePayload = Resolve-TxPayloadPath $action.backup_payload
            if ((Get-SkillMeshFileSha256 $safePayload) -eq $action.post_hash) { return }
            # The READ side of the copy is gated too: a redirected source would pull
            # a file from outside the home INTO the backup, corrupting the pre-image
            # that rollback depends on.
            $safeSource = Assert-SafeActionTarget $action 'back it up'
            New-DirectoryFor $safePayload
            Copy-Item -LiteralPath $safeSource -Destination $safePayload -Force
            return
        }
        'retire' {
            # Copy-then-delete, never a bare move: at every instant the bytes exist
            # in at least one place, so a crash between the two is recoverable in
            # either direction. BOTH steps are separate mutation points, so both
            # re-resolve containment immediately before they run.
            $safePayload = Resolve-TxPayloadPath $action.backup_payload
            if ((Get-SkillMeshFileSha256 $safePayload) -ne $action.pre_hash) {
                $safeSource = Assert-SafeActionTarget $action 'retire it'
                New-DirectoryFor $safePayload
                Copy-Item -LiteralPath $safeSource -Destination $safePayload -Force
            }
            $safeTarget = Assert-SafeActionTarget $action 'delete it'
            if (Test-Path -LiteralPath $safeTarget -PathType Leaf) {
                Remove-Item -LiteralPath $safeTarget -Force
            }
            return
        }
        'install' {
            # Gate BEFORE creating the parent chain and again AFTER, because
            # New-DirectoryFor materializes directories that did not exist at the
            # first check and the leaf write is a second mutation point.
            $safeTargetPreCreate = Assert-SafeActionTarget $action 'install over it'
            New-DirectoryFor $safeTargetPreCreate
            $safeTarget = Assert-SafeActionTarget $action 'install over it'
            Copy-Item -LiteralPath $action.source -Destination $safeTarget -Force
            return
        }
        'ledger' {
            $safeTargetPreCreate = Assert-SafeActionTarget $action 'rewrite the ledger'
            New-DirectoryFor $safeTargetPreCreate
            $safeTarget = Assert-SafeActionTarget $action 'rewrite the ledger'
            $safeTmp = "$safeTarget.$PID.tmp"
            [System.IO.File]::WriteAllText($safeTmp, $script:LedgerJson, $UTF8_NO_BOM)
            Move-Item -LiteralPath $safeTmp -Destination $safeTarget -Force
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
            # An action can be in the undo set having only reached `begin` -- the
            # failure that triggered rollback may have happened before its mutation
            # ran, and a retire is the one kind whose payload is produced BY the
            # mutation (installs and the ledger are backed up during `prepared`).
            # If the target still holds its pre-image, nothing moved: a no-op, not a
            # missing-payload error.
            if ([string](Get-HomeRelHash $action.rel_path) -eq [string]$action.pre_hash) {
                return
            }
            $safePayload = Resolve-TxPayloadPath $action.backup_payload
            if (-not (Test-Path -LiteralPath $safePayload -PathType Leaf)) {
                throw "migrate-legacy-install: cannot restore retired '$($action.rel_path)' -- backup payload is missing."
            }
            $safeTarget = Assert-SafeActionTarget $action 'restore it'
            # post_hash for a retire is $null (the target should be ABSENT), so this
            # refuses when another file has since appeared at the retired path.
            Assert-OurBytesAtTarget $safeTarget $action.post_hash $action.rel_path 'restore over'
            New-DirectoryFor $safeTarget
            $safeTarget = Assert-SafeActionTarget $action 'restore it'
            Copy-Item -LiteralPath $safePayload -Destination $safeTarget -Force
            return
        }
        'install' {
            $safeTarget = Assert-SafeActionTarget $action 'undo the install of'
            # ONE rule for BOTH cases. Whether this migration created the file or
            # overwrote an existing one, the bytes there must still be the ones it
            # wrote. Previously only the created-case checked, so the overwrite case
            # silently clobbered a legitimate post-migration edit and still reported
            # rolled_back.
            Assert-OurBytesAtTarget $safeTarget $action.post_hash $action.rel_path 'undo the install of'
            if ($null -eq $action.pre_hash) {
                # Created by this migration: undoing means removing it.
                if (Test-Path -LiteralPath $safeTarget -PathType Leaf) {
                    Remove-Item -LiteralPath $safeTarget -Force
                }
                return
            }
            $safePayload = Resolve-TxPayloadPath $action.backup_payload
            if (-not (Test-Path -LiteralPath $safePayload -PathType Leaf)) {
                throw "migrate-legacy-install: cannot restore overwritten '$($action.rel_path)' -- backup payload is missing."
            }
            New-DirectoryFor $safeTarget
            $safeTarget = Assert-SafeActionTarget $action 'restore it'
            Copy-Item -LiteralPath $safePayload -Destination $safeTarget -Force
            return
        }
        'ledger' {
            $safeTarget = Assert-SafeActionTarget $action 'undo the ledger rewrite of'
            Assert-OurBytesAtTarget $safeTarget $action.post_hash $action.rel_path 'undo the ledger rewrite of'
            if ($null -eq $action.pre_hash) {
                # There was no ledger before this migration, so undoing means
                # removing the one it wrote -- and only while it still holds the
                # bytes it wrote, which the assertion above just proved.
                if (Test-Path -LiteralPath $safeTarget -PathType Leaf) {
                    Remove-Item -LiteralPath $safeTarget -Force
                }
                return
            }
            $safePayload = Resolve-TxPayloadPath $action.backup_payload
            if (-not (Test-Path -LiteralPath $safePayload -PathType Leaf)) {
                throw "migrate-legacy-install: cannot restore the prior ledger -- backup payload is missing."
            }
            Copy-Item -LiteralPath $safePayload -Destination $safeTarget -Force
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
    $current = Get-SkillMeshFileSha256 $targetAbs
    switch ($action.action) {
        'preserve' { return ([string]$current -eq [string]$action.post_hash) }
        'backup' {
            return ((Get-SkillMeshFileSha256 (Resolve-TxPayloadPath $action.backup_payload)) -eq $action.post_hash)
        }
        'retire' {
            # Target gone AND the payload safely holds its bytes.
            if ($null -ne $current) { return $false }
            return ((Get-SkillMeshFileSha256 (Resolve-TxPayloadPath $action.backup_payload)) -eq $action.pre_hash)
        }
    }
    # install / ledger: the generated bytes are already in place.
    return ([string]$current -eq [string]$action.post_hash)
}

# -- Pre-flight ---------------------------------------------------------------

function Test-Preconditions($plan) {
    # Re-validate EVERY action's precondition hash against current on-disk state.
    # Runs in state `prepared`, before the first mutation, so drift since planning
    # aborts as a true no-op.
    # Uniform across every action kind: pre_hash always describes the same thing
    # (the current state of rel_path in the home), so no kind is exempt.
    $drift = @()
    foreach ($a in @($plan.actions)) {
        $current = Get-HomeRelHash $a.rel_path
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
            if ($null -ne $current) { $bad += $a.rel_path }
        } elseif ($a.action -eq 'preserve') {
            if ([string]$current -ne [string]$a.pre_hash) { $bad += $a.rel_path }
        }
    }
    return , @($bad)
}

# -- Transaction discovery ----------------------------------------------------

function Get-TransactionDirs([string]$backupAbs) {
    if (-not (Test-Path -LiteralPath $backupAbs -PathType Container)) { return , @() }
    return , @(Get-ChildItem -LiteralPath $backupAbs -Directory -Force |
        Where-Object { Test-SkillMeshMigrationId $_.Name } | Sort-Object -Property Name)
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
        $manifest = Read-JsonFile (Join-Path $d.FullName $BACKUP_MANIFEST_FILE)
        if ($null -eq $manifest) { continue }
        $plan = Read-JsonFile (Join-Path $d.FullName $PLAN_FILE)
        if ($null -eq $plan) { continue }
        # NOT $home: $HOME is a protected PowerShell automatic variable and
        # assigning to it throws VariableNotWritable (the same trap
        # install-skill-mesh.ps1 documents for its -Home parameter).
        $planHome = [string](Get-SkillMeshTxField $plan 'consumer_home')
        if (-not $planHome.Equals($script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase)) { continue }
        $status = [string](Get-SkillMeshTxField $manifest 'status')
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
        if ($unresolved.status -eq 'failed_incomplete') {
            $remedy = ("Its rollback did NOT complete, so the home is MIXED and neither -Resume nor " +
                       "-Rollback will act on it (both refuse a terminal transaction). Recover " +
                       "MANUALLY from the retained backup payloads under the transaction directory " +
                       "named below, then remove that directory to clear this block.")
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

function Invoke-TransactionRun($plan, [string]$startStatus, [bool]$isResume) {
    # The single apply path, shared by -Apply and -Resume.
    $manifestName = $BACKUP_MANIFEST_FILE
    $statusWriter = {
        param($status)
        $m = Read-JsonFile (Resolve-TxPath $manifestName)
        if ($null -eq $m) { return }
        $m.status = $status
        Write-TxJsonFile $manifestName $m
    }.GetNewClosure()

    $tx = New-SkillMeshTransaction -MigrationId $plan.migration_id `
        -JournalPath (Resolve-TxPath $JOURNAL_FILE) `
        -Status $startStatus -StatusWriter $statusWriter

    $getPre = { param($a) Get-HomeRelHash $a.rel_path }
    $getPost = { param($a) Get-HomeRelHash $a.rel_path }
    $mutate = { param($a) Invoke-ActionMutate $a }
    $undo = { param($a) Invoke-ActionUndo $a }
    $skip = $null
    if ($isResume) { $skip = { param($a) Test-ActionAlreadyApplied $a } }

    $applyError = $null
    try {
        Invoke-SkillMeshTxApply -Transaction $tx -Actions @($plan.actions) `
            -GetPreHash $getPre -Mutate $mutate -GetPostHash $getPost `
            -Undo $undo -ShouldSkip $skip
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
        Write-Diag "the consumer home was restored to its pre-migration state (status $($tx.status))."
        Complete-Run $tx.status $plan.migration_id 1
    }

    # TEST SEAM (inert unless set): corrupt one home-relative path AFTER the engine's
    # per-action loop has committed and BEFORE post-install verification runs. This
    # is the only way to reach Test-PostInstall's failure branch from outside, and it
    # is the only check that covers a `preserve` action -- the engine verifies post
    # hashes for MUTATING actions only, so a preserved consumer-only skill or the
    # _shared core-holder changing mid-transaction is detectable here and nowhere
    # else. See tools/skill-mesh-transaction.ps1's TEST SEAMS note for the
    # convention; like those, it can only affect a process the caller already started.
    $tamper = [Environment]::GetEnvironmentVariable('SKILL_MESH_MIGRATE_TAMPER_AFTER_APPLY')
    if (-not [string]::IsNullOrWhiteSpace($tamper)) {
        $safeTamper = Resolve-HomeTargetForRead $tamper.Trim()
        if ($null -ne $safeTamper -and (Test-Path -LiteralPath $safeTamper -PathType Leaf)) {
            [Console]::Error.WriteLine(
                "migrate-legacy-install: TEST SEAM -- tampering with '$($tamper.Trim())' before post-install verification.")
            [System.IO.File]::AppendAllText($safeTamper, "`n# tampered by test seam`n", $UTF8_NO_BOM)
        }
    }

    $bad = Test-PostInstall $plan
    if (@($bad).Count -gt 0) {
        Write-Diag "post-install verification FAILED for $(@($bad).Count) path(s); rolling back."
        # A `preserve` action has NO backup payload -- by design, so a byte-untouched
        # consumer tree is never copied into the backup (disclosure minimization).
        # The consequence is that if one of those trees is what failed verification,
        # rollback structurally CANNOT restore it, and reporting `rolled_back` would
        # claim a clean home that is actually mixed. This wrapper escalates exactly
        # that case to failed_incomplete (exit 3, backup retained) while leaving every
        # other rollback -- including a later explicit -Rollback, where a consumer's
        # own later edit to their own skill is none of this tool's business --
        # completely unaffected.
        $badSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($b in @($bad)) { [void]$badSet.Add([string]$b) }
        $verifyUndo = {
            param($a)
            Invoke-ActionUndo $a
            if ($a.action -eq 'preserve' -and $badSet.Contains([string]$a.rel_path)) {
                throw ("migrate-legacy-install: preserved path '$($a.rel_path)' changed during " +
                       "the transaction and has no backup payload by design; it cannot be restored.")
            }
        }.GetNewClosure()
        $failure = Invoke-SkillMeshTxRollback $tx @($plan.actions) $verifyUndo
        if ($null -ne $failure) {
            Write-Diag ("ROLLBACK INCOMPLETE -- $($failure.Exception.Message) The backup is retained " +
                        "at MigrationId $($plan.migration_id); recover from it manually.")
            Complete-Run 'failed_incomplete' $plan.migration_id 3
        }
        Complete-Run 'rolled_back' $plan.migration_id 1
    }

    Remove-EmptiedRetiredDirs $plan
    Write-Outcome ("migration $($plan.migration_id) APPLIED " +
                "($(@($plan.actions | Where-Object { $_.action -eq 'install' }).Count) installed, " +
                "$(@($plan.actions | Where-Object { $_.action -eq 'retire' }).Count) retired, " +
                "$(@($plan.actions | Where-Object { $_.action -eq 'preserve' }).Count) preserved).")
    Complete-Run 'applied' $plan.migration_id 0
}

function Remove-EmptiedRetiredDirs($plan) {
    # Cosmetic, post-transaction, and strictly bounded: remove ONLY directories
    # this transaction emptied by retiring their last file, and only while they are
    # empty. Nothing that still holds a file is ever removed, so preserved and
    # untouched operator content always keeps its directory.
    # Collected as home-RELATIVE paths so the removal below can re-resolve each one
    # through the choke point immediately before deleting it, rather than deleting a
    # lexically-derived absolute captured earlier in the run.
    $dirs = @()
    foreach ($a in @($plan.actions | Where-Object { $_.action -eq 'retire' })) {
        $rel = [string]$a.rel_path
        while ($rel.Contains('/')) {
            $rel = $rel.Substring(0, $rel.LastIndexOf('/'))
            if ([string]::IsNullOrWhiteSpace($rel)) { break }
            $dirs += $rel
        }
    }
    # De-duplicate on the PATH, then order deepest-first on a SEPARATE sort.
    # `Sort-Object -Property @{Expression={...}} -Unique` de-duplicates on the
    # CALCULATED key, so two different directories whose names happen to be the same
    # length (e.g. two sibling skill dirs with equal-length names -- ordinary across
    # ~50 manifest names) collapsed to one and the other was silently never cleaned.
    # The sibling helpers Remove-CreatedDirs and Remove-EmptyCreatedDirs already sort
    # by segment count with no -Unique; this now matches them.
    $dirs = @(@($dirs | Sort-Object -Unique) |
        Sort-Object -Property @{ Expression = { ([string]$_ -split '[\\/]').Count } } -Descending)
    foreach ($d in $dirs) {
        $safeDir = Resolve-HomeTargetForRead ([string]$d)
        if ($null -eq $safeDir) { continue }
        if (-not (Test-Path -LiteralPath $safeDir -PathType Container)) { continue }
        if (@(Get-ChildItem -LiteralPath $safeDir -Force).Count -eq 0) {
            Remove-Item -LiteralPath $safeDir -Force
        }
    }
}

function Complete-Run([string]$status, [string]$migrationId, [int]$code) {
    if ($Format -eq 'json') {
        Write-Output (New-ResultDocument $status $migrationId @() | ConvertTo-Json -Depth 6)
    }
    exit $code
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
    $planHome = [string](Get-SkillMeshTxField $plan 'consumer_home')
    if (-not $planHome.Equals($script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase)) {
        Exit-Blocked 'HOME_MISMATCH' "transaction $MigrationId was planned for a different consumer home."
    }
    $planRel = ($plan.source_release | ConvertTo-Json -Depth 6 -Compress)
    $manRel = ($manifest.source_release | ConvertTo-Json -Depth 6 -Compress)
    if ($planRel -ne $manRel) {
        Exit-Blocked 'RELEASE_MISMATCH' "transaction $MigrationId has a plan and backup manifest naming different releases."
    }
    return @{ dir = $txDir; plan = $plan; manifest = $manifest }
}

function Update-ActionSources($plan, [string]$distAbs) {
    # A resume may run from a different -DistDir than the original apply (the
    # release tree can be re-staged), so an install's source is RE-DERIVED from the
    # current -DistDir rather than replayed from the recorded absolute path. The
    # bytes are still pinned: the action's post_hash must match, or the engine's
    # post-mutation verification fails the resume.
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

    if ($status -eq 'applied') {
        Write-Outcome "migration $MigrationId is already applied (no-op)."
        Complete-Run 'applied' $MigrationId 0
    }
    if ($status -eq 'rolled_back') {
        Exit-Blocked 'TRANSACTION_RESOLVED' "migration $MigrationId was rolled back; it cannot be resumed."
    }
    if ($status -eq 'failed_incomplete') {
        Exit-Blocked 'TRANSACTION_RESOLVED' `
            "migration $MigrationId ended failed_incomplete; the home is mixed and requires manual recovery from the retained backup."
    }
    if (-not (Test-SkillMeshTxMember @('prepared', 'applying') $status)) {
        Exit-Blocked 'TRANSACTION_RESOLVED' "migration $MigrationId has an unknown status '$status'."
    }
    Invoke-TransactionRun $plan $status $true
}

function Invoke-Rollback([string]$backupAbs) {
    $ctx = Get-TransactionContext $backupAbs
    $script:TxDir = $ctx.dir
    $plan = $ctx.plan
    $script:LedgerJson = [string](Get-SkillMeshTxField $plan 'ledger_json')
    $status = [string](Get-SkillMeshTxField $ctx.manifest 'status')

    if (Test-SkillMeshTxMember @('rolled_back', 'failed_incomplete') $status) {
        Exit-Blocked 'TRANSACTION_RESOLVED' "migration $MigrationId is already in terminal state '$status'."
    }

    $manifestName = $BACKUP_MANIFEST_FILE
    $statusWriter = {
        param($s)
        $m = Read-JsonFile (Resolve-TxPath $manifestName)
        if ($null -eq $m) { return }
        $m.status = $s
        Write-TxJsonFile $manifestName $m
    }.GetNewClosure()
    $tx = New-SkillMeshTransaction -MigrationId $plan.migration_id `
        -JournalPath (Resolve-TxPath $JOURNAL_FILE) `
        -Status $status -StatusWriter $statusWriter

    # The undo set is what the JOURNAL says was BEGUN -- the authoritative record
    # of what may have mutated a target -- intersected with the plan, in apply
    # order. Invoke-SkillMeshTxRollback then walks it in reverse.
    $begun = Get-SkillMeshTxBegunSeqs (Read-SkillMeshTxJournal (Resolve-TxPath $JOURNAL_FILE))
    $undoSet = @(@($plan.actions) | Where-Object { $begun.Contains([int]$_.seq) })

    $undo = { param($a) Invoke-ActionUndo $a }
    $failure = Invoke-SkillMeshTxRollback $tx @($undoSet) $undo
    if ($null -ne $failure) {
        Write-Diag ("ROLLBACK INCOMPLETE -- $($failure.Exception.Message). The backup is retained at " +
                    "MigrationId $($plan.migration_id).")
        Complete-Run 'failed_incomplete' $plan.migration_id 3
    }
    Remove-EmptyCreatedDirs $plan
    Write-Outcome "migration $($plan.migration_id) ROLLED BACK ($(@($undoSet).Count) action(s) reversed)."
    Complete-Run 'rolled_back' $plan.migration_id 0
}

function Remove-EmptyCreatedDirs($plan) {
    # Rollback removes only directories the migration itself created, and only
    # while empty -- so a pre-existing (operator-owned) directory always survives.
    $dirs = @(@(Get-SkillMeshTxField $plan 'created_dirs' @()) |
        Sort-Object -Property @{ Expression = { ([string]$_ -split '/').Count } } -Descending)
    foreach ($rel in $dirs) {
        if ([string]::IsNullOrWhiteSpace([string]$rel)) { continue }
        $safeDir = Resolve-HomeTargetForRead ([string]$rel)
        if ($null -eq $safeDir) { continue }
        if (-not (Test-Path -LiteralPath $safeDir -PathType Container)) { continue }
        if (@(Get-ChildItem -LiteralPath $safeDir -Force).Count -eq 0) {
            Remove-Item -LiteralPath $safeDir -Force
        }
    }
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
    $script:HomeAbs = ([System.IO.Path]::GetFullPath($TargetHome)).TrimEnd('\', '/')
} catch {
    Exit-Blocked 'INVALID_HOME' "-Home is not a valid path ($($_.Exception.GetType().Name))."
}
if (-not (Test-Path -LiteralPath $script:HomeAbs -PathType Container)) {
    Exit-Blocked 'INVALID_HOME' '-Home does not exist or is not a directory.'
}

# -BackupDir is required in EVERY mode: it locates the transaction folder, and an
# -Apply without it is exactly the unbacked overwrite this command exists to
# replace. Validated here, before any scan, so the refusal is a true no-op.
if ([string]::IsNullOrWhiteSpace($BackupDir)) {
    Exit-Blocked 'BACKUP_DIR_REQUIRED' `
        '-BackupDir is required (an external backup directory OUTSIDE the consumer home). Nothing was written.'
}
try {
    $backupAbs = ([System.IO.Path]::GetFullPath($BackupDir)).TrimEnd('\', '/')
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

$manifest = Read-Manifest
$script:ManifestMap = $manifest.skills
$script:KnownProviders = @($manifest.providers)

if ($Rollback) {
    if (-not (Test-Path -LiteralPath $backupAbs -PathType Container)) {
        Exit-Blocked 'UNKNOWN_TRANSACTION' 'the backup directory does not exist.'
    }
    Invoke-Rollback $backupAbs
}

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
