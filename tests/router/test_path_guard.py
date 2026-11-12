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


# --------------------------------------------------------------------------- #
# The canonicalization fast path (installer slow-path fix) changes no verdict
# --------------------------------------------------------------------------- #

# The walk as it stood before the fast path, kept verbatim (renamed) as the oracle:
# the fast path is only correct if it returns byte-identical results.
_REFERENCE_WALK = r"""
function Get-CanonicalRealPathReference {
    param(
        [Parameter(Mandatory = $true)][string]$InputPath,
        [int]$Depth = 0
    )
    if ([string]::IsNullOrWhiteSpace($InputPath)) { throw "path-guard: empty path" }
    if ($Depth -gt 40) { throw "path-guard: reparse-point resolution exceeded max depth (possible link cycle) for '$InputPath'" }
    $full = [System.IO.Path]::GetFullPath($InputPath)
    $root = [System.IO.Path]::GetPathRoot($full)
    if ([string]::IsNullOrEmpty($root)) { return $full }
    $rest = $full.Substring($root.Length)
    $segments = $rest.Split([char[]]@('\', '/'), [System.StringSplitOptions]::RemoveEmptyEntries)
    $current = $root
    if (-not ($current.EndsWith('\') -or $current.EndsWith('/'))) {
        $current = $current + [System.IO.Path]::DirectorySeparatorChar
    }
    foreach ($seg in $segments) {
        $current = [System.IO.Path]::Combine($current, $seg)
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            $linkTarget = $null
            $targetMember = $item | Get-Member -Name Target -ErrorAction SilentlyContinue
            if ($targetMember) {
                $t = $item.Target
                if ($t) { $linkTarget = @($t)[0] }
            }
            if ($linkTarget) {
                if (-not [System.IO.Path]::IsPathRooted($linkTarget)) {
                    $linkParent = [System.IO.Path]::GetDirectoryName($current)
                    $linkTarget = [System.IO.Path]::Combine($linkParent, $linkTarget)
                }
                $current = Get-CanonicalRealPathReference -InputPath $linkTarget -Depth ($Depth + 1)
            } else {
                $current = $item.FullName
            }
        }
    }
    return [System.IO.Path]::GetFullPath($current)
}
"""

# param() must be the script's first statement, so the oracle goes after it.
_DIFF_DRIVER_PARAM = r"""
param([string]$Guard, [string]$PathList)
"""

_DIFF_DRIVER = r"""
$ErrorActionPreference = 'Stop'
. $Guard
foreach ($p in [System.IO.File]::ReadAllLines($PathList)) {
    if ($p -eq '') { continue }
    $ref = try { Get-CanonicalRealPathReference -InputPath $p } catch { 'THROW ' + $_.Exception.Message }
    $new = try { Get-CanonicalRealPath -InputPath $p } catch { 'THROW ' + $_.Exception.Message }
    if ($ref -ceq $new) { [Console]::Out.WriteLine("SAME`t$p`t$new") }
    else { [Console]::Out.WriteLine("DIFF`t$p`t$ref`t$new") }
}
"""


def _mklink(*args):
    return subprocess.run(["cmd", "/c", "mklink", *args], capture_output=True, text=True)


def _junction(link, target):
    mk = _mklink("/J", str(link), str(target))
    assert mk.returncode == 0, (mk.stdout, mk.stderr)


