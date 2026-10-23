"""Unit tests for the build-step -> build-phase verdict contract.

Covers the default-deny / fail-closed consume rule in
`build_step_verdict.classify_verdict` over every documented case, the EMIT-side
`translate_build_step_verdict` terminal-string mapping, and a prose<->code
contract guard asserting build-step SKILL.md still documents the translator
table near a verdict.json mention.

Runs under pytest. Sibling import (same dir as the module under test), mirroring
test_score_skill_absolute.py.
"""

from __future__ import annotations

import json
import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

SECRET = "11" * 32
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Sibling import - same dir as the module under test.
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from build_step_verdict import (  # noqa: E402  (sys.path tweak above)
    ADVANCE,
    BLOCKED,
    MCP_MAX_JSON_NESTING,
    ORCHESTRATOR_WRITER,
    SCHEMA_VERSION,
    SERVICE_REQUEST_KEYS,
    SERVICE_SCHEMA,
    VerdictService,
    _mcp_tool_schema,
    claude_parent_guard,
    classify_verdict,
    decode_service_request,
    serve_mcp,
    serve_verdict_service,
    translate_build_step_verdict,
    write_verdict,
)


def _write_verdict(tmp_path: Path, payload: dict, *, name: str = "verdict.json") -> Path:
    """Write a recorded verdict.json fixture and return its path."""
    p = tmp_path / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# classify_verdict -- the default-deny consume rule
# ---------------------------------------------------------------------------


def test_needs_work_blocks(tmp_path):
    p = _write_verdict(
        tmp_path,
        {"timestamp": "2026-06-22T00:00:00", "result": "NEEDS-WORK", "halt": None, "summary": "x"},
    )
    assert classify_verdict(p) == BLOCKED


def test_post_merge_halt_blocks_even_with_pass_result(tmp_path):
    # halt forces BLOCKED regardless of result.
    p = _write_verdict(
        tmp_path,
        {"timestamp": "t", "result": "PASS", "halt": "POST_MERGE_HALT", "summary": "x"},
    )
    assert classify_verdict(p) == BLOCKED


def test_ship_gate_halt_blocks(tmp_path):
    p = _write_verdict(
        tmp_path,
        {"timestamp": "t", "result": "PASS", "halt": "SHIP_GATE_HALT", "summary": "x"},
    )
    assert classify_verdict(p) == BLOCKED


def test_pass_with_null_halt_advances(tmp_path):
    p = _write_verdict(
        tmp_path,
        {"timestamp": "t", "result": "PASS", "halt": None, "summary": "x"},
    )
    assert classify_verdict(p) == ADVANCE


def test_deferred_to_uat_with_null_halt_advances(tmp_path):
    p = _write_verdict(
        tmp_path,
        {"timestamp": "t", "result": "DEFERRED-TO-UAT", "halt": None, "summary": "x"},
    )
    assert classify_verdict(p) == ADVANCE


def test_expected_run_id_requires_versioned_orchestrator_identity(tmp_path):
    p = _write_verdict(
        tmp_path,
        {
            "schema_version": SCHEMA_VERSION,
            "timestamp": "t",
            "run_id": "run-123",
            "writer": ORCHESTRATOR_WRITER,
            "result": "PASS",
            "halt": None,
            "summary": "x",
        },
    )
    # Re-write through the authenticated writer; hand-built unsigned payloads fail.
    write_verdict(
        p,
        run_id="run-123",
        secret=SECRET,
        terminal="PASS",
        summary="x",
    )
    assert classify_verdict(
        p, expected_run_id="run-123", expected_secret=SECRET
    ) == ADVANCE
    assert classify_verdict(
        p, expected_run_id="other-run", expected_secret=SECRET
    ) == BLOCKED


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", 1),
        ("writer", "developer"),
        ("run_id", ""),
    ],
)
def test_expected_run_id_rejects_identity_tampering(tmp_path, field, value):
    payload = {
        "schema_version": SCHEMA_VERSION,
        "timestamp": "t",
        "run_id": "run-123",
        "writer": ORCHESTRATOR_WRITER,
        "result": "PASS",
        "halt": None,
        "summary": "x",
    }
    payload[field] = value
    p = _write_verdict(tmp_path, payload)
    assert classify_verdict(
        p, expected_run_id="run-123", expected_secret=SECRET
    ) == BLOCKED


def test_missing_file_blocks(tmp_path):
    p = tmp_path / "does_not_exist.json"
    assert classify_verdict(p) == BLOCKED


def test_malformed_truncated_json_blocks(tmp_path):
    p = tmp_path / "verdict.json"
    # Truncated mid-object -> json.loads raises -> fail closed.
    p.write_text('{"result": "PASS", "halt": nul', encoding="utf-8")
    assert classify_verdict(p) == BLOCKED


def test_unknown_result_string_blocks(tmp_path):
    p = _write_verdict(
        tmp_path,
        {"timestamp": "t", "result": "MAYBE", "halt": None, "summary": "x"},
    )
    assert classify_verdict(p) == BLOCKED


def test_empty_file_blocks(tmp_path):
    p = tmp_path / "verdict.json"
    p.write_text("", encoding="utf-8")
    assert classify_verdict(p) == BLOCKED


def test_missing_result_key_blocks(tmp_path):
    # result key absent entirely -> unknown -> BLOCKED.
    p = _write_verdict(tmp_path, {"timestamp": "t", "halt": None, "summary": "x"})
    assert classify_verdict(p) == BLOCKED


def test_unknown_halt_sentinel_blocks(tmp_path):
    # A non-null halt that is not a recognized sentinel still BLOCKED.
    p = _write_verdict(
        tmp_path,
        {"timestamp": "t", "result": "PASS", "halt": "BOGUS_HALT", "summary": "x"},
    )
    assert classify_verdict(p) == BLOCKED


def test_non_object_json_blocks(tmp_path):
    # A bare JSON list is valid JSON but not a verdict object.
    p = tmp_path / "verdict.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    assert classify_verdict(p) == BLOCKED


def test_accepts_str_path(tmp_path):
    # classify_verdict accepts a str path, not just a pathlib.Path.
    p = _write_verdict(
        tmp_path,
        {"timestamp": "t", "result": "PASS", "halt": None, "summary": "x"},
    )
    assert classify_verdict(str(p)) == ADVANCE


