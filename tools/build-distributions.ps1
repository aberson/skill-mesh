<#
.SYNOPSIS
    build-distributions.ps1 -- DETERMINISTICALLY generate host-specific
    compatibility trees from config/skill-manifest.json + the canonical
    skills/<name>/{core.md,providers/claude.md,providers/gpt.md} source tree.

.DESCRIPTION
    Emits one discovery profile per provider into a staging output directory
    (default <repo>/dist). Host discovery requires provider-specific filenames and
    directories, but those requirements never dictate canonical ownership: the
    canonical files under skills/ are the single source of truth and are NEVER
    rewritten. Each generated file is a copy carrying a GENERATED provenance header.

      dist/claude/<skill>/SKILL.md   Claude Code discovery launcher. Body is the
                                     skill's Claude adapter (providers/claude.md)
                                     whose own-core reference (../core.md) is
                                     rewritten to the co-located core.md.
      dist/claude/<skill>/core.md    The shared canonical core (portable skills
                                     only), so the launcher's reference resolves.
      dist/gpt/<skill>/SKILL.md      GPT/Copilot discovery launcher (providers/gpt.md).
      dist/gpt/<skill>/core.md       The shared canonical core (portable only).
      dist/<p>/_shared/<asset>       The shared support payload (judge-core.md,
                                     score-skill.md, the scoring/grader scripts, the
                                     scoring Workflow), ONE copy per profile at the
                                     profile root as a sibling of the skill dirs.

    SHARED REFERENCES. Canonical sources cite the payload from two levels down
    (skills/<n>/core.md -> ../../_shared/x) or three (skills/<n>/providers/<p>.md ->
    ../../../_shared/x). Nothing exists above a host discovery root, so every emitted
    file -- skill dirs and the payload alike -- sits exactly ONE level below it and
    every such reference is repointed to ../_shared/x. The rewrite is
    longest-token-first because '../../../_shared/' contains '../../_shared/', and it
    is NOT conditional on the skill having a core (judge-motion is core: null and
    still cites the payload).

    The payload SET is the transitive closure re-walked from this profile's own
    emitted sources on every run, not a committed list, and every emitted asset is
    stamped with the same provenance marker as the markdown (.js via
    Add-JsProvenance, which wraps the identical header in /* */) so the installer can
    own -- and uninstall can remove -- every byte of it.

    Provider-native skills (manifest status 'provider-native' / core == null) get
    ONLY their truthful supported adapter: they appear in dist/claude/ with no core
    reference, and are ABSENT from dist/gpt/ -- no misleading stub for the
    unsupported provider.

    SECURITY: the manifest is treated as untrusted input. Each skill 'name' is
    validated as a safe single path segment before it is joined into an output path,
    and every generated file's resolved absolute path is asserted to stay within the
    intended profile directory (defense in depth via runtime/path-guard.ps1). Every
    SOURCE path read from the manifest (core / providers.<p>) is likewise validated
    to stay within the canonical skills/ root before it is read/copied -- a traversal
    or absolute source path is rejected, never read into a generated file.

    DETERMINISM: output is byte-identical across repeated runs on unchanged input.
    Skills are processed in a stable manifest-name order; no wall-clock timestamp is
    embedded in any file body (the provenance header names only the canonical source
    path + the manifest, never a date); all files are written UTF-8 (no BOM) with LF
    line endings.

.PARAMETER OutputDir
    Staging root the profiles are written under. Default: <repo>/dist. Each
    per-provider subtree (<OutputDir>/claude, <OutputDir>/gpt) is removed and
    regenerated from scratch so a rebuild cannot leave stale files behind.

.PARAMETER Provider
    Which profile(s) to build: 'claude', 'gpt', or 'both' (default).

.PARAMETER ManifestPath
    Override the manifest consumed. Default: <repo>/config/skill-manifest.json.
    (Primarily a test seam for adversarial manifests.)

