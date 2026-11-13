"""Producer -> consumer round trip for build-step's `landed-paths.json`.

PRODUCER: the real P1 helper `skills/build-step/scripts/build_step_tree.py`, driven
through its library API (`run_cli` with an injected `Context`, the only seam the
helper offers for its owner process and temp root) along the Step 8 path a passing
run takes: scope -> worktree-create -> changes -> land -> verify-landed -> archive.
`archive` writes `landed-paths.json` (schema `build-step-landed-paths/1`).

CONSUMER: build-phase's landed-paths reader, EXTRACTED from
`skills/build-phase/core.md` (the python heredoc in the section 2d recheck block)
and executed as written -- never a re-implementation in this file. Its result is
the commit set build-phase's 2e checkpoint stages (`commit-set.z`), the section 2c
`Files changed` list (`files-changed.txt`) and the 2d advisory notes
(`landed-notes.txt`).

The bug class this gates lives in the RELATIONSHIP (code-quality.md: grep every
consumer when a shape changes; integration test through the production caller):
the helper and the core are written by different lanes, so a schema string, a
key name, a path spelling, or a blob-id definition (filtered `git hash-object`
vs raw bytes; the clone runs `core.autocrlf=true`) can drift on either side
while each side's own tests stay green.

Real disposable Git repositories only, under `tmp_path`, with a hermetic Git
configuration. Nothing here commits outside those repositories.
"""

import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "skills" / "build-step" / "scripts" / "build_step_tree.py"
BUILD_PHASE_CORE = REPO_ROOT / "skills" / "build-phase" / "core.md"
SCHEMA = "build-step-landed-paths/1"

# The exact invocation line in the core: the argument ORDER is part of the contract.
_READER_RE = re.compile(
    r'^if ! python - "\$LANDED_LIST" "\$GIT_ROOT" "\$PROJECT_PREFIX" "\$PLAN_REL" '
    r'"\$SCOPE_DIR" <<\'PY\'\n(.*?)\nPY\n', re.S | re.M)


def _reader_source():
    text = BUILD_PHASE_CORE.read_bytes().decode("utf-8").replace("\r\n", "\n")
    found = _READER_RE.findall(text)
    assert len(found) == 1, (
        f"expected exactly one landed-paths reader heredoc in {BUILD_PHASE_CORE.name}, "
        f"found {len(found)}; the consumer this round trip grades has moved")
    return found[0] + "\n"


def _load_helper():
    assert HELPER.is_file(), f"producer missing: {HELPER}"
    name = "build_step_tree_roundtrip_under_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HELPER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses resolve their module through sys.modules
    spec.loader.exec_module(module)
    for attr in ("run_cli", "Context", "process_start_time"):
        assert hasattr(module, attr), f"producer no longer exposes {attr}"
    return module


def _git(cwd, *args, check=True):
    proc = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"git {args} failed: {proc.stderr.decode(errors='replace')}")
    return proc.stdout.decode("utf-8", "surrogateescape").strip()


