<#
.SYNOPSIS
    skill-mesh-provenance.ps1 -- the SINGLE source of truth for the provenance marker
    that stamps every skill-mesh-generated file, AND for the anchored check that
    decides whether a file on disk is a well-formed skill-mesh-generated file.

.DESCRIPTION
    File-content provenance -- NOT the mutable on-disk ledger -- is the ownership
    authority for "may skill-mesh overwrite or delete this file?". The builder
    (build-distributions.ps1) embeds the marker LINE in every generated file's
    provenance header; the installer (install-skill-mesh.ps1) gates every destructive
    op (install overwrite, uninstall delete, stale-removal) on the target file's HEAD
    bearing a well-formed generated header via Test-SkillMeshProvenance.

    The detection is ANCHORED to the exact header block the builder emits
    (`<!-- GENERATED FILE - DO NOT EDIT. ... Marker: <token> ... -->`), NOT a
    substring-anywhere scan -- so an operator file that merely MENTIONS or quotes the
    token is never misclassified as skill-mesh-owned.

    Both the emit side and the check side live here, so the marker token, the marker
    line, and the header structure cannot drift between the two scripts (code-quality:
    one source of truth for data-shape constants).

    ASCII-only, no BOM (PowerShell 5.1 reads a no-BOM .ps1 as ANSI/cp1252).
#>

function Get-SkillMeshMarker {
    # Distinctive, unlikely-to-collide provenance token.
    return 'SKILL-MESH-GENERATED-FILE'
}

function Get-SkillMeshMarkerLine {
    # The exact "Marker: <token>" line the builder emits inside the header and the
    # installer anchors its detection to. Single-sourced so the prefix cannot drift.
    return ('Marker: ' + (Get-SkillMeshMarker))
}

function Get-SkillMeshHeaderOpen {
    # Opening line of the generated-file provenance header block.
    return '<!-- GENERATED FILE - DO NOT EDIT.'
}

function Test-SkillMeshProvenance([string]$text) {
    # True only when $text contains a WELL-FORMED generated header: the exact opener,
    # then the Marker line with the token, then a comment terminator, in order. Far
    # stricter than a Contains()-anywhere scan -- a file that merely quotes the token
    # (an operator doc, a hand-authored SKILL.md) does NOT match.
    if ([string]::IsNullOrEmpty($text)) { return $false }
    $pattern = [regex]::Escape((Get-SkillMeshHeaderOpen)) +
               '(?:.|\n)*?' +
               [regex]::Escape((Get-SkillMeshMarkerLine)) +
               '(?:.|\n)*?-->'
    return [regex]::IsMatch($text, $pattern)
}
