"""user-pm hands the user-fermize deep dive to a Codex window (v3 user-pm plan Step 5, #230).

user-fermize has no Claude adapter in this catalog yet, so the user-pm core labels its
paste line with the exact text "Run in: a Codex window". The plan's Step 18 drops the label
once a Claude adapter exists; until then this test keeps it from disappearing silently.
The garbage anchors prove the check can fail: a core without the label, or one where the
label no longer sits beside the user-fermize rule, must be rejected.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "skills" / "user-pm" / "core.md"
LABEL = "Run in: a Codex window"


def _labels_fermize_for_codex(text: str) -> bool:
    """True when one line both names user-fermize and carries the exact Codex-window label."""
    return any("user-fermize" in line and LABEL in line for line in text.splitlines())


def test_core_labels_the_user_fermize_line_for_a_codex_window() -> None:
    # Arrange
    core = CORE.read_text(encoding="utf-8")

    # Act
    labelled = _labels_fermize_for_codex(core)

    # Assert
    assert LABEL in core
    assert labelled, "the user-fermize rule must carry the exact label " + repr(LABEL)


def test_check_rejects_a_core_without_the_label() -> None:
    # Arrange: the real core with the label removed, and with it moved off the fermize line.
    core = CORE.read_text(encoding="utf-8")
    without_label = core.replace(LABEL, "Run in: any window")
    detached = "\n".join(
        line.replace(LABEL, "") for line in core.splitlines()
    ) + "\n" + LABEL + "\n"

    # Act / Assert
    assert not _labels_fermize_for_codex(without_label)
    assert not _labels_fermize_for_codex(detached)
