"""Structural + clause-preservation gate for the migrated skills/<name>/ tree (Step 35).

Two independent layers:

- STRUCTURAL (mandatory, needs NO private/legacy source): every portable skill
  dir has exactly core.md + providers/claude.md + providers/gpt.md; every
  provider-native dir has ONLY providers/claude.md (no core.md, no gpt.md); the
  counts match the manifest (47 portable, 3 native, 50 total); skills/inventory.json
  agrees with the manifest and the committed expected_inventory.json fixture; and
  no operator-private absolute path leaked into the migrated tree.

- CLAUSE-PRESERVATION (optional, SKIPS cleanly without SKILL_MESH_LEGACY_SOURCE,
  like test_migration_source_files_exist): re-derives each migrated file from its
  READ-ONLY legacy source via the production transform and asserts (a) it
  reproduces the committed bytes exactly (determinism / zero drift) and (b) the
  normalized clause-bearing prose is identical (no required clause dropped or
  reworded -- only path tokens changed).

Runnable via pytest (`python -m pytest tests/package-integrity`) or standalone.
"""

import json
import os
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"
FIXTURE_PATH = Path(__file__).resolve().parent / "expected_inventory.json"
INVENTORY_PATH = REPO_ROOT / "skills" / "inventory.json"
SKILLS_DIR = REPO_ROOT / "skills"

# Import the production generator (single source of truth for the migration
# transform and plan) -- reused, never re-implemented, by the source-bearing test.
sys.path.insert(0, str(REPO_ROOT / "tools"))
import gen_skill_tree  # noqa: E402

PRIVATE_PATH_RE = re.compile(r"[A-Za-z]:[\\/]Users[\\/]abero")


