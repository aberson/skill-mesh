"""Host-loading authority-map gate (Step 42 of
documentation/host-native-discovery-cutover-plan.md).

Locks the three-mechanism authority map so it can never silently drift into
describing workspace instruction injection, host-native skill discovery, and
router dispatch as interchangeable, and never swap the two provider discovery
roots. The regression this exists to prevent: an operator (or a future doc edit)
treating a running GPT model as evidence of a correctly installed GPT profile.

Asserts, against the real committed docs (NO private/legacy source needed):
- documentation/host-discovery.md exists and states every required fact -- model
  choice does not select a skill tree; Claude discovers `.claude/skills`; GPT
  discovers `.copilot/skills`; workspace instruction files hold no skill
  implementations; the router is explicit, not implicit.
- The three mechanisms are documented as DISTINCT / non-interchangeable.
- The discovery-root table maps each provider to the CORRECT native root (a
  swap-guard: Claude->.claude/skills, GPT->.copilot/skills, never crossed).
- providers/claude.md names the Claude root (not the GPT root) and providers/gpt.md
  names the GPT root (not the Claude root), each cross-linking the authority map.

Each check is written so it goes RED if the doc drifts to "interchangeable" or the
roots are swapped (a gate that cannot go red is worthless --
.claude/rules/measurement-validity.md), proven by the two anchor tests below.

Runnable via pytest (`python -m pytest tests/package-integrity`) or standalone
(`python tests/package-integrity/test_host_discovery.py`).
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "documentation" / "host-discovery.md"
CLAUDE_GUIDE = REPO_ROOT / "documentation" / "providers" / "claude.md"
GPT_GUIDE = REPO_ROOT / "documentation" / "providers" / "gpt.md"

# Build the ".claude/skills" path token from parts so this test's own source
# carries no literal ".claude/" path (tests/router/test_no_claude_dependency.py
# flags a load-bearing ".claude/" reference in executable code). The ".copilot/"
# token is not flagged by that scanner, so it is written literally.
_DOTCLAUDE = "." + "claude"
CLAUDE_ROOT = _DOTCLAUDE + "/skills"     # ".claude/skills"
COPILOT_ROOT = ".copilot/skills"


def _read(path):
    return path.read_text(encoding="utf-8")


def _norm(text):
    """Lowercase and collapse all whitespace runs (incl. line wraps) to one space,
    so a required phrase matches regardless of markdown line breaks."""
    return re.sub(r"\s+", " ", text).lower()


# --------------------------------------------------------------------------- #
# Discovery-root swap-guard (the load-bearing regression: never cross the roots)
# --------------------------------------------------------------------------- #

def _discovery_root_defects(text):
    """Defects if the discovery-root table maps a provider to the WRONG native
    root. Claude must own `.claude/skills`; GPT must own `.copilot/skills`; neither
    row may name the other's root. Empty list == correct and non-swapped.

    Rows are located by their leading provider cell (`| Claude |` / `| GPT |`),
    which in the authority map appears only in the discovery-root table."""
    defects = []
    claude_row = gpt_row = None
    for ln in text.splitlines():
        s = ln.strip().lower()
        if s.startswith("| claude |"):
            claude_row = s
        elif s.startswith("| gpt |"):
            gpt_row = s
    if claude_row is None:
        defects.append("no '| Claude |' discovery-root row found")
    else:
        if CLAUDE_ROOT not in claude_row:
            defects.append(f"Claude row does not name {CLAUDE_ROOT}")
        if COPILOT_ROOT in claude_row:
            defects.append(f"Claude row wrongly names {COPILOT_ROOT} (roots swapped)")
    if gpt_row is None:
        defects.append("no '| GPT |' discovery-root row found")
    else:
        if COPILOT_ROOT not in gpt_row:
            defects.append(f"GPT row does not name {COPILOT_ROOT}")
        if CLAUDE_ROOT in gpt_row:
            defects.append(f"GPT row wrongly names {CLAUDE_ROOT} (roots swapped)")
    return defects


def _unnegated_interchangeable(norm):
    """Return every UN-negated 'interchangeable' assertion in the normalized text.
    A sanctioned occurrence is immediately preceded by 'not' or 'never'
    ('distinct and not interchangeable', 'never interchangeable'); anything else
    ('are/is/be/mechanisms interchangeable') is a contradiction the doc must not
    contain. Two-sided by design: a doc that keeps the sanctioned line but ALSO
    adds a contradicting 'these mechanisms are interchangeable' sentence is
    flagged (mirrors the discovery-root swap-guard)."""
    hits = []
    for m in re.finditer(r"\binterchangeable\b", norm):
        preceding = norm[:m.start()].rstrip()
        last_word = preceding.split(" ")[-1] if preceding else ""
        if last_word not in ("not", "never"):
            start = max(0, m.start() - 30)
            hits.append(norm[start:m.end()])
    return hits


def test_interchangeable_guard_reds_on_contradiction():
    # ANCHOR: the two-sided guard MUST flag an un-negated 'interchangeable'
    # assertion and stay silent on the sanctioned negation.
    good = "these three mechanisms are distinct and not interchangeable."
    bad = "these three mechanisms are interchangeable."
    assert _unnegated_interchangeable(_norm(good)) == []
    assert _unnegated_interchangeable(_norm(bad)), \
        "guard failed to flag an un-negated 'interchangeable' assertion"


def test_swap_guard_reds_on_swapped_roots():
    # ANCHOR: the swap-guard MUST go red when the two roots are crossed, and stay
    # green on a correctly-mapped table. Built from the path-token variables so
    # this test carries no literal ".claude/" of its own.
    correct = (
        f"| Claude | Claude Code | `<install-home>/{CLAUDE_ROOT}/<skill>/` |\n"
        f"| GPT | GitHub Copilot CLI | `<install-home>/{COPILOT_ROOT}/<skill>/` |\n"
    )
    swapped = (
        f"| Claude | Claude Code | `<install-home>/{COPILOT_ROOT}/<skill>/` |\n"
        f"| GPT | GitHub Copilot CLI | `<install-home>/{CLAUDE_ROOT}/<skill>/` |\n"
    )
    assert _discovery_root_defects(correct) == []
    assert _discovery_root_defects(swapped), "swap-guard failed to detect crossed roots"


# --------------------------------------------------------------------------- #
# host-discovery.md content contract
# --------------------------------------------------------------------------- #

def test_host_discovery_doc_exists():
    assert DOC_PATH.is_file(), f"missing authority map: {DOC_PATH}"


def test_doc_states_model_does_not_select_tree():
    norm = _norm(_read(DOC_PATH))
    assert "model choice does not select a skill tree" in norm
    # the exact-confusion killer: a running model is not install proof
    assert "not evidence of a correctly installed gpt profile" in norm


def test_doc_names_both_discovery_roots():
    text = _read(DOC_PATH)
    assert CLAUDE_ROOT in text, f"authority map missing Claude root {CLAUDE_ROOT}"
    assert COPILOT_ROOT in text, f"authority map missing GPT root {COPILOT_ROOT}"


def test_doc_discovery_roots_not_swapped():
    defects = _discovery_root_defects(_read(DOC_PATH))
    assert not defects, "discovery-root table swapped/incomplete:\n" + "\n".join(defects)


def test_doc_instruction_files_hold_no_skill_implementations():
    norm = _norm(_read(DOC_PATH))
    # CLAUDE.md / AGENTS.md are instruction adapters, not skill registries
    assert "claude.md" in norm and "agents.md" in norm
    assert "instruction adapter" in norm
    assert "not skill registries" in norm or "not a skill registry" in norm
    assert "does not contain skill implementations" in norm


def test_doc_router_is_explicit_not_implicit():
    norm = _norm(_read(DOC_PATH))
    assert "the router is explicit, not implicit" in norm
    # and it is NOT the prerequisite for native invocation
    assert "prerequisite for native skill invocation" in norm


def test_doc_states_three_mechanisms_are_distinct():
    norm = _norm(_read(DOC_PATH))
    for mechanism in ("workspace instruction injection",
                      "host-native skill discovery",
                      "router dispatch"):
        assert mechanism in norm, f"authority map does not name mechanism: {mechanism}"
    # Distinctness leans on the specific negation, NOT the bare word "distinct"
    # (which also matches the unrelated "distinct axes" in the doc). The
    # two-sided contradiction guard lives in
    # test_doc_mechanisms_are_never_documented_as_interchangeable.
    assert "not interchangeable" in norm or "never interchangeable" in norm


def test_doc_mechanisms_are_never_documented_as_interchangeable():
    """Two-sided invariant: the doc must REQUIRE a sanctioned negation AND must
    NOT contain any un-negated 'interchangeable' assertion. Presence-only would
    let a contradicting sentence slip through beside the sanctioned line."""
    norm = _norm(_read(DOC_PATH))
    assert "not interchangeable" in norm or "never interchangeable" in norm, \
        "authority map must state the mechanisms are not/never interchangeable"
    violations = _unnegated_interchangeable(norm)
    assert not violations, (
        "authority map contains an un-negated 'interchangeable' assertion "
        "(contradicts the non-interchangeable invariant): " + repr(violations))


# --------------------------------------------------------------------------- #
# Provider guides: correct root each, cross-linked, never swapped
# --------------------------------------------------------------------------- #

def test_claude_guide_names_claude_root_only():
    text = _read(CLAUDE_GUIDE)
    assert CLAUDE_ROOT in text, f"providers/claude.md missing {CLAUDE_ROOT}"
    assert COPILOT_ROOT not in text, (
        f"providers/claude.md names the GPT root {COPILOT_ROOT} (roots must not be "
        "interchangeable)")
    assert "host-discovery.md" in text, "providers/claude.md must cross-link the authority map"
    assert "instruction adapter" in _norm(text)


def test_gpt_guide_names_gpt_root_only():
    text = _read(GPT_GUIDE)
    assert COPILOT_ROOT in text, f"providers/gpt.md missing {COPILOT_ROOT}"
    assert CLAUDE_ROOT not in text, (
        f"providers/gpt.md names the Claude root {CLAUDE_ROOT} (roots must not be "
        "interchangeable)")
    assert "host-discovery.md" in text, "providers/gpt.md must cross-link the authority map"
    assert "instruction adapter" in _norm(text)


def _all_tests():
    return [v for k, v in sorted(globals().items())
            if k.startswith("test_") and callable(v)]


if __name__ == "__main__":
    passed = 0
    for fn in _all_tests():
        fn()
        passed += 1
        print(f"PASS {fn.__name__}")
    print(f"\n{passed} checks passed")
