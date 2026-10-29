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
    assert "Run only after the exact Rail A delegation returned `Result: COMPLETE`." in section
    assert "skip reconciliation" in CORE.read_text(encoding="utf-8")
    assert "shipped default ref unverified" in section


def test_cleanup_requires_stale_clean_unlocked_redundant_build_tree():
    section = _cleanup_section()
    for required in (
        "starts `build-step-`",
        "starts `worktree_build-step-`",
        "not `locked` or `prunable`",
        "classifies it as stale rather",
        "status --porcelain --untracked-files=all",
        "stash list` is empty",
        "HEAD is an ancestor",
        "tree equals its merge-base tree",
        "every nonempty line",
    ):
        assert required in section


def test_cleanup_never_forces_prunes_deletes_branches_or_raw_directories():
    section = _cleanup_section()
    assert "WITHOUT\n`--force`" in section
    assert "never\nretry, prune, `rm`, `Remove-Item`, or delete a branch" in section
    assert "local and remote branches remain intact" in section
    assert "fresh `git worktree list --porcelain`" in section
    assert "directory is absent on disk" in section


def test_dry_run_proves_but_does_not_remove():
    section = _cleanup_section()
    assert "Under `--dry-run`" in section
    assert "remove nothing" in section
    assert "would remove" in section
