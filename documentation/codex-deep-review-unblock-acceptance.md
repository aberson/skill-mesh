# Phase CD Step 156: installed proof and activation

This procedure is not an acceptance result. The code-only source mapping remains
unqualified until Step 156. Run after Step 155 is accepted in a fresh host with the
required capabilities. An ordinary CLI can fail this probe: record INCOMPLETE.
No host/model switch, consumer gate change or retry-budget reset is implied.

## Contained disposable lifecycle

Run from the accepted Skill Mesh checkout in the capable collaboration host. First
define these functions. Cleanup checks the resolved root and rejects reparse points
before recursion. This is a pre-delete check, not race-free OS isolation. Refusal
preserves the tree for inspection and leaves Step 156 INCOMPLETE. All processes run
foreground; there are no background watchers or jobs to leave behind.

```powershell
# CD156 lifecycle
function Assert-Cd156Tree([string]$cdPath) {
    $cdTemp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\','/')
    $cdFull = [IO.Path]::GetFullPath($cdPath).TrimEnd('\','/')
    if ((Split-Path -Parent $cdFull) -ne $cdTemp -or
        (Split-Path -Leaf $cdFull) -notmatch '^cd156-[a-f0-9]{32}$') {
        throw 'INCOMPLETE: disposable root containment failed'
    }
    $cdCursor = Get-Item -LiteralPath $cdFull -Force
    while ($null -ne $cdCursor) {
        if ($cdCursor.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw 'INCOMPLETE: reparse ancestor'
        }
        $cdCursor = $cdCursor.Parent
    }
    $cdQueue = New-Object 'System.Collections.Generic.Queue[string]'
    $cdQueue.Enqueue($cdFull)
    while ($cdQueue.Count -gt 0) {
        foreach ($cdEntry in Get-ChildItem -LiteralPath $cdQueue.Dequeue() -Force) {
            if ($cdEntry.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw 'INCOMPLETE: reparse entry; preserve tree for inspection'
            }
            if ($cdEntry.PSIsContainer) { $cdQueue.Enqueue($cdEntry.FullName) }
        }
    }
    return $cdFull
}

function Invoke-Cd156Disposable([string]$cdRoot, [scriptblock]$cdAction) {
    try {
        $null = Assert-Cd156Tree $cdRoot
        & $cdAction
    } finally {
        $cdSafeRoot = Assert-Cd156Tree $cdRoot
        Remove-Item -LiteralPath $cdSafeRoot -Recurse -Force -ErrorAction Stop
    }
}
```

## Setup and fresh host

Retain evidence outside the disposable cleanup root. Prefer a safe snapshot of
pending useful work when available; the following small fixture is solely a
workflow-boundary proof. Preserve the host's current authentication and environment:
do not reset HOME, USERPROFILE or CODEX_HOME or copy authentication files. The fresh
coordinator explicitly loads the disposable installed paths; this tests explicit
skill loading, not automatic native discovery.

```powershell
$ErrorActionPreference = 'Stop'
$cdSource = (Get-Location).Path
$cdToken = [Guid]::NewGuid().ToString('N')
$cdRoot = Join-Path ([IO.Path]::GetTempPath()) ('cd156-' + $cdToken)
$cdEvidence = Join-Path $cdSource ('.build-step/cd156-evidence-' + $cdToken)
$cdFixture = Join-Path $cdRoot 'fixture'
$cdHome = Join-Path $cdRoot 'home'
$cdUtf8 = New-Object Text.UTF8Encoding($false)
New-Item -ItemType Directory -Path $cdRoot,$cdFixture,$cdHome,$cdEvidence | Out-Null
try {
    & powershell -NoProfile -File (Join-Path $cdSource 'tools/build-distributions.ps1') -Provider all
    if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: build failed' }
    & powershell -NoProfile -File (Join-Path $cdSource 'tools/install-skill-mesh.ps1') -Provider codex -Home $cdHome -DistDir (Join-Path $cdSource 'dist')
    if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: disposable install failed' }
    & powershell -NoProfile -File (Join-Path $cdSource 'tools/inspect-host-install.ps1') -Home $cdHome -Format json |
        Out-File -LiteralPath (Join-Path $cdEvidence 'install-inspection.json') -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: inspection failed' }
    [IO.File]::WriteAllText((Join-Path $cdFixture 'README.md'), "# CD fixture`n", $cdUtf8)
    [IO.File]::WriteAllText((Join-Path $cdFixture '.gitignore'), ".build-step/`n.review-deep/`n.claude/task-state/`n", $cdUtf8)
    # Existing checkpoint dependency, copied unmodified into the disposable repo.
    $cdWorkspace = Split-Path -Parent $cdSource
    foreach ($cdSupport in @('.claude/hooks/lib/task-state-derive.ps1', '.claude/references/task-state-schema.md')) {
        $cdSupportSource = Join-Path $cdWorkspace $cdSupport
        if (-not (Test-Path -LiteralPath $cdSupportSource -PathType Leaf)) { throw 'INCOMPLETE: workspace checkpoint dependency absent' }
        $cdSupportTarget = Join-Path $cdFixture $cdSupport
        New-Item -ItemType Directory -Path (Split-Path -Parent $cdSupportTarget) -Force | Out-Null
        Copy-Item -LiteralPath $cdSupportSource -Destination $cdSupportTarget
    }
    $cdPlan = @'
