from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "experiments" / "recovery" / "run-lifecycle-probe.ps1"
TEMPLATE = REPO_ROOT / "experiments" / "recovery" / "lifecycle-probe" / "marketplace-template"
REPORT_TEMPLATE = REPO_ROOT / "documentation" / "experiments" / "lifecycle-report-template.md"
RUNBOOK = REPO_ROOT / "documentation" / "experiments" / "lifecycle-runbook.md"
SNAPSHOT_HELPER = REPO_ROOT / "experiments" / "recovery" / "lifecycle-probe" / "live_snapshot.py"
JOB_HELPER = REPO_ROOT / "experiments" / "recovery" / "lifecycle-probe" / "job_process.py"


FAKE_HOST = r'''#requires -Version 5.1
$HostKind = [string]$args[0]
if ($HostKind -notin @('codex', 'claude')) { [Console]::Error.WriteLine('host kind missing'); exit 89 }
$ErrorActionPreference = 'Stop'
$tokens = @($args | Select-Object -Skip 1)
if ($HostKind -eq 'codex') {
    if ($tokens.Count -eq 0 -or $tokens[0] -ne '--strict-config') { [Console]::Error.WriteLine('strict config missing'); exit 90 }
    $tokens = @($tokens | Select-Object -Skip 1)
}

function Test-ProviderKey([string]$Name) {
    return $Name -match '^(ANTHROPIC|OPENAI|CODEX|CLAUDE|CHATGPT|AZURE|AWS|CLOUD_ML|VERTEX|GOOGLE|OLLAMA|LMSTUDIO|MISTRAL|GROQ|TOGETHER|XAI|DEEPSEEK)_' -or $Name -eq 'VF_CLAUDE_BIN'
}
$allowed = if ($HostKind -eq 'codex') {
    @('CODEX_HOME', 'CODEX_SQLITE_HOME')
} else {
    @('CLAUDE_CONFIG_DIR', 'CLAUDE_CODE_PLUGIN_CACHE_DIR', 'CLAUDE_CODE_DISABLE_AUTO_MEMORY', 'CLAUDE_CODE_SKIP_PROMPT_HISTORY', 'CLAUDE_CODE_SYNC_PLUGIN_INSTALL', 'CLAUDE_CODE_AUTO_CONNECT_IDE')
}
$bad = @(Get-ChildItem Env: | Where-Object { (Test-ProviderKey $_.Name) -and $_.Name -notin $allowed })
if ($bad.Count -gt 0) { [Console]::Error.WriteLine("ambient provider keys survived: $($bad.Name -join ',')"); exit 91 }
if ($HostKind -eq 'claude' -and $env:CLAUDE_CODE_AUTO_CONNECT_IDE -ne 'false') {
    [Console]::Error.WriteLine('Claude IDE auto-connect is not disabled'); exit 97
}

$fakeHome = if ($HostKind -eq 'codex') { $env:CODEX_HOME } else { $env:CLAUDE_CONFIG_DIR }
if (-not $fakeHome) { [Console]::Error.WriteLine('isolated host home missing'); exit 92 }
foreach ($name in @('USERPROFILE', 'HOME', 'APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP')) {
    $value = [Environment]::GetEnvironmentVariable($name)
    if (-not $value -or -not ([System.IO.Path]::GetFullPath($value)).StartsWith([System.IO.Path]::GetFullPath($fakeHome), [System.StringComparison]::OrdinalIgnoreCase)) {
        [Console]::Error.WriteLine("$name is not isolated"); exit 93
    }
}
if ($HostKind -eq 'codex') {
    $config = Join-Path $fakeHome 'config.toml'
    if (-not (Test-Path -LiteralPath (Join-Path $fakeHome 'auth.json')) -or -not (Test-Path -LiteralPath $config)) { exit 94 }
    $configText = Get-Content -Raw -LiteralPath $config
    if ($configText -notmatch 'cli_auth_credentials_store\s*=\s*"file"' -or $configText -notmatch 'check_for_update_on_startup\s*=\s*false') { exit 95 }
} elseif (-not (Test-Path -LiteralPath (Join-Path $fakeHome '.credentials.json'))) { exit 96 }

if ($env:SMLP_FAKE_LIVE_TARGET) { Add-Content -LiteralPath $env:SMLP_FAKE_LIVE_TARGET -Value 'fake-live-write' }

$statePath = Join-Path $fakeHome 'fake-state.json'
function Load-State {
    if (Test-Path -LiteralPath $statePath) { return Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json }
    return [pscustomobject]@{ source = ''; marketplace = ''; plugin = ''; installed = $false; enabled = $true }
}
function Save-State($State) { $State | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath $statePath }
function Get-MarketplaceName([string]$Source) {
    $path = if ($HostKind -eq 'codex') { Join-Path $Source '.agents\plugins\marketplace.json' } else { Join-Path $Source '.claude-plugin\marketplace.json' }
    return [string](Get-Content -Raw -LiteralPath $path | ConvertFrom-Json).name
}
function Get-PluginName([string]$Source) {
    $path = if ($HostKind -eq 'codex') { Join-Path $Source '.agents\plugins\marketplace.json' } else { Join-Path $Source '.claude-plugin\marketplace.json' }
    return [string](Get-Content -Raw -LiteralPath $path | ConvertFrom-Json).plugins[0].name
}
function Install-Plugin($State, [string]$Selector) {
    if ($env:SMLP_FAKE_FAIL_OPERATION -eq 'install') { [Console]::Error.WriteLine('planned fake install failure'); exit 42 }
    $plugin = $Selector.Split('@')[0]
    $sourceRoot = Join-Path $State.source "plugins\$plugin"
    $targetParent = Join-Path $fakeHome 'plugins'
    $targetRoot = Join-Path $targetParent $plugin
    if (Test-Path -LiteralPath $targetRoot) { Remove-Item -Force -Recurse -LiteralPath $targetRoot }
    $null = New-Item -ItemType Directory -Force -Path $targetParent
    Copy-Item -Force -Recurse -LiteralPath $sourceRoot -Destination $targetRoot
    $State.plugin = $plugin; $State.installed = $true; $State.enabled = $true
    Save-State $State
}
function Remove-Plugin($State) {
    if ($State.plugin) {
        $target = Join-Path $fakeHome "plugins\$($State.plugin)"
        if (Test-Path -LiteralPath $target) { Remove-Item -Force -Recurse -LiteralPath $target }
    }
    $State.installed = $false; $State.enabled = $false; Save-State $State
}
function Write-PluginList($State, [bool]$Available) {
    if ($Available) { @([ordered]@{ name = $State.plugin; marketplace = $State.marketplace }) | ConvertTo-Json -Compress; return }
    if ($State.installed) {
        @([ordered]@{ name = $State.plugin; enabled = [bool]$State.enabled; installPath = (Join-Path $fakeHome "plugins\$($State.plugin)") }) | ConvertTo-Json -Compress
    } else { '[]' }
}
function Write-Consumer($State, [string]$Prompt) {
    if (-not $State.installed -or -not $State.enabled) {
        [ordered]@{ model = 'test-resolved-model'; result = 'not-discovered'; usage = [ordered]@{ input_tokens = 1; output_tokens = 1 } } | ConvertTo-Json -Compress
        return
    }
    $pluginRoot = Join-Path $fakeHome "plugins\$($State.plugin)"
    $values = @{}
    Get-Content -LiteralPath (Join-Path $pluginRoot 'shared\probe-reference.md') | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') { $values[$Matches[1]] = $Matches[2] }
    }
    Get-Content -LiteralPath (Join-Path $pluginRoot 'assets\probe-helper.txt') | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') { $values[$Matches[1]] = $Matches[2] }
    }
    if ($Prompt -match 'mesh-probe-beta') {
        $marker = "BETA|run=$($values.run_id)|version=$($values.version)|reference=$($values.reference_marker)|helper=$($values.helper_marker)"
    } else {
        $marker = "ALPHA|run=$($values.run_id)|version=$($values.version)|reference=$($values.reference_marker)"
    }
    [ordered]@{ model = 'test-resolved-model'; result = $marker; usage = [ordered]@{ input_tokens = 1; output_tokens = 1 } } | ConvertTo-Json -Compress
}

$state = Load-State
if ($tokens.Count -eq 1 -and $tokens[0] -eq '--version') { "$HostKind-test 0.0.0"; exit 0 }
if ($tokens[0] -eq 'exec') { Write-Consumer $state $tokens[-1]; exit 0 }
if ($tokens[0] -eq '-p') { Write-Consumer $state $tokens[1]; exit 0 }
if (($tokens[0] -eq 'login' -and $tokens[1] -eq 'status')) { 'Logged in using copied file'; exit 0 }
if (($tokens[0] -eq 'auth' -and $tokens[1] -eq 'status')) { '{"loggedIn": true}'; exit 0 }
if ($tokens[0] -ne 'plugin') { [Console]::Error.WriteLine('unknown command'); exit 97 }
if ($tokens[-1] -eq '--help') {
    if ($HostKind -eq 'codex' -and $tokens.Count -eq 2) {
        @'
Commands:
  add          Add a plugin
  list         List plugins
  marketplace  Manage marketplaces
  remove       Remove a plugin
  help         Print help

Options:
  --enable <FEATURE>  Enable a feature flag
  --disable <FEATURE> Disable a feature flag
'@
    } else { 'fake plugin subcommand help' }
    exit 0
}
if ($tokens[1] -eq 'validate') { 'valid'; exit 0 }
if ($tokens[1] -eq 'marketplace') {
    $action = $tokens[2]
    if ($action -eq 'add') {
        $state.source = $tokens[3]; $state.marketplace = Get-MarketplaceName $state.source; $state.plugin = Get-PluginName $state.source; Save-State $state; 'added'; exit 0
    }
    if ($action -eq 'list') { @([ordered]@{ name = $state.marketplace; source = $state.source }) | ConvertTo-Json -Compress; exit 0 }
    if ($action -eq 'update') { 'updated'; exit 0 }
    if ($action -eq 'remove') { $state.marketplace = ''; Save-State $state; 'removed'; exit 0 }
}
if ($tokens[1] -eq 'list') { Write-PluginList $state ($tokens -contains '--available'); exit 0 }
if ($tokens[1] -in @('add', 'install')) {
    if ($HostKind -eq 'codex' -and $tokens[1] -eq 'add' -and $state.installed) {
        if ($env:SMLP_FAKE_REPEAT_ADD_EXIT) { [Console]::Error.WriteLine('repeat-add unavailable'); exit ([int]$env:SMLP_FAKE_REPEAT_ADD_EXIT) }
        'already installed'; exit 0
    }
    Install-Plugin $state $tokens[2]; 'installed'; exit 0
}
if ($tokens[1] -eq 'update') { Install-Plugin $state $tokens[2]; 'updated'; exit 0 }
if ($tokens[1] -eq 'disable') { $state.enabled = $false; Save-State $state; 'disabled'; exit 0 }
if ($tokens[1] -eq 'enable') { $state.enabled = $true; Save-State $state; 'enabled'; exit 0 }
if ($tokens[1] -in @('remove', 'uninstall')) { Remove-Plugin $state; 'removed'; exit 0 }
[Console]::Error.WriteLine("unknown plugin command: $($tokens -join ' ')")
exit 98
'''


