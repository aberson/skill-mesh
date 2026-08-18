<#
.SYNOPSIS
    probe-codex-skills.ps1 -- READ-ONLY bring-up probe for the codex profile: resolve
    $CODEX_EFFECTIVE_HOME, then report that home's .agents/skills tree and ledger state.

.DESCRIPTION
    Phase CP Step 5 (#122). Answers the two questions an operator needs before the
    first real codex install, and answers NEITHER by guessing:

      1. WHICH home is $CODEX_EFFECTIVE_HOME? Resolved ONCE, from HOME and USERPROFILE,
         with an agreement check. A disagreement REPORTS AND STOPS (exit 2) -- it never
         picks a winner, because picking one is how a profile lands in a home the host
         does not read.
      2. WHAT is in that home's codex discovery root right now? The .agents/skills tree
         (per-directory, with generated-header candidacy) and the install ledger's codex
         entry.

    IT NEVER RUNS THE CODEX CLI. Not to detect a version, not to confirm a path. This
    probe is filesystem + environment only, so it is safe to run on a machine where
    Codex is not installed and its answers do not depend on a host being present.

    READ-ONLY, WITH NO WRITE MODE AT ALL -- and that is deliberate rather than
    unfinished. Installing is already owned end-to-end by tools/install-skill-mesh.ps1
    (ledger, provenance-gated overwrite, containment re-resolution, ownership-scoped
    uninstall). A second write path here would be a duplicate implementation of
    destructive authority, which is precisely the drift class
    tools/skill-mesh-discovery.ps1 exists to prevent. To WRITE the profile:

        powershell -File tools\install-skill-mesh.ps1 -Provider codex -Home <the home
                        this probe reported> -DistDir <dist built with -Provider codex>

    Only Test-Path / Get-Item / Get-ChildItem and a bounded head-read of each file are
    used; nothing is created, moved, or deleted, and no environment variable is set.

    THE CODEX ROOT IS NOT PRIVATE TO CODEX. .agents/skills is also one of GitHub
    Copilot CLI's active discovery roots (Get-SkillMeshActiveProjectDiscoveryRoots in
    tools/skill-mesh-discovery.ps1 has listed it since before codex was installable).
    This probe therefore reports what is THERE, and never claims which host put it
    there or which hosts read it. Whether Copilot actually loads codex-profile packages
    is an M1 observation recorded in documentation/parity-deltas.md (design decision
    D-CP6); it is not decided here and no guard is pre-built for it.

    PATH DISPLAY. The resolved home IS this probe's primary answer, so it is printed --
    unlike tools/inspect-host-install.ps1, which never echoes its -Home because the home
    is that tool's input rather than its finding. It is still bounded before display
    (control characters replaced, length capped): an environment variable is
    consumer-supplied text and may carry anything. Everything BELOW the home is shown
    home-relative, and each consumer-created directory name is bounded per segment
    exactly as the inspector bounds it.

.PARAMETER Home
    Override the resolved $CODEX_EFFECTIVE_HOME with an explicit path. Alias:
    -Destination, -CodexHome. Backed by $TargetHome ($HOME is a protected PowerShell
    automatic variable and cannot be bound as a parameter).

    This is the disposable-home rehearsal switch: point it at a temp directory to
    exercise the whole probe (and the install/uninstall round trip it precedes)
    without reading or touching any real consumer home. When it is supplied, the
    HOME/USERPROFILE agreement check is still PERFORMED and REPORTED -- an override
    silences the stop, not the diagnosis -- but the override wins, and env_agreement
    then carries `overridden` so a report can never be mistaken for an unattended
    resolution.

.PARAMETER Format
    'text' (default) or 'json'.

.PARAMETER AbsolutePaths
    Show tree paths as absolute rather than home-relative. Changes DISPLAY only;
    nothing read changes. The resolved home itself is always shown.

.EXAMPLE
    powershell -File tools\probe-codex-skills.ps1
    powershell -File tools\probe-codex-skills.ps1 -Format json
    powershell -File tools\probe-codex-skills.ps1 -Home C:\tmp\rehearsal-home

.NOTES
    Exit codes: 0 the home resolved and the report is complete; 2 no report --
    resolution stopped (HOME/USERPROFILE disagreement, neither set, a non-absolute
    value, or an unusable -Home). Never prompts. Never mutates.

    ASCII-only, no BOM (PowerShell 5.1 reads a no-BOM .ps1 as ANSI/cp1252).