# Disposable code-review proof

### Step 1: Add a checked addition function
- **Type:** code
- **Status:** TODO
- **Flags:** --reviewers deep --isolation worktree --max-iter 3
- **Problem:** The fixture needs integer addition with an executable check.
- **Files:** sum.py; test_sum.py
- **Produces:** add(a, b) and a stdlib unittest exercising positive and negative values.
- **Done when:** python -m unittest discover passes and six independent code lenses complete.
'@
    [IO.File]::WriteAllText((Join-Path $cdFixture 'proof-plan.md'), $cdPlan, $cdUtf8)
    & git -C $cdFixture init -b main
    if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: git init' }
    & git -C $cdFixture config user.name CD-proof
    if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: fixture identity' }
    & git -C $cdFixture config user.email cd-proof@example.invalid
    if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: fixture identity' }
    & git -C $cdFixture add README.md .gitignore proof-plan.md .claude/hooks/lib/task-state-derive.ps1 .claude/references/task-state-schema.md
    if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: fixture stage' }
    & git -C $cdFixture -c user.name=CD-proof -c user.email=cd-proof@example.invalid commit -m 'Initialize disposable proof'
    if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: fixture commit' }
    & git init --bare -b main (Join-Path $cdRoot 'origin.git')
    if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: local origin' }
    & git -C $cdFixture remote add origin (Join-Path $cdRoot 'origin.git')
    if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: origin binding' }
    & git -C $cdFixture push -u origin main
    if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: initial local push' }
    & git -C $cdFixture remote set-head origin main
    if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: origin default branch' }
    $cdPrompt = @"