def test_bom_prefixed_valid_pass_advances(tmp_path):
    # PowerShell-written verdict.json carries a UTF-8 BOM; utf-8-sig must strip it
    # so a valid PASS still ADVANCEs (a plain utf-8 read would FALSE-BLOCK here).
    p = tmp_path / "verdict.json"
    p.write_text(
        json.dumps({"timestamp": "t", "result": "PASS", "halt": None, "summary": "x"}),
        encoding="utf-8-sig",  # prepends a BOM
    )
    assert classify_verdict(p) == ADVANCE


def test_result_value_null_blocks(tmp_path):
    # Explicit JSON null for result (not a missing key) -> unknown -> BLOCKED.
    p = _write_verdict(
        tmp_path,
        {"timestamp": "t", "result": None, "halt": None, "summary": "x"},
    )
    assert classify_verdict(p) == BLOCKED


def test_halt_empty_string_blocks(tmp_path):
    # Empty-string halt is non-null -> any non-null halt fails closed to BLOCKED.
    p = _write_verdict(
        tmp_path,
        {"timestamp": "t", "result": "PASS", "halt": "", "summary": "x"},
    )
    assert classify_verdict(p) == BLOCKED


def test_invalid_encoding_bytes_block(tmp_path):
    # Bytes that are not valid UTF-8/UTF-8-BOM must fail closed to BLOCKED,
    # not raise UnicodeDecodeError (a ValueError, NOT an OSError -- regression
    # for the too-narrow except clause). Windows writers garble encodings
    # routinely (windows-shell.md).
    p = tmp_path / "verdict.json"
    p.write_bytes(b'{"result": "PASS", "halt": null, "summary": "\xff\xfe bad"}')
    assert classify_verdict(p) == BLOCKED


def test_non_string_result_blocks(tmp_path):
    # A non-string result (list/object/number) must fail closed to BLOCKED,
    # not raise TypeError on the unhashable set-membership check.
    p = _write_verdict(
        tmp_path,
        {"timestamp": "t", "result": ["PASS"], "halt": None, "summary": "x"},
    )
    assert classify_verdict(p) == BLOCKED
    p2 = _write_verdict(
        tmp_path,
        {"timestamp": "t", "result": {"value": "PASS"}, "halt": None, "summary": "x"},
        name="verdict2.json",
    )
    assert classify_verdict(p2) == BLOCKED


# ---------------------------------------------------------------------------
# translate_build_step_verdict -- the EMIT-side terminal-string mapping
# ---------------------------------------------------------------------------


def test_translate_needs_work_space_to_hyphen():
    # build-step terminal "NEEDS WORK" (space) -> result "NEEDS-WORK" (hyphen).
    out = translate_build_step_verdict("NEEDS WORK")
    assert out["result"] == "NEEDS-WORK"


def test_translate_pass_to_pass():
    out = translate_build_step_verdict("PASS")
    assert out["result"] == "PASS"


def test_translate_approved_to_pass():
    assert translate_build_step_verdict("APPROVED")["result"] == "PASS"


def test_translate_rejected_to_needs_work():
    assert translate_build_step_verdict("REJECTED")["result"] == "NEEDS-WORK"


def test_translate_carries_valid_halt():
    out = translate_build_step_verdict("PASS", halt="POST_MERGE_HALT", summary="s")
    assert out["halt"] == "POST_MERGE_HALT"
    assert out["summary"] == "s"


def test_translate_rejects_unknown_terminal():
    with pytest.raises(ValueError):
        translate_build_step_verdict("MAYBE")


def test_translate_rejects_unknown_halt():
    with pytest.raises(ValueError):
        translate_build_step_verdict("PASS", halt="BOGUS_HALT")


def test_translate_rejects_none_terminal():
    # None terminal is not a known string -> ValueError (mirrors unknown-terminal).
    with pytest.raises(ValueError):
        translate_build_step_verdict(None)


def test_translate_deferred_to_uat_passthrough():
    out = translate_build_step_verdict("DEFERRED-TO-UAT")
    assert out["result"] == "DEFERRED-TO-UAT"


def test_translate_output_classifies_consistently(tmp_path):
    # Round-trip: translator output -> verdict.json -> classify_verdict.
    payload = translate_build_step_verdict("PASS")
    payload["timestamp"] = "t"
    p = _write_verdict(tmp_path, payload)
    assert classify_verdict(p) == ADVANCE

    payload2 = translate_build_step_verdict("NEEDS WORK")
    payload2["timestamp"] = "t"
    p2 = _write_verdict(tmp_path, payload2, name="verdict2.json")
    assert classify_verdict(p2) == BLOCKED


def test_translate_with_run_id_emits_versioned_identity():
    out = translate_build_step_verdict("PASS", run_id="run-123")
    assert out["schema_version"] == SCHEMA_VERSION
    assert out["run_id"] == "run-123"
    assert out["writer"] == ORCHESTRATOR_WRITER


def test_translate_rejects_empty_run_id():
    with pytest.raises(ValueError):
        translate_build_step_verdict("PASS", run_id="")


def test_write_verdict_atomically_overwrites_planted_pass(tmp_path):
    p = tmp_path / "durable" / "verdict.json"
    p.parent.mkdir()
    p.write_text(
        '{"result":"PASS","halt":null,"writer":"developer"}',
        encoding="utf-8",
    )
    payload = write_verdict(
        p,
        run_id="run-123",
        secret=SECRET,
        terminal="NEEDS WORK",
        summary="iteration limit exhausted",
    )
    assert payload["result"] == "NEEDS-WORK"
    assert classify_verdict(
        p, expected_run_id="run-123", expected_secret=SECRET
    ) == BLOCKED
    assert not list(p.parent.glob("*.tmp"))


