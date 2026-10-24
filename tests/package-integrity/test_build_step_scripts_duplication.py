"""Content pin between the two copies of build-step's capture script.

build-step's reviewed packaging exception (packet route P2) ships
`skills/build-step/scripts/capture_evidence.py` into every profile. That file is
an LF copy of the LEGACY top-level package's `build-step/scripts/capture_evidence.py`,
which stays in place for the legacy deprecation window, so the repository now
carries the same script twice. Duplicate definitions drift, and an edit to one
copy alone would change what the canonical skill ships without the legacy copy
(or the reverse) -- this gate makes that drift loud. It does not bless the
duplication: when the legacy package is retired, delete this file with it.

Only the shared leaf is compared. The canonical `scripts/` directory also holds
`build_step_tree.py`, the P1 mechanics helper, which has no legacy twin; the
legacy directory may not grow a leaf the canonical one lacks, because the
legacy capture script is the only file the P2 copy was taken from.

Comparison is newline-normalized (CRLF and lone CR read as LF on both sides),
for the reason `test_review_deep_scripts_duplication.py` records at length: a
checkout's line endings are a property of the clone, not of the content.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CANONICAL = "skills/build-step/scripts"
LEGACY = "build-step/scripts"
SHARED_LEAF = "capture_evidence.py"
# The canonical directory's own leaf with no legacy twin (the P1 helper).
CANONICAL_ONLY = {"build_step_tree.py"}

SKIP_DIR_NAMES = ("__pycache__",)
SKIP_SUFFIXES = (".pyc", ".pyo")

_RETIREMENT_HINT = (
    "If the legacy top-level build-step package was RETIRED, delete this whole "
    "gate in the same change rather than leaving it vacuous or repairing it.")


def _normalized(raw):
    """Newline-normalize file bytes (CRLF and lone CR -> LF) before comparing."""
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _leaves(root):
    """Every non-generated file under `root`, relative to it (posix spelling)."""
    out = set()
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if not p.is_file() or any(part in SKIP_DIR_NAMES for part in rel.parts):
            continue
        if rel.suffix.lower() in SKIP_SUFFIXES:
            continue
        out.add(rel.as_posix())
    return out


def test_leaves_skips_generated_artifacts_but_keeps_real_files(tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "capture_evidence.cpython-314.pyc").write_bytes(b"\x00")
    (tmp_path / ".gitkeep").write_text("", encoding="utf-8")
    (tmp_path / "capture_evidence.py").write_text("# real\n", encoding="utf-8")
    assert _leaves(tmp_path) == {".gitkeep", "capture_evidence.py"}


def test_script_listings_agree_apart_from_the_p1_helper():
    canonical = _leaves(REPO_ROOT / CANONICAL)
    legacy = _leaves(REPO_ROOT / LEGACY)
    assert SHARED_LEAF in legacy, f"{LEGACY}/{SHARED_LEAF} is missing. {_RETIREMENT_HINT}"
    assert legacy == {SHARED_LEAF}, (
        f"{LEGACY} now holds {sorted(legacy)}; the P2 copy was taken from "
        f"{SHARED_LEAF} alone, so a new legacy leaf has no canonical twin.")
    assert canonical == legacy | CANONICAL_ONLY, (
        f"{CANONICAL} holds {sorted(canonical)}, expected exactly "
        f"{sorted(legacy | CANONICAL_ONLY)} -- the reviewed P2 exception names "
        f"these files and no others.")


def test_shared_capture_script_is_identical_modulo_newlines():
    canonical_bytes = (REPO_ROOT / CANONICAL / SHARED_LEAF).read_bytes()
    legacy_bytes = (REPO_ROOT / LEGACY / SHARED_LEAF).read_bytes()
    assert canonical_bytes.strip(), "the canonical capture script is empty"
    assert _normalized(canonical_bytes) == _normalized(legacy_bytes), (
        f"{SHARED_LEAF} drifted between {CANONICAL} ({len(canonical_bytes)} bytes) "
        f"and {LEGACY} ({len(legacy_bytes)} bytes), newline-normalized before "
        f"comparing -- edit BOTH copies identically, or retire the legacy package "
        f"and delete this gate.")


def test_comparison_reds_on_a_one_byte_drift():
    # Red-on-garbage anchor: the comparison the gate relies on must see a
    # single changed byte and must not see a pure line-ending difference.
    original = (REPO_ROOT / CANONICAL / SHARED_LEAF).read_bytes()
    crlf = _normalized(original).replace(b"\n", b"\r\n")
    assert _normalized(original) == _normalized(crlf)
    mutated = original.replace(b"headless", b"headfull", 1)
    assert mutated != original, "anchor mutation did not apply"
    assert _normalized(mutated) != _normalized(original)