Work only in $cdFixture and its disposable sibling worktrees. Explicitly load installed build-phase, build-step, review-deep and task-handoff SKILL.md and cores from $cdHome/.agents/skills in full, not current global/source skills. Follow $cdSource/documentation/codex-deep-review-unblock-acceptance.md. Retain sanitized evidence at $cdEvidence. Verify loaded package paths/hashes and run the existing conversation and parent-only authority probes. Then /build-phase --plan proof-plan.md --steps 1. Keep build-step in this parent context. Use your actual host-assigned session identity for fixture-local checkpoints. The fixture has no issue; no GitHub writes are authorized, and its local bare origin is the only push destination. Bind plan_step to the resolved absolute proof-plan.md path with forward slashes plus :1. Use only installed helpers. Before worktree cleanup copy the actual canonical unsigned audit and retain its digest in parent memory. After all ship gates and cleanup, capture the actual service classify response and same-run audit digest as instructed. No pre-entered PASS or fabricated receipt qualifies. Emit INCOMPLETE on failure. Close all services in finally. Never publish private verifier material. Do not refresh the real consumer profile in this disposable session.
"@
    [IO.File]::WriteAllText((Join-Path $cdEvidence 'coordinator-prompt.txt'), $cdPrompt, $cdUtf8)
} catch {
    Invoke-Cd156Disposable $cdRoot { throw 'INCOMPLETE: setup failed' }
}
```

In the existing host, read the generated prompt and call
`collaboration.spawn_agent(task_name="cd156_proof", fork_turns="none", message=<exact prompt bytes>)`.
Record the actual tool entry point and host/version. The child is the new review
coordinator: it owns its own service and directly spawns its own fresh lens children.
Wait for completion through the collaboration tools. If capacity or caller-scoped
capability is unavailable, preserve the failure and return INCOMPLETE; do not launch
an ordinary CLI or use the outer parent's service as a substitute.

The outer coordinator must run the following cleanup whether setup, dispatch or the
child succeeds or fails, after terminating/waiting for any active child and its
services. Reload the lifecycle function block in the cleanup PowerShell call if its
shell process differs. Use the exact recorded `$cdRoot`/`$cdEvidence` from setup.

```powershell
Invoke-Cd156Disposable $cdRoot {
    if (-not (Test-Path -LiteralPath (Join-Path $cdEvidence 'parent-observation.json'))) {
        throw 'INCOMPLETE: actual parent observation absent'
    }
}
```

Only the nested `build-phase -> build-step -> review-deep` route and explicit installed
loading are qualified by this procedure. It does not qualify standalone build-step or
automatic discovery. The retained prompt contains disposable paths; publish sanitized
observations rather than this local setup file.

## Same-parent evidence capture

Before dispatch, compare installed owned-file hashes with the generated distribution
using the function below with the disposable home. Record sanitized observations:
host/version/entry point, conversation protocol v2 control and actual comparisons,
separate private-state/service/tamper/key-rotation results, each lens's direct-child
dispatch mode and batch, identical input digest, read-only byte comparison, and actual
commands/exit codes. Never retain the key, private verdict path, run id, signature or
service handle. Do not copy a private tool transcript wholesale.

Build-phase's Codex adapter loads build-step in the same parent context: it retains
the parsed plan and step. Pass the absolute normalized `plan_step` and extracted
step to review-deep. Execute the installed adapter's Python invocation recipe with
actual raw reports, prior-sidecar, lint and invocation metadata. Use the existing
`aggregate()` and `write_sidecar()` API; its CLI cannot bind the plan. Do not insert
metadata after producing the audit or silently skip plan-conformance.

Immediately after `write_sidecar`, before worktree cleanup, copy only its returned
file to the retained evidence directory as `audit.json`. Retain its SHA-256, exact
plan binding and originating review invocation in parent memory. Never select an
audit by glob/latest timestamp or accept a pre-created file. Complete the normal
ship/cleanup/stash gates, then use the existing parent's terminal write and classify.
Capture the actual parsed public classify response for that same code step; ADVANCE
must correspond to its PASS, not a deferred result. Service cleanup/close are mandatory.

Run the following in that parent, supplying `classification` directly from its
service response and `audit_digest`/`expected_plan_step` from that same invocation's
retained values. No `Read-Host`, entered PASS, child attestation or replayed observation
is allowed. This records a sanitized observation, not a new signed receipt framework.

```python
# CD156 evidence capture
import hashlib
import json
from pathlib import Path

def preserve_cd156_observation(classification, audit_digest, expected_plan_step, evidence_dir):
    evidence = Path(evidence_dir)
    audit_bytes = (evidence / "audit.json").read_bytes()
    if hashlib.sha256(audit_bytes).hexdigest() != audit_digest:
        raise ValueError("INCOMPLETE: same-run audit digest mismatch")
    if classification != {"ok": True, "op": "classify", "classification": "ADVANCE"}:
        raise ValueError("INCOMPLETE: parent did not authenticate advancement")
    audit = json.loads(audit_bytes)
    expected = ["correctness", "bugs", "security", "test-quality", "style", "plan-conformance"]
    if (audit.get("plan_step") != expected_plan_step or not expected_plan_step
            or audit.get("skill_version") != "v3"
            or audit.get("invocation", {}).get("reviewers_flag") != "code"
            or audit.get("aggregated_verdict", {}).get("result") != "PASS"
            or audit.get("deferred_uat_items") != []):
        raise ValueError("INCOMPLETE: audit does not prove this code step")
    lenses = audit.get("lens_verdicts", [])
    if [v.get("lens_id") for v in lenses] != expected:
        raise ValueError("INCOMPLETE: six ordered lenses required")
    for lens in lenses:
        if (lens.get("overall_verdict") != "PASS" or not isinstance(lens.get("findings"), list)
                or any(f.get("severity") != "FYI" for f in lens["findings"])):
            raise ValueError("INCOMPLETE: lens did not pass")
    observation = {"classification": classification, "audit_sha256": audit_digest}
    (evidence / "parent-observation.json").write_text(
        json.dumps(observation, indent=2) + "\n", encoding="utf-8")
