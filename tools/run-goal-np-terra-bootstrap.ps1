[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Preflight', 'Run', 'Inspect')]
    [string]$Action,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$ApprovedCommit,

    [Parameter(Mandatory = $true)]
    [string]$ApprovalMessageFile
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$ExpectedApproval = 'Approve Goal NP plan Publication 4 with D01-D10 and the Terra bootstrap recovery amendment.'
$ExpectedBranch = 'plan/native-codex-skill-parity'
$ExpectedCodexVersion = 'codex-cli 0.147.0'
$ExpectedCodexHash = '935a1911ed2556e4ffcec995f4886ac2ac425863ba26fed264df62e30272ad9d'
$ExpectedCodexPackageHash = 'bbaf3b9597b54bc1d4cf4aea93870e9035629d79bdaba58234011c31f0cfcf3d'
$ExpectedPythonVersion = 'Python 3.14.3'
$ExpectedPythonHash = 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
$ExpectedLockHash = 'c197caa7da4306f0b744c9d352ce4c1a858d57514453c1ec1d249c83564cd555'
$PriorP3RequestId = 'tba-b7e5898e6389ff19b3ce34738f16b47d0a832dfc4625789fbcf4308352f2b1a0'
$PriorP3ApprovedCommit = '71a5aea3fd21320d2fbb3cb9228bc52e42cb3215'
$PriorP3ApprovalMessageHash = '66df8cd413fddd097e80dc63ccfacab221e96c72c795345d14b72ae1ae3474ef'
$PriorP3StateHash = 'ae59a6ac7f512d2e399675fe541b916d1710c209a13b45433642cf019a07df97'
$PriorP3RootManifestHash = '9b01de1f550019a8bf81c23431925b6f38a173ec1ce22023c765a2a8d290cdcf'
$PriorP3RootEntryCount = 3
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Get-Sha256Text([string]$Text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Get-FileSha256([string]$Path) {
    $stream = $null
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $stream = [System.IO.File]::Open(
            $Path,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::Read
        )
        return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        if ($stream) { $stream.Dispose() }
        $sha.Dispose()
    }
}

function Write-Utf8NoBom([string]$Path, [string]$Text) {
    [System.IO.File]::WriteAllText($Path, $Text, $Utf8NoBom)
}

function Write-State([string]$Phase, [hashtable]$Extra) {
    $payload = [ordered]@{
        schema_version = 1
        request_id = $script:RequestId
        phase = $Phase
        approved_commit = $ApprovedCommit
        approval_message_sha256 = $script:ApprovalMessageHash
        updated_utc = [DateTime]::UtcNow.ToString('o')
    }
    foreach ($key in $Extra.Keys) { $payload[$key] = $Extra[$key] }
    $temp = $script:StatePath + '.tmp'
    Write-Utf8NoBom $temp (($payload | ConvertTo-Json -Depth 8) + "`n")
    Move-Item -LiteralPath $temp -Destination $script:StatePath -Force
}

function Get-WorktreeTree([string]$Label) {
    $snapshotIndex = Join-Path $script:EvidenceRoot ('identity-' + $Label + '.index')
    if (Test-Path -LiteralPath $snapshotIndex) { throw "Identity snapshot already exists: $Label" }
    $originalIndex = $env:GIT_INDEX_FILE
    try {
        $env:GIT_INDEX_FILE = $snapshotIndex
        & git read-tree HEAD
        if ($LASTEXITCODE -ne 0) { throw "Failed to initialize identity snapshot: $Label" }
        & git add -A -- .
        if ($LASTEXITCODE -ne 0) { throw "Failed to populate identity snapshot: $Label" }
        $tree = (& git write-tree).Trim()
        if ($LASTEXITCODE -ne 0) { throw "Failed to write identity snapshot: $Label" }
        return $tree
    }
    finally {
        if ($null -eq $originalIndex) { Remove-Item Env:GIT_INDEX_FILE -ErrorAction SilentlyContinue }
        else { $env:GIT_INDEX_FILE = $originalIndex }
    }
}

function Get-RepoIdentity([string]$SnapshotLabel) {
    $statusLines = @(& git status --porcelain=v1 --untracked-files=all)
    $statusText = ($statusLines -join "`n")
    $identity = [ordered]@{
        root = $script:RepoRoot
        git_common_dir = (& git rev-parse --git-common-dir).Trim()
        ref = (& git branch --show-current).Trim()
        head = (& git rev-parse HEAD).Trim()
        tree = (& git rev-parse 'HEAD^{tree}').Trim()
        index_tree = (& git write-tree).Trim()
        status_sha256 = Get-Sha256Text $statusText
        status_count = $statusLines.Count
    }
    if ($SnapshotLabel) { $identity['worktree_tree'] = Get-WorktreeTree $SnapshotLabel }
    return $identity
}

function Assert-NoAlternateDataStream([string]$Path) {
    $streams = @(Get-Item -LiteralPath $Path -Stream * -Force -ErrorAction Stop)
    $alternate = @($streams | Where-Object { $_.Stream -cne ':$DATA' })
    if ($alternate.Count -ne 0) { throw "Alternate data stream is forbidden: $Path" }
}

function Get-OrdinalTreeManifest([string]$TreeRoot) {
    if (-not (Test-Path -LiteralPath $TreeRoot -PathType Container)) {
        return [ordered]@{ exists = $false; entry_count = 0; sha256 = Get-Sha256Text '' }
    }
    $rootItem = Get-Item -LiteralPath $TreeRoot -Force -ErrorAction Stop
    if (($rootItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Tree root must not be a reparse point: $TreeRoot"
    }
    Assert-NoAlternateDataStream $rootItem.FullName
    $root = $rootItem.FullName.TrimEnd('\')
    $rows = New-Object System.Collections.Generic.List[string]
    $rows.Add('D' + "`t" + '.')
    $pending = New-Object 'System.Collections.Generic.Queue[string]'
    $pending.Enqueue($root)
    while ($pending.Count -ne 0) {
        $directory = $pending.Dequeue()
        foreach ($item in @(Get-ChildItem -LiteralPath $directory -Force -ErrorAction Stop)) {
            $relative = $item.FullName.Substring($root.Length).TrimStart('\').Replace('\', '/')
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Reparse point is forbidden in protected tree: $relative"
            }
            Assert-NoAlternateDataStream $item.FullName
            if ($item.PSIsContainer) {
                $rows.Add(('D' + "`t" + $relative))
                $pending.Enqueue($item.FullName)
            }
            else {
                $length = (Get-Item -LiteralPath $item.FullName -Force -ErrorAction Stop).Length
                $rows.Add(('F' + "`t" + $relative + "`t" + $length + "`t" + (Get-FileSha256 $item.FullName)))
            }
        }
    }
    $sorted = $rows.ToArray()
    [Array]::Sort($sorted, [StringComparer]::Ordinal)
    return [ordered]@{ exists = $true; entry_count = $sorted.Count; sha256 = Get-Sha256Text ($sorted -join "`n") }
}

function Get-CodexHomeManifest([string]$CodexHome) {
    return Get-OrdinalTreeManifest $CodexHome
}

function Get-NormalizedProcessName([string]$Name) {
    if (-not $Name) { throw 'Process census returned an empty process name.' }
    return [System.IO.Path]::GetFileNameWithoutExtension($Name).ToLowerInvariant()
}

function Get-QuiescenceProof {
    if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1 -or
        $PSVersionTable.PSEdition -cne 'Desktop') {
        throw 'Publication 4 requires Windows PowerShell 5.1 Desktop.'
    }
    $processes = @(Get-CimInstance -ClassName Win32_Process -Property ProcessId, ParentProcessId, Name, CreationDate -ErrorAction Stop)
    if ($processes.Count -eq 0) { throw 'The process census is empty.' }
    $byId = @{}
    foreach ($process in $processes) {
        $processId = [int]$process.ProcessId
        if ($byId.ContainsKey($processId)) { throw 'The process census contains a duplicate process ID.' }
        $byId[$processId] = $process
    }

    $forbiddenNames = @('code', 'codex', 'claude', 'chatgpt', 'cursor')
    $globalForbidden = @($processes | Where-Object {
        $forbiddenNames -ccontains (Get-NormalizedProcessName $_.Name)
    })

    $ancestry = New-Object System.Collections.Generic.List[string]
    $seen = @{}
    $currentId = [int]$PID
    while ($true) {
        if ($seen.ContainsKey($currentId)) { throw 'The process ancestry contains a cycle.' }
        $seen[$currentId] = $true
        if (-not $byId.ContainsKey($currentId)) { throw 'The complete process ancestry cannot be proven.' }
        $current = $byId[$currentId]
        $currentName = Get-NormalizedProcessName $current.Name
        $ancestry.Add($currentName)
        if ($currentName -ceq 'explorer') { break }
        $parentId = [int]$current.ParentProcessId
        if ($parentId -eq 0) { break }
        if (-not $byId.ContainsKey($parentId)) { throw 'The complete process ancestry cannot be proven.' }
        $parent = $byId[$parentId]
        if (-not $current.CreationDate -or -not $parent.CreationDate) {
            throw 'The process ancestry creation times cannot be proven.'
        }
        if ([DateTime]$parent.CreationDate -gt [DateTime]$current.CreationDate) {
            throw 'The process ancestry is inconsistent with process creation order.'
        }
        $currentId = $parentId
    }
    if ($ancestry.Count -eq 0 -or $ancestry[0] -cne 'powershell') {
        throw 'Publication 4 must run in standalone powershell.exe, not an embedded or substituted shell.'
    }
    $ancestryRoot = $ancestry[$ancestry.Count - 1]
    if ($ancestryRoot -notin @('explorer', 'windowsterminal')) {
        throw "The process ancestry did not terminate at an allowed standalone-shell root: $ancestryRoot"
    }
    $forbiddenAncestors = @($ancestry.ToArray() | Where-Object { $forbiddenNames -ccontains $_ })
    if ($forbiddenAncestors.Count -ne 0) {
        throw ('Publication 4 must run from independent ordinary PowerShell; forbidden ancestry: ' +
            (($forbiddenAncestors | Sort-Object -Unique) -join ', '))
    }
    if ($globalForbidden.Count -ne 0) {
        $names = @($globalForbidden | ForEach-Object { Get-NormalizedProcessName $_.Name } | Sort-Object -Unique)
        throw ('Publication 4 requires all Code, Codex, Claude, ChatGPT, and Cursor processes to be closed: ' +
            ($names -join ', '))
    }
    return [ordered]@{
        powershell = 'Windows PowerShell 5.1 Desktop'
        ancestry_names = $ancestry.ToArray()
        ancestry_root = $ancestryRoot
        forbidden_ancestor_count = 0
        forbidden_process_count = 0
    }
}

function Test-ManifestEqual([System.Collections.IDictionary]$Left, [System.Collections.IDictionary]$Right) {
    return ($Left.exists -eq $Right.exists -and
        $Left.entry_count -eq $Right.entry_count -and
        $Left.sha256 -ceq $Right.sha256)
}

function Get-PriorP3EvidenceProof {
    $priorRoot = Join-Path $env:LOCALAPPDATA ('SkillMesh\Evidence\GoalNP\TerraBootstrap\' + $PriorP3RequestId)
    $priorStatePath = Join-Path $priorRoot 'state.json'
    if (-not (Test-Path -LiteralPath $priorStatePath -PathType Leaf)) {
        throw 'The frozen Publication-3 blocked state is absent.'
    }
    $stateHash = Get-FileSha256 $priorStatePath
    if ($stateHash -cne $PriorP3StateHash) { throw 'The frozen Publication-3 blocked state hash changed.' }
    $state = Get-Content -LiteralPath $priorStatePath -Raw | ConvertFrom-Json
    if ($state.schema_version -ne 1 -or $state.request_id -cne $PriorP3RequestId -or
        $state.phase -cne 'blocked' -or $state.approved_commit -cne $PriorP3ApprovedCommit -or
        $state.approval_message_sha256 -cne $PriorP3ApprovalMessageHash) {
        throw 'The frozen Publication-3 blocked state identity changed.'
    }
    $rootManifest = Get-OrdinalTreeManifest $priorRoot
    if (-not $rootManifest.exists -or $rootManifest.entry_count -ne $PriorP3RootEntryCount -or
        $rootManifest.sha256 -cne $PriorP3RootManifestHash) {
        throw 'The frozen Publication-3 blocked evidence root changed.'
    }
    return [ordered]@{
        request_id = $PriorP3RequestId
        approved_commit = $PriorP3ApprovedCommit
        approval_message_sha256 = $PriorP3ApprovalMessageHash
        state_sha256 = $stateHash
        root_manifest = $rootManifest
    }
}

function Assert-PriorP3EvidenceUnchanged([System.Collections.IDictionary]$Expected) {
    $actual = Get-PriorP3EvidenceProof
    if ($actual.state_sha256 -cne $Expected.state_sha256 -or
        -not (Test-ManifestEqual $actual.root_manifest $Expected.root_manifest)) {
        throw 'Publication-3 blocked evidence changed during Publication-4 execution.'
    }
    return $actual
}

function Get-ClosedConfigArguments {
    $arguments = New-Object System.Collections.Generic.List[string]
    foreach ($value in @(
        'model_reasoning_effort=xhigh',
        'approval_policy=never',
        'project_doc_max_bytes=0',
        'project_doc_fallback_filenames=[]',
        'agents.enabled=false',
        'web_search=disabled'
    )) {
        $arguments.Add('--config')
        $arguments.Add($value)
    }
    foreach ($feature in @(
        'apps', 'plugins', 'hooks', 'skill_search', 'skill_mcp_dependency_install',
        'plugin_sharing', 'remote_plugin', 'recommended_plugins', 'browser_use',
        'browser_use_external', 'browser_use_full_cdp_access', 'computer_use',
        'image_generation', 'tool_suggest', 'memories'
    )) {
        $arguments.Add('--disable')
        $arguments.Add($feature)
    }
    return $arguments.ToArray()
}

function Invoke-RecordedProcess(
    [string]$Label,
    [string]$FilePath,
    [string[]]$Arguments,
    [string]$OutputRoot,
    [int]$TimeoutMilliseconds = 3600000
) {
    if (-not $OutputRoot) { $OutputRoot = $script:EvidenceRoot }
    $stdout = Join-Path $OutputRoot ($Label + '.stdout.txt')
    $stderr = Join-Path $OutputRoot ($Label + '.stderr.txt')
    $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -NoNewWindow -PassThru `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if (-not $process.WaitForExit($TimeoutMilliseconds)) {
        $process.Kill()
        $process.WaitForExit()
        throw "$Label exceeded its $TimeoutMilliseconds-millisecond limit."
    }
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw "$Label exited $($process.ExitCode)." }
    return [ordered]@{
        exit_code = $process.ExitCode
        stdout_path = $stdout
        stdout_sha256 = Get-FileSha256 $stdout
        stderr_path = $stderr
        stderr_sha256 = Get-FileSha256 $stderr
    }
}

function Get-ChangedPaths {
    $paths = @(& git diff --name-only --diff-filter=ACMRTUXB) + @(& git ls-files --others --exclude-standard)
    return @($paths | Where-Object { $_ } | Sort-Object -Unique)
}

function Assert-AdminScope {
    $changed = @(Get-ChangedPaths)
    $unexpected = @($changed | Where-Object { $AllowedAdminPaths -cnotcontains $_ })
    if ($unexpected.Count -ne 0) { throw ('Unexpected ADMIN path(s): ' + ($unexpected -join ', ')) }
    $missing = @($AllowedAdminPaths | Where-Object { -not (Test-Path -LiteralPath (Join-Path $script:RepoRoot $_) -PathType Leaf) })
    if ($missing.Count -ne 0) { throw ('Missing ADMIN path(s): ' + ($missing -join ', ')) }
    $notChanged = @($AllowedAdminPaths | Where-Object { $changed -cnotcontains $_ })
    if ($notChanged.Count -ne 0) { throw ('ADMIN output was not created: ' + ($notChanged -join ', ')) }
    return $changed
}

function Remove-DisposableCodexHome {
    if (-not $script:DisposableCodexHome -or -not (Test-Path -LiteralPath $script:DisposableCodexHome)) { return }
    $resolvedEvidence = [System.IO.Path]::GetFullPath($script:EvidenceRoot).TrimEnd('\')
    $resolvedTarget = [System.IO.Path]::GetFullPath($script:DisposableCodexHome).TrimEnd('\')
    $expectedTarget = Join-Path $resolvedEvidence 'disposable-codex-home'
    if ($resolvedTarget -cne $expectedTarget -or -not $resolvedTarget.StartsWith($resolvedEvidence + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Refusing to remove a disposable Codex home outside the exact evidence root.'
    }
    Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
    $script:DisposableCodexHome = $null
}

function Get-PromptInputProof([string]$Label, [string]$CallLaunchRoot) {
    $quiescenceBefore = Get-QuiescenceProof
    $arguments = @('--model', 'gpt-5.6-terra') + @(Get-ClosedConfigArguments) + @(
        '--sandbox', 'read-only', '--cd', $CallLaunchRoot, '--add-dir', $script:RepoRoot,
        'debug', 'prompt-input', 'Goal-NP-Publication-4-Terra-bootstrap-prompt-surface-proof'
    )
    $proof = $null
    try {
        $proof = Invoke-RecordedProcess ($Label + '-prompt-input') $script:CodexExe $arguments $script:EvidenceRoot 120000
    }
    finally {
        $quiescenceAfter = Get-QuiescenceProof
    }
    $text = Get-Content -LiteralPath $proof.stdout_path -Raw
    $null = $text | ConvertFrom-Json
    foreach ($forbidden in @(
        'AGENTS.md instructions for', 'GitHub Copilot workspace adapter', '.agents/skills/',
        '.agents\skills\', '.github/skills/', '.github\skills\', '<apps_instructions>',
        '<plugins_instructions>', '<recommended_plugins>'
    )) {
        if ($text.IndexOf($forbidden, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
            throw "Prompt-input proof contains forbidden ambient input: $forbidden"
        }
    }
    $systemSkillMatches = [regex]::Matches($text, '\(file:\s*([^\)]+)\)')
    foreach ($match in $systemSkillMatches) {
        $locator = $match.Groups[1].Value.Replace('\', '/')
        if ($locator.IndexOf('/skills/.system/', [StringComparison]::OrdinalIgnoreCase) -lt 0) {
            throw "Prompt-input proof contains a non-system skill locator: $locator"
        }
    }
    return [ordered]@{
        process = $proof
        system_skill_descriptor_count = $systemSkillMatches.Count
        launch_root = $CallLaunchRoot
        quiescence_before = $quiescenceBefore
        quiescence_after = $quiescenceAfter
    }
}

function Invoke-Terra(
    [string]$Label,
    [string]$Sandbox,
    [string]$PromptPath,
    [System.Collections.IDictionary]$ExpectedRepoIdentity
) {
    $callLaunchRoot = Join-Path $script:LaunchRoot $Label
    if (-not (Test-Path -LiteralPath $callLaunchRoot -PathType Container)) {
        New-Item -ItemType Directory -Path $callLaunchRoot | Out-Null
    }
    $promptInputProof = Get-PromptInputProof $Label $callLaunchRoot
    $jsonl = Join-Path $script:EvidenceRoot ($Label + '.jsonl')
    $stderr = Join-Path $script:EvidenceRoot ($Label + '.stderr.txt')
    $last = Join-Path $script:EvidenceRoot ($Label + '.result.json')
    $arguments = @('exec', '--model', 'gpt-5.6-terra') + @(Get-ClosedConfigArguments) + @(
        '--sandbox', $Sandbox, '--cd', $callLaunchRoot, '--add-dir', $script:RepoRoot,
        '--skip-git-repo-check', '--ephemeral', '--ignore-user-config', '--ignore-rules',
        '--strict-config', '--output-schema', $script:ResultSchema, '--json',
        '--output-last-message', $last, '-'
    )
    $invocationPath = Join-Path $script:EvidenceRoot ($Label + '.invocation.json')
    $invocation = [ordered]@{
        requested_model = 'gpt-5.6-terra'
        requested_reasoning_effort = 'xhigh'
        sandbox = $Sandbox
        arguments = $arguments
        environment = [ordered]@{
            CODEX_HOME = $env:CODEX_HOME
            TEMP = $env:TEMP
            TMP = $env:TMP
            PIP_CACHE_DIR = $env:PIP_CACHE_DIR
            PYTHONNOUSERSITE = $env:PYTHONNOUSERSITE
            PYTHONDONTWRITEBYTECODE = $env:PYTHONDONTWRITEBYTECODE
        }
        prompt_input_proof_sha256 = $promptInputProof.process.stdout_sha256
        prompt_input_quiescence_before = $promptInputProof.quiescence_before
        prompt_input_quiescence_after = $promptInputProof.quiescence_after
    }
    Write-Utf8NoBom $invocationPath (($invocation | ConvertTo-Json -Depth 8) + "`n")
    $preRepoIdentity = Get-RepoIdentity ($Label + '-pre')
    $preIdentity = [ordered]@{
        codex_executable = $script:CodexExe
        codex_version = (& $script:CodexExe --version).Trim()
        codex_executable_sha256 = Get-FileSha256 $script:CodexExe
        argv_sha256 = Get-Sha256Text (($arguments | ConvertTo-Json -Compress) + "`n")
        prompt_sha256 = Get-FileSha256 $PromptPath
        repo = $preRepoIdentity
    }
    if ($preIdentity.codex_executable -cne $script:CodexExe -or
        $preIdentity.codex_version -cne $ExpectedCodexVersion -or
        $preIdentity.codex_executable_sha256 -cne $ExpectedCodexHash) {
        throw "$Label pre-call Codex identity mismatch."
    }
    foreach ($field in @('root', 'git_common_dir', 'ref', 'head', 'tree', 'index_tree', 'status_sha256', 'status_count', 'worktree_tree')) {
        if ($preRepoIdentity[$field] -cne $ExpectedRepoIdentity[$field]) {
            throw "$Label pre-call Git identity mismatch: $field"
        }
    }
    Write-Utf8NoBom (Join-Path $script:EvidenceRoot ($Label + '.pre-identity.json')) (($preIdentity | ConvertTo-Json -Depth 6) + "`n")
    $preCallQuiescence = Get-QuiescenceProof
    $process = Start-Process -FilePath $script:CodexExe -ArgumentList $arguments -NoNewWindow -PassThru `
        -RedirectStandardInput $PromptPath -RedirectStandardOutput $jsonl -RedirectStandardError $stderr
    $failureMessage = $null
    $exitCode = $null
    try {
        if (-not $process.WaitForExit(3600000)) {
            $process.Kill()
            $process.WaitForExit()
            $failureMessage = "$Label Codex process exceeded the 3600-second limit."
        }
        else { $process.WaitForExit() }
        $exitCode = $process.ExitCode
        if (-not $failureMessage -and $exitCode -ne 0) { $failureMessage = "$Label Codex process exited $exitCode." }
    }
    catch {
        $failureMessage = "$Label Codex process handling failed: $($_.Exception.Message)"
        if (-not $process.HasExited) {
            $process.Kill()
            $process.WaitForExit()
        }
        if ($process.HasExited) { $exitCode = $process.ExitCode }
    }
    finally {
        $postRepoIdentity = Get-RepoIdentity ($Label + '-post')
        $postIdentity = [ordered]@{
            codex_executable = $script:CodexExe
            codex_version = (& $script:CodexExe --version).Trim()
            codex_executable_sha256 = Get-FileSha256 $script:CodexExe
            argv_sha256 = Get-Sha256Text (($arguments | ConvertTo-Json -Compress) + "`n")
            prompt_sha256 = Get-FileSha256 $PromptPath
            repo = $postRepoIdentity
        }
        Write-Utf8NoBom (Join-Path $script:EvidenceRoot ($Label + '.post-identity.json')) (($postIdentity | ConvertTo-Json -Depth 6) + "`n")
    }
    $postCallQuiescence = Get-QuiescenceProof
    foreach ($field in @('codex_executable', 'codex_version', 'codex_executable_sha256', 'argv_sha256', 'prompt_sha256')) {
        if ($preIdentity[$field] -cne $postIdentity[$field]) { throw "$Label changed protected process identity field $field." }
    }
    foreach ($field in @('root', 'git_common_dir', 'ref', 'head', 'tree', 'index_tree')) {
        if ($preRepoIdentity[$field] -cne $postRepoIdentity[$field]) { throw "$Label changed protected Git identity field $field." }
    }
    if ($Sandbox -eq 'read-only' -and (
        $preRepoIdentity.status_sha256 -cne $postRepoIdentity.status_sha256 -or
        $preRepoIdentity.status_count -ne $postRepoIdentity.status_count -or
        $preRepoIdentity.worktree_tree -cne $postRepoIdentity.worktree_tree
    )) { throw "$Label changed the worktree despite read-only review authority." }
    if ($failureMessage) { throw $failureMessage }
    if (-not (Test-Path -LiteralPath $last -PathType Leaf)) { throw "$Label did not publish its result." }
    $result = Get-Content -LiteralPath $last -Raw | ConvertFrom-Json
    if ($result.verdict -ne 'PASS') { throw "$Label returned $($result.verdict)." }
    $materialFindings = @($result.findings | Where-Object { $_.severity -in @('blocker', 'significant') })
    if ($materialFindings.Count -ne 0) { throw "$Label returned PASS with material findings." }
    return [ordered]@{
        jsonl_path = $jsonl
        jsonl_sha256 = Get-FileSha256 $jsonl
        stderr_path = $stderr
        stderr_sha256 = Get-FileSha256 $stderr
        result_path = $last
        result_sha256 = Get-FileSha256 $last
        invocation_path = $invocationPath
        invocation_sha256 = Get-FileSha256 $invocationPath
        prompt_input_proof = $promptInputProof
        pre_identity_sha256 = Get-FileSha256 (Join-Path $script:EvidenceRoot ($Label + '.pre-identity.json'))
        post_identity_sha256 = Get-FileSha256 (Join-Path $script:EvidenceRoot ($Label + '.post-identity.json'))
        pre_call_quiescence = $preCallQuiescence
        post_call_quiescence = $postCallQuiescence
    }
}

function Invoke-ZeroWritePreflight {
    if (Test-Path -LiteralPath $script:EvidenceRoot) {
        throw 'This deterministic Publication-4 lineage already exists. Run Inspect; do not create another attempt.'
    }
    $quiescenceBefore = Get-QuiescenceProof
    $priorP3Before = Get-PriorP3EvidenceProof

    $liveCodexHome = if ([string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
        Join-Path $env:USERPROFILE '.codex'
    } else {
        $env:CODEX_HOME
    }
    if (-not [System.IO.Path]::IsPathRooted($liveCodexHome)) {
        throw 'The live CODEX_HOME must be an absolute path.'
    }
    $liveCodexHome = [System.IO.Path]::GetFullPath($liveCodexHome).TrimEnd('\')
    $liveCodexHomeFirst = Get-CodexHomeManifest $liveCodexHome
    if (-not $liveCodexHomeFirst.exists) { throw 'The live CODEX_HOME is absent.' }
    $liveAuthPath = Join-Path $liveCodexHome 'auth.json'
    if (-not (Test-Path -LiteralPath $liveAuthPath -PathType Leaf)) { throw 'Codex authentication is unavailable.' }
    $liveAuthHash = Get-FileSha256 $liveAuthPath

    $gitCommand = Get-Command git -CommandType Application | Select-Object -First 1
    if (-not $gitCommand) { throw 'Git executable is unavailable.' }
    $gitPrefix = @(
        '-c', 'core.fsmonitor=false',
        '-c', 'core.untrackedCache=false',
        '-C', $script:RepoRoot
    )
    $originalOptionalLocks = [Environment]::GetEnvironmentVariable('GIT_OPTIONAL_LOCKS', 'Process')
    try {
        $env:GIT_OPTIONAL_LOCKS = '0'
        $repoRootObserved = (& $gitCommand.Source @gitPrefix rev-parse --show-toplevel).Trim()
        if ($LASTEXITCODE -ne 0) { throw 'Failed to resolve the publication worktree root.' }
        $repoRootObserved = [System.IO.Path]::GetFullPath($repoRootObserved).TrimEnd('\')
        $gitCommonDir = (& $gitCommand.Source @gitPrefix rev-parse --git-common-dir).Trim()
        if ($LASTEXITCODE -ne 0) { throw 'Failed to resolve the publication Git common directory.' }
        $head = (& $gitCommand.Source @gitPrefix rev-parse HEAD).Trim()
        if ($LASTEXITCODE -ne 0) { throw 'Failed to resolve the publication HEAD.' }
        $headTree = (& $gitCommand.Source @gitPrefix rev-parse 'HEAD^{tree}').Trim()
        if ($LASTEXITCODE -ne 0) { throw 'Failed to resolve the publication tree.' }
        $branch = (& $gitCommand.Source @gitPrefix branch --show-current).Trim()
        if ($LASTEXITCODE -ne 0) { throw 'Failed to resolve the publication branch.' }
        $statusLines = @(& $gitCommand.Source @gitPrefix status --porcelain=v1 --untracked-files=all)
        if ($LASTEXITCODE -ne 0) { throw 'Failed to inspect the publication worktree.' }
        if (-not $repoRootObserved.Equals($script:RepoRoot, [StringComparison]::OrdinalIgnoreCase) -or
            $head -cne $ApprovedCommit -or $branch -cne $ExpectedBranch -or $statusLines.Count -ne 0) {
            throw 'Publication worktree identity is not the exact clean approved anchor.'
        }

        $bundleHashes = [ordered]@{}
        foreach ($relative in $RequiredBundle) {
            $path = Join-Path $script:RepoRoot $relative
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing publication file: $relative" }
            $treeHash = (& $gitCommand.Source @gitPrefix rev-parse ($ApprovedCommit + ':' + $relative)).Trim()
            if ($LASTEXITCODE -ne 0) { throw "Missing committed publication blob: $relative" }
            $workHash = (& $gitCommand.Source @gitPrefix hash-object -- $relative).Trim()
            if ($LASTEXITCODE -ne 0 -or $treeHash -cne $workHash) { throw "Publication byte mismatch: $relative" }
            $bundleHashes[$relative] = Get-FileSha256 $path
        }
    }
    finally {
        if ($null -eq $originalOptionalLocks) { Remove-Item Env:GIT_OPTIONAL_LOCKS -ErrorAction SilentlyContinue }
        else { $env:GIT_OPTIONAL_LOCKS = $originalOptionalLocks }
    }

    $codexExe = Join-Path $env:APPDATA 'npm\node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc\bin\codex.exe'
    $codexPackagePath = Join-Path $env:APPDATA 'npm\node_modules\@openai\codex\package.json'
    if (-not (Test-Path -LiteralPath $codexExe -PathType Leaf) -or
        -not (Test-Path -LiteralPath $codexPackagePath -PathType Leaf)) {
        throw 'Pinned Codex installation is absent.'
    }
    if ((Get-FileSha256 $codexExe) -cne $ExpectedCodexHash -or
        (Get-FileSha256 $codexPackagePath) -cne $ExpectedCodexPackageHash) {
        throw 'Pinned Codex installation hash mismatch.'
    }
    $codexPackage = Get-Content -LiteralPath $codexPackagePath -Raw | ConvertFrom-Json
    if ($codexPackage.name -cne '@openai/codex' -or $codexPackage.version -cne '0.147.0') {
        throw 'Pinned Codex package identity mismatch.'
    }

    $pythonCommand = Get-Command python -CommandType Application | Select-Object -First 1
    if (-not $pythonCommand) { throw 'Pinned CPython is unavailable.' }
    $pythonExe = $pythonCommand.Source
    $pythonVersionLines = @(& $pythonExe --version 2>&1)
    $pythonExitCode = $LASTEXITCODE
    $pythonVersion = ($pythonVersionLines -join "`n").Trim()
    if ($pythonExitCode -ne 0 -or $pythonVersion -cne $ExpectedPythonVersion) {
        throw 'Pinned CPython version mismatch.'
    }
    if ((Get-FileSha256 $pythonExe) -cne $ExpectedPythonHash) { throw 'Pinned CPython executable hash mismatch.' }

    $baseArgvTemplate = @('exec', '--model', 'gpt-5.6-terra') + @(Get-ClosedConfigArguments) + @(
        '--sandbox', '<sandbox>', '--cd', '<instruction-free-launch-root>', '--add-dir', '<owner-worktree>',
        '--skip-git-repo-check', '--ephemeral', '--ignore-user-config', '--ignore-rules',
        '--strict-config', '--output-schema', '<result-schema>', '--json',
        '--output-last-message', '<last-message-file>', '-'
    )
    $baseArgvHash = Get-Sha256Text (($baseArgvTemplate | ConvertTo-Json -Compress) + "`n")

    $liveCodexHomeSecond = Get-CodexHomeManifest $liveCodexHome
    if (-not (Test-ManifestEqual $liveCodexHomeFirst $liveCodexHomeSecond)) {
        throw 'The live CODEX_HOME changed during zero-write preflight.'
    }
    if ((Get-FileSha256 $liveAuthPath) -cne $liveAuthHash) {
        throw 'The live Codex authentication bytes changed during zero-write preflight.'
    }
    $priorP3After = Assert-PriorP3EvidenceUnchanged $priorP3Before
    $quiescenceAfter = Get-QuiescenceProof
    if (Test-Path -LiteralPath $script:EvidenceRoot) {
        throw 'The Publication-4 evidence root appeared during zero-write preflight.'
    }

    return [ordered]@{
        schema_version = 1
        action = 'Preflight'
        verdict = 'PASS'
        request_id = $script:RequestId
        approved_commit = $ApprovedCommit
        approval_message_sha256 = $script:ApprovalMessageHash
        approval_message_file_sha256 = Get-FileSha256 $script:CanonicalApprovalMessageFile
        evidence_root = $script:EvidenceRoot
        evidence_root_absent = $true
        repo = [ordered]@{
            root = $repoRootObserved
            git_common_dir = $gitCommonDir
            ref = $branch
            head = $head
            tree = $headTree
            status_sha256 = Get-Sha256Text ($statusLines -join "`n")
            status_count = $statusLines.Count
        }
        bundle_sha256 = $bundleHashes
        codex = [ordered]@{
            requested_version = $ExpectedCodexVersion
            executable = $codexExe
            executable_sha256 = $ExpectedCodexHash
            package_sha256 = $ExpectedCodexPackageHash
        }
        python = [ordered]@{
            version = $pythonVersion
            executable = $pythonExe
            executable_sha256 = $ExpectedPythonHash
        }
        base_argv_sha256 = $baseArgvHash
        live_codex_home = $liveCodexHome
        live_codex_home_manifest = $liveCodexHomeSecond
        live_auth_sha256 = $liveAuthHash
        prior_publication3_before = $priorP3Before
        prior_publication3_after = $priorP3After
        quiescence_before = $quiescenceBefore
        quiescence_after = $quiescenceAfter
    }
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$script:RepoRoot = $RepoRoot
$RequiredBundle = @(
    'plan.md',
    'documentation/native-claude-codex-skill-parity-plan.md',
    'documentation/native-claude-codex-skill-parity-terra-amendment.md',
    'documentation/native-claude-codex-skill-parity-proposal.html',
    'schemas/terra-bootstrap-result-v1.schema.json',
    'tools/run-goal-np-terra-bootstrap.ps1'
)
$AllowedAdminPaths = @(
    'config/workspace-targets.json',
    'config/goal-np-bootstrap-execution.json',
    'config/goal-np-test-requirements.txt',
    'schemas/approval1-request-v1.schema.json',
    'schemas/approval1-v1.schema.json',
    'schemas/issue-sync-v1.schema.json',
    'schemas/github-issue-mutation-journal-v1.schema.json',
    'schemas/execution-status-event-v1.schema.json',
    'schemas/bootstrap-np01-v1.schema.json',
    'schemas/np-bootstrap-execution-v1.schema.json',
    'schemas/admin-sync-v1.schema.json',
    'schemas/workspace-targets-v1.schema.json',
    'schemas/workspace-roots-v1.schema.json',
    'tools/bootstrap-goal-np-approval.ps1',
    'tests/package-integrity/test_goal_np_admin_sync.py'
)

$script:CanonicalApprovalMessageFile = Join-Path $env:LOCALAPPDATA 'SkillMesh\Evidence\GoalNP\Publication4\approval1-message.txt'
$suppliedApprovalPath = [System.IO.Path]::GetFullPath($ApprovalMessageFile)
$canonicalApprovalPath = [System.IO.Path]::GetFullPath($script:CanonicalApprovalMessageFile)
if (-not $suppliedApprovalPath.Equals($canonicalApprovalPath, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'ApprovalMessageFile is not the canonical Publication-4 approval path.'
}
if (-not (Test-Path -LiteralPath $canonicalApprovalPath -PathType Leaf)) { throw 'ApprovalMessageFile does not exist.' }
$expectedApprovalBytes = $Utf8NoBom.GetBytes($ExpectedApproval + "`n")
$actualApprovalBytes = [System.IO.File]::ReadAllBytes($canonicalApprovalPath)
if ([Convert]::ToBase64String($actualApprovalBytes) -cne [Convert]::ToBase64String($expectedApprovalBytes)) {
    throw 'Approval message is not exact UTF-8 without BOM, with one final LF, for Publication 4.'
}
$script:ApprovalMessageHash = Get-Sha256Text $ExpectedApproval
$identityText = @(
    'publication-4-recovery-v1',
    $ApprovedCommit,
    $script:ApprovalMessageHash,
    $PriorP3RequestId,
    $PriorP3StateHash
) -join "`n"
$script:RequestId = 'tba-' + (Get-Sha256Text $identityText)
$script:EvidenceRoot = Join-Path $env:LOCALAPPDATA ('SkillMesh\Evidence\GoalNP\TerraBootstrap\' + $script:RequestId)
$script:StatePath = Join-Path $script:EvidenceRoot 'state.json'

if ($Action -eq 'Inspect') {
    if (-not (Test-Path -LiteralPath $script:StatePath -PathType Leaf)) { throw 'No matching Terra bootstrap state exists.' }
    $stateText = Get-Content -LiteralPath $script:StatePath -Raw
    $state = $stateText | ConvertFrom-Json
    if ($state.schema_version -ne 1 -or $state.request_id -cne $script:RequestId -or
        $state.approved_commit -cne $ApprovedCommit -or
        $state.approval_message_sha256 -cne $script:ApprovalMessageHash) {
        throw 'Terra bootstrap state identity is invalid.'
    }
    if ($state.phase -eq 'pass') {
        $expectedReceipt = Join-Path $script:EvidenceRoot 'receipt.json'
        if ($state.receipt_path -cne $expectedReceipt -or
            -not (Test-Path -LiteralPath $expectedReceipt -PathType Leaf) -or
            (Get-FileSha256 $expectedReceipt) -cne $state.receipt_sha256) {
            throw 'Terra bootstrap PASS receipt binding is invalid.'
        }
        $receipt = Get-Content -LiteralPath $expectedReceipt -Raw | ConvertFrom-Json
        if ($receipt.schema_version -ne 1 -or $receipt.request_id -cne $script:RequestId -or
            $receipt.approved_commit -cne $ApprovedCommit -or $receipt.verdict -cne 'PASS') {
            throw 'Terra bootstrap PASS receipt identity is invalid.'
        }
    }
    $stateText
    exit 0
}

$preflight = Invoke-ZeroWritePreflight
if ($Action -eq 'Preflight') {
    $preflight | ConvertTo-Json -Depth 12
    exit 0
}

if (Test-Path -LiteralPath $script:EvidenceRoot) {
    throw 'This deterministic Publication-4 lineage already exists. Run Inspect; do not create another attempt.'
}
New-Item -ItemType Directory -Path $script:EvidenceRoot | Out-Null
$script:LaunchRoot = Join-Path $script:EvidenceRoot 'instruction-free-launch-roots'
$previous = Get-Location
$EnvironmentNames = @(
    'CODEX_HOME', 'TEMP', 'TMP', 'PIP_CACHE_DIR', 'PYTHONNOUSERSITE',
    'PYTHONDONTWRITEBYTECODE', 'PIP_NO_INPUT', 'PIP_DISABLE_PIP_VERSION_CHECK', 'PIP_CONFIG_FILE'
)
$OriginalEnvironment = [ordered]@{}
foreach ($name in $EnvironmentNames) {
    $OriginalEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
$script:DisposableCodexHome = $null
$LiveCodexHome = $preflight.live_codex_home
$LiveCodexHomeBefore = $preflight.live_codex_home_manifest
$PriorP3Before = $preflight.prior_publication3_after
$bundleHashes = $preflight.bundle_sha256
$baseArgvHash = $preflight.base_argv_sha256
$PythonExe = $preflight.python.executable
$script:CodexExe = $preflight.codex.executable
$script:ResultSchema = Join-Path $RepoRoot 'schemas\terra-bootstrap-result-v1.schema.json'
try {
    $preflightPath = Join-Path $script:EvidenceRoot 'preflight.json'
    Write-Utf8NoBom $preflightPath (($preflight | ConvertTo-Json -Depth 12) + "`n")
    New-Item -ItemType Directory -Path $script:LaunchRoot | Out-Null
    $LiveAuthPath = Join-Path $LiveCodexHome 'auth.json'
    if (-not (Test-Path -LiteralPath $LiveAuthPath -PathType Leaf)) { throw 'Codex authentication is unavailable.' }
    if ((Get-FileSha256 $LiveAuthPath) -cne $preflight.live_auth_sha256) {
        throw 'Live Codex authentication changed after preflight.'
    }
    $postAllocationLiveCodexHome = Get-CodexHomeManifest $LiveCodexHome
    if (-not (Test-ManifestEqual $LiveCodexHomeBefore $postAllocationLiveCodexHome)) {
        throw 'The live CODEX_HOME changed after preflight and before execution.'
    }
    $PriorP3PostAllocation = Assert-PriorP3EvidenceUnchanged $PriorP3Before
    $script:DisposableCodexHome = Join-Path $script:EvidenceRoot 'disposable-codex-home'
    New-Item -ItemType Directory -Path $script:DisposableCodexHome | Out-Null
    Copy-Item -LiteralPath $LiveAuthPath -Destination (Join-Path $script:DisposableCodexHome 'auth.json')
    if ((Get-FileSha256 (Join-Path $script:DisposableCodexHome 'auth.json')) -cne $preflight.live_auth_sha256) {
        throw 'Disposable Codex authentication copy mismatch.'
    }
    $env:CODEX_HOME = $script:DisposableCodexHome

    Set-Location $RepoRoot
    $postAllocationQuiescence = Get-QuiescenceProof
    if ((& $script:CodexExe --version).Trim() -cne $ExpectedCodexVersion) { throw 'Pinned Codex version mismatch.' }

    Write-State 'prepared' @{
        preflight_sha256 = Get-FileSha256 $preflightPath
        bundle_sha256 = $bundleHashes
        codex_executable_sha256 = $ExpectedCodexHash
        python_executable_sha256 = $ExpectedPythonHash
        live_codex_home_before = $LiveCodexHomeBefore
        prior_publication3_before = $PriorP3Before
        prior_publication3_post_allocation = $PriorP3PostAllocation
        post_allocation_quiescence = $postAllocationQuiescence
        base_argv_sha256 = $baseArgvHash
    }

    $implementationPrompt = @"
Implement only ADMIN-BOOTSTRAP for Goal NP Publication 4 at commit $ApprovedCommit.
The exact owner worktree is $RepoRoot. Read $RepoRoot\plan.md,
$RepoRoot\documentation\native-claude-codex-skill-parity-plan.md, and
$RepoRoot\documentation\native-claude-codex-skill-parity-terra-amendment.md. The amendment controls
the implementation executor. Modify only the 15 ADMIN paths enumerated there and in the base plan.
Implement the Terra-direct executor fields and zero-model deterministic issue synchronization.
Do not commit, stage, mutate GitHub, invoke another model, install dependencies, run tests, use a
repo/user skill, plugin, MCP, web, or browser, write a live discovery/config home, or touch any other
path. Built-in system-skill instructions may be read and followed when their system trigger requires
it, but they add no path, tool, network, model, or write authority. The outer launcher owns the exact
contained tests and review. End with schema-valid JSON only; PASS means the files are ready for those
deterministic gates.
"@
    $implementationPromptPath = Join-Path $script:EvidenceRoot 'implementation-prompt.txt'
    Write-Utf8NoBom $implementationPromptPath $implementationPrompt
    Write-State 'implementation-started' @{ implementation_prompt_sha256 = Get-FileSha256 $implementationPromptPath }
    $expectedImplementationIdentity = Get-RepoIdentity 'implementation-expected'
    $approvedTree = (& git rev-parse ($ApprovedCommit + '^{tree}')).Trim()
    if ($expectedImplementationIdentity.ref -cne $ExpectedBranch -or
        $expectedImplementationIdentity.head -cne $ApprovedCommit -or
        $expectedImplementationIdentity.tree -cne $approvedTree -or
        $expectedImplementationIdentity.index_tree -cne $approvedTree -or
        $expectedImplementationIdentity.worktree_tree -cne $approvedTree -or
        $expectedImplementationIdentity.status_count -ne 0 -or
        $expectedImplementationIdentity.status_sha256 -cne (Get-Sha256Text '')) {
        throw 'Implementation anchor changed before the Terra call.'
    }
    $implementation = Invoke-Terra 'implementation' 'workspace-write' $implementationPromptPath $expectedImplementationIdentity
    if ((& git rev-parse HEAD).Trim() -cne $ApprovedCommit) { throw 'Implementation process changed HEAD.' }
    Write-State 'implementation-pass' @{ implementation = $implementation }

    $changed = @(Assert-AdminScope)
    $LockPath = Join-Path $RepoRoot 'config\goal-np-test-requirements.txt'
    if ((Get-Item -LiteralPath $LockPath).Length -ne 661 -or (Get-FileSha256 $LockPath) -cne $ExpectedLockHash) {
        throw 'ADMIN test lock byte-count/hash mismatch.'
    }
    $ToolingRoot = Join-Path $script:EvidenceRoot 'tooling'
    $VenvRoot = Join-Path $ToolingRoot 'venv'
    $TempRoot = Join-Path $ToolingRoot 'temp'
    $PipCacheRoot = Join-Path $ToolingRoot 'pip-cache'
    $PytestCacheRoot = Join-Path $ToolingRoot 'pytest-cache'
    foreach ($directory in @($ToolingRoot, $TempRoot, $PipCacheRoot, $PytestCacheRoot)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
    $env:TEMP = $TempRoot
    $env:TMP = $TempRoot
    $env:PIP_CACHE_DIR = $PipCacheRoot
    $env:PYTHONNOUSERSITE = '1'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:PIP_NO_INPUT = '1'
    $env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
    $env:PIP_CONFIG_FILE = 'NUL'
    $venvCreate = Invoke-RecordedProcess 'venv-create' $PythonExe @('-m', 'venv', $VenvRoot) $script:EvidenceRoot
    $VenvPython = Join-Path $VenvRoot 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) { throw 'Contained test venv was not created.' }
    $pipInstall = Invoke-RecordedProcess 'pip-install' $VenvPython @(
        '-m', 'pip', 'install', '--require-hashes', '--only-binary=:all:', '-r', $LockPath
    ) $script:EvidenceRoot
    $ReviewLaunchRoot = Join-Path $script:LaunchRoot 'review'
    New-Item -ItemType Directory -Path $ReviewLaunchRoot -Force | Out-Null
    $ReviewInputRoot = Join-Path $ReviewLaunchRoot 'review-input'
    New-Item -ItemType Directory -Path $ReviewInputRoot | Out-Null
    $focusedTests = Invoke-RecordedProcess 'focused-tests' $VenvPython @(
        '-m', 'pytest', '-q', '-o', ('cache_dir=' + $PytestCacheRoot),
        'tests/package-integrity/test_goal_np_admin_sync.py'
    ) $ReviewInputRoot
    $rootTests = Invoke-RecordedProcess 'root-tests' $VenvPython @(
        '-m', 'pytest', '-o', ('cache_dir=' + $PytestCacheRoot)
    ) $ReviewInputRoot
    $changed = @(Assert-AdminScope)

    $gitCommand = Get-Command git -CommandType Application | Select-Object -First 1
    if (-not $gitCommand) { throw 'Git executable is unavailable.' }
    $candidateIndex = Join-Path $script:EvidenceRoot 'candidate.index'
    $originalGitIndex = $env:GIT_INDEX_FILE
    try {
        $env:GIT_INDEX_FILE = $candidateIndex
        & $gitCommand.Source read-tree $ApprovedCommit
        if ($LASTEXITCODE -ne 0) { throw 'Failed to initialize the candidate index.' }
        & $gitCommand.Source add -A -- $AllowedAdminPaths
        if ($LASTEXITCODE -ne 0) { throw 'Failed to populate the candidate index.' }
        $candidateTree = (& $gitCommand.Source write-tree).Trim()
        if ($LASTEXITCODE -ne 0) { throw 'Failed to write the candidate tree.' }
        $candidateStaged = @(& $gitCommand.Source diff --cached --name-only $ApprovedCommit | Where-Object { $_ } | Sort-Object -Unique)
        if (Compare-Object $changed $candidateStaged) { throw 'Candidate index does not equal the closed ADMIN diff.' }
        $candidateDiff = Invoke-RecordedProcess 'candidate-diff' $gitCommand.Source `
            (@('diff', '--cached', '--binary', $ApprovedCommit, '--') + $AllowedAdminPaths) $ReviewInputRoot
        $diffCheck = Invoke-RecordedProcess 'candidate-diff-check' $gitCommand.Source `
            (@('diff', '--cached', '--check', $ApprovedCommit, '--') + $AllowedAdminPaths) $ReviewInputRoot
    }
    finally {
        if ($null -eq $originalGitIndex) { Remove-Item Env:GIT_INDEX_FILE -ErrorAction SilentlyContinue }
        else { $env:GIT_INDEX_FILE = $originalGitIndex }
    }

    $candidateEvidence = [ordered]@{
        schema_version = 1
        approved_commit = $ApprovedCommit
        base_tree = (& git rev-parse ($ApprovedCommit + '^{tree}')).Trim()
        candidate_tree = $candidateTree
        changed_paths = $changed
        candidate_diff = $candidateDiff
        diff_check = $diffCheck
        implementation_jsonl_sha256 = $implementation.jsonl_sha256
        implementation_result_sha256 = $implementation.result_sha256
        python_version = $ExpectedPythonVersion
        python_executable_sha256 = $ExpectedPythonHash
        test_lock_sha256 = $ExpectedLockHash
        venv_create = $venvCreate
        pip_install = $pipInstall
        focused_tests = $focusedTests
        root_tests = $rootTests
    }
    $candidateEvidencePath = Join-Path $ReviewInputRoot 'candidate-evidence.json'
    Write-Utf8NoBom $candidateEvidencePath (($candidateEvidence | ConvertTo-Json -Depth 10) + "`n")

    $reviewPrompt = @"
    Independently review the exact uncommitted ADMIN-BOOTSTRAP candidate for Goal NP Publication 4.
The owner worktree is $RepoRoot and the approved commit is $ApprovedCommit. Read the exact plan at
$RepoRoot\documentation\native-claude-codex-skill-parity-plan.md and controlling amendment at
$RepoRoot\documentation\native-claude-codex-skill-parity-terra-amendment.md. The candidate evidence
is $candidateEvidencePath; its SHA-256 is $(Get-FileSha256 $candidateEvidencePath). The exact binary
diff is $($candidateDiff.stdout_path) with SHA-256 $($candidateDiff.stdout_sha256). The evidence binds
the candidate tree, implementation JSONL, contained lock-based test results, path scope, and diff gate.
Check standalone executability, security/capability boundaries, schemas, zero-model issue sync, crash
behavior, exact 15-path scope, and absence of live/GitHub/model side effects. You are read-only. Do not
invoke another model or use a repo/user skill, plugin, MCP, web, or browser. Built-in system-skill
instructions may be read and followed when their system trigger requires it, but they add no authority.
Do not change any file. End with schema-valid JSON only. PASS permits no blocker or significant gap.
"@
    $reviewPromptPath = Join-Path $script:EvidenceRoot 'review-prompt.txt'
    Write-Utf8NoBom $reviewPromptPath $reviewPrompt
    Write-State 'review-started' @{
        review_prompt_sha256 = Get-FileSha256 $reviewPromptPath
        candidate_evidence_sha256 = Get-FileSha256 $candidateEvidencePath
    }
    $expectedReviewIdentity = Get-RepoIdentity 'review-expected'
    if ($expectedReviewIdentity.ref -cne $ExpectedBranch -or
        $expectedReviewIdentity.head -cne $ApprovedCommit -or
        $expectedReviewIdentity.tree -cne $approvedTree -or
        $expectedReviewIdentity.index_tree -cne $approvedTree -or
        $expectedReviewIdentity.worktree_tree -cne $candidateTree) {
        throw 'Reviewed candidate changed before the Terra review call.'
    }
    $review = Invoke-Terra 'review' 'read-only' $reviewPromptPath $expectedReviewIdentity
    Write-State 'review-pass' @{ implementation = $implementation; review = $review; candidate_tree = $candidateTree }

    $LiveCodexHomeAfter = Get-CodexHomeManifest $LiveCodexHome
    if ($LiveCodexHomeBefore.exists -ne $LiveCodexHomeAfter.exists -or
        $LiveCodexHomeBefore.entry_count -ne $LiveCodexHomeAfter.entry_count -or
        $LiveCodexHomeBefore.sha256 -cne $LiveCodexHomeAfter.sha256) {
        throw 'The live Codex home changed during the disposable Terra envelope.'
    }
    $PriorP3BeforeCommit = Assert-PriorP3EvidenceUnchanged $PriorP3Before
    $preCommitQuiescence = Get-QuiescenceProof
    Remove-DisposableCodexHome

    $changed = @(Assert-AdminScope)
    & git add -- $AllowedAdminPaths
    if ($LASTEXITCODE -ne 0) { throw 'Failed to stage the exact ADMIN paths.' }
    $staged = @(& git diff --cached --name-only | Where-Object { $_ } | Sort-Object -Unique)
    $unstaged = @(& git diff --name-only)
    $untracked = @(& git ls-files --others --exclude-standard)
    if ((Compare-Object $changed $staged) -or $unstaged.Count -ne 0 -or $untracked.Count -ne 0) {
        throw 'Staged ADMIN bytes do not equal the closed reviewed diff.'
    }
    $stagedTree = (& git write-tree).Trim()
    if ($LASTEXITCODE -ne 0 -or $stagedTree -cne $candidateTree) { throw 'Staged tree differs from the reviewed candidate tree.' }
    & git commit -m 'chore(goal-np): bootstrap approval tooling'
    if ($LASTEXITCODE -ne 0) { throw 'ADMIN commit failed.' }
    $adminCommit = (& git rev-parse HEAD).Trim()
    $finalStatus = @(& git status --porcelain=v1 --untracked-files=all)
    if ($finalStatus.Count -ne 0) { throw 'ADMIN commit did not leave a clean worktree.' }
    $PriorP3Terminal = Assert-PriorP3EvidenceUnchanged $PriorP3Before

    $receipt = [ordered]@{
        schema_version = 1
        request_id = $script:RequestId
        verdict = 'PASS'
        approved_commit = $ApprovedCommit
        admin_commit = $adminCommit
        approval_message_sha256 = $script:ApprovalMessageHash
        preflight_sha256 = Get-FileSha256 $preflightPath
        bundle_sha256 = $bundleHashes
        codex_version = $ExpectedCodexVersion
        codex_executable_sha256 = $ExpectedCodexHash
        requested_model = 'gpt-5.6-terra'
        requested_reasoning_effort = 'xhigh'
        reported_identity_status = 'unavailable'
        base_argv_sha256 = $baseArgvHash
        implementation = $implementation
        review = $review
        candidate_evidence_sha256 = Get-FileSha256 $candidateEvidencePath
        candidate_tree = $candidateTree
        python_version = $ExpectedPythonVersion
        python_executable_sha256 = $ExpectedPythonHash
        test_lock_sha256 = $ExpectedLockHash
        focused_tests = $focusedTests
        root_tests = $rootTests
        live_codex_home_before = $LiveCodexHomeBefore
        live_codex_home_after = $LiveCodexHomeAfter
        prior_publication3_before = $PriorP3Before
        prior_publication3_before_commit = $PriorP3BeforeCommit
        prior_publication3_terminal = $PriorP3Terminal
        pre_commit_quiescence = $preCommitQuiescence
        disposable_codex_home_removed = $true
        completed_utc = [DateTime]::UtcNow.ToString('o')
    }
    $receiptPath = Join-Path $script:EvidenceRoot 'receipt.json'
    Write-Utf8NoBom $receiptPath (($receipt | ConvertTo-Json -Depth 12) + "`n")
    Write-State 'pass' @{ admin_commit = $adminCommit; receipt_path = $receiptPath; receipt_sha256 = Get-FileSha256 $receiptPath }
    [ordered]@{ verdict = 'PASS'; admin_commit = $adminCommit; receipt_path = $receiptPath; next_action = 'Run committed bootstrap-goal-np-approval.ps1 Prepare -> Sync -> Inspect -> RunBootstrapNP01.' } |
        ConvertTo-Json -Depth 4
}
catch {
    $originalError = $_
    $blocked = [ordered]@{ error = $originalError.Exception.Message }
    try {
        Remove-DisposableCodexHome
        $blocked['disposable_codex_home_removed'] = $true
    }
    catch {
        $blocked['disposable_codex_home_removed'] = $false
        $blocked['disposable_codex_home_cleanup_error'] = $_.Exception.Message
    }
    if ($LiveCodexHome -and $LiveCodexHomeBefore) {
        try {
            $blockedLiveCodexHomeAfter = Get-CodexHomeManifest $LiveCodexHome
            $blocked['live_codex_home_after'] = $blockedLiveCodexHomeAfter
            $blocked['live_codex_home_unchanged'] = (
                $LiveCodexHomeBefore.exists -eq $blockedLiveCodexHomeAfter.exists -and
                $LiveCodexHomeBefore.entry_count -eq $blockedLiveCodexHomeAfter.entry_count -and
                $LiveCodexHomeBefore.sha256 -ceq $blockedLiveCodexHomeAfter.sha256
            )
        }
        catch {
            $blocked['live_codex_home_manifest_error'] = $_.Exception.Message
        }
    }
    if ($PriorP3Before) {
        try {
            $blockedPriorP3After = Assert-PriorP3EvidenceUnchanged $PriorP3Before
            $blocked['prior_publication3_after'] = $blockedPriorP3After
            $blocked['prior_publication3_unchanged'] = $true
        }
        catch {
            $blocked['prior_publication3_unchanged'] = $false
            $blocked['prior_publication3_manifest_error'] = $_.Exception.Message
        }
    }
    if (Test-Path -LiteralPath $script:EvidenceRoot) {
        Write-State 'blocked' $blocked
    }
    throw $originalError
}
finally {
    try { Remove-DisposableCodexHome }
    finally {
        foreach ($name in $EnvironmentNames) {
            $value = $OriginalEnvironment[$name]
            if ($null -eq $value) { Remove-Item -Path ('Env:' + $name) -ErrorAction SilentlyContinue }
            else { Set-Item -Path ('Env:' + $name) -Value $value }
        }
        Set-Location $previous
    }
}
