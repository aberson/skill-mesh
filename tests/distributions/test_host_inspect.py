"""Read-only host-install inspection gate (Step 46).

Exercises tools/inspect-host-install.ps1 END-TO-END against consumer-home shapes
built by legacy_install_fixtures. Every assertion runs the ACTUAL PowerShell
inspector via subprocess (never a Python re-implementation of the classification
logic).

The shapes are SYNTHESIZED at test time, not committed. A committed fixture
`SKILL.md` sitting at `.claude/skills/<name>/` is a real, host-discoverable skill --
Claude Code discovers skills from nested `.claude/skills/` directories anywhere in a
tree -- so the previous committed tree published phantom `build-phase`,
`build-step`, `context-slim`, `build-observer`, and `goblin-sweep` skills to anyone
working in this repository (#86).

Guarantees proven here:
  - each shape produces a STABLE manifest-driven classification;
  - the inspector is READ-ONLY (the tree hashes identically before/after);
  - default output is consumer-home-RELATIVE; -AbsolutePaths switches to absolute;
  - instruction evidence is never claimed as `observed` (plan section 7);
  - every emitted scalar stays inside its declared vocabulary or bounded shape,
    on stdout AND stderr, even against a deliberately hostile home.

Style matches tests/distributions/test_distributions.py: shell out to
powershell.exe, use tmp_path, and skipif when powershell is not on PATH.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import legacy_install_fixtures as fx

PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
INSPECT_SCRIPT = REPO_ROOT / "tools" / "inspect-host-install.ps1"
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")

# Shapes built directly by the synthesizer. The two junction shapes need a second
# directory outside the home, so they are assembled here on top of a base shape.
SYNTHESIZED = fx.SHAPES
JUNCTION_SHAPES = ["05-junction", "18-junction-external"]
ALL_SHAPES = SYNTHESIZED + JUNCTION_SHAPES

FILE_ATTRIBUTE_REPARSE_POINT = 0x400

# The closed vocabularies the report may draw from.
PROVIDER_SLUGS = set(json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["providers"])
ELIGIBILITY = {"managed", "consumer-only", "core-holder", "foreign"}
EVIDENCE_CLASSES = {"host-convention", "unknown"}
LINK_TYPES = {"directory", "junction", "symlink", "reparse", "absent"}
LEDGER_STATES = {"absent", "valid", "corrupt"}
ROUTER_CLASSES = {"canonical", "legacy", "absent"}

# A bounded display name: the skill-name charset, capped, with an optional
# truncation marker. `<unnamed>` is the empty-name sentinel.
SAFE_NAME_RE = re.compile(r"\A(<unnamed>|[A-Za-z0-9._-]{1,64}~?)\Z")
DRIVE_ABS_RE = re.compile(r"[A-Za-z]:[\\/]")


# --------------------------------------------------------------------------- #
# Inspector invocation
# --------------------------------------------------------------------------- #

def _run_inspect(home, fmt="json", absolute=False):
    args = [PWSH, "-NonInteractive", "-File", str(INSPECT_SCRIPT),
            "-Home", str(home), "-Format", fmt]
    if absolute:
        args.append("-AbsolutePaths")
    return subprocess.run(args, capture_output=True, text=True)


def _inspect_json(home, absolute=False):
    r = _run_inspect(home, fmt="json", absolute=absolute)
    assert r.returncode == 0, f"inspect failed:\n{r.stdout}\n{r.stderr}"
    return json.loads(r.stdout)


def _codes(d):
    return {w["code"] for w in d["warnings"]}


def _skill(prof, name):
    for s in prof["skills"]:
        if s["name"] == name:
            return s
    return None


def _all_profiles(d):
    return (d["profiles"]["claude"], d["profiles"]["gpt"], d["legacy_skills_gpt"])


# --------------------------------------------------------------------------- #
# Shape materialization
# --------------------------------------------------------------------------- #

def _make_junction(link: Path, target: Path) -> bool:
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       capture_output=True, text=True)
    return r.returncode == 0


def _materialize(kind, dest: Path):
    """Build a consumer home of the given shape at `dest`.

    Returns the path, or raises pytest.skip for a junction shape when a junction
    cannot be created in this environment."""
    if kind == "05-junction":
        # Discovery root is a junction pointing INSIDE the home.
        fx.build("02-generated", dest)
        claude_skills = dest / ".claude" / "skills"
        backing = dest / ".claude" / "skills_backing"
        os.rename(claude_skills, backing)
        if not _make_junction(claude_skills, backing):
            pytest.skip("cannot create a Windows junction in this environment")
        return dest
    if kind == "18-junction-external":
        # Discovery root is a junction pointing OUTSIDE the home -- the branch that
        # exercises the `<external>` sentinel, i.e. the absolute-path leak guard.
        fx.build("02-generated", dest)
        claude_skills = dest / ".claude" / "skills"
        outside = dest.parent / "outside-target"
        os.rename(claude_skills, outside)
        if not _make_junction(claude_skills, outside):
            pytest.skip("cannot create a Windows junction in this environment")
        return dest
    return fx.build(kind, dest)


# --------------------------------------------------------------------------- #
# Read-only proof: hash the entire tree (reparse points recorded, not descended)
# --------------------------------------------------------------------------- #

def _is_reparse(p: Path) -> bool:
    try:
        attrs = os.lstat(p).st_file_attributes  # Windows-only attribute
    except (OSError, AttributeError):
        return False
    return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)


def _reparse_marker(p: Path) -> str:
    try:
        return "<reparse:" + os.readlink(p) + ">"
    except OSError:
        return "<reparse>"


def _tree_digest(root: Path):
    """posix-relative path -> sha256 (files) / reparse marker (junctions).

    Reparse-point directories are recorded but NOT descended, so a junction cannot
    cause double-counting or an infinite walk."""
    root = Path(root)
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        kept = []
        for dn in dirnames:
            full = Path(dirpath) / dn
            if _is_reparse(full):
                rel = full.relative_to(root).as_posix()
                out[rel + "/<reparse>"] = _reparse_marker(full)
            else:
                kept.append(dn)
        dirnames[:] = kept
        for fn in filenames:
            full = Path(dirpath) / fn
            rel = full.relative_to(root).as_posix()
            try:
                out[rel] = hashlib.sha256(full.read_bytes()).hexdigest()
            except OSError:
                out[rel] = "<unreadable>"
    return out


# --------------------------------------------------------------------------- #
# Tooling + synthesizer self-check
# --------------------------------------------------------------------------- #

def test_inspector_exists():
    assert INSPECT_SCRIPT.is_file(), f"missing {INSPECT_SCRIPT}"


def test_no_committed_skill_md_under_a_discovery_path():
    """The #86 regression guard: no git-tracked file may sit at a host discovery
    path, or this repository publishes phantom skills into its own host.

    Enumerated from `git ls-files`, never hand-listed -- a newly committed fixture is
    covered the moment it is tracked."""
    tracked = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True).stdout.split("\n")
    roots = (".claude/skills/", ".claude/skills-gpt/", ".github/skills/", ".copilot/skills/")
    offenders = [f for f in tracked if f.strip() and any(r in f for r in roots)]
    assert not offenders, (
        "git-tracked files sit at a host skill-discovery path and will be discovered "
        f"as real skills: {offenders}")


@pytest.mark.parametrize("kind", SYNTHESIZED)
def test_synthesizer_writes_a_nonempty_shape(kind, tmp_path):
    """A silent no-op synthesizer would turn this whole module green-on-nothing.

    `01-clean` is empty BY DESIGN, so it is asserted empty rather than non-empty --
    the two branches together mean neither an over-eager nor a dead builder passes."""
    home = fx.build(kind, tmp_path / "home")
    files = [p for p in home.rglob("*") if p.is_file()]
    if kind == "01-clean":
        assert files == [], f"{kind} must be an empty home"
    else:
        assert files, f"{kind} synthesized no files"


def test_foreign_name_is_not_a_manifest_record():
    """Red-on-garbage anchor for the `foreign` fixture: if a future manifest added a
    skill by this name, 11-foreign would silently become `managed` and the only
    negative anchor for the four-class model would evaporate."""
    names = {s["name"] for s in json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["skills"]}
    assert fx.FOREIGN_DIR not in names
    assert fx.FOREIGN_DIR != "_shared"


# --------------------------------------------------------------------------- #
# -Home validation / exit codes
# --------------------------------------------------------------------------- #

def test_missing_home_exits_nonzero_without_prompt():
    r = subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(INSPECT_SCRIPT), "-Format", "json"],
        capture_output=True, text=True)
    assert r.returncode != 0
    assert "required" in (r.stdout + r.stderr).lower()


def test_nonexistent_home_exits_nonzero(tmp_path):
    r = _run_inspect(tmp_path / "does-not-exist", fmt="json")
    assert r.returncode != 0
    assert "does not exist" in (r.stdout + r.stderr).lower()


def test_file_home_is_rejected(tmp_path):
    f = tmp_path / "a-file"
    f.write_text("x", encoding="utf-8")
    r = _run_inspect(f, fmt="json")
    assert r.returncode != 0
    assert "not a directory" in (r.stdout + r.stderr).lower()


# --------------------------------------------------------------------------- #
# Read-only proof (all shapes, both formats)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("kind", ALL_SHAPES)
def test_inspector_is_read_only(kind, tmp_path):
    home = _materialize(kind, tmp_path / "home")
    before = _tree_digest(home)
    for fmt in ("text", "json"):
        for absolute in (False, True):
            r = _run_inspect(home, fmt=fmt, absolute=absolute)
            assert r.returncode == 0, f"{kind}/{fmt}: {r.stderr}"
    after = _tree_digest(home)
    assert before == after, f"{kind}: inspector mutated the tree"


# --------------------------------------------------------------------------- #
# Stable schema
# --------------------------------------------------------------------------- #

def test_schema_shape_is_stable(tmp_path):
    home = _materialize("02-generated", tmp_path / "home")
    d = _inspect_json(home)
    assert d["schema_version"] == 1
    for key in ("consumer_home", "instruction_files", "profiles", "legacy_skills_gpt",
                "ledger", "router", "legacy_shadows", "warnings"):
        assert key in d, f"missing top-level key {key}"
    assert set(d["profiles"].keys()) == {"claude", "gpt"}
    for prof in _all_profiles(d):
        for key in ("discovery_root", "state", "link_type", "link_target",
                    "owned_count", "unowned_count", "skills", "adapter_sample"):
            assert key in prof
    for key in ("state", "providers", "unrecognized_provider_count"):
        assert key in d["ledger"], f"missing ledger key {key}"


@pytest.mark.parametrize("kind", ALL_SHAPES)
def test_ledger_shape_is_stable_across_every_state(kind, tmp_path):
    """`unrecognized_provider_count` must exist on the absent and corrupt branches
    too, or a consumer keying off it breaks exactly when the ledger is broken."""
    d = _inspect_json(_materialize(kind, tmp_path / "home"))
    assert d["ledger"]["state"] in LEDGER_STATES
    assert isinstance(d["ledger"]["unrecognized_provider_count"], int)
    assert isinstance(d["ledger"]["providers"], list)


# --------------------------------------------------------------------------- #
# Per-shape classification (each via the real inspector)
# --------------------------------------------------------------------------- #

def test_clean_home_is_empty_state(tmp_path):
    home = _materialize("01-clean", tmp_path / "home")
    d = _inspect_json(home)
    assert d["profiles"]["claude"]["state"] == "absent"
    assert d["profiles"]["gpt"]["state"] == "absent"
    assert d["legacy_skills_gpt"]["state"] == "absent"
    assert d["ledger"]["state"] == "absent"
    assert d["router"]["classification"] == "absent"
    assert d["warnings"] == []
    assert d["legacy_shadows"] == []
    for f in d["instruction_files"]:
        assert f["present"] is False
        # Absent at a convention path is `unknown`, NOT `host-convention`:
        # host-convention means the convention AND a file present at it.
        assert f["evidence_class"] == "unknown"


def test_generated_home_both_owned(tmp_path):
    home = _materialize("02-generated", tmp_path / "home")
    d = _inspect_json(home)
    cl, gp = d["profiles"]["claude"], d["profiles"]["gpt"]
    assert cl["state"] == "present" and gp["state"] == "present"
    assert _skill(cl, "build-phase")["eligibility"] == "managed"
    assert _skill(cl, "build-phase")["owned"] is True
    assert _skill(gp, "build-phase")["owned"] is True
    assert cl["owned_count"] == 1 and cl["unowned_count"] == 0
    assert gp["owned_count"] == 1 and gp["unowned_count"] == 0
    assert cl["adapter_sample"]["profile_header"] == "claude"
    assert gp["adapter_sample"]["profile_header"] == "gpt"
    assert d["ledger"]["state"] == "valid"
    assert d["ledger"]["providers"] == ["claude", "gpt"]
    assert d["ledger"]["unrecognized_provider_count"] == 0
    # a clean generated state carries no warnings
    assert _codes(d) == set(), d["warnings"]
    # A PRESENT instruction file is `host-convention` -- the file is at a documented
    # discovery path. It is never `observed`: nothing here asks the host what it
    # loaded (see test_evidence_class_is_never_observed).
    claude_md = [f for f in d["instruction_files"] if f["rel_path"] == "CLAUDE.md"][0]
    assert claude_md["present"] is True and claude_md["evidence_class"] == "host-convention"


def test_legacy_foreign_tree_at_managed_paths(tmp_path):
    home = _materialize("03-legacy", tmp_path / "home")
    d = _inspect_json(home)
    cl = d["profiles"]["claude"]
    for name in ("build-phase", "build-step"):
        s = _skill(cl, name)
        assert s["eligibility"] == "managed", name
        assert s["owned"] is False, name
    assert cl["owned_count"] == 0 and cl["unowned_count"] == 2
    codes = _codes(d)
    assert "MANAGED_PATH_UNOWNED" in codes
    assert "MANAGED_SKILL_MISSING_GPT_PROFILE" in codes
    assert d["ledger"]["state"] == "absent"


def test_mixed_owned(tmp_path):
    home = _materialize("04-mixed-owned", tmp_path / "home")
    d = _inspect_json(home)
    cl = d["profiles"]["claude"]
    assert _skill(cl, "build-phase")["owned"] is True
    assert _skill(cl, "build-step")["owned"] is False
    assert cl["owned_count"] == 1 and cl["unowned_count"] == 1
    assert "MANAGED_PATH_UNOWNED" in _codes(d)


def test_absent_gpt_missing_profile_carve_out(tmp_path):
    home = _materialize("06-absent-gpt", tmp_path / "home")
    d = _inspect_json(home)
    assert d["profiles"]["gpt"]["state"] == "absent"
    codes = _codes(d)
    assert "MANAGED_SKILL_MISSING_GPT_PROFILE" in codes
    msg = [w["message"] for w in d["warnings"]
           if w["code"] == "MANAGED_SKILL_MISSING_GPT_PROFILE"][0]
    # portable skill flagged; provider-native (single-profile) skill NOT flagged
    assert "build-phase" in msg
    assert "context-slim" not in msg
    cs = _skill(d["profiles"]["claude"], "context-slim")
    assert cs["manifest_status"] == "provider-native"
    assert cs["single_profile"] is True


def test_prior_wrong_target_copilot(tmp_path):
    home = _materialize("07-prior-wrong-target", tmp_path / "home")
    d = _inspect_json(home)
    assert "RETIRED_COPILOT_TARGET_PRESENT" in _codes(d)
    assert ".copilot/skills" in d["legacy_shadows"]
    assert d["profiles"]["claude"]["state"] == "absent"
    assert d["profiles"]["gpt"]["state"] == "absent"
    agents = [f for f in d["instruction_files"] if f["rel_path"] == "AGENTS.md"][0]
    assert agents["present"] is True and agents["evidence_class"] == "host-convention"


def test_consumer_only_not_managed(tmp_path):
    home = _materialize("08-consumer-only", tmp_path / "home")
    d = _inspect_json(home)
    s = _skill(d["profiles"]["claude"], "build-observer")
    assert s["eligibility"] == "consumer-only"
    assert s["manifest_status"] is None
    codes = _codes(d)
    assert "CONSUMER_ONLY_PRESENT" in codes
    # the KEY distinction: an unmanifested tree is never a managed-path defect
    assert "MANAGED_PATH_UNOWNED" not in codes
    assert "MANAGED_SKILL_MISSING_GPT_PROFILE" not in codes


def test_both_trees_consumer_only_in_each_root(tmp_path):
    home = _materialize("09-both-trees-consumer-only", tmp_path / "home")
    d = _inspect_json(home)
    a = _skill(d["profiles"]["claude"], "goblin-sweep")
    b = _skill(d["legacy_skills_gpt"], "goblin-sweep")
    assert a is not None and b is not None
    # consumer-only in EACH root; managed in NEITHER
    assert a["eligibility"] == "consumer-only"
    assert b["eligibility"] == "consumer-only"
    codes = _codes(d)
    assert "LEGACY_CLAUDE_SKILLS_GPT_PRESENT" in codes
    assert "CONSUMER_ONLY_PRESENT" in codes
    assert ".claude/skills-gpt" in d["legacy_shadows"]


def test_core_holder_distinct_from_foreign(tmp_path):
    home = _materialize("10-core-holder", tmp_path / "home")
    d = _inspect_json(home)
    s = _skill(d["profiles"]["claude"], "_shared")
    assert s is not None
    assert s["eligibility"] == "core-holder"
    assert s["has_skill_md"] is False
    cl = d["profiles"]["claude"]
    assert cl["owned_count"] == 0 and cl["unowned_count"] == 0
    assert "MANAGED_PATH_UNOWNED" not in _codes(d)


def test_foreign_is_distinct_from_consumer_only_and_core_holder(tmp_path):
    """The four-class model's missing negative anchor (#85 gap 1).

    Without a `foreign` case, a regression collapsing `consumer-only` into `foreign`
    -- which would make a migrator delete a consumer's own skills -- passes."""
    home = _materialize("11-foreign", tmp_path / "home")
    d = _inspect_json(home)
    s = _skill(d["profiles"]["claude"], fx.FOREIGN_DIR)
    assert s is not None, "the foreign directory was not enumerated at all"
    assert s["eligibility"] == "foreign"
    assert s["has_skill_md"] is False
    assert s["owned"] is False
    assert s["manifest_status"] is None
    # foreign is neither of its neighbours, and never counted as an install
    assert s["eligibility"] not in ("consumer-only", "core-holder", "managed")
    cl = d["profiles"]["claude"]
    assert cl["owned_count"] == 0 and cl["unowned_count"] == 0
    # a foreign directory is not a consumer-only skill, so that warning must be quiet
    assert "CONSUMER_ONLY_PRESENT" not in _codes(d)


