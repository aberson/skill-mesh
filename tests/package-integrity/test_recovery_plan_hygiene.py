"""Stable-authority and public-path checks for recovery Step 73."""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_HOME = re.compile(r"[A-Za-z]:[\\/]Users[\\/](?!<)")

AUTHORITY_FILES = (
    "plan.md",
    "AGENTS.md",
    "CLAUDE.md",
    "documentation/skill-mesh-recovery-plan.md",
    "documentation/product-charter.md",
    "documentation/operator-communication-profile.md",
    "documentation/skill-mesh-course-correction-plan.md",
    "documentation/step-4-checkpoint-2026-08-13.md",
    "documentation/step-4-second-opinion-prompt.md",
    "documentation/omnigent-revisit-seed.md",
    "documentation/runbooks/preserve-step-4.md",
)


def read(relative_path):
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_recovery_authority_files_are_public_and_resolve():
    missing = [path for path in AUTHORITY_FILES if not (REPO_ROOT / path).is_file()]
    assert not missing, f"missing recovery authority files: {missing}"

    private_paths = []
    for relative_path in AUTHORITY_FILES:
        for line_number, line in enumerate(read(relative_path).splitlines(), 1):
            if PRIVATE_HOME.search(line):
                private_paths.append(f"{relative_path}:{line_number}")
    assert not private_paths, f"private home paths in recovery authority: {private_paths}"


def test_root_adapters_are_thin_and_point_to_stable_authority():
    agents = read("AGENTS.md")
    claude = read("CLAUDE.md")

    assert len(agents.splitlines()) <= 8
    assert "`CLAUDE.md`" in agents
    assert "`plan.md`" in agents
    assert "does not enumerate skills" in agents

    current = claude.split("## Current authority", 1)[1].split(
        "## Environment requirements", 1
    )[0]
    for required in (
        "`plan.md`",
        "`documentation/skill-mesh-recovery-plan.md`",
        "`documentation/product-charter.md`",
        "Do not infer current execution state",
    ):
        assert required in current
    assert "BUILD-READY" not in current


def test_parked_provider_plan_is_not_advertised_as_active():
    provider_plan = read("documentation/provider-expansion-plan.md")
    provider_header = "\n".join(provider_plan.splitlines()[:15])
    claude = read("CLAUDE.md")
    plan = read("plan.md")

    assert "**Status:** PARKED" in provider_header
    assert "not an active execution authority" in provider_header
    assert "Do not infer current execution state" in claude
    assert "Provider expansion | PARKED" in plan
