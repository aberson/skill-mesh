"""Shared fixtures for tests/distributions/test_build_step_tree*.py.

Hermetic Git (GIT_CONFIG_GLOBAL -> a temp file, GIT_CONFIG_NOSYSTEM=1, local identity), the
platform temp directory redirected into tmp_path (TMP/TEMP/TMPDIR), real disposable repositories,
and real long-lived "owner" processes.

Owner approach (documented per the B-helper lane brief): subprocess-driven helper calls cannot be
given a real host ancestor in a test, and the helper deliberately has no CLI or environment
override for its owner.  Calls that must resolve an owner (``scope`` and ``recover --abandon``)
therefore run in-process through the library API ``main(argv, Context(owner_resolver=...))``,
with the owner set to a REAL sleeper process this module starts (its real PID and start time),
so liveness is real: killing the sleeper makes the run dead.  Every other call can also run as a
real CLI subprocess.  ``test_scope_without_host_ancestor_is_unavailable`` drives the real CLI
entry point with no host ancestor and asserts the fail-closed ``unavailable`` result.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import socket
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "skills" / "build-step" / "scripts" / "build_step_tree.py"
STATUSES = {"ok": 0, "halt": 1, "scope-escape": 2, "unavailable": 3}


def load_helper():
    name = "build_step_tree_under_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HELPER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses on 3.14 need the module registered first
    spec.loader.exec_module(module)
    return module


bst = load_helper()


def parse_one(stdout: str) -> dict:
    """Exactly one JSON object on one line, with a known status."""
    assert stdout.endswith("\n"), f"output must end with a newline: {stdout!r}"
    lines = stdout.splitlines()
    assert len(lines) == 1, f"expected exactly one line of output, got {len(lines)}: {stdout!r}"
    obj = json.loads(lines[0])
    assert isinstance(obj, dict)
    assert obj.get("status") in STATUSES, obj
    return obj


def git(cwd, *args, check=True, input=None) -> str:
    proc = subprocess.run(["git", *[str(a) for a in args]], cwd=str(cwd), capture_output=True,
                          input=input, stdin=None if input is not None else subprocess.DEVNULL)
    if check and proc.returncode != 0:
        raise AssertionError(f"git {args} failed: {proc.stderr.decode('utf-8', 'replace')}")
    return proc.stdout.decode("utf-8", "replace").strip()


def write(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode("utf-8")
    path.write_bytes(data)
    return path


def is_link(path) -> bool:
    """A symlink, or on Windows any reparse point (junction, directory symlink), never followed."""
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def make_dir_link(link: Path, target: Path) -> None:
    """A directory junction on Windows (what npm/pnpm links and `file:` deps create), else a symlink."""
    link.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        proc = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True,
                              stdin=subprocess.DEVNULL)
        assert proc.returncode == 0, proc.stderr
    else:
        os.symlink(target, link, target_is_directory=True)
    assert is_link(link)


def tree_bytes(root: Path) -> dict:
    """Every regular file under root (relative posix path -> bytes)."""
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def make_repo(root: Path, files: dict, *, autocrlf: bool = False, origin: bool = False) -> Path:
    root.mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Build Step Test")
    git(root, "config", "user.email", "build-step-test@example.invalid")
    git(root, "config", "core.autocrlf", "true" if autocrlf else "false")
    for rel, data in files.items():
        write(root / rel, data)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "baseline")
    if autocrlf:  # re-check out so the working tree holds the converted (CRLF) form
        for rel in files:
            (root / rel).unlink()
        git(root, "checkout", "--", ".")
    if origin:
        bare = root.parent / f"{root.name}-origin.git"
        git(root.parent, "init", "-q", "--bare", "-b", "main", bare.name)
        git(root, "remote", "add", "origin", bare.as_uri())
        git(root, "push", "-q", "-u", "origin", "main")
        git(root, "remote", "set-head", "origin", "main")
    return root


class Owner:
    """A real long-lived process standing in for the host agent process."""

    def __init__(self) -> None:
        self.proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(3600)"],
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
        ident = None
        for _ in range(100):
            ident = bst.process_identity(self.proc.pid)
            if ident:
                break
            time.sleep(0.02)
        assert ident, "sleeper identity unavailable"
        self.record = {"pid": ident["pid"], "start_time": ident["start_time"], "host": socket.gethostname(),
                       "exe": ident["exe"], "session_id": None}

    def kill(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=30)


class Env:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp = tmp_path
        self.temp = tmp_path / "temp"
        self.owners: list = []

    @property
    def root(self) -> Path:
        return self.temp / "skill-mesh"

    def owner(self) -> Owner:
        o = Owner()
        self.owners.append(o)
        return o

    def ctx(self, owner=None, *, clock_offset: float = 0.0, **kw):
        record = owner.record if isinstance(owner, Owner) else owner
        kw.setdefault("lock_poll_seconds", 0.05)
        return bst.Context(owner_resolver=lambda: dict(record) if record else None,
                           clock=lambda: time.time() + clock_offset, temp_root=str(self.temp), **kw)

    def call(self, ctx, *argv) -> dict:
        """In-process call through main(): asserts exactly one JSON object and its exit code."""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = bst.main([str(a) for a in argv], ctx)
        obj = parse_one(buf.getvalue())
        assert rc == STATUSES[obj["status"]], (rc, obj)
        return obj

    def cli(self, *argv, cwd=None, timeout=120) -> dict:
        """Real CLI subprocess call: exactly one JSON object and the matching exit code."""
        proc = subprocess.run([sys.executable, str(HELPER), *[str(a) for a in argv]], cwd=str(cwd or self.tmp),
                              capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout)
        obj = parse_one(proc.stdout.decode("utf-8"))
        assert proc.returncode == STATUSES[obj["status"]], (proc.returncode, obj, proc.stderr)
        return obj

    def cli_async(self, *argv, cwd=None) -> subprocess.Popen:
        return subprocess.Popen([sys.executable, str(HELPER), *[str(a) for a in argv]], cwd=str(cwd or self.tmp),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)

    def finish(self, proc: subprocess.Popen, timeout=120) -> dict:
        out, err = proc.communicate(timeout=timeout)
        obj = parse_one(out.decode("utf-8"))
        assert proc.returncode == STATUSES[obj["status"]], (proc.returncode, obj, err)
        return obj

    def state(self, branch: str) -> dict:
        return json.loads((self.root / "build-step-runs" / branch / "state.json").read_text(encoding="utf-8"))

    def start(self, owner, project: Path, **kw) -> str:
        res = self.call(self.ctx(owner, **kw), "scope", "--project-root", project)
        assert res["status"] == "ok", res
        return res["run"]

    def prepare(self, owner, project: Path, edits=None, *, stash=False) -> tuple:
        """scope [+ stash-save] + worktree-create + developer edits + changes.  Returns (branch, wt_project)."""
        branch = self.start(owner, project)
        if stash:
            res = self.cli("stash-save", "--run", branch)
            assert res["status"] == "ok", res
        res = self.cli("worktree-create", "--run", branch)
        assert res["status"] == "ok", res
        wtp = Path(res["worktree_project"])
        for rel, data in (edits or {}).items():
            if data is None:
                (wtp / rel).unlink()
            else:
                write(wtp / rel, data)
        res = self.cli("changes", "--run", branch)
        assert res["status"] == "ok", res
        return branch, wtp

    def lock_files(self, repo: Path) -> dict:
        common = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
        found = {}
        for p in common.glob("skill-mesh-*.lock"):
            found[p.name] = json.loads(p.read_text(encoding="utf-8"))
        return found


@pytest.fixture
def env(tmp_path, monkeypatch):
    for key in list(os.environ):
        if key.upper().startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)
    gitconfig = tmp_path / "gitconfig"
    gitconfig.write_text("[init]\n\tdefaultBranch = main\n[core]\n\tautocrlf = false\n", encoding="utf-8")
    temp = tmp_path / "temp"
    temp.mkdir()
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(gitconfig))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    for var in ("TMP", "TEMP", "TMPDIR"):
        monkeypatch.setenv(var, str(temp))
    monkeypatch.setenv("PYTHONIOENCODING", "utf-8")
    monkeypatch.setattr(tempfile, "tempdir", None)
    e = Env(tmp_path)
    yield e
    for o in e.owners:
        try:
            o.kill()
        except Exception:  # noqa: BLE001
            pass
    # never leave registered worktrees or app processes behind
    for state in (e.root / "build-step-runs").glob("*/state.json"):
        try:
            st = json.loads(state.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if st.get("supervisor"):
            subprocess.run([sys.executable, str(HELPER), "app-stop", "--run", st["branch"]], capture_output=True,
                           stdin=subprocess.DEVNULL, timeout=60)
