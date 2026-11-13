"""End-to-end gate for tools/release.ps1 (Step 38): real invocations against
REAL git repositories, staged into isolated tmp_path locations so this suite
never touches this repository's own working tree, its (gitignored)
release-stage/ output, or its actual git index/staging area.

Deliberately kept OUTSIDE tests/package-integrity/: release.ps1's own CHECK
phase runs `python -m pytest tests/package-integrity` against the tree it just
staged, and this file drives release.ps1 itself. If this file lived inside
tests/package-integrity/, a release.ps1 invocation's CHECK phase would pick it
up and recursively try to release the tree it is in the middle of staging.
Style matches tests/distributions/ (the sibling gate for
tools/build-distributions.ps1 + tools/install-skill-mesh.ps1): shell out to
powershell.exe via subprocess, use tmp_path, skip cleanly if powershell is
absent (it IS present here, so these RUN).

release.ps1 stages ONLY git-TRACKED files (a release must contain only
committed content -- see the module docstring in tools/release.ps1). This
session's own working tree has genuinely uncommitted new files (this test
file among them), so every test here builds its `-SourceRoot` from the
`source_repo` fixture below: an ISOLATED, throwaway git repository that
mirrors the current working tree and `git add -A`s everything into ITS OWN
index. This never touches this session's real git state -- it is exactly the
same "disposable git repo in tmp_path" pattern already used by
tests/package-integrity/test_release_gates.py's
test_no_tracked_dist_reds_on_planted_tracked_dist_file.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

PWSH = shutil.which("powershell")
GIT = shutil.which("git")
REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASE_SCRIPT = REPO_ROOT / "tools" / "release.ps1"

pytestmark = [
    pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH"),
    pytest.mark.skipif(GIT is None, reason="git is not available on PATH"),
]

# Mirrored into the throwaway source_repo, EXCLUDING VCS internals, generated/
# staging output, and caches -- this is test-fixture scaffolding only (NOT
# release.ps1's own staging logic, which now stages from `git ls-files`, no
# denylist at all).
_FIXTURE_IGNORE = shutil.ignore_patterns(
    ".git", "dist", "release-stage", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "node_modules", "tmp", ".build-step",
)


def _run(args, timeout=1800):
    return subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(RELEASE_SCRIPT), *args],
        capture_output=True, text=True, timeout=timeout,
    )


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _init_repo(root):
    root.mkdir(parents=True, exist_ok=True)
    _git(["init", "-q"], root)
    _git(["config", "user.email", "t@example.com"], root)
    _git(["config", "user.name", "test"], root)
    return root


def _parse_checksums_text(text):
    """{relpath: sha256hex} from the text of a release.ps1-produced CHECKSUMS.txt."""
    out = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        h, _, rel = line.partition("  ")
        out[rel] = h
    return out


def _parse_checksums(path):
    """{relpath: sha256hex} from a release.ps1-produced CHECKSUMS.txt."""
    return _parse_checksums_text(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def source_repo(tmp_path_factory):
    """A throwaway git repo mirroring the CURRENT working tree (including this
    session's not-yet-committed files), `git add -A`ed into ITS OWN index.
    Read-only for every test below except where explicitly noted; tests that
    need to mutate content copy this fixture first (`_clone_repo`)."""
    root = tmp_path_factory.mktemp("source-repo")
    shutil.copytree(REPO_ROOT, root, dirs_exist_ok=True, ignore=_FIXTURE_IGNORE)
    _init_repo(root)
    _git(["add", "-A"], root)
    return root


def _clone_repo(source_repo, dest):
    """A full standalone copy of source_repo (including its .git), safe to
    mutate without affecting the shared module-scoped fixture or any other
    test."""
    shutil.copytree(source_repo, dest)
    return dest


# --------------------------------------------------------------------------- #
# Tooling presence
# --------------------------------------------------------------------------- #

def test_release_script_exists():
    assert RELEASE_SCRIPT.is_file(), f"missing {RELEASE_SCRIPT}"


# --------------------------------------------------------------------------- #
# The shared release run (v3 guard Step 7)
#
# Five properties used to cost seven full release runs (each one stages, builds
# both profiles and runs tests/package-integrity inside the stage). They are all
# properties of an ordinary successful release, so one fixture makes two runs
# and the five tests below read its record:
#
#   run 1  into a fresh stage, from a clone of `source_repo` with an UNTRACKED
#          scratch file and an UNSTAGED README edit (a broken link) planted;
#   run 2  into the SAME stage, from the same planted clone.
#
# Run 1 grades the happy path, tracked-only staging and index-bytes staging.
# Run 2 grades reuse of the script's own prior stage, and comparing the two
# CHECKSUMS.txt grades reproducibility. Reproducibility across two DIFFERENT
# stage paths (a build that embeds its output path) is still graded by
# test_release_checksums_unchanged_across_source_line_ending_variants, which
# releases into two different stages and compares their checksum entries.
# --------------------------------------------------------------------------- #

_UNTRACKED_NAME = "UNTRACKED_SCRATCH.txt"
_UNSTAGED_README_TAIL = (
    b"\n[unstaged release leak](documentation/DOES_NOT_EXIST_UNSTAGED.md)\n"
)


def _stage_record(stage, result):
    """What a test needs from one run, captured before the next run clears it."""
    checksums = stage / "CHECKSUMS.txt"
    return {
        "result": result,
        "has_dist_claude": (stage / "dist" / "claude").is_dir(),
        "has_dist_gpt": (stage / "dist" / "gpt").is_dir(),
        "has_readme": (stage / "README.md").is_file(),
        "has_release_script": (stage / "tools" / "release.ps1").is_file(),
        "has_release_checks": (stage / "tools" / "release_checks.py").is_file(),
        "has_git": (stage / ".git").exists(),
        "has_pycache": any(stage.rglob("__pycache__")),
        "has_pytest_cache": any(stage.rglob(".pytest_cache")),
        "has_untracked": (stage / _UNTRACKED_NAME).exists(),
        "readme_bytes": (stage / "README.md").read_bytes()
        if (stage / "README.md").is_file() else None,
        "checksums_text": checksums.read_text(encoding="utf-8")
        if checksums.is_file() else None,
    }


@pytest.fixture(scope="module")
def shared_release(source_repo, tmp_path_factory):
    """Two release runs into one stage, from a planted clone of source_repo.

    Selecting any one of the five tests that read it (for example with -k) still pays
    for both runs: the fixture makes them together."""
    work = tmp_path_factory.mktemp("shared-release")
    planted = _clone_repo(source_repo, work / "planted")
    (planted / _UNTRACKED_NAME).write_text("do not ship me", encoding="utf-8")
    readme = planted / "README.md"
    readme.write_bytes(readme.read_bytes() + _UNSTAGED_README_TAIL)
    index_readme = subprocess.run(
        ["git", "show", ":README.md"], cwd=planted, capture_output=True, check=True
    ).stdout
    assert readme.read_bytes() != index_readme, "the README edit was not planted"

    stage = work / "stage"
    first = _stage_record(stage, _run(["-SourceRoot", str(planted), "-StageDir", str(stage)]))
    second = _stage_record(stage, _run(["-SourceRoot", str(planted), "-StageDir", str(stage)]))
    return {"first": first, "second": second, "index_readme": index_readme}


def _assert_ok(record, what):
    r = record["result"]
    assert r.returncode == 0, f"{what} failed:\n{r.stdout}\n{r.stderr}"


# --------------------------------------------------------------------------- #
# Happy path: stage (tracked-only) + build + check + checksum
# --------------------------------------------------------------------------- #

def test_release_builds_stages_and_checksums(shared_release):
    first = shared_release["first"]
    _assert_ok(first, "release")

    assert first["has_dist_claude"]
    assert first["has_dist_gpt"]
    assert first["has_readme"]
    assert first["has_release_script"]
    assert first["has_release_checks"]

    assert first["checksums_text"] is not None, "CHECKSUMS.txt was not written"
    entries = _parse_checksums_text(first["checksums_text"])
    assert len(entries) > 100, "implausibly few files in the release checksum manifest"
    # CHECKSUMS.txt covers ONLY dist/ -- the deterministically-generated
    # artifact -- never the raw (line-ending-sensitive) source tree.
    assert all(rel.startswith("dist/") for rel in entries), \
        "CHECKSUMS.txt must cover only dist/, not the staged source tree"
    for h in list(entries.values())[:5]:
        assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)


def test_release_stage_excludes_vcs_and_untracked_content(shared_release):
    """The stage contains git-tracked content only: no .git, no cache dirs, and
    -- unlike a whole-working-dir mirror -- no file the fixture deliberately
    left untracked (proving staging is git-ls-files-driven, not a denylist)."""
    for key in ("first", "second"):
        run = shared_release[key]
        _assert_ok(run, f"release ({key} run)")
        assert not run["has_git"]
        assert not run["has_pycache"]
        assert not run["has_pytest_cache"]
        assert not run["has_untracked"], \
            f"an untracked working-tree file leaked into the release stage ({key} run)"


def test_release_stages_index_bytes_not_unstaged_worktree_bytes(shared_release):
    """A tracked, unstaged README defect must neither leak into stage nor fail it."""
    expected = shared_release["index_readme"]
    for key in ("first", "second"):
        run = shared_release[key]
        r = run["result"]
        assert r.returncode == 0, (
            f"unstaged worktree bytes leaked into release ({key} run):\n{r.stdout}\n{r.stderr}")
        assert run["readme_bytes"] == expected


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #

def test_release_is_reproducible_across_two_runs(shared_release):
    first, second = shared_release["first"], shared_release["second"]
    _assert_ok(first, "release (first run)")
    _assert_ok(second, "release (second run)")
    assert first["checksums_text"] is not None and second["checksums_text"] is not None
    assert first["checksums_text"] == second["checksums_text"], \
        "CHECKSUMS.txt differs across two runs over an unchanged tree"


def test_release_checksums_unchanged_across_source_line_ending_variants(source_repo, tmp_path):
    """BLOCK 3 regression: CHECKSUMS.txt covers only the GENERATED dist/
    artifacts, which build-distributions.ps1 normalizes (CRLF -> LF, no BOM)
    when reading source content -- so a source checkout's incidental line
    ending (this machine's autocrlf history, a fresh clone, a different OS)
    must never change the generated bytes or their checksums. Forces BOTH an
    LF and a CRLF variant explicitly (never assumes which one this machine's
    own git checkout happens to be -- core.autocrlf can make that either way,
    which is exactly the non-reproducibility this test guards against)."""
    target_rel = Path("skills") / "build-phase" / "providers" / "claude.md"

    lf_variant = _clone_repo(source_repo, tmp_path / "lf-variant")
    crlf_variant = _clone_repo(source_repo, tmp_path / "crlf-variant")
    normalized = (lf_variant / target_rel).read_bytes().replace(b"\r\n", b"\n")
    (lf_variant / target_rel).write_bytes(normalized)
    (crlf_variant / target_rel).write_bytes(normalized.replace(b"\n", b"\r\n"))
    assert (lf_variant / target_rel).read_bytes() != (crlf_variant / target_rel).read_bytes()

    stage_lf = tmp_path / "stage-lf"
    stage_crlf = tmp_path / "stage-crlf"
    r_lf = _run(["-SourceRoot", str(lf_variant), "-StageDir", str(stage_lf)])
    assert r_lf.returncode == 0, r_lf.stderr
    r_crlf = _run(["-SourceRoot", str(crlf_variant), "-StageDir", str(stage_crlf)])
    assert r_crlf.returncode == 0, r_crlf.stderr

    entries_lf = _parse_checksums(stage_lf / "CHECKSUMS.txt")
    entries_crlf = _parse_checksums(stage_crlf / "CHECKSUMS.txt")
    assert entries_lf == entries_crlf, (
        "dist/ checksums differ between an LF and a CRLF source checkout of the "
        "same content -- the generated artifact is not properly normalized"
    )


# --------------------------------------------------------------------------- #
# BLOCK 1: staging is git-ls-files-driven, so the no-tracked-dist gate is
# enforceable against the SOURCE repo's own index -- not a self-skip against
# the (deliberately git-less) stage.
# --------------------------------------------------------------------------- #

def test_release_check_catches_a_tracked_dist_file(source_repo, tmp_path):
    mutated = _clone_repo(source_repo, tmp_path / "mutated")
    leaked_dir = mutated / "dist" / "claude"
    leaked_dir.mkdir(parents=True)
    (leaked_dir / "leaked.md").write_text("should never ship", encoding="utf-8")
    _git(["add", "-f", "dist/claude/leaked.md"], mutated)

    stage = tmp_path / "stage"
    r = _run(["-SourceRoot", str(mutated), "-StageDir", str(stage)])
    assert r.returncode != 0, "release.ps1 did not fail on a git-add -f'd dist/ file"
    combined = (r.stdout + r.stderr).lower()
    # The release must fail BECAUSE the nested no-tracked-dist check ran against the
    # SOURCE repo's index and found the file -- not for some other staged-tree defect.
    # A looser "tracked or package-integrity" substring passed even when the check was
    # pointed at the git-less stage and skipped (v3 guard review, should-fix 1).
    assert "test_no_tracked_dist_on_real_repo" in combined, combined[-4000:]
    assert not (stage / "CHECKSUMS.txt").exists(), \
        "checksums were written despite a tracked generated-distribution path"


# --------------------------------------------------------------------------- #
# The gate actually gates: a planted README defect aborts the release, no
# checksums written.
# --------------------------------------------------------------------------- #

def test_release_aborts_and_writes_no_checksums_on_a_broken_link(source_repo, tmp_path):
    mutated = _clone_repo(source_repo, tmp_path / "mutated")
    readme = mutated / "README.md"
    text = readme.read_text(encoding="utf-8")
    text += "\n\nSee the [planted broken link](documentation/DOES_NOT_EXIST_PLANTED.md).\n"
    readme.write_text(text, encoding="utf-8")
    _git(["add", "README.md"], mutated)

    stage = tmp_path / "stage"
    r = _run(["-SourceRoot", str(mutated), "-StageDir", str(stage)])
    assert r.returncode != 0, "release.ps1 did not fail on a planted broken README link"
    combined = r.stdout + r.stderr
    assert "FAILED" in combined or "package-integrity" in combined.lower()
    assert not (stage / "CHECKSUMS.txt").exists(), \
        "checksums were written despite a failing package-integrity gate"


# --------------------------------------------------------------------------- #
# BLOCK 2: destructive-delete safety (no data loss).
# --------------------------------------------------------------------------- #

def test_release_refuses_stage_dir_equal_to_source_root(tmp_path):
    src = _init_repo(tmp_path / "src")
    (src / "f.txt").write_text("x", encoding="utf-8")
    _git(["add", "-A"], src)
    r = _run(["-SourceRoot", str(src), "-StageDir", str(src)])
    assert r.returncode != 0
    assert "same as the source root" in (r.stdout + r.stderr)


def test_release_refuses_trailing_separator_variant_of_source_root(tmp_path):
    """Regression: [IO.Path]::GetFullPath('<repo>') != GetFullPath('<repo>\\')
    (a bare string compare misses this); canonicalization must catch it so
    -StageDir '<source>\\' cannot bypass the equality guard and delete the
    source checkout."""
    src = _init_repo(tmp_path / "src")
    (src / "f.txt").write_text("x", encoding="utf-8")
    _git(["add", "-A"], src)
    r = _run(["-SourceRoot", str(src), "-StageDir", str(src) + "\\"])
    assert r.returncode != 0, "trailing-separator StageDir variant was not refused"
    assert "same as the source root" in (r.stdout + r.stderr)
    assert (src / "f.txt").is_file(), "source file survived only by accident"
    assert (src / ".git").exists(), "source .git survived only by accident"


def test_release_refuses_stage_dir_that_is_an_ancestor_of_source_root(tmp_path):
    """A -StageDir that CONTAINS the source root must be refused -- clearing it
    would delete the source itself."""
    outer = tmp_path / "outer"
    src = _init_repo(outer / "nested" / "src")
    (src / "f.txt").write_text("x", encoding="utf-8")
    _git(["add", "-A"], src)

    r = _run(["-SourceRoot", str(src), "-StageDir", str(outer)])
    assert r.returncode != 0, "release.ps1 did not refuse a StageDir that is an ancestor of the source root"
    assert "ancestor" in (r.stdout + r.stderr).lower()
    assert (src / "f.txt").is_file(), "source file was deleted"
    assert (src / ".git").exists(), "source .git was deleted"


def test_release_refuses_nonempty_foreign_stage_dir_without_marker(tmp_path):
    """A pre-existing, non-empty -StageDir that this script never created
    (no marker file) must be refused, never silently wiped."""
    src = _init_repo(tmp_path / "src")
    (src / "f.txt").write_text("x", encoding="utf-8")
    _git(["add", "-A"], src)

    foreign_stage = tmp_path / "foreign"
    foreign_stage.mkdir()
    (foreign_stage / "operator-content.txt").write_text("precious", encoding="utf-8")

    r = _run(["-SourceRoot", str(src), "-StageDir", str(foreign_stage)])
    assert r.returncode != 0, "release.ps1 wiped a foreign non-empty StageDir without a marker"
    assert (foreign_stage / "operator-content.txt").is_file(), \
        "foreign StageDir content was deleted"
    assert (foreign_stage / "operator-content.txt").read_text(encoding="utf-8") == "precious"


def test_release_reuses_its_own_prior_stage_dir_without_refusing(shared_release):
    """A StageDir this script created on a PRIOR run (marker present) may be
    reused (cleared + re-staged) without -Force or any special flag -- the
    marker is proof of ownership, not a one-shot lock. The shared fixture's
    second run goes into the first run's stage."""
    _assert_ok(shared_release["first"], "release (first run)")
    second = shared_release["second"]
    r2 = second["result"]
    assert r2.returncode == 0, f"re-run over its own prior stage was refused:\n{r2.stdout}\n{r2.stderr}"
    assert second["checksums_text"] is not None, "the reused stage has no CHECKSUMS.txt"


def _all_tests():
    return [v for k, v in sorted(globals().items())
            if k.startswith("test_") and callable(v)]


if __name__ == "__main__":
    passed = skipped = 0
    for fn in _all_tests():
        try:
            fn()
            passed += 1
            print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            if e.__class__.__name__ == "Skipped":
                skipped += 1
                print(f"SKIP {fn.__name__}: {e}")
            else:
                raise
    print(f"\n{passed} checks passed, {skipped} skipped")
