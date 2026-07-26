"""
Explicit provider-selection scenarios for the neutral runtime/skill-router.ps1.

Every scenario invokes the REAL router (dry-run based, so no live credentials or
model calls) and asserts the documented CLI-compatibility contract in
documentation/architecture.md sections 5-6:

  - -Provider claude|gpt|local  explicit selection
  - -Provider (explicit) beats host metadata
  - -Model (deprecated alias)  maps onto -Provider
  - -Provider auto ambiguous  -> exit 2
  - -Provider auto unset      -> exit 2
  - Copilot-first GPT transport works WITHOUT OPENAI_API_KEY

There is NO .claude dependency here: the router path is the neutral runtime home.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTER_PATH = REPO_ROOT / "runtime" / "skill-router.ps1"

HOST_MARKERS = [
    "CLAUDECODE",
    "CLAUDE_CODE_ENTRYPOINT",
    "COPILOT_CLI",
    "COPILOT_AGENT_SESSION_ID",
]

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")


def _run(args, extra_env=None, strip_markers=True):
    env = os.environ.copy()
    if strip_markers:
        for marker in HOST_MARKERS:
            env.pop(marker, None)
    # Deterministic spend line (no auto-generated session-id warning noise).
    env["SKILL_ROUTER_SESSION_ID"] = "router-scenario-test"
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


def test_router_exists():
    assert ROUTER_PATH.is_file(), f"missing neutral router: {ROUTER_PATH}"


def test_provider_claude_selection():
    result = _run(["-Provider", "claude", "-Skill", "plan-init", "-DryRun"])
    assert result.returncode == 0, result.stderr
    assert "--provider claude --skill plan-init" in result.stdout
    assert "claude-capable: True" in result.stdout


def test_provider_gpt_selection():
    result = _run(["-Provider", "gpt", "-Skill", "plan-init", "-DryRun"])
    assert result.returncode == 0, result.stderr
    assert "--provider gpt --skill plan-init" in result.stdout
    assert "GPT peer:" in result.stdout
    assert "gpt-capable:    True" in result.stdout


def test_provider_local_selection():
    # plan-init is local-capable in config/model-mapping.json.
    result = _run(["-Provider", "local", "-Skill", "plan-init", "-DryRun"])
    assert result.returncode == 0, result.stderr
    assert "--provider local --skill plan-init" in result.stdout
    assert "local-capable:  True" in result.stdout


def test_explicit_provider_overrides_host_metadata():
    # CLAUDECODE present would auto-select claude, but explicit -Provider gpt wins.
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init", "-DryRun"],
        extra_env={"CLAUDECODE": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert "--provider gpt --skill plan-init" in result.stdout
    assert "GPT peer:" in result.stdout


def test_model_alias_maps_to_provider_and_warns():
    result = _run(["-Model", "gpt", "-Skill", "plan-init", "-DryRun"])
    assert result.returncode == 0, result.stderr
    assert "--provider gpt --skill plan-init" in result.stdout
    # Deprecation notice goes to stderr; stdout is the routing plan.
    assert "deprecated" in result.stderr.lower()


def test_auto_ambiguous_exits_2():
    result = _run(
        ["-Provider", "auto", "-Skill", "plan-init", "-DryRun"],
        extra_env={"CLAUDECODE": "1", "COPILOT_CLI": "1"},
    )
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert "ambiguous" in result.stderr.lower()


def test_auto_unset_exits_2():
    # All four host markers stripped -> auto cannot resolve.
    result = _run(["-Provider", "auto", "-Skill", "plan-init", "-DryRun"])
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert "-Provider claude|gpt" in result.stderr


def test_auto_claude_only_selects_claude():
    result = _run(
        ["-Provider", "auto", "-Skill", "plan-init", "-DryRun"],
        extra_env={"CLAUDECODE": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert "--provider claude --skill plan-init" in result.stdout


def test_auto_gpt_only_selects_gpt():
    result = _run(
        ["-Provider", "auto", "-Skill", "plan-init", "-DryRun"],
        extra_env={"COPILOT_CLI": "copilot-session"},
    )
    assert result.returncode == 0, result.stderr
    assert "--provider gpt --skill plan-init" in result.stdout


def test_copilot_path_without_openai_key():
    # Copilot-first transport: a GitHub token is enough; OPENAI_API_KEY is optional.
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init", "-DryRun"],
        extra_env={"OPENAI_API_KEY": None, "COPILOT_GITHUB_TOKEN": "test-copilot-token"},
    )
    assert result.returncode == 0, result.stderr
    assert (
        "Copilot token:     present "
        "(COPILOT_GITHUB_TOKEN/GH_TOKEN/GITHUB_TOKEN/gh auth token)"
    ) in result.stdout
    assert "OPENAI_API_KEY:    NOT SET" in result.stdout


def test_invalid_skill_name_rejected():
    # Path traversal in the skill name is a security reject (exit 2), not fail-open.
    result = _run(["-Provider", "claude", "-Skill", "../../evil", "-DryRun"])
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert "SECURITY" in result.stderr