def test_all_four_eligibility_classes_are_reachable(tmp_path):
    """Every class in the declared vocabulary is produced by some shape. A class no
    fixture can produce is a contract the suite does not actually test."""
    seen = set()
    for kind in ("02-generated", "08-consumer-only", "10-core-holder", "11-foreign"):
        d = _inspect_json(_materialize(kind, tmp_path / kind))
        for prof in _all_profiles(d):
            seen.update(s["eligibility"] for s in prof["skills"])
    assert seen == ELIGIBILITY, f"unreachable eligibility classes: {ELIGIBILITY - seen}"


# --------------------------------------------------------------------------- #
# Instruction evidence class (plan section 7 runtime-provenance rule)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("kind", ALL_SHAPES)
def test_evidence_class_is_never_observed(kind, tmp_path):
    """`observed` means THE HOST EXPOSED runtime provenance. This inspector only runs
    Test-Path, so it may never make that claim -- reporting `observed` from file
    presence is precisely the confusion Step 43 existed to disprove.

    Parametrized over every shape so the guarantee cannot hold for one fixture and
    lapse for another."""
    d = _inspect_json(_materialize(kind, tmp_path / "home"))
    for f in d["instruction_files"]:
        assert f["evidence_class"] != "observed", (
            f"{kind}/{f['rel_path']}: evidence_class upgraded to 'observed'")
        assert f["evidence_class"] in EVIDENCE_CLASSES
        # present <-> host-convention, absent <-> unknown, with no third combination
        expected = "host-convention" if f["present"] else "unknown"
        assert f["evidence_class"] == expected