def test_write_verdict_replaces_stale_pass_with_post_merge_halt(tmp_path):
    p = tmp_path / "verdict.json"
    write_verdict(
        p, run_id="run-123", secret=SECRET, terminal="PASS", summary="provisional"
    )
    write_verdict(
        p,
        run_id="run-123",
        secret=SECRET,
        terminal="NEEDS WORK",
        halt="POST_MERGE_HALT",
        summary="main-project tests failed",
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["halt"] == "POST_MERGE_HALT"
    assert classify_verdict(
        p, expected_run_id="run-123", expected_secret=SECRET
    ) == BLOCKED


def test_authenticated_verdict_rejects_payload_tampering(tmp_path):
    p = tmp_path / "verdict.json"
    write_verdict(
        p, run_id="run-123", secret=SECRET, terminal="PASS", summary="clean"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    data["summary"] = "developer changed this"
    p.write_text(json.dumps(data), encoding="utf-8")
    assert classify_verdict(
        p, expected_run_id="run-123", expected_secret=SECRET
    ) == BLOCKED


@pytest.mark.parametrize("signature", ["é" * 64, "A" * 64, "0" * 63, 123])
def test_authenticated_verdict_rejects_malformed_signature(tmp_path, signature):
    p = tmp_path / "verdict.json"
    write_verdict(
        p, run_id="run-123", secret=SECRET, terminal="PASS", summary="clean"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    data["signature"] = signature
    p.write_text(json.dumps(data), encoding="utf-8")
    assert classify_verdict(
        p, expected_run_id="run-123", expected_secret=SECRET
    ) == BLOCKED


@pytest.mark.parametrize("secret", ["", "aa", "not-hex", "11" * 31])
def test_write_verdict_rejects_invalid_secret(tmp_path, secret):
    with pytest.raises(ValueError):
        write_verdict(
            tmp_path / "verdict.json",
            run_id="run-123",
            secret=secret,
            terminal="PASS",
        )


# ---------------------------------------------------------------------------
# parent-only JSON-lines verdict service
# ---------------------------------------------------------------------------


def test_verdict_service_open_write_classify_tamper_and_cleanup(tmp_path):
    path = tmp_path / "service" / "verdict.json"
    service = VerdictService()

    opened, close = service.handle({
        "op": "open", "verdict_path": str(path), "run_id": "run-service",
    })
    assert opened == {"ok": True, "op": "open"}
    assert close is False
    assert service.handle({"op": "classify"})[0] == {
        "ok": True, "op": "classify", "classification": BLOCKED,
    }

    written, _ = service.handle({
        "op": "write",
        "terminal": "PASS",
        "halt": None,
        "summary": "all gates passed",
    })
    assert written == {"ok": True, "op": "write"}
    assert service.handle({"op": "classify"})[0]["classification"] == ADVANCE

    path.write_text("{}\n", encoding="utf-8")
    assert service.handle({"op": "classify"})[0]["classification"] == BLOCKED

    cleaned, _ = service.handle({"op": "cleanup"})
    assert cleaned == {"ok": True, "op": "cleanup"}
    assert not path.exists()


@pytest.mark.parametrize(
    "raw",
    [
        '{"op":"classify","op":"write"}',
        '{"op":"classify","extra":true}',
        '[]',
        'not-json',
        "x" * 4097,
    ],
)
def test_service_decoder_rejects_duplicate_extra_malformed_and_oversize(raw):
    with pytest.raises(ValueError):
        decode_service_request(raw)


def test_service_decoder_recursion_error_preserves_connection(monkeypatch):
    nesting = sys.getrecursionlimit() + 100
    overdeep = "[" * nesting + "0" + "]" * nesting
    stdin = io.StringIO(overdeep + '\n{"op":"cleanup"}\n')
    stdout = io.StringIO()
    original_loads = json.loads

    def decoder_with_depth_failure(raw, *args, **kwargs):
        if raw == overdeep:
            raise RecursionError("decoder nesting limit")
        return original_loads(raw, *args, **kwargs)

    with monkeypatch.context() as scoped:
        scoped.setattr(json, "loads", decoder_with_depth_failure)
        assert serve_verdict_service(stdin, stdout) == 0
    responses = [original_loads(line) for line in stdout.getvalue().splitlines()]
    assert responses == [
        {"ok": True, "schema": SERVICE_SCHEMA},
        {"ok": False, "error": "invalid_request"},
        {"ok": True, "op": "cleanup"},
    ]


@pytest.mark.parametrize(
    "service_request",
    [
        {"op": "open", "verdict_path": "relative.json", "run_id": "run"},
        {"op": "write", "terminal": "PASS", "halt": None, "summary": "line\nbreak"},
        {"op": "write", "terminal": "PASS", "halt": None, "summary": "x" * 513},
        {"op": "classify", "extra": "not allowed"},
        {"op": "unknown"},
    ],
)
def test_verdict_service_rejects_invalid_request_shapes(tmp_path, service_request):
    service = VerdictService()
    response, close = service.handle(service_request)
    assert response["ok"] is False
    assert set(response) == {"ok", "error"}
    assert close is False


def test_service_treats_summary_as_data_not_python(tmp_path):
    verdict_path = tmp_path / "verdict.json"
    injected_path = tmp_path / "injected.txt"
    summary = (
        '"; __import__("pathlib").Path('
        + repr(str(injected_path))
        + ').write_text("owned"); #'
    )
    service = VerdictService()
    assert service.handle({
        "op": "open", "verdict_path": str(verdict_path), "run_id": "run-injection",
    })[0]["ok"]
    assert service.handle({
        "op": "write", "terminal": "PASS", "halt": None, "summary": summary,
    })[0]["ok"]
    assert not injected_path.exists()
    assert json.loads(verdict_path.read_text(encoding="utf-8"))["summary"] == summary


def test_service_rotates_the_hmac_key_for_each_open_channel(tmp_path):
    first_secret = "11" * 32
    second_secret = "22" * 32
    secret_values = iter((first_secret, second_secret))
    service = VerdictService(secret_factory=lambda: next(secret_values))

    first_path = tmp_path / "first.json"
    assert service.handle({
        "op": "open", "verdict_path": str(first_path), "run_id": "run-first",
    })[0]["ok"]
    assert service.handle({
        "op": "write", "terminal": "PASS", "halt": None, "summary": "first",
    })[0]["ok"]
    assert classify_verdict(
        first_path, expected_run_id="run-first", expected_secret=first_secret,
    ) == ADVANCE
    assert service.handle({"op": "cleanup"})[0]["ok"]

    second_path = tmp_path / "second.json"
    assert service.handle({
        "op": "open", "verdict_path": str(second_path), "run_id": "run-second",
    })[0]["ok"]
    assert service.handle({
        "op": "write", "terminal": "PASS", "halt": None, "summary": "second",
    })[0]["ok"]
    assert classify_verdict(
        second_path, expected_run_id="run-second", expected_secret=first_secret,
    ) == BLOCKED
    assert classify_verdict(
        second_path, expected_run_id="run-second", expected_secret=second_secret,
    ) == ADVANCE


def test_unlink_failure_destroys_channel_state_and_cannot_keep_close_alive(
    tmp_path, monkeypatch,
):
    secrets = iter(("33" * 32, "44" * 32, "55" * 32))
    service = VerdictService(secret_factory=lambda: next(secrets))
    cleanup_path = tmp_path / "cleanup-failure.json"
    close_path = tmp_path / "close-failure.json"
    blocked_paths = {cleanup_path, close_path}
    original_unlink = Path.unlink

    def refuse_selected_unlinks(path, *args, **kwargs):
        if path in blocked_paths:
            raise PermissionError("planted sidecar lock")
        return original_unlink(path, *args, **kwargs)

    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "unlink", refuse_selected_unlinks)

        assert service.handle({
            "op": "open", "verdict_path": str(cleanup_path),
            "run_id": "run-cleanup-failure",
        })[0]["ok"]
        cleanup_response, cleanup_close = service.handle({"op": "cleanup"})
        assert cleanup_response == {"ok": False, "error": "invalid_request"}
        assert cleanup_close is False
        assert service.handle({"op": "classify"})[0]["ok"] is False

        # The failed unlink did not leave the old channel/key live: a new open
        # succeeds and therefore consumes a fresh secret.
        recovered_path = tmp_path / "recovered.json"
        assert service.handle({
            "op": "open", "verdict_path": str(recovered_path),
            "run_id": "run-recovered",
        })[0]["ok"]
        assert service.handle({"op": "cleanup"})[0]["ok"]

        assert service.handle({
            "op": "open", "verdict_path": str(close_path),
            "run_id": "run-close-failure",
        })[0]["ok"]
        close_response, should_close = service.handle({"op": "close"})
        assert close_response == {"ok": False, "error": "cleanup_failed"}
        assert should_close is True
        assert service.handle({"op": "classify"})[0]["ok"] is False

    # Simulate the parent's external best-effort cleanup after releasing a lock.
    cleanup_path.unlink()
    close_path.unlink()


def test_service_cli_is_strict_json_lines_and_emits_no_verdict_secret(tmp_path):
    verdict_path = tmp_path / "cli" / "verdict.json"
    process = subprocess.Popen(
        [sys.executable, str(THIS_DIR / "build_step_verdict.py"), "--service"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        creationflags=CREATE_NO_WINDOW,
    )
    requests = (
        {"op": "open", "verdict_path": str(verdict_path), "run_id": "run-cli"},
        {"op": "write", "terminal": "PASS", "halt": None, "summary": "clean"},
        {"op": "classify"},
        {"op": "close"},
    )
    request_stream = "".join(
        json.dumps(request, separators=(",", ":")) + "\n" for request in requests
    )
    try:
        stdout, stderr = process.communicate(input=request_stream, timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        pytest.fail("verdict service did not complete its bounded JSON-lines exchange")

    responses = [json.loads(line) for line in stdout.splitlines()]
    assert responses[0] == {"ok": True, "schema": SERVICE_SCHEMA}

    assert responses[-2]["classification"] == ADVANCE
    assert responses[-1] == {"ok": True, "op": "close"}
    assert process.returncode == 0
    assert stderr == ""
    assert not verdict_path.exists()
    rendered = json.dumps(responses, separators=(",", ":"))
    assert "signature" not in rendered
    assert "secret" not in rendered


def _acceptance_request(tmp_path, run_id="run-production"):
    # Generated fixture IDs cannot be mistaken for retained private session IDs.
    from uuid import uuid4

    return {
        "op": "export",
        "destination": str(tmp_path / "parent-acceptance.json"),
        "schema": "swarm-forge/parent-acceptance-v1",
        "attempt_id": str(uuid4()),
        "submission_id": str(uuid4()),
        "verdict_run_id": run_id,
        "classification": "ADVANCE",
        "result": "PASS",
        "plan_path": "docs/plans/master_plan.md",
        "approved_input_plan_sha256": "1" * 64,
        "checkpoint_plan_sha256": "2" * 64,
        "item_id": "Step 1",
        "baseline_checkpoint": "3" * 40,
        "accepted_checkpoint": "4" * 40,
        "candidate_source": {"head": "5" * 40, "tree_sha256": "6" * 64},
        "installed_skills_sha256": "7" * 64,
        "suite_evidence": [{"name": "pytest", "locator": "evidence/pytest.txt", "sha256": "8" * 64}],
        "review_evidence": [{"name": "review-deep", "locator": "evidence/review.json", "sha256": "9" * 64}],
        "landed_paths_locator": "archive/landed-paths.json",
        "native_session_id": str(uuid4()),
        "observed_model": "claude-opus-5-5",
    }


def _mcp_initialize(request_id=1, **overrides):
    params = {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1"},
    }
    params.update(overrides)
    return {"jsonrpc": "2.0", "id": request_id, "method": "initialize", "params": params}


def test_export_requires_live_advancing_channel_and_hashes_exact_receipt(tmp_path):
    service = VerdictService(secret_factory=lambda: SECRET)
    verdict_path = tmp_path / "verdict.json"
    export = _acceptance_request(tmp_path)
    assert service.handle({"op": "open", "verdict_path": str(verdict_path), "run_id": "run-production"})[0]["ok"]
    assert service.handle(export)[0] == {"ok": False, "error": "invalid_request"}
    assert service.handle({"op": "write", "terminal": "PASS", "halt": None, "summary": "accepted"})[0]["ok"]
    assert service.handle({
        "op": "write", "terminal": "DEFERRED-TO-UAT", "halt": None,
        "summary": "deferred",
    })[0]["ok"]
    deferred = {**export, "result": "DEFERRED-TO-UAT"}
    assert service.handle(deferred)[0] == {"ok": False, "error": "invalid_request"}
    assert not Path(export["destination"]).exists()
    assert service.handle({"op": "write", "terminal": "PASS", "halt": None, "summary": "accepted"})[0]["ok"]
    response, close = service.handle(export)
    assert close is False
    assert set(response) == {"ok", "op", "attempt_id", "submission_id", "verdict_run_id", "destination", "receipt_sha256"}
    receipt = Path(export["destination"])
    assert response["receipt_sha256"] == __import__("hashlib").sha256(receipt.read_bytes()).hexdigest()
    assert "signature" not in receipt.read_text(encoding="ascii")


def test_mcp_same_connection_cleanup_reopen_audit_and_final_close(tmp_path):
    verdict_one = tmp_path / "one.json"
    verdict_two = tmp_path / "two.json"
    calls = [
        {"op": "open", "verdict_path": str(verdict_one), "run_id": "canary"},
        {"op": "cleanup"},
        {"op": "open", "verdict_path": str(verdict_two), "run_id": "production"},
        {"op": "write", "terminal": "PASS", "halt": None, "summary": "accepted"},
        {"op": "classify"},
        {"op": "close"},
    ]
    messages = [
        _mcp_initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
    ]
    messages += [{"jsonrpc": "2.0", "id": i + 2, "method": "tools/call", "params": {"name": "verdict", "arguments": call}} for i, call in enumerate(calls)]
    process = subprocess.run(
        [sys.executable, str(THIS_DIR / "build_step_verdict.py"), "--mcp"],
        input="".join(json.dumps(item) + "\n" for item in messages),
        text=True, capture_output=True, timeout=10, check=False,
        creationflags=CREATE_NO_WINDOW,
    )
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    structured = [item["result"]["structuredContent"] for item in responses[1:]]
    assert [item["audit_seq"] for item in structured] == [1, 2, 3, 4, 5, 6]
    assert structured[-2]["classification"] == ADVANCE
    assert structured[-1] == {"ok": True, "op": "close", "audit_seq": 6}
    assert process.returncode == 0
    assert "signature" not in process.stdout and "secret" not in process.stdout


def test_mcp_protocol_initialize_ping_list_notifications_and_errors():
    stream = "not-json\n" + "".join(json.dumps(item) + "\n" for item in (
        {"jsonrpc": "2.0", "id": 1, "method": "unknown", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        _mcp_initialize(2),
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "ping", "params": {}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "verdict", "arguments": {"op": "close"}}},
    ))
    process = subprocess.run(
        [sys.executable, str(THIS_DIR / "build_step_verdict.py"), "--mcp"],
        input=stream, text=True, capture_output=True, timeout=10, check=False,
        creationflags=CREATE_NO_WINDOW,
    )
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert responses[0]["error"]["code"] == -32700
    assert responses[1]["error"]["code"] == -32002
    assert responses[2]["result"]["serverInfo"]["name"] == "forge-verdict"
    assert responses[3]["result"] == {}
    tool = responses[4]["result"]["tools"][0]
    assert tool["name"] == "verdict"
    assert tool["inputSchema"]["type"] == "object"
    assert all(variant["additionalProperties"] is False for variant in tool["inputSchema"]["oneOf"])
    assert responses[5]["result"]["structuredContent"]["audit_seq"] == 1


def test_mcp_rejects_bad_initialize_params_and_id_bearing_notification():
    messages = (
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": []}},
        {"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": []},
        _mcp_initialize(3),
        {"jsonrpc": "2.0", "id": 4, "method": "notifications/unknown", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "verdict", "arguments": {"op": "close"}}},
    )
    process = subprocess.run(
        [sys.executable, str(THIS_DIR / "build_step_verdict.py"), "--mcp"],
        input="".join(json.dumps(item) + "\n" for item in messages),
        text=True, capture_output=True, timeout=10, check=False,
        creationflags=CREATE_NO_WINDOW,
    )
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert [item.get("id") for item in responses] == [1, 2, 3, 4, 5]
    assert responses[0]["error"]["code"] == -32602
    assert responses[1]["error"]["code"] == -32600
    assert responses[2]["result"]["protocolVersion"] == "2025-06-18"
    assert responses[3]["error"]["code"] == -32002


def test_mcp_rejects_invalid_ids_and_idless_requests_without_audit():
    messages = (
        _mcp_initialize(),
        {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "verdict", "arguments": {"op": "classify"}}},
        {"jsonrpc": "2.0", "id": True, "method": "tools/call", "params": {"name": "verdict", "arguments": {"op": "classify"}}},
        {"jsonrpc": "2.0", "id": None, "method": "ping", "params": {}},
        {"jsonrpc": "2.0", "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "ping", "params": {}},
        {"jsonrpc": "2.0", "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "verdict", "arguments": {"op": "classify"}}},
    )
    process = subprocess.run(
        [sys.executable, str(THIS_DIR / "build_step_verdict.py"), "--mcp"],
        input="".join(json.dumps(item) + "\n" for item in messages),
        text=True, capture_output=True, timeout=10, check=False,
        creationflags=CREATE_NO_WINDOW,
    )
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert len(responses) == 4
    assert responses[0]["result"]["protocolVersion"] == "2025-06-18"
    assert responses[1]["error"]["code"] == -32600
    assert responses[2]["error"]["code"] == -32600
    assert responses[3]["result"]["structuredContent"]["audit_seq"] == 1


def test_mcp_schema_variants_are_derived_from_service_request_keys():
    schema = _mcp_tool_schema()
    assert schema["type"] == "object"
    variants = {
        variant["properties"]["op"]["const"]: variant
        for variant in schema["oneOf"]
    }
    assert set(variants) == set(SERVICE_REQUEST_KEYS)
    for op, fields in SERVICE_REQUEST_KEYS.items():
        variant = variants[op]
        assert set(variant["properties"]) == fields
        assert set(variant["required"]) == fields
        assert variant["additionalProperties"] is False
        assert all(variant["properties"][field] for field in fields)


def _mcp_exchange(*messages):
    stdin = io.StringIO("".join(
        item if isinstance(item, str) else json.dumps(item) + "\n"
        for item in messages
    ))
    stdout = io.StringIO()
    assert serve_mcp(stdin, stdout) == 0
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


@pytest.mark.parametrize(
    ("arguments", "path_name"),
    [
        (None, None),
        ({}, None),
        ({"op": "unknown"}, None),
        ({"op": "classify", "extra": True}, None),
        ({"op": "classify", "_meta": {"progressToken": "wrong-layer"}}, None),
        ({"op": "cleanup", "extra": True}, None),
        ({"op": "close", "extra": True}, None),
        ({"op": "open", "verdict_path": "relative.json", "run_id": "run"}, None),
        ({"op": "open", "verdict_path": "PATH", "run_id": ""}, "invalid-open.json"),
        ({"op": "write", "terminal": 1, "halt": None, "summary": "ok"}, None),
        ({"op": "write", "terminal": "PASS", "halt": 1, "summary": "ok"}, None),
        ({"op": "write", "terminal": "PASS", "halt": None, "summary": "line\nbreak"}, None),
    ],
)
def test_mcp_rejects_every_closed_operation_argument_shape_without_audit(
    tmp_path, arguments, path_name,
):
    if path_name:
        arguments = {**arguments, "verdict_path": str(tmp_path / path_name)}
    invalid_call = {
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "verdict", "arguments": arguments},
    }
    responses = _mcp_exchange(
        _mcp_initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        invalid_call,
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "verdict", "arguments": {"op": "classify"},
        }},
    )
    assert responses[1]["error"] == {"code": -32602, "message": "invalid tool arguments"}
    assert responses[2]["result"]["structuredContent"]["audit_seq"] == 1
    if path_name:
        assert not (tmp_path / path_name).exists()


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("destination", "relative.json"),
        ("schema", "wrong"),
        ("attempt_id", "wrong"),
        ("submission_id", "wrong"),
        ("verdict_run_id", ""),
        ("classification", "BLOCKED"),
        ("result", "DEFERRED-TO-UAT"),
        ("plan_path", ""),
        ("approved_input_plan_sha256", "x" * 64),
        ("checkpoint_plan_sha256", "x" * 64),
        ("item_id", ""),
        ("baseline_checkpoint", "x" * 40),
        ("accepted_checkpoint", "x" * 40),
        ("candidate_source", {"head": "5" * 40}),
        ("installed_skills_sha256", "x" * 64),
        ("suite_evidence", []),
        ("review_evidence", [{"name": "review", "locator": "e", "sha256": []}]),
        ("landed_paths_locator", ""),
        ("native_session_id", ""),
        ("observed_model", ""),
    ],
)
def test_mcp_rejects_each_export_argument_before_service_dispatch(
    tmp_path, field, invalid,
):
    arguments = _acceptance_request(tmp_path)
    arguments[field] = invalid
    responses = _mcp_exchange(
        _mcp_initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "verdict", "arguments": arguments,
        }},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "verdict", "arguments": {"op": "classify"},
        }},
    )
    assert responses[1]["error"]["code"] == -32602
    assert responses[2]["result"]["structuredContent"]["audit_seq"] == 1
    assert not Path(_acceptance_request(tmp_path)["destination"]).exists()


