#!/usr/bin/env python3
"""Private, immutable lesson observations for the lesson-harvest skill.

What this is
------------
A standard-library-only helper and deterministic CLI that lets a model preserve one
evidenced in-session mistake as a private, immutable record, and lets a later harvest
read those records back at unchanged Git HEAD. It is the producer/consumer seam
behind lesson-harvest's record mode and the observation half of a normal harvest.

It is a small append-only inbox, NOT a database, a queue service, or a checkpoint
store. Nothing here opens a pull request, writes a memory file, edits a rule, or
mutates any versioned content. The skill contract owns every judgement; this module
owns only persistence, bounded reads, and refusal.

Storage
-------
--repo PATH must name an existing, non-bare Git working tree. The working-tree root
and the COMMON Git metadata directory are both resolved by invoking Git with argument
arrays (never a command string), so linked worktrees share one repository inbox while
each record retains the working-tree root it came from. Records live under:

    <common git dir>/lesson-harvest/observations/<uuid4>.md   immutable observation
    <common git dir>/lesson-harvest/receipts/<uuid4>.json     immutable disposition

That location is deliberate: it is private to the clone, it is never versioned
content, and it needs no ignore rule in any target project. Parent repositories are
never searched. Read commands create no directories. Evidence locators are inert text --
this module never executes, fetches, or opens one.

A state path is refused before it is opened when ANY component of it, from the
resolved common Git directory down to the leaf, is a symlink or a Windows reparse
point, and the refusal is applied on read commands exactly as on write commands. The
whole chain is inspected rather than the leaf alone because os.lstat declines to
follow a link only at the FINAL component: an ancestor junction would otherwise
redirect the entire subtree transparently, and the leaf's own lstat would report the
redirected target's attributes rather than a refusal. The resolved real path is then
required to stay inside the resolved inbox root at inspection time. These checks
inspect filesystem state before access; they do not protect against another process
replacing a directory concurrently. Git metadata is operator-controlled, and hostile
concurrent mutation of it is outside this helper's supported boundary.

Publication
-----------
Every record is written to a same-directory temporary file, flushed and fsynced in
full, and only then published with an atomic, NO-OVERWRITE primitive. Both halves
hold on every path: a reader can never observe a partially written file at a record's
final path, and an existing destination is never replaced. Where a filesystem offers
no such primitive the publication FAILS CLOSED with a JSON diagnostic (exit 3) rather
than dropping either half; nothing lands at the final path, so the id stays
recordable. Re-recording identical content under the same id is an
idempotent replay (exit 0, status replayed); DIFFERENT content under an existing id is
a conflict (exit 3) and never overwrites the historical bytes. Abandoned temporary
files are ignored by readers and reported as diagnostics. There is no apply lock and
no stale-process recovery: normal mutating harvest is one invocation per target
repository, concurrent capture and reading are supported, and concurrent candidate
publication is out of scope. Sequential retry reconciliation is not a claim of
concurrent pull-request uniqueness.

Corrections
-----------
Saved bytes are immutable, so a correction is a NEW record whose supersedes field
names an earlier observation in the same inbox. The pending command reports the
relationship in its diagnostics -- inspected across the WHOLE inbox, not just the
current page, so bounded paging cannot hide a correction that lives past the page
boundary. An original with a correction is historical and is never a source of a new
candidate; its replacement stays eligible. Two or more corrections of the same
original are a conflicting corrective branch: reported, left undecided, never
resolved by newest timestamp.

Commands and exit codes
-----------------------
    new-id                                            print one UUID4, no repo access
    record   --repo PATH --input FILE                 persist one observation
    pending  --repo PATH [--limit N] [--after UUID]   read-only bounded page
    complete --repo PATH --input FILE                 persist one disposition receipt

    0  the requested operation completed -- including a replay, and including a page
       with no pending observations
    2  invalid input, repository, or state -- including a malformed command line
    3  conflicting content, failed publication, or an unexpected internal failure;
       stdout carries no success receipt

That set is CLOSED: {0, 2, 3} are the only codes this CLI returns. Every path out of
main is mapped onto one of them, including a command line argparse itself rejects and
including an exception no branch anticipated, so a caller never has to distinguish a
refusal from an interpreter traceback.

Responses are closed JSON objects on stdout, with ONE deliberate exception: new-id
prints a bare UUID4 and a newline, because its whole job is to hand a shell one
substitutable token. That bare-UUID output is the contract the skill documents and
this module's tests pin; the other three commands answer with a JSON object.
Diagnostics go to stderr as one JSON
object carrying code, message, and optionally observation_id; no saved narrative is
ever echoed into an error, and no traceback is ever printed.

Pagination is STATELESS. --after names an existing observation and the page continues
strictly after it, even when that observation already has a receipt, so a retained or
completed old record can never starve a later one. No cursor is stored, an unknown
cursor is an error, and truncation is always reported through remaining and next_after
rather than performed silently.
"""

from __future__ import annotations

import argparse
import errno
import json
import os
import re
import stat
import subprocess
import sys
import uuid
from datetime import datetime, timezone

# -- Schemas ------------------------------------------------------------------

SCHEMA_OBSERVATION = "lesson-observation-v1"
SCHEMA_CAPTURE_RECEIPT = "lesson-capture-receipt-v1"
SCHEMA_PENDING = "lesson-pending-v1"
SCHEMA_DISPOSITION = "lesson-disposition-v1"
SCHEMA_COMPLETION_RECEIPT = "lesson-completion-receipt-v1"

# -- Exit codes ---------------------------------------------------------------

EXIT_OK = 0
EXIT_INVALID = 2
EXIT_CONFLICT = 3

# -- Bounds -------------------------------------------------------------------

MAX_REQUEST_BYTES = 16 * 1024
MAX_ENVELOPE_BYTES = 32 * 1024
MAX_SESSION_CHARS = 256
MAX_LOCATOR_CHARS = 1024
MAX_NARRATIVE_CHARS = 2000
MAX_CANDIDATE_REF_CHARS = 2048
MIN_EVIDENCE_ITEMS = 1
MAX_EVIDENCE_ITEMS = 5

PAGE_LIMIT_MIN = 1
PAGE_LIMIT_MAX = 50
PAGE_LIMIT_DEFAULT = 20

# -- Layout -------------------------------------------------------------------

STATE_DIR_NAME = "lesson-harvest"
OBSERVATIONS_DIR_NAME = "observations"
RECEIPTS_DIR_NAME = "receipts"
OBSERVATION_SUFFIX = ".md"
RECEIPT_SUFFIX = ".json"
TEMP_SUFFIX = ".tmp"

OBSERVATION_TITLE = "# Lesson observation"
FENCE_OPEN = "```json"
FENCE_CLOSE = "```"

# -- Field sets (closed; unknown keys are errors) ------------------------------

OBSERVATION_REQUEST_FIELDS = (
    "observation_id", "session", "source", "observed_error", "evidence",
    "correction", "supersedes",
)
OBSERVATION_ENVELOPE_FIELDS = (
    ("schema",) + OBSERVATION_REQUEST_FIELDS + ("recorded_at", "repo_root")
)
COMPLETION_REQUEST_FIELDS = (
    "observation_id", "classification", "disposition", "evidence_refs",
    "candidate_ref",
)
COMPLETION_ENVELOPE_FIELDS = (
    ("schema",) + COMPLETION_REQUEST_FIELDS + ("recorded_at",)
)