#>

[CmdletBinding()]
param(
    # NOT [Parameter(Mandatory)]: a mandatory parameter PROMPTS when absent in an
    # interactive host, and the whole point of this command is that the value is
    # normally RESOLVED rather than supplied.
    [Alias('Home', 'Destination', 'CodexHome')]
    [string]$TargetHome = '',

    [ValidateSet('text', 'json')]
    [string]$Format = 'text',

    [switch]$AbsolutePaths
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -- Path resolution ----------------------------------------------------------

$TOOLS_DIR = $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $TOOLS_DIR
$PROVENANCE = Join-Path $TOOLS_DIR 'skill-mesh-provenance.ps1'
$DISCOVERY = Join-Path $TOOLS_DIR 'skill-mesh-discovery.ps1'

# Shared, single-source-of-truth libraries. Dot-source with no args so only their
# functions load (Test-SkillMeshProvenance; Get-SkillMeshDiscoveryRoot).
. $PROVENANCE
. $DISCOVERY

$SCHEMA_VERSION = 1

# The codex discovery root, home-relative and POSIX-form, read from the ONE owner.
# Spelling it here would make this the fourth mirror of a shape constant that has
# already cost this repository one silent-drift incident (Step 43/44).
$CODEX_ROOT_REL = Get-SkillMeshDiscoveryRoot 'codex'
$LEDGER_NAME = '.skill-mesh-install.json'
$SHARED_DIR_NAME = '_shared'
$LEDGER_VERSION_EXPECTED = 1
$PROVIDER = 'codex'

# -- Error helper -------------------------------------------------------------

function Exit-Stop([string]$code, [string]$message) {
    # REPORT AND STOP. Structured on stderr so a disagreement is machine-readable in
    # either -Format, and exit 2 so a caller cannot mistake a stop for an empty home.
    [Console]::Error.WriteLine("probe-codex-skills: $code -- $message")
    exit 2
}

# -- Display bounding ---------------------------------------------------------

$SAFE_LABEL_MAX = 64
$SAFE_HOME_MAX = 260

function Get-SafeLabel([string]$value, [int]$max = $SAFE_LABEL_MAX) {
    # Bound ONE consumer-supplied path segment for display: the legal skill-name
    # charset, a length cap, and no separators, quotes, list commas, or control
    # characters. Mirrors Get-SafeLabel in tools/inspect-host-install.ps1 -- same
    # charset, same cap, same truncation marker -- so the two reports cannot render
    # the same directory differently.
    if ([string]::IsNullOrEmpty($value)) { return '<unnamed>' }
    $clean = [regex]::Replace($value, '[^A-Za-z0-9._-]', '_')
    if ($clean.Length -gt $max) { $clean = $clean.Substring(0, $max) + '~' }
    return $clean
}

function Get-SafeHomeDisplay([string]$value) {
    # The home is a WHOLE PATH, not a segment, so separators, a drive colon, and
    # spaces are legitimate and must survive. Everything that could corrupt a report
    # or a pasted log line does not: control characters (an env var can hold a
    # newline, which would forge an extra report line) and unbounded length.
    if ([string]::IsNullOrEmpty($value)) { return '<unset>' }
    $clean = [regex]::Replace($value, '[\x00-\x1F\x7F]', '?')
    if ($clean.Length -gt $SAFE_HOME_MAX) {
        $clean = $clean.Substring(0, $SAFE_HOME_MAX) + '~'
    }
    return $clean
}

# -- $CODEX_EFFECTIVE_HOME resolution -----------------------------------------

function Get-EnvHomeValue([string]$name) {
    # $null when unset OR set-but-blank. A blank value is not a home, and treating it
    # as one would make an empty string "agree" with nothing.
    $v = [System.Environment]::GetEnvironmentVariable($name)
    if ([string]::IsNullOrWhiteSpace($v)) { return $null }
    return $v
}

function Get-ComparableHome([string]$path) {
    # A CASE-FOLDED, separator-normalized, trailing-separator-free form for the
    # agreement comparison ONLY -- never for display and never for reading.
    #
    # LEXICAL BY DESIGN. GetFullPath does not touch the filesystem, so this comparison
    # is honest about what it is: "do these two strings name the same location". It
    # deliberately does NOT resolve junctions/symlinks, because doing so would make
    # HOME and USERPROFILE "agree" when one of them is a link an operator planted --
    # exactly the ambiguity the agreement check exists to surface. Non-existence is
    # likewise not a resolution question here.
    if ([string]::IsNullOrWhiteSpace($path)) { return $null }
    try {
        $full = [System.IO.Path]::GetFullPath($path)
    } catch {
        return $null
    }
    return $full.TrimEnd('\', '/').ToLowerInvariant()
}

function Resolve-CodexEffectiveHome([string]$override) {
    <#
      THE ONE resolver for $CODEX_EFFECTIVE_HOME. Returns
      @{ home; source; env_agreement; home_env; userprofile_env }.

      The rule, from documentation/native-claude-codex-skill-parity-plan.md section 3.2:
      the value is "resolved once from the environment inherited by the native Codex
      process. On Windows, absolute HOME and USERPROFILE must resolve to the same
      directory; a missing value uses the other, and a disagreement stops before
      mutation unless an explicit reviewed override is recorded."

      Encoded exactly, with every branch named:

        both set + equal      -> agree           -> that value          (source both)
        both set + different  -> disagree        -> STOP, exit 2
        exactly one set       -> single          -> that value          (source is that var)
        neither set           -> absent          -> STOP, exit 2
        a set value not rooted-> invalid         -> STOP, exit 2

      -Home is "the explicit reviewed override": it wins over every branch above, but
      the diagnosis is still computed and reported, so a rehearsal report always says
      that a human chose the home. It cannot be a silent bypass.
    #>
    $homeEnv = Get-EnvHomeValue 'HOME'
    $userEnv = Get-EnvHomeValue 'USERPROFILE'
    $homeCmp = Get-ComparableHome $homeEnv
    $userCmp = Get-ComparableHome $userEnv

    $agreement = 'absent'
    $resolved = $null
    $source = 'none'
    if ($null -ne $homeEnv -and $null -ne $userEnv) {
        if ($null -eq $homeCmp -or $null -eq $userCmp) {
            $agreement = 'invalid'
        } elseif ($homeCmp -ceq $userCmp) {
            $agreement = 'agree'
            $resolved = $homeEnv
            $source = 'HOME+USERPROFILE'
        } else {
            $agreement = 'disagree'
        }
    } elseif ($null -ne $homeEnv) {
        if ($null -eq $homeCmp) { $agreement = 'invalid' }
        else { $agreement = 'single'; $resolved = $homeEnv; $source = 'HOME' }
    } elseif ($null -ne $userEnv) {
        if ($null -eq $userCmp) { $agreement = 'invalid' }
        else { $agreement = 'single'; $resolved = $userEnv; $source = 'USERPROFILE' }
    }

    # A relative value is not a home. Codex inherits an absolute one; accepting a
    # relative string would silently bind the profile to whatever the current
    # directory happened to be at probe time.
    if ($null -ne $resolved -and -not [System.IO.Path]::IsPathRooted($resolved)) {
        $agreement = 'invalid'
        $resolved = $null
        $source = 'none'
    }

    if (-not [string]::IsNullOrWhiteSpace($override)) {
        return @{
            home            = $override
            source          = 'override'
            env_agreement   = 'overridden'
            env_diagnosis   = $agreement
            home_env_set    = ($null -ne $homeEnv)
            userprofile_set = ($null -ne $userEnv)
        }
    }

    # STOP BEFORE ANYTHING ELSE HAPPENS. There is no mutation in this tool to stop
    # before, and that is the point: the same resolver is what an install-bearing
    # caller must consult, so its refusals live here rather than at each call site.
    if ($agreement -eq 'disagree') {
        Exit-Stop 'HOME_DISAGREEMENT' `
            ('HOME and USERPROFILE are both set and name different directories, so ' +
             '$CODEX_EFFECTIVE_HOME is ambiguous. Nothing was read and nothing was ' +
             'written. Make them agree, or re-run with an explicit -Home <path> as ' +
             'the reviewed override. The two values are NOT echoed here.')
    }
    if ($agreement -eq 'invalid') {
        Exit-Stop 'HOME_NOT_ABSOLUTE' `
            ('HOME or USERPROFILE is set to a value that is not a usable absolute ' +
             'path, so $CODEX_EFFECTIVE_HOME cannot be resolved. The value is NOT ' +
             'echoed here. Re-run with an explicit -Home <path> to override.')
    }
    if ($agreement -eq 'absent' -or $null -eq $resolved) {
        Exit-Stop 'HOME_UNRESOLVED' `
            ('neither HOME nor USERPROFILE is set, so $CODEX_EFFECTIVE_HOME cannot ' +
             'be resolved. Re-run with an explicit -Home <path>.')
    }

    return @{
        home            = $resolved
        source          = $source
        env_agreement   = $agreement
        env_diagnosis   = $agreement
        home_env_set    = ($null -ne $homeEnv)
        userprofile_set = ($null -ne $userEnv)
    }
}

# -- Read-only helpers --------------------------------------------------------

function Read-Head([string]$absPath, [int]$maxBytes = 8192) {
    # Read only the first $maxBytes (UTF-8 decoded); the provenance header is at the
    # top (optionally after a small YAML frontmatter). READ-ONLY (OpenRead).
    $fs = [System.IO.File]::OpenRead($absPath)
    try {
        $len = [int][Math]::Min([long]$maxBytes, $fs.Length)
        if ($len -le 0) { return '' }
        $buf = New-Object byte[] $len
        $read = $fs.Read($buf, 0, $len)
        return [System.Text.Encoding]::UTF8.GetString($buf, 0, $read)
    } finally {
        $fs.Close()
    }
}

function Get-HeadTextSafe([string]$absPath) {
    if (-not (Test-Path -LiteralPath $absPath -PathType Leaf)) { return '' }
    try { return (Read-Head $absPath 8192) } catch { return '' }
}

function Test-HeadOwned([string]$headText) {
    # Generated-CANDIDATE evidence: the anchored shared parser, never a raw scan, and
    # never an authorship claim. A consumer can retain or reproduce a valid header.
    return (Test-SkillMeshProvenance $headText)
}

function Join-ProbeHomePath([string]$relPosix) {
    return (Join-Path $script:ProbeHomeAbs ($relPosix -replace '/', '\'))
}

function Format-DisplayPath([string]$absPath) {
    if ([string]::IsNullOrEmpty($absPath)) { return $null }
    $full = [System.IO.Path]::GetFullPath($absPath)
    if ($AbsolutePaths) { return (Get-SafeHomeDisplay $full) }
    $isHome = $full.Equals($script:ProbeHomeAbs, [System.StringComparison]::OrdinalIgnoreCase)
    if ($isHome) { return '.' }
    if ($full.StartsWith($script:ProbeHomeAbs + [System.IO.Path]::DirectorySeparatorChar,
            [System.StringComparison]::OrdinalIgnoreCase)) {
        $rel = $full.Substring($script:ProbeHomeAbs.Length).TrimStart('\', '/')
        return ($rel -replace '\\', '/')
    }
    return '<external>'
}

function Get-LinkInfo([string]$absDir) {
    # link_type in { directory | not-a-directory | junction | symlink | reparse |
    # absent }. READ-ONLY. A CLOSED set: whatever else the OS reports stays 'reparse'
    # rather than passing an OS-supplied string through as a new label.
    #
    # `not-a-directory` is its own label rather than folding into 'directory'. A plain
    # FILE occupying the path where a discovery directory belongs is not an
    # install-ready root, and a bare Test-Path (no -PathType) cannot tell the two
    # apart: it reports the file as present, Get-Item hands back a FileInfo with no
    # reparse attribute, and the root renders exactly like a genuine empty root.
    if (-not (Test-Path -LiteralPath $absDir)) {
        return @{ link_type = 'absent'; link_target = $null }
    }
    $item = Get-Item -LiteralPath $absDir -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0) {
        if (Test-Path -LiteralPath $absDir -PathType Container) {
            return @{ link_type = 'directory'; link_target = $null }
        }
        return @{ link_type = 'not-a-directory'; link_target = $null }
    }
    $lt = 'reparse'
    $ltMember = $item | Get-Member -Name LinkType -ErrorAction SilentlyContinue
    if ($ltMember -and $item.LinkType) {
        switch -Regex ($item.LinkType) {
            'Junction'     { $lt = 'junction' }
            'SymbolicLink' { $lt = 'symlink' }
        }
    }
    $target = $null
    $tgtMember = $item | Get-Member -Name Target -ErrorAction SilentlyContinue
    if ($tgtMember -and $item.Target) {
        $raw = @($item.Target)[0]
        if ($raw) {
            if (-not [System.IO.Path]::IsPathRooted($raw)) {
                $raw = [System.IO.Path]::Combine([System.IO.Path]::GetDirectoryName($absDir), $raw)
            }
            $shown = Format-DisplayPath $raw
            if ($AbsolutePaths -or $shown -eq '<external>' -or $shown -eq '.') {
                $target = $shown
            } else {
                $target = ((($shown -split '/') | ForEach-Object { Get-SafeLabel $_ }) -join '/')
            }
        }
    }
    return @{ link_type = $lt; link_target = $target }
}

# -- The codex discovery root -------------------------------------------------

function Get-CodexRootReport {
    # state in { absent | not-a-directory | present | home-absent }. The last is set
    # by the caller when the resolved home itself does not exist.
    $rootAbs = Join-ProbeHomePath $CODEX_ROOT_REL
    $link = Get-LinkInfo $rootAbs
    if (-not (Test-Path -LiteralPath $rootAbs)) {
        return [PSCustomObject]@{
            discovery_root = (Format-DisplayPath $rootAbs)
            state          = 'absent'
            link_type      = 'absent'
            link_target    = $null
            entry_count    = 0
            owned_count    = 0
            entries        = @()
        }
    }
    if (-not (Test-Path -LiteralPath $rootAbs -PathType Container)) {
        # A FILE (or a link to one) occupies the discovery root path. It gets its OWN
        # state because the alternative is indistinguishable from a genuine empty,
        # install-ready root: Get-ChildItem -Directory over a file path yields nothing,
        # so the report would read `state=present, link=directory, entries=0` for a
        # path no install can use. M1 is the first real-home install and this probe is
        # what the operator runs FIRST to decide whether proceeding is safe, so the two
        # must never render identically. Read-only: nothing is created or removed.
        return [PSCustomObject]@{
            discovery_root = (Format-DisplayPath $rootAbs)
            state          = 'not-a-directory'
            link_type      = $link.link_type
            link_target    = $link.link_target
            entry_count    = 0
            owned_count    = 0
            entries        = @()
        }
    }
    $entries = @()
    $owned = 0
    foreach ($dir in @(Get-ChildItem -LiteralPath $rootAbs -Force -Directory `
                -ErrorAction SilentlyContinue | Sort-Object -Property Name)) {
        $skillMd = Join-Path $dir.FullName 'SKILL.md'
        $hasSkillMd = Test-Path -LiteralPath $skillMd -PathType Leaf
        $isShared = ($dir.Name -eq $SHARED_DIR_NAME) -and (-not $hasSkillMd)
        $fileCount = 0
        $ownedFiles = 0
        foreach ($f in @(Get-ChildItem -LiteralPath $dir.FullName -Recurse -File -Force `
                    -ErrorAction SilentlyContinue)) {
            $fileCount++
            if (Test-HeadOwned (Get-HeadTextSafe $f.FullName)) { $ownedFiles++ }
        }
        # A `_shared` directory structurally has no SKILL.md, so its candidacy is
        # decided per FILE -- the same split tools/inspect-host-install.ps1 makes, for
        # the same reason: judging it by an absent SKILL.md reports a payload full of
        # marker-bearing files as unowned consumer content.
        if ($isShared) {
            $isOwned = ($ownedFiles -gt 0)
        } else {
            $isOwned = $hasSkillMd -and (Test-HeadOwned (Get-HeadTextSafe $skillMd))
        }
        if ($isOwned) { $owned++ }
        $entries += [PSCustomObject]@{
            name         = (Get-SafeLabel $dir.Name)
            kind         = $(if ($isShared) { 'shared-payload' }
                             elseif ($hasSkillMd) { 'skill' }
                             else { 'other' })
            has_skill_md = $hasSkillMd
            file_count   = $fileCount
            owned        = $isOwned
        }
    }
    return [PSCustomObject]@{
        discovery_root = (Format-DisplayPath $rootAbs)
        state          = 'present'
        link_type      = $link.link_type
        link_target    = $link.link_target
        entry_count    = @($entries).Count
        owned_count    = $owned
        entries        = @($entries)
    }
}

# -- The install ledger's codex entry -----------------------------------------

function Get-CodexLedgerReport {
    <#
      state: absent | corrupt | valid. When valid, `codex_installed` says whether the
      ledger holds a codex entry and `codex_owned_files` how many paths it claims.

      NAMES AND COUNTS ONLY -- never an owned_files path, never a hash. The ledger is
      a hand-editable file in a consumer home; echoing its payload is how
      tools/inspect-host-install.ps1 once put a real absolute path into a report (#84).
    #>
    $path = Join-ProbeHomePath $LEDGER_NAME
    $absent = [PSCustomObject]@{
        state = 'absent'; codex_installed = $false; codex_owned_files = 0
        discovery_subdir_matches_map = $null
    }
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $absent }
    try {
        $parsed = ([System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8) |
            ConvertFrom-Json)
    } catch {
        return [PSCustomObject]@{
            state = 'corrupt'; codex_installed = $false; codex_owned_files = 0
            discovery_subdir_matches_map = $null
        }
    }
    $installsProp = $parsed.PSObject.Properties['installs']
    $verProp = $parsed.PSObject.Properties['ledger_version']
    if ($null -eq $installsProp -or
        -not ($installsProp.Value -is [System.Management.Automation.PSCustomObject]) -or
        $null -eq $verProp -or
        ([string]$verProp.Value) -ne ([string]$LEDGER_VERSION_EXPECTED)) {
        return [PSCustomObject]@{
            state = 'corrupt'; codex_installed = $false; codex_owned_files = 0
            discovery_subdir_matches_map = $null
        }
    }
    $entryProp = $installsProp.Value.PSObject.Properties[$PROVIDER]
    if ($null -eq $entryProp -or $null -eq $entryProp.Value) {
        return [PSCustomObject]@{
            state = 'valid'; codex_installed = $false; codex_owned_files = 0
            discovery_subdir_matches_map = $null
        }
    }
    $entry = $entryProp.Value
    $ownedProp = $entry.PSObject.Properties['owned_files']
    $count = 0
    if ($null -ne $ownedProp -and $null -ne $ownedProp.Value) {
        $count = @($ownedProp.Value).Count
    }
    # A recorded discovery_subdir that no longer equals the map's value means the
    # ledger was written by a build whose root differed -- exactly the silent-drift
    # failure tools/skill-mesh-discovery.ps1 exists to prevent. Surfaced, not fixed:
    # this tool has no authority to rewrite a ledger.
    # NOT named $matches: that is a PowerShell automatic variable the regex operators
    # overwrite, so a later -match anywhere in scope would silently rewrite this answer.
    $subdirMatches = $null
    $subdirProp = $entry.PSObject.Properties['discovery_subdir']
    if ($null -ne $subdirProp) {
        $subdirMatches = ([string]$subdirProp.Value -ceq [string]$CODEX_ROOT_REL)
    }
    return [PSCustomObject]@{
        state = 'valid'; codex_installed = $true; codex_owned_files = $count
        discovery_subdir_matches_map = $subdirMatches
    }
}

# -- Main ---------------------------------------------------------------------

$resolution = Resolve-CodexEffectiveHome $TargetHome

try {
    $script:ProbeHomeAbs = ([System.IO.Path]::GetFullPath($resolution.home)).TrimEnd('\', '/')
} catch {
    Exit-Stop 'HOME_UNUSABLE' `
        "the resolved home is not a valid path ($($_.Exception.GetType().Name)). It is NOT echoed here."
}
if ([string]::IsNullOrWhiteSpace($script:ProbeHomeAbs)) {
    Exit-Stop 'HOME_UNUSABLE' 'the resolved home is an empty path.'
}

# NOT a stop when the home does not exist. "The home Codex would use is not there
# yet" is a legitimate, reportable pre-install state, and refusing it would make the
# probe useless on exactly the machine it is most needed on. Both sub-reports then
# take their explicit absent branch rather than enumerating a path that is not there.
$homeExists = Test-Path -LiteralPath $script:ProbeHomeAbs -PathType Container

$rootReport = $(if ($homeExists) { Get-CodexRootReport } else {
    [PSCustomObject]@{
        discovery_root = $CODEX_ROOT_REL
        state          = 'home-absent'
        link_type      = 'absent'
        link_target    = $null
        entry_count    = 0
        owned_count    = 0
        entries        = @()
    }
})
$ledgerReport = $(if ($homeExists) { Get-CodexLedgerReport } else {
    [PSCustomObject]@{
        state = 'absent'; codex_installed = $false; codex_owned_files = 0
        discovery_subdir_matches_map = $null
    }
})

# AGENTS.md is the instruction adapter Codex reads. It is reported with the SAME
# evidence vocabulary tools/inspect-host-install.ps1 uses (host-convention when
# present, unknown when absent -- never 'observed', which is reserved for a host that
# exposes runtime provenance). It is deliberately NOT correlated with the discovery
# root: instruction injection and skill discovery are separate, non-interchangeable
# mechanisms (documentation/host-discovery.md), so an AGENTS.md is neither evidence
# for nor against an installed profile.
$agentsPresent = $homeExists -and
    (Test-Path -LiteralPath (Join-ProbeHomePath 'AGENTS.md') -PathType Leaf)

$report = [PSCustomObject]@{
    schema_version   = $SCHEMA_VERSION
    provider         = $PROVIDER
    codex_home       = (Get-SafeHomeDisplay $script:ProbeHomeAbs)
    home_source      = $resolution.source
    home_exists      = $homeExists
    env_agreement    = $resolution.env_agreement
    env_diagnosis    = $resolution.env_diagnosis
    home_env_set     = $resolution.home_env_set
    userprofile_set  = $resolution.userprofile_set
    discovery_root   = $CODEX_ROOT_REL
    root             = $rootReport
    ledger           = $ledgerReport
    instruction_file = [PSCustomObject]@{
        rel_path       = 'AGENTS.md'
        present        = $agentsPresent
        evidence_class = $(if ($agentsPresent) { 'host-convention' } else { 'unknown' })
    }
    codex_cli_invoked = $false
}

if ($Format -eq 'json') {
    # -Depth 12 keeps the nested report from collapsing to System.Object[]; every
    # array-valued field is already forced to @(...) at assignment time so the JSON
    # shape is stable regardless of counts (PS 5.1 renders an empty array as "" and a
    # one-element array as a scalar otherwise).
    Write-Output ($report | ConvertTo-Json -Depth 12)
    exit 0
}

function Format-YesNo([bool]$b) { if ($b) { return 'yes' } else { return 'no' } }

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("skill-mesh codex probe (schema_version $SCHEMA_VERSION) -- READ-ONLY, codex CLI NOT invoked")
$lines.Add("codex_home: $($report.codex_home)")
$lines.Add("  source=$($report.home_source) env_agreement=$($report.env_agreement) exists=$(Format-YesNo $report.home_exists)")
$lines.Add("  HOME set=$(Format-YesNo $report.home_env_set)  USERPROFILE set=$(Format-YesNo $report.userprofile_set)")
$lines.Add('')
$lines.Add("codex discovery root ($($report.root.discovery_root)): state=$($report.root.state) link=$($report.root.link_type)")
if ($null -ne $report.root.link_target) { $lines.Add("  link_target: $($report.root.link_target)") }
$lines.Add("  entries=$($report.root.entry_count) generated-header candidates=$($report.root.owned_count)")
foreach ($e in @($report.root.entries)) {
    $lines.Add("    - $($e.name): $($e.kind) (files=$($e.file_count), owned=$(Format-YesNo $e.owned))")
}
$lines.Add('')
$lines.Add("ledger ($LEDGER_NAME): state=$($report.ledger.state) codex_installed=$(Format-YesNo $report.ledger.codex_installed) owned_files=$($report.ledger.codex_owned_files)")
if ($false -eq $report.ledger.discovery_subdir_matches_map) {
    $lines.Add("  WARNING: the ledger's recorded codex discovery_subdir does not match $CODEX_ROOT_REL.")
}
$lines.Add("instruction file: $($report.instruction_file.rel_path): present=$(Format-YesNo $report.instruction_file.present) [$($report.instruction_file.evidence_class)]")

Write-Output ($lines -join [Environment]::NewLine)
exit 0