@pytest.fixture
def hermetic_git(tmp_path, monkeypatch):
    config = tmp_path / "gitconfig"
    config.write_text("[user]\n\tname = roundtrip\n\temail = roundtrip@example.invalid\n"
                      "[init]\n\tdefaultBranch = main\n", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    for var in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(var, raising=False)
    return config


def _context(helper, tmp_path):
    pid = os.getpid()
    owner = {"pid": pid, "start_time": helper.process_start_time(pid),
             "host": socket.gethostname(), "exe": "pytest", "session_id": None}
    assert owner["start_time"], "the producer cannot read this process's start time"
    return helper.Context(owner_resolver=lambda: dict(owner),
                          temp_root=str(tmp_path / "platform-temp"))


def _ok(helper, ctx, *argv):
    result = helper.run_cli(list(argv), ctx)
    assert result.get("status") == "ok", f"{argv[0]} -> {result}"
    return result


def _operator_repo(tmp_path, autocrlf):
    repo = tmp_path / "operator" / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "core.autocrlf", "true" if autocrlf else "false")
    (repo / "app").mkdir()
    (repo / "docs").mkdir()
    (repo / "app" / "keep.txt").write_text("keep\n", encoding="utf-8")
    (repo / "app" / "edit.txt").write_text("before\n", encoding="utf-8")
    (repo / "app" / "gone.txt").write_text("gone\n", encoding="utf-8")
    (repo / "app" / "dirty.txt").write_text("clean\n", encoding="utf-8")
    (repo / "docs" / "plan.md").write_text("### Step 1: demo\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "baseline")
    return repo


def _land(helper, ctx, project_root, edits):
    """Run the real helper's passing-run landing and return its archive result."""
    scope = _ok(helper, ctx, "scope", "--project-root", str(project_root))
    branch = scope["run"]
    created = _ok(helper, ctx, "worktree-create", "--run", branch)
    worktree_project = Path(created["worktree_project"])
    for rel, content in edits.items():
        target = worktree_project / rel
        if content is None:
            target.unlink()
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    changes = _ok(helper, ctx, "changes", "--run", branch)
    assert changes["files"] == len(edits), changes
    _ok(helper, ctx, "land", "--run", branch)
    _ok(helper, ctx, "verify-landed", "--run", branch)
    archived = _ok(helper, ctx, "archive", "--run", branch)
    landed = Path(archived["landed_paths"])
    assert landed.is_file(), archived
    return branch, landed


def _scope_dir(tmp_path, repo, prefix, pre_dirty=()):
    """The parts of build-phase's Step 1 scope record and 2d block the reader reads."""
    scope = tmp_path / "scope"
    scope.mkdir(exist_ok=True)
    (scope / "preflight-dirty.z").write_bytes(b"".join(p.encode() + b"\0" for p in pre_dirty))
    spec = prefix or "."
    tracked = subprocess.run(["git", "diff", "--no-renames", "--name-only", "-z", "HEAD", "--", spec],
                             cwd=str(repo), capture_output=True, check=True).stdout
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z", "--", spec],
                               cwd=str(repo), capture_output=True, check=True).stdout
    changed = {p for p in (tracked + untracked).split(b"\0") if p} - {p.encode() for p in pre_dirty}
    (scope / "project-changes.z").write_bytes(b"".join(p + b"\0" for p in sorted(changed)))
    return scope


def _run_reader(landed_list, git_root, prefix, plan_rel, scope):
    proc = subprocess.run(
        [sys.executable, "-", str(landed_list), git_root, prefix, plan_rel, str(scope)],
        input=_reader_source().encode("utf-8"), capture_output=True)
    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    commit = {p.decode("utf-8") for p in (scope / "commit-set.z").read_bytes().split(b"\0") if p}
    files = (scope / "files-changed.txt").read_text(encoding="utf-8").splitlines()
    notes = (scope / "landed-notes.txt").read_text(encoding="utf-8").splitlines()
    return commit, files, notes


def _note(notes, label):
    hits = [n for n in notes if n.startswith(label + ": ")]
    assert len(hits) <= 1, notes
    return hits[0][len(label) + 2:] if hits else None


EDITS = {
    "edit.txt": b"after\n",
    "gone.txt": None,
    "new file.txt": b"brand new\n",
}
LANDED = {"app/edit.txt", "app/gone.txt", "app/new file.txt"}


