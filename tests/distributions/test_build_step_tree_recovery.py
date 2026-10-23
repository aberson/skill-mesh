"""build_step_tree.py run state machine: concurrency, liveness and recovery (T1-T20).

Implements design-notes section 9 (S1-S12) and section 10 rows C1 and D1-D4 as executable tests
against real disposable repositories.  Two runs are two real long-lived owner processes; a dead
run is a killed owner process (or a finalized run); a helper crash is a library-injected fault.
Every assertion reads real state: bytes on disk, `git stash list`, lock files in the Git common
directory and the run-state JSON.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pytest

from build_step_tree_fixtures import bst, env, git, make_repo, tree_bytes, write  # noqa: F401

FILES = {"a.txt": "alpha\n", "b.txt": "bravo\n", "c.txt": "charlie\n", "frontend/x.js": "x\n"}


def tree_lock(env, repo) -> dict:
    locks = {k: v for k, v in env.lock_files(repo).items() if k.startswith("skill-mesh-tree-")}
    assert len(locks) == 1, locks
    return next(iter(locks.values()))


def lock_name(env, repo) -> str:
    (name,) = [k for k in env.lock_files(repo) if k.startswith("skill-mesh-tree-")]
    return name


def stash_oids(repo) -> list:
    out = git(repo, "stash", "list", "--format=%H")
    return out.splitlines() if out else []


def test_s1_same_prefix_runs_serialize_on_the_tree_lock(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    a, _ = env.prepare(env.owner(), repo, {"a.txt": "A\n"})
    b, _ = env.prepare(env.owner(), repo, {"b.txt": "B\n"})
    assert env.cli("preview-apply", "--run", a)["status"] == "ok"
    proc = env.cli_async("land", "--run", b)
    time.sleep(2.0)
    assert proc.poll() is None, "B must wait on the tree lock while A's preview is active"
    assert tree_lock(env, repo)["branch"] == a
    assert env.state(b)["snapshots"] == []
    assert env.cli("preview-rollback", "--run", a)["status"] == "ok"
    res = env.finish(proc)
    assert res["status"] == "ok", res
    assert [s["lifecycle"] for s in env.state(a)["snapshots"]] == ["rolled-back"]
    assert [s["lifecycle"] for s in env.state(b)["snapshots"]] == ["active"]
    assert env.cli("verify-landed", "--run", b)["status"] == "ok"
    assert env.cli("land", "--run", a)["status"] == "ok"
    assert env.cli("verify-landed", "--run", a)["status"] == "ok"
    assert (repo / "a.txt").read_text() == "A\n" and (repo / "b.txt").read_text() == "B\n"
    for run in (a, b):
        assert env.cli("recover", "--check", "--run", run)["tree"] == "clean"


def test_s2_nested_prefixes_share_one_tree_lock(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    a, _ = env.prepare(env.owner(), repo, {"a.txt": "A root\n", "frontend/x.js": "A x\n"})
    b, _ = env.prepare(env.owner(), repo / "frontend", {"x.js": "B x\n"})
    assert env.state(a)["project_prefix"] == "." and env.state(b)["project_prefix"] == "frontend/"
    assert env.cli("preview-apply", "--run", b)["status"] == "ok"
    assert (repo / "frontend" / "x.js").read_text() == "B x\n"
    proc = env.cli_async("land", "--run", a)
    time.sleep(2.0)
    assert proc.poll() is None
    assert tree_lock(env, repo)["branch"] == b
    rb = env.cli("preview-rollback", "--run", b)
    assert rb["status"] == "ok"  # B's rollback finds no leftover
    res = env.finish(proc)
    assert res["status"] == "ok", res
    (landing,) = env.state(a)["snapshots"]
    prior = {e["path"]: e["prior"]["sha256"] for e in landing["entries"]}
    assert prior["frontend/x.js"] == hashlib.sha256(b"x\n").hexdigest()  # never B's preview bytes
    assert (repo / "frontend" / "x.js").read_text() == "A x\n"
    assert env.cli("verify-landed", "--run", a)["status"] == "ok"


def test_s3_crash_between_stash_push_and_state_write(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "operator wip\n")
    owner = env.owner()
    branch = env.start(owner, repo)
    with pytest.raises(bst.InjectedCrash):
        env.call(env.ctx(owner, faults=frozenset({"after-stash-push"})), "stash-save", "--run", branch)
    assert env.state(branch)["stash"]["state"] == "pending"
    assert git(repo, "stash", "list", "--format=%gs") == f"On main: build-step {branch}"
    assert {v["branch"] for v in env.lock_files(repo).values()} == {branch}  # crash left both locks
    res = env.cli("stash-restore", "--run", branch)  # the finalizer's call, same run token
    assert res["status"] == "ok" and res["restored"] is True
    assert stash_oids(repo) == [] and (repo / "wip.txt").read_text() == "operator wip\n"
    assert env.lock_files(repo) == {}
    assert env.cli("finalize", "helper failure", "--run", branch)["tree"] == "clean"
    # host died instead: recover resolves the pending stash the same way
    write(repo / "wip2.txt", "more wip\n")
    owner2 = env.owner()
    b2 = env.start(owner2, repo)
    with pytest.raises(bst.InjectedCrash):
        env.call(env.ctx(owner2, faults=frozenset({"after-stash-push"})), "stash-save", "--run", b2)
    owner2.kill()
    rec = env.cli("recover", b2)
    assert rec["status"] == "ok" and rec["result"] == "recovered"
    assert (repo / "wip2.txt").exists() and stash_oids(repo) == [] and env.lock_files(repo) == {}


def test_s4_dead_run_with_active_preview_blocks_a_new_run(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    dead_owner = env.owner()
    d, _ = env.prepare(dead_owner, repo, {"a.txt": "D\n"})
    assert env.cli("preview-apply", "--run", d)["status"] == "ok"
    dead_owner.kill()
    c = env.start(env.owner(), repo)
    res = env.cli("recover", "--check", "--run", c)
    assert res["status"] == "halt" and res["reason"] == "unfinished prior run"
    (unfinished,) = res["unfinished"]
    assert unfinished["branch"] == d and unfinished["alive"] is False
    assert unfinished["active_snapshots"][0]["paths"] == ["a.txt"]
    assert any(f"recover {d}" in r for r in res["remedy"])
    assert tree_lock(env, repo)["branch"] == d  # C took nothing
    assert env.state(c)["stash"]["state"] == "none"
    fin = env.cli("finalize", "unfinished prior run", "--run", c)
    assert fin["tree"] == "leftover" and fin["tree_paths"] == ["a.txt"]


def test_s6_finalizer_meets_a_busy_lock_and_keeps_its_outcome(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "operator wip\n")
    owner_a = env.owner()
    a, _ = env.prepare(owner_a, repo, {"a.txt": "A\n"}, stash=True)
    b, _ = env.prepare(env.owner(), repo, {"b.txt": "B\n"})
    assert env.cli("preview-apply", "--run", b)["status"] == "ok"
    res = env.call(env.ctx(owner_a, lock_wait_seconds=1.0), "stash-restore", "--run", a)
    assert res["status"] == "halt" and res["reason"] == "lock busy"
    assert res["owner_record"]["branch"] == b and res["owner_alive"] is True and res["remedy"] == []
    assert env.state(a)["stash"]["state"] == "saved" and len(stash_oids(repo)) == 1
    fin = env.cli("finalize", "reviewer record invalid", "--run", a)
    assert fin["finalized"] == "reviewer record invalid" and fin["tree"] == "leftover"
    assert {v["branch"] for v in env.lock_files(repo).values()} == {b}  # A holds nothing
    assert env.cli("preview-rollback", "--run", b)["status"] == "ok"
    rec = env.cli("recover", a)
    assert rec["status"] == "ok" and (repo / "wip.txt").read_text() == "operator wip\n"


def test_s7_concurrent_run_active_beside_an_active_snapshot(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    owner_b = env.owner()
    b, _ = env.prepare(owner_b, repo / "frontend", {"x.js": "B\n"})
    assert env.cli("preview-apply", "--run", b)["status"] == "ok"
    a = env.start(env.owner(), repo)
    res = env.cli("recover", "--check", "--run", a)
    assert res["status"] == "halt" and res["reason"] == "concurrent run active"
    assert [r["branch"] for r in res["concurrent"]] == [b] and res["remedy"] == []
    same = env.start(owner_b, repo)  # a run of B's own process
    res2 = env.cli("recover", "--check", "--run", same)
    assert res2["status"] == "halt" and any(f"recover {b} --abandon --by {same}" in r for r in res2["remedy"])
    fin = env.cli("finalize", "concurrent run active", "--run", a)
    assert fin["tree"] == "leftover" and env.lock_files(repo) and tree_lock(env, repo)["branch"] == b
    assert env.state(b)["snapshots"][0]["lifecycle"] == "active"


def test_s8_disrupted_same_session_run_then_abandon(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "operator wip\n")
    session, outsider = env.owner(), env.owner()
    r1 = env.start(session, repo)
    assert env.cli("stash-save", "--run", r1)["stashed"] is True
    time.sleep(0.05)
    r2 = env.start(session, repo)
    chk = env.cli("recover", "--check", "--run", r2)
    assert chk["status"] == "halt" and chk["reason"] == "concurrent run active"
    assert any(f"recover {r1} --abandon --by {r2}" in r for r in chk["remedy"])
    assert env.cli("finalize", "concurrent run active", "--run", r2)["tree"] == "clean"
    plain = env.cli("recover", r1)
    assert plain["status"] == "halt" and plain["reason"] == "owner alive"  # T14
    early = env.call(env.ctx(session), "recover", r1, "--abandon", "--by", r2)
    assert early["status"] == "halt" and early["reason"] == "abandon refused"
    assert "15 minutes" in early["detail"] and env.state(r1)["finalized"] is None
    foreign = env.call(env.ctx(outsider, clock_offset=16 * 60), "recover", r1, "--abandon", "--by", r2)
    assert foreign["status"] == "halt" and foreign["reason"] == "abandon refused"
    assert env.state(r1)["finalized"] is None and len(stash_oids(repo)) == 1
    late = env.call(env.ctx(session, clock_offset=16 * 60), "recover", r1, "--abandon", "--by", r2)
    assert late["status"] == "ok" and late["result"] == "recovered"
    assert "abandoned" in late["notes"] and "stash restored" in late["notes"]
    assert stash_oids(repo) == [] and (repo / "wip.txt").read_text() == "operator wip\n"
    assert env.lock_files(repo) == {} and env.state(r1)["finalized"] == "recovered"
    stale = env.cli("stash-restore", "--run", r1)
    assert stale["status"] == "halt" and stale["reason"] == "run finalized"  # T12


def test_s9_s11_recover_halts_on_leftover_then_keep_current(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "operator wip\n")
    owner = env.owner()
    d, _ = env.prepare(owner, repo, {"a.txt": "D a\n", "b.txt": "D b\n"}, stash=True)
    assert env.cli("land", "--run", d)["status"] == "ok"
    owner.kill()
    write(repo / "a.txt", "operator after crash\n")
    first = env.cli("recover", d)
    assert first["status"] == "halt" and first["reason"] == "recover halted"
    (left,) = first["leftovers"]
    assert left["path"] == "a.txt"
    assert Path(left["saved"]["prior"]).read_bytes() == b"alpha\n"
    assert Path(left["saved"]["written"]).read_bytes() == b"D a\n"
    assert (repo / "b.txt").read_text() == "bravo\n" and (repo / "a.txt").read_text() == "operator after crash\n"
    assert len(stash_oids(repo)) == 1 and not (repo / "wip.txt").exists()  # no stash restore yet
    locks = env.lock_files(repo)
    assert list(locks) == [lock_name(env, repo)] and tree_lock(env, repo)["branch"] == d  # stash lock free
    assert any("--keep-current a.txt" in r for r in first["remedy"])
    # S11: unlock is refused while the tree lock guards an active snapshot
    un = env.cli("unlock", lock_name(env, repo), "--project-root", repo)
    assert un["status"] == "halt" and un["reason"] == "unlock refused" and any(f"recover {d}" in r for r in un["remedy"])
    bad = env.cli("recover", d, "--keep-current", "b.txt")
    assert bad["status"] == "halt" and bad["reason"] == "not a listed leftover"
    second = env.cli("recover", d, "--keep-current", "a.txt")
    assert second["status"] == "ok" and second["result"] == "recovered"
    assert (repo / "a.txt").read_text() == "operator after crash\n"
    assert (repo / "wip.txt").read_text() == "operator wip\n" and stash_oids(repo) == []
    assert env.lock_files(repo) == {}
    assert [s["lifecycle"] for s in env.state(d)["snapshots"]] == ["rolled-back"]


def test_s10_dead_owner_recover_adopts_its_locks(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "operator wip\n")
    owner = env.owner()
    d, _ = env.prepare(owner, repo, {"a.txt": "D a\n", "new.txt": "D new\n"}, stash=True)
    assert env.cli("land", "--run", d)["status"] == "ok"
    assert tree_lock(env, repo)["branch"] == d
    owner.kill()
    started = time.monotonic()
    rec = env.cli("recover", d)
    assert rec["status"] == "ok" and rec["result"] == "recovered"
    assert time.monotonic() - started < 60  # no 10-minute lock wait
    assert (repo / "a.txt").read_text() == "alpha\n" and not (repo / "new.txt").exists()
    assert (repo / "wip.txt").read_text() == "operator wip\n" and stash_oids(repo) == []
    assert env.lock_files(repo) == {}
    assert env.state(d)["finalized"] == "recovered"


def test_s12_pass_beside_another_runs_active_preview(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    a, _ = env.prepare(env.owner(), repo, {"a.txt": "A\n", "p.txt": "A p\n"})
    b, _ = env.prepare(env.owner(), repo, {"b.txt": "B\n"})
    assert env.cli("land", "--run", a)["status"] == "ok"
    assert env.cli("verify-landed", "--run", a)["status"] == "ok"
    assert env.cli("preview-apply", "--run", b)["status"] == "ok"  # B's preview after A's release
    arc = env.cli("archive", "--run", a)
    assert env.cli("cleanup", "--run", a)["status"] == "ok"
    chk = env.cli("recover", "--check", "--project-root", repo)
    assert chk["status"] == "ok" and chk["tree"] == "leftover" and chk["tree_paths"] == ["b.txt"]
    doc = json.loads(Path(arc["landed_paths"]).read_text(encoding="utf-8"))
    listed = {p["path"]: p["state"] for p in doc["paths"]}
    assert sorted(listed) == ["a.txt", "p.txt"]  # exactly A's landed paths, none of B's
    for rel, blob in listed.items():
        assert git(repo, "hash-object", "--", rel) == blob
    assert env.cli("preview-rollback", "--run", b)["status"] == "ok"


def test_b2_overlapping_preview_changes_a_listed_blob_until_rolled_back(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    a, _ = env.prepare(env.owner(), repo, {"c.txt": "A c\n"})
    b, _ = env.prepare(env.owner(), repo, {"c.txt": "B c\n"})
    assert env.cli("land", "--run", a)["status"] == "ok"
    assert env.cli("verify-landed", "--run", a)["status"] == "ok"
    listed = json.loads(Path(env.cli("archive", "--run", a)["landed_paths"]).read_text())["paths"][0]["state"]
    assert env.cli("preview-apply", "--run", b)["status"] == "ok"
    assert git(repo, "hash-object", "--", "c.txt") != listed  # P3 would leave c.txt out (LANDED-CHANGED)
    assert env.cli("preview-rollback", "--run", b)["status"] == "ok"  # no leftover
    assert (repo / "c.txt").read_text() == "A c\n" and git(repo, "hash-object", "--", "c.txt") == listed


def test_c1_write_during_the_lock_wait_is_caught_under_the_lock(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    owner_a = env.owner()
    a, wta = env.prepare(owner_a, repo, {"a.txt": "A reviewed\n"})
    b, _ = env.prepare(env.owner(), repo, {"b.txt": "B\n"})
    assert env.cli("preview-apply", "--run", b)["status"] == "ok"
    waits = []

    def during_wait(kind, attempt):
        waits.append((kind, attempt))
        if attempt == 1:
            write(wta / "a.txt", "stray write during the wait\n")
            assert env.cli("preview-rollback", "--run", b)["status"] == "ok"

    res = env.call(env.ctx(owner_a, on_lock_wait=during_wait), "land", "--run", a)
    assert waits and waits[0] == ("tree", 1)
    assert res["status"] == "halt" and res["reason"] == "payload changed after review"
    assert res["stage"] == "under-lock" and res["lock_released"] is True
    assert env.lock_files(repo) == {} and env.state(a)["snapshots"] == []
    assert (repo / "a.txt").read_text() == "alpha\n"
    assert env.cli("finalize", "payload changed after review", "--run", a)["tree"] == "clean"


def test_d1_to_d4_failed_stash_restore_and_operator_resolution(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "a.txt", "operator a\n")
    owner = env.owner()
    a, _ = env.prepare(owner, repo, {"b.txt": "dev b\n"}, stash=True)
    oid = env.state(a)["stash"]["oid"]
    assert env.cli("land", "--run", a)["status"] == "ok"
    assert env.cli("verify-landed", "--run", a)["status"] == "ok"
    write(repo / "a.txt", "operator edited a stashed path during the run\n")
    # D1
    d1 = env.cli("stash-restore", "--run", a)
    assert d1["status"] == "halt" and d1["reason"] == "restore failed"
    assert d1["oid"] == oid and d1["entry"] == "stash@{0}"
    assert any("--stash-resolved" in r for r in d1["remedy"]) and any(r.endswith(f"recover {a}") for r in d1["remedy"])
    assert stash_oids(repo) == [oid] and (repo / "b.txt").read_text() == "dev b\n"  # entry and landing kept
    assert env.lock_files(repo) == {} and env.state(a)["stash"]["state"] == "saved"
    fin = env.cli("finalize", "restore failed", "--run", a)
    assert fin["tree"] == "leftover"
    # D2
    d2 = env.cli("recover", a)
    assert d2["status"] == "halt" and d2["reason"] == "recover halted: stash restore failed" and d2["oid"] == oid
    assert stash_oids(repo) == [oid] and env.state(a)["stash"]["state"] == "saved"
    assert env.state(a)["finalized"] == "restore failed" and env.lock_files(repo) == {}
    assert (repo / "a.txt").read_text() == "operator edited a stashed path during the run\n"
    # D3
    before = env.state(a)
    d3 = env.cli("recover", a, "--stash-resolved")
    assert d3["status"] == "halt" and d3["reason"] == "stash entry remains" and d3["entry"] == "stash@{0}"
    assert env.state(a)["stash"] == before["stash"] and env.state(a)["finalized"] == before["finalized"]
    # D4: the operator settles it by hand
    git(repo, "checkout", "--", "a.txt")
    git(repo, "stash", "pop")
    assert stash_oids(repo) == []
    d4 = env.cli("recover", a, "--stash-resolved")
    assert d4["status"] == "ok" and d4["result"] == "recovered" and "stash resolved by operator" in d4["notes"]
    assert env.state(a)["stash"]["state"] == "restored" and env.state(a)["finalized"] == "recovered"
    c = env.start(env.owner(), repo)
    assert env.cli("recover", "--check", "--run", c)["status"] == "ok"  # no longer T3
    nothing = env.cli("recover", a, "--stash-resolved")
    assert nothing["status"] == "halt" and nothing["reason"] == "no saved stash"


def test_finalized_run_stays_final_against_an_in_flight_land(env, tmp_path):
    """RF-5 (exp-overlap-unfinalize through the CLI): A's `land` is blocked on B's preview tree
    lock (a host tool timeout leaves it running); the orchestrator rolls back and finalizes A.
    The late land must not land, un-finalize A, or leave a snapshot or lock behind."""
    repo = make_repo(tmp_path / "repo", FILES)
    a, _ = env.prepare(env.owner(), repo, {"a.txt": "A payload\n"})
    b, _ = env.prepare(env.owner(), repo, {"b.txt": "B preview\n"})
    assert env.cli("preview-apply", "--run", b)["status"] == "ok"
    late = env.cli_async("land", "--run", a)
    time.sleep(3.0)
    assert late.poll() is None, "A's land must be waiting on B's tree lock"
    rb = env.cli("land-rollback", "--run", a)
    assert rb["status"] == "ok" and rb.get("noop") is True
    fin = env.cli("finalize", "helper failure", "--run", a)
    assert fin["status"] == "ok" and fin["finalized"] == "helper failure"
    assert env.cli("preview-rollback", "--run", b)["status"] == "ok"  # B releases the tree lock
    res = env.finish(late)
    assert res["status"] != "ok", res
    assert res["reason"] == "run finalized"
    assert res["stage"] == "after lock wait", res  # R2-1 (TQ-A-4): refused at rejoin, not at entry
    assert (repo / "a.txt").read_text() == "alpha\n"
    st = env.state(a)
    assert st["finalized"] == "helper failure"
    assert [s["id"] for s in st["snapshots"] if s["lifecycle"] == "active"] == []
    assert env.lock_files(repo) == {}
    th = env.cli("tree-hash", "--run", a)
    assert th["status"] == "halt" and th["reason"] == "run finalized"


def _operator_entries_around_the_run(env, repo, owner) -> tuple:
    """Operator stash entry E1 before stash-save, E2 after it: the run's entry is stash@{1}."""
    write(repo / "c.txt", "operator change for E1\n")
    git(repo, "stash", "push", "-q", "-m", "operator E1")
    (e1,) = stash_oids(repo)
    write(repo / "wip.txt", "operator wip\n")
    run = env.start(owner, repo)
    assert env.cli("stash-save", "--run", run)["stashed"] is True
    mine = env.state(run)["stash"]["oid"]
    write(repo / "b.txt", "operator change for E2\n")
    git(repo, "stash", "push", "-q", "-m", "operator E2")
    e2 = stash_oids(repo)[0]
    assert stash_oids(repo) == [e2, mine, e1]
    return run, e1, e2


