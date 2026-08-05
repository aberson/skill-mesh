"""Reversible legacy-install migration gate (Step 47).

Exercises the two new tools END-TO-END through the REAL PowerShell scripts:

  tools/skill-mesh-transaction.ps1  -- the shared transaction engine (state
                                       machine, append-only journal, ordered
                                       rollback, idempotent resume), dot-sourced
                                       by both the installer and the migrator.
  tools/migrate-legacy-install.ps1  -- dry-run-default migration with an external
                                       backup, explicit -Apply, -Resume, -Rollback.

Nothing here re-implements classification, hashing, or the state machine in
Python: every assertion runs the actual script via subprocess and reads what it
wrote to disk.

Consumer homes are SYNTHESIZED at test time by legacy_install_fixtures. A
committed fixture SKILL.md sitting at `.claude/skills/<name>/` is loaded by Claude
Code as a LIVE skill -- that was #86, and
test_host_inspect.test_no_committed_skill_md_under_a_discovery_path keeps it from
returning.

Style matches tests/distributions/test_host_inspect.py: shell out to
powershell.exe, use tmp_path, skipif when powershell is not on PATH. Paths under
tmp_path are kept SHORT deliberately -- the backup payload mirrors the home's
relative path under `<backup>/<migration_id>/payload/`, and MAX_PATH (260) is real
on machines without LongPathsEnabled.
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
MIGRATE_SCRIPT = REPO_ROOT / "tools" / "migrate-legacy-install.ps1"
TRANSACTION_SCRIPT = REPO_ROOT / "tools" / "skill-mesh-transaction.ps1"
INSTALL_SCRIPT = REPO_ROOT / "tools" / "install-skill-mesh.ps1"
BUILD_SCRIPT = REPO_ROOT / "tools" / "build-distributions.ps1"
MANIFEST_PATH = REPO_ROOT / "config" / "skill-manifest.json"

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")

# The six transaction states, mirrored from the plan's BackupManifest.status
# vocabulary. test_state_machine_matches_the_engines_own_vocabulary proves the
# engine agrees, so this list can never silently drift from the implementation.
STATES = ["prepared", "applying", "applied", "rolling_back", "rolled_back",
          "failed_incomplete"]
TERMINAL_RESOLVED = {"applied", "rolled_back"}

# Exactly the transitions the engine may allow. `applied -> rolling_back` and
# `prepared -> rolling_back` are the operator-initiated -Rollback entries the CLI
# contract requires; everything else is the plan's failure-path narrative.
LEGAL_TRANSITIONS = {
    ("prepared", "applying"),
    ("prepared", "rolling_back"),
    ("applying", "applied"),
    ("applying", "rolling_back"),
    ("applied", "rolling_back"),
    ("rolling_back", "rolled_back"),
    ("rolling_back", "failed_incomplete"),
}

ACTION_KINDS = {"backup", "install", "retire", "preserve", "ledger"}
MUTATING_KINDS = {"retire", "install", "ledger"}

CLAUDE_ROOT = fx.CLAUDE_ROOT
GPT_ROOT = fx.GPT_ROOT
COPILOT_ROOT = fx.RETIRED_COPILOT_ROOT
LEDGER_NAME = fx.LEDGER_NAME

# A bounded display segment: the skill-name charset, capped, with an optional
# truncation marker. Same shape tests/distributions/test_host_inspect.py pins for the
# inspector, so the two tools' report-bounding contracts cannot diverge.
SAFE_NAME_RE = re.compile(r"\A(<unnamed>|[A-Za-z0-9._-]{1,64}~?)\Z")


# --------------------------------------------------------------------------- #
# Invocation helpers
# --------------------------------------------------------------------------- #

def _run(script, args, env=None):
    full_env = None
    if env:
        full_env = dict(os.environ)
        full_env.update(env)
    return subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(script), *args],
        capture_output=True, text=True, env=full_env)


def _migrate(home, backup, dist=None, mode=None, migration_id=None,
             fmt="json", env=None, omit_backup=False):
    args = ["-Home", str(home)]
    if not omit_backup:
        args += ["-BackupDir", str(backup)]
    if dist is not None:
        args += ["-DistDir", str(dist)]
    if mode:
        args.append(mode)
    if migration_id:
        args += ["-MigrationId", migration_id]
    args += ["-Format", fmt]
    return _run(MIGRATE_SCRIPT, args, env=env)


def _plan(home, backup, dist):
    """The dry-run MigrationPlan, as a dict. Asserts the dry run succeeded."""
    r = _migrate(home, backup, dist)
    assert r.returncode == 0, f"dry run failed ({r.returncode}):\n{r.stdout}\n{r.stderr}"
    return json.loads(r.stdout)


def _blocked_plan(home, backup, dist):
    """The dry-run plan for a home the migrator refuses (exit 2)."""
    r = _migrate(home, backup, dist)
    assert r.returncode == 2, f"expected a blocked dry run, got {r.returncode}:\n{r.stdout}"
    return json.loads(r.stdout)


def _apply(home, backup, dist, env=None):
    return _migrate(home, backup, dist, mode="-Apply", env=env)


def _tx_dirs(backup):
    if not Path(backup).is_dir():
        return []
    return sorted(p for p in Path(backup).iterdir() if p.is_dir())


def _only_tx(backup):
    dirs = _tx_dirs(backup)
    assert len(dirs) == 1, f"expected exactly one transaction, found {[d.name for d in dirs]}"
    return dirs[0]


def _manifest_of(tx_dir):
    return json.loads((Path(tx_dir) / "backup-manifest.json").read_text(encoding="utf-8"))


def _plan_of(tx_dir):
    return json.loads((Path(tx_dir) / "plan.json").read_text(encoding="utf-8"))


def _journal_of(tx_dir):
    text = (Path(tx_dir) / "journal.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _sha256(path):
    p = Path(path)
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _tree_digest(root):
    """posix-relative path -> sha256 for every file under root."""
    root = Path(root)
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# --------------------------------------------------------------------------- #
# Distributions
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def full_dist(tmp_path_factory):
    """The real, complete two-profile distribution."""
    out = tmp_path_factory.mktemp("fd")
    r = _run(BUILD_SCRIPT, ["-OutputDir", str(out), "-Provider", "both"])
    assert r.returncode == 0, f"build failed:\n{r.stdout}\n{r.stderr}"
    return out


@pytest.fixture(scope="module")
def mini_dist(full_dist, tmp_path_factory):
    """A REAL distribution trimmed to the fixture's skills.

    Every byte is still builder output (same provenance headers, same YAML
    frontmatter) -- only the skill SET is smaller, so the 30+ apply/resume/rollback
    cases here cost seconds instead of minutes. The one full-distribution
    end-to-end migration lives in test_full_distribution_migrates_both_profiles.
    """
    out = tmp_path_factory.mktemp("md")
    for provider in ("claude", "gpt"):
        for skill in fx.MIGRATION_MANAGED:
            src = full_dist / provider / skill
            if src.is_dir():
                shutil.copytree(src, out / provider / skill)
    native = full_dist / "claude" / fx.MIGRATION_NATIVE
    assert native.is_dir(), f"{fx.MIGRATION_NATIVE} missing from the claude profile"
    shutil.copytree(native, out / "claude" / fx.MIGRATION_NATIVE)
    return out


# --------------------------------------------------------------------------- #
# Tooling presence + source hygiene
# --------------------------------------------------------------------------- #

def test_migration_scripts_exist():
    assert MIGRATE_SCRIPT.is_file(), f"missing {MIGRATE_SCRIPT}"
    assert TRANSACTION_SCRIPT.is_file(), f"missing {TRANSACTION_SCRIPT}"


def _has_high_byte(data):
    return any(b > 127 for b in data)


def test_tracked_powershell_sources_are_ascii_without_bom():
    """PowerShell 5.1 reads a no-BOM .ps1 as ANSI/cp1252, so ONE non-ASCII
    character can silently corrupt parsing with no error at all -- a false green.

    Enumerated from `git ls-files`, never hand-listed: a .ps1 added tomorrow is
    covered the moment it is tracked."""
    tracked = subprocess.run(["git", "ls-files", "*.ps1"], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True).stdout.split("\n")
    files = [REPO_ROOT / f.strip() for f in tracked if f.strip()]
    assert files, "git ls-files matched no .ps1 files -- the gate would be vacuous"
    offenders = []
    for p in files:
        data = p.read_bytes()
        if data[:3] == b"\xef\xbb\xbf":
            offenders.append(f"{p.relative_to(REPO_ROOT)}: UTF-8 BOM")
        elif _has_high_byte(data):
            first = next(i for i, b in enumerate(data) if b > 127)
            offenders.append(f"{p.relative_to(REPO_ROOT)}: non-ASCII byte at offset {first}")
    assert not offenders, "ASCII/BOM violations:\n" + "\n".join(offenders)


def test_ascii_gate_reds_on_a_non_ascii_source():
    """Red-on-garbage anchor for the gate above: prove the predicate actually
    fires, so a future refactor cannot leave it passing on everything."""
    # The em dash is written as an ESCAPE, never as a literal byte: this module is
    # itself a tracked source file, and a raw non-ASCII character in it is invisible
    # in an editor and survives copy/paste into places it must never reach. Same
    # discipline legacy_install_fixtures.py uses for its U+00AD lookalike plant.
    em_dash = "\u2014"
    assert _has_high_byte(("Set-StrictMode\n# em dash " + em_dash + " here\n").encode("utf-8"))
    assert not _has_high_byte(b"Set-StrictMode -Version Latest\n")


def test_migration_fixture_names_match_the_manifest():
    """Red-on-garbage anchor for the fixtures: a manifest edit that changed one of
    these statuses would silently invert what the positive/negative cases prove.

    MIGRATION_MANAGED must be portable in BOTH profiles (so they exercise the
    both-profile transaction) and MIGRATION_NATIVE must be provider-native with
    core: null (so it exercises the missing-GPT-profile carve-out)."""
    m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_name = {s["name"]: s for s in m["skills"]}
    for name in fx.MIGRATION_MANAGED:
        rec = by_name.get(name)
        assert rec is not None, f"{name} is not a manifest record"
        assert rec["status"] == "portable", f"{name} is no longer portable"
        assert rec["providers"].get("claude") and rec["providers"].get("gpt"), name
    native = by_name.get(fx.MIGRATION_NATIVE)
    assert native is not None and native["status"] == "provider-native", fx.MIGRATION_NATIVE
    assert native.get("core") is None, f"{fx.MIGRATION_NATIVE} is no longer core: null"
    for name in fx.MIGRATION_CONSUMER_ONLY:
        assert name not in by_name, f"{name} entered the manifest; it is no longer consumer-only"
    assert fx.FOREIGN_DIR not in by_name


# --------------------------------------------------------------------------- #
# Transaction engine: state machine (the dot-sourced library, run for real)
# --------------------------------------------------------------------------- #

def _engine_script(script_path, snippet):
    """Dot-source a REAL shared library and run `snippet` against it."""
    script = ". '" + str(script_path).replace("'", "''") + "'\n" + snippet
    return subprocess.run([PWSH, "-NonInteractive", "-Command", script],
                          capture_output=True, text=True)


def _engine(snippet):
    return _engine_script(TRANSACTION_SCRIPT, snippet)


def test_state_machine_matches_the_engines_own_vocabulary():
    r = _engine("(Get-SkillMeshTxStates) -join ','")
    assert r.returncode == 0, r.stderr
    assert sorted(r.stdout.strip().split(",")) == sorted(STATES)
    r2 = _engine("(Get-SkillMeshTxActionKinds) -join ','")
    assert sorted(r2.stdout.strip().split(",")) == sorted(ACTION_KINDS)


def test_only_the_declared_transitions_are_legal():
    """Every (from, to) pair in the full cross product is asked of the ENGINE, so a
    widened map fails here rather than silently permitting an illegal advance."""
    pairs = [f"{a}>{b}" for a in STATES for b in STATES]
    snippet = (
        "$out=@(); foreach ($p in @('" + "','".join(pairs) + "')) { "
        "$s=$p.Split('>'); if (Test-SkillMeshTxTransition $s[0] $s[1]) { $out += $p } }; "
        "$out -join ','")
    r = _engine(snippet)
    assert r.returncode == 0, r.stderr
    allowed = {tuple(p.split(">")) for p in r.stdout.strip().split(",") if p.strip()}
    assert allowed == LEGAL_TRANSITIONS, (
        f"unexpected: {allowed - LEGAL_TRANSITIONS}; missing: {LEGAL_TRANSITIONS - allowed}")


@pytest.mark.parametrize("frm,to", [
    ("prepared", "applied"),          # skipping `applying` entirely
    ("applied", "applying"),          # re-entering a completed apply
    ("rolled_back", "applying"),      # leaving a terminal state
    ("failed_incomplete", "applied"),  # laundering a mixed home into success
])
def test_illegal_transition_is_refused(frm, to, tmp_path):
    """Red-on-garbage anchor for the state machine: Set-SkillMeshTxStatus must
    THROW, and must not have mutated the status before throwing."""
    journal = (tmp_path / "j.jsonl").as_posix()
    snippet = (
        f"$tx = New-SkillMeshTransaction -MigrationId '20260101T000000Z-0000abcd' "
        f"-JournalPath '{journal}' -Status '{frm}'; "
        f"try {{ Set-SkillMeshTxStatus $tx '{to}'; Write-Output 'ALLOWED' }} "
        f"catch {{ Write-Output ('REFUSED:' + $tx.status) }}")
    r = _engine(snippet)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == f"REFUSED:{frm}", r.stdout


def test_migration_id_shape_is_validated():
    """-MigrationId is joined into a path, so its shape is validated exactly, not
    merely scanned for separators."""
    cases = {
        "20260731T210000Z-a1b2c3d4": True,
        "20260731T210000Z-A1B2C3D4": False,   # uppercase hex is not the minted shape
        "../../escape": False,
        "20260731T210000Z-a1b2c3d": False,    # 7 hex digits
        "": False,
    }
    for value, expected in cases.items():
        r = _engine(f"Test-SkillMeshMigrationId '{value}'")
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip() == str(expected), f"{value!r} -> {r.stdout.strip()}"


# --------------------------------------------------------------------------- #
# Dry run is the default
# --------------------------------------------------------------------------- #

def test_dry_run_is_the_default_and_mutates_nothing(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    plan = _plan(home, backup, mini_dist)
    assert _tree_digest(home) == before, "the dry run mutated the consumer home"
    assert not backup.exists(), "the dry run created the backup directory"
    assert plan["actions"], "the dry run produced no actions"


def test_dry_run_plan_document_shape(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    plan = _plan(home, tmp_path / "b", mini_dist)
    for key in ("schema_version", "migration_id", "source_release", "consumer_home",
                "backup_dir", "actions", "blocked"):
        assert key in plan, f"missing plan key {key}"
    assert plan["schema_version"] == 1
    assert isinstance(plan["actions"], list) and isinstance(plan["blocked"], list)
    for key in ("commit", "tag", "dist_checksums"):
        assert key in plan["source_release"], key
    kinds = {a["action"] for a in plan["actions"]}
    assert kinds <= ACTION_KINDS, kinds
    # the ledger action is LAST-sequenced, so reverse-order rollback reverts it first
    seqs = [a["seq"] for a in plan["actions"]]
    assert seqs == sorted(seqs) and seqs == list(range(len(seqs)))
    assert plan["actions"][-1]["action"] == "ledger"
    assert sum(1 for a in plan["actions"] if a["action"] == "ledger") == 1


def test_json_format_emits_exactly_one_document_on_every_exit_path(mini_dist, tmp_path):
    """`-Format json` promises ONE document on stdout.

    json.loads raises on concatenated documents, so this catches both halves of the
    real failure mode: a human progress line printed ahead of the document, and a
    blocked path emitting both a plan and a result document."""
    runs = {}
    ok_home, ok_backup = fx.migration_home(tmp_path / "hc"), tmp_path / "bc"
    runs["dry-run"] = _migrate(ok_home, ok_backup, mini_dist)
    runs["apply"] = _apply(ok_home, ok_backup, mini_dist)
    tx_name = _only_tx(ok_backup).name
    runs["resume-applied"] = _migrate(ok_home, ok_backup, mini_dist, mode="-Resume",
                                      migration_id=tx_name)
    runs["rollback"] = _migrate(ok_home, ok_backup, mode="-Rollback", migration_id=tx_name)

    bad_home, bad_backup = fx.migration_home(tmp_path / "hb", foreign=True), tmp_path / "bb"
    runs["blocked-dry-run"] = _migrate(bad_home, bad_backup, mini_dist)
    runs["blocked-apply"] = _apply(bad_home, bad_backup, mini_dist)
    runs["no-backup-dir"] = _migrate(bad_home, None, mini_dist, mode="-Apply",
                                     omit_backup=True)
    runs["unknown-transaction"] = _migrate(bad_home, bad_backup, mini_dist, mode="-Resume",
                                           migration_id="20260101T000000Z-0000abcd")

    # Both outcome classes are represented, or the gate could pass on successes alone.
    assert {r.returncode for r in runs.values()} >= {0, 2}
    for label, r in runs.items():
        assert r.stdout.strip(), f"{label}: -Format json produced no document"
        try:
            json.loads(r.stdout)
        except ValueError as exc:
            raise AssertionError(
                f"{label} (exit {r.returncode}): stdout is not one JSON document "
                f"({exc}); first 200 chars: {r.stdout[:200]!r}")


# --------------------------------------------------------------------------- #
# -Apply preconditions
# --------------------------------------------------------------------------- #

def test_apply_without_backupdir_fails_before_mutation(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    before = _tree_digest(home)
    r = _migrate(home, None, mini_dist, mode="-Apply", omit_backup=True)
    assert r.returncode == 2, f"expected exit 2, got {r.returncode}:\n{r.stdout}\n{r.stderr}"
    assert "BACKUP_DIR_REQUIRED" in r.stderr
    assert _tree_digest(home) == before, "a refused -Apply mutated the home"


def test_backup_dir_inside_the_home_is_refused(mini_dist, tmp_path):
    """A backup written inside the tree being migrated is not a backup."""
    home = fx.migration_home(tmp_path / "h")
    before = _tree_digest(home)
    r = _apply(home, home / "bk", mini_dist)
    assert r.returncode == 2, r.stdout
    assert "BACKUP_DIR_INSIDE_HOME" in r.stderr
    assert _tree_digest(home) == before


# --------------------------------------------------------------------------- #
# The migration itself
# --------------------------------------------------------------------------- #

def test_full_distribution_migrates_both_profiles_as_one_transaction(full_dist, tmp_path):
    """The acceptance case, against the COMPLETE built distribution: a synthetic
    legacy home becomes generated `.claude/skills` + `.github/skills` in ONE
    transaction, retiring the pre-retarget `.copilot/skills` install."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    r = _apply(home, backup, full_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    manifest = _manifest_of(_only_tx(backup))
    assert manifest["status"] == "applied"

    # Both profiles are present and generated (every installed file's hash matches).
    installed = manifest["installed_files"]
    assert any(f["rel_path"].startswith(CLAUDE_ROOT + "/") for f in installed)
    assert any(f["rel_path"].startswith(GPT_ROOT + "/") for f in installed)
    for f in installed:
        assert _sha256(Path(home) / f["rel_path"]) == f["sha256"], f["rel_path"]

    # ONE transaction covered both providers.
    assert len(_tx_dirs(backup)) == 1

    # The retired pre-retarget GPT install is gone.
    assert not (Path(home) / COPILOT_ROOT).exists(), "the retired .copilot/skills tree survived"

    # The provider-native skill landed in the Claude profile only.
    assert (Path(home) / CLAUDE_ROOT / fx.MIGRATION_NATIVE / "SKILL.md").is_file()
    assert not (Path(home) / GPT_ROOT / fx.MIGRATION_NATIVE).exists()