CLASSIFICATIONS = (
    "instruction-gap", "instruction-not-used", "tooling-environment",
    "task-specific", "unsupported",
)
DISPOSITIONS = ("candidate-prepared", "already-codified", "rejected")
DISPOSITION_REQUIRING_CANDIDATE = "candidate-prepared"

# -- Shapes -------------------------------------------------------------------

# Canonical lowercase UUID4, version and variant included: a model that invents an id
# by hand rather than calling new-id is rejected instead of silently accepted.
UUID4_RE = re.compile(
    r"\A[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
# The HTTPS GitHub pull-request URL SHAPE. Shape only -- this module performs no
# network request and makes no claim that the pull request exists or is relevant.
# Verifying that is the skill's job, before it calls complete.
CANDIDATE_REF_RE = re.compile(
    r"\Ahttps://github\.com/[A-Za-z0-9][A-Za-z0-9._-]*"
    r"/[A-Za-z0-9][A-Za-z0-9._-]*/pull/[1-9][0-9]*\Z")
# Every control character EXCEPT tab (09) and LF (0a). CR is rejected with the rest: a
# narrative string carrying one is a transport artifact, not authored content.
CONTROL_CHAR_RE = re.compile("[\x00-\x08\x0b-\x1f\x7f]")
# Error messages name a rejected key, so the key is reduced to a bounded, inert token
# first: a request is untrusted input and must not steer its own diagnostic.
UNSAFE_KEY_RE = re.compile(r"[^A-Za-z0-9_.-]")
MAX_REPORTED_KEYS = 8
MAX_REPORTED_KEY_CHARS = 48
MAX_REPORTED_ARGUMENT_CHARS = 200

# -- Diagnostic codes ---------------------------------------------------------

DIAG_COMPLETED = "observation-completed"
DIAG_SUPERSEDED = "observation-superseded"
DIAG_CORRECTION = "observation-corrects-earlier"
DIAG_CORRECTION_CONFLICT = "correction-conflict"
DIAG_SUPERSEDES_MISSING = "superseded-record-unavailable"
DIAG_MALFORMED_OBSERVATION = "observation-malformed"
DIAG_MALFORMED_RECEIPT = "receipt-malformed"
DIAG_ABANDONED_TEMP = "abandoned-temporary-file"
DIAG_UNEXPECTED_ENTRY = "unexpected-inbox-entry"


class LessonError(Exception):
    """One refusal, carrying its exit code and machine-readable code with it."""

    def __init__(self, code, message, exit_code=EXIT_INVALID, observation_id=None):
        super(LessonError, self).__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.observation_id = observation_id


class StateFileError(LessonError):
    """A saved record could not be read as its declared envelope.

    Raised with the CONFLICT code by default, because a publication path that finds
    unreadable bytes at its destination must never overwrite them. The pending
    command catches this class and turns it into a diagnostic instead: a reader
    reports a malformed file and leaves it in place rather than failing a whole page.
    """

    def __init__(self, code, message, exit_code=EXIT_CONFLICT, observation_id=None):
        super(StateFileError, self).__init__(code, message, exit_code, observation_id)


class PublicationUnsupported(Exception):
    """This filesystem offers no atomic, no-overwrite publication primitive.

    Internal to publication: _publish_atomically maps it onto the closed exit-code
    set as a `publication-unsupported` refusal after discarding the temporary file,
    so it never reaches a caller and never escapes as a traceback.
    """


class Inbox(object):
    """The resolved private location for one target repository.

    `common_dir` is the guard ROOT, not decoration: every state path this module
    touches is required to sit underneath it, and every component between the two is
    inspected for a reparse point before the path is opened.
    """

    def __init__(self, repo_root, common_dir):
        self.repo_root = repo_root
        self.common_dir = os.path.normpath(os.path.abspath(common_dir))
        self.state_dir = os.path.join(self.common_dir, STATE_DIR_NAME)
        self.observations_dir = os.path.join(self.state_dir, OBSERVATIONS_DIR_NAME)
        self.receipts_dir = os.path.join(self.state_dir, RECEIPTS_DIR_NAME)


# --------------------------------------------------------------------------- #
# Repository resolution
# --------------------------------------------------------------------------- #

def _run_git(repo_path, args):
    """Run one Git command as an ARGUMENT ARRAY; return stdout, or None on failure.

    No value is ever interpolated into a shell command line: the operator-supplied
    path is an argv element, so no quoting, escaping, or shell metacharacter in it
    can change which command runs.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", repo_path] + list(args),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    except OSError:
        raise LessonError(
            "git-unavailable",
            "git could not be executed; it is required to resolve the target "
            "repository.")
    except subprocess.SubprocessError:
        raise LessonError(
            "git-failed",
            "git did not complete while resolving the target repository.")
    if proc.returncode != 0:
        return None
    try:
        return proc.stdout.decode("utf-8").strip()
    except UnicodeDecodeError:
        raise LessonError(
            "git-output-undecodable",
            "git returned a path this helper cannot decode as UTF-8.")


def resolve_inbox(repo_arg):
    """Resolve --repo to one private inbox, or refuse.

    The refusals are deliberate and each is exit 2: a path that is not a directory,
    a path Git does not answer for, and a BARE repository (which has no working tree
    for an observation to belong to).
    """
    if not repo_arg:
        raise LessonError("repository-not-given", "--repo is required.")
    path = os.path.abspath(repo_arg)
    if not os.path.isdir(path):
        raise LessonError(
            "repository-not-found", "--repo must name an existing directory.")
    bare = _run_git(path, ["rev-parse", "--is-bare-repository"])
    if bare is None:
        raise LessonError(
            "not-a-git-working-tree",
            "--repo must name a path inside a Git working tree.")
    if bare != "false":
        raise LessonError(
            "bare-repository",
            "--repo must name a non-bare Git working tree; a bare repository has no "
            "working tree an observation can belong to.")
    top = _run_git(path, ["rev-parse", "--show-toplevel"])
    if not top:
        raise LessonError(
            "not-a-git-working-tree",
            "--repo must name a path inside a Git working tree.")
    common = _run_git(path, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
    if not common:
        # Older Git has no --path-format; its answer is relative to the -C directory.
        common = _run_git(path, ["rev-parse", "--git-common-dir"])
        if not common:
            raise LessonError(
                "git-metadata-unresolved",
                "the common Git metadata directory could not be resolved for --repo.")
        if not os.path.isabs(common):
            common = os.path.join(path, common)
    return Inbox(os.path.normpath(top), os.path.normpath(common))


# --------------------------------------------------------------------------- #
# State-path safety and atomic publication
# --------------------------------------------------------------------------- #

def _lstat_state_path(path):
    """os.lstat for a private state path; None when the path is genuinely absent.

    Absence is proven by FileNotFoundError and by nothing else -- the same single
    exception the guard already treated as absence before this boundary existed.
    Every OTHER OSError -- a permission denial from an antivirus scan or a file
    lock, a sharing violation, a network-share hiccup -- is a failure to LOOK, not
    evidence of absence, and is RAISED rather than answered as False.

    That distinction is the whole point of routing every state-path stat through
    here: os.path.lexists, os.path.isfile and os.path.isdir all swallow OSError and
    answer False, which converts a transient read failure into a confident wrong
    answer (a completed observation silently reported as pending, or a present
    record silently reported as "not a file").
    """
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError:
        raise LessonError(
            "state-path-unreadable",
            "a private state path could not be inspected.")


def _stat_is_reparse_point(st):
    """True when an already-taken lstat result describes a link/reparse point."""
    if stat.S_ISLNK(st.st_mode):
        return True
    attributes = getattr(st, "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _is_reparse_point(path):
    """True when `path` itself is a symlink or a Windows reparse point."""
    st = _lstat_state_path(path)
    if st is None:
        return False
    return _stat_is_reparse_point(st)


def _list_state_dir(path):
    """sorted(os.listdir), raised as this module's own refusal rather than a crash.

    DIRECTORY scope, so this is deliberately NOT the per-entry contract: a reader
    that cannot enumerate the inbox cannot know what it is not showing, and serving
    a partial page would be a silent wrong answer. What changes is only the shape of
    the refusal: an ordinary permission denial used to fall through to main's
    bare-Exception backstop and surface as a generic `internal-error` at exit 3,
    which reads as "this helper has a bug" rather than "this directory could not be
    read". It is now the same closed refusal class every other state-path failure
    uses, at exit 2.
    """
    try:
        return sorted(os.listdir(path))
    except OSError:
        raise LessonError(
            "state-dir-unreadable",
            "a private state directory could not be listed.")


def _refuse_reparse_point():
    raise LessonError(
        "state-path-is-a-reparse-point",
        "a private state path, or one of the directories containing it, is a symlink "
        "or reparse point; refusing to read or write through it.")


def _components_under_root(path, root):
    """Every component from `root` (exclusive) down to `path` (inclusive).

    Refuses a path that is not under the root at all, so a caller cannot hand the
    guard something outside the inbox and have the walk quietly terminate at the
    filesystem root.
    """
    path = os.path.normpath(os.path.abspath(path))
    root = os.path.normpath(os.path.abspath(root))
    parts = []
    current = path
    while os.path.normcase(current) != os.path.normcase(root):
        parent = os.path.dirname(current)
        if parent == current:
            raise LessonError(
                "state-path-outside-inbox",
                "a private state path resolved outside this repository's inbox; "
                "refusing to read or write through it.")
        parts.append(current)
        current = parent
    parts.reverse()
    return parts


def _guard_state_path(inbox, path):
    """Refuse a symlinked or reparse-point state path BEFORE it is opened.

    EVERY component from the resolved common Git directory down to the leaf is
    inspected, not the leaf alone. os.lstat refuses to follow a link only at the
    FINAL component of the path it is given; every ancestor is resolved normally by
    the OS. So a symlink or junction on any directory between the inbox root and the
    leaf would redirect the whole subtree while the leaf's own lstat reported the
    REDIRECTED target's attributes -- a guard that inspects only the leaf sees
    nothing and writes private records wherever the ancestor points.

    The realpath containment check that follows is a second, independent question:
    the walk asks "is any component a link", and this asks "did the path we are
    about to open end up inside the inbox". Either one alone has a gap the other
    covers, and the pair is cheap.
    """
    for component in _components_under_root(path, inbox.common_dir):
        if _is_reparse_point(component):
            _refuse_reparse_point()
    real_root = os.path.realpath(inbox.common_dir)
    real_path = os.path.realpath(path)
    if os.path.normcase(real_path) != os.path.normcase(real_root) and \
            not os.path.normcase(real_path).startswith(
                os.path.normcase(os.path.join(real_root, ""))):
        _refuse_reparse_point()
    return path


def _ensure_state_dirs(inbox):
    """Create the inbox directories. Called by WRITE commands only.

    Read commands do NOT call this (they create nothing), so they re-run the guard
    over the same paths themselves rather than inheriting a check from a write.
    """
    for path in (inbox.state_dir, inbox.observations_dir, inbox.receipts_dir):
        _guard_state_path(inbox, path)
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except FileExistsError:
                raise LessonError(
                    "state-directory-unavailable",
                    "a private state directory path is occupied by a file.")
            except OSError:
                raise LessonError(
                    "state-directory-unavailable",
                    "a private state directory could not be created.")
        _guard_state_path(inbox, path)


def _discard(path):
    try:
        os.unlink(path)
    except OSError:
        pass


def _rename_refuses_an_existing_destination():
    """True only where os.rename is BOTH atomic and no-overwrite.

    CPython implements os.rename on Windows with MoveFileExW and WITHOUT
    MOVEFILE_REPLACE_EXISTING, so an existing destination raises FileExistsError --
    the same atomic question os.link asks, answered by the kernel. POSIX rename(2)
    REPLACES an existing destination silently, so it can never stand in for os.link
    there no matter what check precedes it.
    """
    return os.name == "nt"


def _publish_no_clobber(temp_path, dest_path):
    """Publish the FULLY WRITTEN `temp_path` as `dest_path`.

    Two properties must hold AT ONCE on every path through this function, and each
    one of them has already cost this module a review round on its own:

      ATOMIC        no partially written file is ever observable at a record's final
                    path. A concurrent pending/complete that lists the directory
                    mid-publication would otherwise read a truncated record and
                    report a perfectly good capture as `observation-malformed`; worse,
                    an abrupt kill (SIGKILL, power loss -- no exception, no cleanup)
                    would leave corrupt bytes at the final path FOREVER, and the next
                    record for that id would then fail to parse them and refuse,
                    making the id permanently unrecordable without a human deletion.
      NO-OVERWRITE  an existing destination is refused by the kernel, not by a
                    preceding lexists() check -- that check is a TOCTOU window in
                    which a racing writer's immutable record is destroyed.

    os.link has both on every platform this ships to, so it is the primary primitive:
    the temporary file is complete and fsynced before the destination name exists at
    all, and link() refuses an existing name atomically.

    Where linking is refused for an UNRELATED reason -- a filesystem or mount with no
    hardlink support, which this shared module can reach because it also ships into
    the codex and gpt profiles -- the only stdlib stand-in that keeps BOTH properties
    is os.rename on Windows. An earlier spelling re-created the destination with
    O_CREAT|O_EXCL and wrote the payload there: no-overwrite, but the bytes then
    arrive at the record's FINAL path over time, which loses the atomic half.

    Where neither primitive is available this FAILS CLOSED, by raising
    PublicationUnsupported: nothing is published, nothing partial is left at
    dest_path, and the observation id stays recordable by a later attempt. A
    documented refusal with a JSON diagnostic is the honest answer on such a
    filesystem; silently dropping one of the two properties is not.
    """
    try:
        os.link(temp_path, dest_path)
    except FileExistsError:
        raise
    except (AttributeError, NotImplementedError, OSError) as exc:
        if getattr(exc, "errno", None) == errno.EEXIST:
            raise FileExistsError(dest_path)
        if not _rename_refuses_an_existing_destination():
            raise PublicationUnsupported(dest_path)
        # Atomic: the destination appears complete or not at all. No-overwrite:
        # FileExistsError, raised by the kernel, on an existing destination.
        os.rename(temp_path, dest_path)
        return
    _discard(temp_path)


def _publish_atomically(inbox, directory, filename, payload):
    """Write a same-directory temporary file and publish it with no overwrite."""
    dest_path = os.path.join(directory, filename)
    _guard_state_path(inbox, dest_path)
    temp_path = os.path.join(
        directory, filename + "." + uuid.uuid4().hex + TEMP_SUFFIX)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    try:
        handle = os.open(temp_path, flags, 0o600)
    except OSError:
        raise LessonError(
            "publication-failed",
            "a temporary capture file could not be created in the private inbox.",
            EXIT_CONFLICT)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        _discard(temp_path)
        raise LessonError(
            "publication-failed",
            "a record could not be written to the private inbox.", EXIT_CONFLICT)
    try:
        _publish_no_clobber(temp_path, dest_path)
    except FileExistsError:
        _discard(temp_path)
        raise LessonError(
            "destination-exists",
            "a record already exists at that private path.", EXIT_CONFLICT)
    except PublicationUnsupported:
        _discard(temp_path)
        raise LessonError(
            "publication-unsupported",
            "this filesystem offers no atomic, no-overwrite publication primitive; "
            "nothing was written and that observation id is still recordable.",
            EXIT_CONFLICT)
    except OSError:
        _discard(temp_path)
        raise LessonError(
            "publication-failed",
            "a record could not be published into the private inbox.", EXIT_CONFLICT)
    return dest_path


def _read_state_file(inbox, path, observation_id=None):
    """Read one saved record, bounded to MAX_ENVELOPE_BYTES."""
    _guard_state_path(inbox, path)
    try:
        size = os.path.getsize(path)
    except OSError:
        raise StateFileError(
            "state-file-unreadable", "a saved record could not be read.",
            observation_id=observation_id)
    if size > MAX_ENVELOPE_BYTES:
        raise StateFileError(
            "state-file-too-large",
            "a saved record is larger than the reader's envelope bound.",
            observation_id=observation_id)
    try:
        with open(path, "rb") as stream:
            data = stream.read(MAX_ENVELOPE_BYTES + 1)
    except OSError:
        raise StateFileError(
            "state-file-unreadable", "a saved record could not be read.",
            observation_id=observation_id)
    if len(data) > MAX_ENVELOPE_BYTES:
        raise StateFileError(
            "state-file-too-large",
            "a saved record is larger than the reader's envelope bound.",
            observation_id=observation_id)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise StateFileError(
            "state-file-not-utf8", "a saved record is not valid UTF-8.",
            observation_id=observation_id)


# --------------------------------------------------------------------------- #
# Envelope rendering and parsing
# --------------------------------------------------------------------------- #

def _render_envelope_json(envelope):
    """Serialize an envelope so no narrative byte can break out of its fence.

    Every backtick is emitted as its JSON \\u0060 escape, so an evidence locator or
    a correction containing a fence (or a lone backtick) round-trips exactly and can
    never terminate the surrounding markdown fence early.
    """
    body = json.dumps(envelope, indent=2, ensure_ascii=False, sort_keys=False)
    return body.replace("`", "\\u0060")


def render_observation_document(envelope):
    """The fixed document shape: one title, then exactly one closed JSON fence."""
    return "".join([
        OBSERVATION_TITLE, "\n\n",
        FENCE_OPEN, "\n", _render_envelope_json(envelope), "\n",
        FENCE_CLOSE, "\n",
    ])


def _parse_fenced_json(text, observation_id):
    lines = text.splitlines()
    if not lines or lines[0].strip() != OBSERVATION_TITLE:
        raise StateFileError(
            "observation-title-missing",
            "a saved observation does not begin with the fixed title.",
            observation_id=observation_id)
    try:
        start = lines.index(FENCE_OPEN)
    except ValueError:
        raise StateFileError(
            "observation-fence-missing",
            "a saved observation carries no JSON fence.",
            observation_id=observation_id)
    try:
        end = lines.index(FENCE_CLOSE, start + 1)
    except ValueError:
        raise StateFileError(
            "observation-fence-unclosed",
            "a saved observation has an unclosed JSON fence.",
            observation_id=observation_id)
    try:
        parsed = json.loads("\n".join(lines[start + 1:end]))
    except ValueError:
        raise StateFileError(
            "observation-json-invalid",
            "a saved observation does not carry a parseable JSON envelope.",
            observation_id=observation_id)
    if not isinstance(parsed, dict):
        raise StateFileError(
            "observation-json-invalid",
            "a saved observation does not carry a JSON object envelope.",
            observation_id=observation_id)
    return parsed


def _check_saved_envelope(parsed, fields, schema, observation_id, kind):
    if sorted(parsed) != sorted(fields):
        raise StateFileError(
            kind + "-fields-unexpected",
            "a saved record does not carry exactly the expected envelope fields.",
            observation_id=observation_id)
    if parsed.get("schema") != schema:
        raise StateFileError(
            kind + "-schema-unexpected",
            "a saved record does not declare the expected schema.",
            observation_id=observation_id)
    if parsed.get("observation_id") != observation_id:
        raise StateFileError(
            kind + "-id-mismatch",
            "a saved record's id does not match its own filename.",
            observation_id=observation_id)
    return parsed


def parse_observation_document(text, observation_id):
    parsed = _parse_fenced_json(text, observation_id)
    return _check_saved_envelope(
        parsed, OBSERVATION_ENVELOPE_FIELDS, SCHEMA_OBSERVATION, observation_id,
        "observation")


def parse_receipt_document(text, observation_id):
    try:
        parsed = json.loads(text)
    except ValueError:
        raise StateFileError(
            "receipt-json-invalid",
            "a saved disposition receipt is not parseable JSON.",
            observation_id=observation_id)
    if not isinstance(parsed, dict):
        raise StateFileError(
            "receipt-json-invalid",
            "a saved disposition receipt is not a JSON object.",
            observation_id=observation_id)
    return _check_saved_envelope(
        parsed, COMPLETION_ENVELOPE_FIELDS, SCHEMA_DISPOSITION, observation_id,
        "receipt")


# --------------------------------------------------------------------------- #
# Request validation
# --------------------------------------------------------------------------- #

def _safe_key(key):
    token = UNSAFE_KEY_RE.sub("?", str(key))
    if len(token) > MAX_REPORTED_KEY_CHARS:
        token = token[:MAX_REPORTED_KEY_CHARS] + "..."
    return token


def _safe_key_list(keys):
    listed = sorted(_safe_key(key) for key in keys)
    if len(listed) > MAX_REPORTED_KEYS:
        listed = listed[:MAX_REPORTED_KEYS] + ["..."]
    return ", ".join(listed)


def _require_exact_keys(request, fields, kind):
    present = set(request)
    missing = set(fields) - present
    unknown = present - set(fields)
    if missing:
        raise LessonError(
            "missing-field",
            kind + " request is missing required field(s): "
            + _safe_key_list(missing) + ".")
    if unknown:
        raise LessonError(
            "unknown-field",
            kind + " request carries unknown key(s): " + _safe_key_list(unknown)
            + ".")


def _check_encodable(value, field):
    """Refuse a string Python cannot encode as UTF-8, before anything writes it.

    A JSON document may be perfectly valid UTF-8 and still decode to a str holding a
    LONE UTF-16 surrogate: `"\\ud800"` is a legal JSON escape and Python's decoder
    does not require surrogate pairing. Such a str passes the control-character
    screen (surrogates are not in \\x00-\\x1f/\\x7f) and every length bound, and then
    raises UnicodeEncodeError at the .encode("utf-8") that renders the record --
    long after validation, from a call site with no diagnostic of its own. Probing
    the encode HERE turns that into a normal exit-2 refusal, and it closes the whole
    class rather than the surrogate range alone: anything the codec rejects is
    rejected by name instead of crashing the process later.
    """
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise LessonError(
            "field-not-encodable",
            field + " carries a code point that cannot be encoded as UTF-8 (an "
            "unpaired surrogate, for example); a saved record must be UTF-8.")
    return value


def _check_text(value, field, max_chars):
    if not isinstance(value, str):
        raise LessonError("field-type", field + " must be a string.")
    _check_encodable(value, field)
    if CONTROL_CHAR_RE.search(value):
        raise LessonError(
            "field-control-characters",
            field + " carries a control character; only tab and line feed are "
            "accepted.")
    if not value.strip():
        raise LessonError("field-blank", field + " must not be blank.")
    if len(value) > max_chars:
        raise LessonError(
            "field-too-long",
            field + " exceeds its bound of " + str(max_chars) + " characters.")
    return value


def _check_locator_list(value, field):
    if not isinstance(value, list):
        raise LessonError("field-type", field + " must be an array.")
    if not MIN_EVIDENCE_ITEMS <= len(value) <= MAX_EVIDENCE_ITEMS:
        raise LessonError(
            "field-cardinality",
            field + " must carry between " + str(MIN_EVIDENCE_ITEMS) + " and "
            + str(MAX_EVIDENCE_ITEMS) + " locators.")
    return [_check_text(item, field + " item", MAX_LOCATOR_CHARS) for item in value]


def _check_uuid(value, field):
    if not isinstance(value, str) or not UUID4_RE.match(value):
        raise LessonError(
            "field-shape",
            field + " must be a lowercase canonical UUID4; obtain one from the "
            "helper's new-id command.")
    return value


def validate_observation_request(request):
    """Validate one record request and return exactly its closed field set."""
    _require_exact_keys(request, OBSERVATION_REQUEST_FIELDS, "record")
    observation_id = _check_uuid(request["observation_id"], "observation_id")
    supersedes = request["supersedes"]
    if supersedes is not None:
        supersedes = _check_uuid(supersedes, "supersedes")
        if supersedes == observation_id:
            raise LessonError(
                "supersedes-self",
                "supersedes must name a different, earlier observation.")
    return {
        "observation_id": observation_id,
        "session": _check_text(request["session"], "session", MAX_SESSION_CHARS),
        "source": _check_text(request["source"], "source", MAX_LOCATOR_CHARS),
        "observed_error": _check_text(
            request["observed_error"], "observed_error", MAX_NARRATIVE_CHARS),
        "evidence": _check_locator_list(request["evidence"], "evidence"),
        "correction": _check_text(
            request["correction"], "correction", MAX_NARRATIVE_CHARS),
        "supersedes": supersedes,
    }


def validate_completion_request(request):
    """Validate one complete request and return exactly its closed field set."""
    _require_exact_keys(request, COMPLETION_REQUEST_FIELDS, "complete")
    observation_id = _check_uuid(request["observation_id"], "observation_id")
    classification = request["classification"]
    if classification not in CLASSIFICATIONS:
        raise LessonError(
            "field-enum",
            "classification must be one of: " + ", ".join(CLASSIFICATIONS) + ".")
    disposition = request["disposition"]
    if disposition not in DISPOSITIONS:
        raise LessonError(
            "field-enum",
            "disposition must be one of: " + ", ".join(DISPOSITIONS) + ".")
    candidate_ref = request["candidate_ref"]
    if disposition == DISPOSITION_REQUIRING_CANDIDATE:
        if not isinstance(candidate_ref, str):
            raise LessonError(
                "candidate-ref-required",
                "candidate_ref must be a verified draft pull-request URL when the "
                "disposition is " + DISPOSITION_REQUIRING_CANDIDATE + ".")
        if len(candidate_ref) > MAX_CANDIDATE_REF_CHARS:
            raise LessonError(
                "field-too-long",
                "candidate_ref exceeds its bound of "
                + str(MAX_CANDIDATE_REF_CHARS) + " characters.")
        if not CANDIDATE_REF_RE.match(candidate_ref):
            raise LessonError(
                "candidate-ref-shape",
                "candidate_ref must have the HTTPS GitHub pull-request URL shape.")
    elif candidate_ref is not None:
        raise LessonError(
            "candidate-ref-unexpected",
            "candidate_ref must be null unless the disposition is "
            + DISPOSITION_REQUIRING_CANDIDATE + ".")
    return {
        "observation_id": observation_id,
        "classification": classification,
        "disposition": disposition,
        "evidence_refs": _check_locator_list(
            request["evidence_refs"], "evidence_refs"),
        "candidate_ref": candidate_ref,
    }


def read_request(path):
    """Read one bounded UTF-8 JSON request object from a caller-supplied file."""
    try:
        size = os.path.getsize(path)
    except OSError:
        raise LessonError(
            "input-unreadable", "--input must name a readable request file.")
    if size > MAX_REQUEST_BYTES:
        raise LessonError(
            "input-too-large",
            "the request file exceeds the bound of " + str(MAX_REQUEST_BYTES)
            + " bytes.")
    try:
        with open(path, "rb") as stream:
            data = stream.read(MAX_REQUEST_BYTES + 1)
    except OSError:
        raise LessonError(
            "input-unreadable", "--input must name a readable request file.")
    if len(data) > MAX_REQUEST_BYTES:
        raise LessonError(
            "input-too-large",
            "the request file exceeds the bound of " + str(MAX_REQUEST_BYTES)
            + " bytes.")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise LessonError("input-not-utf8", "the request file is not valid UTF-8.")
    try:
        parsed = json.loads(text)
    except ValueError:
        raise LessonError("input-not-json", "the request file is not valid JSON.")
    if not isinstance(parsed, dict):
        raise LessonError(
            "input-not-object", "the request file must carry one JSON object.")
    return parsed


# --------------------------------------------------------------------------- #
# Publication with replay
# --------------------------------------------------------------------------- #

def _utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z")


def _saved_matches(inbox, path, observation_id, parser, fields, request):
    """True when the saved record carries the same REQUEST fields.

    recorded_at is deliberately excluded: a replay re-generates the timestamp, and
    comparing it would turn every honest retry into a conflict.
    """
    parsed = parser(_read_state_file(inbox, path, observation_id), observation_id)
    return all(parsed.get(field) == request[field] for field in fields)


def _publish_with_replay(inbox, directory, filename, payload, observation_id, parser,
                         fields, request, conflict_code):
    dest_path = os.path.join(directory, filename)
    _guard_state_path(inbox, dest_path)
    if os.path.lexists(dest_path):
        if _saved_matches(inbox, dest_path, observation_id, parser, fields, request):
            return dest_path, "replayed"
        raise LessonError(
            conflict_code,
            "a different record is already saved under that observation id; the "
            "historical record is immutable and was not overwritten.",
            EXIT_CONFLICT, observation_id)
    try:
        _publish_atomically(inbox, directory, filename, payload)
    except LessonError as exc:
        if exc.code != "destination-exists":
            raise
        if _saved_matches(inbox, dest_path, observation_id, parser, fields, request):
            return dest_path, "replayed"
        raise LessonError(
            conflict_code,
            "a different record is already saved under that observation id; the "
            "historical record is immutable and was not overwritten.",
            EXIT_CONFLICT, observation_id)
    return dest_path, "recorded"


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #

def cmd_new_id(args):
    """Print one UUID4. No repository access, no filesystem access, no writes."""
    sys.stdout.write(str(uuid.uuid4()) + "\n")
    return None


def cmd_record(args):
    inbox = resolve_inbox(args.repo)
    request = validate_observation_request(read_request(args.input_path))
    observation_id = request["observation_id"]
    _ensure_state_dirs(inbox)
    supersedes = request["supersedes"]
    if supersedes is not None:
        earlier = os.path.join(
            inbox.observations_dir, supersedes + OBSERVATION_SUFFIX)
        _guard_state_path(inbox, earlier)
        if not os.path.isfile(earlier):
            raise LessonError(
                "supersedes-not-found",
                "supersedes must name an existing observation in this repository's "
                "private inbox.", EXIT_INVALID, observation_id)
    envelope = {"schema": SCHEMA_OBSERVATION}
    for field in OBSERVATION_REQUEST_FIELDS:
        envelope[field] = request[field]
    envelope["recorded_at"] = _utc_now()
    envelope["repo_root"] = inbox.repo_root
    payload = render_observation_document(envelope).encode("utf-8")
    path, status = _publish_with_replay(
        inbox, inbox.observations_dir, observation_id + OBSERVATION_SUFFIX, payload,
        observation_id, parse_observation_document, OBSERVATION_REQUEST_FIELDS,
        request, "observation-conflict")
    return {
        "schema": SCHEMA_CAPTURE_RECEIPT,
        "observation_id": observation_id,
        "status": status,
        "path": path,
    }


def cmd_complete(args):
    inbox = resolve_inbox(args.repo)
    request = validate_completion_request(read_request(args.input_path))
    observation_id = request["observation_id"]
    observation_path = os.path.join(
        inbox.observations_dir, observation_id + OBSERVATION_SUFFIX)
    _guard_state_path(inbox, observation_path)
    if not os.path.isfile(observation_path):
        raise LessonError(
            "observation-not-found",
            "no observation with that id exists in this repository's private inbox.",
            EXIT_INVALID, observation_id)
    try:
        parse_observation_document(
            _read_state_file(inbox, observation_path, observation_id),
            observation_id)
    except StateFileError as exc:
        raise LessonError(
            "observation-unreadable",
            "the observation being completed could not be read as the expected "
            "envelope.", EXIT_INVALID, observation_id)
    _ensure_state_dirs(inbox)
    envelope = {"schema": SCHEMA_DISPOSITION}
    for field in COMPLETION_REQUEST_FIELDS:
        envelope[field] = request[field]
    envelope["recorded_at"] = _utc_now()
    payload = (json.dumps(envelope, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8")
    _, status = _publish_with_replay(
        inbox, inbox.receipts_dir, observation_id + RECEIPT_SUFFIX, payload,
        observation_id, parse_receipt_document, COMPLETION_REQUEST_FIELDS,
        request, "disposition-conflict")
    return {
        "schema": SCHEMA_COMPLETION_RECEIPT,
        "observation_id": observation_id,
        "status": status,
    }


def _diagnostic(code, message, observation_id=None, related=None):
    entry = {"code": code, "message": message}
    if observation_id is not None:
        entry["observation_id"] = observation_id
    if related:
        entry["related_observation_ids"] = list(related)
    return entry


def _report_abandoned_temporaries(inbox, directory, diagnostics):
    _guard_state_path(inbox, directory)
    if not os.path.isdir(directory):
        return
    for name in _list_state_dir(directory):
        if name.endswith(TEMP_SUFFIX):
            diagnostics.append(_diagnostic(
                DIAG_ABANDONED_TEMP,
                "an abandoned temporary capture file is present in the private "
                "inbox; it was ignored and left in place."))


# --------------------------------------------------------------------------- #
# The per-entry read boundary
# --------------------------------------------------------------------------- #
#
# THE INVARIANT, stated once and enforced in ONE place:
#
#     A failure raised while reading ONE inbox entry withholds THAT entry with a
#     diagnostic and keeps serving the page. Only a failure that invalidates the
#     whole inbox -- the DIRECTORY-level guards, which deliberately run OUTSIDE
#     both loops -- may terminate the command.
#
# It is enforced at this CALL BOUNDARY rather than at any raise site because the
# guard helpers beneath it (_is_reparse_point, _guard_state_path,
# _components_under_root) serve TWO callers with different failure contracts:
# whole-command validation for record/complete and for pending's directory-level
# guards, and this per-entry read. A callee cannot know which contract it is
# serving, so it cannot pick the right exception class -- which is why respelling
# one more raise site per round kept leaving another escape one call deeper. The
# escape no pre-check can remove is the re-walk _read_state_file performs through
# its own _guard_state_path: it re-lstats the leaf AND every ancestor, per entry,
# after any leaf pre-check has already passed.
#
# The loop body is the only code that KNOWS it is in the per-entry contract, so it
# is the code that declares it. Everything raised beneath this boundary is anchored
# at THIS entry's leaf, so nothing whole-command can be caught here -- that is the
# false-positive check for widening the handler.
#
# One honest edge, stated rather than left to be rediscovered: the re-walk also
# inspects the leaf's ANCESTORS. If it detects an ancestor that became a reparse
# point during a page, that entry is refused instead of failing the command.
# The directory-level guards refuse an ancestor detected as a reparse
# point before the loop, at exit 2. When the per-entry re-walk detects a changed
# ancestor, that entry is withheld and named before its file is opened. These are
# point-in-time checks; a directory replaced after a check is outside the stated
# operator-controlled Git metadata boundary.
#
# That check has a second sub-case, and it is the one that has to be handled
# rather than observed: a redirected ancestor whose target holds no file by this
# leaf's name. The leaf's own os.lstat then raises FileNotFoundError while transiting
# the poisoned ancestor, and at that one call a poisoned ancestor and an ordinary
# deletion are indistinguishable. Absence is the only outcome both callers treat as
# innocuous -- a record removed between the listing and the read; an observation that
# simply has no receipt yet -- so an UNVERIFIED absence is the one answer that drops
# a live record from the page with no diagnostic at all, which is strictly worse than
# the named refusal above. The absent branch therefore re-checks the chain before
# concluding absence; an ancestor detected as poisoned becomes a named refusal.
#
# The handler is `except LessonError`, NOT `except Exception`: a genuine bug
# (TypeError, KeyError) still reaches main's backstop and still reports exit 3. Any
# refusal added anywhere beneath this call in the future -- including checks that do
# not exist yet -- is absorbed automatically.

ENTRY_OK = "ok"
ENTRY_ABSENT = "absent"
ENTRY_REFUSED = "refused"
ENTRY_NOT_A_FILE = "not-a-file"
ENTRY_UNREADABLE = "unreadable"

# The guard refusals that describe the ENTRY itself rather than its bytes. Mapping
# them here, at the one boundary, is what keeps the taxonomy from collapsing when
# the boundary absorbs a refusal raised too deep for the caller to have anticipated.
ENTRY_REFUSAL_CODES = frozenset((
    "state-path-is-a-reparse-point",
    "state-path-outside-inbox",
))


def _read_inbox_entry(inbox, path, observation_id, parse):
    """Read and parse ONE inbox entry under the per-entry failure contract.

    Returns (outcome, parsed) where outcome is one of the ENTRY_* constants and
    parsed is meaningful only for ENTRY_OK. Raises no refusal of its own: deciding
    what a withheld entry means to the page is the caller's job, and both callers
    keep their own distinct diagnostic codes.

    ONE lstat answers presence, link-ness and regular-file-ness together, so the
    three questions cannot disagree across a race and none of them is answered by a
    helper that hides an OSError behind False. The single exception is ABSENCE, which
    that lstat cannot answer alone: see the absent branch below.
    """
    try:
        st = _lstat_state_path(path)
        if st is None:
            # An absent conclusion must not be reached THROUGH an unverified
            # ancestor. The lstat above reports FileNotFoundError just as readily for
            # a leaf whose ancestor was redirected mid-page to somewhere that has no
            # file by this name, and both callers read ENTRY_ABSENT as innocuous and
            # continue WITHOUT a diagnostic -- so, unverified, this is the one branch
            # that can drop a live record from the page silently. Re-walking the
            # chain here checks for a poisoned ancestor at that point in time; one
            # detected by the guard raises and the handler below reports it as the
            # per-entry refusal the loops already name. A deletion costs one bounded
            # ancestor walk and still answers ENTRY_ABSENT.
            _guard_state_path(inbox, path)
            return ENTRY_ABSENT, None
        if _stat_is_reparse_point(st):
            return ENTRY_REFUSED, None
        if not stat.S_ISREG(st.st_mode):
            return ENTRY_NOT_A_FILE, None
        return ENTRY_OK, parse(
            _read_state_file(inbox, path, observation_id), observation_id)
    except LessonError as exc:
        if exc.code in ENTRY_REFUSAL_CODES:
            return ENTRY_REFUSED, None
        return ENTRY_UNREADABLE, None


def _load_observations(inbox, diagnostics):
    """Every well-formed saved observation, sorted by recorded_at then id.

    A malformed file is REPORTED and left in place: it never enters the ordering, so
    it can neither become a cursor value nor advance one, and one unreadable byte
    sequence cannot hide every later observation behind it.
    """
    entries = []
    # Guarded BEFORE the isdir probe: os.path.isdir FOLLOWS links, so asking it
    # first would answer through a redirected ancestor and then return a tidy empty
    # list -- a refusal silently reported as "nothing recorded yet".
    _guard_state_path(inbox, inbox.observations_dir)
    if not os.path.isdir(inbox.observations_dir):
        return entries
    for name in _list_state_dir(inbox.observations_dir):
        if name.endswith(TEMP_SUFFIX):
            continue
        path = os.path.join(inbox.observations_dir, name)
        stem, extension = os.path.splitext(name)
        if extension != OBSERVATION_SUFFIX or not UUID4_RE.match(stem):
            diagnostics.append(_diagnostic(
                DIAG_UNEXPECTED_ENTRY,
                "an entry in the private inbox does not have the observation "
                "filename shape; it was ignored."))
            continue
        outcome, envelope = _read_inbox_entry(
            inbox, path, stem, parse_observation_document)
        if outcome == ENTRY_OK:
            entries.append(envelope)
        elif outcome == ENTRY_ABSENT:
            # Absent at the read and ancestor re-check. A record removed between
            # listing and reading can be skipped without withholding that record.
            continue
        elif outcome == ENTRY_REFUSED:
            diagnostics.append(_diagnostic(
                DIAG_UNEXPECTED_ENTRY,
                "an inbox entry is a symlink or reparse point; it was refused and "
                "left in place.", stem))
        elif outcome == ENTRY_NOT_A_FILE:
            diagnostics.append(_diagnostic(
                DIAG_UNEXPECTED_ENTRY,
                "an inbox entry with the observation filename shape is not a file; "
                "it was ignored.", stem))
        else:
            diagnostics.append(_diagnostic(
                DIAG_MALFORMED_OBSERVATION,
                "a saved observation could not be read as the expected envelope; it "
                "was reported and left in place, and it does not advance the page "
                "cursor.", stem))
    entries.sort(key=lambda entry: (entry["recorded_at"], entry["observation_id"]))
    return entries


def _load_receipt_state(inbox, entries, diagnostics):
    """(completed ids, withheld ids) for the loaded observations.

    A receipt that cannot be read is WITHHELD rather than treated as absent. The two
    wrong answers are not symmetric: reporting an unreadable receipt as absent
    re-offers an already-dispositioned observation as a fresh candidate with no
    diagnostic at all, so the conservative direction is to say nothing about this
    observation and name it.
    """
    completed = set()
    withheld = set()
    _guard_state_path(inbox, inbox.receipts_dir)
    if not os.path.isdir(inbox.receipts_dir):
        return completed, withheld
    for entry in entries:
        observation_id = entry["observation_id"]
        path = os.path.join(inbox.receipts_dir, observation_id + RECEIPT_SUFFIX)
        outcome, _ = _read_inbox_entry(
            inbox, path, observation_id, parse_receipt_document)
        if outcome == ENTRY_ABSENT:
            # No receipt found at the read and ancestor re-check.
            continue
        if outcome == ENTRY_OK:
            completed.add(observation_id)
            continue
        withheld.add(observation_id)
        if outcome == ENTRY_REFUSED:
            diagnostics.append(_diagnostic(
                DIAG_UNEXPECTED_ENTRY,
                "a saved disposition receipt is a symlink or reparse point; it was "
                "refused and left in place, and the observation is withheld from "
                "candidates until it is resolved.", observation_id))
        elif outcome == ENTRY_NOT_A_FILE:
            diagnostics.append(_diagnostic(
                DIAG_UNEXPECTED_ENTRY,
                "a saved disposition receipt is not a regular file; it was refused "
                "and left in place, and the observation is withheld from candidates "
                "until it is resolved.", observation_id))
        else:
            diagnostics.append(_diagnostic(
                DIAG_MALFORMED_RECEIPT,
                "a saved disposition receipt could not be read as the expected "
                "envelope; the observation is withheld from candidates until it is "
                "resolved.", observation_id))
    return completed, withheld


def cmd_pending(args):
    limit = args.limit
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise LessonError("invalid-limit", "--limit must be an integer.")
    if not PAGE_LIMIT_MIN <= limit <= PAGE_LIMIT_MAX:
        raise LessonError(
            "invalid-limit",
            "--limit must be between " + str(PAGE_LIMIT_MIN) + " and "
            + str(PAGE_LIMIT_MAX) + ".")
    inbox = resolve_inbox(args.repo)
    diagnostics = []
    _guard_state_path(inbox, inbox.state_dir)
    entries = _load_observations(inbox, diagnostics)
    _report_abandoned_temporaries(inbox, inbox.observations_dir, diagnostics)
    _report_abandoned_temporaries(inbox, inbox.receipts_dir, diagnostics)
    completed, withheld = _load_receipt_state(inbox, entries, diagnostics)

    known_ids = set(entry["observation_id"] for entry in entries)
    # Correction relationships are derived over the WHOLE inbox, never over the page:
    # a correction sitting past the page boundary still makes its original historical.
    corrections = {}
    for entry in entries:
        earlier = entry["supersedes"]
        if earlier is not None:
            corrections.setdefault(earlier, []).append(entry["observation_id"])
    conflicted_originals = set(
        earlier for earlier, ids in corrections.items() if len(ids) > 1)
    conflicted_corrections = set()
    for earlier in conflicted_originals:
        conflicted_corrections.update(corrections[earlier])

    start = 0
    cursor = args.after
    if cursor is not None:
        if not UUID4_RE.match(str(cursor)):
            raise LessonError(
                "invalid-cursor", "--after must be a lowercase canonical UUID4.")
        index = None
        for position, entry in enumerate(entries):
            if entry["observation_id"] == cursor:
                index = position
                break
        if index is None:
            raise LessonError(
                "unknown-cursor",
                "--after does not name a readable observation in this repository's "
                "private inbox.", EXIT_INVALID, cursor)
        start = index + 1

    window = entries[start:start + limit]
    remaining = len(entries) - (start + len(window))
    next_after = window[-1]["observation_id"] if window and remaining > 0 else None

    observations = []
    for entry in window:
        observation_id = entry["observation_id"]
        if observation_id in withheld:
            continue
        if observation_id in completed:
            diagnostics.append(_diagnostic(
                DIAG_COMPLETED,
                "this observation already carries a final disposition receipt; it is "
                "not a candidate source.", observation_id))
            # A completed observation can ALSO have been corrected, and one that was
            # corrected twice carries a conflicting corrective branch the operator
            # still has to resolve. Reporting completion first and returning would
            # suppress that: the conflict is otherwise only visible from the
            # corrections' own entries, which can sit past this page's boundary --
            # the one place bounded paging is not allowed to hide a correction.
            if observation_id in corrections:
                related = sorted(corrections[observation_id])
                diagnostics.append(_diagnostic(
                    DIAG_SUPERSEDED,
                    "a later correction supersedes this observation; it is "
                    "historical and is never a source of a new candidate.",
                    observation_id, related))
                if observation_id in conflicted_originals:
                    diagnostics.append(_diagnostic(
                        DIAG_CORRECTION_CONFLICT,
                        "more than one correction supersedes this observation; the "
                        "corrective branch is reported and left undecided.",
                        observation_id, related))
            continue
        if observation_id in corrections:
            related = sorted(corrections[observation_id])
            diagnostics.append(_diagnostic(
                DIAG_SUPERSEDED,
                "a later correction supersedes this observation; it is historical and "
                "is never a source of a new candidate.", observation_id, related))
            if observation_id in conflicted_originals:
                diagnostics.append(_diagnostic(
                    DIAG_CORRECTION_CONFLICT,
                    "more than one correction supersedes this observation; the "
                    "corrective branch is reported and left undecided.",
                    observation_id, related))
            continue
        if observation_id in conflicted_corrections:
            earlier = entry["supersedes"]
            diagnostics.append(_diagnostic(
                DIAG_CORRECTION_CONFLICT,
                "this observation is one of several conflicting corrections of the "
                "same earlier observation; the corrective branch is reported and left "
                "undecided.", observation_id, sorted(corrections[earlier])))
            continue
        earlier = entry["supersedes"]
        if earlier is not None:
            if earlier in known_ids:
                diagnostics.append(_diagnostic(
                    DIAG_CORRECTION,
                    "this observation corrects an earlier one; the earlier record "
                    "stays historical.", observation_id, [earlier]))
            else:
                diagnostics.append(_diagnostic(
                    DIAG_SUPERSEDES_MISSING,
                    "this observation corrects an earlier record that is not readable "
                    "in this inbox; the correction itself remains eligible.",
                    observation_id, [earlier]))
        observations.append(entry)

    return {
        "schema": SCHEMA_PENDING,
        "observations": observations,
        "diagnostics": diagnostics,
        "remaining": remaining,
        "next_after": next_after,
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

class _Parser(argparse.ArgumentParser):
    """An ArgumentParser whose refusals obey this module's error contract.

    argparse runs BEFORE any code here: type= coercion, required= enforcement and
    an unknown subcommand are all decided inside parse_args, and the stock
    ArgumentParser.error prints a bare `usage:`/`error:` pair and calls sys.exit
    itself. The exit code would be 2, which is in contract by coincidence, but the
    stderr bytes would be free text -- so a caller doing json.loads(stderr) on a
    nonzero exit crashes on a malformed command line and succeeds on every other
    refusal. Raising the module's own error instead routes this class through
    _emit_error like everything else.

    add_subparsers defaults parser_class to type(self), so every subcommand parser
    inherits this behaviour without being constructed separately.
    """

    def error(self, message):
        raise LessonError(
            "invalid-arguments",
            "the command line was rejected: " + _bounded_argparse_message(message)
            + ".")


def _bounded_argparse_message(message):
    """argparse's own text, made safe to place inside a JSON diagnostic.

    The text can quote the caller's argv, so it is stripped of control characters
    and truncated rather than copied through: a diagnostic must not be steerable by
    the input it is describing.
    """
    text = CONTROL_CHAR_RE.sub(" ", str(message).replace("\n", " ").replace("\t", " "))
    text = " ".join(text.split()).rstrip(".")
    if len(text) > MAX_REPORTED_ARGUMENT_CHARS:
        text = text[:MAX_REPORTED_ARGUMENT_CHARS] + "..."
    return text


def build_parser():
    parser = _Parser(
        prog="lesson_observations",
        description="Private, immutable lesson observations for lesson-harvest.")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    new_id = sub.add_parser(
        "new-id", help="print one UUID4; no repository access and no writes")
    new_id.set_defaults(func=cmd_new_id)

    record = sub.add_parser("record", help="persist one immutable observation")
    record.add_argument("--repo", required=True,
                        help="path inside the target Git working tree")
    record.add_argument("--input", required=True, dest="input_path",
                        help="UTF-8 JSON request file, at most 16 KiB")
    record.set_defaults(func=cmd_record)

    pending = sub.add_parser(
        "pending", help="read-only bounded page of pending observations")
    pending.add_argument("--repo", required=True,
                         help="path inside the target Git working tree")
    pending.add_argument("--limit", type=int, default=PAGE_LIMIT_DEFAULT,
                         help="page size, 1..50 (default 20)")
    pending.add_argument("--after", default=None,
                         help="stateless cursor: an existing observation id")
    pending.set_defaults(func=cmd_pending)

    complete = sub.add_parser(
        "complete", help="persist one immutable disposition receipt")
    complete.add_argument("--repo", required=True,
                          help="path inside the target Git working tree")
    complete.add_argument("--input", required=True, dest="input_path",
                          help="UTF-8 JSON request file, at most 16 KiB")
    complete.set_defaults(func=cmd_complete)
    return parser


def _emit_error(exc):
    payload = {"code": exc.code, "message": exc.message}
    if exc.observation_id is not None:
        payload["observation_id"] = exc.observation_id
    sys.stderr.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main(argv=None):
    """Every exit from this CLI, mapped onto the closed {0, 2, 3} contract.

    parse_args sits INSIDE the try because _Parser.error raises this module's own
    error rather than printing usage text and calling sys.exit itself.

    The bare `except Exception` is the fail-closed backstop, and it is deliberate. A
    caller of this helper is a skill contract reading stderr as JSON; an
    unanticipated exception escaping main would hand it an interpreter traceback --
    an out-of-contract exit 1, absolute source paths on stderr, and, for an exception
    raised while rendering a record, fragments of private narrative inside the
    message. So the exception TYPE is reported and its message is NOT, and the code
    is 3: the operation did not complete and stdout carries no receipt. SystemExit
    and KeyboardInterrupt derive from BaseException and are deliberately not caught.
    """
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        payload = args.func(args)
    except LessonError as exc:
        _emit_error(exc)
        return exc.exit_code
    except Exception as exc:
        _emit_error(LessonError(
            "internal-error",
            "the helper failed with an unexpected " + type(exc).__name__
            + "; no record was published and no receipt was printed.",
            EXIT_CONFLICT))
        return EXIT_CONFLICT
    if payload is not None:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
