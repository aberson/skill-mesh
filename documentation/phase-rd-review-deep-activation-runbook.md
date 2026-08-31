# Phase RD Step 4 — review-deep Codex activation runbook

## 1. Purpose and authority

This is the sole executable procedure for Phase RD Step 4. It is a planning artifact, not approval
to run the active-profile portion. `build-phase` halts at the step's `Type: wait` boundary. An
attended coordinator then runs the disposable rehearsal, publishes its record, shows the operator
the exact active-home path, and stops again. Only a new target-specific operator approval permits
the active install.

Never use direct copy, `-Force`, `-ForceShared`, a mutable donor, an on-the-fly installer build, or a
host restart. Do not change certificates, Code Integrity/App Control/AppLocker, Secure Boot, boot
configuration, SDK/WDK, drivers, or either sibling consumer repository.

The Step 4 issue number is the populated `**Issue:**` value under `### Step 4` in
`documentation/phase-rd-review-deep-restoration-plan.md`. All three records below are comments on
that issue. The returned REST comment ID, followed by an individual REST reread, is authoritative;
never select a record by searching prose or by assuming a just-posted comment succeeded.

## 2. Frozen inputs

Before rehearsal, every row must equal both `git rev-parse HEAD:<path>` and `git hash-object <path>`:

| path | required Git blob |
|---|---|
| `documentation/phase-is-completion-plan.md` | `03efa251907cc4d6e99c1ea651296d1813f32f8b` |
| `documentation/instruction-file-symmetry-plan.md` | `6fb9f94f957fca5d3416ffd6dbe6a99ebe6a16e2` |
| `documentation/findings/instruction-file-symmetry-uat.md` | `c285605543f1c3ad02f8ceaf70dac5cb0af37b43` |
| `documentation/phase-is-disposable-c2n-c4-environment-plan.md` | `d41b290bd8e8541d41316463bfcd48cb6d9fb4c6` |
| `documentation/findings/phase-is-route-decision.json` | `a18ea40d9ed04e5649c8a681bf72e1c43920fdc9` |
| `documentation/findings/phase-is-route-decision.selector` | `fa04bb8e39f7d33a8cdb24ccc2d357f211342f7f` |
| `documentation/findings/phase-is-route-resolution.json` | `14482e5ac6ac550d1e65e511fcfe9b31a18385f6` |

The route-decision raw SHA-256 is
`646264e9ceec001ea01b999566f8991e4c2c80f7fc15563d9be2d35dd3495b00`; the selector raw SHA-256 is
`6c3bdb6b56bf578a156102a3553b130fffa6745c6cf77666f925252a21619122`; the resolution raw SHA-256 is
`9c30fadc2b0fe75c7ba7dc2987b63e7824ea8eb11fee2aa0aac90ffee5b9c02b`.

## 3. Canonical bytes and identifiers

All record objects are closed: exactly the listed keys are allowed, every key is required, and no
JSON `null` is permitted. Serialize record bodies as UTF-8 without byte-order mark, keys in the
table order, compact separators, ASCII JSON escapes, and no trailing newline. SHA-256 strings are
lowercase hexadecimal.

`distribution_sha256` and `installed_closure_sha256` use the same closure algorithm:

