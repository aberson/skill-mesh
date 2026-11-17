"""No class, no pass: every collected test file has exactly one class in tests/gate-classes.json.

The catalog gate runs the files whose class carries the catalog flag. A hand-listed
selection silently drops a new repo-wide scan (the w3 router-scan miss), and a
directory glob would repeat it, so the map is keyed by exact path and this test
fails on any file it does not name. The checker is tests/gate/gate_classes.py; this
file runs it on the repository, or on the tree GATE_CLASSES_ROOT names, and proves
on synthetic trees that each failure it exists for goes red.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

GATE_DIR = Path(__file__).resolve().parents[1] / "gate"
sys.path.insert(0, str(GATE_DIR))
import gate_classes as gc  # noqa: E402

THIS_TEST = Path(__file__).resolve()

PLAIN = "def test_ok():\n    assert True\n"
SHELLS = "import subprocess\n\ndef test_install():\n    subprocess.run(['powershell', '-File', 'x.ps1'])\n"
MIXED = SHELLS + "\ndef test_fast():\n    assert True\n"


def test_every_test_file_has_exactly_one_class():
    problems = gc.check_tree(gc.tree_root())
    assert not problems, "\n".join(problems)


# --- synthetic trees ---------------------------------------------------------

def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _tree(root: Path, files: dict[str, str], mapping: dict[str, dict], raw_map: str | None = None) -> Path:
    for rel, text in files.items():
        _write(root, rel, text)
    data = {
        "classes": {
            "catalog-content": {"catalog": True, "reason": "fast content scans"},
            "installer": {"catalog": False, "reason": "shells out to PowerShell"},
        },
        "files": mapping,
    }
    _write(root, gc.MAP_RELPATH, raw_map if raw_map is not None else json.dumps(data, indent=2))
    return root


GOOD_FILES = {
    "tests/package-integrity/test_scan.py": PLAIN,
    "tests/distributions/test_install.py": SHELLS,
}
GOOD_MAP = {
    "tests/package-integrity/test_scan.py": {"class": "catalog-content"},
    "tests/distributions/test_install.py": {"class": "installer"},
}


def _problems(tmp_path: Path, extra_files=None, mapping=None, raw_map=None) -> list[str]:
    files = dict(GOOD_FILES, **(extra_files or {}))
    root = _tree(tmp_path, files, GOOD_MAP if mapping is None else mapping, raw_map)
    return gc.check_tree(root)


def test_known_good_tree_passes(tmp_path):
    assert _problems(tmp_path) == []


def test_unclassified_file_in_router_dir_fails(tmp_path):
    # (a) the glob case: a new scan dropped beside existing router tests.
    problems = _problems(tmp_path, {"tests/router/test_new_scan.py": PLAIN})
    assert problems == ["unclassified test file (add it to tests/gate-classes.json by exact path): "
                        "tests/router/test_new_scan.py"]


def test_unclassified_file_elsewhere_fails(tmp_path):
    # (b) outside tests/: the walk follows pytest's collection, not a root list.
    problems = _problems(tmp_path, {"skills/demo/scripts/test_demo.py": PLAIN})
    assert problems == ["unclassified test file (add it to tests/gate-classes.json by exact path): "
                        "skills/demo/scripts/test_demo.py"]


def test_non_catalog_file_without_marker_or_reason_fails(tmp_path):
    # (c) a fast scan cannot be excluded from the catalog gate by default.
    files = {"tests/router/test_fast_scan.py": PLAIN}
    mapping = dict(GOOD_MAP, **{"tests/router/test_fast_scan.py": {"class": "installer"}})
    problems = _problems(tmp_path, files, mapping)
    assert problems == ["non-catalog file with no PowerShell marker needs an exclude_reason: "
                        "tests/router/test_fast_scan.py"]
    mapping["tests/router/test_fast_scan.py"]["exclude_reason"] = "measured slow; see the class table"
    assert _problems(tmp_path, files, mapping) == []


def test_entry_for_deleted_file_fails(tmp_path):
    # (d) a stale entry is a red, not dead weight.
    mapping = dict(GOOD_MAP, **{"tests/router/test_gone.py": {"class": "catalog-content"}})
    assert _problems(tmp_path, mapping=mapping) == ["map entry matches no test file: tests/router/test_gone.py"]


def test_mixed_file_is_reported_not_failed(tmp_path):
    # Report-only until Step 1's per-test seconds exist (coordinator decision, 2026-11-17).
    files = {"tests/distributions/test_both.py": MIXED}
    mapping = dict(GOOD_MAP, **{"tests/distributions/test_both.py": {"class": "installer"}})
    assert _problems(tmp_path, files, mapping) == []
    rows = gc.mixed_files(tmp_path)
    assert [r.split("\t")[0] for r in rows] == ["tests/distributions/test_both.py"]
    assert "1 of 2 tests reach a marker" in rows[0]


def test_glob_and_directory_keys_are_rejected(tmp_path):
    for key in ("tests/router/test_*.py", "tests/router/", "tests/router/test_?.py"):
        mapping = dict(GOOD_MAP, **{key: {"class": "catalog-content"}})
        problems = _problems(tmp_path, mapping=mapping)
        assert len(problems) == 1 and "not an exact forward-slash .py file path" in problems[0], key


def test_one_file_with_two_classes_is_rejected(tmp_path):
    raw = textwrap.dedent('''
        {"classes": {"catalog-content": {"catalog": true, "reason": "r"},
                     "installer": {"catalog": false, "reason": "r"}},
         "files": {"tests/package-integrity/test_scan.py": {"class": "catalog-content"},
                   "tests/package-integrity/test_scan.py": {"class": "installer"},
                   "tests/distributions/test_install.py": {"class": "installer"}}}
    ''')
    problems = _problems(tmp_path, raw_map=raw)
    assert problems == ["duplicate key in tests/gate-classes.json: tests/package-integrity/test_scan.py"]


def test_walk_and_collector_disagreement_fails(tmp_path):
    # A file pytest cannot collect (an import error) is walked but not collected.
    files = {"tests/router/test_broken.py": "import no_such_module_anywhere\n" + PLAIN}
    mapping = dict(GOOD_MAP, **{"tests/router/test_broken.py": {"class": "catalog-content"}})
    problems = _problems(tmp_path, files, mapping)
    assert any(p.startswith("collection error: ERROR") for p in problems), problems
    assert "walked but not collected (the walk is out of step with pytest): tests/router/test_broken.py" in problems


def test_catalog_files_are_the_flagged_classes(tmp_path):
    root = _tree(tmp_path, GOOD_FILES, GOOD_MAP)
    assert gc.catalog_files(gc.load_map(root)) == ["tests/package-integrity/test_scan.py"]


def test_the_completeness_test_honors_the_root_variable(tmp_path):
    good = _tree(tmp_path / "good", GOOD_FILES, GOOD_MAP)
    bad = _tree(tmp_path / "bad", dict(GOOD_FILES, **{"tests/router/test_new_scan.py": PLAIN}), GOOD_MAP)
    node = "%s::test_every_test_file_has_exactly_one_class" % THIS_TEST
    codes = {}
    for name, root in (("good", good), ("bad", bad)):
        env = dict(os.environ, **{gc.ROOT_ENV: str(root)})
        proc = subprocess.run([sys.executable, "-m", "pytest", node, "-q", "-p", "no:cacheprovider"],
                              env=env, capture_output=True, text=True, timeout=600)
        codes[name] = proc.returncode
        if name == "bad":
            assert "tests/router/test_new_scan.py" in proc.stdout, proc.stdout[-2000:]
    assert codes == {"good": 0, "bad": 1}
