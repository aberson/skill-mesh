"""Runtime builder for the consumer-home shapes the host-install gate exercises.

These shapes used to be COMMITTED under ``tests/fixtures/legacy-install/**``. Every
fixture ``SKILL.md`` there sat at a real discovery path (``.claude/skills/<name>/``,
``.github/skills/<name>/``) with valid YAML frontmatter, and Claude Code discovers
skills from nested ``.claude/skills/`` directories anywhere in a tree -- so merely
working in this repository surfaced phantom ``build-phase``, ``build-step``,
``context-slim``, ``build-observer``, and ``goblin-sweep`` skills whose body was a
stub (#86). There is no path-based discovery exclude: ``skillOverrides`` hides by
NAME after discovery, which would hide the real skill too. The only fix is to stop
committing files at those paths.

So every shape is synthesized into a caller-supplied temp directory at test time.
Step 46 already did this for the clean and junction shapes; this module extends it
to all of them, and adds the shapes that close the #85 coverage gaps.

The generated-file provenance header is DERIVED from ``tools/skill-mesh-provenance.ps1``
rather than duplicated here, so the fixture marker cannot drift from the parser that
reads it.
"""
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROVENANCE_SCRIPT = REPO_ROOT / "tools" / "skill-mesh-provenance.ps1"
INSPECT_SCRIPT = REPO_ROOT / "tools" / "inspect-host-install.ps1"

# Consumer-home-relative locations, mirrored from inspect-host-install.ps1.
CLAUDE_ROOT = ".claude/skills"
GPT_ROOT = ".github/skills"
LEGACY_SKILLS_GPT_ROOT = ".claude/skills-gpt"
RETIRED_COPILOT_ROOT = ".copilot/skills"
LEDGER_NAME = ".skill-mesh-install.json"


def _inspector_path_constant(varname):
    """Read a watched-path constant straight from the inspector under test.

    Two reasons this is derived rather than duplicated. First, a router fixture that
    hardcoded its own path could drift from the path the tool actually watches, and
    the test would then prove nothing. Second, the legacy router lives under the
    legacy coding-root source layout, and tests/router/test_no_claude_dependency.py
    correctly fails any executable file in tests/ that names that layout -- deriving
    the value keeps this module honest instead of assembling the literal to dodge the
    guard.
    """
    text = INSPECT_SCRIPT.read_text(encoding="utf-8")
    m = re.search(r"^\$" + varname + r"\s*=\s*'([^']+)'", text, re.M)
    assert m, "constant $%s not found in tools/inspect-host-install.ps1" % varname
    return m.group(1)


CANONICAL_ROUTER = _inspector_path_constant("CANONICAL_ROUTER_REL")
LEGACY_ROUTER = _inspector_path_constant("LEGACY_ROUTER_REL")

# A directory name that is deliberately NOT a manifest record (asserted by
# test_foreign_name_is_not_a_manifest_record, so a future manifest addition that
# stole this name would go red instead of silently reclassifying the fixture).
FOREIGN_DIR = "operator-notes"

# Canary for the leak gates. Deliberately all [A-Za-z0-9-]: a charset filter alone
# can never suppress it, which is why the leak assertions check closed-vocabulary
# CHANNELS structurally rather than hunting for this substring.
SECRET = "sk-LEAKCANARY-0123456789abcdef"
VICTIM_PATH = r"C:\Users\victim\secrets" + "\\" + SECRET

# Length of the over-long directory-name plant. Must exceed the inspector's 64-char
# display cap (so truncation is proven) while leaving MAX_PATH headroom once mounted
# under a pytest tmp_path -- see the comment in _hostile().
OVERLONG_NAME_LEN = 100

# 'claude' followed by 300 SOFT HYPHENs (U+00AD). A culture-aware string comparison
# treats this as EQUAL to 'claude'; an ordinal one does not. Written as an escape,
# never as a literal -- the character is invisible in an editor.
LOOKALIKE_PROVIDER_KEY = "claude" + chr(0x00AD) * 300


# --------------------------------------------------------------------------- #
# File bodies
# --------------------------------------------------------------------------- #

def marker_token():
    """The provenance token, read from its single source of truth."""
    m = re.search(r"return\s+'([^']+)'", PROVENANCE_SCRIPT.read_text(encoding="utf-8"))
    assert m, "marker literal not found in tools/skill-mesh-provenance.ps1"
    return m.group(1)


