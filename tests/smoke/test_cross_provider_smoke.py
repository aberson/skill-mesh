"""
Step 40 cross-provider package + workflow smoke tests
(documentation/provider-neutral-skill-mesh-plan.md).

Structural parity (Steps 33-39: every skill has a core.md + providers/{claude,
gpt}.md, the manifest is complete, distributions build/install cleanly) does
not prove that an installed profile actually DISPATCHES to the right adapter at
runtime and preserves the shared-core contract across providers. This suite
drives the REAL runtime/skill-router.ps1 (never a re-implementation) for one
representative skill per family:

    planning            -> plan-init
    review              -> review-gauntlet
    build-orchestration  -> build-phase
    session              -> session-wrap

(tests/fixtures/representative_skills.json is the single source of truth for
this mapping.)

For each representative skill this file asserts every Step-40 Done-when item:
  1. Adapter RESOLUTION: a Claude dry-run and a GPT dry-run each resolve to the
     expected provider-specific adapter file.
     IMPORTANT (post-review correction): `-DryRun` prints BOTH the GPT and
     Claude entry points unconditionally (skill-router.ps1's dry-run block does
     not branch on -Provider), so this proves RESOLUTION only -- that both
     adapters exist and are found -- never provider SELECTION. An earlier draft
     of this suite mislabeled these as "selection" tests; a -Provider gpt dry
     run asserting the Claude-adapter path would still pass, which is exactly
     the vacuous-test defect this docstring now calls out.
  2. Provider SELECTION (the real claim "the intended adapter was used"): a
     real (non-dry-run) invocation for EACH provider, asserted from a
     provider-CONDITIONED signal that could only appear on that provider's
     code path -- for GPT, the actual transmitted request body contains the
     selected GPT adapter's content; for Claude, the router's own
     "Routing to Claude" / "Claude entry point: <path>" dispatch lines (which
     never appear on a GPT-dispatch run, and vice versa).
  3. Shared-core parity: both provider adapters reference the SAME canonical
     core.md (a skill whose adapters disagree fails this test).
  4. Direct GPT via GitHub Copilot works WITHOUT OPENAI_API_KEY (hermetic mock
     transport; fake Copilot token so no real `gh auth token` call is made).
  5. A fallback scenario (both GPT transports unavailable) performs exactly ONE
     bounded Claude retry -- not zero, not repeated -- and preserves the
     documented exit code.
  6. Secret redaction has teeth: a planted sentinel is wired in as the REAL
     Copilot token the router receives (not merely asserted absent without
     ever being supplied), a 401 forces the error/diagnostic path, and the
     sentinel must never appear in stdout/stderr.

Hermeticity (release-acceptance requirement): every scenario runs through
tests/smoke/_scenarios.run_router, which pins transport base URLs to an
unreachable loopback address by default, supplies a fake non-empty Copilot
token (so Get-CopilotToken's `gh auth token` subprocess fallback is never
reached), and never sets OPENAI_API_KEY unless a test explicitly wants the
optional direct-OpenAI transport exercised. No test in this file makes a real
network call or reads the operator's real gh credentials.
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _scenarios as sc  # noqa: E402

pytestmark = pytest.mark.skipif(sc.PWSH is None, reason="powershell is not available on PATH")

FAMILIES = sc.load_representative_skills()
SKILLS = sorted(set(FAMILIES.values()))


def test_representative_skills_exist_and_are_gpt_and_claude_capable():
    # Sanity gate for the fixture itself: every family maps to a REAL skill with
    # both provider adapters on disk (config/model-mapping.json capability is
    # exercised indirectly by every -DryRun assertion below).
    assert set(FAMILIES) == {"planning", "review", "build-orchestration", "session"}
    for skill in SKILLS:
        paths = sc.adapter_paths(skill)
        assert paths["claude"].is_file(), f"{skill}: missing providers/claude.md"
        assert paths["gpt"].is_file(), f"{skill}: missing providers/gpt.md"
        assert (sc.SKILLS_ROOT / skill / "core.md").is_file(), f"{skill}: missing core.md"


# --------------------------------------------------------------------------- #
# 1. Dry-run adapter RESOLUTION (NOT provider selection -- see module docstring)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("skill", SKILLS)
def test_claude_dry_run_resolves_claude_adapter(skill):
    """Proves the router's Resolve-SkillEntryPoint finds the Claude adapter file
    for this skill. Does NOT prove provider selection (see module docstring) --
    -DryRun prints the GPT entry point too, unconditionally."""
    row = sc.claude_dry_run(skill)
    assert row["exit_code"] == 0, row["raw"].stderr
    expected = sc.adapter_paths(skill)["claude"].resolve()
    assert row["adapter"], f"no Claude entry point resolved for {skill}:\n{row['raw'].stdout}"
    assert Path(row["adapter"]).resolve() == expected


@pytest.mark.parametrize("skill", SKILLS)
def test_gpt_dry_run_resolves_gpt_adapter(skill):
    """Proves the router's Resolve-SkillEntryPoint finds the GPT adapter file
    for this skill. Does NOT prove provider selection (see module docstring) --
    -DryRun prints the Claude entry point too, unconditionally."""
    row = sc.gpt_dry_run(skill)
    assert row["exit_code"] == 0, row["raw"].stderr
    expected = sc.adapter_paths(skill)["gpt"].resolve()
    assert row["adapter"], f"no GPT entry point resolved for {skill}:\n{row['raw'].stdout}"
    assert Path(row["adapter"]).resolve() == expected


# --------------------------------------------------------------------------- #
# 2. Provider SELECTION, proven from a provider-CONDITIONED signal
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("skill", SKILLS)
def test_claude_live_invocation_is_provider_conditioned(skill):
    """Real (non-dry-run) -Provider claude run. Asserts on the router's own
    dispatch lines, which are conditioned on Claude ACTUALLY being selected
    ('Routing to Claude for skill ...', 'Claude invocation succeeded ...') and
    on the GPT-only substrings ('via copilot' / 'via openai-direct') being
    absent -- a run that dispatched to GPT instead would fail this."""
    row = sc.claude_live_run(skill)
    assert row["exit_code"] == 0, row["raw"].stdout + row["raw"].stderr
    assert row["verdict"] == "PASS", row["raw"].stdout
    expected = sc.adapter_paths(skill)["claude"].resolve()
    assert row["adapter"], f"no 'Claude entry point:' line found for {skill}:\n{row['raw'].stdout}"
    assert Path(row["adapter"]).resolve() == expected


@pytest.mark.parametrize("skill", SKILLS)
def test_copilot_gpt_invocation_succeeds_without_openai_api_key(skill):
    """Real (non-dry-run) -Provider gpt run with OPENAI_API_KEY unset. Asserts
    the provider-conditioned 'via copilot' success line and that 'Routing to
    Claude' never appears (no fallback occurred -- genuine GPT selection, not
    a masked fallback)."""
    row = sc.gpt_copilot_live(skill)
    assert row["exit_code"] == 0, row["raw"].stderr
    assert row["verdict"] == "PASS", row["raw"].stdout
    assert row["mock_received"], "Copilot mock server was never contacted"


@pytest.mark.parametrize("skill", SKILLS)
def test_copilot_invocation_transmits_the_selected_adapter_content(skill):
    # Stronger-than-dry-run evidence: the LIVE request body actually carries the
    # selected GPT adapter's content (not just that the router says it would).
    # The body is a JSON payload (Invoke-GPTModel ConvertTo-Json's the adapter
    # text into the "input" field), so it must be JSON-decoded before a
    # substring check -- a raw-bytes containment check would always fail
    # because JSON escapes newlines/quotes in the adapter's markdown text.
    row = sc.gpt_copilot_live(skill)
    assert row["exit_code"] == 0, row["raw"].stderr
    # newline="" disables Python's universal-newline translation: the adapter
    # files are CRLF on disk, and PowerShell's `Get-Content -Raw` (used by
    # Invoke-GPTModel) preserves the literal CRLF bytes into the JSON "input"
    # field -- reading with translation on would silently strip every '\r' and
    # make this containment check fail on every call.
    adapter_text = sc.adapter_paths(skill)["gpt"].read_text(encoding="utf-8", newline="")
    decoded_inputs = []
    for entry in row["mock_received"]:
        if not entry["body"]:
            continue
        try:
            payload = json.loads(entry["body"].decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(payload, dict) and "input" in payload:
            decoded_inputs.append(payload["input"])
    assert decoded_inputs, f"{skill}: no JSON request body with an 'input' field was captured"
    assert any(adapter_text in decoded for decoded in decoded_inputs), (
        f"{skill}: selected GPT adapter content was not found in any transmitted request 'input'"
    )


# --------------------------------------------------------------------------- #
# 3. Shared-core parity: both provider adapters reference the SAME core.md
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("skill", SKILLS)
def test_claude_and_gpt_adapters_reference_the_same_canonical_core(skill):
    paths = sc.adapter_paths(skill)
    claude_core = sc.resolved_core_path_from_adapter(paths["claude"])
    gpt_core = sc.resolved_core_path_from_adapter(paths["gpt"])
    canonical = (sc.SKILLS_ROOT / skill / "core.md").resolve()
    assert claude_core == canonical, f"{skill}: claude adapter does not resolve to the canonical core"
    assert gpt_core == canonical, f"{skill}: gpt adapter does not resolve to the canonical core"
    assert canonical.is_file()


def test_core_reference_parsing_detects_decoy_substring_content_drift(tmp_path, monkeypatch):
    """Regression guard for the exact gap a deep review found in an earlier
    draft: resolved_core_path_from_adapter() used to check only for the
    LITERAL substring '../core.md' ANYWHERE in the adapter file, then computed
    the resolved core path POSITIONALLY (adapter_path.parent / '../core.md'),
    ignoring what the adapter actually declared. For the fixed
    skills/<name>/providers/ layout that made the two-adapter comparison
    unreachable dead code -- both positional guesses were always "this
    skill's own core.md". This test builds a throwaway skill whose CLAUDE
    adapter's declared 'Core:' reference points at a DIFFERENT skill's
    core.md, while a decoy '../core.md' substring survives elsewhere (an HTML
    comment) -- exactly the adversarial input that fooled the old
    substring-only gate. The FIXED parser (_extract_declared_core_reference)
    must parse the real 'Core:' value, not the decoy, so canonical_core() must
    raise here (red-on-garbage)."""
    skills_root = tmp_path / "skills"
    victim = skills_root / "victim-skill"
    other = skills_root / "other-skill"
    (victim / "providers").mkdir(parents=True)
    other.mkdir(parents=True)
    (victim / "core.md").write_text("VICTIM CORE", encoding="utf-8")
    (other / "core.md").write_text("OTHER CORE", encoding="utf-8")
    # The decoy: a '../core.md' substring that is NOT the declared Core: value
    # and is NOT a markdown link target -- exactly what a substring-presence
    # check would have accepted.
    (victim / "providers" / "claude.md").write_text(
        "<!-- legacy note, ignore: ../core.md -->\n"
        "Core: ../../other-skill/core.md\n",
        encoding="utf-8",
    )
    (victim / "providers" / "gpt.md").write_text("Core: ../core.md\n", encoding="utf-8")

    monkeypatch.setattr(sc, "SKILLS_ROOT", skills_root)

    claude_adapter = victim / "providers" / "claude.md"
    gpt_adapter = victim / "providers" / "gpt.md"
    claude_core = sc.resolved_core_path_from_adapter(claude_adapter)
    gpt_core = sc.resolved_core_path_from_adapter(gpt_adapter)
    assert claude_core == (other / "core.md").resolve(), (
        "parser did not follow the declared Core: reference to the other skill"
    )
    assert gpt_core == (victim / "core.md").resolve()
    assert claude_core != gpt_core, (
        "the parity check failed to detect adapter-content drift -- it is still "
        "resolving positionally instead of parsing the declared Core: reference"
    )

    with pytest.raises(AssertionError):
        sc.canonical_core("victim-skill")


# --------------------------------------------------------------------------- #
# 4. Bounded one-transition fallback to Claude
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("skill", SKILLS)
def test_gpt_fallback_preserves_one_transition_budget_to_claude(skill):
    row = sc.gpt_fallback_to_claude(skill)
    assert row["exit_code"] == 2, (row["exit_code"], row["raw"].stdout, row["raw"].stderr)
    assert row["verdict"] == "PASS", row["raw"].stdout
    assert "retry_count=1" in row["fallback"]
    assert "success_count=1" in row["fallback"]


# --------------------------------------------------------------------------- #
# 5. Secret redaction with teeth: the sentinel is a REAL credential the router
# receives, not merely asserted absent without ever being supplied.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("skill", SKILLS)
def test_planted_secret_is_redacted_on_copilot_auth_failure(skill):
    """PLANTED_SECRET is wired in as the actual COPILOT_GITHUB_TOKEN the router
    uses for this call (a forced 401 exercises the auth-failure/diagnostic
    path with that value in scope). This assertion FAILS if
    Protect-SecretsInText regresses -- unlike a check that merely asserts a
    value's absence without ever supplying it to the code under test."""
    row = sc.gpt_auth_failure_secret_redaction(skill)
    assert row["exit_code"] == 2, (row["exit_code"], row["raw"].stdout, row["raw"].stderr)
    assert sc.PLANTED_SECRET not in row["raw"].stdout, "planted secret leaked in stdout"
    assert sc.PLANTED_SECRET not in row["raw"].stderr, "planted secret leaked in stderr"
    assert row["verdict"] == "PASS"