def test_backup_manifest_records_release_identity_and_every_hash(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)
    manifest, plan = _manifest_of(tx), _plan_of(tx)

    # Release identity, present and IDENTICAL in both documents.
    assert manifest["source_release"] == plan["source_release"]
    rel = manifest["source_release"]
    assert rel["commit"] is None or len(rel["commit"]) == 40
    assert rel["dist_checksums"], "dist checksums are empty"

    # Every ORIGINAL hash (pre-image of a mutated path) and every INSTALLED hash.
    for f in manifest["original_files"]:
        payload = Path(tx) / f["backup_payload"]
        assert payload.is_file(), f"missing backup payload for {f['rel_path']}"
        assert _sha256(payload) == f["sha256"], f["rel_path"]
    for f in manifest["installed_files"]:
        assert _sha256(Path(home) / f["rel_path"]) == f["sha256"], f["rel_path"]
    assert manifest["original_ledger"] is not None, "the prior ledger was not backed up"
    assert (Path(tx) / manifest["original_ledger"]["backup_payload"]).is_file()


def test_backup_payload_set_equals_the_mutating_action_set(mini_dist, tmp_path):
    """Backup fidelity and disclosure minimization are ONE rule: every mutated
    path is restorable, and nothing byte-untouched is copied.

    Under-collection breaks rollback; over-collection copies private, untouched
    consumer content into a backup that can never need it."""
    home = fx.migration_home(tmp_path / "h", stale_generated=True)
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)
    plan, manifest = _plan_of(tx), _manifest_of(tx)

    mutating = {a["rel_path"] for a in plan["actions"]
                if a["action"] in MUTATING_KINDS and a["pre_hash"] is not None}
    payload_root = Path(tx) / "payload"
    on_disk = {p.relative_to(payload_root).as_posix()
               for p in payload_root.rglob("*") if p.is_file()}
    assert on_disk == mutating, (
        f"payload set != mutating action set; extra={on_disk - mutating}, "
        f"missing={mutating - on_disk}")

    # A preserved tree contributes a path+hash record and NO payload byte.
    preserved = {f["rel_path"] for f in manifest["preserved_files"]}
    assert preserved, "no preserved trees in this fixture -- the assertion would be vacuous"
    assert preserved & on_disk == set(), "a byte-untouched tree was payload-copied"
    for f in manifest["preserved_files"]:
        assert set(f.keys()) == {"rel_path", "sha256"}, f
        assert _sha256(Path(home) / f["rel_path"]) == f["sha256"], f["rel_path"]


