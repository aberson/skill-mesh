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

    Add-JsProvenance is the .js comment-syntax adapter for that same header: it wraps
    the builder's header VERBATIM in /* */ rather than authoring a JS-flavoured marker
    of its own, so a shipped .js payload passes Test-SkillMeshProvenance exactly like
    every .md and .py file does. It also keeps a leading '#!' hashbang on line 1, where
    it is the only place it is legal -- provenance validity and PARSE validity are two
    different properties and the emitter owes both.

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

function Add-JsProvenance([string]$body, [string]$header) {
    # Stamp a JavaScript payload with the generated-file header.
    #
    # $header MUST be the builder's New-ProvenanceHeader output, and it is embedded
    # VERBATIM -- only wrapped in a /* */ block comment so the file stays valid JS.
    # A hand-rolled '/* skill-mesh generated */' marker of our own wording would NOT
    # satisfy Test-SkillMeshProvenance below, which is anchored to the exact three-part
    # shape (opener -> Marker line -> comment terminator). A non-conforming marker makes
    # the shipped .js FOREIGN to install-skill-mesh.ps1, invisible to owned_files, and
    # undeletable by uninstall -- an orphan on disk that a no-orphan gate still calls
    # clean. Wrapping verbatim is what keeps the emit side and the check side one shape.
    if ([string]::IsNullOrEmpty($header)) {
        throw "skill-mesh-provenance: Add-JsProvenance requires a provenance header"
    }
    if ($header.Contains('*/')) {
        # A '*/' inside the header would terminate the comment early and leave the
        # remainder of the marker as executable JS. Refuse rather than emit a file
        # that is neither valid JS nor provenance-valid.
        throw "skill-mesh-provenance: provenance header contains '*/' and cannot be wrapped as a JS comment"
    }
    $block = "/*`n" + $header + "`n*/`n`n"
    # A '#!' hashbang is legal ONLY on line 1. Prepending the comment block over it
    # ships a file that is marker-valid (so install owns it, uninstall removes it, and
    # every provenance assertion is green) and does NOT parse -- the same leading-
    # directive hazard Add-PythonProvenance solves for __future__ imports, which is why
    # this emitter must solve it too rather than prepending unconditionally.
    if ($body.StartsWith('#!')) {
        $nl = $body.IndexOf("`n")
        if ($nl -lt 0) {
            # Hashbang-only file (no newline): keep it on its own first line.
            return $body + "`n" + $block
        }
        return $body.Substring(0, $nl + 1) + $block + $body.Substring($nl + 1)
    }
    return $block + $body
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
