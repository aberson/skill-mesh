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

    GPT transport precedence (Step 37): GitHub Copilot authentication is tried
    FIRST; the optional direct-OpenAI transport (OPENAI_API_KEY) is tried SECOND,
    only when Copilot is unavailable or fails. Selecting GPT never requires
    OPENAI_API_KEY -- Copilot-only sessions work with it unset. Provider choice and
    transport authentication are separate axes (documentation/providers/). Host
    metadata detection for "-Provider auto" is delegated to the per-source adapters
    in runtime/providers/ (claude-host.ps1, copilot-host.ps1); this file only
    composes their results and applies the ambiguity/absence contract. Spend
    ceiling: the value is config only; per-call cost metering is not yet wired
    (Add-SpendEntry has no call sites), so the spend gate currently trips only on
    an unavailable/rejected durable ledger, not on spend.

    Exit codes:
      0 = success on requested provider (no fallback triggered)
      1 = skill execution error (not a router error)
      2 = fallback provider used successfully, OR -Provider auto could not
          resolve a provider (ambiguous/unset host metadata), OR an invalid
          skill name / unsafe path was rejected
      3 = both cloud providers failed AND no supported local fallback exists

    DELIBERATE Step-37 exit-code correction: -Provider gpt with BOTH transports
    unavailable pre-flight (no Copilot token/health-check pass AND no configured
    OpenAI fallback) now exits 2, not 0. Pre-Step-37 this specific pre-flight
    case fell through to Invoke-ClaudeVariant WITHOUT -IsRetry and exited 0 --
    inconsistent with this file's own contract above ("0 = success on the
    REQUESTED provider"), since gpt was requested and never even attempted.
    Every OTHER GPT-unavailable path (an attempted-and-failed invocation) always
    exited 2. This was a latent inconsistency in the pre-Step-37 router, not a
    documented behavior; no test asserted the old exit-0 value for this case.
    Fixed by treating "no transport available" and "attempted transport failed"
    as the same GPT-provider-failure outcome (both throw into the single
    catch block below that always retries with -IsRetry $true).
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

# Load the per-source host-metadata adapters (defines Test-ClaudeHostMarkers /
# Test-CopilotHostMarkers). Each adapter reads ONLY its own approved source
# (documentation/architecture.md section 5.3); this file composes their results.
. (Join-Path $RUNTIME_DIR 'providers\claude-host.ps1')
. (Join-Path $RUNTIME_DIR 'providers\copilot-host.ps1')

# -- Constants ----------------------------------------------------------------

$ROUTER_VERSION = '1.3.0'
$SPEND_CEILING_DEFAULT = 5.0
$LOCAL_MODEL_URL_DEFAULT = 'http://localhost:11434'
$COPILOT_BASE_URL_DEFAULT = 'https://api.githubcopilot.com'
$OPENAI_BASE_URL_DEFAULT = 'https://api.openai.com'
$HEALTH_CHECK_TIMEOUT_SEC_DEFAULT = 8
$INVOCATION_TIMEOUT_SEC_DEFAULT = 120

function Test-IsLoopbackUrl([string]$Url) {
    # Security gate for the test-only base-URL overrides below: only a loopback
    # target is ever honored. Without this, a stray/leaked SKILL_MESH_*_BASE_URL
    # in a real config (wrong shell profile, copy-pasted .env, CI misconfig) could
    # silently redirect a REAL Copilot/OpenAI credential to an attacker-controlled
    # host instead of the real API.
    try {
        $uri = [System.Uri]$Url
        if ($uri.Scheme -ne 'http' -and $uri.Scheme -ne 'https') { return $false }
        $h = $uri.Host
        return ($h -eq '127.0.0.1') -or ($h -eq '::1') -or ($h -eq 'localhost')
    } catch {
        return $false
    }
}

