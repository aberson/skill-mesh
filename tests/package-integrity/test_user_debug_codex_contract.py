"""Focused fail-closed contract tests for user-debug's Codex adapter."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER = REPO_ROOT / "skills" / "user-debug" / "providers" / "codex.md"
MANIFEST = REPO_ROOT / "config" / "skill-manifest.json"
MAPPING = REPO_ROOT / "config" / "model-mapping.json"
PWSH = shutil.which("powershell")


def _section(text, heading):
    lines = text.splitlines()
    marker = f"## {heading}"
    assert marker in lines, f"missing contract heading: {marker}"
    start = lines.index(marker) + 1
    end = next(
        (i for i in range(start, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def _rows(text):
    rows = {}
    for line in _section(text, "Independent-diagnosis capability contract").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 2 and cells[0].startswith("`"):
            rows[cells[0].strip("`")] = cells[1].lower()
    return rows


REQUIREMENTS = {
    "fresh-context-dispatch": (
        'fork_turns="none"', "runtime host capability", "non-mutating probe",
        "cannot read parent session state", "never infer",
    ),
    "step-2-arm": (
        "parent directly spawns", "fresh sibling", "symptom", "repro instructions",
        "bounded read-only primary-source scope", "excludes", "root-cause hypothesis",
        "task state", "handoff", "session material", "fix design",
        "repro evidence", "diagnosis only", "never as a reuse", "follow-up",
        "child successor",
    ),
    "option-4-arm": (
        "option 1 re-investigation", "separate fresh sibling", "not a reuse",
        "follow-up", "child successor", "no prior diagnosis", "diagnosis comparison",
        "repro evidence", "diagnosis only",
    ),
    "parent-authority": (
        "parent alone", "diagnosis comparison", "fix design", "confirms",
        "do not compare diagnoses", "or mutate the project",
    ),
    "shared-filesystem-tools": (
        "permitted", "not os isolation", "fresh context", "parent authority",
        "unexpected child mutation invalidates", "fails closed",
    ),
    "missing-capability": (
        "ordinary codex cli", "absent, failed, or inconclusive",
        "required_tool_missing", "at step 2", "before any fix design or code change",
        "at that tie-breaker", "never reuse", "follow up",
    ),
}


def _defects(text):
    rows = _rows(text)
    defects = []
    for name, tokens in REQUIREMENTS.items():
        if name not in rows:
            defects.append(f"missing {name}")
            continue
        defects.extend(f"{name} lacks {token!r}" for token in tokens if token not in rows[name])
    for forbidden in ("codex has no isolated fresh-context agent primitive",):
        if forbidden in text.lower():
            defects.append(f"stale unconditional provider claim: {forbidden}")
    return defects


def test_user_debug_codex_contract_is_capability_conditioned_and_fail_closed():
    assert not _defects(ADAPTER.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ('fork_turns="none"', 'fork_turns="all"'),
        ("not a reuse", "a reuse is allowed"),
        ("no prior diagnosis", "the parent diagnosis"),
        ("unexpected child mutation invalidates", "unexpected child mutation is evidence"),
        ("absent, failed, or inconclusive", "successful"),
    ],
)
def test_user_debug_contract_rejects_planted_negative_regressions(old, new):
    text = ADAPTER.read_text(encoding="utf-8")
    assert old in text, f"planted-negative anchor moved: {old!r}"
    assert _defects(text.replace(old, new, 1))


def test_user_debug_manifest_and_router_mapping_require_sub_agents():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = next(skill for skill in manifest["skills"] if skill["name"] == "user-debug")
    assert entry["local_capable"] is False
    assert "sub-agent" in entry["capabilities"]
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    assert mapping["skills"]["user-debug"]["local"] is False


@pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")
def test_explicit_local_user_debug_halts_before_local_request():
    result = subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(REPO_ROOT / "runtime" / "skill-router.ps1"),
         "-Provider", "local", "-Skill", "user-debug"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3, (result.returncode, result.stdout, result.stderr)
    output = (result.stdout + result.stderr).lower()
    assert "not local-capable" in output
    assert "cannot route to code-30b" in output


@pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")
def test_codex_distribution_emits_the_capability_conditioned_user_debug_adapter():
    build = subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(REPO_ROOT / "tools" / "build-distributions.ps1"),
         "-Provider", "codex"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (build.stdout, build.stderr)
    emitted = REPO_ROOT / "dist" / "codex" / "user-debug" / "SKILL.md"
    assert emitted.is_file()
    assert "## Independent-diagnosis capability contract" in emitted.read_text(encoding="utf-8")
    assert "Codex has no isolated fresh-context agent primitive" not in emitted.read_text(encoding="utf-8")
