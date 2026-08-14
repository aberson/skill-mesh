# Gate A decision packet

## Outcome first

Gate A is `APPROVED` with terminal action `stop`. The one authorized bounded follow-up ran once. It
stopped when Claude lifecycle attempt `a1` returned `FAIL` before the explicit update operation. The
stop rule prevented Codex lifecycle `a1` and the Claude reviewer dispatcher `a0-r1` from running.

No architecture is selected. Goal B authorization is `no`, live cutover is `not-authorized`, and
Phase 2 remains locked. No retry, correction, fallback model, additional host run, product work,
Step 4 use, live-home write, merge, or cutover is authorized. This outcome uses `L-CLAUDE`,
`L-CODEX`, `L-CLAUDE-A1`, `CF-M-CODEX`, `CF-M-CLAUDE`, `CF-D-CODEX`, and `CF-D-CLAUDE`.

## Evidence used

Each reference binds a raw report to its raw evidence manifest.

| Reference | Evidence | Report SHA-256 | Manifest SHA-256 |
|---|---|---|---|
| `L-CLAUDE` | Claude lifecycle | `e478ba1cd8577d89eae6565a62efbf9740629524306143b00bd685e84261ff6d` | `3ac1020e58cd6da00793cbc4641aba46d6fc78cacd37ab3ce570550c5b60b916` |
| `L-CODEX` | Codex lifecycle | `c92b65e8807f01fbdf3e38e83c2e5d1760f8d1484609ffb8197a832e61e3f453` | `58e2e204b43851e63053f7bb3e1977163a17080d86c2e1c12f992052f88ca9bc` |
| `L-CLAUDE-A1` | Claude lifecycle bounded follow-up | `a3b2a90e4ac72b4964db1650cc4812a0646b9e98f78d178c591f912a36933d4f` | `33001429c8d2cdf5d22cf4c30fc4590a49a6376451401137b693b30dcc91ddd9` |
| `CF-M-CODEX` | Final manual Codex run; requested `gpt-5.6-terra` | `1f29c4d4516a674d23e25073278b653346a8f46c8ced1d50eb83dac7b815e5ce` | `174d90314def22df5d5fe50d229354973d873b1b5e58808340a5bbb8771d13c7` |
| `CF-M-CLAUDE` | Final manual Claude-host run; requested `sonnet` | `bfa635ed488d78fb135dfb540ebe26ffcb91c0e4576a31eec1c867d9f5941315` | `a46b30b32e64c0c6e25f7024b2ccf21b684555612d877c51006aa351b676ae6d` |
| `CF-D-CODEX` | Final dispatcher Codex run; requested `gpt-5.6-terra` | `2efac6573b5a606bd5c7ae743811eb3fd786b6fa73e4e90b7fa543eaf504eb4a` | `50137bb7178b1b3685e8e2305882025308379827231ccb11e861e7e025df32ae` |
| `CF-D-CLAUDE` | Final dispatcher Claude-host run; requested `sonnet` | `d372b76ec00abb2e854bcbf56188c4780c8c4792e9390a70d060e1ede6fbdb69` | `c8db1c6dcf3e806cbd293271db3f3cd9aa84b62f716f80d9e7e9dbc20fdfbf9f` |

The external append-only index records earlier attempts and superseded candidates. Its final
SHA-256 is `94d26b399bf700b66d986cde6973023eeaafc9325077621718e4ddbaccb7078f`.
The bounded follow-up appended exactly the `followup-lifecycle-claude-a1-report` and
`followup-lifecycle-claude-a1-manifest` rows. It appended no Codex `a1` or dispatcher `a0-r1` row.
The committed summaries are
`documentation/evidence/goal-a/goala-20260814T021737Z-1b5ec416/lifecycle-report.md` and
`documentation/evidence/goal-a/goala-20260814T021737Z-1b5ec416/cross-family-report.md`.

| Committed packet artifact | SHA-256 |
|---|---|
| Lifecycle summary | `64cbfb215d567113cb2b3f7ffef9b66e5883b556ee95568f8b26a3c07d2970b1` |
| Cross-family summary | `847d58d0479f721d6cc1146ef945a53ee45c54640cbd4780076897790957bdac` |
| Two-report `MANIFEST.sha256` | `301cd34f4667dd56ed17827ea7658c6fba396531fb68f9064d8b12b86dc9be95` |

The two-report manifest excludes itself, this decision packet, and `plan.md` to avoid a hash cycle.

## Evidence-to-decision table

