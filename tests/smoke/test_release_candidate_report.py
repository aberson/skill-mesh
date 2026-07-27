"""
Step 40 Done-when: documentation/release-candidate-report.md must be
generatable/refreshable from a real smoke run, not hand-typed.

This suite regenerates the report in-memory via
tests/smoke/gen_release_candidate_report.py (which runs the SAME hermetic
scenario functions tests/smoke/test_cross_provider_smoke.py exercises) and
diffs it against the committed file -- any drift (a skill renamed, a core.md
edited, router behavior changed) fails loudly instead of letting the committed
report silently go stale. It also checks the report's shape and confirms it
carries no private/operator-local path.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _scenarios as sc  # noqa: E402
import gen_release_candidate_report as gen  # noqa: E402

pytestmark = pytest.mark.skipif(sc.PWSH is None, reason="powershell is not available on PATH")

REPORT_PATH = gen.REPORT_PATH


def test_report_exists_with_generated_marker():
    assert REPORT_PATH.is_file(), (
        f"missing {REPORT_PATH}; run `python tests/smoke/gen_release_candidate_report.py`"
    )
    text = REPORT_PATH.read_text(encoding="utf-8")
    assert "GENERATED FILE - DO NOT EDIT" in text
    assert "gen_release_candidate_report.py" in text


def test_report_is_not_stale_relative_to_a_real_smoke_run():
    fresh = gen.generate()
    committed = REPORT_PATH.read_text(encoding="utf-8")
    assert fresh == committed, (
        "documentation/release-candidate-report.md is stale relative to a real "
        "router smoke run -- regenerate via "
        "`python tests/smoke/gen_release_candidate_report.py` and commit the result."
    )


def test_report_has_required_columns():
    text = REPORT_PATH.read_text(encoding="utf-8")
    for col in gen.COLUMNS:
        assert col in text, f"missing column '{col}' in release-candidate report"


def test_report_has_exactly_n_scenario_rows_per_representative_skill():
    # gen.SCENARIOS_PER_SKILL is the single source of truth (the literal list
    # of scenario functions the generator runs) -- an exact match here means
    # this gate can never silently drift from what collect_rows() actually
    # emits, and a missing/duplicated row for any skill is caught precisely.
    text = REPORT_PATH.read_text(encoding="utf-8")
    families = sc.load_representative_skills()
    table_rows = [line for line in text.splitlines() if line.startswith("| ")]
    for skill in sorted(set(families.values())):
        needle = f"| {skill} |"
        count = sum(1 for line in table_rows if needle in line)
        assert count == gen.SCENARIOS_PER_SKILL, (
            f"expected exactly {gen.SCENARIOS_PER_SKILL} scenario rows for '{skill}', found {count}"
        )


def test_report_has_no_private_or_operator_local_paths():
    text = REPORT_PATH.read_text(encoding="utf-8")
    for forbidden in (".claude", "coding-root", "C:\\Users", "C:/Users", "/Users/", "\\Users\\"):
        assert forbidden not in text, f"report leaks a private/operator-local path token: {forbidden!r}"
