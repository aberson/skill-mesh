[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Skill,

    [Parameter(Mandatory = $true)]
    [string]$Model,

    [Parameter(Mandatory = $true)]
    [long]$TokensIn,

    [Parameter(Mandatory = $true)]
    [long]$TokensOut,

    [Parameter(Mandatory = $true)]
    [long]$LatencyMs,

    [Parameter(Mandatory = $true)]
    [double]$CostUsd,

    [Parameter(Mandatory = $true)]
    [ValidateSet('pass', 'fail', 'stub')]
    [string]$Verdict
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# runtime/telemetry -> runtime -> repo root. path-guard lives in runtime/.
$RUNTIME_DIR = Split-Path -Parent $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $RUNTIME_DIR
. (Join-Path $RUNTIME_DIR 'path-guard.ps1')

$outputPath = $env:SKILL_MESH_TELEMETRY_PATH
$explicit = -not [string]::IsNullOrWhiteSpace($outputPath)
if (-not $explicit) {
    $outputPath = Join-Path $PSScriptRoot 'invocations.jsonl'
}

# Canonicalize + validate against a FIXED allowed-root set (the repo, the OS temp
# tree, and the LOCALAPPDATA skill-mesh data dir). An explicit
# SKILL_MESH_TELEMETRY_PATH is checked against these roots -- NOT against its own
# parent -- so a '..'/symlink/junction path that escapes them is actually rejected.
$allowedRoots = @($REPO_ROOT, [System.IO.Path]::GetTempPath())
if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    $allowedRoots += (Join-Path $env:LOCALAPPDATA 'skill-mesh')
}
$outputPath = Resolve-SafePath -Path $outputPath -AllowedRoots $allowedRoots

if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) {
    $TokensIn = 0
    $TokensOut = 0
    $CostUsd = 0.0
    $Verdict = 'stub'
}

$record = [PSCustomObject][ordered]@{
    timestamp  = [DateTime]::UtcNow.ToString('o')
    skill      = $Skill
    model      = $Model
    tokens_in  = $TokensIn
    tokens_out = $TokensOut
    latency_ms = $LatencyMs
    cost_usd   = $CostUsd
    verdict    = $Verdict
}

$parent = Split-Path -Parent $outputPath
if (-not [string]::IsNullOrWhiteSpace($parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

$json = $record | ConvertTo-Json -Compress
[IO.File]::AppendAllText($outputPath, $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
