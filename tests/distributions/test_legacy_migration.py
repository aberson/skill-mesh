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
ACTIVE_RETAIN_ADVISORY = "ACTIVE_MANAGED_FILE_RETAINED"

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


def _resume(home, backup, dist, tx):
    return _migrate(home, backup, dist, mode="-Resume", migration_id=Path(tx).name)


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


def _append_journal_record(tx_dir, plan, action, phase):
    """Append one structurally complete legacy journal record for recovery tests."""
    record = {
        "schema_version": 1,
        "migration_id": plan["migration_id"],
        "seq": action["seq"],
        "action": action["action"],
        "rel_path": action["rel_path"],
        "phase": phase,
        "pre_hash": action["pre_hash"],
        "post_hash": action["post_hash"] if phase == "commit" else None,
        "utc": "2026-08-12T00:00:00.0000000Z",
    }
    with (Path(tx_dir) / "journal.jsonl").open(
            "a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, separators=(",", ":")) + "\n")


def _replace_journal_records(tx_dir, records):
    """Replace a synthetic recovery journal while retaining newline framing."""
    with (Path(tx_dir) / "journal.jsonl").open(
            "w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, separators=(",", ":")) + "\n")


def _write_json(path, document):
    Path(path).write_text(json.dumps(document, indent=2), encoding="utf-8")


def _stage_migrator_checkout(root, manifest_bytes=None):
    """Copy the rollback entry point and its runtime libraries, never repo config."""
    checkout = Path(root) / "checkout"
    rels = (
        "tools/migrate-legacy-install.ps1",
        "tools/skill-mesh-provenance.ps1",
        "tools/skill-mesh-transaction.ps1",
        "tools/skill-mesh-discovery.ps1",
        "runtime/path-guard.ps1",
    )
    for rel in rels:
        source = REPO_ROOT / rel
        target = checkout / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    if manifest_bytes is not None:
        manifest = checkout / "config" / "skill-manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_bytes(manifest_bytes)
    return checkout / "tools" / "migrate-legacy-install.ps1"


def _replace_staged_source_once(path, anchor, replacement):
    """Inject one test-only fault into a staged checkout, never the repo source."""
    source = Path(path).read_text(encoding="utf-8")
    assert source.count(anchor) == 1, (
        f"staged-source injection anchor count was {source.count(anchor)}, expected 1"
    )
    Path(path).write_text(source.replace(anchor, replacement, 1), encoding="utf-8")


def _stage_migrator_library(root):
    """Stage the real migrator definitions but suppress its CLI entry point."""
    script = _stage_migrator_checkout(root)
    anchor = "# -- Entry point --------------------------------------------------------------\n\n"
    _replace_staged_source_once(script, anchor, anchor + "return\n\n")
    return script


def _stage_migrator_with_after_undo_fault(root):
    """Stage a crash/journal-damage probe immediately after the first real undo."""
    script = _stage_migrator_checkout(root)
    transaction = script.parent / "skill-mesh-transaction.ps1"
    anchor = "            & $Undo $action\n"
    injection = anchor + """\
            $testFault = [Environment]::GetEnvironmentVariable(
                'SKILL_MESH_TEST_AFTER_ONE_UNDO')
            if (-not [string]::IsNullOrWhiteSpace($testFault)) {
                [Environment]::SetEnvironmentVariable(
                    'SKILL_MESH_TEST_AFTER_ONE_UNDO', $null)
                $testJournal = [string](Get-SkillMeshTxField $Transaction 'journal_path')
                if ($testFault -eq 'missing') {
                    Remove-Item -LiteralPath $testJournal -Force
                } elseif ($testFault -eq 'truncated') {
                    $testStream = New-Object System.IO.FileStream(
                        $testJournal, [System.IO.FileMode]::Open,
                        [System.IO.FileAccess]::ReadWrite,
                        [System.IO.FileShare]::Read)
                    try {
                        $testStream.SetLength($testStream.Length - 1)
                        $testStream.Flush($true)
                    } finally {
                        $testStream.Dispose()
                    }
                } elseif ($testFault -eq 'crash') {
                    [Console]::Error.WriteLine(
                        'skill-mesh-transaction: TEST INJECTION -- crash after one undo.')
                    [Environment]::Exit(9)
                }
            }
"""
    _replace_staged_source_once(transaction, anchor, injection)
    return script


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
def shared_dist(full_dist, mini_dist, tmp_path_factory):
    """`mini_dist` plus the REAL shared payload the builder emits at each profile root.

    Kept SEPARATE from `mini_dist` on purpose. A distribution that ships no `_shared/`
    is the pre-Step-64 shape and is still a legal input, so the cases built on
    `mini_dist` keep proving the other half of the per-FILE rule: when the shipped set
    is empty, every `_shared` file in the home stays preserved exactly as before.
    """
    out = tmp_path_factory.mktemp("sd") / "d"
    shutil.copytree(mini_dist, out)
    for provider in ("claude", "gpt"):
        src = full_dist / provider / "_shared"
        assert src.is_dir(), f"the built {provider} profile has no _shared payload"
        shutil.copytree(src, out / provider / "_shared")
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


def _synthetic_recovery_documents(begun_seqs):
    """Minimal plan actions + exact begin records for journal grammar tests."""
    migration_id = "20260813T000000Z-a1b2c3d4"
    actions = []
    records = []
    for seq in range(3):
        digest = f"{seq + 1:064x}"
        action = {
            "seq": seq,
            "action": "install",
            "rel_path": f".claude/skills/synthetic-{seq}/SKILL.md",
            "pre_hash": digest,
            "post_hash": f"{seq + 11:064x}",
        }
        actions.append(action)
        if seq in begun_seqs:
            records.append({
                "schema_version": 1,
                "migration_id": migration_id,
                "seq": seq,
                "action": action["action"],
                "rel_path": action["rel_path"],
                "phase": "begin",
                "pre_hash": action["pre_hash"],
                "post_hash": None,
                "utc": "2026-08-13T00:00:00.000Z",
            })
    records.append({
        "schema_version": 1,
        "migration_id": migration_id,
        "phase": "rollback_complete",
        "begun_seqs": list(begun_seqs),
        "utc": "2026-08-13T00:00:01.000Z",
    })
    return migration_id, actions, records


def _validate_synthetic_recovery_journal(staged_migrator, migration_id,
                                         actions, records):
    """Run the real Assert-RecoveryJournal from a CLI-suppressed staged copy."""
    actions_json = json.dumps(actions, separators=(",", ":"))
    records_json = json.dumps(records, separators=(",", ":"))
    snippet = f"""
$actions = @((ConvertFrom-Json -InputObject '{actions_json}'))
$records = @((ConvertFrom-Json -InputObject '{records_json}'))
$bySeq = @{{}}
foreach ($action in $actions) {{ $bySeq[[int]$action.seq] = $action }}
try {{
    Assert-RecoveryJournal $records $bySeq '{migration_id}' 'rolled_back' `
        -RequireRollbackComplete
    Write-Output 'ACCEPTED'
}} catch {{
    Write-Output ('REFUSED:' + $_.Exception.Message)
}}
"""
    return _engine_script(staged_migrator, snippet)


def test_state_machine_matches_the_engines_own_vocabulary():
    r = _engine("(Get-SkillMeshTxStates) -join ','")
    assert r.returncode == 0, r.stderr
    assert sorted(r.stdout.strip().split(",")) == sorted(STATES)
    r2 = _engine("(Get-SkillMeshTxActionKinds) -join ','")
    assert sorted(r2.stdout.strip().split(",")) == sorted(ACTION_KINDS)


@pytest.mark.parametrize("count", [0, 1, 3], ids=["zero", "one", "many"])
def test_rollback_complete_writer_preserves_zero_one_or_many_as_a_json_array(
        count, tmp_path):
    """The shared writer emits the exact v1 transaction-level record shape."""
    journal = (tmp_path / "journal.jsonl").as_posix()
    migration_id = "20260813T000000Z-a1b2c3d4"
    actions = "@()" if count == 0 else "@(" + ",".join(
        f"[PSCustomObject]@{{ seq = {seq} }}" for seq in range(count)
    ) + ")"
    snippet = f"""
[IO.File]::WriteAllText('{journal}', '', (New-Object Text.UTF8Encoding($false)))
$tx = New-SkillMeshTransaction -MigrationId '{migration_id}' `
    -JournalPath '{journal}' -Status 'rolling_back'
$actions = {actions}
Add-SkillMeshTxRollbackCompleteRecord $tx $actions
"""
    written = _engine(snippet)
    assert written.returncode == 0, written.stderr
    raw = (tmp_path / "journal.jsonl").read_text(encoding="utf-8")
    assert raw.endswith("\n") and raw.count("\n") == 1
    record = json.loads(raw)
    assert set(record) == {
        "schema_version", "migration_id", "phase", "begun_seqs", "utc",
    }
    assert type(record["schema_version"]) is int and record["schema_version"] == 1
    assert record["migration_id"] == migration_id
    assert record["phase"] == "rollback_complete"
    assert record["begun_seqs"] == list(range(count))
    assert isinstance(record["begun_seqs"], list)
    assert isinstance(record["utc"], str) and record["utc"].strip()


@pytest.mark.parametrize("begun_seqs", [[], [0], [0, 1, 2]],
                         ids=["zero", "one", "many"])
def test_rollback_complete_validator_accepts_exact_zero_one_or_many_grammar(
        begun_seqs, tmp_path):
    staged = _stage_migrator_library(tmp_path / "stage")
    migration_id, actions, records = _synthetic_recovery_documents(begun_seqs)
    result = _validate_synthetic_recovery_journal(
        staged, migration_id, actions, records,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ACCEPTED", result.stdout


@pytest.mark.parametrize("damage", [
    "case-variant-phase",
    "ignorable-phase",
    "extra-field",
    "missing-utc",
    "nonstring-utc",
    "scalar-seqs",
    "duplicate-seqs",
    "descending-seqs",
    "mismatched-seqs",
    "record-after-marker",
], ids=lambda value: value)
def test_rollback_complete_validator_rejects_malformed_v1_grammar(
        damage, tmp_path):
    staged = _stage_migrator_library(tmp_path / "stage")
    migration_id, actions, records = _synthetic_recovery_documents([0, 1])
    marker = records[-1]
    if damage == "case-variant-phase":
        marker["phase"] = "ROLLBACK_COMPLETE"
    elif damage == "ignorable-phase":
        marker["phase"] = "rollback_complete\u00ad"
    elif damage == "extra-field":
        marker["seq"] = 1
    elif damage == "missing-utc":
        marker.pop("utc")
    elif damage == "nonstring-utc":
        marker["utc"] = 20260813
    elif damage == "scalar-seqs":
        marker["begun_seqs"] = 1
    elif damage == "duplicate-seqs":
        marker["begun_seqs"] = [0, 0, 1]
    elif damage == "descending-seqs":
        marker["begun_seqs"] = [1, 0]
    elif damage == "mismatched-seqs":
        marker["begun_seqs"] = [0]
    elif damage == "record-after-marker":
        records.append(dict(records[0]))
    result = _validate_synthetic_recovery_journal(
        staged, migration_id, actions, records,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("REFUSED:"), result.stdout


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
        f"[IO.File]::WriteAllText('{journal}', '', (New-Object Text.UTF8Encoding($false))); "
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
    for key in ("schema_version", "root_encoding", "migration_id", "source_release", "consumer_home",
                "backup_dir", "actions", "blocked"):
        assert key in plan, f"missing plan key {key}"
    assert plan["schema_version"] == 1
    assert plan["root_encoding"] == "canonical-realpath.v1"
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


def test_new_plan_and_manifest_record_canonical_realpath_roots(
        mini_dist, tmp_path):
    """New artifacts bind authority to canonical roots, even via aliases."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    backup.mkdir()
    home_alias = tmp_path / "ha"
    backup_alias = tmp_path / "ba"
    _junction_or_skip(home_alias, Path(home))
    _junction_or_skip(backup_alias, backup)

    applied = _apply(home_alias, backup_alias, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    plan, manifest = _plan_of(tx), _manifest_of(tx)
    assert plan["root_encoding"] == manifest["root_encoding"] == \
        "canonical-realpath.v1"
    assert plan["consumer_home"] == manifest["consumer_home"]
    assert plan["backup_dir"] == manifest["backup_dir"]

    canonical_home = os.path.normcase(os.path.normpath(str(Path(home).resolve())))
    canonical_backup = os.path.normcase(os.path.normpath(str(backup.resolve())))
    recorded_home = os.path.normcase(os.path.normpath(plan["consumer_home"]))
    recorded_backup = os.path.normcase(os.path.normpath(plan["backup_dir"]))
    assert recorded_home == canonical_home
    assert recorded_backup == canonical_backup
    assert recorded_home != os.path.normcase(os.path.normpath(str(home_alias)))
    assert recorded_backup != os.path.normcase(os.path.normpath(str(backup_alias)))


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


def test_effective_personal_home_is_refused_before_planning(mini_dist, tmp_path):
    """Project-relative `.copilot/skills` must never be inferred inside `~`.

    USERPROFILE and HOME are set before the child PowerShell starts, matching the
    host-resolution boundary rather than mutating this test process's profile.
    The target is a disposable fixture; no real personal path is touched.
    """
    home = fx.migration_home(tmp_path / "profile")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    env = {"USERPROFILE": str(home), "HOME": str(home)}
    for mode in (None, "-Apply"):
        r = _migrate(home, backup, mini_dist, mode=mode, env=env)
        assert r.returncode == 2, f"{r.stdout}\n{r.stderr}"
        assert "PERSONAL_HOME_UNSUPPORTED" in r.stderr
        assert _tree_digest(home) == before
        assert not backup.exists(), "personal-home refusal created a transaction"


def test_personal_home_resume_is_refused_but_explicit_rollback_is_allowed(
        mini_dist, tmp_path):
    """The personal-home guard blocks forward recovery, never emergency undo.

    The transaction is created while the disposable fixture is an ordinary project
    root. Only the recovery processes see it as their effective personal home. A
    Resume would continue destructive project-relative retirement and must refuse;
    Rollback must remain available to reverse already-journaled mutations.
    """
    home = fx.migration_home(tmp_path / "profile")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    plan = _plan(home, tmp_path / "preview", mini_dist)
    install_seq = _seq_of(plan, "install")[0]
    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_TX_CRASH_AT": f"{install_seq}:after-mutate"},
    )
    assert crashed.returncode == 9, f"{crashed.stdout}\n{crashed.stderr}"
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "applying"
    after_crash = _tree_digest(home)
    assert after_crash != before, "the crash did not leave a mutation to recover"

    personal_env = {"USERPROFILE": str(home), "HOME": str(home)}
    resumed = _migrate(
        home, backup, mini_dist, mode="-Resume", migration_id=tx.name,
        env=personal_env,
    )
    assert resumed.returncode == 2, f"{resumed.stdout}\n{resumed.stderr}"
    assert "PERSONAL_HOME_UNSUPPORTED" in resumed.stderr
    assert _manifest_of(tx)["status"] == "applying"
    assert _tree_digest(home) == after_crash, "a refused Resume mutated the home"

    rolled_back = _migrate(
        home, backup, mode="-Rollback", migration_id=tx.name,
        env=personal_env,
    )
    assert rolled_back.returncode == 0, (
        f"personal-home emergency rollback was refused:\n"
        f"{rolled_back.stdout}\n{rolled_back.stderr}"
    )
    assert _manifest_of(tx)["status"] == "rolled_back"
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

    # The retired pre-retarget GPT FILES are gone. Empty ancestors intentionally
    # remain because directories carry no durable byte identity.
    retired_root = Path(home) / COPILOT_ROOT
    assert not any(p.is_file() for p in retired_root.rglob("*")), (
        "the retired .copilot/skills files survived"
    )

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
    """Consumer-only skills are classified against the manifest and left alone --
    never overwritten, retired, or blocked.

    `mini_dist` ships no `_shared/` payload, so BOTH files in the home's `_shared`
    directory are outside the shipped set and both stay preserved. That is the
    empty-set end of the per-FILE rule; the shipped end is covered against
    `shared_dist` below."""
    home = fx.migration_home(tmp_path / "h")
    before = {rel: h for rel, h in _tree_digest(home).items()
              if any(rel.startswith(f"{CLAUDE_ROOT}/{n}/") for n in fx.MIGRATION_CONSUMER_ONLY)
              or rel.startswith(f"{CLAUDE_ROOT}/_shared/")}
    assert len(before) == len(fx.MIGRATION_CONSUMER_ONLY) + 2, before
    assert _apply(home, tmp_path / "b", mini_dist).returncode == 0
    after = _tree_digest(home)
    for rel, digest in before.items():
        assert after.get(rel) == digest, f"preserved path {rel} changed"


def test_stale_generated_file_in_an_active_root_is_retained_with_advisory(
        mini_dist, tmp_path):
    """Approved iteration-3 behavior: loop 2 may warn but never delete.

    The file looks exactly generated and the current distribution no longer emits it,
    but content provenance alone cannot authorize a destructive action inside an
    active discovery root. It therefore appears in no action set, survives Apply
    byte-for-byte, and is named by the stable advisory.
    """
    home = fx.migration_home(tmp_path / "h", stale_generated=True)
    stale = Path(home) / CLAUDE_ROOT / fx.MIGRATION_MANAGED[0] / "stale-core.md"
    assert stale.is_file(), "fixture did not plant the stale generated file"
    before = stale.read_bytes()
    backup = tmp_path / "b"
    rel = stale.relative_to(home).as_posix()
    plan = _plan(home, backup, mini_dist)
    assert all(rel not in _rels(plan, kind) for kind in ACTION_KINDS), \
        "an advisory-only active-root candidate leaked into the action set"

    r = _apply(home, backup, mini_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert stale.read_bytes() == before, "Apply changed the retained active-root file"
    lines = [ln for ln in r.stderr.splitlines() if ACTIVE_RETAIN_ADVISORY in ln]
    assert len(lines) == 1, r.stderr
    assert rel in lines[0], lines[0]


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
# The shipped `_shared` payload (Step 65 / decision D3)
#
# The whole point is that `_shared` is classified PER FILE. Every case below is
# built from ONE home shape that holds both populations at once -- a name the
# builder ships and a name it does not -- so a directory-level reclassification in
# either direction fails at least one of them.
# --------------------------------------------------------------------------- #

SHARED_SHIPPED_REL = f"{CLAUDE_ROOT}/_shared/{fx.SHARED_COLLIDING}"
SHARED_CONSUMER_REL = f"{CLAUDE_ROOT}/_shared/{fx.SHARED_CONSUMER_ONLY}"


def _rels(plan, kind):
    return {a["rel_path"] for a in plan["actions"] if a["action"] == kind}


def _payload_pairs(dist, home):
    """(source, installed target) for every shared-payload file in both profiles."""
    for provider, root in (("claude", CLAUDE_ROOT), ("gpt", GPT_ROOT)):
        for src in sorted((Path(dist) / provider / "_shared").rglob("*")):
            if src.is_file():
                leaf = src.relative_to(Path(dist) / provider / "_shared").as_posix()
                yield src, Path(home) / root / "_shared" / leaf


def test_shared_fixture_names_match_the_built_payload(full_dist):
    """The per-FILE fixtures mean nothing unless the builder really does ship one of
    the two planted names and really does not ship the other. Asserted against the
    REAL build, so a builder change that started shipping `operator-notes.md` (or
    stopped shipping `judge-core.md`) reds here instead of silently defusing every
    per-FILE assertion below into a tautology."""
    for provider in ("claude", "gpt"):
        shipped = {p.name for p in (full_dist / provider / "_shared").iterdir() if p.is_file()}
        assert shipped, f"the {provider} profile shipped no _shared payload at all"
        assert fx.SHARED_COLLIDING in shipped, \
            f"{provider}: the collision fixture names an asset the builder does not ship"
        assert fx.SHARED_CONSUMER_ONLY not in shipped, \
            f"{provider}: the consumer-only fixture names an asset the builder DOES ship"
        # The marker-only populations mean nothing unless the dist really does NOT ship
        # their paths -- a shipped path is classified by the FIRST yes and would never
        # reach the marker branch whose active/retired location split these cases test.
        assert fx.SHARED_STALE_ASSET not in shipped, \
            f"{provider}: the stale-asset fixture names an asset the builder DOES ship"
        assert fx.SHARED_QUOTING_DOC not in shipped, \
            f"{provider}: the quoting-doc fixture names an asset the builder DOES ship"


def test_a_shipped_shared_payload_does_not_block_and_classifies_per_file(shared_dist, tmp_path):
    """A dry run against a home that already holds a hand-authored `_shared/`
    completes, emits no FOREIGN_FILE, and does not trip the latent `$null`
    dereference in the both-profile completeness loop.

    That dereference (`$ManifestMap['_shared'].adapters` under
    `Set-StrictMode -Version Latest`) was unreachable while the dist walk skipped
    `_shared` outright; lifting the first-segment stop is what makes it reachable."""
    home = fx.migration_home(tmp_path / "h")
    r = _migrate(home, tmp_path / "b", shared_dist)
    assert r.returncode == 0, f"exit {r.returncode}:\n{r.stdout}\n{r.stderr}"
    plan = json.loads(r.stdout)
    assert plan["blocked"] == [], plan["blocked"]
    for token in ("PropertyNotFoundException", "cannot be found on this object",
                  "StrictMode"):
        assert token not in r.stderr, f"StrictMode failure on stderr:\n{r.stderr}"

    installs, preserved = _rels(plan, "install"), _rels(plan, "preserve")
    # shipped -> managed, in BOTH profiles
    assert SHARED_SHIPPED_REL in installs, sorted(r for r in installs if "_shared" in r)
    assert f"{GPT_ROOT}/_shared/{fx.SHARED_COLLIDING}" in installs
    # not shipped -> preserved, and never an install target
    assert SHARED_CONSUMER_REL in preserved, sorted(r for r in preserved if "_shared" in r)
    assert SHARED_CONSUMER_REL not in installs


def test_no_relative_path_is_both_preserved_and_installed(shared_dist, tmp_path):
    """A path in BOTH sets is a misreport with no exit-code signal (D3): the preserve
    action records the consumer's bytes as untouched while the install action
    overwrites them, and the rollback drift advisory then names skill-mesh's own new
    bytes as consumer drift. Nothing downstream can see it, so it has to be asserted
    directly."""
    home = fx.migration_home(tmp_path / "h")
    plan = _plan(home, tmp_path / "b", shared_dist)
    preserved, installs = _rels(plan, "preserve"), _rels(plan, "install")
    assert preserved, "no preserve actions -- the intersection would be vacuous"
    assert installs, "no install actions -- the intersection would be vacuous"
    both = {r.lower() for r in preserved} & {r.lower() for r in installs}
    assert both == set(), f"classified BOTH preserved and installed: {sorted(both)}"


def test_apply_installs_the_shared_payload_and_preserves_consumer_shared_files(
        shared_dist, tmp_path):
    """An APPLY run, not a dry run: migrate-legacy-install.ps1's own contract says a
    dry run mutates NOTHING, so it structurally cannot exercise the write path this
    step changes."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    consumer = Path(home) / SHARED_CONSUMER_REL
    consumer_before = _sha256(consumer)
    assert consumer_before is not None, "the fixture planted no consumer _shared file"

    r = _apply(home, backup, shared_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    manifest = _manifest_of(_only_tx(backup))

    # every shipped asset landed byte-exact in both profiles, carrying the marker
    pairs = list(_payload_pairs(shared_dist, home))
    assert pairs, "no payload files to check"
    marker = fx.marker_token()
    for src, dst in pairs:
        assert dst.is_file(), f"{dst} was not installed"
        assert _sha256(dst) == _sha256(src), dst
        head = dst.read_text(encoding="utf-8", errors="replace")[:8192]
        assert marker in head, f"{dst} carries no provenance marker"

    # the consumer's own file in the SAME directory is byte-unchanged...
    assert _sha256(consumer) == consumer_before, "a consumer _shared file was overwritten"
    # ...and is still fully audited: path + hash in the backup manifest, no payload copy
    preserved = {f["rel_path"]: f["sha256"] for f in manifest["preserved_files"]}
    assert SHARED_CONSUMER_REL in preserved, sorted(preserved)
    assert preserved[SHARED_CONSUMER_REL] == consumer_before
    payload_root = Path(_only_tx(backup)) / "payload"
    assert not (payload_root / SHARED_CONSUMER_REL).exists(), \
        "a byte-untouched consumer file was payload-copied into the backup"
    # the ADOPTED collision does carry a pre-image, so -Rollback can put it back
    originals = {f["rel_path"] for f in manifest["original_files"]}
    assert SHARED_SHIPPED_REL in originals, sorted(o for o in originals if "_shared" in o)
    assert (payload_root / SHARED_SHIPPED_REL).is_file()


def test_the_shared_payload_is_indexed_but_consumer_shared_files_are_not(
        shared_dist, tmp_path):
    """The ledger split. An unindexed payload file is an orphan the ownership-safe
    uninstall can never remove; an indexed consumer file is one the uninstall would
    try to delete."""
    home = fx.migration_home(tmp_path / "h")
    assert _apply(home, tmp_path / "b", shared_dist).returncode == 0
    ledger = json.loads((Path(home) / LEDGER_NAME).read_text(encoding="utf-8"))
    owned = set()
    for entry in ledger["installs"].values():
        owned.update(entry["owned_files"])
    assert SHARED_SHIPPED_REL in owned, sorted(o for o in owned if "_shared" in o)
    assert SHARED_CONSUMER_REL not in owned
    for name in fx.MIGRATION_CONSUMER_ONLY:
        assert not any(f"/{name}/" in rel for rel in owned), name


def test_uninstall_removes_the_migrated_shared_payload_and_spares_consumer_files(
        shared_dist, tmp_path):
    """End-to-end through the PRODUCTION uninstall entry point
    (install-skill-mesh.ps1 -Uninstall), which is the only thing that can prove the
    migrator's ledger is actually consumable: a payload file missing from
    `owned_files`, or written without a marker, survives as an orphan."""
    home = fx.migration_home(tmp_path / "h")
    assert _apply(home, tmp_path / "b", shared_dist).returncode == 0
    consumer = Path(home) / SHARED_CONSUMER_REL
    consumer_hash = _sha256(consumer)
    pairs = list(_payload_pairs(shared_dist, home))
    assert all(dst.is_file() for _, dst in pairs), "payload was not installed"

    for provider in ("claude", "gpt"):
        r = _run(INSTALL_SCRIPT, ["-Home", str(home), "-Provider", provider, "-Uninstall"])
        assert r.returncode == 0, f"uninstall {provider} failed:\n{r.stdout}\n{r.stderr}"

    for _, dst in pairs:
        assert not dst.exists(), f"a marker-bearing _shared file survived uninstall: {dst}"
    assert _sha256(consumer) == consumer_hash, "uninstall deleted or altered a consumer file"


def test_a_consumer_shared_file_still_gets_a_rollback_drift_advisory(
        shared_dist, tmp_path):
    """A preserved `_shared` file keeps every audit property the reclassification
    could have silently taken from it -- including the rollback drift advisory, which
    only fires for `preserve` actions. A file swept into the managed set would simply
    stop being mentioned, on a code path whose exit code never changes."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    assert _apply(home, backup, shared_dist).returncode == 0
    tx = _only_tx(backup)
    consumer = Path(home) / SHARED_CONSUMER_REL
    consumer.write_text("# edited by the operator after the migration\n", encoding="utf-8")

    r = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert r.returncode == 0, f"the advisory changed the exit code:\n{r.stderr}"
    assert "ADVISORY" in r.stderr, r.stderr
    assert fx.SHARED_CONSUMER_ONLY in r.stderr, \
        f"the drift advisory never named the preserved _shared file:\n{r.stderr}"


def test_the_adopted_shared_collision_is_disclosed_before_apply(shared_dist, tmp_path):
    """The installer REFUSES a marker-less `_shared` collision and makes the operator
    opt in with -ForceShared -BackupDir. This tool adopts it -- that is what a
    migration is -- but the dry run must SAY so, so the decision is visible before
    -Apply rather than discovered afterwards."""
    home = fx.migration_home(tmp_path / "h")
    r = _migrate(home, tmp_path / "b", shared_dist)
    assert r.returncode == 0, r.stderr
    lines = [ln for ln in r.stderr.splitlines() if "ADVISORY -- adopting" in ln]
    # EXACTLY the one path being adopted. The home holds a `_shared` only under the
    # claude root and only one of its two files is shipped, so a per-directory claim
    # (two lines) or a marker-blind one (a line for every payload file) fails here.
    assert len(lines) == 1, r.stderr
    assert fx.SHARED_COLLIDING in lines[0], lines[0]
    assert fx.SHARED_CONSUMER_ONLY not in lines[0], lines[0]


@pytest.mark.parametrize("replacement", ["marker-less", "marker-bearing", "directory"])
def test_resume_refuses_changed_bytes_at_an_install_target(
        shared_dist, tmp_path, replacement):
    """Resume accepts only the exact pre-image recorded by the plan.

    -Apply re-checks every precondition hash before its first mutation, but -Resume
    runs no precondition pass at all -- so between an interrupted transaction and its
    resume, a consumer file appearing at an install target had nothing standing
    between it and the copy. The action was planned against an ABSENT target, so it
    carries `pre_hash: null` and therefore NO backup payload: the clobber would have
    been unrecoverable, not merely rude. A generated-looking header is deliberately
    included as the second case: provenance can scope a candidate, but cannot prove
    that its current bytes are the ones this transaction planned against."""
    home = fx.migration_home(tmp_path / "h", core_holder=False)
    backup = tmp_path / "b"
    plan = _plan(home, backup, shared_dist)
    action = next(a for a in plan["actions"]
                  if a["action"] == "install" and a["rel_path"] == SHARED_SHIPPED_REL)
    assert action["pre_hash"] is None, \
        "the window under test is an ABSENT target; this fixture already has the file"

    crashed = _apply(home, backup, shared_dist,
                     env={"SKILL_MESH_TX_CRASH_AT": f"{action['seq']}:after-begin"})
    assert crashed.returncode == 9, f"crash seam did not fire ({crashed.returncode})"
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "applying"

    victim = Path(home) / SHARED_SHIPPED_REL
    victim.parent.mkdir(parents=True, exist_ok=True)
    if replacement == "directory":
        victim.mkdir()
        before_tree = _tree_digest(victim)
    else:
        content = (fx.forged_generated_header_doc() if replacement == "marker-bearing"
                   else "# operator content that appeared mid-transaction\n")
        victim.write_text(content, encoding="utf-8")
        before = _sha256(victim)
    if replacement == "marker-bearing":
        assert fx.marker_token() in victim.read_text(encoding="utf-8"), \
            "the marker-bearing branch is vacuous"

    r = _migrate(home, backup, shared_dist, mode="-Resume", migration_id=tx.name)
    assert r.returncode != 0, f"the resume clobbered a {replacement} consumer file"
    assert "SECURITY" in r.stderr, r.stderr
    if replacement == "directory":
        assert victim.is_dir(), "the consumer directory was replaced"
        assert _tree_digest(victim) == before_tree == {}, (
            "Copy-Item treated the target directory as a destination and left a "
            "nested generated file behind"
        )
    else:
        assert _sha256(victim) == before, "the consumer file was overwritten anyway"


def test_the_marker_guard_still_lets_the_planned_adoption_through(shared_dist, tmp_path):
    """Red-on-garbage pair for the guard above: the ONLY difference is whether the
    bytes at the target are the pre-image the plan recorded. A guard that refused
    every marker-less target would break the legacy adoption this tool exists to
    perform, and would fail here."""
    home = fx.migration_home(tmp_path / "h")
    victim = Path(home) / SHARED_SHIPPED_REL
    assert _sha256(victim) is not None, "the fixture planted no marker-less collision"
    r = _apply(home, tmp_path / "b", shared_dist)
    assert r.returncode == 0, f"a planned adoption was refused:\n{r.stdout}\n{r.stderr}"
    assert fx.marker_token() in victim.read_text(encoding="utf-8", errors="replace")


@pytest.mark.parametrize("kind,replacement", [
    ("ledger", "file"),
    ("ledger", "directory"),
    ("retire", "marker-less"),
    ("retire", "marker-bearing"),
    ("retire", "directory"),
])
def test_resume_refuses_changed_ledger_or_retire_preimage(
        kind, replacement, mini_dist, tmp_path):
    """Every destructive resume action accepts only its recorded pre-image."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    plan = _plan(home, tmp_path / "preview", mini_dist)
    action = next(a for a in plan["actions"] if a["action"] == kind)
    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_TX_CRASH_AT": f"{action['seq']}:after-begin"},
    )
    assert crashed.returncode == 9
    tx = _only_tx(backup)
    target = Path(home) / action["rel_path"]
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    if replacement == "directory":
        target.mkdir()
        before = _tree_digest(target)
    else:
        content = (fx.forged_generated_header_doc()
                   if replacement == "marker-bearing"
                   else "# operator bytes written while the transaction was down\n")
        target.write_text(content, encoding="utf-8")
        before = target.read_bytes()

    resumed = _resume(home, backup, mini_dist, tx)
    assert resumed.returncode != 0, f"resume overwrote/deleted {kind} {replacement}"
    assert "SECURITY" in resumed.stderr
    if replacement == "directory":
        assert target.is_dir() and _tree_digest(target) == before
    else:
        assert target.read_bytes() == before


def test_resume_refuses_a_changed_distribution_source_before_target_write(
        mini_dist, tmp_path):
    dist = tmp_path / "dist"
    shutil.copytree(mini_dist, dist)
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    plan = _plan(home, tmp_path / "preview", dist)
    action = next(a for a in plan["actions"]
                  if a["action"] == "install" and a["pre_hash"] is None)
    crashed = _apply(
        home, backup, dist,
        env={"SKILL_MESH_TX_CRASH_AT": f"{action['seq']}:after-begin"},
    )
    assert crashed.returncode == 9
    tx = _only_tx(backup)
    target = Path(home) / action["rel_path"]
    assert not target.exists()
    source = Path(action["source"])
    source.write_text(source.read_text(encoding="utf-8") + "\n# changed dist\n",
                      encoding="utf-8")

    resumed = _resume(home, backup, dist, tx)
    assert resumed.returncode == 1
    assert "distribution source" in resumed.stderr
    assert not target.exists(), "wrong source bytes were copied before refusal"
    assert _manifest_of(tx)["status"] == "rolled_back"


SHARED_STALE_REL = f"{CLAUDE_ROOT}/_shared/{fx.SHARED_STALE_ASSET}"
SHARED_QUOTING_REL = f"{CLAUDE_ROOT}/_shared/{fx.SHARED_QUOTING_DOC}"
ACTIVE_FORGED_REL = (
    f"{CLAUDE_ROOT}/{fx.MIGRATION_MANAGED[0]}/{fx.ACTIVE_FORGED_HEADER_DOC}"
)
SHARED_RETIRED_REL = f"{COPILOT_ROOT}/_shared/{fx.SHARED_COLLIDING}"
SHARED_RETIRED_CONSUMER_REL = f"{COPILOT_ROOT}/_shared/{fx.SHARED_CONSUMER_ONLY}"


def test_rollback_restores_the_adopted_shared_collision_byte_for_byte(shared_dist, tmp_path):
    """THE promise the whole adoption feature rests on, asserted end-to-end.

    `Assert-InstallTargetAdoptable` justifies overwriting a marker-less consumer file at
    a shipped `_shared` path entirely on "the pre-image is backed up and -Rollback puts
    it back byte-for-byte". Every pre-existing rollback case runs against `mini_dist`,
    which ships no `_shared` payload at all -- so `_shared` is always `preserve` there
    and the adopt-then-rollback path was exercised by nothing. Existence of a payload
    file is not the claim; equal BYTES are, so this compares them (and the manifest's
    recorded hash) against the pre-migration original."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    adopted = Path(home) / SHARED_SHIPPED_REL
    before_bytes = adopted.read_bytes()
    before_hash = _sha256(adopted)
    assert fx.marker_token() not in before_bytes.decode("utf-8", "replace"), \
        "the fixture is marker-BEARING; this case is about adopting consumer bytes"

    assert _apply(home, backup, shared_dist).returncode == 0
    tx = _only_tx(backup)
    assert _sha256(adopted) != before_hash, "the adoption never overwrote the file"

    entry = next(f for f in _manifest_of(tx)["original_files"]
                 if f["rel_path"] == SHARED_SHIPPED_REL)
    payload = Path(tx) / "payload" / SHARED_SHIPPED_REL
    assert _sha256(payload) == entry["sha256"], "the payload does not match its manifest hash"
    assert entry["sha256"] == before_hash, "the recorded pre-image is not the original bytes"

    r = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert r.returncode == 0, f"rollback failed:\n{r.stdout}\n{r.stderr}"
    assert _manifest_of(tx)["status"] == "rolled_back"
    assert adopted.read_bytes() == before_bytes, \
        "-Rollback did not restore the adopted _shared file byte-for-byte"


def test_a_consumer_doc_that_quotes_the_header_is_preserved_not_retired(
        shared_dist, tmp_path):
    """A `_shared` file whose SUBJECT is the marker format is the consumer's, not ours.

    `_shared` ownership is content-driven per file, and the marker-only half of that
    rule is the one with a DESTRUCTIVE consequence: a file read as ours that the dist
    does not ship is planned as a `retire` and deleted from the live home. An operator
    doc quoting a whole header verbatim is byte-for-byte indistinguishable from a
    generated file except in WHERE the block sits, so this is the case that decides
    whether the header parser's position anchor is load-bearing or decorative.

    Asserted through -Apply, not only the plan: the dry run mutates nothing by
    contract, so it cannot show that the file survives."""
    home = fx.migration_home(tmp_path / "h", shared_quoting_doc=True)
    backup = tmp_path / "b"
    doc = Path(home) / SHARED_QUOTING_REL
    before = doc.read_bytes()
    assert fx.marker_token() in before.decode("utf-8"), \
        "the fixture doc does not quote the marker at all -- it proves nothing"

    plan = _plan(home, backup, shared_dist)
    assert SHARED_QUOTING_REL in _rels(plan, "preserve"), sorted(_rels(plan, "preserve"))
    assert SHARED_QUOTING_REL not in _rels(plan, "retire"), \
        "an operator doc that quotes the header format was planned for DELETION"
    assert SHARED_QUOTING_REL not in _rels(plan, "install")

    r = _apply(home, backup, shared_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert doc.is_file(), "the operator's own _shared doc was deleted from the home"
    assert doc.read_bytes() == before, "the operator's own _shared doc was rewritten"
    # ...and it is audited as CONSUMER content, not as a superseded asset of ours.
    manifest = _manifest_of(_only_tx(backup))
    assert SHARED_QUOTING_REL in {f["rel_path"] for f in manifest["preserved_files"]}
    assert SHARED_QUOTING_REL not in {f["rel_path"] for f in manifest["original_files"]}


def test_a_forged_header_in_an_active_managed_dir_survives_apply_with_advisory(
        shared_dist, tmp_path):
    """Regression for the exact destructive escape iteration 2 could not parse away.

    This consumer file begins with a byte-exact generated header at an emitter-legal
    position. The shared predicate must accept that shape or it would strand genuine
    payloads, so safety must come from loop 2 having no delete action. Apply must leave
    the bytes intact while the stable advisory names the candidate.
    """
    home = fx.migration_home(tmp_path / "h", active_forged_header=True)
    backup = tmp_path / "b"
    victim = Path(home) / ACTIVE_FORGED_REL
    before = victim.read_bytes()
    assert fx.marker_token() in before.decode("utf-8"), \
        "the fixture does not carry the forged header -- the regression is vacuous"

    plan = _plan(home, backup, shared_dist)
    assert all(ACTIVE_FORGED_REL not in _rels(plan, kind) for kind in ACTION_KINDS), \
        "the forged active-root file leaked into the transaction action set"

    r = _apply(home, backup, shared_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert victim.is_file(), "Apply deleted the consumer's forged-header file"
    assert victim.read_bytes() == before, "Apply rewrote the consumer's forged-header file"
    lines = [ln for ln in r.stderr.splitlines() if ACTIVE_RETAIN_ADVISORY in ln]
    assert len(lines) == 1, r.stderr
    assert ACTIVE_FORGED_REL in lines[0], lines[0]
    assert "left untouched" in lines[0], lines[0]


def test_a_marker_bearing_shared_asset_in_an_active_root_is_retained_with_advisory(
        shared_dist, tmp_path):
    """The approved location split applies inside `_shared` too.

    A payload-shaped file a newer build stopped emitting is generated-looking, but its
    active-root location provides no independent deletion authority. The migrator
    names it for the operator and otherwise leaves it outside every action set.
    """
    home = fx.migration_home(tmp_path / "h", shared_stale_generated=True)
    victim = Path(home) / SHARED_STALE_REL
    before = victim.read_bytes()
    plan = _plan(home, tmp_path / "b", shared_dist)
    assert SHARED_STALE_REL not in _rels(plan, "retire")
    assert SHARED_STALE_REL not in _rels(plan, "preserve")
    assert SHARED_STALE_REL not in _rels(plan, "install")

    r = _apply(home, tmp_path / "b2", shared_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert victim.read_bytes() == before, "Apply changed the retained _shared asset"
    lines = [ln for ln in r.stderr.splitlines() if ACTIVE_RETAIN_ADVISORY in ln]
    assert len(lines) == 1, r.stderr
    assert SHARED_STALE_REL in lines[0], lines[0]


def test_the_same_shared_asset_without_a_marker_is_preserved(shared_dist, tmp_path):
    """Red-on-garbage pair for the case above. Identical home, identical path, identical
    dist -- the ONLY difference is whether the file carries the provenance header. A
    retire rule that keyed on anything else (the directory, the extension, absence from
    the shipped set) would delete this file too."""
    home = fx.migration_home(tmp_path / "h", shared_stale_generated=True)
    victim = Path(home) / SHARED_STALE_REL
    victim.write_text("# not ours\n\nSame path, no provenance header.\n", encoding="utf-8")
    before = victim.read_bytes()

    plan = _plan(home, tmp_path / "b", shared_dist)
    assert SHARED_STALE_REL in _rels(plan, "preserve"), sorted(_rels(plan, "preserve"))
    assert SHARED_STALE_REL not in _rels(plan, "retire")
    assert _apply(home, tmp_path / "b2", shared_dist).returncode == 0
    assert victim.read_bytes() == before, "a marker-less _shared file was touched"


def test_a_marker_bearing_shared_asset_under_the_retired_root_is_retired(
        shared_dist, tmp_path):
    """Marker-only retirement, scenario 2: a `_shared` payload copy left under the
    retired `.copilot/skills` root by a pre-retarget install.

    A DIFFERENT path to the same rule: the retired root is scanned with the same
    `$sharedInstallRels` set, and none of that set's paths can ever match one under it
    -- so the shipped-path yes is structurally unavailable and the marker is the only
    thing that can classify the file. The consumer file planted beside it is what keeps
    this from passing under a directory-wide claim."""
    home = fx.migration_home(tmp_path / "h", shared_retired_copilot=True)
    preview = _migrate(home, tmp_path / "b", shared_dist)
    assert preview.returncode == 0, preview.stderr
    plan = json.loads(preview.stdout)
    retires = _rels(plan, "retire")
    assert SHARED_RETIRED_REL in retires, sorted(retires)
    assert SHARED_RETIRED_CONSUMER_REL not in retires, \
        "a consumer file under the retired root was swept in by a directory-wide claim"
    assert SHARED_RETIRED_CONSUMER_REL in _rels(plan, "preserve")
    disclosures = [ln for ln in preview.stderr.splitlines()
                   if "ADVISORY -- retiring" in ln]
    assert len(disclosures) == 1, preview.stderr
    assert SHARED_RETIRED_REL in disclosures[0], disclosures[0]

    r = _apply(home, tmp_path / "b2", shared_dist)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert not (Path(home) / SHARED_RETIRED_REL).exists(), \
        "a pre-retarget skill-mesh asset survived under the retired root"
    assert (Path(home) / SHARED_RETIRED_CONSUMER_REL).is_file(), \
        "a consumer file under the retired root was deleted"


def test_every_active_shared_candidate_is_named_as_retained(shared_dist, tmp_path):
    """The deliberately rewritten third lock on the old loop-2 retire behavior.

    An active `_shared` candidate must produce the named, path-specific retention
    advisory. It must never reuse the loop-1 `retiring` disclosure, which would tell
    the operator the opposite consequence.
    """
    home = fx.migration_home(tmp_path / "h", shared_stale_generated=True)
    r = _migrate(home, tmp_path / "b", shared_dist)
    assert r.returncode == 0, f"the advisory changed the exit code:\n{r.stderr}"
    lines = [ln for ln in r.stderr.splitlines() if ACTIVE_RETAIN_ADVISORY in ln]
    assert len(lines) == 1, r.stderr
    assert SHARED_STALE_REL in lines[0], lines[0]
    assert "retaining" in lines[0] and "left untouched" in lines[0], lines[0]
    # It names only the candidate -- never a preserved neighbour in the same dir.
    assert fx.SHARED_CONSUMER_ONLY not in lines[0], lines[0]
    assert "ADVISORY -- retiring" not in r.stderr, r.stderr


def test_no_active_retention_advisory_fires_without_a_candidate(shared_dist, tmp_path):
    """Red-on-garbage pair: the named advisory is candidate-driven, not noise."""
    home = fx.migration_home(tmp_path / "h")
    r = _migrate(home, tmp_path / "b", shared_dist)
    assert r.returncode == 0, r.stderr
    assert [ln for ln in r.stderr.splitlines() if ACTIVE_RETAIN_ADVISORY in ln] == [], \
        r.stderr


def test_action_sets_converge_between_run_two_and_run_three(shared_dist, tmp_path):
    """Convergence asserted at the PLAN level, not as a tree digest.

    Two consecutive runs can leave byte-identical trees while planning different
    work -- a path oscillating between the preserve and install sets changes no byte
    and is invisible to a digest comparison. Run 1 legitimately differs (it retires
    the pre-retarget tree and creates directories); runs 2 and 3 must be identical."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    plan1 = _plan(home, backup, shared_dist)
    assert _apply(home, backup, shared_dist).returncode == 0
    plan2 = _plan(home, backup, shared_dist)
    assert _apply(home, backup, shared_dist).returncode == 0
    plan3 = _plan(home, backup, shared_dist)
    assert _apply(home, backup, shared_dist).returncode == 0

    assert plan2["actions"] == plan3["actions"], (
        "the action set did not converge; "
        f"run2-only={[a for a in plan2['actions'] if a not in plan3['actions']]}, "
        f"run3-only={[a for a in plan3['actions'] if a not in plan2['actions']]}")
    assert plan1["actions"] != plan3["actions"], \
        "run 1 planned identical work to run 3 -- the convergence assertion is vacuous"


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
    # No preserved consumer-only skill may be indexed. `_shared` is NOT in this list
    # any more: D3 makes a SHIPPED shared-payload path a legitimate ledger entry, and
    # asserting the whole directory out would re-freeze the very defect Step 65 fixes
    # (an unindexed payload file is an orphan uninstall cannot remove). The per-FILE
    # split is asserted directly in
    # test_the_shared_payload_is_indexed_but_consumer_shared_files_are_not.
    for name in fx.MIGRATION_CONSUMER_ONLY:
        assert not any(f"/{name}/" in rel for rel in owned), \
            f"the ledger claims ownership of preserved tree {name}"
    # `mini_dist` ships no payload, so nothing under `_shared` may be indexed here.
    assert not any("/_shared/" in rel for rel in owned), \
        "a payload-free distribution indexed a _shared path"


def test_uninstall_after_migration_never_deletes_preserved_trees(mini_dist, tmp_path):
    """The ledger the migrator writes is consumed by the PRODUCTION uninstall path
    (install-skill-mesh.ps1 -Uninstall). Anything wrongly indexed would be deleted
    here, so this is the end-to-end proof that the exclusion is real."""
    home = fx.migration_home(tmp_path / "h")
    assert _apply(home, tmp_path / "b", mini_dist).returncode == 0
    # `mini_dist` ships no `_shared` payload, so every file under `_shared` is
    # preserved here too -- see the shared_dist twin for the split case.
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


def test_applied_commit_only_history_is_observational_during_rollback(
        mini_dist, tmp_path):
    """A legacy commit can report post-state without granting delete authority.

    One created install is reduced to commit-only history in an otherwise complete
    applied transaction. Rollback must accept that history, ignore the observational
    seq, and still reverse every action carrying a durable begin record.
    """
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    plan = _plan_of(tx)
    observed = next(
        a for a in plan["actions"]
        if a["action"] == "install" and a["pre_hash"] is None
    )
    observed_target = Path(home) / observed["rel_path"]
    observed_bytes = observed_target.read_bytes()
    assert _sha256(observed_target) == observed["post_hash"]

    records = _journal_of(tx)
    records = [
        record for record in records
        if not (record["seq"] == observed["seq"] and record["phase"] == "begin")
    ]
    _replace_journal_records(tx, records)
    phases = [
        record["phase"] for record in _journal_of(tx)
        if record["seq"] == observed["seq"]
    ]
    assert phases == ["commit"], phases

    rolled_back = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert rolled_back.returncode == 0, (
        f"valid commit-only observation was rejected:\n"
        f"{rolled_back.stdout}\n{rolled_back.stderr}"
    )
    assert _manifest_of(tx)["status"] == "rolled_back"
    assert observed_target.read_bytes() == observed_bytes, (
        "commit-only history granted deletion authority"
    )
    after = _tree_digest(home)
    differing = {
        rel for rel in set(before) | set(after)
        if before.get(rel) != after.get(rel)
    }
    assert differing == {observed["rel_path"]}, (
        f"actual begun actions were not fully reversed: {sorted(differing)}"
    )


def test_unbegun_pre_equals_post_install_remains_a_noop_through_resume_and_rollback(
        mini_dist, tmp_path):
    """A pre==post action needs observation, not manufactured ownership."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    noop_target = (
        Path(home) / CLAUDE_ROOT / fx.MIGRATION_MANAGED[0] / "SKILL.md"
    )
    noop_source = (
        Path(mini_dist) / "claude" / fx.MIGRATION_MANAGED[0] / "SKILL.md"
    )
    shutil.copyfile(noop_source, noop_target)
    before = _tree_digest(home)
    preview = _plan(home, tmp_path / "preview", mini_dist)
    noop = next(
        a for a in preview["actions"]
        if a["action"] == "install"
        and a["rel_path"] == noop_target.relative_to(home).as_posix()
    )
    assert noop["pre_hash"] == noop["post_hash"] == _sha256(noop_target)

    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_TX_CRASH_AT": f"{noop['seq']}:before-begin"},
    )
    assert crashed.returncode == 9, f"{crashed.stdout}\n{crashed.stderr}"
    tx = _only_tx(backup)
    assert _tree_digest(home) != before, "no actual begun action preceded the no-op"
    assert not any(
        record["seq"] == noop["seq"] and record["phase"] == "begin"
        for record in _journal_of(tx)
    )

    resumed = _resume(home, backup, mini_dist, tx)
    assert resumed.returncode == 0, f"{resumed.stdout}\n{resumed.stderr}"
    assert _manifest_of(tx)["status"] == "applied"
    phases = [
        record["phase"] for record in _journal_of(tx)
        if record["seq"] == noop["seq"]
    ]
    assert phases == ["commit"], (
        "Resume minted begin authority for a byte-identical no-op: "
        f"{phases}"
    )
    noop_bytes = noop_target.read_bytes()

    durable_plan = _plan_of(tx)
    actually_created = next(
        a for a in durable_plan["actions"]
        if a["action"] == "install"
        and a["pre_hash"] is None
        and any(
            record["seq"] == a["seq"] and record["phase"] == "begin"
            for record in _journal_of(tx)
        )
    )
    created_target = Path(home) / actually_created["rel_path"]
    assert created_target.is_file()

    rolled_back = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert rolled_back.returncode == 0, f"{rolled_back.stdout}\n{rolled_back.stderr}"
    assert _manifest_of(tx)["status"] == "rolled_back"
    assert noop_target.read_bytes() == noop_bytes
    assert not created_target.exists(), "an actually begun install survived rollback"
    assert _tree_digest(home) == before


@pytest.mark.parametrize("status", ["applying", "applied"])
@pytest.mark.parametrize("damage", ["missing", "non-leaf", "malformed"])
def test_recovery_fails_closed_for_missing_nonleaf_or_malformed_journal(
        status, damage, mini_dist, tmp_path):
    """Non-prepared recovery requires a readable, framed, valid journal."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    if status == "applying":
        preview = _plan(home, tmp_path / "preview", mini_dist)
        seq = _seq_of(preview, "install")[0]
        started = _apply(
            home, backup, mini_dist,
            env={"SKILL_MESH_TX_CRASH_AT": f"{seq}:after-mutate"},
        )
        assert started.returncode == 9, f"{started.stdout}\n{started.stderr}"
    else:
        started = _apply(home, backup, mini_dist)
        assert started.returncode == 0, f"{started.stdout}\n{started.stderr}"
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == status
    before_recovery = _tree_digest(home)
    journal = Path(tx) / "journal.jsonl"
    if damage == "missing":
        journal.unlink()
    elif damage == "non-leaf":
        journal.unlink()
        journal.mkdir()
    else:
        journal.write_bytes(b"{this is not json}\n")

    if status == "applying":
        recovered = _resume(home, backup, mini_dist, tx)
    else:
        recovered = _migrate(
            home, backup, mode="-Rollback", migration_id=tx.name,
        )
    assert recovered.returncode == 2, (
        f"{status}/{damage} recovery did not fail closed:\n"
        f"{recovered.stdout}\n{recovered.stderr}"
    )
    assert "INVALID_JOURNAL" in recovered.stderr
    assert _manifest_of(tx)["status"] == status
    assert _tree_digest(home) == before_recovery, "journal refusal mutated the home"


@pytest.mark.parametrize("damage", ["empty", "truncated"])
def test_applied_rollback_rejects_empty_or_truncated_history_without_false_success(
        damage, mini_dist, tmp_path):
    """Missing undo authority can never yield rolled_back over applied bytes."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    before_apply = _tree_digest(home)
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    applied_tree = _tree_digest(home)
    assert applied_tree != before_apply, "fixture has no applied mutations"
    journal = Path(tx) / "journal.jsonl"
    if damage == "empty":
        journal.write_bytes(b"")
    else:
        original = journal.read_bytes()
        assert original.endswith(b"\n")
        journal.write_bytes(original[:-1])

    rolled_back = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert rolled_back.returncode == 2, (
        f"{damage} history reported successful rollback:\n"
        f"{rolled_back.stdout}\n{rolled_back.stderr}"
    )
    assert "INVALID_JOURNAL" in rolled_back.stderr
    assert json.loads(rolled_back.stdout)["status"] == "blocked"
    assert _manifest_of(tx)["status"] == "applied"
    assert _tree_digest(home) == applied_tree


@pytest.mark.parametrize("terminal_status,mode", [
    ("applied", "resume"),
    ("applied", "rollback"),
    ("rolled_back", "resume"),
    ("rolled_back", "rollback"),
])
def test_explicit_recovery_validates_a_terminal_journal_before_resolved_response(
        terminal_status, mode, mini_dist, tmp_path):
    """A terminal manifest label never bypasses explicit recovery validation."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    if terminal_status == "rolled_back":
        completed = _migrate(
            home, backup, mode="-Rollback", migration_id=tx.name,
        )
        assert completed.returncode == 0, f"{completed.stdout}\n{completed.stderr}"
        assert _journal_of(tx)[-1]["phase"] == "rollback_complete"
    assert _manifest_of(tx)["status"] == terminal_status

    journal = Path(tx) / "journal.jsonl"
    journal.unlink()
    before_recovery = _tree_digest(home)
    if mode == "resume":
        recovered = _migrate(
            home, backup, mini_dist, mode="-Resume", migration_id=tx.name,
        )
    else:
        recovered = _migrate(
            home, backup, mode="-Rollback", migration_id=tx.name,
        )

    assert recovered.returncode == 2, (
        f"{terminal_status}/{mode} trusted a label over its missing journal:\n"
        f"{recovered.stdout}\n{recovered.stderr}"
    )
    assert "INVALID_JOURNAL" in recovered.stderr
    assert "already applied (no-op)" not in recovered.stderr
    assert "TRANSACTION_RESOLVED" not in recovered.stderr
    assert json.loads(recovered.stdout)["status"] == "blocked"
    assert _manifest_of(tx)["status"] == terminal_status
    assert _tree_digest(home) == before_recovery


def test_recovery_rejects_reordered_plan_action_phases_before_mutation(
        mini_dist, tmp_path):
    """Recovery preserves backup/preserve/retire/install/ledger phase order."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    before_recovery = _tree_digest(home)
    plan = _plan_of(tx)
    retire_index = next(
        i for i, action in enumerate(plan["actions"])
        if action["action"] == "retire"
    )
    install_index = next(
        i for i, action in enumerate(plan["actions"])
        if action["action"] == "install"
    )
    assert retire_index < install_index
    install = plan["actions"].pop(install_index)
    plan["actions"].insert(retire_index, install)
    for seq, action in enumerate(plan["actions"]):
        action["seq"] = seq
    _write_json(Path(tx) / "plan.json", plan)

    rolled_back = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert rolled_back.returncode == 2, (
        f"reordered action phases reached rollback:\n"
        f"{rolled_back.stdout}\n{rolled_back.stderr}"
    )
    assert "INVALID_TRANSACTION" in rolled_back.stderr
    assert "do not preserve backup/preserve/retire/install/ledger order" in rolled_back.stderr
    assert _manifest_of(tx)["status"] == "applied"
    assert _tree_digest(home) == before_recovery


@pytest.mark.parametrize("invalidity", ["unknown-provider", "wrong-root"])
def test_recovery_rejects_invalid_install_provider_or_target_root_before_mutation(
        invalidity, mini_dist, tmp_path):
    """Serialized provider text cannot redirect a recovery install action."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    before_recovery = _tree_digest(home)
    plan = _plan_of(tx)
    install = next(
        action for action in plan["actions"]
        if action["action"] == "install" and action["provider"] == "claude"
    )
    assert install["rel_path"].startswith(CLAUDE_ROOT + "/")
    install["provider"] = "not-a-provider" if invalidity == "unknown-provider" else "gpt"
    _write_json(Path(tx) / "plan.json", plan)

    rolled_back = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert rolled_back.returncode == 2, (
        f"{invalidity} install metadata reached rollback:\n"
        f"{rolled_back.stdout}\n{rolled_back.stderr}"
    )
    assert "INVALID_TRANSACTION" in rolled_back.stderr
    assert "invalid provider or target root" in rolled_back.stderr
    assert _manifest_of(tx)["status"] == "applied"
    assert _tree_digest(home) == before_recovery


def test_encoded_recovery_rejects_retire_outside_retired_project_root(
        mini_dist, tmp_path):
    """Only unencoded legacy artifacts may carry restorative active-root retires."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    before_recovery = _tree_digest(home)
    plan = _plan_of(tx)
    assert plan["root_encoding"] == "canonical-realpath.v1"
    retire = next(action for action in plan["actions"]
                  if action["action"] == "retire")
    retire["rel_path"] = f"{CLAUDE_ROOT}/forged-active-retire.md"
    _write_json(Path(tx) / "plan.json", plan)

    rolled_back = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert rolled_back.returncode == 2, (
        f"encoded active-root retire reached rollback:\n"
        f"{rolled_back.stdout}\n{rolled_back.stderr}"
    )
    assert "INVALID_TRANSACTION" in rolled_back.stderr
    assert "outside the retired project root" in rolled_back.stderr
    assert _manifest_of(tx)["status"] == "applied"
    assert _tree_digest(home) == before_recovery


@pytest.mark.parametrize("mode", ["resume", "rollback"])
@pytest.mark.parametrize("aliased_root", ["home", "backup"])
def test_legacy_schema_v1_alias_roots_are_refused_before_recovery_mutation(
        mode, aliased_root, mini_dist, tmp_path):
    """Unencoded legacy authority cannot be rebound through a root junction.

    Pre-policy schema-v1 documents carry no root_encoding discriminator. A lexical
    Home or BackupDir alias that differs from the selected canonical root is
    ambiguous: it could now point at a replacement project. Both forward recovery
    and emergency undo must refuse without changing either home bytes or status.
    """
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    preview = _plan(home, tmp_path / "preview", mini_dist)
    install_seq = _seq_of(preview, "install")[0]
    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_TX_CRASH_AT": f"{install_seq}:after-mutate"},
    )
    assert crashed.returncode == 9, f"{crashed.stdout}\n{crashed.stderr}"
    tx = _only_tx(backup)
    plan, manifest = _plan_of(tx), _manifest_of(tx)
    assert manifest["status"] == "applying"
    canonical_home = plan["consumer_home"]
    canonical_backup = plan["backup_dir"]

    home_alias = tmp_path / "ha"
    backup_alias = tmp_path / "ba"
    _junction_or_skip(home_alias, Path(home))
    _junction_or_skip(backup_alias, backup)
    plan.pop("root_encoding")
    manifest.pop("root_encoding")
    plan["consumer_home"] = (
        str(home_alias) if aliased_root == "home" else canonical_home
    )
    manifest["consumer_home"] = plan["consumer_home"]
    plan["backup_dir"] = (
        str(backup_alias) if aliased_root == "backup" else canonical_backup
    )
    manifest["backup_dir"] = plan["backup_dir"]
    _write_json(Path(tx) / "plan.json", plan)
    _write_json(Path(tx) / "backup-manifest.json", manifest)

    home_before = _tree_digest(home)
    manifest_path = Path(tx) / "backup-manifest.json"
    manifest_before = manifest_path.read_bytes()
    plan_before = (Path(tx) / "plan.json").read_bytes()
    if mode == "resume":
        recovered = _migrate(
            home, backup, mini_dist, mode="-Resume", migration_id=tx.name,
        )
    else:
        recovered = _migrate(
            home, backup, mode="-Rollback", migration_id=tx.name,
        )

    assert recovered.returncode == 2, (
        f"legacy {aliased_root} alias reached {mode}:\n"
        f"{recovered.stdout}\n{recovered.stderr}"
    )
    assert "LEGACY_ALIAS_ROOT_UNSUPPORTED" in recovered.stderr
    assert json.loads(recovered.stdout)["status"] == "blocked"
    assert _tree_digest(home) == home_before
    assert manifest_path.read_bytes() == manifest_before
    assert (Path(tx) / "plan.json").read_bytes() == plan_before
    assert _manifest_of(tx)["status"] == "applying"


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

    # This is the GENUINELY-mixed branch: an undo of a MUTATED path threw, so bytes
    # this tool wrote are still on disk. D2 corrects the false-MIXED message for a
    # preserve-only remainder while requiring it stay intact here -- "without
    # weakening it for a genuine undo failure that really did leave the home mixed".
    # Without this positive assertion, an over-correction that stripped the wording
    # from this branch too would pass the suite, since every other MIXED assertion in
    # this file is a negative one.
    assert "MIXED" in r.stderr, r.stderr
    assert "recover from it manually" in r.stderr, r.stderr


@pytest.mark.parametrize("kind", ["retire", "install", "ledger"])
def test_explicit_rollback_refuses_a_corrupt_restore_payload(
        kind, mini_dist, tmp_path):
    """A backup path is not restore authority unless its bytes still match.

    Each action here has a real pre-image. Corrupting that action's external
    payload after Apply must leave the current target untouched (or absent for a
    retire), retain the evidence, and publish failed_incomplete -- never copy the
    attacker-controlled replacement into the project.
    """
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    plan = _plan_of(tx)
    candidates = [
        a for a in plan["actions"]
        if a["action"] == kind and a["pre_hash"] is not None
    ]
    assert candidates, f"fixture has no restorable {kind} action"
    action = candidates[0]
    target = Path(home) / action["rel_path"]
    payload = Path(tx) / action["backup_payload"]
    assert payload.is_file(), f"missing payload for {action['rel_path']}"
    assert _sha256(payload) == action["pre_hash"]

    if kind == "retire":
        assert not target.exists(), "the retire action did not reach its post-state"
        target_after_apply = None
    else:
        assert _sha256(target) == action["post_hash"]
        target_after_apply = target.read_bytes()

    corrupt = b"corrupt payload bytes that the transaction never backed up\n"
    assert hashlib.sha256(corrupt).hexdigest() != action["pre_hash"]
    payload.write_bytes(corrupt)

    rolled_back = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert rolled_back.returncode == 3, (
        f"corrupt {kind} payload was accepted:\n"
        f"{rolled_back.stdout}\n{rolled_back.stderr}"
    )
    assert _manifest_of(tx)["status"] == "failed_incomplete"
    assert payload.read_bytes() == corrupt, "failed recovery discarded its evidence"
    if kind == "retire":
        assert not target.exists(), "corrupt payload bytes were restored to the target"
    else:
        assert target.read_bytes() == target_after_apply
        assert target.read_bytes() != corrupt, "corrupt payload bytes reached the target"


@pytest.mark.parametrize("redirected", [False, True], ids=["unaliased", "redirected"])
def test_schema_v1_active_root_retire_restore_requires_its_recorded_canonical_path(
        redirected, mini_dist, tmp_path):
    """Legacy active-root retire actions are restorative-only and alias-bound.

    Step 65 no longer creates this action shape, but a schema-v1 transaction may
    already contain one. Its verified payload can be restored at the unaliased
    recorded active path. A new in-home junction to a different active path must
    instead fail incomplete without writing the payload through the redirect.
    """
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    plan = _plan_of(tx)
    manifest = _manifest_of(tx)
    assert plan["schema_version"] == manifest["schema_version"] == 1
    # This fixture models a transaction written before Step 65's canonical-root
    # discriminator existed. Keeping the new encoding while inventing the old
    # active-root retire shape would create an internally impossible artifact.
    assert plan.pop("root_encoding") == "canonical-realpath.v1"
    assert manifest.pop("root_encoding") == "canonical-realpath.v1"

    retire = next(a for a in plan["actions"] if a["action"] == "retire")
    old_rel = retire["rel_path"]
    legacy_rel = ".agents/skills/legacy-v1-retire/legacy.md"
    retire["rel_path"] = legacy_rel
    original = next(
        entry for entry in manifest["original_files"]
        if entry["rel_path"] == old_rel
    )
    original["rel_path"] = legacy_rel
    records = _journal_of(tx)
    for record in records:
        if record["seq"] == retire["seq"]:
            assert record["rel_path"] == old_rel
            record["rel_path"] = legacy_rel
    _write_json(Path(tx) / "plan.json", plan)
    _write_json(Path(tx) / "backup-manifest.json", manifest)
    _replace_journal_records(tx, records)

    payload = Path(tx) / retire["backup_payload"]
    payload_bytes = payload.read_bytes()
    assert hashlib.sha256(payload_bytes).hexdigest() == retire["pre_hash"]
    target = Path(home) / legacy_rel
    assert not target.exists()
    redirect_leaf = None
    if redirected:
        redirect_parent = Path(home) / CLAUDE_ROOT / "legacy-v1-restore-sink"
        redirect_parent.mkdir(parents=True)
        redirect_leaf = redirect_parent / target.name
        _junction_or_skip(target.parent, redirect_parent)
        assert not target.exists() and not redirect_leaf.exists()

    rolled_back = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    if not redirected:
        assert rolled_back.returncode == 0, (
            f"unaliased schema-v1 restore failed:\n"
            f"{rolled_back.stdout}\n{rolled_back.stderr}"
        )
        assert _manifest_of(tx)["status"] == "rolled_back"
        assert target.read_bytes() == payload_bytes
    else:
        assert rolled_back.returncode == 3, (
            f"redirected schema-v1 restore was not refused:\n"
            f"{rolled_back.stdout}\n{rolled_back.stderr}"
        )
        assert _manifest_of(tx)["status"] == "failed_incomplete"
        assert "SECURITY" in rolled_back.stderr and "legacy retire restore" in rolled_back.stderr
        assert not redirect_leaf.exists(), "payload bytes were written through the active alias"
        assert not target.exists()
    assert payload.read_bytes() == payload_bytes, "recovery payload was discarded"


@pytest.mark.parametrize("manifest_state", ["missing", "malformed"])
def test_explicit_rollback_does_not_depend_on_the_current_checkout_manifest(
        manifest_state, mini_dist, tmp_path):
    """A staged recovery checkout can undo without readable planning config."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    assert _tree_digest(home) != before

    manifest_bytes = None
    if manifest_state == "malformed":
        manifest_bytes = b"{not valid manifest json}\n"
    staged_script = _stage_migrator_checkout(
        tmp_path / "stage", manifest_bytes=manifest_bytes,
    )
    staged_manifest = staged_script.parents[1] / "config" / "skill-manifest.json"
    if manifest_state == "missing":
        assert not staged_manifest.exists()
    else:
        assert staged_manifest.read_bytes() == manifest_bytes

    rolled_back = _run(staged_script, [
        "-Home", str(home),
        "-BackupDir", str(backup),
        "-Rollback",
        "-MigrationId", tx.name,
        "-Format", "json",
    ])
    assert rolled_back.returncode == 0, (
        f"rollback depended on {manifest_state} checkout config:\n"
        f"{rolled_back.stdout}\n{rolled_back.stderr}"
    )
    assert _manifest_of(tx)["status"] == "rolled_back"
    assert _tree_digest(home) == before


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


@pytest.mark.parametrize("document", ["plan.json", "backup-manifest.json"])
@pytest.mark.parametrize("damage", ["missing", "malformed"])
def test_bare_apply_refuses_prior_transaction_with_unreadable_authority_metadata(
        document, damage, mini_dist, tmp_path):
    """Damaged matching-home metadata never makes an unresolved run disappear."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_TX_CRASH_AT": "0:after-begin"},
    )
    assert crashed.returncode == 9, f"{crashed.stdout}\n{crashed.stderr}"
    tx = _only_tx(backup)
    plan = _plan_of(tx)
    assert Path(plan["consumer_home"]).resolve() == Path(home).resolve()
    before_retry = _tree_digest(home)

    authority = Path(tx) / document
    if damage == "missing":
        authority.unlink()
    else:
        authority.write_bytes(b"{not valid recovery metadata}\n")

    retried = _apply(home, backup, mini_dist)
    assert retried.returncode == 2, (
        f"bare Apply ignored {damage} {document}:\n"
        f"{retried.stdout}\n{retried.stderr}"
    )
    assert "INCOMPLETE_TRANSACTION" in retried.stderr
    assert "status 'corrupt'" in retried.stderr
    assert tx.name in retried.stderr
    assert _tree_digest(home) == before_retry
    assert _tx_dirs(backup) == [tx], "refusal minted a second transaction"


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "malformed",
        "relabelled-incomplete-applied",
        "relabelled-incomplete-rolled-back",
    ],
)
def test_bare_apply_refuses_terminal_transaction_without_valid_complete_journal(
        damage, mini_dist, tmp_path):
    """A terminal-looking manifest cannot hide missing rollback authority.

    Explicit recovery validates the journal, but bare Apply first has to discover
    whether a matching-home transaction is unresolved.  A damaged applied history,
    or an applying history relabelled as applied/rolled_back before its current
    action commit or undo,
    must be reported as corrupt instead of being skipped as resolved and layered
    under a second transaction.
    """
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"

    if damage.startswith("relabelled-incomplete"):
        preview = _plan(home, tmp_path / "preview", mini_dist)
        seq = _seq_of(preview, "install")[0]
        started = _apply(
            home, backup, mini_dist,
            env={"SKILL_MESH_TX_CRASH_AT": f"{seq}:after-mutate"},
        )
        assert started.returncode == 9, f"{started.stdout}\n{started.stderr}"
    else:
        started = _apply(home, backup, mini_dist)
        assert started.returncode == 0, f"{started.stdout}\n{started.stderr}"

    tx = _only_tx(backup)
    plan = _plan_of(tx)
    assert Path(plan["consumer_home"]).resolve() == Path(home).resolve()
    manifest_path = Path(tx) / "backup-manifest.json"
    manifest = _manifest_of(tx)

    if damage == "missing":
        assert manifest["status"] == "applied"
        (Path(tx) / "journal.jsonl").unlink()
    elif damage == "malformed":
        assert manifest["status"] == "applied"
        (Path(tx) / "journal.jsonl").write_bytes(b"{not valid journal json}\n")
    else:
        assert manifest["status"] == "applying"
        records = _journal_of(tx)
        incomplete = [
            record for record in records
            if record["seq"] == seq
        ]
        assert [record["phase"] for record in incomplete] == ["begin"]
        manifest["status"] = (
            "rolled_back" if damage.endswith("rolled-back") else "applied"
        )
        _write_json(manifest_path, manifest)

    before_retry = _tree_digest(home)
    retried = _apply(home, backup, mini_dist)
    assert retried.returncode == 2, (
        f"bare Apply ignored {damage} terminal history:\n"
        f"{retried.stdout}\n{retried.stderr}"
    )
    assert "INCOMPLETE_TRANSACTION" in retried.stderr
    assert "status 'corrupt'" in retried.stderr
    assert tx.name in retried.stderr
    assert _tree_digest(home) == before_retry, "terminal-history refusal mutated the home"
    assert _tx_dirs(backup) == [tx], "terminal-history refusal minted a second transaction"


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


def test_explicit_rollback_advises_on_preserve_drift_without_changing_its_exit_code(
        mini_dist, tmp_path):
    """The advisory's SECOND call site: the explicit `-Rollback` path.

    Decision D2 case 3 covers both rollback paths -- the failure-triggered shared one
    (exit 1) and this operator-initiated one, which keeps exit 0. Every other rollback
    test runs with no drifted preserved file, so the call is a silent no-op in all of
    them and the suite passing proves nothing about this site. Here the consumer edits
    their own preserved skill after a clean apply and before rolling back: the advisory
    must name it, the exit code must stay 0, and their bytes must survive."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    plan = _plan(home, backup, mini_dist)
    preserves = [a for a in plan["actions"] if a["action"] == "preserve"]
    assert preserves, "no preserve action in this fixture -- the test would be vacuous"
    preserved_rel = preserves[0]["rel_path"]
    planned_hash = preserves[0]["post_hash"]

    assert _apply(home, backup, mini_dist).returncode == 0
    tx = _only_tx(backup)

    target = Path(home) / preserved_rel
    target.write_text(target.read_text(encoding="utf-8") + "\nconsumer edit before rollback\n",
                      encoding="utf-8")
    edited_hash = _sha256(target)
    assert edited_hash != planned_hash, "the edit did not change the file"

    r = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert r.returncode == 0, (
        f"the advisory changed the explicit rollback's exit code "
        f"({r.returncode}):\n{r.stdout}\n{r.stderr}")
    assert _manifest_of(tx)["status"] == "rolled_back"
    json.loads(r.stdout)  # -Format json still emits exactly one document

    advisories = [ln for ln in r.stderr.splitlines() if "ADVISORY" in ln]
    assert len(advisories) == 1, f"expected exactly one advisory line, got {advisories}"
    adv = advisories[0]
    assert preserved_rel in adv, adv
    assert planned_hash in adv, adv
    assert edited_hash in adv, adv
    assert "ADVISORY UNAVAILABLE" not in adv, "the drift check failed to run"

    # Rollback holds no payload for a preserved path, so the consumer's edit stands.
    assert _sha256(target) == edited_hash, "rollback overwrote the consumer's own edit"


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
    # File bytes are restored exactly. Empty directories carry no durable identity,
    # so rollback intentionally leaves both a migration-created empty root and a
    # pre-existing directory alone.
    assert (Path(home) / GPT_ROOT).is_dir(), "rollback removed an identity-less empty root"
    assert not any(p.is_file() for p in (Path(home) / GPT_ROOT).rglob("*")), (
        "rollback left generated files behind"
    )
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


def test_late_resume_failure_rolls_back_every_historically_begun_mutation(
        mini_dist, tmp_path):
    """A new-process failure must undo work begun by the crashed process too.

    The crash occurs after the final ledger write, so every mutating action has
    already reached its post-state. An operator then edits an early preserve row.
    Resume detects that drift and aborts; all transaction-owned file mutations are
    restored while the operator's unowned edit survives.
    """
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    preview = _plan(home, tmp_path / "preview", mini_dist)
    preserves = [a for a in preview["actions"] if a["action"] == "preserve"]
    assert preserves, "fixture has no preserve action to drift"
    preserve = preserves[0]
    ledger_seq = _seq_of(preview, "ledger")[-1]

    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_TX_CRASH_AT": f"{ledger_seq}:after-mutate"},
    )
    assert crashed.returncode == 9, f"{crashed.stdout}\n{crashed.stderr}"
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "applying"
    assert _tree_digest(home) != before, "the late crash left no mutations"

    target = Path(home) / preserve["rel_path"]
    target.write_text(
        target.read_text(encoding="utf-8") + "\noperator edit after the crash\n",
        encoding="utf-8",
    )
    edited_hash = _sha256(target)
    assert edited_hash != preserve["post_hash"]

    resumed = _resume(home, backup, mini_dist, tx)
    assert resumed.returncode == 1, f"{resumed.stdout}\n{resumed.stderr}"
    assert _manifest_of(tx)["status"] == "rolled_back"
    final_records = _journal_of(tx)
    completion = [record for record in final_records
                  if record["phase"] == "rollback_complete"]
    assert len(completion) == 1 and final_records[-1] == completion[0]
    assert completion[0]["begun_seqs"] == sorted({
        record["seq"] for record in final_records if record["phase"] == "begin"
    })
    assert _sha256(target) == edited_hash, "rollback overwrote the preserve edit"

    after = _tree_digest(home)
    differing = {
        rel for rel in set(before) | set(after)
        if before.get(rel) != after.get(rel)
    }
    assert differing == {preserve["rel_path"]}, (
        "Resume rollback omitted historically begun mutations: "
        f"{sorted(differing - {preserve['rel_path']})}"
    )


@pytest.mark.parametrize(
    "phases,target_survives",
    [(["commit"], True), (["begin", "commit"], False)],
    ids=["legacy-commit-only", "actual-begin-and-commit"],
)
def test_only_an_actual_begin_record_grants_install_rollback_authority(
        phases, target_survives, mini_dist, tmp_path):
    """A legacy post-only observation cannot authorize deletion of equal bytes.

    The paired case proves the inverse is still usable: once an actual begin is
    durable, an exact transaction post-state is owned and explicit rollback removes
    a file whose recorded pre-state was absent.
    """
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_TX_CRASH_AT": "0:before-begin"},
    )
    assert crashed.returncode == 9, f"{crashed.stdout}\n{crashed.stderr}"
    tx = _only_tx(backup)
    plan = _plan_of(tx)
    action = next(
        a for a in plan["actions"]
        if a["action"] == "install" and a["pre_hash"] is None
    )
    target = Path(home) / action["rel_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(action["source"], target)
    planted = target.read_bytes()
    assert _sha256(target) == action["post_hash"]
    for phase in phases:
        _append_journal_record(tx, plan, action, phase)

    rolled_back = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert rolled_back.returncode == 0, (
        f"{phases}: {rolled_back.stdout}\n{rolled_back.stderr}"
    )
    assert _manifest_of(tx)["status"] == "rolled_back"
    assert target.exists() is target_survives
    if target_survives:
        assert target.read_bytes() == planted, (
            "a commit-only record granted deletion authority over consumer bytes"
        )


def test_resume_refuses_an_unbegun_install_already_at_exact_post_state(
        mini_dist, tmp_path):
    """Exact generated bytes alone are observation, not transaction ownership."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    preview = _plan(home, tmp_path / "preview", mini_dist)
    action = next(
        a for a in preview["actions"]
        if a["action"] == "install" and a["pre_hash"] is None
    )
    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_TX_CRASH_AT": f"{action['seq']}:before-begin"},
    )
    assert crashed.returncode == 9, f"{crashed.stdout}\n{crashed.stderr}"
    tx = _only_tx(backup)
    durable_action = next(
        a for a in _plan_of(tx)["actions"] if a["seq"] == action["seq"]
    )
    assert not any(
        rec["seq"] == action["seq"] and rec["phase"] == "begin"
        for rec in _journal_of(tx)
    )

    target = Path(home) / durable_action["rel_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(durable_action["source"], target)
    planted = target.read_bytes()
    assert _sha256(target) == durable_action["post_hash"]

    resumed = _resume(home, backup, mini_dist, tx)
    assert resumed.returncode == 1, f"{resumed.stdout}\n{resumed.stderr}"
    assert _manifest_of(tx)["status"] == "rolled_back"
    assert "SECURITY" in resumed.stderr and "unrecorded post-state" in resumed.stderr
    assert target.read_bytes() == planted, (
        "Resume adopted or rollback deleted a post-state with no begin authority"
    )


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


@pytest.mark.parametrize("alias_site", ["retired-root", "retired-child"])
def test_retired_junction_alias_cannot_authorize_active_file_deletion(
        alias_site, mini_dist, tmp_path):
    """Loop 1's authority is canonical residence, never a lexical alias.

    Both shapes stay inside the consumer home, so the generic containment gate must
    accept them. The retired spelling nevertheless points at an ACTIVE managed tree.
    A consumer-authored file with an emitter-valid header is therefore advisory-only:
    dry run schedules no retire and Apply leaves its bytes intact.
    """
    home = fx.migration_home(tmp_path / "h", retired_copilot=False,
                             active_forged_header=True)
    active_skill = Path(home) / CLAUDE_ROOT / fx.MIGRATION_MANAGED[0]
    victim = active_skill / fx.ACTIVE_FORGED_HEADER_DOC
    before = victim.read_bytes()

    if alias_site == "retired-root":
        _junction_or_skip(Path(home) / COPILOT_ROOT,
                          Path(home) / CLAUDE_ROOT)
    else:
        _junction_or_skip(Path(home) / COPILOT_ROOT / fx.MIGRATION_MANAGED[0],
                          active_skill)

    preview = _migrate(home, tmp_path / "preview", mini_dist)
    assert preview.returncode == 0, f"{preview.stdout}\n{preview.stderr}"
    plan = json.loads(preview.stdout)
    assert plan["blocked"] == [], plan["blocked"]

    active_rel = victim.relative_to(home).as_posix()
    retired_alias_rel = (
        f"{COPILOT_ROOT}/{fx.MIGRATION_MANAGED[0]}/"
        f"{fx.ACTIVE_FORGED_HEADER_DOC}"
    )
    retires = _rels(plan, "retire")
    assert active_rel not in retires, sorted(retires)
    assert retired_alias_rel not in retires, sorted(retires)
    assert all(rel == COPILOT_ROOT or rel.startswith(f"{COPILOT_ROOT}/")
               for rel in retires), sorted(retires)
    lines = [ln for ln in preview.stderr.splitlines()
             if ACTIVE_RETAIN_ADVISORY in ln and active_rel in ln]
    assert len(lines) == 1, preview.stderr

    applied = _apply(home, tmp_path / "apply", mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    assert victim.read_bytes() == before, (
        "Apply deleted or rewrote an active file through the retired junction alias"
    )


def test_resume_rechecks_retired_domain_after_post_plan_junction_swap(
        mini_dist, tmp_path):
    """The retire domain is checked at mutation time, not only while planning.

    Crash after the retire begin record, replace its lexical retired directory with
    an in-home junction to an ACTIVE directory whose file has the exact planned hash,
    then resume. Hash and ordinary home-containment checks both pass in that shape;
    only the canonical retired-domain guard can stop the active-file deletion.
    """
    home = fx.migration_home(tmp_path / "h")
    retired_file = (Path(home) / COPILOT_ROOT / fx.MIGRATION_MANAGED[0] /
                    "SKILL.md")
    active_file = (Path(home) / CLAUDE_ROOT / fx.MIGRATION_MANAGED[0] /
                   "SKILL.md")
    # Make the active target hash-identical to the planned retired pre-image so a
    # hash-only precondition is deliberately powerless.
    active_file.write_bytes(retired_file.read_bytes())
    active_before = active_file.read_bytes()

    preview = _plan(home, tmp_path / "preview", mini_dist)
    retire = next(a for a in preview["actions"]
                  if a["action"] == "retire" and
                  a["rel_path"] == retired_file.relative_to(home).as_posix())
    backup = tmp_path / "apply"
    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_TX_CRASH_AT": f"{retire['seq']}:after-begin"},
    )
    assert crashed.returncode == 9, f"{crashed.stdout}\n{crashed.stderr}"
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "applying"

    retired_skill = retired_file.parent
    shutil.rmtree(retired_skill)
    _junction_or_skip(retired_skill, active_file.parent)
    assert _sha256(retired_file) == retire["pre_hash"], (
        "the alias plant does not defeat the hash-only precondition"
    )

    resumed = _migrate(home, backup, mini_dist, mode="-Resume",
                       migration_id=tx.name)
    assert resumed.returncode == 3, f"{resumed.stdout}\n{resumed.stderr}"
    assert _manifest_of(tx)["status"] == "failed_incomplete"
    assert "SECURITY" in resumed.stderr and "outside the retired root" in resumed.stderr
    assert active_file.read_bytes() == active_before, (
        "Resume deleted or rewrote the active file through a same-hash alias"
    )


def test_resume_never_restores_a_retire_payload_through_an_active_alias(
        mini_dist, tmp_path):
    """An after-mutate retire remains fail-closed when its old path is repointed.

    The retired target is absent and its payload is valid -- normally the exact
    crash shape Resume can commit or Rollback can restore. Replacing the retired
    parent with a junction to an empty ACTIVE discovery directory must revoke both
    operations: no payload byte is written into the active tree, and the external
    backup remains available for manual recovery.
    """
    # Keep at least one ordinary preserve row: the serialized recovery contract
    # distinguishes a real empty array from PowerShell's scalar/null collapse.
    home = fx.migration_home(tmp_path / "h", core_holder=False)
    backup = tmp_path / "b"
    preview = _plan(home, tmp_path / "preview", mini_dist)
    retire = next(a for a in preview["actions"] if a["action"] == "retire")
    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_TX_CRASH_AT": f"{retire['seq']}:after-mutate"},
    )
    assert crashed.returncode == 9, f"{crashed.stdout}\n{crashed.stderr}"
    tx = _only_tx(backup)
    action = next(a for a in _plan_of(tx)["actions"] if a["seq"] == retire["seq"])
    payload = Path(tx) / action["backup_payload"]
    payload_bytes = payload.read_bytes()
    assert hashlib.sha256(payload_bytes).hexdigest() == action["pre_hash"]

    retired_target = Path(home) / action["rel_path"]
    assert not retired_target.exists(), "the retire crash did not reach post-state"
    retired_parent = retired_target.parent
    shutil.rmtree(retired_parent)
    active_parent = Path(home) / ".agents" / "skills" / "recovery-target"
    active_parent.mkdir(parents=True)
    active_target = active_parent / retired_target.name
    assert not active_target.exists(), "the active test leaf is not absent"
    _junction_or_skip(retired_parent, active_parent)
    assert not retired_target.exists(), "junction plant unexpectedly created the leaf"

    resumed = _resume(home, backup, mini_dist, tx)
    assert resumed.returncode == 3, f"{resumed.stdout}\n{resumed.stderr}"
    assert _manifest_of(tx)["status"] == "failed_incomplete"
    assert "SECURITY" in resumed.stderr
    assert not active_target.exists(), "Resume restored retired bytes into an active root"
    assert payload.read_bytes() == payload_bytes, "failed recovery discarded its payload"


@pytest.mark.parametrize("alias_site", ["active-root", "active-child", "agents-child"])
def test_active_junction_into_retired_tree_removes_retire_authority(
        alias_site, mini_dist, tmp_path):
    """Host reachability wins over physical residence under the retired root.

    A whole active discovery root or one active skill child points into `.copilot`.
    The generated-looking consumer file is physically retired but actively visible,
    so it receives one retention advisory, no retire action, and survives Apply.
    """
    home = fx.migration_home(tmp_path / "h", active_forged_header=False)
    retired_skill = Path(home) / COPILOT_ROOT / fx.MIGRATION_MANAGED[0]
    victim = retired_skill / fx.ACTIVE_FORGED_HEADER_DOC
    victim.write_text(fx.forged_generated_header_doc(), encoding="utf-8")
    before = victim.read_bytes()

    if alias_site == "active-root":
        active_root = Path(home) / CLAUDE_ROOT
        shutil.rmtree(active_root)
        _junction_or_skip(active_root, Path(home) / COPILOT_ROOT)
    elif alias_site == "active-child":
        active_skill = Path(home) / CLAUDE_ROOT / fx.MIGRATION_MANAGED[0]
        shutil.rmtree(active_skill)
        _junction_or_skip(active_skill, retired_skill)
    else:
        # Copilot discovers `.agents/skills` even though skill-mesh installs its GPT
        # profile into `.github/skills`. Alternate active roots still revoke retire
        # authority.
        _junction_or_skip(
            Path(home) / ".agents" / "skills" / fx.MIGRATION_MANAGED[0],
            retired_skill,
        )

    preview = _migrate(home, tmp_path / "preview", mini_dist)
    assert preview.returncode == 0, f"{preview.stdout}\n{preview.stderr}"
    plan = json.loads(preview.stdout)
    retired_rel = victim.relative_to(home).as_posix()
    assert retired_rel not in _rels(plan, "retire"), sorted(_rels(plan, "retire"))
    lines = [ln for ln in preview.stderr.splitlines()
             if ACTIVE_RETAIN_ADVISORY in ln and retired_rel in ln]
    assert len(lines) == 1, preview.stderr

    applied = _apply(home, tmp_path / "apply", mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    assert victim.read_bytes() == before, (
        "Apply deleted a retired-resident file exposed through active discovery"
    )


@pytest.mark.parametrize("alias_site", ["active-child", "outside-roundtrip"])
def test_resume_rechecks_active_reachability_after_plan(
        alias_site, tmp_path, mini_dist):
    """An active alias planted after the retire plan revokes deletion authority."""
    # No preserved active-root rows: after the alias swap, the next incomplete
    # action must be the retire itself. Otherwise a missing preserved path fails
    # safely first and the test never reaches the authority guard it exists to pin.
    home = fx.migration_home(tmp_path / "h", consumer_only=False,
                             core_holder=False)
    retired_skill = Path(home) / COPILOT_ROOT / fx.MIGRATION_MANAGED[0]
    retired_file = retired_skill / "SKILL.md"
    before = retired_file.read_bytes()
    plan = _plan(home, tmp_path / "preview", mini_dist)
    retire = next(a for a in plan["actions"]
                  if a["action"] == "retire" and
                  a["rel_path"] == retired_file.relative_to(home).as_posix())

    backup = tmp_path / "apply"
    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_TX_CRASH_AT": f"{retire['seq']}:after-begin"},
    )
    assert crashed.returncode == 9, f"{crashed.stdout}\n{crashed.stderr}"
    tx = _only_tx(backup)

    active_root = Path(home) / CLAUDE_ROOT
    if alias_site == "active-child":
        active_skill = active_root / fx.MIGRATION_MANAGED[0]
        shutil.rmtree(active_skill)
        _junction_or_skip(active_skill, retired_skill)
    else:
        # The active root first escapes the home, then a child junction points back
        # to the retired file. Looking only at contained canonical roots and skipping
        # the outside one misses this round trip and authorizes the delete.
        shutil.rmtree(active_root)
        outside = tmp_path / "outside-active"
        outside.mkdir()
        _junction_or_skip(outside / fx.MIGRATION_MANAGED[0], retired_skill)
        _junction_or_skip(active_root, outside)

    resumed = _migrate(home, backup, mini_dist, mode="-Resume",
                       migration_id=tx.name)
    assert resumed.returncode == 3, f"{resumed.stdout}\n{resumed.stderr}"
    assert _manifest_of(tx)["status"] == "failed_incomplete"
    assert "active host discovery path" in resumed.stderr
    assert retired_file.read_bytes() == before, (
        "Resume deleted a retired target after it became actively discoverable"
    )


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
# Post-install verification -- decision D2 case 2 (the one escalating drift case)
# --------------------------------------------------------------------------- #

def test_post_install_verification_catches_a_corrupted_preserved_tree(mini_dist, tmp_path):
    """Decision D2 case 2: a preserved path that fails post-install verification
    AFTER the transaction fully applied escalates to `failed_incomplete` (exit 3).

    The engine's per-action post-hash check is kind-blind, so it already covers a
    preserved path edited while the apply loop is running (that is case 3 -- see
    test_a_preserved_file_edited_during_the_crash_window_rolls_back_with_an_advisory).
    The seam here corrupts a preserved file after the loop commits and before
    verification runs -- the one window the loop structurally cannot see."""
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

    # D2 corrects this branch's MESSAGE while keeping its exit code. Rollback runs in
    # strict reverse seq order and the plan emits backup < preserve < retire < install
    # < ledger, so every MUTATING action was undone before the preserve throw -- which
    # the tree comparison below independently proves. Claiming the home is MIXED and
    # telling the operator to recover from the backup would invite restoring a stale
    # payload over the consumer's own newer bytes: the round-5 regression.
    assert "MIXED" not in r.stderr, r.stderr
    assert "recover from it manually" not in r.stderr, r.stderr
    assert "every verified file mutation this tool made was reversed" in r.stderr, r.stderr
    assert preserved_rel in r.stderr, "the escalation did not name the unrestorable path"

    # Everything rollback DOES own was still restored: only the tampered preserved
    # path differs from the pre-migration tree.
    after = _tree_digest(home)
    differing = {rel for rel in set(before) | set(after) if before.get(rel) != after.get(rel)}
    assert differing == {preserved_rel}, (
        f"rollback left more than the unrestorable preserved path changed: {differing}")


def test_a_preserved_file_edited_during_the_crash_window_rolls_back_with_an_advisory(
        mini_dist, tmp_path):
    """Decision D2 case 3 -- and the only coverage of the SHARED apply/resume rollback
    path, which no assertion reached before this test.

    A consumer edits their own preserved skill while the migration is down between a
    crash and the `-Resume`. The engine's per-action post-hash check is kind-blind and
    a `preserve` action carries post_hash == pre_hash, so the edited file fails
    verification mid-apply and aborts the resume -- the drift IS the trigger. That is a
    PRE-COMPLETION abort, so it must not escalate: `rolled_back` is the honest status
    (every verified file mutation was reversed; the consumer's file was never touched),
    the drift is disclosed as an advisory naming the path and both hashes, and the
    documented remedy -- a plain `-Apply`, which re-plans against the new contents --
    converges.

    Round 4's only Block demanded escalation here; round 5's headline Block condemned
    exactly that escalation. This test pins the adjudicated answer so a later round
    cannot silently flip it back."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    plan = _plan(home, backup, mini_dist)
    preserves = [a for a in plan["actions"] if a["action"] == "preserve"]
    assert preserves, "no preserve action in this fixture -- the test would be vacuous"
    preserved_rel = preserves[0]["rel_path"]
    planned_hash = preserves[0]["post_hash"]
    target = Path(home) / preserved_rel
    assert target.is_file(), f"fixture did not plant the preserved file {preserved_rel}"

    # Crash at seq 0 (the seam defaults to after-begin), leaving `applying` on disk.
    assert _apply(home, backup, mini_dist,
                  env={"SKILL_MESH_TX_CRASH_AT": "0"}).returncode == 9
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "applying"

    # The consumer edits THEIR OWN file, out of process, during the downtime.
    target.write_text(target.read_text(encoding="utf-8") + "\nconsumer edit during downtime\n",
                      encoding="utf-8")
    edited_hash = _sha256(target)
    assert edited_hash != planned_hash, "the edit did not change the file"

    r = _migrate(home, backup, mini_dist, mode="-Resume", migration_id=tx.name)
    assert r.returncode == 1, (
        f"a pre-completion abort escalated instead of rolling back "
        f"(exit {r.returncode}):\n{r.stdout}\n{r.stderr}")
    assert _manifest_of(tx)["status"] == "rolled_back"

    # The advisory names the path and BOTH hashes. Assert against the ADVISORY LINE
    # itself, not the whole stream: the engine's own "post-mutation verification
    # FAILED ... expected hash X but found Y" message is echoed earlier on this same
    # path and already contains the path and both hashes, so whole-stream assertions
    # would stay green even if the advisory's payload were stripped entirely.
    advisories = [ln for ln in r.stderr.splitlines() if "ADVISORY" in ln]
    assert len(advisories) == 1, f"expected exactly one advisory line, got {advisories}"
    adv = advisories[0]
    assert preserved_rel in adv, f"the advisory did not name the drifted path: {adv}"
    assert planned_hash in adv, f"the advisory did not report the expected hash: {adv}"
    assert edited_hash in adv, f"the advisory did not report the observed hash: {adv}"
    # ...while nothing claims a mixed home or sends the operator to restore a backup
    # over their own newer bytes (the round-5 regression), and the status line makes
    # only the narrow claim.
    assert "MIXED" not in r.stderr, r.stderr
    assert "recover from it manually" not in r.stderr, r.stderr
    assert "restored to its pre-migration state" not in r.stderr, r.stderr
    assert "every verified file mutation this tool made was reversed" in r.stderr, r.stderr

    # The consumer's edit survived: rollback holds no payload for a preserved path.
    assert _sha256(target) == edited_hash, "rollback overwrote the consumer's own edit"

    # The documented remedy converges -- `rolled_back` is terminal, so a bare -Apply
    # is not refused as an unresolved transaction and re-plans against the new bytes.
    before_dirs = {d.name for d in _tx_dirs(backup)}
    r2 = _apply(home, backup, mini_dist)
    assert r2.returncode == 0, (
        f"the follow-up -Apply did not converge ({r2.returncode}):\n{r2.stdout}\n{r2.stderr}")
    fresh = [d for d in _tx_dirs(backup) if d.name not in before_dirs]
    assert len(fresh) == 1, f"expected exactly one new transaction, got {[d.name for d in fresh]}"
    assert _manifest_of(fresh[0])["status"] == "applied"
    assert _sha256(target) == edited_hash, "the follow-up apply clobbered the preserved edit"


def test_rolling_back_with_durable_completion_only_publishes_terminal_status(
        mini_dist, tmp_path):
    """A crash-shaped status lag after rollback completion never replays undo."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    first = _migrate(
        home, backup, mode="-Rollback", migration_id=tx.name,
        env={"SKILL_MESH_TX_CRASH_AFTER_ROLLBACK_COMPLETE": "1"},
    )
    assert first.returncode == 9, f"{first.stdout}\n{first.stderr}"
    assert "simulated crash after rollback completion" in first.stderr
    records = _journal_of(tx)
    assert [record["phase"] for record in records].count("rollback_complete") == 1
    before_recovery = _tree_digest(home)

    manifest = _manifest_of(tx)
    assert manifest["status"] == "rolling_back"

    blocked = _apply(home, backup, mini_dist)
    assert blocked.returncode == 2, f"{blocked.stdout}\n{blocked.stderr}"
    assert "INCOMPLETE_TRANSACTION" in blocked.stderr
    assert _tree_digest(home) == before_recovery
    assert _tx_dirs(backup) == [tx]

    recovered = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert recovered.returncode == 0, f"{recovered.stdout}\n{recovered.stderr}"
    assert "durable completion recovered" in recovered.stderr
    assert _manifest_of(tx)["status"] == "rolled_back"
    assert _tree_digest(home) == before_recovery
    assert [record["phase"] for record in _journal_of(tx)].count(
        "rollback_complete") == 1


@pytest.mark.parametrize("damage", ["missing", "truncated"])
def test_journal_damage_during_undo_can_never_certify_rolled_back(
        damage, mini_dist, tmp_path):
    """The final certificate revalidates authority after every inverse ran."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    assert _tree_digest(home) != before
    staged_script = _stage_migrator_with_after_undo_fault(tmp_path / "stage")

    recovered = _run(staged_script, [
        "-Home", str(home),
        "-BackupDir", str(backup),
        "-Rollback",
        "-MigrationId", tx.name,
        "-Format", "json",
    ], env={"SKILL_MESH_TEST_AFTER_ONE_UNDO": damage})

    assert recovered.returncode == 3, (
        f"{damage} journal was certified after undo:\n"
        f"{recovered.stdout}\n{recovered.stderr}"
    )
    assert _manifest_of(tx)["status"] == "failed_incomplete"
    assert json.loads(recovered.stdout)["status"] == "failed_incomplete"
    assert "ROLLBACK INCOMPLETE" in recovered.stderr
    journal = Path(tx) / "journal.jsonl"
    raw = journal.read_bytes() if journal.is_file() else b""
    assert b'"phase":"rollback_complete"' not in raw
    assert _tree_digest(home) == before, "best-effort undo did not finish"


def test_rolling_back_without_completion_continues_a_partially_finished_undo(
        mini_dist, tmp_path):
    """Exact pre-state is an idempotent inverse, not proof of full completion."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    applied_tree = _tree_digest(home)
    assert applied_tree != before
    plan = _plan_of(tx)
    assert plan["actions"][-1]["action"] == "ledger"
    ledger_action = plan["actions"][-1]
    installed = next(
        action for action in plan["actions"]
        if action["action"] == "install" and action["pre_hash"] is None
    )

    staged_script = _stage_migrator_with_after_undo_fault(tmp_path / "stage")
    interrupted = _run(staged_script, [
        "-Home", str(home),
        "-BackupDir", str(backup),
        "-Rollback",
        "-MigrationId", tx.name,
        "-Format", "json",
    ], env={"SKILL_MESH_TEST_AFTER_ONE_UNDO": "crash"})
    assert interrupted.returncode == 9, f"{interrupted.stdout}\n{interrupted.stderr}"
    assert "crash after one undo" in interrupted.stderr
    assert _manifest_of(tx)["status"] == "rolling_back"
    assert not any(
        record["phase"] == "rollback_complete" for record in _journal_of(tx)
    )
    assert _sha256(Path(home) / ledger_action["rel_path"]) == ledger_action["pre_hash"]
    assert _sha256(Path(home) / installed["rel_path"]) == installed["post_hash"]
    partial_tree = _tree_digest(home)
    assert partial_tree != before and partial_tree != applied_tree

    continued = _migrate(
        home, backup, mode="-Rollback", migration_id=tx.name,
    )
    assert continued.returncode == 0, f"{continued.stdout}\n{continued.stderr}"
    assert _manifest_of(tx)["status"] == "rolled_back"
    assert _tree_digest(home) == before
    records = _journal_of(tx)
    markers = [record for record in records
               if record["phase"] == "rollback_complete"]
    assert len(markers) == 1 and records[-1] == markers[0]
    assert markers[0]["begun_seqs"] == sorted({
        record["seq"] for record in records if record["phase"] == "begin"
    })


def test_completed_rollback_allows_fresh_plan_after_retired_bytes_change(
        mini_dist, tmp_path):
    """Completion evidence avoids freezing historical mutating pre-images forever."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    rolled_back = _migrate(home, backup, mode="-Rollback", migration_id=tx.name)
    assert rolled_back.returncode == 0, f"{rolled_back.stdout}\n{rolled_back.stderr}"
    assert _manifest_of(tx)["status"] == "rolled_back"
    assert _journal_of(tx)[-1]["phase"] == "rollback_complete"

    plan = _plan_of(tx)
    retire = next(action for action in plan["actions"]
                  if action["action"] == "retire")
    restored = Path(home) / retire["rel_path"]
    assert restored.is_file() and _sha256(restored) == retire["pre_hash"]
    restored.write_text(
        restored.read_text(encoding="utf-8") + "\nconsumer edit after rollback\n",
        encoding="utf-8",
    )
    changed_hash = _sha256(restored)
    assert changed_hash != retire["pre_hash"]

    before_dirs = {path.name for path in _tx_dirs(backup)}
    replanned = _apply(home, backup, mini_dist)
    assert replanned.returncode == 0, f"{replanned.stdout}\n{replanned.stderr}"
    fresh = [path for path in _tx_dirs(backup) if path.name not in before_dirs]
    assert len(fresh) == 1 and _manifest_of(fresh[0])["status"] == "applied"


@pytest.mark.parametrize("entrypoint", ["apply", "resume", "rollback"])
def test_completed_rollback_rejects_a_tampered_mutating_begin_record(
        entrypoint, mini_dist, tmp_path):
    """Completion permits later disk edits, never rewritten historical authority."""
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    applied = _apply(home, backup, mini_dist)
    assert applied.returncode == 0, f"{applied.stdout}\n{applied.stderr}"
    tx = _only_tx(backup)
    completed = _migrate(
        home, backup, mode="-Rollback", migration_id=tx.name,
    )
    assert completed.returncode == 0, f"{completed.stdout}\n{completed.stderr}"
    assert _manifest_of(tx)["status"] == "rolled_back"
    plan = _plan_of(tx)
    by_seq = {action["seq"]: action for action in plan["actions"]}
    records = _journal_of(tx)
    begin = next(
        record for record in records
        if record["phase"] == "begin"
        and by_seq[record["seq"]]["action"] in MUTATING_KINDS
        and isinstance(by_seq[record["seq"]]["pre_hash"], str)
    )
    expected_pre = by_seq[begin["seq"]]["pre_hash"]
    forged_pre = ("0" if expected_pre[0] != "0" else "1") + expected_pre[1:]
    assert len(forged_pre) == 64 and forged_pre != expected_pre
    begin["pre_hash"] = forged_pre
    _replace_journal_records(tx, records)
    before_retry = _tree_digest(home)

    if entrypoint == "apply":
        retried = _apply(home, backup, mini_dist)
    elif entrypoint == "resume":
        retried = _migrate(
            home, backup, mini_dist, mode="-Resume", migration_id=tx.name,
        )
    else:
        retried = _migrate(
            home, backup, mode="-Rollback", migration_id=tx.name,
        )
    assert retried.returncode == 2, (
        f"{entrypoint} hid a tampered mutating begin behind rollback_complete:\n"
        f"{retried.stdout}\n{retried.stderr}"
    )
    if entrypoint == "apply":
        assert "INCOMPLETE_TRANSACTION" in retried.stderr
        assert "status 'corrupt'" in retried.stderr
    else:
        assert "INVALID_JOURNAL" in retried.stderr
        assert "TRANSACTION_RESOLVED" not in retried.stderr
    assert _tree_digest(home) == before_retry
    assert _tx_dirs(backup) == [tx]


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


def test_resume_after_pre_postcheck_crash_reruns_postinstall_validation(
        mini_dist, tmp_path):
    """Action-loop completion is not the durable `applied` acceptance point.

    The first process crashes after every action commit but before the wider
    post-install check. Resume then uses the existing postcheck tamper seam: seeing
    that corruption proves it re-entered post-install validation instead of treating
    complete action history as an already-applied no-op.
    """
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    preview = _plan(home, tmp_path / "preview", mini_dist)
    preserve = next(a for a in preview["actions"] if a["action"] == "preserve")

    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_MIGRATE_CRASH_BEFORE_POSTCHECK": "1"},
    )
    assert crashed.returncode == 9, f"{crashed.stdout}\n{crashed.stderr}"
    assert "simulated crash before post-install verification" in crashed.stderr
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "applying"
    committed = {
        record["seq"] for record in _journal_of(tx)
        if record["phase"] == "commit"
    }
    assert committed == {action["seq"] for action in _plan_of(tx)["actions"]}, (
        "the seam fired before the engine action loop completed"
    )

    resumed = _migrate(
        home, backup, mini_dist, mode="-Resume", migration_id=tx.name,
        env={"SKILL_MESH_MIGRATE_TAMPER_AFTER_APPLY": preserve["rel_path"]},
    )
    assert resumed.returncode == 3, f"{resumed.stdout}\n{resumed.stderr}"
    assert "post-install verification FAILED" in resumed.stderr
    assert _manifest_of(tx)["status"] == "failed_incomplete"

    # All owned mutations were reversed; only the deliberately tampered preserve
    # row remains different because it has no backup payload by design.
    after = _tree_digest(home)
    differing = {
        rel for rel in set(before) | set(after)
        if before.get(rel) != after.get(rel)
    }
    assert differing == {preserve["rel_path"]}, differing


def test_status_writer_failure_reports_the_last_verified_persisted_status(
        mini_dist, tmp_path):
    """A failed terminal publication cannot leak into result JSON as success."""
    staged_script = _stage_migrator_checkout(tmp_path / "stage")
    staged_manifest = staged_script.parents[1] / "config" / "skill-manifest.json"
    staged_manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MANIFEST_PATH, staged_manifest)
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    postcheck_anchor = """\
    try {
        $postActionRecords = Read-SkillMeshTxJournal (Resolve-TxPath $JOURNAL_FILE)
"""
    postcheck_injection = """\
    try {
        $statusWriterSource = $statusWriter
        $statusWriter = {
            param($s)
            if ($s -eq 'failed_incomplete') {
                throw 'migrate-legacy-install: TEST INJECTION -- failed terminal status write.'
            }
            & $statusWriterSource $s
        }.GetNewClosure()
        $tx.status_writer = $statusWriter
        $journalForTest = Resolve-TxPath $JOURNAL_FILE
        $journalStreamForTest = New-Object System.IO.FileStream(
            $journalForTest, [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::Read)
        try {
            $journalStreamForTest.SetLength($journalStreamForTest.Length - 1)
            $journalStreamForTest.Flush($true)
        } finally {
            $journalStreamForTest.Dispose()
        }
        $postActionRecords = Read-SkillMeshTxJournal $journalForTest
"""
    _replace_staged_source_once(staged_script, postcheck_anchor, postcheck_injection)
    result = _run(staged_script, [
        "-Home", str(home),
        "-BackupDir", str(backup),
        "-DistDir", str(mini_dist),
        "-Apply",
        "-Format", "json",
    ])
    assert result.returncode == 3, f"{result.stdout}\n{result.stderr}"
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "rolling_back"
    result_doc = json.loads(result.stdout)
    assert result_doc["status"] == "rolling_back"
    assert result_doc["status"] != "failed_incomplete"
    assert "failed_incomplete status could not be persisted" in result.stderr
    assert "last verified persisted transaction status is 'rolling_back'" in result.stderr


def test_late_resume_failure_never_rolls_back_a_commit_only_created_install(
        mini_dist, tmp_path):
    """Post-install failure cannot turn legacy observation into delete authority.

    Model a legacy transaction whose created install has only a durable commit, then
    fail Resume later in the separate post-install verification pass.  Failure
    rollback may reverse every sequence carrying a begin record, but it must retain
    the commit-only target even when its bytes exactly match the planned post-state.
    """
    home = fx.migration_home(tmp_path / "h")
    backup = tmp_path / "b"
    before = _tree_digest(home)
    preview = _plan(home, tmp_path / "preview", mini_dist)
    preserve = next(a for a in preview["actions"] if a["action"] == "preserve")

    crashed = _apply(
        home, backup, mini_dist,
        env={"SKILL_MESH_MIGRATE_CRASH_BEFORE_POSTCHECK": "1"},
    )
    assert crashed.returncode == 9, f"{crashed.stdout}\n{crashed.stderr}"
    tx = _only_tx(backup)
    assert _manifest_of(tx)["status"] == "applying"
    plan = _plan_of(tx)
    observed = next(
        action for action in plan["actions"]
        if action["action"] == "install" and action["pre_hash"] is None
    )
    observed_target = Path(home) / observed["rel_path"]
    observed_bytes = observed_target.read_bytes()
    assert _sha256(observed_target) == observed["post_hash"]

    records = [
        record for record in _journal_of(tx)
        if not (record["seq"] == observed["seq"] and record["phase"] == "begin")
    ]
    _replace_journal_records(tx, records)
    assert [
        record["phase"] for record in _journal_of(tx)
        if record["seq"] == observed["seq"]
    ] == ["commit"]

    resumed = _migrate(
        home, backup, mini_dist, mode="-Resume", migration_id=tx.name,
        env={"SKILL_MESH_MIGRATE_TAMPER_AFTER_APPLY": preserve["rel_path"]},
    )
    assert resumed.returncode == 3, f"{resumed.stdout}\n{resumed.stderr}"
    assert "post-install verification FAILED" in resumed.stderr
    assert _manifest_of(tx)["status"] == "failed_incomplete"
    assert observed_target.read_bytes() == observed_bytes, (
        "late failure rollback deleted a target known only by a commit observation"
    )

    after = _tree_digest(home)
    differing = {
        rel for rel in set(before) | set(after)
        if before.get(rel) != after.get(rel)
    }
    assert differing == {observed["rel_path"], preserve["rel_path"]}, (
        "rollback did not limit authority to durable begin records: "
        f"{sorted(differing)}"
    )


# --------------------------------------------------------------------------- #
# Emptied-directory cleanup
# --------------------------------------------------------------------------- #

def test_empty_retired_dirs_are_preserved_without_durable_identity(mini_dist, tmp_path):
    """Retiring files does not confer ownership of later empty directories.

    Directory objects have no recorded byte identity, so cosmetic cleanup cannot
    distinguish the directories it emptied from operator replacements created in
    the same paths during a transaction window. Both equal-length siblings remain
    empty while every retired file is gone."""
    a, b = fx.EQUAL_LENGTH_RETIRED
    assert len(a) == len(b), "the fixture names must be equal length or this proves nothing"
    home = fx.migration_home(tmp_path / "h", equal_length_retired=True)
    for name in (a, b):
        assert (Path(home) / COPILOT_ROOT / name / "SKILL.md").is_file(), name
    assert _apply(home, tmp_path / "b", mini_dist).returncode == 0
    for name in (a, b):
        retired_dir = Path(home) / COPILOT_ROOT / name
        assert retired_dir.is_dir(), f"identity-less empty directory was removed: {name}"
        assert not any(retired_dir.iterdir()), f"retired file survived in {name}"


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
ROOT_LITERALS = ["'.claude/skills'", "'.github/skills'", "'.agents/skills'",
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
                       "[string](Get-SkillMeshDiscoveryRoot 'nope') + '|' + "
                       "((Get-SkillMeshActiveProjectDiscoveryRoots) -join ',')")
    assert r.returncode == 0, r.stderr
    claude, gpt, retired, legacy, unknown, active = r.stdout.strip().split("|")
    assert (claude, gpt) == (CLAUDE_ROOT, GPT_ROOT)
    assert retired == COPILOT_ROOT
    assert legacy == fx.LEGACY_SKILLS_GPT_ROOT
    assert unknown == "", "an unknown provider must resolve to $null, not a guess"
    assert set(active.split(",")) == {CLAUDE_ROOT, GPT_ROOT, ".agents/skills"}


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
    the routing: a clean install still needs only -Provider and -Home.

    AMENDED in Step 64, which added an OPTIONAL `-BackupDir` to the installer by an
    explicit operator decision (the `-Force` take-ownership guardrails: adopting an
    operator's existing `_shared/` files must record their bytes and hashes first).
    The original assertion banned the SUBSTRING `BackupDir` anywhere in the script,
    which was a proxy for this test's own declared contract -- its name says "no
    REQUIRED backupdir" -- and the substring ban is strictly weaker than the property
    it stood in for: it would have passed for a mandatory parameter spelled anything
    else, and it fails for an optional one spelled this way.

    So the check is made exact rather than dropped: the parameter must be declared
    optional with an empty default and must not be Mandatory, an install given
    neither -BackupDir nor -ForceShared must still succeed (asserted above), and such
    a run must write NO backup artifact anywhere. The routing contract this test was
    written for -- no migration_id, no journal, no migrator-shaped ledger -- is
    untouched below.
    """
    dist = tmp_path / "d"
    r = _run(BUILD_SCRIPT, ["-OutputDir", str(dist), "-Provider", "claude"])
    assert r.returncode == 0, r.stderr
    home = tmp_path / "h"
    ri = _run(INSTALL_SCRIPT, ["-Home", str(home), "-Provider", "claude",
                               "-DistDir", str(dist)])
    assert ri.returncode == 0, f"{ri.stdout}\n{ri.stderr}"

    text = INSTALL_SCRIPT.read_text(encoding="utf-8")
    assert re.search(r"^\s*\[string\]\$BackupDir\s*=\s*''\s*,?\s*$", text, re.M), \
        "the installer's -BackupDir is no longer declared optional with an empty default"
    # ...and carries no parameter ATTRIBUTES. In PowerShell those sit between the
    # previous parameter's comma and this one's type, so that whole span is the
    # declaration: reading only the `[string]$BackupDir` token itself would be a
    # vacuous check that a `[Parameter(Mandatory = $true)]` on the line above evades.
    at = text.index("[string]$BackupDir")
    decl = text[text.rindex(",", 0, at) + 1:at]
    assert "Parameter(" not in decl and "Mandatory" not in decl, \
        f"the installer's -BackupDir grew parameter attributes: {decl.strip()!r}"
    # A plain install writes no backup artifact: take-ownership is opt-in only, so a
    # run that took ownership of nothing must leave nothing behind to restore from.
    strays = sorted(p.name for p in tmp_path.rglob("take-ownership-backup.json"))
    assert not strays, f"a plain install produced a take-ownership backup: {strays}"
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
