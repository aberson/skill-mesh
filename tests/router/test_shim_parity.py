"""
Legacy-shim generation + dry-run parity.

tools/gen-router-shim.ps1 emits a backward-compatibility shim at the legacy path
.claude/lib/skill-router.ps1 (a MIGRATION-PROVENANCE path only -- it is generated
into a temp install dir here, never into a live .claude tree). This test installs
the shim into a temp directory and proves it delegates to runtime/skill-router.ps1
with byte-identical dry-run stdout and the same exit code -- i.e. no behavior loss.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTER_PATH = REPO_ROOT / "runtime" / "skill-router.ps1"
GENERATOR_PATH = REPO_ROOT / "tools" / "gen-router-shim.ps1"

HOST_MARKERS = [
    "CLAUDECODE",
    "CLAUDE_CODE_ENTRYPOINT",
    "COPILOT_CLI",
    "COPILOT_AGENT_SESSION_ID",
]

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")


def _deterministic_env():
    env = os.environ.copy()
    for marker in HOST_MARKERS:
        env.pop(marker, None)
    # Fixed so the spend line and peer resolution are identical for both runs.
    env["SKILL_ROUTER_SESSION_ID"] = "shim-parity-test"
    env["SKILL_MESH_CLAUDE_TIER"] = "opus"
    return env


def _run_file(script, args, env):
    return subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(script), *args],
        env=env,
        capture_output=True,
        text=True,
    )


def test_generator_exists():
    assert GENERATOR_PATH.is_file(), f"missing generator: {GENERATOR_PATH}"


def test_shim_generates_at_legacy_path(tmp_path):
    gen = _run_file(GENERATOR_PATH, ["-Destination", str(tmp_path)], os.environ.copy())
    assert gen.returncode == 0, gen.stderr
    shim = tmp_path / ".claude" / "lib" / "skill-router.ps1"
    assert shim.is_file(), f"shim not generated at {shim}"
    body = shim.read_text(encoding="utf-8")
    # It must genuinely delegate to the canonical runtime router.
    assert "skill-router.ps1" in body
    assert str(ROUTER_PATH) in body


def test_shim_dry_run_parity(tmp_path):
    gen = _run_file(GENERATOR_PATH, ["-Destination", str(tmp_path)], os.environ.copy())
    assert gen.returncode == 0, gen.stderr
    shim = tmp_path / ".claude" / "lib" / "skill-router.ps1"
    assert shim.is_file()

    args = ["-Provider", "gpt", "-Skill", "plan-init", "-DryRun"]
    env = _deterministic_env()

    direct = _run_file(ROUTER_PATH, args, env)
    via_shim = _run_file(shim, args, env)

    assert direct.returncode == 0, direct.stderr
    assert via_shim.returncode == direct.returncode
    assert via_shim.stdout == direct.stdout, (
        "shim dry-run output diverged from the canonical router\n"
        f"--- direct ---\n{direct.stdout}\n--- shim ---\n{via_shim.stdout}"
    )
