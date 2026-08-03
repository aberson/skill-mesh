"""Distribution build + install/uninstall gate (Step 36).

Exercises the two host-distribution tools end-to-end on a real Windows host:

  tools/build-distributions.ps1  -- deterministically renders per-provider
                                    discovery profiles from config/skill-manifest.json
                                    + the canonical skills/<name>/ source tree.
  tools/install-skill-mesh.ps1   -- installs a profile into a target home with an
                                    ownership ledger, idempotent reinstall, and an
                                    ownership-safe uninstall.

Style matches tests/router/ and tests/package-integrity/: shell out to
powershell.exe via subprocess, use tmp_path, and gate cleanly (skipif) when
powershell is not on PATH. On this Windows host powershell IS present, so these RUN.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "tools" / "build-distributions.ps1"
INSTALL_SCRIPT = REPO_ROOT / "tools" / "install-skill-mesh.ps1"
PROVENANCE_SCRIPT = REPO_ROOT / "tools" / "skill-mesh-provenance.ps1"
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"
SKILLS_ROOT = REPO_ROOT / "skills"


def _marker_literal():
    """The single-source-of-truth provenance marker, read from the shared script."""
    m = re.search(r"return\s+'([^']+)'", PROVENANCE_SCRIPT.read_text(encoding="utf-8"))
    assert m, "marker literal not found in tools/skill-mesh-provenance.ps1"
    return m.group(1)

# Provider-specific install target under the install home (must mirror the
# $DISCOVERY_SUBDIR map in install-skill-mesh.ps1). GPT installs to .github/skills --
# a real GitHub Copilot CLI discovery root (Step 43 proof); the project-relative
# .copilot/skills is the RETIRED wrong target. (`.claude` is written via Path() so
# this file carries no literal ".claude/" path token -- tests/router/
# test_no_claude_dependency.py flags load-bearing ".claude/" references in code.)
DISCOVERY_SUBDIR = {
    "claude": Path(".claude") / "skills",
    "gpt": Path(".github") / "skills",
}
# The retired project-relative GPT target: a GPT install must NEVER write here.
RETIRED_GPT_SUBDIR = Path(".copilot") / "skills"

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _run(script, args):
    return subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(script), *args],
        capture_output=True,
        text=True,
    )


def _build(out_dir, provider="both"):
    r = _run(BUILD_SCRIPT, ["-OutputDir", str(out_dir), "-Provider", provider])
    assert r.returncode == 0, f"build failed:\n{r.stdout}\n{r.stderr}"
    return r


def _install(home, provider, dist_dir=None, uninstall=False, force=False):
    args = ["-Home", str(home), "-Provider", provider]
    if dist_dir is not None:
        args += ["-DistDir", str(dist_dir)]
    if force:
        args.append("-Force")
    if uninstall:
        args.append("-Uninstall")
    return _run(INSTALL_SCRIPT, args)


def _write_manifest(path, skills):
    """Write a minimal adversarial manifest with the given skills list."""
    path.write_text(json.dumps({"skills": skills}), encoding="utf-8")
    return path


def _load_manifest():
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


GEN_MANIFEST_PATH = REPO_ROOT / "tools" / "gen_manifest.py"


def _load_gen_manifest():
    """Import tools/gen_manifest.py by path (under a private module name so its
    `if __name__ == '__main__'` guard never fires and no legacy source is needed).
    Returns the module so tests can read its authoritative DESCRIPTIONS constant."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "gen_manifest_under_test", GEN_MANIFEST_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _skill_partition():
    m = _load_manifest()
    portable = [s["name"] for s in m["skills"] if s["status"] == "portable"]
    native = [s["name"] for s in m["skills"] if s["status"] == "provider-native"]
    return portable, native


def _tree_snapshot(root):
    """Map of posix-relative path -> file bytes for every file under root."""
    snap = {}
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            snap[p.relative_to(root).as_posix()] = p.read_bytes()
    return snap


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def dist_root(tmp_path_factory):
    """Build both profiles once for the module."""
    out = tmp_path_factory.mktemp("dist")
    _build(out, provider="both")
    return out


# --------------------------------------------------------------------------- #
# Tooling presence
# --------------------------------------------------------------------------- #

def test_scripts_exist():
    assert BUILD_SCRIPT.is_file(), f"missing {BUILD_SCRIPT}"
    assert INSTALL_SCRIPT.is_file(), f"missing {INSTALL_SCRIPT}"


# --------------------------------------------------------------------------- #
# Build structure
# --------------------------------------------------------------------------- #

def test_build_emits_both_profiles(dist_root):
    assert (dist_root / "claude").is_dir()
    assert (dist_root / "gpt").is_dir()


def test_portable_skills_have_launcher_and_core_in_both_profiles(dist_root):
    portable, _ = _skill_partition()
    for name in portable:
        for profile in ("claude", "gpt"):
            d = dist_root / profile / name
            assert (d / "SKILL.md").is_file(), f"{profile}/{name}: missing SKILL.md"
            assert (d / "core.md").is_file(), f"{profile}/{name}: missing core.md"


def test_native_exclusions_only_truthful_adapter(dist_root):
    """Provider-native skills appear in claude/ (no core, since core is null) and are
    ABSENT from gpt/ -- no misleading stub for the unsupported provider."""
    _, native = _skill_partition()
    assert native, "expected provider-native skills in the manifest"
    for name in native:
        claude_dir = dist_root / "claude" / name
        assert (claude_dir / "SKILL.md").is_file(), f"claude/{name}: missing SKILL.md"
        assert not (claude_dir / "core.md").exists(), f"claude/{name}: unexpected core.md"
        assert not (dist_root / "gpt" / name).exists(), \
            f"gpt/{name}: provider-native skill must not be stubbed for GPT"


def test_build_file_counts_match_manifest(dist_root):
    portable, native = _skill_partition()
    claude_files = list((dist_root / "claude").rglob("*"))
    claude_files = [p for p in claude_files if p.is_file()]
    gpt_files = [p for p in (dist_root / "gpt").rglob("*") if p.is_file()]
    # claude: portable*(SKILL+core) + native*(SKILL only) + 2 verdict helpers;
    # gpt: portable*(SKILL+core) + 2 verdict helpers.
    assert len(claude_files) == len(portable) * 2 + len(native) * 1 + 2
    assert len(gpt_files) == len(portable) * 2 + 2


# --------------------------------------------------------------------------- #
# Provenance
# --------------------------------------------------------------------------- #

