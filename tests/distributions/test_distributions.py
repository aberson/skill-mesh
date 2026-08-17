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
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest

PWSH = shutil.which("powershell")
# Used ONLY by the JavaScript parse gate. Its test skips (visibly) when node is absent
# rather than passing vacuously -- a green run with no parser is not evidence.
NODE = shutil.which("node")
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
# The shared payload (Step 64). D1 ships `_shared/` ONCE per profile, at the profile
# root as a sibling of the skill dirs, so every emitted `../_shared/x` reference
# resolves inside a consumer's discovery root.
# --------------------------------------------------------------------------- #

SHARED_SRC = REPO_ROOT / "_shared"
SHARED_DEST = "_shared"

# The payload as it stands today. This is a VALUE pin, not the authority on the SET:
# `test_shared_payload_matches_an_independent_closure_walk` re-derives the closure and
# compares it against a real build, so a builder walk that narrows (or widens) reds
# there even if this literal were edited to agree with it.
EXPECTED_SHARED_PAYLOAD = frozenset({
    "judge-core.md",
    "score-skill.md",
    "build_step_verdict.py",
    "calibrate_judge.py",
    "grader_prompt.py",
    "score_skill_absolute.py",
    "score_skill_composite.py",
    "score_skill.workflow.js",
    # The seven workspace references vendored in Step 66. They enter the closure the
    # same way every other asset does -- as `_shared/<leaf>` tokens harvested from the
    # canonical cores that cite them (spelled `<repo>/_shared/<leaf>` there; see
    # `Repoint-SharedReference`) -- so the independent walk below finds them without
    # being told about them.
    "intake-engine.md",
    "skill-pipeline.md",
    "skill-role-taxonomy.md",
    "step-authoring.md",
    "subagent-economy.md",
    "task-state-schema.md",
    "worktree-hygiene.md",
})

# A `_shared/<leaf>` asset reference in any spelling the canonical sources use: bare,
# or anchored at depth 2 / depth 3.
_SHARED_REF_RE = re.compile(r"(?:\.\./)*_shared/([A-Za-z0-9][A-Za-z0-9._-]*)")
# A BARE `_shared/` token -- the namespace named with no relative anchor. Mirrors
# `$BARE_SHARED_REF_RE` in the builder, INCLUDING the negative lookbehind: the
# lookbehind is what keeps `../_shared/x` (the rewrite's own output) and the provenance
# header's `<repo>/_shared/x` label from matching.
_BARE_SHARED_RE = re.compile(r"(?<![\w/\\.-])_shared/")
# pytest's default collection patterns. `dist/` is the builder's DEFAULT output
# directory and sits inside this repository's pytest rootdir with no config excluding
# it, so a shipped test module would be collected twice under a duplicate basename and
# break the project's own repo-root DONE gate.
_PYTEST_MODULE_RE = re.compile(r"\A(?:test_.*\.py|.*_test\.py)\Z")


def _independent_shared_closure(provider):
    """Re-derive the shared payload from the canonical sources, in Python.

    Deliberately a SECOND implementation of the walk `build-distributions.ps1`
    performs, so the emitted set is compared against something other than itself. A
    builder-side narrowing (or a stray new edge) shows up as a set difference here
    even if the frozen literal above were edited to match the narrowed builder.
    """
    manifest = _load_manifest()
    names = sorted(p.name for p in SHARED_SRC.iterdir() if p.is_file())
    seeds = []
    for skill in sorted(manifest["skills"], key=lambda r: r["name"]):
        core = skill.get("core")
        native = skill.get("status") == "provider-native" or core is None
        if provider == "gpt" and native:
            continue
        adapter = (skill.get("providers") or {}).get(provider)
        if not adapter:
            continue
        for rel in [adapter] + ([core] if core else []):
            seeds += _SHARED_REF_RE.findall(
                (REPO_ROOT / rel).read_text(encoding="utf-8"))

    found, queue = set(), list(seeds)
    while queue:
        leaf = queue.pop()
        if leaf in found:
            continue
        found.add(leaf)
        if not leaf.lower().endswith(".md"):
            continue  # .py/.js assets are payload leaves, not prose to follow
        body = (SHARED_SRC / leaf).read_text(encoding="utf-8")
        queue += _SHARED_REF_RE.findall(body)
        for name in names:
            # A sibling citation inside `_shared/` carries no namespace prefix -- it is
            # how judge-core.md reaches grader_prompt.py and score-skill.md reaches
            # score_skill_absolute.py.
            if name == leaf:
                continue
            if re.search(r"(?<![\w/\\.-])" + re.escape(name) + r"(?![\w-])", body):
                queue.append(name)
    return found


def _repoint_shared_asset(body):
    """The ONLY transformations the builder is permitted to apply to a payload body.

    A second implementation of `Repoint-SharedAssetReference`, deliberately spelled out
    here rather than parsed out of the `.ps1`: the content-fidelity assertion below is
    "the shipped bytes ARE the canonical asset, modulo exactly this", so re-deriving the
    modulo from the code under test would make it vacuous. Longest token first (D2).
    """
    out = body.replace("../../../_shared/", "../_shared/")
    out = out.replace("../../_shared/", "../_shared/")
    # The Step 66 spelling. Mirrored here for fidelity even though no payload source
    # carries it today -- the provenance header's `<repo>/_shared/<leaf>` label is
    # stamped AFTER the repoint, on purpose, so it is never rewritten.
    out = out.replace("<repo>/_shared/", "../_shared/")
    return _BARE_SHARED_RE.sub("../_shared/", out)


def _canonical_shared_body(name):
    """`_shared/<name>` as the builder is expected to emit its BODY.

    Read exactly as `Read-SourceText` reads it -- BOM stripped (`utf-8-sig`) and line
    endings normalized to LF -- then repointed.
    """
    raw = (SHARED_SRC / name).read_text(encoding="utf-8-sig")
    return _repoint_shared_asset(raw.replace("\r\n", "\n").replace("\r", "\n"))


_PROV_OPEN = "<!-- GENERATED FILE - DO NOT EDIT."


def _strip_provenance_header(text, name):
    """The emitted payload body with the generated header (and only it) removed.

    One branch per emitter in `build-distributions.ps1`, each asserting the placement it
    expects rather than searching loosely -- an emitter that moved the header somewhere
    else must red here, not be silently accommodated.
    """
    if name.endswith(".js"):
        # Add-JsProvenance: an optional hashbang line, then `/*` + header + `*/` + blank.
        prefix = ""
        rest = text
        if rest.startswith("#!"):
            nl = rest.index("\n") + 1
            prefix, rest = rest[:nl], rest[nl:]
        assert rest.startswith("/*\n" + _PROV_OPEN), rest[:80]
        head, sep, body = rest.partition("\n*/\n\n")
        assert sep, "the JS provenance comment is not terminated as emitted"
        return prefix + body
    if name.endswith(".py"):
        # Add-PythonProvenance: inserted INSIDE the leading docstring, right after `"""`.
        i = text.index('"""')
        head, rest = text[:i + 3], text[i + 3:]
        assert rest.startswith("\n" + _PROV_OPEN), rest[:80]
        return head + rest[rest.index("-->") + 3:]
    # Add-Provenance (markdown): prepended, then a blank line. No `_shared/` asset opens
    # with YAML frontmatter today; assert that premise instead of quietly taking the
    # other branch, which would strip nothing and make the comparison lie.
    assert not text.startswith("---\n"), f"{name} grew frontmatter; update this stripper"
    assert text.startswith(_PROV_OPEN), text[:80]
    body = text[text.index("-->") + 3:]
    assert body.startswith("\n\n"), repr(body[:20])
    return body[2:]


def _provenance_verdicts(root, tmp_path):
    """{relative posix path: bool} from the REAL Test-SkillMeshProvenance.

    Shells out to the shipped predicate rather than re-implementing the header shape
    in Python: the whole point of the .js emitter is that ONE anchored check decides
    generated-header-candidate status for every extension, so the test must ask it.
    """
    probe = tmp_path / "provenance_probe.ps1"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text(
        "param([string]$Root)\n"
        "Set-StrictMode -Version Latest\n"
        "$ErrorActionPreference = 'Stop'\n"
        f". '{PROVENANCE_SCRIPT}'\n"
        "Get-ChildItem -LiteralPath $Root -Recurse -File | "
        "Sort-Object -Property FullName | ForEach-Object {\n"
        "    $t = [System.IO.File]::ReadAllText($_.FullName)\n"
        "    $rel = $_.FullName.Substring($Root.Length).TrimStart('\\','/')\n"
        "    Write-Output (($rel -replace '\\\\','/') + '|' + "
        "(Test-SkillMeshProvenance $t))\n"
        "}\n",
        encoding="ascii")
    r = _run(probe, ["-Root", str(root)])
    assert r.returncode == 0, f"provenance probe failed:\n{r.stdout}\n{r.stderr}"
    out = {}
    for line in r.stdout.splitlines():
        if "|" not in line:
            continue
        rel, verdict = line.rsplit("|", 1)
        out[rel.strip()] = verdict.strip() == "True"
    return out


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


def _install(home, provider, dist_dir=None, uninstall=False, force=False,
             force_shared=False, backup_dir=None, env=None):
    args = ["-Home", str(home), "-Provider", provider]
    if dist_dir is not None:
        args += ["-DistDir", str(dist_dir)]
    if force:
        args.append("-Force")
    if force_shared:
        args.append("-ForceShared")
    if backup_dir is not None:
        args += ["-BackupDir", str(backup_dir)]
    if uninstall:
        args.append("-Uninstall")
    if env is None:
        return _run(INSTALL_SCRIPT, args)
    return subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(INSTALL_SCRIPT), *args],
        capture_output=True, text=True, env=env,
    )


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


def _codex_skills():
    """Names declaring a `providers.codex` path -- exactly what dist/codex may hold.

    Read from the manifest rather than spelled, because this list GROWS across Phase CP
    (0 at Step 3, 5 after Step 4's pilot, the portable catalog after the cohorts) and a
    spelled copy would have to be edited by every one of those steps.
    """
    m = _load_manifest()
    return [s["name"] for s in m["skills"] if "codex" in s.get("providers", {})]


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
    # claude: portable*(SKILL+core) + native*(SKILL only) + 2 verdict helpers
    #         + the shared payload at the profile root (Step 64);
    # gpt: portable*(SKILL+core) + 2 verdict helpers + the same shared payload.
    # RECOMPUTED, deliberately still EXACT: relaxing this to `>=` would silently
    # permit a future accidental emission, which is the whole reason the count is
    # asserted at all. The shared term is a length, not a directory listing --
    # `test_shared_payload_matches_an_independent_closure_walk` is what proves the
    # SET, from a re-walk rather than from this literal.
    shared = len(EXPECTED_SHARED_PAYLOAD)
    assert len(claude_files) == len(portable) * 2 + len(native) * 1 + 2 + shared
    assert len(gpt_files) == len(portable) * 2 + 2 + shared


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
            # canonical source path names the real source the file was copied from.
            # AMENDED for Step 64: a `_shared/`-sourced doc is not a skills/ file, so
            # asserting the `skills/` prefix over EVERY dist markdown would have been
            # false. It is narrowed per origin rather than dropped -- and the shared
            # spelling carries a `<repo>/` prefix on purpose, because a bare
            # `_shared/x` token INSIDE a shipped file is itself a reference, one that
            # resolves from the file's own directory to `_shared/_shared/x`.
            rel = md.relative_to(dist_root / profile)
            if rel.parts[0] == SHARED_DEST:
                assert f"Canonical source: <repo>/_shared/{rel.name}" in text, md
            else:
                assert "Canonical source: skills/" in text, md
            # The generated-candidate provenance marker is embedded in every file; it
            # is not standalone proof of current-byte authorship.
            assert marker in text, f"missing provenance marker in {md}"

    for profile in ("claude", "gpt"):
        for consumer in ("build-step", "build-phase"):
            helper = dist_root / profile / consumer / "build_step_verdict.py"
            text = helper.read_text(encoding="utf-8")
            assert marker in text
            assert "Canonical source: <repo>/_shared/build_step_verdict.py" in text
            compile(text, str(helper), "exec")


# --------------------------------------------------------------------------- #
# Shared payload: dist/<profile>/_shared/ (Step 64)
# --------------------------------------------------------------------------- #

def test_shared_payload_matches_an_independent_closure_walk(dist_root):
    """The emitted payload equals the closure re-derived from the canonical sources.

    Two independent derivations plus one frozen value: the builder's PowerShell walk
    (what shipped), this module's Python walk (a second implementation), and
    EXPECTED_SHARED_PAYLOAD (the value pin). Editing the literal to match a narrowed
    builder still reds, because the literal is not what the emitted set is compared to
    first.

    SCOPE, stated so a reader does not over-trust this: it compares the SET. All eight
    live assets are DIRECT seeds from `skills/**`, so a narrowing that does not change
    today's emitted set stays green here -- dropping either transitive walk edge does
    exactly that. The individual EDGES are covered by the synthetic tests below
    (`..._follows_a_sibling_mention`, `..._bare_shared_token_...`,
    `..._seeds_from_the_adapter_...`), one per edge.
    """
    for profile in ("claude", "gpt"):
        shared_dir = dist_root / profile / SHARED_DEST
        assert shared_dir.is_dir(), f"{profile}: no shared payload was emitted"
        emitted = {p.name for p in shared_dir.iterdir() if p.is_file()}
        assert emitted == _independent_shared_closure(profile), (
            f"{profile}: the emitted shared payload differs from the closure "
            "re-walked from the canonical sources")
        assert emitted == set(EXPECTED_SHARED_PAYLOAD), (
            f"{profile}: shared payload {sorted(emitted)} != the frozen expectation")
        # Nothing nested: the payload is a flat directory of leaf assets.
        assert not [p for p in shared_dir.iterdir() if p.is_dir()], \
            f"{profile}: the shared payload grew a subdirectory"


