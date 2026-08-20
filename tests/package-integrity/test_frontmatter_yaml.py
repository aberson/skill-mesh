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

The strict parser is PyYAML, a declared Environment requirement. When it is absent
this file goes RED and says so by name -- it never skips (a skip is a false green)
and it never breaks collection (that would erase ~1004 unrelated tests' verdicts).
frontmatter_contract.require_yaml() is what makes that possible; its docstring owns
the reasoning.

Run: `python -m pytest tests/package-integrity/test_frontmatter_yaml.py`
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

import frontmatter_contract as fc

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "skills"

# Floor, not an equality: skills are added, never quietly removed. Below it, every
# per-file loop in this module would be vacuous. Raised 50 -> 57 at Phase CP
# Step 10 (issue #127); a floor left behind the catalog stops noticing a
# whole promotion's worth of adapters going missing.
MIN_CLAUDE_ADAPTERS = 57

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
# The dependency this gate is only as good as
# --------------------------------------------------------------------------- #

def test_the_strict_yaml_parser_this_gate_depends_on_is_installed():
    """Named, first, and a FAILURE -- so a machine without PyYAML learns it from a
    red line rather than from a skip nobody reads or a collection abort that takes
    the rest of the suite's verdict with it.

    Every check below that calls the parser reds with this same message via
    frontmatter_contract.require_yaml(); this one exists so the summary names the
    cause once, unambiguously, instead of leaving the reader to infer it from
    fifteen downstream tracebacks.
    """
    assert fc.YAML_IMPORT_ERROR is None, fc.YAML_IMPORT_ERROR
    assert fc.require_yaml() is not None


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
        for defect in fc.frontmatter_defects(_read(path), allowed_keys=fc.CLAUDE_KEYS):
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
        if fc.split_frontmatter(text) is None:
            continue
        with_block.append(_rel(path))
        for defect in fc.frontmatter_defects(text):
            failures.append(f"{_rel(path)}: {defect}")
    assert not failures, (
        "a canonical GPT adapter grew frontmatter that violates the contract:\n  "
        + "\n  ".join(failures))
    assert not with_block, (
        "a canonical GPT adapter now ships its own frontmatter: "
        f"{with_block}. That is not forbidden, but it routes the build through "
        "build-distributions.ps1's pass-through branch instead of "
        "New-SynthesizedFrontmatter -- confirm the emitted profile is still graded before "
        "updating this premise.")


def test_user_invocable_is_a_real_boolean_and_the_suppression_is_pinned():
    """IDENTITY, not truthiness. `user-invocable: "false"` parses to 'false' -- a
    truthy string -- so `if value:` and `assert value` both pass on the exact
    regression this step exists to prevent."""
    declared_true = []
    declared_false = []
    for path in _claude_adapters():
        fm = fc.parse_frontmatter(_read(path))
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
    assert fc.frontmatter_defects(text, allowed_keys=fc.CLAUDE_KEYS) == [], \
        fc.frontmatter_defects(text, allowed_keys=fc.CLAUDE_KEYS)
    fm = fc.parse_frontmatter(text)
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
        block, _ = fc.split_frontmatter(_read(path))
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
    assert fc.frontmatter_defects(_GOOD) == [], fc.frontmatter_defects(_GOOD)
    fm = fc.parse_frontmatter(_GOOD)
    assert fm["description"] == "Does a thing: carefully, with a colon."
    assert fm["argument"] == \
        "Optional flags: --project <name-or-path> (default: innermost)"
    assert fm["user-invocable"] is True


def test_anchor_reds_on_an_unquoted_colon_bearing_description():
    bad = _GOOD.replace('description: "Does a thing: carefully, with a colon."',
                        "description: Does a thing: carefully, with a colon.")
    assert bad != _GOOD, "the probe did not change the block"
    defects = fc.frontmatter_defects(bad)
    assert any("not valid YAML" in d for d in defects), defects


def test_anchor_reds_on_an_unquoted_colon_bearing_argument():
    bad = _GOOD.replace(
        'argument: "Optional flags: --project <name-or-path> (default: innermost)"',
        "argument: Optional flags: --project <name-or-path> (default: innermost)")
    assert bad != _GOOD, "the probe did not change the block"
    defects = fc.frontmatter_defects(bad)
    assert any("not valid YAML" in d for d in defects), defects


def test_anchor_reds_on_the_user_invokable_misspelling():
    bad = _GOOD.replace("user-invocable: true", "user-invokable: false")
    assert bad != _GOOD, "the probe did not change the block"
    defects = fc.frontmatter_defects(bad)
    assert any("unknown key 'user-invokable'" in d for d in defects), defects


def test_anchor_reds_on_a_quoted_boolean_in_both_directions():
    """The blanket-quoting regression, in the direction that matters most: a quoted
    'false' is truthy, so it silently INVERTS a suppression flag."""
    for literal in ('"false"', '"true"', "'false'"):
        bad = _GOOD.replace("user-invocable: true", f"user-invocable: {literal}")
        assert bad != _GOOD, "the probe did not change the block"
        defects = fc.frontmatter_defects(bad)
        assert any("not an unquoted YAML boolean" in d for d in defects), \
            f"{literal}: {defects}"
    # And the reason it matters, stated as an executable fact rather than a comment.
    assert bool(fc.parse_frontmatter(
        _GOOD.replace("user-invocable: true", 'user-invocable: "false"')
    )["user-invocable"]) is True


def test_anchor_reds_on_a_value_quoted_twice():
    bad = _GOOD.replace('description: "Does a thing: carefully, with a colon."',
                        'description: "\\"Does a thing\\""')
    assert bad != _GOOD, "the probe did not change the block"
    defects = fc.frontmatter_defects(bad)
    assert any("quoted a second time" in d for d in defects), defects


def test_anchor_reds_on_a_comment_truncated_value():
    """Parses cleanly, loses text. Rule 1 alone cannot see this one."""
    bad = _GOOD.replace('description: "Does a thing: carefully, with a colon."',
                        "description: Does a thing # carefully")
    assert bad != _GOOD, "the probe did not change the block"
    assert fc.parse_frontmatter(bad)["description"] == "Does a thing", \
        "the probe did not actually truncate -- this anchor would be vacuous"
    defects = fc.frontmatter_defects(bad)
    assert any("did not survive the parse" in d for d in defects), defects


def test_anchor_reds_on_a_duplicate_key():
    bad = _GOOD.replace("user-invocable: true",
                        "user-invocable: true\ndescription: second")
    assert bad != _GOOD, "the probe did not change the block"
    defects = fc.frontmatter_defects(bad)
    assert any("duplicate key 'description'" in d for d in defects), defects


def test_anchor_reds_on_a_missing_or_unterminated_block():
    assert fc.frontmatter_defects("# demo\n\nno frontmatter here\n") == \
        ["does not lead with a `---` frontmatter block closed by a `---` line"]
    assert fc.frontmatter_defects("---\nname: demo\n# never closed\n") == \
        ["does not lead with a `---` frontmatter block closed by a `---` line"]
    assert fc.split_frontmatter("---\nname: demo\n# never closed\n") is None


def test_anchor_reds_on_a_missing_required_key_and_on_a_non_mapping():
    bad = _GOOD.replace("name: demo\n", "")
    assert any("missing required key 'name'" in d for d in fc.frontmatter_defects(bad)), \
        fc.frontmatter_defects(bad)
    assert any("not a mapping" in d
               for d in fc.frontmatter_defects("---\n- a\n- b\n---\nbody\n")), \
        fc.frontmatter_defects("---\n- a\n- b\n---\nbody\n")


def test_anchor_the_allowlist_is_closed_not_advisory():
    """A narrower allowlist must reject a key the wider one permits -- proof the
    parameter is actually consulted, not decoration."""
    defects = fc.frontmatter_defects(_GOOD, allowed_keys=frozenset({"name", "description"}))
    assert any("unknown key 'argument'" in d for d in defects), defects
    assert any("unknown key 'user-invocable'" in d for d in defects), defects


def _contract_with_yaml_blocked():
    """A SECOND, throwaway copy of the contract module loaded with `import yaml`
    forced to fail -- the absent-PyYAML condition, reproduced in-process.

    `sys.modules["yaml"] = None` is the documented way to make CPython raise
    ImportError for a name without uninstalling anything; the real module object is
    saved and restored in a finally, so nothing outside this call is affected.
    """
    saved = sys.modules.get("yaml")
    sys.modules["yaml"] = None
    try:
        spec = importlib.util.spec_from_file_location(
            "frontmatter_contract_yaml_blocked", Path(fc.__file__))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if saved is None:
            sys.modules.pop("yaml", None)
        else:
            sys.modules["yaml"] = saved


def test_anchor_a_missing_parser_reds_this_gate_and_leaves_collection_standing():
    """The anchor for the dependency handling itself -- without it, the absent-PyYAML
    behaviour would rest on a one-time manual experiment rather than on a gate
    (.claude/rules/measurement-validity.md: a gate never seen red is not a gate).

    Proves all four properties the design has to hold at once, in the one condition
    that exercises them.
    """
    # 1. IMPORTING it must not raise. This call returning at all is the proof that a
    # missing dependency cannot abort collection and erase every other test's verdict.
    # An ordinary exception is re-raised so its traceback survives; a BaseException
    # that is NOT an Exception (pytest's own skip signal is exactly that) would be
    # dispatched by pytest as a SKIP of this test rather than a failure, so it is
    # converted into an explicit failure here instead of being allowed to propagate.
    try:
        module = _contract_with_yaml_blocked()
    except Exception:
        raise
    except BaseException as exc:
        pytest.fail(
            f"importing the contract module with PyYAML blocked raised {exc!r}, a "
            "BaseException that is not an Exception -- pytest reports that as a SKIP "
            "of this anchor, not a failure, which is the exact outcome this anchor "
            "exists to make impossible")

    # 2. The failure is RECORDED, and its message is actionable.
    assert module.YAML_IMPORT_ERROR is not None
    for token in ("PyYAML", "pip install pyyaml", "CLAUDE.md",
                  "Environment requirements"):
        assert token in module.YAML_IMPORT_ERROR, \
            f"the missing-dependency message no longer names {token!r}"

    # 3. Parserless work still answers truthfully rather than failing for show.
    assert module.split_frontmatter(_GOOD) is not None

    # 4. Everything that needs a parser reds at CALL time -- and reds as an ordinary
    # Exception. pytest's skip signal is a BaseException that is NOT an Exception, so
    # the isinstance check below is what distinguishes "fails loudly" from "skips
    # quietly".
    #
    # `pytest.raises(RuntimeError)` CANNOT make that distinction and must not be used
    # here: it only suppresses exceptions matching the declared type, so a skip-shaped
    # BaseException would sail past it, out of this test body, and be converted by
    # pytest's own outcome dispatcher into a SKIP of the whole anchor -- with the
    # isinstance assertion never reached. `except BaseException` catches
    # unconditionally, which puts the pass/fail decision in the assertions below
    # rather than in pytest's implicit Skipped-to-skip handling.
    for entry_point in (module.frontmatter_defects, module.parse_frontmatter):
        try:
            entry_point(_GOOD)
        except BaseException as exc:
            assert isinstance(exc, Exception), (
                f"{entry_point.__name__} raised {exc!r} -- a BaseException that is "
                "not an Exception. pytest reports that as a SKIP, not a FAILURE, so "
                "a missing parser would paint this gate green on the one machine "
                "nobody checked. It must FAIL, never skip.")
            assert isinstance(exc, RuntimeError), (
                f"{entry_point.__name__} raised {exc!r}, not the RuntimeError "
                "require_yaml() promises")
            assert "PyYAML" in str(exc)
            assert exc.__cause__ is module._YAML_IMPORT_EXC, (
                "the raise lost its `from _YAML_IMPORT_EXC` chain -- the original "
                "ImportError is what tells an operator WHICH import failed")
        else:
            pytest.fail(
                f"{entry_point.__name__} returned a verdict with no parser installed "
                "-- a 'no defects' answer without a parser is an over-claim, not a "
                "pass")

    # And the real module is untouched by the probe.
    assert fc.YAML_IMPORT_ERROR is None
    assert fc.frontmatter_defects(_GOOD) == []


def _codex_adapters():
    return sorted(SKILLS_ROOT.glob("*/providers/codex.md"))


def test_canonical_codex_adapters_carry_no_frontmatter_and_are_graded_if_they_grow_one():
    """The codex arm of the premise above (Phase CP Step 3, issue #120).

    LIVE SINCE PHASE CP STEP 4, and armed since Step 3. Step 3 built the generation
    rails and authored ZERO codex adapters, so the per-file loop below had nothing to
    iterate; Step 4 landed the pilot five and the loop started grading them with no edit
    here, which is the whole point of having armed it early. Its sibling GPT check can
    assert a vacuity FLOOR (>= 47 adapters); this one still cannot, because the roster
    grows across Steps 6-8 and a spelled floor here would have to move every time.

    What it does instead, so the count is a CHECKED FACT rather than an accident:

      * The count is cross-checked against the manifest's own `counts["codex"]`. A typo
        in the glob (`codex.MD`, `provider/`) would silently return 0 forever and this
        gate would report PASS for the rest of Phase CP -- the exact false-green shape
        this repository keeps getting bitten by. Tying it to a number produced by a
        different generator, from a different input, makes a broken glob loud.
      * The roster's exact membership is pinned elsewhere, by
        tests/package-integrity/test_manifest_contract.py::test_exact_codex_set, so this
        gate can stay a pure frontmatter check.

    The premise itself is the same as the GPT one: canonical adapters ship no frontmatter
    because build-distributions.ps1 synthesizes it from the manifest record
    (New-SynthesizedFrontmatter, shared by both profiles). If one grows its own block the
    build silently routes through the pass-through branch instead, so the premise is
    asserted, and any block that does appear is graded -- under CODEX_KEYS, which is
    codex's actual contract, not Claude's laxer superset.
    """
    adapters = _codex_adapters()
    manifest = json.loads(
        (REPO_ROOT / "config" / "skill-manifest.json").read_text(encoding="utf-8"))
    assert len(adapters) == manifest["counts"]["codex"], (
        f"{len(adapters)} skills/*/providers/codex.md on disk but the manifest counts "
        f"{manifest['counts']['codex']} -- either the glob is wrong (this gate would be "
        "silently vacuous for the rest of Phase CP) or the manifest needs regenerating "
        "with `python tools/gen_manifest.py`")

    failures = []
    with_block = []
    for path in adapters:
        text = _read(path)
        if fc.split_frontmatter(text) is None:
            continue
        with_block.append(_rel(path))
        for defect in fc.frontmatter_defects(text, allowed_keys=fc.CODEX_KEYS):
            failures.append(f"{_rel(path)}: {defect}")
    assert not failures, (
        "a canonical codex adapter grew frontmatter that violates the contract:\n  "
        + "\n  ".join(failures))
    assert not with_block, (
        "a canonical codex adapter now ships its own frontmatter: "
        f"{with_block}. That is not forbidden, but it routes the build through "
        "build-distributions.ps1's pass-through branch instead of "
        "New-SynthesizedFrontmatter -- confirm the emitted profile is still graded "
        "before updating this premise.")


def test_no_provider_native_skill_carries_a_codex_adapter():
    """Provider-native is CLAUDE-ONLY, so codex.md must not appear in one.

    Non-vacuous TODAY, unlike the check above: the three native skills exist now, so
    this genuinely grades something at Step 3. It is the frontmatter-suite view of a
    contract also enforced in tools/gen_manifest.py (derived_skill_sets raises),
    tests/package-integrity/test_manifest_contract.py (manifest records),
    tests/package-integrity/test_skill_tree.py (tree shape) and tools/release_checks.py
    (release gate) -- four independent layers, because the builder EXCLUDES these skills
    from every non-claude profile and a declaration here would promise a package that is
    never emitted.
    """
    offenders = []
    for path in _claude_adapters():
        skill_dir = path.parent.parent
        if (skill_dir / "core.md").exists():
            continue  # portable: a codex adapter is legitimate here
        if (skill_dir / "providers" / "codex.md").exists():
            offenders.append(skill_dir.name)
    assert not offenders, (
        "provider-native (Claude-only) skills must not carry providers/codex.md: "
        f"{sorted(offenders)}")
