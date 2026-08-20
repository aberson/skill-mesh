"""Single-owner guard for the autofix-marker contract (Step 9, issue #126).

`skills/plan-review/core.md` section "Autofix marker" is the ONE owner of the
marker contract among the canonical `skills/` tree; `skills/plan-wrap/core.md`
applies it by citation and restates only a bounded cite-site minimum, never the
literal regex. The link gate (test_link_resolution.py) now covers the cited
path's existence -- plan-wrap's citation is an explicitly-relative markdown
link -- but it cannot see the definition re-duplicated into another file, the
definition leaving the cited section, a renamed owner heading, or the citation
being deleted outright. Those are what these assertions add (the prose analogue
of "regression tests must assert `is`, not just `==`").
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

OWNER = "skills/plan-review/core.md"
CITER = "skills/plan-wrap/core.md"
OWNER_HEADING = re.compile(r"^### Autofix marker\s*$", re.MULTILINE)
# The normative literal regex, as prose bytes -- used as a plain substring
# probe, never compiled. Its one home is the owner section.
MARKER_REGEX_TEXT = r"<!-- autofix-applied: \d{4}-\d{2}-\d{2} -->"


def test_autofix_marker_regex_has_exactly_one_owner():
    # Enumerated by glob, never hand-listed: a hand-maintained list cannot see
    # a new file re-duplicating the definition. The sweep is every markdown
    # file under skills/ (cores, provider adapters, and anything else) plus
    # _shared/, so a duplicate landing in an adapter, a core-less skill, or a
    # shared doc goes red. The legacy top-level */SKILL.md packages are
    # deliberately out of scope: they are policy-frozen pre-2026-08-19 copies
    # (not canonical, not a build input, never installed) per the
    # deprecation-window record in documentation/parity-deltas.md.
    sources = sorted(
        [*REPO_ROOT.glob("skills/**/*.md"), *REPO_ROOT.glob("_shared/**/*.md")]
    )
    assert (REPO_ROOT / OWNER) in sources, "owner core missing from the sweep"

    carriers = [
        p.relative_to(REPO_ROOT).as_posix()
        for p in sources
        if MARKER_REGEX_TEXT in p.read_text(encoding="utf-8")
    ]
    assert carriers == [OWNER], (
        f"the normative marker regex must live in exactly one file across "
        f"skills/ and _shared/ ({OWNER}); found in: {carriers}")

    owner_text = (REPO_ROOT / OWNER).read_text(encoding="utf-8")
    heading = OWNER_HEADING.search(owner_text)
    assert heading, (
        "owner heading '### Autofix marker' renamed or removed -- every "
        "citation to it now dangles; rename the citations in the same change "
        "or revert")

    # Bind the definition to the section every citation names: the normative
    # regex and its Format bullet must live INSIDE '### Autofix marker', not
    # merely somewhere in the owner file.
    end = owner_text.find("\n### ", heading.end())
    if end == -1:
        end = len(owner_text)
    section = owner_text[heading.start():end]
    assert MARKER_REGEX_TEXT in section, (
        "the normative regex left the '### Autofix marker' section the "
        "citations name -- move it back or re-point every citation")
    assert "- **Format:**" in section, (
        "the Format bullet left the '### Autofix marker' section the "
        "citations name -- move it back or re-point every citation")


def test_plan_wrap_cites_the_owner_without_restating_it():
    citer_text = (REPO_ROOT / CITER).read_text(encoding="utf-8")
    # The relative spelling resolves in the canonical tree AND in every emitted
    # or installed tree, where the two skills are siblings.
    assert "../plan-review/core.md" in citer_text, (
        f"{CITER} lost its citation to the marker-contract owner")
    assert "Autofix marker" in citer_text, (
        f"{CITER} no longer names the owner section it binds to")
    # Canaries on phrases the cite site must never carry. 'ISO 8601' is the
    # one format phrase the deliberate cite-site minimum omits (the minimum
    # DOES carry 'YYYY-MM-DD, no time, no timezone, no whitespace' by design;
    # regex-level duplication is covered by the sweep above). The other two
    # are the retired per-fix phrasings, which must not be revived here.
    for phrase in ("ISO 8601", "for each applied fix", "per-finding-class"):
        assert phrase not in citer_text, (
            f"{CITER} carries the owner-only or retired phrase {phrase!r} -- "
            f"cite {OWNER} section 'Autofix marker' instead of duplicating it")