def test_shared_payload_carries_valid_provenance_for_every_extension(dist_root, tmp_path):
    """`Test-SkillMeshProvenance` is TRUE for every emitted `_shared/*` file.

    Regardless of extension, and the `.js` asset is the one that matters: a marker of
    our own JS-flavoured wording would look fine by eye while failing the shared
    generated-header-candidate check. That removes one required lifecycle guard and can
    strand emitted bytes even though a substring-only no-orphan gate reports clean.
    """
    marker = _marker_literal()
    for profile in ("claude", "gpt"):
        shared_dir = dist_root / profile / SHARED_DEST
        verdicts = _provenance_verdicts(shared_dir, tmp_path / profile)
        assert set(verdicts) == {p.name for p in shared_dir.iterdir() if p.is_file()}
        bad = sorted(rel for rel, ok in verdicts.items() if not ok)
        assert not bad, (
            f"{profile}: emitted shared assets whose provenance marker is NOT "
            f"well-formed: {bad}")
        for name in verdicts:
            text = (shared_dir / name).read_text(encoding="utf-8")
            assert marker in text, f"{profile}/{name}"
            if name.endswith(".py"):
                compile(text, name, "exec")
    # And specifically the .js: the header is wrapped VERBATIM, so the whole marker
    # block sits inside one /* */ comment and the payload below it is untouched.
    js = (dist_root / "claude" / SHARED_DEST / "score_skill.workflow.js").read_text(
        encoding="utf-8")
    assert js.startswith("/*\n<!-- GENERATED FILE - DO NOT EDIT."), js[:80]
    header, _, body = js.partition("\n*/\n")
    assert "*/" not in header, "the wrapped header would close its own comment early"
    assert body.lstrip().startswith("export const meta"), body[:80]


def test_every_generated_file_reads_owned_through_the_anchored_parser(dist_root, tmp_path):
    """`Test-SkillMeshProvenance` is TRUE for EVERY emitted file of a real build.

    The anti-stranding control for the header parser's anchors. That parser rejects a
    header that is not contiguous, not at a line start, or not at a position one of the
    build's emitters could have put it -- and the failure mode of getting any of those
    wrong is the opposite of the one they exist to prevent: a genuinely emitted file
    that fails the generated-candidate check cannot satisfy that required lifecycle
    guard and can be stranded. Nothing else in the suite would
    say so, because every other provenance assertion here is a substring check that an
    unanchored and an anchored parser both satisfy.

    Whole corpus, both profiles, every extension -- not a sample: a NEW emitter (or an
    existing one moving its header) is exactly the change that would strand files, and
    it would land as a handful of paths among two hundred."""
    for profile in ("claude", "gpt"):
        root = dist_root / profile
        verdicts = _provenance_verdicts(root, tmp_path / profile)
        expected = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
        assert set(verdicts) == expected, "the probe did not visit every emitted file"
        unowned = sorted(rel for rel, ok in verdicts.items() if not ok)
        assert not unowned, (
            f"{profile}: {len(unowned)} emitted file(s) do NOT read as skill-mesh-owned "
            f"through the shipped parser -- install would refuse them and uninstall "
            f"could never remove them: {unowned}")


def test_the_anchored_parser_rejects_a_document_that_quotes_the_header(dist_root, tmp_path):
    """A file whose SUBJECT is the marker format supplies no generated-candidate evidence.

    The header block is lifted VERBATIM out of a real emitted file, so the quoting cases
    differ from the matching case in exactly one respect: where the block sits. Content
    alone cannot separate them -- which is why the parser also anchors position, and why
    this test would be satisfied by nothing weaker.

    The stakes are not cosmetic. `_shared/` is classified per FILE by
    migrate-legacy-install.ps1. Only a candidate resident under the retired project-root
    tree can proceed toward a guarded `retire`, and only when independent plan/path/hash/
    state checks pass; active-root matches are advisory and retained."""
    src = next(p for p in (dist_root / "claude" / SHARED_DEST).iterdir()
               if p.is_file() and p.suffix == ".md")
    text = src.read_text(encoding="utf-8")
    start = text.index(_PROV_OPEN)
    header = text[start:text.index("-->", start) + 3]
    assert header.count("\n") >= 2, "the lifted header is not the multi-line block"

    probe = tmp_path / "cases"
    probe.mkdir(parents=True, exist_ok=True)
    (probe / "generated.md").write_text(header + "\n\n# body\n", encoding="utf-8")
    (probe / "quoted.md").write_text(
        "# marker format (operator notes)\n\nskill-mesh emits this header:\n\n"
        "```\n" + header + "\n```\n\nMine carry no such block.\n", encoding="utf-8")
    (probe / "scattered.md").write_text(
        "# notes\n\nThe block opens with `" + _PROV_OPEN + "`.\n\n"
        "Somewhere below it comes a line reading `Marker: " + _marker_literal() + "`,\n"
        "and the whole thing is closed by `-->`.\n", encoding="utf-8")
    # The SAME three tokens in the same order, starting at offset 0 so the position
    # anchor is satisfied and only ADJACENCY can reject it. Without this case the
    # scattered-token defect the parser was rewritten for is untested: `scattered.md`
    # above is refused by position before contiguity is ever consulted.
    (probe / "scattered_at_top.md").write_text(
        _PROV_OPEN + "\n"
        "This is the operator's own note about that opener.\n"
        "\n"
        "Marker: " + _marker_literal() + " is the line it carries.\n"
        "\n"
        "The block is terminated by -->, and that is the whole convention.\n",
        encoding="utf-8")
    # An end-anchored lazy frontmatter regex can backtrack past the FIRST close to a
    # later Markdown horizontal rule, then bless a quoted generated header as an
    # emitter-position candidate. The builder always inserts immediately after the
    # first close, so this placement is consumer prose and must not match.
    (probe / "frontmatter_then_rule_then_quoted.md").write_text(
        "---\nname: consumer\n---\n# Consumer body\n\n---\n" + header + "\n",
        encoding="utf-8")

    verdicts = _provenance_verdicts(probe, tmp_path / "run")
    assert verdicts["generated.md"] is True, \
        "a header at an emitter-legal position stopped reading as owned"
    assert verdicts["quoted.md"] is False, \
        "a doc quoting the header verbatim in its body reads as skill-mesh-owned"
    assert verdicts["scattered.md"] is False, \
        "the three header tokens scattered through prose read as one header"
    assert verdicts["scattered_at_top.md"] is False, \
        "the three header tokens scattered across a document, but starting at offset 0, " \
        "read as one contiguous header"
    assert verdicts["frontmatter_then_rule_then_quoted.md"] is False, \
        "a later Markdown rule was mistaken for the frontmatter close and a quoted " \
        "header in consumer prose read as owned"


def test_shared_payload_ships_no_pytest_module(dist_root):
    """No emitted profile contains a pytest module.

    `dist/` is the builder's default output directory and lives inside this
    repository's pytest rootdir, which has no configuration excluding it. A shipped
    `test_*.py` would therefore be collected twice, under a basename that already
    exists in `_shared/`, and error out the repo-root run this phase's DONE gate uses.
    The builder refuses to emit one; this asserts the refusal held.
    """
    for profile in ("claude", "gpt"):
        offenders = sorted(p.name for p in (dist_root / profile).rglob("*")
                           if p.is_file() and _PYTEST_MODULE_RE.match(p.name))
        assert not offenders, f"{profile} ships pytest modules: {offenders}"


def test_shared_payload_bytes_are_the_canonical_asset(dist_root):
    """CONTENT FIDELITY: the shipped bytes ARE the canonical asset.

    Every other assertion in this section checks the payload's NAMES (the closure walk),
    its MARKERS (the provenance predicate) or its REFERENCE SHAPE (the repoint). All
    three are satisfied by correctly-named, correctly-stamped, correctly-repointed
    STUBS: truncating the markdown bodies to a dozen lines takes judge-core.md from
    20,800 B to 1,681 B -- most of the remainder being the provenance header -- with
    nothing objecting. The payload IS the deliverable of this step (a consumer must be
    able to READ judge-core.md out of their own discovery root), so the bytes need a
    control of their own.

    The comparison is exact, not a floor: body after the header == canonical body,
    modulo exactly the documented transformations (BOM strip, CRLF->LF, and the
    `_shared` reference repoints) and nothing else.
    """
    mismatched = []
    for profile in ("claude", "gpt"):
        shared_dir = dist_root / profile / SHARED_DEST
        for f in sorted(shared_dir.iterdir()):
            if not f.is_file():
                continue
            emitted = _strip_provenance_header(f.read_text(encoding="utf-8"), f.name)
            expected = _canonical_shared_body(f.name)
            if emitted != expected:
                mismatched.append(
                    f"{profile}/{SHARED_DEST}/{f.name}: emitted body is "
                    f"{len(emitted)} chars, canonical is {len(expected)}")
    assert not mismatched, (
        "the emitted shared payload is not the canonical asset: " + "; ".join(mismatched))

    # The co-located verdict-helper copies are produced from the same source, with the
    # same label and the same repoint, so they cannot drift from the payload copy.
    for profile in ("claude", "gpt"):
        payload = (dist_root / profile / SHARED_DEST / "build_step_verdict.py").read_bytes()
        for consumer in ("build-step", "build-phase"):
            co = dist_root / profile / consumer / "build_step_verdict.py"
            assert co.read_bytes() == payload, \
                f"{profile}/{consumer}/build_step_verdict.py drifted from the payload copy"


def test_shared_references_are_repointed_and_resolve(dist_root):
    """Zero deep `_shared` references survive, and every emitted one resolves.

    Both halves matter and neither implies the other: a rewrite that produced
    `../_shared/x` for an asset the build does not ship would satisfy the first and
    fail the second, and a build that shipped the payload without rewriting anything
    would satisfy the second vacuously.

    WIDENED for Step 64 from `.md` to EVERY emitted file. The `.md`-only filter was a
    live blind spot, not a hypothetical one: the `.py` emit branch applied no repoint, so
    `_shared/score_skill_composite.py` shipped a bare `` `_shared/score-skill.md` ``
    token that resolves, from `dist/<p>/_shared/`, to
    `dist/<p>/_shared/_shared/score-skill.md` -- a path present in NEITHER profile. A
    reference is a reference whatever the extension of the file carrying it.
    """
    deep, unresolved, bare = [], [], []
    for profile in ("claude", "gpt"):
        profile_dir = dist_root / profile
        for f in sorted(profile_dir.rglob("*")):
            if not f.is_file():
                continue
            text = f.read_text(encoding="utf-8")
            rel = f.relative_to(profile_dir).as_posix()
            for token in ("../../_shared/", "../../../_shared/"):
                if token in text:
                    deep.append(f"{profile}/{rel}: {token}")
            # The Step 66 spelling. It is a canonical BUILD-INPUT token and must never
            # survive into an emitted file -- unrepointed it is not even a path a
            # consumer can follow. The one legitimate occurrence is the provenance
            # header's `Canonical source:` value, which names where the file came from
            # rather than citing anything, and which is stamped after the repoint.
            for m in re.finditer(r"(?<!Canonical source: )<repo>/_shared/", text):
                deep.append(f"{profile}/{rel}: <repo>/_shared/ at offset {m.start()}")
            for leaf in re.findall(r"\.\./_shared/([A-Za-z0-9][A-Za-z0-9._-]*)", text):
                if not (f.parent / ".." / "_shared" / leaf).resolve().is_file():
                    unresolved.append(f"{profile}/{rel} -> ../_shared/{leaf}")
            # BARE `_shared/x` tokens, checked inside the payload only. The asymmetry is
            # the builder's and is deliberate: a bare token in a SKILL core is frozen in
            # the link gate's allowlist as class `shared_bare` and must keep its
            # spelling, while a payload file is new in this step and owes only that its
            # own references RESOLVE.
            if rel.split("/")[0] == SHARED_DEST:
                for m in _BARE_SHARED_RE.finditer(text):
                    bare.append(f"{profile}/{rel}: ...{text[m.start():m.start() + 40]!r}")
    assert not deep, f"deep `_shared` references survived the repoint: {deep[:10]}"
    assert not unresolved, f"emitted `../_shared/x` that does not exist: {unresolved[:10]}"
    assert not bare, f"un-repointed bare `_shared/x` inside the payload: {bare[:10]}"


# The Step 66 build-input citation spelling. See `Repoint-SharedReference` for why the
# canonical cores cannot spell these citations relatively.
_REPO_ROOTED_SHARED_RE = re.compile(r"<repo>/_shared/([A-Za-z0-9][A-Za-z0-9._-]*)")

# Floor on the DERIVED pair set below. A derivation that finds nothing passes vacuously,
# and this repository has already been burned by a gate whose target list quietly emptied.
# 12 is what the tree carries today (18 occurrences over 12 keys); the floor moves only
# when a citation is deliberately retired.
MIN_VENDORED_REFERENCE_CITATIONS = 12


def _canonical_vendored_citations():
    """(skill, leaf) for every `<repo>/_shared/<leaf>` citation in the canonical cores.

    DERIVED from the tree, never hand-listed: a hand-maintained roster of what a gate is
    supposed to cover is a false green the first time someone adds a citation and not a
    row. Paired with the floor above so an empty derivation cannot pass either.
    """
    pairs = set()
    for core in sorted((REPO_ROOT / "skills").glob("*/core.md")):
        for leaf in _REPO_ROOTED_SHARED_RE.findall(core.read_text(encoding="utf-8")):
            pairs.add((core.parent.name, leaf))
    return sorted(pairs)