.EXAMPLE
    powershell -File tools\build-distributions.ps1
    powershell -File tools\build-distributions.ps1 -Provider claude -OutputDir C:\stage\dist
#>

[CmdletBinding()]
param(
    [string]$OutputDir = '',

    [ValidateSet('claude', 'gpt', 'both')]
    [string]$Provider = 'both',

    [string]$ManifestPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -- Path resolution (repo-root relative) -------------------------------------

$TOOLS_DIR = $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $TOOLS_DIR
$SKILLS_ROOT = Join-Path $REPO_ROOT 'skills'
$SHARED_ROOT = Join-Path $REPO_ROOT '_shared'
# The shared payload ships at the PROFILE ROOT, as a sibling of the skill dirs (D1):
# one copy per profile instead of one per consuming skill, and one level below the
# discovery root -- exactly the depth every '../_shared/x' repoint assumes.
$SHARED_DEST = '_shared'
# A '_shared/<leaf>' asset reference in any spelling the sources use: bare
# ('_shared/x'), or anchored at depth 2 / depth 3 ('../../_shared/x',
# '../../../_shared/x'). The capture is the leaf, which is all the emitter needs.
$SHARED_REF_RE = [regex]'(?:\.\./)*_shared/([A-Za-z0-9][A-Za-z0-9._-]*)'
$VERDICT_HELPER_SOURCE = Join-Path $SHARED_ROOT 'build_step_verdict.py'
$PATH_GUARD = Join-Path $REPO_ROOT 'runtime\path-guard.ps1'
$PROVENANCE = Join-Path $TOOLS_DIR 'skill-mesh-provenance.ps1'

if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
    $ManifestPath = Join-Path $REPO_ROOT 'config\skill-manifest.json'
}
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $REPO_ROOT 'dist'
}

# Reuse the Step-34 path guard (traversal/junction/symlink rejection). Dot-source
# with no -Path so only its functions load (Resolve-SafePath in this scope).
. $PATH_GUARD
# Shared provenance marker (single source of truth; defines Get-SkillMeshMarker).
. $PROVENANCE

$UTF8_NO_BOM = New-Object System.Text.UTF8Encoding($false)

# -- Helpers ------------------------------------------------------------------

function Get-Prop($obj, [string]$name) {
    # StrictMode-safe property read: returns $null when the property is absent (or
    # the container itself is null).
    if ($null -eq $obj) { return $null }
    $p = $obj.PSObject.Properties[$name]
    if ($p) { return $p.Value }
    return $null
}

function Test-SafeSegment([string]$name) {
    # A safe single path segment: non-empty, no separators, no traversal, not
    # absolute, no drive/colon. Rejects a hostile manifest name like
    # '..\..\evil-escape' before it is joined into an output path.
    if ([string]::IsNullOrWhiteSpace($name)) { return $false }
    if ($name -match '[\\/]') { return $false }
    if ($name.Contains('..')) { return $false }
    if ($name.Contains(':')) { return $false }
    if ($name -eq '.' -or $name -eq '..') { return $false }
    if ([System.IO.Path]::IsPathRooted($name)) { return $false }
    return $true
}

