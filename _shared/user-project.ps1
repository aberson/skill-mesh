<#
.SYNOPSIS
    user-project.ps1 -- the session-active project pin (SET, SHOW, CLEAR).

.DESCRIPTION
    The single "eliminate" mechanism of the working-directory model: a session-scoped
    pin naming which project repo pipeline work should target, so cwd stops mattering.
    Honoring skills read the pin and operate on that repo via `git -C <abs-path>`; when
    it is unset they fall back to the plan/argument project, then the cwd-derived repo.
    The pin is advisory-but-honored: it never blocks anything.

    This script replaced the retired project-pin skill (v3 catalog cleanup, decision
    item 15). It is deterministic: no model, no agent, no interactive input.

    Usage (Windows PowerShell 5.1):
        powershell -NoProfile -File user-project.ps1 <name>  -SessionId <id>   # SET
        powershell -NoProfile -File user-project.ps1         -SessionId <id>   # SHOW
        powershell -NoProfile -File user-project.ps1 clear   -SessionId <id>   # CLEAR

    Coding-root discovery is by MARKER, not `git rev-parse --show-toplevel`: walk up from
    -StartDir (default: the current directory) to the directory that owns
    `.claude/observatory/registry.toml`. That root holds the registry, is the base of
    every resolved repo path, and holds the session file
    `<root>\.claude\task-state\sessions\<SessionId>.md` (the task-state schema's
    `**Active project:**` header field), so every reader resolves the pin from one place.

    The pin is one header line, immediately under `**Last written:**`:
        **Active project:** <slug> (<abs-repo-path>)

