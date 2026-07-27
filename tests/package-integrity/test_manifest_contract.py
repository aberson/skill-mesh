"""Package-integrity contract gate for the skill-mesh neutral package (Step 33).

Validates config/skill-manifest.json against a committed authoritative inventory
(expected_inventory.json) plus the documented command contract in
documentation/architecture.md.

Design:
- The public package tests depend on NO private/legacy source. All expected truth
  is committed in tests/package-integrity/expected_inventory.json.
- An optional migration-source verification test re-checks the manifest's legacy
  paths against the real READ-ONLY source, and SKIPS clearly when that source is
  not present (resolved only from SKILL_MESH_LEGACY_SOURCE; never a private
  absolute default).

Runnable via pytest (`python -m pytest tests/package-integrity`) or standalone
(`python tests/package-integrity/test_manifest_contract.py`).
"""

import json
import os
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"
FIXTURE_PATH = Path(__file__).resolve().parent / "expected_inventory.json"
ARCH_PATH = REPO_ROOT / "documentation" / "architecture.md"

CAPABILITY_VOCAB = {"filesystem", "sub-agent", "vision"}
KEBAB = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def load_manifest():
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_fixture():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_arch():
    return ARCH_PATH.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Schema / structure
# --------------------------------------------------------------------------- #

def test_manifest_and_fixture_exist_and_parse():
    assert MANIFEST_PATH.is_file(), f"missing manifest: {MANIFEST_PATH}"
    assert FIXTURE_PATH.is_file(), f"missing fixture: {FIXTURE_PATH}"
    m = load_manifest()
    assert m["schema_version"] == 1
    assert isinstance(m["skills"], list)


def test_capability_vocabulary_declared():
    assert set(load_manifest()["capability_vocabulary"]) == CAPABILITY_VOCAB


def test_capability_semantics_documented():
    sem = load_manifest()["capability_semantics"]
    assert set(sem.keys()) == CAPABILITY_VOCAB
    for key, text in sem.items():
        assert isinstance(text, str) and len(text) > 20, key
    # sub-agent semantics must distinguish isolated agents from named-skill dispatch.
    assert "named-skill dispatch" in sem["sub-agent"].lower()


def test_names_unique_and_kebab():
    names = [s["name"] for s in load_manifest()["skills"]]
    assert len(names) == len(set(names)), "duplicate skill names"
    for n in names:
        assert KEBAB.match(n), f"non-kebab name: {n}"


# --------------------------------------------------------------------------- #
# Exact inventory vs committed fixture
# --------------------------------------------------------------------------- #

def test_counts_match_fixture_and_array():
    m = load_manifest()
    fx = load_fixture()
    skills = m["skills"]
    derived = {
        "total": len(skills),
        "portable": sum(1 for s in skills if s["status"] == "portable"),
        "provider_native": sum(1 for s in skills if s["status"] == "provider-native"),
        "local_capable": sum(1 for s in skills if s.get("local_capable")),
        "sub_agent": sum(1 for s in skills if "sub-agent" in s["capabilities"]),
        "vision": sum(1 for s in skills if "vision" in s["capabilities"]),
        "filesystem": sum(1 for s in skills if "filesystem" in s["capabilities"]),
    }
    assert m["counts"] == derived, (m["counts"], derived)
    assert fx["counts"] == derived, (fx["counts"], derived)
    # spelled-out expectations
    assert derived["total"] == 50
    assert derived["portable"] == 47
    assert derived["provider_native"] == 3
    assert derived["local_capable"] == 24
    assert derived["sub_agent"] == 16
    assert derived["vision"] == 2
    assert derived["filesystem"] == 50


def test_exact_skill_names_and_statuses():
    m = load_manifest()
    fx = load_fixture()
    by_name = {s["name"]: s for s in m["skills"]}
    expected_portable = set(fx["portable"])
    expected_native = set(fx["provider_native"])
    assert set(by_name) == expected_portable | expected_native
    assert len(expected_portable & expected_native) == 0
    for n in expected_portable:
        assert by_name[n]["status"] == "portable", n
    for n in expected_native:
        assert by_name[n]["status"] == "provider-native", n