def test_t10_drop_removes_only_the_runs_entry(env, tmp_path):
    """RF-6: operator stash entries pushed before (E1) and after (E2) stash-save survive, in order,
    through stash-restore."""
    repo = make_repo(tmp_path / "repo", FILES)
    run, e1, e2 = _operator_entries_around_the_run(env, repo, env.owner())
    res = env.cli("stash-restore", "--run", run)
    assert res["status"] == "ok" and res["restored"] is True and "stale_entry" not in res, res
    assert stash_oids(repo) == [e2, e1]
    assert (repo / "wip.txt").read_text() == "operator wip\n"


def test_t10_drop_through_recover_removes_only_the_runs_entry(env, tmp_path):
    """RF-6: the same containment through `recover <b>` of a dead run (T13: T5 + T10)."""
    repo = make_repo(tmp_path / "repo", FILES)
    owner = env.owner()
    run, e1, e2 = _operator_entries_around_the_run(env, repo, owner)
    owner.kill()
    rec = env.cli("recover", run)
    assert rec["status"] == "ok" and rec["result"] == "recovered" and "stash restored" in rec["notes"], rec
    assert stash_oids(repo) == [e2, e1]
    assert (repo / "wip.txt").read_text() == "operator wip\n"


def test_recover_check_after_cleanup_never_scopes_the_ambient_cwd(env, tmp_path):
    """RF-8 (E9): after A's cleanup, `recover --check --run A` called from an unrelated repository
    resolves A's operator tree from its archive, so B's active preview still makes it leftover."""
    repo = make_repo(tmp_path / "repo", FILES)
    unrelated = make_repo(tmp_path / "unrelated", {"u.txt": "u\n"})
    a, _ = env.prepare(env.owner(), repo, {"a.txt": "A\n"})
    b, _ = env.prepare(env.owner(), repo, {"b.txt": "B\n"})
    assert env.cli("land", "--run", a)["status"] == "ok"
    assert env.cli("verify-landed", "--run", a)["status"] == "ok"
    assert env.cli("archive", "--run", a)["status"] == "ok"
    assert env.cli("cleanup", "--run", a)["status"] == "ok"
    assert env.cli("preview-apply", "--run", b)["status"] == "ok"
    chk = env.cli("recover", "--check", "--run", a, cwd=unrelated)
    assert chk["status"] == "ok", chk
    assert chk["tree"] == "leftover" and chk["scope_source"] == "archive"
    assert f"run {b} has an active snapshot" in chk["tree_reasons"] and chk["tree_paths"] == ["b.txt"]
    assert chk["git_root"] == git(repo, "rev-parse", "--show-toplevel")
    gone = env.cli("recover", "--check", "--run", "build-step-20200101T000000Z-0000abcd", cwd=unrelated)
    assert gone["status"] == "halt" and gone["reason"] == "no run state", gone
    explicit = env.cli("recover", "--check", "--run", a, "--project-root", unrelated, cwd=repo)
    assert explicit["status"] == "ok" and explicit["scope_source"] == "project root"
    assert explicit["tree"] == "clean" and explicit["git_root"] == git(unrelated, "rev-parse", "--show-toplevel")
    assert env.cli("preview-rollback", "--run", b)["status"] == "ok"


