"""Migrate skill cores + provider adapters into the neutral skills/<name>/ tree.

Step 35 of the provider-neutral skill-mesh plan. Drives entirely off
config/skill-manifest.json (locked in Step 33): each skill's `migration` block
names the READ-ONLY legacy source paths and its `core`/`providers` entries name
the canonical destination paths. For every skill this generator reads the legacy
source, applies a deterministic, content-preserving transform (intra-repo path
references rewritten to the neutral layout; the operator's private home-directory
paths neutralized), and writes:

    portable skill  -> skills/<name>/core.md
                       skills/<name>/providers/claude.md
                       skills/<name>/providers/gpt.md
    provider-native -> skills/<name>/providers/claude.md   (no core, no gpt)

plus a machine-readable skills/inventory.json enumerating what exists per skill
and an explicit exclusion record for each provider-native skill.

Determinism: the transform is a pure function of its input, so the same source and
the same manifest always produce the same bytes. It touches only path tokens
(markdown link targets, the `Core:` header line, `.claude/...` citations, RELATIVE
`../`-anchored citations, and private absolute paths); every substantive prose clause
is preserved. It no longer FOLLOWS that a fresh run reproduces the committed tree --
see NOTE ON RE-RUNNING below; that claim held while the legacy source was intact and
the tree was generator-owned, and both of those stopped being true.

STEP 67 closed two gaps in that transform, both of which had left legacy path tokens
standing in the migrated tree:
  - a RELATIVE citation written as backtick or bare prose (not a markdown link, no
    `.claude/` prefix) was matched by no pass at all. `_REL_CITATION_RE` is that
    third syntax; it runs last, with fences and the already-rewritten links stashed.
  - `_map_neutral` mapped only two of the `references/*` targets. The seven workspace
    references Step 66 vendored into `_shared/` now map there too, via
    `VENDORED_SHARED_REFS` -- and only those seven, so a `references/*` document this
    package does not ship stays an honest external citation.

NOTE ON RE-RUNNING. This generator reads the legacy source, which the Step 50
consumer cutover overwrote; it can no longer be re-run against a reproducible root,
and the committed tree has since been hand-edited by Steps 62-66. The two additions
above therefore change no committed byte -- they are exercised by direct unit tests
of `transform()` in tests/package-integrity/test_skill_tree.py, which is also where
the retired legacy-reproduce gate used to live. (Its hermetic sibling,
tools/gen_manifest.py, needs no external root at all as of Step 67.)

Neutral-target mapping (`_map_neutral`) is HARDCODED, not read from the manifest's
`global_support_assets`. Two deliberate points where it is authoritative over the
manifest for TODAY's resolvability:
  - Shared assets resolve to the EXISTING repo-root `_shared/` (e.g. `../../_shared/
    judge-core.md`). The manifest declares the EVENTUAL canonical home as
    `skills/_shared/`; that dir does not exist yet, so pointing there would dangle.
    The later global-support-asset migration that creates `skills/_shared/` MUST
    re-point these refs. Until then a guard test asserts `skills/_shared/` never
    appears in a migrated ref.
  - The per-skill support-asset fallback is CONSERVATIVE: it only rewrites a tail
    that lands under a DECLARED `support_asset` dest, so an illustrative or gitignored
    runtime tail (e.g. `.judge-motion/<run-id>`) is never fabricated into a bogus
    `skills/...` path.

Usage:
    $env:SKILL_MESH_LEGACY_SOURCE = "<coding-root>"   # the READ-ONLY checkout
    python tools/gen_skill_tree.py
  or:
    python tools/gen_skill_tree.py --legacy-source <coding-root>

No absolute private path is embedded: the legacy source root must be supplied via
--legacy-source or the SKILL_MESH_LEGACY_SOURCE environment variable.
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"
INVENTORY_PATH = REPO_ROOT / "skills" / "inventory.json"

# Explicit, truthful reasons the 3 provider-native skills receive no neutral core
# and no GPT adapter (documentation/architecture.md sec 7.3). ASCII only.
EXCLUSION_REASONS = {
    "claude-oauth-auth": "Claude-native - Claude OAuth flow; excluded from GPT porting.",
    "context-slim": "Claude-native - Claude Code context management; excluded from GPT porting.",
    "judge-motion": "Claude-native - depends on Claude-native motion/vision capture; excluded from GPT porting.",
}

# Step 66 vendored seven workspace reference documents into the repo-root `_shared/`
# payload, so their legacy citations NOW have a neutral equivalent. Until then this
# generator mapped only TWO `references/*` targets (the two model-* files) and demoted
# every other one to plain prose -- which is why ten migrated cores ended up citing a
# `references/` directory this repository does not have.
#
# Keyed by the legacy `.claude/`-relative path rather than by leaf name, because the
# seven did not all come from one tree: six were vendored out of `references/` and
# `subagent-economy.md` out of `rules/` (it has no `references/` copy). The per-file
# sign-off lives in documentation/step-66-vendored-reference-decisions.md.
#
# ONLY these seven map. A `references/*` or `rules/*` target this package does NOT
# ship -- model-tiering.md, shakedown-engine.md, code-quality.md, ... -- stays
# external and is still demoted to prose. Fabricating a `_shared/` path for a document
# that is not in the payload would convert a truthful external citation into a
# dangling repo link, which is the failure mode the conservative support-asset
# fallback below already guards against.
VENDORED_SHARED_REFS = {
    "references/intake-engine.md": "_shared/intake-engine.md",
    "references/skill-pipeline.md": "_shared/skill-pipeline.md",
    "references/skill-role-taxonomy.md": "_shared/skill-role-taxonomy.md",
    "references/step-authoring.md": "_shared/step-authoring.md",
    "references/task-state-schema.md": "_shared/task-state-schema.md",
    "references/worktree-hygiene.md": "_shared/worktree-hygiene.md",
    "rules/subagent-economy.md": "_shared/subagent-economy.md",
}

# Markdown link: [label](target)  (label captured so a path-shaped label is fixed too)
_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
# The `Core:` header line inside a provider adapter names the neutral core file.
_CORE_LINE_RE = re.compile(r"(?m)^([ \t]*Core:[ \t]*)(\S+)([ \t]*)$")


# --------------------------------------------------------------------------- #
# Manifest -> migration plan
# --------------------------------------------------------------------------- #

def load_manifest() -> dict:
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def skill_sets(manifest: dict):
    """Return (portable_names, native_names) derived from the manifest status."""
    portable = {s["name"] for s in manifest["skills"] if s["status"] == "portable"}
    native = {s["name"] for s in manifest["skills"]
              if s["status"] == "provider-native"}
    return portable, native


def support_dests(manifest: dict):
    """Return the set of declared support_asset dest paths (bounds the conservative
    per-skill fallback in `_map_neutral` so no bogus `skills/...` path is fabricated
    from an illustrative/gitignored tail)."""
    dests = set()
    for s in manifest["skills"]:
        for a in s.get("support_assets", []):
            dests.add(a["dest"].rstrip("/"))
    return dests


def build_plan(manifest: dict):
    """Yield one migration record per file to write.

    Each record: {name, status, role, legacy_rel, dest_rel, legacy_dir_parts,
    dest_base}. Paths come straight from the manifest -- no hardcoded mapping.

    role is one of: 'core', 'claude', 'gpt'.
    legacy_dir_parts: POSIX path parts of the legacy source's parent directory
      relative to the '.claude/' root (used to resolve relative references).
    dest_base: relative prefix from the destination file's directory back to the
      'skills/' directory ('../' for a core.md, '../../' for a providers/*.md).
    """
    plan = []
    for s in manifest["skills"]:
        name = s["name"]
        status = s["status"]
        mig = s["migration"]
        # core (portable only)
        if s.get("core"):
            plan.append(_record(name, status, "core",
                                 mig["legacy_core"], s["core"]))
        # claude adapter (portable: SKILL-claude.md; native: SKILL.md)
        plan.append(_record(name, status, "claude",
                            mig["legacy_claude_adapter"],
                            s["providers"]["claude"]))
        # gpt adapter (portable only)
        if "gpt" in s["providers"]:
            plan.append(_record(name, status, "gpt",
                                 mig["legacy_gpt"], s["providers"]["gpt"]))
    return plan


def _record(name, status, role, legacy_rel, dest_rel):
    assert legacy_rel and legacy_rel.startswith(".claude/"), (name, role, legacy_rel)
    # parent dir of the legacy source, relative to the '.claude/' root
    inside = legacy_rel[len(".claude/"):]
    dir_parts = inside.split("/")[:-1]
    return {
        "name": name,
        "status": status,
        "role": role,
        "legacy_rel": legacy_rel,
        "dest_rel": dest_rel,
        "legacy_dir_parts": dir_parts,
        "dest_dir": posixpath.dirname(dest_rel),  # e.g. skills/<name>[/providers]
    }


# --------------------------------------------------------------------------- #
# Path-reference rewriting (legacy .claude layout -> neutral, resolvable repo)
# --------------------------------------------------------------------------- #
#
# Every intra-repo reference is rewritten so it RESOLVES WITHIN the published
# repo. Three reference syntaxes are handled: markdown links `[label](target)`,
# the adapter `Core:` header line, and backtick/bare absolute `.claude/...`
# citations. References with a declared neutral equivalent (documentation/
# architecture.md global_support_assets + the per-skill core/adapter mapping) are
# repointed to their REAL repo location; genuinely-external references
# (`.claude/rules/*`, task-state, hooks, ...) are demoted to plain prose (a broken
# markdown link is unwrapped to its label) and kept as citations; operator-private
# paths (home dir, harness session-dir slug, second-brain memory) are fully
# neutralized so no username, absolute path, or private slug leaks into the tree.


def _map_neutral(parts, portable, native, support):
    """Map a legacy '.claude/'-relative path (POSIX parts) to a REPO-ROOT-relative
    neutral path, or None when the path is genuinely external / private / not a
    real migrated artifact.

    Neutral targets: a portable skill's `core.md`/`providers/*.md`, a provider-native
    skill's `providers/claude.md`, the cross-skill SHARED assets at the EXISTING
    repo-root `_shared/` (see the module docstring on the `skills/_shared/` divergence),
    a per-skill support asset DECLARED in the manifest (`support` = the set of declared
    support_asset dests), and the hardcoded global-asset equivalents below
    (references/model-* -> config/, lib/* -> runtime//tests/). The per-skill fallback is
    CONSERVATIVE: an unrecognized/illustrative tail (e.g. a gitignored `.judge-motion/
    <run-id>` runtime path) is NOT rewritten into a fabricated `skills/...` path -> None.
    """
    if not parts:
        return None
    # The seven Step-66 vendored workspace references resolve to the shared payload.
    # Checked first and by FULL path, so `references/` and `rules/` each map only the
    # leaves this package actually ships (see VENDORED_SHARED_REFS).
    vendored = VENDORED_SHARED_REFS.get("/".join(parts))
    if vendored:
        return vendored
    tree = parts[0]
    if tree in ("skills", "skills-gpt"):
        if len(parts) >= 2 and parts[1] == "_shared":
            return "/".join(["_shared", *parts[2:]]) if len(parts) > 2 else "_shared"
        if len(parts) >= 2 and (parts[1] in portable or parts[1] in native):
            skill = parts[1]
            rest = parts[2:]
            if not rest:
                return (f"skills/{skill}/core.md" if skill in portable
                        else f"skills/{skill}/providers/claude.md")
            if len(rest) == 1:
                fname = rest[0]
                if fname == "SKILL-core.md":
                    return f"skills/{skill}/core.md"
                if fname == "SKILL-claude.md":
                    return f"skills/{skill}/providers/claude.md"
                if fname == "SKILL-gpt.md":
                    return f"skills/{skill}/providers/gpt.md"
                if fname == "SKILL.md":
                    return (f"skills/{skill}/core.md" if skill in portable
                            else f"skills/{skill}/providers/claude.md")
            # skill-local support asset -- only if it lands under a DECLARED dest
            # (never fabricate a path for an illustrative/gitignored runtime tail).
            candidate = "/".join(["skills", skill, *rest])
            if any(candidate == d or candidate.startswith(d.rstrip("/") + "/")
                   for d in support):
                return candidate
            return None
        return None
    if tree == "references":  # global-asset equivalents (architecture.md)
        rel = "/".join(parts[1:])
        if rel == "model-tier-map.json":
            return "config/model-tier-map.json"
        if rel == "model-mapping.md":
            return "config/model-mapping.json"
        return None
    if tree == "lib":
        if len(parts) >= 2:
            if parts[1] == "skill-router.ps1":
                return "runtime/skill-router.ps1"
            if parts[1] == "telemetry":
                return ("/".join(["runtime", "telemetry", *parts[2:]])
                        if len(parts) > 2 else "runtime/telemetry")
            if parts[1] == "calibration":
                return ("/".join(["tests", "calibration", *parts[2:]])
                        if len(parts) > 2 else "tests/calibration")
        return None
    return None


def _resolve_relative(legacy_dir_parts, target):
    """Resolve a RELATIVE reference against the legacy dir. Returns POSIX parts
    relative to the '.claude/' root, or None if it escapes '.claude/'."""
    joined = "/".join([*legacy_dir_parts, target]) if legacy_dir_parts else target
    norm = posixpath.normpath(joined)
    parts = norm.split("/")
    if not parts or parts[0] in ("..", "", "."):
        return None
    return parts


def _is_abs_home(path):
    """True for an absolute operator-home path (drive-letter or '~'-rooted)."""
    return bool(re.match(r"^[A-Za-z]:[\\/]", path)) or path.startswith("~")


def _neutral_for(path, legacy_dir_parts, portable, native, support):
    """Repo-root-relative neutral for a reference PATH (no anchor), or None if
    external / private / unresolvable. Absolute home paths are private -> None."""
    if _is_abs_home(path):
        return None
    if path.startswith(".claude/"):
        return _map_neutral(path[len(".claude/"):].split("/"), portable, native, support)
    parts = _resolve_relative(legacy_dir_parts, path)
    if parts is None:
        return None
    return _map_neutral(parts, portable, native, support)


# A visible link LABEL that is itself a legacy path reference (the adapter
# boilerplate `See [<legacy-path>](...)`, or a `_shared`/sibling asset label whose
# display text still names the legacy location) -- repointed to the neutral file so
# the label names a file that exists. Matches a relative path (./ or ../ rooted) or
# a bare SKILL-file name; a non-path label (e.g. `/build-step`, prose) is left as-is.
_LABEL_PATH_RE = re.compile(r"^(?:\.\.?/)+[\w./-]+$|^SKILL[-a-z]*\.md$")


def _rewrite_label(label, legacy_dir_parts, dest_dir, portable, native, support):
    core = label.strip().strip("`").strip()
    if not _LABEL_PATH_RE.match(core):
        return label
    neutral = _neutral_for(core, legacy_dir_parts, portable, native, support)
    if neutral is None:
        return label
    rel = posixpath.relpath(neutral, dest_dir)
    # preserve backtick wrapping if the original label was inline code
    return f"`{rel}`" if label.strip().startswith("`") else rel


def _rewrite_link(m, legacy_dir_parts, dest_dir, portable, native, support):
    label, target = m.group(1), m.group(2)
    path, sep, anchor = target.partition("#")
    if path == "" or path.startswith(("http://", "https://", "mailto:", "<")):
        return m.group(0)
    if any(c in path for c in "<>*"):
        return m.group(0)  # template/glob placeholder, not a real file -> leave
    neutral = _neutral_for(path, legacy_dir_parts, portable, native, support)
    if neutral is None:
        # external / private reference -> demote to plain-prose label (no broken
        # repo link, no leaked private path).
        return label
    rel = posixpath.relpath(neutral, dest_dir)
    new_label = _rewrite_label(label, legacy_dir_parts, dest_dir, portable, native, support)
    return f"[{new_label}]({rel}{sep}{anchor})"


def _rewrite_core_line(m, legacy_dir_parts, dest_dir, portable, native, support):
    prefix, target, suffix = m.group(1), m.group(2), m.group(3)
    path, sep, anchor = target.partition("#")
    neutral = _neutral_for(path, legacy_dir_parts, portable, native, support)
    if neutral is None:
        return m.group(0)
    return prefix + posixpath.relpath(neutral, dest_dir) + sep + anchor + suffix


# Absolute `.claude/...` citations in backtick/bare prose (never markdown links,
# verified against the legacy source), OPTIONALLY carrying a leading operator-home
# or coding-root prefix (`~/`, `<drive>:/Users/abero[/dev]/`). The prefix is
# CONSUMED (group 1 captures only the `.claude/...` tail) so the result is a clean
# repo-relative citation with no stranded `~/` or drive prefix -- for both a mapped
# neutral target AND an external `.claude/...` ref left as prose.
_ABS_CLAUDE_RE = re.compile(
    r"(?:~[\\/]|[A-Za-z]:[\\/]Users[\\/]abero(?:[\\/]dev)?[\\/])?"
    r"(\.claude[\\/][A-Za-z0-9._/\\\-]+)")


def _rewrite_abs_claude(m, portable, native, support):
    claude_ref = m.group(1)                       # '.claude/<tail>' (prefix dropped)
    tail = re.split(r"[\\/]", claude_ref)[1:]     # drop the leading '.claude'
    neutral = _map_neutral(tail, portable, native, support)
    return neutral if neutral else claude_ref


# ---- private path / harness session-slug neutralization (separator-agnostic) --
# Second-brain memory references (drive-, '~'-rooted, or bare) -> placeholder.
_MEM_RE = re.compile(
    r"(?:[A-Za-z]:[\\/]Users[\\/]abero[\\/]|~[\\/])?"
    r"\.claude[\\/]projects[\\/][^\s`\"')\\/]+[\\/]memory[\\/]?")
# Operator home / coding-root absolute paths (mixed separators tolerated: no
# same-separator backreference, so `C:\Users\abero/dev` cannot evade the scrub).
_HOME_DEV_RE = re.compile(r"[A-Za-z]:[\\/]Users[\\/]abero[\\/]dev(?=[\\/]|$|[^\w])")
_HOME_RE = re.compile(r"[A-Za-z]:[\\/]Users[\\/]abero(?=[\\/]|$|[^\w])")
# Residual harness session-dir slug (a direct encoding of the operator username).
_SLUG_RE = re.compile(r"[A-Za-z]--Users-abero(?:-[\w-]+)?")


def _scrub_private(text):
    text = _MEM_RE.sub("<workspace-memory>/", text)
    text = _HOME_DEV_RE.sub("<workspace>", text)
    text = _HOME_RE.sub("~", text)
    text = _SLUG_RE.sub("<workspace-id>", text)
    return text


_FENCE_RE = re.compile(r"```.*?```", re.S)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def _protect_code(text):
    """Stash fenced code blocks and any inline-code span that itself contains a
    full `[...](...)` markdown link (a literal link *syntax example*, e.g.
    `` `[path](path)` ``), so link rewriting never touches it. A backtick-wrapped
    link LABEL (e.g. ``[`../x/core.md`](../x/core.md)``) contains no `](` and is
    deliberately NOT protected, so its stale path label is still rewritten."""
    spans = []

    def _stash(m):
        spans.append(m.group(0))
        return f"\x00{len(spans) - 1}\x00"

    text = _FENCE_RE.sub(_stash, text)
    text = _INLINE_CODE_RE.sub(
        lambda m: _stash(m) if "](" in m.group(0) else m.group(0), text)
    return text, spans


def _restore_code(text, spans):
    return re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], text)


# --------------------------------------------------------------------------- #
# THIRD reference syntax: a RELATIVE citation that is not a link (Step 67)
# --------------------------------------------------------------------------- #
# Markdown links and `.claude/...`-absolute citations were both rewritten; a
# RELATIVE path written as a backtick citation or bare prose (`../../references/
# task-state-schema.md`, `../../skills-gpt/<name>/SKILL-core.md`) was not, so it
# survived the migration pointing at the legacy layout. `_ABS_CLAUDE_RE` cannot see it
# -- it has no `.claude/` prefix to anchor on -- and `_LINK_RE` cannot either, because
# it is not a link.
#
# Anchored on one or more leading `../` segments: that is what makes a token a PATH
# rather than prose, and it is the shape every relative citation in the legacy sources
# uses. A bare `./x` is deliberately NOT matched (too close to ordinary prose), and the
# token must END on a word character, so `cd ../..` and a trailing sentence period are
# both left alone. The lookbehind rejects a token glued to a longer path but ADMITS a
# leading backtick, since a backtick citation is the main case this exists for.
#
# Conservative in the same way `_map_neutral`'s support-asset fallback is: a token with
# no declared neutral equivalent is returned UNCHANGED, never rewritten into a
# fabricated repo path.
_REL_CITATION_RE = re.compile(
    r"(?<![\w/\\.~-])((?:\.\./)+[A-Za-z0-9_.\-/]*[A-Za-z0-9_-])")


def _rewrite_rel_citation(m, legacy_dir_parts, dest_dir, portable, native, support):
    token = m.group(1)
    neutral = _neutral_for(token, legacy_dir_parts, portable, native, support)
    if neutral is None:
        return token
    return posixpath.relpath(neutral, dest_dir)


def _protect_fences_and_links(text):
    """Stash fenced code blocks AND whole markdown links before the relative-citation
    pass. Fences first, so a link inside a fence is carried away with it rather than
    stashed twice; links second, because by this point their targets are already
    NEUTRAL paths and re-resolving them against the legacy directory would corrupt
    correct output."""
    spans = []

    def _stash(m):
        spans.append(m.group(0))
        return f"\x00{len(spans) - 1}\x00"

    text = _FENCE_RE.sub(_stash, text)
    text = _LINK_RE.sub(_stash, text)
    return text, spans


def transform(text, legacy_dir_parts, dest_dir, portable, native, support):
    """Deterministic, clause-preserving migration transform for one file.

    `support` is the set of declared support_asset dest paths (from the manifest);
    it bounds the conservative per-skill fallback in `_map_neutral`.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # markdown links: rewrite only OUTSIDE code spans (in-code links are examples)
    text, code_spans = _protect_code(text)
    text = _LINK_RE.sub(
        lambda m: _rewrite_link(m, legacy_dir_parts, dest_dir, portable, native, support),
        text)
    text = _restore_code(text, code_spans)
    text = _CORE_LINE_RE.sub(
        lambda m: _rewrite_core_line(m, legacy_dir_parts, dest_dir, portable, native, support),
        text)
    text = _ABS_CLAUDE_RE.sub(
        lambda m: _rewrite_abs_claude(m, portable, native, support), text)
    # THIRD syntax LAST, with fences and the already-rewritten links stashed: every
    # relative token still standing at this point is a prose/backtick citation that no
    # earlier pass claimed.
    text, protected = _protect_fences_and_links(text)
    text = _REL_CITATION_RE.sub(
        lambda m: _rewrite_rel_citation(m, legacy_dir_parts, dest_dir, portable,
                                        native, support),
        text)
    text = _restore_code(text, protected)
    text = _scrub_private(text)
    return text


# --------------------------------------------------------------------------- #
# Clause-preservation normalization (shared with the source-bearing test)
# --------------------------------------------------------------------------- #

_NORM_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
# A file token ending in a known extension (tolerating a trailing quote/punct).
_NORM_EXT_RE = re.compile(
    r"\.(?:md|py|js|json|jsonl|ps1|ts|tsx|html|svg|toml|txt|ya?ml|sh|css|tsv)"
    r"(?=[\s\"'`)\].,;:>]|$)")
_NORM_DRIVE_RE = re.compile(r"[A-Za-z]:[\\/]")            # C:/... anywhere in token
_NORM_HOME_RE = re.compile(r"~[\\/]|\.claude[\\/]")       # ~/... or .claude/...
# a known repo/legacy root followed by a separator, or the unambiguous _shared dir.
_NORM_ROOTPATH_RE = re.compile(
    r"(?<![\w-])(?:skills|skills-gpt|config|runtime|tests|tools|documentation)/"
    r"|(?<![\w-])_shared(?![\w-])")
_NORM_RELPATH_RE = re.compile(r"(?<![\w])\.{1,2}[\\/]")   # ./ or ../
_NORM_PLACEHOLDER_RE = re.compile(r"<[A-Za-z][\w-]*>")


def _is_path_token(tok):
    """A GENUINE path/file token (ext, drive/home/rooted path, placeholder, or
    ./.. relative path) -- NOT arbitrary slash-joined prose like 'producer/
    consumer', 'Block/Nit', or 'PASS/FAIL', which stay visible so a reword is
    detected."""
    return bool(_NORM_EXT_RE.search(tok) or _NORM_DRIVE_RE.search(tok)
                or _NORM_HOME_RE.search(tok) or _NORM_ROOTPATH_RE.search(tok)
                or _NORM_RELPATH_RE.search(tok) or _NORM_PLACEHOLDER_RE.search(tok))


def normalize_clause_lines(text):
    """Clause-bearing lines with markdown links unwrapped to their label and
    genuine path/file tokens masked -- so a faithful path rewrite is invisible
    while a dropped/reworded PROSE clause (including a slash-joined prose token)
    is still detected.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _NORM_LINK_RE.sub(r"\1", text)  # unwrap [label](url) -> label
    out = []
    for ln in text.splitlines():
        toks = ["@" if _is_path_token(t) else t for t in ln.split()]
        s = " ".join(toks).strip()
        if s:
            out.append(s)
    return out


# --------------------------------------------------------------------------- #
# Inventory
# --------------------------------------------------------------------------- #

def build_inventory(manifest: dict) -> dict:
    skills = []
    for s in manifest["skills"]:
        name = s["name"]
        status = s["status"]
        rec = {
            "name": name,
            "status": status,
            "core": bool(s.get("core")),
            "providers": {
                "claude": "claude" in s["providers"],
                "gpt": "gpt" in s["providers"],
            },
        }
        if status == "provider-native":
            rec["exclusion"] = {
                "reason": EXCLUSION_REASONS[name],
                "core": False,
                "gpt": False,
            }
        skills.append(rec)
    counts = {
        "total": len(skills),
        "portable": sum(1 for s in skills if s["status"] == "portable"),
        "provider_native": sum(1 for s in skills
                               if s["status"] == "provider-native"),
    }
    return {
        "note": (
            "Machine-readable inventory of the migrated skills/<name>/ tree. "
            "Generated by tools/gen_skill_tree.py from config/skill-manifest.json. "
            "Portable skills carry a neutral core plus Claude and GPT adapters; "
            "provider-native skills carry only a Claude adapter and an explicit "
            "exclusion record."
        ),
        "generated_by": "tools/gen_skill_tree.py",
        "counts": counts,
        "skills": skills,
    }


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #

def _write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    # UTF-8, no BOM, LF endings (write bytes to dodge platform newline translation)
    path.write_bytes(text.encode("utf-8"))


def run(legacy_root: Path):
    manifest = load_manifest()
    portable, native = skill_sets(manifest)
    support = support_dests(manifest)
    plan = build_plan(manifest)
    written = 0
    for rec in plan:
        legacy_path = legacy_root / rec["legacy_rel"]
        raw = legacy_path.read_bytes().decode("utf-8")
        out = transform(raw, rec["legacy_dir_parts"], rec["dest_dir"],
                        portable, native, support)
        _write(REPO_ROOT / rec["dest_rel"], out)
        written += 1
    inventory = build_inventory(manifest)
    _write(INVENTORY_PATH, json.dumps(inventory, indent=2) + "\n")
    return written, inventory["counts"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legacy-source",
                    default=os.environ.get("SKILL_MESH_LEGACY_SOURCE"))
    args = ap.parse_args()
    if not args.legacy_source:
        sys.exit("error: set SKILL_MESH_LEGACY_SOURCE or pass --legacy-source "
                 "(the READ-ONLY coding-root checkout)")
    legacy_root = Path(args.legacy_source)
    if not (legacy_root / ".claude").is_dir():
        sys.exit(f"error: no .claude tree under legacy source: {legacy_root}")
    written, counts = run(legacy_root)
    print(f"wrote {written} skill files + skills/inventory.json")
    print(f"counts: {counts}")


if __name__ == "__main__":
    main()
