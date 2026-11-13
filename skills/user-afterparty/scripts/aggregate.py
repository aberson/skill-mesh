"""Aggregate scanned skill-usage events into a dated snapshot (user-afterparty telemetry).

Usage:
  python -I aggregate.py --manifest <skill-manifest.json> --events <events.jsonl>
                         --out-dir <snapshot folder> [--repo <skill-mesh checkout>]
                         [--as-of <ISO-8601 time>] [--cadence-days 35]
  python -I aggregate.py --check-cadence --out-dir <snapshot folder> [--cadence-days 35]

Every location is an explicit argument; nothing is derived from this file's own folder,
so the installed copy never writes into the installed tree. The snapshot is
`<out-dir>/usage-<YYYY-MM-DD>.json` (the as-of date). Snapshots are private data: the
folder is given a `.gitignore` of `*` when this script creates it, and a folder inside the
repository that owns --manifest is refused (exit 2), so a snapshot never lands in the
skill catalog's repository.

--repo is optional. When it is given, each row also carries the core's line count and git
history (last commit, commits in the 60 days before the as-of time, all commits); without
it those fields are null. After writing, the script prints the table and what changed
since the newest earlier snapshot in the folder. --check-cadence writes nothing: it prints
a one-line nudge when the newest snapshot is older than the cadence (or none exists).

Packaged with user-afterparty (v3 catalog cleanup Step 18); it began as the hand-run
2026-11-11 usage survey script. Counting rules are unchanged from that survey; the one
addition is --as-of, which also drops events stamped after it (the survey used "now").
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

# The operator's recorded default (v3 cleanup decision item 8): nudge when the newest
# snapshot is over 35 days old.
CADENCE_DAYS = 35
SNAPSHOT_RE = re.compile(r"^usage-(\d{4}-\d{2}-\d{2})\.json$")
BUILTIN = {"clear", "model", "goal", "compact", "resume", "config", "init", "help", "context",
           "cost", "exit", "login", "status"}
NOT_SKILLS = {"x", "example", "demo", "fresh", "stale", "pending", "unreviewed", "unavailable",
              "reviewable"}


def parse_ts(value):
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def load_events(path):
    raw = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            e = json.loads(line)
            if "error" in e:
                continue
            e["skill"] = e["skill"].split(":")[-1].split()[0]
            if e["host"] == "codex" and e["root"].startswith("build:"):
                continue
            raw.append(e)
    return raw


def collapse(raw):
    """Drop Codex inventory sweeps, collapse repeat reads, parse timestamps."""
    percall = collections.defaultdict(set)
    perturn = collections.defaultdict(set)
    for e in raw:
        if e["host"] == "codex":
            percall[e["id"].rsplit(":", 1)[0]].add(e["skill"])
            perturn[(e["session"], e["turn"])].add(e["skill"])
    sweep_reads = collections.Counter()
    ev, seen = [], set()
    for e in raw:
        # Inventory sweep: one call reading >= 3 skills, or one turn reading >= 6.
        if e["host"] == "codex" and (len(percall[e["id"].rsplit(":", 1)[0]]) >= 3
                                     or len(perturn[(e["session"], e["turn"])]) >= 6):
            sweep_reads[e["skill"]] += 1
            continue
        # One Codex turn reading one SKILL.md several times is one invocation.
        if e["host"] == "codex":
            key = ("codex", e["session"], e["turn"] or e["id"], e["skill"])
        else:
            key = (e["host"], e["id"])
        if key in seen:
            continue
        seen.add(key)
        e["t"] = parse_ts(e.get("ts") or "")
        ev.append(e)
    return ev, sweep_reads


def project_of(cwd):
    if not cwd:
        return None
    parts = cwd.replace("\\", "/").rstrip("/").lower().split("/")
    if "dev" in parts:
        i = parts.index("dev")
        return parts[i + 1] if i + 1 < len(parts) else "dev(root)"
    return parts[-1]


def git_stats(repo, name, since):
    if not repo:
        return None, None, None, None

    def git(*a):
        return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True,
                              encoding="utf-8").stdout.strip()

    d = os.path.join(repo, "skills", name)
    core = os.path.join(d, "core.md")
    src = core if os.path.exists(core) else os.path.join(d, "providers", "claude.md")
    lines = sum(1 for _ in open(src, encoding="utf-8")) if os.path.exists(src) else 0
    last = git("log", "-1", "--format=%cs", "--", f"skills/{name}") or None
    c60 = int(git("rev-list", "--count", f"--since={since}", "HEAD", "--", f"skills/{name}") or 0)
    call = int(git("rev-list", "--count", "HEAD", "--", f"skills/{name}") or 0)
    return lines, last, c60, call


def build(manifest, events, as_of, repo):
    m = json.load(open(manifest, encoding="utf-8"))
    skills = m.get("skills", m) if isinstance(m, dict) else m
    meta = {s["name"]: s for s in skills}
    w6 = as_of - dt.timedelta(days=42)   # about the span Claude keeps transcripts
    w2 = as_of - dt.timedelta(days=14)
    since = (as_of - dt.timedelta(days=60)).date().isoformat()
    ev, sweep_reads = collapse(load_events(events))
    ev = [e for e in ev if e["t"] is None or e["t"] <= as_of]
    by = collections.defaultdict(list)
    for e in ev:
        by[e["skill"]].append(e)

    rows = []
    for name, s in meta.items():
        es = by.get(name, [])
        lines, last_commit, c60, call = git_stats(repo, name, since)
        tv = [e["t"] for e in es if e["t"]]

        def n(pred):
            return sum(1 for e in es if pred(e))

        rows.append(dict(
            name=name, status=s.get("status"), description=s.get("description", ""),
            core_lines=lines, last_commit=last_commit, commits_60d=c60, commits_all=call,
            total=len(es),
            w6=n(lambda e: e["t"] and e["t"] >= w6),
            w2=n(lambda e: e["t"] and e["t"] >= w2),
            top_w6=n(lambda e: e["t"] and e["t"] >= w6 and e["source"] != "subagent"),
            top_w2=n(lambda e: e["t"] and e["t"] >= w2 and e["source"] != "subagent"),
            top_all=n(lambda e: e["source"] != "subagent"),
            sub_w6=n(lambda e: e["t"] and e["t"] >= w6 and e["source"] == "subagent"),
            sweep=sweep_reads.get(name, 0),
            sessions_w6=len({(e["host"], e["session"]) for e in es if e["t"] and e["t"] >= w6}),
            claude=n(lambda e: e["host"] == "claude"),
            codex=n(lambda e: e["host"] == "codex"),
            copilot=n(lambda e: e["host"] == "copilot"),
            claude_w6=n(lambda e: e["host"] == "claude" and e["t"] and e["t"] >= w6),
            codex_w6=n(lambda e: e["host"] == "codex" and e["t"] and e["t"] >= w6),
            operator=n(lambda e: e["source"] == "operator"),
            model=n(lambda e: e["source"] == "model"),
            subagent=n(lambda e: e["source"] == "subagent"),
            sessions=len({(e["host"], e["session"]) for e in es}),
            projects=sorted({p for p in (project_of(e.get("cwd")) for e in es) if p}),
            self_share=round(sum(1 for e in es if project_of(e.get("cwd")) == "skill-mesh") / len(es), 2)
            if es else 0,
            first=min(tv).date().isoformat() if tv else None,
            last=max(tv).date().isoformat() if tv else None,
        ))
    rows.sort(key=lambda r: (-r["top_w6"], -r["sub_w6"], -r["top_all"], r["name"]))

    non = collections.Counter()
    for k, es in by.items():
        if (k in meta or k in BUILTIN or len(k) <= 2 or k.lower() in NOT_SKILLS
                or k.startswith(("zz-", "mesh-probe"))):
            continue
        non[k] = len(es)
    others = []
    for k, c in non.most_common():
        tv = [e["t"] for e in by[k] if e["t"]]
        others.append(dict(name=k, total=c, w6=sum(1 for t in tv if t >= w6),
                           last=max(tv).date().isoformat() if tv else None,
                           hosts=dict(collections.Counter(e["host"] for e in by[k])),
                           projects=sorted({p for p in (project_of(e.get("cwd")) for e in by[k]) if p})))
    hosts = {}
    for h in ("claude", "codex", "copilot"):
        tv = [e["t"] for e in ev if e["host"] == h and e["t"]]
        hosts[h] = dict(first=min(tv).date().isoformat(), last=max(tv).date().isoformat(),
                        n=len(tv)) if tv else None
    return dict(rows=rows, others=others, hosts=hosts, generated=as_of.isoformat())


def snapshots(out_dir):
    found = []
    for p in glob.glob(os.path.join(out_dir, "usage-*.json")):
        mt = SNAPSHOT_RE.match(os.path.basename(p))
        if mt:
            found.append((mt.group(1), p))
    return sorted(found)


def inside(path, root):
    path, root = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(root))
    return path == root or path.startswith(root.rstrip("\\/") + os.sep)


def changes(prev, cur):
    """Lines describing what moved since the previous snapshot."""
    before = {r["name"]: r for r in prev.get("rows", [])}
    after = {r["name"]: r for r in cur["rows"]}
    out = []
    for name in sorted(set(after) - set(before)):
        out.append(f"  new in catalog: {name}")
    for name in sorted(set(before) - set(after)):
        out.append(f"  gone from catalog: {name}")
    for name in sorted(set(before) & set(after)):
        d = after[name]["top_w6"] - before[name]["top_w6"]
        if d:
            out.append(f"  {name}: top_w6 {before[name]['top_w6']} -> {after[name]['top_w6']} ({d:+d})")
    return out or ["  no change in top-level 6-week counts"]


def cadence_line(out_dir, now, cadence):
    snaps = snapshots(out_dir) if os.path.isdir(out_dir) else []
    if not snaps:
        return f"usage telemetry: no snapshot yet in {out_dir}; run /user-afterparty (cadence {cadence} days)."
    last = dt.date.fromisoformat(snaps[-1][0])
    age = (now.date() - last).days
    if age > cadence:
        return (f"usage telemetry: last snapshot {last.isoformat()} is {age} days old "
                f"(cadence {cadence} days); run /user-afterparty.")
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Aggregate scanned skill-usage events into a dated snapshot.")
    ap.add_argument("--manifest")
    ap.add_argument("--events")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--repo")
    ap.add_argument("--as-of")
    ap.add_argument("--cadence-days", type=int, default=CADENCE_DAYS)
    ap.add_argument("--check-cadence", action="store_true")
    a = ap.parse_args(argv)
    now = parse_ts(a.as_of) if a.as_of else dt.datetime.now(dt.timezone.utc)
    if now is None:
        print(f"aggregate: --as-of is not an ISO-8601 time: {a.as_of}", file=sys.stderr)
        return 2
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    if a.check_cadence:
        line = cadence_line(a.out_dir, now, a.cadence_days)
        if line:
            print(line)
        return 0
    if not a.manifest or not a.events:
        print("aggregate: --manifest and --events are required (or use --check-cadence)", file=sys.stderr)
        return 2
    catalog_repo = os.path.dirname(os.path.dirname(os.path.abspath(a.manifest)))
    if inside(a.out_dir, catalog_repo):
        print(f"aggregate: refusing to write a snapshot inside the catalog repository ({catalog_repo}); "
              "snapshots are private data", file=sys.stderr)
        return 2
    prev = snapshots(a.out_dir) if os.path.isdir(a.out_dir) else []
    data = build(a.manifest, a.events, now, a.repo)
    if not os.path.isdir(a.out_dir):
        os.makedirs(a.out_dir)
        with open(os.path.join(a.out_dir, ".gitignore"), "w", encoding="utf-8") as fh:
            fh.write("# Private usage snapshots (user-afterparty telemetry); never committed.\n*\n")
    target = os.path.join(a.out_dir, f"usage-{now.date().isoformat()}.json")
    prev = [p for p in prev if os.path.abspath(p[1]) != os.path.abspath(target)]
    with open(target, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    print(f"snapshot: {target}")
    print("host windows:", data["hosts"])
    print(f"{'#':>2} {'skill':22} {'top6':>4} {'top2':>4} {'topA':>4} {'sub6':>4} {'swp':>4} "
          f"{'cl6':>4} {'cx6':>4} {'op':>3} {'ses6':>4} {'self':>4} {'last':10}")
    for i, r in enumerate(data["rows"], 1):
        print(f"{i:>2} {r['name']:22} {r['top_w6']:>4} {r['top_w2']:>4} {r['top_all']:>4} "
              f"{r['sub_w6']:>4} {r['sweep']:>4} {r['claude_w6']:>4} {r['codex_w6']:>4} "
              f"{r['operator']:>3} {r['sessions_w6']:>4} {r['self_share']:>4} {str(r['last']):10}")
    if prev:
        print(f"changes since {prev[-1][0]}:")
        for line in changes(json.load(open(prev[-1][1], encoding="utf-8")), data):
            print(line)
    else:
        print("changes since: no earlier snapshot")
    return 0


if __name__ == "__main__":
    sys.exit(main())