def test_t18_unlock_rules(env, tmp_path):
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "wip\n")
    owner = env.owner()
    d = env.start(owner, repo)
    with pytest.raises(bst.InjectedCrash):
        env.call(env.ctx(owner, faults=frozenset({"after-stash-push"})), "stash-save", "--run", d)
    names = sorted(env.lock_files(repo))
    assert names[0] == "skill-mesh-stash.lock" and names[1].startswith("skill-mesh-tree-")
    alive = env.cli("unlock", "skill-mesh-stash.lock", "--project-root", repo)
    assert alive["status"] == "halt" and alive["reason"] == "unlock refused"  # live owner
    owner.kill()
    for name in names:  # dead owner, no active snapshot
        res = env.cli("unlock", name, "--project-root", repo)
        assert res["status"] == "ok" and res["cleared"] is True
    assert env.lock_files(repo) == {}
    # a lock whose run state is missing is judged by its recorded (dead) process
    common = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    ghost = {"kind": "stash", "branch": "build-step-20200101T000000Z-00000000", "token": "0" * 32,
             "owner": owner.record, "acquired_epoch": time.time()}
    (common / "skill-mesh-stash.lock").write_text(json.dumps(ghost), encoding="utf-8")
    res = env.cli("unlock", "skill-mesh-stash.lock", "--project-root", repo)
    assert res["status"] == "ok" and res["cleared"] is True
    rec = env.cli("recover", d)  # T5 then T10 on the crashed run
    assert rec["status"] == "ok" and (repo / "wip.txt").exists() and stash_oids(repo) == []


