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
import shutil
import subprocess
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
# STEP 66 (iteration 2): the two DISCLOSURE classes the six patterns above cannot see.
# --------------------------------------------------------------------------- #
# Every pattern in `_LEAK_PATTERNS` keys on an IDENTIFIER -- a drive letter, a home
# path, the username, a session UUID. The scrub Step 66 actually performed spent most
# of its budget on two classes that carry none of those:
#
#   X  a pointer into the PRIVATE workspace repository's issue namespace
#   M  account-level cost / usage telemetry
#
# The proof that the gap was inert rather than theoretical is Step 66's own iteration 1:
# it extended this sweep to `_shared/` AND landed fresh instances of both classes in
# `documentation/`, which was not a swept root at all. It is one now.
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
_PRIVATE_REPO_TOKEN = (
    r"(?:aberson/coding-root"
    r"|private[\s*_`]{1,4}(?:workspace[\s*_`]{1,4})?repositor(?:y|ies))")
_ISSUE_POINTER = (
    r"(?:\b(?:issue|issues|pr|prs|pull\s+request|post|gh)[\s\-]*#\s*\d+"
    r"|(?<![\w#])#\d+)")
# Characters, not lines: two adjacent wrapped markdown lines are ~160.
_CROSS_REPO_WINDOW = 220
_CROSS_REPO_POINTER_RE = re.compile(
    r"(?is)(?:"
    + _PRIVATE_REPO_TOKEN + r".{0," + str(_CROSS_REPO_WINDOW) + r"}?" + _ISSUE_POINTER
    + r"|"
    + _ISSUE_POINTER + r".{0," + str(_CROSS_REPO_WINDOW) + r"}?" + _PRIVATE_REPO_TOKEN
    + r")")
_FOREIGN_REPO_ISSUE_RE = re.compile(r"\b[\w.-]+/[\w.-]+#\d+")
# M: a number attributed to a BILL, plus the two bare phrasings that attribute one with
# no number present. A percentage ALONE is not the shape -- `session-wrap`'s context
# utilisation table is legitimately full of them, and so is every SVG in `_shared/`.
_COST_TELEMETRY_RE = re.compile(
    r"(?i)(?:"
    r"\b~?\d{1,3}\s*%[^\n]{0,48}?\b(?:bill|billed|billing|spend|spent|invoice|cost)\b"
    r"|\b(?:billed|billable)\s+tokens?\b"
    r"|\b(?:share|percent|percentage|fraction|slice)\s+of\s+"
    r"(?:the\s+|one\s+|an?\s+)?(?:operator'?s?\s+)?(?:bill|spend|invoice)\b"
    r")")

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