# Test-only seams: SKILL_MESH_COPILOT_BASE_URL / SKILL_MESH_OPENAI_BASE_URL let
# tests point the router's GPT transports at a local mock HTTP server instead of
# the real cloud endpoints (no live credentials or network calls needed to
# exercise auth-failure/rate-limit/timeout/precedence behavior). Unset in
# production; the router talks to the real APIs by default. Gated to loopback
# only (Test-IsLoopbackUrl) -- a non-loopback value is ignored, not honored.
function Get-CopilotBaseUrl {
    if (-not [string]::IsNullOrWhiteSpace($env:SKILL_MESH_COPILOT_BASE_URL)) {
        $candidate = $env:SKILL_MESH_COPILOT_BASE_URL.TrimEnd('/')
        if (Test-IsLoopbackUrl $candidate) {
            return $candidate
        }
        Write-RouterWarning "SKILL_MESH_COPILOT_BASE_URL is set to a non-loopback host; ignoring it (test-only override, loopback only) and using the real Copilot endpoint."
    }
    return $COPILOT_BASE_URL_DEFAULT
}

function Get-OpenAIBaseUrl {
    if (-not [string]::IsNullOrWhiteSpace($env:SKILL_MESH_OPENAI_BASE_URL)) {
        $candidate = $env:SKILL_MESH_OPENAI_BASE_URL.TrimEnd('/')
        if (Test-IsLoopbackUrl $candidate) {
            return $candidate
        }
        Write-RouterWarning "SKILL_MESH_OPENAI_BASE_URL is set to a non-loopback host; ignoring it (test-only override, loopback only) and using the real OpenAI endpoint."
    }
    return $OPENAI_BASE_URL_DEFAULT
}

# Test-only seam: SKILL_MESH_TRANSPORT_TIMEOUT_SEC shortens both health-check and
# invocation timeouts so a timeout scenario can be exercised in test time rather
# than waiting out the production default. Unset in production.
function Get-TransportTimeoutSec([int]$Default) {
    if (-not [string]::IsNullOrWhiteSpace($env:SKILL_MESH_TRANSPORT_TIMEOUT_SEC)) {
        try {
            return [int]$env:SKILL_MESH_TRANSPORT_TIMEOUT_SEC
        } catch {
            return $Default
        }
    }
    return $Default
}

# Exit codes
$EXIT_SUCCESS = 0
$EXIT_SKILL_ERROR = 1
$EXIT_FALLBACK_USED = 2
$EXIT_ALL_PROVIDERS_FAILED = 3

# -- Helpers ------------------------------------------------------------------

# Secrets resolved at RUNTIME rather than read directly from an env var (e.g. the
# gh-CLI-derived Copilot token -- see Get-CopilotToken's `gh auth token` fallback
# below) have no env var for Protect-SecretsInText to read. Any such value must be
# registered here via Add-ResolvedSecretCandidate the moment it is resolved, so
# the redaction guarantee below covers it too.
$script:ResolvedSecretCandidates = New-Object System.Collections.Generic.List[string]

function Add-ResolvedSecretCandidate([string]$Secret) {
    if (-not [string]::IsNullOrWhiteSpace($Secret)) {
        $script:ResolvedSecretCandidates.Add($Secret)
    }
}

function Protect-SecretsInText([string]$Text) {
    <#
      Redact any known credential VALUE out of a diagnostic string before it is
      ever written to stdout/stderr/telemetry. This is a defense-in-depth backstop
      -- diagnostics must report only credential presence and source class (e.g.
      "Copilot token: present (env)"), never the value, not even truncated. Applied
      unconditionally by Write-RouterWarning/-Info/-Error/-RawStderr so every call
      site is covered without relying on each call site to remember to redact.
    #>
    if ([string]::IsNullOrEmpty($Text)) { return $Text }
    $secretCandidates = @(
        $env:OPENAI_API_KEY,
        $env:ANTHROPIC_API_KEY,
        $env:CLAUDE_CODE_OAUTH_TOKEN,
        $env:COPILOT_GITHUB_TOKEN,
        $env:GH_TOKEN,
        $env:GITHUB_TOKEN
    ) + @($script:ResolvedSecretCandidates)
    foreach ($secret in $secretCandidates) {
        # Length guard avoids redacting short/common incidental substrings.
        if ((-not [string]::IsNullOrWhiteSpace($secret)) -and $secret.Length -ge 6 -and $Text.Contains($secret)) {
            $Text = $Text.Replace($secret, '[REDACTED]')
        }
    }
    return $Text
}

function Write-RouterWarning([string]$Message) {
    Write-Warning "skill-router: WARNING -- $(Protect-SecretsInText $Message)"
}

function Write-RouterInfo([string]$Message) {
    Write-Host "skill-router: $(Protect-SecretsInText $Message)" -ForegroundColor Cyan
}

