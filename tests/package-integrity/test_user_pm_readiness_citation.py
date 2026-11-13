"""user-pm's readiness rubric cites user-build-route instead of copying it (v3 user-pm plan Step 6, #231).

The Overnight rubric's three readiness checks (checkout and commit rule, host capability,
agent capacity) are decided by applying user-build-route's section "Check the route can
run". A mocked prose test cannot see drift between the two cores, so this test reads BOTH
files and checks the relationship:

(a) the rubric cites `skills/user-build-route/core.md` and the heading by name;
(b) that heading exists in `skills/user-build-route/core.md` (rename it and this fails);
(c) the rubric names the three gaps;
(d) user-pm restates no route table: no table headed `Route`, and none of the producer's
    route-table criteria copied in;
(e) the rubric's Known-conflict bullet defers short-lived conflicts to the producer's own
    short-lived rule, citing it rather than restating it, and the producer still has one.

The garbage anchors prove each check can fail: a user-pm core with the citation removed,
a producer with the heading renamed, a core missing a gap, a core with the route table
pasted in, and the three ways the short-lived alignment can break.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
USER_PM_CORE = ROOT / "skills" / "user-pm" / "core.md"
ROUTE_CORE = ROOT / "skills" / "user-build-route" / "core.md"
ROUTE_CORE_PATH = "skills/user-build-route/core.md"
HEADING = "Check the route can run"
ROUTE_TABLE_SECTION = "Choose the next slice"
RUBRIC_HEADING = "## Overnight category"
GAP_LABELS = ("**Checkout and commit rule.**", "**Host capability.**", "**Agent capacity.**")
KNOWN_CONFLICT = "- **Known conflict**"
SHORT_LIVED = "short-lived"
NGRAM = 5


def _section(text: str, heading_prefix: str) -> str:
    """The lines of the `## ` section whose heading starts with `heading_prefix`, else ""."""
    lines = text.splitlines()
    for start, line in enumerate(lines):
        if line.startswith(heading_prefix):
            end = next(
                (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
                len(lines),
            )
            return "\n".join(lines[start:end])
    return ""


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9'-]*", text.lower())


def _ngrams(words: list[str]) -> set[tuple[str, ...]]:
    return {tuple(words[i : i + NGRAM]) for i in range(len(words) - NGRAM + 1)}


def _route_criteria(route_core: str) -> list[str]:
    """The producer's route-table "Use when" cells, read from its own table."""
    cells = []
    for line in _section(route_core, f"## {ROUTE_TABLE_SECTION}").splitlines():
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) == 2 and parts[0].startswith("**") and not set(parts[1]) <= set("-: "):
            cells.append(parts[1])
    return cells


def _short_lived_rule(route_core: str) -> str:
    """The producer's short-lived rule: the sentence that defines it and the one after it."""
    section = " ".join(_section(route_core, f"## {HEADING}").split())
    sentences = re.split(r"(?<=[.!?])\s+", section)
    for i, sentence in enumerate(sentences):
        if f"is {SHORT_LIVED}:" in sentence:
            return " ".join(sentences[i : i + 2])
    return ""


def readiness_defects(pm_core: str, route_core: str) -> list[str]:
    """Every way the user-pm rubric has drifted from the route core it cites; empty when aligned."""
    defects: list[str] = []
    rubric = _section(pm_core, RUBRIC_HEADING)
    rubric_lines = rubric.splitlines()
    quoted_heading = f'"{HEADING}"'

    # (b) The cited heading exists in the producer.
    if f"## {HEADING}" not in route_core.splitlines():
        defects.append(f"(b) {ROUTE_CORE_PATH} has no heading '## {HEADING}'")

    # (a) The rubric cites the route core and the heading by name.
    if not rubric:
        defects.append(f"(a) user-pm core has no '{RUBRIC_HEADING}' section")
    if not any(ROUTE_CORE_PATH in line and quoted_heading in line for line in rubric_lines):
        defects.append(f"(a) the rubric does not cite {ROUTE_CORE_PATH} with {quoted_heading}")

    # (c) The rubric names the three gaps.
    for label in GAP_LABELS:
        if not any(line.startswith(f"- {label}") for line in rubric_lines):
            defects.append(f"(c) the rubric does not name the gap {label}")

    # (d) No restated route table.
    for line in pm_core.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|") and cells and cells[0].strip("*") == "Route":
            defects.append(f"(d) user-pm core has a table headed 'Route': {line.strip()}")
    if re.search(r"Route\s*\|\s*Eligibility", pm_core):
        defects.append("(d) user-pm core has a 'Route | Eligibility' table")
    criteria = _route_criteria(route_core)
    if not criteria:
        defects.append(f"(d) cannot read the route table in {ROUTE_CORE_PATH} '{ROUTE_TABLE_SECTION}'")
    flat_pm = " ".join(pm_core.split())
    for cell in criteria:
        if " ".join(cell.split()) in flat_pm:
            defects.append(f"(d) user-pm core copies a route criterion: {cell}")

    # (e) Known-conflict defers short-lived conflicts to the producer's rule, without restating it.
    bullets = [line for line in rubric_lines if line.startswith(KNOWN_CONFLICT)]
    rule = _short_lived_rule(route_core)
    if not rule:
        defects.append(f"(e) {ROUTE_CORE_PATH} '{HEADING}' has no short-lived rule to cite")
    if len(bullets) != 1:
        defects.append(f"(e) expected one Known-conflict bullet in the rubric, found {len(bullets)}")
    for bullet in bullets:
        if not (SHORT_LIVED in bullet and ROUTE_CORE_PATH in bullet and quoted_heading in bullet):
            defects.append(
                "(e) the Known-conflict bullet does not defer a short-lived conflict to "
                f"{ROUTE_CORE_PATH}, {quoted_heading}"
            )
        own_words = _words(bullet.replace(quoted_heading, ""))
        copied = _ngrams(own_words) & _ngrams(_words(rule))
        if rule and copied:
            sample = " ".join(sorted(copied)[0])
            defects.append(f"(e) the Known-conflict bullet restates the short-lived rule ('{sample}')")
    return defects


