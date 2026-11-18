<#
.SYNOPSIS
    install-companions.ps1 -- install (or uninstall) the Skill Mesh companion
    members listed in config/companions.json into one target home.

.DESCRIPTION
    Core companion plan (documentation/core-companion-plan.md) Step 9. The members
    are small public tools the skills call (passing-notes, tripwire, ...). This
    script is normally run by tools/install-skill-mesh.ps1 -Companions core|all,
    AFTER the skill profile install has completed; it can also be run on its own.

    For each member of the selected rings, in manifest order:
      1. uv tool install "git+<repo>@<tag>"
      2. the member's health argv (exit 0 = healthy)
      3. the member's own skill installer, when the manifest names one: it is run
         from a tagged source checkout (git clone --depth 1 --branch <tag>) kept in
         <home>/.skill-mesh-companions/src/<slug>, with "--host <host> --root <the
         host's skills folder under this home>" appended
      4. the member's setup_write.install, when present
      5. one status line: "install-companions: <slug>: installed",
         "... already current" or "... skipped: <reason>"
      6. for -Companions all, the optional ring's setup lines, printed, never run.

    -Uninstall reverses only ledger-owned work, member by member in reverse
    manifest order: setup_write.uninstall, the member skill uninstaller (for each
    host it ran for), the source checkout, then uv tool uninstall <slug>. Both
    install and uninstall run tools/companions.py verify on the manifest first.

    A tag upgrade keeps the OLD tag in the ledger until the reinstall, health
    check, member skill installer and setup_write have all succeeded, so a failed
    or interrupted upgrade is re-attempted by the next run.

    THE COMPANION LEDGER is <home>/.skill-mesh-companions.json (schema_version 1,
    plan section 4), written atomically (temp file + replace) and read only by this
    script. It is separate from the Skill Mesh skill ledger
    (<home>/.skill-mesh-install.json), which this script never opens. A member
    whose command was already on PATH (or in uv's tool bin directory) before this
    script installed it is recorded "pre-existing" and is never installed over or
    uninstalled. Member skill files are owned by the member's installer and its own
    ledger; Skill Mesh never copies or deletes them itself.

    Fail open: a member that fails is reported and the others continue. With uv,
    git or Python 3.12+ missing from PATH every member is reported
    "skipped: missing <tool>" and nothing runs. A member with a null tag is
    "skipped: unreleased".

    Exit codes: 0 done (skips included); 1 at least one member failed; 2 usage or
    home error; 3 manifest or companion ledger refused (nothing changed); 4 another
    companion operation holds this home's lock.

    ASCII-only, no BOM (Windows PowerShell 5.1 reads a no-BOM .ps1 as ANSI).

.PARAMETER Provider
    'claude' | 'gpt' | 'codex': the host profile whose skills folder member skill
    installers write into. gpt has no member skill host, so member skills are not
    installed for it.

.PARAMETER Home
    The target home (must exist). Alias: -Destination. Backed by $TargetHome.

.PARAMETER Companions
    'core' (core ring), 'all' (core + optional) or 'none' (do nothing). Candidates
    are never installed. With -Uninstall, 'core' reverses ledger members whose
    manifest ring is core and 'all' reverses every ledger member.

.PARAMETER Manifest
    The companion manifest to read (default: config/companions.json beside this
    script). It is checked with tools/companions.py verify before anything runs.

.PARAMETER Uninstall
    Reverse ledger-owned companion work.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('claude', 'gpt', 'codex')]
    [string]$Provider,

    [Parameter(Mandatory = $true)]
    [Alias('Home', 'Destination')]
    [string]$TargetHome,

    # Defaults to 'core' here, unlike install-skill-mesh.ps1 -Companions (which
    # defaults to 'none' until plan Step 20): running this script on its own is
    # already an explicit request to install companions.
    [ValidateSet('core', 'all', 'none')]
    [string]$Companions = 'core',

    [string]$Manifest = '',

    [switch]$Uninstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$TOOLS_DIR = $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $TOOLS_DIR
$PATH_GUARD = Join-Path $REPO_ROOT 'runtime\path-guard.ps1'
$DISCOVERY = Join-Path $TOOLS_DIR 'skill-mesh-discovery.ps1'
$MANIFEST_TOOL = Join-Path $TOOLS_DIR 'companions.py'

# Resolve-SafePath / Get-CanonicalRealPath (containment, follows reparse points).
. $PATH_GUARD
# The provider -> discovery-root map (its one owner).
. $DISCOVERY

$LEDGER_NAME = '.skill-mesh-companions.json'
$CACHE_NAME = '.skill-mesh-companions'
$LEDGER_SCHEMA_VERSION = 1
$MANIFEST_SCHEMA_VERSION = 1
$PYTHON_FLOOR = [Version]'3.12'
$UTF8_NO_BOM = New-Object System.Text.UTF8Encoding($false)

# Skill Mesh provider -> the --host value of a member skill installer. Read from
# passing-notes tools/skills_install.py (its --host choices are claude and codex).
# A provider absent here has no member skill host: member skills are not installed.
$MEMBER_SKILL_HOSTS = @{
    'claude' = 'claude'
    'codex'  = 'codex'
}

# Bounded child processes: a member install fetches from the network.
$TIMEOUT_INSTALL_S = 900
$TIMEOUT_COMMAND_S = 300
$TIMEOUT_PROBE_S = 30
$OUTPUT_TAIL = 400

