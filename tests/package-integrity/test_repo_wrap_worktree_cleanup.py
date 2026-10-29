"""Contract checks for repo-wrap's conservative build-worktree reconciliation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "skills" / "repo-wrap" / "core.md"


def _cleanup_section() -> str:
    text = CORE.read_text(encoding="utf-8")
    start = text.index("### Post-closeout build-worktree reconciliation")
    end = text.index("\n## Rail B", start)
    return text[start:end]


def test_cleanup_runs_only_after_complete_owned_project_closeout():
    section = _cleanup_section()
    assert "Run only after Rail A returns `Result: COMPLETE`" in section
    assert "skip reconciliation" in CORE.read_text(encoding="utf-8")
    assert "pushed\n`origin/<default>` ref is verified" in section


def test_cleanup_is_conservative_and_never_forces_removal():
    section = _cleanup_section()
    for required in (
        "branch leaf `build-step-*`",
        "path leaf `worktree_build-step-*`",
        "classifies as stale",
        "unlocked",
        "status --porcelain --untracked-files=all",
        "contains no `+` line",
        "never `--force`",
        "keep its branch",
        "never prune, raw-delete, or delete its branch",
        "would be removed without mutating",
    ):
        assert required in section
