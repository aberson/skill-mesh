#!/usr/bin/env python3
"""Single source of truth for the build-step -> build-phase verdict contract.

`/build-phase` creates a private run id and durable verdict path outside the
developer worktree, then starts this module's `--service` mode in a caller-scoped
parent execution session. The service generates and retains the HMAC key in opaque
parent state; `/build-phase` passes only the verdict path and run id to `/build-step`. The build-step
orchestrator atomically writes that sidecar on every terminal path by sending a strict
JSON-lines request to the parent service;
the path, run id, and key are never passed to developer or reviewer children. A child
with shared filesystem tools might discover or alter the sidecar, but unauthenticated,
missing, or malformed bytes fail closed and cannot authorize advancement.
`/build-phase` §2c ("Capture result")
reads it with the expected run id/key and decides whether to ADVANCE to the next step
or treat the step as BLOCKED. This module is the ONE place the emit/consume rule
lives so the SKILL.md prose and the test suite cannot drift apart (per
`dev/.claude/rules/code-quality.md` -- "one source of truth for data-shape
constants" / "grep all downstream consumers when changing a key/id shape").

Pure stdlib (json, pathlib). No LLM, no third-party deps. `--service` is the
non-executable request boundary used by capable Codex hosts; direct imports remain
the library API used by other hosts and tests.

verdict.json schema
-------------------
::

    {
      "schema_version": 2,
      "timestamp": str,                  # ISO-8601, when build-step wrote the verdict
      "run_id":    str,                  # parent-minted opaque invocation identity
      "writer":    "build-step-orchestrator",
      "result":    "PASS" | "NEEDS-WORK" | "DEFERRED-TO-UAT",
      "halt":      "POST_MERGE_HALT" | "SHIP_GATE_HALT" | null,
      "summary":   str,                  # one-line human-readable rationale
      "signature": str                   # HMAC-SHA256 over every prior field
    }

The `result` enum MIRRORS (but does NOT import or adopt) review-deep's
`aggregate.py` `aggregated_verdict.result` enum (PASS | NEEDS-WORK |
DEFERRED-TO-UAT). build-step emits DEFERRED-TO-UAT only on the `--reviewers
deep` lane (review-deep's aggregated verdict passes through); the other lanes
never emit it. build-phase's consume rule handles it as an ADVANCE.

The `halt` field carries build-step's in-band BLOCKED sentinels (Step 7
normalization table) stripped of their trailing colon: `POST_MERGE_HALT:` ->
`"POST_MERGE_HALT"`, `SHIP_GATE_HALT:` -> `"SHIP_GATE_HALT"`. A non-null halt
means the merge mechanics / ship gate broke (NOT a developer-fix scenario) and
the orchestrator must surface it to the operator -- so any non-null halt forces
BLOCKED regardless of `result`.

Consume rule (DEFAULT-DENY / FAIL-CLOSED)
-----------------------------------------
`classify_verdict` returns exactly `"ADVANCE"` or `"BLOCKED"`. It NEVER raises;
anything it cannot positively confirm as a clean pass fails closed to
`"BLOCKED"` (== NEEDS-WORK). ADVANCE happens ONLY when the file exists, parses,
carries the expected run identity and orchestrator writer, carries a known
passing `result`, AND has no halt.
"""

from __future__ import annotations

import json
import hashlib
import hmac
import math
import os
import secrets
import sys
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

# The two literal results classify_verdict / build-phase distinguish.
ADVANCE = "ADVANCE"
BLOCKED = "BLOCKED"

# Schema enums (single source of truth; mirrored in both SKILL.md docs).
VALID_RESULTS = {"PASS", "NEEDS-WORK", "DEFERRED-TO-UAT"}
VALID_HALTS = {"POST_MERGE_HALT", "SHIP_GATE_HALT"}

# Results that clear the gate (when halt is null). NEEDS-WORK is intentionally
# excluded: it is the explicit "developer must iterate" signal.
ADVANCING_RESULTS = {"PASS", "DEFERRED-TO-UAT"}
SCHEMA_VERSION = 2
ORCHESTRATOR_WRITER = "build-step-orchestrator"
SIGNED_FIELDS = (
    "schema_version",
    "timestamp",
    "run_id",
    "writer",
    "result",
    "halt",
    "summary",
)

