"""build_step_tree.py (build-step P1 helper): CLI contract, change set, landing, stash, archive.

Every test drives real disposable Git repositories under tmp_path and asserts real repository
state (bytes on disk, `git stash list`, `git worktree list`, lock files), never a mocked PASS.
Owner handling and the hermetic environment are documented in build_step_tree_fixtures.py.
Concurrency, liveness and recovery scenarios (S1-S12, C1, D1-D4) live in
test_build_step_tree_recovery.py.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from build_step_tree_fixtures import (HELPER, STATUSES, bst, env, git, is_link, make_dir_link,  # noqa: F401
                                      make_repo, parse_one, tree_bytes, write)

BASE_FILES = {
    "a.txt": "alpha\n",
    "b.txt": "bravo\n",
    "old.txt": "to be deleted\n",
    "lines.txt": "".join(f"line {i}\n" for i in range(1, 21)),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------------------------------
# CLI contract
# ------------------------------------------------------------------------------------------

def test_scope_without_host_ancestor_is_unavailable(env, tmp_path):
    """Real CLI entry point (run as __main__) in a process whose parent has exited: no host
    ancestor exists, so scope must fail closed with `unavailable` and write no run state."""
    repo = make_repo(tmp_path / "repo", {"a.txt": "x\n"})
    out = tmp_path / "orphan.out"
    child = (
        "import os, sys, time, runpy, importlib.util\n"
        "ppid, helper, out, repo = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]\n"
        "spec = importlib.util.spec_from_file_location('bst_probe', helper)\n"
        "m = importlib.util.module_from_spec(spec); sys.modules['bst_probe'] = m; spec.loader.exec_module(m)\n"
        "end = time.time() + 30\n"
        "gone = (lambda: ppid not in m._win_table()) if os.name == 'nt' else (lambda: os.getppid() != ppid)\n"
        "while not gone() and time.time() < end: time.sleep(0.05)\n"
        "sys.stdout = open(out, 'w', encoding='utf-8')\n"
        "sys.argv = [helper, 'scope', '--project-root', repo]\n"
        "code = 0\n"
        "try:\n"
        "    runpy.run_path(helper, run_name='__main__')\n"
        "except SystemExit as exc:\n"
        "    code = exc.code\n"
        "sys.stdout.flush(); sys.stdout.close()\n"
        "open(out + '.rc', 'w').write(str(code))\n"
    )
    launcher = (
        "import os, subprocess, sys\n"
        "subprocess.Popen([sys.executable, '-c', sys.argv[1], str(os.getpid())] + sys.argv[2:],"
        " stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)\n"
    )
    subprocess.run([sys.executable, "-c", launcher, child, str(HELPER), str(out), str(repo)], check=True,
                   stdin=subprocess.DEVNULL, timeout=60)
    rc_file = Path(str(out) + ".rc")
    end = time.time() + 90
    while not rc_file.exists() and time.time() < end:
        time.sleep(0.1)
    assert rc_file.exists(), "orphaned helper did not finish"
    obj = parse_one(out.read_text(encoding="utf-8"))
    assert obj["status"] == "unavailable"
    assert obj["reason"] == "no host ancestor"
    assert int(rc_file.read_text()) == STATUSES["unavailable"]
    runs = env.root / "build-step-runs"
    assert not runs.exists() or not any(runs.iterdir())


def test_host_executable_names():
    assert bst._is_host_exe("claude.exe") and bst._is_host_exe("CLAUDE.EXE") and bst._is_host_exe("codex")
    assert not bst._is_host_exe("node.exe") and not bst._is_host_exe("python.exe") and not bst._is_host_exe("")


def test_exactly_one_json_object_on_every_error_path(env, tmp_path):
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    cases = [
        [],
        ["bogus"],
        ["--help"],
        ["stash-save"],
        ["changes", "--run", "../escape"],
        ["changes", "--run", "build-step-20260101T000000Z-deadbeef"],
        ["unlock", "evil.lock"],
        ["recover", "--check", "--project-root", str(plain)],
        ["test-count", "--command", "make test", "--log", str(plain / "missing.log")],
        ["budget", "advance", "--key", "nothex"],
        ["finalize", "--run", "build-step-20260101T000000Z-deadbeef"],
    ]
    seen = set()
    for argv in cases:
        obj = env.cli(*argv)  # asserts one JSON object + matching exit code
        seen.add(obj["status"])
        if argv != ["--help"]:
            assert obj["status"] in ("halt", "unavailable"), (argv, obj)
    assert "halt" in seen
    # a run-state file that is not valid JSON is reported, not crashed on
    bad = env.root / "build-step-runs" / "build-step-20260101T000000Z-0badf00d"
    bad.mkdir(parents=True)
    (bad / "state.json").write_text("{not json", encoding="utf-8")
    obj = env.cli("changes", "--run", bad.name)
    assert obj["status"] == "unavailable" and obj["reason"] == "run state unreadable"


# ------------------------------------------------------------------------------------------
# Full happy path: complete change set, landing, stash, archive, cleanup
# ------------------------------------------------------------------------------------------

def test_full_change_set_lands_and_cleans_up(env, tmp_path):
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    write(repo / "operator-notes.txt", "operator wip\n")  # untracked operator work -> stashed
    write(repo / "b.txt", "bravo operator edit\n")  # tracked operator work -> stashed
    owner = env.owner()
    branch = env.start(owner, repo)
    res = env.cli("stash-save", "--run", branch)
    assert res["status"] == "ok" and res["stashed"] is True
    assert sorted(res["stash"]["paths"]) == ["b.txt", "operator-notes.txt"]
    assert git(repo, "status", "--porcelain") == ""
    wt = env.cli("worktree-create", "--run", branch)
    assert wt["status"] == "ok"
    wtp = Path(wt["worktree_project"])
    assert not str(wtp).lower().startswith(str(repo).lower() + os.sep)
    # developer: a commit, a staged new file, an unstaged edit, an untracked file, a deletion,
    # plus orchestrator files that must never land
    write(wtp / "a.txt", "alpha developer\n")
    git(wtp, "add", "a.txt")
    git(wtp, "-c", "user.name=d", "-c", "user.email=d@d", "commit", "-q", "-m", "dev commit")
    write(wtp / "c.txt", "staged new\n")
    git(wtp, "add", "c.txt")
    write(wtp / "lines.txt", "changed\n")
    write(wtp / "new dir" / "d e.txt", "untracked new file with spaces\n")
    (wtp / "old.txt").unlink()
    write(wtp / ".build-step" / "dev-report.md", "report\n")
    write(wtp / ".review-deep" / "x.json", "{}\n")
    ch = env.cli("changes", "--run", branch)
    assert ch["status"] == "ok"
    assert ch["paths"] == ["a.txt", "c.txt", "lines.txt", "new dir/d e.txt", "old.txt"]
    patch = Path(ch["patch"]).read_bytes()
    assert sha(patch) == ch["payload_sha256"]
    assert b"untracked new file with spaces" in patch and b".build-step" not in patch
    th1 = env.cli("tree-hash", "--run", branch)
    th2 = env.cli("tree-hash", "--run", branch)
    assert th1["tree_hash"] == th2["tree_hash"]
    land = env.cli("land", "--run", branch)
    assert land["status"] == "ok", land
    assert (repo / "a.txt").read_bytes() == b"alpha developer\n"
    assert (repo / "c.txt").read_bytes() == b"staged new\n"
    assert (repo / "new dir" / "d e.txt").read_bytes() == b"untracked new file with spaces\n"
    assert not (repo / "old.txt").exists()
    assert not (repo / ".build-step").exists() and not (repo / ".review-deep").exists()
    assert git(repo, "diff", "--cached", "--name-only") == ""  # landing never writes the index
    assert git(repo, "rev-parse", "HEAD") == env.state(branch)["baseline"]  # never commits
    assert any(name.startswith("skill-mesh-tree-") for name in env.lock_files(repo))
    ver = env.cli("verify-landed", "--run", branch)
    assert ver["status"] == "ok"
    assert env.lock_files(repo) == {}
    rest = env.cli("stash-restore", "--run", branch)
    assert rest["status"] == "ok" and rest["restored"] is True
    assert git(repo, "stash", "list") == ""
    assert (repo / "operator-notes.txt").read_text() == "operator wip\n"
    assert (repo / "b.txt").read_text() == "bravo operator edit\n"
    arc = env.cli("archive", "--run", branch)
    assert arc["status"] == "ok"
    doc = json.loads(Path(arc["landed_paths"]).read_text(encoding="utf-8"))
    assert set(doc) == {"schema", "branch", "git_root", "paths"}
    assert doc["schema"] == "build-step-landed-paths/1" and doc["branch"] == branch
    assert doc["git_root"] == git(repo, "rev-parse", "--show-toplevel")
    states = {p["path"]: p["state"] for p in doc["paths"]}
    assert states["old.txt"] == "deleted"
    for rel in ("a.txt", "c.txt", "lines.txt", "new dir/d e.txt"):
        assert states[rel] == git(repo, "hash-object", "--", rel)
    assert (Path(arc["archive"]) / ".build-step" / "dev-report.md").exists()
    assert (Path(arc["archive"]) / "payload.patch").read_bytes() == patch
    worktree_path = env.state(branch)["worktree"]
    cl = env.cli("cleanup", "--run", branch)
    assert cl["status"] == "ok"
    assert not os.path.exists(worktree_path)
    assert git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1
    assert git(repo, "branch", "--list", branch) == ""
    assert not (env.root / "build-step-runs" / branch).exists()
    # tree= after cleanup: recover --check from the project
    chk = env.cli("recover", "--check", "--project-root", repo)
    assert chk["status"] == "ok" and chk["tree"] == "clean"


def test_scope_escape_is_reported_and_nothing_lands(env, tmp_path):
    repo = make_repo(tmp_path / "repo", {"root.txt": "root\n", "frontend/app.js": "app\n"})
    owner = env.owner()
    branch = env.start(owner, repo / "frontend")
    st = env.state(branch)
    assert st["project_prefix"] == "frontend/" and st["project_root"].lower().endswith("frontend")
    wt = env.cli("worktree-create", "--run", branch)
    wtroot, wtp = Path(wt["worktree"]), Path(wt["worktree_project"])
    write(wtp / "app.js", "app changed\n")
    write(wtroot / "root.txt", "escaped\n")
    write(wtroot / ".build-step" / "x.md", "orchestrator path outside the prefix is still an escape\n")
    res = env.cli("changes", "--run", branch)
    assert res["status"] == "scope-escape"
    assert res["paths"] == [".build-step/x.md", "root.txt"]
    assert env.state(branch)["payload"] is None
    assert (repo / "frontend" / "app.js").read_text() == "app\n"
    assert (repo / "root.txt").read_text() == "root\n"


def test_same_size_edits_right_after_checkout_are_captured(env, tmp_path):
    """Regression: a same-size edit within the checkout's timestamp granularity must not be
    hidden by stale index stat data (the payload is content-hashed)."""
    repo = make_repo(tmp_path / "repo", {f"f{i}.txt": "0000\n" for i in range(8)})
    branch = env.start(env.owner(), repo)
    wtp = Path(env.cli("worktree-create", "--run", branch)["worktree_project"])
    for i in range(8):
        (wtp / f"f{i}.txt").write_bytes(b"1111\n")  # same size, written immediately
    first = env.cli("changes", "--run", branch)
    assert first["paths"] == [f"f{i}.txt" for i in range(8)]
    again = env.cli("changes", "--run", branch)
    assert again["payload_sha256"] == first["payload_sha256"]


def test_empty_payload_is_reported(env, tmp_path):
    repo = make_repo(tmp_path / "repo", {"a.txt": "a\n"})
    branch, _wtp = env.prepare(env.owner(), repo, {".build-step/report.md": "only orchestrator files\n"})
    st = env.state(branch)
    assert st["payload"]["entries"] == []
    assert env.cli("changes", "--run", branch)["empty"] is True


# ------------------------------------------------------------------------------------------
# Landing classification (Step 8.3)
# ------------------------------------------------------------------------------------------

def test_merge_file_merges_operator_change_without_touching_index(env, tmp_path):
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    original = (repo / "lines.txt").read_text()
    dev = original.replace("line 1\n", "line 1 developer\n")
    branch, _wtp = env.prepare(env.owner(), repo, {"lines.txt": dev})
    write(repo / "lines.txt", original.replace("line 20\n", "line 20 operator\n"))  # operator edit during run
    res = env.cli("land", "--run", branch)
    assert res["status"] == "ok", res
    merged = (repo / "lines.txt").read_text()
    assert "line 1 developer\n" in merged and "line 20 operator\n" in merged
    assert git(repo, "diff", "--cached", "--name-only") == ""
    assert env.cli("verify-landed", "--run", branch)["status"] == "ok"


def test_merge_conflict_writes_nothing_and_rollback_is_noop(env, tmp_path):
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    original = (repo / "lines.txt").read_text()
    branch, _wtp = env.prepare(env.owner(), repo, {"lines.txt": original.replace("line 5\n", "dev five\n"),
                                                    "a.txt": "alpha dev\n"})
    operator_bytes = original.replace("line 5\n", "operator five\n").encode()
    write(repo / "lines.txt", operator_bytes)
    res = env.cli("land", "--run", branch)
    assert res["status"] == "halt" and res["reason"] == "merge conflict"
    assert [c["path"] for c in res["conflicts"]] == ["lines.txt"]
    assert (repo / "lines.txt").read_bytes() == operator_bytes
    assert (repo / "a.txt").read_text() == "alpha\n"  # nothing written, not even the clean path
    assert env.lock_files(repo) == {}
    rb = env.cli("land-rollback", "--run", branch)
    assert rb["status"] == "ok" and rb.get("noop") is True
    fin = env.cli("finalize", "merge conflict", "--run", branch)
    assert fin["status"] == "ok" and fin["tree"] == "clean" and fin["finalized"] == "merge conflict"


def test_untracked_collision_and_stash_overlap_are_conflicts(env, tmp_path):
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    branch, _wtp = env.prepare(env.owner(), repo, {"new.txt": "dev new\n"})
    write(repo / "new.txt", "operator untracked\n")
    res = env.cli("land", "--run", branch)
    assert res["status"] == "halt" and res["reason"] == "merge conflict"
    assert (repo / "new.txt").read_text() == "operator untracked\n"
    # Step 8.2: a stashed operator path in the payload is a conflict before any write
    repo2 = make_repo(tmp_path / "repo2", BASE_FILES)
    write(repo2 / "a.txt", "operator a\n")
    branch2, _ = env.prepare(env.owner(), repo2, {"a.txt": "dev a\n"}, stash=True)
    res2 = env.cli("land", "--run", branch2)
    assert res2["status"] == "halt" and res2["reason"] == "merge conflict" and res2["overlap"] == ["a.txt"]
    assert (repo2 / "a.txt").read_text() == "alpha\n"
    assert env.cli("stash-restore", "--run", branch2)["restored"] is True
    assert (repo2 / "a.txt").read_text() == "operator a\n"


def test_released_landing_is_never_rolled_back(env, tmp_path):
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    branch, _ = env.prepare(env.owner(), repo, {"a.txt": "landed\n"})
    assert env.cli("land", "--run", branch)["status"] == "ok"
    assert env.cli("verify-landed", "--run", branch)["status"] == "ok"
    for sub in ("land-rollback", "preview-rollback"):
        res = env.cli(sub, "--run", branch)
        assert res["status"] == "ok" and res.get("noop") is True
    assert (repo / "a.txt").read_text() == "landed\n"
    fin = env.cli("finalize", "cleanup failed", "--run", branch)
    assert fin["tree"] == "clean"
    assert (repo / "a.txt").read_text() == "landed\n"


def test_payload_changed_after_review_is_refused_before_any_lock(env, tmp_path):
    """Red-on-garbage anchor: a payload tampered after review never lands."""
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    branch, wtp = env.prepare(env.owner(), repo, {"a.txt": "reviewed\n"})
    write(wtp / "a.txt", "tampered after review\n")
    res = env.cli("land", "--run", branch)
    assert res["status"] == "halt" and res["reason"] == "payload changed after review"
    assert res["stage"] == "before-lock" and res["lock_taken"] is False
    assert (repo / "a.txt").read_text() == "alpha\n"
    assert env.lock_files(repo) == {}
    assert [s for s in env.state(branch)["snapshots"]] == []
    fin = env.cli("finalize", "payload changed after review", "--run", branch)
    assert fin["tree"] == "clean"
    # the next run in this tree takes the tree lock at once
    branch2, _ = env.prepare(env.owner(), repo, {"b.txt": "next\n"})
    assert env.cli("preview-apply", "--run", branch2)["status"] == "ok"
    assert env.cli("preview-rollback", "--run", branch2)["status"] == "ok"


def test_tampered_landing_fails_verification_and_leftover_is_saved(env, tmp_path):
    """Red-on-garbage anchor: bytes changed after the landing fail verify-landed; rollback keeps
    the foreign bytes as a leftover with both saved versions and restores the rest."""
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    branch, _ = env.prepare(env.owner(), repo, {"a.txt": "dev a\n", "b.txt": "dev b\n"})
    assert env.cli("land", "--run", branch)["status"] == "ok"
    write(repo / "a.txt", "someone else\n")
    ver = env.cli("verify-landed", "--run", branch)
    assert ver["status"] == "halt" and ver["reason"] == "landing verification failed" and ver["paths"] == ["a.txt"]
    rb = env.cli("land-rollback", "--run", branch)
    assert rb["status"] == "halt" and rb["reason"] == "rollback failed"
    (left,) = rb["leftovers"]
    assert left["path"] == "a.txt"
    assert Path(left["saved"]["prior"]).read_bytes() == b"alpha\n"
    assert Path(left["saved"]["written"]).read_bytes() == b"dev a\n"
    assert (repo / "a.txt").read_text() == "someone else\n"
    assert (repo / "b.txt").read_text() == "bravo\n"
    fin = env.cli("finalize", "landing verification failed", "--run", branch)
    assert fin["tree"] == "leftover" and fin["holds_tree_lock"] is True


def test_preview_apply_and_rollback_restore_exact_prior_state(env, tmp_path):
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    branch, _ = env.prepare(env.owner(), repo, {"a.txt": "preview a\n", "old.txt": None,
                                                 "deep/new/file.txt": "new\n"})
    pre = env.cli("preview-apply", "--run", branch)
    assert pre["status"] == "ok"
    assert (repo / "a.txt").read_text() == "preview a\n" and not (repo / "old.txt").exists()
    assert (repo / "deep" / "new" / "file.txt").exists()
    again = env.cli("preview-apply", "--run", branch)
    assert again["status"] == "halt" and again["reason"] == "active snapshot"
    rb = env.cli("preview-rollback", "--run", branch)
    assert rb["status"] == "ok"
    assert (repo / "a.txt").read_text() == "alpha\n" and (repo / "old.txt").read_text() == "to be deleted\n"
    assert not (repo / "deep").exists()
    assert git(repo, "status", "--porcelain") == ""
    assert env.lock_files(repo) == {}


def test_autocrlf_true_landing_uses_working_tree_bytes_and_blob_ids(env, tmp_path):
    repo = make_repo(tmp_path / "repo", {"t.txt": "one\ntwo\n", "keep.txt": "k\n"}, autocrlf=True)
    assert (repo / "t.txt").read_bytes() == b"one\r\ntwo\r\n"
    owner = env.owner()
    branch, wtp = env.prepare(owner, repo, {"t.txt": b"one\r\ntwo\r\nthree\r\n", "n.txt": b"new\r\n"})
    pre = env.cli("preview-apply", "--run", branch)
    assert pre["status"] == "ok"
    assert (repo / "t.txt").read_bytes() == b"one\r\ntwo\r\nthree\r\n"
    assert env.cli("preview-rollback", "--run", branch)["status"] == "ok"
    assert (repo / "t.txt").read_bytes() == b"one\r\ntwo\r\n"  # raw prior bytes restored exactly
    assert env.cli("land", "--run", branch)["status"] == "ok"
    assert (repo / "t.txt").read_bytes() == b"one\r\ntwo\r\nthree\r\n"
    assert env.cli("verify-landed", "--run", branch)["status"] == "ok"
    arc = env.cli("archive", "--run", branch)
    doc = json.loads(Path(arc["landed_paths"]).read_text(encoding="utf-8"))
    states = {p["path"]: p["state"] for p in doc["paths"]}
    lf_blob = git(repo, "hash-object", "--stdin", input=b"one\ntwo\nthree\n")
    assert states["t.txt"] == lf_blob == git(repo, "hash-object", "--", "t.txt")
    assert git(repo, "status", "--porcelain", "--", "keep.txt") == ""


# ------------------------------------------------------------------------------------------
# Stash, finalize, cleanup guards, T12
# ------------------------------------------------------------------------------------------

def test_stash_is_scoped_to_project_prefix(env, tmp_path):
    repo = make_repo(tmp_path / "repo", {"root.txt": "r\n", "frontend/app.js": "a\n"})
    write(repo / "root.txt", "operator root edit\n")
    write(repo / "frontend" / "app.js", "operator app edit\n")
    write(repo / "frontend" / "wip.js", "untracked wip\n")
    branch = env.start(env.owner(), repo / "frontend")
    res = env.cli("stash-save", "--run", branch)
    assert res["status"] == "ok" and sorted(res["stash"]["paths"]) == ["frontend/app.js", "frontend/wip.js"]
    assert (repo / "root.txt").read_text() == "operator root edit\n"  # outside the prefix: untouched
    assert not (repo / "frontend" / "wip.js").exists()
    entries = git(repo, "stash", "list", "--format=%gs").splitlines()
    assert entries == [f"On main: build-step {branch}"]
    assert env.cli("stash-restore", "--run", branch)["restored"] is True
    assert (repo / "frontend" / "wip.js").read_text() == "untracked wip\n"
    assert git(repo, "stash", "list") == ""


def test_finalized_run_refuses_every_call_but_recover(env, tmp_path):
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    branch, _ = env.prepare(env.owner(), repo, {"a.txt": "x\n"})
    assert env.cli("finalize", "developer BLOCKED", "--run", branch)["status"] == "ok"
    for sub in ("changes", "land", "stash-restore", "preview-apply", "cleanup", "finalize"):
        argv = [sub, "--run", branch] if sub != "finalize" else ["finalize", "again", "--run", branch]
        res = env.cli(*argv)
        assert res["status"] == "halt" and res["reason"] == "run finalized", (sub, res)
    assert env.cli("recover", "--check", "--run", branch)["status"] == "ok"


def test_cleanup_refuses_while_stash_saved_or_snapshot_active(env, tmp_path):
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    write(repo / "notes.txt", "wip\n")
    branch, _ = env.prepare(env.owner(), repo, {"a.txt": "x\n"}, stash=True)
    res = env.cli("cleanup", "--run", branch)
    assert res["status"] == "halt" and res["reason"] == "cleanup refused"
    assert env.cli("stash-restore", "--run", branch)["restored"] is True
    assert env.cli("preview-apply", "--run", branch)["status"] == "ok"
    res = env.cli("cleanup", "--run", branch)
    assert res["status"] == "halt" and res["reason"] == "cleanup refused"
    assert os.path.isdir(env.state(branch)["worktree"])


# ------------------------------------------------------------------------------------------
# Correction cycle 1: links (RF-1, RF-2), stash byte fidelity and index scope (RF-3, RF-4),
# tree-hash sensitivity (RF-7)
# ------------------------------------------------------------------------------------------

def test_cleanup_removes_a_junction_as_a_link_never_its_target(env, tmp_path):
    """RF-1: a dependency-install junction in the child worktree points at operator data outside
    GIT_ROOT and outside the worktree; cleanup must never delete through it."""
    sentinel = tmp_path / "operator-sibling"
    write(sentinel / "src" / "precious.js", "operator work outside GIT_ROOT\n")
    write(sentinel / "README.md", b"keep\r\nme\n")
    before = tree_bytes(sentinel)
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    branch = env.start(env.owner(), repo)
    wt = Path(env.cli("worktree-create", "--run", branch)["worktree"])
    link = wt / "node_modules" / "dep"
    make_dir_link(link, sentinel)
    assert (link / "src" / "precious.js").read_text() == "operator work outside GIT_ROOT\n"
    res = env.cli("cleanup", "--run", branch)
    assert tree_bytes(sentinel) == before  # every sentinel file still exists, byte-identical
    assert res["status"] == "ok", res
    assert [os.path.normcase(p) for p in res["links_removed"]] == [os.path.normcase(str(link))]
    assert not os.path.lexists(wt)
    assert git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1
    assert git(repo, "branch", "--list", branch) == ""
    assert not (env.root / "build-step-runs" / branch).exists()


def test_stash_save_refuses_a_junction_under_the_prefix(env, tmp_path):
    """RF-2: an untracked, non-ignored junction under the prefix is refused before any push."""
    sentinel = tmp_path / "outside-sentinel"
    write(sentinel / "keep" / "precious.txt", "operator data outside the repository\n")
    before = tree_bytes(sentinel)
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    write(repo / "wip.txt", "operator wip\n")
    link = repo / "vendor"
    make_dir_link(link, sentinel)
    branch = env.start(env.owner(), repo)
    ref_before = git(repo, "rev-parse", "-q", "--verify", "refs/stash", check=False)
    res = env.cli("stash-save", "--run", branch)
    assert res["status"] == "halt" and res["reason"] == "stash failed", res
    assert res["links"] == ["vendor"]
    assert git(repo, "rev-parse", "-q", "--verify", "refs/stash", check=False) == ref_before == ""
    assert git(repo, "stash", "list") == ""
    assert env.state(branch)["stash"]["state"] == "none"
    assert tree_bytes(sentinel) == before
    assert is_link(link) and (link / "keep" / "precious.txt").read_bytes() == before["keep/precious.txt"]
    assert (repo / "wip.txt").read_text() == "operator wip\n"
    assert env.lock_files(repo) == {}


def test_stash_round_trip_is_raw_byte_faithful_under_autocrlf(env, tmp_path):
    """RF-3: core.autocrlf=true (the workspace setting): LF and mixed-EOL operator files come back
    with their exact raw bytes, and finalize reports tree=clean."""
    repo = make_repo(tmp_path / "repo", {"app.js": "one\ntwo\n", "keep.txt": "k\n"}, autocrlf=True)
    assert (repo / "app.js").read_bytes() == b"one\r\ntwo\r\n"
    operator = {
        "deploy.sh": b"#!/bin/sh\necho deploy\n",  # untracked, LF on purpose
        "app.js": b"one\ntwo\nthree\n",  # tracked, rewritten by an editor with LF
        "notes.md": b"a\r\nb\nc\r\n",  # mixed line endings
    }
    for rel, data in operator.items():
        write(repo / rel, data)
    branch = env.start(env.owner(), repo)
    res = env.cli("stash-save", "--run", branch)
    assert res["status"] == "ok" and res["stashed"] is True, res
    assert res["stash"]["paths"] == ["app.js", "deploy.sh", "notes.md"]
    assert not (repo / "deploy.sh").exists() and (repo / "app.js").read_bytes() == b"one\r\ntwo\r\n"
    rest = env.cli("stash-restore", "--run", branch)
    assert rest["status"] == "ok" and rest["restored"] is True, rest
    for rel, data in operator.items():
        assert (repo / rel).read_bytes() == data, rel
    assert git(repo, "stash", "list") == ""
    fin = env.cli("finalize", "developer BLOCKED", "--run", branch)
    assert fin["status"] == "ok" and fin["tree"] == "clean", fin
    for rel, data in operator.items():
        assert (repo / rel).read_bytes() == data, rel


def _index_and_bytes(repo: Path, rels) -> dict:
    return {"cached": git(repo, "diff", "--cached", "--name-only"), "unstaged": git(repo, "diff", "--name-only"),
            "untracked": git(repo, "ls-files", "--others", "--exclude-standard"), "index": git(repo, "ls-files", "-s"),
            "bytes": {rel: (repo / rel).read_bytes() if (repo / rel).exists() else None for rel in rels}}


def test_stash_save_refuses_staged_changes_outside_the_prefix(env, tmp_path):
    """RF-4 (S2 nested-project shape): staged root.txt plus staged+unstaged frontend/app.js and an
    untracked frontend/wip.js, run scoped to frontend/: refused before the push, nothing changed."""
    repo = make_repo(tmp_path / "repo", {"root.txt": "r\n", "frontend/app.js": "a\n"})
    write(repo / "root.txt", "r\nstaged by operator for the root project\n")
    git(repo, "add", "root.txt")
    write(repo / "frontend" / "app.js", "a\noperator staged\n")
    git(repo, "add", "frontend/app.js")
    write(repo / "frontend" / "app.js", "a\noperator staged\nand unstaged\n")
    write(repo / "frontend" / "wip.js", "untracked wip\n")
    rels = ["root.txt", "frontend/app.js", "frontend/wip.js"]
    pre = _index_and_bytes(repo, rels)
    branch = env.start(env.owner(), repo / "frontend")
    res = env.cli("stash-save", "--run", branch)
    assert res["status"] == "halt" and res["reason"] == "stash failed", res
    assert res["staged_outside_prefix"] == ["root.txt"]
    assert git(repo, "stash", "list") == ""
    assert env.state(branch)["stash"] == {"state": "none"}  # the refusal recorded nothing: no paths, no raw copies
    assert _index_and_bytes(repo, rels) == pre
    assert env.lock_files(repo) == {}


def test_in_prefix_staged_changes_round_trip_through_the_index(env, tmp_path):
    """RF-4 / X07: staged in-prefix changes come back staged (apply --index); out-of-prefix
    unstaged work is never stashed and never recorded."""
    repo = make_repo(tmp_path / "repo", {"root.txt": "r\n", "frontend/app.js": "a\n", "frontend/lib.js": "l\n"})
    write(repo / "root.txt", "operator unstaged root edit\n")
    write(repo / "frontend" / "app.js", "a\nstaged\n")
    git(repo, "add", "frontend/app.js")
    write(repo / "frontend" / "app.js", "a\nstaged\nplus unstaged\n")
    write(repo / "frontend" / "new.js", "staged new file\n")
    git(repo, "add", "frontend/new.js")
    write(repo / "frontend" / "wip.js", "untracked\n")
    rels = ["root.txt", "frontend/app.js", "frontend/lib.js", "frontend/new.js", "frontend/wip.js"]
    pre = _index_and_bytes(repo, rels)
    assert pre["cached"].splitlines() == ["frontend/app.js", "frontend/new.js"]
    branch = env.start(env.owner(), repo / "frontend")
    res = env.cli("stash-save", "--run", branch)
    assert res["status"] == "ok" and res["stashed"] is True, res
    assert res["stash"]["paths"] == ["frontend/app.js", "frontend/new.js", "frontend/wip.js"]
    assert git(repo, "diff", "--cached", "--name-only") == ""
    assert (repo / "root.txt").read_text() == "operator unstaged root edit\n"
    rest = env.cli("stash-restore", "--run", branch)
    assert rest["status"] == "ok" and rest["restored"] is True, rest
    post = _index_and_bytes(repo, rels)
    assert post["cached"] == pre["cached"]  # X07: without --index the staged state is lost
    assert post == pre
    assert git(repo, "stash", "list") == ""


def test_tree_hash_changes_on_reviewer_visible_writes_only(env, tmp_path):
    """RF-7: tree-hash must be able to fail: it changes on tracked, untracked and operator
    payload-path writes, and ignores orchestrator and gitignored paths."""
    repo = make_repo(tmp_path / "repo", {**BASE_FILES, ".gitignore": "ignored/\n*.log\n"})
    branch, wtp = env.prepare(env.owner(), repo, {"a.txt": "dev a\n"})

    def tree_hash() -> str:
        res = env.cli("tree-hash", "--run", branch)
        assert res["status"] == "ok", res
        return res["tree_hash"]

    h0 = tree_hash()
    assert tree_hash() == h0
    write(wtp / ".build-step" / "reviewer-note.md", "orchestrator path\n")
    assert tree_hash() == h0
    write(wtp / ".review-deep" / "lens.json", "{}\n")
    assert tree_hash() == h0
    write(wtp / "ignored" / "cache.bin", b"\x00\x01")
    write(wtp / "run.log", "ignored log\n")
    assert tree_hash() == h0
    seen = {h0}
    write(wtp / "b.txt", "a reviewer wrote a tracked file\n")
    h1 = tree_hash()
    assert h1 not in seen
    seen.add(h1)
    write(wtp / "stray.txt", "a new untracked, non-ignored file\n")
    h2 = tree_hash()
    assert h2 not in seen
    seen.add(h2)
    write(repo / "a.txt", "an edit of an operator-tree payload path\n")
    h3 = tree_hash()
    assert h3 not in seen


# ------------------------------------------------------------------------------------------
# Correction cycle 2: the RF-3 non-equivalent drift branch (R2-4) and the cleanup guard (R2-5)
# ------------------------------------------------------------------------------------------

def _stash_with_smudge_drift(env, tmp_path, owner) -> tuple:
    """An untracked operator file under a smudge-only filter: `git stash` stores its clean
    (identity) blob b"fresh\\n", and `stash apply` checks it out through the smudge filter as
    b"fresh X\\n", which is NOT Git-equivalent to the raw bytes saved at stash-save."""
    repo = make_repo(tmp_path / "repo", {**BASE_FILES, ".gitattributes": "new.txt filter=tag\n"})
    git(repo, "config", "filter.tag.smudge", "sed 's/$/ X/'")
    write(repo / "new.txt", b"fresh\n")
    branch = env.start(owner, repo)
    res = env.cli("stash-save", "--run", branch)
    assert res["status"] == "ok" and res["stash"]["paths"] == ["new.txt"], res
    assert not (repo / "new.txt").exists()
    return repo, branch


def _saved_copy_dir(env, branch) -> str:
    return os.path.normcase(str(env.root / "build-step-runs" / branch / "leftovers" / "stash"))


def test_stash_restore_reports_non_equivalent_drift_and_keeps_the_saved_bytes(env, tmp_path):
    """R2-4 (TQ-A-1 = GS-A9): drift that Git does not treat as equivalent is never returned as a
    silent `restored` or `tree=clean`: halt `restore failed` naming the path, the pre-run raw bytes
    kept under leftovers/stash/, the operator file not overwritten, finalize `tree=leftover`."""
    repo, branch = _stash_with_smudge_drift(env, tmp_path, env.owner())
    rest = env.cli("stash-restore", "--run", branch)
    assert rest["status"] == "halt" and rest["reason"] == "restore failed", rest
    (item,) = rest["drift"]
    assert item["path"] == "new.txt"
    assert os.path.normcase(os.path.dirname(item["saved"])) == _saved_copy_dir(env, branch)
    assert Path(item["saved"]).read_bytes() == b"fresh\n"  # the operator's pre-run raw bytes
    assert (repo / "new.txt").read_bytes() == b"fresh X\n"  # the applied bytes are not overwritten
    assert git(repo, "stash", "list") == ""
    stash = env.state(branch)["stash"]
    assert stash["state"] == "restored" and [d["path"] for d in stash.get("drift", [])] == ["new.txt"], stash
    fin = env.cli("finalize", "restore failed", "--run", branch)
    assert fin["status"] == "ok" and fin["tree"] == "leftover", fin
    assert "stash restored with drift" in fin["tree_reasons"] and fin["tree_paths"] == ["new.txt"]
    assert Path(item["saved"]).read_bytes() == b"fresh\n"


def test_recover_of_a_dead_run_reports_stash_drift(env, tmp_path):
    """R2-4 through `recover <b>` of a dead run: `recover halted: stash restored with drift`, the
    saved bytes kept, no lock left; a second plain recover finishes as `recovered` with a note."""
    owner = env.owner()
    repo, branch = _stash_with_smudge_drift(env, tmp_path, owner)
    owner.kill()
    rec = env.cli("recover", branch)
    assert rec["status"] == "halt" and rec["reason"] == "recover halted: stash restored with drift", rec
    (item,) = rec["drift"]
    assert item["path"] == "new.txt" and Path(item["saved"]).read_bytes() == b"fresh\n"
    assert os.path.normcase(os.path.dirname(item["saved"])) == _saved_copy_dir(env, branch)
    assert (repo / "new.txt").read_bytes() == b"fresh X\n"
    st = env.state(branch)
    assert st["finalized"] is None and st["stash"]["state"] == "restored"
    assert [d["path"] for d in st["stash"].get("drift", [])] == ["new.txt"]
    assert env.lock_files(repo) == {} and git(repo, "stash", "list") == ""
    again = env.cli("recover", branch)
    assert again["status"] == "ok" and again["result"] == "recovered", again
    assert any("stash restored with drift" in n and "new.txt" in n for n in again["notes"]), again["notes"]
    assert Path(item["saved"]).read_bytes() == b"fresh\n"


def test_cleanup_refuses_while_drifted_bytes_exist_only_in_run_state(env, tmp_path):
    """R2-5 (GS-A2): after a drift halt the saved copy under run state is the only copy of the
    operator's stash-save bytes; cleanup must not delete it (it refuses and names it)."""
    repo, branch = _stash_with_smudge_drift(env, tmp_path, env.owner())
    rest = env.cli("stash-restore", "--run", branch)
    assert rest["status"] == "halt" and rest["reason"] == "restore failed", rest
    (item,) = rest["drift"]
    wt = env.cli("worktree-create", "--run", branch)["worktree"]
    res = env.cli("cleanup", "--run", branch)
    assert os.path.exists(item["saved"]) and Path(item["saved"]).read_bytes() == b"fresh\n"
    assert res["status"] == "halt" and res["reason"] == "cleanup refused", res
    assert res["drift"] == [{"path": "new.txt", "saved": item["saved"]}]
    assert (env.root / "build-step-runs" / branch / "state.json").exists()
    assert os.path.isdir(wt) and git(repo, "branch", "--list", branch) != ""
    assert (repo / "new.txt").read_bytes() == b"fresh X\n"


