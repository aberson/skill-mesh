"""Test support for the lane inbox hook: build a stub `passing-notes` executable.

On Windows the helper runs only a `.exe` resolution (a `.cmd` shim would pass its
arguments through cmd.exe), so the stub is a real console launcher: the standard
script launcher that ships inside CPython's bundled pip wheel (`ensurepip`), with a
shebang naming this interpreter and a zip holding the stub as `__main__.py`.
Arguments reach the stub byte-for-byte, exactly as with the uv-built real tool.
On other systems the stub is a shebang script with the executable bit.

Used by `_shared/` unit tests and by the integration tests under `tests/`.
"""

import glob
import io
import json
import os
import platform
import stat
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
STUB_SOURCE = os.path.join(HERE, "stub_passing_notes.py")


def _launcher_bytes():
    machine = platform.machine().lower()
    name = "t64-arm.exe" if machine in ("arm64", "aarch64") else "t64.exe"
    try:
        import pip._vendor.distlib as distlib  # noqa: F401
        path = os.path.join(os.path.dirname(distlib.__file__), name)
        if os.path.isfile(path):
            with open(path, "rb") as handle:
                return handle.read()
    except Exception:
        pass
    import ensurepip
    wheels = glob.glob(os.path.join(os.path.dirname(ensurepip.__file__), "_bundled", "pip-*.whl"))
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as archive:
            member = "pip/_vendor/distlib/" + name
            if member in archive.namelist():
                return archive.read(member)
    raise RuntimeError(
        "no script launcher found (needs CPython's bundled pip wheel); "
        "the stub passing-notes executable cannot be built")


def make_stub_tool(folder):
    """Write a stub `passing-notes` into folder and return its path."""
    os.makedirs(folder, exist_ok=True)
    with open(STUB_SOURCE, "rb") as handle:
        source = handle.read()
    source = source.replace(b"HERE = os.path.dirname(os.path.abspath(__file__))",
                            ("HERE = %r" % HERE).encode("utf-8"))
    if os.name == "nt":
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("__main__.py", source)
        shebang = ('#!"%s"\r\n' % sys.executable).encode("utf-8")
        path = os.path.join(folder, "passing-notes.exe")
        with open(path, "wb") as handle:
            handle.write(_launcher_bytes() + shebang + buffer.getvalue())
        return path
    path = os.path.join(folder, "passing-notes")
    with open(path, "wb") as handle:
        handle.write(("#!%s\n" % sys.executable).encode("utf-8") + source)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def write_scenario(path, scenario):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(scenario, handle)


def read_log(path):
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def fixture_text(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as handle:
        return handle.read()
