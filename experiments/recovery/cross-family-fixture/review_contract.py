"""Strict parsing, validation, and deterministic grading for reviewer output.

This module deliberately uses only the Python standard library.  It does not
start a reviewer, inspect a host, or read ambient configuration.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any


MAX_JSON_BYTES = 1024 * 1024
MAX_FINDINGS = 20

_TOP_LEVEL_KEYS = frozenset(
    {"run_id", "source_sha", "payload_sha256", "verdict", "summary", "findings"}
)
_FINDING_KEYS = frozenset(
    {"requirement_id", "severity", "title", "evidence", "explanation"}
)
_VERDICTS = frozenset({"PASS", "NEEDS_WORK", "UNCERTAIN"})
_REQUIREMENT_IDS = frozenset(
    {"REQ-QUANTITY", "REQ-TAX", "REQ-SHIPPING", "REQ-ROUND", "OTHER"}
)
_SEVERITIES = frozenset({"BLOCK", "NIT"})
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_WORD_RE = re.compile(r"[a-z0-9]+")


class ReviewContractError(ValueError):
    """Raised when reviewer or inventory data violates the frozen contract."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReviewContractError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_non_finite(token: str) -> None:
    raise ReviewContractError(f"non-finite JSON number is not allowed: {token}")


def _parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ReviewContractError(f"non-finite JSON number is not allowed: {token}")
    return value


def load_json_strict(raw: bytes | bytearray | memoryview) -> dict[str, Any]:
    """Load one bounded UTF-8 JSON object and reject permissive JSON features.

    Duplicate object keys at any depth, non-finite numbers, malformed UTF-8,
    trailing content, and top-level values other than an object fail closed.
    """

    if not isinstance(raw, (bytes, bytearray, memoryview)):
        raise ReviewContractError("review response must be supplied as bytes")
    if len(raw) > MAX_JSON_BYTES:
        raise ReviewContractError(
            f"review response exceeds the {MAX_JSON_BYTES}-byte limit"
        )
    encoded = bytes(raw)
    try:
        text = encoded.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ReviewContractError("review response is not valid UTF-8") from exc

    decoder = json.JSONDecoder(
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_non_finite,
        parse_float=_parse_finite_float,
    )
    start = len(text) - len(text.lstrip())
    try:
        value, end = decoder.raw_decode(text, start)
    except ReviewContractError:
        raise
    except json.JSONDecodeError as exc:
        raise ReviewContractError(
            f"review response is not one valid JSON value: {exc.msg}"
        ) from exc
    if text[end:].strip():
        raise ReviewContractError("review response has trailing content")
    if type(value) is not dict:
        raise ReviewContractError("review response must be a JSON object")
    return value


def _require_exact_keys(
    value: Mapping[str, Any], expected: frozenset[str], context: str
) -> None:
    actual = frozenset(value.keys())
    if actual == expected:
        return
    missing = sorted(expected - actual)
    extra = sorted(repr(key) for key in actual - expected)
    details: list[str] = []
    if missing:
        details.append(f"missing={missing!r}")
    if extra:
        details.append(f"extra={extra!r}")
    raise ReviewContractError(f"{context} has invalid keys: {', '.join(details)}")


def _require_string(
    value: Any,
    context: str,
    *,
    minimum: int,
    maximum: int,
    allowed: frozenset[str] | None = None,
    pattern: re.Pattern[str] | None = None,
) -> str:
    if type(value) is not str:
        raise ReviewContractError(f"{context} must be a string")
    if not minimum <= len(value) <= maximum:
        raise ReviewContractError(
            f"{context} length must be between {minimum} and {maximum}"
        )
    if allowed is not None and value not in allowed:
        raise ReviewContractError(f"{context} has an unsupported value: {value!r}")
    if pattern is not None and pattern.fullmatch(value) is None:
        raise ReviewContractError(f"{context} has an invalid format")
    return value


