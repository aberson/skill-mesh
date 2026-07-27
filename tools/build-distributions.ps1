<#
.SYNOPSIS
    build-distributions.ps1 -- DETERMINISTICALLY generate host-specific
    compatibility trees from config/skill-manifest.json + the canonical
    skills/<name>/{core.md,providers/claude.md,providers/gpt.md} source tree.

.DESCRIPTION
    Emits one discovery profile per provider into a staging output directory
    (default <repo>/dist). Host discovery requires provider-specific filenames and
    directories, but those requirements never dictate canonical ownership: the
    canonical files under skills/ are the single source of truth and are NEVER
    rewritten. Each generated file is a copy carrying a GENERATED provenance header.

      dist/claude/<skill>/SKILL.md   Claude Code discovery launcher. Body is the
                                     skill's Claude adapter (providers/claude.md)
                                     whose own-core reference (../core.md) is
                                     rewritten to the co-located core.md.
      dist/claude/<skill>/core.md    The shared canonical core (portable skills
                                     only), so the launcher's reference resolves.
      dist/gpt/<skill>/SKILL.md      GPT/Copilot discovery launcher (providers/gpt.md).
      dist/gpt/<skill>/core.md       The shared canonical core (portable only).

    Provider-native skills (manifest status 'provider-native' / core == null) get
    ONLY their truthful supported adapter: they appear in dist/claude/ with no core
    reference, and are ABSENT from dist/gpt/ -- no misleading stub for the
    unsupported provider.

    SECURITY: the manifest is treated as untrusted input. Each skill 'name' is
    validated as a safe single path segment before it is joined into an output path,
    and every generated file's resolved absolute path is asserted to stay within the
    intended profile directory (defense in depth via runtime/path-guard.ps1). Every
    SOURCE path read from the manifest (core / providers.<p>) is likewise validated
    to stay within the canonical skills/ root before it is read/copied -- a traversal
    or absolute source path is rejected, never read into a generated file.

    DETERMINISM: output is byte-identical across repeated runs on unchanged input.
    Skills are processed in a stable manifest-name order; no wall-clock timestamp is
    embedded in any file body (the provenance header names only the canonical source
    path + the manifest, never a date); all files are written UTF-8 (no BOM) with LF
    line endings.

.PARAMETER OutputDir
    Staging root the profiles are written under. Default: <repo>/dist. Each
    per-provider subtree (<OutputDir>/claude, <OutputDir>/gpt) is removed and
    regenerated from scratch so a rebuild cannot leave stale files behind.

.PARAMETER Provider
    Which profile(s) to build: 'claude', 'gpt', or 'both' (default).

.PARAMETER ManifestPath
    Override the manifest consumed. Default: <repo>/config/skill-manifest.json.
    (Primarily a test seam for adversarial manifests.)

.EXAMPLE
    powershell -File tools\build-distributions.ps1
    powershell -File tools\build-distributions.ps1 -Provider claude -OutputDir C:\stage\dist
#>

[CmdletBinding()]
param(
    [string]$OutputDir = '',

    [ValidateSet('claude', 'gpt', 'both')]
    [string]$Provider = 'both',

    [string]$ManifestPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -- Path resolution (repo-root relative) -------------------------------------

$TOOLS_DIR = $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $TOOLS_DIR
$SKILLS_ROOT = Join-Path $REPO_ROOT 'skills'
$PATH_GUARD = Join-Path $REPO_ROOT 'runtime\path-guard.ps1'
$PROVENANCE = Join-Path $TOOLS_DIR 'skill-mesh-provenance.ps1'

if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
    $ManifestPath = Join-Path $REPO_ROOT 'config\skill-manifest.json'
}
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $REPO_ROOT 'dist'
}

# Reuse the Step-34 path guard (traversal/junction/symlink rejection). Dot-source
# with no -Path so only its functions load (Resolve-SafePath in this scope).
. $PATH_GUARD
# Shared provenance marker (single source of truth; defines Get-SkillMeshMarker).
. $PROVENANCE

$UTF8_NO_BOM = New-Object System.Text.UTF8Encoding($false)

# -- Helpers ------------------------------------------------------------------