function Write-RouterError([string]$Message) {
    Write-Error "skill-router: ERROR -- $(Protect-SecretsInText $Message)" -ErrorAction Continue
}

function Write-RouterRawStderr([string]$PreformattedMessage) {
    <#
      Raw, single-line stderr write for early-exit / entry-point diagnostics
      that are already fully formatted with their own "skill-router: X --"
      prefix (ambiguous/absent provider, invalid skill name, deprecation
      notices, spend-ledger escape, etc). Deliberately bypasses Write-Warning
      (lands on STDOUT under this host's capture semantics -- verified
      empirically) and Write-Error (adds a multi-line CategoryInfo /
      FullyQualifiedErrorId block) so these messages keep landing on stderr as
      a single clean line, exactly as several existing tests assert
      (test_router_scenarios.py, test_spend_ledger_guard.py). Still passes
      through Protect-SecretsInText so the centralized-redaction guarantee
      covers these sites too, not just Write-RouterWarning/-Info/-Error.
    #>
    [Console]::Error.WriteLine((Protect-SecretsInText $PreformattedMessage))
}

function Read-SafeConfigText([string]$ConfigPath) {
    # Validate the config path stays inside the repo before reading it.
    $safe = Resolve-SafePath -Path $ConfigPath -AllowedRoots @($REPO_ROOT)
    return (Get-Content $safe -Raw)
}

# -- Host-metadata provider detection (-Provider auto) -------------------------

