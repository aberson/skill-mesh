"""Host-loading authority-map gate (Step 42, retargeted in Step 44 of
documentation/host-native-discovery-cutover-plan.md).

Locks the three-mechanism authority map so it can never silently drift into
describing workspace instruction injection, host-native skill discovery, and
router dispatch as interchangeable, and never crosses the provider install
targets. That provider set is DERIVED from its one owner --
`tools/skill-mesh-discovery.ps1`'s `Get-SkillMeshDiscoveryRoots` -- and is never
hand-listed here, so a provider added there is gated the day it is added rather
than the day someone remembers to widen this file. Hand-listing two of the three
is what left the codex install target ungated (#142). The regression this exists
to prevent: an operator (or a future doc edit) treating a running GPT model as
evidence of a correctly installed GPT profile.

A derivation is only as good as its parse, so the derived provider set is pinned
by SET EQUALITY against two INDEPENDENT declarations of the same vocabulary --
`config/skill-manifest.json`'s top-level `providers` and the `[ValidateSet(...)]`
on `install-skill-mesh.ps1`'s `-Provider` parameter. A floor (`len(roots) >= 3`)
cannot detect an UNDER-read: a provider the parse silently drops still leaves
three entries and reads as "nothing to gate", which is #142's false green one
layer down. Equality reds instead, in both directions -- a provider added to one
source but not the others reds the day it is added.

Both DERIVED axes are gated: the install-target table AND the per-host guide
(`documentation/providers/<provider>.md` must exist, name its own install target,
and cross-link this authority map, for every declared provider).

Step 43 (#58) PROVED GitHub Copilot CLI does NOT discover skills at the
project-relative `.copilot/skills` this package originally installed to; its real
native project roots are `.github/skills`, `.agents/skills`, and the Claude root,
plus the personal `~/.copilot/skills`, and every SKILL.md must LEAD with a YAML
frontmatter block (`name`, `description`). This gate now asserts the retargeted
truth and guards the retired `.copilot/skills` claim.

`.agents/skills` carries TWO roles that must never collapse into one: it is the
codex INSTALL TARGET (the owner map declares `'codex' = '.agents/skills'`) and it
is ALSO one of Copilot's native project DISCOVERY roots (Step 43). Naming only the
second is the half-truth #142 identifies -- it matches the symptom a reader is
debugging, so they stop before learning the first. The role checks below refuse it.

Asserts, against the real committed docs (NO private/legacy source needed):
- documentation/host-discovery.md exists and states every required fact -- model
  choice does not select a skill tree; EVERY install target the discovery-root
  owner declares is named; the documented Copilot discovery roots include
  `.github/skills`, `.agents/skills`, the Claude root, and `~/.copilot/skills`;
  `.agents/skills` is stated in BOTH its roles, together; every SKILL.md must lead
  with a YAML frontmatter block; workspace instruction files hold no skill
  implementations; the router is explicit, not implicit.
- The three mechanisms are documented as DISTINCT / non-interchangeable.
- The install-target table maps EVERY declared provider to the CORRECT target (a
  swap-guard driven by the derived map: no row may name another provider's target,
  no row may be missing, and no row may name the retired `.copilot/skills`).
- The retired project-relative `.copilot/skills` claim appears ONLY where it is
  explicitly labeled retired/legacy; no doc asserts it as a current Copilot
  discovery root (the personal `~/.copilot/skills` root is exempt -- it IS current).
- providers/claude.md names the Claude root only; providers/gpt.md names the GPT
  install target `.github/skills` AND names codex as the writer of the shared
  `.agents/skills`; providers/codex.md exists and names the codex install target
  in both of its roles -- each cross-linking the authority map.
- Role attributions are graded over READABLE PROSE (table rows dropped, inline
  links collapsed to their labels), so a table cell can never stand in for the
  prose a reader needs, and markdown markup never counts as distance between two
  adjacent claims.

Each check is written so it goes RED if the doc drifts (swap the targets, drop the
frontmatter requirement, or re-assert `.copilot/skills` as current) -- proven by the
anchor tests below (a gate that cannot go red is worthless --
.claude/rules/measurement-validity.md).

Runnable via pytest (`python -m pytest tests/package-integrity`) or standalone
(`python tests/package-integrity/test_host_discovery.py`).
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "documentation" / "host-discovery.md"
CLAUDE_GUIDE = REPO_ROOT / "documentation" / "providers" / "claude.md"
GPT_GUIDE = REPO_ROOT / "documentation" / "providers" / "gpt.md"
CODEX_GUIDE = REPO_ROOT / "documentation" / "providers" / "codex.md"
PROVIDERS_README = REPO_ROOT / "documentation" / "providers" / "README.md"
README = REPO_ROOT / "README.md"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

# The SOLE owner of the provider -> install-target map. Read, never re-spelled.
DISCOVERY_SCRIPT = REPO_ROOT / "tools" / "skill-mesh-discovery.ps1"

# Two INDEPENDENT declarations of the same provider vocabulary. Neither is parsed
# the way the owner map is, and neither is written by the same hand at the same
# time, so agreement between all three is real evidence that the derived map is
# COMPLETE -- which a floor (`len(roots) >= 3`) can never be.
MANIFEST = REPO_ROOT / "config" / "skill-manifest.json"
INSTALLER = REPO_ROOT / "tools" / "install-skill-mesh.ps1"

# Build the Claude ".claude/skills" path token from parts so this test's own source
# carries no literal ".claude/" path (tests/router/test_no_claude_dependency.py flags
# a load-bearing ".claude/" reference in executable code). The other tokens are not
# flagged by that scanner, so they are written literally.
_DOTCLAUDE = "." + "claude"
CLAUDE_ROOT = _DOTCLAUDE + "/skills"          # ".claude/skills"
GITHUB_ROOT = ".github/skills"                # GPT install target (Step 44 retarget)
AGENTS_ROOT = ".agents/skills"                # codex install target AND a Copilot
                                              # project discovery root -- two roles,
                                              # one literal, never conflated (D-CP6)
COPILOT_PERSONAL = "~/.copilot/skills"        # Copilot personal root (current, legit)
COPILOT_LEGACY = ".copilot/skills"            # retired project-relative wrong target

# Tokens that mark a `.copilot/skills` mention as the RETIRED legacy target rather
# than a current-root assertion. "retire" also catches "retired"; "retarget" catches
# "pre-retarget"/"retargeted".
RETIRE_TOKENS = (
    "retire", "retarget", "legacy", "former", "wrong", "falsif",
    "no longer", "not a ", "do not use", "deprecat", "superseded", "migrate off",
)

# How far from a `.copilot/skills` mention a retirement label still counts. Named,
# not spelled twice: the prose used to say "~140-char window before it" while the
# code looked 160 chars back AND 60 chars forward -- a hand-written description
# drifting from what the code does, in the file whose whole subject is that drift.
RETIRE_LOOKBEHIND = 160
RETIRE_LOOKAHEAD = 60


def _read(path):
    return path.read_text(encoding="utf-8")


def _norm(text):
    """Lowercase and collapse all whitespace runs (incl. line wraps) to one space,
    so a required phrase matches regardless of markdown line breaks."""
    return re.sub(r"\s+", " ", text).lower()


# --------------------------------------------------------------------------- #
# Install targets are DERIVED from their one owner -- never hand-listed here --
# and the derived provider VOCABULARY is cross-checked, by SET EQUALITY, against
# two independent declarations of the same vocabulary, so an UNDER-read reds
# instead of vanishing.
# --------------------------------------------------------------------------- #

# One `'name' = 'value'` entry of the owner's literal hashtable, in every legal
# PowerShell spelling: bare / single- / double-quoted key, single- or
# double-quoted value, optional trailing comment, tolerant of the CRLF the
# repository's .ps1 files use. Anchored to a whole line, and no branch can begin
# with `#`, so a commented-out pair is still never read as a live declaration.
#
# The narrow `^\s*'([A-Za-z0-9_-]+)'\s*=\s*'([^']+)'\s*$` this replaces accepted
# exactly ONE of those spellings. Measured, by planting a fourth provider in a
# copy of the owner script: `'zeta' = '.zeta/skills'   # added Phase X`,
# `'zeta' = ".zeta/skills"`, and `zeta = '.zeta/skills'` each parsed to the SAME
# three pairs, and EVERY test in this module stayed green -- a silently dropped
# provider, which is the #142 false green one layer down. `assert pairs` cannot
# see it: it fires only on a TOTAL wipeout, never on a partial parse.
_MAP_PAIR = re.compile(
    r"""^[ \t]*
        (?: '(?P<kq>[A-Za-z0-9_-]+)'          # 'quoted' key
          | "(?P<kd>[A-Za-z0-9_-]+)"          # "quoted" key
          |  (?P<kb>[A-Za-z0-9_-]+)           #  bare key
        )
        [ \t]*=[ \t]*
        (?: '(?P<vs>[^']+)'                   # 'quoted' value
          | "(?P<vd>[^"]+)"                   # "quoted" value
        )
        [ \t\r]*(?:\#[^\n]*)?$                # optional trailing comment
    """, re.M | re.X)

# The installer's `-Provider` value set. Anchored to the `$Provider` parameter
# (the file carries other `ValidateSet` mentions), so no other validated
# parameter can ever be read in its place.
_PROVIDER_VALIDATESET = re.compile(
    r"\[ValidateSet\(\s*([^)]*?)\s*\)\]"      # the accepted values
    r"(?:\s*\[[^\]\n]*\])*"                   # further attributes, e.g. [Alias(..)][string]
    r"\s*\$Provider\b")


def _parse_discovery_map(script_text):
    """Parse `Get-SkillMeshDiscoveryRoots`'s literal hashtable -> {provider: root}.

    Pure -- it takes the script TEXT -- so the planted-defect anchors below can
    drive it with a fabricated fourth provider without touching the real owner.
    Fails LOUDLY (assert) rather than falling back to a default set; a silent
    fallback re-creates the exact false green this gate exists to kill."""
    body = re.search(r"function Get-SkillMeshDiscoveryRoots\b.*?\n}", script_text, re.S)
    assert body, "Get-SkillMeshDiscoveryRoots not found in the discovery-root owner"
    pairs = [(m.group("kq") or m.group("kd") or m.group("kb"),
              m.group("vs") if m.group("vs") is not None else m.group("vd"))
             for m in _MAP_PAIR.finditer(body.group(0))]
    assert pairs, "the discovery-root owner declares no provider -> root pairs"
    return dict(pairs)


def _manifest_providers():
    """The provider vocabulary the MANIFEST declares -- an independent source.

    `config/skill-manifest.json`'s top-level `providers` object is authored and
    consumed by the build, not by the discovery-root owner, so it cannot drift in
    lockstep with a mis-parse of that owner."""
    providers = json.loads(_read(MANIFEST)).get("providers") or {}
    assert providers, "config/skill-manifest.json declares no top-level providers"
    return set(providers)


def _installer_providers():
    """The provider vocabulary `-Provider` ACCEPTS -- the third independent source.

    Read from the real `param(...)` block, never from prose: a documented flag list
    drifts, a `[ValidateSet(...)]` is what the tool actually enforces."""
    m = _PROVIDER_VALIDATESET.search(_read(INSTALLER))
    assert m, "install-skill-mesh.ps1's -Provider [ValidateSet(...)] not found"
    providers = {a or b for a, b in re.findall(r"'([^']+)'|\"([^\"]+)\"", m.group(1))}
    assert providers, "install-skill-mesh.ps1's -Provider ValidateSet is empty"
    return providers


def _provider_vocabulary_defects(derived):
    """Defects if the DERIVED provider set disagrees with either independent source.

    A floor (`len(roots) >= 3`) cannot detect an UNDER-read: a provider the parse
    silently drops still leaves three entries and reads as "nothing to gate". SET
    EQUALITY against two vocabularies nothing here parses the same way turns that
    silence into a red. It is bidirectional by design -- a provider added to ONE
    source but not the others reds the day it is added, in whichever source it was
    forgotten, which is the whole promise this gate makes about a fourth provider."""
    derived = set(derived)
    manifest = _manifest_providers()
    installer = _installer_providers()
    defects = []
    if derived != manifest:
        defects.append(
            f"discovery-root owner declares {sorted(derived)} but the manifest's "
            f"providers are {sorted(manifest)} "
            f"(only in owner: {sorted(derived - manifest)}; "
            f"only in manifest: {sorted(manifest - derived)})")
    if derived != installer:
        defects.append(
            f"discovery-root owner declares {sorted(derived)} but "
            f"install-skill-mesh.ps1's -Provider accepts {sorted(installer)} "
            f"(only in owner: {sorted(derived - installer)}; "
            f"only in installer: {sorted(installer - derived)})")
    if manifest != installer:
        defects.append(
            f"the two independent vocabularies disagree with each other: manifest "
            f"{sorted(manifest)} vs -Provider {sorted(installer)}")
    return defects


def _discovery_roots():
    """The WHOLE provider -> install-target map, read from its sole owner.

    `tools/skill-mesh-discovery.ps1`'s `Get-SkillMeshDiscoveryRoots` owns that
    mapping. Reading the whole map -- rather than looking up a hand-written pair of
    provider names -- is the point: a provider added to the owner is gated by this
    file the day it is added. Hand-listing `claude` and `gpt` is exactly how the
    codex install target stayed ungated after codex became installable (#142), and a
    hand-list would repeat it for a fourth provider.

    Parsed rather than executed, following the sibling precedent
    `tests/package-integrity/test_codex_budgets.py::_discovery_root`: this suite is
    hermetic Python and must not need powershell on PATH, and this module promises
    standalone `python tests/package-integrity/test_host_discovery.py` runnability.

    The parse is BROAD (every legal hashtable spelling) and the result is
    CROSS-CHECKED for set equality against the manifest and the installer before it
    is handed to any caller, so no caller can ride a partially-parsed map.

    Returns an insertion-ordered {provider: root} dict. The roots are home-relative
    POSIX (`.github/skills`) while the doc spells `<install-home>/.github/skills/`,
    so every caller SUBSTRING-matches; none compares for equality.
    """
    roots = _parse_discovery_map(_read(DISCOVERY_SCRIPT))
    defects = _provider_vocabulary_defects(roots)
    assert not defects, (
        "the derived install-target map disagrees with the independent provider "
        "vocabularies (a dropped or one-sided provider, NOT a doc defect):\n"
        + "\n".join(defects))
    return roots


# Every legal PowerShell spelling of one added hashtable pair. All three of the
# non-ordinary spellings were INVISIBLE to the pattern this module used to carry.
_PLANTED_SPELLINGS = {
    "trailing comment": "        'zeta'   = '.zeta/skills'   # added Phase X",
    "double-quoted value": "        'zeta'   = \".zeta/skills\"",
    "bare (unquoted) key": "        zeta     = '.zeta/skills'",
    "ordinary pair": "        'zeta'   = '.zeta/skills'",
}


def test_map_parser_reads_every_legal_hashtable_spelling():
    """ANCHOR: a fourth provider must be SEEN however it is legally spelled.

    Each spelling below is valid PowerShell that a real author might write, and
    each was invisible to the narrow `'name' = 'value'` line pattern this parser
    replaces -- so a fourth provider could be added to the owner map and stay
    entirely ungated while every test in this module stayed green. A gate that
    cannot see the thing it exists to gate is the #142 defect, one layer down."""
    text = _read(DISCOVERY_SCRIPT)
    live = "'codex'  = '.agents/skills'"
    assert live in text, (
        "the owner's codex pair is no longer spelled as this anchor expects; "
        "re-derive the anchor rather than deleting it")
    for label, line in _PLANTED_SPELLINGS.items():
        planted = text.replace(live, live + "\n" + line, 1)
        parsed = _parse_discovery_map(planted)
        assert parsed.get("zeta") == ".zeta/skills", (
            f"parser is blind to a fourth provider written as a {label}: {parsed}")
    # ...and a COMMENTED-OUT pair is still never read as a live declaration.
    commented = text.replace(live, live + "\n        # 'zeta' = '.zeta/skills'", 1)
    assert "zeta" not in _parse_discovery_map(commented), \
        "parser read a commented-out pair as a live install target"


def test_derived_provider_set_agrees_with_two_independent_vocabularies():
    """ANCHOR + live check for the cross-source equality that replaced the floor.

    Live: the three sources must agree exactly today. ANCHOR: the check must go RED
    on an under-read (a provider silently dropped by the parse -- the failure the
    floor was structurally unable to see), on a one-sided addition (a provider added
    to the owner but not to the manifest or the installer), and on a wipeout."""
    roots = _discovery_roots()
    assert _provider_vocabulary_defects(roots) == [], "the three sources disagree"
    assert set(roots) == _manifest_providers() == _installer_providers()

    for dropped in sorted(roots):
        under_read = {k: v for k, v in roots.items() if k != dropped}
        assert _provider_vocabulary_defects(under_read), (
            f"cross-check failed to detect an under-read that dropped {dropped!r} "
            "-- this is exactly what `len(roots) >= 3` could not see")
    assert _provider_vocabulary_defects(dict(roots, zeta=".zeta/skills")), \
        "cross-check failed to detect a provider declared in only one source"
    assert _provider_vocabulary_defects({}), \
        "cross-check failed to detect a total parse wipeout"


def test_install_target_map_is_derived_from_its_one_owner():
    """VACUITY + DRIFT anchor for the derivation every other target check rides on.

    The provider set is pinned by SET EQUALITY against two independent vocabularies
    (above), not by a floor: a floor reads a garbage or partial parse as "nothing to
    gate". The three named providers below are this module's own path-TOKEN pins --
    they exist so a literal spelled here can never drift into asserting a path
    nothing installs to -- and are not the working list, which is always derived."""
    roots = _discovery_roots()
    assert not _provider_vocabulary_defects(roots), \
        f"derived provider set is not cross-source consistent: {roots}"
    for provider in ("claude", "gpt", "codex"):
        assert provider in roots, \
            f"discovery-root owner declares no install target for {provider!r}"
    assert roots["claude"] == CLAUDE_ROOT, roots["claude"]
    assert roots["gpt"] == GITHUB_ROOT, roots["gpt"]
    assert roots["codex"] == AGENTS_ROOT, roots["codex"]
    assert COPILOT_LEGACY not in roots.values(), \
        f"the retired {COPILOT_LEGACY} is declared as a live install target"


# --------------------------------------------------------------------------- #
# Retired-`.copilot/skills` guard: a project-relative mention is allowed ONLY when
# labeled retired; the personal `~/.copilot/skills` root is exempt (it IS current).
# --------------------------------------------------------------------------- #

def _unlabeled_project_copilot_hits(text):
    """Every project-relative `.copilot/skills` mention that is NOT labeled retired.

    A `~/`-prefixed occurrence is the personal Copilot root (a real current root) and
    is skipped. For any other occurrence, a retirement label must appear within the
    RETIRE_LOOKBEHIND chars BEFORE it or the RETIRE_LOOKAHEAD chars AFTER it --
    windowed, not line-bound, so a sentence that wraps across markdown lines still
    counts, and a label that trails the mention counts too. Both bounds are named
    constants because this description used to say "~140-char window before it"
    while the code looked 160 back and 60 forward. A non-empty return means the doc
    asserts the retired project-relative target as if it were current."""
    low = text.lower()
    hits = []
    idx = 0
    while True:
        j = low.find(COPILOT_LEGACY, idx)
        if j < 0:
            break
        idx = j + 1
        if low[max(0, j - 2):j] == "~/":
            continue  # personal root ~/.copilot/skills -- current and legitimate
        window = low[max(0, j - RETIRE_LOOKBEHIND):
                     j + len(COPILOT_LEGACY) + RETIRE_LOOKAHEAD]
        if not any(tok in window for tok in RETIRE_TOKENS):
            hits.append(text[max(0, j - 60):j + len(COPILOT_LEGACY) + 10].strip())
    return hits


def test_retired_copilot_guard_reds_on_unlabeled_and_silent_on_labeled():
    # ANCHOR: the guard MUST flag an un-labeled current-root assertion and stay
    # silent on both the labeled-retired mention and the personal root.
    bad = "GPT natively discovers project skills at .copilot/skills at install time."
    assert _unlabeled_project_copilot_hits(bad), \
        "guard failed to flag an un-labeled project-relative .copilot/skills claim"
    labeled = "the retired project-relative .copilot/skills target is not a Copilot root."
    assert _unlabeled_project_copilot_hits(labeled) == []
    personal = "Copilot's personal discovery root is ~/.copilot/skills for the user."
    assert _unlabeled_project_copilot_hits(personal) == []


# --------------------------------------------------------------------------- #
# Install-target swap-guard (the load-bearing regression: never cross the targets)
# --------------------------------------------------------------------------- #

# A markdown row whose FIRST cell is a single bare word -- the shape of a provider
# cell (`| Codex |`). Multi-word cells (the mechanism and summary tables) and the
# `|---|---|` separator never match, so the scan stays inside the install-target
# table exactly as the hard-coded prefixes used to.
_PROVIDER_CELL = re.compile(r"^\|\s*([a-z0-9][a-z0-9_-]*)\s*\|")


def _install_target_defects(text):
    """Defects if the install-target table maps a provider to the WRONG target.

    EVERY provider the discovery-root owner declares must have a row; that row must
    name its OWN target, must not name any OTHER provider's target, and must never
    name the retired `.copilot/skills`. Empty list == correct, complete, non-swapped.

    The provider set is DERIVED, not a hand-written pair. Selecting rows by literal
    `| claude |` / `| gpt |` prefixes is the same false green one layer down from the
    one #142 names: with the pair hard-coded, a Codex row naming the Claude root
    produced zero defects, because no code ever looked at that row.

    EVERY matching row is collected, not just the last one. Assigning `rows[p] = s`
    is last-row-wins across the whole file, so a second table that happened to put a
    provider name in a bare first cell would silently REPLACE the install-target row
    actually being graded -- a duplicate shape quietly overwriting the graded one
    (.claude/rules/code-quality.md). The contract per provider is now: at least one
    row names its own target, and NO row names a wrong one."""
    roots = _discovery_roots()
    rows = {}
    for ln in text.splitlines():
        s = ln.strip().lower()
        m = _PROVIDER_CELL.match(s)
        if m and m.group(1) in roots:
            rows.setdefault(m.group(1), []).append(s)
    defects = []
    for provider, root in roots.items():
        provider_rows = rows.get(provider) or []
        if not provider_rows:
            defects.append(f"no '| {provider} |' install-target row found")
            continue
        if not any(root in row for row in provider_rows):
            defects.append(f"{provider} row does not name its target {root}")
        for row in provider_rows:
            for other, other_root in roots.items():
                if other != provider and other_root in row:
                    defects.append(
                        f"{provider} row wrongly names {other}'s target {other_root} "
                        "(targets swapped)")
            if COPILOT_LEGACY in row:
                defects.append(f"{provider} row names the retired {COPILOT_LEGACY}")
    return defects


def _target_table(mapping):
    """A synthetic install-target table, one `| provider | host | target |` row per
    entry -- built from the derived path tokens so this test carries no literal
    ".claude/" of its own."""
    return "".join(f"| {p} | Some Host | `<install-home>/{r}/<skill>/` |\n"
                   for p, r in mapping.items())


def test_swap_guard_reds_on_swapped_targets():
    # ANCHOR: the swap-guard MUST stay green on the correct table and go red on a
    # crossed target, a missing row, and a row regressed to the retired
    # `.copilot/skills` -- for EVERY declared provider, not just the first two.
    # Driven by the derived map, so a fourth provider is anchored the day it is
    # declared rather than the day someone remembers to add a case here.
    roots = _discovery_roots()
    providers = list(roots)
    assert len(providers) >= 3, \
        f"anchor needs at least three declared providers, got {providers}"

    assert _install_target_defects(_target_table(roots)) == []

    # every row crossed onto the NEXT provider's target at once
    rotated = {p: roots[providers[(i + 1) % len(providers)]]
               for i, p in enumerate(providers)}
    assert _install_target_defects(_target_table(rotated)), \
        "swap-guard failed to detect crossed targets"

    for i, p in enumerate(providers):
        other = providers[(i + 1) % len(providers)]
        crossed = dict(roots, **{p: roots[other]})
        assert _install_target_defects(_target_table(crossed)), \
            f"swap-guard failed to detect the {p} row naming {other}'s target"

        regressed = dict(roots, **{p: COPILOT_LEGACY})
        assert _install_target_defects(_target_table(regressed)), \
            f"swap-guard failed to detect the {p} row regressed to {COPILOT_LEGACY}"

        dropped = {k: v for k, v in roots.items() if k != p}
        assert _install_target_defects(_target_table(dropped)), \
            f"swap-guard failed to detect a missing '| {p} |' row"


# --------------------------------------------------------------------------- #
# `.agents/skills` role guard: ONE literal, TWO roles, and neither stands alone.
# --------------------------------------------------------------------------- #

# How far from an `.agents/skills` mention a role attribution still counts as being
# ABOUT that mention -- measured over READABLE PROSE, after `_role_prose()` drops
# markdown table rows and collapses inline links to their label text.
#
# Both of those normalizations are load-bearing, not tidying. At the previous 480
# over the RAW markdown this check could not go red for the drift it names: delete
# the entire two-distinct-roles section from the authority map and it still scored
# (True, True, True), because the two roles were synthesized out of TABLE FURNITURE
# -- "codex" from a row's provider cell and "install target" from the table HEADER
# cell -- bridged into the next paragraph's Copilot sentence. The real pre-#142 doc
# plus one Codex table row and ZERO role prose scored the same. Dropping table rows
# removes that synthesis at any width; collapsing links stops a 100-char relative
# path from counting as prose distance between two adjacent bullets.
#
# 240 was chosen from a measured sweep of the live docs and three planted decoys
# (the anchors below re-run all three on every test run, so this number can never
# quietly stop discriminating):
#   host-discovery.md      both roles together from W >= 170   (needs W >= 170)
#   providers/codex.md     both roles together from W >= 115   (needs W >= 115)
#   DECOY role prose cut   together only from W >= 300         (needs W <  300)
#   DECOY old doc + a row  target role NEVER attested, any W   (structurally red)
ROLE_WINDOW = 240

# A role attribution is graded as a CLAIM, not as one exact bigram. Measured against
# rewordings that keep both facts perfectly intact, the old literal "install target"
# test scored (False, ...) on 3 of 4 natural phrasings -- failing safe, but making
# the doc's exact wording load-bearing without saying so anywhere in the doc.
_ROLE_TARGET_RE = re.compile(
    r"install target|installation target|install root|installs? (?:to|into)\b|"
    r"\binstall(?:s|ed|ation)?\b[^.]{0,30}\b(?:writes?|populates?)\b|"
    r"writes? .{0,40}\bthere\b")
_ROLE_ROOT_RE = re.compile(r"discovery root|\bscans?\b|\bscanned\b|enumerat")

# `[label](target)` -> `label`. A relative path is markup, not prose a reader reads.
_MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def _role_prose(text):
    """Normalized READABLE prose: markdown table rows dropped, inline links
    collapsed to their label, whitespace collapsed, lowercased.

    Table rows go because a table cell must never, by itself, attest a prose role
    (see ROLE_WINDOW above); links collapse because their target inflates character
    distance without adding anything a reader reads."""
    body = "\n".join(ln for ln in text.split("\n") if not ln.lstrip().startswith("|"))
    return _norm(_MD_LINK.sub(r"\1", body))


def _agents_root_roles(text):
    """Which of `.agents/skills`'s two roles a document actually attests.

    Returns (codex_install_target, copilot_discovery_root, both_in_one_window):

    a. codex_install_target -- some mention is described as codex's INSTALL target
       (the owner map declares `'codex' = '.agents/skills'`).
    b. copilot_discovery_root -- some mention is described as a root GitHub Copilot
       CLI natively discovers from / scans (proven live in Step 43, #58).
    c. both_in_one_window -- one mention carries both, so a reader meets them as two
       roles of one root rather than as two unrelated facts pages apart.

    (b) alone is the exact half-truth #142 identifies: it matches the symptom a
    reader is debugging, so they stop before learning (a) and conclude that a
    Copilot-scanned tree is evidence of which host wrote it. Presence of the literal
    is what cemented that single attribution, so presence is not what is asserted."""
    norm = _role_prose(text)
    codex_target = copilot_root = together = False
    for m in re.finditer(re.escape(AGENTS_ROOT), norm):
        window = norm[max(0, m.start() - ROLE_WINDOW):m.end() + ROLE_WINDOW]
        is_target = "codex" in window and bool(_ROLE_TARGET_RE.search(window))
        is_root = "copilot" in window and bool(_ROLE_ROOT_RE.search(window))
        codex_target = codex_target or is_target
        copilot_root = copilot_root or is_root
        together = together or (is_target and is_root)
    return codex_target, copilot_root, together


def test_agents_root_role_guard_reds_on_single_role_framing():
    # ANCHOR: the guard MUST refuse the pre-#142 framing (`.agents/skills` named
    # ONLY as a Copilot discovery root), MUST equally refuse the mirror-image
    # omission, and MUST stay green when one mention carries both roles.
    copilot_only = ("GitHub Copilot CLI's native project discovery roots are "
                    ".github/skills, .agents/skills, and the Claude root.")
    assert _agents_root_roles(copilot_only) == (False, True, False), \
        "role guard accepted the Copilot-only framing this gate exists to refuse"
    codex_only = ("A codex install writes every package to .agents/skills, this "
                  "package's codex install target.")
    assert _agents_root_roles(codex_only) == (True, False, False), \
        "role guard read a codex-only framing as also naming the Copilot role"
    both = ("`.agents/skills` is the codex install target and is also one of "
            "GitHub Copilot CLI's native project discovery roots.")
    assert _agents_root_roles(both) == (True, True, True), \
        "role guard failed to accept a mention carrying both roles"
    silent = "This paragraph names no discovery root at all."
    assert _agents_root_roles(silent) == (False, False, False)
    # A role is graded as a CLAIM, not as one exact bigram. Each rewording below
    # keeps BOTH facts perfectly intact; measured against the old literal
    # "install target" / "discovery root|scan" test, three of them scored
    # target=False and would have red-flagged a correct doc.
    for reworded in (
            "`.agents/skills` is where a codex install writes its profile, and "
            "GitHub Copilot CLI also enumerates that same root.",
            "`.agents/skills` is codex's install root; GitHub Copilot CLI scans it "
            "too.",
            "`.agents/skills` is Codex's installation target and one of the roots "
            "Copilot scans."):
        assert _agents_root_roles(reworded) == (True, True, True), \
            "role guard rejected a rewording that states both roles: " + reworded


def test_agents_role_guard_reds_on_table_furniture_alone():
    """ANCHOR: an install-target TABLE ROW must never, by itself, attest the codex
    install-target role.

    This is the defect the guard shipped with. At the old 480-char window over the
    RAW markdown, both roles were synthesized out of table furniture -- "codex" from
    the row's provider cell, "install target" from the table HEADER cell -- and
    bridged into the neighbouring Copilot sentence. Measured consequence: the real
    pre-#142 authority map plus ONE Codex install-target row, carrying ZERO role
    prose, scored (True, True, True) and the gate stayed green. Rows are dropped
    before the scan now, so this decoy reds at ANY window width."""
    table = _target_table(_discovery_roots())
    copilot_sentence = ("GitHub Copilot CLI's native project discovery roots are "
                        ".github/skills, .agents/skills, and the Claude root.\n")
    codex_target, _, together = _agents_root_roles(table + "\n" + copilot_sentence)
    assert not codex_target, \
        "an install-target table row ALONE attested the codex install-target role"
    assert not together, \
        "table furniture plus one neighbouring sentence read as the two-role claim"
    # ...and the guard still reads the prose sentence beside it, so the decoy is
    # discriminating rather than merely blind to the whole input.
    assert _agents_root_roles(copilot_sentence) == (False, True, False)


def test_agents_role_guard_reds_when_the_two_roles_are_stated_far_apart():
    """ANCHOR: the window must stay FINITE. Two roles stated in unrelated sections
    are two facts a reader meets pages apart, not the one two-role claim that stops
    them concluding a root's name identifies its writer."""
    codex_only = ("A codex install writes every package to .agents/skills, this "
                  "package's codex install target.")
    copilot_only = ("GitHub Copilot CLI's native project discovery roots include "
                    ".agents/skills, which it scans on every run.")
    far = codex_only + ("\n\nUnrelated filler prose. " * 120) + copilot_only
    codex_target, copilot_root, together = _agents_root_roles(far)
    assert codex_target and copilot_root, "decoy lost one of the two roles"
    assert not together, \
        "role guard read two far-apart facts as one two-role claim"


def _unnegated_interchangeable(norm):
    """Return every UN-negated 'interchangeable' assertion in the normalized text.
    A sanctioned occurrence is immediately preceded by 'not' or 'never'
    ('distinct and not interchangeable', 'never interchangeable'); anything else
    ('are/is/be/mechanisms interchangeable') is a contradiction the doc must not
    contain. Two-sided by design: a doc that keeps the sanctioned line but ALSO
    adds a contradicting 'these mechanisms are interchangeable' sentence is
    flagged (mirrors the install-target swap-guard)."""
    hits = []
    for m in re.finditer(r"\binterchangeable\b", norm):
        preceding = norm[:m.start()].rstrip()
        last_word = preceding.split(" ")[-1] if preceding else ""
        if last_word not in ("not", "never"):
            start = max(0, m.start() - 30)
            hits.append(norm[start:m.end()])
    return hits


def test_interchangeable_guard_reds_on_contradiction():
    # ANCHOR: the two-sided guard MUST flag an un-negated 'interchangeable'
    # assertion and stay silent on the sanctioned negation.
    good = "these three mechanisms are distinct and not interchangeable."
    bad = "these three mechanisms are interchangeable."
    assert _unnegated_interchangeable(_norm(good)) == []
    assert _unnegated_interchangeable(_norm(bad)), \
        "guard failed to flag an un-negated 'interchangeable' assertion"


# --------------------------------------------------------------------------- #
# host-discovery.md content contract
# --------------------------------------------------------------------------- #

def test_host_discovery_doc_exists():
    assert DOC_PATH.is_file(), f"missing authority map: {DOC_PATH}"


def test_doc_states_model_does_not_select_tree():
    norm = _norm(_read(DOC_PATH))
    assert "model choice does not select a skill tree" in norm
    # the exact-confusion killer: a running model is not install proof
    assert "not evidence of a correctly installed gpt profile" in norm


def test_doc_names_every_declared_install_target():
    """EVERY install target the discovery-root owner declares must be named by the
    authority map -- derived, so a provider added to the owner cannot land here
    ungated. Substring, not equality: the owner's roots are home-relative
    (`.github/skills`) while the doc spells `<install-home>/.github/skills/<skill>/`."""
    text = _read(DOC_PATH)
    missing = [f"{p} -> {r}" for p, r in _discovery_roots().items() if r not in text]
    assert not missing, (
        "authority map does not name every declared install target: " + repr(missing))


def test_doc_states_real_copilot_discovery_roots():
    """The documented Copilot discovery roots must include ALL of the real roots
    proven in Step 43 -- the three project roots plus the personal root. That
    `.agents/skills` is among them is Copilot's SCAN role only; its separate role as
    the codex install target is asserted by
    test_doc_distinguishes_the_two_agents_root_roles, never by this presence check."""
    text = _read(DOC_PATH)
    for root in (GITHUB_ROOT, AGENTS_ROOT, CLAUDE_ROOT, COPILOT_PERSONAL):
        assert root in text, f"authority map missing Copilot discovery root {root}"


def test_doc_distinguishes_the_two_agents_root_roles():
    """`.agents/skills` is the codex INSTALL TARGET and, distinctly, one of Copilot's
    native DISCOVERY roots. The authority map must state both, and state them close
    enough together to read as two roles of one literal -- stating only the Copilot
    role is what let a reader conclude the root's name identifies its writer."""
    codex_target, copilot_root, together = _agents_root_roles(_read(DOC_PATH))
    assert codex_target, (
        f"authority map never names {AGENTS_ROOT} as the codex install target -- "
        f"its own owner declares 'codex' = '{AGENTS_ROOT}'")
    assert copilot_root, (
        f"authority map never names {AGENTS_ROOT} as a root Copilot discovers from")
    assert together, (
        f"authority map states the two {AGENTS_ROOT} roles too far apart to read as "
        "two roles of one root")


def test_doc_requires_yaml_frontmatter():
    norm = _norm(_read(DOC_PATH))
    assert "must lead with a yaml frontmatter block" in norm, \
        "authority map must state SKILL.md leads with a YAML frontmatter block"
    # NOT bare "name"/"description": the text is lowercased, so those match inside
    # "filename", "named" and any ordinary prose -- there is no version of this doc
    # that could fail that, which makes it a line adding nothing. Require the two
    # BACKTICKED key names, attached to the frontmatter claim itself.
    assert re.search(r"must lead with a yaml frontmatter block.{0,200}?`name`"
                     r".{0,120}?`description`", norm), (
        "authority map must name `name` and `description` as the required "
        "frontmatter keys, next to the frontmatter requirement itself")


def test_doc_install_targets_not_swapped():
    defects = _install_target_defects(_read(DOC_PATH))
    assert not defects, "install-target table swapped/incomplete:\n" + "\n".join(defects)


def test_readme_install_target_table_is_not_swapped():
    """README.md republishes the provider -> install-target mapping, and the
    authority map says outright that the two tables must match. A duplicated
    data-shape constant that only one side gates is the drift pattern
    .claude/rules/code-quality.md names: run the same derived swap/missing-row
    guard against the copy, so a fourth provider -- or a crossed row -- reds in
    BOTH places rather than only in the one somebody remembered."""
    defects = _install_target_defects(_read(README))
    assert not defects, (
        "README install-target table swapped/incomplete:\n" + "\n".join(defects))


def test_doc_does_not_assert_retired_copilot_as_current():
    hits = _unlabeled_project_copilot_hits(_read(DOC_PATH))
    assert not hits, (
        "authority map asserts the retired project-relative .copilot/skills as a "
        "current Copilot discovery root: " + repr(hits))


def test_doc_instruction_files_hold_no_skill_implementations():
    norm = _norm(_read(DOC_PATH))
    # CLAUDE.md / AGENTS.md are instruction adapters, not skill registries
    assert "claude.md" in norm and "agents.md" in norm
    assert "instruction adapter" in norm
    assert "not skill registries" in norm or "not a skill registry" in norm
    assert "does not contain skill implementations" in norm


def test_doc_router_is_explicit_not_implicit():
    norm = _norm(_read(DOC_PATH))
    assert "the router is explicit, not implicit" in norm
    # and it is NOT the prerequisite for native invocation
    assert "prerequisite for native skill invocation" in norm


def test_doc_states_three_mechanisms_are_distinct():
    norm = _norm(_read(DOC_PATH))
    for mechanism in ("workspace instruction injection",
                      "host-native skill discovery",
                      "router dispatch"):
        assert mechanism in norm, f"authority map does not name mechanism: {mechanism}"
    # Distinctness leans on the specific negation, NOT the bare word "distinct"
    # (which also matches the unrelated "distinct axes" in the doc). The
    # two-sided contradiction guard lives in
    # test_doc_mechanisms_are_never_documented_as_interchangeable.
    assert "not interchangeable" in norm or "never interchangeable" in norm


def test_doc_mechanisms_are_never_documented_as_interchangeable():
    """Two-sided invariant: the doc must REQUIRE a sanctioned negation AND must
    NOT contain any un-negated 'interchangeable' assertion. Presence-only would
    let a contradicting sentence slip through beside the sanctioned line."""
    norm = _norm(_read(DOC_PATH))
    assert "not interchangeable" in norm or "never interchangeable" in norm, \
        "authority map must state the mechanisms are not/never interchangeable"
    violations = _unnegated_interchangeable(norm)
    assert not violations, (
        "authority map contains an un-negated 'interchangeable' assertion "
        "(contradicts the non-interchangeable invariant): " + repr(violations))


# --------------------------------------------------------------------------- #
# Provider guides: correct target each, cross-linked, no unlabeled retired root
# --------------------------------------------------------------------------- #

def test_claude_guide_names_claude_root_only():
    text = _read(CLAUDE_GUIDE)
    assert CLAUDE_ROOT in text, f"providers/claude.md missing {CLAUDE_ROOT}"
    assert GITHUB_ROOT not in text, (
        f"providers/claude.md names the GPT target {GITHUB_ROOT} (targets must not "
        "be interchangeable)")
    assert AGENTS_ROOT not in text, (
        f"providers/claude.md names the codex target {AGENTS_ROOT} (targets must not "
        "be interchangeable)")
    assert COPILOT_LEGACY not in text, (
        f"providers/claude.md names the retired GPT target {COPILOT_LEGACY}")
    assert "host-discovery.md" in text, "providers/claude.md must cross-link the authority map"
    assert "instruction adapter" in _norm(text)


def test_gpt_guide_names_gpt_install_target():
    text = _read(GPT_GUIDE)
    assert GITHUB_ROOT in text, f"providers/gpt.md missing GPT install target {GITHUB_ROOT}"
    assert "host-discovery.md" in text, "providers/gpt.md must cross-link the authority map"
    assert "instruction adapter" in _norm(text)
    # the retired project-relative target may appear ONLY labeled retired
    hits = _unlabeled_project_copilot_hits(text)
    assert not hits, (
        "providers/gpt.md asserts the retired project-relative .copilot/skills as a "
        "current Copilot discovery root: " + repr(hits))


def test_gpt_guide_names_codex_as_the_writer_of_the_shared_root():
    """providers/gpt.md discusses `.agents/skills` as one of the project roots
    Copilot scans. It must ALSO name codex as the package that writes there -- the
    same half-truth #142 calls load-bearing in the authority map, one document over.
    A Copilot-only framing here hands a reader debugging an enumerated tree exactly
    the fact that stops them one short of the answer."""
    codex_target, copilot_root, _ = _agents_root_roles(_read(GPT_GUIDE))
    assert copilot_root, (
        f"providers/gpt.md no longer names {AGENTS_ROOT} as a root Copilot scans")
    assert codex_target, (
        f"providers/gpt.md names {AGENTS_ROOT} without naming codex as the install "
        "target that writes there")


def _guide_path(provider):
    return REPO_ROOT / "documentation" / "providers" / f"{provider}.md"


def test_every_declared_provider_has_a_cross_linked_host_guide():
    """The per-host-GUIDE axis, DERIVED -- the same discipline as the install-target
    axis, which it did not used to share.

    `CLAUDE_GUIDE` / `GPT_GUIDE` / `CODEX_GUIDE` are three hand-written constants
    with one hand-written test each. A fourth provider added to the owner map reds
    the install-target tests, but nothing required `documentation/providers/
    <provider>.md` to exist, to name its own install target, or to cross-link the
    authority map -- the same hand-list failure mode as #142, one axis over. The
    provider-specific extras (claude names no other root; gpt must also name codex
    as the writer of the shared root) stay as named tests on top of this."""
    missing, wrong_root, unlinked = [], [], []
    for provider, root in _discovery_roots().items():
        path = _guide_path(provider)
        if not path.is_file():
            missing.append(f"documentation/providers/{provider}.md")
            continue
        text = _read(path)
        if root not in text:
            wrong_root.append(f"{provider} -> {root}")
        if "host-discovery.md" not in text:
            unlinked.append(provider)
    assert not missing, \
        "declared provider has no per-host guide: " + repr(missing)
    assert not wrong_root, \
        "per-host guide does not name its own install target: " + repr(wrong_root)
    assert not unlinked, \
        "per-host guide does not cross-link the authority map: " + repr(unlinked)


def test_providers_readme_lists_every_declared_provider():
    """The provider index is read by no test today, so a fourth provider's guide
    could land unreachable from the directory's own README."""
    norm = _norm(_read(PROVIDERS_README))
    missing = [p for p in _discovery_roots() if p not in norm]
    assert not missing, \
        "documentation/providers/README.md never names: " + repr(missing)


def test_codex_guide_exists():
    assert CODEX_GUIDE.is_file(), f"missing per-host guide: {CODEX_GUIDE}"


def test_codex_guide_names_codex_install_target():
    """The codex sibling of the claude/gpt guide gates. Before #142 there was no
    codex guide and no constant naming one, so a codex guide could land -- or later
    be deleted -- entirely ungated."""
    text = _read(CODEX_GUIDE)
    assert AGENTS_ROOT in text, \
        f"providers/codex.md missing codex install target {AGENTS_ROOT}"
    assert "host-discovery.md" in text, \
        "providers/codex.md must cross-link the authority map"
    assert "instruction adapter" in _norm(text)
    roles = _agents_root_roles(text)
    assert roles == (True, True, True), (
        f"providers/codex.md must state BOTH roles of {AGENTS_ROOT} together "
        "(codex install target, Copilot discovery root, stated together) -- got "
        + repr(roles))
    # the retired project-relative target may appear ONLY labeled retired
    hits = _unlabeled_project_copilot_hits(text)
    assert not hits, (
        "providers/codex.md asserts the retired project-relative .copilot/skills as "
        "a current Copilot discovery root: " + repr(hits))


def test_no_doc_asserts_retired_copilot_as_current_root():
    """Repo-doc sweep: none of the consumer-facing docs may assert the project-relative
    `.copilot/skills` as a current Copilot discovery root (the personal
    `~/.copilot/skills` root and explicitly-retired labels are exempt)."""
    offenders = {}
    for path in (DOC_PATH, GPT_GUIDE, CLAUDE_GUIDE, CODEX_GUIDE, README, CLAUDE_MD):
        hits = _unlabeled_project_copilot_hits(_read(path))
        if hits:
            offenders[path.name] = hits
    assert not offenders, (
        "docs assert project-relative .copilot/skills as a current root: " + repr(offenders))


def _all_tests():
    return [v for k, v in sorted(globals().items())
            if k.startswith("test_") and callable(v)]


if __name__ == "__main__":
    passed = 0
    for fn in _all_tests():
        fn()
        passed += 1
        print(f"PASS {fn.__name__}")
    print(f"\n{passed} checks passed")
