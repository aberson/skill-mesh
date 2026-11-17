"""Package-integrity contract gate for the skill-mesh neutral package (Step 33).

Validates config/skill-manifest.json against a committed authoritative inventory
(expected_inventory.json) plus the documented command contract in
documentation/architecture.md.

Design:
- The public package tests depend on NO private/legacy source. All expected truth
  is committed in tests/package-integrity/expected_inventory.json.
- Since Step 67 the GENERATOR depends on no external source either, and the last
  section of this file is the gate that holds it there: a regeneration must
  reproduce all three committed artifacts with no environment set, and since Phase
  CL Step 111 it validates all three before replacing any, replaces each one safely,
  and offers a no-write `--check`.

Runnable via pytest (`python -m pytest tests/package-integrity`) or standalone
(`python tests/package-integrity/test_manifest_contract.py`).
"""

import importlib.util
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"
FIXTURE_PATH = Path(__file__).resolve().parent / "expected_inventory.json"
INVENTORY_PATH = REPO_ROOT / "skills" / "inventory.json"
ARCH_PATH = REPO_ROOT / "documentation" / "architecture.md"
GEN_MANIFEST_PATH = REPO_ROOT / "tools" / "gen_manifest.py"

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
        # Per-provider adapter tallies (Phase CP Step 3). Derived from the per-skill
        # `providers` dicts, which is the only place adapter presence is stated.
        "claude": sum(1 for s in skills if "claude" in s["providers"]),
        "gpt": sum(1 for s in skills if "gpt" in s["providers"]),
        "codex": sum(1 for s in skills if "codex" in s["providers"]),
        "local_capable": sum(1 for s in skills if s.get("local_capable")),
        "sub_agent": sum(1 for s in skills if "sub-agent" in s["capabilities"]),
        "vision": sum(1 for s in skills if "vision" in s["capabilities"]),
        "filesystem": sum(1 for s in skills if "filesystem" in s["capabilities"]),
    }
    assert m["counts"] == derived, (m["counts"], derived)
    assert fx["counts"] == derived, (fx["counts"], derived)
    # spelled-out expectations
    assert derived["total"] == 47
    assert derived["portable"] == 45
    assert derived["provider_native"] == 2
    assert derived["claude"] == 47, "every skill carries a Claude adapter"
    # GPT is optional since Phase CL Step 111: skill-crud (Step 113) is the one
    # portable skill born after that, and it ships no gpt.md.
    assert derived["gpt"] == 44, "every portable skill but skill-crud has a gpt adapter"
    # Codex is a REQUIRED provider since Phase CL Step 111
    # (portable_provider_contract.required), so this equals `portable` by
    # construction. A portable skill dir without skills/<name>/providers/codex.md is
    # an incomplete package that gen_manifest.derived_skill_sets() refuses.
    assert derived["codex"] == derived["portable"] == 45
    # user-debug requires independent fresh-context diagnosis arms, so it is no
    # longer eligible for text-only local fallback and joins the sub-agent set.
    # user-uat requires isolated deep assessment and strong final visual review;
    # lesson-harvest requires a fresh strong privacy/disposition reviewer.
    assert derived["local_capable"] == 17
    assert derived["sub_agent"] == 16
    assert derived["vision"] == 1
    assert derived["filesystem"] == 47


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


def test_exact_codex_set():
    """The codex set, pinned against the committed fixture like its siblings.

    Codex is required (decision CL-D4 as amended 2026-11-14), so the set the manifest's
    `providers` dicts imply is exactly the portable set -- and decision CL-D14 says it
    is DERIVED from that set rather than spelled as a second roster.
    """
    m = load_manifest()
    fx = load_fixture()
    codex = {s["name"] for s in m["skills"] if "codex" in s["providers"]}
    assert codex == set(fx["codex"])
    portable = {s["name"] for s in m["skills"] if s["status"] == "portable"}
    assert codex == portable == set(fx["portable"])


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
        assert got["origin"] == exp["origin"], name
        assert got["migration"] == exp["migration"], name
        assert got["support_assets"] == exp["support_assets"], name


# --------------------------------------------------------------------------- #
# Path / status truth
# --------------------------------------------------------------------------- #

def test_status_values_valid():
    for s in load_manifest()["skills"]:
        assert s["status"] in {"portable", "provider-native"}, s["name"]


# The ordered required-provider set (Phase CL Step 111; CL-D4 as amended 2026-11-14
# by operator decision). Spelled here as a pin, and asserted equal to the manifest
# field and the generator constant; the lifecycle guide's section 4 list is held to
# the same value by test_skill_catalog_lifecycle.py.
REQUIRED_PROVIDERS = ["claude", "codex"]


def test_portable_provider_contract_is_the_ordered_required_set():
    m = load_manifest()
    contract = m["portable_provider_contract"]
    assert contract["required"] == REQUIRED_PROVIDERS
    # Every required provider is in the installable vocabulary, and the vocabulary is
    # wider than the set: gpt is declared and is not required.
    assert set(contract["required"]) <= set(m["providers"])
    assert "gpt" in m["providers"] and "gpt" not in contract["required"]
    assert list(_load_gen_manifest().REQUIRED_PROVIDERS) == REQUIRED_PROVIDERS


def test_portable_skill_truth():
    required = load_manifest()["portable_provider_contract"]["required"]
    for s in load_manifest()["skills"]:
        if s["status"] != "portable":
            continue
        name = s["name"]
        assert s["core"] == f"skills/{name}/core.md", name
        prov = s["providers"]
        # Every REQUIRED provider is mandatory -- that set is what "portable" means
        # since Phase CL Step 111. gpt is OPTIONAL: present where its adapter is still
        # authored, absent (no key, never a null) otherwise, and its absence is not
        # drift. Asserted as "the required set, plus at most gpt" rather than an exact
        # set, so an unexpected FOURTH provider key is still caught here.
        assert set(required) <= set(prov.keys()), name
        assert set(prov.keys()) <= set(required) | {"gpt"}, name
        for provider, path in prov.items():
            assert path == f"skills/{name}/providers/{provider}.md", (name, provider)


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
        # Provider-native means CLAUDE-ONLY. A codex adapter on one of these three
        # skills is a contradiction, not an upgrade -- the same reason a gpt adapter is
        # rejected on the line above. tools/gen_manifest.py's derived_skill_sets()
        # raises on the tree-level version of this defect; this is the manifest-level
        # assertion of the same contract, so a hand-edited manifest cannot slip past.
        assert "codex" not in prov, name


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

