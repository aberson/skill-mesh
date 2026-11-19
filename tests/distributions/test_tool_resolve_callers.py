"""Companion tool resolution: wiring and production-caller tests (V4-10 core companion plan Step 5).

The producers are the call sites that run drift-ranger and switchboard: the shared
`intent-continuity.md`, and the `review-deep`, `review-gauntlet` and `tier-offload` cores,
plus (the Step 5 follow-up) the inert `context-slim` classifier offload and the documented,
not-wired `skill-evolve` and `skill-iterate` grader call shapes.
The consumer is the real resolver, `_shared/tool_resolve.py`. A unit test of the resolver
cannot see a core that still calls a checkout, so these tests build the real Claude and
Codex profiles with `tools/build-distributions.ps1`, extract each call site's marked block
(`tool-resolve-call: <point>`) from the EMITTED text, run its resolver line with the shipped
resolver, then run its call line with the resolved `argv` against fake tools that really
execute (never the real tools, no network). Three fixtures per call site: the tool (a) on
PATH, (b) only in a `DEV_UTILITIES_ROOT` checkout, (c) absent.
"""

from __future__ import annotations

import io
import json
import os
import re
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "tools" / "build-distributions.ps1"
LANE_FIXTURES = REPO_ROOT / "_shared" / "fixtures" / "lane-inbox"
if str(LANE_FIXTURES) not in sys.path:
    sys.path.insert(0, str(LANE_FIXTURES))

import stub_support  # noqa: E402

PWSH = "powershell"
PROFILES = ("claude", "codex")
IS_WINDOWS = os.name == "nt"
RESOLVER = "tool_resolve.py"
# The convention is a coding-root document, not part of this package. The test holds only
# its leaf name and reads the cited path from the emitted payloads, so it asserts on what
# the payloads cite rather than carrying a host source path as code.
CONVENTION_LEAF = "advisory-call-convention.md"
CITATION_RE = re.compile(
    r"`([^`\s]*/references/" + re.escape(CONVENTION_LEAF) + r")` in the coding root, section 4")

# point -> (emitted file relative to the profile root, the skill whose directory fills
# <skill-dir>, the tool, the caller's documented absent outcome).
CALL_SITES = {
    "intent-continuity": ("_shared/intent-continuity.md", "build-step", "drift-ranger",
                          "means unavailable"),
    "review-deep-style": ("review-deep/core.md", "review-deep", "switchboard",
                          "is a **defer**"),
    "review-gauntlet-style": ("review-gauntlet/core.md", "review-gauntlet", "switchboard",
                              "is a `defer`, exactly as before"),
    "tier-offload-validate": ("tier-offload/core.md", "tier-offload", "switchboard",
                              "means validation is unavailable"),
    "context-slim-classifier": ("context-slim/SKILL.md", "context-slim", "switchboard",
                                "is a **defer**"),
    "skill-evolve-grader": ("skill-evolve/core.md", "skill-evolve", "switchboard",
                            "is a **defer**"),
    "skill-iterate-grader": ("skill-iterate/core.md", "skill-iterate", "switchboard",
                             "is a **defer**, so the normal grader is used"),
}
# context-slim is provider-native Claude-only (core: null), so only the Claude profile emits
# it. Declared, not discovered: a site that silently vanished from a profile must fail.
PROFILE_ONLY = {"context-slim-classifier": ("claude",)}
# Every core that follows the intent continuity contract reaches the drift-ranger site.
INTENT_CONSUMERS = ("build-phase", "build-queue", "build-step", "plan-feature", "plan-init",
                    "session-wrap", "task-handoff")
# The forms Step 5 retires. None may survive in an emitted caller.
RETIRED = ("python -m switchboard judge", "drift_ranger.py",
           "switchboard/switchboard/config.py")
# The retired judge form, matched across any whitespace and a versioned interpreter name.
# It targets `judge` only: tier-offload documents the checkout route
# `python -m switchboard config ...` deliberately, and that must not be flagged.
RETIRED_JUDGE_RE = re.compile(r"\bpython[0-9.]*\s+-m\s+switchboard\s+judge\b")

BLOCK_RE = re.compile(
    r"```text\r?\n[ \t]*tool-resolve-call: ([a-z0-9-]+)\r?\n"
    r"[ \t]*([^\r\n]+)\r?\n[ \t]*([^\r\n]+)\r?\n[ \t]*```")
CANNED = {"switchboard": '{"defer": true, "reason": "offload-off"}\n',
          "drift-ranger": "No projects.\n"}


