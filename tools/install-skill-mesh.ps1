<#
.SYNOPSIS
    install-skill-mesh.ps1 -- install a generated host profile into a target home
    WITHOUT making canonical files host-owned, with a ledger-scoped uninstall.

.DESCRIPTION
    Copies one provider's generated discovery tree (produced by
    tools/build-distributions.ps1) into a target home under the host's expected,
    provider-specific discovery location:

        claude -> <Home>/.claude/skills/<skill>/{SKILL.md, core.md}
        gpt    -> <Home>/.github/skills/<skill>/{SKILL.md, core.md}

    ...plus the shared support payload the builder emits at the PROFILE ROOT, as a
    sibling of the skill dirs, so every generated '../_shared/x' reference resolves
    inside the discovery root a consumer home actually has:

        claude -> <Home>/.claude/skills/_shared/<asset>
        gpt    -> <Home>/.github/skills/_shared/<asset>

    (GitHub Copilot CLI discovers project skills from .github/skills, .agents/skills,
    and .claude/skills, plus the personal ~/.copilot/skills; this installer writes the
    GPT profile to .github/skills. The project-relative .copilot/skills target used
    before the Step 43 proof is RETIRED -- Copilot does not discover it.)

    DESTRUCTIVE AUTHORITY = PATH SCOPE + MARKER + RECORDED CURRENT-BYTE HASH.
    Every generated file carries the provenance marker from tools/skill-mesh-provenance.ps1
    (Get-SkillMeshMarker). Every destructive op is gated on the TARGET FILE'S content:
      - A routine overwrite, stale removal, or uninstall delete requires an exact
        match between the current file hash and `owned_file_hashes[rel]`.
      - A legacy/hashless entry grants no destructive authority. An existing target
        byte-identical to the incoming distribution is a no-op and may self-seed the
        hash map; any other mismatch requires explicit backed-up take-ownership.
      - A corrupt ledger deletes nothing. The marker alone never authorizes deletion.

    The ledger (<Home>/.skill-mesh-install.json) is written atomically (temp file +
    rename). Ledger version 1 entries carry an exact `owned_files` /
    `owned_file_hashes` bijection. Missing, malformed, or extra hashes authorize no
    overwrite or removal.

    Containment (runtime/path-guard.ps1 Resolve-SafePath, which follows junctions /
    symlinks) is re-resolved on the target AND its parent immediately BEFORE each
    directory creation and each copy -- not once at scan -- so a junction planted on
    an ancestor between scan and write cannot redirect a write outside the home.

    TRANSACTIONAL install (validate-before-mutate): scan for foreign collisions with
    NO change to the install home; a refusal is a TRUE no-op. On a partial-copy
    failure, a reconciled recovery ledger records only marker-valid candidate files
    that actually exist on disk, so a retry resumes without -Force.

    `created_dirs` remains an audit/back-compat record only. Directory absence at one
    instant is not durable ownership identity, so uninstall NEVER removes directories.

    Source of the generated tree: -DistDir points at a pre-built dist root (containing
    claude/ and/or gpt/). When omitted, the profile is built on the fly into an OS-temp
    staging dir via tools/build-distributions.ps1 and cleaned up on every exit path.

.PARAMETER Provider
    'claude' | 'gpt'. Alias: -Profile.

.PARAMETER Home
    Target install root. Alias: -Destination. Backed by $TargetHome ($HOME is a
    protected automatic variable and cannot be bound as a parameter). Created (and
    tracked as created_dir '.') only when it does not already exist.

.PARAMETER DistDir
    Optional pre-built dist root (containing a <provider>/ subtree).

.PARAMETER Force
    Overwrite AND take ownership of a pre-existing non-marker (foreign) file at ANY
    colliding target path (explicit opt-in, UNSCOPED). This is the blunt instrument
    and is NOT the sanctioned way to adopt an existing consumer _shared/ tree -- use
    -ForceShared for that.

    Every mismatching target adopted through -Force requires -BackupDir.

.PARAMETER ForceShared
    SCOPED take-ownership: overwrite AND take ownership of foreign files ONLY where the
    collision is inside the profile's `_shared/` payload. A foreign collision anywhere
    else still REFUSES the whole install, unchanged. Requires -BackupDir.

    Why the scope exists: a real consumer home holds a hand-authored `_shared/` tree,
    only some of whose files skill-mesh now ships. Adoption must be a per-FILE claim
    over exactly the payload -- never a directory-wide one, and never a licence to
    clobber a colliding SKILL.md somewhere else in the same run.

    The scope is decided on BOTH the source-relative path and the reparse-point-resolved
    target, so a junction planted at <installRoot>/_shared cannot redirect the
    authorization onto a path outside the payload.

.PARAMETER BackupDir
    Directory to write pre-overwrite backups into before any foreign file is taken
    over. Each RUN gets its own subdirectory <BackupDir>/<provider>-<run id>/ (the
    sibling migrator's <BackupDir>/<migration_id>/ precedent) holding the original bytes
    at files/<rel> plus take-ownership-backup.json, which records the provider, a
    non-disclosing home_id, and each rel_path with its pre-overwrite sha256 and size.
    Per-run scoping is what lets a two-profile / two-home cutover share ONE -BackupDir
    without the second run erasing the first run's restore record.

    Mandatory for every mismatching target adopted by -Force or -ForceShared.

.PARAMETER Uninstall
    Remove a previously-installed provider profile (marker- + ledger-gated).

.EXAMPLE
    powershell -File tools\install-skill-mesh.ps1 -Provider claude -Home C:\tmp\home
    powershell -File tools\install-skill-mesh.ps1 -Provider gpt -Home C:\tmp\home -DistDir C:\stage\dist
    powershell -File tools\install-skill-mesh.ps1 -Provider claude -Home C:\tmp\home -Uninstall
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('claude', 'gpt')]
    [Alias('Profile')]
    [string]$Provider,

    # Exposed on the CLI as -Home (and -Destination). The backing variable is
    # $TargetHome, NOT $Home: $HOME is a protected PowerShell automatic variable and
    # cannot be bound as a parameter (VariableNotWritable).
    [Parameter(Mandatory = $true)]
    [Alias('Home', 'Destination')]
    [string]$TargetHome,

    [string]$DistDir = '',

    [switch]$Force,

    [switch]$ForceShared,

    [string]$BackupDir = '',

    [switch]$Uninstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -- Path resolution ----------------------------------------------------------

$TOOLS_DIR = $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $TOOLS_DIR
$BUILD_SCRIPT = Join-Path $TOOLS_DIR 'build-distributions.ps1'
$PATH_GUARD = Join-Path $REPO_ROOT 'runtime\path-guard.ps1'
$PROVENANCE = Join-Path $TOOLS_DIR 'skill-mesh-provenance.ps1'
$TRANSACTION = Join-Path $TOOLS_DIR 'skill-mesh-transaction.ps1'
$DISCOVERY = Join-Path $TOOLS_DIR 'skill-mesh-discovery.ps1'

# Reuse the Step-34 path guard (traversal/junction/symlink rejection). Dot-source
# with no -Path so only its functions load (Resolve-SafePath in this scope).
. $PATH_GUARD
# Shared provenance marker (single source of truth; defines Get-SkillMeshMarker).
. $PROVENANCE
# Shared discovery-root map (single source of truth for the provider -> root shape;
# also dot-sourced by inspect-host-install.ps1 and migrate-legacy-install.ps1).
. $DISCOVERY
# Shared transaction engine (single source of truth for ordered apply + journal +
# post-mutation verification), also dot-sourced by tools/migrate-legacy-install.ps1
# so atomicity mechanics cannot drift between install and migration.
. $TRANSACTION

$UTF8_NO_BOM = New-Object System.Text.UTF8Encoding($false)

# Provider-specific install target subdirectory (relative to Home), POSIX form.
# GPT installs to the real GitHub Copilot CLI project discovery root proven in
# Step 43; the retired project-relative Copilot tree is NOT a Copilot root. The
# literal map lives in tools/skill-mesh-discovery.ps1 (ONE owner, shared with the
# inspector and the migrator) -- see that file for why it is not spelled here.
$DISCOVERY_SUBDIR = Get-SkillMeshDiscoveryRoots

$LEDGER_NAME = '.skill-mesh-install.json'
$WRITE_AHEAD_NAME = '.skill-mesh-install.write-ahead.json'

# -- Small helpers ------------------------------------------------------------

function New-CIStringSet {
    # Comma-wrap the return: a bare `return $set` would let PowerShell UNROLL the
    # (empty) enumerable to nothing, yielding $null at the call site.
    $s = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    return , $s
}

function Get-Field($obj, [string]$name, $default = $null) {
    # StrictMode-safe property read: returns $default when the property is absent (or
    # the container is null) -- so a corrupt/old-shape ledger yields a clean
    # diagnostic path, never a PropertyNotFoundException lockout.
    if ($null -eq $obj) { return $default }
    $p = $obj.PSObject.Properties[$name]
    if ($p) { return $p.Value }
    return $default
}

function Read-FileHead([string]$absPath, [int]$maxBytes = 8192) {
    # Read only the first $maxBytes (UTF-8 decoded). The provenance header is always at
    # the top (optionally right after a small YAML frontmatter), so an unbounded read
    # is unnecessary -- and this is called 2+ times per colliding path.
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
    # Candidate signal: does this file carry a well-formed generated header at an
    # emitter-legal position? The anchored parser rejects a bare token mention and
    # ordinary prose quotation, but cannot prove current-byte authorship: a consumer
    # can retain or reproduce a valid header. Destructive authority needs the
    # separate installed-byte identity repair recorded by Step 65.
    #
    # ASSUMPTION: the generated provenance header lives within the first 8 KB (it is
    # emitted at the very top, or immediately after a small YAML frontmatter, by
    # build-distributions.ps1). If the builder ever moves the header deeper than 8 KB
    # this bound must grow in lockstep, or a genuine generated file would be
    # misclassified as foreign (a reinstall-over-own would then refuse) -- the
    # reinstall-over-own + idempotency tests would catch that regression.
    if (-not (Test-Path -LiteralPath $absPath -PathType Leaf)) { return $false }
    try {
        $head = Read-FileHead $absPath 8192
    } catch {
        return $false
    }
    return (Test-SkillMeshProvenance $head)
}

function Resolve-Contained([string]$path, [string]$homeAbs) {
    # Re-resolve the REAL path (path-guard follows junctions/symlinks) and assert it
    # stays within the install home RIGHT NOW. Throws on escape. Called immediately
    # before each dir-create and each copy to close the write-time TOCTOU.
    return (Resolve-SafePath -Path $path -AllowedRoots @($homeAbs))
}

function Test-SharedPayloadRel([string]$relFromSource) {
    # Is this source-relative path part of the shipped _shared/ payload?
    #
    # Read off the SOURCE tree's own layout (build-distributions.ps1 emits the payload
    # at <profile>/_shared/<asset>), never a list of asset names -- a hand-maintained
    # payload list here would drift from the builder's re-walked closure and would
    # silently start authorizing, or refusing, the wrong files.
    if ([string]::IsNullOrWhiteSpace($relFromSource)) { return $false }
    $segments = @(($relFromSource -replace '\\', '/').Split('/') |
                  Where-Object { -not [string]::IsNullOrEmpty($_) })
    if ($segments.Count -lt 2) { return $false }
    return ($segments[0] -eq '_shared')
}