def _validate_response_schema(value: Any) -> dict[str, Any]:
    if type(value) is not dict:
        raise ReviewContractError("review response must be an object")
    _require_exact_keys(value, _TOP_LEVEL_KEYS, "review response")

    _require_string(value["run_id"], "run_id", minimum=1, maximum=100)
    _require_string(
        value["source_sha"],
        "source_sha",
        minimum=40,
        maximum=40,
        pattern=_SHA1_RE,
    )
    _require_string(
        value["payload_sha256"],
        "payload_sha256",
        minimum=64,
        maximum=64,
        pattern=_SHA256_RE,
    )
    _require_string(
        value["verdict"],
        "verdict",
        minimum=1,
        maximum=10,
        allowed=_VERDICTS,
    )
    _require_string(value["summary"], "summary", minimum=1, maximum=2000)

    findings = value["findings"]
    if type(findings) is not list:
        raise ReviewContractError("findings must be an array")
    if len(findings) > MAX_FINDINGS:
        raise ReviewContractError(f"findings cannot contain more than {MAX_FINDINGS} items")
    for index, finding in enumerate(findings):
        context = f"findings[{index}]"
        if type(finding) is not dict:
            raise ReviewContractError(f"{context} must be an object")
        _require_exact_keys(finding, _FINDING_KEYS, context)
        _require_string(
            finding["requirement_id"],
            f"{context}.requirement_id",
            minimum=1,
            maximum=20,
            allowed=_REQUIREMENT_IDS,
        )
        _require_string(
            finding["severity"],
            f"{context}.severity",
            minimum=1,
            maximum=5,
            allowed=_SEVERITIES,
        )
        _require_string(finding["title"], f"{context}.title", minimum=1, maximum=300)
        _require_string(
            finding["evidence"], f"{context}.evidence", minimum=1, maximum=2000
        )
        _require_string(
            finding["explanation"],
            f"{context}.explanation",
            minimum=1,
            maximum=2000,
        )
    return value


def validate_response(
    value: Any,
    expected_run_id: str,
    expected_source_sha: str,
    expected_payload_sha: str,
) -> dict[str, Any]:
    """Validate the exact response schema and its three sealed identity echoes.

    The original object is returned after validation.  A caller can therefore
    validate once and pass the same value to :func:`grade_response`.
    """

    response = _validate_response_schema(value)
    expected = (
        ("run_id", expected_run_id),
        ("source_sha", expected_source_sha),
        ("payload_sha256", expected_payload_sha),
    )
    for field, binding in expected:
        if type(binding) is not str:
            raise ReviewContractError(f"expected {field} binding must be a string")
        if response[field] != binding:
            raise ReviewContractError(f"{field} does not match the sealed request")
    return response


def _words(text: str) -> frozenset[str]:
    return frozenset(_WORD_RE.findall(text.casefold()))


def _has_word_prefix(words: frozenset[str], *prefixes: str) -> bool:
    return any(word.startswith(prefix) for word in words for prefix in prefixes)


def _quantity_signature(text: str) -> bool:
    words = _words(text)
    has_quantity = _has_word_prefix(words, "quantit")
    has_constraint = bool(
        words.intersection({"positive", "nonpositive", "zero", "negative", "0"})
    ) or ("non" in words and "positive" in words)
    has_behavior = _has_word_prefix(
        words, "valid", "reject", "accept", "allow", "permit", "remov", "omit"
    ) or bool(words.intersection({"check", "checks", "checked", "checking"}))
    return has_quantity and has_constraint and has_behavior


def _tax_signature(text: str) -> bool:
    words = _words(text)
    has_tax = _has_word_prefix(words, "tax")
    has_coupon = _has_word_prefix(words, "coupon", "discount")
    has_order_or_base = bool(
        words.intersection({"subtotal", "base", "before", "after", "order", "ordering"})
    )
    return has_tax and has_coupon and has_order_or_base


def _shipping_signature(text: str) -> bool:
    words = _words(text)
    has_shipping = _has_word_prefix(words, "ship")
    has_threshold = _has_word_prefix(words, "threshold")
    has_boundary = bool(
        words.intersection(
            {"boundary", "equal", "equality", "inclusive", "excluded", "excludes", "comparison"}
        )
    ) or ">" in text or "greater than or equal" in text.casefold()
    return has_shipping and has_threshold and has_boundary


_SEMANTIC_SIGNATURES: dict[str, Callable[[str], bool]] = {
    "CF-VALIDATION-001": _quantity_signature,
    "CF-TAX-001": _tax_signature,
    "CF-BOUNDARY-001": _shipping_signature,
}