# ------------------------------------------------------------------------------------------
# Archive retention and budget
# ------------------------------------------------------------------------------------------

def test_archive_keeps_both_review_deep_sidecars_of_a_retried_round(env, tmp_path):
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    branch, wtp = env.prepare(env.owner(), repo, {"a.txt": "dev\n"})
    rdir = env.root / "build-step-runs" / branch
    first = {"timestamp": "20261012T010101Z", "lens_verdicts": [{"lens_id": "correctness",
             "overall_verdict": "NEEDS-WORK", "findings": [{"severity": "Block", "title": "kept"}]}]}
    retry = {"timestamp": "20261012T020202Z", "lens_verdicts": [{"lens_id": "correctness",
             "overall_verdict": "PASS", "findings": []}]}
    write(rdir / "reviews" / "round-1" / "review-deep" / "20261012T010101Z.json", json.dumps(first))
    write(rdir / "reviews" / "round-1" / "review-deep-retry" / "20261012T020202Z.json", json.dumps(retry))
    write(rdir / "reviews" / "round-2" / "correctness.json", json.dumps({"lens": "correctness", "round": 2}))
    write(rdir / "dispatch.json", json.dumps({"developer": {"requested": "inherit"}}))
    write(wtp / ".build-step" / "gate-test.log", "1 passed in 0.01s\n")
    assert env.cli("land", "--run", branch)["status"] == "ok"
    assert env.cli("verify-landed", "--run", branch)["status"] == "ok"
    arc = env.cli("archive", "--run", branch)
    adir = Path(arc["archive"])
    for rel in ("reviews/round-1/review-deep/20261012T010101Z.json",
                "reviews/round-1/review-deep-retry/20261012T020202Z.json",
                "reviews/round-2/correctness.json", "dispatch.json", ".build-step/gate-test.log", "payload.patch"):
        src = (rdir / rel) if not rel.startswith(".build-step") else (wtp / rel)
        assert (adir / rel).read_bytes() == src.read_bytes(), rel
    # the first sidecar's Block finding survives whole in the archive even though the retry passed
    kept = json.loads((adir / "reviews/round-1/review-deep/20261012T010101Z.json").read_text())
    assert kept["lens_verdicts"][0]["findings"][0]["severity"] == "Block"
    budget = env.cli("budget", "read", "--run", branch, "--issue", "7", "--problem", "p")
    env.cli("budget", "advance", "--run", branch)
    assert env.cli("cleanup", "--run", branch)["status"] == "ok"
    assert (adir / "landed-paths.json").exists()  # the archive outlives cleanup
    # cleanup removes run state but never the budget: only an explicit clear (after the PASS write) does
    assert json.loads(Path(budget["record"]).read_text(encoding="utf-8"))["consumed"] == 1
    assert env.cli("budget", "clear", "--key", budget["key"])["cleared"] is True
    assert not Path(budget["record"]).exists()


