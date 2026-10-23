"""build_step_tree.py - Git, run-state and process mechanics helper for build-step (P1).

Invocation: ``python <skill-dir>/scripts/build_step_tree.py <subcommand> [options]``, one tool
call per subcommand.  Every call prints exactly ONE JSON object on stdout whose ``status`` field
is authoritative: ``ok`` | ``halt`` | ``scope-escape`` | ``unavailable``.  A call that prints
anything else is a helper failure for the caller, whatever its exit code.  Python 3 standard
library only (>= 3.11); Windows process and job APIs through ctypes, POSIX fallbacks.

Contract source: the reviewed build-step core (Mechanics helper, Run state machine T1-T20, Steps
0-10) and design notes sections 1, 3, 9 and 10.  Labels: [AD] = agent-defaulted where the core
is silent (build-contract decision B-P1); everything else follows the core.

Subcommands and flags (subcommand names are the core's; flag spellings are [AD]):
  scope [--project-root DIR]                       T1; PROJECT_ROOT defaults to the cwd
  recover --check [--run B] [--project-root DIR]   T2/T3 listing and tree= input
  recover B [--keep-current P ...] [--stash-resolved] [--abandon --by C]   T13-T20
  unlock LOCK [--project-root DIR]                 T18
  stash-save --run B                               T4
  stash-restore --run B                            T5 + T10
  worktree-create --run B
  changes --run B
  tree-hash --run B
  preview-apply --run B / preview-rollback --run B T6 / T7
  land --run B / land-rollback --run B             T8 / T7 (Step 8.2 overlap check inside land)
  verify-landed --run B                            T9
  ship-gate --run B                                Step 8.1
  app-start --run B --start-cmd CMD [--url U] [--ready-url R] [--log PATH]
  app-stop --run B
  test-count (--check-runner CMD | (--command CMD | --runner NAME) --log PATH) [--project-root D]
  budget read --run B (--problem T | --problem-file P) [--plan-step S] [--issue N] [--max-iter N]
  budget advance (--run B | --key K) / budget clear (--run B | --key K)
  archive --run B [--keep-evidence]                Step 8.9 (writes landed-paths.json)
  cleanup --run B                                  Step 8.9
  finalize OUTCOME --run B                         T11

Agent defaults [AD]:
  * Exit codes: 0 ok, 1 halt, 2 scope-escape, 3 unavailable.  Callers trust only the JSON.
  * The run is named by ``--run <branch>``; run state is keyed by that branch.  Run state never
    holds a verdict key, verdict path or verdict run id; this helper never receives them.
  * Owner process: the nearest ancestor of this helper process whose executable base name
    (case-insensitive, ``.exe`` stripped) is one of HOST_EXECUTABLES (``claude``, ``codex``),
    found through the Toolhelp32 parent chain (Windows) or /proc or ps (POSIX), with its start
    time (GetProcessTimes creation time on Windows).  A parent whose start time is later than its
    child's is a reused PID and ends the walk.  No host ancestor -> ``unavailable`` (fail
    closed; there is no fallback, no CLI flag and no environment override).  A host whose CLI runs
    under a generic interpreter image (for example node.exe) is not recognized.  ``session_id``
    is recorded as null: identity rests on PID + start time + host name only.
  * The owner resolver, the clock, the lock wait and poll bounds, the readiness timeouts, a
    lock-wait callback and crash-fault points are injectable ONLY through the library API
    (``Context`` passed to ``run_cli``/``main``), for tests.
  * Tree lock name: ``skill-mesh-tree-<first 16 hex of sha256(normcase(GIT_ROOT))>.lock``.  Lock
    files are created atomically (hard link of a fully written temp file) and hold JSON with the
    owner run's branch, token, owner fields, GIT_ROOT and acquisition time.  Poll interval 0.5 s.
  * Payload (AV-29): built in a temporary index (GIT_INDEX_FILE under run state) loaded with the
    child worktree index's entries (``ls-files -s``) but no stat data, then ``git add -A``; so it
    holds commits, staged, unstaged and untracked non-ignored changes (the core's
    ``git diff <baseline>`` plus ``ls-files --others --exclude-standard``) and content-hashes
    every tracked file instead of trusting stat data (same-size racy edits are never missed).  The audit runs over every changed path of the
    whole child worktree before orchestrator paths (``.build-step``, ``.review-deep`` under the
    project) are removed.  The filtered payload is written into a second temporary index read
    from the baseline tree; its ``write-tree`` id is recorded and landing reads blobs from that
    immutable tree.  Payload hash = sha256 of the deterministic tree-to-tree patch
    (``--binary --full-index --no-renames --no-ext-diff --no-textconv``, fixed prefixes and
    algorithm).  Symlink and submodule changes are refused (``halt``, unsupported path type).
  * Writing a payload path uses ``git cat-file --filters --path=<p> <blob>`` so the operator tree
    receives working-tree form bytes (autocrlf, attributes).  Snapshots, rollback and
    verify-landed compare raw byte sha256 (AV-28); only ``landed-paths.json`` uses the filtered
    blob id from ``git hash-object -- <path>`` taken right after the write under the lock.
  * This helper never writes any index, so a snapshot's recorded written index entry always
    equals its prior entry and rollback never restores an index entry.
  * Preview writes the payload state of each path (copy or delete) under an active snapshot; it
    does not merge, because every preview is rolled back before any review decision.  Landing
    classifies every path and computes every merge BEFORE the snapshot; a conflict therefore
    writes nothing, releases the tree lock and returns ``halt`` (``merge conflict``); the
    caller's ``land-rollback`` is then an ok no-op.  Both-deleted and identical both-added paths
    are no-ops; a payload deletion of an operator-changed file, an operator deletion of a
    payload-modified file, any existing untracked destination, and a binary merge are conflicts.
  * ``recover --check`` returns ``halt`` (``concurrent run active`` T2 or ``unfinished prior
    run`` T3) only for a ``--run`` that is still in state ``scoped`` (the table's T2/T3 state);
    otherwise (no ``--run``, a later state, or a cleaned run) it returns ``ok`` with the listing
    and ``tree``.  Any unreadable run state makes it ``unavailable`` (``tree=leftover``).
  * [AD RF-8] ``recover --check --run B`` for a run whose state is gone (after ``cleanup``) never
    takes GIT_ROOT from the ambient cwd: ``--project-root`` when given, else the ``git_root`` of
    ``<archive>/B/landed-paths.json`` (listed for the whole operator tree, prefix ``.``), else
    ``halt`` (``no run state``).  The result names the route in ``scope_source``.  Without
    ``--run`` the cwd stays the PROJECT_ROOT default, as for ``scope``.
  * ``ship-gate``: no ``origin`` remote, or no resolvable default branch (origin/HEAD, else the
    single existing origin/main or origin/master) -> ``unavailable``.  A failed fetch with a
    configured remote is ``halt`` (``ship-gate fetch failed``), never not-checked.
  * ``stash-restore`` with no stash entry carrying the recorded object id returns ``halt``
    (``restore failed``, entry missing) instead of re-applying; the operator resolves via
    ``recover <b> --stash-resolved``.  After a successful apply, a drop failure keeps the result
    ``restored`` and names the stale entry (AV-31); a drop that removed a different object is
    re-stored with ``git stash store``.
  * [AD RF-2] ``stash-save`` refuses with ``halt`` (``stash failed``, naming ``links``) before any
    ``git stash push`` when a dirty or untracked path under PROJECT_PREFIX, or one of its
    directories below GIT_ROOT, is a symlink, junction or other reparse point (``git stash``
    deletes through a junction and restores a plain directory); a path that cannot be inspected
    counts as a link.  ``refs/stash``, the stash state (``none``), the link and its target are
    unchanged.
  * [AD RF-4] ``stash-save`` also refuses (``stash failed``, naming ``staged_outside_prefix``, nothing
    stashed) when PROJECT_PREFIX is not ``.`` and the operator index has staged changes outside
    it: ``git stash push -- <prefix>`` records the whole index, so ``apply --index`` would fail
    or rewrite out-of-prefix index entries.  An accepted stash's index commit therefore differs
    from its base only under the prefix, and ``stash.paths`` lists only prefix paths.  The
    prefix filter inside ``stash_paths`` is defense in depth and untested by construction: after
    the refusal an out-of-prefix path can reach it only through a race between the refusal and
    the push, or through T5 (a reviewer mutation that removes the filter, Y7, survives the suite).
  * [AD RF-3] ``stash-save`` records the raw bytes and sha256 of every path it stashes (under
    ``<run-state>/stash-raw/``; a directory entry such as an untracked nested repository, which
    ``git stash`` never takes, is not recorded).  After a successful ``apply --index`` each path is compared raw:
    Git-equivalent drift (the same clean-filtered blob, for example autocrlf CRLF on a file the
    operator saved with LF) gets the saved bytes written back atomically; any other drift keeps
    the saved bytes under ``leftovers/stash/``, records ``stash.drift`` (so ``tree=leftover``) and
    returns ``halt`` (``restore failed``; in ``recover``: ``recover halted: stash restored with
    drift``).  The entry is never re-applied.  [AD] Drift reuses the existing reason
    ``restore failed`` and carries no ``remedy``: the entry is already dropped, so the usual
    ``restore failed`` remedies do not fit (``--stash-resolved`` gives ``no saved stash``); each
    ``drift`` item names its saved copy, and a later plain ``recover <b>`` finishes as
    ``recovered`` with a note naming the drifted paths.
  * [AD R2-5] ``cleanup`` refuses (``cleanup refused``, naming each drift path and its saved copy
    in ``drift``, nothing removed) while the run's stash was restored with drift: the copies under
    ``leftovers/stash/`` are then the only copy of the operator's stash-save bytes, and removing
    the run state would delete them.  The run state, worktree and branch are kept, as for every
    BLOCKED run; there is no helper remedy: the operator copies the saved bytes out, then removes
    the worktree, branch and run state by hand.  (Refusal was chosen over relocating the copies
    into the archive.)
  * ``app-start`` starts a detached supervisor (this script, internal ``_supervise``) that puts
    itself in a named Windows job object with KILL_ON_JOB_CLOSE (POSIX: a new session / process
    group) and runs ``--start-cmd`` through the platform shell from PROJECT_ROOT; it then polls
    ``--ready-url`` for HTTP 200 (60 s) and ``--url`` for any HTTP status below 500 (30 s).  App
    exit during startup -> ``halt`` (``app exited during startup``); timeout -> ``halt``
    (``readiness timeout``); a port already bound -> ``halt`` (``port in use``).  ``app-stop``
    terminates only that job or process group, then confirms the ports are free; a still-bound
    port is ``halt`` (``port still bound``) with owning PIDs where the OS reports them.
  * ``test-count`` strips env assignments, ``cross-env``, ``uv run``, ``npx``, ``pnpm exec``,
    ``python -m`` and follows ``npm [--prefix d] test``, ``npm run``, ``pnpm test|run``,
    ``yarn test|run`` through package.json scripts (at most 3 hops); a script with several
    recognized runners of different kinds is ambiguous (unrecognized).  An unreadable count is
    ``unavailable`` (``count unreadable``).
  * ``budget``: key = sha256 of {GIT_ROOT, plan-step else issue, sha256(problem)}; without
    plan-step or issue the run branch joins the key (a fresh budget per invocation).  ``read``
    creates the record (limit = --max-iter or 10); an explicit --max-iter replaces the limit only.
  * ``landed-paths.json`` = {"schema":"build-step-landed-paths/1","branch":...,"git_root":<GIT_ROOT
    as Git prints it>,"paths":[{"path":"<repo-relative posix>","state":"<blob-id>|deleted"}]}.
  * [AD RF-1] ``cleanup`` walks the recorded worktree without following links before
    ``git worktree remove --force`` (which deletes THROUGH a junction on Windows) and removes
    every symlink, junction or reparse point as a link, never its target (reported as
    ``links_removed``).  A worktree root that is itself a link, an entry that cannot be
    inspected, or a link that cannot be removed as a link is ``cleanup failed`` naming it, and
    the worktree, branch and run state are kept.
  * [AD RF-5] Per-run call lock: an OS byte-range lock (msvcrt on Windows, flock on POSIX, released
    by the OS when the process exits) on ``<temp>/skill-mesh/build-step-calls/<branch>.lock``.
    Every call of a run (``recover <b>`` on its target) holds it from entry to exit except while
    waiting on a busy tree or stash lock; every run-state write happens under it (enforced).  A
    call that waited takes it back, reloads the run state, and if the run was finalized meanwhile
    returns ``halt`` (``run finalized``) after releasing every lock T11 says a finalized run must
    not hold, writing nothing; otherwise it re-validates its preconditions on the reloaded state.
    So once ``finalize`` has returned ``ok``, no other call of the run except ``recover`` writes
    operator bytes, snapshots, applies or drops a stash, or clears ``finalized``.  The call lock
    busy for longer than 10 minutes is ``halt`` (``run call in progress``).  [AD] That result
    names no holder process and carries no remedy (only ``waited_seconds``).  [AD] Call-lock
    files are never deleted: ``cleanup`` leaves one empty, unlocked file per run under
    ``build-step-calls/``.
  * [AD R2-3] The stash lock is held only under the run's tree lock (T4/T10 guard order).  Lock
    files are owned per run token, not per call, so a sibling call of the same run (for example a
    no-op rollback) can release the tree lock while this call waits on the stash lock.  After the
    stash lock is taken, a call that no longer holds its tree lock releases the stash lock, writes
    nothing (no ``pending``, no push, no apply) and returns ``halt`` (``lock busy``, ``lock_kind``
    ``tree``, detail ``tree lock lost during wait``, no remedy).  The check is by run token: a tree
    lock that a sibling call of the same run re-took meanwhile counts as held.
  * [AD R2-2] ``recover <b>`` never releases the target's tree lock while the target's reloaded
    state has an ``active`` snapshot.  A helper call of the dead run that outlived its host (a
    "zombie", for example a ``land`` waiting on another run's tree lock) can land during
    recover's own lock wait; recover then returns ``halt`` (``recover halted``, detail naming the
    active snapshot, ``snapshots``, ``holds_tree_lock``) with the remedy ``recover <b>``, which
    rolls that snapshot back (T7) and continues T13.
  * Internal errors return ``halt`` (``internal error``), never ``unavailable``, so no exception
    can fail open as a not-checked ship gate.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime
import hashlib
import io
import json
import os
import re
import secrets
import shlex
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

HELPER_VERSION = "1"
SCHEMA_RUN = "build-step-run/1"
SCHEMA_LANDED = "build-step-landed-paths/1"
SCHEMA_BUDGET = "build-step-budget/1"
EXIT_CODES = {"ok": 0, "halt": 1, "scope-escape": 2, "unavailable": 3}
HOST_EXECUTABLES = ("claude", "codex")
LOCK_WAIT_SECONDS = 600.0
ABANDON_HEARTBEAT_SECONDS = 15 * 60
OTHER_HOST_HEARTBEAT_SECONDS = 24 * 60 * 60
DEFAULT_MAX_ITER = 10
ORCHESTRATOR_DIRS = (".build-step", ".review-deep")
BRANCH_RE = re.compile(r"^build-step-\d{8}T\d{6}Z-[0-9a-f]{8}$")
LOCK_NAME_RE = re.compile(r"^skill-mesh-(stash|tree-[0-9a-f]{16})\.lock$")
SCRIPT_PATH = os.path.abspath(__file__)
IS_WINDOWS = os.name == "nt"
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_REPARSE_POINT = 0x400

if IS_WINDOWS:
    import msvcrt
else:
    import fcntl


# ---------------------------------------------------------------------------------------------
# Outcomes and context
# ---------------------------------------------------------------------------------------------

class Outcome(Exception):
    """A terminal result of one call: status plus fields."""

    def __init__(self, status: str, reason: Optional[str] = None, **fields: Any) -> None:
        super().__init__(reason or status)
        self.status = status
        self.reason = reason
        self.fields = fields


class InjectedCrash(BaseException):
    """Raised at a library-injected fault point to simulate a killed helper (tests only)."""


class GitError(Exception):
    def __init__(self, args: list, code: int, stderr: bytes) -> None:
        super().__init__(f"git {' '.join(args)} exited {code}")
        self.git_args = args
        self.code = code
        self.stderr = stderr.decode("utf-8", "replace").strip()


def halt(reason: str, **fields: Any) -> "Outcome":
    raise Outcome("halt", reason, **fields)


def unavailable(reason: str, **fields: Any) -> "Outcome":
    raise Outcome("unavailable", reason, **fields)


@dataclasses.dataclass
class Context:
    """Library-only injection points (never reachable from the CLI or the environment)."""

    owner_resolver: Optional[Callable[[], Optional[dict]]] = None
    clock: Callable[[], float] = time.time
    sleep: Callable[[float], None] = time.sleep
    lock_wait_seconds: float = LOCK_WAIT_SECONDS
    lock_poll_seconds: float = 0.5
    ready_timeout_seconds: float = 60.0
    url_timeout_seconds: float = 30.0
    temp_root: Optional[str] = None
    cwd: Optional[str] = None
    on_lock_wait: Optional[Callable[[str, int], None]] = None
    faults: frozenset = frozenset()
    call_lock_wait_seconds: float = LOCK_WAIT_SECONDS
    call_locks: dict = dataclasses.field(default_factory=dict)  # branch -> OS file descriptor (RF-5)

    def now(self) -> float:
        return float(self.clock())

    def root(self) -> Path:
        base = self.temp_root if self.temp_root is not None else tempfile.gettempdir()
        return Path(os.path.abspath(base)) / "skill-mesh"

    def resolve_owner(self) -> Optional[dict]:
        if self.owner_resolver is not None:
            return self.owner_resolver()
        return resolve_host_owner()


def _fault(ctx: Context, name: str) -> None:
    if name in ctx.faults:
        raise InjectedCrash(name)


def iso(ts: float) -> str:
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def remedy_cmd(*parts: str) -> str:
    quoted = []
    for part in parts:
        quoted.append(f'"{part}"' if (" " in part or "\\" in part or not part) else part)
    return f'python "{SCRIPT_PATH}" ' + " ".join(quoted)


# ---------------------------------------------------------------------------------------------
# Atomic file I/O
# ---------------------------------------------------------------------------------------------

def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}-{secrets.token_hex(4)}")
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    last: Optional[BaseException] = None
    for _ in range(40):
        try:
            os.replace(tmp, path)
            return
        except PermissionError as exc:  # Windows: a reader holds the target open
            last = exc
            time.sleep(0.05)
    try:
        os.unlink(tmp)
    except OSError:
        pass
    raise last if last else OSError(f"cannot replace {path}")


def atomic_write_json(path: Path, obj: Any) -> None:
    atomic_write_bytes(path, (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode("utf-8"))


def read_json(path: Path) -> Any:
    for attempt in range(5):
        try:
            with open(path, "rb") as handle:
                return json.loads(handle.read().decode("utf-8"))
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.05)
    return None


def raw_state(path: Path) -> Optional[str]:
    """sha256 of the raw bytes at path, None when absent, 'dir' for a directory."""
    if os.path.islink(path):
        try:
            return "link:" + sha256_bytes(os.readlink(path).encode("utf-8", "surrogateescape"))
        except OSError:
            return "link:?"
    if path.is_dir():
        return "dir"
    try:
        with open(path, "rb") as handle:
            return sha256_bytes(handle.read())
    except FileNotFoundError:
        return None


def replace_bytes(dst: Path, data: bytes) -> None:
    """Atomically replace an existing operator-tree file with data, keeping its mode (RF-3)."""
    tmp = dst.with_name(f".{dst.name}.bst-{secrets.token_hex(4)}")
    with open(tmp, "wb") as handle:
        handle.write(data)
    try:
        if not IS_WINDOWS:
            shutil.copymode(dst, tmp)
        os.replace(tmp, dst)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------------------------
# Links: symlinks, junctions and other reparse points (RF-1, RF-2)
# ---------------------------------------------------------------------------------------------

def is_link_like(info: os.stat_result) -> bool:
    """True for a symlink, or (Windows) any reparse point: junction, directory symlink, others."""
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT)


def path_is_link_like(path: Any) -> bool:
    """lstat-based (never follows the last component); an uninspectable path counts as a link."""
    try:
        return is_link_like(os.lstat(path))
    except (FileNotFoundError, NotADirectoryError):
        return False
    except OSError:
        return True


def links_on_paths(git_root: str, rels: list) -> list:
    """Each repo-relative path, or the first of its directories below GIT_ROOT, that is link-like."""
    known: dict = {}
    found = set()
    for rel in rels:
        parts = [p for p in rel.rstrip("/").split("/") if p]
        for i in range(1, len(parts) + 1):
            sub = "/".join(parts[:i])
            if sub not in known:
                known[sub] = path_is_link_like(fs_path(git_root, sub))
            if known[sub]:
                found.add(sub)
                break
    return sorted(found)


def find_links(root: str) -> tuple:
    """Walk root without following any link: ([link-like entries], [entries that could not be read])."""
    links, unreadable = [], []
    stack = [root]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                entries = list(it)
        except OSError:
            unreadable.append(cur)
            continue
        for entry in entries:
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError:
                unreadable.append(entry.path)
                continue
            if is_link_like(info):
                links.append(entry.path)
            elif stat.S_ISDIR(info.st_mode):
                stack.append(entry.path)
    return sorted(links), sorted(unreadable)


def remove_link(path: str) -> Optional[str]:
    """Remove a link-like entry as a link (never its target).  Returns an error text or None."""
    try:
        info = os.lstat(path)
        if not is_link_like(info):
            return "no longer a link; not removed"
        if IS_WINDOWS and getattr(info, "st_file_attributes", 0) & FILE_ATTRIBUTE_DIRECTORY:
            os.rmdir(path)  # junction or directory symlink: RemoveDirectoryW removes the link only
        else:
            os.unlink(path)
    except OSError as exc:
        return f"{type(exc).__name__}: {exc}"
    return "still present after removal" if os.path.lexists(path) else None


# ---------------------------------------------------------------------------------------------
# Git plumbing
# ---------------------------------------------------------------------------------------------

_GIT_ENV_DROP = {
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_PREFIX", "GIT_LITERAL_PATHSPECS",
    "GIT_GLOB_PATHSPECS", "GIT_NOGLOB_PATHSPECS", "GIT_ICASE_PATHSPECS", "GIT_NAMESPACE",
}


def git_env(extra: Optional[dict] = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k.upper() not in _GIT_ENV_DROP}
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["LC_ALL"] = "C"
    env["LANGUAGE"] = "C"
    if extra:
        env.update(extra)
    return env


def git(args: list, cwd: Any, *, env: Optional[dict] = None, input: Optional[bytes] = None,
        check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["git", *[str(a) for a in args]]
    kwargs: dict = {"cwd": str(cwd), "env": git_env(env), "capture_output": True}
    if input is None:
        kwargs["stdin"] = subprocess.DEVNULL
    else:
        kwargs["input"] = input
    proc = subprocess.run(cmd, **kwargs)
    if check and proc.returncode != 0:
        raise GitError(list(args), proc.returncode, proc.stderr)
    return proc


def git_out(args: list, cwd: Any, **kw: Any) -> str:
    return git(args, cwd, **kw).stdout.decode("utf-8", "surrogateescape").strip()


def split_z(data: bytes) -> list:
    return [p.decode("utf-8", "surrogateescape") for p in data.split(b"\0") if p]


def norm_key(path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def fs_path(git_root: str, rel: str) -> Path:
    return Path(os.path.normpath(git_root)).joinpath(*rel.split("/"))


def safe_rel(rel: str) -> bool:
    if not rel or rel.startswith("/") or "\\" in rel or "\0" in rel:
        return False
    parts = rel.split("/")
    for part in parts:
        if part in ("", ".", "..") or part.lower() == ".git":
            return False
        if IS_WINDOWS and ":" in part:
            return False
    return True


def in_prefix(rel: str, prefix: str) -> bool:
    if prefix == ".":
        return True
    base = prefix.rstrip("/")
    return rel == base or rel.startswith(base + "/")


def prefixes_overlap(a: str, b: str) -> bool:
    if a == "." or b == ".":
        return True
    a1, b1 = a.rstrip("/"), b.rstrip("/")
    return a1 == b1 or a1.startswith(b1 + "/") or b1.startswith(a1 + "/")


def prefix_pathspec(prefix: str) -> str:
    return "." if prefix == "." else f":(top,literal){prefix.rstrip('/')}"


def zero_oid(like: str) -> str:
    return "0" * len(like)


def index_map(git_root: str) -> dict:
    """path -> 'mode oid stage' lines for the operator index (stage 0 preferred)."""
    out = git(["ls-files", "-s", "-z"], git_root).stdout
    result: dict = {}
    for rec in split_z(out):
        meta, _, path = rec.partition("\t")
        mode, oid, stage = meta.split(" ")
        if stage == "0" or path not in result:
            result[path] = {"mode": mode, "oid": oid, "stage": stage}
    return result


def hash_object(git_root: str, rel: str) -> str:
    return git_out(["hash-object", "--", rel], git_root)


def hash_object_bytes(git_root: str, rel: str, data: bytes) -> str:
    """Blob id of data as if it were the working-tree file at rel (its clean filters applied)."""
    return git_out(["hash-object", "--stdin", f"--path={rel}"], git_root, input=data)


def worktree_form(git_root: str, rel: str, oid: str) -> bytes:
    return git(["cat-file", "--filters", f"--path={rel}", oid], git_root).stdout


# ---------------------------------------------------------------------------------------------
# Process identity and liveness (Windows via ctypes; POSIX via /proc or ps)
# ---------------------------------------------------------------------------------------------

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _TH32CS_SNAPPROCESS = 0x00000002
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _STILL_ACTIVE = 259
    _INVALID_HANDLE = wintypes.HANDLE(-1).value

    class _PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260),
        ]

    _k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    _k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    _k32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
    _k32.Process32FirstW.restype = wintypes.BOOL
    _k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
    _k32.Process32NextW.restype = wintypes.BOOL
    _k32.OpenProcess.restype = wintypes.HANDLE
    _k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _k32.CloseHandle.argtypes = [wintypes.HANDLE]
    _k32.CloseHandle.restype = wintypes.BOOL
    _k32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    _k32.GetProcessTimes.restype = wintypes.BOOL
    _k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    _k32.GetExitCodeProcess.restype = wintypes.BOOL

    def _win_table() -> dict:
        snap = _k32.CreateToolhelp32Snapshot(_TH32CS_SNAPPROCESS, 0)
        if not snap or snap == _INVALID_HANDLE:
            return {}
        table: dict = {}
        try:
            entry = _PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(_PROCESSENTRY32W)
            ok = _k32.Process32FirstW(snap, ctypes.byref(entry))
            while ok:
                table[int(entry.th32ProcessID)] = (int(entry.th32ParentProcessID), entry.szExeFile)
                ok = _k32.Process32NextW(snap, ctypes.byref(entry))
        finally:
            _k32.CloseHandle(snap)
        return table

    def _win_times(pid: int) -> tuple:
        """(creation ticks or None, running bool or None-if-unknown)."""
        handle = _k32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not handle:
            err = ctypes.get_last_error()
            return (None, None if err == 5 else False)
        try:
            c, e, k, u = (wintypes.FILETIME() for _ in range(4))
            if not _k32.GetProcessTimes(handle, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)):
                return (None, None)
            ticks = (int(c.dwHighDateTime) << 32) | int(c.dwLowDateTime)
            code = wintypes.DWORD()
            running = None
            if _k32.GetExitCodeProcess(handle, ctypes.byref(code)):
                running = int(code.value) == _STILL_ACTIVE
            return (ticks, running)
        finally:
            _k32.CloseHandle(handle)


def _posix_stat(pid: int) -> Optional[tuple]:
    """(ppid, comm, start) from /proc, else ps; None when the process is gone."""
    proc = Path(f"/proc/{pid}/stat")
    if proc.exists():
        try:
            data = proc.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        lpar, rpar = data.find("("), data.rfind(")")
        comm = data[lpar + 1:rpar]
        fields = data[rpar + 2:].split()
        try:
            exe = os.path.basename(os.readlink(f"/proc/{pid}/exe"))
        except OSError:
            exe = comm
        return (int(fields[1]), exe or comm, "proc:" + fields[19])
    try:
        out = subprocess.run(["ps", "-o", "ppid=", "-o", "lstart=", "-o", "comm=", "-p", str(pid)],
                             capture_output=True, text=True, stdin=subprocess.DEVNULL)
    except OSError:
        return None
    line = out.stdout.strip()
    if out.returncode != 0 or not line:
        return None
    parts = line.split()
    if len(parts) < 7:
        return None
    return (int(parts[0]), os.path.basename(" ".join(parts[6:])), "ps:" + " ".join(parts[1:6]))


def process_start_time(pid: int) -> Optional[str]:
    if IS_WINDOWS:
        ticks, _running = _win_times(pid)
        return None if ticks is None else f"win:{ticks}"
    st = _posix_stat(pid)
    return None if st is None else st[2]


def process_identity(pid: int) -> Optional[dict]:
    """Public helper: {pid, start_time, exe} of a running process, or None."""
    if IS_WINDOWS:
        table = _win_table()
        start = process_start_time(pid)
        if start is None or pid not in table:
            return None
        return {"pid": int(pid), "start_time": start, "exe": table[pid][1]}
    st = _posix_stat(pid)
    if st is None:
        return None
    return {"pid": int(pid), "start_time": st[2], "exe": st[1]}


def process_alive(pid: Any, start_time: Any) -> bool:
    """True when a process with this PID and exactly this start time runs on this host."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if IS_WINDOWS:
        ticks, running = _win_times(pid)
        if ticks is None:
            return running is None  # access denied: exists, start unknown -> conservative alive
        return running is not False and f"win:{ticks}" == start_time
    st = _posix_stat(pid)
    return st is not None and st[2] == start_time


