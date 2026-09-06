"""Drift gate for review-deep's package-local model-tier-map snapshot (#177).

Step RD-lite imported `config/model-tier-map.json` into review-deep's canonical
package tree as `skills/review-deep/config/model-tier-map.json`. That is the
step's SECOND exact duplication (the first is the `scripts/` package, pinned by
`test_review_deep_scripts_duplication.py`), and `dev/.claude/rules/code-quality.md`
"one source of truth for data-shape constants" is explicit that duplicate
definitions always drift when nothing compares them.

The snapshot is inert TODAY -- nothing reads it yet; wiring it into the manifest,
builder or installer is deferred work -- which is exactly why the drift would be
invisible: an operator retiers a model in the root config (the file's whole
purpose), every OTHER gate stays green because none of them reads the snapshot,
and it silently keeps the old tiering until the day a later step ships it.

Two assertions, deliberately not one -- they discriminate:

- RAW BYTES is the wider net. A snapshot re-serialized with different
  indentation or key order reds here while the parsed assertion stays green.
- PARSED JSON is the louder one. When it fires too, the tier MAPPING itself
  changed rather than the formatting -- a different remedy.

Both sides are read from the WORKING TREE, never pinned as a recorded digest:
a digest bakes the authoring machine's line endings into the gate.

When the snapshot is eventually wired to a real consumer (or generated rather
than copied), replace this gate with the generator's own round-trip check
instead of deleting it.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

ROOT_CONFIG = "config/model-tier-map.json"
SNAPSHOT = "skills/review-deep/config/model-tier-map.json"


def _read_bytes(rel):
    path = REPO_ROOT / rel
    assert path.is_file(), (
        f"{rel} is missing -- this gate pins {SNAPSHOT} against {ROOT_CONFIG}; "
        f"if either was intentionally removed, delete or repoint the gate in "
        f"the same change rather than leaving it vacuous")
    return path.read_bytes()


def test_review_deep_tier_map_snapshot_is_byte_identical_to_the_root_config():
    root_bytes = _read_bytes(ROOT_CONFIG)
    snapshot_bytes = _read_bytes(SNAPSHOT)

    # Vacuity floor: an empty (or truncated-to-nothing) pair would compare equal.
    assert len(root_bytes) > 0, f"{ROOT_CONFIG} is empty"

    assert snapshot_bytes == root_bytes, (
        f"{SNAPSHOT} has drifted from {ROOT_CONFIG} "
        f"({len(snapshot_bytes)} bytes vs {len(root_bytes)}). The snapshot is a "
        f"verbatim copy: re-copy it from the root config in the same change that "
        f"edits the root config.")


def test_review_deep_tier_map_snapshot_parses_to_the_same_mapping():
    root_json = json.loads(_read_bytes(ROOT_CONFIG).decode("utf-8-sig"))
    snapshot_json = json.loads(_read_bytes(SNAPSHOT).decode("utf-8-sig"))

    assert root_json, f"{ROOT_CONFIG} parsed to an empty document"
    assert snapshot_json == root_json, (
        f"{SNAPSHOT} and {ROOT_CONFIG} describe DIFFERENT model tierings -- not "
        f"a formatting difference. Re-copy the snapshot from the root config; "
        f"do not hand-edit one side.")
