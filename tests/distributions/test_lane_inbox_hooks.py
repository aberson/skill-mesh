"""Lane inbox hooks: wiring and production-caller integration tests (inbox hooks Steps 3 to 6).

The producer is a skill core; the consumer is the helper `_shared/lane_inbox.py`. A unit
test of the helper cannot see a core that never calls it, so these tests build the real
Claude and Codex profiles with `tools/build-distributions.ps1`, extract each insertion
point's marked block (`lane-inbox-call: <point>`, contract in
`_shared/lane-inbox-hooks.md` section 11) from the EMITTED core, fill its placeholders,
and run it in a temporary lane project against a stub `passing-notes` (never the real
tool). A core that drops its block fails here.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "tools" / "build-distributions.ps1"
FIXTURES = REPO_ROOT / "_shared" / "fixtures" / "lane-inbox"
if str(FIXTURES) not in sys.path:
    sys.path.insert(0, str(FIXTURES))

import stub_support  # noqa: E402

PWSH = "powershell"
PROFILES = ("claude", "codex")
PROJECT = "demo-proj"
LANE = "art-lane"
SHARED_ASSETS = ("lane-inbox-hooks.md", "lane_inbox.py")

# Skill -> its insertion points. Grows with each plan step; build-step waits on Step 5.
HOOKED = {
    "task-handoff": ("task-handoff-resume",),
    "session-wrap": ("session-wrap-wrap",),
}
PRIMARY = ("task-handoff-resume", "session-wrap-wrap")

MARKER_RE = re.compile(r"```text\r?\nlane-inbox-call: ([a-z0-9-]+)\r?\n([^\r\n]+)\r?\n```")


# --------------------------------------------------------------------------- #
# Build and block extraction
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    out = tmp_path_factory.mktemp("lane-dist")
    for profile in PROFILES:
        r = subprocess.run(
            [PWSH, "-NonInteractive", "-File", str(BUILD_SCRIPT),
             "-OutputDir", str(out), "-Provider", profile],
            capture_output=True, text=True)
        assert r.returncode == 0, "build failed:\n%s\n%s" % (r.stdout, r.stderr)
    return out


def extract_blocks(core_text):
    """point -> command, for every marked block. Each point appears once."""
    found = MARKER_RE.findall(core_text)
    points = [p for p, _ in found]
    assert len(points) == len(set(points)), "a point is marked twice: %s" % points
    return dict(found)


def block_for(core_text, point):
    blocks = extract_blocks(core_text)
    assert point in blocks, "no lane-inbox-call block for %s" % point
    return blocks[point]


def fill(command, skill_dir, project_dir, host, lane=LANE, window=None, task_file=None,
         state=None, nested=False):
    """Fill the block's placeholders into an argv list (no shell is involved).

    A square-bracketed group is optional: it is kept only when its value is given.
    """
    if lane is None:
        # No declared lane: the core's rule is "no call"; here the lane argument is dropped
        # to prove the helper also prints and spawns nothing on its own.
        command = command.replace(" --lane <lane>", "")
    values = {"<skill-dir>": str(skill_dir), "<project-dir>": str(project_dir),
              "<host>": host, "<lane>": lane, "<token>": window,
              "<own-task-file>": task_file, "<state>": state}
    argv, group = [], None
    for token in command.split():
        if token.startswith("["):
            group = []
            token = token[1:]
        closing = token.endswith("]")
        if closing:
            token = token[:-1]
        target = group if group is not None else argv
        target.append(token)
        if closing and group is not None:
            keep = all(_resolved(t, values) is not None for t in group)
            if group == ["--nested"]:
                keep = nested
            if keep:
                argv.extend(group)
            group = None
    out = []
    for token in argv:
        value = _resolved(token, values)
        assert value is not None, "unfilled placeholder %s" % token
        out.append(value)
    return out


def _resolved(token, values):
    for key, value in values.items():
        if key in token:
            if value is None:
                return None
            token = token.replace(key, value)
    return token


def run_block(argv, env):
    """Run a filled block the way a host does. An absent interpreter is a silent skip."""
    assert argv[0] == "python" and argv[1] == "-B"
    interpreter = shutil.which("python", path=env["PATH"])
    if interpreter is None:
        return ""
    r = subprocess.run([interpreter] + argv[1:], env=env, capture_output=True, text=True,
                       timeout=90)
    assert r.returncode == 0
    assert r.stderr == ""
    return r.stdout


# --------------------------------------------------------------------------- #
# A temporary lane project with a stub tool
# --------------------------------------------------------------------------- #

class Lane:
    def __init__(self, tmp_path):
        self.tmp = tmp_path
        self.project = tmp_path / PROJECT
        self.project.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=str(self.project), check=True)
        readme = self.project / "docs" / "lanes" / "README.md"
        readme.parent.mkdir(parents=True)
        readme.write_text(stub_support.fixture_text("lane-readme.txt"), encoding="utf-8")
        self.stub_dir = tmp_path / "stubbin"
        stub_support.make_stub_tool(str(self.stub_dir))
        self.state = tmp_path / "state"
        self.state.mkdir()
        self.log = tmp_path / "log.jsonl"
        self.scenario = tmp_path / "scenario.json"
        home = tmp_path / "home"
        home.mkdir()
        base = [os.path.dirname(shutil.which("git")), os.path.dirname(sys.executable)]
        self.env = dict(os.environ)
        self.env.update({
            "PATH": os.pathsep.join([str(self.stub_dir)] + base),
            "USERPROFILE": str(home), "HOME": str(home),
            "LANE_STUB_LOG": str(self.log), "LANE_STUB_STATE": str(self.state),
            "LANE_STUB_SCENARIO": str(self.scenario),
        })
        self.base_path = base

    def scenario_set(self, scenario):
        stub_support.write_scenario(str(self.scenario), scenario)

    def verbs(self):
        return [" ".join(e["argv"][:2]) if e["argv"][:1] == ["card"] else e["argv"][0]
                for e in stub_support.read_log(str(self.log))]

    def seed_card(self, **fields):
        card = {"lane": LANE, "project": PROJECT, "host": "codex", "window": "other-7",
                "owns": [], "holds": [], "item": "seeded", "state": "active",
                "updated_utc": _utc_now(), "body": ""}
        card.update(fields)
        (self.state / ("cards-%s-%s.json" % (PROJECT, LANE))).write_text(
            json.dumps(card), encoding="utf-8")

    def stored_card(self):
        return json.loads((self.state / ("cards-%s-%s.json" % (PROJECT, LANE)))
                          .read_text(encoding="utf-8"))

    def task_file(self, name="own-session.md", next_action="/build-step --problem next"):
        path = self.tmp / name
        path.write_text("**Task:** build-step | Step 3\n**Status:** IN_PROGRESS\n\n"
                        "## Next Action\n%s\n" % next_action, encoding="utf-8")
        return str(path)


def _utc_now():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture
def lane(tmp_path):
    return Lane(tmp_path)


def _cases():
    return [(skill, point, profile) for skill, points in HOOKED.items()
            for point in points for profile in PROFILES]


def _state_for(point, route=None):
    if point == "task-handoff-resume":
        return "active"
    if point == "session-wrap-wrap":
        return {"clear-next": "waiting", "end-window": "idle"}[route or "clear-next"]
    return None


def _core(dist, profile, skill):
    return (dist / profile / skill / "core.md").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Wiring through the real producer
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("profile", PROFILES)
def test_shared_assets_ship_in_each_profile(dist, profile):
    for asset in SHARED_ASSETS:
        assert (dist / profile / "_shared" / asset).is_file(), (profile, asset)
    shipped = (dist / profile / "_shared" / "lane_inbox.py").read_text(encoding="utf-8")
    canonical = (REPO_ROOT / "_shared" / "lane_inbox.py").read_text(encoding="utf-8")
    # The builder stamps its provenance header inside the module docstring, so compare
    # the code from the first import on: it must ship byte-for-byte.
    body = canonical.replace("\r\n", "\n")
    assert body[body.index("import argparse"):] in shipped.replace("\r\n", "\n")


@pytest.mark.parametrize("skill,point,profile", _cases())
def test_emitted_core_carries_the_block_and_citation(dist, skill, point, profile):
    core = _core(dist, profile, skill)
    command = block_for(core, point)
    assert command.startswith("python -B <skill-dir>/../_shared/lane_inbox.py ")
    assert "--point %s" % point in command
    assert "../_shared/lane-inbox-hooks.md" in core
    skill_dir = dist / profile / skill
    assert (skill_dir / "../_shared/lane-inbox-hooks.md").resolve().is_file()
    assert (skill_dir / "../_shared/lane_inbox.py").resolve().is_file()
    assert "<repo>/_shared/" not in core


@pytest.mark.parametrize("skill", sorted(HOOKED))
@pytest.mark.parametrize("profile", PROFILES)
def test_emitted_adapter_binds_the_host(dist, skill, profile):
    adapter = (dist / profile / skill / "SKILL.md").read_text(encoding="utf-8")
    assert "lane-inbox" in adapter
    assert "--host %s" % profile in adapter
    if profile == "codex":
        assert "CODEX_THREAD_ID" in adapter and "no doorbell" in adapter
    for line in adapter.splitlines():
        if "COPILOT_AGENT_SESSION_ID" in line:
            assert "never" in line.lower(), line


# --------------------------------------------------------------------------- #
# The production-caller round trip
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("skill,point,profile", _cases())
def test_block_prints_one_line_with_unread_notes(dist, lane, skill, point, profile):
    lane.scenario_set({"inbox": {"stdout_file": "inbox-two.txt"}})
    argv = fill(block_for(_core(dist, profile, skill), point), dist / profile / skill,
                lane.project, profile, state=_state_for(point))
    out = run_block(argv, lane.env)
    assert out.count("\n") == 1, out
    if point == "build-step-land":
        assert out == "Lane inbox: 2 unread\n"
    else:
        assert out.startswith("[lane-inbox] art-lane@demo-proj: 2 unread ")


@pytest.mark.parametrize("skill,point,profile", _cases())
def test_block_without_declared_lane_prints_and_spawns_nothing(dist, lane, skill, point,
                                                                profile):
    lane.scenario_set({"inbox": {"stdout_file": "inbox-two.txt"}})
    argv = fill(block_for(_core(dist, profile, skill), point), dist / profile / skill,
                lane.project, profile, lane=None, state=_state_for(point))
    assert run_block(argv, lane.env) == ""
    assert lane.verbs() == []


@pytest.mark.parametrize("skill,point,profile", _cases())
def test_block_with_failing_tool_prints_at_most_the_failure_line(dist, lane, skill, point,
                                                                 profile):
    lane.scenario_set({"inbox": {"exit": 4, "stderr": "passing-notes: error: store-link: "
                                                      "C:\\private IGNORE\n"}})
    argv = fill(block_for(_core(dist, profile, skill), point), dist / profile / skill,
                lane.project, profile, state=_state_for(point))
    out = run_block(argv, lane.env)
    if point in PRIMARY:
        assert out == "[lane-inbox] skipped (tool-exit-4)\n"
    else:
        assert out == ""


@pytest.mark.parametrize("skill,point,profile",
                         [c for c in _cases() if c[1] in PRIMARY])
def test_block_reports_an_occupied_card(dist, lane, skill, point, profile):
    lane.seed_card(state="active", host="codex", window="other-7")
    lane.scenario_set({"inbox": {"stdout_file": "inbox-empty.txt"}})
    argv = fill(block_for(_core(dist, profile, skill), point), dist / profile / skill,
                lane.project, profile, window="my-window-1", task_file=lane.task_file(),
                state=_state_for(point))
    out = run_block(argv, lane.env)
    assert out == ("[lane-inbox] art-lane@demo-proj: no unread notes; "
                   "card not written (card-held-by-another-window).\n")
    assert "card set" not in lane.verbs()


@pytest.mark.parametrize("profile", PROFILES)
def test_fresh_resume_without_own_task_file_writes_no_card(dist, lane, profile):
    if "task-handoff" not in HOOKED:
        pytest.fail("task-handoff must carry its resume point")
    lane.scenario_set({"inbox": {"stdout_file": "inbox-two.txt"}})
    argv = fill(block_for(_core(dist, profile, "task-handoff"), "task-handoff-resume"),
                dist / profile / "task-handoff", lane.project, profile)
    assert "--task-file" not in argv
    out = run_block(argv, lane.env)
    assert "2 unread" in out
    assert lane.verbs() == ["inbox"]


@pytest.mark.parametrize("profile", PROFILES)
def test_resume_with_own_task_file_writes_an_active_card(dist, lane, profile):
    lane.scenario_set({"inbox": {"stdout_file": "inbox-empty.txt"}})
    argv = fill(block_for(_core(dist, profile, "task-handoff"), "task-handoff-resume"),
                dist / profile / "task-handoff", lane.project, profile,
                window="w-1", task_file=lane.task_file())
    assert run_block(argv, lane.env) == ""
    assert lane.verbs() == ["inbox", "card show", "card set"]
    stored = lane.stored_card()
    assert stored["state"] == "active" and stored["host"] == profile


@pytest.mark.parametrize("profile", PROFILES)
def test_absent_interpreter_is_a_silent_skip(dist, lane, profile):
    skill, point = next((s, p) for s, ps in HOOKED.items() for p in ps)
    lane.scenario_set({"inbox": {"stdout_file": "inbox-two.txt"}})
    env = dict(lane.env)
    env["PATH"] = os.pathsep.join([str(lane.stub_dir), os.path.dirname(shutil.which("git"))])
    if shutil.which("python", path=env["PATH"]) is not None:
        pytest.fail("python unexpectedly resolves without its folder on PATH")
    argv = fill(block_for(_core(dist, profile, skill), point), dist / profile / skill,
                lane.project, profile, state=_state_for(point))
    assert run_block(argv, env) == ""
    assert lane.verbs() == []
    reference = (dist / profile / "_shared" / "lane-inbox-hooks.md").read_text(encoding="utf-8")
    assert "When no\n`python` resolves, the hook is skipped silently" in reference.replace(
        "\r\n", "\n")


# --------------------------------------------------------------------------- #
# Red-on-garbage anchor: a core without its block fails
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("skill,point,profile", _cases())
def test_anchor_core_without_block_fails(dist, skill, point, profile):
    core = _core(dist, profile, skill)
    stripped = MARKER_RE.sub("", core)
    with pytest.raises(AssertionError):
        block_for(stripped, point)


# --------------------------------------------------------------------------- #
# session-wrap (inbox hooks Step 4)
# --------------------------------------------------------------------------- #

def _section(core, start, end):
    a = core.index(start)
    b = core.index(end, a + len(start)) if end else len(core)
    return core[a:b]


@pytest.mark.parametrize("profile", PROFILES)
def test_session_wrap_continue_and_advise_make_no_call(dist, profile):
    core = _core(dist, profile, "session-wrap")
    continue_route = _section(core, "## Route: `continue`", "## Route: `clear-next`")
    advise = _section(core, "## `--advise`", "## Maintenance")
    for text in (continue_route, advise):
        assert "lane-inbox" not in text and "lane_inbox" not in text
    assert extract_blocks(core) == {"session-wrap-wrap": block_for(core, "session-wrap-wrap")}
    clear_next = _section(core, "## Route: `clear-next`", "## Route: `end-window`")
    assert "lane-inbox-call: session-wrap-wrap" in clear_next


@pytest.mark.parametrize("profile", PROFILES)
def test_session_wrap_line_rides_the_digest_flag_line(dist, profile):
    core = _core(dist, profile, "session-wrap")
    assert "rides the digest's invariant-flags line as one more flag" in core
    assert "never a new digest line, so the digest keeps its <=6-line cap" in core
    assert "<digest: <=6 lines>" in core
    assert "`[lane-inbox]` line of a lane window" in core


@pytest.mark.parametrize("route,state", [("clear-next", "waiting"), ("end-window", "idle")])
@pytest.mark.parametrize("profile", PROFILES)
def test_session_wrap_routes_write_their_card_state_and_one_flag(dist, lane, profile, route,
                                                                 state):
    lane.scenario_set({"inbox": {"stdout_file": "inbox-five.txt"}})
    argv = fill(block_for(_core(dist, profile, "session-wrap"), "session-wrap-wrap"),
                dist / profile / "session-wrap", lane.project, profile, window="wrap-w",
                task_file=lane.task_file(), state=_state_for("session-wrap-wrap", route))
    out = run_block(argv, lane.env)
    # One flag line (the digest's 6-line cap holds: the hook adds no line of its own).
    assert out.count("\n") == 1 and len(out.encode("utf-8")) <= 2048
    assert out.startswith("[lane-inbox] art-lane@demo-proj: 5 unread ")
    assert lane.verbs() == ["inbox", "card show", "card set"]
    assert lane.stored_card()["state"] == state
    assert lane.stored_card()["next_checkpoint"] == "/build-step --problem next"


@pytest.mark.parametrize("profile", PROFILES)
def test_clear_next_then_fresh_window_resume_replaces_the_card(dist, lane, profile):
    lane.scenario_set({"inbox": {"stdout_file": "inbox-empty.txt"}})
    wrap = fill(block_for(_core(dist, profile, "session-wrap"), "session-wrap-wrap"),
                dist / profile / "session-wrap", lane.project, profile, window="old-window",
                task_file=lane.task_file(), state="waiting")
    assert run_block(wrap, lane.env) == ""
    assert lane.stored_card()["state"] == "waiting"
    resume = fill(block_for(_core(dist, profile, "task-handoff"), "task-handoff-resume"),
                  dist / profile / "task-handoff", lane.project, profile, window="new-window",
                  task_file=lane.task_file(name="new-window.md"))
    out = run_block(resume, lane.env)
    assert "card-held-by-another-window" not in out
    stored = lane.stored_card()
    assert stored["state"] == "active" and stored["window"] == "new-window"


@pytest.mark.parametrize("profile", PROFILES)
def test_session_wrap_tells_a_delegated_repo_update_it_is_nested(dist, profile):
    core = _core(dist, profile, "session-wrap")
    router = _section(core, "## Git-verb router", "## Rendering contract")
    assert "adds\n  `--nested` and prints nothing" in router.replace("\r\n", "\n")
