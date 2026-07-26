"""
Path-canonicalization rejection tests for runtime/path-guard.ps1.

The guard (used by runtime/skill-router.ps1 and the telemetry scripts) must reject
any path that canonicalizes OUTSIDE its allowed roots -- whether the escape is via
a lexical '..', a Windows directory junction, or a symbolic link. Each case below
plants the escape inside an allowed root and confirms the production CLI rejects it
(exit 3), while a legitimate in-root path is accepted (exit 0).

Symlink creation needs privilege (Developer Mode / admin); that case skips cleanly
where unavailable. Junctions and '..' need no privilege and always run.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD_PATH = REPO_ROOT / "runtime" / "path-guard.ps1"

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")


def _guard(path, root):
    return subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(GUARD_PATH),
         "-Path", str(path), "-AllowedRoot", str(root)],
        capture_output=True,
        text=True,
    )


def test_guard_exists():
    assert GUARD_PATH.is_file(), f"missing path-guard: {GUARD_PATH}"


def test_guard_accepts_path_inside_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    target = root / "ok.txt"
    target.write_text("x", encoding="utf-8")
    result = _guard(target, root)
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("OK ")


def test_guard_rejects_dotdot_traversal(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("s", encoding="utf-8")

    candidate = root / ".." / "outside" / "secret.txt"
    result = _guard(candidate, root)
    assert result.returncode == 3, (result.stdout, result.stderr)
    assert "SECURITY" in result.stderr


def test_guard_rejects_junction_escaping_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("s", encoding="utf-8")

    jlink = root / "jlink"
    mk = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(jlink), str(outside)],
        capture_output=True,
        text=True,
    )
    assert mk.returncode == 0, (mk.stdout, mk.stderr)

    candidate = jlink / "secret.txt"
    result = _guard(candidate, root)
    assert result.returncode == 3, (result.stdout, result.stderr)
    assert "SECURITY" in result.stderr


def test_guard_rejects_symlink_escaping_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("s", encoding="utf-8")

    slink = root / "slink"
    mk = subprocess.run(
        [PWSH, "-NonInteractive", "-Command",
         f"New-Item -ItemType SymbolicLink -Path '{slink}' -Target '{outside}' -ErrorAction Stop"],
        capture_output=True,
        text=True,
    )
    if mk.returncode != 0:
        pytest.skip("symbolic-link creation requires privilege (Developer Mode/admin) on this host")

    candidate = slink / "secret.txt"
    result = _guard(candidate, root)
    assert result.returncode == 3, (result.stdout, result.stderr)
    assert "SECURITY" in result.stderr
