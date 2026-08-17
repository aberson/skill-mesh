from __future__ import annotations

from decimal import Decimal
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SOURCE = REPO_ROOT / "experiments" / "recovery" / "cross-family-fixture"
CREATOR = FIXTURE_SOURCE / "create_fixture.py"
INVENTORY = FIXTURE_SOURCE / "expected-defects.json"
MODEL_POLICY = FIXTURE_SOURCE / "experiment-model-policy.json"
RESPONSE_SCHEMA = FIXTURE_SOURCE / "review-response.schema.json"
PROMPT_TEMPLATE = FIXTURE_SOURCE / "review-prompt-template.md"
RUNNER = REPO_ROOT / "experiments" / "recovery" / "run-cross-family-probe.ps1"
REPORT_TEMPLATE = REPO_ROOT / "documentation" / "experiments" / "cross-family-report-template.md"
RUNBOOK = REPO_ROOT / "documentation" / "experiments" / "cross-family-runbook.md"
REVIEW_CONTRACT = FIXTURE_SOURCE / "review_contract.py"
EVIDENCE_HELPERS = FIXTURE_SOURCE / "evidence.py"
HOST_RUNTIME = FIXTURE_SOURCE / "host_runtime.py"
PROBE = FIXTURE_SOURCE / "probe.py"
PINNED_DEFECT_INVENTORY_SHA256 = (
    "98baaa178e41dc23e5de70e3161de78c66b9c91052c4d0d99295ae1a8928ed37"
)


def _load_review_contract():
    specification = importlib.util.spec_from_file_location(
        "cross_family_review_contract", REVIEW_CONTRACT
    )
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _load_evidence_helpers():
    specification = importlib.util.spec_from_file_location(
        "cross_family_evidence", EVIDENCE_HELPERS
    )
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _load_host_runtime():
    fixture_path = str(FIXTURE_SOURCE)
    sys.path.insert(0, fixture_path)
    try:
        specification = importlib.util.spec_from_file_location(
            "cross_family_host_runtime", HOST_RUNTIME
        )
        assert specification and specification.loader
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        return module
    finally:
        assert sys.path[0] == fixture_path
        sys.path.pop(0)


def _load_probe():
    fixture_path = str(FIXTURE_SOURCE)
    sys.path.insert(0, fixture_path)
    try:
        specification = importlib.util.spec_from_file_location(
            "cross_family_probe", PROBE
        )
        assert specification and specification.loader
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        return module
    finally:
        assert sys.path[0] == fixture_path
        sys.path.pop(0)


def _finding(
    requirement_id: str,
    title: str,
    evidence: str,
    explanation: str,
    *,
    severity: str = "BLOCK",
) -> dict[str, str]:
    return {
        "requirement_id": requirement_id,
        "severity": severity,
        "title": title,
        "evidence": evidence,
        "explanation": explanation,
    }


def _review_response(
    findings: list[dict[str, str]] | None = None,
    *,
    verdict: str = "NEEDS_WORK",
) -> dict[str, object]:
    return {
        "run_id": "cross-claude-to-gpt-manual-saved-handoff-20260814T120000Z-1234abcd",
        "source_sha": "a" * 40,
        "payload_sha256": "b" * 64,
        "verdict": verdict,
        "summary": "Bounded synthetic review.",
        "findings": [] if findings is None else findings,
    }


def _probe_request(
    local_appdata: Path,
    live_claude: Path,
    live_codex: Path,
    *,
    action: str = "Prepare",
    direction: str = "claude-to-gpt",
    mechanism: str = "manual-saved-handoff",
    candidate_sha: str = "a" * 40,
) -> dict[str, object]:
    goal_a_id = "goala-20260814T021737Z-1b5ec416"
    run_id = (
        f"cross-{direction}-{mechanism}-20260814T120000Z-1234abcd"
    )
    attempt_id = "a0"
    return {
        "schema": "skill-mesh.cross-family.probe-request.v1",
        "goal_a_id": goal_a_id,
        "action": action,
        "direction": direction,
        "mechanism": mechanism,
        "fixture_root": str(
            local_appdata
            / "SkillMesh"
            / "Homes"
            / goal_a_id
            / f"{run_id}-{attempt_id}"
        ),
        "candidate_sha": candidate_sha,
        "evidence_dir": str(
            local_appdata
            / "SkillMesh"
            / "Evidence"
            / goal_a_id
            / "cross-family"
            / run_id
            / attempt_id
        ),
        "run_id": run_id,
        "attempt_id": attempt_id,
        "live_claude_home": str(live_claude),
        "live_codex_home": str(live_codex),
        "requested_reviewer_model": (
            "gpt-5.6-terra" if direction == "claude-to-gpt" else "sonnet"
        ),
        "credential_mode": "copy-file",
        "reviewer_timeout_seconds": 600,
        "what_if": True,
    }