def test_generated_files_carry_provenance(dist_root):
    marker = _marker_literal()
    for profile in ("claude", "gpt"):
        for md in (dist_root / profile).rglob("*.md"):
            text = md.read_text(encoding="utf-8")
            assert "GENERATED FILE - DO NOT EDIT" in text, md
            assert "config/skill-manifest.json" in text, md
            assert f"Profile: {profile}" in text, md
            # canonical source path names the real skills/<name>/... source.
            assert "Canonical source: skills/" in text, md
            # the ownership-authority provenance marker is embedded in every file.
            assert marker in text, f"missing provenance marker in {md}"

    for profile in ("claude", "gpt"):
        for consumer in ("build-step", "build-phase"):
            helper = dist_root / profile / consumer / "build_step_verdict.py"
            text = helper.read_text(encoding="utf-8")
            assert marker in text
            assert "Canonical source: _shared/build_step_verdict.py" in text
            compile(text, str(helper), "exec")


# --------------------------------------------------------------------------- #
# Adapter resolution: claude discovery -> claude adapter; gpt -> gpt adapter
# --------------------------------------------------------------------------- #

def test_claude_discovery_resolves_claude_adapter(dist_root):
    skill = "build-phase"
    launcher = (dist_root / "claude" / skill / "SKILL.md").read_text(encoding="utf-8")
    assert "Canonical source: skills/build-phase/providers/claude.md" in launcher
    assert "Claude entry point" in launcher
    assert "GPT entry point" not in launcher


def test_gpt_discovery_resolves_gpt_adapter(dist_root):
    skill = "build-phase"
    launcher = (dist_root / "gpt" / skill / "SKILL.md").read_text(encoding="utf-8")
    assert "Canonical source: skills/build-phase/providers/gpt.md" in launcher
    assert "GPT entry point" in launcher
    assert "Claude entry point" not in launcher


# --------------------------------------------------------------------------- #
# GPT SKILL.md YAML frontmatter (Step 44): Copilot requires every SKILL.md to LEAD
# with a `name`+`description` frontmatter block; the provenance header sits right
# after the closing `---`.
# --------------------------------------------------------------------------- #

