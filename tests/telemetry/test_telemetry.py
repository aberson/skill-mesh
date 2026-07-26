"""
Tests for the re-homed telemetry writer/summary (runtime/telemetry/).

Both scripts are invoked through their real PowerShell entry points against a
neutral output path (a temp file under the OS temp tree, allowed by the writer's
path guard). No .claude dependency.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
TELEMETRY_DIR = REPO_ROOT / "runtime" / "telemetry"
TELEMETRY_WRITER = TELEMETRY_DIR / "telemetry-writer.ps1"
TELEMETRY_SUMMARY = TELEMETRY_DIR / "telemetry-summary.ps1"

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")


def test_telemetry_scripts_exist():
    assert TELEMETRY_WRITER.is_file(), f"missing writer: {TELEMETRY_WRITER}"
    assert TELEMETRY_SUMMARY.is_file(), f"missing summary: {TELEMETRY_SUMMARY}"


def test_telemetry_writer_creates_and_appends_stub_jsonl(tmp_path):
    output_path = tmp_path / "invocations.jsonl"
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    env["SKILL_MESH_TELEMETRY_PATH"] = str(output_path)

    command = [
        PWSH,
        "-NonInteractive",
        "-File",
        str(TELEMETRY_WRITER),
        "-Skill", "plan-init",
        "-Model", "gpt-5.5",
        "-TokensIn", "100",
        "-TokensOut", "50",
        "-LatencyMs", "25",
        "-CostUsd", "0.01",
        "-Verdict", "pass",
    ]
    first = subprocess.run(command, env=env, capture_output=True, text=True)
    second = subprocess.run(command, env=env, capture_output=True, text=True)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    records = [json.loads(line) for line in output_path.read_text().splitlines()]
    assert len(records) == 2
    # No OPENAI_API_KEY -> stub verdict, zeroed metrics.
    assert records[0]["verdict"] == "stub"
    assert records[0]["tokens_in"] == 0
    assert records[0]["tokens_out"] == 0
    assert records[0]["cost_usd"] == 0


def test_telemetry_summary_prints_model_comparison(tmp_path):
    output_path = tmp_path / "invocations.jsonl"
    records = [
        {
            "timestamp": "2026-07-24T00:00:00Z",
            "skill": "plan-init",
            "model": "gpt-5.5",
            "tokens_in": 100,
            "tokens_out": 50,
            "latency_ms": 20,
            "cost_usd": 0.01,
            "verdict": "pass",
        },
        {
            "timestamp": "2026-07-24T00:01:00Z",
            "skill": "plan-init",
            "model": "gpt-5.5",
            "tokens_in": 200,
            "tokens_out": 70,
            "latency_ms": 40,
            "cost_usd": 0.02,
            "verdict": "fail",
        },
    ]
    output_path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["SKILL_MESH_TELEMETRY_PATH"] = str(output_path)

    result = subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(TELEMETRY_SUMMARY)],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "skill" in result.stdout
    assert "avg_tokens_in" in result.stdout
    assert "plan-init" in result.stdout
    assert "gpt-5.5" in result.stdout


def test_telemetry_summary_empty_log_is_graceful(tmp_path):
    output_path = tmp_path / "invocations.jsonl"
    output_path.write_text("", encoding="utf-8")
    env = os.environ.copy()
    env["SKILL_MESH_TELEMETRY_PATH"] = str(output_path)

    result = subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(TELEMETRY_SUMMARY)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "No telemetry records" in result.stdout


def test_telemetry_writer_rejects_traversal_path(tmp_path):
    # A SKILL_MESH_TELEMETRY_PATH that canonicalizes OUTSIDE the fixed allowed roots
    # (repo / OS temp / LOCALAPPDATA) must be rejected -- not validated against its
    # own parent. Escape to the drive root, which is under none of those roots.
    drive = Path(tmp_path).drive or "C:"
    escape_path = f"{drive}\\skillmesh-evil-telemetry-{tmp_path.name}.jsonl"
    env = os.environ.copy()
    env["SKILL_MESH_TELEMETRY_PATH"] = escape_path

    result = subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(TELEMETRY_WRITER),
         "-Skill", "plan-init", "-Model", "gpt-5.5",
         "-TokensIn", "1", "-TokensOut", "1", "-LatencyMs", "1",
         "-CostUsd", "0.0", "-Verdict", "pass"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, (result.returncode, result.stdout)
    assert "SECURITY" in result.stderr
    assert not Path(escape_path).exists()