@pytest.mark.parametrize(
    ("message", "error_code"),
    [
        ({"jsonrpc": "1.0", "id": 2, "method": "ping", "params": {}}, -32600),
        ({"jsonrpc": "2.0", "id": True, "method": "ping", "params": {}}, -32600),
        ({"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {"extra": 1}}, -32602),
        ({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {"extra": 1}}, -32602),
        ({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "wrong", "arguments": {"op": "classify"}}}, -32602),
        ({"jsonrpc": "2.0", "id": 2, "method": "unknown", "params": {}}, -32601),
    ],
)
def test_mcp_malformed_envelope_method_and_tool_have_no_audit(message, error_code):
    responses = _mcp_exchange(
        _mcp_initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        message,
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "verdict", "arguments": {"op": "classify"},
        }},
    )
    assert responses[1]["error"]["code"] == error_code
    assert responses[2]["result"]["structuredContent"]["audit_seq"] == 1


def test_mcp_requires_initialized_notification_and_bounds_input_lines():
    oversized = json.dumps({
        "jsonrpc": "2.0", "id": 9, "method": "ping",
        "params": {"padding": "secret" * 800},
    }) + "\n"
    responses = _mcp_exchange(
        _mcp_initialize(),
        {"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {"bad": True}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        oversized,
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "verdict", "arguments": {"op": "classify"},
        }},
    )
    assert responses[1]["result"] == {}
    assert responses[2] == {
        "jsonrpc": "2.0", "id": None,
        "error": {"code": -32600, "message": "invalid request"},
    }
    assert "secret" not in json.dumps(responses[2])
    assert responses[3]["result"]["structuredContent"]["audit_seq"] == 1


