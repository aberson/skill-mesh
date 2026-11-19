"""Pinned companion call contracts (core companion plan Step 11).

Network cases install public tags in a disposable, tag-keyed tool cache under
the system temp directory (override with SKILL_MESH_CONTRACT_CACHE). They never
use a companion from the operator's PATH or write to the operator's stores.
Cache hits reuse the installed tag snapshot; they do not re-resolve mutable tags.
Use a new SKILL_MESH_CONTRACT_CACHE directory to validate a fresh installation.
The receipt records the resolved commit, not an independently pinned commit.
SKILL_MESH_CONTRACTS_OFFLINE=1 skips those cases before any network/tool call,
even when a cache exists. A failed connectivity probe also reports ``offline``;
missing pins, failed installs and broken contracts fail, rather than skip.

Run with pytest -rs to expose skip reasons. Local fixture cases below exercise
the same health/payload checks without invoking uv, git, or the network.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "config/companions.json"
CONTRACT_NAMES = {
    "find-again": "find-again-search-json",
    "passing-notes": "passing-notes-lane-text",
    "tripwire": "tripwire-check-json",
    "drift-ranger": "drift-ranger-store",
}


def members():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["members"]


def contract_members():
    """A candidate's non-null pin is a promise too, and must be exercised."""
    return [row for row in members()
            if row["ring"] in ("core", "optional") or row["tag"] is not None]


def require_online():
    if os.environ.get("SKILL_MESH_CONTRACTS_OFFLINE") == "1":
        pytest.skip("offline")
    try:
        with urllib.request.urlopen("https://github.com", timeout=10):
            pass
    except urllib.error.HTTPError as exc:
        pytest.fail(f"connectivity probe returned HTTP {exc.code}; not an offline pass")
    except (urllib.error.URLError, TimeoutError, OSError):
        pytest.skip("offline")


def isolated_env(home):
    home.mkdir(parents=True, exist_ok=True)
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT"}
    env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    scratch = home / "tmp"
    scratch.mkdir(exist_ok=True)
    env.update({
        "TEMP": str(scratch), "TMP": str(scratch), "TMPDIR": str(scratch),
        "HOME": str(home), "USERPROFILE": str(home),
        "LOCALAPPDATA": str(home / "local"), "APPDATA": str(home / "roaming"),
        "XDG_CONFIG_HOME": str(home / "config"), "XDG_DATA_HOME": str(home / "data"),
        "XDG_CACHE_HOME": str(home / "cache"), "XDG_STATE_HOME": str(home / "state"),
        "PASSING_NOTES_ROOT": str(home / "notes"),
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": str(home / "gitconfig"),
        "GIT_TERMINAL_PROMPT": "0", "PYTHONIOENCODING": "utf-8",
        "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
        "UV_NO_CONFIG": "1", "UV_PYTHON_DOWNLOADS": "never",
    })
    return env