# --------------------------------------------------------------------------- #
# Hermeticity meta-test: the real `gh auth token` path is never reached.
# --------------------------------------------------------------------------- #

def test_gh_auth_never_invoked_when_copilot_token_is_supplied(tmp_path):
    """PATH-shims `gh` to a script that leaves a marker file if invoked, then
    runs a representative -DryRun (which calls Get-CopilotToken for its 'Key
    presence' banner on every invocation, dry-run included). Because
    _scenarios.run_router ALWAYS supplies COPILOT_GITHUB_TOKEN explicitly, the
    real `gh auth token` subprocess branch must never be reached -- proving the
    hermeticity claim rather than merely asserting it."""
    marker = tmp_path / "gh-was-invoked.marker"
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir()
    (shim_dir / "gh.cmd").write_text(
        f'@echo off\r\necho INVOKED > "{marker}"\r\necho shim-token\r\n',
        encoding="utf-8",
    )
    path_override = str(shim_dir) + os.pathsep + os.environ.get("PATH", "")

    for skill in SKILLS:
        row = sc.run_router(["-Provider", "gpt", "-Skill", skill, "-DryRun"], path_override=path_override)
        assert row.returncode == 0, row.stderr

    assert not marker.exists(), (
        "the PATH-shimmed `gh` was invoked during a supposedly-hermetic smoke run "
        "-- COPILOT_GITHUB_TOKEN was not honored ahead of the gh-auth fallback"
    )
