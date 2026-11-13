"""user-pm's `--json` keys are a superset of the Step 1 baseline (v3 user-pm plan Step 10, #235).

`--json` is additive only: no existing key is renamed, removed or retyped, and every new
key is optional. The baseline below is the Step 1 wire audit's list, captured from
`origin/main` before the v3 rewrite began (the audit lives in the operator's planning
records, `<coding-root>/docs/skill-mesh-3-review/user-pm-revamp-wire-audit-2026-11-12.md`,
"Baseline key lists"). Its findings F1 (`notes` applies to both modes) and the "only the
top-level names and the `category` enum" scope are applied here.

The test reads the key table the core states in its "dev-observatory hook" section and
checks: every baseline key keeps its mode and presence; the `category` enum is unchanged;
the seven new keys are present and optional; `board[].route` uses the plan's four values
and maps the prose owner `you` to `human`; and the core says no production code parses
`--json` today.

Garbage anchors: the pre-revamp `--json` text (the baseline key list itself, verbatim),
a core missing each baseline key in turn, a baseline key made optional, a renamed
`category` value, a new key made mandatory, a route enum without `human`, and a core
that drops the no-production-caller statement must all fail.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "skills" / "user-pm" / "core.md"
HOOK_HEADING = "## dev-observatory hook"

# Step 1 baseline: (mode, key) -> presence, in the core's own presence words.
ALWAYS = "always"
PRINTED = "when the section is printed"
OMITTED = "omitted when empty"
BASELINE = {
    ("default", "project"): ALWAYS,
    ("default", "what_it_is"): ALWAYS,
    ("default", "history"): PRINTED,
    ("default", "outstanding"): PRINTED,
    ("default", "possible_next"): PRINTED,
    ("default", "cut_candidates"): PRINTED,
    ("default", "notes"): OMITTED,
    ("topic", "project"): ALWAYS,
    ("topic", "topic"): ALWAYS,
    ("topic", "context"): ALWAYS,
    ("topic", "unblocks"): ALWAYS,
    ("topic", "work"): ALWAYS,
    ("topic", "notes"): OMITTED,
}
CATEGORY_ENUM = {"test", "build", "decide", "overnight", "other"}

# Step 10's additive keys and the fields each must name.
NEW_KEYS = {
    "status": ("verified", "not_yet_verified", "manual_checks"),
    "board": ("item", "source", "route", "owner", "next_action", "evidence_age"),
    "decisions": ("open", "decided", "register"),
    "readiness": ("lanes", "blockers", "fallback_pool"),
    "lanes": ("lane", "host", "state", "item", "updated"),
    "lane_plan": ("mode", "lanes", "unplaced", "shared_resources"),
    "ideas": ("idea", "anchor", "judged"),
}
ROUTE_ENUM = ("core-pipeline", "bounded-goal", "direct-task", "human")
YOU_TO_HUMAN = "a row whose prose Route and Owner are `you` carries `human` in both"
NO_CALLER = "`--json` has no production caller today"
REQUIRED_VALUE_PHRASES = (
    "`judged` always `false`",
    "`mode` is `proposed` or `reviewed`",
    "`{lane, purpose, owns, items, host, handoffs}`",
)

# The pre-revamp `--json` text, verbatim from the Step 1 audit: the baseline key list
# itself, which must fail the superset check because it states no table and no new key.
BASELINE_SECTION = """## dev-observatory hook (additive; see `.claude/rules/descriptor-contract.md`)

