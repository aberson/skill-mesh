"""Behavioural tests for the session-active project pin script (`user-project.ps1`).

v3 catalog cleanup Step 15 (#271): the project-pin skill became a deterministic
PowerShell script in this folder. These tests run the REAL script (Windows PowerShell
5.1, as the callers do) against a scratch coding-root fixture and assert the outputs the
retired skill core documented for SET, SHOW and CLEAR, the three failure modes, and the
identity rule: nothing is written without the caller's own session id.

The identity checks are graded by one helper, `_identity_violations`, so the garbage
anchor at the bottom can prove that helper reds on a script that falls back to the
freshest session file when no id is given (the exact behaviour the contract forbids).
"""

import hashlib
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "user-project.ps1"
EM = "—"
IDENTITY_LINE = ("Active project not changed: required_tool_missing (session identity). "
                 "Honoring skills fall back to the plan/argument or cwd repo.")
SHOW_NO_ID = ("Active project: unknown (session identity unavailable); honoring skills "
              "fall back to the plan/argument or cwd repo.")

REGISTRY = (
    '[[project]]\nslug = "alpha"\npath = "alpha"\nowned = true\n'
    '  [project.launch.dev]\n  path = "nested-trap"\n\n'
    '[[project]]\nslug = "gamma"\nowned = true\n'
    '  [project.launch.dev]\n  path = "gamma-trap"\n\n'
    '[[project]]\nslug = "tin"\npath = "vendor/tin"\nowned = false\n'
)


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "coding-root"
    (root / ".claude" / "observatory").mkdir(parents=True)
    (root / ".claude" / "observatory" / "registry.toml").write_text(REGISTRY, encoding="utf-8")
    (root / "alpha" / "src").mkdir(parents=True)
    return root


def _run(script: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(script), *args],
        cwd=str(cwd), capture_output=True, check=False)
    proc.stdout = proc.stdout.decode("utf-8")
    proc.stderr = proc.stderr.decode("utf-8", errors="replace")
    return proc


def _state(root: Path) -> dict:
    """Every file under the task-state tree, by relative path, with its bytes' hash."""
    base = root / ".claude" / "task-state"
    if not base.exists():
        return {}
    return {str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(base.rglob("*")) if p.is_file()}


def _session(root: Path, sid: str) -> Path:
    return root / ".claude" / "task-state" / "sessions" / f"{sid}.md"


def _lines(proc: subprocess.CompletedProcess) -> list:
    return proc.stdout.splitlines()


# --------------------------------------------------------------------------- #
# SET
# --------------------------------------------------------------------------- #

def test_set_creates_the_minimal_session_file_with_the_pin(tmp_path):
    root = _root(tmp_path)
    proc = _run(SCRIPT, root / "alpha" / "src", "alpha", "-SessionId", "s1")
    abs_alpha = str(root / "alpha")
    assert proc.returncode == 0, proc.stderr
    assert _lines(proc) == [f"Pinned active project: alpha ({abs_alpha}). Pipeline skills "
                            "will target it via git -C regardless of cwd."]
    raw = _session(root, "s1").read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "the session file must be UTF-8 with no BOM"
    text = raw.decode("utf-8")
    lines = text.splitlines()
    assert lines[0].startswith(f"# Task State {EM} project pin ")
    assert f"**Active project:** alpha ({abs_alpha})" in lines
    assert lines.index(f"**Active project:** alpha ({abs_alpha})") == \
        next(i for i, l in enumerate(lines) if l.startswith("**Last written:**")) + 1
    assert "**Status:** IN_PROGRESS" in lines
    # The Next Action body is the placeholder, never a runnable command.
    assert lines[lines.index("## Next Action") + 2] == "(none recorded)"
    assert list(_state(root)) == [str(Path("sessions") / "s1.md")]


def test_set_merges_into_an_existing_file_and_preserves_every_other_line(tmp_path):
    root = _root(tmp_path)
    f = _session(root, "s2")
    f.parent.mkdir(parents=True)
    original = ("# Task State - real task\n\n**Task:** build the thing\n**Status:** IN_PROGRESS\n"
                "**Session SHA:** abc1234\n**Last written:** 2026-01-01T00:00:00Z\n"
                "**Custom:** keep me\n\n## Next Action\n\nrun the tests\n")
    f.write_bytes(original.encode("utf-8"))
    proc = _run(SCRIPT, root, "alpha", "-SessionId", "s2")
    assert proc.returncode == 0, proc.stderr
    after = f.read_text(encoding="utf-8").splitlines()
    pin = f"**Active project:** alpha ({root / 'alpha'})"
    assert after[after.index(pin) - 1].startswith("**Last written:**")
    assert after[after.index(pin) - 1] != "**Last written:** 2026-01-01T00:00:00Z", \
        "Last written must be refreshed"
    kept = [l for l in after if not l.startswith(("**Active project:**", "**Last written:**",
                                                  "**Session SHA:**"))]
    expected = [l for l in original.splitlines() if not l.startswith(("**Last written:**",
                                                                      "**Session SHA:**"))]
    assert kept == expected
    # Idempotent: a second SET rewrites the same single line.
    again = _run(SCRIPT, root, "alpha", "-SessionId", "s2")
    assert again.returncode == 0, again.stderr
    after2 = f.read_text(encoding="utf-8").splitlines()
    assert [l for l in after2 if l.startswith("**Active project:**")] == [pin]