def test_fast_path_matches_the_reference_walk_byte_for_byte(tmp_path):
    """Differential check over junctions, a junction chain, a dangling junction, a
    hard link, a file mid-path, missing tails, '..', mixed separators, names with a
    space, brackets, '$' and a non-ASCII letter, and a lower-case drive letter (the
    probe re-spells it, so the fast path must not skip the first existing segment)."""
    root = tmp_path / "root"
    deep = root / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (deep / "file.txt").write_text("x", encoding="utf-8")
    outside = tmp_path / "outside"
    (outside / "x" / "y" / "deep").mkdir(parents=True)
    (outside / "x" / "y" / "deep" / "secret.txt").write_text("s", encoding="utf-8")
    (outside / "hl.txt").write_text("h", encoding="utf-8")
    (outside / "gone").mkdir()
    odd = root / "sp ace" / "[br]$x" / "caf\u00e9" / ".hid"
    odd.mkdir(parents=True)
    (odd / "f.md").write_text("o", encoding="utf-8")

    a = root / "a"
    _junction(a / "jout", outside / "x" / "y")
    _junction(a / "jin", a / "b")
    _junction(a / "jchain", a / "jout")
    _junction(a / "dangle", outside / "gone")
    (outside / "gone").rmdir()
    hard = _mklink("/H", str(a / "hard.txt"), str(outside / "hl.txt"))

    s = str(tmp_path)
    lower_drive = s[0].lower() + s[1:] if s[1:2] == ":" else s
    paths = [
        deep / "file.txt",
        deep / "new" / "sub" / "file.md",
        deep / "file.txt" / "extra",
        a / "jout" / "deep" / "secret.txt",
        a / "jout" / "deep" / "new.md",
        a / "jin" / "c" / "file.txt",
        a / "jchain" / "deep",
        a / "dangle" / "child",
        root / "a" / "b" / ".." / "jout" / "deep",
        str(deep).replace("\\", "/") + "/file.txt",
        lower_drive + "\\root\\a\\b\\c\\file.txt",
        lower_drive + "\\root\\a\\jout\\deep\\secret.txt",
        lower_drive + "\\root\\missing\\x",
        tmp_path,
        odd / "f.md",
        odd / "new" / "x.md",
    ]
    if hard.returncode == 0:
        paths.append(a / "hard.txt")

    driver = tmp_path / "diff_driver.ps1"
    driver.write_text(_DIFF_DRIVER_PARAM + _REFERENCE_WALK + _DIFF_DRIVER, encoding="ascii")
    plist = tmp_path / "paths.txt"
    plist.write_text("\n".join(str(p) for p in paths) + "\n", encoding="utf-8")
    r = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(driver),
                        "-Guard", str(GUARD_PATH), "-PathList", str(plist)],
                       capture_output=True, text=True, errors="replace")
    assert r.returncode == 0, r.stderr
    rows = [line.split("\t") for line in r.stdout.splitlines() if line]
    assert [row for row in rows if row[0] != "SAME"] == [], r.stdout
    assert len(rows) == len(paths), r.stdout
    # Non-vacuity: the corpus really crosses a junction to the outside, and really
    # exercises the drive re-spelling the fast path has to respect.
    by_input = {row[1]: row[2] for row in rows}
    assert by_input[str(a / "jout" / "deep" / "secret.txt")].startswith(str(outside)), r.stdout
    if lower_drive != s:
        assert by_input[lower_drive + "\\root\\a\\b\\c\\file.txt"][0].isupper(), r.stdout


_SAME_PROCESS_DRIVER = r"""
param([string]$Guard, [string]$Root, [string]$Candidate, [string]$Outside)
$ErrorActionPreference = 'Stop'
. $Guard
$first = Resolve-SafePath -Path $Candidate -AllowedRoots @($Root)
[Console]::Out.WriteLine("FIRST $first")
$parent = Split-Path -Parent $Candidate
Remove-Item -LiteralPath $parent -Recurse -Force
cmd /c mklink /J "$parent" "$Outside" | Out-Null
try {
    $second = Resolve-SafePath -Path $Candidate -AllowedRoots @($Root)
    [Console]::Out.WriteLine("SECOND-ACCEPTED $second")
    exit 1
} catch {
    [Console]::Out.WriteLine("SECOND-REJECTED " + $_.Exception.Message)
    exit 0
}
"""


def test_junction_planted_between_calls_in_one_process_is_still_rejected(tmp_path):
    """Nothing is remembered between calls: a path accepted once, whose deep ancestor
    is then swapped for a junction to the outside, is rejected on the next call in
    the SAME process (the installer's write-time re-check depends on this)."""
    root = tmp_path / "home"
    parent = root / "l1" / "l2" / "l3" / "l4"
    parent.mkdir(parents=True)
    candidate = parent / "SKILL.md"
    candidate.write_text("x", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()

    driver = tmp_path / "same_process.ps1"
    driver.write_text(_SAME_PROCESS_DRIVER, encoding="ascii")
    r = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(driver),
                        "-Guard", str(GUARD_PATH), "-Root", str(root),
                        "-Candidate", str(candidate), "-Outside", str(outside)],
                       capture_output=True, text=True)
    assert "FIRST " in r.stdout, (r.stdout, r.stderr)
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "SECOND-REJECTED" in r.stdout and "SECURITY" in r.stdout, r.stdout


def test_guard_rejects_junction_deep_below_ordinary_directories(tmp_path):
    """The escape sits after several ordinary directories (the fast-path segments)."""
    root = tmp_path / "root"
    mid = root / "a" / "b" / "c" / "d"
    mid.mkdir(parents=True)
    outside = tmp_path / "outside"
    (outside / "e").mkdir(parents=True)
    _junction(mid / "j", outside)
    result = _guard(mid / "j" / "e" / "new.md", root)
    assert result.returncode == 3, (result.stdout, result.stderr)
    assert "SECURITY" in result.stderr