def run(argv, *, cwd, env, allowed=(0,), timeout=30, input=None):
    try:
        proc = subprocess.run(
            [str(p) for p in argv], cwd=cwd, env=env, input=input,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        pytest.fail(f"command unavailable: {argv[0]}: {exc}")
    assert proc.returncode in allowed, (
        f"command failed ({proc.returncode}): {argv}\n{proc.stdout}\n{proc.stderr}"
    )
    return proc.stdout


def assert_schema(payload, row):
    assert isinstance(payload, dict), "payload must be an object"
    actual = payload.get("schema_version")
    expected = row["contract"]["schema_version"]
    assert type(actual) is int and actual == expected, (
        f"schema_version: expected {expected}, got {actual!r}"
    )


def call(argv, commands, workspace, env, **kwargs):
    # Resolve only the explicitly installed command, never an unrelated PATH tool.
    assert argv and argv[0] in commands, f"health/call command not installed: {argv}"
    return run([*commands[argv[0]], *argv[1:]], cwd=workspace, env=env, **kwargs)


def check_health(row, commands, workspace, env):
    return call(row["health"], commands, workspace, env)


def check_member_callers(row, source):
    for caller in row["callers"]:
        if caller.startswith("member:"):
            path = (source / caller.removeprefix("member:")).resolve()
            assert path.is_relative_to(source.resolve()), f"escaping caller: {caller}"
            assert path.is_file(), f"missing caller at {row['tag']}: {caller}"


def installed_tag(row, cache):
    assert row["tag"], f"{row['slug']}: missing pinned tag"
    identity = {"repo": row["repo"], "tag": row["tag"], "python": sys.executable,
                "version": sys.version, "cache_version": 1}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
    folder = cache / key
    folder.mkdir(parents=True, exist_ok=True)
    receipt = folder / "installed.json"
    if receipt.exists():
        saved = json.loads(receipt.read_text(encoding="utf-8"))
        assert saved["identity"] == identity, "cache identity mismatch"
        attempt = folder / saved["attempt"]
        assert attempt.resolve().is_relative_to(folder.resolve()), "escaping cache receipt"
    else:
        # Failed attempts have no receipt and cannot become a cached success. Keep
        # their logs/tree for diagnosis; a retry gets another disposable directory.
        attempt = Path(tempfile.mkdtemp(prefix="install-", dir=folder))
        env = isolated_env(attempt / "home")
        env.update({"UV_TOOL_DIR": str(attempt / "tools"),
                    "UV_TOOL_BIN_DIR": str(attempt / "bin")})
        git, uv = shutil.which("git"), shutil.which("uv")
        assert git and uv, "online contracts require git and uv"
        run([git, "clone", "--depth", "1", "--branch", row["tag"], "--",
             row["repo"], attempt / "source"], cwd=attempt, env=env, timeout=180)
        # Resolve the exact tag, not a branch of the same name.
        tag_commit = run([git, "rev-parse", f"refs/tags/{row['tag']}^{{commit}}"],
                         cwd=attempt / "source", env=env).strip()
        head = run([git, "rev-parse", "HEAD"], cwd=attempt / "source", env=env).strip()
        assert head == tag_commit, "checkout does not match pinned tag"
        run([uv, "tool", "install", "--python", sys.executable, attempt / "source"],
            cwd=attempt, env=env, timeout=180)
        exe = attempt / "bin" / (row["cli"] + (".exe" if os.name == "nt" else ""))
        assert exe.is_file(), f"installed tag has no {row['cli']} command"
        # Publish atomically only after successful installation. Parallel runs
        # may create independent attempts; either complete receipt is usable.
        pending = attempt / "receipt.json"
        pending.write_text(json.dumps({"identity": identity, "attempt": attempt.name,
                                       "commit": head}), encoding="utf-8")
        pending.replace(receipt)
    executable = attempt / "bin" / (row["cli"] + (".exe" if os.name == "nt" else ""))
    assert executable.is_file(), f"cached command missing: {executable}"
    assert (attempt / "source").is_dir(), "cached source missing"
    return {row["cli"]: [str(executable)]}, attempt / "source"


def check_payload(row, commands, workspace, env):
    cli, slug = row["cli"], row["slug"]

    def invoke(argv, **kwargs):
        return call([cli, *argv], commands, workspace, env, **kwargs)

    assert row["contract"]["name"] == CONTRACT_NAMES[slug], "unknown contract name"
    if slug == "tripwire":
        # The read-only check requires a git root. Its findings may legitimately
        # use exit 1 or 2; argparse errors still fail JSON/shape validation.
        payload = json.loads(invoke(["check", "--root", str(workspace), "--json"],
                                    allowed=(0, 1, 2)))
        assert_schema(payload, row)
        assert isinstance(payload["target"], str)
        assert isinstance(payload["findings"], list)
        for finding in payload["findings"]:
            assert all(isinstance(finding[k], str) for k in
                       ("rule_id", "severity", "message", "observed", "provenance", "evaluator"))
    elif slug == "find-again":
        (workspace / "find-again.toml").write_text(
            'schema_version = 1\nroots = ["docs"]\n', encoding="utf-8")
        (workspace / "docs").mkdir()
        (workspace / "docs" / "note.md").write_text("companion_contract_marker\n", encoding="utf-8")
        invoke(["--root", str(workspace), "index"])
        payload = json.loads(invoke(["--root", str(workspace), "--json", "search",
                                    "companion_contract_marker", "--type", "markdown", "--limit", "5"]))
        assert_schema(payload, row)
        assert payload["query"] == "companion_contract_marker"
        assert payload["count"] == len(payload["results"]) == 1
        result = payload["results"][0]
        assert result["type"] == "markdown"
        assert all(isinstance(result[k], str) for k in ("doc_id", "excerpt", "locator"))
        assert "docs/note.md" in result["locator"]
        assert "companion_contract_marker" in result["excerpt"]
    elif slug == "passing-notes":
        # Text protocol v1 has no invented JSON payload or --json switch.
        assert row["contract"]["schema_version"] == 1, "schema_version: lane-text requires v1"
        project = ["--project", "contract-fixture"]
        invoke(["card", "set", *project, "--lane", "reader", "--host", "codex",
                "--item", "contract fixture", "--state", "idle"])
        cards = invoke(["card", "show", *project])
        assert "diagnostics: 0" in cards.splitlines()
        fields = next(line.split("\t") for line in cards.splitlines() if line.startswith("reader\t"))
        assert fields[:4] == ["reader", "codex", "idle", "contract fixture"]
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fields[4])
        note = invoke(["post", *project, "--from", "writer", "--to", "reader",
                       "--kind", "fyi", "--needs", "ack", "--subject", "contract fixture",
                       "--body-stdin"], input="Synthetic contract body.\n").strip()
        inbox = invoke(["inbox", *project, "--lane", "reader"])
        assert "diagnostics: 0" in inbox.splitlines()
        assert [note, "fyi", "ack", "writer", "contract fixture"] in [
            line.split("\t") for line in inbox.splitlines()]
        settings = Path(env["HOME"]) / ".claude" / "settings.json"
        invoke(["hook", "install", "--settings", str(settings)])
        before = settings.read_bytes()
        invoke(["hook", "install", "--settings", str(settings), "--check"])
        assert settings.read_bytes() == before, "hook --check must be read-only"
    elif slug == "drift-ranger":
        store = Path(env["HOME"]) / "drift"
        invoke(["init", "contract-fixture", "--store", str(store), "--intent", "Fixture outcome",
                "--entry-point", "Fixture CLI", "--next-gap", "Verify contract"])
        invoke(["checkpoint", "contract-fixture", "--store", str(store), "--unit", "first",
                "--can", "Read fixture", "--cannot", "Claim live acceptance",
                "--next-gap", "Verify contract", "--progress", "unchanged"])
        for name in ("intent.json", "events/first.json"):
            payload = json.loads((store / "contract-fixture" / name).read_text(encoding="utf-8"))
            assert_schema(payload, row)
            assert payload["project_id"] == "contract-fixture"
        assert "Fixture outcome" in invoke(["show", "contract-fixture", "--store", str(store)])