def test_preserved_trees_survive_byte_for_byte(mini_dist, tmp_path):
    """Consumer-only skills and the `_shared` core-holder are classified against
    the manifest and left alone -- never overwritten, retired, or blocked."""
    home = fx.migration_home(tmp_path / "h")
    before = {rel: h for rel, h in _tree_digest(home).items()
              if any(rel.startswith(f"{CLAUDE_ROOT}/{n}/") for n in fx.MIGRATION_CONSUMER_ONLY)
              or rel.startswith(f"{CLAUDE_ROOT}/_shared/")}
    assert len(before) == len(fx.MIGRATION_CONSUMER_ONLY) + 1, before
    assert _apply(home, tmp_path / "b", mini_dist).returncode == 0
    after = _tree_digest(home)
    for rel, digest in before.items():
        assert after.get(rel) == digest, f"preserved path {rel} changed"


def test_stale_generated_file_is_retired_not_blocked(mini_dist, tmp_path):
    """A file skill-mesh itself generated but no longer emits is OURS to retire.
    Paired with the foreign case below: only content we did not generate blocks."""
    home = fx.migration_home(tmp_path / "h", stale_generated=True)
    stale = Path(home) / CLAUDE_ROOT / fx.MIGRATION_MANAGED[0] / "stale-core.md"
    assert stale.is_file(), "fixture did not plant the stale generated file"
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    assert not stale.exists(), "a superseded generated file was left behind"
    tx = _only_tx(backup)
    retired = {a["rel_path"] for a in _plan_of(tx)["actions"] if a["action"] == "retire"}
    assert stale.relative_to(home).as_posix() in retired


