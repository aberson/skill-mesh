"""Read-only host-install inspection gate (Step 46).

Exercises tools/inspect-host-install.ps1 END-TO-END against the consumer-home
fixture shapes under tests/fixtures/legacy-install/. Every assertion runs the
ACTUAL PowerShell inspector via subprocess (never a Python re-implementation of the
classification logic).

Guarantees proven here:
  - each fixture produces a STABLE manifest-driven classification;
  - the inspector is READ-ONLY (the fixture tree hashes identically before/after);
  - default output is consumer-home-RELATIVE; -AbsolutePaths switches to absolute;
  - no secret-shaped value or file content leaks into either output format.

Style matches tests/distributions/test_distributions.py: shell out to
powershell.exe, use tmp_path, and skipif when powershell is not on PATH.
"""
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
INSPECT_SCRIPT = REPO_ROOT / "tools" / "inspect-host-install.ps1"
PROVENANCE_SCRIPT = REPO_ROOT / "tools" / "skill-mesh-provenance.ps1"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "legacy-install"

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")

# Committed fixture shapes (materialized by copytree). The clean/empty (#1) and
# junction (#5) shapes are synthesized at runtime.
COMMITTED = [
    "02-generated",
    "03-legacy",
    "04-mixed-owned",
    "06-absent-gpt",
    "07-prior-wrong-target",
    "08-consumer-only",
    "09-both-trees-consumer-only",
    "10-core-holder",
]
ALL_SHAPES = ["01-clean"] + COMMITTED + ["05-junction"]

FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def _marker_literal():
    m = re.search(r"return\s+'([^']+)'", PROVENANCE_SCRIPT.read_text(encoding="utf-8"))
    assert m, "marker literal not found in tools/skill-mesh-provenance.ps1"
    return m.group(1)


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


# --------------------------------------------------------------------------- #
# Fixture materialization (copy committed shapes; synthesize clean + junction)
# --------------------------------------------------------------------------- #

def _make_junction(link: Path, target: Path) -> bool:
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       capture_output=True, text=True)
    return r.returncode == 0


def _materialize(kind, dest: Path):
    """Build a consumer home of the given shape at `dest`. Returns the path, or
    raises pytest.skip for the junction shape when a junction cannot be created."""
    if kind == "01-clean":
        dest.mkdir(parents=True, exist_ok=True)
        return dest
    if kind == "05-junction":
        shutil.copytree(FIXTURES / "02-generated", dest)
        claude_skills = dest / ".claude" / "skills"
        backing = dest / ".claude" / "skills_backing"
        os.rename(claude_skills, backing)
        if not _make_junction(claude_skills, backing):
            pytest.skip("cannot create a Windows junction in this environment")
        return dest
    shutil.copytree(FIXTURES / kind, dest)
    return dest


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
# Tooling presence
# --------------------------------------------------------------------------- #

def test_inspector_and_fixtures_exist():
    assert INSPECT_SCRIPT.is_file(), f"missing {INSPECT_SCRIPT}"
    for kind in COMMITTED:
        assert (FIXTURES / kind).is_dir(), f"missing fixture {kind}"


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
    for prof in (d["profiles"]["claude"], d["profiles"]["gpt"], d["legacy_skills_gpt"]):
        for key in ("discovery_root", "state", "link_type", "link_target",
                    "owned_count", "unowned_count", "skills", "adapter_sample"):
            assert key in prof


# --------------------------------------------------------------------------- #
# Per-fixture classification (each via the real inspector)
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
        assert f["evidence_class"] == "host-convention"


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
    # a clean generated state carries no warnings
    assert _codes(d) == set(), d["warnings"]
    # instruction file observed only when actually present
    claude_md = [f for f in d["instruction_files"] if f["rel_path"] == "CLAUDE.md"][0]
    assert claude_md["present"] is True and claude_md["evidence_class"] == "observed"


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
    assert agents["present"] is True and agents["evidence_class"] == "observed"


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


def test_junction_root_detected(tmp_path):
    home = _materialize("05-junction", tmp_path / "home")
    d = _inspect_json(home)
    cl = d["profiles"]["claude"]
    assert cl["link_type"] == "junction"
    # target resolves inside the home -> shown relative (never leaked as absolute)
    assert cl["link_target"] is not None
    assert not re.search(r"[A-Za-z]:[\\/]", cl["link_target"])
    assert "DISCOVERY_ROOT_JUNCTION" in _codes(d)
    # content still classifies through the junction
    assert _skill(cl, "build-phase")["owned"] is True


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
    assert re.search(r"[A-Za-z]:[\\/]", text) is None
    js = _run_inspect(home, fmt="json", absolute=False).stdout
    assert re.search(r"[A-Za-z]:[\\/]", js) is None


def test_absolute_paths_switch(tmp_path):
    home = _materialize("02-generated", tmp_path / "home")
    d = _inspect_json(home, absolute=True)
    assert os.path.isabs(d["consumer_home"])
    assert os.path.normcase(os.path.normpath(d["consumer_home"])) == \
        os.path.normcase(os.path.normpath(str(home)))
    assert os.path.isabs(d["profiles"]["claude"]["discovery_root"])
    assert d["profiles"]["claude"]["discovery_root"].lower().endswith("skills")


# --------------------------------------------------------------------------- #
# No secret-shaped value / file content leaks
# --------------------------------------------------------------------------- #

SECRET = "sk-LEAKCANARY-0123456789abcdef"


def test_no_secret_or_content_leak(tmp_path):
    home = _materialize("02-generated", tmp_path / "home")
    # Plant a secret in a SKILL.md body, an instruction file, and a ledger payload.
    skill_md = home / ".claude" / "skills" / "build-phase" / "SKILL.md"
    skill_md.write_text(skill_md.read_text(encoding="utf-8") +
                        f"\nAPI_KEY={SECRET}\n", encoding="utf-8")
    (home / "CLAUDE.md").write_text(f"token: {SECRET}\n", encoding="utf-8")
    ledger_path = home / ".skill-mesh-install.json"
    led = json.loads(ledger_path.read_text(encoding="utf-8"))
    led["installs"]["claude"]["secret_field"] = SECRET
    ledger_path.write_text(json.dumps(led, indent=2), encoding="utf-8")

    marker = _marker_literal()
    for absolute in (False, True):
        for fmt in ("text", "json"):
            out = _run_inspect(home, fmt=fmt, absolute=absolute).stdout
            assert SECRET not in out, f"secret leaked ({fmt}, absolute={absolute})"
            # ownership is reported as a class, never by dumping the provenance marker
            assert marker not in out, f"marker literal leaked ({fmt}, absolute={absolute})"
    # ledger still reports provider NAMES only (no payload fields)
    d = _inspect_json(home)
    assert d["ledger"]["providers"] == ["claude", "gpt"]
    assert "secret_field" not in json.dumps(d)