# Parent-only JSON-lines service.  The service owns the HMAC key inside its
# process and accepts data-only requests; callers never interpolate request
# values into Python source.  The host adapter separately proves that the
# process/session handle is caller-scoped to the parent orchestration context.
SERVICE_SCHEMA = "skill-mesh/build-step-verdict-service/v1"
SERVICE_MAX_REQUEST_BYTES = 4096
SERVICE_MAX_SUMMARY_CHARS = 512
SERVICE_REQUEST_KEYS = {
    "open": {"op", "verdict_path", "run_id"},
    "write": {"op", "terminal", "halt", "summary"},
    "classify": {"op"},
    "cleanup": {"op"},
    "close": {"op"},
    "export": {
        "op", "destination", "schema", "attempt_id", "submission_id",
        "verdict_run_id", "classification", "result", "plan_path",
        "approved_input_plan_sha256", "checkpoint_plan_sha256", "item_id",
        "baseline_checkpoint", "accepted_checkpoint", "candidate_source",
        "installed_skills_sha256", "suite_evidence", "review_evidence",
        "landed_paths_locator", "native_session_id", "observed_model",
    },
}
MCP_SCHEMA = "skill-mesh/forge-verdict-mcp/v1"
MCP_TOOL_NAME = "verdict"
MCP_PROTOCOL_VERSION = "2025-06-18"
MCP_MAX_JSON_NESTING = 512
MCP_REQUEST_METHODS = {"initialize", "ping", "tools/list", "tools/call"}
MCP_NOTIFICATION_METHODS = {"notifications/initialized", "notifications/cancelled"}
MCP_REQUEST_PARAM_FIELDS = {
    "initialize": {"protocolVersion", "capabilities", "clientInfo"},
    "ping": set(),
    "tools/list": {"cursor"},
    "tools/call": {"name", "arguments"},
}
MCP_NOTIFICATION_PARAM_FIELDS = {
    "notifications/initialized": set(),
    "notifications/cancelled": {"requestId", "reason"},
}
ACCEPTANCE_SCHEMA = "swarm-forge/parent-acceptance-v1"
_HEX64 = set("0123456789abcdef")


def _secret_bytes(secret: str) -> bytes:
    if not isinstance(secret, str):
        raise ValueError("verdict secret must be a 64-character hex string")
    try:
        value = bytes.fromhex(secret)
    except ValueError as exc:
        raise ValueError("verdict secret must be a 64-character hex string") from exc
    if len(value) != 32:
        raise ValueError("verdict secret must encode exactly 32 bytes")
    return value


def _signature(payload: dict[str, Any], secret: str) -> str:
    signed = {field: payload[field] for field in SIGNED_FIELDS}
    message = json.dumps(
        signed,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=True,
    ).encode("ascii")
    return hmac.new(_secret_bytes(secret), message, hashlib.sha256).hexdigest()


def classify_verdict(
    verdict_path: str | Path,
    *,
    expected_run_id: str | None = None,
    expected_secret: str | None = None,
) -> str:
    """Apply the default-deny consume rule to a verdict.json file.

    Returns the literal string ``"ADVANCE"`` or ``"BLOCKED"`` -- never raises.

    Fail-closed decision ladder (first match wins):

    * file missing / unreadable / not valid JSON / not a JSON object -> BLOCKED
    * expected identity set and schema/writer/run id/signature mismatch -> BLOCKED
    * ``halt`` present and non-null (any value)                          -> BLOCKED
    * ``result`` not in :data:`VALID_RESULTS` (unknown / missing)        -> BLOCKED
    * ``result`` == ``"NEEDS-WORK"``                                     -> BLOCKED
    * ``result`` in {PASS, DEFERRED-TO-UAT} AND ``halt`` is null         -> ADVANCE

    ``expected_run_id`` and ``expected_secret`` are an all-or-none pair for the
    authenticated v2 channel. Accepts a ``str`` path or a
    :class:`pathlib.Path`.
    """
    path = Path(verdict_path)

    # --- File-level fail-closed: missing / unreadable / malformed JSON ---
    try:
        # utf-8-sig transparently strips a leading BOM (build-step's verdict.json
        # is often written via PowerShell, which emits one) and is identical to
        # utf-8 when no BOM is present -- without it, json.loads would reject the
        # BOM and FALSE-BLOCK an otherwise-valid PASS verdict.
        raw = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        # Missing file, permission error, is-a-directory, or bytes that are
        # not valid UTF-8/UTF-8-BOM (UnicodeDecodeError is a ValueError, NOT
        # an OSError -- without this clause a garbled-encoding verdict.json
        # would raise instead of failing closed).
        return BLOCKED
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        # Empty file, truncated/malformed JSON.
        return BLOCKED
    if not isinstance(data, dict):
        # A bare list / string / number is not a verdict object.
        return BLOCKED

    # --- invocation identity: parent-minted path + run id, fail closed ---
    if expected_run_id is not None or expected_secret is not None:
        if not isinstance(expected_run_id, str) or not expected_run_id:
            return BLOCKED
        if not isinstance(expected_secret, str):
            return BLOCKED
        if data.get("schema_version") != SCHEMA_VERSION:
            return BLOCKED
        if data.get("writer") != ORCHESTRATOR_WRITER:
            return BLOCKED
        if data.get("run_id") != expected_run_id:
            return BLOCKED
        expected_fields = set(SIGNED_FIELDS) | {"signature"}
        if set(data) != expected_fields:
            return BLOCKED
        signature = data.get("signature")
        if (
            not isinstance(signature, str)
            or len(signature) != 64
            or any(char not in "0123456789abcdef" for char in signature)
        ):
            return BLOCKED
        try:
            computed = _signature(data, expected_secret)
        except (KeyError, TypeError, ValueError):
            return BLOCKED
        if not hmac.compare_digest(signature, computed):
            return BLOCKED

    # --- halt fail-closed: any non-null halt blocks (regardless of result) ---
    halt = data.get("halt")
    if halt is not None:
        # Any non-null halt (valid or not) forces BLOCKED -- fail closed at
        # CONSUME time. Halt-sentinel validation lives at EMIT time in
        # translate_build_step_verdict, not here.
        return BLOCKED

    # --- result fail-closed: unknown / missing / non-string -> BLOCKED ---
    result = data.get("result")
    if not isinstance(result, str):
        # A non-string result (list/object/number) must fail closed; an
        # unhashable value would raise TypeError on the set-membership check.
        return BLOCKED
    if result not in VALID_RESULTS:
        return BLOCKED
    if result == "NEEDS-WORK":
        return BLOCKED

    # result in {PASS, DEFERRED-TO-UAT} and halt is null.
    return ADVANCE


