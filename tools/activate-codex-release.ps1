<#
.SYNOPSIS
    Activates a qualified Codex release with a durable, reversible operation record.

.DESCRIPTION
    Validates a retained qualified release, previews its exact effect on one Codex
    home, applies the preview through install-skill-mesh.ps1, and can restore the
    exact preimage.  The installer deliberately has no exact activation rollback;
    this wrapper owns the durable preimage and operation status under -StateRoot.

    release_manifest_sha256 is SHA-256 of UTF-8 (without BOM) canonical manifest
    bytes.  Its lines, sorted ordinally by release-relative artifact path, are
    "dist/codex/... <sha256>\n".

.PARAMETER Mode
    inspect, preview, apply, or rollback.  Missing values are rejected without
    prompting.

.PARAMETER ReleaseDir
    Retained release directory containing release.json and dist/codex.

.PARAMETER TargetHome
    Consumer home to inspect, preview, or activate.

.PARAMETER StateRoot
    Private durable state directory for locks, operations, and selector evidence.

.PARAMETER OperationId
    UUID4 produced by preview and required by apply or rollback.

.EXAMPLE
    powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode preview -ReleaseDir $releaseDir -TargetHome $targetHome -StateRoot $stateRoot

.EXAMPLE
    powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode rollback -StateRoot $stateRoot -OperationId $operationId

.NOTES
    SKILL_MESH_CODEX_ACTIVATION_TEST_FAIL_SELECTOR_PUBLISH=1 is a test-only seam.
    When set exactly to 1, it fails immediately before selector publication.  It is
    inert otherwise and exists only to exercise recovery after a verified install.
    ASCII-only, no BOM, Windows PowerShell 5.1 compatible.
#>

[CmdletBinding()]
param(
    [ValidateSet('inspect', 'preview', 'apply', 'rollback', '')]
    [string]$Mode = '',

    [string]$ReleaseDir = '',
    [string]$TargetHome = '',
    [string]$StateRoot = '',
    [string]$OperationId = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$TOOLS_DIR = $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $TOOLS_DIR
$INSTALLER = Join-Path $TOOLS_DIR 'install-skill-mesh.ps1'
$PATH_GUARD = Join-Path $REPO_ROOT 'runtime\path-guard.ps1'
$DISCOVERY = Join-Path $TOOLS_DIR 'skill-mesh-discovery.ps1'
$PROVENANCE = Join-Path $TOOLS_DIR 'skill-mesh-provenance.ps1'
$TRANSACTION = Join-Path $TOOLS_DIR 'skill-mesh-transaction.ps1'
$UTF8_NO_BOM = New-Object System.Text.UTF8Encoding($false)
$LEDGER_NAME = '.skill-mesh-install.json'

. $PATH_GUARD
. $DISCOVERY
. $PROVENANCE
. $TRANSACTION

if ([string]::IsNullOrWhiteSpace((Get-SkillMeshMarker))) {
    throw 'activate-codex-release: shared provenance marker is unavailable.'
}

function Stop-ActivationRefusal([string]$Message) {
    throw (New-Object System.InvalidOperationException(
        "activate-codex-release: REFUSING -- $Message"))
}

function Get-ObjectField($Object, [string]$Name, $Default = $null) {
    if ($null -eq $Object) { return $Default }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Test-OrdinalEquals([string]$Left, [string]$Right) {
    return [string]::Equals($Left, $Right, [System.StringComparison]::Ordinal)
}

function Test-OrdinalIgnoreCaseEquals([string]$Left, [string]$Right) {
    return [string]::Equals($Left, $Right, [System.StringComparison]::OrdinalIgnoreCase)
}

function Test-OrdinalContains($Values, [string]$Wanted) {
    foreach ($value in @($Values)) {
        if (Test-OrdinalEquals ([string]$value) $Wanted) { return $true }
    }
    return $false
}

function Get-OrdinalSortedStrings($Values) {
    $items = New-Object 'System.Collections.Generic.List[string]'
    foreach ($value in @($Values)) { [void]$items.Add([string]$value) }
    $items.Sort([System.StringComparer]::Ordinal)
    return , $items.ToArray()
}

function Get-TextSha256([string]$Text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $UTF8_NO_BOM.GetBytes($Text)
        $digest = $sha.ComputeHash($bytes)
        return ([System.BitConverter]::ToString($digest) -replace '-', '').ToLowerInvariant()
    } finally {
        $sha.Dispose()
    }
}

function Assert-NoPlaceholder([string]$Value, [string]$Name) {
    if (-not [string]::IsNullOrEmpty($Value) -and
        ($Value.Contains('<') -or $Value.Contains('>'))) {
        Stop-ActivationRefusal "$Name contains an obvious placeholder path."
    }
}

function Assert-NoReparseAncestor([string]$Path) {
    $full = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetPathRoot($full)
    $rest = $full.Substring($root.Length)
    $segments = $rest.Split([char[]]@('\', '/'),
        [System.StringSplitOptions]::RemoveEmptyEntries)
    $current = $root
    foreach ($segment in $segments) {
        $current = Join-Path $current $segment
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                Stop-ActivationRefusal 'a target or state path has a reparse-point ancestor.'
            }
        }
    }
}

function Resolve-ActivationPath([string]$Path, [string]$Root) {
    Assert-NoReparseAncestor $Root
    Assert-NoReparseAncestor $Path
    try {
        return (Resolve-SafePath -Path $Path -AllowedRoots @($Root))
    } catch {
        Stop-ActivationRefusal $_.Exception.Message
    }
}

function Assert-SafeTargetAndParent([string]$Path, [string]$Root) {
    $safe = Resolve-ActivationPath $Path $Root
    $parent = Split-Path -Parent $safe
    if ([string]::IsNullOrWhiteSpace($parent)) {
        Stop-ActivationRefusal 'a target path has no parent.'
    }
    [void](Resolve-ActivationPath $parent $Root)
    return $safe
}