def test_vendored_reference_citations_reach_the_payload(dist_root):
    """Every Step 66 citation ships as a `../_shared/<leaf>` that RESOLVES, per profile.

    The canonical cores spell these citations `<repo>/_shared/<leaf>` -- a template
    placeholder, deliberately outside the reference scope of both the link gate and
    `test_skill_tree`'s reachability scan, because under the link gate's resolution
    model NO relative spelling of a `_shared` citation from `skills/<n>/core.md` can
    resolve, and the Step 63 allowlist is shrink-only so a new dangling key hard-fails.
    That places the ENTIRE correctness burden on the emit-time repoint: nothing else
    can see a typo, a dropped rewrite, or an asset that never made it into the closure.

    So this asserts the whole chain per (skill, document) pair rather than sampling it:
    the emitted core cites `../_shared/<leaf>`, the leaf exists in that profile's
    payload, and no `<repo>/` spelling survived. `test_shared_references_are_repointed_
    and_resolve` covers the negative half tree-wide; this is the positive half, and it
    is the one that fails if a citation is silently dropped instead of repointed.
    """
    pairs = _canonical_vendored_citations()
    assert len(pairs) >= MIN_VENDORED_REFERENCE_CITATIONS, (
        f"only {len(pairs)} `<repo>/_shared/` citation(s) found in skills/*/core.md, "
        f"floor is {MIN_VENDORED_REFERENCE_CITATIONS}. Either citations were retired "
        "(lower the floor deliberately, in the same commit) or the derivation stopped "
        "seeing them, which would make every assertion below vacuous.")
    # The derivation reads `skills/*/core.md` only, which is where all of Step 66's
    # citations live. An adapter carrying one would emit into SKILL.md, not core.md, so
    # the pair below would check the wrong file -- fail instead of quietly missing it.
    stray = [p.relative_to(REPO_ROOT).as_posix()
             for p in sorted((REPO_ROOT / "skills").glob("*/providers/*.md"))
             if _REPO_ROOTED_SHARED_RE.search(p.read_text(encoding="utf-8"))]
    assert not stray, (
        "an ADAPTER now carries a `<repo>/_shared/` citation, which this test's "
        f"core.md-only derivation cannot grade: {stray}. Extend the derivation to "
        "SKILL.md before landing it.")
    missing = []
    for profile in ("claude", "gpt"):
        for skill, leaf in pairs:
            core = dist_root / profile / skill / "core.md"
            if not core.is_file():
                missing.append(f"{profile}/{skill}/core.md is absent")
                continue
            text = core.read_text(encoding="utf-8")
            if f"../_shared/{leaf}" not in text:
                missing.append(f"{profile}/{skill}/core.md does not cite ../_shared/{leaf}")
            if not (dist_root / profile / SHARED_DEST / leaf).is_file():
                missing.append(f"{profile}/_shared/{leaf} was not emitted")
    assert not missing, "vendored-reference citations did not reach the payload:\n" + \
        "\n".join(missing)


def _synthetic_build_repo(tmp_path, shared_files, core_body, adapter_body=None,
                          gpt_adapter_body=None, description=None,
                          codex_adapter_body=None):
    """A minimal, fully SYNTHETIC repo the real builder can run inside.

    The builder resolves `_shared/` and `skills/` from its own `$PSScriptRoot`, so the
    only way to exercise its refusal paths is to give it a different repo. Nothing is
    planted in this checkout -- a stray file at a real source path is its own defect
    class here (#83-#86).

    `gpt_adapter_body` also declares a `gpt` provider, so a caller can build BOTH
    profiles from planted sources -- the only way to reach build-distributions.ps1's
    frontmatter PASS-THROUGH branch (a gpt adapter that already leads with `---`, so
    New-SynthesizedFrontmatter is skipped), which no real canonical source exercises
    today. `description` populates the manifest record New-SynthesizedFrontmatter
    synthesizes from.

    `codex_adapter_body` declares a `codex` provider the same way. This is THE fixture
    seam for the codex profile: Phase CP Step 3 builds the generation rails but
    deliberately authors no real `skills/*/providers/codex.md` (that is Step 4's pilot
    five), so a synthetic repo is the only honest way to prove `-Provider codex` emits
    a correct, deterministic tree. Nothing is planted in the real checkout.
    """
    repo = tmp_path / "srepo"
    for sub in ("tools", "runtime", "config", "_shared", "skills/demo/providers"):
        (repo / sub).mkdir(parents=True, exist_ok=True)
    for name in ("build-distributions.ps1", "skill-mesh-provenance.ps1"):
        shutil.copy2(REPO_ROOT / "tools" / name, repo / "tools" / name)
    shutil.copy2(REPO_ROOT / "runtime" / "path-guard.ps1",
                 repo / "runtime" / "path-guard.ps1")
    # The builder reads the durable-verdict helper unconditionally (it only SKIPS the
    # per-consumer copy when the consumer skill is absent), so the synthetic tree must
    # carry one. It is never part of the closure here: nothing cites it.
    (repo / "_shared" / "build_step_verdict.py").write_text(
        '"""synthetic verdict helper."""\n\nVERDICT = "ok"\n', encoding="utf-8")
    (repo / "skills" / "demo" / "core.md").write_text(core_body, encoding="utf-8")
    (repo / "skills" / "demo" / "providers" / "claude.md").write_text(
        adapter_body or "# demo adapter\n\nLoads ../core.md in full.\n", encoding="utf-8")
    for name, body in shared_files.items():
        (repo / "_shared" / name).write_text(body, encoding="utf-8")
    entry = {
        "name": "demo", "status": "portable", "core": "skills/demo/core.md",
        "providers": {"claude": "skills/demo/providers/claude.md"},
    }
    if gpt_adapter_body is not None:
        (repo / "skills" / "demo" / "providers" / "gpt.md").write_text(
            gpt_adapter_body, encoding="utf-8")
        entry["providers"]["gpt"] = "skills/demo/providers/gpt.md"
    if codex_adapter_body is not None:
        (repo / "skills" / "demo" / "providers" / "codex.md").write_text(
            codex_adapter_body, encoding="utf-8")
        entry["providers"]["codex"] = "skills/demo/providers/codex.md"
    if description is not None:
        entry["description"] = description
    _write_manifest(repo / "config" / "skill-manifest.json", [entry])
    return repo


def _synthetic_build(repo, out_dir, provider="claude"):
    return _run(repo / "tools" / "build-distributions.ps1",
                ["-OutputDir", str(out_dir), "-Provider", provider])


def test_shared_closure_follows_a_sibling_mention(tmp_path):
    """An asset reached only through a `_shared/*.md` sibling citation still ships.

    This is the transitive half of the walk, and it is the half a "just ship what the
    skills cite" implementation silently drops: `judge-core.md` names
    `grader_prompt.py` as a bare sibling, with no `_shared/` prefix to match on.
    """
    repo = _synthetic_build_repo(
        tmp_path,
        {"doc.md": "# doc\n\nRuns [`helper.py`](helper.py) for grading.\n",
         "helper.py": '"""helper."""\n\nVALUE = 1\n'},
        "# demo core\n\nSee `_shared/doc.md`.\n")
    out = tmp_path / "out"
    r = _synthetic_build(repo, out)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    emitted = {p.name for p in (out / "claude" / SHARED_DEST).iterdir() if p.is_file()}
    assert emitted == {"doc.md", "helper.py"}, emitted


def test_bare_shared_token_inside_a_shared_asset_is_repointed(tmp_path):
    """A bare `_shared/x` token inside a SHIPPED asset is normalized to `../_shared/x`.

    Left alone it would resolve, from `dist/<p>/_shared/`, to
    `dist/<p>/_shared/_shared/x` -- a brand new dangling reference introduced by the
    very step that exists to remove them.
    """
    repo = _synthetic_build_repo(
        tmp_path,
        {"doc.md": "# doc\n\nRun `_shared/helper.py` to grade.\n",
         "helper.py": '"""helper."""\n\nVALUE = 1\n'},
        "# demo core\n\nSee `_shared/doc.md`.\n")
    out = tmp_path / "out"
    assert _synthetic_build(repo, out).returncode == 0
    # WALK EDGE (b): the anchored `_shared/<leaf>` token is the ONLY way helper.py can
    # reach this closure -- the bare-sibling edge cannot see it, because its negative
    # lookbehind rejects the `/`-prefixed occurrence. Without this line the whole edge
    # has no control at all: the repoint below is unconditional, so it stays green with
    # `$next = @(Get-SharedLeafReference $body)` replaced by `@()`.
    assert (out / "claude" / SHARED_DEST / "helper.py").is_file(), \
        "the anchored `_shared/x` walk edge did not pull the asset into the closure"
    emitted = (out / "claude" / SHARED_DEST / "doc.md").read_text(encoding="utf-8")
    assert "`../_shared/helper.py`" in emitted, emitted
    # ...and idempotently: no `../_shared/../_shared/` or `.././_shared/` mangling.
    assert emitted.count("../_shared/helper.py") == 1
    assert "_shared/_shared/" not in emitted
    # The provenance header's own canonical-source value must survive the repoint.
    assert "Canonical source: <repo>/_shared/doc.md" in emitted


def test_repo_rooted_shared_citation_is_seeded_and_repointed(tmp_path):
    """ANCHOR for the Step 66 spelling, on a synthetic tree: `<repo>/_shared/x`.

    Two independent claims, both of which a one-line regression would break silently on
    the live tree (the citation is out of BOTH gates' reference scope by construction):

      * the closure SEES it. `$SHARED_REF_RE` has no lookbehind, so the `_shared/<leaf>`
        substring inside `<repo>/_shared/<leaf>` is harvested as a seed -- which is also
        why a mistyped leaf throws in `Get-SharedClosure` instead of shipping.
      * the emit REPOINTS it to `../_shared/<leaf>`, the one spelling that resolves one
        level below a discovery root. Dropping the third `.Replace` in
        `Repoint-SharedReference` leaves `<repo>/_shared/x` in the shipped core: a
        reference no consumer can follow, and one no scope-based gate reports.
    """
    repo = _synthetic_build_repo(
        tmp_path,
        {"vendored.md": "# vendored\n\nWorkspace doctrine.\n"},
        "# demo core\n\nSize each step per `<repo>/_shared/vendored.md` section 1.\n")
    out = tmp_path / "out"
    r = _synthetic_build(repo, out)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert (out / "claude" / SHARED_DEST / "vendored.md").is_file(), \
        "the `<repo>/_shared/<leaf>` citation did not seed the closure"
    emitted = (out / "claude" / "demo" / "core.md").read_text(encoding="utf-8")
    assert "`../_shared/vendored.md`" in emitted, emitted
    assert "<repo>/_shared/" not in emitted, \
        "the `<repo>/_shared/` build-input spelling survived into the emitted core"
    assert (out / "claude" / "demo" / ".." / "_shared" / "vendored.md").resolve().is_file()


def test_mistyped_repo_rooted_shared_citation_throws_the_build(tmp_path):
    """RED-ON-GARBAGE for the Step 66 spelling: a typo must fail the build, loudly.

    The positive half is covered three ways (the two tests above plus the live-tree pair
    walk). None of them can fail if the protection itself is gone, and for THIS spelling
    the protection is singular: `<repo>/_shared/<leaf>` is exempted from both link gates
    by the `<>*` template-placeholder rule, so unlike `../_shared/x`, `../../_shared/x`
    and bare `_shared/x` there is no second line of defense behind the build-time throw
    in `Get-SharedClosure`. The decision record leans on that throw as the whole
    replacement for D5's abandoned link-form validation, so the throw needs its own
    anchor: without this test, deleting the `Test-Path` guard leaves every other
    assertion in this file green while a mistyped citation ships as a reference no
    consumer can follow.
    """
    repo = _synthetic_build_repo(
        tmp_path,
        {"vendored.md": "# vendored\n\nWorkspace doctrine.\n"},
        # One character off: `vendoredd.md` does not exist in `_shared/`.
        "# demo core\n\nSize each step per `<repo>/_shared/vendoredd.md` section 1.\n")
    out = tmp_path / "out"
    r = _synthetic_build(repo, out)
    assert r.returncode != 0, (
        "the builder accepted a `<repo>/_shared/<leaf>` citation whose leaf does not "
        f"exist -- a typo in this spelling now ships green:\n{r.stdout}\n{r.stderr}")
    combined = f"{r.stdout}\n{r.stderr}"
    assert "shared asset source missing" in combined, (
        "the build failed, but not with the seeding throw -- this anchor is no longer "
        f"proving what it claims:\n{combined}")
    assert "vendoredd.md" in combined, \
        f"the failure does not name the missing leaf, so it is not actionable:\n{combined}"
    # ...and the payload the citation named is not there. MEASURED ordering, recorded
    # rather than wished for: the builder emits each skill's files BEFORE it resolves
    # the shared closure, so a refused build does leave a partial `dist/` behind. That
    # is safe only because the run exits non-zero and every consumer of `dist/`
    # (`tools/release.ps1`, the installer) branches on that -- so the assertion here is
    # the one that is actually true, not the one that sounds tidier.
    assert not (out / "claude" / SHARED_DEST / "vendoredd.md").is_file()
    assert not (out / "claude" / SHARED_DEST / "vendored.md").is_file(), \
        "the closure shipped assets despite refusing one of its seeds"


def test_shared_closure_seeds_from_the_adapter_as_well_as_the_core(tmp_path):
    """WALK EDGE: the seed harvest reads the ADAPTER body, not only the core body.

    judge-motion is `core: null` and cites the payload from its adapter alone, so an
    implementation that harvested seeds from cores only would drop that skill's payload.
    On the live tree the loss is invisible -- every asset judge-motion cites is also
    cited by some skill that HAS a core -- so the edge needs a fixture where the adapter
    is the only citer.
    """
    repo = _synthetic_build_repo(
        tmp_path,
        {"doc.md": "# doc\n\nDoctrine.\n"},
        "# demo core\n\nNo shared citation here.\n",
        adapter_body="# demo adapter\n\nLoads ../core.md in full. See `_shared/doc.md`.\n")
    out = tmp_path / "out"
    r = _synthetic_build(repo, out)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    shared_dir = out / "claude" / SHARED_DEST
    assert shared_dir.is_dir(), "an adapter-only citation shipped no payload at all"
    emitted = {p.name for p in shared_dir.iterdir() if p.is_file()}
    assert emitted == {"doc.md"}, emitted


