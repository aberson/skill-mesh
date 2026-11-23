"""Safely merge Skill Mesh owned file hooks into a host's hook settings JSON.

Claude reads them from ``<home>/.claude/settings.json``; Codex reads the same JSON hook
contract from its user layer ``<home>/.codex/hooks.json`` (``--host codex``).

The helper deliberately edits text at the containing object/array boundary.  Existing
settings bytes are therefore retained verbatim; only the new entry (or the exact owned
entry during removal) changes.  Invalid or ambiguous JSON is refused before backup or
write.

Codex keeps one hook layer per location: hooks defined in ``config.toml`` and in
``hooks.json`` load side by side with a warning.  With ``--codex-config`` an install or
inspect refuses (status ``layer-conflict``, nothing written) when that ``config.toml``
defines hooks.  Its ``[hooks.state.*]`` tables are Codex's own /hooks trust records, not
hook definitions, and are ignored; this helper never writes ``config.toml``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any


class SettingsError(ValueError):
    """The settings file cannot be changed without ambiguity."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SettingsError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _decode(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text, object_pairs_hook=_pairs)
    except (json.JSONDecodeError, UnicodeError, SettingsError) as exc:
        raise SettingsError(str(exc)) from None
    if not isinstance(value, dict):
        raise SettingsError("top-level settings value is not an object")
    hooks = value.get("hooks", {})
    if not isinstance(hooks, dict):
        raise SettingsError("hooks is not an object")
    return value


def _skip_ws(text: str, pos: int) -> int:
    while pos < len(text) and text[pos] in " \t\r\n":
        pos += 1
    return pos


def _string_end(text: str, pos: int) -> int:
    if pos >= len(text) or text[pos] != '"':
        raise SettingsError("expected JSON string")
    pos += 1
    while pos < len(text):
        if text[pos] == "\\":
            pos += 2
        elif text[pos] == '"':
            return pos + 1
        else:
            pos += 1
    raise SettingsError("unterminated JSON string")


def _value_end(text: str, pos: int) -> int:
    pos = _skip_ws(text, pos)
    if pos >= len(text):
        raise SettingsError("missing JSON value")
    if text[pos] == '"':
        return _string_end(text, pos)
    if text[pos] in "[{":
        opener = text[pos]
        closer = "]" if opener == "[" else "}"
        depth = 1
        pos += 1
        while pos < len(text):
            if text[pos] == '"':
                pos = _string_end(text, pos)
                continue
            if text[pos] == opener:
                depth += 1
            elif text[pos] == closer:
                depth -= 1
                if depth == 0:
                    return pos + 1
            pos += 1
        raise SettingsError("unterminated JSON container")
    end = pos
    while end < len(text) and text[end] not in ",]} \t\r\n":
        end += 1
    if end == pos:
        raise SettingsError("missing JSON scalar")
    return end


def _object_members(text: str, start: int, end: int) -> list[tuple[str, int, int]]:
    if text[start] != "{" or text[end - 1] != "}":
        raise SettingsError("expected JSON object")
    members: list[tuple[str, int, int]] = []
    pos = _skip_ws(text, start + 1)
    while pos < end - 1:
        key_start = pos
        key_end = _string_end(text, key_start)
        key = json.loads(text[key_start:key_end])
        pos = _skip_ws(text, key_end)
        if pos >= end or text[pos] != ":":
            raise SettingsError("expected colon after JSON key")
        value_start = _skip_ws(text, pos + 1)
        value_end = _value_end(text, value_start)
        members.append((key, value_start, value_end))
        pos = _skip_ws(text, value_end)
        if pos < end - 1:
            if text[pos] != ",":
                raise SettingsError("expected comma between JSON members")
            pos = _skip_ws(text, pos + 1)
    return members


def _array_elements(text: str, start: int, end: int) -> list[tuple[int, int]]:
    if text[start] != "[" or text[end - 1] != "]":
        raise SettingsError("expected JSON array")
    elements: list[tuple[int, int]] = []
    pos = _skip_ws(text, start + 1)
    while pos < end - 1:
        value_end = _value_end(text, pos)
        elements.append((pos, value_end))
        pos = _skip_ws(text, value_end)
        if pos < end - 1:
            if text[pos] != ",":
                raise SettingsError("expected comma between JSON values")
            pos = _skip_ws(text, pos + 1)
    return elements