@pytest.mark.parametrize("capabilities", [
    {"roots": []},
    {"roots": {"listChanged": "yes"}},
    {"sampling": []},
    {"elicitation": True},
    {"experimental": []},
    {"experimental": {"vendor.example/feature": []}},
])
def test_mcp_invalid_known_capability_shapes_do_not_initialize(capabilities):
    responses = _mcp_exchange(
        _mcp_initialize(1, capabilities=capabilities),
        _mcp_initialize(2),
    )
    assert responses[0]["error"] == {
        "code": -32602, "message": "invalid initialize params",
    }
    assert responses[1]["result"]["protocolVersion"] == "2025-06-18"


def test_mcp_negotiates_version_accepts_capability_extensions_and_gates_tools():
    capabilities = {
        "roots": {"listChanged": True, "vendorRootOption": {"enabled": True}},
        "sampling": {"vendorSamplingOption": "kept"},
        "elicitation": {},
        "experimental": {"vendor.example/feature": {"revision": 2}},
        "vendor.example/top-level": {"mode": "custom"},
    }
    initialize = _mcp_initialize(
        1,
        protocolVersion="2099-01-01",
        capabilities=capabilities,
        clientInfo={
            "name": "test-client", "title": "Test Client", "version": "1",
            "vendorClientOption": {"enabled": True},
        },
    )
    initialize["params"]["_meta"] = {
        "progressToken": "initialize-progress", "vendorMeta": {"trace": 1},
    }
    responses = _mcp_exchange(
        initialize,
        _mcp_initialize(2),
        {"jsonrpc": "2.0", "id": 3, "method": "ping", "params": {
            "_meta": {"progressToken": "ping-progress"},
        }},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {
            "name": "verdict", "arguments": {"op": "classify"},
            "_meta": {"progressToken": 7},
        }},
    )
    assert capabilities["vendor.example/top-level"] == {"mode": "custom"}
    assert responses[0]["result"]["protocolVersion"] == "2025-06-18"
    assert responses[1]["error"]["code"] == -32602
    assert responses[2]["result"] == {}
    assert responses[3]["error"]["code"] == -32002
    assert responses[4]["result"]["structuredContent"]["audit_seq"] == 1


