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
import sys
from pathlib import Path

import pytest

SECRET = "11" * 32

# Sibling import - same dir as the module under test.
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from build_step_verdict import (  # noqa: E402  (sys.path tweak above)
    ADVANCE,
    BLOCKED,
    ORCHESTRATOR_WRITER,
    SCHEMA_VERSION,
    classify_verdict,
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
