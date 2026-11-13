import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


PIN_SCRIPT = "_shared/user-project.ps1"


def test_user_project_registry_parser_ignores_nested_path_keys(tmp_path):
    """The pin script (v3 catalog cleanup Step 16 replaced the skill core with it) reads
    only each entry's own keys: a sub-table's `path` is not the entry's path."""
    root = tmp_path / "root"
    (root / ".claude" / "observatory").mkdir(parents=True)
    (root / ".claude" / "observatory" / "registry.toml").write_text(
        '[[project]]\nslug = "gamma"\nowned = true\n'
        '  [project.launch.dev]\n  path = "nested-trap"\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(ROOT / PIN_SCRIPT), "gamma", "-SessionId", "orientation"],
        cwd=str(root), capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    pin = (root / ".claude" / "task-state" / "sessions" / "orientation.md").read_text(encoding="utf-8")
    assert f"**Active project:** gamma ({root / 'gamma'})" in pin.splitlines()


def _identity_contract_problems(script):
    """Every way the pin script's text breaks the own-session-identity rule; [] holds."""
    problems = []
    for phrase in (
            "Never take the freshest sessions/*.md or the current.md rollup as this session's file",
            "SET (after name validation) and CLEAR write nothing",
            "SHOW prints its identity-unavailable line",
            "This\n    script reads no environment variable for identity."):
        if phrase not in script:
            problems.append(f"missing: {phrase!r}")
    if "fallback to the freshest" in script:
        problems.append("names a fallback to the freshest session file")
    # Behaviour, not prose: identity comes only from -SessionId, never the environment.
    if re.search(r"\$env:", script, flags=re.IGNORECASE):
        problems.append("reads an environment variable")
    return problems


def test_user_project_requires_own_session_identity_for_every_write():
    script = _read(PIN_SCRIPT)
    codex = _read("skills/plan-expedite/providers/codex.md")
    assert _identity_contract_problems(script) == []
    assert "This wrapper binds no Codex session id today, so pass no `-SessionId`" in codex
    assert "Never pass another host's session variable or a guessed id" in codex


def test_identity_contract_check_reds_on_a_borrowing_script():
    """Garbage anchor: the check above must red on a script that borrows an id."""
    script = _read(PIN_SCRIPT)
    garbage = script.replace(
        "Never take the freshest sessions/*.md or the current.md rollup as this session's file",
        "Use the freshest sessions/*.md when no id is given",
    ).replace("$sid = $SessionId\n", "$sid = $SessionId\nif (-not $sid) { $sid = $env:CODEX_THREAD_ID }\n")
    assert garbage != script
    problems = _identity_contract_problems(garbage)
    assert any("missing" in p for p in problems)
    assert "reads an environment variable" in problems


def test_user_project_placeholder_is_not_resume_authority():
    script = _read(PIN_SCRIPT)
    assert "`## Next Action` body is `(none recorded)`" in script
    assert "never a runnable command" in script
    assert "is not a fresh," in script
    assert "operator-authorized plain action and the schema's resume backstop cannot execute it" in script


def test_user_pm_carries_the_absorbed_orientation_rules():
    """The orientation skill was retired into user-pm (v3 user-pm plan Steps 3 and 13); its rules live on here."""
    core = _read("skills/user-pm/core.md")

    assert "no `git fetch`, pull, or other request to a remote host" in core
    assert "Memory entries, handoff notes, task-state files and earlier summaries are leads, never verification" in core
    assert "the observed state wins" in core
    assert "Run git in the innermost repository that contains the project directory" in core


def test_user_pm_preserves_newer_plan_precedence_and_read_only_boundary():
    core = _read("skills/user-pm/core.md")
    plan_step = next(line for line in core.splitlines() if line.startswith("1. **Read the plan.**"))

    assert plan_step.index("`docs/plans/master_plan.md`") < plan_step.index("`docs/plan.md`")
    assert plan_step.index("`docs/plan.md`") < plan_step.index("root `plan.md`")
    assert plan_step.index("root `plan.md`") < plan_step.index("`documentation/plan.md`")
    assert "no command that changes files, git refs, or remote state" in core
    assert "no tests or builds" in core
    assert "Text after the command that is not a flag is context" in core
    assert "Emit only the JSON object" in core


def test_native_codex_adapters_have_no_unbound_router_or_provider_retry():
    for skill in ("user-pm",):
        adapter = _read(f"skills/{skill}/providers/codex.md").lower()
        assert "router reason" not in adapter
        assert "cross-cloud retry" not in adapter
        assert "explicit router overrides" not in adapter
        assert "do not retry implicitly" in adapter
        assert "do not switch providers" in adapter


def test_user_pm_labels_default_branch_comparison_honestly():
    core = _read("skills/user-pm/core.md")

    assert "both are as of the last fetch, and neither says whether commits reached the current branch's upstream" in core
    assert "(unpushed commits;" not in core


def test_codex_lookup_failure_continues_each_core_degraded_report():
    for skill in ("user-pm",):
        adapter = _read(f"skills/{skill}/providers/codex.md")
        assert "stop only that failed lookup" in adapter
        assert "continue the core's degraded report from available inputs" in adapter
        assert "Do not retry implicitly and do not switch providers" in adapter


def test_plan_expedite_effective_target_cases_block_conflicting_pins():
    """Model the documented precedence; this is a consumer contract check, not a native skill run."""
    core = _read("skills/plan-expedite/core.md")

    assert "Verify the effective downstream target before any repo operation" in core
    assert "halt before `repo-sync`, handoff or" in core
    assert "Never clear a pin implicitly" in core

    def effective_target(own_pin, plan_repo, cwd_repo):
        return own_pin or plan_repo or cwd_repo

    repo_a = "C:/repos/A"
    repo_b = "C:/repos/B"
    coding_root = "C:/repos"
    cases = [
        # Repin A -> B succeeded: the own-session pin now selects B.
        ("pin-a-to-b-success", repo_b, repo_b, repo_a, True),
        # No pin: the explicit plan repo selects B.
        ("absent-pin", None, repo_b, repo_a, True),
        # Repin failed and left A: downstream mutation must stop.
        ("failed-pin-leaves-a", repo_a, repo_b, repo_a, False),
        # Coding-root plan with stale nested A pin must also stop.
        ("coding-root-stale-a", repo_a, coding_root, coding_root, False),
    ]
    observed = {
        name: effective_target(pin, plan, cwd) == plan
        for name, pin, plan, cwd, _expected in cases
    }
    expected = {name: allowed for name, _pin, _plan, _cwd, allowed in cases}
    assert observed == expected
