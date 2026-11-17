"""Load and check tests/gate-classes.json, the per-file test class map (catalog gate).

The map classifies every collected test file by EXACT path: no globs, no directory
entries. A new test file must be added by name, which is what forces the
classification decision (documentation/v3-catalog-gate-plan.md, Step 2). The
completeness test, tests/package-integrity/test_gate_classes.py, calls
check_tree() on the repository (or on the tree named by GATE_CLASSES_ROOT) and
fails on any problem it returns.

Which files are test files is derived, never listed: the walk applies pytest's own
collection defaults (python_files `test_*.py` and `*_test.py`, the default
norecursedirs) over the whole tree, minus paths Git ignores, and is cross-checked
against `pytest --collect-only` so the walk and the collector cannot drift apart.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

GATE_DIR = Path(__file__).resolve().parent
REPO_ROOT = GATE_DIR.parents[1]
MAP_RELPATH = "tests/gate-classes.json"
ROOT_ENV = "GATE_CLASSES_ROOT"

sys.path.insert(0, str(GATE_DIR))
from marker_scan import Scanner  # noqa: E402

# pytest's defaults (python_files, norecursedirs); no ini in this repo overrides them.
PYTHON_FILES = ("test_*.py", "*_test.py")
NORECURSE = ("*.egg", ".*", "_darcs", "build", "CVS", "dist", "node_modules", "venv", "{arch}")
FILE_KEYS = {"class", "exclude_reason", "mixed_reason"}
CLASS_KEYS = {"catalog", "reason"}


def tree_root() -> Path:
    """The tree to check: GATE_CLASSES_ROOT when set, else this repository."""
    value = os.environ.get(ROOT_ENV)
    return Path(value).resolve() if value else REPO_ROOT


class MapError(ValueError):
    pass


def _no_duplicates(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise MapError("duplicate key in %s: %s" % (MAP_RELPATH, key))
        seen[key] = value
    return seen


def load_map(root: Path) -> dict:
    """Parse and shape-check the map; raise MapError on any malformed entry."""
    path = root / MAP_RELPATH
    if not path.is_file():
        raise MapError("missing %s" % MAP_RELPATH)
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicates)
    if set(data) != {"classes", "files"}:
        raise MapError("top level must be exactly {classes, files}, got %s" % sorted(data))
    for name, cls in data["classes"].items():
        if set(cls) != CLASS_KEYS or not isinstance(cls["catalog"], bool) or not cls["reason"].strip():
            raise MapError("class %s needs exactly a boolean `catalog` and a non-empty `reason`" % name)
    for key, entry in data["files"].items():
        if any(c in key for c in "*?[") or key.endswith("/") or "\\" in key or not key.endswith(".py"):
            raise MapError("map key is not an exact forward-slash .py file path: %s" % key)
        if not set(entry) <= FILE_KEYS or "class" not in entry:
            raise MapError("entry %s: keys must be `class` plus optional %s" % (key, sorted(FILE_KEYS - {"class"})))
        if entry["class"] not in data["classes"]:
            raise MapError("entry %s: unknown class %s" % (key, entry["class"]))
        for reason in ("exclude_reason", "mixed_reason"):
            if reason in entry and not str(entry[reason]).strip():
                raise MapError("entry %s: empty %s" % (key, reason))
    return data


def catalog_files(data: dict) -> list[str]:
    """Every mapped file whose class carries the catalog flag."""
    flagged = {n for n, c in data["classes"].items() if c["catalog"]}
    return sorted(f for f, e in data["files"].items() if e["class"] in flagged)


def _ignored(root: Path, rels: list[str]) -> set[str]:
    if not rels or not (root / ".git").exists():
        return set()
    proc = subprocess.run(["git", "-C", str(root), "check-ignore", "--stdin"],
                          input="\n".join(rels), capture_output=True, text=True)
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def walk_test_files(root: Path) -> list[str]:
    """Every file pytest would collect from `root`, by its default rules, minus Git-ignored paths."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not any(fnmatch.fnmatch(d, p) for p in NORECURSE))
        for name in filenames:
            if any(fnmatch.fnmatch(name, p) for p in PYTHON_FILES):
                found.append((Path(dirpath) / name).relative_to(root).as_posix())
    ignored = _ignored(root, found)
    return sorted(f for f in found if f not in ignored)


