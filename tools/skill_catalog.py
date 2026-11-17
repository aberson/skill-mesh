"""Read-only catalog inspector and verifier for Skill Mesh lifecycle mutations.

Phase CL Step 112 (issue #170). Two commands, and neither writes a byte:

    python tools/skill_catalog.py inspect --operation READ --name <skill-slug> --format json
    python tools/skill_catalog.py verify --request-file <absolute-json-path> --format json

`inspect` reports the state a mutation would start from: whether the named identity
can take the requested operation, which paths are already dirty, and -- for DELETE and
RENAME -- every old-name occurrence the caller must disposition. `verify` reads one
normalized lifecycle request (documentation/skill-catalog-lifecycle.md section 6) and
judges the candidate worktree against the immutable preimage at `base_ref`.

Both commands also grade the whole catalog: the canonical skills/ tree, the manifest,
skills/inventory.json, the expected-inventory fixture, and config/model-mapping.json
must name exactly the same skills; every portable skill must carry an adapter for every
provider in the manifest's `portable_provider_contract.required`; and the three
generated artifacts must equal a regeneration by tools/gen_manifest.py.

EXIT CODES AND VERDICTS (the locked v1 contract, master plan section "Non-mutating
lifecycle helper"). Exit 0 is PASS, exit 2 is INVALID_REQUEST or PROHIBITED, exit 3 is
DRIFT. Several findings take the most severe verdict, in the order DRIFT, PROHIBITED,
INVALID_REQUEST. FINDING_VERDICTS below is the closed finding-code vocabulary; no other
code can be emitted.

JSON OUTPUT is UTF-8 with LF line endings and exactly one trailing LF. Object keys are
sorted. `required_providers` keeps manifest order; `findings` are sorted by (code, path,
detail), `references` by (path, line, column, before_sha256, class, rationale) and
`changed_paths` by path, so the same tree always yields the same bytes.

NEVER WRITES. Git runs with GIT_OPTIONAL_LOCKS=0 so a status-style read cannot refresh
the index, and the generator is imported with bytecode caching switched off so no
__pycache__ file is created. Git is invoked only with argument arrays and shell=False,
from the resolved repository root; every name, ref and path is validated before it
reaches an argument, and nothing is interpolated into a shell command.

HASHES AND COLUMNS. `before_sha256` is the SHA-256 of a file's bytes after the
normalization the generator and release tooling already apply (strip a UTF-8 BOM, fold
CRLF and lone CR to LF), because a checkout's line endings are a property of the clone.
Lines and columns are one-based and counted in characters of that normalized text.

Standard library only.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = 1
OPERATIONS = ("CREATE", "READ", "UPDATE", "DELETE", "RENAME")
MUTATIONS = ("CREATE", "UPDATE", "DELETE", "RENAME")
REFERENCE_OPERATIONS = ("DELETE", "RENAME")

# The normalized request, in the order the lifecycle guide's section 6 lists it.
REQUEST_FIELDS = ("operation", "skill_name", "new_name", "base_ref", "description",
                  "capabilities", "resource_paths", "reference_dispositions")
DISPOSITION_FIELDS = ("path", "line", "column", "before_sha256", "class", "rationale")
DISPOSITION_CLASSES = ("must-update", "historical-preserve")

# THE CLOSED FINDING VOCABULARY and the verdict each code carries.
FINDING_VERDICTS = {
    "INVALID_REQUEST_FILE": "INVALID_REQUEST",
    "INVALID_OPERATION": "INVALID_REQUEST",
    "INVALID_SKILL_NAME": "INVALID_REQUEST",
    "INVALID_BASE_REF": "INVALID_REQUEST",
    "TARGET_PATH_DIRTY": "INVALID_REQUEST",
    "SKILL_NOT_FOUND": "INVALID_REQUEST",
    "CREATE_COLLISION": "INVALID_REQUEST",
    "RENAME_DESTINATION_REQUIRED": "INVALID_REQUEST",
    "RENAME_DESTINATION_COLLISION": "INVALID_REQUEST",
    "REFERENCE_DISPOSITION_INVALID": "INVALID_REQUEST",
    "PROVIDER_NATIVE_REVIEW_REQUIRED": "PROHIBITED",
    "PACKAGE_RESOURCE_PLAN_REQUIRED": "PROHIBITED",
    "NOT_SKILL_MESH_SOURCE": "PROHIBITED",
    "REFERENCE_BINARY_MATCH": "PROHIBITED",
    "REQUIRED_PROVIDER_SET_DRIFT": "DRIFT",
    "MISSING_REQUIRED_ADAPTER": "DRIFT",
    "MODEL_MAPPING_DRIFT": "DRIFT",
    "INVENTORY_DRIFT": "DRIFT",
    "ORPHAN_SKILL_DIRECTORY": "DRIFT",
    "GENERATED_ONLY_EDIT": "DRIFT",
    "STALE_OLD_NAME_REFERENCE": "DRIFT",
    "CATALOG_MUTATION_INCOMPLETE": "DRIFT",
    "INTERNAL_ERROR": "DRIFT",
}
VERDICT_EXIT = {"PASS": 0, "INVALID_REQUEST": 2, "PROHIBITED": 2, "DRIFT": 3}
VERDICT_SEVERITY = ("DRIFT", "PROHIBITED", "INVALID_REQUEST")

MANIFEST_REL = "config/skill-manifest.json"
MODEL_MAPPING_REL = "config/model-mapping.json"
GENERATOR_REL = "tools/gen_manifest.py"
HELPER_REL = "tools/skill_catalog.py"
SKILLS_REL = "skills"
# The cross-skill payload namespace; never a skill (tools/gen_manifest.py skips it too).
SHARED_NAMESPACE = "_shared"

# The manifest name rule, owned by tests/package-integrity/test_manifest_contract.py
# (test_names_unique_and_kebab) and restated by the lifecycle guide's section 6.
NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
# Windows device names satisfy NAME_RE and behave unstably as path segments, so the
# guide's section 6 rejects the whole set before any path or pathspec is built.
DOS_DEVICE_NAMES = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{i}" for i in range(1, 10)}
    | {f"lpt{i}" for i in range(1, 10)})
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
# Characters that continue a kebab-name token. A match must not touch one on either
# side, so `build-step` does not match inside `build-steps` or `x-build-step`.
_NAME_CHARS = "A-Za-z0-9_-"

# Generated or consumer surfaces that a catalog change must never edit by hand
# (lifecycle guide section 3, "Forbidden, without exception").
_CONSUMER_ROOT_RE = re.compile(r"(?:^|/)\.(?:claude|agents|github)/skills(?:/|$)")
_LEGACY_PACKAGE_RE = re.compile(r"^[^/]+/SKILL[^/]*\.md$")

# Git environment variables that could redirect a command away from the resolved root.
_GIT_ENV_DROP = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_NAMESPACE",
                 "GIT_PREFIX", "GIT_CEILING_DIRECTORIES")


class GitError(RuntimeError):
    """A Git command exited nonzero."""


class _RequestStop(Exception):
    """The request cannot be evaluated further; its findings are already recorded."""


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #


def _finding(code, path, detail):
    if code not in FINDING_VERDICTS:
        raise ValueError(f"unlisted finding code {code!r}")
    if path is not None:
        path = str(path).replace("\\", "/")
    return {"code": code, "path": path, "detail": " ".join(str(detail).split())}


def _norm(data: bytes) -> bytes:
    """Strip a UTF-8 BOM, then fold CRLF and lone CR to LF."""
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(_norm(data)).hexdigest()


def _load_json_bytes(data: bytes):
    return json.loads(_norm(data).decode("utf-8"))


def _read_json(path: Path):
    return _load_json_bytes(path.read_bytes())


def valid_skill_name(value) -> bool:
    """True when `value` may become a skills/<name>/ path segment and a pathspec."""
    return (isinstance(value, str) and NAME_RE.fullmatch(value) is not None
            and value not in DOS_DEVICE_NAMES)


def _clean_rel(value) -> bool:
    """A slash-normalized, repository-relative path with no traversal."""
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return False
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return False
    return all(part not in ("", ".", "..") for part in value.split("/"))


@contextlib.contextmanager
def _no_bytecode():
    """Import repository code without writing a __pycache__ file into the tree."""
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        sys.dont_write_bytecode = previous


# --------------------------------------------------------------------------- #
# Git: argument arrays only, shell=False, from the resolved root
# --------------------------------------------------------------------------- #


def _git_env():
    env = {key: value for key, value in os.environ.items() if key not in _GIT_ENV_DROP}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def git(root: Path, args, stdin: bytes | None = None) -> bytes:
    """Run one Git command against `root`. `args` is a list of already-validated
    strings; it is passed as an argument array with shell=False."""
    argv = ["git", "-C", str(root), "-c", "core.quotepath=off", *args]
    if not all(isinstance(arg, str) for arg in argv):
        raise TypeError("git arguments must be strings")
    proc = subprocess.run(argv, input=stdin, capture_output=True, shell=False,
                          env=_git_env(), check=False)
    if proc.returncode != 0:
        message = proc.stderr.decode("utf-8", "replace").strip().splitlines()
        raise GitError(f"git {args[0]} exited {proc.returncode}"
                       + (f": {message[0]}" if message else ""))
    return proc.stdout


def _z_paths(data: bytes):
    return [item.decode("utf-8") for item in data.split(b"\0") if item]


def resolve_commit(root: Path, ref) -> str | None:
    """Return `ref` when it is a full 40-hex commit that exists, else None."""
    if not isinstance(ref, str) or COMMIT_RE.fullmatch(ref) is None:
        return None
    try:
        out = git(root, ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"])
    except GitError:
        return None
    resolved = out.decode("utf-8").strip()
    return resolved if resolved == ref else None


def changed_paths(root: Path, base: str):
    """Every path that differs between `base` and the working tree, plus every
    untracked, not-ignored file. `base` is "HEAD" or a validated commit."""
    diff = git(root, ["diff", "--name-only", "-z", "--no-renames", "--no-ext-diff",
                      base, "--"])
    untracked = git(root, ["ls-files", "-z", "--others", "--exclude-standard"])
    return sorted(set(_z_paths(diff)) | set(_z_paths(untracked)))


def worktree_files(root: Path):
    """Tracked plus untracked-but-not-ignored files that exist in the working tree."""
    listed = git(root, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"])
    return sorted(p for p in set(_z_paths(listed)) if (root / p).is_file())


def untracked_files(root: Path):
    """Untracked, non-ignored paths of the working tree."""
    return set(_z_paths(git(root, ["ls-files", "-z", "--others", "--exclude-standard"])))


def _base_blobs(root: Path, commit: str):
    """Map path -> bytes for every blob in `commit`'s tree."""
    listing = git(root, ["ls-tree", "-r", "-z", "--full-tree", commit])
    entries = []
    for item in listing.split(b"\0"):
        if not item:
            continue
        meta, _, path = item.partition(b"\t")
        parts = meta.split()
        if len(parts) == 3 and parts[1] == b"blob":
            entries.append((path.decode("utf-8"), parts[2].decode("ascii")))
    if not entries:
        return {}
    out = git(root, ["cat-file", "--batch"],
              stdin=("\n".join(oid for _, oid in entries) + "\n").encode("ascii"))
    blobs, pos = {}, 0
    for path, _oid in entries:
        header_end = out.index(b"\n", pos)
        header = out[pos:header_end].split()
        size = int(header[2])
        start = header_end + 1
        blobs[path] = out[start:start + size]
        pos = start + size + 1
    return blobs