@pytest.fixture(scope="session")
def online():
    require_online()


def check_all_contracts(row, commands, source, workspace, env):
    checks = (
        ("health", lambda: check_health(row, commands, workspace, env)),
        ("member callers", lambda: check_member_callers(row, source)),
        ("payload", lambda: check_payload(row, commands, workspace, env)),
    )
    failures = []
    for label, check in checks:
        try:
            check()
        except (Exception, pytest.fail.Exception) as exc:
            failures.append(f"{label}: {type(exc).__name__}: {exc}")
    assert not failures, "member contract failures:\n" + "\n".join(failures)


@pytest.mark.parametrize("row", contract_members(), ids=lambda r: r["slug"])
def test_pinned_member_contract(row, online, tmp_path):
    assert row["slug"] in CONTRACT_NAMES, f"add a contract case for {row['slug']} before promotion"
    cache = Path(os.environ.get("SKILL_MESH_CONTRACT_CACHE",
                                str(Path(tempfile.gettempdir()) / "skill-mesh-companion-contracts")))
    commands, source = installed_tag(row, cache)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    env = isolated_env(tmp_path / "home")
    run(["git", "init", "--quiet", str(workspace)], cwd=tmp_path, env=env)
    check_all_contracts(row, commands, source, workspace, env)


def test_manifest_contract_fields():
    for row in contract_members():
        assert row["tag"], f"{row['slug']}: missing pinned tag"
        assert row["contract"]["name"] == CONTRACT_NAMES[row["slug"]]
        assert type(row["contract"]["schema_version"]) is int
        assert row["contract"]["schema_version"] >= 1


def test_pinned_candidate_is_in_contract_selection(monkeypatch):
    drift = copy.deepcopy(next(row for row in members() if row["slug"] == "drift-ranger"))
    drift.update(ring="candidate", tag="v1.2.3")
    unpinned = dict(drift, slug="unpinned-fixture", tag=None)
    monkeypatch.setattr(sys.modules[__name__], "members", lambda: [drift, unpinned])
    assert contract_members() == [drift]


