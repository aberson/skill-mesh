#requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateSet("codex", "claude")]
    [string]$HostName = "",

    [string]$GoalAId = "",

    [string]$DisposableHome = "",

    [string]$LiveClaudeHome = "",

    [string]$LiveCodexHome = "",

    [string]$EvidenceDir = "",

    [string]$RunId = "",

    [string]$AttemptId = "",

    [string]$CandidateSha = "",

    [string]$RequestedModel = "",

    [ValidateSet("copy-file", "host-store")]
    [string]$CredentialMode = "copy-file",

    [ValidateRange(30, 900)]
    [int]$ConsumerTimeoutSeconds = 300,

    [switch]$WhatIf
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$script:RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..')).TrimEnd('\', '/')

$script:CommandSequence = 0
$script:CommandResults = New-Object System.Collections.ArrayList
$script:Checks = New-Object System.Collections.ArrayList
$script:ReportResult = "AMBIGUOUS"
$script:FailureReason = ""
$script:CleanupNotes = New-Object System.Collections.ArrayList
$script:ProcessTreeClear = $true
$script:LiveSnapshotHmacKeyHex = ''
$script:UsageStatus = 'unavailable'
$script:CostStatus = 'unavailable'
$script:LifecycleExitCode = 2
$script:LiveSnapshotDeadlineSeconds = 600
$script:LiveSnapshotParentTimeoutMilliseconds = 630000
$script:LiveSnapshotMaxRecords = 100000

function Get-CanonicalRealPath {
    param(
        [Parameter(Mandatory = $true)][string]$InputPath,
        [int]$Depth = 0
    )

    if ([string]::IsNullOrWhiteSpace($InputPath)) {
        throw "Path is empty"
    }
    if ($Depth -gt 40) {
        throw "Reparse-point resolution exceeded the maximum depth: $InputPath"
    }

    $full = [System.IO.Path]::GetFullPath($InputPath)
    $root = [System.IO.Path]::GetPathRoot($full)
    if ([string]::IsNullOrEmpty($root)) {
        return $full
    }

    $current = $root
    $segments = $full.Substring($root.Length).Split(
        [char[]]@('\', '/'),
        [System.StringSplitOptions]::RemoveEmptyEntries
    )
    foreach ($segment in $segments) {
        $current = [System.IO.Path]::Combine($current, $segment)
        if (-not (Test-Path -LiteralPath $current)) {
            continue
        }
        $item = Get-Item -LiteralPath $current -Force
        $targetMember = $item | Get-Member -Name Target -ErrorAction SilentlyContinue
        $target = if ($targetMember -and $item.Target) { @($item.Target)[0] } else { $null }
        if ($target) {
            if (-not [System.IO.Path]::IsPathRooted($target)) {
                $target = [System.IO.Path]::Combine([System.IO.Path]::GetDirectoryName($current), $target)
            }
            $current = Get-CanonicalRealPath -InputPath $target -Depth ($Depth + 1)
        }
        else {
            $current = $item.FullName
        }
    }
    return [System.IO.Path]::GetFullPath($current)
}

function Write-Utf8NoBom([string]$Path, [string]$Text) {
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        $null = New-Item -ItemType Directory -Path $parent
    }
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $encoding)
}

function Write-NewUtf8NoBom([string]$Path, [string]$Text) {
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        $null = New-Item -ItemType Directory -Path $parent
    }
    if (Test-Path -LiteralPath $Path) {
        throw "Evidence file already exists: $Path"
    }
    $temporary = "$Path.tmp-$([Guid]::NewGuid().ToString('N'))"
    $encoding = New-Object System.Text.UTF8Encoding($false)
    try {
        [System.IO.File]::WriteAllText($temporary, $Text, $encoding)
        [System.IO.File]::Move($temporary, $Path)
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -Force -LiteralPath $temporary
        }
    }
}

function Get-AbsolutePath([string]$Path) {
    if (-not [System.IO.Path]::IsPathRooted($Path)) {
        throw "Path must be absolute: $Path"
    }
    return (Get-CanonicalRealPath -InputPath $Path).TrimEnd('\', '/')
}

function Test-SameOrChild([string]$Candidate, [string]$Root) {
    $candidateFull = (Get-AbsolutePath $Candidate)
    $rootFull = (Get-AbsolutePath $Root)
    if ($candidateFull.Equals($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }
    return $candidateFull.StartsWith(
        $rootFull + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase
    )
}

function Assert-NoReparsePoint([string]$Path, [string]$Label) {
    $cursor = Get-AbsolutePath $Path
    while (-not (Test-Path -LiteralPath $cursor)) {
        $parent = Split-Path -Parent $cursor
        if (-not $parent -or $parent -eq $cursor) {
            throw "$Label has no existing ancestor: $Path"
        }
        $cursor = $parent
    }

    while ($cursor) {
        $item = Get-Item -Force -LiteralPath $cursor
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "$Label crosses a reparse point: $cursor"
        }
        $parent = Split-Path -Parent $cursor
        if (-not $parent -or $parent -eq $cursor) {
            break
        }
        $cursor = $parent
    }
}

function Get-WorktreeRoots {
    $priorOptionalLocks = $env:GIT_OPTIONAL_LOCKS
    $env:GIT_OPTIONAL_LOCKS = '0'
    $repoRoot = $null
    $repoExitCode = $null
    try {
        $repoRoot = (& git --no-optional-locks -C $PSScriptRoot rev-parse --show-toplevel 2>$null)
        $repoExitCode = $LASTEXITCODE
    }
    finally {
        if ($null -eq $priorOptionalLocks) {
            Remove-Item Env:GIT_OPTIONAL_LOCKS -ErrorAction SilentlyContinue
        }
        else {
            $env:GIT_OPTIONAL_LOCKS = $priorOptionalLocks
        }
    }
    if ($repoExitCode -ne 0 -or -not $repoRoot) {
        throw "Runner is not inside a Git worktree"
    }
    $repoRoot = Get-AbsolutePath $repoRoot
    $roots = New-Object System.Collections.ArrayList
    $worktreeOutput = @(& git --no-optional-locks -C $repoRoot worktree list --porcelain 2>$null)
    $worktreeExitCode = $LASTEXITCODE
    if ($worktreeExitCode -ne 0) {
        throw "Git worktree enumeration failed"
    }
    $worktreeOutput | ForEach-Object {
        if ($_ -like 'worktree *') {
            $null = $roots.Add((Get-AbsolutePath $_.Substring(9)))
        }
    }
    if ($roots.Count -eq 0 -or -not @($roots | Where-Object { $_.Equals($repoRoot, [System.StringComparison]::OrdinalIgnoreCase) })) {
        throw "Git worktree enumeration did not include the current repository root"
    }
    return @($roots)
}

function Assert-RequiredParameters {
    $required = @{
        HostName = $HostName
        GoalAId = $GoalAId
        DisposableHome = $DisposableHome
        LiveClaudeHome = $LiveClaudeHome
        LiveCodexHome = $LiveCodexHome
        EvidenceDir = $EvidenceDir
        RunId = $RunId
        AttemptId = $AttemptId
        CandidateSha = $CandidateSha
        RequestedModel = $RequestedModel
    }
    foreach ($name in $required.Keys) {
        if ([string]::IsNullOrWhiteSpace([string]$required[$name])) {
            throw "Required parameter is missing: -$name"
        }
    }
    if ($GoalAId -notmatch '^goala-\d{8}T\d{6}Z-[0-9a-f]{8}$') {
        throw "GoalAId has invalid format: $GoalAId"
    }
    if ($RunId -notmatch '^lifecycle-(codex|claude)-\d{8}T\d{6}Z-[0-9a-f]{8}$') {
        throw "RunId has invalid format: $RunId"
    }
    if ($AttemptId -notmatch '^a[0-2](-r1)?$') {
        throw "AttemptId has invalid format: $AttemptId"
    }
    if ($CandidateSha -notmatch '^[0-9a-f]{40}$') {
        throw "CandidateSha must be a full lowercase 40-hex commit"
    }
}

function Assert-CandidateIdentity {
    $planPath = Join-Path $script:RepoRoot 'plan.md'
    $recordedGoalAId = Select-String -LiteralPath $planPath -Pattern '^\*\*GoalAId:\*\* `([^`]+)`$'
    if (-not $recordedGoalAId -or $recordedGoalAId.Matches[0].Groups[1].Value -ne $GoalAId) {
        throw "GoalAId does not match plan.md"
    }
    $planText = Get-Content -Raw -LiteralPath $planPath
    $step74Section = [regex]::Match($planText, '(?ms)^### Step 74:.*?(?=^### Step |\z)')
    $recordedCandidate = [regex]::Match(
        $step74Section.Value,
        '(?m)^\*\*Candidate commit:\*\* `([0-9a-f]{40})`'
    )
    if (-not $recordedCandidate.Success -or $recordedCandidate.Groups[1].Value -ne $CandidateSha) {
        throw "CandidateSha does not match the active Step 74 candidate in plan.md"
    }

    & git --no-optional-locks -C $script:RepoRoot cat-file -e "$CandidateSha^{commit}" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "CandidateSha is not a commit in this repository: $CandidateSha"
    }
    & git --no-optional-locks -C $script:RepoRoot merge-base --is-ancestor $CandidateSha HEAD
    if ($LASTEXITCODE -ne 0) {
        throw "CandidateSha is not an ancestor of the current Goal A HEAD"
    }
    $stepPaths = @(
        'experiments/recovery/lifecycle-probe',
        'experiments/recovery/run-lifecycle-probe.ps1',
        'tests/experiments/test_lifecycle_probe.py',
        'documentation/experiments/lifecycle-report-template.md',
        'documentation/experiments/lifecycle-runbook.md'
    )
    & git --no-optional-locks -C $script:RepoRoot diff --quiet $CandidateSha -- @stepPaths
    if ($LASTEXITCODE -ne 0) {
        throw "Executing Step 74 files differ from CandidateSha"
    }

    $indexPath = Join-Path $script:GoalAEvidenceRoot 'evidence-index.md'
    if (-not (Test-Path -LiteralPath $indexPath -PathType Leaf)) {
        throw "Goal A evidence index is missing: $indexPath"
    }
    $candidateLines = @(
        Select-String -LiteralPath $indexPath -Pattern '^\| `step74-candidate`' |
            Where-Object { [regex]::Match($_.Line, '[0-9a-f]{40}').Value -eq $CandidateSha }
    )
    if ($candidateLines.Count -ne 1) {
        throw "CandidateSha must have exactly one matching Step 74 row in the Goal A evidence index"
    }
}

function Assert-ProbePaths {
    $disposable = Get-AbsolutePath $DisposableHome
    $evidence = Get-AbsolutePath $EvidenceDir
    $liveClaude = Get-AbsolutePath $LiveClaudeHome
    $liveCodex = Get-AbsolutePath $LiveCodexHome

    $localAppData = Get-AbsolutePath $env:LOCALAPPDATA
    $script:GoalAEvidenceRoot = Get-AbsolutePath (Join-Path $localAppData "SkillMesh\Evidence\$GoalAId")
    $script:GoalAHomesRoot = Get-AbsolutePath (Join-Path $localAppData "SkillMesh\Homes\$GoalAId")

    if (-not (Test-Path -LiteralPath $liveClaude -PathType Container)) {
        throw "LiveClaudeHome does not exist: $liveClaude"
    }
    if (-not (Test-Path -LiteralPath $liveCodex -PathType Container)) {
        throw "LiveCodexHome does not exist: $liveCodex"
    }
    if (Test-Path -LiteralPath $disposable) {
        throw "DisposableHome already exists: $disposable"
    }
    if (Test-Path -LiteralPath $evidence) {
        throw "EvidenceDir already exists: $evidence"
    }
    if (-not (Test-SameOrChild $evidence $script:GoalAEvidenceRoot)) {
        throw "EvidenceDir must be below the Goal A evidence root"
    }
    if (-not (Test-SameOrChild $disposable $script:GoalAHomesRoot)) {
        throw "DisposableHome must be below the Goal A homes root"
    }

    Assert-NoReparsePoint $disposable "DisposableHome"
    Assert-NoReparsePoint $evidence "EvidenceDir"
    Assert-NoReparsePoint $liveClaude "LiveClaudeHome"
    Assert-NoReparsePoint $liveCodex "LiveCodexHome"

    $pairs = @(
        @($disposable, $evidence, "DisposableHome and EvidenceDir"),
        @($disposable, $liveClaude, "DisposableHome and LiveClaudeHome"),
        @($disposable, $liveCodex, "DisposableHome and LiveCodexHome"),
        @($evidence, $liveClaude, "EvidenceDir and LiveClaudeHome"),
        @($evidence, $liveCodex, "EvidenceDir and LiveCodexHome")
    )
    foreach ($pair in $pairs) {
        if ((Test-SameOrChild $pair[0] $pair[1]) -or (Test-SameOrChild $pair[1] $pair[0])) {
            throw "$($pair[2]) overlap"
        }
    }

    $script:WorktreeRoots = @(Get-WorktreeRoots)
    foreach ($root in $script:WorktreeRoots) {
        if ((Test-SameOrChild $disposable $root) -or (Test-SameOrChild $root $disposable)) {
            throw "DisposableHome overlaps Git worktree: $root"
        }
        if ((Test-SameOrChild $evidence $root) -or (Test-SameOrChild $root $evidence)) {
            throw "EvidenceDir overlaps Git worktree: $root"
        }
    }

    if (-not $RunId.StartsWith("lifecycle-$HostName-")) {
        throw "RunId host does not match HostName"
    }
    if ((Split-Path -Leaf $evidence) -ne $AttemptId) {
        throw "EvidenceDir leaf must equal AttemptId '$AttemptId'"
    }
    if ((Split-Path -Leaf (Split-Path -Parent $evidence)) -ne $RunId) {
        throw "EvidenceDir parent must equal RunId '$RunId'"
    }
    if ((Split-Path -Leaf $disposable) -ne "$RunId-$AttemptId") {
        throw "DisposableHome leaf must equal '$RunId-$AttemptId'"
    }

    $script:DisposableHomeApproved = $disposable
    $script:EvidenceDirApproved = $evidence
    $script:LiveClaudeHomeApproved = $liveClaude
    $script:LiveCodexHomeApproved = $liveCodex
}

function Get-Sha256Text([string]$Text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Get-Sha256File([string]$Path) {
    $stream = [System.IO.File]::Open($Path, 'Open', 'Read', 'ReadWrite')
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
        $stream.Dispose()
    }
}

