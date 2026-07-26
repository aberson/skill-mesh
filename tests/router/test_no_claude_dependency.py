r"""
Regression guard for the Step-34 Done-when: no neutral runtime code REQUIRES a
`.claude` source root.

The one-time manual grep is replaced by a deterministic static scan of runtime/,
config/, and tests/. A load-bearing `.claude` PATH reference (`.claude` immediately
followed by a `/` or `\` separator) in executable code fails this test;
comment/docstring/provenance mentions (and JSON description/note/legacy_* fields)
are allowed, matching the reviewer's observation that every current mention lives in
a comment or docstring.

Excluded: the Step-33 migration manifest and its fixture/test (whose whole purpose
is to record legacy `.claude` sources) and this scanner file itself.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = ["runtime", "config", "tests"]

EXCLUDE_NAMES = {
    "skill-manifest.json",          # Step-33 migration manifest (provenance by design)
    "expected_inventory.json",      # Step-33 fixture
    "test_manifest_contract.py",    # reads the migration manifest
    "test_no_claude_dependency.py",  # this scanner references `.claude/` in its own patterns
}

# A load-bearing reference is `.claude` immediately followed by a path separator.
# Property access like `$v.claude` (no separator) is not a path and is ignored.
PATH_RE = re.compile(r"\.claude[\\/]")
JSON_PROVENANCE_KEY = re.compile(r'"(description|note|notes|legacy_[a-z_]+|source|dest)"\s*:')


def _iter_files():
    for d in SCAN_DIRS:
        base = REPO_ROOT / d
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.suffix not in {".ps1", ".py", ".json"}:
                continue
            if path.name in EXCLUDE_NAMES:
                continue
            if "__pycache__" in path.parts:
                continue
            yield path


def _strip_ps(text):
    text = re.sub(r"<#.*?#>", "", text, flags=re.S)  # block comments
    text = re.sub(r"#.*", "", text)                   # line comments
    return text


def _strip_py(text):
    text = re.sub(r'"""(?:.|\n)*?"""', "", text)      # triple-quoted (docstrings)
    text = re.sub(r"'''(?:.|\n)*?'''", "", text)
    text = re.sub(r"#.*", "", text)                   # line comments
    return text


def _violations(path):
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".ps1":
        return [path] if PATH_RE.search(_strip_ps(text)) else []
    if path.suffix == ".py":
        return [path] if PATH_RE.search(_strip_py(text)) else []
    # .json: allow `.claude/` only inside provenance/description/note fields.
    for line in text.splitlines():
        if PATH_RE.search(line) and not JSON_PROVENANCE_KEY.search(line):
            return [path]
    return []


def test_no_load_bearing_claude_path_in_neutral_tree():
    offenders = []
    scanned = 0
    for path in _iter_files():
        scanned += 1
        offenders.extend(str(p.relative_to(REPO_ROOT)) for p in _violations(path))
    assert scanned > 0, "scan found no files -- runtime/config/tests layout changed?"
    assert not offenders, (
        "load-bearing '.claude/...' path reference found in neutral runtime code "
        f"(comment/docstring/provenance mentions are allowed): {offenders}"
    )


def test_scan_covers_the_runtime_router():
    # Sanity: the scanner actually reaches the router (guards against an empty scan
    # silently passing if the directory layout moves).
    files = {p.name for p in _iter_files()}
    assert "skill-router.ps1" in files
    assert "model-mapping.json" in files
