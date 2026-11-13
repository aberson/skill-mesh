"""Every catalog skill is reachable from an operator vent, or deliberately is not.

`_shared/skill-pipeline.md` (the routing web) is the one owner of the rails. A skill is a
*rail entry* when the rail table names it as a backticked `/skill` invocation, and a
*not-vent target* when it has a row in the web's "Not vent targets" table. The
`/user-gateway` core's Step 3 gives one seed shape per rail.

This module checks the three guarantees the operator asked for (2026-11-13):

1. every skill in `config/skill-manifest.json` is a rail entry or a not-vent target,
   never both and never neither;
2. a name in either list that is not in the manifest fails (the web's declared host
   commands, `/goal` and `/deep-research`, are the only exception, and a declared host
   command that IS in the manifest also fails);
3. every rail in the table has a seed shape in the gateway's Step 3, and the decide
   rail's shape carries the `/user-dr` register line.

The parse is line-based but blind to fenced code blocks and HTML comments, so a row
parked inside either does not count as present. The garbage anchors at the bottom prove
each check can fail.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "config" / "skill-manifest.json"
PIPELINE = ROOT / "_shared" / "skill-pipeline.md"
GATEWAY = ROOT / "skills" / "user-gateway" / "core.md"

RAILS_HEADING = "## The rails"
NOT_VENT_HEADING = "## Not vent targets"
HOST_LINE_START = "**Host commands, not catalog skills:**"
SEED_HEADING_START = "### Step 3"

_SLASH_CODE_RE = re.compile(r"`/([a-z][a-z0-9-]*)")
_RAIL_CELL_RE = re.compile(r"^\*\*([a-z][a-z0-9-]*)\*\*$")
_NAME_CELL_RE = re.compile(r"^`([a-z][a-z0-9-]*)`$")
_SEED_BULLET_RE = re.compile(r"^- \*\*([a-z][a-z0-9-]*)\*\* →")
_SEPARATOR_RE = re.compile(r"^\|[-:| ]*-[-:| ]*\|?\s*$")


def _visible_lines(text: str) -> list[str]:
    """The document's lines with fenced code blocks and HTML comments removed."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    out, fence = [], None
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence is None and marker:
            fence = marker.group(1)[0] * 3
            continue
        if fence is not None:
            if line.lstrip().startswith(fence):
                fence = None
            continue
        out.append(line)
    return out


def _section(lines: list[str], heading_start: str) -> list[str]:
    """Lines under the first heading that starts with `heading_start`, up to the next
    heading of the same or higher level. Empty when the heading is absent."""
    level = len(heading_start) - len(heading_start.lstrip("#"))
    for i, line in enumerate(lines):
        if line.startswith(heading_start):
            body = []
            for nxt in lines[i + 1:]:
                m = re.match(r"^(#{1,6}) ", nxt)
                if m and len(m.group(1)) <= level:
                    break
                body.append(nxt)
            return body
    return []


def _table_rows(section: list[str]) -> list[list[str]]:
    """Data rows of every table in the section: a header row followed by a separator
    row, then contiguous pipe rows. Each row is its list of stripped cells."""
    rows, i = [], 0
    while i < len(section):
        if (section[i].startswith("|") and i + 1 < len(section)
                and _SEPARATOR_RE.match(section[i + 1])):
            i += 2
            while i < len(section) and section[i].startswith("|"):
                cells = section[i].strip().strip("|").split("|")
                rows.append([c.strip() for c in cells])
                i += 1
        else:
            i += 1
    return rows


def parse_rails(pipeline_text: str) -> dict[str, set[str]]:
    """Rail name -> the skills its row names as `/skill` invocations."""
    rails = {}
    for row in _table_rows(_section(_visible_lines(pipeline_text), RAILS_HEADING)):
        m = _RAIL_CELL_RE.match(row[0])
        if m:
            rails[m.group(1)] = set(_SLASH_CODE_RE.findall(" | ".join(row[1:])))
    return rails


def parse_not_vent(pipeline_text: str) -> tuple[list[str], set[str]]:
    """(not-vent skill names in table order, declared host commands)."""
    section = _section(_visible_lines(pipeline_text), NOT_VENT_HEADING)
    names = []
    for row in _table_rows(section):
        m = _NAME_CELL_RE.match(row[0])
        if m:
            names.append(m.group(1))
    host = set()
    for line in section:
        if line.startswith(HOST_LINE_START):
            host |= set(_SLASH_CODE_RE.findall(line))
    return names, host


def parse_seed_shapes(gateway_text: str) -> dict[str, str]:
    """Rail name -> the full text of its Step 3 seed-shape bullet."""
    shapes, current = {}, None
    for line in _section(_visible_lines(gateway_text), SEED_HEADING_START):
        m = _SEED_BULLET_RE.match(line)
        if m:
            current = m.group(1)
            shapes[current] = line
        elif current and line.startswith("  "):
            shapes[current] += "\n" + line
        else:
            current = None
    return shapes


