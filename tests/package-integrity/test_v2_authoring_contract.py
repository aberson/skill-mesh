"""Focused contract checks for the Skill Mesh v2 authoring trio.

These skills primarily implement behavior in prose.  The checks below pin the
safety and handoff clauses whose omission would change observable behavior.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _core(skill: str) -> str:
    return (ROOT / "skills" / skill / "core.md").read_text(encoding="utf-8")


def _codex(skill: str) -> str:
    return (
        ROOT / "skills" / skill / "providers" / "codex.md"
    ).read_text(encoding="utf-8")


def test_user_brainstorm_resumes_without_overwriting_existing_work() -> None:
    core = _core("user-brainstorm")

    assert "Every write is create-only" in core
    assert "run Step 7 for the missing files only" in core
    assert "sub-directories and hidden entries included" in core
    assert "another writer produced the index" in core
    assert "finish with the normal end report without offering a new path" in core
    assert "retry that single file once" in core
    assert "only after the original arm has terminated" in core
    assert "report that file as pending and assign no second writer" in core


def test_user_learn_preflights_before_fanout_and_rechecks_real_outputs() -> None:
    core = _core("user-learn")
    codex = _codex("user-learn")

    hashes = core.index("Record SHA-256 hashes")
    sync = core.index("uv sync --project <root> --locked --inexact", hashes)
    dispatch = core.index("One background sub-agent", sync)
    assert hashes < sync < dispatch

    assert "uses the Knowledge-base / mentoring template, including its BOUNDARY" in core
    assert "Resolve `<ABS-ROOT>` as the absolute output project root" in core
    assert "whether the re-hashed `pyproject.toml` and `uv.lock` are unchanged or changed" in core
    assert "your own `NN`-unique temp files" in core
    assert "`gpt-5.6-sol` at medium effort" in codex
    assert "never let those arms inherit the coordinator model" in codex


def test_user_lavishify_keeps_egress_loopback_and_issue_writes_bounded() -> None:
    core = _core("user-lavishify")
    codex = _codex("user-lavishify")

    for guard in (
        "LAVISH_AXI_TELEMETRY=0",
        "Never run `lavish-axi share`",
        "Never run `lavish-axi setup hooks`",
        "no tunnel, relay or port-forward",
    ):
        assert guard in core

    assert "resolve the target once" in core
    assert "normalized absolute paths; separator- and case-insensitive on Windows" in core
    assert "either a matching `repo_url` names the target" in core
    assert "never rely on the tool's default repository" in core
    assert "not the checked target (<owner/name>)" in core
    assert "never run `lavish-axi setup hooks`" in codex


def test_native_codex_failure_mapping_uses_core_semantics_without_router_failover() -> None:
    adapters = {
        skill: _codex(skill)
        for skill in ("user-brainstorm", "user-learn", "user-lavishify")
    }

    for skill, adapter in adapters.items():
        assert "Native Codex has no router or cross-cloud retry" in adapter, skill
        assert "router reason code" not in adapter, skill
        assert "shared cross-cloud retry allowance" not in adapter, skill

    assert "assign no second writer" in adapters["user-brainstorm"]
    assert "a still-running or unknown arm receives no second writer" in adapters["user-learn"]
    assert "follow the core's held-state rule" in adapters["user-lavishify"]
    assert "this is not transport failover" in adapters["user-lavishify"]