def _base_file(root: Path, commit: str, rel: str):
    try:
        return git(root, ["show", f"{commit}:{rel}"])
    except GitError:
        return None


# --------------------------------------------------------------------------- #
# The Skill Mesh source predicate (lifecycle guide section 3)
# --------------------------------------------------------------------------- #


def source_findings(root: Path):
    """The target qualifies when it is a Git working tree whose top is `root` and it
    contains both config/skill-manifest.json and tools/skill_catalog.py."""
    try:
        top = git(root, ["rev-parse", "--show-toplevel"]).decode("utf-8").strip()
    except GitError:
        return [_finding("NOT_SKILL_MESH_SOURCE", None,
                         "the helper's repository root is not a Git working tree")]
    if os.path.normcase(os.path.realpath(top)) != os.path.normcase(os.path.realpath(root)):
        return [_finding("NOT_SKILL_MESH_SOURCE", None,
                         "the helper is not at the top of its Git working tree")]
    return [_finding("NOT_SKILL_MESH_SOURCE", rel, f"{rel} is missing")
            for rel in (MANIFEST_REL, HELPER_REL) if not (root / rel).is_file()]


# --------------------------------------------------------------------------- #
# Catalog: the five representations and their agreement
# --------------------------------------------------------------------------- #


def required_provider_set(manifest, vocabulary=None):
    """The manifest's ordered `portable_provider_contract.required`, or None when the
    field is absent or malformed. Valid means a non-empty list of unique, non-empty
    provider names that leads with claude and, when `vocabulary` is given, names only
    declared providers. This is the one Python statement of the rule; release_checks
    calls it. (tools/build-distributions.ps1 restates it in PowerShell, because the
    builder runs no Python.)"""
    contract = manifest.get("portable_provider_contract") if isinstance(manifest, dict) else None
    required = contract.get("required") if isinstance(contract, dict) else None
    if not (isinstance(required, list) and required
            and all(isinstance(p, str) and p for p in required)
            and len(set(required)) == len(required) and required[0] == "claude"):
        return None
    if vocabulary is not None and not set(required) <= set(vocabulary):
        return None
    return list(required)


def _is_native(record) -> bool:
    """A provider-native record: Claude-only, no neutral core."""
    return record.get("status") == "provider-native" or record.get("core") is None


def _load_generator(root: Path):
    path = root / GENERATOR_REL
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(f"skill_catalog_generator_{digest}", path)
    module = importlib.util.module_from_spec(spec)
    with _no_bytecode():
        spec.loader.exec_module(module)
    return module