def test_observed_never_appears_in_raw_output(tmp_path):
    """Substring backstop: catches an `observed` reintroduced through a code path the
    structured assertion above does not walk."""
    home = _materialize("02-generated", tmp_path / "home")
    for fmt in ("text", "json"):
        out = _run_inspect(home, fmt=fmt).stdout
        assert "observed" not in out, f"'observed' emitted in {fmt} output"


# --------------------------------------------------------------------------- #
# Ledger states (#85 gap 2 -- all three corrupt return paths)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("kind", [
    "12-ledger-unparseable",    # not JSON at all
    "13-ledger-bad-installs",   # `installs` present but not an object
    "14-ledger-bad-version",    # unknown schema version
])
def test_corrupt_ledger_states(kind, tmp_path):
    d = _inspect_json(_materialize(kind, tmp_path / "home"))
    assert d["ledger"]["state"] == "corrupt", kind
    assert d["ledger"]["providers"] == []
    assert "LEDGER_CORRUPT" in _codes(d), kind


def test_bad_version_ledger_is_not_reached_through_the_installs_branch(tmp_path):
    """Red-on-garbage anchor for the corrupt trio: the installs check runs BEFORE the
    version check, so the version fixture must carry a WELL-FORMED installs object.
    Otherwise all three fixtures would prove the same single branch."""
    home = _materialize("14-ledger-bad-version", tmp_path / "home")
    led = json.loads((home / fx.LEDGER_NAME).read_text(encoding="utf-8"))
    assert isinstance(led["installs"], dict) and led["installs"], \
        "version fixture must have valid installs or it trips the installs branch"
    assert led["ledger_version"] != 1


