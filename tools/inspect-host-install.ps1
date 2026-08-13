<#
.SYNOPSIS
    inspect-host-install.ps1 -- a READ-ONLY preflight that reports a consumer
    home's skill-mesh install state, as a human report OR a stable JSON document.

.DESCRIPTION
    Answers "what is installed in this home, and is it ours?" WITHOUT mutating,
    prompting, authenticating, or contacting any network service. It only reads:
    Test-Path / Get-Item / Get-ChildItem and a bounded head-read of each SKILL.md.

    It reports:
      - root instruction files (CLAUDE.md / AGENTS.md) with an evidence class
        (host-convention when present, unknown when absent -- NEVER 'observed',
        which is reserved for a host that exposes runtime provenance);
      - the Claude discovery root (.claude/skills) and the GPT discovery root
        (.github/skills), each with its state, link type/target, and a per-skill
        eligibility classification cross-referenced against config/skill-manifest.json;
      - the RETIRED project-relative .copilot/skills wrong-target (flagged when
        present -- a leftover from a pre-Step-44 GPT install);
      - the legacy .claude/skills-gpt tree (classified per-skill too, so a
        consumer-only skill mirrored there is never mistaken for managed);
      - provenance ownership counts (owned vs foreign) per root;
      - the install ledger state (absent | valid | corrupt; provider names only);
      - the router path, version, and classification (canonical | legacy | absent).

    GENERATED-CANDIDATE EVIDENCE = FILE-CONTENT PROVENANCE. The report's stable
    `owned` field means the bounded file head matches an emitter-valid generated-header
    shape. It does not mean the inspector consulted the ledger, and it proves neither
    current-byte authorship nor that the bytes were not later edited. The field is
    computed by the shared, anchored marker parser (Test-SkillMeshProvenance from
    tools/skill-mesh-provenance.ps1) applied to each file's head -- never the
    mutable ledger, and never a substring-anywhere scan. This inspector REUSES that
    parser; it does not fork it.

    CLASSIFICATION (manifest-driven; absence from the manifest is the SOLE
    criterion for consumer-only):
      managed       -- the skill dir name IS a record in config/skill-manifest.json.
      consumer-only -- a SKILL.md-shaped tree whose name is NOT in the manifest
                       (classified per root; a .claude/skills twin never makes a
                       .github/skills or .claude/skills-gpt entry "managed").
      shared-payload -- a `_shared` directory (no SKILL.md) holding at least one
                       emitter-valid generated-header candidate. This is the stable
                       payload-shaped classification; `owned` is decided PER FILE
                       from header shape, not from a SKILL.md it structurally cannot
                       have, and is not an authorship claim.
      core-holder   -- a `_shared` directory inside a discovery root, no SKILL.md,
                       and no marker-bearing file: purely consumer-held.
      foreign       -- anything else (no manifest record, no SKILL.md, not _shared).

    WHY `_shared` NEEDS ITS OWN REPORTING RULE. Every other class decides `owned`
    from its SKILL.md head, and a `_shared` directory has no SKILL.md -- so before
    this rule it reported `owned=false` unconditionally, which after the payload
    shipped meant reporting a directory full of generated-looking marker-bearing files
    as unowned consumer content. It never surfaced as a failure anywhere, because
    nothing is classed foreign and unowned_count stays 0; it had to be fixed
    deliberately. Its header-shape parser mirrors migrate-legacy-install.ps1's
    Get-DirEligibility + Test-SharedFileIsOurs. In the migrator, a match can contribute
    to destructive retirement only for a candidate resident under the retired
    project-root tree and only with independent plan/path/hash/state guards. Active-root
    matches are advisory and retained; this report is never standalone mutation authority.

    unowned_count is deliberately NOT extended to `_shared`. It counts SKILL.md-shaped
    trees at managed-shaped paths that lack generated-header-candidate evidence -- the
    "a host may load this but its header is not one our emitters produce" signal. A
    consumer's own `_shared/README.md` is neither header-shaped nor loadable as a skill,
    so counting it would turn a clean home into a dirty report.

    PATH DISPLAY. Default output is consumer-home-RELATIVE (consumer_home = '.').
    -AbsolutePaths switches DISPLAY to absolute; it changes nothing that is read.
    A link target outside the home is shown as the sentinel '<external>' in
    relative mode (never a leaked absolute path), and as its real absolute path
    only when -AbsolutePaths is given.

    NEVER emits secret values or file contents -- only presence classes, counts,
    provider names, and stable classification labels.

    OUTPUT SANITATION. Every scalar in the report is one of two classes.
      CLOSED VOCABULARY -- provider slugs (from the manifest's `providers` object),
        manifest skill names, classification labels, warning codes. A value outside
        its vocabulary is DROPPED and counted, never echoed; a value INSIDE it is
        emitted as the manifest's OWN slug, never the consumer's spelling of it
        (a provider match is ordinal and case-insensitive, so a legitimate
        `-Provider CLAUDE` install is recognized and normalized rather than dropped,
        while a culture-equal lookalike padded with ignorable characters is not
        admitted at all). This covers the two
        channels that could carry arbitrary bytes: install-ledger keys (free-form
        text in a hand-editable file, proven able to carry an absolute path) and the
        `Profile:` header token (whose charset happily spells a credential).
      CONSUMER PATH TEXT -- skill directory names and link targets. These are
        in-contract (naming what is installed is the report's job) but are bounded
        per segment to the skill-name charset and a length cap, so a hostile or
        hand-edited home cannot inject separators, list commas, control characters,
        or a 255-character name into the report.
    The raw -Home value and this checkout's absolute manifest path are never echoed,
    on stdout or stderr -- an invalid -Home is reported without quoting it back.

    EXPLICIT NON-GOAL: a skill DIRECTORY NAME is reported (bounded, per above), not
    withheld. Naming what is installed is the report's entire purpose, so a consumer
    who names a directory after a credential will see that name in the report. The
    guarantee is that no name can carry an absolute path, exceed its cap, or inject
    separators/control characters -- not that path text is suppressed.

    -Home is REQUIRED. Exit 0 on success; nonzero (2) when -Home is missing,
    unreadable, or not a directory. The command NEVER prompts.

    ASCII-only, no BOM (PowerShell 5.1 reads a no-BOM .ps1 as ANSI/cp1252).
#>

[CmdletBinding()]
param(
    # NOT [Parameter(Mandatory)] on purpose: a mandatory param PROMPTS when absent
    # in an interactive host, and this command must NEVER prompt. Missing -Home is
    # validated manually below and exits 2.
    [Alias('Home', 'Destination')]
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
$MANIFEST_REL = 'config/skill-manifest.json'
$MANIFEST_PATH = Join-Path $REPO_ROOT 'config\skill-manifest.json'

# Shared, single-source-of-truth provenance parser (Test-SkillMeshProvenance).
# Dot-source with no args so only its functions load.
. $PROVENANCE
# Shared, single-source-of-truth discovery-root map. These paths used to be
# hand-mirrored here from the installer; that duplicate-shape-constant now has ONE
# owner (see tools/skill-mesh-discovery.ps1 for the rationale).
. $DISCOVERY

# HostInstallReport v2 adds `shared-payload` to the closed eligibility vocabulary
# and lets a generated-header-candidate `_shared` entry contribute one to `owned_count`. Both
# are parser-visible semantic changes from the four-value/count behavior shipped
# in v1, even though the JSON object shape itself is unchanged.
$SCHEMA_VERSION = 2

# Discovery roots (home-relative, POSIX form) and the legacy/retired resolution
# shadows, all read from the shared owner rather than re-spelled.
$CLAUDE_ROOT_REL = Get-SkillMeshDiscoveryRoot 'claude'
$GPT_ROOT_REL = Get-SkillMeshDiscoveryRoot 'gpt'
$LEGACY_SKILLS_GPT_REL = Get-SkillMeshLegacySkillsGptRoot
$RETIRED_COPILOT_REL = Get-SkillMeshRetiredCopilotRoot
$LEDGER_NAME = '.skill-mesh-install.json'
# The shared support payload directory the builder emits at each profile root, as a
# sibling of the per-skill dirs. Same spelling as migrate-legacy-install.ps1's
# $SHARED_DIR_NAME and tools/build-distributions.ps1's $SHARED_DEST.
$SHARED_DIR_NAME = '_shared'
$LEGACY_ROUTER_REL = '.claude/lib/skill-router.ps1'
$CANONICAL_ROUTER_REL = 'runtime/skill-router.ps1'
$LEDGER_VERSION_EXPECTED = 1

# -- Error helper -------------------------------------------------------------

function Exit-Invalid([string]$message) {
    [Console]::Error.WriteLine("inspect-host-install: $message")
    exit 2
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
    # Generated-candidate evidence: the anchored shared parser (never a raw scan).
    return (Test-SkillMeshProvenance $headText)
}

# -- Output sanitation --------------------------------------------------------

$SAFE_LABEL_MAX = 64

function Get-SafeLabel([string]$value, [int]$max = $SAFE_LABEL_MAX) {
    # Bound ONE consumer-supplied path segment for display: the legal skill-name
    # charset, a length cap, and no separators, quotes, list commas, or control
    # characters. Replacement (not redaction) keeps a real consumer-only skill
    # identifiable while making the segment unable to corrupt the report. Mirrors
    # the Get-SanitizedSessionId idiom in runtime/skill-router.ps1.
    if ([string]::IsNullOrEmpty($value)) { return '<unnamed>' }
    $clean = [regex]::Replace($value, '[^A-Za-z0-9._-]', '_')
    if ($clean.Length -gt $max) { $clean = $clean.Substring(0, $max) + '~' }
    return $clean
}

function Resolve-KnownProvider([string]$value) {
    # Delegates to the SHARED normalizer in tools/skill-mesh-discovery.ps1, which
    # now owns provider-slug resolution for the installer, this inspector, and the
    # migrator. The semantics are unchanged and still test-locked: ordinal but
    # case-insensitive matching, returning the manifest's OWN slug, so a legitimate
    # `-Provider CLAUDE` install is recognized and normalized while a culture-equal
    # lookalike padded with ignorable characters is refused outright.
    return (Resolve-SkillMeshProvider $value $script:KnownProviders)
}

function Get-ProfileHeaderTag([string]$headText) {
    # The generated provenance header carries a `Profile: <profile>` line. Only a
    # value the manifest DECLARES as a provider is returned: build-distributions.ps1
    # is the supported emitter of this line, while a retained or reproduced header can
    # contain any token. Treat values outside the closed provider vocabulary as untrusted
    # and withhold them -- the token charset [A-Za-z0-9_-] spells most credential shapes
    # verbatim. Get-SkillMeshHeaderBlock returns ONLY the exact
    # validated header span from the shared ownership parser. This excludes decoys
    # before its opener, below a merely opener-shaped string, and -- load-bearing --
    # body text after the validated block's `-->` terminator.
    if ([string]::IsNullOrEmpty($headText)) { return $null }
    $header = Get-SkillMeshHeaderBlock $headText
    if ([string]::IsNullOrEmpty($header)) { return $null }
    $m = [regex]::Match($header, '(?m)^[ \t]*Profile:[ \t]*([A-Za-z0-9_-]+)[ \t]*\r?$')
    if (-not $m.Success) { return $null }
    return (Resolve-KnownProvider $m.Groups[1].Value)
}

# -- Path display -------------------------------------------------------------

function Format-DisplayPath([string]$absPath) {
    # Home-relative by default; absolute only under -AbsolutePaths. A path outside
    # the home becomes '<external>' in relative mode (never a leaked absolute path).
    if ([string]::IsNullOrEmpty($absPath)) { return $null }
    $full = [System.IO.Path]::GetFullPath($absPath)
    $isHome = $full.Equals($script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase)
    $underHome = $isHome -or $full.StartsWith(
        $script:HomeAbs + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase)
    if ($AbsolutePaths) { return $full }
    if ($underHome) {
        if ($isHome) { return '.' }
        $rel = $full.Substring($script:HomeAbs.Length).TrimStart('\', '/')
        return ($rel -replace '\\', '/')
    }
    return '<external>'
}

function Format-LinkTargetPath([string]$absPath) {
    # A link target's RELATIVE rendering is composed of consumer directory names, so
    # each segment is bounded before display. (discovery_root and rel_path are built
    # from this script's own root constants plus an already-bounded skill name, so
    # they need no second pass.) '<external>' still covers any target outside the
    # home, and -AbsolutePaths still shows the real path verbatim.
    $shown = Format-DisplayPath $absPath
    if ([string]::IsNullOrEmpty($shown)) { return $shown }
    if ($AbsolutePaths -or $shown -eq '<external>' -or $shown -eq '.') { return $shown }
    return ((($shown -split '/') | ForEach-Object { Get-SafeLabel $_ }) -join '/')
}

function Join-HomePath([string]$relPosix) {
    return (Join-Path $script:HomeAbs ($relPosix -replace '/', '\'))
}

# -- Link type ----------------------------------------------------------------

function Get-LinkInfo([string]$absDir) {
    # Returns @{ link_type; link_target }. link_type in
    # { directory | junction | symlink | reparse | absent }. READ-ONLY.
    if (-not (Test-Path -LiteralPath $absDir)) {
        return @{ link_type = 'absent'; link_target = $null }
    }
    $item = Get-Item -LiteralPath $absDir -Force
    $isReparse = [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
    if (-not $isReparse) {
        return @{ link_type = 'directory'; link_target = $null }
    }
    # link_type is a CLOSED set: directory | junction | symlink | reparse | absent.
    # Anything else the OS reports (a mount point, an AppExeCLink) stays 'reparse'
    # rather than passing an OS-supplied string through as a new label.
    $lt = 'reparse'
    $ltMember = $item | Get-Member -Name LinkType -ErrorAction SilentlyContinue
    if ($ltMember -and $item.LinkType) {
        switch -Regex ($item.LinkType) {
            'Junction'     { $lt = 'junction' }
            'SymbolicLink' { $lt = 'symlink' }
        }
    }
    $targetDisplay = $null
    $tgtMember = $item | Get-Member -Name Target -ErrorAction SilentlyContinue
    if ($tgtMember -and $item.Target) {
        $rawTarget = @($item.Target)[0]
        if ($rawTarget) {
            if (-not [System.IO.Path]::IsPathRooted($rawTarget)) {
                $parent = [System.IO.Path]::GetDirectoryName($absDir)
                $rawTarget = [System.IO.Path]::Combine($parent, $rawTarget)
            }
            $targetDisplay = Format-LinkTargetPath $rawTarget
        }
    }
    return @{ link_type = $lt; link_target = $targetDisplay }
}

# -- Manifest -----------------------------------------------------------------

function Read-Manifest {
    # Returns @{ skills = <name -> @{ status; single_profile }>; providers = <slugs> }.
    # `providers` is the CLOSED vocabulary every provider-slug check validates
    # against, read from the manifest's own top-level `providers` object rather than
    # duplicated here -- so a provider added in a later phase is honored without
    # editing this tool (a hardcoded {claude, gpt} would silently report zero
    # providers for a new lane, a false-clean preflight). Missing/unparseable
    # manifest is a hard input error (the inspector cannot classify without it).
    # Diagnostics name the repo-RELATIVE manifest path: this checkout's absolute
    # path is never echoed, not even on stderr.
    if (-not (Test-Path -LiteralPath $MANIFEST_PATH -PathType Leaf)) {
        Exit-Invalid "manifest not found at $MANIFEST_REL (relative to the skill-mesh checkout)"
    }
    try {
        $raw = [System.IO.File]::ReadAllText($MANIFEST_PATH, [System.Text.Encoding]::UTF8)
        $parsed = $raw | ConvertFrom-Json
    } catch {
        Exit-Invalid "$MANIFEST_REL is unparseable ($($_.Exception.GetType().Name))"
    }
    $map = @{}
    foreach ($s in @($parsed.skills)) {
        $name = [string]$s.name
        if ([string]::IsNullOrWhiteSpace($name)) { continue }
        $status = [string]$s.status
        $coreProp = $s.PSObject.Properties['core']
        $coreNull = ($null -eq $coreProp) -or ($null -eq $coreProp.Value)
        $single = ($status -eq 'provider-native') -or $coreNull
        $map[$name] = @{ status = $status; single_profile = $single }
    }
    $providers = @()
    $provProp = $parsed.PSObject.Properties['providers']
    if ($null -ne $provProp -and $null -ne $provProp.Value) {
        $providers = @($provProp.Value.PSObject.Properties | ForEach-Object { $_.Name } | Sort-Object)
    }
    if ($providers.Count -eq 0) {
        Exit-Invalid "$MANIFEST_REL declares no providers; provider slugs cannot be validated"
    }
    return @{ skills = $map; providers = @($providers) }
}

# -- Per-root skill classification --------------------------------------------

function Get-RootAnalysis([string]$rootRel) {
    # Analyze one discovery-root-shaped tree (claude, gpt, or legacy skills-gpt).
    # Returns a profile-shaped PSCustomObject. Purely READ-ONLY.
    $rootAbs = Join-HomePath $rootRel
    $link = Get-LinkInfo $rootAbs

    if (-not (Test-Path -LiteralPath $rootAbs)) {
        return [PSCustomObject]@{
            discovery_root = (Format-DisplayPath $rootAbs)
            state          = 'absent'
            link_type      = 'absent'
            link_target    = $null
            owned_count    = 0
            unowned_count  = 0
            skills         = @()
            adapter_sample = $null
        }
    }

    $entries = @()
    $ownedCount = 0
    $unownedCount = 0
    $adapterSample = $null

    $childDirs = @(Get-ChildItem -LiteralPath $rootAbs -Force -Directory -ErrorAction SilentlyContinue |
        Sort-Object -Property Name)
    foreach ($dir in $childDirs) {
        $name = $dir.Name
        $skillMd = Join-Path $dir.FullName 'SKILL.md'
        $hasSkillMd = Test-Path -LiteralPath $skillMd -PathType Leaf
        $head = if ($hasSkillMd) { Get-HeadTextSafe $skillMd } else { '' }
        $owned = $hasSkillMd -and (Test-HeadOwned $head)

        # PER-FILE generated-candidate classification for the shared payload. A `_shared` directory has no
        # SKILL.md, so the line above can only ever answer "not owned" for it -- which
        # is a misreport once the builder ships marker-bearing assets there. Scoped to
        # the `_shared` name and to a SKILL.md-less directory so no other class changes
        # its reporting rule, and read through the SAME anchored parser.
        #
        # `owned` is a generated-candidate signal downstream automation may inspect, so
        # this loop is only ever as honest as that parser: a content-quoting operator
        # file counted here would misclassify consumer bytes as payload-shaped. In
        # migrate-legacy-install.ps1 the same match can participate in a destructive
        # retire only when the candidate resides under the retired project-root tree and
        # independent plan/path/hash/state guards also pass. Active-root matches are
        # advisory and retained. The position + adjacency anchors prevent the quoted-
        # header false positive; they do not prove authorship.
        $isSharedDir = ($name -eq $SHARED_DIR_NAME) -and (-not $hasSkillMd)
        $sharedOwnedFiles = 0
        if ($isSharedDir) {
            foreach ($f in @(Get-ChildItem -LiteralPath $dir.FullName -Recurse -File -Force `
                        -ErrorAction SilentlyContinue)) {
                if (Test-HeadOwned (Get-HeadTextSafe $f.FullName)) { $sharedOwnedFiles++ }
            }
            $owned = ($sharedOwnedFiles -gt 0)
        }

        $inManifest = $script:ManifestMap.ContainsKey($name)
        $manifestStatus = $null
        $singleProfile = $false
        if ($inManifest) {
            $manifestStatus = $script:ManifestMap[$name].status
            $singleProfile = $script:ManifestMap[$name].single_profile
        }

        if ($inManifest) {
            $eligibility = 'managed'
        } elseif ($isSharedDir) {
            # Split PER FILE, not per directory: a `_shared` holding one or more
            # emitter-valid generated-header candidates is a shared-payload root;
            # one holding only the
            # consumer's own files is still the legacy core-holder and stays
            # preserved. The old unconditional 'core-holder' verdict reported the
            # first case as the second.
            $eligibility = $(if ($sharedOwnedFiles -gt 0) { 'shared-payload' } else { 'core-holder' })
        } elseif ($hasSkillMd) {
            $eligibility = 'consumer-only'
        } else {
            $eligibility = 'foreign'
        }

        if ($owned) { $ownedCount++ }
        elseif ($hasSkillMd) { $unownedCount++ }

        # A manifest name is already a closed-vocabulary value; anything else is a
        # consumer-created directory name and is bounded before it reaches output.
        $safeName = if ($inManifest) { $name } else { Get-SafeLabel $name }

        if ($null -eq $adapterSample -and $eligibility -eq 'managed' -and $owned) {
            $tag = Get-ProfileHeaderTag $head
            if ([string]::IsNullOrEmpty($tag)) { $tag = 'unknown' }
            $adapterSample = [PSCustomObject]@{ skill = $safeName; profile_header = $tag }
        }

        $entries += [PSCustomObject]@{
            name            = $safeName
            # Composed from this script's root constant plus the bounded name, so
            # rel_path can never diverge from the name it describes.
            rel_path        = $(if ($AbsolutePaths) { Format-DisplayPath $dir.FullName } else { "$rootRel/$safeName" })
            eligibility     = $eligibility
            has_skill_md    = $hasSkillMd
            owned           = $owned
            manifest_status = $manifestStatus
            single_profile  = $singleProfile
        }
    }

    return [PSCustomObject]@{
        discovery_root = (Format-DisplayPath $rootAbs)
        state          = 'present'
        link_type      = $link.link_type
        link_target    = $link.link_target
        owned_count    = $ownedCount
        unowned_count  = $unownedCount
        skills         = @($entries)
        adapter_sample = $adapterSample
    }
}

# -- Instruction files --------------------------------------------------------

function Get-InstructionFiles {
    $out = @()
    foreach ($rel in @('CLAUDE.md', 'AGENTS.md')) {
        $abs = Join-HomePath $rel
        $present = Test-Path -LiteralPath $abs -PathType Leaf
        # Runtime-provenance rule (plan section 7): this inspector never learns which
        # instruction file a host actually LOADED -- it only runs Test-Path -- so it
        # NEVER claims 'observed'. 'observed' is reserved for a host that exposes
        # runtime provenance. A file present at a documented convention path is
        # 'host-convention'; an absent one is 'unknown'.
        $evidence = if ($present) { 'host-convention' } else { 'unknown' }
        $out += [PSCustomObject]@{
            rel_path       = $rel
            present        = $present
            evidence_class = $evidence
        }
    }
    return @($out)
}

# -- Ledger (read-only mirror of install-skill-mesh Read-Ledger) --------------

function Get-LedgerState {
    $path = Join-HomePath $LEDGER_NAME
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        return [PSCustomObject]@{ state = 'absent'; providers = @(); unrecognized_provider_count = 0 }
    }
    try {
        $raw = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
        $parsed = $raw | ConvertFrom-Json
    } catch {
        return [PSCustomObject]@{ state = 'corrupt'; providers = @(); unrecognized_provider_count = 0 }
    }
    $installsProp = $parsed.PSObject.Properties['installs']
    if ($null -eq $installsProp -or
        -not ($installsProp.Value -is [System.Management.Automation.PSCustomObject])) {
        return [PSCustomObject]@{ state = 'corrupt'; providers = @(); unrecognized_provider_count = 0 }
    }
    $verProp = $parsed.PSObject.Properties['ledger_version']
    if ($null -eq $verProp -or ([string]$verProp.Value) -ne ([string]$LEDGER_VERSION_EXPECTED)) {
        return [PSCustomObject]@{ state = 'corrupt'; providers = @(); unrecognized_provider_count = 0 }
    }
    # Provider NAMES only -- never any owned_files / created_dirs payload -- AND only
    # names the manifest declares. An `installs` key is written solely from the
    # installer's ValidateSet-bound -Provider, so a key outside that vocabulary is
    # hand-edited or hostile; echoing keys verbatim put a real absolute path into the
    # default report (#84). Unrecognized keys are counted, never printed.
    $allKeys = @($installsProp.Value.PSObject.Properties | ForEach-Object { $_.Name })
    $resolved = @($allKeys | ForEach-Object { Resolve-KnownProvider $_ })
    # The CANONICAL slug is emitted, never the ledger's spelling of it.
    $providers = @($resolved | Where-Object { $null -ne $_ } | Sort-Object -Unique)
    $unrecognized = @($resolved | Where-Object { $null -eq $_ }).Count
    return [PSCustomObject]@{
        state                       = 'valid'
        providers                   = @($providers)
        unrecognized_provider_count = $unrecognized
    }
}

# -- Router -------------------------------------------------------------------

function Get-RouterInfo {
    $canonicalAbs = Join-HomePath $CANONICAL_ROUTER_REL
    $legacyAbs = Join-HomePath $LEGACY_ROUTER_REL
    $found = $null
    $classification = 'absent'
    if (Test-Path -LiteralPath $canonicalAbs -PathType Leaf) {
        $found = $canonicalAbs
        $classification = 'canonical'
    } elseif (Test-Path -LiteralPath $legacyAbs -PathType Leaf) {
        $found = $legacyAbs
        $classification = 'legacy'
    }
    $version = $null
    $relPath = $null
    if ($null -ne $found) {
        $relPath = Format-DisplayPath $found
        $head = Get-HeadTextSafe $found
        $m = [regex]::Match($head, '\$ROUTER_VERSION\s*=\s*''([^'']+)''')
        # \A..\z, not ^..$: in .NET '$' also matches BEFORE a trailing newline, so a
        # version ending in LF passed the old gate and split the text report onto two
        # lines. [0-9], not \d, so Unicode digits cannot pass. {1,4} caps the length.
        if ($m.Success -and ($m.Groups[1].Value -match '\A[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}\z')) {
            $version = $m.Groups[1].Value
        }
    }
    return [PSCustomObject]@{
        rel_path       = $relPath
        version        = $version
        classification = $classification
    }
}

# -- Main ---------------------------------------------------------------------

# -- Validate -Home (never prompt; exit 2 on any invalid input) --
if ([string]::IsNullOrWhiteSpace($TargetHome)) {
    Exit-Invalid "-Home is required (path to the consumer home to inspect)."
}
# The -Home value is NEVER quoted back. It is an absolute path by construction and
# may carry newlines or control characters, so echoing it wrote an attacker- or
# accident-shaped line into stderr -- a stream a caller may fold into a pasted
# report. The caller just supplied the value, so repeating it adds nothing.
try {
    $script:HomeAbs = ([System.IO.Path]::GetFullPath($TargetHome)).TrimEnd('\', '/')
} catch {
    Exit-Invalid "-Home is not a valid path ($($_.Exception.GetType().Name))."
}
if ([string]::IsNullOrWhiteSpace($script:HomeAbs)) {
    Exit-Invalid "-Home resolves to an empty path."
}
if (-not (Test-Path -LiteralPath $script:HomeAbs)) {
    Exit-Invalid "-Home does not exist."
}
if (-not (Test-Path -LiteralPath $script:HomeAbs -PathType Container)) {
    Exit-Invalid "-Home is not a directory."
}

$manifest = Read-Manifest
$script:ManifestMap = $manifest.skills
$script:KnownProviders = @($manifest.providers)

# -- Gather --
$instructionFiles = Get-InstructionFiles
$claudeProfile = Get-RootAnalysis $CLAUDE_ROOT_REL
$gptProfile = Get-RootAnalysis $GPT_ROOT_REL
$legacySkillsGpt = Get-RootAnalysis $LEGACY_SKILLS_GPT_REL
$ledger = Get-LedgerState
$router = Get-RouterInfo

# -- Legacy shadows (present-only, relative paths) --
$legacyShadows = @()
foreach ($rel in @($LEGACY_SKILLS_GPT_REL, $RETIRED_COPILOT_REL)) {
    if (Test-Path -LiteralPath (Join-HomePath $rel)) { $legacyShadows += $rel }
}
$legacyShadows = @($legacyShadows | Sort-Object)

# -- Warnings (stable UPPER_SNAKE codes; no secrets, no file contents) --
$warnings = @()
function Add-Warning([string]$code, [string]$message) {
    $script:warnings += [PSCustomObject]@{ code = $code; message = $message }
}

function Format-NameList($names, [int]$cap = 10, [int]$maxChars = 400) {
    # Bound every name before joining: an unbounded name would otherwise put ~2.5 KB
    # of consumer bytes into one warning, and a name containing this function's own
    # ', ' separator would render indistinguishably from two names. The count cap
    # alone did neither.
    $arr = @(@($names | ForEach-Object { Get-SafeLabel ([string]$_) }) | Sort-Object -Unique)
    if ($arr.Count -eq 0) { return '' }
    if ($arr.Count -gt $cap) {
        $text = (($arr[0..($cap - 1)] -join ', ') + ", ... (+$($arr.Count - $cap) more)")
    } else {
        $text = ($arr -join ', ')
    }
    if ($text.Length -gt $maxChars) { $text = $text.Substring(0, $maxChars) + ' ...' }
    return $text
}

if (Test-Path -LiteralPath (Join-HomePath $RETIRED_COPILOT_REL)) {
    Add-Warning 'RETIRED_COPILOT_TARGET_PRESENT' `
        "$RETIRED_COPILOT_REL is present -- a retired project-relative GPT target (Copilot does not discover it); likely a pre-retarget install."
}
if (Test-Path -LiteralPath (Join-HomePath $LEGACY_SKILLS_GPT_REL)) {
    Add-Warning 'LEGACY_CLAUDE_SKILLS_GPT_PRESENT' `
        "$LEGACY_SKILLS_GPT_REL is present -- a legacy GPT core tree that can still shadow resolution."
}

# Foreign content at MANAGED skill paths (a hand-authored / non-marker SKILL.md
# occupying a manifest-name directory) -- distinct from a legitimate consumer-only
# tree. Reported per root.
foreach ($p in @(
    @{ prof = $claudeProfile; root = $CLAUDE_ROOT_REL },
    @{ prof = $gptProfile; root = $GPT_ROOT_REL },
    @{ prof = $legacySkillsGpt; root = $LEGACY_SKILLS_GPT_REL })) {
    $unownedManaged = @($p.prof.skills |
        Where-Object { $_.eligibility -eq 'managed' -and $_.has_skill_md -and (-not $_.owned) } |
        ForEach-Object { $_.name })
    if ($unownedManaged.Count -gt 0) {
        Add-Warning 'MANAGED_PATH_UNOWNED' `
            "$($p.root): $($unownedManaged.Count) managed-name skill(s) have a non-skill-mesh (foreign) SKILL.md: $(Format-NameList $unownedManaged)"
    }
}

# Consumer-only trees present (legitimate, but surfaced so a preflight is complete).
$consumerOnly = @()
foreach ($p in @($claudeProfile, $gptProfile, $legacySkillsGpt)) {
    $consumerOnly += @($p.skills | Where-Object { $_.eligibility -eq 'consumer-only' } | ForEach-Object { $_.name })
}
$consumerOnly = @($consumerOnly | Sort-Object -Unique)
if ($consumerOnly.Count -gt 0) {
    Add-Warning 'CONSUMER_ONLY_PRESENT' `
        "$($consumerOnly.Count) consumer-only (unmanifested) skill(s) present: $(Format-NameList $consumerOnly)"
}

# A discovery root that is a junction (informational -- resolution follows it).
foreach ($p in @(
    @{ prof = $claudeProfile; root = $CLAUDE_ROOT_REL },
    @{ prof = $gptProfile; root = $GPT_ROOT_REL })) {
    if ($p.prof.link_type -eq 'junction') {
        Add-Warning 'DISCOVERY_ROOT_JUNCTION' "$($p.root) is a Windows junction (resolution follows the link target)."
    }
}

# Portable managed skills present under .claude/skills but absent from .github/skills.
# The provider-native (single-profile) carve-out: those legitimately have no GPT
# profile, so they are NEVER flagged here.
$gptManagedNames = @{}
foreach ($e in @($gptProfile.skills)) {
    if ($e.eligibility -eq 'managed') { $gptManagedNames[$e.name] = $true }
}
$missingGpt = @($claudeProfile.skills |
    Where-Object {
        $_.eligibility -eq 'managed' -and
        $_.manifest_status -eq 'portable' -and
        (-not $_.single_profile) -and
        (-not $gptManagedNames.ContainsKey($_.name))
    } | ForEach-Object { $_.name })
if ($missingGpt.Count -gt 0) {
    Add-Warning 'MANAGED_SKILL_MISSING_GPT_PROFILE' `
        "$($missingGpt.Count) portable managed skill(s) under $CLAUDE_ROOT_REL have no $GPT_ROOT_REL counterpart: $(Format-NameList $missingGpt)"
}

if ($ledger.state -eq 'corrupt') {
    Add-Warning 'LEDGER_CORRUPT' "the install ledger ($LEDGER_NAME) is unparseable or an unknown schema; ownership tracking is lost."
}
if ($ledger.state -eq 'valid' -and $ledger.unrecognized_provider_count -gt 0) {
    Add-Warning 'LEDGER_UNKNOWN_PROVIDER' `
        "the install ledger names $($ledger.unrecognized_provider_count) install key(s) that are not declared providers; the key names are withheld from this report."
}
if ($router.classification -eq 'legacy') {
    Add-Warning 'ROUTER_LEGACY' "the router at $($router.rel_path) is the legacy path ($LEGACY_ROUTER_REL); the canonical router is $CANONICAL_ROUTER_REL."
}

$warnings = @($warnings | Sort-Object -Property code, message)

# -- Assemble report --
$report = [PSCustomObject]@{
    schema_version    = $SCHEMA_VERSION
    consumer_home     = $(if ($AbsolutePaths) { $script:HomeAbs } else { '.' })
    instruction_files = @($instructionFiles)
    profiles          = [PSCustomObject]@{
        claude = $claudeProfile
        gpt    = $gptProfile
    }
    legacy_skills_gpt = $legacySkillsGpt
    ledger            = $ledger
    router            = $router
    legacy_shadows    = @($legacyShadows)
    warnings          = @($warnings)
}

# -- Emit ---------------------------------------------------------------------

if ($Format -eq 'json') {
    # ConvertTo-Json (PS 5.1) can render an empty array property as "" and a
    # single-element array as a scalar. Array-valued fields are already forced to
    # @(...) at assignment time, so the JSON shape is STABLE regardless of counts;
    # -Depth 12 keeps the nested report from collapsing to System.Object[].
    $json = $report | ConvertTo-Json -Depth 12
    Write-Output $json
    exit 0
}

# -- Text report --
function Format-YesNo([bool]$b) { if ($b) { return 'yes' } else { return 'no' } }

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("skill-mesh host-install report (schema_version $SCHEMA_VERSION)")
$lines.Add("consumer_home: $($report.consumer_home)")
$lines.Add('')
$lines.Add('instruction files:')
foreach ($f in @($report.instruction_files)) {
    $lines.Add("  $($f.rel_path): present=$(Format-YesNo $f.present) [$($f.evidence_class)]")
}
$lines.Add('')

function Add-ProfileLines($label, $prof) {
    $script:lines.Add("$label ($($prof.discovery_root)): state=$($prof.state) link=$($prof.link_type)")
    if ($null -ne $prof.link_target) { $script:lines.Add("  link_target: $($prof.link_target)") }
    if ($prof.state -eq 'present') {
        $script:lines.Add("  owned=$($prof.owned_count) unowned=$($prof.unowned_count)")
        if ($null -ne $prof.adapter_sample) {
            $script:lines.Add("  adapter_sample: $($prof.adapter_sample.skill) -> profile=$($prof.adapter_sample.profile_header)")
        }
        foreach ($s in @($prof.skills)) {
            $ms = if ($null -ne $s.manifest_status) { $s.manifest_status } else { '-' }
            $script:lines.Add("    - $($s.name): $($s.eligibility) (manifest=$ms, owned=$(Format-YesNo $s.owned))")
        }
    }
}

Add-ProfileLines 'claude profile' $report.profiles.claude
$lines.Add('')
Add-ProfileLines 'gpt profile' $report.profiles.gpt
$lines.Add('')
Add-ProfileLines 'legacy .claude/skills-gpt' $report.legacy_skills_gpt
$lines.Add('')
$lines.Add("ledger: state=$($report.ledger.state) providers=[$(@($report.ledger.providers) -join ', ')] unrecognized=$($report.ledger.unrecognized_provider_count)")
$routerVer = if ($null -ne $report.router.version) { $report.router.version } else { '-' }
$routerPath = if ($null -ne $report.router.rel_path) { $report.router.rel_path } else { '-' }
$lines.Add("router: classification=$($report.router.classification) version=$routerVer path=$routerPath")
$lines.Add("legacy_shadows: [$(@($report.legacy_shadows) -join ', ')]")
$lines.Add('')
$lines.Add("warnings ($(@($report.warnings).Count)):")
foreach ($w in @($report.warnings)) {
    $lines.Add("  [$($w.code)] $($w.message)")
}

Write-Output ($lines -join [Environment]::NewLine)
exit 0