def translate_build_step_verdict(
    terminal: str | None,
    halt: str | None = None,
    summary: str = "",
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Translate build-step's Step 7 terminal strings into a verdict.json dict.

    This encodes the EMIT-side translator (the thin mapping documented in
    build-step SKILL.md Step 7). It is a translation, NOT adoption of
    review-deep's aggregate.py.

    Terminal-string -> ``result`` mapping:

    * ``"PASS"``      / ``"APPROVED"``  -> ``"PASS"``
    * ``"NEEDS WORK"`` (a SPACE) / ``"REJECTED"`` -> ``"NEEDS-WORK"`` (a HYPHEN)
    * ``"DEFERRED-TO-UAT"`` (emitted only by the ``--reviewers deep`` lane,
      passing review-deep's aggregated verdict through) passes through unchanged.

    ``halt`` is carried through after validation: a non-null halt that is not in
    :data:`VALID_HALTS` raises ``ValueError`` (caught at EMIT time, not at
    consume time -- the consumer's job is to fail closed, the producer's job is
    to emit a well-formed sentinel).

    When ``run_id`` is supplied, the versioned invocation identity fields are
    included. A caller omitting it receives the legacy translation shape for
    compatibility with existing standalone users.

    Returns a dict missing only ``timestamp`` (the caller stamps that), e.g.::

        {"result": "PASS", "halt": None, "summary": "..."}
    """
    mapping = {
        "PASS": "PASS",
        "APPROVED": "PASS",
        "NEEDS WORK": "NEEDS-WORK",  # space -> hyphen
        "REJECTED": "NEEDS-WORK",
        "DEFERRED-TO-UAT": "DEFERRED-TO-UAT",
    }
    key = (terminal or "").strip()
    if key not in mapping:
        raise ValueError(
            f"unknown build-step terminal string {terminal!r}; "
            f"expected one of {sorted(mapping)}"
        )
    result = mapping[key]

    if halt is not None and halt not in VALID_HALTS:
        raise ValueError(
            f"unknown halt sentinel {halt!r}; expected one of {sorted(VALID_HALTS)} "
            f"or None"
        )

    payload: dict[str, Any] = {
        "result": result,
        "halt": halt,
        "summary": summary,
    }
    if run_id is not None:
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("run_id must be a non-empty string when supplied")
        payload = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "writer": ORCHESTRATOR_WRITER,
            **payload,
        }
    return payload


def write_verdict(
    verdict_path: str | Path,
    *,
    run_id: str,
    secret: str,
    terminal: str,
    halt: str | None = None,
    summary: str = "",
) -> dict[str, Any]:
    """Atomically write one final orchestrator-owned verdict.

    The target is replaced, never merged with existing content. This makes a
    stale or producer-planted file irrelevant: every terminal path must call
    this function, and the parent consumer also verifies ``run_id``.
    """
    path = Path(verdict_path)
    payload = translate_build_step_verdict(
        terminal,
        halt=halt,
        summary=summary,
        run_id=run_id,
    )
    payload["timestamp"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    payload["signature"] = _signature(payload, secret)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(payload, handle, separators=(",", ":"), ensure_ascii=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
    return payload


def _service_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build one JSON object while rejecting duplicate keys."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate service request key")
        result[key] = value
    return result


def _validate_service_request(request: Any) -> dict[str, Any]:
    """Validate the closed, non-executable service request vocabulary."""
    if not isinstance(request, dict):
        raise ValueError("service request must be an object")
    op = request.get("op")
    if not isinstance(op, str) or op not in SERVICE_REQUEST_KEYS:
        raise ValueError("unknown service operation")
    if set(request) != SERVICE_REQUEST_KEYS[op]:
        raise ValueError("service request fields do not match operation")

    if op == "open":
        path = request["verdict_path"]
        run_id = request["run_id"]
        if (
            not isinstance(path, str)
            or not path
            or "\x00" in path
            or not Path(path).is_absolute()
        ):
            raise ValueError("verdict_path must be a non-empty absolute path")
        if not isinstance(run_id, str) or not run_id or len(run_id) > 256:
            raise ValueError("run_id must be a non-empty bounded string")

    if op == "write":
        terminal = request["terminal"]
        halt = request["halt"]
        summary = request["summary"]
        if not isinstance(terminal, str) or not terminal:
            raise ValueError("terminal must be a non-empty string")
        if halt is not None and not isinstance(halt, str):
            raise ValueError("halt must be a string or null")
        if (
            not isinstance(summary, str)
            or len(summary) > SERVICE_MAX_SUMMARY_CHARS
            or any(ord(char) < 32 or ord(char) == 127 for char in summary)
        ):
            raise ValueError("summary must be one bounded printable line")

    if op == "export":
        if request["schema"] != ACCEPTANCE_SCHEMA:
            raise ValueError("unknown acceptance schema")
        destination = request["destination"]
        if not isinstance(destination, str) or not destination or "\x00" in destination or not Path(destination).is_absolute():
            raise ValueError("destination must be an absolute path")
        for field in ("attempt_id", "submission_id"):
            try:
                if str(uuid.UUID(request[field], version=4)) != request[field].lower():
                    raise ValueError("invalid UUID")
            except (AttributeError, TypeError, ValueError) as exc:
                raise ValueError("invalid UUID") from exc
        for field in ("approved_input_plan_sha256", "checkpoint_plan_sha256", "installed_skills_sha256"):
            value = request[field]
            if not isinstance(value, str) or len(value) != 64 or any(c not in _HEX64 for c in value):
                raise ValueError("invalid sha256")
        for field in ("baseline_checkpoint", "accepted_checkpoint"):
            value = request[field]
            if not isinstance(value, str) or len(value) != 40 or any(c not in _HEX64 for c in value):
                raise ValueError("invalid git checkpoint")
        if request["classification"] != ADVANCE or request["result"] != "PASS":
            raise ValueError("acceptance must be a literal PASS")
        for field in ("verdict_run_id", "plan_path", "item_id", "landed_paths_locator", "native_session_id", "observed_model"):
            value = request[field]
            if not isinstance(value, str) or not value or len(value) > 1024 or any(ord(c) < 32 for c in value):
                raise ValueError("invalid acceptance string")
        candidate = request["candidate_source"]
        if not isinstance(candidate, dict) or set(candidate) != {"head", "tree_sha256"}:
            raise ValueError("invalid candidate source")
        if not isinstance(candidate["head"], str) or len(candidate["head"]) != 40 or any(c not in _HEX64 for c in candidate["head"]):
            raise ValueError("invalid candidate head")
        if not isinstance(candidate["tree_sha256"], str) or len(candidate["tree_sha256"]) != 64 or any(c not in _HEX64 for c in candidate["tree_sha256"]):
            raise ValueError("invalid candidate tree hash")
        for field in ("suite_evidence", "review_evidence"):
            values = request[field]
            if not isinstance(values, list) or not values:
                raise ValueError("evidence must be a non-empty list")
            for item in values:
                if not isinstance(item, dict) or set(item) != {"name", "locator", "sha256"}:
                    raise ValueError("invalid evidence item")
                if not all(isinstance(item[k], str) and item[k] for k in ("name", "locator")):
                    raise ValueError("invalid evidence string")
                if (
                    not isinstance(item["sha256"], str)
                    or len(item["sha256"]) != 64
                    or any(c not in _HEX64 for c in item["sha256"])
                ):
                    raise ValueError("invalid evidence hash")

    return request


def decode_service_request(raw: str) -> dict[str, Any]:
    """Decode one strict JSON-lines request without accepting duplicate keys."""
    if not isinstance(raw, str) or not raw:
        raise ValueError("empty service request")
    if len(raw.encode("utf-8")) > SERVICE_MAX_REQUEST_BYTES:
        raise ValueError("service request exceeds byte limit")
    try:
        request = json.loads(raw, object_pairs_hook=_service_object)
    except (RecursionError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("invalid service request JSON") from exc
    return _validate_service_request(request)


class VerdictService:
    """One-channel parent service that rotates its process-internal key per open."""

    def __init__(
        self,
        *,
        secret_factory: Callable[[], str] | None = None,
    ) -> None:
        self.__secret_factory = secret_factory or (lambda: secrets.token_hex(32))
        self.__secret: str | None = None
        self._path: Path | None = None
        self._run_id: str | None = None

    def cleanup(self) -> None:
        path = self._path
        try:
            if path is not None:
                path.unlink()
        except FileNotFoundError:
            pass
        finally:
            # Destroy authorization state even when Windows or another host
            # refuses sidecar deletion.  The caller treats the cleanup error as
            # a halt, but a stale file must never keep a usable signing key live.
            self._path = None
            self._run_id = None
            self.__secret = None

    def _requires_channel(self) -> tuple[Path, str, str]:
        if self._path is None or self._run_id is None or self.__secret is None:
            raise ValueError("no open verdict channel")
        return self._path, self._run_id, self.__secret

    def handle(self, request: Any) -> tuple[dict[str, Any], bool]:
        """Handle one already-decoded request; return (response, should_close)."""
        try:
            request = _validate_service_request(request)
            op = request["op"]

            if op == "open":
                if self._path is not None:
                    raise ValueError("verdict channel already open")
                path = Path(request["verdict_path"])
                run_id = request["run_id"]
                secret = self.__secret_factory()
                _secret_bytes(secret)
                write_verdict(
                    path,
                    run_id=run_id,
                    secret=secret,
                    terminal="NEEDS WORK",
                    summary="run incomplete",
                )
                self._path = path
                self._run_id = run_id
                self.__secret = secret
                return {"ok": True, "op": "open"}, False

            if op == "write":
                path, run_id, secret = self._requires_channel()
                write_verdict(
                    path,
                    run_id=run_id,
                    secret=secret,
                    terminal=request["terminal"],
                    halt=request["halt"],
                    summary=request["summary"],
                )
                return {"ok": True, "op": "write"}, False

            if op == "classify":
                path, run_id, secret = self._requires_channel()
                classification = classify_verdict(
                    path,
                    expected_run_id=run_id,
                    expected_secret=secret,
                )
                return {
                    "ok": True,
                    "op": "classify",
                    "classification": classification,
                }, False

            if op == "export":
                path, run_id, secret = self._requires_channel()
                if request["verdict_run_id"] != run_id or classify_verdict(
                    path, expected_run_id=run_id, expected_secret=secret
                ) != ADVANCE:
                    raise ValueError("verdict is not authorized")
                # Correlate the exported result to the authenticated live
                # verdict too; ADVANCE alone intentionally merges two results.
                live = json.loads(path.read_text(encoding="utf-8-sig"))
                if (
                    not isinstance(live, dict)
                    or live.get("result") != request["result"]
                    or not hmac.compare_digest(live.get("signature", ""), _signature(live, secret))
                ):
                    raise ValueError("acceptance result does not match verdict")
                payload = {key: value for key, value in request.items() if key not in {"op", "destination"}}
                payload["exported_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
                destination = Path(request["destination"])
                destination.parent.mkdir(parents=True, exist_ok=True)
                encoded = (json.dumps(payload, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")
                receipt_sha256 = hashlib.sha256(encoded).hexdigest()
                temp_name: str | None = None
                try:
                    with tempfile.NamedTemporaryFile(mode="wb", dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp", delete=False) as handle:
                        temp_name = handle.name
                        handle.write(encoded)
                        handle.flush()
                        os.fsync(handle.fileno())
                    os.replace(temp_name, destination)
                    temp_name = None
                finally:
                    if temp_name is not None:
                        try:
                            os.unlink(temp_name)
                        except OSError:
                            pass
                return {
                    "ok": True,
                    "op": "export",
                    "attempt_id": request["attempt_id"],
                    "submission_id": request["submission_id"],
                    "verdict_run_id": run_id,
                    "destination": str(destination),
                    "receipt_sha256": receipt_sha256,
                }, False

            if op == "cleanup":
                self.cleanup()
                return {"ok": True, "op": "cleanup"}, False

            # The closed vocabulary makes this the only remaining operation.
            # Close always terminates the service, even if unlinking the
            # sidecar fails.  cleanup() has already destroyed the key/state.
            try:
                self.cleanup()
            except OSError:
                return {"ok": False, "error": "cleanup_failed"}, True
            return {"ok": True, "op": "close"}, True
        except (OSError, TypeError, ValueError):
            # Fail closed without reflecting request values, paths, or exception
            # text into the parent transcript.
            return {"ok": False, "error": "invalid_request"}, False


def _emit_service_response(stdout: Any, response: dict[str, Any]) -> None:
    stdout.write(json.dumps(response, separators=(",", ":"), ensure_ascii=True) + "\n")
    stdout.flush()


def serve_verdict_service(stdin: Any = None, stdout: Any = None) -> int:
    """Run the strict JSON-lines service; the HMAC key never leaves this call."""
    if stdin is None:
        stdin = sys.stdin
    if stdout is None:
        stdout = sys.stdout
    service = VerdictService()
    _emit_service_response(stdout, {"ok": True, "schema": SERVICE_SCHEMA})
    try:
        for raw in stdin:
            try:
                request = decode_service_request(raw.rstrip("\r\n"))
            except ValueError:
                _emit_service_response(stdout, {"ok": False, "error": "invalid_request"})
                continue
            response, should_close = service.handle(request)
            _emit_service_response(stdout, response)
            if should_close:
                return 0
    finally:
        service.cleanup()
    return 0


def _mcp_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _mcp_tool_schema() -> dict[str, Any]:
    """Describe the same closed operation vocabulary enforced by the service."""
    field_schemas: dict[str, dict[str, Any]] = {
        "op": {"type": "string"},
        "verdict_path": {"type": "string", "minLength": 1},
        "run_id": {"type": "string", "minLength": 1, "maxLength": 256},
        "terminal": {"type": "string", "minLength": 1},
        "halt": {"type": ["string", "null"]},
        "summary": {"type": "string", "maxLength": SERVICE_MAX_SUMMARY_CHARS},
        "destination": {"type": "string", "minLength": 1},
        "schema": {"const": ACCEPTANCE_SCHEMA},
        "attempt_id": {"type": "string", "format": "uuid"},
        "submission_id": {"type": "string", "format": "uuid"},
        "verdict_run_id": {"type": "string", "minLength": 1, "maxLength": 1024},
        "classification": {"const": ADVANCE},
        "result": {"const": "PASS"},
        "plan_path": {"type": "string", "minLength": 1, "maxLength": 1024},
        "approved_input_plan_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "checkpoint_plan_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "item_id": {"type": "string", "minLength": 1, "maxLength": 1024},
        "baseline_checkpoint": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
        "accepted_checkpoint": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
        "candidate_source": {
            "type": "object",
            "properties": {
                "head": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
                "tree_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            },
            "required": ["head", "tree_sha256"],
            "additionalProperties": False,
        },
        "installed_skills_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "landed_paths_locator": {"type": "string", "minLength": 1, "maxLength": 1024},
        "native_session_id": {"type": "string", "minLength": 1, "maxLength": 1024},
        "observed_model": {"type": "string", "minLength": 1, "maxLength": 1024},
    }
    evidence_schema = {
        "type": "array",
        "minItems": 1,
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "locator": {"type": "string", "minLength": 1},
                "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            },
            "required": ["locator", "name", "sha256"],
            "additionalProperties": False,
        },
    }
    field_schemas["suite_evidence"] = evidence_schema
    field_schemas["review_evidence"] = evidence_schema
    variants = []
    for op, fields in SERVICE_REQUEST_KEYS.items():
        properties = {field: field_schemas[field] for field in fields}
        properties["op"] = {"const": op}
        variants.append({
            "type": "object",
            "properties": properties,
            "required": sorted(fields),
            "additionalProperties": False,
        })
    return {"type": "object", "oneOf": variants}


def _classify_mcp_message(message: Any) -> tuple[str, Any, str | None, dict[str, Any] | None]:
    """Validate the JSON-RPC envelope before any stateful MCP dispatch."""
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return "error", None, None, None
    method = message.get("method")
    if not isinstance(method, str):
        return "error", None, None, None
    if "id" not in message:
        if not set(message) <= {"jsonrpc", "method", "params"}:
            return "ignore", None, method, None
        params = message.get("params", {})
        if not isinstance(params, dict):
            return "ignore", None, method, None
        if method in MCP_NOTIFICATION_METHODS:
            return "notification", None, method, params
        if method in MCP_REQUEST_METHODS:
            return "request_without_id", None, method, params
        return "ignore", None, method, params
    request_id = message["id"]
    if not _valid_request_id(request_id):
        return "error", None, None, None
    if not set(message) <= {"jsonrpc", "id", "method", "params"}:
        return "error", request_id, method, None
    params = message.get("params", {})
    if not isinstance(params, dict):
        return "error", request_id, method, None
    return "request", request_id, method, params


def _valid_initialize_params(params: dict[str, Any]) -> bool:
    client_info = params.get("clientInfo")
    capabilities = params.get("capabilities")
    return (
        set(params) == MCP_REQUEST_PARAM_FIELDS["initialize"]
        and isinstance(params.get("protocolVersion"), str)
        and bool(params["protocolVersion"])
        and _valid_client_capabilities(capabilities)
        and isinstance(client_info, dict)
        and isinstance(client_info.get("name"), str)
        and bool(client_info["name"])
        and isinstance(client_info.get("version"), str)
        and bool(client_info["version"])
        and ("title" not in client_info or isinstance(client_info["title"], str))
    )


def _valid_client_capabilities(capabilities: Any) -> bool:
    """Validate standardized capability shapes while retaining extensions."""
    if not isinstance(capabilities, dict):
        return False
    roots = capabilities.get("roots")
    if "roots" in capabilities and not isinstance(roots, dict):
        return False
    if isinstance(roots, dict) and (
        "listChanged" in roots and not isinstance(roots["listChanged"], bool)
    ):
        return False
    for name in ("sampling", "elicitation"):
        if name in capabilities and not isinstance(capabilities[name], dict):
            return False
    experimental = capabilities.get("experimental")
    if "experimental" in capabilities and (
        not isinstance(experimental, dict)
        or any(not isinstance(value, dict) for value in experimental.values())
    ):
        return False
    return True


def _protocol_params_without_meta(
    params: dict[str, Any], *, request: bool,
) -> dict[str, Any] | None:
    """Validate protocol metadata, then keep it outside method arguments."""
    if "_meta" not in params:
        return params
    metadata = params["_meta"]
    if not isinstance(metadata, dict):
        return None
    if request and "progressToken" in metadata:
        token = metadata["progressToken"]
        if not _valid_request_id(token):
            return None
    return {key: value for key, value in params.items() if key != "_meta"}


def _valid_request_id(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (str, int, float))
        and (not isinstance(value, float) or math.isfinite(value))
    )


def _valid_finite_json_values(value: Any) -> bool:
    pending = [(value, 0)]
    while pending:
        current, depth = pending.pop()
        if depth > MCP_MAX_JSON_NESTING:
            return False
        if isinstance(current, float):
            if not math.isfinite(current):
                return False
        elif isinstance(current, list):
            pending.extend((item, depth + 1) for item in current)
        elif isinstance(current, dict):
            pending.extend((item, depth + 1) for item in current.values())
    return True


def _reject_json_constant(value: str) -> None:
    raise json.JSONDecodeError("invalid JSON number", value, 0)


def _valid_mcp_notification(method: str, params: dict[str, Any], state: str) -> bool:
    """Accept only notifications valid for the current MCP lifecycle state."""
    if method not in MCP_NOTIFICATION_PARAM_FIELDS:
        return False
    if not set(params) <= MCP_NOTIFICATION_PARAM_FIELDS[method]:
        return False
    if method == "notifications/initialized":
        return state == "initialize_responded" and not params
    if method == "notifications/cancelled":
        request_id = params.get("requestId")
        return (
            state == "ready"
            and "requestId" in params
            and _valid_request_id(request_id)
            and ("reason" not in params or isinstance(params["reason"], str))
        )
    return False


def _valid_empty_method_params(params: dict[str, Any]) -> bool:
    return not params


def _valid_list_tools_params(params: dict[str, Any]) -> bool:
    return (
        set(params) <= MCP_REQUEST_PARAM_FIELDS["tools/list"]
        and ("cursor" not in params or isinstance(params["cursor"], str))
    )


def serve_mcp(stdin: Any = None, stdout: Any = None) -> int:
    """Serve a minimal newline-delimited stdio MCP facade over VerdictService."""
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    service = VerdictService()
    audit_seq = 0
    lifecycle = "new"
    try:
        for raw in stdin:
            request_id: Any = None
            raw = raw.rstrip("\r\n")
            if len(raw.encode("utf-8")) > SERVICE_MAX_REQUEST_BYTES:
                _emit_service_response(stdout, _mcp_error(None, -32600, "invalid request"))
                continue
            try:
                message = json.loads(
                    raw,
                    object_pairs_hook=_service_object,
                    parse_constant=_reject_json_constant,
                )
            except json.JSONDecodeError:
                _emit_service_response(stdout, _mcp_error(None, -32700, "parse error"))
                continue
            except (RecursionError, TypeError, ValueError):
                _emit_service_response(stdout, _mcp_error(None, -32600, "invalid request"))
                continue
            try:
                if not _valid_finite_json_values(message):
                    _emit_service_response(stdout, _mcp_error(None, -32600, "invalid request"))
                    continue
                kind, request_id, method, params = _classify_mcp_message(message)
                if kind == "error":
                    _emit_service_response(stdout, _mcp_error(request_id, -32600, "invalid request"))
                    continue
                if kind == "notification":
                    notification_params = _protocol_params_without_meta(
                        params, request=False,
                    )
                    if notification_params is not None and _valid_mcp_notification(
                        method, notification_params, lifecycle,
                    ) and method == "notifications/initialized":
                        lifecycle = "ready"
                    continue
                if kind in {"request_without_id", "ignore"}:
                    continue
                method_params = _protocol_params_without_meta(params, request=True)
                if method_params is None:
                    _emit_service_response(stdout, _mcp_error(request_id, -32602, "invalid method params"))
                    continue
                params = method_params
                if method == "initialize":
                    if lifecycle != "new" or not _valid_initialize_params(params):
                        _emit_service_response(stdout, _mcp_error(request_id, -32602, "invalid initialize params"))
                        continue
                    result = {"protocolVersion": MCP_PROTOCOL_VERSION, "capabilities": {"tools": {}}, "serverInfo": {"name": "forge-verdict", "version": "1"}}
                elif method == "ping" and lifecycle in {"initialize_responded", "ready"}:
                    if not _valid_empty_method_params(params):
                        _emit_service_response(stdout, _mcp_error(request_id, -32602, "invalid method params"))
                        continue
                    result = {}
                elif lifecycle != "ready":
                    _emit_service_response(stdout, _mcp_error(request_id, -32002, "server not initialized"))
                    continue
                elif method == "tools/list":
                    if not _valid_list_tools_params(params):
                        _emit_service_response(stdout, _mcp_error(request_id, -32602, "invalid method params"))
                        continue
                    result = {"tools": [{"name": MCP_TOOL_NAME, "description": "Parent-private build verdict operations", "inputSchema": _mcp_tool_schema()}]}
                elif method == "tools/call":
                    if (
                        "name" not in params
                        or not set(params) <= MCP_REQUEST_PARAM_FIELDS["tools/call"]
                        or params["name"] != MCP_TOOL_NAME
                    ):
                        _emit_service_response(stdout, _mcp_error(request_id, -32602, "invalid tool call"))
                        continue
                    try:
                        arguments = _validate_service_request(params.get("arguments"))
                    except (TypeError, ValueError):
                        _emit_service_response(stdout, _mcp_error(request_id, -32602, "invalid tool arguments"))
                        continue
                    response, should_close = service.handle(arguments)
                    audit_seq += 1
                    response["audit_seq"] = audit_seq
                    result = {"content": [{"type": "text", "text": json.dumps(response, separators=(",", ":"), ensure_ascii=True)}], "structuredContent": response, "isError": not response.get("ok", False)}
                else:
                    _emit_service_response(stdout, _mcp_error(request_id, -32601, "method not found"))
                    continue
                _emit_service_response(stdout, {"jsonrpc": "2.0", "id": request_id, "result": result})
                if method == "initialize":
                    lifecycle = "initialize_responded"
                if method == "tools/call" and should_close:
                    return 0
            except (TypeError, ValueError):
                _emit_service_response(stdout, _mcp_error(request_id, -32600, "invalid request"))
    finally:
        service.cleanup()
    return 0


def claude_parent_guard(expected_session_id: str, stdin: Any = None, stdout: Any = None) -> int:
    """Return a Claude PreToolUse permission decision; this function holds no key."""
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    allowed = False
    try:
        value = json.loads(stdin.read(), object_pairs_hook=_service_object)
        allowed = (
            isinstance(value, dict)
            and value.get("session_id") == expected_session_id
            and "agent_id" not in value
            and value.get("tool_name") == "mcp__forge_verdict__verdict"
        )
    except (TypeError, ValueError, json.JSONDecodeError):
        allowed = False
    decision = "allow" if allowed else "deny"
    payload = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision, "permissionDecisionReason": "parent session verified" if allowed else "parent session required"}}
    stdout.write(json.dumps(payload, separators=(",", ":"), ensure_ascii=True) + "\n")
    stdout.flush()
    return 0


def _main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv == ["--service"]:
        return serve_verdict_service()
    if argv == ["--mcp"]:
        return serve_mcp()
    if len(argv) == 2 and argv[0] == "--claude-parent-guard" and argv[1]:
        return claude_parent_guard(argv[1])
    print("usage: build_step_verdict.py (--service | --mcp | --claude-parent-guard SESSION_ID)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