def test_valid_ledger_reports_no_unrecognized_providers(tmp_path):
    d = _inspect_json(_materialize("02-generated", tmp_path / "home"))
    assert d["ledger"]["unrecognized_provider_count"] == 0
    assert "LEDGER_UNKNOWN_PROVIDER" not in _codes(d)


# --------------------------------------------------------------------------- #
# Router classification (#85 gap 3)
# --------------------------------------------------------------------------- #

def test_router_canonical_classification(tmp_path):
    d = _inspect_json(_materialize("15-router-canonical", tmp_path / "home"))
    assert d["router"]["classification"] == "canonical"
    assert d["router"]["version"] == "2.3.4"
    assert d["router"]["rel_path"] == fx.CANONICAL_ROUTER
    assert "ROUTER_LEGACY" not in _codes(d)


def test_router_legacy_classification_warns(tmp_path):
    d = _inspect_json(_materialize("16-router-legacy", tmp_path / "home"))
    assert d["router"]["classification"] == "legacy"
    assert d["router"]["version"] == "0.9.1"
    assert d["router"]["rel_path"] == fx.LEGACY_ROUTER
    assert "ROUTER_LEGACY" in _codes(d)


def test_router_version_rejects_non_semver(tmp_path):
    """A router IS present, so classification must still resolve -- only the version
    is withheld. Reporting `absent` here would read as 'no router installed'."""
    d = _inspect_json(_materialize("17-router-bad-version", tmp_path / "home"))
    assert d["router"]["classification"] == "canonical"
    assert d["router"]["version"] is None