class Catalog:
    """One tree's catalog representations, loaded and cross-checked.

    `findings` holds every disagreement. A representation that cannot be read is
    itself a finding, and the checks that need it are skipped rather than guessed.
    """

    def __init__(self, root: Path):
        self.root = root
        self.findings = []
        self.manifest = None
        self.records = {}
        self.vocabulary = []
        self.required = []
        self.required_valid = False
        self.capability_vocabulary = []
        self.artifacts = (MANIFEST_REL,)
        self.payloads = None
        self.tree = self._tree()
        self._load_manifest()

    # -- loading ----------------------------------------------------------- #

    def _tree(self):
        skills = self.root / SKILLS_REL
        tree = {}
        if skills.is_dir():
            for entry in sorted(skills.iterdir()):
                if entry.is_dir() and entry.name != SHARED_NAMESPACE:
                    tree[entry.name] = entry
        return tree

    def _add(self, code, path, detail):
        self.findings.append(_finding(code, path, detail))

    def _load_manifest(self):
        try:
            manifest = _read_json(self.root / MANIFEST_REL)
            skills = manifest["skills"]
            if not isinstance(skills, list) or not all(
                    isinstance(s, dict) and isinstance(s.get("name"), str) for s in skills):
                raise ValueError("`skills` is not a list of named records")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self._add("INVENTORY_DRIFT", MANIFEST_REL, f"the manifest cannot be read: {exc}")
            return
        self.manifest = manifest
        for record in skills:
            if record["name"] in self.records:
                self._add("INVENTORY_DRIFT", MANIFEST_REL,
                          f"the manifest repeats the skill {record['name']}")
            self.records[record["name"]] = record
        providers = manifest.get("providers")
        self.vocabulary = list(providers) if isinstance(providers, dict) else []
        caps = manifest.get("capability_vocabulary")
        self.capability_vocabulary = list(caps) if isinstance(caps, list) else []
        valid = required_provider_set(manifest, self.vocabulary)
        self.required_valid = valid is not None
        if valid is not None:
            self.required = valid
        else:
            contract = manifest.get("portable_provider_contract")
            required = contract.get("required") if isinstance(contract, dict) else None
            self.required = [p for p in (required if isinstance(required, list) else [])
                             if isinstance(p, str)]
            self._add("REQUIRED_PROVIDER_SET_DRIFT", MANIFEST_REL,
                      "portable_provider_contract.required must be a non-empty, unique, "
                      "ordered list of declared providers that leads with claude; found "
                      f"{required!r}")

    def present(self, name) -> bool:
        return name in self.records or name in self.tree

    def package_files(self, name, listed):
        """Package-relative paths of `listed` repository files under skills/<name>/."""
        prefix = f"{SKILLS_REL}/{name}/"
        return {p[len(prefix):] for p in listed if p.startswith(prefix)}

    def resources(self, files):
        """Package-local files other than the core and the provider adapters."""
        allowed = {"core.md"} | {f"providers/{p}.md" for p in self.vocabulary}
        return sorted(f for f in files if f not in allowed)

    # -- agreement ---------------------------------------------------------- #

    def check(self, changed=None, base_reader=None):
        """Grade every representation. `changed` is the set of changed paths and
        `base_reader(rel)` returns a file's base bytes; both are None when no Git
        preimage exists (the release gate), and then generated drift is reported as
        stale rather than classified."""
        if self.manifest is None:
            return self.findings
        self._load_generator()
        self._check_tree()
        self._check_counts()
        self._check_mapping()
        self._check_inventories()
        self._check_generator(changed, base_reader)
        return self.findings

    def _load_generator(self):
        """The generator owns the artifact list and the required-provider constant."""
        self.generator = None
        try:
            self.generator = _load_generator(self.root)
            self.artifacts = tuple(self.generator.ARTIFACTS)
        except Exception as exc:  # the generator is repository code; any failure is drift
            self.generator = None
            self._add("INVENTORY_DRIFT", GENERATOR_REL,
                      f"the generator cannot be loaded: {type(exc).__name__}: {exc}")

    def _adapters(self, name):
        providers_dir = self.tree[name] / "providers"
        return {p for p in self.vocabulary if (providers_dir / f"{p}.md").is_file()}

    def _check_tree(self):
        required = self.required if self.required else ["claude"]
        optional = [p for p in self.vocabulary if p not in required]
        for name in sorted(set(self.tree) - set(self.records)):
            self._add("ORPHAN_SKILL_DIRECTORY", f"{SKILLS_REL}/{name}",
                      f"skills/{name}/ is not a manifest record")
        for name in sorted(set(self.records) - set(self.tree)):
            self._add("INVENTORY_DRIFT", f"{SKILLS_REL}/{name}",
                      f"the manifest names {name} but skills/{name}/ does not exist")
        for name in sorted(self.tree):
            has_core = (self.tree[name] / "core.md").is_file()
            adapters = self._adapters(name)
            needed = required if has_core else ["claude"]
            for provider in needed:
                if provider not in adapters:
                    self._add("MISSING_REQUIRED_ADAPTER",
                              f"{SKILLS_REL}/{name}/providers/{provider}.md",
                              f"{name} is missing its required {provider} adapter")
            record = self.records.get(name)
            if record is None:
                continue
            declared = record.get("providers") if isinstance(record.get("providers"), dict) else {}
            if _is_native(record):
                if has_core:
                    self._add("INVENTORY_DRIFT", MANIFEST_REL,
                              f"{name} is provider-native in the manifest but carries core.md")
                extra = sorted((set(declared) | adapters) - {"claude"})
                if extra:
                    self._add("INVENTORY_DRIFT", f"{SKILLS_REL}/{name}",
                              f"provider-native {name} is Claude-only but carries {extra}")
            else:
                if record.get("status") != "portable":
                    self._add("INVENTORY_DRIFT", MANIFEST_REL,
                              f"{name} has unknown status {record.get('status')!r}")
                if not has_core:
                    self._add("INVENTORY_DRIFT", MANIFEST_REL,
                              f"{name} is portable in the manifest but has no core.md")
                if record.get("core") != f"{SKILLS_REL}/{name}/core.md":
                    self._add("INVENTORY_DRIFT", MANIFEST_REL,
                              f"{name} does not declare its canonical core path")
                for provider in self.vocabulary:
                    on_disk, listed = provider in adapters, provider in declared
                    if listed and declared[provider] != f"{SKILLS_REL}/{name}/providers/{provider}.md":
                        self._add("INVENTORY_DRIFT", MANIFEST_REL,
                                  f"{name} declares a non-canonical {provider} adapter path")
                    if on_disk and not listed:
                        self._add("INVENTORY_DRIFT", MANIFEST_REL,
                                  f"{name} carries a {provider} adapter the manifest does not declare")
                    elif listed and not on_disk and provider in optional:
                        # A missing REQUIRED adapter is already MISSING_REQUIRED_ADAPTER.
                        self._add("INVENTORY_DRIFT", MANIFEST_REL,
                                  f"{name} declares an optional {provider} adapter that does not exist")
                unknown = sorted(set(declared) - set(self.vocabulary))
                if unknown:
                    self._add("INVENTORY_DRIFT", MANIFEST_REL,
                              f"{name} declares providers outside the vocabulary: {unknown}")

    def _check_counts(self):
        counts = self.manifest.get("counts")
        if not isinstance(counts, dict):
            self._add("INVENTORY_DRIFT", MANIFEST_REL, "the manifest carries no counts")
            return
        records = list(self.records.values())
        recount = {
            "total": len(records),
            "portable": sum(1 for r in records if r.get("status") == "portable"),
            "provider_native": sum(1 for r in records if r.get("status") == "provider-native"),
        }
        for provider in self.vocabulary:
            recount[provider] = sum(1 for r in records
                                    if provider in (r.get("providers") or {}))
        for key, value in recount.items():
            if counts.get(key) != value:
                self._add("INVENTORY_DRIFT", MANIFEST_REL,
                          f"counts.{key} is {counts.get(key)!r}; the records give {value}")

    def _check_mapping(self):
        try:
            rows = _read_json(self.root / MODEL_MAPPING_REL)["skills"]
            if not isinstance(rows, dict):
                raise ValueError("`skills` is not an object")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self._add("MODEL_MAPPING_DRIFT", MODEL_MAPPING_REL,
                      f"the model mapping cannot be read: {exc}")
            return
        for name in sorted(set(self.records) - set(rows)):
            self._add("MODEL_MAPPING_DRIFT", MODEL_MAPPING_REL,
                      f"catalog skill {name} has no routing row; the router would fall "
                      "back to Claude-only for a shipped catalog member")
        for name in sorted(set(rows) - set(self.records)):
            self._add("MODEL_MAPPING_DRIFT", MODEL_MAPPING_REL,
                      f"routing row {name} names no catalog skill")
        for name in sorted(set(rows) & set(self.records)):
            row, record = rows[name], self.records[name]
            if not isinstance(row, dict):
                self._add("MODEL_MAPPING_DRIFT", MODEL_MAPPING_REL,
                          f"routing row {name} is not an object")
                continue
            expected = {
                "claude": True,
                "gpt": "gpt" in (record.get("providers") or {}),
                "local": record.get("local_capable"),
            }
            for key, value in expected.items():
                if row.get(key) is not value:
                    self._add("MODEL_MAPPING_DRIFT", MODEL_MAPPING_REL,
                              f"routing row {name}.{key} is {row.get(key)!r}; the "
                              f"manifest gives {value!r}")

    def _check_inventories(self):
        names = set(self.records)
        statuses = {n: r.get("status") for n, r in self.records.items()}
        counts = self.manifest.get("counts") if isinstance(self.manifest.get("counts"), dict) else {}
        for rel in self.artifacts:
            if rel == MANIFEST_REL:
                continue
            try:
                doc = _read_json(self.root / rel)
                rows = doc["skills"]
                listed = [r["name"] for r in rows]
            except (OSError, ValueError, KeyError, TypeError) as exc:
                self._add("INVENTORY_DRIFT", rel, f"cannot be read: {exc}")
                continue
            for name in sorted(names - set(listed)):
                self._add("INVENTORY_DRIFT", rel, f"lacks the catalog skill {name}")
            for name in sorted(set(listed) - names):
                self._add("INVENTORY_DRIFT", rel, f"names {name}, which the manifest does not")
            for row in rows:
                name = row.get("name")
                if name not in names:
                    continue
                if row.get("status") != statuses[name]:
                    self._add("INVENTORY_DRIFT", rel,
                              f"{name} status {row.get('status')!r} disagrees with the manifest")
                if "core" in row and row["core"] != bool(self.records[name].get("core")):
                    self._add("INVENTORY_DRIFT", rel, f"{name} core flag disagrees with the manifest")
                if isinstance(row.get("providers"), dict):
                    declared = self.records[name].get("providers") or {}
                    for provider in self.vocabulary:
                        if bool(row["providers"].get(provider)) != (provider in declared):
                            self._add("INVENTORY_DRIFT", rel,
                                      f"{name} {provider} flag disagrees with the manifest")
            doc_counts = doc.get("counts") if isinstance(doc.get("counts"), dict) else {}
            for key, value in doc_counts.items():
                if counts.get(key) != value:
                    self._add("INVENTORY_DRIFT", rel,
                              f"counts.{key} is {value!r}; the manifest gives {counts.get(key)!r}")
            rosters = {
                "portable": {n for n, s in statuses.items() if s == "portable"},
                "provider_native": {n for n, s in statuses.items() if s == "provider-native"},
                "codex": {n for n, r in self.records.items()
                          if "codex" in (r.get("providers") or {})},
            }
            for key, expected in rosters.items():
                if key in doc and set(doc[key]) != expected:
                    self._add("INVENTORY_DRIFT", rel, f"its {key} roster disagrees with the manifest")

    def _check_generator(self, changed, base_reader):
        generator = self.generator
        if generator is None:
            return
        required = getattr(generator, "REQUIRED_PROVIDERS", None)
        if required is None or list(required) != self.required:
            self._add("REQUIRED_PROVIDER_SET_DRIFT", GENERATOR_REL,
                      f"the generator's REQUIRED_PROVIDERS {required!r} disagrees with the "
                      f"manifest's {self.required!r}")
        try:
            with _no_bytecode():
                _, payloads = generator.render_artifacts()
        except Exception as exc:  # a refused regeneration is drift, whatever its type
            self._add("INVENTORY_DRIFT", GENERATOR_REL,
                      f"regeneration refused: {type(exc).__name__}: {exc}")
            return
        self.payloads = payloads
        for rel, data in payloads.items():
            path = self.root / rel
            if not path.is_file():
                self._add("INVENTORY_DRIFT", rel, "missing; run python tools/gen_manifest.py")
                continue
            if _norm(path.read_bytes()) == _norm(data):
                continue
            base = base_reader(rel) if (changed is not None and rel in changed
                                        and base_reader is not None) else None
            if base is not None and _norm(base) == _norm(data):
                self._add("GENERATED_ONLY_EDIT", rel,
                          "hand-edited: its generator inputs still reproduce the base bytes")
            else:
                self._add("INVENTORY_DRIFT", rel,
                          "stale: differs from a regeneration; run python tools/gen_manifest.py")


