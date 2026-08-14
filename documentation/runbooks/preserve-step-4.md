# Preserve Skill Mesh Step 4

**Status:** Goal A bootstrap runbook — execution requires Abraham's Goal A approval

## Inputs

- `RecoveryRoot`: `%LOCALAPPDATA%\SkillMesh\Recovery`
- Repository root: the exact result of `git rev-parse --show-toplevel` when run inside Skill Mesh
- Expected Step 4 base: `111fc2ba1cce1621811073b87a44bf9b4a897003`

`RecoveryRoot` must not equal, contain, or sit inside any path reported by `git worktree list --porcelain`. It must not resolve through a link or reparse point into a Git worktree. The destination directory must not already exist.

## Run identifier

Create `RunId` as UTC `yyyyMMddTHHmmssZ` plus eight lowercase hexadecimal characters from a cryptographic random value. Example: `20260814T011530Z-a1b2c3d4`.

`RunId` must be unique within `RecoveryRoot`. Use only ASCII letters, digits, one `T`, one `Z`, and hyphens. Runners use it in directory names, report names, and record fields.

## Required source set

The recovery set is the exact `Files` list in recovery-plan Step 72. Before copying, resolve every path and stop if a file is missing.

Also record all existing Skill Mesh worktrees. Divergent worktrees on branches `build-step-1786408322` and `fix/plan-expedite-explicit-handoff` existed during plan review. Record their resolved paths; do not remove or change them.

## Procedure

1. Resolve `RecoveryRoot` and every Git worktree path. Stop on overlap or a reparse ambiguity.
2. Create only `<RecoveryRoot>\skill-mesh-step-4-<RunId>`.
3. Write `base-sha.txt`, `git-status.txt`, `git-diff-stat.txt`, and `git-worktrees.txt`.
4. Write `tracked.patch` with `git diff --binary 111fc2b --` for the four tracked Step 4 files.
5. Copy every untracked planning artifact into `untracked\` while preserving repository-relative paths.
6. Copy the four current tracked files into `working-files\` while preserving repository-relative paths.
7. Export the exact base into an isolated verification copy inside the recovery directory.
8. Run `git apply --check <tracked.patch>` there. This proves semantic applicability; it does not prove original working-file line endings.
9. Replace the four patched files with their authoritative byte copies from `working-files\`.
10. Add the copied untracked files to the verification copy. Compare every restored SHA-256 with the recorded source hashes.
11. Re-hash the original source files and Git index. Prove that the source worktree and index did not change.
12. Write `manifest.json` atomically from a temporary file. Then replace the final file.
13. Keep the verification copy inside the recovery directory as evidence. Keep the recovery directory.

Use native PowerShell path APIs and explicit literal paths. Do not use `git add`, `git commit`, `git reset`, `git restore`, `git clean`, an installer, or another shell for file deletion.

## Copy-paste bootstrap

Run the following block from the Skill Mesh repository root. The block writes only below the validated recovery destination. It keeps the verification copy as evidence and removes nothing.

```powershell
$ErrorActionPreference = 'Stop'
$expectedBase = '111fc2ba1cce1621811073b87a44bf9b4a897003'
$skillMeshRoot = [IO.Path]::GetFullPath((& git --no-optional-locks rev-parse --show-toplevel).Trim())
$gitIndexPath = (& git --no-optional-locks -C $skillMeshRoot rev-parse --git-path index).Trim()
if (-not [IO.Path]::IsPathRooted($gitIndexPath)) { $gitIndexPath = Join-Path $skillMeshRoot $gitIndexPath }
$gitIndexPath = [IO.Path]::GetFullPath($gitIndexPath)
if (-not (Test-Path -LiteralPath $gitIndexPath -PathType Leaf)) { throw "Missing Git index: $gitIndexPath" }
$gitIndexHashBefore = (Get-FileHash -LiteralPath $gitIndexPath -Algorithm SHA256).Hash.ToLowerInvariant()
$recoveryRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'SkillMesh\Recovery'))
$utf8NoBom = New-Object Text.UTF8Encoding($false)

$trackedPaths = @(
    'tools/install-skill-mesh.ps1'
    'tools/migrate-legacy-install.ps1'
    'tests/distributions/test_distributions.py'
    'tests/distributions/test_legacy_migration.py'
)
$planningPaths = @(
    'plan.md'
    'documentation/step-4-checkpoint-2026-08-13.md'
    'documentation/step-4-second-opinion-prompt.md'
    'documentation/skill-mesh-course-correction-plan.md'
    'documentation/skill-mesh-course-correction-proposal.html'
    'documentation/skill-mesh-recovery-plan.md'
    'documentation/product-charter.md'
    'documentation/operator-communication-profile.md'
    'documentation/omnigent-revisit-seed.md'
    'documentation/runbooks/preserve-step-4.md'
)