# --------------------------------------------------------------------------- #
# Path display: relative by default, absolute on opt-in
# --------------------------------------------------------------------------- #

def test_default_output_is_home_relative(tmp_path):
    home = _materialize("02-generated", tmp_path / "home")
    d = _inspect_json(home, absolute=False)
    assert d["consumer_home"] == "."
    assert d["profiles"]["claude"]["discovery_root"] == ".claude/skills"
    assert d["profiles"]["gpt"]["discovery_root"] == ".github/skills"
    assert _skill(d["profiles"]["claude"], "build-phase")["rel_path"].startswith(".claude/skills")
    # no drive-absolute path anywhere in default (relative) output
    text = _run_inspect(home, fmt="text", absolute=False).stdout
    assert DRIVE_ABS_RE.search(text) is None
    js = _run_inspect(home, fmt="json", absolute=False).stdout
    assert DRIVE_ABS_RE.search(js) is None


def test_absolute_paths_switch(tmp_path):
    home = _materialize("02-generated", tmp_path / "home")
    d = _inspect_json(home, absolute=True)
    assert os.path.isabs(d["consumer_home"])
    assert os.path.normcase(os.path.normpath(d["consumer_home"])) == \
        os.path.normcase(os.path.normpath(str(home)))
    assert os.path.isabs(d["profiles"]["claude"]["discovery_root"])
    assert d["profiles"]["claude"]["discovery_root"].lower().endswith("skills")