@pytest.mark.skipif(NODE is None, reason="node is not available on PATH")
def test_emitted_javascript_still_parses(dist_root, tmp_path):
    """PARSE validity, which provenance validity does not imply.

    `Add-JsProvenance` displaces whatever was on line 1. Nothing else in `tests/` runs a
    JavaScript parser, so an unparseable-but-marker-valid `.js` would ship green: the
    parser would see a generated-looking candidate (not standalone mutation authority),
    while the consumer would get a file their runtime refuses to load.
    """
    real = dist_root / "claude" / SHARED_DEST / "score_skill.workflow.js"
    r = subprocess.run([NODE, "--check", str(real)], capture_output=True, text=True)
    assert r.returncode == 0, f"the emitted payload .js does not parse:\n{r.stderr}"

    # The latent case the real asset does not exercise: a `#!` hashbang is legal ONLY on
    # line 1, so a prepended comment block makes the file unparseable.
    repo = _synthetic_build_repo(
        tmp_path,
        {"tool.js": "#!/usr/bin/env node\nconst x = 1;\nconsole.log(x);\n"},
        "# demo core\n\nSee `_shared/tool.js`.\n")
    out = tmp_path / "out"
    rb = _synthetic_build(repo, out)
    assert rb.returncode == 0, f"{rb.stdout}\n{rb.stderr}"
    emitted = out / "claude" / SHARED_DEST / "tool.js"
    text = emitted.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env node\n"), text[:60]
    assert _marker_literal() in text, "the hashbang branch dropped the provenance marker"
    rc = subprocess.run([NODE, "--check", str(emitted)], capture_output=True, text=True)
    assert rc.returncode == 0, f"a stamped hashbang .js does not parse:\n{rc.stderr}"


def test_builder_refuses_a_shared_asset_it_cannot_stamp(tmp_path):
    """An asset with no provenance emitter fails the BUILD, loudly.

    Copying it unstamped would plant a file the installer cannot own and uninstall
    cannot remove -- an orphan that a no-orphan gate still reports as clean.
    """
    repo = _synthetic_build_repo(
        tmp_path,
        {"notes.txt": "plain text asset\n"},
        "# demo core\n\nSee `_shared/notes.txt`.\n")
    r = _synthetic_build(repo, tmp_path / "out")
    assert r.returncode != 0, "an unstampable shared asset was shipped silently"
    assert "no provenance emitter" in (r.stdout + r.stderr)


def test_builder_refuses_to_ship_a_pytest_module(tmp_path):
    """A `_shared/*.md` that names its unit-test module must not drag it into dist/.

    `dist/` is the default output directory and sits inside this repository's pytest
    rootdir, so a shipped `test_*.py` is collected a second time under a duplicate
    basename and errors out the repo-root DONE gate.
    """
    repo = _synthetic_build_repo(
        tmp_path,
        {"doc.md": "# doc\n\nFixtures live in `test_helper.py`.\n",
         "test_helper.py": '"""tests."""\n\ndef test_x():\n    assert True\n'},
        "# demo core\n\nSee `_shared/doc.md`.\n")
    r = _synthetic_build(repo, tmp_path / "out")
    assert r.returncode != 0, "a pytest module was shipped into a discovery profile"
    assert "pytest module" in (r.stdout + r.stderr)


def test_core_null_adapter_is_repointed_at_depth_three(dist_root):
    """judge-motion is `core: null`, and its ADAPTER carries depth-3 `_shared` refs.

    The rewrite must not be gated on the skill having a core, and it must be
    longest-token-first: `../../../_shared/` literally contains `../../_shared/`, so a
    two-dot-first replace leaves `../_shared/` prefixed by a stray `../` -- still
    broken, and nothing else in this file would notice.
    """
    _, native = _skill_partition()
    assert "judge-motion" in native, "judge-motion is no longer provider-native"
    source = (SKILLS_ROOT / "judge-motion" / "providers" / "claude.md").read_text(
        encoding="utf-8")
    assert "../../../_shared/" in source, \
        "the depth-3 fixture this test relies on is gone from the canonical adapter"

    launcher = dist_root / "claude" / "judge-motion" / "SKILL.md"
    text = launcher.read_text(encoding="utf-8")
    assert not (launcher.parent / "core.md").exists(), "judge-motion gained a core.md"
    assert "../../../_shared/" not in text and "../../_shared/" not in text
    leaves = set(re.findall(r"\.\./_shared/([A-Za-z0-9][A-Za-z0-9._-]*)", text))
    assert leaves, "judge-motion's depth-3 references vanished instead of being repointed"
    for leaf in sorted(leaves):
        assert (dist_root / "claude" / SHARED_DEST / leaf).is_file(), leaf


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


# --------------------------------------------------------------------------- #
# STRICT YAML frontmatter on the EMITTED profiles (Step 68, #69).
#
# `_parse_leading_frontmatter` above is deliberately tolerant -- it is the in-repo
# `key: value` reader, and it happily parsed the unquoted colon-bearing `argument:`
# value that Copilot CLI REJECTED. The gates below run the emitted bytes through a
# real strict parser (PyYAML, a declared Environment requirement), using the same
# contract module the canonical-source gate uses, so producer and consumer are graded
# by ONE set of rules rather than two that drift.
# --------------------------------------------------------------------------- #

_FRONTMATTER_CONTRACT_PATH = (
    REPO_ROOT / "tests" / "package-integrity" / "frontmatter_contract.py")


def _frontmatter_contract():
    """Import the ONE owner of the frontmatter contract (tests/package-integrity/
    frontmatter_contract.py) by path -- the two suite directories are not a package.
    Mirrors _load_gen_manifest's loader. Deliberately NOT a local copy of the rules."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "frontmatter_contract_under_test", _FRONTMATTER_CONTRACT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _yaml_double_quoted(value):
    """The author-side spelling of a YAML double-quoted scalar, mirroring
    ConvertTo-YamlDoubleQuoted in build-distributions.ps1. Used to WRITE a planted
    adapter, never to grade one -- the grading is PyYAML's."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


# The planted values. Colon-bearing on BOTH string keys (the #69 shape), plus a
# literal double-quote to prove escaping survives the trip, and a real boolean whose
# identity is asserted after the round-trip.
_PLANTED_FRONTMATTER = {
    "name": "demo",
    "description": 'Audits a thing: carefully, including a "quoted" clause.',
    "user-invocable": True,
    "argument": "Optional flags: --project <name-or-path> (default: innermost)",
}

_PLANTED_ADAPTER_BODY = (
    "---\n"
    f"name: {_PLANTED_FRONTMATTER['name']}\n"
    f"description: {_yaml_double_quoted(_PLANTED_FRONTMATTER['description'])}\n"
    "user-invocable: true\n"
    f"argument: {_yaml_double_quoted(_PLANTED_FRONTMATTER['argument'])}\n"
    "---\n"
    "\n# demo adapter\n\nLoads ../core.md in full.\n"
)


def test_every_emitted_skill_md_frontmatter_survives_a_strict_yaml_parse(dist_root):
    """What a host actually parses. Claude launchers pass the canonical adapter's own
    block through verbatim; GPT launchers carry the synthesized `name`+`description`
    block. Both must parse strictly, carry only allowlisted keys, and keep
    `user-invocable` a real boolean."""
    fc = _frontmatter_contract()
    portable, native = _skill_partition()
    # Per-profile expected launcher count, derived from the manifest rather than
    # spelled: claude carries every skill, gpt carries the portable ones. No `codex`
    # entry here -- `dist_root` builds -Provider both, which is claude + gpt BY DESIGN
    # (see the $profiles comment in build-distributions.ps1) and never produces a
    # dist/codex to grade. The codex profile has its own dedicated coverage below,
    # built from the synthetic fixture repo; a third dict entry here would be dead code
    # dressed as codex coverage, since the loop below only ever iterates these two.
    expected = {"claude": len(portable) + len(native), "gpt": len(portable)}
    allowed = {"claude": fc.CLAUDE_KEYS, "gpt": fc.GPT_KEYS}
    failures = []
    for profile in ("claude", "gpt"):
        launchers = sorted((dist_root / profile).glob("*/SKILL.md"))
        assert len(launchers) == expected[profile], (
            f"{profile}: {len(launchers)} launchers emitted, manifest declares "
            f"{expected[profile]} -- this gate would grade the wrong file set")
        for path in launchers:
            text = path.read_text(encoding="utf-8")
            for defect in fc.frontmatter_defects(text, allowed_keys=allowed[profile]):
                failures.append(f"{profile}/{path.parent.name}/SKILL.md: {defect}")
    assert not failures, (
        "emitted SKILL.md frontmatter violates the strict-YAML contract:\n  "
        + "\n  ".join(failures))


def test_emitted_frontmatter_gate_reds_on_an_unquoted_colon_bearing_value(dist_root):
    """ANCHOR on REAL emitted bytes: strip the quotes the fix added to context-slim's
    colon-bearing `argument` and the gate must go red. Without this, the check above
    could be passing because it never actually reaches the frontmatter through the
    provenance header that follows it."""
    fc = _frontmatter_contract()
    text = (dist_root / "claude" / "context-slim" / "SKILL.md").read_text(
        encoding="utf-8")
    assert fc.frontmatter_defects(text) == [], fc.frontmatter_defects(text)
    block, _ = fc.split_frontmatter(text)
    line = next(ln for ln in block.splitlines() if ln.startswith("argument:"))
    assert ': "' in line, (
        "context-slim's emitted `argument` is no longer quoted at the source -- the "
        "probe below would not be planting the #69 defect")
    unquoted = line.replace('argument: "', "argument: ").rstrip('"')
    broken = text.replace(line, unquoted, 1)
    assert broken != text, "the probe did not change the emitted block"
    defects = fc.frontmatter_defects(broken)
    assert any("not valid YAML" in d for d in defects), defects


def test_planted_colon_bearing_pair_round_trips_in_both_profiles(tmp_path):
    """Done-when, both halves: a planted colon-bearing `description` AND `argument`
    reach both emitted profiles byte-intact through a STRICT parse.

    The GPT half also covers build-distributions.ps1's frontmatter pass-through branch
    (an adapter that already leads with `---` skips New-SynthesizedFrontmatter), which no
    canonical source reaches today and which nothing tested before this step."""
    fc = _frontmatter_contract()
    body = _PLANTED_ADAPTER_BODY
    repo = _synthetic_build_repo(
        tmp_path, {}, "# demo core\n\nNo shared payload.\n",
        adapter_body=body, gpt_adapter_body=body,
        description="a synthesized description that must NOT appear")
    out = tmp_path / "out"
    r = _synthetic_build(repo, out, provider="both")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    for profile in ("claude", "gpt"):
        text = (out / profile / "demo" / "SKILL.md").read_text(encoding="utf-8")
        assert fc.frontmatter_defects(text) == [], \
            f"{profile}: {fc.frontmatter_defects(text)}"
        fm = fc.parse_frontmatter(text)
        assert fm == _PLANTED_FRONTMATTER, (
            f"{profile}: planted frontmatter did not round-trip: {fm!r} != "
            f"{_PLANTED_FRONTMATTER!r}")
        # Identity, not truthiness: the string 'true' would satisfy `assert fm[...]`.
        assert fm["user-invocable"] is True, \
            f"{profile}: user-invocable is {fm['user-invocable']!r}, not the bool True"
        # Exactly ONE block: the pass-through branch must not stack a synthesized
        # block on top of the adapter's own, and the provenance header sits right
        # after the closing fence.
        _, rest = fc.split_frontmatter(text)
        assert rest.startswith("<!-- GENERATED FILE - DO NOT EDIT."), \
            f"{profile}: provenance header is not immediately after the frontmatter"
        assert fc.split_frontmatter(rest) is None, \
            f"{profile}: a second frontmatter block was stacked on the first"
        assert "a synthesized description that must NOT appear" not in text, \
            f"{profile}: the builder synthesized a block over the adapter's own"


def test_gpt_synthesized_frontmatter_survives_a_strict_yaml_parse(tmp_path):
    """The other GPT path: New-SynthesizedFrontmatter synthesizing from a manifest description
    that is FULL of colons. `_parse_leading_frontmatter` cannot prove this -- it would
    accept a block a strict parser rejects. PyYAML can."""
    fc = _frontmatter_contract()
    raw_desc = ('Three modes: --small (default: quick wins), --big, and --uat: '
                'pick exactly one.')
    entry = _real_skill_entry("build-phase")
    entry["description"] = raw_desc
    manifest = _write_manifest(tmp_path / "mf_strict.json", [entry])
    dist = tmp_path / "dist"
    _build_from_manifest(dist, manifest, provider="gpt")

    text = (dist / "gpt" / "build-phase" / "SKILL.md").read_text(encoding="utf-8")
    assert fc.frontmatter_defects(text, allowed_keys=fc.GPT_KEYS) == [], \
        fc.frontmatter_defects(text, allowed_keys=fc.GPT_KEYS)
    assert fc.parse_frontmatter(text)["description"] == raw_desc, (
        "colon-bearing description did not round-trip through the strict parse: "
        f"{fc.parse_frontmatter(text)['description']!r} != {raw_desc!r}")


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
    entry = led["installs"][provider]
    assert len(entry["owned_files"]) > 0
    assert set(entry["owned_file_hashes"]) == set(entry["owned_files"])
    assert all(re.fullmatch(r"[0-9a-f]{64}", h)
               for h in entry["owned_file_hashes"].values())


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