def _run(
    arguments: list[str],
    *,
    cwd: Path,
    timeout: int = 120,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def _create(target: Path) -> dict[str, object]:
    result = _run(
        [sys.executable, "-I", "-B", str(CREATOR), "--target", str(target)],
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _load_candidate_module(candidate: Path):
    specification = importlib.util.spec_from_file_location("seeded_order_totals", candidate / "order_totals.py")
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _candidate_source_with_inventory(target: Path, inventory_bytes: bytes) -> Path:
    source_paths = (
        FIXTURE_SOURCE / "seed/base/README.md",
        PROMPT_TEMPLATE,
        RESPONSE_SCHEMA,
        MODEL_POLICY,
        REPORT_TEMPLATE,
    )
    for source in source_paths:
        destination = target / source.relative_to(REPO_ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    inventory = target / INVENTORY.relative_to(REPO_ROOT)
    inventory.parent.mkdir(parents=True, exist_ok=True)
    inventory.write_bytes(inventory_bytes)
    return target


@pytest.mark.parametrize(
    "line_ending",
    (b"\n", b"\r\n", b"\r"),
    ids=("lf", "crlf", "lone-cr"),
)
def test_prepare_seals_one_canonical_defect_inventory_identity_for_all_line_endings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    line_ending: bytes,
) -> None:
    probe = _load_probe()
    canonical_inventory = (
        INVENTORY.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    )
    source_root = _candidate_source_with_inventory(
        tmp_path / "candidate-source",
        canonical_inventory.replace(b"\n", line_ending),
    )
    monkeypatch.setattr(probe, "candidate_source_root", lambda: source_root)
    request = _probe_request(
        tmp_path / "local", tmp_path / ".claude", tmp_path / ".codex"
    )
    paths = {
        "fixture": tmp_path / "fixture",
        "evidence": tmp_path / "evidence",
        "live_claude": tmp_path / ".claude",
        "live_codex": tmp_path / ".codex",
    }

    prepared = probe.prepare(request, REPO_ROOT, paths)

    inventory_artifact = paths["evidence"] / "defect-inventory.json"
    assert inventory_artifact.read_bytes() == canonical_inventory
    assert b"\r" not in inventory_artifact.read_bytes()
    assert (
        hashlib.sha256(inventory_artifact.read_bytes()).hexdigest()
        == PINNED_DEFECT_INVENTORY_SHA256
    )
    fixture_json = json.loads((paths["evidence"] / "fixture.json").read_bytes())
    receipt_json = json.loads((paths["evidence"] / "prepare-receipt.json").read_bytes())
    assert prepared["fixture"]["defect_inventory_sha256"] == PINNED_DEFECT_INVENTORY_SHA256
    assert prepared["receipt"]["defect_inventory_sha256"] == PINNED_DEFECT_INVENTORY_SHA256
    assert fixture_json["defect_inventory_sha256"] == PINNED_DEFECT_INVENTORY_SHA256
    assert receipt_json["defect_inventory_sha256"] == PINNED_DEFECT_INVENTORY_SHA256
    manifest = dict(
        line.split("  ", 1)[::-1]
        for line in (paths["evidence"] / "prepare-manifest.sha256")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    assert manifest["defect-inventory.json"] == PINNED_DEFECT_INVENTORY_SHA256
    loaded = probe.load_prepared(request, paths)
    assert (
        loaded["fixture"]["defect_inventory_sha256"]
        == loaded["receipt"]["defect_inventory_sha256"]
    )
    assert loaded["receipt"]["defect_inventory_sha256"] == PINNED_DEFECT_INVENTORY_SHA256


def test_prepare_rejects_fixture_and_canonical_inventory_identity_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = _load_probe()
    create_fixture = probe.create_fixture.create_fixture

    def create_drifted_fixture(*args, **kwargs):
        fixture = create_fixture(*args, **kwargs)
        return {**fixture, "defect_inventory_sha256": "0" * 64}

    monkeypatch.setattr(probe.create_fixture, "create_fixture", create_drifted_fixture)
    request = _probe_request(
        tmp_path / "local", tmp_path / ".claude", tmp_path / ".codex"
    )
    paths = {
        "fixture": tmp_path / "fixture",
        "evidence": tmp_path / "evidence",
        "live_claude": tmp_path / ".claude",
        "live_codex": tmp_path / ".codex",
    }

    with pytest.raises(probe.ProbeError, match="canonical source"):
        probe.prepare(request, REPO_ROOT, paths)

    assert not (paths["evidence"] / "defect-inventory.json").exists()
    assert not (paths["evidence"] / "prepare-receipt.json").exists()


def test_fixture_creation_is_deterministic_clean_and_hides_oracle(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_result = _create(first)
    second_result = _create(second)
    assert first_result == second_result
    assert first_result["schema_version"] == 1
    assert first_result["base_sha"] != first_result["candidate_sha"]
    assert first_result["base_sha"] == "8cde6ac5b70357f5f5f0dd581f1a05c3a629ffcf"
    assert first_result["candidate_sha"] == "a02b8d5b42682a688b588b17dca221166e6bd647"
    assert first_result["candidate_tree_sha256"] == "3783ed5a9ead148f4dc13d8da224a021d5465647cf97788aede6afca8e1d1885"
    assert first_result["diff_sha256"] == "68d7b836cb1b2892da7ad6f492c555d94cc363fa2b065c3e33fe0fe5c4830333"
    assert first_result["defect_inventory_sha256"] == PINNED_DEFECT_INVENTORY_SHA256
    assert len(str(first_result["base_sha"])) == 40
    assert len(str(first_result["candidate_sha"])) == 40
    assert _run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=first).stdout == ""
    assert _run(["git", "rev-list", "--count", "HEAD"], cwd=first).stdout.strip() == "2"
    assert _run(["git", "rev-parse", "--show-object-format"], cwd=first).stdout.strip() == "sha1"
    assert not (first / "expected-defects.json").exists()
    assert not (first / "review-response.schema.json").exists()
    public_tests = _run([sys.executable, "-m", "unittest", "-q"], cwd=first)
    assert public_tests.returncode == 0, public_tests.stderr
    diff_bytes = first_result["diff_utf8"].encode("utf-8")
    assert diff_bytes.endswith(b"\n")
    assert hashlib.sha256(diff_bytes).hexdigest() == first_result["diff_sha256"]
    exact_diff = subprocess.run(
        [
            "git",
            "-c",
            "core.autocrlf=false",
            "-c",
            "color.ui=false",
            "diff",
            "--binary",
            "--no-ext-diff",
            "--full-index",
            "--src-prefix=a/",
            "--dst-prefix=b/",
            f"{first_result['base_sha']}..{first_result['candidate_sha']}",
            "--",
        ],
        cwd=first,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert exact_diff.returncode == 0, exact_diff.stderr.decode("utf-8", errors="replace")
    assert exact_diff.stdout == diff_bytes


def test_seeded_candidate_contains_three_real_requirement_defects(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    _create(candidate)
    module = _load_candidate_module(candidate)

    zero_quantity_total = module.order_total(
        [(Decimal("10.00"), 0)], Decimal("0"), Decimal("0"), Decimal("100.00")
    )
    assert zero_quantity_total == Decimal("7.50")

    coupon_total = module.order_total(
        [(Decimal("100.00"), 1)], Decimal("0.10"), Decimal("0.10"), Decimal("1000.00")
    )
    assert coupon_total == Decimal("107.50")
    assert coupon_total != Decimal("106.50")

    boundary_total = module.order_total(
        [(Decimal("100.00"), 1)], Decimal("0"), Decimal("0"), Decimal("100.00")
    )
    assert boundary_total == Decimal("107.50")
    assert boundary_total != Decimal("100.00")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    assert [item["id"] for item in inventory["defects"]] == [
        "CF-VALIDATION-001",
        "CF-TAX-001",
        "CF-BOUNDARY-001",
    ]
    assert [item["requirement_id"] for item in inventory["defects"]] == [
        "REQ-QUANTITY",
        "REQ-TAX",
        "REQ-SHIPPING",
    ]


def test_fixture_contract_files_are_stable_and_do_not_claim_qualification() -> None:
    policy = json.loads(MODEL_POLICY.read_text(encoding="utf-8"))
    assert policy["status"] == "candidate-unqualified"
    assert policy["fallback_allowed"] is False
    assert policy["reviewer_reasoning_effort"] == "medium"
    assert policy["production_map_change_allowed"] is False
    assert policy["step77_pairs"][0] == {
        "claude_model": "sonnet",
        "gpt_model": "gpt-5.6-terra",
        "run_in_step77": True,
    }
    assert policy["step77_pairs"][1]["claude_model"] == "fable"
    assert policy["step77_pairs"][1]["gpt_model"] == "gpt-5.6-sol"

    schema = json.loads(RESPONSE_SCHEMA.read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False
    assert schema["required"][:3] == ["run_id", "source_sha", "payload_sha256"]
    assert schema["properties"]["verdict"]["enum"] == ["PASS", "NEEDS_WORK", "UNCERTAIN"]
    finding = schema["properties"]["findings"]["items"]
    assert "requirement_id" in finding["required"]
    assert finding["properties"]["requirement_id"]["enum"] == [
        "REQ-QUANTITY",
        "REQ-TAX",
        "REQ-SHIPPING",
        "REQ-ROUND",
        "OTHER",
    ]
    prompt = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    assert "{{REQUIREMENTS}}" in prompt
    assert "{{DIFF}}" in prompt
    assert "{{RUN_ID}}" in prompt
    assert "{{SEEDED_CANDIDATE_SHA}}" in prompt
    assert "{{PAYLOAD_SHA256}}" in prompt
    assert "synthetic provenance" in prompt
    assert "exact `requirement_id`" in prompt
    assert hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def test_creator_rejects_relative_or_existing_target(tmp_path: Path) -> None:
    relative = _run(
        [sys.executable, "-I", "-B", str(CREATOR), "--target", "relative"],
        cwd=tmp_path,
    )
    assert relative.returncode == 2
    assert "must be absolute" in relative.stderr

    existing = tmp_path / "existing"
    existing.mkdir()
    duplicate = _run(
        [sys.executable, "-I", "-B", str(CREATOR), "--target", str(existing)],
        cwd=REPO_ROOT,
    )
    assert duplicate.returncode == 2
    assert "target already exists" in duplicate.stderr


def test_creator_ignores_ambient_git_redirection(tmp_path: Path) -> None:
    target = tmp_path / "isolated"
    trap = tmp_path / "ambient-git-dir"
    trap.mkdir()
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_DIR": str(trap),
            "GIT_WORK_TREE": str(tmp_path / "outside-worktree"),
            "GIT_INDEX_FILE": str(tmp_path / "outside-index"),
            "GIT_OBJECT_DIRECTORY": str(tmp_path / "outside-objects"),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.hooksPath",
            "GIT_CONFIG_VALUE_0": str(tmp_path / "outside-hooks"),
        }
    )
    result = _run(
        [sys.executable, "-I", "-B", str(CREATOR), "--target", str(target)],
        cwd=REPO_ROOT,
        env=environment,
    )
    assert result.returncode == 0, result.stderr
    assert (target / ".git").is_dir()
    assert list(trap.iterdir()) == []
    assert not (tmp_path / "outside-index").exists()
    assert not (tmp_path / "outside-objects").exists()


def test_report_template_has_one_closed_token_contract() -> None:
    template = REPORT_TEMPLATE.read_text(encoding="utf-8")
    tokens = re.findall(r"\{\{([A-Z0-9_]+)\}\}", template)
    assert len(tokens) == len(set(tokens)) == 61
    assert {
        "RESULT",
        "RUN_ID",
        "STEP76_CANDIDATE_SHA",
        "PAYLOAD_SHA256",
        "RESPONSE_SCHEMA_SHA256",
        "DEFECT_INVENTORY_SHA256",
        "REQUESTED_MODEL",
        "RESOLVED_MODEL",
        "RESOLVED_STATUS",
        "HOST_STARTED_COUNT",
        "ROOT_EXIT_CODE",
        "JOB_HELPER_SHA256",
        "SNAPSHOT_HELPER_SHA256",
        "LIVE_STATE_STATUS",
        "CLEANUP_STATUS",
    }.issubset(tokens)
    rendered = template
    for token in tokens:
        rendered = rendered.replace("{{" + token + "}}", "test-value")
    assert "{{" not in rendered
    assert "Fallback allowed | `false`" in template
    assert "identity is load-bearing" in template


def test_wrapper_and_runbook_define_only_the_bounded_mechanisms() -> None:
    wrapper = RUNNER.read_bytes()
    wrapper.decode("ascii")
    assert not wrapper.startswith(b"\xef\xbb\xbf")
    text = wrapper.decode("ascii")
    assert "manual-saved-handoff" in text
    assert "reviewer-only-dispatcher" in text
    assert "manual-now-automation-deferred" not in text
    assert "skill-mesh.cross-family.probe-request.v1" in text
    assert "[ValidateRange(1, 900)]" in text

    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert "manual-now-automation-deferred` is a Gate A policy option" in runbook
    assert "does not prove that a Claude-family or GPT-family model built" in runbook
    assert "Reviewer model identity is load-bearing here" in runbook
    assert "Missing or unverified resolved identity makes the overall result `AMBIGUOUS`" in runbook
    assert "runtime/skill-router.ps1" not in runbook


def test_report_template_token_names_are_exact() -> None:
    tokens = set(
        re.findall(
            r"\{\{([A-Z0-9_]+)\}\}", REPORT_TEMPLATE.read_text(encoding="utf-8")
        )
    )
    assert tokens == {
        "RESULT",
        "FAILURE_REASON",
        "GOAL_A_ID",
        "RUN_ID",
        "ATTEMPT_ID",
        "DIRECTION",
        "MECHANISM",
        "SYNTHETIC_ORIGIN_STATUS",
        "REVIEWER_HOST",
        "REVIEWER_ROLE",
        "STEP76_CANDIDATE_SHA",
        "SEEDED_BASE_SHA",
        "SEEDED_CANDIDATE_SHA",
        "SEEDED_TREE_SHA256",
        "SEEDED_DIFF_SHA256",
        "PAYLOAD_SHA256",
        "RESPONSE_SCHEMA_SHA256",
        "DEFECT_INVENTORY_SHA256",
        "MODEL_POLICY_SHA256",
        "MODEL_POLICY_STATUS",
        "REQUESTED_MODEL",
        "REQUESTED_MODEL_KIND",
        "RESOLVED_MODEL",
        "RESOLVED_STATUS",
        "RESOLVED_SOURCE",
        "FALLBACK_ATTEMPTS",
        "REVIEWER_EXECUTABLE",
        "REVIEWER_EXECUTABLE_SHA256",
        "REVIEWER_VERSION",
        "REVIEWER_CWD",
        "TOOL_POLICY",
        "SANDBOX_POLICY",
        "HOST_STARTED_COUNT",
        "ROOT_EXIT_CODE",
        "JOB_HELPER_SHA256",
        "SNAPSHOT_HELPER_SHA256",
        "GIT_VERSION",
        "GIT_EXECUTABLE_SHA256",
        "REDACTED_ARGV",
        "REVIEWER_VERDICT",
        "DETECTED_DEFECT_COUNT",
        "DETECTED_DEFECT_IDS",
        "REVIEWER_SUMMARY",
        "REVIEWER_FINDINGS",
        "UNMATCHED_FINDINGS",
        "LATENCY_SECONDS",
        "TOKEN_USAGE",
        "COST",
        "INPUT_TRANSFER",
        "PROMPT_SHA256",
        "RESPONSE_SHA256",
        "RAW_STDOUT_SHA256",
        "RAW_STDERR_SHA256",
        "CANDIDATE_BEFORE_IDENTITY",
        "CANDIDATE_AFTER_IDENTITY",
        "CANDIDATE_IDENTITY_STATUS",
        "LIVE_STATE_STATUS",
        "LIVE_STATE_DETAIL",
        "CLEANUP_STATUS",
        "CLEANUP_DETAIL",
        "UNRESOLVED_PREMISES",
    }


def test_strict_review_json_rejects_duplicate_trailing_nonfinite_and_oversize() -> None:
    contract = _load_review_contract()
    invalid_payloads = [
        b'{"outer":{"key":1,"key":2}}',
        b'{} trailing',
        b'{"number":NaN}',
        b'{"number":1e999}',
        b'\xff',
        b' ' * (contract.MAX_JSON_BYTES + 1),
    ]
    for raw in invalid_payloads:
        with pytest.raises(contract.ReviewContractError):
            contract.load_json_strict(raw)

    valid = _review_response()
    encoded = json.dumps(valid, allow_nan=False, separators=(",", ":")).encode("utf-8")
    assert contract.load_json_strict(encoded) == valid


def test_response_validation_enforces_bounds_exact_keys_and_all_bindings() -> None:
    contract = _load_review_contract()
    valid = _review_response()
    assert contract.validate_response(
        valid, valid["run_id"], valid["source_sha"], valid["payload_sha256"]
    ) is valid

    schema_failures: list[dict[str, object]] = []
    too_long = json.loads(json.dumps(valid))
    too_long["summary"] = "x" * 2001
    schema_failures.append(too_long)
    too_many = json.loads(json.dumps(valid))
    too_many["findings"] = [
        _finding("OTHER", "Extra", "Extra evidence", "Extra explanation")
        for _ in range(contract.MAX_FINDINGS + 1)
    ]
    schema_failures.append(too_many)
    extra_key = json.loads(json.dumps(valid))
    extra_key["unexpected"] = True
    schema_failures.append(extra_key)
    nested_extra = json.loads(json.dumps(valid))
    nested_extra["findings"] = [
        {
            **_finding("OTHER", "Extra", "Extra evidence", "Extra explanation"),
            "unexpected": True,
        }
    ]
    schema_failures.append(nested_extra)

    for response in schema_failures:
        with pytest.raises(contract.ReviewContractError):
            contract.validate_response(
                response, valid["run_id"], valid["source_sha"], valid["payload_sha256"]
            )

    mismatched_bindings = [
        ("different-run", valid["source_sha"], valid["payload_sha256"]),
        (valid["run_id"], "c" * 40, valid["payload_sha256"]),
        (valid["run_id"], valid["source_sha"], "d" * 64),
    ]
    for bindings in mismatched_bindings:
        with pytest.raises(contract.ReviewContractError):
            contract.validate_response(valid, *bindings)


def test_grader_requires_matching_requirement_and_retains_unmatched_findings() -> None:
    contract = _load_review_contract()
    quantity = _finding(
        "REQ-QUANTITY",
        "Quantity validation accepts zero quantities",
        "The positive quantity check was removed.",
        "The function must reject nonpositive quantities.",
    )
    duplicate_quantity = _finding(
        "REQ-QUANTITY",
        "Zero quantity is allowed",
        "Quantity validation no longer rejects zero.",
        "Restore the positive quantity check.",
    )
    wrong_requirement = _finding(
        "REQ-SHIPPING",
        "Tax is calculated before the coupon",
        "The tax base uses subtotal before discount.",
        "Apply the coupon before calculating tax.",
    )
    tax = _finding(
        "REQ-TAX",
        "Tax is calculated before the coupon",
        "The tax base uses subtotal before discount.",
        "Apply the coupon before calculating tax.",
    )
    shipping = _finding(
        "REQ-SHIPPING",
        "Shipping threshold equality boundary is excluded",
        "The comparison changed from >= to >.",
        "An order equal to the threshold must receive free shipping.",
    )
    unrelated = _finding(
        "OTHER",
        "Naming could be clearer",
        "A local name is short.",
        "This is not a seeded requirement defect.",
        severity="NIT",
    )
    response = _review_response(
        [quantity, duplicate_quantity, wrong_requirement, tax, shipping, unrelated]
    )

    result = contract.grade_response(
        response, json.loads(INVENTORY.read_text(encoding="utf-8"))
    )

    assert result["detected_defect_ids"] == [
        "CF-VALIDATION-001",
        "CF-TAX-001",
        "CF-BOUNDARY-001",
    ]
    assert [item["title"] for item in result["unmatched_findings"]] == [
        duplicate_quantity["title"],
        wrong_requirement["title"],
        unrelated["title"],
    ]
    assert result["counts"] == {
        "finding_count": 6,
        "block_finding_count": 5,
        "detected_defect_count": 3,
        "unmatched_finding_count": 3,
    }


def test_grader_surfaces_verdict_and_severity_contradictions() -> None:
    contract = _load_review_contract()
    findings = [
        _finding(
            "REQ-QUANTITY",
            "Quantity validation accepts zero quantities",
            "The positive quantity check was removed.",
            "The function must reject nonpositive quantities.",
            severity="NIT",
        ),
        _finding(
            "REQ-TAX",
            "Tax is calculated before the coupon",
            "The tax base uses subtotal before discount.",
            "Apply the coupon before calculating tax.",
            severity="NIT",
        ),
        _finding(
            "REQ-SHIPPING",
            "Shipping threshold equality boundary is excluded",
            "The comparison changed from >= to >.",
            "An order equal to the threshold must receive free shipping.",
            severity="NIT",
        ),
    ]
    result = contract.grade_response(
        _review_response(findings, verdict="PASS"),
        json.loads(INVENTORY.read_text(encoding="utf-8")),
    )
    assert result["counts"]["detected_defect_count"] == 3
    assert len(result["consistency_warnings"]) == 4
    assert all("severity NIT" in warning for warning in result["consistency_warnings"][:3])
    assert "verdict PASS conflicts" in result["consistency_warnings"][3]


def test_wrapper_parses_and_rejects_invalid_action_or_direction_model_pairs(
    tmp_path: Path,
) -> None:
    quoted_runner = str(RUNNER).replace("'", "''")
    parsed = _run(
        [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"[void][scriptblock]::Create([IO.File]::ReadAllText('{quoted_runner}'))",
        ],
        cwd=REPO_ROOT,
    )
    assert parsed.returncode == 0, parsed.stderr

    common = [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(RUNNER),
        "-GoalAId",
        "goala-20260814T021737Z-1b5ec416",
        "-Direction",
        "claude-to-gpt",
        "-Mechanism",
        "manual-saved-handoff",
        "-FixtureRoot",
        str(tmp_path / "fixture"),
        "-CandidateSha",
        "a" * 40,
        "-EvidenceDir",
        str(tmp_path / "evidence"),
        "-RunId",
        "cross-claude-to-gpt-manual-saved-handoff-20260814T120000Z-1234abcd",
        "-AttemptId",
        "a0",
        "-LiveClaudeHome",
        str(tmp_path / "live-claude"),
        "-LiveCodexHome",
        str(tmp_path / "live-codex"),
    ]
    invalid_action = _run(
        [*common, "-Action", "Run", "-RequestedReviewerModel", "gpt-5.6-terra"],
        cwd=REPO_ROOT,
    )
    assert invalid_action.returncode == 2
    assert "action 'Run' is not valid for mechanism 'manual-saved-handoff'" in invalid_action.stderr

    invalid_model = _run(
        [*common, "-Action", "Prepare", "-RequestedReviewerModel", "sonnet"],
        cwd=REPO_ROOT,
    )
    assert invalid_model.returncode == 2
    assert "requires requested reviewer model 'gpt-5.6-terra'" in invalid_model.stderr


def test_windows_powershell_wrapper_delivers_utf8_request_to_probe(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("Windows PowerShell 5.1 is the supported wrapper host")
    live_claude = tmp_path / ".claude"
    live_codex = tmp_path / ".codex"
    live_claude.mkdir()
    live_codex.mkdir()
    run_id = "cross-claude-to-gpt-manual-saved-handoff-20260814T120000Z-1234abcd"
    command = [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(RUNNER),
        "-GoalAId",
        "goala-20260814T021737Z-1b5ec416",
        "-Action",
        "Prepare",
        "-Direction",
        "claude-to-gpt",
        "-Mechanism",
        "manual-saved-handoff",
        "-FixtureRoot",
        str(tmp_path / "fixture"),
        "-CandidateSha",
        "a" * 40,
        "-EvidenceDir",
        str(tmp_path / "evidence"),
        "-RunId",
        run_id,
        "-AttemptId",
        "a0",
        "-LiveClaudeHome",
        str(live_claude),
        "-LiveCodexHome",
        str(live_codex),
        "-RequestedReviewerModel",
        "gpt-5.6-terra",
        "-WhatIf",
    ]

    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 2
    result = json.loads(completed.stdout)
    assert result["status"] == "REJECTED"
    assert "request is not one UTF-8 JSON object" not in result["error"]
    assert "live_claude_home is not the current user's native Claude home" in result["error"]
    assert "PropertyAssignmentException" not in completed.stderr
    assert not (tmp_path / "fixture").exists()
    assert not (tmp_path / "evidence").exists()


def test_isolated_probe_bootstrap_loads_candidate_sibling_modules() -> None:
    bootstrap = (
        "import runpy,sys;from pathlib import Path;"
        "p=str(Path(sys.argv[1]).resolve());"
        "sys.path.insert(0,str(Path(p).parent));"
        "runpy.run_path(p,run_name='__main__')"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", bootstrap, str(FIXTURE_SOURCE / "probe.py")],
        input=b"{}",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert result.returncode == 2
    payload = json.loads(result.stdout.decode("ascii"))
    assert payload["status"] == "REJECTED"
    assert "ModuleNotFoundError" not in result.stderr.decode("utf-8", errors="replace")


def test_evidence_writes_are_create_new_and_collision_safe(tmp_path: Path) -> None:
    evidence = _load_evidence_helpers()
    destination = tmp_path / "result.json"
    evidence.write_new(destination, b"first\n")
    with pytest.raises((evidence.EvidenceError, FileExistsError)):
        evidence.write_new(destination, b"replacement\n")
    assert destination.read_bytes() == b"first\n"

    bounded = tmp_path / "bounded.txt"
    with pytest.raises(evidence.EvidenceError, match="size bound"):
        evidence.write_new(bounded, b"123", maximum=2)
    evidence.write_new(bounded, b"123", maximum=3)


def test_report_renderer_requires_exact_keys_and_closes_all_placeholders() -> None:
    evidence = _load_evidence_helpers()
    template = REPORT_TEMPLATE.read_text(encoding="utf-8")
    tokens = re.findall(r"\{\{([A-Z0-9_]+)\}\}", template)
    values = {token: "test-value" for token in tokens}
    rendered = evidence.render_template(template, values)
    assert "{{" not in rendered

    missing = dict(values)
    missing.pop("RESULT")
    with pytest.raises(evidence.EvidenceError):
        evidence.render_template(template, missing)
    with pytest.raises(evidence.EvidenceError):
        evidence.render_template(template, {**values, "EXTRA": "not allowed"})
    with pytest.raises(evidence.EvidenceError):
        evidence.render_template("{{RESULT}} {{RESULT}}", {"RESULT": "PASS"})
    with pytest.raises(evidence.EvidenceError):
        evidence.render_template(template, {**values, "RESULT": "{{INJECTED}}"})


def test_evidence_redaction_removes_private_paths_case_insensitively() -> None:
    evidence = _load_evidence_helpers()
    private_home = "C:" + r"\Users\Alice"
    private_fixture = private_home + r"\private\fixture"
    source = (
        private_fixture.upper()
        + "\n"
        + private_home.lower()
        + r"\elsewhere"
        + "\x01"
    )
    redacted = evidence.redact_text(
        source,
        {private_home: "<HOME>", private_fixture: "<FIXTURE>"},
    )
    assert private_home.casefold() not in redacted.casefold()
    assert "<FIXTURE>" in redacted
    assert r"<HOME>\elsewhere" in redacted
    assert "\x01" not in redacted


def test_manifest_covers_retained_files_once_and_excludes_itself(tmp_path: Path) -> None:
    evidence = _load_evidence_helpers()
    nested = tmp_path / "nested"
    nested.mkdir()
    (tmp_path / "alpha.txt").write_bytes(b"alpha\n")
    (nested / "beta.json").write_bytes(b'{"beta":true}\n')
    manifest = tmp_path / "MANIFEST.sha256"

    entries = evidence.write_manifest(tmp_path, manifest)

    assert [entry["path"] for entry in entries] == ["alpha.txt", "nested/beta.json"]
    assert all(entry["path"] != manifest.name for entry in entries)
    manifest_lines = manifest.read_text(encoding="utf-8").splitlines()
    assert manifest_lines == [
        f"{entry['sha256']}  {entry['path']}" for entry in entries
    ]
    with pytest.raises(evidence.EvidenceError):
        evidence.write_manifest(tmp_path, manifest)


def test_host_environment_scrubs_ambient_credentials_and_uses_disposable_homes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = _load_host_runtime()
    ambient_secrets = {
        "CLAUDE_CODE_OAUTH_TOKEN": "claude-secret",
        "ANTHROPIC_API_KEY": "anthropic-secret",
        "OPENAI_API_KEY": "openai-secret",
        "AZURE_OPENAI_API_KEY": "azure-secret",
        "GOOGLE_API_KEY": "google-secret",
        "AWS_ACCESS_KEY_ID": "aws-secret",
        "GITHUB_TOKEN": "github-secret",
        "CODEX_HOME": str(tmp_path / "ambient-codex"),
        "CLAUDE_CONFIG_DIR": str(tmp_path / "ambient-claude"),
    }
    for name, value in ambient_secrets.items():
        monkeypatch.setenv(name, value)

    codex_root = tmp_path / "codex-runtime"
    codex_environment = host._minimal_environment(codex_root, "codex")
    claude_root = tmp_path / "claude-runtime"
    claude_environment = host._minimal_environment(claude_root, "claude")

    secret_names = set(ambient_secrets) - {"CODEX_HOME", "CLAUDE_CONFIG_DIR"}
    assert secret_names.isdisjoint(codex_environment)
    assert secret_names.isdisjoint(claude_environment)
    assert "CLAUDE_CONFIG_DIR" not in codex_environment
    assert "CODEX_HOME" not in claude_environment
    assert codex_environment["HOME"] == str(codex_root / "user")
    assert codex_environment["USERPROFILE"] == str(codex_root / "user")
    assert codex_environment["APPDATA"] == str(codex_root / "appdata")
    assert codex_environment["LOCALAPPDATA"] == str(codex_root / "localappdata")
    assert codex_environment["CODEX_HOME"] == str(codex_root / "codex-home")
    assert codex_environment["CODEX_SQLITE_HOME"] == str(codex_root / "codex-sqlite")
    assert claude_environment["CLAUDE_CONFIG_DIR"] == str(
        claude_root / "claude-home"
    )
    assert claude_environment["CLAUDE_CODE_AUTO_CONNECT_IDE"] == "false"


def test_host_commands_pin_model_and_apply_no_tool_read_only_policy(tmp_path: Path) -> None:
    host = _load_host_runtime()
    executable = tmp_path / "reviewer.exe"
    cwd = tmp_path / "cwd"
    evidence_dir = tmp_path / "evidence"

    codex_argv, codex_response = host._host_command(
        "codex",
        executable,
        "gpt-5.6-terra",
        "synthetic prompt",
        cwd,
        evidence_dir,
        RESPONSE_SCHEMA,
    )
    assert codex_argv[0] == "--strict-config"
    assert codex_argv[codex_argv.index("--model") + 1] == "gpt-5.6-terra"
    assert codex_argv[codex_argv.index("--sandbox") + 1] == "read-only"
    assert codex_argv[codex_argv.index("--ask-for-approval") + 1] == "never"
    assert "--ignore-user-config" in codex_argv
    assert "--ignore-rules" in codex_argv
    assert codex_argv[codex_argv.index("exec") + 1] == "--skip-git-repo-check"
    assert "--ephemeral" in codex_argv
    assert 'cli_auth_credentials_store="file"' in codex_argv
    assert codex_response == evidence_dir / "review-response.json"

    claude_argv, claude_response = host._host_command(
        "claude",
        executable,
        "sonnet",
        "synthetic prompt",
        cwd,
        evidence_dir,
        RESPONSE_SCHEMA,
    )
    assert claude_argv[claude_argv.index("--model") + 1] == "sonnet"
    assert claude_argv[claude_argv.index("--permission-mode") + 1] == "dontAsk"
    assert claude_argv[claude_argv.index("--tools") + 1] == ""
    assert claude_argv[claude_argv.index("--disallowedTools") + 1] == "*"
    assert "--safe-mode" in claude_argv
    assert "--no-session-persistence" in claude_argv
    assert claude_response == evidence_dir / "reviewer-stdout.txt"
    retained_schema = json.loads(RESPONSE_SCHEMA.read_text(encoding="utf-8"))
    assert "$schema" in retained_schema
    claude_schema = json.loads(
        claude_argv[claude_argv.index("--json-schema") + 1]
    )
    assert "$schema" not in claude_schema
    assert claude_schema == {
        key: value for key, value in retained_schema.items() if key != "$schema"
    }


def test_claude_identity_parser_handles_one_or_multiple_model_usage_entries() -> None:
    host = _load_host_runtime()
    response = _review_response()
    one_model = json.dumps(
        {
            "structured_output": response,
            "modelUsage": {"claude-sonnet-test": {"inputTokens": 10}},
            "usage": {"input_tokens": 10},
            "total_cost_usd": 0.01,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    parsed = host._parse_claude(one_model)
    assert json.loads(parsed[0]) == response
    assert parsed[2:5] == (
        "claude-sonnet-test",
        "provider-reported",
        "reviewer-stdout.txt::$['modelUsage']['claude-sonnet-test']",
    )

    multiple_models = json.dumps(
        {
            "structured_output": response,
            "modelUsage": {
                "claude-sonnet-test": {"inputTokens": 10},
                "claude-fallback-test": {"inputTokens": 1},
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")
    parsed_multiple = host._parse_claude(multiple_models)
    assert parsed_multiple[2] == "claude-fallback-test|claude-sonnet-test"
    assert parsed_multiple[3] == "unverified"
    assert "multiple entries" in parsed_multiple[4]

    result_only = json.dumps(
        {"result": json.dumps(response), "modelUsage": {"claude-sonnet-test": {}}},
        separators=(",", ":"),
    ).encode("utf-8")
    with pytest.raises(host.HostRuntimeError, match="structured_output"):
        host._parse_claude(result_only)


def test_codex_identity_parser_ignores_model_names_in_assistant_text(
    tmp_path: Path,
) -> None:
    host = _load_host_runtime()
    response_path = tmp_path / "review-response.json"
    response = _review_response()
    response_path.write_text(json.dumps(response), encoding="utf-8")
    stdout = (
        json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "text": 'I used {"model":"gpt-5.6-terra"}.',
                },
            },
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")

    parsed = host._parse_codex(stdout, response_path)

    assert json.loads(parsed[0]) == response
    assert parsed[2] == ""
    assert parsed[3] == "unavailable"
    assert parsed[4] == "no allowlisted structured model field"


def test_snapshot_contract_covers_live_roots_and_detects_any_record_change(
    tmp_path: Path,
) -> None:
    host = _load_host_runtime()
    live_claude = tmp_path / ".claude"
    live_codex = tmp_path / ".codex"
    request = host._snapshot_request(
        live_claude,
        live_codex,
        [live_claude / ".credentials.json", live_codex / "auth.json"],
        b"k" * 32,
        [tmp_path / "approved-reparse-target"],
    )
    assert request["roots"] == [
        {"label": "claude", "path": str(live_claude)},
        {"label": "codex", "path": str(live_codex)},
        {"label": "agents", "path": str(tmp_path / ".agents")},
    ]
    assert request["secret_paths"] == [
        str(live_claude / ".credentials.json"),
        str(live_codex / "auth.json"),
    ]
    assert request["hmac_key_hex"] == (b"k" * 32).hex()
    assert request["allowed_reparse_roots"] == [
        str(tmp_path / "approved-reparse-target")
    ]

    before = {"records": [{"path": "codex/session", "sha256": "a"}]}
    assert host.compare_snapshots(before, before) == (
        "MATCH",
        {"record_count": 1, "changed_paths": []},
    )
    status, detail = host.compare_snapshots(
        before, {"records": [{"path": "codex/session", "sha256": "b"}]}
    )
    assert status == "AMBIGUOUS"
    assert detail["changed_paths"] == ["codex/session"]


def test_snapshot_evidence_uses_its_separate_64_mib_bound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = _load_host_runtime()
    payload = {"schema": 1, "status": "COMPLETE", "records": []}
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        host.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(payload, separators=(",", ":")).encode("ascii"),
            stderr=b"",
        ),
    )

    def fake_write(path: Path, content: bytes, *, maximum: int) -> None:
        captured.update(path=path, content=content, maximum=maximum)

    monkeypatch.setattr(host, "write_new", fake_write)
    destination = tmp_path / "live-before.json"
    assert host.take_snapshot(
        tmp_path / "helper.py",
        {"schema": 1},
        destination,
    ) == payload
    assert captured["path"] == destination
    assert captured["maximum"] == 64 * 1024 * 1024


def test_job_invocation_requires_proof_that_the_job_is_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = _load_host_runtime()
    captured: dict[str, object] = {}

    def job_result(*, empty: bool) -> dict[str, object]:
        return {
            "schema": 1,
            "status": "COMPLETE" if empty else "INCOMPLETE",
            "target_started": True,
            "assigned_before_resume": True,
            "root_pid": 1234,
            "root_exit_code": 0,
            "timed_out": False,
            "survivors_existed": False,
            "survivor_pids": [],
            "terminate_job_called": False,
            "job_empty_confirmed": empty,
            "duration_seconds": 0.25,
            "stage": "complete" if empty else "job-not-empty",
            "win32_error": None,
        }

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(job_result(empty=True)).encode("utf-8"),
            stderr=b"",
        )

    monkeypatch.setattr(host.subprocess, "run", fake_run)
    evidence_dir = tmp_path / "complete"
    evidence_dir.mkdir()
    result = host._invoke_job(
        tmp_path / "job_process.py",
        tmp_path / "reviewer.exe",
        ["--model", "test"],
        tmp_path,
        evidence_dir,
        {"HOME": str(tmp_path / "home")},
        17,
    )
    assert result["job_empty_confirmed"] is True
    request = json.loads(captured["kwargs"]["input"])
    assert request["timeout_ms"] == 17_000
    assert captured["kwargs"]["timeout"] == 47
    assert captured["kwargs"]["env"] == {"HOME": str(tmp_path / "home")}
    assert json.loads((evidence_dir / "containment.json").read_text(encoding="ascii")) == result

    def fake_incomplete(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=3,
            stdout=json.dumps(job_result(empty=False)).encode("utf-8"),
            stderr=b"",
        )

    monkeypatch.setattr(host.subprocess, "run", fake_incomplete)
    incomplete_dir = tmp_path / "incomplete"
    incomplete_dir.mkdir()
    with pytest.raises(host.HostRuntimeError, match="zero active processes"):
        host._invoke_job(
            tmp_path / "job_process.py",
            tmp_path / "reviewer.exe",
            [],
            tmp_path,
            incomplete_dir,
            {},
            17,
        )


def test_probe_path_validation_accepts_only_reviewed_run_leaves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = _load_probe()
    local_appdata = tmp_path / "local"
    local_appdata.mkdir()
    live_claude = tmp_path / "live" / ".claude"
    live_codex = tmp_path / "live" / ".codex"
    live_claude.mkdir(parents=True)
    live_codex.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    request = _probe_request(local_appdata, live_claude, live_codex)
    monkeypatch.setenv("LOCALAPPDATA", str(local_appdata))
    monkeypatch.setenv("USERPROFILE", str(live_claude.parent))
    monkeypatch.setattr(probe, "_worktree_roots", lambda _: [repo])

    paths = probe.validate_paths(request, repo)
    assert paths["fixture"] == Path(request["fixture_root"])
    assert paths["evidence"] == Path(request["evidence_dir"])

    wrong_leaf = dict(request)
    wrong_leaf["fixture_root"] = str(local_appdata / "unreviewed-fixture")
    with pytest.raises(probe.ProbeError, match="run-specific locator"):
        probe.validate_paths(wrong_leaf, repo)

    overlapping_live = dict(request)
    overlapping_live["live_codex_home"] = str(live_claude)
    with pytest.raises(probe.ProbeError, match="overlap"):
        probe.validate_paths(overlapping_live, repo)

    monkeypatch.setenv("TEMP", str(live_claude))
    with pytest.raises(probe.ProbeError, match="candidate runtime root overlaps"):
        probe.validate_paths(request, repo)


def test_candidate_validation_binds_plan_and_external_index_exactly_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = _load_probe()
    candidate = "a" * 40
    other = "b" * 40
    repo = tmp_path / "repo"
    repo.mkdir()
    local_appdata = tmp_path / "local"
    index = (
        local_appdata
        / "SkillMesh"
        / "Evidence"
        / "goala-20260814T021737Z-1b5ec416"
        / "evidence-index.md"
    )
    index.parent.mkdir(parents=True)
    request = _probe_request(
        local_appdata,
        tmp_path / ".claude",
        tmp_path / ".codex",
        candidate_sha=candidate,
    )
    changed_path = ["experiments/recovery/cross-family-fixture/probe.py"]

    def fake_git(_repo, *args, allow=(0,)):
        stdout = (
            (changed_path[0] + "\n").encode("utf-8")
            if args and args[0] == "diff-tree"
            else b""
        )
        return subprocess.CompletedProcess(
            args=["git", *args], returncode=0, stdout=stdout, stderr=b""
        )

    monkeypatch.setenv("LOCALAPPDATA", str(local_appdata))
    monkeypatch.setattr(probe, "_run_git", fake_git)
    monkeypatch.setattr(
        probe.host_runtime,
        "validate_helpers",
        lambda _repo, _candidate: {
            "job": {"sha256": "1" * 64},
            "snapshot": {"sha256": "2" * 64},
        },
    )

    def write_plan(selected: str) -> None:
        (repo / "plan.md").write_text(
            "# Plan\n\n"
            "**GoalAId:** `goala-20260814T021737Z-1b5ec416`\n\n"
            "### Step 76: Cross-family fixture\n\n"
            f"**Candidate commit:** `{selected}`\n\n"
            "### Step 77: Live experiment\n",
            encoding="utf-8",
        )

    write_plan(candidate)
    index.write_text(
        f"| fixture | `step76-candidate` | `{candidate}` | active |\n",
        encoding="utf-8",
    )
    result = probe.validate_candidate(request, repo)
    assert result == {
        "candidate_sha": candidate,
        "job_helper_sha256": "1" * 64,
        "snapshot_helper_sha256": "2" * 64,
    }

    write_plan(other)
    with pytest.raises(probe.ProbeError, match="plan.md"):
        probe.validate_candidate(request, repo)

    write_plan(candidate)
    index.write_text(
        f"| fixture | `step76-candidate` | `{other}` | active |\n",
        encoding="utf-8",
    )
    with pytest.raises(probe.ProbeError, match="external evidence index"):
        probe.validate_candidate(request, repo)

    index.write_text(
        (
            f"| fixture-1 | `step76-candidate` | `{candidate}` | active |\n"
            f"| fixture-2 | `step76-candidate` | `{candidate}` | active |\n"
        ),
        encoding="utf-8",
    )
    with pytest.raises(probe.ProbeError, match="exactly one"):
        probe.validate_candidate(request, repo)

    index.write_text(
        f"| fixture | `step76-candidate` | `{candidate}` | active |\n",
        encoding="utf-8",
    )
    changed_path[0] = "README.md"
    with pytest.raises(probe.ProbeError, match="outside its allowlist"):
        probe.validate_candidate(request, repo)


def test_what_if_plan_is_deterministic_and_writes_nothing(tmp_path: Path) -> None:
    probe = _load_probe()
    local_appdata = tmp_path / "local"
    request = _probe_request(
        local_appdata, tmp_path / ".claude", tmp_path / ".codex"
    )
    paths = {
        "fixture": Path(request["fixture_root"]),
        "evidence": Path(request["evidence_dir"]),
        "live_claude": Path(request["live_claude_home"]),
        "live_codex": Path(request["live_codex_home"]),
    }
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    candidate = {
        "candidate_sha": request["candidate_sha"],
        "job_helper_sha256": "1" * 64,
        "snapshot_helper_sha256": "2" * 64,
    }

    first = probe.what_if_plan(request, paths, candidate)
    second = probe.what_if_plan(request, paths, candidate)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert first == second
    assert before == after == []
    assert first["status"] == "WHAT_IF"
    assert first["host_start_count"] == 0
    assert first["fallback_allowed"] is False
    assert first["delete_targets"] == [
        str(probe.candidate_runtime_root(request))
    ]
    assert str(paths["fixture"]) in first["write_targets"]
    assert str(paths["evidence"]) in first["write_targets"]
    assert str(paths["evidence"] / "review-starting.json") not in first["write_targets"]
    assert str(paths["live_codex"] / "auth.json") not in first["read_targets"]
    assert first["candidate_helpers"] == {
        "job_sha256": "1" * 64,
        "snapshot_sha256": "2" * 64,
    }
    assert all("start exactly one" not in step for step in first["command_sequence"])

    run_request = _probe_request(
        local_appdata,
        tmp_path / ".claude",
        tmp_path / ".codex",
        action="Run",
        mechanism="reviewer-only-dispatcher",
    )
    run_paths = {
        "fixture": Path(run_request["fixture_root"]),
        "evidence": Path(run_request["evidence_dir"]),
        "live_claude": Path(run_request["live_claude_home"]),
        "live_codex": Path(run_request["live_codex_home"]),
    }
    run_plan = probe.what_if_plan(run_request, run_paths, candidate)
    assert run_plan["host_start_count"] == 1
    assert run_plan["snapshot_policy"]["max_evidence_bytes"] == 64 * 1024 * 1024
    assert str(run_paths["live_codex"] / "auth.json") in run_plan["read_targets"]
    assert str(run_paths["evidence"] / "candidate-before.json") in run_plan["write_targets"]
    assert str(run_paths["evidence"] / "candidate-after.json") in run_plan["write_targets"]
    assert str(run_paths["evidence"] / "invocation-plan.json") in run_plan["write_targets"]
    assert any("start exactly one native codex reviewer" in step for step in run_plan["command_sequence"])
    assert sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")) == []


@pytest.mark.parametrize(
    ("action", "mechanism", "expected_sequence", "expected_status"),
    (
        ("Prepare", "manual-saved-handoff", ["prepare"], "PREPARED"),
        (
            "Run",
            "reviewer-only-dispatcher",
            ["prepare", "load_prepared", "execute_review"],
            "COMPLETE",
        ),
        (
            "InvokeSavedHandoff",
            "manual-saved-handoff",
            ["load_prepared", "execute_review"],
            "COMPLETE",
        ),
    ),
)
def test_main_reopens_monolithic_run_and_preserves_other_action_flows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    mechanism: str,
    expected_sequence: list[str],
    expected_status: str,
) -> None:
    probe = _load_probe()
    request = _probe_request(
        tmp_path / "local",
        tmp_path / ".claude",
        tmp_path / ".codex",
        action=action,
        mechanism=mechanism,
    )
    request["what_if"] = False
    paths = {
        "fixture": Path(request["fixture_root"]),
        "evidence": Path(request["evidence_dir"]),
        "live_claude": Path(request["live_claude_home"]),
        "live_codex": Path(request["live_codex_home"]),
    }
    candidate = {"candidate_sha": request["candidate_sha"]}
    produced = {
        "source": "prepare",
        "receipt": {"payload_sha256": "1" * 64},
    }
    reopened = {
        "source": "load_prepared",
        "receipt": {"payload_sha256": "1" * 64},
    }
    sequence: list[str] = []
    emitted: list[dict[str, object]] = []
    monkeypatch.setattr(
        probe.sys,
        "stdin",
        type("Input", (), {"buffer": io.BytesIO(b"synthetic request")})(),
    )
    monkeypatch.setattr(probe, "load_request", lambda _raw: request)
    monkeypatch.setattr(probe, "repository_root", lambda: REPO_ROOT)
    monkeypatch.setattr(probe, "validate_paths", lambda _request, _repo: paths)
    monkeypatch.setattr(probe, "validate_candidate", lambda _request, _repo: candidate)
    monkeypatch.setattr(
        probe,
        "reinvoke_candidate_runtime",
        lambda _raw, _request, _repo: None,
    )

    def fake_prepare(_request, _repo, _paths):
        sequence.append("prepare")
        return produced

    def fake_load_prepared(_request, _paths):
        if action == "Run":
            assert sequence == ["prepare"]
        sequence.append("load_prepared")
        return reopened

    def fake_execute_review(_request, _candidate, prepared, _repo, _paths):
        sequence.append("execute_review")
        assert prepared is reopened
        return {"experiment_result": "PASS"}

    monkeypatch.setattr(probe, "prepare", fake_prepare)
    monkeypatch.setattr(probe, "load_prepared", fake_load_prepared)
    monkeypatch.setattr(probe, "execute_review", fake_execute_review)
    monkeypatch.setattr(probe, "_emit", lambda value: emitted.append(dict(value)))

    assert probe.main() == 0

    assert sequence == expected_sequence
    assert emitted[-1]["status"] == expected_status


def test_rejected_saved_handoff_what_if_preserves_every_existing_byte(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    probe = _load_probe()
    prepare_request = _probe_request(
        tmp_path / "local", tmp_path / ".claude", tmp_path / ".codex"
    )
    prepare_request["fixture_root"] = str(tmp_path / "fixture")
    prepare_request["evidence_dir"] = str(tmp_path / "evidence")
    paths = {
        "fixture": Path(prepare_request["fixture_root"]),
        "evidence": Path(prepare_request["evidence_dir"]),
        "live_claude": Path(prepare_request["live_claude_home"]),
        "live_codex": Path(prepare_request["live_codex_home"]),
    }
    probe.prepare(prepare_request, REPO_ROOT, paths)
    (paths["evidence"] / "unexpected.txt").write_text("tamper", encoding="ascii")
    invoke_request = dict(prepare_request)
    invoke_request["action"] = "InvokeSavedHandoff"
    invoke_request["what_if"] = True
    raw = json.dumps(invoke_request, separators=(",", ":")).encode("utf-8")

    def snapshot() -> list[tuple[str, bytes]]:
        return [
            (path.relative_to(tmp_path).as_posix(), path.read_bytes())
            for path in sorted(tmp_path.rglob("*"))
            if path.is_file()
        ]

    before = snapshot()
    monkeypatch.setattr(probe.sys, "stdin", type("Input", (), {"buffer": io.BytesIO(raw)})())
    monkeypatch.setattr(probe, "repository_root", lambda: REPO_ROOT)
    monkeypatch.setattr(probe, "validate_paths", lambda _request, _repo: paths)
    monkeypatch.setattr(
        probe,
        "validate_candidate",
        lambda _request, _repo: {
            "candidate_sha": prepare_request["candidate_sha"],
            "job_helper_sha256": "1" * 64,
            "snapshot_helper_sha256": "2" * 64,
        },
    )

    assert probe.main() == 2

    output = json.loads(capfd.readouterr().out)
    assert output["status"] == "REJECTED"
    assert "unexpected or missing entry" in output["error"]
    assert snapshot() == before
    assert not (paths["evidence"] / "fallback-report.txt").exists()
    assert not (paths["evidence"] / "MANIFEST.sha256").exists()


def test_prepare_creates_a_sealed_host_free_handoff_and_detects_tampering(
    tmp_path: Path,
) -> None:
    probe = _load_probe()
    request = _probe_request(
        tmp_path / "local", tmp_path / ".claude", tmp_path / ".codex"
    )
    fixture = tmp_path / "fixture"
    evidence_dir = tmp_path / "evidence"
    paths = {
        "fixture": fixture,
        "evidence": evidence_dir,
        "live_claude": tmp_path / ".claude",
        "live_codex": tmp_path / ".codex",
    }

    prepared = probe.prepare(request, REPO_ROOT, paths)

    assert prepared["receipt"]["host_started"] is False
    assert prepared["receipt"]["fallback_allowed"] is False
    assert prepared["receipt"]["fixture_root"] == str(fixture.resolve())
    assert prepared["receipt"]["evidence_dir"] == str(evidence_dir.resolve())
    assert prepared["receipt"]["live_claude_home"] == str(paths["live_claude"].resolve())
    assert prepared["receipt"]["live_codex_home"] == str(paths["live_codex"].resolve())
    assert prepared["receipt"]["credential_mode"] == "copy-file"
    assert prepared["receipt"]["reviewer_timeout_seconds"] == 600
    assert prepared["receipt"]["requested_reviewer_model"] == "gpt-5.6-terra"
    assert (fixture / "seeded-repo" / ".git").is_dir()
    assert not (evidence_dir / "reviewer-stdout.txt").exists()
    assert not (evidence_dir / "live-before.json").exists()
    manifest_paths = [
        line.split("  ", 1)[1]
        for line in (evidence_dir / "prepare-manifest.sha256")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert manifest_paths == sorted(
        {
            ".skill-mesh-owner.json",
            "defect-inventory.json",
            "fixture.json",
            "model-policy.json",
            "prepare-receipt.json",
            "response-schema.json",
            "review-request.md",
            "sealed-payload.json",
        }
    )
    loaded = probe.load_prepared(request, paths)
    assert loaded["receipt"] == prepared["receipt"]
    (fixture / "reviewer-runtime").mkdir()
    with pytest.raises(probe.ProbeError, match="prepared fixture contains"):
        probe.load_prepared(request, paths)
    (fixture / "reviewer-runtime").rmdir()
    (evidence_dir / "report.md").write_text("stale report", encoding="utf-8")
    (evidence_dir / "MANIFEST.sha256").write_text("stale manifest", encoding="utf-8")
    with pytest.raises(probe.ProbeError, match="unexpected or missing entry"):
        probe.load_prepared(request, paths)
    (evidence_dir / "report.md").unlink()
    (evidence_dir / "MANIFEST.sha256").unlink()
    changed_runtime = dict(request)
    changed_runtime["reviewer_timeout_seconds"] = 599
    with pytest.raises(probe.ProbeError, match="reviewer_timeout_seconds"):
        probe.load_prepared(changed_runtime, paths)

    response = _review_response()
    runtime = {
        "host": "codex",
        "resolved_model": "gpt-5.6-terra",
        "resolved_status": "provider-reported",
        "resolved_source": "reviewer-stdout.txt::$['model']",
        "executable": REPO_ROOT / "synthetic-codex.exe",
        "executable_sha256": "3" * 64,
        "reviewer_cwd": fixture / "reviewer-runtime" / "empty-cwd",
        "argv": ["--model", "gpt-5.6-terra", "synthetic prompt"],
        "host_started_count": 1,
        "containment": {"root_exit_code": 0},
        "job_helper_sha256": "1" * 64,
        "snapshot_helper_sha256": "2" * 64,
        "latency_seconds": 1.25,
        "token_usage": {"availability": "unavailable"},
        "cost": {"availability": "unavailable"},
        "response_bytes": b"{}\n",
        "stdout_sha256": "4" * 64,
        "stderr_sha256": "5" * 64,
        "live_state_status": "MATCH",
        "live_state_detail": {"changed_paths": []},
    }
    grade = {
        "detected_defect_ids": [],
        "unmatched_findings": [],
        "consistency_warnings": [],
        "counts": {"detected_defect_count": 0},
    }
    identity = {
        "head": loaded["fixture"]["candidate_sha"],
        "tree_sha256": loaded["fixture"]["candidate_tree_sha256"],
        "status": "clean",
    }
    report_values = probe._report_values(
        request=request,
        candidate={"candidate_sha": request["candidate_sha"]},
        prepared=loaded,
        runtime=runtime,
        response=response,
        grade=grade,
        result="PASS",
        failure_reason="synthetic closure test",
        before_identity=identity,
        after_identity=identity,
        cleanup_status="PASS",
        cleanup_detail="synthetic cleanup",
        repo=REPO_ROOT,
        paths=paths,
    )
    assert report_values["DEFECT_INVENTORY_SHA256"] == PINNED_DEFECT_INVENTORY_SHA256
    template = REPORT_TEMPLATE.read_text(encoding="utf-8")
    assert set(report_values) == set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", template))
    rendered_report = probe.render_template(template, report_values)
    assert "{{" not in rendered_report
    assert str(fixture) not in rendered_report
    assert str(evidence_dir) not in rendered_report

    fixture_json = evidence_dir / "fixture.json"
    original_fixture_json = fixture_json.read_bytes()
    changed_fixture = json.loads(original_fixture_json)
    changed_fixture["candidate_tree_sha256"] = "0" * 64
    fixture_json.write_text(json.dumps(changed_fixture), encoding="ascii")
    with pytest.raises(probe.ProbeError, match="fixture.json"):
        probe.load_prepared(request, paths)
    fixture_json.write_bytes(original_fixture_json)

    prepare_manifest = evidence_dir / "prepare-manifest.sha256"
    original_manifest = prepare_manifest.read_bytes()
    manifest_text = original_manifest.decode("utf-8")
    first_digest = manifest_text[:64]
    replacement = ("0" if first_digest[0] != "0" else "1") + first_digest[1:]
    prepare_manifest.write_text(replacement + manifest_text[64:], encoding="utf-8")
    with pytest.raises(probe.ProbeError, match="prepare manifest hash differs"):
        probe.load_prepared(request, paths)
    prepare_manifest.write_bytes(original_manifest)

    seeded_file = fixture / "seeded-repo" / "order_totals.py"
    original_seeded_file = seeded_file.read_bytes()
    seeded_file.write_bytes(original_seeded_file + b"\n# synthetic tamper\n")
    with pytest.raises(probe.ProbeError, match="clean immutable Git commit"):
        probe.load_prepared(request, paths)
    seeded_file.write_bytes(original_seeded_file)

    (evidence_dir / "review-request.md").write_text("tampered", encoding="utf-8")
    with pytest.raises(probe.ProbeError, match="prepared artifact hash differs"):
        probe.load_prepared(request, paths)


@pytest.mark.parametrize(
    ("action", "mechanism"),
    (
        ("Run", "reviewer-only-dispatcher"),
        ("InvokeSavedHandoff", "manual-saved-handoff"),
    ),
    ids=("monolithic-run", "saved-handoff"),
)
def test_main_publishes_ambiguous_failure_when_reviewer_mutates_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
    action: str,
    mechanism: str,
) -> None:
    probe = _load_probe()
    request = _probe_request(
        tmp_path / "local",
        tmp_path / ".claude",
        tmp_path / ".codex",
        action=action,
        mechanism=mechanism,
    )
    request["fixture_root"] = str(tmp_path / "fixture")
    request["evidence_dir"] = str(tmp_path / "evidence")
    request["what_if"] = False
    paths = {
        "fixture": Path(request["fixture_root"]),
        "evidence": Path(request["evidence_dir"]),
        "live_claude": Path(request["live_claude_home"]),
        "live_codex": Path(request["live_codex_home"]),
    }
    real_prepare = probe.prepare
    real_load_prepared = probe.load_prepared
    real_execute_review = probe.execute_review
    if action == "InvokeSavedHandoff":
        prepare_request = dict(request)
        prepare_request["action"] = "Prepare"
        real_prepare(prepare_request, REPO_ROOT, paths)
    inventory_path = paths["evidence"] / "defect-inventory.json"
    sequence: list[str] = []
    reviewer_calls = 0

    def fake_run_reviewer(**_kwargs):
        nonlocal reviewer_calls
        reviewer_calls += 1
        receipt = json.loads(
            (paths["evidence"] / "prepare-receipt.json").read_bytes()
        )
        response = {
            "run_id": request["run_id"],
            "source_sha": receipt["seeded_candidate_sha"],
            "payload_sha256": receipt["payload_sha256"],
            "verdict": "NEEDS_WORK",
            "summary": "Synthetic response reaches the post-review inventory check.",
            "findings": [],
        }
        inventory_path.write_bytes(inventory_path.read_bytes() + b" ")
        return {"response_bytes": probe.canonical_json_bytes(response)}

    inventory_reads: list[Path] = []
    original_read_bounded = probe.read_bounded

    def tracked_read_bounded(path: Path, *args, **kwargs):
        if Path(path) == inventory_path:
            inventory_reads.append(Path(path))
        return original_read_bounded(path, *args, **kwargs)

    grade_called = False

    def forbidden_grade(_response, _inventory):
        nonlocal grade_called
        grade_called = True
        pytest.fail("grading must not run after sealed inventory mutation")

    def tracked_prepare(_request, _repo, _paths):
        sequence.append("prepare")
        return real_prepare(_request, _repo, _paths)

    def tracked_load_prepared(_request, _paths):
        sequence.append("load_prepared")
        return real_load_prepared(_request, _paths)

    def tracked_execute_review(_request, _candidate, _prepared, _repo, _paths):
        sequence.append("execute_review")
        return real_execute_review(
            _request,
            _candidate,
            _prepared,
            _repo,
            _paths,
        )

    monkeypatch.setattr(probe.host_runtime, "run_reviewer", fake_run_reviewer)
    monkeypatch.setattr(probe, "read_bounded", tracked_read_bounded)
    monkeypatch.setattr(probe.review_contract, "grade_response", forbidden_grade)
    monkeypatch.setattr(probe, "prepare", tracked_prepare)
    monkeypatch.setattr(probe, "load_prepared", tracked_load_prepared)
    monkeypatch.setattr(probe, "execute_review", tracked_execute_review)
    monkeypatch.setattr(
        probe.sys,
        "stdin",
        type(
            "Input",
            (),
            {"buffer": io.BytesIO(probe.canonical_json_bytes(request))},
        )(),
    )
    monkeypatch.setattr(probe, "repository_root", lambda: REPO_ROOT)
    monkeypatch.setattr(probe, "validate_paths", lambda _request, _repo: paths)
    monkeypatch.setattr(
        probe,
        "validate_candidate",
        lambda _request, _repo: {
            "candidate_sha": request["candidate_sha"],
            "job_helper_sha256": "1" * 64,
            "snapshot_helper_sha256": "2" * 64,
        },
    )
    monkeypatch.setattr(
        probe,
        "reinvoke_candidate_runtime",
        lambda _raw, _request, _repo: None,
    )

    assert probe.main() == 0

    output = json.loads(capfd.readouterr().out)
    expected_sequence = (
        ["prepare", "load_prepared", "execute_review"]
        if action == "Run"
        else ["load_prepared", "execute_review"]
    )
    assert sequence == expected_sequence
    assert output["status"] == "COMPLETE"
    assert output["experiment_result"] == "AMBIGUOUS"
    assert output["host_started"] is None
    assert output["resolved_status"] == "unavailable"
    assert output["detected_defect_count"] == 0
    assert "fallback_report" not in output

    assert reviewer_calls == 1
    assert inventory_reads == [inventory_path]
    assert grade_called is False
    assert (paths["evidence"] / "candidate-after.json").is_file()
    assert not paths["fixture"].exists()

    report_path = paths["evidence"] / "report.md"
    manifest_path = paths["evidence"] / "MANIFEST.sha256"
    report = report_path.read_text(encoding="utf-8")
    assert output["report"] == str(report_path)
    assert output["manifest"] == str(manifest_path)
    assert "**AMBIGUOUS**" in report
    assert (
        "ProbeError: defect inventory bytes differ from the prepared receipt"
        in report
    )
    assert "Reviewer verdict | `UNCERTAIN`" in report
    assert "Detected seeded defect count | `0`" in report
    assert "Detected seeded defect IDs | []" in report
    assert (
        "The attempt did not produce a trustworthy parsed reviewer result."
        in report
    )
    assert "Synthetic response reaches the post-review inventory check." not in report
    assert not (paths["evidence"] / "fallback-report.txt").exists()

    manifest_lines = manifest_path.read_text(encoding="utf-8").splitlines()
    manifest_entries: dict[str, str] = {}
    for line in manifest_lines:
        assert re.fullmatch(r"[0-9a-f]{64}  [^\r\n]+", line)
        digest, relative = line.split("  ", 1)
        assert relative not in manifest_entries
        manifest_entries[relative] = digest
    retained_files = sorted(
        path.relative_to(paths["evidence"]).as_posix()
        for path in paths["evidence"].rglob("*")
        if path.is_file() and path != manifest_path
    )
    assert list(manifest_entries) == retained_files
    for relative, digest in manifest_entries.items():
        assert (
            hashlib.sha256((paths["evidence"] / relative).read_bytes()).hexdigest()
            == digest
        )
    assert manifest_entries["defect-inventory.json"] == hashlib.sha256(
        inventory_path.read_bytes()
    ).hexdigest()
    assert manifest_entries["defect-inventory.json"] != PINNED_DEFECT_INVENTORY_SHA256


def test_runtime_git_helper_does_not_inherit_ambient_git_redirection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = _load_host_runtime()
    captured: dict[str, object] = {}
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "redirected"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "outside"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "outside-index"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setattr(host.shutil, "which", lambda _: sys.executable)

    def fake_run(*args, **kwargs):
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=b"ok\n", stderr=b""
        )

    monkeypatch.setattr(host.subprocess, "run", fake_run)
    assert host._run_git(tmp_path, "status") == b"ok\n"
    environment = captured["kwargs"]["env"]
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_CONFIG_COUNT"):
        assert name not in environment
    assert environment["GIT_CONFIG_NOSYSTEM"] == "1"
    assert environment["GIT_CONFIG_GLOBAL"] == "NUL"
    assert environment["HOME"] == str(tmp_path / ".git" / "cross-family-read-home")


def test_runtime_attempts_after_snapshot_when_reviewer_invocation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = _load_host_runtime()
    snapshot_calls: list[Path] = []
    monkeypatch.setattr(
        host,
        "validate_helpers",
        lambda _repo, _candidate, _source_root=None: {
            "job": {"path": tmp_path / "job.py", "sha256": "1" * 64},
            "snapshot": {"path": tmp_path / "snapshot.py", "sha256": "2" * 64},
        },
    )
    monkeypatch.setattr(host, "_copy_credential", lambda *args: (tmp_path / "auth", True))
    monkeypatch.setattr(host, "_write_codex_config", lambda *_: None)
    fake_executable = tmp_path / "codex.exe"
    fake_executable.write_bytes(b"synthetic executable")
    monkeypatch.setattr(host, "_resolve_executable", lambda _: fake_executable)
    monkeypatch.setattr(
        host,
        "_host_command",
        lambda *args: (["exec", "synthetic"], tmp_path / "response.json"),
    )
    monkeypatch.setattr(host, "_snapshot_request", lambda *args: {"schema": 1})

    def fake_snapshot(_helper, _request, destination):
        snapshot_calls.append(destination)
        return {"records": []}

    monkeypatch.setattr(host, "take_snapshot", fake_snapshot)
    monkeypatch.setattr(
        host,
        "_invoke_job",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            host.HostRuntimeError("synthetic invocation failure")
        ),
    )
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    fixture_root = tmp_path / "fixture"
    fixture_root.mkdir()

    with pytest.raises(host.HostRuntimeError, match="synthetic invocation failure"):
        host.run_reviewer(
            repo=tmp_path / "repo",
            candidate_sha="a" * 40,
            fixture_root=fixture_root,
            evidence_dir=evidence_dir,
            live_claude_home=tmp_path / ".claude",
            live_codex_home=tmp_path / ".codex",
            direction="claude-to-gpt",
            requested_model="gpt-5.6-terra",
            prompt="synthetic prompt",
            response_schema=RESPONSE_SCHEMA,
            timeout_seconds=10,
        )
    assert snapshot_calls == [
        evidence_dir / "live-before.json",
        evidence_dir / "live-after.json",
    ]


def test_candidate_runtime_materializes_only_committed_allowlisted_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = _load_probe()
    request = _probe_request(
        tmp_path / "local", tmp_path / ".claude", tmp_path / ".codex"
    )
    request["what_if"] = False
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setenv("TEMP", str(tmp_path / "temp"))
    relative = "experiments/recovery/cross-family-fixture/probe.py"
    committed = b"# committed candidate probe\n"

    def fake_git(_repo, *args, allow=(0,)):
        if args[0] == "ls-tree":
            stdout = (relative + "\n").encode("utf-8")
        elif args[0] == "show":
            assert args[1] == f"{request['candidate_sha']}:{relative}"
            stdout = committed
        else:
            raise AssertionError(args)
        return subprocess.CompletedProcess(
            args=["git", *args], returncode=0, stdout=stdout, stderr=b""
        )

    monkeypatch.setattr(probe, "_run_git", fake_git)
    runtime_root = probe._materialize_candidate_runtime(request, repo)
    assert runtime_root == probe.candidate_runtime_root(request)
    assert (runtime_root / relative).read_bytes() == committed
    assert sorted(
        path.relative_to(runtime_root).as_posix()
        for path in runtime_root.rglob("*")
        if path.is_file()
    ) == [".candidate-runtime-owner.json", relative]
    with pytest.raises(probe.ProbeError, match="already exists"):
        probe._materialize_candidate_runtime(request, repo)


def test_candidate_runtime_reinvoke_uses_exported_probe_and_always_removes_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = _load_probe()
    request = _probe_request(
        tmp_path / "local", tmp_path / ".claude", tmp_path / ".codex"
    )
    request["what_if"] = False
    repo = tmp_path / "repo"
    repo.mkdir()
    runtime_root = tmp_path / "candidate-runtime"
    candidate_probe = (
        runtime_root / "experiments/recovery/cross-family-fixture/probe.py"
    )
    candidate_probe.parent.mkdir(parents=True)
    candidate_probe.write_text("raise SystemExit(99)\n", encoding="ascii")
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        probe, "_materialize_candidate_runtime", lambda _request, _repo: runtime_root
    )

    def fake_run(*args, **kwargs):
        captured["args"] = args[0]
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            args=args[0], returncode=7, stdout=b'{"status":"COMPLETE"}\n', stderr=b""
        )

    monkeypatch.setattr(probe.subprocess, "run", fake_run)
    raw_request = json.dumps(request, separators=(",", ":")).encode("utf-8")
    assert probe.reinvoke_candidate_runtime(raw_request, request, repo) == 7
    assert captured["args"] == [
        sys.executable,
        "-I",
        "-B",
        "-c",
        probe.CANDIDATE_BOOTSTRAP,
        str(candidate_probe),
    ]
    assert captured["kwargs"]["input"] == raw_request
    assert captured["kwargs"]["env"]["SKILL_MESH_CROSS_FAMILY_CANDIDATE_STAGE"] == "1"
    assert captured["kwargs"]["env"]["SKILL_MESH_CROSS_FAMILY_REPO_ROOT"] == str(repo)
    assert captured["kwargs"]["stdout"] is subprocess.PIPE
    assert captured["kwargs"]["stderr"] is subprocess.PIPE
    assert not runtime_root.exists()


def test_candidate_runtime_cleanup_failure_never_forwards_child_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    probe = _load_probe()
    request = _probe_request(
        tmp_path / "local", tmp_path / ".claude", tmp_path / ".codex"
    )
    request["what_if"] = False
    runtime_root = tmp_path / "candidate-runtime"
    candidate_probe = runtime_root / "experiments/recovery/cross-family-fixture/probe.py"
    candidate_probe.parent.mkdir(parents=True)
    candidate_probe.write_text("raise SystemExit(0)\n", encoding="ascii")
    monkeypatch.setattr(
        probe, "_materialize_candidate_runtime", lambda _request, _repo: runtime_root
    )
    monkeypatch.setattr(
        probe.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=b'{"status":"COMPLETE"}\n', stderr=b""
        ),
    )
    monkeypatch.setattr(
        probe,
        "_remove_tree_exact",
        lambda _path: (_ for _ in ()).throw(PermissionError("synthetic cleanup refusal")),
    )

    with pytest.raises(probe.ProbeError, match="candidate runtime cleanup failed"):
        probe.reinvoke_candidate_runtime(b"{}", request, tmp_path / "repo")

    captured = capfd.readouterr()
    assert captured.out == ""
    assert runtime_root.is_dir()


def test_owned_cleanup_clears_read_only_files_only_below_exact_root(tmp_path: Path) -> None:
    probe = _load_probe()
    request = _probe_request(
        tmp_path / "local", tmp_path / ".claude", tmp_path / ".codex"
    )
    root = tmp_path / "fixture"
    owner = probe._owner(request, "fixture")
    probe._create_owned(root, owner)
    locked = root / "seeded-repo" / ".git" / "objects" / "synthetic"
    locked.parent.mkdir(parents=True)
    locked.write_bytes(b"read only")
    locked.chmod(0o444)

    status, detail = probe._safe_cleanup(root, owner)

    assert status == "PASS", detail
    assert not root.exists()


def test_baseline_failure_never_copies_a_live_credential(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = _load_host_runtime()
    copy_calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        host,
        "validate_helpers",
        lambda _repo, _candidate, _source_root=None: {
            "job": {"path": tmp_path / "job.py", "sha256": "1" * 64},
            "snapshot": {"path": tmp_path / "snapshot.py", "sha256": "2" * 64},
        },
    )
    monkeypatch.setattr(host, "_resolve_executable", lambda _: tmp_path / "codex.exe")
    monkeypatch.setattr(
        host,
        "_host_command",
        lambda *args: (["exec", "synthetic"], tmp_path / "response.json"),
    )
    monkeypatch.setattr(host, "_discover_reparse_targets", lambda _roots: [])

    def fail_baseline(_helper, _request, _destination):
        raise host.HostRuntimeError("synthetic baseline failure")

    monkeypatch.setattr(host, "take_snapshot", fail_baseline)
    monkeypatch.setattr(
        host,
        "_copy_credential",
        lambda *args: copy_calls.append(args),
    )
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    fixture_root = tmp_path / "fixture"
    fixture_root.mkdir()

    with pytest.raises(host.HostRuntimeError, match="synthetic baseline failure"):
        host.run_reviewer(
            repo=tmp_path / "repo",
            candidate_sha="a" * 40,
            fixture_root=fixture_root,
            evidence_dir=evidence_dir,
            live_claude_home=tmp_path / ".claude",
            live_codex_home=tmp_path / ".codex",
            direction="claude-to-gpt",
            requested_model="gpt-5.6-terra",
            prompt="synthetic prompt",
            response_schema=RESPONSE_SCHEMA,
            timeout_seconds=10,
        )
    assert copy_calls == []
    assert not (evidence_dir / "credential-copy-complete.json").exists()
    assert not (evidence_dir / "review-starting.json").exists()


def test_reviewer_runtime_root_must_be_created_new(tmp_path: Path) -> None:
    host = _load_host_runtime()
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    preexisting = fixture / "reviewer-runtime"
    preexisting.mkdir()
    planted = preexisting / "planted.txt"
    planted.write_text("must survive rejection", encoding="ascii")

    with pytest.raises(host.HostRuntimeError, match="already exists"):
        host._create_disposable_root(fixture)

    assert planted.read_text(encoding="ascii") == "must survive rejection"


def test_codex_resolution_uses_the_single_native_npm_cli_binary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = _load_host_runtime()
    appdata = tmp_path / "appdata"
    native = (
        appdata
        / "npm/node_modules/@openai/codex"
        / "node_modules/@openai/codex-win32-x64"
        / "vendor/x86_64-pc-windows-msvc/bin/codex.exe"
    )
    native.parent.mkdir(parents=True)
    native.write_bytes(b"synthetic native executable")
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setattr(
        host.shutil,
        "which",
        lambda _: (_ for _ in ()).throw(AssertionError("PATH alias must not be used")),
    )

    assert host._resolve_executable("codex") == native.resolve()

    second = (
        appdata
        / "npm/node_modules/@openai/codex"
        / "node_modules/@openai/codex-win32-arm64"
        / "vendor/aarch64-pc-windows-msvc/bin/codex.exe"
    )
    second.parent.mkdir(parents=True)
    second.write_bytes(b"second synthetic executable")
    with pytest.raises(host.HostRuntimeError, match="exactly one native executable"):
        host._resolve_executable("codex")


def test_interrupted_attempt_publishes_ambiguous_and_cleans_only_with_job_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = _load_probe()
    request = _probe_request(
        tmp_path / "local", tmp_path / ".claude", tmp_path / ".codex"
    )
    candidate = {
        "candidate_sha": request["candidate_sha"],
        "job_helper_sha256": "1" * 64,
        "snapshot_helper_sha256": "2" * 64,
    }

    def prepare_case(name: str):
        paths = {
            "fixture": tmp_path / name / "fixture",
            "evidence": tmp_path / name / "evidence",
            "live_claude": tmp_path / ".claude",
            "live_codex": tmp_path / ".codex",
        }
        prepared = probe.prepare(request, REPO_ROOT, paths)
        (paths["evidence"] / "credential-copy-complete.json").write_text(
            '{"schema":1,"copied":true,"exact_in_memory_match":true}\n',
            encoding="ascii",
        )
        (paths["evidence"] / "review-starting.json").write_text(
            '{"schema":1,"host":"codex"}\n', encoding="ascii"
        )
        (paths["evidence"] / "invocation-plan.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "host": "codex",
                    "executable": str(paths["fixture"] / "reviewer-runtime" / "codex.exe"),
                    "executable_sha256": "3" * 64,
                    "argv": ["--model", "gpt-5.6-terra"],
                    "cwd": str(paths["fixture"] / "reviewer-runtime" / "empty-cwd"),
                    "requested_model": "gpt-5.6-terra",
                    "fallback_allowed": False,
                },
                separators=(",", ":"),
            )
            + "\n",
            encoding="ascii",
        )
        return paths, prepared

    unsafe_paths, unsafe_prepared = prepare_case("unsafe")
    unsafe = probe.publish_ambiguous_failure(
        request=request,
        candidate=candidate,
        prepared=unsafe_prepared,
        error=RuntimeError("synthetic interruption after credential copy"),
        repo=REPO_ROOT,
        paths=unsafe_paths,
    )
    unsafe_report = Path(unsafe["report"]).read_text(encoding="utf-8")
    assert unsafe["experiment_result"] == "AMBIGUOUS"
    assert "**AMBIGUOUS**" in unsafe_report
    assert "synthetic interruption after credential copy" in unsafe_report
    assert "zero active reviewer processes was not proved" in unsafe_report
    assert "Reviewer process starts | `unavailable`" in unsafe_report
    assert "<FIXTURE_ROOT>" in unsafe_report
    assert "codex.exe" in unsafe_report
    assert '"gpt-5.6-terra"' in unsafe_report
    assert unsafe_paths["fixture"].is_dir()
    assert Path(unsafe["manifest"]).is_file()
    assert unsafe["host_started"] is None

    safe_paths, safe_prepared = prepare_case("safe")
    (safe_paths["evidence"] / "containment.json").write_text(
        json.dumps(
            {
                "target_started": True,
                "job_empty_confirmed": True,
                "root_exit_code": 137,
                "duration_seconds": 0.5,
            },
            separators=(",", ":"),
        )
        + "\n",
        encoding="ascii",
    )
    snapshot_payload = '{"records":[],"schema":1,"status":"COMPLETE"}\n'
    for name in ("live-before.json", "live-after.json"):
        (safe_paths["evidence"] / name).write_text(
            snapshot_payload,
            encoding="ascii",
        )
    snapshot_read_bounds: list[tuple[str, int | None]] = []
    real_read_bounded = probe.read_bounded

    def capture_read_bound(path: Path, *args, **kwargs) -> bytes:
        if path.name in {"live-before.json", "live-after.json"}:
            maximum = args[0] if args else kwargs.get("maximum")
            snapshot_read_bounds.append((path.name, maximum))
        return real_read_bounded(path, *args, **kwargs)

    monkeypatch.setattr(probe, "read_bounded", capture_read_bound)
    safe = probe.publish_ambiguous_failure(
        request=request,
        candidate=candidate,
        prepared=safe_prepared,
        error=RuntimeError("synthetic contained interruption"),
        repo=REPO_ROOT,
        paths=safe_paths,
    )
    safe_report = Path(safe["report"]).read_text(encoding="utf-8")
    assert safe["experiment_result"] == "AMBIGUOUS"
    assert "Reviewer root exit code | `137`" in safe_report
    assert "Cleanup status | `PASS`" in safe_report
    assert safe["host_started"] is True
    assert not safe_paths["fixture"].exists()
    assert snapshot_read_bounds == [
        ("live-before.json", 64 * 1024 * 1024),
        ("live-after.json", 64 * 1024 * 1024),
    ]

    collision_paths, collision_prepared = prepare_case("collision")
    (collision_paths["evidence"] / "report.md").write_text(
        "existing non-ambiguous report", encoding="utf-8"
    )
    with pytest.raises(probe.ProbeError, match="existing final artifact"):
        probe.publish_ambiguous_failure(
            request=request,
            candidate=candidate,
            prepared=collision_prepared,
            error=RuntimeError("synthetic post-report interruption"),
            repo=REPO_ROOT,
            paths=collision_paths,
        )