def test_junction_root_detected(tmp_path):
    home = _materialize("05-junction", tmp_path / "home")
    d = _inspect_json(home)
    cl = d["profiles"]["claude"]
    assert cl["link_type"] == "junction"
    # target resolves inside the home -> shown relative (never leaked as absolute)
    assert cl["link_target"] is not None
    assert DRIVE_ABS_RE.search(cl["link_target"]) is None
    assert "DISCOVERY_ROOT_JUNCTION" in _codes(d)
    # content still classifies through the junction
    assert _skill(cl, "build-phase")["owned"] is True


def test_external_junction_target_is_sentinelled(tmp_path):
    """#85 gap 4: the `<external>` sentinel IS the absolute-path leak guard for
    junctions, and the only junction fixture pointed inside the home, so the guard
    itself never ran."""
    home = _materialize("18-junction-external", tmp_path / "home")
    d = _inspect_json(home)
    cl = d["profiles"]["claude"]
    assert cl["link_type"] == "junction"
    assert cl["link_target"] == "<external>", \
        f"outside-home junction target leaked as {cl['link_target']!r}"
    for fmt in ("text", "json"):
        out = _run_inspect(home, fmt=fmt, absolute=False).stdout
        assert DRIVE_ABS_RE.search(out) is None
    # -AbsolutePaths is the documented opt-in that DOES reveal the real target
    d_abs = _inspect_json(home, absolute=True)
    assert d_abs["profiles"]["claude"]["link_target"] != "<external>"
    assert os.path.isabs(d_abs["profiles"]["claude"]["link_target"])


# --------------------------------------------------------------------------- #
# Output sanitation: closed vocabularies and bounded shapes (#84)
# --------------------------------------------------------------------------- #