def _generic_signature(text: str, terms: Sequence[str]) -> bool:
    normalized = " ".join(_WORD_RE.findall(text.casefold()))
    normalized_terms = [" ".join(_WORD_RE.findall(term.casefold())) for term in terms]
    normalized_terms = [term for term in normalized_terms if term]
    if not normalized_terms:
        return False
    hits = sum(1 for term in normalized_terms if term in normalized)
    required = 1 if len(normalized_terms) == 1 else max(2, (len(normalized_terms) + 1) // 2)
    return hits >= required


def _inventory_defects(inventory: Any) -> list[dict[str, Any]]:
    if type(inventory) is not dict:
        raise ReviewContractError("defect inventory must be an object")
    defects = inventory.get("defects")
    if type(defects) is not list or not defects:
        raise ReviewContractError("defect inventory must contain a nonempty defects array")
    result: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, defect in enumerate(defects):
        context = f"inventory.defects[{index}]"
        if type(defect) is not dict:
            raise ReviewContractError(f"{context} must be an object")
        for field in ("id", "requirement_id", "match_terms"):
            if field not in defect:
                raise ReviewContractError(f"{context} is missing {field!r}")
        defect_id = _require_string(defect["id"], f"{context}.id", minimum=1, maximum=100)
        if defect_id in seen_ids:
            raise ReviewContractError(f"duplicate defect inventory ID: {defect_id!r}")
        seen_ids.add(defect_id)
        requirement_id = _require_string(
            defect["requirement_id"],
            f"{context}.requirement_id",
            minimum=1,
            maximum=20,
            allowed=_REQUIREMENT_IDS,
        )
        terms = defect["match_terms"]
        if type(terms) is not list or not terms or len(terms) > 20:
            raise ReviewContractError(f"{context}.match_terms must contain 1 to 20 strings")
        checked_terms = [
            _require_string(term, f"{context}.match_terms", minimum=1, maximum=100)
            for term in terms
        ]
        result.append(
            {
                "id": defect_id,
                "requirement_id": requirement_id,
                "match_terms": checked_terms,
            }
        )
    return result


def _semantic_text(finding: Mapping[str, Any]) -> str:
    """Return only the three reviewer fields authorized for semantic matching."""

    return "\n".join(
        (str(finding["title"]), str(finding["evidence"]), str(finding["explanation"]))
    )


def grade_response(value: Any, inventory: Any) -> dict[str, Any]:
    """Grade validated findings against the seeded-defect inventory.

    A requirement ID is only a routing key.  Detection also requires the
    defect-specific semantic signature in the finding's title, evidence, or
    explanation.  Each finding and each defect can match at most once.
    Reviewer verdict and severity are retained; inconsistencies are warnings.
    """

    response = _validate_response_schema(value)
    defects = _inventory_defects(inventory)
    findings: list[dict[str, Any]] = response["findings"]

    detected: set[str] = set()
    unmatched: list[dict[str, Any]] = []
    warnings: list[str] = []

    for index, finding in enumerate(findings):
        requirement_id = finding["requirement_id"]
        if requirement_id in {"REQ-ROUND", "OTHER"}:
            unmatched.append(dict(finding))
            continue
        semantic_text = _semantic_text(finding)
        matching: list[dict[str, Any]] = []
        for defect in defects:
            if defect["requirement_id"] != requirement_id:
                continue
            signature = _SEMANTIC_SIGNATURES.get(defect["id"])
            matches = (
                signature(semantic_text)
                if signature is not None
                else _generic_signature(semantic_text, defect["match_terms"])
            )
            if matches:
                matching.append(defect)

        if matching and finding["severity"] != "BLOCK":
            warnings.append(
                f"findings[{index}] matches {matching[0]['id']} but uses severity "
                f"{finding['severity']}; seeded functional defects require BLOCK"
            )
        selected = next((defect for defect in matching if defect["id"] not in detected), None)
        if selected is None:
            unmatched.append(dict(finding))
            continue
        detected.add(selected["id"])

    detected_ids = [defect["id"] for defect in defects if defect["id"] in detected]
    block_count = sum(1 for finding in findings if finding["severity"] == "BLOCK")
    functional_finding_present = bool(detected_ids) or block_count > 0
    verdict = response["verdict"]
    if functional_finding_present and verdict != "NEEDS_WORK":
        warnings.append(
            f"reviewer verdict {verdict} conflicts with functional findings; expected NEEDS_WORK"
        )
    elif not functional_finding_present and verdict == "NEEDS_WORK":
        warnings.append(
            "reviewer verdict NEEDS_WORK has no BLOCK or seeded-defect finding"
        )

    return {
        "detected_defect_ids": detected_ids,
        "unmatched_findings": unmatched,
        "consistency_warnings": warnings,
        "counts": {
            "finding_count": len(findings),
            "block_finding_count": block_count,
            "detected_defect_count": len(detected_ids),
            "unmatched_finding_count": len(unmatched),
        },
    }
