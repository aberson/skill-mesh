"""Package-integrity contract gate for the skill-mesh neutral package (Step 33).

Validates config/skill-manifest.json against a committed authoritative inventory
(expected_inventory.json) plus the documented command contract in
documentation/architecture.md.

Design:
- The public package tests depend on NO private/legacy source. All expected truth
  is committed in tests/package-integrity/expected_inventory.json.
- Since Step 67 the GENERATOR depends on no external source either, and the last
  section of this file is the gate that holds it there: a regeneration must
  reproduce both committed artifacts with no environment set.

Runnable via pytest (`python -m pytest tests/package-integrity`) or standalone
(`python tests/package-integrity/test_manifest_contract.py`).
"""

import importlib.util
import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"
FIXTURE_PATH = Path(__file__).resolve().parent / "expected_inventory.json"
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
    assert derived["total"] == 57
    assert derived["portable"] == 54
    assert derived["provider_native"] == 3
    assert derived["claude"] == 57, "every skill carries a Claude adapter"
    assert derived["gpt"] == 54, "the gpt adapter set IS the portable set"
    # 54 at Phase CP Step 10. It was 0 at Step 3 (the generation rails ship before
    # any codex adapter is authored), 5 at Step 4, 17 at Step 6, 33 at Step 7, and
    # Step 8 closed it at the then-portable catalog of 47. Step 10 (issue #127)
    # promoted seven workspace-custom skills, each authored portable AND codex in
    # one commit, so this grew WITH `portable` rather than apart from it. A value
    # here without a matching skills/*/providers/codex.md on disk is caught by
    # gen_manifest.py's CODEX-vs-tree guard.
    assert derived["codex"] == 54
    # local_capable is UNCHANGED at 24: none of the seven Step 10 promotions has a
    # local-capable row in the legacy model-mapping table, so none was declared (see
    # gen_manifest.py's LOCAL_CAPABLE note). sub_agent gains exactly one --
    # citation-sweep, whose core dispatches one isolated per-artifact review worker.
    assert derived["local_capable"] == 24
    assert derived["sub_agent"] == 17
    assert derived["vision"] == 2
    assert derived["filesystem"] == 57


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
    """The codex roster, pinned against the committed fixture like its siblings.

    Non-vacuous from Phase CP Step 4 onward: the pilot five are the first names in it.
    A count alone cannot tell "the pilot five" from "any five portable skills", and the
    cohort steps grow this set deliberately -- so the NAMES are asserted, and against a
    fixture produced by the same generator run that produced the manifest.
    """
    m = load_manifest()
    fx = load_fixture()
    codex = {s["name"] for s in m["skills"] if "codex" in s["providers"]}
    assert codex == set(fx["codex"])
    # Orthogonal axis: every codex name is also portable (see gen_manifest.CODEX).
    portable = {s["name"] for s in m["skills"] if s["status"] == "portable"}
    assert codex <= portable


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
        # claude + gpt are MANDATORY for a portable skill (that pair is what
        # "portable" means); codex is OPTIONAL and additive -- present only for the
        # skills whose adapter has been authored, which grows across Phase CP
        # (0 at Step 3, the pilot five at Step 4, the catalog after the cohorts).
        # Asserted as "the required pair, plus at most codex" rather than a widened
        # exact set, so an unexpected FOURTH provider key is still caught here.
        assert {"claude", "gpt"} <= set(prov.keys()), name
        assert set(prov.keys()) <= {"claude", "gpt", "codex"}, name
        assert prov["claude"] == f"skills/{name}/providers/claude.md", name
        assert prov["gpt"] == f"skills/{name}/providers/gpt.md", name
        if "codex" in prov:
            assert prov["codex"] == f"skills/{name}/providers/codex.md", name


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
    src = GEN_MANIFEST_PATH.read_text(encoding="utf-8")
    assert "add_argument" not in src, (
        "gen_manifest.py's CLI declares an argument again; generation takes no input "
        "beyond this repository")
    assert "import os" not in src and "os.environ" not in src, (
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


def test_write_artifacts_reproduces_both_files(tmp_path):
    """Through the real writer, not just the in-memory doc: `write_artifacts` is what
    `main()` calls, and it is the only place the serialized text becomes bytes."""
    gm = _load_gen_manifest()
    gm.write_artifacts(tmp_path)
    for rel, committed in zip(gm.ARTIFACTS, (MANIFEST_PATH, FIXTURE_PATH)):
        written = tmp_path / rel
        assert written.is_file(), rel
        assert _norm(written.read_bytes()) == _norm(committed.read_bytes()), rel


def test_cli_regenerates_both_artifacts_with_no_legacy_source_set():
    """END-TO-END through the production entry point.

    `python tools/gen_manifest.py`, with SKILL_MESH_LEGACY_SOURCE scrubbed from the
    environment and no argument passed, must leave both committed artifacts
    unchanged. The committed bytes are captured first and restored in `finally`, so a
    failure reports the drift instead of leaving it in the working tree.
    """
    targets = (MANIFEST_PATH, FIXTURE_PATH)
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
    portable, native, codex = gm.derived_skill_sets()
    assert portable == sorted(gm.PORTABLE)
    assert native == sorted(gm.NATIVE)
    assert codex == sorted(gm.CODEX)
    assert (len(portable), len(native)) == (54, 3)
    # 54 at Phase CP Step 10: the Step 8 catalog of 47 plus the seven promoted
    # workspace-custom skills (issue #127), each landing portable and codex in the
    # same commit. Spelled, like its siblings above, so any step that grows the
    # roster must come here and state the new number rather than letting a glob
    # silently redefine it.
    assert len(codex) == 54
    # Codex is an ORTHOGONAL axis, not a third bucket -- every codex name is also
    # portable, and the 54/3 partition is unaffected by codex membership. This is the
    # invariant that lets counts["portable"], the README's GPT-capable line and the
    # `total == portable + native` arithmetic all keep their existing meanings.
    assert set(codex) <= set(portable)
    assert not set(codex) & set(native)


def _plant_skill_tree(root, portable=54, native=3, extras=(), codex=0,
                      codex_on_native=0):
    """A synthetic skills/ tree: `portable` dirs with providers/gpt.md, `native`
    without, plus whatever non-skill entries the caller wants to prove are skipped.

    `codex` plants providers/codex.md on the first N PORTABLE dirs (the legal shape);
    `codex_on_native` plants it on the first N NATIVE dirs (the illegal shape, since
    provider-native means Claude-only).
    """
    root.mkdir(parents=True, exist_ok=True)
    for i in range(portable):
        d = root / f"skill-{i:02d}" / "providers"
        d.mkdir(parents=True)
        (d / "gpt.md").write_text("x", encoding="utf-8")
        (d / "claude.md").write_text("x", encoding="utf-8")
        if i < codex:
            (d / "codex.md").write_text("x", encoding="utf-8")
    for i in range(native):
        d = root / f"native-{i}" / "providers"
        d.mkdir(parents=True)
        (d / "claude.md").write_text("x", encoding="utf-8")
        if i < codex_on_native:
            (d / "codex.md").write_text("x", encoding="utf-8")
    for name in extras:
        if name.endswith("/"):
            (root / name.rstrip("/")).mkdir()
        else:
            (root / name).write_text("{}", encoding="utf-8")


def test_enumeration_skips_inventory_json_and_the_shared_namespace(tmp_path):
    """The two gates the enumeration must apply, proven on a synthetic tree.

    `p.is_dir()` keeps the generated skills/inventory.json from counting as a 58th
    skill, and `_shared` is excluded because it is the cross-skill payload namespace,
    not a skill. `_shared` does not exist under skills/ today, so only a planted tree
    can exercise that branch at all -- without this the exclusion would be untested
    code that silently stops working the day the directory lands.
    """
    gm = _load_gen_manifest()
    root = tmp_path / "skills"
    _plant_skill_tree(root, extras=("inventory.json", "_shared/"))
    (root / "_shared" / "judge-core.md").write_text("x", encoding="utf-8")
    portable, native, codex = gm.derived_skill_sets(root)
    assert (len(portable), len(native)) == (54, 3)
    assert codex == []
    assert "inventory.json" not in portable + native
    assert "_shared" not in portable + native


def test_codex_enumeration_is_orthogonal_to_the_portable_native_partition(tmp_path):
    """A planted codex.md changes the codex roster and NOTHING else.

    This is the load-bearing property of the Phase CP Step 3 shape choice: codex is an
    additive axis, so planting 5 codex adapters must leave the 54/3 partition -- and
    therefore every committed count, the README's GPT-capable line, and the
    `total == portable + native` arithmetic -- byte-for-byte unchanged. If codex were
    modelled as a third STATUS instead, this test would red.
    """
    gm = _load_gen_manifest()
    root = tmp_path / "skills"
    _plant_skill_tree(root, codex=5)
    portable, native, codex = gm.derived_skill_sets(root)
    assert (len(portable), len(native)) == (54, 3)
    assert len(codex) == 5
    assert set(codex) <= set(portable)


def test_enumeration_reds_when_a_native_skill_carries_a_codex_adapter(tmp_path):
    """Red-on-garbage anchor for the native-is-Claude-only guard.

    Provider-native means Claude-only, so providers/codex.md inside a native skill dir
    is a contradiction. Without this guard the generator would happily emit a
    `providers.codex` path for a skill the builder deliberately excludes from every
    non-claude profile -- a manifest promising a profile that dist/codex will never
    contain. The counts stay valid (54/3), so no count-based guard can catch it.
    """
    gm = _load_gen_manifest()
    root = tmp_path / "skills"
    _plant_skill_tree(root, codex_on_native=1)
    with pytest.raises(ValueError, match="Claude-only"):
        gm.derived_skill_sets(root)


def test_enumeration_reds_when_the_tree_disagrees_with_the_counts(tmp_path):
    """Red-on-garbage anchor. What it can decide, stated exactly:

    Every planted tree here must be REJECTED, so deleting the whole guard block reds
    this test. Beyond that, no ONE guard can carry the block alone -- for each single
    guard, at least one planted case slips past it: keep only the total guard and 55/2
    slips (it sums to 57); keep only the portable guard and 54/4 slips; keep only the
    native guard and BOTH 55/3 and 53/3 slip. Before the 55/2 case existed the other
    three all broke the total too (58/58/56), so a total-only block passed this
    anchor -- that is the hole 55/2 closes. The four cases do NOT each have a distinct
    catching subset, and this docstring does not claim they do: 55/3 and 53/3 are both
    caught by exactly {total, portable}.

    What it CANNOT decide, and does not claim: deleting exactly one guard is invisible
    to any count-based tree, because total == portable + native makes any two of the
    three guards imply the third. That is a property of the arithmetic, not a gap a
    fifth planted tree could close.

    The guards raise ValueError, not AssertionError, precisely so `python -O` cannot
    strip them; catching ValueError here keeps that property under test.
    """
    gm = _load_gen_manifest()
    for kwargs in ({"portable": 55}, {"native": 4}, {"portable": 53},
                   {"portable": 55, "native": 2}):
        root = tmp_path / ("skills-" + "-".join(f"{k}{v}" for k, v in sorted(kwargs.items())))
        _plant_skill_tree(root, **kwargs)
        try:
            gm.derived_skill_sets(root)
        except ValueError:
            continue
        raise AssertionError(f"enumeration accepted a tree with {kwargs}")


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
