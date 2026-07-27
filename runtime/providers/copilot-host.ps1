<#
.SYNOPSIS
    copilot-host.ps1 -- host-metadata adapter for the GPT/Copilot provider.

.DESCRIPTION
    One of the host-metadata adapters backing runtime/skill-router.ps1's
    "-Provider auto" detection (documentation/architecture.md section 5.3). Reads
    ONLY the approved GPT/Copilot host-identity markers -- COPILOT_CLI (non-empty)
    or COPILOT_AGENT_SESSION_ID (non-empty) -- and nothing else. Credential
    variables (OPENAI_API_KEY, GH_TOKEN, GITHUB_TOKEN, COPILOT_GITHUB_TOKEN) are
    explicitly excluded: a credential identifies a transport, not the active host
    (section 5.3).

    Dual mode, mirroring runtime/path-guard.ps1:
      - Dot-sourced (no -Detect): only defines Test-CopilotHostMarkers; runs no
        logic. This is how runtime/skill-router.ps1 consumes it.
      - CLI (-Detect): prints 'gpt' if detected, else 'unknown', and exits 0.

.PARAMETER Detect
    CLI mode only: run detection now against the current environment and print
    the result ('gpt' or 'unknown').

.NOTES
    Windows PowerShell 5.1 compatible. ASCII-only source (no BOM required).
#>

[CmdletBinding()]
param(
    [switch]$Detect
)

function Test-CopilotHostMarkers {
    <#
      Return $true if any approved GPT/Copilot host-identity marker is set:
        COPILOT_CLI is non-empty  OR  COPILOT_AGENT_SESSION_ID is non-empty.
      Returns $false otherwise. Never consults credential variables.
    #>
    if (-not [string]::IsNullOrWhiteSpace($env:COPILOT_CLI)) { return $true }
    if (-not [string]::IsNullOrWhiteSpace($env:COPILOT_AGENT_SESSION_ID)) { return $true }
    return $false
}

if ($Detect) {
    if (Test-CopilotHostMarkers) {
        Write-Host 'gpt'
    } else {
        Write-Host 'unknown'
    }
    exit 0
}