def test_isolated_child_receives_only_allowlisted_environment(tmp_path, monkeypatch):
    private_keys = ("GH_TOKEN", "ANTHROPIC_API_KEY", "AWS_SECRET_ACCESS_KEY",
                    "UNEXPECTED_TEST_TOKEN", "CODEX_THREAD_ID")
    for key in private_keys:
        monkeypatch.setenv(key, "synthetic-private-value")
    home = tmp_path / "home"
    env = isolated_env(home)
    received = json.loads(run(
        [sys.executable, "-c", "import json, os; print(json.dumps(dict(os.environ)))"],
        cwd=tmp_path, env=env,
    ))
    assert not set(private_keys).intersection(received)
    assert received["HOME"] == received["USERPROFILE"] == str(home)
    assert received["PASSING_NOTES_ROOT"] == str(home / "notes")
    assert received["TEMP"] == str(home / "tmp")
    assert "PATH" in received


def test_offline_skips_before_network_or_install(monkeypatch):
    monkeypatch.setenv("SKILL_MESH_CONTRACTS_OFFLINE", "1")
    def forbidden(*args, **kwargs):
        pytest.fail("offline mode attempted external work")
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    with pytest.raises(pytest.skip.Exception, match="^offline$"):
        require_online()


def test_unreachable_network_skips(monkeypatch):
    monkeypatch.delenv("SKILL_MESH_CONTRACTS_OFFLINE", raising=False)
    def unavailable(*args, **kwargs):
        raise urllib.error.URLError("offline fixture")
    monkeypatch.setattr(urllib.request, "urlopen", unavailable)
    with pytest.raises(pytest.skip.Exception, match="^offline$"):
        require_online()


def test_http_failure_is_not_mislabeled_offline(monkeypatch):
    monkeypatch.delenv("SKILL_MESH_CONTRACTS_OFFLINE", raising=False)
    def rejected(*args, **kwargs):
        raise urllib.error.HTTPError("https://github.com", 403, "fixture", {}, None)
    monkeypatch.setattr(urllib.request, "urlopen", rejected)
    with pytest.raises(pytest.fail.Exception, match="HTTP 403"):
        require_online()


@pytest.fixture
def local_tool(tmp_path):
    script = tmp_path / "fixture_tool.py"
    script.write_text(
        "import json, sys\n"
        "if sys.argv[1:] == ['--version']:\n"
        "    print('fixture 1.0.0')\n"
        "elif sys.argv[1:] == ['--help']:\n"
        "    print('usage: fixture check --root ROOT --json')\n"
        "elif sys.argv[1:2] == ['check']:\n"
        "    print(json.dumps({'schema_version': 1, 'target': 'fixture', 'findings': []}))\n"
        "else:\n"
        "    sys.exit(2)\n", encoding="utf-8")
    row = copy.deepcopy(next(r for r in members() if r["slug"] == "tripwire"))
    return row, {row["cli"]: [sys.executable, str(script)]}, tmp_path, isolated_env(tmp_path / "home")


def test_local_fixture_accepts_contract(local_tool):
    check_health(*local_tool)
    check_payload(*local_tool)


def test_wrong_schema_version_fails_local_fixture(local_tool):
    row, commands, workspace, env = local_tool
    row["contract"]["schema_version"] = 999
    with pytest.raises(AssertionError, match="schema_version"):
        check_payload(row, commands, workspace, env)


def test_all_member_failures_are_reported(local_tool):
    row, commands, workspace, env = local_tool
    row["health"] = ["tripwire", "missing-health-verb"]
    row["contract"]["schema_version"] = 999
    row["callers"] = ["member:missing-hook.ps1"]
    with pytest.raises(AssertionError) as failure:
        check_all_contracts(row, commands, workspace, workspace, env)
    message = str(failure.value)
    assert "health: AssertionError: command failed" in message
    assert "member callers: AssertionError: missing caller" in message
    assert "payload: AssertionError: schema_version" in message


@pytest.mark.parametrize("argv", [["tripwire", "missing-health-verb"], ["missing-command", "--version"]])
def test_missing_health_fails_local_fixture(local_tool, argv):
    row, commands, workspace, env = local_tool
    row["health"] = argv
    with pytest.raises(AssertionError, match="command"):
        check_health(row, commands, workspace, env)


def test_missing_member_caller_fails(tmp_path):
    row = {"tag": "v1.0.0", "callers": ["member:hooks/check.ps1"]}
    with pytest.raises(AssertionError, match="missing caller"):
        check_member_callers(row, tmp_path)
    (tmp_path / "hooks").mkdir()
    (tmp_path / "hooks" / "check.ps1").write_text("# fixture\n", encoding="utf-8")
    check_member_callers(row, tmp_path)


def test_unpinned_member_cannot_install(tmp_path, monkeypatch):
    row = copy.deepcopy(next(r for r in members() if r["slug"] == "tripwire"))
    row["tag"] = None
    def forbidden(*args, **kwargs):
        pytest.fail("unpinned member attempted installation")
    monkeypatch.setattr(subprocess, "run", forbidden)
    with pytest.raises(AssertionError, match="missing pinned tag"):
        installed_tag(row, tmp_path)