| Evidence | Topic | Observed fact | Inference | Recommendation | Unresolved premise | Smallest valid option | Cost | Step 4 effect |
|---|---|---|---|---|---|---|---|---|
| `L-CLAUDE`, `L-CLAUDE-A1` | Claude lifecycle | Initial `a0` stopped at safety preflight. In the quiet `a1` run, isolated authentication, v1 install, v1 discovery, containment, live-state comparison, and cleanup passed. Before explicit update, a fresh consumer returned the v2 marker, so the required lifecycle behavior failed. | Source-linked or hot-refresh behavior is plausible, but the evidence does not identify the mechanism. | Stop; do not select a lifecycle owner. | Explicit update, enable, disable, uninstall, and post-uninstall behavior remain unknown. | Terminal Gate A stop. | No further run. | Keep frozen. |
| `L-CODEX` | Codex lifecycle | Initial `a0` stopped at safety preflight. Authorized `a1` was not reached after Claude `a1` failed. | No Codex lifecycle conclusion is possible. | Do not select an owner or run another attempt. | Install, discovery, and uninstall are unknown. Native update, enable, and disable remain known gaps. | Terminal Gate A stop. | No further run. | Keep frozen. |
| `CF-M-CODEX` | Codex manual seam; requested `gpt-5.6-terra` | The real review exited `0`, returned `NEEDS_WORK`, and found three of three defects. Resolved identity was unavailable and protected files changed. | The sealed handoff works with the current Codex CLI. Exact model service and live-byte safety are not proved. | Keep as a candidate only. | Trusted resolved identity and quiet-state proof are absent. | Do not approve this reviewer direction now. | No follow-up cost. | No use of Step 4. |
| `CF-D-CODEX` | Codex dispatcher seam; requested `gpt-5.6-terra` | It produced the same verdict and three detections. Identity and live-state evidence remained ambiguous. | The dispatcher seam also works, but one trial cannot show that it is better. | Do not choose this mechanism now. | Repeatability and exact model identity are unknown. | Defer the Codex-reviewer direction. | No follow-up cost. | No use of Step 4. |
| `CF-M-CLAUDE`, `CF-D-CLAUDE` | Claude host, requested `sonnet` | Both earlier Claude calls returned `401`. The authorized dispatcher `a0-r1` was not reached after lifecycle failure. | The earlier authentication failure no longer describes the lifecycle credential check, but Claude reviewer behavior and identity remain unmeasured. | Do not run another reviewer attempt. | Review behavior and resolved identity are unknown. | Terminal Gate A stop. | No further run. | No use of Step 4. |
| `L-CLAUDE-A1`, `CF-M-CODEX`, `CF-M-CLAUDE`, `CF-D-CODEX`, `CF-D-CLAUDE` | Safety and cleanup | Every started host was Job-contained. Claude lifecycle `a1` proved protected-state `MATCH`, an empty Job, and disposable cleanup. | The containment and cleanup boundary worked for the attempted paths. | Preserve the evidence; do not redesign safety controls in Goal A. | Work delegated through an unrelated system service remains outside Job coverage. | Terminal Gate A stop. | None. | No effect. |
| All seven references | Attempt budget | The bounded follow-up was invoked once. Its first required attempt returned `FAIL`, so the committed stop rule prevented both later attempts. | Continuing would exceed the approved experiment contract. | End Goal A. | Any new experiment would require a new goal and new authority. | Terminal Gate A stop. | No further work. | Keep frozen. |

## Terminal Gate A disposition

### Selected action: stop

End Goal A. Keep the Step 4 recovery artifact frozen. Do not start Phase 2 or implement Skill Mesh
product changes.

A terminal stop response states only `gate action=stop`, `Goal B authorization=no`, and
`live cutover=not-authorized`. It creates no architecture packet because no later phase or validator
can consume one. The recovery plan's no-blank rule applies to `proceed` and
`bounded-follow-up-experiment`, which do create architecture-field records. A stop response ends
Goal A instead of inventing lifecycle-owner or Step 4 values that the evidence cannot support.

| Stop-record field | Recorded value |
|---|---|
| Gate action | `stop` |
| Goal B authorization | `no` |
| Live cutover | `not-authorized` |

### Bounded follow-up — consumed

Abraham approved the exact experiment `goal-a-quiescent-qualification-v1`. It was invoked once.
Claude lifecycle `a1` returned `FAIL`, which consumed the authorization and activated its mandatory
stop rule. No retry, correction, fallback, Codex lifecycle `a1`, or dispatcher `a0-r1` is authorized.

### Proceed — unavailable

Not available. The evidence does not select an architecture, and Goal B authorization is `no`.

## Historical bounded follow-up contract — consumed

**CLOSED — EXECUTED ONCE — DO NOT RUN.** The content below preserves the exact authorized contract
and command for audit. It grants no current execution authority.

**Name:** `goal-a-quiescent-qualification-v1`

**Operator prerequisites:**

1. Abraham supplies valid Claude Code authentication before approving the follow-up. Authentication
   maintenance is outside this experiment's authority.
2. Abraham closes active Claude Code, Codex CLI, ChatGPT desktop, and IDE agent sessions.
3. The runs start from a plain PowerShell session after protected Codex databases become quiet.

**Allowed scope:**

- Keep the completed lifecycle `a0` evidence bound to executed candidate
  `3a17746fa1d04c24088effd8f3871afe10f1601f`; do not relabel it.
- The approved follow-up specified corrected lifecycle candidate
  `0c72392ec51da5201c4f3c17272e2b79a32a055d` for both `a1` run slots. Only Claude `a1` ran.
