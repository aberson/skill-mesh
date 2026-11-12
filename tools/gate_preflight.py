"""Machine check before the full repo-root gate.

The repo-root ``python -m pytest`` gate runs for hours and shells out to
PowerShell for most of its tests. On a machine with little free memory, or
while another pytest run is competing for it, random subprocess tests go red
and pass again in isolation, so a red gate on such a machine is not evidence.
This tool refuses to approve a full gate under those conditions and prints the
two measured numbers so the gate record can carry them.

Exit codes: 0 approved, 3 refused, 2 a probe failed (also a refusal, because
an unmeasured machine is not approved).

Windows only, like the rest of this repository's tooling. Standard library only.
"""

from __future__ import annotations

import ctypes
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


MIN_AVAILABLE_MB = 2048

EXIT_APPROVED = 0
EXIT_PROBE_FAILED = 2
EXIT_REFUSED = 3

PREFIX = "gate-preflight:"

# A process counts as a pytest run when its command line names pytest as a
# word: `python -m pytest`, `pytest.exe`, `py.test`. `pytest_notes.txt` does not.
PYTEST_RE = re.compile(r"(?<![\w-])py\.?test(?![\w])", re.IGNORECASE)


class ProbeError(RuntimeError):
    """A machine measurement could not be taken."""


@dataclass(frozen=True)
class ProcessInfo:
    pid: int
    ppid: int
    command_line: str


def is_pytest_command(command_line: str) -> bool:
    return bool(command_line) and PYTEST_RE.search(command_line) is not None


def own_tree(self_pid: int, processes: Iterable[ProcessInfo]) -> set[int]:
    """This process, its ancestors, and its descendants."""
    procs = list(processes)
    parent = {p.pid: p.ppid for p in procs}
    tree = {self_pid}
    pid = self_pid
    while pid in parent and parent[pid] not in tree and parent[pid] != 0:
        pid = parent[pid]
        tree.add(pid)
    changed = True
    descendants = {self_pid}
    while changed:
        changed = False
        for p in procs:
            if p.ppid in descendants and p.pid not in descendants:
                descendants.add(p.pid)
                changed = True
    return tree | descendants


def other_pytest_processes(self_pid: int, processes: Iterable[ProcessInfo]) -> list[ProcessInfo]:
    procs = list(processes)
    mine = own_tree(self_pid, procs)
    return [p for p in procs if p.pid not in mine and is_pytest_command(p.command_line)]


# -- real probes (Windows) ---------------------------------------------------

class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def available_memory_mb() -> int:
    """Available physical memory in MB (the `\\Memory\\Available MBytes` figure)."""
    if os.name != "nt":
        raise ProbeError("memory probe is Windows-only")
    status = _MemoryStatusEx()
    status.dwLength = ctypes.sizeof(_MemoryStatusEx)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ProbeError("GlobalMemoryStatusEx failed")
    return int(status.ullAvailPhys // (1024 * 1024))


# The query deliberately does not contain the word it filters for, so the probe
# never counts itself (it is also excluded as a descendant).
_PROCESS_QUERY = (
    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
    "@(Get-CimInstance Win32_Process | "
    "Select-Object ProcessId,ParentProcessId,CommandLine) | ConvertTo-Json -Compress"
)


def parse_process_json(text: str) -> list[ProcessInfo]:
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise ProbeError(f"process list is not JSON: {exc}") from exc
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ProbeError("process list is not a JSON array")
    out = []
    for row in data:
        if not isinstance(row, dict):
            raise ProbeError("process row is not a JSON object")
        try:
            pid = int(row["ProcessId"])
            ppid = int(row.get("ParentProcessId") or 0)
        except (KeyError, TypeError, ValueError) as exc:
            raise ProbeError(f"process row has no usable ids: {exc}") from exc
        out.append(ProcessInfo(pid, ppid, str(row.get("CommandLine") or "")))
    return out


def list_processes() -> list[ProcessInfo]:
    if os.name != "nt":
        raise ProbeError("process probe is Windows-only")
    try:
        done = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", _PROCESS_QUERY],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProbeError(f"process probe did not run: {exc}") from exc
    if done.returncode != 0:
        raise ProbeError(f"process probe exited {done.returncode}: {done.stderr.strip()[:200]}")
    return parse_process_json(done.stdout)


# -- entry point -------------------------------------------------------------

def main(
    argv: Sequence[str] | None = None,
    *,
    memory_probe: Callable[[], int] = available_memory_mb,
    process_probe: Callable[[], list[ProcessInfo]] = list_processes,
    self_pid: int | None = None,
    out=None,
) -> int:
    out = out if out is not None else sys.stdout
    if argv:
        print(f"{PREFIX} takes no arguments", file=out)
        return EXIT_PROBE_FAILED
    pid = os.getpid() if self_pid is None else self_pid
    try:
        memory_mb = int(memory_probe())
        others = other_pytest_processes(pid, process_probe())
    except ProbeError as exc:
        print(f"{PREFIX} PROBE-FAILED -- {exc}", file=out)
        print(f"{PREFIX} REFUSED -- the machine could not be measured", file=out)
        return EXIT_PROBE_FAILED

    print(f"{PREFIX} available_memory_mb={memory_mb} other_pytest_processes={len(others)}", file=out)
    reasons = []
    if memory_mb < MIN_AVAILABLE_MB:
        reasons.append(f"available memory {memory_mb} MB is under {MIN_AVAILABLE_MB} MB")
    if others:
        pids = ",".join(str(p.pid) for p in sorted(others, key=lambda p: p.pid))
        reasons.append(f"{len(others)} other pytest process(es) running (pids {pids})")
    for reason in reasons:
        print(f"{PREFIX} REFUSED -- {reason}", file=out)
    if reasons:
        return EXIT_REFUSED
    print(f"{PREFIX} APPROVED -- full repo-root gate may start", file=out)
    return EXIT_APPROVED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
