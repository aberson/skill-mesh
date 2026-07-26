<#
.SYNOPSIS
    skill-router.ps1 -- provider-neutral router: dispatches a skill invocation to
    Claude, GPT/Copilot, or the local code-30b path.

.DESCRIPTION
    Re-homed into the canonical skill-mesh tree (runtime/skill-router.ps1). It
    resolves ALL of its own paths relative to the repository root (its own script
    dir -> repo root); no path here depends on a .claude source root. Config is
    loaded from config/model-mapping.json and config/model-tier-map.json.

    Provider selection (see documentation/architecture.md sections 5-6):
      -Provider auto            Default. Selects via trustworthy host metadata only
                                (CLAUDECODE / CLAUDE_CODE_ENTRYPOINT for Claude;
                                COPILOT_CLI / COPILOT_AGENT_SESSION_ID for GPT).
                                Ambiguous OR unset -> exit 2 (never silently Claude).
      -Provider claude|gpt|local Explicit selection; always honored.
      -Model claude|gpt|local   Deprecated compatibility alias -> maps onto
                                -Provider and emits a deprecation notice.

    Fail-open contract (Framework-Design S.5) is preserved: a router error falls
    back to Claude and emits exit code 2; exit 3 is the only halt (both clouds down
    + no supported local fallback). Provider-selection failures (ambiguous/unset
    -Provider auto) also exit 2 per architecture section 5.3.

    Every filesystem path the router touches (config files, the skill entry point
    derived from the caller-supplied skill name, the telemetry writer, and the
    durable spend-ledger path composed from SKILL_ROUTER_SESSION_ID /
    SKILL_MESH_LEDGER_DIR -- with the session id sanitized to a filename-safe
    token) is validated through runtime/path-guard.ps1 (Resolve-SafePath) so a
    '..'/symlink/junction that escapes the allowed roots cannot be read or written.

.PARAMETER Provider
    'auto' | 'claude' | 'gpt' | 'local'. Default: 'auto'.

.PARAMETER Model
    DEPRECATED compatibility alias: 'claude' | 'gpt' | 'local'. Maps onto -Provider.

.PARAMETER Skill
    Skill name (e.g., 'plan-init', 'build-step'). Kebab-case; no path separators.

.PARAMETER FallbackModel
    Override fallback model: 'claude' | 'local'. Default: 'claude'.

.PARAMETER GptModel
    Explicit GPT model override. When set, tier-peer resolution is skipped.

.PARAMETER DryRun
    Print the routing plan without making API calls or executing any skill.

.PARAMETER SkillInput
    Input payload for the skill (string or path to JSON file).

.EXAMPLE
    powershell -File runtime\skill-router.ps1 -Provider gpt -Skill plan-init -DryRun
    powershell -File runtime\skill-router.ps1 -Provider auto -Skill plan-init
    powershell -File runtime\skill-router.ps1 -Model gpt -Skill plan-init -DryRun   # deprecated alias

.NOTES
    Config ownership:
      - config/model-mapping.json owns per-skill provider/local capability booleans.
      - config/model-tier-map.json owns Claude-tier-to-GPT-peer mapping.

    GPT transport: GitHub Copilot is the sole wired GPT transport. OPENAI_API_KEY is
    optional and acts only as an advisory availability signal -- there is no direct
    OpenAI API call path. Spend ceiling: the value is config only; per-call cost
    metering is not yet wired (Add-SpendEntry has no call sites), so the spend gate
    currently trips only on an unavailable/rejected durable ledger, not on spend.

    Exit codes:
      0 = success on requested provider (no fallback triggered)
      1 = skill execution error (not a router error)
      2 = fallback provider used successfully, OR -Provider auto could not
          resolve a provider (ambiguous/unset host metadata), OR an invalid
          skill name / unsafe path was rejected
      3 = both cloud providers failed AND no supported local fallback exists
#>

