<#
.SYNOPSIS
    skill-mesh-discovery.ps1 -- the SINGLE source of truth for WHERE a host
    discovers skills inside a consumer home: the provider -> discovery-root map and
    the retired/legacy roots the tooling still has to recognize.

.DESCRIPTION
    Dot-sourced (never executed), exactly like tools/skill-mesh-provenance.ps1 and
    tools/skill-mesh-transaction.ps1, by every tool that has to name a root:

      tools/install-skill-mesh.ps1     writes a profile into one of these roots
      tools/inspect-host-install.ps1   reports on all of them
      tools/migrate-legacy-install.ps1 scans, installs into, and retires them
      tools/probe-codex-skills.ps1     reports on the codex root (read-only)

    WHY THIS FILE EXISTS. These path shapes were previously hand-maintained in each
    of those three scripts, each commented as a "mirror" of the others. That is the
    duplicate-shape-constants anti-pattern the workspace's code-quality rule names
    explicitly ("Dimensions, action counts, schema column lists, magic widths -- any
    constant defining data shape must have ONE source of truth ... Duplicate
    definitions always drift"), and this repository has already paid for exactly this
    drift class once: the Step 43/44 proof retargeted the GPT root from the
    project-relative .copilot tree to the real Copilot project root, which had to be
    corrected in the installer AND in every mirror of it. A provider MISSING from the
    map is caught loudly (the migrator blocks with UNKNOWN_PROVIDER_ROOT), but a
    provider whose root is CHANGED in one script and not the others fails silently --
    the tools would scan, install, and back up at a path the host no longer reads.
    So the literal lives here once and the others call for it.

    tests/distributions/test_legacy_migration.py::
    test_discovery_roots_have_exactly_one_owner enforces that: it strips comments
    from every git-tracked .ps1 and fails if any file other than this one still
    spells a root literal in executable code, so a fourth copy cannot reappear.

    THE PROJECT ROOTS.
      claude -> .claude/skills   Claude Code's project skill-discovery root.
      gpt    -> .github/skills   A real GitHub Copilot CLI project discovery root,
                                 proven live in Step 43 (#58) and confirmed to win
                                 the both-profile collision in Step 45 (#67).
      codex  -> .agents/skills   Codex's skill-discovery root, resolved against the
                                 caller's base (for a live Codex install that base is
                                 $CODEX_EFFECTIVE_HOME; see tools/probe-codex-skills.ps1,
                                 the ONE resolver for that value). Added Phase CP Step 5.

                                 SAME LITERAL ROOT AS THE COPILOT ACTIVE ALTERNATE.
                                 Before Step 5 this exact path appeared ONLY in
                                 Get-SkillMeshActiveProjectDiscoveryRoots below, as a
                                 Copilot-scanned root skill-mesh never installed into.
                                 It is not a second, different root: this file has
                                 exactly ONE base (the caller's -Home), so both names
                                 denote the same directory whenever the two bases
                                 coincide. That is the collision design decision D-CP6
                                 defers to M1 evidence -- it is REAL, not vacuous, and
                                 no guard is pre-built here. Whether Copilot actually
                                 loads codex-profile packages is recorded by M1 in
                                 documentation/parity-deltas.md; the policy (accept vs
                                 guard) is decided there, not assumed here.

                                 Note the shape this creates: the active-project set
                                 below was already a SUPERSET of this map's values
                                 (.claude/skills, .github/skills, + .agents/skills).
                                 With codex installable the two sets are now EQUAL --
                                 every root skill-mesh installs into is a root some
                                 supported host actively scans, which is the
                                 pre-existing pattern for claude and gpt, not a new one.
    Retired / legacy, recognized but never installed into:
      .copilot/skills            The pre-Step-44 PROJECT-relative GPT target.
                                 Copilot does not discover that project path; any
                                 generated tree found there is superseded. In
                                 contrast, `~/.copilot/skills` is an ACTIVE personal
                                 discovery root and is never retirement-eligible.
      .claude/skills-gpt         The legacy GPT core tree that can still shadow
                                 resolution.

    Paths are home-relative and POSIX-form; callers translate separators.

    ASCII-only, no BOM (PowerShell 5.1 reads a no-BOM .ps1 as ANSI/cp1252).
    No Set-StrictMode here: dot-sourcing runs in the CALLER's scope and must not
    change the caller's strictness.
#>

function Get-SkillMeshDiscoveryRoots {
    # provider slug -> home-relative POSIX discovery root. A FRESH hashtable per
    # call, so a caller that mutates its copy cannot corrupt another caller's view.
    # A hashtable is a single object, so it needs no comma-wrap to survive return.
    return @{
        'claude' = '.claude/skills'
        'gpt'    = '.github/skills'
        'codex'  = '.agents/skills'
    }
}

function Get-SkillMeshActiveProjectDiscoveryRoots {
    <#
      Every project-relative root a supported host actively scans, whether or not
      skill-mesh installs a profile there. The migrator consumes this larger set
      when deciding whether bytes under the retired project `.copilot/skills` tree
      are nevertheless host-visible through an in-home alias.

      Claude installs/discovers `.claude/skills`. Copilot discovers that root plus
      `.github/skills` and `.agents/skills`; skill-mesh chooses `.github/skills` as
      its GPT install target. A FRESH array prevents caller mutation.

      SCOPE UNCHANGED BY STEP 5 -- read this before "simplifying" the two functions
      into one. This set answers "could a host SEE bytes here?", which is the
      question the retirement authorization asks; the map above answers "where does
      skill-mesh WRITE?". Since Step 5 made `.agents/skills` installable (codex) the
      two sets happen to hold the same three paths, and that coincidence is exactly
      why they must stay separate functions: a future host root skill-mesh never
      installs into belongs here and NOT there, and deriving one from the other
      would silently drop it. `.agents/skills` was in this set before codex existed
      and stays here for its ORIGINAL reason (Copilot scans it) independently of
      the new one.
    #>
    return @('.claude/skills', '.github/skills', '.agents/skills')
}

function Get-SkillMeshDiscoveryRoot {
    # The root for ONE provider, or $null when this tool knows no root for it.
    # $null is a meaningful answer, not an error: the migrator turns it into a loud
    # UNKNOWN_PROVIDER_ROOT block rather than silently skipping the provider.
    param([string]$Provider)
    if ([string]::IsNullOrWhiteSpace($Provider)) { return $null }
    $map = Get-SkillMeshDiscoveryRoots
    if ($map.ContainsKey($Provider)) { return $map[$Provider] }
    return $null
}

function Resolve-SkillMeshProvider {
    <#
      Match a caller-supplied provider token against a closed vocabulary and return
      the VOCABULARY'S OWN spelling -- never the caller's. The single owner for
      provider-slug normalization across the installer, the inspector, and the
      migrator (it replaced the inspector's private Resolve-KnownProvider rather
      than becoming a fourth copy of it).

      $Vocabulary is supplied by the caller because each tool already holds the
      authoritative list: the inspector and migrator read the manifest's own
      top-level `providers` object, the installer uses the keys of the map above.
      Passing it in keeps this function from needing a manifest path and keeps the
      vocabulary sourced from one place per tool.

      Two traps make the obvious `-contains` wrong, and BOTH behaviors are
      test-locked -- do not "simplify" either away:

        1. `-contains` is CULTURE-aware, so it treats 'claude' plus a run of
           Unicode-ignorable characters (U+00AD and friends) as EQUAL to 'claude'.
           Echoing the matched token would then put unbounded non-ASCII consumer
           bytes into a report under the guise of a known provider. So the
           comparison is ORDINAL.
        2. It is also case-INSENSITIVE, which we WANT: the installer's
           [ValidateSet('claude','gpt','codex')] accepts -Provider CLAUDE, so a
           case-sensitive match would drop a legitimate install -- a false-clean
           preflight, worse than the leak.

      Match case-insensitively but ORDINALLY, and emit the vocabulary's own slug so
      the closed vocabulary holds either way. Returns $null when there is no match.
    #>
    param([string]$Value, [string[]]$Vocabulary)
    if ([string]::IsNullOrEmpty($Value)) { return $null }
    if ($null -eq $Vocabulary) { return $null }
    foreach ($p in $Vocabulary) {
        if ([string]::Equals($p, $Value, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $p
        }
    }
    return $null
}

function Get-SkillMeshRetiredCopilotRoot {
    # The RETIRED project-relative GPT target. Named here so the inspector's
    # "present -- likely a pre-retarget install" warning and the migrator's retire
    # set can never disagree about which path that is.
    return '.copilot/skills'
}

function Get-SkillMeshLegacySkillsGptRoot {
    # The legacy GPT core tree (still classified by the inspector; out of scope for
    # the Step-47 migrator, which leaves it untouched for the Step-48 handoff).
    return '.claude/skills-gpt'
}
