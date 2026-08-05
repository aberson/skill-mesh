<#
.SYNOPSIS
    migrate-legacy-install.ps1 -- reversible cutover of a legacy consumer home to
    the generated host profiles, as ONE journaled transaction with an external
    backup, ordered rollback, and idempotent crash-resume.

.DESCRIPTION
    The safe installer REFUSES a live legacy Claude tree (hand-authored SKILL.md
    files carry no provenance marker, so they are foreign), and -Force overwrites
    them with no backup and no undo. This command is the third option: classify
    every path, back up the pre-image of everything it will mutate, apply the
    Claude and GPT profiles as ONE transaction, and be able to put the home back.

    DRY RUN IS THE DEFAULT. With no -Apply/-Resume/-Rollback the command plans and
    prints a MigrationPlan and mutates NOTHING -- not the home, not the backup
    directory.

    CLASSIFICATION is the Step-46 inspector's manifest-driven cascade, reused
    verbatim so preserve/retire/install cannot diverge from what the read-only
    preflight reported:
        in config/skill-manifest.json      -> managed
        `_shared` with no SKILL.md         -> core-holder
        has a SKILL.md                     -> consumer-only
        anything else                      -> foreign
    `managed` trees are migrated (their generated paths are installed over, with
    the pre-image backed up; their STALE marker-bearing files are retired).
    `consumer-only` trees and the `core-holder` are PRESERVED byte-for-byte --
    never overwritten, never retired, never a block -- and are recorded in the
    backup manifest by relative path and SHA-256 ONLY, never payload-copied, so
    private consumer content is not duplicated into a backup it can never need.
    `foreign` BLOCKS before the first mutation.

    OWNERSHIP AUTHORITY IS FILE-CONTENT PROVENANCE, exactly as in the installer:
    Test-SkillMeshProvenance from tools/skill-mesh-provenance.ps1 (dot-sourced,
    never forked) decides whether a file is skill-mesh's to retire. The only
    non-marker files this command ever writes over are the exact target paths of
    the generated distribution -- the legacy adoption this command exists to
    perform -- and every one of those has its pre-image in the backup first.

    ATOMICITY IS NOT IMPLEMENTED HERE. The state machine, append-only journal,
    ordered rollback, and resume live in tools/skill-mesh-transaction.ps1, shared
    with tools/install-skill-mesh.ps1, so the "both profiles or neither" guarantee
    has one implementation.

    PROVIDER VOCABULARY comes from the manifest's own top-level `providers`
    object (never a hardcoded {claude, gpt}); the per-provider discovery root is
    mirrored from install-skill-mesh.ps1's $DISCOVERY_SUBDIR. A manifest provider
    with no known discovery root BLOCKS rather than being silently skipped -- a
    silent skip would be a false-clean migration that half-migrated the home.

.PARAMETER Home
    Consumer home to migrate. Required in every mode. Backed by $TargetHome
    ($HOME is a protected automatic variable and cannot be bound as a parameter).

.PARAMETER BackupDir
    External backup root, OUTSIDE the consumer home. Required in every mode: it
    locates the transaction folder. -Apply without it FAILS before any mutation.

.PARAMETER DistDir
    Pre-built dist root (containing claude/ and gpt/) from
    tools/build-distributions.ps1. Required for dry-run, -Apply, and -Resume.

.PARAMETER Apply / -Resume / -Rollback
    Mutually exclusive. Omit all three for the safe preview. -Resume and -Rollback
    require -MigrationId.

.PARAMETER Format
    'text' (default) or 'json'. In dry run, 'json' emits exactly one MigrationPlan.

.NOTES
    Exit codes: 0 success; 1 operational failure with the home left clean
    (rollback completed, or nothing was mutated); 2 blocked / unsafe precondition
    / refused incomplete transaction, always PRE-MUTATION; 3 rollback itself
    failed -- the home is mixed and the retained backup is the recovery source.

    ASCII-only, no BOM (PowerShell 5.1 reads a no-BOM .ps1 as ANSI/cp1252).
#>