def _member(text: str, start: int, end: int, name: str) -> tuple[int, int] | None:
    for key, value_start, value_end in _object_members(text, start, end):
        if key == name:
            return value_start, value_end
    return None


def _command_paths(group: Any) -> list[str]:
    if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
        return []
    paths: list[str] = []
    for hook in group["hooks"]:
        if not isinstance(hook, dict) or not isinstance(hook.get("command"), str):
            continue
        match = re.search(
            r'(?i)(?:^|\s)-File\s+(?:"([^"]+)"|(\S+))(?:\s|$)',
            hook["command"],
        )
        if match:
            paths.append(match.group(1) or match.group(2))
    return paths


def _norm(path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def _is_current(group: Any, companion_path: Path, entry: dict[str, Any]) -> bool:
    if not isinstance(group, dict) or group.get("matcher") != entry.get("matcher"):
        return False
    expected_hooks = entry.get("hooks")
    hooks = group.get("hooks")
    if (
        not isinstance(expected_hooks, list)
        or len(expected_hooks) != 1
        or not isinstance(hooks, list)
    ):
        return False
    expected_path = _norm(str(companion_path))
    return any(
        item == expected_hooks[0]
        and any(_norm(path) == expected_path for path in _command_paths({"hooks": [item]}))
        for item in hooks
    )


def _current_count(groups: list[Any], companion_path: Path, entry: dict[str, Any]) -> int:
    expected_hooks = entry.get("hooks")
    if not isinstance(expected_hooks, list) or len(expected_hooks) != 1:
        raise SettingsError("expected one companion hook command")
    expected_path = _norm(str(companion_path))
    count = 0
    for group in groups:
        if not isinstance(group, dict) or group.get("matcher") != entry.get("matcher"):
            continue
        hooks = group.get("hooks")
        if not isinstance(hooks, list):
            continue
        count += sum(
            item == expected_hooks[0]
            and any(
                _norm(path) == expected_path
                for path in _command_paths({"hooks": [item]})
            )
            for item in hooks
        )
    return count


def _is_collision(group: Any, companion_path: Path, entry: dict[str, Any]) -> bool:
    if _is_current(group, companion_path, entry):
        return False
    leaf = companion_path.name.casefold()
    return any(Path(path).name.casefold() == leaf for path in _command_paths(group))


def _event_groups(settings: dict[str, Any], event: str) -> list[Any]:
    hooks = settings.get("hooks", {})
    groups = hooks.get(event, [])
    if not isinstance(groups, list):
        raise SettingsError(f"hooks.{event} is not a list")
    return groups


def _append(text: str, event: str, entry: dict[str, Any]) -> str:
    payload = json.dumps(entry, ensure_ascii=True, separators=(",", ":"))
    root_end = _value_end(text, _skip_ws(text, 0))
    hooks_span = _member(text, _skip_ws(text, 0), root_end, "hooks")
    if hooks_span is None:
        insertion = json.dumps({"hooks": {event: [entry]}}, separators=(",", ":"))[1:-1]
        prefix = "," if _object_members(text, _skip_ws(text, 0), root_end) else ""
        return text[: root_end - 1] + prefix + insertion + text[root_end - 1 :]
    hooks_start, hooks_end = hooks_span
    event_span = _member(text, hooks_start, hooks_end, event)
    if event_span is None:
        prefix = "," if _object_members(text, hooks_start, hooks_end) else ""
        insertion = json.dumps(event) + ":[" + payload + "]"
        return text[: hooks_end - 1] + prefix + insertion + text[hooks_end - 1 :]
    event_start, event_end = event_span
    prefix = "," if _array_elements(text, event_start, event_end) else ""
    return text[: event_end - 1] + prefix + payload + text[event_end - 1 :]


def _cut_last(text: str, previous_end: int, start: int, end: int) -> str:
    """Remove a container's last element together with the comma before it.

    Cutting from the comma (not from the previous element's end) keeps the
    whitespace before the closing bracket, so removing an entry this helper
    appended restores the original bytes exactly.
    """
    comma = text.rindex(",", previous_end, start)
    return text[:comma] + text[end:]


def _remove_one(
    text: str,
    event: str,
    companion_path: Path,
    entry: dict[str, Any],
) -> tuple[str, bool, int]:
    """Remove the owned entry; also return how many later entries moved up.

    Codex keys a hook's trust by its position (``<file>:<event>:<group>:<handler>``),
    so the caller tells the operator when a removal shifts entries after it.
    """
    root_start = _skip_ws(text, 0)
    root_end = _value_end(text, root_start)
    hooks_span = _member(text, root_start, root_end, "hooks")
    if hooks_span is None:
        return text, False, 0
    event_span = _member(text, *hooks_span, event)
    if event_span is None:
        return text, False, 0
    elements = _array_elements(text, *event_span)
    for index in range(len(elements) - 1, -1, -1):
        start, end = elements[index]
        group = json.loads(text[start:end], object_pairs_hook=_pairs)
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            continue
        if group.get("matcher") != entry.get("matcher"):
            continue
        hooks_span = _member(text, start, end, "hooks")
        if hooks_span is None:
            continue
        items = _array_elements(text, *hooks_span)
        for item_index in range(len(items) - 1, -1, -1):
            item_start, item_end = items[item_index]
            item = json.loads(text[item_start:item_end], object_pairs_hook=_pairs)
            expected_hooks = entry.get("hooks")
            if not isinstance(expected_hooks, list) or len(expected_hooks) != 1:
                raise SettingsError("expected one companion hook command")
            if item != expected_hooks[0]:
                continue
            paths = _command_paths({"hooks": [item]})
            if not any(_norm(path) == _norm(str(companion_path)) for path in paths):
                continue
            # A generated group has only matcher + hooks. Once its sole owned
            # command is gone the empty group can go too. If the user added any
            # other command or group field, remove only our nested command.
            generated_group = set(group) <= {"matcher", "hooks"}
            if len(items) == 1 and generated_group:
                moved = len(elements) - 1 - index
                if len(elements) == 1:
                    return text[:start] + text[end:], True, moved
                if index < len(elements) - 1:
                    return text[:start] + text[elements[index + 1][0] :], True, moved
                return _cut_last(text, elements[index - 1][1], start, end), True, moved
            moved = len(items) - 1 - item_index
            if len(items) == 1:
                return text[:item_start] + text[item_end:], True, moved
            if item_index < len(items) - 1:
                return text[:item_start] + text[items[item_index + 1][0] :], True, moved
            return _cut_last(text, items[item_index - 1][1], item_start, item_end), True, moved
    return text, False, 0


def _read(path: Path) -> tuple[bytes | None, str]:
    if not path.exists():
        return None, "{}\n"
    raw = path.read_bytes()
    if not raw:
        raise SettingsError("settings file is empty")
    try:
        return raw, raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SettingsError(f"settings file is not UTF-8 ({exc})") from None


def _secure_temp(path: Path, suffix: str) -> Path:
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=path.name + suffix,
        dir=path.parent,
        delete=False,
    )
    handle.close()
    return Path(handle.name)


