"""Unit tests for the companion tool resolver beside this file (`tool_resolve.py`).

The resolver is file lookups only, so most tests run it in process against a
temporary PATH, user profile and DEV_UTILITIES_ROOT made of plain files. The
end-to-end runs through the emitted skill cores, with fake tools that really
execute, live in `tests/distributions/test_tool_resolve_callers.py`.

Runs under pytest. Sibling import, as the other `_shared/` tests do.
"""

from __future__ import annotations

import ast
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import tool_resolve as tr  # noqa: E402

HELPER = THIS_DIR / "tool_resolve.py"
IS_WINDOWS = os.name == "nt"


def _make_command(folder: Path, name: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (name + ".exe" if IS_WINDOWS else name)
    path.write_bytes(b"fake")
    if not IS_WINDOWS:
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


class Env:
    def __init__(self, tmp_path, monkeypatch):
        self.tmp = tmp_path
        self.bin = tmp_path / "bin"
        self.bin.mkdir()
        self.home = tmp_path / "home"
        self.home.mkdir()
        self.utils = tmp_path / "utils"
        self.utils.mkdir()
        self.monkeypatch = monkeypatch
        monkeypatch.setenv("PATH", str(self.bin))
        monkeypatch.setenv("USERPROFILE", str(self.home))
        monkeypatch.setenv("HOME", str(self.home))
        monkeypatch.delenv(tr.ROOT_VARIABLE, raising=False)

    def checkout(self, slug, pyproject=True):
        folder = self.utils / slug
        folder.mkdir()
        if pyproject:
            (folder / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
        self.monkeypatch.setenv(tr.ROOT_VARIABLE, str(self.utils))
        return folder


@pytest.fixture
def env(tmp_path, monkeypatch):
    return Env(tmp_path, monkeypatch)


# --------------------------------------------------------------------------- #
# Step 1: the command on PATH, else the user uv tool bin directory
# --------------------------------------------------------------------------- #

def test_command_on_path_resolves_first(env):
    command = _make_command(env.bin, "switchboard")
    assert tr.resolve("switchboard") == {
        "tool": "switchboard", "via": "path", "argv": [str(command)]}


def test_command_in_user_bin_directory_when_path_is_stale(env):
    command = _make_command(env.home / ".local" / "bin", "drift-ranger")
    assert tr.resolve("drift-ranger") == {
        "tool": "drift-ranger", "via": "path", "argv": [str(command)]}


def test_path_beats_checkout(env):
    command = _make_command(env.bin, "switchboard")
    _make_command(env.bin, "uv")
    env.checkout("switchboard")
    assert tr.resolve("switchboard")["argv"] == [str(command)]


def test_relative_path_entries_are_ignored(env, monkeypatch):
    _make_command(env.bin, "switchboard")
    monkeypatch.chdir(env.tmp)
    monkeypatch.setenv("PATH", "bin")
    assert tr.resolve("switchboard") is None


@pytest.mark.skipif(not IS_WINDOWS, reason="drive-less rooted paths are a Windows shape")
def test_windows_drive_less_rooted_entries_are_ignored(env, monkeypatch):
    _make_command(env.bin, "switchboard")
    _make_command(env.bin, "uv")
    env.checkout("switchboard")
    drive, rest = os.path.splitdrive(str(env.bin))
    assert drive and rest.startswith("\\")
    monkeypatch.chdir(env.tmp)
    monkeypatch.setenv("PATH", rest)
    monkeypatch.setenv(tr.ROOT_VARIABLE, os.path.splitdrive(str(env.utils))[1])
    assert tr.resolve("switchboard") is None
    # Red-on-garbage anchor: the same folders with their drive resolve.
    monkeypatch.setenv("PATH", str(env.bin))
    assert tr.resolve("switchboard")["via"] == "path"


@pytest.mark.skipif(not IS_WINDOWS, reason="Windows accepts only an .exe")
def test_windows_cmd_and_bat_shims_count_as_absent(env):
    for suffix in (".cmd", ".bat", ""):
        (env.bin / ("switchboard" + suffix)).write_text("@echo off\n", encoding="utf-8")
    assert tr.resolve("switchboard") is None


@pytest.mark.skipif(IS_WINDOWS, reason="POSIX needs the executable bit")
def test_posix_file_without_exec_bit_counts_as_absent(env):
    (env.bin / "switchboard").write_text("#!/bin/sh\n", encoding="utf-8")
    assert tr.resolve("switchboard") is None


def test_directory_named_like_the_command_is_not_a_command(env):
    (env.bin / ("switchboard.exe" if IS_WINDOWS else "switchboard")).mkdir()
    assert tr.resolve("switchboard") is None


# --------------------------------------------------------------------------- #
# Step 2: the DEV_UTILITIES_ROOT checkout through uv run --project
# --------------------------------------------------------------------------- #

def test_checkout_resolves_through_uv_run_project(env):
    uv = _make_command(env.bin, "uv")
    folder = env.checkout("switchboard")
    assert tr.resolve("switchboard") == {
        "tool": "switchboard", "via": "checkout", "checkout": str(folder),
        "argv": [str(uv), "run", "--project", str(folder), "switchboard"]}


def test_checkout_without_pyproject_is_absent(env):
    _make_command(env.bin, "uv")
    env.checkout("switchboard", pyproject=False)
    assert tr.resolve("switchboard") is None


def test_checkout_without_uv_is_absent(env):
    env.checkout("switchboard")
    assert tr.resolve("switchboard") is None


@pytest.mark.parametrize("value", ["", "   ", "utils", "./utils"])
def test_unset_empty_or_relative_root_is_absent(env, monkeypatch, value):
    _make_command(env.bin, "uv")
    env.checkout("switchboard")
    monkeypatch.chdir(env.tmp)
    monkeypatch.setenv(tr.ROOT_VARIABLE, value)
    assert tr.resolve("switchboard") is None


# --------------------------------------------------------------------------- #
# Step 3 and the edges: nothing printed
# --------------------------------------------------------------------------- #

def test_absent_everywhere_is_none(env):
    assert tr.resolve("switchboard") is None


@pytest.mark.parametrize("slug", ["", "Switchboard", "../switchboard", "a/b", "a\\b",
                                  "-x", "x-", "a" * 65, "switch board"])
def test_invalid_slug_never_looks_anything_up(env, slug):
    _make_command(env.bin, "uv")
    assert tr.resolve(slug) is None


@pytest.mark.parametrize("argv", [
    [], ["resolve"], ["resolve", "--tool"], ["run", "--tool", "switchboard"],
    ["--help"], ["resolve", "--tool", "switchboard", "--extra"],
])
def test_bad_arguments_print_nothing(env, argv):
    _make_command(env.bin, "switchboard")
    assert tr.run(argv) is None


def test_run_prints_one_sorted_json_line(env):
    command = _make_command(env.bin, "switchboard")
    line = tr.run(["resolve", "--tool", "switchboard"])
    assert "\n" not in line
    assert json.loads(line) == {"argv": [str(command)], "tool": "switchboard", "via": "path"}
    assert line.startswith('{"argv": ')


def test_internal_error_prints_nothing_and_exits_zero(env, monkeypatch, capsys):
    def boom(_slug):
        raise RuntimeError("unexpected")
    monkeypatch.setattr(tr, "resolve", boom)
    assert tr.main(["resolve", "--tool", "switchboard"]) == 0
    assert capsys.readouterr() == ("", "")


# --------------------------------------------------------------------------- #
# The real script: one process, at most one line, exit 0, never reads stdin
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("fixture", ["path", "checkout", "absent"])
def test_script_prints_at_most_one_line_and_never_blocks(env, fixture):
    if fixture == "path":
        _make_command(env.bin, "switchboard")
    elif fixture == "checkout":
        _make_command(env.bin, "uv")
        env.checkout("switchboard")
    child_env = dict(os.environ)
    # stdin stays open and is never written: a resolver that read it would hang.
    proc = subprocess.Popen([sys.executable, "-B", str(HELPER), "resolve", "--tool",
                             "switchboard"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=child_env)
    try:
        proc.wait(timeout=30)
        out = proc.stdout.read().decode("utf-8")
        err = proc.stderr.read().decode("utf-8")
    finally:
        proc.stdin.close()
        if proc.poll() is None:
            proc.kill()
    assert proc.returncode == 0
    assert err == ""
    lines = out.splitlines()
    if fixture == "absent":
        assert lines == []
    else:
        assert len(lines) == 1 and json.loads(lines[0])["via"] == fixture


# --------------------------------------------------------------------------- #
# Source invariants
# --------------------------------------------------------------------------- #

def test_source_is_ascii_standard_library_and_spawns_nothing():
    source = HELPER.read_bytes()
    source.decode("ascii")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module.split(".")[0])
    assert imported <= {"argparse", "json", "os", "re", "sys"}
    for forbidden in ("subprocess", "os.system", "os.popen", "input(", "stdin"):
        assert forbidden not in source.decode("ascii").split('"""', 2)[2], forbidden


def test_docstring_states_the_order_path_then_checkout_then_nothing():
    doc = ast.get_docstring(ast.parse(HELPER.read_text(encoding="ascii")))
    first = doc.index("1. The tool's own command on PATH")
    second = doc.index("2. Else, when DEV_UTILITIES_ROOT")
    third = doc.index("3. Else nothing")
    assert first < second < third
    assert "uv run --project \"$DEV_UTILITIES_ROOT/<slug>\" <slug>" in doc
    assert "advisory-call-convention.md" in doc and "section 4" in doc
