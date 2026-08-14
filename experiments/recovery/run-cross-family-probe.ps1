[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^goala-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$')]
    [string]$GoalAId,

    [Parameter(Mandatory = $true)]
    [ValidateSet('Prepare', 'InvokeSavedHandoff', 'Run')]
    [string]$Action,

    [Parameter(Mandatory = $true)]
    [ValidateSet('claude-to-gpt', 'gpt-to-claude')]
    [string]$Direction,

    [Parameter(Mandatory = $true)]
    [ValidateSet('manual-saved-handoff', 'reviewer-only-dispatcher')]
    [string]$Mechanism,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$FixtureRoot,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$CandidateSha,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$EvidenceDir,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^cross-(claude-to-gpt|gpt-to-claude)-(manual-saved-handoff|reviewer-only-dispatcher)-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$')]
    [string]$RunId,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^a[0-2](-r1)?$')]
    [string]$AttemptId,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$LiveClaudeHome,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$LiveCodexHome,

    [Parameter(Mandatory = $true)]
    [ValidateSet('gpt-5.6-terra', 'sonnet')]
    [string]$RequestedReviewerModel,

    [ValidateSet('copy-file')]
    [string]$CredentialMode = 'copy-file',

    [ValidateRange(1, 900)]
    [int]$ReviewerTimeoutSeconds = 600,

    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Stop-Wrapper([string]$Message) {
    [Console]::Error.WriteLine("cross-family wrapper: $Message")
    exit 2
}

$validAction = (
    ($Mechanism -eq 'manual-saved-handoff' -and $Action -in @('Prepare', 'InvokeSavedHandoff')) -or
    ($Mechanism -eq 'reviewer-only-dispatcher' -and $Action -eq 'Run')
)
if (-not $validAction) {
    Stop-Wrapper "action '$Action' is not valid for mechanism '$Mechanism'"
}

$expectedModel = if ($Direction -eq 'claude-to-gpt') { 'gpt-5.6-terra' } else { 'sonnet' }
if ($RequestedReviewerModel -cne $expectedModel) {
    Stop-Wrapper "direction '$Direction' requires requested reviewer model '$expectedModel'"
}

$expectedRunPrefix = "cross-$Direction-$Mechanism-"
if (-not $RunId.StartsWith($expectedRunPrefix, [System.StringComparison]::Ordinal)) {
    Stop-Wrapper "run ID does not match direction '$Direction' and mechanism '$Mechanism'"
}

$probePath = Join-Path $PSScriptRoot 'cross-family-fixture\probe.py'
if (-not (Test-Path -LiteralPath $probePath -PathType Leaf)) {
    Stop-Wrapper "candidate probe is missing: $probePath"
}
$probePath = (Resolve-Path -LiteralPath $probePath).Path

$pythonCommand = @(Get-Command python.exe -CommandType Application -All -ErrorAction SilentlyContinue |
    Where-Object { $_.Source -and (Test-Path -LiteralPath $_.Source -PathType Leaf) } |
    Select-Object -First 1)
if ($pythonCommand.Count -ne 1) {
    Stop-Wrapper 'python.exe was not found on PATH'
}
$pythonPath = $pythonCommand[0].Source

$request = [ordered]@{
    schema = 'skill-mesh.cross-family.probe-request.v1'
    goal_a_id = $GoalAId
    action = $Action
    direction = $Direction
    mechanism = $Mechanism
    fixture_root = $FixtureRoot
    candidate_sha = $CandidateSha
    evidence_dir = $EvidenceDir
    run_id = $RunId
    attempt_id = $AttemptId
    live_claude_home = $LiveClaudeHome
    live_codex_home = $LiveCodexHome
    requested_reviewer_model = $RequestedReviewerModel
    credential_mode = $CredentialMode
    reviewer_timeout_seconds = $ReviewerTimeoutSeconds
    what_if = [bool]$WhatIf
}
$requestJson = $request | ConvertTo-Json -Compress

$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = $pythonPath
$bootstrap = "import runpy,sys;from pathlib import Path;p=str(Path(sys.argv[1]).resolve());sys.path.insert(0,str(Path(p).parent));runpy.run_path(p,run_name='__main__')"
$startInfo.Arguments = "-I -B -c `"$bootstrap`" `"$probePath`""
$startInfo.WorkingDirectory = $PSScriptRoot
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.RedirectStandardInput = $true
$startInfo.RedirectStandardOutput = $false
$startInfo.RedirectStandardError = $false

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $startInfo
$priorInputEncoding = [Console]::InputEncoding
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
    if (-not $process.Start()) {
        Stop-Wrapper 'python.exe did not start'
    }
    try {
        $process.StandardInput.Write($requestJson)
    }
    finally {
        $process.StandardInput.Close()
    }
    $process.WaitForExit()
    $exitCode = $process.ExitCode
}
catch {
    Stop-Wrapper "failed to invoke candidate probe: $($_.Exception.Message)"
}
finally {
    $process.Dispose()
    [Console]::InputEncoding = $priorInputEncoding
}

exit $exitCode
