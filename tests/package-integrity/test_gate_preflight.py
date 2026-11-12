"""Unit tests for tools/gate_preflight.py, the machine check before the full gate.

Probes are injected except in the two real-machine tests at the end. Those assert
only what this test controls (a probe result's shape, and a child process this
test started), never the machine's free memory or which other pytest processes
happen to be running.
"""

from __future__ import annotations

import importlib.util
import io
import os
import re
import signal
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "tools" / "gate_preflight.py"
SPEC = importlib.util.spec_from_file_location("gate_preflight", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
gp = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gp
SPEC.loader.exec_module(gp)

P = gp.ProcessInfo
SELF = 500


def _run(memory_mb, processes, self_pid=SELF):
    buf = io.StringIO()
    code = gp.main([], memory_probe=lambda: memory_mb, process_probe=lambda: list(processes),
                   self_pid=self_pid, out=buf)
    return code, buf.getvalue()


def _quiet_machine():
    return [P(4, 0, "System"), P(100, 4, "explorer.exe"), P(SELF, 100, "python tools/gate_preflight.py")]


def test_approves_a_quiet_machine_and_prints_both_numbers():
    code, out = _run(4096, _quiet_machine())
    assert code == gp.EXIT_APPROVED == 0
    assert "gate-preflight: available_memory_mb=4096 other_pytest_processes=0" in out
    assert "APPROVED" in out and "REFUSED" not in out


def test_threshold_is_2048_mb_inclusive():
    assert gp.MIN_AVAILABLE_MB == 2048
    assert _run(2048, _quiet_machine())[0] == gp.EXIT_APPROVED
    code, out = _run(2047, _quiet_machine())
    assert code == gp.EXIT_REFUSED == 3
    assert "gate-preflight: REFUSED -- available memory 2047 MB is under 2048 MB" in out
    assert "available_memory_mb=2047" in out


def test_refuses_when_another_pytest_is_running():
    procs = _quiet_machine() + [P(900, 100, '"C:\\venv\\Scripts\\python.exe" -m pytest tests/')]
    code, out = _run(8192, procs)
    assert code == gp.EXIT_REFUSED
    assert "other_pytest_processes=1" in out
    assert "gate-preflight: REFUSED -- 1 other pytest process(es) running (pids 900)" in out


def test_both_reasons_are_reported_together():
    procs = _quiet_machine() + [P(901, 100, "pytest.exe -q"), P(902, 901, "python.exe pytest.exe -q")]
    code, out = _run(1000, procs)
    assert code == gp.EXIT_REFUSED
    assert "available_memory_mb=1000 other_pytest_processes=2" in out
    assert out.count("REFUSED --") == 2


def test_own_process_tree_is_excluded():
    # An ancestor pytest (this tool launched from inside a test run), the tool itself,
    # and a descendant are all this run's own tree; only the unrelated one counts.
    procs = [
        P(4, 0, "System"),
        P(10, 4, "python -m pytest tests/package-integrity"),
        P(SELF, 10, "python -m pytest -k preflight"),
        P(600, SELF, "powershell -Command py.test --version"),
        P(700, 4, "C:\\other\\.venv\\Scripts\\pytest.exe bridge/tests"),
    ]
    code, out = _run(4096, procs)
    assert code == gp.EXIT_REFUSED
    assert "other_pytest_processes=1" in out
    assert "(pids 700)" in out


def test_parent_cycle_does_not_hang():
    procs = [P(SELF, 501, "a"), P(501, SELF, "b"), P(800, 4, "python -m pytest")]
    assert [p.pid for p in gp.other_pytest_processes(SELF, procs)] == [800]


@pytest.mark.parametrize("cmd, expected", [
    ("python -m pytest", True),
    ('"C:\\x\\.venv\\Scripts\\pytest.exe" -q -p no:cacheprovider', True),
    ("py.test tests", True),
    ("PYTEST.EXE", True),
    ("python -m pip install requests", False),
    ("notepad.exe pytest_notes.txt", False),
    ("python -m my-pytest-helper", False),
    ("", False),
])
def test_pytest_command_detection(cmd, expected):
    assert gp.is_pytest_command(cmd) is expected


def test_unreadable_python_processes_refuse_and_other_unreadable_ones_do_not():
    # Command lines the probe cannot read come back empty. A python or pytest image
    # among them might be a pytest run, so it refuses; a system process does not.
    procs = _quiet_machine() + [
        P(950, 4, "", "python.exe"),
        P(951, 4, "", "csrss.exe"),
        P(952, 4, "  ", "pytest.exe"),
        P(953, SELF, "", "python.exe"),  # this run's own child: excluded
    ]
    code, out = _run(4096, procs)
    assert code == gp.EXIT_REFUSED
    assert "other_pytest_processes=0 unreadable_python_processes=2" in out
    assert ("gate-preflight: REFUSED -- 2 python process(es) whose command line could not be"
            " read, so they may be pytest runs (pids 950,952)") in out


def test_unreadable_non_python_processes_do_not_refuse():
    procs = _quiet_machine() + [P(951, 4, "", "csrss.exe"), P(954, 4, "", "MsMpEng.exe"),
                                P(955, 4, "", "")]
    code, out = _run(4096, procs)
    assert code == gp.EXIT_APPROVED
    assert "other_pytest_processes=0 unreadable_python_processes=0" in out


@pytest.mark.parametrize("name, command_line, expected", [
    ("python.exe", "", True),
    ("pythonw.exe", "", True),
    ("python3.14t.exe", "", True),
    ("PYTEST.EXE", "", True),
    ("py.test.exe", "", True),
    ("python.exe", "python tools/x.py", False),
    ("csrss.exe", "", False),
    ("py.exe", "", False),
    ("mypython.exe", "", False),
    ("", "", False),
])
def test_unreadable_python_detection(name, command_line, expected):
    assert gp.is_unreadable_python(P(1, 0, command_line, name)) is expected


def test_a_process_list_without_this_process_is_a_probe_failure():
    # A list that misses this process is partial, so its zero count proves nothing.
    code, out = _run(9999, [P(4, 0, "System"), P(100, 4, "explorer.exe")])
    assert code == gp.EXIT_PROBE_FAILED
    assert "gate-preflight: PROBE-FAILED -- own pid 500 is not in the process list" in out
    assert "APPROVED" not in out


def test_a_failed_probe_refuses_with_its_own_exit_code():
    def broken():
        raise gp.ProbeError("no CIM")
    buf = io.StringIO()
    code = gp.main([], memory_probe=lambda: 9999, process_probe=broken, self_pid=SELF, out=buf)
    assert code == gp.EXIT_PROBE_FAILED == 2
    assert "gate-preflight: PROBE-FAILED -- no CIM" in buf.getvalue()
    assert "REFUSED" in buf.getvalue()


def test_rejects_arguments():
    buf = io.StringIO()
    assert gp.main(["--force"], memory_probe=lambda: 9999, process_probe=lambda: [],
                   self_pid=SELF, out=buf) == gp.EXIT_PROBE_FAILED


def test_parse_process_json_accepts_one_object_or_an_array():
    one = '{"ProcessId":5,"ParentProcessId":4,"CommandLine":null}'
    assert gp.parse_process_json(one) == [P(5, 4, "")]
    many = '[{"ProcessId":5,"ParentProcessId":4,"CommandLine":"a"},{"ProcessId":4,"ParentProcessId":0}]'
    assert gp.parse_process_json(many) == [P(5, 4, "a"), P(4, 0, "")]
    named = '{"ProcessId":6,"ParentProcessId":4,"Name":"python.exe","CommandLine":null}'
    assert gp.parse_process_json(named) == [P(6, 4, "", "python.exe")]
    for bad in ("not json", '"text"', '[1]', '[{"CommandLine":"x"}]'):
        with pytest.raises(gp.ProbeError):
            gp.parse_process_json(bad)


@pytest.mark.skipif(os.name != "nt", reason="the memory probe is Windows-only")
def test_real_memory_probe_returns_a_positive_megabyte_count():
    # Shape only: the number itself is whatever this machine has right now.
    assert gp.available_memory_mb() > 0


# The launcher starts two sleeping children and exits, so their parent is gone and
# they are not in this run's own process tree, which the probe excludes. Holding the
# launcher's Popen object keeps its process handle open, so Windows cannot hand the
# launcher's pid to the probe's own PowerShell child while the probe runs.
_SLEEPER = "import time; time.sleep(120)"
_LAUNCHER = (
    "import subprocess, sys\n"
    "kw = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
    "named = subprocess.Popen([sys.executable, '-c', sys.argv[1], 'pytest', '-q'], **kw)\n"
    "plain = subprocess.Popen([sys.executable, '-c', sys.argv[1], 'notes.txt'], **kw)\n"
    "print(named.pid, plain.pid, flush=True)\n"
)


@pytest.mark.skipif(os.name != "nt", reason="the process probe is Windows-only")
def test_real_process_probe_detects_a_real_pytest_child():
    # Known-good anchor for the real probe: a process whose command line names pytest
    # is counted, and one that does not is not. Memory is injected so only the process
    # half decides; any other pytest run on the machine only adds pids.
    launcher = subprocess.Popen([sys.executable, "-c", _LAUNCHER, _SLEEPER],
                                stdout=subprocess.PIPE, text=True)
    started: list[int] = []
    try:
        printed, _ = launcher.communicate(timeout=60)
        started = [int(pid) for pid in printed.split()]
        named_pid, plain_pid = started

        seen: list = []

        def real_probe():
            seen[:] = gp.list_processes()
            return list(seen)

        buf = io.StringIO()
        code = gp.main([], memory_probe=lambda: gp.MIN_AVAILABLE_MB, process_probe=real_probe,
                       out=buf)
        out = buf.getvalue()
    finally:
        for pid in started:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass

    rows = {p.pid: p for p in seen}
    assert os.getpid() in rows, "the real probe did not list this process"
    assert named_pid in rows and plain_pid in rows, "the real probe missed a child it started"
    assert "pytest" in rows[named_pid].command_line
    assert gp.PYTHON_IMAGE_RE.match(rows[named_pid].name)
    assert code == gp.EXIT_REFUSED, out
    match = re.search(r"other pytest process\(es\) running \(pids ([\d,]+)\)", out)
    assert match, out
    reported = {int(pid) for pid in match.group(1).split(",")}
    assert named_pid in reported, out
    assert plain_pid not in reported, out