def _yaml_unescape(s):
    """Reverse the two escapes ConvertTo-YamlDoubleQuoted emits inside a double-quoted
    scalar: `\\"`->`"` and `\\\\`->`\\`. A single left-to-right scan (NOT sequential
    str.replace, which would double-unescape a `\\\\"` sequence). Any other backslash
    run is left literal -- the builder never emits other escapes."""
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s) and s[i + 1] in ('"', "\\"):
            out.append(s[i + 1])
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _parse_leading_frontmatter(text):
    """Parse a leading YAML frontmatter block. Returns (mapping, rest_after_block)
    or None if the text does not begin with a `---\\n ... \\n---\\n` block. Only the
    simple `key: value` scalars this builder emits are parsed; double-quoted values
    are unwrapped AND unescaped (so a description containing `"`/`\\` reports its true
    value). No third-party YAML dependency."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", len("---\n"))
    if end < 0:
        return None
    block = text[len("---\n"):end]
    fm = {}
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            continue
        val = m.group(2).strip()
        if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
            val = _yaml_unescape(val[1:-1])
        fm[m.group(1)] = val
    rest = text[end + len("\n---\n"):]
    return fm, rest


def test_gpt_skill_md_leads_with_frontmatter_then_provenance(dist_root):
    """Every GPT SKILL.md must begin with a valid YAML frontmatter block whose `name`
    equals the skill and whose `description` equals THAT skill's per-skill
    `description` in config/skill-manifest.json (single source of truth -- NOT the
    generic `<name> (skill-mesh skill).` builder stub), with the provenance header
    placed IMMEDIATELY after the closing `---`."""
    portable, _ = _skill_partition()
    marker = _marker_literal()
    desc_by_name = {s["name"]: s.get("description") for s in _load_manifest()["skills"]}
    assert portable, "expected portable skills in the manifest"
    for name in portable:
        text = (dist_root / "gpt" / name / "SKILL.md").read_text(encoding="utf-8")
        parsed = _parse_leading_frontmatter(text)
        assert parsed is not None, f"gpt/{name}/SKILL.md does not lead with YAML frontmatter"
        fm, rest = parsed
        assert fm.get("name") == name, \
            f"gpt/{name}: frontmatter name is {fm.get('name')!r}, expected {name!r}"
        # Exact equality against the manifest -- catches a manifest->frontmatter wiring
        # regression AND the generic stub fallback (which never equals the manifest
        # value). Two-sided: any other string, blank, or stub fails here.
        expected_desc = desc_by_name.get(name)
        assert expected_desc, f"manifest has no description for portable skill {name!r}"
        assert fm.get("description") == expected_desc, (
            f"gpt/{name}: frontmatter description {fm.get('description')!r} != "
            f"manifest description {expected_desc!r} "
            "(builder stub substituted or manifest->frontmatter wiring regressed)")
        assert rest.startswith("<!-- GENERATED FILE - DO NOT EDIT."), \
            f"gpt/{name}: provenance header is not immediately after the frontmatter"
        assert marker in rest, f"gpt/{name}: missing provenance marker after frontmatter"


def test_gpt_frontmatter_anchor_reds_on_missing_or_headerless_block():
    """ANCHOR: the frontmatter parser must reject a headerless file and a file whose
    body has no closing `---`, and accept a well-formed block -- otherwise the check
    above could pass on a SKILL.md that never grew frontmatter."""
    assert _parse_leading_frontmatter("<!-- GENERATED FILE -->\n# body\n") is None
    assert _parse_leading_frontmatter("---\nname: x\n# no close\n") is None
    parsed = _parse_leading_frontmatter('---\nname: x\ndescription: "d"\n---\nrest\n')
    assert parsed is not None
    fm, rest = parsed
    assert fm["name"] == "x" and fm["description"] == "d" and rest == "rest\n"


def test_claude_skill_md_not_given_synthesized_frontmatter(dist_root):
    """Claude output is unchanged: its canonical adapter already ships frontmatter, so
    the launcher still carries the Claude adapter's own `user-invocable` field -- proof
    the builder did not synthesize a fresh (name+description-only) GPT-style block over
    it."""
    text = (dist_root / "claude" / "build-phase" / "SKILL.md").read_text(encoding="utf-8")
    parsed = _parse_leading_frontmatter(text)
    assert parsed is not None, "claude SKILL.md lost its frontmatter"
    fm, _ = parsed
    assert "user-invocable" in fm, "claude frontmatter was replaced by a synthesized block"


def test_manifest_description_matches_gen_manifest_source_of_truth():
    """Done-when #3: the per-skill `description` in the COMMITTED
    config/skill-manifest.json must equal gen_manifest.py's authoritative
    DESCRIPTIONS constant for EVERY skill. A hand-edited manifest description (which a
    regen would wipe) or a generator/manifest drift on either side fails here. Runs
    with NO legacy source -- DESCRIPTIONS is an importable in-module constant."""
    descriptions = _load_gen_manifest().DESCRIPTIONS
    manifest = _load_manifest()
    names = {s["name"] for s in manifest["skills"]}

    # Every committed record's description is present in and equals the source of truth.
    mismatches = []
    for s in manifest["skills"]:
        name = s["name"]
        assert name in descriptions, \
            f"gen_manifest.DESCRIPTIONS is missing an entry for committed skill {name!r}"
        if s.get("description") != descriptions[name]:
            mismatches.append((name, s.get("description"), descriptions[name]))
    assert not mismatches, (
        "manifest/generator description drift (committed != DESCRIPTIONS): "
        f"{mismatches[:3]}")

    # Symmetric: no generator description without a committed skill, and vice-versa --
    # so a stale DESCRIPTIONS key or a manifest skill with no source of truth also reds.
    assert set(descriptions) == names, (
        "DESCRIPTIONS keys and manifest skills diverge: "
        f"only-in-gen={sorted(set(descriptions) - names)}, "
        f"only-in-manifest={sorted(names - set(descriptions))}")


def test_gpt_frontmatter_roundtrips_quotes_and_backslashes(tmp_path):
    """Finding 2 (adversarial): a manifest description containing a literal double-quote
    AND a backslash must survive ConvertTo-YamlDoubleQuoted's escaping in
    build-distributions.ps1 and round-trip to the EXACT original string in the emitted
    GPT frontmatter. Fails if the builder mis-escapes OR if the parser mis-decodes."""
    raw_desc = 'A "quoted" phrase, a back\\slash, and a colon: still ok.'
    entry = _real_skill_entry("build-phase")
    entry["description"] = raw_desc
    manifest = _write_manifest(tmp_path / "mf_desc.json", [entry])
    dist = tmp_path / "dist"
    _build_from_manifest(dist, manifest, provider="gpt")

    text = (dist / "gpt" / "build-phase" / "SKILL.md").read_text(encoding="utf-8")
    parsed = _parse_leading_frontmatter(text)
    assert parsed is not None, "generated GPT SKILL.md does not lead with frontmatter"
    fm, _ = parsed
    assert fm.get("description") == raw_desc, (
        f"description did not round-trip: emitted {fm.get('description')!r} != "
        f"original {raw_desc!r}")
    # Sanity: the raw block on disk really carries the escaped forms (proves the
    # round-trip exercised escaping, not a coincidental no-op).
    head = text[:text.find("\n---\n", 4)]
    assert '\\"' in head and "\\\\" in head, \
        "emitted frontmatter did not escape the quote/backslash -- test would be vacuous"


def test_launcher_core_reference_is_repointed_and_resolves(dist_root):
    """The launcher references the co-located core.md (not the source '../core.md'),
    and that referenced path exists in the generated tree."""
    for profile in ("claude", "gpt"):
        skill_dir = dist_root / profile / "build-phase"
        launcher = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert "../core.md" not in launcher, f"{profile}: stale ../core.md reference"
        assert "core.md" in launcher, f"{profile}: missing core.md reference"
        assert (skill_dir / "core.md").is_file(), \
            f"{profile}: referenced core.md does not exist in installed tree"


def test_build_contract_verdict_helper_reference_is_repointed(dist_root):
    for profile in ("claude", "gpt"):
        for consumer in ("build-step", "build-phase"):
            skill_dir = dist_root / profile / consumer
            core = (skill_dir / "core.md").read_text(encoding="utf-8")
            assert "../../_shared/build_step_verdict.py" not in core
            assert "build_step_verdict.py" in core
            assert (skill_dir / "build_step_verdict.py").is_file()


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #

def test_build_is_byte_identical_across_runs(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    _build(a, provider="both")
    _build(b, provider="both")
    snap_a = _tree_snapshot(a)
    snap_b = _tree_snapshot(b)
    assert set(snap_a) == set(snap_b), "file SET differs across builds"
    diffs = [k for k in snap_a if snap_a[k] != snap_b[k]]
    assert not diffs, f"non-deterministic file contents: {diffs[:5]}"


# --------------------------------------------------------------------------- #
# Install / reinstall / uninstall
# --------------------------------------------------------------------------- #

def _installed_root(home, provider):
    return Path(home) / DISCOVERY_SUBDIR[provider]


def _ledger(home):
    p = Path(home) / ".skill-mesh-install.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.mark.parametrize("provider", ["claude", "gpt"])
def test_install_places_profile_and_resolves_adapter(dist_root, tmp_path, provider):
    home = tmp_path / "home"
    r = _install(home, provider, dist_dir=dist_root)
    assert r.returncode == 0, f"install failed:\n{r.stdout}\n{r.stderr}"

    root = _installed_root(home, provider)
    launcher = (root / "build-phase" / "SKILL.md").read_text(encoding="utf-8")
    if provider == "claude":
        assert "Claude entry point" in launcher and "GPT entry point" not in launcher
    else:
        assert "GPT entry point" in launcher and "Claude entry point" not in launcher
    # relative core reference resolves inside the installed tree
    assert (root / "build-phase" / "core.md").is_file()

    led = _ledger(home)
    assert led is not None and provider in led["installs"]
    assert len(led["installs"][provider]["owned_files"]) > 0


def test_gpt_install_target_is_github_skills_not_copilot(dist_root, tmp_path):
    """Step 44 retarget: a GPT install writes to <home>/.github/skills/<skill>/ and
    NEVER to the retired project-relative <home>/.copilot/skills. Two-sided so it
    fails both if the target regresses AND if nothing is written."""
    home = tmp_path / "home"
    r = _install(home, "gpt", dist_dir=dist_root)
    assert r.returncode == 0, f"gpt install failed:\n{r.stdout}\n{r.stderr}"
    github_target = home / DISCOVERY_SUBDIR["gpt"] / "build-phase" / "SKILL.md"
    assert github_target.is_file(), \
        f"GPT install did not write to {DISCOVERY_SUBDIR['gpt']} (got no SKILL.md at {github_target})"
    retired = home / RETIRED_GPT_SUBDIR
    assert not retired.exists(), \
        f"GPT install wrote to the retired target {RETIRED_GPT_SUBDIR}"
    # the installer's own ledger records the retargeted subdir
    led = _ledger(home)
    assert led is not None and "gpt" in led["installs"]
    assert led["installs"]["gpt"]["discovery_subdir"] == DISCOVERY_SUBDIR["gpt"].as_posix()


def test_reinstall_is_idempotent(dist_root, tmp_path):
    home = tmp_path / "home"
    ledger_path = home / ".skill-mesh-install.json"
    r1 = _install(home, "claude", dist_dir=dist_root)
    assert r1.returncode == 0, r1.stderr
    root = _installed_root(home, "claude")
    snap1 = _tree_snapshot(root)
    led1 = ledger_path.read_bytes()

    r2 = _install(home, "claude", dist_dir=dist_root)
    assert r2.returncode == 0, r2.stderr
    snap2 = _tree_snapshot(root)
    led2 = ledger_path.read_bytes()

    assert set(snap1) == set(snap2), "reinstall changed the installed file set"
    assert all(snap1[k] == snap2[k] for k in snap1), "reinstall changed file contents"
    assert led1 == led2, "reinstall changed the ownership ledger (byte-identical expected)"


def test_uninstall_removes_only_owned_files(dist_root, tmp_path):
    home = tmp_path / "home"
    # Pre-seed unrelated content: a sentinel INSIDE the discovery dir + one at root.
    disco = _installed_root(home, "claude")
    sentinel = disco / "pre-existing-tool" / "SKILL.md"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text("SENTINEL-DO-NOT-TOUCH", encoding="utf-8")
    root_sentinel = home / "unrelated.txt"
    root_sentinel.write_text("also unrelated", encoding="utf-8")

    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr
    led = _ledger(home)
    owned = [Path(home) / rel for rel in led["installs"]["claude"]["owned_files"]]
    assert owned and all(p.is_file() for p in owned)

    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode == 0, f"uninstall failed:\n{ru.stdout}\n{ru.stderr}"

    # All owned files gone.
    assert not any(p.exists() for p in owned), "owned files survived uninstall"
    # Ledger removed (no installs remain).
    assert not (home / ".skill-mesh-install.json").exists()
    # Unrelated pre-existing files untouched.
    assert sentinel.is_file() and sentinel.read_text(encoding="utf-8") == "SENTINEL-DO-NOT-TOUCH"
    assert root_sentinel.is_file()
    # The pre-existing dir that held the sentinel survives (was not skill-mesh-created).
    assert sentinel.parent.is_dir()


def test_install_on_the_fly_build_without_distdir(tmp_path):
    """Installer can build the profile itself when -DistDir is omitted."""
    home = tmp_path / "home"
    r = _install(home, "gpt", dist_dir=None)
    assert r.returncode == 0, f"install (on-the-fly) failed:\n{r.stdout}\n{r.stderr}"
    root = _installed_root(home, "gpt")
    assert (root / "build-phase" / "SKILL.md").is_file()
    assert (root / "build-phase" / "core.md").is_file()
    # provider-native skill is absent from a gpt install (no misleading stub).
    _, native = _skill_partition()
    for name in native:
        assert not (root / name).exists()


def test_uninstall_when_nothing_installed_is_noop(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    r = _install(home, "claude", uninstall=True)
    assert r.returncode == 0, f"noop uninstall errored:\n{r.stdout}\n{r.stderr}"


# --------------------------------------------------------------------------- #
# Adversarial security regressions (BLOCK 1-4). Each locks in a fix so it cannot
# silently regress; every case was empirically reproduced against the scripts.
# --------------------------------------------------------------------------- #

def test_build_refuses_traversal_skill_name_and_writes_nothing_outside_dist(tmp_path):
    """BLOCK 1: a manifest 'name' that is a path-traversal segment must be rejected
    before it is joined into an output path -- and NOTHING may be written outside the
    intended dist dir."""
    dist = tmp_path / "dist"
    manifest = _write_manifest(tmp_path / "mf_name.json", [{
        "name": "..\\..\\evil",
        "status": "portable",
        "core": "skills/build-phase/core.md",
        "providers": {
            "claude": "skills/build-phase/providers/claude.md",
            "gpt": "skills/build-phase/providers/gpt.md",
        },
    }])
    r = _run(BUILD_SCRIPT, ["-ManifestPath", str(manifest),
                            "-OutputDir", str(dist), "-Provider", "claude"])
    assert r.returncode != 0, "build accepted a traversal skill name"
    # No escape artifact anywhere near the dist dir.
    assert not (tmp_path / "evil").exists()
    assert not (tmp_path.parent / "evil").exists()
    # No generated launcher escaped the dist dir.
    for skillmd in tmp_path.rglob("SKILL.md"):
        assert dist in skillmd.parents, f"SKILL.md written outside dist: {skillmd}"


def test_build_refuses_traversal_source_path(tmp_path):
    """BLOCK 2: a manifest core/providers value that escapes the canonical skills/
    root must be refused BEFORE it is read/copied into a generated file."""
    dist = tmp_path / "dist"
    # A resolvable traversal that climbs out of skills/ (and the repo) entirely.
    escaping = "skills/../../secret-outside-repo.md"
    manifest = _write_manifest(tmp_path / "mf_src.json", [{
        "name": "evilsrc",
        "status": "portable",
        "core": escaping,
        "providers": {"claude": escaping, "gpt": "skills/build-phase/providers/gpt.md"},
    }])
    r = _run(BUILD_SCRIPT, ["-ManifestPath", str(manifest),
                            "-OutputDir", str(dist), "-Provider", "claude"])
    assert r.returncode != 0, "build read a source path outside skills/"
    combined = r.stdout + r.stderr
    assert "SECURITY" in combined or "escapes" in combined
    # Nothing for the malicious skill was produced.
    assert not (dist / "claude" / "evilsrc").exists()


def test_uninstall_refuses_escaping_ledger_entry(dist_root, tmp_path):
    """BLOCK 3: the ledger is untrusted at uninstall time. A tampered owned_files
    entry that resolves OUTSIDE the install home must be skipped, and the outside
    file must SURVIVE."""
    home = tmp_path / "home"
    sibling = tmp_path / "sibling"
    sibling.mkdir()
    canary = sibling / "canary.txt"
    canary.write_text("CANARY", encoding="utf-8")

    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr

    ledger_path = home / ".skill-mesh-install.json"
    led = json.loads(ledger_path.read_text(encoding="utf-8"))
    # Tamper: append an entry that escapes the install home.
    led["installs"]["claude"]["owned_files"].append("../sibling/canary.txt")
    ledger_path.write_text(json.dumps(led), encoding="utf-8")

    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode == 0, f"uninstall errored on tampered ledger:\n{ru.stderr}"
    assert "WARNING" in ru.stderr or "outside" in (ru.stdout + ru.stderr)
    # The outside file must survive.
    assert canary.is_file() and canary.read_text(encoding="utf-8") == "CANARY"


def test_install_refuses_to_clobber_pre_existing_real_skill_file(dist_root, tmp_path):
    """BLOCK 4: a pre-existing file at a REAL skill's install path that skill-mesh did
    NOT create must never be silently owned+clobbered, and uninstall must never delete
    it. Default install REFUSES; the file is left byte-for-byte intact."""
    home = tmp_path / "home"
    target = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("CUSTOM-USER-CONTENT", encoding="utf-8")

    # Default (no -Force): refuse, write nothing, own nothing.
    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode != 0, "install silently clobbered a pre-existing real-skill file"
    assert "REFUS" in (r.stdout + r.stderr)
    assert target.read_text(encoding="utf-8") == "CUSTOM-USER-CONTENT"
    assert not (home / ".skill-mesh-install.json").exists(), "foreign file was owned"

    # A no-op uninstall must not touch it either.
    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode == 0
    assert target.read_text(encoding="utf-8") == "CUSTOM-USER-CONTENT"


def test_force_overwrites_and_owns_colliding_file(dist_root, tmp_path):
    """BLOCK 4 (opt-in): -Force is the explicit override -- it overwrites the colliding
    path AND takes ownership, so uninstall then removes it."""
    home = tmp_path / "home"
    target = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("CUSTOM-USER-CONTENT", encoding="utf-8")

    r = _install(home, "claude", dist_dir=dist_root, force=True)
    assert r.returncode == 0, f"forced install failed:\n{r.stderr}"
    assert target.read_text(encoding="utf-8") != "CUSTOM-USER-CONTENT"
    led = json.loads((home / ".skill-mesh-install.json").read_text(encoding="utf-8"))
    owned = led["installs"]["claude"]["owned_files"]
    assert any(o.endswith("build-phase/SKILL.md") for o in owned)

    # Complete the lifecycle: uninstall must actually remove the forced-owned file.
    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode == 0, f"uninstall failed:\n{ru.stderr}"
    assert not target.exists(), "forced-owned file survived uninstall"


# --------------------------------------------------------------------------- #
# Install lifecycle regressions (NEW-BLOCK A/B/D): the transactional install must
# validate before it mutates, recognize its own files on re-run, and never delete a
# pre-existing (operator-owned) directory.
# --------------------------------------------------------------------------- #

def _build_from_manifest(out_dir, manifest_path, provider="claude"):
    r = _run(BUILD_SCRIPT, ["-ManifestPath", str(manifest_path),
                            "-OutputDir", str(out_dir), "-Provider", provider])
    assert r.returncode == 0, f"custom build failed:\n{r.stdout}\n{r.stderr}"
    return out_dir


def _real_skill_entry(name):
    return {
        "name": name,
        "status": "portable",
        "core": f"skills/{name}/core.md",
        "providers": {
            "claude": f"skills/{name}/providers/claude.md",
            "gpt": f"skills/{name}/providers/gpt.md",
        },
    }


def test_refused_reinstall_is_true_noop(tmp_path):
    """NEW-BLOCK A: a reinstall that refuses (foreign collision at a NEW skill's path,
    no -Force) must be a TRUE no-op -- the prior provider's owned files survive
    byte-intact and the ledger is unchanged."""
    home = tmp_path / "home"
    small = _build_from_manifest(tmp_path / "dsmall",
                                 _write_manifest(tmp_path / "small.json",
                                                 [_real_skill_entry("build-phase")]))
    big = _build_from_manifest(tmp_path / "dbig",
                               _write_manifest(tmp_path / "big.json",
                                               [_real_skill_entry("build-phase"),
                                                _real_skill_entry("build-step")]))
    # Install the small profile (owns build-phase only).
    r = _install(home, "claude", dist_dir=small)
    assert r.returncode == 0, r.stderr
    bp = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    ledger_path = home / ".skill-mesh-install.json"
    bp_before = bp.read_bytes()
    ledger_before = ledger_path.read_bytes()

    # Plant a FOREIGN file at the NEW skill's install path, then reinstall the bigger
    # profile without -Force -> must refuse.
    foreign = home / DISCOVERY_SUBDIR["claude"] / "build-step" / "SKILL.md"
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_text("FOREIGN-BUILD-STEP", encoding="utf-8")

    r2 = _install(home, "claude", dist_dir=big)
    assert r2.returncode != 0, "reinstall over a foreign collision was not refused"
    assert "REFUS" in (r2.stdout + r2.stderr)
    # TRUE no-op: prior owned file + ledger unchanged; foreign file untouched.
    assert bp.read_bytes() == bp_before, "prior owned file was mutated by a refused reinstall"
    assert ledger_path.read_bytes() == ledger_before, "ledger changed on a refused reinstall"
    assert foreign.read_text(encoding="utf-8") == "FOREIGN-BUILD-STEP"


def test_reinstall_over_own_files_is_allowed_without_force(dist_root, tmp_path):
    """NEW-BLOCK B: skill-mesh's OWN previously-written files must never be treated as
    foreign collisions -- a re-run over them succeeds without -Force (the ledger
    records the owned set, so a resumed/repeated install recognizes them)."""
    home = tmp_path / "home"
    r1 = _install(home, "claude", dist_dir=dist_root)
    assert r1.returncode == 0, r1.stderr
    bp = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    assert bp.is_file()
    # Re-run WITHOUT -Force over skill-mesh's own files: must succeed, not refuse.
    r2 = _install(home, "claude", dist_dir=dist_root)
    assert r2.returncode == 0, f"re-run over own files was refused:\n{r2.stdout}\n{r2.stderr}"
    assert "REFUS" not in (r2.stdout + r2.stderr)
    assert bp.is_file()


def test_preexisting_empty_dirs_survive_full_uninstall(dist_root, tmp_path):
    """NEW-BLOCK D: a pre-existing EMPTY home (and an empty intermediate dir the
    operator created) must survive a full uninstall -- skill-mesh only removes dirs it
    actually created."""
    home = tmp_path / "home"
    home.mkdir()  # operator-created, empty, BEFORE any install
    other_empty = home / DISCOVERY_SUBDIR["claude"] / "other-empty-tool"
    other_empty.mkdir(parents=True)  # unrelated empty intermediate/leaf dir

    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr
    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode == 0, ru.stderr

    assert home.is_dir(), "pre-existing empty home was deleted by uninstall"
    assert other_empty.is_dir(), "pre-existing empty intermediate dir was deleted"
    # skill-mesh's own skill dir is gone.
    assert not (home / DISCOVERY_SUBDIR["claude"] / "build-phase").exists()


# --------------------------------------------------------------------------- #
# Marker-based ownership (file-content provenance is the authority, NOT the
# mutable ledger). Locks in the audit-driven class fix.
# --------------------------------------------------------------------------- #

def _disco_rel(provider, *parts):
    """POSIX rel path under the provider's discovery subdir, built from
    DISCOVERY_SUBDIR so this file carries no load-bearing '.claude/...' literal
    (tests/router/test_no_claude_dependency scans tests/ for exactly that)."""
    return DISCOVERY_SUBDIR[provider].joinpath(*parts).as_posix()


def _write_ledger(home, provider, owned, created, subdir=None):
    if subdir is None:
        subdir = DISCOVERY_SUBDIR[provider].as_posix()
    led = {
        "tool": "skill-mesh", "ledger_version": 1,
        "installs": {provider: {
            "provider": provider, "discovery_subdir": subdir,
            "owned_files": owned, "created_dirs": created,
        }},
    }
    (home / ".skill-mesh-install.json").write_text(json.dumps(led), encoding="utf-8")


def test_marker_single_source_of_truth():
    """The marker literal is defined ONCE (shared script). Neither the builder nor the
    installer may hardcode it (drift risk) -- both must go through the shared function
    and dot-source the shared script."""
    assert PROVENANCE_SCRIPT.is_file()
    marker = _marker_literal()
    for script in (BUILD_SCRIPT, INSTALL_SCRIPT):
        text = script.read_text(encoding="utf-8")
        assert marker not in text, (
            f"{script.name} hardcodes the marker literal '{marker}' -- use "
            "Get-SkillMeshMarker so the token has one source of truth")
        assert "skill-mesh-provenance.ps1" in text, (
            f"{script.name} does not dot-source the shared provenance constant")


def test_poisoned_ledger_cannot_clobber_or_delete_foreign_file(dist_root, tmp_path):
    """A file WITHOUT the marker at a target path is NEVER overwritten (no -Force) nor
    deleted by uninstall, even when the ledger explicitly lists it as owned."""
    home = tmp_path / "home"
    target = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("OPERATOR-CONTENT-NO-MARKER", encoding="utf-8")
    # Poison: claim ownership of the foreign file in the ledger.
    _write_ledger(home, "claude",
                  owned=[_disco_rel("claude", "build-phase", "SKILL.md")],
                  created=[_disco_rel("claude", "build-phase")])

    # Plain install must refuse (marker absent -> foreign), not overwrite.
    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode != 0 and "REFUS" in (r.stdout + r.stderr)
    assert target.read_text(encoding="utf-8") == "OPERATOR-CONTENT-NO-MARKER"

    # Uninstall must not delete a non-marker file even though the ledger lists it.
    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode == 0, ru.stderr
    assert target.read_text(encoding="utf-8") == "OPERATOR-CONTENT-NO-MARKER"


def test_recreated_operator_file_at_owned_path_not_clobbered(dist_root, tmp_path):
    """Ghost/recovered-operator-file: after skill-mesh owned a path, if an operator
    file (no marker) later occupies it, a plain reinstall must NOT clobber it."""
    home = tmp_path / "home"
    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr
    owned = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    assert owned.is_file()
    # Operator replaces skill-mesh's file with their own content (marker now gone).
    operator_bytes = b"MY-OWN-EDIT"
    owned.write_bytes(operator_bytes)
    r2 = _install(home, "claude", dist_dir=dist_root)
    assert r2.returncode != 0 and "REFUS" in (r2.stdout + r2.stderr)
    assert owned.read_bytes() == operator_bytes, "operator file was clobbered"


def test_partial_copy_recovery_ledger_lists_only_existing_files(dist_root, tmp_path):
    """After a mid-copy failure (simulated via an exclusive file lock), the persisted
    (recovery) owned set must list ONLY files that exist on disk -- no ghost entries
    that a later plain reinstall could clobber."""
    try:
        import msvcrt
    except ImportError:  # pragma: no cover - non-Windows
        pytest.skip("msvcrt (file locking) unavailable")

    home = tmp_path / "home"
    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr
    lockpath = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "core.md"

    f = open(lockpath, "r+b")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        r2 = _install(home, "claude", dist_dir=dist_root)
    finally:
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        f.close()

    if r2.returncode == 0:
        pytest.skip("file lock did not interrupt the copy on this host")
    led = json.loads((home / ".skill-mesh-install.json").read_text(encoding="utf-8"))
    owned = led["installs"]["claude"]["owned_files"]
    ghosts = [o for o in owned
              if not (home / Path(o.replace("/", "\\"))).exists()]
    assert not ghosts, f"recovery ledger lists non-existent (ghost) files: {ghosts}"


CORRUPT_LEDGER = '{"note":"old-shape-ledger"}'


def test_corrupt_ledger_install_self_heals_with_warning(dist_root, tmp_path):
    """A corrupt/old-shape ledger must NOT crash (PropertyNotFoundException lockout);
    install self-heals, warns LOUDLY (distinguishing corrupt from never-installed),
    and writes a fresh valid ledger."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".skill-mesh-install.json").write_text(CORRUPT_LEDGER, encoding="utf-8")
    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, f"install crashed on corrupt ledger:\n{r.stdout}\n{r.stderr}"
    assert "CORRUPT" in (r.stdout + r.stderr), "no loud corrupt-ledger diagnostic"
    assert (home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md").is_file()
    led = json.loads((home / ".skill-mesh-install.json").read_text(encoding="utf-8"))
    assert "claude" in led["installs"], "install did not write a fresh valid ledger"


def test_corrupt_ledger_uninstall_recovers_not_silently_orphan(dist_root, tmp_path):
    """If the ledger is corrupted between install and uninstall, uninstall must NOT
    silently no-op and orphan skill-mesh files -- it falls back to a marker-based scan,
    emits a loud diagnostic, and removes the marker-bearing files."""
    home = tmp_path / "home"
    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr
    disco = home / DISCOVERY_SUBDIR["claude"]
    assert len(list(disco.rglob("*.md"))) > 0
    # Corrupt the ledger AFTER install (simulates truncation/tamper).
    (home / ".skill-mesh-install.json").write_text(CORRUPT_LEDGER, encoding="utf-8")

    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode == 0, f"uninstall crashed on corrupt ledger:\n{ru.stdout}\n{ru.stderr}"
    diag = ru.stdout + ru.stderr
    assert ("lost track" in diag) or ("fallback" in diag) or ("CORRUPT" in diag), \
        "no loud lost-tracking diagnostic on corrupt-ledger uninstall"
    # The marker-based fallback must have removed the orphaned skill-mesh files.
    assert not list(disco.rglob("*.md")), "corrupt-ledger uninstall silently orphaned files"


def test_marker_false_positive_token_mention_not_owned(dist_root, tmp_path):
    """BLOCK 1: an operator file that merely MENTIONS the marker token (not a
    well-formed generated header) at a colliding path is NOT clobbered on a plain
    install and NOT deleted on uninstall, even when the ledger lists it as owned."""
    home = tmp_path / "home"
    target = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    target.parent.mkdir(parents=True)
    marker = _marker_literal()
    # Operator's own file that quotes the token in prose (no generated header block).
    operator_text = f"# My hand-authored notes\nThe {marker} token is documented here.\n"
    target.write_text(operator_text, encoding="utf-8")
    _write_ledger(home, "claude",
                  owned=[_disco_rel("claude", "build-phase", "SKILL.md")],
                  created=[_disco_rel("claude", "build-phase")])

    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode != 0 and "REFUS" in (r.stdout + r.stderr), \
        "a token-mentioning operator file was misclassified as owned and overwritten"
    assert target.read_text(encoding="utf-8") == operator_text

    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode == 0, ru.stderr
    assert target.read_text(encoding="utf-8") == operator_text, \
        "a token-mentioning operator file was deleted on uninstall"


def test_zero_file_provider_install_completes_cleanly(tmp_path):
    """BLOCK 2: a provider install that resolves to ZERO installable files (e.g. a
    manifest with only a provider-native skill under -Provider gpt) must complete
    cleanly into a fresh home -- valid empty-owned ledger, no crash."""
    manifest = _write_manifest(tmp_path / "native.json", [{
        "name": "claude-oauth-auth", "status": "provider-native", "core": None,
        "providers": {"claude": "skills/claude-oauth-auth/providers/claude.md"},
    }])
    dist = _build_from_manifest(tmp_path / "d", manifest, provider="gpt")
    assert not list((dist / "gpt").rglob("*.md")), "expected an empty gpt profile"

    home = tmp_path / "home"  # fresh, does not exist yet
    r = _install(home, "gpt", dist_dir=dist)
    assert r.returncode == 0, f"zero-file install crashed:\n{r.stdout}\n{r.stderr}"
    led = json.loads((home / ".skill-mesh-install.json").read_text(encoding="utf-8"))
    assert led["installs"]["gpt"]["owned_files"] == []


def _open_deny_delete(path):
    """Open a Windows handle to `path` with share=READ only (denies delete/write), so
    a concurrent Remove-Item raises a sharing violation. Returns a closer callable, or
    None if the handle can't be opened (test then skips cleanly)."""
    try:
        import ctypes
        from ctypes import wintypes
    except Exception:  # pragma: no cover - non-Windows
        return None
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    OPEN_EXISTING = 3
    INVALID = ctypes.c_void_p(-1).value
    CreateFileW = ctypes.windll.kernel32.CreateFileW
    CreateFileW.restype = wintypes.HANDLE
    CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                            ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    h = CreateFileW(str(path), GENERIC_READ, FILE_SHARE_READ, None, OPEN_EXISTING, 0, None)
    if not h or h == INVALID:
        return None
    return lambda: ctypes.windll.kernel32.CloseHandle(h)


def test_uninstall_partial_removal_reconciles_ledger(dist_root, tmp_path):
    """Uninstall interrupted partway (an owned file held with a delete-denying handle)
    must reconcile the ledger to list ONLY the owned files still present, so a retry
    resumes cleanly."""
    home = tmp_path / "home"
    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr
    lockpath = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "core.md"

    closer = _open_deny_delete(lockpath)
    if closer is None:
        pytest.skip("cannot open a delete-denying handle in this environment")
    try:
        ru = _install(home, "claude", uninstall=True)
    finally:
        closer()

    if ru.returncode == 0:
        pytest.skip("delete-denying handle did not interrupt the uninstall on this host")
    led = json.loads((home / ".skill-mesh-install.json").read_text(encoding="utf-8"))
    owned = led["installs"]["claude"]["owned_files"]
    # Reconciled: every listed owned file must still exist on disk (no ghost entries),
    # and the locked (un-removable) file must still be listed for a resumable retry.
    ghosts = [o for o in owned if not (home / Path(o.replace("/", "\\"))).exists()]
    assert not ghosts, f"reconciled ledger lists non-existent files: {ghosts}"
    assert any(o.endswith("build-phase/core.md") for o in owned), \
        "the un-removable owned file was dropped from the reconciled ledger"


def test_junction_on_ancestor_does_not_write_outside_home(dist_root, tmp_path):
    """Best-effort: a junction planted on an ancestor of the discovery dir must not let
    a write land outside the install home (write-time containment re-resolution).
    Skips cleanly if junctions are not creatable in the test environment."""
    home = tmp_path / "home"
    outside = tmp_path / "outside"
    outside.mkdir()
    (home / ".claude").mkdir(parents=True)
    junction = home / ".claude" / "skills"
    mk = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                        capture_output=True, text=True)
    if mk.returncode != 0 or not junction.exists():
        pytest.skip("cannot create a directory junction in this environment")

    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode != 0, "install wrote through an escaping junction"
    # Nothing skill-mesh-shaped may have landed in the outside target.
    assert not any(outside.rglob("SKILL.md")), "a file was written outside the install home"