def _is_host_exe(name: str) -> bool:
    base = os.path.basename(name or "").lower()
    if base.endswith(".exe"):
        base = base[:-4]
    return base in HOST_EXECUTABLES


def resolve_host_owner() -> Optional[dict]:
    """Nearest ancestor running a host executable, with start time; None when absent."""
    host = socket.gethostname()
    pid = os.getpid()
    if IS_WINDOWS:
        table = _win_table()
        cur_ticks, _ = _win_times(pid)
        if cur_ticks is None:
            return None
        for _ in range(64):
            if pid not in table:
                return None
            ppid = table[pid][0]
            if ppid <= 0 or ppid == pid or ppid not in table:
                return None
            p_ticks, _running = _win_times(ppid)
            if p_ticks is None or p_ticks > cur_ticks:
                return None
            exe = table[ppid][1]
            if _is_host_exe(exe):
                return {"pid": ppid, "start_time": f"win:{p_ticks}", "host": host, "exe": exe,
                        "session_id": None}
            pid, cur_ticks = ppid, p_ticks
        return None
    cur = _posix_stat(pid)
    for _ in range(64):
        if cur is None:
            return None
        ppid = cur[0]
        if ppid <= 1 or ppid == pid:
            return None
        parent = _posix_stat(ppid)
        if parent is None:
            return None
        if _is_host_exe(parent[1]):
            return {"pid": ppid, "start_time": parent[2], "host": host, "exe": parent[1],
                    "session_id": None}
        pid, cur = ppid, parent
    return None


def same_process(a: Optional[dict], b: Optional[dict]) -> bool:
    if not a or not b:
        return False
    return (int(a.get("pid", -1)) == int(b.get("pid", -2)) and a.get("start_time") == b.get("start_time")
            and a.get("host") == b.get("host"))


# ---------------------------------------------------------------------------------------------
# Run state
# ---------------------------------------------------------------------------------------------

def runs_root(ctx: Context) -> Path:
    return ctx.root() / "build-step-runs"


def run_dir(ctx: Context, branch: str) -> Path:
    if not BRANCH_RE.match(branch or ""):
        halt("invalid run name", run=branch)
    return runs_root(ctx) / branch


def load_state(ctx: Context, branch: str, *, missing_ok: bool = False) -> Optional[dict]:
    path = run_dir(ctx, branch) / "state.json"
    if not path.exists():
        if missing_ok:
            return None
        halt("no run state", run=branch)
    try:
        st = read_json(path)
    except (OSError, ValueError) as exc:
        unavailable("run state unreadable", run=branch, error=str(exc))
    if not isinstance(st, dict) or st.get("schema") != SCHEMA_RUN or st.get("branch") != branch:
        unavailable("run state unreadable", run=branch)
    return st


def save_state(ctx: Context, st: dict) -> None:
    if st["branch"] not in ctx.call_locks:  # RF-5: every run-state write happens under its call lock
        raise RuntimeError(f"run state write without the run call lock ({st['branch']})")
    atomic_write_json(run_dir(ctx, st["branch"]) / "state.json", st)