def _run(
    args: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout: int = 120
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def _run_snapshot(request: dict[str, object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-B", str(SNAPSHOT_HELPER)],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


def _run_job(request: dict[str, object], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-B", str(JOB_HELPER)],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def _job_request(tmp_path: Path, code: str, *, timeout_ms: int = 10_000) -> dict[str, object]:
    return {
        "schema": 1,
        "executable": sys.executable,
        "argv": ["-I", "-B", "-c", code],
        "cwd": str(tmp_path),
        "timeout_ms": timeout_ms,
        "stdout_path": str(tmp_path / "target-stdout.raw"),
        "stderr_path": str(tmp_path / "target-stderr.raw"),
    }


def _pid_exists(pid: int) -> bool:
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}",
        ],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _assert_pid_stops(pid: int, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_exists(pid):
            return
        time.sleep(0.05)
    pytest.fail(f"process {pid} still exists")


def _git(repo: Path, *args: str) -> str:
    result = _run(["git", *args], cwd=repo)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _ps_quote(value: Path | str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _make_whatif_repo(tmp_path: Path, host: str = "codex") -> dict[str, object]:
    repo = tmp_path / "repo"
    shutil.copytree(TEMPLATE, repo / "experiments" / "recovery" / "lifecycle-probe" / "marketplace-template")
    shutil.copy2(
        SNAPSHOT_HELPER,
        repo / "experiments" / "recovery" / "lifecycle-probe" / SNAPSHOT_HELPER.name,
    )
    shutil.copy2(
        JOB_HELPER,
        repo / "experiments" / "recovery" / "lifecycle-probe" / JOB_HELPER.name,
    )
    (repo / "experiments" / "recovery").mkdir(parents=True, exist_ok=True)
    shutil.copy2(RUNNER, repo / "experiments" / "recovery" / RUNNER.name)
    (repo / "documentation" / "experiments").mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPORT_TEMPLATE, repo / "documentation" / "experiments" / REPORT_TEMPLATE.name)
    shutil.copy2(RUNBOOK, repo / "documentation" / "experiments" / RUNBOOK.name)
    goal_a_id = "goala-20260814T040000Z-1234abcd"
    plan_path = repo / "plan.md"
    plan_path.write_text(
        f"**GoalAId:** `{goal_a_id}`\n\n"
        "### Step 74: Prepare the lifecycle fixture\n\n"
        "**Status:** IN PROGRESS\n",
        encoding="utf-8",
    )
    (repo / "tests" / "experiments").mkdir(parents=True, exist_ok=True)
    (repo / "tests" / "experiments" / "test_lifecycle_probe.py").write_text("# fixture\n", encoding="utf-8")

    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Skill Mesh Test")
    _git(repo, "config", "user.email", "skill-mesh-test@example.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "fixture")
    candidate_sha = _git(repo, "rev-parse", "HEAD")
    plan_path.write_text(
        f"**GoalAId:** `{goal_a_id}`\n\n"
        "### Step 74: Prepare the lifecycle fixture\n\n"
        "**Status:** DONE\n\n"
        f"**Candidate commit:** `{candidate_sha}`\n",
        encoding="utf-8",
    )
    _git(repo, "add", "plan.md")
    _git(repo, "commit", "-m", "record candidate")

    local_app_data = tmp_path / "localappdata"
    goal_root = local_app_data / "SkillMesh" / "Evidence" / goal_a_id
    goal_root.mkdir(parents=True)
    (goal_root / "evidence-index.md").write_text(
        "| `step74-candidate` | `git:1111111111111111111111111111111111111111` | `test` | superseded fixture |\n"
        f"| `step74-candidate` | `git:{candidate_sha}` | `test` | active fixture |\n",
        encoding="utf-8",
    )

    live_claude = tmp_path / "live" / "claude"
    live_codex = tmp_path / "live" / "codex"
    live_claude.mkdir(parents=True)
    live_codex.mkdir(parents=True)
    run_id = f"lifecycle-{host}-20260814T040100Z-deadbeef"
    evidence_dir = goal_root / "lifecycle" / run_id / "a0"
    disposable_home = local_app_data / "SkillMesh" / "Homes" / goal_a_id / f"{run_id}-a0"

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    marker = tmp_path / "host-was-invoked.txt"
    if host == "codex":
        fake_host = fake_bin / "codex.ps1"
        fake_host.write_text(f"Set-Content -LiteralPath {_ps_quote(marker)} -Value invoked\n", encoding="ascii")
    else:
        fake_host = fake_bin / "claude.cmd"
        fake_host.write_text(f"@echo invoked>{marker}\r\n", encoding="ascii")

    env = os.environ.copy()
    env["LOCALAPPDATA"] = str(local_app_data)
    env["PATH"] = str(fake_bin) + os.pathsep + env["PATH"]
    args = [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(repo / "experiments" / "recovery" / RUNNER.name),
        "-HostName",
        host,
        "-GoalAId",
        goal_a_id,
        "-DisposableHome",
        str(disposable_home),
        "-LiveClaudeHome",
        str(live_claude),
        "-LiveCodexHome",
        str(live_codex),
        "-EvidenceDir",
        str(evidence_dir),
        "-RunId",
        run_id,
        "-AttemptId",
        "a0",
        "-CandidateSha",
        candidate_sha,
        "-RequestedModel",
        "test-model",
        "-CredentialMode",
        "host-store",
        "-WhatIf",
    ]
    return {
        "repo": repo,
        "env": env,
        "args": args,
        "marker": marker,
        "evidence_dir": evidence_dir,
        "disposable_home": disposable_home,
        "live_claude": live_claude,
        "live_codex": live_codex,
        "candidate_sha": candidate_sha,
        "fake_bin": fake_bin,
    }


def _install_fake_host(fixture: dict[str, object]) -> None:
    fake_bin = Path(fixture["fake_bin"])
    fake_script = fake_bin / "fake-host.ps1"
    fake_script.write_text(FAKE_HOST, encoding="ascii")
    (fake_bin / "codex.ps1").write_text(
        "& powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass "
        "-File (Join-Path $PSScriptRoot 'fake-host.ps1') codex @args\nexit $LASTEXITCODE\n",
        encoding="ascii",
    )
    (fake_bin / "claude.cmd").write_text(
        '@powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass '
        '-File "%~dp0fake-host.ps1" claude %*\r\n',
        encoding="ascii",
    )


def _make_actual_fixture(tmp_path: Path, host: str) -> dict[str, object]:
    fixture = _make_whatif_repo(tmp_path, host)
    _install_fake_host(fixture)
    Path(fixture["live_codex"], "auth.json").write_text('{"tokens":"test-only"}\n', encoding="utf-8")
    Path(fixture["live_claude"], ".credentials.json").write_text(
        '{"claudeAiOauth":"test-only"}\n', encoding="utf-8"
    )
    args = list(fixture["args"])
    args.remove("-WhatIf")
    args[args.index("-CredentialMode") + 1] = "copy-file"
    fixture["args"] = args
    env = dict(fixture["env"])
    env["CLAUDE_CODE_OAUTH_TOKEN"] = "must-not-reach-child"
    env["OPENAI_API_KEY"] = "must-not-reach-child"
    env["CHATGPT_ACCESS_TOKEN"] = "must-not-reach-child"
    fixture["env"] = env
    return fixture


def test_runner_is_ascii_power_shell_51_and_dot_source_has_no_side_effect(tmp_path: Path) -> None:
    payload = RUNNER.read_bytes()
    payload.decode("ascii")
    assert not payload.startswith(b"\xef\xbb\xbf")
    marker = tmp_path / "dot-source-marker.txt"
    command = (
        f". {_ps_quote(RUNNER)}; "
        f"if (-not (Get-Command Invoke-LifecycleProbe -ErrorAction SilentlyContinue)) {{ exit 9 }}; "
        f"if (Test-Path -LiteralPath {_ps_quote(marker)}) {{ exit 10 }}; Write-Output DOT_SOURCE_OK"
    )
    result = _run(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command], cwd=REPO_ROOT)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "DOT_SOURCE_OK"
    assert not marker.exists()


def test_runner_parses_without_power_shell_errors() -> None:
    command = (
        f"$t=$null; $e=$null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile({_ps_quote(RUNNER)},[ref]$t,[ref]$e)|Out-Null; "
        "if ($e.Count) { $e | ForEach-Object { Write-Error $_.Message }; exit 1 }"
    )
    result = _run(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command], cwd=REPO_ROOT)
    assert result.returncode == 0, result.stderr


def test_codex_native_surface_uses_command_section_and_stops_on_new_commands() -> None:
    baseline = """Commands:
  add          Add a plugin
  list         List plugins
  marketplace  Manage marketplaces
  remove       Remove a plugin

Options:
  --enable <FEATURE>   Enable a feature flag
  --disable <FEATURE>  Disable a feature flag
"""
    changed = baseline.replace("  remove", "  update       Update a plugin\n  remove")
    command = (
        f". {_ps_quote(RUNNER)}; "
        f"$baseline={_ps_quote(baseline)}; $changed={_ps_quote(changed)}; "
        "$script:Checks=New-Object System.Collections.ArrayList; "
        "Assert-CodexNativeSurface $baseline 'help-evidence' 'test-version'; "
        "if (@($script:Checks | Where-Object {$_.status -eq 'UNAVAILABLE'}).Count -ne 2) { exit 11 }; "
        "try { Assert-CodexNativeSurface $changed 'help-evidence' 'test-version'; exit 12 } "
        "catch { if ($_.Exception.Data['probe_status'] -ne 'AMBIGUOUS') { exit 13 } }; "
        "Write-Output SURFACE_OK"
    )
    result = _run(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "SURFACE_OK"


def test_live_volatility_is_exact_dynamic_and_limits_attribution(tmp_path: Path) -> None:
    session = tmp_path / "session.jsonl"
    session.write_bytes(b"abcdef")

    def record(path: str, length: int, digest: str, file_id: str, physical: Path) -> dict[str, object]:
        return {
            "path": path,
            "kind": "FILE",
            "length": length,
            "final_length": length,
            "grew_during_read": False,
            "sha256": digest,
            "secret_hmac": "",
            "file_id": file_id,
            "physical_path": str(physical),
            "secret": False,
            "target": "",
        }

    first = {
        "records": [
            record(
                "codex/sessions/2026/08/13/example.jsonl",
                3,
                hashlib.sha256(b"abc").hexdigest(),
                "1:1",
                session,
            ),
            record("codex/logs_2.sqlite-shm", 8, "a" * 64, "2:2", session),
        ]
    }
    second = {
        "records": [
            record(
                "codex/sessions/2026/08/13/example.jsonl",
                6,
                hashlib.sha256(b"abcdef").hexdigest(),
                "1:1",
                session,
            ),
            record("codex/logs_2.sqlite-shm", 8, "b" * 64, "2:2", session),
        ]
    }
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    replacement_path = tmp_path / "replacement.json"
    first_path.write_text(json.dumps(first), encoding="utf-8")
    second_path.write_text(json.dumps(second), encoding="utf-8")
    replacement = json.loads(json.dumps(second))
    replacement["records"][0]["file_id"] = "9:9"
    replacement_path.write_text(json.dumps(replacement), encoding="utf-8")
    command = (
        f". {_ps_quote(RUNNER)}; "
        f"$first=Get-Content -Raw -LiteralPath {_ps_quote(first_path)}|ConvertFrom-Json; "
        f"$second=Get-Content -Raw -LiteralPath {_ps_quote(second_path)}|ConvertFrom-Json; "
        f"$replacement=Get-Content -Raw -LiteralPath {_ps_quote(replacement_path)}|ConvertFrom-Json; "
        "$v=Get-PreflightVolatility $first $second; "
        "if (@($v.append_paths).Count -ne 1 -or @($v.opaque_paths).Count -ne 1) { exit 21 }; "
        "$c=Compare-LiveHomeSnapshots $first $second @($v.append_paths) @($v.opaque_paths); "
        "if (-not $c.pass) { exit 22 }; "
        "try { $null=Get-PreflightVolatility $first $replacement; exit 23 } catch { }; "
        "$replaced=Compare-LiveHomeSnapshots $first $replacement @($v.append_paths) @($v.opaque_paths); "
        "if ($replaced.pass) { exit 24 }; Write-Output VOLATILITY_OK"
    )
    result = _run(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "VOLATILITY_OK"


def test_live_snapshot_helper_is_deterministic_bounded_and_secret_safe(tmp_path: Path) -> None:
    root = tmp_path / "root"
    target = tmp_path / "target"
    root.mkdir()
    target.mkdir()
    (root / "empty").mkdir()
    (root / "normal.txt").write_text("normal-data", encoding="utf-8")
    credential = target / "credential.json"
    credential.write_text("secret-A", encoding="utf-8")
    alias = root / "credential-alias"
    back = target / "cycle-back"
    for link, destination in ((alias, target), (back, root)):
        result = subprocess.run(
            [
                "cmd.exe",
                "/d",
                "/c",
                "mklink",
                "/J",
                str(link),
                str(destination),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

    key = "42" * 32
    request: dict[str, object] = {
        "schema": 1,
        "hmac_key_hex": key,
        "deadline_seconds": 10,
        "max_records": 100,
        "roots": [{"label": "root", "path": str(root)}],
        "secret_paths": [str(credential)],
        "allowed_reparse_roots": [str(tmp_path)],
    }
    first = _run_snapshot(request)
    second = _run_snapshot(request)
    assert first.returncode == second.returncode == 0, first.stderr + second.stderr
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["records"] == second_payload["records"]
    assert key not in first.stdout
    assert "secret-A" not in first.stdout
    assert not (SNAPSHOT_HELPER.parent / "__pycache__").exists()

    records = {record["path"]: record for record in first_payload["records"]}
    assert records["root/empty"]["kind"] == "DIR"
    secret_record = records["root/credential-alias@target/credential.json"]
    assert secret_record["secret"] is True
    assert secret_record["sha256"] == ""
    assert secret_record["secret_hmac"]
    assert records["root/credential-alias@target/cycle-back"]["kind"] == "REPARSE"

    credential.write_text("secret-B", encoding="utf-8")
    changed = _run_snapshot(request)
    assert changed.returncode == 0, changed.stderr
    changed_records = {record["path"]: record for record in json.loads(changed.stdout)["records"]}
    assert changed_records[secret_record["path"]]["secret_hmac"] != secret_record["secret_hmac"]

    timed_request = dict(request)
    timed_request["deadline_seconds"] = 0
    timed = _run_snapshot(timed_request)
    assert timed.returncode == 2
    assert "deadline exceeded" in timed.stderr
    assert not timed.stdout

    growth_root = tmp_path / "growth-root"
    growth_root.mkdir()
    growing_file = growth_root / "growing.bin"
    with growing_file.open("wb") as stream:
        stream.seek(64 * 1024 * 1024 - 1)
        stream.write(b"\0")
    stop_growth = threading.Event()
    writer_started = threading.Event()

    def append_while_snapshot_runs() -> None:
        with growing_file.open("ab", buffering=0) as stream:
            writer_started.set()
            while not stop_growth.is_set():
                stream.write(b"growth" * 1024)
                time.sleep(0.001)

    writer = threading.Thread(target=append_while_snapshot_runs, daemon=True)
    writer.start()
    assert writer_started.wait(timeout=5)
    growth_request = dict(request)
    growth_request["roots"] = [{"label": "growth", "path": str(growth_root)}]
    growth_request["secret_paths"] = []
    growth_request["allowed_reparse_roots"] = [str(growth_root)]
    try:
        growth = _run_snapshot(growth_request)
    finally:
        stop_growth.set()
        writer.join(timeout=5)
    assert growth.returncode == 0, growth.stderr
    growth_records = {item["path"]: item for item in json.loads(growth.stdout)["records"]}
    observed = growth_records["growth/growing.bin"]
    assert observed["grew_during_read"] is True
    assert observed["final_length"] > observed["length"]


def test_job_helper_contains_normal_timeout_and_surviving_grandchild(tmp_path: Path) -> None:
    normal_dir = tmp_path / "normal"
    normal_dir.mkdir()
    normal = _run_job(
        _job_request(
            normal_dir,
            "import sys; print('normal-out'); sys.stderr.write('normal-err'); raise SystemExit(7)",
        )
    )
    assert normal.returncode == 0, normal.stderr + normal.stdout
    normal_payload = json.loads(normal.stdout)
    assert normal_payload["status"] == "COMPLETE"
    assert normal_payload["assigned_before_resume"] is True
    assert normal_payload["root_exit_code"] == 7
    assert normal_payload["job_empty_confirmed"] is True
    assert normal_payload["survivors_existed"] is False
    assert (normal_dir / "target-stdout.raw").read_text(encoding="utf-8").strip() == "normal-out"
    assert (normal_dir / "target-stderr.raw").read_text(encoding="utf-8") == "normal-err"

    timeout_dir = tmp_path / "timeout"
    timeout_dir.mkdir()
    timed = _run_job(_job_request(timeout_dir, "import time; time.sleep(60)", timeout_ms=1_000))
    assert timed.returncode == 0, timed.stderr + timed.stdout
    timed_payload = json.loads(timed.stdout)
    assert timed_payload["timed_out"] is True
    assert timed_payload["terminate_job_called"] is True
    assert timed_payload["job_empty_confirmed"] is True

    survivor_dir = tmp_path / "survivor"
    survivor_dir.mkdir()
    grandchild = "import time; time.sleep(60)"
    intermediate = (
        "import subprocess,sys; "
        f"p=subprocess.Popen([sys.executable,'-I','-B','-c',{grandchild!r}]); "
        "print(p.pid, flush=True)"
    )
    root = (
        "import subprocess,sys; "
        f"subprocess.run([sys.executable,'-I','-B','-c',{intermediate!r}], check=True)"
    )
    survived = _run_job(_job_request(survivor_dir, root))
    assert survived.returncode == 0, survived.stderr + survived.stdout
    survived_payload = json.loads(survived.stdout)
    grandchild_pid = int((survivor_dir / "target-stdout.raw").read_text(encoding="utf-8").strip())
    assert survived_payload["survivors_existed"] is True
    assert grandchild_pid in survived_payload["survivor_pids"]
    assert survived_payload["terminate_job_called"] is True
    assert survived_payload["job_empty_confirmed"] is True
    _assert_pid_stops(grandchild_pid)


def test_job_helper_kill_on_close_and_create_new_are_fail_closed(tmp_path: Path) -> None:
    collision_dir = tmp_path / "collision"
    collision_dir.mkdir()
    marker = collision_dir / "target-ran.txt"
    collision_request = _job_request(collision_dir, f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')")
    Path(str(collision_request["stdout_path"])).write_text("occupied", encoding="utf-8")
    collision = _run_job(collision_request)
    assert collision.returncode == 2
    collision_payload = json.loads(collision.stdout)
    assert collision_payload["target_started"] is False
    assert collision_payload["job_empty_confirmed"] is True
    assert not marker.exists()

    killed_dir = tmp_path / "killed-helper"
    killed_dir.mkdir()
    killed_request = _job_request(
        killed_dir,
        "import os,time; print(os.getpid(), flush=True); time.sleep(60)",
        timeout_ms=120_000,
    )
    helper = subprocess.Popen(
        [sys.executable, "-I", "-B", str(JOB_HELPER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert helper.stdin is not None
    helper.stdin.write(json.dumps(killed_request))
    helper.stdin.close()
    target_stdout = Path(str(killed_request["stdout_path"]))
    deadline = time.monotonic() + 10
    target_pid = 0
    while time.monotonic() < deadline:
        if target_stdout.exists() and target_stdout.stat().st_size:
            target_pid = int(target_stdout.read_text(encoding="utf-8").strip())
            break
        time.sleep(0.05)
    assert target_pid
    assert _pid_exists(target_pid)
    helper.kill()
    helper.wait(timeout=10)
    _assert_pid_stops(target_pid)


def test_runner_marks_surviving_job_member_ambiguous_but_tree_clear(tmp_path: Path) -> None:
    evidence = tmp_path / "runner-evidence"
    (evidence / "commands").mkdir(parents=True)
    grandchild = "import time; time.sleep(60)"
    intermediate = (
        "import subprocess,sys; "
        f"p=subprocess.Popen([sys.executable,'-I','-B','-c',{grandchild!r}]); "
        "print(p.pid, flush=True)"
    )
    root = (
        "import subprocess,sys; "
        f"subprocess.run([sys.executable,'-I','-B','-c',{intermediate!r}], check=True)"
    )
    command = (
        f". {_ps_quote(RUNNER)}; "
        f"$EvidenceDir={_ps_quote(evidence)}; "
        "$script:DisposableHomeApproved=''; $script:EvidenceDirApproved=$EvidenceDir; "
        "$script:LiveClaudeHomeApproved=''; $script:LiveCodexHomeApproved=''; "
        "$script:ProcessTreeClear=$true; $script:CommandSequence=0; "
        "$script:CommandResults=New-Object System.Collections.ArrayList; "
        f"try {{ $null=Invoke-LoggedCommand 'survivor' {_ps_quote(sys.executable)} @('-I','-B','-c',{_ps_quote(root)}) @{{}} {_ps_quote(tmp_path)} 30; exit 31 }} "
        "catch { if ($_.Exception.Data['probe_status'] -ne 'AMBIGUOUS') { Write-Error $_; exit 32 } }; "
        "if (-not $script:ProcessTreeClear) { exit 33 }; Write-Output RUNNER_JOB_OK"
    )
    result = _run(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=REPO_ROOT,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert result.stdout.strip() == "RUNNER_JOB_OK"
    containment = json.loads((evidence / "commands" / "01-survivor" / "containment.json").read_text(encoding="utf-8"))
    assert containment["survivors_existed"] is True
    assert containment["job_empty_confirmed"] is True


def test_fixture_contract_has_two_skills_one_reference_and_one_helper() -> None:
    plugin = TEMPLATE / "plugins" / "mesh-lifecycle-probe"
    skills = sorted((plugin / "skills").glob("*/SKILL.md"))
    assert [path.parent.name for path in skills] == ["mesh-probe-alpha", "mesh-probe-beta"]
    alpha = skills[0].read_text(encoding="utf-8")
    beta = skills[1].read_text(encoding="utf-8")
    assert "../../shared/probe-reference.md" in alpha
    assert "../../shared/probe-reference.md" in beta
    assert "../../assets/probe-helper.txt" not in alpha
    assert "../../assets/probe-helper.txt" in beta
    assert "{{TRIGGER_ALPHA}}" in alpha
    assert "{{TRIGGER_BETA}}" in beta
    codex_manifest = (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    assert "defaultPrompt" in codex_manifest
    assert "mesh-probe" not in json.loads(codex_manifest)["interface"]["defaultPrompt"]
    assert "{{TRIGGER" not in json.loads(codex_manifest)["interface"]["defaultPrompt"]


def test_materialization_is_deterministic_run_specific_and_token_complete(tmp_path: Path) -> None:
    command = f"""
. {_ps_quote(RUNNER)}
$RunId = 'lifecycle-codex-20260814T040200Z-89abcdef'
$script:ProbeId = (Get-Sha256Text $RunId).Substring(0,12)
$script:PluginName = "skill-mesh-lifecycle-$($script:ProbeId)"
$script:MarketplaceName = "skill-mesh-lifecycle-market-$($script:ProbeId)"
$script:TriggerAlpha = "SMLP-$($script:ProbeId.ToUpperInvariant())-ALPHA"
$script:TriggerBeta = "SMLP-$($script:ProbeId.ToUpperInvariant())-BETA"
$script:CandidateTemplateRoot = {_ps_quote(TEMPLATE)}
$v1 = New-MaterializedMarketplace {_ps_quote(tmp_path / 'first-v1')} 'v1'
$v1b = New-MaterializedMarketplace {_ps_quote(tmp_path / 'second-v1')} 'v1'
$v2 = New-MaterializedMarketplace {_ps_quote(tmp_path / 'first-v2')} 'v2'
[pscustomobject]@{{
    v1 = $v1.tree_sha256
    v1_repeat = $v1b.tree_sha256
    v2 = $v2.tree_sha256
    plugin = $script:PluginName
    v1_version = $v1.version
    v2_version = $v2.version
}} | ConvertTo-Json -Compress
"""
    result = _run(["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command], cwd=REPO_ROOT)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["v1"] == data["v1_repeat"]
    assert data["v1"] != data["v2"]
    assert data["plugin"].startswith("skill-mesh-lifecycle-")
    assert data["v1_version"].startswith("1.0.0+codex.")
    assert data["v2_version"].startswith("2.0.0+codex.")
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert "{{" not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("host", ["codex", "claude"])
def test_whatif_is_deterministic_complete_and_launches_no_host(tmp_path: Path, host: str) -> None:
    fixture = _make_whatif_repo(tmp_path, host)
    first = _run(fixture["args"], cwd=fixture["repo"], env=fixture["env"])
    second = _run(fixture["args"], cwd=fixture["repo"], env=fixture["env"])
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first.stdout == second.stdout
    plan = json.loads(first.stdout)
    assert plan["candidate_sha"] == fixture["candidate_sha"]
    assert plan["host"] == host
    assert plan["live_snapshot"]["deadline_seconds"] == 600
    assert plan["live_snapshot"]["parent_timeout_seconds"] == 630
    assert plan["live_snapshot"]["max_records"] == 100_000
    assert any(path.endswith("report.md") for path in plan["write_targets"])
    assert any(path.endswith("manifest.sha256") for path in plan["write_targets"])
    assert len(plan["rendered_fixture_files"]) == 24
    assert "candidate-archive" in plan["planned_command_ids"]
    assert len(plan["operations"]) >= 8
    assert {item["id"] for item in plan["planned_commands"]} == set(plan["planned_command_ids"])
    assert all(item["arguments"] for item in plan["planned_commands"])
    assert any(path.endswith("live-append-allowlist.txt") for path in plan["write_targets"])
    assert any(path.endswith("live-volatile-allowlist.txt") for path in plan["write_targets"])
    assert any(path.endswith("installed-v1-plugin-locators.json") for path in plan["write_targets"])
    config_targets = [path for path in plan["write_targets"] if path.endswith("config.toml")]
    assert bool(config_targets) is (host == "codex")
    if host == "codex":
        assert all(item["arguments"][0] == "--strict-config" for item in plan["planned_commands"] if item["id"] != "candidate-archive")
    assert not fixture["marker"].exists()
    assert not fixture["evidence_dir"].exists()
    assert not fixture["disposable_home"].exists()


def test_whatif_copy_file_rejects_missing_credential_before_writes(tmp_path: Path) -> None:
    fixture = _make_whatif_repo(tmp_path, "claude")
    args = list(fixture["args"])
    args[args.index("-CredentialMode") + 1] = "copy-file"
    result = _run(args, cwd=fixture["repo"], env=fixture["env"])
    assert result.returncode == 2
    assert "credential source is absent" in result.stderr
    assert not Path(fixture["evidence_dir"]).exists()
    assert not Path(fixture["disposable_home"]).exists()


@pytest.mark.parametrize("relation", ["same", "inside-live", "contains-live", "inside-evidence"])
def test_whatif_rejects_protected_path_overlap(tmp_path: Path, relation: str) -> None:
    fixture = _make_whatif_repo(tmp_path)
    args = list(fixture["args"])
    disposable_index = args.index("-DisposableHome") + 1
    evidence_index = args.index("-EvidenceDir") + 1
    if relation == "same":
        args[disposable_index] = args[evidence_index]
    elif relation == "inside-live":
        args[disposable_index] = str(fixture["live_codex"] / "child")
    elif relation == "contains-live":
        args[disposable_index] = str(Path(fixture["live_codex"]).parent)
    else:
        args[disposable_index] = str(Path(fixture["evidence_dir"]) / "child")
    result = _run(args, cwd=fixture["repo"], env=fixture["env"])
    assert result.returncode == 2
    assert any(
        phrase in result.stderr.lower()
        for phrase in ("overlap", "below the goal a", "already exists")
    )
    assert not fixture["marker"].exists()


def test_whatif_rejects_host_run_id_mismatch_and_unrecorded_candidate(tmp_path: Path) -> None:
    fixture = _make_whatif_repo(tmp_path)
    mismatch = list(fixture["args"])
    run_index = mismatch.index("-RunId") + 1
    mismatch[run_index] = mismatch[run_index].replace("lifecycle-codex-", "lifecycle-claude-")
    result = _run(mismatch, cwd=fixture["repo"], env=fixture["env"])
    assert result.returncode == 2
    assert "host does not match" in result.stderr

    plan_path = Path(fixture["repo"]) / "plan.md"
    original_plan = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(
        original_plan.replace(str(fixture["candidate_sha"]), "f" * 40),
        encoding="utf-8",
    )
    result = _run(fixture["args"], cwd=fixture["repo"], env=fixture["env"])
    assert result.returncode == 2
    assert "does not match the active Step 74 candidate" in result.stderr
    plan_path.write_text(original_plan, encoding="utf-8")

    evidence_index = Path(fixture["env"]["LOCALAPPDATA"]) / "SkillMesh" / "Evidence" / "goala-20260814T040000Z-1234abcd" / "evidence-index.md"
    evidence_index.write_text("# no candidate\n", encoding="utf-8")
    result = _run(fixture["args"], cwd=fixture["repo"], env=fixture["env"])
    assert result.returncode == 2
    assert "exactly one matching Step 74 row" in result.stderr


@pytest.mark.parametrize(
    ("host", "expected_code", "expected_result"),
    [("claude", 0, "PASS"), ("codex", 1, "PARTIAL")],
)
def test_fake_host_executes_full_mutating_lifecycle_and_cleans_up(
    tmp_path: Path, host: str, expected_code: int, expected_result: str
) -> None:
    fixture = _make_actual_fixture(tmp_path, host)
    whatif = _run(
        [*fixture["args"], "-WhatIf"], cwd=fixture["repo"], env=fixture["env"]
    )
    assert whatif.returncode == 0, whatif.stderr
    plan = json.loads(whatif.stdout)
    result = _run(fixture["args"], cwd=fixture["repo"], env=fixture["env"], timeout=180)
    assert result.returncode == expected_code, result.stderr
    assert f"RESULT={expected_result}" in result.stdout
    assert not Path(fixture["disposable_home"]).exists()

    evidence_dir = Path(fixture["evidence_dir"])
    report = (evidence_dir / "report.md").read_text(encoding="utf-8")
    assert f"**{expected_result}**" in report
    assert "consumer-alpha-before-install | PASS" in report
    assert "consumer-beta-before-install | PASS" in report
    assert "consumer-bytes-v1 | PASS" in report
    assert "live-home-full-roots | PASS" in report
    assert "test-resolved-model" in report
    assert "must-not-reach-child" not in report
    assert (evidence_dir / "inventories" / "installed-v1-plugin-locators.json").is_file()
    assert (evidence_dir / "inventories" / "installed-v2-plugin-locators.json").is_file()

    argv_records = list((evidence_dir / "commands").glob("*/argv.json"))
    assert argv_records
    actual_ids = [path.parent.name.split("-", 1)[1] for path in sorted(argv_records)]
    assert actual_ids == plan["planned_command_ids"]
    first_argv = json.loads(argv_records[0].read_text(encoding="utf-8"))
    assert "CLAUDE_CODE_OAUTH_TOKEN" in first_argv["removed_ambient_provider_keys"]
    assert "OPENAI_API_KEY" in first_argv["removed_ambient_provider_keys"]
    manifest_lines = (evidence_dir / "manifest.sha256").read_text(encoding="utf-8").splitlines()
    retained = {
        path.relative_to(evidence_dir).as_posix()
        for path in evidence_dir.rglob("*")
        if path.is_file() and path.name != "manifest.sha256"
    }
    assert retained == {line.split("  ", 1)[1] for line in manifest_lines}


def test_codex_repeat_add_failure_still_runs_the_observation(tmp_path: Path) -> None:
    fixture = _make_actual_fixture(tmp_path, "codex")
    fixture["env"]["SMLP_FAKE_REPEAT_ADD_EXIT"] = "42"
    result = _run(fixture["args"], cwd=fixture["repo"], env=fixture["env"], timeout=180)
    assert result.returncode == 1, result.stderr
    assert "RESULT=PARTIAL" in result.stdout
    evidence_dir = Path(fixture["evidence_dir"])
    report = (evidence_dir / "report.md").read_text(encoding="utf-8")
    assert "repeat-add | UNAVAILABLE" in report
    assert list((evidence_dir / "commands").glob("*-consumer-alpha-after-repeat-add"))


def test_fake_host_clear_install_failure_reduces_to_fail(tmp_path: Path) -> None:
    fixture = _make_actual_fixture(tmp_path, "claude")
    fixture["env"]["SMLP_FAKE_FAIL_OPERATION"] = "install"
    result = _run(fixture["args"], cwd=fixture["repo"], env=fixture["env"], timeout=180)
    assert result.returncode == 1, result.stderr
    report = (Path(fixture["evidence_dir"]) / "report.md").read_text(encoding="utf-8")
    assert "**FAIL**" in report
    assert "run-completion | FAIL" in report
    assert not Path(fixture["disposable_home"]).exists()


def test_fake_host_live_root_write_is_ambiguous(tmp_path: Path) -> None:
    fixture = _make_actual_fixture(tmp_path, "claude")
    live_target = Path(fixture["live_claude"]) / "settings.json"
    live_target.write_text("{}\n", encoding="utf-8")
    fixture["env"]["SMLP_FAKE_LIVE_TARGET"] = str(live_target)
    result = _run(fixture["args"], cwd=fixture["repo"], env=fixture["env"], timeout=180)
    assert result.returncode == 3, result.stderr
    report = (Path(fixture["evidence_dir"]) / "report.md").read_text(encoding="utf-8")
    assert "**AMBIGUOUS**" in report
    assert "live-home-full-roots | AMBIGUOUS" in report


def test_runner_keeps_native_and_compatibility_operations_distinct() -> None:
    text = RUNNER.read_text(encoding="ascii")
    assert "plugin', 'marketplace', 'upgrade" not in text
    assert "native-update' 'UNAVAILABLE'" in text
    assert "native-enable-disable' 'UNAVAILABLE'" in text
    assert "feature flags are not substitutes" in text
    assert "compatibility-reinstall-v2" in text
    assert "'--tools', 'Skill,Read'" in text
    assert "'--allowedTools', 'Skill,Read'" in text
    assert "Test-SameOrChild $DisposableHome $DisposableHome" not in text
    assert "Assert-CleanupTarget" in text
    assert ".skill-mesh-lifecycle-owner.json" in text
    assert "runtime\\path-guard.ps1" not in text
    assert "cli_auth_credentials_store = \"file\"" in text
    assert "Remove-InheritedProviderEnvironment" in text
    assert "CLAUDE_CODE_AUTO_CONNECT_IDE'] = 'false'" in text
    assert "RootStartedUtc.AddSeconds(-2)" in text
    assert "A prior process tree is not confirmed stopped" in text
    assert "live_snapshot.py" in text
    assert '"-I -B $' in text
    assert "$script:LiveSnapshotDeadlineSeconds = 600" in text
    assert "$script:LiveSnapshotParentTimeoutMilliseconds = 630000" in text
    assert "$parentExited = $process.WaitForExit($script:LiveSnapshotParentTimeoutMilliseconds)" in text
    assert "deadline_seconds = $script:LiveSnapshotDeadlineSeconds" in text
    assert "$process.WaitForExit(150000)" not in text
    assert "deadline_seconds = 120" not in text
    assert "120 seconds and 100000 records" not in text


def test_docs_are_public_and_exact_tokens_are_consistent() -> None:
    private_home_prefix = "C:" + "\\Users\\"
    for path in (REPORT_TEMPLATE, RUNBOOK):
        text = path.read_text(encoding="utf-8")
        assert private_home_prefix not in text
        assert "TODO" not in text
    report_tokens = set(part.split("}}", 1)[0] for part in REPORT_TEMPLATE.read_text(encoding="utf-8").split("{{")[1:])
    runner_text = RUNNER.read_text(encoding="ascii")
    for token in report_tokens:
        assert f"{{{{{token}}}}}" in runner_text
    assert "fallback-report.txt" in RUNBOOK.read_text(encoding="utf-8")
    assert "(Join-Path $EvidenceDir 'fallback-report.txt')" in runner_text


def test_template_bytes_have_no_overlapping_legacy_placeholders() -> None:
    joined = "\n".join(path.read_text(encoding="utf-8") for path in TEMPLATE.rglob("*") if path.is_file())
    for legacy in (
        "PROBE_RUN_ID",
        "PROBE_VERSION",
        "REFERENCE_PROBE_VERSION",
        "HELPER_PROBE_VERSION",
        "PROBE_TRIGGER_ALPHA",
        "PROBE_TRIGGER_BETA",
    ):
        assert legacy not in joined
    assert hashlib.sha256(joined.encode("utf-8")).hexdigest()
