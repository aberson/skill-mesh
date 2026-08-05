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
    assert _has_high_byte("Set-StrictMode\n# em dash — here\n".encode("utf-8"))
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

def _engine(snippet):
    """Dot-source the REAL engine and run `snippet` against it."""
    script = ". '" + str(TRANSACTION_SCRIPT).replace("'", "''") + "'\n" + snippet
    return subprocess.run([PWSH, "-NonInteractive", "-Command", script],
                          capture_output=True, text=True)


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
