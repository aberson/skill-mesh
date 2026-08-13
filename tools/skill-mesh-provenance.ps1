<#
.SYNOPSIS
    skill-mesh-provenance.ps1 -- the SINGLE source of truth for the provenance marker
    that stamps every skill-mesh-generated file, AND for the anchored check that
    decides whether bytes on disk have a well-formed generated-header shape.

.DESCRIPTION
    File-content provenance is a generated-looking CANDIDATE signal, not proof of
    current-byte authorship: a consumer can retain or reproduce a valid header. The
    builder (build-distributions.ps1) embeds the marker LINE in every generated file's
    provenance header; the installer (install-skill-mesh.ps1) gates every destructive
    op (install overwrite, uninstall delete, stale-removal) on the target file's HEAD
    bearing a well-formed generated header via Test-SkillMeshProvenance.

    The detection is ANCHORED to the exact header block the builder emits
    (`<!-- GENERATED FILE - DO NOT EDIT. ... Marker: <token> ... -->`), NOT a
    substring-anywhere scan -- so a bare token mention or an ordinary fenced quotation
    is rejected. An exact header at an emitter-legal position still matches and must
    be combined with independent path/ledger/current-byte authority before destruction. Three anchors carry that shape check
    (line start, marker-line adjacency, emitter-legal position); Get-SkillMeshHeaderSpan
    holds all three and Test-SkillMeshProvenance is its boolean face.

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
    # the shipped .js fail the generated-header-candidate check, depriving lifecycle
    # operations of one required guard and risking an orphan. A conforming header is
    # still only candidate evidence; path/ledger/current-byte authority remains
    # independent. Wrapping verbatim keeps the emit side and check side one shape.
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
    # ships a file that is marker-valid (so the shared parser sees a generated-looking
    # candidate, not proof that install or uninstall may mutate it) and does NOT parse --
    # the same leading-directive hazard Add-PythonProvenance solves for __future__
    # imports, which is why
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

# Upper bound on the continuation lines between the Marker line and the block's
# `-->`. The builder emits three; the cap only has to stop an unterminated opener
# from swallowing an arbitrarily long document while it hunts for a terminator.
$script:SKILL_MESH_HEADER_MAX_LINES = 16

function Test-SkillMeshHeaderPreamble([string]$pre) {
    # Is $pre an EMITTER-LEGAL run of bytes in front of the header block?
    #
    # Mirrors, one branch per emitter, the four placements the build actually
    # produces -- Add-Provenance (bare or after YAML frontmatter), Add-JsProvenance,
    # Add-PythonProvenance. That mirroring is the point: it is what lets the check
    # say "this header is where an emitter would have PUT one" rather than only
    # "these bytes look like a header", and a verbatim quotation of the header inside
    # a document body is the case only the position anchor can reject.
    #
    # A branch added to build-distributions.ps1 without a branch added here would
    # strand real payload files, so tests/distributions/test_distributions.py runs
    # this predicate (via Test-SkillMeshProvenance) over EVERY emitted file of a real
    # build -- a new placement reds there rather than shipping bytes the parser cannot
    # recognize as generated-header candidates.
    if ($null -eq $pre -or $pre.Length -eq 0) { return $true }
    # Add-Provenance, frontmatter branch. The emitter inserts after the FIRST
    # closing delimiter. An end-anchored lazy regex can backtrack to a later Markdown
    # horizontal rule and falsely bless a quoted header in the document body, so
    # match the first block and require that it consumes the complete preamble.
    $frontmatter = [regex]::Match($pre, '^---\r?\n[\s\S]*?\r?\n---\r?\n')
    if ($frontmatter.Success -and $frontmatter.Length -eq $pre.Length) { return $true }
    # Add-JsProvenance: `/*` at the top, after a line-1 hashbang when there is one.
    if ([regex]::IsMatch($pre, '^(?:#![^\r\n]*\r?\n)?/\*\r?\n$')) { return $true }
    # Add-PythonProvenance: inserted after the FIRST '"""', which that emitter
    # requires to start within the first 256 characters.
    if ([regex]::IsMatch($pre, '^(?:(?!""")[\s\S]){0,256}"""\r?\n$')) { return $true }
    return $false
}

