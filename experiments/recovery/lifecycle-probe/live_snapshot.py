"""Bounded live-host tree snapshot for the disposable lifecycle probe."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import stat
import sys
import time
from typing import Any


SCHEMA = 1
REPARSE_POINT = 0x400
HMAC_DOMAIN = b"skill-mesh-live-snapshot-v1\0"


class SnapshotError(RuntimeError):
    pass


def _is_reparse(file_stat: os.stat_result) -> bool:
    return bool(getattr(file_stat, "st_file_attributes", 0) & REPARSE_POINT)


def _canonical(path: str) -> str:
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


def _is_unc(path: str) -> bool:
    return os.path.abspath(path).startswith("\\\\")


class Snapshot:
    def __init__(self, request: dict[str, Any]) -> None:
        if request.get("schema") != SCHEMA:
            raise SnapshotError("unsupported request schema")
        try:
            self.key = bytes.fromhex(request["hmac_key_hex"])
        except (KeyError, TypeError, ValueError) as error:
            raise SnapshotError("invalid secret-comparison key") from error
        if len(self.key) != 32:
            raise SnapshotError("secret-comparison key must contain 32 bytes")
        timeout = int(request.get("deadline_seconds", 120))
        self.deadline = time.monotonic() + timeout
        self.max_records = int(request.get("max_records", 100_000))
        self.records: list[dict[str, Any]] = []
        self.visited: set[str] = set()
        self.secret_paths = {_canonical(path) for path in request.get("secret_paths", [])}
        self.allowed_reparse_roots = {
            _canonical(path) for path in request.get("allowed_reparse_roots", [])
        }

    def check_budget(self) -> None:
        if time.monotonic() > self.deadline:
            raise SnapshotError("snapshot deadline exceeded")
        if len(self.records) >= self.max_records:
            raise SnapshotError("snapshot record limit exceeded")

    def add(self, record: dict[str, Any]) -> None:
        self.check_budget()
        self.records.append(record)

    def file_record(self, label: str, path: str, file_stat: os.stat_result) -> None:
        canonical = _canonical(path)
        secret = canonical in self.secret_paths
        digest = hmac.new(self.key, HMAC_DOMAIN, hashlib.sha256) if secret else hashlib.sha256()
        remaining = file_stat.st_size
        with open(path, "rb", buffering=0) as stream:
            while remaining:
                self.check_budget()
                chunk = stream.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise SnapshotError("file ended during snapshot")
                digest.update(chunk)
                remaining -= len(chunk)
            final_stat = os.fstat(stream.fileno())
        if (final_stat.st_dev, final_stat.st_ino) != (file_stat.st_dev, file_stat.st_ino):
            raise SnapshotError("file identity changed during snapshot")
        if final_stat.st_size < file_stat.st_size:
            raise SnapshotError("file shrank during snapshot")
        if final_stat.st_size == file_stat.st_size and final_stat.st_mtime_ns != file_stat.st_mtime_ns:
            raise SnapshotError("file changed during snapshot")
        grew_during_read = final_stat.st_size > file_stat.st_size
        self.add(
            {
                "path": label,
                "kind": "FILE",
                "length": file_stat.st_size,
                "final_length": final_stat.st_size,
                "grew_during_read": grew_during_read,
                "sha256": "" if secret else digest.hexdigest(),
                "secret_hmac": digest.hexdigest() if secret else "",
                "file_id": f"{file_stat.st_dev}:{file_stat.st_ino}",
                "physical_path": os.path.abspath(path),
                "secret": secret,
                "target": "",
            }
        )

    def scan(self, label: str, path: str) -> None:
        self.check_budget()
        absolute = os.path.abspath(path)
        try:
            item_stat = os.lstat(absolute)
        except FileNotFoundError:
            self.add(
                {
                    "path": label,
                    "kind": "MISSING",
                    "length": 0,
                    "final_length": 0,
                    "grew_during_read": False,
                    "sha256": "",
                    "secret_hmac": "",
                    "file_id": "",
                    "physical_path": "",
                    "secret": False,
                    "target": "",
                }
            )
            return

        if _is_reparse(item_stat):
            target = _canonical(absolute)
            if _is_unc(target):
                raise SnapshotError("network reparse target is not permitted")
            if not any(
                os.path.commonpath((target, allowed)) == allowed
                for allowed in self.allowed_reparse_roots
            ):
                raise SnapshotError("reparse target is outside the approved local roots")
            self.add(
                {
                    "path": label,
                    "kind": "REPARSE",
                    "length": 0,
                    "final_length": 0,
                    "grew_during_read": False,
                    "sha256": hashlib.sha256(target.encode("utf-8")).hexdigest(),
                    "secret_hmac": "",
                    "file_id": "",
                    "physical_path": absolute,
                    "secret": False,
                    "target": target,
                }
            )
            if target not in self.visited:
                self.scan(f"{label}@target", target)
            return

        if stat.S_ISREG(item_stat.st_mode):
            self.file_record(label, absolute, item_stat)
            return
        if not stat.S_ISDIR(item_stat.st_mode):
            raise SnapshotError("unsupported live-root entry type")

        canonical = _canonical(absolute)
        if canonical in self.visited:
            return
        self.visited.add(canonical)
        self.add(
            {
                "path": label,
                "kind": "DIR",
                "length": 0,
                "final_length": 0,
                "grew_during_read": False,
                "sha256": "",
                "secret_hmac": "",
                "file_id": "",
                "physical_path": absolute,
                "secret": False,
                "target": "",
            }
        )
        with os.scandir(absolute) as entries:
            for entry in sorted(entries, key=lambda value: os.path.normcase(value.name)):
                self.scan(f"{label}/{entry.name}", entry.path)


def main() -> int:
    try:
        request = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        started = time.monotonic()
        snapshot = Snapshot(request)
        roots = request.get("roots")
        if not isinstance(roots, list) or not roots:
            raise SnapshotError("at least one root is required")
        for root in roots:
            snapshot.scan(str(root["label"]), str(root["path"]))
        payload = {
            "schema": SCHEMA,
            "status": "COMPLETE",
            "duration_seconds": round(time.monotonic() - started, 3),
            "records": sorted(snapshot.records, key=lambda value: value["path"]),
        }
        json.dump(payload, sys.stdout, ensure_ascii=True, separators=(",", ":"))
        sys.stdout.write("\n")
        return 0
    except Exception as error:  # fail closed at the process boundary
        print(f"snapshot failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
