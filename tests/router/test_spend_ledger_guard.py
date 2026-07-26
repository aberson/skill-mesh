"""
Spend-ledger path-traversal guard (deep-review Block fix).

The durable spend ledger is composed from SKILL_ROUTER_SESSION_ID and (optionally)
SKILL_MESH_LEDGER_DIR. A hostile value must NOT let the router read or write an
attacker-chosen location: the session id is sanitized to a filename-safe token and
the composed path is validated through Resolve-SafePath against a fixed allowed-root
set. These tests drive the real router (dry-run) as the production caller.
"""
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTER_PATH = REPO_ROOT / "runtime" / "skill-router.ps1"

HOST_MARKERS = ["CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "COPILOT_CLI", "COPILOT_AGENT_SESSION_ID"]

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")


def _run(args, extra_env=None):
    env = os.environ.copy()
    for marker in HOST_MARKERS:
        env.pop(marker, None)
    if extra_env:
        for key, value in extra_env.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
    return subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(ROUTER_PATH), *args],
        env=env,
        capture_output=True,
        text=True,
    )


def test_traversal_session_id_does_not_read_outside_ledger_dir(tmp_path):
    # Ledger base is tmp/base; plant a hostile ledger one level OUT, at tmp/evil.json,
    # with a large accumulated spend. A traversal session id must NOT reach it.
    base = tmp_path / "base"
    base.mkdir()
    escape_file = tmp_path / "evil.json"
    escape_file.write_text(
        '{"session_spend_usd":777.0,"ceiling_usd":5.0,"calls":[]}',
        encoding="utf-8",
    )

    result = _run(
        ["-Provider", "claude", "-Skill", "plan-init", "-DryRun"],
        extra_env={
            "SKILL_MESH_LEDGER_DIR": str(base),
            "SKILL_ROUTER_SESSION_ID": r"..\evil",
        },
    )
    assert result.returncode == 0, result.stderr
    # The planted spend must never be read: accumulated stays $0, "777" never appears.
    assert "777" not in result.stdout
    assert "Accumulated this session: $0" in result.stdout
    # And no ledger file was composed at the escape target (sanitized name stays in base).
    assert not (base / "evil.json").exists()


def test_absolute_session_id_is_neutralized(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    result = _run(
        ["-Provider", "claude", "-Skill", "plan-init", "-DryRun"],
        extra_env={
            "SKILL_MESH_LEDGER_DIR": str(base),
            "SKILL_ROUTER_SESSION_ID": r"C:\Windows\Temp\evil",
        },
    )
    assert result.returncode == 0, result.stderr
    # No drive-absolute escape; the run completes cleanly on the sanitized name.
    assert "Dry-run complete" in result.stdout


def test_ledger_dir_outside_allowed_roots_is_rejected(tmp_path):
    # A ledger dir at drive root is outside repo/temp/LOCALAPPDATA -> ledger disabled.
    drive = Path(tmp_path).drive or "C:"
    outside = f"{drive}\\skillmesh-evil-guard-{uuid.uuid4().hex}"
    result = _run(
        ["-Provider", "claude", "-Skill", "plan-init", "-DryRun"],
        extra_env={
            "SKILL_MESH_LEDGER_DIR": outside,
            "SKILL_ROUTER_SESSION_ID": "clean-session",
        },
    )
    assert result.returncode == 0, result.stderr
    assert "disabling durable spend tracking" in result.stderr
    assert not Path(outside).exists()


def test_scrubbed_environment_does_not_crash(tmp_path):
    # No LOCALAPPDATA / HOME / XDG / ledger dir -> must fall back safely, not throw.
    result = _run(
        ["-Provider", "claude", "-Skill", "plan-init", "-DryRun"],
        extra_env={
            "SKILL_MESH_LEDGER_DIR": None,
            "LOCALAPPDATA": None,
            "HOME": None,
            "XDG_DATA_HOME": None,
            "SKILL_ROUTER_SESSION_ID": "scrub-session",
        },
    )
    assert result.returncode == 0, result.stderr
    assert "Dry-run complete" in result.stdout