function Resolve-RepoPath([string]$relPosix) {
    # Manifest paths are POSIX ('skills/x/core.md'); resolve under the repo root.
    return (Join-Path $REPO_ROOT ($relPosix -replace '/', '\'))
}

function Resolve-SafeSharedSource([string]$leaf) {
    # SECOND scoped resolve, pinned to the canonical _shared/ root. Deliberately NOT a
    # widening of Resolve-SafeSource below: that guard stays pinned to skills/ so a
    # manifest-declared skill source can never be read from anywhere else. A shared
    # asset name is harvested from PROSE (a reference inside a core/adapter body), so it
    # is validated as a single safe path segment FIRST and then re-resolved inside
    # $SHARED_ROOT -- two independent guards, neither relaxing the other.
    if (-not (Test-SafeSegment $leaf)) {
        throw ("build-distributions: SECURITY -- unsafe shared-asset name '$leaf' " +
               "harvested from a source reference (must be a single path segment: no " +
               "separators, no '..', not absolute). Refusing to read.")
    }
    $abs = Join-Path $SHARED_ROOT $leaf
    try {
        return (Resolve-SafePath -Path $abs -AllowedRoots @($SHARED_ROOT))
    } catch {
        throw ("build-distributions: SECURITY -- shared asset '$leaf' escapes the " +
               "canonical _shared/ root; refusing to read. " + $_.Exception.Message)
    }
}

function Resolve-SafeSource([string]$relPosix, [string]$name, [string]$role) {
    # Validate a manifest-declared SOURCE path stays within the canonical skills/
    # root BEFORE it is read. A traversal/absolute path throws (build refuses).
    if ([string]::IsNullOrWhiteSpace($relPosix)) {
        throw "build-distributions: empty $role source for skill '$name'"
    }
    $abs = Resolve-RepoPath $relPosix
    try {
        return (Resolve-SafePath -Path $abs -AllowedRoots @($SKILLS_ROOT))
    } catch {
        throw ("build-distributions: SECURITY -- $role source '$relPosix' for skill " +
               "'$name' escapes the canonical skills/ root; refusing to read. " +
               $_.Exception.Message)
    }
}

function Read-SourceText([string]$absPath) {
    # Read canonical bytes and normalize to LF so provenance + rewrites are
    # deterministic regardless of the working tree's checkout line endings.
    $raw = [System.IO.File]::ReadAllText($absPath, [System.Text.Encoding]::UTF8)
    return ($raw -replace "`r`n", "`n") -replace "`r", "`n"
}

function New-ProvenanceHeader([string]$canonicalSource, [string]$profile) {
    # GENERATED do-not-edit marker. Names the canonical source path + the manifest.
    # NO date / wall-clock time -- provenance must not break byte reproducibility.
    $lines = @(
        (Get-SkillMeshHeaderOpen),
        "     $(Get-SkillMeshMarkerLine)",
        '     Produced by tools/build-distributions.ps1 from config/skill-manifest.json.',
        "     Canonical source: $canonicalSource",
        "     Profile: $profile",
        '     Edit the canonical source and rebuild; edits here are overwritten. -->'
    )
    return ($lines -join "`n")
}

function Add-Provenance([string]$body, [string]$canonicalSource, [string]$profile) {
    # Insert the provenance header. When the body opens with a YAML frontmatter
    # block, the header is placed immediately AFTER it so the frontmatter stays on
    # line 1 (Claude Code discovery requires frontmatter first); otherwise it is
    # prepended.
    $prov = New-ProvenanceHeader $canonicalSource $profile
    $fmMatch = [regex]::Match($body, "(?s)^---\n.*?\n---\n")
    if ($fmMatch.Success) {
        $fm = $fmMatch.Value
        $rest = $body.Substring($fm.Length)
        return $fm + $prov + "`n" + $rest
    }
    return $prov + "`n`n" + $body
}

function ConvertTo-YamlDoubleQuoted([string]$s) {
    # A YAML double-quoted scalar: escape backslash then double-quote (order matters),
    # wrap in quotes. Robust regardless of the description's punctuation (colons,
    # hashes, leading special chars are all safe inside a double-quoted scalar).
    $e = $s.Replace('\', '\\').Replace('"', '\"')
    return '"' + $e + '"'
}

function New-GptFrontmatter([string]$name, [string]$description) {
    # GitHub Copilot CLI requires every native SKILL.md to LEAD with a YAML
    # frontmatter block carrying at least `name` + `description` (Step 43 proof).
    # `name` and `description` both come from the manifest record (single source of
    # truth); the description is never re-authored per host.
    $descYaml = ConvertTo-YamlDoubleQuoted $description
    $lines = @(
        '---',
        "name: $name",
        "description: $descYaml",
        '---'
    )
    return (($lines -join "`n") + "`n")
}

function Repoint-CoreReference([string]$adapterBody) {
    # In the canonical tree the adapter lives at skills/<name>/providers/<p>.md and
    # references its core as '../core.md'. In the flat discovery layout core.md is a
    # sibling of SKILL.md, so repoint the own-core reference to 'core.md'. Only the
    # exact '../core.md' token is touched: cross-skill refs like
    # '../../judge-ui/core.md' are left intact.
    return $adapterBody.Replace('../core.md', 'core.md')
}

function Repoint-VerdictHelperReference([string]$coreBody) {
    # The canonical cores point at the repo-root shared implementation. Generated
    # host profiles co-locate a provenance-owned copy beside each consuming core.
    return $coreBody.Replace('../../_shared/build_step_verdict.py',
                             'build_step_verdict.py')
}

function Repoint-SharedReference([string]$body) {
    # Canonical cores/adapters cite the repo-root shared assets from inside
    # skills/<name>/ (depth 2 -> '../../_shared/x') or skills/<name>/providers/
    # (depth 3 -> '../../../_shared/x'). A built profile puts every generated file
    # exactly ONE level below the discovery root -- dist/<p>/<skill>/ and, for the
    # shared payload itself, dist/<p>/_shared/ -- so the one correct spelling in an
    # emitted file is '../_shared/x'.
    #
    # LONGEST TOKEN FIRST is load-bearing (design decision D2): '../../../_shared/'
    # literally CONTAINS '../../_shared/', so replacing the two-dot form first
    # rewrites judge-motion's depth-3 references into still-broken depth-2
    # references, silently, with nothing objecting. There ARE live depth-3
    # references (skills/judge-motion/providers/claude.md), and judge-motion is a
    # core: null skill -- so callers must NOT gate this on a core being present.
    $out = $body.Replace('../../../_shared/', '../_shared/')
    return $out.Replace('../../_shared/', '../_shared/')
}

# A BARE '_shared/x' token: the namespace named without a relative anchor. The
# negative lookbehind keeps it from matching the '_shared/' that is already the tail
# of a longer path -- '../_shared/x' (this function's own output, so the rewrite is
# idempotent) or a host-home citation like '<dot>claude/skills/_shared/x', which
# names the consumer home and is not ours to repoint.
$BARE_SHARED_REF_RE = [regex]'(?<![\w/\\.-])_shared/'

function Repoint-SharedAssetReference([string]$body) {
    # The repoint for a file emitted INTO dist/<p>/_shared/. On top of the anchored
    # rewrite above it also normalizes BARE '_shared/x' tokens, which the skill-side
    # rewrite deliberately leaves alone.
    #
    # Why the asymmetry: a bare token inside a SKILL core is frozen in the link gate's
    # allowlist as class `shared_bare`, and rewriting it there would make the frozen
    # entry neither repairable (it still would not resolve under its frozen spelling)
    # nor retirable (its bytes survive inside the longer token) -- an unwinnable
    # position for that gate. A file emitted into dist/<p>/_shared/ has no frozen
    # entries at all: it is new in this step, so its own references must simply
    # RESOLVE, and '_shared/x' resolved from dist/<p>/_shared/ would mean
    # dist/<p>/_shared/_shared/x, which does not exist.
    $out = Repoint-SharedReference $body
    return $BARE_SHARED_REF_RE.Replace($out, '../_shared/')
}

function Test-PytestModuleName([string]$leaf) {
    # pytest's default collection patterns (`test_*.py`, `*_test.py`). Named as the
    # predicate it is so the emit-side refusal below reads as one condition.
    return ($leaf -match '^test_.*\.py$') -or ($leaf -match '.*_test\.py$')
}

function Get-SharedCanonicalLabel([string]$leaf) {
    # ONE spelling of the 'Canonical source:' value for a _shared/-sourced file.
    #
    # Spelled '<repo>/_shared/<leaf>', NOT '_shared/<leaf>': the header ships INSIDE
    # the generated file, and a bare '_shared/x' token there is a REFERENCE that
    # resolves from the emitting file's own directory (dist/<p>/_shared/_shared/x --
    # absent). The '<repo>/' prefix names the identical canonical path while making
    # the token unambiguously repo-rooted rather than relative.
    return "<repo>/_shared/$leaf"
}

function Get-SharedLeafReference([string]$text) {
    # Every '_shared/<leaf>' asset named by $text, in any anchored or bare spelling.
    $out = @()
    foreach ($m in $SHARED_REF_RE.Matches($text)) { $out += $m.Groups[1].Value }
    return $out
}

function Get-SharedClosure([string[]]$seeds) {
    # RE-WALK the transitive closure at build time rather than shipping a list.
    #
    # Seeds are the '_shared/<leaf>' tokens harvested from the skill sources this
    # profile actually emits, so a profile that emits no consumer (an adversarial or
    # minimal manifest) legitimately ships no shared payload at all. From each
    # markdown asset already in the closure, two further edges are followed:
    #   * another '_shared/<leaf>' token, and
    #   * a BARE mention of a file that exists in the canonical _shared/ root --
    #     which is how judge-core.md reaches grader_prompt.py / calibrate_judge.py /
    #     score_skill.workflow.js and score-skill.md reaches score_skill_absolute.py.
    #     Those are sibling citations inside _shared/, so they carry no namespace
    #     prefix to match on.
    # Only markdown is walked: .py/.js assets are payload leaves, and their bodies are
    # code, not the prose a reader follows.
    #
    # The walk is deliberately allowed to OVER-include: an asset it pulls in that has
    # no emitter for its extension makes the build THROW (see the emit block), so an
    # unexpected edge is loud rather than a silently unstamped file.
    $found = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $queue = New-Object 'System.Collections.Generic.Queue[string]'
    foreach ($s in $seeds) {
        if ($found.Add($s)) { $queue.Enqueue($s) }
    }
    $sharedNames = @(Get-ChildItem -LiteralPath $SHARED_ROOT -File |
                     ForEach-Object { $_.Name } | Sort-Object)
    while ($queue.Count -gt 0) {
        $leaf = $queue.Dequeue()
        if (-not $leaf.ToLowerInvariant().EndsWith('.md')) { continue }
        $abs = Resolve-SafeSharedSource $leaf
        if (-not (Test-Path -LiteralPath $abs -PathType Leaf)) {
            throw "build-distributions: shared asset source missing: _shared/$leaf"
        }
        $body = Read-SourceText $abs
        $next = @(Get-SharedLeafReference $body)
        foreach ($n in $sharedNames) {
            if ($n -eq $leaf) { continue }
            $pattern = '(?<![\w/\\.-])' + [regex]::Escape($n) + '(?![\w-])'
            if ([regex]::IsMatch($body, $pattern)) { $next += $n }
        }
        foreach ($n in $next) {
            if ($found.Add($n)) { $queue.Enqueue($n) }
        }
    }
    # Sorted: the emitted file SET and the emit ORDER must both be deterministic.
    return @($found | Sort-Object)
}

function Add-PythonProvenance([string]$body, [string]$canonicalSource, [string]$profile) {
    # Keep __future__ imports legal by inserting the generated marker INSIDE the
    # module's existing leading docstring rather than prepending a new statement.
    $marker = New-ProvenanceHeader $canonicalSource $profile
    $docStart = $body.IndexOf('"""')
    if ($docStart -lt 0 -or $docStart -gt 256) {
        throw "build-distributions: Python support source lacks a leading docstring: $canonicalSource"
    }
    return $body.Insert($docStart + 3, "`n$marker")
}

function Write-GeneratedFile([string]$absPath, [string]$content, [string]$profileDir) {
    # Defense in depth: assert the resolved output path stays within the intended
    # profile dir before writing (name validation is the primary guard; this catches
    # any residual escape).
    $safe = Resolve-SafePath -Path $absPath -AllowedRoots @($profileDir)
    $dir = Split-Path -Parent $safe
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($safe, $content, $UTF8_NO_BOM)
}

# -- Load manifest ------------------------------------------------------------

if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "build-distributions: manifest not found at $ManifestPath"
}
$manifest = (Read-SourceText $ManifestPath) | ConvertFrom-Json

# Stable order: sort by skill name so the file SET + contents are deterministic
# regardless of manifest array order.
$skills = @($manifest.skills | Sort-Object -Property name)

$profiles = if ($Provider -eq 'both') { @('claude', 'gpt') } else { @($Provider) }

# -- Build --------------------------------------------------------------------

foreach ($profile in $profiles) {
    $profileDir = Join-Path $OutputDir $profile
    # Regenerate from scratch: a rebuild must never inherit stale files.
    if (Test-Path -LiteralPath $profileDir) {
        Remove-Item -LiteralPath $profileDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    # Canonical absolute form of the profile dir, for containment assertions.
    $profileDirAbs = (Resolve-Path -LiteralPath $profileDir).Path

    $skillCount = 0
    $fileCount = 0
    # Seeds for this profile's shared-payload closure, harvested from the sources this
    # profile actually emits. Per-profile, not global: the GPT profile omits the
    # provider-native skills, and a minimal manifest may emit nothing at all.
    $sharedSeeds = @()

    foreach ($skill in $skills) {
        $name = [string](Get-Prop $skill 'name')
        $status = [string](Get-Prop $skill 'status')

        # SECURITY: validate the skill name as a safe single segment BEFORE it is
        # joined into any output path.
        if (-not (Test-SafeSegment $name)) {
            throw ("build-distributions: SECURITY -- unsafe skill name " +
                   "'$name' in manifest (must be a single path segment: no " +
                   "separators, no '..', not absolute). Refusing to build.")
        }

        $isNative = ($status -eq 'provider-native') -or ($null -eq (Get-Prop $skill 'core'))

        # GPT profile excludes provider-native skills entirely (no misleading stub).
        if ($profile -eq 'gpt' -and $isNative) { continue }

        $providersObj = Get-Prop $skill 'providers'
        $adapterRel = Get-Prop $providersObj $profile
        if ([string]::IsNullOrWhiteSpace($adapterRel)) {
            # No adapter declared for this provider (e.g. gpt on a native skill).
            continue
        }

        # SECURITY: validate + resolve ALL of this skill's SOURCE paths within skills/
        # BEFORE writing ANY output file, so a core-only-malicious manifest cannot
        # leave a partial dist artifact (SKILL.md written, then core validation throws).
        $adapterAbs = Resolve-SafeSource $adapterRel $name "$profile-adapter"
        if (-not (Test-Path -LiteralPath $adapterAbs)) {
            throw "build-distributions: adapter source missing for '$name' ($profile): $adapterAbs"
        }
        $coreRel = Get-Prop $skill 'core'
        $hasCore = -not [string]::IsNullOrWhiteSpace($coreRel)
        $coreAbs = $null
        if ($hasCore) {
            $coreAbs = Resolve-SafeSource $coreRel $name 'core'
            if (-not (Test-Path -LiteralPath $coreAbs)) {
                throw "build-distributions: core source missing for '$name': $coreAbs"
            }
        }

        $skillOutDir = Join-Path $profileDir $name

        # -- Launcher (SKILL.md) -- (all sources validated above)
        $adapterBody = Read-SourceText $adapterAbs
        # Harvest closure seeds from the CANONICAL text, before any repoint.
        $sharedSeeds += @(Get-SharedLeafReference $adapterBody)
        if ($hasCore) {
            $adapterBody = Repoint-CoreReference $adapterBody
        }
        # NOT gated on $hasCore: judge-motion is core: null in the manifest and its
        # adapter still carries depth-3 '../../../_shared/' references (D2).
        $adapterBody = Repoint-SharedReference $adapterBody
        # GPT/Copilot native discovery requires the SKILL.md to LEAD with a YAML
        # frontmatter block (name + description). The canonical gpt.md adapters carry
        # no frontmatter, so synthesize it from the manifest record here; the
        # provenance header is then placed immediately AFTER the closing '---' by
        # Add-Provenance's frontmatter-first path. Skip synthesis if the adapter body
        # somehow already leads with frontmatter (defensive: avoid double blocks).
        # Claude output is untouched -- its canonical claude.md already ships
        # frontmatter and Add-Provenance already sequences behind it.
        if ($profile -eq 'gpt' -and -not $adapterBody.StartsWith("---`n")) {
            $desc = [string](Get-Prop $skill 'description')
            if ([string]::IsNullOrWhiteSpace($desc)) {
                # Fallback keeps minimal/adversarial manifests (no description field)
                # producing a valid frontmatter rather than an empty one.
                $desc = "$name (skill-mesh skill)."
            }
            $adapterBody = (New-GptFrontmatter $name $desc) + $adapterBody
        }
        $launcher = Add-Provenance $adapterBody $adapterRel $profile
        Write-GeneratedFile (Join-Path $skillOutDir 'SKILL.md') $launcher $profileDirAbs
        $fileCount++

        # -- Shared core (portable skills only) --
        if ($hasCore) {
            $coreBody = Read-SourceText $coreAbs
            $sharedSeeds += @(Get-SharedLeafReference $coreBody)
            # ORDER IS LOAD-BEARING (D2): the verdict-helper repoint runs FIRST,
            # because it consumes the longest token of all
            # ('../../_shared/build_step_verdict.py' -> the co-located copy). Running
            # the generic shared repoint first would turn it into
            # '../_shared/build_step_verdict.py' and this repoint would never match.
            if ($name -eq 'build-step' -or $name -eq 'build-phase') {
                $coreBody = Repoint-VerdictHelperReference $coreBody
            }
            $coreBody = Repoint-SharedReference $coreBody
            $coreOut = Add-Provenance $coreBody $coreRel $profile
            Write-GeneratedFile (Join-Path $skillOutDir 'core.md') $coreOut $profileDirAbs
            $fileCount++
        }

        $skillCount++
    }

    # -- Shared payload: dist/<profile>/_shared/ (D1) --
    # One copy per profile, at the profile root, so every emitted '../_shared/x'
    # reference resolves inside the discovery root a consumer home actually has.
    # The SET is the transitive closure RE-WALKED from this profile's own sources,
    # never a committed list -- a hand-maintained payload list is the workspace's
    # canonical false-green shape.
    $sharedClosure = Get-SharedClosure $sharedSeeds
    $sharedOutDir = Join-Path $profileDir $SHARED_DEST
    foreach ($leaf in $sharedClosure) {
        $sharedAbs = Resolve-SafeSharedSource $leaf
        if (-not (Test-Path -LiteralPath $sharedAbs -PathType Leaf)) {
            throw "build-distributions: shared asset source missing: _shared/$leaf"
        }
        if (Test-PytestModuleName $leaf) {
            # Fail LOUD rather than silently filtering. The default OutputDir is
            # <repo>/dist, which sits INSIDE this repository's own pytest rootdir, and
            # this repository has no pytest config to exclude it -- so shipping a test
            # module would make the project's declared DONE gate (repo-root
            # `python -m pytest`) collect two extra copies of it under duplicate
            # basenames and error out. A shared doc that merely NAMES its unit-test
            # module drags it into the closure, so the remedy is at the citation:
            # describe it as repo-only prose, the same disposition the two workspace
            # citations in score-skill.md already carry.
            throw ("build-distributions: shared asset '_shared/$leaf' is a pytest " +
                   "module and must not ship into a discovery profile (it would be " +
                   "collected by this repository's own repo-root pytest run). A " +
                   "_shared/*.md file cites it by name; convert that citation to " +
                   "prose that does not name the file.")
        }
        # REPOINT EVERY EXTENSION, not just markdown, and BEFORE stamping (so the
        # header's own 'Canonical source' value is never rewritten by it). A
        # '_shared/<leaf>' token inside a .py docstring or a .js comment is a reference
        # a reader follows exactly like a markdown one, and left alone it resolves from
        # dist/<p>/_shared/ to dist/<p>/_shared/_shared/<leaf> -- a path that exists in
        # NEITHER profile. Applying the repoint only on the .md branch shipped one such
        # token live (_shared/score_skill_composite.py cites _shared/score-skill.md).
        $sharedBody = Repoint-SharedAssetReference (Read-SourceText $sharedAbs)
        $sharedLabel = Get-SharedCanonicalLabel $leaf
        $ext = [System.IO.Path]::GetExtension($leaf).ToLowerInvariant()
        if ($ext -eq '.md') {
            $sharedOut = Add-Provenance $sharedBody $sharedLabel $profile
        } elseif ($ext -eq '.py') {
            $sharedOut = Add-PythonProvenance $sharedBody $sharedLabel $profile
        } elseif ($ext -eq '.js') {
            # Add-JsProvenance wraps the SAME header verbatim in /* */ so
            # Test-SkillMeshProvenance holds for the .js exactly as for .md/.py --
            # without it the shipped payload is foreign to install, absent from
            # owned_files, and undeletable by uninstall.
            $sharedOut = Add-JsProvenance $sharedBody (New-ProvenanceHeader $sharedLabel $profile)
        } else {
            # Fail LOUD. Every shipped file must carry a provenance marker or the
            # installer cannot own it; silently copying an unstampable extension
            # would plant an orphan that a no-orphan gate still reports as clean.
            throw ("build-distributions: no provenance emitter for shared asset " +
                   "'_shared/$leaf' (extension '$ext'); refusing to ship an " +
                   "unstamped file.")
        }
        Write-GeneratedFile (Join-Path $sharedOutDir $leaf) $sharedOut $profileDirAbs
        $fileCount++
    }

    # Shared durable-verdict helper. Both build-step and build-phase execute it,
    # but each host discovery package must remain self-contained; co-locate one
    # generated copy beside each consuming core (decision: KEEP co-location -- the
    # profile-root _shared/ copy above is the reference copy, the co-located one is
    # what build-step's own contract executes). Canonical ownership stays at
    # repo-root _shared/build_step_verdict.py.
    $verdictHelperAbs = Resolve-SafePath -Path $VERDICT_HELPER_SOURCE -AllowedRoots @($SHARED_ROOT)
    if (-not (Test-Path -LiteralPath $verdictHelperAbs -PathType Leaf)) {
        throw "build-distributions: verdict helper source missing: $verdictHelperAbs"
    }
    # Same repoint as the payload copy above: the co-located copy also sits exactly one
    # level below the discovery root (dist/<p>/<consumer>/), so '../_shared/x' is the one
    # correct spelling there too. Applying it here keeps the two copies byte-identical by
    # construction -- they cannot drift into two different reference shapes.
    $verdictHelperBody = Repoint-SharedAssetReference (Read-SourceText $verdictHelperAbs)
    $verdictHelperOut = Add-PythonProvenance $verdictHelperBody `
                            (Get-SharedCanonicalLabel 'build_step_verdict.py') $profile
    foreach ($consumer in @('build-step', 'build-phase')) {
        $consumerDir = Join-Path $profileDir $consumer
        if (-not (Test-Path -LiteralPath $consumerDir -PathType Container)) {
            # Adversarial/minimal manifests legitimately omit one or both build
            # skills. Emit support only for consumers present in this profile.
            continue
        }
        Write-GeneratedFile (Join-Path $consumerDir 'build_step_verdict.py') `
                            $verdictHelperOut $profileDirAbs
        $fileCount++
    }

    Write-Host "build-distributions: $profile -> $profileDir ($skillCount skills, $fileCount files)"
}

Write-Host "build-distributions: done. OutputDir = $OutputDir"
exit 0
