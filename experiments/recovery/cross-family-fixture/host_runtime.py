"""Isolated host execution for the Goal A cross-family experiment.

This module is experiment-only. It starts exactly one native reviewer through the
candidate-bound Windows Job Object helper and compares protected live state before
and after that reviewer. It never selects a fallback model or a second host.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import stat
import subprocess
import sys
import time
from typing import Any, Mapping

from evidence import canonical_json_bytes, read_bounded, sha256_file, write_new


SNAPSHOT_DEADLINE_SECONDS = 600
SNAPSHOT_PARENT_TIMEOUT_SECONDS = 630
SNAPSHOT_MAX_RECORDS = 100_000
SNAPSHOT_EVIDENCE_MAX_BYTES = 64 * 1024 * 1024
REPARSE_DISCOVERY_SECONDS = 120
MAX_CREDENTIAL_BYTES = 16 * 1024 * 1024
JOB_BLOB = "187d26bcadd4a776b02410c0295792c025d05c70"
SNAPSHOT_BLOB = "2e56b34694a7bfb26d3c9ec8e07c3cb943e0488d"


class HostRuntimeError(RuntimeError):
    """Raised when reviewer execution cannot produce trustworthy evidence."""


def _run_git(repo: Path, *args: str, timeout: int = 30) -> bytes:
    git = shutil.which("git.exe") or shutil.which("git")
    if not git:
        raise HostRuntimeError("Git executable was not found")
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
        timeout=timeout,
        check=False,
    )
    if completed.returncode:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise HostRuntimeError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout


def validate_helpers(
    repo: Path,
    candidate_sha: str,
    source_root: Path | None = None,
) -> dict[str, Any]:
    source_root = source_root or repo
    paths = {
        "job": source_root / "experiments/recovery/lifecycle-probe/job_process.py",
        "snapshot": source_root / "experiments/recovery/lifecycle-probe/live_snapshot.py",
    }
    expected_blobs = {"job": JOB_BLOB, "snapshot": SNAPSHOT_BLOB}
    result: dict[str, Any] = {}
    for label, path in paths.items():
        relative = path.relative_to(source_root).as_posix()
        blob = _run_git(repo, "rev-parse", f"{candidate_sha}:{relative}").decode("ascii").strip()
        if blob != expected_blobs[label]:
            raise HostRuntimeError(f"{label} helper blob differs from the reviewed Step 74 helper")
        committed = _run_git(repo, "show", f"{candidate_sha}:{relative}")
        current = path.read_bytes()
        if current != committed:
            raise HostRuntimeError(f"{label} helper working bytes differ from candidate commit")
        result[label] = {
            "path": path,
            "blob": blob,
            "sha256": hashlib.sha256(current).hexdigest(),
        }
    return result


def _minimal_environment(disposable: Path, host: str) -> dict[str, str]:
    environment: dict[str, str] = {}
    for name in ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT"):
        if name in os.environ:
            environment[name] = os.environ[name]
    system_root = Path(environment.get("SystemRoot", r"C:\Windows"))
    home = disposable / "user"
    appdata = disposable / "appdata"
    local_appdata = disposable / "localappdata"
    temp = disposable / "temp"
    for path in (home, appdata, local_appdata, temp):
        path.mkdir(parents=True, exist_ok=True)
    environment.update(
        {
            "USERPROFILE": str(home),
            "HOME": str(home),
            "APPDATA": str(appdata),
            "LOCALAPPDATA": str(local_appdata),
            "TEMP": str(temp),
            "TMP": str(temp),
            "PATH": str(system_root / "System32"),
            "NO_COLOR": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    if host == "codex":
        codex_home = disposable / "codex-home"
        sqlite_home = disposable / "codex-sqlite"
        codex_home.mkdir()
        sqlite_home.mkdir()
        environment.update(
            {
                "CODEX_HOME": str(codex_home),
                "CODEX_SQLITE_HOME": str(sqlite_home),
            }
        )
    elif host == "claude":
        claude_home = disposable / "claude-home"
        claude_home.mkdir()
        environment.update(
            {
                "CLAUDE_CONFIG_DIR": str(claude_home),
                "CLAUDE_CODE_AUTO_CONNECT_IDE": "false",
                "CLAUDE_CODE_SKIP_PROMPT_HISTORY": "1",
                "CLAUDE_CODE_DISABLE_AGENT_VIEW": "1",
                "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
                "DISABLE_AUTOUPDATER": "1",
                "DISABLE_TELEMETRY": "1",
            }
        )
    else:
        raise HostRuntimeError(f"unknown reviewer host: {host}")
    return environment


def _regular_secret(path: Path) -> bytes:
    cursor = path
    while True:
        if cursor.exists():
            item_stat = os.lstat(cursor)
            if cursor.is_symlink() or bool(getattr(item_stat, "st_file_attributes", 0) & 0x400):
                raise HostRuntimeError("credential source crosses a reparse point")
        if cursor.parent == cursor:
            break
        cursor = cursor.parent
    if path.is_symlink() or not path.is_file():
        raise HostRuntimeError(f"credential source is not one regular file: {path.name}")
    before = path.stat()
    if before.st_size > MAX_CREDENTIAL_BYTES:
        raise HostRuntimeError("credential source exceeds the size bound")
    descriptor = os.open(path, os.O_RDONLY)
    try:
        opened_before = os.fstat(descriptor)
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            payload = stream.read(MAX_CREDENTIAL_BYTES + 1)
        opened_after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.stat()
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    opened_identity_before = (
        opened_before.st_dev,
        opened_before.st_ino,
        opened_before.st_size,
        opened_before.st_mtime_ns,
    )
    opened_identity_after = (
        opened_after.st_dev,
        opened_after.st_ino,
        opened_after.st_size,
        opened_after.st_mtime_ns,
    )
    if (
        identity_before != identity_after
        or identity_before != opened_identity_before
        or opened_identity_before != opened_identity_after
        or len(payload) != before.st_size
    ):
        raise HostRuntimeError("credential source changed while it was copied")
    return payload


def _copy_credential(
    host: str,
    live_claude_home: Path,
    live_codex_home: Path,
    disposable: Path,
) -> tuple[Path, bool]:
    if host == "codex":
        source = live_codex_home / "auth.json"
        destination = disposable / "codex-home" / "auth.json"
    else:
        source = live_claude_home / ".credentials.json"
        destination = disposable / "claude-home" / ".credentials.json"
    payload = _regular_secret(source)
    write_new(destination, payload)
    copied = destination.read_bytes()
    if not secrets.compare_digest(payload, copied):
        raise HostRuntimeError("credential copy does not match its source")
    return source, True


def _discover_reparse_targets(roots: list[Path]) -> list[Path]:
    pending = [root.resolve() for root in roots if root.exists()]
    visited: set[str] = set()
    targets: dict[str, Path] = {}
    records = 0
    deadline = time.monotonic() + REPARSE_DISCOVERY_SECONDS
    user_root = Path(os.environ.get("USERPROFILE", "")).resolve()
    while pending:
        current = pending.pop()
        canonical = os.path.normcase(str(current.resolve()))
        if canonical in visited:
            continue
        visited.add(canonical)
        try:
            entries = list(os.scandir(current))
        except OSError as error:
            raise HostRuntimeError(f"cannot inventory reparse targets below {current.name}") from error
        for entry in entries:
            if time.monotonic() > deadline:
                raise HostRuntimeError("reparse-target inventory exceeded its deadline")
            records += 1
            if records > SNAPSHOT_MAX_RECORDS:
                raise HostRuntimeError("reparse-target inventory exceeds the record bound")
            item_stat = entry.stat(follow_symlinks=False)
            if bool(getattr(item_stat, "st_file_attributes", 0) & 0x400):
                target = Path(os.path.realpath(entry.path)).resolve()
                if str(target).startswith("\\\\") or os.path.commonpath((str(target), str(user_root))) != str(user_root):
                    raise HostRuntimeError("live-home reparse target is not below the local user root")
                key = os.path.normcase(str(target))
                targets[key] = target
                if target.is_dir():
                    pending.append(target)
            elif stat.S_ISDIR(item_stat.st_mode):
                pending.append(Path(entry.path))
    return [targets[key] for key in sorted(targets)]


def _snapshot_request(
    live_claude_home: Path,
    live_codex_home: Path,
    secret_paths: list[Path],
    hmac_key: bytes,
    allowed_reparse_roots: list[Path],
) -> dict[str, Any]:
    agents_root = live_codex_home.parent / ".agents"
    return {
        "schema": 1,
        "roots": [
            {"label": "claude", "path": str(live_claude_home)},
            {"label": "codex", "path": str(live_codex_home)},
            {"label": "agents", "path": str(agents_root)},
        ],
        "secret_paths": [str(path) for path in secret_paths],
        "allowed_reparse_roots": [str(path) for path in allowed_reparse_roots],
        "hmac_key_hex": hmac_key.hex(),
        "deadline_seconds": SNAPSHOT_DEADLINE_SECONDS,
        "max_records": SNAPSHOT_MAX_RECORDS,
    }


def take_snapshot(
    helper: Path,
    request: Mapping[str, Any],
    destination: Path,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-B", str(helper)],
            input=canonical_json_bytes(dict(request)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=SNAPSHOT_PARENT_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise HostRuntimeError("protected live-state snapshot exceeded its parent timeout") from error
    if completed.returncode:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise HostRuntimeError(f"protected live-state snapshot failed: {detail}")
    try:
        payload = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise HostRuntimeError("protected live-state snapshot returned invalid JSON") from error
    if payload.get("schema") != 1 or payload.get("status") != "COMPLETE":
        raise HostRuntimeError("protected live-state snapshot is incomplete")
    records = payload.get("records")
    if not isinstance(records, list) or any(
        not isinstance(record, dict)
        or record.get("grew_during_read") is True
        or record.get("length") != record.get("final_length")
        for record in records
    ):
        raise HostRuntimeError("protected live-state snapshot changed while it was read")
    write_new(
        destination,
        canonical_json_bytes(payload),
        maximum=SNAPSHOT_EVIDENCE_MAX_BYTES,
    )
    return payload


def compare_snapshots(before: Mapping[str, Any], after: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    before_records = before.get("records")
    after_records = after.get("records")
    if not isinstance(before_records, list) or not isinstance(after_records, list):
        return "AMBIGUOUS", {"reason": "snapshot records are missing"}
    if before_records == after_records:
        return "MATCH", {"record_count": len(before_records), "changed_paths": []}
    indexed_before = {str(item.get("path")): item for item in before_records if isinstance(item, dict)}
    indexed_after = {str(item.get("path")): item for item in after_records if isinstance(item, dict)}
    changed = sorted(
        path
        for path in set(indexed_before) | set(indexed_after)
        if indexed_before.get(path) != indexed_after.get(path)
    )
    return "AMBIGUOUS", {
        "reason": "protected live state changed during the reviewer interval",
        "changed_path_count": len(changed),
        "changed_paths": changed[:100],
        "truncated": len(changed) > 100,
    }


def _resolve_executable(host: str) -> Path:
    if host == "codex":
        appdata = Path(os.environ.get("APPDATA", ""))
        package_root = appdata / "npm/node_modules/@openai/codex"
        candidates = sorted(package_root.glob("node_modules/@openai/codex-win32-*/vendor/*/bin/codex.exe"))
        if len(candidates) != 1:
            raise HostRuntimeError("installed npm Codex CLI did not resolve to exactly one native executable")
        path = candidates[0].resolve()
        name = "npm Codex CLI native executable"
    else:
        resolved = shutil.which("claude.exe")
        if not resolved:
            raise HostRuntimeError("claude.exe was not found")
        path = Path(resolved).resolve()
        name = "claude.exe"
    if not path.is_file() or path.is_symlink():
        raise HostRuntimeError(f"{name} did not resolve to one regular executable")
    return path


def _write_codex_config(disposable: Path) -> None:
    config = (
        'cli_auth_credentials_store = "file"\n'
        "check_for_update_on_startup = false\n"
        'model_reasoning_effort = "medium"\n'
    ).encode("utf-8")
    write_new(disposable / "codex-home" / "config.toml", config)


def _host_command(
    host: str,
    executable: Path,
    model: str,
    prompt: str,
    reviewer_cwd: Path,
    evidence_dir: Path,
    response_schema: Path,
) -> tuple[list[str], Path]:
    if host == "codex":
        response_path = evidence_dir / "review-response.json"
        argv = [
            "--strict-config",
            "--disable", "apps",
            "--disable", "image_generation",
            "--disable", "in_app_browser",
            "--disable", "multi_agent",
            "--disable", "plugins",
            "--disable", "plugin_sharing",
            "--disable", "remote_plugin",
            "--disable", "shell_snapshot",
            "--disable", "shell_tool",
            "--disable", "skill_mcp_dependency_install",
            "--disable", "skill_search",
            "--disable", "view_image",
            "-c", 'web_search="disabled"',
            "-c", "agents.enabled=false",
            "-c", "apps._default.enabled=false",
            "-c", 'cli_auth_credentials_store="file"',
            "-c", "check_for_update_on_startup=false",
            "-c", 'model_reasoning_effort="medium"',
            "--model", model,
            "--sandbox", "read-only",
            "--ask-for-approval", "never",
            "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--cd", str(reviewer_cwd),
            "--output-schema", str(response_schema),
            "--output-last-message", str(response_path),
            "--json",
            prompt,
        ]
        return argv, response_path
    try:
        claude_schema = json.loads(read_bounded(response_schema).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise HostRuntimeError("review response schema is not valid UTF-8 JSON") from error
    if not isinstance(claude_schema, dict):
        raise HostRuntimeError("review response schema is not one JSON object")
    claude_schema.pop("$schema", None)
    compact_schema = json.dumps(
        claude_schema,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    response_path = evidence_dir / "reviewer-stdout.txt"
    argv = [
        "-p", prompt,
        "--safe-mode",
        "--no-session-persistence",
        "--no-chrome",
        "--disable-slash-commands",
        "--permission-mode", "dontAsk",
        "--tools", "",
        "--disallowedTools", "*",
        "--model", model,
        "--effort", "medium",
        "--max-turns", "1",
        "--output-format", "json",
        "--json-schema", compact_schema,
    ]
    return argv, response_path


def _invoke_job(
    helper: Path,
    executable: Path,
    argv: list[str],
    cwd: Path,
    evidence_dir: Path,
    environment: Mapping[str, str],
    timeout_seconds: int,
) -> dict[str, Any]:
    stdout_path = evidence_dir / "reviewer-stdout.txt"
    stderr_path = evidence_dir / "reviewer-stderr.txt"
    request = {
        "schema": 1,
        "executable": str(executable),
        "argv": argv,
        "cwd": str(cwd),
        "timeout_ms": timeout_seconds * 1000,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
    }
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-B", str(helper)],
            input=canonical_json_bytes(request),
            env=dict(environment),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds + 30,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise HostRuntimeError("Job Object helper exceeded its parent timeout") from error
    try:
        result = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise HostRuntimeError("Job Object helper returned invalid containment JSON") from error
    required = {
        "schema",
        "status",
        "target_started",
        "assigned_before_resume",
        "root_pid",
        "root_exit_code",
        "timed_out",
        "survivors_existed",
        "survivor_pids",
        "terminate_job_called",
        "job_empty_confirmed",
        "duration_seconds",
        "stage",
        "win32_error",
    }
    if not isinstance(result, dict) or set(result) != required or result.get("schema") != 1:
        raise HostRuntimeError("Job Object helper result shape is invalid")
    for name in (
        "target_started",
        "assigned_before_resume",
        "timed_out",
        "survivors_existed",
        "terminate_job_called",
        "job_empty_confirmed",
    ):
        if type(result.get(name)) is not bool:
            raise HostRuntimeError(f"Job Object helper field is not Boolean: {name}")
    if result["target_started"] and not result["assigned_before_resume"]:
        raise HostRuntimeError("reviewer target started before containment was proved")
    write_new(evidence_dir / "containment.json", canonical_json_bytes(result))
    if not result.get("job_empty_confirmed"):
        raise HostRuntimeError("reviewer Job Object did not prove zero active processes")
    if completed.returncode not in (0, 2, 3):
        raise HostRuntimeError("Job Object helper returned an unknown exit code")
    return result


def _parse_claude(raw: bytes) -> tuple[bytes, dict[str, Any], str, str, str, Any, Any]:
    try:
        envelope = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise HostRuntimeError("Claude output is not one JSON envelope") from error
    response = envelope.get("structured_output")
    if not isinstance(response, dict):
        raise HostRuntimeError("Claude output lacks the required structured_output object")
    response_bytes = canonical_json_bytes(response)
    model_usage = envelope.get("modelUsage")
    if isinstance(model_usage, dict) and len(model_usage) == 1:
        model = next(iter(model_usage))
        resolved_status = "provider-reported"
        source = f"reviewer-stdout.txt::$['modelUsage']['{model}']"
    elif isinstance(model_usage, dict) and len(model_usage) > 1:
        model = "|".join(sorted(str(key) for key in model_usage))
        resolved_status = "unverified"
        source = "reviewer-stdout.txt::$['modelUsage'] (multiple entries)"
    else:
        model = ""
        resolved_status = "unavailable"
        source = "no allowlisted structured model field"
    return (
        response_bytes,
        envelope,
        model,
        resolved_status,
        source,
        envelope.get("usage", {"availability": "unavailable"}),
        envelope.get("total_cost_usd", {"availability": "unavailable"}),
    )


def _parse_codex(
    stdout: bytes,
    response_path: Path,
) -> tuple[bytes, list[Any], str, str, str, Any, Any]:
    events: list[Any] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line.decode("utf-8")))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise HostRuntimeError("Codex JSONL output contains an invalid event") from error
    response_bytes = read_bounded(response_path, 1024 * 1024)
    usage: Any = {"availability": "unavailable"}
    for event in events:
        if isinstance(event, dict) and isinstance(event.get("usage"), dict):
            usage = event["usage"]
    # Codex 0.147.0 does not document a reviewer-model field in JSONL.
    return (
        response_bytes,
        events,
        "",
        "unavailable",
        "no allowlisted structured model field",
        usage,
        {"availability": "unavailable"},
    )


def _create_disposable_root(fixture_root: Path) -> tuple[Path, Path]:
    disposable = fixture_root / "reviewer-runtime"
    try:
        disposable.mkdir(parents=False, exist_ok=False)
    except OSError as error:
        raise HostRuntimeError("reviewer runtime root already exists or cannot be created") from error
    disposable_stat = os.lstat(disposable)
    if disposable.is_symlink() or bool(
        getattr(disposable_stat, "st_file_attributes", 0) & 0x400
    ):
        raise HostRuntimeError("reviewer runtime root is a reparse point")
    reviewer_cwd = disposable / "empty-cwd"
    reviewer_cwd.mkdir(parents=False, exist_ok=False)
    return disposable, reviewer_cwd


def run_reviewer(
    *,
    repo: Path,
    candidate_sha: str,
    fixture_root: Path,
    evidence_dir: Path,
    live_claude_home: Path,
    live_codex_home: Path,
    direction: str,
    requested_model: str,
    prompt: str,
    response_schema: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    host = "codex" if direction == "claude-to-gpt" else "claude"
    source_root = Path(__file__).resolve().parents[3]
    helpers = validate_helpers(repo, candidate_sha, source_root)
    disposable, reviewer_cwd = _create_disposable_root(fixture_root)
    environment = _minimal_environment(disposable, host)
    executable = _resolve_executable(host)
    argv, response_path = _host_command(
        host,
        executable,
        requested_model,
        prompt,
        reviewer_cwd,
        evidence_dir,
        response_schema,
    )
    snapshot_key = secrets.token_bytes(32)
    reparse_targets = _discover_reparse_targets(
        [live_claude_home, live_codex_home, live_codex_home.parent / ".agents"]
    )
    write_new(
        evidence_dir / "reparse-targets.json",
        canonical_json_bytes(
            {
                "schema": 1,
                "targets": [str(path) for path in reparse_targets],
            }
        ),
    )
    snapshot_request = _snapshot_request(
        live_claude_home,
        live_codex_home,
        [live_claude_home / ".credentials.json", live_codex_home / "auth.json"],
        snapshot_key,
        reparse_targets,
    )
    before = take_snapshot(
        helpers["snapshot"]["path"], snapshot_request, evidence_dir / "live-before.json"
    )
    write_new(evidence_dir / "baseline-complete.json", canonical_json_bytes({"schema": 1, "complete": True}))
    credential_source, credential_copy_match = _copy_credential(
        host, live_claude_home, live_codex_home, disposable
    )
    write_new(
        evidence_dir / "credential-copy-complete.json",
        canonical_json_bytes({"schema": 1, "copied": True, "exact_in_memory_match": credential_copy_match}),
    )
    if host == "codex":
        _write_codex_config(disposable)
    started = time.monotonic()
    write_new(
        evidence_dir / "invocation-plan.json",
        canonical_json_bytes(
            {
                "schema": 1,
                "host": host,
                "executable": str(executable),
                "executable_sha256": sha256_file(executable),
                "argv": argv,
                "cwd": str(reviewer_cwd),
                "requested_model": requested_model,
                "fallback_allowed": False,
            }
        ),
    )
    write_new(evidence_dir / "review-starting.json", canonical_json_bytes({"schema": 1, "host": host}))
    invocation_error: Exception | None = None
    containment: dict[str, Any] | None = None
    try:
        containment = _invoke_job(
            helpers["job"]["path"],
            executable,
            argv,
            reviewer_cwd,
            evidence_dir,
            environment,
            timeout_seconds,
        )
    except Exception as error:  # The after snapshot remains mandatory after a possible start.
        invocation_error = error
    latency = round(time.monotonic() - started, 3)
    after_error: Exception | None = None
    after: dict[str, Any] | None = None
    try:
        after = take_snapshot(
            helpers["snapshot"]["path"], snapshot_request, evidence_dir / "live-after.json"
        )
    except Exception as error:
        after_error = error
    if invocation_error is not None or after_error is not None:
        details = []
        if invocation_error is not None:
            details.append(f"reviewer invocation: {type(invocation_error).__name__}: {invocation_error}")
        if after_error is not None:
            details.append(f"after snapshot: {type(after_error).__name__}: {after_error}")
        raise HostRuntimeError("; ".join(details))
    assert containment is not None and after is not None
    write_new(
        evidence_dir / "review-finished.json",
        canonical_json_bytes(
            {
                "schema": 1,
                "target_started": containment["target_started"],
                "job_empty_confirmed": containment["job_empty_confirmed"],
            }
        ),
    )
    live_status, live_detail = compare_snapshots(before, after)
    stdout = read_bounded(evidence_dir / "reviewer-stdout.txt")
    stderr = read_bounded(evidence_dir / "reviewer-stderr.txt")
    if host == "claude":
        response_bytes, envelope, resolved, resolved_status, resolved_source, usage, cost = _parse_claude(stdout)
        host_events: Any = envelope
    else:
        response_bytes, events, resolved, resolved_status, resolved_source, usage, cost = _parse_codex(
            stdout, response_path
        )
        host_events = events
    write_new(evidence_dir / "parsed-review.json", response_bytes)
    return {
        "host": host,
        "executable": executable,
        "executable_sha256": sha256_file(executable),
        "argv": argv,
        "reviewer_cwd": reviewer_cwd,
        "credential_source": credential_source,
        "credential_copy_match": credential_copy_match,
        "containment": containment,
        "host_started_count": 1 if containment.get("target_started") else 0,
        "latency_seconds": latency,
        "response_bytes": response_bytes,
        "host_events": host_events,
        "resolved_model": resolved,
        "resolved_status": resolved_status,
        "resolved_source": resolved_source,
        "token_usage": usage,
        "cost": cost,
        "live_state_status": live_status,
        "live_state_detail": live_detail,
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "job_helper_sha256": helpers["job"]["sha256"],
        "snapshot_helper_sha256": helpers["snapshot"]["sha256"],
    }