def test_mcp_supported_protocol_surface_accepts_metadata_and_list_cursor():
    responses = _mcp_exchange(
        _mcp_initialize(),
        {"jsonrpc": "2.0", "id": 1.5, "method": "ping", "params": {
            "_meta": {"progressToken": 2.5, "vendorRequestMeta": True},
        }},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {
            "_meta": {
                "progressToken": {"notificationMetadataIsUnconstrained": True},
                "vendorNotificationMeta": [1, 2],
            },
        }},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {
            "cursor": "opaque-page", "_meta": {"progressToken": "list-progress"},
        }},
        {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {
            "requestId": 1.5, "reason": "late", "_meta": {"anything": {"goes": True}},
        }},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "verdict", "arguments": {"op": "classify"},
            "_meta": {"progressToken": "tool-progress"},
        }},
    )
    assert [response["id"] for response in responses] == [1, 1.5, 2, 3]
    assert responses[1]["result"] == {}
    assert responses[2]["result"]["tools"][0]["name"] == "verdict"
    assert responses[3]["result"]["structuredContent"]["audit_seq"] == 1


@pytest.mark.parametrize("metadata", [[], "bad", 1])
def test_mcp_malformed_initialized_notification_metadata_leaves_tools_gated(metadata):
    responses = _mcp_exchange(
        _mcp_initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {
            "_meta": metadata,
        }},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )
    assert responses[1]["error"]["code"] == -32002