# Provenance, pinned by name (Phase CL Step 111, decision CL-D8). Measured against
# the coding root's Git history at Step 111: these four were authored directly in
# Skill Mesh, and the legacy paths the manifest used to give them never existed
# except as Skill Mesh's own install output. repo-wrap was a single Claude SKILL.md
# in the workspace tree before Phase CP Step 10 promoted it. Spelled here so a
# provenance change has to state itself in a test, like every other partition.
CANONICAL_ORIGIN = {"code-consigliere", "skill-crud", "user-build-route", "user-dr",
                    "user-fermize"}
SINGLE_FILE_PORTABLE = {"repo-wrap"}


def test_origin_partition_is_pinned():
    records = load_manifest()["skills"]
    assert {s["origin"] for s in records} <= {"legacy-migrated", "canonical"}
    assert {s["name"] for s in records if s["origin"] == "canonical"} == CANONICAL_ORIGIN
    single = {s["name"] for s in records if s["origin"] == "legacy-migrated"
              and s["status"] == "portable" and s["migration"]["legacy_core"] is None}
    assert single == SINGLE_FILE_PORTABLE


def test_migration_launcher_adapter_convention():
    for s in load_manifest()["skills"]:
        name = s["name"]
        mig = s["migration"]
        if s["origin"] == "canonical":
            # Authored in Skill Mesh: no legacy source exists, so there is no block
            # to fill and none is fabricated. Exactly null, not an all-null object.
            assert mig is None, name
            assert s["support_assets"] == [], name
            continue
        assert s["origin"] == "legacy-migrated", name
        assert set(mig.keys()) == {
            "legacy_core", "legacy_claude_launcher",
            "legacy_claude_adapter", "legacy_gpt",
        }, name
        if s["status"] == "portable" and name not in SINGLE_FILE_PORTABLE:
            assert mig["legacy_core"] == f".claude/skills-gpt/{name}/SKILL-core.md", name
            assert mig["legacy_claude_launcher"] == f".claude/skills/{name}/SKILL.md", name
            assert mig["legacy_claude_adapter"] == f".claude/skills/{name}/SKILL-claude.md", name
            assert mig["legacy_gpt"] == f".claude/skills-gpt/{name}/SKILL-gpt.md", name
        else:  # one SKILL.md was the substantive skill: no core, launcher or gpt
            assert mig["legacy_core"] is None, name
            assert mig["legacy_claude_launcher"] is None, name
            assert mig["legacy_claude_adapter"] == f".claude/skills/{name}/SKILL.md", name
            assert mig["legacy_gpt"] is None, name


def test_migration_paths_are_coding_root_relative():
    for s in load_manifest()["skills"]:
        if s["migration"] is None:
            continue
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
    assert "skills/plan-redline/reference-proposal.html" in dests["plan-redline"]
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

# A real Windows home path, either separator. The negative lookahead keeps the
# documented placeholder form (`C:/Users/<user>/...`) legal -- docs are supposed
# to show the shape, and flagging the placeholder would push authors back toward
# writing a real path.
PRIVATE_PATH_RE = re.compile(r"[A-Za-z]:[\\/]Users[\\/](?!<)")

# Files that MUST contain the pattern to do their job. Each needs a reason; a
# path is not exempt because it is inconvenient to fix.
PRIVATE_PATH_EXEMPT = {
    # Implements _scrub_private(); its regexes must spell the path out.
    "tools/gen_skill_tree.py",
    # Red-on-garbage anchors for that scrubber: they assert the detector fires
    # on a real home path, so they must contain one.
    "tests/package-integrity/test_skill_tree.py",
}


def _tracked_text_files():
    """Every git-tracked file PLUS every untracked-but-not-ignored one, minus
    binaries. Enumerated, never hand-listed.

    Same principle as release staging (`git ls-files`, not a denylist): a new
    committed file is covered the moment it is tracked, so the gate cannot go
    quietly false-green on a document nobody remembered to add.

    `--others --exclude-standard` closes an ENUMERATION-TIMING hole that a
    tracked-only sweep leaves open, and which bit this repository for real: a new
    file authored during a change is untracked while the suite runs, so every gate
    built on this helper reports green — and then goes red the moment the file is
    committed, i.e. exactly when the author has stopped looking. A full-suite pass
    before `git add` must actually mean the gates hold after it. Ignored paths stay
    excluded, so local scratch and build output (`dist/`) are still out of scope.
    """
    r = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                       cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    skip_suffix = {".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc", ".zip"}
    for rel in r.stdout.splitlines():
        rel = rel.strip()
        if not rel or rel in PRIVATE_PATH_EXEMPT:
            continue
        p = REPO_ROOT / rel
        if not p.is_file() or p.suffix.lower() in skip_suffix:
            continue
        yield rel, p


@pytest.mark.skipif(not (REPO_ROOT / ".git").exists(),
                    reason="not a git working tree (e.g. release stage)")
def test_no_absolute_private_paths_committed():
    offenders = []
    for rel, p in _tracked_text_files():
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if PRIVATE_PATH_RE.search(line):
                offenders.append(f"{rel}:{i}")
    assert not offenders, (
        "absolute private path committed in: " + ", ".join(offenders[:20])
    )