def test_exact_local_capable_set():
    m = load_manifest()
    fx = load_fixture()
    local = {s["name"] for s in m["skills"] if s.get("local_capable")}
    assert local == set(fx["local_capable"])


def test_exact_sub_agent_set():
    m = load_manifest()
    fx = load_fixture()
    sub = {s["name"] for s in m["skills"] if "sub-agent" in s["capabilities"]}
    assert sub == set(fx["sub_agent"])


def test_exact_vision_set():
    m = load_manifest()
    fx = load_fixture()
    vis = {s["name"] for s in m["skills"] if "vision" in s["capabilities"]}
    assert vis == set(fx["vision"])


def test_manifest_matches_fixture_per_skill():
    m = {s["name"]: s for s in load_manifest()["skills"]}
    fx = {s["name"]: s for s in load_fixture()["skills"]}
    assert set(m) == set(fx)
    for name, exp in fx.items():
        got = m[name]
        assert got["status"] == exp["status"], name
        assert got["local_capable"] == exp["local_capable"], name
        assert got["capabilities"] == exp["capabilities"], name
        assert got["migration"] == exp["migration"], name
        assert got["support_assets"] == exp["support_assets"], name


# --------------------------------------------------------------------------- #
# Path / status truth
# --------------------------------------------------------------------------- #

def test_status_values_valid():
    for s in load_manifest()["skills"]:
        assert s["status"] in {"portable", "provider-native"}, s["name"]


def test_portable_skill_truth():
    for s in load_manifest()["skills"]:
        if s["status"] != "portable":
            continue
        name = s["name"]
        assert s["core"] == f"skills/{name}/core.md", name
        prov = s["providers"]
        assert set(prov.keys()) == {"claude", "gpt"}, name
        assert prov["claude"] == f"skills/{name}/providers/claude.md", name
        assert prov["gpt"] == f"skills/{name}/providers/gpt.md", name


def test_provider_native_skill_truth():
    for s in load_manifest()["skills"]:
        if s["status"] != "provider-native":
            continue
        name = s["name"]
        assert s["core"] is None, name
        prov = s["providers"]
        assert set(prov.keys()) == {"claude"}, name
        assert prov["claude"] == f"skills/{name}/providers/claude.md", name
        assert "gpt" not in prov, name


def test_paths_scoped_to_skill_dir():
    for s in load_manifest()["skills"]:
        name = s["name"]
        if s["core"] is not None:
            assert s["core"].startswith(f"skills/{name}/"), name
        for role, path in s["providers"].items():
            assert path.startswith(f"skills/{name}/providers/"), (name, role)
            assert ".." not in path, (name, role)


def test_capabilities_within_vocabulary():
    for s in load_manifest()["skills"]:
        caps = s["capabilities"]
        assert "filesystem" in caps, s["name"]
        assert set(caps) <= CAPABILITY_VOCAB, s["name"]
        assert len(caps) == len(set(caps)), f"dup capabilities: {s['name']}"


def test_vision_or_subagent_implies_not_local():
    for s in load_manifest()["skills"]:
        caps = set(s["capabilities"])
        if caps & {"vision", "sub-agent"}:
            assert not s.get("local_capable"), (
                f"{s['name']} declares {caps & {'vision', 'sub-agent'}} "
                "but is local_capable"
            )


# --------------------------------------------------------------------------- #
# Migration launcher / adapter convention
# --------------------------------------------------------------------------- #

def test_migration_launcher_adapter_convention():
    for s in load_manifest()["skills"]:
        name = s["name"]
        mig = s["migration"]
        assert set(mig.keys()) == {
            "legacy_core", "legacy_claude_launcher",
            "legacy_claude_adapter", "legacy_gpt",
        }, name
        if s["status"] == "portable":
            assert mig["legacy_core"] == f".claude/skills-gpt/{name}/SKILL-core.md", name
            assert mig["legacy_claude_launcher"] == f".claude/skills/{name}/SKILL.md", name
            assert mig["legacy_claude_adapter"] == f".claude/skills/{name}/SKILL-claude.md", name
            assert mig["legacy_gpt"] == f".claude/skills-gpt/{name}/SKILL-gpt.md", name
        else:  # provider-native: SKILL.md is the substantive adapter, no launcher
            assert mig["legacy_core"] is None, name
            assert mig["legacy_claude_launcher"] is None, name
            assert mig["legacy_claude_adapter"] == f".claude/skills/{name}/SKILL.md", name
            assert mig["legacy_gpt"] is None, name


