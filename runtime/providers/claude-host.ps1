<#
.SYNOPSIS
    claude-host.ps1 -- host-metadata adapter for the Claude provider.

.DESCRIPTION
    One of the host-metadata adapters backing runtime/skill-router.ps1's
    "-Provider auto" detection (documentation/architecture.md section 5.3). Reads
    ONLY the approved Claude host-identity markers -- CLAUDECODE (must equal '1')
    or CLAUDE_CODE_ENTRYPOINT (any non-empty value) -- and nothing else. Credential
    variables (ANTHROPIC_API_KEY, CLAUDE_CODE_OAUTH_TOKEN) are explicitly excluded:
    a credential identifies a transport, not the active host (section 5.3).

    Dual mode, mirroring runtime/path-guard.ps1:
      - Dot-sourced (no -Detect): only defines Test-ClaudeHostMarkers; runs no
        logic. This is how runtime/skill-router.ps1 consumes it.
      - CLI (-Detect): prints 'claude' if detected, else 'unknown', and exits 0.

.PARAMETER Detect
    CLI mode only: run detection now against the current environment and print
    the result ('claude' or 'unknown').

.NOTES
    Windows PowerShell 5.1 compatible. ASCII-only source (no BOM required).
#>

[CmdletBinding()]
param(
    [switch]$Detect
)

function Test-ClaudeHostMarkers {
    <#
      Return $true if any approved Claude host-identity marker is set:
        CLAUDECODE = '1'  OR  CLAUDE_CODE_ENTRYPOINT is non-empty.
      Returns $false otherwise. Never consults credential variables.
    #>
    if ($env:CLAUDECODE -eq '1') { return $true }
    if (-not [string]::IsNullOrWhiteSpace($env:CLAUDE_CODE_ENTRYPOINT)) { return $true }
    return $false
}

if ($Detect) {
    if (Test-ClaudeHostMarkers) {
        Write-Host 'claude'
    } else {
        Write-Host 'unknown'
    }
    exit 0
}
