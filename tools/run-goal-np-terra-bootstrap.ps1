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

$ExpectedApproval = 'Approve Goal NP plan Publication 7 with D01-D10 and the Terra writable-root grammar recovery amendment.'
$ExpectedBranch = 'plan/native-codex-skill-parity'
$ExpectedCodexVersion = 'codex-cli 0.147.0'
$ExpectedCodexHash = '935a1911ed2556e4ffcec995f4886ac2ac425863ba26fed264df62e30272ad9d'
$ExpectedCodexPackageHash = 'bbaf3b9597b54bc1d4cf4aea93870e9035629d79bdaba58234011c31f0cfcf3d'
$ExpectedPythonVersion = 'Python 3.14.3'
$ExpectedPythonHash = 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
$ExpectedLockHash = 'c197caa7da4306f0b744c9d352ce4c1a858d57514453c1ec1d249c83564cd555'
$PriorP6RequestId = 'tba-cc76394efc1359d75b406ce5a2d2300d5ed41020b5cf7fc972ba3039dc3a6ab0'
$PriorP6ApprovedCommit = 'd0f83210e3092e18a28ee24db20a1af95887c31b'
$PriorP6ExpectedApproval = 'Approve Goal NP plan Publication 6 with D01-D10 and the Terra sandbox-attestation recovery amendment.'
$PriorP6ApprovalMessageHash = 'ad20542c0d5dc9b77fbab14413998f614ab178ca4949a1269f06c08f24b3407e'
$PriorP6ApprovalMessageFileHash = '064e50a53d93dc976cb98b87a5a49d0260d91f88aadddb23bcd8bf60d9be2add'
$PriorP6HandoffHash = 'ae085575b9441080ece62194cd4a3144df809eaa9d70b2ed2fcd76624d455b47'
$PriorP6FailureCode = 'PERMISSION_ATTESTATION_FAILED'
$PriorP6FailureLabel = 'preclaim-permission-attestation'
$PriorP6FailureMessage = 'Permissions text differs from the complete closed permission grammar.'
$PriorP5RequestId = 'tba-03e474757a5e0c92e8d3f0bd4c5a0731a742397a43c99d5e027016643fced916'
$PriorP5ApprovedCommit = '6d292bb37c37944c71ed8b18214fabb23f22869e'
$PriorP5ApprovalMessageHash = '2d19ad716f3179baf67c67c77d19dfb29697ea5b2e6f2b0a0d1fe87ee03d0f47'
$PriorP5ApprovalMessageFileHash = '5ad7472cb113d6965de18204dc1b7f860a0c2982ad1e8152e34547efa714a8e3'
$PriorP5StateHash = 'b0e9355ff3f39c1ccca196ae45ebe7c4f042c9fcd2587d84882c7d9af4724f50'
$PriorP5RootManifestHash = '11f84ea3e5140a2832586f63fc362c97b92286b1663c91df2c80fb7784d6f700'
$PriorP5RootEntryCount = 17
$PriorP4RequestId = 'tba-461c20be4d35c7255a83d05f91f16c5bccbdd5a36af738360bcedc330ab6b1e4'
$PriorP4ApprovedCommit = '58223098887468953570ecf153494871c5404605'
$PriorP4ApprovalMessageHash = '1a7698085d7bc12e74d60874e0d64b4d069b039470ab17701541cfe6c77202fe'
$PriorP4ApprovalMessageFileHash = '2f74ea66ac7bdac38b419fd24b7e6caa9479de007bc178e69acd54f9f8b42857'
$PriorP4StateHash = '4517ecd2d5ff948bbcf7763e32686797f65b5112ceb14e71c96c8222e6e12e05'
$PriorP4RootManifestHash = '893c099e299a5152f26edd912a5bfcdc75bd69e030dfd40653c0365ffe4d5e44'
$PriorP4RootEntryCount = 9
$PriorP3RequestId = 'tba-b7e5898e6389ff19b3ce34738f16b47d0a832dfc4625789fbcf4308352f2b1a0'
$PriorP3ApprovedCommit = '71a5aea3fd21320d2fbb3cb9228bc52e42cb3215'
$PriorP3ApprovalMessageHash = '66df8cd413fddd097e80dc63ccfacab221e96c72c795345d14b72ae1ae3474ef'
$PriorP3ApprovalMessageFileHash = '33d3e1756ed2bfd661698da3dfdf85a921380efd87fe3d635b777dafe3c6e04b'
$PriorP3StateHash = 'ae59a6ac7f512d2e399675fe541b916d1710c209a13b45433642cf019a07df97'
$PriorP3RootManifestHash = '9b01de1f550019a8bf81c23431925b6f38a173ec1ce22023c765a2a8d290cdcf'
$PriorP3RootEntryCount = 3
$FailureCodes = @(
    'PROCESS_START_FAILED',
    'PROCESS_HANDLE_UNAVAILABLE',
    'PROCESS_TIMEOUT',
    'PROCESS_EXIT_CODE_UNAVAILABLE',
    'PROCESS_EXIT_NONZERO',
    'PROCESS_CANARY_FAILED',
    'PERMISSION_ATTESTATION_FAILED',
    'PERMISSION_STAGING_COLLISION',
    'PERMISSION_STAGING_CLEANUP_FAILED',
    'MODEL_VERDICT_BLOCKED',
    'MODEL_VERDICT_CHANGES_REQUIRED',
    'MODEL_VERDICT_INVALID',
    'MODEL_PASS_MATERIAL_FINDINGS',
    'PRIOR_PUBLICATION6_PRECLAIM_MISMATCH',
    'PRIOR_PUBLICATION5_EVIDENCE_MISMATCH',
    'PRIOR_PUBLICATION4_EVIDENCE_MISMATCH',
    'PRIOR_PUBLICATION3_EVIDENCE_MISMATCH',
    'UNEXPECTED_FAILURE'
)
$PermissionMismatchDiagnosticFields = @(
    'permission_expected_sha256',
    'permission_actual_sha256',
    'permission_expected_line_count',
    'permission_actual_line_count',
    'permission_first_differing_line_number',
    'permission_expected_line_present',
    'permission_actual_line_present',
    'permission_expected_line_sha256',
    'permission_actual_line_sha256'
)
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function New-P6Failure(
    [string]$Code,
    [string]$Label,
    [string]$Message,
    [System.Exception]$InnerException = $null,
    [string]$CauseCode = $null
) {
    if ($FailureCodes -cnotcontains $Code) { throw "Unknown Publication-7 failure code: $Code" }
    if ([string]::IsNullOrWhiteSpace($Label)) { $Label = 'launcher' }
    $rendered = "[$Code] [$Label] $Message"
    $exception = if ($InnerException) {
        New-Object System.InvalidOperationException($rendered, $InnerException)
    } else {
        New-Object System.InvalidOperationException($rendered)
    }
    $exception.Data['error_code'] = $Code
    $exception.Data['error_label'] = $Label
    if ($CauseCode) { $exception.Data['cause_code'] = $CauseCode }
    return $exception
}

function Get-P6FailureMetadata([System.Exception]$Exception) {
    $code = 'UNEXPECTED_FAILURE'
    $label = 'launcher'
    $causeCode = $null
    if ($Exception.Data.Contains('error_code') -and
        $FailureCodes -ccontains ([string]$Exception.Data['error_code'])) {
        $code = [string]$Exception.Data['error_code']
    }
    if ($Exception.Data.Contains('error_label') -and
        -not [string]::IsNullOrWhiteSpace([string]$Exception.Data['error_label'])) {
        $label = [string]$Exception.Data['error_label']
    }
    if ($Exception.Data.Contains('cause_code') -and
        $FailureCodes -ccontains ([string]$Exception.Data['cause_code'])) {
        $causeCode = [string]$Exception.Data['cause_code']
    }
    return [ordered]@{
        error_code = $code
        error_label = $label
        error = $Exception.Message
        cause_code = $causeCode
    }
}

function New-P6ModelVerdictFailure(
    [string]$Code,
    [string]$Label,
    [string]$Verdict,
    [string]$Message,
    [string]$ResultPath,
    [string]$ResultSha256
) {
    $exception = New-P6Failure $Code $Label $Message
    $exception.Data['model_verdict'] = $Verdict
    $exception.Data['model_result_path'] = $ResultPath
    $exception.Data['model_result_sha256'] = $ResultSha256
    return $exception
}

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

