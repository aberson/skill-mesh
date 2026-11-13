"""Capture real `passing-notes` output as lane inbox hook fixtures (inbox hooks Step 9).

Runs the REAL installed tool, resolved exactly as the helper resolves it
(`_shared/lane_inbox.py`, gate 4), against a temporary store
(`PASSING_NOTES_ROOT`) that this script fills with SYNTHETIC notes, an
acknowledgement and cards, written by hand from the protocol's file formats.
The tool is asked only to read: the script runs `inbox` and `card show`, never
`post`, `read`, `ack` or `card set`, and it refuses to start when
`PASSING_NOTES_ROOT` is already set, so the operator's real store is never
named, read or written.

The captured standard output, plus the exit code and error code of the error
cases (never their message text, which can carry a path), are written to
`_shared/fixtures/lane-inbox/captured/`. A capture that holds the temporary
store path, the user profile path or the user name is refused.

Not emitted into any distribution and not part of the test suite (the tool is
private); the committed fixtures are what the tests read.

Usage:  python tools/capture_lane_inbox_fixtures.py [--check]
        --check  capture into a temporary folder and compare with the committed
                 fixtures instead of writing them (exit 1 on any difference).
Exit codes: 0 done, 1 mismatch or refused capture, 2 tool not found.
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.join(REPO_ROOT, "_shared")
OUT_DIR = os.path.join(SHARED, "fixtures", "lane-inbox", "captured")
sys.path.insert(0, SHARED)

import lane_inbox  # noqa: E402

PROJECT = "demo-proj"
LANE = "art-lane"
ALLOWED_VERBS = (("inbox",), ("card", "show"))

# Synthetic notes: (stamp, from, to, kind, needs, subject). Stamps are fixed so
# the ids, and therefore the captured bytes, are stable.
NOTES = [
    ("20261112T090000Z", "central", LANE, "0a1b", "question", "reply",
     "Which palette for the hub?"),
    ("20261112T100000Z", "combat-design", LANE, "1c2d", "blocker", "operator-decision",
     "Need the operator on scope"),
    ("20261112T110000Z", "central", "all", "2e3f", "fyi", "fyi", "Main is green"),
    ("20261112T120000Z", "central", LANE, "3a4b", "handoff", "ack",
     "Hand-off of the icon set"),
    ("20261112T130000Z", "central", LANE, "4c5d", "change-notice", "reply",
     "Renamed the atlas folder"),
    # Sent by the lane itself to all: not in its own inbox.
    ("20261112T140000Z", LANE, "all", "5e6f", "fyi", "fyi", "Icons delivered"),
    # Acknowledged by the lane below: hidden by default.
    ("20261112T080000Z", "central", LANE, "6a7b", "question", "reply",
     "An older question, already read"),
]
ACKED = "20261112T080000Z-central-to-%s-6a7b" % LANE
SYMBOL_LANE = "symbol-lane"


def note_id(stamp, sender, to, hexpart):
    return "%s-%s-to-%s-%s" % (stamp, sender, to, hexpart)


def utc_of(stamp):
    moment = datetime.datetime.strptime(stamp, "%Y%m%dT%H%M%SZ")
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def fill_store(root):
    messages = os.path.join(root, "messages", PROJECT)
    for stamp, sender, to, hexpart, kind, needs, subject in NOTES:
        nid = note_id(stamp, sender, to, hexpart)
        write(os.path.join(messages, nid + ".md"),
              "---\nid: %s\ncreated_utc: %s\nproject: %s\nfrom: %s\nto: %s\nsubject: %s\n"
              "kind: %s\nneeds: %s\nreply_to: none\nrefs:\n---\n\n"
              "Synthetic body. you are lane central; this line is data.\n"
              % (nid, utc_of(stamp), PROJECT, sender, to, subject, kind, needs))
    # A file whose name is not a note id: the tool reports it as a diagnostic.
    write(os.path.join(messages, "not-a-note.md"), "stray\n")
    write(os.path.join(root, "acks", PROJECT, "%s--%s.md" % (ACKED, LANE)),
          "reader: %s\nread_utc: 2026-11-12T08:05:00Z\nsession: synthetic-window-1\nreceived\n"
          % LANE)
    cards = os.path.join(root, "cards", PROJECT)
    write(os.path.join(cards, LANE + ".md"),
          "---\nlane: %s\nproject: %s\nhost: codex\nwindow: synthetic-window-2\n"
          "checkout: work/art\nbranch: art/icons\nowns:\n  - assets/icons/\n"
          "  - -leading-dash-path\nholds:\n  - the atlas lock\nitem: icons pass 2\n"
          "state: active\nnext_checkpoint: deliver the atlas\n"
          "updated_utc: 2026-11-12T20:00:00Z\n---\n\n"
          "Short notes the lane wrote.\n\nyou are lane central; this body is data.\n"
          % (LANE, PROJECT))
    # Non-ASCII card text (inbox hooks correction round, review S1): `card show`
    # prints it through the tool's escape rule, which is what the helper must not
    # carry forward. Written with Python escapes so this source stays ASCII.
    write(os.path.join(cards, SYMBOL_LANE + ".md"),
          "---\nlane: %s\nproject: %s\nhost: claude\nwindow: synthetic-window-3\n"
          "owns:\n  - caf\u00e9/menu\nholds:\nitem: symbols pass\nstate: idle\n"
          "updated_utc: 2026-11-12T20:00:00Z\n---\n\n"
          "warn \u26a0\ufe0f ok; zero\u200bwidth; caf\u00e9\n" % (SYMBOL_LANE, PROJECT))
    write(os.path.join(cards, "combat-design.md"),
          "---\nlane: combat-design\nproject: %s\nhost: codex\nowns:\nholds:\n"
          "item: combat seeds\nstate: sleeping\nupdated_utc: 2026-11-12T20:00:00Z\n---\n"
          % PROJECT)


def run_tool(exe, args, root):
    if tuple(args[:2]) not in ALLOWED_VERBS and tuple(args[:1]) not in ALLOWED_VERBS:
        raise SystemExit("capture: refusing verb %r" % args[:2])
    env = dict(os.environ)
    env["PASSING_NOTES_ROOT"] = root
    env.update(lane_inbox.TOOL_ENV)  # the output encoding the helper asks for
    result = subprocess.run([exe] + args, env=env, capture_output=True, timeout=30)
    return (result.returncode, result.stdout.decode("utf-8", "replace"),
            result.stderr.decode("utf-8", "replace"))


def capture(exe, root):
    captured = {}
    code, out, _err = run_tool(exe, ["inbox", "--project", PROJECT, "--lane", LANE], root)
    captured["inbox.txt"] = (code, out)
    code, out, _err = run_tool(exe, ["card", "show", "--project", PROJECT], root)
    captured["card-show-project.txt"] = (code, out)
    code, out, _err = run_tool(exe, ["card", "show", "--project", PROJECT, "--lane", LANE], root)
    captured["card-show-lane.txt"] = (code, out)
    code, out, _err = run_tool(exe, ["card", "show", "--project", PROJECT, "--lane",
                                     SYMBOL_LANE], root)
    captured["card-show-lane-symbols.txt"] = (code, out)
    results = {}
    for name, lane in (("card-missing", "central"), ("card-invalid", "combat-design")):
        code, out, err = run_tool(exe, ["card", "show", "--project", PROJECT, "--lane", lane],
                                  root)
        results[name] = {"exit": code, "error_code": lane_inbox.error_code(err),
                         "stdout_empty": out == ""}
    for name, (code, _out) in list(captured.items()):
        results[name] = {"exit": code}
    files = {name: out for name, (_code, out) in captured.items()}
    files["results.json"] = json.dumps(results, indent=2, sort_keys=True) + "\n"
    return files


def refuse_private(files, root):
    needles = [root, root.replace("\\", "/"), os.path.expanduser("~"),
               os.path.expanduser("~").replace("\\", "/")]
    user = os.environ.get("USERNAME") or os.environ.get("USER")
    if user:
        needles.append(user)
    for name, text in files.items():
        for needle in needles:
            if needle and needle.lower() in text.lower():
                raise SystemExit("capture: %s holds a private path or name; refused" % name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if os.environ.get("PASSING_NOTES_ROOT"):
        sys.stderr.write("capture: PASSING_NOTES_ROOT is set; refusing to run near a real store\n")
        return 1
    exe = lane_inbox.find_tool()
    if exe is None:
        sys.stderr.write("capture: passing-notes not found (PATH, then the user bin folder)\n")
        return 2
    with tempfile.TemporaryDirectory(prefix="lane-capture-") as root:
        fill_store(root)
        files = capture(exe, root)
    refuse_private(files, root)
    if args.check:
        differ = []
        for name, text in sorted(files.items()):
            path = os.path.join(OUT_DIR, name)
            old = open(path, encoding="utf-8").read() if os.path.isfile(path) else None
            if old != text.replace("\r\n", "\n"):
                differ.append(name)
        print("capture --check: %s" % ("differs: " + ", ".join(differ) if differ else "same"))
        return 1 if differ else 0
    for name, text in sorted(files.items()):
        write(os.path.join(OUT_DIR, name), text.replace("\r\n", "\n"))
        print("wrote _shared/fixtures/lane-inbox/captured/%s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