function Ensure-ActivationDirectory([string]$Path, [string]$Root) {
    $safe = Resolve-ActivationPath $Path $Root
    if (Test-Path -LiteralPath $safe) {
        if (-not (Test-Path -LiteralPath $safe -PathType Container)) {
            Stop-ActivationRefusal 'a required state directory is not a directory.'
        }
        return $safe
    }
    $parent = Split-Path -Parent $safe
    if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
        Ensure-ActivationDirectory $parent $Root | Out-Null
    }
    if (Test-PathUnderRoot -Candidate $parent -Root $Root) {
        [void](Assert-SafeTargetAndParent $safe $Root)
    } else {
        # Creating the state root itself necessarily writes beneath its already
        # existing parent, which is outside the new root. Guard that parent too.
        Assert-NoReparseAncestor $parent
        [void](Resolve-SafePath -Path $parent -AllowedRoots @($parent))
        [void](Resolve-ActivationPath $safe $Root)
    }
    New-Item -ItemType Directory -Path $safe -ErrorAction Stop | Out-Null
    return (Resolve-ActivationPath $safe $Root)
}

function Write-ActivationAtomicBytes([string]$Path, [byte[]]$Bytes, [string]$Root) {
    # One same-volume, process-unique sibling temp plus File.Replace/File.Move makes
    # every metadata publication all-or-old, never a partially written JSON record.
    $safe = Assert-SafeTargetAndParent $Path $Root
    $parent = Split-Path -Parent $safe
    Ensure-ActivationDirectory $parent $Root | Out-Null
    $safe = Assert-SafeTargetAndParent $safe $Root
    if ((Test-Path -LiteralPath $safe) -and -not (Test-Path -LiteralPath $safe -PathType Leaf)) {
        Stop-ActivationRefusal 'a state file destination is not a regular file.'
    }
    $temp = Join-Path $parent ('.activation-' + $PID + '-' + [guid]::NewGuid().ToString('N') + '.tmp')
    $backup = $temp + '.bak'
    try {
        [void](Assert-SafeTargetAndParent $temp $Root)
        [System.IO.File]::WriteAllBytes($temp, $Bytes)
        [void](Assert-SafeTargetAndParent $safe $Root)
        if (Test-Path -LiteralPath $safe -PathType Leaf) {
            [void](Assert-SafeTargetAndParent $backup $Root)
            [System.IO.File]::Replace($temp, $safe, $backup)
        } else {
            [System.IO.File]::Move($temp, $safe)
        }
    } finally {
        if (Test-Path -LiteralPath $temp -PathType Leaf) {
            Remove-Item -LiteralPath $temp -Force
        }
        if (Test-Path -LiteralPath $backup -PathType Leaf) {
            Remove-Item -LiteralPath $backup -Force
        }
    }
}

function Write-ActivationAtomicJson([string]$Path, $Object, [string]$Root) {
    $json = $Object | ConvertTo-Json -Depth 32
    Write-ActivationAtomicBytes $Path $UTF8_NO_BOM.GetBytes($json) $Root
}

function Remove-ActivationFile([string]$Path, [string]$Root) {
    $safe = Assert-SafeTargetAndParent $Path $Root
    if (-not (Test-Path -LiteralPath $safe)) { return }
    if (-not (Test-Path -LiteralPath $safe -PathType Leaf)) {
        Stop-ActivationRefusal 'a planned file became a non-file.'
    }
    Remove-Item -LiteralPath $safe -Force
}

function Read-OptionalFileState([string]$Path, [string]$Root, [string]$Label) {
    $safe = Resolve-ActivationPath $Path $Root
    if (-not (Test-Path -LiteralPath $safe)) {
        return [PSCustomObject]@{ present = $false; sha256 = $null; bytes = $null; path = $safe }
    }
    if (-not (Test-Path -LiteralPath $safe -PathType Leaf)) {
        Stop-ActivationRefusal "$Label is not a regular file."
    }
    return [PSCustomObject]@{
        present = $true
        sha256 = Get-SkillMeshFileSha256 $safe
        bytes = [System.IO.File]::ReadAllBytes($safe)
        path = $safe
    }
}

function Get-HomeId([string]$HomeAbs) {
    $normalized = (Get-CanonicalRealPath -InputPath $HomeAbs).ToUpperInvariant()
    return (Get-TextSha256 $normalized)
}