# ------------------------------------------------------------------------------------------
# Correction cycle 2: the RF-5(b) call lock (R2-1), recover's tree lock on a zombie landing
# (R2-2), and stash push/apply only under the tree lock (R2-3)
# ------------------------------------------------------------------------------------------

def _work_bytes(repo: Path) -> dict:
    """Every regular file of the operator tree outside .git (relative posix path -> bytes)."""
    return {k: v for k, v in tree_bytes(repo).items() if not k.startswith(".git/")}


def test_run_call_lock_serializes_the_calls_of_one_run(env, tmp_path):
    """R2-1 (RF-5(b), TQ-M-1): while another call of run A holds A's call lock (here this test
    process, through the helper's own library function), a CLI `finalize` of A waits and writes
    nothing, then finishes once the lock is released.  An in-process call bounded to 1 s gives up
    with `run call in progress`, the state unchanged."""
    repo = make_repo(tmp_path / "repo", FILES)
    owner = env.owner()
    a = env.start(owner, repo)
    state_file = env.root / "build-step-runs" / a / "state.json"
    holder = env.ctx(owner)
    bst.hold_call_lock(holder, a)  # stands in for an in-flight call of A in a non-waiting phase
    try:
        before = state_file.read_bytes()
        late = env.cli_async("finalize", "helper failure", "--run", a)
        time.sleep(2.5)
        assert late.poll() is None, "finalize must wait while another call of A holds A's call lock"
        assert state_file.read_bytes() == before, "nothing may be written while the call lock is held elsewhere"
        marked = env.state(a)
        marked["serialization_marker"] = "written by holder"
        bst.save_state(holder, marked)
        after_marker = state_file.read_bytes()
        busy = env.call(env.ctx(owner, call_lock_wait_seconds=1.0), "finalize", "helper failure", "--run", a)
        assert busy["status"] == "halt" and busy["reason"] == "run call in progress", busy
        assert state_file.read_bytes() == after_marker
        assert late.poll() is None
    finally:
        bst.release_call_lock(holder, a)
    res = env.finish(late)
    assert res["status"] == "ok" and res["finalized"] == "helper failure", res
    assert env.state(a)["finalized"] == "helper failure"
    assert env.state(a)["serialization_marker"] == "written by holder"