[CmdletBinding()]
param(
    # NOT [Parameter(Mandatory)]: a mandatory parameter PROMPTS when absent in an
    # interactive host. This command must never prompt, so every requirement is
    # validated manually and exits 2.
    [Alias('Home', 'Destination')]
    [string]$TargetHome = '',

    [string]$DistDir = '',

    [string]$BackupDir = '',

    [switch]$Apply,

    [switch]$Resume,

    [switch]$Rollback,

    [string]$MigrationId = '',

    [ValidateSet('text', 'json')]
    [string]$Format = 'text'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -- Path resolution ----------------------------------------------------------

$TOOLS_DIR = $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $TOOLS_DIR
$PATH_GUARD = Join-Path $REPO_ROOT 'runtime\path-guard.ps1'
$PROVENANCE = Join-Path $TOOLS_DIR 'skill-mesh-provenance.ps1'
$TRANSACTION = Join-Path $TOOLS_DIR 'skill-mesh-transaction.ps1'
$MANIFEST_REL = 'config/skill-manifest.json'
$MANIFEST_PATH = Join-Path $REPO_ROOT 'config\skill-manifest.json'

# Dot-source the three shared, single-source-of-truth libraries (no -Path, so only
# their functions load).
. $PATH_GUARD
. $PROVENANCE
. $TRANSACTION

$UTF8_NO_BOM = New-Object System.Text.UTF8Encoding($false)

$SCHEMA_VERSION = 1

# Provider -> discovery root, mirrored from install-skill-mesh.ps1 $DISCOVERY_SUBDIR.
# The provider VOCABULARY is read from the manifest; this map only says where a
# known provider's tree lives.
$DISCOVERY_SUBDIR = @{
    'claude' = '.claude/skills'
    'gpt'    = '.github/skills'
}
# The pre-Step-44 GPT target. Copilot does not discover it, so any generated tree
# found here is superseded and gets RETIRED into the backup.
$RETIRED_ROOT_REL = '.copilot/skills'

$LEDGER_NAME = '.skill-mesh-install.json'
$LEDGER_VERSION = 1

$PLAN_FILE = 'plan.json'
$BACKUP_MANIFEST_FILE = 'backup-manifest.json'
$JOURNAL_FILE = 'journal.jsonl'
$PAYLOAD_DIR = 'payload'

# -- Diagnostics / exits ------------------------------------------------------

function Write-Diag([string]$message) {
    [Console]::Error.WriteLine("migrate-legacy-install: $message")
}

function Write-Outcome([string]$message) {
    # The human-readable outcome line. Under -Format json it is routed to STDERR:
    # stdout must carry exactly ONE JSON document, and a Write-Host line prepended
    # to it makes the stream unparseable for the caller the json format exists for.
    if ($Format -eq 'json') {
        [Console]::Error.WriteLine("migrate-legacy-install: $message")
    } else {
        Write-Host "migrate-legacy-install: $message"
    }
}

function Exit-Blocked([string]$code, [string]$message) {
    # The ONLY exit-2 path: a blocked or unsafe precondition, always before the
    # first mutation.
    Write-Diag "BLOCKED [$code] $message"
    if ($Format -eq 'json') {
        Write-Output (New-ResultDocument 'blocked' $null @(New-Block $code '' $message) | ConvertTo-Json -Depth 6)
    }
    exit 2
}

function New-Block([string]$code, [string]$relPath, [string]$message) {
    return [PSCustomObject]@{ code = $code; rel_path = $relPath; message = $message }
}

function New-ResultDocument([string]$status, [string]$migrationId, $blocked) {
    return [PSCustomObject]@{
        schema_version = $SCHEMA_VERSION
        mode           = $script:RunMode
        migration_id   = $migrationId
        status         = $status
        blocked        = @($blocked)
    }
}

# -- Small helpers ------------------------------------------------------------

function Join-HomePath([string]$relPosix) {
    return (Join-Path $script:HomeAbs ($relPosix -replace '/', '\'))
}

function ConvertTo-HomeRel([string]$absPath) {
    $full = [System.IO.Path]::GetFullPath($absPath)
    if ($full.Equals($script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase)) { return '.' }
    $rel = $full.Substring($script:HomeAbs.Length).TrimStart('\', '/')
    return ($rel -replace '\\', '/')
}

function Test-ContainedInHome([string]$absPath) {
    # Re-resolve through the path guard (which FOLLOWS junctions/symlinks) and
    # assert the real path is still inside the home. Used at scan time AND again
    # immediately before every write, so a junction planted on an ancestor between
    # the two cannot redirect a mutation out of the home.
    try {
        $null = Resolve-SafePath -Path $absPath -AllowedRoots @($script:HomeAbs)
        return $true
    } catch {
        return $false
    }
}

function Read-FileHead([string]$absPath, [int]$maxBytes = 8192) {
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

function Test-FileHasMarker([string]$absPath) {
    # Ownership authority: the ANCHORED shared parser, never a substring scan.
    if (-not (Test-Path -LiteralPath $absPath -PathType Leaf)) { return $false }
    try {
        $head = Read-FileHead $absPath 8192
    } catch {
        return $false
    }
    return (Test-SkillMeshProvenance $head)
}

function New-DirectoryFor([string]$absFilePath) {
    $dir = Split-Path -Parent $absFilePath
    if (-not [string]::IsNullOrWhiteSpace($dir) -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

function Get-PayloadAbs([string]$payloadRel) {
    return (Join-Path $script:TxDir ($payloadRel -replace '/', '\'))
}

# -- Manifest -----------------------------------------------------------------

function Read-Manifest {
    # @{ skills = <name -> @{status; single_profile; providers = @(slug)}>;
    #    providers = @(slug) }.
    # `providers` is the CLOSED vocabulary, read from the manifest's own top-level
    # object rather than duplicated here, so a provider added in a later phase is
    # honored without editing this tool.
    if (-not (Test-Path -LiteralPath $MANIFEST_PATH -PathType Leaf)) {
        Exit-Blocked 'MANIFEST_UNREADABLE' "manifest not found at $MANIFEST_REL (relative to the skill-mesh checkout)"
    }
    try {
        $raw = [System.IO.File]::ReadAllText($MANIFEST_PATH, [System.Text.Encoding]::UTF8)
        $parsed = $raw | ConvertFrom-Json
    } catch {
        Exit-Blocked 'MANIFEST_UNREADABLE' "$MANIFEST_REL is unparseable ($($_.Exception.GetType().Name))"
    }
    $map = @{}
    foreach ($s in @($parsed.skills)) {
        $name = [string](Get-SkillMeshTxField $s 'name')
        if ([string]::IsNullOrWhiteSpace($name)) { continue }
        $status = [string](Get-SkillMeshTxField $s 'status')
        $coreValue = Get-SkillMeshTxField $s 'core'
        $single = ($status -eq 'provider-native') -or ($null -eq $coreValue)
        $adapters = @()
        $provObj = Get-SkillMeshTxField $s 'providers'
        if ($null -ne $provObj) {
            foreach ($p in @($provObj.PSObject.Properties)) {
                if (-not [string]::IsNullOrWhiteSpace([string]$p.Value)) { $adapters += $p.Name }
            }
        }
        $map[$name] = @{ status = $status; single_profile = $single; adapters = @($adapters) }
    }
    $providers = @()
    $provProp = $parsed.PSObject.Properties['providers']
    if ($null -ne $provProp -and $null -ne $provProp.Value) {
        $providers = @($provProp.Value.PSObject.Properties | ForEach-Object { $_.Name } | Sort-Object)
    }
    if ($providers.Count -eq 0) {
        Exit-Blocked 'MANIFEST_UNREADABLE' "$MANIFEST_REL declares no providers; discovery roots cannot be resolved"
    }
    return @{ skills = $map; providers = @($providers) }
}

function Resolve-KnownProvider([string]$value) {
    # Return the manifest's OWN slug for a consumer-supplied provider token, or
    # $null. ORDINAL (not -contains, which is culture-aware and would accept a
    # token padded with Unicode-ignorable characters) but case-INSENSITIVE (the
    # installer's ValidateSet accepts -Provider CLAUDE and writes that spelling
    # verbatim into the ledger). Same discipline as inspect-host-install.ps1.
    if ([string]::IsNullOrEmpty($value)) { return $null }
    foreach ($p in $script:KnownProviders) {
        if ([string]::Equals($p, $value, [System.StringComparison]::OrdinalIgnoreCase)) { return $p }
    }
    return $null
}

function Get-DirEligibility([string]$name, [bool]$hasSkillMd) {
    # THE classification cascade, identical to inspect-host-install.ps1's
    # Get-RootAnalysis. Absence from the manifest is the SOLE criterion for
    # consumer-only, so a consumer's own skill can never be classified managed and
    # overwritten.
    if ($script:ManifestMap.ContainsKey($name)) { return 'managed' }
    if ($name -eq '_shared' -and (-not $hasSkillMd)) { return 'core-holder' }
    if ($hasSkillMd) { return 'consumer-only' }
    return 'foreign'
}

# -- Release identity ---------------------------------------------------------

function Get-GitValue([string[]]$GitArgs) {
    # Release identity is BEST-EFFORT: a checkout without git, or without a tag,
    # records $null rather than failing the migration. The value is only ever an
    # audit record and an equality check between the plan and the backup manifest,
    # so a null on both sides is still a correct comparison.
    # $ErrorActionPreference is function-scoped here: git legitimately writes to
    # stderr (e.g. `describe --exact-match` with no tag) and 'Stop' would turn that
    # into a terminating NativeCommandError.
    $ErrorActionPreference = 'Continue'
    try {
        $all = @('-C', $REPO_ROOT) + @($GitArgs)
        $out = & git @all 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
        $text = ([string](@($out) | Select-Object -First 1)).Trim()
        if ([string]::IsNullOrWhiteSpace($text)) { return $null }
        return $text
    } catch {
        return $null
    }
}

function Get-SourceRelease([string]$distAbs) {
    # commit/tag identify the release candidate; dist_checksums pin the exact bytes
    # the transaction will install. Recorded identically in the plan and in the
    # backup manifest and compared for equality on resume/rollback, so a backup can
    # never be replayed against a different build.
    $commit = Get-GitValue @('rev-parse', 'HEAD')
    if ($null -ne $commit -and $commit -notmatch '\A[0-9a-f]{40}\z') { $commit = $null }
    $tag = Get-GitValue @('describe', '--tags', '--exact-match')
    $checksums = [ordered]@{}
    foreach ($f in @(Get-ChildItem -LiteralPath $distAbs -Recurse -File | Sort-Object -Property FullName)) {
        $rel = ($f.FullName.Substring($distAbs.Length).TrimStart('\', '/') -replace '\\', '/')
        $checksums[$rel] = (Get-SkillMeshFileSha256 $f.FullName)
    }
    return [PSCustomObject]@{
        commit         = $commit
        tag            = $tag
        dist_checksums = [PSCustomObject]$checksums
    }
}

# -- Home scan ----------------------------------------------------------------

function Get-RootScan([string]$rootRel) {
    # Classify one discovery-root-shaped tree. Returns
    # @{ blocked; preserve; managed_files } where every entry is a home-relative
    # POSIX path. Purely read-only.
    $result = @{ blocked = @(); preserve = @(); managed_files = @() }
    $rootAbs = Join-HomePath $rootRel
    if (-not (Test-Path -LiteralPath $rootAbs)) { return $result }
    if (-not (Test-ContainedInHome $rootAbs)) {
        $result.blocked += New-Block 'UNSAFE_LINK' $rootRel `
            'the discovery root resolves outside the consumer home (junction or symlink escape); refusing to migrate through it'
        return $result
    }
    if (-not (Test-Path -LiteralPath $rootAbs -PathType Container)) {
        $result.blocked += New-Block 'FOREIGN_FILE' $rootRel `
            'the discovery root path exists but is a FILE, not a directory'
        return $result
    }

    foreach ($child in @(Get-ChildItem -LiteralPath $rootAbs -Force | Sort-Object -Property Name)) {
        $childRel = "$rootRel/$($child.Name)"
        if (-not $child.PSIsContainer) {
            $result.blocked += New-Block 'FOREIGN_FILE' $childRel `
                'a loose file sits directly under the discovery root; skill-mesh only owns per-skill directories'
            continue
        }
        if (-not (Test-ContainedInHome $child.FullName)) {
            $result.blocked += New-Block 'UNSAFE_LINK' $childRel `
                'this directory resolves outside the consumer home (junction or symlink escape)'
            continue
        }
        $hasSkillMd = Test-Path -LiteralPath (Join-Path $child.FullName 'SKILL.md') -PathType Leaf
        $eligibility = Get-DirEligibility $child.Name $hasSkillMd
        if ($eligibility -eq 'foreign') {
            $result.blocked += New-Block 'FOREIGN_FILE' $childRel `
                ('an unknown directory: not a manifest skill, no SKILL.md, and not the _shared core-holder. ' +
                 'It is never adopted, overwritten, or deleted -- remove or relocate it, then re-run.')
            continue
        }
        foreach ($f in @(Get-ChildItem -LiteralPath $child.FullName -Recurse -File -Force |
                Sort-Object -Property FullName)) {
            if (-not (Test-ContainedInHome $f.FullName)) {
                $result.blocked += New-Block 'UNSAFE_LINK' "$childRel/..." `
                    'a file inside this directory resolves outside the consumer home'
                continue
            }
            $rel = ConvertTo-HomeRel $f.FullName
            if ($eligibility -eq 'managed') {
                $result.managed_files += $rel
            } else {
                # consumer-only / core-holder: byte-untouched, recorded by path and
                # hash only, NEVER payload-copied.
                $result.preserve += $rel
            }
        }
    }
    return $result
}

# -- Plan construction --------------------------------------------------------

function New-MigrationPlan([string]$distAbs, [string]$backupAbs, [string]$migrationId) {
    $blocked = @()
    $preserveRels = @()
    $managedRels = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)

    # -- Which providers does this migration bind? --
    $providerRoots = [ordered]@{}
    foreach ($p in $script:KnownProviders) {
        if (-not $DISCOVERY_SUBDIR.ContainsKey($p)) {
            $blocked += New-Block 'UNKNOWN_PROVIDER_ROOT' '' `
                ("the manifest declares provider '$p' but this tool knows no discovery root for it; " +
                 'migrating would leave that profile uninstalled')
            continue
        }
        $providerRoots[$p] = $DISCOVERY_SUBDIR[$p]
    }

    # -- Scan the consumer home --
    foreach ($p in @($providerRoots.Keys)) {
        $scan = Get-RootScan $providerRoots[$p]
        $blocked += @($scan.blocked)
        $preserveRels += @($scan.preserve)
        foreach ($r in @($scan.managed_files)) { [void]$managedRels.Add($r) }
    }
    $retiredScan = Get-RootScan $RETIRED_ROOT_REL
    $blocked += @($retiredScan.blocked)
    $preserveRels += @($retiredScan.preserve)
    $retiredManaged = @($retiredScan.managed_files)

    # -- Generated install targets --
    $installs = @()
    $distSkills = @{}      # "<provider>/<skill>" -> $true
    foreach ($p in @($providerRoots.Keys)) {
        $profileDir = Join-Path $distAbs $p
        if (-not (Test-Path -LiteralPath $profileDir -PathType Container)) { continue }
        $profileAbs = [System.IO.Path]::GetFullPath($profileDir)
        foreach ($f in @(Get-ChildItem -LiteralPath $profileAbs -Recurse -File | Sort-Object -Property FullName)) {
            $relFromProfile = ($f.FullName.Substring($profileAbs.Length).TrimStart('\', '/') -replace '\\', '/')
            $skill = @($relFromProfile.Split('/'))[0]
            if (-not $script:ManifestMap.ContainsKey($skill)) {
                $blocked += New-Block 'FOREIGN_FILE' "$p/$relFromProfile" `
                    ("the supplied distribution contains skill directory '$skill', which is not a record in " +
                     "$MANIFEST_REL; refusing to install an unmanifested tree")
                continue
            }
            $distSkills["$p/$skill"] = $true
            $targetRel = "$($providerRoots[$p])/$relFromProfile"
            $targetAbs = Join-HomePath $targetRel
            if (-not (Test-ContainedInHome $targetAbs)) {
                $blocked += New-Block 'UNSAFE_LINK' $targetRel `
                    'the install target resolves outside the consumer home (junction or symlink escape)'
                continue
            }
            $installs += [PSCustomObject]@{
                provider  = $p
                skill     = $skill
                rel_path  = $targetRel
                source    = $f.FullName
                pre_hash  = (Get-SkillMeshFileSha256 $targetAbs)
                post_hash = (Get-SkillMeshFileSha256 $f.FullName)
            }
        }
    }

    # -- Both-profile completeness. A skill the manifest gives an adapter for MUST
    # be present in that provider's profile. A provider-native skill (core: null)
    # declares no gpt adapter, so its absence from the GPT profile can never fire
    # here -- that is the carve-out, expressed as a manifest fact rather than a
    # special case.
    $seenSkills = @($installs | ForEach-Object { $_.skill } | Sort-Object -Unique)
    foreach ($skill in $seenSkills) {
        foreach ($p in @($providerRoots.Keys)) {
            if (-not (Test-SkillMeshTxMember @($script:ManifestMap[$skill].adapters) $p)) { continue }
            if (-not $distSkills.ContainsKey("$p/$skill")) {
                $blocked += New-Block 'MISSING_PROFILE' "$p/$skill" `
                    ("the manifest declares a '$p' adapter for skill '$skill' but the supplied distribution " +
                     "has no $p profile for it; both profiles must migrate as one transaction")
            }
        }
    }

    # -- Retire set: our OWN superseded generated files. --
    $installRels = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($i in $installs) { [void]$installRels.Add($i.rel_path) }

    $retires = @()
    foreach ($rel in @($retiredManaged)) {
        # The retired .copilot/skills target: every marker-bearing file there is a
        # pre-retarget install Copilot cannot see. A NON-marker file is operator
        # content and is left strictly alone.
        if (Test-FileHasMarker (Join-HomePath $rel)) { $retires += $rel }
    }
    foreach ($rel in @($managedRels)) {
        if ($installRels.Contains($rel)) { continue }
        # A stale generated file inside a managed skill dir (a skill or file the
        # current distribution no longer emits). Only OUR files are retired; a
        # hand-authored file inside a managed dir is left untouched.
        if (Test-FileHasMarker (Join-HomePath $rel)) { $retires += $rel }
    }
    $retires = @($retires | Sort-Object -Unique)

    # -- Ledger rewrite --
    $ledgerRel = $LEDGER_NAME
    $ledgerAbs = Join-HomePath $ledgerRel
    $createdDirs = Get-CreatedDirs $installs
    $ledgerJson = New-LedgerJson $installs $providerRoots $createdDirs (Get-PriorCreatedDirs $ledgerAbs)
    $ledgerPostHash = Get-SkillMeshStringSha256 $ledgerJson

    # -- Assemble the ordered action set.
    # backup -> preserve -> retire -> install -> ledger. The ledger is
    # LAST-sequenced so reverse-order rollback reverts it FIRST: no window ever
    # leaves a new ledger indexing already-reverted files.
    $actions = @()
    $seq = 0

    # backup: the pre-image of every overwriting install, plus the prior ledger.
    # A retire produces its own payload during the move, so it needs no separate
    # backup action; both kinds are recorded in BackupManifest.original_files.
    foreach ($i in @($installs | Where-Object { $null -ne $_.pre_hash })) {
        $actions += [PSCustomObject]@{
            seq = $seq; action = 'backup'; rel_path = $i.rel_path; provider = $i.provider
            eligibility = 'managed'; pre_hash = $i.pre_hash; post_hash = $i.pre_hash
            source = ''; backup_payload = "$PAYLOAD_DIR/$($i.rel_path)"
        }
        $seq++
    }
    $ledgerPreHash = Get-SkillMeshFileSha256 $ledgerAbs
    if ($null -ne $ledgerPreHash) {
        $actions += [PSCustomObject]@{
            seq = $seq; action = 'backup'; rel_path = $ledgerRel; provider = ''
            eligibility = 'managed'; pre_hash = $ledgerPreHash; post_hash = $ledgerPreHash
            source = ''; backup_payload = "$PAYLOAD_DIR/$ledgerRel"
        }
        $seq++
    }

    foreach ($rel in @($preserveRels | Sort-Object -Unique)) {
        $h = Get-SkillMeshFileSha256 (Join-HomePath $rel)
        $actions += [PSCustomObject]@{
            seq = $seq; action = 'preserve'; rel_path = $rel; provider = ''
            eligibility = 'preserved'; pre_hash = $h; post_hash = $h
            source = ''; backup_payload = ''
        }
        $seq++
    }

    foreach ($rel in @($retires)) {
        $actions += [PSCustomObject]@{
            seq = $seq; action = 'retire'; rel_path = $rel; provider = ''
            eligibility = 'managed'; pre_hash = (Get-SkillMeshFileSha256 (Join-HomePath $rel))
            post_hash = $null; source = ''; backup_payload = "$PAYLOAD_DIR/$rel"
        }
        $seq++
    }

    foreach ($i in $installs) {
        $actions += [PSCustomObject]@{
            seq = $seq; action = 'install'; rel_path = $i.rel_path; provider = $i.provider
            eligibility = 'managed'; pre_hash = $i.pre_hash; post_hash = $i.post_hash
            source = $i.source
            backup_payload = $(if ($null -ne $i.pre_hash) { "$PAYLOAD_DIR/$($i.rel_path)" } else { '' })
        }
        $seq++
    }

    $actions += [PSCustomObject]@{
        seq = $seq; action = 'ledger'; rel_path = $ledgerRel; provider = ''
        eligibility = 'managed'; pre_hash = $ledgerPreHash; post_hash = $ledgerPostHash
        source = ''; backup_payload = $(if ($null -ne $ledgerPreHash) { "$PAYLOAD_DIR/$ledgerRel" } else { '' })
    }

    return [PSCustomObject]@{
        schema_version = $SCHEMA_VERSION
        migration_id   = $migrationId
        source_release = (Get-SourceRelease $distAbs)
        consumer_home  = $script:HomeAbs
        backup_dir     = $backupAbs
        created_dirs   = @($createdDirs)
        ledger_json    = $ledgerJson
        actions        = @($actions)
        blocked        = @($blocked | Sort-Object -Property code, rel_path)
    }
}

function Get-SkillMeshStringSha256([string]$text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $sha.ComputeHash($UTF8_NO_BOM.GetBytes($text))
    } finally {
        $sha.Dispose()
    }
    return ([System.BitConverter]::ToString($bytes) -replace '-', '').ToLowerInvariant()
}

function Get-CreatedDirs($installs) {
    # ONLY-OWN-WHAT-YOU-CREATE: a directory is recorded only when it does not
    # already exist at plan time, so an operator-owned .claude/ or .github/ is
    # never adopted (and therefore never removed by an ownership-safe uninstall).
    $set = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($i in @($installs)) {
        $segments = @($i.rel_path.Split('/'))
        $current = ''
        for ($k = 0; $k -lt $segments.Count - 1; $k++) {
            $current = $(if ($current -eq '') { $segments[$k] } else { "$current/$($segments[$k])" })
            if (-not (Test-Path -LiteralPath (Join-HomePath $current))) { [void]$set.Add($current) }
        }
    }
    return , @(@($set) | Sort-Object)
}

function Get-PriorCreatedDirs([string]$ledgerAbs) {
    # provider -> the created_dirs the PRIOR ledger already claimed. Read
    # defensively: a corrupt or old-shape ledger yields an empty map, never a throw.
    $map = @{}
    $parsed = Read-JsonFile $ledgerAbs
    if ($null -eq $parsed) { return $map }
    $installs = Get-SkillMeshTxField $parsed 'installs'
    if ($null -eq $installs -or -not ($installs -is [System.Management.Automation.PSCustomObject])) {
        return $map
    }
    if ([string](Get-SkillMeshTxField $parsed 'ledger_version') -ne [string]$LEDGER_VERSION) {
        return $map
    }
    foreach ($p in @($installs.PSObject.Properties)) {
        $slug = Resolve-KnownProvider $p.Name
        if ($null -eq $slug) { continue }
        $dirs = @(Get-SkillMeshTxField $p.Value 'created_dirs' @()) |
            Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }
        $map[$slug] = @($dirs)
    }
    return $map
}

function New-LedgerJson($installs, $providerRoots, $createdDirs, $priorCreatedDirs) {
    # The rewritten ownership ledger. It indexes ONLY migration-installed managed
    # files: no preserved consumer-only skill and no _shared core-holder ever
    # appears here, so a later ownership-safe uninstall cannot delete them.
    # Shape and serialization are byte-compatible with install-skill-mesh.ps1's
    # writer, so its uninstall path reads this ledger unchanged.
    $installsObj = [PSCustomObject]@{}
    foreach ($p in @($providerRoots.Keys)) {
        $subdir = $providerRoots[$p]
        $owned = @(@($installs | Where-Object { $_.provider -eq $p } | ForEach-Object { $_.rel_path }) |
            Sort-Object -Unique)
        $mine = @($createdDirs | Where-Object {
            $_ -eq $subdir -or $_.StartsWith("$subdir/") -or $subdir.StartsWith("$_/") })
        # UNIONED with the prior entry, exactly as install-skill-mesh.ps1 does, so a
        # RERUN produces a byte-identical ledger: the second run creates none of the
        # directories the first one did, and without the union its created_dirs
        # would silently shrink to empty (idempotency broken, and a later
        # ownership-safe uninstall would leave the dirs it made behind).
        $prior = @()
        if ($null -ne $priorCreatedDirs -and $priorCreatedDirs.ContainsKey($p)) {
            $prior = @($priorCreatedDirs[$p])
        }
        $dirs = @(@($mine + $prior) | Sort-Object -Unique)
        $entry = [PSCustomObject]@{
            provider         = $p
            discovery_subdir = $subdir
            owned_files      = @($owned)
            created_dirs     = @($dirs)
        }
        $installsObj | Add-Member -NotePropertyName $p -NotePropertyValue $entry -Force
    }
    $ledger = [PSCustomObject]@{
        tool           = 'skill-mesh'
        ledger_version = $LEDGER_VERSION
        installs       = $installsObj
    }
    return ($ledger | ConvertTo-Json -Depth 8)
}

# -- Backup manifest ----------------------------------------------------------

function New-BackupManifest($plan) {
    $originals = @()
    foreach ($a in @($plan.actions)) {
        if ($a.action -ne 'retire' -and -not ($a.action -eq 'install' -and $null -ne $a.pre_hash)) { continue }
        $abs = Join-HomePath $a.rel_path
        $size = 0
        if (Test-Path -LiteralPath $abs -PathType Leaf) { $size = (Get-Item -LiteralPath $abs -Force).Length }
        $originals += [PSCustomObject]@{
            rel_path       = $a.rel_path
            size           = $size
            sha256         = $a.pre_hash
            backup_payload = $a.backup_payload
        }
    }
    $preserved = @()
    foreach ($a in @($plan.actions | Where-Object { $_.action -eq 'preserve' })) {
        # Path + hash ONLY. Copying a byte-untouched consumer tree would duplicate
        # private content into a backup that can never need to restore it.
        $preserved += [PSCustomObject]@{ rel_path = $a.rel_path; sha256 = $a.pre_hash }
    }
    $installed = @()
    foreach ($a in @($plan.actions | Where-Object { $_.action -eq 'install' })) {
        $installed += [PSCustomObject]@{ rel_path = $a.rel_path; sha256 = $a.post_hash }
    }
    $ledgerAction = @($plan.actions | Where-Object { $_.action -eq 'ledger' })[0]
    $originalLedger = $null
    if ($null -ne $ledgerAction.pre_hash) {
        $originalLedger = [PSCustomObject]@{
            backup_payload = $ledgerAction.backup_payload
            sha256         = $ledgerAction.pre_hash
        }
    }
    return [PSCustomObject]@{
        schema_version = $SCHEMA_VERSION
        migration_id   = $plan.migration_id
        created_utc    = (Get-SkillMeshTxUtcNow)
        source_release = $plan.source_release
        original_files = @($originals)
        preserved_files = @($preserved)
        original_ledger = $originalLedger
        installed_files = @($installed)
        status         = 'prepared'
    }
}

function Write-JsonFile([string]$absPath, $object) {
    New-DirectoryFor $absPath
    $json = ($object | ConvertTo-Json -Depth 12)
    $tmp = "$absPath.$PID.tmp"
    [System.IO.File]::WriteAllText($tmp, $json, $UTF8_NO_BOM)
    Move-Item -LiteralPath $tmp -Destination $absPath -Force
}

function Read-JsonFile([string]$absPath) {
    if (-not (Test-Path -LiteralPath $absPath -PathType Leaf)) { return $null }
    try {
        return ([System.IO.File]::ReadAllText($absPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json)
    } catch {
        return $null
    }
}

# -- Transaction action handlers ----------------------------------------------

function Get-ActionTargetAbs($action) {
    return (Join-HomePath $action.rel_path)
}

function Invoke-ActionMutate($action) {
    $targetAbs = Get-ActionTargetAbs $action
    switch ($action.action) {
        'preserve' {
            # Audit-only: never mutates. The engine's post-hash check still runs,
            # so a preserved file that changed under us aborts the transaction.
            return
        }
        'backup' {
            $payload = Get-PayloadAbs $action.backup_payload
            if ((Get-SkillMeshFileSha256 $payload) -eq $action.post_hash) { return }
            New-DirectoryFor $payload
            Copy-Item -LiteralPath $targetAbs -Destination $payload -Force
            return
        }
        'retire' {
            # Copy-then-delete, never a bare move: at every instant the bytes exist
            # in at least one place, so a crash between the two is recoverable in
            # either direction.
            $payload = Get-PayloadAbs $action.backup_payload
            if ((Get-SkillMeshFileSha256 $payload) -ne $action.pre_hash) {
                New-DirectoryFor $payload
                Copy-Item -LiteralPath $targetAbs -Destination $payload -Force
            }
            if (Test-Path -LiteralPath $targetAbs -PathType Leaf) {
                Remove-Item -LiteralPath $targetAbs -Force
            }
            return
        }
        'install' {
            # Re-resolve containment on the parent AND the target immediately
            # before the write (junction-on-ancestor TOCTOU), exactly as the
            # installer does.
            $parent = Split-Path -Parent $targetAbs
            if (-not (Test-ContainedInHome $parent)) {
                throw "migrate-legacy-install: SECURITY -- '$($action.rel_path)' parent resolves outside the consumer home."
            }
            New-DirectoryFor $targetAbs
            if (-not (Test-ContainedInHome $targetAbs)) {
                throw "migrate-legacy-install: SECURITY -- '$($action.rel_path)' resolves outside the consumer home."
            }
            Copy-Item -LiteralPath $action.source -Destination $targetAbs -Force
            return
        }
        'ledger' {
            New-DirectoryFor $targetAbs
            $tmp = "$targetAbs.$PID.tmp"
            [System.IO.File]::WriteAllText($tmp, $script:LedgerJson, $UTF8_NO_BOM)
            Move-Item -LiteralPath $tmp -Destination $targetAbs -Force
            return
        }
    }
    throw "migrate-legacy-install: unknown action kind '$($action.action)'."
}

function Invoke-ActionUndo($action) {
    $targetAbs = Get-ActionTargetAbs $action
    switch ($action.action) {
        'preserve' { return }
        'backup' { return }
        'retire' {
            # An action can be in the undo set having only reached `begin` -- the
            # failure that triggered rollback may have happened before its mutation
            # ran, and a retire is the one kind whose payload is produced BY the
            # mutation (installs and the ledger are backed up during `prepared`).
            # If the target still holds its pre-image, nothing moved: a no-op, not a
            # missing-payload error. Without this a failure injected at a retire seq
            # would land failed_incomplete on a home that was never touched.
            if ([string](Get-SkillMeshFileSha256 $targetAbs) -eq [string]$action.pre_hash) {
                return
            }
            $payload = Get-PayloadAbs $action.backup_payload
            if (-not (Test-Path -LiteralPath $payload -PathType Leaf)) {
                throw "migrate-legacy-install: cannot restore retired '$($action.rel_path)' -- backup payload is missing."
            }
            New-DirectoryFor $targetAbs
            Copy-Item -LiteralPath $payload -Destination $targetAbs -Force
            return
        }
        'install' {
            if ($null -eq $action.pre_hash) {
                # The target did not exist before the migration: remove ONLY what
                # this transaction wrote. A file whose bytes are no longer ours is
                # left in place rather than deleted.
                if (Test-Path -LiteralPath $targetAbs -PathType Leaf) {
                    if ((Get-SkillMeshFileSha256 $targetAbs) -eq $action.post_hash) {
                        Remove-Item -LiteralPath $targetAbs -Force
                    }
                }
                return
            }
            $payload = Get-PayloadAbs $action.backup_payload
            if (-not (Test-Path -LiteralPath $payload -PathType Leaf)) {
                throw "migrate-legacy-install: cannot restore overwritten '$($action.rel_path)' -- backup payload is missing."
            }
            New-DirectoryFor $targetAbs
            Copy-Item -LiteralPath $payload -Destination $targetAbs -Force
            return
        }
        'ledger' {
            if ($null -eq $action.pre_hash) {
                if (Test-Path -LiteralPath $targetAbs -PathType Leaf) {
                    Remove-Item -LiteralPath $targetAbs -Force
                }
                return
            }
            $payload = Get-PayloadAbs $action.backup_payload
            if (-not (Test-Path -LiteralPath $payload -PathType Leaf)) {
                throw "migrate-legacy-install: cannot restore the prior ledger -- backup payload is missing."
            }
            Copy-Item -LiteralPath $payload -Destination $targetAbs -Force
            return
        }
    }
    throw "migrate-legacy-install: unknown action kind '$($action.action)'."
}

function Test-ActionAlreadyApplied($action) {
    # Resume predicate: does this action's POST-state already hold on disk? The
    # answer is read from the filesystem, never from the journal, so a crash
    # between a mutation and its commit flush converges rather than being redone.
    $targetAbs = Get-ActionTargetAbs $action
    $current = Get-SkillMeshFileSha256 $targetAbs
    switch ($action.action) {
        'preserve' { return ([string]$current -eq [string]$action.post_hash) }
        'backup' {
            return ((Get-SkillMeshFileSha256 (Get-PayloadAbs $action.backup_payload)) -eq $action.post_hash)
        }
        'retire' {
            # Target gone AND the payload safely holds its bytes.
            if ($null -ne $current) { return $false }
            return ((Get-SkillMeshFileSha256 (Get-PayloadAbs $action.backup_payload)) -eq $action.pre_hash)
        }
    }
    # install / ledger: the generated bytes are already in place.
    return ([string]$current -eq [string]$action.post_hash)
}

# -- Pre-flight ---------------------------------------------------------------

function Test-Preconditions($plan) {
    # Re-validate EVERY action's precondition hash against current on-disk state.
    # Runs in state `prepared`, before the first mutation, so drift since planning
    # aborts as a true no-op.
    # Uniform across every action kind: pre_hash always describes the same thing
    # (the current state of rel_path in the home), so no kind is exempt.
    $drift = @()
    foreach ($a in @($plan.actions)) {
        $current = Get-SkillMeshFileSha256 (Join-HomePath $a.rel_path)
        if ([string]$current -ne [string]$a.pre_hash) { $drift += $a.rel_path }
    }
    return , @($drift | Sort-Object -Unique)
}

function Test-PostInstall($plan) {
    # Post-install verification: every generated file is present with its expected
    # hash, and every retired path is gone.
    $bad = @()
    foreach ($a in @($plan.actions)) {
        $current = Get-SkillMeshFileSha256 (Join-HomePath $a.rel_path)
        if ($a.action -eq 'install' -or $a.action -eq 'ledger') {
            if ([string]$current -ne [string]$a.post_hash) { $bad += $a.rel_path }
        } elseif ($a.action -eq 'retire') {
            if ($null -ne $current) { $bad += $a.rel_path }
        } elseif ($a.action -eq 'preserve') {
            if ([string]$current -ne [string]$a.pre_hash) { $bad += $a.rel_path }
        }
    }
    return , @($bad)
}

# -- Transaction discovery ----------------------------------------------------

function Get-TransactionDirs([string]$backupAbs) {
    if (-not (Test-Path -LiteralPath $backupAbs -PathType Container)) { return , @() }
    return , @(Get-ChildItem -LiteralPath $backupAbs -Directory -Force |
        Where-Object { Test-SkillMeshMigrationId $_.Name } | Sort-Object -Property Name)
}

function Find-UnresolvedTransaction([string]$backupAbs) {
    # An unresolved transaction is one whose status is NOT applied and NOT
    # rolled_back -- prepared, applying, rolling_back, and the known-mixed
    # failed_incomplete all count. Scoped to THIS consumer home via the
    # transaction's own plan.json.
    # Assigned first, NOT wrapped in @(): Get-TransactionDirs comma-wraps its
    # return (so an empty result stays an array), and @() around such a call
    # produces a one-element array holding the array.
    $txDirs = Get-TransactionDirs $backupAbs
    foreach ($d in $txDirs) {
        $manifest = Read-JsonFile (Join-Path $d.FullName $BACKUP_MANIFEST_FILE)
        if ($null -eq $manifest) { continue }
        $plan = Read-JsonFile (Join-Path $d.FullName $PLAN_FILE)
        if ($null -eq $plan) { continue }
        # NOT $home: $HOME is a protected PowerShell automatic variable and
        # assigning to it throws VariableNotWritable (the same trap
        # install-skill-mesh.ps1 documents for its -Home parameter).
        $planHome = [string](Get-SkillMeshTxField $plan 'consumer_home')
        if (-not $planHome.Equals($script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase)) { continue }
        $status = [string](Get-SkillMeshTxField $manifest 'status')
        if (-not (Test-SkillMeshTxTerminal $status)) {
            return [PSCustomObject]@{ migration_id = $d.Name; status = $status }
        }
    }
    return $null
}

# -- Reporting ----------------------------------------------------------------

function Write-PlanReport($plan) {
    if ($Format -eq 'json') {
        Write-Output ($plan | ConvertTo-Json -Depth 12)
        return
    }
    $counts = @{}
    foreach ($kind in @(Get-SkillMeshTxActionKinds)) {
        $counts[$kind] = @($plan.actions | Where-Object { $_.action -eq $kind }).Count
    }
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("skill-mesh migration plan (schema_version $SCHEMA_VERSION)")
    $lines.Add("migration_id: $($plan.migration_id)")
    $commit = $(if ($null -ne $plan.source_release.commit) { $plan.source_release.commit } else { '-' })
    $lines.Add("source_release: commit=$commit")
    $lines.Add('')
    $lines.Add('actions:')
    foreach ($kind in @(Get-SkillMeshTxActionKinds)) {
        $lines.Add("  $kind : $($counts[$kind])")
    }
    $lines.Add('')
    $lines.Add("blocked ($(@($plan.blocked).Count)):")
    foreach ($b in @($plan.blocked)) {
        $lines.Add("  [$($b.code)] $($b.rel_path) -- $($b.message)")
    }
    Write-Output ($lines -join [Environment]::NewLine)
}

# -- Modes --------------------------------------------------------------------

function Invoke-DryRun([string]$distAbs, [string]$backupAbs) {
    $plan = New-MigrationPlan $distAbs $backupAbs (New-SkillMeshMigrationId)
    Write-PlanReport $plan
    if (@($plan.blocked).Count -gt 0) {
        Write-Diag "the plan is BLOCKED by $(@($plan.blocked).Count) finding(s); nothing was written."
        exit 2
    }
    exit 0
}

function Invoke-Apply([string]$distAbs, [string]$backupAbs) {
    # A bare -Apply never silently adopts a prior transaction.
    $unresolved = Find-UnresolvedTransaction $backupAbs
    if ($null -ne $unresolved) {
        Exit-Blocked 'INCOMPLETE_TRANSACTION' `
            ("an unresolved transaction (MigrationId $($unresolved.migration_id), status " +
             "'$($unresolved.status)') already exists in the backup directory for this home. " +
             "Re-run with -Resume -MigrationId $($unresolved.migration_id) to drive it forward, " +
             "or -Rollback -MigrationId $($unresolved.migration_id) to reverse it. Nothing was written.")
    }

    $migrationId = New-SkillMeshMigrationId
    $plan = New-MigrationPlan $distAbs $backupAbs $migrationId
    if (@($plan.blocked).Count -gt 0) {
        # The PLAN is the report on this path -- its `blocked` array already carries
        # every finding -- so Exit-Blocked's own result document is deliberately NOT
        # emitted here. Two JSON documents on one stdout stream is not parseable
        # output, and -Format json promises exactly one.
        Write-Diag ("BLOCKED [" + [string](@($plan.blocked)[0].code) + "] " +
                    "$(@($plan.blocked).Count) blocking finding(s); refusing to migrate. " +
                    'Nothing was written.')
        Write-PlanReport $plan
        exit 2
    }

    # The backup directory is created only NOW -- after the plan validated clean --
    # so a blocked -Apply is a true no-op in the backup tree as well as in the home.
    $script:TxDir = Join-Path $backupAbs $migrationId
    $script:LedgerJson = $plan.ledger_json
    New-Item -ItemType Directory -Path $script:TxDir -Force | Out-Null

    # ---- PREPARED: materialize backup payloads + the manifest, mutate nothing --
    # No `exit` inside this try: a flow-control exit interacting with catch/finally
    # is exactly the kind of subtlety that hides a bug, so the failure is recorded
    # and acted on after the block.
    $prepError = $null
    try {
        foreach ($a in @($plan.actions | Where-Object { $_.action -eq 'backup' })) {
            $payload = Get-PayloadAbs $a.backup_payload
            New-DirectoryFor $payload
            Copy-Item -LiteralPath (Join-HomePath $a.rel_path) -Destination $payload -Force
            if ((Get-SkillMeshFileSha256 $payload) -ne $a.pre_hash) {
                throw "backup payload for '$($a.rel_path)' did not verify."
            }
        }
        Write-JsonFile (Join-Path $script:TxDir $PLAN_FILE) $plan
        Write-JsonFile (Join-Path $script:TxDir $BACKUP_MANIFEST_FILE) (New-BackupManifest $plan)
    } catch {
        $prepError = $_
    }
    if ($null -ne $prepError) {
        # Nothing in the HOME was touched; discard the half-built transaction so it
        # can never masquerade as an unresolved transaction blocking a retry.
        Remove-TransactionDir
        Write-Diag "preparation failed before any mutation: $($prepError.Exception.Message)"
        Complete-Run 'aborted' $migrationId 1
    }

    $drift = Test-Preconditions $plan
    if (@($drift).Count -gt 0) {
        $sample = ((@($drift) | Select-Object -First 5) -join ', ')
        Remove-TransactionDir
        Exit-Blocked 'PRECONDITION_DRIFT' `
            "$(@($drift).Count) path(s) changed between planning and apply: $sample. Nothing was written."
    }

    Invoke-TransactionRun $plan 'prepared' $false
}

function Remove-TransactionDir {
    if (-not [string]::IsNullOrWhiteSpace($script:TxDir) -and (Test-Path -LiteralPath $script:TxDir)) {
        Remove-Item -LiteralPath $script:TxDir -Recurse -Force
    }
}

function Invoke-TransactionRun($plan, [string]$startStatus, [bool]$isResume) {
    # The single apply path, shared by -Apply and -Resume.
    $manifestPath = Join-Path $script:TxDir $BACKUP_MANIFEST_FILE
    $statusWriter = {
        param($status)
        $m = Read-JsonFile $manifestPath
        if ($null -eq $m) { return }
        $m.status = $status
        Write-JsonFile $manifestPath $m
    }.GetNewClosure()

    $tx = New-SkillMeshTransaction -MigrationId $plan.migration_id `
        -JournalPath (Join-Path $script:TxDir $JOURNAL_FILE) `
        -Status $startStatus -StatusWriter $statusWriter

    $getPre = { param($a) Get-SkillMeshFileSha256 (Join-HomePath $a.rel_path) }
    $getPost = { param($a) Get-SkillMeshFileSha256 (Join-HomePath $a.rel_path) }
    $mutate = { param($a) Invoke-ActionMutate $a }
    $undo = { param($a) Invoke-ActionUndo $a }
    $skip = $null
    if ($isResume) { $skip = { param($a) Test-ActionAlreadyApplied $a } }

    $applyError = $null
    try {
        Invoke-SkillMeshTxApply -Transaction $tx -Actions @($plan.actions) `
            -GetPreHash $getPre -Mutate $mutate -GetPostHash $getPost `
            -Undo $undo -ShouldSkip $skip
    } catch {
        $applyError = $_
    }
    if ($null -ne $applyError) {
        Write-Diag "transaction FAILED: $($applyError.Exception.Message)"
        if ($tx.status -eq 'failed_incomplete') {
            Write-Diag ("ROLLBACK INCOMPLETE -- the consumer home is MIXED. The backup is retained at " +
                        "MigrationId $($plan.migration_id); recover from it manually.")
            Complete-Run 'failed_incomplete' $plan.migration_id 3
        }
        Write-Diag "the consumer home was restored to its pre-migration state (status $($tx.status))."
        Complete-Run $tx.status $plan.migration_id 1
    }

    $bad = Test-PostInstall $plan
    if (@($bad).Count -gt 0) {
        Write-Diag "post-install verification FAILED for $(@($bad).Count) path(s); rolling back."
        $failure = Invoke-SkillMeshTxRollback $tx @($plan.actions) $undo
        if ($null -ne $failure) { Complete-Run 'failed_incomplete' $plan.migration_id 3 }
        Complete-Run 'rolled_back' $plan.migration_id 1
    }

    Remove-EmptiedRetiredDirs $plan
    Write-Outcome ("migration $($plan.migration_id) APPLIED " +
                "($(@($plan.actions | Where-Object { $_.action -eq 'install' }).Count) installed, " +
                "$(@($plan.actions | Where-Object { $_.action -eq 'retire' }).Count) retired, " +
                "$(@($plan.actions | Where-Object { $_.action -eq 'preserve' }).Count) preserved).")
    Complete-Run 'applied' $plan.migration_id 0
}

function Remove-EmptiedRetiredDirs($plan) {
    # Cosmetic, post-transaction, and strictly bounded: remove ONLY directories
    # this transaction emptied by retiring their last file, and only while they are
    # empty. Nothing that still holds a file is ever removed, so preserved and
    # untouched operator content always keeps its directory.
    $dirs = @()
    foreach ($a in @($plan.actions | Where-Object { $_.action -eq 'retire' })) {
        $d = Split-Path -Parent (Join-HomePath $a.rel_path)
        while (-not [string]::IsNullOrWhiteSpace($d) -and
               $d.Length -gt $script:HomeAbs.Length -and
               (Test-ContainedInHome $d)) {
            $dirs += $d
            $d = Split-Path -Parent $d
        }
    }
    $dirs = @($dirs | Sort-Object -Property @{ Expression = { $_.Length } } -Descending -Unique)
    foreach ($d in $dirs) {
        if (-not (Test-Path -LiteralPath $d -PathType Container)) { continue }
        if (@(Get-ChildItem -LiteralPath $d -Force).Count -eq 0) {
            Remove-Item -LiteralPath $d -Force
        }
    }
}

function Complete-Run([string]$status, [string]$migrationId, [int]$code) {
    if ($Format -eq 'json') {
        Write-Output (New-ResultDocument $status $migrationId @() | ConvertTo-Json -Depth 6)
    }
    exit $code
}

function Get-TransactionContext([string]$backupAbs) {
    # Load one transaction's plan + backup manifest, validating the migration id
    # shape, the transaction's containment inside -BackupDir, that it belongs to
    # THIS home, and that the plan and manifest name the same release.
    if (-not (Test-SkillMeshMigrationId $MigrationId)) {
        Exit-Blocked 'INVALID_MIGRATION_ID' `
            '-MigrationId must have the form yyyyMMddTHHmmssZ-<8 lowercase hex>.'
    }
    $txDir = Join-Path $backupAbs $MigrationId
    try {
        $null = Resolve-SafePath -Path $txDir -AllowedRoots @($backupAbs)
    } catch {
        Exit-Blocked 'UNSAFE_LINK' 'the transaction directory resolves outside -BackupDir.'
    }
    if (-not (Test-Path -LiteralPath $txDir -PathType Container)) {
        Exit-Blocked 'UNKNOWN_TRANSACTION' "no transaction $MigrationId exists in the backup directory."
    }
    $plan = Read-JsonFile (Join-Path $txDir $PLAN_FILE)
    $manifest = Read-JsonFile (Join-Path $txDir $BACKUP_MANIFEST_FILE)
    if ($null -eq $plan -or $null -eq $manifest) {
        Exit-Blocked 'UNKNOWN_TRANSACTION' "transaction $MigrationId is missing or has an unparseable plan/manifest."
    }
    $planHome = [string](Get-SkillMeshTxField $plan 'consumer_home')
    if (-not $planHome.Equals($script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase)) {
        Exit-Blocked 'HOME_MISMATCH' "transaction $MigrationId was planned for a different consumer home."
    }
    $planRel = ($plan.source_release | ConvertTo-Json -Depth 6 -Compress)
    $manRel = ($manifest.source_release | ConvertTo-Json -Depth 6 -Compress)
    if ($planRel -ne $manRel) {
        Exit-Blocked 'RELEASE_MISMATCH' "transaction $MigrationId has a plan and backup manifest naming different releases."
    }
    return @{ dir = $txDir; plan = $plan; manifest = $manifest }
}

function Update-ActionSources($plan, [string]$distAbs) {
    # A resume may run from a different -DistDir than the original apply (the
    # release tree can be re-staged), so an install's source is RE-DERIVED from the
    # current -DistDir rather than replayed from the recorded absolute path. The
    # bytes are still pinned: the action's post_hash must match, or the engine's
    # post-mutation verification fails the resume.
    foreach ($a in @($plan.actions | Where-Object { $_.action -eq 'install' })) {
        $provider = [string](Get-SkillMeshTxField $a 'provider')
        if (-not $DISCOVERY_SUBDIR.ContainsKey($provider)) { continue }
        $root = $DISCOVERY_SUBDIR[$provider] + '/'
        $rel = [string](Get-SkillMeshTxField $a 'rel_path')
        if (-not $rel.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) { continue }
        $fromProfile = $rel.Substring($root.Length)
        $a.source = (Join-Path (Join-Path $distAbs $provider) ($fromProfile -replace '/', '\'))
    }
}

function Invoke-Resume([string]$backupAbs, [string]$distAbs) {
    $ctx = Get-TransactionContext $backupAbs
    $script:TxDir = $ctx.dir
    $plan = $ctx.plan
    Update-ActionSources $plan $distAbs
    $script:LedgerJson = [string](Get-SkillMeshTxField $plan 'ledger_json')
    $status = [string](Get-SkillMeshTxField $ctx.manifest 'status')

    if ($status -eq 'applied') {
        Write-Outcome "migration $MigrationId is already applied (no-op)."
        Complete-Run 'applied' $MigrationId 0
    }
    if ($status -eq 'rolled_back') {
        Exit-Blocked 'TRANSACTION_RESOLVED' "migration $MigrationId was rolled back; it cannot be resumed."
    }
    if ($status -eq 'failed_incomplete') {
        Exit-Blocked 'TRANSACTION_RESOLVED' `
            "migration $MigrationId ended failed_incomplete; the home is mixed and requires manual recovery from the retained backup."
    }
    if (-not (Test-SkillMeshTxMember @('prepared', 'applying') $status)) {
        Exit-Blocked 'TRANSACTION_RESOLVED' "migration $MigrationId has an unknown status '$status'."
    }
    Invoke-TransactionRun $plan $status $true
}

function Invoke-Rollback([string]$backupAbs) {
    $ctx = Get-TransactionContext $backupAbs
    $script:TxDir = $ctx.dir
    $plan = $ctx.plan
    $script:LedgerJson = [string](Get-SkillMeshTxField $plan 'ledger_json')
    $status = [string](Get-SkillMeshTxField $ctx.manifest 'status')

    if (Test-SkillMeshTxMember @('rolled_back', 'failed_incomplete') $status) {
        Exit-Blocked 'TRANSACTION_RESOLVED' "migration $MigrationId is already in terminal state '$status'."
    }

    $manifestPath = Join-Path $script:TxDir $BACKUP_MANIFEST_FILE
    $statusWriter = {
        param($s)
        $m = Read-JsonFile $manifestPath
        if ($null -eq $m) { return }
        $m.status = $s
        Write-JsonFile $manifestPath $m
    }.GetNewClosure()
    $tx = New-SkillMeshTransaction -MigrationId $plan.migration_id `
        -JournalPath (Join-Path $script:TxDir $JOURNAL_FILE) `
        -Status $status -StatusWriter $statusWriter

    # The undo set is what the JOURNAL says was BEGUN -- the authoritative record
    # of what may have mutated a target -- intersected with the plan, in apply
    # order. Invoke-SkillMeshTxRollback then walks it in reverse.
    $begun = Get-SkillMeshTxBegunSeqs (Read-SkillMeshTxJournal (Join-Path $script:TxDir $JOURNAL_FILE))
    $undoSet = @(@($plan.actions) | Where-Object { $begun.Contains([int]$_.seq) })

    $undo = { param($a) Invoke-ActionUndo $a }
    $failure = Invoke-SkillMeshTxRollback $tx @($undoSet) $undo
    if ($null -ne $failure) {
        Write-Diag ("ROLLBACK INCOMPLETE -- $($failure.Exception.Message). The backup is retained at " +
                    "MigrationId $($plan.migration_id).")
        Complete-Run 'failed_incomplete' $plan.migration_id 3
    }
    Remove-EmptyCreatedDirs $plan
    Write-Outcome "migration $($plan.migration_id) ROLLED BACK ($(@($undoSet).Count) action(s) reversed)."
    Complete-Run 'rolled_back' $plan.migration_id 0
}

function Remove-EmptyCreatedDirs($plan) {
    # Rollback removes only directories the migration itself created, and only
    # while empty -- so a pre-existing (operator-owned) directory always survives.
    $dirs = @(@(Get-SkillMeshTxField $plan 'created_dirs' @()) |
        Sort-Object -Property @{ Expression = { ([string]$_ -split '/').Count } } -Descending)
    foreach ($rel in $dirs) {
        if ([string]::IsNullOrWhiteSpace([string]$rel)) { continue }
        $abs = Join-HomePath ([string]$rel)
        if (-not (Test-ContainedInHome $abs)) { continue }
        if (-not (Test-Path -LiteralPath $abs -PathType Container)) { continue }
        if (@(Get-ChildItem -LiteralPath $abs -Force).Count -eq 0) {
            Remove-Item -LiteralPath $abs -Force
        }
    }
}

# -- Entry point --------------------------------------------------------------

$script:TxDir = ''
$script:LedgerJson = ''
$script:RunMode = 'dry-run'
if ($Apply) { $script:RunMode = 'apply' }
if ($Resume) { $script:RunMode = 'resume' }
if ($Rollback) { $script:RunMode = 'rollback' }

$modeCount = @($Apply, $Resume, $Rollback | Where-Object { $_ }).Count
if ($modeCount -gt 1) {
    Exit-Blocked 'INVALID_MODE' '-Apply, -Resume, and -Rollback are mutually exclusive.'
}

if ([string]::IsNullOrWhiteSpace($TargetHome)) {
    Exit-Blocked 'INVALID_HOME' '-Home is required (path to the consumer home to migrate).'
}
try {
    $script:HomeAbs = ([System.IO.Path]::GetFullPath($TargetHome)).TrimEnd('\', '/')
} catch {
    Exit-Blocked 'INVALID_HOME' "-Home is not a valid path ($($_.Exception.GetType().Name))."
}
if (-not (Test-Path -LiteralPath $script:HomeAbs -PathType Container)) {
    Exit-Blocked 'INVALID_HOME' '-Home does not exist or is not a directory.'
}

# -BackupDir is required in EVERY mode: it locates the transaction folder, and an
# -Apply without it is exactly the unbacked overwrite this command exists to
# replace. Validated here, before any scan, so the refusal is a true no-op.
if ([string]::IsNullOrWhiteSpace($BackupDir)) {
    Exit-Blocked 'BACKUP_DIR_REQUIRED' `
        '-BackupDir is required (an external backup directory OUTSIDE the consumer home). Nothing was written.'
}
try {
    $backupAbs = ([System.IO.Path]::GetFullPath($BackupDir)).TrimEnd('\', '/')
} catch {
    Exit-Blocked 'BACKUP_DIR_REQUIRED' "-BackupDir is not a valid path ($($_.Exception.GetType().Name))."
}
if ($backupAbs.Equals($script:HomeAbs, [System.StringComparison]::OrdinalIgnoreCase) -or
    $backupAbs.StartsWith($script:HomeAbs + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase)) {
    Exit-Blocked 'BACKUP_DIR_INSIDE_HOME' `
        '-BackupDir must be OUTSIDE the consumer home (a backup inside the tree being migrated is not a backup).'
}

$manifest = Read-Manifest
$script:ManifestMap = $manifest.skills
$script:KnownProviders = @($manifest.providers)

if ($Rollback) {
    if (-not (Test-Path -LiteralPath $backupAbs -PathType Container)) {
        Exit-Blocked 'UNKNOWN_TRANSACTION' 'the backup directory does not exist.'
    }
    Invoke-Rollback $backupAbs
}

# Every remaining mode reads generated bytes.
if ([string]::IsNullOrWhiteSpace($DistDir)) {
    Exit-Blocked 'DIST_DIR_REQUIRED' '-DistDir is required (a dist root built by tools/build-distributions.ps1).'
}
$distAbs = ([System.IO.Path]::GetFullPath($DistDir)).TrimEnd('\', '/')
if (-not (Test-Path -LiteralPath $distAbs -PathType Container)) {
    Exit-Blocked 'DIST_DIR_REQUIRED' '-DistDir does not exist or is not a directory.'
}

if ($Resume) {
    if (-not (Test-Path -LiteralPath $backupAbs -PathType Container)) {
        Exit-Blocked 'UNKNOWN_TRANSACTION' 'the backup directory does not exist.'
    }
    Invoke-Resume $backupAbs $distAbs
}

if ($Apply) {
    Invoke-Apply $distAbs $backupAbs
}

Invoke-DryRun $distAbs $backupAbs