# Per-run call lock (RF-5) [AD]: an OS byte-range lock (msvcrt on Windows, flock on POSIX) on
# <temp>/skill-mesh/build-step-calls/<branch>.lock, released by the OS when the process exits.  A
# call of a run holds it from entry to exit, except while it waits on a busy tree or stash lock;
# after such a wait it takes it back and reloads the run state (rejoin_run).

def call_lock_path(ctx: Context, branch: str) -> Path:
    if not BRANCH_RE.match(branch or ""):
        halt("invalid run name", run=branch)
    return ctx.root() / "build-step-calls" / f"{branch}.lock"


def _os_try_lock(fd: int) -> bool:
    try:
        if IS_WINDOWS:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _os_unlock(fd: int) -> None:
    try:
        if IS_WINDOWS:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    try:
        os.close(fd)
    except OSError:
        pass


def hold_call_lock(ctx: Context, branch: str) -> None:
    if branch in ctx.call_locks:
        return
    path = call_lock_path(ctx, branch)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o600)
    start = time.monotonic()
    while not _os_try_lock(fd):
        waited = time.monotonic() - start
        if waited >= ctx.call_lock_wait_seconds:
            os.close(fd)
            halt("run call in progress", run=branch, waited_seconds=round(waited, 1),
                 detail="another helper call of this run holds its call lock")
        ctx.sleep(ctx.lock_poll_seconds)
    ctx.call_locks[branch] = fd


def release_call_lock(ctx: Context, branch: str) -> None:
    fd = ctx.call_locks.pop(branch, None)
    if fd is not None:
        _os_unlock(fd)


def release_call_locks(ctx: Context) -> None:
    for branch in list(ctx.call_locks):
        release_call_lock(ctx, branch)


def run_alive(ctx: Context, st: dict) -> bool:
    if st.get("finalized"):
        return False
    owner = st.get("owner") or {}
    if owner.get("host") == socket.gethostname():
        return process_alive(owner.get("pid"), owner.get("start_time"))
    try:
        return ctx.now() - float(st.get("heartbeat_epoch", 0)) < OTHER_HOST_HEARTBEAT_SECONDS
    except (TypeError, ValueError):
        return False


def active_snapshots(st: dict) -> list:
    return [s for s in st.get("snapshots", []) if s.get("lifecycle") == "active"]


def snapshot_paths(snap: dict) -> list:
    return [e["path"] for e in snap.get("entries", [])]


def enter_run(ctx: Context, branch: str) -> dict:
    """Load a run for a non-recover call under its call lock: T12 refusal, then heartbeat refresh."""
    if not (run_dir(ctx, branch) / "state.json").exists():
        halt("no run state", run=branch)
    hold_call_lock(ctx, branch)
    st = load_state(ctx, branch)
    if st.get("finalized"):
        halt("run finalized", run=branch, finalized=st.get("finalized"))
    now = ctx.now()
    st["heartbeat_epoch"] = now
    st["heartbeat"] = iso(now)
    save_state(ctx, st)
    return st


def all_runs(ctx: Context) -> tuple:
    """([state dicts], [unreadable state paths])."""
    root = runs_root(ctx)
    states, bad = [], []
    if not root.is_dir():
        return states, bad
    for child in sorted(root.iterdir()):
        if not child.is_dir() or not BRANCH_RE.match(child.name):
            continue
        path = child / "state.json"
        if not path.exists():
            continue
        try:
            st = read_json(path)
            if not isinstance(st, dict) or st.get("schema") != SCHEMA_RUN or st.get("branch") != child.name:
                raise ValueError("schema")
            states.append(st)
        except (OSError, ValueError):
            bad.append(str(path))
    return states, bad


# ---------------------------------------------------------------------------------------------
# Locks
# ---------------------------------------------------------------------------------------------

def tree_lock_name(git_root: str) -> str:
    return f"skill-mesh-tree-{sha256_bytes(norm_key(git_root).encode('utf-8'))[:16]}.lock"


def lock_path(st: dict, kind: str) -> Path:
    common = Path(st["git_common_dir"])
    return common / ("skill-mesh-stash.lock" if kind == "stash" else tree_lock_name(st["git_root"]))


def read_lock(path: Path) -> Optional[dict]:
    try:
        data = read_json(path)
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        return {"unreadable": True}
    return data if isinstance(data, dict) else {"unreadable": True}