SESSION IDENTITY (write authority)
    -SessionId is the caller's own stable session id, bound by the caller's host wrapper:
    on Claude, the parent-directory name of the session's scratchpad path (it equals the
    hook session_id and the transcript basename); on Codex and GPT, only an id that the
    running host's wrapper explicitly binds. It is accepted only as one path segment (no
    backslash, slash or `..`).
    Never take the freshest sessions/*.md or the current.md rollup as this session's file,
    and never fabricate, guess or borrow an id: not another host's session variable (for
    example COPILOT_AGENT_SESSION_ID), not an environment variable the running host's
    wrapper does not name, not a launching environment's id, and never the router's
    SKILL_ROUTER_SESSION_ID (a spend-ledger key that names no session). Those files belong
    to other windows; writing one silently re-targets another window's pipeline. This
    script reads no environment variable for identity.
    With no usable id, SET (after name validation) and CLEAR write nothing and print the
    identity-unavailable line; SHOW prints its identity-unavailable line. That is an
    advisory result (exit 0), never a halt for a caller.

WRITES
    Only this session's file: the `**Active project:**`, `**Last written:**` (UTC
    ISO-8601) and `**Session SHA:**` lines, read-merge-write with every other line kept
    verbatim, UTF-8 with no BOM. When the file is absent, SET creates a minimal one whose
    `## Next Action` body is `(none recorded)` (the placeholder the resume hook prints for
    an empty Next Action), never a runnable command. That placeholder is not a fresh,
    operator-authorized plain action and the schema's resume backstop cannot execute it;
    the next task-handoff checkpoint replaces it and preserves the pin. Never current.md,
    another session's file, the registry, or the git index (no git add, no commit).
    Failures write nothing: no coding-root marker (exit 1), unknown name (exit 1, lists
    the known slugs), identity unavailable (exit 0, the advisory line), and a link
    (junction or symlink) between the coding root and the session file (exit 1).
    Idempotent: re-running SET with the same name rewrites the same line; a second CLEAR
    prints `Active project already unset.`

    ASCII-only, no BOM (PowerShell 5.1 reads a no-BOM .ps1 as ANSI). Non-ASCII output
    characters are built from code points.
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)][string]$Project = '',
    [string]$SessionId = '',
    [string]$StartDir = ''
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false } catch { }
$EM = [string][char]0x2014
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false

$IdentityUnavailableLine = 'Active project not changed: required_tool_missing (session identity). Honoring skills fall back to the plan/argument or cwd repo.'

function Write-Line([string]$text) { [Console]::Out.WriteLine($text) }
function Write-Fail([string]$text) { [Console]::Error.WriteLine($text) }

# -- Shared resolution: the coding-root, by marker --
if ($StartDir) { $d = (Resolve-Path -LiteralPath $StartDir).Path } else { $d = (Get-Location).Path }
$startShown = $d
while ($d -and -not (Test-Path -LiteralPath (Join-Path $d '.claude/observatory/registry.toml'))) {
    $p = Split-Path $d -Parent
    if (-not $p -or $p -eq $d) { $d = $null; break }
    $d = $p
}
if (-not $d) {
    Write-Fail "user-project.ps1: could not locate coding-root (no .claude/observatory/registry.toml at or above $startShown)."
    exit 1
}
$root = $d
$registry = Join-Path $root '.claude\observatory\registry.toml'

# -- Session identity: the caller-bound id, one path segment, or unavailable --
$sid = $SessionId
if ($sid -and ($sid.Contains('\') -or $sid.Contains('/') -or $sid.Contains('..') -or $sid.Trim() -ne $sid)) {
    $sid = ''
}
$sessionFile = $null
if ($sid) { $sessionFile = Join-Path $root ".claude\task-state\sessions\$sid.md" }

function Get-SessionSha {
    $sha = $null
    try { $sha = (& git -C $root rev-parse --short HEAD 2>$null) } catch { $sha = $null }
    if ($LASTEXITCODE -ne 0 -or -not $sha) { return 'unknown' }
    return ([string]$sha).Trim()
}

function Get-UtcStamp { return (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }

function Read-SessionLines([string]$path) {
    $text = [System.IO.File]::ReadAllText($path, $Utf8NoBom)
    $nl = "`n"
    if ($text.Contains("`r`n")) { $nl = "`r`n" }
    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($l in [regex]::Split($text, '\r?\n')) { $lines.Add($l) }
    return @{ lines = $lines; nl = $nl }
}

function Set-HeaderLine($lines, [string]$label, [string]$value) {
    # Overwrite an existing `**<label>:**` header line in place; report whether it existed.
    $prefix = "**${label}:**"
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i].StartsWith($prefix)) { $lines[$i] = "$prefix $value"; return $true }
    }
    return $false
}

function Write-SessionLines([string]$path, $lines, [string]$nl) {
    [System.IO.File]::WriteAllText($path, ($lines -join $nl), $Utf8NoBom)
}

function Show-CwdRepo {
    $base = $StartDir
    if (-not $base) { $base = (Get-Location).Path }
    $top = $null
    try { $top = (& git -C $base rev-parse --show-toplevel 2>$null) } catch { $top = $null }
    if ($LASTEXITCODE -ne 0 -or -not $top) { $top = '(not a git repository)' }
    Write-Line "cwd repo: $top"
}

function Assert-SessionTarget {
    # Containment before any write: the session file and every existing folder between it
    # and the coding root must be real entries, not links (junctions, symlinks) that could
    # carry the write somewhere else. The id is already one path segment. Refuse, write
    # nothing, exit 1.
    $p = $sessionFile
    while ($p -and $p.Length -gt $root.Length) {
        if (Test-Path -LiteralPath $p) {
            $item = Get-Item -LiteralPath $p -Force
            if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
                Write-Fail "user-project.ps1: refusing to write through a link under the coding root ($p)."
                exit 1
            }
        }
        $p = Split-Path $p -Parent
    }
}

# -- SHOW --
if ($Project -eq '') {
    if (-not $sid) {
        Write-Line 'Active project: unknown (session identity unavailable); honoring skills fall back to the plan/argument or cwd repo.'
        Show-CwdRepo
        exit 0
    }
    if (Test-Path -LiteralPath $sessionFile -PathType Leaf) {
        $s = Read-SessionLines $sessionFile
        foreach ($l in $s.lines) {
            if ($l.StartsWith('**Active project:**')) {
                $pin = $l.Substring('**Active project:**'.Length).Trim()
                Write-Line "Active project: $pin $EM honored by pipeline skills via git -C."
                exit 0
            }
        }
    }
    Write-Line "Active project: unset $EM deriving from cwd."
    Show-CwdRepo
    exit 0
}

# -- CLEAR --
if ($Project -eq 'clear') {
    if (-not $sid) { Write-Line $IdentityUnavailableLine; exit 0 }
    Assert-SessionTarget
    if (-not (Test-Path -LiteralPath $sessionFile -PathType Leaf)) { Write-Line 'Active project already unset.'; exit 0 }
    $s = Read-SessionLines $sessionFile
    $idx = -1
    for ($i = 0; $i -lt $s.lines.Count; $i++) {
        if ($s.lines[$i].StartsWith('**Active project:**')) { $idx = $i; break }
    }
    if ($idx -lt 0) { Write-Line 'Active project already unset.'; exit 0 }
    $s.lines.RemoveAt($idx)
    $null = Set-HeaderLine $s.lines 'Last written' (Get-UtcStamp)
    $null = Set-HeaderLine $s.lines 'Session SHA' (Get-SessionSha)
    Write-SessionLines $sessionFile $s.lines $s.nl
    Write-Line "Active project cleared $EM reverting to cwd-derived repo."
    exit 0
}

# -- SET: 1. validate against the registry (slug OR path, exact) --
$name = $Project
$reg = [System.IO.File]::ReadAllText($registry)
$entries = foreach ($blk in ($reg -split '(?m)^\s*\[\[project\]\]\s*$')) {
    # The entry's own keys end at its first sub-table header, including an indented one.
    $head = ($blk -split '(?m)^\s*\[', 2)[0]
    $slug = [regex]::Match($head, '(?m)^\s*slug\s*=\s*"([^"]+)"').Groups[1].Value
    if (-not $slug) { continue }
    $path = [regex]::Match($head, '(?m)^\s*path\s*=\s*"([^"]+)"').Groups[1].Value
    if (-not $path) { $path = $slug }
    $owned = [regex]::Match($head, '(?m)^\s*owned\s*=\s*(true|false)').Groups[1].Value
    [pscustomobject]@{ slug = $slug; path = $path; owned = $owned }
}
$entries = @($entries)
$match = $entries | Where-Object { $_.slug -eq $name -or $_.path -eq $name } | Select-Object -First 1
if ($null -eq $match) {
    Write-Fail ("user-project.ps1: unknown project '$name'. Known slugs: " + ((@($entries | ForEach-Object { $_.slug }) | Sort-Object) -join ', '))
    exit 1
}

# -- SET: 2. the absolute repo path, backslash-normalized --
$abs = [System.IO.Path]::GetFullPath((Join-Path $root $match.path))
$suffix = ''
if ($match.owned -eq 'false') { $suffix = ' [third-party]' }

# -- SET: 3. identity --
if (-not $sid) { Write-Line $IdentityUnavailableLine; exit 0 }
Assert-SessionTarget

# -- SET: 4. write the pin (read-merge-write) --
$pinValue = "$($match.slug) ($abs)"
$stamp = Get-UtcStamp
$sha = Get-SessionSha
if (Test-Path -LiteralPath $sessionFile -PathType Leaf) {
    $s = Read-SessionLines $sessionFile
    $lines = $s.lines
    if (-not (Set-HeaderLine $lines 'Active project' $pinValue)) {
        $at = -1
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i].StartsWith('**Last written:**')) { $at = $i; break }
        }
        if ($at -lt 0) {
            # Malformed file: after the last `**...:**` header line before the first section.
            for ($i = 0; $i -lt $lines.Count; $i++) {
                if ($lines[$i].StartsWith('## ')) { break }
                if ($lines[$i] -match '^\*\*[^*]+:\*\*') { $at = $i }
            }
        }
        if ($at -lt 0) { $at = 0 }
        $lines.Insert($at + 1, "**Active project:** $pinValue")
    }
    $null = Set-HeaderLine $lines 'Last written' $stamp
    $null = Set-HeaderLine $lines 'Session SHA' $sha
    Write-SessionLines $sessionFile $lines $s.nl
} else {
    $dir = Split-Path -Parent $sessionFile
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $date = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
    $body = @(
        "# Task State $EM project pin $date",
        '',
        "**Task:** (no task yet $EM project pinned via user-project.ps1)",
        '**Status:** IN_PROGRESS',
        "**Session SHA:** $sha",
        "**Last written:** $stamp",
        "**Active project:** $pinValue",
        '',
        '## Next Action',
        '',
        '(none recorded)',
        ''
    )
    [System.IO.File]::WriteAllText($sessionFile, ($body -join "`n"), $Utf8NoBom)
}

# -- SET: 5. confirm --
Write-Line ("Pinned active project: $($match.slug) ($abs). Pipeline skills will target it via git -C regardless of cwd." + $suffix)
exit 0