@pytest.mark.parametrize("forge_hash", [False, True], ids=["unhashed", "hash-forged"])
def test_uninstall_refuses_escaping_ledger_entry(dist_root, tmp_path, forge_hash):
    """BLOCK 3: the ledger is untrusted at uninstall time. An owned_files entry that
    resolves OUTSIDE the install home grants NO removal authority at all: uninstall
    fails closed, the refusal NAMES the escaping row, and nothing is touched anywhere
    -- not the outside file, not the installed tree, not the ledger.

    Authority is all-or-nothing, per Get-ValidOwnedHashMap's own contract: "A
    partially useful-looking legacy/tampered map grants no destructive authority,
    because selecting only its convenient rows would silently bless an ambiguous
    ledger shape." Skipping the bad row and deleting the rest IS selecting the
    convenient rows, so this test asserts refusal rather than a warned partial run.

    Both tamper shapes are covered:

    * ``unhashed`` -- the row is appended to owned_files alone, so the
      owned_files/owned_file_hashes bijection breaks. (The shape a naive tamperer
      produces, and the one this test carried before the map became authority.)
    * ``hash-forged`` -- the row is appended WITH a syntactically valid 64-hex
      hash, so the bijection survives and the escaping PATH is the only thing left
      that can reject it. This is the strictly more capable attacker, and it is the
      shape that isolates the containment check inside Get-ValidOwnedHashMap
      (Assert-ProviderTargetDomain) as the thing doing the work -- the bijection
      dimension alone is already covered by
      test_invalid_owned_hash_maps_never_authorize_uninstall.
    """
    home = tmp_path / "home"
    sibling = tmp_path / "sibling"
    sibling.mkdir()
    canary = sibling / "canary.txt"
    canary.write_text("CANARY", encoding="utf-8")

    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr

    disco = home / DISCOVERY_SUBDIR["claude"]
    before_tree = _tree_snapshot(disco)
    ledger_path = home / ".skill-mesh-install.json"
    led = json.loads(ledger_path.read_text(encoding="utf-8"))
    # Tamper: append an entry that escapes the install home.
    escaping = "../sibling/canary.txt"
    led["installs"]["claude"]["owned_files"].append(escaping)
    if forge_hash:
        led["installs"]["claude"]["owned_file_hashes"][escaping] = \
            hashlib.sha256(canary.read_bytes()).hexdigest()
    ledger_path.write_text(json.dumps(led), encoding="utf-8")
    before_ledger = ledger_path.read_bytes()

    ru = _install(home, "claude", uninstall=True)
    combined = ru.stdout + ru.stderr
    assert ru.returncode != 0, f"a tampered ledger authorized deletion:\n{combined}"
    assert "REFUS" in combined, combined
    # The escape must be NAMED, not buried under a generic malformed-map message.
    assert "WARNING" in ru.stderr and "outside" in combined, combined
    assert escaping in combined, combined
    # The outside file must survive...
    assert canary.is_file() and canary.read_text(encoding="utf-8") == "CANARY"
    # ...and so must everything else: a refusal is a true no-op.
    assert _tree_snapshot(disco) == before_tree
    assert ledger_path.read_bytes() == before_ledger


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

    backup = tmp_path / "backup"
    before = target.read_bytes()
    r = _install(home, "claude", dist_dir=dist_root, force=True, backup_dir=backup)
    assert r.returncode == 0, f"forced install failed:\n{r.stderr}"
    assert target.read_text(encoding="utf-8") != "CUSTOM-USER-CONTENT"
    run_dir, manifest = _backup_runs(backup)[0]
    row = next(f for f in manifest["files"] if f["rel_path"].endswith("build-phase/SKILL.md"))
    assert (run_dir / row["backup_rel"]).read_bytes() == before
    led = json.loads((home / ".skill-mesh-install.json").read_text(encoding="utf-8"))
    owned = led["installs"]["claude"]["owned_files"]
    assert any(o.endswith("build-phase/SKILL.md") for o in owned)

    # Complete the lifecycle: uninstall must actually remove the forced-owned file.
    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode == 0, f"uninstall failed:\n{ru.stderr}"
    assert not target.exists(), "forced-owned file survived uninstall"


# --------------------------------------------------------------------------- #
# -ForceShared: SCOPED take-ownership of the `_shared/` payload (Step 64).
#
# The real consumer home already holds a hand-authored `_shared/` tree whose files
# carry no marker, so the first install after this step would REFUSE outright. The
# four guardrails the decision requires -- back up first, scope to the payload, leave
# every other file byte-unchanged, and prove ownership actually landed -- each get an
# assertion here.
# --------------------------------------------------------------------------- #

_PRESEEDED_PAYLOAD = "judge-core.md"          # collides with the shipped payload
_PRESEEDED_BYSTANDER = "README.md"            # in `_shared/`, but not shipped


def _backup_runs(backup):
    """Every take-ownership manifest under a `-BackupDir`, as parsed JSON.

    Each RUN owns a `<provider>-<run id>/` subdirectory (the sibling migrator's
    precedent), so this returns a LIST: a `-BackupDir` legitimately holds more than one
    record, and the whole point of the per-run scoping is that a second run cannot
    replace the first one's.
    """
    out = []
    for m in sorted(Path(backup).glob("*/take-ownership-backup.json")):
        out.append((m.parent, json.loads(m.read_text(encoding="utf-8"))))
    return out


def _make_junction(link, target):
    """A real NTFS directory junction (no admin rights needed, unlike a symlink)."""
    Path(target).mkdir(parents=True, exist_ok=True)
    Path(link).parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"mklink failed: {r.stdout}\n{r.stderr}"


def _preseed_shared(home, provider="claude"):
    """A consumer `_shared/` holding one colliding file and one bystander, no markers."""
    shared = _installed_root(home, provider) / "_shared"
    shared.mkdir(parents=True, exist_ok=True)
    payload = shared / _PRESEEDED_PAYLOAD
    bystander = shared / _PRESEEDED_BYSTANDER
    payload.write_text("# operator's own judge doctrine\n", encoding="utf-8")
    bystander.write_text("# operator's own shared README\n", encoding="utf-8")
    return payload, bystander


def test_force_shared_backs_up_takes_ownership_and_spares_bystanders(dist_root, tmp_path):
    home = tmp_path / "home"
    backup = tmp_path / "backup"
    payload, bystander = _preseed_shared(home)
    before_payload = payload.read_bytes()
    before_bystander = bystander.read_bytes()

    # GUARDRAIL 1 + 2: authorized because the collision is inside the payload.
    r = _install(home, "claude", dist_dir=dist_root, force_shared=True, backup_dir=backup)
    assert r.returncode == 0, f"scoped take-ownership failed:\n{r.stdout}\n{r.stderr}"

    # GUARDRAIL 1: the pre-overwrite bytes, hash and size are recorded and restorable.
    runs = _backup_runs(backup)
    assert len(runs) == 1, [str(d) for d, _ in runs]
    run_dir, manifest = runs[0]
    rows = {f["rel_path"]: f for f in manifest["files"]}
    rel = next(k for k in rows if k.endswith(f"_shared/{_PRESEEDED_PAYLOAD}"))
    assert rows[rel]["sha256"] == hashlib.sha256(before_payload).hexdigest()
    assert rows[rel]["size_bytes"] == len(before_payload)
    assert (run_dir / "files" / rel).read_bytes() == before_payload, \
        "the backup does not hold the ORIGINAL bytes"
    assert not any(k.endswith(_PRESEEDED_BYSTANDER) for k in rows), \
        "a file that was never overwritten was recorded as taken over"

    # GUARDRAIL 3: the non-payload file in the same directory is byte-unchanged. This
    # is a per-FILE claim, never a directory-wide one.
    assert bystander.read_bytes() == before_bystander

    # GUARDRAIL 4: ownership actually landed -- marker in the bytes AND in owned_files,
    # so uninstall can remove it. Ownership without the marker is just an orphan.
    marker = _marker_literal()
    assert marker in payload.read_text(encoding="utf-8")
    assert payload.read_bytes() != before_payload
    owned = _ledger(home)["installs"]["claude"]["owned_files"]
    assert rel in owned, f"{rel} was overwritten but not recorded as owned"

    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode == 0, ru.stderr
    assert not payload.exists(), "the taken-over payload file survived uninstall"
    assert bystander.read_bytes() == before_bystander, \
        "uninstall deleted or altered a file skill-mesh never owned"


def test_force_shared_still_refuses_a_collision_outside_the_payload(dist_root, tmp_path):
    """GUARDRAIL 2, stated as a refusal: the scope is not a global override.

    A foreign file at a SKILL path is untouched and the whole install is a true no-op --
    including the backup, which must not be written for a run that never mutates.
    """
    home = tmp_path / "home"
    backup = tmp_path / "backup"
    payload, _ = _preseed_shared(home)
    outside = _installed_root(home, "claude") / "build-phase" / "SKILL.md"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text("CUSTOM-USER-CONTENT", encoding="utf-8")
    before_payload = payload.read_bytes()

    r = _install(home, "claude", dist_dir=dist_root, force_shared=True, backup_dir=backup)
    assert r.returncode != 0, "-ForceShared authorized a collision outside the payload"
    assert "REFUS" in (r.stdout + r.stderr)
    assert outside.read_text(encoding="utf-8") == "CUSTOM-USER-CONTENT"
    assert payload.read_bytes() == before_payload, "a refused run still overwrote bytes"
    assert not _backup_runs(backup), \
        "a refused run wrote a backup, so a later run cannot tell it apart from a real one"
    assert not (home / ".skill-mesh-install.json").exists()


def test_force_shared_scope_is_decided_on_the_resolved_target_not_the_source_path(
        dist_root, tmp_path):
    """GUARDRAIL 2 against a directory JUNCTION at the payload root.

    `-ForceShared`'s authorization used to be computed from the SOURCE-relative path
    (`_shared\\x`, which starts with `_shared` by construction) while the overwrite
    landed on the reparse-point-RESOLVED target. With `<installRoot>/_shared` junctioned
    to a sibling directory, that authorized clobbering an operator file at a path with
    no `_shared` segment at all, and adopted eight paths under the operator's own
    namespace into `owned_files` -- which a later `-Uninstall` would then delete.

    Containment was never the hole (a junction pointing OUTSIDE the home is refused by
    path-guard); the SCOPE PREDICATE was.
    """
    home = tmp_path / "home"
    backup = tmp_path / "backup"
    victim_dir = _installed_root(home, "claude") / "victim"
    victim = victim_dir / _PRESEEDED_PAYLOAD
    victim_dir.mkdir(parents=True, exist_ok=True)
    victim.write_text("IRREPLACEABLE OPERATOR JUDGE DOCTRINE\n", encoding="utf-8")
    before = victim.read_bytes()
    _make_junction(_installed_root(home, "claude") / "_shared", victim_dir)

    r = _install(home, "claude", dist_dir=dist_root, force_shared=True, backup_dir=backup)
    assert r.returncode != 0, \
        "-ForceShared took ownership through a junction, outside the payload"
    assert victim.read_bytes() == before, "an operator file outside `_shared/` was clobbered"
    assert not _backup_runs(backup), "a refused run wrote a backup"
    led = home / ".skill-mesh-install.json"
    if led.exists():
        owned = json.loads(led.read_text(encoding="utf-8"))["installs"]["claude"]["owned_files"]
        assert not [o for o in owned if "/victim/" in o], \
            f"paths in the operator's own namespace were adopted into owned_files: {owned}"


def test_two_profiles_into_one_backup_dir_keep_both_restore_records(dist_root, tmp_path):
    """Both providers' restore records survive one shared `-BackupDir`.

    A fixed `<BackupDir>/take-ownership-backup.json` is overwritten by the second run:
    the pre-overwrite BYTES survive under `files/`, but the `rel_path`/`sha256`/
    `size_bytes` rows that make a restore VERIFIABLE exist only for the last provider,
    both runs exit 0, and nothing warns. Steps 70/71 are exactly this shape -- two
    profiles, one external backup destination.
    """
    home = tmp_path / "home"
    backup = tmp_path / "backup"
    claude_payload, _ = _preseed_shared(home, "claude")
    gpt_payload, _ = _preseed_shared(home, "gpt")
    claude_payload.write_text("# claude-side operator doctrine\n", encoding="utf-8")
    gpt_payload.write_text("# gpt-side operator doctrine, DIFFERENT\n", encoding="utf-8")
    before = {
        "claude": claude_payload.read_bytes(),
        "gpt": gpt_payload.read_bytes(),
    }

    for provider in ("claude", "gpt"):
        r = _install(home, provider, dist_dir=dist_root, force_shared=True,
                     backup_dir=backup)
        assert r.returncode == 0, f"{provider}:\n{r.stdout}\n{r.stderr}"

    runs = _backup_runs(backup)
    assert len(runs) == 2, \
        f"one run's restore record was destroyed by the other: {[str(d) for d, _ in runs]}"
    by_provider = {m["provider"]: (d, m) for d, m in runs}
    assert set(by_provider) == {"claude", "gpt"}, sorted(by_provider)
    for provider, (run_dir, manifest) in by_provider.items():
        rows = {f["rel_path"]: f for f in manifest["files"]}
        rel = next(k for k in rows if k.endswith(f"_shared/{_PRESEEDED_PAYLOAD}"))
        # The VERIFICATION METADATA, not just the bytes: a restore is only a restore if
        # the recorded hash still proves what is being put back.
        assert rows[rel]["sha256"] == hashlib.sha256(before[provider]).hexdigest(), provider
        assert rows[rel]["size_bytes"] == len(before[provider]), provider
        assert (run_dir / "files" / rel).read_bytes() == before[provider], provider
        # Same home, so the same non-disclosing identifier, and never an absolute path.
        assert manifest["home_id"] == by_provider["claude"][1]["home_id"]
        assert not re.search(r"[A-Za-z]:[\\/]", json.dumps(manifest)), \
            "an absolute install path leaked into the backup manifest"


