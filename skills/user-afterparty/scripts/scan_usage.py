"""Scan Claude, Codex and Copilot transcripts for skill invocations (user-afterparty telemetry).

Writes one JSON event per invocation to --out (JSON Lines):
  host, skill, ts, session, source (operator|model|subagent), cwd, root, id, turn
Read-only over the transcript stores. The stores are found under --home (default: the
user's home directory, via os.path.expanduser), so no absolute path is embedded here.

Usage:
  python -I scan_usage.py --out <events.jsonl> [--home <dir>] [--workers <n>]

Packaged with user-afterparty (v3 catalog cleanup Step 18); it began as the hand-run
2026-11-11 usage survey script. Detection rules are unchanged from that survey.
"""
import argparse
import glob
import json
import os
import re
import sys
from multiprocessing import Pool

CMD_RE = re.compile(r"<command-name>/?([^<\s]+)</command-name>")
# A skill-root SKILL.md path (forward or back slashes); ~80 chars of prefix classify the root.
PATH_RE = re.compile(r"([^\s'\"`]{0,80}?)[\\/]+skills[\\/]+([A-Za-z0-9._:-]+)[\\/]+SKILL\.md", re.I)
COP_RE = re.compile(r'"skillName":"([^"]+)"')


def classify_root(prefix):
    p = prefix.replace("\\", "/").lower()
    for tag in ("release-stage", "/dist/", "dist/", "/tests/", "fixtures", "archive"):
        if tag in p:
            return "build:" + tag.strip("/")
    for tag in (".agents", ".codex", ".claude", ".github", ".copilot"):
        if p.endswith(tag) or (tag + "/") in p:
            return tag
    return "other"


def text_of(content):
    if isinstance(content, str):
        return content
    out = []
    if isinstance(content, list):
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                out.append(c.get("text", ""))
    return "\n".join(out)


def scan_claude(path):
    ev = []
    sub = os.sep + "subagents" + os.sep in path
    try:
        fh = open(path, "rb")
    except OSError:
        return ev
    with fh:
        for raw in fh:
            if b'"name":"Skill"' not in raw and b"<command-name>" not in raw:
                continue
            try:
                d = json.loads(raw)
            except Exception:
                continue
            t = d.get("type")
            base = dict(host="claude", ts=d.get("timestamp"), session=d.get("sessionId"),
                        cwd=d.get("cwd"), root=".claude", turn=None)
            if t == "assistant":
                for c in (d.get("message") or {}).get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Skill":
                        sk = (c.get("input") or {}).get("skill")
                        if sk:
                            ev.append(dict(base, skill=sk, id=c.get("id"),
                                           source="subagent" if (sub or d.get("isSidechain")) else "model"))
            elif t == "user" and not d.get("isMeta"):
                txt = text_of((d.get("message") or {}).get("content"))
                m = CMD_RE.search(txt[:2000])
                if m:
                    ev.append(dict(base, skill=m.group(1), id=d.get("uuid"),
                                   source="subagent" if sub else "operator"))
    return ev


def scan_codex(path):
    ev = []
    session = None
    thread = "user"
    cwd = None
    turn = None
    try:
        fh = open(path, "rb")
    except OSError:
        return ev
    with fh:
        for raw in fh:
            head = raw[:400]
            if b'"session_meta"' in head:
                try:
                    p = json.loads(raw).get("payload") or {}
                    session = p.get("id") or p.get("session_id")
                    cwd = p.get("cwd")
                    ts_ = p.get("thread_source")
                    thread = ts_ if isinstance(ts_, str) else (
                        "subagent" if isinstance(p.get("source"), dict) else "user")
                except Exception:
                    pass
                continue
            if b'"task_started"' in head or b'"turn_context"' in head:
                try:
                    p = json.loads(raw).get("payload") or {}
                    turn = p.get("turn_id") or turn
                except Exception:
                    pass
                continue
            if b"SKILL.md" not in raw:
                continue
            if not (b'"function_call"' in head or b'"custom_tool_call"' in head
                    or b'"local_shell_call"' in head):
                continue
            try:
                d = json.loads(raw)
            except Exception:
                continue
            p = d.get("payload", d)
            pt = p.get("type")
            if pt == "function_call":
                txt = p.get("arguments") or ""
            elif pt == "custom_tool_call":
                txt = p.get("input") or ""
            elif pt == "local_shell_call":
                txt = json.dumps(p.get("action"))
            else:
                continue
            if not isinstance(txt, str):
                txt = json.dumps(txt)
            txt = txt.replace("\\\\", "\\")
            seen = set()
            for m in PATH_RE.finditer(txt):
                sk = m.group(2)
                if sk.startswith(".") or sk in seen:
                    continue
                seen.add(sk)
                ev.append(dict(host="codex", skill=sk, ts=d.get("timestamp"), session=session, cwd=cwd,
                               root=classify_root(m.group(1)), turn=turn,
                               id=(p.get("call_id") or p.get("id") or "") + ":" + sk,
                               source="subagent" if thread != "user" else "model"))
    return ev


def scan_copilot(path):
    ev = []
    try:
        fh = open(path, "rb")
    except OSError:
        return ev
    session = os.path.basename(os.path.dirname(path))
    with fh:
        for raw in fh:
            if b'"tool.execution_complete"' not in raw[:200] or b'"skillName"' not in raw:
                continue
            try:
                d = json.loads(raw)
            except Exception:
                continue
            m = COP_RE.search(raw.decode("utf-8", "replace"))
            if not m:
                continue
            dd = d.get("data") or {}
            ev.append(dict(host="copilot", skill=m.group(1), ts=d.get("timestamp"), session=session,
                           cwd=None, root="copilot", turn=None,
                           id=dd.get("toolCallId") or d.get("id"), source="model"))
    return ev


SCANNERS = {"claude": scan_claude, "codex": scan_codex, "copilot": scan_copilot}


def work(item):
    kind, path = item
    try:
        return SCANNERS[kind](path)
    except Exception as e:  # one bad file never kills the run; it is reported as an error event
        return [dict(host=kind, error=str(e), path=path)]


def transcript_items(home):
    items = []
    for kind, parts in (("claude", (".claude", "projects")),
                        ("codex", (".codex", "sessions")),
                        ("codex", (".codex", "archived_sessions")),
                        ("copilot", (".copilot", "session-state"))):
        for p in glob.glob(os.path.join(home, *parts, "**", "*.jsonl"), recursive=True):
            items.append((kind, p))
    # Biggest first, for better load balance.
    items.sort(key=lambda it: -os.path.getsize(it[1]))
    return items


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scan Claude, Codex and Copilot transcripts for skill invocations.")
    ap.add_argument("--out", required=True, help="events file to write (JSON Lines)")
    ap.add_argument("--home", default=os.path.expanduser("~"),
                    help="directory holding .claude, .codex and .copilot (default: your home)")
    ap.add_argument("--workers", type=int, default=max(2, (os.cpu_count() or 4) - 1),
                    help="worker processes; 1 scans in this process")
    a = ap.parse_args(argv)
    items = transcript_items(a.home)
    n = 0
    with open(a.out, "w", encoding="utf-8") as out:
        if a.workers <= 1:
            results = map(work, items)
            for evs in results:
                for e in evs:
                    out.write(json.dumps(e) + "\n")
                    n += 1
        else:
            with Pool(a.workers) as pool:
                for evs in pool.imap_unordered(work, items, chunksize=4):
                    for e in evs:
                        out.write(json.dumps(e) + "\n")
                        n += 1
    print(f"files={len(items)} events={n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
