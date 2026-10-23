import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_user_project_registry_parser_ignores_nested_path_keys(tmp_path):
    core = _read("skills/user-project/core.md")
    blocks = re.findall(r"```powershell\n(.*?)```", core, flags=re.DOTALL)
    parser = next(block for block in blocks if "$entries = foreach" in block)
    registry = tmp_path / "registry.toml"
    registry.write_text(
        '[[project]]\nslug = "gamma"\nowned = true\n'
        '  [project.launch.dev]\n  path = "nested-trap"\n',
        encoding="utf-8",
    )
    script = (
        f"$registry = '{str(registry).replace(chr(39), chr(39) * 2)}'\n"
        "$name = 'gamma'\n"
        + parser
        + '\nWrite-Output "$($match.slug)|$($match.path)"\n'
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", "-"],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "gamma|gamma"


def test_user_project_requires_own_session_identity_for_every_write():
    core = _read("skills/user-project/core.md")
    codex = _read("skills/user-project/providers/codex.md")

    assert "**Never** take the freshest `sessions/*.md` or the `current.md` rollup as this session's file" in core
    assert "SET (after name validation) and CLEAR write nothing" in core
    assert "SHOW prints its identity-unavailable line" in core
    assert "Never use the freshest `sessions/*.md` or the `current.md` rollup" in codex
    assert "write nothing, and stop" in codex
    assert "fallback to the freshest" not in core
    assert "fallback to the freshest" not in codex


def test_user_project_placeholder_is_not_resume_authority():
    core = _read("skills/user-project/core.md")
    assert "whose body is `(none recorded)`" in core
    assert "never a runnable command" in core
    assert "it is not a fresh," in core
    assert "operator-authorized plain action and the schema's resume backstop cannot execute it" in core


def test_user_orient_full_mode_uses_read_only_local_evidence():
    core = _read("skills/user-orient/core.md")

    assert "An explicit `/user-orient` runs the full orientation" in core
    assert "`/user-orient --quick` runs quick mode" in core
    assert "no `git fetch`, pull, or request to a remote host" in core
    assert "When the thread edited files in more than one repository" in core
    assert "Memory entries, handoff notes, task-state files, and earlier summaries are leads, not verification" in core
    assert "Skip Step 1 entirely — fire no tool calls" in core


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
    for skill in ("user-project", "user-orient", "user-pm"):
        adapter = _read(f"skills/{skill}/providers/codex.md").lower()
        assert "router reason" not in adapter
        assert "cross-cloud retry" not in adapter
        assert "explicit router overrides" not in adapter
        assert "do not retry implicitly" in adapter
        assert "do not switch providers" in adapter


def test_user_orient_labels_default_branch_comparison_honestly():
    core = _read("skills/user-orient/core.md")

    assert "commits ahead of the locally known default-branch ref" in core
    assert "does not say whether they were pushed to the current branch's upstream" in core
    assert "(unpushed commits;" not in core


def test_codex_lookup_failure_continues_each_core_degraded_report():
    for skill in ("user-orient", "user-pm"):
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