# --------------------------------------------------------------------------- #
# Build and block extraction
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    out = tmp_path_factory.mktemp("resolve-dist")
    for profile in PROFILES:
        r = subprocess.run(
            [PWSH, "-NonInteractive", "-File", str(BUILD_SCRIPT),
             "-OutputDir", str(out), "-Provider", profile],
            capture_output=True, text=True)
        assert r.returncode == 0, "build failed:\n%s\n%s" % (r.stdout, r.stderr)
    return out


def _text(dist, profile, point):
    rel = CALL_SITES[point][0]
    return (dist / profile / rel).read_text(encoding="utf-8")


def extract_blocks(text):
    found = BLOCK_RE.findall(text)
    points = [p for p, _, _ in found]
    assert len(points) == len(set(points)), "a point is marked twice: %s" % points
    return {p: (resolve_line, call_line) for p, resolve_line, call_line in found}


def block_for(text, point):
    blocks = extract_blocks(text)
    assert point in blocks, "no tool-resolve-call block for %s" % point
    return blocks[point]


def cited_convention(text):
    """Return the one convention path a payload cites with its section 4, or fail."""
    cited = set(CITATION_RE.findall(" ".join(text.split())))
    assert len(cited) == 1, "expected one section 4 citation of %s, got %s" % (
        CONVENTION_LEAF, sorted(cited))
    return cited.pop()


def _cases():
    return [(point, profile) for point in CALL_SITES
            for profile in PROFILE_ONLY.get(point, PROFILES)]


def retired_forms_in(text):
    """Every retired form a payload text still carries (empty means clean)."""
    found = [form for form in ("drift_ranger.py", "switchboard/switchboard/config.py")
             if form in text]
    if RETIRED_JUDGE_RE.search(text):
        found.append("python -m switchboard judge")
    return found


# --------------------------------------------------------------------------- #
# Fake tools that really execute
# --------------------------------------------------------------------------- #

STUB_SOURCE = """import json, sys
with open(%(log)r, "a", encoding="utf-8") as handle:
    handle.write(json.dumps({"name": %(name)r, "argv": sys.argv[1:]}) + "\\n")
sys.stdout.write(%(out)r)
"""


def make_fake(folder, name, log, out):
    folder.mkdir(parents=True, exist_ok=True)
    source = (STUB_SOURCE % {"log": str(log), "name": name, "out": out}).encode("utf-8")
    if IS_WINDOWS:
        # The same real console launcher the lane inbox stub uses: the resolver accepts
        # only an .exe on Windows, and arguments reach the stub byte-for-byte.
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("__main__.py", source)
        path = folder / (name + ".exe")
        path.write_bytes(stub_support._launcher_bytes()
                         + ('#!"%s"\r\n' % sys.executable).encode("utf-8")
                         + buffer.getvalue())
        return path
    path = folder / name
    path.write_bytes(("#!%s\n" % sys.executable).encode("utf-8") + source)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


class Fixture:
    """One of the three Done-when fixtures for one tool, with an isolated environment."""

    def __init__(self, tmp_path, kind, tool):
        self.kind = kind
        self.tool = tool
        self.log = tmp_path / "calls.jsonl"
        self.bin = tmp_path / "bin"
        self.bin.mkdir()
        home = tmp_path / "home"
        home.mkdir()
        self.checkout = None
        self.env = {k: v for k, v in os.environ.items() if k.upper() != "DEV_UTILITIES_ROOT"}
        self.env.update({
            # Only the fake tools and the interpreter: a real installed tool never leaks in.
            "PATH": os.pathsep.join([str(self.bin), os.path.dirname(sys.executable)]),
            "USERPROFILE": str(home), "HOME": str(home),
        })
        if kind == "path":
            self.command = make_fake(self.bin, tool, self.log, CANNED[tool])
        elif kind == "checkout":
            utils = tmp_path / "utils"
            self.checkout = utils / tool
            self.checkout.mkdir(parents=True)
            (self.checkout / "pyproject.toml").write_text(
                "[project]\nname = '%s'\n" % tool, encoding="utf-8")
            self.command = make_fake(self.bin, "uv", self.log, CANNED[tool])
            self.env["DEV_UTILITIES_ROOT"] = str(utils)
        else:
            self.command = None

    def calls(self):
        if not self.log.is_file():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]


def fill_resolve(line, skill_dir):
    argv = line.replace("<skill-dir>", str(skill_dir)).split()
    assert argv[:2] == ["python", "-B"]
    assert "<" not in " ".join(argv), "unfilled placeholder in %s" % line
    return argv


