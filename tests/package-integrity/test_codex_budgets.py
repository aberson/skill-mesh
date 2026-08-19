"""Codex metadata/catalog budget gates (Phase CP Step 3, issue #120).

Codex publishes two DIFFERENT limits, and conflating them is the whole reason this
module exists. From documentation/native-claude-codex-skill-parity-plan.md:175-181,
carried forward as documentation/codex-parity-delivery-plan.md:60-62:

  1. PER-SKILL CAP -- 7,500 UTF-8 characters. "The exact production serialization of
     Skill Mesh name, description, and source metadata must be at most 7,500 UTF-8
     characters as a conservative PROJECT cap, not as claimed reserved headroom." It is
     a self-imposed ceiling on one skill's metadata, and it is generous: nothing in the
     catalog is remotely near it today. Its job is to catch a future skill whose
     description grows into an essay.

  2. WHOLE-CATALOG INITIAL-LIST BUDGET -- "at most 2% of the selected model's context,
     or 8,000 characters only when the context size is UNKNOWN", and it "applies to the
     whole effective catalog, INCLUDING PATHS". This is the host's limit, not ours, and
     8,000 is the pessimistic floor: the number that applies when Codex cannot size the
     model's context. Exceeding it risks skills being silently omitted or truncated from
     the initial list -- a skill the operator cannot select is a skill that does not
     exist, and no test of the emitted bytes would notice.

The two are not comparable per-skill: 7,500 is a cap on ONE skill while 8,000 caps the
SUM over ~47-54 of them, so the catalog budget is the binding constraint by roughly two
orders of magnitude. A reader who assumes the per-skill cap implies catalog headroom has
it exactly backwards.

WHY THIS MEASURES THE PORTABLE CATALOG AND NOT THE CODEX RECORDS
---------------------------------------------------------------
At Step 3 there are ZERO authored codex adapters, and at Step 4 there are five of a
projected 47 (the rails ship first; Step 4 adds the pilot five, Steps 6-8 the cohorts --
Step 6's Cohort B raised the authored roster to seventeen, Step 7's Cohort C to
thirty-three, and Step 8's Cohort D closed it at the full 47). Summing over the codex
records would therefore have measured 0 characters -- and after Step 4 still only about
a tenth of the catalog -- against an 8,000 floor, and report a comfortable PASS that
means nothing: a vacuous gate on the exact axis the plan flags as a live risk
("Initial-list budget (8,000 chars) with 47-54 skills | Catalog could truncate in
Codex's skill list", codex-parity-delivery-plan.md:719).

So the estimate is taken over the CODEX-ELIGIBLE catalog: the portable skills, which is
precisely the set the cohort steps authored codex adapters for. That made the gate
meaningful from Step 3 onward -- the plan's own words, "budget tests from Step 3 onward
estimate serialization" -- and it makes the number MOVE when a description is edited,
which is what turns it into an early warning rather than a formality. Since Step 8 the
eligible and authored rosters COINCIDE at 47, so the same sum is now also a measurement
of the real catalog a Codex host serializes; the basis stays eligibility-by-status
regardless (see test_catalog_estimate_basis_is_eligibility_not_the_authored_roster).

WHAT THIS GATE CANNOT DECIDE
----------------------------
It is an ESTIMATE of a host-internal serialization, not a measurement of one. Codex's
exact framing (separators, quoting, whether it lists paths verbatim) is not published,
so this module measures the CONTENT the repository controls -- name + description +
install path per skill -- and deliberately adds no invented per-row framing overhead,
which would be this repository's guess masquerading as a budget. Real-host confirmation
that nothing truncates is M1/M2's job (D-CP7 re-verifies format assumptions against the
INSTALLED Codex CLI); this gate's job is to fail in CI long before an operator gets
there, and to keep failing until a description is trimmed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"

# The two published limits. Spelled here as the single source for this module, with the
# provenance in the docstring above.
PER_SKILL_CAP = 7_500
CATALOG_FLOOR = 8_000

DISCOVERY_SCRIPT = REPO_ROOT / "tools" / "skill-mesh-discovery.ps1"


def _discovery_root(provider):
    """Read one provider's discovery root from its SOLE owner.

    Phase CP Step 5 added the `codex` entry to
    tools/skill-mesh-discovery.ps1's `Get-SkillMeshDiscoveryRoots`, so this module no
    longer spells the path: it derives it, exactly as Step 3's parked comment
    instructed ("when Step 5 adds the real map entry, this should read from it
    instead"). A budget measured against a path this module invented would stop being
    a budget the moment the real root changed.

    Parsed rather than executed on purpose -- this suite is hermetic Python and must
    not need powershell on PATH to state a number. The map is a literal hashtable, so
    the parse is exact, and it fails LOUDLY (assert) rather than falling back to a
    guess, because a silent fallback is how a budget starts measuring nothing.
    """
    text = DISCOVERY_SCRIPT.read_text(encoding="utf-8")
    body = re.search(r"function Get-SkillMeshDiscoveryRoots\b.*?\n}", text, re.S)
    assert body, "Get-SkillMeshDiscoveryRoots not found in the discovery-root owner"
    m = re.search(r"^\s*'" + re.escape(provider) + r"'\s*=\s*'([^']+)'\s*$",
                  body.group(0), re.M)
    assert m, f"the discovery-root owner declares no root for {provider!r}"
    return m.group(1)


# Where a Codex skill package lands in a consumer home, home-relative and POSIX-form.
# This is a BUDGET input -- the path shape whose characters count against the catalog
# floor -- not an install target, and nothing in this module installs anything. It is
# DERIVED from the map so the two can never disagree about how many characters a codex
# package path costs.
CODEX_SKILL_ROOT = _discovery_root("codex")


def _load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _codex_eligible_records(manifest=None):
    """The skill records that carry a codex adapter: the portable ones.

    Provider-native skills are Claude-only and are excluded from dist/codex by the
    builder, so they never appear in a Codex catalog and must not be charged against
    its budget.

    The membership predicate is ELIGIBILITY (`status == "portable"`), deliberately NOT
    `"codex" in providers`. Since Step 8 the two select the same 47 records from the
    committed manifest, so no assertion over real records can tell them apart any more
    -- which is exactly why `manifest` is a parameter: the basis-pinning test feeds a
    synthetic manifest where the two predicates disagree and proves this function
    follows eligibility.
    """
    if manifest is None:
        manifest = _load_manifest()
    return [s for s in manifest["skills"] if s["status"] == "portable"]


def _skill_metadata_serialization(name, description):
    """The per-skill metadata whose size both budgets are measured over.

    "name, description, and source metadata" per the research doc. `source metadata` is
    the skill's own install path, which is why the catalog budget is documented as
    applying "including paths".
    """
    return f"{name}{description}{CODEX_SKILL_ROOT}/{name}/SKILL.md"


def _utf8_len(s):
    """UTF-8 CHARACTER cost as the budget counts it -- encoded byte length.

    The cap is stated in "UTF-8 characters", and for the ASCII-only catalog this
    repository commits those two readings are identical. Byte length is the
    conservative one of the two if a non-ASCII character ever lands, so it is what this
    module measures: a gate should not go quiet the moment content gets harder.
    """
    return len(s.encode("utf-8"))


# --------------------------------------------------------------------------- #
# Per-skill cap
# --------------------------------------------------------------------------- #

def test_every_skill_metadata_serialization_is_under_the_per_skill_cap():
    """No single skill's metadata may exceed the 7,500-char project cap."""
    offenders = []
    for s in _codex_eligible_records():
        size = _utf8_len(_skill_metadata_serialization(s["name"], s["description"]))
        if size > PER_SKILL_CAP:
            offenders.append(f"{s['name']}: {size} > {PER_SKILL_CAP}")
    assert not offenders, (
        "per-skill Codex metadata cap exceeded (trim the manifest description, which "
        "is authored in tools/gen_manifest.py's DESCRIPTIONS and regenerated into "
        "config/skill-manifest.json):\n  " + "\n  ".join(offenders))


def test_per_skill_cap_reds_on_an_oversized_description():
    """Red-on-garbage anchor for the per-skill cap.

    Without this, a cap set absurdly high (or a comparison written backwards) would
    still report PASS on every real skill, because the real catalog's worst case is
    ~2% of the cap. The anchor proves the check can actually say no.
    """
    huge = "x" * (PER_SKILL_CAP + 1)
    assert _utf8_len(_skill_metadata_serialization("demo", huge)) > PER_SKILL_CAP


# --------------------------------------------------------------------------- #
# Whole-catalog initial list
# --------------------------------------------------------------------------- #

def _catalog_estimate():
    """(total_chars, per_skill_sizes) over the codex-eligible catalog."""
    sizes = {s["name"]: _utf8_len(
        _skill_metadata_serialization(s["name"], s["description"]))
        for s in _codex_eligible_records()}
    return sum(sizes.values()), sizes


def _fits_under_floor(total_bytes):
    """The ONE predicate the catalog-floor gate and its anchor both exercise.

    Factored out so an anchor can prove the gate is falsifiable without re-implementing
    its comparison: a separate inline `<` at the anchor site would not go red if this
    operator were inverted or broken, which is precisely what happened before this fix
    (a tautology at the anchor that could never fail regardless of the real catalog
    size). Both `test_whole_catalog_initial_list_estimate_is_under_the_unknown_context_floor`
    and `test_catalog_floor_reds_when_the_catalog_grows_past_it` call this function, so
    inverting it reds both tests together.
    """
    return total_bytes < CATALOG_FLOOR


def test_whole_catalog_initial_list_estimate_is_under_the_unknown_context_floor():
    """The binding constraint: the WHOLE eligible catalog must fit in 8,000 chars.

    This is the gate that is genuinely close to its limit, and it is meant to be --
    Phase CP's risk register names catalog truncation as a live risk and names the
    remedy ("worst case: trim descriptions -- they're authored, not derived"). The
    failure message therefore reports the overage and points at the one file where
    descriptions are authored, so a red here is directly actionable instead of merely
    alarming.
    """
    total, sizes = _catalog_estimate()
    assert sizes, "no codex-eligible skills found -- this gate would be vacuous"
    # Since Step 8 (Cohort D) the initial list IS the whole portable catalog: the full
    # 47-name roster, every name backed by an authored codex adapter, serializes under
    # the floor with no name dropped. Both halves are asserted -- the count AND the
    # exact name set against the manifest's own portable roster -- so a record silently
    # falling out of the estimate can never make the floor easier to fit.
    portable_names = {s["name"] for s in _load_manifest()["skills"]
                      if s["status"] == "portable"}
    assert len(sizes) == 47
    assert set(sizes) == portable_names
    assert _fits_under_floor(total), (
        f"Codex initial-list estimate {total} chars over {len(sizes)} skills exceeds "
        f"the {CATALOG_FLOOR}-char unknown-context floor by {total - CATALOG_FLOOR}. "
        "Codex may silently omit or truncate skills from its initial list, and an "
        "unlistable skill is unselectable. Trim the longest descriptions in "
        "tools/gen_manifest.py's DESCRIPTIONS and re-run `python tools/gen_manifest.py`. "
        f"Longest entries: "
        + ", ".join(f"{n}={sz}" for n, sz in
                    sorted(sizes.items(), key=lambda kv: -kv[1])[:5]))


def test_catalog_estimate_basis_is_eligibility_not_the_authored_roster():
    """The anti-vacuity guard, re-pinned for the post-Step-8 catalog.

    Through Step 7 this test proved the basis was ELIGIBILITY by arithmetic on the real
    manifest: the authored roster was a proper subset of the eligible one, so measuring
    the wrong basis under-reported the estimate visibly. Step 8's Cohort D made the two
    rosters coincide at 47, which is the situation the old assertion's own message
    anticipated ("at that point pin the basis another way rather than dropping it") --
    no arithmetic over real records can separate the predicates any more.

    So the basis is pinned on a SYNTHETIC manifest where the predicates disagree: one
    portable record with no authored codex adapter (legal: portability precedes
    authoring for any future skill) and one provider-native record carrying neither.
    Eligibility must include the not-yet-authored portable record -- a rewrite of
    `_codex_eligible_records` to filter on `"codex" in providers` drops it and reds
    here -- and must still exclude the native record, whose absence from dist/codex is
    the builder's contract.
    """
    manifest = _load_manifest()
    eligible = {s["name"] for s in _codex_eligible_records()}
    portable = {s["name"] for s in manifest["skills"] if s["status"] == "portable"}
    assert eligible == portable
    assert len(eligible) == manifest["counts"]["portable"] == 47
    # Since Step 8 every eligible record is also authored -- the pass-2 exit fact --
    # and the coincidence is asserted so a dropped adapter cannot hide behind it.
    authored = {s["name"] for s in manifest["skills"] if "codex" in s["providers"]}
    assert authored == eligible
    assert len(authored) == manifest["counts"]["codex"] == 47
    # The synthetic-manifest pin: predicates disagree, eligibility must win.
    synthetic = {"skills": [
        {"name": "future-portable", "status": "portable", "description": "d",
         "providers": {"claude": "x", "gpt": "y"}},
        {"name": "native-only", "status": "provider-native", "description": "d",
         "providers": {"claude": "x"}},
    ]}
    basis = {s["name"] for s in _codex_eligible_records(synthetic)}
    assert basis == {"future-portable"}, (
        "the estimate's membership predicate drifted off eligibility "
        f"(status == portable): got {sorted(basis)}")
    total, sizes = _catalog_estimate()
    assert len(sizes) == 47
    assert total > 0


def test_catalog_floor_reds_when_the_catalog_grows_past_it():
    """Red-on-garbage anchor for the catalog floor, and a documented early warning.

    The headroom is genuinely thin, so this anchor does double duty: it proves the
    comparison can fail, and it records WHY the promoted-skill step has to re-measure.
    Phase CP Step 10 promotes 7 more skills into the catalog; scaling the current
    estimate to 54 skills is what shows that step it will need description trims rather
    than discovering it on a real host.

    The anchor calls the SAME `_fits_under_floor` helper the real gate
    (`test_whole_catalog_initial_list_estimate_is_under_the_unknown_context_floor`)
    calls, and asserts BOTH directions against it: the measured catalog must fit, and a
    catalog deliberately blown out by two floors' worth of extra content must not. A
    separately re-implemented comparison here would not notice if the real gate's
    operator were inverted or broken -- which is exactly the failure mode this anchor
    exists to catch.
    """
    total, sizes = _catalog_estimate()
    per_skill_mean = total / len(sizes)
    # The anchor: the measured catalog fits, and one deliberately two floors past the
    # cap does not. Same predicate as the real gate, both directions.
    assert _fits_under_floor(total) is True
    assert _fits_under_floor(total + CATALOG_FLOOR * 2) is False
    # The early warning, asserted as arithmetic rather than left in a comment so it
    # cannot rot: at the post-Step-10 catalog size of 54, today's mean row size
    # exceeds the floor. This is a FACT about the current descriptions, not a
    # prediction, and Step 10 owns the trim.
    projected_54 = per_skill_mean * 54
    assert projected_54 > CATALOG_FLOOR, (
        "the 54-skill projection now FITS under the floor -- if descriptions were "
        "trimmed, update this assertion and Phase CP Step 10's expectations together")


# Cohort B, the pipeline family (Phase CP Step 6, issue #123). SPELLED here -- like the
# distributions suite's cohort rosters -- so "the budget holds over the enlarged
# catalog" grades the step's actual roster rather than whatever the manifest happens to
# declare.
STEP6_COHORT_B = [
    "plan-expedite", "plan-feature", "plan-init", "plan-merge", "plan-redline",
    "plan-trim", "plan-wrap", "repo-init", "repo-sync", "repo-update",
    "user-project", "user-wrap",
]


def test_step6_cohort_is_authored_and_every_authored_record_fits_the_per_skill_cap():
    """Phase CP Step 6 extends the AUTHORED roster; the budget must hold over it.

    The catalog-floor gate above already measures the full ELIGIBLE catalog (all 47
    portable skills), so enlarging the authored set moves no estimate -- that is the
    projected-catalog design working as intended. What Step 6 adds is worth pinning
    separately: the twelve Cohort B adapters are really declared (a codex.md on disk
    without its manifest entry ships nothing), the authored tally agrees with the
    manifest's own count, and every AUTHORED record -- the rows a real Codex host will
    actually serialize today -- fits the per-skill cap individually.
    """
    manifest = _load_manifest()
    authored = {s["name"]: s for s in manifest["skills"] if "codex" in s["providers"]}
    missing = [n for n in STEP6_COHORT_B if n not in authored]
    assert not missing, f"Step 6 cohort skills missing a manifest codex entry: {missing}"
    # 47 = the Step 4 pilot five + Cohort B's twelve + Cohort C's sixteen (Step 7,
    # issue #124) + Cohort D's fourteen (Step 8, issue #125) -- the full portable
    # catalog. Spelled, so any step that grows the roster must come here and state
    # its new number.
    assert len(authored) == manifest["counts"]["codex"] == 47
    offenders = []
    for name, rec in authored.items():
        size = _utf8_len(_skill_metadata_serialization(name, rec["description"]))
        if size > PER_SKILL_CAP:
            offenders.append(f"{name}: {size} > {PER_SKILL_CAP}")
    assert not offenders, (
        "an authored codex record exceeds the per-skill metadata cap:\n  "
        + "\n  ".join(offenders))


# Cohort C, the build/review/skill/tier families (Phase CP Step 7, issue #124) -- the
# heaviest host-abstraction consumers. SPELLED for the same reason as Cohort B above:
# the cohort sweep must grade the step's actual roster, not whatever the manifest
# happens to declare.
STEP7_COHORT_C = [
    "build-phase", "build-queue", "build-step", "goblin-do", "goblin-suggest",
    "judge-ui", "review-deep", "review-gauntlet", "review-proof", "review-uat",
    "skill-eval-setup", "skill-evolve", "skill-iterate", "test-prune",
    "tier-escalate", "tier-offload",
]


def test_step7_cohort_is_authored_and_every_authored_record_fits_the_per_skill_cap():
    """Phase CP Step 7 extends the AUTHORED roster; the budget must hold over it.

    Same design as the Step 6 sweep above (which also owns the spelled total): the
    catalog-floor gate already measures the full ELIGIBLE catalog, so what this pins is
    that the sixteen Cohort C adapters are really DECLARED (a codex.md on disk without
    its manifest entry ships nothing), that the two cohorts do not overlap, and that
    every authored record -- the rows a real Codex host will actually serialize today
    -- fits the per-skill cap individually.
    """
    manifest = _load_manifest()
    authored = {s["name"]: s for s in manifest["skills"] if "codex" in s["providers"]}
    missing = [n for n in STEP7_COHORT_C if n not in authored]
    assert not missing, f"Step 7 cohort skills missing a manifest codex entry: {missing}"
    # The cohorts are disjoint rosters; a name spelled in both would double-count the
    # step's contribution and hide a dropped adapter behind the shared total.
    assert not set(STEP7_COHORT_C) & set(STEP6_COHORT_B)
    offenders = []
    for name, rec in authored.items():
        size = _utf8_len(_skill_metadata_serialization(name, rec["description"]))
        if size > PER_SKILL_CAP:
            offenders.append(f"{name}: {size} > {PER_SKILL_CAP}")
    assert not offenders, (
        "an authored codex record exceeds the per-skill metadata cap:\n  "
        + "\n  ".join(offenders))


# Cohort D, the remainder of the portable catalog (Phase CP Step 8, issue #125) --
# memory-distill, observatory-doctor, research-prospect, and the user-* conversational
# family. SPELLED for the same reason as the two cohorts above: the sweep must grade
# the step's actual roster, not whatever the manifest happens to declare.
STEP8_COHORT_D = [
    "memory-distill", "observatory-doctor", "research-prospect",
    "user-afterparty", "user-brainstorm", "user-debug", "user-draft",
    "user-gateway", "user-lavishify", "user-learn", "user-pm",
    "user-shakedown", "user-uat", "user-walkthrough",
]


def test_step8_cohort_is_authored_and_the_catalog_is_closed():
    """Phase CP Step 8 closes the authored roster at the portable catalog.

    Same design as the two cohort sweeps above (the Step 6 sweep owns the spelled
    total): the fourteen Cohort D adapters are really DECLARED (a codex.md on disk
    without its manifest entry ships nothing), the three cohort rosters plus the pilot
    are pairwise disjoint and together ARE the authored set exactly -- no stray
    fifteenth adapter rode in with the cohort -- and every authored record fits the
    per-skill cap individually.
    """
    manifest = _load_manifest()
    authored = {s["name"]: s for s in manifest["skills"] if "codex" in s["providers"]}
    missing = [n for n in STEP8_COHORT_D if n not in authored]
    assert not missing, f"Step 8 cohort skills missing a manifest codex entry: {missing}"
    assert not set(STEP8_COHORT_D) & set(STEP6_COHORT_B)
    assert not set(STEP8_COHORT_D) & set(STEP7_COHORT_C)
    # The pilot five are the only authored names no cohort list spells; naming them
    # here makes the partition exact instead of merely disjoint.
    pilot = {"lesson-harvest", "plan-review", "session-wrap", "task-handoff",
             "user-orient"}
    assert not pilot & set(STEP6_COHORT_B + STEP7_COHORT_C + STEP8_COHORT_D)
    assert set(authored) == pilot | set(STEP6_COHORT_B) | set(STEP7_COHORT_C) \
        | set(STEP8_COHORT_D)
    offenders = []
    for name, rec in authored.items():
        size = _utf8_len(_skill_metadata_serialization(name, rec["description"]))
        if size > PER_SKILL_CAP:
            offenders.append(f"{name}: {size} > {PER_SKILL_CAP}")
    assert not offenders, (
        "an authored codex record exceeds the per-skill metadata cap:\n  "
        + "\n  ".join(offenders))


def test_codex_install_path_shape_is_pinned():
    """The path shape charged against the catalog budget.

    Pinned because path characters are explicitly inside Codex's budget, so a change
    from `.agents/skills` to a longer root silently consumes headroom the catalog test
    is already close to spending.

    Since Phase CP Step 5 this is the CROSS-CHECK Step 3's comment promised: the
    constant is derived from tools/skill-mesh-discovery.ps1 (the sole owner), and the
    spelled value below is the second, independent statement of the same fact. They
    are allowed to disagree only by someone editing both -- which is exactly the
    visible, deliberate act a budget change should require.
    """
    assert CODEX_SKILL_ROOT == ".agents/skills"
    assert not CODEX_SKILL_ROOT.startswith("/")
    assert "\\" not in CODEX_SKILL_ROOT, "home-relative POSIX form, per the map's contract"
    # The derivation is live: the owner really does declare the other two roots too,
    # so a parser that silently matched nothing would fail here rather than pass by
    # returning the value this test happens to expect.
    assert _discovery_root("claude") == ".claude/skills"
    assert _discovery_root("gpt") == ".github/skills"


@pytest.mark.parametrize("name,expected_substrings", [
    ("plan-review", ["plan-review", ".agents/skills/plan-review/SKILL.md"]),
    # A Cohort B row (Phase CP Step 6), so the serialization contract is exercised
    # against the enlarged catalog and not only the pilot.
    ("repo-sync", ["repo-sync", ".agents/skills/repo-sync/SKILL.md"]),
    # A Cohort C row (Phase CP Step 7), same rationale one cohort later.
    ("build-step", ["build-step", ".agents/skills/build-step/SKILL.md"]),
    # A Cohort D row (Phase CP Step 8), closing the catalog at all 47.
    ("user-debug", ["user-debug", ".agents/skills/user-debug/SKILL.md"]),
])
def test_serialization_includes_name_description_and_path(name, expected_substrings):
    """The serialization must actually contain all three metered fields.

    A model that quietly dropped the path would under-report the catalog estimate by
    ~1,700 chars across 47 skills -- more than the entire remaining headroom -- and
    would turn a red gate green without anyone editing a description.
    """
    rec = next(s for s in _codex_eligible_records() if s["name"] == name)
    serialized = _skill_metadata_serialization(rec["name"], rec["description"])
    for sub in expected_substrings:
        assert sub in serialized
    assert rec["description"] in serialized
