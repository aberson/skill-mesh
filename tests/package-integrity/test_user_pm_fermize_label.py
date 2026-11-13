"""user-pm hands the user-fermize deep dive to a Codex window (v3 user-pm plan Step 5, #230).

user-fermize has no Claude adapter in this catalog yet, so the user-pm core labels its
paste line with the exact text "Run in: a Codex window". The plan's Step 18 drops the label
once a Claude adapter exists; until then this test keeps it from disappearing silently.
Every line that defines the deep dive (the output template's bullet and the rule) must name
user-fermize and carry the label. The garbage anchors prove the check can fail: a core
without the label, one where the label is removed from only one of those lines, or one
where the label no longer sits beside user-fermize must be rejected.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "skills" / "user-pm" / "core.md"
LABEL = "Run in: a Codex window"
DEEP_DIVE_LINE_STARTS = ("- **Deep dive:**", "**Deep dive on one decision.**")


def _deep_dive_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith(DEEP_DIVE_LINE_STARTS)]


def _labels_fermize_for_codex(text: str) -> bool:
    """True when both deep-dive definitions exist and each names user-fermize with the label."""
    lines = _deep_dive_lines(text)
    found = {start for start in DEEP_DIVE_LINE_STARTS for line in lines if line.startswith(start)}
    return found == set(DEEP_DIVE_LINE_STARTS) and all(
        "user-fermize" in line and LABEL in line for line in lines
    )


def test_core_labels_the_user_fermize_line_for_a_codex_window() -> None:
    # Arrange
    core = CORE.read_text(encoding="utf-8")

    # Act
    labelled = _labels_fermize_for_codex(core)

    # Assert
    assert LABEL in core
    assert labelled, "every user-fermize deep-dive line must carry the exact label " + repr(LABEL)


def test_check_rejects_a_core_without_the_label() -> None:
    # Arrange: the real core with the label removed everywhere, from one line only,
    # and moved off the deep-dive lines.
    core = CORE.read_text(encoding="utf-8")
    without_label = core.replace(LABEL, "Run in: any window")
    one_line_unlabelled = [
        "\n".join(
            line.replace(LABEL, "Run in: any window") if line.startswith(start) else line
            for line in core.splitlines()
        )
        for start in DEEP_DIVE_LINE_STARTS
    ]
    detached = "\n".join(
        line.replace(LABEL, "") for line in core.splitlines()
    ) + "\n" + LABEL + "\n"

    # Act / Assert
    assert not _labels_fermize_for_codex(without_label)
    for mutated in one_line_unlabelled:
        assert mutated != core
        assert not _labels_fermize_for_codex(mutated)
    assert not _labels_fermize_for_codex(detached)