function Add-PermissionMismatchDiagnostics(
    [System.Collections.IDictionary]$Record,
    [System.Exception]$Exception
) {
    foreach ($field in $PermissionMismatchDiagnosticFields) {
        if ($Exception.Data.Contains($field)) { $Record[$field] = $Exception.Data[$field] }
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
        throw 'Publication 7 requires Windows PowerShell 5.1 Desktop.'
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
        throw 'Publication 7 must run in standalone powershell.exe, not an embedded or substituted shell.'
    }
    $ancestryRoot = $ancestry[$ancestry.Count - 1]
    if ($ancestryRoot -notin @('explorer', 'windowsterminal')) {
        throw "The process ancestry did not terminate at an allowed standalone-shell root: $ancestryRoot"
    }
    $forbiddenAncestors = @($ancestry.ToArray() | Where-Object { $forbiddenNames -ccontains $_ })
    if ($forbiddenAncestors.Count -ne 0) {
        throw ('Publication 7 must run from independent ordinary PowerShell; forbidden ancestry: ' +
            (($forbiddenAncestors | Sort-Object -Unique) -join ', '))
    }
    if ($globalForbidden.Count -ne 0) {
        $names = @($globalForbidden | ForEach-Object { Get-NormalizedProcessName $_.Name } | Sort-Object -Unique)
        throw ('Publication 7 requires all Code, Codex, Claude, ChatGPT, and Cursor processes to be closed: ' +
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

function Assert-LiveCodexHomeUnchanged(
    [System.Collections.IDictionary]$Expected,
    [string]$Label
) {
    $actual = Get-CodexHomeManifest $script:LiveCodexHome
    if (-not (Test-ManifestEqual $Expected $actual)) {
        throw "The live CODEX_HOME changed at boundary: $Label"
    }
    return $actual
}

function Get-PriorP6PreclaimProof {
    try {
        $priorApprovalPath = Join-Path $env:LOCALAPPDATA `
            'SkillMesh\Evidence\GoalNP\Publication6\approval1-message.txt'
        $priorHandoffPath = Join-Path $env:LOCALAPPDATA `
            ('SkillMesh\Evidence\GoalNP\Publication6\terra-transition-handoff-' +
                $PriorP6ApprovedCommit + '.txt')
        $priorEvidenceRoot = Join-Path $env:LOCALAPPDATA `
            ('SkillMesh\Evidence\GoalNP\TerraBootstrap\' + $PriorP6RequestId)
        $priorStagingPublicationRoot = Join-Path $env:LOCALAPPDATA `
            'SkillMesh\Staging\GoalNP\Publication6'
        $priorStagingRequestRoot = Join-Path $priorStagingPublicationRoot $PriorP6RequestId

        $priorIdentityText = @(
            'publication-6-sandbox-attestation-recovery-v1',
            $PriorP6ApprovedCommit,
            $PriorP6ApprovalMessageHash,
            $PriorP5RequestId,
            $PriorP5StateHash,
            $PriorP5RootManifestHash,
            $PriorP4RequestId,
            $PriorP4StateHash,
            $PriorP4RootManifestHash,
            $PriorP3RequestId,
            $PriorP3StateHash,
            $PriorP3RootManifestHash
        ) -join "`n"
        if (('tba-' + (Get-Sha256Text $priorIdentityText)) -cne $PriorP6RequestId) {
            throw 'The retired Publication-6 request identity does not reproduce.'
        }
        if ((Get-Sha256Text $PriorP6ExpectedApproval) -cne $PriorP6ApprovalMessageHash) {
            throw 'The retired Publication-6 approval-text identity does not reproduce.'
        }

        $gitCommand = Get-Command git -CommandType Application | Select-Object -First 1
        if (-not $gitCommand) { throw 'Git is unavailable for Publication-6 lineage proof.' }
        $originalOptionalLocks = [Environment]::GetEnvironmentVariable('GIT_OPTIONAL_LOCKS', 'Process')
        try {
            $env:GIT_OPTIONAL_LOCKS = '0'
            & $gitCommand.Source -c core.fsmonitor=false -c core.untrackedCache=false `
                -C $script:RepoRoot merge-base --is-ancestor `
                $PriorP6ApprovedCommit $ApprovedCommit 2>$null
            if ($LASTEXITCODE -ne 0) {
                throw 'The approved Publication-7 commit does not descend from the retired Publication-6 commit.'
            }
        }
        finally {
            if ($null -eq $originalOptionalLocks) {
                Remove-Item Env:GIT_OPTIONAL_LOCKS -ErrorAction SilentlyContinue
            }
            else { $env:GIT_OPTIONAL_LOCKS = $originalOptionalLocks }
        }

        if (-not (Test-Path -LiteralPath $priorApprovalPath -PathType Leaf)) {
            throw 'The retired Publication-6 approval file is absent.'
        }
        $approvalItem = Get-Item -LiteralPath $priorApprovalPath -Force -ErrorAction Stop
        if (($approvalItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'The retired Publication-6 approval file is a reparse point.'
        }
        Assert-NoAlternateDataStream $approvalItem.FullName
        $approvalFileHash = Get-FileSha256 $approvalItem.FullName
        if ($approvalFileHash -cne $PriorP6ApprovalMessageFileHash) {
            throw 'The retired Publication-6 approval file hash changed.'
        }
        $expectedApprovalBytes = $Utf8NoBom.GetBytes($PriorP6ExpectedApproval + "`n")
        $actualApprovalBytes = [System.IO.File]::ReadAllBytes($approvalItem.FullName)
        if ([Convert]::ToBase64String($actualApprovalBytes) -cne
            [Convert]::ToBase64String($expectedApprovalBytes)) {
            throw 'The retired Publication-6 approval file bytes changed.'
        }

        if (-not (Test-Path -LiteralPath $priorHandoffPath -PathType Leaf)) {
            throw 'The retired Publication-6 handoff is absent.'
        }
        $handoffItem = Get-Item -LiteralPath $priorHandoffPath -Force -ErrorAction Stop
        if (($handoffItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'The retired Publication-6 handoff is a reparse point.'
        }
        Assert-NoAlternateDataStream $handoffItem.FullName
        if ($handoffItem.Length -ne 18494) { throw 'The retired Publication-6 handoff length changed.' }
        $handoffHash = Get-FileSha256 $handoffItem.FullName
        if ($handoffHash -cne $PriorP6HandoffHash) {
            throw 'The retired Publication-6 handoff hash changed.'
        }
        if (Test-Path -LiteralPath $priorEvidenceRoot) {
            throw 'The retired Publication-6 preclaim request unexpectedly has an evidence root.'
        }
        if (Test-Path -LiteralPath $priorStagingRequestRoot) {
            throw 'The retired Publication-6 permission-staging request subtree reappeared.'
        }
        if (Test-Path -LiteralPath $priorStagingPublicationRoot) {
            throw 'The retired Publication-6 permission-staging publication root reappeared.'
        }

        return [ordered]@{
            request_id = $PriorP6RequestId
            approved_commit = $PriorP6ApprovedCommit
            approval_message_sha256 = $PriorP6ApprovalMessageHash
            approval_message_file_sha256 = $approvalFileHash
            handoff_sha256 = $handoffHash
            handoff_length = [int64]$handoffItem.Length
            evidence_root_absent = $true
            permission_staging_request_root_absent = $true
            permission_staging_publication_root_absent = $true
            operator_reported_preclaim_context = [ordered]@{
                error_code = $PriorP6FailureCode
                error_label = $PriorP6FailureLabel
                message_suffix = $PriorP6FailureMessage
            }
        }
    }
    catch {
        $metadata = Get-P6FailureMetadata $_.Exception
        if ($metadata.error_code -ceq 'PRIOR_PUBLICATION6_PRECLAIM_MISMATCH') { throw $_.Exception }
        throw (New-P6Failure 'PRIOR_PUBLICATION6_PRECLAIM_MISMATCH' 'publication-6-preclaim' `
            $_.Exception.Message $_.Exception)
    }
}

function Assert-PriorP6PreclaimUnchanged([System.Collections.IDictionary]$Expected) {
    $actual = Get-PriorP6PreclaimProof
    if ($actual.request_id -cne $Expected.request_id -or
        $actual.approved_commit -cne $Expected.approved_commit -or
        $actual.approval_message_sha256 -cne $Expected.approval_message_sha256 -or
        $actual.approval_message_file_sha256 -cne $Expected.approval_message_file_sha256 -or
        $actual.handoff_sha256 -cne $Expected.handoff_sha256 -or
        $actual.handoff_length -ne $Expected.handoff_length -or
        -not $actual.evidence_root_absent -or
        -not $actual.permission_staging_request_root_absent -or
        -not $actual.permission_staging_publication_root_absent) {
        throw (New-P6Failure 'PRIOR_PUBLICATION6_PRECLAIM_MISMATCH' 'publication-6-preclaim' `
            'Publication-6 retired preclaim proof changed during Publication-7 execution.')
    }
    return $actual
}

function Get-PriorP5EvidenceProof {
    try {
        $priorRoot = Join-Path $env:LOCALAPPDATA ('SkillMesh\Evidence\GoalNP\TerraBootstrap\' + $PriorP5RequestId)
        $priorStatePath = Join-Path $priorRoot 'state.json'
        $priorApprovalPath = Join-Path $env:LOCALAPPDATA 'SkillMesh\Evidence\GoalNP\Publication5\approval1-message.txt'
        if (-not (Test-Path -LiteralPath $priorApprovalPath -PathType Leaf)) {
            throw 'The frozen Publication-5 approval file is absent.'
        }
        $approvalItem = Get-Item -LiteralPath $priorApprovalPath -Force -ErrorAction Stop
        if (($approvalItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'The frozen Publication-5 approval file is a reparse point.'
        }
        Assert-NoAlternateDataStream $approvalItem.FullName
        $approvalFileHash = Get-FileSha256 $approvalItem.FullName
        if ($approvalFileHash -cne $PriorP5ApprovalMessageFileHash) {
            throw 'The frozen Publication-5 approval file hash changed.'
        }
        if (-not (Test-Path -LiteralPath $priorStatePath -PathType Leaf)) {
            throw 'The frozen Publication-5 blocked state is absent.'
        }
        $stateHash = Get-FileSha256 $priorStatePath
        if ($stateHash -cne $PriorP5StateHash) { throw 'The frozen Publication-5 blocked state hash changed.' }
        $state = Get-Content -LiteralPath $priorStatePath -Raw | ConvertFrom-Json
        if ($state.schema_version -ne 1 -or $state.request_id -cne $PriorP5RequestId -or
            $state.phase -cne 'blocked' -or $state.approved_commit -cne $PriorP5ApprovedCommit -or
            $state.approval_message_sha256 -cne $PriorP5ApprovalMessageHash) {
            throw 'The frozen Publication-5 blocked state identity changed.'
        }
        $rootManifest = Get-OrdinalTreeManifest $priorRoot
        if (-not $rootManifest.exists -or $rootManifest.entry_count -ne $PriorP5RootEntryCount -or
            $rootManifest.sha256 -cne $PriorP5RootManifestHash) {
            throw 'The frozen Publication-5 blocked evidence root changed.'
        }
        return [ordered]@{
            request_id = $PriorP5RequestId
            approved_commit = $PriorP5ApprovedCommit
            approval_message_sha256 = $PriorP5ApprovalMessageHash
            approval_message_file_sha256 = $approvalFileHash
            state_sha256 = $stateHash
            root_manifest = $rootManifest
        }
    }
    catch {
        $metadata = Get-P6FailureMetadata $_.Exception
        if ($metadata.error_code -ceq 'PRIOR_PUBLICATION5_EVIDENCE_MISMATCH') { throw $_.Exception }
        throw (New-P6Failure 'PRIOR_PUBLICATION5_EVIDENCE_MISMATCH' 'publication-5-evidence' `
            $_.Exception.Message $_.Exception)
    }
}

function Assert-PriorP5EvidenceUnchanged([System.Collections.IDictionary]$Expected) {
    $actual = Get-PriorP5EvidenceProof
    if ($actual.approval_message_file_sha256 -cne $Expected.approval_message_file_sha256 -or
        $actual.state_sha256 -cne $Expected.state_sha256 -or
        -not (Test-ManifestEqual $actual.root_manifest $Expected.root_manifest)) {
        throw (New-P6Failure 'PRIOR_PUBLICATION5_EVIDENCE_MISMATCH' 'publication-5-evidence' `
            'Publication-5 blocked evidence changed during Publication-7 execution.')
    }
    return $actual
}

function Get-PriorP4EvidenceProof {
    try {
        $priorRoot = Join-Path $env:LOCALAPPDATA ('SkillMesh\Evidence\GoalNP\TerraBootstrap\' + $PriorP4RequestId)
        $priorStatePath = Join-Path $priorRoot 'state.json'
        $priorApprovalPath = Join-Path $env:LOCALAPPDATA 'SkillMesh\Evidence\GoalNP\Publication4\approval1-message.txt'
        if (-not (Test-Path -LiteralPath $priorApprovalPath -PathType Leaf)) {
            throw 'The frozen Publication-4 approval file is absent.'
        }
        $approvalItem = Get-Item -LiteralPath $priorApprovalPath -Force -ErrorAction Stop
        if (($approvalItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'The frozen Publication-4 approval file is a reparse point.'
        }
        Assert-NoAlternateDataStream $approvalItem.FullName
        $approvalFileHash = Get-FileSha256 $approvalItem.FullName
        if ($approvalFileHash -cne $PriorP4ApprovalMessageFileHash) {
            throw 'The frozen Publication-4 approval file hash changed.'
        }
        if (-not (Test-Path -LiteralPath $priorStatePath -PathType Leaf)) {
            throw 'The frozen Publication-4 blocked state is absent.'
        }
        $stateHash = Get-FileSha256 $priorStatePath
        if ($stateHash -cne $PriorP4StateHash) { throw 'The frozen Publication-4 blocked state hash changed.' }
        $state = Get-Content -LiteralPath $priorStatePath -Raw | ConvertFrom-Json
        if ($state.schema_version -ne 1 -or $state.request_id -cne $PriorP4RequestId -or
            $state.phase -cne 'blocked' -or $state.approved_commit -cne $PriorP4ApprovedCommit -or
            $state.approval_message_sha256 -cne $PriorP4ApprovalMessageHash) {
            throw 'The frozen Publication-4 blocked state identity changed.'
        }
        $rootManifest = Get-OrdinalTreeManifest $priorRoot
        if (-not $rootManifest.exists -or $rootManifest.entry_count -ne $PriorP4RootEntryCount -or
            $rootManifest.sha256 -cne $PriorP4RootManifestHash) {
            throw 'The frozen Publication-4 blocked evidence root changed.'
        }
        return [ordered]@{
            request_id = $PriorP4RequestId
            approved_commit = $PriorP4ApprovedCommit
            approval_message_sha256 = $PriorP4ApprovalMessageHash
            approval_message_file_sha256 = $approvalFileHash
            state_sha256 = $stateHash
            root_manifest = $rootManifest
        }
    }
    catch {
        $metadata = Get-P6FailureMetadata $_.Exception
        if ($metadata.error_code -ceq 'PRIOR_PUBLICATION4_EVIDENCE_MISMATCH') { throw $_.Exception }
        throw (New-P6Failure 'PRIOR_PUBLICATION4_EVIDENCE_MISMATCH' 'publication-4-evidence' `
            $_.Exception.Message $_.Exception)
    }
}

function Assert-PriorP4EvidenceUnchanged([System.Collections.IDictionary]$Expected) {
    $actual = Get-PriorP4EvidenceProof
    if ($actual.approval_message_file_sha256 -cne $Expected.approval_message_file_sha256 -or
        $actual.state_sha256 -cne $Expected.state_sha256 -or
        -not (Test-ManifestEqual $actual.root_manifest $Expected.root_manifest)) {
        throw (New-P6Failure 'PRIOR_PUBLICATION4_EVIDENCE_MISMATCH' 'publication-4-evidence' `
            'Publication-4 blocked evidence changed during Publication-7 execution.')
    }
    return $actual
}

function Get-PriorP3EvidenceProof {
    try {
        $priorRoot = Join-Path $env:LOCALAPPDATA ('SkillMesh\Evidence\GoalNP\TerraBootstrap\' + $PriorP3RequestId)
        $priorStatePath = Join-Path $priorRoot 'state.json'
        $priorApprovalPath = Join-Path $env:LOCALAPPDATA 'SkillMesh\Evidence\GoalNP\Publication3\approval1-message.txt'
        if (-not (Test-Path -LiteralPath $priorApprovalPath -PathType Leaf)) {
            throw 'The frozen Publication-3 approval file is absent.'
        }
        $approvalItem = Get-Item -LiteralPath $priorApprovalPath -Force -ErrorAction Stop
        if (($approvalItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'The frozen Publication-3 approval file is a reparse point.'
        }
        Assert-NoAlternateDataStream $approvalItem.FullName
        $approvalFileHash = Get-FileSha256 $approvalItem.FullName
        if ($approvalFileHash -cne $PriorP3ApprovalMessageFileHash) {
            throw 'The frozen Publication-3 approval file hash changed.'
        }
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
            approval_message_file_sha256 = $approvalFileHash
            state_sha256 = $stateHash
            root_manifest = $rootManifest
        }
    }
    catch {
        $metadata = Get-P6FailureMetadata $_.Exception
        if ($metadata.error_code -ceq 'PRIOR_PUBLICATION3_EVIDENCE_MISMATCH') { throw $_.Exception }
        throw (New-P6Failure 'PRIOR_PUBLICATION3_EVIDENCE_MISMATCH' 'publication-3-evidence' `
            $_.Exception.Message $_.Exception)
    }
}

function Assert-PriorP3EvidenceUnchanged([System.Collections.IDictionary]$Expected) {
    $actual = Get-PriorP3EvidenceProof
    if ($actual.approval_message_file_sha256 -cne $Expected.approval_message_file_sha256 -or
        $actual.state_sha256 -cne $Expected.state_sha256 -or
        -not (Test-ManifestEqual $actual.root_manifest $Expected.root_manifest)) {
        throw (New-P6Failure 'PRIOR_PUBLICATION3_EVIDENCE_MISMATCH' 'publication-3-evidence' `
            'Publication-3 blocked evidence changed during Publication-7 execution.')
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
        'skills.bundled.enabled=false',
        'skills.include_instructions=false',
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

function Get-ExpectedPermissionInstructionsText(
    [string]$Sandbox,
    [string]$OwnerRoot
) {
    $sandboxSentence = switch -CaseSensitive ($Sandbox) {
        'workspace-write' {
            'Filesystem sandboxing defines which files can be read or written. `sandbox_mode` is `workspace-write`: The sandbox permits reading files, and editing files in `cwd` and `writable_roots`. Editing files in other directories requires approval. Network access is restricted.'
        }
        'read-only' {
            'Filesystem sandboxing defines which files can be read or written. `sandbox_mode` is `read-only`: The sandbox only permits reading files. Network access is restricted.'
        }
        default { throw "Unsupported permission-instructions sandbox: $Sandbox" }
    }
    $permissionLines = @(
        '<permissions instructions>',
        $sandboxSentence,
        'Approval policy is currently never. Do not provide the `sandbox_permissions` for any reason, commands will be rejected.'
    )
    if ($Sandbox -ceq 'workspace-write') {
        if ([string]::IsNullOrWhiteSpace($OwnerRoot)) {
            throw 'Workspace-write permission instructions require the canonical owner root.'
        }
        $root = [System.IO.Path]::GetFullPath($OwnerRoot).TrimEnd('\')
        $permissionLines += (' The writable root is `' + $root + '`.')
    }
    $permissionLines += '</permissions instructions>'
    return $permissionLines -join "`n"
}

function Get-ExpectedEnvironmentContextText(
    [string]$Sandbox,
    [string]$OwnerRoot
) {
    $root = [System.IO.Path]::GetFullPath($OwnerRoot).TrimEnd('\')
    $writeEntries = if ($Sandbox -ceq 'workspace-write') {
        '<entry access="write"><path>' + $root + '</path></entry>' +
        '<entry access="write"><special>:slash_tmp</special></entry>' +
        '<entry access="write"><special>:tmpdir</special></entry>'
    }
    elseif ($Sandbox -ceq 'read-only') { '' }
    else { throw "Unsupported environment-context sandbox: $Sandbox" }
    $protectedReadEntries = if ($Sandbox -ceq 'workspace-write') {
        '<entry access="read"><path>' + (Join-Path $root '.git') + '</path></entry>' +
        '<entry access="read"><path>' + (Join-Path $root '.agents') + '</path></entry>' +
        '<entry access="read"><path>' + (Join-Path $root '.codex') + '</path></entry>'
    } else { '' }
    $filesystem = '<filesystem><workspace_roots><root>' + $root + '</root></workspace_roots>' +
        '<permission_profile type="managed"><file_system type="restricted">' +
        '<entry access="read"><special>:root</special></entry>' + $writeEntries +
        $protectedReadEntries + '</file_system></permission_profile></filesystem>'
    return @(
        '<environment_context>',
        ('  <cwd>' + $root + '</cwd>'),
        '  <shell>powershell</shell>',
        ('  <current_date>' + [DateTime]::Now.ToString('yyyy-MM-dd') + '</current_date>'),
        '  <timezone>America/Los_Angeles</timezone>',
        ('  ' + $filesystem),
        '</environment_context>'
    ) -join "`n"
}

function New-PermissionAttestationCanaryJson(
    [string]$Sandbox,
    [string]$Cwd,
    [string[]]$WorkspaceRoots,
    [string[]]$WritePaths,
    [string]$ProfileType = 'managed',
    [string]$FileSystemType = 'restricted',
    [int]$ProfileCount = 1,
    [string]$DiagnosticText = 'permission-parser-canary',
    [string]$PermissionExtraText = '',
    [string]$EnvironmentExtraText = '',
    [string]$ExtraAmbientText = '',
    [bool]$IncludeWritableRootAnnotation = $true,
    [string]$WritableRootAnnotation = ''
) {
    $rootTags = (($WorkspaceRoots | ForEach-Object { '<root>' + $_ + '</root>' }) -join '')
    $writeTags = (($WritePaths | ForEach-Object {
        '<entry access="write"><path>' + $_ + '</path></entry>'
    }) -join '')
    $specialWrites = if ($Sandbox -ceq 'workspace-write') {
        '<entry access="write"><special>:slash_tmp</special></entry>' +
        '<entry access="write"><special>:tmpdir</special></entry>'
    } else { '' }
    $protectedReads = if ($Sandbox -ceq 'workspace-write' -and $WorkspaceRoots.Count -ne 0) {
        '<entry access="read"><path>' + (Join-Path $WorkspaceRoots[0] '.git') + '</path></entry>' +
        '<entry access="read"><path>' + (Join-Path $WorkspaceRoots[0] '.agents') + '</path></entry>' +
        '<entry access="read"><path>' + (Join-Path $WorkspaceRoots[0] '.codex') + '</path></entry>'
    } else { '' }
    $permissionOwnerRoot = $null
    if ($Sandbox -ceq 'workspace-write') {
        if (-not [string]::IsNullOrWhiteSpace($WritableRootAnnotation)) {
            $permissionOwnerRoot = $WritableRootAnnotation
        }
        elseif (@($WorkspaceRoots).Count -ne 0) {
            $permissionOwnerRoot = $WorkspaceRoots[0]
        }
        else {
            throw 'Workspace-write canary generation requires a workspace root.'
        }
    }
    $permissions = Get-ExpectedPermissionInstructionsText $Sandbox $permissionOwnerRoot
    if ($Sandbox -ceq 'workspace-write' -and -not $IncludeWritableRootAnnotation) {
        $canonicalPermissionRoot = [System.IO.Path]::GetFullPath($permissionOwnerRoot).TrimEnd('\')
        $annotationLine = ' The writable root is `' + $canonicalPermissionRoot + '`.'
        $permissions = $permissions.Replace(("`n" + $annotationLine), '')
    }
    if (-not [string]::IsNullOrWhiteSpace($PermissionExtraText)) {
        $permissions = $permissions.Replace(
            "`n</permissions instructions>",
            ("`n" + $PermissionExtraText + "`n</permissions instructions>")
        )
    }
    $profileMarkup = ''
    for ($profileIndex = 0; $profileIndex -lt $ProfileCount; $profileIndex++) {
        $profileMarkup += '<permission_profile type="' + $ProfileType + '"><file_system type="' +
            $FileSystemType + '"><entry access="read"><special>:root</special></entry>' +
            $writeTags + $specialWrites + $protectedReads + '</file_system></permission_profile>'
    }
    $environment = @(
        '<environment_context>',
        ('  <cwd>' + $Cwd + '</cwd>'),
        '  <shell>powershell</shell>',
        ('  <current_date>' + [DateTime]::Now.ToString('yyyy-MM-dd') + '</current_date>'),
        '  <timezone>America/Los_Angeles</timezone>',
        ('  <filesystem><workspace_roots>' + $rootTags + '</workspace_roots>' +
            $profileMarkup + '</filesystem>'),
        '</environment_context>'
    ) -join "`n"
    if (-not [string]::IsNullOrWhiteSpace($EnvironmentExtraText)) {
        $environment = $environment.Replace(
            "`n</environment_context>",
            ("`n" + $EnvironmentExtraText + "`n</environment_context>")
        )
    }
    $developerContent = @([ordered]@{ type = 'input_text'; text = $permissions })
    if (-not [string]::IsNullOrWhiteSpace($ExtraAmbientText)) {
        $developerContent += [ordered]@{ type = 'input_text'; text = $ExtraAmbientText }
    }
    $items = @(
        [ordered]@{ type = 'message'; role = 'developer'; content = $developerContent },
        [ordered]@{
            type = 'message'
            role = 'user'
            content = @([ordered]@{ type = 'input_text'; text = $environment })
        },
        [ordered]@{
            type = 'message'
            role = 'user'
            content = @([ordered]@{ type = 'input_text'; text = $DiagnosticText })
        }
    )
    return ($items | ConvertTo-Json -Depth 6 -Compress)
}

function Assert-PermissionAttestationJson(
    [string]$JsonText,
    [ValidateSet('read-only', 'workspace-write')]
    [string]$ExpectedSandbox,
    [string]$ExpectedRoot,
    [string]$ExpectedDiagnosticText,
    [string]$Label
) {
    try {
        $root = [System.IO.Path]::GetFullPath($ExpectedRoot).TrimEnd('\')
        $payload = $JsonText | ConvertFrom-Json
        $items = @($payload)
        if ($items.Count -ne 3) { throw 'Prompt input must contain exactly three message items.' }
        $expectedRoles = @('developer', 'user', 'user')
        $expectedContentCounts = @(1, 1, 1)
        for ($itemIndex = 0; $itemIndex -lt 3; $itemIndex++) {
            $item = $items[$itemIndex]
            if (-not $item.PSObject.Properties['type'] -or [string]$item.type -cne 'message' -or
                -not $item.PSObject.Properties['role'] -or [string]$item.role -cne $expectedRoles[$itemIndex] -or
                -not $item.PSObject.Properties['content'] -or
                @($item.content).Count -ne $expectedContentCounts[$itemIndex]) {
                throw "Prompt input message shape is invalid at item $itemIndex."
            }
            foreach ($content in @($item.content)) {
                if (-not $content -or -not $content.PSObject.Properties['type'] -or
                    [string]$content.type -cne 'input_text' -or
                    -not $content.PSObject.Properties['text'] -or
                    [string]::IsNullOrWhiteSpace([string]$content.text)) {
                    throw "Prompt input contains non-text or empty content at item $itemIndex."
                }
            }
        }
        $permissionText = [string]$items[0].content[0].text
        $environmentText = [string]$items[1].content[0].text
        $diagnosticText = [string]$items[2].content[0].text
        if ($diagnosticText -cne $ExpectedDiagnosticText) {
            throw 'Prompt input diagnostic user text is not exact.'
        }
        $normalizedPermissionText = $permissionText.Replace("`r`n", "`n").Replace("`r", "`n").Trim()
        $expectedPermissionText = Get-ExpectedPermissionInstructionsText $ExpectedSandbox $root
        if ($normalizedPermissionText -cne $expectedPermissionText) {
            $expectedLines = @($expectedPermissionText -split "`n")
            $actualLines = @($normalizedPermissionText -split "`n")
            $firstDifferenceIndex = -1
            $expectedLinePresent = $false
            $actualLinePresent = $false
            $expectedLineHash = $null
            $actualLineHash = $null
            for ($lineIndex = 0; $lineIndex -lt [Math]::Max($expectedLines.Count, $actualLines.Count); $lineIndex++) {
                $expectedLinePresent = $lineIndex -lt $expectedLines.Count
                $actualLinePresent = $lineIndex -lt $actualLines.Count
                $expectedLine = if ($expectedLinePresent) { [string]$expectedLines[$lineIndex] } else { $null }
                $actualLine = if ($actualLinePresent) { [string]$actualLines[$lineIndex] } else { $null }
                if (-not $expectedLinePresent -or -not $actualLinePresent -or $expectedLine -cne $actualLine) {
                    $firstDifferenceIndex = $lineIndex
                    if ($expectedLinePresent) { $expectedLineHash = Get-Sha256Text $expectedLine }
                    if ($actualLinePresent) { $actualLineHash = Get-Sha256Text $actualLine }
                    break
                }
            }
            $mismatch = New-P6Failure 'PERMISSION_ATTESTATION_FAILED' $Label `
                'Permissions text differs from the complete closed permission grammar.'
            $mismatch.Data['permission_expected_sha256'] = Get-Sha256Text $expectedPermissionText
            $mismatch.Data['permission_actual_sha256'] = Get-Sha256Text $normalizedPermissionText
            $mismatch.Data['permission_expected_line_count'] = $expectedLines.Count
            $mismatch.Data['permission_actual_line_count'] = $actualLines.Count
            $mismatch.Data['permission_first_differing_line_number'] = $firstDifferenceIndex + 1
            $mismatch.Data['permission_expected_line_present'] = $expectedLinePresent
            $mismatch.Data['permission_actual_line_present'] = $actualLinePresent
            $mismatch.Data['permission_expected_line_sha256'] = $expectedLineHash
            $mismatch.Data['permission_actual_line_sha256'] = $actualLineHash
            throw $mismatch
        }
        if ([regex]::Matches($permissionText, '<permissions instructions>').Count -ne 1 -or
            [regex]::Matches($permissionText, '</permissions instructions>').Count -ne 1) {
            throw 'Permissions block tags are not singular and closed.'
        }
        $sandboxMatches = [regex]::Matches($permissionText, 'sandbox_mode` is `([^`]+)`')
        if ($sandboxMatches.Count -ne 1 -or
            $sandboxMatches[0].Groups[1].Value -cne $ExpectedSandbox) {
            throw "Effective sandbox is not exactly $ExpectedSandbox."
        }
        $approvalMatches = [regex]::Matches($permissionText, 'Approval policy is currently ([^.]+)\.')
        if ($approvalMatches.Count -ne 1 -or $approvalMatches[0].Groups[1].Value -cne 'never') {
            throw 'Effective approval policy is not exactly never.'
        }
        if ([regex]::Matches($permissionText, 'Approval policy is currently').Count -ne 1 -or
            [regex]::Matches($permissionText, 'Network access is').Count -ne 1 -or
            [regex]::Matches($permissionText, 'Network access is restricted\.').Count -ne 1) {
            throw 'Effective network policy is not exactly restricted.'
        }
        $writableRootAnnotationMatches = [regex]::Matches(
            $normalizedPermissionText,
            '(?m)^ The writable root is `([^`]+)`\.$'
        )
        $effectivePermissionWritableRoot = $null
        if ($ExpectedSandbox -ceq 'workspace-write') {
            if ($writableRootAnnotationMatches.Count -ne 1) {
                throw 'Workspace-write permissions do not expose one exact writable-root annotation.'
            }
            $effectivePermissionWritableRoot = [System.IO.Path]::GetFullPath(
                $writableRootAnnotationMatches[0].Groups[1].Value
            ).TrimEnd('\')
            if (-not $effectivePermissionWritableRoot.Equals($root, [StringComparison]::OrdinalIgnoreCase)) {
                throw 'Permission writable-root annotation is not the exact owner worktree.'
            }
        }
        elseif ($writableRootAnnotationMatches.Count -ne 0) {
            throw 'Read-only permissions unexpectedly expose a writable-root annotation.'
        }

        if ([regex]::Matches($environmentText, '<environment_context>').Count -ne 1 -or
            [regex]::Matches($environmentText, '</environment_context>').Count -ne 1) {
            throw 'Environment block tags are not singular and closed.'
        }
        $cwdMatches = [regex]::Matches($environmentText, '<cwd>([^<]+)</cwd>')
        if ($cwdMatches.Count -ne 1) { throw 'Prompt input does not expose exactly one cwd.' }
        $effectiveCwd = [System.IO.Path]::GetFullPath($cwdMatches[0].Groups[1].Value).TrimEnd('\')
        if (-not $effectiveCwd.Equals($root, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Effective cwd is not the exact owner worktree.'
        }
        $workspaceRootContainer = [regex]::Matches(
            $environmentText,
            '(?s)<workspace_roots>(.*?)</workspace_roots>'
        )
        if ($workspaceRootContainer.Count -ne 1) {
            throw 'Prompt input does not expose exactly one workspace-roots container.'
        }
        $workspaceRootMatches = [regex]::Matches(
            $workspaceRootContainer[0].Groups[1].Value,
            '<root>([^<]+)</root>'
        )
        if ($workspaceRootMatches.Count -ne 1) {
            throw 'Effective workspace roots are not the exact closed owner set.'
        }
        $effectiveWorkspaceRoot = [System.IO.Path]::GetFullPath(
            $workspaceRootMatches[0].Groups[1].Value
        ).TrimEnd('\')
        if (-not $effectiveWorkspaceRoot.Equals($root, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Effective workspace root is not the exact owner worktree.'
        }

        if ([regex]::Matches($environmentText, '<permission_profile\b').Count -ne 1 -or
            [regex]::Matches($environmentText, '</permission_profile>').Count -ne 1 -or
            [regex]::Matches($environmentText, '<file_system\b').Count -ne 1 -or
            [regex]::Matches($environmentText, '</file_system>').Count -ne 1) {
            throw 'Permission-profile and restricted-filesystem tags are not singular and closed.'
        }
        $allProfileMatches = [regex]::Matches(
            $environmentText,
            '(?s)<permission_profile\b[^>]*>.*?</permission_profile>'
        )
        $profileMatches = [regex]::Matches(
            $environmentText,
            '(?s)<permission_profile type="managed">(.*?)</permission_profile>'
        )
        if ($allProfileMatches.Count -ne 1 -or $profileMatches.Count -ne 1) {
            throw 'Prompt input does not expose exactly one managed permission profile.'
        }
        $profileText = $profileMatches[0].Value
        $allFileSystemMatches = [regex]::Matches($profileText, '(?s)<file_system\b[^>]*>.*?</file_system>')
        $restrictedFileSystemMatches = [regex]::Matches(
            $profileText,
            '(?s)<file_system type="restricted">(.*?)</file_system>'
        )
        if ($allFileSystemMatches.Count -ne 1 -or $restrictedFileSystemMatches.Count -ne 1) {
            throw 'Permission profile does not expose exactly one restricted filesystem.'
        }
        $restrictedFileSystemText = $restrictedFileSystemMatches[0].Value
        $writePathMatches = [regex]::Matches(
            $restrictedFileSystemText,
            '<entry access="write"><path>([^<]+)</path></entry>'
        )
        $writePaths = @($writePathMatches | ForEach-Object {
            [System.IO.Path]::GetFullPath($_.Groups[1].Value).TrimEnd('\')
        })
        $specialWriteMatches = [regex]::Matches(
            $restrictedFileSystemText,
            '<entry access="write"><special>([^<]+)</special></entry>'
        )
        $specialWrites = @($specialWriteMatches | ForEach-Object { $_.Groups[1].Value })
        $allWriteEntries = [regex]::Matches(
            $restrictedFileSystemText,
            '(?s)<entry\b[^>]*\baccess="write"[^>]*>.*?</entry>'
        )
        if ($allWriteEntries.Count -ne ($writePaths.Count + $specialWrites.Count)) {
            throw 'Restricted filesystem contains an unknown write-entry form.'
        }
        if ($ExpectedSandbox -ceq 'workspace-write') {
            if ($writePaths.Count -ne 1 -or
                -not $writePaths[0].Equals($root, [StringComparison]::OrdinalIgnoreCase)) {
                throw 'Effective filesystem write paths are not the exact owner worktree.'
            }
            if ($specialWrites.Count -ne 2 -or $specialWrites[0] -cne ':slash_tmp' -or
                $specialWrites[1] -cne ':tmpdir') {
                throw 'Effective special write paths are not the closed Codex temporary set.'
            }
        }
        elseif ($writePaths.Count -ne 0 -or $specialWrites.Count -ne 0) {
            throw 'Read-only permission profile exposes a write entry.'
        }
        $normalizedEnvironmentText = $environmentText.Replace("`r`n", "`n").Replace("`r", "`n").Trim()
        if ($normalizedEnvironmentText -cne (Get-ExpectedEnvironmentContextText $ExpectedSandbox $root)) {
            throw 'Environment text differs from the complete closed environment grammar.'
        }

        $allClosedTexts = @($permissionText, $environmentText, $diagnosticText)
        foreach ($forbidden in @(
            'AGENTS.md instructions for', 'GitHub Copilot workspace adapter', '.agents/skills/',
            '.agents\skills\', '.github/skills/', '.github\skills\', '<apps_instructions>',
            '<plugins_instructions>', '<recommended_plugins>', '<skills_instructions>',
            '</skills_instructions>', '/skills/.system/', '\skills\.system\'
        )) {
            foreach ($text in $allClosedTexts) {
                if ($text.IndexOf($forbidden, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
                    throw "Prompt input contains forbidden ambient input: $forbidden"
                }
            }
        }
        foreach ($text in $allClosedTexts) {
            if ([regex]::Matches($text, '\(file:\s*[^\)]+\)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase).Count -ne 0) {
                throw 'Prompt input exposes a forbidden skill or file locator.'
            }
        }
        return [ordered]@{
            effective_sandbox = $ExpectedSandbox
            effective_approval_policy = 'never'
            effective_network_policy = 'restricted'
            effective_cwd = $effectiveCwd
            permission_writable_root = $effectivePermissionWritableRoot
            workspace_roots = @($effectiveWorkspaceRoot)
            filesystem_write_paths = $writePaths
            special_write_paths = $specialWrites
            system_skill_instruction_block_count = 0
            system_skill_locator_count = 0
        }
    }
    catch {
        $metadata = Get-P6FailureMetadata $_.Exception
        if ($metadata.error_code -ceq 'PERMISSION_ATTESTATION_FAILED') { throw $_.Exception }
        throw (New-P6Failure 'PERMISSION_ATTESTATION_FAILED' $Label $_.Exception.Message $_.Exception)
    }
}

function Invoke-PermissionParserCanary([string]$OwnerRoot) {
    $root = [System.IO.Path]::GetFullPath($OwnerRoot).TrimEnd('\')
    $acceptedJson = New-PermissionAttestationCanaryJson 'workspace-write' $root @($root) @($root) `
        'managed' 'restricted' 1 'permission-parser-canary'
    $accepted = Assert-PermissionAttestationJson $acceptedJson 'workspace-write' $root `
        'permission-parser-canary' 'permission-parser-canary-accept'
    $rejectCases = @(
        [ordered]@{
            name = 'read-only'
            json = New-PermissionAttestationCanaryJson 'read-only' $root @($root) @() `
                'managed' 'restricted' 1 'permission-parser-canary'
        },
        [ordered]@{
            name = 'wrong-cwd'
            json = New-PermissionAttestationCanaryJson 'workspace-write' ($root + '\wrong') @($root) @($root) `
                'managed' 'restricted' 1 'permission-parser-canary'
        },
        [ordered]@{
            name = 'missing-writable-root-annotation'
            json = New-PermissionAttestationCanaryJson -Sandbox 'workspace-write' -Cwd $root `
                -WorkspaceRoots @($root) -WritePaths @($root) -DiagnosticText 'permission-parser-canary' `
                -IncludeWritableRootAnnotation $false
        },
        [ordered]@{
            name = 'wrong-writable-root-annotation'
            json = New-PermissionAttestationCanaryJson -Sandbox 'workspace-write' -Cwd $root `
                -WorkspaceRoots @($root) -WritePaths @($root) -DiagnosticText 'permission-parser-canary' `
                -WritableRootAnnotation ($root + '\wrong')
        },
        [ordered]@{
            name = 'missing-write-path'
            json = New-PermissionAttestationCanaryJson 'workspace-write' $root @($root) @() `
                'managed' 'restricted' 1 'permission-parser-canary'
        },
        [ordered]@{
            name = 'extra-write-path'
            json = New-PermissionAttestationCanaryJson 'workspace-write' $root @($root) @($root, ($root + '\extra')) `
                'managed' 'restricted' 1 'permission-parser-canary'
        },
        [ordered]@{
            name = 'unmanaged-profile'
            json = New-PermissionAttestationCanaryJson 'workspace-write' $root @($root) @($root) `
                'unmanaged' 'restricted' 1 'permission-parser-canary'
        },
        [ordered]@{
            name = 'unrestricted-filesystem'
            json = New-PermissionAttestationCanaryJson 'workspace-write' $root @($root) @($root) `
                'managed' 'unrestricted' 1 'permission-parser-canary'
        },
        [ordered]@{
            name = 'duplicate-profile'
            json = New-PermissionAttestationCanaryJson 'workspace-write' $root @($root) @($root) `
                'managed' 'restricted' 2 'permission-parser-canary'
        },
        [ordered]@{
            name = 'extra-ambient-content'
            json = New-PermissionAttestationCanaryJson 'workspace-write' $root @($root) @($root) `
                'managed' 'restricted' 1 'permission-parser-canary' '' '' '<memory>unexpected</memory>'
        },
        [ordered]@{
            name = 'permission-embedded-text'
            json = New-PermissionAttestationCanaryJson 'workspace-write' $root @($root) @($root) `
                'managed' 'restricted' 1 'permission-parser-canary' '<memory>unexpected</memory>'
        },
        [ordered]@{
            name = 'environment-embedded-text'
            json = New-PermissionAttestationCanaryJson 'workspace-write' $root @($root) @($root) `
                'managed' 'restricted' 1 'permission-parser-canary' '' '<memory>unexpected</memory>'
        },
        [ordered]@{
            name = 'system-skills-block'
            json = New-PermissionAttestationCanaryJson 'workspace-write' $root @($root) @($root) `
                'managed' 'restricted' 1 'permission-parser-canary' `
                '<skills_instructions>unexpected</skills_instructions>'
        },
        [ordered]@{
            name = 'system-skill-locator'
            json = New-PermissionAttestationCanaryJson 'workspace-write' $root @($root) @($root) `
                'managed' 'restricted' 1 'permission-parser-canary' `
                '(file: C:/canary/skills/.system/sample/SKILL.md)'
        }
    )
    $rejected = New-Object System.Collections.Generic.List[string]
    foreach ($case in $rejectCases) {
        $didReject = $false
        try {
            $null = Assert-PermissionAttestationJson $case.json 'workspace-write' $root `
                'permission-parser-canary' ('permission-parser-canary-' + $case.name)
        }
        catch {
            $metadata = Get-P6FailureMetadata $_.Exception
            if ($metadata.error_code -cne 'PERMISSION_ATTESTATION_FAILED') { throw $_.Exception }
            $didReject = $true
        }
        if (-not $didReject) {
            throw (New-P6Failure 'PERMISSION_ATTESTATION_FAILED' 'permission-parser-canary' `
                ('Parser canary accepted forbidden case: ' + $case.name))
        }
        $rejected.Add($case.name)
    }
    return [ordered]@{
        accepted_case_count = 1
        rejected_case_count = $rejected.Count
        rejected_cases = $rejected.ToArray()
        accepted_permission_writable_root = $accepted.permission_writable_root
        system_skill_surface_absent = ($accepted.system_skill_instruction_block_count -eq 0 -and
            $accepted.system_skill_locator_count -eq 0)
    }
}

function Assert-PermissionStagingDirectory([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if (-not $item.PSIsContainer -or
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Permission-staging directory identity is invalid: $Path"
    }
    Assert-NoAlternateDataStream $item.FullName
    return $item.FullName.TrimEnd('\')
}

function New-PermissionStagingLayout {
    $localAppData = [System.IO.Path]::GetFullPath($env:LOCALAPPDATA).TrimEnd('\')
    $skillMeshRoot = Join-Path $localAppData 'SkillMesh'
    if (-not (Test-Path -LiteralPath $skillMeshRoot -PathType Container)) {
        throw 'The SkillMesh local application-data root is absent.'
    }
    $null = Assert-PermissionStagingDirectory $skillMeshRoot
    $stagingRoot = Join-Path $skillMeshRoot 'Staging'
    $goalRoot = Join-Path $stagingRoot 'GoalNP'
    $publicationRoot = Join-Path $goalRoot 'Publication7'
    $requestRoot = Join-Path $publicationRoot $script:RequestId
    $attestationRoot = Join-Path $requestRoot 'permission-attestation'
    $codexHome = Join-Path $attestationRoot 'codex-home'
    $outputRoot = Join-Path $attestationRoot 'output'
    $tempRoot = Join-Path $attestationRoot 'temp'
    $createdParents = New-Object System.Collections.Generic.List[string]
    $layout = [ordered]@{
        staging_root = [System.IO.Path]::GetFullPath($stagingRoot).TrimEnd('\')
        request_root = [System.IO.Path]::GetFullPath($requestRoot).TrimEnd('\')
        attestation_root = [System.IO.Path]::GetFullPath($attestationRoot).TrimEnd('\')
        codex_home = [System.IO.Path]::GetFullPath($codexHome).TrimEnd('\')
        output_root = [System.IO.Path]::GetFullPath($outputRoot).TrimEnd('\')
        temp_root = [System.IO.Path]::GetFullPath($tempRoot).TrimEnd('\')
        created_parents = @()
        request_root_owned = $false
    }
    try {
        foreach ($directory in @($stagingRoot, $goalRoot, $publicationRoot)) {
            if (Test-Path -LiteralPath $directory) {
                $null = Assert-PermissionStagingDirectory $directory
            }
            else {
                New-Item -ItemType Directory -Path $directory | Out-Null
                $createdParents.Add([System.IO.Path]::GetFullPath($directory).TrimEnd('\'))
                $layout.created_parents = $createdParents.ToArray()
                $null = Assert-PermissionStagingDirectory $directory
            }
        }
        if (Test-Path -LiteralPath $requestRoot) {
            throw (New-P6Failure 'PERMISSION_STAGING_COLLISION' 'permission-staging' `
                'The deterministic Publication-7 permission-staging request path already exists; no cleanup was attempted.')
        }
        New-Item -ItemType Directory -Path $requestRoot | Out-Null
        $layout.request_root_owned = $true
        $null = Assert-PermissionStagingDirectory $requestRoot
        foreach ($directory in @($attestationRoot, $codexHome, $outputRoot, $tempRoot)) {
            New-Item -ItemType Directory -Path $directory | Out-Null
            $null = Assert-PermissionStagingDirectory $directory
        }
        return $layout
    }
    catch {
        $creationFailure = $_.Exception
        if ($layout.request_root_owned -or @($layout.created_parents).Count -ne 0) {
            try { Remove-PermissionStagingLayout $layout }
            catch { throw $_.Exception }
        }
        throw $creationFailure
    }
}

function Remove-PermissionStagingLayout([System.Collections.IDictionary]$Layout) {
    try {
        $localAppData = [System.IO.Path]::GetFullPath($env:LOCALAPPDATA).TrimEnd('\')
        $expectedStagingRoot = Join-Path $localAppData 'SkillMesh\Staging'
        $expectedRequestRoot = Join-Path $expectedStagingRoot ('GoalNP\Publication7\' + $script:RequestId)
        $stagingRoot = [System.IO.Path]::GetFullPath([string]$Layout.staging_root).TrimEnd('\')
        $requestRoot = [System.IO.Path]::GetFullPath([string]$Layout.request_root).TrimEnd('\')
        if (-not $stagingRoot.Equals($expectedStagingRoot, [StringComparison]::OrdinalIgnoreCase) -or
            -not $requestRoot.Equals($expectedRequestRoot, [StringComparison]::OrdinalIgnoreCase) -or
            -not $requestRoot.StartsWith($stagingRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Refusing to remove a permission-staging path outside the exact Publication-7 request root.'
        }
        $unownedRequestRoot = $false
        if ((Test-Path -LiteralPath $requestRoot) -and [bool]$Layout.request_root_owned) {
            $null = Get-OrdinalTreeManifest $requestRoot
            Remove-Item -LiteralPath $requestRoot -Recurse -Force
            if (Test-Path -LiteralPath $requestRoot) { throw 'Permission-staging request cleanup was incomplete.' }
        }
        elseif (Test-Path -LiteralPath $requestRoot) {
            $unownedRequestRoot = $true
        }
        $allowedParents = @(
            (Join-Path $expectedStagingRoot 'GoalNP\Publication7'),
            (Join-Path $expectedStagingRoot 'GoalNP'),
            $expectedStagingRoot
        )
        $createdParents = @($Layout.created_parents)
        [Array]::Reverse($createdParents)
        foreach ($parent in $createdParents) {
            $resolvedParent = [System.IO.Path]::GetFullPath([string]$parent).TrimEnd('\')
            $isAllowed = @($allowedParents | Where-Object {
                $resolvedParent.Equals($_, [StringComparison]::OrdinalIgnoreCase)
            }).Count -eq 1
            if (-not $isAllowed) { throw "Refusing to remove unexpected staging parent: $resolvedParent" }
            if (Test-Path -LiteralPath $resolvedParent) {
                $null = Assert-PermissionStagingDirectory $resolvedParent
                if (@(Get-ChildItem -LiteralPath $resolvedParent -Force -ErrorAction Stop).Count -ne 0) {
                    if ($unownedRequestRoot) { continue }
                    throw "Created permission-staging parent is not empty: $resolvedParent"
                }
                Remove-Item -LiteralPath $resolvedParent -Force
            }
        }
    }
    catch {
        $metadata = Get-P6FailureMetadata $_.Exception
        if ($metadata.error_code -ceq 'PERMISSION_STAGING_CLEANUP_FAILED') { throw $_.Exception }
        throw (New-P6Failure 'PERMISSION_STAGING_CLEANUP_FAILED' 'permission-staging-cleanup' `
            $_.Exception.Message $_.Exception)
    }
}

function Invoke-PreclaimPermissionAttestation(
    [string]$CodexExe,
    [string]$LiveAuthPath,
    [string]$LiveAuthSha256,
    [string]$LiveCodexHome,
    [System.Collections.IDictionary]$ExpectedLiveCodexHomeManifest,
    [bool]$RetainStaging
) {
    $layout = $null
    $originalCodexHome = [Environment]::GetEnvironmentVariable('CODEX_HOME', 'Process')
    $originalTemp = [Environment]::GetEnvironmentVariable('TEMP', 'Process')
    $originalTmp = [Environment]::GetEnvironmentVariable('TMP', 'Process')
    $failure = $null
    $cleanupFailure = $null
    $result = $null
    $liveBefore = Get-CodexHomeManifest $LiveCodexHome
    if (-not (Test-ManifestEqual $ExpectedLiveCodexHomeManifest $liveBefore)) {
        throw (New-P6Failure 'PERMISSION_ATTESTATION_FAILED' 'preclaim-live-home' `
            'The live CODEX_HOME changed before permission attestation.')
    }
    $priorP6Before = Get-PriorP6PreclaimProof
    $priorP5Before = Get-PriorP5EvidenceProof
    $priorP4Before = Get-PriorP4EvidenceProof
    $priorP3Before = Get-PriorP3EvidenceProof
    $liveAfter = $null
    $priorP6After = $null
    $priorP5After = $null
    $priorP4After = $null
    $priorP3After = $null
    try {
        $layout = New-PermissionStagingLayout
        $scratchAuthPath = Join-Path $layout.codex_home 'auth.json'
        Copy-Item -LiteralPath $LiveAuthPath -Destination $scratchAuthPath
        $scratchAuthItem = Get-Item -LiteralPath $scratchAuthPath -Force -ErrorAction Stop
        if (($scratchAuthItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Permission-staging Codex authentication copy is a reparse point.'
        }
        Assert-NoAlternateDataStream $scratchAuthItem.FullName
        if ((Get-FileSha256 $scratchAuthPath) -cne $LiveAuthSha256) {
            throw 'Permission-staging Codex authentication copy mismatch.'
        }
        $env:CODEX_HOME = $layout.codex_home
        $env:TEMP = $layout.temp_root
        $env:TMP = $layout.temp_root
        $arguments = @('--model', 'gpt-5.6-terra') + @(Get-ClosedConfigArguments) + @(
            '--sandbox', 'workspace-write', '--cd', $script:RepoRoot,
            'debug', 'prompt-input', 'Goal-NP-Publication-7-preclaim-permission-attestation'
        )
        $process = Invoke-RecordedProcess 'preclaim-permission' $CodexExe $arguments $layout.output_root 120000
        if ((Get-Item -LiteralPath $process.stderr_path -Force).Length -ne 0) {
            throw 'Pinned Codex permission diagnostic wrote stderr.'
        }
        $jsonText = (Get-Content -LiteralPath $process.stdout_path -Raw).Trim()
        $effective = Assert-PermissionAttestationJson $jsonText 'workspace-write' $script:RepoRoot `
            'Goal-NP-Publication-7-preclaim-permission-attestation' 'preclaim-permission-attestation'
        $result = [ordered]@{
            diagnostic = 'codex debug prompt-input'
            diagnostic_status = 'supported'
            debug_strict_config_supported = $false
            requested_sandbox = 'workspace-write'
            requested_cwd = $script:RepoRoot
            requested_additional_writable_directory_count = 0
            requested_temp_root = $layout.temp_root
            argv_sha256 = Get-Sha256Text (($arguments | ConvertTo-Json -Compress) + "`n")
            stdout_path = $process.stdout_path
            stdout_sha256 = $process.stdout_sha256
            stderr_path = $process.stderr_path
            stderr_sha256 = $process.stderr_sha256
            scratch_manifest_before_cleanup = Get-OrdinalTreeManifest $layout.request_root
            effective = $effective
            effective_projection_sha256 = Get-Sha256Text (($effective | ConvertTo-Json -Depth 6 -Compress) + "`n")
            layout = $layout
            scratch_retained_for_run = $RetainStaging
        }
    }
    catch {
        $failure = $_.Exception
    }
    finally {
        if ($null -eq $originalCodexHome) { Remove-Item Env:CODEX_HOME -ErrorAction SilentlyContinue }
        else { $env:CODEX_HOME = $originalCodexHome }
        if ($null -eq $originalTemp) { Remove-Item Env:TEMP -ErrorAction SilentlyContinue }
        else { $env:TEMP = $originalTemp }
        if ($null -eq $originalTmp) { Remove-Item Env:TMP -ErrorAction SilentlyContinue }
        else { $env:TMP = $originalTmp }
        try {
            $liveAfter = Get-CodexHomeManifest $LiveCodexHome
            if (-not (Test-ManifestEqual $ExpectedLiveCodexHomeManifest $liveAfter)) {
                throw 'The live CODEX_HOME changed during permission attestation.'
            }
            $priorP6After = Assert-PriorP6PreclaimUnchanged $priorP6Before
            $priorP5After = Assert-PriorP5EvidenceUnchanged $priorP5Before
            $priorP4After = Assert-PriorP4EvidenceUnchanged $priorP4Before
            $priorP3After = Assert-PriorP3EvidenceUnchanged $priorP3Before
        }
        catch {
            $boundaryMetadata = Get-P6FailureMetadata $_.Exception
            if ($boundaryMetadata.error_code -in @(
                'PRIOR_PUBLICATION6_PRECLAIM_MISMATCH',
                'PRIOR_PUBLICATION5_EVIDENCE_MISMATCH',
                'PRIOR_PUBLICATION4_EVIDENCE_MISMATCH',
                'PRIOR_PUBLICATION3_EVIDENCE_MISMATCH'
            )) {
                $failure = $_.Exception
            }
            else {
                $failure = New-P6Failure 'PERMISSION_ATTESTATION_FAILED' 'preclaim-protected-boundary' `
                    $_.Exception.Message $_.Exception
            }
        }
        if ($layout -and ((-not $RetainStaging) -or $failure)) {
            try { Remove-PermissionStagingLayout $layout }
            catch { $cleanupFailure = $_.Exception }
        }
    }
    if ($cleanupFailure) { throw $cleanupFailure }
    if ($failure) {
        $metadata = Get-P6FailureMetadata $failure
        if ($metadata.error_code -in @(
            'PERMISSION_ATTESTATION_FAILED', 'PERMISSION_STAGING_COLLISION',
            'PERMISSION_STAGING_CLEANUP_FAILED', 'PRIOR_PUBLICATION6_PRECLAIM_MISMATCH',
            'PRIOR_PUBLICATION5_EVIDENCE_MISMATCH', 'PRIOR_PUBLICATION4_EVIDENCE_MISMATCH',
            'PRIOR_PUBLICATION3_EVIDENCE_MISMATCH'
        )) { throw $failure }
        throw (New-P6Failure 'PERMISSION_ATTESTATION_FAILED' 'preclaim-permission-attestation' `
            $failure.Message $failure)
    }
    if (-not $RetainStaging) {
        $result['scratch_removed'] = $true
        $result['stdout_path'] = $null
        $result['stderr_path'] = $null
        $result['layout'] = $null
    }
    else {
        $result['scratch_removed'] = $false
    }
    $result['live_codex_home_before'] = $liveBefore
    $result['live_codex_home_after'] = $liveAfter
    $result['prior_publication6_before'] = $priorP6Before
    $result['prior_publication6_after'] = $priorP6After
    $result['prior_publication5_before'] = $priorP5Before
    $result['prior_publication5_after'] = $priorP5After
    $result['prior_publication4_before'] = $priorP4Before
    $result['prior_publication4_after'] = $priorP4After
    $result['prior_publication3_before'] = $priorP3Before
    $result['prior_publication3_after'] = $priorP3After
    return $result
}

function Get-CapturedProcessExitCode(
    [System.Diagnostics.Process]$Process,
    [string]$Label
) {
    try {
        if (-not $Process.HasExited) {
            throw (New-P6Failure 'PROCESS_EXIT_CODE_UNAVAILABLE' $Label `
                'The process had not exited before exit-code capture.')
        }
        $rawExitCode = $Process.ExitCode
    }
    catch {
        $metadata = Get-P6FailureMetadata $_.Exception
        if ($metadata.error_code -eq 'PROCESS_EXIT_CODE_UNAVAILABLE') { throw $_.Exception }
        throw (New-P6Failure 'PROCESS_EXIT_CODE_UNAVAILABLE' $Label `
            'The process exit-code getter failed after the process wait completed.' $_.Exception)
    }
    if ($null -eq $rawExitCode) {
        throw (New-P6Failure 'PROCESS_EXIT_CODE_UNAVAILABLE' $Label `
            'The process returned a null exit code after its handle was cached and it exited.')
    }
    if ($rawExitCode -isnot [int]) {
        throw (New-P6Failure 'PROCESS_EXIT_CODE_UNAVAILABLE' $Label `
            ('The process returned a non-Int32 exit code: ' + $rawExitCode.GetType().FullName))
    }
    $exitCode = [int]$rawExitCode
    return $exitCode
}

function Wait-CapturedProcessExitCode(
    [System.Diagnostics.Process]$Process,
    [string]$Label,
    [int]$TimeoutMilliseconds
) {
    $timedOut = $false
    try {
        if (-not $Process.WaitForExit($TimeoutMilliseconds)) {
            $timedOut = $true
            $Process.Kill()
        }
        $Process.WaitForExit()
    }
    catch {
        $metadata = Get-P6FailureMetadata $_.Exception
        if ($metadata.error_code -ne 'UNEXPECTED_FAILURE') { throw $_.Exception }
        throw (New-P6Failure 'UNEXPECTED_FAILURE' $Label `
            'Process wait or timeout cleanup failed.' $_.Exception)
    }
    $exitCode = Get-CapturedProcessExitCode $Process $Label
    if ($timedOut) {
        throw (New-P6Failure 'PROCESS_TIMEOUT' $Label `
            "The process exceeded its $TimeoutMilliseconds-millisecond limit.")
    }
    return $exitCode
}

function Invoke-ProcessExitCanaryCase(
    [string]$CmdExe,
    [int]$ExpectedExitCode
) {
    $label = 'process-canary-exit-' + $ExpectedExitCode
    $process = $null
    try {
        try {
            $process = Start-Process -FilePath $CmdExe -ArgumentList @(
                '/d', '/s', '/c', ('"exit ' + $ExpectedExitCode + '"')
            ) -NoNewWindow -PassThru
            $rawHandle = $process.Handle
        }
        catch {
            if ($null -eq $process) {
                throw (New-P6Failure 'PROCESS_START_FAILED' $label 'The process could not be started.' $_.Exception)
            }
            throw (New-P6Failure 'PROCESS_HANDLE_UNAVAILABLE' $label `
                'The process handle could not be acquired immediately after start.' $_.Exception)
        }
        if ($null -eq $rawHandle -or $rawHandle -isnot [IntPtr] -or $rawHandle -eq [IntPtr]::Zero) {
            throw (New-P6Failure 'PROCESS_HANDLE_UNAVAILABLE' $label `
                'The process returned an invalid handle immediately after start.')
        }
        $cachedHandle = [IntPtr]$rawHandle
        $exitCode = Wait-CapturedProcessExitCode $process $label 30000
        if ($exitCode -ne $ExpectedExitCode) {
            throw (New-P6Failure 'PROCESS_CANARY_FAILED' $label `
                "The process-exit canary expected $ExpectedExitCode and observed $exitCode.")
        }
        return [ordered]@{
            expected_exit_code = $ExpectedExitCode
            observed_exit_code = $exitCode
        }
    }
    catch {
        $originalFailure = $_.Exception
        if ($process) {
            try {
                if (-not $process.HasExited) {
                    $process.Kill()
                    $process.WaitForExit()
                }
            }
            catch {
                throw (New-P6Failure 'UNEXPECTED_FAILURE' $label `
                    'Process-exit canary cleanup failed.' $_.Exception)
            }
        }
        throw $originalFailure
    }
    finally {
        if ($process) { $process.Dispose() }
    }
}

function Invoke-ProcessExitCanary {
    try {
        $systemDirectory = [Environment]::SystemDirectory
        if ([string]::IsNullOrWhiteSpace($systemDirectory) -or
            -not [System.IO.Path]::IsPathRooted($systemDirectory)) {
            throw (New-P6Failure 'PROCESS_CANARY_FAILED' 'process-exit-canary' `
                'The canonical Windows system directory is unavailable.')
        }
        $cmdExe = Join-Path ([System.IO.Path]::GetFullPath($systemDirectory).TrimEnd('\')) 'cmd.exe'
        if (-not (Test-Path -LiteralPath $cmdExe -PathType Leaf)) {
            throw (New-P6Failure 'PROCESS_CANARY_FAILED' 'process-exit-canary' `
                'The canonical System32 cmd.exe is unavailable.')
        }
        $cmdItem = Get-Item -LiteralPath $cmdExe -Force -ErrorAction Stop
        if (($cmdItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            -not $cmdItem.FullName.Equals($cmdExe, [StringComparison]::OrdinalIgnoreCase)) {
            throw (New-P6Failure 'PROCESS_CANARY_FAILED' 'process-exit-canary' `
                'The canonical System32 cmd.exe identity is invalid.')
        }
        Assert-NoAlternateDataStream $cmdItem.FullName
        $cmdHash = Get-FileSha256 $cmdItem.FullName
        $cases = @(
            Invoke-ProcessExitCanaryCase $cmdExe 0
            Invoke-ProcessExitCanaryCase $cmdExe 37
        )
        return [ordered]@{
            executable = $cmdItem.FullName
            executable_sha256 = $cmdHash
            cases = $cases
        }
    }
    catch {
        $metadata = Get-P6FailureMetadata $_.Exception
        if ($metadata.error_code -eq 'PROCESS_CANARY_FAILED') { throw $_.Exception }
        $failureLabel = if ($metadata.error_label -eq 'launcher') { 'process-exit-canary' } else { $metadata.error_label }
        throw (New-P6Failure 'PROCESS_CANARY_FAILED' $failureLabel `
            'The Windows PowerShell 5.1 process-exit canary failed.' $_.Exception $metadata.error_code)
    }
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
    $process = $null
    try {
        try {
            $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -NoNewWindow -PassThru `
                -RedirectStandardOutput $stdout -RedirectStandardError $stderr
            $rawHandle = $process.Handle
        }
        catch {
            if ($null -eq $process) {
                throw (New-P6Failure 'PROCESS_START_FAILED' $Label 'The process could not be started.' $_.Exception)
            }
            throw (New-P6Failure 'PROCESS_HANDLE_UNAVAILABLE' $Label `
                'The process handle could not be acquired immediately after start.' $_.Exception)
        }
        if ($null -eq $rawHandle -or $rawHandle -isnot [IntPtr] -or $rawHandle -eq [IntPtr]::Zero) {
            throw (New-P6Failure 'PROCESS_HANDLE_UNAVAILABLE' $Label `
                'The process returned an invalid handle immediately after start.')
        }
        $cachedHandle = [IntPtr]$rawHandle
        $exitCode = Wait-CapturedProcessExitCode $process $Label $TimeoutMilliseconds
        if ($exitCode -ne 0) {
            throw (New-P6Failure 'PROCESS_EXIT_NONZERO' $Label "The process exited $exitCode.")
        }
        return [ordered]@{
            exit_code = $exitCode
            stdout_path = $stdout
            stdout_sha256 = Get-FileSha256 $stdout
            stderr_path = $stderr
            stderr_sha256 = Get-FileSha256 $stderr
        }
    }
    catch {
        $originalFailure = $_.Exception
        if ($process) {
            try {
                if (-not $process.HasExited) {
                    $process.Kill()
                    $process.WaitForExit()
                }
            }
            catch {
                throw (New-P6Failure 'UNEXPECTED_FAILURE' $Label `
                    'Process failure cleanup failed.' $_.Exception)
            }
        }
        throw $originalFailure
    }
    finally {
        if ($process) { $process.Dispose() }
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
    if (-not $script:PermissionStagingLayout) { return }
    Remove-PermissionStagingLayout $script:PermissionStagingLayout
    $script:DisposableCodexHome = $null
    $script:PermissionStagingLayout = $null
}

function Get-PromptInputProof([string]$Label, [string]$Sandbox) {
    $quiescenceBefore = Get-QuiescenceProof
    $diagnosticText = 'Goal-NP-Publication-7-' + $Label + '-prompt-surface-proof'
    $arguments = @('--model', 'gpt-5.6-terra') + @(Get-ClosedConfigArguments) + @(
        '--sandbox', $Sandbox, '--cd', $script:RepoRoot,
        'debug', 'prompt-input', $diagnosticText
    )
    $proof = $null
    $liveCodexHomeBefore = Assert-LiveCodexHomeUnchanged $script:LiveCodexHomeBefore `
        ($Label + '-before-prompt-input')
    $priorP6Before = Assert-PriorP6PreclaimUnchanged $script:PriorP6Before
    $priorP5Before = Assert-PriorP5EvidenceUnchanged $script:PriorP5Before
    $priorP4Before = Assert-PriorP4EvidenceUnchanged $script:PriorP4Before
    $priorP3Before = Assert-PriorP3EvidenceUnchanged $script:PriorP3Before
    try {
        $proof = Invoke-RecordedProcess ($Label + '-prompt-input') $script:CodexExe $arguments $script:EvidenceRoot 120000
    }
    finally {
        $quiescenceAfter = Get-QuiescenceProof
        $liveCodexHomeAfter = Assert-LiveCodexHomeUnchanged $script:LiveCodexHomeBefore `
            ($Label + '-after-prompt-input')
        $priorP6After = Assert-PriorP6PreclaimUnchanged $script:PriorP6Before
        $priorP5After = Assert-PriorP5EvidenceUnchanged $script:PriorP5Before
        $priorP4After = Assert-PriorP4EvidenceUnchanged $script:PriorP4Before
        $priorP3After = Assert-PriorP3EvidenceUnchanged $script:PriorP3Before
    }
    if ((Get-Item -LiteralPath $proof.stderr_path -Force).Length -ne 0) {
        throw (New-P6Failure 'PERMISSION_ATTESTATION_FAILED' ($Label + '-prompt-input') `
            'Pinned Codex prompt-input proof wrote stderr.')
    }
    $text = (Get-Content -LiteralPath $proof.stdout_path -Raw).Trim()
    $effective = Assert-PermissionAttestationJson $text $Sandbox $script:RepoRoot `
        $diagnosticText ($Label + '-prompt-input')
    return [ordered]@{
        process = $proof
        requested_sandbox = $Sandbox
        requested_cwd = $script:RepoRoot
        requested_additional_writable_directory_count = 0
        debug_strict_config_supported = $false
        argv_sha256 = Get-Sha256Text (($arguments | ConvertTo-Json -Compress) + "`n")
        effective = $effective
        effective_projection_sha256 = Get-Sha256Text (($effective | ConvertTo-Json -Depth 6 -Compress) + "`n")
        quiescence_before = $quiescenceBefore
        quiescence_after = $quiescenceAfter
        live_codex_home_before = $liveCodexHomeBefore
        live_codex_home_after = $liveCodexHomeAfter
        prior_publication6_before = $priorP6Before
        prior_publication6_after = $priorP6After
        prior_publication5_before = $priorP5Before
        prior_publication5_after = $priorP5After
        prior_publication4_before = $priorP4Before
        prior_publication4_after = $priorP4After
        prior_publication3_before = $priorP3Before
        prior_publication3_after = $priorP3After
    }
}

function Assert-NoSystemSkillScratchSurface([string]$Label) {
    if (-not $script:PermissionStagingLayout -or
        [string]::IsNullOrWhiteSpace([string]$script:PermissionStagingLayout.codex_home)) {
        throw (New-P6Failure 'MODEL_VERDICT_INVALID' $Label `
            'The retained permission-staging CODEX_HOME is unavailable for the system-skill surface check.')
    }
    $codexHome = [System.IO.Path]::GetFullPath([string]$script:PermissionStagingLayout.codex_home).TrimEnd('\')
    $systemSkillRoot = Join-Path $codexHome 'skills\.system'
    if (Test-Path -LiteralPath $systemSkillRoot) {
        throw (New-P6Failure 'MODEL_VERDICT_INVALID' $Label `
            'The disposable CODEX_HOME contains a forbidden bundled system-skill subtree.')
    }
    return [ordered]@{
        system_skill_root = $systemSkillRoot
        system_skill_root_exists = $false
        codex_home_manifest = Get-OrdinalTreeManifest $codexHome
        request_scratch_manifest = Get-OrdinalTreeManifest $script:PermissionStagingLayout.request_root
    }
}

function Test-SystemSkillPathLiteral([string]$Text) {
    if ([string]::IsNullOrEmpty($Text)) { return $false }
    return $Text.Replace('\', '/') -match '(?i)(^|/+|["''\s])skills/+\.system(?:/+|["''\s]|$)'
}

function Test-NativeSkillEventValue([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
    return $Value -match '(?i)(^|[._:/-])skills?($|[._:/-])'
}

function Assert-NoSystemSkillJsonEvent(
    [object]$EventObject,
    [int]$LineNumber,
    [string]$Label
) {
    $eventFieldNames = @('type', 'event', 'name', 'tool', 'tool_name', 'tool_type', 'action', 'action_type')
    $requestFieldNames = @(
        'command', 'argv', 'arguments', 'args', 'input', 'tool_input', 'parameters',
        'path', 'file_path', 'cwd'
    )
    $outputFieldNames = @(
        'aggregated_output', 'output', 'stdout', 'stderr', 'text', 'message', 'content',
        'result', 'response', 'last_message', 'final_output', 'tool_output', 'error', 'summary'
    )
    $requestKindPattern = '(?i)(^|[._-])(?:command|command_execution|shell_command|exec_command|tool_call|tool_request|function_call|function_request|mcp_tool_call|custom_tool_call|dynamic_tool_call|computer_action|action_request)($|[._-])'
    $outputKindPattern = '(?i)(^|[._-])(?:output|result|response)($|[._-])'
    $requestFieldCount = 0
    $pending = New-Object 'System.Collections.Generic.Queue[object]'
    $pending.Enqueue([pscustomobject]@{
        value = $EventObject
        suppressed_output = $false
        inspect_request_text = $false
    })
    while ($pending.Count -ne 0) {
        $state = $pending.Dequeue()
        $node = $state.value
        if ($null -eq $node -or [bool]$state.suppressed_output) { continue }
        if ($node -is [string]) {
            if ([bool]$state.inspect_request_text -and (Test-SystemSkillPathLiteral $node)) {
                throw (New-P6Failure 'MODEL_VERDICT_INVALID' $Label `
                    "The model JSONL executable request references a forbidden system-skill path at line $LineNumber.")
            }
            continue
        }
        if ($node -is [ValueType]) { continue }
        if ($node -is [System.Collections.IEnumerable] -and
            $node -isnot [System.Collections.IDictionary] -and
            $node -isnot [System.Management.Automation.PSCustomObject]) {
            foreach ($value in $node) {
                if ($null -ne $value) {
                    $pending.Enqueue([pscustomobject]@{
                        value = $value
                        suppressed_output = $false
                        inspect_request_text = [bool]$state.inspect_request_text
                    })
                }
            }
            continue
        }

        $properties = New-Object System.Collections.Generic.List[object]
        if ($node -is [System.Collections.IDictionary]) {
            foreach ($key in $node.Keys) {
                $properties.Add([pscustomobject]@{ name = [string]$key; value = $node[$key] })
            }
        }
        elseif ($node -is [System.Management.Automation.PSCustomObject]) {
            foreach ($property in $node.PSObject.Properties) {
                $properties.Add([pscustomobject]@{ name = $property.Name; value = $property.Value })
            }
        }
        else { continue }

        $discriminators = New-Object System.Collections.Generic.List[string]
        $hasCommandField = $false
        $hasToolIdentity = $false
        $hasToolPayload = $false
        foreach ($property in $properties) {
            $fieldName = ([string]$property.name).ToLowerInvariant()
            $value = $property.value
            if ($fieldName -in @('command', 'argv')) { $hasCommandField = $true }
            if ($fieldName -in @('tool', 'tool_name')) { $hasToolIdentity = $true }
            if ($fieldName -in @('arguments', 'args', 'input', 'tool_input', 'parameters')) {
                $hasToolPayload = $true
            }
            if ($eventFieldNames -ccontains $fieldName -and $value -is [string]) {
                if (Test-NativeSkillEventValue $value) {
                    throw (New-P6Failure 'MODEL_VERDICT_INVALID' $Label `
                        "The model JSONL transcript exposes a native skill invocation event at line $LineNumber.")
                }
                $discriminators.Add($value)
            }
        }
        $isOutputNode = @($discriminators | Where-Object { $_ -match $outputKindPattern }).Count -ne 0
        $isRequestNode = (-not [bool]$state.inspect_request_text) -and (-not $isOutputNode) -and (
            @($discriminators | Where-Object { $_ -match $requestKindPattern }).Count -ne 0 -or
            $hasCommandField -or ($hasToolIdentity -and $hasToolPayload)
        )
        foreach ($property in $properties) {
            $fieldName = ([string]$property.name).ToLowerInvariant()
            $value = $property.value
            if ($null -eq $value) { continue }
            $childSuppressed = $false
            $childInspect = $false
            if ([bool]$state.inspect_request_text) {
                $childInspect = $true
            }
            elseif ($outputFieldNames -ccontains $fieldName) {
                $childSuppressed = $true
            }
            elseif ($isRequestNode -and $requestFieldNames -ccontains $fieldName) {
                $childInspect = $true
                $requestFieldCount++
            }
            $pending.Enqueue([pscustomobject]@{
                value = $value
                suppressed_output = $childSuppressed
                inspect_request_text = $childInspect
            })
        }
    }
    return [ordered]@{
        executable_request_field_count = $requestFieldCount
        system_skill_path_reference_count = 0
        native_skill_event_count = 0
    }
}

function Assert-NoSystemSkillJsonLine(
    [string]$Line,
    [int]$LineNumber,
    [string]$Label
) {
    if ([string]::IsNullOrWhiteSpace($Line)) {
        throw (New-P6Failure 'MODEL_VERDICT_INVALID' $Label `
            "The model JSONL transcript contains an empty record at line $LineNumber.")
    }
    try { $eventObject = $Line | ConvertFrom-Json }
    catch {
        throw (New-P6Failure 'MODEL_VERDICT_INVALID' $Label `
            "The model JSONL transcript contains invalid JSON at line $LineNumber." $_.Exception)
    }
    if ($null -eq $eventObject -or $eventObject -isnot [System.Management.Automation.PSCustomObject] -or
        @($eventObject).Count -ne 1 -or @($eventObject.PSObject.Properties).Count -eq 0) {
        throw (New-P6Failure 'MODEL_VERDICT_INVALID' $Label `
            "The model JSONL transcript record at line $LineNumber is not one event object.")
    }
    return Assert-NoSystemSkillJsonEvent $eventObject $LineNumber $Label
}

function Invoke-SystemSkillJsonlParserCanary {
    $systemSkillPath = 'C:\scratch\skills\.system\review-agent\SKILL.md'
    $acceptedCases = [ordered]@{
        'aggregated-output-literal' = ([ordered]@{
            type = 'item.completed'
            item = [ordered]@{
                type = 'command_execution'
                command = 'Write-Output safe'
                aggregated_output = $systemSkillPath
            }
        } | ConvertTo-Json -Depth 6 -Compress)
        'agent-text-literal' = ([ordered]@{
            type = 'item.completed'
            item = [ordered]@{ type = 'agent_message'; text = $systemSkillPath }
        } | ConvertTo-Json -Depth 6 -Compress)
    }
    foreach ($name in $acceptedCases.Keys) {
        $null = Assert-NoSystemSkillJsonLine $acceptedCases[$name] 1 ('jsonl-canary-' + $name)
    }
    $rejectedCases = [ordered]@{
        'command-request-path' = ([ordered]@{
            type = 'item.started'
            item = [ordered]@{
                type = 'command_execution'
                command = ('Get-Content -LiteralPath "' + $systemSkillPath + '"')
            }
        } | ConvertTo-Json -Depth 6 -Compress)
        'tool-request-path' = ([ordered]@{
            type = 'item.started'
            item = [ordered]@{
                type = 'mcp_tool_call'
                tool_name = 'read_file'
                arguments = [ordered]@{ path = $systemSkillPath }
            }
        } | ConvertTo-Json -Depth 6 -Compress)
        'native-skill-event' = ([ordered]@{
            type = 'item.started'
            item = [ordered]@{ type = 'skill_invocation'; name = 'review-agent' }
        } | ConvertTo-Json -Depth 6 -Compress)
        'malformed-json' = '{'
        'non-object-json' = '"not-an-event"'
    }
    $rejected = New-Object System.Collections.Generic.List[string]
    foreach ($name in $rejectedCases.Keys) {
        $didReject = $false
        try { $null = Assert-NoSystemSkillJsonLine $rejectedCases[$name] 1 ('jsonl-canary-' + $name) }
        catch {
            $metadata = Get-P6FailureMetadata $_.Exception
            if ($metadata.error_code -cne 'MODEL_VERDICT_INVALID') { throw $_.Exception }
            $didReject = $true
        }
        if (-not $didReject) {
            throw (New-P6Failure 'MODEL_VERDICT_INVALID' 'jsonl-parser-canary' `
                ('JSONL parser canary accepted forbidden case: ' + $name))
        }
        $rejected.Add($name)
    }
    return [ordered]@{
        accepted_case_count = $acceptedCases.Count
        accepted_cases = @($acceptedCases.Keys)
        rejected_case_count = $rejected.Count
        rejected_cases = $rejected.ToArray()
    }
}

function Assert-NoSystemSkillJsonl(
    [string]$Path,
    [string]$Label
) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw (New-P6Failure 'MODEL_VERDICT_INVALID' $Label 'The model JSONL transcript is absent.')
    }
    $lineCount = 0
    $requestFieldCount = 0
    foreach ($line in [System.IO.File]::ReadAllLines($Path, $Utf8NoBom)) {
        $lineCount++
        $lineProof = Assert-NoSystemSkillJsonLine $line $lineCount $Label
        $requestFieldCount += $lineProof.executable_request_field_count
    }
    if ($lineCount -eq 0) {
        throw (New-P6Failure 'MODEL_VERDICT_INVALID' $Label 'The model JSONL transcript is empty.')
    }
    return [ordered]@{
        line_count = $lineCount
        jsonl_sha256 = Get-FileSha256 $Path
        executable_request_field_count = $requestFieldCount
        system_skill_path_reference_count = 0
        native_skill_event_count = 0
    }
}

function Invoke-Terra(
    [string]$Label,
    [string]$Sandbox,
    [string]$PromptPath,
    [System.Collections.IDictionary]$ExpectedRepoIdentity
) {
    $expectedCodexHome = [System.IO.Path]::GetFullPath($script:PermissionStagingLayout.codex_home).TrimEnd('\')
    $effectiveCodexHome = [System.IO.Path]::GetFullPath($env:CODEX_HOME).TrimEnd('\')
    if (-not $effectiveCodexHome.Equals($expectedCodexHome, [StringComparison]::OrdinalIgnoreCase)) {
        throw (New-P6Failure 'PERMISSION_ATTESTATION_FAILED' ($Label + '-codex-home') `
            'Codex process does not use the retained permission-staging CODEX_HOME.')
    }
    $env:TEMP = $script:PermissionStagingLayout.temp_root
    $env:TMP = $script:PermissionStagingLayout.temp_root
    foreach ($name in @('TEMP', 'TMP')) {
        $effectiveTemp = [System.IO.Path]::GetFullPath([Environment]::GetEnvironmentVariable($name, 'Process')).TrimEnd('\')
        if (-not $effectiveTemp.Equals($script:PermissionStagingLayout.temp_root, [StringComparison]::OrdinalIgnoreCase)) {
            throw (New-P6Failure 'PERMISSION_ATTESTATION_FAILED' ($Label + '-temp-root') `
                "$name is not the retained permission-staging temporary root.")
        }
    }
    $promptInputProof = Get-PromptInputProof $Label $Sandbox
    if ($Label -ceq 'implementation' -and
        $promptInputProof.effective_projection_sha256 -cne $script:PreclaimPermissionProjectionHash) {
        throw (New-P6Failure 'PERMISSION_ATTESTATION_FAILED' 'implementation-permission-projection' `
            'Post-claim implementation permission projection differs from the pre-claim attestation.')
    }
    $systemSkillScratchBefore = Assert-NoSystemSkillScratchSurface ($Label + '-before-model-skill-surface')
    $jsonl = Join-Path $script:EvidenceRoot ($Label + '.jsonl')
    $stderr = Join-Path $script:EvidenceRoot ($Label + '.stderr.txt')
    $last = Join-Path $script:EvidenceRoot ($Label + '.result.json')
    $arguments = @('exec', '--model', 'gpt-5.6-terra') + @(Get-ClosedConfigArguments) + @(
        '--sandbox', $Sandbox, '--cd', $script:RepoRoot,
        '--skip-git-repo-check', '--ephemeral', '--ignore-user-config', '--ignore-rules',
        '--strict-config', '--output-schema', $script:ResultSchema, '--json',
        '--output-last-message', $last, '-'
    )
    $invocationPath = Join-Path $script:EvidenceRoot ($Label + '.invocation.json')
    $invocation = [ordered]@{
        requested_model = 'gpt-5.6-terra'
        requested_reasoning_effort = 'xhigh'
        sandbox = $Sandbox
        cwd = $script:RepoRoot
        additional_writable_directory_count = 0
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
        live_codex_home_before_prompt_input = $promptInputProof.live_codex_home_before
        live_codex_home_after_prompt_input = $promptInputProof.live_codex_home_after
        prior_publication6_before_prompt_input = $promptInputProof.prior_publication6_before
        prior_publication6_after_prompt_input = $promptInputProof.prior_publication6_after
        prior_publication5_before_prompt_input = $promptInputProof.prior_publication5_before
        prior_publication5_after_prompt_input = $promptInputProof.prior_publication5_after
        prior_publication4_before_prompt_input = $promptInputProof.prior_publication4_before
        prior_publication4_after_prompt_input = $promptInputProof.prior_publication4_after
        prior_publication3_before_prompt_input = $promptInputProof.prior_publication3_before
        prior_publication3_after_prompt_input = $promptInputProof.prior_publication3_after
        system_skill_scratch_before_model = $systemSkillScratchBefore
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
    $liveCodexHomeBeforeCodex = Assert-LiveCodexHomeUnchanged $script:LiveCodexHomeBefore `
        ($Label + '-before-codex')
    $priorP6BeforeCodex = Assert-PriorP6PreclaimUnchanged $script:PriorP6Before
    $priorP5BeforeCodex = Assert-PriorP5EvidenceUnchanged $script:PriorP5Before
    $priorP4BeforeCodex = Assert-PriorP4EvidenceUnchanged $script:PriorP4Before
    $priorP3BeforeCodex = Assert-PriorP3EvidenceUnchanged $script:PriorP3Before
    $process = $null
    $processFailure = $null
    $exitCode = $null
    $systemSkillScratchAfter = $null
    try {
        try {
            try {
                $process = Start-Process -FilePath $script:CodexExe -ArgumentList $arguments -NoNewWindow -PassThru `
                    -RedirectStandardInput $PromptPath -RedirectStandardOutput $jsonl -RedirectStandardError $stderr
                $rawHandle = $process.Handle
            }
            catch {
                if ($null -eq $process) {
                    throw (New-P6Failure 'PROCESS_START_FAILED' $Label 'The Codex process could not be started.' $_.Exception)
                }
                throw (New-P6Failure 'PROCESS_HANDLE_UNAVAILABLE' $Label `
                    'The Codex process handle could not be acquired immediately after start.' $_.Exception)
            }
            if ($null -eq $rawHandle -or $rawHandle -isnot [IntPtr] -or $rawHandle -eq [IntPtr]::Zero) {
                throw (New-P6Failure 'PROCESS_HANDLE_UNAVAILABLE' $Label `
                    'The Codex process returned an invalid handle immediately after start.')
            }
            $cachedHandle = [IntPtr]$rawHandle
            $exitCode = Wait-CapturedProcessExitCode $process $Label 3600000
            if ($exitCode -ne 0) {
                throw (New-P6Failure 'PROCESS_EXIT_NONZERO' $Label "The Codex process exited $exitCode.")
            }
        }
        catch {
            $processFailure = $_.Exception
            if ($process) {
                try {
                    if (-not $process.HasExited) {
                        $process.Kill()
                        $process.WaitForExit()
                    }
                }
                catch {
                    $processFailure = New-P6Failure 'UNEXPECTED_FAILURE' $Label `
                        'Codex process failure cleanup failed.' $_.Exception
                }
            }
        }
    }
    finally {
        try {
            $systemSkillScratchAfter = Assert-NoSystemSkillScratchSurface ($Label + '-after-model-skill-surface')
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
        finally {
            if ($process) { $process.Dispose() }
        }
    }
    $postCallQuiescence = Get-QuiescenceProof
    $liveCodexHomeAfterCodex = Assert-LiveCodexHomeUnchanged $script:LiveCodexHomeBefore `
        ($Label + '-after-codex')
    $priorP6AfterCodex = Assert-PriorP6PreclaimUnchanged $script:PriorP6Before
    $priorP5AfterCodex = Assert-PriorP5EvidenceUnchanged $script:PriorP5Before
    $priorP4AfterCodex = Assert-PriorP4EvidenceUnchanged $script:PriorP4Before
    $priorP3AfterCodex = Assert-PriorP3EvidenceUnchanged $script:PriorP3Before
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
    if ($processFailure) { throw $processFailure }
    $systemSkillJsonlProof = Assert-NoSystemSkillJsonl $jsonl ($Label + '-jsonl-skill-surface')
    if (-not (Test-Path -LiteralPath $last -PathType Leaf)) { throw "$Label did not publish its result." }
    $result = Get-Content -LiteralPath $last -Raw | ConvertFrom-Json
    $resultHash = Get-FileSha256 $last
    switch -CaseSensitive ([string]$result.verdict) {
        'BLOCKED' {
            throw (New-P6ModelVerdictFailure 'MODEL_VERDICT_BLOCKED' $Label 'BLOCKED' `
                "$Label returned schema-valid BLOCKED." $last $resultHash)
        }
        'CHANGES_REQUIRED' {
            throw (New-P6ModelVerdictFailure 'MODEL_VERDICT_CHANGES_REQUIRED' $Label 'CHANGES_REQUIRED' `
                "$Label returned schema-valid CHANGES_REQUIRED." $last $resultHash)
        }
        'INVALID' {
            throw (New-P6ModelVerdictFailure 'MODEL_VERDICT_INVALID' $Label 'INVALID' `
                "$Label returned schema-valid INVALID." $last $resultHash)
        }
        'PASS' { }
        default {
            throw (New-P6ModelVerdictFailure 'MODEL_VERDICT_INVALID' $Label ([string]$result.verdict) `
                "$Label returned an unsupported verdict." $last $resultHash)
        }
    }
    $materialFindings = @($result.findings | Where-Object { $_.severity -in @('blocker', 'significant') })
    if ($materialFindings.Count -ne 0) {
        throw (New-P6ModelVerdictFailure 'MODEL_PASS_MATERIAL_FINDINGS' $Label 'PASS' `
            "$Label returned PASS with material findings." $last $resultHash)
    }
    return [ordered]@{
        exit_code = $exitCode
        jsonl_path = $jsonl
        jsonl_sha256 = Get-FileSha256 $jsonl
        stderr_path = $stderr
        stderr_sha256 = Get-FileSha256 $stderr
        result_path = $last
        result_sha256 = $resultHash
        invocation_path = $invocationPath
        invocation_sha256 = Get-FileSha256 $invocationPath
        prompt_input_proof = $promptInputProof
        system_skill_scratch_before_model = $systemSkillScratchBefore
        system_skill_scratch_after_model = $systemSkillScratchAfter
        system_skill_jsonl_proof = $systemSkillJsonlProof
        pre_identity_sha256 = Get-FileSha256 (Join-Path $script:EvidenceRoot ($Label + '.pre-identity.json'))
        post_identity_sha256 = Get-FileSha256 (Join-Path $script:EvidenceRoot ($Label + '.post-identity.json'))
        pre_call_quiescence = $preCallQuiescence
        post_call_quiescence = $postCallQuiescence
        live_codex_home_before_codex = $liveCodexHomeBeforeCodex
        live_codex_home_after_codex = $liveCodexHomeAfterCodex
        prior_publication6_before_codex = $priorP6BeforeCodex
        prior_publication6_after_codex = $priorP6AfterCodex
        prior_publication5_before_codex = $priorP5BeforeCodex
        prior_publication5_after_codex = $priorP5AfterCodex
        prior_publication4_before_codex = $priorP4BeforeCodex
        prior_publication4_after_codex = $priorP4AfterCodex
        prior_publication3_before_codex = $priorP3BeforeCodex
        prior_publication3_after_codex = $priorP3AfterCodex
    }
}

function Invoke-P7Preflight([bool]$RetainPermissionStaging) {
    if (Test-Path -LiteralPath $script:EvidenceRoot) {
        throw 'This deterministic Publication-7 lineage already exists. Run Inspect; do not create another attempt.'
    }
    $quiescenceBefore = Get-QuiescenceProof
    $priorP6Before = Get-PriorP6PreclaimProof
    $priorP5Before = Get-PriorP5EvidenceProof
    $priorP4Before = Get-PriorP4EvidenceProof
    $priorP3Before = Get-PriorP3EvidenceProof
    $processExitCanary = Invoke-ProcessExitCanary

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
    $liveAuthItem = Get-Item -LiteralPath $liveAuthPath -Force -ErrorAction Stop
    if (($liveAuthItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'Live Codex authentication is a reparse point.'
    }
    Assert-NoAlternateDataStream $liveAuthItem.FullName
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
        '--sandbox', '<sandbox>', '--cd', '<owner-worktree>',
        '--skip-git-repo-check', '--ephemeral', '--ignore-user-config', '--ignore-rules',
        '--strict-config', '--output-schema', '<result-schema>', '--json',
        '--output-last-message', '<last-message-file>', '-'
    )
    $baseArgvHash = Get-Sha256Text (($baseArgvTemplate | ConvertTo-Json -Compress) + "`n")
    $permissionParserCanary = Invoke-PermissionParserCanary $script:RepoRoot
    $systemSkillJsonlParserCanary = Invoke-SystemSkillJsonlParserCanary
    $permissionAttestation = $null
    try {
        $permissionAttestation = Invoke-PreclaimPermissionAttestation $codexExe $liveAuthPath $liveAuthHash `
            $liveCodexHome $liveCodexHomeFirst $RetainPermissionStaging

    $liveCodexHomeSecond = Get-CodexHomeManifest $liveCodexHome
    if (-not (Test-ManifestEqual $liveCodexHomeFirst $liveCodexHomeSecond)) {
        throw 'The live CODEX_HOME changed during Publication-7 preflight.'
    }
    if ((Get-FileSha256 $liveAuthPath) -cne $liveAuthHash) {
        throw 'The live Codex authentication bytes changed during Publication-7 preflight.'
    }
    $priorP6After = Assert-PriorP6PreclaimUnchanged $priorP6Before
    $priorP5After = Assert-PriorP5EvidenceUnchanged $priorP5Before
    $priorP4After = Assert-PriorP4EvidenceUnchanged $priorP4Before
    $priorP3After = Assert-PriorP3EvidenceUnchanged $priorP3Before
    $quiescenceAfter = Get-QuiescenceProof
    if (Test-Path -LiteralPath $script:EvidenceRoot) {
        throw 'The Publication-7 evidence root appeared during preflight.'
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
        permission_parser_canary = $permissionParserCanary
        system_skill_jsonl_parser_canary = $systemSkillJsonlParserCanary
        permission_attestation = $permissionAttestation
        live_codex_home = $liveCodexHome
        live_codex_home_manifest = $liveCodexHomeSecond
        live_auth_sha256 = $liveAuthHash
        process_exit_canary = $processExitCanary
        prior_publication6_before = $priorP6Before
        prior_publication6_after = $priorP6After
        prior_publication5_before = $priorP5Before
        prior_publication5_after = $priorP5After
        prior_publication4_before = $priorP4Before
        prior_publication4_after = $priorP4After
        prior_publication3_before = $priorP3Before
        prior_publication3_after = $priorP3After
        quiescence_before = $quiescenceBefore
        quiescence_after = $quiescenceAfter
        }
    }
    catch {
        $preflightFailure = $_.Exception
        if ($permissionAttestation -and $permissionAttestation.layout) {
            try { Remove-PermissionStagingLayout $permissionAttestation.layout }
            catch { throw $_.Exception }
        }
        throw $preflightFailure
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

try {
    $script:CanonicalApprovalMessageFile = Join-Path $env:LOCALAPPDATA 'SkillMesh\Evidence\GoalNP\Publication7\approval1-message.txt'
    $suppliedApprovalPath = [System.IO.Path]::GetFullPath($ApprovalMessageFile)
    $canonicalApprovalPath = [System.IO.Path]::GetFullPath($script:CanonicalApprovalMessageFile)
    if (-not $suppliedApprovalPath.Equals($canonicalApprovalPath, [StringComparison]::OrdinalIgnoreCase)) {
        throw (New-P6Failure 'UNEXPECTED_FAILURE' 'approval-message' `
            'ApprovalMessageFile is not the canonical Publication-7 approval path.')
    }
    if (-not (Test-Path -LiteralPath $canonicalApprovalPath -PathType Leaf)) {
        throw (New-P6Failure 'UNEXPECTED_FAILURE' 'approval-message' 'ApprovalMessageFile does not exist.')
    }
    $approvalItem = Get-Item -LiteralPath $canonicalApprovalPath -Force -ErrorAction Stop
    if (($approvalItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw (New-P6Failure 'UNEXPECTED_FAILURE' 'approval-message' 'ApprovalMessageFile is a reparse point.')
    }
    Assert-NoAlternateDataStream $approvalItem.FullName
    $expectedApprovalBytes = $Utf8NoBom.GetBytes($ExpectedApproval + "`n")
    $actualApprovalBytes = [System.IO.File]::ReadAllBytes($canonicalApprovalPath)
    if ([Convert]::ToBase64String($actualApprovalBytes) -cne [Convert]::ToBase64String($expectedApprovalBytes)) {
        throw (New-P6Failure 'UNEXPECTED_FAILURE' 'approval-message' `
            'Approval message is not exact UTF-8 without BOM, with one final LF, for Publication 7.')
    }
}
catch {
    if ($_.Exception.Data.Contains('error_code')) { throw $_.Exception }
    throw (New-P6Failure 'UNEXPECTED_FAILURE' 'approval-message' $_.Exception.Message $_.Exception)
}
$script:ApprovalMessageHash = Get-Sha256Text $ExpectedApproval
$identityText = @(
    'publication-7-writable-root-grammar-recovery-v1',
    $ApprovedCommit,
    $script:ApprovalMessageHash,
    $PriorP6ApprovedCommit,
    $PriorP6RequestId,
    $PriorP6ApprovalMessageHash,
    $PriorP6ApprovalMessageFileHash,
    $PriorP6HandoffHash,
    $PriorP5RequestId,
    $PriorP5StateHash,
    $PriorP5RootManifestHash,
    $PriorP4RequestId,
    $PriorP4StateHash,
    $PriorP4RootManifestHash,
    $PriorP3RequestId,
    $PriorP3StateHash,
    $PriorP3RootManifestHash
) -join "`n"
$script:RequestId = 'tba-' + (Get-Sha256Text $identityText)
$script:EvidenceRoot = Join-Path $env:LOCALAPPDATA ('SkillMesh\Evidence\GoalNP\TerraBootstrap\' + $script:RequestId)
$script:StatePath = Join-Path $script:EvidenceRoot 'state.json'

if ($Action -eq 'Inspect') {
    $null = Get-PriorP6PreclaimProof
    $null = Get-PriorP5EvidenceProof
    $null = Get-PriorP4EvidenceProof
    $null = Get-PriorP3EvidenceProof
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

try {
    $preflight = Invoke-P7Preflight ($Action -ceq 'Run')
}
catch {
    $preflightException = $_.Exception
    $metadata = Get-P6FailureMetadata $preflightException
    if (-not $preflightException.Data.Contains('error_code')) {
        $preflightException = New-P6Failure 'UNEXPECTED_FAILURE' 'preflight' `
            $_.Exception.Message $_.Exception
        $metadata = Get-P6FailureMetadata $preflightException
    }
    $preflightFailure = [ordered]@{
        schema_version = 1
        action = $Action
        verdict = 'BLOCKED'
        request_id = $script:RequestId
        approved_commit = $ApprovedCommit
        error_code = $metadata.error_code
        error_label = $metadata.error_label
        error = $preflightException.Message
        evidence_root_absent = -not (Test-Path -LiteralPath $script:EvidenceRoot)
    }
    Add-PermissionMismatchDiagnostics $preflightFailure $preflightException
    if ($metadata.cause_code) { $preflightFailure['cause_code'] = $metadata.cause_code }
    [Console]::Out.Write(($preflightFailure | ConvertTo-Json -Depth 6) + "`n")
    throw $preflightException
}
if ($Action -eq 'Preflight') {
    $preflight | ConvertTo-Json -Depth 12
    exit 0
}

$script:PermissionStagingLayout = $preflight.permission_attestation.layout
try {
    if (-not $script:PermissionStagingLayout -or
        -not (Test-Path -LiteralPath $script:PermissionStagingLayout.request_root -PathType Container)) {
        throw (New-P6Failure 'PERMISSION_ATTESTATION_FAILED' 'permission-staging-retention' `
            'Run preflight did not retain the exact permission-staging request root.')
    }
    if (Test-Path -LiteralPath $script:EvidenceRoot) {
        throw 'This deterministic Publication-7 lineage already exists. Run Inspect; do not create another attempt.'
    }
    New-Item -ItemType Directory -Path $script:EvidenceRoot | Out-Null
}
catch {
    $claimFailure = $_.Exception
    if ($script:PermissionStagingLayout) {
        try { Remove-DisposableCodexHome }
        catch { throw $_.Exception }
    }
    throw $claimFailure
}
$previous = Get-Location
$EnvironmentNames = @(
    'CODEX_HOME', 'TEMP', 'TMP', 'PIP_CACHE_DIR', 'PYTHONNOUSERSITE',
    'PYTHONDONTWRITEBYTECODE', 'PIP_NO_INPUT', 'PIP_DISABLE_PIP_VERSION_CHECK', 'PIP_CONFIG_FILE'
)
$OriginalEnvironment = [ordered]@{}
foreach ($name in $EnvironmentNames) {
    $OriginalEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
$script:DisposableCodexHome = $script:PermissionStagingLayout.codex_home
$script:LiveCodexHome = $preflight.live_codex_home
$script:LiveCodexHomeBefore = $preflight.live_codex_home_manifest
$script:PriorP6Before = $preflight.prior_publication6_after
$script:PriorP5Before = $preflight.prior_publication5_after
$script:PriorP4Before = $preflight.prior_publication4_after
$script:PriorP3Before = $preflight.prior_publication3_after
$script:PreclaimPermissionProjectionHash = $preflight.permission_attestation.effective_projection_sha256
$bundleHashes = $preflight.bundle_sha256
$baseArgvHash = $preflight.base_argv_sha256
$PythonExe = $preflight.python.executable
$script:CodexExe = $preflight.codex.executable
$script:ResultSchema = Join-Path $RepoRoot 'schemas\terra-bootstrap-result-v1.schema.json'
$script:PermissionCleanupAttempted = $false
try {
    $preflightPath = Join-Path $script:EvidenceRoot 'preflight.json'
    Write-Utf8NoBom $preflightPath (($preflight | ConvertTo-Json -Depth 12) + "`n")
    $LiveAuthPath = Join-Path $LiveCodexHome 'auth.json'
    if (-not (Test-Path -LiteralPath $LiveAuthPath -PathType Leaf)) { throw 'Codex authentication is unavailable.' }
    if ((Get-FileSha256 $LiveAuthPath) -cne $preflight.live_auth_sha256) {
        throw 'Live Codex authentication changed after preflight.'
    }
    $postAllocationLiveCodexHome = Get-CodexHomeManifest $LiveCodexHome
    if (-not (Test-ManifestEqual $LiveCodexHomeBefore $postAllocationLiveCodexHome)) {
        throw 'The live CODEX_HOME changed after preflight and before execution.'
    }
    $PriorP6PostAllocation = Assert-PriorP6PreclaimUnchanged $PriorP6Before
    $PriorP5PostAllocation = Assert-PriorP5EvidenceUnchanged $PriorP5Before
    $PriorP4PostAllocation = Assert-PriorP4EvidenceUnchanged $PriorP4Before
    $PriorP3PostAllocation = Assert-PriorP3EvidenceUnchanged $PriorP3Before
    if ((Get-FileSha256 (Join-Path $script:DisposableCodexHome 'auth.json')) -cne $preflight.live_auth_sha256) {
        throw 'Retained permission-staging Codex authentication copy mismatch.'
    }
    $preclaimStdoutPath = Join-Path $script:EvidenceRoot 'preclaim-permission.stdout.json'
    $preclaimStderrPath = Join-Path $script:EvidenceRoot 'preclaim-permission.stderr.txt'
    Copy-Item -LiteralPath $preflight.permission_attestation.stdout_path -Destination $preclaimStdoutPath
    Copy-Item -LiteralPath $preflight.permission_attestation.stderr_path -Destination $preclaimStderrPath
    if ((Get-FileSha256 $preclaimStdoutPath) -cne $preflight.permission_attestation.stdout_sha256 -or
        (Get-FileSha256 $preclaimStderrPath) -cne $preflight.permission_attestation.stderr_sha256) {
        throw 'Retained pre-claim permission proof copy mismatch.'
    }
    $env:CODEX_HOME = $script:DisposableCodexHome
    $env:TEMP = $script:PermissionStagingLayout.temp_root
    $env:TMP = $script:PermissionStagingLayout.temp_root

    Set-Location $RepoRoot
    $postAllocationQuiescence = Get-QuiescenceProof
    if ((& $script:CodexExe --version).Trim() -cne $ExpectedCodexVersion) { throw 'Pinned Codex version mismatch.' }

    Write-State 'prepared' @{
        preflight_sha256 = Get-FileSha256 $preflightPath
        bundle_sha256 = $bundleHashes
        codex_executable_sha256 = $ExpectedCodexHash
        python_executable_sha256 = $ExpectedPythonHash
        live_codex_home_before = $LiveCodexHomeBefore
        process_exit_canary = $preflight.process_exit_canary
        preclaim_permission_stdout_sha256 = Get-FileSha256 $preclaimStdoutPath
        preclaim_permission_stderr_sha256 = Get-FileSha256 $preclaimStderrPath
        preclaim_permission_projection_sha256 = $script:PreclaimPermissionProjectionHash
        prior_publication6_before = $PriorP6Before
        prior_publication6_post_allocation = $PriorP6PostAllocation
        prior_publication5_before = $PriorP5Before
        prior_publication5_post_allocation = $PriorP5PostAllocation
        prior_publication4_before = $PriorP4Before
        prior_publication4_post_allocation = $PriorP4PostAllocation
        prior_publication3_before = $PriorP3Before
        prior_publication3_post_allocation = $PriorP3PostAllocation
        post_allocation_quiescence = $postAllocationQuiescence
        base_argv_sha256 = $baseArgvHash
    }

    $implementationPrompt = @"
Implement only ADMIN-BOOTSTRAP for Goal NP Publication 7 at commit $ApprovedCommit.
The exact owner worktree is $RepoRoot. Read $RepoRoot\plan.md,
$RepoRoot\documentation\native-claude-codex-skill-parity-plan.md, and
$RepoRoot\documentation\native-claude-codex-skill-parity-terra-amendment.md. The amendment controls
the implementation executor. Modify only the 15 ADMIN paths enumerated there and in the base plan.
Implement the Terra-direct executor fields and zero-model deterministic issue synchronization.
This is only local generic repository implementation against frozen approved inputs. All Codex,
model, and CLI strings and behavior are opaque literals; their names are incidental. This is not a
request to discover or validate current OpenAI or Codex facts, docs, settings, setup, troubleshooting,
prompting, model choice, APIs, or SDKs. If a genuine system trigger nevertheless requires an unavailable
capability, return schema-valid BLOCKED without attempting web or network access.
Do not commit, stage, mutate GitHub, invoke another model, install dependencies, run tests, use a
repo/user skill, plugin, MCP, web, or browser, write a live discovery/config home, or touch any other
path. No system-skill trigger applies to this frozen generic task; do not open or invoke a system skill.
If you judge that a system-skill trigger nevertheless applies, return schema-valid BLOCKED before any
mutation and do not attempt web or network access. The outer launcher owns the exact contained tests
and review. End with schema-valid JSON only; PASS means the files are ready for those deterministic
gates.
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
    $ReviewInputRoot = Join-Path $script:EvidenceRoot 'review-input'
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
Independently review the exact uncommitted ADMIN-BOOTSTRAP candidate for Goal NP Publication 7.
The owner worktree is $RepoRoot and the approved commit is $ApprovedCommit. Read the exact plan at
$RepoRoot\documentation\native-claude-codex-skill-parity-plan.md and controlling amendment at
$RepoRoot\documentation\native-claude-codex-skill-parity-terra-amendment.md. The candidate evidence
is $candidateEvidencePath; its SHA-256 is $(Get-FileSha256 $candidateEvidencePath). The exact binary
diff is $($candidateDiff.stdout_path) with SHA-256 $($candidateDiff.stdout_sha256). The evidence binds
the candidate tree, implementation JSONL, contained lock-based test results, path scope, and diff gate.
Check standalone executability, security/capability boundaries, schemas, zero-model issue sync, crash
behavior, exact 15-path scope, and absence of live/GitHub/model side effects. You are read-only. Do not
change any file. This is only local generic repository review against frozen approved inputs. All Codex, model, and CLI
strings and behavior are opaque literals; their names are incidental. This is not a request to discover
or validate current OpenAI or Codex facts, docs, settings, setup, troubleshooting, prompting, model
choice, APIs, or SDKs. If a genuine system trigger nevertheless requires an unavailable capability,
return schema-valid BLOCKED without attempting web or network access. Do not invoke another model or
use a repo/user skill, plugin, MCP, web, or browser. No system-skill trigger applies to this frozen generic
task; do not open or invoke a system skill. If you judge that a system-skill trigger nevertheless applies,
return schema-valid BLOCKED and do not attempt web or network access. End with schema-valid JSON only.
PASS permits no blocker or significant gap.
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

    $LiveCodexHomeAfter = Assert-LiveCodexHomeUnchanged $LiveCodexHomeBefore 'before-commit'
    $PriorP6BeforeCommit = Assert-PriorP6PreclaimUnchanged $PriorP6Before
    $PriorP5BeforeCommit = Assert-PriorP5EvidenceUnchanged $PriorP5Before
    $PriorP4BeforeCommit = Assert-PriorP4EvidenceUnchanged $PriorP4Before
    $PriorP3BeforeCommit = Assert-PriorP3EvidenceUnchanged $PriorP3Before
    $preCommitQuiescence = Get-QuiescenceProof
    Remove-DisposableCodexHome
    foreach ($name in @('CODEX_HOME', 'TEMP', 'TMP')) {
        $value = $OriginalEnvironment[$name]
        if ($null -eq $value) { Remove-Item -Path ('Env:' + $name) -ErrorAction SilentlyContinue }
        else { Set-Item -Path ('Env:' + $name) -Value $value }
    }

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
    $commitOutput = @(& git commit -m 'chore(goal-np): bootstrap approval tooling')
    if ($LASTEXITCODE -ne 0) { throw 'ADMIN commit failed.' }
    $adminCommit = (& git rev-parse HEAD).Trim()
    $finalStatus = @(& git status --porcelain=v1 --untracked-files=all)
    if ($finalStatus.Count -ne 0) { throw 'ADMIN commit did not leave a clean worktree.' }
    $LiveCodexHomeTerminal = Assert-LiveCodexHomeUnchanged $LiveCodexHomeBefore 'success'
    $PriorP6Terminal = Assert-PriorP6PreclaimUnchanged $PriorP6Before
    $PriorP5Terminal = Assert-PriorP5EvidenceUnchanged $PriorP5Before
    $PriorP4Terminal = Assert-PriorP4EvidenceUnchanged $PriorP4Before
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
        live_codex_home_terminal = $LiveCodexHomeTerminal
        process_exit_canary = $preflight.process_exit_canary
        prior_publication6_before = $PriorP6Before
        prior_publication6_before_commit = $PriorP6BeforeCommit
        prior_publication6_terminal = $PriorP6Terminal
        prior_publication5_before = $PriorP5Before
        prior_publication5_before_commit = $PriorP5BeforeCommit
        prior_publication5_terminal = $PriorP5Terminal
        prior_publication4_before = $PriorP4Before
        prior_publication4_before_commit = $PriorP4BeforeCommit
        prior_publication4_terminal = $PriorP4Terminal
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
    $failure = Get-P6FailureMetadata $originalError.Exception
    $terminalException = $originalError.Exception
    if (-not $originalError.Exception.Data.Contains('error_code')) {
        $terminalException = New-P6Failure 'UNEXPECTED_FAILURE' 'launcher' `
            $originalError.Exception.Message $originalError.Exception
        $failure = Get-P6FailureMetadata $terminalException
    }
    $blocked = [ordered]@{
        error_code = $failure.error_code
        error_label = $failure.error_label
        error = $originalError.Exception.Message
    }
    Add-PermissionMismatchDiagnostics $blocked $terminalException
    if ($failure.cause_code) { $blocked['cause_code'] = $failure.cause_code }
    foreach ($field in @('model_verdict', 'model_result_path', 'model_result_sha256')) {
        if ($terminalException.Data.Contains($field)) { $blocked[$field] = $terminalException.Data[$field] }
    }
    $script:PermissionCleanupAttempted = $true
    try {
        Remove-DisposableCodexHome
        $blocked['disposable_codex_home_removed'] = $true
    }
    catch {
        $cleanupException = $_.Exception
        $blocked['disposable_codex_home_removed'] = $false
        $blocked['disposable_codex_home_cleanup_error'] = $cleanupException.Message
        $blocked['cause_code'] = $failure.error_code
        $terminalException = New-P6Failure 'PERMISSION_STAGING_CLEANUP_FAILED' `
            'permission-staging-cleanup' $cleanupException.Message $cleanupException $failure.error_code
        $failure = Get-P6FailureMetadata $terminalException
        $blocked['error_code'] = $failure.error_code
        $blocked['error_label'] = $failure.error_label
        $blocked['error'] = $terminalException.Message
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
    if ($PriorP6Before) {
        try {
            $blockedPriorP6After = Assert-PriorP6PreclaimUnchanged $PriorP6Before
            $blocked['prior_publication6_after'] = $blockedPriorP6After
            $blocked['prior_publication6_unchanged'] = $true
        }
        catch {
            $blocked['prior_publication6_unchanged'] = $false
            $blocked['prior_publication6_preclaim_error'] = $_.Exception.Message
        }
    }
    if ($PriorP5Before) {
        try {
            $blockedPriorP5After = Assert-PriorP5EvidenceUnchanged $PriorP5Before
            $blocked['prior_publication5_after'] = $blockedPriorP5After
            $blocked['prior_publication5_unchanged'] = $true
        }
        catch {
            $blocked['prior_publication5_unchanged'] = $false
            $blocked['prior_publication5_manifest_error'] = $_.Exception.Message
        }
    }
    if ($PriorP4Before) {
        try {
            $blockedPriorP4After = Assert-PriorP4EvidenceUnchanged $PriorP4Before
            $blocked['prior_publication4_after'] = $blockedPriorP4After
            $blocked['prior_publication4_unchanged'] = $true
        }
        catch {
            $blocked['prior_publication4_unchanged'] = $false
            $blocked['prior_publication4_manifest_error'] = $_.Exception.Message
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
        [Console]::Out.Write((Get-Content -LiteralPath $script:StatePath -Raw))
    }
    throw $terminalException
}
finally {
    try {
        if (-not $script:PermissionCleanupAttempted) { Remove-DisposableCodexHome }
    }
    finally {
        foreach ($name in $EnvironmentNames) {
            $value = $OriginalEnvironment[$name]
            if ($null -eq $value) { Remove-Item -Path ('Env:' + $name) -ErrorAction SilentlyContinue }
            else { Set-Item -Path ('Env:' + $name) -Value $value }
        }
        Set-Location $previous
    }
}