@pytest.mark.parametrize("autocrlf", [False, True], ids=["autocrlf-false", "autocrlf-true"])
def test_real_helper_archive_feeds_the_core_reader(tmp_path, hermetic_git, autocrlf):
    helper = _load_helper()
    assert helper.SCHEMA_LANDED == SCHEMA, "producer schema string drifted"
    assert f'"{SCHEMA}"' in _reader_source(), "consumer schema string drifted"
    repo = _operator_repo(tmp_path, autocrlf)
    edits = dict(EDITS)
    if autocrlf:  # working-tree CRLF bytes; the blob id is the filtered (LF) one
        edits["edit.txt"] = b"after\r\n"
    ctx = _context(helper, tmp_path)
    _branch, landed = _land(helper, ctx, repo / "app", edits)

    doc = json.loads(landed.read_text(encoding="utf-8"))
    assert doc["schema"] == SCHEMA
    assert {e["path"] for e in doc["paths"]} == LANDED
    assert {e["path"]: e["state"] for e in doc["paths"]}["app/gone.txt"] == "deleted"

    git_root = _git(repo, "rev-parse", "--show-toplevel")
    # Another session's edit made during the step: never committed, named UNATTRIBUTED.
    (repo / "app" / "other-session.txt").write_text("not ours\n", encoding="utf-8")
    (repo / "docs" / "plan.md").write_text("### Step 1: demo\n- **Status:** DONE\n", encoding="utf-8")

    # MATCH: every landed path still holds its landed state.
    scope = _scope_dir(tmp_path, repo, "app")
    commit, files, notes = _run_reader(landed, git_root, "app", "docs/plan.md", scope)
    assert commit == LANDED | {"docs/plan.md"}
    assert set(files) == LANDED
    assert _note(notes, "LANDED-CHANGED") is None
    assert _note(notes, "LANDED-LIST-UNREADABLE") is None
    assert _note(notes, "UNATTRIBUTED") == "app/other-session.txt"

    # The 2e commit block stages exactly that set: the stray edit stays uncommitted.
    (scope / "commit-set.z").write_bytes(
        b"".join(p.encode() + b"\0" for p in sorted(commit)))
    for args in (["add", "-A"], ["commit", "-q", "-m", "checkpoint: step 1 complete"]):
        subprocess.run(["git", "--literal-pathspecs", "-C", git_root, *args,
                        f"--pathspec-from-file={scope / 'commit-set.z'}", "--pathspec-file-nul"],
                       capture_output=True, check=True)
    committed = set(_git(repo, "show", "--name-only", "--format=", "HEAD").splitlines())
    assert committed == LANDED | {"docs/plan.md"}
    assert "app/other-session.txt" in _git(repo, "status", "--porcelain")


def test_changed_blob_is_landed_changed_and_left_uncommitted(tmp_path, hermetic_git):
    helper = _load_helper()
    repo = _operator_repo(tmp_path, autocrlf=False)
    ctx = _context(helper, tmp_path)
    _branch, landed = _land(helper, ctx, repo / "app", dict(EDITS))
    git_root = _git(repo, "rev-parse", "--show-toplevel")

    (repo / "app" / "edit.txt").write_text("someone changed it after landing\n", encoding="utf-8")
    (repo / "app" / "gone.txt").write_text("recreated\n", encoding="utf-8")
    scope = _scope_dir(tmp_path, repo, "app")
    commit, files, notes = _run_reader(landed, git_root, "app", "docs/plan.md", scope)
    assert commit == {"app/new file.txt", "docs/plan.md"}
    assert _note(notes, "LANDED-CHANGED") == "app/edit.txt, app/gone.txt"
    assert set(files) == LANDED  # Files changed still names what build-step landed
    assert _note(notes, "UNATTRIBUTED") is None  # a changed landed path is not unattributed


def test_pre_existing_and_out_of_scope_paths_are_never_committed(tmp_path, hermetic_git):
    helper = _load_helper()
    repo = _operator_repo(tmp_path, autocrlf=False)
    ctx = _context(helper, tmp_path)
    _branch, landed = _land(helper, ctx, repo / "app", dict(EDITS))
    git_root = _git(repo, "rev-parse", "--show-toplevel")

    # Step 1 recorded app/edit.txt as pre-existing; the run was scoped to app/ only,
    # but the list names a docs/ path too (a garbage producer).
    doc = json.loads(landed.read_text(encoding="utf-8"))
    doc["paths"].append({"path": "docs/elsewhere.md", "state": "deleted"})
    widened = tmp_path / "widened.json"
    widened.write_text(json.dumps(doc), encoding="utf-8")
    scope = _scope_dir(tmp_path, repo, "app", pre_dirty=("app/edit.txt",))
    commit, _files, notes = _run_reader(widened, git_root, "app", "docs/plan.md", scope)
    assert commit == {"app/gone.txt", "app/new file.txt", "docs/plan.md"}
    assert _note(notes, "PRE-DIRTY-TOUCHED") == "app/edit.txt"
    assert _note(notes, "OUT-OF-SCOPE") == "docs/elsewhere.md"