def test_set_without_a_last_written_anchor_inserts_after_the_last_header(tmp_path):
    root = _root(tmp_path)
    f = _session(root, "s3")
    f.parent.mkdir(parents=True)
    f.write_text("# T\n**Task:** x\n**Status:** IN_PROGRESS\n\n## Next Action\n\n(none)\n",
                 encoding="utf-8")
    assert _run(SCRIPT, root, "alpha", "-SessionId", "s3").returncode == 0
    lines = f.read_text(encoding="utf-8").splitlines()
    assert lines[3] == f"**Active project:** alpha ({root / 'alpha'})"
    assert lines[2] == "**Status:** IN_PROGRESS" and lines[5] == "## Next Action"


def test_set_matches_path_or_slug_ignores_nested_path_keys_and_marks_third_party(tmp_path):
    root = _root(tmp_path)
    by_path = _run(SCRIPT, root, "vendor/tin", "-SessionId", "s4")
    assert by_path.returncode == 0, by_path.stderr
    assert _lines(by_path) == [f"Pinned active project: tin ({root / 'vendor' / 'tin'}). "
                               "Pipeline skills will target it via git -C regardless of cwd. "
                               "[third-party]"]
    # gamma has no own path key; its sub-table's `path` must not be read as its own.
    gamma = _run(SCRIPT, root, "gamma", "-SessionId", "s4")
    assert gamma.returncode == 0, gamma.stderr
    assert f"({root / 'gamma'})" in gamma.stdout
    assert _run(SCRIPT, root, "nested-trap", "-SessionId", "s4").returncode == 1


# --------------------------------------------------------------------------- #
# Failure modes
# --------------------------------------------------------------------------- #

def test_unknown_name_fails_loud_lists_known_slugs_and_writes_nothing(tmp_path):
    root = _root(tmp_path)
    before = _state(root)
    proc = _run(SCRIPT, root, "nope", "-SessionId", "s5")
    assert proc.returncode == 1
    assert proc.stderr.strip() == "user-project.ps1: unknown project 'nope'. Known slugs: alpha, gamma, tin"
    assert proc.stdout == ""
    assert _state(root) == before


def test_no_coding_root_fails_and_writes_nothing(tmp_path):
    lone = tmp_path / "nowhere"
    lone.mkdir()
    assert not any((d / ".claude" / "observatory" / "registry.toml").exists()
                   for d in [lone, *lone.parents]), "fixture precondition: no marker above tmp"
    proc = _run(SCRIPT, lone, "alpha", "-SessionId", "s6")
    assert proc.returncode == 1
    assert proc.stderr.strip().startswith(
        "user-project.ps1: could not locate coding-root (no .claude/observatory/registry.toml at or above ")
    assert not (lone / ".claude").exists()


def test_a_link_on_the_way_to_the_session_file_is_refused_and_nothing_is_written(tmp_path):
    root = _root(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (root / ".claude" / "task-state").mkdir()
    link = root / ".claude" / "task-state" / "sessions"
    made = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(elsewhere)],
                          capture_output=True, check=False)
    assert made.returncode == 0, made.stderr
    for args in (["alpha", "-SessionId", "s9"], ["clear", "-SessionId", "s9"]):
        proc = _run(SCRIPT, root, *args)
        assert proc.returncode == 1, (args, proc.stdout, proc.stderr)
        assert proc.stderr.strip().startswith(
            "user-project.ps1: refusing to write through a link under the coding root (")
    assert list(elsewhere.iterdir()) == [], "the write must not land through the junction"