function Get-TreeHash([string]$Root) {
    $rootFull = Get-AbsolutePath $Root
    $lines = New-Object System.Collections.ArrayList
    Get-ChildItem -Force -LiteralPath $rootFull -Recurse -File |
        Sort-Object FullName |
        ForEach-Object {
            $relative = $_.FullName.Substring($rootFull.Length + 1).Replace('\', '/')
            $hash = Get-Sha256File $_.FullName
            $null = $lines.Add("$relative`t$hash")
        }
    return Get-Sha256Text ((@($lines) -join "`n") + "`n")
}

function Copy-DirectoryContents([string]$Source, [string]$Destination) {
    if (Test-Path -LiteralPath $Destination) {
        throw "Copy destination already exists: $Destination"
    }
    $null = New-Item -ItemType Directory -Path $Destination
    Get-ChildItem -Force -LiteralPath $Source | ForEach-Object {
        Copy-Item -Force -Recurse -LiteralPath $_.FullName -Destination $Destination
    }
}

function Set-JsonFile([string]$Path, $Value) {
    $json = $Value | ConvertTo-Json -Depth 20
    Write-Utf8NoBom $Path ($json + "`n")
}

function Replace-TreeTokens([string]$Root, [object[]]$Replacements) {
    $files = @(Get-ChildItem -Force -LiteralPath $Root -Recurse -File | Sort-Object FullName)
    foreach ($replacement in $Replacements) {
        $token = [string]$replacement.token
        $count = 0
        foreach ($file in $files) {
            $text = [System.IO.File]::ReadAllText($file.FullName)
            $count += [regex]::Matches($text, [regex]::Escape($token)).Count
        }
        if ($count -lt [int]$replacement.minimum) {
            throw "Fixture token '$token' occurred $count times; expected at least $($replacement.minimum)"
        }
        foreach ($file in $files) {
            $text = [System.IO.File]::ReadAllText($file.FullName)
            if ($text.Contains($token)) {
                Write-Utf8NoBom $file.FullName ($text.Replace($token, [string]$replacement.value))
            }
        }
    }

    foreach ($file in $files) {
        $text = [System.IO.File]::ReadAllText($file.FullName)
        if ($text -match '\{\{[A-Z0-9_]+\}\}') {
            throw "Unresolved fixture token '$($Matches[0])' in $($file.FullName)"
        }
    }
}

function New-MaterializedMarketplace([string]$Destination, [string]$ReleaseName) {
    $template = $script:CandidateTemplateRoot
    if (-not (Test-Path -LiteralPath $template -PathType Container)) {
        throw "Fixture template is missing: $template"
    }
    Copy-DirectoryContents $template $Destination

    $basePlugin = Join-Path $Destination 'plugins\mesh-lifecycle-probe'
    $pluginParent = Split-Path -Parent $basePlugin
    Rename-Item -LiteralPath $basePlugin -NewName $script:PluginName
    $pluginRoot = Join-Path $pluginParent $script:PluginName

    if ($ReleaseName -eq 'v1') {
        $version = "1.0.0+codex.$($script:ProbeId).v1"
    }
    elseif ($ReleaseName -eq 'v2') {
        $version = "2.0.0+codex.$($script:ProbeId).v2"
    }
    else {
        throw "Unknown release: $ReleaseName"
    }

    $referenceToken = (Get-Sha256Text "$RunId|$ReleaseName|reference").Substring(0, 20)
    $helperToken = (Get-Sha256Text "$RunId|$ReleaseName|helper").Substring(0, 20)
    $replacements = @(
        [pscustomobject]@{ token = '{{MARKETPLACE_NAME}}'; value = $script:MarketplaceName; minimum = 2 },
        [pscustomobject]@{ token = '{{PLUGIN_NAME}}'; value = $script:PluginName; minimum = 6 },
        [pscustomobject]@{ token = '{{PROBE_ID}}'; value = $script:ProbeId; minimum = 1 },
        [pscustomobject]@{ token = '{{SEMVER}}'; value = $version; minimum = 2 },
        [pscustomobject]@{ token = '{{RUN_ID}}'; value = $RunId; minimum = 1 },
        [pscustomobject]@{ token = '{{RELEASE}}'; value = $ReleaseName; minimum = 3 },
        [pscustomobject]@{ token = '{{REFERENCE_TOKEN}}'; value = "ref-$referenceToken"; minimum = 1 },
        [pscustomobject]@{ token = '{{HELPER_TOKEN}}'; value = "helper-$helperToken"; minimum = 1 },
        [pscustomobject]@{ token = '{{TRIGGER_ALPHA}}'; value = $script:TriggerAlpha; minimum = 1 },
        [pscustomobject]@{ token = '{{TRIGGER_BETA}}'; value = $script:TriggerBeta; minimum = 1 }
    )
    Replace-TreeTokens $Destination $replacements

    Get-Content -Raw -LiteralPath (Join-Path $Destination '.agents\plugins\marketplace.json') | ConvertFrom-Json | Out-Null
    Get-Content -Raw -LiteralPath (Join-Path $Destination '.claude-plugin\marketplace.json') | ConvertFrom-Json | Out-Null
    Get-Content -Raw -LiteralPath (Join-Path $pluginRoot '.codex-plugin\plugin.json') | ConvertFrom-Json | Out-Null
    Get-Content -Raw -LiteralPath (Join-Path $pluginRoot '.claude-plugin\plugin.json') | ConvertFrom-Json | Out-Null

    return [pscustomobject]@{
        release = $ReleaseName
        version = $version
        root = $Destination
        plugin_root = $pluginRoot
        tree_sha256 = Get-TreeHash $Destination
        reference_token = "ref-$referenceToken"
        helper_token = "helper-$helperToken"
    }
}

function ConvertTo-CommandLineArgument([string]$Argument) {
    if ($null -eq $Argument -or $Argument.Length -eq 0) {
        return '""'
    }
    if ($Argument -notmatch '[\s"]') {
        return $Argument
    }
    $builder = New-Object System.Text.StringBuilder
    $null = $builder.Append('"')
    $slashes = 0
    foreach ($character in $Argument.ToCharArray()) {
        if ($character -eq '\') {
            $slashes++
            continue
        }
        if ($character -eq '"') {
            $null = $builder.Append(('\' * (($slashes * 2) + 1)))
            $null = $builder.Append('"')
            $slashes = 0
            continue
        }
        if ($slashes -gt 0) {
            $null = $builder.Append(('\' * $slashes))
            $slashes = 0
        }
        $null = $builder.Append($character)
    }
    if ($slashes -gt 0) {
        $null = $builder.Append(('\' * ($slashes * 2)))
    }
    $null = $builder.Append('"')
    return $builder.ToString()
}

function ConvertTo-RedactedValue([string]$Value) {
    $redacted = $Value
    $pairs = @(
        [pscustomobject]@{ value = $script:DisposableHomeApproved; label = '<DISPOSABLE_HOME>' },
        [pscustomobject]@{ value = $script:EvidenceDirApproved; label = '<EVIDENCE_DIR>' },
        [pscustomobject]@{ value = $script:LiveClaudeHomeApproved; label = '<LIVE_CLAUDE_HOME>' },
        [pscustomobject]@{ value = $script:LiveCodexHomeApproved; label = '<LIVE_CODEX_HOME>' },
        [pscustomobject]@{ value = $script:RepoRoot; label = '<REPO_ROOT>' },
        [pscustomobject]@{ value = [string]$env:LOCALAPPDATA; label = '<LOCALAPPDATA>' },
        [pscustomobject]@{ value = [string]$env:APPDATA; label = '<APPDATA>' },
        [pscustomobject]@{ value = [string]$env:USERPROFILE; label = '<USERPROFILE>' }
    ) | Sort-Object { $_.value.Length } -Descending
    foreach ($pair in $pairs) {
        if (-not [string]::IsNullOrEmpty($pair.value)) {
            $redacted = $redacted.Replace($pair.value, $pair.label)
        }
    }
    return $redacted
}

function Test-IsProviderEnvironmentKey([string]$Name) {
    return (
        $Name -match '^(ANTHROPIC|OPENAI|CODEX|CLAUDE|CHATGPT|AZURE|AWS|CLOUD_ML|VERTEX|GOOGLE|OLLAMA|LMSTUDIO|MISTRAL|GROQ|TOGETHER|XAI|DEEPSEEK)_' -or
        $Name -in @(
            'GOOGLE_APPLICATION_CREDENTIALS',
            'GOOGLE_CLOUD_PROJECT',
            'GCLOUD_PROJECT',
            'VF_CLAUDE_BIN'
        )
    )
}

function Remove-InheritedProviderEnvironment([System.Diagnostics.ProcessStartInfo]$StartInfo) {
    $removed = New-Object System.Collections.ArrayList
    foreach ($key in @($StartInfo.EnvironmentVariables.Keys)) {
        if (Test-IsProviderEnvironmentKey ([string]$key)) {
            $null = $removed.Add([string]$key)
            $StartInfo.EnvironmentVariables.Remove([string]$key)
        }
    }
    return @($removed | Sort-Object -Unique)
}

function Get-DescendantProcessCheck([int]$RootProcessId, [DateTime]$RootStartedUtc) {
    try {
        $processes = @(Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, CreationDate -ErrorAction Stop)
        $descendants = New-Object System.Collections.ArrayList
        $frontier = @($RootProcessId)
        while ($frontier.Count -gt 0) {
            $next = New-Object System.Collections.ArrayList
            foreach ($parentId in $frontier) {
                foreach ($processInfo in @($processes | Where-Object { [int]$_.ParentProcessId -eq [int]$parentId })) {
                    $createdUtc = ([DateTime]$processInfo.CreationDate).ToUniversalTime()
                    if ($createdUtc -lt $RootStartedUtc.AddSeconds(-2)) {
                        continue
                    }
                    if (-not $descendants.Contains([int]$processInfo.ProcessId)) {
                        $null = $descendants.Add([int]$processInfo.ProcessId)
                        $null = $next.Add([int]$processInfo.ProcessId)
                    }
                }
            }
            $frontier = @($next)
        }
        return [pscustomobject]@{ checked = $true; process_ids = @($descendants) }
    }
    catch {
        return [pscustomobject]@{ checked = $false; process_ids = @(); error = $_.Exception.Message }
    }
}

function Invoke-LoggedCommand(
    [string]$Id,
    [string]$FilePath,
    [string[]]$Arguments,
    [hashtable]$Environment,
    [string]$WorkingDirectory,
    [int]$TimeoutSeconds = 120
) {
    if (-not $script:ProcessTreeClear) {
        throw "A prior process tree is not confirmed stopped; no later command can start"
    }
    $script:CommandSequence++
    $sequence = $script:CommandSequence.ToString('D2')
    $commandDir = Join-Path $EvidenceDir "commands\$sequence-$Id"
    $null = New-Item -ItemType Directory -Path $commandDir
    $displayArgs = @($Arguments | ForEach-Object { ConvertTo-CommandLineArgument $_ })
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = $displayArgs -join ' '
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $removedEnvironmentKeys = @(Remove-InheritedProviderEnvironment $psi)
    foreach ($key in $Environment.Keys) {
        $psi.EnvironmentVariables[$key] = [string]$Environment[$key]
    }
    $forbiddenEffectiveKeys = @($psi.EnvironmentVariables.Keys | Where-Object {
        (Test-IsProviderEnvironmentKey ([string]$_)) -and -not $Environment.ContainsKey([string]$_)
    })
    if ($forbiddenEffectiveKeys.Count -gt 0) {
        throw "A provider environment key survived isolation: $($forbiddenEffectiveKeys -join ', ')"
    }

    $redactedRecord = [ordered]@{
        executable = ConvertTo-RedactedValue $FilePath
        arguments = @($Arguments | ForEach-Object { ConvertTo-RedactedValue $_ })
        working_directory = ConvertTo-RedactedValue $WorkingDirectory
        isolation_overrides = @($Environment.Keys | Sort-Object)
        removed_ambient_provider_keys = $removedEnvironmentKeys
    }
    Write-NewUtf8NoBom (Join-Path $commandDir 'argv.json') (($redactedRecord | ConvertTo-Json -Depth 5) + "`n")

    $containmentHelper = Join-Path $script:RepoRoot 'experiments\recovery\lifecycle-probe\job_process.py'
    if (-not (Test-Path -LiteralPath $containmentHelper -PathType Leaf)) {
        throw "Job Object containment helper is missing"
    }
    $targetStdoutPath = Join-Path $commandDir 'target-stdout.raw'
    $targetStderrPath = Join-Path $commandDir 'target-stderr.raw'
    $containmentRequest = [ordered]@{
        schema = 1
        executable = [System.IO.Path]::GetFullPath($FilePath)
        argv = @($Arguments)
        cwd = [System.IO.Path]::GetFullPath($WorkingDirectory)
        timeout_ms = $TimeoutSeconds * 1000
        stdout_path = $targetStdoutPath
        stderr_path = $targetStderrPath
    }
    $python = (Get-Command python.exe -ErrorAction Stop).Source
    $psi.FileName = $python
    $psi.Arguments = "-I -B $(ConvertTo-CommandLineArgument $containmentHelper)"
    $psi.WorkingDirectory = $script:RepoRoot
    $psi.RedirectStandardInput = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    $processStarted = $false
    $helperStopped = $false
    $script:ProcessTreeClear = $false
    try {
        $null = $process.Start()
        $processStarted = $true
        $helperStdoutTask = $process.StandardOutput.ReadToEndAsync()
        $helperStderrTask = $process.StandardError.ReadToEndAsync()
        $process.StandardInput.Write((($containmentRequest | ConvertTo-Json -Depth 5 -Compress) + "`n"))
        $process.StandardInput.Close()
        $helperExited = $process.WaitForExit(($TimeoutSeconds + 30) * 1000)
        $taskkillExitCode = $null
        if (-not $helperExited) {
            $terminationText = (& taskkill.exe /PID $process.Id /T /F 2>&1 | Out-String)
            $taskkillExitCode = $LASTEXITCODE
            Write-NewUtf8NoBom (Join-Path $commandDir 'containment-helper-termination.txt') $terminationText
            $helperExited = $process.WaitForExit(10000)
        }
        $streamsClosed = $helperExited -and $helperStdoutTask.Wait(10000) -and $helperStderrTask.Wait(10000)
        $helperStopped = $helperExited -and $streamsClosed
        $helperStdout = if ($streamsClosed) { $helperStdoutTask.Result } else { '' }
        $helperStderr = if ($streamsClosed) { $helperStderrTask.Result } else { 'containment helper output did not close' }
        Write-NewUtf8NoBom (Join-Path $commandDir 'containment-helper-stderr.txt') $helperStderr

        $containment = $null
        if ($helperStopped -and -not [string]::IsNullOrWhiteSpace($helperStdout)) {
            try { $containment = $helperStdout | ConvertFrom-Json } catch { $containment = $null }
        }
        $requiredContainmentFields = @(
            'schema', 'status', 'target_started', 'assigned_before_resume', 'root_pid',
            'root_exit_code', 'timed_out', 'survivors_existed', 'survivor_pids',
            'terminate_job_called', 'job_empty_confirmed', 'duration_seconds', 'stage', 'win32_error'
        )
        $containmentValid = $containment -and $containment.schema -eq 1 -and
            @($requiredContainmentFields | Where-Object { $_ -notin $containment.PSObject.Properties.Name }).Count -eq 0
        if ($containmentValid) {
            Write-NewUtf8NoBom (Join-Path $commandDir 'containment.json') (($containment | ConvertTo-Json -Depth 5) + "`n")
        }
        $treeExitConfirmed = $containmentValid -and $containment.job_empty_confirmed -eq $true
        if ($treeExitConfirmed) {
            $script:ProcessTreeClear = $true
        }

        $utf8 = New-Object System.Text.UTF8Encoding($false, $false)
        $stdout = if (Test-Path -LiteralPath $targetStdoutPath -PathType Leaf) {
            $utf8.GetString([System.IO.File]::ReadAllBytes($targetStdoutPath))
        }
        else { '[unavailable: target stdout was not created]' }
        $stderr = if (Test-Path -LiteralPath $targetStderrPath -PathType Leaf) {
            $utf8.GetString([System.IO.File]::ReadAllBytes($targetStderrPath))
        }
        else { '[unavailable: target stderr was not created]' }
        $timedOut = $containmentValid -and $containment.timed_out -eq $true
        $survivorsExisted = $containmentValid -and $containment.survivors_existed -eq $true
        $targetStarted = $containmentValid -and $containment.target_started -eq $true
        $exitCode = if ($containmentValid -and $null -ne $containment.root_exit_code) {
            [int]$containment.root_exit_code
        }
        elseif ($timedOut) { 124 }
        else { 125 }
        $duration = if ($containmentValid) { [double]$containment.duration_seconds } else { 0.0 }
        $helperExitCode = if ($helperExited) { $process.ExitCode } else { 125 }

        Write-NewUtf8NoBom (Join-Path $commandDir 'stdout.txt') $stdout
        Write-NewUtf8NoBom (Join-Path $commandDir 'stderr.txt') $stderr
        Write-NewUtf8NoBom (Join-Path $commandDir 'result.txt') ("exit_code=$exitCode`ntimed_out=$timedOut`nsurvivors_existed=$survivorsExisted`ncontainment_helper_exit_code=$helperExitCode`ntaskkill_exit_code=$taskkillExitCode`nprocess_tree_exit_confirmed=$treeExitConfirmed`nduration_seconds=$duration`n")

        $result = [pscustomobject]@{
            id = $Id
            sequence = $sequence
            executable = $redactedRecord.executable
            arguments = $redactedRecord.arguments
            removed_ambient_provider_keys = $removedEnvironmentKeys
            exit_code = $exitCode
            timed_out = $timedOut
            survivors_existed = $survivorsExisted
            duration_seconds = $duration
            stdout = $stdout
            stderr = $stderr
            evidence_dir = $commandDir
        }
        $null = $script:CommandResults.Add($result)
        if (-not $containmentValid -or -not $treeExitConfirmed) {
            Stop-Probe 'AMBIGUOUS' "Command '$Id' did not prove an empty Job Object"
        }
        if (-not $targetStarted -or -not $containment.assigned_before_resume) {
            Stop-Probe 'AMBIGUOUS' "Command '$Id' did not start inside the Job Object"
        }
        if ($helperExitCode -ne 0 -or $timedOut -or $survivorsExisted) {
            Stop-Probe 'AMBIGUOUS' "Command '$Id' timed out or left a surviving Job Object member"
        }
        return $result
    }
    finally {
        if ($processStarted -and -not $helperStopped) {
            try {
                if (-not $process.HasExited) {
                    $null = (& taskkill.exe /PID $process.Id /T /F 2>&1 | Out-String)
                    $null = $process.WaitForExit(10000)
                }
            }
            catch { }
        }
        $process.Dispose()
    }
}

function Invoke-HostCommand([string]$Id, [string[]]$Arguments, [hashtable]$Environment, [string]$WorkingDirectory, [int]$TimeoutSeconds = 120) {
    $launcher = if ($HostName -eq 'codex') {
        (Get-Command codex -ErrorAction Stop).Source
    }
    else {
        (Get-Command claude -ErrorAction Stop).Source
    }
    $extension = [System.IO.Path]::GetExtension($launcher).ToLowerInvariant()
    if ($extension -eq '.ps1') {
        $powershell = (Get-Command powershell.exe -ErrorAction Stop).Source
        $prefix = @('-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', $launcher)
        $hostArguments = if ($HostName -eq 'codex') { @('--strict-config') + @($Arguments) } else { @($Arguments) }
        return Invoke-LoggedCommand $Id $powershell (@($prefix) + @($hostArguments)) $Environment $WorkingDirectory $TimeoutSeconds
    }
    if ($extension -eq '.cmd' -or $extension -eq '.bat') {
        $cmd = (Get-Command cmd.exe -ErrorAction Stop).Source
        $hostArguments = if ($HostName -eq 'codex') { @('--strict-config') + @($Arguments) } else { @($Arguments) }
        return Invoke-LoggedCommand $Id $cmd (@('/d', '/s', '/c', $launcher) + @($hostArguments)) $Environment $WorkingDirectory $TimeoutSeconds
    }
    $hostArguments = if ($HostName -eq 'codex') { @('--strict-config') + @($Arguments) } else { @($Arguments) }
    return Invoke-LoggedCommand $Id $launcher $hostArguments $Environment $WorkingDirectory $TimeoutSeconds
}

function Add-Check([string]$Name, [string]$Status, [string]$Evidence, [string]$Detail) {
    $null = $script:Checks.Add([pscustomobject]@{
        name = $Name
        status = $Status
        evidence = $Evidence
        detail = $Detail
    })
}

function Stop-Probe([ValidateSet('FAIL', 'AMBIGUOUS')][string]$Status, [string]$Message) {
    $exception = New-Object System.Exception($Message)
    $exception.Data['probe_status'] = $Status
    throw $exception
}

function Assert-ProbeCommand($Result, [string]$Message, [string]$FailureStatus = 'FAIL') {
    if (-not $script:ProcessTreeClear) {
        Stop-Probe 'AMBIGUOUS' "$Message because the process tree is not confirmed stopped"
    }
    if ($Result.exit_code -eq 0) { return }
    $status = if ($Result.timed_out -or -not $script:ProcessTreeClear) { 'AMBIGUOUS' } else { $FailureStatus }
    Stop-Probe $status "$Message (exit $($Result.exit_code))"
}

function Assert-OneInstalledPlugin($Evidence, [string]$Label) {
    if ($Evidence.rejected_count -gt 0) {
        Stop-Probe 'AMBIGUOUS' "$Label found a linked or escaped installed-package candidate"
    }
    if ($Evidence.matching_count -eq 1) {
        Add-Check $Label 'PASS' $Evidence.locator_path "One exact installed package matches the expected release; inventory_sha256=$($Evidence.inventory_sha256)"
        return
    }
    if ($Evidence.matching_count -eq 0) {
        Stop-Probe 'FAIL' "$Label found no installed package with the expected bytes"
    }
    Stop-Probe 'AMBIGUOUS' "$Label found $($Evidence.matching_count) installed packages with the same expected bytes"
}

function New-SnapshotHmacKeyHex {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return ([System.BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}

function Invoke-LiveSnapshotHelper([string]$RequestJson) {
    if (-not $script:ProcessTreeClear) {
        throw "A prior process tree is not confirmed stopped; snapshot refused"
    }
    $helper = Join-Path $script:RepoRoot 'experiments\recovery\lifecycle-probe\live_snapshot.py'
    if (-not (Test-Path -LiteralPath $helper -PathType Leaf)) {
        throw "Live snapshot helper is missing"
    }
    $python = (Get-Command python.exe -ErrorAction Stop).Source
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $python
    $psi.Arguments = "-I -B $(ConvertTo-CommandLineArgument $helper)"
    $psi.WorkingDirectory = $script:RepoRoot
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $null = Remove-InheritedProviderEnvironment $psi

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    $startedProcess = $false
    $treeConfirmed = $false
    $stdoutTask = $null
    $stderrTask = $null
    $rootStartedUtc = [DateTime]::UtcNow
    try {
        $script:ProcessTreeClear = $false
        $null = $process.Start()
        $startedProcess = $true
        $rootStartedUtc = $process.StartTime.ToUniversalTime()
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $process.StandardInput.Write($RequestJson)
        $process.StandardInput.Close()
        $parentExited = $process.WaitForExit($script:LiveSnapshotParentTimeoutMilliseconds)
        if (-not $parentExited) {
            $null = (& taskkill.exe /PID $process.Id /T /F 2>&1 | Out-String)
            $parentExited = $process.WaitForExit(10000)
        }
        $streamsClosed = $parentExited -and $stdoutTask.Wait(10000) -and $stderrTask.Wait(10000)
        $descendantCheck = Get-DescendantProcessCheck $process.Id $rootStartedUtc
        $treeConfirmed = $parentExited -and $streamsClosed -and $descendantCheck.checked -and $descendantCheck.process_ids.Count -eq 0
        if (-not $treeConfirmed) {
            throw "Live snapshot helper process tree is not confirmed stopped"
        }
        $script:ProcessTreeClear = $true
        $stdout = $stdoutTask.Result
        $stderr = $stderrTask.Result
        if ($process.ExitCode -ne 0) {
            throw "Live snapshot helper failed: $stderr"
        }
        $payload = $stdout | ConvertFrom-Json
        if ($payload.schema -ne 1 -or $payload.status -ne 'COMPLETE') {
            throw "Live snapshot helper returned an invalid result"
        }
        return $payload
    }
    catch {
        if ($startedProcess -and -not $treeConfirmed) {
            try {
                if (-not $process.HasExited) {
                    $null = (& taskkill.exe /PID $process.Id /T /F 2>&1 | Out-String)
                    $null = $process.WaitForExit(10000)
                }
                $descendantCheck = Get-DescendantProcessCheck $process.Id $rootStartedUtc
                $treeConfirmed = $process.HasExited -and $descendantCheck.checked -and $descendantCheck.process_ids.Count -eq 0
            }
            catch { $treeConfirmed = $false }
            $script:ProcessTreeClear = $treeConfirmed
        }
        throw
    }
    finally {
        $process.Dispose()
    }
}

function Get-LiveHomeSnapshot([string]$ClaudeHome, [string]$CodexHome) {
    if (-not $script:LiveSnapshotHmacKeyHex) {
        $script:LiveSnapshotHmacKeyHex = New-SnapshotHmacKeyHex
    }
    $request = [ordered]@{
        schema = 1
        hmac_key_hex = $script:LiveSnapshotHmacKeyHex
        deadline_seconds = $script:LiveSnapshotDeadlineSeconds
        max_records = $script:LiveSnapshotMaxRecords
        roots = @(
            [ordered]@{ label = 'claude'; path = (Get-AbsolutePath $ClaudeHome) },
            [ordered]@{ label = 'codex'; path = (Get-AbsolutePath $CodexHome) },
            [ordered]@{ label = 'agents'; path = (Get-AbsolutePath (Join-Path (Split-Path -Parent $CodexHome) '.agents')) }
        )
        secret_paths = @(
            (Get-AbsolutePath (Join-Path $ClaudeHome '.credentials.json')),
            (Get-AbsolutePath (Join-Path $CodexHome 'auth.json'))
        )
        allowed_reparse_roots = @(
            (Get-AbsolutePath (Split-Path -Parent $ClaudeHome)),
            (Get-AbsolutePath (Split-Path -Parent $CodexHome))
        )
    }
    $payload = Invoke-LiveSnapshotHelper (($request | ConvertTo-Json -Depth 5 -Compress) + "`n")
    $records = @($payload.records)

    $publicRows = @($records | Sort-Object path | ForEach-Object {
        if ($_.secret) {
            "$($_.kind)`t$($_.path)`t$($_.length)`t$($_.final_length)`t$($_.grew_during_read)`tREDACTED_CREDENTIAL"
        }
        elseif ($_.kind -eq 'REPARSE') {
            "$($_.kind)`t$($_.path)`t$($_.length)`t$($_.final_length)`t$($_.grew_during_read)`t$(ConvertTo-RedactedValue $_.target)`t$($_.sha256)"
        }
        else {
            "$($_.kind)`t$($_.path)`t$($_.length)`t$($_.final_length)`t$($_.grew_during_read)`t$($_.sha256)"
        }
    })
    $comparisonRows = @($records | Sort-Object path | ForEach-Object {
        if ($_.secret) { "$($_.kind)`t$($_.path)`t$($_.length)`t$($_.final_length)`t$($_.grew_during_read)`tSECRET_NOT_HASHED" }
        else { "$($_.kind)`t$($_.path)`t$($_.length)`t$($_.final_length)`t$($_.grew_during_read)`t$($_.sha256)" }
    })
    $publicText = ($publicRows -join "`n") + "`n"
    return [pscustomobject]@{
        records = @($records)
        public_text = $publicText
        public_sha256 = Get-Sha256Text $publicText
        comparison_sha256 = Get-Sha256Text (($comparisonRows -join "`n") + "`n")
        duration_seconds = [double]$payload.duration_seconds
    }
}

function Test-LiveRecordEqual($First, $Second) {
    if (-not $First -or -not $Second -or $First.kind -ne $Second.kind -or $First.length -ne $Second.length) { return $false }
    if ($First.grew_during_read -or $Second.grew_during_read) { return $false }
    if ($First.kind -eq 'FILE' -and $First.file_id -ne $Second.file_id) { return $false }
    if ($First.secret -or $Second.secret) {
        return $First.secret -and $Second.secret -and $First.secret_hmac -eq $Second.secret_hmac
    }
    return $First.sha256 -eq $Second.sha256
}

function Get-RecordMap($Snapshot) {
    $map = @{}
    foreach ($record in @($Snapshot.records)) {
        $map[[string]$record.path] = $record
    }
    return $map
}

function Get-FilePrefixSha256([string]$Path, [long]$Length) {
    $stream = [System.IO.File]::Open($Path, 'Open', 'Read', 'ReadWrite')
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $buffer = New-Object byte[] 1048576
        $remaining = $Length
        while ($remaining -gt 0) {
            $read = $stream.Read($buffer, 0, [int][Math]::Min($buffer.Length, $remaining))
            if ($read -le 0) { throw "File ended before the required prefix: $Path" }
            $null = $sha.TransformBlock($buffer, 0, $read, $null, 0)
            $remaining -= $read
        }
        $null = $sha.TransformFinalBlock((New-Object byte[] 0), 0, 0)
        return ([System.BitConverter]::ToString($sha.Hash)).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
        $stream.Dispose()
    }
}

function Get-PreflightVolatility($First, $Second) {
    $firstMap = Get-RecordMap $First
    $secondMap = Get-RecordMap $Second
    $allPaths = @($firstMap.Keys + $secondMap.Keys | Sort-Object -Unique)
    $allowedAppends = New-Object System.Collections.ArrayList
    $opaqueVolatile = New-Object System.Collections.ArrayList
    foreach ($path in $allPaths) {
        $a = $firstMap[$path]
        $b = $secondMap[$path]
        if (Test-LiveRecordEqual $a $b) {
            continue
        }
        $isSessionAppend = $a -and $b -and $a.kind -eq 'FILE' -and $b.kind -eq 'FILE' -and
            $a.file_id -eq $b.file_id -and $path -match '^codex/sessions/.+\.jsonl$' -and $b.length -ge $a.length -and
            (Get-FilePrefixSha256 $b.physical_path $a.length) -eq $a.sha256
        if ($isSessionAppend) {
            $null = $allowedAppends.Add($path)
            continue
        }
        $isOpaqueCodexRuntimeFile = $a -and $b -and $a.kind -eq 'FILE' -and $b.kind -eq 'FILE' -and
            $a.file_id -eq $b.file_id -and $path -match '^codex/(?:logs_[0-9]+\.sqlite(?:-(?:shm|wal))?|state_[0-9]+\.sqlite-(?:shm|wal))$'
        if ($isOpaqueCodexRuntimeFile) {
            $null = $opaqueVolatile.Add($path)
            continue
        }
        throw "A live host path changed during the preflight quiet sample: $path"
    }
    return [pscustomobject]@{
        append_paths = @($allowedAppends | Sort-Object -Unique)
        opaque_paths = @($opaqueVolatile | Sort-Object -Unique)
    }
}

function Compare-LiveHomeSnapshots($Before, $After, [string[]]$AllowedAppendPaths, [string[]]$OpaqueVolatilePaths) {
    $beforeMap = Get-RecordMap $Before
    $afterMap = Get-RecordMap $After
    $allowed = @{}
    foreach ($path in $AllowedAppendPaths) { $allowed[$path] = $true }
    $opaque = @{}
    foreach ($path in $OpaqueVolatilePaths) { $opaque[$path] = $true }
    $changes = New-Object System.Collections.ArrayList
    foreach ($path in @($beforeMap.Keys + $afterMap.Keys | Sort-Object -Unique)) {
        $a = $beforeMap[$path]
        $b = $afterMap[$path]
        if (Test-LiveRecordEqual $a $b) {
            continue
        }
        $appendOkay = $allowed.ContainsKey($path) -and $a -and $b -and $a.kind -eq 'FILE' -and
            $b.kind -eq 'FILE' -and $a.file_id -eq $b.file_id -and $b.length -ge $a.length -and
            (Get-FilePrefixSha256 $b.physical_path $a.length) -eq $a.sha256
        $opaqueOkay = $opaque.ContainsKey($path) -and $a -and $b -and $a.kind -eq 'FILE' -and
            $b.kind -eq 'FILE' -and $a.file_id -eq $b.file_id
        if (-not $appendOkay -and -not $opaqueOkay) {
            $null = $changes.Add($path)
        }
    }
    return [pscustomobject]@{ pass = ($changes.Count -eq 0); changes = @($changes) }
}

function Get-DirectoryInventory([string]$Root) {
    $rootFull = Get-AbsolutePath $Root
    $rows = New-Object System.Collections.ArrayList
    if (-not (Test-Path -LiteralPath $rootFull -PathType Container)) {
        return "MISSING`t.`n"
    }
    $stack = New-Object 'System.Collections.Generic.Stack[string]'
    $stack.Push($rootFull)
    while ($stack.Count -gt 0) {
        $directory = $stack.Pop()
        foreach ($item in @(Get-ChildItem -Force -LiteralPath $directory | Sort-Object FullName)) {
            $relative = $item.FullName.Substring($rootFull.Length).TrimStart('\', '/').Replace('\', '/')
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                $null = $rows.Add("REPARSE`t$relative")
                continue
            }
            if ($item.PSIsContainer) {
                $stack.Push($item.FullName)
                continue
            }
            if ($relative -ieq 'auth.json' -or $relative -ieq '.credentials.json') {
                $null = $rows.Add("REDACTED_CREDENTIAL`t$relative")
                continue
            }
            $hash = Get-Sha256File $item.FullName
            $null = $rows.Add("FILE`t$relative`t$($item.Length)`t$hash")
        }
    }
    if ($rows.Count -eq 0) {
        return "EMPTY`t.`n"
    }
    return ((@($rows) | Sort-Object) -join "`n") + "`n"
}

function Write-ConsumerInventory([string]$Label) {
    $inventoryDir = Join-Path $EvidenceDir 'inventories'
    if (-not (Test-Path -LiteralPath $inventoryDir)) {
        $null = New-Item -ItemType Directory -Path $inventoryDir
    }
    $path = Join-Path $inventoryDir "$Label.tsv"
    $text = Get-DirectoryInventory $DisposableHome
    Write-NewUtf8NoBom $path $text
    return [pscustomobject]@{
        path = $path
        sha256 = Get-Sha256Text $text
        contains_plugin = $text.Contains($script:PluginName)
    }
}

function Write-InstalledPluginEvidence([string]$Label, $Release) {
    $inventory = Write-ConsumerInventory $Label
    $manifestRelative = if ($HostName -eq 'codex') { '.codex-plugin/plugin.json' } else { '.claude-plugin/plugin.json' }
    $essential = @(
        $manifestRelative,
        'skills/mesh-probe-alpha/SKILL.md',
        'skills/mesh-probe-beta/SKILL.md',
        'shared/probe-reference.md',
        'assets/probe-helper.txt'
    )
    $roots = @{}
    $rejectedRoots = New-Object System.Collections.ArrayList
    Get-ChildItem -Force -LiteralPath $DisposableHome -Recurse -Filter 'plugin.json' -File | ForEach-Object {
        $manifestDir = Split-Path -Parent $_.FullName
        if ((Split-Path -Leaf $manifestDir) -in @('.codex-plugin', '.claude-plugin')) {
            $pluginRoot = Split-Path -Parent $manifestDir
            try {
                $manifest = Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json
                if ([string]$manifest.name -eq $script:PluginName) {
                    $canonicalRoot = Get-AbsolutePath $pluginRoot
                    try { Assert-NoReparsePoint $pluginRoot 'Installed plugin candidate' }
                    catch {
                        $null = $rejectedRoots.Add([ordered]@{ locator = ConvertTo-RedactedValue $pluginRoot; reason = $_.Exception.Message })
                        return
                    }
                    if (-not (Test-SameOrChild $canonicalRoot $script:DisposableHomeApproved)) {
                        $null = $rejectedRoots.Add([ordered]@{ locator = ConvertTo-RedactedValue $pluginRoot; reason = 'resolved outside DisposableHome' })
                        return
                    }
                    $roots[$canonicalRoot.ToLowerInvariant()] = $canonicalRoot
                }
            }
            catch { }
        }
    }

    $rows = New-Object System.Collections.ArrayList
    $matching = New-Object System.Collections.ArrayList
    foreach ($root in @($roots.Values | Sort-Object)) {
        $fileRows = New-Object System.Collections.ArrayList
        $allMatch = $true
        foreach ($relative in $essential) {
            $source = Join-Path $Release.plugin_root $relative.Replace('/', '\')
            $installed = Join-Path $root $relative.Replace('/', '\')
            if (-not (Test-Path -LiteralPath $source -PathType Leaf) -or -not (Test-Path -LiteralPath $installed -PathType Leaf)) {
                $allMatch = $false
                $null = $fileRows.Add([ordered]@{ path = $relative; status = 'MISSING'; source_sha256 = ''; installed_sha256 = '' })
                continue
            }
            $sourceHash = Get-Sha256File $source
            $installedHash = Get-Sha256File $installed
            if ($sourceHash -ne $installedHash) { $allMatch = $false }
            $null = $fileRows.Add([ordered]@{
                path = $relative
                status = if ($sourceHash -eq $installedHash) { 'MATCH' } else { 'MISMATCH' }
                source_sha256 = $sourceHash
                installed_sha256 = $installedHash
            })
        }
        if ($allMatch) { $null = $matching.Add($root) }
        $null = $rows.Add([ordered]@{
            locator = ConvertTo-RedactedValue $root
            expected_release = $Release.release
            exact_match = $allMatch
            tree_sha256 = Get-TreeHash $root
            files = @($fileRows)
        })
    }
    $locatorPath = Join-Path $EvidenceDir "inventories\$Label-plugin-locators.json"
    Write-NewUtf8NoBom $locatorPath (([ordered]@{
        inventory_sha256 = $inventory.sha256
        plugin_name = $script:PluginName
        expected_release = $Release.release
        candidates = @($rows)
        rejected_candidates = @($rejectedRoots)
        matching_locators = @($matching | ForEach-Object { ConvertTo-RedactedValue $_ })
    } | ConvertTo-Json -Depth 8) + "`n")
    return [pscustomobject]@{
        inventory_path = $inventory.path
        inventory_sha256 = $inventory.sha256
        locator_path = $locatorPath
        candidate_count = $roots.Count
        rejected_count = $rejectedRoots.Count
        matching_count = $matching.Count
    }
}

function Assert-NoNestedReparsePoint([string]$Root, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        return
    }
    $stack = New-Object 'System.Collections.Generic.Stack[string]'
    $stack.Push((Get-AbsolutePath $Root))
    while ($stack.Count -gt 0) {
        $directory = $stack.Pop()
        foreach ($item in @(Get-ChildItem -Force -LiteralPath $directory)) {
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "$Label contains a reparse point: $($item.FullName)"
            }
            if ($item.PSIsContainer) {
                $stack.Push($item.FullName)
            }
        }
    }
}

function Assert-CleanupTarget {
    if (-not $script:ProcessTreeClear) {
        throw "A child process tree is not confirmed stopped; cleanup refused"
    }
    $current = Get-AbsolutePath $DisposableHome
    if (-not $current.Equals($script:DisposableHomeApproved, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "DisposableHome no longer resolves to the approved cleanup target"
    }
    Assert-NoReparsePoint $current 'DisposableHome cleanup target'
    Assert-NoNestedReparsePoint $current 'DisposableHome cleanup target'
    $refreshedWorktreeRoots = @(Get-WorktreeRoots)
    $protected = @(
        $script:EvidenceDirApproved,
        $script:LiveClaudeHomeApproved,
        $script:LiveCodexHomeApproved,
        $script:RepoRoot
    ) + @($script:WorktreeRoots) + $refreshedWorktreeRoots
    $protected = @($protected | Sort-Object -Unique)
    foreach ($root in $protected) {
        if ((Test-SameOrChild $current $root) -or (Test-SameOrChild $root $current)) {
            throw "DisposableHome cleanup target overlaps protected root: $root"
        }
    }
    $markerPath = Join-Path $current '.skill-mesh-lifecycle-owner.json'
    if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) {
        throw "DisposableHome ownership marker is missing"
    }
    $marker = Get-Content -Raw -LiteralPath $markerPath | ConvertFrom-Json
    if ($marker.goal_a_id -ne $GoalAId -or $marker.run_id -ne $RunId -or $marker.attempt_id -ne $AttemptId -or
        -not ([string]$marker.canonical_path).Equals($current, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "DisposableHome ownership marker does not match this attempt"
    }
    return $current
}

function Get-CredentialPaths {
    if ($HostName -eq 'codex') {
        return [pscustomobject]@{
            source = Join-Path $script:LiveCodexHomeApproved 'auth.json'
            destination = Join-Path $script:DisposableHomeApproved 'auth.json'
        }
    }
    return [pscustomobject]@{
        source = Join-Path $script:LiveClaudeHomeApproved '.credentials.json'
        destination = Join-Path $script:DisposableHomeApproved '.credentials.json'
    }
}

function Assert-CredentialSource {
    if ($CredentialMode -eq 'host-store') { return }
    $paths = Get-CredentialPaths
    if (-not (Test-Path -LiteralPath $paths.source -PathType Leaf)) {
        throw "Required isolated credential source is absent"
    }
    $sourceItem = Get-Item -Force -LiteralPath $paths.source
    if (($sourceItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Credential source is a reparse point"
    }
}

function Copy-HostCredential {
    if ($CredentialMode -eq 'host-store') {
        Add-Check 'credential-isolation' 'PASS' 'host auth status' 'No credential file copied; isolated host store will be checked'
        return
    }
    Assert-CredentialSource
    $paths = Get-CredentialPaths
    Copy-Item -LiteralPath $paths.source -Destination $paths.destination
    Add-Check 'credential-isolation' 'PASS' 'credential file presence only' 'One host credential file copied to the disposable home; bytes and the ephemeral live-snapshot HMAC key are not logged'
}

function Write-DisposableCodexConfig {
    if ($HostName -ne 'codex') { return }
    $config = @(
        'cli_auth_credentials_store = "file"',
        'check_for_update_on_startup = false'
    ) -join "`n"
    Write-NewUtf8NoBom (Join-Path $script:DisposableHomeApproved 'config.toml') ($config + "`n")
    Add-Check 'codex-auth-store' 'PASS' 'config.toml' 'Codex authentication is forced to the disposable auth.json file'
}

function Update-ModelEvidence([string]$Output) {
    if ($Output -match '"model"\s*:\s*"([^"\\]+)"') {
        $script:ResolvedModel = $Matches[1]
        $script:ResolvedStatus = 'provider-reported'
    }
    elseif ($Output -match '"modelUsage"\s*:\s*\{\s*"([^"\\]+)"') {
        $script:ResolvedModel = $Matches[1]
        $script:ResolvedStatus = 'provider-reported'
    }
    if ($Output -match 'input_tokens|inputTokens|output_tokens|outputTokens|usage') {
        $script:UsageStatus = 'available in raw provider output'
    }
    if ($Output -match 'total_cost|totalCost|cost_usd|costUSD') {
        $script:CostStatus = 'available in raw provider output'
    }
}

function Get-ReducedResult {
    $statuses = @($script:Checks | ForEach-Object { $_.status })
    if ($statuses -contains 'AMBIGUOUS') { return 'AMBIGUOUS' }
    if ($statuses -contains 'FAIL') { return 'FAIL' }
    if ($statuses -contains 'UNAVAILABLE') { return 'PARTIAL' }
    return 'PASS'
}

function Replace-ActiveMarketplace([string]$Source) {
    if (Test-Path -LiteralPath $script:ActiveSource) {
        if (-not (Test-SameOrChild $script:ActiveSource $EvidenceDir)) {
            throw "Active source escaped EvidenceDir"
        }
        Remove-Item -Force -Recurse -LiteralPath $script:ActiveSource
    }
    Copy-DirectoryContents $Source $script:ActiveSource
}

function Test-OutputHasMarker([string]$Text, [string]$Skill, $Release) {
    if ($Skill -eq 'alpha') {
        $expected = "ALPHA|run=$RunId|version=$($Release.release)|reference=$($Release.reference_token)"
    }
    else {
        $expected = "BETA|run=$RunId|version=$($Release.release)|reference=$($Release.reference_token)|helper=$($Release.helper_token)"
    }
    return $Text.Contains($expected)
}

function Export-CandidateFixture {
    $archivePath = Join-Path $EvidenceDir 'candidate.zip'
    $treePath = Join-Path $EvidenceDir 'candidate-tree'
    $gitPath = (Get-Command git.exe -ErrorAction Stop).Source
    $candidatePaths = @(
        'experiments/recovery/lifecycle-probe',
        'experiments/recovery/run-lifecycle-probe.ps1',
        'tests/experiments/test_lifecycle_probe.py',
        'documentation/experiments/lifecycle-report-template.md',
        'documentation/experiments/lifecycle-runbook.md'
    )
    $arguments = @('archive', '--format=zip', "--output=$archivePath", $CandidateSha, '--') + $candidatePaths
    $archiveResult = Invoke-LoggedCommand 'candidate-archive' $gitPath $arguments @{ GIT_OPTIONAL_LOCKS = '0' } $script:RepoRoot 120
    if ($archiveResult.exit_code -ne 0 -or -not (Test-Path -LiteralPath $archivePath -PathType Leaf)) {
        throw "Candidate archive failed"
    }
    Expand-Archive -LiteralPath $archivePath -DestinationPath $treePath
    $script:CandidateTemplateRoot = Join-Path $treePath 'experiments\recovery\lifecycle-probe\marketplace-template'
    $script:ReportTemplatePath = Join-Path $treePath 'documentation\experiments\lifecycle-report-template.md'
    if (-not (Test-Path -LiteralPath $script:CandidateTemplateRoot -PathType Container) -or
        -not (Test-Path -LiteralPath $script:ReportTemplatePath -PathType Leaf)) {
        throw "Candidate archive is missing a Step 74 input"
    }
    $archiveHash = Get-Sha256File $archivePath
    Add-Check 'candidate-source' 'PASS' 'candidate.zip' "commit=$CandidateSha; archive_sha256=$archiveHash"
}

function New-ConsumerPrompt([string]$Skill) {
    if ($Skill -eq 'alpha') {
        $skillName = 'mesh-probe-alpha'
        $trigger = $script:TriggerAlpha
    }
    else {
        $skillName = 'mesh-probe-beta'
        $trigger = $script:TriggerBeta
    }
    if ($HostName -eq 'claude') {
        $qualified = "/$($script:PluginName):$skillName"
    }
    else {
        $qualified = "`$$($script:PluginName):$skillName"
    }
    return "Use the installed skill $qualified that matches trigger $trigger. Follow that skill and return only its marker line."
}

function Invoke-Consumer([string]$Id, [string]$Skill, $ExpectedRelease, [bool]$ExpectPresent, $StaleRelease) {
    $prompt = New-ConsumerPrompt $Skill
    if ($prompt.Contains($RunId) -or $prompt.Contains($ExpectedRelease.reference_token) -or
        ($Skill -eq 'beta' -and $prompt.Contains($ExpectedRelease.helper_token))) {
        Stop-Probe 'AMBIGUOUS' "Consumer prompt exposes a hidden marker"
    }
    if ($HostName -eq 'codex') {
        $arguments = @('exec', '-C', $script:ConsumerRoot, '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-m', $RequestedModel, $prompt)
    }
    else {
        $arguments = @('-p', $prompt, '--output-format', 'json', '--permission-mode', 'auto', '--no-session-persistence', '--model', $RequestedModel, '--tools', 'Skill,Read', '--allowedTools', 'Skill,Read')
    }
    $result = Invoke-HostCommand $Id $arguments $script:HostEnvironment $script:ConsumerRoot $ConsumerTimeoutSeconds
    Assert-ProbeCommand $result "Consumer call '$Id' failed"
    Update-ModelEvidence $result.stdout
    if ($ExpectPresent) {
        if (-not (Test-OutputHasMarker $result.stdout $Skill $ExpectedRelease)) {
            Stop-Probe 'FAIL' "Consumer call '$Id' did not return the expected $($ExpectedRelease.release) $Skill marker"
        }
        if ($StaleRelease -and ($result.stdout.Contains($StaleRelease.reference_token) -or
            ($Skill -eq 'beta' -and $result.stdout.Contains($StaleRelease.helper_token)))) {
            Stop-Probe 'FAIL' "Consumer call '$Id' returned a stale marker"
        }
        Add-Check $Id 'PASS' $result.evidence_dir "$Skill returned $($ExpectedRelease.release) markers"
    }
    else {
        $hasMarker = $result.stdout.Contains("ALPHA|run=$RunId|") -or $result.stdout.Contains("BETA|run=$RunId|")
        if ($hasMarker) {
            Stop-Probe 'FAIL' "Consumer call '$Id' discovered a marker after the plugin should be unavailable"
        }
        Add-Check $Id 'PASS' $result.evidence_dir 'No run-specific marker was discoverable'
    }
    return $result
}

function Invoke-CodexRepeatAddObservation($V1, $V2) {
    $prompt = New-ConsumerPrompt 'alpha'
    $arguments = @('exec', '-C', $script:ConsumerRoot, '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-m', $RequestedModel, $prompt)
    $result = Invoke-HostCommand 'consumer-alpha-after-repeat-add' $arguments $script:HostEnvironment $script:ConsumerRoot $ConsumerTimeoutSeconds
    if ($result.exit_code -ne 0) {
        Assert-ProbeCommand $result 'Codex repeat-add observation failed'
    }
    Update-ModelEvidence $result.stdout
    if (Test-OutputHasMarker $result.stdout 'alpha' $V2) {
        Add-Check 'repeat-add-observation' 'PASS' $result.evidence_dir 'repeat-add exposed v2; this is compatibility behavior, not a native update command'
        return
    }
    if (Test-OutputHasMarker $result.stdout 'alpha' $V1) {
        Add-Check 'repeat-add-observation' 'UNAVAILABLE' $result.evidence_dir 'repeat-add retained v1; Codex has no native update command'
        return
    }
    Stop-Probe 'AMBIGUOUS' "Codex repeat-add observation returned neither trustworthy v1 nor v2 markers"
}

function Assert-ListedState([string]$Text, [bool]$ShouldContain, [string]$Label) {
    $contains = $Text.Contains($script:PluginName)
    if ($contains -ne $ShouldContain) {
        Stop-Probe 'FAIL' "$Label did not show the expected plugin presence state"
    }
}

function Get-CodexPluginCommandNames([string]$HelpText) {
    $commands = New-Object System.Collections.ArrayList
    $insideCommands = $false
    foreach ($line in @($HelpText -split "`r?`n")) {
        if ($line -match '^Commands:\s*$') {
            $insideCommands = $true
            continue
        }
        if ($insideCommands -and $line -match '^[A-Za-z][A-Za-z ]*:\s*$') {
            break
        }
        if ($insideCommands -and $line -match '^\s{2,}([a-z][a-z0-9-]*)\s{2,}') {
            $null = $commands.Add($Matches[1])
        }
    }
    $commands = @($commands | Sort-Object -Unique)
    foreach ($required in @('add', 'list', 'marketplace', 'remove')) {
        if ($required -notin $commands) {
            Stop-Probe 'AMBIGUOUS' "Codex plugin help did not expose the expected '$required' command"
        }
    }
    return $commands
}

function Assert-CodexNativeSurface([string]$HelpText, [string]$Evidence, [string]$HostVersion) {
    $pluginCommands = @(Get-CodexPluginCommandNames $HelpText)
    $newNativeCommands = @($pluginCommands | Where-Object { $_ -in @('update', 'enable', 'disable') })
    if ($newNativeCommands.Count -gt 0) {
        Stop-Probe 'AMBIGUOUS' "Codex now exposes a native plugin command that this frozen experiment does not exercise: $($newNativeCommands -join ', ')"
    }
    Add-Check 'native-update' 'UNAVAILABLE' $Evidence "$HostVersion exposes no plugin update command"
    Add-Check 'native-enable-disable' 'UNAVAILABLE' $Evidence "$HostVersion exposes no plugin enable or disable command; feature flags are not substitutes"
}

function Find-PluginStateObjects($Value, $Results) {
    if ($null -eq $Value -or $Value -is [string] -or $Value -is [ValueType]) { return }
    if ($Value -is [System.Collections.IEnumerable] -and -not ($Value -is [pscustomobject])) {
        foreach ($item in $Value) { Find-PluginStateObjects $item $Results }
        return
    }
    $properties = @($Value.PSObject.Properties)
    $identifiesPlugin = @($properties | Where-Object {
        $_.Value -is [string] -and ([string]$_.Value).Contains($script:PluginName)
    }).Count -gt 0
    $enabledProperty = $properties | Where-Object { $_.Name -ieq 'enabled' } | Select-Object -First 1
    if ($identifiesPlugin -and $enabledProperty) {
        $null = $Results.Add([bool]$enabledProperty.Value)
    }
    foreach ($property in $properties) {
        Find-PluginStateObjects $property.Value $Results
    }
}

function Assert-ClaudeEnabledState([string]$Text, [bool]$Expected, [string]$Label) {
    try { $payload = $Text | ConvertFrom-Json }
    catch { Stop-Probe 'FAIL' "$Label did not return valid JSON" }
    $states = New-Object System.Collections.ArrayList
    Find-PluginStateObjects $payload $states
    if ($states.Count -eq 0) {
        Stop-Probe 'FAIL' "$Label did not bind an enabled state to the target plugin"
    }
    if (@($states | Where-Object { $_ -ne $Expected }).Count -gt 0) {
        Stop-Probe 'FAIL' "$Label reported an unexpected enabled state for the target plugin"
    }
}

function Write-ReportAndManifest([string]$Result, [string]$FailureReason, $V1, $V2, [string]$LiveBeforeHash, [string]$LiveAfterHash) {
    $templatePath = $script:ReportTemplatePath
    if (-not (Test-Path -LiteralPath $templatePath)) {
        throw "Report template is missing: $templatePath"
    }
    $template = [System.IO.File]::ReadAllText($templatePath)
    $checkRows = @($script:Checks | ForEach-Object {
        $evidence = ConvertTo-RedactedValue ([string]$_.evidence)
        $detail = (ConvertTo-RedactedValue ([string]$_.detail)).Replace('|', '/').Replace("`r", ' ').Replace("`n", ' ')
        "| $($_.name) | $($_.status) | $evidence | $detail |"
    }) -join "`n"
    $commandRows = @($script:CommandResults | ForEach-Object {
        "| $($_.sequence)-$($_.id) | $($_.exit_code) | $($_.duration_seconds) | `commands/$($_.sequence)-$($_.id)/argv.json` |"
    }) -join "`n"
    $commandArguments = @($script:CommandResults | ForEach-Object {
        $argsJson = @($_.arguments) | ConvertTo-Json -Compress
        "- ``$($_.sequence)-$($_.id)``: ``$argsJson``"
    }) -join "`n"
    $unresolvedPremises = @($script:Checks | Where-Object { $_.status -in @('UNAVAILABLE', 'AMBIGUOUS') } | ForEach-Object {
        "- $($_.name): $(ConvertTo-RedactedValue ([string]$_.detail))"
    })
    if ($unresolvedPremises.Count -eq 0) { $unresolvedPremises = @('- None recorded.') }
    $report = $template.Replace('{{RUN_ID}}', $RunId)
    $report = $report.Replace('{{GOAL_A_ID}}', $GoalAId)
    $report = $report.Replace('{{ATTEMPT_ID}}', $AttemptId)
    $report = $report.Replace('{{HOST}}', $HostName)
    $report = $report.Replace('{{CANDIDATE_SHA}}', $CandidateSha)
    $report = $report.Replace('{{CREDENTIAL_MODE}}', $CredentialMode)
    $report = $report.Replace('{{RESULT}}', $Result)
    $report = $report.Replace('{{FAILURE_REASON}}', $(if ($FailureReason) { ConvertTo-RedactedValue $FailureReason } else { 'none' }))
    $report = $report.Replace('{{SOURCE_SHA}}', $CandidateSha)
    $report = $report.Replace('{{PLUGIN_NAME}}', $script:PluginName)
    $report = $report.Replace('{{MARKETPLACE_NAME}}', $script:MarketplaceName)
    $report = $report.Replace('{{REQUESTED_MODEL}}', $RequestedModel)
    $report = $report.Replace('{{RESOLVED_MODEL}}', $script:ResolvedModel)
    $report = $report.Replace('{{RESOLVED_STATUS}}', $script:ResolvedStatus)
    $report = $report.Replace('{{USAGE_STATUS}}', $script:UsageStatus)
    $report = $report.Replace('{{COST_STATUS}}', $script:CostStatus)
    $report = $report.Replace('{{HOST_EXECUTABLE}}', (Split-Path -Leaf $script:HostExecutablePath))
    $report = $report.Replace('{{HOST_EXECUTABLE_SHA}}', $script:HostExecutableSha256)
    $report = $report.Replace('{{HOST_VERSION}}', $script:HostVersion.Replace("`r", ' ').Replace("`n", ' '))
    $report = $report.Replace('{{V1_TREE_HASH}}', $V1.tree_sha256)
    $report = $report.Replace('{{V2_TREE_HASH}}', $V2.tree_sha256)
    $report = $report.Replace('{{LIVE_BEFORE_HASH}}', $LiveBeforeHash)
    $report = $report.Replace('{{LIVE_AFTER_HASH}}', $LiveAfterHash)
    $report = $report.Replace('{{CLEANUP_NOTES}}', ((ConvertTo-RedactedValue (@($script:CleanupNotes) -join '; ')).Replace('|', '/')))
    $report = $report.Replace('{{CHECK_ROWS}}', $checkRows)
    $report = $report.Replace('{{COMMAND_ROWS}}', $commandRows)
    $report = $report.Replace('{{COMMAND_ARGUMENTS}}', $commandArguments)
    $report = $report.Replace('{{UNRESOLVED_PREMISES}}', ($unresolvedPremises -join "`n"))
    if ($report -match '\{\{[A-Z0-9_]+\}\}') {
        throw "Unresolved report-template token '$($Matches[0])'"
    }
    Write-NewUtf8NoBom (Join-Path $EvidenceDir 'report.md') $report

    $manifestRows = New-Object System.Collections.ArrayList
    Get-ChildItem -Force -LiteralPath $EvidenceDir -Recurse -File |
        Where-Object { $_.Name -ne 'manifest.sha256' } |
        Sort-Object FullName |
        ForEach-Object {
            $relative = $_.FullName.Substring((Get-AbsolutePath $EvidenceDir).Length + 1).Replace('\', '/')
            $hash = Get-Sha256File $_.FullName
            $null = $manifestRows.Add("$hash  $relative")
        }
    Write-NewUtf8NoBom (Join-Path $EvidenceDir 'manifest.sha256') ((@($manifestRows) -join "`n") + "`n")
}

function Invoke-LifecycleProbe {
Assert-RequiredParameters
Assert-ProbePaths
Assert-CandidateIdentity

$script:ReportTemplatePath = Join-Path $script:RepoRoot 'documentation\experiments\lifecycle-report-template.md'
if (-not (Test-Path -LiteralPath $script:ReportTemplatePath -PathType Leaf)) {
    throw "Report template is missing: $($script:ReportTemplatePath)"
}

if ($HostName -eq 'codex') {
    $script:HostExecutablePath = (Get-Command codex -ErrorAction Stop).Source
}
else {
    $script:HostExecutablePath = (Get-Command claude -ErrorAction Stop).Source
}
$script:HostExecutableSha256 = Get-Sha256File $script:HostExecutablePath
$script:HostVersion = 'not run'

$script:ProbeId = (Get-Sha256Text $RunId).Substring(0, 12)
$script:PluginName = "skill-mesh-lifecycle-$($script:ProbeId)"
$script:MarketplaceName = "skill-mesh-lifecycle-market-$($script:ProbeId)"
$script:TriggerAlpha = "SMLP-$($script:ProbeId.ToUpperInvariant())-ALPHA"
$script:TriggerBeta = "SMLP-$($script:ProbeId.ToUpperInvariant())-BETA"
$script:ResolvedModel = "unavailable"
$script:ResolvedStatus = "unavailable"
$script:ActiveSource = Join-Path $EvidenceDir 'source\current'
$sourceV1 = Join-Path $EvidenceDir 'source\v1'
$sourceV2 = Join-Path $EvidenceDir 'source\v2'
$consumerRoot = Join-Path $DisposableHome 'consumer-workspace'
$script:ConsumerRoot = $consumerRoot
$selector = "$($script:PluginName)@$($script:MarketplaceName)"
$profileRoot = Join-Path $DisposableHome 'profile'
$appDataRoot = Join-Path $DisposableHome 'appdata\roaming'
$localAppDataRoot = Join-Path $DisposableHome 'appdata\local'
$tempRoot = Join-Path $DisposableHome 'tmp'
$homeDrive = [System.IO.Path]::GetPathRoot($profileRoot).TrimEnd('\', '/')
$homePath = $profileRoot.Substring($homeDrive.Length)
$script:HostEnvironment = @{
    USERPROFILE = $profileRoot
    HOME = $profileRoot
    HOMEDRIVE = $homeDrive
    HOMEPATH = $homePath
    APPDATA = $appDataRoot
    LOCALAPPDATA = $localAppDataRoot
    TEMP = $tempRoot
    TMP = $tempRoot
}
if ($HostName -eq 'codex') {
    $script:HostEnvironment['CODEX_HOME'] = $script:DisposableHomeApproved
    $script:HostEnvironment['CODEX_SQLITE_HOME'] = $script:DisposableHomeApproved
}
else {
    $script:HostEnvironment['CLAUDE_CONFIG_DIR'] = $script:DisposableHomeApproved
    $script:HostEnvironment['CLAUDE_CODE_PLUGIN_CACHE_DIR'] = (Join-Path $script:DisposableHomeApproved 'plugins')
    $script:HostEnvironment['CLAUDE_CODE_DISABLE_AUTO_MEMORY'] = '1'
    $script:HostEnvironment['CLAUDE_CODE_SKIP_PROMPT_HISTORY'] = '1'
    $script:HostEnvironment['CLAUDE_CODE_SYNC_PLUGIN_INSTALL'] = '1'
    $script:HostEnvironment['CLAUDE_CODE_AUTO_CONNECT_IDE'] = 'false'
    $script:HostEnvironment['DISABLE_AUTOUPDATER'] = '1'
}

if ($HostName -eq 'codex') {
    $plannedOperations = @(
        'codex --version and login status',
        'marketplace add/list; plugin available/add/list',
        'fresh alpha and beta v1 consumers',
        'source switch; pre-operation v1 consumer',
        'record native update unavailable; observe repeat-add',
        'compatibility remove and reinstall from v2 source',
        'fresh alpha and beta v2 consumers',
        'record enable/disable unavailable',
        'plugin remove; marketplace remove; fresh non-discovery consumer'
    )
}
else {
    $plannedOperations = @(
        'claude --version, auth status, and strict plugin validation',
        'marketplace add/list; plugin install/list',
        'fresh alpha and beta v1 consumers',
        'source switch; pre-update v1 consumer',
        'marketplace update; native plugin update; plugin list',
        'fresh alpha and beta v2 consumers',
        'disable/list/non-discovery; enable/list/v2 rediscovery',
        'uninstall; marketplace remove; list; fresh non-discovery consumer'
    )
}
$plannedOperations = @('bounded candidate-owned live-root snapshots before and after host operations') + @($plannedOperations)

$alphaPrompt = New-ConsumerPrompt 'alpha'
$betaPrompt = New-ConsumerPrompt 'beta'
if ($HostName -eq 'codex') {
    $commandArgumentMap = [ordered]@{
        'host-version' = @('--strict-config', '--version')
        'plugin-help' = @('--strict-config', 'plugin', '--help')
        'marketplace-help' = @('--strict-config', 'plugin', 'marketplace', '--help')
        'plugin-add-help' = @('--strict-config', 'plugin', 'add', '--help')
        'plugin-remove-help' = @('--strict-config', 'plugin', 'remove', '--help')
        'auth-status' = @('--strict-config', 'login', 'status')
        'consumer-alpha-before-install' = @('--strict-config', 'exec', '-C', $consumerRoot, '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-m', $RequestedModel, $alphaPrompt)
        'consumer-beta-before-install' = @('--strict-config', 'exec', '-C', $consumerRoot, '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-m', $RequestedModel, $betaPrompt)
        'marketplace-add-v1' = @('--strict-config', 'plugin', 'marketplace', 'add', $script:ActiveSource, '--json')
        'marketplace-list-v1' = @('--strict-config', 'plugin', 'marketplace', 'list', '--json')
        'plugin-available-v1' = @('--strict-config', 'plugin', 'list', '--marketplace', $script:MarketplaceName, '--available', '--json')
        'plugin-install-v1' = @('--strict-config', 'plugin', 'add', $selector, '--json')
        'plugin-list-v1' = @('--strict-config', 'plugin', 'list', '--marketplace', $script:MarketplaceName, '--json')
        'consumer-alpha-v1' = @('--strict-config', 'exec', '-C', $consumerRoot, '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-m', $RequestedModel, $alphaPrompt)
        'consumer-beta-v1' = @('--strict-config', 'exec', '-C', $consumerRoot, '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-m', $RequestedModel, $betaPrompt)
        'consumer-alpha-before-operation' = @('--strict-config', 'exec', '-C', $consumerRoot, '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-m', $RequestedModel, $alphaPrompt)
        'plugin-repeat-add-v2' = @('--strict-config', 'plugin', 'add', $selector, '--json')
        'consumer-alpha-after-repeat-add' = @('--strict-config', 'exec', '-C', $consumerRoot, '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-m', $RequestedModel, $alphaPrompt)
        'compat-remove-v1' = @('--strict-config', 'plugin', 'remove', $selector, '--json')
        'compat-marketplace-remove-v1' = @('--strict-config', 'plugin', 'marketplace', 'remove', $script:MarketplaceName, '--json')
        'compat-marketplace-add-v2' = @('--strict-config', 'plugin', 'marketplace', 'add', $script:ActiveSource, '--json')
        'compat-install-v2' = @('--strict-config', 'plugin', 'add', $selector, '--json')
        'plugin-list-v2' = @('--strict-config', 'plugin', 'list', '--marketplace', $script:MarketplaceName, '--json')
        'consumer-alpha-v2' = @('--strict-config', 'exec', '-C', $consumerRoot, '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-m', $RequestedModel, $alphaPrompt)
        'consumer-beta-v2' = @('--strict-config', 'exec', '-C', $consumerRoot, '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-m', $RequestedModel, $betaPrompt)
        'plugin-remove-final' = @('--strict-config', 'plugin', 'remove', $selector, '--json')
        'marketplace-remove-final' = @('--strict-config', 'plugin', 'marketplace', 'remove', $script:MarketplaceName, '--json')
        'plugin-list-after-remove' = @('--strict-config', 'plugin', 'list', '--json')
        'consumer-after-uninstall' = @('--strict-config', 'exec', '-C', $consumerRoot, '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-m', $RequestedModel, $alphaPrompt)
    }
}
else {
    $claudeAlpha = @('-p', $alphaPrompt, '--output-format', 'json', '--permission-mode', 'auto', '--no-session-persistence', '--model', $RequestedModel, '--tools', 'Skill,Read', '--allowedTools', 'Skill,Read')
    $claudeBeta = @('-p', $betaPrompt, '--output-format', 'json', '--permission-mode', 'auto', '--no-session-persistence', '--model', $RequestedModel, '--tools', 'Skill,Read', '--allowedTools', 'Skill,Read')
    $commandArgumentMap = [ordered]@{
        'host-version' = @('--version')
        'plugin-validate-v1' = @('plugin', 'validate', $script:ActiveSource, '--strict')
        'auth-status' = @('auth', 'status', '--json')
        'consumer-alpha-before-install' = $claudeAlpha
        'consumer-beta-before-install' = $claudeBeta
        'marketplace-add-v1' = @('plugin', 'marketplace', 'add', $script:ActiveSource, '--scope', 'user')
        'marketplace-list-v1' = @('plugin', 'marketplace', 'list', '--json')
        'plugin-install-v1' = @('plugin', 'install', $selector, '--scope', 'user')
        'plugin-list-v1' = @('plugin', 'list', '--json')
        'consumer-alpha-v1' = $claudeAlpha
        'consumer-beta-v1' = $claudeBeta
        'consumer-alpha-before-update' = $claudeAlpha
        'marketplace-update-v2' = @('plugin', 'marketplace', 'update', $script:MarketplaceName)
        'plugin-update-v2' = @('plugin', 'update', $selector, '--scope', 'user')
        'plugin-list-v2' = @('plugin', 'list', '--json')
        'consumer-alpha-v2' = $claudeAlpha
        'consumer-beta-v2' = $claudeBeta
        'plugin-disable' = @('plugin', 'disable', $selector, '--scope', 'user')
        'plugin-list-disabled' = @('plugin', 'list', '--json')
        'consumer-while-disabled' = $claudeAlpha
        'plugin-enable' = @('plugin', 'enable', $selector, '--scope', 'user')
        'plugin-list-enabled' = @('plugin', 'list', '--json')
        'consumer-after-enable' = $claudeAlpha
        'plugin-uninstall' = @('plugin', 'uninstall', $selector, '--scope', 'user', '-y')
        'marketplace-remove' = @('plugin', 'marketplace', 'remove', $script:MarketplaceName, '--scope', 'user')
        'plugin-list-after-remove' = @('plugin', 'list', '--json')
        'consumer-after-uninstall' = $claudeAlpha
    }
}
$candidateArchivePlan = [ordered]@{
    id = 'candidate-archive'
    executable = 'git.exe'
    arguments = @(
        'archive', '--format=zip', "--output=$(Join-Path $EvidenceDir 'candidate.zip')", $CandidateSha, '--',
        'experiments/recovery/lifecycle-probe',
        'experiments/recovery/run-lifecycle-probe.ps1',
        'tests/experiments/test_lifecycle_probe.py',
        'documentation/experiments/lifecycle-report-template.md',
        'documentation/experiments/lifecycle-runbook.md'
    ) | ForEach-Object { ConvertTo-RedactedValue ([string]$_) }
}
$plannedCommands = @($candidateArchivePlan) + @($commandArgumentMap.GetEnumerator() | ForEach-Object {
    [ordered]@{ id = $_.Key; executable = (Split-Path -Leaf $script:HostExecutablePath); arguments = @($_.Value | ForEach-Object { ConvertTo-RedactedValue ([string]$_) }) }
})
$plannedCommandIds = @($plannedCommands | ForEach-Object { $_.id })
$plannedCommandEvidenceTargets = New-Object System.Collections.ArrayList
$plannedSequence = 0
foreach ($command in $plannedCommands) {
    $plannedSequence++
    $commandRoot = Join-Path $EvidenceDir "commands\$($plannedSequence.ToString('D2'))-$($command.id)"
    foreach ($leaf in @(
        'argv.json', 'target-stdout.raw', 'target-stderr.raw', 'stdout.txt', 'stderr.txt',
        'result.txt', 'containment.json', 'containment-helper-stderr.txt',
        'containment-helper-termination.txt'
    )) {
        $null = $plannedCommandEvidenceTargets.Add((Join-Path $commandRoot $leaf))
    }
}

$fixtureFiles = @(
    '.agents/plugins/marketplace.json',
    '.claude-plugin/marketplace.json',
    "plugins/$($script:PluginName)/.claude-plugin/plugin.json",
    "plugins/$($script:PluginName)/.codex-plugin/plugin.json",
    "plugins/$($script:PluginName)/assets/probe-helper.txt",
    "plugins/$($script:PluginName)/shared/probe-reference.md",
    "plugins/$($script:PluginName)/skills/mesh-probe-alpha/SKILL.md",
    "plugins/$($script:PluginName)/skills/mesh-probe-beta/SKILL.md"
)
$renderedTargets = New-Object System.Collections.ArrayList
foreach ($root in @($sourceV1, $sourceV2, $script:ActiveSource)) {
    foreach ($relative in $fixtureFiles) {
        $null = $renderedTargets.Add((Join-Path $root $relative.Replace('/', '\')))
    }
}
$plannedTempRoot = $tempRoot

$plan = [ordered]@{
    host = $HostName
    run_id = $RunId
    attempt_id = $AttemptId
    requested_model = $RequestedModel
    credential_mode = $CredentialMode
    candidate_sha = $CandidateSha
    candidate_source = 'git archive of the exact Step 74 candidate'
    host_executable = $script:HostExecutablePath
    host_executable_sha256 = $script:HostExecutableSha256
    disposable_home = Get-AbsolutePath $DisposableHome
    evidence_dir = Get-AbsolutePath $EvidenceDir
    live_claude_home = Get-AbsolutePath $LiveClaudeHome
    live_codex_home = Get-AbsolutePath $LiveCodexHome
    plugin_name = $script:PluginName
    marketplace_name = $script:MarketplaceName
    source_v1 = $sourceV1
    source_v2 = $sourceV2
    active_source = $script:ActiveSource
    consumer_root = $consumerRoot
    create_directories = @(
        (Split-Path -Parent $EvidenceDir), (Split-Path -Parent $DisposableHome),
        $EvidenceDir, $DisposableHome, $consumerRoot, $plannedTempRoot, $profileRoot,
        $appDataRoot, $localAppDataRoot,
        (Join-Path $EvidenceDir 'candidate-tree'), $sourceV1, $sourceV2, $script:ActiveSource,
        (Join-Path $EvidenceDir 'commands'), (Join-Path $EvidenceDir 'inventories')
    )
    write_targets = @(@(
        (Join-Path $DisposableHome '.skill-mesh-lifecycle-owner.json'),
        (Join-Path $EvidenceDir 'plan.json'), (Join-Path $EvidenceDir 'candidate.zip'),
        (Join-Path $EvidenceDir 'live-surface-before.tsv'), (Join-Path $EvidenceDir 'live-surface-before.sha256'),
        (Join-Path $EvidenceDir 'live-surface-after.tsv'), (Join-Path $EvidenceDir 'live-surface-after.sha256'),
        (Join-Path $EvidenceDir 'live-append-allowlist.txt'),
        (Join-Path $EvidenceDir 'live-volatile-allowlist.txt'),
        (Join-Path $EvidenceDir 'inventories\installed-v1.tsv'),
        (Join-Path $EvidenceDir 'inventories\installed-v1-plugin-locators.json'),
        (Join-Path $EvidenceDir 'inventories\installed-v2.tsv'),
        (Join-Path $EvidenceDir 'inventories\installed-v2-plugin-locators.json'),
        (Join-Path $EvidenceDir 'inventories\after-uninstall.tsv'),
        (Join-Path $EvidenceDir 'inventories\before-cleanup.tsv'),
        (Join-Path $EvidenceDir 'report.md'),
        (Join-Path $EvidenceDir 'fallback-report.txt'),
        (Join-Path $EvidenceDir 'manifest.sha256')
    ) + $(if ($HostName -eq 'codex') { @((Join-Path $DisposableHome 'config.toml')) } else { @() }) + @($plannedCommandEvidenceTargets))
    rendered_fixture_files = @($renderedTargets)
    protected_roots = @($script:LiveClaudeHomeApproved, $script:LiveCodexHomeApproved, $script:RepoRoot) + @($script:WorktreeRoots)
    operations = $plannedOperations
    planned_command_ids = $plannedCommandIds
    planned_commands = $plannedCommands
    credential_source = if ($HostName -eq 'codex') { '<LIVE_CODEX_HOME>/auth.json' } else { '<LIVE_CLAUDE_HOME>/.credentials.json' }
    credential_destination = if ($HostName -eq 'codex') { (Join-Path $DisposableHome 'auth.json') } else { (Join-Path $DisposableHome '.credentials.json') }
    cleanup_target = $DisposableHome
    host_managed_write_root = $DisposableHome
    candidate_tree_root = (Join-Path $EvidenceDir 'candidate-tree')
    cleanup = "remove plugin and marketplace, delete only the marked DisposableHome, retain EvidenceDir"
    child_environment_policy = [ordered]@{
        scrub_provider_prefixes = @('ANTHROPIC_*', 'OPENAI_*', 'CODEX_*', 'CLAUDE_CODE_*', 'CHATGPT_*', 'cloud and local provider routing keys')
        explicit_overrides = @($script:HostEnvironment.Keys | Sort-Object)
        codex_auth_store = if ($HostName -eq 'codex') { 'file in DisposableHome/auth.json with --strict-config' } else { 'not applicable' }
    }
    live_snapshot = [ordered]@{
        helper = '<REPO_ROOT>/experiments/recovery/lifecycle-probe/live_snapshot.py'
        invocation = 'python -I -B <helper>; request and ephemeral HMAC key are sent only on redirected stdin'
        deadline_seconds = $script:LiveSnapshotDeadlineSeconds
        parent_timeout_seconds = [int]($script:LiveSnapshotParentTimeoutMilliseconds / 1000)
        max_records = $script:LiveSnapshotMaxRecords
        roots = @('<LIVE_CLAUDE_HOME>', '<LIVE_CODEX_HOME>', '<USERPROFILE>/.agents', 'unique local reparse targets')
        limits = "$($script:LiveSnapshotDeadlineSeconds) seconds and $($script:LiveSnapshotMaxRecords) records per complete snapshot; parent process timeout is $([int]($script:LiveSnapshotParentTimeoutMilliseconds / 1000)) seconds"
        credential_comparison = 'ephemeral HMAC held in runner memory; no credential digest, bytes, or key is retained'
    }
    process_containment = [ordered]@{
        helper = '<REPO_ROOT>/experiments/recovery/lifecycle-probe/job_process.py'
        invocation = 'python -I -B <helper>; command metadata is sent on redirected stdin; environment values are inherited, not serialized'
        policy = 'create suspended; assign to an unnamed kill-on-close Windows Job Object; resume; confirm active process count reaches zero'
        boundary = 'ordinary CreateProcess descendants are contained; work delegated through an unrelated system service is outside this bounded experiment'
    }
}

Assert-CredentialSource

if ($WhatIf) {
    $plan | ConvertTo-Json -Depth 5
    $script:LifecycleExitCode = 0
    return
}

$quietFirst = Get-LiveHomeSnapshot $script:LiveClaudeHomeApproved $script:LiveCodexHomeApproved
Start-Sleep -Seconds 2
$liveBefore = Get-LiveHomeSnapshot $script:LiveClaudeHomeApproved $script:LiveCodexHomeApproved
$preflightVolatility = Get-PreflightVolatility $quietFirst $liveBefore
$allowedLiveAppends = @($preflightVolatility.append_paths)
$opaqueLiveVolatility = @($preflightVolatility.opaque_paths)

try {
$null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $EvidenceDir)
$null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $DisposableHome)
$null = New-Item -ItemType Directory -Path $EvidenceDir
$null = New-Item -ItemType Directory -Path $DisposableHome
$null = New-Item -ItemType Directory -Path $consumerRoot
$null = New-Item -ItemType Directory -Path $tempRoot
$null = New-Item -ItemType Directory -Path $profileRoot
$null = New-Item -ItemType Directory -Force -Path $appDataRoot
$null = New-Item -ItemType Directory -Force -Path $localAppDataRoot
$ownershipMarker = [ordered]@{
    goal_a_id = $GoalAId
    run_id = $RunId
    attempt_id = $AttemptId
    canonical_path = $script:DisposableHomeApproved
}
Write-Utf8NoBom (Join-Path $DisposableHome '.skill-mesh-lifecycle-owner.json') (($ownershipMarker | ConvertTo-Json) + "`n")
Write-NewUtf8NoBom (Join-Path $EvidenceDir 'plan.json') (($plan | ConvertTo-Json -Depth 5) + "`n")

$liveBeforeHash = $liveBefore.public_sha256
Write-NewUtf8NoBom (Join-Path $EvidenceDir 'live-surface-before.tsv') $liveBefore.public_text
Write-NewUtf8NoBom (Join-Path $EvidenceDir 'live-surface-before.sha256') ($liveBeforeHash + "`n")
Write-NewUtf8NoBom (Join-Path $EvidenceDir 'live-append-allowlist.txt') ((@($allowedLiveAppends) -join "`n") + "`n")
Write-NewUtf8NoBom (Join-Path $EvidenceDir 'live-volatile-allowlist.txt') ((@($opaqueLiveVolatility) -join "`n") + "`n")
if ($opaqueLiveVolatility.Count -gt 0) {
    Add-Check 'live-root-concurrent-volatility' 'AMBIGUOUS' 'live-volatile-allowlist.txt' "Opaque live Codex database activity prevents safe attribution: $($opaqueLiveVolatility -join ', ')"
}
elseif ($allowedLiveAppends.Count -gt 0) {
    Add-Check 'live-root-concurrent-volatility' 'UNAVAILABLE' 'live-append-allowlist.txt' "Exact pre-existing Codex session files grew append-only during the sample: $($allowedLiveAppends -join ', ')"
}

$v1 = $null
$v2 = $null
$runFailure = $null
$environment = $script:HostEnvironment

try {
    if ($opaqueLiveVolatility.Count -gt 0) {
        Stop-Probe 'AMBIGUOUS' 'Opaque live Codex database activity must quiesce before the lifecycle experiment can run'
    }
    Export-CandidateFixture
    $v1 = New-MaterializedMarketplace $sourceV1 'v1'
    $v2 = New-MaterializedMarketplace $sourceV2 'v2'
    if ($v1.tree_sha256 -eq $v2.tree_sha256) {
        throw "v1 and v2 tree hashes are identical"
    }
    Replace-ActiveMarketplace $sourceV1
    Add-Check 'materialized-v1-v2' 'PASS' 'source/v1; source/v2' "v1=$($v1.tree_sha256); v2=$($v2.tree_sha256)"
    Write-DisposableCodexConfig
    Copy-HostCredential

    if ($HostName -eq 'codex') {
        $versionResult = Invoke-HostCommand 'host-version' @('--version') $environment $consumerRoot
        $script:HostVersion = ($versionResult.stdout + ' ' + $versionResult.stderr).Trim()
        Add-Check 'host-version' $(if ($versionResult.exit_code -eq 0) { 'PASS' } else { 'FAIL' }) $versionResult.evidence_dir $script:HostVersion
        Assert-ProbeCommand $versionResult 'Codex version command failed'

        $pluginHelp = Invoke-HostCommand 'plugin-help' @('plugin', '--help') $environment $consumerRoot
        $marketHelp = Invoke-HostCommand 'marketplace-help' @('plugin', 'marketplace', '--help') $environment $consumerRoot
        $addHelp = Invoke-HostCommand 'plugin-add-help' @('plugin', 'add', '--help') $environment $consumerRoot
        $removeHelp = Invoke-HostCommand 'plugin-remove-help' @('plugin', 'remove', '--help') $environment $consumerRoot
        $helpResults = @($pluginHelp, $marketHelp, $addHelp, $removeHelp)
        foreach ($helpResult in $helpResults) { Assert-ProbeCommand $helpResult 'Codex lifecycle help capture failed' }
        Assert-CodexNativeSurface ($pluginHelp.stdout + "`n" + $pluginHelp.stderr) $pluginHelp.evidence_dir $script:HostVersion

        $auth = Invoke-HostCommand 'auth-status' @('login', 'status') $environment $consumerRoot
        if ($auth.exit_code -ne 0 -or -not (($auth.stdout + $auth.stderr) -match 'Logged in')) { Stop-Probe 'AMBIGUOUS' "Codex isolated auth status is ambiguous" }
        Add-Check 'auth-status' 'PASS' $auth.evidence_dir 'Isolated Codex home reports logged in'

        $null = Invoke-Consumer 'consumer-alpha-before-install' 'alpha' $v1 $false $null
        $null = Invoke-Consumer 'consumer-beta-before-install' 'beta' $v1 $false $null

        $addMarket = Invoke-HostCommand 'marketplace-add-v1' @('plugin', 'marketplace', 'add', $script:ActiveSource, '--json') $environment $consumerRoot
        Assert-ProbeCommand $addMarket 'Codex marketplace add failed'
        $marketList = Invoke-HostCommand 'marketplace-list-v1' @('plugin', 'marketplace', 'list', '--json') $environment $consumerRoot
        Assert-ProbeCommand $marketList 'Codex marketplace list failed'
        if (-not $marketList.stdout.Contains($script:MarketplaceName)) { Stop-Probe 'FAIL' "Codex marketplace source was not listed" }
        Add-Check 'marketplace-source-v1' 'PASS' $marketList.evidence_dir $script:MarketplaceName

        $available = Invoke-HostCommand 'plugin-available-v1' @('plugin', 'list', '--marketplace', $script:MarketplaceName, '--available', '--json') $environment $consumerRoot
        Assert-ProbeCommand $available 'Codex available-plugin list failed'
        if (-not $available.stdout.Contains($script:PluginName)) { Stop-Probe 'FAIL' "Codex did not discover the available plugin" }
        $install = Invoke-HostCommand 'plugin-install-v1' @('plugin', 'add', $selector, '--json') $environment $consumerRoot
        Assert-ProbeCommand $install 'Codex plugin install failed'
        $installed = Invoke-HostCommand 'plugin-list-v1' @('plugin', 'list', '--marketplace', $script:MarketplaceName, '--json') $environment $consumerRoot
        Assert-ProbeCommand $installed 'Codex plugin list failed'
        Assert-ListedState $installed.stdout $true 'Codex installed list'
        Add-Check 'install-v1' 'PASS' $installed.evidence_dir $selector
        $inventoryV1 = Write-InstalledPluginEvidence 'installed-v1' $v1
        Assert-OneInstalledPlugin $inventoryV1 'consumer-bytes-v1'
        $null = Invoke-Consumer 'consumer-alpha-v1' 'alpha' $v1 $true $null
        $null = Invoke-Consumer 'consumer-beta-v1' 'beta' $v1 $true $null

        Replace-ActiveMarketplace $sourceV2
        $null = Invoke-Consumer 'consumer-alpha-before-operation' 'alpha' $v1 $true $null
        $repeatAdd = Invoke-HostCommand 'plugin-repeat-add-v2' @('plugin', 'add', $selector, '--json') $environment $consumerRoot
        if ($repeatAdd.timed_out -or -not $script:ProcessTreeClear) { Stop-Probe 'AMBIGUOUS' 'Codex repeat-add observation did not terminate cleanly' }
        Add-Check 'repeat-add' $(if ($repeatAdd.exit_code -eq 0) { 'PASS' } else { 'UNAVAILABLE' }) $repeatAdd.evidence_dir 'Observed separately from native update support'
        Invoke-CodexRepeatAddObservation $v1 $v2

        $compatRemove = Invoke-HostCommand 'compat-remove-v1' @('plugin', 'remove', $selector, '--json') $environment $consumerRoot
        Assert-ProbeCommand $compatRemove 'Codex compatibility remove failed'
        $compatMarketRemove = Invoke-HostCommand 'compat-marketplace-remove-v1' @('plugin', 'marketplace', 'remove', $script:MarketplaceName, '--json') $environment $consumerRoot
        Assert-ProbeCommand $compatMarketRemove 'Codex compatibility marketplace remove failed'
        $compatMarketAdd = Invoke-HostCommand 'compat-marketplace-add-v2' @('plugin', 'marketplace', 'add', $script:ActiveSource, '--json') $environment $consumerRoot
        Assert-ProbeCommand $compatMarketAdd 'Codex compatibility marketplace add failed'
        $compatInstall = Invoke-HostCommand 'compat-install-v2' @('plugin', 'add', $selector, '--json') $environment $consumerRoot
        Assert-ProbeCommand $compatInstall 'Codex compatibility reinstall failed'
        $installedV2 = Invoke-HostCommand 'plugin-list-v2' @('plugin', 'list', '--marketplace', $script:MarketplaceName, '--json') $environment $consumerRoot
        Assert-ProbeCommand $installedV2 'Codex v2 plugin list failed'
        Assert-ListedState $installedV2.stdout $true 'Codex compatibility v2 list'
        $inventoryV2 = Write-InstalledPluginEvidence 'installed-v2' $v2
        Assert-OneInstalledPlugin $inventoryV2 'compatibility-reinstall-v2'
        $null = Invoke-Consumer 'consumer-alpha-v2' 'alpha' $v2 $true $v1
        $null = Invoke-Consumer 'consumer-beta-v2' 'beta' $v2 $true $v1

        $remove = Invoke-HostCommand 'plugin-remove-final' @('plugin', 'remove', $selector, '--json') $environment $consumerRoot
        Assert-ProbeCommand $remove 'Codex final plugin remove failed'
        $marketRemove = Invoke-HostCommand 'marketplace-remove-final' @('plugin', 'marketplace', 'remove', $script:MarketplaceName, '--json') $environment $consumerRoot
        Assert-ProbeCommand $marketRemove 'Codex final marketplace remove failed'
        $afterRemove = Invoke-HostCommand 'plugin-list-after-remove' @('plugin', 'list', '--json') $environment $consumerRoot
        Assert-ProbeCommand $afterRemove 'Codex plugin list after remove failed'
        Assert-ListedState $afterRemove.stdout $false 'Codex list after remove'
        $inventoryRemoved = Write-ConsumerInventory 'after-uninstall'
        Add-Check 'uninstall' 'PASS' $inventoryRemoved.path "inventory_sha256=$($inventoryRemoved.sha256); retained_cache_name_present=$($inventoryRemoved.contains_plugin)"
        $null = Invoke-Consumer 'consumer-after-uninstall' 'alpha' $v2 $false $null
    }
    else {
        $versionResult = Invoke-HostCommand 'host-version' @('--version') $environment $consumerRoot
        $script:HostVersion = ($versionResult.stdout + ' ' + $versionResult.stderr).Trim()
        Add-Check 'host-version' $(if ($versionResult.exit_code -eq 0) { 'PASS' } else { 'FAIL' }) $versionResult.evidence_dir $script:HostVersion
        Assert-ProbeCommand $versionResult 'Claude version command failed'

        $validate = Invoke-HostCommand 'plugin-validate-v1' @('plugin', 'validate', $script:ActiveSource, '--strict') $environment $consumerRoot
        Assert-ProbeCommand $validate 'Claude strict plugin validation failed'
        Add-Check 'plugin-validate-v1' 'PASS' $validate.evidence_dir 'Candidate-derived v1 marketplace passed strict validation'

        $auth = Invoke-HostCommand 'auth-status' @('auth', 'status', '--json') $environment $consumerRoot
        if ($auth.exit_code -ne 0 -or -not $auth.stdout.Contains('"loggedIn": true')) { Stop-Probe 'AMBIGUOUS' "Claude isolated auth status is ambiguous" }
        Add-Check 'auth-status' 'PASS' $auth.evidence_dir 'Isolated Claude home reports logged in'

        $null = Invoke-Consumer 'consumer-alpha-before-install' 'alpha' $v1 $false $null
        $null = Invoke-Consumer 'consumer-beta-before-install' 'beta' $v1 $false $null

        $addMarket = Invoke-HostCommand 'marketplace-add-v1' @('plugin', 'marketplace', 'add', $script:ActiveSource, '--scope', 'user') $environment $consumerRoot
        Assert-ProbeCommand $addMarket 'Claude marketplace add failed'
        $marketList = Invoke-HostCommand 'marketplace-list-v1' @('plugin', 'marketplace', 'list', '--json') $environment $consumerRoot
        Assert-ProbeCommand $marketList 'Claude marketplace list failed'
        if (-not $marketList.stdout.Contains($script:MarketplaceName)) { Stop-Probe 'FAIL' "Claude marketplace source was not listed" }
        Add-Check 'marketplace-source-v1' 'PASS' $marketList.evidence_dir $script:MarketplaceName

        $install = Invoke-HostCommand 'plugin-install-v1' @('plugin', 'install', $selector, '--scope', 'user') $environment $consumerRoot
        Assert-ProbeCommand $install 'Claude plugin install failed'
        $installed = Invoke-HostCommand 'plugin-list-v1' @('plugin', 'list', '--json') $environment $consumerRoot
        Assert-ProbeCommand $installed 'Claude plugin list failed'
        Assert-ListedState $installed.stdout $true 'Claude installed list'
        Add-Check 'install-v1' 'PASS' $installed.evidence_dir $selector
        $inventoryV1 = Write-InstalledPluginEvidence 'installed-v1' $v1
        Assert-OneInstalledPlugin $inventoryV1 'consumer-bytes-v1'
        $null = Invoke-Consumer 'consumer-alpha-v1' 'alpha' $v1 $true $null
        $null = Invoke-Consumer 'consumer-beta-v1' 'beta' $v1 $true $null

        Replace-ActiveMarketplace $sourceV2
        $null = Invoke-Consumer 'consumer-alpha-before-update' 'alpha' $v1 $true $null
        $marketUpdate = Invoke-HostCommand 'marketplace-update-v2' @('plugin', 'marketplace', 'update', $script:MarketplaceName) $environment $consumerRoot
        Assert-ProbeCommand $marketUpdate 'Claude marketplace update failed'
        $update = Invoke-HostCommand 'plugin-update-v2' @('plugin', 'update', $selector, '--scope', 'user') $environment $consumerRoot
        Assert-ProbeCommand $update 'Claude plugin update failed'
        Add-Check 'native-update-v2' 'PASS' $update.evidence_dir $selector
        $installedV2 = Invoke-HostCommand 'plugin-list-v2' @('plugin', 'list', '--json') $environment $consumerRoot
        Assert-ProbeCommand $installedV2 'Claude v2 plugin list failed'
        Assert-ListedState $installedV2.stdout $true 'Claude v2 list'
        $inventoryV2 = Write-InstalledPluginEvidence 'installed-v2' $v2
        Assert-OneInstalledPlugin $inventoryV2 'consumer-bytes-v2'
        $null = Invoke-Consumer 'consumer-alpha-v2' 'alpha' $v2 $true $v1
        $null = Invoke-Consumer 'consumer-beta-v2' 'beta' $v2 $true $v1

        $disable = Invoke-HostCommand 'plugin-disable' @('plugin', 'disable', $selector, '--scope', 'user') $environment $consumerRoot
        Assert-ProbeCommand $disable 'Claude plugin disable failed'
        $disabledList = Invoke-HostCommand 'plugin-list-disabled' @('plugin', 'list', '--json') $environment $consumerRoot
        Assert-ProbeCommand $disabledList 'Claude disabled-state list failed'
        Assert-ClaudeEnabledState $disabledList.stdout $false 'Claude disabled-state list'
        $null = Invoke-Consumer 'consumer-while-disabled' 'alpha' $v2 $false $null
        $enable = Invoke-HostCommand 'plugin-enable' @('plugin', 'enable', $selector, '--scope', 'user') $environment $consumerRoot
        Assert-ProbeCommand $enable 'Claude plugin enable failed'
        $enabledList = Invoke-HostCommand 'plugin-list-enabled' @('plugin', 'list', '--json') $environment $consumerRoot
        Assert-ProbeCommand $enabledList 'Claude enabled-state list failed'
        Assert-ClaudeEnabledState $enabledList.stdout $true 'Claude enabled-state list'
        $null = Invoke-Consumer 'consumer-after-enable' 'alpha' $v2 $true $v1
        Add-Check 'disable-enable' 'PASS' $enable.evidence_dir $selector

        $remove = Invoke-HostCommand 'plugin-uninstall' @('plugin', 'uninstall', $selector, '--scope', 'user', '-y') $environment $consumerRoot
        Assert-ProbeCommand $remove 'Claude plugin uninstall failed'
        $marketRemove = Invoke-HostCommand 'marketplace-remove' @('plugin', 'marketplace', 'remove', $script:MarketplaceName, '--scope', 'user') $environment $consumerRoot
        Assert-ProbeCommand $marketRemove 'Claude marketplace remove failed'
        $afterRemove = Invoke-HostCommand 'plugin-list-after-remove' @('plugin', 'list', '--json') $environment $consumerRoot
        Assert-ProbeCommand $afterRemove 'Claude plugin list after uninstall failed'
        Assert-ListedState $afterRemove.stdout $false 'Claude list after uninstall'
        $inventoryRemoved = Write-ConsumerInventory 'after-uninstall'
        Add-Check 'uninstall' 'PASS' $inventoryRemoved.path "inventory_sha256=$($inventoryRemoved.sha256); retained_cache_name_present=$($inventoryRemoved.contains_plugin)"
        $null = Invoke-Consumer 'consumer-after-uninstall' 'alpha' $v2 $false $null
    }

    $activeSourceHash = Get-TreeHash $script:ActiveSource
    if ($activeSourceHash -ne $v2.tree_sha256) {
        Stop-Probe 'AMBIGUOUS' "Active source bytes changed or do not match the retained v2 source"
    }
    Add-Check 'active-source-identity' 'PASS' 'source/current' "tree_sha256=$activeSourceHash"
    if ($script:ResolvedStatus -eq 'unavailable') {
        Add-Check 'resolved-model-identity' 'UNAVAILABLE' 'commands/' 'The provider output did not report the resolved model identity'
    }
    else {
        Add-Check 'resolved-model-identity' 'PASS' 'commands/' "resolved_model=$($script:ResolvedModel); status=$($script:ResolvedStatus)"
    }
    $script:ReportResult = Get-ReducedResult
}
catch {
    $runFailure = $_.Exception.Message
    $script:FailureReason = $runFailure
    $failureStatus = if ($_.Exception.Data.Contains('probe_status')) { [string]$_.Exception.Data['probe_status'] } else { 'AMBIGUOUS' }
    $script:ReportResult = $failureStatus
    Add-Check 'run-completion' $failureStatus 'report.md' $runFailure
}
finally {
    if (Test-Path -LiteralPath $DisposableHome) {
        try {
            $beforeCleanup = Write-ConsumerInventory 'before-cleanup'
            Add-Check 'consumer-bytes-before-cleanup' 'PASS' $beforeCleanup.path "inventory_sha256=$($beforeCleanup.sha256)"
            $cleanupTarget = Assert-CleanupTarget
            Remove-Item -Force -Recurse -LiteralPath $cleanupTarget
            if (Test-Path -LiteralPath $cleanupTarget) {
                throw "DisposableHome still exists after cleanup"
            }
            $null = $script:CleanupNotes.Add("DisposableHome removed")
            Add-Check 'cleanup' 'PASS' 'inventories/before-cleanup.tsv' 'Owned disposable home removed; evidence retained'
        }
        catch {
            $null = $script:CleanupNotes.Add("DisposableHome cleanup failed: $($_.Exception.Message)")
            $script:ReportResult = 'AMBIGUOUS'
            if (-not $script:FailureReason) { $script:FailureReason = $_.Exception.Message }
            Add-Check 'cleanup' 'AMBIGUOUS' 'inventories/before-cleanup.tsv' $_.Exception.Message
        }
    }
}

$liveAfter = Get-LiveHomeSnapshot $script:LiveClaudeHomeApproved $script:LiveCodexHomeApproved
$liveAfterHash = $liveAfter.public_sha256
Write-NewUtf8NoBom (Join-Path $EvidenceDir 'live-surface-after.tsv') $liveAfter.public_text
Write-NewUtf8NoBom (Join-Path $EvidenceDir 'live-surface-after.sha256') ($liveAfterHash + "`n")
$liveComparison = Compare-LiveHomeSnapshots $liveBefore $liveAfter $allowedLiveAppends $opaqueLiveVolatility
if (-not $liveComparison.pass) {
    $changedPaths = @($liveComparison.changes) -join ', '
    Add-Check 'live-home-full-roots' 'AMBIGUOUS' 'live-surface-before.tsv; live-surface-after.tsv' "A protected live path changed: $changedPaths"
    $script:ReportResult = 'AMBIGUOUS'
    if (-not $script:FailureReason) { $script:FailureReason = "A protected live path changed: $changedPaths" }
}
else {
    Add-Check 'live-home-full-roots' 'PASS' 'live-surface-before.tsv; live-surface-after.tsv; live-append-allowlist.txt; live-volatile-allowlist.txt' 'All protected paths match within the exact preflight-recorded volatility limits'
}

Assert-NoNestedReparsePoint $EvidenceDir 'EvidenceDir'
$script:ReportResult = Get-ReducedResult

if (-not $v1) {
    $v1 = [pscustomobject]@{ tree_sha256 = 'unavailable' }
}
if (-not $v2) {
    $v2 = [pscustomobject]@{ tree_sha256 = 'unavailable' }
}
Write-ReportAndManifest $script:ReportResult $script:FailureReason $v1 $v2 $liveBeforeHash $liveAfterHash

Write-Output "RESULT=$($script:ReportResult)"
Write-Output "EVIDENCE=$EvidenceDir"
if ($script:ReportResult -eq 'PASS' -or $script:ReportResult -eq 'PARTIAL') {
    $script:LifecycleExitCode = $(if ($script:ReportResult -eq 'PASS') { 0 } else { 1 })
    return
}
if ($script:ReportResult -eq 'FAIL') {
    $script:LifecycleExitCode = 1
    return
}
$script:LifecycleExitCode = 3
return
}
catch {
    $outerFailure = $_.Exception.Message
    try {
        if (Test-Path -LiteralPath $DisposableHome -PathType Container) {
            $cleanupTarget = Assert-CleanupTarget
            Remove-Item -Force -Recurse -LiteralPath $cleanupTarget
        }
    }
    catch {
        $outerFailure = "$outerFailure; cleanup also failed: $($_.Exception.Message)"
    }
    if (Test-Path -LiteralPath $EvidenceDir -PathType Container) {
        try {
            if (-not (Test-Path -LiteralPath (Join-Path $EvidenceDir 'fallback-report.txt'))) {
                Write-NewUtf8NoBom (Join-Path $EvidenceDir 'fallback-report.txt') ("RESULT=AMBIGUOUS`nFAILURE=$outerFailure`n")
            }
            if (-not (Test-Path -LiteralPath (Join-Path $EvidenceDir 'manifest.sha256'))) {
                $rows = New-Object System.Collections.ArrayList
                Get-ChildItem -Force -LiteralPath $EvidenceDir -Recurse -File |
                    Where-Object { $_.Name -ne 'manifest.sha256' } |
                    Sort-Object FullName |
                    ForEach-Object {
                        $relative = $_.FullName.Substring((Get-AbsolutePath $EvidenceDir).Length + 1).Replace('\', '/')
                        $hash = Get-Sha256File $_.FullName
                        $null = $rows.Add("$hash  $relative")
                    }
                Write-NewUtf8NoBom (Join-Path $EvidenceDir 'manifest.sha256') ((@($rows) -join "`n") + "`n")
            }
        }
        catch { }
    }
    [Console]::Error.WriteLine($outerFailure)
    $script:LifecycleExitCode = 3
    return
}
}

if ($MyInvocation.InvocationName -ne '.') {
    try {
        Invoke-LifecycleProbe
        exit $script:LifecycleExitCode
    }
    catch {
        [Console]::Error.WriteLine($_.Exception.Message)
        exit 2
    }
}