def test_private_path_gate_reds_on_a_planted_path(tmp_path):
    """Red-on-garbage anchor: the sweep must actually fail on a planted path.

    Without this, a regex or enumeration bug turns the gate above into a
    permanent green that inspects nothing.
    """
    # Built at runtime: this file is itself swept, so it must not contain a
    # literal instance of the pattern under test.
    sep = chr(92)
    planted = tmp_path / "doc.md"
    planted.write_text(f"run it from C:{sep}Users{sep}someone{sep}dev\n", encoding="utf-8")
    hits = [i for i, line in enumerate(planted.read_text(encoding="utf-8").splitlines(), 1)
            if PRIVATE_PATH_RE.search(line)]
    assert hits == [1]
    # ...and stays quiet on the placeholder forms the docs are supposed to use.
    clean = tmp_path / "clean.md"
    clean.write_text(
        f"run it from <workspace>{sep}dev\n"
        "or C:/Users/<user>/AppData/Local/Temp/\n",
        encoding="utf-8")
    assert not PRIVATE_PATH_RE.search(clean.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# No hardcoded default-branch assumption in minted link templates (#87)
# --------------------------------------------------------------------------- #

# A doc link that assumes the repository's default branch. GitHub has defaulted
# new repos to `main` since 2020, so a skill that mints a link naming the old
# default produces links that 404 on essentially every repo it is pointed at --
# and `/build-phase` uses exactly those links to find the step it is executing.
# Both the pattern AND the prose above avoid spelling a branch-bearing link out:
# this file is swept by its own gate, so a literal example here would flag it.
_BRANCH_ASSUMING_LINK_RE = re.compile(r"blob/(?:" + "master" + r"|main)/")


@pytest.mark.skipif(not (REPO_ROOT / ".git").exists(),
                    reason="not a git working tree (e.g. release stage)")
def test_no_hardcoded_default_branch_in_link_templates():
    """Sweep every tracked file for a branch-assuming doc-link template.

    Hardcoding `main` instead of `master` would merely invert the same defect, so
    both are caught; the legal form is the `<default-branch>` placeholder that
    /repo-sync resolves via `gh repo view --json defaultBranchRef`.
    """
    offenders = []
    for rel, p in _tracked_text_files():
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if _BRANCH_ASSUMING_LINK_RE.search(line):
                offenders.append(f"{rel}:{i}")
    assert not offenders, (
        "doc-link template hardcodes a default branch (use the "
        "'<default-branch>' placeholder, resolved via gh): " + ", ".join(offenders[:20])
    )


def test_default_branch_gate_reds_on_a_planted_link(tmp_path):
    """Red-on-garbage anchor: without it, a regex bug makes the sweep a permanent
    green that inspects nothing."""
    planted = tmp_path / "skill.md"
    planted.write_text(
        "see [plan.md](../blob/" + "master" + "/plan.md)\n"
        "and [other](../blob/" + "main" + "/other.md)\n",
        encoding="utf-8")
    hits = [i for i, line in enumerate(planted.read_text(encoding="utf-8").splitlines(), 1)
            if _BRANCH_ASSUMING_LINK_RE.search(line)]
    assert hits == [1, 2], "the gate must catch a hardcoded branch in a link template"
    # ...and stays quiet on the placeholder form the templates are supposed to use.
    clean = tmp_path / "clean.md"
    clean.write_text("see [plan.md](../blob/<default-branch>/plan.md)\n", encoding="utf-8")
    assert not _BRANCH_ASSUMING_LINK_RE.search(clean.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Hermetic regeneration (STEP 67)
# --------------------------------------------------------------------------- #
# What stood here was an OPTIONAL verification that every `migration` and
# `support_assets` path still existed under the READ-ONLY legacy root, skipped unless
# SKILL_MESH_LEGACY_SOURCE was set. It is RETIRED, not loosened: the Step 50 consumer
# cutover overwrote that root with this package's own installed output, so the check
# has no reproducible source left to read. Set the variable today and it reports 47 of
# 50 skills as missing -- a defect that lives in the retired root, not in the manifest.
# A check whose only outcomes are "skipped" and "wrong" is not a gate.
#
# Its replacement asserts the property the manifest actually needs and requires
# nothing external: the generator REPRODUCES both committed artifacts, from this
# repository alone. That is also what makes the manifest auditable again -- before
# Step 67 a regeneration silently rewrote 47 of 50 `support_assets` blocks, feeding
# skill-mesh's own installed output back into skill-mesh's own manifest.
#
# LINE ENDINGS -- `_norm` is load-bearing, not decoration. This repository has no
# .gitattributes and core.autocrlf=true, so ONE git blob is CRLF in a Windows checkout
# and LF in a POSIX one. A raw byte comparison would therefore pass in one clone and
# fail in another, which is exactly how a Step 66 gate went green in a worktree and
# red in main (#112). Both sides are normalized here -- UTF-8 BOM stripped, then
# CRLF/CR -> LF -- the same rule tools/release.ps1 already applies to `dist/`.


def _norm(data: bytes) -> bytes:
    """Strip a UTF-8 BOM, then fold CRLF/CR to LF. Applied to BOTH sides, always."""
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _load_gen_manifest():
    """Import tools/gen_manifest.py under a private module name, so its
    `if __name__ == '__main__'` guard never fires."""
    spec = importlib.util.spec_from_file_location(
        "gen_manifest_hermetic", GEN_MANIFEST_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generator_reads_no_external_source():
    """The hermetic property itself, asserted structurally rather than by reading a
    comment: `build()` takes no source argument, the CLI declares no arguments to
    hand it one, and the module never touches the environment."""
    gm = _load_gen_manifest()
    assert list(inspect.signature(gm.build).parameters) == [], (
        "gen_manifest.build() regained a parameter -- the only thing it ever took was "
        "an external legacy root, which the Step 50 cutover overwrote")
    # The CLI's whole surface is ONE value-less mode switch. `--check` selects
    # compare-instead-of-write; it names no source, so a parser that accepts anything
    # else -- the retired --legacy-source above all -- has regained an input.
    parser = gm.build_parser()
    assert vars(parser.parse_args([])) == {"check": False}
    assert vars(parser.parse_args(["--check"])) == {"check": True}
    for stale in (["--legacy-source", "x"], ["--check", "x"], ["somewhere"]):
        with pytest.raises(SystemExit):
            parser.parse_args(stale)
    src = GEN_MANIFEST_PATH.read_text(encoding="utf-8")
    assert src.count("add_argument(") == 1, (
        "gen_manifest.py's CLI declares a second argument; generation takes no input "
        "beyond this repository")
    # `os` is imported for the safe per-file replacement (fsync + atomic rename);
    # what must never come back is a read of the environment.
    assert not re.search(r"\benviron\b|getenv", src), (
        "gen_manifest.py reads the environment again; the legacy-source variable is "
        "exactly the input this generator no longer has")


def test_build_reproduces_the_committed_manifest():
    gm = _load_gen_manifest()
    manifest, _ = gm.build()
    assert _norm(gm.serialize(manifest).encode("utf-8")) == _norm(MANIFEST_PATH.read_bytes()), (
        "config/skill-manifest.json is not what tools/gen_manifest.py produces "
        "(line endings normalized on both sides)")


def test_build_reproduces_the_committed_fixture():
    gm = _load_gen_manifest()
    _, fixture = gm.build()
    assert _norm(gm.serialize(fixture).encode("utf-8")) == _norm(FIXTURE_PATH.read_bytes()), (
        "expected_inventory.json is not what tools/gen_manifest.py produces "
        "(line endings normalized on both sides)")


def test_write_artifacts_reproduces_all_three_files(tmp_path):
    """Through the real writer, not just the in-memory doc: `write_artifacts` is what
    `main()` calls, and it is the only place the serialized text becomes bytes."""
    gm = _load_gen_manifest()
    gm.write_artifacts(tmp_path)
    for rel, committed in zip(gm.ARTIFACTS,
                              (MANIFEST_PATH, FIXTURE_PATH, INVENTORY_PATH)):
        written = tmp_path / rel
        assert written.is_file(), rel
        assert _norm(written.read_bytes()) == _norm(committed.read_bytes()), rel


def test_cli_regenerates_all_three_artifacts_with_no_legacy_source_set():
    """END-TO-END through the production entry point.

    `python tools/gen_manifest.py`, with SKILL_MESH_LEGACY_SOURCE scrubbed from the
    environment and no argument passed, must leave all three committed artifacts
    unchanged. The committed bytes are captured first and restored in `finally`, so a
    failure reports the drift instead of leaving it in the working tree.
    """
    targets = (MANIFEST_PATH, FIXTURE_PATH, INVENTORY_PATH)
    before = {p: p.read_bytes() for p in targets}
    env = {k: v for k, v in os.environ.items() if k != "SKILL_MESH_LEGACY_SOURCE"}
    try:
        r = subprocess.run([sys.executable, str(GEN_MANIFEST_PATH)],
                           cwd=str(REPO_ROOT), env=env,
                           capture_output=True, text=True)
        after = {p: p.read_bytes() for p in targets}
    finally:
        for p, data in before.items():
            p.write_bytes(data)
    assert r.returncode == 0, f"generator failed: {r.stderr}"
    drifted = [p.relative_to(REPO_ROOT).as_posix()
               for p in targets if _norm(after[p]) != _norm(before[p])]
    assert not drifted, (
        "a hermetic regeneration changed committed artifact(s): " + ", ".join(drifted))


def test_support_assets_constant_matches_the_committed_manifest():
    """The baked constant IS the committed data, per skill and in order.

    `test_build_reproduces_the_committed_manifest` would also catch a change here, but
    only as one opaque whole-document mismatch; this names the skill.
    """
    gm = _load_gen_manifest()
    committed = {s["name"]: s["support_assets"] for s in load_manifest()["skills"]}
    assert set(gm.SUPPORT_ASSETS) == set(committed), (
        "SUPPORT_ASSETS and the manifest disagree on the skill roster: "
        f"{sorted(set(gm.SUPPORT_ASSETS) ^ set(committed))}")
    for name in sorted(committed):
        assert gm.skill_support_assets(name) == committed[name], name


def test_judge_ui_calibration_note_is_generated_and_tracked():
    """The one support asset that came from the legacy GPT tree.

    It is the entry a naive `skills/` enumeration would erase and the entry the old
    external scan lost once the cutover overwrote its source, so it is asserted on the
    GENERATED side, not only on the committed one. Step 62 vendored the file itself,
    so the declaration now resolves to a real tracked path.
    """
    gm = _load_gen_manifest()
    manifest, _ = gm.build()
    judge_ui = next(s for s in manifest["skills"] if s["name"] == "judge-ui")
    dests = {a["dest"] for a in judge_ui["support_assets"]}
    assert "skills/judge-ui/calibration-notes.md" in dests, (
        "the generator dropped judge-ui's calibration note")
    assert (REPO_ROOT / "skills" / "judge-ui" / "calibration-notes.md").is_file(), (
        "the declared calibration note is not on disk")


def test_derived_skill_sets_match_the_spelled_out_rosters():
    """The roster guards inside `build()`, exercised on their own so a roster edited in
    one place only is named here rather than surfacing as a generator crash."""
    gm = _load_gen_manifest()
    sets = gm.derived_skill_sets()
    assert sets.portable == sorted(gm.PORTABLE)
    assert sets.native == sorted(gm.NATIVE)
    assert (len(sets.portable), len(sets.native)) == (45, 2)
    # gpt is the one OPTIONAL provider today. Every portable skill that predates
    # Phase CL Step 113 still carries its adapter until V4-7 removes them; skill-crud,
    # created in that step, ships none. Spelled, so the next change in that set is a
    # deliberate edit here rather than a silent change of meaning.
    assert set(sets.optional) == {"gpt"}
    assert sets.optional["gpt"] == sorted(set(sets.portable) - {"skill-crud"})
    assert not set(sets.optional["gpt"]) & set(sets.native)


def test_no_independent_codex_membership_authority_remains():
    """Decision CL-D14: Codex membership is DERIVED from PORTABLE plus the required set.

    A spelled codex roster beside PORTABLE is a second authority for an equality the
    contract requires, so its return is a defect this test names. The derivation is
    proven through the production builder: every portable record carries codex
    because codex is required, and nothing else puts it there.
    """
    gm = _load_gen_manifest()
    assert not hasattr(gm, "CODEX"), "a spelled CODEX roster is back in gen_manifest.py"
    src = GEN_MANIFEST_PATH.read_text(encoding="utf-8")
    assert not re.search(r"^CODEX\s*=", src, re.M)
    assert "codex" in gm.REQUIRED_PROVIDERS and "codex" not in gm.OPTIONAL_PROVIDERS
    manifest, _ = gm.build()
    codex = [s["name"] for s in manifest["skills"] if "codex" in s["providers"]]
    assert codex == sorted(gm.PORTABLE)


def _plant_skill_tree(root, portable=45, native=2, extras=(), gpt=None,
                      drop=None, native_extra=None, names=None, native_names=None):
    """A synthetic skills/ tree.

    `portable` dirs carry core.md plus an adapter for every required provider (claude,
    codex) -- the legal portable shape -- and the first `gpt` of them (default: all)
    also carry the optional gpt.md. `native` dirs carry core-less providers/claude.md.

    `drop`, `(provider, n)`, removes that required adapter from the first n portable
    dirs (the incomplete-package shape); `native_extra`, `(provider, n)`, plants a
    non-Claude adapter on the first n native dirs (illegal: provider-native means
    Claude-only). `names` / `native_names` override the generated directory names.
    `extras` are non-skill entries the caller wants to prove are skipped.
    """
    root.mkdir(parents=True, exist_ok=True)
    names = names or [f"skill-{i:02d}" for i in range(portable)]
    native_names = native_names or [f"native-{i}" for i in range(native)]
    gpt = len(names) if gpt is None else gpt
    for i, name in enumerate(names):
        d = root / name
        (d / "providers").mkdir(parents=True)
        (d / "core.md").write_text("x", encoding="utf-8")
        for provider in ("claude", "codex"):
            if drop and drop[0] == provider and i < drop[1]:
                continue
            (d / "providers" / f"{provider}.md").write_text("x", encoding="utf-8")
        if i < gpt:
            (d / "providers" / "gpt.md").write_text("x", encoding="utf-8")
    for i, name in enumerate(native_names):
        d = root / name / "providers"
        d.mkdir(parents=True)
        (d / "claude.md").write_text("x", encoding="utf-8")
        if native_extra and i < native_extra[1]:
            (d / f"{native_extra[0]}.md").write_text("x", encoding="utf-8")
    for name in extras:
        if name.endswith("/"):
            (root / name.rstrip("/")).mkdir()
        else:
            (root / name).write_text("{}", encoding="utf-8")


def test_enumeration_skips_inventory_json_and_the_shared_namespace(tmp_path):
    """The two gates the enumeration must apply, proven on a synthetic tree.

    `p.is_dir()` keeps the generated skills/inventory.json from counting as a skill,
    and `_shared` is excluded because it is the cross-skill payload namespace, not a
    skill. `_shared` does not exist under skills/ today, so only a planted tree can
    exercise that branch at all -- without this the exclusion would be untested code
    that silently stops working the day the directory lands.
    """
    gm = _load_gen_manifest()
    root = tmp_path / "skills"
    _plant_skill_tree(root, extras=("inventory.json", "_shared/"))
    (root / "_shared" / "judge-core.md").write_text("x", encoding="utf-8")
    sets = gm.derived_skill_sets(root)
    assert (len(sets.portable), len(sets.native)) == (45, 2)
    assert "inventory.json" not in sets.portable + sets.native
    assert "_shared" not in sets.portable + sets.native


def test_gpt_is_optional_and_changes_nothing_but_the_gpt_entry(tmp_path):
    """A portable skill without gpt.md is still portable -- that is not drift.

    GPT is no longer a required provider (operator decision 2026-11-14), so leaving
    gpt.md off five portable dirs must leave the 45/2 partition byte-for-byte
    unchanged and only shrink the optional gpt list.
    """
    gm = _load_gen_manifest()
    root = tmp_path / "skills"
    _plant_skill_tree(root, gpt=40)
    sets = gm.derived_skill_sets(root)
    assert (len(sets.portable), len(sets.native)) == (45, 2)
    assert len(sets.optional["gpt"]) == 40
    assert set(sets.optional["gpt"]) <= set(sets.portable)


@pytest.mark.parametrize("provider", ["claude", "codex"])
def test_enumeration_reds_on_a_portable_skill_missing_a_required_adapter(tmp_path, provider):
    """Red-on-garbage anchor for the required-provider rule at the tree level.

    A core plus only some required adapters is an incomplete change, not a portable
    skill in a partial state. It must raise naming the skill and the missing provider,
    not be filed as provider-native or merely miscounted.
    """
    gm = _load_gen_manifest()
    root = tmp_path / "skills"
    _plant_skill_tree(root, drop=(provider, 1))
    with pytest.raises(ValueError, match=rf"required provider.*skill-00 \(missing {provider}\)"):
        gm.derived_skill_sets(root)


@pytest.mark.parametrize("provider", ["codex", "gpt"])
def test_enumeration_reds_when_a_native_skill_carries_another_providers_adapter(
        tmp_path, provider):
    """Red-on-garbage anchor for the native-is-Claude-only guard.

    Provider-native means Claude-only, so any other provider's adapter inside a native
    skill dir is a contradiction. Without this guard the generator would emit a
    provider path for a skill the builder deliberately excludes from every non-claude
    profile -- a manifest promising a profile that will never contain it. The counts
    stay valid (45/2), so no count-based guard can catch it.
    """
    gm = _load_gen_manifest()
    root = tmp_path / "skills"
    _plant_skill_tree(root, native_extra=(provider, 1))
    with pytest.raises(ValueError, match="Claude-only"):
        gm.derived_skill_sets(root)


def test_enumeration_reds_when_the_tree_disagrees_with_the_counts(tmp_path):
    """Red-on-garbage anchor. What it can decide, stated exactly:

    Every planted tree here must be REJECTED, so deleting the whole guard block reds
    this test. Beyond that, no ONE guard can carry the block alone -- for each single
    guard, at least one planted case slips past it: keep only the total guard and 46/1
    slips (it sums to 47); keep only the portable guard and 45/3 slips; keep only the
    native guard and BOTH 46/2 and 44/2 slip. Before the 46/1 case existed the other
    three all broke the total too, so a total-only block passed this anchor -- that is
    the hole 46/1 closes. The four cases do NOT each have a distinct catching subset,
    and this docstring does not claim they do: 46/2 and 44/2 are both caught by exactly
    {total, portable}.

    What it CANNOT decide, and does not claim: deleting exactly one guard is invisible
    to any count-based tree, because total == portable + native makes any two of the
    three guards imply the third. That is a property of the arithmetic, not a gap a
    fifth planted tree could close.

    The expected counts are DERIVED from the spelled roster (Phase CL Step 111), so
    these trees are judged against len(PORTABLE) / len(NATIVE) -- 45/2 today.

    The guards raise ValueError, not AssertionError, precisely so `python -O` cannot
    strip them; catching ValueError here keeps that property under test.
    """
    gm = _load_gen_manifest()
    for kwargs in ({"portable": 46}, {"native": 3}, {"portable": 44},
                   {"portable": 46, "native": 1}):
        root = tmp_path / ("skills-" + "-".join(f"{k}{v}" for k, v in sorted(kwargs.items())))
        _plant_skill_tree(root, **kwargs)
        try:
            gm.derived_skill_sets(root)
        except ValueError:
            continue
        raise AssertionError(f"enumeration accepted a tree with {kwargs}")


# --------------------------------------------------------------------------- #
# Provenance: origin + nullable migration (Phase CL Step 111, CL-D8)
# --------------------------------------------------------------------------- #

def _plant_catalog_with_a_new_skill(gm, tmp_path, monkeypatch, assets=()):
    """The committed roster plus one CANONICAL-born portable skill, `skill-new`,
    planted as core.md + claude.md + codex.md and NO gpt.md -- the shape a CREATE
    produces now that GPT is not required. Every module constant a real CREATE edits
    is extended the same way, and SKILLS_DIR points at the planted tree, so the
    record comes out of the production `build()` / `render_artifacts()` path."""
    root = tmp_path / "skills"
    portable = list(gm.PORTABLE)
    _plant_skill_tree(root, names=portable, native_names=list(gm.NATIVE))
    # Mirror the committed tree's optional adapters: a portable skill that ships no
    # gpt.md (skill-crud since Phase CL Step 113) ships none here either.
    with_gpt = set(gm.derived_skill_sets().optional["gpt"])
    for name in portable:
        if name not in with_gpt:
            (root / name / "providers" / "gpt.md").unlink()
    new = root / "skill-new"
    (new / "providers").mkdir(parents=True)
    for rel in ("core.md", "providers/claude.md", "providers/codex.md"):
        (new / rel).write_text("x", encoding="utf-8")
    monkeypatch.setattr(gm, "SKILLS_DIR", root)
    monkeypatch.setattr(gm, "PORTABLE", portable + ["skill-new"])
    monkeypatch.setattr(gm, "DESCRIPTIONS", {**gm.DESCRIPTIONS, "skill-new": "A new skill."})
    monkeypatch.setattr(gm, "SUPPORT_ASSETS", {**gm.SUPPORT_ASSETS, "skill-new": list(assets)})


def test_a_canonical_born_fixture_carries_null_migration(tmp_path, monkeypatch):
    """The canonical fixture: a skill authored in Skill Mesh has `origin: canonical`
    and `migration: null` -- never a fabricated legacy path -- in the manifest AND the
    expected fixture, and it validates and projects into the inventory unchanged."""
    gm = _load_gen_manifest()
    _plant_catalog_with_a_new_skill(gm, tmp_path, monkeypatch)
    manifest, payloads = gm.render_artifacts()
    record = next(s for s in manifest["skills"] if s["name"] == "skill-new")
    assert record["origin"] == "canonical"
    assert record["migration"] is None
    assert record["status"] == "portable"
    # The required set and nothing else: no gpt.md, so no gpt key, and that is legal.
    assert record["providers"] == {
        "claude": "skills/skill-new/providers/claude.md",
        "codex": "skills/skill-new/providers/codex.md",
    }
    fixture = json.loads(payloads[gm.ARTIFACTS[1]])
    fixture_record = next(s for s in fixture["skills"] if s["name"] == "skill-new")
    assert (fixture_record["origin"], fixture_record["migration"]) == ("canonical", None)
    assert "skill-new" in fixture["codex"]
    inventory = json.loads(payloads[gm.ARTIFACTS[2]])
    inv = next(s for s in inventory["skills"] if s["name"] == "skill-new")
    assert inv["providers"] == {"claude": True, "gpt": False, "codex": True}
    # ...and the counts it moves are the ones a CREATE should move, no others.
    assert manifest["counts"]["portable"] == 46 and manifest["counts"]["codex"] == 46
    assert manifest["counts"]["gpt"] == 44
    # Existing records keep their truthful legacy provenance through the same run.
    plan_init = next(s for s in manifest["skills"] if s["name"] == "plan-init")
    assert plan_init["origin"] == "legacy-migrated"
    assert plan_init["migration"]["legacy_core"] == ".claude/skills-gpt/plan-init/SKILL-core.md"


def test_a_canonical_skill_cannot_declare_legacy_sourced_support_assets(tmp_path, monkeypatch):
    """A support asset's `source` is a legacy path, so on a canonical skill it would
    be exactly the fabricated provenance CL-D8 forbids."""
    gm = _load_gen_manifest()
    _plant_catalog_with_a_new_skill(gm, tmp_path, monkeypatch, assets=[("skills", "evals/")])
    with pytest.raises(ValueError, match="canonical skill cannot declare"):
        gm.build()


def test_legacy_provenance_is_closed_history(monkeypatch):
    """The legacy sets may only shrink: a name the roster no longer carries is a
    DELETE that left its provenance behind, and a provider-native skill without
    legacy provenance would be a new native identity."""
    gm = _load_gen_manifest()
    monkeypatch.setattr(gm, "LEGACY_SPLIT", gm.LEGACY_SPLIT | {"ghost"})
    with pytest.raises(ValueError, match="not in the roster"):
        gm.build()
    monkeypatch.setattr(gm, "LEGACY_SPLIT", gm.LEGACY_SPLIT - {"ghost"})
    monkeypatch.setattr(gm, "LEGACY_SINGLE_FILE", gm.LEGACY_SINGLE_FILE - {"context-slim"})
    with pytest.raises(ValueError, match="provider-native skills must carry legacy"):
        gm.build()


# --------------------------------------------------------------------------- #
# Validate-then-replace writer and the no-write --check (Phase CL Step 111)
# --------------------------------------------------------------------------- #

def _artifact_state(gm, root):
    """Bytes and mtime of each artifact, plus the listing of every directory that
    holds one -- the evidence that a run wrote nothing, temporaries included."""
    state = {}
    for rel in gm.ARTIFACTS:
        p = root / rel
        state[rel] = (p.read_bytes(), p.stat().st_mtime_ns) if p.exists() else None
        state["dir:" + rel] = sorted(x.name for x in p.parent.iterdir()) \
            if p.parent.is_dir() else None
    return state


def test_check_cli_is_read_only_and_green():
    """`python tools/gen_manifest.py --check` through the production entry point:
    exit 0 on the committed tree, and not one byte, mtime or directory entry of the
    three artifacts' homes changes."""
    gm = _load_gen_manifest()
    before = _artifact_state(gm, REPO_ROOT)
    env = {k: v for k, v in os.environ.items() if k != "SKILL_MESH_LEGACY_SOURCE"}
    r = subprocess.run([sys.executable, str(GEN_MANIFEST_PATH), "--check"],
                       cwd=str(REPO_ROOT), env=env, capture_output=True, text=True)
    assert r.returncode == 0, f"--check is red on the committed tree:\n{r.stderr}"
    assert "match a regeneration" in r.stdout
    assert _artifact_state(gm, REPO_ROOT) == before, "--check changed the tree"


def test_check_mode_never_reaches_the_writer(monkeypatch):
    """In-process, with every write primitive booby-trapped: `main(["--check"])` must
    finish without touching one of them."""
    gm = _load_gen_manifest()

    def trap(*args, **kwargs):
        raise AssertionError("--check reached a write path")

    monkeypatch.setattr(gm, "_replace_file", trap)
    monkeypatch.setattr(gm, "write_artifacts", trap)
    monkeypatch.setattr(gm, "_write_payload", trap)
    assert gm.main(["--check"]) == 0


def test_check_reports_drift_and_missing_files_without_writing(tmp_path):
    gm = _load_gen_manifest()
    for rel, committed in zip(gm.ARTIFACTS, (MANIFEST_PATH, FIXTURE_PATH, INVENTORY_PATH)):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        # CRLF copies of the committed bytes: a property of the clone, never drift.
        (tmp_path / rel).write_bytes(_norm(committed.read_bytes()).replace(b"\n", b"\r\n"))
    assert gm.check_artifacts(tmp_path) == []
    (tmp_path / gm.ARTIFACTS[0]).write_bytes(MANIFEST_PATH.read_bytes() + b" ")
    (tmp_path / gm.ARTIFACTS[2]).unlink()
    before = _artifact_state(gm, tmp_path)
    assert gm.check_artifacts(tmp_path) == [gm.ARTIFACTS[0], f"{gm.ARTIFACTS[2]} (missing)"]
    assert _artifact_state(gm, tmp_path) == before


def test_all_three_payloads_are_validated_before_the_first_replacement(tmp_path, monkeypatch):
    gm = _load_gen_manifest()
    events = []
    real_validate, real_replace = gm.validate_payloads, gm._replace_file

    def validate(payloads):
        events.append(("validate", tuple(payloads)))
        real_validate(payloads)

    def replace(path, data):
        events.append(("replace", path.relative_to(tmp_path).as_posix()))
        real_replace(path, data)

    monkeypatch.setattr(gm, "validate_payloads", validate)
    monkeypatch.setattr(gm, "_replace_file", replace)
    gm.write_artifacts(tmp_path)
    assert events == [("validate", gm.ARTIFACTS)] + [("replace", rel) for rel in gm.ARTIFACTS]


def test_a_payload_that_fails_validation_replaces_nothing(tmp_path, monkeypatch):
    """The third payload is the one built last; corrupting it must still stop the
    FIRST replacement, which is what "validate all three first" means."""
    gm = _load_gen_manifest()
    seed = b'{"stale": true}\n'
    for rel in gm.ARTIFACTS:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(seed)
    real_build_inventory = gm._build_inventory

    def bad_inventory(manifest):
        inventory = real_build_inventory(manifest)
        inventory["counts"]["codex"] -= 1
        return inventory

    monkeypatch.setattr(gm, "_build_inventory", bad_inventory)
    before = _artifact_state(gm, tmp_path)
    with pytest.raises(ValueError, match="nothing was written"):
        gm.write_artifacts(tmp_path)
    assert _artifact_state(gm, tmp_path) == before


def test_validation_reds_on_each_planted_defect():
    """Red-on-garbage anchors for `validate_payloads`: each planted defect, alone, on
    otherwise-valid payloads, is refused."""
    gm = _load_gen_manifest()
    _, good = gm.render_artifacts()

    def mutated(index, change):
        docs = [json.loads(good[rel]) for rel in gm.ARTIFACTS]
        change(docs[index])
        return {rel: gm.serialize(doc).encode("utf-8") for rel, doc in zip(gm.ARTIFACTS, docs)}

    def first(doc, name):
        return next(s for s in doc["skills"] if s["name"] == name)

    planted = {
        "required set widened": (0, lambda d: d["portable_provider_contract"]["required"].append("gpt")),
        "portable record lost codex": (0, lambda d: first(d, "plan-init")["providers"].pop("codex")),
        "canonical record fabricated": (0, lambda d: first(d, "user-dr").update(
            migration={k: None for k in gm.MIGRATION_KEYS})),
        "legacy record lost provenance": (0, lambda d: first(d, "plan-init").update(migration=None)),
        "fixture origin drifted": (1, lambda d: first(d, "user-dr").update(origin="legacy-migrated")),
        "inventory flag drifted": (2, lambda d: first(d, "plan-init")["providers"].update(codex=False)),
    }
    gm.validate_payloads(good)
    for label, (index, change) in planted.items():
        with pytest.raises(ValueError):
            gm.validate_payloads(mutated(index, change))
            raise AssertionError(f"validation accepted: {label}")
    crlf = dict(good)
    crlf[gm.ARTIFACTS[1]] = good[gm.ARTIFACTS[1]].replace(b"\n", b"\r\n")
    with pytest.raises(ValueError, match="LF"):
        gm.validate_payloads(crlf)


@pytest.mark.parametrize("where", ["mid-write", "between-files"])
def test_an_interrupted_regeneration_never_truncates_and_check_reports_it(
        tmp_path, monkeypatch, where):
    """Inject an interruption into the second replacement -- part-way through writing
    its bytes, or before it starts -- and prove the two properties the writer claims:
    no artifact is ever truncated (each file is wholly old or wholly new, and no
    temporary is left behind), and the next `--check` names exactly the files the
    interrupted run did not reach. A rerun then repairs the tree."""
    gm = _load_gen_manifest()
    seed = b'{"stale": true}\n'
    for rel in gm.ARTIFACTS:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(seed)
    _, payloads = gm.render_artifacts()
    calls = []

    class Interrupted(KeyboardInterrupt):
        pass

    if where == "mid-write":
        real_write = gm._write_payload

        def write(handle, data):
            calls.append(len(data))
            if len(calls) == 2:
                handle.write(data[: len(data) // 2])
                raise Interrupted()
            real_write(handle, data)

        monkeypatch.setattr(gm, "_write_payload", write)
    else:
        real_replace = gm._replace_file

        def replace(path, data):
            calls.append(path)
            if len(calls) == 2:
                raise Interrupted()
            real_replace(path, data)

        monkeypatch.setattr(gm, "_replace_file", replace)

    with pytest.raises(Interrupted):
        gm.write_artifacts(tmp_path)
    first, second, third = (tmp_path / rel for rel in gm.ARTIFACTS)
    assert first.read_bytes() == payloads[gm.ARTIFACTS[0]]
    assert second.read_bytes() == seed, "the interrupted artifact is not the old file whole"
    assert third.read_bytes() == seed
    leftovers = sorted(p.name for p in tmp_path.rglob("*.tmp"))
    assert not leftovers, f"temporary files left behind: {leftovers}"
    assert gm.check_artifacts(tmp_path) == [gm.ARTIFACTS[1], gm.ARTIFACTS[2]]
    monkeypatch.undo()
    gm.write_artifacts(tmp_path)
    assert gm.check_artifacts(tmp_path) == []



# Each of these checks once had no test that could fail: a reviewer disabled each one in
# a scratch copy and this whole file stayed green, because every planted defect above
# that could reach it is also caught by a sibling check. So each case plants ONE defect
# that this check is the one to name, and matches on that check's own message: removing
# the check turns its case red even while a sibling still refuses the payload.
_NAMED_CHECKS = {
    "fixture counts match manifest counts": (
        1, lambda d, first: d["counts"].update(vision=d["counts"]["vision"] + 1),
        "fixture counts != manifest counts"),
    "portable record core path": (
        0, lambda d, first: first(d, "plan-init").update(core="skills/user-dr/core.md"),
        "plan-init: portable record without its core"),
    "providers in vocabulary order": (
        0, lambda d, first: first(d, "plan-init").update(
            providers=dict(reversed(list(first(d, "plan-init")["providers"].items())))),
        "plan-init: providers not in vocabulary order"),
    "provider-native has no core": (
        0, lambda d, first: first(d, "claude-oauth-auth").update(
            core="skills/claude-oauth-auth/core.md"),
        "claude-oauth-auth: provider-native record is not Claude-only"),
    "provider-native has only claude": (
        0, lambda d, first: first(d, "claude-oauth-auth")["providers"].update(
            codex="skills/claude-oauth-auth/providers/codex.md"),
        "claude-oauth-auth: provider-native record is not Claude-only"),
    "legacy record names a Claude source": (
        0, lambda d, first: first(d, "claude-oauth-auth")["migration"].update(
            legacy_claude_adapter=None),
        "claude-oauth-auth: legacy record names no Claude source"),
    "fixture codex roster matches the portable records": (
        1, lambda d, first: d["codex"].remove("plan-init"),
        "fixture codex roster != the portable records"),
}


@pytest.mark.parametrize("label", sorted(_NAMED_CHECKS))
def test_validation_names_each_otherwise_unguarded_check(label):
    gm = _load_gen_manifest()
    _, good = gm.render_artifacts()
    index, change, message = _NAMED_CHECKS[label]
    docs = [json.loads(good[rel]) for rel in gm.ARTIFACTS]

    def first(doc, name):
        return next(s for s in doc["skills"] if s["name"] == name)

    change(docs[index], first)
    bad = {rel: gm.serialize(doc).encode("utf-8") for rel, doc in zip(gm.ARTIFACTS, docs)}
    assert bad != good, f"the planted defect changed nothing: {label}"
    with pytest.raises(ValueError) as caught:
        gm.validate_payloads(bad)
    assert message in str(caught.value), (
        f"{label}: refused, but not by its own check:\n{caught.value}")


# --check exit codes through the production CLI, on a private copy of exactly what the
# generator reads (it resolves REPO_ROOT from its own file). Each outcome has its own
# code, so a caller reading only the code can tell stale artifacts from a broken
# generator. 2 is argparse's usage error and is deliberately not reused.
_GENERATOR_COPY = ("skills", "tools/gen_manifest.py", "tools/gen_skill_tree.py",
                   "config/skill-manifest.json",
                   "tests/package-integrity/expected_inventory.json")


@pytest.fixture()
def generator_copy(tmp_path):
    root = tmp_path / "repo"
    for rel in _GENERATOR_COPY:
        src, dst = REPO_ROOT / rel, root / rel
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return root


def _run_check(root):
    env = {k: v for k, v in os.environ.items() if k != "SKILL_MESH_LEGACY_SOURCE"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, str(root / "tools" / "gen_manifest.py"), "--check"],
                          cwd=str(root), env=env, capture_output=True, text=True)


def test_check_cli_exit_codes_are_pinned_and_distinct():
    gm = _load_gen_manifest()
    assert (gm.EXIT_CLEAN, gm.EXIT_DRIFT, gm.EXIT_INVALID) == (0, 1, 3)


def test_check_cli_exits_0_on_a_clean_copy(generator_copy):
    r = _run_check(generator_copy)
    assert r.returncode == 0, r.stderr
    assert "match a regeneration" in r.stdout and r.stderr == ""


def test_check_cli_exits_1_on_drift_naming_each_file(generator_copy):
    gm = _load_gen_manifest()
    stale = generator_copy / gm.ARTIFACTS[0]
    stale.write_bytes(stale.read_bytes() + b" ")
    (generator_copy / gm.ARTIFACTS[2]).unlink()
    r = _run_check(generator_copy)
    assert r.returncode == 1, r.stderr
    assert f"drift: {gm.ARTIFACTS[0]}" in r.stderr
    assert f"drift: {gm.ARTIFACTS[2]} (missing)" in r.stderr
    assert "Traceback" not in r.stderr and "validation failed" not in r.stderr


@pytest.mark.parametrize("planted", ["payload", "roster"])
def test_check_cli_exits_3_on_a_validation_failure_with_one_line(generator_copy, planted):
    """A generator whose own output fails validation (`payload`), or that refuses the
    tree before it serializes anything (`roster`, an unlisted skill directory), is a
    broken generator, not drift: exit 3, ONE named stderr line, no traceback."""
    gm_path = generator_copy / "tools" / "gen_manifest.py"
    if planted == "payload":
        text = gm_path.read_text(encoding="utf-8")
        old = "    inventory = _build_inventory(manifest)\n"
        assert text.count(old) == 1
        gm_path.write_text(text.replace(
            old, old + '    inventory["counts"]["codex"] -= 1\n'), encoding="utf-8")
    else:
        package = generator_copy / "skills" / "zz-unlisted"
        (package / "providers").mkdir(parents=True)
        (package / "core.md").write_text("# zz-unlisted\n", encoding="utf-8")
        for provider in ("claude", "codex"):
            (package / "providers" / f"{provider}.md").write_text("x\n", encoding="utf-8")
    r = _run_check(generator_copy)
    assert r.returncode == 3, f"exit {r.returncode}:\n{r.stderr}"
    lines = r.stderr.splitlines()
    assert len(lines) == 1, f"expected one error line:\n{r.stderr}"
    assert lines[0].startswith("validation failed: ValueError: "), lines[0]
    assert "Traceback" not in r.stderr and "drift:" not in r.stderr
    assert r.stdout == ""
    if planted == "payload":
        assert "inventory counts['codex'] != manifest counts['codex']" in lines[0]


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