- Reuse the cross-family candidate `7b094897a0e7afc4ffecaeac15f20d2d875614c8` without code changes.
- Create no production router, receipt service, installer, migrator, or live-host file.
- Keep Step 4 frozen and preserve every current attempt.

The follow-up authorized zero live-home writes. The reviewed runners could not write either live
home. Its first required attempt returned `FAIL`, so the approved contract required `stop`.

**Exact read paths:**

- `experiments/recovery/run-lifecycle-probe.ps1`
- `documentation/experiments/lifecycle-runbook.md`
- `experiments/recovery/run-cross-family-probe.ps1`
- `documentation/experiments/cross-family-runbook.md`

**Exact run contract and write paths:**

| Run | Fixed arguments | External evidence leaf | Disposable leaf |
|---|---|---|---|
| Claude Code lifecycle | `-HostName claude -RunId lifecycle-claude-20260814T065643Z-e1ea3dd1 -AttemptId a1 -CandidateSha 0c72392ec51da5201c4f3c17272e2b79a32a055d -RequestedModel sonnet -CredentialMode copy-file -ConsumerTimeoutSeconds 300` | `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\lifecycle\lifecycle-claude-20260814T065643Z-e1ea3dd1\a1\` | `%LOCALAPPDATA%\SkillMesh\Homes\goala-20260814T021737Z-1b5ec416\lifecycle-claude-20260814T065643Z-e1ea3dd1-a1` |
| Codex lifecycle | `-HostName codex -RunId lifecycle-codex-20260814T065645Z-34c7074f -AttemptId a1 -CandidateSha 0c72392ec51da5201c4f3c17272e2b79a32a055d -RequestedModel gpt-5.6-terra -CredentialMode copy-file -ConsumerTimeoutSeconds 300` | `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\lifecycle\lifecycle-codex-20260814T065645Z-34c7074f\a1\` | `%LOCALAPPDATA%\SkillMesh\Homes\goala-20260814T021737Z-1b5ec416\lifecycle-codex-20260814T065645Z-34c7074f-a1` |
| Claude reviewer dispatcher | `-Action Run -Direction gpt-to-claude -Mechanism reviewer-only-dispatcher -RunId cross-gpt-to-claude-reviewer-only-dispatcher-20260814T085608Z-c450d8b6 -AttemptId a0-r1 -CandidateSha 7b094897a0e7afc4ffecaeac15f20d2d875614c8 -RequestedReviewerModel sonnet -CredentialMode copy-file -ReviewerTimeoutSeconds 600` | `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-gpt-to-claude-reviewer-only-dispatcher-20260814T085608Z-c450d8b6\a0-r1\` | `%LOCALAPPDATA%\SkillMesh\Homes\goala-20260814T021737Z-1b5ec416\cross-gpt-to-claude-reviewer-only-dispatcher-20260814T085608Z-c450d8b6-a0-r1` |

This exact block was run once from Windows PowerShell 5.1 after Abraham approved the contract. It is
retained only as historical evidence. Do not run it again.

```powershell
$ErrorActionPreference = 'Stop'
$GoalAId = 'goala-20260814T021737Z-1b5ec416'
$RepoRoot = Join-Path $env:LOCALAPPDATA "SkillMesh\Worktrees\$GoalAId"
$LifecycleRunner = Join-Path $RepoRoot 'experiments\recovery\run-lifecycle-probe.ps1'
$CrossRunner = Join-Path $RepoRoot 'experiments\recovery\run-cross-family-probe.ps1'
$EvidenceRoot = Join-Path $env:LOCALAPPDATA "SkillMesh\Evidence\$GoalAId"
$EvidenceIndex = Join-Path $EvidenceRoot 'evidence-index.md'
$HomesRoot = Join-Path $env:LOCALAPPDATA "SkillMesh\Homes\$GoalAId"
$LiveClaudeHome = Join-Path $env:USERPROFILE '.claude'
$LiveCodexHome = Join-Path $env:USERPROFILE '.codex'
$LifecycleAttemptId = 'a1'
$CrossAttemptId = 'a0-r1'
$env:GIT_OPTIONAL_LOCKS = '0'

Set-Location -LiteralPath $RepoRoot
if ((git branch --show-current).Trim() -cne 'recovery/goala-20260814T021737Z-1b5ec416') {
    throw 'Wrong Goal A branch'
}
$RepositoryStatus = @(git status --porcelain=v1 --untracked-files=all)
if ($LASTEXITCODE -ne 0 -or $RepositoryStatus.Count -ne 0) {
    throw 'Goal A worktree must be clean before the follow-up'
}

function Test-ExactBytes {
    param([byte[]]$Left, [byte[]]$Right)
    if ($Left.Length -ne $Right.Length) { return $false }
    for ($Index = 0; $Index -lt $Left.Length; $Index++) {
        if ($Left[$Index] -ne $Right[$Index]) { return $false }
    }
    return $true
}

