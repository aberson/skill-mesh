"""Goal A Step 76/77 cross-family experiment probe.

The PowerShell wrapper sends one request on standard input. This script validates
the committed Step 76 candidate, owns disposable paths, seals one synthetic review
handoff, and optionally invokes one isolated reviewer through ``host_runtime``.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
from typing import Any, Mapping

import create_fixture
from evidence import (
    EvidenceError,
    canonical_json_bytes,
    json_display,
    read_bounded,
    redact_text,
    render_template,
    sha256_bytes,
    sha256_file,
    table_display,
    write_manifest,
    write_new,
)
import host_runtime
import review_contract


REQUEST_SCHEMA = "skill-mesh.cross-family.probe-request.v1"
RESULT_SCHEMA = "skill-mesh.cross-family.probe-result.v1"
OWNER_SCHEMA = "skill-mesh.cross-family.owner.v1"
GOAL_A_RE = re.compile(r"^goala-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")
RUN_RE = re.compile(
    r"^cross-(claude-to-gpt|gpt-to-claude)-"
    r"(manual-saved-handoff|reviewer-only-dispatcher)-"
    r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$"
)
ATTEMPT_RE = re.compile(r"^a[0-2](?:-r1)?$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
REPARSE_POINT = 0x400
MAX_REQUEST_BYTES = 64 * 1024
ALLOWED_PATHS = (
    "experiments/recovery/cross-family-fixture",
    "experiments/recovery/run-cross-family-probe.ps1",
    "tests/experiments/test_cross_family_probe.py",
    "documentation/experiments/cross-family-report-template.md",
    "documentation/experiments/cross-family-runbook.md",
)
RUNTIME_HELPER_PATHS = (
    "experiments/recovery/lifecycle-probe/job_process.py",
    "experiments/recovery/lifecycle-probe/live_snapshot.py",
)
CANDIDATE_BOOTSTRAP = (
    "import runpy,sys;from pathlib import Path;"
    "p=str(Path(sys.argv[1]).resolve());"
    "sys.path.insert(0,str(Path(p).parent));"
    "runpy.run_path(p,run_name='__main__')"
)
EXPECTED_REQUEST_KEYS = {
    "schema",
    "goal_a_id",
    "action",
    "direction",
    "mechanism",
    "fixture_root",
    "candidate_sha",
    "evidence_dir",
    "run_id",
    "attempt_id",
    "live_claude_home",
    "live_codex_home",
    "requested_reviewer_model",
    "credential_mode",
    "reviewer_timeout_seconds",
    "what_if",
}


class ProbeError(RuntimeError):
    """Raised when the bounded probe must stop."""


def _duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProbeError(f"request repeats key: {key}")
        result[key] = value
    return result


def load_request(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_REQUEST_BYTES:
        raise ProbeError("request exceeds the size bound")
    try:
        request = json.loads(raw.decode("utf-8"), object_pairs_hook=_duplicates)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ProbeError("request is not one UTF-8 JSON object") from error
    if not isinstance(request, dict) or set(request) != EXPECTED_REQUEST_KEYS:
        raise ProbeError("request keys do not match the reviewed wrapper contract")
    if request.get("schema") != REQUEST_SCHEMA:
        raise ProbeError("request schema is unsupported")
    for name in (
        "goal_a_id",
        "action",
        "direction",
        "mechanism",
        "fixture_root",
        "candidate_sha",
        "evidence_dir",
        "run_id",
        "attempt_id",
        "live_claude_home",
        "live_codex_home",
        "requested_reviewer_model",
        "credential_mode",
    ):
        if type(request[name]) is not str or not request[name]:
            raise ProbeError(f"{name} must be nonempty text")
    if type(request["what_if"]) is not bool:
        raise ProbeError("what_if must be a Boolean")
    if type(request["reviewer_timeout_seconds"]) is not int or not 1 <= request["reviewer_timeout_seconds"] <= 900:
        raise ProbeError("reviewer_timeout_seconds is outside 1..900")
    if not GOAL_A_RE.fullmatch(request["goal_a_id"]):
        raise ProbeError("goal_a_id has an invalid format")
    if not RUN_RE.fullmatch(request["run_id"]):
        raise ProbeError("run_id has an invalid format")
    if not ATTEMPT_RE.fullmatch(request["attempt_id"]):
        raise ProbeError("attempt_id has an invalid format")
    if not SHA1_RE.fullmatch(request["candidate_sha"]):
        raise ProbeError("candidate_sha must be one lowercase SHA-1 commit ID")
    if request["direction"] not in ("claude-to-gpt", "gpt-to-claude"):
        raise ProbeError("direction is unsupported")
    if request["mechanism"] not in ("manual-saved-handoff", "reviewer-only-dispatcher"):
        raise ProbeError("mechanism is unsupported")
    valid_action = (
        request["mechanism"] == "manual-saved-handoff"
        and request["action"] in ("Prepare", "InvokeSavedHandoff")
    ) or (
        request["mechanism"] == "reviewer-only-dispatcher"
        and request["action"] == "Run"
    )
    if not valid_action:
        raise ProbeError("action does not match the selected mechanism")
    expected_model = "gpt-5.6-terra" if request["direction"] == "claude-to-gpt" else "sonnet"
    if request["requested_reviewer_model"] != expected_model:
        raise ProbeError("requested reviewer model does not match the direction")
    if request["credential_mode"] != "copy-file":
        raise ProbeError("only copy-file credential isolation is supported")
    expected_prefix = f"cross-{request['direction']}-{request['mechanism']}-"
    if not request["run_id"].startswith(expected_prefix):
        raise ProbeError("run_id does not match direction and mechanism")
    return request


def _run_git(repo: Path, *args: str, allow: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[bytes]:
    git = shutil.which("git.exe") or shutil.which("git")
    if not git:
        raise ProbeError("Git executable was not found")
    environment = {
        name: os.environ[name]
        for name in ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP")
        if name in os.environ
    }
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "NUL",
            "GIT_CONFIG_SYSTEM": "NUL",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "HOME": str(repo / ".git" / "cross-family-read-home"),
        }
    )
    completed = subprocess.run(
        [str(Path(git).resolve()), "--no-optional-locks", *args],
        cwd=repo,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    if completed.returncode not in allow:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ProbeError(f"git {' '.join(args)} failed: {detail}")
    return completed


def repository_root() -> Path:
    explicit = os.environ.get("SKILL_MESH_CROSS_FAMILY_REPO_ROOT")
    expected = Path(explicit).resolve() if explicit else Path(__file__).resolve().parents[3]
    result = _run_git(expected, "rev-parse", "--show-toplevel").stdout.decode("utf-8").strip()
    resolved = Path(result).resolve()
    if resolved != expected:
        raise ProbeError("probe location and Git repository root disagree")
    return resolved


def candidate_source_root() -> Path:
    return Path(__file__).resolve().parents[3]


def candidate_runtime_root(request: Mapping[str, Any]) -> Path:
    temp = Path(os.environ.get("TEMP", ""))
    if not temp.is_absolute():
        raise ProbeError("TEMP is unavailable")
    return temp / "SkillMesh" / "CrossFamilyRuntime" / f"{request['run_id']}-{request['attempt_id']}"


def _remove_tree_exact(path: Path) -> None:
    """Remove one validated tree, clearing only read-only entries below it."""

    root = _canonical(path)
    if not path.is_dir() or path.is_symlink() or root != path.resolve():
        raise ProbeError("cleanup target is not one local directory")

    def retry_read_only(function: Any, name: str, error_info: tuple[Any, Any, Any]) -> None:
        target = Path(name)
        if not _same_or_child(target, root):
            raise ProbeError("cleanup callback escaped the approved root") from error_info[1]
        try:
            item_stat = os.lstat(target)
        except OSError:
            raise error_info[1]
        attributes = getattr(item_stat, "st_file_attributes", 0)
        read_only = getattr(stat, "FILE_ATTRIBUTE_READONLY", 1)
        if target.is_symlink() or bool(attributes & REPARSE_POINT):
            raise ProbeError("cleanup encountered a reparse point") from error_info[1]
        if not bool(attributes & read_only):
            raise error_info[1]
        os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
        function(name)

    shutil.rmtree(path, onerror=retry_read_only)
    if path.exists():
        raise ProbeError("cleanup target still exists")


def _materialize_candidate_runtime(
    request: Mapping[str, Any],
    repo: Path,
) -> Path:
    runtime_root = candidate_runtime_root(request)
    _reject_special_path(runtime_root, "candidate runtime root")
    if runtime_root.exists():
        raise ProbeError("candidate runtime root already exists")
    runtime_root.mkdir(parents=True, exist_ok=False)
    try:
        requested_paths = (*ALLOWED_PATHS, *RUNTIME_HELPER_PATHS)
        listing = _run_git(
            repo,
            "ls-tree",
            "-r",
            "--name-only",
            request["candidate_sha"],
            "--",
            *requested_paths,
        ).stdout.decode("utf-8").splitlines()
        if not listing:
            raise ProbeError("candidate runtime export is empty")
        for relative in listing:
            if not any(
                relative == allowed or relative.startswith(allowed.rstrip("/") + "/")
                for allowed in requested_paths
            ):
                raise ProbeError("candidate runtime export contains an unexpected path")
            destination = runtime_root / Path(relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            write_new(
                destination,
                _run_git(repo, "show", f"{request['candidate_sha']}:{relative}").stdout,
            )
        write_new(
            runtime_root / ".candidate-runtime-owner.json",
            canonical_json_bytes(
                {
                    "schema": 1,
                    "candidate_sha": request["candidate_sha"],
                    "paths": listing,
                }
            ),
        )
    except Exception:
        if runtime_root.is_dir() and not runtime_root.is_symlink():
            try:
                _remove_tree_exact(runtime_root)
            except Exception:
                pass
        raise
    return runtime_root


def _validate_materialized_runtime(
    request: Mapping[str, Any],
    repo: Path,
    source_root: Path,
) -> None:
    if source_root == repo:
        raise ProbeError("candidate-stage marker cannot be used from the mutable worktree")
    marker = json.loads(read_bounded(source_root / ".candidate-runtime-owner.json").decode("ascii"))
    if marker.get("schema") != 1 or marker.get("candidate_sha") != request["candidate_sha"]:
        raise ProbeError("candidate runtime owner marker is invalid")
    paths = marker.get("paths")
    if not isinstance(paths, list) or not paths or not all(isinstance(item, str) for item in paths):
        raise ProbeError("candidate runtime path inventory is invalid")
    actual_files = sorted(
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*")
        if path.is_file() and path.name != ".candidate-runtime-owner.json"
    )
    if actual_files != sorted(paths):
        raise ProbeError("candidate runtime file inventory differs from its owner marker")
    for relative in paths:
        if (source_root / relative).read_bytes() != _run_git(
            repo, "show", f"{request['candidate_sha']}:{relative}"
        ).stdout:
            raise ProbeError(f"materialized candidate byte mismatch: {relative}")


def reinvoke_candidate_runtime(
    raw_request: bytes,
    request: Mapping[str, Any],
    repo: Path,
) -> int | None:
    if request["what_if"]:
        return None
    if os.environ.get("SKILL_MESH_CROSS_FAMILY_CANDIDATE_STAGE") == "1":
        _validate_materialized_runtime(request, repo, candidate_source_root())
        return None
    runtime_root = _materialize_candidate_runtime(request, repo)
    probe_path = runtime_root / "experiments/recovery/cross-family-fixture/probe.py"
    environment = dict(os.environ)
    environment["SKILL_MESH_CROSS_FAMILY_CANDIDATE_STAGE"] = "1"
    environment["SKILL_MESH_CROSS_FAMILY_REPO_ROOT"] = str(repo)
    completed: subprocess.CompletedProcess[bytes] | None = None
    cleanup_error: Exception | None = None
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-B", "-c", CANDIDATE_BOOTSTRAP, str(probe_path)],
            input=raw_request,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=int(request["reviewer_timeout_seconds"]) + 1500,
            check=False,
        )
    finally:
        try:
            _remove_tree_exact(runtime_root)
        except Exception as error:
            cleanup_error = error
    if cleanup_error is not None:
        if completed is not None and completed.stderr:
            sys.stderr.buffer.write(completed.stderr)
            sys.stderr.buffer.flush()
        raise ProbeError(
            f"candidate runtime cleanup failed: {type(cleanup_error).__name__}: {cleanup_error}"
        ) from cleanup_error
    if completed is None:
        raise ProbeError("candidate runtime did not return a result")
    if completed.stderr:
        sys.stderr.buffer.write(completed.stderr)
        sys.stderr.buffer.flush()
    if completed.stdout:
        sys.stdout.buffer.write(completed.stdout)
        sys.stdout.buffer.flush()
    return completed.returncode


def _canonical(path: Path) -> Path:
    return Path(os.path.realpath(os.path.abspath(path)))


def _same_or_child(candidate: Path, root: Path) -> bool:
    candidate_text = os.path.normcase(str(_canonical(candidate)))
    root_text = os.path.normcase(str(_canonical(root)))
    try:
        return os.path.commonpath((candidate_text, root_text)) == root_text
    except ValueError:
        return False


def _overlap(left: Path, right: Path) -> bool:
    return _same_or_child(left, right) or _same_or_child(right, left)


def _reject_special_path(path: Path, label: str) -> None:
    text = str(path)
    if not path.is_absolute():
        raise ProbeError(f"{label} must be absolute")
    if text.startswith("\\\\") or text.startswith("\\?\\") or text.startswith("\\.\\"):
        raise ProbeError(f"{label} cannot be a UNC or device path")
    current = path
    ancestors: list[Path] = []
    while True:
        ancestors.append(current)
        if current.parent == current:
            break
        current = current.parent
    for ancestor in reversed(ancestors):
        if not ancestor.exists():
            continue
        item_stat = os.lstat(ancestor)
        if ancestor.is_symlink() or bool(getattr(item_stat, "st_file_attributes", 0) & REPARSE_POINT):
            raise ProbeError(f"{label} has an existing reparse-point ancestor")


def _worktree_roots(repo: Path) -> list[Path]:
    raw = _run_git(repo, "worktree", "list", "--porcelain").stdout.decode("utf-8")
    roots = [Path(line[9:]).resolve() for line in raw.splitlines() if line.startswith("worktree ")]
    if repo not in roots:
        raise ProbeError("Git worktree inventory does not include the current repository")
    return roots


def validate_paths(request: Mapping[str, Any], repo: Path) -> dict[str, Path]:
    fixture = Path(request["fixture_root"])
    evidence_dir = Path(request["evidence_dir"])
    live_claude = Path(request["live_claude_home"])
    live_codex = Path(request["live_codex_home"])
    runtime_root = candidate_runtime_root(request)
    for label, path in (
        ("fixture_root", fixture),
        ("evidence_dir", evidence_dir),
        ("live_claude_home", live_claude),
        ("live_codex_home", live_codex),
        ("candidate runtime root", runtime_root),
    ):
        _reject_special_path(path, label)
    if not live_claude.is_dir() or not live_codex.is_dir():
        raise ProbeError("both live-home locators must exist as directories")
    if _overlap(live_claude, live_codex):
        raise ProbeError("live-home locators overlap")
    userprofile = Path(os.environ.get("USERPROFILE", ""))
    if not userprofile.is_absolute():
        raise ProbeError("USERPROFILE is unavailable")
    if os.path.normcase(str(_canonical(live_claude))) != os.path.normcase(
        str(_canonical(userprofile / ".claude"))
    ):
        raise ProbeError("live_claude_home is not the current user's native Claude home")
    if os.path.normcase(str(_canonical(live_codex))) != os.path.normcase(
        str(_canonical(userprofile / ".codex"))
    ):
        raise ProbeError("live_codex_home is not the current user's native Codex home")
    if _overlap(fixture, evidence_dir) or _overlap(fixture, live_claude) or _overlap(fixture, live_codex):
        raise ProbeError("fixture path overlaps evidence or a live home")
    if _overlap(evidence_dir, live_claude) or _overlap(evidence_dir, live_codex):
        raise ProbeError("evidence path overlaps a live home")
    if any(
        _overlap(runtime_root, protected)
        for protected in (fixture, evidence_dir, live_claude, live_codex)
    ):
        raise ProbeError("candidate runtime root overlaps a protected path")
    for worktree in _worktree_roots(repo):
        if (
            _overlap(fixture, worktree)
            or _overlap(evidence_dir, worktree)
            or _overlap(runtime_root, worktree)
        ):
            raise ProbeError("fixture, evidence, or candidate runtime overlaps a Git worktree")
    local_appdata = Path(os.environ.get("LOCALAPPDATA", ""))
    if not local_appdata.is_absolute():
        raise ProbeError("LOCALAPPDATA is unavailable")
    goal_a_id = request["goal_a_id"]
    expected_fixture = local_appdata / "SkillMesh" / "Homes" / goal_a_id / f"{request['run_id']}-{request['attempt_id']}"
    expected_evidence = local_appdata / "SkillMesh" / "Evidence" / goal_a_id / "cross-family" / request["run_id"] / request["attempt_id"]
    if os.path.normcase(str(_canonical(fixture))) != os.path.normcase(str(_canonical(expected_fixture))):
        raise ProbeError("fixture_root does not match the reviewed run-specific locator")
    if os.path.normcase(str(_canonical(evidence_dir))) != os.path.normcase(str(_canonical(expected_evidence))):
        raise ProbeError("evidence_dir does not match the reviewed run-specific locator")
    return {
        "fixture": fixture,
        "evidence": evidence_dir,
        "live_claude": live_claude,
        "live_codex": live_codex,
    }


def validate_candidate(request: Mapping[str, Any], repo: Path) -> dict[str, Any]:
    candidate = request["candidate_sha"]
    _run_git(repo, "cat-file", "-e", f"{candidate}^{{commit}}")
    _run_git(repo, "merge-base", "--is-ancestor", candidate, "HEAD")
    plan = (repo / "plan.md").read_text(encoding="utf-8")
    goal_values = re.findall(r"(?m)^\*\*GoalAId:\*\* `([^`]+)`$", plan)
    if goal_values != [request["goal_a_id"]]:
        raise ProbeError("plan.md does not bind this GoalAId exactly once")
    section_match = re.search(
        r"(?ms)^### Step 76:.*?(?=^### Step 77:)",
        plan,
    )
    if not section_match:
        raise ProbeError("plan.md has no Step 76 journal section")
    candidate_values = re.findall(r"(?m)^\*\*Candidate commit:\*\* `([0-9a-f]{40})`$", section_match.group(0))
    if candidate_values != [candidate]:
        raise ProbeError("plan.md does not select exactly this Step 76 candidate")
    index = Path(os.environ["LOCALAPPDATA"]) / "SkillMesh" / "Evidence" / request["goal_a_id"] / "evidence-index.md"
    index_text = index.read_text(encoding="utf-8")
    matching_rows = [
        line
        for line in index_text.splitlines()
        if "`step76-candidate`" in line and candidate in line
    ]
    if len(matching_rows) != 1:
        raise ProbeError("external evidence index does not contain exactly one active Step 76 candidate row")
    dirty = _run_git(
        repo,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        *ALLOWED_PATHS,
    ).stdout.decode("utf-8")
    if dirty:
        raise ProbeError("Step 76 allowed paths contain mutable or untracked bytes")
    diff = _run_git(repo, "diff", "--exit-code", candidate, "--", *ALLOWED_PATHS, allow=(0, 1))
    if diff.returncode:
        raise ProbeError("current Step 76 bytes differ from the selected candidate")
    changed = _run_git(
        repo,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        f"{candidate}^",
        candidate,
    ).stdout.decode("utf-8").splitlines()
    if not changed:
        raise ProbeError("Step 76 candidate has no changed paths")
    for relative in changed:
        if not any(
            relative == allowed or relative.startswith(allowed.rstrip("/") + "/")
            for allowed in ALLOWED_PATHS
        ):
            raise ProbeError(f"Step 76 candidate changes a path outside its allowlist: {relative}")
    helpers = host_runtime.validate_helpers(repo, candidate)
    return {
        "candidate_sha": candidate,
        "job_helper_sha256": helpers["job"]["sha256"],
        "snapshot_helper_sha256": helpers["snapshot"]["sha256"],
    }


def _owner(request: Mapping[str, Any], kind: str) -> dict[str, Any]:
    return {
        "schema": OWNER_SCHEMA,
        "goal_a_id": request["goal_a_id"],
        "run_id": request["run_id"],
        "attempt_id": request["attempt_id"],
        "kind": kind,
    }


def _create_owned(path: Path, owner: Mapping[str, Any]) -> None:
    path.mkdir(parents=True, exist_ok=False)
    write_new(path / ".skill-mesh-owner.json", canonical_json_bytes(dict(owner)))


def _assert_owner(path: Path, owner: Mapping[str, Any]) -> None:
    if not path.is_dir() or path.is_symlink():
        raise ProbeError("owned path is missing or linked")
    actual = json.loads(read_bounded(path / ".skill-mesh-owner.json").decode("ascii"))
    if actual != dict(owner):
        raise ProbeError("owned path marker does not match the request")


def _load_sources(source_root: Path) -> dict[str, Path]:
    root = source_root / "experiments/recovery/cross-family-fixture"
    sources = {
        "requirements": root / "seed/base/README.md",
        "prompt": root / "review-prompt-template.md",
        "schema": root / "review-response.schema.json",
        "inventory": root / "expected-defects.json",
        "policy": root / "experiment-model-policy.json",
        "report": source_root / "documentation/experiments/cross-family-report-template.md",
    }
    for path in sources.values():
        if not path.is_file() or path.is_symlink():
            raise ProbeError(f"candidate source is missing or linked: {path.name}")
    return sources


def _render_prompt(template: str, values: Mapping[str, str]) -> str:
    expected = {"RUN_ID", "SEEDED_CANDIDATE_SHA", "PAYLOAD_SHA256", "REQUIREMENTS", "DIFF"}
    found = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", template))
    if found != expected:
        raise ProbeError("review prompt placeholder contract changed")
    rendered = template
    for key in expected:
        rendered = rendered.replace("{{" + key + "}}", values[key])
    if "{{" in rendered:
        raise ProbeError("review prompt contains an unresolved placeholder")
    return rendered


def _fixture_identity(fixture_repo: Path, git_executable: Path) -> dict[str, Any]:
    environment = create_fixture.isolated_git_environment(fixture_repo)
    status = subprocess.run(
        [
            str(git_executable),
            "-c", "core.autocrlf=false",
            "-c", "color.ui=false",
            "status", "--porcelain=v1", "--untracked-files=all",
        ],
        cwd=fixture_repo,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    head = subprocess.run(
        [str(git_executable), "-c", "core.autocrlf=false", "rev-parse", "HEAD"],
        cwd=fixture_repo,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if status.returncode or head.returncode or status.stdout:
        raise ProbeError("seeded candidate is not one clean immutable Git commit")
    return {
        "head": head.stdout.decode("ascii").strip(),
        "tree_sha256": create_fixture.tree_sha256(fixture_repo),
        "status": "clean",
    }


def prepare(
    request: Mapping[str, Any],
    repo: Path,
    paths: Mapping[str, Path],
) -> dict[str, Any]:
    fixture_root = paths["fixture"]
    evidence_dir = paths["evidence"]
    if fixture_root.exists() or evidence_dir.exists():
        raise ProbeError("Prepare and Run require absent fixture and evidence leaves")
    _create_owned(fixture_root, _owner(request, "fixture"))
    _create_owned(evidence_dir, _owner(request, "evidence"))
    fixture_repo = fixture_root / "seeded-repo"
    git_path_text = shutil.which("git.exe") or shutil.which("git")
    if not git_path_text:
        raise ProbeError("Git executable was not found")
    git_path = Path(git_path_text).resolve()
    fixture = create_fixture.create_fixture(fixture_repo, str(git_path))
    sources = _load_sources(candidate_source_root())
    requirements = sources["requirements"].read_text(encoding="utf-8")
    schema_bytes = sources["schema"].read_bytes()
    inventory_bytes = sources["inventory"].read_bytes()
    policy_bytes = sources["policy"].read_bytes()
    payload = {
        "schema_version": 1,
        "fixture_id": fixture["fixture_id"],
        "run_id": request["run_id"],
        "source_sha": fixture["candidate_sha"],
        "requirements_utf8": requirements,
        "diff_utf8": fixture["diff_utf8"],
        "response_schema_sha256": sha256_bytes(schema_bytes),
        "model_policy_sha256": sha256_bytes(policy_bytes),
    }
    payload_bytes = canonical_json_bytes(payload)
    payload_sha = sha256_bytes(payload_bytes)
    prompt = _render_prompt(
        sources["prompt"].read_text(encoding="utf-8"),
        {
            "RUN_ID": request["run_id"],
            "SEEDED_CANDIDATE_SHA": str(fixture["candidate_sha"]),
            "PAYLOAD_SHA256": payload_sha,
            "REQUIREMENTS": requirements.rstrip("\n"),
            "DIFF": str(fixture["diff_utf8"]).rstrip("\n"),
        },
    )
    prompt_bytes = prompt.encode("utf-8")
    artifacts = {
        "sealed-payload.json": payload_bytes,
        "review-request.md": prompt_bytes,
        "response-schema.json": schema_bytes,
        "defect-inventory.json": inventory_bytes,
        "model-policy.json": policy_bytes,
        "fixture.json": canonical_json_bytes({key: value for key, value in fixture.items() if key != "diff_utf8"}),
    }
    for name, content in artifacts.items():
        write_new(evidence_dir / name, content)
    artifact_hashes = {name: sha256_bytes(content) for name, content in artifacts.items()}
    receipt = {
        "schema": "skill-mesh.cross-family.prepare-receipt.v1",
        "goal_a_id": request["goal_a_id"],
        "run_id": request["run_id"],
        "attempt_id": request["attempt_id"],
        "direction": request["direction"],
        "mechanism": request["mechanism"],
        "step76_candidate_sha": request["candidate_sha"],
        "seeded_candidate_sha": fixture["candidate_sha"],
        "payload_sha256": payload_sha,
        "prompt_sha256": sha256_bytes(prompt_bytes),
        "response_schema_sha256": sha256_bytes(schema_bytes),
        "defect_inventory_sha256": sha256_bytes(inventory_bytes),
        "model_policy_sha256": sha256_bytes(policy_bytes),
        "fixture_json_sha256": artifact_hashes["fixture.json"],
        "fixture_root": str(_canonical(fixture_root)),
        "evidence_dir": str(_canonical(evidence_dir)),
        "live_claude_home": str(_canonical(paths["live_claude"])),
        "live_codex_home": str(_canonical(paths["live_codex"])),
        "credential_mode": request["credential_mode"],
        "reviewer_timeout_seconds": request["reviewer_timeout_seconds"],
        "requested_reviewer_model": request["requested_reviewer_model"],
        "fallback_allowed": False,
        "host_started": False,
    }
    write_new(evidence_dir / "prepare-receipt.json", canonical_json_bytes(receipt))
    prepare_paths = sorted(
        path
        for path in evidence_dir.iterdir()
        if path.is_file() and path.name != "prepare-manifest.sha256"
    )
    lines = [f"{sha256_file(path)}  {path.name}" for path in prepare_paths]
    write_new(evidence_dir / "prepare-manifest.sha256", ("\n".join(lines) + "\n").encode("utf-8"))
    return {"fixture": fixture, "receipt": receipt, "prompt": prompt}


def load_prepared(
    request: Mapping[str, Any],
    paths: Mapping[str, Path],
) -> dict[str, Any]:
    fixture_root = paths["fixture"]
    evidence_dir = paths["evidence"]
    _assert_owner(fixture_root, _owner(request, "fixture"))
    _assert_owner(evidence_dir, _owner(request, "evidence"))
    expected_fixture_entries = {".skill-mesh-owner.json", "seeded-repo"}
    actual_fixture_entries = {path.name for path in fixture_root.iterdir()}
    if actual_fixture_entries != expected_fixture_entries:
        raise ProbeError("prepared fixture contains an unexpected or missing entry")
    fixture_owner_path = fixture_root / ".skill-mesh-owner.json"
    seeded_repo = fixture_root / "seeded-repo"
    fixture_owner_stat = os.lstat(fixture_owner_path)
    seeded_repo_stat = os.lstat(seeded_repo)
    if (
        not fixture_owner_path.is_file()
        or fixture_owner_path.is_symlink()
        or bool(getattr(fixture_owner_stat, "st_file_attributes", 0) & REPARSE_POINT)
        or not seeded_repo.is_dir()
        or seeded_repo.is_symlink()
        or bool(getattr(seeded_repo_stat, "st_file_attributes", 0) & REPARSE_POINT)
    ):
        raise ProbeError("prepared fixture entries are not regular local objects")
    receipt = json.loads(read_bounded(evidence_dir / "prepare-receipt.json").decode("ascii"))
    expected = {
        "goal_a_id": request["goal_a_id"],
        "run_id": request["run_id"],
        "attempt_id": request["attempt_id"],
        "direction": request["direction"],
        "mechanism": request["mechanism"],
        "step76_candidate_sha": request["candidate_sha"],
        "requested_reviewer_model": request["requested_reviewer_model"],
        "fixture_root": str(_canonical(fixture_root)),
        "evidence_dir": str(_canonical(evidence_dir)),
        "live_claude_home": str(_canonical(paths["live_claude"])),
        "live_codex_home": str(_canonical(paths["live_codex"])),
        "credential_mode": request["credential_mode"],
        "reviewer_timeout_seconds": request["reviewer_timeout_seconds"],
        "fallback_allowed": False,
        "host_started": False,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ProbeError(f"prepared receipt differs at {key}")
    file_hashes = {
        "sealed-payload.json": receipt["payload_sha256"],
        "review-request.md": receipt["prompt_sha256"],
        "response-schema.json": receipt["response_schema_sha256"],
        "defect-inventory.json": receipt["defect_inventory_sha256"],
        "model-policy.json": receipt["model_policy_sha256"],
        "fixture.json": receipt["fixture_json_sha256"],
    }
    for name, expected_hash in file_hashes.items():
        if sha256_file(evidence_dir / name) != expected_hash:
            raise ProbeError(f"prepared artifact hash differs: {name}")
    expected_prepare_files = {
        ".skill-mesh-owner.json",
        "sealed-payload.json",
        "review-request.md",
        "response-schema.json",
        "defect-inventory.json",
        "model-policy.json",
        "fixture.json",
        "prepare-receipt.json",
    }
    expected_evidence_entries = expected_prepare_files | {"prepare-manifest.sha256"}
    actual_evidence_entries = {path.name for path in evidence_dir.iterdir()}
    if actual_evidence_entries != expected_evidence_entries:
        raise ProbeError("prepared evidence directory contains an unexpected or missing entry")
    for name in expected_evidence_entries:
        artifact = evidence_dir / name
        artifact_stat = os.lstat(artifact)
        if (
            not artifact.is_file()
            or artifact.is_symlink()
            or bool(getattr(artifact_stat, "st_file_attributes", 0) & REPARSE_POINT)
        ):
            raise ProbeError(f"prepared evidence entry is not one regular file: {name}")
    manifest_lines = read_bounded(evidence_dir / "prepare-manifest.sha256").decode("utf-8").splitlines()
    observed_manifest: dict[str, str] = {}
    for line in manifest_lines:
        if not re.fullmatch(r"[0-9a-f]{64}  [^\r\n]+", line):
            raise ProbeError("prepare manifest has an invalid line")
        digest, name = line.split("  ", 1)
        if name in observed_manifest:
            raise ProbeError("prepare manifest repeats a file")
        observed_manifest[name] = digest
    if set(observed_manifest) != expected_prepare_files:
        raise ProbeError("prepare manifest file set differs from the sealed handoff")
    for name, digest in observed_manifest.items():
        if sha256_file(evidence_dir / name) != digest:
            raise ProbeError(f"prepare manifest hash differs: {name}")
    fixture_data = json.loads(read_bounded(evidence_dir / "fixture.json").decode("ascii"))
    if fixture_data.get("candidate_sha") != receipt["seeded_candidate_sha"]:
        raise ProbeError("prepared fixture identity differs from its receipt")
    git_path_text = shutil.which("git.exe") or shutil.which("git")
    if not git_path_text:
        raise ProbeError("Git executable was not found while validating the sealed handoff")
    actual_identity = _fixture_identity(seeded_repo, Path(git_path_text).resolve())
    if (
        actual_identity["head"] != fixture_data.get("candidate_sha")
        or actual_identity["tree_sha256"] != fixture_data.get("candidate_tree_sha256")
    ):
        raise ProbeError("actual seeded repository differs from the sealed fixture identity")
    return {
        "receipt": receipt,
        "fixture": fixture_data,
        "prompt": read_bounded(evidence_dir / "review-request.md").decode("utf-8"),
    }


def _safe_cleanup(path: Path, owner: Mapping[str, Any]) -> tuple[str, str]:
    try:
        _assert_owner(path, owner)
        if path.is_symlink() or not path.is_dir():
            raise ProbeError("cleanup target is not one owned directory")
        _remove_tree_exact(path)
        return "PASS", "the exact owned disposable fixture was removed"
    except Exception as error:
        return "AMBIGUOUS", f"cleanup was refused or incomplete: {type(error).__name__}: {error}"


def _redactions(repo: Path, paths: Mapping[str, Path]) -> dict[str, str]:
    replacements = {
        str(paths["fixture"]): "<FIXTURE_ROOT>",
        str(paths["evidence"]): "<EVIDENCE_DIR>",
        str(paths["live_claude"]): "<LIVE_CLAUDE_HOME>",
        str(paths["live_codex"]): "<LIVE_CODEX_HOME>",
        str(repo): "<REPO_ROOT>",
    }
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        replacements[userprofile] = "<USERPROFILE>"
    return replacements


def _redact_structure(value: Any, replacements: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        return redact_text(value, replacements, maximum=8000)
    if isinstance(value, list):
        return [_redact_structure(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            redact_text(str(key), replacements, maximum=300): _redact_structure(item, replacements)
            for key, item in value.items()
        }
    return value


def _model_status_is_trustworthy(direction: str, requested: str, resolved: str, status: str) -> bool:
    if status not in ("verified", "provider-reported") or not resolved:
        return False
    lowered = resolved.casefold()
    if direction == "claude-to-gpt":
        return requested.casefold() in lowered or ("gpt-5.6" in lowered and "terra" in lowered)
    return "sonnet" in lowered


def _report_values(
    *,
    request: Mapping[str, Any],
    candidate: Mapping[str, Any],
    prepared: Mapping[str, Any],
    runtime: Mapping[str, Any],
    response: Mapping[str, Any],
    grade: Mapping[str, Any],
    result: str,
    failure_reason: str,
    before_identity: Mapping[str, Any],
    after_identity: Mapping[str, Any],
    cleanup_status: str,
    cleanup_detail: str,
    repo: Path,
    paths: Mapping[str, Path],
) -> dict[str, str]:
    replacements = _redactions(repo, paths)
    redact = lambda value, maximum=8000: redact_text(str(value), replacements, maximum=maximum)
    fixture = prepared["fixture"]
    receipt = prepared["receipt"]
    policy = json.loads(read_bounded(paths["evidence"] / "model-policy.json").decode("utf-8"))
    git_path_text = shutil.which("git.exe") or shutil.which("git")
    git_path = Path(git_path_text).resolve() if git_path_text else None
    git_version = "unavailable"
    git_hash = "unavailable"
    if git_path:
        completed = subprocess.run([str(git_path), "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, check=False)
        if completed.returncode == 0:
            git_version = completed.stdout.decode("utf-8", errors="replace").strip()
        git_hash = sha256_file(git_path)
    findings = response.get("findings", [])
    values = {
        "RESULT": result,
        "FAILURE_REASON": redact(failure_reason),
        "GOAL_A_ID": request["goal_a_id"],
        "RUN_ID": request["run_id"],
        "ATTEMPT_ID": request["attempt_id"],
        "DIRECTION": request["direction"],
        "MECHANISM": request["mechanism"],
        "SYNTHETIC_ORIGIN_STATUS": "synthetic-role-simulation",
        "REVIEWER_HOST": runtime["host"],
        "REVIEWER_ROLE": "independent code reviewer",
        "STEP76_CANDIDATE_SHA": request["candidate_sha"],
        "SEEDED_BASE_SHA": str(fixture["base_sha"]),
        "SEEDED_CANDIDATE_SHA": str(fixture["candidate_sha"]),
        "SEEDED_TREE_SHA256": str(fixture["candidate_tree_sha256"]),
        "SEEDED_DIFF_SHA256": str(fixture["diff_sha256"]),
        "PAYLOAD_SHA256": str(receipt["payload_sha256"]),
        "RESPONSE_SCHEMA_SHA256": str(receipt["response_schema_sha256"]),
        "DEFECT_INVENTORY_SHA256": str(receipt["defect_inventory_sha256"]),
        "MODEL_POLICY_SHA256": str(receipt["model_policy_sha256"]),
        "MODEL_POLICY_STATUS": str(policy["status"]),
        "REQUESTED_MODEL": request["requested_reviewer_model"],
        "REQUESTED_MODEL_KIND": "qualified-alias" if request["requested_reviewer_model"] == "sonnet" else "exact-pin",
        "RESOLVED_MODEL": redact(runtime["resolved_model"] or "unavailable", 1000),
        "RESOLVED_STATUS": runtime["resolved_status"],
        "RESOLVED_SOURCE": redact(runtime["resolved_source"]),
        "FALLBACK_ATTEMPTS": json_display(
            {"availability": "unavailable", "configured_allowed": False}
        ),
        "REVIEWER_EXECUTABLE": redact(runtime["executable"]),
        "REVIEWER_EXECUTABLE_SHA256": runtime["executable_sha256"],
        "REVIEWER_VERSION": "unavailable (not separately invoked)",
        "REVIEWER_CWD": redact(runtime["reviewer_cwd"]),
        "TOOL_POLICY": table_display("no tools"),
        "SANDBOX_POLICY": table_display("read-only/no-tool isolated reviewer"),
        "HOST_STARTED_COUNT": str(runtime["host_started_count"]),
        "ROOT_EXIT_CODE": str(runtime["containment"].get("root_exit_code", "unavailable")),
        "JOB_HELPER_SHA256": runtime["job_helper_sha256"],
        "SNAPSHOT_HELPER_SHA256": runtime["snapshot_helper_sha256"],
        "GIT_VERSION": redact(git_version),
        "GIT_EXECUTABLE_SHA256": git_hash,
        "REDACTED_ARGV": json_display([redact(item, 12_000) for item in runtime["argv"]]),
        "REVIEWER_VERDICT": str(response["verdict"]),
        "DETECTED_DEFECT_COUNT": str(grade["counts"]["detected_defect_count"]),
        "DETECTED_DEFECT_IDS": table_display(grade["detected_defect_ids"]),
        "REVIEWER_SUMMARY": redact(response["summary"]),
        "REVIEWER_FINDINGS": json_display(_redact_structure(findings, replacements)),
        "UNMATCHED_FINDINGS": json_display(
            _redact_structure(
                {
                    "findings": grade["unmatched_findings"],
                    "consistency_warnings": grade["consistency_warnings"],
                },
                replacements,
            )
        ),
        "LATENCY_SECONDS": str(runtime["latency_seconds"]),
        "TOKEN_USAGE": table_display(runtime["token_usage"]),
        "COST": table_display(runtime["cost"]),
        "INPUT_TRANSFER": table_display({"kind": "sealed positional argument", "fallback": False}),
        "PROMPT_SHA256": str(receipt["prompt_sha256"]),
        "RESPONSE_SHA256": sha256_bytes(runtime["response_bytes"]),
        "RAW_STDOUT_SHA256": runtime["stdout_sha256"],
        "RAW_STDERR_SHA256": runtime["stderr_sha256"],
        "CANDIDATE_BEFORE_IDENTITY": sha256_bytes(canonical_json_bytes(dict(before_identity))),
        "CANDIDATE_AFTER_IDENTITY": sha256_bytes(canonical_json_bytes(dict(after_identity))),
        "CANDIDATE_IDENTITY_STATUS": "MATCH" if before_identity == after_identity else "AMBIGUOUS",
        "LIVE_STATE_STATUS": runtime["live_state_status"],
        "LIVE_STATE_DETAIL": table_display(runtime["live_state_detail"]),
        "CLEANUP_STATUS": cleanup_status,
        "CLEANUP_DETAIL": table_display(cleanup_detail),
        "UNRESOLVED_PREMISES": json_display([
            "The origin role is synthetic; direction does not prove an origin model.",
            "Quality evidence from one seeded candidate does not qualify a model pair.",
            "A protected live-state delta prevents attribution and architecture approval.",
        ]),
    }
    return {key: str(value) for key, value in values.items()}


def execute_review(
    request: Mapping[str, Any],
    candidate: Mapping[str, Any],
    prepared: Mapping[str, Any],
    repo: Path,
    paths: Mapping[str, Path],
) -> dict[str, Any]:
    fixture_repo = paths["fixture"] / "seeded-repo"
    git_path_text = shutil.which("git.exe") or shutil.which("git")
    if not git_path_text:
        raise ProbeError("Git executable disappeared before reviewer execution")
    git_path = Path(git_path_text).resolve()
    before_identity = _fixture_identity(fixture_repo, git_path)
    write_new(paths["evidence"] / "candidate-before.json", canonical_json_bytes(before_identity))
    runtime = host_runtime.run_reviewer(
        repo=repo,
        candidate_sha=request["candidate_sha"],
        fixture_root=paths["fixture"],
        evidence_dir=paths["evidence"],
        live_claude_home=paths["live_claude"],
        live_codex_home=paths["live_codex"],
        direction=request["direction"],
        requested_model=request["requested_reviewer_model"],
        prompt=prepared["prompt"],
        response_schema=paths["evidence"] / "response-schema.json",
        timeout_seconds=request["reviewer_timeout_seconds"],
    )
    after_identity = _fixture_identity(fixture_repo, git_path)
    write_new(paths["evidence"] / "candidate-after.json", canonical_json_bytes(after_identity))
    try:
        response = review_contract.load_json_strict(runtime["response_bytes"])
        review_contract.validate_response(
            response,
            request["run_id"],
            prepared["receipt"]["seeded_candidate_sha"],
            prepared["receipt"]["payload_sha256"],
        )
    except review_contract.ReviewContractError as error:
        raise ProbeError(f"review response failed the exact contract: {error}") from error
    inventory = json.loads(read_bounded(paths["evidence"] / "defect-inventory.json").decode("utf-8"))
    grade = review_contract.grade_response(response, inventory)
    trustworthy_identity = _model_status_is_trustworthy(
        request["direction"],
        request["requested_reviewer_model"],
        runtime["resolved_model"],
        runtime["resolved_status"],
    )
    reasons: list[str] = []
    result = "PASS"
    if runtime["live_state_status"] != "MATCH":
        reasons.append("protected live state changed or could not be compared")
    if before_identity != after_identity:
        reasons.append("seeded candidate identity changed")
    containment = runtime["containment"]
    if not containment.get("job_empty_confirmed") or containment.get("timed_out") or containment.get("survivors_existed"):
        reasons.append("reviewer process containment is incomplete")
    if not trustworthy_identity:
        reasons.append("reviewer model identity is unavailable, unverified, or mismatched")
    if reasons:
        result = "AMBIGUOUS"
    elif containment.get("root_exit_code") != 0:
        result = "FAIL"
        reasons.append("reviewer host returned a nonzero exit code")
    elif grade["counts"]["detected_defect_count"] == 0:
        result = "FAIL"
        reasons.append("reviewer detected none of the seeded defects")
    elif (
        grade["counts"]["detected_defect_count"] < 3
        or grade["counts"]["unmatched_finding_count"] > 0
        or bool(grade["consistency_warnings"])
    ):
        result = "PARTIAL"
        reasons.append("mechanism worked but review quality was incomplete or added unmatched findings")
    else:
        reasons.append("all required experiment observations have trustworthy evidence")
    cleanup_status, cleanup_detail = _safe_cleanup(paths["fixture"], _owner(request, "fixture"))
    if cleanup_status != "PASS":
        result = "AMBIGUOUS"
        reasons.append("disposable cleanup could not be proved")
    values = _report_values(
        request=request,
        candidate=candidate,
        prepared=prepared,
        runtime=runtime,
        response=response,
        grade=grade,
        result=result,
        failure_reason="; ".join(reasons),
        before_identity=before_identity,
        after_identity=after_identity,
        cleanup_status=cleanup_status,
        cleanup_detail=cleanup_detail,
        repo=repo,
        paths=paths,
    )
    template = (candidate_source_root() / "documentation/experiments/cross-family-report-template.md").read_text(encoding="utf-8")
    report = render_template(template, values)
    write_new(paths["evidence"] / "report.md", report.encode("utf-8"))
    write_manifest(paths["evidence"], paths["evidence"] / "MANIFEST.sha256")
    return {
        "experiment_result": result,
        "report": str(paths["evidence"] / "report.md"),
        "manifest": str(paths["evidence"] / "MANIFEST.sha256"),
        "host_started": runtime["host_started_count"] == 1,
        "resolved_status": runtime["resolved_status"],
        "detected_defect_count": grade["counts"]["detected_defect_count"],
    }


def publish_ambiguous_failure(
    *,
    request: Mapping[str, Any],
    candidate: Mapping[str, Any],
    prepared: Mapping[str, Any],
    error: Exception,
    repo: Path,
    paths: Mapping[str, Path],
) -> dict[str, Any]:
    """Publish a Section 6 result when the attempt cannot reach normal reduction."""

    evidence_dir = paths["evidence"]
    replacements = _redactions(repo, paths)
    template = (candidate_source_root() / "documentation/experiments/cross-family-report-template.md").read_text(encoding="utf-8")
    tokens = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", template))
    values = {token: "unavailable" for token in tokens}
    receipt = prepared["receipt"]
    fixture = prepared["fixture"]
    host = "codex" if request["direction"] == "claude-to-gpt" else "claude"
    containment: dict[str, Any] = {}
    containment_path = evidence_dir / "containment.json"
    if containment_path.is_file():
        try:
            containment = json.loads(read_bounded(containment_path).decode("ascii"))
        except Exception:
            containment = {}
    review_starting = (evidence_dir / "review-starting.json").exists()
    invocation: dict[str, Any] = {}
    invocation_path = evidence_dir / "invocation-plan.json"
    if invocation_path.is_file():
        try:
            candidate_invocation = json.loads(read_bounded(invocation_path).decode("ascii"))
            if (
                candidate_invocation.get("schema") == 1
                and candidate_invocation.get("host") == host
                and isinstance(candidate_invocation.get("executable"), str)
                and isinstance(candidate_invocation.get("executable_sha256"), str)
                and isinstance(candidate_invocation.get("cwd"), str)
                and isinstance(candidate_invocation.get("argv"), list)
                and all(isinstance(item, str) for item in candidate_invocation["argv"])
            ):
                invocation = candidate_invocation
        except Exception:
            invocation = {}
    cleanup_allowed = not review_starting or containment.get("job_empty_confirmed") is True
    if cleanup_allowed:
        cleanup_status, cleanup_detail = _safe_cleanup(paths["fixture"], _owner(request, "fixture"))
    else:
        cleanup_status = "AMBIGUOUS"
        cleanup_detail = "cleanup was refused because zero active reviewer processes was not proved"
    live_detail: dict[str, Any] = {"reason": "one or both protected-state snapshots are unavailable"}
    live_status = "AMBIGUOUS"
    before_path = evidence_dir / "live-before.json"
    after_path = evidence_dir / "live-after.json"
    if before_path.is_file() and after_path.is_file():
        try:
            before = json.loads(read_bounded(before_path).decode("ascii"))
            after = json.loads(read_bounded(after_path).decode("ascii"))
            live_status, live_detail = host_runtime.compare_snapshots(before, after)
        except Exception as snapshot_error:
            live_detail = {"reason": f"snapshot comparison failed: {type(snapshot_error).__name__}"}
    def file_hash(name: str) -> str:
        path = evidence_dir / name
        return sha256_file(path) if path.is_file() else "unavailable"
    if containment.get("target_started") is True:
        host_started_count = "1"
    elif containment.get("target_started") is False or not review_starting:
        host_started_count = "0"
    else:
        host_started_count = "unavailable"
    invocation_argv = invocation.get("argv", [])
    values.update(
        {
            "RESULT": "AMBIGUOUS",
            "FAILURE_REASON": redact_text(
                f"{type(error).__name__}: {error}", replacements, maximum=4000
            ),
            "GOAL_A_ID": request["goal_a_id"],
            "RUN_ID": request["run_id"],
            "ATTEMPT_ID": request["attempt_id"],
            "DIRECTION": request["direction"],
            "MECHANISM": request["mechanism"],
            "SYNTHETIC_ORIGIN_STATUS": "synthetic-role-simulation",
            "REVIEWER_HOST": host,
            "REVIEWER_ROLE": "independent code reviewer",
            "STEP76_CANDIDATE_SHA": request["candidate_sha"],
            "SEEDED_BASE_SHA": str(fixture.get("base_sha", "unavailable")),
            "SEEDED_CANDIDATE_SHA": str(fixture.get("candidate_sha", "unavailable")),
            "SEEDED_TREE_SHA256": str(fixture.get("candidate_tree_sha256", "unavailable")),
            "SEEDED_DIFF_SHA256": str(fixture.get("diff_sha256", "unavailable")),
            "PAYLOAD_SHA256": str(receipt.get("payload_sha256", "unavailable")),
            "RESPONSE_SCHEMA_SHA256": str(receipt.get("response_schema_sha256", "unavailable")),
            "DEFECT_INVENTORY_SHA256": str(receipt.get("defect_inventory_sha256", "unavailable")),
            "MODEL_POLICY_SHA256": str(receipt.get("model_policy_sha256", "unavailable")),
            "MODEL_POLICY_STATUS": "candidate-unqualified",
            "REQUESTED_MODEL": request["requested_reviewer_model"],
            "REQUESTED_MODEL_KIND": "qualified-alias" if request["requested_reviewer_model"] == "sonnet" else "exact-pin",
            "RESOLVED_MODEL": "unavailable",
            "RESOLVED_STATUS": "unavailable",
            "RESOLVED_SOURCE": "normal host-envelope parsing did not complete",
            "FALLBACK_ATTEMPTS": json_display(
                {"availability": "unavailable", "configured_allowed": False}
            ),
            "REVIEWER_EXECUTABLE": redact_text(
                str(invocation.get("executable", "unavailable")), replacements, maximum=4000
            ),
            "REVIEWER_EXECUTABLE_SHA256": str(
                invocation.get("executable_sha256", "unavailable")
            ),
            "REVIEWER_VERSION": "unavailable",
            "REVIEWER_CWD": redact_text(
                str(invocation.get("cwd", "unavailable")), replacements, maximum=4000
            ),
            "TOOL_POLICY": table_display("no tools"),
            "SANDBOX_POLICY": table_display("read-only/no-tool isolated reviewer"),
            "HOST_STARTED_COUNT": host_started_count,
            "ROOT_EXIT_CODE": str(containment.get("root_exit_code", "unavailable")),
            "JOB_HELPER_SHA256": str(candidate.get("job_helper_sha256", "unavailable")),
            "SNAPSHOT_HELPER_SHA256": str(candidate.get("snapshot_helper_sha256", "unavailable")),
            "GIT_VERSION": "unavailable",
            "GIT_EXECUTABLE_SHA256": "unavailable",
            "REDACTED_ARGV": json_display(
                [redact_text(item, replacements, maximum=12_000) for item in invocation_argv]
            ),
            "REVIEWER_VERDICT": "UNCERTAIN",
            "DETECTED_DEFECT_COUNT": "0",
            "DETECTED_DEFECT_IDS": "[]",
            "REVIEWER_SUMMARY": "The attempt did not produce a trustworthy parsed reviewer result.",
            "REVIEWER_FINDINGS": "[]",
            "UNMATCHED_FINDINGS": "[]",
            "LATENCY_SECONDS": str(containment.get("duration_seconds", "unavailable")),
            "TOKEN_USAGE": table_display({"availability": "unavailable"}),
            "COST": table_display({"availability": "unavailable"}),
            "INPUT_TRANSFER": table_display({"kind": "sealed positional argument", "completion": "unverified"}),
            "PROMPT_SHA256": str(receipt.get("prompt_sha256", "unavailable")),
            "RESPONSE_SHA256": file_hash("parsed-review.json"),
            "RAW_STDOUT_SHA256": file_hash("reviewer-stdout.txt"),
            "RAW_STDERR_SHA256": file_hash("reviewer-stderr.txt"),
            "CANDIDATE_BEFORE_IDENTITY": "unavailable",
            "CANDIDATE_AFTER_IDENTITY": "unavailable",
            "CANDIDATE_IDENTITY_STATUS": "AMBIGUOUS",
            "LIVE_STATE_STATUS": live_status,
            "LIVE_STATE_DETAIL": table_display(live_detail),
            "CLEANUP_STATUS": cleanup_status,
            "CLEANUP_DETAIL": table_display(cleanup_detail),
            "UNRESOLVED_PREMISES": json_display(
                [
                    "The failed attempt does not identify a viable architecture.",
                    "The origin role remains synthetic.",
                    "Reviewer model identity was not proved.",
                ]
            ),
        }
    )
    report_path = evidence_dir / "report.md"
    manifest_path = evidence_dir / "MANIFEST.sha256"
    if report_path.exists() or manifest_path.exists():
        raise ProbeError("ambiguous publication collided with an existing final artifact")
    write_new(report_path, render_template(template, values).encode("utf-8"))
    write_manifest(evidence_dir, manifest_path)
    target_started = containment.get("target_started")
    return {
        "experiment_result": "AMBIGUOUS",
        "report": str(report_path),
        "manifest": str(manifest_path),
        "host_started": target_started if type(target_started) is bool else None,
        "resolved_status": "unavailable",
        "detected_defect_count": 0,
    }


def what_if_plan(
    request: Mapping[str, Any],
    paths: Mapping[str, Path],
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    action = request["action"]
    if action in ("Prepare", "Run"):
        if paths["fixture"].exists() or paths["evidence"].exists():
            raise ProbeError("planned create-new fixture or evidence leaf already exists")
    else:
        load_prepared(request, paths)
    runtime_root = candidate_runtime_root(request)
    _reject_special_path(runtime_root, "candidate runtime root")
    if runtime_root.exists():
        raise ProbeError("candidate runtime root already exists")
    host = "codex" if request["direction"] == "claude-to-gpt" else "claude"
    prepare_targets = [
        candidate_runtime_root(request),
        paths["fixture"],
        paths["fixture"] / ".skill-mesh-owner.json",
        paths["fixture"] / "seeded-repo",
        paths["evidence"],
        paths["evidence"] / ".skill-mesh-owner.json",
        paths["evidence"] / "sealed-payload.json",
        paths["evidence"] / "review-request.md",
        paths["evidence"] / "response-schema.json",
        paths["evidence"] / "defect-inventory.json",
        paths["evidence"] / "model-policy.json",
        paths["evidence"] / "fixture.json",
        paths["evidence"] / "prepare-receipt.json",
        paths["evidence"] / "prepare-manifest.sha256",
    ]
    runtime_targets = [
        candidate_runtime_root(request),
        paths["fixture"] / "reviewer-runtime",
        paths["fixture"] / "reviewer-runtime" / "empty-cwd",
        paths["fixture"] / "reviewer-runtime" / ("codex-home" if host == "codex" else "claude-home"),
        paths["evidence"] / "reparse-targets.json",
        paths["evidence"] / "live-before.json",
        paths["evidence"] / "reviewer-stdout.txt",
        paths["evidence"] / "reviewer-stderr.txt",
        paths["evidence"] / "containment.json",
        paths["evidence"] / "baseline-complete.json",
        paths["evidence"] / "credential-copy-complete.json",
        paths["evidence"] / "invocation-plan.json",
        paths["evidence"] / "review-starting.json",
        paths["evidence"] / "review-finished.json",
        paths["evidence"] / "candidate-before.json",
        paths["evidence"] / "candidate-after.json",
        paths["evidence"] / "review-response.json" if host == "codex" else paths["evidence"] / "reviewer-stdout.txt",
        paths["evidence"] / "live-after.json",
        paths["evidence"] / "parsed-review.json",
        paths["evidence"] / "report.md",
        paths["evidence"] / "MANIFEST.sha256",
        paths["evidence"] / "fallback-report.txt",
    ]
    if host == "codex":
        runtime_targets.extend(
            [
                paths["fixture"] / "reviewer-runtime" / "codex-home" / "auth.json",
                paths["fixture"] / "reviewer-runtime" / "codex-home" / "config.toml",
                paths["fixture"] / "reviewer-runtime" / "codex-sqlite",
            ]
        )
        credential_source = paths["live_codex"] / "auth.json"
    else:
        runtime_targets.append(paths["fixture"] / "reviewer-runtime" / "claude-home" / ".credentials.json")
        credential_source = paths["live_claude"] / ".credentials.json"
    write_targets = prepare_targets if action == "Prepare" else runtime_targets
    if action == "Run":
        write_targets = [*prepare_targets, *runtime_targets]
    return {
        "schema": RESULT_SCHEMA,
        "status": "WHAT_IF",
        "action": action,
        "direction": request["direction"],
        "mechanism": request["mechanism"],
        "requested_reviewer_model": request["requested_reviewer_model"],
        "reviewer_host": host,
        "host_start_count": 0 if action == "Prepare" else 1,
        "write_targets": list(dict.fromkeys(str(path) for path in write_targets)),
        "read_targets": [
            *([] if action == "Prepare" else [str(credential_source)]),
            str(paths["live_claude"]),
            str(paths["live_codex"]),
            str(paths["live_codex"].parent / ".agents"),
        ],
        "delete_targets": [
            str(candidate_runtime_root(request)),
            *([] if action == "Prepare" else [str(paths["fixture"])]),
        ],
        "command_sequence": (
            (["create deterministic two-commit seeded repository", "seal payload and prepare receipt"] if action in ("Prepare", "Run") else [])
            + ([] if action == "Prepare" else [
                "inventory exact local reparse targets",
                "take candidate-bound protected-state baseline",
                "copy exactly one reviewer credential into the disposable home",
                f"start exactly one native {host} reviewer in a kill-on-close Job Object",
                "take candidate-bound protected-state after snapshot",
                "strictly parse, grade, redact, and publish the report",
                "remove only the exact owned disposable fixture",
            ])
        ),
        "candidate_helpers": {
            "job_sha256": candidate["job_helper_sha256"],
            "snapshot_sha256": candidate["snapshot_helper_sha256"],
        },
        "reviewer_policy": {
            "requested_model": request["requested_reviewer_model"],
            "reasoning_effort": "medium",
            "tools": "none",
            "sandbox": "read-only/no-tool",
            "credential_source": str(credential_source),
        },
        "snapshot_policy": {
            "before": 1,
            "after": 1,
            "any_delta": "AMBIGUOUS",
            "deadline_seconds": host_runtime.SNAPSHOT_DEADLINE_SECONDS,
            "parent_timeout_seconds": host_runtime.SNAPSHOT_PARENT_TIMEOUT_SECONDS,
            "max_records": host_runtime.SNAPSHOT_MAX_RECORDS,
            "reparse_inventory_deadline_seconds": host_runtime.REPARSE_DISCOVERY_SECONDS,
        },
        "fallback_allowed": False,
    }


def _emit(value: Mapping[str, Any]) -> None:
    sys.stdout.buffer.write(canonical_json_bytes(dict(value)))


def main() -> int:
    request: dict[str, Any] | None = None
    paths: dict[str, Path] | None = None
    evidence_owned = False
    repo: Path | None = None
    candidate: dict[str, Any] | None = None
    prepared: dict[str, Any] | None = None
    try:
        raw_request = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        request = load_request(raw_request)
        repo = repository_root()
        paths = validate_paths(request, repo)
        candidate = validate_candidate(request, repo)
        candidate_exit = reinvoke_candidate_runtime(raw_request, request, repo)
        if candidate_exit is not None:
            return candidate_exit
        if request["what_if"]:
            _emit(what_if_plan(request, paths, candidate))
            return 0
        if request["action"] in ("Prepare", "Run"):
            prepared = prepare(request, repo, paths)
            evidence_owned = True
        else:
            prepared = load_prepared(request, paths)
            evidence_owned = True
        if request["action"] == "Prepare":
            _emit(
                {
                    "schema": RESULT_SCHEMA,
                    "status": "PREPARED",
                    "experiment_result": None,
                    "run_id": request["run_id"],
                    "host_started": False,
                    "payload_sha256": prepared["receipt"]["payload_sha256"],
                    "receipt": str(paths["evidence"] / "prepare-receipt.json"),
                    "prepare_manifest": str(paths["evidence"] / "prepare-manifest.sha256"),
                }
            )
            return 0
        completed = execute_review(request, candidate, prepared, repo, paths)
        _emit(
            {
                "schema": RESULT_SCHEMA,
                "status": "COMPLETE",
                "run_id": request["run_id"],
                **completed,
            }
        )
        return 0
    except (Exception, KeyboardInterrupt) as error:  # Preserve bounded evidence for interruption or failure.
        if request is not None and request.get("what_if") is True:
            _emit(
                {
                    "schema": RESULT_SCHEMA,
                    "status": "REJECTED",
                    "error": f"{type(error).__name__}: {error}",
                }
            )
            return 2
        if paths is not None and paths["evidence"].is_dir():
            try:
                _assert_owner(paths["evidence"], _owner(request or {}, "evidence"))
                evidence_owned = True
            except Exception:
                evidence_owned = False
        if (
            evidence_owned
            and paths is not None
            and paths["evidence"].is_dir()
            and request is not None
            and prepared is not None
            and candidate is not None
            and repo is not None
            and request.get("action") != "Prepare"
        ):
            try:
                completed = publish_ambiguous_failure(
                    request=request,
                    candidate=candidate,
                    prepared=prepared,
                    error=error,
                    repo=repo,
                    paths=paths,
                )
                _emit(
                    {
                        "schema": RESULT_SCHEMA,
                        "status": "COMPLETE",
                        "run_id": request["run_id"],
                        **completed,
                    }
                )
                return 0
            except Exception:
                pass
        if evidence_owned and paths is not None and paths["evidence"].is_dir():
            fallback = paths["evidence"] / "fallback-report.txt"
            try:
                if not fallback.exists():
                    write_new(
                        fallback,
                        f"INCOMPLETE\n{type(error).__name__}: {error}\n".encode("utf-8", errors="replace"),
                    )
                manifest = paths["evidence"] / "MANIFEST.sha256"
                if not manifest.exists():
                    write_manifest(paths["evidence"], manifest)
            except Exception:
                pass
            _emit(
                {
                    "schema": RESULT_SCHEMA,
                    "status": "INCOMPLETE",
                    "run_id": request.get("run_id") if request else None,
                    "error": f"{type(error).__name__}: {error}",
                    "fallback_report": str(fallback),
                }
            )
            return 3
        _emit(
            {
                "schema": RESULT_SCHEMA,
                "status": "REJECTED",
                "error": f"{type(error).__name__}: {error}",
            }
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