def catalog_findings(root: Path):
    """The Git-free catalog agreement findings for one tree (the release gate's entry)."""
    return Catalog(root).check()


def surface_findings(paths, names):
    """A changed path on a generated, distribution, release, consumer, or legacy
    compatibility surface is a generated-only edit. `names` is the set of catalog
    skill names; a legacy package is a top-level `<name>/SKILL*.md` for one of them."""
    findings = []
    for path in paths:
        if path == "dist" or path.startswith("dist/"):
            what = "the generated distribution"
        elif path == "release-stage" or path.startswith("release-stage/"):
            what = "release staging"
        elif _CONSUMER_ROOT_RE.search(path):
            what = "a consumer discovery root"
        elif _LEGACY_PACKAGE_RE.match(path) and path.split("/", 1)[0] in names:
            what = "a legacy top-level compatibility package"
        else:
            continue
        findings.append(_finding("GENERATED_ONLY_EDIT", path,
                                 f"{path} is {what}; it is produced, never edited"))
    return findings


# --------------------------------------------------------------------------- #
# Old-name references (DELETE and RENAME)
# --------------------------------------------------------------------------- #


def _token_patterns(name):
    """The old-name token as a whole kebab word: a (text, bytes) pattern pair."""
    pattern = rf"(?<![{_NAME_CHARS}]){re.escape(name)}(?![{_NAME_CHARS}])"
    return re.compile(pattern), re.compile(pattern.encode("ascii"))


