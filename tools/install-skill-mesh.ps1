<#
.SYNOPSIS
    install-skill-mesh.ps1 -- install a generated host profile into a target home
    WITHOUT making canonical files host-owned, with an ownership-safe uninstall.

.DESCRIPTION
    Copies one provider's generated discovery tree (produced by
    tools/build-distributions.ps1) into a target home under the host's expected,
    provider-specific discovery location:

        claude -> <Home>/.claude/skills/<skill>/{SKILL.md, core.md}
        gpt    -> <Home>/.github/skills/<skill>/{SKILL.md, core.md}

    (GitHub Copilot CLI discovers project skills from .github/skills, .agents/skills,
    and .claude/skills, plus the personal ~/.copilot/skills; this installer writes the
    GPT profile to .github/skills. The project-relative .copilot/skills target used
    before the Step 43 proof is RETIRED -- Copilot does not discover it.)

    OWNERSHIP AUTHORITY = FILE-CONTENT PROVENANCE, NOT THE LEDGER.
    Every generated file carries the provenance marker from tools/skill-mesh-provenance.ps1
    (Get-SkillMeshMarker). Every destructive op is gated on the TARGET FILE'S content:
      - Install overwrite: a target may be written only if it does NOT exist OR it
        already bears the marker (a skill-mesh file). A target that exists WITHOUT the
        marker is FOREIGN -- refused by default; -Force is the explicit opt-in.
      - Uninstall delete / stale-removal: a file is deleted only if it bears the marker
        AND the ledger lists it. The marker is the SAFETY gate ("ours to touch?"); the
        ledger is only the SCOPING hint ("which marker file is this provider's").
    Because the marker lives in the file's own bytes, a poisoned/mutable ledger can
    never cause an operator (non-marker) file to be clobbered or deleted, and a
    re-created operator file at a formerly-owned ("ghost") path is never clobbered.

    The ledger (<Home>/.skill-mesh-install.json) is an index/hint only. It is written
    atomically (temp file + rename), read StrictMode-safely, and self-heals from a
    corrupt/old-shape file with a clean diagnostic (never a lockout).

    Containment (runtime/path-guard.ps1 Resolve-SafePath, which follows junctions /
    symlinks) is re-resolved on the target AND its parent immediately BEFORE each
    directory creation and each copy -- not once at scan -- so a junction planted on
    an ancestor between scan and write cannot redirect a write outside the home.

    TRANSACTIONAL install (validate-before-mutate): scan for foreign collisions with
    NO change to the install home; a refusal is a TRUE no-op. On a partial-copy
    failure, a reconciled recovery ledger records only skill-mesh's own marker files
    that actually exist on disk, so a retry resumes without -Force.

    ONLY-OWN-WHAT-YOU-CREATE (dirs): a directory is recorded in created_dirs only if
    this install actually created it (it did not pre-exist), unioned with the prior
    entry so a reinstall's ledger stays byte-identical. Uninstall removes a created dir
    only when empty, so a pre-existing (operator-owned) empty home/intermediate survives.

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
    Overwrite AND take ownership of a pre-existing non-marker (foreign) file at a
    colliding target path (explicit opt-in).

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
    # Ownership authority: is this file a WELL-FORMED skill-mesh-generated file? The
    # check is ANCHORED to the generated header block (Test-SkillMeshProvenance), NOT a
    # substring-anywhere scan -- so an operator file that merely mentions the token is
    # NOT misclassified as owned.
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
    $path = Get-LedgerPath $homeAbs
    if (-not (Test-Path -LiteralPath $path)) {
        $script:LedgerStatus = 'absent'
        return (New-EmptyLedger)
    }
    try {
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
    # Atomic: write a PROCESS-UNIQUE temp file then rename over the target (same-volume
    # rename), so a crash mid-write can never corrupt the now load-bearing ledger and
    # two concurrent installs against the same home (claude + gpt in parallel) cannot
    # lost-update via a shared temp name.
    # Re-resolved through the path guard immediately before the write, like every
    # other consumer-home mutation here: the ledger is a file in the install home,
    # so a junction planted on the home between scan and commit would otherwise
    # redirect it.
    $safeLedger = Resolve-Contained (Get-LedgerPath $homeAbs) $homeAbs
    $safeTmp = "$safeLedger.$PID.$([Guid]::NewGuid().ToString('N')).tmp"
    $json = $ledger | ConvertTo-Json -Depth 8
    try {
        [System.IO.File]::WriteAllText($safeTmp, $json, $UTF8_NO_BOM)
        Move-Item -LiteralPath $safeTmp -Destination $safeLedger -Force
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

function New-InstallEntry([string]$provider, [string]$subdir, $ownedRels, $createdDirs) {
    return [PSCustomObject]@{
        provider         = $provider
        discovery_subdir = $subdir
        owned_files      = Select-CleanRels $ownedRels
        created_dirs     = Select-CleanRels $createdDirs
    }
}

function Resolve-RemovableCreatedDir([string]$rel, [string]$homeAbs) {
    # THE single directory-removal invariant, shared by every dir-removal path:
    # return the absolute path eligible for removal, or $null to REFUSE. A directory is
    # eligible only if (1) $rel is a valid non-empty entry (skill-mesh provably created
    # it -> it is in created_dirs), (2) it resolves strictly INSIDE the home, and (3) if
    # it resolves to the home ROOT, only when $rel is the genuine '.' record -- an
    # empty/null/'..' entry must NEVER map to the home root. Emptiness is checked by the
    # caller immediately before the actual Remove-Item.
    if ([string]::IsNullOrWhiteSpace($rel)) { return $null }
    $abs = Get-ContainedAbs $rel $homeAbs
    if ($null -eq $abs) { return $null }
    if ($abs.Equals($homeAbs, [System.StringComparison]::OrdinalIgnoreCase) -and $rel -ne '.') {
        # Exact-match sentinel (NOT $rel.Trim()): a whitespace-padded or otherwise
        # non-literal entry (e.g. ' . ') that Windows path-normalization collapses to
        # the home root must be REFUSED, so a tampered ledger cannot delete the
        # operator's pre-existing home. Only the literal '.' record maps to the root.
        return $null
    }
    return $abs
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

function Remove-OwnedFiles([string]$homeAbs, $entry) {
    # Delete a ledger-listed owned file ONLY if it (a) resolves inside the home
    # (untrusted-ledger containment) AND (b) bears the skill-mesh marker. A ledger
    # entry pointing at a foreign/operator (non-marker) file is NEVER deleted.
    if ($null -eq $entry) { return }
    foreach ($rel in @(Get-Field $entry 'owned_files' @())) {
        $abs = Get-ContainedAbs $rel $homeAbs
        if ($null -eq $abs) { continue }
        if (-not (Test-Path -LiteralPath $abs)) { continue }
        if (-not (Test-FileHasMarker $abs)) {
            [Console]::Error.WriteLine(
                "install-skill-mesh: WARNING -- ledger lists '$rel' as owned but its " +
                "content does NOT bear the skill-mesh marker (foreign/operator file); NOT deleting.")
            continue
        }
        $safeTarget = Resolve-Contained $abs $homeAbs
        Remove-Item -LiteralPath $safeTarget -Force
    }
}

function Remove-CreatedDirs([string]$homeAbs, $entry) {
    # Remove created dirs bottom-up, contained-within-home, and ONLY when empty (so a
    # pre-existing sentinel or foreign file keeps its directory alive).
    if ($null -eq $entry) { return }
    # Deepest-first by path-SEGMENT COUNT (a child always has more segments than its
    # ancestor), so a parent is only considered after its children are gone.
    $dirs = @(Get-Field $entry 'created_dirs' @()) |
        Sort-Object -Property @{ Expression = { ([string]$_ -split '/').Count } } -Descending
    foreach ($rel in $dirs) {
        # Single dir-removal invariant: only a provably-created, in-home dir (and the
        # home root only via a genuine '.' entry).
        $abs = Resolve-RemovableCreatedDir ([string]$rel) $homeAbs
        if ($null -eq $abs) { continue }
        if (Test-Path -LiteralPath $abs) {
            $remaining = @(Get-ChildItem -LiteralPath $abs -Force)
            if ($remaining.Count -eq 0) {
                $safeDir = Resolve-Contained $abs $homeAbs
                Remove-Item -LiteralPath $safeDir -Force
            }
        }
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
    # Ledger tracking is LOST (corrupt/old-shape) but skill-mesh files may still be on
    # disk. Recover by scanning the provider's discovery subdir and removing ONLY
    # well-formed marker-bearing FILES (contained-within-home). It must NOT be a silent
    # clean no-op (warns loudly + reports).
    #
    # FILES ONLY -- NEVER remove directories here. Without a created_dirs record the
    # fallback cannot prove skill-mesh created any directory (the discovery root may be
    # a shared .claude/skills used by other manually-installed skills, and an
    # intermediate dir may be operator-owned). The dir-removal invariant requires proof
    # of creation, which this path structurally lacks -> leave all directories in place.
    $subdir = $DISCOVERY_SUBDIR[$Provider]
    $root = Join-Path $homeAbs ($subdir -replace '/', '\')
    [Console]::Error.WriteLine(
        "install-skill-mesh: WARNING -- ledger lost track (corrupt/old-shape); falling back " +
        "to a marker-based scan of $root to remove skill-mesh files (files only; no dirs).")
    if (-not (Test-Path -LiteralPath $root)) {
        Write-Host "install-skill-mesh: no discovery dir at $root; nothing to recover for '$Provider'."
        return
    }
    $removed = 0
    foreach ($f in @(Get-ChildItem -LiteralPath $root -Recurse -File)) {
        try {
            $safe = Resolve-SafePath -Path $f.FullName -AllowedRoots @($homeAbs)
        } catch {
            continue
        }
        if (Test-FileHasMarker $safe) {
            $safeTarget = Resolve-Contained $safe $homeAbs
            Remove-Item -LiteralPath $safeTarget -Force
            $removed++
        }
    }
    Write-Host "install-skill-mesh: marker-based fallback removed $removed skill-mesh file(s) under $root for '$Provider' (directories left in place)."
}

function Invoke-Uninstall([string]$homeAbs) {
    $ledger = Read-Ledger $homeAbs
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
    $subdir = Get-Field $entry 'discovery_subdir' ''
    try {
        Remove-OwnedFiles $homeAbs $entry
    } catch {
        # Reconcile: rewrite the entry to only the owned files that STILL exist, so a
        # retry resumes cleanly; surface a clean diagnostic rather than a torn state.
        $remaining = @()
        foreach ($rel in @(Get-Field $entry 'owned_files' @())) {
            $abs = Get-ContainedAbs $rel $homeAbs
            if ($null -ne $abs -and (Test-Path -LiteralPath $abs)) { $remaining += $rel }
        }
        $reconciled = New-InstallEntry $Provider $subdir $remaining @(Get-Field $entry 'created_dirs' @())
        Set-InstallEntry $ledger $Provider $reconciled
        Write-Ledger $homeAbs $ledger
        throw
    }
    # Update the ledger. Removing the ledger file first lets the home dir become empty
    # so its created-dir removal (last) can succeed on a full uninstall.
    Remove-InstallEntry $ledger $Provider
    if (Test-InstallsEmpty $ledger) {
        $safeLedger = Resolve-Contained (Get-LedgerPath $homeAbs) $homeAbs
        if (Test-Path -LiteralPath $safeLedger) {
            Remove-Item -LiteralPath $safeLedger -Force
        }
    } else {
        Write-Ledger $homeAbs $ledger
    }
    Remove-CreatedDirs $homeAbs $entry
    Write-Host "install-skill-mesh: uninstalled '$Provider' from $homeAbs."
}

# -- Install (transactional: validate -> commit) ------------------------------

function Invoke-Install([string]$homeAbs) {
    $ledger = Read-Ledger $homeAbs
    $prior = Get-InstallEntry $ledger $Provider
    # Prior-owned rels: used ONLY to scope stale-removal + the recovery set. They are
    # NOT the overwrite/foreign authority -- the marker in the target file is.
    $priorOwnedRel = if ($null -ne $prior) { @(Get-Field $prior 'owned_files' @()) } else { @() }
    $priorDirs = if ($null -ne $prior) { @(Get-Field $prior 'created_dirs' @()) } else { @() }

    $subdir = $DISCOVERY_SUBDIR[$Provider]

    $stageDir = ''
    try {
        # ================= VALIDATE (no change to the install home) =============
        $resolved = Resolve-SourceProfileDir $Provider
        $sourceDir = $resolved[0]
        $stageDir = $resolved[1]

        $installRoot = Join-Path $homeAbs ($subdir -replace '/', '\')
        $srcFiles = @(Get-ChildItem -LiteralPath $sourceDir -Recurse -File | Sort-Object -Property FullName)

        $pairs = @()          # each: @(srcFull, safeTarget, rel)
        $foreign = @()
        foreach ($f in $srcFiles) {
            $relFromSrc = $f.FullName.Substring($sourceDir.Length).TrimStart('\', '/')
            $target = Join-Path $installRoot $relFromSrc
            $safeTarget = Resolve-Contained $target $homeAbs
            $rel = ConvertTo-PosixRel $safeTarget $homeAbs
            $pairs += , @($f.FullName, $safeTarget, $rel)
            # FOREIGN = target exists AND its content does NOT bear the marker. The
            # ledger is NOT consulted here (a poisoned ledger cannot launder a foreign
            # file into "owned").
            if ((Test-Path -LiteralPath $safeTarget) -and (-not (Test-FileHasMarker $safeTarget))) {
                $foreign += $rel
            }
        }

        if ($foreign.Count -gt 0 -and -not $Force) {
            $list = ($foreign | Sort-Object) -join "`n  "
            throw ("install-skill-mesh: REFUSING to install -- $($foreign.Count) target " +
                   "path(s) already exist and are NOT skill-mesh-generated (no provenance " +
                   "marker); installing would overwrite operator content:`n  $list`n" +
                   "Pass -Force to overwrite AND take ownership of these paths, or remove " +
                   "them first. Nothing was written; prior state is unchanged.")
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
        $txGetHash = {
            param($a)
            # Re-resolve rather than trusting the scan-time path, so the hash is
            # taken from the same real path the mutation will write.
            Get-SkillMeshFileSha256 (Resolve-Contained $a.target $homeAbs)
        }
        $txMutate = {
            param($a)
            $rel = $a.rel_path

            # Re-resolve containment on the PARENT immediately before creating it
            # (junction-on-ancestor TOCTOU).
            $targetDir = Split-Path -Parent $a.target
            $safeDir = Resolve-Contained $targetDir $homeAbs
            New-TrackedDir $safeDir $homeAbs $createdSet

            # Re-resolve containment on the TARGET immediately before the copy.
            $safeTarget = Resolve-Contained $a.target $homeAbs

            # Marker TOCTOU guard: a foreign file may have appeared here AFTER the
            # scan. Overwrite only a non-existent target or a marker-bearing one.
            if ((Test-Path -LiteralPath $safeTarget) -and
                (-not (Test-FileHasMarker $safeTarget)) -and
                (-not $writtenSet.Contains($rel)) -and
                (-not $Force)) {
                throw ("install-skill-mesh: SECURITY -- a foreign (non-marker) file " +
                       "appeared at '$rel' after the pre-scan; aborting to avoid " +
                       "clobbering it (pass -Force to override).")
            }

            Copy-Item -LiteralPath $a.source -Destination $safeTarget -Force
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

            # Copy fully succeeded -> remove STALE prior-owned files (owned before but
            # not produced now), marker-gated + contained; then write the FINAL ledger.
            foreach ($r in $priorOwnedRel) {
                if (-not $writtenSet.Contains($r)) {
                    $abs = Get-ContainedAbs $r $homeAbs
                    if ($null -ne $abs -and (Test-Path -LiteralPath $abs) -and (Test-FileHasMarker $abs)) {
                        $safeStale = Resolve-Contained $abs $homeAbs
                        Remove-Item -LiteralPath $safeStale -Force
                    }
                }
            }
            $ownedFinal = Get-ExistingOwned $writtenRel $homeAbs
            $entry = New-InstallEntry $Provider $subdir $ownedFinal $createdSet
            Set-InstallEntry $ledger $Provider $entry
            Write-Ledger $homeAbs $ledger
            Write-Host "install-skill-mesh: installed '$Provider' into $installRoot ($($ownedFinal.Count) files)."
        } catch {
            # Partial copy / TOCTOU abort: persist a RECONCILED recovery ledger listing
            # only skill-mesh's own marker files that ACTUALLY exist on disk (prior +
            # written), so a retry recognizes them as owned -- never a re-created
            # operator file (which lacks the marker) as owned/foreign-clobberable.
            $candidate = New-CIStringSet
            foreach ($r in $priorOwnedRel) { [void]$candidate.Add($r) }
            foreach ($r in $writtenRel) { [void]$candidate.Add($r) }
            $recovered = Get-ExistingOwned $candidate $homeAbs
            $entry = New-InstallEntry $Provider $subdir $recovered $createdSet
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
    # exist on disk, AND bear the skill-mesh marker. Never persist a ghost (deleted)
    # or a non-marker (operator) path as owned.
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

# -- Entry point --------------------------------------------------------------

$homeAbs = Resolve-HomeRoot $TargetHome

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

if ($Uninstall) {
    Invoke-Uninstall $homeAbs
} else {
    Invoke-Install $homeAbs
}

exit 0