def _assert_report_is_bounded(d, where):
    """Positive shape gate over every emitted scalar.

    A substring hunt for a planted canary only ever finds what the plant happened to
    name; five of the audited channels carry arbitrary consumer bytes. Asserting that
    each field stays INSIDE its declared vocabulary catches all of them at once."""
    assert set(d["ledger"]["providers"]) <= PROVIDER_SLUGS, where
    assert d["ledger"]["state"] in LEDGER_STATES, where
    assert d["router"]["classification"] in ROUTER_CLASSES, where
    if d["router"]["version"] is not None:
        assert re.match(r"\A[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}\Z", d["router"]["version"]), where
    for f in d["instruction_files"]:
        assert f["evidence_class"] in EVIDENCE_CLASSES, where
    for prof in _all_profiles(d):
        assert prof["link_type"] in LINK_TYPES, where
        if prof["adapter_sample"] is not None:
            assert prof["adapter_sample"]["profile_header"] in PROVIDER_SLUGS | {"unknown"}, where
            assert SAFE_NAME_RE.match(prof["adapter_sample"]["skill"]), where
        for s in prof["skills"]:
            assert s["eligibility"] in ELIGIBILITY, where
            assert SAFE_NAME_RE.match(s["name"]), f"{where}: unbounded name {s['name']!r}"
            assert s["rel_path"].endswith("/" + s["name"]), \
                f"{where}: rel_path {s['rel_path']!r} diverged from name {s['name']!r}"
    blob = json.dumps(d)
    assert DRIVE_ABS_RE.search(blob) is None, f"{where}: absolute path in default output"
    for ctrl in ("\\n", "\\r", "\\t"):
        assert ctrl not in blob, f"{where}: control character reached the report"


@pytest.mark.parametrize("kind", ALL_SHAPES)
def test_every_shape_emits_a_bounded_report(kind, tmp_path):
    _assert_report_is_bounded(_inspect_json(_materialize(kind, tmp_path / "home")), kind)


def test_hostile_home_is_fully_bounded(tmp_path):
    """The adversarial case: every consumer-controlled channel carries a hostile
    value at once."""
    home = _materialize("19-hostile", tmp_path / "home")
    d = _inspect_json(home)
    _assert_report_is_bounded(d, "19-hostile")

    # Ledger KEYS: the channel that put a real absolute path into the default report.
    assert d["ledger"]["state"] == "valid"
    assert d["ledger"]["providers"] == ["claude", "gpt"]
    assert d["ledger"]["unrecognized_provider_count"] == 3
    assert "LEDGER_UNKNOWN_PROVIDER" in _codes(d)

    # A decoy `Profile:` ABOVE the real header must not win.
    assert d["profiles"]["claude"]["adapter_sample"]["profile_header"] == "claude"

    # An LF-terminated version must not pass the semver gate, while the router is
    # still correctly classified as present.
    assert d["router"]["classification"] == "legacy"
    assert d["router"]["version"] is None

    names = {s["name"] for s in d["profiles"]["claude"]["skills"]}
    assert "comma,injected-name" not in names, "list separator survived into a name"
    assert not any(len(n) > 65 for n in names), "an over-long name was not capped"

    for fmt in ("text", "json"):
        r = _run_inspect(home, fmt=fmt)
        assert fx.VICTIM_PATH not in r.stdout
        assert "INJECTED_LEDGER_LINE" not in r.stdout
        assert "Q" * 100 not in r.stdout
        assert r.stderr == "", f"unexpected stderr on a valid home: {r.stderr!r}"


def test_hostile_plants_are_actually_present(tmp_path):
    """Red-on-garbage anchor for the hostile fixture itself.

    If a future edit stopped writing the plants, every assertion above would pass
    against a clean home and the leak gate would be a permanent green."""
    home = fx.build("19-hostile", tmp_path / "home")
    led = json.loads((home / fx.LEDGER_NAME).read_text(encoding="utf-8"))
    keys = list(led["installs"])
    assert fx.VICTIM_PATH in keys, "absolute-path ledger key plant missing"
    assert any("\n" in k for k in keys), "newline ledger key plant missing"
    assert any(len(k) >= 400 for k in keys), "over-long ledger key plant missing"
    skill_md = (home / fx.CLAUDE_ROOT / "build-phase" / "SKILL.md").read_text(encoding="utf-8")
    assert skill_md.startswith("Profile: " + fx.SECRET), "decoy Profile plant missing"
    dirs = {p.name for p in (home / fx.CLAUDE_ROOT).iterdir() if p.is_dir()}
    assert "comma,injected-name" in dirs, "comma-bearing directory plant missing"
    assert any(len(n) == fx.OVERLONG_NAME_LEN for n in dirs), "over-long directory plant missing"
    # The plant must stay ABOVE the display cap (or it proves no truncation) and
    # BELOW a length that overflows MAX_PATH once mounted under tmp_path.
    assert fx.OVERLONG_NAME_LEN > 64
    assert len(str(home / fx.CLAUDE_ROOT / ("Z" * fx.OVERLONG_NAME_LEN) / "SKILL.md")) < 260
    # The LF terminator is the whole point of this plant -- CRLF would not exercise
    # the regex hole at all.
    router = (home / fx.LEGACY_ROUTER).read_bytes()
    assert b"'1.2.3\n'" in router and b"\r" not in router, "router LF plant is not LF"


