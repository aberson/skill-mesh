"""Run one Windows process inside a kill-on-close Job Object.

The lifecycle runner sends one JSON request on stdin. Target stdout and stderr go
directly to create-new evidence files. This helper returns containment metadata
only; it never returns the child environment or command output.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
import subprocess
import sys
import time
from typing import Any


if os.name != "nt":
    raise SystemExit("job_process.py requires Windows")


HANDLE = wintypes.HANDLE
LPVOID = wintypes.LPVOID
SIZE_T = ctypes.c_size_t
ULONG_PTR = ctypes.c_size_t
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

CREATE_NEW = 1
OPEN_EXISTING = 3
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_ATTRIBUTE_NORMAL = 0x00000080
STARTF_USESTDHANDLES = 0x00000100
CREATE_SUSPENDED = 0x00000004
CREATE_NO_WINDOW = 0x08000000
EXTENDED_STARTUPINFO_PRESENT = 0x00080000
PROC_THREAD_ATTRIBUTE_HANDLE_LIST = 0x00020002
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION = 1
JOB_OBJECT_BASIC_PROCESS_ID_LIST = 3
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
ERROR_INSUFFICIENT_BUFFER = 122


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", LPVOID),
        ("bInheritHandle", wintypes.BOOL),
    ]


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(wintypes.BYTE)),
        ("hStdInput", HANDLE),
        ("hStdOutput", HANDLE),
        ("hStdError", HANDLE),
    ]


class STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [("StartupInfo", STARTUPINFOW), ("lpAttributeList", LPVOID)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", HANDLE),
        ("hThread", HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", SIZE_T),
        ("MaximumWorkingSetSize", SIZE_T),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ULONG_PTR),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", SIZE_T),
        ("JobMemoryLimit", SIZE_T),
        ("PeakProcessMemoryUsed", SIZE_T),
        ("PeakJobMemoryUsed", SIZE_T),
    ]


class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_longlong),
        ("TotalKernelTime", ctypes.c_longlong),
        ("ThisPeriodTotalUserTime", ctypes.c_longlong),
        ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
        ("TotalPageFaultCount", wintypes.DWORD),
        ("TotalProcesses", wintypes.DWORD),
        ("ActiveProcesses", wintypes.DWORD),
        ("TotalTerminatedProcesses", wintypes.DWORD),
    ]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.POINTER(SECURITY_ATTRIBUTES),
    wintypes.DWORD,
    wintypes.DWORD,
    HANDLE,
]
kernel32.CreateFileW.restype = HANDLE
kernel32.CreateJobObjectW.argtypes = [ctypes.POINTER(SECURITY_ATTRIBUTES), wintypes.LPCWSTR]
kernel32.CreateJobObjectW.restype = HANDLE
kernel32.SetInformationJobObject.argtypes = [HANDLE, ctypes.c_int, LPVOID, wintypes.DWORD]
kernel32.SetInformationJobObject.restype = wintypes.BOOL
kernel32.QueryInformationJobObject.argtypes = [
    HANDLE,
    ctypes.c_int,
    LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]
kernel32.QueryInformationJobObject.restype = wintypes.BOOL
kernel32.InitializeProcThreadAttributeList.argtypes = [LPVOID, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(SIZE_T)]
kernel32.InitializeProcThreadAttributeList.restype = wintypes.BOOL
kernel32.UpdateProcThreadAttribute.argtypes = [LPVOID, wintypes.DWORD, SIZE_T, LPVOID, SIZE_T, LPVOID, ctypes.POINTER(SIZE_T)]
kernel32.UpdateProcThreadAttribute.restype = wintypes.BOOL
kernel32.DeleteProcThreadAttributeList.argtypes = [LPVOID]
kernel32.DeleteProcThreadAttributeList.restype = None
kernel32.CreateProcessW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    ctypes.POINTER(SECURITY_ATTRIBUTES),
    ctypes.POINTER(SECURITY_ATTRIBUTES),
    wintypes.BOOL,
    wintypes.DWORD,
    LPVOID,
    wintypes.LPCWSTR,
    ctypes.POINTER(STARTUPINFOW),
    ctypes.POINTER(PROCESS_INFORMATION),
]
kernel32.CreateProcessW.restype = wintypes.BOOL
kernel32.AssignProcessToJobObject.argtypes = [HANDLE, HANDLE]
kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
kernel32.IsProcessInJob.argtypes = [HANDLE, HANDLE, ctypes.POINTER(wintypes.BOOL)]
kernel32.IsProcessInJob.restype = wintypes.BOOL
kernel32.ResumeThread.argtypes = [HANDLE]
kernel32.ResumeThread.restype = wintypes.DWORD
kernel32.WaitForSingleObject.argtypes = [HANDLE, wintypes.DWORD]
kernel32.WaitForSingleObject.restype = wintypes.DWORD
kernel32.GetExitCodeProcess.argtypes = [HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel32.GetExitCodeProcess.restype = wintypes.BOOL
kernel32.TerminateProcess.argtypes = [HANDLE, wintypes.UINT]
kernel32.TerminateProcess.restype = wintypes.BOOL
kernel32.TerminateJobObject.argtypes = [HANDLE, wintypes.UINT]
kernel32.TerminateJobObject.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


class ProtocolError(RuntimeError):
    pass


def _winerror(action: str) -> OSError:
    code = ctypes.get_last_error()
    return OSError(code, f"{action} failed", None, code)


def _close(handle: HANDLE | None) -> None:
    if handle and handle != INVALID_HANDLE_VALUE:
        kernel32.CloseHandle(handle)


def _request() -> dict[str, Any]:
    raw = sys.stdin.buffer.read().decode("utf-8-sig")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        prefix = ",".join(f"U+{ord(character):04X}" for character in raw[:4])
        raise ProtocolError(f"request is not valid JSON at {exc.pos}: {exc.msg}; prefix={prefix}") from exc
    except UnicodeError as exc:
        raise ProtocolError(f"request text encoding is invalid: {type(exc).__name__}") from exc
    expected = {"schema", "executable", "argv", "cwd", "timeout_ms", "stdout_path", "stderr_path"}
    if not isinstance(value, dict) or set(value) != expected or value.get("schema") != 1:
        raise ProtocolError("request shape is invalid")
    if not isinstance(value["argv"], list) or not all(isinstance(item, str) for item in value["argv"]):
        raise ProtocolError("argv must be a string array")
    for name in ("executable", "cwd", "stdout_path", "stderr_path"):
        if not isinstance(value[name], str) or not os.path.isabs(value[name]):
            raise ProtocolError(f"{name} must be an absolute path")
    if not os.path.isfile(value["executable"]):
        raise ProtocolError("executable is not a file")
    if not os.path.isdir(value["cwd"]):
        raise ProtocolError("cwd is not a directory")
    if os.path.normcase(value["stdout_path"]) == os.path.normcase(value["stderr_path"]):
        raise ProtocolError("stdout_path and stderr_path must differ")
    if type(value["timeout_ms"]) is not int or not 1_000 <= value["timeout_ms"] <= 900_000:
        raise ProtocolError("timeout_ms is outside the supported range")
    return value


def _open_inheritable(path: str, access: int, share: int, disposition: int) -> HANDLE:
    security = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), None, True)
    handle = kernel32.CreateFileW(path, access, share, ctypes.byref(security), disposition, FILE_ATTRIBUTE_NORMAL, None)
    if handle == INVALID_HANDLE_VALUE:
        raise _winerror("CreateFileW")
    return handle


def _active_count(job: HANDLE) -> int:
    info = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
    returned = wintypes.DWORD()
    if not kernel32.QueryInformationJobObject(
        job,
        JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION,
        ctypes.byref(info),
        ctypes.sizeof(info),
        ctypes.byref(returned),
    ):
        raise _winerror("QueryInformationJobObject(accounting)")
    return int(info.ActiveProcesses)


def _process_ids(job: HANDLE) -> list[int]:
    capacity = 64
    while capacity <= 65_536:
        size = ctypes.sizeof(wintypes.DWORD) * 2 + ctypes.sizeof(ULONG_PTR) * capacity
        buffer = ctypes.create_string_buffer(size)
        returned = wintypes.DWORD()
        if kernel32.QueryInformationJobObject(
            job,
            JOB_OBJECT_BASIC_PROCESS_ID_LIST,
            buffer,
            size,
            ctypes.byref(returned),
        ):
            count = wintypes.DWORD.from_buffer(buffer, ctypes.sizeof(wintypes.DWORD)).value
            offset = ctypes.sizeof(wintypes.DWORD) * 2
            return [int(ULONG_PTR.from_buffer(buffer, offset + index * ctypes.sizeof(ULONG_PTR)).value) for index in range(count)]
        if ctypes.get_last_error() != ERROR_INSUFFICIENT_BUFFER:
            raise _winerror("QueryInformationJobObject(process ids)")
        capacity *= 2
    raise ProtocolError("job process list exceeds the safety bound")


def _poll_empty(job: HANDLE, seconds: float = 10.0) -> bool:
    deadline = time.monotonic() + seconds
    while True:
        if _active_count(job) == 0:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.05)


def _remaining_after_drain(job: HANDLE, root_pid: int, seconds: float = 2.0) -> list[int]:
    deadline = time.monotonic() + seconds
    while True:
        remaining = sorted(pid for pid in _process_ids(job) if pid != root_pid)
        if not remaining or time.monotonic() >= deadline:
            return remaining
        time.sleep(0.05)


def _result_template() -> dict[str, Any]:
    return {
        "schema": 1,
        "status": "INCOMPLETE",
        "target_started": False,
        "assigned_before_resume": False,
        "root_pid": 0,
        "root_exit_code": None,
        "timed_out": False,
        "survivors_existed": False,
        "survivor_pids": [],
        "terminate_job_called": False,
        "job_empty_confirmed": False,
        "duration_seconds": 0.0,
        "stage": "request",
        "win32_error": 0,
    }


def _run(request: dict[str, Any]) -> tuple[dict[str, Any], int]:
    result = _result_template()
    started_at = time.monotonic()
    stdin_handle: HANDLE | None = None
    stdout_handle: HANDLE | None = None
    stderr_handle: HANDLE | None = None
    job_handle: HANDLE | None = None
    process_info = PROCESS_INFORMATION()
    process_created = False
    attribute_buffer: ctypes.Array[ctypes.c_char] | None = None
    attribute_initialized = False
    try:
        result["stage"] = "evidence-files"
        stdout_handle = _open_inheritable(request["stdout_path"], GENERIC_WRITE, FILE_SHARE_READ, CREATE_NEW)
        stderr_handle = _open_inheritable(request["stderr_path"], GENERIC_WRITE, FILE_SHARE_READ, CREATE_NEW)
        stdin_handle = _open_inheritable("NUL", GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, OPEN_EXISTING)

        result["stage"] = "job"
        job_handle = kernel32.CreateJobObjectW(None, None)
        if not job_handle:
            raise _winerror("CreateJobObjectW")
        limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            job_handle,
            JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            raise _winerror("SetInformationJobObject")

        result["stage"] = "attribute-list"
        attribute_size = SIZE_T()
        kernel32.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(attribute_size))
        if ctypes.get_last_error() != ERROR_INSUFFICIENT_BUFFER or attribute_size.value == 0:
            raise _winerror("InitializeProcThreadAttributeList(size)")
        attribute_buffer = ctypes.create_string_buffer(attribute_size.value)
        if not kernel32.InitializeProcThreadAttributeList(attribute_buffer, 1, 0, ctypes.byref(attribute_size)):
            raise _winerror("InitializeProcThreadAttributeList")
        attribute_initialized = True
        inherited_handles = (HANDLE * 3)(stdin_handle, stdout_handle, stderr_handle)
        if not kernel32.UpdateProcThreadAttribute(
            attribute_buffer,
            0,
            PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
            ctypes.cast(inherited_handles, LPVOID),
            ctypes.sizeof(inherited_handles),
            None,
            None,
        ):
            raise _winerror("UpdateProcThreadAttribute")

        startup = STARTUPINFOEXW()
        startup.StartupInfo.cb = ctypes.sizeof(startup)
        startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES
        startup.StartupInfo.hStdInput = stdin_handle
        startup.StartupInfo.hStdOutput = stdout_handle
        startup.StartupInfo.hStdError = stderr_handle
        startup.lpAttributeList = ctypes.cast(attribute_buffer, LPVOID)
        command_line = ctypes.create_unicode_buffer(
            subprocess.list2cmdline([request["executable"], *request["argv"]])
        )

        result["stage"] = "create-suspended"
        if not kernel32.CreateProcessW(
            request["executable"],
            command_line,
            None,
            None,
            True,
            CREATE_SUSPENDED | CREATE_NO_WINDOW | EXTENDED_STARTUPINFO_PRESENT,
            None,
            request["cwd"],
            ctypes.cast(ctypes.byref(startup), ctypes.POINTER(STARTUPINFOW)),
            ctypes.byref(process_info),
        ):
            raise _winerror("CreateProcessW")
        process_created = True
        result["root_pid"] = int(process_info.dwProcessId)
        _close(stdin_handle)
        _close(stdout_handle)
        _close(stderr_handle)
        stdin_handle = stdout_handle = stderr_handle = None

        result["stage"] = "assign"
        if not kernel32.AssignProcessToJobObject(job_handle, process_info.hProcess):
            raise _winerror("AssignProcessToJobObject")
        membership = wintypes.BOOL()
        if not kernel32.IsProcessInJob(process_info.hProcess, job_handle, ctypes.byref(membership)):
            raise _winerror("IsProcessInJob")
        if not membership.value:
            raise ProtocolError("suspended target is not in the new Job Object")
        result["assigned_before_resume"] = True

        result["stage"] = "resume"
        if kernel32.ResumeThread(process_info.hThread) == 0xFFFFFFFF:
            raise _winerror("ResumeThread")
        result["target_started"] = True
        _close(process_info.hThread)
        process_info.hThread = None

        result["stage"] = "wait-root"
        wait_result = kernel32.WaitForSingleObject(process_info.hProcess, request["timeout_ms"])
        if wait_result == WAIT_TIMEOUT:
            result["timed_out"] = True
            result["terminate_job_called"] = True
            if not kernel32.TerminateJobObject(job_handle, 124):
                raise _winerror("TerminateJobObject(timeout)")
        elif wait_result != WAIT_OBJECT_0:
            raise _winerror("WaitForSingleObject")
        else:
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(process_info.hProcess, ctypes.byref(exit_code)):
                raise _winerror("GetExitCodeProcess")
            result["root_exit_code"] = int(exit_code.value)
            survivors = _remaining_after_drain(job_handle, result["root_pid"])
            if survivors:
                result["survivors_existed"] = True
                result["survivor_pids"] = survivors
                result["terminate_job_called"] = True
                if not kernel32.TerminateJobObject(job_handle, 125):
                    raise _winerror("TerminateJobObject(survivors)")

        result["stage"] = "confirm-empty"
        result["job_empty_confirmed"] = _poll_empty(job_handle)
        result["status"] = "COMPLETE" if result["job_empty_confirmed"] else "INCOMPLETE"
        result["stage"] = "complete" if result["job_empty_confirmed"] else "job-not-empty"
        return result, 0 if result["job_empty_confirmed"] else 3
    except (OSError, ProtocolError) as exc:
        if isinstance(exc, OSError):
            result["win32_error"] = int(getattr(exc, "winerror", 0) or getattr(exc, "errno", 0) or 0)
        result["stage"] = f"error:{result['stage']}"
        if process_created:
            if job_handle and result["assigned_before_resume"]:
                result["terminate_job_called"] = True
                kernel32.TerminateJobObject(job_handle, 126)
                try:
                    result["job_empty_confirmed"] = _poll_empty(job_handle)
                except OSError:
                    result["job_empty_confirmed"] = False
            else:
                kernel32.TerminateProcess(process_info.hProcess, 126)
                result["job_empty_confirmed"] = kernel32.WaitForSingleObject(process_info.hProcess, 10_000) == WAIT_OBJECT_0
        else:
            result["job_empty_confirmed"] = True
        result["status"] = "PRESTART_FAILURE" if not result["target_started"] else "INCOMPLETE"
        return result, 2 if not result["target_started"] else 3
    finally:
        result["duration_seconds"] = round(time.monotonic() - started_at, 3)
        if attribute_initialized and attribute_buffer is not None:
            kernel32.DeleteProcThreadAttributeList(attribute_buffer)
        _close(process_info.hThread)
        _close(process_info.hProcess)
        _close(stdin_handle)
        _close(stdout_handle)
        _close(stderr_handle)
        _close(job_handle)


def main() -> int:
    result = _result_template()
    exit_code = 2
    started_at = time.monotonic()
    try:
        request = _request()
        result, exit_code = _run(request)
    except ProtocolError as exc:
        result["status"] = "PRESTART_FAILURE"
        result["stage"] = f"error:request:{exc}"
        result["job_empty_confirmed"] = True
    except Exception as exc:  # Fail closed on an unexpected helper defect.
        result["status"] = "INCOMPLETE"
        result["stage"] = "error:internal"
        result["win32_error"] = int(getattr(exc, "winerror", 0) or 0)
        exit_code = 3
    result["duration_seconds"] = round(time.monotonic() - started_at, 3)
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