def _current_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def _write(path: Path, raw: bytes | None, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = text.encode("utf-8")
    if raw is not None and raw.startswith(b"\xef\xbb\xbf"):
        encoded = b"\xef\xbb\xbf" + encoded
    backup_temp: Path | None = None
    write_temp: Path | None = None
    try:
        if raw is not None:
            backup_temp = _secure_temp(path, ".bak.")
            backup_temp.write_bytes(raw)
        write_temp = _secure_temp(path, ".skill-mesh.tmp.")
        write_temp.write_bytes(encoded)
        if _current_bytes(path) != raw:
            raise SettingsError("settings file changed during merge; retry")
        if backup_temp is not None:
            os.replace(backup_temp, Path(str(path) + ".bak"))
            backup_temp = None
        if _current_bytes(path) != raw:
            raise SettingsError("settings file changed during merge; retry")
        os.replace(write_temp, path)
        write_temp = None
    finally:
        for leftover in (backup_temp, write_temp):
            if leftover is not None:
                try:
                    leftover.unlink()
                except FileNotFoundError:
                    pass


def codex_config_hooks(config: Path) -> str | None:
    """Why ``config.toml`` holds Codex hook definitions, or None when it holds none.

    Any key under the ``hooks`` table other than ``state`` is a definition (an event
    list today).  ``hooks.state`` holds the /hooks trust records Codex writes itself.
    """
    try:
        raw = config.read_bytes()
    except FileNotFoundError:
        return None
    try:
        document = tomllib.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise SettingsError(f"{config} is not valid TOML ({exc})") from None
    hooks = document.get("hooks")
    if hooks is None:
        return None
    if not isinstance(hooks, dict):
        return f"{config} defines hooks"
    defined = sorted(key for key in hooks if key != "state")
    if defined:
        return f"{config} defines hooks ({', '.join(defined)})"
    return None


def change(
    action: str,
    path: Path,
    event: str,
    companion_path: Path,
    entry: dict[str, Any],
    codex_config: Path | None = None,
) -> dict[str, Any]:
    if codex_config is not None and action in ("inspect", "install"):
        conflict = codex_config_hooks(codex_config)
        if conflict is not None:
            return {
                "status": "layer-conflict",
                "reason": conflict + "; Codex hooks stay in one layer, so "
                + path.name + " was not changed",
            }
    raw, text = _read(path)
    settings = _decode(text)
    groups = _event_groups(settings, event)
    if action == "inspect":
        if any(_is_current(group, companion_path, entry) for group in groups):
            return {"status": "current"}
        if any(_is_collision(group, companion_path, entry) for group in groups):
            return {"status": "collision", "reason": f"hand-registered {companion_path.name} entry"}
        return {"status": "missing"}
    if action == "install":
        if any(_is_current(group, companion_path, entry) for group in groups):
            return {"status": "current"}
        if any(_is_collision(group, companion_path, entry) for group in groups):
            return {"status": "collision", "reason": f"hand-registered {companion_path.name} entry"}
        merged = _append(text, event, entry)
        _decode(merged)
        _write(path, raw, merged)
        return {"status": "installed"}
    exact_count = _current_count(groups, companion_path, entry)
    if exact_count > 1:
        return {
            "status": "collision",
            "reason": f"multiple exact {companion_path.name} entries",
        }
    text, removed, moved = _remove_one(text, event, companion_path, entry)
    if not removed:
        if any(_is_collision(group, companion_path, entry) for group in groups):
            return {
                "status": "collision",
                "reason": f"modified {companion_path.name} entry",
            }
        return {"status": "absent"}
    _decode(text)
    _write(path, raw, text)
    return {"status": "removed", "moved": moved}


def hook_command(host: str, command: str, timeout: int) -> dict[str, Any]:
    """The one owned command entry, in the host's own hook schema.

    Both hosts read ``type``/``command``/``timeout`` (seconds).  ``onFailure`` is a
    Claude field; the Codex entry carries only the fields Codex documents.
    """
    item: dict[str, Any] = {"type": "command", "command": command, "timeout": timeout}
    if host == "claude":
        item["onFailure"] = "continue"
    return item


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("inspect", "install", "remove"))
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--matcher", required=True)
    parser.add_argument("--timeout", type=int, required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--companion-path", type=Path, required=True)
    parser.add_argument("--host", choices=("claude", "codex"), default="claude")
    parser.add_argument("--codex-config", type=Path, default=None)
    args = parser.parse_args()
    entry = {
        "matcher": args.matcher,
        "hooks": [hook_command(args.host, args.command, args.timeout)],
    }
    try:
        result = change(
            args.action, args.settings, args.event, args.companion_path, entry,
            codex_config=args.codex_config,
        )
    except (OSError, SettingsError) as exc:
        print(json.dumps({"status": "invalid", "reason": str(exc)}))
        return 3
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