function Test-UnderPayloadRoot([string]$safeTarget, [string]$payloadRootAbs) {
    # SECOND half of the -ForceShared scope decision, read off the RESOLVED target.
    #
    # Test-SharedPayloadRel above reads the SOURCE spelling ('_shared\x'), which always
    # starts with '_shared' by construction; $safeTarget is the real path AFTER
    # reparse-point resolution. A directory junction at <installRoot>/_shared makes the
    # two disagree -- and authorizing on the source spelling alone took ownership of a
    # file with NO '_shared' segment at all, adopting the operator's own namespace into
    # owned_files (so a later -Uninstall would delete it). One concept, two path
    # spellings, and the security decision must read the one the write lands on.
    if ([string]::IsNullOrWhiteSpace($safeTarget) -or
        [string]::IsNullOrWhiteSpace($payloadRootAbs)) { return $false }
    $prefix = $payloadRootAbs.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    return $safeTarget.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-InstallHomeId([string]$homeAbs, [switch]$Full) {
    # A STABLE, NON-DISCLOSING identifier for an install home: SHA-256
    # over its canonical, case-folded absolute path. It lets one -BackupDir hold restore
    # records for several homes without any of them being mistakable for another, while
    # keeping the manifest free of the operator's absolute path so it can still be
    # pasted into a cutover record or an issue.
    $norm = (Get-CanonicalRealPath -InputPath $homeAbs).TrimEnd('\', '/').ToLowerInvariant()
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hash = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($norm))
    } finally {
        $sha.Dispose()
    }
    $hex = (([System.BitConverter]::ToString($hash)) -replace '-', '').ToLowerInvariant()
    if ($Full) { return $hex }
    return $hex.Substring(0, 16)
}

function Resolve-FreshSharedTarget([string]$rel, [string]$provider, [string]$homeAbs, [string]$payloadRootAbs) {
    $prefix = ([string]$DISCOVERY_SUBDIR[$provider]).TrimEnd('/') + '/_shared/'
    if (-not $rel.StartsWith($prefix, [System.StringComparison]::Ordinal)) {
        throw "install-skill-mesh: SECURITY -- '$rel' is outside lexical _shared scope."
    }
    $fresh = Assert-ProviderTargetDomain $rel $provider $homeAbs
    if (-not (Test-UnderPayloadRoot $fresh $payloadRootAbs)) {
        throw "install-skill-mesh: SECURITY -- '$rel' resolves outside _shared scope."
    }
    return $fresh
}