def test_save_state_refuses_a_write_without_the_run_call_lock(env, tmp_path):
    """R2-1 (RF-5): every run-state write happens under the run call lock.  A Context that does not
    hold A's call lock cannot write A's state; the same write under the lock lands (control)."""
    repo = make_repo(tmp_path / "repo", FILES)
    owner = env.owner()
    a = env.start(owner, repo)
    state_file = env.root / "build-step-runs" / a / "state.json"
    before = state_file.read_bytes()
    st = env.state(a)
    st["finalized"] = "probe"
    ctx = env.ctx(owner)
    with pytest.raises(RuntimeError, match="without the run call lock"):
        bst.save_state(ctx, st)
    assert state_file.read_bytes() == before
    bst.hold_call_lock(ctx, a)
    try:
        bst.save_state(ctx, st)
    finally:
        bst.release_call_lock(ctx, a)
    assert env.state(a)["finalized"] == "probe"


def test_recover_halt_keeps_the_tree_lock_of_a_zombie_landing(env, tmp_path):
    """R2-2 (SF-M1 = GS-A4; spec-fidelity x3): A's `land` waits on C's tree lock when A's host dies;
    the helper call lives on (a zombie).  `recover A` waits on the same lock; C releases it and the
    zombie lands first.  Recover must halt with the remedy `recover A` and keep A's tree lock while
    A's landing is active; a second `recover A` then rolls the landing back and restores the stash.
    The ordering is made deterministic with the library lock-wait callback."""
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "operator wip\n")
    owner_a = env.owner()
    a, _ = env.prepare(owner_a, repo, {"a.txt": "A payload\n"}, stash=True)
    c, _ = env.prepare(env.owner(), repo, {"c.txt": "C preview\n"})
    assert env.cli("preview-apply", "--run", c)["status"] == "ok"
    zombie = env.cli_async("land", "--run", a)
    time.sleep(3.0)
    assert zombie.poll() is None, "A's land must be waiting on C's tree lock"
    owner_a.kill()  # A's host dies; its helper call lives on
    token = env.state(a)["token"]
    tree_name = bst.tree_lock_name(env.state(a)["git_root"])
    seen = {}

    def during_wait(kind, attempt):
        if attempt == 1:
            seen["kind"] = kind
            assert env.cli("preview-rollback", "--run", c)["status"] == "ok"  # C frees the tree lock
            seen["zombie"] = env.finish(zombie)  # the zombie takes it and lands while recover waits

    res = env.call(env.ctx(None, on_lock_wait=during_wait), "recover", a)
    assert seen["kind"] == "tree"
    assert seen["zombie"]["status"] == "ok" and seen["zombie"]["snapshot"] == "landing-1", seen
    assert res["status"] == "halt" and res["reason"] == "recover halted", res
    assert "active snapshot" in res["detail"] and res["snapshots"] == ["landing-1"]
    assert any(r.endswith(f"recover {a}") for r in res["remedy"]), res["remedy"]
    assert res["holds_tree_lock"] is True
    st = env.state(a)
    assert st["finalized"] is None and st["stash"]["state"] == "saved"
    assert [s["id"] for s in st["snapshots"] if s["lifecycle"] == "active"] == ["landing-1"]
    locks = env.lock_files(repo)
    assert list(locks) == [tree_name], locks  # the tree lock guards A's active landing
    assert locks[tree_name]["branch"] == a and locks[tree_name]["token"] == token
    assert (repo / "a.txt").read_text() == "A payload\n" and not (repo / "wip.txt").exists()
    again = env.cli("recover", a)
    assert again["status"] == "ok" and again["result"] == "recovered" and "stash restored" in again["notes"], again
    assert (repo / "a.txt").read_text() == "alpha\n" and (repo / "wip.txt").read_text() == "operator wip\n"
    assert env.lock_files(repo) == {} and stash_oids(repo) == []
    st = env.state(a)
    assert st["finalized"] == "recovered" and [s["lifecycle"] for s in st["snapshots"]] == ["rolled-back"]