function Write-Utf8File([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

function Get-NormalPath([string]$Path) {
    return [IO.Path]::GetFullPath($Path).TrimEnd([char[]]'\/')
}

function Test-PathContains([string]$Parent, [string]$Child) {
    $normalParent = Get-NormalPath $Parent
    $normalChild = Get-NormalPath $Child
    return $normalChild.Equals($normalParent, [StringComparison]::OrdinalIgnoreCase) -or
        $normalChild.StartsWith($normalParent + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)
}

function Assert-NoReparseAncestor([string]$Path) {
    $probe = Get-NormalPath $Path
    while (-not (Test-Path -LiteralPath $probe)) {
        $parent = [IO.Path]::GetDirectoryName($probe)
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $probe) { throw "No existing ancestor for $Path" }
        $probe = $parent
    }
    while (-not [string]::IsNullOrWhiteSpace($probe)) {
        $item = Get-Item -LiteralPath $probe -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse-point ancestor: $probe" }
        $parent = [IO.Path]::GetDirectoryName($probe)
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $probe) { break }
        $probe = $parent
    }
}

function Invoke-GitBinary([string[]]$Arguments, [string]$OutputPath) {
    $Arguments = @('--no-optional-locks') + $Arguments
    $quoted = $Arguments | ForEach-Object { '"' + $_.Replace('"', '\"') + '"' }
    $start = New-Object Diagnostics.ProcessStartInfo
    $start.FileName = 'git.exe'
    $start.Arguments = $quoted -join ' '
    $start.UseShellExecute = $false
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $process = New-Object Diagnostics.Process
    $process.StartInfo = $start
    [void]$process.Start()
    $stream = [IO.File]::Open($OutputPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $process.StandardOutput.BaseStream.CopyTo($stream) } finally { $stream.Dispose() }
    $errorText = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw "git failed ($($process.ExitCode)): $errorText" }
}

if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { throw 'LOCALAPPDATA is not available.' }
if ((& git --no-optional-locks -C $skillMeshRoot rev-parse HEAD).Trim() -ne $expectedBase) { throw 'HEAD does not match the frozen Step 4 base.' }

$worktreeText = (& git --no-optional-locks -C $skillMeshRoot worktree list --porcelain) -join "`n"
if ($LASTEXITCODE -ne 0) { throw 'Cannot read Git worktrees.' }
$worktreePaths = @($worktreeText -split "`n" | Where-Object { $_ -like 'worktree *' } | ForEach-Object { Get-NormalPath $_.Substring(9) })
Assert-NoReparseAncestor $recoveryRoot
foreach ($worktreePath in $worktreePaths) {
    Assert-NoReparseAncestor $worktreePath
    if ((Test-PathContains $worktreePath $recoveryRoot) -or (Test-PathContains $recoveryRoot $worktreePath)) {
        throw "Recovery/worktree overlap: $worktreePath"
    }
}