def _generated_header(profile):
    return (
        "<!-- GENERATED FILE - DO NOT EDIT.\n"
        "     Marker: " + marker_token() + "\n"
        "     Produced by tools/build-distributions.ps1 from config/skill-manifest.json.\n"
        "     Profile: " + profile + "\n"
        "     Edit the canonical source and rebuild; edits here are overwritten. -->\n"
    )


def generated_skill_md(name, profile):
    """A SKILL.md carrying a well-formed skill-mesh provenance header (owned)."""
    return (
        "---\n"
        "name: " + name + "\n"
        'description: "A skill-mesh managed skill."\n'
        "---\n"
        + _generated_header(profile)
        + "\n# " + name + "\n\nGenerated " + profile + " launcher body.\n"
    )


def generated_core_md(profile):
    return _generated_header(profile) + "\n# shared core\n\nGenerated core body.\n"


def hand_authored_skill_md(name):
    """A SKILL.md with NO provenance header -- foreign content at a managed path."""
    return (
        "---\n"
        "name: " + name + "\n"
        "---\n"
        "# " + name + " (operator-maintained)\n\n"
        "This SKILL.md was hand-authored and is not skill-mesh generated.\n"
    )


def consumer_skill_md(name):
    """A consumer's own skill: SKILL.md-shaped, absent from the manifest."""
    return (
        "---\n"
        "name: " + name + "\n"
        "description: \"A consumer's own skill.\"\n"
        "---\n"
        "# " + name + "\n\n"
        "Consumer-only skill; not part of the skill-mesh manifest.\n"
    )


def ledger(providers):
    """A well-formed install ledger naming exactly `providers`."""
    roots = {"claude": CLAUDE_ROOT, "gpt": GPT_ROOT}
    installs = {}
    for p in providers:
        sub = roots[p]
        installs[p] = {
            "provider": p,
            "discovery_subdir": sub,
            "owned_files": [sub + "/build-phase/SKILL.md", sub + "/build-phase/core.md"],
            "created_dirs": [sub, sub + "/build-phase"],
        }
    doc = {"tool": "skill-mesh", "ledger_version": 1, "installs": installs}
    return json.dumps(doc, indent=2) + "\n"


def router_source(version):
    """A router stub whose $ROUTER_VERSION line matches the inspector's regex."""
    return (
        "# skill-router (fixture stub)\n"
        "$ROUTER_VERSION = '" + version + "'\n"
    )


# --------------------------------------------------------------------------- #
# Shape assembly
# --------------------------------------------------------------------------- #

def write(home, rel, content):
    """Write `content` to `home/rel`, creating parents. Returns the path."""
    p = Path(home) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def write_exact(home, rel, content):
    r"""Write with NO newline translation.

    Load-bearing for the LF-terminated router-version plant: ``Path.write_text`` on
    Windows turns ``\n`` into ``\r\n``, and a CRLF terminator does NOT slip past even
    the old ``$``-anchored version regex (``\r`` blocks ``$``). A naive plant
    therefore looks clean and proves nothing.
    """
    p = Path(home) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(content)
    return p


def _generated(home):
    """Both profiles installed and owned, valid two-provider ledger, CLAUDE.md."""
    write(home, CLAUDE_ROOT + "/build-phase/SKILL.md", generated_skill_md("build-phase", "claude"))
    write(home, CLAUDE_ROOT + "/build-phase/core.md", generated_core_md("claude"))
    write(home, GPT_ROOT + "/build-phase/SKILL.md", generated_skill_md("build-phase", "gpt"))
    write(home, GPT_ROOT + "/build-phase/core.md", generated_core_md("gpt"))
    write(home, LEDGER_NAME, ledger(["claude", "gpt"]))
    write(home, "CLAUDE.md", "# workspace instructions\n")


def _legacy(home):
    """Hand-authored SKILL.md at two managed names; no ledger."""
    write(home, CLAUDE_ROOT + "/build-phase/SKILL.md", hand_authored_skill_md("build-phase"))
    write(home, CLAUDE_ROOT + "/build-step/SKILL.md", hand_authored_skill_md("build-step"))


def _mixed_owned(home):
    """One owned managed skill beside one foreign-content managed name."""
    write(home, CLAUDE_ROOT + "/build-phase/SKILL.md", generated_skill_md("build-phase", "claude"))
    write(home, CLAUDE_ROOT + "/build-phase/core.md", generated_core_md("claude"))
    write(home, CLAUDE_ROOT + "/build-step/SKILL.md", hand_authored_skill_md("build-step"))
    write(home, LEDGER_NAME, ledger(["claude"]))