def _alive_run_holding_the_stash_lock(env, repo) -> dict:
    """An alive run (real owner process) holds the stash lock, taken with the helper's own code."""
    holder_owner = env.owner()
    holder = env.start(holder_owner, repo)
    hst = env.state(holder)
    bst.acquire_lock(env.ctx(holder_owner), hst, "stash")
    return hst


def test_stash_save_refuses_an_active_preview_without_writing(env, tmp_path):
    """RX-1 sequential x5/e6d: T4 refuses an active preview before taking either lock or
    changing refs/stash, then rollback and finalize restore the exact pre-run operator tree."""
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "operator wip\n")
    pre = _work_bytes(repo)
    a, _ = env.prepare(env.owner(), repo, {"a.txt": "A unreviewed preview\n"})
    assert env.cli("preview-apply", "--run", a)["status"] == "ok"
    ref_before = git(repo, "rev-parse", "-q", "--verify", "refs/stash", check=False)
    res = env.cli("stash-save", "--run", a)
    assert res["status"] == "halt" and res["reason"] == "stash failed", res
    assert res["detail"] == "active snapshot" and res["snapshots"] == ["preview-1"]
    assert git(repo, "rev-parse", "-q", "--verify", "refs/stash", check=False) == ref_before == ""
    assert git(repo, "stash", "list") == "" and env.state(a)["stash"] == {"state": "none"}
    assert (repo / "a.txt").read_text() == "A unreviewed preview\n"
    assert [s["id"] for s in env.state(a)["snapshots"] if s["lifecycle"] == "active"] == ["preview-1"]
    assert env.cli("preview-rollback", "--run", a)["status"] == "ok"
    fin = env.cli("finalize", "helper failure", "--run", a)
    assert fin["status"] == "ok" and fin["tree"] == "clean", fin
    assert _work_bytes(repo) == pre and env.lock_files(repo) == {}