foreach ($repoPath in @($trackedPaths + $planningPaths)) {
    $sourcePath = Join-Path $skillMeshRoot $repoPath
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Missing source: $repoPath" }
}
foreach ($repoPath in $trackedPaths) {
    $listedPath = (& git --no-optional-locks -C $skillMeshRoot ls-files -- $repoPath) -join ''
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($listedPath)) { throw "Expected tracked file is not tracked: $repoPath" }
}
foreach ($repoPath in $planningPaths) {
    $listedPath = (& git --no-optional-locks -C $skillMeshRoot ls-files -- $repoPath) -join ''
    if ($LASTEXITCODE -ne 0) { throw "Cannot check tracked state: $repoPath" }
    if (-not [string]::IsNullOrWhiteSpace($listedPath)) { throw "Expected untracked planning file is already tracked: $repoPath" }
}
$expectedDirtyPaths = @($trackedPaths + $planningPaths | Sort-Object)
$observedDirtyPaths = @(& git --no-optional-locks -C $skillMeshRoot status --porcelain=v1 --untracked-files=all | ForEach-Object { $_.Substring(3).Replace('\', '/') } | Sort-Object)
$statusDelta = @(Compare-Object -ReferenceObject $expectedDirtyPaths -DifferenceObject $observedDirtyPaths)
if ($statusDelta.Count -ne 0) { throw "Dirty-path set differs from the reviewed Step 72 set: $($statusDelta | Out-String)" }

$randomBytes = New-Object byte[] 4
$random = [Security.Cryptography.RandomNumberGenerator]::Create()
try { $random.GetBytes($randomBytes) } finally { $random.Dispose() }
$suffix = ($randomBytes | ForEach-Object { $_.ToString('x2') }) -join ''
$runId = ([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')) + '-' + $suffix
$destination = Join-Path $recoveryRoot ("skill-mesh-step-4-$runId")
if (Test-Path -LiteralPath $destination) { throw "Destination exists: $destination" }

$destinationCreated = $false
try {
    if (-not (Test-Path -LiteralPath $recoveryRoot)) {
        New-Item -ItemType Directory -Path $recoveryRoot -Force | Out-Null
        Assert-NoReparseAncestor $recoveryRoot
    }
    New-Item -ItemType Directory -Path $destination | Out-Null
    $destinationCreated = $true

    $beforeHashes = @{}
    foreach ($repoPath in @($trackedPaths + $planningPaths)) {
        $beforeHashes[$repoPath] = (Get-FileHash -LiteralPath (Join-Path $skillMeshRoot $repoPath) -Algorithm SHA256).Hash.ToLowerInvariant()
    }

    $statusBefore = (& git --no-optional-locks -C $skillMeshRoot status --porcelain=v2 --untracked-files=all) -join "`n"
    Write-Utf8File (Join-Path $destination 'base-sha.txt') ($expectedBase + "`n")
    Write-Utf8File (Join-Path $destination 'git-status.txt') ($statusBefore + "`n")
    Write-Utf8File (Join-Path $destination 'git-diff-stat.txt') (((& git --no-optional-locks -C $skillMeshRoot diff --stat $expectedBase -- @trackedPaths) -join "`n") + "`n")
    Write-Utf8File (Join-Path $destination 'git-worktrees.txt') ($worktreeText + "`n")

    $patchPath = Join-Path $destination 'tracked.patch'
    $diffArguments = @('-C', $skillMeshRoot, 'diff', '--binary', $expectedBase, '--') + $trackedPaths
    Invoke-GitBinary -Arguments $diffArguments -OutputPath $patchPath

    $fileRecords = @()
    foreach ($repoPath in $trackedPaths) {
        $savedPath = Join-Path $destination (Join-Path 'working-files' $repoPath)
        New-Item -ItemType Directory -Path (Split-Path -Parent $savedPath) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $skillMeshRoot $repoPath) -Destination $savedPath
        $fileRecords += [ordered]@{ repo_path = $repoPath; kind = 'tracked-working'; source_sha256 = $beforeHashes[$repoPath]; recovery_sha256 = (Get-FileHash -LiteralPath $savedPath -Algorithm SHA256).Hash.ToLowerInvariant() }
    }
    foreach ($repoPath in $planningPaths) {
        $savedPath = Join-Path $destination (Join-Path 'untracked' $repoPath)
        New-Item -ItemType Directory -Path (Split-Path -Parent $savedPath) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $skillMeshRoot $repoPath) -Destination $savedPath
        $fileRecords += [ordered]@{ repo_path = $repoPath; kind = 'untracked'; source_sha256 = $beforeHashes[$repoPath]; recovery_sha256 = (Get-FileHash -LiteralPath $savedPath -Algorithm SHA256).Hash.ToLowerInvariant() }
    }

    foreach ($record in $fileRecords) {
        if ($record.source_sha256 -ne $record.recovery_sha256) { throw "Saved-copy mismatch: $($record.repo_path)" }
    }

    $archivePath = Join-Path $destination 'base.zip'
    $archiveArguments = @('-C', $skillMeshRoot, 'archive', '--format=zip', $expectedBase)
    Invoke-GitBinary -Arguments $archiveArguments -OutputPath $archivePath
    $verificationRoot = Join-Path $destination 'verification-base'
    Expand-Archive -LiteralPath $archivePath -DestinationPath $verificationRoot
    & git --no-optional-locks -C $verificationRoot apply --check --binary -- $patchPath
    if ($LASTEXITCODE -ne 0) { throw 'git apply --check failed.' }
    & git --no-optional-locks -C $verificationRoot apply --binary -- $patchPath
    if ($LASTEXITCODE -ne 0) { throw 'Patch application failed.' }

    foreach ($repoPath in $trackedPaths) {
        $targetPath = Join-Path $verificationRoot $repoPath
        Copy-Item -LiteralPath (Join-Path $destination (Join-Path 'working-files' $repoPath)) -Destination $targetPath -Force
    }

    foreach ($repoPath in $planningPaths) {
        $targetPath = Join-Path $verificationRoot $repoPath
        New-Item -ItemType Directory -Path (Split-Path -Parent $targetPath) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $destination (Join-Path 'untracked' $repoPath)) -Destination $targetPath
    }
    foreach ($repoPath in @($trackedPaths + $planningPaths)) {
        $restoredHash = (Get-FileHash -LiteralPath (Join-Path $verificationRoot $repoPath) -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($restoredHash -ne $beforeHashes[$repoPath]) { throw "Restored-file mismatch: $repoPath" }
        $sourceHash = (Get-FileHash -LiteralPath (Join-Path $skillMeshRoot $repoPath) -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($sourceHash -ne $beforeHashes[$repoPath]) { throw "Source changed during capture: $repoPath" }
    }
    $statusAfter = (& git --no-optional-locks -C $skillMeshRoot status --porcelain=v2 --untracked-files=all) -join "`n"
    if ($statusAfter -ne $statusBefore) { throw 'Source Git status changed during capture.' }
    $gitIndexHashAfter = (Get-FileHash -LiteralPath $gitIndexPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($gitIndexHashAfter -ne $gitIndexHashBefore) { throw 'Source Git index changed during capture.' }

    $manifest = [ordered]@{
        schema_version = 1
        run_id = $runId
        created_utc = [DateTime]::UtcNow.ToString('o')
        repository = $skillMeshRoot
        base_sha = $expectedBase
        source_status_sha256 = (Get-FileHash -LiteralPath (Join-Path $destination 'git-status.txt') -Algorithm SHA256).Hash.ToLowerInvariant()
        source_index_sha256 = $gitIndexHashBefore
        patch_sha256 = (Get-FileHash -LiteralPath $patchPath -Algorithm SHA256).Hash.ToLowerInvariant()
        files = $fileRecords
        verification = [ordered]@{ apply_check = 'PASS'; hash_match = 'PASS' }
    }
    $manifestTemp = Join-Path $destination 'manifest.json.tmp'
    Write-Utf8File $manifestTemp (($manifest | ConvertTo-Json -Depth 6) + "`n")
    Move-Item -LiteralPath $manifestTemp -Destination (Join-Path $destination 'manifest.json')
    Write-Output "PASS $destination"
}
catch {
    if ($destinationCreated -and (Test-Path -LiteralPath $destination)) {
        Write-Utf8File (Join-Path $destination 'FAILED.txt') (($_ | Out-String) + "`n")
    }
    throw
}
```

The reviewed command is the full block above. Do not shorten it into an unreviewed one-liner. If the block fails, keep its destination and use a new `RunId` for any later attempt.

## Manifest shape

`manifest.json` contains:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schema_version` | integer | yes | `1` |
| `run_id` | string | yes | Identifier defined above |
| `created_utc` | string | yes | ISO 8601 UTC time |
| `repository` | string | yes | Resolved Skill Mesh root |
| `base_sha` | string | yes | Full 40-character expected base |
| `source_status_sha256` | string | yes | Hash of `git-status.txt` |
| `source_index_sha256` | string | yes | Source Git index hash, unchanged before and after capture |
| `patch_sha256` | string | yes | Hash of `tracked.patch` |
| `files` | array | yes | One entry for every tracked and untracked source file |
| `files[].repo_path` | string | yes | Repository-relative path |
| `files[].kind` | string | yes | `tracked-working` or `untracked` |
| `files[].source_sha256` | string | yes | Hash before capture |
| `files[].recovery_sha256` | string | yes | Hash of saved copy |
| `verification` | object | yes | Apply and restore result |
| `verification.apply_check` | string | yes | `PASS` or `FAIL` |
| `verification.hash_match` | string | yes | `PASS` or `FAIL` |

The run passes only when both verification fields are `PASS` and all source/recovery hashes match. A failed run remains for diagnosis. Do not overwrite it or call it verified.

## Failure cleanup

On failure, stop. Keep the incomplete recovery directory and add `FAILED.txt` with the failed step and exact error. Do not retry in the same directory. A retry uses a new `RunId`.