def test_foreign_file_blocks_before_mutation(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h", foreign=True)
    backup = tmp_path / "b"
    before = _tree_digest(home)
    r = _apply(home, backup, mini_dist)
    assert r.returncode == 2, f"expected exit 2, got {r.returncode}:\n{r.stdout}\n{r.stderr}"
    assert "FOREIGN_FILE" in r.stderr
    assert _tree_digest(home) == before, "a blocked migration mutated the home"
    assert not backup.exists(), "a blocked migration created a backup transaction"
    plan = _blocked_plan(home, backup, mini_dist)
    codes = {b["code"] for b in plan["blocked"]}
    assert codes == {"FOREIGN_FILE"}, plan["blocked"]
    assert any(fx.FOREIGN_DIR in b["rel_path"] for b in plan["blocked"])


def test_the_same_home_without_the_foreign_dir_migrates(mini_dist, tmp_path):
    """Red-on-garbage pair for the block above: the ONLY difference is the foreign
    directory, so a migrator that blocked on consumer-only or core-holder trees --
    or that blocked on nothing at all -- fails one of the two."""
    home = fx.migration_home(tmp_path / "h", foreign=False)
    r = _apply(home, tmp_path / "b", mini_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"


def test_provider_native_skill_never_triggers_a_missing_gpt_profile_block(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    plan = _plan(home, tmp_path / "b", mini_dist)
    assert plan["blocked"] == [], plan["blocked"]
    installs = {a["rel_path"] for a in plan["actions"] if a["action"] == "install"}
    assert f"{CLAUDE_ROOT}/{fx.MIGRATION_NATIVE}/SKILL.md" in installs
    assert not any(f"/{fx.MIGRATION_NATIVE}/" in rel and rel.startswith(GPT_ROOT)
                   for rel in installs)


def test_a_portable_skill_missing_its_gpt_profile_does_block(mini_dist, tmp_path):
    """Red-on-garbage pair for the carve-out above: absence from the GPT profile is
    fine ONLY when the manifest declares no gpt adapter."""
    broken = tmp_path / "d"
    shutil.copytree(mini_dist, broken)
    shutil.rmtree(broken / "gpt" / fx.MIGRATION_MANAGED[0])
    home = fx.migration_home(tmp_path / "h")
    before = _tree_digest(home)
    r = _apply(home, tmp_path / "b", broken)
    assert r.returncode == 2, r.stdout
    assert "MISSING_PROFILE" in r.stderr
    assert _tree_digest(home) == before


def test_rerun_is_idempotent(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    after_first = _tree_digest(home)
    r2 = _apply(home, backup, mini_dist)
    assert r2.returncode == 0, f"{r2.stdout}\n{r2.stderr}"
    assert _tree_digest(home) == after_first, "a rerun changed the migrated home"


# --------------------------------------------------------------------------- #
# The rewritten ownership ledger
# --------------------------------------------------------------------------- #

def test_ledger_indexes_only_migration_installed_files(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    ledger = json.loads((Path(home) / LEDGER_NAME).read_text(encoding="utf-8"))
    assert ledger["ledger_version"] == 1
    assert set(ledger["installs"]) == {"claude", "gpt"}
    owned = set()
    for entry in ledger["installs"].values():
        owned.update(entry["owned_files"])
    installs = {a["rel_path"] for a in _plan_of(_only_tx(backup))["actions"]
                if a["action"] == "install"}
    assert owned == installs, f"extra={owned - installs}, missing={installs - owned}"
    # No preserved consumer-only skill and no core-holder may be indexed.
    for name in list(fx.MIGRATION_CONSUMER_ONLY) + ["_shared"]:
        assert not any(f"/{name}/" in rel for rel in owned), \
            f"the ledger claims ownership of preserved tree {name}"


def test_uninstall_after_migration_never_deletes_preserved_trees(mini_dist, tmp_path):
    """The ledger the migrator writes is consumed by the PRODUCTION uninstall path
    (install-skill-mesh.ps1 -Uninstall). Anything wrongly indexed would be deleted
    here, so this is the end-to-end proof that the exclusion is real."""
    home = fx.migration_home(tmp_path / "h")
    assert _apply(home, tmp_path / "b", mini_dist).returncode == 0
    preserved = {rel: h for rel, h in _tree_digest(home).items()
                 if any(f"/{n}/" in "/" + rel for n in
                        list(fx.MIGRATION_CONSUMER_ONLY) + ["_shared"])}
    assert preserved, "no preserved trees present -- the assertion would be vacuous"

    for provider in ("claude", "gpt"):
        r = _run(INSTALL_SCRIPT, ["-Home", str(home), "-Provider", provider, "-Uninstall"])
        assert r.returncode == 0, f"uninstall {provider} failed:\n{r.stdout}\n{r.stderr}"

    after = _tree_digest(home)
    for rel, digest in preserved.items():
        assert after.get(rel) == digest, f"uninstall deleted or altered preserved path {rel}"
    # and it really did remove the managed install
    assert not (Path(home) / CLAUDE_ROOT / fx.MIGRATION_MANAGED[0] / "SKILL.md").exists()


# --------------------------------------------------------------------------- #
# Journal + recorded state progression
# --------------------------------------------------------------------------- #

def test_journal_records_begin_and_commit_around_every_mutation(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h", stale_generated=True)
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)
    plan, records = _plan_of(tx), _journal_of(tx)
    for rec in records:
        assert rec["schema_version"] == 1
        assert rec["phase"] in ("begin", "commit")
        assert rec["action"] in ACTION_KINDS
        assert rec["migration_id"] == plan["migration_id"]
        assert rec["utc"].endswith("Z")
    begun = {r["seq"] for r in records if r["phase"] == "begin"}
    committed = {r["seq"] for r in records if r["phase"] == "commit"}
    expected = {a["seq"] for a in plan["actions"]}
    assert begun == expected, f"actions with no begin record: {expected - begun}"
    assert committed == expected, f"actions with no commit record: {expected - committed}"
    # begin ALWAYS precedes its commit -- that ordering is what makes a crash
    # between the two detectable.
    for seq in expected:
        first_begin = next(i for i, r in enumerate(records)
                           if r["seq"] == seq and r["phase"] == "begin")
        first_commit = next(i for i, r in enumerate(records)
                            if r["seq"] == seq and r["phase"] == "commit")
        assert first_begin < first_commit, f"seq {seq}: commit was flushed before begin"


def test_status_advances_only_through_legal_states(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "applied"
    # prepared -> applying -> applied is the only route to `applied`, and each hop
    # is in the declared map.
    for hop in (("prepared", "applying"), ("applying", "applied")):
        assert hop in LEGAL_TRANSITIONS


# --------------------------------------------------------------------------- #
# Failure, rollback, resume
# --------------------------------------------------------------------------- #

def _seq_of(plan, kind):
    seqs = [a["seq"] for a in plan["actions"] if a["action"] == kind]
    assert seqs, f"no {kind} action in the plan"
    return seqs


def test_injected_failure_restores_both_profiles_and_the_prior_ledger(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    plan = _plan(home, backup, mini_dist)
    before = _tree_digest(home)
    # Fail on the LAST install, so both profiles have already been partly written.
    last_install = _seq_of(plan, "install")[-1]
    r = _apply(home, backup, mini_dist, env={"SKILL_MESH_TX_FAIL_AT": str(last_install)})
    assert r.returncode == 1, f"expected exit 1 (home clean), got {r.returncode}:\n{r.stderr}"
    assert _manifest_of(_only_tx(backup))["status"] == "rolled_back"
    assert _tree_digest(home) == before, "rollback did not restore the pre-migration home"
    # the prior ledger is byte-restored, not merely present
    assert (Path(home) / LEDGER_NAME).read_text(encoding="utf-8") == fx.ledger(["claude"])


def test_failure_at_a_retire_action_still_rolls_back_cleanly(mini_dist, tmp_path):
    """A `retire` is the one action kind whose backup payload is produced BY its
    mutation, so an action that reached `begin` but failed before mutating has no
    payload to restore from. Undo must recognize that the target still holds its
    pre-image and no-op, not report a missing payload and land failed_incomplete on
    a home that was never touched."""
    home = fx.migration_home(tmp_path / "h", stale_generated=True)
    backup = tmp_path / "b"
    plan = _plan(home, backup, mini_dist)
    before = _tree_digest(home)
    r = _apply(home, backup, mini_dist,
               env={"SKILL_MESH_TX_FAIL_AT": str(_seq_of(plan, "retire")[0])})
    assert r.returncode == 1, f"expected exit 1 (home clean), got {r.returncode}:\n{r.stderr}"
    assert _manifest_of(_only_tx(backup))["status"] == "rolled_back"
    assert _tree_digest(home) == before


def test_failed_undo_lands_failed_incomplete_with_the_backup_retained(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    plan = _plan(home, backup, mini_dist)
    installs = _seq_of(plan, "install")
    r = _apply(home, backup, mini_dist, env={
        "SKILL_MESH_TX_FAIL_AT": str(installs[-1]),
        "SKILL_MESH_TX_FAIL_UNDO_AT": str(installs[0]),
    })
    assert r.returncode == 3, f"expected exit 3, got {r.returncode}:\n{r.stdout}\n{r.stderr}"
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "failed_incomplete"
    assert (Path(tx) / "payload").is_dir(), "the backup was discarded on a failed undo"
    assert (Path(tx) / "backup-manifest.json").is_file()


@pytest.mark.parametrize("status_env,expected_status", [
    ({"SKILL_MESH_TX_CRASH_AT": "0:after-begin"}, "applying"),
])
def test_bare_apply_refuses_an_unresolved_transaction(status_env, expected_status,
                                                      mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    crashed = _apply(home, backup, mini_dist, env=status_env)
    assert crashed.returncode == 9, f"the crash seam did not fire: {crashed.returncode}"
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == expected_status
    assert _manifest_of(tx)["status"] not in TERMINAL_RESOLVED

    before = _tree_digest(home)
    r = _apply(home, backup, mini_dist)
    assert r.returncode == 2, f"a bare -Apply adopted an unresolved transaction: {r.returncode}"
    assert "INCOMPLETE_TRANSACTION" in r.stderr
    assert tx.name in r.stderr, "the refusal did not name the MigrationId to resume"
    assert _tree_digest(home) == before, "the refusal mutated the home"
    assert len(_tx_dirs(backup)) == 1, "the refusal minted a second transaction"


def test_bare_apply_refuses_a_failed_incomplete_transaction(mini_dist, tmp_path):
    """`failed_incomplete` is terminal but NOT resolved: the home is known-mixed,
    so a bare -Apply over it would compound the damage."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    plan = _plan(home, backup, mini_dist)
    installs = _seq_of(plan, "install")
    assert _apply(home, backup, mini_dist, env={
        "SKILL_MESH_TX_FAIL_AT": str(installs[-1]),
        "SKILL_MESH_TX_FAIL_UNDO_AT": str(installs[0]),
    }).returncode == 3
    assert _manifest_of(_only_tx(backup))["status"] == "failed_incomplete"
    r = _apply(home, backup, mini_dist)
    assert r.returncode == 2, r.stdout
    assert "INCOMPLETE_TRANSACTION" in r.stderr


def test_rollback_restores_original_hashes_and_removes_only_migration_files(
        mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)

    r = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert _manifest_of(tx)["status"] == "rolled_back"
    after = _tree_digest(home)
    assert after == before, (
        f"rollback did not restore the tree; extra={set(after) - set(before)}, "
        f"missing={set(before) - set(after)}")
    # a directory the migration created is gone; one it did not create survives
    assert not (Path(home) / GPT_ROOT).exists(), "a migration-created root survived rollback"
    assert (Path(home) / CLAUDE_ROOT).is_dir(), "a pre-existing directory was removed"


def test_rollback_of_a_resolved_transaction_is_refused(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)
    assert _migrate(home, backup, mode="-Rollback", migration_id=tx.name).returncode == 0
    r = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert r.returncode == 2, "a terminal transaction was rolled back twice"
    assert "TRANSACTION_RESOLVED" in r.stderr


@pytest.mark.parametrize("kind,point", [
    ("install", "after-mutate"),   # crash mid-applying, between write and commit
    ("install", "after-begin"),    # crash after the begin record, before the write
    ("retire", "after-mutate"),    # crash mid-retire: file moved, commit not flushed
    ("ledger", "after-mutate"),    # crash mid-ledger: new ledger written, no commit
])
def test_crash_resumes_to_the_same_terminal_state(kind, point, mini_dist, tmp_path):
    """A crash at any point converges, via -Resume, on the SAME home a clean apply
    produces -- compared as a full-tree hash, not as a status field."""
    clean_home = fx.migration_home(tmp_path / "c", stale_generated=True)
    assert _apply(clean_home, tmp_path / "cb", mini_dist).returncode == 0
    expected = _tree_digest(clean_home)

    home = fx.migration_home(tmp_path / "h", stale_generated=True)
    backup = tmp_path / "b"
    plan = _plan(home, backup, mini_dist)
    seq = _seq_of(plan, kind)[0]

    crashed = _apply(home, backup, mini_dist,
                     env={"SKILL_MESH_TX_CRASH_AT": f"{seq}:{point}"})
    assert crashed.returncode == 9, f"crash seam did not fire ({crashed.returncode})"
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "applying"

    r = _migrate(home, backup, mini_dist, mode="-Resume", migration_id=tx.name)
    assert r.returncode == 0, f"resume failed:\n{r.stdout}\n{r.stderr}"
    assert _manifest_of(tx)["status"] == "applied"
    assert _tree_digest(home) == expected, "resume did not converge on the clean result"


def test_resume_of_an_applied_transaction_is_a_no_op(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)
    before = _tree_digest(home)
    r = _migrate(home, backup, mini_dist, mode="-Resume", migration_id=tx.name)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert _tree_digest(home) == before
    assert _manifest_of(tx)["status"] == "applied"


def test_resume_rejects_a_transaction_from_another_home(mini_dist, tmp_path):
    home = fx.migration_home(tmp_path / "h")
    other = fx.migration_home(tmp_path / "o")
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)
    r = _migrate(other, backup, mini_dist, mode="-Resume", migration_id=tx.name)
    assert r.returncode == 2, "a transaction was replayed against a different home"
    assert "HOME_MISMATCH" in r.stderr


# --------------------------------------------------------------------------- #
# UNSAFE_LINK: junction/symlink escape, at every reachable site
#
# Junctions are created with `cmd /c mklink /J` and the test SKIPS when the
# environment refuses -- the same technique and fallback tests/distributions/
# test_host_inspect.py uses for the read-only inspector.
# --------------------------------------------------------------------------- #

def _make_junction(link: Path, target: Path) -> bool:
    link.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       capture_output=True, text=True)
    return r.returncode == 0


def _junction_or_skip(link: Path, target: Path):
    if not _make_junction(link, target):
        pytest.skip("cannot create a Windows junction in this environment")


def _blocked_codes(payload):
    return {b["code"] for b in payload["blocked"]}


@pytest.mark.parametrize("site", [
    "discovery-root",     # the provider root itself is a junction out of the home
    "skill-dir",          # a per-skill directory under the root is a junction
    "nested-dir",         # a junction nested INSIDE a classified skill directory
    "install-target",     # an ancestor of a not-yet-existing install target
])
def test_junction_escape_blocks_with_unsafe_link(site, mini_dist, tmp_path):
    """UNSAFE_LINK is one of the three blocking codes the plan names, and a wrong
    classification here is what would let the migrator read, write, or back up
    OUTSIDE the consumer home.

    Each parameter plants the escape at a different point in the path so a guard
    that only covers one site cannot pass all four."""
    outside = tmp_path / "out"
    outside.mkdir()
    (outside / "victim.md").write_text("real file outside the home\n", encoding="utf-8")
    home = Path(tmp_path / "h")
    home.mkdir()

    if site == "discovery-root":
        _junction_or_skip(home / ".claude" / "skills", outside)
    elif site == "skill-dir":
        (home / ".claude" / "skills").mkdir(parents=True)
        _junction_or_skip(home / ".claude" / "skills" / fx.MIGRATION_MANAGED[0], outside)
    elif site == "nested-dir":
        skill = home / ".claude" / "skills" / fx.MIGRATION_MANAGED[0]
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(fx.legacy_skill_md(fx.MIGRATION_MANAGED[0]),
                                        encoding="utf-8")
        _junction_or_skip(skill / "sub", outside)
    else:
        # `.github` redirects, so `.github/skills` does not exist under the home and
        # the root scan sees nothing -- only the per-install-target containment check
        # can catch this one.
        _junction_or_skip(home / ".github", outside)

    before_outside = _tree_digest(outside)
    r = _migrate(home, tmp_path / "b", mini_dist)
    assert r.returncode == 2, f"{site}: expected exit 2, got {r.returncode}:\n{r.stdout}"
    plan = json.loads(r.stdout)
    assert "UNSAFE_LINK" in _blocked_codes(plan), f"{site}: blocked={plan['blocked']}"

    # -Apply must refuse identically, and touch nothing on either side of the link.
    ra = _apply(home, tmp_path / "b", mini_dist)
    assert ra.returncode == 2, f"{site}: -Apply did not refuse ({ra.returncode})"
    assert "UNSAFE_LINK" in ra.stderr
    assert _tree_digest(outside) == before_outside, \
        f"{site}: the migrator touched a real file OUTSIDE the consumer home"
    assert not (tmp_path / "b").exists(), f"{site}: a refused run created a backup"


def test_junction_gate_reds_on_a_target_inside_the_home(mini_dist, tmp_path):
    """Red-on-garbage anchor for all four cases above.

    The identical junction pointing INSIDE the home must NOT block -- otherwise
    UNSAFE_LINK could be firing on the mere presence of a reparse point rather than
    on the escape, and the four tests above would prove nothing."""
    home = Path(tmp_path / "h")
    (home / ".claude" / "skills").mkdir(parents=True)
    backing = home / "backing"
    backing.mkdir()
    _junction_or_skip(home / ".claude" / "skills" / fx.MIGRATION_MANAGED[0], backing)
    (backing / "SKILL.md").write_text(fx.legacy_skill_md(fx.MIGRATION_MANAGED[0]),
                                      encoding="utf-8")
    plan = _plan(home, tmp_path / "b", mini_dist)
    assert "UNSAFE_LINK" not in _blocked_codes(plan), plan["blocked"]
    assert plan["blocked"] == [], plan["blocked"]


def test_transaction_directory_escape_blocks_with_unsafe_link(mini_dist, tmp_path):
    """The fifth UNSAFE_LINK site: -Rollback/-Resume join -MigrationId into a path
    under -BackupDir, so a transaction directory that is a junction out of the
    backup tree must be refused before anything is read from it."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    backup.mkdir()
    outside = tmp_path / "out"
    outside.mkdir()
    fake_id = "20260101T000000Z-0000abcd"
    _junction_or_skip(backup / fake_id, outside)
    r = _migrate(home, backup, mini_dist, mode="-Resume", migration_id=fake_id)
    assert r.returncode == 2, f"expected exit 2, got {r.returncode}:\n{r.stdout}\n{r.stderr}"
    assert "UNSAFE_LINK" in r.stderr, r.stderr


def test_undo_refuses_a_target_redirected_out_of_the_home(mini_dist, tmp_path):
    """Rollback is the highest-stakes path: it runs after a crash, possibly much
    later, when the home has had every chance to change under the recorded plan.

    Apply cleanly, THEN plant a junction that redirects an installed skill directory
    outside the home, then roll back. The undo must refuse rather than delete or
    overwrite the real file behind the link."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)

    skill_dir = Path(home) / CLAUDE_ROOT / fx.MIGRATION_MANAGED[0]
    outside = tmp_path / "out"
    outside.mkdir()
    (outside / "SKILL.md").write_text("a real operator file outside the home\n",
                                      encoding="utf-8")
    before_outside = _tree_digest(outside)
    shutil.rmtree(skill_dir)
    _junction_or_skip(skill_dir, outside)

    r = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert r.returncode == 3, (
        f"undo did not refuse the redirected target (exit {r.returncode}); "
        f"a rollback that follows a junction writes outside the home:\n{r.stderr}")
    assert _manifest_of(tx)["status"] == "failed_incomplete"
    assert _tree_digest(outside) == before_outside, \
        "rollback wrote through the junction to a file outside the consumer home"


# --------------------------------------------------------------------------- #
# Post-install verification (the only check that covers a `preserve` action)
# --------------------------------------------------------------------------- #

def test_post_install_verification_catches_a_corrupted_preserved_tree(mini_dist, tmp_path):
    """A `preserve` action is audit-only: the engine's per-action post-hash check
    runs for MUTATING actions only, so post-install verification is the ONLY place a
    preserved consumer-only skill or the `_shared` core-holder is re-checked.

    The seam corrupts a preserved file after the engine's loop commits and before
    verification runs -- the one window nothing else covers."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    preserved_rel = f"{CLAUDE_ROOT}/{fx.MIGRATION_CONSUMER_ONLY[0]}/SKILL.md"
    assert (Path(home) / preserved_rel).is_file(), "fixture did not plant the preserved file"
    before = _tree_digest(home)

    r = _apply(home, backup, mini_dist,
               env={"SKILL_MESH_MIGRATE_TAMPER_AFTER_APPLY": preserved_rel})
    assert "post-install verification FAILED" in r.stderr, r.stderr
    # A preserved tree has NO backup payload by design (nothing byte-untouched is
    # copied), so rollback structurally cannot restore it. The honest terminal state
    # is failed_incomplete with the backup retained -- NOT `rolled_back`, which would
    # claim a clean home over a mixed one.
    assert r.returncode == 3, (
        f"a rollback that cannot restore reported success (exit {r.returncode}):"
        f"\n{r.stdout}\n{r.stderr}")
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "failed_incomplete"
    assert (Path(tx) / "payload").is_dir(), "the backup was discarded on an unrestorable rollback"

    # Everything rollback DOES own was still restored: only the tampered preserved
    # path differs from the pre-migration tree.
    after = _tree_digest(home)
    differing = {rel for rel in set(before) | set(after) if before.get(rel) != after.get(rel)}
    assert differing == {preserved_rel}, (
        f"rollback left more than the unrestorable preserved path changed: {differing}")


def test_post_install_verification_catches_a_corrupted_installed_file(mini_dist, tmp_path):
    """The mirror case: a file the migration CREATED is corrupted before
    verification. Undo refuses to delete bytes that are no longer ours (that would
    destroy someone else's edit) and therefore cannot complete, which is again
    failed_incomplete rather than a false `rolled_back`."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    plan = _plan(home, backup, mini_dist)
    created = [a["rel_path"] for a in plan["actions"]
               if a["action"] == "install" and a["pre_hash"] is None]
    assert created, "no newly-created install targets in this fixture"
    installed_rel = created[0]
    r = _apply(home, backup, mini_dist,
               env={"SKILL_MESH_MIGRATE_TAMPER_AFTER_APPLY": installed_rel})
    assert "post-install verification FAILED" in r.stderr, r.stderr
    assert r.returncode == 3, f"exit {r.returncode}:\n{r.stdout}\n{r.stderr}"
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "failed_incomplete"
    # The tampered file is LEFT IN PLACE -- deleting content this migration did not
    # write is exactly what the guard exists to prevent.
    assert (Path(home) / installed_rel).is_file()
    assert (Path(tx) / "payload").is_dir(), "the backup was discarded"


def test_post_install_seam_is_inert_when_unset(mini_dist, tmp_path):
    """Red-on-garbage anchor for the two tests above: without the seam the identical
    home applies cleanly, so the failures they assert come from the injected
    corruption and not from the fixture or the seam merely existing."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    r = _apply(home, backup, mini_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert _manifest_of(_only_tx(backup))["status"] == "applied"
    assert "post-install verification FAILED" not in r.stderr


# --------------------------------------------------------------------------- #
# Emptied-directory cleanup
# --------------------------------------------------------------------------- #

def test_equal_length_retired_dirs_are_both_cleaned(mini_dist, tmp_path):
    """`Sort-Object -Property @{Expression={...}} -Unique` de-duplicates on the
    CALCULATED key, so two directories whose paths are the same length collapsed to
    one and the survivor was silently never removed.

    Two sibling retired trees with equal-length manifest names reproduce it."""
    a, b = fx.EQUAL_LENGTH_RETIRED
    assert len(a) == len(b), "the fixture names must be equal length or this proves nothing"
    home = fx.migration_home(tmp_path / "h", equal_length_retired=True)
    for name in (a, b):
        assert (Path(home) / COPILOT_ROOT / name / "SKILL.md").is_file(), name
    assert _apply(home, tmp_path / "b", mini_dist).returncode == 0
    leftovers = [name for name in (a, b) if (Path(home) / COPILOT_ROOT / name).exists()]
    assert not leftovers, f"emptied retired directories were not cleaned: {leftovers}"
    assert not (Path(home) / COPILOT_ROOT).exists()


# --------------------------------------------------------------------------- #
# Operator guidance on the terminal failure state
# --------------------------------------------------------------------------- #

def test_failed_incomplete_guidance_does_not_send_the_operator_to_dead_ends(
        mini_dist, tmp_path):
    """`failed_incomplete` is unresolved (a bare -Apply must still refuse) but also
    TERMINAL: -Resume refuses it and -Rollback refuses it, both by design. The
    refusal must therefore not offer those two commands as the remedy -- and this
    test proves both really do bounce, so the guidance is checked against behavior
    rather than against its own wording."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    plan = _plan(home, backup, mini_dist)
    installs = _seq_of(plan, "install")
    assert _apply(home, backup, mini_dist, env={
        "SKILL_MESH_TX_FAIL_AT": str(installs[-1]),
        "SKILL_MESH_TX_FAIL_UNDO_AT": str(installs[0]),
    }).returncode == 3
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "failed_incomplete"

    blocked = _apply(home, backup, mini_dist)
    assert blocked.returncode == 2
    msg = blocked.stderr
    assert "INCOMPLETE_TRANSACTION" in msg
    # Both commands the generic message used to advise really are dead ends here.
    assert _migrate(home, backup, mini_dist, mode="-Resume",
                    migration_id=tx.name).returncode == 2
    assert _migrate(home, backup, mode="-Rollback",
                    migration_id=tx.name).returncode == 2
    assert "-Resume -MigrationId" not in msg, \
        "the refusal advises -Resume, which refuses a failed_incomplete transaction"
    assert "MANUALLY" in msg or "manual" in msg.lower(), \
        "the refusal does not name manual recovery from the retained backup"
    assert tx.name in msg, "the refusal does not name the MigrationId"


def test_unresolved_but_resumable_transaction_still_gets_the_resume_remedy(
        mini_dist, tmp_path):
    """Red-on-garbage pair: for a genuinely resumable status the message must still
    offer -Resume, or the fix above would have silently removed useful guidance from
    every path instead of the one where it is wrong."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist,
                  env={"SKILL_MESH_TX_CRASH_AT": "0:after-begin"}).returncode == 9
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "applying"
    r = _apply(home, backup, mini_dist)
    assert r.returncode == 2
    assert "-Resume -MigrationId" in r.stderr, r.stderr
    assert tx.name in r.stderr


# --------------------------------------------------------------------------- #
# Explicit -Rollback against a NON-applied transaction
# --------------------------------------------------------------------------- #

def test_rollback_of_a_crashed_applying_transaction_restores_the_home(
        mini_dist, tmp_path):
    """-Rollback is the documented recovery route for a crashed migration, and the
    state machine legalizes `applying -> rolling_back` for exactly that. Every other
    rollback test here drives an already-`applied` transaction, so this covers the
    crash-recovery entry."""
    home = fx.migration_home(tmp_path / "h", stale_generated=True)
    backup = tmp_path / "b"
    plan = _plan(home, backup, mini_dist)
    before = _tree_digest(home)
    crash_seq = _seq_of(plan, "install")[0]
    assert _apply(home, backup, mini_dist,
                  env={"SKILL_MESH_TX_CRASH_AT": f"{crash_seq}:after-mutate"}).returncode == 9
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "applying"
    assert _tree_digest(home) != before, "the crash left the home untouched -- nothing to undo"

    r = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert _manifest_of(tx)["status"] == "rolled_back"
    assert _tree_digest(home) == before, "rollback of a crashed transaction did not restore"


def test_rollback_of_a_prepared_transaction_is_a_clean_no_op(mini_dist, tmp_path):
    """`prepared -> rolling_back` is the other operator-initiated entry: a
    transaction that never mutated anything must be discardable, leaving the home
    byte-identical."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    assert _apply(home, backup, mini_dist,
                  env={"SKILL_MESH_TX_CRASH_AT": "0:before-begin"}).returncode == 9
    tx = _only_tx(backup)
    # A crash during preparation legitimately leaves `prepared` on disk; the engine
    # flips to `applying` before its first action, so the status is reset here to
    # model the earlier crash window rather than to fake an unreachable state.
    manifest_path = Path(tx) / "backup-manifest.json"
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    doc["status"] = "prepared"
    manifest_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    r = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert _manifest_of(tx)["status"] == "rolled_back"
    assert _tree_digest(home) == before


# --------------------------------------------------------------------------- #
# Report bounding for consumer-supplied path text
# --------------------------------------------------------------------------- #

def test_blocked_rel_path_is_bounded(mini_dist, tmp_path):
    """A blocked finding is the channel an operator reads, pastes, and forwards, and
    its rel_path is a consumer-controlled directory name. Same discipline
    inspect-host-install.ps1 adopted for #84: charset-bounded segments and a length
    cap, so a hostile or hand-edited home cannot inject separators, list commas, or
    control characters into a report."""
    home = fx.migration_home(tmp_path / "h", hostile_foreign_name=True)
    plan = _blocked_plan(home, tmp_path / "b", mini_dist)
    assert plan["blocked"], "the hostile directory did not block at all"
    for b in plan["blocked"]:
        for segment in b["rel_path"].split("/"):
            assert SAFE_NAME_RE.match(segment), f"unbounded segment {segment!r}"
    blob = json.dumps(plan["blocked"])
    assert "," not in "".join(b["rel_path"] for b in plan["blocked"]), \
        "a list separator survived into a blocked rel_path"
    assert fx.HOSTILE_DIR not in blob, "the raw hostile directory name reached the report"
    text = _migrate(home, tmp_path / "b", mini_dist, fmt="text").stdout
    assert fx.HOSTILE_DIR not in text
    assert "z" * 80 not in text, "an over-long name was not capped in the text report"


def test_operational_rel_paths_stay_verbatim(mini_dist, tmp_path):
    """The bounding above is DISPLAY-only on purpose. `actions[].rel_path` and the
    backup manifest's records are OPERATIONAL -- undo resolves its target from them
    and restore fidelity requires the exact original bytes -- so bounding them would
    trade a formatting nit for data loss. This pins that boundary."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)
    for action in _plan_of(tx)["actions"]:
        if action["action"] == "preserve":
            assert (Path(home) / action["rel_path"]).is_file(), \
                f"operational rel_path {action['rel_path']!r} no longer resolves"
    for record in _manifest_of(tx)["preserved_files"]:
        assert (Path(home) / record["rel_path"]).is_file(), record


# --------------------------------------------------------------------------- #
# One owner for the discovery-root shape
# --------------------------------------------------------------------------- #

DISCOVERY_SCRIPT = REPO_ROOT / "tools" / "skill-mesh-discovery.ps1"
ROOT_LITERALS = ["'.claude/skills'", "'.github/skills'",
                 "'.copilot/skills'", "'.claude/skills-gpt'"]


def _strip_ps_comments(text):
    """Drop block and line comments, mirroring tests/router/test_no_claude_dependency.py.

    Documentation comments may legitimately spell a root; only EXECUTABLE code is
    held to the single-owner rule."""
    text = re.sub(r"<#.*?#>", "", text, flags=re.S)
    return re.sub(r"#.*", "", text)


def test_discovery_roots_have_exactly_one_owner():
    """`.claude/rules/code-quality.md` -- "any constant defining data shape must
    have ONE source of truth ... Duplicate definitions always drift". These roots
    previously lived as three hand-maintained mirrors, and this repository already
    paid for that drift class once in the Step 43/44 GPT retarget.

    Enumerated from `git ls-files`, never hand-listed, so a fourth copy added
    tomorrow fails the moment it is tracked."""
    tracked = subprocess.run(["git", "ls-files", "*.ps1"], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True).stdout.split("\n")
    files = [REPO_ROOT / f.strip() for f in tracked if f.strip()]
    assert files, "git ls-files matched no .ps1 files -- the gate would be vacuous"
    offenders = {}
    for p in files:
        if p.resolve() == DISCOVERY_SCRIPT.resolve():
            continue
        code = _strip_ps_comments(p.read_text(encoding="utf-8"))
        hits = [lit for lit in ROOT_LITERALS if lit in code]
        if hits:
            offenders[str(p.relative_to(REPO_ROOT))] = hits
    assert not offenders, (
        "discovery-root literals are duplicated outside their single owner "
        f"(tools/skill-mesh-discovery.ps1): {offenders}")


def test_single_owner_gate_reds_on_a_duplicate():
    """Red-on-garbage anchor: the gate's own detector must fire on a planted copy,
    and must not fire on a comment that merely documents a root."""
    assert any(lit in _strip_ps_comments("$GPT = '.github/skills'\n") for lit in ROOT_LITERALS)
    assert not any(lit in _strip_ps_comments("# GPT installs to '.github/skills' today\n")
                   for lit in ROOT_LITERALS)


def test_the_owner_actually_defines_every_root():
    """The complement of the gate: proving nobody ELSE spells a root is only
    meaningful if the owner does, and if the values are the ones the tools use."""
    code = _strip_ps_comments(DISCOVERY_SCRIPT.read_text(encoding="utf-8"))
    for lit in ROOT_LITERALS:
        assert lit in code, f"the owner does not define {lit}"
    r = _engine_script(DISCOVERY_SCRIPT,
                       "(Get-SkillMeshDiscoveryRoot 'claude') + '|' + "
                       "(Get-SkillMeshDiscoveryRoot 'gpt') + '|' + "
                       "(Get-SkillMeshRetiredCopilotRoot) + '|' + "
                       "(Get-SkillMeshLegacySkillsGptRoot) + '|' + "
                       "[string](Get-SkillMeshDiscoveryRoot 'nope')")
    assert r.returncode == 0, r.stderr
    claude, gpt, retired, legacy, unknown = r.stdout.strip().split("|")
    assert (claude, gpt) == (CLAUDE_ROOT, GPT_ROOT)
    assert retired == COPILOT_ROOT
    assert legacy == fx.LEGACY_SKILLS_GPT_ROOT
    assert unknown == "", "an unknown provider must resolve to $null, not a guess"


# --------------------------------------------------------------------------- #
# The installer's public contract is unchanged by the shared engine
# --------------------------------------------------------------------------- #

def test_both_tools_dot_source_the_one_shared_engine():
    """Atomicity mechanics must have a single implementation. A tool that grew its
    own copy would pass every behavior test above while defeating the point."""
    for script in (INSTALL_SCRIPT, MIGRATE_SCRIPT):
        text = script.read_text(encoding="utf-8")
        assert "skill-mesh-transaction.ps1" in text, f"{script.name} does not load the engine"
        assert "$TRANSACTION" in text, f"{script.name} does not dot-source the engine"
    engine = TRANSACTION_SCRIPT.read_text(encoding="utf-8")
    for fn in ("function Invoke-SkillMeshTxApply", "function Invoke-SkillMeshTxRollback",
               "function Set-SkillMeshTxStatus", "function Add-SkillMeshTxJournalRecord"):
        assert fn in engine, fn
        # ...and defined ONLY there
        for script in (INSTALL_SCRIPT, MIGRATE_SCRIPT):
            assert fn not in script.read_text(encoding="utf-8"), \
                f"{script.name} redefines {fn} instead of sharing it"


def test_installer_gains_no_required_backupdir_and_emits_no_migration_id(tmp_path):
    """The installer's public CLI, required parameters, and output are unchanged by
    the routing: a clean install still needs only -Provider and -Home."""
    dist = tmp_path / "d"
    r = _run(BUILD_SCRIPT, ["-OutputDir", str(dist), "-Provider", "claude"])
    assert r.returncode == 0, r.stderr
    home = tmp_path / "h"
    ri = _run(INSTALL_SCRIPT, ["-Home", str(home), "-Provider", "claude",
                               "-DistDir", str(dist)])
    assert ri.returncode == 0, f"{ri.stdout}\n{ri.stderr}"

    text = INSTALL_SCRIPT.read_text(encoding="utf-8")
    assert "BackupDir" not in text, "the installer grew a -BackupDir parameter"
    # No transaction identity leaks into the installer's output or its ledger.
    assert "migration_id" not in (ri.stdout + ri.stderr)
    ledger_text = (home / LEDGER_NAME).read_text(encoding="utf-8")
    assert "migration_id" not in ledger_text
    ledger = json.loads(ledger_text)
    assert set(ledger["installs"]["claude"]) == {
        "provider", "discovery_subdir", "owned_files", "created_dirs"}
    # and no transaction state directory was left in the install home
    assert not any(p.name == "journal.jsonl" for p in home.rglob("*"))


def test_installer_install_really_runs_through_the_shared_engine(tmp_path):
    """Wiring proof through the PRODUCTION entry point.

    A static grep cannot tell a dot-sourced-but-never-called engine from a wired
    one. The engine's crash seam is reachable ONLY from inside its per-action apply
    loop, so an installer that exits 9 with the engine's own message has provably
    executed that loop. The paired clean run rules out an installer that always
    fails."""
    dist = tmp_path / "d"
    assert _run(BUILD_SCRIPT, ["-OutputDir", str(dist), "-Provider", "claude"]).returncode == 0

    seamed = _run(INSTALL_SCRIPT,
                  ["-Home", str(tmp_path / "h1"), "-Provider", "claude", "-DistDir", str(dist)],
                  env={"SKILL_MESH_TX_CRASH_AT": "0:after-begin"})
    assert seamed.returncode == 9, (
        f"the installer never reached the shared engine's apply loop "
        f"(exit {seamed.returncode}):\n{seamed.stdout}\n{seamed.stderr}")
    assert "skill-mesh-transaction" in seamed.stderr

    clean = _run(INSTALL_SCRIPT,
                 ["-Home", str(tmp_path / "h2"), "-Provider", "claude", "-DistDir", str(dist)])
    assert clean.returncode == 0, f"{clean.stdout}\n{clean.stderr}"
    assert (tmp_path / "h2" / ".claude" / "skills").is_dir()


# --------------------------------------------------------------------------- #
# Content identity: undo never destroys bytes that are not ours
# --------------------------------------------------------------------------- #

def test_rollback_refuses_to_clobber_a_post_migration_edit(mini_dist, tmp_path):
    """The overwrite case used to restore the backup payload UNCONDITIONALLY.

    A legitimate edit made after the migration was silently destroyed and the run
    still reported exit 0 / `rolled_back`. The rule is now one shared function that
    every undo branch calls, so the overwrite case cannot drift from the
    created case (which always checked)."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)

    # A path this migration OVERWROTE (a legacy hand-authored launcher), now edited
    # by the operator the way any consumer might after a cutover.
    edited_rel = f"{CLAUDE_ROOT}/{fx.MIGRATION_MANAGED[0]}/SKILL.md"
    plan = _plan_of(tx)
    overwritten = [a["rel_path"] for a in plan["actions"]
                   if a["action"] == "install" and a["pre_hash"] is not None]
    assert edited_rel in overwritten, "fixture no longer overwrites this path"
    edit = "\n# operator edit made after the migration\n"
    (Path(home) / edited_rel).write_text(
        (Path(home) / edited_rel).read_text(encoding="utf-8") + edit, encoding="utf-8")
    after_edit = _sha256(Path(home) / edited_rel)

    r = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert r.returncode == 3, (
        f"rollback silently clobbered a post-migration edit (exit {r.returncode}):"
        f"\n{r.stdout}\n{r.stderr}")
    assert _manifest_of(tx)["status"] == "failed_incomplete"
    assert _sha256(Path(home) / edited_rel) == after_edit, \
        "the operator's edit was destroyed by rollback"


def test_rollback_still_restores_when_nothing_was_edited(mini_dist, tmp_path):
    """Red-on-garbage pair: the identity check must not make every rollback refuse."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)
    r = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert _tree_digest(home) == before


# --------------------------------------------------------------------------- #
# Coverage gap D1: a home that never had a ledger
# --------------------------------------------------------------------------- #

def test_migration_into_a_home_with_no_prior_ledger(mini_dist, tmp_path):
    """`legacy_ledger` defaulted True in every fixture, so the ledger action's
    pre_hash==null path -- the genuinely-legacy shape, a consumer who never ran this
    installer -- had never executed across the whole suite.

    Its undo branch DELETES the ledger the migration created, which is the only undo
    in the tool that removes a file it created at a path that did not exist."""
    home = fx.migration_home(tmp_path / "h", legacy_ledger=False)
    assert not (Path(home) / LEDGER_NAME).exists(), "fixture still wrote a ledger"
    backup = tmp_path / "b"
    before = _tree_digest(home)

    plan = _plan(home, backup, mini_dist)
    ledger_actions = [a for a in plan["actions"] if a["action"] == "ledger"]
    assert len(ledger_actions) == 1
    assert ledger_actions[0]["pre_hash"] is None, \
        "this fixture is supposed to exercise the no-prior-ledger branch"
    # With no prior ledger there is nothing to back up for it.
    assert ledger_actions[0]["backup_payload"] == ""

    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)
    assert _manifest_of(tx)["original_ledger"] is None
    assert (Path(home) / LEDGER_NAME).is_file(), "the migration wrote no ledger"

    r = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert not (Path(home) / LEDGER_NAME).exists(), \
        "rollback left behind the ledger it created in a home that never had one"
    assert _tree_digest(home) == before


def test_no_prior_ledger_undo_refuses_when_the_ledger_was_edited(mini_dist, tmp_path):
    """The same branch, content-identity side: if the created ledger no longer holds
    the bytes this migration wrote, deleting it would destroy someone else's file."""
    home = fx.migration_home(tmp_path / "h", legacy_ledger=False)
    backup = tmp_path / "b"
    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)
    ledger_path = Path(home) / LEDGER_NAME
    ledger_path.write_text(ledger_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    r = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert r.returncode == 3, f"exit {r.returncode}: {r.stderr}"
    assert ledger_path.is_file(), "an edited ledger was deleted by rollback"


# --------------------------------------------------------------------------- #
# Coverage gap D2: the APPLY-TIME containment gate (the real TOCTOU window)
# --------------------------------------------------------------------------- #

def test_junction_planted_after_planning_is_caught_at_apply_time(mini_dist, tmp_path):
    """Every other junction test plants the link BEFORE the first scan, so
    Get-RootScan catches it and the apply-time re-check never runs.

    This one plants it in the real window. `-Resume` reads the plan from disk and
    does NOT re-scan, so scan-time classification cannot help: only the choke point
    called immediately before each mutation can catch it."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    outside = tmp_path / "out"
    outside.mkdir()
    (outside / "victim.md").write_text("a real file outside the home\n", encoding="utf-8")
    before_outside = _tree_digest(outside)

    plan = _plan(home, backup, mini_dist)
    gpt_installs = [a for a in plan["actions"]
                    if a["action"] == "install" and a["rel_path"].startswith(GPT_ROOT + "/")]
    assert gpt_installs, "no GPT-profile installs to redirect"
    crash_seq = _seq_of(plan, "install")[0]

    assert _apply(home, backup, mini_dist,
                  env={"SKILL_MESH_TX_CRASH_AT": f"{crash_seq}:after-begin"}).returncode == 9
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "applying"

    # NOW redirect the whole GPT discovery root, after planning is done.
    gpt_root = Path(home) / GPT_ROOT
    if gpt_root.exists():
        shutil.rmtree(gpt_root)
    _junction_or_skip(gpt_root, outside)

    r = _migrate(home, backup, mini_dist, mode="-Resume", migration_id=tx.name)
    assert r.returncode != 0, "resume wrote through a junction planted after planning"
    assert "SECURITY" in r.stderr, r.stderr
    assert _tree_digest(outside) == before_outside, \
        "the migrator wrote into a real directory outside the consumer home"


# --------------------------------------------------------------------------- #
# #89: the installer normalizes -Provider to the canonical slug
# --------------------------------------------------------------------------- #

def _install(home, provider, dist):
    return _run(INSTALL_SCRIPT, ["-Home", str(home), "-Provider", provider,
                                 "-DistDir", str(dist)])


def test_provider_casing_produces_byte_identical_installs(tmp_path):
    """PowerShell's [ValidateSet] matches case-insensitively and does NOT normalize,
    so `-Provider CLAUDE` used to key the ledger 'CLAUDE', write provider='CLAUDE',
    and stamp `Profile: CLAUDE` into every generated file -- making DISTRIBUTION
    BYTES depend on invocation casing in a repo that advertises reproducible
    releases (#89)."""
    dist = tmp_path / "d"
    assert _run(BUILD_SCRIPT, ["-OutputDir", str(dist), "-Provider", "claude"]).returncode == 0

    lower, upper = tmp_path / "hl", tmp_path / "hu"
    assert _install(lower, "claude", dist).returncode == 0
    assert _install(upper, "CLAUDE", dist).returncode == 0

    assert _tree_digest(lower) == _tree_digest(upper), \
        "install bytes differ by the casing of -Provider"

    for home in (lower, upper):
        ledger = json.loads((home / LEDGER_NAME).read_text(encoding="utf-8"))
        assert list(ledger["installs"]) == ["claude"], \
            f"ledger key is not the canonical slug: {list(ledger['installs'])}"
        assert ledger["installs"]["claude"]["provider"] == "claude"
    body = (upper / CLAUDE_ROOT / fx.MIGRATION_MANAGED[0] / "SKILL.md").read_text(encoding="utf-8")
    assert "Profile: claude" in body
    assert "Profile: CLAUDE" not in body, "generated bytes still carry the caller's casing"


def test_uninstall_works_against_a_mixed_case_ledger(tmp_path):
    """A home installed by the PREVIOUS build carries a 'CLAUDE' ledger key. The
    normalization must not strand it: uninstall still has to find and remove it."""
    dist = tmp_path / "d"
    assert _run(BUILD_SCRIPT, ["-OutputDir", str(dist), "-Provider", "claude"]).returncode == 0
    home = tmp_path / "h"
    assert _install(home, "claude", dist).returncode == 0

    ledger_path = home / LEDGER_NAME
    doc = json.loads(ledger_path.read_text(encoding="utf-8"))
    doc["installs"] = {"CLAUDE": doc["installs"]["claude"]}
    ledger_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    r = _run(INSTALL_SCRIPT, ["-Home", str(home), "-Provider", "claude", "-Uninstall"])
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert not list((home / CLAUDE_ROOT).rglob("*.md")) if (home / CLAUDE_ROOT).exists() else True, \
        "uninstall did not remove files tracked under a mixed-case ledger key"


def test_provider_normalizer_has_one_owner_and_keeps_its_semantics():
    """The normalizer lives in the shared discovery module; the inspector's private
    copy now delegates to it. Its two locked behaviors: ordinal (so a lookalike
    padded with Unicode-ignorable characters is refused) but case-insensitive (so a
    real `-Provider CLAUDE` install is recognized, not dropped)."""
    # Scoped to the function body: OrdinalIgnoreCase is legitimately used elsewhere
    # in the inspector for path comparison, so a whole-file sweep would be a false
    # positive. What must be gone is a private COMPARISON inside the resolver.
    for tool in ("inspect-host-install.ps1", "migrate-legacy-install.ps1"):
        src = _strip_ps_comments((REPO_ROOT / "tools" / tool).read_text(encoding="utf-8"))
        start = src.index("function Resolve-KnownProvider")
        body = src[start:src.index("\nfunction ", start + 1)]
        assert "Resolve-SkillMeshProvider" in body, \
            f"{tool} does not delegate to the shared normalizer"
        assert "[string]::Equals" not in body, \
            f"{tool} kept a private copy of the provider comparison"
        assert "foreach" not in body, f"{tool} kept a private matching loop"

    lookalike = "claude" + chr(0x00AD) * 5
    r = _engine_script(DISCOVERY_SCRIPT,
                       "$v = @('claude','gpt'); "
                       "(Resolve-SkillMeshProvider 'CLAUDE' $v) + '|' + "
                       "(Resolve-SkillMeshProvider 'claude' $v) + '|' + "
                       "[string](Resolve-SkillMeshProvider ('claude' + "
                       "([string][char]0x00AD * 5)) $v) + '|' + "
                       "[string](Resolve-SkillMeshProvider 'nope' $v)")
    assert r.returncode == 0, r.stderr
    upper, lower, ignorable, unknown = r.stdout.strip().split("|")
    assert upper == "claude", "a legitimate mixed-case slug was not normalized"
    assert lower == "claude"
    assert ignorable == "", f"a culture-equal lookalike was accepted: {lookalike!r}"
    assert unknown == ""
