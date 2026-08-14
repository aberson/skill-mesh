"""Create-new evidence helpers for the Goal A cross-family experiment."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping


MAX_EVIDENCE_FILE_BYTES = 16 * 1024 * 1024
TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


class EvidenceError(RuntimeError):
    """Raised when evidence cannot be created without ambiguity."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    before = path.stat()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        after = os.fstat(stream.fileno())
    if (
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    ):
        raise EvidenceError(f"evidence file changed while hashing: {path.name}")
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def read_bounded(path: Path, maximum: int = MAX_EVIDENCE_FILE_BYTES) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise EvidenceError(f"evidence input is not one regular file: {path.name}")
    size = path.stat().st_size
    if size > maximum:
        raise EvidenceError(f"evidence input exceeds {maximum} bytes: {path.name}")
    payload = path.read_bytes()
    if len(payload) != size:
        raise EvidenceError(f"evidence input changed while being read: {path.name}")
    return payload


def write_new(
    path: Path,
    payload: bytes,
    *,
    maximum: int = MAX_EVIDENCE_FILE_BYTES,
) -> None:
    if type(maximum) is not int or maximum <= 0:
        raise EvidenceError("evidence output bound is invalid")
    if len(payload) > maximum:
        raise EvidenceError(f"evidence output exceeds the size bound: {path.name}")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise EvidenceError(f"evidence parent is not one regular directory: {path.parent}")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)


def redact_text(
    value: str,
    replacements: Mapping[str, str],
    *,
    maximum: int = 8000,
) -> str:
    """Redact private absolute locators and bound provider-controlled prose."""

    if type(value) is not str:
        raise EvidenceError("redaction input must be text")
    result = value.replace("\r\n", "\n").replace("\r", "\n")
    for private, public in sorted(
        replacements.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if private:
            result = re.sub(re.escape(private), lambda _: public, result, flags=re.IGNORECASE)
    result = "".join(character if character in "\n\t" or ord(character) >= 32 else "?" for character in result)
    if len(result) > maximum:
        result = result[:maximum] + "\n<TRUNCATED>"
    return result


def json_display(value: Any) -> str:
    return "```json\n" + json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n```"


def table_display(value: Any) -> str:
    """Return one Markdown-table-safe JSON scalar or compact structure."""

    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return rendered.replace("|", "\\|").replace("\n", " ")


def render_template(template: str, values: Mapping[str, str]) -> str:
    tokens = TOKEN_RE.findall(template)
    token_set = set(tokens)
    if len(tokens) != len(token_set):
        raise EvidenceError("report template repeats a placeholder")
    if token_set != set(values):
        missing = sorted(token_set - set(values))
        extra = sorted(set(values) - token_set)
        raise EvidenceError(f"report values do not match template: missing={missing}; extra={extra}")
    rendered = template
    for token in tokens:
        value = values[token]
        if type(value) is not str:
            raise EvidenceError(f"report value {token} must be text")
        rendered = rendered.replace("{{" + token + "}}", value)
    if TOKEN_RE.search(rendered) or "{{" in rendered:
        raise EvidenceError("report contains an unresolved placeholder")
    encoded = rendered.encode("utf-8")
    if len(encoded) > MAX_EVIDENCE_FILE_BYTES:
        raise EvidenceError("rendered report exceeds the evidence size bound")
    return rendered


def write_manifest(root: Path, manifest_path: Path) -> list[dict[str, Any]]:
    """Hash every retained regular file except the create-new manifest itself."""

    if manifest_path.parent != root:
        raise EvidenceError("manifest must be at the evidence root")
    if manifest_path.exists():
        raise EvidenceError("manifest already exists")
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if path == manifest_path or path.is_dir():
            continue
        if path.is_symlink() or not path.is_file():
            raise EvidenceError("evidence tree contains a linked or unsupported entry")
        relative = path.relative_to(root).as_posix()
        if "\n" in relative or "\r" in relative:
            raise EvidenceError("evidence path contains a line break")
        entries.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    lines = [f"{entry['sha256']}  {entry['path']}" for entry in entries]
    write_new(manifest_path, ("\n".join(lines) + "\n").encode("utf-8"))
    return entries
