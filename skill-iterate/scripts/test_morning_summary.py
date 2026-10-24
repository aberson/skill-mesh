"""Self-contained unit tests for morning_summary.write_morning_summary."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

_CANONICAL_IMPORT_DIR = Path(__file__).resolve().parents[2] / "skills" / "skill-iterate" / "scripts"
while str(_CANONICAL_IMPORT_DIR) in sys.path:
    sys.path.remove(str(_CANONICAL_IMPORT_DIR))
sys.path.insert(0, str(_CANONICAL_IMPORT_DIR))

import morning_summary as morning_summary_module
from morning_summary import SkillResult, write_morning_summary


CANONICAL_DIR = Path(__file__).resolve().parents[2] / "skills" / "skill-iterate" / "scripts"
assert Path(morning_summary_module.__file__).resolve().parent == CANONICAL_DIR

def _r(
    skill: str,
    baseline: float | None = 0.80,
    final: float | None = 0.85,
    delta: float | None = 0.05,
    iters: int = 3,
    wall: float = 100.0,
    status: str = "keep",
    keeps: list[str] | None = None,
    url: str | None = None,
) -> SkillResult:
    return SkillResult(
        skill=skill,
        baseline_score=baseline,
        final_score=final,
        delta=delta,
        iterations_run=iters,
        wall_seconds_total=wall,
        ship_status=status,
        top_keep_descriptions=keeps or [],
        parked_issue_url=url,
    )


class WriteMorningSummaryTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.runs_dir = Path(self._tmp.name) / "skill-iterate-runs"
        self.started = "2026-01-15T22:00:00Z"
        self.ended = "2026-01-16T05:30:00Z"

    def test_happy_path_writes_full_summary(self) -> None:
        results = [
            _r("session-wrap", 0.85, 0.91, 0.06, 4, 1842, "keep",
               keeps=["tighten rejection criteria", "remove redundant check"]),
            _r("skill-eval-setup", 0.70, 0.70, 0.00, 12, 3214, "no-improvement"),
        ]
        out = write_morning_summary(
            runs_dir=self.runs_dir,
            skill_results=results,
            started_at=self.started,
            ended_at=self.ended,
            date_str="2026-01-15",
            skipped_by_skip_list=["verify", "run"],
            skipped_by_cross_night=[{"skill": "build-overnight", "mtime_iso": "2026-01-15T10:00:00Z"}],
        )
        self.assertEqual(out, self.runs_dir / "2026-01-15.md")
        text = out.read_text(encoding="utf-8")
        self.assertIn("# /skill-iterate morning summary -- 2026-01-15", text)
        self.assertIn("## Per-skill results", text)
        self.assertIn("| session-wrap | 0.85 | 0.91 | +0.06 | 4 | 1842 | keep | -- |", text)
        self.assertIn("| skill-eval-setup | 0.70 | 0.70 | 0.00 | 12 | 3214 | no-improvement | -- |", text)
        self.assertIn("## Top keeps per skill", text)
        self.assertIn("### session-wrap (kept 2 of 4)", text)
        self.assertIn("1. tighten rejection criteria", text)
        self.assertIn("### skill-eval-setup (kept 0 of 12)", text)
        self.assertIn("(no keeps this run)", text)
        self.assertIn("## Skills excluded", text)
        self.assertIn("verify, run: skip-list", text)
        self.assertIn("build-overnight: cross-night-resume", text)
        self.assertIn("## Run metadata", text)
        self.assertIn(f"- Started: {self.started}", text)
        self.assertIn(f"- Ended: {self.ended}", text)
        self.assertIn("- Skills processed: 2", text)
        self.assertIn("- Skills excluded: 3", text)

    def test_filename_disambiguation(self) -> None:
        self.runs_dir.mkdir(parents=True)
        (self.runs_dir / "2026-01-15.md").write_text("pre-existing", encoding="utf-8")
        out = write_morning_summary(
            runs_dir=self.runs_dir,
            skill_results=[],
            started_at=self.started,
            ended_at=self.ended,
            date_str="2026-01-15",
        )
        self.assertEqual(out, self.runs_dir / "2026-01-15b.md")
        # Original file untouched.
        self.assertEqual(
            (self.runs_dir / "2026-01-15.md").read_text(encoding="utf-8"),
            "pre-existing",
        )

    def test_partial_flag_adds_header(self) -> None:
        out = write_morning_summary(
            runs_dir=self.runs_dir,
            skill_results=[_r("session-wrap")],
            started_at=self.started,
            ended_at=self.ended,
            date_str="2026-01-15",
            partial=True,
        )
        text = out.read_text(encoding="utf-8")
        # Trigger-agnostic wording: covers kill-switch / exception / finally.
        self.assertIn(f"(partial -- stopped at {self.ended})", text)
        # The old hardcoded kill-switch wording must not survive.
        self.assertNotIn("kill-switch hit at", text)

    def test_empty_skill_results_renders_zero_row_table(self) -> None:
        out = write_morning_summary(
            runs_dir=self.runs_dir,
            skill_results=[],
            started_at=self.started,
            ended_at=self.ended,
            date_str="2026-01-15",
        )
        text = out.read_text(encoding="utf-8")
        # H1 header present.
        self.assertIn("# /skill-iterate morning summary -- 2026-01-15", text)
        # Per-skill results section with table-header row, no data rows.
        self.assertIn("## Per-skill results", text)
        self.assertIn(
            "| skill | baseline | final | delta | iters | wall_s | status | link |",
            text,
        )
        self.assertIn("|---|---|---|---|---|---|---|---|", text)
        # Top keeps heading present with zero per-skill sub-sections.
        self.assertIn("## Top keeps per skill", text)
        self.assertNotIn("### ", text)
        # Run metadata reports zero skills processed.
        self.assertIn("## Run metadata", text)
        self.assertIn("- Skills processed: 0", text)

    def test_disambiguation_exhaustion_raises(self) -> None:
        # Pre-create base + b..z (27 files total) so every candidate slot is taken.
        self.runs_dir.mkdir(parents=True)
        (self.runs_dir / "2026-01-15.md").write_text("base", encoding="utf-8")
        for code in range(ord("b"), ord("z") + 1):
            (self.runs_dir / f"2026-01-15{chr(code)}.md").write_text(
                "taken", encoding="utf-8"
            )
        with self.assertRaises(FileExistsError):
            write_morning_summary(
                runs_dir=self.runs_dir,
                skill_results=[],
                started_at=self.started,
                ended_at=self.ended,
                date_str="2026-01-15",
            )

    def test_defect_park_link_rendering(self) -> None:
        results = [
            _r("fix-bug", None, None, None, 0, 0, "defect-park", url="#142"),
            _r("review-deep", None, None, None, 0, 0, "defect-park",
               url="docs/skill-iterate-runs/parked-2026-01-15.md"),
        ]
        out = write_morning_summary(
            runs_dir=self.runs_dir,
            skill_results=results,
            started_at=self.started,
            ended_at=self.ended,
            date_str="2026-01-15",
        )
        text = out.read_text(encoding="utf-8")
        # GitHub issue link renders as the verbatim '#142'.
        self.assertIn("| fix-bug | -- | -- | -- | 0 | 0 | defect-park | #142 |", text)
        # Local-fallback path renders as the verbatim path.
        self.assertIn(
            "| review-deep | -- | -- | -- | 0 | 0 | defect-park | docs/skill-iterate-runs/parked-2026-01-15.md |",
            text,
        )

    def test_review_required_link_rendering(self) -> None:
        out = write_morning_summary(
            runs_dir=self.runs_dir,
            skill_results=[_r("review-deep", status="review-required",
                              url="docs/skill-iterate-runs/proposals/review-deep.md")],
            started_at=self.started,
            ended_at=self.ended,
            date_str="2026-01-15",
        )
        self.assertIn(
            "| review-deep | 0.80 | 0.85 | +0.05 | 3 | 100 | review-required | docs/skill-iterate-runs/proposals/review-deep.md |",
            out.read_text(encoding="utf-8"),
        )

    def test_cli_accepts_review_required_and_rejects_unknown_status(self) -> None:
        script = CANONICAL_DIR / "morning_summary.py"
        base = {
            "skill": "review-deep", "baseline_score": 0.8,
            "final_score": 0.85, "delta": 0.05, "iterations_run": 3,
            "wall_seconds_total": 100, "top_keep_descriptions": [],
            "parked_issue_url": "proposal.md",
        }
        for status, expected in (("review-required", 0), ("unknown-status", 1)):
            payload = self.runs_dir / f"{status}.json"
            payload.parent.mkdir(parents=True, exist_ok=True)
            payload.write_text(json.dumps({"skill_results": [{**base, "ship_status": status}]}),
                               encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script), str(self.runs_dir), "--input", str(payload),
                 "--date", "2026-01-15"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, expected, result.stderr)

    def test_all_none_scores_skipped_from_top_keeps(self) -> None:
        # A skill that crashed before scoring (no baseline, no final) and is NOT
        # defect-park - e.g. dirty-master-skip. Should appear in the table with
        # '--' score columns, but be omitted from the 'Top keeps' section.
        results = [
            _r("dirty-skill", None, None, None, 0, 0, "dirty-master-skip"),
            _r("kept-skill", 0.50, 0.60, 0.10, 2, 50, "keep", keeps=["a fix"]),
        ]
        out = write_morning_summary(
            runs_dir=self.runs_dir,
            skill_results=results,
            started_at=self.started,
            ended_at=self.ended,
            date_str="2026-01-15",
        )
        text = out.read_text(encoding="utf-8")
        # Table row present with '--' score cells.
        self.assertIn("| dirty-skill | -- | -- | -- | 0 | 0 | dirty-master-skip | -- |", text)
        # 'Top keeps' section: kept-skill present, dirty-skill omitted entirely.
        self.assertIn("### kept-skill (kept 1 of 2)", text)
        self.assertNotIn("### dirty-skill", text)

    def test_excluded_section_omitted_when_empty(self) -> None:
        out = write_morning_summary(
            runs_dir=self.runs_dir,
            skill_results=[_r("session-wrap")],
            started_at=self.started,
            ended_at=self.ended,
            date_str="2026-01-15",
            skipped_by_skip_list=None,
            skipped_by_cross_night=None,
        )
        text = out.read_text(encoding="utf-8")
        self.assertNotIn("## Skills excluded", text)
        # Sanity: empty list is treated the same as None.
        out2 = write_morning_summary(
            runs_dir=self.runs_dir,
            skill_results=[_r("session-wrap")],
            started_at=self.started,
            ended_at=self.ended,
            date_str="2026-01-15",
            skipped_by_skip_list=[],
            skipped_by_cross_night=[],
        )
        text2 = out2.read_text(encoding="utf-8")
        self.assertNotIn("## Skills excluded", text2)


if __name__ == "__main__":
    unittest.main()
