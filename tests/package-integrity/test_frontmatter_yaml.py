"""Strict-YAML frontmatter gate for the CANONICAL adapter sources (Step 68, #69).

Issue #69 was reported as a builder defect and is not one: there is no Claude
frontmatter builder. tools/build-distributions.ps1 passes the canonical
`skills/<name>/providers/claude.md` frontmatter through verbatim ("Claude output is
untouched -- its canonical claude.md already ships frontmatter"), so the only place
the defect can live is the SOURCE, and the only place it can be fixed is the source.
This module grades the source; tests/distributions/test_distributions.py grades the
bytes that reach a host. Both import their rules from frontmatter_contract.py.

The measured defect: 50 of 50 Claude adapters carried a frontmatter block, 49 parsed
under a strict parser, and one -- `context-slim`, the only file in the repository with
an `argument` key -- did not, because its value opened `Optional flags: --project ...`
unquoted. Copilot CLI's scan of the Claude discovery root rejected that file outright.

What this gate does NOT do is quote every scalar. `user-invocable: true` must stay a
real boolean, and `claude-oauth-auth`'s deliberate `user-invocable: false` must stay
falsy: quoted, it becomes the string 'false', which is TRUTHY in every strict parser,
and a presence-only assertion would ship that green. Hence the identity checks below.

Every assertion has an anchor test that plants the corresponding defect and proves
this gate goes RED on it (.claude/rules/measurement-validity.md -- a gate never seen
red is not a gate).

Run: `python -m pytest tests/package-integrity/test_frontmatter_yaml.py`
"""

from pathlib import Path