@pytest.mark.parametrize("params", [
    {},
    {"requestId": True},
    {"requestId": []},
    {"requestId": 1, "reason": 2},
    {"requestId": 1, "extra": True},
    {"requestId": 1, "_meta": []},
])
def test_mcp_malformed_cancellation_notifications_are_silent_and_stateless(params):
    responses = _mcp_exchange(
        _mcp_initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": params},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "verdict", "arguments": {"op": "classify"},
        }},
    )
    assert len(responses) == 2
    assert responses[1]["result"]["structuredContent"]["audit_seq"] == 1


@pytest.mark.parametrize(
    ("wire", "error_code"),
    [
        ("not-json\n", -32700),
        ('{"jsonrpc":"2.0",\n', -32700),
        ('{"jsonrpc":"2.0","id":NaN,"method":"ping"}\n', -32700),
        ('{"jsonrpc":"2.0","id":Infinity,"method":"ping"}\n', -32700),
        ('[]\n', -32600),
        ('{"jsonrpc":"2.0","jsonrpc":"2.0","id":1,"method":"ping"}\n', -32600),
        ('{"jsonrpc":"2.0","id":1e999,"method":"ping"}\n', -32600),
    ],
)
def test_mcp_parse_errors_are_distinct_from_decoded_invalid_requests(wire, error_code):
    responses = _mcp_exchange(wire)
    assert responses == [{
        "jsonrpc": "2.0", "id": None,
        "error": {
            "code": error_code,
            "message": "parse error" if error_code == -32700 else "invalid request",
        },
    }]


def test_mcp_parse_and_decoded_errors_do_not_dispatch_service_operations():
    responses = _mcp_exchange(
        _mcp_initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        "not-json\n",
        "[]\n",
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "verdict", "arguments": {"op": "classify"},
        }},
    )
    assert [response.get("error", {}).get("code") for response in responses[1:3]] == [
        -32700, -32600,
    ]
    assert responses[3]["result"]["structuredContent"]["audit_seq"] == 1


def test_mcp_deep_valid_metadata_preserves_connection_for_following_request():
    nested_metadata = "[" * 500 + "0" + "]" * 500
    deep_ping = (
        '{"jsonrpc":"2.0","id":2,"method":"ping","params":{"_meta":'
        f'{{"nested":{nested_metadata}}}}}}}\n'
    )
    responses = _mcp_exchange(
        _mcp_initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        deep_ping,
        {"jsonrpc": "2.0", "id": 3, "method": "ping", "params": {}},
    )
    assert [response["id"] for response in responses] == [1, 2, 3]
    assert responses[1]["result"] == {}
    assert responses[2]["result"] == {}


def test_mcp_decoder_depth_rejection_preserves_connection_for_valid_request():
    nesting = MCP_MAX_JSON_NESTING + 1
    nested_metadata = "[" * nesting + "0" + "]" * nesting
    overdeep = (
        '{"jsonrpc":"2.0","id":2,"method":"ping","params":{"_meta":'
        f'{{"nested":{nested_metadata}}}}}}}\n'
    )
    responses = _mcp_exchange(
        _mcp_initialize(),
        overdeep,
        {"jsonrpc": "2.0", "id": 3, "method": "ping", "params": {}},
    )
    assert responses[1] == {
        "jsonrpc": "2.0", "id": None,
        "error": {"code": -32600, "message": "invalid request"},
    }
    assert responses[2]["id"] == 3
    assert responses[2]["result"] == {}