def test_budget_is_cumulative_per_step_and_cleared_only_explicitly(env, tmp_path):
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    r1 = env.start(env.owner(), repo)
    b = env.cli("budget", "read", "--run", r1, "--plan-step", "plan.md:3", "--problem", "Add reset")
    assert (b["limit"], b["consumed"], b["exhausted"]) == (10, 0, False)
    env.cli("budget", "advance", "--run", r1)
    b = env.cli("budget", "advance", "--run", r1)
    assert b["consumed"] == 2
    env.cli("finalize", "iteration budget exhausted", "--run", r1)
    r2 = env.start(env.owner(), repo)
    b2 = env.cli("budget", "read", "--run", r2, "--plan-step", "plan.md:3", "--problem", "Add reset")
    assert b2["key"] == b["key"] and (b2["limit"], b2["consumed"]) == (10, 2)  # continues, no reset
    b2 = env.cli("budget", "read", "--run", r2, "--plan-step", "plan.md:3", "--problem", "Add reset",
                 "--max-iter", "2")
    assert (b2["limit"], b2["consumed"], b2["exhausted"]) == (2, 2, True)  # limit replaced, count kept
    b2 = env.cli("budget", "read", "--run", r2, "--plan-step", "plan.md:3", "--problem", "Add reset")
    assert b2["limit"] == 2  # no newer default adopted
    other = env.cli("budget", "read", "--run", r2, "--plan-step", "plan.md:3", "--problem", "Different fix")
    assert other["key"] != b["key"] and other["consumed"] == 0
    r3 = env.start(env.owner(), repo)
    lone = env.cli("budget", "read", "--run", r3, "--problem", "Add reset")
    r4 = env.start(env.owner(), repo)
    lone2 = env.cli("budget", "read", "--run", r4, "--problem", "Add reset")
    assert lone["key"] != lone2["key"]  # no plan-step/issue: each invocation is its own step
    issue = env.cli("budget", "read", "--run", r4, "--issue", "42", "--problem", "Add reset")
    assert issue["key"] not in (b["key"], lone2["key"])
    record = Path(b2["record"])
    assert record.exists()
    cleared = env.cli("budget", "clear", "--key", b["key"])
    assert cleared["cleared"] is True and not record.exists()
    bad = env.cli("budget", "read", "--run", r4, "--problem", "x", "--max-iter", "0")
    assert bad["status"] == "halt"