# --------------------------------------------------------------------------- #
# Directory-removal invariant: a directory is removed ONLY if skill-mesh provably
# created it (recorded in created_dirs) AND it is empty AND inside the home. Locks in
# the round-5 class fix across every deletion path.
# --------------------------------------------------------------------------- #

def _assert_no_empty_ledger_entries(led):
    for prov, entry in led["installs"].items():
        for field in ("owned_files", "created_dirs"):
            vals = entry.get(field)
            assert isinstance(vals, list), f"{prov}.{field} is not a list: {vals!r}"
            for v in vals:
                assert isinstance(v, str) and v.strip(), \
                    f"{prov}.{field} has a null/empty entry: {vals!r}"


def test_uninstall_partial_removal_preexisting_tree_never_deletes_home(tmp_path):
    """BLOCK 1: when the ENTIRE discovery tree pre-existed the install (created_dirs is
    empty), a partial-removal-and-reconcile during uninstall must NOT persist a
    null/empty created_dirs entry, and a retry must NEVER delete the operator's
    pre-existing home directory via such an entry."""
    home = tmp_path / "home"
    # Operator pre-creates the WHOLE discovery tree (home + subdirs + the skill dir),
    # so skill-mesh creates NO directory during install -> created_dirs == [].
    skill_dir = home / DISCOVERY_SUBDIR["claude"] / "build-phase"
    skill_dir.mkdir(parents=True)
    dist = _build_from_manifest(tmp_path / "d",
                                _write_manifest(tmp_path / "m.json",
                                                [_real_skill_entry("build-phase")]),
                                provider="claude")
    r = _install(home, "claude", dist_dir=dist)
    assert r.returncode == 0, r.stderr
    led0 = json.loads((home / ".skill-mesh-install.json").read_text(encoding="utf-8"))
    assert led0["installs"]["claude"]["created_dirs"] == [], "expected empty created_dirs"

    lockpath = skill_dir / "core.md"
    closer = _open_deny_delete(lockpath)
    if closer is None:
        pytest.skip("cannot open a delete-denying handle in this environment")
    try:
        ru = _install(home, "claude", uninstall=True)  # partial: core.md un-removable
    finally:
        closer()
    if ru.returncode == 0:
        pytest.skip("delete-denying handle did not interrupt the uninstall on this host")

    led1 = json.loads((home / ".skill-mesh-install.json").read_text(encoding="utf-8"))
    _assert_no_empty_ledger_entries(led1)  # no [null]/[""] persisted
    assert led1["installs"]["claude"]["created_dirs"] == []

    # Retry uninstall to completion, then the operator's pre-existing home MUST survive.
    rr = _install(home, "claude", uninstall=True)
    assert rr.returncode == 0, rr.stderr
    assert home.is_dir(), "operator's pre-existing home directory was deleted"
    assert skill_dir.is_dir() or not skill_dir.exists()  # dir may or may not remain, but home must