@pytest.mark.parametrize(
    ("method", "params"),
    [
        ("tools/list", {"cursor": 1}),
        ("tools/list", {"cursor": None}),
        ("tools/list", {"cursor": "ok", "extra": True}),
        ("tools/call", {"name": "verdict"}),
        ("tools/call", {"name": "verdict", "arguments": {"op": "classify"}, "extra": True}),
    ],
)
def test_mcp_supported_request_field_table_rejects_wrong_shapes_without_audit(
    method, params,
):
    responses = _mcp_exchange(
        _mcp_initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": method, "params": params},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "verdict", "arguments": {"op": "classify"},
        }},
    )
    assert responses[1]["error"]["code"] == -32602
    assert responses[2]["result"]["structuredContent"]["audit_seq"] == 1


@pytest.mark.parametrize("metadata", [
    [],
    {"progressToken": True},
    {"progressToken": {}},
])
def test_mcp_invalid_request_metadata_has_no_service_side_effect(metadata):
    responses = _mcp_exchange(
        _mcp_initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "verdict", "arguments": {"op": "classify"}, "_meta": metadata,
        }},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "verdict", "arguments": {"op": "classify"},
        }},
    )
    assert responses[1]["error"]["code"] == -32602
    assert responses[2]["result"]["structuredContent"]["audit_seq"] == 1


@pytest.mark.parametrize("overrides", [
    {"protocolVersion": ""},
    {"capabilities": []},
    {"clientInfo": []},
    {"clientInfo": {"name": "client"}},
    {"clientInfo": {"name": "", "version": "1"}},
    {"clientInfo": {"name": "client", "version": 1}},
    {"clientInfo": {"name": "client", "version": "1", "title": 1}},
])
def test_mcp_initialize_requires_valid_version_capabilities_and_client_info(overrides):
    process = subprocess.run(
        [sys.executable, str(THIS_DIR / "build_step_verdict.py"), "--mcp"],
        input=json.dumps(_mcp_initialize(**overrides)) + "\n",
        text=True, capture_output=True, timeout=10, check=False,
        creationflags=CREATE_NO_WINDOW,
    )
    response = json.loads(process.stdout)
    assert response["id"] == 1
    assert response["error"]["code"] == -32602


def test_export_rejects_non_string_evidence_sha256(tmp_path):
    request = _acceptance_request(tmp_path)
    request["suite_evidence"][0]["sha256"] = ["8"] * 64
    with pytest.raises(ValueError, match="invalid evidence hash"):
        decode_service_request(json.dumps(request))


def test_forge_launcher_passes_agents_file_path_without_json_reencoding():
    # This is an external consumer check, not an asset shipped by Skill Mesh.
    # Explicit selection keeps release checkouts independent of sibling layout.
    selected = os.environ.get("SKILL_MESH_FORGE_LAUNCHER")
    if not selected:
        pytest.skip("external Forge launcher not selected; set SKILL_MESH_FORGE_LAUNCHER")
    launcher = Path(selected).read_text(encoding="ascii")
    assert "$common += @('--agents', $agentPath)" in launcher
    assert "ReadAllText($agentPath)" not in launcher


def test_claude_build_step_maps_every_terminal_verdict_and_keeps_pass_last():
    adapter = (
        THIS_DIR.parent / "skills" / "build-step" / "providers" / "claude.md"
    ).read_text(encoding="utf-8")
    assert "map every terminal core `write_verdict` call" in adapter
    assert "including blocked, failed and halt exits" in adapter
    assert "Send terminal `PASS` only after every ship gate" in adapter


@pytest.mark.parametrize(
    ("event", "decision"),
    [
        ({"session_id": "parent", "tool_name": "mcp__forge_verdict__verdict"}, "allow"),
        ({"session_id": "parent", "agent_id": "child", "tool_name": "mcp__forge_verdict__verdict"}, "deny"),
        ({"session_id": "other", "tool_name": "mcp__forge_verdict__verdict"}, "deny"),
        ({"session_id": "parent"}, "deny"),
    ],
)
def test_claude_parent_guard_native_decision(event, decision):
    output = io.StringIO()
    assert claude_parent_guard("parent", io.StringIO(json.dumps(event)), output) == 0
    payload = json.loads(output.getvalue())
    assert payload["hookSpecificOutput"]["permissionDecision"] == decision
    assert "secret" not in output.getvalue()


# ---------------------------------------------------------------------------
# prose <-> code contract guard
# ---------------------------------------------------------------------------


def test_build_step_skill_documents_translator_table():
    """Guard the prose<->code contract: build-step SKILL.md must document the
    translator mapping as an actual table ROW -- a single line carrying BOTH the
    "NEEDS WORK" space-form terminal AND the "NEEDS-WORK" hyphen-form result enum,
    proving the mapping rather than just both strings appearing somewhere."""
    skill = (
        THIS_DIR.parent / "skills" / "build-step" / "core.md"
    ).read_text(encoding="utf-8")
    assert "verdict.json" in skill, "build-step SKILL.md must mention verdict.json"

    # The mapping row must put space-form and hyphen-form on the SAME line.
    # Robust to whitespace/formatting: scan each line for both substrings.
    def _maps_space_to_hyphen(line: str) -> bool:
        return "NEEDS WORK" in line and "NEEDS-WORK" in line

    assert any(_maps_space_to_hyphen(line) for line in skill.splitlines()), (
        "build-step SKILL.md must contain a translator-table row mapping "
        "'NEEDS WORK' (space) -> 'NEEDS-WORK' (hyphen) on a single line"
    )


def test_build_contract_uses_durable_run_bound_verdict():
    build_step = (
        THIS_DIR.parent / "skills" / "build-step" / "core.md"
    ).read_text(encoding="utf-8")
    build_phase = (
        THIS_DIR.parent / "skills" / "build-phase" / "core.md"
    ).read_text(encoding="utf-8")

    for token in ("--verdict-path", "--verdict-run-id"):
        assert token in build_step, f"build-step contract missing {token}"
        assert token in build_phase, f"build-phase contract missing {token}"
    assert "--verdict-key" not in build_step
    assert "--verdict-key" not in build_phase
    assert "parent-local `VERDICT_KEY`" in build_step
    assert "parent-local `VERDICT_KEY`" in build_phase
    assert "write_verdict" in build_step
    assert "expected_run_id" in build_phase
    assert "expected_secret" in build_phase
    assert "Fallback (older build-step with no sidecar)" not in build_phase
    assert "PASS only after" in build_step
