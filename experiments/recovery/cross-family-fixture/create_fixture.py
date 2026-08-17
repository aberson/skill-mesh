"""Create the deterministic two-commit repository used by Goal A Step 76."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


FIXED_DATE = "2026-08-14T00:00:00Z"
TRACKED_PATHS = (".gitattributes", "README.md", "order_totals.py", "test_order_totals.py")
GIT_TIMEOUT_SECONDS = 30


def git_executable(requested: str | None = None) -> str:
    resolved = requested or shutil.which("git")
    if not resolved or not Path(resolved).is_absolute() or not Path(resolved).is_file():
        raise RuntimeError("git executable did not resolve to an absolute file")
    return str(Path(resolved).resolve())


def isolated_git_environment(target: Path) -> dict[str, str]:
    environment = {
        name: os.environ[name]
        for name in ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP")
        if name in os.environ
    }
    environment.update(
        {
            "GIT_AUTHOR_DATE": FIXED_DATE,
            "GIT_COMMITTER_DATE": FIXED_DATE,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "NUL",
            "GIT_CONFIG_SYSTEM": "NUL",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "HOME": str(target / ".git" / "isolated-home"),
            "XDG_CONFIG_HOME": str(target / ".git" / "isolated-xdg"),
            "LC_ALL": "C",
            "LANG": "C",
            "TZ": "UTC",
        }
    )
    return environment


def run_git(target: Path, *arguments: str, executable: str | None = None) -> str:
    environment = isolated_git_environment(target)
    completed = subprocess.run(
        [
            git_executable(executable),
            "-c",
            "core.autocrlf=false",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "init.templateDir=",
            "-c",
            "color.ui=false",
            *arguments,
        ],
        cwd=target,
        env=environment,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"git {' '.join(arguments)} failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def run_git_bytes(target: Path, *arguments: str, executable: str) -> bytes:
    completed = subprocess.run(
        [
            executable,
            "-c",
            "core.autocrlf=false",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "init.templateDir=",
            "-c",
            "color.ui=false",
            *arguments,
        ],
        cwd=target,
        env=isolated_git_environment(target),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )
    if completed.returncode:
        error = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(arguments)} failed: {error}")
    return completed.stdout


def tree_sha256(target: Path) -> str:
    digest = hashlib.sha256()
    for relative in TRACKED_PATHS:
        encoded = relative.encode("utf-8")
        payload = (target / relative).read_bytes()
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def create_fixture(target: Path, requested_git: str | None = None) -> dict[str, object]:
    if not target.is_absolute():
        raise ValueError("--target must be absolute")
    if target.exists():
        raise FileExistsError(f"target already exists: {target}")

    source_root = Path(__file__).resolve().parent
    base_root = source_root / "seed" / "base"
    candidate_source = source_root / "seed" / "candidate" / "order_totals.py"
    inventory = source_root / "expected-defects.json"
    for path in (*[base_root / item for item in TRACKED_PATHS], candidate_source, inventory):
        if not path.is_file():
            raise FileNotFoundError(path)

    target.mkdir(parents=True)
    for relative in TRACKED_PATHS:
        shutil.copyfile(base_root / relative, target / relative)

    resolved_git = git_executable(requested_git)
    run_git(target, "init", "--object-format=sha1", "-b", "main", executable=resolved_git)
    hooks = target / ".git" / "disabled-hooks"
    hooks.mkdir()
    run_git(target, "config", "core.hooksPath", str(hooks), executable=resolved_git)
    run_git(target, "config", "user.name", "Skill Mesh Fixture", executable=resolved_git)
    run_git(target, "config", "user.email", "skill-mesh-fixture@example.invalid", executable=resolved_git)
    run_git(target, "add", "--", *TRACKED_PATHS, executable=resolved_git)
    run_git(target, "commit", "--no-gpg-sign", "-m", "base: correct order total", executable=resolved_git)
    base_sha = run_git(target, "rev-parse", "HEAD", executable=resolved_git)

    candidate_payload = (
        candidate_source.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    )
    (target / "order_totals.py").write_bytes(candidate_payload)
    run_git(target, "add", "--", "order_totals.py", executable=resolved_git)
    run_git(target, "commit", "--no-gpg-sign", "-m", "candidate: simplify order total", executable=resolved_git)
    candidate_sha = run_git(target, "rev-parse", "HEAD", executable=resolved_git)
    status = run_git(target, "status", "--porcelain=v1", "--untracked-files=all", executable=resolved_git)
    if status:
        raise RuntimeError(f"fixture is not clean: {status}")

    diff = run_git_bytes(
        target,
        "diff",
        "--binary",
        "--no-ext-diff",
        "--full-index",
        "--src-prefix=a/",
        "--dst-prefix=b/",
        f"{base_sha}..{candidate_sha}",
        "--",
        executable=resolved_git,
    )
    diff_text = diff.decode("utf-8")
    result = {
        "schema_version": 1,
        "fixture_id": "skill-mesh-cross-family-order-total-v1",
        "base_sha": base_sha,
        "candidate_sha": candidate_sha,
        "candidate_tree_sha256": tree_sha256(target),
        "diff_sha256": hashlib.sha256(diff).hexdigest(),
        "diff_utf8": diff_text,
        "defect_inventory_sha256": hashlib.sha256(
            inventory.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        ).hexdigest(),
        "tracked_paths": list(TRACKED_PATHS),
        "public_test_command": ["python", "-m", "unittest", "-q"],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--git-executable")
    arguments = parser.parse_args()
    try:
        result = create_fixture(arguments.target, arguments.git_executable)
    except Exception as error:
        print(f"fixture creation failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