# ------------------------------------------------------------------------------------------
# test-count
# ------------------------------------------------------------------------------------------

def test_test_count_resolves_wrappers_and_reads_counts(env, tmp_path):
    proj = tmp_path / "proj"
    write(proj / "package.json", json.dumps({"scripts": {"test": "npm run unit", "unit": "node --test",
                                                         "loop1": "npm run loop2", "loop2": "npm run loop3",
                                                         "loop3": "npm run loop4", "loop4": "node --test",
                                                         "mixed": "pytest && jest"}}))
    write(proj / "sub" / "package.json", json.dumps({"scripts": {"test": "vitest run"}}))

    def runner(cmd):
        return env.cli("test-count", "--check-runner", cmd, "--project-root", proj)

    assert runner("npm test")["runner"] == "node-test"
    assert runner("npm --prefix sub test")["runner"] == "vitest"
    assert runner("uv run --extra dev pytest -q")["runner"] == "pytest"
    assert runner("python -m pytest tests")["runner"] == "pytest"
    assert runner("npx jest --ci")["runner"] == "jest"
    assert runner("CI=1 cargo test")["runner"] == "cargo"
    assert runner("go test ./...")["runner"] == "go"
    assert runner("npm run loop1")["recognized"] is False  # more than three hops
    assert runner("npm run mixed")["recognized"] is False  # ambiguous
    assert runner("make test")["recognized"] is False
    logs = {
        "node-test": "TAP version 13\n# tests 3\n# suites 0\n# pass 3\n# fail 0\n",
        "pytest": "....\n4 passed, 1 skipped in 0.12s\n",
        "jest": "Tests:       1 failed, 5 passed, 6 total\n",
        "vitest": " Test Files  1 passed (1)\n      Tests  4 passed (4)\n",
        "cargo": "test result: ok. 3 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out\n",
        "go": "--- PASS: TestA (0.00s)\n--- PASS: TestB (0.00s)\nok  \tx\t0.1s\n",
    }
    expected = {"node-test": (3, 3), "pytest": (5, 4), "jest": (6, 5), "vitest": (4, 4), "cargo": (4, 3), "go": (2, 2)}
    for name, text in logs.items():
        log = write(tmp_path / f"{name}.log", text)
        res = env.cli("test-count", "--runner", name, "--log", log)
        assert (res["collected"], res["passed"]) == expected[name], (name, res)
    spec = write(tmp_path / "spec.log", "\u2714 adds (1ms)\n\u2139 tests 2\n\u2139 pass 2\n\u2139 fail 0\n")
    res = env.cli("test-count", "--command", "npm test", "--log", spec, "--project-root", proj)
    assert (res["runner"], res["collected"], res["passed"]) == ("node-test", 2, 2)
    garbage = write(tmp_path / "garbage.log", "everything is fine, trust me\n")
    res = env.cli("test-count", "--command", "npm test", "--log", garbage, "--project-root", proj)
    assert res["status"] == "unavailable" and res["reason"] == "count unreadable"
    zero = write(tmp_path / "zero.log", "no tests ran in 0.01s\n")
    assert env.cli("test-count", "--runner", "pytest", "--log", zero)["collected"] == 0


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_test_count_reads_a_real_node_test_log(env, tmp_path):
    proj = tmp_path / "proj"
    write(proj / "package.json", json.dumps({"scripts": {"test": "node --test"}}))
    write(proj / "a.test.mjs", "import test from 'node:test';\nimport assert from 'node:assert';\n"
                               "test('one', () => assert.equal(1, 1));\ntest('two', () => assert.equal(2, 2));\n")
    log = tmp_path / "gate-test.log"
    with open(log, "wb") as handle:
        rc = subprocess.run(["node", "--test"], cwd=str(proj), stdout=handle, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL).returncode
    assert rc == 0
    res = env.cli("test-count", "--command", "npm test", "--log", log, "--project-root", proj)
    assert res["status"] == "ok" and (res["collected"], res["passed"]) == (2, 2), res


