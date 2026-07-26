<#
.SYNOPSIS
    gen-router-shim.ps1 -- emit a legacy .claude/lib/skill-router.ps1 SHIM that
    delegates to the canonical runtime/skill-router.ps1.

.DESCRIPTION
    Backward-compatibility generator. A Claude host that still looks for the router
    at its historical path (.claude/lib/skill-router.ps1) gets a thin launcher that
    forwards every argument to the neutral runtime router and returns its exit code
    unchanged -- so no behavior is lost during migration.

    The generated shim is NOT a canonical source file: it is produced into a
    caller-supplied destination (a dist/ staging area or a temp install dir), never
    committed as the real router. -Destination is mandatory so the shim is never
    written into an operator's live .claude tree by default.

.PARAMETER Destination
    Base directory to write the shim under. The shim lands at
    <Destination>/.claude/lib/skill-router.ps1.

.PARAMETER RuntimeRouter
    Absolute path to the canonical runtime/skill-router.ps1 the shim delegates to.
    Defaults to this repository's runtime/skill-router.ps1.

.EXAMPLE
    powershell -File tools\gen-router-shim.ps1 -Destination C:\stage\install
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Destination,

    [string]$RuntimeRouter = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$TOOLS_DIR = $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $TOOLS_DIR

if ([string]::IsNullOrWhiteSpace($RuntimeRouter)) {
    $RuntimeRouter = Join-Path $REPO_ROOT 'runtime\skill-router.ps1'
}
$RuntimeRouter = [System.IO.Path]::GetFullPath($RuntimeRouter)
if (-not (Test-Path -LiteralPath $RuntimeRouter)) {
    throw "gen-router-shim: canonical runtime router not found at $RuntimeRouter"
}

$shimDir = Join-Path (Join-Path $Destination '.claude') 'lib'
New-Item -ItemType Directory -Path $shimDir -Force | Out-Null
$shimPath = Join-Path $shimDir 'skill-router.ps1'

# Escape single quotes for embedding in a single-quoted PowerShell string literal.
$escapedTarget = $RuntimeRouter.Replace("'", "''")

$shimLines = @(
    '<#',
    '  GENERATED compatibility shim -- do not edit.',
    '  Legacy path .claude/lib/skill-router.ps1 delegating to the canonical',
    '  runtime/skill-router.ps1. Emitted by tools/gen-router-shim.ps1.',
    '#>',
    'Set-StrictMode -Version Latest',
    "`$ErrorActionPreference = 'Stop'",
    "",
    "# Canonical neutral router this shim forwards to (baked at generation time).",
    "`$targetRouter = '$escapedTarget'",
    "if (-not (Test-Path -LiteralPath `$targetRouter)) {",
    "    [Console]::Error.WriteLine(`"skill-router shim: canonical router not found at `$targetRouter`")",
    "    exit 3",
    "}",
    "",
    "`$psExe = (Get-Process -Id `$PID).Path",
    "if ([string]::IsNullOrWhiteSpace(`$psExe)) { `$psExe = 'powershell' }",
    "",
    "# Forward every argument verbatim and preserve the router's exit code.",
    "& `$psExe -NoProfile -NonInteractive -File `$targetRouter @args",
    "exit `$LASTEXITCODE"
)

$shimContent = ($shimLines -join [Environment]::NewLine) + [Environment]::NewLine
[System.IO.File]::WriteAllText($shimPath, $shimContent, [System.Text.UTF8Encoding]::new($false))

Write-Host $shimPath