def fill_call(line, resolved_argv, values):
    tokens = line.split()
    assert tokens[0] == "<argv>", line
    out = list(resolved_argv)
    for token in tokens[1:]:
        token = token.strip('"')
        token = values.get(token, token)
        assert not token.startswith("<"), "unfilled placeholder %s" % token
        out.append(token)
    return out, [values.get(t.strip('"'), t.strip('"')) for t in tokens[1:]]


def run_resolver(argv, env):
    """Run the resolver line as a host does. stdin stays open and unwritten: never a block."""
    proc = subprocess.Popen([sys.executable] + argv[1:], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        proc.wait(timeout=60)
        out = proc.stdout.read().decode("utf-8")
        err = proc.stderr.read().decode("utf-8")
    finally:
        proc.stdin.close()
        if proc.poll() is None:
            proc.kill()
    assert proc.returncode == 0
    assert err == ""
    return out


# --------------------------------------------------------------------------- #
# The emitted payloads carry the new order and every cited path resolves
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("profile", PROFILES)
def test_resolver_ships_in_each_profile_byte_for_byte(dist, profile):
    shipped = (dist / profile / "_shared" / RESOLVER).read_text(encoding="utf-8")
    canonical = (REPO_ROOT / "_shared" / RESOLVER).read_text(encoding="utf-8")
    # The builder stamps its provenance header inside the module docstring, so compare
    # from the first import on: the code must ship byte-for-byte.
    body = canonical.replace("\r\n", "\n")
    assert body[body.index("import argparse"):] in shipped.replace("\r\n", "\n")
    # The shipped resolver states the convention's order: PATH, then checkout, then nothing.
    flat = shipped.replace("\r\n", "\n")
    first = flat.index("1. The tool's own command on PATH")
    second = flat.index("2. Else, when DEV_UTILITIES_ROOT")
    third = flat.index("3. Else nothing")
    assert first < second < third
    assert cited_convention(flat).endswith("/references/" + CONVENTION_LEAF)


@pytest.mark.parametrize("point,profile", _cases())
def test_emitted_caller_carries_the_block_and_its_paths_resolve(dist, point, profile):
    rel, skill, tool, _absent = CALL_SITES[point]
    text = _text(dist, profile, point)
    resolve_line, call_line = block_for(text, point)
    assert resolve_line == (
        "python -B <skill-dir>/../_shared/tool_resolve.py resolve --tool %s" % tool)
    assert call_line.startswith("<argv> ")
    skill_dir = dist / profile / skill
    # <skill-dir> is the directory of the loaded file: the core, or for a provider-native
    # skill (no core) its emitted SKILL.md.
    loaded = "SKILL.md" if rel.endswith("/SKILL.md") else "core.md"
    assert (skill_dir / loaded).is_file()
    assert (skill_dir / ".." / "_shared" / RESOLVER).resolve().is_file()
    # The caller cites the convention (its section 4 owns the order) and restates none of it.
    # It cites the very path the shipped resolver cites, so callers and resolver name
    # one owner.
    resolver = (dist / profile / "_shared" / RESOLVER).read_text(encoding="utf-8")
    assert cited_convention(text) == cited_convention(resolver)
    assert "uv run --project" not in text and "DEV_UTILITIES_ROOT" not in text
    for retired in RETIRED:
        assert retired not in text, (point, retired)


@pytest.mark.parametrize("profile", PROFILES)
def test_every_intent_continuity_consumer_reaches_the_drift_ranger_site(dist, profile):
    for skill in INTENT_CONSUMERS:
        core = (dist / profile / skill / "core.md").read_text(encoding="utf-8")
        assert "../_shared/intent-continuity.md" in core, skill
        assert (dist / profile / skill / ".." / "_shared" /
                "intent-continuity.md").resolve().is_file()


def test_profile_only_sites_are_absent_from_the_other_profiles(dist):
    for point, profiles in PROFILE_ONLY.items():
        skill = CALL_SITES[point][1]
        for profile in PROFILES:
            assert (dist / profile / skill).is_dir() == (profile in profiles), (point, profile)


@pytest.mark.parametrize("profile", PROFILES)
def test_no_emitted_skill_still_runs_a_retired_form(dist, profile):
    root = dist / profile
    scanned = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_bytes().decode("utf-8", errors="replace")
        scanned += 1
        assert retired_forms_in(text) == [], (path, retired_forms_in(text))
    assert scanned > 0
    for skill in ("review-deep", "review-gauntlet"):
        core = (root / skill / "core.md").read_text(encoding="utf-8")
        assert "python -m switchboard" not in core, skill


# --------------------------------------------------------------------------- #
# The production-caller round trip: (a) on PATH, (b) checkout only, (c) absent
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("kind", ["path", "checkout", "absent"])
@pytest.mark.parametrize("point,profile", _cases())
def test_block_round_trip(dist, tmp_path, point, profile, kind):
    rel, skill, tool, absent_phrase = CALL_SITES[point]
    text = _text(dist, profile, point)
    resolve_line, call_line = block_for(text, point)
    fx = Fixture(tmp_path, kind, tool)

    out = run_resolver(fill_resolve(resolve_line, dist / profile / skill), fx.env)
    lines = out.splitlines()
    assert len(lines) <= 1, out

    if kind == "absent":
        # Nothing printed, nothing spawned, and the caller documents what absence means.
        assert out == ""
        assert fx.calls() == []
        assert absent_phrase in " ".join(text.split()), (point, absent_phrase)
        return

    record = json.loads(lines[0])
    assert record["tool"] == tool and record["via"] == kind
    if kind == "path":
        assert record["argv"] == [str(fx.command)]
    else:
        assert record["checkout"] == str(fx.checkout)
        assert record["argv"] == [str(fx.command), "run", "--project", str(fx.checkout), tool]

    prompt = tmp_path / "prompt.txt"
    prompt.write_text("judge this\n", encoding="utf-8")
    values = {"<style-lens-prompt-file>": str(prompt),
              "<absolute-config-path>": str(tmp_path / "offload-config.json"),
              "<section-prompt-file>": str(prompt),
              "<grading-prompt-file>": str(prompt),
              "<project-id>": "demo-project"}
    argv, call_args = fill_call(call_line, record["argv"], values)
    r = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                       env=fx.env, timeout=60)
    assert r.returncode == 0, r.stderr
    # At most one line reaches the caller: the tool's own one-line answer.
    assert r.stdout == CANNED[tool]
    (call,) = fx.calls()
    if kind == "path":
        assert call == {"name": tool, "argv": call_args}
    else:
        assert call == {"name": "uv",
                        "argv": ["run", "--project", str(fx.checkout), tool] + call_args}


