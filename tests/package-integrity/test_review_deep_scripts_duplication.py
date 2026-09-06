"""Byte-identity pin between the two `review-deep/scripts/` copies (issue #177).

Step RD-lite imported review-deep's calibration corpus into the canonical
package tree at `skills/review-deep/`. Four of the imported leaves --
`scripts/README.md`, `aggregate.py`, `auth_gate_probe.sh`, `lint_prepass.sh` --
already existed byte-identical in the LEGACY top-level `review-deep/` package,
so the repository now carries the same script package in two places.

Retiring the legacy copy is out of scope for RD-lite (smallest diff wins), which
leaves a live duplication hazard: an edit to one copy silently drifts from the
other, and `dev/.claude/rules/code-quality.md` "one source of truth for
data-shape constants" is explicit that duplicate definitions always drift. This
gate makes the drift loud. It does NOT bless the duplication -- when the legacy
package is finally retired, delete this file with it.

Enumerated, never hand-listed: both sides are walked from the filesystem, so a
fifth leaf added to either copy is covered automatically and an addition to only
ONE side is itself the failure (per the workspace lesson that hand-maintained
gate lists are false greens).

The walk skips CPython build artifacts -- `__pycache__/` and `*.pyc`/`*.pyo` --
and nothing else. Both copies hold `aggregate.py`, so the moment anything
imports it one tree grows a `__pycache__/` the other lacks, and an unfiltered
walk would then red with "the packages have diverged in CONTENTS" and instruct
the reader to add the `.pyc` to BOTH copies -- a false red with an actively
harmful remedy. The exclusion is deliberately that narrow: dotfiles are REAL
leaves of a script package, so a `.gitkeep` or `.gitattributes` present in only
one copy, or drifting in bytes between them, still reds.

Byte comparison is between the two WORKING-TREE files, not against a recorded
digest: a digest pinned on the authoring machine reds on any clone whose
checkout line-endings differ (workspace lesson -- never fingerprint source bytes
without normalizing CRLF/BOM). The same lesson applies WITHIN one clone: two
files can carry different checkout-era line endings in the same working tree
(git's stat cache preserves a smudge state older than the current autocrlf
setting -- measured 2026-09-06, when the legacy copy sat on disk as CRLF while
the freshly merged canonical copy was LF, blobs byte-identical). Comparison is
therefore newline-normalized: CRLF and lone CR read as LF on both sides. A
drift that consists ONLY of line endings is deliberately invisible here -- the
release pipeline normalizes CRLF->LF at checksum time, so eol is checkout
noise, not content.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CANONICAL = "skills/review-deep/scripts"
LEGACY = "review-deep/scripts"

# Vacuity floor, not an inventory: it only guards against both trees being
# emptied (or mis-rooted) and the equality assertions passing over nothing. It
# is a `>=` floor, so adding a fifth leaf needs no edit here.
MIN_LEAVES = 4

# Generated-artifact classes excluded from the walk (see the module docstring).
SKIP_DIR_NAMES = ("__pycache__",)
SKIP_SUFFIXES = (".pyc", ".pyo")

_RETIREMENT_HINT = (
    "If the legacy top-level review-deep package was RETIRED, delete this whole "
    "gate in the same change rather than leaving it vacuous or repairing it.")


def _normalized(raw):
    """Newline-normalize file bytes (CRLF and lone CR -> LF) before comparing."""
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _is_build_artifact(rel):
    """True for CPython build output, which is not part of the package."""
    if any(part in SKIP_DIR_NAMES for part in rel.parts):
        return True
    return rel.suffix.lower() in SKIP_SUFFIXES


def _leaves(root):
    """Every non-generated file under `root`, relative to it (posix spelling)."""
    return {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and not _is_build_artifact(p.relative_to(root))
    }


def test_leaves_skips_generated_artifacts_but_keeps_real_files(tmp_path):
    # Pins both arms of the filter. Without the first, a `__pycache__` in one
    # copy only reds the listings gate with a message blaming source drift;
    # with the filter any wider, a dotfile divergence is silently invisible.
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "aggregate.cpython-314.pyc").write_bytes(b"\x00")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "mod.pyc").write_bytes(b"\x00")
    (tmp_path / ".gitkeep").write_text("", encoding="utf-8")
    (tmp_path / "aggregate.py").write_text("# real\n", encoding="utf-8")
    (tmp_path / "nested" / "README.md").write_text("# real\n", encoding="utf-8")

    assert _leaves(tmp_path) == {".gitkeep", "aggregate.py", "nested/README.md"}


def test_script_package_listings_agree():
    canonical = _leaves(REPO_ROOT / CANONICAL)
    legacy = _leaves(REPO_ROOT / LEGACY)

    assert len(canonical) >= MIN_LEAVES, (
        f"{CANONICAL} holds {len(canonical)} files, expected at least "
        f"{MIN_LEAVES} -- the byte-identity assertions below would be vacuous. "
        f"{_RETIREMENT_HINT}")

    only_canonical = sorted(canonical - legacy)
    only_legacy = sorted(legacy - canonical)
    assert canonical == legacy, (
        f"the two review-deep script packages have diverged in CONTENTS.\n"
        f"  only in {CANONICAL}: {only_canonical}\n"
        f"  only in {LEGACY}: {only_legacy}\n"
        f"Add or remove the leaf in BOTH copies, or retire the legacy package "
        f"and delete this gate.")


def test_every_shared_script_leaf_is_byte_identical():
    leaves = sorted(_leaves(REPO_ROOT / CANONICAL) & _leaves(REPO_ROOT / LEGACY))
    assert len(leaves) >= MIN_LEAVES, (
        f"only {len(leaves)} shared leaves found, expected at least "
        f"{MIN_LEAVES}. {_RETIREMENT_HINT}")

    drifted = []
    for leaf in leaves:
        canonical_bytes = (REPO_ROOT / CANONICAL / leaf).read_bytes()
        legacy_bytes = (REPO_ROOT / LEGACY / leaf).read_bytes()
        if _normalized(canonical_bytes) != _normalized(legacy_bytes):
            drifted.append(
                f"{leaf} ({len(canonical_bytes)} bytes in {CANONICAL} vs "
                f"{len(legacy_bytes)} bytes in {LEGACY}, newline-normalized "
                f"before comparing)")

    assert not drifted, (
        f"review-deep script copies drifted -- edit BOTH copies identically, "
        f"or retire the legacy package and delete this gate:\n  "
        + "\n  ".join(drifted))
