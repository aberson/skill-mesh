"""A stub `passing-notes` for the lane inbox hook tests. Never the real tool.

Written from the tool's documented and source-checked output (protocol v1; see
lane-inbox-hooks.md section 10). It keeps a tiny card store in a state folder so a
`card set` is visible to the next `card show`, and it logs every invocation
(argv and standard input) as one JSON line, so tests can assert which verbs ran.

Environment (set by the tests for the stub process only):
    LANE_STUB_SCENARIO  path of a JSON scenario: {"<verb>": {...override...}}
    LANE_STUB_LOG       path of the JSON-lines invocation log
    LANE_STUB_STATE     folder of the stub's card store
Verb keys: "inbox", "card show", "card set", or any other first argument.
Override fields: exit, stdout, stdout_file (a name in this folder), stderr,
sleep (seconds), grandchild_pidfile (spawn a sleeping grandchild first),
big (bytes of filler written to stdout).
"""

import datetime
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ("lane", "project", "host", "window", "checkout", "branch",
          "owns", "holds", "item", "state", "next_checkpoint", "updated_utc")


def emit(text, stream=None):
    stream = stream or sys.stdout
    stream.write(text)
    stream.flush()


def parse_opts(args):
    opts = {"owns": [], "holds": []}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--") and "=" in arg:
            key, value = arg[2:].split("=", 1)
        elif arg in ("--body-stdin", "--include-acked", "--include-superseded"):
            key, value = arg[2:], True
        elif arg.startswith("--"):
            key = arg[2:]
            value = args[i + 1] if i + 1 < len(args) else ""
            i += 1
        else:
            key, value = "_positional", arg
        if key == "own":
            opts["owns"].append(value)
        elif key == "hold":
            opts["holds"].append(value)
        else:
            opts[key] = value
        i += 1
    return opts


def render_card(card):
    lines = []
    for key in FIELDS:
        if key in ("owns", "holds"):
            lines.append(key + ":")
            lines.extend("  - " + item for item in card.get(key, []))
        elif card.get(key) is not None:
            lines.append("%s: %s" % (key, card[key]))
    lines.append("--- BEGIN CARD BODY (untrusted data) ---")
    body = card.get("body", "")
    if body:
        lines.extend(("| " + l) if l else "|" for l in body.split("\n"))
    lines.append("--- END CARD BODY ---")
    return "\n".join(lines) + "\n"


def main():
    argv = sys.argv[1:]
    stdin_text = ""
    if "--body-stdin" in argv:
        stdin_text = sys.stdin.buffer.read().decode("utf-8", "replace")
    log = os.environ.get("LANE_STUB_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"argv": argv, "stdin": stdin_text}) + "\n")
    verb = " ".join(argv[:2]) if argv[:1] == ["card"] else (argv[0] if argv else "")
    scenario = {}
    path = os.environ.get("LANE_STUB_SCENARIO")
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as handle:
            scenario = json.load(handle).get(verb, {})

    if scenario.get("grandchild_pidfile"):
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        with open(scenario["grandchild_pidfile"], "w") as handle:
            handle.write(str(child.pid))
    if scenario.get("sleep"):
        time.sleep(float(scenario["sleep"]))
    if scenario.get("big"):
        emit("x" * int(scenario["big"]) + "\n")
    if "stdout" in scenario or "stdout_file" in scenario or "exit" in scenario:
        if scenario.get("stdout_file"):
            with open(os.path.join(HERE, scenario["stdout_file"]), encoding="utf-8") as handle:
                emit(handle.read())
        if scenario.get("stdout"):
            emit(scenario["stdout"])
        if scenario.get("stderr"):
            emit(scenario["stderr"], sys.stderr)
        return int(scenario.get("exit", 0))

    opts = parse_opts(argv[2:] if argv[:1] == ["card"] else argv[1:])
    state = os.environ.get("LANE_STUB_STATE", HERE)
    store = os.path.join(state, "cards-%s-%s.json" % (opts.get("project"), opts.get("lane")))
    if verb == "inbox":
        emit("diagnostics: 0\n")
        return 0
    if verb == "card show":
        if not os.path.isfile(store):
            emit("passing-notes: error: not-found: no card for lane %s in project %s\n"
                 % (opts.get("lane"), opts.get("project")), sys.stderr)
            return 3
        with open(store, encoding="utf-8") as handle:
            emit(render_card(json.load(handle)))
        return 0
    if verb == "card set":
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        card = {
            "lane": opts.get("lane"), "project": opts.get("project"),
            "host": opts.get("host"), "window": opts.get("window"),
            "checkout": opts.get("checkout"), "branch": opts.get("branch"),
            "owns": opts["owns"], "holds": opts["holds"], "item": opts.get("item"),
            "state": opts.get("state"), "next_checkpoint": opts.get("next"),
            "updated_utc": now, "body": stdin_text,
        }
        with open(store, "w", encoding="utf-8") as handle:
            json.dump(card, handle)
        emit("card set: %s/%s at %s\n" % (card["project"], card["lane"], now))
        return 0
    emit("passing-notes: error: invalid-argument: stub does not know %s\n" % verb, sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