def scan_bytes(data: bytes, patterns):
    """Return (occurrences, binary): one-based (line, column) pairs of the token in a
    UTF-8 text file, or binary=True when the token occurs in a non-text file."""
    text_re, raw_re = patterns
    if raw_re.search(data) is None:
        return [], False
    if b"\x00" in data:
        return [], True
    try:
        text = _norm(data).decode("utf-8")
    except UnicodeDecodeError:
        return [], True
    occurrences = []
    for number, line in enumerate(text.split("\n"), 1):
        occurrences.extend((number, m.start() + 1) for m in text_re.finditer(line))
    return occurrences, False


def scan_files(files: dict, patterns):
    """`files` maps path -> bytes. Returns (occurrences: path -> (sha, set), binary)."""
    occurrences, binary = {}, []
    for path in sorted(files):
        found, is_binary = scan_bytes(files[path], patterns)
        if is_binary:
            binary.append(path)
        elif found:
            occurrences[path] = (_sha256(files[path]), set(found))
    return occurrences, binary


def _read_worktree(root: Path, paths):
    return {p: (root / p).read_bytes() for p in paths}


# --------------------------------------------------------------------------- #
# Request validation
# --------------------------------------------------------------------------- #


class Evaluation:
    """One command's accumulating result."""

    def __init__(self, command):
        self.command = command
        self.operation = None
        self.skill_name = None
        self.new_name = None
        self.base_ref = None
        self.findings = []
        self.references = []
        self.changed = []
        self.required = []

    def add(self, code, path, detail):
        self.findings.append(_finding(code, path, detail))

    def stop(self, code, path, detail):
        self.add(code, path, detail)
        raise _RequestStop()

    def result(self):
        unique = {(f["code"], f["path"] or "", f["detail"]): f for f in self.findings}
        findings = [unique[key] for key in sorted(unique)]
        verdict = "PASS"
        for candidate in VERDICT_SEVERITY:
            if any(FINDING_VERDICTS[f["code"]] == candidate for f in findings):
                verdict = candidate
                break
        references = sorted(self.references, key=lambda r: (
            r["path"], r["line"], r["column"], r["before_sha256"],
            r["class"] or "", r["rationale"] or ""))
        return {
            "schema_version": SCHEMA_VERSION,
            "command": self.command,
            "operation": self.operation,
            "skill_name": self.skill_name,
            "new_name": self.new_name,
            "base_ref": self.base_ref,
            "verdict": verdict,
            "exit_code": VERDICT_EXIT[verdict],
            "required_providers": list(self.required),
            "findings": findings,
            "references": references,
            "changed_paths": sorted(set(self.changed)),
        }


def _validate_identity(ev: Evaluation, operation, skill_name, new_name):
    """Operation and names. Names are validated before any path is built from them."""
    if operation not in OPERATIONS:
        ev.stop("INVALID_OPERATION", None,
                f"operation must be one of {', '.join(OPERATIONS)}; got {operation!r}")
    if not valid_skill_name(skill_name):
        ev.stop("INVALID_SKILL_NAME", None,
                f"skill_name {skill_name!r} is not a kebab-case slug, or is a Windows "
                "device name")
    if operation == "RENAME":
        if new_name is None:
            ev.stop("RENAME_DESTINATION_REQUIRED", None, "a RENAME needs new_name")
        if not valid_skill_name(new_name):
            ev.stop("INVALID_SKILL_NAME", None,
                    f"new_name {new_name!r} is not a kebab-case slug, or is a Windows "
                    "device name")
        if new_name == skill_name:
            ev.stop("RENAME_DESTINATION_COLLISION", None,
                    "new_name equals skill_name")
    elif new_name is not None:
        ev.stop("INVALID_REQUEST_FILE", None, f"new_name must be null for {operation}")


def _validate_base_ref(ev: Evaluation, root: Path, operation, base_ref, required):
    if operation == "READ":
        if base_ref is not None:
            ev.stop("INVALID_BASE_REF", None, "base_ref must be null for READ")
        return None
    if base_ref is None:
        if required:
            ev.stop("INVALID_BASE_REF", None, f"a {operation} needs a full 40-hex base_ref")
        return None
    if not isinstance(base_ref, str) or COMMIT_RE.fullmatch(base_ref) is None:
        ev.stop("INVALID_BASE_REF", None, "base_ref must be a full 40-hex lowercase commit")
    if resolve_commit(root, base_ref) is None:
        ev.stop("INVALID_BASE_REF", None, "base_ref does not resolve to a commit")
    return base_ref


def _read_request(ev: Evaluation, request_file):
    """Read the request file once. Returns the parsed object."""
    if not isinstance(request_file, str) or not os.path.isabs(request_file):
        ev.stop("INVALID_REQUEST_FILE", None, "--request-file must be an absolute path")
    path = Path(request_file)
    if path.is_symlink() or not path.is_file():
        ev.stop("INVALID_REQUEST_FILE", None, "--request-file is not a regular file")
    try:
        data = path.read_bytes()
    except OSError as exc:
        ev.stop("INVALID_REQUEST_FILE", None, f"cannot read the request file: {exc}")

    def _no_duplicates(pairs):
        keys = [k for k, _ in pairs]
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate key")
        return dict(pairs)

    # Any file the parser cannot turn into a value is an invalid request, never an
    # internal error: undecodable bytes and malformed JSON raise ValueError, and a
    # pathologically nested document exhausts the decoder's recursion guard
    # (RecursionError) or, for a huge one, memory.
    try:
        request = json.loads(_norm(data).decode("utf-8"), object_pairs_hook=_no_duplicates)
    except (ValueError, RecursionError, MemoryError) as exc:
        ev.stop("INVALID_REQUEST_FILE", None,
                f"the request is not parseable UTF-8 JSON: {type(exc).__name__}: {exc}")
    if not isinstance(request, dict):
        ev.stop("INVALID_REQUEST_FILE", None, "the request is not a JSON object")
    # Echo what can be echoed before the shape is judged, so a refused request still
    # names itself in the result.
    for field in ("operation", "skill_name", "new_name", "base_ref"):
        value = request.get(field)
        setattr(ev, field, value if isinstance(value, str) else None)
    unknown = sorted(set(request) - set(REQUEST_FIELDS))
    missing = [f for f in REQUEST_FIELDS if f not in request]
    if unknown or missing:
        ev.stop("INVALID_REQUEST_FILE", None,
                f"the request must carry exactly the eight normalized fields; unknown "
                f"{unknown}, missing {missing}")
    types = {
        "operation": (str,), "skill_name": (str,), "new_name": (str, type(None)),
        "base_ref": (str, type(None)), "description": (str, type(None)),
        "capabilities": (list,), "resource_paths": (list,),
        "reference_dispositions": (list,),
    }
    wrong = [f for f, allowed in types.items() if not isinstance(request[f], allowed)]
    if wrong:
        ev.stop("INVALID_REQUEST_FILE", None, f"fields of the wrong type: {wrong}")
    return request


