"""Behavioral contract tests for the reversible Codex release activator."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest

PWSH = shutil.which("powershell")
REPO_ROOT = Path(__file__).resolve().parents[2]
ACTIVATE = REPO_ROOT / "tools" / "activate-codex-release.ps1"
BUILD = REPO_ROOT / "tools" / "build-distributions.ps1"

pytestmark = pytest.mark.skipif(PWSH is None, reason="powershell is not available on PATH")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _snapshot(root):
    root = Path(root)
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}


def _run(*args, env=None):
    return subprocess.run([PWSH, "-NoProfile", "-File", str(ACTIVATE), *map(str, args)],
                          capture_output=True, text=True, env=env, timeout=90)


def _synthetic_repo(root):
    repo = root / "synthetic"
    for directory in ("tools", "runtime", "config", "_shared", "skills/demo/providers"):
        (repo / directory).mkdir(parents=True, exist_ok=True)
    for name in ("build-distributions.ps1", "skill-mesh-provenance.ps1"):
        shutil.copy2(REPO_ROOT / "tools" / name, repo / "tools" / name)
    shutil.copy2(REPO_ROOT / "runtime" / "path-guard.ps1", repo / "runtime" / "path-guard.ps1")
    (repo / "_shared" / "build_step_verdict.py").write_text('"""fixture."""\n', encoding="utf-8")
    (repo / "skills/demo/core.md").write_text("# Demo core\n", encoding="utf-8")
    (repo / "skills/demo/providers/claude.md").write_text("# Claude\n", encoding="utf-8")
    (repo / "skills/demo/providers/codex.md").write_text("# Codex\n", encoding="utf-8")
    manifest = {"skills": [{"name": "demo", "status": "portable",
                 "core": "skills/demo/core.md", "providers": {
                     "claude": "skills/demo/providers/claude.md",
                     "codex": "skills/demo/providers/codex.md"}}]}
    (repo / "config/skill-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return repo


@pytest.fixture(scope="module")
def codex_dist(tmp_path_factory):
    root = tmp_path_factory.mktemp("activation-builder")
    repo = _synthetic_repo(root)
    out = root / "dist"
    built = subprocess.run([PWSH, "-NoProfile", "-File", str(repo / "tools/build-distributions.ps1"),
                            "-Provider", "codex", "-OutputDir", str(out)],
                           capture_output=True, text=True, timeout=90)
    assert built.returncode == 0, built.stdout + built.stderr
    return out


def _release(tmp_path, codex_dist, **changes):
    release = tmp_path / "release"
    shutil.copytree(codex_dist, release / "dist")
    artifacts = [{"path": "dist/codex/" + p.relative_to(release / "dist/codex").as_posix(),
                  "sha256": _sha(p)}
                 for p in sorted((release / "dist/codex").rglob("*")) if p.is_file()]
    record = {"schema_version": 1, "product": "skill-mesh", "version": "1.2.3",
              "source_commit": "a" * 40, "source_tree": "b" * 40, "builder_commit": "c" * 40,
              "created_at": "2026-09-24T00:00:00.000Z", "qualification": "QUALIFIED",
              "providers": ["codex"], "artifacts": artifacts}
    record.update(changes)
    (release / "release.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return release


def _preview(release, home, state, *, expect=0):
    result = _run("-Mode", "preview", "-ReleaseDir", release, "-TargetHome", home, "-StateRoot", state)
    assert result.returncode == expect, result.stdout + result.stderr
    if expect:
        return result, None, None
    match = re.search(r"operation_id: ([0-9a-f-]{36})", result.stdout)
    assert match, result.stdout
    op = match.group(1)
    preview = json.loads((Path(state) / "operations" / op / "preview.json").read_text(encoding="utf-8"))
    return result, op, preview


def _apply(release, home, state, op, *, expect=0, env=None):
    result = _run("-Mode", "apply", "-ReleaseDir", release, "-TargetHome", home,
                  "-StateRoot", state, "-OperationId", op, env=env)
    assert result.returncode == expect, result.stdout + result.stderr
    return result


def _rollback(state, op, home=None, *, expect=0):
    args = ["-Mode", "rollback", "-StateRoot", state, "-OperationId", op]
    if home is not None:
        args += ["-TargetHome", home]
    result = _run(*args)
    assert result.returncode == expect, result.stdout + result.stderr
    return result


def _desired(release):
    return _snapshot(Path(release) / "dist/codex")


def _installed(home):
    return _snapshot(Path(home) / ".agents/skills")


def _ledger_entry(files):
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    return {"provider": "codex", "discovery_subdir": ".agents/skills", "owned_files": sorted(files),
            "owned_file_hashes": hashes, "created_dirs": []}


def test_inspect_good_release(codex_dist, tmp_path):
    release = _release(tmp_path, codex_dist)
    result = _run("-Mode", "inspect", "-ReleaseDir", release)
    assert result.returncode == 0, result.stderr
    assert "release_id: skill-mesh/1.2.3" in result.stdout
    assert "release_manifest_sha256:" in result.stdout


def test_inspect_refuses_nonqualified_release(codex_dist, tmp_path):
    release = _release(tmp_path, codex_dist, qualification="INCOMPLETE")
    result = _run("-Mode", "inspect", "-ReleaseDir", release)
    assert result.returncode == 2 and "QUALIFIED" in result.stderr


def test_inspect_refuses_corrupt_artifact_hash(codex_dist, tmp_path):
    release = _release(tmp_path, codex_dist)
    record = json.loads((release / "release.json").read_text())
    record["artifacts"][0]["sha256"] = "0" * 64
    (release / "release.json").write_text(json.dumps(record), encoding="utf-8")
    result = _run("-Mode", "inspect", "-ReleaseDir", release)
    assert result.returncode == 2 and "hash" in result.stderr


def test_inspect_refuses_extra_codex_file(codex_dist, tmp_path):
    release = _release(tmp_path, codex_dist)
    (release / "dist/codex/extra.txt").write_text("extra", encoding="utf-8")
    result = _run("-Mode", "inspect", "-ReleaseDir", release)
    assert result.returncode == 2 and "artifact set" in result.stderr


def test_preview_writes_uuid_add_plan_without_touching_home(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    _, op, preview = _preview(release, home, state)
    assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", op)
    assert preview["status"] == "previewed"
    assert {row["action"] for row in preview["plan"]} == {"add"}
    assert not home.exists()


def test_preview_refuses_foreign_collision(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    victim = home / ".agents/skills/demo/SKILL.md"
    victim.parent.mkdir(parents=True)
    victim.write_text("foreign", encoding="utf-8")
    result, _, _ = _preview(release, home, state, expect=2)
    assert "foreign collision" in result.stderr
    assert not (state / "operations").exists()


def test_apply_clean_home_installs_bytes_ledger_and_selector(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    _, op, _ = _preview(release, home, state)
    _apply(release, home, state, op)
    assert _installed(home) == _desired(release)
    ledger = json.loads((home / ".skill-mesh-install.json").read_text())
    entry = ledger["installs"]["codex"]
    expected = {".agents/skills/" + name: hashlib.sha256(data).hexdigest()
                for name, data in _desired(release).items()}
    assert set(entry["owned_files"]) == set(expected)
    assert entry["owned_file_hashes"] == expected
    selector = json.loads((state / "current-codex.json").read_text())
    assert selector["operation_id"] == op and selector["release_id"] == "skill-mesh/1.2.3"


def test_apply_idempotent_noop_preview_keeps_home_and_ledger_bytes(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    _, first, _ = _preview(release, home, state)
    _apply(release, home, state, first)
    before = _snapshot(home)
    _, second, preview = _preview(release, home, state)
    assert {row["action"] for row in preview["plan"]} == {"no-op"}
    _apply(release, home, state, second)
    assert _snapshot(home) == before


def test_apply_refuses_target_drift_after_preview(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    _, op, preview = _preview(release, home, state)
    rel = preview["plan"][0]["rel"]
    victim = home / Path(rel)
    victim.parent.mkdir(parents=True)
    victim.write_text("drift", encoding="utf-8")
    result = _apply(release, home, state, op, expect=2)
    assert "NEW preview" in result.stderr


def test_apply_refuses_unknown_operation_id(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    result = _apply(release, home, state, "12345678-1234-4123-8123-123456789abc", expect=2)
    assert "unknown" in result.stderr


def test_apply_refuses_operation_for_other_home(codex_dist, tmp_path):
    release, state = _release(tmp_path, codex_dist), tmp_path / "state"
    _, op, _ = _preview(release, tmp_path / "home-a", state)
    result = _apply(release, tmp_path / "home-b", state, op, expect=2)
    assert "target_home" in result.stderr


def test_rollback_restores_prior_bytes_ledger_and_selector(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    old = (release / "dist/codex/demo/SKILL.md").read_bytes() + b"\nold\n"
    rel = ".agents/skills/demo/SKILL.md"
    (home / Path(rel)).parent.mkdir(parents=True)
    (home / Path(rel)).write_bytes(old)
    prior = {"tool": "skill-mesh", "ledger_version": 1, "installs": {"codex": _ledger_entry({rel: old})}}
    (home / ".skill-mesh-install.json").write_text(json.dumps(prior), encoding="utf-8")
    state.mkdir()
    selector = b'{"previous":true}\n'
    (state / "current-codex.json").write_bytes(selector)
    ledger_before = (home / ".skill-mesh-install.json").read_bytes()
    _, op, _ = _preview(release, home, state)
    _apply(release, home, state, op)
    _rollback(state, op, home)
    assert (home / Path(rel)).read_bytes() == old
    assert (home / ".skill-mesh-install.json").read_bytes() == ledger_before
    assert (state / "current-codex.json").read_bytes() == selector


def test_rollback_deletes_files_absent_before(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    _, op, _ = _preview(release, home, state)
    _apply(release, home, state, op)
    _rollback(state, op)
    assert not (home / ".agents/skills/demo/SKILL.md").exists()
    assert not (home / ".skill-mesh-install.json").exists()
    assert not (state / "current-codex.json").exists()


def test_rollback_preserves_foreign_files(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    _, op, _ = _preview(release, home, state)
    _apply(release, home, state, op)
    foreign = home / "consumer-only.txt"
    foreign.write_text("keep", encoding="utf-8")
    _rollback(state, op)
    assert foreign.read_text(encoding="utf-8") == "keep"


def test_rollback_refuses_postapply_drift(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    _, op, _ = _preview(release, home, state)
    _apply(release, home, state, op)
    (home / ".agents/skills/demo/SKILL.md").write_text("drift", encoding="utf-8")
    result = _rollback(state, op, expect=2)
    assert "drift" in result.stderr


def test_rollback_refuses_previewed_operation(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    _, op, _ = _preview(release, home, state)
    result = _rollback(state, op, expect=2)
    assert "nothing to roll back" in result.stderr


def test_rollback_refuses_double_rollback(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    _, op, _ = _preview(release, home, state)
    _apply(release, home, state, op)
    _rollback(state, op)
    result = _rollback(state, op, expect=2)
    assert "already" in result.stderr


def test_interrupted_selector_publish_is_incomplete_and_rolls_back(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    _, op, _ = _preview(release, home, state)
    env = os.environ.copy()
    env["SKILL_MESH_CODEX_ACTIVATION_TEST_FAIL_SELECTOR_PUBLISH"] = "1"
    result = _apply(release, home, state, op, expect=1, env=env)
    assert "INCOMPLETE" in result.stderr
    preview = json.loads((state / "operations" / op / "preview.json").read_text())
    assert preview["status"] == "incomplete"
    assert (home / ".agents/skills/demo/SKILL.md").is_file()
    _rollback(state, op)
    assert not (home / ".agents/skills/demo/SKILL.md").exists()


def test_lock_contention_is_reported_not_broken(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    _, op, _ = _preview(release, home, state)
    normalized = str(home.resolve()).upper()
    lock = state / "locks" / (hashlib.sha256(normalized.encode("utf-8")).hexdigest() + ".lock")
    command = "$s=[IO.File]::Open('" + str(lock).replace("'", "''") + "',[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None); Start-Sleep -Seconds 8; $s.Dispose()"
    holder = subprocess.Popen([PWSH, "-NoProfile", "-Command", command])
    try:
        time.sleep(0.5)
        result = _apply(release, home, state, op, expect=2)
        assert "contention" in result.stderr or "stale lock" in result.stderr
        assert lock.exists()
    finally:
        holder.terminate()
        holder.wait(timeout=10)


def test_second_ledger_profile_survives_apply_and_rollback(codex_dist, tmp_path):
    release, home, state = _release(tmp_path, codex_dist), tmp_path / "home", tmp_path / "state"
    home.mkdir()
    gpt = {"provider": "gpt", "subdir": ".github/skills", "owned_files": [".github/skills/x/SKILL.md"],
           "owned_file_hashes": {".github/skills/x/SKILL.md": "a" * 64}, "created_dirs": []}
    initial = {"tool": "skill-mesh", "ledger_version": 1, "installs": {"gpt": gpt}}
    (home / ".skill-mesh-install.json").write_text(json.dumps(initial), encoding="utf-8")
    _, op, _ = _preview(release, home, state)
    _apply(release, home, state, op)
    assert json.loads((home / ".skill-mesh-install.json").read_text())["installs"]["gpt"] == gpt
    _rollback(state, op)
    assert json.loads((home / ".skill-mesh-install.json").read_text())["installs"]["gpt"] == gpt


def test_preview_refuses_missing_codex_directory(codex_dist, tmp_path):
    release = _release(tmp_path, codex_dist)
    shutil.rmtree(release / "dist/codex")
    result = _run("-Mode", "preview", "-ReleaseDir", release, "-TargetHome", tmp_path / "home", "-StateRoot", tmp_path / "state")
    assert result.returncode == 2 and "dist/codex" in result.stderr


def test_missing_required_mode_argument_is_exit_two():
    result = _run()
    assert result.returncode == 2 and "Mode" in result.stderr


def test_placeholder_path_is_refused(codex_dist, tmp_path):
    result = _run("-Mode", "inspect", "-ReleaseDir", "<releaseDir>")
    assert result.returncode == 2 and "placeholder" in result.stderr
