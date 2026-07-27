"""
Per-source host-metadata adapters (Step 37): runtime/providers/claude-host.ps1
and runtime/providers/copilot-host.ps1.

Each adapter is invoked standalone in its CLI mode (-Detect), exactly like
runtime/path-guard.ps1's own dual-mode contract, so each of the FOUR approved
host-metadata sources from documentation/architecture.md section 5.3 is proven
individually -- independent of skill-router.ps1's composition logic (which is
covered separately in tests/router/test_router_scenarios.py).
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
CLAUDE_HOST_PATH = REPO_ROOT / "runtime" / "providers" / "claude-host.ps1"
COPILOT_HOST_PATH = REPO_ROOT / "runtime" / "providers" / "copilot-host.ps1"

ALL_MARKERS = [
    "CLAUDECODE",
    "CLAUDE_CODE_ENTRYPOINT",
    "COPILOT_CLI",
    "COPILOT_AGENT_SESSION_ID",
]

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")


def _detect(script_path, extra_env=None):
    env = os.environ.copy()
    for marker in ALL_MARKERS:
        env.pop(marker, None)
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(script_path), "-Detect"],
        env=env,
        capture_output=True,
        text=True,
    )
    return result


def test_adapters_exist():
    assert CLAUDE_HOST_PATH.is_file(), f"missing adapter: {CLAUDE_HOST_PATH}"
    assert COPILOT_HOST_PATH.is_file(), f"missing adapter: {COPILOT_HOST_PATH}"


# -- Claude host adapter: both approved markers, individually -----------------

def test_claude_host_detects_claudecode_marker():
    result = _detect(CLAUDE_HOST_PATH, {"CLAUDECODE": "1"})
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "claude"


def test_claude_host_detects_entrypoint_marker():
    result = _detect(CLAUDE_HOST_PATH, {"CLAUDE_CODE_ENTRYPOINT": "cli"})
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "claude"


def test_claude_host_unknown_when_absent():
    result = _detect(CLAUDE_HOST_PATH)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "unknown"


def test_claude_host_ignores_credential_vars():
    # ANTHROPIC_API_KEY / CLAUDE_CODE_OAUTH_TOKEN are credentials, not host identity
    # (architecture.md section 5.3) -- must NOT trigger detection.
    result = _detect(
        CLAUDE_HOST_PATH,
        {"ANTHROPIC_API_KEY": "fake-key", "CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth"},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "unknown"


def test_claude_host_requires_exact_value_for_claudecode():
    # CLAUDECODE must equal '1' exactly per the approved-marker table.
    result = _detect(CLAUDE_HOST_PATH, {"CLAUDECODE": "true"})
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "unknown"


# -- Copilot host adapter: both approved markers, individually ----------------

def test_copilot_host_detects_copilot_cli_marker():
    result = _detect(COPILOT_HOST_PATH, {"COPILOT_CLI": "1"})
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "gpt"


def test_copilot_host_detects_agent_session_marker():
    result = _detect(COPILOT_HOST_PATH, {"COPILOT_AGENT_SESSION_ID": "session-123"})
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "gpt"


def test_copilot_host_unknown_when_absent():
    result = _detect(COPILOT_HOST_PATH)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "unknown"


def test_copilot_host_ignores_credential_vars():
    # OPENAI_API_KEY / GH_TOKEN / GITHUB_TOKEN / COPILOT_GITHUB_TOKEN identify a
    # transport, not the active host -- must NOT trigger detection.
    result = _detect(
        COPILOT_HOST_PATH,
        {
            "OPENAI_API_KEY": "fake-key",
            "GH_TOKEN": "fake-gh",
            "GITHUB_TOKEN": "fake-gh2",
            "COPILOT_GITHUB_TOKEN": "fake-copilot",
        },
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "unknown"


def test_dot_sourcing_runs_no_detection_logic():
    # Dot-sourcing (no -Detect) must define the function without side effects --
    # i.e. it must not print/exit even when markers are present.
    env = os.environ.copy()
    for marker in ALL_MARKERS:
        env.pop(marker, None)
    env["CLAUDECODE"] = "1"
    script = f". '{CLAUDE_HOST_PATH}'; Write-Host 'loaded-ok'"
    result = subprocess.run(
        [PWSH, "-NonInteractive", "-Command", script],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    # If dot-sourcing ran detection and exited early, stdout would be 'claude' (or
    # 'unknown') INSTEAD of reaching the Write-Host line below the dot-source.
    assert result.stdout.strip() == "loaded-ok", (
        f"dot-sourcing must not run detection/exit as a side effect; got: {result.stdout!r}"
    )
