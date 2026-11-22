"""Step 10: Claude hooks installed through the production companion entry point."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from test_companions_install import (
    COMPANION_LEDGER,
    INSTALL_SKILL_MESH,
    MANIFEST,
    POWERSHELL,
    SYSTEM_PATH,
    TAG,
    NEW_TAG,
    Env,
    member,
    mini_dist,
    pinned_manifest,
    skill_install,
)


def settings(home: Path) -> Path:
    return home / ".claude" / "settings.json"


def groups(home: Path, event: str) -> list[dict[str, object]]:
    if not settings(home).exists():
        return []
    return json.loads(settings(home).read_text(encoding="utf-8")).get("hooks", {}).get(event, [])


def commands(home: Path, event: str) -> list[str]:
    return [
        item["command"]
        for group in groups(home, event)
        for item in group.get("hooks", [])
        if isinstance(item, dict) and isinstance(item.get("command"), str)
    ]


def hook_record(ledger: dict[str, object], slug: str) -> dict[str, object]:
    records = ledger["members"][slug]["hooks"]
    assert len(records) == 1
    return records[0]


def load_settings_helper():
    path = INSTALL_SKILL_MESH.parent / "companion_settings.py"
    spec = importlib.util.spec_from_file_location("companion_settings_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_production_entry_installs_both_claude_hook_kinds(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)

    result = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest", str(manifest_path)
    )

    assert result.returncode == 0, result.stdout + result.stderr
    copied = env.home / ".claude" / "hooks" / "companions" / "tripwire-pretool.ps1"
    assert copied.exists(), result.stdout + result.stderr
    assert copied.read_text(encoding="ascii") == "# fake packaged tripwire hook v9.9.9\n"
    (tripwire_command,) = commands(env.home, "PreToolUse")
    assert tripwire_command == (
        f'powershell.exe -NoProfile -NonInteractive -File "{copied}"'
    )
    tripwire_group = groups(env.home, "PreToolUse")[0]
    assert tripwire_group["matcher"] == "Bash|PowerShell"
    assert tripwire_group["hooks"][0]["timeout"] == 5
    assert tripwire_group["hooks"][0]["onFailure"] == "continue"
    assert commands(env.home, "Stop") == ["passing-notes hook stop"]
    ledger = env.ledger()
    file_record = hook_record(ledger, "tripwire")
    assert file_record["sha256"] == hashlib.sha256(copied.read_bytes()).hexdigest()
    assert "pending_sha256" not in file_record
    assert hook_record(ledger, "passing-notes")["owned"] is True


@pytest.mark.parametrize("initial", [None, b"{}\n"])
def test_missing_and_empty_object_settings_are_merged(tmp_path, mini_dist, initial):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    if initial is not None:
        settings(env.home).parent.mkdir(parents=True)
        settings(env.home).write_bytes(initial)

    result = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest", str(manifest_path)
    )

    assert result.returncode == 0
    assert json.loads(settings(env.home).read_text(encoding="utf-8"))
    assert commands(env.home, "PreToolUse")
    assert commands(env.home, "Stop")


def test_zero_byte_settings_are_refused_without_writes(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    settings(env.home).parent.mkdir(parents=True)
    settings(env.home).write_bytes(b"")

    result = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest", str(manifest_path)
    )

    assert result.returncode == 0
    assert settings(env.home).read_bytes() == b""
    assert "settings file is empty" in result.stdout
    assert not (env.home / ".claude" / "hooks" / "companions" / "tripwire-pretool.ps1").exists()


def test_unrelated_settings_bytes_and_hooks_are_retained(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    original = (
        '{\n  "theme": "dark",\n  "hooks": {\n'
        '    "Notification": [{"hooks": [{"type": "command", "command": "foreign"}]}],\n'
        '    "Stop": [{"hooks": [{"type": "command", "command": "passing-notes hook stop", "timeout": 10}]}]\n'
        "  }\n}\n"
    ).encode()
    settings(env.home).parent.mkdir(parents=True)
    settings(env.home).write_bytes(original)

    result = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest", str(manifest_path)
    )

    assert result.returncode == 0
    merged = settings(env.home).read_bytes()
    copied = env.home / ".claude" / "hooks" / "companions" / "tripwire-pretool.ps1"
    entry = {
        "matcher": "Bash|PowerShell",
        "hooks": [{
            "type": "command",
            "command": f'powershell.exe -NoProfile -NonInteractive -File "{copied}"',
            "timeout": 5,
            "onFailure": "continue",
        }],
    }
    expected = original.decode().replace(
        "\n  }\n}\n",
        "\n  ," + json.dumps("PreToolUse") + ":["
        + json.dumps(entry, separators=(",", ":")) + "]}\n}\n",
    ).encode()
    assert merged == expected
    assert Path(str(settings(env.home)) + ".bak").read_bytes() == original
    assert groups(env.home, "Notification") == [
        {"hooks": [{"type": "command", "command": "foreign"}]}
    ]


def test_malformed_settings_are_untouched_and_file_hook_is_not_copied(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    broken = b'{"hooks": [}'
    settings(env.home).parent.mkdir(parents=True)
    settings(env.home).write_bytes(broken)

    result = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest", str(manifest_path)
    )

    assert result.returncode == 0
    assert settings(env.home).read_bytes() == broken
    assert not Path(str(settings(env.home)) + ".bak").exists()
    assert not (env.home / ".claude" / "hooks" / "companions" / "tripwire-pretool.ps1").exists()
    assert "settings invalid" in result.stdout


@pytest.mark.parametrize("quoted", [True, False])
def test_hand_registered_tripwire_collision_is_reported_without_duplicate(
    tmp_path, mini_dist, quoted
):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    foreign = tmp_path / "manual" / "tripwire-pretool.ps1"
    foreign.parent.mkdir()
    foreign.write_text("# manual\n", encoding="ascii")
    settings(env.home).parent.mkdir(parents=True)
    settings(env.home).write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Bash|PowerShell",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": (
                                        f'powershell.exe -File "{foreign}"'
                                        if quoted
                                        else f"powershell.exe -File {foreign}"
                                    ),
                                    "timeout": 5,
                                }
                            ],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    result = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest", str(manifest_path)
    )

    assert result.returncode == 0
    expected_command = (
        f'powershell.exe -File "{foreign}"'
        if quoted
        else f"powershell.exe -File {foreign}"
    )
    assert commands(env.home, "PreToolUse") == [expected_command]
    assert "hand-registered tripwire-pretool.ps1 entry" in result.stdout
    assert hook_record(env.ledger(), "passing-notes")["owned"] is True
    assert env.ledger()["members"]["tripwire"]["hooks"] == []


def test_preexisting_member_hook_is_not_owned_or_uninstalled(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    settings(env.home).parent.mkdir(parents=True)
    original = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "passing-notes hook stop", "timeout": 99}]}]}}
    settings(env.home).write_text(json.dumps(original), encoding="utf-8")

    install = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest", str(manifest_path)
    )
    assert install.returncode == 0
    assert hook_record(env.ledger(), "passing-notes")["owned"] is False

    uninstall = skill_install(
        env,
        mini_dist,
        "-Uninstall",
        "-Companions",
        "core",
        "-CompanionsManifest",
        str(manifest_path),
    )
    assert uninstall.returncode == 0
    assert commands(env.home, "Stop") == ["passing-notes hook stop"]


@pytest.mark.parametrize(
    ("locate", "reason"),
    [
        ("relative.ps1\n", "path that is not fully qualified"),
        ("C:tripwire-pretool.ps1\n", "path that is not fully qualified"),
        (r"C:\missing\tripwire-pretool.ps1" + "\n", "missing file"),
        ('C:\\bad"path\\tripwire-pretool.ps1\n', "path containing a quote"),
    ],
)
def test_invalid_locate_output_preserves_settings(tmp_path, mini_dist, locate, reason):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    env.overrides["FAKE_HOOK_LOCATE"] = locate
    settings(env.home).parent.mkdir(parents=True)
    settings(env.home).write_text("{}\n", encoding="utf-8")
    before = settings(env.home).read_bytes()

    result = skill_install(
        env,
        mini_dist,
        "-Companions",
        "core",
        "-CompanionsManifest",
        str(manifest_path),
        "-SkipHook",
        "passing-notes",
    )

    assert result.returncode == 0
    assert f"file hook skipped: hook locate returned a {reason}" in result.stdout
    assert settings(env.home).read_bytes() == before


def test_locate_outside_uv_tool_directory_is_refused(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    outside = tmp_path / "outside" / "tripwire-pretool.ps1"
    outside.parent.mkdir()
    outside.write_text("# outside\n", encoding="ascii")
    env.overrides["FAKE_HOOK_LOCATE"] = str(outside) + "\n"
    settings(env.home).parent.mkdir(parents=True)
    settings(env.home).write_text("{}\n", encoding="utf-8")
    before = settings(env.home).read_bytes()

    result = skill_install(
        env,
        mini_dist,
        "-Companions",
        "core",
        "-CompanionsManifest",
        str(manifest_path),
        "-SkipHook",
        "passing-notes",
    )

    assert result.returncode == 0
    assert "outside the uv tool directory" in result.stdout
    assert settings(env.home).read_bytes() == before


@pytest.mark.parametrize("extra", ["\n{path}\n", "{path}\n\n"])
def test_locate_output_with_blank_lines_is_refused(tmp_path, mini_dist, extra):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    packaged = env.tool_dir / "tripwire" / "hooks" / "claude" / "tripwire-pretool.ps1"
    packaged.parent.mkdir(parents=True)
    packaged.write_text("# located\n", encoding="ascii")
    env.overrides["FAKE_HOOK_LOCATE"] = extra.format(path=packaged)

    result = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest",
        str(manifest_path), "-SkipHook", "passing-notes"
    )

    assert result.returncode == 0
    assert "did not return exactly one line" in result.stdout
    assert not commands(env.home, "PreToolUse")


def test_located_hook_reparse_escape_is_refused(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside = outside_dir / "tripwire-pretool.ps1"
    outside.write_text("# outside\n", encoding="ascii")
    linked = env.tool_dir / "tripwire" / "hooks" / "claude" / "tripwire-pretool.ps1"
    linked.parent.mkdir(parents=True)
    try:
        linked.symlink_to(outside)
    except OSError as exc:
        linked.parent.rmdir()
        junction = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(linked.parent), str(outside_dir)],
            capture_output=True,
            text=True,
        )
        if junction.returncode != 0:
            pytest.skip(f"file links and junctions unavailable: {exc}; {junction.stderr}")
    env.overrides["FAKE_HOOK_LOCATE"] = str(linked) + "\n"

    result = skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest",
        str(manifest_path), "-SkipHook", "passing-notes"
    )

    assert result.returncode == 0
    assert "outside the uv tool directory" in result.stdout
    assert not commands(env.home, "PreToolUse")


def test_reinstall_is_hook_noop_and_uninstall_keeps_modified_file(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    settings(env.home).parent.mkdir(parents=True)
    foreign = {
        "matcher": "Write|Edit",
        "hooks": [{"type": "command", "command": "foreign hook", "timeout": 2}],
    }
    settings(env.home).write_text(
        json.dumps({"hooks": {"PreToolUse": [foreign]}}), encoding="utf-8"
    )
    args = ("-Companions", "core", "-CompanionsManifest", str(manifest_path))
    assert skill_install(env, mini_dist, *args).returncode == 0
    copied = env.home / ".claude" / "hooks" / "companions" / "tripwire-pretool.ps1"
    before_settings = settings(env.home).read_bytes()
    before_ledger = (env.home / COMPANION_LEDGER).read_bytes()
    before_file = copied.read_bytes()

    assert skill_install(env, mini_dist, *args).returncode == 0
    assert settings(env.home).read_bytes() == before_settings
    assert (env.home / COMPANION_LEDGER).read_bytes() == before_ledger
    assert copied.read_bytes() == before_file

    copied.write_text("# user modified\n", encoding="ascii")
    uninstall = skill_install(env, mini_dist, "-Uninstall", *args)
    assert uninstall.returncode == 0
    assert copied.read_text(encoding="ascii") == "# user modified\n"
    assert "modified hook file" in uninstall.stdout
    assert not any("hooks\\companions" in command for command in commands(env.home, "PreToolUse"))
    assert groups(env.home, "PreToolUse") == [foreign]
    assert "passing-notes hook stop" not in commands(env.home, "Stop")


def test_uninstall_removes_owned_unmodified_hook_file(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = ("-Companions", "core", "-CompanionsManifest", str(manifest_path))
    assert skill_install(env, mini_dist, *args).returncode == 0
    copied = env.home / ".claude" / "hooks" / "companions" / "tripwire-pretool.ps1"
    assert copied.exists()

    result = skill_install(env, mini_dist, "-Uninstall", *args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not copied.exists()
    assert not commands(env.home, "PreToolUse")


def test_uninstall_keeps_user_modified_registered_command(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = ("-Companions", "core", "-CompanionsManifest", str(manifest_path))
    assert skill_install(env, mini_dist, *args).returncode == 0
    data = json.loads(settings(env.home).read_text(encoding="utf-8"))
    item = data["hooks"]["PreToolUse"][-1]["hooks"][0]
    item["command"] = item["command"].replace(
        "-NonInteractive", "-NonInteractive -ExecutionPolicy Bypass"
    )
    settings(env.home).write_text(json.dumps(data), encoding="utf-8")
    copied = env.home / ".claude" / "hooks" / "companions" / "tripwire-pretool.ps1"

    result = skill_install(env, mini_dist, "-Uninstall", *args)

    assert result.returncode == 0
    assert "companion step reported a problem (exit 1)" in result.stdout
    assert "modified tripwire-pretool.ps1 entry" in result.stdout
    assert copied.exists()
    assert "-ExecutionPolicy Bypass" in commands(env.home, "PreToolUse")[0]
    assert (env.home / COMPANION_LEDGER).exists()


def test_uninstall_removes_only_owned_command_from_a_mixed_group(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = ("-Companions", "core", "-CompanionsManifest", str(manifest_path))
    assert skill_install(env, mini_dist, *args).returncode == 0
    data = json.loads(settings(env.home).read_text(encoding="utf-8"))
    owned_group = data["hooks"]["PreToolUse"][-1]
    foreign_item = {"type": "command", "command": "foreign nested hook", "timeout": 7}
    owned_group["hooks"].append(foreign_item)
    owned_group["note"] = "user field"
    settings(env.home).write_text(json.dumps(data), encoding="utf-8")

    result = skill_install(env, mini_dist, "-Uninstall", *args)

    assert result.returncode == 0
    remaining = groups(env.home, "PreToolUse")
    assert any(group.get("note") == "user field" for group in remaining)
    assert commands(env.home, "PreToolUse") == ["foreign nested hook"]


def test_file_hook_uninstall_refuses_duplicate_exact_entries(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = (
        "-Companions", "core", "-CompanionsManifest", str(manifest_path),
        "-SkipHook", "passing-notes",
    )
    assert skill_install(env, mini_dist, *args).returncode == 0
    data = json.loads(settings(env.home).read_text(encoding="utf-8"))
    data["hooks"]["PreToolUse"].append(
        json.loads(json.dumps(data["hooks"]["PreToolUse"][-1]))
    )
    settings(env.home).write_text(json.dumps(data), encoding="utf-8")
    before = settings(env.home).read_bytes()
    copied = env.home / ".claude" / "hooks" / "companions" / "tripwire-pretool.ps1"

    result = skill_install(env, mini_dist, "-Uninstall", *args)

    assert result.returncode == 0
    assert "multiple exact tripwire-pretool.ps1 entries" in result.stdout
    assert settings(env.home).read_bytes() == before
    assert copied.exists()
    assert hook_record(env.ledger(), "tripwire")


def test_member_uninstall_preserves_foreign_command_in_mixed_stop_group(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = ("-Companions", "core", "-CompanionsManifest", str(manifest_path))
    assert skill_install(env, mini_dist, *args).returncode == 0
    data = json.loads(settings(env.home).read_text(encoding="utf-8"))
    stop_group = next(
        group
        for group in data["hooks"]["Stop"]
        if any(item.get("command") == "passing-notes hook stop" for item in group["hooks"])
    )
    stop_group["hooks"].append(
        {"type": "command", "command": "foreign stop hook", "timeout": 3}
    )
    settings(env.home).write_text(json.dumps(data), encoding="utf-8")

    result = skill_install(env, mini_dist, "-Uninstall", *args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert commands(env.home, "Stop") == ["foreign stop hook"]


def test_member_uninstall_refuses_duplicate_exact_commands(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = (
        "-Companions", "core", "-CompanionsManifest", str(manifest_path),
        "-SkipHook", "tripwire",
    )
    assert skill_install(env, mini_dist, *args).returncode == 0
    data = json.loads(settings(env.home).read_text(encoding="utf-8"))
    data["hooks"]["Stop"].append(
        {"hooks": [{"type": "command", "command": "passing-notes hook stop", "timeout": 10}]}
    )
    settings(env.home).write_text(json.dumps(data), encoding="utf-8")
    before = settings(env.home).read_bytes()

    result = skill_install(env, mini_dist, "-Uninstall", *args)

    assert result.returncode == 0
    assert "more than one exact hook command is present" in result.stdout
    assert settings(env.home).read_bytes() == before
    assert hook_record(env.ledger(), "passing-notes")["owned"] is True


def test_untrusted_file_hook_ledger_path_is_kept(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = (
        "-Companions", "core", "-CompanionsManifest", str(manifest_path),
        "-SkipHook", "passing-notes",
    )
    assert skill_install(env, mini_dist, *args).returncode == 0
    planted = env.home / "user-file.ps1"
    planted.write_text("# user\n", encoding="ascii")
    ledger_path = env.home / COMPANION_LEDGER
    ledger = env.ledger()
    record = hook_record(ledger, "tripwire")
    record["path"] = "user-file.ps1"
    record["sha256"] = hashlib.sha256(planted.read_bytes()).hexdigest()
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")

    result = skill_install(env, mini_dist, "-Uninstall", *args)

    assert result.returncode == 0
    assert "does not match the owned tripwire destination" in result.stdout
    assert planted.read_text(encoding="ascii") == "# user\n"
    assert hook_record(env.ledger(), "tripwire")["path"] == "user-file.ps1"


def test_untrusted_member_uninstall_argv_is_never_executed(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = ("-Companions", "core", "-CompanionsManifest", str(manifest_path))
    assert skill_install(env, mini_dist, *args).returncode == 0
    ledger_path = env.home / COMPANION_LEDGER
    ledger = env.ledger()
    hook_record(ledger, "passing-notes")["uninstall"] = ["tripwire", "--version"]
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    env.reset_log()

    result = skill_install(env, mini_dist, "-Uninstall", *args)

    assert result.returncode == 0
    assert "does not match the approved passing-notes hook" in result.stdout
    assert not any(
        call["tool"] == "cli:tripwire" and call["argv"] == ["--version"]
        for call in env.calls()
    )
    assert hook_record(env.ledger(), "passing-notes")["uninstall"] == ["tripwire", "--version"]


def test_tag_upgrade_replaces_an_unmodified_owned_hook(tmp_path, mini_dist):
    manifest_path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = ("-Companions", "core", "-CompanionsManifest", str(manifest_path))
    assert skill_install(env, mini_dist, *args).returncode == 0
    copied = env.home / ".claude" / "hooks" / "companions" / "tripwire-pretool.ps1"
    assert copied.read_text(encoding="ascii").endswith(f"{TAG}\n")
    member(manifest, "tripwire")["tag"] = NEW_TAG
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = skill_install(env, mini_dist, *args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert copied.read_text(encoding="ascii").endswith(f"{NEW_TAG}\n")
    assert hook_record(env.ledger(), "tripwire")["sha256"] == hashlib.sha256(
        copied.read_bytes()
    ).hexdigest()


def test_interrupted_file_hook_install_recovers_from_prerecorded_ownership(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = ("-Companions", "core", "-CompanionsManifest", str(manifest_path))
    assert skill_install(env, mini_dist, *args).returncode == 0
    copied = env.home / ".claude" / "hooks" / "companions" / "tripwire-pretool.ps1"
    copied.unlink()
    data = json.loads(settings(env.home).read_text(encoding="utf-8"))
    data["hooks"]["PreToolUse"] = []
    settings(env.home).write_text(json.dumps(data), encoding="utf-8")
    assert hook_record(env.ledger(), "tripwire")["sha256"]

    result = skill_install(env, mini_dist, *args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert copied.exists()
    assert len(commands(env.home, "PreToolUse")) == 1


def test_interrupted_member_hook_install_retains_owned_recovery(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = ("-Companions", "core", "-CompanionsManifest", str(manifest_path))
    assert skill_install(env, mini_dist, *args).returncode == 0
    data = json.loads(settings(env.home).read_text(encoding="utf-8"))
    data["hooks"]["Stop"] = []
    settings(env.home).write_text(json.dumps(data), encoding="utf-8")
    assert hook_record(env.ledger(), "passing-notes")["owned"] is True

    result = skill_install(env, mini_dist, *args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert commands(env.home, "Stop") == ["passing-notes hook stop"]
    assert hook_record(env.ledger(), "passing-notes")["owned"] is True


def test_failed_member_hook_install_does_not_confer_uninstall_ownership(tmp_path, mini_dist):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = (
        "-Companions", "core", "-CompanionsManifest", str(manifest_path),
        "-SkipHook", "tripwire",
    )
    env.fail.append("hook-install:passing-notes")

    failed = skill_install(env, mini_dist, *args)

    assert failed.returncode == 0
    assert env.ledger()["members"]["passing-notes"]["hooks"] == []
    settings(env.home).parent.mkdir(parents=True, exist_ok=True)
    settings(env.home).write_text(
        json.dumps(
            {"hooks": {"Stop": [{"hooks": [{
                "type": "command", "command": "passing-notes hook stop", "timeout": 99,
            }]}]}}
        ),
        encoding="utf-8",
    )
    env.fail.clear()

    uninstalled = skill_install(env, mini_dist, "-Uninstall", *args)

    assert uninstalled.returncode == 0
    assert commands(env.home, "Stop") == ["passing-notes hook stop"]


def test_manifest_hook_removal_reconciles_owned_ledger_hooks(tmp_path, mini_dist):
    manifest_path, manifest = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = ("-Companions", "core", "-CompanionsManifest", str(manifest_path))
    assert skill_install(env, mini_dist, *args).returncode == 0
    for slug in ("tripwire", "passing-notes"):
        member(manifest, slug)["hooks"] = []
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = skill_install(env, mini_dist, *args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not commands(env.home, "PreToolUse")
    assert not commands(env.home, "Stop")
    assert env.ledger()["members"]["tripwire"]["hooks"] == []
    assert env.ledger()["members"]["passing-notes"]["hooks"] == []
    assert not (env.home / ".claude" / "hooks" / "companions" / "tripwire-pretool.ps1").exists()


def test_settings_merge_refuses_a_concurrent_external_edit(tmp_path, monkeypatch):
    helper = load_settings_helper()
    path = tmp_path / "settings.json"
    original = b'{"theme":"dark"}\n'
    external = b'{"theme":"external"}\n'
    path.write_bytes(original)
    calls = 0
    real_current = helper._current_bytes

    def changing_current(candidate):
        nonlocal calls
        calls += 1
        if calls == 2:
            path.write_bytes(external)
        return real_current(candidate)

    monkeypatch.setattr(helper, "_current_bytes", changing_current)
    entry = {
        "matcher": "Bash",
        "hooks": [{
            "type": "command", "command": 'powershell.exe -File "C:\\owned.ps1"',
            "timeout": 5, "onFailure": "continue",
        }],
    }
    with pytest.raises(helper.SettingsError, match="changed during merge"):
        helper.change("install", path, "PreToolUse", Path(r"C:\owned.ps1"), entry)
    assert path.read_bytes() == external


def test_settings_merge_does_not_follow_fixed_backup_or_temp_links(tmp_path):
    helper = load_settings_helper()
    path = tmp_path / "settings.json"
    original = b'{"theme":"dark"}\n'
    path.write_bytes(original)
    backup_target = tmp_path / "backup-target.txt"
    temp_target = tmp_path / "temp-target.txt"
    backup_target.write_bytes(b"backup secret")
    temp_target.write_bytes(b"temp secret")
    backup = Path(str(path) + ".bak")
    fixed_temp = Path(str(path) + ".skill-mesh.tmp")
    try:
        backup.symlink_to(backup_target)
        fixed_temp.symlink_to(temp_target)
    except OSError as exc:
        pytest.skip(f"file symlinks unavailable: {exc}")
    entry = {
        "matcher": "Bash",
        "hooks": [{
            "type": "command", "command": 'powershell.exe -File "C:\\owned.ps1"',
            "timeout": 5, "onFailure": "continue",
        }],
    }

    result = helper.change("install", path, "PreToolUse", Path(r"C:\owned.ps1"), entry)

    assert result == {"status": "installed"}
    assert backup_target.read_bytes() == b"backup secret"
    assert temp_target.read_bytes() == b"temp secret"
    assert backup.read_bytes() == original
    assert fixed_temp.is_symlink()


@pytest.mark.parametrize(
    ("flags", "skipped"),
    [
        (("-NoHooks",), {"tripwire", "passing-notes"}),
        (("-SkipHook", "tripwire"), {"tripwire"}),
        (("-SkipHook", "passing-notes"), {"passing-notes"}),
        (("-SkipHook", "tripwire", "-SkipHook", "passing-notes"), {"tripwire", "passing-notes"}),
    ],
)
def test_persisted_hook_opt_outs(tmp_path, mini_dist, flags, skipped):
    manifest_path, _ = pinned_manifest(tmp_path)
    env = Env(tmp_path)
    args = ("-Companions", "core", "-CompanionsManifest", str(manifest_path), *flags)

    assert skill_install(env, mini_dist, *args).returncode == 0
    ledger = env.ledger()
    assert ledger["opt_outs"]["no_hooks"] is ("-NoHooks" in flags)
    assert set(ledger["opt_outs"]["skip_hook"]) == (
        set() if "-NoHooks" in flags else skipped
    )
    assert bool(commands(env.home, "PreToolUse")) is ("tripwire" not in skipped)
    assert bool(commands(env.home, "Stop")) is ("passing-notes" not in skipped)

    # The persisted ledger is authoritative even when the flags are omitted later.
    assert skill_install(
        env, mini_dist, "-Companions", "core", "-CompanionsManifest", str(manifest_path)
    ).returncode == 0
    assert bool(commands(env.home, "PreToolUse")) is ("tripwire" not in skipped)
    assert bool(commands(env.home, "Stop")) is ("passing-notes" not in skipped)


def test_real_pinned_tools_install_and_execute_hooks_through_production_entry(tmp_path, mini_dist):
    """One command installs the pinned packages; their real hook commands then run."""
    uv = shutil.which("uv")
    git = shutil.which("git")
    if not uv or not git:
        pytest.fail("uv and git are required for the pinned companion integration")
    home = tmp_path / "real-home"
    home.mkdir()
    tool_dir = tmp_path / "real-uv-tools"
    tool_bin = tmp_path / "real-uv-bin"
    # PowerShell 5.1 derives its module-analysis cache from the profile's
    # conventional AppData/Local folder even when LOCALAPPDATA is overridden.
    # Create that disposable shape so it never falls back to a cwd-relative
    # Microsoft/Windows/PowerShell path.
    local = home / "AppData" / "Local"
    tool_dir.mkdir()
    tool_bin.mkdir()
    local.mkdir(parents=True)
    uv_only = tmp_path / "uv-only"
    uv_only.mkdir()
    shutil.copy2(uv, uv_only / "uv.exe")
    env = dict(os.environ)
    env.update(
        {
            "PATH": os.pathsep.join(
                [str(uv_only), str(Path(git).parent), str(Path(sys.executable).parent), str(tool_bin), *map(str, SYSTEM_PATH)]
            ),
            "UV_TOOL_DIR": str(tool_dir),
            "UV_TOOL_BIN_DIR": str(tool_bin),
            "UV_CACHE_DIR": str(tmp_path / "uv-cache"),
            "LOCALAPPDATA": str(local),
            "USERPROFILE": str(home),
            "HOME": str(home),
        }
    )
    result = subprocess.run(
        [
            str(POWERSHELL),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(INSTALL_SKILL_MESH),
            "-Provider",
            "claude",
            "-Home",
            str(home),
            "-DistDir",
            str(mini_dist),
            "-Companions",
            "core",
            "-CompanionsManifest",
            str(MANIFEST),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=1200,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "tripwire: installed" in result.stdout
    assert "passing-notes: installed" in result.stdout
    (registered_command,) = commands(home, "PreToolUse")
    hook_run = subprocess.run(
        registered_command,
        input=json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "git add -A"},
                "cwd": str(INSTALL_SKILL_MESH.parents[2]),
            }
        ),
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert hook_run.returncode == 0, hook_run.stdout + hook_run.stderr
    assert "additionalContext" in hook_run.stdout
    assert "permissionDecision" not in hook_run.stdout

    pn = tool_bin / ("passing-notes.exe" if os.name == "nt" else "passing-notes")
    fixture = tmp_path / "passing-notes-settings.json"
    install = subprocess.run(
        [str(pn), "hook", "install", "--settings", str(fixture)],
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert install.returncode == 0, install.stdout + install.stderr
    assert any(
        item.get("command") == "passing-notes hook stop"
        for group in json.loads(fixture.read_text(encoding="utf-8"))["hooks"]["Stop"]
        for item in group.get("hooks", [])
    )
    check = subprocess.run(
        [str(pn), "hook", "install", "--settings", str(fixture), "--check"],
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert check.returncode == 0, check.stdout + check.stderr
    assert "installed" in check.stdout.casefold()
    fixture_data = json.loads(fixture.read_text(encoding="utf-8"))
    owned_group = next(
        group
        for group in fixture_data["hooks"]["Stop"]
        if any(item.get("command") == "passing-notes hook stop" for item in group["hooks"])
    )
    owned_group["hooks"].append(
        {"type": "command", "command": "foreign stop hook", "timeout": 3}
    )
    fixture.write_text(json.dumps(fixture_data), encoding="utf-8")
    uninstall = subprocess.run(
        [str(pn), "hook", "uninstall", "--settings", str(fixture)],
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert uninstall.returncode == 0, uninstall.stdout + uninstall.stderr
    assert not any(
        item.get("command") == "passing-notes hook stop"
        for group in json.loads(fixture.read_text(encoding="utf-8")).get("hooks", {}).get("Stop", [])
        for item in group.get("hooks", [])
    )
    assert [
        item.get("command")
        for group in json.loads(fixture.read_text(encoding="utf-8"))["hooks"]["Stop"]
        for item in group.get("hooks", [])
    ] == ["foreign stop hook"]