def test_backup_dir_reaching_into_the_home_through_a_junction_is_refused(
        dist_root, tmp_path):
    """The outside-the-home assertion must resolve reparse points, not compare strings.

    `[System.IO.Path]::GetFullPath` + `StartsWith` walks straight through a junction, so
    a `-BackupDir` spelled OUTSIDE the home whose target is INSIDE it passed the check
    and landed the backup inside the very tree it exists to undo.
    """
    home = tmp_path / "home"
    payload, _ = _preseed_shared(home)
    before = payload.read_bytes()
    inside = home / "sneaky-backup"
    link = tmp_path / "outside-link"
    _make_junction(link, inside)

    r = _install(home, "claude", dist_dir=dist_root, force_shared=True, backup_dir=link)
    assert r.returncode != 0, "a -BackupDir junctioned into the install home was accepted"
    assert "OUTSIDE" in (r.stdout + r.stderr)
    assert payload.read_bytes() == before
    assert not _backup_runs(inside), "a backup landed inside the home it protects"


def test_unscoped_force_also_backs_up_when_given_a_backup_dir(dist_root, tmp_path):
    """`-BackupDir` is not a `-ForceShared`-only affordance.

    Documented in the installer's help, so it needs a test: the unscoped `-Force`
    remains unscoped (that contract is unchanged and covered above), but when the
    operator supplies a backup destination, every path it clobbers is recorded the
    same way -- otherwise the blunt instrument would be the one with no restore path.
    """
    home = tmp_path / "home"
    backup = tmp_path / "backup"
    target = _installed_root(home, "claude") / "build-phase" / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("CUSTOM-USER-CONTENT", encoding="utf-8")
    before = target.read_bytes()

    r = _install(home, "claude", dist_dir=dist_root, force=True, backup_dir=backup)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    runs = _backup_runs(backup)
    assert len(runs) == 1, [str(d) for d, _ in runs]
    run_dir, manifest = runs[0]
    rows = {f["rel_path"]: f for f in manifest["files"]}
    rel = next(k for k in rows if k.endswith("build-phase/SKILL.md"))
    assert rows[rel]["sha256"] == hashlib.sha256(before).hexdigest()
    assert (run_dir / "files" / rel).read_bytes() == before
    assert target.read_bytes() != before


def test_force_shared_requires_a_backup_dir(dist_root, tmp_path):
    """GUARDRAIL 1 as a precondition: no restore path, no take-ownership."""
    home = tmp_path / "home"
    payload, _ = _preseed_shared(home)
    before = payload.read_bytes()
    r = _install(home, "claude", dist_dir=dist_root, force_shared=True)
    assert r.returncode != 0, "-ForceShared ran without a backup destination"
    assert "-BackupDir" in (r.stdout + r.stderr)
    assert payload.read_bytes() == before


def test_backup_dir_inside_the_install_home_is_refused(dist_root, tmp_path):
    """A backup stored inside the tree it protects is not a restore path."""
    home = tmp_path / "home"
    payload, _ = _preseed_shared(home)
    before = payload.read_bytes()
    r = _install(home, "claude", dist_dir=dist_root, force_shared=True,
                 backup_dir=home / "backup")
    assert r.returncode != 0, "a backup dir inside the install home was accepted"
    assert "OUTSIDE" in (r.stdout + r.stderr)
    assert payload.read_bytes() == before


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


def test_marker_retaining_customization_refuses_reinstall_as_true_noop(dist_root, tmp_path):
    home = tmp_path / "home"
    assert _install(home, "claude", dist_dir=dist_root).returncode == 0
    target = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    target.write_bytes(target.read_bytes() + b"\nCONSUMER CUSTOMIZATION\n")
    ledger_path = home / ".skill-mesh-install.json"
    before_target, before_ledger = target.read_bytes(), ledger_path.read_bytes()

    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode != 0 and "REFUS" in (r.stdout + r.stderr)
    assert target.read_bytes() == before_target
    assert ledger_path.read_bytes() == before_ledger


def test_legacy_exact_incoming_self_seeds_hashes_without_rewriting(dist_root, tmp_path):
    home = tmp_path / "home"
    assert _install(home, "claude", dist_dir=dist_root).returncode == 0
    target = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    before_bytes = target.read_bytes()
    before_mtime = target.stat().st_mtime_ns
    ledger_path = home / ".skill-mesh-install.json"
    led = json.loads(ledger_path.read_text(encoding="utf-8"))
    del led["installs"]["claude"]["owned_file_hashes"]
    ledger_path.write_text(json.dumps(led), encoding="utf-8")

    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr
    assert target.read_bytes() == before_bytes
    assert target.stat().st_mtime_ns == before_mtime, "exact incoming legacy file was rewritten"
    entry = _ledger(home)["installs"]["claude"]
    assert set(entry["owned_file_hashes"]) == set(entry["owned_files"])


def test_plain_force_mismatch_requires_external_backup(dist_root, tmp_path):
    home = tmp_path / "home"
    target = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"OPERATOR BYTES")
    before = target.read_bytes()
    r = _install(home, "claude", dist_dir=dist_root, force=True)
    assert r.returncode != 0 and "-BackupDir" in (r.stdout + r.stderr)
    assert target.read_bytes() == before
    assert not (home / ".skill-mesh-install.json").exists()