function Get-SkillMeshHeaderSpan([string]$text) {
    # Start + length of the ONE well-formed generated header block in $text, or null.
    # Get-SkillMeshHeaderStart and Get-SkillMeshHeaderBlock are its public faces: the
    # former preserves the generated-candidate parser's historical offset contract; the latter
    # lets metadata consumers inspect ONLY the validated block rather than accidentally
    # reading a lookalike field from arbitrary body text after its `-->` terminator.
    #
    # THREE anchors, every one of them satisfied by construction by the emitters and
    # none of them by a document that talks ABOUT the header:
    #
    #   1. LINE START -- the opener begins a line. All 211 files of a real build do.
    #   2. ADJACENCY  -- the `Marker:` line is the line IMMEDIATELY after the opener,
    #      and the `-->` closes the SAME uninterrupted block: no blank line between
    #      them, at most $SKILL_MESH_HEADER_MAX_LINES continuation lines. This is the
    #      anchor the previous `(?:.|\n)*?` shape lacked, which let the three tokens
    #      be scattered across an entire document and still read as one header.
    #   3. POSITION   -- everything in FRONT of the block is an emitter-legal preamble
    #      (Test-SkillMeshHeaderPreamble). Contiguity alone cannot tell a real header
    #      from a verbatim copy of one quoted inside a file's body, and under
    #      migrate-legacy-install.ps1's per-file `_shared` rule that difference is one
    #      required signal for a guarded retire of a candidate resident under the
    #      retired project-root tree. Active-root candidates are advisory and retained.
    #
    # Tolerant on purpose about everything that legitimately varies: CRLF or LF, the
    # indent width of the continuation lines, and how many of them there are -- none
    # of which distinguishes our bytes from anyone else's.
    if ([string]::IsNullOrEmpty($text)) { return $null }
    # A decoded UTF-8 BOM is not part of the header question, and leaving it in front
    # would make offset 0 itself an illegal preamble.
    $t = $text.TrimStart([char]0xFEFF)
    $delta = $text.Length - $t.Length
    $open = [regex]::Escape((Get-SkillMeshHeaderOpen))
    $marker = [regex]::Escape((Get-SkillMeshMarkerLine))
    # A continuation line: non-blank, consumed lazily so the FIRST '-->' terminates.
    $cont = '(?:(?![ \t]*\r?\n)[^\r\n]*\r?\n){0,' + $script:SKILL_MESH_HEADER_MAX_LINES + '}?'
    $pattern = '(?m)^' + $open + '[^\r\n]*\r?\n' +
               '[ \t]*' + $marker +
               '(?:[^\r\n]*-->' +
               '|[^\r\n]*\r?\n' + $cont + '(?![ \t]*\r?\n)[^\r\n]*?-->)'
    $m = [regex]::Match($t, $pattern)
    while ($m.Success) {
        if (Test-SkillMeshHeaderPreamble ($t.Substring(0, $m.Index))) {
            return [PSCustomObject]@{ start = ($m.Index + $delta); length = $m.Length }
        }
        $m = $m.NextMatch()
    }
    return $null
}

function Get-SkillMeshHeaderStart([string]$text) {
    # Character offset of the validated generated header block, or -1.
    $span = Get-SkillMeshHeaderSpan $text
    if ($null -eq $span) { return -1 }
    return [int]$span.start
}

function Get-SkillMeshHeaderBlock([string]$text) {
    # Exact validated header bytes, bounded at the terminator matched by the shared
    # parser. Metadata after `-->` is body content and is never part of this result.
    $span = Get-SkillMeshHeaderSpan $text
    if ($null -eq $span) { return $null }
    return $text.Substring([int]$span.start, [int]$span.length)
}

function Test-SkillMeshProvenance([string]$text) {
    # True only when $text carries a WELL-FORMED generated header block at a position
    # an emitter could have put it. See Get-SkillMeshHeaderStart for the three anchors
    # -- a file that merely quotes or documents the token does NOT match.
    return ((Get-SkillMeshHeaderStart $text) -ge 0)
}