def test_provider_case_variant_is_recognized_and_normalized(tmp_path):
    """A provider slug spelled in another case is a LEGITIMATE install, not an
    attack: the installer's ValidateSet accepts `-Provider CLAUDE` and writes that
    spelling verbatim. Dropping it would under-report a real install (a false-clean
    preflight); echoing it would break the closed vocabulary. It must be recognized
    AND normalized to the manifest slug."""
    d = _inspect_json(_materialize("20-provider-case-variant", tmp_path / "home"))
    assert d["ledger"]["state"] == "valid"
    assert d["ledger"]["unrecognized_provider_count"] == 0, "a real install was dropped"
    assert d["ledger"]["providers"] == ["claude"], "the ledger's spelling was echoed"
    assert d["profiles"]["claude"]["adapter_sample"]["profile_header"] == "claude"
    assert "LEDGER_UNKNOWN_PROVIDER" not in _codes(d)


def test_provider_lookalike_is_rejected_not_echoed(tmp_path):
    """A culture-aware string comparison treats 'claude' + U+00AD*300 as EQUAL to
    'claude'. Matching that way and emitting the matched token would echo 300
    unbounded non-ASCII consumer bytes as a recognized provider -- so the comparison
    must be ORDINAL, and the emitted value must be the vocabulary's own slug."""
    home = _materialize("21-provider-lookalike", tmp_path / "home")
    d = _inspect_json(home)
    assert d["ledger"]["state"] == "valid"
    assert d["ledger"]["providers"] == [], "an ignorable-character lookalike was accepted"
    assert d["ledger"]["unrecognized_provider_count"] == 1
    assert "LEDGER_UNKNOWN_PROVIDER" in _codes(d)
    for fmt in ("text", "json"):
        r = _run_inspect(home, fmt=fmt)
        assert chr(0x00AD) not in r.stdout, f"lookalike bytes echoed into {fmt} output"


def test_invalid_home_does_not_echo_the_path_to_stderr(tmp_path):
    """The stderr channel no test previously read. -Home is an absolute path by
    construction, so echoing it back wrote a private path into a stream a caller may
    fold into a pasted report."""
    missing = tmp_path / "no-such-home"
    r = _run_inspect(missing, fmt="json")
    assert r.returncode == 2
    assert DRIVE_ABS_RE.search(r.stderr) is None, f"absolute path in stderr: {r.stderr!r}"
    assert str(missing) not in r.stderr
    assert r.stderr.strip().count("\n") == 0, "multi-line stderr suggests injection"

    a_file = tmp_path / "a-file"
    a_file.write_text("x", encoding="utf-8")
    r2 = _run_inspect(a_file, fmt="json")
    assert r2.returncode == 2
    assert DRIVE_ABS_RE.search(r2.stderr) is None, f"absolute path in stderr: {r2.stderr!r}"


def test_no_secret_or_content_leak(tmp_path):
    """File CONTENT never reaches the report.

    Note the CLAUDE.md plant is a forward guard only: Get-InstructionFiles runs
    Test-Path and never opens the file, so no byte of it can reach output today. It
    stays so that a future content-read goes red."""
    home = _materialize("02-generated", tmp_path / "home")
    secret = fx.SECRET
    skill_md = home / ".claude" / "skills" / "build-phase" / "SKILL.md"
    skill_md.write_text(skill_md.read_text(encoding="utf-8") +
                        f"\nAPI_KEY={secret}\n", encoding="utf-8")
    (home / "CLAUDE.md").write_text(f"token: {secret}\n", encoding="utf-8")
    ledger_path = home / fx.LEDGER_NAME
    led = json.loads(ledger_path.read_text(encoding="utf-8"))
    led["installs"]["claude"]["secret_field"] = secret
    ledger_path.write_text(json.dumps(led, indent=2), encoding="utf-8")

    marker = fx.marker_token()
    for absolute in (False, True):
        for fmt in ("text", "json"):
            r = _run_inspect(home, fmt=fmt, absolute=absolute)
            out = r.stdout + r.stderr
            assert secret not in out, f"secret leaked ({fmt}, absolute={absolute})"
            # ownership is reported as a class, never by dumping the provenance marker
            assert marker not in out, f"marker literal leaked ({fmt}, absolute={absolute})"
    # ledger still reports provider NAMES only (no payload fields)
    d = _inspect_json(home)
    assert d["ledger"]["providers"] == ["claude", "gpt"]
    assert "secret_field" not in json.dumps(d)
