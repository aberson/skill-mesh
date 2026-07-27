"""
GPT transport selection + authentication (Step 37): Copilot-first with an
OPTIONAL direct-OpenAI fallback transport, separate from provider selection.

These drive the REAL (non-dry-run) router end to end, but every external
transport is a local mock HTTP server (tests/router/conftest.py) via the
test-only SKILL_MESH_COPILOT_BASE_URL / SKILL_MESH_OPENAI_BASE_URL /
SKILL_MESH_TRANSPORT_TIMEOUT_SEC env overrides -- no live credentials and no
real network calls. Invoke-ClaudeModel is a stub in the current router (returns
'CLAUDE_NATIVE_EXECUTION' with no network call), so Claude-path assertions are
also safe to run for real.

Covers the Step 37 Done-when list:
  - host-bound Claude AND GPT invocation
  - explicit -Provider overrides
  - Copilot auth WITHOUT OPENAI_API_KEY
  - optional OpenAI fallback + transport precedence
  - token-expiry / authentication-failure handling
  - provider rate-limit / timeout behavior
  - no secret in any output
  - the bounded cross-provider retry contract (single Claude retry, not widened)
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import responses_api_body

PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTER_PATH = REPO_ROOT / "runtime" / "skill-router.ps1"

HOST_MARKERS = ["CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "COPILOT_CLI", "COPILOT_AGENT_SESSION_ID"]
TRANSPORT_OVERRIDES = [
    "SKILL_MESH_COPILOT_BASE_URL",
    "SKILL_MESH_OPENAI_BASE_URL",
    "SKILL_MESH_TRANSPORT_TIMEOUT_SEC",
]

PLANTED_SECRET = "sk-PLANTED-TEST-SECRET-9f8e7d6c5b4a"

# Loopback port 1 refuses connections immediately (no listener can bind to a
# privileged port as a non-elevated process) -- a fast, local, deterministic
# "unavailable" target for the transport base URLs.
UNREACHABLE_URL = "http://127.0.0.1:1"

# Hermetic default Copilot token. NEITHER the UNREACHABLE_URL base-URL default
# NOR clearing COPILOT_GITHUB_TOKEN/GH_TOKEN/GITHUB_TOKEN is sufficient on its
# own to prevent a real network call: Get-CopilotToken resolves a token BEFORE
# any HTTP request is attempted, and its 4th precedence step shells out to a
# REAL `gh auth token` subprocess if all three env vars are absent -- proven via
# a PATH-shimmed gh (this sandbox has `gh` authenticated: 3 real invocations
# logged from 3 tests that merely cleared the token env vars, even though the
# base URL was already hermetically unreachable). Every test therefore gets
# this fake, non-empty token by default; a test wanting a SPECIFIC value
# (a planted secret, an explicit "test-copilot-token") overrides it via
# extra_env, and that override always wins below. No test in this file should
# ever pass COPILOT_GITHUB_TOKEN/GH_TOKEN/GITHUB_TOKEN as None.
HERMETIC_FAKE_COPILOT_TOKEN = "hermetic-default-fake-copilot-token-never-real"

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")


def _run(args, extra_env=None, timeout=30):
    env = os.environ.copy()
    for marker in HOST_MARKERS:
        env.pop(marker, None)
    for override in TRANSPORT_OVERRIDES:
        env.pop(override, None)
    env.pop("OPENAI_API_KEY", None)
    # Hermetic defaults -- see UNREACHABLE_URL / HERMETIC_FAKE_COPILOT_TOKEN
    # docstrings above; extra_env below can override any of these.
    env["COPILOT_GITHUB_TOKEN"] = HERMETIC_FAKE_COPILOT_TOKEN
    env.pop("GH_TOKEN", None)
    env.pop("GITHUB_TOKEN", None)
    env["SKILL_ROUTER_SESSION_ID"] = "gpt-transport-test"
    env["SKILL_MESH_COPILOT_BASE_URL"] = UNREACHABLE_URL
    env["SKILL_MESH_OPENAI_BASE_URL"] = UNREACHABLE_URL
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
        timeout=timeout,
    )


def _assert_no_secret_leak(result):
    assert PLANTED_SECRET not in result.stdout, f"secret leaked in stdout: {result.stdout}"
    assert PLANTED_SECRET not in result.stderr, f"secret leaked in stderr: {result.stderr}"


# -- Real Responses-API output shapes (deep-review Block 1 fix) ---------------

def test_gpt_succeeds_on_reasoning_leading_output_shape(mock_transport_server):
    # Both Copilot peers (gpt-5.6-sol, gpt-5.5) are reasoning-tier models whose
    # real Responses-API output commonly LEADS with a {type:"reasoning"} item
    # that has NO "content" key, before the final {type:"message"} item that
    # does. Under Set-StrictMode -Version Latest, naked property access on that
    # leading item used to throw PropertyNotFoundException -- caught by the
    # surrounding try/catch and silently mis-reported as "Copilot transport
    # failed", defeating Copilot-first precedence for every real reasoning-tier
    # response. This must now succeed via the copilot transport, no fallback.
    srv = mock_transport_server(
        status=200,
        body=responses_api_body("REASONING_SHAPE_OK", reasoning_leading=True),
    )
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_COPILOT_BASE_URL": srv.base_url,
            "COPILOT_GITHUB_TOKEN": "test-copilot-token",
        },
    )
    assert result.returncode == 0, result.stderr
    assert "GPT invocation succeeded for 'plan-init' via copilot." in result.stdout
    assert "Copilot transport failed" not in result.stdout
    assert "Attempting single Claude retry" not in result.stdout


# -- Host-bound invocation (real, non-dry-run) ---------------------------------

def test_host_bound_claude_invocation_succeeds():
    result = _run(
        ["-Provider", "auto", "-Skill", "plan-init"],
        extra_env={"CLAUDECODE": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert "Claude invocation succeeded for 'plan-init'." in result.stdout


def test_host_bound_gpt_invocation_succeeds_via_copilot(mock_transport_server):
    srv = mock_transport_server(status=200, body=responses_api_body("OK"))
    result = _run(
        ["-Provider", "auto", "-Skill", "plan-init"],
        extra_env={
            "COPILOT_CLI": "1",
            "SKILL_MESH_COPILOT_BASE_URL": srv.base_url,
            "COPILOT_GITHUB_TOKEN": "test-copilot-token",
        },
    )
    assert result.returncode == 0, result.stderr
    assert "GPT invocation succeeded for 'plan-init' via copilot." in result.stdout
    assert len(srv.received) >= 2  # health check (/models) + invocation (/responses)


def test_explicit_provider_gpt_overrides_absent_host_metadata(mock_transport_server):
    # No host markers at all; -Provider gpt is still honored explicitly.
    srv = mock_transport_server(status=200, body=responses_api_body("OK"))
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_COPILOT_BASE_URL": srv.base_url,
            "COPILOT_GITHUB_TOKEN": "test-copilot-token",
        },
    )
    assert result.returncode == 0, result.stderr
    assert "via copilot" in result.stdout


# -- Copilot-first precedence, with/without the optional OpenAI key -----------

def test_copilot_succeeds_without_openai_api_key(mock_transport_server):
    # Selecting GPT must not require OPENAI_API_KEY: Copilot alone is sufficient.
    srv = mock_transport_server(status=200, body=responses_api_body("OK"))
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_COPILOT_BASE_URL": srv.base_url,
            "COPILOT_GITHUB_TOKEN": "test-copilot-token",
            "OPENAI_API_KEY": None,
        },
    )
    assert result.returncode == 0, result.stderr
    assert "via copilot" in result.stdout


def test_copilot_preferred_when_both_transports_available(mock_transport_server):
    copilot_srv = mock_transport_server(status=200, body=responses_api_body("COPILOT_OK"))
    openai_srv = mock_transport_server(status=200, body=responses_api_body("OPENAI_OK"))
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_COPILOT_BASE_URL": copilot_srv.base_url,
            "SKILL_MESH_OPENAI_BASE_URL": openai_srv.base_url,
            "COPILOT_GITHUB_TOKEN": "test-copilot-token",
            "OPENAI_API_KEY": "test-openai-key",
        },
    )
    assert result.returncode == 0, result.stderr
    assert "via copilot" in result.stdout
    assert len(openai_srv.received) == 0, "OpenAI must not be called when Copilot is available"


def test_openai_fallback_used_when_copilot_unavailable(mock_transport_server):
    # Copilot's endpoint is unreachable (the hermetic UNREACHABLE_URL default
    # from _run(), left un-overridden here) -> optional OpenAI fallback
    # transport is used instead. An EXPLICIT fake token is supplied (never
    # cleared) so Get-CopilotToken resolves it immediately and never falls
    # through to its `gh auth token` subprocess step -- clearing all three env
    # sources instead would (and, before this fix, did: proven via a
    # PATH-shimmed gh) shell out to the operator's REAL gh credential store.
    openai_srv = mock_transport_server(status=200, body=responses_api_body("OPENAI_OK"))
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_OPENAI_BASE_URL": openai_srv.base_url,
            "OPENAI_API_KEY": "test-openai-key",
            "COPILOT_GITHUB_TOKEN": "fake-copilot-token-unreachable-endpoint",
        },
    )
    assert result.returncode == 0, result.stderr
    assert "via openai-direct" in result.stdout
    assert len(openai_srv.received) >= 1


def test_openai_fallback_used_when_copilot_health_check_fails(mock_transport_server):
    copilot_srv = mock_transport_server(status=503, body={"error": "unavailable"})
    openai_srv = mock_transport_server(status=200, body=responses_api_body("OPENAI_OK"))
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_COPILOT_BASE_URL": copilot_srv.base_url,
            "SKILL_MESH_OPENAI_BASE_URL": openai_srv.base_url,
            "COPILOT_GITHUB_TOKEN": "test-copilot-token",
            "OPENAI_API_KEY": "test-openai-key",
        },
    )
    assert result.returncode == 0, result.stderr
    assert "via openai-direct" in result.stdout


def test_no_gpt_transport_available_falls_back_to_claude(mock_transport_server):
    # Copilot unavailable (endpoint unreachable via the hermetic default) AND
    # no OPENAI_API_KEY -> single Claude retry. An explicit fake Copilot token
    # is supplied (see comment in test_openai_fallback_used_when_copilot_unavailable
    # above) so this never shells out to the real `gh auth token`.
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "COPILOT_GITHUB_TOKEN": "fake-copilot-token-unreachable-endpoint",
            "OPENAI_API_KEY": None,
        },
    )
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert "Claude invocation succeeded for 'plan-init' (retry after GPT failure)." in result.stdout


# -- Token expiry / authentication failure -------------------------------------

def test_copilot_auth_failure_falls_back_to_claude(mock_transport_server):
    # 401 simulates an expired/invalid Copilot token.
    srv = mock_transport_server(status=401, body={"error": "invalid_token"})
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_COPILOT_BASE_URL": srv.base_url,
            "COPILOT_GITHUB_TOKEN": PLANTED_SECRET,
            "OPENAI_API_KEY": None,
        },
    )
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert "Claude invocation succeeded for 'plan-init' (retry after GPT failure)." in result.stdout
    _assert_no_secret_leak(result)


def test_openai_auth_failure_after_copilot_unavailable_falls_back_to_claude(mock_transport_server):
    # Copilot unreachable (hermetic default) with an explicit fake token (never
    # cleared -- see test_openai_fallback_used_when_copilot_unavailable comment
    # for why clearing it would shell out to the real `gh auth token`).
    openai_srv = mock_transport_server(status=401, body={"error": "invalid_api_key"})
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_OPENAI_BASE_URL": openai_srv.base_url,
            "OPENAI_API_KEY": PLANTED_SECRET,
            "COPILOT_GITHUB_TOKEN": "fake-copilot-token-unreachable-endpoint",
        },
    )
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert "Claude invocation succeeded for 'plan-init' (retry after GPT failure)." in result.stdout
    _assert_no_secret_leak(result)


# -- Rate limit / timeout ------------------------------------------------------

def test_copilot_rate_limit_falls_back_to_claude(mock_transport_server):
    srv = mock_transport_server(status=429, body={"error": "rate_limited"})
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_COPILOT_BASE_URL": srv.base_url,
            "COPILOT_GITHUB_TOKEN": PLANTED_SECRET,
            "OPENAI_API_KEY": None,
        },
    )
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert "Claude invocation succeeded for 'plan-init' (retry after GPT failure)." in result.stdout
    _assert_no_secret_leak(result)


def test_copilot_timeout_falls_back_to_claude(mock_transport_server):
    # Health check sleeps past the shortened test timeout -> WebException -> fail-open.
    srv = mock_transport_server(status=200, body={}, delay=3.0)
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_COPILOT_BASE_URL": srv.base_url,
            "SKILL_MESH_TRANSPORT_TIMEOUT_SEC": "1",
            "COPILOT_GITHUB_TOKEN": PLANTED_SECRET,
            "OPENAI_API_KEY": None,
        },
        timeout=30,
    )
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert "Claude invocation succeeded for 'plan-init' (retry after GPT failure)." in result.stdout
    _assert_no_secret_leak(result)


def test_openai_rate_limit_falls_back_to_claude(mock_transport_server):
    # The rate-limit/timeout Done-when item, exercised at the OpenAI-direct tier
    # (Copilot unreachable via the hermetic default -> OpenAI tried -> 429).
    openai_srv = mock_transport_server(status=429, body={"error": "rate_limited"})
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_OPENAI_BASE_URL": openai_srv.base_url,
            "OPENAI_API_KEY": PLANTED_SECRET,
            "COPILOT_GITHUB_TOKEN": "fake-copilot-token-unreachable-endpoint",
        },
    )
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert "Claude invocation succeeded for 'plan-init' (retry after GPT failure)." in result.stdout
    _assert_no_secret_leak(result)


def test_openai_timeout_falls_back_to_claude(mock_transport_server):
    openai_srv = mock_transport_server(status=200, body={}, delay=3.0)
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_OPENAI_BASE_URL": openai_srv.base_url,
            "SKILL_MESH_TRANSPORT_TIMEOUT_SEC": "1",
            "OPENAI_API_KEY": PLANTED_SECRET,
            "COPILOT_GITHUB_TOKEN": "fake-copilot-token-unreachable-endpoint",
        },
        timeout=30,
    )
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert "Claude invocation succeeded for 'plan-init' (retry after GPT failure)." in result.stdout
    _assert_no_secret_leak(result)


# -- Test-only base-URL override is gated to loopback (security fold item) ----

def test_dryrun_warns_and_ignores_non_loopback_base_url_override():
    # A stray/leaked SKILL_MESH_COPILOT_BASE_URL pointed at a non-loopback host
    # must be REJECTED, not honored -- otherwise a real credential could be
    # silently redirected to an attacker-controlled endpoint. Exercised via
    # -DryRun so this test makes no network call itself (Get-CopilotBaseUrl only
    # warns and returns the real default; it never dials out).
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init", "-DryRun"],
        extra_env={"SKILL_MESH_COPILOT_BASE_URL": "http://evil.example.com"},
    )
    assert result.returncode == 0, result.stderr
    assert "non-loopback host" in result.stdout
    assert "Dry-run complete. No API calls made." in result.stdout


def test_dryrun_accepts_loopback_base_url_override(mock_transport_server):
    srv = mock_transport_server(status=200)
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init", "-DryRun"],
        extra_env={"SKILL_MESH_COPILOT_BASE_URL": srv.base_url},
    )
    assert result.returncode == 0, result.stderr
    assert "non-loopback host" not in result.stdout
    assert "Dry-run complete. No API calls made." in result.stdout


def test_dryrun_shows_gpt_transport_precedence_line():
    result = _run(["-Provider", "gpt", "-Skill", "plan-init", "-DryRun"])
    assert result.returncode == 0, result.stderr
    assert (
        "GPT transport precedence: copilot -> openai-direct "
        "(2nd is optional; selecting GPT never requires OPENAI_API_KEY)"
    ) in result.stdout


# -- No secret in any output (planted-secret sweep) ----------------------------

def test_no_secret_leak_on_full_success_path(mock_transport_server):
    srv = mock_transport_server(status=200, body=responses_api_body("OK"))
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_COPILOT_BASE_URL": srv.base_url,
            "COPILOT_GITHUB_TOKEN": PLANTED_SECRET,
            "OPENAI_API_KEY": PLANTED_SECRET,
        },
    )
    assert result.returncode == 0, result.stderr
    _assert_no_secret_leak(result)


def test_no_secret_leak_when_both_transports_fail(mock_transport_server):
    copilot_srv = mock_transport_server(status=401, body={"error": "invalid_token"})
    openai_srv = mock_transport_server(status=401, body={"error": "invalid_api_key"})
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_COPILOT_BASE_URL": copilot_srv.base_url,
            "SKILL_MESH_OPENAI_BASE_URL": openai_srv.base_url,
            "COPILOT_GITHUB_TOKEN": PLANTED_SECRET,
            "OPENAI_API_KEY": PLANTED_SECRET,
        },
    )
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    _assert_no_secret_leak(result)


# -- Bounded cross-provider retry contract (not widened) -----------------------

def test_exactly_one_claude_retry_when_both_gpt_transports_exhausted(mock_transport_server):
    # Both Copilot and the optional OpenAI fallback fail -> exactly ONE Claude
    # retry (exit 2, EXIT_FALLBACK_USED), not repeated GPT attempts and not a
    # hard halt (exit 3). Each mock server must be hit exactly once.
    copilot_srv = mock_transport_server(status=500, body={"error": "server_error"})
    openai_srv = mock_transport_server(status=500, body={"error": "server_error"})
    result = _run(
        ["-Provider", "gpt", "-Skill", "plan-init"],
        extra_env={
            "SKILL_MESH_COPILOT_BASE_URL": copilot_srv.base_url,
            "SKILL_MESH_OPENAI_BASE_URL": openai_srv.base_url,
            "COPILOT_GITHUB_TOKEN": "test-copilot-token",
            "OPENAI_API_KEY": "test-openai-key",
        },
    )
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert result.stdout.count("Claude invocation succeeded") == 1
    assert result.stdout.count("Attempting single Claude retry") == 1
    # Health-check probes hit each mock exactly once -- no internal GPT retry loop.
    assert len(copilot_srv.received) == 1
    assert len(openai_srv.received) == 1