def _normalize(file_id: str, root: Path) -> str:
    """A parent pytest.ini can make pytest's rootdir an ancestor of `root`; strip that prefix."""
    parts = file_id.split("/")
    for i in range(len(parts)):
        candidate = "/".join(parts[i:])
        if (root / candidate).is_file():
            return candidate
    return file_id


def collected_files(root: Path) -> tuple[set[str], list[str]]:
    """File ids from `pytest --collect-only -q` run in `root`, and any collection errors."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    files, errors = set(), []
    for line in proc.stdout.splitlines():
        if "::" in line and not line.startswith(" "):
            files.add(_normalize(line.split("::", 1)[0].strip(), root))
        elif line.startswith("ERROR"):
            errors.append(line.strip())
    if proc.returncode not in (0, 5):
        errors.append("pytest --collect-only exited %d" % proc.returncode)
    ignored = _ignored(root, sorted(files))
    return {f for f in files if f not in ignored}, errors


def _scanned(root: Path, walked: list[str], mapped: dict):
    scanner = Scanner(root)
    for f in walked:
        if f in mapped:
            yield f, mapped[f], scanner.scan_file(root / f)


def mixed_files(root: Path) -> list[str]:
    """Report (not a red) every mapped file where some tests reach a marker and some do not.

    Report-only until Step 1's per-test seconds exist; then it becomes a red for
    non-catalog files, each mixed_reason citing measured seconds (coordinator
    decision, 2026-11-17). Catalog-class mixed files stay bounded by Step 5's
    time guard.
    """
    data = load_map(root)
    rows = []
    for f, entry, scan in _scanned(root, walk_test_files(root), data["files"]):
        reach = list(scan["tests"].values())
        if any(reach) and not all(reach):
            catalog = data["classes"][entry["class"]]["catalog"]
            rows.append("%s\t%s\tcatalog=%s\t%d of %d tests reach a marker\t%s" % (
                f, entry["class"], catalog, sum(reach), len(reach), entry.get("mixed_reason", "")))
    return rows


def check_tree(root: Path, collect: bool = True) -> list[str]:
    """Return every completeness problem in `root`; an empty list is a pass."""
    try:
        data = load_map(root)
    except (MapError, json.JSONDecodeError) as exc:
        return [str(exc)]
    problems = []
    walked = walk_test_files(root)
    mapped = data["files"]
    for f in walked:
        if f not in mapped:
            problems.append("unclassified test file (add it to %s by exact path): %s" % (MAP_RELPATH, f))
    for f in sorted(set(mapped) - set(walked)):
        problems.append("map entry matches no test file: %s" % f)

    for f, entry, scan in _scanned(root, walked, mapped):
        catalog = data["classes"][entry["class"]]["catalog"]
        if not catalog and not scan["powershell_marker"] and "exclude_reason" not in entry:
            problems.append("non-catalog file with no PowerShell marker needs an exclude_reason: %s" % f)

    if collect:
        got, errors = collected_files(root)
        problems += ["collection error: " + e for e in errors]
        for f in sorted(got - set(walked)):
            problems.append("collected but not walked (the walk is out of step with pytest): %s" % f)
        for f in sorted(set(walked) - got):
            problems.append("walked but not collected (the walk is out of step with pytest): %s" % f)
    return problems


if __name__ == "__main__":
    # The mixed-file report for the gate evidence: python tests/gate/gate_classes.py --mixed
    if sys.argv[1:] != ["--mixed"]:
        sys.exit("usage: python tests/gate/gate_classes.py --mixed")
    rows = mixed_files(tree_root())
    print("\n".join(rows))
    print("mixed files: %d (report-only)" % len(rows))