def test_stash_save_active_snapshot_entry_guard_precedes_any_lock(env, tmp_path, monkeypatch):
    """RX-1 entry-guard mutation anchor: an already-active snapshot refuses before lock code."""
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "operator wip\n")
    owner = env.owner()
    a, _ = env.prepare(owner, repo, {"a.txt": "A preview\n"})
    assert env.cli("preview-apply", "--run", a)["status"] == "ok"

    def forbidden(*_args, **_kwargs):
        raise AssertionError("stash-save reached lock acquisition with an active snapshot")

    monkeypatch.setattr(bst, "acquire_lock", forbidden)
    res = env.call(env.ctx(owner), "stash-save", "--run", a)
    assert res["status"] == "halt" and res["reason"] == "stash failed", res
    assert res["detail"] == "active snapshot"


def test_stash_save_rechecks_for_a_same_run_preview_after_the_stash_lock_wait(env, tmp_path):
    """RX-1 concurrent e6b/x4: while T4 waits on the stash lock, a sibling preview of the
    same run reuses its tree-lock token.  The post-wait State check refuses before capture/push."""
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "operator wip\n")
    hst = _alive_run_holding_the_stash_lock(env, repo)
    a, _ = env.prepare(env.owner(), repo, {"a.txt": "A unreviewed preview\n"})
    waiting = env.cli_async("stash-save", "--run", a)
    time.sleep(3.0)
    assert waiting.poll() is None, "stash-save must be waiting on the held stash lock"
    preview = env.cli("preview-apply", "--run", a)
    assert preview["status"] == "ok" and preview["snapshot"] == "preview-1", preview
    bst.release_lock(hst, "stash")
    res = env.finish(waiting)
    assert res["status"] == "halt" and res["reason"] == "stash failed", res
    assert res["detail"] == "active snapshot" and res["snapshots"] == ["preview-1"]
    assert git(repo, "stash", "list") == "" and env.state(a)["stash"] == {"state": "none"}
    assert (repo / "a.txt").read_text() == "A unreviewed preview\n"
    assert (repo / "wip.txt").read_text() == "operator wip\n"
    assert env.cli("preview-rollback", "--run", a)["status"] == "ok"


def test_stash_restore_checks_an_active_snapshot_before_the_benign_state_return(env, tmp_path):
    """RX-2 T10 audit: after its last lock wait, an active snapshot is a safety halt even if a
    sibling has also changed the stash to a state that would otherwise return benignly."""
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "operator wip\n")
    owner = env.owner()
    a, _ = env.prepare(owner, repo, {"a.txt": "A preview\n"}, stash=True)
    hst = _alive_run_holding_the_stash_lock(env, repo)
    seen = {}

    def during_wait(kind, attempt):
        if attempt == 1:
            seen["preview"] = env.cli("preview-apply", "--run", a)
            state_ctx = env.ctx(owner)
            bst.hold_call_lock(state_ctx, a)
            try:
                changed = env.state(a)
                changed["stash"] = {"state": "restored", "audit_probe": True}
                bst.save_state(state_ctx, changed)
            finally:
                bst.release_call_lock(state_ctx, a)
            bst.release_lock(hst, "stash")

    res = env.call(env.ctx(owner, on_lock_wait=during_wait), "stash-restore", "--run", a)
    assert seen["preview"]["status"] == "ok"
    assert res["status"] == "halt" and res["reason"] == "active snapshot", res
    assert res["snapshots"] == ["preview-1"]
    assert env.state(a)["stash"] == {"state": "restored", "audit_probe": True}
    assert env.cli("preview-rollback", "--run", a)["status"] == "ok"


def test_recover_keeps_the_tree_lock_if_an_active_snapshot_appears_before_final_release(env, tmp_path, monkeypatch):
    """RX-2 T13 audit: pin the final post-wait invariant independently of restore_stash's own
    guard.  A simulated late zombie persists an active snapshot under the real call/tree locks."""
    repo = make_repo(tmp_path / "repo", FILES)
    owner = env.owner()
    a = env.start(owner, repo)
    owner.kill()
    original = bst.restore_stash

    def late_snapshot(ctx, target, *, in_recover):
        frag = original(ctx, target, in_recover=in_recover)
        bst.acquire_lock(ctx, target, "tree", allow_finalized=True)
        target["snapshots"].append({"id": "preview-late", "kind": "preview", "lifecycle": "active", "entries": []})
        bst.save_state(ctx, target)
        return frag

    monkeypatch.setattr(bst, "restore_stash", late_snapshot)
    res = env.call(env.ctx(None), "recover", a)
    assert res["status"] == "halt" and res["reason"] == "recover halted", res
    assert res["snapshots"] == ["preview-late"] and res["holds_tree_lock"] is True
    assert env.state(a)["finalized"] is None
    tree_name = bst.tree_lock_name(env.state(a)["git_root"])
    assert list(env.lock_files(repo)) == [tree_name]


