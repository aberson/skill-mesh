[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# runtime/telemetry -> runtime -> repo root. path-guard lives in runtime/.
$RUNTIME_DIR = Split-Path -Parent $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $RUNTIME_DIR
. (Join-Path $RUNTIME_DIR 'path-guard.ps1')

$inputPath = $env:SKILL_MESH_TELEMETRY_PATH
$explicit = -not [string]::IsNullOrWhiteSpace($inputPath)
if (-not $explicit) {
    $inputPath = Join-Path $PSScriptRoot 'invocations.jsonl'
}

# Same FIXED allowed-root set as telemetry-writer.ps1 (kept in sync): repo, OS temp
# tree, LOCALAPPDATA skill-mesh dir. An explicit SKILL_MESH_TELEMETRY_PATH is
# validated against these roots, NOT its own parent, so a traversal path is rejected.
$allowedRoots = @($REPO_ROOT, [System.IO.Path]::GetTempPath())
if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    $allowedRoots += (Join-Path $env:LOCALAPPDATA 'skill-mesh')
}
$inputPath = Resolve-SafePath -Path $inputPath -AllowedRoots $allowedRoots

if (-not (Test-Path $inputPath)) {
    Write-Host "No telemetry data found at $inputPath"
    exit 0
}

$records = @(
    Get-Content -Path $inputPath | ForEach-Object {
        if (-not [string]::IsNullOrWhiteSpace($_)) {
            $_ | ConvertFrom-Json
        }
    }
)

if ($records.Count -eq 0) {
    Write-Host "No telemetry records found at $inputPath"
    exit 0
}

$rows = foreach ($group in ($records | Group-Object -Property skill, model)) {
    $items = @($group.Group)
    $runs = $items.Count
    $passes = @($items | Where-Object { $_.verdict -eq 'pass' }).Count
    [PSCustomObject][ordered]@{
        skill          = [string]$items[0].skill
        model          = [string]$items[0].model
        runs           = $runs
        avg_tokens_in  = [Math]::Round(($items | Measure-Object -Property tokens_in -Average).Average, 2)
        avg_tokens_out = [Math]::Round(($items | Measure-Object -Property tokens_out -Average).Average, 2)
        avg_latency_ms = [Math]::Round(($items | Measure-Object -Property latency_ms -Average).Average, 2)
        avg_cost_usd   = [Math]::Round(($items | Measure-Object -Property cost_usd -Average).Average, 6)
        pass_rate      = [Math]::Round((100.0 * $passes / $runs), 2)
    }
}

$rows | Sort-Object -Property skill, model | Format-Table -AutoSize