def test_tampered_dotlike_created_dir_entry_never_deletes_home(tmp_path):
    """BLOCK (iter-6): a tampered ledger whose created_dirs holds a whitespace-padded /
    non-literal entry that Windows path-normalization collapses to the home root
    (e.g. ' . ') must NOT be accepted as the genuine '.' record. The home-root guard is
    exact-match, so uninstall REFUSES to delete the operator's pre-existing home. Only
    the literal '.' sentinel maps to the home root."""
    for i, poison in enumerate((" . ", ".  ", "  .", " ./ ")):
        home = tmp_path / f"home_{i}"
        home.mkdir()
        assert home.is_dir()
        ledger = {
            "tool": "skill-mesh",
            "ledger_version": 1,
            "installs": {
                "claude": {
                    "provider": "claude",
                    "discovery_subdir": DISCOVERY_SUBDIR["claude"].as_posix(),
                    "owned_files": [],
                    "created_dirs": [poison],
                }
            },
        }
        (home / ".skill-mesh-install.json").write_text(json.dumps(ledger), encoding="utf-8")
        ru = _install(home, "claude", uninstall=True)
        assert ru.returncode == 0, f"uninstall errored on tampered entry {poison!r}:\n{ru.stderr}"
        assert home.is_dir(), (
            f"tampered created_dirs entry {poison!r} deleted the operator's pre-existing home"
        )


