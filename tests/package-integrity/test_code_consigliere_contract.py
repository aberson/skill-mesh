"""Focused contract checks for the portable code-consigliere front door."""

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "code-consigliere"
BUILD = REPO_ROOT / "tools" / "build-distributions.ps1"


def _read(path):
    return path.read_text(encoding="utf-8")


def test_canonical_front_door_carries_the_attended_boundary_and_helper_fallback():
    core = _read(SKILL_ROOT / "core.md")
    for required in (
        "Invocation: `/code-consigliere [target]`",
        "Init -> Discuss -> Signoff -> Implement",
        "recorded-rationale",
        "observed-behavior",
        "unknown-history",
        "CODE_CONSIGLIERE_HOME",
        "docs/plans/seeds/",
        "No application edit is allowed without agreed signoff",
        "Measure current performance",
        "investigate indirect invocation",
        "<repo>/_shared/consigliere-records.md",
    ):
        assert required in core, required
    private_prefixes = ("C:" + "/Users/", "C:" + "\\Users\\")
    assert not any(prefix in core for prefix in private_prefixes)


def test_all_three_adapters_are_thin_and_load_the_same_core():
    for provider in ("claude", "gpt", "codex"):
        text = _read(SKILL_ROOT / "providers" / f"{provider}.md")
        assert "[../core.md](../core.md)" in text, provider
        assert "Load the core in full" in text, provider
        assert "Never\nsimulate persistent collection" in text or (
            "persistent collection" in text and "simulate" in text
        ), provider


def test_all_three_emitted_front_doors_are_standalone_and_references_resolve(tmp_path):
    result = subprocess.run(
        ["powershell", "-NonInteractive", "-File", str(BUILD),
         "-OutputDir", str(tmp_path), "-Provider", "all"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    for provider in ("claude", "gpt", "codex"):
        profile = tmp_path / provider
        front = profile / "code-consigliere" / "SKILL.md"
        assert front.is_file(), f"{provider}: missing emitted front door"
        launcher = _read(front)
        assert "core.md" in launcher and "Load the core in full" in launcher, provider
        emitted_core = profile / "code-consigliere" / "core.md"
        assert emitted_core.is_file(), f"{provider}: missing emitted core"
        text = _read(emitted_core)
        assert "/code-consigliere [target]" in text, provider
        assert "Init -> Discuss -> Signoff -> Implement" in text, provider
        assert "../_shared/consigliere-records.md" in text, provider
        records = profile / "_shared" / "consigliere-records.md"
        assert records.is_file(), f"{provider}: shared record contract was not emitted"
        schema = _read(records)
        for kind in ("`request`", "`signoff`", "`seed-receipt`", "`wiki-revision`"):
            assert kind in schema, f"{provider}: {kind} missing from record contract"