function Resolve-ProviderFromHostMetadata {
    # Approved host-identity markers ONLY (architecture section 5.3), delegated to
    # the per-source adapters in runtime/providers/. Credentials (ANTHROPIC_API_KEY
    # / OPENAI_API_KEY / tokens) are NOT host identity and are never consulted here.
    $claudeDetected = Test-ClaudeHostMarkers
    $gptDetected = Test-CopilotHostMarkers

    if ($claudeDetected -and $gptDetected) {
        Write-RouterRawStderr (
            'skill-router: ERROR -- -Provider auto is ambiguous: both Claude host markers ' +
            '(CLAUDECODE=1 / CLAUDE_CODE_ENTRYPOINT) and GPT/Copilot host markers ' +
            '(COPILOT_CLI / COPILOT_AGENT_SESSION_ID) are present. Pass -Provider claude|gpt explicitly.'
        )
        exit $EXIT_FALLBACK_USED
    }
    if ($claudeDetected) { return 'claude' }
    if ($gptDetected) { return 'gpt' }

    Write-RouterRawStderr (
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
        Write-RouterRawStderr 'skill-router: WARNING -- model-tier-map.json missing or unreadable; using default_tier_peer gpt-5.5'
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
        Write-RouterRawStderr "skill-router: WARNING -- spend-ledger path '$candidate' resolves outside the allowed roots; disabling durable spend tracking for this session. $($_.Exception.Message)"
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

function Get-ProviderTransportPrecedence([string]$ProviderName) {
    # Reads the documented transport order for a provider from
    # config/model-mapping.json's providers block (kept in sync with
    # documentation/providers/*.md by Step 37). Informational/diagnostic only --
    # the actual precedence is enforced in code by Invoke-GptWithTransportPrecedence
    # and Invoke-ClaudeVariant; this just surfaces the config that documents it.
    $fallback = @{
        'claude' = @('host-native', 'anthropic-api')
        'gpt'    = @('copilot', 'openai-direct')
        'local'  = @('ollama')
    }
    if (-not (Test-Path $MODEL_MAPPING_PATH)) {
        return $fallback[$ProviderName]
    }
    try {
        $config = Read-SafeConfigText $MODEL_MAPPING_PATH | ConvertFrom-Json
        $providersProp = $config.PSObject.Properties['providers']
        if ($providersProp) {
            $entry = $providersProp.Value.PSObject.Properties[$ProviderName]
            if ($entry -and $entry.Value.transport_precedence) {
                return @($entry.Value.transport_precedence)
            }
        }
    } catch {
        # Fall through to the built-in default below.
    }
    return $fallback[$ProviderName]
}

# -- Health checks -------------------------------------------------------------

# Health check for the OPTIONAL direct-OpenAI fallback transport (Step 37; see
# Invoke-OpenAIModel and Invoke-GptWithTransportPrecedence below). OPENAI_API_KEY
# is required only for THIS transport -- selecting GPT never requires it, because
# Copilot is always tried first.
function Test-OpenAIAvailable {
    if (-not $env:OPENAI_API_KEY) {
        Write-RouterWarning "OPENAI_API_KEY not set -- direct-OpenAI fallback transport unavailable (optional; Copilot is tried first)."
        return $false
    }
    try {
        $response = Invoke-RestMethod `
            -Uri "$(Get-OpenAIBaseUrl)/v1/models" `
            -Headers @{ Authorization = "Bearer $($env:OPENAI_API_KEY)" } `
            -Method GET `
            -TimeoutSec (Get-TransportTimeoutSec 5) `
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
        if ($token -and $token.Trim()) {
            $resolved = $token.Trim()
            # This value has no env var for Protect-SecretsInText to read directly
            # (it came from a subprocess, not $env:*) -- register it explicitly so
            # the redaction guarantee covers it too.
            Add-ResolvedSecretCandidate $resolved
            return $resolved
        }
    } catch { }
    return $null
}

function Get-CopilotTokenPresence {
    # Presence-only diagnostic for -DryRun. Reports env-var presence + source class
    # WITHOUT materializing the token value: it never calls 'gh auth token' (which would
    # read the operator's real credential from the gh keyring -- issue #51) and never adds
    # network egress. Per the Protect-SecretsInText contract above, diagnostics report
    # presence/source only, never the value. The gh-keyring fallback is still used by
    # Get-CopilotToken at real runtime; a dry-run must not read live credentials, so the
    # fallback is reported as runtime-only rather than probed here.
    if ($env:COPILOT_GITHUB_TOKEN) { return 'present (COPILOT_GITHUB_TOKEN)' }
    if ($env:GH_TOKEN) { return 'present (GH_TOKEN)' }
    if ($env:GITHUB_TOKEN) { return 'present (GITHUB_TOKEN)' }
    return 'not in env (COPILOT_GITHUB_TOKEN/GH_TOKEN/GITHUB_TOKEN); gh auth token fallback used at runtime, not probed in dry-run'
}

function Test-CopilotAvailable {
    $token = Get-CopilotToken
    if (-not $token) {
        Write-RouterWarning "No GitHub token found (COPILOT_GITHUB_TOKEN/GH_TOKEN/GITHUB_TOKEN/gh auth token) -- Copilot GPT unavailable."
        return $false
    }
    try {
        $response = Invoke-RestMethod `
            -Uri "$(Get-CopilotBaseUrl)/models" `
            -Headers @{ Authorization = "Bearer $token"; 'Copilot-Integration-Id' = 'skill-mesh-router' } `
            -Method GET `
            -TimeoutSec (Get-TransportTimeoutSec $HEALTH_CHECK_TIMEOUT_SEC_DEFAULT) `
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

# -- GPT invocation (Copilot-first, optional direct-OpenAI fallback) -----------

function ConvertFrom-ResponsesApiOutput($Response) {
    <#
      Shared parser: both the Copilot and the direct-OpenAI transport speak the
      same "responses" API shape (output[].content[].text). Real output from a
      reasoning-tier model (BOTH Copilot peers -- gpt-5.6-sol and gpt-5.5 -- are
      reasoning-tier) commonly LEADS with one or more {type:"reasoning"} items
      that have NO "content" key at all, before the final {type:"message"} item
      that does. Under Set-StrictMode -Version Latest (line 106), naked dot
      access on a property that doesn't exist on a given item throws
      PropertyNotFoundException -- every access below is therefore guarded via
      .PSObject.Properties[...] lookups (which never throw: they return $null
      for a missing key). A missing/content-less/textless item means "no text
      from THIS item"; scanning continues to the rest of output. Only throw
      when NO item across the whole response yielded any text.
    #>
    $texts = New-Object System.Collections.Generic.List[string]

    $outputProp = $Response.PSObject.Properties['output']
    $items = if ($outputProp -and $outputProp.Value) { @($outputProp.Value) } else { @() }

    foreach ($item in $items) {
        if ($null -eq $item) { continue }
        $contentProp = $item.PSObject.Properties['content']
        if (-not $contentProp -or $null -eq $contentProp.Value) { continue }
        foreach ($contentItem in @($contentProp.Value)) {
            if ($null -eq $contentItem) { continue }
            $textProp = $contentItem.PSObject.Properties['text']
            if ($textProp -and -not [string]::IsNullOrEmpty([string]$textProp.Value)) {
                $texts.Add([string]$textProp.Value)
            }
        }
    }

    if ($texts.Count -gt 0) {
        return ($texts -join '')
    }
    throw "response contained no output text."
}

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
            -Uri "$(Get-CopilotBaseUrl)/responses" `
            -Method POST `
            -Headers @{ Authorization = "Bearer $token"; 'Copilot-Integration-Id' = 'skill-mesh-router' } `
            -ContentType 'application/json' `
            -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) `
            -TimeoutSec (Get-TransportTimeoutSec $INVOCATION_TIMEOUT_SEC_DEFAULT) `
            -ErrorAction Stop
        return ConvertFrom-ResponsesApiOutput $response
    } catch {
        throw "Copilot GPT invocation failed: $($_.Exception.Message)"
    }
}

function Invoke-OpenAIModel([string]$Prompt, [string]$SkillEntryPoint, [string]$ResolvedModel) {
    # OPTIONAL fallback transport (Step 37). Only reached when Copilot is
    # unavailable or fails AND OPENAI_API_KEY is set; see
    # Invoke-GptWithTransportPrecedence. Never the primary GPT transport.
    Write-RouterInfo "Routing to $ResolvedModel via direct OpenAI API (optional fallback transport) for skill '$Skill'"
    if (-not $env:OPENAI_API_KEY) {
        throw "OPENAI_API_KEY not set; the direct-OpenAI fallback transport requires it."
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
            -Uri "$(Get-OpenAIBaseUrl)/v1/responses" `
            -Method POST `
            -Headers @{ Authorization = "Bearer $($env:OPENAI_API_KEY)" } `
            -ContentType 'application/json' `
            -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) `
            -TimeoutSec (Get-TransportTimeoutSec $INVOCATION_TIMEOUT_SEC_DEFAULT) `
            -ErrorAction Stop
        return ConvertFrom-ResponsesApiOutput $response
    } catch {
        throw "Direct-OpenAI GPT invocation failed: $($_.Exception.Message)"
    }
}

