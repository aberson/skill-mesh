"""
Shared scenario runner for tests/smoke/ (Step 40 of
documentation/provider-neutral-skill-mesh-plan.md): cross-provider adapter
resolution + shared-core parity + hermetic Copilot transport + bounded
Claude-fallback checks, exercised against the REAL runtime/skill-router.ps1.

Reuses the SAME hermetic patterns Step 37 established in tests/router/conftest.py
and tests/router/test_gpt_transport_precedence.py:
  - a local, ephemeral-port mock HTTP server stands in for Copilot/OpenAI
    (MockTransportServer / responses_api_body), never a real endpoint;
  - COPILOT_GITHUB_TOKEN is ALWAYS supplied explicitly (never cleared to None),
    so Get-CopilotToken's `gh auth token` subprocess fallback is structurally
    unreachable -- every scenario function below sets it before any other
    override is applied;
  - the base-transport env overrides (SKILL_MESH_COPILOT_BASE_URL /
    SKILL_MESH_OPENAI_BASE_URL) default to an unreachable loopback address
    (127.0.0.1:1), never a real cloud host.

Representative skills (one per family) come from
tests/fixtures/representative_skills.json -- the single source of truth so this
module, tests/smoke/test_cross_provider_smoke.py, and
tests/smoke/gen_release_candidate_report.py can never silently pick different
skills for the same family.

No path here references coding-root's private legacy `.claude` layout -- every
path is relative to THIS repo's own runtime/, config/, and skills/ trees.

Provider SELECTION vs adapter RESOLUTION (post-review distinction; see the
review note in test_cross_provider_smoke.py): `-DryRun` prints BOTH the GPT
and Claude entry points unconditionally (skill-router.ps1's dry-run block does
not branch on -Provider), so it can only prove that both adapters RESOLVE to
a real file -- it cannot prove which provider was actually SELECTED. Selection
is proven from a provider-CONDITIONED signal produced by a real (non-dry-run)
invocation: for GPT, the transmitted request body (gpt_copilot_live); for
Claude, the router's own "Routing to Claude" / "Claude entry point: <path>" /
"Claude invocation succeeded" dispatch lines, which never appear on a GPT path
and vice versa (claude_live_run).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTER_PATH = REPO_ROOT / "runtime" / "skill-router.ps1"
SKILLS_ROOT = REPO_ROOT / "skills"
FIXTURES_PATH = REPO_ROOT / "tests" / "fixtures" / "representative_skills.json"

# Reuse the Step-37 hermetic transport helpers (MockTransportServer,
# responses_api_body) rather than re-implementing them.
sys.path.insert(0, str(REPO_ROOT / "tests" / "router"))
from conftest import MockTransportServer, responses_api_body  # noqa: E402

PWSH = shutil.which("powershell")

HOST_MARKERS = ["CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "COPILOT_CLI", "COPILOT_AGENT_SESSION_ID"]
TRANSPORT_OVERRIDES = [
    "SKILL_MESH_COPILOT_BASE_URL",
    "SKILL_MESH_OPENAI_BASE_URL",
    "SKILL_MESH_TRANSPORT_TIMEOUT_SEC",
]

# Hermetic default token (Step 37 lesson, restated in test_gpt_transport_precedence.py):
# Get-CopilotToken shells out to a REAL `gh auth token` only when
# COPILOT_GITHUB_TOKEN/GH_TOKEN/GITHUB_TOKEN are ALL absent. run_router() below
# always supplies this fake, non-empty token so that branch is never reached.
HERMETIC_FAKE_COPILOT_TOKEN = "hermetic-fake-copilot-token-smoke-never-real"

# Loopback port 1: refuses connections immediately (no listener can bind to a
# privileged port as a non-elevated process) -- a fast, deterministic,
# always-local "transport unavailable" target.
UNREACHABLE_URL = "http://127.0.0.1:1"

# A sentinel that is ACTUALLY wired into the router as a real credential value
# in gpt_auth_failure_secret_redaction() below (COPILOT_GITHUB_TOKEN) -- unlike
# a value that is merely asserted absent without ever being supplied, this lets
# the assertion genuinely fail if redaction regresses.
PLANTED_SECRET = "sk-PLANTED-SMOKE-TEST-SECRET-7a6b5c4d3e2f"


def load_representative_skills():
    data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    return data["families"]


def run_router(args, extra_env=None, timeout=30, path_override=None):
    """Invoke the real router as a subprocess. Hermetic by default: host markers
    stripped, transport base URLs pinned to an unreachable loopback address,
    OPENAI_API_KEY unset, and a fake (non-empty) Copilot token supplied so the
    real `gh auth token` fallback is never reached. extra_env overrides any of
    these per-scenario (a value of None removes the key)."""
    env = os.environ.copy()
    for marker in HOST_MARKERS:
        env.pop(marker, None)
    for override in TRANSPORT_OVERRIDES:
        env.pop(override, None)
    env.pop("OPENAI_API_KEY", None)
    env["COPILOT_GITHUB_TOKEN"] = HERMETIC_FAKE_COPILOT_TOKEN
    env.pop("GH_TOKEN", None)
    env.pop("GITHUB_TOKEN", None)
    env["SKILL_ROUTER_SESSION_ID"] = "smoke-test-session"
    env["SKILL_MESH_COPILOT_BASE_URL"] = UNREACHABLE_URL
    env["SKILL_MESH_OPENAI_BASE_URL"] = UNREACHABLE_URL
    if path_override is not None:
        env["PATH"] = path_override
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


def adapter_paths(skill):
    return {
        "claude": SKILLS_ROOT / skill / "providers" / "claude.md",
        "gpt": SKILLS_ROOT / skill / "providers" / "gpt.md",
    }



# Matches a 'Core: <path>' declaration line (build-phase/plan-init/session-wrap
# style adapters), capturing the path TOKEN, not just detecting the line.
_CORE_LINE_RE = re.compile(r"^Core:\s*(\S+)", re.MULTILINE)

# Matches a markdown link whose TARGET ends in core.md, e.g.
# 'See [../core.md](../core.md) for the full specification.' (review-gauntlet
# style adapters). Captures the link target (the part in parens), which is the
# actual reference -- the link TEXT (in brackets) is not trusted.
_CORE_LINK_RE = re.compile(r"\]\(([^)\s]+core\.md)\)", re.IGNORECASE)


def _extract_declared_core_reference(text):
    """Parse the adapter's OWN declared core reference out of its real content
    -- either the 'Core: <path>' line form or the '[...](<path>core.md)'
    markdown link form -- and return the captured path token, or None if
    neither form is present. This is a real parse of what the file DECLARES,
    not a positional guess and not a bare substring-presence check: a decoy
    '../core.md' string sitting elsewhere in the file (a comment, a stray
    mention) that is NOT the actual 'Core:' value or link target is not
    matched by either regex and does not fool this function."""
    m = _CORE_LINE_RE.search(text)
    if m:
        return m.group(1).strip()
    m = _CORE_LINK_RE.search(text)
    if m:
        return m.group(1).strip()
    return None


def resolved_core_path_from_adapter(adapter_path):
    """Parse the adapter's OWN declared core reference (see
    _extract_declared_core_reference) and resolve THAT path relative to the
    adapter file's own directory -- e.g. a declared 'Core: ../core.md' in
    skills/X/providers/claude.md resolves to skills/X/core.md, but a declared
    'Core: ../../other-skill/core.md' resolves to skills/other-skill/core.md,
    a genuinely different file. (Post-review fix: an earlier version only
    checked for the literal substring '../core.md' ANYWHERE in the file and
    then computed the result POSITIONALLY [adapter_path.parent / '../core.md'],
    which always returned "this skill's own core.md" regardless of what the
    adapter actually declared -- for the fixed skills/<name>/providers/ layout
    that made the two-adapter parity check unreachable dead code, since both
    positional guesses were always identical. A decoy '../core.md' substring
    left elsewhere in the file, e.g. in an HTML comment, would have satisfied
    the old check even while the real 'Core:' line pointed somewhere else --
    see test_core_reference_parsing_detects_decoy_substring_content_drift.)
    Does not require the resolved file to exist; callers assert that."""
    text = adapter_path.read_text(encoding="utf-8")
    ref = _extract_declared_core_reference(text)
    assert ref, (
        f"{adapter_path} does not declare a parseable core reference "
        "(no 'Core: <path>' line and no '[...](<path>core.md)' markdown link found)"
    )
    return (adapter_path.parent / ref).resolve()


def canonical_core(skill):
    """The ONE core.md both provider adapters for `skill` must reference.
    Resolves each adapter's own '../core.md' reference INDEPENDENTLY (by
    reading that adapter's own file, not by deriving a path from the skill
    name) and ASSERTS the two resolve to the same file -- a skill whose two
    adapters disagreed on which core to use raises here, rather than silently
    reporting an independently-recomputed hash that could never disagree with
    itself. Returns (resolved_path, sha256_hex)."""
    paths = adapter_paths(skill)
    claude_core = resolved_core_path_from_adapter(paths["claude"])
    gpt_core = resolved_core_path_from_adapter(paths["gpt"])
    if claude_core != gpt_core:
        raise AssertionError(
            f"{skill}: claude adapter core ({claude_core}) != gpt adapter core ({gpt_core})"
        )
    if not claude_core.is_file():
        raise AssertionError(f"{skill}: resolved canonical core does not exist: {claude_core}")
    return claude_core, hashlib.sha256(claude_core.read_bytes()).hexdigest()


def canonical_core_hash(skill):
    return canonical_core(skill)[1]


def dryrun_entrypoints(stdout):
    """Parse the '    GPT:    <path>' / '    Claude: <path>' lines a -DryRun run
    always prints (regardless of which -Provider was requested) into
    {'gpt': path_or_None, 'claude': path_or_None}. NOTE: because -DryRun prints
    BOTH lines unconditionally, this can prove adapter RESOLUTION only, never
    provider SELECTION -- see claude_live_run / gpt_copilot_live for that."""
    out = {"gpt": None, "claude": None}
    for line in stdout.splitlines():
        s = line.strip()
        if s.startswith("GPT:"):
            val = s[len("GPT:"):].strip()
            out["gpt"] = None if val.startswith("(") else val
        elif s.startswith("Claude:"):
            val = s[len("Claude:"):].strip()
            out["claude"] = None if val.startswith("(") else val
    return out


# --------------------------------------------------------------------------- #
# Scenario runners -- each returns a normalized dict consumed by both the
# smoke tests and the release-candidate report generator.
# --------------------------------------------------------------------------- #

def claude_dry_run(skill):
    """Adapter RESOLUTION (not selection -- see module docstring): -DryRun with
    -Provider claude prints the Claude entry point the router would use."""
    r = run_router(["-Provider", "claude", "-Skill", skill, "-DryRun"])
    eps = dryrun_entrypoints(r.stdout)
    adapter = eps["claude"]
    return {
        "skill": skill,
        "scenario": "claude dry-run adapter resolution",
        "adapter": adapter,
        "core_hash": canonical_core_hash(skill) if adapter else None,
        "transport": "host-native (dry-run, no invocation)",
        "verdict": "DRYRUN_OK" if (r.returncode == 0 and adapter) else "DRYRUN_FAIL",
        "exit_code": r.returncode,
        "fallback": "n/a",
        "raw": r,
    }


def gpt_dry_run(skill):
    """Adapter RESOLUTION (not selection -- see module docstring): -DryRun with
    -Provider gpt prints the GPT entry point the router would use."""
    r = run_router(["-Provider", "gpt", "-Skill", skill, "-DryRun"])
    eps = dryrun_entrypoints(r.stdout)
    adapter = eps["gpt"]
    return {
        "skill": skill,
        "scenario": "gpt dry-run adapter resolution",
        "adapter": adapter,
        "core_hash": canonical_core_hash(skill) if adapter else None,
        "transport": "copilot (declared precedence, dry-run)",
        "verdict": "DRYRUN_OK" if (r.returncode == 0 and adapter) else "DRYRUN_FAIL",
        "exit_code": r.returncode,
        "fallback": "n/a",
        "raw": r,
    }


def claude_live_run(skill):
    """Real (non-dry-run) Claude invocation -- the genuine provider SELECTION
    proof for Claude. Invoke-ClaudeModel is a stub (no network call), but the
    router's own dispatch lines are provider-CONDITIONED: 'Routing to Claude
    for skill ...', 'Claude entry point: <path>', and 'Claude invocation
    succeeded for ...' are emitted only when Claude is actually dispatched, and
    the GPT-specific 'via copilot' / 'via openai-direct' substrings never
    appear on this path. A run that instead dispatched to GPT (a code defect)
    would fail every assertion built on these lines."""
    r = run_router(["-Provider", "claude", "-Skill", skill])
    entry_point = None
    needle = "Claude entry point: "
    for line in r.stdout.splitlines():
        idx = line.find(needle)
        if idx != -1:
            entry_point = line[idx + len(needle):].strip()
    ok = (
        r.returncode == 0
        and f"Routing to Claude for skill '{skill}'" in r.stdout
        and f"Claude invocation succeeded for '{skill}'." in r.stdout
        and "via copilot" not in r.stdout
        and "via openai-direct" not in r.stdout
        and entry_point is not None
    )
    return {
        "skill": skill,
        "scenario": "claude live invocation (provider-conditioned selection proof)",
        "adapter": entry_point,
        "core_hash": canonical_core_hash(skill),
        "transport": "host-native",
        "verdict": "PASS" if ok else "FAIL",
        "exit_code": r.returncode,
        "fallback": "none",
        "raw": r,
    }


def gpt_copilot_live(skill, path_override=None):
    """Real (non-dry-run) GPT invocation via the mock Copilot transport, with
    OPENAI_API_KEY explicitly unset -- proves Copilot alone is sufficient. This
    is the genuine provider SELECTION proof for GPT: the transmitted request
    body carries the actual selected GPT adapter's content (see
    test_copilot_invocation_transmits_the_selected_adapter_content), and
    'Routing to Claude' never appears (no fallback occurred)."""
    srv = MockTransportServer(status=200, body=responses_api_body(f"SMOKE_OK:{skill}"))
    try:
        r = run_router(
            ["-Provider", "gpt", "-Skill", skill],
            extra_env={"SKILL_MESH_COPILOT_BASE_URL": srv.base_url, "OPENAI_API_KEY": None},
            path_override=path_override,
        )
    finally:
        srv.shutdown()
    ok = (
        r.returncode == 0
        and f"GPT invocation succeeded for '{skill}' via copilot." in r.stdout
        and "Routing to Claude" not in r.stdout
    )
    return {
        "skill": skill,
        "scenario": "gpt live invocation via Copilot (no OPENAI_API_KEY, provider-conditioned selection proof)",
        "adapter": str(adapter_paths(skill)["gpt"]),
        "core_hash": canonical_core_hash(skill),
        "transport": "copilot",
        "verdict": "PASS" if ok else "FAIL",
        "exit_code": r.returncode,
        "fallback": "none",
        "raw": r,
        "mock_received": srv.received,
    }


def gpt_fallback_to_claude(skill):
    """Both GPT transports unavailable (Copilot unreachable via the hermetic
    default, no OPENAI_API_KEY) -> exactly ONE bounded Claude retry."""
    r = run_router(["-Provider", "gpt", "-Skill", skill], extra_env={"OPENAI_API_KEY": None})
    retry_count = r.stdout.count("Attempting single Claude retry")
    success_count = r.stdout.count("Claude invocation succeeded")
    one_transition = retry_count == 1 and success_count == 1
    ok = r.returncode == 2 and one_transition
    return {
        "skill": skill,
        "scenario": "gpt transport unavailable -> bounded Claude fallback",
        "adapter": str(adapter_paths(skill)["claude"]),
        "core_hash": canonical_core_hash(skill),
        "transport": "claude (single-transition fallback)",
        "verdict": "PASS" if ok else "FAIL",
        "exit_code": r.returncode,
        "fallback": f"one-transition-to-claude (retry_count={retry_count}, success_count={success_count})",
        "raw": r,
    }


def gpt_auth_failure_secret_redaction(skill):
    """Plants PLANTED_SECRET as the credential the router ACTUALLY receives
    (COPILOT_GITHUB_TOKEN), forces a 401 from the mock Copilot transport so the
    router's error-handling/diagnostic path runs with that value in scope, then
    lets the caller assert the sentinel is absent from stdout/stderr. This is a
    real end-to-end redaction probe: because the secret genuinely reaches the
    router, the assertion FAILS if Protect-SecretsInText regresses -- unlike
    asserting a value's absence without ever supplying it. Mirrors the pattern
    tests/router/test_gpt_transport_precedence.py established in Step 37
    (test_copilot_auth_failure_falls_back_to_claude)."""
    srv = MockTransportServer(status=401, body={"error": "invalid_token"})
    try:
        r = run_router(
            ["-Provider", "gpt", "-Skill", skill],
            extra_env={
                "SKILL_MESH_COPILOT_BASE_URL": srv.base_url,
                "COPILOT_GITHUB_TOKEN": PLANTED_SECRET,
                "OPENAI_API_KEY": None,
            },
        )
    finally:
        srv.shutdown()
    no_leak = PLANTED_SECRET not in r.stdout and PLANTED_SECRET not in r.stderr
    ok = r.returncode == 2 and no_leak
    return {
        "skill": skill,
        "scenario": "planted-secret redaction on Copilot 401 -> Claude fallback",
        "adapter": str(adapter_paths(skill)["claude"]),
        "core_hash": canonical_core_hash(skill),
        "transport": "claude (fallback after redacted auth failure)",
        "verdict": "PASS" if ok else "FAIL",
        "exit_code": r.returncode,
        "fallback": "one-transition-to-claude (secret-redaction probe)",
        "raw": r,
    }