def _cores() -> tuple[str, str]:
    return USER_PM_CORE.read_text(encoding="utf-8"), ROUTE_CORE.read_text(encoding="utf-8")


def _without_line(text: str, start: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith(start))


def test_rubric_cites_the_route_compat_section_and_is_aligned_with_it() -> None:
    # Arrange
    pm_core, route_core = _cores()

    # Act
    defects = readiness_defects(pm_core, route_core)

    # Assert
    assert defects == [], "\n".join(defects)


def test_garbage_anchor_core_without_the_citation_fails() -> None:
    # Arrange: the plan's named anchor, the real user-pm core with the citation removed.
    pm_core, route_core = _cores()
    garbage = pm_core.replace(ROUTE_CORE_PATH, "the routing notes")

    # Act
    defects = readiness_defects(garbage, route_core)

    # Assert
    assert garbage != pm_core
    assert any(d.startswith("(a)") for d in defects), defects


def test_garbage_anchor_renamed_heading_in_the_route_core_fails() -> None:
    # Arrange
    pm_core, route_core = _cores()
    renamed = route_core.replace(f"## {HEADING}", "## Check the route is compatible")

    # Act
    defects = readiness_defects(pm_core, renamed)

    # Assert
    assert renamed != route_core
    assert any(d.startswith("(b)") for d in defects), defects


def test_garbage_anchor_each_missing_gap_fails() -> None:
    pm_core, route_core = _cores()
    for label in GAP_LABELS:
        # Arrange
        garbage = _without_line(pm_core, f"- {label}")

        # Act
        defects = readiness_defects(garbage, route_core)

        # Assert
        assert garbage != pm_core, label
        assert any(d.startswith("(c)") and label in d for d in defects), (label, defects)


def test_garbage_anchor_restated_route_table_fails() -> None:
    # Arrange: paste the producer's own route table into the rubric.
    pm_core, route_core = _cores()
    table = "\n".join(
        line for line in _section(route_core, f"## {ROUTE_TABLE_SECTION}").splitlines()
        if line.startswith("|")
    )
    garbage = pm_core.replace(RUBRIC_HEADING, f"{table}\n\n{RUBRIC_HEADING}", 1)

    # Act
    defects = readiness_defects(garbage, route_core)

    # Assert
    assert table and garbage != pm_core
    assert sum(d.startswith("(d)") for d in defects) >= 2, defects


def test_garbage_anchor_known_conflict_without_the_short_lived_deferral_fails() -> None:
    # Arrange: drop the deferral sentence from the Known-conflict bullet.
    pm_core, route_core = _cores()
    garbage = "\n".join(
        re.sub(r"\s*A short-lived conflict follows[^\n]*$", "", line)
        if line.startswith(KNOWN_CONFLICT) else line
        for line in pm_core.splitlines()
    )

    # Act
    defects = readiness_defects(garbage, route_core)

    # Assert
    assert garbage != pm_core
    assert any("does not defer" in d for d in defects), defects


def test_garbage_anchor_known_conflict_that_restates_the_rule_fails() -> None:
    # Arrange: append the producer's rule text to the bullet instead of citing it.
    pm_core, route_core = _cores()
    rule = _short_lived_rule(route_core)
    garbage = "\n".join(
        f"{line} {rule}" if line.startswith(KNOWN_CONFLICT) else line
        for line in pm_core.splitlines()
    )

    # Act
    defects = readiness_defects(garbage, route_core)

    # Assert
    assert rule and garbage != pm_core
    assert any("restates the short-lived rule" in d for d in defects), defects


def test_garbage_anchor_route_core_without_a_short_lived_rule_fails() -> None:
    # Arrange: the producer loses the rule user-pm defers to.
    pm_core, route_core = _cores()
    garbage = route_core.replace(f"is {SHORT_LIVED}:", "is temporary;")

    # Act
    defects = readiness_defects(pm_core, garbage)

    # Assert
    assert garbage != route_core
    assert any("no short-lived rule" in d for d in defects), defects