def test_migration_paths_are_coding_root_relative():
    for s in load_manifest()["skills"]:
        for key in ("legacy_core", "legacy_claude_launcher",
                    "legacy_claude_adapter", "legacy_gpt"):
            val = s["migration"][key]
            if val is not None:
                assert val.startswith(".claude/"), (s["name"], key, val)
                assert not re.match(r"^[A-Za-z]:\\", val), (s["name"], key, val)


# --------------------------------------------------------------------------- #
# Support assets
# --------------------------------------------------------------------------- #

def test_skill_support_assets_shape():
    for s in load_manifest()["skills"]:
        name = s["name"]
        assert isinstance(s["support_assets"], list), name
        for a in s["support_assets"]:
            assert set(a.keys()) == {"source", "dest"}, (name, a)
            assert a["source"].startswith(".claude/"), (name, a)
            assert a["dest"].startswith(f"skills/{name}/"), (name, a)
            assert ".." not in a["dest"], (name, a)


def test_known_skill_local_assets_present():
    by_name = {s["name"]: s for s in load_manifest()["skills"]}
    dests = {n: {a["dest"] for a in s["support_assets"]}
             for n, s in by_name.items()}
    # a few evidence-anchored assets that must be captured
    assert "skills/goblin-do/goblin_do.workflow.js" in dests["goblin-do"]
    assert "skills/judge-motion/package.json" in dests["judge-motion"]
    assert "skills/judge-motion/scripts/" in dests["judge-motion"]
    assert "skills/build-step/scripts/" in dests["build-step"]
    assert "skills/tier-offload/sample-offload-config.json" in dests["tier-offload"]
    assert "skills/judge-ui/calibration-notes.md" in dests["judge-ui"]  # from skills-gpt tree


def test_global_support_assets_present():
    m = load_manifest()
    fx = load_fixture()
    ga = m["global_support_assets"]
    assert ga == fx["global_support_assets"]
    sources = {g["source"] for g in ga}
    assert ".claude/lib/skill-router.ps1" in sources
    assert ".claude/lib/telemetry/" in sources
    assert ".claude/lib/calibration/" in sources
    assert ".claude/references/model-mapping.md" in sources
    assert ".claude/references/model-tier-map.json" in sources
    assert ".claude/skills/_shared/" in sources
    assert "documentation/multi-model/" in sources  # coding-root-relative, not under .claude
    for g in ga:
        assert set(g.keys()) == {"source", "dest", "note"}, g


# --------------------------------------------------------------------------- #
# Host metadata sources (for Step 37)
# --------------------------------------------------------------------------- #

def test_host_metadata_sources_contract():
    hm = load_manifest()["host_metadata_sources"]
    claude_vars = {mk["var"] for mk in hm["claude"]["markers"]}
    gpt_vars = {mk["var"] for mk in hm["gpt"]["markers"]}
    assert "CLAUDECODE" in claude_vars
    assert "CLAUDE_CODE_ENTRYPOINT" in claude_vars
    assert "COPILOT_CLI" in gpt_vars
    assert "COPILOT_AGENT_SESSION_ID" in gpt_vars
    # credentials are explicitly NOT host-identity sources
    excluded = set(hm["excluded_non_identity"])
    assert {"ANTHROPIC_API_KEY", "OPENAI_API_KEY",
            "CLAUDE_CODE_OAUTH_TOKEN"} <= excluded
    assert claude_vars.isdisjoint(excluded)
    assert gpt_vars.isdisjoint(excluded)
    # precedence covers select / ambiguous / unset
    prec = " ".join(hm["precedence"]).lower()
    assert "ambiguous" in prec and "exit 2" in prec
    assert "neither" in prec or "unset" in prec


# --------------------------------------------------------------------------- #
# Documentation command contract (normalized, portable)
# --------------------------------------------------------------------------- #