if (-not (Test-Path -LiteralPath $EvidenceIndex -PathType Leaf)) { throw 'Evidence index is missing' }
if ((Get-Item -LiteralPath $EvidenceIndex -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw 'Evidence index is a reparse point'
}
$script:ExpectedIndexBytes = [IO.File]::ReadAllBytes($EvidenceIndex)

function Get-ExperimentResult {
    param([Parameter(Mandatory = $true)][string]$ReportPath)

    if (-not (Test-Path -LiteralPath $ReportPath -PathType Leaf)) {
        throw "Missing report: $ReportPath"
    }
    $Text = [System.IO.File]::ReadAllText($ReportPath)
    $Match = [regex]::Match(
        $Text,
        '(?ms)^## Result\r?\n\r?\n\*\*(PASS|PARTIAL|FAIL|AMBIGUOUS)\*\*'
    )
    if (-not $Match.Success) { throw "Report result is missing or invalid: $ReportPath" }
    return $Match.Groups[1].Value
}

function Assert-AllowedCodexPartial {
    param([Parameter(Mandatory = $true)][string]$ReportPath)

    $Text = [System.IO.File]::ReadAllText($ReportPath)
    $Rows = @([regex]::Matches(
        $Text,
        '(?m)^\| (?<id>[^|]+?) \| (?<status>PASS|PARTIAL|FAIL|AMBIGUOUS|UNAVAILABLE) \|'
    ) | ForEach-Object {
        [pscustomobject]@{
            Id = $_.Groups['id'].Value.Trim()
            Status = $_.Groups['status'].Value
        }
    })
    $NonPass = @($Rows | Where-Object { $_.Status -ne 'PASS' })
    $AllowedIds = @('repeat-add', 'repeat-add-observation', 'native-update', 'native-enable-disable')
    if ($NonPass.Count -eq 0) { throw 'Codex PARTIAL has no unavailable operation' }
    if (@($NonPass | Where-Object { $_.Status -ne 'UNAVAILABLE' }).Count -ne 0) {
        throw 'Codex PARTIAL contains a result other than PASS or UNAVAILABLE'
    }
    if (@($NonPass | Where-Object { $_.Id -notin $AllowedIds }).Count -ne 0) {
        throw 'Codex PARTIAL is not limited to the approved native-operation gap'
    }
    if ('native-update' -notin $NonPass.Id -or 'native-enable-disable' -notin $NonPass.Id) {
        throw 'Codex PARTIAL does not record the known update, enable, and disable gap'
    }
}

function Publish-EvidencePair {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$RelativeRoot,
        [Parameter(Mandatory = $true)][string]$ReportId,
        [Parameter(Mandatory = $true)][string]$ManifestId,
        [Parameter(Mandatory = $true)][string]$ManifestName,
        [Parameter(Mandatory = $true)][string]$Producer
    )

    $ReportPath = Join-Path $Directory 'report.md'
    $ManifestPath = Join-Path $Directory $ManifestName
    foreach ($Path in @($ReportPath, $ManifestPath)) {
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing evidence: $Path" }
        if ((Get-Item -LiteralPath $Path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Evidence is a reparse point: $Path"
        }
    }

    $DirectoryFull = [IO.Path]::GetFullPath($Directory).TrimEnd('\')
    $DirectoryPrefix = $DirectoryFull + '\'
    $ManifestText = [IO.File]::ReadAllText($ManifestPath)
    $Lines = @($ManifestText -split '\r?\n' | Where-Object { $_ -ne '' })
    if ($Lines.Count -eq 0) { throw "Empty manifest: $ManifestPath" }
    $Listed = New-Object System.Collections.Generic.List[string]
    foreach ($Line in $Lines) {
        $Match = [regex]::Match($Line, '^([0-9a-f]{64})  (.+)$')
        if (-not $Match.Success) { throw "Invalid manifest line: $Line" }
        $Relative = $Match.Groups[2].Value.Replace('/', '\')
        if ([IO.Path]::IsPathRooted($Relative)) { throw "Absolute manifest path: $Relative" }
        $Full = [IO.Path]::GetFullPath((Join-Path $DirectoryFull $Relative))
        if (-not $Full.StartsWith($DirectoryPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Manifest path escapes its evidence leaf: $Relative"
        }
        if (-not (Test-Path -LiteralPath $Full -PathType Leaf)) { throw "Missing manifest entry: $Relative" }
        if ((Get-Item -LiteralPath $Full -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Manifest entry is a reparse point: $Relative"
        }
        $ActualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Full).Hash.ToLowerInvariant()
        if ($ActualHash -cne $Match.Groups[1].Value) { throw "Manifest hash mismatch: $Relative" }
        $null = $Listed.Add($Relative.Replace('\', '/'))
    }

    $Actual = @(Get-ChildItem -LiteralPath $DirectoryFull -Recurse -Force -File |
        Where-Object { -not $_.FullName.Equals($ManifestPath, [StringComparison]::OrdinalIgnoreCase) } |
        ForEach-Object { $_.FullName.Substring($DirectoryPrefix.Length).Replace('\', '/') } |
        Sort-Object -Unique)
    $ListedSorted = @($Listed | Sort-Object -Unique)
    if ($ListedSorted.Count -ne $Lines.Count) { throw "Duplicate manifest entry: $ManifestPath" }
    if (@(Compare-Object -ReferenceObject $Actual -DifferenceObject $ListedSorted).Count -ne 0) {
        throw "Manifest coverage mismatch: $ManifestPath"
    }

    if (-not (Test-Path -LiteralPath $EvidenceIndex -PathType Leaf)) { throw 'Evidence index is missing' }
    if ((Get-Item -LiteralPath $EvidenceIndex -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'Evidence index is a reparse point'
    }
    $CurrentIndexBytes = [IO.File]::ReadAllBytes($EvidenceIndex)
    if (-not (Test-ExactBytes $CurrentIndexBytes $script:ExpectedIndexBytes)) {
        throw 'Evidence index changed outside this append operation'
    }
    $CurrentIndex = [Text.Encoding]::UTF8.GetString($CurrentIndexBytes)
    foreach ($Id in @($ReportId, $ManifestId)) {
        if ($CurrentIndex.Contains($Id)) { throw "Evidence ID already exists: $Id" }
    }
    $ReportHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ReportPath).Hash.ToLowerInvariant()
    $ManifestHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ManifestPath).Hash.ToLowerInvariant()
    $Rows = @(
        ('| `{0}` | `{1}` | `{2}` | {3} |' -f
            $ReportId, "$RelativeRoot\report.md", $ReportHash, $Producer),
        ('| `{0}` | `{1}` | `{2}` | {3}; complete manifest verified |' -f
            $ManifestId, "$RelativeRoot\$ManifestName", $ManifestHash, $Producer)
    )
    $Utf8NoBom = New-Object Text.UTF8Encoding($false)
    $RowText = ($Rows -join [Environment]::NewLine) + [Environment]::NewLine
    $RowBytes = $Utf8NoBom.GetBytes($RowText)
    $ExpectedAfter = New-Object byte[] ($script:ExpectedIndexBytes.Length + $RowBytes.Length)
    [Buffer]::BlockCopy($script:ExpectedIndexBytes, 0, $ExpectedAfter, 0, $script:ExpectedIndexBytes.Length)
    [Buffer]::BlockCopy($RowBytes, 0, $ExpectedAfter, $script:ExpectedIndexBytes.Length, $RowBytes.Length)
    [IO.File]::AppendAllText($EvidenceIndex, $RowText, $Utf8NoBom)
    $ActualAfter = [IO.File]::ReadAllBytes($EvidenceIndex)
    if (-not (Test-ExactBytes $ActualAfter $ExpectedAfter)) {
        throw 'Evidence-index append bytes do not match the two reviewed rows'
    }
    $script:ExpectedIndexBytes = $ExpectedAfter
}

foreach ($item in @(
    @{ HostName = 'claude'; RunId = 'lifecycle-claude-20260814T065643Z-e1ea3dd1'; Model = 'sonnet' },
    @{ HostName = 'codex'; RunId = 'lifecycle-codex-20260814T065645Z-34c7074f'; Model = 'gpt-5.6-terra' }
)) {
    $EvidenceDir = Join-Path $EvidenceRoot "lifecycle\$($item.RunId)\$LifecycleAttemptId"
    $DisposableHome = Join-Path $HomesRoot "$($item.RunId)-$LifecycleAttemptId"
    $Arguments = @(
        '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-File', $LifecycleRunner,
        '-HostName', $item.HostName,
        '-GoalAId', $GoalAId,
        '-DisposableHome', $DisposableHome,
        '-LiveClaudeHome', $LiveClaudeHome,
        '-LiveCodexHome', $LiveCodexHome,
        '-EvidenceDir', $EvidenceDir,
        '-RunId', $item.RunId,
        '-AttemptId', $LifecycleAttemptId,
        '-CandidateSha', '0c72392ec51da5201c4f3c17272e2b79a32a055d',
        '-RequestedModel', $item.Model,
        '-CredentialMode', 'copy-file',
        '-ConsumerTimeoutSeconds', '300'
    )
    & powershell.exe @Arguments -WhatIf
    if ($LASTEXITCODE -ne 0) { throw "$($item.HostName) lifecycle WhatIf failed" }
    & powershell.exe @Arguments
    $LifecycleExit = $LASTEXITCODE
    $LifecycleReport = Join-Path $EvidenceDir 'report.md'
    $LifecycleResult = Get-ExperimentResult -ReportPath $LifecycleReport
    $LifecyclePrefix = "followup-lifecycle-$($item.HostName)-$LifecycleAttemptId"
    Publish-EvidencePair `
        -Directory $EvidenceDir `
        -RelativeRoot "lifecycle\$($item.RunId)\$LifecycleAttemptId" `
        -ReportId "$LifecyclePrefix-report" `
        -ManifestId "$LifecyclePrefix-manifest" `
        -ManifestName 'manifest.sha256' `
        -Producer "Gate A bounded follow-up: $($item.HostName) lifecycle $LifecycleResult"
    if ($item.HostName -eq 'claude') {
        if ($LifecycleExit -ne 0 -or $LifecycleResult -ne 'PASS') {
            throw 'Claude lifecycle did not return PASS; stop the follow-up'
        }
    }
    elseif ($LifecycleResult -eq 'PASS') {
        if ($LifecycleExit -ne 0) { throw 'Codex PASS returned the wrong exit code' }
    }
    elseif ($LifecycleResult -eq 'PARTIAL') {
        if ($LifecycleExit -ne 1) { throw 'Codex PARTIAL returned the wrong exit code' }
        Assert-AllowedCodexPartial -ReportPath $LifecycleReport
    }
    else {
        throw "Codex lifecycle returned $LifecycleResult; stop the follow-up"
    }
}

$CrossRunId = 'cross-gpt-to-claude-reviewer-only-dispatcher-20260814T085608Z-c450d8b6'
$CrossEvidenceDir = Join-Path $EvidenceRoot "cross-family\$CrossRunId\$CrossAttemptId"
$FixtureRoot = Join-Path $HomesRoot "$CrossRunId-$CrossAttemptId"
$CrossArguments = @(
    '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
    '-File', $CrossRunner,
    '-GoalAId', $GoalAId,
    '-Action', 'Run',
    '-Direction', 'gpt-to-claude',
    '-Mechanism', 'reviewer-only-dispatcher',
    '-FixtureRoot', $FixtureRoot,
    '-CandidateSha', '7b094897a0e7afc4ffecaeac15f20d2d875614c8',
    '-EvidenceDir', $CrossEvidenceDir,
    '-RunId', $CrossRunId,
    '-AttemptId', $CrossAttemptId,
    '-LiveClaudeHome', $LiveClaudeHome,
    '-LiveCodexHome', $LiveCodexHome,
    '-RequestedReviewerModel', 'sonnet',
    '-CredentialMode', 'copy-file',
    '-ReviewerTimeoutSeconds', '600'
)
& powershell.exe @CrossArguments -WhatIf
if ($LASTEXITCODE -ne 0) { throw 'Claude reviewer WhatIf failed' }
& powershell.exe @CrossArguments
$CrossExit = $LASTEXITCODE
$CrossResult = Get-ExperimentResult -ReportPath (Join-Path $CrossEvidenceDir 'report.md')
Publish-EvidencePair `
    -Directory $CrossEvidenceDir `
    -RelativeRoot "cross-family\$CrossRunId\$CrossAttemptId" `
    -ReportId 'followup-cross-dispatcher-claude-a0-r1-report' `
    -ManifestId 'followup-cross-dispatcher-claude-a0-r1-manifest' `
    -ManifestName 'MANIFEST.sha256' `
    -Producer "Gate A bounded follow-up: Claude reviewer dispatcher $CrossResult"
if ($CrossExit -ne 0 -or $CrossResult -ne 'PASS') {
    throw "Claude reviewer returned $CrossResult; stop the follow-up"
}

$RepositoryStatusAfter = @(git status --porcelain=v1 --untracked-files=all)
if ($LASTEXITCODE -ne 0 -or $RepositoryStatusAfter.Count -ne 0) {
    throw 'A runner changed the Goal A worktree; stop before indexing evidence'
}

$CleanupTargets = @(
    (Join-Path $HomesRoot 'lifecycle-claude-20260814T065643Z-e1ea3dd1-a1'),
    (Join-Path $HomesRoot 'lifecycle-codex-20260814T065645Z-34c7074f-a1'),
    (Join-Path $HomesRoot 'cross-gpt-to-claude-reviewer-only-dispatcher-20260814T085608Z-c450d8b6-a0-r1'),
    (Join-Path $env:TEMP 'SkillMesh\CrossFamilyRuntime\cross-gpt-to-claude-reviewer-only-dispatcher-20260814T085608Z-c450d8b6-a0-r1')
)
foreach ($Target in $CleanupTargets) {
    if (Test-Path -LiteralPath $Target) { throw "Disposable path remains: $Target" }
}

```

No argument was changed. The block is consumed and must not run again.

The block ran until the required stop and indexed only Claude lifecycle `a1`. That attempt returned
`FAIL` before the explicit update command. Codex lifecycle `a1` and the Claude reviewer dispatcher
`a0-r1` were not invoked.

The cross-family run can create only this additional temporary runtime root:

`$env:TEMP\SkillMesh\CrossFamilyRuntime\cross-gpt-to-claude-reviewer-only-dispatcher-20260814T085608Z-c450d8b6-a0-r1`

That root has create-new semantics and must be absent after the run.

The runners only read the external evidence index. After rehashing each complete attempt, the
operator appends exactly one report row and one manifest row per attempt. A successful three-run
follow-up adds six rows. An early stop adds two rows for each completed attempt before it stops. The
rows go to `$env:LOCALAPPDATA\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\evidence-index.md`.
Only these tracked packet paths can change after the follow-up:

- `documentation/evidence/goal-a/goala-20260814T021737Z-1b5ec416/lifecycle-report.md`
- `documentation/evidence/goal-a/goala-20260814T021737Z-1b5ec416/cross-family-report.md`
- `documentation/evidence/goal-a/goala-20260814T021737Z-1b5ec416/MANIFEST.sha256`
- `documentation/decisions/gate-a.md`
- `plan.md`

Every other repository path and live-home path is read-only.

**Historical attempt limit — consumed:**

- One corrected `a1` for lifecycle series `lifecycle-claude-20260814T065643Z-e1ea3dd1`, bound to
  candidate `0c72392ec51da5201c4f3c17272e2b79a32a055d`.
- One corrected `a1` for lifecycle series `lifecycle-codex-20260814T065645Z-34c7074f`, bound to
  candidate `0c72392ec51da5201c4f3c17272e2b79a32a055d`.
- One byte-identical `a0-r1` for dispatcher series
  `cross-gpt-to-claude-reviewer-only-dispatcher-20260814T085608Z-c450d8b6` after valid authentication
  is supplied outside the experiment.
- No manual-handoff rerun, Codex-reviewer rerun, runner edit, retry, or correction.
- Any preflight or evidence ambiguity returns to Gate A as `stop`.

**Required exit evidence — not met:**

- Claude Code lifecycle is `PASS`.
- Codex lifecycle can be `PARTIAL` only for missing native update, enable, or disable operations.
  Every available lifecycle, source, safety, containment, and cleanup check must pass.
- The Claude reviewer authenticates and completes one real dispatcher cross-family review.
- The overall cross-family result is `PASS`.
- The request is exactly `sonnet`. The resolved status is `provider-reported`, and the resolved
  identity satisfies the runner's approved Sonnet policy.
- The runner configures and selects no fallback or retry, and exactly one reviewer starts.
  Fallback-attempt telemetry can remain `unavailable`; it is not treated as proof of absence.
- The report contains a complete rehashed manifest, a new external-index row, exact candidate
  identity, Job-empty proof, protected-live-state `MATCH`, three seeded detections, no unmatched
  finding, and no consistency warning.
- Any future release direction is explicitly asymmetric: GPT-family origin role to Claude reviewer.
- Any `AMBIGUOUS`, `FAIL`, authentication problem, preflight problem, or requested correction ends
  the follow-up as `stop`. No additional run is authorized.

Claude lifecycle `a1` returned `FAIL`. This activated the final bullet and closed the experiment.

**Historical estimated operator cost:** supply a credential established outside this experiment,
close active agent sessions, and run up to three host experiments. The actual run stopped after the
first experiment. No product code or live installation was included. The contract and its exit
criteria are bound to the evidence references above.

## Historical choice glossary

These definitions preserve the choices that existed before the terminal decision. They do not
approve an architecture or authorize another experiment.

### Gate action

| Value | Meaning | Tradeoff |
|---|---|---|
| `proceed` | Select every architecture field and permit Goal B when its value is also `yes`. | Requires decisive evidence; current evidence makes this value invalid. |
| `bounded-follow-up-experiment` | Authorize only one exact experiment and defer unresolved architecture fields. | Concrete field values constrain the experiment but unlock no implementation. |
| `stop` | End Goal A without selecting an architecture. | Preserves recovery evidence but starts no control or product work. |

### Lifecycle owner

| Value | Meaning | Tradeoff |
|---|---|---|
| `native` | The host owns install, update, enable, disable, and uninstall. | Smallest Skill Mesh surface, but only valid when native behavior passes. |
| `bounded-compatibility` | Skill Mesh fills only an exact native lifecycle gap. | Adds a limited maintenance surface and needs explicit retirement criteria. |
| `rechartered-installer` | A separately approved safety subsystem owns lifecycle behavior. | Highest implementation and rollback burden; it requires its own subplan. |
| `deferred-by-follow-up` | No owner is selected until the named experiment finishes. | Keeps product work locked and costs another operator run. |

### Step 4 disposition

| Value | Meaning | Recovery effect |
|---|---|---|
| `archive-only` | Keep the preserved bytes only as historical and recovery evidence. | Never merge or execute Step 4. The external recovery bundle remains the restore source. |
| `one-time-manual-cutover` | Use approved Step 4 logic once through a Gate D runbook. | Retain the recovery bundle through the rollback window; do not maintain an installer. |
| `bounded-legacy-utility` | Keep only named Step 4 functions with tests, an owner, and retirement criteria. | Recovery covers that exact utility until retirement; all other Step 4 bytes stay archived. |
| `candidate-input-to-rechartered-installer` | Treat Step 4 as design input for a new installer safety subsystem. | Do not merge Step 4 directly. The new subsystem needs separate approval and rollback proof. |
| `deferred-by-follow-up` | Preserve and freeze Step 4 while evidence remains incomplete. | No Step 4 byte enters a candidate. The existing recovery bundle remains authoritative. |

### Cross-family mechanism and direction

| Value | Meaning | Tradeoff or failure behavior |
|---|---|---|
| `manual-saved-handoff` | An operator saves a hashed packet, checkpoints it, and invokes the reviewer. | Highest operator work; failure retains the sealed packet and receipt. |
| `reviewer-only-dispatcher` | A bounded dispatcher invokes one reviewer with no general routing or fallback. | Less operator work; adds one narrow automation boundary and receipt contract. |
| `manual-now-automation-deferred` | The manual handoff remains release proof while automation is postponed. | Ships less automation now; a later decision must approve a dispatcher. |
| `stop` | Release has no cross-family review seam. | Ends this requirement instead of substituting an unproved mechanism. |
| `deferred-by-follow-up` | No mechanism is selected until the named follow-up finishes. | Keeps Phase 2 locked. |

| Direction | Meaning | Coverage and tradeoff |
|---|---|---|
| `claude-to-gpt` | A synthetic Claude-family origin role sends the fixture to a real Codex reviewer. | Covers one reviewer direction. The requested GPT model is not a resolved-model claim. |
| `gpt-to-claude` | A synthetic GPT-family origin role sends the fixture to a real Claude reviewer. | Covers the opposite direction. Provider-reported reviewer identity remains required. |
| Both directions | Execute and retain both direction contracts. | Gives symmetric mechanism coverage at roughly twice the model and operator cost. |
| `deferred-by-follow-up` | Select no release direction yet. | Keeps Phase 2 locked until the named evidence arrives. |

The origin role is synthetic in every direction; it does not prove which model built the fixture.
Any one-direction choice must state the visible asymmetry.

### Remaining Gate A fields

| Field and value | Meaning and tradeoff |
|---|---|
| Copilot `quarantine` | Keep Copilot evidence and code out of the release path. |
| Copilot `compatibility-only` | Retain an explicitly labeled legacy compatibility surface; it cannot stand in for Codex. |
| Copilot `deferred-by-follow-up` | Make no Copilot disposition until the named experiment finishes. |
| Identity waiver `none` | Require the normal resolved-identity evidence. |
| Identity waiver `<host/lane/reason/expiry>` | Accept one exact, time-bounded identity gap. The waiver cannot imply a resolved model. |
| Identity waiver `deferred-by-follow-up` | Select no waiver until the named experiment finishes. |
| Control branch `reference-only` | Read `fix/plan-expedite-explicit-handoff@875de2a`; import no bytes. |
| Control branch `park` | Exclude that branch from Phase 2. |
| Control branch `bounded-adoption-plan` | Reimplement only named ideas through a later approved plan; never silently cherry-pick. |
| Control branch `stop` | End control repair because the branch conflict is unacceptable. |
| Control branch `deferred-by-follow-up` | Select no branch disposition until the named experiment finishes. |
| Goal B `yes` | Start Phase 2 only when Gate action is also `proceed`. |
| Goal B `no` | Keep Phase 2 locked. |
| Live cutover `not-authorized` | Permit no live install or cutover. This value is mandatory at Gate A. |

## Historical bounded-follow-up field values — consumed

Abraham approved these values for the one bounded follow-up. The first required attempt returned
`FAIL`; the stop rule consumed and closed that authority. The table is retained only as provenance.

| Field | Historical approved value | Meaning and tradeoff |
|---|---|---|
| Gate action | `bounded-follow-up-experiment` | Gain decisive evidence without starting product work. |
| Lifecycle owner for Claude Code | `deferred-by-follow-up` | No lifecycle owner is selected yet. |
| Lifecycle owner for Codex | `deferred-by-follow-up` | No lifecycle owner is selected yet. |
| Step 4 disposition | `deferred-by-follow-up` | Preserve and freeze the bytes until evidence selects a path. |
| Cross-family mechanism | `deferred-by-follow-up` | Manual and dispatcher remain candidates only. |
| Permitted cross-family direction | `deferred-by-follow-up` | No release direction is approved. |
| Copilot disposition | `quarantine` | Copilot evidence cannot stand in for Codex evidence. |
| Resolved-identity waiver | `none` | Do not weaken exact-model transparency. |
| Existing control branch | `reference-only` | It can inform later work but contributes no bytes now. |
| Goal B authorization | `no` | Phase 2 remains locked. |
| Live cutover | `not-authorized` | No live install or cutover. |

## Abraham's decision

**Status:** `APPROVED`

**Decision locator:** Abraham's 2026-08-14 direct conversation response supplying the exact three
terminal values below after the bounded follow-up result was reported.

| Terminal record field | Approved value |
|---|---|
| Gate action | `stop` |
| Goal B authorization | `no` |
| Live cutover | `not-authorized` |

This decision ends Goal A. It creates no architecture packet or remaining architecture-field record.
It authorizes no retry, correction, fallback model, additional host run, Phase 2, Goal B, product
work, Step 4 use, live-home write, merge, or live cutover.