def test_change_pack_selects_only_manifest_or_callers():
    spec = importlib.util.spec_from_file_location("companion_change_pack", ROOT / "tools/change_pack.py")
    pack = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pack)
    contract = "tests/companions/test_contracts.py"
    assert contract not in pack.selection(changed=["README.md"])[0]
    assert contract not in pack.selection(changed=[contract])[0]
    assert contract in pack.selection(changed=["config/companions.json"])[0]
    assert contract in pack.selection(changed=["config\\companions.json"])[0]
    assert contract in pack.selection(changed=["./config/companions.json"])[0]
    assert contract in pack.selection(changed=[str(MANIFEST)])[0]
    for row in members():
        for caller in row["callers"]:
            if not caller.startswith("member:"):
                assert contract in pack.selection(changed=[caller])[0]


def test_change_pack_cli_selection(tmp_path):
    for changed, expected in (("README.md", False), ("config/companions.json", True)):
        proc = subprocess.run(
            [sys.executable, "-B", str(ROOT / "tools/change_pack.py"), "--list", "--changed", changed],
            cwd=tmp_path, capture_output=True, text=True, timeout=30,
        )
        assert proc.returncode == 0, proc.stderr
        assert ("tests/companions/test_contracts.py" in json.loads(proc.stdout)["targets"]) == expected


def test_change_pack_source_archive_lists_conservative_selection(tmp_path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "config").mkdir()
    script = tmp_path / "tools/change_pack.py"
    shutil.copyfile(ROOT / "tools/change_pack.py", script)
    shutil.copyfile(MANIFEST, tmp_path / "config/companions.json")
    proc = subprocess.run([sys.executable, "-B", str(script), "--list"],
                          cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert "tests/companions/test_contracts.py" in result["targets"]
    assert result["changed_paths"] is None
    assert "outside a git checkout" in result["selection_source"]


def test_nested_source_copy_does_not_use_parent_git_history():
    # Use the existing checkout as the parent: no git init/add/commit is needed.
    git = shutil.which("git")
    if git is None:
        pytest.skip("nested source fixture requires git")
    parent = subprocess.run([git, "rev-parse", "--show-toplevel"], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    if parent.returncode:
        pytest.skip("nested source fixture requires an existing parent checkout")
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="contract-source-", dir=scratch) as folder:
        source = Path(folder).resolve()
        assert source.is_relative_to(scratch.resolve())
        assert source != Path(parent.stdout.strip()).resolve()
        (source / "tools").mkdir()
        (source / "config").mkdir()
        script = source / "tools/change_pack.py"
        shutil.copyfile(ROOT / "tools/change_pack.py", script)
        shutil.copyfile(MANIFEST, source / "config/companions.json")
        proc = subprocess.run([sys.executable, "-B", str(script), "--list"], cwd=source,
                              capture_output=True, text=True, timeout=30)
        assert proc.returncode == 0, proc.stderr
        result = json.loads(proc.stdout)
        assert "tests/companions/test_contracts.py" in result["targets"]
        assert result["changed_paths"] is None
        assert "parent git checkout" in result["selection_source"]


def test_clean_checkout_selects_latest_commit(monkeypatch):
    spec = importlib.util.spec_from_file_location("clean_change_pack", ROOT / "tools/change_pack.py")
    pack = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pack)
    calls = []

    def fake_git(argv, **kwargs):
        calls.append(argv)
        assert kwargs["encoding"] == "utf-8"
        if argv[1] == "rev-parse":
            assert argv[2] == "--show-toplevel"
            return subprocess.CompletedProcess(argv, 0, str(ROOT) + "\n", "")
        if argv[1] == "diff":
            return subprocess.CompletedProcess(argv, 0, "", "")
        assert argv[1] == "diff-tree"
        return subprocess.CompletedProcess(argv, 0, "config/companions.json\0", "")

    monkeypatch.setattr(pack.subprocess, "run", fake_git)
    paths, source = pack.changed_paths(None)
    assert paths == ["config/companions.json"]
    assert source == "latest commit (clean checkout)"
    assert pack.COMPANION_CONTRACTS in pack.selection(changed=paths)[0]
    calls.clear()
    paths, source = pack.changed_paths("HEAD")
    assert paths == [] and source == "git diff HEAD"
    assert all(argv[1] != "diff-tree" for argv in calls)