def _identity_violations(script: Path, tmp_path: Path) -> list:
    """Every way `script` breaks the identity rule; [] means it holds.

    An OTHER window's session file is planted first and made the freshest, so a script
    that borrows the freshest file has something to borrow.
    """
    root = _root(tmp_path)
    other = _session(root, "other-window")
    other.parent.mkdir(parents=True)
    other.write_text("# Other\n**Last written:** 2026-01-01T00:00:00Z\n"
                     "**Active project:** gamma (x)\n\n## Next Action\n\nkeep\n", encoding="utf-8")
    bad = []
    for label, args, expected in (
            ("SET without an id", ["alpha"], [IDENTITY_LINE]),
            ("CLEAR without an id", ["clear"], [IDENTITY_LINE]),
            ("SET with a path-shaped id", ["alpha", "-SessionId", "..\\other-window"], [IDENTITY_LINE]),
            ("SET with a slash id", ["alpha", "-SessionId", "a/b"], [IDENTITY_LINE]),
            ("SET with a stream-colon id", ["alpha", "-SessionId", "other-window:x"], [IDENTITY_LINE]),
            ("SHOW without an id", [], [SHOW_NO_ID, "cwd repo: (not a git repository)"])):
        before = _state(root)
        proc = _run(script, root, *args)
        if proc.returncode != 0:
            bad.append(f"{label}: exit {proc.returncode} (an advisory result, never a halt)")
        if _lines(proc) != expected:
            bad.append(f"{label}: printed {_lines(proc)!r}")
        if _state(root) != before:
            bad.append(f"{label}: wrote to the task-state tree")
    return bad


def test_without_its_own_session_id_nothing_is_written(tmp_path):
    assert _identity_violations(SCRIPT, tmp_path) == []


# --------------------------------------------------------------------------- #
# SHOW and CLEAR
# --------------------------------------------------------------------------- #

def test_show_reports_unset_then_the_pin(tmp_path):
    root = _root(tmp_path)
    unset = _run(SCRIPT, root, "-SessionId", "s7")
    assert unset.returncode == 0, unset.stderr
    assert _lines(unset) == [f"Active project: unset {EM} deriving from cwd.",
                             "cwd repo: (not a git repository)"]
    assert _state(root) == {}, "SHOW is read-only"
    assert _run(SCRIPT, root, "alpha", "-SessionId", "s7").returncode == 0
    shown = _run(SCRIPT, root, "-SessionId", "s7")
    assert _lines(shown) == [f"Active project: alpha ({root / 'alpha'}) {EM} honored by "
                             "pipeline skills via git -C."]


def test_clear_removes_the_pin_then_reports_already_unset(tmp_path):
    root = _root(tmp_path)
    missing = _run(SCRIPT, root, "clear", "-SessionId", "s8")
    assert _lines(missing) == ["Active project already unset."]
    assert _state(root) == {}, "CLEAR with no file creates nothing"
    assert _run(SCRIPT, root, "alpha", "-SessionId", "s8").returncode == 0
    cleared = _run(SCRIPT, root, "clear", "-SessionId", "s8")
    assert cleared.returncode == 0, cleared.stderr
    assert _lines(cleared) == [f"Active project cleared {EM} reverting to cwd-derived repo."]
    text = _session(root, "s8").read_text(encoding="utf-8")
    assert "**Active project:**" not in text and "(none recorded)" in text
    before = _state(root)
    again = _run(SCRIPT, root, "clear", "-SessionId", "s8")
    assert _lines(again) == ["Active project already unset."]
    assert _state(root) == before


def test_script_is_ascii_with_no_bom():
    raw = SCRIPT.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert all(b < 128 for b in raw), "PowerShell 5.1 reads a no-BOM .ps1 as ANSI; keep it ASCII"


# --------------------------------------------------------------------------- #
# Garbage anchor: a script that skips the identity check must fail the helper
# --------------------------------------------------------------------------- #

def test_identity_helper_reds_on_a_script_that_borrows_the_freshest_session(tmp_path):
    source = SCRIPT.read_text(encoding="utf-8")
    seam = "$sid = $SessionId\n"
    assert source.count(seam) == 1, "the anchor's mutation seam moved; re-point it"
    garbage = source.replace(seam, seam + (
        "if (-not $sid) { $sid = (Get-ChildItem -LiteralPath (Join-Path $root "
        "'.claude\\task-state\\sessions') -Filter *.md | Sort-Object LastWriteTime | "
        "Select-Object -Last 1).BaseName }\n"))
    bad_script = tmp_path / "garbage" / "user-project.ps1"
    bad_script.parent.mkdir()
    bad_script.write_bytes(garbage.encode("ascii"))
    violations = _identity_violations(bad_script, tmp_path / "anchor")
    assert violations, "the identity helper passed a script that borrows another window's file"
    assert any("wrote to the task-state tree" in v for v in violations)
