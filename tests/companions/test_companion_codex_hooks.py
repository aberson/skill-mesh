"""v3.0.4: the tripwire file hook installed for Codex (core companion plan Step 21).

`-Provider codex` writes the companion's Codex hook into the user-layer
`<home>/.codex/hooks.json` (the same JSON contract as Claude's settings hooks), copies
the packaged hook to `<home>/.codex/hooks/companions/tripwire-pretool.ps1`, and records
it in the companion ledger with host codex. It never writes `config.toml`, so it never
writes a Codex hook-trust record; it prints one line asking the operator to trust the
entry in Codex's /hooks view instead.

Every test runs in a disposable home under tmp_path with the fake tools from
test_companions_install (no network, no real installed tool, no live home).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from test_companions_install import (
    BUILD_SCRIPT,
    COMPANION_LEDGER,
    INSTALL_SKILL_MESH,
    POWERSHELL,
    TAG,
    Env,
    member,
    pinned_manifest,
)

TRUST_LINE = "open /hooks in Codex and trust"
CODEX_ENTRY_KEYS = {"type", "command", "timeout"}
# A real user-layer hooks.json (Codex 0.167+), foreign to the companion.
FOREIGN_DOCUMENT = (
    '{\n  "description": "operator guards",\n  "hooks": {\n'
    '    "PreToolUse": [\n'
    '      {"matcher": "^Bash$", "hooks": [{"type": "command", '
    '"command": "py -3.14 -I -S C:\\\\guards\\\\secret-read-guard.py", '
    '"timeout": 10, "statusMessage": "secret-read-guard"}]}\n'
    "    ]\n  }\n}\n"
)


def hooks_json(home: Path) -> Path:
    return home / ".codex" / "hooks.json"


def config_toml(home: Path) -> Path:
    return home / ".codex" / "config.toml"


def copied(home: Path) -> Path:
    return home / ".codex" / "hooks" / "companions" / "tripwire-pretool.ps1"


def groups(home: Path, event: str = "PreToolUse") -> list[dict[str, object]]:
    if not hooks_json(home).exists():
        return []
    return json.loads(hooks_json(home).read_text(encoding="utf-8")).get("hooks", {}).get(event, [])


def commands(home: Path, event: str = "PreToolUse") -> list[str]:
    return [item["command"] for group in groups(home, event) for item in group.get("hooks", [])]


def expected_command(path: Path) -> str:
    text = str(path)
    if re.fullmatch(r"[A-Za-z0-9\\:._-]+", text):
        return "powershell.exe -NoProfile -NonInteractive -File " + text
    return 'powershell.exe -NoProfile -NonInteractive -File "' + text + '"'


def expected_group(home: Path) -> dict[str, object]:
    return {
        "matcher": "^Bash$",
        "hooks": [{"type": "command", "command": expected_command(copied(home)), "timeout": 5}],
    }


def codex_records(ledger: dict[str, object]) -> list[dict[str, object]]:
    return [r for r in ledger["members"]["tripwire"]["hooks"] if r["host"] == "codex"]


def run_codex(env: Env, manifest: Path, *args: str):
    # The Codex skills folder exists once the Skill Mesh codex profile is installed;
    # the member skill installer (passing-notes) needs it.
    (env.home / ".agents" / "skills").mkdir(parents=True, exist_ok=True)
    return env.companions(*args, provider="codex", manifest=manifest)


def tree(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


@pytest.fixture(scope="module")
def codex_mini_dist(tmp_path_factory):
    """A one-skill codex profile cut from a real build, so a skill install is fast."""
    full = tmp_path_factory.mktemp("codex-dist-full")
    r = subprocess.run(
        [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-File", str(BUILD_SCRIPT),
         "-OutputDir", str(full), "-Provider", "codex"],
        capture_output=True, text=True, timeout=300,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    mini = tmp_path_factory.mktemp("codex-dist-mini")
    skill = sorted(p for p in (full / "codex").iterdir() if p.is_dir() and p.name != "_shared")[0]
    target = mini / "codex" / skill.name
    target.mkdir(parents=True)
    for f in skill.iterdir():
        (target / f.name).write_bytes(f.read_bytes())
    return mini


def test_production_entry_creates_a_fresh_codex_hooks_json(tmp_path, codex_mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)

    result = env.run(
        INSTALL_SKILL_MESH, "-Provider", "codex", "-Home", str(env.home),
        "-DistDir", str(codex_mini_dist), "-Companions", "core",
        "-CompanionsManifest", str(manifest_path),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert copied(env.home).read_text(encoding="ascii") == f"# fake packaged tripwire codex hook {TAG}\n"
    document = json.loads(hooks_json(env.home).read_text(encoding="utf-8"))
    assert document == {"hooks": {"PreToolUse": [expected_group(env.home)]}}
    assert set(document["hooks"]["PreToolUse"][0]["hooks"][0]) == CODEX_ENTRY_KEYS
    # The Codex profile writes no Claude settings and never touches config.toml.
    assert not (env.home / ".claude" / "settings.json").exists()
    assert not config_toml(env.home).exists()
    assert TRUST_LINE in result.stdout


def test_ledger_records_the_codex_hook_with_host_codex(tmp_path):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)

    result = run_codex(env, manifest_path)

    assert result.returncode == 0, result.stdout + result.stderr
    (record,) = codex_records(env.ledger())
    assert record == {
        "kind": "file",
        "host": "codex",
        "event": "PreToolUse",
        "name": "pretool",
        "path": ".codex/hooks/companions/tripwire-pretool.ps1",
        "sha256": hashlib.sha256(copied(env.home).read_bytes()).hexdigest(),
        "matcher": "^Bash$",
        "timeout": 5,
    }
    # A Codex run records no Claude hook: the claude records stay a claude run's.
    assert [r["host"] for r in env.ledger()["members"]["tripwire"]["hooks"]] == ["codex"]


def test_merge_preserves_a_foreign_group_and_the_top_level_description(tmp_path):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    hooks_json(env.home).parent.mkdir(parents=True)
    original = FOREIGN_DOCUMENT.encode("utf-8")
    hooks_json(env.home).write_bytes(original)
    foreign_group = json.loads(FOREIGN_DOCUMENT)["hooks"]["PreToolUse"][0]

    result = run_codex(env, manifest_path)

    assert result.returncode == 0, result.stdout + result.stderr
    merged = hooks_json(env.home).read_bytes()
    appended = "," + json.dumps(expected_group(env.home), separators=(",", ":"))
    expected = FOREIGN_DOCUMENT.replace("}]}\n    ]", "}]}\n    " + appended + "]")
    assert merged == expected.encode("utf-8")
    document = json.loads(merged)
    assert document["description"] == "operator guards"
    # Append-only: the foreign group keeps index 0, so its Codex trust key
    # (<hooks.json>:pre_tool_use:0:0) is unchanged.
    assert document["hooks"]["PreToolUse"] == [foreign_group, expected_group(env.home)]
    assert Path(str(hooks_json(env.home)) + ".bak").read_bytes() == original


@pytest.mark.parametrize("home_name", ["home", "space home"])
def test_command_has_no_leading_quote_and_parses_in_windows_powershell(tmp_path, home_name):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    if home_name != "home":
        env.home = tmp_path / home_name
        env.home.mkdir()

    result = run_codex(env, manifest_path)

    assert result.returncode == 0, result.stdout + result.stderr
    (command,) = commands(env.home)
    assert command == expected_command(copied(env.home))
    assert not command.startswith(('"', "'"))
    assert (" " in str(copied(env.home))) is command.endswith('"')
    # Codex runs a hook command through PowerShell. Parse it with Windows
    # PowerShell 5.1's own parser: no errors, and the first token is the bare
    # command name. The leading-quoted form is the red anchor: it must fail to
    # parse, which is why the companion never writes it.
    quoted = '"%s" -NoProfile -NonInteractive -File "%s"' % (
        r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe", copied(env.home))
    probe = (
        "$ErrorActionPreference='Stop';"
        "foreach ($name in 'HOOK_COMMAND','HOOK_ANCHOR') {"
        "$t=$null;$e=$null;"
        "[void][System.Management.Automation.Language.Parser]::ParseInput("
        "[Environment]::GetEnvironmentVariable($name),[ref]$t,[ref]$e);"
        "Write-Output ($name + '|' + $e.Count + '|' + $t[0].Kind + '|' + $t[0].Text)}"
    )
    child_env = dict(os.environ, HOOK_COMMAND=command, HOOK_ANCHOR=quoted)
    parsed = subprocess.run(
        [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-Command", probe],
        capture_output=True, text=True, env=child_env, timeout=120,
    )
    assert parsed.returncode == 0, parsed.stdout + parsed.stderr
    rows = dict(line.split("|", 1) for line in parsed.stdout.splitlines() if "|" in line)
    assert rows["HOOK_COMMAND"] == "0|Generic|powershell.exe"
    assert not rows["HOOK_ANCHOR"].startswith("0|"), rows["HOOK_ANCHOR"]
    # And it runs: the copied hook executes with a PreToolUse payload on stdin.
    ran = subprocess.run(
        [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-Command",
         "Invoke-Expression $env:HOOK_COMMAND; exit $LASTEXITCODE"],
        input=json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                          "tool_input": {"command": "git status"}}),
        capture_output=True, text=True, env=child_env, timeout=120,
    )
    assert ran.returncode == 0, ran.stdout + ran.stderr


@pytest.mark.parametrize("broken", [b'{"hooks": [}', b"", b'{"hooks": {"PreToolUse": {}}}'])
def test_malformed_hooks_json_is_refused_and_left_byte_identical(tmp_path, broken):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    hooks_json(env.home).parent.mkdir(parents=True)
    hooks_json(env.home).write_bytes(broken)

    result = run_codex(env, manifest_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert hooks_json(env.home).read_bytes() == broken
    assert not Path(str(hooks_json(env.home)) + ".bak").exists()
    assert not copied(env.home).exists()
    assert "file hook skipped: settings invalid" in result.stdout
    assert TRUST_LINE not in result.stdout
    assert codex_records(env.ledger()) == []


@pytest.mark.parametrize(
    "toml",
    [
        '[[hooks.PreToolUse]]\nmatcher = "^Bash$"\n\n[[hooks.PreToolUse.hooks]]\n'
        'type = "command"\ncommand = "echo config-layer"\n',
        '[hooks]\nPreToolUse = []\n',
    ],
    ids=["array-of-tables", "inline-event"],
)
def test_config_toml_hook_definitions_skip_the_codex_hook(tmp_path, toml):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    config_toml(env.home).parent.mkdir(parents=True)
    config_toml(env.home).write_text(toml, encoding="utf-8")
    before = tree(env.home / ".codex")

    result = run_codex(env, manifest_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert tree(env.home / ".codex") == before
    skipped = [line for line in result.stdout.splitlines() if "defines hooks" in line]
    assert len(skipped) == 1, result.stdout
    assert "config.toml" in skipped[0] and "file hook skipped" in skipped[0]
    assert TRUST_LINE not in result.stdout
    assert codex_records(env.ledger()) == []


def test_config_toml_trust_records_alone_do_not_skip(tmp_path):
    # Codex keeps /hooks trust decisions under [hooks.state.*] in config.toml.
    # Those are not hook definitions (Codex 0.171 reports no two-layer warning
    # for them), so an operator who has trusted any hook still gets this one.
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    config_toml(env.home).parent.mkdir(parents=True)
    trust = (
        'model = "gpt-5"\n\n[hooks.state."C:\\\\x\\\\hooks.json:pre_tool_use:0:0"]\n'
        'trusted_hash = "sha256:00"\n'
    )
    config_toml(env.home).write_text(trust, encoding="utf-8")
    before = config_toml(env.home).read_bytes()

    result = run_codex(env, manifest_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert groups(env.home) == [expected_group(env.home)]
    assert config_toml(env.home).read_bytes() == before


def test_trust_line_is_printed_and_no_trust_record_is_written(tmp_path):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)

    result = run_codex(env, manifest_path)

    assert result.returncode == 0, result.stdout + result.stderr
    lines = [line for line in result.stdout.splitlines() if TRUST_LINE in line]
    assert len(lines) == 1, result.stdout
    assert str(copied(env.home)) in lines[0] and "PreToolUse" in lines[0]
    assert not config_toml(env.home).exists()
    for path, data in tree(env.home).items():
        assert b"trusted_hash" not in data, path


def test_rerun_is_idempotent_and_prints_no_trust_line(tmp_path):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    hooks_json(env.home).parent.mkdir(parents=True)
    hooks_json(env.home).write_text(FOREIGN_DOCUMENT, encoding="utf-8")
    assert run_codex(env, manifest_path).returncode == 0
    before = tree(env.home)
    stamps = {p: p.stat().st_mtime_ns for p in env.home.rglob("*") if p.is_file()}

    result = run_codex(env, manifest_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert tree(env.home) == before
    assert {p: p.stat().st_mtime_ns for p in env.home.rglob("*") if p.is_file()} == stamps
    assert TRUST_LINE not in result.stdout
    assert "tripwire: already current" in result.stdout


def test_uninstall_removes_only_the_owned_entry_and_file(tmp_path):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    hooks_json(env.home).parent.mkdir(parents=True)
    hooks_json(env.home).write_text(FOREIGN_DOCUMENT, encoding="utf-8")
    assert run_codex(env, manifest_path).returncode == 0
    assert copied(env.home).exists()

    result = run_codex(env, manifest_path, "-Uninstall")

    assert result.returncode == 0, result.stdout + result.stderr
    assert hooks_json(env.home).read_text(encoding="utf-8") == FOREIGN_DOCUMENT
    assert not copied(env.home).exists()
    assert env.ledger() is None


def test_uninstall_reports_moved_later_entries(tmp_path):
    # Codex keys trust by position (<file>:<event>:<group>:<handler>). Removing
    # the owned group moves any later group up one place, so the operator is told.
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    assert run_codex(env, manifest_path).returncode == 0
    data = json.loads(hooks_json(env.home).read_text(encoding="utf-8"))
    later = {"matcher": "^Bash$", "hooks": [{"type": "command", "command": "later guard"}]}
    data["hooks"]["PreToolUse"].append(later)
    hooks_json(env.home).write_text(json.dumps(data), encoding="utf-8")

    result = run_codex(env, manifest_path, "-Uninstall")

    assert result.returncode == 0, result.stdout + result.stderr
    assert groups(env.home) == [later]
    assert "1 later Codex PreToolUse hook entry moved" in result.stdout


def test_skip_hook_tripwire_is_honoured_and_removes_an_owned_entry(tmp_path):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    (tmp_path / "fresh").mkdir()
    fresh = Env(tmp_path / "fresh")

    skipped = run_codex(fresh, manifest_path, "-SkipHook", "tripwire")
    assert skipped.returncode == 0, skipped.stdout + skipped.stderr
    assert not hooks_json(fresh.home).exists() and not copied(fresh.home).exists()
    assert fresh.ledger()["opt_outs"]["skip_hook"] == ["tripwire"]

    assert run_codex(env, manifest_path).returncode == 0
    assert commands(env.home)
    result = run_codex(env, manifest_path, "-SkipHook", "tripwire")

    assert result.returncode == 0, result.stdout + result.stderr
    assert commands(env.home) == [] and not copied(env.home).exists()
    assert codex_records(env.ledger()) == []
    assert "file hook skipped: opted out" in result.stdout


def test_no_hooks_is_honoured(tmp_path):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)

    result = run_codex(env, manifest_path, "-NoHooks")

    assert result.returncode == 0, result.stdout + result.stderr
    assert not hooks_json(env.home).exists() and not copied(env.home).exists()
    assert env.ledger()["opt_outs"]["no_hooks"] is True


def test_claude_and_codex_hooks_in_one_home_are_kept_apart(tmp_path):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    (env.home / ".claude" / "skills").mkdir(parents=True)
    claude = env.companions(provider="claude", manifest=manifest_path)
    assert claude.returncode == 0, claude.stdout + claude.stderr
    claude_settings = (env.home / ".claude" / "settings.json").read_bytes()

    codex = run_codex(env, manifest_path)

    assert codex.returncode == 0, codex.stdout + codex.stderr
    # The Codex run neither reconciles away nor rewrites the Claude hook.
    assert (env.home / ".claude" / "settings.json").read_bytes() == claude_settings
    hosts = sorted(r["host"] for r in env.ledger()["members"]["tripwire"]["hooks"])
    assert hosts == ["claude", "codex"]
    again = env.companions(provider="claude", manifest=manifest_path)
    assert again.returncode == 0
    assert groups(env.home) == [expected_group(env.home)]

    removed = run_codex(env, manifest_path, "-Uninstall")

    assert removed.returncode == 0, removed.stdout + removed.stderr
    assert groups(env.home) == []
    assert not copied(env.home).exists()
    assert not (env.home / ".claude" / "hooks" / "companions" / "tripwire-pretool.ps1").exists()


def test_a_tag_without_codex_hook_packaging_skips_only_the_codex_hook(tmp_path):
    # tripwire v0.1.1 has no `hook path --host codex`; its locate fails, and the
    # companion reports the skip and carries on (fail open).
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    env.fail.append("hook-path:codex")

    result = run_codex(env, manifest_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "tripwire: file hook skipped: hook locate failed (exit 2)" in result.stdout
    assert not hooks_json(env.home).exists()
    assert "tripwire: installed" in result.stdout


def test_modified_codex_hook_file_is_kept_on_uninstall(tmp_path):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    assert run_codex(env, manifest_path).returncode == 0
    copied(env.home).write_text("# user modified\n", encoding="ascii")

    result = run_codex(env, manifest_path, "-Uninstall")

    assert result.returncode == 0, result.stdout + result.stderr
    assert copied(env.home).read_text(encoding="ascii") == "# user modified\n"
    assert "modified hook file" in result.stdout
    assert commands(env.home) == []


def test_codex_manifest_rows_match_the_trusted_uninstall_record(tmp_path):
    # Uninstall trusts only a fixed record shape per host; the manifest row must
    # produce exactly that shape, or an owned hook could never be removed.
    manifest_path, manifest = pinned_manifest(tmp_path)
    (row,) = [h for h in member(manifest, "tripwire")["hooks"] if h["host"] == "codex"]
    env = Env(tmp_path)
    assert run_codex(env, manifest_path).returncode == 0
    (record,) = codex_records(env.ledger())
    assert (record["matcher"], record["timeout"], record["event"], record["name"]) == (
        row["matcher"], row["timeout"], row["event"], row["name"])
    assert (env.home / COMPANION_LEDGER).exists()