$script:Failures = 0

function Write-Line([string]$text) {
    Write-Host ('install-companions: ' + $text)
}

function Write-Refusal([string]$text) {
    # Refusals and errors go to the error stream, as in tools/install-skill-mesh.ps1.
    [Console]::Error.WriteLine('install-companions: ' + $text)
}

function Write-Status([string]$slug, [string]$status) {
    Write-Line ($slug + ': ' + $status)
}

function Write-Note([string]$slug, [string]$text) {
    Write-Line ('note: ' + $slug + ': ' + $text)
}

function Get-Prop($obj, [string]$name) {
    # StrictMode-safe property read; $null when absent.
    if ($null -eq $obj) { return $null }
    $p = $obj.PSObject.Properties[$name]
    if ($p) { return $p.Value }
    return $null
}

function Test-HasProp($obj, [string]$name) {
    if ($null -eq $obj) { return $false }
    return ($null -ne $obj.PSObject.Properties[$name])
}

# -- Child processes ------------------------------------------------------------

function ConvertTo-NativeArgument([string]$arg) {
    # CommandLineToArgvW quoting: quote when empty or holding space/tab/quote;
    # double backslashes that precede a quote.
    if ($arg.Length -gt 0 -and $arg -notmatch '[\s"]') { return $arg }
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append('"')
    $slashes = 0
    foreach ($ch in $arg.ToCharArray()) {
        if ($ch -eq '\') {
            $slashes++
        } elseif ($ch -eq '"') {
            [void]$sb.Append('\' * (2 * $slashes + 1))
            [void]$sb.Append('"')
            $slashes = 0
        } else {
            if ($slashes -gt 0) { [void]$sb.Append('\' * $slashes) }
            [void]$sb.Append($ch)
            $slashes = 0
        }
    }
    if ($slashes -gt 0) { [void]$sb.Append('\' * (2 * $slashes)) }
    [void]$sb.Append('"')
    return $sb.ToString()
}

function Get-Tail([string]$text) {
    if ($null -eq $text) { return '' }
    $t = $text.Trim()
    if ($t.Length -gt $OUTPUT_TAIL) { $t = '...' + $t.Substring($t.Length - $OUTPUT_TAIL) }
    return (($t -split "`r?`n") -join ' | ')
}

function Invoke-Native {
    # Run one resolved executable with an argv list, no window, stdin closed,
    # stdout/stderr captured, bounded by a timeout. On timeout the whole process
    # tree is killed. Never throws for a non-zero exit.
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = '',
        [int]$TimeoutSeconds = 300
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = (@($Arguments | ForEach-Object { ConvertTo-NativeArgument ([string]$_) }) -join ' ')
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $UTF8_NO_BOM
    $psi.StandardErrorEncoding = $UTF8_NO_BOM
    if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
        $psi.WorkingDirectory = $WorkingDirectory
    }
    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
    } catch {
        return [PSCustomObject]@{ ExitCode = -1; Out = ''; Err = $_.Exception.Message; TimedOut = $false }
    }
    try {
        $proc.StandardInput.Close()
        $outTask = $proc.StandardOutput.ReadToEndAsync()
        $errTask = $proc.StandardError.ReadToEndAsync()
        if (-not $proc.WaitForExit($TimeoutSeconds * 1000)) {
            $taskkill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
            try {
                $kill = New-Object System.Diagnostics.ProcessStartInfo
                $kill.FileName = $taskkill
                $kill.Arguments = '/PID ' + $proc.Id + ' /T /F'
                $kill.UseShellExecute = $false
                $kill.CreateNoWindow = $true
                $killer = [System.Diagnostics.Process]::Start($kill)
                [void]$killer.WaitForExit(15000)
            } catch {
                try { $proc.Kill() } catch { }
            }
            [void]$proc.WaitForExit(15000)
            return [PSCustomObject]@{ ExitCode = -1; Out = ''; Err = "timed out after $TimeoutSeconds s"; TimedOut = $true }
        }
        $proc.WaitForExit()
        return [PSCustomObject]@{
            ExitCode = $proc.ExitCode
            Out      = [string]$outTask.Result
            Err      = [string]$errTask.Result
            TimedOut = $false
        }
    } finally {
        $proc.Dispose()
    }
}

function Find-Application([string]$name) {
    # An application on PATH only: never a PowerShell alias, function or cmdlet of
    # the same name.
    $cmd = Get-Command -Name $name -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $cmd) { return $null }
    return [string]$cmd.Source
}

$script:UvBinDir = $null
$script:UvBinDirRead = $false

function Get-UvBinDir {
    if ($script:UvBinDirRead) { return $script:UvBinDir }
    $script:UvBinDirRead = $true
    if ($null -eq $script:UvExe) { return $null }
    $r = Invoke-Native -FilePath $script:UvExe -Arguments @('tool', 'dir', '--bin') -TimeoutSeconds $TIMEOUT_PROBE_S
    if ($r.ExitCode -eq 0) {
        $line = @(($r.Out -split "`r?`n") | Where-Object { $_.Trim() -ne '' } | Select-Object -First 1)
        if ($line.Count -eq 1 -and [System.IO.Path]::IsPathRooted($line[0].Trim()) -and
            (Test-Path -LiteralPath $line[0].Trim() -PathType Container)) {
            $script:UvBinDir = $line[0].Trim()
        }
    }
    return $script:UvBinDir
}

function Find-MemberCommand([string]$name) {
    # A member command: PATH first, then uv's tool bin directory (which uv does not
    # always put on PATH for a new user).
    $onPath = Find-Application $name
    if ($null -ne $onPath) { return $onPath }
    $bin = Get-UvBinDir
    if ($null -eq $bin) { return $null }
    foreach ($ext in @('.exe', '.cmd', '.bat', '')) {
        $candidate = Join-Path $bin ($name + $ext)
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    return $null
}

function Find-Python312 {
    # The first python on PATH (python, python3, then the py launcher) that is
    # 3.12 or later. Returns @(exe, prefixArgs) or $null.
    $probe = "import sys;sys.stdout.write(str(sys.version_info[0])+'.'+str(sys.version_info[1]))"
    foreach ($candidate in @(@('python', @()), @('python3', @()), @('py', @('-3')))) {
        $exe = Find-Application ([string]$candidate[0])
        if ($null -eq $exe) { continue }
        $prefix = @($candidate[1])
        $r = Invoke-Native -FilePath $exe -Arguments ($prefix + @('-c', $probe)) -TimeoutSeconds $TIMEOUT_PROBE_S
        if ($r.ExitCode -ne 0) { continue }
        $text = $r.Out.Trim()
        $version = $null
        if ($text -match '^\d+\.\d+$' -and [Version]::TryParse($text, [ref]$version) -and
            $version -ge $PYTHON_FLOOR) {
            return , @($exe, $prefix)
        }
    }
    return $null
}

# -- Paths inside the home --------------------------------------------------------

function Get-HomePath([string]$rel) {
    # Containment-checked absolute path under the home (follows reparse points).
    return (Resolve-SafePath -Path (Join-Path $script:HomeReal $rel) -AllowedRoots @($script:HomeReal))
}

function Get-SkillsRoot([string]$memberHost) {
    $provider = $null
    foreach ($key in $MEMBER_SKILL_HOSTS.Keys) {
        if ($MEMBER_SKILL_HOSTS[$key] -ceq $memberHost) { $provider = $key }
    }
    if ($null -eq $provider) { return $null }
    $rel = Get-SkillMeshDiscoveryRoot $provider
    if ($null -eq $rel) { return $null }
    return (Get-HomePath ($rel -replace '/', '\'))
}

function Get-CheckoutPath([string]$slug) {
    return (Get-HomePath ($CACHE_NAME + '\src\' + $slug))
}

function Remove-CompanionTree([string]$path) {
    # Delete one directory this script created under the companion cache. Refuses
    # (returns $false) when the tree holds a reparse point, so a planted junction is
    # never followed. Read-only files (git packs) are cleared first.
    $safeTree = Resolve-SafePath -Path $path -AllowedRoots @((Get-HomePath $CACHE_NAME))
    if (-not (Test-Path -LiteralPath $safeTree)) { return $true }
    $root = New-Object System.IO.DirectoryInfo($safeTree)
    if (($root.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { return $false }
    $stack = New-Object System.Collections.Stack
    $stack.Push($root)
    $files = @()
    while ($stack.Count -gt 0) {
        $dir = $stack.Pop()
        foreach ($entry in $dir.GetFileSystemInfos()) {
            if (($entry.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { return $false }
            if ($entry -is [System.IO.DirectoryInfo]) { $stack.Push($entry) } else { $files += $entry }
        }
    }
    foreach ($f in $files) {
        if (($f.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0) {
            $f.Attributes = [System.IO.FileAttributes]::Normal
        }
    }
    [System.IO.Directory]::Delete($safeTree, $true)
    return $true
}

function Remove-EmptyCacheDirs {
    foreach ($rel in @(($CACHE_NAME + '\src'), $CACHE_NAME)) {
        $safeDir = Resolve-SafePath -Path (Join-Path $script:HomeReal $rel) -AllowedRoots @($script:HomeReal)
        if ((Test-Path -LiteralPath $safeDir -PathType Container) -and
            @(Get-ChildItem -LiteralPath $safeDir -Force).Count -eq 0) {
            Remove-Item -LiteralPath $safeDir -Force
        }
    }
}

# -- Manifest -----------------------------------------------------------------------

function Read-Manifest([string]$path) {
    try {
        $text = [System.IO.File]::ReadAllText($path, $UTF8_NO_BOM)
        $doc = ConvertFrom-Json -InputObject $text
    } catch {
        return $null
    }
    if ($null -eq $doc -or (Get-Prop $doc 'schema_version') -ne $MANIFEST_SCHEMA_VERSION) { return $null }
    $members = Get-Prop $doc 'members'
    if ($null -eq $members) { return $null }
    return , @($members)
}

function Test-ManifestVerified([string]$path, $python) {
    $r = Invoke-Native -FilePath ([string]$python[0]) `
        -Arguments (@($python[1]) + @($MANIFEST_TOOL, 'verify', '--manifest', $path)) `
        -TimeoutSeconds $TIMEOUT_COMMAND_S
    if ($r.ExitCode -eq 0) { return $null }
    $why = "exit $($r.ExitCode)"
    try {
        $payload = ConvertFrom-Json -InputObject $r.Out
        $findings = @(Get-Prop $payload 'findings')
        if ($findings.Count -gt 0 -and $null -ne $findings[0]) {
            $why += ': ' + [string](Get-Prop $findings[0] 'message')
        }
    } catch {
        $why += ': ' + (Get-Tail ($r.Out + ' ' + $r.Err))
    }
    return $why
}

function Expand-Argv($argv) {
    # Replace the two manifest tokens in every entry after the command.
    $settings = Join-Path (Join-Path $script:HomeReal '.claude') 'settings.json'
    $out = @()
    $i = 0
    foreach ($item in @($argv)) {
        $s = [string]$item
        if ($i -gt 0) { $s = $s.Replace('{home}', $script:HomeReal).Replace('{settings}', $settings) }
        $out += $s
        $i++
    }
    return , $out
}

function Invoke-MemberArgv($argv, [string]$workingDirectory, [int]$timeout, [string[]]$extra = @()) {
    # Resolve argv[0] as a member command (PATH, then uv's tool bin) and run it.
    $expanded = Expand-Argv $argv
    $exe = Find-MemberCommand ([string]$expanded[0])
    if ($null -eq $exe) {
        return [PSCustomObject]@{ ExitCode = -1; Out = ''; Err = "command '$($expanded[0])' not found"; TimedOut = $false }
    }
    $rest = @()
    if ($expanded.Count -gt 1) { $rest = @($expanded[1..($expanded.Count - 1)]) }
    return (Invoke-Native -FilePath $exe -Arguments ($rest + $extra) `
            -WorkingDirectory $workingDirectory -TimeoutSeconds $timeout)
}

function Get-FailReason([string]$what, $r) {
    if ($r.TimedOut) { return "$what timed out" }
    if ($r.ExitCode -eq -1 -and $r.Err) { return "$what failed ($($r.Err))" }
    return "$what failed (exit $($r.ExitCode))"
}

# -- Companion ledger -------------------------------------------------------------

function New-LedgerEntry([string]$tag, [string]$tool) {
    return [ordered]@{
        tag          = $tag
        tool         = $tool
        skills       = $false
        skills_hosts = @()
        setup_write  = $false
        hooks        = @()
    }
}

function Read-CompanionLedger {
    # Returns @{ members = ordered; opt_outs = ordered } or throws a refusal.
    $ledgerPath = Get-HomePath $LEDGER_NAME
    $ledger = @{
        members  = [ordered]@{}
        opt_outs = [ordered]@{ no_hooks = $false; skip_hook = @() }
        exists   = $false
    }
    if (-not (Test-Path -LiteralPath $ledgerPath)) { return $ledger }
    $ledger.exists = $true
    try {
        $doc = ConvertFrom-Json -InputObject ([System.IO.File]::ReadAllText($ledgerPath, $UTF8_NO_BOM))
    } catch {
        throw "companion ledger $LEDGER_NAME is not JSON; nothing was changed"
    }
    $version = Get-Prop $doc 'schema_version'
    if (($version -isnot [int] -and $version -isnot [long]) -or $version -lt 1) {
        throw "companion ledger $LEDGER_NAME has no valid schema_version; nothing was changed"
    }
    if ($version -gt $LEDGER_SCHEMA_VERSION) {
        throw "companion ledger $LEDGER_NAME has schema_version $version, newer than this installer ($LEDGER_SCHEMA_VERSION); nothing was changed"
    }
    $members = Get-Prop $doc 'members'
    if ($null -eq $members -or $members -isnot [System.Management.Automation.PSCustomObject]) {
        throw "companion ledger $LEDGER_NAME has no members object; nothing was changed"
    }
    foreach ($p in $members.PSObject.Properties) {
        $e = $p.Value
        $tag = Get-Prop $e 'tag'
        $tool = Get-Prop $e 'tool'
        $skills = Get-Prop $e 'skills'
        $setupWrite = Get-Prop $e 'setup_write'
        if ($p.Name -notmatch '^[a-z0-9][a-z0-9-]*$' -or $tag -isnot [string] -or
            ($tool -cne 'installed' -and $tool -cne 'pre-existing') -or
            $skills -isnot [bool] -or $setupWrite -isnot [bool] -or
            -not (Test-HasProp $e 'hooks')) {
            throw "companion ledger $LEDGER_NAME has a malformed entry for '$($p.Name)'; nothing was changed"
        }
        $hosts = @()
        foreach ($h in @(Get-Prop $e 'skills_hosts')) {
            if ($null -eq $h) { continue }
            if ($h -isnot [string] -or $MEMBER_SKILL_HOSTS.Values -notcontains $h) {
                throw "companion ledger $LEDGER_NAME has a malformed skills_hosts for '$($p.Name)'; nothing was changed"
            }
            $hosts += $h
        }
        $entry = New-LedgerEntry $tag $tool
        $entry.skills = $skills
        $entry.skills_hosts = $hosts
        $entry.setup_write = $setupWrite
        $entry.hooks = @(Get-Prop $e 'hooks' | Where-Object { $null -ne $_ })
        $ledger.members[$p.Name] = $entry
    }
    $opt = Get-Prop $doc 'opt_outs'
    if ($null -ne $opt) {
        $noHooks = Get-Prop $opt 'no_hooks'
        if ($noHooks -is [bool]) { $ledger.opt_outs.no_hooks = $noHooks }
        $ledger.opt_outs.skip_hook = @(Get-Prop $opt 'skip_hook' | Where-Object { $_ -is [string] })
    }
    return $ledger
}

function Write-CompanionLedger($ledger) {
    # Atomic: write a sibling temp file, then replace. Removes the ledger when it
    # records nothing (no members, default opt-outs).
    $safeLedger = Resolve-SafePath -Path (Join-Path $script:HomeReal $LEDGER_NAME) -AllowedRoots @($script:HomeReal)
    $safeTemp = $safeLedger + '.tmp'
    # A stale temp (or a planted link of that name) is removed, never written
    # through: File.Delete removes a link itself, not its target. The write below
    # then creates a fresh regular file. Unconditional: Test-Path is false for a
    # dangling link, and File.Delete is a no-op when nothing is there.
    [System.IO.File]::Delete($safeTemp)
    $defaultOptOuts = (-not $ledger.opt_outs.no_hooks) -and (@($ledger.opt_outs.skip_hook).Count -eq 0)
    if ($ledger.members.Count -eq 0 -and $defaultOptOuts) {
        if (Test-Path -LiteralPath $safeLedger) { [System.IO.File]::Delete($safeLedger) }
        $ledger.exists = $false
        return
    }
    $members = [ordered]@{}
    foreach ($slug in @($ledger.members.Keys | Sort-Object)) {
        $e = $ledger.members[$slug]
        $e.skills = (@($e.skills_hosts).Count -gt 0)
        $members[$slug] = [ordered]@{
            tag          = $e.tag
            tool         = $e.tool
            skills       = $e.skills
            skills_hosts = @($e.skills_hosts)
            setup_write  = $e.setup_write
            hooks        = @($e.hooks)
        }
    }
    $doc = [ordered]@{
        schema_version = $LEDGER_SCHEMA_VERSION
        members        = $members
        opt_outs       = [ordered]@{
            no_hooks  = [bool]$ledger.opt_outs.no_hooks
            skip_hook = @($ledger.opt_outs.skip_hook)
        }
    }
    $text = (ConvertTo-Json -InputObject $doc -Depth 12) -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($safeTemp, $text + "`n", $UTF8_NO_BOM)
    if (Test-Path -LiteralPath $safeLedger) {
        [System.IO.File]::Replace($safeTemp, $safeLedger, [NullString]::Value)
    } else {
        [System.IO.File]::Move($safeTemp, $safeLedger)
    }
    $ledger.exists = $true
}

# -- Member steps -----------------------------------------------------------------

function Invoke-ToolInstall([string]$repo, [string]$tag, [switch]$Force) {
    $args2 = @('tool', 'install')
    if ($Force) { $args2 += '--force' }
    $args2 += ('git+' + $repo + '@' + $tag)
    return (Invoke-Native -FilePath $script:UvExe -Arguments $args2 -TimeoutSeconds $TIMEOUT_INSTALL_S)
}

function Initialize-Checkout([string]$slug, [string]$repo, [string]$tag) {
    # A fresh tagged checkout at <home>/.skill-mesh-companions/src/<slug>.
    # Returns $null on success or a failure reason.
    if ($null -eq $script:GitExe) { return 'missing git' }
    $checkout = Get-CheckoutPath $slug
    if (-not (Remove-CompanionTree $checkout)) {
        return "source checkout $checkout holds a reparse point; left in place"
    }
    $safeParent = Resolve-SafePath -Path (Join-Path $script:HomeReal ($CACHE_NAME + '\src')) -AllowedRoots @($script:HomeReal)
    if (-not (Test-Path -LiteralPath $safeParent)) {
        New-Item -ItemType Directory -Path $safeParent -Force | Out-Null
    }
    $r = Invoke-Native -FilePath $script:GitExe -TimeoutSeconds $TIMEOUT_INSTALL_S -Arguments @(
        '-c', 'advice.detachedHead=false', 'clone', '--quiet', '--depth', '1',
        '--branch', $tag, '--', $repo, $checkout)
    if ($r.ExitCode -ne 0) { return (Get-FailReason 'git clone' $r) }
    return $null
}

function Invoke-SkillInstaller($argv, [string]$slug, [string]$memberHost) {
    # Runs a member skill installer/uninstaller argv from the source checkout with
    # --host <host> --root <skills folder>. Returns $null or a failure reason.
    $root = Get-SkillsRoot $memberHost
    if ($null -eq $root) { return "no skills folder for host $memberHost" }
    if (-not (Test-Path -LiteralPath $root -PathType Container)) {
        return "skills folder $root does not exist (install the Skill Mesh $memberHost profile first)"
    }
    $checkout = Get-CheckoutPath $slug
    $r = Invoke-MemberArgv $argv $checkout $TIMEOUT_INSTALL_S @('--host', $memberHost, '--root', $root)
    if ($r.ExitCode -ne 0) {
        return ((Get-FailReason ('member skill ' + [string]@($argv)[-1]) $r) + ' ' + (Get-Tail $r.Err))
    }
    return $null
}

function Install-Member($member, $ledger) {
    $slug = [string]$member.slug
    $tag = [string]$member.tag
    $repo = [string]$member.repo
    $cli = [string]$member.cli
    $skills = Get-Prop $member 'skills'
    $setupWrite = Get-Prop $member 'setup_write'
    $memberHost = $null
    if ($MEMBER_SKILL_HOSTS.ContainsKey($Provider)) { $memberHost = $MEMBER_SKILL_HOSTS[$Provider] }
    $entry = $null
    if ($ledger.members.Contains($slug)) { $entry = $ledger.members[$slug] }
    $changed = $false
    $rerunHosts = @()
    $rerunSetup = $false

    # 1. The tool.
    if ($null -eq $entry -or $entry.tool -ceq 'pre-existing') {
        $found = Find-MemberCommand $cli
        if ($null -ne $found) {
            $hooks = @()
            if ($null -ne $entry) { $hooks = @($entry.hooks) }
            $pre = New-LedgerEntry $tag 'pre-existing'
            $pre.hooks = $hooks
            $ledger.members[$slug] = $pre
            Write-CompanionLedger $ledger
            return "skipped: pre-existing $cli at $found was not installed by Skill Mesh; left alone"
        }
        # Write-ahead: ownership is recorded BEFORE uv runs, so a crash between the
        # install and the ledger write cannot leave an installed tool that a later
        # run mistakes for a pre-existing one and never uninstalls. A ledger-owned
        # entry whose command is missing is simply re-installed next time.
        $entry = New-LedgerEntry $tag 'installed'
        $ledger.members[$slug] = $entry
        Write-CompanionLedger $ledger
        $r = Invoke-ToolInstall $repo $tag
        if ($r.ExitCode -ne 0) {
            if ($null -eq (Find-MemberCommand $cli)) {
                # Nothing was installed: drop the write-ahead entry.
                [void]$ledger.members.Remove($slug)
                Write-CompanionLedger $ledger
            }
            $script:Failures++
            return ('skipped: ' + (Get-FailReason 'uv tool install' $r) + ' ' + (Get-Tail $r.Err))
        }
        $changed = $true
    } elseif ($entry.tag -cne $tag -or $null -eq (Find-MemberCommand $cli)) {
        # Ledger-owned: upgrade (or repair) in place.
        $r = Invoke-ToolInstall $repo $tag -Force
        if ($r.ExitCode -ne 0) {
            $script:Failures++
            return ('skipped: ' + (Get-FailReason 'uv tool install' $r) + ' ' + (Get-Tail $r.Err))
        }
        $changed = $true
    }
    if ($entry.tag -cne $tag) {
        # A new tag re-runs the member's own installers, which upgrade in place.
        # The ledger keeps the OLD tag until every step below has succeeded, so a
        # failure (or a killed process) leaves the tag mismatch in place and the
        # next run re-attempts the owed work instead of reporting it current.
        $rerunHosts = @($entry.skills_hosts)
        $rerunSetup = [bool]$entry.setup_write
    }

    # 2. The health check.
    $health = @(Get-Prop $member 'health')
    if ($health.Count -gt 0) {
        $r = Invoke-MemberArgv $health '' $TIMEOUT_COMMAND_S
        if ($r.ExitCode -ne 0) {
            $script:Failures++
            return ('skipped: ' + (Get-FailReason 'health check' $r))
        }
        if ($null -eq (Find-Application ([string]$health[0]))) {
            Write-Note $slug ("'$($health[0])' is not on PATH; add uv's tool directory to PATH (uv tool update-shell)")
        }
    }

    # 3. The member's own skill installer.
    if ($null -ne $skills) {
        $hosts = @($rerunHosts)
        if ($null -eq $memberHost) {
            Write-Note $slug "member skills not installed: the member skill installer has no host for provider $Provider"
        } elseif ($hosts -notcontains $memberHost -and @($entry.skills_hosts) -notcontains $memberHost) {
            $hosts += $memberHost
        }
        if ($hosts.Count -gt 0) {
            $why = Initialize-Checkout $slug $repo $tag
            if ($null -ne $why) {
                $script:Failures++
                return ('skipped: member skills not installed: ' + $why)
            }
            foreach ($h in $hosts) {
                $why = Invoke-SkillInstaller (Get-Prop $skills 'installer') $slug $h
                if ($null -ne $why) {
                    $script:Failures++
                    return ('skipped: ' + $why)
                }
                if (@($entry.skills_hosts) -notcontains $h) {
                    $entry.skills_hosts = @(@($entry.skills_hosts) + $h)
                }
                Write-CompanionLedger $ledger
                $changed = $true
            }
        }
    }

    # 4. The member's own ledgered writer.
    if ($null -ne $setupWrite -and ($rerunSetup -or -not $entry.setup_write)) {
        $r = Invoke-MemberArgv (Get-Prop $setupWrite 'install') '' $TIMEOUT_INSTALL_S
        if ($r.ExitCode -ne 0) {
            $script:Failures++
            return ('skipped: ' + (Get-FailReason 'setup_write.install' $r) + ' ' + (Get-Tail $r.Err))
        }
        $entry.setup_write = $true
        Write-CompanionLedger $ledger
        $changed = $true
    }

    # Every step succeeded: only now does the ledger record the new tag.
    if ($entry.tag -cne $tag) {
        $entry.tag = $tag
        Write-CompanionLedger $ledger
        $changed = $true
    }

    if ($changed) { return 'installed' }
    return 'already current'
}

function Uninstall-Member([string]$slug, $member, $ledger) {
    $entry = $ledger.members[$slug]
    if ($entry.tool -ceq 'pre-existing') {
        [void]$ledger.members.Remove($slug)
        Write-CompanionLedger $ledger
        $cliName = $slug
        if ($null -ne $member) { $cliName = [string]$member.cli }
        return "skipped: pre-existing $cliName was not installed by Skill Mesh; left alone"
    }
    $cli = $slug
    $skills = $null
    $setupWrite = $null
    $repo = $null
    if ($null -ne $member) {
        $cli = [string]$member.cli
        $skills = Get-Prop $member 'skills'
        $setupWrite = Get-Prop $member 'setup_write'
        $repo = Get-Prop $member 'repo'
    }

    # Reverse of install step 4.
    if ($entry.setup_write) {
        $undo = $null
        if ($null -ne $setupWrite) { $undo = Get-Prop $setupWrite 'uninstall' }
        if ($null -ne $undo) {
            $r = Invoke-MemberArgv $undo '' $TIMEOUT_INSTALL_S
            if ($r.ExitCode -ne 0) {
                $script:Failures++
                return ('skipped: ' + (Get-FailReason 'setup_write.uninstall' $r) + ' ' + (Get-Tail $r.Err))
            }
        } else {
            Write-Note $slug 'its setup_write output has no uninstall command; left in place'
        }
        $entry.setup_write = $false
        Write-CompanionLedger $ledger
    }

    # Reverse of install step 3, for every host it ran for. A host whose skills
    # folder is gone (for example the skill uninstall removed it) has nothing left
    # to reverse: it is noted and dropped, so the rest of the member still reverses.
    foreach ($h in @($entry.skills_hosts)) {
        $root = Get-SkillsRoot $h
        if ($null -eq $root -or -not (Test-Path -LiteralPath $root -PathType Container)) {
            Write-Note $slug "the $h skills folder is gone; no member skills left to uninstall there"
            $entry.skills_hosts = @(@($entry.skills_hosts) | Where-Object { $_ -cne $h })
            Write-CompanionLedger $ledger
        }
    }
    $hosts = @($entry.skills_hosts)
    if ($hosts.Count -gt 0) {
        if ($null -eq $skills) {
            $script:Failures++
            return 'skipped: member skills were installed but the manifest no longer names their uninstaller; ledger kept'
        }
        $checkout = Get-CheckoutPath $slug
        if (-not (Test-Path -LiteralPath $checkout -PathType Container)) {
            if ($null -eq $script:GitExe) { return "skipped: missing git (needed to fetch $slug $($entry.tag) for its skill uninstaller)" }
            $why = Initialize-Checkout $slug ([string]$repo) $entry.tag
            if ($null -ne $why) {
                $script:Failures++
                return ('skipped: member skills not uninstalled: ' + $why)
            }
        }
        [array]::Reverse($hosts)
        foreach ($h in $hosts) {
            $why = Invoke-SkillInstaller (Get-Prop $skills 'uninstaller') $slug $h
            if ($null -ne $why) {
                $script:Failures++
                return ('skipped: ' + $why)
            }
            $entry.skills_hosts = @(@($entry.skills_hosts) | Where-Object { $_ -cne $h })
            Write-CompanionLedger $ledger
        }
    }
    if (-not (Remove-CompanionTree (Get-CheckoutPath $slug))) {
        Write-Note $slug 'its source checkout holds a reparse point; left in place'
    }

    # Reverse of install step 1.
    if ($null -ne (Find-MemberCommand $cli)) {
        $r = Invoke-Native -FilePath $script:UvExe -Arguments @('tool', 'uninstall', $slug) -TimeoutSeconds $TIMEOUT_COMMAND_S
        if ($r.ExitCode -ne 0) {
            $script:Failures++
            return ('skipped: ' + (Get-FailReason 'uv tool uninstall' $r) + ' ' + (Get-Tail $r.Err))
        }
    }
    [void]$ledger.members.Remove($slug)
    Write-CompanionLedger $ledger
    return 'uninstalled'
}

# -- Lock -------------------------------------------------------------------------

function Enter-CompanionLock {
    $norm = $script:HomeReal.TrimEnd('\', '/').ToLowerInvariant()
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { $hash = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($norm)) } finally { $sha.Dispose() }
    $hex = (([System.BitConverter]::ToString($hash)) -replace '-', '').ToLowerInvariant()
    $mutex = New-Object System.Threading.Mutex($false, ('Local\skill-mesh-companions-' + $hex))
    $acquired = $false
    try { $acquired = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $acquired = $true }
    if (-not $acquired) {
        $mutex.Dispose()
        return $null
    }
    return $mutex
}

# -- Entry point --------------------------------------------------------------------

if ($Companions -ceq 'none') { exit 0 }

$homeFull = [System.IO.Path]::GetFullPath($TargetHome)
if (-not (Test-Path -LiteralPath $homeFull -PathType Container)) {
    Write-Refusal "refusing: the home '$homeFull' does not exist."
    exit 2
}
$script:HomeReal = Get-CanonicalRealPath -InputPath $homeFull

if ([string]::IsNullOrWhiteSpace($Manifest)) {
    $Manifest = Join-Path $REPO_ROOT 'config\companions.json'
}
$manifestPath = [System.IO.Path]::GetFullPath($Manifest)
$members = Read-Manifest $manifestPath
if ($null -eq $members) {
    Write-Refusal "refusing: the companion manifest '$manifestPath' is unreadable or not schema_version $MANIFEST_SCHEMA_VERSION; nothing was changed."
    exit 3
}

$rings = @('core')
if ($Companions -ceq 'all') { $rings = @('core', 'optional') }

$verb = 'install'
if ($Uninstall) { $verb = 'uninstall' }
Write-Line ("$verb -Companions $Companions (rings: " + ($rings -join ', ') + ") for $Provider in $($script:HomeReal)")

$script:UvExe = Find-Application 'uv'
$script:GitExe = Find-Application 'git'

$lock = Enter-CompanionLock
if ($null -eq $lock) {
    Write-Refusal 'refusing: another companion install or uninstall holds the lock for this home.'
    exit 4
}
try {
    if (-not $Uninstall) {
        $selected = @($members | Where-Object { $rings -contains [string](Get-Prop $_ 'ring') })
        $missing = @()
        if ($null -eq $script:UvExe) { $missing += 'uv' }
        if ($null -eq $script:GitExe) { $missing += 'git' }
        $python = Find-Python312
        if ($null -eq $python) { $missing += 'Python 3.12' }
        if ($missing.Count -gt 0) {
            foreach ($m in $selected) {
                Write-Status ([string](Get-Prop $m 'slug')) ('skipped: missing ' + ($missing -join ', '))
            }
            Write-Line ('prerequisites missing from PATH: ' + ($missing -join ', ') + '; no member was installed.')
            exit 0
        }
        $why = Test-ManifestVerified $manifestPath $python
        if ($null -ne $why) {
            Write-Refusal "refusing: the companion manifest failed tools/companions.py verify ($why); nothing was changed."
            exit 3
        }
        try {
            $ledger = Read-CompanionLedger
        } catch {
            Write-Refusal ('refusing: ' + $_.Exception.Message + '.')
            exit 3
        }
        $setupMembers = @()
        foreach ($m in $selected) {
            $slug = [string]$m.slug
            if ($null -eq (Get-Prop $m 'tag')) {
                Write-Status $slug 'skipped: unreleased'
                continue
            }
            try {
                $status = Install-Member $m $ledger
            } catch {
                $script:Failures++
                $status = 'skipped: ' + $_.Exception.Message
            }
            Write-Status $slug $status
            if ([string]$m.ring -ceq 'optional' -and
                ($status -ceq 'installed' -or $status -ceq 'already current') -and
                @(Get-Prop $m 'setup').Count -gt 0) {
                $setupMembers += $m
            }
        }
        foreach ($m in $setupMembers) {
            Write-Line ("setup for optional member $($m.slug) (printed, never run):")
            $n = 1
            foreach ($line in @($m.setup)) {
                Write-Host ("  $n. " + [string]$line)
                $n++
            }
        }
    } else {
        # The manifest's argv (setup_write.uninstall, skills.uninstaller) and repo
        # are executed here too, so they pass the same verify as on install.
        $python = Find-Python312
        if ($null -eq $python) {
            Write-Line 'Python 3.12 is missing from PATH, so the companion manifest cannot be verified; no member was uninstalled.'
            exit 0
        }
        $why = Test-ManifestVerified $manifestPath $python
        if ($null -ne $why) {
            Write-Refusal "refusing: the companion manifest failed tools/companions.py verify ($why); nothing was changed."
            exit 3
        }
        try {
            $ledger = Read-CompanionLedger
        } catch {
            Write-Refusal ('refusing: ' + $_.Exception.Message + '.')
            exit 3
        }
        $bySlug = @{}
        foreach ($m in $members) { $bySlug[[string](Get-Prop $m 'slug')] = $m }
        # Reverse manifest order; ledger members the manifest no longer lists go
        # first (with -Companions all only).
        $order = @()
        foreach ($slug in @($ledger.members.Keys | Sort-Object -Descending)) {
            if (-not $bySlug.ContainsKey($slug) -and $Companions -ceq 'all') { $order += $slug }
        }
        $reversed = @($members)
        [array]::Reverse($reversed)
        foreach ($m in $reversed) {
            if ($rings -contains [string](Get-Prop $m 'ring')) { $order += [string]$m.slug }
        }
        foreach ($slug in $order) {
            if (-not $ledger.members.Contains($slug)) {
                Write-Status $slug 'skipped: not installed by Skill Mesh'
                continue
            }
            if ($null -eq $script:UvExe -and $ledger.members[$slug].tool -ceq 'installed') {
                Write-Status $slug 'skipped: missing uv'
                continue
            }
            $member = $null
            if ($bySlug.ContainsKey($slug)) { $member = $bySlug[$slug] }
            try {
                $status = Uninstall-Member $slug $member $ledger
            } catch {
                $script:Failures++
                $status = 'skipped: ' + $_.Exception.Message
            }
            Write-Status $slug $status
        }
        Remove-EmptyCacheDirs
    }
} finally {
    try { $lock.ReleaseMutex() } finally { $lock.Dispose() }
}

if ($script:Failures -gt 0) {
    Write-Line "$($script:Failures) member(s) failed; the others were processed."
    exit 1
}
exit 0