def load_manifest():
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_inventory():
    with open(INVENTORY_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_fixture():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
# Inventory artifact
# --------------------------------------------------------------------------- #

def test_inventory_exists_and_parses():
    assert INVENTORY_PATH.is_file(), f"missing inventory: {INVENTORY_PATH}"
    inv = load_inventory()
    assert isinstance(inv["skills"], list)
    assert inv["generated_by"] == "tools/gen_skill_tree.py"


def test_inventory_counts():
    inv = load_inventory()
    skills = inv["skills"]
    derived = {
        "total": len(skills),
        "portable": sum(1 for s in skills if s["status"] == "portable"),
        "provider_native": sum(1 for s in skills
                               if s["status"] == "provider-native"),
    }
    assert inv["counts"] == derived, (inv["counts"], derived)
    assert derived["total"] == 50
    assert derived["portable"] == 47
    assert derived["provider_native"] == 3


def test_inventory_matches_manifest():
    m = {s["name"]: s for s in load_manifest()["skills"]}
    inv = {s["name"]: s for s in load_inventory()["skills"]}
    assert set(m) == set(inv), "inventory skill set != manifest skill set"
    for name, mrec in m.items():
        irec = inv[name]
        assert irec["status"] == mrec["status"], name
        assert irec["core"] == bool(mrec.get("core")), name
        assert irec["providers"]["claude"] == ("claude" in mrec["providers"]), name
        assert irec["providers"]["gpt"] == ("gpt" in mrec["providers"]), name


def test_inventory_skill_set_matches_fixture():
    fx = load_fixture()
    inv = load_inventory()
    names = {s["name"] for s in inv["skills"]}
    assert names == set(fx["portable"]) | set(fx["provider_native"])
    portable = {s["name"] for s in inv["skills"] if s["status"] == "portable"}
    native = {s["name"] for s in inv["skills"]
              if s["status"] == "provider-native"}
    assert portable == set(fx["portable"])
    assert native == set(fx["provider_native"])


def test_exclusion_records_for_native_only():
    for s in load_inventory()["skills"]:
        if s["status"] == "provider-native":
            exc = s.get("exclusion")
            assert exc is not None, s["name"]
            assert exc["core"] is False and exc["gpt"] is False, s["name"]
            assert isinstance(exc["reason"], str) and len(exc["reason"]) > 10, s["name"]
            assert "gpt" in exc["reason"].lower(), s["name"]
        else:
            assert "exclusion" not in s, s["name"]


# --------------------------------------------------------------------------- #
# On-disk tree shape (mandatory, no private source)
# --------------------------------------------------------------------------- #

def test_portable_dirs_have_exactly_core_and_two_adapters():
    for s in load_manifest()["skills"]:
        if s["status"] != "portable":
            continue
        name = s["name"]
        d = SKILLS_DIR / name
        assert (d / "core.md").is_file(), f"{name}: missing core.md"
        assert (d / "providers" / "claude.md").is_file(), f"{name}: missing claude.md"
        assert (d / "providers" / "gpt.md").is_file(), f"{name}: missing gpt.md"


def test_native_dirs_have_only_claude_adapter():
    for s in load_manifest()["skills"]:
        if s["status"] != "provider-native":
            continue
        name = s["name"]
        d = SKILLS_DIR / name
        assert (d / "providers" / "claude.md").is_file(), f"{name}: missing claude.md"
        assert not (d / "core.md").exists(), f"{name}: unexpected core.md"
        assert not (d / "providers" / "gpt.md").exists(), f"{name}: unexpected gpt.md"


def test_tree_matches_inventory_booleans():
    for s in load_inventory()["skills"]:
        name = s["name"]
        d = SKILLS_DIR / name
        assert (d / "core.md").is_file() == s["core"], name
        assert (d / "providers" / "claude.md").is_file() == s["providers"]["claude"], name
        assert (d / "providers" / "gpt.md").is_file() == s["providers"]["gpt"], name


def test_file_counts_across_tree():
    cores = list(SKILLS_DIR.glob("*/core.md"))
    claude = list(SKILLS_DIR.glob("*/providers/claude.md"))
    gpt = list(SKILLS_DIR.glob("*/providers/gpt.md"))
    assert len(cores) == 47, len(cores)
    assert len(claude) == 50, len(claude)   # 47 portable + 3 native
    assert len(gpt) == 47, len(gpt)


def test_no_private_absolute_paths_in_migrated_tree():
    offenders = []
    for md in SKILLS_DIR.rglob("*.md"):
        if PRIVATE_PATH_RE.search(md.read_text(encoding="utf-8")):
            offenders.append(str(md.relative_to(REPO_ROOT)))
    assert not offenders, "private absolute path leaked:\n" + "\n".join(offenders)


def test_generator_and_inventory_have_no_private_paths():
    for p in (REPO_ROOT / "tools" / "gen_skill_tree.py", INVENTORY_PATH,
              Path(__file__).resolve()):
        # a bare "C:\\Users\\abero\\"-style absolute path must never be committed;
        # the generator's neutralization regex uses a capture group, not that literal.
        assert not re.search(r"[A-Za-z]:\\Users\\abero\\", p.read_text(encoding="utf-8")), p


# --------------------------------------------------------------------------- #
# Operator-privacy leak guard (STRENGTHENED, no private source needed)
# --------------------------------------------------------------------------- #
# The public tree must never carry the operator's Windows username, home path,
# harness session-dir slug, or private second-brain (.claude/projects) path. The
# `abero(?![a-z])` token catches the bare username WITHOUT flagging the legitimate
# public org name `aberson/...`.
_LEAK_PATTERNS = [
    ("session-dir slug (c--Users-abero...)", re.compile(r"c--Users-abero")),
    ("home path (<drive>:/Users/abero)", re.compile(r"[A-Za-z]:[\\/]Users[\\/]abero")),
    ("/Users/<user>/ path", re.compile(r"[\\/]Users[\\/]abero")),
    ("private harness projects path", re.compile(r"\.claude[\\/]projects[\\/]")),
    ("bare operator username 'abero'", re.compile(r"abero(?![a-z])")),
]


def _find_leaks(text):
    return [name for name, rx in _LEAK_PATTERNS if rx.search(text)]


def test_leak_detector_reds_on_planted_leak():
    # ANCHOR: prove the detector goes RED on every private form (drive, ~, slug,
    # projects path) and stays green on the legitimate public org name. The drive
    # anchor uses '/' so this test file itself carries no committed backslash home
    # path (test_generator_and_inventory_have_no_private_paths guards that).
    # '.claude/projects' is assembled from parts so this file carries no literal
    # load-bearing '.claude/' path (the Step-34 router guard scans tests/).
    proj = "." + "claude" + "/projects/"
    assert _find_leaks("C:/Users/abero/dev/.plan-expedite-state.x")
    assert _find_leaks("~/" + proj + "c--Users-abero-dev/memory/MEMORY.md")
    assert _find_leaks("a bare c--Users-abero-dev slug in prose")
    assert _find_leaks(proj + "c--Users-abero-dev/memory/")
    assert not _find_leaks("gh -R aberson/coding-root issue list  # public org, ok")


def test_no_private_leak_in_migrated_tree():
    offenders = []
    for md in SKILLS_DIR.rglob("*.md"):
        hits = _find_leaks(md.read_text(encoding="utf-8"))
        if hits:
            offenders.append(f"{md.relative_to(REPO_ROOT)}: {hits}")
    inv_hits = _find_leaks(INVENTORY_PATH.read_text(encoding="utf-8"))
    if inv_hits:
        offenders.append(f"skills/inventory.json: {inv_hits}")
    assert not offenders, "operator-private leak in public tree:\n" + "\n".join(offenders)


# --------------------------------------------------------------------------- #
# Global-asset rewrite guard: a legacy '.claude/...' path WITH a declared neutral
# equivalent must be fully rewritten (fix #3); the dangling 'skills/_shared/' form
# must not appear (fix #2). The must-rewrite list is DERIVED from the manifest's
# global_support_assets (not hand-listed) -- which also keeps a literal
# '<dot>claude/' string out of this test's source (the Step-34 router guard flags
# load-bearing '.claude/' path literals in tests/).
# --------------------------------------------------------------------------- #

def _must_rewrite_legacy_paths():
    ga = load_manifest()["global_support_assets"]
    legacy = [g["source"] for g in ga if g["source"].startswith(".claude")]
    legacy.append("skills/_shared/")  # the dangling form fix #2 must eliminate
    return legacy


def test_global_asset_paths_fully_rewritten():
    offenders = []
    must = _must_rewrite_legacy_paths()
    for md in SKILLS_DIR.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        for legacy in must:
            if legacy in text:
                offenders.append(f"{md.relative_to(REPO_ROOT)}: unrewritten '{legacy}'")
    assert not offenders, "legacy path with a neutral equivalent still present:\n" + \
        "\n".join(offenders)


def test_shared_dest_divergence_is_intentional():
    # The manifest (locked) declares the EVENTUAL canonical `_shared` home as
    # skills/_shared/, but that dir does not exist yet, so migrated refs point at the
    # EXISTING repo-root _shared/ for today's resolvability. This test documents the
    # deliberate divergence so a future global-support-asset step (which creates
    # skills/_shared/ and must re-point these refs) notices before recreating the
    # dangling defect. See tools/gen_skill_tree.py module docstring.
    ga = {g["source"]: g["dest"] for g in load_manifest()["global_support_assets"]}
    shared_src = "." + "claude" + "/skills/_shared/"
    assert ga.get(shared_src) == "skills/_shared/", "manifest _shared dest changed"
    assert (REPO_ROOT / "_shared").is_dir(), "repo-root _shared/ must exist today"
    assert not (REPO_ROOT / "skills" / "_shared").exists(), \
        "skills/_shared/ now exists -- re-point migrated refs and update this guard"
    # no migrated ref may use the manifest's (not-yet-existent) skills/_shared/ dest.
    for md in SKILLS_DIR.rglob("*.md"):
        assert "skills/_shared/" not in md.read_text(encoding="utf-8"), md


# --------------------------------------------------------------------------- #
# COMPREHENSIVE intra-repo reference reachability (fix #6, no private source).
#
# Scans EVERY migrated file under skills/ for BOTH markdown-link targets AND
# backtick-quoted / bare repo-relative path tokens, and asserts each INTERNAL ref
# resolves to a real repo file/dir. The allowlist is for known-EXTERNAL prefixes
# ONLY -- every internal ref (anything under skills/, _shared/, config/, runtime/,
# tests/, documentation/, tools/, or a ./..-relative path) MUST resolve. A stranded
# home/drive prefix on a repo path (`~/skills/...`, `<drive>:/...`, `~/.claude/...`)
# is ALWAYS a defect. A path under a declared support_assets dest is deferred to a
# later migration step and is the only INTERNAL exception. This wide net is the
# audit tool -- its full failure list is the authoritative to-fix list.
# --------------------------------------------------------------------------- #

_REPO_ROOTS = ("skills", "_shared", "config", "runtime", "tests", "documentation", "tools")
# ".claude"/".claude" prefixes (rules/, external references/*, task-state, hooks,
# ...) are the only EXTERNAL .claude allowance; a home/drive prefix in FRONT of them
# is still a defect (handled by _STRANDED_RE first). Assembled without a literal
# "<dot>claude/" to keep the Step-34 router guard green.
_DOTCLAUDE = "." + "claude"
_EXT_PREFIXES = (_DOTCLAUDE + "/", _DOTCLAUDE + "\\", "http://", "https://",
                 "mailto:", "#")
# a stranded operator-home / drive prefix sitting in front of a .claude or repo root.
_STRANDED_RE = re.compile(
    r"^(?:~|[A-Za-z]:)[\\/](?:" + _DOTCLAUDE +
    r"|skills|_shared|config|runtime|tests|documentation|tools)[\\/]")
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_BT_RE = re.compile(r"`([^`\n]+)`")
# a bare (non-link, non-backtick) token that LOOKS like a repo/home path.
_BARE_RE = re.compile(
    r"(?<![\w`/\\.-])((?:~[\\/]|[A-Za-z]:[\\/]|\.{1,2}[\\/]|"
    r"(?:skills|_shared|config|runtime|tests|documentation|tools)[\\/])"
    r"[\w./\\<>:#-]*)")


def _support_dests():
    dests = set()
    for s in load_manifest()["skills"]:
        for a in s.get("support_assets", []):
            dests.add(a["dest"].rstrip("/"))
    return dests


# Real skill-mesh-repo top-level content dirs (a relative ref resolving to a FIRST
# segment outside this set -- references/, rules/, docs/, ... -- is a legacy-external
# citation, not a broken repo ref).
_REAL_DIRS = ("skills", "_shared", "config", "runtime", "tests", "documentation", "tools")
# The repo's OWN generated-artifact namespaces: an absolute backtick/bare ref here
# that does not resolve is a genuine defect (fabricated/dangling), never an
# illustrative user-project example (which live under documentation/ and tests/).
_ARTIFACT_DIRS = ("skills/", "_shared/")


def _clean_ref(raw):
    """Reduce a raw candidate to its path core (strip anchor, ::symbol, wrappers,
    trailing punctuation)."""
    tok = raw.strip().strip("`\"'")
    tok = tok.split()[0] if tok.split() else ""
    tok = tok.split("#")[0].split("::")[0]
    return tok.rstrip(".,;:)\"'`")


def _ref_defect(core, fdir, support, is_link):
    """Defect reason for a reference, else None. Markdown links must resolve if
    internal (they render as clickable repo links). Backtick/bare TOKENS are
    citations, so only a stranded home/drive prefix or an unresolved ref in the
    repo's own artifact namespaces (skills/, _shared/, or an extension-bearing
    config//runtime//tests/calibration/) counts -- illustrative user-project example
    paths (documentation/*, tests/test_*, prose runtime/full) are not repo refs."""
    if not core or any(c in core for c in "<>*"):
        return None  # template / glob placeholder
    if _STRANDED_RE.match(core):
        return "stranded home/drive prefix on a repo path"
    if (core.startswith(_EXT_PREFIXES) or core.startswith("~")
            or core.startswith("mailto:")):
        return None  # external (.claude/*, http, ~-home generic, mailto)
    if core.startswith(tuple(r + "/" for r in _REAL_DIRS)):
        rel, target = core, (REPO_ROOT / core)
    elif core.startswith(("./", "../")):
        if not is_link:
            return None  # a relative backtick/bare token is a prose citation
            #             (illustrative output dir / sibling project / worktree),
            #             not a clickable repo link -- only links are resolved here.
        resolved = (fdir / core).resolve()
        try:
            rel = resolved.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return None  # escapes the repo -> external workspace doc, allowed
        if rel.split("/")[0] not in _REAL_DIRS:
            return None  # ../../references, ../../rules, ... -> legacy-external
        target = resolved
    else:
        return None  # not a repo-relative path token
    if target.is_file() or target.is_dir():
        return None
    if any(rel == d or rel.startswith(d + "/") for d in support):
        return None  # declared support asset, migrated in a later step
    if is_link:
        return "nonexistent repo path (broken markdown link)"
    # backtick/bare token: flag only the repo's own artifact namespaces
    if rel.startswith(_ARTIFACT_DIRS):
        return "nonexistent repo path"
    if rel.split("/")[0] in ("config", "runtime") and re.search(r"\.\w+$", rel):
        return "nonexistent repo path"
    if rel.startswith("tests/calibration/"):
        return "nonexistent repo path"
    return None  # illustrative user-project example path (documentation/, tests/, prose)


def _reference_offenders(md_path, text, support):
    fdir = md_path.parent
    seen, out = set(), []
    for tgt in _LINK_RE.findall(text):
        core = _clean_ref(tgt)
        if not core or core in seen:
            continue
        seen.add(core)
        reason = _ref_defect(core, fdir, support, is_link=True)
        if reason:
            out.append(f"{core}  ({reason})")
    tokens = list(_BT_RE.findall(text)) + [m.group(1) for m in _BARE_RE.finditer(text)]
    for raw in tokens:
        core = _clean_ref(raw)
        if not core or core in seen:
            continue
        seen.add(core)
        reason = _ref_defect(core, fdir, support, is_link=False)
        if reason:
            out.append(f"{core}  ({reason})")
    return out


def test_reachability_reds_on_planted_defects():
    # ANCHOR: the comprehensive scan MUST go red on a stranded ~/ ref, a nonexistent
    # skills/<x>/nope.md backtick ref, and a dangling relative markdown link.
    f = SKILLS_DIR / "build-phase" / "core.md"  # real location for ../ resolution
    support = _support_dests()
    assert _ref_defect("~/skills/review-gauntlet/core.md", f.parent, support, False)
    assert _ref_defect("skills/build-phase/nope.md", f.parent, support, False)
    assert _ref_defect("../../_shared/DOES_NOT_EXIST.md", f.parent, support, True)
    assert _ref_defect(_DOTCLAUDE + "/skills/review-gauntlet/SKILL.md", f.parent, support, False) is None
    # ...and stay green on real refs, external refs, placeholders, support assets
    assert _ref_defect("../review-gauntlet/core.md", f.parent, support, True) is None
    assert _ref_defect(_DOTCLAUDE + "/rules/code-quality.md", f.parent, support, False) is None
    assert _ref_defect("<workspace-memory>/MEMORY.md", f.parent, support, False) is None
    assert _ref_defect("skills/skill-iterate/scripts/adversarial_calibration.py",
                       f.parent, support, False) is None
    assert _ref_defect("documentation/foo-plan.md", f.parent, support, False) is None


def test_intra_repo_refs_resolve():
    support = _support_dests()
    offenders = []
    for md in SKILLS_DIR.rglob("*.md"):
        for b in _reference_offenders(md, md.read_text(encoding="utf-8"), support):
            offenders.append(f"{md.relative_to(REPO_ROOT)}: {b}")
    assert not offenders, (f"{len(offenders)} dangling/malformed intra-repo "
                           "reference(s):\n" + "\n".join(offenders))


# --------------------------------------------------------------------------- #
# Clause-normalization sensitivity (fix #5): a genuine slash-joined PROSE reword
# must be detected; a path rewrite must stay invisible.
# --------------------------------------------------------------------------- #

def test_normalize_detects_prose_reword_but_hides_path_rewrite():
    nz = gen_skill_tree.normalize_clause_lines
    assert nz("the producer/consumer split") != nz("the producer/user split")
    assert nz("Block/Nit/FYI tiers") != nz("Block/Nit/WOW tiers")
    assert nz("load [c](../../skills/_shared/judge-core.md)") == \
        nz("load [c](../../_shared/judge-core.md)")


# --------------------------------------------------------------------------- #
# Clause preservation (optional; skips without the READ-ONLY legacy source)
# --------------------------------------------------------------------------- #

def _legacy_root():
    root = os.environ.get("SKILL_MESH_LEGACY_SOURCE")
    return Path(root) if root else None


def test_migrated_tree_reproduces_from_legacy_and_preserves_clauses():
    root = _legacy_root()
    if root is None or not (root / ".claude").is_dir():
        pytest.skip("legacy source not present (set SKILL_MESH_LEGACY_SOURCE to verify)")
    manifest = gen_skill_tree.load_manifest()
    portable, native = gen_skill_tree.skill_sets(manifest)
    support = gen_skill_tree.support_dests(manifest)
    plan = gen_skill_tree.build_plan(manifest)

    drift = []          # committed bytes != deterministic transform output
    clause_loss = []    # normalized prose differs (a clause dropped or reworded)
    for rec in plan:
        legacy_text = (root / rec["legacy_rel"]).read_bytes().decode("utf-8")
        expected = gen_skill_tree.transform(
            legacy_text, rec["legacy_dir_parts"], rec["dest_dir"],
            portable, native, support)
        committed = (REPO_ROOT / rec["dest_rel"]).read_bytes().decode("utf-8")
        if committed != expected:
            drift.append(rec["dest_rel"])
        if gen_skill_tree.normalize_clause_lines(legacy_text) != \
                gen_skill_tree.normalize_clause_lines(committed):
            clause_loss.append(f"{rec['dest_rel']}  <-  {rec['legacy_rel']}")

    assert not drift, ("committed tree drifted from a fresh generator run "
                       "(re-run tools/gen_skill_tree.py):\n" + "\n".join(drift))
    assert not clause_loss, ("clause preservation failed (prose differs beyond "
                             "path tokens):\n" + "\n".join(clause_loss))


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