```

The audit's schema contains a disposable absolute plan path. Retain it locally;
publish its digest and a sanitized description, not private paths. An arbitrary
file matching this observation schema is not proof: only the observed same-parent
sequence qualifies. Preserve failure evidence outside cleanup too. Capture, service
cleanup or disposable cleanup failure leaves Step 156 INCOMPLETE even after PASS.

## Normal intended-profile refresh

Use the operator's intended home as `$cdTargetHome`. Recheck it now: the earlier
125-file observation is not activation authority. Inspector `owned` is only header
evidence; verify ledger/current-byte hashes independently. Preserve foreign and
consumer-only files. Never use `-Force` or `-ForceShared` to overcome conflicts.

```powershell
# CD156 ownership check
function Test-Cd156OwnedHashes([string]$cdTargetHome, [string]$cdDistRoot, [switch]$cdCompareDist) {
    $cdLedger = Get-Content -LiteralPath (Join-Path $cdTargetHome '.skill-mesh-install.json') -Raw | ConvertFrom-Json
    $cdInstall = $cdLedger.installs.codex
    if ($null -eq $cdInstall -or @($cdInstall.owned_files).Count -eq 0) { throw 'INCOMPLETE: no Codex ownership' }
    $cdRootFull = [IO.Path]::GetFullPath($cdTargetHome).TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar
    foreach ($cdRelative in $cdInstall.owned_files) {
        if ($cdRelative -notmatch '^\.agents/skills/[^:]+$' -or $cdRelative -match '(^|/)\.\.(/|$)') { throw 'INCOMPLETE: ledger path' }
        $cdTarget = [IO.Path]::GetFullPath((Join-Path $cdTargetHome $cdRelative))
        if (-not $cdTarget.StartsWith($cdRootFull, [StringComparison]::OrdinalIgnoreCase)) { throw 'INCOMPLETE: ledger containment' }
        $cdHash = (Get-FileHash -LiteralPath $cdTarget -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($cdHash -ne $cdInstall.owned_file_hashes.$cdRelative) { throw 'INCOMPLETE: owned file edited' }
        if ($cdCompareDist) {
            $cdIncoming = Join-Path (Join-Path $cdDistRoot 'codex') $cdRelative.Substring('.agents/skills/'.Length)
            if ($cdHash -ne (Get-FileHash -LiteralPath $cdIncoming -Algorithm SHA256).Hash.ToLowerInvariant()) { throw 'INCOMPLETE: distribution differs' }
        }
    }
    if ($cdCompareDist) {
        $cdCount = @(Get-ChildItem -LiteralPath (Join-Path $cdDistRoot 'codex') -Recurse -File).Count
        if ($cdCount -ne @($cdInstall.owned_files).Count) { throw 'INCOMPLETE: owned set differs' }
    }
}
```

Retain the qualified distribution unchanged, record its per-file hashes during
disposable proof and compare them again before activation. Set `$cdTargetHome` from
the operator's intended home and keep `$cdSource` from setup, then execute:

```powershell
Test-Cd156OwnedHashes $cdTargetHome (Join-Path $cdSource 'dist')
& powershell -NoProfile -File (Join-Path $cdSource 'tools/inspect-host-install.ps1') -Home $cdTargetHome -Format json
if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: intended-home inspection' }
& powershell -NoProfile -File (Join-Path $cdSource 'tools/install-skill-mesh.ps1') -Provider codex -Home $cdTargetHome -DistDir (Join-Path $cdSource 'dist')
if ($LASTEXITCODE -ne 0) { throw 'INCOMPLETE: activation conflict' }
Test-Cd156OwnedHashes $cdTargetHome (Join-Path $cdSource 'dist') -cdCompareDist
```

Record source commit, distribution hashes, actual entry points, probe/batch evidence,
audit digest, actual public classification, installer/inspection exit codes, final
owned-hash check and cleanup result in `plan.md` by durable evidence locator. Only
then may Step 156 complete. No provider-wide, ordinary CLI, runtime/full or different
host claim follows. The separately qualified Claude route remains independent.

Fresh-session consumer resume prompt:

> Load the qualified installed build-phase, build-step and review-deep packages and
> compare their hashes with Phase CD evidence. Run this session's existing capability
> probes. Resume the preserved consumer candidate with its actual plan/deep flags and
> consumed retry history. Keep prior review evidence and unresolved findings. Stop
> `required_tool_missing` on any absent or inconclusive capability; no host/model
> switch, self-review or retry reset is authorized.