def classify(manifest: set[str], rails: dict[str, set[str]], not_vent: list[str],
             host: set[str]) -> dict[str, list[str]]:
    """Every coverage defect, by kind. All lists empty means full coverage."""
    entries = set().union(*rails.values()) if rails else set()
    nv = set(not_vent)
    return {
        "neither": sorted(manifest - entries - nv),
        "both": sorted(entries & nv),
        "unknown_rail_entry": sorted(entries - manifest - host),
        "unknown_not_vent": sorted(nv - manifest),
        "duplicate_not_vent": sorted({n for n in not_vent if not_vent.count(n) > 1}),
        "host_in_manifest": sorted(host & manifest),
    }


def missing_seed_shapes(rails: dict[str, set[str]], shapes: dict[str, str]) -> list[str]:
    """Rails without a Step 3 seed shape, plus `decide` when its shape lacks /user-dr."""
    missing = sorted(set(rails) - set(shapes))
    if "decide" in rails and "decide" in shapes and "`/user-dr" not in shapes["decide"]:
        missing.append("decide (no /user-dr register line)")
    return missing


def _manifest_names() -> set[str]:
    return {s["name"] for s in json.loads(MANIFEST.read_text(encoding="utf-8"))["skills"]}


def _pipeline() -> str:
    return PIPELINE.read_text(encoding="utf-8")


def _gateway() -> str:
    return GATEWAY.read_text(encoding="utf-8")


def _no_defects(report: dict[str, list[str]]) -> bool:
    return not any(report.values())


# --------------------------------------------------------------------------- #
# The guarantees, on the committed documents.
# --------------------------------------------------------------------------- #

def test_parse_is_not_vacuous() -> None:
    rails = parse_rails(_pipeline())
    not_vent, host = parse_not_vent(_pipeline())
    assert {"bug", "plan", "decide", "verify"} <= set(rails), sorted(rails)
    assert all(rails.values()), f"a rail row names no /skill: {rails}"
    assert not_vent, "the Not vent targets table parsed empty"
    assert host == {"goal", "deep-research"}, host


def test_every_manifest_skill_is_a_rail_entry_or_not_a_vent_target() -> None:
    rails = parse_rails(_pipeline())
    not_vent, host = parse_not_vent(_pipeline())
    report = classify(_manifest_names(), rails, not_vent, host)
    assert _no_defects(report), report


def test_every_rail_has_a_gateway_seed_shape() -> None:
    rails = parse_rails(_pipeline())
    shapes = parse_seed_shapes(_gateway())
    assert not missing_seed_shapes(rails, shapes), missing_seed_shapes(rails, shapes)
    assert not set(shapes) - set(rails), \
        f"gateway seed shapes for rails the web does not own: {sorted(set(shapes) - set(rails))}"


# --------------------------------------------------------------------------- #
# Garbage anchors: each check must go red on a known defect.
# --------------------------------------------------------------------------- #

def test_anchor_extra_manifest_skill_is_reported() -> None:
    rails = parse_rails(_pipeline())
    not_vent, host = parse_not_vent(_pipeline())
    report = classify(_manifest_names() | {"fake-skill"}, rails, not_vent, host)
    assert report["neither"] == ["fake-skill"], report


def test_anchor_name_in_both_lists_is_reported() -> None:
    rails = parse_rails(_pipeline())
    not_vent, host = parse_not_vent(_pipeline())
    report = classify(_manifest_names(), rails, not_vent + ["user-debug"], host)
    assert report["both"] == ["user-debug"], report


def test_anchor_unknown_names_are_reported() -> None:
    rails = parse_rails(_pipeline())
    not_vent, host = parse_not_vent(_pipeline())
    rails = dict(rails, bug=rails["bug"] | {"user-dbug"})
    report = classify(_manifest_names(), rails, not_vent + ["ghost-skill"], host)
    assert report["unknown_rail_entry"] == ["user-dbug"], report
    assert report["unknown_not_vent"] == ["ghost-skill"], report


def test_anchor_host_command_that_is_a_catalog_skill_is_reported() -> None:
    rails = parse_rails(_pipeline())
    not_vent, host = parse_not_vent(_pipeline())
    report = classify(_manifest_names(), rails, not_vent, host | {"user-pm"})
    assert report["host_in_manifest"] == ["user-pm"], report


def test_anchor_row_hidden_in_a_fence_or_comment_does_not_count() -> None:
    text = _pipeline()
    row = "| `claude-oauth-auth` | reference doc |"
    assert text.count(row) == 1
    for hidden in ("<!--\n" + row + "\n-->", "```\n" + row + "\n```"):
        not_vent, host = parse_not_vent(text.replace(row, hidden))
        report = classify(_manifest_names(), parse_rails(text), not_vent, host)
        assert report["neither"] == ["claude-oauth-auth"], (hidden, report)


def test_anchor_missing_seed_shape_is_reported() -> None:
    gateway = _gateway()
    rails = parse_rails(_pipeline())
    learn = [line for line in gateway.splitlines() if line.startswith("- **learn** →")]
    assert len(learn) == 1
    shapes = parse_seed_shapes(gateway.replace(learn[0] + "\n", ""))
    assert missing_seed_shapes(rails, shapes) == ["learn"]
    shapes = parse_seed_shapes(gateway.replace("`/user-dr", "`/user-xx"))
    assert missing_seed_shapes(rails, shapes) == ["decide (no /user-dr register line)"]
