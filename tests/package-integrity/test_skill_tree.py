"""Structural + clause-preservation gate for the migrated skills/<name>/ tree (Step 35).

Two independent layers:

- STRUCTURAL (mandatory, needs NO private/legacy source): every portable skill
  dir has core.md + providers/claude.md + providers/gpt.md, and OPTIONALLY
  providers/codex.md (the additive third provider from Phase CP Step 3 -- 0 authored
  at that step, the pilot five at Step 4); every provider-native dir has ONLY
  providers/claude.md (no core.md, no gpt.md, no codex.md -- provider-native means
  Claude-only); the counts match the manifest (47 portable, 3 native, 50 total, 5
  codex); skills/inventory.json
  agrees with the manifest and the committed expected_inventory.json fixture; and
  no operator-private absolute path leaked into the migrated tree.

- TRANSFORM BEHAVIOR (mandatory, needs NO private/legacy source): the production
  migration transform is driven directly over synthetic inputs, covering the two
  reference syntaxes Step 67 added -- a RELATIVE `../`-anchored citation written as
  backtick or bare prose, and the seven Step-66 vendored `references/*` + `rules/*`
  targets that now resolve into `_shared/`.

RETIRED IN STEP 67: the clause-preservation layer that re-derived every migrated file
from the READ-ONLY legacy source and compared it to the committed bytes. It was
optional (it skipped without SKILL_MESH_LEGACY_SOURCE), and the Step 50 consumer
cutover OVERWROTE that source with this package's own installed output -- so setting
the variable no longer verifies anything: the run errors on missing `legacy_rel`
bytes. A gate whose only two outcomes are "skipped" and "wrong" is not a gate. The
mandatory layers above, plus the hermetic regeneration gate in
test_manifest_contract.py, are what replaced it.

Runnable via pytest (`python -m pytest tests/package-integrity`) or standalone.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"
FIXTURE_PATH = Path(__file__).resolve().parent / "expected_inventory.json"
INVENTORY_PATH = REPO_ROOT / "skills" / "inventory.json"
SKILLS_DIR = REPO_ROOT / "skills"

# Import the production generator (single source of truth for the migration
# transform and plan) -- reused, never re-implemented, by the transform tests below.
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
        # Additive third-provider tally (Phase CP Step 3), derived from the per-skill
        # booleans so the count and the records cannot disagree.
        "codex": sum(1 for s in skills if s["providers"]["codex"]),
    }
    assert inv["counts"] == derived, (inv["counts"], derived)
    assert derived["total"] == 50
    assert derived["portable"] == 47
    assert derived["provider_native"] == 3
    # 47 since Phase CP Step 8 (issue #125) added Cohort D's fourteen remaining
    # adapters on top of Cohort C's sixteen, Cohort B's twelve, and the pilot five --
    # every portable skill now carries a providers/codex.md.
    assert derived["codex"] == 47


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
        assert irec["providers"]["codex"] == ("codex" in mrec["providers"]), name


def test_inventory_codex_count_matches_the_manifest_count():
    """The two generators must agree on the codex tally.

    skills/inventory.json is owned by tools/gen_skill_tree.py and
    config/skill-manifest.json by tools/gen_manifest.py -- two separate producers
    counting the same thing off the same per-skill `providers` dicts. Regenerating one
    and not the other is the drift this catches, and it is a real risk here because the
    two are regenerated by different commands.
    """
    assert load_inventory()["counts"]["codex"] ==         load_manifest()["counts"]["codex"]


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
        # Provider-native is CLAUDE-ONLY, so a codex adapter here is a contradiction --
        # the tree-level twin of the manifest assertion in test_manifest_contract.py and
        # of the guard in gen_manifest.derived_skill_sets().
        assert not (d / "providers" / "codex.md").exists(),             f"{name}: unexpected codex.md (provider-native is Claude-only)"


def test_tree_matches_inventory_booleans():
    for s in load_inventory()["skills"]:
        name = s["name"]
        d = SKILLS_DIR / name
        assert (d / "core.md").is_file() == s["core"], name
        assert (d / "providers" / "claude.md").is_file() == s["providers"]["claude"], name
        assert (d / "providers" / "gpt.md").is_file() == s["providers"]["gpt"], name
        assert (d / "providers" / "codex.md").is_file() == s["providers"]["codex"], name


def test_file_counts_across_tree():
    cores = list(SKILLS_DIR.glob("*/core.md"))
    claude = list(SKILLS_DIR.glob("*/providers/claude.md"))
    gpt = list(SKILLS_DIR.glob("*/providers/gpt.md"))
    codex = list(SKILLS_DIR.glob("*/providers/codex.md"))
    assert len(cores) == 47, len(cores)
    assert len(claude) == 50, len(claude)   # 47 portable + 3 native
    assert len(gpt) == 47, len(gpt)
    # 47 since Phase CP Step 8 -- Step 4's pilot five, Cohort B's twelve (issue #123),
    # Cohort C's sixteen (issue #124), and Cohort D's fourteen (issue #125), on rails
    # that shipped empty at Step 3. This is a SPELLED count on purpose, exactly like
    # its three siblings: any step that authors more adapters must come here and state
    # the new number, so the catalog size is never silently redefined by a glob.
    assert len(codex) == 47, len(codex)


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
#
# STEP 66 widened this in two directions, because the five original patterns are all
# keyed on a drive letter, a home path or the username -- and the highest-value private
# token in the documents this repository now vendors carries none of them. The source
# line `~/.claude/projects/<slug>/<uuid>.jsonl` trips three of the five, but the RAW
# SESSION UUID on the line above it trips none: it is just 32 hex digits.
#
# 1. A hex-UUID pattern, so a raw harness session id is a leak on its own.
# 2. The sweep now covers `_shared/**` as well as `skills/**` -- see
#    `_LEAK_SWEEP_ROOTS`. Nothing scanned `_shared/` before this step, and `_shared/`
#    is exactly where the vendored workspace references land.

# RFC 4122 Appendix A's documentation UUID: the canonical "this is an example" value,
# used as an illustrative `run_id` in a JSON sample in skills/build-step/core.md. It
# identifies no session and no person. Exempted by LITERAL, never by shape -- any other
# UUID-shaped token is treated as a raw harness session id and reds. Keep this list at
# the one value that is already in the tree; a growing exemption list is how a real id
# eventually rides in.
_EXAMPLE_UUIDS = ("550e8400-e29b-41d4-a716-446655440000",)
_UUID_RE = re.compile(
    r"\b(?!(?:" + "|".join(re.escape(u) for u in _EXAMPLE_UUIDS) + r")\b)"
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")

_LEAK_PATTERNS = [
    ("session-dir slug (c--Users-abero...)", re.compile(r"c--Users-abero")),
    ("home path (<drive>:/Users/abero)", re.compile(r"[A-Za-z]:[\\/]Users[\\/]abero")),
    ("/Users/<user>/ path", re.compile(r"[\\/]Users[\\/]abero")),
    ("private harness projects path", re.compile(r"\.claude[\\/]projects[\\/]")),
    ("bare operator username 'abero'", re.compile(r"abero(?![a-z])")),
    ("raw harness session UUID", _UUID_RE),
]

# --------------------------------------------------------------------------- #
# STEP 66 (iteration 3): what this gate CLAIMS, per surface -- and who owns the rest.
# --------------------------------------------------------------------------- #
# Every pattern in `_LEAK_PATTERNS` keys on an IDENTIFIER -- a drive letter, a home
# path, the username, a session UUID. The scrub Step 66 actually performed spent most
# of its budget on two classes that carry none of those:
#
#   X  a pointer into the PRIVATE workspace repository's issue namespace
#   M  account-level cost / usage telemetry -- a number drawn from a private
#      measurement set
#
# The proof that the gap was inert rather than theoretical is Step 66's own iteration 1:
# it extended this sweep to `_shared/` AND landed fresh instances of both classes in
# `documentation/`, which was not a swept root at all. It is one now.
#
# But X and M are SEMANTIC classes, and a regex decides a SYNTACTIC one. The gap between
# the two is unbounded -- paraphrase, distance and vocabulary substitution each defeat
# any fixed shape. Iterations 1 and 2 each answered a review finding by fitting one more
# shape to the instance that had just escaped, and each time a further instance escaped;
# the second was a live member of M sitting in a file whose sign-off certified that very
# class handled. So the defect was never the pattern list, it was the CLAIM: an
# over-claiming gate is worse than no gate, because the team stops looking. Iteration 3
# fixes the claim instead of adding a third fitted shape.
#
# This gate therefore makes THREE DIFFERENT CLAIMS, and never mistakes one for another:
#
#   TIER 1  CATEGORICAL BANS over TWO BOUNDED SURFACES -- the seven `_shared/*.md`
#           documents carrying the Step 66 vendor banner, and every document declaring
#           itself a scrub RECORD of them. Whole CATEGORIES are forbidden outright
#           (issue-shaped pointers, shares and percentages, scaled or open-ended
#           magnitudes) rather than each private phrasing being recognised, so what the
#           rule claims IS the category it names, and that claim is decidable.
#           Deliberately strict: a false positive is resolved by REWORDING the offending
#           document and recording the adaptation, which is cheap across a handful of
#           files and unaffordable anywhere else. That is exactly why the bans are
#           scoped to those two surfaces and must never be pointed at an open root --
#           this repository carries hundreds of legitimate issue numbers and
#           percentages, and a gate that reds on all of them is one somebody switches
#           off within a week. See `_VENDORED_PAYLOAD_BANS` and `_tier1_graded_docs`.
#
#   TIER 2  TRIPWIRES over the open roots (`skills/`, `_shared/`, `documentation/`).
#           `_DISCLOSURE_PATTERNS` recognises shapes that have ACTUALLY ESCAPED into
#           this tree. It does not certify either class on any root, and a green run is
#           not evidence that X or M is absent from an open root -- only that no KNOWN
#           shape is present. A tripwire is maintained by widening it when a real new
#           phrasing is observed; believing that a widening certifies the class is the
#           anti-pattern this block exists to name.
#
#   TIER 3  THE PER-FILE HUMAN SIGN-OFF is the ONLY class-level authority
#           (`documentation/step-66-vendored-reference-decisions.md`, section 3).
#           Class-level absence is a judgment no shape rule reproduces: within one file
#           the sign-off keeps a public project name, drops a machine-local branch name,
#           and deliberately keeps a state-directory path -- three different verdicts on
#           tokens no regex can tell apart. A pointer spelled "Step 12 of the same
#           phase" carries no digit-magnitude and no decidable token at all. Tiers 1
#           and 2 ENFORCE; tier 3 DECIDES. Nothing below may be cited as establishing
#           that a class is absent.
#
# X is deliberately NOT "a bare #N". This repository carries hundreds of legitimate
# references to its OWN issues, and a gate that reds on every one of them gets turned
# off within a week. The disclosure is the number BOUND to another, private repository.
# Two bindings are recognised here:
#   * `owner/repo#123`, GitHub's canonical cross-repo spelling, which is self-binding;
#   * an issue pointer within a short WINDOW of a token naming the private workspace
#     repo, in either order -- a window and not a line, because markdown wraps and the
#     real instance this closes had the pointer and the repo name on adjacent lines.
# A third binding -- "it is inside a document vendored FROM that repo, so every issue
# number in it is foreign by construction" -- needs no proximity condition at all and is
# enforced separately over the derived vendored set, by
# `test_vendored_payload_carries_no_issue_pointer`. That is the rule that would have
# caught this step's two real instances at their SOURCE, where they appeared bare.
#
# TIER 2 -- tripwire, not a certifier. WIDENED in iteration 3 (a pure widening: every
# string the iteration-2 form matched still matches) to admit the repository's name used
# as a common noun between "private" and "repository" -- `private <name> repository`,
# which is the phrasing that actually shipped historically and which the iteration-2
# form, hard-coded to the single literal `workspace`, could not see. Up to two
# interposed word tokens are allowed. This is tripwire MAINTENANCE against an observed
# phrasing and it closes nothing at the class level: a third phrasing defeats it again,
# which is the whole point of the tier label.
_PRIVATE_REPO_TOKEN = (
    r"(?:aberson/coding-root"
    r"|private[\s*_`]{1,4}(?:[\w.-]{1,24}[\s*_`]{1,4}){0,2}repositor(?:y|ies))")
_ISSUE_POINTER = (
    r"(?:\b(?:issue|issues|pr|prs|pull\s+request|post|gh)[\s\-]*#\s*\d+"
    r"|(?<![\w#])#\d+)")
# Characters, not lines: two adjacent wrapped markdown lines are ~160.
#
# This bound is ACCEPTED AS PERMEABLE, not defended. Any finite window is defeated at
# window+1 -- roughly 230 characters of filler clears this one, and an ordinary
# two-sentence paragraph is that long -- so raising the number would only move the
# defeat point outward while widening the false-positive surface across three open
# roots, and would buy a coverage claim the construction cannot support either way.
# That permeability is precisely why this pattern is labelled a TIER 2 tripwire, and
# why the surface where a miss is expensive -- the vendored payload -- is graded
# instead by a TIER 1 categorical ban with no proximity condition at all.
_CROSS_REPO_WINDOW = 220
_CROSS_REPO_POINTER_RE = re.compile(
    r"(?is)(?:"
    + _PRIVATE_REPO_TOKEN + r".{0," + str(_CROSS_REPO_WINDOW) + r"}?" + _ISSUE_POINTER
    + r"|"
    + _ISSUE_POINTER + r".{0," + str(_CROSS_REPO_WINDOW) + r"}?" + _PRIVATE_REPO_TOKEN
    + r")")
_FOREIGN_REPO_ISSUE_RE = re.compile(r"\b[\w.-]+/[\w.-]+#\d+")
# TIER 2 -- tripwire, not a certifier. M: a number attributed to a BILL, plus the two
# bare phrasings that attribute one with no number present. A percentage ALONE is not the
# shape here -- `session-wrap`'s context utilisation table is legitimately full of them,
# and so is every SVG in `_shared/`. That unavoidable looseness on an open root is
# exactly the hole an M-class magnitude escaped through twice; on the vendored payload,
# where a percentage has no legitimate use, TIER 1 bans the category outright instead.
_COST_TELEMETRY_RE = re.compile(
    r"(?i)(?:"
    r"\b~?\d{1,3}\s*%[^\n]{0,48}?\b(?:bill|billed|billing|spend|spent|invoice|cost)\b"
    r"|\b(?:billed|billable)\s+tokens?\b"
    r"|\b(?:share|percent|percentage|fraction|slice)\s+of\s+"
    r"(?:the\s+|one\s+|an?\s+)?(?:operator'?s?\s+)?(?:bill|spend|invoice)\b"
    r")")

# TIER 2 registry. Every row is a tripwire for a shape that has been OBSERVED escaping
# into this tree, listed in the order it was added. The list is not, and cannot be made,
# a certification that class X or class M is absent from an open root -- see the tier
# block above, and `_VENDORED_PAYLOAD_BANS` for the one surface that is graded
# categorically.
_DISCLOSURE_PATTERNS = [
    ("cross-repo issue pointer (owner/repo#N)", _FOREIGN_REPO_ISSUE_RE),
    ("issue pointer bound to the private workspace repo", _CROSS_REPO_POINTER_RE),
    ("account cost/usage telemetry", _COST_TELEMETRY_RE),
]

# Every tree the leak sweep walks. `skills/` is the migrated canonical source; `_shared/`
# is the shared payload both profiles ship, and it was unscanned until Step 66 -- a
# second publishing surface with no guard on it. `documentation/` joined them in Step 66
# iteration 2: it is published exactly as widely as the other two (this is a public
# repository), it is where the scrub RECORD and the plan that specifies the scrub live,
# and it had never been graded by this sweep at all. Enumerated here, once, so the
# assertions below and the enumeration guard all read the same list.
_LEAK_SWEEP_ROOTS = ("skills", "_shared", "documentation")


_GIT = shutil.which("git")
# Build artifacts, never published, and actively HOSTILE to this sweep: CPython embeds
# the absolute source path of the module it compiled into every `.pyc`, so a single
# `_shared/__pycache__/` -- which this repository's own repo-root pytest run creates,
# because `_shared/` is one of its test roots -- would report the developer's home
# directory as an operator-private leak in the public tree. That is a false RED with no
# legal remedy: the file is gitignored and cannot reach a release artifact.
_LEAK_SWEEP_SKIP_DIRS = ("__pycache__",)


def _tracked_leak_sweep_files():
    """git-tracked files under `_LEAK_SWEEP_ROOTS`, or None when git cannot answer.

    Returns None -- meaning "fall back to the filesystem walk" -- for anything that is
    not a positive, non-empty answer about THIS tree's index: no git, a failed
    subprocess, or a `rev-parse --show-toplevel` that is not `REPO_ROOT` (which is the
    case inside `tools/release.ps1`'s staging directory, where git still answers for the
    OUTER repository).
    """
    if _GIT is None:
        return None
    try:
        top = subprocess.run([_GIT, "-C", str(REPO_ROOT), "rev-parse", "--show-toplevel"],
                             capture_output=True, timeout=60, check=True).stdout
        if Path(top.decode("utf-8").strip()).resolve() != REPO_ROOT.resolve():
            return None
        out = subprocess.run([_GIT, "-C", str(REPO_ROOT), "ls-files", "-z", "--",
                              *_LEAK_SWEEP_ROOTS],
                             capture_output=True, timeout=60, check=True).stdout
    except (OSError, ValueError, UnicodeDecodeError, subprocess.SubprocessError):
        return None
    files = [REPO_ROOT / rel for rel in
             (chunk.decode("utf-8") for chunk in out.split(b"\0") if chunk)]
    files = [p for p in files if p.is_file()]
    return sorted(files, key=lambda p: p.as_posix()) or None


def _leak_sweep_files():
    """Every file the leak sweep grades, from every root in `_LEAK_SWEEP_ROOTS`.

    EVERY file, not `*.md`: `_shared/` ships `.py`, `.js` and `.svg` into both profiles,
    and a private path in a docstring or an SVG title is published exactly as widely as
    one in prose. The `.md`-only filter the sweep started with was a markdown-shaped
    assumption, not a disclosure-shaped one.

    Enumerated from `git ls-files` when git can answer for this tree, which is the
    repository's convention for anything that must reflect TRACKED state and is exactly
    the right scope here: `tools/release.ps1` stages from `git ls-files`, so the tracked
    set IS the publishable set, and it reads the INDEX, so a staged-but-uncommitted file
    is graded before it can be committed. Untracked scratch and gitignored build output
    (`__pycache__`) are excluded because they cannot reach a consumer -- see
    `_LEAK_SWEEP_SKIP_DIRS` for why including them is worse than a narrowing.

    The fallback is the WIDER filesystem walk, minus those same build directories: an
    untracked file then shows up as a leak rather than vanishing.
    """
    tracked = _tracked_leak_sweep_files()
    if tracked is not None:
        return tracked
    out = []
    for root in _LEAK_SWEEP_ROOTS:
        for p in sorted((REPO_ROOT / root).rglob("*")):
            if p.is_file() and not any(d in p.parts for d in _LEAK_SWEEP_SKIP_DIRS):
                out.append(p)
    return out


def _find_leaks(text):
    return [name for name, rx in _LEAK_PATTERNS + _DISCLOSURE_PATTERNS if rx.search(text)]


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
    # STEP 66 ANCHOR -- the pattern the other five cannot see. A raw harness session
    # UUID carries no drive letter, no home path and no username, so it survived every
    # original pattern. Both halves are asserted: a session-shaped id reds...
    # (the planted value is synthetic on purpose -- pasting a REAL session id into a
    # committed anchor would be the very disclosure this pattern exists to stop)
    assert _find_leaks("run id deadbeef-0000-4000-8000-00000000cafe from the transcript") \
        == ["raw harness session UUID"]
    assert _find_leaks("~/" + proj + "some-slug/0f1e2d3c-4b5a-6978-8765-43210fedcba9.jsonl")
    # ...and the ONE literal documentation UUID does not, so the exemption is proven to
    # be by value and not by a weakened shape.
    assert not _find_leaks(f'"run_id":"{_EXAMPLE_UUIDS[0]}"')
    assert len(_EXAMPLE_UUIDS) == 1, (
        "the UUID exemption list grew. Each entry is a hole in a disclosure gate; add "
        "one only with the reason recorded beside it.")


def test_disclosure_detector_reds_on_the_two_classes_the_identifier_patterns_miss():
    """ANCHOR for the X and M classes. Every planted value is SYNTHETIC.

    A real private issue number or a real share-of-spend figure pasted into a committed
    anchor would be the disclosure the pattern exists to stop -- the same discipline the
    session-UUID anchor above already follows.

    Both directions are asserted for each class, because the whole point of these two
    patterns is that they must fire on a shape while staying silent on the very common
    legitimate neighbour of that shape. For X, that neighbour is this repository's own
    issue numbers, of which `documentation/` alone carries well over a hundred.
    """
    # X -- the canonical cross-repo spelling binds itself: no window needed.
    assert _find_leaks("see aberson/some-other-repo#4242 for the rationale") == \
        ["cross-repo issue pointer (owner/repo#N)"]
    # X -- an issue pointer bound to the private repo by proximity, in BOTH orders,
    # and across a line break (the real instance wrapped).
    bound = "issue pointer bound to the private workspace repo"
    assert bound in _find_leaks(
        "pointers into `aberson/coding-root`, which is private -- issue #4242 and more")
    assert bound in _find_leaks("post-#4242 lives in the operator's private\nrepository")
    assert bound in _find_leaks("#4242 was filed against aberson/coding-root last week")
    # ...including the REAL HISTORICAL PHRASING, which is the calibration this anchor
    # lacked until iteration 3: the repo's name used as a common noun between "private"
    # and "repository". The two spellings above are EASIER garbage than the one that
    # actually shipped, so passing on them alone overstated what the tripwire
    # demonstrates -- a red-on-garbage anchor is only as strong as its garbage.
    assert bound in _find_leaks("post-#4242 lives in the private coding-root repository")
    assert bound in _find_leaks(
        "filed as issue #4242 against the operator's private second-brain repository")
    # ...and the widening is bounded: three or more interposed words is not the shape.
    assert bound not in _find_leaks(
        "#4242 is private to the internal build tooling repository")
    # ...and a bound pointer that is far away is NOT claimed: the window is a real
    # constraint, not decoration.
    assert bound not in _find_leaks(
        "aberson/coding-root" + ("x" * 400) + "issue #4242")
    # X -- this repository's OWN issue numbers, unbound, are not a disclosure.
    assert not _find_leaks("closed by #97; see issue #98 for the follow-up")
    assert not _find_leaks("Step 12 of the same phase, per the plan")
    # M -- a number attributed to a bill, and the bare form with no number at all.
    assert _find_leaks("11% of billed spend lands above the ceiling") == \
        ["account cost/usage telemetry"]
    assert _find_leaks("a stated share of the invoice") == ["account cost/usage telemetry"]
    # M -- a percentage that is not about money stays green. Both of these are real
    # shapes in this tree: a context-utilisation threshold and an SVG dimension.
    assert not _find_leaks("| `CLEARNEXT_FORCE_UTIL` | 75% | >150k tokens | take it |")
    assert not _find_leaks('<rect width="100%" height="60%" fill="none" />')
    assert not _find_leaks("token cost is incurred at high context")


def _vendored_payload_docs():
    """`_shared/*.md` carrying the Step 66 vendor banner. DERIVED, never hand-listed.

    A hand-maintained roster of what a gate covers is a false green the first time
    someone vendors an eighth document and does not add a row.
    """
    banner = "**Vendored into skill-mesh.**"
    return sorted(p for p in (REPO_ROOT / "_shared").glob("*.md")
                  if banner in p.read_text(encoding="utf-8"))


# Floor on the DERIVED set above: seven documents were vendored by Step 66. It moves
# only when a document is deliberately retired from the payload, in the same commit.
MIN_VENDORED_PAYLOAD_DOCS = 7

# Inside a vendored document there is no such thing as a local issue number: the whole
# file is a copy of a document that lives in the private workspace repo. So no proximity
# binding is required here, and none is applied.
_VENDORED_ISSUE_POINTER_RE = re.compile(
    r"(?i)\b(?:issue|issues|pr|prs|pull\s+request|post|gh)[\s\-]*#\s*\d+")

# --------------------------------------------------------------------------- #
# TIER 1 -- the categorical bans over the bounded vendored payload.
# --------------------------------------------------------------------------- #
# Each row forbids a whole CATEGORY inside a vendored document, with no proximity
# condition and no attempt to recognise a private phrasing. That is the property the
# tripwires do not have: what a row claims IS the category it names, so the claim is
# decidable and cannot over-reach. The issue-pointer row reuses the
# `_VENDORED_ISSUE_POINTER_RE` OBJECT rather than a second copy of the shape, so the
# dedicated test above and the table below can never drift apart.
#
# Why these three categories:
#   * issue-shaped pointer -- inside a document copied wholesale out of the private
#     workspace repo there is no such thing as a local issue number, so every one is
#     foreign by construction and no binding is required. Two real instances of the
#     step's own scrub appeared exactly this way, bare.
#   * share or percentage -- M's most common spelling. Zero legitimate occurrences in
#     the payload today, so the ban costs nothing now; a future one is reworded into a
#     qualitative claim, which is precisely the substitution the M scrub already made.
#   * scaled or open-ended magnitude -- a measured quantity lifted out of a private
#     measurement set, and the row that mechanically catches the M-class member that
#     survived both tripwire rounds. The shape is `999k`, `18M`, `999+`: three INVENTED
#     values, and invented on purpose. This comment ships in a public repository like
#     every other byte here, so illustrating the shape with the real magnitudes the step
#     removed would republish them in the file that bans them -- which is precisely the
#     mistake this whole tier exists to stop. Plain integers and years are
#     deliberately NOT banned: `500`, `2026` and `8601` occur legitimately in the payload
#     and carry no scale, so banning them would be the false-positive flood that gets a
#     gate deleted.
#
# One category was CONSIDERED AND REJECTED: a bare `owner/repo` token. Measured over the
# current payload it produces 36 matches and all 36 are false (`P/D`, `open/close`,
# `plan-review/plan-wrap`, `issue/cron`, ...), because slash-joined word pairs are
# ordinary prose in these documents. A ban whose first run is 100% false positives is a
# ban somebody deletes, so it is not made. The canonical `owner/repo#N` cross-repo
# spelling is already a tier-2 pattern; an UNADORNED foreign repo slug is left to the
# tier-3 sign-off, and is named here so that the omission is a recorded decision rather
# than an unexamined hole.
#
# The magnitude row spells its number as `\d[\d,]*(?:\.\d+)?` rather than `\d[\d,.]*` on
# purpose: the looser form absorbs a trailing sentence period, so an ordinary numbered
# list item whose text begins with a lone capital (`2. M -- the class`, a shape these
# very documents use) would red as `2. M`. That is not a magnitude, and a ban is only
# worth having if the category it names is the category it matches.
_VENDORED_SHARE_RE = re.compile(r"(?i)%|\bpercent(?:age|ile)?s?\b")
_VENDORED_MAGNITUDE_RE = re.compile(r"(?<![\w.])~?\d[\d,]*(?:\.\d+)?\s*(?:[kKmM]\b|\+)")

_VENDORED_PAYLOAD_BANS = [
    ("issue-shaped pointer", _VENDORED_ISSUE_POINTER_RE),
    ("share or percentage", _VENDORED_SHARE_RE),
    ("scaled or open-ended magnitude", _VENDORED_MAGNITUDE_RE),
]

# --------------------------------------------------------------------------- #
# TIER 1, SECOND SURFACE -- the scrub RECORD is payload too.
# --------------------------------------------------------------------------- #
# The bans above were scoped to the seven vendored documents on the reasoning that a
# categorical ban is affordable only where a false positive is answered by rewording a
# handful of files. That reasoning was right and its SCOPE was too small. A document
# whose entire subject is the private values REMOVED from those seven is at least as
# likely to carry one as they are, and Step 66 demonstrated it three times: the record
# re-quoted the issue pointers it had just removed; then it kept a magnitude the same
# row certified gone; then the fix for that reintroduced a third value two lines under
# the record's own promise that such values are restated nowhere in it. Three rounds of
# patching the named line each produced a fresh one, because the surface was never
# graded -- only the files it describes were.
#
# So this is a SCOPE change to the existing gate and not a new mechanism: the same
# `_VENDORED_PAYLOAD_BANS` rows, the same compiled objects, one more bounded surface.
# No pattern is added, nothing is fitted to an observed instance, and nothing is pointed
# at an open root.
#
# WHY A MARKER RATHER THAN THIS ONE FILE'S NAME: the hazard belongs to the GENRE, not to
# this instance, so the ban covers any document that declares itself a scrub record --
# and the set is DERIVED from that self-declaration exactly as the vendored set is
# derived from the vendor banner, because a hand-listed roster of what a gate covers is
# a false green the first time a second record is written. The derivation has the same
# honest limit as the vendor banner: an author who omits the marker is not graded, and
# tier 3 owns that gap.
#
# The PLAN deliberately does NOT carry the marker. It narrates this scrub in one section
# but it is not a record OF the scrub, and it legitimately carries this repository's own
# issue numbers and plain `N+` counts throughout -- measured, the three rows red on 12
# tokens there and ALL 12 ARE FALSE (6 issue numbers this repository or Phase 8 owns, 5
# plain counts, 1 category noun), which is exactly the false-positive flood that gets a
# gate switched off. Its scrub narrative stays under the tier-3 sign-off. That is a
# recorded decision rather than an unexamined hole, like the `owner/repo` row above.
#
# TWO legitimate record constructs tripped these bans when the scope widened, and NEITHER
# was answered by loosening a row (the record's section 7.2 carries the full decision):
#   * this repository's own issue pointer, in the record's opening line. The record now
#     reaches that number through the plan's Step 66 block, which owns it. On THIS
#     document, "is this issue number ours or lifted from the private source?" is the
#     exact judgment that failed in round 1, so the document does not make it inline.
#   * the noun "percentage", used to NAME a category rather than to state a value. The
#     record says "share figure" and cites `_VENDORED_PAYLOAD_BANS` as the owner of the
#     category list -- which also retires three prose copies of that list, so the reword
#     pays for itself in drift the repository would otherwise have to police by eye.
#
# The marker must OPEN A BANNER LINE, not merely appear somewhere in the bytes. A bare
# substring test selected the plan on its first run, because the plan describes this very
# mechanism and quotes the marker inline -- a document that MENTIONS the marker has not
# declared itself, and a self-declaration that any citation of it can trigger is not one.
# The vendor banner is matched loosely because it is prose no other document quotes; this
# marker is quoted by design, so it is anchored instead.
_SCRUB_RECORD_MARKER = "**Scrub record.**"
_SCRUB_RECORD_MARKER_RE = re.compile(r"(?m)^>[ \t]*\*\*Scrub record\.\*\*")


def _scrub_record_docs():
    """`documentation/*.md` declaring themselves scrub records. DERIVED, never hand-listed."""
    return sorted(p for p in (REPO_ROOT / "documentation").glob("*.md")
                  if _SCRUB_RECORD_MARKER_RE.search(p.read_text(encoding="utf-8")))


# Floor on the derived set above, the same discipline as MIN_VENDORED_PAYLOAD_DOCS: it
# moves only when a record is deliberately retired, in the same commit.
MIN_SCRUB_RECORD_DOCS = 1

# The two floors above can only see the graded surface SHRINK. This is their counterpart
# for the other direction, and the same discipline: the document tier 1 deliberately does
# NOT grade, carrying the measured reason it is out. A floor pins how few documents may be
# graded; this pins WHICH document must stay ungraded -- so widening the bans onto the plan
# becomes a deliberate edit here rather than a silent side effect of a marker landing in
# one more file, and the reason survives without a future reader re-deriving it. The
# reason itself is recorded once, in the tier-1 second-surface block above; this entry
# states the measurement so the failure message can hand it over at the point of failure.
TIER1_UNGRADED_DOCS = {
    "documentation/host-parity-repair-plan.md":
        "it narrates this scrub in one section but is not a record OF it, and it "
        "legitimately carries this repository's own issue numbers and plain counts "
        "throughout: measured, the three rows red on 12 tokens there and ALL 12 ARE "
        "FALSE (6 issue numbers this repository or Phase 8 owns, 5 plain counts, 1 "
        "category noun). Grading it is the false-positive flood that gets a gate "
        "switched off; its scrub narrative stays under the tier-3 sign-off.",
}


def _tier1_graded_docs():
    """Every document the tier-1 categorical bans grade: the payload, plus every record."""
    return _vendored_payload_docs() + _scrub_record_docs()


def test_vendored_payload_carries_no_issue_pointer():
    """No issue-shaped pointer may survive in a document vendored from the private repo.

    This is the rule that grades the class AS IT APPEARED at the source: bare, with
    nothing on the line to bind it to a repository, so the proximity rule in
    `_DISCLOSURE_PATTERNS` could not have seen either of the two real instances.
    """
    # ANCHOR first -- both real shapes, with synthetic numbers.
    assert _VENDORED_ISSUE_POINTER_RE.search("## Review routing (post-#4242)")
    assert _VENDORED_ISSUE_POINTER_RE.search("hook wiring lands with issue #4242")
    # ...and silent on a numbered CLASS reference, which is not an issue pointer.
    # `skill-pipeline.md` legitimately names a halt-contract class this way.
    assert not _VENDORED_ISSUE_POINTER_RE.search("where /build-phase halts (class #4)")

    docs = _vendored_payload_docs()
    assert len(docs) >= MIN_VENDORED_PAYLOAD_DOCS, (
        f"only {len(docs)} vendored document(s) carry the banner, floor is "
        f"{MIN_VENDORED_PAYLOAD_DOCS}. Either a document was retired (lower the floor "
        "deliberately, in the same commit) or the banner drifted and this gate just "
        "stopped grading the payload it exists for.")
    offenders = []
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for m in _VENDORED_ISSUE_POINTER_RE.finditer(text):
            line = text[:m.start()].count("\n") + 1
            offenders.append(f"{doc.relative_to(REPO_ROOT).as_posix()}:{line}: "
                             f"{m.group(0)!r}")
    assert not offenders, (
        "a vendored document carries a pointer into the private workspace repo's "
        "issue namespace:\n" + "\n".join(offenders))


def test_vendored_payload_carries_no_banned_category():
    """TIER 1: whole CATEGORIES are forbidden across both bounded tier-1 surfaces.

    Those surfaces are the seven vendored documents and every scrub RECORD describing
    them -- see `_tier1_graded_docs`. The record is graded by the same rows, from the
    same table, because a document whose subject is the removed values is as likely to
    carry one as the files it describes.

    The generalisation of `test_vendored_payload_carries_no_issue_pointer`, which is
    retained above unchanged with its own anchors: that test grades one row of this
    table against the vendored set, this one grades every row against both surfaces,
    and both read the same `_VENDORED_ISSUE_POINTER_RE` object so they cannot drift.

    This is the tier that makes an HONEST mechanical claim. It does not try to
    recognise a private phrasing -- an unbounded problem that defeated two rounds of
    tripwire-fitting -- it forbids the category outright over a surface small enough
    that a false positive is answered by rewording a handful of files. Class-level
    absence is still owned by the per-file human sign-off (tier 3), not by this test.

    Every planted anchor value is SYNTHETIC, for the same reason the sweep anchors are.
    """
    # WIRING. The shared-object claim in the docstring is ASSERTED, not asserted-in-prose:
    # `is`, not `==`, so re-declaring a shape as a second copy reds here instead of
    # drifting silently away from the constant the rest of the file reads.
    #
    # EVERY row is checked, not just the issue-pointer one. Until this loop existed the
    # share and magnitude rows -- the two that closed the escape this step was blocked on
    # -- could be deleted from the table with the whole suite still green, because the
    # anchors below exercise the compiled objects DIRECTLY and never assert that the table
    # still carries them. Anchors prove a pattern works; only identity proves it is wired.
    for label, obj in (("issue-shaped pointer", _VENDORED_ISSUE_POINTER_RE),
                       ("share or percentage", _VENDORED_SHARE_RE),
                       ("scaled or open-ended magnitude", _VENDORED_MAGNITUDE_RE)):
        assert any(rx is obj for _, rx in _VENDORED_PAYLOAD_BANS), (
            f"the {label!r} ban is no longer the same compiled object this file "
            "declares -- the row was dropped from _VENDORED_PAYLOAD_BANS, or replaced "
            "by a second copy of the shape. Either way the gate below stopped grading "
            "that category and no anchor in this test can see it.")
    assert len(_VENDORED_PAYLOAD_BANS) == 3, (
        "_VENDORED_PAYLOAD_BANS gained or lost a row. A ban is only worth having with a "
        "red-on-garbage anchor and a silent-on-the-neighbour anchor beside it: add both "
        "above and move this count in the same commit.")

    # ANCHORS -- each row reds on its own category...
    assert _VENDORED_SHARE_RE.search("about 42% of the window")
    assert _VENDORED_SHARE_RE.search("a large percentage of a long window's cost")
    assert _VENDORED_MAGNITUDE_RE.search("a 999k-char return the orchestrator skims")
    assert _VENDORED_MAGNITUDE_RE.search("carried resident for 999+ turns")
    assert _VENDORED_MAGNITUDE_RE.search("roughly 42M tokens in one window")
    assert _VENDORED_MAGNITUDE_RE.search("about 1,024k characters")
    assert _VENDORED_MAGNITUDE_RE.search("some 3.5M tokens")
    # ...and stays silent on the neighbouring shapes that ARE legitimately in the
    # payload today, so the bans are strict without being indiscriminate: a plain
    # count, a date, a standard number, and the qualitative form the M scrub adopted.
    assert not _VENDORED_MAGNITUDE_RE.search("truncate the pointer at 500 characters")
    assert not _VENDORED_MAGNITUDE_RE.search("dated 2026-06-22 in the ledger")
    assert not _VENDORED_MAGNITUDE_RE.search("an ISO 8601 timestamp, UTC")
    # ...and a numbered list item whose text opens with a lone capital is a list
    # marker, not a magnitude -- the shape the number spelling above exists to exclude.
    assert not _VENDORED_MAGNITUDE_RE.search("2. M -- account-level usage telemetry")
    assert not _VENDORED_SHARE_RE.search(
        "the large majority of a long window's token cost is incurred at high context")

    # ...and the SECOND SURFACE's self-declaration is anchored in both directions too: a
    # banner line declares a document a scrub record, an inline mention of the marker does
    # not. This is not hypothetical either -- as a bare substring test it selected the plan
    # on its first run, because the plan describes this mechanism and quotes the marker.
    assert _SCRUB_RECORD_MARKER_RE.search(
        "# Title\n\n> **Scrub record.** the values below are named by class only\n")
    assert not _SCRUB_RECORD_MARKER_RE.search(
        "derived from a self-declared `**Scrub record.**` marker, never hand-listed")

    # BOTH surfaces are floored SEPARATELY. A single floor over the union would let one
    # surface empty out while the other's count carried the assertion -- which is the
    # shape of false green this repository has already been burned by.
    payload = _vendored_payload_docs()
    assert len(payload) >= MIN_VENDORED_PAYLOAD_DOCS, (
        f"only {len(payload)} vendored document(s) carry the banner, floor is "
        f"{MIN_VENDORED_PAYLOAD_DOCS}. Either a document was retired (lower the floor "
        "deliberately, in the same commit) or the banner drifted and this gate just "
        "stopped grading the payload it exists for.")
    records = _scrub_record_docs()
    assert len(records) >= MIN_SCRUB_RECORD_DOCS, (
        f"only {len(records)} document(s) carry {_SCRUB_RECORD_MARKER!r}, floor is "
        f"{MIN_SCRUB_RECORD_DOCS}. The scrub record is tier-1 payload: a marker typo "
        "silently stops grading the one document whose whole subject is the values "
        "this tier forbids.")
    docs = _tier1_graded_docs()
    graded = {p.relative_to(REPO_ROOT).as_posix() for p in docs}
    assert "documentation/step-66-vendored-reference-decisions.md" in graded, (
        "the Step 66 scrub record is not being graded by the tier-1 bans; it carried a "
        "banned value in three consecutive review rounds and is the reason this surface "
        "exists")
    assert all(f"_shared/{leaf}" in graded for leaf in
               ("subagent-economy.md", "task-state-schema.md", "skill-pipeline.md")), graded

    # ...and the EXCLUSION is pinned in the same breath, because "which documents does
    # this gate grade?" is only half-answered by naming the ones that are in. The plan is
    # out by a MEASURED decision, and until this assertion existed nothing held that
    # decision: the surface could widen onto the plan -- or the record could drop out of
    # it -- with the whole suite green, which is the exact shape of defect this step spent
    # three rounds on. A scope decision that lives only in a comment is not pinned.
    for rel, why in sorted(TIER1_UNGRADED_DOCS.items()):
        # Existence first. "not in graded" is satisfied vacuously by a file that was
        # renamed or deleted, so without this the entry would quietly stop asserting
        # anything -- a hand-listed roster decaying into a false green.
        assert (REPO_ROOT / rel).is_file(), (
            f"{rel} is listed in TIER1_UNGRADED_DOCS as deliberately ungraded, but no "
            "longer exists at that path, so the exclusion below now asserts nothing. "
            "Repoint the entry at the file's new path, or drop it, in the commit that "
            "moved it.")
        assert rel not in graded, (
            f"{rel} is now GRADED by the tier-1 categorical bans. It is deliberately "
            f"excluded: {why}\n\nIf a scrub-record marker landed in it by mistake, "
            "remove the marker -- a document that merely MENTIONS the marker must quote "
            "it inline rather than open a banner line with it. If widening tier 1 onto "
            "this document is genuinely intended, delete its entry here in the same "
            "commit, and expect to reword every one of those tokens: do NOT answer this "
            "failure by narrowing a ban.")
    offenders = []
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for label, rx in _VENDORED_PAYLOAD_BANS:
            for m in rx.finditer(text):
                line = text[:m.start()].count("\n") + 1
                offenders.append(f"{doc.relative_to(REPO_ROOT).as_posix()}:{line}: "
                                 f"{label}: {m.group(0)!r}")
    assert not offenders, (
        "a tier-1 document carries a BANNED CATEGORY:\n" + "\n".join(offenders) +
        "\n\nThese bans are CATEGORICAL, not heuristic. The fix is to REWORD the "
        "offending document into a qualitative claim and record the adaptation in the "
        "Step 66 decision record -- in the per-file sign-off for a vendored file, in "
        "section 7.2 for the record itself. A record documenting a scrub must describe "
        "the removed value by CLASS AND LOCATION and never restate it, including inside "
        "quotation marks and including in a sentence explaining that it was removed: "
        "that last one is not hypothetical, it is how this gate came to exist. Do NOT "
        "narrow a ban to admit the offending token: that converts a real finding into a "
        "false green, which is the exact failure this tier exists to prevent.")


def test_leak_sweep_filesystem_fallback_skips_build_output(tmp_path, monkeypatch):
    """`_LEAK_SWEEP_SKIP_DIRS` is only REACHABLE in the fallback branch -- test it there.

    Wherever git answers -- the normal case, and git is a declared dependency of this
    repository -- `_leak_sweep_files()` returns the `git ls-files` set, in which
    `__pycache__` is absent because it is UNTRACKED, not because the filter worked. So
    `test_leak_sweep_covers_the_shared_payload`'s no-`__pycache__` assertion is true
    today for a reason unrelated to the code it guards: a typo in the skip list, or
    `d == p.name` written in place of `d in p.parts`, would ship green behind it. This
    drives the fallback directly, which is the only branch that filter has.
    """
    module = sys.modules[__name__]
    (tmp_path / "skills" / "demo" / "__pycache__").mkdir(parents=True)
    (tmp_path / "skills" / "demo" / "core.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / "skills" / "demo" / "__pycache__" / "core.cpython-313.pyc").write_bytes(
        b"\x00\x0f\r\n")
    (tmp_path / "_shared" / "nested" / "__pycache__").mkdir(parents=True)
    (tmp_path / "_shared" / "payload.md").write_text("# payload\n", encoding="utf-8")
    (tmp_path / "_shared" / "nested" / "__pycache__" / "x.pyc").write_bytes(b"\x00")
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "_LEAK_SWEEP_ROOTS", ("skills", "_shared"))
    monkeypatch.setattr(module, "_tracked_leak_sweep_files", lambda: None)
    swept = {p.relative_to(tmp_path).as_posix() for p in _leak_sweep_files()}
    assert swept == {"skills/demo/core.md", "_shared/payload.md"}, swept


def test_leak_sweep_covers_the_shared_payload():
    """ENUMERATION GUARD: the sweep must actually reach `_shared/`, and non-markdown.

    The sweep was `skills/**/*.md` until Step 66, so the entire shared payload -- which
    ships into BOTH host profiles -- was unscanned. A later edit narrowing the walk back
    would leave every assertion below green over a smaller tree, which is the shape this
    repository has already been burned by. So the roots and the breadth are asserted,
    not assumed.
    """
    swept = {p.relative_to(REPO_ROOT).as_posix() for p in _leak_sweep_files()}
    assert any(f.startswith("_shared/") for f in swept), \
        "the leak sweep no longer reaches _shared/"
    assert any(f.startswith("skills/") for f in swept), \
        "the leak sweep no longer reaches skills/"
    # ...and `documentation/`, added in iteration 2. Dropping this root is how the two
    # disclosure classes above become unenforceable again without a single pattern
    # changing: every real instance either of them has ever caught lived here.
    assert any(f.startswith("documentation/") for f in swept), \
        "the leak sweep no longer reaches documentation/"
    assert "documentation/host-parity-repair-plan.md" in swept, \
        "the plan that SPECIFIES the scrub is outside the gate that grades it"
    assert "documentation/step-66-vendored-reference-decisions.md" in swept, \
        "the scrub RECORD is outside the gate that grades it"
    assert "_shared/judge-core.md" in swept
    assert any(f.startswith("_shared/") and f.endswith(".py") for f in swept), \
        "the leak sweep is markdown-only again; `_shared/` ships .py/.js/.svg too"
    # ...and the enumeration must not drag in gitignored build output. A `.pyc` embeds
    # the absolute path of the source it was compiled from, so one `__pycache__` entry
    # turns this gate into a false RED reporting the developer's own home directory.
    assert not [f for f in swept if "__pycache__" in f], \
        "the leak sweep is walking gitignored build output; see _LEAK_SWEEP_SKIP_DIRS"
    # Every vendored Step 66 document is in the swept set -- the whole reason the sweep
    # was widened. Named individually so a partial enumeration cannot pass on one file.
    for leaf in ("step-authoring.md", "task-state-schema.md", "skill-pipeline.md",
                 "intake-engine.md", "skill-role-taxonomy.md", "worktree-hygiene.md",
                 "subagent-economy.md"):
        assert f"_shared/{leaf}" in swept, f"_shared/{leaf} is not being swept"


def test_no_private_leak_in_migrated_tree():
    offenders = []
    for f in _leak_sweep_files():
        hits = _find_leaks(f.read_text(encoding="utf-8", errors="replace"))
        if hits:
            offenders.append(f"{f.relative_to(REPO_ROOT)}: {hits}")
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
# Migration transform (STEP 67) -- driven directly, no legacy source required
# --------------------------------------------------------------------------- #
# These replace the retired clause-preservation gate (see the module docstring). They
# drive `gen_skill_tree.transform` -- the SAME production function the generator's
# `run()` calls on every migrated file -- over synthetic inputs, so the two rewrite
# behaviors Step 67 added are exercised on every run instead of only when a source
# root that no longer exists happens to be present.
#
# Nothing here reads the committed tree: the generator cannot be re-run against the
# overwritten legacy root, so these additions change no committed byte and must not
# pretend to.


def _transform_args():
    """(portable, native, support) exactly as `run()` assembles them."""
    manifest = gen_skill_tree.load_manifest()
    portable, native = gen_skill_tree.skill_sets(manifest)
    return portable, native, gen_skill_tree.support_dests(manifest)


def test_vendored_shared_refs_map_only_documents_the_payload_ships():
    """The `references/*` + `rules/*` map is pinned to the DERIVED Step 66 payload.

    Derived from the vendor banner, never hand-listed against a second roster: an
    eighth vendored document that nobody adds to the map -- or a map entry naming a
    file the payload does not carry -- both red here. The second assertion is the one
    that matters for consumers: every target must be a real file, because a mapping
    to a missing `_shared/` leaf would convert an honest external citation into a
    dangling repo link.
    """
    payload = {f"_shared/{p.name}" for p in _vendored_payload_docs()}
    assert set(gen_skill_tree.VENDORED_SHARED_REFS.values()) == payload, (
        "VENDORED_SHARED_REFS and the Step 66 vendored payload disagree: "
        f"map={sorted(gen_skill_tree.VENDORED_SHARED_REFS.values())} payload={sorted(payload)}")
    for legacy, target in sorted(gen_skill_tree.VENDORED_SHARED_REFS.items()):
        assert (REPO_ROOT / target).is_file(), f"{legacy} -> {target} does not exist"


def test_transform_rewrites_a_relative_backtick_citation():
    """STEP 67 gap 1. A relative citation is neither a markdown link nor a
    `.claude/`-absolute path, so before this step NO pass claimed it and it survived
    the migration still naming the legacy `references/` layout."""
    portable, native, support = _transform_args()
    out = gen_skill_tree.transform(
        "Follow `../../references/task-state-schema.md` before writing state.\n",
        ["skills-gpt", "session-wrap"], "skills/session-wrap",
        portable, native, support)
    assert out == "Follow `../../_shared/task-state-schema.md` before writing state.\n"


def test_transform_rewrites_a_bare_relative_citation_in_prose():
    portable, native, support = _transform_args()
    out = gen_skill_tree.transform(
        "Routing lives at ../../references/skill-pipeline.md today.\n",
        ["skills-gpt", "user-gateway"], "skills/user-gateway",
        portable, native, support)
    assert out == "Routing lives at ../../_shared/skill-pipeline.md today.\n"


def test_transform_maps_the_one_vendored_rules_target():
    """Six of the seven came from `references/`; `subagent-economy.md` came from
    `rules/` and has no `references/` copy, so a leaf-name map would have missed it."""
    portable, native, support = _transform_args()
    out = gen_skill_tree.transform(
        "Budget per `../../rules/subagent-economy.md`.\n",
        ["skills", "build-step"], "skills/build-step/providers",
        portable, native, support)
    assert out == "Budget per `../../../_shared/subagent-economy.md`.\n"


def test_transform_leaves_an_unshipped_reference_as_prose():
    """CONSERVATIVE half. `model-tiering.md` and `shakedown-engine.md` are real
    workspace documents this package does NOT ship, so their citations stay external
    and unchanged. Fabricating a `_shared/` path for them would trade a truthful
    external citation for a dangling repo link."""
    portable, native, support = _transform_args()
    for leaf in ("references/model-tiering.md", "references/shakedown-engine.md",
                 "rules/code-quality.md"):
        src = f"See `../../{leaf}` for the policy.\n"
        assert gen_skill_tree.transform(
            src, ["skills-gpt", "tier-escalate"], "skills/tier-escalate",
            portable, native, support) == src, leaf


def test_transform_does_not_rewrite_relative_paths_inside_a_fence():
    """Fenced code is a literal sample; the relative pass runs with fences stashed."""
    portable, native, support = _transform_args()
    src = ("intro\n\n```\ncp ../../references/task-state-schema.md .\n```\n\n"
           "outro `../../references/task-state-schema.md`\n")
    out = gen_skill_tree.transform(src, ["skills-gpt", "session-wrap"],
                                   "skills/session-wrap", portable, native, support)
    assert "cp ../../references/task-state-schema.md ." in out, "fence was rewritten"
    assert out.endswith("outro `../../_shared/task-state-schema.md`\n")


def test_transform_leaves_an_already_rewritten_link_target_alone():
    """ORDERING. The relative pass runs LAST, with the links it must not touch
    stashed: their targets are already NEUTRAL by then, and re-resolving a neutral
    path against the LEGACY directory is how a correct rewrite gets corrupted. The
    assertion is on the composed output, which is what the tree would ship."""
    portable, native, support = _transform_args()
    out = gen_skill_tree.transform(
        "See [core](../../skills-gpt/plan-review/SKILL-core.md).\n",
        ["skills", "plan-review"], "skills/plan-review/providers",
        portable, native, support)
    assert out == "See [core](../core.md).\n"


def test_transform_ignores_non_path_relative_prose():
    """A `../`-anchored token must END on a word character, so a bare `cd ../..` and
    a trailing sentence period are left alone rather than half-consumed."""
    portable, native, support = _transform_args()
    src = "Run cd ../.. first, then re-read ../../references/nope.md.\n"
    out = gen_skill_tree.transform(src, ["skills-gpt", "build-step"],
                                   "skills/build-step", portable, native, support)
    assert out == src


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
