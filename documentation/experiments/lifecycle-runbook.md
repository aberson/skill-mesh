# Goal A lifecycle experiment runbook

## Result

Run this procedure only after Step 74 is committed and its full commit SHA is in the external Goal A
evidence index. The procedure creates two disposable host profiles. It does not write to either live
host profile.

Expected results:

- Claude Code can return `PASS` if every native lifecycle operation works.
- Codex can return `PARTIAL` because Codex CLI 0.147.0 has no native plugin update, enable, or
  disable command.
- `FAIL` means the evidence identifies a required behavior that did not work.
- `AMBIGUOUS` means the evidence cannot support an architecture choice.

## Before you run

1. Close other Claude Code and Codex processes that can change plugin settings.
2. Run from the clean Goal A worktree.
3. Confirm `plan.md` names the expected Goal A ID.
4. Confirm `evidence-index.md` has exactly one `step74-candidate` row.
5. Do not edit the runner, fixture, template, or this runbook after that commit.

The runner copies only the selected host credential file into its disposable profile. It removes
inherited provider credentials and gives the child isolated home directories. Codex also uses a
strict disposable configuration that selects file-based authentication. Credential bytes are not
logged. The live-root check compares them with an ephemeral keyed HMAC; neither the key nor a
reusable credential digest is retained. The runner deletes the disposable profile in its guarded
cleanup.

## Copy-paste procedure

Run this entire block from the Skill Mesh repository root in Windows PowerShell 5.1:

```powershell
$ErrorActionPreference = 'Stop'
$goalAId = 'goala-20260814T021737Z-1b5ec416'
$goalRoot = Join-Path $env:LOCALAPPDATA "SkillMesh\Evidence\$goalAId"
$evidenceIndex = Join-Path $goalRoot 'evidence-index.md'
$candidateLines = @(Select-String -LiteralPath $evidenceIndex -Pattern '^\| `step74-candidate`')
if ($candidateLines.Count -ne 1) { throw "Expected one step74-candidate row; found $($candidateLines.Count)" }
$candidateLine = $candidateLines[0]
$candidateSha = [regex]::Match($candidateLine.Line, '[0-9a-f]{40}').Value
if ($candidateSha -notmatch '^[0-9a-f]{40}$') { throw 'Step 74 candidate SHA is invalid' }

$recordedGoalA = Select-String -LiteralPath .\plan.md -Pattern '^\*\*GoalAId:\*\* `([^`]+)`$'
if (-not $recordedGoalA -or $recordedGoalA.Matches[0].Groups[1].Value -ne $goalAId) {
    throw 'plan.md does not name the expected Goal A ID'
}

function New-EightHex {
    $bytes = New-Object byte[] 4
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return ([System.BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}

$runner = (Resolve-Path .\experiments\recovery\run-lifecycle-probe.ps1).Path
$liveClaudeHome = Join-Path $env:USERPROFILE '.claude'
$liveCodexHome = Join-Path $env:USERPROFILE '.codex'
$series = @(
    [pscustomobject]@{ HostName = 'claude'; RequestedModel = 'sonnet' },
    [pscustomobject]@{ HostName = 'codex'; RequestedModel = 'gpt-5.6-terra' }
)

foreach ($item in $series) {
    $stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
    $runId = "lifecycle-$($item.HostName)-$stamp-$(New-EightHex)"
    $attemptId = 'a0'
    $evidenceDir = Join-Path $goalRoot "lifecycle\$runId\$attemptId"
    $disposableHome = Join-Path $env:LOCALAPPDATA "SkillMesh\Homes\$goalAId\$runId-$attemptId"
    $arguments = @(
        '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', $runner,
        '-HostName', $item.HostName,
        '-GoalAId', $goalAId,
        '-DisposableHome', $disposableHome,
        '-LiveClaudeHome', $liveClaudeHome,
        '-LiveCodexHome', $liveCodexHome,
        '-EvidenceDir', $evidenceDir,
        '-RunId', $runId,
        '-AttemptId', $attemptId,
        '-CandidateSha', $candidateSha,
        '-RequestedModel', $item.RequestedModel,
        '-CredentialMode', 'copy-file',
        '-ConsumerTimeoutSeconds', '300'
    )

    & powershell.exe @arguments -WhatIf
    if ($LASTEXITCODE -ne 0) { throw "$($item.HostName) WhatIf failed with exit $LASTEXITCODE" }

    & powershell.exe @arguments
    $resultCode = $LASTEXITCODE
    if ($resultCode -notin @(0, 1)) {
        throw "$($item.HostName) stopped with exit $resultCode; retain its evidence and do not invent a replacement result"
    }
    Write-Host "$($item.HostName) evidence: $evidenceDir"
}
```

`-WhatIf` validates every path and prints the complete operation plan. It creates no file and launches
no host command. The actual invocation uses the same paths.

## Corrected attempts

Use the same run ID for a correction. Change `AttemptId` to `a1` or `a2`. Change both the evidence
directory leaf and disposable-home suffix to match. Run `-WhatIf` again before the actual command.

A byte-identical rerun uses `a0-r1`, `a1-r1`, or `a2-r1`. Retain all earlier attempts. If the runner
or fixture changes, return to Step 74 and commit a new candidate. Do not label that change as another
attempt against the old candidate.

## Exit codes

| Exit | Meaning | Next action |
|---:|---|---|
| 0 | `PASS` | Retain the report and manifest. |
| 1 | Evidence-complete `PARTIAL` or `FAIL` | Retain the report. Use its stated result. |
| 2 | Unsafe or invalid precondition | Correct the precondition before any host mutation. |
| 3 | `AMBIGUOUS` or cleanup refusal | Stop. Retain all evidence. Check whether guarded cleanup removed the home. |

Do not manually delete a retained home after exit 3. A cleanup refusal means the reviewed ownership
or path proof did not pass. The runner can still remove the home after an ambiguous measurement when
the cleanup proof succeeds. Inspect `report.md` before authorizing any new cleanup action. If the
runner stopped before it could create that report, inspect `fallback-report.txt` instead.

## Required retained evidence

Each attempt must retain `manifest.sha256` and either `report.md` or the fail-closed
`fallback-report.txt`. A completed lifecycle attempt also retains the candidate archive, v1 and v2
source trees, redacted command records, consumer inventories, and both live-surface snapshots.
Confirm that the manifest covers every retained file except itself.

The candidate-owned snapshot helper runs as `python -I -B`. Each complete snapshot is limited to 120
seconds and 100,000 records. The live-surface evidence covers the complete Claude, Codex, and sibling
`.agents` roots. It records local junction targets separately. The only permitted concurrent change
is append-only growth in the same exact Codex session file that the preflight sample found active.
That exception makes live-root attribution `UNAVAILABLE` and the run no better than `PARTIAL`.
In-place activity in a pre-existing Codex runtime database or sidecar makes the result `AMBIGUOUS`
and stops the lifecycle experiment before a host command runs. Creation, deletion, replacement, or
change to any other path is also ambiguous.

Every native host command starts suspended inside an unnamed Windows Job Object. The runner assigns
the process before it resumes, enables kill-on-close, and confirms that the Job Object has no active
process before another command or cleanup. A timeout or surviving descendant makes the run
`AMBIGUOUS`; the runner terminates the whole Job Object before safe cleanup. This containment covers
ordinary child processes created by the CLI. Work delegated through an unrelated system service or
Windows Management Instrumentation broker is outside this bounded experiment and remains an
explicit premise.