def test_corrupt_ledger_fallback_preserves_operator_dirs(dist_root, tmp_path):
    """BLOCK 2: the corrupt-ledger marker fallback removes marker-bearing FILES only and
    NEVER removes directories -- a pre-existing operator dir, an unrelated non-marker
    file, and the shared discovery root all survive."""
    home = tmp_path / "home"
    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr
    disco = home / DISCOVERY_SUBDIR["claude"]
    op_dir = disco / "operator-tool"
    op_dir.mkdir()                                  # operator's own (empty) dir
    unrelated = disco / "operator-notes.txt"
    unrelated.write_text("my notes, no marker", encoding="utf-8")  # non-marker file

    (home / ".skill-mesh-install.json").write_text(CORRUPT_LEDGER, encoding="utf-8")
    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode == 0, ru.stderr

    # Directories (incl. shared discovery root) + the unrelated file survive.
    assert disco.is_dir(), "shared discovery root was deleted by the fallback"
    assert op_dir.is_dir(), "operator dir was deleted by the fallback"
    assert unrelated.read_text(encoding="utf-8") == "my notes, no marker"
    # skill-mesh's marker files were removed.
    assert not (disco / "build-phase" / "SKILL.md").exists()


def test_persisted_ledger_never_has_null_or_empty_entries(dist_root, tmp_path):
    """Schema guard: a persisted ledger must never contain a null/empty owned_files or
    created_dirs entry (normal install, reinstall, and a zero-file install)."""
    home = tmp_path / "home"
    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr
    _assert_no_empty_ledger_entries(
        json.loads((home / ".skill-mesh-install.json").read_text(encoding="utf-8")))

    # Zero-file provider install into a fresh home.
    home2 = tmp_path / "home2"
    manifest = _write_manifest(tmp_path / "native.json", [{
        "name": "claude-oauth-auth", "status": "provider-native", "core": None,
        "providers": {"claude": "skills/claude-oauth-auth/providers/claude.md"},
    }])
    dist = _build_from_manifest(tmp_path / "d", manifest, provider="gpt")
    r2 = _install(home2, "gpt", dist_dir=dist)
    assert r2.returncode == 0, r2.stderr
    led = json.loads((home2 / ".skill-mesh-install.json").read_text(encoding="utf-8"))
    _assert_no_empty_ledger_entries(led)
    assert led["installs"]["gpt"]["owned_files"] == []