def test_competing_home_operation_refuses_and_sequential_retry_succeeds(dist_root, tmp_path):
    home = (tmp_path / "home").resolve()
    env = os.environ.copy()
    env["SKILL_MESH_INSTALL_TEST_HOLD_LOCK_MS"] = "10000"
    holder = subprocess.Popen(
        [PWSH, "-NoProfile", "-NonInteractive", "-File", str(INSTALL_SCRIPT),
         "-Home", str(home), "-Provider", "claude", "-DistDir", str(dist_root)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
    )
    try:
        time.sleep(2)
        blocked = _install(home, "claude", dist_dir=dist_root)
        assert blocked.returncode != 0 and "concurrent operation" in (
            blocked.stdout + blocked.stderr)
        assert not home.exists()
    finally:
        out, err = holder.communicate(timeout=120)
        assert holder.returncode == 0, f"{out}\n{err}"

    retry = _install(home, "claude", dist_dir=dist_root)
    assert retry.returncode == 0, retry.stderr
    assert "claude" in _ledger(home)["installs"]


def test_customized_stale_file_refuses_reinstall_as_true_noop(tmp_path):
    home = tmp_path / "home"
    big = _build_from_manifest(tmp_path / "big",
                               _write_manifest(tmp_path / "big.json", [
                                   _real_skill_entry("build-phase"),
                                   _real_skill_entry("build-step"),
                               ]), provider="claude")
    small = _build_from_manifest(tmp_path / "small",
                                 _write_manifest(tmp_path / "small.json", [
                                     _real_skill_entry("build-phase"),
                                 ]), provider="claude")
    assert _install(home, "claude", dist_dir=big).returncode == 0
    stale = home / DISCOVERY_SUBDIR["claude"] / "build-step" / "SKILL.md"
    stale.write_bytes(stale.read_bytes() + b"\nCUSTOM STALE\n")
    ledger_path = home / ".skill-mesh-install.json"
    before_stale, before_ledger = stale.read_bytes(), ledger_path.read_bytes()
    r = _install(home, "claude", dist_dir=small)
    assert r.returncode != 0
    assert "stale" in (r.stdout + r.stderr).lower()
    assert stale.read_bytes() == before_stale
    assert ledger_path.read_bytes() == before_ledger


def test_customized_owned_file_refuses_uninstall_as_true_noop(dist_root, tmp_path):
    home = tmp_path / "home"
    assert _install(home, "claude", dist_dir=dist_root).returncode == 0
    target = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    target.write_bytes(target.read_bytes() + b"\nCUSTOM BEFORE UNINSTALL\n")
    ledger_path = home / ".skill-mesh-install.json"
    before_tree = _tree_snapshot(home / DISCOVERY_SUBDIR["claude"])
    before_ledger = ledger_path.read_bytes()
    r = _install(home, "claude", uninstall=True)
    assert r.returncode != 0 and "REFUS" in (r.stdout + r.stderr)
    assert _tree_snapshot(home / DISCOVERY_SUBDIR["claude"]) == before_tree
    assert ledger_path.read_bytes() == before_ledger


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
    # Directory records are audit-only; even skill-mesh-created empty dirs survive.
    assert (home / DISCOVERY_SUBDIR["claude"] / "build-phase").is_dir()


def test_uninstall_never_deletes_even_ledger_created_directories(dist_root, tmp_path):
    home = tmp_path / "new-home"
    assert _install(home, "claude", dist_dir=dist_root).returncode == 0
    created = [home / Path(r) for r in _ledger(home)["installs"]["claude"]["created_dirs"]]
    assert created
    assert _install(home, "claude", uninstall=True).returncode == 0
    assert all(path.is_dir() for path in created), "created_dirs authorized directory deletion"


# --------------------------------------------------------------------------- #
# Generated-header candidate checks. File-content provenance is one guard; it does not
# replace independent path, ledger, and current-byte authority. Locks in the parser fix.
# --------------------------------------------------------------------------- #

def _disco_rel(provider, *parts):
    """POSIX rel path under the provider's discovery subdir, built from
    DISCOVERY_SUBDIR so this file carries no load-bearing '.claude/...' literal
    (tests/router/test_no_claude_dependency scans tests/ for exactly that)."""
    return DISCOVERY_SUBDIR[provider].joinpath(*parts).as_posix()


def _write_ledger(home, provider, owned, created, subdir=None, hashes=None):
    if subdir is None:
        subdir = DISCOVERY_SUBDIR[provider].as_posix()
    entry = {
        "provider": provider, "discovery_subdir": subdir,
        "owned_files": owned, "created_dirs": created,
    }
    if hashes is not None:
        entry["owned_file_hashes"] = hashes
    led = {
        "tool": "skill-mesh", "ledger_version": 1,
        "installs": {provider: entry},
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
    ledger_before = (home / ".skill-mesh-install.json").read_bytes()
    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode != 0 and "REFUS" in (ru.stdout + ru.stderr)
    assert target.read_text(encoding="utf-8") == "OPERATOR-CONTENT-NO-MARKER"
    assert (home / ".skill-mesh-install.json").read_bytes() == ledger_before


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


def test_final_ledger_failure_keeps_write_ahead_authority_and_plain_retry_converges(tmp_path):
    """No payload result is orphaned when both normal/recovery ledger publication
    fail after commit: the pre-published write-ahead map authorizes a plain retry.

    This exercises a changed file *and* a stale deletion. The test-only seam fails
    every normal-ledger publication for the interrupted run, not just the first one.
    """
    initial = _build_from_manifest(
        tmp_path / "initial",
        _write_manifest(tmp_path / "initial.json", [
            _real_skill_entry("build-phase"),
            _real_skill_entry("build-step"),
        ]),
        provider="claude",
    )
    changed = tmp_path / "changed"
    shutil.copytree(initial, changed)
    changed_core = changed / "claude" / "build-phase" / "core.md"
    changed_core.write_bytes(changed_core.read_bytes() + b"\nCHANGED-PAYLOAD\n")
    shutil.rmtree(changed / "claude" / "build-step")

    home = tmp_path / "home"
    assert _install(home, "claude", dist_dir=initial).returncode == 0
    ledger_path = home / ".skill-mesh-install.json"
    prior_ledger = ledger_path.read_bytes()
    target = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "core.md"
    stale = home / DISCOVERY_SUBDIR["claude"] / "build-step" / "SKILL.md"
    old_target = target.read_bytes()
    assert stale.exists()

    failed_env = os.environ.copy()
    failed_env["SKILL_MESH_INSTALL_TEST_FAIL_LEDGER_PUBLISH"] = "always"
    failed = _install(home, "claude", dist_dir=changed, env=failed_env)
    assert failed.returncode != 0
    assert target.read_bytes() == changed_core.read_bytes() != old_target
    assert not stale.exists(), "the stale delete should have occurred before final publication"
    assert ledger_path.read_bytes() == prior_ledger, "failed publication changed normal authority"

    write_ahead_path = home / ".skill-mesh-install.write-ahead.json"
    write_ahead = json.loads(write_ahead_path.read_text(encoding="utf-8"))
    transitions = {row["rel_path"]: row for row in write_ahead["actions"]}
    target_rel = target.relative_to(home).as_posix()
    stale_rel = stale.relative_to(home).as_posix()
    assert transitions[target_rel]["post_hash"] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert transitions[stale_rel]["post_hash"] is None
    assert len(transitions) == len(write_ahead["actions"]), "transition paths must be bijective"

    retry = _install(home, "claude", dist_dir=changed)
    assert retry.returncode == 0, f"plain recovery retry failed:\n{retry.stdout}\n{retry.stderr}"
    assert not write_ahead_path.exists(), "recovery record survived durable final authority"
    assert target.read_bytes() == changed_core.read_bytes()
    assert not stale.exists(), "stale path became an untracked orphan after recovery"
    entry = _ledger(home)["installs"]["claude"]
    assert set(entry["owned_files"]) == set(entry["owned_file_hashes"])
    assert stale_rel not in entry["owned_file_hashes"]


def test_write_ahead_recovery_does_not_baseline_an_unreplaced_force_preimage(tmp_path):
    """A write-ahead record distinguishes a backed foreign preimage from prior owned
    authority. It may retain that preimage after an early interruption, but never
    records it as installed ownership."""
    dist = _build_from_manifest(
        tmp_path / "dist",
        _write_manifest(tmp_path / "manifest.json", [_real_skill_entry("build-phase")]),
        provider="claude",
    )
    home = tmp_path / "home"
    target = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    target.parent.mkdir(parents=True)
    foreign = b"OPERATOR-PREIMAGE"
    target.write_bytes(foreign)
    backup = tmp_path / "backup"

    failed_env = os.environ.copy()
    failed_env["SKILL_MESH_INSTALL_TEST_FAIL_LEDGER_PUBLISH"] = "always"
    failed = _install(home, "claude", dist_dir=dist, force=True,
                      backup_dir=backup, env=failed_env)
    assert failed.returncode != 0
    assert target.read_bytes() != foreign
    assert (home / ".skill-mesh-install.write-ahead.json").exists()

    retry = _install(home, "claude", dist_dir=dist)
    assert retry.returncode == 0, f"plain forced-recovery retry failed:\n{retry.stdout}\n{retry.stderr}"
    entry = _ledger(home)["installs"]["claude"]
    target_rel = target.relative_to(home).as_posix()
    assert entry["owned_file_hashes"][target_rel] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert entry["owned_file_hashes"][target_rel] != hashlib.sha256(foreign).hexdigest()


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


def test_corrupt_ledger_uninstall_fails_closed_and_preserves_files(dist_root, tmp_path):
    """A corrupt ledger has no current-byte identity authority; marker-only deletion
    is forbidden, so uninstall fails loudly and preserves every file."""
    home = tmp_path / "home"
    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr
    disco = home / DISCOVERY_SUBDIR["claude"]
    assert len(list(disco.rglob("*.md"))) > 0
    # Corrupt the ledger AFTER install (simulates truncation/tamper).
    (home / ".skill-mesh-install.json").write_text(CORRUPT_LEDGER, encoding="utf-8")

    before = _tree_snapshot(disco)
    ledger_before = (home / ".skill-mesh-install.json").read_bytes()
    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode != 0
    diag = ru.stdout + ru.stderr
    assert ("lost track" in diag) or ("fallback" in diag) or ("CORRUPT" in diag), \
        "no loud lost-tracking diagnostic on corrupt-ledger uninstall"
    assert _tree_snapshot(disco) == before
    assert (home / ".skill-mesh-install.json").read_bytes() == ledger_before


@pytest.mark.parametrize("mutation", ["missing", "malformed", "extra"])
def test_invalid_owned_hash_maps_never_authorize_uninstall(dist_root, tmp_path, mutation):
    home = tmp_path / "home"
    assert _install(home, "claude", dist_dir=dist_root).returncode == 0
    ledger_path = home / ".skill-mesh-install.json"
    led = json.loads(ledger_path.read_text(encoding="utf-8"))
    entry = led["installs"]["claude"]
    if mutation == "missing":
        del entry["owned_file_hashes"]
    elif mutation == "malformed":
        first = entry["owned_files"][0]
        entry["owned_file_hashes"][first] = "not-a-sha256"
    else:
        entry["owned_file_hashes"]["unexpected/extra"] = "0" * 64
    ledger_path.write_text(json.dumps(led, sort_keys=True), encoding="utf-8")
    before_ledger = ledger_path.read_bytes()
    before_tree = _tree_snapshot(home / DISCOVERY_SUBDIR["claude"])

    r = _install(home, "claude", uninstall=True)
    assert r.returncode != 0 and "REFUS" in (r.stdout + r.stderr)
    assert ledger_path.read_bytes() == before_ledger
    assert _tree_snapshot(home / DISCOVERY_SUBDIR["claude"]) == before_tree


def test_hashless_legacy_uninstall_requires_and_honors_backed_force(dist_root, tmp_path):
    home = tmp_path / "home"
    assert _install(home, "claude", dist_dir=dist_root).returncode == 0
    ledger_path = home / ".skill-mesh-install.json"
    led = json.loads(ledger_path.read_text(encoding="utf-8"))
    del led["installs"]["claude"]["owned_file_hashes"]
    ledger_path.write_text(json.dumps(led), encoding="utf-8")
    before = _tree_snapshot(home / DISCOVERY_SUBDIR["claude"])

    refused = _install(home, "claude", uninstall=True)
    assert refused.returncode != 0
    assert _tree_snapshot(home / DISCOVERY_SUBDIR["claude"]) == before

    backup = tmp_path / "backup"
    forced = _install(home, "claude", uninstall=True, force=True, backup_dir=backup)
    assert forced.returncode == 0, forced.stderr
    runs = _backup_runs(backup)
    assert len(runs) == 1
    _, manifest = runs[0]
    assert len(manifest["files"]) == len(before)
    assert not list((home / DISCOVERY_SUBDIR["claude"]).rglob("*.*"))


def test_cross_provider_poison_cannot_authorize_uninstall(dist_root, tmp_path):
    home = tmp_path / "home"
    assert _install(home, "claude", dist_dir=dist_root).returncode == 0
    assert _install(home, "gpt", dist_dir=dist_root).returncode == 0
    victim = home / DISCOVERY_SUBDIR["gpt"] / "build-phase" / "SKILL.md"
    victim_rel = victim.relative_to(home).as_posix()
    ledger_path = home / ".skill-mesh-install.json"
    led = json.loads(ledger_path.read_text(encoding="utf-8"))
    led["installs"]["claude"]["owned_files"] = [victim_rel]
    led["installs"]["claude"]["owned_file_hashes"] = {
        victim_rel: hashlib.sha256(victim.read_bytes()).hexdigest(),
    }
    ledger_path.write_text(json.dumps(led, sort_keys=True), encoding="utf-8")
    before_victim, before_ledger = victim.read_bytes(), ledger_path.read_bytes()
    r = _install(home, "claude", uninstall=True)
    assert r.returncode != 0 and "REFUS" in (r.stdout + r.stderr)
    assert victim.read_bytes() == before_victim
    assert ledger_path.read_bytes() == before_ledger


def test_markerless_distribution_source_refuses_before_home_mutation(tmp_path):
    dist = _build_from_manifest(tmp_path / "dist",
                                _write_manifest(tmp_path / "m.json", [
                                    _real_skill_entry("build-phase"),
                                ]), provider="claude")
    source = dist / "claude" / "build-phase" / "SKILL.md"
    source.write_text("MARKERLESS SOURCE\n", encoding="utf-8")
    home = tmp_path / "home"
    r = _install(home, "claude", dist_dir=dist)
    assert r.returncode != 0 and "source profile" in (r.stdout + r.stderr)
    assert not home.exists(), "markerless source mutated the install home"


def test_marker_false_positive_token_mention_not_owned(dist_root, tmp_path):
    """BLOCK 1: an operator file that merely MENTIONS the marker token (not a
    well-formed generated header) at a colliding path is NOT clobbered on a plain
    install and NOT deleted on uninstall, even when the ledger lists it as owned.

    The ledger here is deliberately MAXIMALLY convincing: a complete, bijective
    owned_file_hashes map whose recorded hash is the operator file's CURRENT bytes.
    Every other authority the installer has therefore says "yes" -- the path is
    listed, the entry is well-formed, the recorded hash matches exactly -- and the
    anchored provenance parser is the single thing standing between the operator's
    file and deletion. That is the property this test is named for.

    (Handing it a hashless ledger instead, as this test did before owned_file_hashes
    became authority, no longer reaches the marker at all: an inconsistent map is
    refused up front by Get-ValidOwnedHashMap -- see
    test_hashless_legacy_uninstall_requires_and_honors_backed_force -- so the marker
    parser would never run and this test would prove nothing about it.)
    """
    home = tmp_path / "home"
    target = home / DISCOVERY_SUBDIR["claude"] / "build-phase" / "SKILL.md"
    target.parent.mkdir(parents=True)
    marker = _marker_literal()
    # Operator's own file that quotes the token in prose (no generated header block).
    operator_text = f"# My hand-authored notes\nThe {marker} token is documented here.\n"
    target.write_text(operator_text, encoding="utf-8")
    owned_rel = _disco_rel("claude", "build-phase", "SKILL.md")
    _write_ledger(home, "claude",
                  owned=[owned_rel],
                  created=[_disco_rel("claude", "build-phase")],
                  hashes={owned_rel: hashlib.sha256(target.read_bytes()).hexdigest()})
    ledger_before = (home / ".skill-mesh-install.json").read_bytes()

    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode != 0 and "REFUS" in (r.stdout + r.stderr), \
        "a token-mentioning operator file was misclassified as owned and overwritten"
    assert target.read_text(encoding="utf-8") == operator_text

    ru = _install(home, "claude", uninstall=True)
    combined = ru.stdout + ru.stderr
    assert ru.returncode != 0 and "REFUS" in combined, \
        "a token-mentioning operator file was misclassified as owned and deleted"
    # The refusal must name PROVENANCE, not a byte change: the recorded hash matches
    # this file exactly, so "no longer matches its recorded hash" would be false and
    # would send the operator looking for a change that never happened.
    assert "generated header" in combined, combined
    assert target.read_text(encoding="utf-8") == operator_text, \
        "a token-mentioning operator file was deleted on uninstall"
    assert (home / ".skill-mesh-install.json").read_bytes() == ledger_before


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
    # ...and the shared payload does not appear either. Step 64's closure is re-walked
    # from the sources THIS profile emits, so a profile that emits nothing has no seeds
    # and ships nothing. An unconditional `_shared/` emit would break this case AND
    # would put judge-core.md in a home whose ledger owns nothing else.
    assert not (dist / "gpt" / SHARED_DEST).exists(), \
        "the shared payload shipped into a profile with no skills to consume it"
    assert not list((dist / "gpt").rglob("*")), "expected a completely empty gpt profile"

    home = tmp_path / "home"  # fresh, does not exist yet
    r = _install(home, "gpt", dist_dir=dist)
    assert r.returncode == 0, f"zero-file install crashed:\n{r.stdout}\n{r.stderr}"
    led = json.loads((home / ".skill-mesh-install.json").read_text(encoding="utf-8"))
    assert led["installs"]["gpt"]["owned_files"] == []

    # ...and the empty ledger it wrote is authority the NEXT run can still read.
    ru = _install(home, "gpt", uninstall=True)
    assert ru.returncode == 0, f"zero-file uninstall refused its own ledger:\n{ru.stderr}"
    assert not (home / ".skill-mesh-install.json").exists()


def _single_file_manifest(path):
    """A manifest whose claude profile is exactly ONE generated file (a Claude-only
    provider-native skill: no core, so no shared payload is seeded either)."""
    return _write_manifest(path, [{
        "name": "claude-oauth-auth", "status": "provider-native", "core": None,
        "providers": {"claude": "skills/claude-oauth-auth/providers/claude.md"},
    }])


def test_single_file_profile_reinstalls_and_uninstalls_without_force(tmp_path):
    """A profile whose ledger owns exactly ONE file is an ordinary install: a plain
    reinstall over changed bytes and a plain uninstall must both succeed.

    Regression, and a real one -- the size of the profile is load-bearing here.
    owned_files is read back for Get-ValidOwnedHashMap's `-is [System.Array]` shape
    check, the check that stops a scalar being accepted as a one-element list. Read
    through a helper whose `return` ENUMERATES, a one-element JSON array arrives as a
    bare string and an empty one as $null, so the check rejected the two shapes it
    existed to accept. A one-file profile therefore lost ALL routine authority: the
    plain reinstall refused ("lack current-byte overwrite authority") and the plain
    uninstall refused ("owned_file_hashes is missing, malformed, or inconsistent"),
    leaving -Force plus an external -BackupDir as the only way to remove a perfectly
    ordinary install. Every other install test in this file owns several files, which
    is exactly why nothing saw it.
    """
    dist = _build_from_manifest(tmp_path / "d",
                                _single_file_manifest(tmp_path / "native.json"),
                                provider="claude")
    produced = sorted(p for p in (dist / "claude").rglob("*") if p.is_file())
    assert len(produced) == 1, f"this regression needs a one-file profile, got {produced}"
    source = produced[0]

    home = tmp_path / "home"
    assert _install(home, "claude", dist_dir=dist).returncode == 0
    entry = _ledger(home)["installs"]["claude"]
    assert len(entry["owned_files"]) == 1, entry["owned_files"]
    assert set(entry["owned_file_hashes"]) == set(entry["owned_files"])
    target = home / entry["owned_files"][0]

    # CHANGED bytes, appended after the generated header so provenance survives. An
    # identical-bytes reinstall is an exact-incoming no-op that never consults the
    # recorded hash, so it could not stand in for this: only a real overwrite proves
    # the one-entry hash map is still readable as authority.
    source.write_bytes(source.read_bytes() + b"\nCHANGED-PAYLOAD\n")
    again = _install(home, "claude", dist_dir=dist)
    assert again.returncode == 0, \
        f"a one-file profile lost routine overwrite authority:\n{again.stdout}\n{again.stderr}"
    assert target.read_bytes() == source.read_bytes()

    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode == 0, f"a one-file profile could not be uninstalled:\n{ru.stderr}"
    assert not target.exists()
    assert not (home / ".skill-mesh-install.json").exists()


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
        assert set(entry["owned_file_hashes"]) == set(entry["owned_files"])


def test_uninstall_partial_removal_preexisting_tree_never_deletes_home(tmp_path):
    """BLOCK 1: when the ENTIRE discovery tree pre-existed the install (created_dirs is
    empty), a partial-removal-and-reconcile during uninstall must NOT persist a
    null/empty created_dirs entry, and a retry must NEVER delete the operator's
    pre-existing home directory via such an entry."""
    home = tmp_path / "home"
    # Operator pre-creates the WHOLE discovery tree (home + subdirs + the skill dir
    # + the profile-root `_shared/` payload dir Step 64 added), so skill-mesh creates
    # NO directory during install -> created_dirs == []. The `_shared` mkdir is a
    # FIXTURE correction, not a weakened assertion: "the whole tree pre-existed" is
    # the premise, and the tree grew a directory.
    skill_dir = home / DISCOVERY_SUBDIR["claude"] / "build-phase"
    skill_dir.mkdir(parents=True)
    (home / DISCOVERY_SUBDIR["claude"] / SHARED_DEST).mkdir(parents=True, exist_ok=True)
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
        assert ru.returncode != 0 and "REFUS" in (ru.stdout + ru.stderr)
        assert home.is_dir(), (
            f"tampered created_dirs entry {poison!r} deleted the operator's pre-existing home"
        )


def test_corrupt_ledger_fallback_preserves_everything(dist_root, tmp_path):
    """Without current-byte hashes a corrupt-ledger uninstall deletes nothing."""
    home = tmp_path / "home"
    r = _install(home, "claude", dist_dir=dist_root)
    assert r.returncode == 0, r.stderr
    disco = home / DISCOVERY_SUBDIR["claude"]
    op_dir = disco / "operator-tool"
    op_dir.mkdir()                                  # operator's own (empty) dir
    unrelated = disco / "operator-notes.txt"
    unrelated.write_text("my notes, no marker", encoding="utf-8")  # non-marker file

    (home / ".skill-mesh-install.json").write_text(CORRUPT_LEDGER, encoding="utf-8")
    generated = disco / "build-phase" / "SKILL.md"
    generated_before = generated.read_bytes()
    ru = _install(home, "claude", uninstall=True)
    assert ru.returncode != 0 and "REFUS" in (ru.stdout + ru.stderr)

    # Directories (incl. shared discovery root) + the unrelated file survive.
    assert disco.is_dir(), "shared discovery root was deleted by the fallback"
    assert op_dir.is_dir(), "operator dir was deleted by the fallback"
    assert unrelated.read_text(encoding="utf-8") == "my notes, no marker"
    assert generated.read_bytes() == generated_before


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


# --------------------------------------------------------------------------- #
# Codex profile (Phase CP Step 3, issue #120)
#
# Codex is the THIRD provider on the existing rails (D-CP1), so these tests grade it
# against the SAME contract the other two profiles already satisfy -- provenance on
# every emitted file, a co-located core.md the launcher can require, LF/UTF-8-no-BOM
# bytes, and byte-identical reruns -- rather than a codex-specific relaxation.
#
# THE FIXTURE-SKILL SEAM. Step 3 builds the generation surface and deliberately authors
# NO real skills/*/providers/codex.md (the pilot five are Step 4, the cohorts Steps
# 6-8), so `-Provider codex` against the committed manifest legitimately emits an EMPTY
# profile. An empty tree cannot prove the rails work, and planting a codex.md in the
# real checkout would BE Step 4's work done early -- so these tests drive the real
# builder over a synthetic repo (_synthetic_build_repo) carrying a fixture skill. That
# is the same seam the shared-closure refusal tests already use, and it plants nothing
# in this checkout.
# --------------------------------------------------------------------------- #

# NOTE the citation is NOT followed by a period. $SHARED_REF_RE's leaf class includes
# '.', so `../../_shared/judge-core.md.` harvests the leaf `judge-core.md.` -- extension
# '' -- and the builder correctly refuses to ship a file it cannot stamp. Real cores
# phrase these citations mid-sentence for the same reason; keep it that way here.
_CODEX_FIXTURE_CORE = (
    "# demo core\n\nThe portable behavior contract. It cites "
    "../../_shared/judge-core.md for the shared payload.\n"
)
_CODEX_FIXTURE_ADAPTER = (
    "# demo -- Codex provider entry point\n\n"
    "Load `../core.md` in full and follow it verbatim. Codex has no Agent tool, so use "
    "the core's documented single-context fallback.\n"
)
_CODEX_FIXTURE_GPT_ADAPTER = (
    "# demo -- GPT/Copilot provider entry point\n\n"
    "Load `../core.md` in full and follow it verbatim.\n"
)
_CODEX_FIXTURE_DESC = "Demo skill for the codex generation rails."


def _codex_fixture_repo(tmp_path):
    """A synthetic repo whose one skill declares core + claude + gpt + codex.

    Genuinely gpt-eligible (not just codex-eligible): `gpt_adapter_body` is set so the
    manifest entry carries a real `providers.gpt` path, which is what
    `test_provider_both_still_means_claude_and_gpt_only` needs to assert gpt is actually
    emitted under `both`/`all` rather than accidentally passing because no gpt adapter
    exists to omit.
    """
    return _synthetic_build_repo(
        tmp_path,
        {"judge-core.md": "# judge core\n\nShared payload.\n"},
        _CODEX_FIXTURE_CORE,
        gpt_adapter_body=_CODEX_FIXTURE_GPT_ADAPTER,
        codex_adapter_body=_CODEX_FIXTURE_ADAPTER,
        description=_CODEX_FIXTURE_DESC,
    )


def test_codex_profile_emits_launcher_and_colocated_core_for_a_fixture_skill(tmp_path):
    """The Step 3 Done-when: -Provider codex emits a real tree for a fixture skill.

    Grades every emission rule the step owes at once, because they are only correct
    together: a launcher whose frontmatter parses but whose core reference still points
    at `../core.md` is a package Codex can list and cannot run.
    """
    repo = _codex_fixture_repo(tmp_path)
    out = tmp_path / "out"
    r = _synthetic_build(repo, out, provider="codex")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    skill_dir = out / "codex" / "demo"
    launcher = skill_dir / "SKILL.md"
    core = skill_dir / "core.md"
    assert launcher.is_file(), "no codex launcher emitted"
    assert core.is_file(), \
        "codex profile must ship the co-located core.md the launcher requires"

    text = launcher.read_text(encoding="utf-8")
    # 1. Frontmatter FIRST (a host scans line 1), synthesized from the manifest record.
    assert text.startswith("---\n"), text[:120]
    assert "\nname: demo\n" in text
    assert '\ndescription: "' + _CODEX_FIXTURE_DESC + '"\n' in text
    # 2. Provenance header, placed AFTER the closing fence so frontmatter stays first.
    assert _PROV_OPEN in text
    assert text.index(_PROV_OPEN) > text.index("---\n"), \
        "provenance must follow the frontmatter block, not precede it"
    assert "Canonical source: skills/demo/providers/codex.md" in text
    assert "Profile: codex" in text
    # 3. The own-core reference is repointed to the co-located sibling.
    assert "core.md" in text
    assert "../core.md" not in text
    # 4. The core itself carries provenance and the repointed shared reference.
    core_text = core.read_text(encoding="utf-8")
    assert _PROV_OPEN in core_text
    assert "../_shared/judge-core.md" in core_text
    assert "../../_shared/" not in core_text


def test_codex_launcher_frontmatter_satisfies_the_codex_keys_contract(tmp_path):
    """Graded by the ONE owner of the frontmatter contract, under CODEX_KEYS.

    The emitted profile is what a host actually parses, so it is graded by the same
    module and the same strict parser as the canonical sources -- producer and consumer
    on one contract, per .claude/rules/code-quality.md.
    """
    fc = _frontmatter_contract()
    repo = _codex_fixture_repo(tmp_path)
    out = tmp_path / "out"
    assert _synthetic_build(repo, out, provider="codex").returncode == 0
    text = (out / "codex" / "demo" / "SKILL.md").read_text(encoding="utf-8")
    defects = fc.frontmatter_defects(text, allowed_keys=fc.CODEX_KEYS)
    assert not defects, defects
    # The parsed values must be the manifest's, not re-authored per host.
    parsed = fc.parse_frontmatter(text)
    assert parsed == {"name": "demo", "description": _CODEX_FIXTURE_DESC}


def test_codex_keys_permits_exactly_name_and_description():
    """ANCHOR: the CODEX_KEYS allowlist is closed, and closed at the right two keys.

    Without this, CODEX_KEYS could be widened (or aliased to a laxer set) and every
    positive test above would still pass -- an over-accepting frontmatter gate is the
    issue-#69 failure mode. Also asserts the equality with GPT_KEYS is a FACT rather
    than a dependency: the two are separately spelled on purpose.
    """
    fc = _frontmatter_contract()
    assert fc.CODEX_KEYS == frozenset({"name", "description"})
    assert fc.CODEX_KEYS == fc.GPT_KEYS
    planted = "---\nname: demo\ndescription: d\nuser-invocable: true\n---\n\nbody\n"
    assert any("user-invocable" in d
               for d in fc.frontmatter_defects(planted, allowed_keys=fc.CODEX_KEYS)), \
        "CODEX_KEYS accepted a key outside its two-key contract"


def test_codex_profile_rerun_is_byte_identical(tmp_path):
    """Determinism, the property the whole build contract rests on."""
    repo = _codex_fixture_repo(tmp_path)
    first, second = tmp_path / "o1", tmp_path / "o2"
    assert _synthetic_build(repo, first, provider="codex").returncode == 0
    assert _synthetic_build(repo, second, provider="codex").returncode == 0
    snap1 = _tree_snapshot(first / "codex")
    snap2 = _tree_snapshot(second / "codex")
    assert snap1 == snap2, "codex profile is not byte-reproducible across runs"
    assert snap1, "codex profile emitted nothing -- determinism would be vacuous"
    # Rebuilding OVER an existing tree must also land the same bytes (the profile dir is
    # wiped and regenerated, so a stale file cannot survive).
    assert _synthetic_build(repo, first, provider="codex").returncode == 0
    assert _tree_snapshot(first / "codex") == snap1


def test_codex_emitted_bytes_are_utf8_no_bom_lf(tmp_path):
    """Same byte discipline as the other profiles: no BOM, no CRLF."""
    repo = _codex_fixture_repo(tmp_path)
    out = tmp_path / "out"
    assert _synthetic_build(repo, out, provider="codex").returncode == 0
    files = [p for p in (out / "codex").rglob("*") if p.is_file()]
    assert files
    for p in files:
        raw = p.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), f"{p} carries a UTF-8 BOM"
        assert b"\r\n" not in raw, f"{p} carries CRLF line endings"
        raw.decode("utf-8")


def test_codex_profile_excludes_provider_native_skills(tmp_path):
    """Provider-native means Claude-only, so these skills are ABSENT from dist/codex.

    Driven over the REAL skills/ tree through the -ManifestPath seam, because the
    exclusion is a decision about manifest records and must be proven on real ones. The
    fixture entry points `providers.codex` at the skill's existing gpt.md: no codex.md
    exists anywhere at Step 3 by design, and this test grades which skills are SELECTED
    into the profile, not what an adapter says.
    """
    portable = "plan-review"
    native = "context-slim"
    entry = _real_skill_entry(portable)
    entry["providers"]["codex"] = f"skills/{portable}/providers/gpt.md"
    native_entry = {
        "name": native,
        "status": "provider-native",
        "core": None,
        "providers": {"claude": f"skills/{native}/providers/claude.md"},
    }
    manifest = _write_manifest(tmp_path / "m.json", [entry, native_entry])
    out = _build_from_manifest(tmp_path / "out", manifest, provider="codex")
    assert (out / "codex" / portable / "SKILL.md").is_file()
    assert (out / "codex" / portable / "core.md").is_file()
    assert not (out / "codex" / native).exists(), \
        "a Claude-only skill was emitted into the codex profile"
    # And the claude profile DOES carry it -- proving the exclusion is provider-scoped,
    # not the skill being dropped everywhere.
    out2 = _build_from_manifest(tmp_path / "out2", manifest, provider="claude")
    assert (out2 / "claude" / native / "SKILL.md").is_file()


def test_provider_both_still_means_claude_and_gpt_only(tmp_path):
    """The `both`-vs-`all` decision, asserted so it cannot drift silently.

    `both` KEEPS its pre-codex meaning (claude + gpt) and `all` is the new
    everything-spelling. This matters beyond taste: tools/release.ps1 defaults to
    `both` and SHA-256s everything under the generated dist/, so a widened `both` would
    silently add a codex profile to every release artifact while codex still has no
    discovery root to install into (Phase CP Step 5). A future edit that "fixes" the
    now-inaccurate word by widening it reds here.

    Both halves of the name are pinned: `both` must still include GPT (not just
    exclude codex -- a `both` that silently NARROWED to claude-only would stay green
    without this), and `all` must include every one of the three profiles. The fixture
    skill carries a real `providers.gpt` path (see `_codex_fixture_repo`), so a missing
    gpt launcher here is a real failure, not an accidentally-vacuous one.
    """
    repo = _codex_fixture_repo(tmp_path)
    out = tmp_path / "out"
    assert _synthetic_build(repo, out, provider="both").returncode == 0
    assert (out / "claude" / "demo" / "SKILL.md").is_file()
    assert (out / "gpt" / "demo" / "SKILL.md").is_file(), \
        "-Provider both must still emit the gpt profile"
    assert not (out / "codex").exists(), \
        "-Provider both emitted a codex profile; 'both' must stay claude+gpt"

    out_all = tmp_path / "out_all"
    assert _synthetic_build(repo, out_all, provider="all").returncode == 0
    assert (out_all / "claude" / "demo" / "SKILL.md").is_file()
    assert (out_all / "gpt" / "demo" / "SKILL.md").is_file(), \
        "-Provider all must include the gpt profile"
    assert (out_all / "codex" / "demo" / "SKILL.md").is_file(), \
        "-Provider all must include the codex profile"


def test_codex_profile_is_empty_for_the_committed_manifest(tmp_path):
    """The honest Step-3 state, pinned so it is a DECISION rather than an oversight.

    No codex adapter is authored yet, so the real manifest yields an empty profile and
    the build must SUCCEED rather than throw -- the cohort steps rely on being able to
    build a partially-populated codex profile. This test flips to "5 skills" at Step 4;
    an accidental early codex entry in the committed manifest reds it here first.
    """
    out = tmp_path / "out"
    r = _build(out, provider="codex")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert "(0 skills, 0 files)" in r.stdout, r.stdout
    assert _codex_skills() == [], _codex_skills()
    emitted = [p for p in (out / "codex").rglob("*") if p.is_file()]
    assert emitted == [], emitted