def _create_lock(path: Path, record: dict) -> bool:
    tmp = path.with_name(f".{path.name}.{record['token'][:8]}.{secrets.token_hex(4)}.tmp")
    with open(tmp, "wb") as handle:
        handle.write(json.dumps(record, sort_keys=True).encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    try:
        try:
            os.link(tmp, path)
            return True
        except FileExistsError:
            return False
        except (OSError, NotImplementedError):
            try:
                fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                return False
            with os.fdopen(fd, "wb") as handle:
                handle.write(json.dumps(record, sort_keys=True).encode("utf-8"))
            return True
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def lock_owner_alive(ctx: Context, rec: dict) -> bool:
    if rec.get("unreadable"):
        return False
    branch = rec.get("branch", "")
    if BRANCH_RE.match(branch or ""):
        path = run_dir(ctx, branch) / "state.json"
        if path.exists():
            try:
                st = read_json(path)
                if isinstance(st, dict) and st.get("token") == rec.get("token"):
                    return run_alive(ctx, st)
            except (OSError, ValueError):
                return True  # unreadable owner state: never treat as dead
    owner = rec.get("owner") or {}
    if owner.get("host") == socket.gethostname():
        return process_alive(owner.get("pid"), owner.get("start_time"))
    try:
        return ctx.now() - float(rec.get("acquired_epoch", 0)) < OTHER_HOST_HEARTBEAT_SECONDS
    except (TypeError, ValueError):
        return False


def owner_remedy(ctx: Context, rec: dict, caller: Optional[dict], alive: bool, lock_file: Optional[Path] = None,
                 git_root: Optional[str] = None) -> list:
    branch = rec.get("branch", "")
    has_state = bool(BRANCH_RE.match(branch or "")) and (run_dir(ctx, branch) / "state.json").exists()
    if not alive:
        if has_state:
            return [remedy_cmd("recover", branch)]
        if lock_file is not None:
            return [remedy_cmd("unlock", lock_file.name, "--project-root", git_root or "")]
        return []
    if caller and same_process(rec.get("owner"), caller.get("owner")) and caller.get("branch") != branch:
        return [remedy_cmd("recover", branch, "--abandon", "--by", caller["branch"])]
    return []


def rejoin_run(ctx: Context, st: dict, kind: Optional[str], *, allow_finalized: bool) -> None:
    """RF-5: after a lock wait, take the run call lock back and reload the run state in place.
    A run finalized meanwhile (and not in recover) returns ``halt`` (``run finalized``) after
    releasing what T11 says a finalized run must not hold; nothing is written."""
    hold_call_lock(ctx, st["branch"])
    try:
        fresh = load_state(ctx, st["branch"])
    except Outcome:
        if kind:
            release_lock(st, kind)
        raise
    st.clear()
    st.update(fresh)
    if fresh.get("finalized") and not allow_finalized:
        release_lock(st, "stash")
        release_tree_if_inactive(st)
        halt("run finalized", run=st["branch"], finalized=fresh.get("finalized"), stage="after lock wait",
             detail="the run was finalized while this call waited for a lock; nothing was written")


def acquire_lock(ctx: Context, st: dict, kind: str, *, allow_finalized: bool = False) -> None:
    path = lock_path(st, kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    waited = 0.0
    attempt = 0
    released = False  # RF-5: the run call lock is not held while waiting on a busy lock
    while True:
        record = {"kind": kind, "branch": st["branch"], "token": st["token"], "owner": st["owner"],
                  "git_root": st["git_root"], "acquired": iso(ctx.now()), "acquired_epoch": ctx.now()}
        rec = None
        if not _create_lock(path, record):
            rec = read_lock(path)
            if rec is None:
                continue  # released between our attempt and the read
        if rec is None or rec.get("token") == st["token"]:  # created, or held by this run's token
            if not released:
                return
            rejoin_run(ctx, st, kind, allow_finalized=allow_finalized)
            released = False
            if holds_lock(st, kind):
                return
            continue  # another call of this run released it meanwhile: take it again
        alive = lock_owner_alive(ctx, rec)
        if not alive or waited >= ctx.lock_wait_seconds:
            if released:
                rejoin_run(ctx, st, None, allow_finalized=allow_finalized)
            halt("lock busy", lock=str(path), lock_kind=kind, owner_record=rec, owner_alive=alive,
                 waited_seconds=round(waited, 1),
                 remedy=owner_remedy(ctx, rec, st, alive, path, st["git_root"]))
        if not released:
            release_call_lock(ctx, st["branch"])
            released = True
        attempt += 1
        if ctx.on_lock_wait is not None:
            ctx.on_lock_wait(kind, attempt)
        ctx.sleep(ctx.lock_poll_seconds)
        waited = max(waited + ctx.lock_poll_seconds, time.monotonic() - start)


def release_lock(st: dict, kind: str) -> bool:
    path = lock_path(st, kind)
    rec = read_lock(path)
    if rec is not None and rec.get("token") == st["token"]:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        return True
    return False


def holds_lock(st: dict, kind: str) -> bool:
    rec = read_lock(lock_path(st, kind))
    return bool(rec) and rec.get("token") == st["token"]


def release_tree_if_inactive(st: dict) -> None:
    if not active_snapshots(st):
        release_lock(st, "tree")


def acquire_stash_lock(ctx: Context, st: dict, *, allow_finalized: bool = False) -> None:
    """T4/T10 guard order: the stash lock is held only under this run's tree lock.  R2-3 [AD]: a
    sibling call of the same run token can release the tree lock while this call waits on the
    stash lock; then the stash lock is released, nothing is written and the call halts."""
    acquire_lock(ctx, st, "stash", allow_finalized=allow_finalized)
    if not holds_lock(st, "tree"):  # R2-3
        release_lock(st, "stash")
        tree = lock_path(st, "tree")
        halt("lock busy", lock=str(tree), lock_kind="tree", owner_record=read_lock(tree), remedy=[],
             detail="tree lock lost during wait: this run's tree lock was released while this call waited "
                    "for the stash lock; the stash lock was released and nothing was stashed, applied or written")


# ---------------------------------------------------------------------------------------------
# Scope and recover --check
# ---------------------------------------------------------------------------------------------

def resolve_scope(project_root: str) -> dict:
    proot = os.path.realpath(os.path.abspath(project_root))
    if not os.path.isdir(proot):
        halt("project root missing", project_root=proot)
    try:
        top = git_out(["rev-parse", "--show-toplevel"], proot)
        prefix = git_out(["rev-parse", "--show-prefix"], proot)
        common = git_out(["rev-parse", "--path-format=absolute", "--git-common-dir"], proot)
    except GitError as exc:
        halt("not a git repository", project_root=proot, error=exc.stderr)
    if not top:
        halt("not a git repository", project_root=proot)
    return {"project_root": proot, "git_root": top, "project_prefix": prefix if prefix else ".",
            "git_common_dir": os.path.normpath(common)}


def run_summary(ctx: Context, st: dict) -> dict:
    stash = st.get("stash") or {"state": "none"}
    return {
        "branch": st["branch"], "alive": run_alive(ctx, st), "finalized": st.get("finalized"),
        "project_prefix": st.get("project_prefix"), "owner": st.get("owner"),
        "heartbeat": st.get("heartbeat"),
        "active_snapshots": [{"id": s["id"], "kind": s["kind"], "paths": snapshot_paths(s)}
                             for s in active_snapshots(st)],
        "stash": {"state": stash.get("state"), "oid": stash.get("oid"), "paths": stash.get("paths", [])},
    }


def check_runs(ctx: Context, git_root: str, prefix: str, self_branch: Optional[str],
               caller: Optional[dict]) -> dict:
    key = norm_key(git_root)
    states, bad = all_runs(ctx)
    listed, t2, t3, others_active = [], [], [], []
    for st in states:
        if st["branch"] == self_branch or norm_key(st.get("git_root", "")) != key:
            continue
        stash = st.get("stash") or {}
        acts = active_snapshots(st)
        stash_live = stash.get("state") in ("pending", "saved")
        if not acts and not stash_live:
            continue
        summary = run_summary(ctx, st)
        listed.append(summary)
        if acts:
            others_active.append(summary)
        snap_in_prefix = any(in_prefix(p, prefix) for s in acts for p in snapshot_paths(s))
        if stash.get("state") == "saved" and stash.get("paths"):
            stash_in_prefix = any(in_prefix(p, prefix) for p in stash["paths"])
        else:
            stash_in_prefix = stash_live and prefixes_overlap(st.get("project_prefix", "."), prefix)
        alive = summary["alive"]
        if alive and (snap_in_prefix or stash_in_prefix):
            t2.append(summary)
        elif not alive and (acts or stash_in_prefix):
            t3.append(summary)
    remedy: list = []
    for summary in t2:
        remedy += owner_remedy(ctx, {"branch": summary["branch"], "owner": summary["owner"]}, caller, True)
    for summary in t3:
        remedy.append(remedy_cmd("recover", summary["branch"]))
    return {"runs": listed, "t2": t2, "t3": t3, "others_active": others_active, "unreadable": bad,
            "remedy": remedy}


def compute_tree(ctx: Context, st: Optional[dict], git_root: str, prefix: str) -> dict:
    reasons, paths = [], []
    if st is not None:
        for snap in active_snapshots(st):
            reasons.append(f"own active {snap['kind']} snapshot")
            paths += snapshot_paths(snap)
        stash = st.get("stash") or {}
        if stash.get("state") in ("pending", "saved"):
            reasons.append(f"stash {stash['state']}")
        if stash.get("drift"):  # RF-3: restored bytes that are not the operator's raw bytes
            reasons.append("stash restored with drift")
            paths += [d["path"] for d in stash["drift"]]
    try:
        info = check_runs(ctx, git_root, prefix, st["branch"] if st else None, st)
    except Outcome as exc:
        return {"tree": "leftover", "reasons": reasons + [f"check unreadable: {exc.reason}"], "paths": paths}
    for summary in info["others_active"]:
        reasons.append(f"run {summary['branch']} has an active snapshot")
        for snap in summary["active_snapshots"]:
            paths += snap["paths"]
    if info["unreadable"]:
        reasons.append("unreadable run state")
    return {"tree": "leftover" if reasons else "clean", "reasons": reasons, "paths": sorted(set(paths)),
            "unreadable": info["unreadable"]}


def cmd_scope(ctx: Context, args: argparse.Namespace) -> dict:
    scope = resolve_scope(args.project_root or ctx.cwd or os.getcwd())
    owner = ctx.resolve_owner()
    if not owner:
        unavailable("no host ancestor", detail="no ancestor process runs a host executable "
                    f"({', '.join(HOST_EXECUTABLES)}); run state was not written")
    runs = runs_root(ctx)
    if norm_key(str(runs)).startswith(norm_key(scope["git_root"]) + os.sep):
        halt("run state inside repository", run_state_root=str(runs))
    now = ctx.now()
    branch = f"build-step-{datetime.datetime.fromtimestamp(now, datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}"
    st = {
        "schema": SCHEMA_RUN, "helper_version": HELPER_VERSION, "branch": branch,
        "token": secrets.token_hex(16), "created": iso(now), "created_epoch": now,
        "heartbeat": iso(now), "heartbeat_epoch": now, "owner": owner, "phase": "scoped",
        **scope, "worktree": None, "worktree_project": None, "baseline": None, "payload": None,
        "stash": {"state": "none"}, "snapshots": [], "supervisor": None, "budget_key": None,
        "finalized": None,
    }
    hold_call_lock(ctx, branch)
    run_dir(ctx, branch).mkdir(parents=True, exist_ok=False)
    save_state(ctx, st)
    return {"status": "ok", "run": branch, "token": st["token"], "run_state": str(run_dir(ctx, branch)),
            "owner": owner, **scope}


def archived_git_root(ctx: Context, branch: str) -> Optional[str]:
    """RF-8: GIT_ROOT recorded in <archive>/<branch>/landed-paths.json, or None."""
    path = ctx.root() / "build-step-archive" / branch / "landed-paths.json"
    try:
        doc = read_json(path)
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA_LANDED or doc.get("branch") != branch:
        return None
    root = doc.get("git_root")
    return root if isinstance(root, str) and root else None


def cmd_recover_check(ctx: Context, args: argparse.Namespace) -> dict:
    st = None
    if args.run:
        st = load_state(ctx, args.run, missing_ok=True)
    if st is not None:
        git_root, prefix, source = st["git_root"], st["project_prefix"], "run state"
    elif args.project_root or not args.run:
        scope = resolve_scope(args.project_root or ctx.cwd or os.getcwd())
        git_root, prefix = scope["git_root"], scope["project_prefix"]
        source = "project root" if args.project_root else "working directory"
    else:
        # RF-8 [AD]: a named run whose state is gone (cleaned up) never falls back to the ambient
        # cwd; its archive names the operator tree, listed whole (prefix `.`).
        git_root = archived_git_root(ctx, args.run)
        if git_root is None:
            halt("no run state", run=args.run,
                 detail="the run state is gone and no archive names its GIT_ROOT; pass --project-root")
        prefix, source = ".", "archive"
    caller = st
    if caller is None:
        owner = ctx.resolve_owner()
        caller = {"branch": args.run or "<this-branch>", "owner": owner} if owner else None
    info = check_runs(ctx, git_root, prefix, st["branch"] if st else args.run, caller)
    tree = compute_tree(ctx, st, git_root, prefix)
    result = {"git_root": git_root, "project_prefix": prefix, "scope_source": source, "runs": info["runs"],
              "tree": tree["tree"], "tree_reasons": tree["reasons"], "tree_paths": tree["paths"],
              "remedy": info["remedy"]}
    if info["unreadable"]:
        unavailable("run state unreadable", unreadable=info["unreadable"], **result)
    outcome = None
    if info["t2"]:
        outcome = "concurrent run active"
    elif info["t3"]:
        outcome = "unfinished prior run"
    result["outcome"] = outcome
    result["concurrent"] = info["t2"]
    result["unfinished"] = info["t3"]
    if outcome and st is not None and st.get("phase") == "scoped" and not st.get("finalized"):
        halt(outcome, **result)
    return {"status": "ok", **result}


# ---------------------------------------------------------------------------------------------
# Stash (T4, T5, T10)
# ---------------------------------------------------------------------------------------------

def stash_ref_oid(git_root: str) -> Optional[str]:
    proc = git(["rev-parse", "-q", "--verify", "refs/stash"], git_root, check=False)
    out = proc.stdout.decode().strip()
    return out if proc.returncode == 0 and out else None


def stash_entries(git_root: str) -> list:
    proc = git(["stash", "list", "-z", "--format=%H %gd %gs"], git_root, check=False)
    entries = []
    for rec in split_z(proc.stdout):
        parts = rec.split(" ", 2)
        if len(parts) == 3:
            entries.append({"oid": parts[0], "ref": parts[1], "subject": parts[2]})
    return entries


def marker_entries(git_root: str, branch: str) -> list:
    tail = f": build-step {branch}"
    return [e for e in stash_entries(git_root) if e["subject"].startswith("On ") and e["subject"].endswith(tail)]


def stash_paths(git_root: str, oid: str, prefix: str) -> list:
    """The stash entry's changed paths under PROJECT_PREFIX only (RF-4)."""
    paths = set(split_z(git(["diff", "--name-only", "-z", "--no-renames", f"{oid}^1", oid], git_root).stdout))
    paths |= set(split_z(git(["diff", "--name-only", "-z", "--no-renames", f"{oid}^1", f"{oid}^2"], git_root).stdout))
    third = git(["rev-parse", "-q", "--verify", f"{oid}^3"], git_root, check=False)
    if third.returncode == 0:
        paths |= set(split_z(git(["ls-tree", "-r", "-z", "--name-only", f"{oid}^3"], git_root).stdout))
    return sorted(p for p in paths if in_prefix(p, prefix))


def project_dirty(st: dict) -> bool:
    out = git(["status", "--porcelain=v1", "-z", "--untracked-files=all", "--",
               prefix_pathspec(st["project_prefix"])], st["git_root"]).stdout
    return bool(out.strip(b"\0"))


def prefix_status_paths(st: dict) -> list:
    """Every dirty or untracked (non-ignored) path under PROJECT_PREFIX, as `git status` lists it."""
    out = git(["status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames", "--",
               prefix_pathspec(st["project_prefix"])], st["git_root"]).stdout
    return sorted({rec[3:] for rec in split_z(out) if len(rec) > 3})


def staged_outside_prefix(st: dict) -> list:
    """Operator index entries that differ from HEAD outside PROJECT_PREFIX (RF-4)."""
    if st["project_prefix"] == ".":
        return []
    out = git(["diff", "--cached", "--name-only", "-z", "--no-renames"], st["git_root"]).stdout
    return sorted(p for p in split_z(out) if not in_prefix(p, st["project_prefix"]))


def capture_raw(ctx: Context, st: dict, rels: list) -> list:
    """RF-3: raw bytes and sha256 of each path the stash will take, kept under run state."""
    rdir = run_dir(ctx, st["branch"]) / "stash-raw"
    raw = []
    for n, rel in enumerate(rels):
        dst = fs_path(st["git_root"], rel)
        if rel.endswith("/") or os.path.isdir(dst):
            continue  # a directory entry (an untracked nested repository): git stash never takes it
        try:
            with open(dst, "rb") as handle:
                data = handle.read()
        except FileNotFoundError:
            raw.append({"path": rel, "sha256": None})
            continue
        saved = rdir / str(n)
        atomic_write_bytes(saved, data)
        raw.append({"path": rel, "sha256": sha256_bytes(data), "file": str(saved)})
    return raw


def restore_raw_bytes(ctx: Context, st: dict, raw: list) -> list:
    """RF-3: after a successful apply, give each stashed path back its raw stash-save bytes.

    Equal raw bytes: nothing to do.  Different but Git-equivalent (the same clean-filtered blob,
    for example autocrlf turning an LF file into CRLF): the saved bytes are written back
    atomically.  Anything else is drift: the saved bytes are kept under leftovers/stash/ and the
    path is reported; nothing else is written."""
    root = st["git_root"]
    ldir = run_dir(ctx, st["branch"]) / "leftovers" / "stash"
    drift = []
    for n, rec in enumerate(raw):
        rel, want = rec["path"], rec.get("sha256")
        dst = fs_path(root, rel)
        cur = raw_state(dst)
        if cur == want:
            continue
        why = None
        if want is not None and cur is not None and cur != "dir" and not cur.startswith("link:"):
            with open(rec["file"], "rb") as handle:
                saved = handle.read()
            try:
                same = hash_object_bytes(root, rel, saved) == hash_object(root, rel)
            except GitError as exc:
                same, why = False, f"hash-object failed: {exc.stderr}"
            if same:
                try:
                    replace_bytes(dst, saved)
                except OSError as exc:
                    why = f"write-back failed: {exc}"
                else:
                    if raw_state(dst) == want:
                        continue
                    why = "write-back did not take"
            elif why is None:
                why = "content differs from the bytes saved at stash-save"
        else:
            why = "expected absent" if want is None else f"unexpected current state ({cur or 'absent'})"
        item = {"path": rel, "saved_sha256": want, "current_sha256": cur, "why": why}
        if rec.get("file"):
            ldir.mkdir(parents=True, exist_ok=True)
            item["saved"] = str(ldir / f"{n}.saved")
            shutil.copyfile(rec["file"], item["saved"])
        drift.append(item)
    return drift


def resolve_pending(ctx: Context, st: dict) -> None:
    """T5: a pending stash becomes saved (one marker entry), none (zero) or halts (several)."""
    stash = st.get("stash") or {}
    if stash.get("state") != "pending":
        return
    found = marker_entries(st["git_root"], st["branch"])
    if len(found) > 1:
        halt("several stash entries carry this run's marker", entries=found,
             remedy=[f"inspect `git stash list`, then {remedy_cmd('recover', st['branch'], '--stash-resolved')}"])
    if len(found) == 1:
        oid = found[0]["oid"]
        st["stash"] = {"state": "saved", "oid": oid,
                       "paths": stash_paths(st["git_root"], oid, st["project_prefix"]),
                       "raw": stash.get("raw", []), "resolved_from": "pending"}
    else:
        st["stash"] = {"state": "none", "resolved_from": "pending"}
    save_state(ctx, st)


def cmd_stash_save(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    stash = st.get("stash") or {}
    if stash.get("state", "none") != "none":
        halt("stash already recorded", stash=stash)
    if active_snapshots(st):  # RX-1 [AD]: T4 is valid only before any preview or landing is active
        halt("stash failed", detail="active snapshot", snapshots=[s["id"] for s in active_snapshots(st)])
    if not project_dirty(st):
        return {"status": "ok", "stashed": False, "stash": st["stash"]}
    acquire_lock(ctx, st, "tree")
    try:
        acquire_stash_lock(ctx, st)  # R2-3: never push without the tree lock
    except Outcome:
        release_tree_if_inactive(st)
        raise
    root, prefix = st["git_root"], st["project_prefix"]
    try:
        stash = st.get("stash") or {}
        if active_snapshots(st):  # RX-1: safety checks precede benign state/dirty early returns after the wait
            halt("stash failed", detail="active snapshot", snapshots=[s["id"] for s in active_snapshots(st)])
        if stash.get("state", "none") != "none":  # RF-5: re-validated on state reloaded after a lock wait
            halt("stash already recorded", stash=stash)
        rels = prefix_status_paths(st)
        links = links_on_paths(root, rels)
        if links:  # RF-2: git stash would delete through the link and restore a plain directory
            halt("stash failed", links=links, stash=st["stash"],
                 detail="a dirty or untracked path under the project prefix, or one of its directories, is a "
                        "symlink, junction or reparse point; nothing was stashed")
        outside = staged_outside_prefix(st)
        if outside:  # RF-4: the stash index commit would carry them and `apply --index` could not restore exactly
            halt("stash failed", staged_outside_prefix=outside, stash=st["stash"],
                 detail="the operator index has staged changes outside the project prefix; nothing was stashed")
        raw = capture_raw(ctx, st, rels)
    except BaseException:
        release_lock(st, "stash")
        release_tree_if_inactive(st)
        raise
    before = stash_ref_oid(root)
    st["stash"] = {"state": "pending", "pre_ref": before, "raw": raw}
    save_state(ctx, st)
    proc = git(["stash", "push", "--include-untracked", "-m", f"build-step {st['branch']}", "--",
                prefix_pathspec(prefix)], root, check=False)
    _fault(ctx, "after-stash-push")
    after = stash_ref_oid(root)
    subject = ""
    if after:
        subject = git_out(["log", "-1", "--format=%s", "refs/stash"], root)
    try:
        if after and after != before and subject.startswith("On ") and subject.endswith(f": build-step {st['branch']}"):
            st["stash"] = {"state": "saved", "oid": after, "paths": stash_paths(root, after, prefix), "raw": raw}
            save_state(ctx, st)
            if project_dirty(st):
                halt("stash failed", detail="project paths still dirty after the stash", stash=st["stash"])
            return {"status": "ok", "stashed": True, "stash": st["stash"]}
        if after == before:
            st["stash"] = {"state": "none"}
            save_state(ctx, st)
            halt("stash failed", detail=proc.stderr.decode("utf-8", "replace").strip())
        halt("stash failed", detail="refs/stash changed without this run's marker; stash left pending",
             stash=st["stash"])
    finally:
        release_lock(st, "stash")
        release_tree_if_inactive(st)


def restore_stash(ctx: Context, st: dict, *, in_recover: bool) -> dict:
    """T10 (after T5).  Returns a result fragment or raises halt."""
    resolve_pending(ctx, st)
    stash = st.get("stash") or {}
    if stash.get("state") != "saved":
        return {"stash": stash, "restored": False}
    if active_snapshots(st):
        halt("active snapshot", detail="stash restore refused while a snapshot is active (AV-20)",
             snapshots=[s["id"] for s in active_snapshots(st)])
    acquire_lock(ctx, st, "tree", allow_finalized=in_recover)
    try:
        acquire_stash_lock(ctx, st, allow_finalized=in_recover)  # R2-3: never apply without the tree lock
    except Outcome:
        release_tree_if_inactive(st)
        raise
    try:
        stash = st.get("stash") or {}  # RF-5: re-validated on state reloaded after a lock wait
        if active_snapshots(st):
            halt("active snapshot", detail="stash restore refused while a snapshot is active (AV-20)",
                 snapshots=[s["id"] for s in active_snapshots(st)])
        if stash.get("state") != "saved":
            return {"stash": stash, "restored": False}
        root, oid, branch = st["git_root"], stash["oid"], st["branch"]
        remedy = [remedy_cmd("recover", branch), remedy_cmd("recover", branch, "--stash-resolved")]
        entry = next((e for e in stash_entries(root) if e["oid"] == oid), None)
        if entry is None:
            halt("recover halted: stash restore failed" if in_recover else "restore failed",
                 detail="no stash entry carries the recorded object id", oid=oid, paths=stash.get("paths"),
                 remedy=[remedy_cmd("recover", branch, "--stash-resolved")])
        proc = git(["stash", "apply", "--index", oid], root, check=False)
        if proc.returncode != 0:
            halt("recover halted: stash restore failed" if in_recover else "restore failed",
                 entry=entry["ref"], oid=oid, paths=stash.get("paths"),
                 detail=(proc.stderr + proc.stdout).decode("utf-8", "replace").strip()[-2000:],
                 remedy=remedy)
        result: dict = {"restored": True, "oid": oid}
        current = next((e for e in stash_entries(root) if e["oid"] == oid), None)
        stale = None
        if current is None:
            stale = "entry vanished before drop"
        else:
            drop = git(["stash", "drop", current["ref"]], root, check=False)
            text = drop.stdout.decode("utf-8", "replace")
            m = re.search(r"\(([0-9a-f]{40,64})\)", text)
            if drop.returncode != 0:
                stale = f"drop failed: {drop.stderr.decode('utf-8', 'replace').strip()}"
            elif m and m.group(1) != oid:
                git(["stash", "store", "-m", "restored by build-step after a mismatched drop", m.group(1)], root,
                    check=False)
                stale = f"dropped a different entry ({m.group(1)}); it was re-stored"
        drift = restore_raw_bytes(ctx, st, stash.get("raw") or [])  # RF-3
        st["stash"] = {"state": "restored", "oid": oid, "paths": stash.get("paths", [])}
        if drift:
            st["stash"]["drift"] = drift
        save_state(ctx, st)
        if stale:
            result["stale_entry"] = {"oid": oid, "note": stale}
        if drift:
            halt("recover halted: stash restored with drift" if in_recover else "restore failed",
                 drift=drift, oid=oid, stash=st["stash"], stale_entry=result.get("stale_entry"),
                 detail="the stash was applied (and dropped), but these paths differ from the bytes saved at "
                        "stash-save in a way Git does not treat as equivalent; their saved bytes are kept and "
                        "nothing was re-applied")
        return result
    finally:
        release_lock(st, "stash")
        release_tree_if_inactive(st)


def cmd_stash_restore(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    return {"status": "ok", **restore_stash(ctx, st, in_recover=False), "stash": st.get("stash")}


# ---------------------------------------------------------------------------------------------
# Worktree, payload, tree-hash
# ---------------------------------------------------------------------------------------------

def cmd_worktree_create(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    if st.get("worktree"):
        halt("worktree already created", worktree=st["worktree"])
    root = st["git_root"]
    head = git(["rev-parse", "--verify", "HEAD^{commit}"], root, check=False)
    if head.returncode != 0:
        halt("no baseline commit", detail="HEAD does not resolve to a commit")
    baseline = head.stdout.decode().strip()
    path = os.path.join(os.path.dirname(os.path.normpath(root)), f"worktree_{st['branch']}")
    if norm_key(path).startswith(norm_key(root) + os.sep):
        halt("worktree path inside GIT_ROOT", worktree=path)
    if os.path.lexists(path):
        halt("worktree path exists", worktree=path)
    git(["worktree", "add", "-b", st["branch"], path, baseline], root)
    project = path if st["project_prefix"] == "." else os.path.join(path, *st["project_prefix"].rstrip("/").split("/"))
    st.update({"worktree": path, "worktree_project": project, "baseline": baseline, "phase": "isolated"})
    save_state(ctx, st)
    return {"status": "ok", "worktree": path, "worktree_project": project, "baseline": baseline,
            "branch": st["branch"]}


def _is_orchestrator(rel: str, prefix: str) -> bool:
    proj = rel if prefix == "." else rel[len(prefix.rstrip("/")) + 1:]
    first = proj.split("/", 1)[0]
    return first in ORCHESTRATOR_DIRS


def build_payload(ctx: Context, st: dict, tag: str) -> dict:
    """Compute the payload from the child worktree in temporary indexes (AV-29)."""
    wt, base, prefix = st["worktree"], st["baseline"], st["project_prefix"]
    rdir = run_dir(ctx, st["branch"])
    idx1, idx2 = rdir / f"{tag}.audit.index", rdir / f"{tag}.payload.index"
    for p in (idx1, idx2):
        if p.exists():
            p.unlink()
    try:
        # The audit index carries the child index's entries (commits + staged, force-added paths
        # included) but NO stat data, so `add -A` content-hashes every tracked file: a copied
        # index would trust stale stat data (racy-clean same-size edits would be missed).
        entries_z = git(["ls-files", "-s", "-z"], wt).stdout
        env1 = {"GIT_INDEX_FILE": str(idx1)}
        git(["read-tree", "--empty"], wt, env=env1)
        if entries_z:
            git(["update-index", "-z", "--index-info"], wt, env=env1, input=entries_z)
        git(["add", "-A"], wt, env=env1)
        raw = git(["diff", "--cached", "--raw", "-z", "--no-renames", "--no-abbrev", base], wt, env=env1).stdout
        recs = raw.split(b"\0")
        changes = []
        i = 0
        while i < len(recs) - 1:
            meta = recs[i].decode("ascii", "replace")
            if not meta.startswith(":"):
                i += 1
                continue
            path = recs[i + 1].decode("utf-8", "surrogateescape")
            old_mode, new_mode, old_oid, new_oid, status = meta[1:].split(" ")
            changes.append({"path": path, "old_mode": old_mode, "new_mode": new_mode, "old_oid": old_oid,
                            "new_oid": new_oid, "status": status})
            i += 2
        escaped = sorted(c["path"] for c in changes if not in_prefix(c["path"], prefix))
        if escaped:
            return {"escape": escaped}
        payload = [c for c in changes if not _is_orchestrator(c["path"], prefix)]
        unsafe = sorted(c["path"] for c in payload if not safe_rel(c["path"]))
        if unsafe:
            halt("unsafe path in payload", paths=unsafe)
        unsupported = sorted(c["path"] for c in payload
                             if c["new_mode"] in ("120000", "160000") or c["old_mode"] in ("120000", "160000"))
        if unsupported:
            halt("unsupported path type", detail="symlink or submodule change in the payload", paths=unsupported)
        env2 = {"GIT_INDEX_FILE": str(idx2)}
        git(["read-tree", base], wt, env=env2)
        info = b""
        for c in payload:
            if c["new_mode"] == "000000":
                info += f"0 {zero_oid(c['old_oid'])}\t".encode() + c["path"].encode("utf-8", "surrogateescape") + b"\0"
            else:
                info += f"{c['new_mode']} {c['new_oid']}\t".encode() + c["path"].encode("utf-8", "surrogateescape") + b"\0"
        if info:
            git(["update-index", "-z", "--index-info"], wt, env=env2, input=info)
        tree = git_out(["write-tree"], wt, env=env2)
        patch = git(["-c", "core.quotepath=on", "-c", "diff.noprefix=false", "-c", "diff.relative=false",
                     "-c", "diff.suppressBlankEmpty=false", "diff", "--binary", "--full-index", "--no-renames",
                     "--no-ext-diff", "--no-textconv", "--no-color", "--diff-algorithm=myers",
                     "--src-prefix=a/", "--dst-prefix=b/", base, tree], wt).stdout
        entries = []
        for c in sorted(payload, key=lambda c: c["path"]):
            entries.append({
                "path": c["path"],
                "old": None if c["old_mode"] == "000000" else {"mode": c["old_mode"], "oid": c["old_oid"]},
                "new": None if c["new_mode"] == "000000" else {"mode": c["new_mode"], "oid": c["new_oid"]},
            })
        return {"tree": tree, "patch": patch, "sha256": sha256_bytes(patch), "entries": entries}
    finally:
        for p in (idx1, idx2):
            try:
                p.unlink()
            except OSError:
                pass


def cmd_changes(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    if not st.get("worktree"):
        halt("no worktree", detail="run worktree-create first")
    built = build_payload(ctx, st, "changes")
    if "escape" in built:
        raise Outcome("scope-escape", "scope escape", paths=built["escape"],
                      project_prefix=st["project_prefix"], worktree=st["worktree"])
    patch_path = run_dir(ctx, st["branch"]) / "payload.patch"
    atomic_write_bytes(patch_path, built["patch"])
    st["payload"] = {"sha256": built["sha256"], "tree": built["tree"], "patch": str(patch_path),
                     "entries": built["entries"]}
    save_state(ctx, st)
    paths = [e["path"] for e in built["entries"]]
    return {"status": "ok", "empty": not paths, "paths": paths, "files": len(paths),
            "payload_sha256": built["sha256"], "payload_tree": built["tree"], "patch": str(patch_path)}


def cmd_tree_hash(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    if not st.get("worktree"):
        halt("no worktree")
    wt, prefix = st["worktree"], st["project_prefix"]
    listed = split_z(git(["ls-files", "-z", "--cached", "--others", "--exclude-standard", "--",
                          prefix_pathspec(prefix)], wt).stdout)
    lines = []
    for rel in sorted(set(listed)):
        if _is_orchestrator(rel, prefix):
            continue
        lines.append(f"W\0{rel}\0{raw_state(fs_path(wt, rel))}")
    for entry in (st.get("payload") or {}).get("entries", []):
        lines.append(f"O\0{entry['path']}\0{raw_state(fs_path(st['git_root'], entry['path']))}")
    digest = sha256_bytes("\n".join(lines).encode("utf-8", "surrogateescape"))
    return {"status": "ok", "tree_hash": digest, "files": len(lines)}


# ---------------------------------------------------------------------------------------------
# Snapshots, preview, landing, rollback (T6-T9)
# ---------------------------------------------------------------------------------------------

def _require_payload(st: dict) -> dict:
    payload = st.get("payload")
    if not payload:
        halt("no payload", detail="run changes first")
    return payload


def _prior_state(git_root: str, rel: str, idx: dict) -> dict:
    dst = fs_path(git_root, rel)
    exists = os.path.lexists(dst)
    tracked = rel in idx
    if exists and dst.is_dir() and not os.path.islink(dst):
        halt("directory in the way", path=rel)
    kind = ("tracked" if exists else "tracked-deleted") if tracked else ("untracked" if exists else "absent")
    return {"kind": kind, "sha256": raw_state(dst) if exists else None,
            "index": idx.get(rel), "exec": bool(exists and os.access(dst, os.X_OK)) if not IS_WINDOWS else False}


def _new_snapshot(ctx: Context, st: dict, kind: str, plan: list) -> dict:
    """plan: [(rel, desired_bytes or None)].  Records prior states; returns the active snapshot."""
    root = st["git_root"]
    n = len(st.get("snapshots", [])) + 1
    sid = f"{kind}-{n}"
    sdir = run_dir(ctx, st["branch"]) / "snapshots" / sid
    (sdir / "prior").mkdir(parents=True, exist_ok=True)
    (sdir / "written").mkdir(parents=True, exist_ok=True)
    idx = index_map(root)
    entries = []
    for i, (rel, data) in enumerate(plan):
        prior = _prior_state(root, rel, idx)
        if prior["sha256"] is not None:
            shutil.copyfile(fs_path(root, rel), sdir / "prior" / str(i))
            prior["file"] = str(sdir / "prior" / str(i))
        written = {"sha256": None if data is None else sha256_bytes(data), "blob": None, "index": prior["index"]}
        if data is not None:
            atomic_write_bytes(sdir / "written" / str(i), data)
            written["file"] = str(sdir / "written" / str(i))
        entries.append({"n": i, "path": rel, "prior": prior, "written": written, "status": "pending"})
    snap = {"id": sid, "kind": kind, "lifecycle": "active", "created": iso(ctx.now()), "dir": str(sdir),
            "entries": entries, "created_dirs": [], "leftovers": []}
    st.setdefault("snapshots", []).append(snap)
    save_state(ctx, st)
    return snap


def _write_entry(st: dict, snap: dict, entry: dict, exec_bit: bool) -> None:
    dst = fs_path(st["git_root"], entry["path"])
    if entry["written"]["sha256"] is None:
        if os.path.lexists(dst):
            os.unlink(dst)
    else:
        parent = dst.parent
        missing = []
        while not parent.exists():
            missing.append(str(parent))
            parent = parent.parent
        for d in reversed(missing):
            os.mkdir(d)
            snap["created_dirs"].append(d)
        with open(entry["written"]["file"], "rb") as src:
            data = src.read()
        tmp = dst.with_name(f".{dst.name}.bst-{secrets.token_hex(4)}")
        with open(tmp, "wb") as handle:
            handle.write(data)
        if not IS_WINDOWS:
            os.chmod(tmp, 0o755 if exec_bit else 0o644)
        os.replace(tmp, dst)
    entry["status"] = "written"


def _payload_bytes(st: dict, entry: dict) -> Optional[bytes]:
    if entry["new"] is None:
        return None
    return worktree_form(st["git_root"], entry["path"], entry["new"]["oid"])


def cmd_preview_apply(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    payload = _require_payload(st)
    if active_snapshots(st):
        halt("active snapshot", snapshots=[s["id"] for s in active_snapshots(st)])
    acquire_lock(ctx, st, "tree")
    try:
        if active_snapshots(st):  # RF-5: re-validated on state reloaded after a lock wait
            halt("active snapshot", snapshots=[s["id"] for s in active_snapshots(st)])
        payload = _require_payload(st)
        plan = [(e["path"], _payload_bytes(st, e)) for e in payload["entries"]]
        snap = _new_snapshot(ctx, st, "preview", plan)
    except BaseException:
        release_tree_if_inactive(st)
        raise
    by_path = {e["path"]: e for e in payload["entries"]}
    for entry in snap["entries"]:
        new = by_path[entry["path"]]["new"]
        _write_entry(st, snap, entry, bool(new and new["mode"] == "100755"))
        save_state(ctx, st)
    return {"status": "ok", "snapshot": snap["id"], "paths": snapshot_paths(snap)}


def rollback_snapshot(ctx: Context, st: dict, snap: dict) -> list:
    """T7.  Returns the leftover list (empty when rolled back)."""
    if snap.get("lifecycle") != "active":
        return []
    root = st["git_root"]
    ldir = run_dir(ctx, st["branch"]) / "leftovers" / snap["id"]
    leftovers = []
    for entry in snap["entries"]:
        if entry.get("status") == "kept":
            continue
        dst = fs_path(root, entry["path"])
        cur = raw_state(dst)
        prior, written = entry["prior"], entry["written"]
        if cur == written["sha256"]:
            if prior["sha256"] is None:
                if os.path.lexists(dst):
                    os.unlink(dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                with open(prior["file"], "rb") as src:
                    data = src.read()
                tmp = dst.with_name(f".{dst.name}.bst-{secrets.token_hex(4)}")
                with open(tmp, "wb") as handle:
                    handle.write(data)
                if not IS_WINDOWS:
                    os.chmod(tmp, 0o755 if prior.get("exec") else 0o644)
                os.replace(tmp, dst)
            entry["status"] = "restored"
        elif cur == prior["sha256"]:
            entry["status"] = "done"
        else:
            ldir.mkdir(parents=True, exist_ok=True)
            saved = {}
            if prior.get("file"):
                saved["prior"] = str(ldir / f"{entry['n']}.prior")
                shutil.copyfile(prior["file"], saved["prior"])
            if written.get("file"):
                saved["written"] = str(ldir / f"{entry['n']}.written")
                shutil.copyfile(written["file"], saved["written"])
            entry["status"] = "leftover"
            leftovers.append({"path": entry["path"], "current_sha256": cur, "prior_sha256": prior["sha256"],
                              "written_sha256": written["sha256"], "saved": saved})
    for d in sorted(snap.get("created_dirs", []), key=len, reverse=True):
        try:
            os.rmdir(d)
        except OSError:
            pass
    snap["leftovers"] = leftovers
    if not leftovers:
        snap["lifecycle"] = "rolled-back"
    save_state(ctx, st)
    release_tree_if_inactive(st)
    return leftovers


def _rollback_kind(ctx: Context, st: dict, kind: str) -> dict:
    snaps = [s for s in active_snapshots(st) if s["kind"] == kind]
    if not snaps:
        release_tree_if_inactive(st)
        return {"status": "ok", "noop": True, "detail": f"no active {kind} snapshot"}
    leftovers = []
    for snap in snaps:
        leftovers += rollback_snapshot(ctx, st, snap)
    if leftovers:
        halt("rollback failed", leftovers=leftovers, snapshots=[s["id"] for s in snaps],
             remedy=[remedy_cmd("recover", st["branch"], "--keep-current", *[l["path"] for l in leftovers])])
    return {"status": "ok", "rolled_back": [s["id"] for s in snaps]}


def cmd_preview_rollback(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    return _rollback_kind(ctx, st, "preview")


def cmd_land_rollback(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    return _rollback_kind(ctx, st, "landing")


def _classify_landing(ctx: Context, st: dict, payload: dict) -> tuple:
    """Pure read: returns ([(rel, bytes|None, exec)], conflicts)."""
    root, base = st["git_root"], st["baseline"]
    idx = index_map(root)
    rdir = run_dir(ctx, st["branch"]) / "merge"
    plan, conflicts = [], []
    for e in payload["entries"]:
        rel, new, old = e["path"], e["new"], e["old"]
        dst = fs_path(root, rel)
        exists = os.path.lexists(dst)
        if exists and dst.is_dir() and not os.path.islink(dst):
            conflicts.append({"path": rel, "why": "directory in the way"})
            continue
        exec_bit = bool(new and new["mode"] == "100755")
        if rel in idx:
            ient = idx[rel]
            cur_blob = hash_object(root, rel) if exists else None
            changed = old is None or ient["oid"] != old["oid"] or ient["stage"] != "0" or cur_blob != old["oid"]
            if not changed:
                plan.append((rel, None if new is None else worktree_form(root, rel, new["oid"]), exec_bit))
                continue
            if new is None:
                if not exists:
                    plan.append((rel, None, False))  # deleted on both sides
                else:
                    conflicts.append({"path": rel, "why": "payload deletes a file the operator tree changed"})
                continue
            if not exists:
                conflicts.append({"path": rel, "why": "operator tree deleted a file the payload changes"})
                continue
            theirs = worktree_form(root, rel, new["oid"])
            with open(dst, "rb") as handle:
                ours = handle.read()
            if old is None:
                if ours == theirs:
                    plan.append((rel, theirs, exec_bit))
                else:
                    conflicts.append({"path": rel, "why": "both sides added different content"})
                continue
            basebytes = worktree_form(root, rel, old["oid"])
            rdir.mkdir(parents=True, exist_ok=True)
            tag = secrets.token_hex(4)
            fo, fb, ft = rdir / f"{tag}.ours", rdir / f"{tag}.base", rdir / f"{tag}.theirs"
            fo.write_bytes(ours)
            fb.write_bytes(basebytes)
            ft.write_bytes(theirs)
            proc = git(["merge-file", "-p", str(fo), str(fb), str(ft)], root, check=False)
            for f in (fo, fb, ft):
                try:
                    f.unlink()
                except OSError:
                    pass
            if proc.returncode == 0:
                plan.append((rel, proc.stdout, exec_bit))
            else:
                why = "merge conflict" if 0 < proc.returncode < 128 else "merge-file failed (binary or error)"
                conflicts.append({"path": rel, "why": why})
        else:
            if exists:
                conflicts.append({"path": rel, "why": "untracked path collides with an operator-tree file"})
            elif old is not None:
                if new is None:
                    plan.append((rel, None, False))
                else:
                    conflicts.append({"path": rel, "why": "operator tree removed a file the payload changes"})
            elif new is not None:
                plan.append((rel, worktree_form(root, rel, new["oid"]), exec_bit))
    return plan, conflicts


def cmd_land(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    payload = _require_payload(st)
    if active_snapshots(st):
        halt("active snapshot", snapshots=[s["id"] for s in active_snapshots(st)])
    resolve_pending(ctx, st)  # T5 before the Step 8.2 overlap check
    stash = st.get("stash") or {}
    if stash.get("state") == "saved":
        overlap = sorted(set(stash.get("paths", [])) & {e["path"] for e in payload["entries"]})
        if overlap:
            halt("merge conflict", detail="stashed operator paths overlap the payload (Step 8.2)",
                 overlap=overlap, stash_state=stash.get("state"))
    first = build_payload(ctx, st, "land1")
    if "escape" in first or first["sha256"] != payload["sha256"]:
        halt("payload changed after review", stage="before-lock", lock_taken=False)
    acquire_lock(ctx, st, "tree")
    try:
        # RF-5: after a lock wait the state was reloaded (and a finalized run already refused);
        # re-validate the preconditions on it before any snapshot or write.
        if active_snapshots(st):
            halt("active snapshot", snapshots=[s["id"] for s in active_snapshots(st)])
        if (st.get("payload") or {}).get("sha256") != payload["sha256"]:
            release_tree_if_inactive(st)
            halt("payload changed after review", stage="under-lock", lock_taken=True, lock_released=True)
        stash = st.get("stash") or {}
        if stash.get("state") in ("pending", "saved"):
            resolve_pending(ctx, st)
            stash = st.get("stash") or {}
            overlap = sorted(set(stash.get("paths", [])) & {e["path"] for e in payload["entries"]})
            if stash.get("state") == "saved" and overlap:
                release_tree_if_inactive(st)
                halt("merge conflict", detail="stashed operator paths overlap the payload (Step 8.2)",
                     overlap=overlap, stash_state=stash.get("state"))
        second = build_payload(ctx, st, "land2")
        if "escape" in second or second["sha256"] != payload["sha256"]:
            release_tree_if_inactive(st)
            halt("payload changed after review", stage="under-lock", lock_taken=True, lock_released=True)
        plan, conflicts = _classify_landing(ctx, st, payload)
        if conflicts:
            release_tree_if_inactive(st)
            halt("merge conflict", conflicts=conflicts, written=False)
        snap = _new_snapshot(ctx, st, "landing", [(rel, data) for rel, data, _x in plan])
    except Outcome:
        release_tree_if_inactive(st)
        raise
    except BaseException:
        release_tree_if_inactive(st)
        raise
    exec_bits = {rel: x for rel, _d, x in plan}
    _fault(ctx, "land-after-snapshot")
    try:
        for entry in snap["entries"]:
            _write_entry(st, snap, entry, exec_bits[entry["path"]])
            if entry["written"]["sha256"] is not None:
                entry["written"]["blob"] = hash_object(st["git_root"], entry["path"])
            save_state(ctx, st)
    except Outcome:
        raise
    except Exception as exc:
        save_state(ctx, st)
        halt("land failed", detail=str(exc), snapshot=snap["id"])
    return {"status": "ok", "snapshot": snap["id"], "landed": [
        {"path": e["path"], "state": e["written"]["blob"] or "deleted"} for e in snap["entries"]]}


def cmd_verify_landed(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    snaps = [s for s in active_snapshots(st) if s["kind"] == "landing"]
    if not snaps:
        released = [s for s in st.get("snapshots", []) if s["kind"] == "landing" and s["lifecycle"] == "released"]
        if released:
            return {"status": "ok", "noop": True, "released": released[-1]["id"]}
        halt("no active landing")
    snap = snaps[-1]
    mismatched = []
    for entry in snap["entries"]:
        if raw_state(fs_path(st["git_root"], entry["path"])) != entry["written"]["sha256"]:
            mismatched.append(entry["path"])
    if mismatched:
        halt("landing verification failed", paths=mismatched, snapshot=snap["id"])
    snap["lifecycle"] = "released"
    snap["released"] = iso(ctx.now())
    save_state(ctx, st)
    release_tree_if_inactive(st)
    return {"status": "ok", "released": snap["id"], "paths": snapshot_paths(snap)}


# ---------------------------------------------------------------------------------------------
# Ship gate
# ---------------------------------------------------------------------------------------------

def cmd_ship_gate(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    root, base = st["git_root"], st.get("baseline")
    if not base:
        halt("no baseline", detail="run worktree-create first")
    remotes = git_out(["remote"], root).split()
    if "origin" not in remotes:
        unavailable("no remote", detail="no origin remote; shipgate=not-checked")
    fetch = git(["fetch", "origin", "--quiet"], root, check=False)
    if fetch.returncode != 0:
        halt("ship-gate fetch failed", detail=fetch.stderr.decode("utf-8", "replace").strip())
    default = None
    sym = git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], root, check=False)
    if sym.returncode == 0 and sym.stdout.strip():
        default = sym.stdout.decode().strip()
        default = default[len("origin/"):] if default.startswith("origin/") else default
    else:
        found = [b for b in ("main", "master")
                 if git(["rev-parse", "-q", "--verify", f"refs/remotes/origin/{b}"], root, check=False).returncode == 0]
        if len(found) == 1:
            default = found[0]
    if not default:
        unavailable("no default branch", detail="origin/HEAD unset and no single origin/main|master")
    remote_ref = f"refs/remotes/origin/{default}"
    new = git_out(["rev-list", f"{base}..{remote_ref}"], root).split()
    if not new:
        return {"status": "ok", "advanced": False, "default_branch": default}
    mb = git_out(["merge-base", base, remote_ref], root)
    advanced = set(split_z(git(["diff", "--name-only", "-z", "--no-renames", mb, remote_ref], root).stdout))
    payload_paths = {e["path"] for e in (st.get("payload") or {}).get("entries", [])}
    overlap = sorted(advanced & payload_paths)
    commits = git_out(["log", "--oneline", f"{base}..{remote_ref}"], root).splitlines()
    if overlap:
        halt("SHIP_GATE_HALT", sentinel=f"SHIP_GATE_HALT: origin/{default} advanced with overlapping files "
             f"since {base}", commits=commits, overlap=overlap, default_branch=default)
    return {"status": "ok", "advanced": True, "overlap": [], "commits": commits, "default_branch": default}


# ---------------------------------------------------------------------------------------------
# App supervisor (job object / process group) and ports
# ---------------------------------------------------------------------------------------------

if IS_WINDOWS:
    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [(n, ctypes.c_ulonglong) for n in ("r", "w", "o", "rb", "wb", "ob")]

    class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION), ("IoInfo", _IO_COUNTERS),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    class _JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
        _fields_ = [("TotalUserTime", ctypes.c_longlong), ("TotalKernelTime", ctypes.c_longlong),
                    ("ThisPeriodTotalUserTime", ctypes.c_longlong), ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
                    ("TotalPageFaultCount", wintypes.DWORD), ("TotalProcesses", wintypes.DWORD),
                    ("ActiveProcesses", wintypes.DWORD), ("TotalTerminatedProcesses", wintypes.DWORD)]

    _k32.CreateJobObjectW.restype = wintypes.HANDLE
    _k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    _k32.OpenJobObjectW.restype = wintypes.HANDLE
    _k32.OpenJobObjectW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    _k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    _k32.SetInformationJobObject.restype = wintypes.BOOL
    _k32.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
                                               ctypes.c_void_p]
    _k32.QueryInformationJobObject.restype = wintypes.BOOL
    _k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    _k32.AssignProcessToJobObject.restype = wintypes.BOOL
    _k32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _k32.TerminateJobObject.restype = wintypes.BOOL
    _k32.GetCurrentProcess.restype = wintypes.HANDLE
    _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
    _JOB_TERMINATE_QUERY = 0x0008 | 0x0004

    def _job_active(handle: Any) -> int:
        info = _JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
        if not _k32.QueryInformationJobObject(handle, 1, ctypes.byref(info), ctypes.sizeof(info), None):
            return -1
        return int(info.ActiveProcesses)


def _url_port(url: Optional[str]) -> Optional[tuple]:
    if not url:
        return None
    parts = urllib.parse.urlsplit(url)
    if not parts.hostname:
        return None
    port = parts.port or (443 if parts.scheme == "https" else 80)
    return (parts.hostname, port)


def port_bound(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def port_pids(port: int) -> list:
    if not IS_WINDOWS:
        return []
    pids = set()
    try:
        iphlp = ctypes.WinDLL("iphlpapi")
        for family, row_size, port_off, pid_off in ((2, 24, 8, 20), (23, 56, 20, 52)):
            size = wintypes.DWORD(0)
            iphlp.GetExtendedTcpTable(None, ctypes.byref(size), False, family, 3, 0)
            buf = ctypes.create_string_buffer(size.value + 64)
            size = wintypes.DWORD(len(buf))
            if iphlp.GetExtendedTcpTable(buf, ctypes.byref(size), False, family, 3, 0) != 0:
                continue
            raw = buf.raw
            count = int.from_bytes(raw[0:4], "little")
            for i in range(count):
                off = 4 + i * row_size
                lport = int.from_bytes(raw[off + port_off:off + port_off + 2], "big")
                if lport == port:
                    pids.add(int.from_bytes(raw[off + pid_off:off + pid_off + 4], "little"))
    except OSError:
        return []
    return sorted(pids)


def _supervisor_running(sup: dict) -> bool:
    return process_alive(sup.get("supervisor_pid"), sup.get("supervisor_start"))


def _http_ok(url: str, need_200: bool) -> bool:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(url, timeout=2) as resp:
            return resp.status == 200 if need_200 else resp.status < 500
    except urllib.error.HTTPError as exc:
        return (not need_200) and exc.code < 500
    except (OSError, ValueError):
        return False


def cmd_app_start(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    if not args.start_cmd:
        halt("usage error", detail="--start-cmd is required")
    sup = st.get("supervisor")
    if sup and _supervisor_running(sup):
        halt("app already started", supervisor=sup)
    ports = [p for p in (_url_port(args.url), _url_port(args.ready_url)) if p]
    bound = [{"host": h, "port": p, "pids": port_pids(p)} for h, p in ports if port_bound(h, p)]
    if bound:
        halt("port in use", ports=bound)
    rdir = run_dir(ctx, st["branch"]) / "supervisor"
    rdir.mkdir(parents=True, exist_ok=True)
    stop_file, status_file = rdir / "stop", rdir / "status.json"
    for f in (stop_file, status_file):
        if f.exists():
            f.unlink()
    if args.log:
        log = os.path.abspath(args.log)
    elif st.get("worktree_project"):
        log = os.path.join(st["worktree_project"], ".build-step", "evidence", "app.log")
    else:
        log = str(rdir / "app.log")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    job_name = f"skill-mesh-build-step-{st['branch']}-{st['token'][:8]}"
    cmd = [sys.executable, SCRIPT_PATH, "_supervise", "--job-name", job_name, "--cwd", st["project_root"],
           "--log", log, "--status", str(status_file), "--stop", str(stop_file), "--command", args.start_cmd]
    kwargs: dict = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
                    "close_fds": True, "cwd": st["project_root"]}
    if IS_WINDOWS:
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | 0x08000000  # CREATE_NO_WINDOW
        try:
            proc = subprocess.Popen(cmd, creationflags=flags | 0x01000000, **kwargs)  # BREAKAWAY_FROM_JOB
        except OSError:
            proc = subprocess.Popen(cmd, creationflags=flags, **kwargs)
    else:
        proc = subprocess.Popen(cmd, start_new_session=True, **kwargs)
    deadline = time.monotonic() + 15
    status = None
    while time.monotonic() < deadline:
        if status_file.exists():
            try:
                status = read_json(status_file)
                break
            except (OSError, ValueError):
                pass
        if proc.poll() is not None:
            break
        time.sleep(0.05)
    if not status:
        halt("app start failed", detail="supervisor did not report", log=log)
    sup = {"supervisor_pid": proc.pid, "supervisor_start": process_start_time(proc.pid) or status.get("start"),
           "job_name": job_name, "pgid": status.get("pgid"), "app_pid": status.get("app_pid"), "log": log,
           "stop_file": str(stop_file), "status_file": str(status_file), "url": args.url,
           "ready_url": args.ready_url}
    st["supervisor"] = sup
    save_state(ctx, st)

    def exited() -> Optional[dict]:
        try:
            cur = read_json(status_file)
        except (OSError, ValueError):
            return None
        return cur if cur.get("state") == "exited" else None

    for url, need_200, timeout in ((args.ready_url, True, ctx.ready_timeout_seconds),
                                   (args.url, False, ctx.url_timeout_seconds)):
        if not url:
            continue
        end = time.monotonic() + timeout
        while True:
            done = exited()
            if done is not None:
                halt("app exited during startup", exit_code=done.get("exit_code"), log=log, supervisor=sup)
            if _http_ok(url, need_200):
                break
            if time.monotonic() >= end:
                halt("readiness timeout", url=url, log=log, supervisor=sup)
            time.sleep(0.25)
    return {"status": "ok", "supervisor": sup, "log": log}


def stop_supervisor(ctx: Context, st: dict) -> dict:
    sup = st.get("supervisor")
    if not sup:
        return {"stopped": False, "detail": "no recorded supervisor"}
    try:
        Path(sup["stop_file"]).touch()
    except OSError:
        pass
    if IS_WINDOWS:
        handle = _k32.OpenJobObjectW(_JOB_TERMINATE_QUERY, False, sup["job_name"])
        if handle:
            try:
                _k32.TerminateJobObject(handle, 1)
                end = time.monotonic() + 10
                while _job_active(handle) > 0 and time.monotonic() < end:
                    time.sleep(0.1)
            finally:
                _k32.CloseHandle(handle)
    else:
        import signal
        pgid = sup.get("pgid")
        if pgid:
            for sig, wait in ((signal.SIGTERM, 5.0), (signal.SIGKILL, 5.0)):
                try:
                    os.killpg(int(pgid), sig)
                except ProcessLookupError:
                    break
                end = time.monotonic() + wait
                gone = False
                while time.monotonic() < end:
                    try:
                        os.killpg(int(pgid), 0)
                    except ProcessLookupError:
                        gone = True
                        break
                    time.sleep(0.1)
                if gone:
                    break
    end = time.monotonic() + 10
    while _supervisor_running(sup) and time.monotonic() < end:
        time.sleep(0.1)
    if _supervisor_running(sup):
        halt("app stop failed", detail="supervisor still running", supervisor=sup)
    ports = [p for p in (_url_port(sup.get("url")), _url_port(sup.get("ready_url"))) if p]
    end = time.monotonic() + 5
    bound = []
    while True:
        bound = [{"host": h, "port": p, "pids": port_pids(p)} for h, p in ports if port_bound(h, p)]
        if not bound or time.monotonic() >= end:
            break
        time.sleep(0.2)
    st["supervisor"] = None
    save_state(ctx, st)
    if bound:
        halt("port still bound", ports=bound, detail="nothing outside the run's job or group was killed")
    return {"stopped": True, "log": sup.get("log")}


def cmd_app_stop(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    return {"status": "ok", **stop_supervisor(ctx, st)}


def supervise(argv: list) -> int:
    """Internal: runs detached; owns the job object / process group for the app's lifetime."""
    p = argparse.ArgumentParser(prog="_supervise")
    for flag in ("--job-name", "--cwd", "--log", "--status", "--stop", "--command"):
        p.add_argument(flag, required=True)
    a = p.parse_args(argv)
    status: dict = {"state": "starting", "supervisor_pid": os.getpid()}
    job = None
    if IS_WINDOWS:
        job = _k32.CreateJobObjectW(None, a.job_name)
        if not job:
            return 3
        info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        _k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
        if not _k32.AssignProcessToJobObject(job, _k32.GetCurrentProcess()):
            return 4
    else:
        status["pgid"] = os.getpgid(0)
    with open(a.log, "ab") as log:
        app = subprocess.Popen(a.command, shell=True, cwd=a.cwd, stdin=subprocess.DEVNULL, stdout=log,
                               stderr=subprocess.STDOUT)
        status.update({"state": "running", "app_pid": app.pid})
        atomic_write_json(Path(a.status), status)
        while True:
            code = app.poll()
            if code is not None:
                status.update({"state": "exited", "exit_code": code})
                atomic_write_json(Path(a.status), status)
                return 0
            if os.path.exists(a.stop):
                if IS_WINDOWS:
                    _k32.TerminateJobObject(job, 1)
                else:
                    import signal
                    os.killpg(os.getpgid(0), signal.SIGTERM)
                return 0
            time.sleep(0.2)


# ---------------------------------------------------------------------------------------------
# test-count
# ---------------------------------------------------------------------------------------------

_UV_VALUE_OPTS = {"--with", "--extra", "--group", "--python", "-p", "--package", "--directory", "--project",
                  "--env-file", "--with-requirements", "--index", "--index-url"}
_SEPARATORS = {"&&", "||", ";", "|", "&"}


def _tokens(command: str) -> list:
    try:
        lex = shlex.shlex(command, posix=True, punctuation_chars="&|;")
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        return command.split()


def _segments(command: str) -> list:
    segs, cur = [], []
    for tok in _tokens(command):
        if tok in _SEPARATORS:
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append(tok)
    if cur:
        segs.append(cur)
    return segs


def _strip_wrappers(tokens: list) -> list:
    t = list(tokens)
    changed = True
    while t and changed:
        changed = False
        while t and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t[0]):
            t, changed = t[1:], True
        if t and t[0] in ("cross-env", "env"):
            t, changed = t[1:], True
        if len(t) >= 2 and t[0] == "uv" and t[1] == "run":
            t = t[2:]
            while t and t[0].startswith("-"):
                t = t[2:] if t[0] in _UV_VALUE_OPTS and "=" not in t[0] else t[1:]
            changed = True
        if t and t[0] == "npx":
            t = t[1:]
            while t and t[0].startswith("-"):
                t = t[2:] if t[0] in ("-p", "--package") else t[1:]
            changed = True
        if len(t) >= 2 and t[0] in ("pnpm", "yarn") and t[1] == "exec":
            t, changed = t[2:], True
        if len(t) >= 3 and os.path.basename(t[0]).lower().removesuffix(".exe") in ("python", "python3", "py") \
                and t[1] == "-m":
            t, changed = t[2:], True
    return t


def _direct_runner(t: list) -> Optional[str]:
    if not t:
        return None
    head = os.path.basename(t[0]).lower().removesuffix(".exe").removesuffix(".cmd")
    if head in ("pytest", "py.test"):
        return "pytest"
    if head == "node" and "--test" in t[1:]:
        return "node-test"
    if head == "go" and len(t) > 1 and t[1] == "test":
        return "go"
    if head == "cargo" and len(t) > 1 and t[1] == "test":
        return "cargo"
    if head == "jest":
        return "jest"
    if head == "vitest":
        return "vitest"
    return None


def _script_ref(t: list, base: str) -> Optional[tuple]:
    """(package dir, script name) for npm/pnpm/yarn script invocations."""
    if not t:
        return None
    head = os.path.basename(t[0]).lower().removesuffix(".cmd").removesuffix(".exe")
    if head not in ("npm", "pnpm", "yarn"):
        return None
    rest = t[1:]
    pkg = base
    args = []
    i = 0
    while i < len(rest):
        tok = rest[i]
        if tok in ("--prefix", "-C", "--dir", "--cwd") and i + 1 < len(rest):
            pkg = os.path.join(base, rest[i + 1])
            i += 2
            continue
        if tok.startswith("--prefix=") or tok.startswith("--dir=") or tok.startswith("--cwd="):
            pkg = os.path.join(base, tok.split("=", 1)[1])
            i += 1
            continue
        if tok.startswith("-") and not args:
            i += 1
            continue
        args.append(tok)
        i += 1
    if not args:
        return None
    if args[0] in ("test", "t", "tst"):
        return (pkg, "test")
    if args[0] in ("run", "run-script") and len(args) > 1:
        return (pkg, args[1])
    if head == "yarn" and args[0] not in ("install", "add"):
        return (pkg, args[0])
    return None


def resolve_runner(command: str, base: str, hops: int = 0, chain: Optional[list] = None) -> dict:
    chain = list(chain or []) + [command]
    found = []
    for seg in _segments(command):
        t = _strip_wrappers(seg)
        direct = _direct_runner(t)
        if direct:
            found.append({"runner": direct, "chain": chain})
            continue
        ref = _script_ref(t, base)
        if ref is None:
            continue
        if hops >= 3:
            return {"runner": None, "recognized": False, "reason": "more than 3 script hops", "chain": chain}
        pkg_dir, name = ref
        try:
            with open(os.path.join(pkg_dir, "package.json"), "rb") as handle:
                scripts = json.loads(handle.read().decode("utf-8")).get("scripts", {})
        except (OSError, ValueError):
            return {"runner": None, "recognized": False, "reason": f"no package.json at {pkg_dir}", "chain": chain}
        script = scripts.get(name)
        if not script:
            return {"runner": None, "recognized": False, "reason": f"no script {name!r}", "chain": chain}
        sub = resolve_runner(script, pkg_dir, hops + 1, chain)
        if not sub.get("recognized"):
            return sub
        found.append({"runner": sub["runner"], "chain": sub["chain"]})
    kinds = sorted({f["runner"] for f in found})
    if len(kinds) == 1:
        return {"runner": kinds[0], "recognized": True, "chain": found[-1]["chain"]}
    if not kinds:
        return {"runner": None, "recognized": False, "reason": "no recognized runner", "chain": chain}
    return {"runner": None, "recognized": False, "reason": f"ambiguous runners {kinds}", "chain": chain}


_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def parse_counts(runner: str, text: str) -> Optional[dict]:
    text = _ANSI.sub("", text)
    lines = text.splitlines()
    if runner == "pytest":
        for line in reversed(lines):
            if not re.search(r"\bin \d+(\.\d+)?s\b", line):
                continue
            if "no tests ran" in line:
                return {"collected": 0, "passed": 0, "failed": 0}
            counts = dict((k, int(v)) for v, k in re.findall(
                r"(\d+) (passed|failed|errors?|skipped|xfailed|xpassed|deselected)", line))
            if not counts:
                continue
            errors = counts.get("error", 0) + counts.get("errors", 0)
            collected = sum(counts.get(k, 0) for k in ("passed", "failed", "skipped", "xfailed", "xpassed")) + errors
            return {"collected": collected, "passed": counts.get("passed", 0),
                    "failed": counts.get("failed", 0) + errors}
        return None
    if runner == "node-test":
        tests = [int(m) for m in re.findall(r"(?m)^\s*(?:#|\u2139)\s*tests\s+(\d+)\s*$", text)]
        passed = [int(m) for m in re.findall(r"(?m)^\s*(?:#|\u2139)\s*pass\s+(\d+)\s*$", text)]
        failed = [int(m) for m in re.findall(r"(?m)^\s*(?:#|\u2139)\s*fail\s+(\d+)\s*$", text)]
        if not tests or not passed:
            return None
        return {"collected": tests[-1], "passed": passed[-1], "failed": failed[-1] if failed else 0}
    if runner == "jest":
        for line in reversed(lines):
            m = re.match(r"^\s*Tests:\s+(.*?)(\d+) total", line)
            if m:
                parts = dict((k, int(v)) for v, k in re.findall(r"(\d+) (passed|failed|skipped|todo)", m.group(1)))
                return {"collected": int(m.group(2)), "passed": parts.get("passed", 0), "failed": parts.get("failed", 0)}
        return None
    if runner == "vitest":
        for line in reversed(lines):
            m = re.match(r"^\s*Tests\s+(.*)\((\d+)\)\s*$", line)
            if m:
                parts = dict((k, int(v)) for v, k in re.findall(r"(\d+) (passed|failed|skipped|todo)", m.group(1)))
                return {"collected": int(m.group(2)), "passed": parts.get("passed", 0), "failed": parts.get("failed", 0)}
        return None
    if runner == "go":
        p = len(re.findall(r"(?m)^\s*--- PASS:", text))
        f = len(re.findall(r"(?m)^\s*--- FAIL:", text))
        s = len(re.findall(r"(?m)^\s*--- SKIP:", text))
        if p or f or s:
            return {"collected": p + f + s, "passed": p, "failed": f}
        if re.search(r"(?m)\[no test files\]|\[no tests to run\]", text) and not re.search(r"(?m)^ok\s", text):
            return {"collected": 0, "passed": 0, "failed": 0}
        return None
    if runner == "cargo":
        found = re.findall(r"test result: \w+\. (\d+) passed; (\d+) failed; (\d+) ignored", text)
        if not found:
            return None
        p = sum(int(a) for a, _b, _c in found)
        f = sum(int(b) for _a, b, _c in found)
        i = sum(int(c) for _a, _b, c in found)
        return {"collected": p + f + i, "passed": p, "failed": f}
    return None


def cmd_test_count(ctx: Context, args: argparse.Namespace) -> dict:
    base = os.path.abspath(args.project_root or ctx.cwd or os.getcwd())
    if args.check_runner:
        res = resolve_runner(args.check_runner, base)
        return {"status": "ok", "runner": res.get("runner"), "recognized": bool(res.get("recognized")),
                "chain": res.get("chain"), "reason": res.get("reason")}
    if not args.log:
        halt("usage error", detail="--log is required with --command or --runner")
    if args.runner:
        runner = args.runner
    elif args.command:
        res = resolve_runner(args.command, base)
        if not res.get("recognized"):
            unavailable("unrecognized runner", detail=res.get("reason"), chain=res.get("chain"))
        runner = res["runner"]
    else:
        halt("usage error", detail="one of --check-runner, --command or --runner is required")
    try:
        with open(args.log, "rb") as handle:
            text = handle.read().decode("utf-8", "replace")
    except OSError as exc:
        unavailable("count unreadable", detail=f"log unreadable: {exc}", runner=runner)
    counts = parse_counts(runner, text)
    if counts is None:
        unavailable("count unreadable", runner=runner, log=args.log)
    return {"status": "ok", "runner": runner, **counts}


# ---------------------------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------------------------

def budget_path(ctx: Context, key: str) -> Path:
    if not re.match(r"^[0-9a-f]{32}$", key or ""):
        halt("invalid budget key", key=key)
    return ctx.root() / "build-step-budget" / f"{key}.json"


def cmd_budget(ctx: Context, args: argparse.Namespace) -> dict:
    action = args.action
    st = None
    if args.run:
        st = enter_run(ctx, args.run)
    if action == "read":
        if st is None:
            halt("usage error", detail="budget read needs --run")
        if args.problem_file:
            with open(args.problem_file, "rb") as handle:
                problem = handle.read()
        elif args.problem is not None:
            problem = args.problem.encode("utf-8")
        else:
            halt("usage error", detail="--problem or --problem-file is required")
        if args.max_iter is not None and args.max_iter < 1:
            halt("usage error", detail="--max-iter must be a positive integer")
        material = {"git_root": norm_key(st["git_root"]), "problem_sha256": sha256_bytes(problem)}
        if args.plan_step:
            material["plan_step"] = args.plan_step
        elif args.issue:
            material["issue"] = str(args.issue)
        else:
            material["run"] = st["branch"]
        key = sha256_bytes(json.dumps(material, sort_keys=True).encode("utf-8"))[:32]
        path = budget_path(ctx, key)
        rec = read_json(path) if path.exists() else None
        if not isinstance(rec, dict) or rec.get("schema") != SCHEMA_BUDGET:
            rec = {"schema": SCHEMA_BUDGET, "key": key, "material": material,
                   "limit": args.max_iter or DEFAULT_MAX_ITER, "consumed": 0}
        elif args.max_iter is not None:
            rec["limit"] = args.max_iter
        rec["updated"] = iso(ctx.now())
        atomic_write_json(path, rec)
        st["budget_key"] = key
        save_state(ctx, st)
    else:
        key = args.key or (st or {}).get("budget_key")
        if not key:
            halt("usage error", detail="--key or a --run with a read budget is required")
        path = budget_path(ctx, key)
        if action == "clear":
            existed = path.exists()
            if existed:
                os.unlink(path)
            return {"status": "ok", "key": key, "cleared": existed}
        if not path.exists():
            halt("no budget record", key=key)
        rec = read_json(path)
        rec["consumed"] = int(rec.get("consumed", 0)) + 1
        rec["updated"] = iso(ctx.now())
        atomic_write_json(path, rec)
    limit, consumed = int(rec["limit"]), int(rec["consumed"])
    return {"status": "ok", "key": key, "limit": limit, "consumed": consumed,
            "remaining": max(0, limit - consumed), "exhausted": consumed >= limit, "record": str(path)}


# ---------------------------------------------------------------------------------------------
# Archive, cleanup, finalize
# ---------------------------------------------------------------------------------------------

def cmd_archive(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    released = [s for s in st.get("snapshots", []) if s["kind"] == "landing" and s["lifecycle"] == "released"]
    if not released:
        halt("no released landing", detail="archive writes landed-paths.json from a released landing")
    landing = released[-1]
    adir = ctx.root() / "build-step-archive" / st["branch"]
    adir.mkdir(parents=True, exist_ok=True)
    rdir = run_dir(ctx, st["branch"])
    copied = []
    if st.get("worktree_project"):
        src = Path(st["worktree_project"]) / ".build-step"
        if src.is_dir():
            shutil.copytree(src, adir / ".build-step", dirs_exist_ok=True)
            copied.append(".build-step")
    for name in ("payload.patch", "dispatch.json"):
        if (rdir / name).exists():
            shutil.copyfile(rdir / name, adir / name)
            copied.append(name)
    if (rdir / "reviews").is_dir():
        shutil.copytree(rdir / "reviews", adir / "reviews", dirs_exist_ok=True)
        copied.append("reviews")
    doc = {"schema": SCHEMA_LANDED, "branch": st["branch"], "git_root": st["git_root"],
           "paths": [{"path": e["path"], "state": e["written"]["blob"] or "deleted"} for e in landing["entries"]]}
    landed = adir / "landed-paths.json"
    atomic_write_json(landed, doc)
    evidence = None
    if args.keep_evidence and st.get("worktree_project"):
        src = Path(st["worktree_project"]) / ".build-step" / "evidence"
        if src.is_dir():
            evidence = ctx.root() / "build-step-evidence" / st["branch"]
            shutil.copytree(src, evidence, dirs_exist_ok=True)
    return {"status": "ok", "archive": str(adir), "landed_paths": str(landed), "landed_count": len(doc["paths"]),
            "copied": copied, "evidence": str(evidence) if evidence else None}


def cmd_cleanup(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    if active_snapshots(st):
        halt("cleanup refused", detail="an active snapshot remains", snapshots=[s["id"] for s in active_snapshots(st)])
    if (st.get("stash") or {}).get("state") in ("pending", "saved"):
        halt("cleanup refused", detail="the stash is not restored", stash=st["stash"])
    drift = (st.get("stash") or {}).get("drift") or []
    if drift:  # R2-5 [AD]: the saved copies are the only copy of the operator's stash-save bytes
        halt("cleanup refused", drift=[{"path": d.get("path"), "saved": d.get("saved")} for d in drift],
             detail="the stash was restored with drift; the saved copies named in `drift` are the only copy of the "
                    "operator's stash-save bytes, so the run state, worktree and branch are kept")
    if (st.get("supervisor") or None):
        halt("cleanup refused", detail="app supervisor still recorded; run app-stop")
    root, branch, wt = st["git_root"], st["branch"], st.get("worktree")
    leftover: list = []
    links_removed: list = []
    if wt:
        if norm_key(wt).startswith(norm_key(root) + os.sep):
            halt("cleanup failed", detail="recorded worktree lies inside GIT_ROOT", leftover=[wt])
        listing = git(["worktree", "list", "--porcelain", "-z"], root).stdout.split(b"\0")
        registered, wt_branch = False, None
        current = None
        for rec in listing:
            text = rec.decode("utf-8", "surrogateescape")
            if text.startswith("worktree "):
                current = text[len("worktree "):]
            elif text.startswith("branch ") and current and norm_key(current) == norm_key(wt):
                wt_branch = text[len("branch "):]
            if current and norm_key(current) == norm_key(wt):
                registered = True
        if registered:
            if wt_branch not in (None, f"refs/heads/{branch}"):
                halt("cleanup failed", detail="recorded worktree is on another branch", leftover=[wt])
            links_removed = remove_worktree_links(wt)  # RF-1: before `worktree remove --force`
            proc = git(["worktree", "remove", "--force", wt], root, check=False)
            if proc.returncode != 0:
                leftover.append(wt)
        elif os.path.exists(wt):
            leftover.append(wt)
    if not leftover:
        exists = git(["rev-parse", "-q", "--verify", f"refs/heads/{branch}"], root, check=False).returncode == 0
        if exists and git(["branch", "-D", branch], root, check=False).returncode != 0:
            leftover.append(f"branch {branch}")
    if leftover:
        save_state(ctx, st)
        halt("cleanup failed", leftover=leftover, worktree=wt, links_removed=links_removed)
    release_lock(st, "stash")
    release_lock(st, "tree")
    rdir = run_dir(ctx, branch)
    shutil.rmtree(rdir, ignore_errors=True)
    if rdir.exists():
        halt("cleanup failed", leftover=[str(rdir)], detail="run state could not be removed")
    return {"status": "ok", "worktree_removed": wt, "branch_deleted": branch, "run_state_removed": str(rdir),
            "links_removed": links_removed}


def remove_worktree_links(wt: str) -> list:
    """RF-1 [AD]: `git worktree remove --force` deletes THROUGH a junction on Windows (for example a
    dependency install's node_modules link to an operator directory).  Walk the recorded worktree
    without following links and remove every symlink, junction or reparse point as a link, never
    its target.  A worktree root that is itself a link, an entry that cannot be inspected, or a link
    that cannot be removed as a link is `cleanup failed`, naming it; the worktree is then kept."""
    if path_is_link_like(wt):
        halt("cleanup failed", detail="the recorded worktree path is itself a link; nothing was removed",
             links=[wt], leftover=[wt])
    links, unreadable = find_links(wt)
    if unreadable:
        halt("cleanup failed", detail="worktree entries could not be inspected for links; nothing was removed",
             unreadable=unreadable, leftover=[wt])
    removed, failed = [], []
    for link in links:
        err = remove_link(link)
        if err:
            failed.append({"path": link, "error": err})
        else:
            removed.append(link)
    if not failed:
        remaining, unreadable = find_links(wt)
        failed = [{"path": p, "error": "link still present"} for p in remaining]
        failed += [{"path": p, "error": "cannot be inspected"} for p in unreadable]
    if failed:
        halt("cleanup failed", detail="a link in the worktree could not be removed as a link; the worktree "
             "was not removed", links=failed, links_removed=removed, leftover=[wt])
    return removed


def cmd_finalize(ctx: Context, st: dict, args: argparse.Namespace) -> dict:
    outcome = " ".join(args.outcome).strip()
    if not outcome:
        halt("usage error", detail="finalize needs an outcome")
    release_lock(st, "stash")
    release_tree_if_inactive(st)
    tree = compute_tree(ctx, st, st["git_root"], st["project_prefix"])
    st["finalized"] = outcome
    st["finalized_at"] = iso(ctx.now())
    st["tree"] = tree["tree"]
    save_state(ctx, st)
    leftovers = [l for s in active_snapshots(st) for l in s.get("leftovers", [])]
    return {"status": "ok", "finalized": outcome, "tree": tree["tree"], "tree_reasons": tree["reasons"],
            "tree_paths": tree["paths"], "stash": st.get("stash"), "leftovers": leftovers,
            "holds_tree_lock": holds_lock(st, "tree"), "worktree": st.get("worktree"),
            "run_state": str(run_dir(ctx, st["branch"]))}


# ---------------------------------------------------------------------------------------------
# recover (T13-T20) and unlock (T18)
# ---------------------------------------------------------------------------------------------

def cmd_recover(ctx: Context, args: argparse.Namespace) -> dict:
    if args.check:
        return cmd_recover_check(ctx, args)
    if not args.branch:
        halt("usage error", detail="recover needs a branch or --check")
    target = load_state(ctx, args.branch, missing_ok=True)
    if target is not None:
        hold_call_lock(ctx, args.branch)  # RF-5: recover acts on the target's state under its call lock
        target = load_state(ctx, args.branch, missing_ok=True)
    if target is None:
        halt("no run state", run=args.branch,
             remedy=["unlock the run's locks with " + remedy_cmd("unlock", "<lock>", "--project-root", "<GIT_ROOT>")])
    branch = target["branch"]
    if args.abandon and not args.by:
        halt("usage error", detail="--abandon needs --by <caller-branch>")
    notes: list = []
    alive = run_alive(ctx, target)
    if alive:
        if not args.abandon:
            halt("owner alive", run=branch, owner=target.get("owner"), heartbeat=target.get("heartbeat"),
                 remedy=[remedy_cmd("recover", branch, "--abandon", "--by", "<this-branch>")
                         + "  (only from the session that owns the run)"])
        caller = ctx.resolve_owner()
        if not caller:
            unavailable("no host ancestor", detail="--abandon needs the caller's own host process")
        refusal = None
        by = load_state(ctx, args.by, missing_ok=True) if BRANCH_RE.match(args.by or "") else None
        if not same_process(target.get("owner"), caller):
            refusal = "caller process is not the target's recorded owner process"
        elif by is None:
            refusal = "caller run state missing"
        elif not same_process(by.get("owner"), caller):
            refusal = "caller run belongs to another process"
        elif by.get("token") == target.get("token") or by["branch"] == branch:
            refusal = "caller run is the target"
        elif float(by.get("created_epoch", 0)) <= float(target.get("heartbeat_epoch", 0)):
            refusal = "caller run was not created after the target's last heartbeat"
        elif ctx.now() - float(target.get("heartbeat_epoch", 0)) <= ABANDON_HEARTBEAT_SECONDS:
            refusal = "target heartbeat is younger than 15 minutes"
        if refusal:
            halt("abandon refused", detail=refusal, run=branch, heartbeat=target.get("heartbeat"))
        target["finalized"] = "abandoned"
        target["abandoned_by"] = args.by
        target["finalized_at"] = iso(ctx.now())
        save_state(ctx, target)
        notes.append("abandoned")
    elif args.abandon:
        notes.append("target already dead; --abandon not needed")
    # T20 guard first: refusals change nothing
    if args.stash_resolved:
        resolve_pending(ctx, target)
        stash = target.get("stash") or {}
        if stash.get("state") != "saved":
            halt("no saved stash", run=branch, stash=stash)
        entry = next((e for e in stash_entries(target["git_root"]) if e["oid"] == stash["oid"]), None)
        if entry is not None:
            halt("stash entry remains", run=branch, entry=entry["ref"], oid=stash["oid"],
                 detail="apply or drop the entry by hand first")
    keep = [p for group in (args.keep_current or []) for p in group]
    if keep:
        listed = {e["path"]: (s, e) for s in active_snapshots(target) for e in s["entries"]
                  if e.get("status") == "leftover"}
        bad = [p for p in keep if p not in listed]
        if bad:
            halt("not a listed leftover", paths=bad, listed=sorted(listed))
        for p in keep:
            listed[p][1]["status"] = "kept"
        save_state(ctx, target)
        notes.append(f"kept current bytes: {', '.join(keep)}")
    # T13
    if target.get("supervisor"):
        try:
            stop_supervisor(ctx, target)
            notes.append("app stopped")
        except Outcome as exc:
            notes.append(f"app-stop: {exc.reason}")
    leftovers = []
    for snap in list(active_snapshots(target)):
        leftovers += rollback_snapshot(ctx, target, snap)
    if leftovers:
        release_lock(target, "stash")
        halt("recover halted", run=branch, leftovers=leftovers,
             remedy=[remedy_cmd("recover", branch, "--keep-current", *[l["path"] for l in leftovers])],
             holds_tree_lock=holds_lock(target, "tree"))
    if args.stash_resolved:
        stash = target["stash"]
        target["stash"] = {"state": "restored", "oid": stash.get("oid"), "paths": stash.get("paths", []),
                           "resolved_by": "operator"}
        save_state(ctx, target)
        notes.append("stash resolved by operator")
    else:
        try:
            frag = restore_stash(ctx, target, in_recover=True)
        except Outcome as exc:
            release_lock(target, "stash")
            release_tree_if_inactive(target)  # R2-2: the tree lock stays while the reloaded target has an active snapshot
            if exc.reason == "active snapshot":  # R2-2 [AD]: a zombie call of the dead run landed during the wait
                halt("recover halted", run=branch, notes=notes, snapshots=[s["id"] for s in active_snapshots(target)],
                     holds_tree_lock=holds_lock(target, "tree"), remedy=[remedy_cmd("recover", branch)],
                     detail="active snapshot: a helper call of this dead run wrote a snapshot while recover waited "
                            "for a lock; nothing was restored, and the tree lock is kept for that snapshot")
            exc.fields.setdefault("run", branch)
            exc.fields.setdefault("notes", notes)
            raise
        if frag.get("restored"):
            notes.append("stash restored")
            if frag.get("stale_entry"):
                notes.append(f"stale stash entry: {frag['stale_entry']}")
        if (target.get("stash") or {}).get("drift"):
            notes.append("stash restored with drift (saved bytes kept): "
                         + ", ".join(d["path"] for d in target["stash"]["drift"]))
    kept_landing = [snapshot_paths(s) for s in target.get("snapshots", [])
                    if s["kind"] == "landing" and s["lifecycle"] == "released"]
    release_lock(target, "stash")
    if active_snapshots(target):  # RX-2 [AD]: a late zombie must keep the tree lock and the run recoverable
        halt("recover halted", run=branch, notes=notes,
             snapshots=[s["id"] for s in active_snapshots(target)],
             holds_tree_lock=holds_lock(target, "tree"), remedy=[remedy_cmd("recover", branch)],
             detail="active snapshot: a helper call of this dead run wrote a snapshot while recover was active; "
                    "the tree lock is kept for that snapshot")
    release_lock(target, "tree")
    target["finalized"] = "recovered"
    target["recovered_at"] = iso(ctx.now())
    save_state(ctx, target)
    return {"status": "ok", "run": branch, "result": "recovered", "notes": notes,
            "kept_landing_paths": [p for paths in kept_landing for p in paths], "stash": target.get("stash"),
            "worktree": target.get("worktree")}


def cmd_unlock(ctx: Context, args: argparse.Namespace) -> dict:
    name = os.path.basename(args.lock)
    if not LOCK_NAME_RE.match(name):
        halt("invalid lock name", lock=args.lock)
    scope = resolve_scope(args.project_root or ctx.cwd or os.getcwd())
    path = Path(scope["git_common_dir"]) / name
    if os.path.dirname(args.lock) and norm_key(os.path.dirname(os.path.abspath(args.lock))) != norm_key(str(path.parent)):
        halt("lock outside this repository's git common dir", lock=args.lock)
    rec = read_lock(path)
    if rec is None:
        return {"status": "ok", "cleared": False, "detail": "lock not held", "lock": str(path)}
    branch = rec.get("branch", "")
    owner_state = None
    if BRANCH_RE.match(branch or ""):
        owner_state = load_state(ctx, branch, missing_ok=True)
        if owner_state is not None and owner_state.get("token") != rec.get("token"):
            owner_state = None
    alive = lock_owner_alive(ctx, rec)
    if alive:
        halt("unlock refused", detail="the lock owner is alive", lock=str(path), owner_record=rec)
    if owner_state is not None and name.startswith("skill-mesh-tree-") and active_snapshots(owner_state):
        halt("unlock refused", detail="the tree lock guards an active snapshot", lock=str(path), owner_record=rec,
             remedy=[remedy_cmd("recover", branch)])
    os.unlink(path)
    return {"status": "ok", "cleared": True, "lock": str(path), "owner_record": rec}


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------

class _UsageError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # never print usage to stdout or exit
        raise _UsageError(message)

    def exit(self, status: int = 0, message: Optional[str] = None) -> None:
        raise _UsageError(message or "parser exit")


def build_parser() -> _Parser:
    p = _Parser(prog="build_step_tree.py", add_help=False)
    sub = p.add_subparsers(dest="cmd", parser_class=_Parser)
    s = sub.add_parser("scope", add_help=False)
    s.add_argument("--project-root")
    r = sub.add_parser("recover", add_help=False)
    r.add_argument("branch", nargs="?")
    r.add_argument("--check", action="store_true")
    r.add_argument("--run")
    r.add_argument("--project-root")
    r.add_argument("--keep-current", nargs="+", action="append")
    r.add_argument("--stash-resolved", action="store_true")
    r.add_argument("--abandon", action="store_true")
    r.add_argument("--by")
    u = sub.add_parser("unlock", add_help=False)
    u.add_argument("lock")
    u.add_argument("--project-root")
    for name in ("stash-save", "stash-restore", "worktree-create", "changes", "tree-hash", "preview-apply",
                 "preview-rollback", "land", "land-rollback", "verify-landed", "ship-gate", "app-stop", "cleanup"):
        x = sub.add_parser(name, add_help=False)
        x.add_argument("--run", required=True)
    a = sub.add_parser("app-start", add_help=False)
    a.add_argument("--run", required=True)
    a.add_argument("--start-cmd")
    a.add_argument("--url")
    a.add_argument("--ready-url")
    a.add_argument("--log")
    t = sub.add_parser("test-count", add_help=False)
    t.add_argument("--check-runner")
    t.add_argument("--command")
    t.add_argument("--runner", choices=["pytest", "node-test", "go", "cargo", "jest", "vitest"])
    t.add_argument("--log")
    t.add_argument("--project-root")
    b = sub.add_parser("budget", add_help=False)
    b.add_argument("action", choices=["read", "advance", "clear"])
    b.add_argument("--run")
    b.add_argument("--key")
    b.add_argument("--problem")
    b.add_argument("--problem-file")
    b.add_argument("--plan-step")
    b.add_argument("--issue")
    b.add_argument("--max-iter", type=int)
    ar = sub.add_parser("archive", add_help=False)
    ar.add_argument("--run", required=True)
    ar.add_argument("--keep-evidence", action="store_true")
    f = sub.add_parser("finalize", add_help=False)
    f.add_argument("outcome", nargs="+")
    f.add_argument("--run", required=True)
    return p


_RUN_COMMANDS = {
    "stash-save": cmd_stash_save, "stash-restore": cmd_stash_restore, "worktree-create": cmd_worktree_create,
    "changes": cmd_changes, "tree-hash": cmd_tree_hash, "preview-apply": cmd_preview_apply,
    "preview-rollback": cmd_preview_rollback, "land": cmd_land, "land-rollback": cmd_land_rollback,
    "verify-landed": cmd_verify_landed, "ship-gate": cmd_ship_gate, "app-start": cmd_app_start,
    "app-stop": cmd_app_stop, "archive": cmd_archive, "cleanup": cmd_cleanup, "finalize": cmd_finalize,
}


def run_cli(argv: list, ctx: Optional[Context] = None) -> dict:
    """Library entry: returns the single result object (never prints)."""
    ctx = ctx or Context()
    sub = argv[0] if argv else None
    if sub in ("-h", "--help", "help"):
        return {"status": "ok", "subcommand": "help", "usage": __doc__}
    try:
        try:
            args = build_parser().parse_args(argv)
            if not args.cmd:
                raise _UsageError("a subcommand is required")
            if args.cmd == "scope":
                result = cmd_scope(ctx, args)
            elif args.cmd == "recover":
                result = cmd_recover(ctx, args)
            elif args.cmd == "unlock":
                result = cmd_unlock(ctx, args)
            elif args.cmd == "test-count":
                result = cmd_test_count(ctx, args)
            elif args.cmd == "budget":
                result = cmd_budget(ctx, args)
            else:
                st = enter_run(ctx, args.run)
                result = _RUN_COMMANDS[args.cmd](ctx, st, args)
        except Outcome as exc:
            result = {"status": exc.status}
            if exc.reason:
                result["reason"] = exc.reason
            result.update(exc.fields)
        except _UsageError as exc:
            result = {"status": "halt", "reason": "usage error", "detail": str(exc).strip()}
        except GitError as exc:
            result = {"status": "halt", "reason": "git failed", "git_args": exc.git_args, "code": exc.code,
                      "detail": exc.stderr[-2000:]}
        except Exception as exc:  # noqa: BLE001 - every failure must still be one JSON object
            result = {"status": "halt", "reason": "internal error", "detail": f"{type(exc).__name__}: {exc}"}
    finally:
        release_call_locks(ctx)  # RF-5 (the OS also releases them when the process exits)
    if sub == "recover" and "--check" in argv:
        label = "recover --check"
    elif sub == "budget" and len(argv) > 1:
        label = f"budget {argv[1]}"
    else:
        label = sub or ""
    result.setdefault("subcommand", label)
    return result


def _jsonable(obj: Any) -> Any:
    return json.loads(json.dumps(obj, default=str))


def main(argv: Optional[list] = None, ctx: Optional[Context] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "_supervise":
        return supervise(argv[1:])
    try:
        result = _jsonable(run_cli(argv, ctx))
    except InjectedCrash:
        raise
    except BaseException as exc:  # noqa: BLE001
        result = {"status": "halt", "reason": "internal error", "detail": f"{type(exc).__name__}: {exc}",
                  "subcommand": argv[0] if argv else ""}
    if result.get("status") not in EXIT_CODES:
        result = {"status": "halt", "reason": "internal error", "detail": "invalid status", "subcommand": ""}
    line = json.dumps(result, ensure_ascii=True, sort_keys=True)
    try:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
    except (OSError, ValueError):
        pass
    return EXIT_CODES[result["status"]]


if __name__ == "__main__":
    sys.exit(main())