def test_stash_save_never_pushes_after_its_tree_lock_was_lost_in_a_wait(env, tmp_path):
    """R2-3 (GS-A1 = SF-A3; git-safety exp-r1 test D through the CLI): A's stash-save holds A's tree
    lock and waits on the stash lock; a sibling no-op `preview-rollback --run A` releases A's tree
    lock (lock files are per run token); run C previews a.txt.  When the stash lock frees, A must
    not stash C's unreviewed preview bytes as operator work, and `tree=clean` is never reported
    while C's bytes are in the operator tree."""
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "operator wip\n")
    pre = _work_bytes(repo)
    hst = _alive_run_holding_the_stash_lock(env, repo)
    a = env.start(env.owner(), repo)
    c, _ = env.prepare(env.owner(), repo, {"a.txt": "C unreviewed preview\n"})
    tree_name = bst.tree_lock_name(env.state(a)["git_root"])
    ref_before = git(repo, "rev-parse", "-q", "--verify", "refs/stash", check=False)
    waiting = env.cli_async("stash-save", "--run", a)
    time.sleep(3.0)
    assert waiting.poll() is None, "A's stash-save must be waiting on the stash lock"
    locks = {k: v["branch"] for k, v in env.lock_files(repo).items()}
    assert locks == {"skill-mesh-stash.lock": hst["branch"], tree_name: a}, locks  # tree lock taken first
    noop = env.cli("preview-rollback", "--run", a)
    assert noop["status"] == "ok" and noop.get("noop") is True
    assert tree_name not in env.lock_files(repo)  # the sibling call released A's tree lock
    assert env.cli("preview-apply", "--run", c)["status"] == "ok"
    assert (repo / "a.txt").read_text() == "C unreviewed preview\n"
    bst.release_lock(hst, "stash")
    res = env.finish(waiting)
    assert res["status"] == "halt" and res["reason"] == "lock busy", res
    assert res["lock_kind"] == "tree" and "tree lock lost during wait" in res["detail"]
    assert git(repo, "rev-parse", "-q", "--verify", "refs/stash", check=False) == ref_before == ""
    assert git(repo, "stash", "list") == ""
    assert env.state(a)["stash"] == {"state": "none"}
    assert (repo / "a.txt").read_text() == "C unreviewed preview\n" and (repo / "wip.txt").read_text() == "operator wip\n"
    assert {k: v["branch"] for k, v in env.lock_files(repo).items()} == {tree_name: c}  # C's lock untouched
    chk = env.cli("recover", "--check", "--run", a)
    assert chk["tree"] == "leftover" and f"run {c} has an active snapshot" in chk["tree_reasons"], chk
    assert env.cli("preview-rollback", "--run", c)["status"] == "ok"
    fin = env.cli("finalize", "concurrent run active", "--run", a)
    assert fin["status"] == "ok" and fin["tree"] == "clean", fin
    assert _work_bytes(repo) == pre and env.lock_files(repo) == {}


def test_stash_restore_never_applies_after_its_tree_lock_was_lost_in_a_wait(env, tmp_path):
    """R2-3 at the T10 site: A's stash-restore holds A's tree lock and waits on the stash lock; a
    sibling no-op rollback releases A's tree lock and run C previews.  When the stash lock frees,
    A must not apply its stash: the entry and the `saved` state are kept and nothing is written."""
    repo = make_repo(tmp_path / "repo", FILES)
    write(repo / "wip.txt", "operator wip\n")
    pre = _work_bytes(repo)
    a = env.start(env.owner(), repo)
    assert env.cli("stash-save", "--run", a)["stashed"] is True
    (oid,) = stash_oids(repo)
    hst = _alive_run_holding_the_stash_lock(env, repo)
    c, _ = env.prepare(env.owner(), repo, {"a.txt": "C unreviewed preview\n"})
    tree_name = bst.tree_lock_name(env.state(a)["git_root"])
    waiting = env.cli_async("stash-restore", "--run", a)
    time.sleep(3.0)
    assert waiting.poll() is None, "A's stash-restore must be waiting on the stash lock"
    locks = {k: v["branch"] for k, v in env.lock_files(repo).items()}
    assert locks == {"skill-mesh-stash.lock": hst["branch"], tree_name: a}, locks
    noop = env.cli("preview-rollback", "--run", a)
    assert noop["status"] == "ok" and noop.get("noop") is True
    assert env.cli("preview-apply", "--run", c)["status"] == "ok"
    bst.release_lock(hst, "stash")
    res = env.finish(waiting)
    assert res["status"] == "halt" and res["reason"] == "lock busy" and res["lock_kind"] == "tree", res
    assert stash_oids(repo) == [oid] and env.state(a)["stash"]["state"] == "saved"
    assert not (repo / "wip.txt").exists() and (repo / "a.txt").read_text() == "C unreviewed preview\n"
    assert {k: v["branch"] for k, v in env.lock_files(repo).items()} == {tree_name: c}
    assert env.cli("preview-rollback", "--run", c)["status"] == "ok"
    rest = env.cli("stash-restore", "--run", a)
    assert rest["status"] == "ok" and rest["restored"] is True, rest
    fin = env.cli("finalize", "concurrent run active", "--run", a)
    assert fin["status"] == "ok" and fin["tree"] == "clean", fin
    assert _work_bytes(repo) == pre and stash_oids(repo) == [] and env.lock_files(repo) == {}