function Invoke-GptWithTransportPrecedence([string]$Prompt, [string]$SkillEntryPoint, [string]$ResolvedModel) {
    <#
      Copilot-first GPT transport selection with an OPTIONAL direct-OpenAI
      fallback (documentation/providers/gpt.md). Returns a PSCustomObject with
      Output + Transport ('copilot' | 'openai-direct') on success, or throws a
      combined error describing why every available transport failed/was absent
      -- the caller (the 'gpt' case in Invoke-SkillRouter) treats that as a single
      GPT-provider failure and applies the existing bounded single-retry-to-Claude
      fallback. This function never widens that cross-provider retry budget: it
      only chooses between two TRANSPORTS of the SAME provider before the
      cross-provider decision is made.
    #>
    if (Test-CopilotAvailable) {
        try {
            $result = Invoke-GPTModel -Prompt $Prompt -SkillEntryPoint $SkillEntryPoint -ResolvedModel $ResolvedModel
            return [PSCustomObject]@{ output = $result; transport = 'copilot' }
        } catch {
            $copilotFailure = $_.Exception.Message
            if (-not $env:OPENAI_API_KEY) {
                throw "Copilot transport failed and no OPENAI_API_KEY fallback is configured: $copilotFailure"
            }
            Write-RouterWarning "Copilot transport failed ($copilotFailure); attempting the optional direct-OpenAI fallback transport."
        }
    } elseif (-not $env:OPENAI_API_KEY) {
        throw "No GPT transport available: Copilot is unavailable (no GitHub token, or the Copilot health check failed) and OPENAI_API_KEY is not set for the optional direct-OpenAI fallback."
    }

    if (-not (Test-OpenAIAvailable)) {
        throw "Direct-OpenAI fallback transport is unavailable (OPENAI_API_KEY is set but the OpenAI health check failed)."
    }
    $result = Invoke-OpenAIModel -Prompt $Prompt -SkillEntryPoint $SkillEntryPoint -ResolvedModel $ResolvedModel
    return [PSCustomObject]@{ output = $result; transport = 'openai-direct' }
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
        Write-Host "    Copilot token:     $(Get-CopilotTokenPresence)"
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
            Write-Host ""
            Write-Host "  GPT transport precedence: $((Get-ProviderTransportPrecedence 'gpt') -join ' -> ') (2nd is optional; selecting GPT never requires OPENAI_API_KEY)"
            # Touch the base-URL resolvers so a misconfigured/non-loopback test-only
            # override is caught and warned about even during a dry run. Neither
            # function makes a network call itself -- "No API calls made" holds.
            $null = Get-CopilotBaseUrl
            $null = Get-OpenAIBaseUrl
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
                $timer = $null
                try {
                    $timer = [Diagnostics.Stopwatch]::StartNew()
                    # Copilot-first, with an OPTIONAL direct-OpenAI fallback transport
                    # (documentation/providers/gpt.md). This is a within-provider
                    # transport choice, not the cross-provider retry budget below.
                    $invocation = Invoke-GptWithTransportPrecedence -Prompt $SkillInput -SkillEntryPoint $ep -ResolvedModel $gptPeer
                    $timer.Stop()
                    # Telemetry 'model' stays the BARE model id on BOTH success and
                    # failure (matches the pre-Step-37 shape; telemetry-summary.ps1
                    # groups/aggregates by this exact string -- suffixing it with
                    # "via copilot"/"via openai-direct" on success only would
                    # fragment that grouping and silently diverge from the failure
                    # path's shape). Transport attribution is surfaced to humans via
                    # the Write-RouterInfo line below, not via telemetry.
                    Write-TelemetryInvocation -ModelUsed $gptPeer -TokensIn 0 -TokensOut 0 -LatencyMs $timer.ElapsedMilliseconds -CostUsd 0.0 -Verdict 'pass'
                    Write-RouterInfo "GPT invocation succeeded for '$Skill' via $($invocation.transport)."
                    exit $EXIT_SUCCESS
                } catch {
                    if ($null -ne $timer) {
                        $timer.Stop()
                        $gptVerdict = if ($_.Exception.Message -like 'GPT invocation stub*') { 'stub' } else { 'fail' }
                        Write-TelemetryInvocation -ModelUsed $gptPeer -TokensIn 0 -TokensOut 0 -LatencyMs $timer.ElapsedMilliseconds -CostUsd 0.0 -Verdict $gptVerdict
                    }
                    # Both GPT transports (Copilot, and the optional direct-OpenAI
                    # fallback) are exhausted -- ONE bounded retry to Claude, per the
                    # existing cross-provider fail-open contract (not widened).
                    Write-RouterWarning "GPT invocation failed for '$Skill' (Copilot-first, optional OpenAI fallback exhausted): $_. Attempting single Claude retry."
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
    Write-RouterRawStderr "skill-router: SECURITY -- invalid skill name '$Skill': path separators and '..' are not allowed."
    exit $EXIT_FALLBACK_USED
}

# Resolve the effective provider (auto detection / deprecated -Model alias).
$deprecatedModelUsed = ($Model -ne '')
if ($Provider -ne 'auto') {
    if ($deprecatedModelUsed) {
        Write-RouterRawStderr "skill-router: WARNING -- both -Provider and -Model supplied; -Provider '$Provider' takes precedence, ignoring deprecated -Model '$Model'."
    }
    $effectiveProvider = $Provider
} elseif ($deprecatedModelUsed) {
    Write-RouterRawStderr "skill-router: WARNING -- -Model is a deprecated compatibility alias; use -Provider. Mapping -Model '$Model' onto -Provider '$Model'."
    $effectiveProvider = $Model
} else {
    $effectiveProvider = Resolve-ProviderFromHostMetadata
}
# The rest of the router keys off $Model as the resolved provider.
$Model = $effectiveProvider

if ([string]::IsNullOrWhiteSpace($env:SKILL_ROUTER_SESSION_ID)) {
    $env:SKILL_ROUTER_SESSION_ID = [System.Guid]::NewGuid().ToString()
    Write-RouterRawStderr "skill-router: WARNING -- SKILL_ROUTER_SESSION_ID not set; auto-generated for this invocation: $($env:SKILL_ROUTER_SESSION_ID). Set SKILL_ROUTER_SESSION_ID in your environment for consistent session spend tracking."
}

Invoke-SkillRouter