def _validate_metadata(ev: Evaluation, request, catalog: Catalog):
    operation = request["operation"]
    description, capabilities = request["description"], request["capabilities"]
    if not all(isinstance(c, str) for c in capabilities):
        ev.stop("INVALID_REQUEST_FILE", None, "capabilities must be strings")
    if (capabilities != sorted(set(capabilities))
            or not set(capabilities) <= set(catalog.capability_vocabulary)):
        ev.stop("INVALID_REQUEST_FILE", None,
                "capabilities must be unique, sorted members of "
                f"{catalog.capability_vocabulary}")
    if description is not None and (not description.strip() or "\n" in description
                                    or "\r" in description):
        ev.stop("INVALID_REQUEST_FILE", None, "description must be one non-empty line")
    if operation == "CREATE" and (description is None or not capabilities):
        ev.stop("INVALID_REQUEST_FILE", None, "a CREATE needs a description and capabilities")
    if operation in ("READ", "DELETE", "RENAME") and (description is not None or capabilities):
        ev.stop("INVALID_REQUEST_FILE", None,
                f"a {operation} carries no description and no capabilities")
    if not all(isinstance(p, str) for p in request["resource_paths"]):
        ev.stop("INVALID_REQUEST_FILE", None, "resource_paths must be strings")
    for rel in sorted(request["resource_paths"]):
        ev.add("PACKAGE_RESOURCE_PLAN_REQUIRED", rel if _clean_rel(rel) else None,
               "the request adds, removes, or relocates a package-local resource; that "
               "needs a scoped packaging plan")
    if operation not in REFERENCE_OPERATIONS and request["reference_dispositions"]:
        ev.stop("REFERENCE_DISPOSITION_INVALID", None,
                f"a {operation} carries no reference dispositions")


def _valid_dispositions(ev: Evaluation, dispositions):
    """Shape-check each disposition; return the valid ones keyed by (path, line, column)."""
    valid = {}
    for index, record in enumerate(dispositions):
        where = f"reference_dispositions[{index}]"
        if not isinstance(record, dict) or sorted(record) != sorted(DISPOSITION_FIELDS):
            ev.add("REFERENCE_DISPOSITION_INVALID", None,
                   f"{where} must carry exactly {list(DISPOSITION_FIELDS)}")
            continue
        path = record["path"]
        problems = []
        if not _clean_rel(path):
            problems.append("path is not slash-normalized and repository-relative")
        for field in ("line", "column"):
            value = record[field]
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                problems.append(f"{field} must be a positive integer")
        if not isinstance(record["before_sha256"], str) or \
                SHA256_RE.fullmatch(record["before_sha256"]) is None:
            problems.append("before_sha256 must be 64 lowercase hex characters")
        if record["class"] not in DISPOSITION_CLASSES:
            problems.append(f"class must be one of {list(DISPOSITION_CLASSES)}")
        if not isinstance(record["rationale"], str) or not record["rationale"].strip():
            problems.append("rationale must be a non-empty string")
        if problems:
            ev.add("REFERENCE_DISPOSITION_INVALID", path if _clean_rel(path) else None,
                   f"{where}: {'; '.join(problems)}")
            continue
        key = (path, record["line"], record["column"])
        if key in valid:
            ev.add("REFERENCE_DISPOSITION_INVALID", path,
                   f"duplicate disposition for {path}:{key[1]}:{key[2]}")
            continue
        valid[key] = dict(record)
    return valid


# --------------------------------------------------------------------------- #
# inspect
# --------------------------------------------------------------------------- #


def _target_paths(catalog: Catalog, names):
    return ([f"{SKILLS_REL}/{n}/" for n in names]
            + [MODEL_MAPPING_REL, GENERATOR_REL] + list(catalog.artifacts))


def _touches(path, targets):
    return any(path == t or (t.endswith("/") and path.startswith(t)) for t in targets)


def inspect(ev: Evaluation, root: Path, operation, skill_name, new_name, base_ref):
    ev.operation, ev.skill_name, ev.new_name, ev.base_ref = operation, skill_name, new_name, base_ref
    for finding in source_findings(root):
        ev.findings.append(finding)
    if ev.findings:
        raise _RequestStop()
    catalog = Catalog(root)
    ev.required = catalog.required
    dirty = changed_paths(root, "HEAD")
    ev.changed = dirty
    ev.findings.extend(surface_findings(dirty, set(catalog.records) | set(catalog.tree)))
    ev.findings.extend(catalog.check(set(dirty), lambda rel: _base_file(root, "HEAD", rel)))

    _validate_identity(ev, operation, skill_name, new_name)
    _validate_base_ref(ev, root, operation, base_ref, required=False)

    if operation == "CREATE":
        if catalog.present(skill_name):
            ev.add("CREATE_COLLISION", f"{SKILLS_REL}/{skill_name}",
                   f"{skill_name} already exists")
    elif not catalog.present(skill_name):
        ev.stop("SKILL_NOT_FOUND", None, f"{skill_name} is not a catalog skill")
    if operation == "RENAME" and catalog.present(new_name):
        ev.add("RENAME_DESTINATION_COLLISION", f"{SKILLS_REL}/{new_name}",
               f"{new_name} already exists")
    record = catalog.records.get(skill_name)
    if operation != "READ" and record is not None and _is_native(record):
        ev.add("PROVIDER_NATIVE_REVIEW_REQUIRED", f"{SKILLS_REL}/{skill_name}",
               f"{skill_name} is provider-native; a mutation needs an operator-approved "
               "architecture plan")
    if operation in MUTATIONS:
        names = [skill_name] + ([new_name] if operation == "RENAME" else [])
        targets = _target_paths(catalog, names)
        for path in dirty:
            if _touches(path, targets):
                ev.add("TARGET_PATH_DIRTY", path,
                       f"{path} already has an uncommitted change in this mutation's targets")
    listed = worktree_files(root)
    if operation in REFERENCE_OPERATIONS:
        for rel in catalog.resources(catalog.package_files(skill_name, listed)):
            ev.add("PACKAGE_RESOURCE_PLAN_REQUIRED", f"{SKILLS_REL}/{skill_name}/{rel}",
                   f"a {operation} moves or removes this package-local resource")
        occurrences, binary = scan_files(_read_worktree(root, listed),
                                         _token_patterns(skill_name))
        for path in binary:
            ev.add("REFERENCE_BINARY_MATCH", path,
                   f"{skill_name} occurs in a non-text file; review it by hand")
        for path, (sha, found) in occurrences.items():
            for line, column in found:
                ev.references.append({"path": path, "line": line, "column": column,
                                      "before_sha256": sha, "class": None,
                                      "rationale": None})


# --------------------------------------------------------------------------- #
# verify
# --------------------------------------------------------------------------- #


