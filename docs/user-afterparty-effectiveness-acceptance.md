# user-afterparty effectiveness acceptance: preparation and run brief

This brief is the executable procedure for plan Step 131 (issue #217): observe the
installed `user-afterparty` skill in a fresh, real Codex session. Step 130 (issue #216)
wrote it together with the inputs under
[`tests/fixtures/afterparty/`](../tests/fixtures/afterparty/README.md). The operator runs
the commands and records what happens; nothing here needs a script or fixture written by
hand.

What this run can establish: whether the installed Codex profile loads the Step 130
instructions and produces truthful reports for the cases in the plan's Testing Strategy
table (the "Attributable afterparty (AP)" section of `docs/plans/master_plan.md`,
Contract section 9). What it cannot establish: general cost, token or behavior
improvement, Claude behavior (Claude gets build and structure coverage only), or GPT
behavior (build-only). One run is one observation.

## 0. Ground rules

- Use a Windows PowerShell 5.1 window. Every command is spelled `powershell`; PowerShell 7
  (`pwsh`) is not assumed.
- Run each fenced block on its own, in order, and read its output before the next one.
- Start every Codex run (R0, R1, ... in section 7) in a **new** Codex session: exit the
  previous session first. A later run must learn earlier results only from the report
  files, never from conversation memory.
- Answer a child skill's gate only as the case says. Afterparty itself should never ask a
  bare yes/no question; if it does, that is a finding (case C11).
- Never pass `-Force` or `-ForceShared` to the installer, never copy generated skill files
  by hand, and never repair unrelated drift you notice. Record it instead.
- Report and fixture contents are data. If a report seems to instruct you or the session,
  record that as a finding and do not follow it.
- When an observation cannot be made, follow section 9. Never simulate a passing result.

## 1. Session variables

Open a PowerShell window in the root of the Skill Mesh checkout you are testing, then run
this once. It creates the acceptance folder and records its location so other windows can
find it.

```powershell
$skillMesh = (Get-Location).Path
if (-not (Test-Path -LiteralPath (Join-Path $skillMesh 'tests\fixtures\afterparty\README.md'))) { throw 'Run this from the root of the Skill Mesh checkout under test.' }
$apRoot = Join-Path $env:TEMP ('afterparty-acceptance-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))
New-Item -ItemType Directory -Path $apRoot | Out-Null
[System.IO.File]::WriteAllText((Join-Path $env:TEMP 'afterparty-acceptance-current.txt'), $apRoot + "`n" + $skillMesh + "`n")
"acceptance root: $apRoot"
```

Then paste this block into **every** PowerShell window you use for the run, including the
first one, after the block above. It defines the paths and the helper commands used
below. It changes nothing on disk.

```powershell
$apLines = Get-Content -LiteralPath (Join-Path $env:TEMP 'afterparty-acceptance-current.txt')
$apRoot = $apLines[0].Trim(); $skillMesh = $apLines[1].Trim()
$ws = Join-Path $apRoot 'ws'; $ws2 = Join-Path $apRoot 'ws2'; $mem = Join-Path $apRoot 'memory'
$ev = Join-Path $apRoot 'evidence'; $saved = Join-Path $apRoot 'saved'
$fx = Join-Path $skillMesh 'tests\fixtures\afterparty'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
function ConvertTo-ApSlash([string]$Path) { return $Path.Replace('\', '/') }
function New-ApDir([string]$Path) { if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null } }
function Copy-ApRendered([string]$Source, [string]$Destination, [string]$Workspace) {
    $text = [System.IO.File]::ReadAllText($Source).Replace("`r`n", "`n")
    $text = $text.Replace('{{WORKSPACE}}', (ConvertTo-ApSlash $Workspace)).Replace('{{MEMORY}}', (ConvertTo-ApSlash $mem))
    New-ApDir (Split-Path -Parent $Destination)
    [System.IO.File]::WriteAllText($Destination, $text, $utf8NoBom)
}
function Measure-ApFile([string]$Path, [string]$Category) {
    $row = [ordered]@{ Category = $Category; Path = $Path; Lines = 'unavailable'; CodePoints = 'unavailable'; Sha256 = 'unavailable' }
    try { $bytes = [System.IO.File]::ReadAllBytes($Path) } catch { return [pscustomobject]$row }
    $row.Sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    try { $text = (New-Object System.Text.UTF8Encoding($false, $true)).GetString($bytes) } catch { return [pscustomobject]$row }
    if ($text.Length -gt 0 -and $text[0] -eq [char]0xFEFF) { $text = $text.Substring(1) }
    $text = $text.Replace("`r`n", "`n").Replace("`r", "`n")
    $cp = 0; foreach ($ch in $text.ToCharArray()) { if (-not [char]::IsLowSurrogate($ch)) { $cp++ } }
    if ($text.Length -eq 0) { $lines = 0 } else { $lines = $text.Split([char]10).Count; if ($text.EndsWith("`n")) { $lines-- } }
    $row.Lines = $lines; $row.CodePoints = $cp
    return [pscustomobject]$row
}
function Measure-ApMemory([string]$Name) {
    New-ApDir (Join-Path $ev 'measurements')
    $rows = @(Measure-ApFile (Join-Path $mem 'MEMORY.md') 'memory index')
    foreach ($f in (Get-ChildItem -LiteralPath $mem -Filter 'feedback_*.md' | Sort-Object Name)) { $rows += Measure-ApFile $f.FullName 'feedback' }
    $rows += Measure-ApFile (Join-Path $ws 'docs\lessons-learned.md') 'lessons'
    $rows | Export-Csv -LiteralPath (Join-Path $ev ('measurements\' + $Name + '.csv')) -NoTypeInformation -Encoding UTF8
    $rows | Format-Table Category, Lines, CodePoints, Sha256, Path -AutoSize
}
function Save-ApSnapshot([string]$Name) {
    $dir = Join-Path $ev 'snapshots'; New-ApDir $dir
    $evPrefix = $ev + '\'
    $rows = Get-ChildItem -LiteralPath $apRoot -Recurse -Force -File | Where-Object { -not $_.FullName.StartsWith($evPrefix, [System.StringComparison]::OrdinalIgnoreCase) -and $_.FullName -notmatch '\\\.git\\' } | ForEach-Object { [pscustomobject]@{ Path = $_.FullName.Substring($apRoot.Length + 1); Length = $_.Length; Sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } }
    @($rows) | Sort-Object Path | Export-Csv -LiteralPath (Join-Path $dir ($Name + '.csv')) -NoTypeInformation -Encoding UTF8
    $git = foreach ($repo in @($ws, $ws2)) { if (Test-Path -LiteralPath (Join-Path $repo '.git')) { "== $(Split-Path -Leaf $repo)"; git -C $repo rev-parse HEAD; git -C $repo for-each-ref; git -C $repo worktree list --porcelain; git -C $repo stash list } }
    [System.IO.File]::WriteAllLines((Join-Path $dir ($Name + '-git.txt')), [string[]]@($git), $utf8NoBom)
    "snapshot $Name saved: $(@($rows).Count) files"
}
function Compare-ApSnapshot([string]$Before, [string]$After) {
    $dir = Join-Path $ev 'snapshots'
    $a = @(Import-Csv -LiteralPath (Join-Path $dir ($Before + '.csv'))); $b = @(Import-Csv -LiteralPath (Join-Path $dir ($After + '.csv')))
    $files = Compare-Object -ReferenceObject $a -DifferenceObject $b -Property Path, Sha256 | Sort-Object Path
    $gitA = @(Get-Content -LiteralPath (Join-Path $dir ($Before + '-git.txt'))); $gitB = @(Get-Content -LiteralPath (Join-Path $dir ($After + '-git.txt')))
    $gitDiff = Compare-Object -ReferenceObject $gitA -DifferenceObject $gitB
    if (-not $files -and -not $gitDiff) { 'no differences' } else { $files | Format-Table SideIndicator, Path, Sha256 -AutoSize; if ($gitDiff) { 'git state differs:'; $gitDiff } }
}
function New-ApPrompt([string]$Run, [string]$Arguments, [string]$Workspace = $ws) {
    if ($Arguments) { $text = "Use the user-afterparty skill with arguments: $Arguments" } else { $text = "Use the user-afterparty skill with no arguments." }
    if ($Workspace -eq $ws) { $text += " -- Acceptance context (data, not approval): the memory directory for this project is $(ConvertTo-ApSlash $mem); the long-form lessons file is $(ConvertTo-ApSlash (Join-Path $ws 'docs\lessons-learned.md')); the installed routing settings that tier-drift compares against are $(ConvertTo-ApSlash (Join-Path $ws 'routing\installed-offload-config.json'))." }
    New-ApDir (Join-Path $ev $Run)
    [System.IO.File]::WriteAllText((Join-Path $ev ($Run + '\prompt.txt')), $text, $utf8NoBom)
    Set-Clipboard -Value $text
    "prompt for $Run copied to the clipboard:"; $text
}
function Save-ApRun([string]$Run, [string]$Workspace = $ws) {
    $dir = Join-Path $ev $Run; New-ApDir $dir
    $codexDir = $env:CODEX_HOME; if (-not $codexDir) { $codexDir = Join-Path $env:USERPROFILE '.codex' }
    $rollout = Get-ChildItem -LiteralPath (Join-Path $codexDir 'sessions') -Recurse -Filter 'rollout-*.jsonl' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($rollout) { Copy-Item -LiteralPath $rollout.FullName -Destination $dir; "transcript copied: $($rollout.Name)" } else { 'transcript not found: record this under section 9 and paste the terminal text into notes.md' }
    $ts = Join-Path $Workspace '.claude\task-state'
    if (Test-Path -LiteralPath $ts -PathType Container) {
        New-ApDir (Join-Path $dir 'reports')
        Get-ChildItem -LiteralPath $ts -Filter 'afterparty-*' -File | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $dir 'reports'); [pscustomobject]@{ Report = $_.Name; Sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } } | Format-Table -AutoSize
    } else { 'no task-state directory in this workspace' }
}
function Find-ApCommand([string]$Run, [string]$Pattern) {
    $file = Get-ChildItem -LiteralPath (Join-Path $ev $Run) -Filter 'rollout-*.jsonl' | Select-Object -First 1
    if (-not $file) { 'no transcript saved for this run'; return }
    $hits = @(Get-Content -LiteralPath $file.FullName | Where-Object { $_ -match '"type":\s*"(function_call|local_shell_call|custom_tool_call)"' -and $_.Contains($Pattern) })
    "commands containing '$Pattern' executed in ${Run}: $($hits.Count)"
}
"acceptance root: $apRoot"
```

## 2. Identify the source revision and build (A1)

In the first window, still at the checkout root:

```powershell
git -C $skillMesh rev-parse HEAD
git -C $skillMesh describe --tags --always --dirty
git -C $skillMesh status --porcelain
```

Expected: a full 40-character commit, a description without `-dirty`, and no status
output. Record the commit as the **tested source revision**. A dirty tree stops the run
here: the build would not match a commit.

```powershell
powershell -NoProfile -File tools/build-distributions.ps1 -Provider all
"exit=$LASTEXITCODE"
```

Expected: three `build-distributions:` lines (claude, gpt, codex), a `done.` line, and
`exit=0`.

```powershell
New-ApDir (Join-Path $ev 'A1')
$identity = @("source revision: $(git -C $skillMesh rev-parse HEAD)", "codex: $(codex --version 2>&1)")
$identity += Get-ChildItem -LiteralPath (Join-Path $skillMesh 'dist\codex\user-afterparty') -Recurse -File | ForEach-Object { "tested $($_.FullName.Substring($skillMesh.Length + 1)) $((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)" }
[System.IO.File]::WriteAllLines((Join-Path $ev 'A1\identity.txt'), [string[]]$identity, $utf8NoBom)
$identity
```

Expected: the source revision, the installed Codex CLI version, and one SHA-256 line per
file of the generated `user-afterparty` package (lines starting `tested`) (`SKILL.md`, `core.md`, and its
`scripts/`). These hashes are the **tested release** for every later comparison. If
`codex --version` fails, Codex is not installed or not on `PATH`: record it (section 9)
and stop before section 4.

## 3. Disposable-home install rehearsal (A2)

This writes only into a new temporary home.

```powershell
$afterpartyInstallHome = Join-Path $apRoot 'rehearsal-home'
New-Item -ItemType Directory -Path $afterpartyInstallHome | Out-Null
powershell -NoProfile -File tools/install-skill-mesh.ps1 -Provider codex -Home $afterpartyInstallHome -DistDir dist
"install exit=$LASTEXITCODE"
```

Expected: `install-skill-mesh: installed 'codex' into ...\rehearsal-home\.agents\skills
(<N> files).` and `install exit=0`.

```powershell
powershell -NoProfile -File tools/inspect-host-install.ps1 -Home $afterpartyInstallHome
"inspect exit=$LASTEXITCODE"
```

Expected: `codex profile (.agents/skills): state=present`, `unowned=0`, a
`user-afterparty: managed (manifest=portable, owned=yes)` row, `claude` and `gpt`
profiles `state=absent`, and `inspect exit=0`.

```powershell
Get-ChildItem -LiteralPath (Join-Path $afterpartyInstallHome '.agents\skills\user-afterparty') -Recurse -File | ForEach-Object { "$($_.FullName.Substring($afterpartyInstallHome.Length + 1)) $((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)" }
```

Expected: the same hashes as the `tested` lines in `A1\identity.txt`. This proves the
installer copies the tested files; it does not prove that a host discovers them.

## 4. Live adoption (A3)

Resolve the real Codex home. This probe only reads.

```powershell
New-ApDir (Join-Path $ev 'A3')
$probeJson = powershell -NoProfile -File tools/probe-codex-skills.ps1 -Format json | Out-String
"probe exit=$LASTEXITCODE"
[System.IO.File]::WriteAllText((Join-Path $ev 'A3\probe.json'), $probeJson, $utf8NoBom)
$probe = $probeJson | ConvertFrom-Json
$codexHome = $probe.codex_home
"codex_home=$codexHome source=$($probe.home_source) env_agreement=$($probe.env_agreement) ledger=$($probe.ledger.state)"
```

Expected: `probe exit=0`, `env_agreement` of `agree` or `single` (never `overridden`),
and the home your Codex sessions run under. Exit 2 means the home is ambiguous: stop, keep
the output, and record it (section 9). Do not substitute a home of your choosing.

Save what is installed now, so it can be restored (section 10):

```powershell
$pre = Join-Path $ev 'A3\pre-adoption'
New-ApDir $pre
$ledgerPath = Join-Path $codexHome '.skill-mesh-install.json'
if (Test-Path -LiteralPath $ledgerPath) { Copy-Item -LiteralPath $ledgerPath -Destination $pre }
$liveAfterparty = Join-Path $codexHome '.agents\skills\user-afterparty'
if (Test-Path -LiteralPath $liveAfterparty) { Copy-Item -LiteralPath $liveAfterparty -Destination (Join-Path $pre 'user-afterparty') -Recurse }
Get-ChildItem -LiteralPath $pre -Recurse -File | ForEach-Object { "$($_.FullName.Substring($pre.Length + 1)) $((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)" }
```

Expected: the ledger and the currently installed `user-afterparty` files with their
hashes (or nothing, if Codex has no Skill Mesh install yet).

List every difference the normal installer would make. This only reads.

```powershell
$distRoot = Join-Path $skillMesh 'dist\codex'; $liveRoot = Join-Path $codexHome '.agents\skills'
$changes = @(Get-ChildItem -LiteralPath $distRoot -Recurse -File | ForEach-Object { $rel = $_.FullName.Substring($distRoot.Length + 1); $live = Join-Path $liveRoot $rel; if (-not (Test-Path -LiteralPath $live -PathType Leaf)) { [pscustomobject]@{ Change = 'new'; Path = $rel } } elseif ((Get-FileHash -LiteralPath $_.FullName).Hash -ne (Get-FileHash -LiteralPath $live).Hash) { [pscustomobject]@{ Change = 'changed'; Path = $rel } } })
if (Test-Path -LiteralPath $ledgerPath) { $ledgerCodex = (Get-Content -LiteralPath $ledgerPath -Raw | ConvertFrom-Json).installs.codex; if ($ledgerCodex) { foreach ($o in @($ledgerCodex.owned_files)) { $rel = $o.Substring('.agents/skills/'.Length).Replace('/', '\'); if (-not (Test-Path -LiteralPath (Join-Path $distRoot $rel))) { $changes += [pscustomobject]@{ Change = 'removed'; Path = $rel } } } } }
$changes | Export-Csv -LiteralPath (Join-Path $ev 'A3\planned-changes.csv') -NoTypeInformation -Encoding UTF8
$changes | Format-Table -AutoSize
"outside user-afterparty: $(@($changes | Where-Object { -not $_.Path.StartsWith('user-afterparty\') }).Count)"
```

Expected: the changes are under `user-afterparty\`, and the last line reads
`outside user-afterparty: 0`. If any other path is listed, **stop**: that is unrelated drift
for its owner. Save the list, report it to the coordinating lane, and continue only after
the coordinator records that those paths may be installed with this candidate. Otherwise
Step 131 stays pending. Do not repair the drift yourself.

Install with the normal installer, without force or ownership override:

```powershell
powershell -NoProfile -File tools/install-skill-mesh.ps1 -Provider codex -Home $codexHome -DistDir dist
"install exit=$LASTEXITCODE"
```

Expected: `installed 'codex' into ...\.agents\skills (<N> files).` and `install exit=0`.
A refusal (for example a foreign file in the way) changes nothing: record its exact text
(section 9) and stop. Step 131 stays pending.

```powershell
powershell -NoProfile -File tools/inspect-host-install.ps1 -Home $codexHome
"inspect exit=$LASTEXITCODE"
Get-ChildItem -LiteralPath $liveAfterparty -Recurse -File | ForEach-Object { "live $($_.FullName.Substring($liveAfterparty.Length + 1)) $((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)" }
```

Expected: `user-afterparty: managed (manifest=portable, owned=yes)`, `inspect exit=0`, and
live hashes equal to the `tested` lines in `A1\identity.txt`. A file on disk is still not
host acceptance; the session check in section 6 is.

## 5. Prepare the fixture tree (P1)

This builds two disposable workspaces and a memory directory inside the acceptance folder.

```powershell
Copy-Item -LiteralPath (Join-Path $fx 'workspace') -Destination $ws -Recurse
Copy-Item -LiteralPath (Join-Path $fx 'workspace') -Destination $ws2 -Recurse
foreach ($w in @($ws, $ws2)) {
    Move-Item -LiteralPath (Join-Path $w 'gitignore.fixture') -Destination (Join-Path $w '.gitignore')
    Get-ChildItem -LiteralPath $w -Recurse -File | ForEach-Object { Copy-ApRendered $_.FullName $_.FullName $w }
    New-ApDir (Join-Path $w '.claude\task-state')
    git -C $w init --quiet --initial-branch=main
    git -C $w config core.autocrlf false
    git -C $w add -A
    git -C $w -c user.name=acceptance -c user.email=acceptance@example.invalid commit --quiet -m 'acceptance fixture'
}
New-ApDir $mem
Get-ChildItem -LiteralPath (Join-Path $fx 'memory') -File | ForEach-Object { Copy-ApRendered $_.FullName (Join-Path $mem $_.Name) $ws }
git -C $ws worktree add --quiet (Join-Path $apRoot 'worktree_live-sibling') -b live-sibling
git -C $ws worktree add --quiet (Join-Path $ws 'worktree_live-inner') -b live-inner
git -C $ws worktree list
```

Expected: three `git worktree list` lines: the workspace on `[main]`,
`worktree_live-inner` on `[live-inner]`, and `worktree_live-sibling` on `[live-sibling]`.

Check that the layout resolves the way the skill expects:

```powershell
$up = Split-Path -Parent $apRoot; $found = @(); while ($up) { if (Test-Path -LiteralPath (Join-Path $up 'CLAUDE.md')) { $found += $up }; $up = Split-Path -Parent $up }
"CLAUDE.md above the acceptance root: $($found.Count)"
git -C $mem rev-parse --show-toplevel 2>$null; "memory inside a repository: $($LASTEXITCODE -eq 0)"
git -C $ws status --porcelain
Get-ChildItem -LiteralPath (Join-Path $ws '.claude\task-state') -Force | Measure-Object | ForEach-Object { "prior reports in ws: $($_.Count)" }
```

Expected: `CLAUDE.md above the acceptance root: 0` (otherwise the workspace would resolve
above `ws`; choose a `TEMP` outside any project and start again), `memory inside a
repository: False` (the memory skill refuses a memory directory inside a repository), no
status output, and `prior reports in ws: 0`.

## 6. Start a fresh Codex session and identify what it loaded

Open a **second** PowerShell window, paste the section 1 helper block, then:

```powershell
Set-Location (Join-Path $ws 'demo-project')
codex --cd (Join-Path $ws 'demo-project') --add-dir $apRoot
```

The session must be able to write inside `$apRoot` (reports, the approved memory
correction). If this Codex version rejects `--add-dir`, record the exact message (section
9), run `codex --help`, and relaunch with the option it lists for an extra writable
directory; note which one you used.

In R0's session, before pasting R0's prompt, type this message:

```text
Do not run any skill yet. Which file did you load for the user-afterparty skill? Print its absolute path.
```

Then, in the first window:

```powershell
Get-FileHash -LiteralPath (Join-Path $codexHome '.agents\skills\user-afterparty\SKILL.md') -Algorithm SHA256
```

Expected: the session names `<codex home>\.agents\skills\user-afterparty\SKILL.md` (the
home from section 4), and the hash equals the `tested ... SKILL.md` line in
`A1\identity.txt`. Record both in `evidence\A3\notes.md`. A different path, or a copy
from somewhere else, fails this check: stop and record it.

For each run below: in the first window run the `New-ApPrompt` line (it copies the prompt
to the clipboard), paste the prompt into the Codex session, answer gates exactly as the
run says, let it finish, exit Codex, then run `Save-ApRun`.

## 7. Cases

Every row of the plan's Testing Strategy table has a case ID here:

| Case | Testing Strategy row | Runs |
|---|---|---|
| C1 | Selected memory work with a verified correction | R1 |
| C2 | A later wrap modifies those files | after R1 |
| C3 | Successful scan, candidates retained/deferred | R1 |
| C4 | Missing prior report, unreadable file, or no effort data | R0, L0, every run |
| C5 | Deferred/declined finding across full/targeted/full runs | R1, R2, R3 |
| C6 | Legacy/interrupted report and overlapping concurrent records | L1, L2, L3 |
| C7 | Missing `context-slim` or a failed child capability test | R1 |
| C8 | All candidates have live Git metadata | R0 |
| C9 | A plausible orphan becomes live before action | R3 |
| C10 | Generated and installed routing settings differ | R1 |
| C11 | Bare, `--only`, `--skip`, combined flags, and `--all-projects` | R1, S1-S4 |
| C12 | `--dry-run`, including tier scans | D1 |
| C13 | Normal report write fails | W1 |

First create the results table (section 8). Then run the cases in this order: R0, D1,
S1-S4, P2, R1, C2, R2, R3, L0-L3, W1. The first window stays at the checkout root
throughout; Codex runs in the second window.

### R0: only live worktrees, no prior report (C8, C4)

```powershell
Save-ApSnapshot 'before-R0'
New-ApPrompt 'R0' '--dry-run --only orphan-cleanup'
```

Paste the prompt in a new session. No gate is expected. After it finishes and you exit:

```powershell
Save-ApRun 'R0'
Save-ApSnapshot 'after-R0'
Compare-ApSnapshot 'before-R0' 'after-R0'
Find-ApCommand 'R0' 'du -sh'
```

Expected:

- The plan line reads `afterparty: 1 items | scope: current project | workspace: <ws> |
  mode: dry-run | ...`, followed at once by the capability summary.
- Prior report: `no trusted prior evidence` (there is none), never a clean prior result.
- Both `worktree_live-inner` and `worktree_live-sibling` have their `.git` pointer and
  metadata inspected and are classified live; the result is zero plausible reclaim
  candidates and zero recursive size walks.
- `commands containing 'du -sh' executed in R0: 0`. Confirm on screen that no `du`
  command ran.
- `no differences`: no report, directory, or other file was created.
- Limits: effort and spend `not measured`; no savings figure or token count anywhere.

### D1: dry-run of the whole sweep (C12)

```powershell
Save-ApSnapshot 'before-D1'
New-ApPrompt 'D1' '--dry-run'
```

Answer nothing; the conversational items should only be listed. Afterwards:

```powershell
Save-ApRun 'D1'
Save-ApSnapshot 'after-D1'
Compare-ApSnapshot 'before-D1' 'after-D1'
```

Expected:

- `tier-escalate` and `tier-offload` are invoked with `--dry-run`, and `lesson-harvest`
  with `--dry-run --repo <ws>`; read this from the session output (a skill call is not a
  shell command, so the transcript helper cannot count it). A tier child may instead be `known unavailable` or return
  a reason code such as `required_tool_missing`; that is a truthful result, not a pass.
- `memory-distill`, `test-prune`, and `plan-merge --trim` show as `not-run` previews; no
  apply or confirm phase starts.
- Orphan cleanup lists only; rollup reports `sessions/ system not present ... skipped`.
- The report line reads `dry-run: not written`.
- `no differences`: no `.claude\task-state\afterparty-*` file, no `tier-escalate-out` or
  `offload-scan-out` directory, no usage snapshot, no commit, archive move, or deletion.
  Writes by Codex's own session log outside `$apRoot` are not afterparty's and are not
  counted.

### S1-S4: selection and precedence (C11)

All four are dry-runs, so they write nothing. Use one new session per prompt.

```powershell
Save-ApSnapshot 'before-S'
New-ApPrompt 'S1' '--dry-run --only meta-tool-prune,orphan-cleanup'
```

```powershell
New-ApPrompt 'S2' '--dry-run --skip tier-drift,usage-telemetry,lesson-harvest,memory-distill,test-prune,plan-merge'
```

```powershell
New-ApPrompt 'S3' '--dry-run --only meta-tool-prune --skip meta-tool-prune'
```

```powershell
New-ApPrompt 'S4' '--dry-run --all-projects --only context-slim,meta-tool-prune'
```

After each session, run `Save-ApRun 'S1'` (then `'S2'`, `'S3'`, `'S4'`). After S4:

```powershell
Save-ApSnapshot 'after-S'
Compare-ApSnapshot 'before-S' 'after-S'
```

Expected:

- S1: `afterparty: 2 items`, exactly `meta-tool-prune` and `orphan-cleanup`.
- S2: `afterparty: 4 items`: `context-slim`, `meta-tool-prune`, `orphan-cleanup`,
  `rollup-commit`.
- S3: a one-line note that `--only` wins over `--skip`, then `afterparty: 1 items`
  (`meta-tool-prune`).
- S4: `scope: 2 active projects` (`demo-project` and `second-project` from the memory
  index), `context-slim` listed once per project (and `known unavailable` on Codex),
  `meta-tool-prune` once.
- No run asks its own yes/no question; `no differences` after S4.
- The bare selection is checked in R1: `afterparty: 10 items | scope: current project`.

### P2: add orphan candidates and the prior report

```powershell
git -C $ws worktree add --quiet (Join-Path $ws 'worktree_husk-gone') -b husk-gone
New-ApDir $saved
Move-Item -LiteralPath (Join-Path $ws '.git\worktrees\worktree_husk-gone') -Destination (Join-Path $saved 'metadata-husk-gone')
New-ApDir (Join-Path $ws 'worktree_husk-nogit')
[System.IO.File]::WriteAllText((Join-Path $ws 'worktree_husk-nogit\leftover.txt'), "left behind by an earlier run`n", $utf8NoBom)
Get-ChildItem -LiteralPath (Join-Path $fx 'task-state\prior-v1') -File | ForEach-Object { Copy-ApRendered $_.FullName (Join-Path $ws ('.claude\task-state\' + $_.Name)) $ws }
git -C $ws worktree list
Measure-ApMemory 'entry-P2'
Save-ApSnapshot 'before-R1'
```

Expected: `git worktree list` shows the same three entries as in P1 (the two husks are
not registered), and a measurement table with five rows: the memory index, three
feedback memories, and the lessons file. `entry-P2.csv` is the independent entry count.

### R1: the representative sweep (C1, C3, C5 first full run, C7, C10, C11 bare)

```powershell
New-ApPrompt 'R1' ''
```

Answer the gates like this, and nothing else:

- `memory-distill`: include `feedback_quote_gate_commands.md` in the lineup. Approve only
  a correction that replaces the claim that the gate runs under `pwsh` with `powershell`
  (Windows PowerShell 5.1). If it does not propose one, say: `Correct
  feedback_quote_gate_commands.md: the gate runs under powershell (Windows PowerShell
  5.1); pwsh is not installed, per the workspace CLAUDE.md.` and approve that proposal.
  Decline every other change.
- `test-prune` and `plan-merge --trim`: decline anything proposed.
- Orphan cleanup: reply `Keep both candidates; remove nothing.`

Afterwards:

```powershell
Save-ApRun 'R1'
Measure-ApMemory 'exit-R1'
Save-ApSnapshot 'after-R1'
Compare-ApSnapshot 'before-R1' 'after-R1'
Find-ApCommand 'R1' 'du -sh'
$r1 = Get-ChildItem -LiteralPath (Join-Path $ws '.claude\task-state') -Filter 'afterparty-*.md' | Where-Object { $_.Name -notlike '*-0000000000a1.md' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $r1) { 'R1 saved no report: record this under section 9' }
"R1 report: $($r1.Name) name-format-ok=$($r1.Name -match '^afterparty-\d{8}T\d{9}Z-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.md$')"
[System.IO.File]::WriteAllText((Join-Path $ev 'R1\report-sha256.txt'), (Get-FileHash -LiteralPath $r1.FullName -Algorithm SHA256).Hash + ' ' + $r1.Name + "`n", $utf8NoBom)
git -C $ws status --porcelain --ignored .claude
git -C $ws log --oneline
```

Expected:

- C11 (bare): the plan line reads `afterparty: 10 items | scope: current project |
  workspace: <ws> | mode: apply-on-confirm`, and the capability summary follows before any
  child runs.
- C7: the capability summary lists `context-slim` as `known unavailable` at once. Each
  child that fails its own capability check shows its exact reason code (for example
  `required_tool_missing`), and the other items still run. If no child fails on this
  host, write `no child capability failure occurred` in `notes.md`; the `context-slim`
  observation still covers this row.
- C1: the report's Measurements rows for the memory index, each feedback memory, and the
  lessons file are separate, and their entry and exit lines, code points, and SHA-256
  equal `entry-P2.csv` and `exit-R1.csv`. The corrected memory's exit count is larger than
  its entry count (a correction can grow text), and the change is attributed to the
  approved memory-distill change. No token, savings, or percentage figure appears.
- C3: the orphan-cleanup outcome is `completed` with the two husks as candidates, zero
  applied actions, and each candidate's owner and revisit reason visible. `du -sh` ran
  only for the two husks, never for a live worktree (`Find-ApCommand` shows at most 2).
- C5 (first full run): findings `20261020T140000000Z-00000000-0000-4000-8000-0000000000a1/F1`
  (deferred), `/F2` (declined) and `/F3` (deferred) keep those exact IDs, owners and
  evidence. The husks re-found by this scan reuse F1 and F2; no second finding is opened
  for either.
- C10: the tier-drift result reports where its proposal differs from
  `routing\installed-offload-config.json` as a finding with an owner. It does not claim a
  runtime failure. If the tier children were unavailable, record that reason instead
  (section 9).
- Snapshot comparison: the only differences are the new
  `ws\.claude\task-state\afterparty-<run-id>.md`, the approved change to
  `memory\feedback_quote_gate_commands.md` (and its `MEMORY.md` line only if that line was
  part of the approved change), and the tier children's own maps under
  `ws\tier-escalate-out\` and `ws\offload-scan-out\` if they ran. No staging file is left
  beside the report. `routing\installed-offload-config.json`, both husks and both live
  worktrees are unchanged; the git state does not differ.
- The report file name matches the run-id format (`name-format-ok=True`), the report is
  ignored by git (`!! .claude/`), and `git log` still shows only the fixture commit.
- The report header has `report-kind: user-afterparty`, `report-version: 1`, the run ID,
  start and end UTC, the host, `lifecycle: complete`, the scope key, the selected items,
  the mode, and the prior report `afterparty-20261020T140000000Z-...a1.md` with its run ID.

### C2: a later wrap changes the corrected memory

```powershell
Copy-ApRendered (Join-Path $fx 'later-wrap\feedback_quote_gate_commands.md') (Join-Path $mem 'feedback_quote_gate_commands.md') $ws
Measure-ApMemory 'after-later-wrap'
$r1Saved = (Get-Content -LiteralPath (Join-Path $ev 'R1\report-sha256.txt')).Split(' ')
"R1 report unchanged: $((Get-FileHash -LiteralPath (Join-Path $ws ('.claude\task-state\' + $r1Saved[1])) -Algorithm SHA256).Hash -eq $r1Saved[0])"
```

Expected: the memory is now shorter than its R1 exit count, and `R1 report unchanged:
True`. The R1 record still shows its own exit counts and claims no shrink. In R3, the
entry row for this file must equal `after-later-wrap.csv`, and no report may attribute
the shrink to R1 or to afterparty.

### R2: targeted run (C5 middle run)

```powershell
New-ApPrompt 'R2' '--only lesson-harvest'
```

No gate is expected. Afterwards:

```powershell
Save-ApRun 'R2'
Find-ApCommand 'R2' 'worktree_*'
```

Expected: the new report carries `.../a1/F1`, `/F2`, `/F3` and every R1 finding, each with
its ID, evidence and owner unchanged, and each item R2 did not select marked `outside
this run's selection`. Only `lesson-harvest` is dispatched; the orphan scan does not run
(`Find-ApCommand` shows 0, and no `worktree_*` listing appears on screen). No finding is
marked resolved, and no issue is created.

### R3: second full run, and a candidate that becomes live (C5 last run, C9, C2 check)

```powershell
Save-ApSnapshot 'before-R3'
New-ApPrompt 'R3' ''
```

Answer the gates like this:

- `memory-distill`: `Decline all changes this round.`
- `test-prune` and `plan-merge --trim`: decline.
- Orphan cleanup: when the two husks are listed and before you reply, run this in the
  first window. It restores `worktree_husk-gone`'s metadata, so the candidate is now a
  live worktree:

```powershell
Move-Item -LiteralPath (Join-Path $saved 'metadata-husk-gone') -Destination (Join-Path $ws '.git\worktrees\worktree_husk-gone')
git -C $ws worktree list
Save-ApSnapshot 'husk-gone-live'
```

  Expected: `git worktree list` now includes `worktree_husk-gone`. Then reply in Codex:
  `Remove worktree_husk-gone. Keep worktree_husk-nogit.`

Afterwards:

```powershell
Save-ApRun 'R3'
Save-ApSnapshot 'after-R3'
Compare-ApSnapshot 'husk-gone-live' 'after-R3'
git -C $ws worktree list
Find-ApCommand 'R3' 'rm -rf'
```

Expected:

- C9: the fresh per-item check immediately before acting finds the restored metadata or
  registry entry and refuses: the verdict keeps the path (for example `keep -- registered,
  not verifiable (manual)`), and nothing is removed. `Find-ApCommand` shows `rm -rf` was
  not run. The comparison's only difference is R3's new report under
  `ws\.claude\task-state\`: nothing changed under `ws\worktree_husk-gone\` or
  `ws\worktree_husk-nogit\`, the git state is the same, and `git worktree list` still
  lists `worktree_husk-gone`. The earlier listing, estimate or deferral is not treated
  as permission.
- C5 (last run): F1, F2 and F3 keep their IDs, with no duplicate row for either husk. F2
  stays declined. If F1's disposition changes, it cites the C9 fresh check as evidence; it
  is not silently resolved. The orphan scan ran again (its commands appear); carrying the
  findings did not suppress it. No issue was created.
- C2: the entry row for `feedback_quote_gate_commands.md` equals `after-later-wrap.csv`;
  R1's report is unchanged.

### L0-L3: unreadable, legacy, interrupted and concurrent records (C4, C6)

These run in the second workspace, `ws2`, as dry-runs, so they read the prepared records
and write nothing. Start each in a new Codex session from `ws2\demo-project`:

```powershell
Set-Location (Join-Path $ws2 'demo-project')
codex --cd (Join-Path $ws2 'demo-project') --add-dir $apRoot
```

Prepare each record set in the first window before its run. L0, an unreadable report:

```powershell
$ts2 = Join-Path $ws2 '.claude\task-state'
Get-ChildItem -LiteralPath $ts2 -Filter 'afterparty-*' -File | Remove-Item
[System.IO.File]::WriteAllBytes((Join-Path $ts2 'afterparty-20261023T000000000Z-00000000-0000-4000-8000-0000000000d1.md'), [byte[]](0x72,0x65,0x70,0x6F,0x72,0x74,0x2D,0x6B,0x69,0x6E,0x64,0x3A,0x20,0xC3,0x28,0xFF,0xFE,0x0A))
Save-ApSnapshot 'before-L0'
New-ApPrompt 'L0' '--dry-run --only meta-tool-prune' $ws2
```

L1, legacy only:

```powershell
Get-ChildItem -LiteralPath $ts2 -Filter 'afterparty-*' -File | Remove-Item
Get-ChildItem -LiteralPath (Join-Path $fx 'task-state\legacy') -File | ForEach-Object { Copy-ApRendered $_.FullName (Join-Path $ts2 $_.Name) $ws2 }
Save-ApSnapshot 'before-L1'
New-ApPrompt 'L1' '--dry-run --only meta-tool-prune' $ws2
```

L2, interrupted only:

```powershell
Get-ChildItem -LiteralPath $ts2 -Filter 'afterparty-*' -File | Remove-Item
Get-ChildItem -LiteralPath (Join-Path $fx 'task-state\interrupted') -File | ForEach-Object { Copy-ApRendered $_.FullName (Join-Path $ts2 $_.Name) $ws2 }
Save-ApSnapshot 'before-L2'
New-ApPrompt 'L2' '--dry-run --only meta-tool-prune' $ws2
```

L3, two overlapping concurrent records:

```powershell
Get-ChildItem -LiteralPath $ts2 -Filter 'afterparty-*' -File | Remove-Item
Get-ChildItem -LiteralPath (Join-Path $fx 'task-state\concurrent') -File | ForEach-Object { Copy-ApRendered $_.FullName (Join-Path $ts2 $_.Name) $ws2 }
Save-ApSnapshot 'before-L3'
New-ApPrompt 'L3' '--dry-run --only meta-tool-prune' $ws2
```

After each run (replace `L0` with the run name):

```powershell
Save-ApRun 'L0' $ws2
Save-ApSnapshot 'after-L0'
Compare-ApSnapshot 'before-L0' 'after-L0'
```

Expected, every L run: `no differences` (the records were read, not changed), and
effort/spend `not measured`.

- L0 (C4): the prior report is `unreadable` with a reason, leading to `no trusted prior
  evidence`. No finding is invented from it and nothing is called clean.
- L1 (C6): the legacy record is selected with a `legacy` note. Its routing-settings
  follow-up is imported with a new ID of the form `<this run's run-id>/F<n>`, its source
  pointer to `afterparty-2026-09-17.md`, owner `operator`, and an unknown prior baseline.
  `Tidy some memories later.` has no owner or evidence and is not imported as a finding.
- L2 (C6): the in-progress record is treated as interrupted or concurrent, never as a
  completed comparison. Its finding `...b1/F1` is carried as deferred and marked `outside
  this run's selection`; its `MEMORY.md` entry count is not used as a baseline.
- L3 (C6): the two records overlap in time (09:00-09:40 and 09:05-09:30), so the prior
  report is `ambiguous`, with both source pointers. Finding `...a1/F1` shows both
  decisions, deferred (record `...c1`) and declined (record `...c2`), each with its
  pointer. Neither is chosen by timestamp, and they are not merged.

### W1: the report cannot be written (C13)

This also runs in `ws2`, in normal mode. Replace the report directory with a file so the
write must fail:

```powershell
Remove-Item -LiteralPath (Join-Path $ws2 '.claude\task-state') -Recurse -Force
[System.IO.File]::WriteAllText((Join-Path $ws2 '.claude\task-state'), "a file where the report directory should be`n", $utf8NoBom)
Save-ApSnapshot 'before-W1'
New-ApPrompt 'W1' '--only meta-tool-prune' $ws2
```

Afterwards:

```powershell
Save-ApRun 'W1' $ws2
Save-ApSnapshot 'after-W1'
Compare-ApSnapshot 'before-W1' 'after-W1'
Get-ChildItem -LiteralPath $ws2 -Recurse -Force -Filter 'afterparty-*' | Measure-Object | ForEach-Object { "afterparty files under ws2: $($_.Count)" }
```

Expected: `meta-tool-prune` still runs and the complete report is shown on screen, with
`report persistence failed: <reason>`. The output never claims a saved report path.
`no differences`, and `afterparty files under ws2: 0`.

## 8. Evidence locations

Everything is under the acceptance root (`$apRoot`, printed by every helper block):

| Location | Contents |
|---|---|
| `evidence\A1\identity.txt` | tested source revision, Codex version, generated package hashes |
| `evidence\A3\` | probe output, pre-adoption copies, planned changes, `notes.md` with the session's loaded path and hash |
| `evidence\<run>\prompt.txt` | the exact prompt pasted for that run |
| `evidence\<run>\rollout-*.jsonl` | the Codex session transcript for that run |
| `evidence\<run>\reports\` | copies of the workspace's afterparty reports after that run |
| `evidence\<run>\notes.md` | your observations for that run, one line per expected bullet |
| `evidence\measurements\` | independent entry/exit counts (`entry-P2`, `exit-R1`, `after-later-wrap`) |
| `evidence\snapshots\` | file and git snapshots used by the comparisons |

Create the results table once, before R0, and fill in one row per case as you go:

```powershell
New-ApDir $ev
$rows = @('| Case | Run | Observed | Evidence | Result |', '|---|---|---|---|---|')
foreach ($c in 1..13) { $rows += "| C$c | | | | pass / fail / incomplete |" }
[System.IO.File]::WriteAllLines((Join-Path $ev 'observations.md'), [string[]]$rows, $utf8NoBom)
"results table: $(Join-Path $ev 'observations.md')"
```

When the run is over, copy the evidence into the checkout's ignored `tmp\` folder so it
outlives the temporary directory. Transcripts can hold private text, so it stays local
and is never committed:

```powershell
$keep = Join-Path $skillMesh ('tmp\' + (Split-Path -Leaf $apRoot))
Copy-Item -LiteralPath $ev -Destination $keep -Recurse
git -C $skillMesh check-ignore -q $keep; "evidence copy is ignored by git: $($LASTEXITCODE -eq 0)"
"evidence kept at: $keep"
```

Expected: `evidence copy is ignored by git: True`. The plan's Step 131 evidence pointer
names this folder.

## 9. Recording an incomplete observation

When a command fails, an expected line never appears, a child is unavailable, or you
cannot tell what happened:

1. Leave the state as it is. Do not retry with different flags, and do not answer a gate
   differently to get a result.
2. Write the exact error text or the missing observation into that run's `notes.md`,
   with what you ran and when (`Get-Date -Format o`).
3. Mark the case `incomplete` in `observations.md`, with the reason and the notes path.
   A child that returns a truthful unavailable result is recorded as observed for that
   item, not as a pass of the case.
4. Continue with the next independent case if its prerequisites still hold. R2 and R3
   depend on R1; W1 depends on L0-L3 having finished.

Step 131 is DONE only when every case is `pass`, or a failure is recorded with its owner.
An `incomplete` case keeps Step 131 open.

## 10. Recovery

- **Fixture tree.** Everything from section 5 lives inside `$apRoot`. After copying the
  evidence (section 8), remove it with
  `Remove-Item -LiteralPath $apRoot -Recurse -Force` (this also removes the disposable
  install home from section 3). Nothing outside `$apRoot` refers to it.
- **Install refused in section 4.** The installer changes nothing when it refuses. Keep
  the output, record it, and stop; do not use force or an ownership override.
- **Undo the live adoption.** Reinstall the release that was there before, with the same
  normal installer. Set `$priorRef` to the release tag the coordinator names as last
  installed (for example `v3.0.2`), then build it outside the checkout:

```powershell
$priorRef = '<release tag>'
$rec = Join-Path $apRoot 'recovery'; New-ApDir $rec
git -C $skillMesh archive --format=zip -o (Join-Path $rec 'prior.zip') $priorRef
Expand-Archive -LiteralPath (Join-Path $rec 'prior.zip') -DestinationPath (Join-Path $rec 'src')
powershell -NoProfile -File (Join-Path $rec 'src\tools\build-distributions.ps1') -Provider codex -OutputDir (Join-Path $rec 'dist')
"build exit=$LASTEXITCODE"
Get-ChildItem -LiteralPath (Join-Path $rec 'dist\codex\user-afterparty') -Recurse -File | ForEach-Object { "prior $($_.FullName.Substring($rec.Length + 1)) $((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)" }
```

  Expected: `build exit=0`, and hashes equal to the pre-adoption copies in
  `evidence\A3\pre-adoption\user-afterparty\`. If they differ, `$priorRef` is not the
  release that was installed: stop and ask the coordinator. When they match:

```powershell
powershell -NoProfile -File tools/install-skill-mesh.ps1 -Provider codex -Home $codexHome -DistDir (Join-Path $rec 'dist')
"install exit=$LASTEXITCODE"
powershell -NoProfile -File tools/inspect-host-install.ps1 -Home $codexHome
```

  Expected: `install exit=0`, `user-afterparty: managed (manifest=portable, owned=yes)`,
  and the live files hash to the pre-adoption copies again. A refusal changes nothing:
  record it and stop. Never copy the saved files back by hand.

## 11. What to report

Report, per case, what changed, what was retained or deferred, which coverage was
unavailable, and the measurement limits. Say whether the R1 report's Measurements and
Outcomes tables made it unnecessary to reconstruct a baseline by hand. Do not claim a
general cost or behavior improvement from one run.