function Enter-ActivationLock([string]$StateAbs, [string]$HomeAbs) {
    $locks = Ensure-ActivationDirectory (Join-Path $StateAbs 'locks') $StateAbs
    $lockPath = Join-Path $locks ((Get-HomeId $HomeAbs) + '.lock')
    $safe = Assert-SafeTargetAndParent $lockPath $StateAbs
    try {
        return ([System.IO.File]::Open($safe, [System.IO.FileMode]::OpenOrCreate,
            [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None))
    } catch {
        Stop-ActivationRefusal 'lock contention or a stale lock was found; do not break or delete it, retry after the other operation exits.'
    }
}

function Get-OperationDirectory([string]$StateAbs, [string]$Id) {
    if ([string]::IsNullOrWhiteSpace($Id) -or
        -not ($Id -cmatch '\A[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\z')) {
        Stop-ActivationRefusal 'OperationId must be a lowercase UUID4 minted by preview.'
    }
    return (Resolve-ActivationPath (Join-Path (Join-Path $StateAbs 'operations') $Id) $StateAbs)
}

function Read-JsonFile([string]$Path, [string]$Root, [string]$Label) {
    $state = Read-OptionalFileState $Path $Root $Label
    if (-not $state.present) { Stop-ActivationRefusal "$Label is absent." }
    try {
        return ($UTF8_NO_BOM.GetString($state.bytes) | ConvertFrom-Json)
    } catch {
        Stop-ActivationRefusal "$Label is not valid JSON."
    }
}

function Get-ReleaseInfo([string]$InputDir) {
    $release = [System.IO.Path]::GetFullPath($InputDir)
    if (-not (Test-Path -LiteralPath $release -PathType Container)) {
        Stop-ActivationRefusal 'ReleaseDir is not a directory.'
    }
    $recordPath = Join-Path $release 'release.json'
    if (-not (Test-Path -LiteralPath $recordPath -PathType Leaf)) {
        Stop-ActivationRefusal 'release.json is absent.'
    }
    try { $record = [System.IO.File]::ReadAllText($recordPath, $UTF8_NO_BOM) | ConvertFrom-Json }
    catch { Stop-ActivationRefusal 'release.json is not valid JSON.' }
    if ([string](Get-ObjectField $record 'schema_version') -cne '1') {
        Stop-ActivationRefusal 'release.json schema_version must be 1.'
    }
    if (-not (Test-OrdinalEquals ([string](Get-ObjectField $record 'product')) 'skill-mesh')) {
        Stop-ActivationRefusal 'release.json product must be skill-mesh.'
    }
    if (-not (Test-OrdinalEquals ([string](Get-ObjectField $record 'qualification')) 'QUALIFIED')) {
        Stop-ActivationRefusal 'release.json qualification must be QUALIFIED.'
    }
    if (-not (Test-OrdinalContains (Get-ObjectField $record 'providers' @()) 'codex')) {
        Stop-ActivationRefusal 'release.json providers does not contain codex.'
    }
    $version = [string](Get-ObjectField $record 'version')
    if ([string]::IsNullOrWhiteSpace($version)) {
        Stop-ActivationRefusal 'release.json version is absent.'
    }
    $profile = Join-Path $release 'dist\codex'
    if (-not (Test-Path -LiteralPath $profile -PathType Container)) {
        Stop-ActivationRefusal 'release dist/codex is absent or is not a directory.'
    }
    $recorded = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
    $artifacts = Get-ObjectField $record 'artifacts' $null
    if ($null -eq $artifacts) { Stop-ActivationRefusal 'release.json artifacts is absent.' }
    foreach ($row in @($artifacts)) {
        $rel = [string](Get-ObjectField $row 'path')
        if (-not $rel.StartsWith('dist/codex/', [System.StringComparison]::Ordinal)) { continue }
        $tail = $rel.Substring('dist/codex/'.Length)
        $hash = [string](Get-ObjectField $row 'sha256')
        if ([string]::IsNullOrWhiteSpace($tail) -or $tail.Contains('\') -or
            @($tail.Split('/') | Where-Object { $_ -eq '' -or $_ -eq '.' -or $_ -eq '..' }).Count -ne 0 -or
            -not ($hash -cmatch '\A[0-9a-f]{64}\z')) {
            Stop-ActivationRefusal "release artifact row is malformed: $rel"
        }
        if ($recorded.ContainsKey($rel)) {
            Stop-ActivationRefusal "release.json has duplicate codex artifact: $rel"
        }
        [void]$recorded.Add($rel, $hash)
        $file = Join-Path $release ($rel -replace '/', '\')
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
            Stop-ActivationRefusal "recorded codex artifact is missing: $rel"
        }
        $actual = Get-SkillMeshFileSha256 $file
        if (-not (Test-OrdinalEquals $actual $hash)) {
            Stop-ActivationRefusal "recorded codex artifact hash differs: $rel"
        }
    }
    $onDisk = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
    foreach ($file in @(Get-ChildItem -LiteralPath $profile -Recurse -File | Sort-Object FullName)) {
        $tail = $file.FullName.Substring($profile.Length).TrimStart('\', '/') -replace '\\', '/'
        $rel = 'dist/codex/' + $tail
        [void]$onDisk.Add($rel, (Get-SkillMeshFileSha256 $file.FullName))
    }
    $missing = @(); $extra = @()
    foreach ($rel in $recorded.Keys) { if (-not $onDisk.ContainsKey($rel)) { $missing += $rel } }
    foreach ($rel in $onDisk.Keys) { if (-not $recorded.ContainsKey($rel)) { $extra += $rel } }
    if ($missing.Count -ne 0 -or $extra.Count -ne 0) {
        Stop-ActivationRefusal ('dist/codex artifact set differs from release.json (missing: ' +
            ($missing -join ', ') + '; extra: ' + ($extra -join ', ') + ').')
    }
    if ($recorded.Count -eq 0) { Stop-ActivationRefusal 'release contains no codex artifacts.' }
    $manifest = ''
    $desired = @()
    foreach ($rel in (Get-OrdinalSortedStrings $recorded.Keys)) {
        $hash = $recorded[$rel]
        $tail = $rel.Substring('dist/codex/'.Length)
        $manifest += $rel + ' ' + $hash + "`n"
        $desired += [PSCustomObject]@{
            release_rel = $rel; profile_rel = $tail; sha256 = $hash
            source = Join-Path $release ($rel -replace '/', '\')
        }
    }
    return [PSCustomObject]@{
        release_dir = $release; record = $record; profile = $profile; desired = $desired
        release_id = 'skill-mesh/' + $version; manifest_sha256 = Get-TextSha256 $manifest
    }
}

function Get-LedgerView($State) {
    if (-not $State.present) { return $null }
    try { return ($UTF8_NO_BOM.GetString($State.bytes) | ConvertFrom-Json) }
    catch { Stop-ActivationRefusal 'install ledger is not valid JSON.' }
}

function Get-CodexOwnedHashes($Ledger, [string]$CodexRoot) {
    $result = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([System.StringComparer]::Ordinal)
    if ($null -eq $Ledger) { return $result }
    if ([string](Get-ObjectField $Ledger 'ledger_version') -cne '1' -or
        -not (Test-OrdinalEquals ([string](Get-ObjectField $Ledger 'tool')) 'skill-mesh')) {
        Stop-ActivationRefusal 'install ledger is not a ledger_version 1 skill-mesh ledger.'
    }
    $installs = Get-ObjectField $Ledger 'installs' $null
    if ($null -eq $installs) { Stop-ActivationRefusal 'install ledger lacks installs.' }
    $entry = Get-ObjectField $installs 'codex' $null
    if ($null -eq $entry) { return $result }
    $files = @(Get-ObjectField $entry 'owned_files' $null)
    $hashes = Get-ObjectField $entry 'owned_file_hashes' $null
    if ($null -eq $hashes) { Stop-ActivationRefusal 'codex ledger entry lacks owned_file_hashes.' }
    $listed = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    foreach ($value in $files) {
        $rel = [string]$value
        if (-not $listed.Add($rel)) { Stop-ActivationRefusal 'codex ledger has duplicate owned_files.' }
    }
    foreach ($property in @($hashes.PSObject.Properties)) {
        $rel = [string]$property.Name; $hash = [string]$property.Value
        if (-not $listed.Contains($rel) -or -not ($hash -cmatch '\A[0-9a-f]{64}\z')) {
            Stop-ActivationRefusal 'codex ledger owned_files and owned_file_hashes are not an exact bijection.'
        }
        if (-not $rel.StartsWith($CodexRoot.TrimEnd('/') + '/', [System.StringComparison]::Ordinal) -or
            @($rel.Split('/') | Where-Object { $_ -eq '' -or $_ -eq '.' -or $_ -eq '..' }).Count -ne 0) {
            Stop-ActivationRefusal 'codex ledger contains an unsafe owned path.'
        }
        [void]$result.Add($rel, $hash)
    }
    if ($result.Count -ne $listed.Count) {
        Stop-ActivationRefusal 'codex ledger owned_files and owned_file_hashes are not an exact bijection.'
    }
    return $result
}

function Get-HomeTargetPath([string]$HomeAbs, [string]$Rel) {
    return (Resolve-ActivationPath (Join-Path $HomeAbs ($Rel -replace '/', '\')) $HomeAbs)
}

function Get-HomeSnapshot([string]$HomeAbs, $Plan, [string]$StateAbs) {
    $snapshot = @{}
    foreach ($row in @($Plan)) {
        $rel = [string](Get-ObjectField $row 'rel')
        $snapshot[$rel] = Read-OptionalFileState (Get-HomeTargetPath $HomeAbs $rel) $HomeAbs "planned path $rel"
    }
    $ledger = Read-OptionalFileState (Join-Path $HomeAbs $LEDGER_NAME) $HomeAbs 'install ledger'
    $selector = Read-OptionalFileState (Join-Path $StateAbs 'current-codex.json') $StateAbs 'current selector'
    return [PSCustomObject]@{ files = $snapshot; ledger = $ledger; selector = $selector }
}

function Get-UnrelatedInstallsJson($Ledger) {
    if ($null -eq $Ledger) { return @{} }
    $out = @{}
    $installs = Get-ObjectField $Ledger 'installs' $null
    if ($null -eq $installs) { return $out }
    foreach ($property in @($installs.PSObject.Properties)) {
        if (-not (Test-OrdinalEquals $property.Name 'codex')) {
            $out[$property.Name] = ($property.Value | ConvertTo-Json -Depth 32 -Compress)
        }
    }
    return $out
}

function Test-UnrelatedInstallsEqual($Before, $After) {
    $left = Get-UnrelatedInstallsJson $Before; $right = Get-UnrelatedInstallsJson $After
    if ($left.Count -ne $right.Count) { return $false }
    foreach ($name in $left.Keys) {
        if (-not $right.ContainsKey($name) -or -not (Test-OrdinalEquals $left[$name] $right[$name])) { return $false }
    }
    return $true
}

function Get-PreviewPath([string]$OperationDir) { return (Join-Path $OperationDir 'preview.json') }

function Read-Operation([string]$StateAbs, [string]$Id) {
    $dir = Get-OperationDirectory $StateAbs $Id
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) {
        Stop-ActivationRefusal 'operation id is unknown.'
    }
    $preview = Read-JsonFile (Get-PreviewPath $dir) $StateAbs 'operation preview.json'
    if ([string](Get-ObjectField $preview 'operation_id') -cne $Id) {
        Stop-ActivationRefusal 'operation preview does not bind its directory id.'
    }
    return [PSCustomObject]@{ dir = $dir; preview = $preview }
}

function Write-OperationPreview($Operation, [string]$StateAbs) {
    Write-ActivationAtomicJson (Get-PreviewPath $Operation.dir) $Operation.preview $StateAbs
}

function Set-OperationStatus($Operation, [string]$Status, [string]$Stage, [string]$StateAbs) {
    $Operation.preview | Add-Member -NotePropertyName status -NotePropertyValue $Status -Force
    if ([string]::IsNullOrWhiteSpace($Stage)) {
        if ($Operation.preview.PSObject.Properties['failure_stage']) {
            $Operation.preview.PSObject.Properties.Remove('failure_stage')
        }
    } else {
        $Operation.preview | Add-Member -NotePropertyName failure_stage -NotePropertyValue $Stage -Force
    }
    Write-OperationPreview $Operation $StateAbs
}

function Assert-NoUnresolvedOperation([string]$StateAbs, [string]$HomeAbs) {
    $operations = Join-Path $StateAbs 'operations'
    if (-not (Test-Path -LiteralPath $operations -PathType Container)) { return }
    foreach ($dir in @(Get-ChildItem -LiteralPath $operations -Directory)) {
        $previewPath = Join-Path $dir.FullName 'preview.json'
        if (-not (Test-Path -LiteralPath $previewPath -PathType Leaf)) { continue }
        try { $preview = [System.IO.File]::ReadAllText($previewPath, $UTF8_NO_BOM) | ConvertFrom-Json }
        catch { Stop-ActivationRefusal 'an existing operation has unreadable preview.json.' }
        if ((Test-OrdinalIgnoreCaseEquals ([string](Get-ObjectField $preview 'target_home')) $HomeAbs) -and
            (Test-OrdinalContains @('applying', 'rolling-back', 'incomplete') ([string](Get-ObjectField $preview 'status')))) {
            Stop-ActivationRefusal 'an unresolved prior operation exists for this target home.'
        }
    }
}

function New-SelectorObject($Preview) {
    return [PSCustomObject]@{
        schema_version = 1; release_id = [string]$Preview.release_id
        release_manifest_sha256 = [string]$Preview.release_manifest_sha256
        target_home = [string]$Preview.target_home; operation_id = [string]$Preview.operation_id
        verified_at = Get-SkillMeshTxUtcNow
    }
}

function Get-SelectorExpectedHash($Preview) {
    # verified_at is assigned at publication, so the durable postimage records the
    # actual selector hash immediately after writing instead of predicting this value.
    return $null
}

function Invoke-Inspect([string]$ReleaseDirValue) {
    $release = Get-ReleaseInfo $ReleaseDirValue
    $record = $release.record
    Write-Output ('release_id: ' + $release.release_id)
    foreach ($field in @('source_commit', 'source_tree', 'builder_commit', 'created_at', 'qualification')) {
        Write-Output ($field + ': ' + [string](Get-ObjectField $record $field ''))
    }
    Write-Output ('providers: ' + (@(Get-ObjectField $record 'providers' @()) -join ', '))
    Write-Output ('file_count: ' + @($release.desired).Count)
    Write-Output ('release_manifest_sha256: ' + $release.manifest_sha256)
    if (-not [string]::IsNullOrWhiteSpace($TargetHome)) {
        $homeAbs = [System.IO.Path]::GetFullPath($TargetHome)
        $ledgerPath = Join-Path $homeAbs $LEDGER_NAME
        if (-not (Test-Path -LiteralPath $ledgerPath -PathType Leaf)) {
            Write-Output 'codex_ledger: absent (owned_files: 0)'
        } else {
            try {
                $ledger = [System.IO.File]::ReadAllText($ledgerPath, $UTF8_NO_BOM) | ConvertFrom-Json
                $entry = Get-ObjectField (Get-ObjectField $ledger 'installs') 'codex' $null
                Write-Output ('codex_ledger: present (owned_files: ' + @(Get-ObjectField $entry 'owned_files' @()).Count + ')')
            } catch { Write-Output 'codex_ledger: present (owned_files: unreadable)' }
        }
    }
    if (-not [string]::IsNullOrWhiteSpace($StateRoot)) {
        $selector = Join-Path ([System.IO.Path]::GetFullPath($StateRoot)) 'current-codex.json'
        if (Test-Path -LiteralPath $selector -PathType Leaf) {
            Write-Output ('current_selector: ' + [System.IO.File]::ReadAllText($selector, $UTF8_NO_BOM))
        } else { Write-Output 'current_selector: absent' }
    }
}

function Invoke-Preview([string]$ReleaseDirValue, [string]$HomeValue, [string]$StateValue) {
    $release = Get-ReleaseInfo $ReleaseDirValue
    $homeAbs = [System.IO.Path]::GetFullPath($HomeValue)
    $state = [System.IO.Path]::GetFullPath($StateValue)
    [void](Resolve-ActivationPath $homeAbs $homeAbs)
    [void](Resolve-ActivationPath $state $state)
    $lock = $null
    try {
        $lock = Enter-ActivationLock $state $homeAbs
        Assert-NoUnresolvedOperation $state $homeAbs
        $codexRoot = Get-SkillMeshDiscoveryRoot 'codex'
        if ([string]::IsNullOrWhiteSpace($codexRoot)) { throw 'activate-codex-release: codex discovery root is unavailable.' }
        $ledgerState = Read-OptionalFileState (Join-Path $homeAbs $LEDGER_NAME) $homeAbs 'install ledger'
        $selectorState = Read-OptionalFileState (Join-Path $state 'current-codex.json') $state 'current selector'
        $ledger = Get-LedgerView $ledgerState
        $owned = Get-CodexOwnedHashes $ledger $codexRoot
        $desiredByRel = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([System.StringComparer]::Ordinal)
        foreach ($file in @($release.desired)) {
            $rel = $codexRoot.TrimEnd('/') + '/' + $file.profile_rel
            [void]$desiredByRel.Add($rel, $file)
        }
        $plan = @(); $collisions = @()
        foreach ($rel in (Get-OrdinalSortedStrings $desiredByRel.Keys)) {
            $desired = $desiredByRel[$rel]
            $current = Read-OptionalFileState (Get-HomeTargetPath $homeAbs $rel) $homeAbs "planned path $rel"
            $action = 'add'
            if ($current.present -and (Test-OrdinalEquals $current.sha256 $desired.sha256)) { $action = 'no-op' }
            elseif ($current.present) {
                if ($owned.ContainsKey($rel) -and (Test-OrdinalEquals $owned[$rel] $current.sha256)) { $action = 'update' }
                else { $collisions += $rel; continue }
            }
            $plan += [PSCustomObject]@{ rel = $rel; action = $action; current_sha256 = $current.sha256; desired_sha256 = $desired.sha256; present_before = [bool]$current.present }
        }
        if ($collisions.Count -ne 0) {
            Stop-ActivationRefusal ('foreign collision(s): ' + ((Get-OrdinalSortedStrings $collisions) -join ', '))
        }
        foreach ($rel in (Get-OrdinalSortedStrings $owned.Keys)) {
            if (-not $desiredByRel.ContainsKey($rel)) {
                $current = Read-OptionalFileState (Get-HomeTargetPath $homeAbs $rel) $homeAbs "planned path $rel"
                $plan += [PSCustomObject]@{ rel = $rel; action = 'remove'; current_sha256 = $current.sha256; desired_sha256 = $null; present_before = [bool]$current.present }
            }
        }
        $plan = @($plan | Sort-Object rel)
        $id = [guid]::NewGuid().ToString()
        $operations = Ensure-ActivationDirectory (Join-Path $state 'operations') $state
        $operationDir = Ensure-ActivationDirectory (Join-Path $operations $id) $state
        $preimage = Ensure-ActivationDirectory (Join-Path $operationDir 'preimage') $state
        $filesDir = Ensure-ActivationDirectory (Join-Path $preimage 'files') $state
        foreach ($row in @($plan)) {
            if (-not $row.present_before) { continue }
            $current = Read-OptionalFileState (Get-HomeTargetPath $homeAbs $row.rel) $homeAbs "planned path $($row.rel)"
            Write-ActivationAtomicBytes (Join-Path $filesDir ($row.rel -replace '/', '\')) $current.bytes $state
        }
        if ($ledgerState.present) { Write-ActivationAtomicBytes (Join-Path $preimage 'ledger.json') $ledgerState.bytes $state }
        if ($selectorState.present) { Write-ActivationAtomicBytes (Join-Path $preimage 'selector.json') $selectorState.bytes $state }
        $preview = [PSCustomObject]@{
            schema_version = 1; operation_id = $id; release_id = $release.release_id
            release_manifest_sha256 = $release.manifest_sha256; release_dir = $release.release_dir
            target_home = $homeAbs; created_at = Get-SkillMeshTxUtcNow; status = 'previewed'; plan = $plan
            ledger_sha256 = $ledgerState.sha256; selector_sha256 = $selectorState.sha256
        }
        Write-ActivationAtomicJson (Join-Path $operationDir 'preview.json') $preview $state
        $summary = @{}
        foreach ($row in @($plan)) { if (-not $summary.ContainsKey($row.action)) { $summary[$row.action] = 0 }; $summary[$row.action]++ }
        Write-Output ('operation_id: ' + $id)
        foreach ($action in @('add', 'update', 'remove', 'no-op')) { Write-Output ($action + ': ' + [int](Get-ObjectField $summary $action 0)) }
    } finally {
        if ($null -ne $lock) { $lock.Dispose() }
    }
}

function Assert-PreviewBinding($Operation, $Release, [string]$HomeAbs, [string]$State) {
    $preview = $Operation.preview
    if (-not (Test-OrdinalEquals ([string]$preview.status) 'previewed')) { Stop-ActivationRefusal 'operation status is not previewed.' }
    if (-not (Test-OrdinalIgnoreCaseEquals ([string]$preview.target_home) $HomeAbs)) { Stop-ActivationRefusal 'operation target_home does not match TargetHome.' }
    if (-not (Test-OrdinalEquals ([string]$preview.release_manifest_sha256) $Release.manifest_sha256)) { Stop-ActivationRefusal 'release manifest differs; take a NEW preview.' }
    $snapshot = Get-HomeSnapshot $HomeAbs @($preview.plan) $State
    foreach ($row in @($preview.plan)) {
        $current = $snapshot.files[[string]$row.rel]
        if ([bool]$row.present_before -ne [bool]$current.present -or
            -not (Test-OrdinalEquals ([string]$row.current_sha256) ([string]$current.sha256))) {
            Stop-ActivationRefusal "planned path changed after preview ($($row.rel)); take a NEW preview."
        }
    }
    if (-not (Test-OrdinalEquals ([string]$preview.ledger_sha256) ([string]$snapshot.ledger.sha256)) -or
        -not (Test-OrdinalEquals ([string]$preview.selector_sha256) ([string]$snapshot.selector.sha256))) {
        Stop-ActivationRefusal 'ledger or selector changed after preview; take a NEW preview.'
    }
    return $snapshot
}

function Invoke-InstallerForActivation([string]$HomeAbs, $Release, $Operation, [string]$State) {
    $stdout = Join-Path $Operation.dir 'installer.stdout.txt'
    $stderr = Join-Path $Operation.dir 'installer.stderr.txt'
    [void](Assert-SafeTargetAndParent $stdout $State); [void](Assert-SafeTargetAndParent $stderr $State)
    $argv = @('-NoProfile', '-File', $INSTALLER, '-Provider', 'codex', '-Home', $HomeAbs, '-DistDir', (Join-Path $Release.release_dir 'dist'))
    & powershell @argv 1> $stdout 2> $stderr
    return [PSCustomObject]@{ exit_code = $LASTEXITCODE; argv = $argv; stdout = $stdout; stderr = $stderr }
}

function Verify-Postimage($Operation, $Release, $Before, [string]$HomeAbs, [string]$State) {
    $expected = @{}
    foreach ($row in @($Operation.preview.plan)) {
        if ([string]$row.action -eq 'remove') { $expected[[string]$row.rel] = $null }
        else { $expected[[string]$row.rel] = [string]$row.desired_sha256 }
    }
    foreach ($rel in $expected.Keys) {
        $now = Read-OptionalFileState (Get-HomeTargetPath $HomeAbs $rel) $HomeAbs "postimage path $rel"
        if (-not (Test-OrdinalEquals ([string]$expected[$rel]) ([string]$now.sha256)) -or
            (($null -eq $expected[$rel]) -and $now.present)) {
            throw "activate-codex-release: postimage verification failed at $rel."
        }
    }
    $ledgerState = Read-OptionalFileState (Join-Path $HomeAbs $LEDGER_NAME) $HomeAbs 'postimage ledger'
    $ledger = Get-LedgerView $ledgerState
    $codexRoot = Get-SkillMeshDiscoveryRoot 'codex'
    $owned = Get-CodexOwnedHashes $ledger $codexRoot
    if ($owned.Count -ne $Release.desired.Count) { throw 'activate-codex-release: postimage codex ledger file count differs.' }
    foreach ($file in @($Release.desired)) {
        $rel = $codexRoot.TrimEnd('/') + '/' + $file.profile_rel
        if (-not $owned.ContainsKey($rel) -or -not (Test-OrdinalEquals $owned[$rel] $file.sha256)) {
            throw 'activate-codex-release: postimage codex ledger differs from desired release.'
        }
    }
    if (-not (Test-UnrelatedInstallsEqual (Get-LedgerView $Before.ledger) $ledger)) {
        throw 'activate-codex-release: unrelated ledger profiles changed.'
    }
    $postDir = Ensure-ActivationDirectory (Join-Path $Operation.dir 'postimage') $State
    Write-ActivationAtomicBytes (Join-Path $postDir 'ledger.json') $ledgerState.bytes $State
    $files = [ordered]@{}
    foreach ($rel in (Get-OrdinalSortedStrings $expected.Keys)) { $files[$rel] = $expected[$rel] }
    $post = [PSCustomObject]@{ schema_version = 1; files = $files; ledger_sha256 = $ledgerState.sha256; selector_sha256 = $null }
    Write-ActivationAtomicJson (Join-Path $Operation.dir 'postimage.json') $post $State
    return [PSCustomObject]@{ ledger = $ledgerState; post = $post }
}

function Write-Receipt($Operation, $Receipt, [string]$State) {
    Write-ActivationAtomicJson (Join-Path $Operation.dir 'receipt.json') $Receipt $State
}

function Invoke-Apply([string]$ReleaseDirValue, [string]$HomeValue, [string]$StateValue, [string]$Id) {
    $release = Get-ReleaseInfo $ReleaseDirValue
    $homeAbs = [System.IO.Path]::GetFullPath($HomeValue); $state = [System.IO.Path]::GetFullPath($StateValue)
    [void](Resolve-ActivationPath $homeAbs $homeAbs); [void](Resolve-ActivationPath $state $state)
    $operation = Read-Operation $state $Id
    $lock = $null; $stage = 'preview binding'; $started = Get-SkillMeshTxUtcNow
    try {
        $lock = Enter-ActivationLock $state $homeAbs
        $before = Assert-PreviewBinding $operation $release $homeAbs $state
        $stage = 'status publication'; Set-OperationStatus $operation 'applying' '' $state
        $stage = 'installer'; $installer = Invoke-InstallerForActivation $homeAbs $release $operation $state
        if ($installer.exit_code -ne 0) { throw "activate-codex-release: installer failed with exit $($installer.exit_code)." }
        $stage = 'postimage verification'; $verified = Verify-Postimage $operation $release $before $homeAbs $state
        $stage = 'selector publication'
        if ([Environment]::GetEnvironmentVariable('SKILL_MESH_CODEX_ACTIVATION_TEST_FAIL_SELECTOR_PUBLISH') -ceq '1') {
            throw 'activate-codex-release: TEST SEAM -- selector publication failure.'
        }
        $selectorPath = Join-Path $state 'current-codex.json'
        $selector = New-SelectorObject $operation.preview
        Write-ActivationAtomicJson $selectorPath $selector $state
        $selectorState = Read-OptionalFileState $selectorPath $state 'published selector'
        $verified.post | Add-Member -NotePropertyName selector_sha256 -NotePropertyValue $selectorState.sha256 -Force
        Write-ActivationAtomicJson (Join-Path $operation.dir 'postimage.json') $verified.post $state
        $stage = 'status publication'; Set-OperationStatus $operation 'applied' '' $state
        Write-Receipt $operation ([PSCustomObject]@{
            schema_version = 1; operation_id = $Id; started_at = $started; completed_at = Get-SkillMeshTxUtcNow
            argv = $installer.argv; installer_exit_code = $installer.exit_code
            evidence = [PSCustomObject]@{ stdout = 'installer.stdout.txt'; stderr = 'installer.stderr.txt'; postimage = 'postimage.json' }
        }) $state
        Write-Output ('applied operation_id: ' + $Id)
    } catch {
        if ($_.Exception.Message.StartsWith('activate-codex-release: REFUSING --',
                [System.StringComparison]::Ordinal)) {
            throw
        }
        $failure = $_.Exception.Message
        try { Set-OperationStatus $operation 'incomplete' $stage $state } catch { $failure += ' Also failed to record incomplete status: ' + $_.Exception.Message }
        [Console]::Error.WriteLine('activate-codex-release: INCOMPLETE at ' + $stage + '. ' + $failure)
        [Console]::Error.WriteLine('Recover with: powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode rollback -StateRoot <stateRoot> -OperationId ' + $Id)
        exit 1
    } finally {
        if ($null -ne $lock) { $lock.Dispose() }
    }
}

function Get-PreimageState($Operation, $Row, [string]$State) {
    if (-not [bool]$Row.present_before) { return [PSCustomObject]@{ present = $false; sha256 = $null } }
    $path = Join-Path (Join-Path (Join-Path $Operation.dir 'preimage') 'files') ([string]$Row.rel -replace '/', '\')
    $saved = Read-OptionalFileState $path $State 'preimage file'
    if (-not $saved.present) { throw 'activate-codex-release: preimage is incomplete.' }
    return [PSCustomObject]@{ present = $true; sha256 = $saved.sha256; bytes = $saved.bytes }
}

function Test-CurrentMatchesOne($Current, $First, $Second) {
    $a = ([bool]$Current.present -eq [bool]$First.present -and
        (Test-OrdinalEquals ([string]$Current.sha256) ([string]$First.sha256)))
    $b = $false
    if ($null -ne $Second) {
        $b = ([bool]$Current.present -eq [bool]$Second.present -and
            (Test-OrdinalEquals ([string]$Current.sha256) ([string]$Second.sha256)))
    }
    return ($a -or $b)
}

function Get-Postimage($Operation, [string]$State, [switch]$Required) {
    $path = Join-Path $Operation.dir 'postimage.json'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        if ($Required) { Stop-ActivationRefusal 'applied operation lacks postimage.json.' }
        return $null
    }
    return (Read-JsonFile $path $State 'postimage.json')
}

function Assert-RollbackDriftFree($Operation, [string]$HomeAbs, [string]$State) {
    $post = Get-Postimage $Operation $State -Required:([string]$Operation.preview.status -eq 'applied')
    foreach ($row in @($Operation.preview.plan)) {
        $pre = Get-PreimageState $Operation $row $State
        $current = Read-OptionalFileState (Get-HomeTargetPath $HomeAbs $row.rel) $HomeAbs "rollback path $($row.rel)"
        $postState = $null
        if ($null -ne $post) {
            $postHash = Get-ObjectField (Get-ObjectField $post 'files') ([string]$row.rel) $null
            $postState = [PSCustomObject]@{ present = ($null -ne $postHash); sha256 = $postHash }
        }
        if ([string]$Operation.preview.status -eq 'applied') {
            if (-not (Test-CurrentMatchesOne $current $postState $null)) { Stop-ActivationRefusal "post-apply drift at $($row.rel)." }
        } elseif (-not (Test-CurrentMatchesOne $current $pre $postState)) {
            Stop-ActivationRefusal "intervening drift at $($row.rel)."
        }
    }
    $preLedger = [PSCustomObject]@{ present = ($null -ne $Operation.preview.ledger_sha256); sha256 = $Operation.preview.ledger_sha256 }
    $preSelector = [PSCustomObject]@{ present = ($null -ne $Operation.preview.selector_sha256); sha256 = $Operation.preview.selector_sha256 }
    $currentLedger = Read-OptionalFileState (Join-Path $HomeAbs $LEDGER_NAME) $HomeAbs 'rollback ledger'
    $currentSelector = Read-OptionalFileState (Join-Path $State 'current-codex.json') $State 'rollback selector'
    $postLedger = $null; $postSelector = $null
    if ($null -ne $post) {
        $postLedger = [PSCustomObject]@{ present = ($null -ne $post.ledger_sha256); sha256 = $post.ledger_sha256 }
        $postSelector = [PSCustomObject]@{ present = ($null -ne $post.selector_sha256); sha256 = $post.selector_sha256 }
    }
    if ([string]$Operation.preview.status -eq 'applied') {
        if (-not (Test-CurrentMatchesOne $currentLedger $postLedger $null) -or -not (Test-CurrentMatchesOne $currentSelector $postSelector $null)) { Stop-ActivationRefusal 'post-apply ledger or selector drift.' }
    } elseif (-not (Test-CurrentMatchesOne $currentLedger $preLedger $postLedger) -or -not (Test-CurrentMatchesOne $currentSelector $preSelector $postSelector)) {
        Stop-ActivationRefusal 'intervening ledger or selector drift.'
    }
}

function Restore-Preimage($Operation, [string]$HomeAbs, [string]$State) {
    foreach ($row in @($Operation.preview.plan)) {
        $target = Get-HomeTargetPath $HomeAbs $row.rel
        if ([bool]$row.present_before) {
            $saved = Get-PreimageState $Operation $row $State
            Write-ActivationAtomicBytes $target $saved.bytes $HomeAbs
        } else { Remove-ActivationFile $target $HomeAbs }
    }
    $preDir = Join-Path $Operation.dir 'preimage'
    $ledgerTarget = Join-Path $HomeAbs $LEDGER_NAME
    if ($null -ne $Operation.preview.ledger_sha256) {
        $saved = Read-OptionalFileState (Join-Path $preDir 'ledger.json') $State 'preimage ledger'
        if (-not $saved.present) { throw 'activate-codex-release: preimage ledger is absent.' }
        Write-ActivationAtomicBytes $ledgerTarget $saved.bytes $HomeAbs
    } else { Remove-ActivationFile $ledgerTarget $HomeAbs }
    $selectorTarget = Join-Path $State 'current-codex.json'
    if ($null -ne $Operation.preview.selector_sha256) {
        $saved = Read-OptionalFileState (Join-Path $preDir 'selector.json') $State 'preimage selector'
        if (-not $saved.present) { throw 'activate-codex-release: preimage selector is absent.' }
        Write-ActivationAtomicBytes $selectorTarget $saved.bytes $State
    } else { Remove-ActivationFile $selectorTarget $State }
}

function Assert-PreimageRestored($Operation, [string]$HomeAbs, [string]$State) {
    foreach ($row in @($Operation.preview.plan)) {
        $expected = Get-PreimageState $Operation $row $State
        $actual = Read-OptionalFileState (Get-HomeTargetPath $HomeAbs $row.rel) $HomeAbs "restored path $($row.rel)"
        if (-not (Test-CurrentMatchesOne $actual $expected $null)) { throw "activate-codex-release: restoration verification failed at $($row.rel)." }
    }
    $ledger = Read-OptionalFileState (Join-Path $HomeAbs $LEDGER_NAME) $HomeAbs 'restored ledger'
    $selector = Read-OptionalFileState (Join-Path $State 'current-codex.json') $State 'restored selector'
    if (-not (Test-OrdinalEquals ([string]$ledger.sha256) ([string]$Operation.preview.ledger_sha256)) -or
        -not (Test-OrdinalEquals ([string]$selector.sha256) ([string]$Operation.preview.selector_sha256))) {
        throw 'activate-codex-release: restoration verification failed for ledger or selector.'
    }
}

function Invoke-Rollback([string]$StateValue, [string]$Id, [string]$OptionalHome) {
    $state = [System.IO.Path]::GetFullPath($StateValue)
    [void](Resolve-ActivationPath $state $state)
    $operation = Read-Operation $state $Id
    $status = [string]$operation.preview.status
    if ($status -eq 'previewed') { Stop-ActivationRefusal 'a previewed operation has nothing to roll back.' }
    if ($status -eq 'rolled-back') { Stop-ActivationRefusal 'operation was already rolled back.' }
    if ($status -ne 'applied' -and $status -ne 'incomplete') { Stop-ActivationRefusal 'operation is not eligible for rollback.' }
    $homeAbs = [string]$operation.preview.target_home
    if (-not [string]::IsNullOrWhiteSpace($OptionalHome) -and
        -not (Test-OrdinalIgnoreCaseEquals ([System.IO.Path]::GetFullPath($OptionalHome)) $homeAbs)) {
        Stop-ActivationRefusal 'TargetHome does not match the operation target_home.'
    }
    [void](Resolve-ActivationPath $homeAbs $homeAbs)
    $lock = $null
    try {
        $lock = Enter-ActivationLock $state $homeAbs
        Assert-RollbackDriftFree $operation $homeAbs $state
        Set-OperationStatus $operation 'rolling-back' '' $state
        Restore-Preimage $operation $homeAbs $state
        Assert-PreimageRestored $operation $homeAbs $state
        Set-OperationStatus $operation 'rolled-back' '' $state
        Write-Receipt $operation ([PSCustomObject]@{ schema_version = 1; operation_id = $Id; rolled_back_at = Get-SkillMeshTxUtcNow; evidence = 'preimage' }) $state
        Write-Output ('rolled back operation_id: ' + $Id)
    } finally {
        if ($null -ne $lock) { $lock.Dispose() }
    }
}

try {
    foreach ($pair in @(@($ReleaseDir, 'ReleaseDir'), @($TargetHome, 'TargetHome'), @($StateRoot, 'StateRoot'), @($OperationId, 'OperationId'))) {
        Assert-NoPlaceholder ([string]$pair[0]) ([string]$pair[1])
    }
    if ([string]::IsNullOrWhiteSpace($Mode)) { Stop-ActivationRefusal 'Mode is required.' }
    switch ($Mode) {
        'inspect' {
            if ([string]::IsNullOrWhiteSpace($ReleaseDir)) { Stop-ActivationRefusal 'inspect requires ReleaseDir.' }
            Invoke-Inspect $ReleaseDir
        }
        'preview' {
            if ([string]::IsNullOrWhiteSpace($ReleaseDir) -or [string]::IsNullOrWhiteSpace($TargetHome) -or [string]::IsNullOrWhiteSpace($StateRoot)) { Stop-ActivationRefusal 'preview requires ReleaseDir, TargetHome, and StateRoot.' }
            Invoke-Preview $ReleaseDir $TargetHome $StateRoot
        }
        'apply' {
            if ([string]::IsNullOrWhiteSpace($ReleaseDir) -or [string]::IsNullOrWhiteSpace($TargetHome) -or [string]::IsNullOrWhiteSpace($StateRoot) -or [string]::IsNullOrWhiteSpace($OperationId)) { Stop-ActivationRefusal 'apply requires ReleaseDir, TargetHome, StateRoot, and OperationId.' }
            Invoke-Apply $ReleaseDir $TargetHome $StateRoot $OperationId
        }
        'rollback' {
            if ([string]::IsNullOrWhiteSpace($StateRoot) -or [string]::IsNullOrWhiteSpace($OperationId)) { Stop-ActivationRefusal 'rollback requires StateRoot and OperationId.' }
            Invoke-Rollback $StateRoot $OperationId $TargetHome
        }
    }
    exit 0
} catch {
    $message = $_.Exception.Message
    [Console]::Error.WriteLine($message)
    if ($message.StartsWith('activate-codex-release: REFUSING --', [System.StringComparison]::Ordinal)) { exit 2 }
    exit 1
}
