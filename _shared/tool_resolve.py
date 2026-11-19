"""Companion tool resolver: find an installed advisory tool, else its checkout, else nothing.

The resolution order is owned by the workspace's advisory-call convention
(`.claude/references/advisory-call-convention.md` in the coding root, section 4);
this module implements it for the Skill Mesh call sites that cite it:

    python -B tool_resolve.py resolve --tool <slug>

1. The tool's own command on PATH (absolute PATH entries only), else in the
   default user `uv tool` bin directory (the `.local/bin` folder of the user
   profile, stat-ed rather than asked of `uv`). On Windows only `<slug>.exe`
   counts: a `.bat` or `.cmd` shim would pass its arguments through cmd.exe.
2. Else, when DEV_UTILITIES_ROOT is set to an absolute path and
   `$DEV_UTILITIES_ROOT/<slug>/pyproject.toml` is a file, and `uv` itself
   resolves the same way as step 1: the command is
   `uv run --project "$DEV_UTILITIES_ROOT/<slug>" <slug>`.
3. Else nothing: no line.

Output is zero lines or exactly one JSON line,
`{"argv": [...], "tool": "<slug>", "via": "path" | "checkout"}` (a `checkout`
result also carries `"checkout": "<directory>"`). The caller runs `argv`
followed by its own call-site arguments. Resolution is file lookups only: it
spawns no process, reads no standard input, prompts for nothing, and always
exits 0, so it can never block or gate its caller. An absent tool, an invalid
argument or any internal error prints nothing. Standard library only, ASCII
source.
"""

import argparse
import json
import os
import re
import sys

SLUG_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
SLUG_MAX = 64
ROOT_VARIABLE = "DEV_UTILITIES_ROOT"
UV = "uv"

IS_WINDOWS = os.name == "nt"


class _Skip(Exception):
    """Nothing to print."""


def valid_slug(value):
    return bool(value) and len(value) <= SLUG_MAX and SLUG_RE.fullmatch(value) is not None


def command_file_names(name):
    return (name + ".exe",) if IS_WINDOWS else (name,)


def is_runnable(path):
    if not os.path.isfile(path):
        return False
    if IS_WINDOWS:
        return path.lower().endswith(".exe")
    return os.access(path, os.X_OK)


def is_absolute(path):
    """True for a fully qualified path. On Windows a drive-less rooted path such as
    a leading single backslash resolves against the current drive, so it needs a drive
    or UNC share too (Python before 3.13 calls it absolute)."""
    if not path or not os.path.isabs(path):
        return False
    return not IS_WINDOWS or bool(os.path.splitdrive(path)[0])


def user_bin_dir():
    home = os.environ.get("USERPROFILE") if IS_WINDOWS else os.environ.get("HOME")
    if not is_absolute(home):
        return None
    return os.path.join(home, ".local", "bin")


def search_dirs():
    dirs = []
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        entry = entry.strip().strip('"')
        if is_absolute(entry):
            dirs.append(entry)
    extra = user_bin_dir()
    if extra:
        dirs.append(extra)
    return dirs


def find_command(name):
    """Step 1: the command's absolute path, or None. Lookups only."""
    for folder in search_dirs():
        for file_name in command_file_names(name):
            candidate = os.path.join(folder, file_name)
            if is_runnable(candidate):
                return candidate
    return None


def find_checkout(slug):
    """Step 2's directory: $DEV_UTILITIES_ROOT/<slug> holding a pyproject.toml, or None."""
    root = os.environ.get(ROOT_VARIABLE, "").strip().strip('"')
    if not is_absolute(root):
        return None
    checkout = os.path.join(root, slug)
    if not os.path.isfile(os.path.join(checkout, "pyproject.toml")):
        return None
    return checkout


def resolve(slug):
    """The resolution record for slug, or None when the tool is absent."""
    if not valid_slug(slug):
        return None
    command = find_command(slug)
    if command is not None:
        return {"tool": slug, "via": "path", "argv": [command]}
    checkout = find_checkout(slug)
    if checkout is None:
        return None
    uv = find_command(UV)
    if uv is None:
        return None
    return {
        "tool": slug,
        "via": "checkout",
        "checkout": checkout,
        "argv": [uv, "run", "--project", checkout, slug],
    }


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise _Skip()

    def exit(self, status=0, message=None):
        raise _Skip()


def build_parser():
    parser = _Parser(prog="tool_resolve.py", add_help=False)
    parser.add_argument("command", choices=("resolve",))
    parser.add_argument("--tool", required=True)
    return parser


def run(argv):
    """The one line to print, or None."""
    try:
        args = build_parser().parse_args(argv)
    except _Skip:
        return None
    record = resolve(args.tool)
    if record is None:
        return None
    return json.dumps(record, sort_keys=True, ensure_ascii=True)


def main(argv=None):
    try:
        line = run(sys.argv[1:] if argv is None else argv)
    except Exception:
        line = None
    if line:
        try:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
