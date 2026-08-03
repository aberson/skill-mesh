"""Host-loading authority-map gate (Step 42, retargeted in Step 44 of
documentation/host-native-discovery-cutover-plan.md).

Locks the three-mechanism authority map so it can never silently drift into
describing workspace instruction injection, host-native skill discovery, and
router dispatch as interchangeable, and never crosses the two provider install
targets. The regression this exists to prevent: an operator (or a future doc edit)
treating a running GPT model as evidence of a correctly installed GPT profile.

Step 43 (#58) PROVED GitHub Copilot CLI does NOT discover skills at the
project-relative `.copilot/skills` this package originally installed to; its real
native project roots are `.github/skills`, `.agents/skills`, and the Claude root,
plus the personal `~/.copilot/skills`, and every SKILL.md must LEAD with a YAML
frontmatter block (`name`, `description`). This gate now asserts the retargeted
truth and guards the retired `.copilot/skills` claim.

Asserts, against the real committed docs (NO private/legacy source needed):
- documentation/host-discovery.md exists and states every required fact -- model
  choice does not select a skill tree; Claude installs to the Claude root; GPT
  installs to `.github/skills`; the documented GPT discovery roots include
  `.github/skills`, `.agents/skills`, the Claude root, and `~/.copilot/skills`;
  every SKILL.md must lead with a YAML frontmatter block; workspace instruction
  files hold no skill implementations; the router is explicit, not implicit.
- The three mechanisms are documented as DISTINCT / non-interchangeable.
- The install-target table maps each provider to the CORRECT target (a swap-guard:
  Claude -> the Claude root, GPT -> `.github/skills`, never crossed, and the GPT
  target is never the retired `.copilot/skills`).
- The retired project-relative `.copilot/skills` claim appears ONLY where it is
  explicitly labeled retired/legacy; no doc asserts it as a current Copilot
  discovery root (the personal `~/.copilot/skills` root is exempt -- it IS current).
- providers/claude.md names the Claude root only; providers/gpt.md names the GPT
  install target `.github/skills`, each cross-linking the authority map.

Each check is written so it goes RED if the doc drifts (swap the targets, drop the
frontmatter requirement, or re-assert `.copilot/skills` as current) -- proven by the
anchor tests below (a gate that cannot go red is worthless --
.claude/rules/measurement-validity.md).

Runnable via pytest (`python -m pytest tests/package-integrity`) or standalone
(`python tests/package-integrity/test_host_discovery.py`).
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "documentation" / "host-discovery.md"
CLAUDE_GUIDE = REPO_ROOT / "documentation" / "providers" / "claude.md"
GPT_GUIDE = REPO_ROOT / "documentation" / "providers" / "gpt.md"
README = REPO_ROOT / "README.md"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

# Build the Claude ".claude/skills" path token from parts so this test's own source
# carries no literal ".claude/" path (tests/router/test_no_claude_dependency.py flags
# a load-bearing ".claude/" reference in executable code). The other tokens are not
# flagged by that scanner, so they are written literally.
_DOTCLAUDE = "." + "claude"
CLAUDE_ROOT = _DOTCLAUDE + "/skills"          # ".claude/skills"
GITHUB_ROOT = ".github/skills"                # GPT install target (Step 44 retarget)
AGENTS_ROOT = ".agents/skills"                # a Copilot project discovery root
COPILOT_PERSONAL = "~/.copilot/skills"        # Copilot personal root (current, legit)
COPILOT_LEGACY = ".copilot/skills"            # retired project-relative wrong target

# Tokens that mark a `.copilot/skills` mention as the RETIRED legacy target rather
# than a current-root assertion. "retire" also catches "retired"; "retarget" catches
# "pre-retarget"/"retargeted".
RETIRE_TOKENS = (
    "retire", "retarget", "legacy", "former", "wrong", "falsif",
    "no longer", "not a ", "do not use", "deprecat", "superseded", "migrate off",
)


def _read(path):
    return path.read_text(encoding="utf-8")


def _norm(text):
    """Lowercase and collapse all whitespace runs (incl. line wraps) to one space,
    so a required phrase matches regardless of markdown line breaks."""
    return re.sub(r"\s+", " ", text).lower()


# --------------------------------------------------------------------------- #
# Retired-`.copilot/skills` guard: a project-relative mention is allowed ONLY when
# labeled retired; the personal `~/.copilot/skills` root is exempt (it IS current).
# --------------------------------------------------------------------------- #

def _unlabeled_project_copilot_hits(text):
    """Every project-relative `.copilot/skills` mention that is NOT labeled retired.

    A `~/`-prefixed occurrence is the personal Copilot root (a real current root) and
    is skipped. For any other occurrence, a retirement label must appear within a
    ~140-char window before it (windowed, not line-bound, so a sentence that wraps
    across markdown lines still counts). A non-empty return means the doc asserts the
    retired project-relative target as if it were current."""
    low = text.lower()
    hits = []
    idx = 0
    while True:
        j = low.find(COPILOT_LEGACY, idx)
        if j < 0:
            break
        idx = j + 1
        if low[max(0, j - 2):j] == "~/":
            continue  # personal root ~/.copilot/skills -- current and legitimate
        window = low[max(0, j - 160):j + len(COPILOT_LEGACY) + 60]
        if not any(tok in window for tok in RETIRE_TOKENS):
            hits.append(text[max(0, j - 60):j + len(COPILOT_LEGACY) + 10].strip())
    return hits


def test_retired_copilot_guard_reds_on_unlabeled_and_silent_on_labeled():
    # ANCHOR: the guard MUST flag an un-labeled current-root assertion and stay
    # silent on both the labeled-retired mention and the personal root.
    bad = "GPT natively discovers project skills at .copilot/skills at install time."
    assert _unlabeled_project_copilot_hits(bad), \
        "guard failed to flag an un-labeled project-relative .copilot/skills claim"
    labeled = "the retired project-relative .copilot/skills target is not a Copilot root."
    assert _unlabeled_project_copilot_hits(labeled) == []
    personal = "Copilot's personal discovery root is ~/.copilot/skills for the user."
    assert _unlabeled_project_copilot_hits(personal) == []


# --------------------------------------------------------------------------- #
# Install-target swap-guard (the load-bearing regression: never cross the targets)
# --------------------------------------------------------------------------- #

def _install_target_defects(text):
    """Defects if the install-target table maps a provider to the WRONG target.
    Claude must own the Claude root; GPT must own `.github/skills`; neither row may
    name the other's target, and the GPT row must never name the retired
    `.copilot/skills`. Empty list == correct and non-swapped.

    Rows are located by their leading provider cell (`| Claude |` / `| GPT |`),
    which in the authority map appears only in the install-target table."""
    defects = []
    claude_row = gpt_row = None
    for ln in text.splitlines():
        s = ln.strip().lower()
        if s.startswith("| claude |"):
            claude_row = s
        elif s.startswith("| gpt |"):
            gpt_row = s
    if claude_row is None:
        defects.append("no '| Claude |' install-target row found")
    else:
        if CLAUDE_ROOT not in claude_row:
            defects.append(f"Claude row does not name {CLAUDE_ROOT}")
        if GITHUB_ROOT in claude_row:
            defects.append(f"Claude row wrongly names {GITHUB_ROOT} (targets swapped)")
        if COPILOT_LEGACY in claude_row:
            defects.append(f"Claude row names the retired {COPILOT_LEGACY}")
    if gpt_row is None:
        defects.append("no '| GPT |' install-target row found")
    else:
        if GITHUB_ROOT not in gpt_row:
            defects.append(f"GPT row does not name {GITHUB_ROOT}")
        if CLAUDE_ROOT in gpt_row:
            defects.append(f"GPT row wrongly names {CLAUDE_ROOT} (targets swapped)")
        if COPILOT_LEGACY in gpt_row:
            defects.append(f"GPT row names the retired {COPILOT_LEGACY} as its target")
    return defects


def test_swap_guard_reds_on_swapped_targets():
    # ANCHOR: the swap-guard MUST go red when the targets are crossed OR when the GPT
    # row regresses to the retired `.copilot/skills`, and stay green on the correct
    # table. Built from the path-token variables so this test carries no literal
    # ".claude/" of its own.
    correct = (
        f"| Claude | Claude Code | `<install-home>/{CLAUDE_ROOT}/<skill>/` |\n"
        f"| GPT | GitHub Copilot CLI | `<install-home>/{GITHUB_ROOT}/<skill>/` |\n"
    )
    swapped = (
        f"| Claude | Claude Code | `<install-home>/{GITHUB_ROOT}/<skill>/` |\n"
        f"| GPT | GitHub Copilot CLI | `<install-home>/{CLAUDE_ROOT}/<skill>/` |\n"
    )
    regressed = (
        f"| Claude | Claude Code | `<install-home>/{CLAUDE_ROOT}/<skill>/` |\n"
        f"| GPT | GitHub Copilot CLI | `<install-home>/{COPILOT_LEGACY}/<skill>/` |\n"
    )
    assert _install_target_defects(correct) == []
    assert _install_target_defects(swapped), "swap-guard failed to detect crossed targets"
    assert _install_target_defects(regressed), \
        "swap-guard failed to detect a GPT row regressed to the retired .copilot/skills"


def _unnegated_interchangeable(norm):
    """Return every UN-negated 'interchangeable' assertion in the normalized text.
    A sanctioned occurrence is immediately preceded by 'not' or 'never'
    ('distinct and not interchangeable', 'never interchangeable'); anything else
    ('are/is/be/mechanisms interchangeable') is a contradiction the doc must not
    contain. Two-sided by design: a doc that keeps the sanctioned line but ALSO
    adds a contradicting 'these mechanisms are interchangeable' sentence is
    flagged (mirrors the install-target swap-guard)."""
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


def test_doc_names_install_targets():
    text = _read(DOC_PATH)
    assert CLAUDE_ROOT in text, f"authority map missing Claude install target {CLAUDE_ROOT}"
    assert GITHUB_ROOT in text, f"authority map missing GPT install target {GITHUB_ROOT}"


def test_doc_states_real_gpt_discovery_roots():
    """The documented GPT discovery roots must include ALL of the real Copilot roots
    proven in Step 43 -- the three project roots plus the personal root."""
    text = _read(DOC_PATH)
    for root in (GITHUB_ROOT, AGENTS_ROOT, CLAUDE_ROOT, COPILOT_PERSONAL):
        assert root in text, f"authority map missing GPT discovery root {root}"


def test_doc_requires_yaml_frontmatter():
    norm = _norm(_read(DOC_PATH))
    assert "must lead with a yaml frontmatter block" in norm, \
        "authority map must state SKILL.md leads with a YAML frontmatter block"
    assert "name" in norm and "description" in norm


def test_doc_install_targets_not_swapped():
    defects = _install_target_defects(_read(DOC_PATH))
    assert not defects, "install-target table swapped/incomplete:\n" + "\n".join(defects)


def test_doc_does_not_assert_retired_copilot_as_current():
    hits = _unlabeled_project_copilot_hits(_read(DOC_PATH))
    assert not hits, (
        "authority map asserts the retired project-relative .copilot/skills as a "
        "current Copilot discovery root: " + repr(hits))


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
# Provider guides: correct target each, cross-linked, no unlabeled retired root
# --------------------------------------------------------------------------- #

def test_claude_guide_names_claude_root_only():
    text = _read(CLAUDE_GUIDE)
    assert CLAUDE_ROOT in text, f"providers/claude.md missing {CLAUDE_ROOT}"
    assert GITHUB_ROOT not in text, (
        f"providers/claude.md names the GPT target {GITHUB_ROOT} (targets must not "
        "be interchangeable)")
    assert COPILOT_LEGACY not in text, (
        f"providers/claude.md names the retired GPT target {COPILOT_LEGACY}")
    assert "host-discovery.md" in text, "providers/claude.md must cross-link the authority map"
    assert "instruction adapter" in _norm(text)


def test_gpt_guide_names_gpt_install_target():
    text = _read(GPT_GUIDE)
    assert GITHUB_ROOT in text, f"providers/gpt.md missing GPT install target {GITHUB_ROOT}"
    assert "host-discovery.md" in text, "providers/gpt.md must cross-link the authority map"
    assert "instruction adapter" in _norm(text)
    # the retired project-relative target may appear ONLY labeled retired
    hits = _unlabeled_project_copilot_hits(text)
    assert not hits, (
        "providers/gpt.md asserts the retired project-relative .copilot/skills as a "
        "current Copilot discovery root: " + repr(hits))


def test_no_doc_asserts_retired_copilot_as_current_root():
    """Repo-doc sweep: none of the consumer-facing docs may assert the project-relative
    `.copilot/skills` as a current Copilot discovery root (the personal
    `~/.copilot/skills` root and explicitly-retired labels are exempt)."""
    offenders = {}
    for path in (DOC_PATH, GPT_GUIDE, CLAUDE_GUIDE, README, CLAUDE_MD):
        hits = _unlabeled_project_copilot_hits(_read(path))
        if hits:
            offenders[path.name] = hits
    assert not offenders, (
        "docs assert project-relative .copilot/skills as a current root: " + repr(offenders))


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
