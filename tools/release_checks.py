"""Production package-integrity check functions for the skill-mesh release gate
(Step 38 of documentation/provider-neutral-skill-mesh-plan.md).

Every function here is a pure defect-finder: given a tree (or a manifest dict, or
a doc's text), it returns a list of human-readable defect strings (empty == clean).
Nothing here re-implements a builder -- distribution trees are always produced by
shelling out to the REAL tools/build-distributions.ps1 (see tests/package-integrity/
test_release_gates.py and tests/release/test_release_script.py), never a parallel
generator that could drift from it (measurement-validity: score the production
artifact, don't re-derive one).

tools/release.ps1's CHECK phase runs `python -m pytest tests/package-integrity`
FROM WITHIN the staged release tree, so the exact same test code that gates a
normal `pytest tests/` run also gates a release -- there is only one checker.

Seven checks, matching plan Step 38's Done-when list:
  1. find_broken_local_links      -- LINK CHECKER
  2. manifest_completeness_defects -- MANIFEST COMPLETENESS
  3. distribution_drift_defects    -- SOURCE -> DISTRIBUTION DRIFT
  4. wrapper_core_reference_defects -- PROVIDER-WRAPPER / CORE-REFERENCE
  5. readme_skill_count_defects    -- SKILL-COUNT
  6. readme_claim_defects          -- README-CLAIM
  7. tracked_dist_defects          -- NO TRACKED GENERATED DISTRIBUTION
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #


def load_manifest(repo_root: Path) -> dict:
    with open(repo_root / "config" / "skill-manifest.json", encoding="utf-8") as f:
        return json.load(f)


def _tree_snapshot(root: Path) -> dict:
    """Map of posix-relative path -> file bytes for every file under root."""
    snap = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            snap[p.relative_to(root).as_posix()] = p.read_bytes()
    return snap


def _safe_repo_path(repo_root: Path, rel: str):
    """Join a manifest-declared, repo-root-relative path and verify the
    resolved result stays CONTAINED within repo_root (mirrors
    runtime/path-guard.ps1's Resolve-SafePath containment check on the
    PowerShell side -- a manifest is untrusted input, same as build-
    distributions.ps1 already treats it). Returns the resolved Path, or None
    for an empty/missing value or a path that escapes the root (a traversal
    like '../../etc/passwd') -- callers treat None as "does not exist"."""
    if not rel:
        return None
    try:
        resolved = (repo_root / rel).resolve()
        resolved.relative_to(repo_root.resolve())
    except (ValueError, OSError):
        return None
    return resolved


def _file_exists_within(repo_root: Path, rel: str) -> bool:
    p = _safe_repo_path(repo_root, rel)
    return p is not None and p.is_file()


# --------------------------------------------------------------------------- #
# 1. LINK CHECKER
# --------------------------------------------------------------------------- #

# Markdown link: '[label](target)' or '[label](target "Title")'. The capture
# is intentionally greedy-minimal up to the FIRST ')' -- a target containing a
# literal, unescaped ')' (rare, unsupported by plain CommonMark without
# <angle-bracket> wrapping) is out of scope; _clean_link_target below strips a
# trailing hover-title so that part never leaks into the resolved path.
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# HTML image / picture-source references: <img src="...">, <source srcset="...">.
# README's diagrams use exactly these two forms (dark/light <picture> pairs).
_HTML_REF_RE = re.compile(r'<(?:img|source)\b[^>]*\b(?:src|srcset)=["\']([^"\']+)["\']', re.I)
_TITLE_RE = re.compile(r'^(\S+)\s+(?:"[^"]*"|\'[^\']*\')$')


def _clean_link_target(raw: str) -> str:
    tok = raw.strip()
    m = _TITLE_RE.match(tok)
    if m:
        tok = m.group(1)
    return tok.split("#", 1)[0].strip()


def find_broken_local_links(doc_paths, root: Path):
    """Every local link/reference target in `doc_paths` (README.md +
    documentation/**/*.md) -- markdown links AND HTML `<img src=...>` /
    `<source srcset=...>` -- must resolve to a real file/dir under `root` (the
    release tree). External (http/https/mailto), anchor-only, and
    template/glob placeholder targets are skipped; a target that resolves
    OUTSIDE `root` entirely is treated as an external citation (not a
    package-integrity defect -- the reachability audit in
    tests/package-integrity/test_skill_tree.py already covers that class for
    the migrated skills/ tree)."""
    root_r = root.resolve()
    offenders = []
    for doc in doc_paths:
        if not doc.is_file():
            continue
        text = doc.read_text(encoding="utf-8")
        fdir = doc.parent
        raw_targets = [m.group(1) for m in _LINK_RE.finditer(text)]
        raw_targets += [m.group(1) for m in _HTML_REF_RE.finditer(text)]
        for raw in raw_targets:
            target = _clean_link_target(raw)
            if not target:
                continue
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if any(c in target for c in "<>*"):
                continue
            resolved = (fdir / target).resolve()
            try:
                resolved.relative_to(root_r)
            except ValueError:
                continue  # escapes the release root -- external, not a defect
            if not resolved.exists():
                offenders.append(f"{doc}: [{raw}] -> missing {resolved}")
    return offenders


# --------------------------------------------------------------------------- #
# 2. MANIFEST COMPLETENESS
# --------------------------------------------------------------------------- #


def manifest_completeness_defects(manifest: dict, repo_root: Path):
    """Every manifest entry has its required neutral core (unless
    provider-native/core:null) and its declared provider adapters, all of which
    must exist on disk; and every skills/<name>/ directory on disk has a
    corresponding manifest entry (no orphans)."""
    defects = []
    names = set()
    for s in manifest.get("skills", []):
        name = s.get("name", "<unnamed>")
        names.add(name)
        status = s.get("status")
        core = s.get("core")
        providers = s.get("providers", {})
        if status == "portable":
            if not core:
                defects.append(f"{name}: portable skill missing 'core' in manifest")
            elif not _file_exists_within(repo_root, core):
                defects.append(f"{name}: declared core '{core}' does not exist on disk (or escapes the release root)")
            for prov in ("claude", "gpt"):
                rel = providers.get(prov)
                if not rel:
                    defects.append(f"{name}: portable skill missing '{prov}' adapter in manifest")
                elif not _file_exists_within(repo_root, rel):
                    defects.append(f"{name}: declared {prov} adapter '{rel}' does not exist on disk (or escapes the release root)")
        elif status == "provider-native":
            if core:
                defects.append(f"{name}: provider-native skill has a non-null core")
            if "gpt" in providers:
                defects.append(f"{name}: provider-native skill has a gpt adapter")
            rel = providers.get("claude")
            if not rel:
                defects.append(f"{name}: provider-native skill missing claude adapter")
            elif not _file_exists_within(repo_root, rel):
                defects.append(f"{name}: declared claude adapter '{rel}' does not exist on disk (or escapes the release root)")
        else:
            defects.append(f"{name}: unknown status '{status}'")

    skills_root = repo_root / "skills"
    if skills_root.is_dir():
        for entry in sorted(skills_root.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name == "_shared":
                continue
            if entry.name not in names:
                defects.append(f"orphan skill directory not in manifest: skills/{entry.name}")
    return defects


# --------------------------------------------------------------------------- #
# 3. SOURCE -> DISTRIBUTION DRIFT
# --------------------------------------------------------------------------- #


def distribution_drift_defects(reference_root: Path, fresh_root: Path):
    """Compare a previously-generated distribution tree (`reference_root`, e.g.
    the release-staged dist/) against a FRESH regeneration from source
    (`fresh_root`, always produced by literally re-invoking
    tools/build-distributions.ps1). Any file-set or content difference is drift:
    either the reference is stale (hand-edited or left over from an older
    source state) or the build is non-deterministic."""
    ref = _tree_snapshot(reference_root)
    fresh = _tree_snapshot(fresh_root)
    defects = []
    for p in sorted(set(ref) - set(fresh)):
        defects.append(f"stale file in reference, absent from a fresh rebuild: {p}")
    for p in sorted(set(fresh) - set(ref)):
        defects.append(f"fresh rebuild produces {p} which the reference lacks")
    for p in sorted(set(ref) & set(fresh)):
        if ref[p] != fresh[p]:
            defects.append(f"content drift: {p} differs between the reference and a fresh rebuild")
    return defects


# --------------------------------------------------------------------------- #
# 4. PROVIDER-WRAPPER / CORE-REFERENCE
# --------------------------------------------------------------------------- #

_CANONICAL_SOURCE_RE = re.compile(r"Canonical source:\s*(\S+)")
# A BARE 'core.md' token (the "Core: core.md" line build-distributions.ps1's
# Repoint-CoreReference produces for a portable skill) -- deliberately NOT
# matched when 'core.md' is part of a longer identifier or path (a deep
# repo-rooted reference like '../../judge-ui/core.md' pointing at ANOTHER
# skill's core, or a filename like 'judge-core.md' that merely ENDS with
# 'core.md'), either of which names a different file and implies no
# co-located sibling requirement.
_BARE_CORE_REF_RE = re.compile(r"(?<![\w/.-])core\.md(?![\w])")


def wrapper_core_reference_defects(dist_root: Path, repo_root: Path):
    """Every generated wrapper (SKILL.md) must resolve within the allowed
    canonical dist root, and its declared core reference (the provenance
    'Canonical source:' line, plus a co-located core.md when the launcher body
    references one) must point at a core that actually exists under repo_root."""
    defects = []
    dist_root_r = dist_root.resolve()

    for md in sorted(dist_root.rglob("*.md")):
        try:
            md.resolve().relative_to(dist_root_r)
        except ValueError:
            defects.append(f"{md}: generated file escapes the canonical dist root {dist_root}")

    for skill_md in sorted(dist_root.rglob("SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        m = _CANONICAL_SOURCE_RE.search(text)
        if not m:
            defects.append(f"{skill_md}: missing 'Canonical source:' provenance line")
            continue
        core_ref = m.group(1)
        if not _file_exists_within(repo_root, core_ref):
            defects.append(f"{skill_md}: Canonical source '{core_ref}' does not exist under {repo_root} (or escapes it)")
        core_sibling = skill_md.parent / "core.md"
        if _BARE_CORE_REF_RE.search(text) and not core_sibling.is_file():
            defects.append(f"{skill_md}: launcher references core.md but no such file exists alongside it")
    return defects


# --------------------------------------------------------------------------- #
# 5. SKILL-COUNT
# --------------------------------------------------------------------------- #

_STATUS_LINE_RE = re.compile(r"(\d+)/(\d+)\s+skills are GPT-capable")


def readme_skill_count_defects(readme_text: str, manifest: dict):
    """The README's skill-count claim must equal the manifest-derived count
    (i.e. it is effectively GENERATED from the manifest, not hand-maintained --
    any hand-edit that drifts from the manifest is caught here)."""
    defects = []
    m = _STATUS_LINE_RE.search(readme_text)
    if not m:
        defects.append("README missing the 'N/N skills are GPT-capable' status line")
        return defects
    claimed_a, claimed_b = int(m.group(1)), int(m.group(2))
    portable = manifest["counts"]["portable"]
    if claimed_a != portable or claimed_b != portable:
        defects.append(
            f"README claims {claimed_a}/{claimed_b} GPT-capable skills; "
            f"manifest portable count is {portable}"
        )
    return defects


# --------------------------------------------------------------------------- #
# 6. README-CLAIM
# --------------------------------------------------------------------------- #

_SKILL_SELF_LINK_RE = re.compile(r"\[([a-z][a-z0-9-]*)\]\(\1/SKILL\.md\)")


def readme_claim_defects(readme_text: str, manifest: dict):
    """Every skill the README names as shipping (a `[name](name/SKILL.md)`
    self-referencing link -- the README's own convention for 'this skill is
    part of the package') must be a real entry in the release manifest. Catches
    a claim the manifest no longer supports (e.g. a stale link surviving after
    a skill is retired from the manifest, even if a stray file still lingers on
    disk -- MANIFEST is the authority for what the package claims to ship, disk
    presence alone is the LINK CHECKER's job)."""
    names = {s["name"] for s in manifest.get("skills", [])}
    referenced = {m.group(1) for m in _SKILL_SELF_LINK_RE.finditer(readme_text)}
    unknown = sorted(referenced - names)
    return [
        f"README links to skill '{n}/SKILL.md' which is not in the release manifest"
        for n in unknown
    ]


# --------------------------------------------------------------------------- #
# 7. NO TRACKED GENERATED DISTRIBUTION
# --------------------------------------------------------------------------- #


def tracked_dist_defects(tracked_paths):
    """`tracked_paths`: an iterable of git-tracked path strings (e.g. from
    `git ls-files`, either '/' or '\\' separated). A generated distribution tree
    (dist/) must never be committed."""
    defects = []
    for p in tracked_paths:
        norm = p.replace("\\", "/").strip()
        if norm == "dist" or norm.startswith("dist/"):
            defects.append(f"generated distribution path is tracked in git: {p}")
    return defects
