"""Pin helper tests to canonical v2 modules while retaining legacy fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

LEGACY_TEST_DIR = Path(__file__).resolve().parent
CANONICAL_DIR = Path(__file__).resolve().parents[2] / "skills" / "skill-iterate" / "scripts"
HELPER_MODULES = (
    "adversarial_calibration",
    "append_result",
    "differential_grader",
    "morning_summary",
    "resolve_queue",
    "structural_metrics",
)

for module_name in HELPER_MODULES:
    sys.modules.pop(module_name, None)
while str(CANONICAL_DIR) in sys.path:
    sys.path.remove(str(CANONICAL_DIR))
sys.path.insert(0, str(CANONICAL_DIR))