class Preimage:
    """The catalog identities at base_ref, read through Git without a checkout."""

    def __init__(self, root: Path, commit: str):
        data = _base_file(root, commit, MANIFEST_REL)
        if data is None:
            raise ValueError("base_ref carries no config/skill-manifest.json")
        manifest = _load_json_bytes(data)
        self.records = {r["name"]: r for r in manifest["skills"]}
        dirs = git(root, ["ls-tree", "-d", "-z", "--name-only", commit, "--", f"{SKILLS_REL}/"])
        self.tree = {p.split("/", 1)[1] for p in _z_paths(dirs)
                     if p.count("/") == 1 and p.split("/", 1)[1] != SHARED_NAMESPACE}
        files = git(root, ["ls-tree", "-r", "-z", "--name-only", commit, "--", f"{SKILLS_REL}/"])
        self.files = _z_paths(files)

    def present(self, name) -> bool:
        return name in self.records or name in self.tree


def _check_existence(ev, operation, old, new, pre: Preimage, cand: Catalog):
    """The existence matrix (lifecycle guide section 7), judged across the preimage at
    base_ref and the candidate worktree. A request-validity failure stops here: the
    candidate cannot be judged against a request that names the wrong identity."""
    if operation == "CREATE":
        if pre.present(old):
            ev.stop("CREATE_COLLISION", f"{SKILLS_REL}/{old}", f"{old} exists at base_ref")
        if not cand.present(old):
            ev.add("CATALOG_MUTATION_INCOMPLETE", f"{SKILLS_REL}/{old}",
                   f"the candidate does not contain {old}")
        return
    if not pre.present(old):
        ev.stop("SKILL_NOT_FOUND", None, f"{old} is not a catalog skill at base_ref")
    if operation == "RENAME" and pre.present(new):
        ev.stop("RENAME_DESTINATION_COLLISION", f"{SKILLS_REL}/{new}",
                f"{new} exists at base_ref")
    if operation == "UPDATE" and not cand.present(old):
        ev.add("CATALOG_MUTATION_INCOMPLETE", f"{SKILLS_REL}/{old}",
               f"an UPDATE removed {old}")
    if operation in ("DELETE", "RENAME") and cand.present(old):
        ev.add("CATALOG_MUTATION_INCOMPLETE", f"{SKILLS_REL}/{old}",
               f"{old} is still present in the candidate")
    if operation == "RENAME" and not cand.present(new):
        ev.add("CATALOG_MUTATION_INCOMPLETE", f"{SKILLS_REL}/{new}",
               f"the candidate does not contain {new}")


def _check_native_and_resources(ev, request, pre: Preimage, cand: Catalog, listed):
    operation, old, new = request["operation"], request["skill_name"], request["new_name"]
    base_record = pre.records.get(old)
    if operation != "CREATE" and base_record is not None and _is_native(base_record):
        ev.add("PROVIDER_NATIVE_REVIEW_REQUIRED", f"{SKILLS_REL}/{old}",
               f"{old} is provider-native; a mutation needs an operator-approved "
               "architecture plan")
    if operation == "CREATE":
        record = cand.records.get(old)
        coreless = old in cand.tree and not (cand.tree[old] / "core.md").is_file()
        if coreless or (record is not None and _is_native(record)):
            ev.add("PROVIDER_NATIVE_REVIEW_REQUIRED", f"{SKILLS_REL}/{old}",
                   "a CREATE may not add a provider-native identity")
    base_resources = set(cand.resources(cand.package_files(old, pre.files)))
    after_name = new if operation == "RENAME" else old
    cand_resources = set(cand.resources(cand.package_files(after_name, listed)))
    if operation == "CREATE":
        moved = cand_resources
    elif operation == "UPDATE":
        moved = base_resources ^ cand_resources
    else:
        moved = base_resources | cand_resources
    for rel in sorted(moved):
        owner = old if rel in base_resources else after_name
        ev.add("PACKAGE_RESOURCE_PLAN_REQUIRED", f"{SKILLS_REL}/{owner}/{rel}",
               f"a {operation} adds, removes, or relocates this package-local resource")
    if operation == "UPDATE" and base_record is not None and old in cand.records:
        if base_record.get("support_assets") != cand.records[old].get("support_assets"):
            ev.add("PACKAGE_RESOURCE_PLAN_REQUIRED", MANIFEST_REL,
                   f"an UPDATE changed {old}'s declared support assets")
    if operation == "CREATE" and old in cand.records and cand.records[old].get("support_assets"):
        ev.add("PACKAGE_RESOURCE_PLAN_REQUIRED", MANIFEST_REL,
               f"a CREATE declares support assets for {old}")


def _check_created_record(ev, request, cand: Catalog):
    record = cand.records.get(request["skill_name"])
    if record is None:
        return
    name = request["skill_name"]
    if request["description"] is not None and record.get("description") != request["description"]:
        ev.add("CATALOG_MUTATION_INCOMPLETE", MANIFEST_REL,
               f"{name}'s manifest description differs from the request")
    if request["capabilities"] and record.get("capabilities") != request["capabilities"]:
        ev.add("CATALOG_MUTATION_INCOMPLETE", MANIFEST_REL,
               f"{name}'s manifest capabilities differ from the request")
    if request["operation"] == "CREATE" and (record.get("origin") != "canonical"
                                             or record.get("migration") is not None):
        ev.add("CATALOG_MUTATION_INCOMPLETE", MANIFEST_REL,
               f"a created skill records origin canonical with migration null; {name} does not")


def _check_references(ev, root: Path, request, commit: str, listed):
    old = request["skill_name"]
    patterns = _token_patterns(old)
    dispositions = _valid_dispositions(ev, request["reference_dispositions"])
    ev.references = [dict(d) for d in dispositions.values()]

    base_files = _base_blobs(root, commit)
    base_occ, base_binary = scan_files(base_files, patterns)
    current = _read_worktree(root, listed)
    cand_occ, cand_binary = scan_files(current, patterns)
    untracked = untracked_files(root)
    for path in sorted(set(base_binary) | set(cand_binary)):
        ev.add("REFERENCE_BINARY_MATCH", path, f"{old} occurs in a non-text file; review it by hand")

    for (path, line, column), record in sorted(dispositions.items()):
        where = f"{path}:{line}:{column}"
        if path in base_files:
            found = base_occ.get(path)
            if found is None or (line, column) not in found[1]:
                ev.add("REFERENCE_DISPOSITION_INVALID", path,
                       f"{where} is not an old-name occurrence at base_ref")
            elif found[0] != record["before_sha256"]:
                ev.add("REFERENCE_DISPOSITION_INVALID", path,
                       f"{where} carries a stale before_sha256")
        else:
            found = cand_occ.get(path)
            if not (path in untracked and record["class"] == "historical-preserve"
                    and found is not None and (line, column) in found[1]
                    and found[0] == record["before_sha256"]):
                ev.add("REFERENCE_DISPOSITION_INVALID", path,
                       f"{where} is not part of the base_ref preimage")
    for path, (_sha, found) in sorted(base_occ.items()):
        unclassified = sorted(pos for pos in found if (path, *pos) not in dispositions)
        if unclassified:
            line, column = unclassified[0]
            ev.add("REFERENCE_DISPOSITION_INVALID", path,
                   f"{len(unclassified)} old-name occurrence(s) at base_ref have no "
                   f"disposition, first at {path}:{line}:{column}")
    for path, (sha, found) in sorted(cand_occ.items()):
        stale = sorted(pos for pos in found
                       if not (dispositions.get((path, *pos), {}).get("class")
                               == "historical-preserve"
                               and dispositions[(path, *pos)]["before_sha256"] == sha))
        if stale:
            line, column = stale[0]
            ev.add("STALE_OLD_NAME_REFERENCE", path,
                   f"{len(stale)} live old-name occurrence(s) of {old} remain, first at "
                   f"{path}:{line}:{column}")
    for (path, line, column), record in sorted(dispositions.items()):
        if record["class"] != "historical-preserve":
            continue
        data = current.get(path)
        if data is None and (root / path).is_file():
            data = (root / path).read_bytes()
        if data is None or _sha256(data) != record["before_sha256"]:
            ev.add("CATALOG_MUTATION_INCOMPLETE", path,
                   f"historical-preserve bytes changed at {path}:{line}:{column}")