def _absent_gpt(home):
    """Claude-only install carrying one portable and one provider-native skill."""
    write(home, CLAUDE_ROOT + "/build-phase/SKILL.md", generated_skill_md("build-phase", "claude"))
    write(home, CLAUDE_ROOT + "/build-phase/core.md", generated_core_md("claude"))
    write(home, CLAUDE_ROOT + "/context-slim/SKILL.md", generated_skill_md("context-slim", "claude"))
    write(home, LEDGER_NAME, ledger(["claude"]))


def _prior_wrong_target(home):
    """A pre-Step-44 GPT install at the RETIRED project-relative .copilot/skills."""
    write(home, RETIRED_COPILOT_ROOT + "/build-phase/SKILL.md", generated_skill_md("build-phase", "gpt"))
    write(home, RETIRED_COPILOT_ROOT + "/build-phase/core.md", generated_core_md("gpt"))
    write(home, "AGENTS.md", "# agent instructions\n")


def _consumer_only(home):
    write(home, CLAUDE_ROOT + "/build-observer/SKILL.md", consumer_skill_md("build-observer"))


def _both_trees_consumer_only(home):
    write(home, CLAUDE_ROOT + "/goblin-sweep/SKILL.md", consumer_skill_md("goblin-sweep"))
    write(home, LEGACY_SKILLS_GPT_ROOT + "/goblin-sweep/SKILL.md", consumer_skill_md("goblin-sweep"))


def _core_holder(home):
    write(home, CLAUDE_ROOT + "/_shared/judge-core.md",
          "# judge-core (shared core)\n\nHolds shared cores; this is not a skill (no SKILL.md).\n")


def _foreign(home):
    """The ONLY input that yields eligibility 'foreign': a directory under a
    discovery root that is absent from the manifest, holds no SKILL.md, and is not
    the `_shared` core-holder. Gives the four-class model its negative anchor (#85)."""
    write(home, CLAUDE_ROOT + "/" + FOREIGN_DIR + "/README.md",
          "# operator notes\n\nNot a skill: no SKILL.md, not _shared, not in the manifest.\n")


def _ledger_unparseable(home):
    """Corrupt path 1/3: the ledger is not JSON at all."""
    _generated(home)
    write(home, LEDGER_NAME, "{ this is not valid json\n")


def _ledger_bad_installs(home):
    """Corrupt path 2/3: `installs` is present but is not an object.

    The installs check runs BEFORE the version check, so ledger_version stays valid
    here to isolate this path."""
    _generated(home)
    write(home, LEDGER_NAME,
          json.dumps({"tool": "skill-mesh", "ledger_version": 1,
                      "installs": "not-an-object"}, indent=2) + "\n")


def _ledger_bad_version(home):
    """Corrupt path 3/3: unknown schema version.

    `installs` must stay a well-formed object or this would trip path 2 instead."""
    _generated(home)
    doc = json.loads(ledger(["claude"]))
    doc["ledger_version"] = 99
    write(home, LEDGER_NAME, json.dumps(doc, indent=2) + "\n")


def _router_canonical(home):
    write(home, CANONICAL_ROUTER, router_source("2.3.4"))


def _router_legacy(home):
    write(home, LEGACY_ROUTER, router_source("0.9.1"))


def _router_unparseable_version(home):
    """Router present at the canonical path but with a non-semver version, so
    classification must still resolve while `version` stays null."""
    write(home, CANONICAL_ROUTER, router_source("not-a-semver"))


def _provider_case_variant(home):
    """A LEGITIMATE install whose provider slug is spelled in another case.

    Reachable with no hostile actor at all: the installer's
    [ValidateSet('claude','gpt')] accepts `-Provider CLAUDE` case-insensitively and
    does NOT normalize, so that spelling lands verbatim in the ledger key and in the
    generated `Profile:` line. The report must RECOGNIZE it (dropping a real install
    is a false-clean preflight, worse than the leak) AND normalize it to the manifest
    slug (echoing it breaks the closed vocabulary).
    """
    _generated(home)
    doc = json.loads(ledger(["claude"]))
    doc["installs"] = {"CLAUDE": doc["installs"]["claude"]}
    write(home, LEDGER_NAME, json.dumps(doc, indent=2) + "\n")
    skill_md = Path(home) / CLAUDE_ROOT / "build-phase" / "SKILL.md"
    skill_md.write_text(
        skill_md.read_text(encoding="utf-8").replace("Profile: claude", "Profile: CLAUDE"),
        encoding="utf-8")