# --------------------------------------------------------------------------- #
# Red-on-garbage anchors
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("point,profile", _cases())
def test_anchor_caller_without_block_fails(dist, point, profile):
    stripped = BLOCK_RE.sub("", _text(dist, profile, point))
    with pytest.raises(AssertionError):
        block_for(stripped, point)


@pytest.mark.parametrize("point,profile", _cases())
def test_anchor_caller_without_the_convention_citation_fails(dist, point, profile):
    text = _text(dist, profile, point)
    cited = cited_convention(text)
    # Drop the citation, or cite a different section: neither may pass.
    for garbage in (text.replace(cited, "the convention"),
                    " ".join(text.split()).replace("in the coding root, section 4",
                                                   "in the coding root, section 2")):
        with pytest.raises(AssertionError):
            cited_convention(garbage)


@pytest.mark.parametrize("garbage", [
    "python -m switchboard judge --site context-slim-classifier --prompt-file p",
    "`python  -m\n  switchboard judge --site skill-evolve-grader`",
    "python3 -m switchboard judge --site skill-iterate-grader",
])
@pytest.mark.parametrize("point,profile", _cases())
def test_anchor_sweep_flags_a_payload_with_the_retired_judge_form(dist, point, profile,
                                                                  garbage):
    text = _text(dist, profile, point)
    assert retired_forms_in(text) == []
    assert retired_forms_in(text + "\n" + garbage + "\n") == ["python -m switchboard judge"]


def test_anchor_sweep_spares_the_documented_config_route(dist):
    """The check is precise: tier-offload's documented checkout config route stays legal."""
    text = _text(dist, "claude", "tier-offload-validate")
    assert "python -m switchboard config" in text
    assert retired_forms_in(text) == []


def test_anchor_a_checkout_only_resolver_fails_the_path_fixture(dist, tmp_path):
    """A resolver that skipped PATH (the old checkout-only shape) must not pass."""
    fx = Fixture(tmp_path, "path", "switchboard")
    fx.env["DEV_UTILITIES_ROOT"] = str(tmp_path / "nowhere")
    resolve_line, _ = block_for(_text(dist, "claude", "review-deep-style"), "review-deep-style")
    argv = fill_resolve(resolve_line, dist / "claude" / "review-deep")
    assert json.loads(run_resolver(argv, fx.env))["via"] == "path"
    # The same fixture with the PATH entry removed resolves nothing: the PATH step is real.
    fx.env["PATH"] = os.path.dirname(sys.executable)
    assert run_resolver(argv, fx.env) == ""
