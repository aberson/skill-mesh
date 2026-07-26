<#
.SYNOPSIS
    path-guard.ps1 -- canonicalize a filesystem path and validate that it stays
    inside a set of allowed roots.

.DESCRIPTION
    Provider-neutral path resolver used by the skill-mesh runtime router and
    telemetry scripts. Every path the runtime touches (config files, skill entry
    points derived from a caller-supplied skill name, telemetry output path) is
    passed through Resolve-SafePath before use.

    Canonicalization resolves lexical '..' segments AND follows Windows reparse
    points (directory junctions and symbolic links), component by component, so a
    junction/symlink planted inside an allowed root that points OUTSIDE the root is
    detected and rejected. A path whose canonical form escapes every allowed root
    is rejected (Resolve-SafePath throws; the CLI form exits 3).

    Dual mode:
      - Dot-sourced (no -Path): only defines the functions; runs no logic. This is
        how runtime/skill-router.ps1 and the telemetry scripts consume it.
      - CLI (with -Path + -AllowedRoot): validates one path and prints the result.
        Exit 0 = accepted (prints 'OK <resolved>'); exit 3 = rejected.

.PARAMETER Path
    CLI mode only: the candidate path to validate.

.PARAMETER AllowedRoot
    CLI mode only: one or more roots the resolved path must stay within.

.NOTES
    Windows PowerShell 5.1 compatible. ASCII-only source (no BOM required).
#>

[CmdletBinding()]
param(
    [string]$Path = '',
    [string[]]$AllowedRoot = @()
)

# -- Canonicalization ----------------------------------------------------------

function Get-CanonicalRealPath {
    <#
      Return the fully-resolved absolute path for $InputPath: lexical '..'/'.'
      collapsed, made absolute, and every existing component that is a reparse
      point (junction/symlink) replaced by its real target. A non-existing tail
      (e.g. a file about to be written) is appended verbatim to the resolved
      existing prefix -- so validation works for paths that do not exist yet.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$InputPath,
        [int]$Depth = 0
    )

    if ([string]::IsNullOrWhiteSpace($InputPath)) {
        throw "path-guard: empty path"
    }
    if ($Depth -gt 40) {
        throw "path-guard: reparse-point resolution exceeded max depth (possible link cycle) for '$InputPath'"
    }

    $full = [System.IO.Path]::GetFullPath($InputPath)
    $root = [System.IO.Path]::GetPathRoot($full)
    if ([string]::IsNullOrEmpty($root)) {
        return $full
    }

    $rest = $full.Substring($root.Length)
    $segments = $rest.Split([char[]]@('\', '/'), [System.StringSplitOptions]::RemoveEmptyEntries)

    $current = $root
    if (-not ($current.EndsWith('\') -or $current.EndsWith('/'))) {
        $current = $current + [System.IO.Path]::DirectorySeparatorChar
    }

    foreach ($seg in $segments) {
        $current = [System.IO.Path]::Combine($current, $seg)
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            $linkTarget = $null
            $targetMember = $item | Get-Member -Name Target -ErrorAction SilentlyContinue
            if ($targetMember) {
                $t = $item.Target
                if ($t) { $linkTarget = @($t)[0] }
            }
            if ($linkTarget) {
                if (-not [System.IO.Path]::IsPathRooted($linkTarget)) {
                    $linkParent = [System.IO.Path]::GetDirectoryName($current)
                    $linkTarget = [System.IO.Path]::Combine($linkParent, $linkTarget)
                }
                $current = Get-CanonicalRealPath -InputPath $linkTarget -Depth ($Depth + 1)
            } else {
                $current = $item.FullName
            }
        }
    }

    return [System.IO.Path]::GetFullPath($current)
}

function Test-PathUnderRoot {
    param(
        [Parameter(Mandatory = $true)][string]$Candidate,
        [Parameter(Mandatory = $true)][string]$Root
    )
    $c = ([System.IO.Path]::GetFullPath($Candidate)).TrimEnd('\', '/')
    $r = ([System.IO.Path]::GetFullPath($Root)).TrimEnd('\', '/')
    if ($c.Equals($r, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }
    return $c.StartsWith($r + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)
}

function Resolve-SafePath {
    <#
      Canonicalize $Path and confirm it stays within one of $AllowedRoots.
      Returns the canonical real path on success; throws a SECURITY error if the
      resolved path escapes every allowed root (traversal via '..', symlink, or
      junction).
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$AllowedRoots
    )

    $realPath = Get-CanonicalRealPath -InputPath $Path
    foreach ($allowed in $AllowedRoots) {
        if ([string]::IsNullOrWhiteSpace($allowed)) { continue }
        $realRoot = Get-CanonicalRealPath -InputPath $allowed
        if (Test-PathUnderRoot -Candidate $realPath -Root $realRoot) {
            return $realPath
        }
    }
    throw "path-guard: SECURITY -- '$Path' resolves to '$realPath' which is outside the allowed root(s): $($AllowedRoots -join '; ')"
}

# -- CLI entry point (skipped when dot-sourced) --------------------------------

if ($Path -ne '') {
    try {
        $resolved = Resolve-SafePath -Path $Path -AllowedRoots $AllowedRoot
        Write-Host "OK $resolved"
        exit 0
    } catch {
        [Console]::Error.WriteLine($_.Exception.Message)
        exit 3
    }
}