# ------------------------------------------------------------------------------------------
# Ship gate
# ------------------------------------------------------------------------------------------

def test_ship_gate_states(env, tmp_path):
    lone = make_repo(tmp_path / "lone", BASE_FILES)
    branch, _ = env.prepare(env.owner(), lone, {"a.txt": "x\n"})
    res = env.cli("ship-gate", "--run", branch)
    assert res["status"] == "unavailable" and res["reason"] == "no remote"

    repo = make_repo(tmp_path / "repo", BASE_FILES, origin=True)
    branch, _ = env.prepare(env.owner(), repo, {"a.txt": "dev a\n"})
    assert env.cli("ship-gate", "--run", branch)["advanced"] is False
    other = tmp_path / "other"
    git(tmp_path, "clone", "-q", (tmp_path / "repo-origin.git").as_uri(), other.name)
    git(other, "config", "user.name", "o")
    git(other, "config", "user.email", "o@o")
    write(other / "b.txt", "upstream b\n")
    git(other, "commit", "-qam", "upstream b")
    git(other, "push", "-q", "origin", "main")
    res = env.cli("ship-gate", "--run", branch)
    assert res["status"] == "ok" and res["advanced"] is True and res["overlap"] == []
    write(other / "a.txt", "upstream a\n")
    git(other, "commit", "-qam", "upstream a")
    git(other, "push", "-q", "origin", "main")
    res = env.cli("ship-gate", "--run", branch)
    assert res["status"] == "halt" and res["reason"] == "SHIP_GATE_HALT" and res["overlap"] == ["a.txt"]
    assert res["sentinel"].startswith("SHIP_GATE_HALT: ")


