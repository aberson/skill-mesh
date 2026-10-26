"""
test_calibrate.py -- calibration harness tests (neutral home).

Re-homed from .claude/lib/calibration/test_calibrate.py (Step 34): ROUTER_PATH now
points at the neutral runtime/skill-router.ps1 and there is NO .claude dependency.
The router's explicit tier-peer / copilot / session scenarios are exercised HERE
via _run_router_dry_run (the same production caller the legacy suite used).

Telemetry writer/summary tests moved to tests/telemetry/test_telemetry.py; the
broader provider-selection scenarios live in tests/router/.

Run with: python -m pytest tests/calibration/test_calibrate.py
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Add calibration dir to path for direct import of the harness under test.
sys.path.insert(0, str(Path(__file__).parent))
import calibrate

PWSH = shutil.which("powershell")
ROUTER_PATH = calibrate.WORKSPACE_ROOT / "runtime" / "skill-router.ps1"


def _run_router_dry_run(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    # Uses the deprecated -Model alias on purpose: it must keep working and map
    # onto -Provider gpt without consulting host metadata.
    return subprocess.run(
        [
            PWSH,
            "-NonInteractive",
            "-File",
            str(ROUTER_PATH),
            "-Model",
            "gpt",
            "-Skill",
            "plan-init",
            "-DryRun",
        ],
        cwd=calibrate.WORKSPACE_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# assess_deterministic
# ---------------------------------------------------------------------------

class TestAssessDeterministic:
    def test_required_string_present_passes(self):
        spec = {"required_strings": ["hello"]}
        result = calibrate.assess_deterministic("say hello world", spec)
        assert result["pass"] is True

    def test_required_string_missing_fails(self):
        spec = {"required_strings": ["missing_token"]}
        result = calibrate.assess_deterministic("output without it", spec)
        assert result["pass"] is False
        assert any("missing_token" in f for f in result["findings"])

    def test_forbidden_string_absent_passes(self):
        spec = {"forbidden_strings": ["ERROR"]}
        result = calibrate.assess_deterministic("all good", spec)
        assert result["pass"] is True

    def test_forbidden_string_present_fails(self):
        spec = {"forbidden_strings": ["ERROR"]}
        result = calibrate.assess_deterministic("ERROR: something broke", spec)
        assert result["pass"] is False

    def test_min_length_passes(self):
        spec = {"min_length": 5}
        result = calibrate.assess_deterministic("hello world", spec)
        assert result["pass"] is True

    def test_min_length_fails(self):
        spec = {"min_length": 100}
        result = calibrate.assess_deterministic("short", spec)
        assert result["pass"] is False

    def test_required_keys_in_valid_json_passes(self):
        spec = {"required_keys": ["result", "halt"]}
        output = json.dumps({"result": "PASS", "halt": None})
        result = calibrate.assess_deterministic(output, spec)
        assert result["pass"] is True

    def test_required_key_missing_in_json_fails(self):
        spec = {"required_keys": ["result", "halt"]}
        output = json.dumps({"result": "PASS"})  # missing "halt"
        result = calibrate.assess_deterministic(output, spec)
        assert result["pass"] is False
        assert any("halt" in f for f in result["findings"])

    def test_invalid_json_when_required_keys_set_fails(self):
        spec = {"required_keys": ["result"]}
        result = calibrate.assess_deterministic("not json", spec)
        assert result["pass"] is False

    def test_empty_spec_always_passes(self):
        result = calibrate.assess_deterministic("anything", {})
        assert result["pass"] is True

    def test_mode_field_is_deterministic(self):
        result = calibrate.assess_deterministic("x", {})
        assert result["mode"] == "deterministic"


# ---------------------------------------------------------------------------
# assess_rubric
# ---------------------------------------------------------------------------

class TestAssessRubric:
    def test_all_sections_present_passes(self):
        spec = {"required_sections": ["## Phase", "Goal", "Step"]}
        actual = "## Phase 1\nGoal: something\nStep 1: do it"
        result = calibrate.assess_rubric(actual, spec)
        assert result["pass"] is True
        assert result["coverage"]["coverage_pct"] == 100.0

    def test_missing_section_fails(self):
        spec = {"required_sections": ["## Phase", "Goal", "Step"], "min_section_count": 3}
        actual = "## Phase 1\nGoal: something"  # missing "Step"
        result = calibrate.assess_rubric(actual, spec)
        assert result["pass"] is False
        assert "Step" in result["coverage"]["required_missing"]

    def test_min_section_count_partial_ok(self):
        # 2 of 3 required but min_section_count = 2 -> pass
        spec = {"required_sections": ["A", "B", "C"], "min_section_count": 2}
        actual = "A here and B here, but no C"
        result = calibrate.assess_rubric(actual, spec)
        assert result["pass"] is True

    def test_optional_sections_tracked_but_not_required(self):
        spec = {
            "required_sections": ["Goal"],
            "optional_sections": ["Risk", "Timeline"],
        }
        actual = "Goal: something\nRisk: low"
        result = calibrate.assess_rubric(actual, spec)
        assert result["pass"] is True
        assert "Risk" in result["coverage"]["optional_found"]
        assert "Timeline" not in result["coverage"]["optional_found"]

    def test_case_insensitive_matching(self):
        spec = {"required_sections": ["GOAL"]}
        actual = "goal: something"
        result = calibrate.assess_rubric(actual, spec)
        assert result["pass"] is True

    def test_empty_required_sections_always_passes(self):
        spec = {"required_sections": []}
        result = calibrate.assess_rubric("anything", spec)
        assert result["pass"] is True
        assert result["coverage"]["coverage_pct"] == 100.0

    def test_mode_field_is_rubric(self):
        result = calibrate.assess_rubric("x", {})
        assert result["mode"] == "rubric"


# ---------------------------------------------------------------------------
# run_calibration
# ---------------------------------------------------------------------------

class TestRunCalibration:
    def test_returns_record_with_both_models(self):
        spec = {"mode": "rubric", "required_sections": []}
        record = calibrate.run_calibration("plan-init", "test prompt", spec, ["claude", "gpt"])
        assert "claude" in record["models"]
        assert "gpt" in record["models"]

    def test_invocation_error_produces_fail_verdict(self):
        spec = {"mode": "rubric", "required_sections": ["impossible"]}
        record = calibrate.run_calibration("plan-init", "test", spec, ["claude"])
        # Claude stub always returns an error
        claude_result = record["models"]["claude"]
        assert claude_result["error"] is not None

    def test_record_contains_skill_name(self):
        spec = {}
        record = calibrate.run_calibration("test-skill", "prompt", spec, ["claude"])
        assert record["skill"] == "test-skill"

    def test_record_has_timestamp(self):
        spec = {}
        record = calibrate.run_calibration("test-skill", "prompt", spec, ["claude"])
        assert "timestamp" in record
        assert record["timestamp"].endswith("Z")


# ---------------------------------------------------------------------------
# Baseline JSON management
# ---------------------------------------------------------------------------

class TestBaselineManagement:
    def test_load_baseline_returns_skeleton_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(calibrate, "BASELINE_PATH", tmp_path / "nonexistent.json")
        baseline = calibrate.load_baseline()
        assert "pilots" in baseline
        assert baseline["schema_version"] == "1.0"

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        path = tmp_path / "baseline.json"
        monkeypatch.setattr(calibrate, "BASELINE_PATH", path)
        data = {"schema_version": "1.0", "pilots": {"plan-init": {"skill": "plan-init"}}}
        calibrate.save_baseline(data)
        loaded = calibrate.load_baseline()
        assert loaded["pilots"]["plan-init"]["skill"] == "plan-init"

    def test_update_baseline_upserts(self, tmp_path, monkeypatch):
        path = tmp_path / "baseline.json"
        monkeypatch.setattr(calibrate, "BASELINE_PATH", path)
        record = {"skill": "plan-init", "models": {}}
        calibrate.update_baseline("plan-init", record)
        baseline = calibrate.load_baseline()
        assert "plan-init" in baseline["pilots"]

    def test_baseline_file_is_utf8_no_bom(self, tmp_path, monkeypatch):
        path = tmp_path / "baseline.json"
        monkeypatch.setattr(calibrate, "BASELINE_PATH", path)
        calibrate.save_baseline({"schema_version": "1.0", "pilots": {}})
        raw = path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), "File must not have UTF-8 BOM"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestCLI:
    def test_list_exits_zero(self):
        rc = calibrate.main(["--list"])
        assert rc == 0

    def test_unknown_skill_without_input_exits_nonzero(self):
        rc = calibrate.main(["--skill", "nonexistent-skill"])
        assert rc != 0

    def test_pilot_runs_without_error(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(calibrate, "BASELINE_PATH", tmp_path / "baseline.json")
        rc = calibrate.main(["--pilot", "--models", "claude"])
        assert rc == 0
        baseline = calibrate.load_baseline()
        for skill in ("plan-init", "build-step", "review-gauntlet"):
            assert skill in baseline["pilots"]

    def test_help_without_args_exits_nonzero(self):
        rc = calibrate.main([])
        assert rc != 0


# ---------------------------------------------------------------------------
# GPT tier-peer resolution (PowerShell router, via the -Model alias)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")
def test_tier_haiku_resolves_gpt54mini():
    env = os.environ.copy()
    env["SKILL_MESH_CLAUDE_TIER"] = "haiku"
    result = _run_router_dry_run(env)
    assert result.returncode == 0, result.stderr
    assert "gpt-5.4-mini" in result.stdout


@pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")
def test_tier_sonnet_resolves_gpt54():
    env = os.environ.copy()
    env["SKILL_MESH_CLAUDE_TIER"] = "sonnet"
    result = _run_router_dry_run(env)
    assert result.returncode == 0, result.stderr
    assert "gpt-5.4" in result.stdout


@pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")
def test_tier_opus_resolves_gpt55():
    env = os.environ.copy()
    env["SKILL_MESH_CLAUDE_TIER"] = "opus"
    result = _run_router_dry_run(env)
    assert result.returncode == 0, result.stderr
    assert "gpt-5.5" in result.stdout


@pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")
def test_tier_fable_resolves_sol():
    env = os.environ.copy()
    env["SKILL_MESH_CLAUDE_TIER"] = "fable"
    result = _run_router_dry_run(env)
    assert result.returncode == 0, result.stderr
    assert "gpt-5.6-sol" in result.stdout


@pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")
def test_tier_unknown_model_falls_back_to_default():
    env = os.environ.copy()
    env.pop("SKILL_MESH_CLAUDE_TIER", None)
    env["SKILL_MESH_CLAUDE_MODEL"] = "claude-unknown-model"
    result = _run_router_dry_run(env)
    assert result.returncode == 0, result.stderr
    assert "gpt-5.6-sol" in result.stdout


@pytest.mark.skipif(PWSH is None, reason="powershell.exe is not available on PATH")
def test_copilot_token_resolution_uses_env_var():
    env = os.environ.copy()
    env["COPILOT_GITHUB_TOKEN"] = "test-copilot-token"
    result = _run_router_dry_run(env)
    assert result.returncode == 0, result.stderr
    # Issue #51: dry-run reports env-var presence + source class, materializing nothing.
    assert "Copilot token:     present (COPILOT_GITHUB_TOKEN)" in result.stdout


def test_router_version_is_updated():
    router_source = ROUTER_PATH.read_text(encoding="utf-8")
    assert "$ROUTER_VERSION = '1.3.0'" in router_source


@pytest.mark.skipif(PWSH is None, reason="powershell.exe is not available on PATH")
def test_router_session_id_autogenerated():
    env = os.environ.copy()
    env.pop("SKILL_ROUTER_SESSION_ID", None)
    result = _run_router_dry_run(env)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "HALT" not in output
