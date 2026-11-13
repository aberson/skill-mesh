"""Tests for user-afterparty's usage-telemetry scripts (scan_usage.py, aggregate.py).

v3 catalog cleanup Step 18 (#274). Both scripts run as the skill runs them (`python -I`,
every location an argument) over a small synthetic transcript store, and the snapshot's
columns and counts are asserted. The counts are graded by one helper, `_count_problems`,
and a garbage store (well-formed JSON with no real skill call in it) must red that helper.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCAN = HERE / "scan_usage.py"
AGG = HERE / "aggregate.py"
AS_OF = "2026-11-13T00:00:00Z"

COLUMNS = {
    "name", "status", "description", "core_lines", "last_commit", "commits_60d", "commits_all",
    "total", "w6", "w2", "top_w6", "top_w2", "top_all", "sub_w6", "sweep", "sessions_w6",
    "claude", "codex", "copilot", "claude_w6", "codex_w6", "operator", "model", "subagent",
    "sessions", "projects", "self_share", "first", "last",
}

# skill -> the counts the good store must produce.
EXPECTED = {
    "build-step": dict(total=2, top_all=1, subagent=1, model=1, claude=2, sweep=1, w6=2, w2=2),
    "plan-review": dict(total=3, top_all=3, operator=1, model=2, claude=1, codex=2, sweep=1, w6=2),
    "user-pm": dict(total=1, top_all=1, copilot=1, model=1, sweep=1),
    "unused": dict(total=0, top_all=0, sweep=0),
}


def _jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Compact separators, as the hosts write them (the scanners prefilter on raw bytes).
    path.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows),
                    encoding="utf-8")


def _claude_skill(skill, ts, uid, sidechain=False):
    return {"type": "assistant", "timestamp": ts, "sessionId": "c1", "cwd": "C:/u/dev/alpha",
            "isSidechain": sidechain,
            "message": {"content": [{"type": "tool_use", "name": "Skill", "id": uid,
                                     "input": {"skill": skill}}]}}


def _codex_call(call_id, ts, skills):
    paths = " ".join(f"C:\\\\u\\\\.agents\\\\skills\\\\{s}\\\\SKILL.md" for s in skills)
    return {"timestamp": ts, "type": "response_item",
            "payload": {"type": "function_call", "call_id": call_id,
                        "arguments": json.dumps({"command": f"Get-Content {paths}"})}}


def _store(home: Path, garbage: bool = False) -> None:
    name = "Read" if garbage else "Skill"
    proj = home / ".claude" / "projects" / "c--u-dev-alpha"
    main = [
        _claude_skill("build-step", "2026-11-10T10:00:00Z", "tu1"),
        {"type": "user", "timestamp": "2026-10-01T10:00:00Z", "sessionId": "c1", "uuid": "u1",
         "cwd": "C:/u/dev/alpha",
         "message": {"content": ("<command-name>/plan-review</command-name>" if not garbage
                                 else "please review the plan")}},
        {"type": "assistant", "timestamp": "2026-11-10T10:01:00Z", "message": {"content": []}},
        "not json at all",
    ]
    if garbage:
        main[0]["message"]["content"][0]["name"] = name
    _jsonl(proj / "c1.jsonl", main)
    sub = _claude_skill("build-step", "2026-11-11T10:00:00Z", "tu2")
    if garbage:
        sub["message"]["content"][0]["name"] = name
    _jsonl(proj / "c1" / "subagents" / "agent-1.jsonl", [sub])

    cx = home / ".codex" / "sessions" / "2026" / "11" / "rollout-1.jsonl"
    codex_rows = [
        {"timestamp": "2026-11-09T09:00:00Z", "type": "session_meta",
         "payload": {"id": "x1", "cwd": "C:/u/dev/skill-mesh", "thread_source": "user"}},
        {"timestamp": "2026-11-09T09:00:01Z", "type": "turn_context", "payload": {"turn_id": "t1"}},
        _codex_call("k1", "2026-11-09T09:00:02Z", ["plan-review"]),
        # The same SKILL.md read again in the same turn is one invocation.
        _codex_call("k2", "2026-11-09T09:00:03Z", ["plan-review"]),
        {"timestamp": "2026-11-09T09:01:00Z", "type": "turn_context", "payload": {"turn_id": "t2"}},
        _codex_call("k3", "2026-11-09T09:01:01Z", ["plan-review"]),
        # One call reading three skills is an inventory sweep, not three invocations.
        _codex_call("k4", "2026-11-09T09:01:02Z", ["build-step", "plan-review", "user-pm"]),
    ]
    if garbage:
        codex_rows = [r for r in codex_rows if r["payload"].get("type") != "function_call"]
    _jsonl(cx, codex_rows)

    cop = {"type": "tool.execution_complete", "timestamp": "2026-11-12T08:00:00Z", "id": "e1",
           "data": {"toolCallId": "p1", "result": {"skillName": "user-pm"}}}
    raw = json.dumps(cop, separators=(",", ":"))
    if garbage:
        raw = raw.replace("skillName", "toolName")
    path = home / ".copilot" / "session-state" / "s9" / "events.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(raw + "\n", encoding="utf-8")


def _manifest(tmp: Path) -> Path:
    m = tmp / "catalog" / "config" / "skill-manifest.json"
    m.parent.mkdir(parents=True)
    m.write_text(json.dumps({"skills": [
        {"name": n, "status": "portable", "description": f"{n} skill"} for n in EXPECTED]}),
        encoding="utf-8")
    return m


def _run(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(script), *args], capture_output=True,
                          text=True, encoding="utf-8", check=False)


def _snapshot(tmp: Path, garbage: bool = False, as_of: str = AS_OF):
    home = tmp / "home"
    if not home.exists():
        _store(home, garbage)
    events = tmp / "events.jsonl"
    scan = _run(SCAN, "--out", str(events), "--home", str(home), "--workers", "1")
    assert scan.returncode == 0, scan.stderr
    out = tmp / "snapshots"
    agg = _run(AGG, "--manifest", str(_manifest(tmp) if not (tmp / "catalog").exists()
                                      else tmp / "catalog" / "config" / "skill-manifest.json"),
               "--events", str(events), "--out-dir", str(out), "--as-of", as_of)
    assert agg.returncode == 0, agg.stderr
    day = as_of[:10]
    return json.loads((out / f"usage-{day}.json").read_text(encoding="utf-8")), agg.stdout, scan.stdout


def _count_problems(usage, expected) -> list:
    rows = {r["name"]: r for r in usage["rows"]}
    bad = []
    for name, want in expected.items():
        row = rows.get(name)
        if row is None:
            bad.append(f"{name}: no row")
            continue
        if set(row) != COLUMNS:
            bad.append(f"{name}: columns {sorted(set(row) ^ COLUMNS)}")
        for key, value in want.items():
            if row[key] != value:
                bad.append(f"{name}.{key} = {row[key]}, expected {value}")
    return bad


def test_snapshot_columns_and_counts_match_the_synthetic_store(tmp_path):
    usage, out, scan_out = _snapshot(tmp_path)
    assert scan_out.strip() == "files=4 events=10", scan_out
    assert _count_problems(usage, EXPECTED) == []
    rows = {r["name"]: r for r in usage["rows"]}
    assert rows["build-step"]["projects"] == ["alpha"]
    assert rows["plan-review"]["projects"] == ["alpha", "skill-mesh"]
    # No --repo: git-derived fields are null, never a guess.
    assert rows["build-step"]["core_lines"] is None and rows["build-step"]["commits_all"] is None
    assert usage["generated"].startswith("2026-11-13T00:00:00")
    assert "changes since: no earlier snapshot" in out


def test_snapshot_folder_is_self_ignoring_and_the_catalog_repo_is_refused(tmp_path):
    _snapshot(tmp_path)
    assert (tmp_path / "snapshots" / ".gitignore").read_text(encoding="utf-8").splitlines()[-1] == "*"
    inside = tmp_path / "catalog" / "docs" / "user-afterparty"
    r = _run(AGG, "--manifest", str(tmp_path / "catalog" / "config" / "skill-manifest.json"),
             "--events", str(tmp_path / "events.jsonl"), "--out-dir", str(inside), "--as-of", AS_OF)
    assert r.returncode == 2
    assert "refusing to write a snapshot inside the catalog repository" in r.stderr
    assert not inside.exists()


def test_a_second_snapshot_reports_what_changed_and_the_cadence_nudge(tmp_path):
    _snapshot(tmp_path, as_of="2026-10-02T00:00:00Z")
    _, out, _ = _snapshot(tmp_path)
    assert "changes since 2026-10-02:" in out
    assert "  build-step: top_w6 0 -> 1 (+1)" in out
    snaps = str(tmp_path / "snapshots")
    fresh = _run(AGG, "--check-cadence", "--out-dir", snaps, "--as-of", "2026-11-20T00:00:00Z")
    assert fresh.returncode == 0 and fresh.stdout == ""
    stale = _run(AGG, "--check-cadence", "--out-dir", snaps, "--as-of", "2026-12-20T00:00:00Z")
    assert stale.stdout.strip() == ("usage telemetry: last snapshot 2026-11-13 is 37 days old "
                                    "(cadence 31 days); run /user-afterparty.")
    none = _run(AGG, "--check-cadence", "--out-dir", str(tmp_path / "empty"), "--as-of", AS_OF)
    assert none.stdout.startswith("usage telemetry: no snapshot yet in ")


def test_count_helper_reds_on_a_garbage_store(tmp_path):
    """Garbage anchor: well-formed transcripts with no real skill call must fail the helper."""
    usage, _, _ = _snapshot(tmp_path, garbage=True)
    problems = _count_problems(usage, EXPECTED)
    assert problems, "the count helper passed a store that holds no skill invocation"
    assert any(p.startswith("build-step.total") for p in problems)