@pytest.mark.parametrize("damage", [
    "missing-file", "not-json", "wrong-schema", "other-repository", "absolute-path",
    "dotdot-path", "bad-state", "duplicate-path", "paths-not-a-list", "empty-list-argument",
])
def test_unreadable_list_commits_the_plan_alone(tmp_path, hermetic_git, damage):
    helper = _load_helper()
    repo = _operator_repo(tmp_path, autocrlf=False)
    ctx = _context(helper, tmp_path)
    _branch, landed = _land(helper, ctx, repo / "app", dict(EDITS))
    git_root = _git(repo, "rev-parse", "--show-toplevel")
    doc = json.loads(landed.read_text(encoding="utf-8"))
    damaged = tmp_path / "damaged.json"
    if damage == "missing-file":
        target = tmp_path / "does-not-exist.json"
    elif damage == "empty-list-argument":
        target = ""
    else:
        target = damaged
        if damage == "not-json":
            damaged.write_text("{not json", encoding="utf-8")
        else:
            if damage == "wrong-schema":
                doc["schema"] = "build-step-landed-paths/2"
            elif damage == "other-repository":
                other = tmp_path / "other"
                other.mkdir()
                _git(other, "init", "-q")
                doc["git_root"] = _git(other, "rev-parse", "--show-toplevel")
            elif damage == "absolute-path":
                doc["paths"][0]["path"] = "/etc/passwd"
            elif damage == "dotdot-path":
                doc["paths"][0]["path"] = "app/../../escape.txt"
            elif damage == "bad-state":
                doc["paths"][0]["state"] = "not-a-blob"
            elif damage == "duplicate-path":
                doc["paths"].append(dict(doc["paths"][0]))
            elif damage == "paths-not-a-list":
                doc["paths"] = {"app/edit.txt": "deleted"}
            damaged.write_text(json.dumps(doc), encoding="utf-8")
    scope = _scope_dir(tmp_path, repo, "app")
    commit, files, notes = _run_reader(target, git_root, "app", "docs/plan.md", scope)
    assert commit == {"docs/plan.md"}, (damage, commit)
    assert files == ["path list unavailable"]
    assert _note(notes, "LANDED-LIST-UNREADABLE"), (damage, notes)
    # Narrower, never wider: the step's own landing is named, not committed.
    assert set((_note(notes, "UNATTRIBUTED") or "").split(", ")) == LANDED


def test_nested_project_prefix_round_trip(tmp_path, hermetic_git):
    """A project below the repository root (build-step PROJECT_PREFIX `app`) and a plan
    outside it: the helper lands only under the prefix and the reader keeps that scope."""
    helper = _load_helper()
    repo = _operator_repo(tmp_path, autocrlf=False)
    ctx = _context(helper, tmp_path)
    _branch, landed = _land(helper, ctx, repo / "app", {"sub dir/deep.txt": b"deep\n"})
    doc = json.loads(landed.read_text(encoding="utf-8"))
    assert [e["path"] for e in doc["paths"]] == ["app/sub dir/deep.txt"]
    git_root = _git(repo, "rev-parse", "--show-toplevel")
    scope = _scope_dir(tmp_path, repo, "app")
    commit, _files, notes = _run_reader(landed, git_root, "app", "", scope)
    assert commit == {"app/sub dir/deep.txt"}  # no plan in this repository: PLAN_REL empty
    assert notes == []