function Get-Prop($obj, [string]$name) {
    # StrictMode-safe property read: returns $null when the property is absent (or
    # the container itself is null).
    if ($null -eq $obj) { return $null }
    $p = $obj.PSObject.Properties[$name]
    if ($p) { return $p.Value }
    return $null
}

function Test-SafeSegment([string]$name) {
    # A safe single path segment: non-empty, no separators, no traversal, not
    # absolute, no drive/colon. Rejects a hostile manifest name like
    # '..\..\evil-escape' before it is joined into an output path.
    if ([string]::IsNullOrWhiteSpace($name)) { return $false }
    if ($name -match '[\\/]') { return $false }
    if ($name.Contains('..')) { return $false }
    if ($name.Contains(':')) { return $false }
    if ($name -eq '.' -or $name -eq '..') { return $false }
    if ([System.IO.Path]::IsPathRooted($name)) { return $false }
    return $true
}

function Resolve-RepoPath([string]$relPosix) {
    # Manifest paths are POSIX ('skills/x/core.md'); resolve under the repo root.
    return (Join-Path $REPO_ROOT ($relPosix -replace '/', '\'))
}

function Resolve-SafeSource([string]$relPosix, [string]$name, [string]$role) {
    # Validate a manifest-declared SOURCE path stays within the canonical skills/
    # root BEFORE it is read. A traversal/absolute path throws (build refuses).
    if ([string]::IsNullOrWhiteSpace($relPosix)) {
        throw "build-distributions: empty $role source for skill '$name'"
    }
    $abs = Resolve-RepoPath $relPosix
    try {
        return (Resolve-SafePath -Path $abs -AllowedRoots @($SKILLS_ROOT))
    } catch {
        throw ("build-distributions: SECURITY -- $role source '$relPosix' for skill " +
               "'$name' escapes the canonical skills/ root; refusing to read. " +
               $_.Exception.Message)
    }
}

function Read-SourceText([string]$absPath) {
    # Read canonical bytes and normalize to LF so provenance + rewrites are
    # deterministic regardless of the working tree's checkout line endings.
    $raw = [System.IO.File]::ReadAllText($absPath, [System.Text.Encoding]::UTF8)
    return ($raw -replace "`r`n", "`n") -replace "`r", "`n"
}

function New-ProvenanceHeader([string]$canonicalSource, [string]$profile) {
    # GENERATED do-not-edit marker. Names the canonical source path + the manifest.
    # NO date / wall-clock time -- provenance must not break byte reproducibility.
    $lines = @(
        (Get-SkillMeshHeaderOpen),
        "     $(Get-SkillMeshMarkerLine)",
        '     Produced by tools/build-distributions.ps1 from config/skill-manifest.json.',
        "     Canonical source: $canonicalSource",
        "     Profile: $profile",
        '     Edit the canonical source and rebuild; edits here are overwritten. -->'
    )
    return ($lines -join "`n")
}

function Add-Provenance([string]$body, [string]$canonicalSource, [string]$profile) {
    # Insert the provenance header. When the body opens with a YAML frontmatter
    # block, the header is placed immediately AFTER it so the frontmatter stays on
    # line 1 (Claude Code discovery requires frontmatter first); otherwise it is
    # prepended.
    $prov = New-ProvenanceHeader $canonicalSource $profile
    $fmMatch = [regex]::Match($body, "(?s)^---\n.*?\n---\n")
    if ($fmMatch.Success) {
        $fm = $fmMatch.Value
        $rest = $body.Substring($fm.Length)
        return $fm + $prov + "`n" + $rest
    }
    return $prov + "`n`n" + $body
}

function Repoint-CoreReference([string]$adapterBody) {
    # In the canonical tree the adapter lives at skills/<name>/providers/<p>.md and
    # references its core as '../core.md'. In the flat discovery layout core.md is a
    # sibling of SKILL.md, so repoint the own-core reference to 'core.md'. Only the
    # exact '../core.md' token is touched: cross-skill refs like
    # '../../judge-ui/core.md' are left intact.
    return $adapterBody.Replace('../core.md', 'core.md')
}

function Write-GeneratedFile([string]$absPath, [string]$content, [string]$profileDir) {
    # Defense in depth: assert the resolved output path stays within the intended
    # profile dir before writing (name validation is the primary guard; this catches
    # any residual escape).
    $safe = Resolve-SafePath -Path $absPath -AllowedRoots @($profileDir)
    $dir = Split-Path -Parent $safe
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($safe, $content, $UTF8_NO_BOM)
}

# -- Load manifest ------------------------------------------------------------

if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "build-distributions: manifest not found at $ManifestPath"
}
$manifest = (Read-SourceText $ManifestPath) | ConvertFrom-Json

# Stable order: sort by skill name so the file SET + contents are deterministic
# regardless of manifest array order.
$skills = @($manifest.skills | Sort-Object -Property name)

$profiles = if ($Provider -eq 'both') { @('claude', 'gpt') } else { @($Provider) }

# -- Build --------------------------------------------------------------------

foreach ($profile in $profiles) {
    $profileDir = Join-Path $OutputDir $profile
    # Regenerate from scratch: a rebuild must never inherit stale files.
    if (Test-Path -LiteralPath $profileDir) {
        Remove-Item -LiteralPath $profileDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    # Canonical absolute form of the profile dir, for containment assertions.
    $profileDirAbs = (Resolve-Path -LiteralPath $profileDir).Path

    $skillCount = 0
    $fileCount = 0

    foreach ($skill in $skills) {
        $name = [string](Get-Prop $skill 'name')
        $status = [string](Get-Prop $skill 'status')

        # SECURITY: validate the skill name as a safe single segment BEFORE it is
        # joined into any output path.
        if (-not (Test-SafeSegment $name)) {
            throw ("build-distributions: SECURITY -- unsafe skill name " +
                   "'$name' in manifest (must be a single path segment: no " +
                   "separators, no '..', not absolute). Refusing to build.")
        }

        $isNative = ($status -eq 'provider-native') -or ($null -eq (Get-Prop $skill 'core'))

        # GPT profile excludes provider-native skills entirely (no misleading stub).
        if ($profile -eq 'gpt' -and $isNative) { continue }

        $providersObj = Get-Prop $skill 'providers'
        $adapterRel = Get-Prop $providersObj $profile
        if ([string]::IsNullOrWhiteSpace($adapterRel)) {
            # No adapter declared for this provider (e.g. gpt on a native skill).
            continue
        }

        # SECURITY: validate + resolve ALL of this skill's SOURCE paths within skills/
        # BEFORE writing ANY output file, so a core-only-malicious manifest cannot
        # leave a partial dist artifact (SKILL.md written, then core validation throws).
        $adapterAbs = Resolve-SafeSource $adapterRel $name "$profile-adapter"
        if (-not (Test-Path -LiteralPath $adapterAbs)) {
            throw "build-distributions: adapter source missing for '$name' ($profile): $adapterAbs"
        }
        $coreRel = Get-Prop $skill 'core'
        $hasCore = -not [string]::IsNullOrWhiteSpace($coreRel)
        $coreAbs = $null
        if ($hasCore) {
            $coreAbs = Resolve-SafeSource $coreRel $name 'core'
            if (-not (Test-Path -LiteralPath $coreAbs)) {
                throw "build-distributions: core source missing for '$name': $coreAbs"
            }
        }

        $skillOutDir = Join-Path $profileDir $name

        # -- Launcher (SKILL.md) -- (all sources validated above)
        $adapterBody = Read-SourceText $adapterAbs
        if ($hasCore) {
            $adapterBody = Repoint-CoreReference $adapterBody
        }
        $launcher = Add-Provenance $adapterBody $adapterRel $profile
        Write-GeneratedFile (Join-Path $skillOutDir 'SKILL.md') $launcher $profileDirAbs
        $fileCount++

        # -- Shared core (portable skills only) --
        if ($hasCore) {
            $coreBody = Read-SourceText $coreAbs
            $coreOut = Add-Provenance $coreBody $coreRel $profile
            Write-GeneratedFile (Join-Path $skillOutDir 'core.md') $coreOut $profileDirAbs
            $fileCount++
        }

        $skillCount++
    }

    Write-Host "build-distributions: $profile -> $profileDir ($skillCount skills, $fileCount files)"
}

Write-Host "build-distributions: done. OutputDir = $OutputDir"
exit 0