def test_architecture_command_contract_normalized():
    text = load_arch()
    required_lines = [
        r"python -m pytest tests\package-integrity",
        r"python -m pytest tests\calibration",
        r"python -m pytest $env:SKILL_MESH_LEGACY_SOURCE\.claude\lib\calibration\test_calibrate.py",
        # Canonical flag names ONLY (-Provider / -Home), never the -Profile /
        # -Destination aliases -- tools/build-distributions.ps1 has NO -Profile
        # alias at all (only -Provider), so a doc that used -Profile here
        # documented a command that fails with "A parameter cannot be found
        # that matches parameter name 'Profile'."
        r"pwsh -File tools\build-distributions.ps1 -Provider claude",
        r"pwsh -File tools\install-skill-mesh.ps1 -Provider claude -Home <host-skills-root>",
    ]
    for line in required_lines:
        assert line in text, f"architecture.md missing normalized command: {line}"


def test_architecture_never_documents_profile_alias_for_build_distributions():
    """tools/build-distributions.ps1's only parameter is -Provider (no -Profile
    alias exists on that script -- -Profile is install-skill-mesh.ps1's alias for
    -Provider). Guards against reintroducing the exact defect this test's sibling
    above was fixed for."""
    text = load_arch()
    assert "build-distributions.ps1 -Profile" not in text


def test_architecture_enumerates_host_metadata_vars():
    text = load_arch()
    for var in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "COPILOT_CLI",
                "COPILOT_AGENT_SESSION_ID"):
        assert var in text, f"architecture.md missing host metadata var: {var}"
    low = text.lower()
    assert "ambiguous" in low and "exit code 2" in low


def test_architecture_lint_typecheck_not_configured():
    text = load_arch().lower()
    assert "not configured" in text
    assert "lint" in text and "typecheck" in text


# --------------------------------------------------------------------------- #
# No absolute private paths in committed docs/config/tests (finding #8)
# --------------------------------------------------------------------------- #

def test_no_absolute_private_paths_committed():
    targets = [
        MANIFEST_PATH,
        FIXTURE_PATH,
        ARCH_PATH,
        Path(__file__).resolve(),
        REPO_ROOT / "documentation" / "providers" / "README.md",
        REPO_ROOT / "documentation" / "providers" / "claude.md",
        REPO_ROOT / "documentation" / "providers" / "gpt.md",
        REPO_ROOT / "tools" / "gen_manifest.py",
    ]
    pat = re.compile(r"[A-Za-z]:\\Users\\")
    for p in targets:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        assert not pat.search(text), f"absolute private path committed in {p}"


# --------------------------------------------------------------------------- #
# Optional migration-source verification (skips if source absent)
# --------------------------------------------------------------------------- #

def _legacy_root():
    root = os.environ.get("SKILL_MESH_LEGACY_SOURCE")
    return Path(root) if root else None


def test_migration_source_files_exist():
    root = _legacy_root()
    if root is None or not (root / ".claude").is_dir():
        pytest.skip("legacy source not present (set SKILL_MESH_LEGACY_SOURCE to verify)")
    m = load_manifest()
    missing = []
    for s in m["skills"]:
        for key in ("legacy_core", "legacy_claude_launcher",
                    "legacy_claude_adapter", "legacy_gpt"):
            val = s["migration"][key]
            if val and not (root / val).exists():
                missing.append(f"{s['name']}:{key} -> {val}")
        for a in s["support_assets"]:
            if not (root / a["source"].rstrip("/")).exists():
                missing.append(f"{s['name']}:asset -> {a['source']}")
    assert not missing, "legacy sources missing:\n" + "\n".join(missing)


def _all_tests():
    return [v for k, v in sorted(globals().items())
            if k.startswith("test_") and callable(v)]


if __name__ == "__main__":
    passed = skipped = 0
    for fn in _all_tests():
        try:
            fn()
            passed += 1
            print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            if e.__class__.__name__ == "Skipped":
                skipped += 1
                print(f"SKIP {fn.__name__}: {e}")
            else:
                raise
    print(f"\n{passed} checks passed, {skipped} skipped")