# ------------------------------------------------------------------------------------------
# App supervisor
# ------------------------------------------------------------------------------------------

def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _bound(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def test_app_start_and_stop_own_the_whole_process_tree(env, tmp_path):
    repo = make_repo(tmp_path / "repo", BASE_FILES)
    write(repo / "index.html", "<p>hi</p>\n")
    branch, _ = env.prepare(env.owner(), repo, {"a.txt": "x\n"})
    port = _free_port()
    cmd = f'"{sys.executable}" -m http.server {port} --bind 127.0.0.1'
    url = f"http://127.0.0.1:{port}/"
    res = env.call(env.ctx(None, ready_timeout_seconds=30, url_timeout_seconds=30), "app-start", "--run", branch,
                   "--start-cmd", cmd, "--url", url, "--ready-url", url)
    try:
        assert res["status"] == "ok", res
        assert _bound(port)
        sup = res["supervisor"]
        assert bst.process_alive(sup["supervisor_pid"], sup["supervisor_start"])
        busy = env.call(env.ctx(None), "app-start", "--run", branch, "--start-cmd", cmd, "--url", url)
        assert busy["status"] == "halt" and busy["reason"] == "app already started"
    finally:
        stop = env.cli("app-stop", "--run", branch)
    assert stop["status"] == "ok" and stop["stopped"] is True
    assert not _bound(port)
    assert not bst.process_alive(sup["supervisor_pid"], sup["supervisor_start"])
    assert env.state(branch)["supervisor"] is None
    # an app that exits during startup is reported as such, with its log
    crash = env.call(env.ctx(None, ready_timeout_seconds=20), "app-start", "--run", branch, "--start-cmd",
                     f'"{sys.executable}" -c "import sys; print(\'boom\'); sys.exit(3)"', "--ready-url", url)
    assert crash["status"] == "halt" and crash["reason"] == "app exited during startup" and crash["exit_code"] == 3
    assert "boom" in Path(crash["log"]).read_text(encoding="utf-8", errors="replace")
    assert env.cli("app-stop", "--run", branch)["status"] == "ok"