**`--json` output mode (additive).** When invoked with `--json`, emit the snapshot as ONE structured JSON object instead of prose, so a tool (e.g. dev-observatory's on-demand goal-vs-reality review) can render it: each default section (`history`, `outstanding`, `possible_next`, `cut_candidates`) and any topic-mode payload becomes a top-level key; prose bullets become arrays of objects. The prose modes are unchanged when `--json` is absent.

Emit only the JSON object, with no fence or prose around it. A default-mode object also carries `project` and `what_it_is`, and each `possible_next` item carries its `category` (`test`, `build`, `decide`, `overnight`, or `other`). A topic-mode object carries `project`, `topic`, `context`, `unblocks`, and `work`. One-line notes go in a `notes` array of strings, omitted when empty. Selection, ordering, count, and omission rules are the same as in prose; an omitted section is an omitted key.
"""


def _hook(core: str) -> str:
    start = core.find(HOOK_HEADING)
    return core[start:] if start >= 0 else ""


def key_table(core: str) -> dict[str, dict[str, object]]:
    """The hook section's key table: key -> {modes, presence, shape}."""
    rows: dict[str, dict[str, object]] = {}
    for line in _hook(core).splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            continue
        key, modes, presence, shape = cells
        rows[key.strip("`")] = {
            "modes": {mode.strip() for mode in modes.split(",")},
            "presence": presence,
            "shape": shape,
        }
    return rows


def _value_bullet(core: str, key: str) -> str:
    prefix = f"- **`{key}`:**"
    return next((line for line in _hook(core).splitlines() if line.startswith(prefix)), "")


def json_contract_defects(core: str) -> list[str]:
    """Every way the core's key list fails to be an additive superset of the baseline."""
    defects: list[str] = []
    table = key_table(core)
    if not table:
        return ["no key table in the dev-observatory hook section"]

    for (mode, key), presence in BASELINE.items():
        row = table.get(key)
        if row is None:
            defects.append(f"baseline key `{key}` ({mode} mode) is missing")
            continue
        if mode not in row["modes"]:
            defects.append(f"baseline key `{key}` no longer appears in {mode} mode")
        if row["presence"] != presence:
            defects.append(f"baseline key `{key}` changed presence: {row['presence']!r} != {presence!r}")

    category = table.get("possible_next", {}).get("shape", "")
    stated = set(re.findall(r"`([a-z]+)`", str(category).split("category", 1)[-1]))
    if stated != CATEGORY_ENUM:
        defects.append(f"`possible_next[].category` enum changed: {sorted(stated)}")

    baseline_keys = {key for _, key in BASELINE}
    for key, row in table.items():
        if key not in baseline_keys and not str(row["presence"]).startswith("optional"):
            defects.append(f"new key `{key}` is not optional: {row['presence']!r}")
    for key, fields in NEW_KEYS.items():
        row = table.get(key)
        if row is None:
            defects.append(f"new key `{key}` is missing")
            continue
        described = str(row["shape"]) + " " + _value_bullet(core, key)
        for field in fields:
            if not re.search(rf"\b{re.escape(field)}\b", described):
                defects.append(f"new key `{key}` does not name its field `{field}`")

    board = _value_bullet(core, "board")
    route_clause = re.search(r"`route` is one of ([^,;]*(?:, [^,;]*)*?)(?:, and |;|\. )", board)
    route_values = set(re.findall(r"`([a-z-]+)`", route_clause.group(1))) if route_clause else set()
    for value in ROUTE_ENUM:
        if value not in route_values:
            defects.append(f"`board[].route` does not list `{value}`")
    if route_values - set(ROUTE_ENUM):
        defects.append(f"`board[].route` lists values outside the plan's enum: {sorted(route_values - set(ROUTE_ENUM))}")
    if YOU_TO_HUMAN not in board:
        defects.append("`board` does not map the prose owner `you` to `human`")
    hook = _hook(core)
    for phrase in REQUIRED_VALUE_PHRASES:
        if phrase not in hook:
            defects.append(f"value rule missing: {phrase}")
    if NO_CALLER not in hook:
        defects.append("the core does not say `--json` has no production caller today")
    return defects


def _core() -> str:
    return CORE.read_text(encoding="utf-8")


def _row_line(core: str, key: str) -> str:
    return next(line for line in core.splitlines() if line.startswith(f"| `{key}` |"))


def test_json_keys_are_an_additive_superset_of_the_baseline() -> None:
    # Act
    defects = json_contract_defects(_core())

    # Assert
    assert defects == [], "\n".join(defects)


def test_garbage_anchor_the_baseline_key_list_itself_fails() -> None:
    # Arrange: the real core with its hook section replaced by the pre-revamp text.
    core = _core()
    garbage = core[: core.find(HOOK_HEADING)] + BASELINE_SECTION

    # Act
    defects = json_contract_defects(garbage)

    # Assert
    assert garbage != core
    assert defects == ["no key table in the dev-observatory hook section"]


@pytest.mark.parametrize("key", sorted({key for _, key in BASELINE}))
def test_garbage_anchor_a_core_missing_a_baseline_key_fails(key: str) -> None:
    # Arrange
    core = _core()
    garbage = core.replace(_row_line(core, key) + "\n", "")

    # Act
    defects = json_contract_defects(garbage)

    # Assert
    assert garbage != core
    assert any(f"baseline key `{key}`" in d for d in defects), defects


def test_garbage_anchor_a_retyped_or_renamed_baseline_value_fails() -> None:
    # Arrange
    core = _core()
    optional_project = core.replace("| `project` | default, topic | always |",
                                    "| `project` | default, topic | optional, omitted when empty |")
    renamed_category = core.replace("`decide`, `overnight` or `other`", "`decide`, `night` or `other`")
    default_only_notes = core.replace("| `notes` | default, topic |", "| `notes` | default |")

    # Act / Assert
    for garbage, expected in ((optional_project, "changed presence"),
                              (renamed_category, "enum changed"),
                              (default_only_notes, "no longer appears in topic mode")):
        assert garbage != core, expected
        assert any(expected in d for d in json_contract_defects(garbage)), expected


def test_garbage_anchor_new_key_rules_fail_when_broken() -> None:
    # Arrange
    core = _core()
    board_row = _row_line(core, "board")
    mandatory_board = core.replace(board_row, board_row.replace("optional, omitted when empty", "always"))
    no_human = core.replace("`direct-task` or `human`", "`direct-task`")
    no_mapping = core.replace(YOU_TO_HUMAN, "a row owned by you keeps it")
    no_ideas = core.replace(_row_line(core, "ideas") + "\n", "")
    no_caller_note = core.replace(NO_CALLER, "`--json` is read by tools")

    # Act / Assert
    for garbage, expected in ((mandatory_board, "new key `board` is not optional"),
                              (no_human, "does not list `human`"),
                              (no_mapping, "does not map the prose owner"),
                              (no_ideas, "new key `ideas` is missing"),
                              (no_caller_note, "no production caller")):
        assert garbage != core, expected
        assert any(expected in d for d in json_contract_defects(garbage)), expected