def _provider_lookalike(home):
    """A provider token a CULTURE-aware comparison would wrongly accept.

    PowerShell's `-contains` ignores Unicode-ignorable format characters, so
    'claude' + U+00AD*300 compares EQUAL to 'claude'. Matching that way and echoing
    the matched token would put 300 unbounded non-ASCII consumer bytes into the
    report labelled as a recognized provider -- the exact leak class the closed
    vocabulary exists to prevent.
    """
    _generated(home)
    doc = json.loads(ledger(["claude"]))
    doc["installs"] = {LOOKALIKE_PROVIDER_KEY: doc["installs"]["claude"]}
    write(home, LEDGER_NAME, json.dumps(doc, indent=2) + "\n")


def _hostile(home):
    """A home whose every consumer-controlled channel carries a hostile value (#84).

    Built ON TOP of the generated shape so the legitimate values sit beside the
    hostile ones -- a report that dropped BOTH would look clean while being broken.
    """
    _generated(home)
    # Ledger KEYS (not nested values): free-form text, proven able to carry an
    # absolute path, an embedded newline, and unbounded length into the report.
    doc = json.loads(ledger(["claude", "gpt"]))
    doc["installs"][VICTIM_PATH] = {"provider": "x"}
    doc["installs"]["claude\nINJECTED_LEDGER_LINE: " + SECRET] = {"provider": "x"}
    doc["installs"]["Q" * 400] = {"provider": "x"}
    write(home, LEDGER_NAME, json.dumps(doc, indent=2) + "\n")
    # A decoy `Profile:` line ABOVE the real generated header: the provenance parser
    # matches its header block anywhere in the head, so arbitrary bytes may precede it.
    skill_md = Path(home) / CLAUDE_ROOT / "build-phase" / "SKILL.md"
    skill_md.write_text("Profile: " + SECRET + "\n" + skill_md.read_text(encoding="utf-8"),
                        encoding="utf-8")
    # Directory names: over-long, and one carrying the exact ', ' separator the
    # warning lists are joined with.
    #
    # OVERLONG_NAME_LEN is deliberately modest. It only has to exceed the display cap
    # (64) to prove truncation, and every extra character is charged against
    # MAX_PATH: the fixture path is tmp_path + ".claude/skills/" + name +
    # "/SKILL.md", so a 240-char name overflows 260 on its own and the whole shape
    # fails to build on any machine without LongPathsEnabled -- which is most of
    # them, and which no CI here would catch.
    for dirname in (SECRET, "comma,injected-name", "Z" * OVERLONG_NAME_LEN):
        write(home, CLAUDE_ROOT + "/" + dirname + "/SKILL.md", consumer_skill_md("x"))
    # A router version terminated by a bare LF (see write_exact).
    write_exact(home, LEGACY_ROUTER, "$ROUTER_VERSION = '1.2.3\n'\n")


_BUILDERS = {
    "01-clean": lambda home: None,
    "02-generated": _generated,
    "03-legacy": _legacy,
    "04-mixed-owned": _mixed_owned,
    "06-absent-gpt": _absent_gpt,
    "07-prior-wrong-target": _prior_wrong_target,
    "08-consumer-only": _consumer_only,
    "09-both-trees-consumer-only": _both_trees_consumer_only,
    "10-core-holder": _core_holder,
    "11-foreign": _foreign,
    "12-ledger-unparseable": _ledger_unparseable,
    "13-ledger-bad-installs": _ledger_bad_installs,
    "14-ledger-bad-version": _ledger_bad_version,
    "15-router-canonical": _router_canonical,
    "16-router-legacy": _router_legacy,
    "17-router-bad-version": _router_unparseable_version,
    "19-hostile": _hostile,
    "20-provider-case-variant": _provider_case_variant,
    "21-provider-lookalike": _provider_lookalike,
}

# Shapes this module builds directly. The junction shapes (05-junction and
# 18-junction-external) need a second directory outside the home, so the test
# module builds them on top of `build()`.
SHAPES = sorted(_BUILDERS)


def build(kind, home):
    """Materialize consumer-home shape `kind` at `home`. Returns `home`."""
    home = Path(home)
    home.mkdir(parents=True, exist_ok=True)
    try:
        builder = _BUILDERS[kind]
    except KeyError:
        raise AssertionError("unknown fixture shape: " + repr(kind))
    builder(home)
    return home