from frontmatter_contract import (
    CLAUDE_KEYS,
    frontmatter_defects,
    parse_frontmatter,
    split_frontmatter,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "skills"

# Floor, not an equality: skills are added, never quietly removed. Below it, every
# per-file loop in this module would be vacuous.
MIN_CLAUDE_ADAPTERS = 50

# The one skill whose adapter deliberately declares itself NOT user-invocable. It is
# a reference document, not a command. Pinned by name so a regression that flips the
# flag -- or quotes it into a truthy string -- has to change this list on purpose.
SUPPRESSED_SKILLS = {"claude-oauth-auth"}


def _claude_adapters():
    return sorted(SKILLS_ROOT.glob("*/providers/claude.md"))


def _gpt_adapters():
    return sorted(SKILLS_ROOT.glob("*/providers/gpt.md"))


def _rel(path):
    return path.relative_to(REPO_ROOT).as_posix()


def _read(path):
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# The live tree
# --------------------------------------------------------------------------- #

def test_every_canonical_claude_adapter_frontmatter_satisfies_the_contract():
    """The whole point of the step: 50 of 50 parse strictly, with a closed key
    allowlist, real booleans, and no double-quoted values."""
    adapters = _claude_adapters()
    assert len(adapters) >= MIN_CLAUDE_ADAPTERS, (
        f"only {len(adapters)} Claude adapter(s) found under {SKILLS_ROOT.name}/, "
        f"floor is {MIN_CLAUDE_ADAPTERS} -- every check below would be vacuous")
    failures = []
    for path in adapters:
        for defect in frontmatter_defects(_read(path), allowed_keys=CLAUDE_KEYS):
            failures.append(f"{_rel(path)}: {defect}")
    assert not failures, (
        "canonical Claude frontmatter violates the strict-YAML contract:\n  "
        + "\n  ".join(failures))


def test_canonical_gpt_adapters_carry_no_frontmatter_and_are_graded_if_they_grow_one():
    """The GPT adapters carry no frontmatter today -- the builder synthesizes it from
    the manifest. That premise is asserted rather than assumed (if it changes, the
    pass-through branch of build-distributions.ps1 starts shipping these bytes), and
    any block that does appear is graded by the same contract."""
    adapters = _gpt_adapters()
    assert len(adapters) >= MIN_CLAUDE_ADAPTERS - 3, \
        f"only {len(adapters)} GPT adapter(s) found -- this check would be vacuous"
    failures = []
    with_block = []
    for path in adapters:
        text = _read(path)
        if split_frontmatter(text) is None:
            continue
        with_block.append(_rel(path))
        for defect in frontmatter_defects(text):
            failures.append(f"{_rel(path)}: {defect}")
    assert not failures, (
        "a canonical GPT adapter grew frontmatter that violates the contract:\n  "
        + "\n  ".join(failures))
    assert not with_block, (
        "a canonical GPT adapter now ships its own frontmatter: "
        f"{with_block}. That is not forbidden, but it routes the build through "
        "build-distributions.ps1's pass-through branch instead of "
        "New-GptFrontmatter -- confirm the emitted profile is still graded before "
        "updating this premise.")


def test_user_invocable_is_a_real_boolean_and_the_suppression_is_pinned():
    """IDENTITY, not truthiness. `user-invocable: "false"` parses to 'false' -- a
    truthy string -- so `if value:` and `assert value` both pass on the exact
    regression this step exists to prevent."""
    declared_true = []
    declared_false = []
    for path in _claude_adapters():
        fm = parse_frontmatter(_read(path))
        assert fm is not None, f"{_rel(path)}: frontmatter did not parse"
        if "user-invocable" not in fm:
            continue
        value = fm["user-invocable"]
        name = path.parent.parent.name
        if value is True:
            declared_true.append(name)
        elif value is False:
            declared_false.append(name)
        else:
            raise AssertionError(
                f"{_rel(path)}: user-invocable is {value!r} ({type(value).__name__}), "
                "not an unquoted YAML boolean")
    assert set(declared_false) == SUPPRESSED_SKILLS, (
        f"the set of skills declaring `user-invocable: false` changed: "
        f"{sorted(declared_false)} != {sorted(SUPPRESSED_SKILLS)}. Suppression is a "
        "deliberate behavior contract -- change it in the adapter and here together.")
    assert len(declared_true) >= MIN_CLAUDE_ADAPTERS - len(SUPPRESSED_SKILLS) - 1, (
        f"only {len(declared_true)} adapter(s) declare `user-invocable: true` -- "
        "the identity assertion above is close to vacuous")


def test_no_adapter_spells_the_user_invokable_typo():
    """`user-invokable` sat in claude-oauth-auth's adapter doing nothing: every host
    reads `user-invocable`, so a deliberate suppression flag had never taken effect.
    The key allowlist catches it, but the misspelling gets its own named gate so the
    fix cannot be silently reverted."""
    offenders = [_rel(p) for p in _claude_adapters() + _gpt_adapters()
                 if "user-invokable" in _read(p)]
    assert not offenders, (
        f"the `user-invokable` misspelling is back in {offenders} -- the correct "
        "spelling is `user-invocable`")


def test_the_colon_bearing_value_that_broke_copilot_now_parses():
    """context-slim's `argument` is the live witness for #69: the only canonical value
    carrying a `: ` sequence. It must parse, keep its colons, and carry NO surrounding
    quotes in the parsed value (quoting the source is the fix; quoting the VALUE would
    be the fix applied twice)."""
    path = SKILLS_ROOT / "context-slim" / "providers" / "claude.md"
    text = _read(path)
    assert frontmatter_defects(text, allowed_keys=CLAUDE_KEYS) == [], \
        frontmatter_defects(text, allowed_keys=CLAUDE_KEYS)
    fm = parse_frontmatter(text)
    argument = fm["argument"]
    assert ": " in argument, (
        "context-slim's `argument` no longer carries a colon -- it was this "
        "repository's only colon-bearing frontmatter value, and without one the "
        "live-tree half of this gate proves nothing. Keep a colon-bearing value "
        "here, or move the witness deliberately.")
    assert not (argument.startswith('"') and argument.endswith('"')), \
        f"context-slim's `argument` value is itself quoted: {argument!r}"
    assert "--project" in argument and "--apply" in argument, \
        f"context-slim's `argument` lost content in the parse: {argument!r}"


def test_at_least_one_canonical_value_is_quoted_so_the_no_double_quoting_rule_bites():
    """Vacuity guard for rule 4: if no canonical value is quoted at the source, the
    "already-quoted values are not quoted again" assertion never exercises anything."""
    quoted = []
    for path in _claude_adapters():
        block, _ = split_frontmatter(_read(path))
        for line in block.splitlines():
            if ": \"" in line:
                quoted.append(_rel(path))
                break
    assert quoted, (
        "no canonical adapter carries a double-quoted frontmatter value, so the "
        "double-quoting rule is untested against the live tree")


# --------------------------------------------------------------------------- #
# ANCHORS -- each plants one defect and proves this gate reds on it
# --------------------------------------------------------------------------- #

_GOOD = (
    "---\n"
    "name: demo\n"
    'description: "Does a thing: carefully, with a colon."\n'
    "user-invocable: true\n"
    'argument: "Optional flags: --project <name-or-path> (default: innermost)"\n'
    "---\n"
    "\n# demo\n"
)


def test_anchor_the_contract_accepts_a_quoted_colon_bearing_pair():
    """Positive control. Without it, every anchor below could be passing because the
    checker reports a defect on EVERYTHING."""
    assert frontmatter_defects(_GOOD) == [], frontmatter_defects(_GOOD)
    fm = parse_frontmatter(_GOOD)
    assert fm["description"] == "Does a thing: carefully, with a colon."
    assert fm["argument"] == \
        "Optional flags: --project <name-or-path> (default: innermost)"
    assert fm["user-invocable"] is True


def test_anchor_reds_on_an_unquoted_colon_bearing_description():
    bad = _GOOD.replace('description: "Does a thing: carefully, with a colon."',
                        "description: Does a thing: carefully, with a colon.")
    assert bad != _GOOD, "the probe did not change the block"
    defects = frontmatter_defects(bad)
    assert any("not valid YAML" in d for d in defects), defects


def test_anchor_reds_on_an_unquoted_colon_bearing_argument():
    bad = _GOOD.replace(
        'argument: "Optional flags: --project <name-or-path> (default: innermost)"',
        "argument: Optional flags: --project <name-or-path> (default: innermost)")
    assert bad != _GOOD, "the probe did not change the block"
    defects = frontmatter_defects(bad)
    assert any("not valid YAML" in d for d in defects), defects


def test_anchor_reds_on_the_user_invokable_misspelling():
    bad = _GOOD.replace("user-invocable: true", "user-invokable: false")
    assert bad != _GOOD, "the probe did not change the block"
    defects = frontmatter_defects(bad)
    assert any("unknown key 'user-invokable'" in d for d in defects), defects


def test_anchor_reds_on_a_quoted_boolean_in_both_directions():
    """The blanket-quoting regression, in the direction that matters most: a quoted
    'false' is truthy, so it silently INVERTS a suppression flag."""
    for literal in ('"false"', '"true"', "'false'"):
        bad = _GOOD.replace("user-invocable: true", f"user-invocable: {literal}")
        assert bad != _GOOD, "the probe did not change the block"
        defects = frontmatter_defects(bad)
        assert any("not an unquoted YAML boolean" in d for d in defects), \
            f"{literal}: {defects}"
    # And the reason it matters, stated as an executable fact rather than a comment.
    assert bool(parse_frontmatter(
        _GOOD.replace("user-invocable: true", 'user-invocable: "false"')
    )["user-invocable"]) is True


def test_anchor_reds_on_a_value_quoted_twice():
    bad = _GOOD.replace('description: "Does a thing: carefully, with a colon."',
                        'description: "\\"Does a thing\\""')
    assert bad != _GOOD, "the probe did not change the block"
    defects = frontmatter_defects(bad)
    assert any("quoted a second time" in d for d in defects), defects


def test_anchor_reds_on_a_comment_truncated_value():
    """Parses cleanly, loses text. Rule 1 alone cannot see this one."""
    bad = _GOOD.replace('description: "Does a thing: carefully, with a colon."',
                        "description: Does a thing # carefully")
    assert bad != _GOOD, "the probe did not change the block"
    assert parse_frontmatter(bad)["description"] == "Does a thing", \
        "the probe did not actually truncate -- this anchor would be vacuous"
    defects = frontmatter_defects(bad)
    assert any("did not survive the parse" in d for d in defects), defects


def test_anchor_reds_on_a_duplicate_key():
    bad = _GOOD.replace("user-invocable: true",
                        "user-invocable: true\ndescription: second")
    assert bad != _GOOD, "the probe did not change the block"
    defects = frontmatter_defects(bad)
    assert any("duplicate key 'description'" in d for d in defects), defects


def test_anchor_reds_on_a_missing_or_unterminated_block():
    assert frontmatter_defects("# demo\n\nno frontmatter here\n") == \
        ["does not lead with a `---` frontmatter block closed by a `---` line"]
    assert frontmatter_defects("---\nname: demo\n# never closed\n") == \
        ["does not lead with a `---` frontmatter block closed by a `---` line"]
    assert split_frontmatter("---\nname: demo\n# never closed\n") is None


def test_anchor_reds_on_a_missing_required_key_and_on_a_non_mapping():
    bad = _GOOD.replace("name: demo\n", "")
    assert any("missing required key 'name'" in d for d in frontmatter_defects(bad)), \
        frontmatter_defects(bad)
    assert any("not a mapping" in d
               for d in frontmatter_defects("---\n- a\n- b\n---\nbody\n")), \
        frontmatter_defects("---\n- a\n- b\n---\nbody\n")


def test_anchor_the_allowlist_is_closed_not_advisory():
    """A narrower allowlist must reject a key the wider one permits -- proof the
    parameter is actually consulted, not decoration."""
    defects = frontmatter_defects(_GOOD, allowed_keys=frozenset({"name", "description"}))
    assert any("unknown key 'argument'" in d for d in defects), defects
    assert any("unknown key 'user-invocable'" in d for d in defects), defects
