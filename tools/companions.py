"""Read and check the core companion manifest, config/companions.json.

The manifest lists the small tools Skill Mesh skills call (the companion
members), their ring, pinned tag, call sites and hooks. Its shape is owned by
documentation/core-companion-plan.md section 4 and described for other readers
by schemas/companions.schema.json. This tool is read-only: it opens files for
reading and writes only to stdout. It uses the Python standard library only.

Usage (from anywhere; paths resolve against this checkout unless given):

    python tools/companions.py inspect [--manifest FILE] [--root DIR]
    python tools/companions.py verify [--release] [--manifest FILE] [--root DIR]

    inspect    print the manifest rows as deterministic JSON. It first runs the
               same checks as verify (without --release); a manifest verify
               refuses gets verify's exit code and its findings, no rows
    verify     check the manifest against the membership rule (plan section 3)
               and the section 4 shape; print the findings as deterministic JSON
    --release  also require a non-null tag for every core and optional member
    --manifest the manifest to read (default: config/companions.json)
    --root     the Skill Mesh tree that caller paths resolve against
               (default: this checkout)

Exit codes. verify exits with the lowest code among its findings, so each kind
of violation has its own code:

    0   no finding
    2   usage error (argparse)
    3   the manifest is missing, unreadable, not UTF-8, not JSON (including a
        byte order mark, a repeated key, NaN or Infinity, or nesting too deep
        for the parser) or nested deeper than MAX_NESTING levels
    10  schema_version is newer than this reader (refused, portfolio P-4)
    11  duplicate slug
    12  members are not sorted by slug
    13  a core or optional member has no callers entry
    14  a skill-mesh caller path does not exist in the tree, or a caller entry
        is not a well-formed repo-relative or member: path (no ':' or control
        character in the path)
    15  repo is not a public https://github.com/<owner>/<slug> URL
    16  a non-null tag does not match ^v[0-9]+.[0-9]+.[0-9]+$
    17  a hook entry is malformed (unknown kind, missing or extra field)
    18  an argv entry holds a {token} other than {home} or {settings}
    19  --release only: a core or optional member has a null tag
    20  any other shape violation of plan section 4 (including a slug or cli
        that does not start with a letter or digit)
    21  an argv's first entry (the command) is not a bare command name: it must
        match CLI_PATTERN, so no leading '-', no path separator, no {token}

Every outcome is one of these codes with JSON-only stdout; argparse usage errors
(2) print to stderr and nothing to stdout.

member: caller entries name a call site in the member's own repository; they are
checked at the pinned tag by the contract suite (plan Step 11), not here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "config" / "companions.json"

SCHEMA_VERSION = 1

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_UNREADABLE = 3
EXIT_NEWER_SCHEMA = 10
EXIT_DUPLICATE_SLUG = 11
EXIT_UNSORTED = 12
EXIT_NO_CALLER = 13
EXIT_CALLER_PATH = 14
EXIT_REPO = 15
EXIT_TAG = 16
EXIT_HOOK = 17
EXIT_ARGV_TOKEN = 18
EXIT_RELEASE_TAG = 19
EXIT_SHAPE = 20
EXIT_COMMAND = 21

# The deepest nesting a manifest may use. The real manifest nests 6 levels
# (object, members, member, hooks, hook, argv); anything deeper is refused before
# any check runs, so no later step can recurse without bound.
MAX_NESTING = 32

CHECK_NAMES = {
    EXIT_UNREADABLE: "unreadable",
    EXIT_NEWER_SCHEMA: "newer-schema-version",
    EXIT_DUPLICATE_SLUG: "duplicate-slug",
    EXIT_UNSORTED: "unsorted-members",
    EXIT_NO_CALLER: "no-caller",
    EXIT_CALLER_PATH: "caller-path",
    EXIT_REPO: "repo",
    EXIT_TAG: "tag",
    EXIT_HOOK: "hook-entry",
    EXIT_ARGV_TOKEN: "argv-token",
    EXIT_RELEASE_TAG: "release-tag",
    EXIT_SHAPE: "shape",
    EXIT_COMMAND: "command",
}

# Patterns shared with schemas/companions.schema.json (a test asserts they agree).
# Each is matched with re.fullmatch, so "$" cannot accept a trailing newline.
# slug, hook name and cli start with a letter or digit, so none can be read as an
# option ("-x") or name a directory ("." or "..").
SLUG_PATTERN = r"^[a-z0-9][a-z0-9-]*$"
TAG_PATTERN = r"^v[0-9]+\.[0-9]+\.[0-9]+$"
REPO_PATTERN = r"^https://github\.com/[A-Za-z0-9-]+/[a-z0-9-]+$"
HOOK_NAME_PATTERN = r"^[a-z0-9][a-z0-9-]*$"
CLI_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]*$"
ARGV_ITEM_PATTERN = r"^(?:[^{}]|\{home\}|\{settings\})*$"

ARGV_TOKENS = ("{home}", "{settings}")

TOP_LEVEL_KEYS = ("schema_version", "members")
RINGS = ("core", "optional", "candidate")
INSTALLED_RINGS = ("core", "optional")
MEMBER_KEYS = (
    "slug",
    "ring",
    "repo",
    "tag",
    "cli",
    "health",
    "contract",
    "callers",
    "skills",
    "setup_write",
    "hooks",
    "setup",
    "candidate_note",
)
CONTRACT_KEYS = ("name", "schema_version")
SKILLS_KEYS = ("installer", "uninstaller", "names")
SETUP_WRITE_KEYS = ("install", "uninstall")
HOOK_KINDS = ("file", "member")
HOOK_KEYS = {
    "file": ("kind", "name", "host", "event", "matcher", "locate", "timeout"),
    "member": ("kind", "host", "event", "install", "uninstall", "check"),
}
HOOK_HOSTS = ("claude", "codex")
HOOK_TIMEOUT_MAX = 600
MEMBER_CALLER_PREFIX = "member:"


class ManifestError(Exception):
    def __init__(
        self,
        code: int,
        message: str,
        findings: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.findings = findings


class _DuplicateKey(ValueError):
    pass


class _NonFiniteNumber(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise _DuplicateKey(key)
        seen[key] = value
    return seen


def _reject_constant(name: str) -> Any:
    raise _NonFiniteNumber(name)


def _nesting_depth(value: Any) -> int:
    """Return how deeply value nests lists and objects (a scalar is 0), iteratively."""
    deepest = 0
    stack: list[tuple[Any, int]] = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        if isinstance(item, dict):
            children: Any = item.values()
        elif isinstance(item, list):
            children = item
        else:
            continue
        depth += 1
        deepest = max(deepest, depth)
        stack.extend((child, depth) for child in children)
    return deepest


def load_manifest(path: Path) -> Any:
    """Return the parsed manifest. Raises ManifestError(EXIT_UNREADABLE)."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise ManifestError(EXIT_UNREADABLE, "cannot read manifest: %s" % exc.strerror)
    except ValueError:
        raise ManifestError(EXIT_UNREADABLE, "cannot read manifest: invalid path")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ManifestError(EXIT_UNREADABLE, "manifest is not UTF-8")
    if text.startswith("\ufeff"):
        raise ManifestError(EXIT_UNREADABLE, "manifest starts with a byte order mark")
    try:
        manifest = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except _DuplicateKey as exc:
        raise ManifestError(
            EXIT_UNREADABLE, "manifest repeats the key %r in one object" % exc.args[0]
        )
    except _NonFiniteNumber as exc:
        raise ManifestError(
            EXIT_UNREADABLE, "manifest is not JSON: %s is not a JSON number" % exc
        )
    except RecursionError:
        raise ManifestError(
            EXIT_UNREADABLE,
            "manifest is not JSON this reader can parse: nested too deep",
        )
    except ValueError as exc:
        raise ManifestError(EXIT_UNREADABLE, "manifest is not JSON: %s" % exc)
    if _nesting_depth(manifest) > MAX_NESTING:
        raise ManifestError(
            EXIT_UNREADABLE,
            "manifest nests deeper than %d levels" % MAX_NESTING,
        )
    return manifest


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _match(pattern: str, value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


class _Findings:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    def add(self, code: int, member: str | None, field: str, message: str) -> None:
        self.items.append(
            {
                "check": CHECK_NAMES[code],
                "code": code,
                "field": field,
                "member": member,
                "message": message,
            }
        )

    def exit_code(self) -> int:
        return min((item["code"] for item in self.items), default=EXIT_OK)


def _check_keys(
    findings: _Findings,
    code: int,
    member: str | None,
    field: str,
    obj: dict[str, Any],
    keys: tuple[str, ...],
) -> bool:
    present = set(obj)
    expected = set(keys)
    missing = sorted(expected - present)
    extra = sorted(present - expected)
    if missing:
        findings.add(code, member, field, "missing field(s): %s" % ", ".join(missing))
    if extra:
        findings.add(code, member, field, "unknown field(s): %s" % ", ".join(extra))
    return not missing and not extra


def _check_argv(
    findings: _Findings,
    member: str,
    field: str,
    value: object,
    shape_code: int,
    allow_empty: bool = False,
) -> None:
    """Check one argv list.

    Shape problems use shape_code, tokens EXIT_ARGV_TOKEN and an unsafe command
    (argv[0]) EXIT_COMMAND.
    """
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        findings.add(shape_code, member, field, "argv must be a list of strings")
        return
    if not value and not allow_empty:
        findings.add(shape_code, member, field, "argv must not be empty")
        return
    if any(item == "" for item in value):
        findings.add(
            shape_code, member, field, "argv entries must not be empty strings"
        )
    if value and value[0] and not _match(CLI_PATTERN, value[0]):
        findings.add(
            EXIT_COMMAND,
            member,
            "%s[0]" % field,
            "command %r must be a bare command name matching %s"
            % (value[0], CLI_PATTERN),
        )
    for index, item in enumerate(value):
        if not _match(ARGV_ITEM_PATTERN, item):
            findings.add(
                EXIT_ARGV_TOKEN,
                member,
                "%s[%d]" % (field, index),
                "argv entry %r holds a {...} other than %s"
                % (item, " or ".join(ARGV_TOKENS)),
            )


def _bad_relative_path(text: str) -> str | None:
    """Return why text is not a clean repo-relative POSIX path, or None."""
    if not text:
        return "empty path"
    if any(ord(char) < 0x20 or char == "\x7f" for char in text):
        return "holds a control character"
    if "\\" in text:
        return "uses a backslash"
    if text.startswith("/") or re.match(r"^[A-Za-z]:", text):
        return "is absolute"
    if ":" in text:
        # A drive letter or an NTFS alternate data stream (file.md:stream).
        return "holds a ':'"
    parts = text.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return "has an empty, '.' or '..' segment"
    return None


def _caller_form_error(entry: str) -> str | None:
    """Return why a caller entry is not well formed, or None.

    A member: entry is checked for form only; containment in the member's
    checkout is the Step 11 contract suite's.
    """
    if entry.startswith(MEMBER_CALLER_PREFIX):
        why = _bad_relative_path(entry[len(MEMBER_CALLER_PREFIX) :])
        return "member: caller %r %s" % (entry, why) if why else None
    why = _bad_relative_path(entry)
    return "caller path %r %s" % (entry, why) if why else None


def _check_caller(
    findings: _Findings, member: str, index: int, entry: object, root: Path
) -> None:
    field = "callers[%d]" % index
    if not isinstance(entry, str):
        findings.add(EXIT_CALLER_PATH, member, field, "caller entry must be a string")
        return
    why = _caller_form_error(entry)
    if why:
        findings.add(EXIT_CALLER_PATH, member, field, why)
        return
    if entry.startswith(MEMBER_CALLER_PREFIX):
        return
    target = root.joinpath(*PurePosixPath(entry).parts)
    try:
        inside = target.resolve().is_relative_to(root.resolve()) and target.is_file()
    except (OSError, ValueError):
        inside = False
    if not inside:
        findings.add(
            EXIT_CALLER_PATH,
            member,
            field,
            "caller path %r does not exist in the tree" % entry,
        )


def _check_hook(
    findings: _Findings,
    member: str,
    index: int,
    hook: object,
    names_seen: set[str],
) -> None:
    field = "hooks[%d]" % index
    if not isinstance(hook, dict):
        findings.add(EXIT_HOOK, member, field, "hook entry must be an object")
        return
    kind = hook.get("kind")
    if kind not in HOOK_KINDS:
        findings.add(
            EXIT_HOOK, member, field, "kind must be one of: %s" % ", ".join(HOOK_KINDS)
        )
        return
    _check_keys(findings, EXIT_HOOK, member, field, hook, HOOK_KEYS[kind])
    if "host" in hook and hook["host"] not in HOOK_HOSTS:
        findings.add(
            EXIT_HOOK,
            member,
            field + ".host",
            "host must be one of: %s" % ", ".join(HOOK_HOSTS),
        )
    if "event" in hook and not (isinstance(hook["event"], str) and hook["event"]):
        findings.add(
            EXIT_HOOK, member, field + ".event", "event must be a non-empty string"
        )
    if kind == "file":
        if "name" in hook:
            if not _match(HOOK_NAME_PATTERN, hook["name"]):
                findings.add(
                    EXIT_HOOK,
                    member,
                    field + ".name",
                    "name must match %s" % HOOK_NAME_PATTERN,
                )
            elif hook["name"] in names_seen:
                findings.add(
                    EXIT_HOOK,
                    member,
                    field + ".name",
                    "hook name %r repeats" % hook["name"],
                )
            else:
                names_seen.add(hook["name"])
        if "matcher" in hook and not (
            isinstance(hook["matcher"], str) and hook["matcher"]
        ):
            findings.add(
                EXIT_HOOK,
                member,
                field + ".matcher",
                "matcher must be a non-empty string",
            )
        if "timeout" in hook:
            timeout = hook["timeout"]
            if not (_is_int(timeout) and 1 <= timeout <= HOOK_TIMEOUT_MAX):
                findings.add(
                    EXIT_HOOK,
                    member,
                    field + ".timeout",
                    "timeout must be an integer from 1 to %d" % HOOK_TIMEOUT_MAX,
                )
        if "locate" in hook:
            _check_argv(findings, member, field + ".locate", hook["locate"], EXIT_HOOK)
    else:
        for key in ("install", "uninstall", "check"):
            if key not in hook:
                continue
            argv = hook[key]
            _check_argv(findings, member, "%s.%s" % (field, key), argv, EXIT_HOOK)
            if isinstance(argv, list) and argv:
                flag_at = [i for i, item in enumerate(argv) if item == "--settings"]
                if not flag_at or flag_at[0] + 1 >= len(argv):
                    findings.add(
                        EXIT_HOOK,
                        member,
                        "%s.%s" % (field, key),
                        "a member hook command must take --settings <path>",
                    )


def _check_member(
    findings: _Findings, member_index: int, row: object, root: Path, release: bool
) -> None:
    if not isinstance(row, dict):
        findings.add(
            EXIT_SHAPE, None, "members[%d]" % member_index, "member must be an object"
        )
        return
    slug = row.get("slug")
    label = slug if isinstance(slug, str) else "members[%d]" % member_index
    _check_keys(findings, EXIT_SHAPE, label, "member", row, MEMBER_KEYS)

    if "slug" in row and not _match(SLUG_PATTERN, slug):
        findings.add(EXIT_SHAPE, label, "slug", "slug must match %s" % SLUG_PATTERN)

    ring = row.get("ring")
    if "ring" in row and ring not in RINGS:
        findings.add(
            EXIT_SHAPE, label, "ring", "ring must be one of: %s" % ", ".join(RINGS)
        )
    installed = ring in INSTALLED_RINGS

    # repo: a public GitHub URL whose name is the slug; required for core/optional.
    if "repo" in row:
        repo = row["repo"]
        if repo is None:
            if installed:
                findings.add(
                    EXIT_REPO,
                    label,
                    "repo",
                    "ring %s needs a public GitHub repo" % ring,
                )
        elif not _match(REPO_PATTERN, repo):
            findings.add(
                EXIT_REPO,
                label,
                "repo",
                "repo %r is not https://github.com/<owner>/<slug>" % (repo,),
            )
        elif _match(SLUG_PATTERN, slug) and repo.rsplit("/", 1)[1] != slug:
            findings.add(
                EXIT_REPO,
                label,
                "repo",
                "repo %r does not name the repository %r" % (repo, slug),
            )

    if "tag" in row:
        tag = row["tag"]
        if tag is not None and not _match(TAG_PATTERN, tag):
            findings.add(
                EXIT_TAG, label, "tag", "tag %r does not match %s" % (tag, TAG_PATTERN)
            )
        if release and installed and tag is None:
            findings.add(
                EXIT_RELEASE_TAG,
                label,
                "tag",
                "ring %s needs a pinned tag for a release" % ring,
            )

    if "cli" in row and not _match(CLI_PATTERN, row["cli"]):
        findings.add(
            EXIT_SHAPE,
            label,
            "cli",
            "cli must be a command name matching %s" % CLI_PATTERN,
        )

    if "health" in row:
        _check_argv(
            findings,
            label,
            "health",
            row["health"],
            EXIT_SHAPE,
            allow_empty=not installed,
        )

    if "contract" in row:
        contract = row["contract"]
        if contract is None:
            if installed:
                findings.add(
                    EXIT_SHAPE, label, "contract", "ring %s needs a contract" % ring
                )
        elif not isinstance(contract, dict):
            findings.add(
                EXIT_SHAPE, label, "contract", "contract must be an object or null"
            )
        elif _check_keys(
            findings, EXIT_SHAPE, label, "contract", contract, CONTRACT_KEYS
        ):
            if not (isinstance(contract["name"], str) and contract["name"]):
                findings.add(
                    EXIT_SHAPE,
                    label,
                    "contract.name",
                    "contract name must be a non-empty string",
                )
            version = contract["schema_version"]
            if not (_is_int(version) and version >= 1):
                findings.add(
                    EXIT_SHAPE,
                    label,
                    "contract.schema_version",
                    "must be an integer >= 1",
                )

    if "callers" in row:
        callers = row["callers"]
        if not isinstance(callers, list):
            findings.add(EXIT_SHAPE, label, "callers", "callers must be a list")
        else:
            if installed and not callers:
                findings.add(
                    EXIT_NO_CALLER,
                    label,
                    "callers",
                    "ring %s needs at least one caller" % ring,
                )
            if len(set(map(repr, callers))) != len(callers):
                findings.add(EXIT_SHAPE, label, "callers", "callers repeat an entry")
            for index, entry in enumerate(callers):
                _check_caller(findings, label, index, entry, root)

    if "skills" in row and row["skills"] is not None:
        skills = row["skills"]
        if not isinstance(skills, dict):
            findings.add(
                EXIT_SHAPE, label, "skills", "skills must be an object or null"
            )
        elif _check_keys(findings, EXIT_SHAPE, label, "skills", skills, SKILLS_KEYS):
            _check_argv(
                findings, label, "skills.installer", skills["installer"], EXIT_SHAPE
            )
            _check_argv(
                findings, label, "skills.uninstaller", skills["uninstaller"], EXIT_SHAPE
            )
            names = skills["names"]
            if (
                not isinstance(names, list)
                or not names
                or not all(_match(SLUG_PATTERN, name) for name in names)
                or len(set(names)) != len(names)
            ):
                findings.add(
                    EXIT_SHAPE,
                    label,
                    "skills.names",
                    "names must be a non-empty list of unique skill names",
                )

    if "setup_write" in row and row["setup_write"] is not None:
        setup_write = row["setup_write"]
        if not isinstance(setup_write, dict):
            findings.add(
                EXIT_SHAPE,
                label,
                "setup_write",
                "setup_write must be an object or null",
            )
        elif _check_keys(
            findings, EXIT_SHAPE, label, "setup_write", setup_write, SETUP_WRITE_KEYS
        ):
            _check_argv(
                findings,
                label,
                "setup_write.install",
                setup_write["install"],
                EXIT_SHAPE,
            )
            if setup_write["uninstall"] is not None:
                _check_argv(
                    findings,
                    label,
                    "setup_write.uninstall",
                    setup_write["uninstall"],
                    EXIT_SHAPE,
                )

    if "hooks" in row:
        hooks = row["hooks"]
        if not isinstance(hooks, list):
            findings.add(EXIT_SHAPE, label, "hooks", "hooks must be a list")
        else:
            names_seen = set()
            for index, hook in enumerate(hooks):
                _check_hook(findings, label, index, hook, names_seen)

    if "setup" in row:
        setup = row["setup"]
        if not isinstance(setup, list) or not all(
            isinstance(line, str) and line for line in setup
        ):
            findings.add(
                EXIT_SHAPE, label, "setup", "setup must be a list of non-empty strings"
            )

    if "candidate_note" in row:
        note = row["candidate_note"]
        if ring == "candidate":
            if not (isinstance(note, str) and note):
                findings.add(
                    EXIT_SHAPE,
                    label,
                    "candidate_note",
                    "a candidate names the hookup that promotes it",
                )
        elif ring in INSTALLED_RINGS and note is not None:
            findings.add(
                EXIT_SHAPE,
                label,
                "candidate_note",
                "only a candidate carries a candidate_note",
            )


def _check_header(findings: _Findings, manifest: Any) -> list[Any] | None:
    """Check the top level. Returns the members list to check, or None to stop."""
    if not isinstance(manifest, dict):
        findings.add(EXIT_SHAPE, None, "manifest", "manifest must be a JSON object")
        return None
    version = manifest.get("schema_version")
    if _is_int(version) and version > SCHEMA_VERSION:
        findings.add(
            EXIT_NEWER_SCHEMA,
            None,
            "schema_version",
            "schema_version %d is newer than this reader (%d); refusing to read it"
            % (version, SCHEMA_VERSION),
        )
        return None
    if version != SCHEMA_VERSION or not _is_int(version):
        findings.add(
            EXIT_SHAPE,
            None,
            "schema_version",
            "schema_version must be the integer %d" % SCHEMA_VERSION,
        )
    _check_keys(findings, EXIT_SHAPE, None, "manifest", manifest, TOP_LEVEL_KEYS)
    members = manifest.get("members")
    if not isinstance(members, list):
        findings.add(EXIT_SHAPE, None, "members", "members must be a list")
        return None
    return members


def verify(manifest: Any, root: Path, release: bool = False) -> list[dict[str, Any]]:
    """Return the list of findings for a parsed manifest."""
    findings = _Findings()
    members = _check_header(findings, manifest)
    if members is None:
        return findings.items

    slugs = [row.get("slug") for row in members if isinstance(row, dict)]
    slugs = [slug for slug in slugs if isinstance(slug, str)]
    for slug in sorted({slug for slug in slugs if slugs.count(slug) > 1}):
        findings.add(
            EXIT_DUPLICATE_SLUG,
            slug,
            "slug",
            "slug %r appears %d times" % (slug, slugs.count(slug)),
        )
    if slugs != sorted(slugs):
        findings.add(EXIT_UNSORTED, None, "members", "members must be sorted by slug")

    for index, row in enumerate(members):
        _check_member(findings, index, row, root, release)
    return findings.items


def inspect(manifest: Any, root: Path) -> dict[str, Any]:
    """Return the deterministic inspect view of a parsed manifest.

    The manifest must first pass verify (without --release), so the rows below
    read only shapes verify has accepted. Otherwise raises ManifestError with
    verify's exit code and findings.
    """
    items = verify(manifest, root)
    if items:
        first = min(items, key=lambda item: item["code"])
        raise ManifestError(first["code"], first["message"], findings=items)
    rows = []
    rings: dict[str, list[str]] = {ring: [] for ring in RINGS}
    for row in manifest["members"]:
        ring = row["ring"]
        rings[ring].append(row["slug"])
        skills = row["skills"]
        rows.append(
            {
                "slug": row["slug"],
                "ring": ring,
                "repo": row["repo"],
                "tag": row["tag"],
                "cli": row["cli"],
                "health": row["health"],
                "contract": row["contract"],
                "callers": row["callers"],
                "skills": skills["names"] if skills else None,
                "setup_write": row["setup_write"] is not None,
                "hooks": [
                    {
                        key: hook[key]
                        for key in ("kind", "name", "host", "event")
                        if key in hook
                    }
                    for hook in row["hooks"]
                ],
                "setup": row["setup"],
                "candidate_note": row["candidate_note"],
                "installable": ring in INSTALLED_RINGS and row["tag"] is not None,
            }
        )
    return {
        "members": rows,
        "rings": rings,
        "schema_version": manifest["schema_version"],
    }


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return path.as_posix()


def _member_count(manifest: Any) -> int | None:
    if isinstance(manifest, dict) and isinstance(manifest.get("members"), list):
        return len(manifest["members"])
    return None


def _emit(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    sys.stdout.flush()
    sys.stdout.buffer.write(text.encode("ascii"))
    sys.stdout.buffer.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "verify"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
        cmd.add_argument("--root", type=Path, default=REPO_ROOT)
        if name == "verify":
            cmd.add_argument("--release", action="store_true")
    args = parser.parse_args(argv)

    root = args.root
    if not root.is_dir():
        parser.error("--root is not a directory: %s" % root)
    display = _display_path(args.manifest, root)
    payload: dict[str, Any] = {"command": args.command, "manifest": display}
    if args.command == "verify":
        payload["release"] = args.release

    try:
        manifest = load_manifest(args.manifest)
        if args.command == "inspect":
            payload.update(inspect(manifest, root))
            payload["exit_code"] = EXIT_OK
            _emit(payload)
            return EXIT_OK
    except ManifestError as exc:
        if exc.findings:
            error = min(exc.findings, key=lambda item: item["code"])
            findings = exc.findings
        else:
            error = {
                "check": CHECK_NAMES[exc.code],
                "code": exc.code,
                "field": None,
                "member": None,
                "message": exc.message,
            }
            findings = [error]
        payload["exit_code"] = exc.code
        if args.command == "verify":
            payload.update({"findings": findings, "members": None, "ok": False})
        else:
            payload.update({"error": error, "findings": findings})
        _emit(payload)
        return exc.code

    items = verify(manifest, root, release=args.release)
    code = min((item["code"] for item in items), default=EXIT_OK)
    payload.update(
        {
            "exit_code": code,
            "findings": items,
            "members": _member_count(manifest),
            "ok": not items,
        }
    )
    _emit(payload)
    return code


if __name__ == "__main__":
    sys.exit(main())