function Assert-BackupOutsideHome([string]$backupPath, [string]$homeAbs) {
    $backupReal = Get-CanonicalRealPath -InputPath $backupPath
    $homeReal = Get-CanonicalRealPath -InputPath $homeAbs
    $homePrefix = $homeReal.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    if ($backupReal.Equals($homeReal, [System.StringComparison]::OrdinalIgnoreCase) -or
        $backupReal.StartsWith($homePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "install-skill-mesh: -BackupDir must remain OUTSIDE the install home."
    }
}

function Write-ForceBackup($forcePairs, [string]$backupDir, [string]$provider, [string]$homeAbs) {
    # Pre-overwrite backup for every foreign file this run is about to take ownership
    # of: the ORIGINAL BYTES under <backupDir>/files/<rel>, plus a manifest recording
    # each rel_path with its pre-overwrite sha256 and size.
    #
    # Runs during VALIDATE, before a single byte of the install home is touched, so a
    # backup failure leaves the home exactly as it was. Restoring is then a plain copy
    # of <run>/files/<rel> back over <home>/<rel>, verified against the recorded hash.
    #
    # PER-RUN SUBDIRECTORY, following the sibling migrator's <BackupDir>/<migration_id>/
    # precedent. A fixed <BackupDir>/take-ownership-backup.json is overwritten by the
    # NEXT run into the same -BackupDir -- and the two-profile, two-home cutover this
    # flag exists for is exactly two runs. The pre-overwrite BYTES survived under
    # files/, but the rel_path + sha256 + size_bytes rows that make a restore VERIFIABLE
    # were destroyed for the first run, both runs exited 0, and nothing warned. Each run
    # now owns its own directory, so no run can erase another's record.
    $backupAbs = [System.IO.Path]::GetFullPath($backupDir)
    if (-not (Test-Path -LiteralPath $backupAbs)) {
        New-Item -ItemType Directory -Path $backupAbs -Force | Out-Null
    }
    $runLeaf = $provider + '-' + (New-SkillMeshMigrationId)
    $safeRunRoot = Resolve-SafePath -Path (Join-Path $backupAbs $runLeaf) -AllowedRoots @($backupAbs)
    if (-not (Test-Path -LiteralPath $safeRunRoot)) {
        New-Item -ItemType Directory -Path $safeRunRoot -Force | Out-Null
    }
    $filesRoot = Join-Path $safeRunRoot 'files'
    $records = @()
    foreach ($p in $forcePairs) {
        Assert-BackupOutsideHome $backupAbs $homeAbs
        $srcAbs = $p[0]
        $rel = $p[1]
        $expectedPreHash = $p[2]
        if ((Get-SkillMeshFileSha256 $srcAbs) -cne $expectedPreHash) {
            throw "install-skill-mesh: SECURITY -- '$rel' changed before its take-ownership backup; nothing was installed."
        }
        $dest = Join-Path $filesRoot ($rel -replace '/', '\')
        $safeBackupDest = Resolve-SafePath -Path $dest -AllowedRoots @($safeRunRoot)
        $safeBackupDestDir = Split-Path -Parent $safeBackupDest
        if (-not (Test-Path -LiteralPath $safeBackupDestDir)) {
            New-Item -ItemType Directory -Path $safeBackupDestDir -Force | Out-Null
        }
        Copy-Item -LiteralPath $srcAbs -Destination $safeBackupDest -Force
        if ((Get-SkillMeshFileSha256 $safeBackupDest) -cne $expectedPreHash) {
            throw "install-skill-mesh: backup verification failed for '$rel'; nothing was installed."
        }
        $records += [PSCustomObject]@{
            rel_path   = $rel
            sha256     = $expectedPreHash
            size_bytes = (Get-Item -LiteralPath $safeBackupDest).Length
            backup_rel = 'files/' + $rel
        }
    }
    # HOME-RELATIVE rel_paths only -- no absolute install path is recorded, so the
    # manifest can be pasted into a cutover record or an issue without leaking the
    # operator's home. `home_id` is a one-way digest of that path for the same reason:
    # two homes backed up into one -BackupDir must be TELLABLE APART (restoring home
    # two's bytes over home one is the failure this identifier exists to prevent)
    # without either home's path appearing in the artifact.
    $manifest = [PSCustomObject]@{
        tool     = 'install-skill-mesh.ps1'
        kind     = 'take-ownership-backup'
        provider = $provider
        home_id  = (Get-InstallHomeId $homeAbs)
        run_id   = $runLeaf
        files    = @($records)
    }
    $safeManifestPath = Resolve-SafePath -Path (Join-Path $safeRunRoot 'take-ownership-backup.json') `
                                         -AllowedRoots @($safeRunRoot)
    Assert-BackupOutsideHome $safeRunRoot $homeAbs
    $json = ($manifest | ConvertTo-Json -Depth 6)
    [System.IO.File]::WriteAllText($safeManifestPath, $json, (New-Object System.Text.UTF8Encoding($false)))
    # Certificate before authority is consumed: re-read the manifest and every backup
    # payload from the external root. A torn/redirected backup never unlocks overwrite.
    Assert-BackupOutsideHome $safeRunRoot $homeAbs
    $cert = ([System.IO.File]::ReadAllText($safeManifestPath, [System.Text.Encoding]::UTF8) |
        ConvertFrom-Json)
    if ([string](Get-Field $cert 'provider' '') -cne $provider -or
        [string](Get-Field $cert 'home_id' '') -cne (Get-InstallHomeId $homeAbs) -or
        @((Get-Field $cert 'files' @())).Count -ne $records.Count) {
        throw "install-skill-mesh: take-ownership backup certificate verification failed."
    }
    foreach ($row in @($cert.files)) {
        $certFile = Resolve-SafePath -Path (Join-Path $safeRunRoot `
            (([string]$row.backup_rel) -replace '/', '\')) -AllowedRoots @($safeRunRoot)
        if ((Get-SkillMeshFileSha256 $certFile) -cne [string]$row.sha256) {
            throw "install-skill-mesh: take-ownership backup payload certificate failed."
        }
    }
    $script:ForceBackupCertificateRoot = $safeRunRoot
    Write-Host ("install-skill-mesh: took ownership of $($records.Count) foreign file(s); " +
                "pre-overwrite bytes + hashes recorded under backup run '$runLeaf'.")
}

function ConvertTo-PosixRel([string]$absPath, [string]$homeAbs) {
    if ($absPath.Equals($homeAbs, [System.StringComparison]::OrdinalIgnoreCase)) {
        return '.'
    }
    $rel = $absPath.Substring($homeAbs.Length).TrimStart('\', '/')
    return ($rel -replace '\\', '/')
}

function ConvertFrom-PosixRel([string]$rel, [string]$homeAbs) {
    # ONLY the sentinel '.' maps to the home root. A null/empty/whitespace rel is
    # INVALID -> $null (never silently mapped to the home root, which would let a
    # bogus '[null]'/'[""]' ledger entry target the operator's home for deletion).
    if ($rel -eq '.') { return $homeAbs }
    if ([string]::IsNullOrWhiteSpace([string]$rel)) { return $null }
    return (Join-Path $homeAbs ($rel -replace '/', '\'))
}

function Get-ContainedAbs([string]$rel, [string]$homeAbs) {
    # Resolve a (possibly TAMPERED / malformed) ledger-relative entry to an absolute
    # path and assert containment within the install home. Returns $null (skip + warn)
    # on an invalid entry or an escape -- so a hostile '../<sibling>/x' or a bogus
    # null/empty entry is never touched.
    $abs = ConvertFrom-PosixRel $rel $homeAbs
    if ([string]::IsNullOrWhiteSpace([string]$abs)) { return $null }
    try {
        return (Resolve-SafePath -Path $abs -AllowedRoots @($homeAbs))
    } catch {
        [Console]::Error.WriteLine(
            "install-skill-mesh: WARNING -- ledger entry '$rel' resolves outside the " +
            "install home ($homeAbs); skipping (not touching). $($_.Exception.Message)")
        return $null
    }
}

function Resolve-HomeRoot([string]$path) {
    # Absolute form only -- NO creation here. The home dir is created (and tracked)
    # lazily during commit, and only if it did not already exist.
    return [System.IO.Path]::GetFullPath($path)
}

# -- Ledger (index/hint only; atomic write, StrictMode-safe read) -------------

function Get-LedgerPath([string]$homeAbs) {
    return (Join-Path $homeAbs $LEDGER_NAME)
}

function New-EmptyLedger {
    return [PSCustomObject]@{
        tool           = 'skill-mesh'
        ledger_version = 1
        installs       = [PSCustomObject]@{}
    }
}

$LEDGER_VERSION = 1

# Read-Ledger sets this to 'absent' (no ledger file -> never installed), 'corrupt'
# (a ledger file exists but is unparseable / old-shape / wrong version -> tracking
# LOST), or 'ok'. Callers use it to distinguish a quiet no-op from a lost-tracking
# recovery path.
$script:LedgerStatus = 'ok'

function Read-Ledger([string]$homeAbs) {
    $script:LedgerStatus = 'ok'
    $lexicalPath = Get-LedgerPath $homeAbs
    if ((Test-Path -LiteralPath $lexicalPath) -and
        (((Get-Item -LiteralPath $lexicalPath -Force).Attributes -band
          [System.IO.FileAttributes]::ReparsePoint) -ne 0)) {
        throw "install-skill-mesh: REFUSING ledger read -- ledger leaf is a reparse point."
    }
    $path = Resolve-Contained $lexicalPath $homeAbs
    if (-not (Test-Path -LiteralPath $path)) {
        $script:LedgerExpectedHash = $null
        $script:LedgerStatus = 'absent'
        return (New-EmptyLedger)
    }
    try {
        $script:LedgerExpectedHash = Get-SkillMeshFileSha256 $path
        $raw = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
        $parsed = $raw | ConvertFrom-Json
    } catch {
        [Console]::Error.WriteLine(
            "install-skill-mesh: WARNING -- ledger at $path is unparseable (CORRUPT); skill-mesh " +
            "may have installed files that are no longer tracked. $($_.Exception.Message)")
        $script:LedgerStatus = 'corrupt'
        return (New-EmptyLedger)
    }
    $installs = Get-Field $parsed 'installs'
    if ([string](Get-Field $parsed 'tool' '') -cne 'skill-mesh') {
        [Console]::Error.WriteLine(
            "install-skill-mesh: WARNING -- ledger at $path has the wrong tool identity (CORRUPT).")
        $script:LedgerStatus = 'corrupt'
        return (New-EmptyLedger)
    }
    if ($null -eq $installs -or -not ($installs -is [System.Management.Automation.PSCustomObject])) {
        [Console]::Error.WriteLine(
            "install-skill-mesh: WARNING -- ledger at $path is missing a valid 'installs' " +
            "object (old-shape/CORRUPT); tracking is lost.")
        $script:LedgerStatus = 'corrupt'
        return (New-EmptyLedger)
    }
    $ver = Get-Field $parsed 'ledger_version'
    if ($null -eq $ver -or ([string]$ver) -ne ([string]$LEDGER_VERSION)) {
        [Console]::Error.WriteLine(
            "install-skill-mesh: WARNING -- ledger at $path has ledger_version '$ver' " +
            "(expected $LEDGER_VERSION); refusing to trust an unknown schema (treating as CORRUPT).")
        $script:LedgerStatus = 'corrupt'
        return (New-EmptyLedger)
    }
    return $parsed
}

function Write-Ledger([string]$homeAbs, $ledger) {
    # Atomic file publication: write a PROCESS-UNIQUE same-volume temp and rename.
    # The per-home operation lock, not the temp name, prevents read/modify/write lost
    # updates between providers.
    # Re-resolved through the path guard immediately before the write, like every
    # other consumer-home mutation here: the ledger is a file in the install home,
    # so a junction planted on the home between scan and commit would otherwise
    # redirect it.
    $safeLedger = Resolve-Contained (Get-LedgerPath $homeAbs) $homeAbs
    if ((Test-Path -LiteralPath $safeLedger) -and
        (((Get-Item -LiteralPath $safeLedger -Force).Attributes -band
          [System.IO.FileAttributes]::ReparsePoint) -ne 0)) {
        throw "install-skill-mesh: REFUSING ledger write -- ledger leaf became a reparse point."
    }
    $currentLedgerHash = Get-SkillMeshFileSha256 $safeLedger
    if ([string]$currentLedgerHash -cne [string]$script:LedgerExpectedHash) {
        throw "install-skill-mesh: SECURITY -- ledger changed after read; refusing lost update."
    }
    if ((Test-Path -LiteralPath $safeLedger) -and
        -not (Test-Path -LiteralPath $safeLedger -PathType Leaf)) {
        throw "install-skill-mesh: REFUSING ledger write -- destination is not a regular file."
    }
    $safeTmp = "$safeLedger.$PID.$([Guid]::NewGuid().ToString('N')).tmp"
    $json = $ledger | ConvertTo-Json -Depth 8
    try {
        # Test-only fault seam. It deliberately sits after every payload write in
        # the final/recovery publication path, so the write-ahead authority record
        # (published before the first payload mutation) must carry recovery by
        # itself. It is never documented as an operator switch.
        if ([Environment]::GetEnvironmentVariable('SKILL_MESH_INSTALL_TEST_FAIL_LEDGER_PUBLISH') -ceq 'always') {
            throw 'install-skill-mesh: TEST -- injected ledger publication failure.'
        }
        [System.IO.File]::WriteAllText($safeTmp, $json, $UTF8_NO_BOM)
        Move-Item -LiteralPath $safeTmp -Destination $safeLedger -Force
        $script:LedgerExpectedHash = Get-SkillMeshFileSha256 $safeLedger
    } finally {
        if (Test-Path -LiteralPath $safeTmp) { Remove-Item -LiteralPath $safeTmp -Force }
    }
}

function Get-InstallEntry($ledger, [string]$provider) {
    $installs = Get-Field $ledger 'installs'
    return (Get-Field $installs $provider)
}

function Set-InstallEntry($ledger, [string]$provider, $entry) {
    $ledger.installs | Add-Member -NotePropertyName $provider -NotePropertyValue $entry -Force
}

function Remove-InstallEntry($ledger, [string]$provider) {
    if ($ledger.installs.PSObject.Properties[$provider]) {
        $ledger.installs.PSObject.Properties.Remove($provider)
    }
}

function Test-InstallsEmpty($ledger) {
    return (@($ledger.installs.PSObject.Properties).Count -eq 0)
}

function Select-CleanRels($rels) {
    # Drop null/empty/whitespace entries so a ledger can NEVER persist [null] or [""]
    # (a bogus entry would later coerce to '' and, via ConvertFrom-PosixRel, target the
    # home root). Sorted + de-duplicated for a byte-stable ledger.
    # Comma-wrap: a bare `return @(...)` unrolls an EMPTY result to $null, which would
    # persist owned_files/created_dirs as JSON null instead of [] (the empty-collection
    # landmine). `, @(...)` returns the (possibly empty) array intact.
    $clean = @(@($rels) |
        Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } |
        Sort-Object -Unique)
    return , $clean
}

function Assert-ForceBackupCertificate([string]$rel, [string]$expectedHash, [string]$homeAbs) {
    $root = $script:ForceBackupCertificateRoot
    if ([string]::IsNullOrWhiteSpace($root)) { throw "install-skill-mesh: SECURITY -- missing force-backup certificate." }
    Assert-BackupOutsideHome $root $homeAbs
    $manifest = Resolve-SafePath -Path (Join-Path $root 'take-ownership-backup.json') -AllowedRoots @($root)
    $cert = ([System.IO.File]::ReadAllText($manifest, [System.Text.Encoding]::UTF8) | ConvertFrom-Json)
    if ([string](Get-Field $cert 'tool' '') -cne 'install-skill-mesh.ps1' -or
        [string](Get-Field $cert 'kind' '') -cne 'take-ownership-backup' -or
        [string](Get-Field $cert 'provider' '') -cne $Provider -or
        [string](Get-Field $cert 'home_id' '') -cne (Get-InstallHomeId $homeAbs) -or
        [string](Get-Field $cert 'run_id' '') -cne (Split-Path -Leaf $root)) {
        throw "install-skill-mesh: SECURITY -- force-backup certificate identity mismatch."
    }
    $rows = @($cert.files | Where-Object { [string]$_.rel_path -ceq $rel -and [string]$_.sha256 -ceq $expectedHash })
    if ($rows.Count -ne 1) { throw "install-skill-mesh: SECURITY -- force-backup certificate mismatch for '$rel'." }
    $payload = Resolve-SafePath -Path (Join-Path $root (([string]$rows[0].backup_rel) -replace '/', '\')) -AllowedRoots @($root)
    if ((Get-SkillMeshFileSha256 $payload) -cne $expectedHash) {
        throw "install-skill-mesh: SECURITY -- force-backup payload changed for '$rel'."
    }
}

function Get-WriteAheadPath([string]$homeAbs) {
    return (Join-Path $homeAbs $WRITE_AHEAD_NAME)
}

function Get-HashOrNull($value) {
    if ($null -eq $value) { return $null }
    $hash = [string]$value
    if ($hash -cnotmatch '^[0-9a-f]{64}$') { return $null }
    return $hash
}

function Get-WriteAheadActions($record, [string]$homeAbs, [string]$provider) {
    if ($record -isnot [System.Management.Automation.PSCustomObject] -or
        [string](Get-Field $record 'tool' '') -cne 'skill-mesh' -or
        [string](Get-Field $record 'write_ahead_version' '') -cne '1' -or
        [string](Get-Field $record 'provider' '') -cne $provider) {
        throw 'install-skill-mesh: REFUSING write-ahead recovery -- record identity is invalid.'
    }
    $rawActions = Get-Field $record 'actions' $null
    if ($null -eq $rawActions -or -not ($rawActions -is [System.Array])) {
        throw 'install-skill-mesh: REFUSING write-ahead recovery -- actions are missing or malformed.'
    }
    $seen = New-CIStringSet
    $actions = @()
    foreach ($raw in @($rawActions)) {
        if ($raw -isnot [System.Management.Automation.PSCustomObject]) {
            throw 'install-skill-mesh: REFUSING write-ahead recovery -- action is not an object.'
        }
        $rel = [string](Get-Field $raw 'rel_path' '')
        $rawPre = Get-Field $raw 'pre_hash' $null
        $rawPost = Get-Field $raw 'post_hash' $null
        $rawAuthority = Get-Field $raw 'authority_hash' $null
        $pre = Get-HashOrNull $rawPre
        $post = Get-HashOrNull $rawPost
        $authority = Get-HashOrNull $rawAuthority
        if ([string]::IsNullOrWhiteSpace($rel) -or -not $seen.Add($rel) -or
            ($null -ne $rawPre -and $null -eq $pre) -or
            ($null -ne $rawPost -and $null -eq $post) -or
            ($null -ne $rawAuthority -and $null -eq $authority) -or
            ($null -eq $pre -and $null -eq $post)) {
            throw 'install-skill-mesh: REFUSING write-ahead recovery -- action identity is invalid.'
        }
        # This proves both lexical provider scope and real-path containment before
        # recovery ever hashes a candidate payload.
        $null = Assert-ProviderTargetDomain $rel $provider $homeAbs
        $actions += [PSCustomObject]@{
            rel_path = $rel; pre_hash = $pre; post_hash = $post; authority_hash = $authority
        }
    }
    return , @($actions | Sort-Object -Property rel_path)
}

function Write-InstallWriteAhead([string]$homeAbs, $record) {
    # This record is the durable authority between the first payload mutation and
    # publication of the normal ledger. It has a distinct name from the ledger, so a
    # CAS/reparse/permission failure at the ledger cannot retroactively remove the
    # sole recovery authority. It is written atomically before payload work begins.
    $safeRecord = Resolve-Contained (Get-WriteAheadPath $homeAbs) $homeAbs
    if (Test-Path -LiteralPath $safeRecord) {
        $item = Get-Item -LiteralPath $safeRecord -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            -not (Test-Path -LiteralPath $safeRecord -PathType Leaf)) {
            throw 'install-skill-mesh: REFUSING write-ahead publication -- destination is not a regular file.'
        }
        throw 'install-skill-mesh: REFUSING write-ahead publication -- an unfinished recovery record already exists.'
    }
    $safeTmp = "$safeRecord.$PID.$([Guid]::NewGuid().ToString('N')).tmp"
    try {
        [System.IO.File]::WriteAllText($safeTmp, ($record | ConvertTo-Json -Depth 8), $UTF8_NO_BOM)
        Move-Item -LiteralPath $safeTmp -Destination $safeRecord
        # Re-read and validate the complete record before it becomes the only
        # authority for subsequent payload changes.
        $saved = [System.IO.File]::ReadAllText($safeRecord, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
        $null = Get-WriteAheadActions $saved $homeAbs $Provider
    } finally {
        if (Test-Path -LiteralPath $safeTmp) { Remove-Item -LiteralPath $safeTmp -Force }
    }
}

function Remove-InstallWriteAhead([string]$homeAbs) {
    $safeRecord = Resolve-Contained (Get-WriteAheadPath $homeAbs) $homeAbs
    if (-not (Test-Path -LiteralPath $safeRecord)) { return }
    $item = Get-Item -LiteralPath $safeRecord -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        -not (Test-Path -LiteralPath $safeRecord -PathType Leaf)) {
        throw 'install-skill-mesh: REFUSING write-ahead cleanup -- recovery record is not a regular file.'
    }
    Remove-Item -LiteralPath $safeRecord -Force
}

function Test-InstallEntryEquals($left, $right, [string]$provider, [string]$subdir, [string]$homeAbs) {
    $leftHashes = Get-ValidOwnedHashMap $left $provider $subdir $homeAbs
    $rightHashes = Get-ValidOwnedHashMap $right $provider $subdir $homeAbs
    if ($null -eq $leftHashes -or $null -eq $rightHashes) { return $false }
    $leftOwned = @(Get-Field $left 'owned_files' @()) | Sort-Object
    $rightOwned = @(Get-Field $right 'owned_files' @()) | Sort-Object
    if (($leftOwned -join "`n") -cne ($rightOwned -join "`n")) { return $false }
    foreach ($rel in $leftOwned) {
        if ([string](Get-OwnedHash $leftHashes $rel) -cne [string](Get-OwnedHash $rightHashes $rel)) {
            return $false
        }
    }
    return $true
}

function Invoke-InstallWriteAheadRecovery([string]$homeAbs, $ledger) {
    $safeRecord = Resolve-Contained (Get-WriteAheadPath $homeAbs) $homeAbs
    if (-not (Test-Path -LiteralPath $safeRecord)) { return $ledger }
    $item = Get-Item -LiteralPath $safeRecord -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        -not (Test-Path -LiteralPath $safeRecord -PathType Leaf)) {
        throw 'install-skill-mesh: REFUSING write-ahead recovery -- recovery record is not a regular file.'
    }
    try {
        $record = [System.IO.File]::ReadAllText($safeRecord, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
    } catch {
        throw "install-skill-mesh: REFUSING write-ahead recovery -- record is unparseable. $($_.Exception.Message)"
    }
    $actions = Get-WriteAheadActions $record $homeAbs $Provider
    $rawExpectedLedgerHash = Get-Field $record 'expected_ledger_hash' $null
    $expectedLedgerHash = Get-HashOrNull $rawExpectedLedgerHash
    if ($null -ne $rawExpectedLedgerHash -and $null -eq $expectedLedgerHash) {
        throw 'install-skill-mesh: REFUSING write-ahead recovery -- expected ledger hash is malformed.'
    }
    $currentLedgerHash = $script:LedgerExpectedHash
    $createdDirs = @(Get-Field $record 'created_dirs' @())
    if ($null -eq $createdDirs -or -not ($createdDirs -is [System.Array])) {
        throw 'install-skill-mesh: REFUSING write-ahead recovery -- created_dirs is malformed.'
    }

    $recoveredRels = @()
    $recoveredHashes = @{}
    $hasPostMutation = $false
    foreach ($action in $actions) {
        $rel = [string]$action.rel_path
        $target = Assert-ProviderTargetDomain $rel $Provider $homeAbs
        $pre = $action.pre_hash
        $post = $action.post_hash
        $authority = $action.authority_hash
        if (-not (Test-Path -LiteralPath $target)) {
            if ($null -ne $pre -and $null -ne $post) {
                throw "install-skill-mesh: REFUSING write-ahead recovery -- '$rel' disappeared outside its recorded transition."
            }
            if ($null -ne $pre -and $null -eq $post) { $hasPostMutation = $true }
            continue
        }
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
            throw "install-skill-mesh: REFUSING write-ahead recovery -- '$rel' is no longer a regular file."
        }
        $actual = Get-SkillMeshFileSha256 $target
        if ($null -ne $post -and $actual -ceq [string]$post) {
            if (-not (Test-FileHasMarker $target)) {
                throw "install-skill-mesh: REFUSING write-ahead recovery -- '$rel' post-state lacks provenance."
            }
            $recoveredRels += $rel
            $recoveredHashes[$rel] = [string]$post
            if ($null -eq $pre -or [string]$pre -cne [string]$post) { $hasPostMutation = $true }
        } elseif ($null -ne $pre -and $actual -ceq [string]$pre) {
            # A backed -Force target can remain at its operator-owned preimage
            # when interruption happened before its replacement. Its observed hash
            # proves only that it was not changed; `authority_hash` is the old
            # durable ledger identity, and is deliberately null for a new foreign
            # adoption so recovery cannot baseline it as ours.
            if ($null -ne $authority) {
                $recoveredRels += $rel
                $recoveredHashes[$rel] = [string]$authority
            }
        } else {
            throw "install-skill-mesh: REFUSING write-ahead recovery -- '$rel' changed outside its recorded transition."
        }
    }
    $subdir = [string]$DISCOVERY_SUBDIR[$Provider]
    $recoveredEntry = New-InstallEntry $Provider $subdir $recoveredRels $createdDirs $recoveredHashes

    # The process may have stopped after publishing the record but before touching a
    # payload. In that exact pre-state there is no recovery ledger to publish; drop
    # the unused record and preserve the original ledger byte-for-byte.
    if (-not $hasPostMutation) {
        Remove-InstallWriteAhead $homeAbs
        return $ledger
    }

    # If the normal ledger already contains the precise recovered authority (for
    # example the prior final write succeeded but cleanup was interrupted), the
    # record is no longer sole authority and may be retired without another ledger
    # write. Otherwise only the pre-recorded ledger revision may be replaced.
    if ([string]$currentLedgerHash -cne [string]$expectedLedgerHash) {
        if ($script:LedgerStatus -eq 'ok' -and
            (Test-InstallEntryEquals (Get-InstallEntry $ledger $Provider) $recoveredEntry $Provider $subdir $homeAbs)) {
            Remove-InstallWriteAhead $homeAbs
            return $ledger
        }
        throw 'install-skill-mesh: REFUSING write-ahead recovery -- normal ledger changed outside the recorded operation.'
    }
    Set-InstallEntry $ledger $Provider $recoveredEntry
    Write-Ledger $homeAbs $ledger
    if (-not (Test-InstallEntryEquals (Get-InstallEntry $ledger $Provider) $recoveredEntry $Provider $subdir $homeAbs)) {
        throw 'install-skill-mesh: SECURITY -- recovered ledger authority did not verify after publication.'
    }
    Remove-InstallWriteAhead $homeAbs
    return $ledger
}

function Assert-ProviderTargetDomain([string]$rel, [string]$provider, [string]$homeAbs) {
    if ($null -ne $script:PinnedHomeReal -and
        (Get-CanonicalRealPath -InputPath $homeAbs) -cne $script:PinnedHomeReal) {
        throw "install-skill-mesh: SECURITY -- pinned Home identity changed before mutation."
    }
    $subdir = [string]$DISCOVERY_SUBDIR[$provider]
    $prefix = $subdir.TrimEnd('/') + '/'
    if ([string]::IsNullOrWhiteSpace($rel) -or $rel.Contains('\') -or
        -not $rel.StartsWith($prefix, [System.StringComparison]::Ordinal)) {
        throw "install-skill-mesh: SECURITY -- '$rel' is outside provider '$provider' lexical discovery domain."
    }
    $target = Get-ContainedAbs $rel $homeAbs
    if ($null -eq $target) { throw "install-skill-mesh: SECURITY -- invalid provider target '$rel'." }
    $domain = Get-CanonicalRealPath -InputPath (Join-Path $homeAbs ($subdir -replace '/', '\'))
    $domainPrefix = $domain.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    if (-not $target.StartsWith($domainPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "install-skill-mesh: SECURITY -- '$rel' resolves outside provider '$provider' discovery domain."
    }
    foreach ($other in @($DISCOVERY_SUBDIR.Keys)) {
        if ([string]$other -ceq $provider) { continue }
        $otherDomain = Get-CanonicalRealPath -InputPath `
            (Join-Path $homeAbs ($DISCOVERY_SUBDIR[$other] -replace '/', '\'))
        $otherPrefix = $otherDomain.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
        # Reject both direct target reachability and overlapping/aliased provider roots,
        # even when their leaves do not exist yet (canonicalization resolves ancestors).
        if ($target.StartsWith($otherPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
            $domain.StartsWith($otherPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
            $otherDomain.StartsWith($domainPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
            $domain.Equals($otherDomain, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "install-skill-mesh: SECURITY -- provider discovery domains overlap or alias."
        }
        # A child junction under the other provider can make this target reachable
        # without making the two roots themselves overlap. Walk ordinary directories
        # only; inspect reparse leaves but never recurse through them (bounded, no loop).
        if (Test-Path -LiteralPath $otherDomain -PathType Container) {
            $pending = New-Object System.Collections.Generic.Stack[string]
            $pending.Push($otherDomain)
            while ($pending.Count -gt 0) {
                $dir = $pending.Pop()
                foreach ($child in @(Get-ChildItem -LiteralPath $dir -Force)) {
                    if (($child.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                        $resolvedChild = Get-CanonicalRealPath -InputPath $child.FullName
                        $resolvedPrefix = $resolvedChild.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
                        if ($target.Equals($resolvedChild, [System.StringComparison]::OrdinalIgnoreCase) -or
                            $target.StartsWith($resolvedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                            throw "install-skill-mesh: SECURITY -- target '$rel' is reachable through another provider's child reparse point."
                        }
                    } elseif ($child.PSIsContainer) {
                        $pending.Push($child.FullName)
                    }
                }
            }
        }
    }
    return $target
}

function Get-ValidOwnedHashMap($entry, [string]$provider = '', [string]$expectedSubdir = '', [string]$homeAbs = '') {
    # Authority is all-or-nothing: owned_files and owned_file_hashes must be an exact
    # bijection. A partially useful-looking legacy/tampered map grants no destructive
    # authority, because selecting only its convenient rows would silently bless an
    # ambiguous ledger shape.
    if ($null -eq $entry) { return $null }
    if (-not [string]::IsNullOrWhiteSpace($provider)) {
        if ([string](Get-Field $entry 'provider' '') -cne $provider -or
            [string](Get-Field $entry 'discovery_subdir' '') -cne $expectedSubdir) {
            return $null
        }
    }
    $owned = Get-Field $entry 'owned_files' $null
    $map = Get-Field $entry 'owned_file_hashes' $null
    if ($null -eq $owned -or -not ($owned -is [System.Array]) -or
        $null -eq $map -or -not ($map -is [System.Management.Automation.PSCustomObject])) {
        return $null
    }
    $ownedList = @($owned)
    $props = @($map.PSObject.Properties)
    if ($ownedList.Count -ne $props.Count) { return $null }
    $seen = New-CIStringSet
    foreach ($relObj in $ownedList) {
        $rel = [string]$relObj
        if ([string]::IsNullOrWhiteSpace($rel) -or -not $seen.Add($rel)) { return $null }
        $prop = $map.PSObject.Properties[$rel]
        if ($null -eq $prop -or ([string]$prop.Name) -cne $rel) { return $null }
        $hash = [string]$prop.Value
        if ($hash -cnotmatch '^[0-9a-f]{64}$') { return $null }
    }
    foreach ($prop in $props) {
        if (-not $seen.Contains([string]$prop.Name)) { return $null }
    }
    if (-not [string]::IsNullOrWhiteSpace($homeAbs)) {
        foreach ($relObj in $ownedList) {
            try { $null = Assert-ProviderTargetDomain ([string]$relObj) $provider $homeAbs }
            catch { return $null }
        }
    }
    return $map
}

function Get-OwnedHash($validMap, [string]$rel) {
    if ($null -eq $validMap -or [string]::IsNullOrWhiteSpace($rel)) { return $null }
    $p = $validMap.PSObject.Properties[$rel]
    if ($null -eq $p -or ([string]$p.Name) -cne $rel) { return $null }
    return [string]$p.Value
}

function New-OwnedHashMap($ownedRels, $hashes) {
    $map = [PSCustomObject]@{}
    foreach ($rel in $ownedRels) {
        $hash = $null
        if ($hashes -is [System.Collections.IDictionary]) {
            if ($hashes.Contains($rel)) { $hash = [string]$hashes[$rel] }
        } elseif ($null -ne $hashes) {
            $p = $hashes.PSObject.Properties[$rel]
            if ($p) { $hash = [string]$p.Value }
        }
        if ($hash -cnotmatch '^[0-9a-f]{64}$') {
            throw "install-skill-mesh: internal error -- missing/invalid owned hash for '$rel'."
        }
        $map | Add-Member -NotePropertyName $rel -NotePropertyValue $hash
    }
    return $map
}

function New-InstallEntry([string]$provider, [string]$subdir, $ownedRels, $createdDirs, $ownedHashes) {
    $cleanOwned = @(@($ownedRels) |
        Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } |
        Sort-Object -Unique)
    return [PSCustomObject]@{
        provider         = $provider
        discovery_subdir = $subdir
        owned_files      = $cleanOwned
        owned_file_hashes = New-OwnedHashMap $cleanOwned $ownedHashes
        created_dirs     = Select-CleanRels $createdDirs
    }
}

function New-TrackedDir([string]$absDir, [string]$homeAbs, $createdSet) {
    # Create $absDir and every missing ancestor down from the home root, recording in
    # $createdSet ONLY segments this call actually creates (only-own-what-you-create).
    # The caller re-resolves containment on $absDir BEFORE calling this.
    # Belt-and-suspenders: Invoke-Install already ensures the home exists (and records
    # '.') before the copy loop, so this branch normally never fires; it is kept so the
    # helper stays correct if ever called on a not-yet-created home.
    if (-not (Test-Path -LiteralPath $homeAbs)) {
        New-Item -ItemType Directory -Path $homeAbs -Force | Out-Null
        [void]$createdSet.Add('.')
    }
    if (Test-Path -LiteralPath $absDir) { return }
    $rel = ConvertTo-PosixRel $absDir $homeAbs
    $segments = $rel.Split('/', [System.StringSplitOptions]::RemoveEmptyEntries)
    $current = $homeAbs
    foreach ($seg in $segments) {
        $current = Join-Path $current $seg
        # Re-resolve containment on EACH intermediate segment (not just the leaf) so a
        # junction swapped onto an ancestor between segment creations cannot redirect a
        # dir-create outside the home.
        $null = Resolve-SafePath -Path $current -AllowedRoots @($homeAbs)
        if (-not (Test-Path -LiteralPath $current)) {
            New-Item -ItemType Directory -Path $current -Force | Out-Null
            [void]$createdSet.Add((ConvertTo-PosixRel $current $homeAbs))
        }
    }
}

function Assert-OwnedFilesRemovable([string]$homeAbs, $entry, $removalHashes, $forcedRels, [string]$payloadRootAbs) {
    if ($null -eq $entry -or $null -eq $removalHashes) {
        throw "install-skill-mesh: REFUSING uninstall -- owned_file_hashes is missing, malformed, or inconsistent; no files were deleted."
    }
    foreach ($rel in @(Get-Field $entry 'owned_files' @())) {
        $abs = Assert-ProviderTargetDomain ([string]$rel) $Provider $homeAbs
        if (-not (Test-Path -LiteralPath $abs)) { continue }
        $expected = [string]$removalHashes[[string]$rel]
        $actual = Get-SkillMeshFileSha256 $abs
        $forced = $forcedRels.Contains([string]$rel)
        if ($forced -and $ForceShared -and -not $Force) {
            $abs = Resolve-FreshSharedTarget ([string]$rel) $Provider $homeAbs $payloadRootAbs
        }
        if ((-not $forced -and -not (Test-FileHasMarker $abs)) -or $actual -cne $expected) {
            throw ("install-skill-mesh: REFUSING uninstall -- '$rel' no longer matches " +
                   "its recorded installed-byte hash; no files were deleted.")
        }
    }
}

function Remove-OwnedFiles([string]$homeAbs, $entry, $removalHashes, $forcedRels, [string]$payloadRootAbs) {
    foreach ($rel in @(Get-Field $entry 'owned_files' @())) {
        $abs = Assert-ProviderTargetDomain ([string]$rel) $Provider $homeAbs
        if (-not (Test-Path -LiteralPath $abs)) { continue }
        $safeTarget = Resolve-Contained $abs $homeAbs
        $expected = [string]$removalHashes[[string]$rel]
        $forced = $forcedRels.Contains([string]$rel)
        if ($forced) {
            Assert-ForceBackupCertificate ([string]$rel) $expected $homeAbs
            if ($ForceShared -and -not $Force) {
                $safeTarget = Resolve-FreshSharedTarget ([string]$rel) $Provider $homeAbs $payloadRootAbs
            }
        }
        if ((Get-SkillMeshFileSha256 $safeTarget) -cne $expected -or
            (-not $forced -and -not (Test-FileHasMarker $safeTarget))) {
            throw ("install-skill-mesh: SECURITY -- '$rel' changed after uninstall " +
                   "preflight; stopping before deleting the changed file.")
        }
        Remove-Item -LiteralPath $safeTarget -Force
    }
}

function Resolve-SourceProfileDir([string]$provider) {
    # Returns (sourceDir, tempStageDir-or-empty). When -DistDir is supplied use its
    # <provider>/ subtree; otherwise build the profile into an OS-temp staging dir.
    # On ANY on-the-fly build/validation failure the stage dir is cleaned before the
    # error propagates (no orphaned %TEMP%\skill-mesh-stage-* dir).
    if (-not [string]::IsNullOrWhiteSpace($DistDir)) {
        $src = Join-Path ([System.IO.Path]::GetFullPath($DistDir)) $provider
        if (-not (Test-Path -LiteralPath $src)) {
            throw "install-skill-mesh: profile '$provider' not found under -DistDir: $src"
        }
        return @($src, '')
    }
    $stage = Join-Path ([System.IO.Path]::GetTempPath()) ("skill-mesh-stage-" + [System.Guid]::NewGuid().ToString('N'))
    try {
        # Spawn the builder in a SEPARATE process: its terminal 'exit 0' would
        # otherwise terminate this parent script (same-process 'exit' semantics). A
        # child process isolates its exit code into $LASTEXITCODE.
        $psExe = (Get-Process -Id $PID).Path
        if ([string]::IsNullOrWhiteSpace($psExe)) { $psExe = 'powershell' }
        & $psExe -NoProfile -NonInteractive -File $BUILD_SCRIPT -Provider $provider -OutputDir $stage | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "install-skill-mesh: build-distributions.ps1 failed (exit $LASTEXITCODE)"
        }
        $src = Join-Path $stage $provider
        if (-not (Test-Path -LiteralPath $src)) {
            throw "install-skill-mesh: build produced no '$provider' profile at $src"
        }
        return @($src, $stage)
    } catch {
        if (Test-Path -LiteralPath $stage) {
            Remove-Item -LiteralPath $stage -Recurse -Force
        }
        throw
    }
}

# -- Uninstall ----------------------------------------------------------------

function Invoke-MarkerFallbackUninstall([string]$homeAbs) {
    # A marker says only "generated-looking". With no durable installed hash there is
    # no current-byte identity to compare, so corrupt-ledger uninstall fails closed.
    throw ("install-skill-mesh: REFUSING uninstall -- ledger tracking is corrupt or " +
           "old-shape and no trusted owned_file_hashes authority remains. Nothing was deleted.")
}

function Invoke-Uninstall([string]$homeAbs) {
    $ledger = Read-Ledger $homeAbs
    # A prior install may have changed payload bytes but been interrupted before
    # normal-ledger publication. Reconcile its write-ahead authority before any
    # uninstall decision so stale pre-ledger hashes can never drive deletion.
    $ledger = Invoke-InstallWriteAheadRecovery $homeAbs $ledger
    $status = $script:LedgerStatus
    $entry = Get-InstallEntry $ledger $Provider
    if ($null -eq $entry) {
        if ($status -eq 'corrupt') {
            # Do NOT report a clean no-op -- tracking is lost, files may remain.
            Invoke-MarkerFallbackUninstall $homeAbs
            return
        }
        Write-Host "install-skill-mesh: provider '$Provider' is not installed under $homeAbs (nothing to remove)."
        return
    }
    $subdir = $DISCOVERY_SUBDIR[$Provider]
    $validHashes = Get-ValidOwnedHashMap $entry $Provider $subdir $homeAbs
    $hadValidHashes = $null -ne $validHashes
    if ($null -eq $validHashes) {
        if (-not $Force -and -not $ForceShared) {
            throw "install-skill-mesh: REFUSING uninstall -- owned_file_hashes is missing, malformed, or inconsistent. Nothing was deleted."
        }
        if ([string](Get-Field $entry 'provider' '') -cne $Provider -or
            [string](Get-Field $entry 'discovery_subdir' '') -cne $subdir -or
            [string]::IsNullOrWhiteSpace($BackupDir)) {
            throw "install-skill-mesh: REFUSING forced uninstall -- legacy entry identity and external -BackupDir are required."
        }
        $ownedHints = @(Get-Field $entry 'owned_files' @())
        $hintSeen = New-CIStringSet
        foreach ($hint in $ownedHints) {
            if ([string]::IsNullOrWhiteSpace([string]$hint) -or
                -not $hintSeen.Add([string]$hint)) {
                throw "install-skill-mesh: REFUSING forced uninstall -- malformed legacy owned_files hints."
            }
            $null = Assert-ProviderTargetDomain ([string]$hint) $Provider $homeAbs
        }
        $validHashes = [PSCustomObject]@{}
    }
    $payloadRootAbs = Join-Path (Get-CanonicalRealPath -InputPath `
        (Join-Path $homeAbs ($subdir -replace '/', '\'))) '_shared'
    $forcedRels = New-CIStringSet
    $removalHashes = @{}
    $forcePairs = @()
    foreach ($rel in @(Get-Field $entry 'owned_files' @())) {
        $rel = [string]$rel
        $abs = Assert-ProviderTargetDomain $rel $Provider $homeAbs
        if (-not (Test-Path -LiteralPath $abs)) { continue }
        $recorded = Get-OwnedHash $validHashes $rel
        $actual = Get-SkillMeshFileSha256 $abs
        if ($null -ne $recorded -and (Test-FileHasMarker $abs) -and $actual -ceq $recorded) {
            $removalHashes[$rel] = $recorded
            continue
        }
        $sharedAllowed = $false
        if ($ForceShared) {
            try { $null = Resolve-FreshSharedTarget $rel $Provider $homeAbs $payloadRootAbs; $sharedAllowed = $true }
            catch { $sharedAllowed = $false }
        }
        if (-not $Force -and -not $sharedAllowed) {
            throw ("install-skill-mesh: REFUSING uninstall -- '$rel' no longer matches " +
                   "its recorded installed-byte hash; no files were deleted.")
        }
        if ([string]::IsNullOrWhiteSpace($BackupDir)) {
            throw "install-skill-mesh: REFUSING forced uninstall -- -BackupDir is required. Nothing was deleted."
        }
        [void]$forcedRels.Add($rel)
        $removalHashes[$rel] = $actual
        $forcePairs += , @($abs, $rel, $actual)
    }
    if ($forcePairs.Count -gt 0) {
        Assert-BackupOutsideHome $BackupDir $homeAbs
        Write-ForceBackup $forcePairs $BackupDir $Provider $homeAbs
    }
    # Complete authorization preflight before the first deletion. A mismatch is a
    # true no-op, including byte-identical ledger preservation.
    Assert-OwnedFilesRemovable $homeAbs $entry $removalHashes $forcedRels $payloadRootAbs
    try {
        Remove-OwnedFiles $homeAbs $entry $removalHashes $forcedRels $payloadRootAbs
    } catch {
        if (-not $hadValidHashes) {
            # Legacy/hashless forced recovery retains the original ledger bytes. Ghost
            # hints are non-authoritative and safe; a backed retry skips absent paths.
            throw
        }
        # Reconcile: rewrite the entry to only the owned files that STILL exist, so a
        # retry resumes cleanly; surface a clean diagnostic rather than a torn state.
        $remaining = @()
        foreach ($rel in @(Get-Field $entry 'owned_files' @())) {
            $abs = Assert-ProviderTargetDomain ([string]$rel) $Provider $homeAbs
            if ($null -ne $abs -and (Test-Path -LiteralPath $abs)) { $remaining += $rel }
        }
        $reconciledHashes = @{}
        foreach ($rel in $remaining) {
            $reconciledHashes[$rel] = Get-OwnedHash $validHashes ([string]$rel)
        }
        $reconciled = New-InstallEntry $Provider $subdir $remaining `
            @(Get-Field $entry 'created_dirs' @()) $reconciledHashes
        Set-InstallEntry $ledger $Provider $reconciled
        Write-Ledger $homeAbs $ledger
        throw
    }
    # Update the ledger. Directories deliberately remain: created_dirs is audit data,
    # not durable deletion authority.
    Remove-InstallEntry $ledger $Provider
    if (Test-InstallsEmpty $ledger) {
        $safeLedger = Resolve-Contained (Get-LedgerPath $homeAbs) $homeAbs
        if (Test-Path -LiteralPath $safeLedger) {
            if ((Get-SkillMeshFileSha256 $safeLedger) -cne $script:LedgerExpectedHash) {
                throw "install-skill-mesh: SECURITY -- ledger changed before removal; refusing lost update."
            }
            Remove-Item -LiteralPath $safeLedger -Force
            $script:LedgerExpectedHash = $null
        }
    } else {
        Write-Ledger $homeAbs $ledger
    }
    Write-Host "install-skill-mesh: uninstalled '$Provider' from $homeAbs."
}

# -- Install (transactional: validate -> commit) ------------------------------

function Invoke-Install([string]$homeAbs) {
    $script:ForceBackupCertificateRoot = $null
    $ledger = Read-Ledger $homeAbs
    # Consume a durable predecessor record before deriving normal overwrite/stale
    # authority. This makes a plain retry converge without -Force after a final
    # ledger publication failure.
    $ledger = Invoke-InstallWriteAheadRecovery $homeAbs $ledger
    $prior = Get-InstallEntry $ledger $Provider
    $subdir = $DISCOVERY_SUBDIR[$Provider]
    # Prior paths scope candidates. Only a complete valid hash map grants authority.
    $priorOwnedRel = if ($null -ne $prior) { @(Get-Field $prior 'owned_files' @()) } else { @() }
    $priorOwnedHashes = Get-ValidOwnedHashMap $prior $Provider $subdir $homeAbs
    $priorDirs = if ($null -ne $prior) { @(Get-Field $prior 'created_dirs' @()) } else { @() }

    $stageDir = ''
    try {
        # ================= VALIDATE (no change to the install home) =============
        $resolved = Resolve-SourceProfileDir $Provider
        $sourceDir = $resolved[0]
        $stageDir = $resolved[1]

        $installRoot = Join-Path $homeAbs ($subdir -replace '/', '\')
        $srcFiles = @(Get-ChildItem -LiteralPath $sourceDir -Recurse -File | Sort-Object -Property FullName)

        if (-not [string]::IsNullOrWhiteSpace($BackupDir)) {
            # The backup must survive the thing it is a backup OF. A -BackupDir inside
            # the install home would be an install target's neighbour: subject to the
            # same stale-removal and uninstall passes, and restorable only from inside
            # the tree it exists to undo.
            #
            # CANONICALIZED on both sides (Get-CanonicalRealPath follows junctions and
            # symlinks), not a GetFullPath string compare: every other containment check
            # in this file resolves reparse points precisely because a lexical compare
            # walks straight through one. A -BackupDir spelled as a junction OUTSIDE the
            # home whose target is INSIDE it passed the string test and landed the
            # backup inside the tree it exists to undo.
            $backupProbe = Get-CanonicalRealPath -InputPath $BackupDir
            $homeReal = Get-CanonicalRealPath -InputPath $homeAbs
            $homePrefix = $homeReal.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
            if ($backupProbe.Equals($homeReal, [System.StringComparison]::OrdinalIgnoreCase) -or
                $backupProbe.StartsWith($homePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                throw ("install-skill-mesh: -BackupDir must be OUTSIDE the install home; " +
                       "a backup stored inside the tree it protects is not a restore path.")
            }
        }

        # The ONE real path -ForceShared may take ownership under. Ancestors are
        # canonicalized (a junction on '.claude' or the home itself is legitimate and
        # must not de-authorize the payload), but the '_shared' leaf is appended
        # LITERALLY -- resolving it would follow a junction planted AT the payload root
        # and hand the flag's authorization to whatever it points at.
        $payloadRootAbs = Join-Path (Get-CanonicalRealPath -InputPath $installRoot) '_shared'

        $pairs = @()          # each: @(srcFull, safeTarget, rel, sourceHash)
        $foreign = @()
        # Home-relative rels this run is permitted to overwrite DESPITE being foreign.
        # Computed once here so the pre-scan refusal and the TOCTOU guard inside the
        # copy loop cannot disagree about what was authorized.
        $forceRels = New-CIStringSet
        $forcePairs = @()     # each: @(safeTarget, rel, preHash) -- backup set
        $forcePreHashes = @{}
        $routinePreHashes = @{}
        $exactIncomingRels = New-CIStringSet
        $producedRels = New-CIStringSet
        foreach ($f in $srcFiles) {
            if (-not (Test-FileHasMarker $f.FullName)) {
                throw ("install-skill-mesh: REFUSING source profile -- generated source " +
                       "file '$($f.Name)' lacks valid skill-mesh provenance. Nothing was written.")
            }
            $relFromSrc = $f.FullName.Substring($sourceDir.Length).TrimStart('\', '/')
            $normalizedSrcRel = ($relFromSrc -replace '\\', '/').TrimStart('/')
            $rel = $subdir.TrimEnd('/') + '/' + $normalizedSrcRel
            $safeTarget = Assert-ProviderTargetDomain $rel $Provider $homeAbs
            $sourceHash = Get-SkillMeshFileSha256 $f.FullName
            $pairs += , @($f.FullName, $safeTarget, $rel, $sourceHash)
            [void]$producedRels.Add($rel)
            if (-not (Test-Path -LiteralPath $safeTarget)) {
                continue
            }
            if (-not (Test-Path -LiteralPath $safeTarget -PathType Leaf)) {
                $foreign += $rel
                continue
            }
            $actualHash = Get-SkillMeshFileSha256 $safeTarget
            if ($actualHash -ceq $sourceHash) {
                # Exact incoming bytes are a genuine no-op. This is the sole safe
                # legacy/hashless self-seed path and does not rewrite the target.
                [void]$exactIncomingRels.Add($rel)
                continue
            }
            $recordedHash = Get-OwnedHash $priorOwnedHashes $rel
            if ($null -ne $recordedHash -and $actualHash -ceq $recordedHash -and
                (Test-FileHasMarker $safeTarget)) {
                $routinePreHashes[$rel] = $recordedHash
                continue
            }
            # Every remaining existing-file mismatch lacks routine authority. Force
            # is an explicit adoption and always requires a verified external backup.
            # ForceShared additionally requires both source and resolved target scope.
            if ($Force -or $ForceShared) {
                $isSharedPayload = (Test-SharedPayloadRel $relFromSrc) -and
                                   (Test-UnderPayloadRoot $safeTarget $payloadRootAbs)
                if ($Force -or ($ForceShared -and $isSharedPayload)) {
                    [void]$forceRels.Add($rel)
                    $forcePairs += , @($safeTarget, $rel, $actualHash)
                    $forcePreHashes[$rel] = $actualHash
                } else {
                    $foreign += $rel
                }
            } else {
                $foreign += $rel
            }
        }

        if ($foreign.Count -gt 0) {
            $list = ($foreign | Sort-Object) -join "`n  "
            throw ("install-skill-mesh: REFUSING to install -- $($foreign.Count) target " +
                   "path(s) lack current-byte overwrite authority; installing would " +
                   "overwrite operator or changed content:`n  $list`n" +
                   "Pass -Force to overwrite AND take ownership of these paths, or remove " +
                   "them first. (-ForceShared covers only the _shared/ payload and does " +
                   "NOT authorize the paths above.) Nothing was written; prior state is " +
                   "unchanged.")
        }

        # Freeze stale-delete authority before any install mutation. Unverifiable
        # stale paths refuse the whole operation as a true no-op.
        $stalePreHashes = @{}
        $staleForcedRels = New-CIStringSet
        $staleRefusals = @()
        foreach ($r in $priorOwnedRel) {
            if ($producedRels.Contains([string]$r)) { continue }
            $abs = Assert-ProviderTargetDomain ([string]$r) $Provider $homeAbs
            if (-not (Test-Path -LiteralPath $abs)) { continue }
            $recorded = Get-OwnedHash $priorOwnedHashes ([string]$r)
            $actual = Get-SkillMeshFileSha256 $abs
            if ($null -ne $recorded -and $actual -ceq $recorded -and (Test-FileHasMarker $abs)) {
                $stalePreHashes[[string]$r] = $recorded
            } else {
                $sharedAllowed = $false
                if ($ForceShared) {
                    try { $null = Resolve-FreshSharedTarget ([string]$r) $Provider $homeAbs $payloadRootAbs; $sharedAllowed = $true }
                    catch { $sharedAllowed = $false }
                }
                if (($Force -or $sharedAllowed) -and -not [string]::IsNullOrWhiteSpace($BackupDir)) {
                    [void]$forceRels.Add([string]$r)
                    [void]$staleForcedRels.Add([string]$r)
                    $forcePairs += , @($abs, [string]$r, $actual)
                    $forcePreHashes[[string]$r] = $actual
                    $stalePreHashes[[string]$r] = $actual
                } else {
                    $staleRefusals += [string]$r
                }
            }
        }
        if ($staleRefusals.Count -gt 0) {
            $list = ($staleRefusals | Sort-Object) -join "`n  "
            throw ("install-skill-mesh: REFUSING stale removal -- changed or hashless " +
                   "stale paths have no default destructive authority:`n  $list`n" +
                   "Nothing was written; prior state is unchanged.")
        }

        # Prove the ledger destination is contained and file-shaped before the first
        # target mutation; recovery must have somewhere safe to publish authority.
        $ledgerPreflight = Resolve-Contained (Get-LedgerPath $homeAbs) $homeAbs
        if ((Test-Path -LiteralPath $ledgerPreflight) -and
            -not (Test-Path -LiteralPath $ledgerPreflight -PathType Leaf)) {
            throw "install-skill-mesh: REFUSING install -- ledger destination is not a regular file. Nothing was written."
        }

        # Back up every authorized-overwrite target BEFORE any home mutation.
        if ($forcePairs.Count -gt 0 -and [string]::IsNullOrWhiteSpace($BackupDir)) {
            throw ("install-skill-mesh: REFUSING take-ownership -- every mismatching " +
                   "target adopted by -Force or -ForceShared requires -BackupDir. " +
                   "Nothing was written.")
        }
        if ($forcePairs.Count -gt 0) {
            Write-ForceBackup $forcePairs $BackupDir $Provider $homeAbs
        }

        # ================= COMMIT (mutation, recoverable) =======================
        $writtenRel = New-Object System.Collections.Generic.List[string]
        $writtenSet = New-CIStringSet
        $createdSet = New-CIStringSet
        # preserve prior record (idempotency), skipping any bogus null/empty entry.
        foreach ($d in $priorDirs) {
            if (-not [string]::IsNullOrWhiteSpace([string]$d)) { [void]$createdSet.Add([string]$d) }
        }

        # Ensure the install home exists BEFORE the copy loop so Write-Ledger always
        # has a parent dir -- even for a ZERO-file provider install (New-TrackedDir
        # otherwise runs only per copied file). Record '.' only if we created it.
        if (-not (Test-Path -LiteralPath $homeAbs)) {
            New-Item -ItemType Directory -Path $homeAbs -Force | Out-Null
            [void]$createdSet.Add('.')
        }

        # The copy loop runs through the SHARED transaction engine
        # (tools/skill-mesh-transaction.ps1): ordered action set, an append-only
        # journal record before and after each write, and a post-write hash
        # verification. This is behind-the-contract only -- no new parameter, no
        # migration_id, no backup directory, and the same exit codes.
        #
        # -NoRollback is DELIBERATE. This command's published contract on a partial
        # copy is a RECONCILED RECOVERY LEDGER (files already written stay on disk
        # and a retry resumes without -Force), not an undo. The engine therefore
        # rethrows and the existing catch below owns recovery, exactly as before.
        # The journal lives in a per-run OS-temp directory removed on every exit
        # path -- nothing new is ever written into the install home.
        $txStateDir = Join-Path ([System.IO.Path]::GetTempPath()) `
            ("skill-mesh-tx-" + [System.Guid]::NewGuid().ToString('N'))
        $txActions = @()
        $txSeq = 0
        foreach ($pair in $pairs) {
            if ($exactIncomingRels.Contains([string]$pair[2])) { continue }
            $txActions += [PSCustomObject]@{
                seq       = $txSeq
                action    = 'install'
                rel_path  = $pair[2]
                source    = $pair[0]
                target    = $pair[1]
                post_hash = (Get-SkillMeshFileSha256 $pair[0])
            }
            $txSeq++
        }

        # Durable write-ahead authority closes the only unsafe interval in the
        # normal ledger protocol. It is fully published and re-validated before the
        # first payload copy or stale delete, and carries every exact transition the
        # operation may make. Do not write it for a byte-only ledger self-seed: no
        # payload mutation follows in that case.
        $writeAheadPublished = $false
        if ($txActions.Count -gt 0 -or $stalePreHashes.Count -gt 0) {
            $writeAheadActions = @()
            foreach ($pair in $pairs) {
                $rel = [string]$pair[2]
                $preHash = $null
                $authorityHash = $null
                if ($forcePreHashes.ContainsKey($rel)) {
                    $preHash = [string]$forcePreHashes[$rel]
                } elseif ($routinePreHashes.ContainsKey($rel)) {
                    $preHash = [string]$routinePreHashes[$rel]
                    $authorityHash = [string]$routinePreHashes[$rel]
                } elseif ($exactIncomingRels.Contains($rel)) {
                    $preHash = [string]$pair[3]
                    $authorityHash = Get-OwnedHash $priorOwnedHashes $rel
                }
                $writeAheadActions += [PSCustomObject]@{
                    rel_path = $rel
                    pre_hash = $preHash
                    post_hash = [string]$pair[3]
                    authority_hash = $authorityHash
                }
            }
            foreach ($rel in @($stalePreHashes.Keys | Sort-Object)) {
                # produced and stale are disjoint by preflight construction.
                $writeAheadActions += [PSCustomObject]@{
                    rel_path = [string]$rel
                    pre_hash = [string]$stalePreHashes[$rel]
                    post_hash = $null
                    authority_hash = (Get-OwnedHash $priorOwnedHashes ([string]$rel))
                }
            }
            $writeAheadRecord = [PSCustomObject]@{
                tool                 = 'skill-mesh'
                write_ahead_version  = 1
                provider             = $Provider
                expected_ledger_hash = $script:LedgerExpectedHash
                # Directory records are audit-only. Carrying the prior set is enough
                # for a retry and never grants directory-deletion authority.
                created_dirs         = @($createdSet | Sort-Object)
                actions              = @($writeAheadActions | Sort-Object -Property rel_path)
            }
            Write-InstallWriteAhead $homeAbs $writeAheadRecord
            $writeAheadPublished = $true
        }
        $txGetHash = {
            param($a)
            # Re-resolve rather than trusting the scan-time path, so the hash is
            # taken from the same real path the mutation will write.
            Get-SkillMeshFileSha256 (Assert-ProviderTargetDomain $a.rel_path $Provider $homeAbs)
        }
        $txMutate = {
            param($a)
            $rel = $a.rel_path

            # Re-resolve containment on the PARENT immediately before creating it
            # (junction-on-ancestor TOCTOU).
            $safeTarget = Assert-ProviderTargetDomain $rel $Provider $homeAbs
            $targetDir = Split-Path -Parent $safeTarget
            $safeDir = Resolve-Contained $targetDir $homeAbs
            New-TrackedDir $safeDir $homeAbs $createdSet

            $existsNow = Test-Path -LiteralPath $safeTarget
            if ($forceRels.Contains($rel)) {
                if (-not $existsNow -or
                    (Get-SkillMeshFileSha256 $safeTarget) -cne [string]$forcePreHashes[$rel]) {
                    throw "install-skill-mesh: SECURITY -- forced target '$rel' changed after backup; refusing overwrite."
                }
            } elseif ($routinePreHashes.ContainsKey($rel)) {
                if (-not $existsNow -or -not (Test-FileHasMarker $safeTarget) -or
                    (Get-SkillMeshFileSha256 $safeTarget) -cne [string]$routinePreHashes[$rel]) {
                    throw "install-skill-mesh: SECURITY -- owned target '$rel' changed after preflight; refusing overwrite."
                }
            } elseif ($existsNow) {
                throw "install-skill-mesh: SECURITY -- a target appeared at '$rel' after preflight; refusing overwrite."
            }

            # Source identity is part of the plan too. A dist file replaced after
            # preflight must not leave markerless/wrong bytes at an owned target.
            if (-not (Test-Path -LiteralPath $a.source -PathType Leaf) -or
                -not (Test-FileHasMarker $a.source) -or
                (Get-SkillMeshFileSha256 $a.source) -cne [string]$a.post_hash) {
                throw "install-skill-mesh: SECURITY -- source '$rel' changed after preflight; refusing copy."
            }
            $tempLeaf = '.skill-mesh-install-' + $PID + '-' + [Guid]::NewGuid().ToString('N') + '.tmp'
            $safeTemp = Resolve-Contained (Join-Path $safeDir $tempLeaf) $homeAbs
            try {
                Copy-Item -LiteralPath $a.source -Destination $safeTemp
                if (-not (Test-FileHasMarker $safeTemp) -or
                    (Get-SkillMeshFileSha256 $safeTemp) -cne [string]$a.post_hash) {
                    throw "install-skill-mesh: staged target verification failed for '$rel'."
                }

                # Fresh lexical resolution + current-byte authority immediately before
                # atomic replacement. Never trust the earlier resolved target here.
                $freshTarget = Assert-ProviderTargetDomain $rel $Provider $homeAbs
                $freshExists = Test-Path -LiteralPath $freshTarget
                if ($forceRels.Contains($rel)) {
                    Assert-ForceBackupCertificate $rel ([string]$forcePreHashes[$rel]) $homeAbs
                    if ($ForceShared -and -not $Force) {
                        $freshTarget = Resolve-FreshSharedTarget $rel $Provider $homeAbs $payloadRootAbs
                    }
                    if (-not $freshExists -or
                        (Get-SkillMeshFileSha256 $freshTarget) -cne [string]$forcePreHashes[$rel]) {
                        throw "install-skill-mesh: SECURITY -- forced target '$rel' changed after backup; refusing replace."
                    }
                } elseif ($routinePreHashes.ContainsKey($rel)) {
                    if (-not $freshExists -or -not (Test-FileHasMarker $freshTarget) -or
                        (Get-SkillMeshFileSha256 $freshTarget) -cne [string]$routinePreHashes[$rel]) {
                        throw "install-skill-mesh: SECURITY -- owned target '$rel' changed before replace."
                    }
                } elseif ($freshExists) {
                    throw "install-skill-mesh: SECURITY -- a target appeared at '$rel' before replace."
                }

                if ($freshExists) {
                    $replaceBackup = Resolve-Contained `
                        (Join-Path $safeDir ('.skill-mesh-replaced-' + $PID + '-' + [Guid]::NewGuid().ToString('N') + '.tmp')) `
                        $homeAbs
                    try {
                        [System.IO.File]::Replace($safeTemp, $freshTarget, $replaceBackup)
                    } finally {
                        if (Test-Path -LiteralPath $replaceBackup) {
                            Remove-Item -LiteralPath $replaceBackup -Force
                        }
                    }
                } else {
                    [System.IO.File]::Move($safeTemp, $freshTarget)
                }
            } finally {
                if (Test-Path -LiteralPath $safeTemp) {
                    Remove-Item -LiteralPath $safeTemp -Force
                }
            }
            $writtenRel.Add($rel)
            [void]$writtenSet.Add($rel)
        }

        try {
            try {
                $tx = New-SkillMeshTransaction `
                    -MigrationId (New-SkillMeshMigrationId) `
                    -JournalPath (Join-Path $txStateDir 'journal.jsonl')
                Invoke-SkillMeshTxApply -Transaction $tx -Actions $txActions `
                    -GetPreHash $txGetHash -Mutate $txMutate -GetPostHash $txGetHash `
                    -NoRollback
            } finally {
                if (Test-Path -LiteralPath $txStateDir) {
                    Remove-Item -LiteralPath $txStateDir -Recurse -Force
                }
            }

            # Verify every produced target, including exact-incoming no-op paths,
            # before stale deletion. A concurrent edit must not let a successful copy
            # elsewhere unlock removal of old files.
            foreach ($pair in $pairs) {
                $rel = [string]$pair[2]
                $safeProduced = Assert-ProviderTargetDomain $rel $Provider $homeAbs
                if (-not (Test-FileHasMarker $safeProduced) -or
                    (Get-SkillMeshFileSha256 $safeProduced) -cne [string]$pair[3]) {
                    throw "install-skill-mesh: post-install identity verification failed for '$rel'."
                }
            }
            # Copy fully succeeded -> remove STALE prior-owned files (owned before but
            # not produced now), marker-gated + contained; then write the FINAL ledger.
            foreach ($r in @($stalePreHashes.Keys)) {
                $safeStale = Assert-ProviderTargetDomain ([string]$r) $Provider $homeAbs
                if (-not (Test-Path -LiteralPath $safeStale)) { continue }
                $staleForced = $staleForcedRels.Contains([string]$r)
                if ($staleForced) {
                    Assert-ForceBackupCertificate ([string]$r) ([string]$stalePreHashes[$r]) $homeAbs
                    if ($ForceShared -and -not $Force) {
                        $safeStale = Resolve-FreshSharedTarget ([string]$r) $Provider $homeAbs $payloadRootAbs
                    }
                }
                if ((-not $staleForced -and -not (Test-FileHasMarker $safeStale)) -or
                    (Get-SkillMeshFileSha256 $safeStale) -cne [string]$stalePreHashes[$r]) {
                    throw "install-skill-mesh: SECURITY -- stale path '$r' changed after preflight; aborting."
                }
                Remove-Item -LiteralPath $safeStale -Force
            }
            $ownedFinal = @()
            $ownedFinalHashes = @{}
            foreach ($pair in $pairs) {
                $rel = [string]$pair[2]
                $safe = Assert-ProviderTargetDomain $rel $Provider $homeAbs
                if (-not (Test-FileHasMarker $safe) -or
                    (Get-SkillMeshFileSha256 $safe) -cne [string]$pair[3]) {
                    throw "install-skill-mesh: post-install identity verification failed for '$rel'."
                }
                $ownedFinal += $rel
                $ownedFinalHashes[$rel] = [string]$pair[3]
            }
            $entry = New-InstallEntry $Provider $subdir $ownedFinal $createdSet $ownedFinalHashes
            Set-InstallEntry $ledger $Provider $entry
            Write-Ledger $homeAbs $ledger
            if ($writeAheadPublished) {
                if (-not (Test-InstallEntryEquals (Get-InstallEntry $ledger $Provider) $entry `
                            $Provider $subdir $homeAbs)) {
                    throw 'install-skill-mesh: SECURITY -- final ledger authority did not verify after publication.'
                }
                # Only retire the sole recovery authority after the normal ledger
                # carries the same exact current-byte map and has been re-read.
                Remove-InstallWriteAhead $homeAbs
            }
            Write-Host "install-skill-mesh: installed '$Provider' into $installRoot ($($ownedFinal.Count) files)."
        } catch {
            # Partial copy / TOCTOU abort: persist a RECONCILED recovery ledger listing
            # only marker-valid candidate files that ACTUALLY exist on disk (prior +
            # written). This is recovery scope, not current-byte identity; the Step
            # 65 installed-hash repair must precede live use.
            $recovered = @()
            $recoveredHashes = @{}
            foreach ($pair in $pairs) {
                $rel = [string]$pair[2]
                $safe = Assert-ProviderTargetDomain $rel $Provider $homeAbs
                if ($null -eq $safe -or -not (Test-Path -LiteralPath $safe) -or
                    -not (Test-FileHasMarker $safe)) { continue }
                $actual = Get-SkillMeshFileSha256 $safe
                $sourceHash = [string]$pair[3]
                $priorHash = Get-OwnedHash $priorOwnedHashes $rel
                if ($actual -ceq $sourceHash) {
                    $recovered += $rel
                    $recoveredHashes[$rel] = $sourceHash
                } elseif ($null -ne $priorHash -and $actual -ceq $priorHash) {
                    $recovered += $rel
                    $recoveredHashes[$rel] = $priorHash
                }
            }
            # Any stale path still present keeps its OLD durable hash. Never baseline
            # commit-time drift or a forced preimage as newly installed authority.
            foreach ($relObj in $priorOwnedRel) {
                $rel = [string]$relObj
                if ($producedRels.Contains($rel)) { continue }
                $oldHash = Get-OwnedHash $priorOwnedHashes $rel
                if ($null -eq $oldHash) { continue }
                $safe = Assert-ProviderTargetDomain $rel $Provider $homeAbs
                if (Test-Path -LiteralPath $safe) {
                    $recovered += $rel
                    $recoveredHashes[$rel] = $oldHash
                }
            }
            $entry = New-InstallEntry $Provider $subdir $recovered $createdSet $recoveredHashes
            Set-InstallEntry $ledger $Provider $entry
            Write-Ledger $homeAbs $ledger
            throw
        }
    } finally {
        if (-not [string]::IsNullOrWhiteSpace($stageDir) -and (Test-Path -LiteralPath $stageDir)) {
            Remove-Item -LiteralPath $stageDir -Recurse -Force
        }
    }
}

function Get-ExistingOwned($rels, [string]$homeAbs) {
    # Reconcile an owned-set with reality: keep only entries that resolve inside home,
    # exist on disk, AND bear the skill-mesh marker. Never persist a ghost or a
    # marker-less path. A valid header alone does not prove current-byte authorship.
    $out = @()
    foreach ($rel in @($rels)) {
        $abs = Get-ContainedAbs $rel $homeAbs
        if ($null -ne $abs -and (Test-Path -LiteralPath $abs) -and (Test-FileHasMarker $abs)) {
            $out += $rel
        }
    }
    # Comma-wrap: a bare `return $out` unrolls an EMPTY array to $null, which then
    # blows up `$ownedFinal.Count` under Set-StrictMode (the empty-collection landmine).
    return , $out
}

function Enter-HomeOperationLock([string]$homeAbs) {
    # Kernel-owned, cross-process and non-replaceable. Full SHA-256 of the canonical
    # home identity keeps aliases on one mutex without disclosing the path.
    $name = 'Local\skill-mesh-install-' + (Get-InstallHomeId $homeAbs -Full)
    $mutex = New-Object System.Threading.Mutex($false, $name)
    try {
        try { $acquired = $mutex.WaitOne(0) }
        catch [System.Threading.AbandonedMutexException] { $acquired = $true }
        if (-not $acquired) {
            $mutex.Dispose()
            throw ("install-skill-mesh: REFUSING concurrent operation -- another " +
                   "install/uninstall already holds the lock for this Home. Retry after it exits.")
        }
        return , @($mutex, (Get-CanonicalRealPath -InputPath $homeAbs))
    } catch {
        if ($null -ne $mutex) { $mutex.Dispose() }
        throw ("install-skill-mesh: REFUSING concurrent operation -- another " +
               "install/uninstall already holds the lock for this Home. Retry after it exits.")
    }
}

# -- Entry point --------------------------------------------------------------

$homeLexical = Resolve-HomeRoot $TargetHome
$pinnedHomeReal = Get-CanonicalRealPath -InputPath $homeLexical
$homeAbs = $pinnedHomeReal
$script:PinnedHomeReal = $pinnedHomeReal
$script:ForceBackupCertificateRoot = $null

# -- #89: normalize -Provider ONCE, at the parameter boundary -----------------
# PowerShell's [ValidateSet] matches case-insensitively and does NOT normalize, so
# `-Provider CLAUDE` previously flowed through verbatim: it keyed the ledger
# 'CLAUDE', wrote provider='CLAUDE', and (via build-distributions) stamped
# `Profile: CLAUDE` into every generated file -- making DISTRIBUTION BYTES vary by
# invocation casing in a repository that advertises reproducible releases.
# Resolve-SkillMeshProvider is the shared ordinal, case-insensitive matcher in
# tools/skill-mesh-discovery.ps1 (the same one the inspector uses), and it returns
# the vocabulary's OWN spelling. From here on $Provider is canonical, so the ledger
# key, the provider field, and the value handed to the builder all agree.
$canonicalProvider = Resolve-SkillMeshProvider $Provider @($DISCOVERY_SUBDIR.Keys)
if ($null -eq $canonicalProvider) {
    # Unreachable through the CLI (ValidateSet already restricted the value); kept
    # so a future vocabulary change fails loudly instead of writing a stray slug.
    [Console]::Error.WriteLine(
        "install-skill-mesh: '$Provider' is not a known provider slug.")
    exit 2
}
$Provider = $canonicalProvider

try {
    $lockResult = Enter-HomeOperationLock $homeAbs
    $operationLock = $lockResult[0]
    if ([string]$lockResult[1] -cne $pinnedHomeReal -or
        (Get-CanonicalRealPath -InputPath $homeLexical) -cne $pinnedHomeReal) {
        throw "install-skill-mesh: SECURITY -- Home identity changed while acquiring its operation lock."
    }
    # Test-only coordination seam for proving cross-process serialization. The value
    # is bounded so an accidentally inherited variable cannot hang an operation.
    $holdText = [Environment]::GetEnvironmentVariable('SKILL_MESH_INSTALL_TEST_HOLD_LOCK_MS')
    if (-not [string]::IsNullOrWhiteSpace($holdText)) {
        $holdMs = 0
        if ([int]::TryParse($holdText, [ref]$holdMs) -and $holdMs -gt 0 -and $holdMs -le 15000) {
            Start-Sleep -Milliseconds $holdMs
        }
    }
    try {
        if ($Uninstall) {
            Invoke-Uninstall $homeAbs
        } else {
            Invoke-Install $homeAbs
        }
    } finally {
        if ($null -ne $operationLock) {
            try { $operationLock.ReleaseMutex() } finally { $operationLock.Dispose() }
        }
    }
} catch {
    throw
}

exit 0