1. Reject any non-regular or reparse-point file below the measured root.
2. For every regular file, derive its root-relative path, replace `\` with `/`, and reject an empty,
   rooted, dot-segment, control-character, or escaping path.
3. Sort paths by ordinal UTF-8 byte order.
4. Emit one UTF-8 row per file: `relative/path<TAB>lowercase-file-sha256<LF>`.
5. Hash the concatenated rows, including the final LF. The candidate Codex closure has exactly 166
   rows: frozen baseline 125 + 39 imported corpus files + 1 tier-map snapshot + 1 package index.

`active_home_id` is SHA-256 over the UTF-8 bytes, with no BOM or newline, of the exact absolute
`codex_home` string returned by `tools/probe-codex-skills.ps1 -Format json` and passed unchanged as
`-Home`. The public records contain only this digest; the coordinator shows the path locally to the
operator and never posts it.

The package-index digest is the raw SHA-256 of
`codex/review-deep/package-assets.index.md`. Inspector-output digests are SHA-256 over the exact
UTF-8, no-BOM, no-terminal-LF compact JSON obtained by parsing the inspector response and
reserializing it with `ConvertTo-Json -Depth 12 -Compress`.

## 4. Closed record schemas

### `PhaseRdActivationRehearsalV1`

| key | type | required value or constraint |
|---|---|---|
| `schema` | string | `skill-mesh/phase-rd-codex-rehearsal/v1` |
| `candidate_commit` | string | 40 lowercase hex; exact rehearsed `HEAD` |
| `candidate_tree` | string | 40 lowercase hex; exact rehearsed `HEAD^{tree}` |
| `distribution_sha256` | string | 64 lowercase hex from §3 |
| `distribution_file_count` | integer | exactly `166` |
| `package_index_sha256` | string | 64 lowercase hex |
| `active_home_id` | string | 64 lowercase hex from §3 |
| `disposable_install_exit` | integer | exactly `0` |
| `disposable_reinstall_exit` | integer | exactly `0` |
| `disposable_inspector_sha256` | string | 64 lowercase hex |
| `aggregate_help_exit` | integer | exactly `0` |
| `lint_help_exit` | integer | exactly `0` |
| `auth_help_exit` | integer | exactly `0` |
| `calibration_exit` | integer | exactly `0` |
| `disposable_uninstall_exit` | integer | exactly `0` |
| `post_uninstall_file_count` | integer | exactly `0` |
| `protected_blobs_match` | boolean | exactly `true` |

### `PhaseRdActivationApprovalV1`

| key | type | required value or constraint |
|---|---|---|
| `schema` | string | `skill-mesh/phase-rd-active-profile-approval/v1` |
| `candidate_commit` | string | exact rehearsal value |
| `candidate_tree` | string | exact rehearsal value |
| `distribution_sha256` | string | exact rehearsal value |
| `active_home_id` | string | exact rehearsal value |
| `rehearsal_comment_id` | integer | positive ID returned when the exact rehearsal body was posted |
| `decision` | string | exactly `APPROVE` |

### `PhaseRdActivationSealV1`

| key | type | required value or constraint |
|---|---|---|
| `schema` | string | `skill-mesh/phase-rd-codex-activation-seal/v1` |
| `candidate_commit` | string | exact rehearsal/approval value |
| `candidate_tree` | string | exact rehearsal/approval value |
| `distribution_sha256` | string | exact rehearsal/approval value |
| `distribution_file_count` | integer | exactly `166` |
| `package_index_sha256` | string | exact rehearsal value |
| `active_home_id` | string | exact rehearsal/approval value |
| `rehearsal_comment_id` | integer | exact approval value |
| `approval_comment_id` | integer | positive ID returned for the reread approval body |
| `installed_closure_sha256` | string | equals `distribution_sha256` |
| `installed_file_count` | integer | exactly `166` |
| `active_inspector_sha256` | string | 64 lowercase hex |
| `active_ledger_file_count` | integer | exactly `166` |
| `aggregate_help_exit` | integer | exactly `0` |
| `lint_help_exit` | integer | exactly `0` |
| `auth_help_exit` | integer | exactly `0` |
| `calibration_exit` | integer | exactly `0` |
| `capability_verdict` | string | exactly `SUPPORTED` |
| `root_gate_exit` | integer | exactly `0` |
| `root_gate_passed` | integer | positive count parsed from pytest summary |
| `root_gate_skipped` | integer | nonnegative count parsed from pytest summary |
| `protected_blobs_match` | boolean | exactly `true` |

For every post, first enumerate all issue comments with REST `per_page=100` and explicit pagination,
reject duplicate positive IDs, then POST. Capture the returned ID/body/URL/time, GET
`repos/aberson/skill-mesh/issues/comments/{returned-id}`, and require exact body equality. Re-enumerate
to exhaustion and require exactly one comment with that returned ID. The later approval must repeat
the reread rehearsal values; the seal must repeat both reread predecessor records. A newer or
conflicting record for the same candidate/home blocks rather than being silently selected.

Use these exact helpers after constructing each record as an `[ordered]` object in the table's key
order. `$rdStep4Issue` is the positive integer backfilled into the plan by repo-sync. The helpers
enforce the closed ordered key set, use a unique Windows-visible temp body/payload, enumerate every
comment, reject a conflicting record for the same candidate/home, use authenticated REST, retain the
returned ID, and perform an individual reread plus a second exhausted enumeration:

```powershell
function Assert-RdRecordShape([System.Collections.IDictionary]$rdRecord, [string[]]$rdExpectedKeys) {
    [string[]]$rdActualKeys = @($rdRecord.Keys | ForEach-Object { [string]$_ })
    if ($rdActualKeys.Count -ne $rdExpectedKeys.Count) { throw 'record key-count mismatch' }
    for ($rdIndex = 0; $rdIndex -lt $rdExpectedKeys.Count; $rdIndex++) {
        if ($rdActualKeys[$rdIndex] -cne $rdExpectedKeys[$rdIndex]) {
            throw "record key/order mismatch at $rdIndex"
        }
        if ($null -eq $rdRecord[$rdActualKeys[$rdIndex]]) { throw "null record field: $($rdActualKeys[$rdIndex])" }
    }
}
function Get-RdIssueComments([int]$rdStep4Issue) {
    if ($rdStep4Issue -le 0) { throw 'Step 4 issue is not populated' }
    $rdPagesJson = gh api --paginate --slurp "repos/aberson/skill-mesh/issues/$rdStep4Issue/comments?per_page=100"
    if ($LASTEXITCODE -ne 0) { throw 'comment pagination failed' }
    $rdPages = $rdPagesJson | ConvertFrom-Json
    $rdComments = New-Object 'System.Collections.Generic.List[object]'
    foreach ($rdPage in @($rdPages)) {
        foreach ($rdComment in @($rdPage)) { $rdComments.Add($rdComment) }
    }
    $rdIds = @($rdComments | ForEach-Object { [long]$_.id })
    if (@($rdIds | Where-Object { $_ -le 0 }).Count -ne 0 -or
        @($rdIds | Select-Object -Unique).Count -ne $rdIds.Count) {
        throw 'invalid or duplicate issue-comment IDs'
    }
    return $rdComments.ToArray()
}
function Read-RdRecord([int]$rdStep4Issue, [long]$rdCommentId, [string]$rdExpectedBody) {
    if ($rdCommentId -le 0) { throw 'record comment ID is not positive' }
    $rdRereadJson = gh api "repos/aberson/skill-mesh/issues/comments/$rdCommentId"
    if ($LASTEXITCODE -ne 0) { throw 'record reread failed' }
    $rdReread = $rdRereadJson | ConvertFrom-Json
    if ([long]$rdReread.id -ne $rdCommentId -or [string]$rdReread.body -cne $rdExpectedBody) {
        throw 'reread record mismatch'
    }
    $rdComments = @(Get-RdIssueComments $rdStep4Issue)
    if (@($rdComments | Where-Object { [long]$_.id -eq $rdCommentId }).Count -ne 1) {
        throw 'record comment ID is not unique in exhausted enumeration'
    }
    return ($rdExpectedBody | ConvertFrom-Json)
}
function Publish-RdRecord(
    [int]$rdStep4Issue,
    [System.Collections.IDictionary]$rdRecord,
    [string[]]$rdExpectedKeys,
    [string]$rdLabel,
    [string]$rdTempRoot,
    [string]$rdRunId
) {
    if ($rdStep4Issue -le 0) { throw 'Step 4 issue is not populated' }
    Assert-RdRecordShape $rdRecord $rdExpectedKeys
    $rdBody = $rdRecord | ConvertTo-Json -Depth 8 -Compress
    if ($rdBody.Contains("`r") -or $rdBody.Contains("`n")) { throw 'record body is not compact' }
    $rdUtf8 = New-Object Text.UTF8Encoding($false)
    $rdBodyPath = Join-Path $rdTempRoot "skill-mesh-rd-$rdLabel-body-$rdRunId.json"
    $rdPayloadPath = Join-Path $rdTempRoot "skill-mesh-rd-$rdLabel-payload-$rdRunId.json"
    [IO.File]::WriteAllText($rdBodyPath, $rdBody, $rdUtf8)
    $rdPayload = ([ordered]@{ body = $rdBody } | ConvertTo-Json -Depth 3 -Compress)
    [IO.File]::WriteAllText($rdPayloadPath, $rdPayload, $rdUtf8)
    $rdBefore = @(Get-RdIssueComments $rdStep4Issue)
    foreach ($rdComment in $rdBefore) {
        $rdSameIdentity = $false
        try {
            $rdExisting = ([string]$rdComment.body | ConvertFrom-Json)
            $rdSameIdentity = (
                $null -ne $rdExisting.PSObject.Properties['schema'] -and
                $null -ne $rdExisting.PSObject.Properties['candidate_commit'] -and
                $null -ne $rdExisting.PSObject.Properties['active_home_id'] -and
                [string]$rdExisting.schema -ceq [string]$rdRecord.schema -and
                [string]$rdExisting.candidate_commit -ceq [string]$rdRecord.candidate_commit -and
                [string]$rdExisting.active_home_id -ceq [string]$rdRecord.active_home_id
            )
        } catch { $rdSameIdentity = $false }
        if ($rdSameIdentity) {
            throw 'same-candidate/home record already exists; stop for reconciliation'
        }
    }
    $rdResponseJson = gh api --method POST "repos/aberson/skill-mesh/issues/$rdStep4Issue/comments" --input $rdPayloadPath
    if ($LASTEXITCODE -ne 0) { throw 'record POST failed' }
    $rdResponse = $rdResponseJson | ConvertFrom-Json
    if ([long]$rdResponse.id -le 0 -or [string]$rdResponse.body -cne $rdBody) { throw 'returned record mismatch' }
    $null = Read-RdRecord $rdStep4Issue ([long]$rdResponse.id) $rdBody
    return [PSCustomObject]@{ id = [long]$rdResponse.id; url = [string]$rdResponse.html_url; body = $rdBody }
}
```

## 5. Start after the build-phase wait halt

Run in Windows PowerShell from the repository root. These variables are task-specific; never
overwrite PowerShell's `$HOME` automatic variable.

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$rdRepo = (git rev-parse --show-toplevel).Trim()
if ((gh repo view --json nameWithOwner -q .nameWithOwner).Trim() -ne 'aberson/skill-mesh') { throw 'wrong repository' }
if ((git branch --show-current).Trim() -ne 'main') { throw 'main required' }
if (git status --porcelain=v1) { throw 'dirty worktree' }
$rdDivergence = (git rev-list --left-right --count HEAD...origin/main).Trim()
if ($rdDivergence -ne "0`t0") { throw "origin divergence: $rdDivergence" }
$rdCommit = (git rev-parse HEAD).Trim()
$rdTree = (git rev-parse 'HEAD^{tree}').Trim()
$rdPlanText = Get-Content -Raw -LiteralPath 'documentation/phase-rd-review-deep-restoration-plan.md'
$rdStep4Matches = [regex]::Matches($rdPlanText, '(?ms)^### Step 4:.*?^- \*\*Issue:\*\* #([1-9][0-9]*)[^\S\r\n]*$')
if ($rdStep4Matches.Count -ne 1) { throw 'Step 4 issue has not been backfilled uniquely' }
$rdStep4Issue = [int]$rdStep4Matches[0].Groups[1].Value
$rdRunId = [guid]::NewGuid().ToString('N')
$rdTempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$rdStage = Join-Path $rdTempRoot "skill-mesh-rd-stage-$rdRunId"
$rdDisposableHome = Join-Path $rdTempRoot "skill-mesh-rd-home-$rdRunId"
foreach ($rdPath in @($rdStage, $rdDisposableHome)) {
    $rdFull = [IO.Path]::GetFullPath($rdPath)
    if (-not $rdFull.StartsWith($rdTempRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'temp containment failure' }
    if (Test-Path -LiteralPath $rdFull) { throw "path must be absent: $rdFull" }
}
New-Item -ItemType Directory -Path $rdStage | Out-Null
New-Item -ItemType Directory -Path $rdDisposableHome | Out-Null
$env:PYTHONDONTWRITEBYTECODE = '1'
```

Define the exact PowerShell-5.1-compatible digest helpers used for every closure and compact JSON
digest in this run:

```powershell
function Get-RdByteSha256([byte[]]$rdBytes) {
    $rdSha = [Security.Cryptography.SHA256]::Create()
    try { $rdHash = $rdSha.ComputeHash($rdBytes) } finally { $rdSha.Dispose() }
    return ([BitConverter]::ToString($rdHash)).Replace('-', '').ToLowerInvariant()
}
function Get-RdClosure([string]$rdRoot) {
    $rdRootFull = [IO.Path]::GetFullPath($rdRoot).TrimEnd('\', '/')
    if (-not (Test-Path -LiteralPath $rdRootFull -PathType Container)) { throw 'closure root absent' }
    $rdPrefix = $rdRootFull + [IO.Path]::DirectorySeparatorChar
    $rdMap = @{}
    $rdSeen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($rdItem in @(Get-ChildItem -LiteralPath $rdRootFull -Recurse -Force)) {
        if (($rdItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'reparse entry in closure' }
        if ($rdItem.PSIsContainer) { continue }
        $rdFull = [IO.Path]::GetFullPath($rdItem.FullName)
        if (-not $rdFull.StartsWith($rdPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'closure escape' }
        $rdRel = $rdFull.Substring($rdPrefix.Length).Replace('\', '/')
        if ([string]::IsNullOrWhiteSpace($rdRel) -or $rdRel.StartsWith('/') -or
            $rdRel -match '(^|/)\.\.?(/|$)' -or $rdRel -match '[^\x20-\x7e]') { throw 'unsafe closure path' }
        if (-not $rdSeen.Add($rdRel)) { throw 'case-colliding closure path' }
        $rdMap[$rdRel] = (Get-FileHash -Algorithm SHA256 -LiteralPath $rdFull).Hash.ToLowerInvariant()
    }
    [string[]]$rdPaths = @($rdMap.Keys)
    [Array]::Sort($rdPaths, [StringComparer]::Ordinal)
    $rdRows = New-Object Text.StringBuilder
    foreach ($rdRel in $rdPaths) { [void]$rdRows.Append($rdRel).Append("`t").Append($rdMap[$rdRel]).Append("`n") }
    $rdBytes = [Text.Encoding]::UTF8.GetBytes($rdRows.ToString())
    return [PSCustomObject]@{
        file_count = $rdPaths.Count
        sha256 = (Get-RdByteSha256 $rdBytes)
        paths = @($rdPaths)
        hashes = $rdMap
    }
}
function Get-RdCompactJson([string]$rdJson) {
    return (($rdJson | ConvertFrom-Json) | ConvertTo-Json -Depth 12 -Compress)
}
function Get-RdCompactJsonSha256([string]$rdJson) {
    $rdCompact = Get-RdCompactJson $rdJson
    return (Get-RdByteSha256 ([Text.Encoding]::UTF8.GetBytes($rdCompact)))
}
function Assert-RdTierMap([string]$rdPackagedMap) {
    $rdCanonicalMap = Join-Path $rdRepo 'config\model-tier-map.json'
    $rdCanonicalBytes = [IO.File]::ReadAllBytes($rdCanonicalMap)
    $rdPackagedBytes = [IO.File]::ReadAllBytes($rdPackagedMap)
    if ((Get-RdByteSha256 $rdCanonicalBytes) -cne (Get-RdByteSha256 $rdPackagedBytes)) {
        throw 'package-local tier map is not byte-identical to the canonical map'
    }
    $null = ([Text.Encoding]::UTF8.GetString($rdCanonicalBytes) | ConvertFrom-Json)
    $null = ([Text.Encoding]::UTF8.GetString($rdPackagedBytes) | ConvertFrom-Json)
}
function Assert-RdInstalledClosure([string]$rdHome, $rdExpectedDistribution) {
    $rdInstalled = Get-RdClosure (Join-Path $rdHome '.agents\skills')
    if ($rdInstalled.file_count -ne $rdExpectedDistribution.file_count -or
        $rdInstalled.sha256 -cne $rdExpectedDistribution.sha256) {
        throw 'installed Codex closure differs from the staged distribution'
    }
    $rdLedgerPath = Join-Path $rdHome '.skill-mesh-install.json'
    $rdLedger = Get-Content -Raw -LiteralPath $rdLedgerPath | ConvertFrom-Json
    $rdCodexProperty = $rdLedger.installs.PSObject.Properties['codex']
    if ($null -eq $rdCodexProperty) { throw 'Codex ledger entry absent' }
    $rdEntry = $rdCodexProperty.Value
    [string[]]$rdExpectedOwned = @($rdExpectedDistribution.paths | ForEach-Object { '.agents/skills/' + $_ })
    [Array]::Sort($rdExpectedOwned, [StringComparer]::Ordinal)
    [string[]]$rdActualOwned = @($rdEntry.owned_files | ForEach-Object { ([string]$_).Replace('\', '/') })
    [Array]::Sort($rdActualOwned, [StringComparer]::Ordinal)
    if (($rdActualOwned -join "`n") -cne ($rdExpectedOwned -join "`n")) {
        throw 'ledger owned_files is not the exact staged closure'
    }
    $rdLedgerHashes = @{}
    foreach ($rdProperty in @($rdEntry.owned_file_hashes.PSObject.Properties)) {
        $rdLedgerRel = ([string]$rdProperty.Name).Replace('\', '/')
        if ($rdLedgerHashes.ContainsKey($rdLedgerRel)) { throw 'duplicate normalized ledger hash path' }
        $rdLedgerHashes[$rdLedgerRel] = ([string]$rdProperty.Value).ToLowerInvariant()
    }
    if ($rdLedgerHashes.Count -ne $rdExpectedOwned.Count) { throw 'ledger hash-map count mismatch' }
    foreach ($rdRel in @($rdExpectedDistribution.paths)) {
        $rdLedgerRel = '.agents/skills/' + $rdRel
        if (-not $rdLedgerHashes.ContainsKey($rdLedgerRel) -or
            $rdLedgerHashes[$rdLedgerRel] -cne $rdExpectedDistribution.hashes[$rdRel]) {
            throw "ledger hash mismatch: $rdLedgerRel"
        }
    }
    return [PSCustomObject]@{
        closure = $rdInstalled
        ledger_file_count = $rdActualOwned.Count
    }
}
function Assert-RdActivePreflight([string]$rdHome, $rdExpectedDistribution, $rdInspectObject, $rdProbeObject) {
    if (@($rdInspectObject.warnings).Count -ne 0) { throw 'active-home inspector reported warnings' }
    $rdProfile = $rdInspectObject.profiles.codex
    if (@('absent', 'present') -notcontains [string]$rdProfile.state) { throw 'unexpected active Codex profile state' }
    if (@('absent', 'directory') -notcontains [string]$rdProfile.link_type) { throw 'active Codex root is linked or non-directory' }
    if ([string]$rdProbeObject.root.state -ne [string]$rdProfile.state -or
        [string]$rdProbeObject.root.link_type -ne [string]$rdProfile.link_type) {
        throw 'probe/inspector active-root disagreement'
    }
    $rdInstallRoot = Join-Path $rdHome '.agents\skills'
    $rdLedgerPath = Join-Path $rdHome '.skill-mesh-install.json'
    if ([string]$rdProfile.state -eq 'absent') {
        if ($rdProbeObject.ledger.codex_installed -or
            ($rdInspectObject.ledger.state -eq 'valid' -and @($rdInspectObject.ledger.providers) -contains 'codex')) {
            throw 'ledger claims Codex ownership while the active root is absent'
        }
        return
    }
    if ($rdProfile.unowned_count -ne 0 -or $rdInspectObject.ledger.state -ne 'valid' -or
        -not (@($rdInspectObject.ledger.providers) -contains 'codex') -or
        -not $rdProbeObject.ledger.codex_installed) {
        throw 'active Codex profile is not wholly ledger-owned'
    }
    $rdCurrent = Get-RdClosure $rdInstallRoot
    $rdLedger = Get-Content -Raw -LiteralPath $rdLedgerPath | ConvertFrom-Json
    $rdEntry = $rdLedger.installs.PSObject.Properties['codex'].Value
    $rdCurrentLedgerHashes = @{}
    foreach ($rdProperty in @($rdEntry.owned_file_hashes.PSObject.Properties)) {
        $rdRel = ([string]$rdProperty.Name).Replace('\', '/')
        if (-not $rdRel.StartsWith('.agents/skills/', [StringComparison]::Ordinal)) {
            throw 'Codex ledger owns a path outside its discovery root'
        }
        $rdLocalRel = $rdRel.Substring('.agents/skills/'.Length)
        if ($rdCurrentLedgerHashes.ContainsKey($rdLocalRel)) { throw 'duplicate normalized active-ledger path' }
        $rdCurrentLedgerHashes[$rdLocalRel] = ([string]$rdProperty.Value).ToLowerInvariant()
    }
    if ($rdCurrentLedgerHashes.Count -ne $rdCurrent.file_count) {
        throw 'active root contains a file not represented by the Codex ledger'
    }
    foreach ($rdRel in @($rdCurrent.paths)) {
        if (-not $rdCurrentLedgerHashes.ContainsKey($rdRel) -or
            $rdCurrentLedgerHashes[$rdRel] -cne $rdCurrent.hashes[$rdRel]) {
            throw "active file is foreign or changed: $rdRel"
        }
    }
    foreach ($rdRel in @($rdExpectedDistribution.paths)) {
        $rdTarget = Join-Path $rdInstallRoot ($rdRel -replace '/', '\')
        if ((Test-Path -LiteralPath $rdTarget) -and -not $rdCurrentLedgerHashes.ContainsKey($rdRel)) {
            throw "incoming path collides with a foreign active file: $rdRel"
        }
    }
}
```

Recheck every §2 blob with both Git-object and working-file hashes:

```powershell
$rdProtectedBlobs = [ordered]@{
    'documentation/phase-is-completion-plan.md' = '03efa251907cc4d6e99c1ea651296d1813f32f8b'
    'documentation/instruction-file-symmetry-plan.md' = '6fb9f94f957fca5d3416ffd6dbe6a99ebe6a16e2'
    'documentation/findings/instruction-file-symmetry-uat.md' = 'c285605543f1c3ad02f8ceaf70dac5cb0af37b43'
    'documentation/phase-is-disposable-c2n-c4-environment-plan.md' = 'd41b290bd8e8541d41316463bfcd48cb6d9fb4c6'
    'documentation/findings/phase-is-route-decision.json' = 'a18ea40d9ed04e5649c8a681bf72e1c43920fdc9'
    'documentation/findings/phase-is-route-decision.selector' = 'fa04bb8e39f7d33a8cdb24ccc2d357f211342f7f'
    'documentation/findings/phase-is-route-resolution.json' = '14482e5ac6ac550d1e65e511fcfe9b31a18385f6'
}
foreach ($rdEntry in $rdProtectedBlobs.GetEnumerator()) {
    $rdHeadBlob = (git rev-parse "HEAD:$($rdEntry.Key)").Trim()
    $rdWorkBlob = (git hash-object -- $rdEntry.Key).Trim()
    if ($rdHeadBlob -ne $rdEntry.Value -or $rdWorkBlob -ne $rdEntry.Value) { throw "protected blob drift: $($rdEntry.Key)" }
}
```

Any mismatch stops. Then build
the immutable candidate; no later command may rebuild it:

```powershell
powershell -NoProfile -NonInteractive -File tools/build-distributions.ps1 -Provider codex -OutputDir $rdStage
if ($LASTEXITCODE -ne 0) { throw 'Codex distribution build failed' }
if ((git rev-parse HEAD).Trim() -ne $rdCommit) { throw 'HEAD moved after build' }
if ((git rev-parse 'HEAD^{tree}').Trim() -ne $rdTree) { throw 'tree moved after build' }
```

Use the helper to derive the bound values and require `166`:

```powershell
$rdDistribution = Get-RdClosure "$rdStage\codex"
if ($rdDistribution.file_count -ne 166) { throw "wrong Codex closure count: $($rdDistribution.file_count)" }
$rdDistributionFileCount = $rdDistribution.file_count
$rdDistributionSha256 = $rdDistribution.sha256
$rdPackageIndexSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath "$rdStage\codex\review-deep\package-assets.index.md").Hash.ToLowerInvariant()
Assert-RdTierMap "$rdStage\codex\review-deep\config\model-tier-map.json"
```

Require the staged
`review-deep/config/model-tier-map.json` bytes and parsed JSON to equal the repository-root
`config/model-tier-map.json`.

Run all staged entry points with `-B`/`PYTHONDONTWRITEBYTECODE` and require exit 0:

```powershell
python -B "$rdStage\codex\review-deep\scripts\aggregate.py" --help
$rdStagedAggregateHelpExit = $LASTEXITCODE
if ($rdStagedAggregateHelpExit -ne 0) { throw 'aggregate help failed' }
bash "$rdStage/codex/review-deep/scripts/lint_prepass.sh" --help
$rdStagedLintHelpExit = $LASTEXITCODE
if ($rdStagedLintHelpExit -ne 0) { throw 'lint help failed' }
bash "$rdStage/codex/review-deep/scripts/auth_gate_probe.sh" --help
$rdStagedAuthHelpExit = $LASTEXITCODE
if ($rdStagedAuthHelpExit -ne 0) { throw 'auth help failed' }
python -B "$rdStage\codex\_shared\calibrate_judge.py" --skill-dir "$rdStage\codex\review-deep" --mode ci
$rdStagedCalibrationExit = $LASTEXITCODE
if ($rdStagedCalibrationExit -ne 0) { throw 'staged calibration failed' }
```

## 6. Disposable install, reinstall, and uninstall

Every install uses the already-measured `$rdStage`:

```powershell
powershell -NoProfile -NonInteractive -File tools/install-skill-mesh.ps1 -Provider codex -Home $rdDisposableHome -DistDir $rdStage
$rdDisposableInstallExit = $LASTEXITCODE
if ($rdDisposableInstallExit -ne 0) { throw 'disposable install failed' }
$rdInspect1 = powershell -NoProfile -NonInteractive -File tools/inspect-host-install.ps1 -Home $rdDisposableHome -Format json
if ($LASTEXITCODE -ne 0) { throw 'disposable inspect failed' }
$rdInspect1Json = $rdInspect1 -join "`n"
$rdInspect1Object = $rdInspect1Json | ConvertFrom-Json
if ($rdInspect1Object.profiles.codex.state -ne 'present' -or $rdInspect1Object.profiles.codex.unowned_count -ne 0 -or $rdInspect1Object.ledger.state -ne 'valid' -or @($rdInspect1Object.warnings).Count -ne 0) { throw 'disposable inspect predicates failed' }
powershell -NoProfile -NonInteractive -File tools/install-skill-mesh.ps1 -Provider codex -Home $rdDisposableHome -DistDir $rdStage
$rdDisposableReinstallExit = $LASTEXITCODE
if ($rdDisposableReinstallExit -ne 0) { throw 'disposable reinstall failed' }
$rdInspect2 = powershell -NoProfile -NonInteractive -File tools/inspect-host-install.ps1 -Home $rdDisposableHome -Format json
if ($LASTEXITCODE -ne 0) { throw 'disposable re-inspect failed' }
$rdInspect2Json = $rdInspect2 -join "`n"
$rdInspect2Object = $rdInspect2Json | ConvertFrom-Json
if ($rdInspect2Object.profiles.codex.state -ne 'present' -or $rdInspect2Object.profiles.codex.unowned_count -ne 0 -or $rdInspect2Object.ledger.state -ne 'valid' -or @($rdInspect2Object.warnings).Count -ne 0) { throw 'disposable re-inspect predicates failed' }
$rdDisposableInspectorSha256 = Get-RdCompactJsonSha256 $rdInspect2Json
$rdDisposableProof = Assert-RdInstalledClosure $rdDisposableHome $rdDistribution
if ($rdDisposableProof.ledger_file_count -ne 166) { throw 'disposable ledger count mismatch' }
Assert-RdTierMap "$rdDisposableHome\.agents\skills\review-deep\config\model-tier-map.json"

python -B "$rdDisposableHome\.agents\skills\review-deep\scripts\aggregate.py" --help
$rdDisposableAggregateHelpExit = $LASTEXITCODE
if ($rdDisposableAggregateHelpExit -ne 0) { throw 'disposable aggregate help failed' }
bash "$rdDisposableHome/.agents/skills/review-deep/scripts/lint_prepass.sh" --help
$rdDisposableLintHelpExit = $LASTEXITCODE
if ($rdDisposableLintHelpExit -ne 0) { throw 'disposable lint help failed' }
bash "$rdDisposableHome/.agents/skills/review-deep/scripts/auth_gate_probe.sh" --help
$rdDisposableAuthHelpExit = $LASTEXITCODE
if ($rdDisposableAuthHelpExit -ne 0) { throw 'disposable auth help failed' }
python -B "$rdDisposableHome\.agents\skills\_shared\calibrate_judge.py" --skill-dir "$rdDisposableHome\.agents\skills\review-deep" --mode ci
$rdDisposableCalibrationExit = $LASTEXITCODE
if ($rdDisposableCalibrationExit -ne 0) { throw 'disposable calibration failed' }
```

The block above proves the installed discovery-root closure and ledger bijection against the staged
166-path digest and records the second, authoritative inspector result. Then uninstall:

```powershell
powershell -NoProfile -NonInteractive -File tools/install-skill-mesh.ps1 -Provider codex -Home $rdDisposableHome -Uninstall
$rdDisposableUninstallExit = $LASTEXITCODE
if ($rdDisposableUninstallExit -ne 0) { throw 'disposable uninstall failed' }
$rdFilesAfterUninstall = @(Get-ChildItem -LiteralPath "$rdDisposableHome\.agents\skills" -Recurse -File -ErrorAction SilentlyContinue)
$rdPostUninstallFileCount = $rdFilesAfterUninstall.Count
if ($rdPostUninstallFileCount -ne 0) { throw 'owned files remain after disposable uninstall' }
if (Test-Path -LiteralPath "$rdDisposableHome\.skill-mesh-install.json") { throw 'disposable ledger remains after uninstall' }
```

## 7. Resolve target, publish rehearsal, and stop for approval

```powershell
$rdProbeJson = powershell -NoProfile -NonInteractive -File tools/probe-codex-skills.ps1 -Format json
if ($LASTEXITCODE -ne 0) { throw 'active Codex home probe failed' }
$rdProbeJson = $rdProbeJson -join "`n"
$rdProbe = $rdProbeJson | ConvertFrom-Json
if (@('agree', 'single') -notcontains $rdProbe.env_agreement -or -not $rdProbe.home_exists) { throw 'active Codex home is ambiguous or absent' }
$rdActiveHomeSource = switch ([string]$rdProbe.home_source) {
    'HOME+USERPROFILE' { [Environment]::GetEnvironmentVariable('HOME'); break }
    'HOME' { [Environment]::GetEnvironmentVariable('HOME'); break }
    'USERPROFILE' { [Environment]::GetEnvironmentVariable('USERPROFILE'); break }
    default { throw 'probe did not resolve an unattended active-home source' }
}
$rdActiveHome = [IO.Path]::GetFullPath($rdActiveHomeSource).TrimEnd('\', '/')
if ([string]$rdProbe.codex_home -cne $rdActiveHome) {
    throw 'probe display transformed or truncated the active path; do not use it as an install target'
}
$rdHasher = [Security.Cryptography.SHA256]::Create()
try { $rdActiveHomeHash = $rdHasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($rdActiveHome)) }
finally { $rdHasher.Dispose() }
$rdActiveHomeId = ([BitConverter]::ToString($rdActiveHomeHash)).Replace('-', '').ToLowerInvariant()

$rdActivePreInspect = powershell -NoProfile -NonInteractive -File tools/inspect-host-install.ps1 -Home $rdActiveHome -Format json
if ($LASTEXITCODE -ne 0) { throw 'active-home preflight inspect failed' }
$rdActivePreInspectJson = $rdActivePreInspect -join "`n"
$rdActivePreInspectObject = $rdActivePreInspectJson | ConvertFrom-Json
Assert-RdActivePreflight $rdActiveHome $rdDistribution $rdActivePreInspectObject $rdProbe
$rdActivePreInspectSha256 = Get-RdCompactJsonSha256 $rdActivePreInspectJson
```

The preflight is read-only and stops on a foreign, changed, unledgered, linked, or ambiguous active
tree. Construct and publish the rehearsal only after it passes:

```powershell
$rdRehearsalKeys = @(
    'schema', 'candidate_commit', 'candidate_tree', 'distribution_sha256',
    'distribution_file_count', 'package_index_sha256', 'active_home_id',
    'disposable_install_exit', 'disposable_reinstall_exit', 'disposable_inspector_sha256',
    'aggregate_help_exit', 'lint_help_exit', 'auth_help_exit', 'calibration_exit',
    'disposable_uninstall_exit', 'post_uninstall_file_count', 'protected_blobs_match'
)
if ($rdCommit -notmatch '^[0-9a-f]{40}$' -or $rdTree -notmatch '^[0-9a-f]{40}$' -or
    $rdDistributionSha256 -notmatch '^[0-9a-f]{64}$' -or
    $rdPackageIndexSha256 -notmatch '^[0-9a-f]{64}$' -or
    $rdActiveHomeId -notmatch '^[0-9a-f]{64}$' -or
    $rdDisposableInspectorSha256 -notmatch '^[0-9a-f]{64}$') {
    throw 'rehearsal identifier shape failed'
}
$rdRehearsalRecord = [ordered]@{
    schema = 'skill-mesh/phase-rd-codex-rehearsal/v1'
    candidate_commit = $rdCommit
    candidate_tree = $rdTree
    distribution_sha256 = $rdDistributionSha256
    distribution_file_count = [int]$rdDistributionFileCount
    package_index_sha256 = $rdPackageIndexSha256
    active_home_id = $rdActiveHomeId
    disposable_install_exit = [int]$rdDisposableInstallExit
    disposable_reinstall_exit = [int]$rdDisposableReinstallExit
    disposable_inspector_sha256 = $rdDisposableInspectorSha256
    aggregate_help_exit = [int]$rdDisposableAggregateHelpExit
    lint_help_exit = [int]$rdDisposableLintHelpExit
    auth_help_exit = [int]$rdDisposableAuthHelpExit
    calibration_exit = [int]$rdDisposableCalibrationExit
    disposable_uninstall_exit = [int]$rdDisposableUninstallExit
    post_uninstall_file_count = [int]$rdPostUninstallFileCount
    protected_blobs_match = [bool]$true
}
Assert-RdRecordShape $rdRehearsalRecord $rdRehearsalKeys
$rdRehearsalPost = Publish-RdRecord $rdStep4Issue $rdRehearsalRecord $rdRehearsalKeys 'rehearsal' $rdTempRoot $rdRunId
$rdRehearsal = Read-RdRecord $rdStep4Issue $rdRehearsalPost.id $rdRehearsalPost.body
```

Now stop. Report locally to the operator: exact `$rdActiveHome`, its non-disclosing ID, candidate
commit/tree, distribution digest, package-index digest, rehearsal comment ID/URL, and every
disposable result, including `$rdActivePreInspectSha256`. Ask for this exact one-line approval, with
the placeholders replaced by the displayed values, and do not install while waiting:

```text
APPROVE PHASE_RD_ACTIVE_PROFILE candidate=<40hex> tree=<40hex> distribution=<64hex> active_home_id=<64hex> rehearsal_comment_id=<positive-integer>
```

Any other wording leaves the step blocked. After receiving that exact approval, reread and compare
the rehearsal again, then construct and publish the approval record:

```powershell
$rdRehearsal = Read-RdRecord $rdStep4Issue $rdRehearsalPost.id $rdRehearsalPost.body
if ([string]$rdRehearsal.candidate_commit -cne $rdCommit -or
    [string]$rdRehearsal.candidate_tree -cne $rdTree -or
    [string]$rdRehearsal.distribution_sha256 -cne $rdDistributionSha256 -or
    [string]$rdRehearsal.active_home_id -cne $rdActiveHomeId) {
    throw 'rehearsal predecessor drifted'
}
$rdApprovalKeys = @(
    'schema', 'candidate_commit', 'candidate_tree', 'distribution_sha256',
    'active_home_id', 'rehearsal_comment_id', 'decision'
)
$rdApprovalRecord = [ordered]@{
    schema = 'skill-mesh/phase-rd-active-profile-approval/v1'
    candidate_commit = $rdCommit
    candidate_tree = $rdTree
    distribution_sha256 = $rdDistributionSha256
    active_home_id = $rdActiveHomeId
    rehearsal_comment_id = [long]$rdRehearsalPost.id
    decision = 'APPROVE'
}
Assert-RdRecordShape $rdApprovalRecord $rdApprovalKeys
$rdApprovalPost = Publish-RdRecord $rdStep4Issue $rdApprovalRecord $rdApprovalKeys 'approval' $rdTempRoot $rdRunId
$rdApproval = Read-RdRecord $rdStep4Issue $rdApprovalPost.id $rdApprovalPost.body
```

## 8. Active install and fresh-context proof

Immediately before mutation, recheck clean/synchronized Git, candidate commit/tree, all §2 blobs,
the retained stage's closure/index/tier-map hashes, the lossless active-home identity and read-only
collision preflight, and both predecessor comment bodies:

```powershell
if (git status --porcelain=v1) { throw 'dirty worktree before active install' }
if ((git rev-list --left-right --count HEAD...origin/main).Trim() -ne "0`t0") { throw 'origin drift before active install' }
if ((git rev-parse HEAD).Trim() -cne $rdCommit -or (git rev-parse 'HEAD^{tree}').Trim() -cne $rdTree) { throw 'candidate moved before active install' }
foreach ($rdEntry in $rdProtectedBlobs.GetEnumerator()) {
    if ((git rev-parse "HEAD:$($rdEntry.Key)").Trim() -cne $rdEntry.Value -or
        (git hash-object -- $rdEntry.Key).Trim() -cne $rdEntry.Value) { throw "protected blob drift: $($rdEntry.Key)" }
}
$rdStageRecheck = Get-RdClosure "$rdStage\codex"
if ($rdStageRecheck.file_count -ne $rdDistributionFileCount -or $rdStageRecheck.sha256 -cne $rdDistributionSha256) { throw 'retained stage drifted' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath "$rdStage\codex\review-deep\package-assets.index.md").Hash.ToLowerInvariant() -cne $rdPackageIndexSha256) { throw 'package index drifted' }
Assert-RdTierMap "$rdStage\codex\review-deep\config\model-tier-map.json"
$rdProbeAgainJson = powershell -NoProfile -NonInteractive -File tools/probe-codex-skills.ps1 -Format json
if ($LASTEXITCODE -ne 0) { throw 'active-home reprobe failed' }
$rdProbeAgainJson = $rdProbeAgainJson -join "`n"
$rdProbeAgain = $rdProbeAgainJson | ConvertFrom-Json
if ([string]$rdProbeAgain.codex_home -cne $rdActiveHome -or @('agree', 'single') -notcontains $rdProbeAgain.env_agreement) { throw 'active home changed or became ambiguous' }
$rdActivePreInspectAgain = powershell -NoProfile -NonInteractive -File tools/inspect-host-install.ps1 -Home $rdActiveHome -Format json
if ($LASTEXITCODE -ne 0) { throw 'active-home preflight re-inspect failed' }
Assert-RdActivePreflight $rdActiveHome $rdDistribution (($rdActivePreInspectAgain -join "`n") | ConvertFrom-Json) $rdProbeAgain
$rdRehearsal = Read-RdRecord $rdStep4Issue $rdRehearsalPost.id $rdRehearsalPost.body
$rdApproval = Read-RdRecord $rdStep4Issue $rdApprovalPost.id $rdApprovalPost.body
if ([long]$rdApproval.rehearsal_comment_id -ne [long]$rdRehearsalPost.id -or
    [string]$rdApproval.decision -cne 'APPROVE' -or
    [string]$rdApproval.candidate_commit -cne $rdCommit -or
    [string]$rdApproval.candidate_tree -cne $rdTree -or
    [string]$rdApproval.distribution_sha256 -cne $rdDistributionSha256 -or
    [string]$rdApproval.active_home_id -cne $rdActiveHomeId) { throw 'approval predecessor drifted' }
```

Then run exactly:

```powershell
powershell -NoProfile -NonInteractive -File tools/install-skill-mesh.ps1 -Provider codex -Home $rdActiveHome -DistDir $rdStage
$rdActiveInstallExit = $LASTEXITCODE
if ($rdActiveInstallExit -ne 0) { throw 'active install failed' }
$rdActiveInspect = powershell -NoProfile -NonInteractive -File tools/inspect-host-install.ps1 -Home $rdActiveHome -Format json
if ($LASTEXITCODE -ne 0) { throw 'active inspect failed' }
$rdActiveInspectJson = $rdActiveInspect -join "`n"
$rdActiveInspectObject = $rdActiveInspectJson | ConvertFrom-Json
if ($rdActiveInspectObject.profiles.codex.state -ne 'present' -or $rdActiveInspectObject.profiles.codex.unowned_count -ne 0 -or $rdActiveInspectObject.ledger.state -ne 'valid' -or @($rdActiveInspectObject.warnings).Count -ne 0) { throw 'active inspect predicates failed' }
$rdActiveInspectorSha256 = Get-RdCompactJsonSha256 $rdActiveInspectJson
$rdActiveProof = Assert-RdInstalledClosure $rdActiveHome $rdDistribution
$rdInstalledClosureSha256 = $rdActiveProof.closure.sha256
$rdInstalledFileCount = [int]$rdActiveProof.closure.file_count
$rdActiveLedgerFileCount = [int]$rdActiveProof.ledger_file_count
if ($rdInstalledClosureSha256 -cne $rdDistributionSha256 -or $rdInstalledFileCount -ne 166 -or $rdActiveLedgerFileCount -ne 166) { throw 'active closure/ledger count mismatch' }
Assert-RdTierMap "$rdActiveHome\.agents\skills\review-deep\config\model-tier-map.json"

python -B "$rdActiveHome\.agents\skills\review-deep\scripts\aggregate.py" --help
$rdActiveAggregateHelpExit = $LASTEXITCODE
if ($rdActiveAggregateHelpExit -ne 0) { throw 'active aggregate help failed' }
bash "$rdActiveHome/.agents/skills/review-deep/scripts/lint_prepass.sh" --help
$rdActiveLintHelpExit = $LASTEXITCODE
if ($rdActiveLintHelpExit -ne 0) { throw 'active lint help failed' }
bash "$rdActiveHome/.agents/skills/review-deep/scripts/auth_gate_probe.sh" --help
$rdActiveAuthHelpExit = $LASTEXITCODE
if ($rdActiveAuthHelpExit -ne 0) { throw 'active auth help failed' }
python -B "$rdActiveHome\.agents\skills\_shared\calibrate_judge.py" --skill-dir "$rdActiveHome\.agents\skills\review-deep" --mode ci
$rdActiveCalibrationExit = $LASTEXITCODE
if ($rdActiveCalibrationExit -ne 0) { throw 'active calibration failed' }
```

No cleanup or force retry is allowed on failure.

Open one fresh `gpt-5.6-terra` context with `fork_turns="none"`. Give it exactly this task (the host
may add only its normal system/developer instructions):

```text
Invoke the active review-deep skill. Run its documented non-mutating Codex host-acceptance probe and mandatory installed-package calibration. Do not modify any file, install anything, inspect a parent session, request prior results, classify a final review verdict, or post an activation record. Return the adapter-defined public evidence and end with exactly one line: PHASE_RD_CAPABILITY=SUPPORTED or PHASE_RD_CAPABILITY=required_tool_missing.
```

The parent creates the adapter-required authenticated sidecar and retains its HMAC key outside the
child/worktree before dispatch. It supplies neither to the child. The parent rejects missing,
duplicate, stale, unauthenticated, or child-written evidence, independently checks that the child had
no inherited conversation, and alone classifies the result. A child response is evidence, never
verdict authority. Only after all adapter predicates pass may the parent set
`$rdCapabilityVerdict = 'SUPPORTED'`; every other result stops with `required_tool_missing`. Record
the fresh child task/session identifier locally, but do not put it or a private sidecar path in a
public record.

Finally run the root gate at the exact candidate repository root and parse its terminal summary:

```powershell
$rdRootLog = Join-Path $rdTempRoot "skill-mesh-rd-root-$rdRunId.log"
python -m pytest 2>&1 | Tee-Object -FilePath $rdRootLog
$rdRootGateExit = $LASTEXITCODE
if ($rdRootGateExit -ne 0) { throw "root gate failed: $rdRootGateExit" }
$rdRootSummary = @(Get-Content -LiteralPath $rdRootLog | Select-String -Pattern '[0-9]+ passed')[-1].Line
if ($rdRootSummary -notmatch '([0-9]+) passed') { throw 'passed count absent' }
$rdRootGatePassed = [int]$Matches[1]
$rdRootGateSkipped = 0
if ($rdRootSummary -match '([0-9]+) skipped') { $rdRootGateSkipped = [int]$Matches[1] }
```

Recheck every bound surface and let the parent coordinator alone construct and publish the seal:

```powershell
if ($rdCapabilityVerdict -cne 'SUPPORTED') { throw 'fresh-context capability was not supported' }
if (git status --porcelain=v1) { throw 'dirty worktree before activation seal' }
if ((git rev-list --left-right --count HEAD...origin/main).Trim() -ne "0`t0") { throw 'origin drift before activation seal' }
if ((git rev-parse HEAD).Trim() -cne $rdCommit -or (git rev-parse 'HEAD^{tree}').Trim() -cne $rdTree) { throw 'candidate moved before activation seal' }
foreach ($rdEntry in $rdProtectedBlobs.GetEnumerator()) {
    if ((git rev-parse "HEAD:$($rdEntry.Key)").Trim() -cne $rdEntry.Value -or
        (git hash-object -- $rdEntry.Key).Trim() -cne $rdEntry.Value) { throw "protected blob drift: $($rdEntry.Key)" }
}
$rdFinalStage = Get-RdClosure "$rdStage\codex"
if ($rdFinalStage.file_count -ne 166 -or $rdFinalStage.sha256 -cne $rdDistributionSha256) { throw 'final stage drift' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath "$rdStage\codex\review-deep\package-assets.index.md").Hash.ToLowerInvariant() -cne $rdPackageIndexSha256) { throw 'final package-index drift' }
Assert-RdTierMap "$rdStage\codex\review-deep\config\model-tier-map.json"
$rdFinalActiveProof = Assert-RdInstalledClosure $rdActiveHome $rdDistribution
if ($rdFinalActiveProof.closure.file_count -ne 166 -or
    $rdFinalActiveProof.closure.sha256 -cne $rdDistributionSha256 -or
    $rdFinalActiveProof.ledger_file_count -ne 166) { throw 'final active closure/ledger drift' }
$rdFinalInspect = powershell -NoProfile -NonInteractive -File tools/inspect-host-install.ps1 -Home $rdActiveHome -Format json
if ($LASTEXITCODE -ne 0) { throw 'final active inspect failed' }
$rdFinalInspectJson = $rdFinalInspect -join "`n"
$rdFinalInspectObject = $rdFinalInspectJson | ConvertFrom-Json
if ($rdFinalInspectObject.profiles.codex.state -ne 'present' -or
    $rdFinalInspectObject.profiles.codex.unowned_count -ne 0 -or
    $rdFinalInspectObject.ledger.state -ne 'valid' -or
    @($rdFinalInspectObject.warnings).Count -ne 0 -or
    (Get-RdCompactJsonSha256 $rdFinalInspectJson) -cne $rdActiveInspectorSha256) { throw 'final inspector drift' }
$rdRehearsal = Read-RdRecord $rdStep4Issue $rdRehearsalPost.id $rdRehearsalPost.body
$rdApproval = Read-RdRecord $rdStep4Issue $rdApprovalPost.id $rdApprovalPost.body
if ([long]$rdApproval.rehearsal_comment_id -ne [long]$rdRehearsalPost.id -or
    [string]$rdApproval.candidate_commit -cne $rdCommit -or
    [string]$rdApproval.candidate_tree -cne $rdTree -or
    [string]$rdApproval.distribution_sha256 -cne $rdDistributionSha256 -or
    [string]$rdApproval.active_home_id -cne $rdActiveHomeId -or
    [string]$rdApproval.decision -cne 'APPROVE') { throw 'final predecessor mismatch' }

$rdSealKeys = @(
    'schema', 'candidate_commit', 'candidate_tree', 'distribution_sha256',
    'distribution_file_count', 'package_index_sha256', 'active_home_id',
    'rehearsal_comment_id', 'approval_comment_id', 'installed_closure_sha256',
    'installed_file_count', 'active_inspector_sha256', 'active_ledger_file_count',
    'aggregate_help_exit', 'lint_help_exit', 'auth_help_exit', 'calibration_exit',
    'capability_verdict', 'root_gate_exit', 'root_gate_passed', 'root_gate_skipped',
    'protected_blobs_match'
)
if ($rdActiveInspectorSha256 -notmatch '^[0-9a-f]{64}$' -or
    $rdInstalledClosureSha256 -cne $rdDistributionSha256 -or
    $rdRootGatePassed -le 0 -or $rdRootGateSkipped -lt 0) { throw 'seal field validation failed' }
$rdSealRecord = [ordered]@{
    schema = 'skill-mesh/phase-rd-codex-activation-seal/v1'
    candidate_commit = $rdCommit
    candidate_tree = $rdTree
    distribution_sha256 = $rdDistributionSha256
    distribution_file_count = [int]$rdDistributionFileCount
    package_index_sha256 = $rdPackageIndexSha256
    active_home_id = $rdActiveHomeId
    rehearsal_comment_id = [long]$rdRehearsalPost.id
    approval_comment_id = [long]$rdApprovalPost.id
    installed_closure_sha256 = $rdInstalledClosureSha256
    installed_file_count = [int]$rdInstalledFileCount
    active_inspector_sha256 = $rdActiveInspectorSha256
    active_ledger_file_count = [int]$rdActiveLedgerFileCount
    aggregate_help_exit = [int]$rdActiveAggregateHelpExit
    lint_help_exit = [int]$rdActiveLintHelpExit
    auth_help_exit = [int]$rdActiveAuthHelpExit
    calibration_exit = [int]$rdActiveCalibrationExit
    capability_verdict = $rdCapabilityVerdict
    root_gate_exit = [int]$rdRootGateExit
    root_gate_passed = [int]$rdRootGatePassed
    root_gate_skipped = [int]$rdRootGateSkipped
    protected_blobs_match = [bool]$true
}
Assert-RdRecordShape $rdSealRecord $rdSealKeys
$rdSealPost = Publish-RdRecord $rdStep4Issue $rdSealRecord $rdSealKeys 'seal' $rdTempRoot $rdRunId
$rdSeal = Read-RdRecord $rdStep4Issue $rdSealPost.id $rdSealPost.body
if ([long]$rdSeal.rehearsal_comment_id -ne [long]$rdRehearsalPost.id -or
    [long]$rdSeal.approval_comment_id -ne [long]$rdApprovalPost.id -or
    [string]$rdSeal.capability_verdict -cne 'SUPPORTED') { throw 'reread activation seal mismatch' }
```

Only after that last reread may the coordinator mark Step 4 `DONE`, commit and push the two status
documents, close its issue, and release the PTA Finance and C2E resume boundaries. The status commit
must not alter any product, frozen, decision, selector, resolution, or UAT byte.

## 9. Cleanup

Cleanup never touches `$rdActiveHome`. After the seal is remotely verified, resolve `$rdStage` and
`$rdDisposableHome` again, require both to remain direct children of `$rdTempRoot` with the exact
run-ID names created in §5, and remove only those two disposable trees. If containment or identity is
uncertain, retain them and report their local paths instead of deleting anything.