[CmdletBinding()]
param(
    [ValidateSet('auto', 'claude', 'gpt', 'local')]
    [string]$Provider = 'auto',

    [ValidateSet('claude', 'gpt', 'local', '')]
    [string]$Model = '',

    [Parameter(Mandatory = $true)]
    [string]$Skill,

    [ValidateSet('claude', 'local')]
    [string]$FallbackModel = 'claude',

    [string]$GptModel = '',

    [switch]$DryRun,

    [string]$SkillInput = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -- Path resolution (repo-root relative) -------------------------------------

$RUNTIME_DIR = $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $RUNTIME_DIR
$CONFIG_DIR = Join-Path $REPO_ROOT 'config'
$SKILLS_ROOT = Join-Path $REPO_ROOT 'skills'
$MODEL_MAPPING_PATH = Join-Path $CONFIG_DIR 'model-mapping.json'
$MODEL_TIER_MAP_PATH = Join-Path $CONFIG_DIR 'model-tier-map.json'
$TELEMETRY_WRITER_PATH = Join-Path $RUNTIME_DIR 'telemetry\telemetry-writer.ps1'

# Load the path-canonicalization guard (defines Resolve-SafePath in this scope).
. (Join-Path $RUNTIME_DIR 'path-guard.ps1')

# -- Constants ----------------------------------------------------------------

$ROUTER_VERSION = '1.3.0'
$SPEND_CEILING_DEFAULT = 5.0
$LOCAL_MODEL_URL_DEFAULT = 'http://localhost:11434'

# Exit codes
$EXIT_SUCCESS = 0
$EXIT_SKILL_ERROR = 1
$EXIT_FALLBACK_USED = 2
$EXIT_ALL_PROVIDERS_FAILED = 3

# -- Helpers ------------------------------------------------------------------

function Write-RouterWarning([string]$Message) {
    Write-Warning "skill-router: WARNING -- $Message"
}

function Write-RouterInfo([string]$Message) {
    Write-Host "skill-router: $Message" -ForegroundColor Cyan
}

function Write-RouterError([string]$Message) {
    Write-Error "skill-router: ERROR -- $Message" -ErrorAction Continue
}

function Read-SafeConfigText([string]$ConfigPath) {
    # Validate the config path stays inside the repo before reading it.
    $safe = Resolve-SafePath -Path $ConfigPath -AllowedRoots @($REPO_ROOT)
    return (Get-Content $safe -Raw)
}

# -- Host-metadata provider detection (-Provider auto) -------------------------

function Resolve-ProviderFromHostMetadata {
    # Approved host-identity markers ONLY (architecture section 5.3). Credentials
    # (ANTHROPIC_API_KEY / OPENAI_API_KEY / tokens) are NOT host identity.
    $claudeDetected = ($env:CLAUDECODE -eq '1') -or
        (-not [string]::IsNullOrWhiteSpace($env:CLAUDE_CODE_ENTRYPOINT))
    $gptDetected = (-not [string]::IsNullOrWhiteSpace($env:COPILOT_CLI)) -or
        (-not [string]::IsNullOrWhiteSpace($env:COPILOT_AGENT_SESSION_ID))

    if ($claudeDetected -and $gptDetected) {
        [Console]::Error.WriteLine(
            'skill-router: ERROR -- -Provider auto is ambiguous: both Claude host markers ' +
            '(CLAUDECODE=1 / CLAUDE_CODE_ENTRYPOINT) and GPT/Copilot host markers ' +
            '(COPILOT_CLI / COPILOT_AGENT_SESSION_ID) are present. Pass -Provider claude|gpt explicitly.'
        )
        exit $EXIT_FALLBACK_USED
    }
    if ($claudeDetected) { return 'claude' }
    if ($gptDetected) { return 'gpt' }

    [Console]::Error.WriteLine(
        'skill-router: ERROR -- -Provider auto could not identify the host: no approved ' +
        'host-identity marker is set (Claude: CLAUDECODE=1 / CLAUDE_CODE_ENTRYPOINT; ' +
        'GPT/Copilot: COPILOT_CLI / COPILOT_AGENT_SESSION_ID). Pass -Provider claude|gpt explicitly.'
    )
    exit $EXIT_FALLBACK_USED
}

# -- GPT tier-peer resolution --------------------------------------------------

$script:GptPeerResolutionPath = ''

function Resolve-GptPeer([string]$ExplicitModel = '') {
    if (-not [string]::IsNullOrWhiteSpace($ExplicitModel)) {
        $script:GptPeerResolutionPath = 'explicit override'
        return $ExplicitModel
    }

    try {
        if (-not (Test-Path $MODEL_TIER_MAP_PATH)) {
            throw 'mapping file not found'
        }

        $tierMapConfig = Read-SafeConfigText $MODEL_TIER_MAP_PATH | ConvertFrom-Json
        if ($null -eq $tierMapConfig.tier_map -or
            $null -eq $tierMapConfig.model_prefix_to_tier -or
            [string]::IsNullOrWhiteSpace([string]$tierMapConfig.default_tier_peer)) {
            throw 'mapping file has an invalid schema'
        }
    } catch {
        [Console]::Error.WriteLine(
            'skill-router: WARNING -- model-tier-map.json missing or unreadable; using default_tier_peer gpt-5.5'
        )
        $script:GptPeerResolutionPath = 'default (mapping unavailable)'
        return 'gpt-5.5'
    }

    $tier = ''
    if (-not [string]::IsNullOrWhiteSpace($env:SKILL_MESH_CLAUDE_TIER)) {
        $candidateTier = $env:SKILL_MESH_CLAUDE_TIER.Trim().ToLowerInvariant()
        if ($tierMapConfig.tier_map.PSObject.Properties.Name -contains $candidateTier) {
            $tier = $candidateTier
            $script:GptPeerResolutionPath = 'env override'
        }
    }

    if ([string]::IsNullOrWhiteSpace($tier)) {
        $claudeModel = $env:SKILL_MESH_CLAUDE_MODEL
        if ([string]::IsNullOrWhiteSpace($claudeModel)) {
            $claudeModel = $env:CLAUDE_MODEL
        }

        if (-not [string]::IsNullOrWhiteSpace($claudeModel)) {
            $normalizedModel = $claudeModel.Trim()
            foreach ($prefixProperty in $tierMapConfig.model_prefix_to_tier.PSObject.Properties) {
                if ($normalizedModel.StartsWith(
                        $prefixProperty.Name,
                        [System.StringComparison]::OrdinalIgnoreCase
                    )) {
                    $tier = [string]$prefixProperty.Value
                    $script:GptPeerResolutionPath = 'model-name match'
                    break
                }
            }
        }
    }

    if ([string]::IsNullOrWhiteSpace($tier)) {
        $tier = 'fable'
        $script:GptPeerResolutionPath = 'default'
    }

    $peer = $tierMapConfig.tier_map.PSObject.Properties[$tier].Value
    if ([string]::IsNullOrWhiteSpace([string]$peer)) {
        $script:GptPeerResolutionPath = 'default'
        return [string]$tierMapConfig.default_tier_peer
    }
    return [string]$peer
}

# -- Spend ceiling -------------------------------------------------------------

function Get-SessionId {
    if ($env:SKILL_ROUTER_SESSION_ID) {
        return $env:SKILL_ROUTER_SESSION_ID
    }
    return $null
}

function Get-SanitizedSessionId {
    # Reduce the session id to a filename-safe token: no path separators, no drive
    # colons, no '..' -- so a hostile SKILL_ROUTER_SESSION_ID can never compose a
    # traversal ledger filename.
    $sessionId = Get-SessionId
    if ([string]::IsNullOrWhiteSpace($sessionId)) {
        return $null
    }
    $sanitized = [regex]::Replace($sessionId, '[^A-Za-z0-9._-]', '_')
    $sanitized = [regex]::Replace($sanitized, '\.\.+', '_')
    $sanitized = $sanitized.Trim('.')
    if ([string]::IsNullOrWhiteSpace($sanitized)) {
        return $null
    }
    if ($sanitized.Length -gt 128) {
        $sanitized = $sanitized.Substring(0, 128)
    }
    return $sanitized
}

function Get-LedgerAllowedRoots {
    # Fixed allowed-root set for the durable spend ledger: the repo, the OS temp
    # tree, and the standard per-user data homes. A SKILL_MESH_LEDGER_DIR that
    # resolves outside all of these is rejected (ledger disabled), never trusted.
    $roots = New-Object System.Collections.Generic.List[string]
    $roots.Add($REPO_ROOT)
    $roots.Add([System.IO.Path]::GetTempPath())
    if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { $roots.Add($env:LOCALAPPDATA) }
    if (-not [string]::IsNullOrWhiteSpace($env:XDG_DATA_HOME)) { $roots.Add($env:XDG_DATA_HOME) }
    if (-not [string]::IsNullOrWhiteSpace($env:HOME)) {
        $roots.Add((Join-Path $env:HOME 'Library'))
        $roots.Add((Join-Path $env:HOME '.local'))
    }
    return $roots.ToArray()
}

function Get-SpendFilePath {
    $sessionId = Get-SanitizedSessionId
    if (-not $sessionId) {
        return $null
    }
    # Null-guarded env dereferences: a fully scrubbed environment falls back to the
    # OS temp tree rather than throwing on Join-Path -Path $null.
    $spendDir = if (-not [string]::IsNullOrWhiteSpace($env:SKILL_MESH_LEDGER_DIR)) {
        $env:SKILL_MESH_LEDGER_DIR
    } elseif (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        Join-Path $env:LOCALAPPDATA 'skill-mesh\spend'
    } elseif (-not [string]::IsNullOrWhiteSpace($env:XDG_DATA_HOME)) {
        Join-Path $env:XDG_DATA_HOME 'skill-mesh/spend'
    } elseif ((-not [string]::IsNullOrWhiteSpace($env:HOME)) -and (Test-Path (Join-Path $env:HOME 'Library'))) {
        Join-Path $env:HOME 'Library/Application Support/skill-mesh/spend'
    } elseif (-not [string]::IsNullOrWhiteSpace($env:HOME)) {
        Join-Path $env:HOME '.local/share/skill-mesh/spend'
    } else {
        Join-Path ([System.IO.Path]::GetTempPath()) 'skill-mesh\spend'
    }
    # Validate the composed ledger path (and any operator-set base) against the
    # fixed roots BEFORE any read/write. Escape -> disable the ledger, never trust.
    $candidate = Join-Path $spendDir "$sessionId.json"
    try {
        return Resolve-SafePath -Path $candidate -AllowedRoots (Get-LedgerAllowedRoots)
    } catch {
        [Console]::Error.WriteLine(
            "skill-router: WARNING -- spend-ledger path '$candidate' resolves outside the allowed roots; disabling durable spend tracking for this session. $($_.Exception.Message)"
        )
        return $null
    }
}

function Get-SpendState {
    $path = Get-SpendFilePath
    if ($path -and (Test-Path $path)) {
        try {
            $state = Get-Content $path -Raw | ConvertFrom-Json
            $state | Add-Member -NotePropertyName ledger_available -NotePropertyValue $true -Force
            return $state
        } catch {
            # Corrupted file -- reset
        }
    }
    $ceiling = if ($env:SKILL_ROUTER_SPEND_CEILING_USD) { [double]$env:SKILL_ROUTER_SPEND_CEILING_USD } else { $SPEND_CEILING_DEFAULT }
    return [PSCustomObject]@{
        session_spend_usd = 0.0
        ceiling_usd       = $ceiling
        calls             = @()
        ledger_available  = [bool]$path
    }
}

function Save-SpendState([PSCustomObject]$State) {
    $path = Get-SpendFilePath
    if (-not $path) {
        throw 'SKILL_ROUTER_SESSION_ID is required before metered GPT execution.'
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force | Out-Null
    $State | ConvertTo-Json -Depth 5 | Set-Content -Path $path -Encoding UTF8 -NoNewline
}

# NOTE: reserved for future live cost metering. This is the ONLY function that
# increments session_spend_usd, and it currently has no call sites -- per-call cost
# is not measured yet, so the accumulated-spend ceiling cannot trip on spend (it
# trips only on an unavailable/rejected ledger; see the spend-check warning below).
# Kept so the ledger schema and the guarded Save path are ready when metering lands.
function Add-SpendEntry([PSCustomObject]$State, [string]$ModelUsed, [int]$PromptTokens, [int]$CompletionTokens, [double]$CostUsd) {
    $entry = [PSCustomObject]@{
        skill             = $Skill
        model             = $ModelUsed
        prompt_tokens     = $PromptTokens
        completion_tokens = $CompletionTokens
        cost_usd          = $CostUsd
        ts                = (Get-Date -Format 'o')
    }
    $State.calls = $State.calls + $entry
    $State.session_spend_usd += $CostUsd
    Save-SpendState $State
    return $State
}

function Test-SpendCeiling([PSCustomObject]$State) {
    return (-not $State.ledger_available) -or ($State.session_spend_usd -ge $State.ceiling_usd)
}

# -- Model mapping -------------------------------------------------------------

function Get-ModelMapping([string]$SkillName) {
    # Read the per-skill capability booleans from config/model-mapping.json.
    $defaults = @{
        'gpt-capable'    = $false
        'claude-capable' = $true
        'local-capable'  = $false
    }

    if (-not (Test-Path $MODEL_MAPPING_PATH)) {
        Write-RouterWarning "model-mapping.json not found at $MODEL_MAPPING_PATH. Using defaults (claude-capable only)."
        return $defaults
    }

    try {
        $config = Read-SafeConfigText $MODEL_MAPPING_PATH | ConvertFrom-Json
        $skillsProp = $config.PSObject.Properties['skills']
        if ($skillsProp) {
            $entry = $skillsProp.Value.PSObject.Properties[$SkillName]
            if ($entry) {
                $v = $entry.Value
                return @{
                    'gpt-capable'    = [bool]$v.gpt
                    'claude-capable' = [bool]$v.claude
                    'local-capable'  = [bool]$v.local
                }
            }
        }
        Write-RouterWarning "Skill '$SkillName' not found in model-mapping.json. Falling back to Claude (safe default)."
        return $defaults
    } catch {
        Write-RouterWarning "Failed to parse model-mapping.json: $_. Using defaults."
        return $defaults
    }
}

# -- Health checks -------------------------------------------------------------

# Advisory health signal ONLY. GitHub Copilot is the sole wired GPT transport
# (Invoke-GPTModel always calls the Copilot endpoint); there is no direct OpenAI
# API transport. OPENAI_API_KEY is therefore optional and, when present, only
# contributes an extra availability probe -- it does not enable an OpenAI call path.
function Test-OpenAIAvailable {
    if (-not $env:OPENAI_API_KEY) {
        Write-RouterWarning "OPENAI_API_KEY not set -- no advisory OpenAI health signal (Copilot is the GPT transport)."
        return $false
    }
    try {
        $response = Invoke-RestMethod `
            -Uri 'https://api.openai.com/v1/models' `
            -Headers @{ Authorization = "Bearer $env:OPENAI_API_KEY" } `
            -Method GET `
            -TimeoutSec 5 `
            -ErrorAction Stop
        return $true
    } catch {
        Write-RouterWarning "OpenAI health check failed: $($_.Exception.Message)"
        return $false
    }
}

function Get-CopilotToken {
    # Token resolution precedence: COPILOT_GITHUB_TOKEN -> GH_TOKEN -> GITHUB_TOKEN -> gh auth token
    if ($env:COPILOT_GITHUB_TOKEN) { return $env:COPILOT_GITHUB_TOKEN }
    if ($env:GH_TOKEN) { return $env:GH_TOKEN }
    if ($env:GITHUB_TOKEN) { return $env:GITHUB_TOKEN }
    try {
        $token = & gh auth token 2>$null
        if ($token -and $token.Trim()) { return $token.Trim() }
    } catch { }
    return $null
}

function Test-CopilotAvailable {
    $token = Get-CopilotToken
    if (-not $token) {
        Write-RouterWarning "No GitHub token found (COPILOT_GITHUB_TOKEN/GH_TOKEN/GITHUB_TOKEN/gh auth token) -- Copilot GPT unavailable."
        return $false
    }
    try {
        $response = Invoke-RestMethod `
            -Uri 'https://api.githubcopilot.com/models' `
            -Headers @{ Authorization = "Bearer $token"; 'Copilot-Integration-Id' = 'skill-mesh-router' } `
            -Method GET `
            -TimeoutSec 8 `
            -ErrorAction Stop
        return $true
    } catch {
        Write-RouterWarning "Copilot health check failed: $($_.Exception.Message)"
        return $false
    }
}

function Test-AnthropicAvailable {
    if ($env:ANTHROPIC_API_KEY) {
        return $true
    }
    Write-RouterInfo "Using Claude native execution path (no ANTHROPIC_API_KEY; VS Code/Claude Code skill pipeline)"
    return $true
}

function Test-LocalModelAvailable {
    $url = if ($env:LOCAL_MODEL_URL) { $env:LOCAL_MODEL_URL } else { $LOCAL_MODEL_URL_DEFAULT }
    try {
        Invoke-RestMethod -Uri "$url/api/tags" -Method GET -TimeoutSec 3 -ErrorAction Stop | Out-Null
        return $true
    } catch {
        Write-RouterWarning "Local model health check failed at $url/api/tags: $($_.Exception.Message)"
        return $false
    }
}

# -- Skill path resolution ------------------------------------------------------

function Resolve-SkillEntryPoint([string]$SkillName, [string]$ModelVariant) {
    # Canonical neutral layout: skills/<name>/providers/{gpt,claude}.md + core.md.
    $candidate = $null
    switch ($ModelVariant) {
        'gpt'    { $candidate = Join-Path $SKILLS_ROOT "$SkillName\providers\gpt.md" }
        'claude' { $candidate = Join-Path $SKILLS_ROOT "$SkillName\providers\claude.md" }
        'local'  { $candidate = Join-Path $SKILLS_ROOT "$SkillName\providers\gpt.md" }  # text-only proxy
    }
    if (-not $candidate) { return $null }

    # Defense in depth: reject anything that escapes skills/ (traversal/symlink/junction).
    $safe = Resolve-SafePath -Path $candidate -AllowedRoots @($SKILLS_ROOT)
    if (Test-Path $safe) { return $safe }

    if ($ModelVariant -ne 'gpt') {
        $coreCandidate = Join-Path $SKILLS_ROOT "$SkillName\core.md"
        $safeCore = Resolve-SafePath -Path $coreCandidate -AllowedRoots @($SKILLS_ROOT)
        if (Test-Path $safeCore) { return $safeCore }
    }
    return $null
}

# -- Local model invocation stub -----------------------------------------------

function Invoke-LocalModel([string]$Prompt, [string]$SkillEntryPoint) {
    $url = if ($env:LOCAL_MODEL_URL) { $env:LOCAL_MODEL_URL } else { $LOCAL_MODEL_URL_DEFAULT }
    Write-RouterInfo "Routing to local model at $url (code-30b text-only path)"
    $body = @{
        model  = 'code-30b'
        prompt = $Prompt
        stream = $false
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod `
            -Uri "$url/api/generate" `
            -Method POST `
            -Body $body `
            -ContentType 'application/json' `
            -TimeoutSec 120 `
            -ErrorAction Stop
        return $response.response
    } catch {
        throw "Local model invocation failed: $($_.Exception.Message)"
    }
}

# -- GPT invocation ------------------------------------------------------------

function Invoke-GPTModel([string]$Prompt, [string]$SkillEntryPoint, [string]$ResolvedModel) {
    Write-RouterInfo "Routing to $ResolvedModel via GitHub Copilot for skill '$Skill'"
    $token = Get-CopilotToken
    if (-not $token) {
        throw "No GitHub token available for Copilot GPT invocation."
    }
    $coreContent = ''
    if ($SkillEntryPoint -and (Test-Path $SkillEntryPoint)) {
        $coreContent = Get-Content $SkillEntryPoint -Raw -Encoding UTF8
    }
    $fullInput = if ($coreContent) { "$coreContent`n`nINPUT:`n$Prompt" } else { $Prompt }
    $body = @{
        model             = $ResolvedModel
        input             = $fullInput
        max_output_tokens = 8192
    } | ConvertTo-Json -Depth 5
    try {
        $response = Invoke-RestMethod `
            -Uri 'https://api.githubcopilot.com/responses' `
            -Method POST `
            -Headers @{ Authorization = "Bearer $token"; 'Copilot-Integration-Id' = 'skill-mesh-router' } `
            -ContentType 'application/json' `
            -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) `
            -TimeoutSec 120 `
            -ErrorAction Stop
        if ($response.output -and $response.output.Count -gt 0) {
            $texts = $response.output | ForEach-Object {
                if ($_.content) { $_.content | ForEach-Object { if ($_.text) { $_.text } } }
            }
            return ($texts -join '')
        }
        throw "Copilot response contained no output text."
    } catch {
        throw "Copilot GPT invocation failed: $($_.Exception.Message)"
    }
}

# -- Claude invocation stub ----------------------------------------------------

function Invoke-ClaudeModel([string]$Prompt, [string]$SkillEntryPoint) {
    Write-RouterInfo "Routing to Claude for skill '$Skill'"
    Write-RouterInfo "Claude entry point: $SkillEntryPoint"
    return "CLAUDE_NATIVE_EXECUTION"
}

# -- Telemetry -----------------------------------------------------------------

function Write-TelemetryInvocation(
    [string]$ModelUsed,
    [long]$TokensIn,
    [long]$TokensOut,
    [long]$LatencyMs,
    [double]$CostUsd,
    [string]$Verdict
) {
    try {
        $safeWriter = Resolve-SafePath -Path $TELEMETRY_WRITER_PATH -AllowedRoots @($REPO_ROOT)
        if (-not (Test-Path $safeWriter)) {
            throw "telemetry writer not found at $safeWriter"
        }
        & $safeWriter `
            -Skill $Skill `
            -Model $ModelUsed `
            -TokensIn $TokensIn `
            -TokensOut $TokensOut `
            -LatencyMs $LatencyMs `
            -CostUsd $CostUsd `
            -Verdict $Verdict
    } catch {
        Write-RouterWarning "Telemetry write failed: $($_.Exception.Message)"
    }
}

# -- Main routing logic --------------------------------------------------------

function Invoke-SkillRouter {
    $spendState = Get-SpendState
    $mapping = Get-ModelMapping -SkillName $Skill
    $gptPeer = $null
    if ($Model -eq 'gpt') {
        $gptPeer = Resolve-GptPeer -ExplicitModel $GptModel
    }

    # -- Dry-run output --------------------------------------------------------
    if ($DryRun) {
        Write-Host ""
        Write-Host "skill-router dry-run: --provider $Model --skill $Skill" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Key presence:"
        $copilotToken = Get-CopilotToken
        Write-Host "    Copilot token:     $(if ($copilotToken) { 'present (COPILOT_GITHUB_TOKEN/GH_TOKEN/GITHUB_TOKEN/gh auth token)' } else { 'absent (COPILOT_GITHUB_TOKEN/GH_TOKEN/GITHUB_TOKEN/gh auth token)' })"
        Write-Host "    ANTHROPIC_API_KEY: $(if ($env:ANTHROPIC_API_KEY) { 'SET' } else { 'NOT SET' })"
        Write-Host "    OPENAI_API_KEY:    $(if ($env:OPENAI_API_KEY) { 'SET' } else { 'NOT SET' })"
        Write-Host "    SKILL_MESH_CLAUDE_TIER: $(if ($env:SKILL_MESH_CLAUDE_TIER) { $env:SKILL_MESH_CLAUDE_TIER } else { 'NOT SET (default: fable)' })"
        Write-Host "    LOCAL_MODEL_URL:   $(if ($env:LOCAL_MODEL_URL) { $env:LOCAL_MODEL_URL } else { $LOCAL_MODEL_URL_DEFAULT })"
        Write-Host ""
        Write-Host "  model-mapping.json lookup for '$Skill':"
        Write-Host "    claude-capable: $($mapping['claude-capable'])"
        Write-Host "    gpt-capable:    $($mapping['gpt-capable'])"
        Write-Host "    local-capable:  $($mapping['local-capable'])"
        if ($Model -eq 'gpt') {
            Write-Host ""
            Write-Host "  GPT peer:"
            Write-Host "    model:      $gptPeer"
            Write-Host "    resolution: $script:GptPeerResolutionPath"
        }
        Write-Host ""
        Write-Host "  Entry points:"
        $gptEp = Resolve-SkillEntryPoint -SkillName $Skill -ModelVariant 'gpt'
        $claudeEp = Resolve-SkillEntryPoint -SkillName $Skill -ModelVariant 'claude'
        Write-Host "    GPT:    $(if ($gptEp) { $gptEp } else { '(not yet ported)' })"
        Write-Host "    Claude: $(if ($claudeEp) { $claudeEp } else { '(NOT FOUND -- misconfiguration)' })"
        Write-Host ""
        Write-Host "  Spend ceiling: `$$($spendState.ceiling_usd)/session (config only; per-call cost metering not yet wired) | Accumulated this session: `$$([Math]::Round($spendState.session_spend_usd, 4))"
        Write-Host ""
        Write-Host "Dry-run complete. No API calls made." -ForegroundColor Green
        exit $EXIT_SUCCESS
    }

    # -- Spend guard check -----------------------------------------------------
    # Per-call cost metering is not yet wired (see Add-SpendEntry), so in practice
    # this gate trips only when the durable ledger is unavailable/rejected, not on
    # accumulated spend. Message is worded to match that reality.
    if ($Model -eq 'gpt' -and (Test-SpendCeiling $spendState)) {
        Write-RouterWarning "Durable session ledger unavailable or rejected (configured ceiling `$$($spendState.ceiling_usd)/session; per-call cost metering not yet wired, so accumulated-spend enforcement is inactive). Falling back to Claude for this call. Accumulated: `$$([Math]::Round($spendState.session_spend_usd, 4)) across $($spendState.calls.Count) calls."
        $Model = 'claude'
    }

    # -- Route based on requested provider -------------------------------------
    try {
        switch ($Model) {
            'gpt' {
                if (-not $mapping['gpt-capable']) {
                    Write-RouterWarning "Skill '$Skill' is not GPT-capable (model-mapping.json). Falling back to Claude."
                    return Invoke-ClaudeVariant
                }
                $ep = Resolve-SkillEntryPoint -SkillName $Skill -ModelVariant 'gpt'
                if (-not $ep) {
                    Write-RouterWarning "No GPT entry point found for '$Skill'. Falling back to Claude."
                    return Invoke-ClaudeVariant
                }
                $gptAvailable = Test-CopilotAvailable
                if (-not $gptAvailable -and $env:OPENAI_API_KEY) {
                    $gptAvailable = Test-OpenAIAvailable
                }
                if (-not $gptAvailable) {
                    Write-RouterWarning "Copilot GPT transport unavailable (OPENAI_API_KEY is only an advisory health signal; no direct OpenAI transport is wired). Falling back to Claude per fail-open contract."
                    return Invoke-ClaudeVariant
                }
                $timer = $null
                try {
                    $timer = [Diagnostics.Stopwatch]::StartNew()
                    $result = Invoke-GPTModel -Prompt $SkillInput -SkillEntryPoint $ep -ResolvedModel $gptPeer
                    $timer.Stop()
                    Write-TelemetryInvocation -ModelUsed $gptPeer -TokensIn 0 -TokensOut 0 -LatencyMs $timer.ElapsedMilliseconds -CostUsd 0.0 -Verdict 'pass'
                    Write-RouterInfo "GPT invocation succeeded for '$Skill'."
                    exit $EXIT_SUCCESS
                } catch {
                    if ($null -ne $timer) {
                        $timer.Stop()
                        $gptVerdict = if ($_.Exception.Message -like 'GPT invocation stub*') { 'stub' } else { 'fail' }
                        Write-TelemetryInvocation -ModelUsed $gptPeer -TokensIn 0 -TokensOut 0 -LatencyMs $timer.ElapsedMilliseconds -CostUsd 0.0 -Verdict $gptVerdict
                    }
                    Write-RouterWarning "GPT invocation failed for '$Skill': $_. Attempting single Claude retry."
                    return Invoke-ClaudeVariant -IsRetry $true
                }
            }
            'local' {
                if (-not $mapping['local-capable']) {
                    Write-RouterError "Skill '$Skill' is not local-capable (requires vision or sub-agents). Cannot route to code-30b."
                    Write-Host "skill-router: HALT -- skill '$Skill' requires capabilities not supported by local fallback (vision/sub-agent). Restore cloud provider credentials to resume full functionality."
                    exit $EXIT_ALL_PROVIDERS_FAILED
                }
                if (-not (Test-LocalModelAvailable)) {
                    Write-RouterError "Local model unavailable. All providers failed."
                    Write-Host "skill-router: HALT -- both cloud providers unavailable and local model is also unreachable. All three providers are down."
                    exit $EXIT_ALL_PROVIDERS_FAILED
                }
                $ep = Resolve-SkillEntryPoint -SkillName $Skill -ModelVariant 'local'
                $timer = [Diagnostics.Stopwatch]::StartNew()
                try {
                    $result = Invoke-LocalModel -Prompt $SkillInput -SkillEntryPoint $ep
                    $timer.Stop()
                    Write-TelemetryInvocation -ModelUsed 'code-30b' -TokensIn 0 -TokensOut 0 -LatencyMs $timer.ElapsedMilliseconds -CostUsd 0.0 -Verdict 'pass'
                    exit $EXIT_FALLBACK_USED
                } catch {
                    $timer.Stop()
                    Write-TelemetryInvocation -ModelUsed 'code-30b' -TokensIn 0 -TokensOut 0 -LatencyMs $timer.ElapsedMilliseconds -CostUsd 0.0 -Verdict 'fail'
                    throw
                }
            }
            default {
                # 'claude' or any unrecognized value -> Claude
                return Invoke-ClaudeVariant
            }
        }
    } catch {
        # Catch-all router error -- fail-open to Claude per S.5. Wrap the fallback so
        # a second, stacked failure still maps to the documented exit code 1 instead
        # of escaping as an unhandled terminating error.
        Write-RouterWarning "Unexpected router error for provider=$Model, skill=$Skill. Falling back to Claude. Error: $_"
        try {
            return Invoke-ClaudeVariant -IsRetry $false
        } catch {
            Write-RouterError "Claude fallback also failed after a router error for '$Skill': $_"
            exit $EXIT_SKILL_ERROR
        }
    }
}

function Invoke-ClaudeVariant([bool]$IsRetry = $false) {
    if (-not (Test-AnthropicAvailable)) {
        $mapping = Get-ModelMapping -SkillName $Skill
        if ($mapping['local-capable'] -and (Test-LocalModelAvailable)) {
            Write-RouterWarning "Claude unavailable. Routing to local code-30b (text-only fallback)."
            $ep = Resolve-SkillEntryPoint -SkillName $Skill -ModelVariant 'local'
            $timer = [Diagnostics.Stopwatch]::StartNew()
            try {
                $result = Invoke-LocalModel -Prompt $SkillInput -SkillEntryPoint $ep
                $timer.Stop()
                Write-TelemetryInvocation -ModelUsed 'code-30b' -TokensIn 0 -TokensOut 0 -LatencyMs $timer.ElapsedMilliseconds -CostUsd 0.0 -Verdict 'pass'
                exit $EXIT_FALLBACK_USED
            } catch {
                $timer.Stop()
                Write-TelemetryInvocation -ModelUsed 'code-30b' -TokensIn 0 -TokensOut 0 -LatencyMs $timer.ElapsedMilliseconds -CostUsd 0.0 -Verdict 'fail'
                throw
            }
        }
        Write-RouterError "Both Claude and GPT unavailable, and skill '$Skill' has no local fallback."
        Write-Host "skill-router: HALT -- both cloud providers unavailable and skill '$Skill' requires capabilities not supported by local fallback (vision/sub-agent). Set LOCAL_MODEL_URL to enable text-only local fallback for other skills. Restore cloud provider credentials to resume full functionality."
        exit $EXIT_ALL_PROVIDERS_FAILED
    }

    $ep = Resolve-SkillEntryPoint -SkillName $Skill -ModelVariant 'claude'
    if (-not $ep) {
        Write-RouterError "No Claude entry point found for '$Skill'. This is a misconfiguration."
        exit $EXIT_SKILL_ERROR
    }

    $timer = $null
    try {
        $timer = [Diagnostics.Stopwatch]::StartNew()
        $result = Invoke-ClaudeModel -Prompt $SkillInput -SkillEntryPoint $ep
        $timer.Stop()
        $exitCode = if ($IsRetry) { $EXIT_FALLBACK_USED } else { $EXIT_SUCCESS }
        Write-TelemetryInvocation -ModelUsed 'claude' -TokensIn 0 -TokensOut 0 -LatencyMs $timer.ElapsedMilliseconds -CostUsd 0.0 -Verdict 'pass'
        Write-RouterInfo "Claude invocation succeeded for '$Skill'$(if ($IsRetry) { ' (retry after GPT failure)' } else { '' })."
        exit $exitCode
    } catch {
        if ($null -ne $timer) {
            $timer.Stop()
            Write-TelemetryInvocation -ModelUsed 'claude' -TokensIn 0 -TokensOut 0 -LatencyMs $timer.ElapsedMilliseconds -CostUsd 0.0 -Verdict 'fail'
        }
        Write-RouterError "Claude invocation also failed for '$Skill': $_"
        exit $EXIT_SKILL_ERROR
    }
}

# -- Entry point ---------------------------------------------------------------

# Reject unsafe skill names before any path is constructed from them.
if ($Skill -match '[\\/]' -or $Skill.Contains('..')) {
    [Console]::Error.WriteLine(
        "skill-router: SECURITY -- invalid skill name '$Skill': path separators and '..' are not allowed."
    )
    exit $EXIT_FALLBACK_USED
}

# Resolve the effective provider (auto detection / deprecated -Model alias).
$deprecatedModelUsed = ($Model -ne '')
if ($Provider -ne 'auto') {
    if ($deprecatedModelUsed) {
        [Console]::Error.WriteLine(
            "skill-router: WARNING -- both -Provider and -Model supplied; -Provider '$Provider' takes precedence, ignoring deprecated -Model '$Model'."
        )
    }
    $effectiveProvider = $Provider
} elseif ($deprecatedModelUsed) {
    [Console]::Error.WriteLine(
        "skill-router: WARNING -- -Model is a deprecated compatibility alias; use -Provider. Mapping -Model '$Model' onto -Provider '$Model'."
    )
    $effectiveProvider = $Model
} else {
    $effectiveProvider = Resolve-ProviderFromHostMetadata
}
# The rest of the router keys off $Model as the resolved provider.
$Model = $effectiveProvider

if ([string]::IsNullOrWhiteSpace($env:SKILL_ROUTER_SESSION_ID)) {
    $env:SKILL_ROUTER_SESSION_ID = [System.Guid]::NewGuid().ToString()
    [Console]::Error.WriteLine(
        "skill-router: WARNING -- SKILL_ROUTER_SESSION_ID not set; auto-generated for this invocation: $($env:SKILL_ROUTER_SESSION_ID). Set SKILL_ROUTER_SESSION_ID in your environment for consistent session spend tracking."
    )
}

Invoke-SkillRouter