def verify(ev: Evaluation, root: Path, request_file):
    request = _read_request(ev, request_file)
    for finding in source_findings(root):
        ev.findings.append(finding)
    if ev.findings:
        raise _RequestStop()
    catalog = Catalog(root)
    ev.required = catalog.required
    operation = request["operation"]
    _validate_identity(ev, operation, request["skill_name"], request["new_name"])
    commit = _validate_base_ref(ev, root, operation, request["base_ref"], required=True)
    _validate_metadata(ev, request, catalog)

    base = commit or "HEAD"
    changed = changed_paths(root, base)
    ev.changed = changed
    names = set(catalog.records) | set(catalog.tree)
    if commit is not None:
        base_manifest = _base_file(root, commit, MANIFEST_REL)
        try:
            names |= {r["name"] for r in _load_json_bytes(base_manifest)["skills"]}
        except (TypeError, ValueError, KeyError, AttributeError):
            pass  # Preimage below reports an unreadable base manifest
    ev.findings.extend(surface_findings(changed, names))
    ev.findings.extend(catalog.check(set(changed), lambda rel: _base_file(root, base, rel)))
    old, new = request["skill_name"], request["new_name"]

    if operation == "READ":
        if not catalog.present(old):
            ev.stop("SKILL_NOT_FOUND", None, f"{old} is not a catalog skill")
        for path in changed:
            if _touches(path, _target_paths(catalog, [old])):
                ev.add("TARGET_PATH_DIRTY", path, f"a READ must change no byte; {path} changed")
        return

    try:
        pre = Preimage(root, commit)
    except (ValueError, KeyError, TypeError) as exc:
        ev.stop("INVALID_BASE_REF", None, f"base_ref is not a readable catalog commit: {exc}")
    _check_existence(ev, operation, old, new, pre, catalog)
    listed = worktree_files(root)
    _check_native_and_resources(ev, request, pre, catalog, listed)
    if operation in ("CREATE", "UPDATE"):
        _check_created_record(ev, request, catalog)
    if operation in REFERENCE_OPERATIONS:
        _check_references(ev, root, request, commit, listed)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def render(result, fmt) -> bytes:
    if fmt == "json":
        text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        return text.encode("utf-8")
    lines = [
        f"verdict: {result['verdict']} (exit {result['exit_code']})",
        f"command: {result['command']}",
        f"operation: {result['operation']}",
        f"skill_name: {result['skill_name']}",
        f"new_name: {result['new_name']}",
        f"base_ref: {result['base_ref']}",
        f"required_providers: {', '.join(result['required_providers'])}",
    ]
    lines += [f"finding: {f['code']} {f['path'] or '-'}: {f['detail']}" for f in result["findings"]]
    lines += [f"reference: {r['path']}:{r['line']}:{r['column']} {r['before_sha256']} "
              f"{r['class'] or '-'} {r['rationale'] or '-'}" for r in result["references"]]
    lines += [f"changed: {p}" for p in result["changed_paths"]]
    return ("\n".join(lines) + "\n").encode("utf-8")


COMMANDS = ("inspect", "verify")


class _CommandLineError(Exception):
    """A command-line error for a known command whose caller asked for JSON."""


class _Parser(argparse.ArgumentParser):
    """argparse, except that under `--format json` a command-line error after a known
    command raises _CommandLineError so run() can answer in the v1 JSON shape. Any
    other error keeps argparse's usage text (exit 2): without a known command there is
    no `command` value the v1 shape could carry."""

    json_errors = False

    def error(self, message):
        if self.json_errors:
            raise _CommandLineError(message)
        super().error(message)


def _wants_json(argv) -> bool:
    """True when the command's own arguments ask for `--format json`."""
    for index, token in enumerate(argv):
        if token == "--format=json":
            return True
        if token == "--format" and argv[index + 1:index + 2] == ["json"]:
            return True
    return False


def build_parser(json_errors: bool = False):
    parser = _Parser(
        prog="skill_catalog.py",
        description="Read-only Skill Mesh catalog inspector and verifier. Never writes.")
    parser.json_errors = json_errors
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    insp = commands.add_parser("inspect", help="report the preimage a mutation starts from")
    insp.add_argument("--operation")
    insp.add_argument("--name")
    insp.add_argument("--new-name", default=None)
    insp.add_argument("--base-ref", default=None)
    insp.add_argument("--format", choices=("json", "text"), default="text")
    ver = commands.add_parser("verify", help="judge a candidate against its request")
    ver.add_argument("--request-file")
    ver.add_argument("--format", choices=("json", "text"), default="text")
    insp.json_errors = ver.json_errors = json_errors
    return parser


def evaluate(args, root: Path = REPO_ROOT):
    """Run one parsed command against `root` and return the result object."""
    ev = Evaluation(args.command)
    try:
        if args.command == "inspect":
            inspect(ev, root, args.operation, args.name, args.new_name, args.base_ref)
        else:
            verify(ev, root, args.request_file)
    except _RequestStop:
        pass
    except Exception as exc:  # the contract maps any unexpected failure to DRIFT
        ev.add("INTERNAL_ERROR", None, f"{type(exc).__name__}: {exc}")
    return ev.result()


def run(argv, root: Path = REPO_ROOT):
    """Parse `argv`, evaluate, and return (exit_code, output_bytes)."""
    argv = list(argv)
    json_errors = bool(argv) and argv[0] in COMMANDS and _wants_json(argv[1:])
    try:
        args = build_parser(json_errors).parse_args(argv)
    except _CommandLineError as exc:
        ev = Evaluation(argv[0])
        ev.add("INVALID_REQUEST_FILE", None, f"command line: {exc}")
        result = ev.result()
        return result["exit_code"], render(result, "json")
    result = evaluate(args, root)
    return result["exit_code"], render(result, args.format)


def main(argv=None) -> int:
    sys.dont_write_bytecode = True
    code, output = run(sys.argv[1:] if argv is None else argv)
    sys.stdout.flush()
    sys.stdout.buffer.write(output)
    sys.stdout.buffer.flush()
    return code


if __name__ == "__main__":
    sys.exit(main())
