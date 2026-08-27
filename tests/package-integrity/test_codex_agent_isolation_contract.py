"""Codex fresh-context and verdict-authority contract gate.

The Codex host surface is capability-conditioned: some hosts expose a proven
no-history child dispatch while ordinary CLI hosts do not.  These tests keep the
adapter from freezing either observation into a provider-wide claim.  They also
hold the independent parent-private HMAC requirement apart from conversational
freshness; sharing a filesystem or tool catalog proves neither one.

The gate deliberately parses named Markdown table rows.  Those row names are the
stable authored contract surface; prose outside them may evolve freely.  Its
planted negatives prove that this lexical gate rejects the representative prose
regressions it names.  Runtime capability is established separately by the
adapter's live, non-mutating host acceptance probe -- this test does not simulate
or claim to prove a host tool boundary.
"""

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_STEP = REPO_ROOT / "skills" / "build-step" / "providers" / "codex.md"
BUILD_PHASE = REPO_ROOT / "skills" / "build-phase" / "providers" / "codex.md"
VERDICT_HELPER = REPO_ROOT / "_shared" / "build_step_verdict.py"
PROVIDER_GUIDE = REPO_ROOT / "documentation" / "providers" / "codex.md"
PROVIDER_MATRIX = REPO_ROOT / "documentation" / "providers" / "README.md"
COMPLETION_PLAN = REPO_ROOT / "documentation" / "phase-is-completion-plan.md"


def _section(text, heading, level=2):
    marker = f"{'#' * level} {heading}"
    lines = text.splitlines()
    assert marker in lines, f"missing contract heading: {marker}"
    start = lines.index(marker) + 1
    end_prefix = f"{'#' * level} "
    end = next(
        (index for index in range(start, len(lines))
         if lines[index].startswith(end_prefix)),
        len(lines),
    )
    return "\n".join(lines[start:end])


def _contract_rows(text, heading):
    """Return the first-column backtick key -> second-column Markdown row."""
    rows = {}
    for line in _section(text, heading).splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 2 or not cells[0].startswith("`"):
            continue
        rows[cells[0].strip("`")] = cells[1]
    return rows


def _missing_tokens(rows, requirements):
    defects = []
    missing_rows = set(requirements) - set(rows)
    extra_rows = set(rows) - set(requirements)
    defects.extend(f"missing row {name!r}" for name in sorted(missing_rows))
    defects.extend(f"unexpected row {name!r}" for name in sorted(extra_rows))
    for row_name, tokens in requirements.items():
        if row_name not in rows:
            continue
        lowered = rows[row_name].lower()
        for token in tokens:
            if token.lower() not in lowered:
                defects.append(f"{row_name!r} lacks {token!r}")
    return defects


STEP_REQUIREMENTS = {
    "fresh-context-dispatch": (
        'fork_turns="none"',
        "non-mutating probe",
        "never infer",
    ),
    "child-topology": (
        "parent directly spawns",
        "separate sibling",
        "no child-spawned reviewer",
        "no producer-to-reviewer follow-up",
        "no reused child",
        "no omitted/default fork mode",
    ),
    "shared-filesystem-tools": (
        "permitted",
        "not os isolation",
        "context and authority",
    ),
    "review-authority": (
        "recommendations only",
        "parent applies",
        "write_verdict",
        "parent-only verdict service",
        "read-only",
        "audit",
        "reject unexpected reviewer mutation",
    ),
    "verdict-channel": (
        "verdict path",
        "run id",
        "hmac key",
        "service handle",
        "never passed to children",
        "ambiently discoverable",
        "cannot authenticate advancement",
        "do not claim path secrecy",
    ),
    "missing-capability": (
        "probe is inconclusive",
        "required_tool_missing",
        "ordinary codex cli",
    ),
}

PHASE_REQUIREMENTS = {
    "fresh-context-gate": (
        "build-step",
        "required for every developer/reviewer arm",
        "does not waive or replace",
    ),
    "private-state-gate": (
        "opaque parent-resident",
        "fresh hmac key on every successful `open`",
        "without ever emitting",
        "`cleanup` clears that key",
        "closes the service after each code step",
        "never serialized",
        "tool argument",
        "environment variable",
        "file",
        "log",
        "separately from sign/write usability",
    ),
    "verdict-service-gate": (
        "for each code step, parent `exec_command` starts a new `python -u build_step_verdict.py --service`",
        "skill-mesh/build-step-verdict-service/v1",
        "generates the key internally",
        "closed, length-bounded json-lines request schema",
        "never evaluates request text as python",
        "parent `write_stdin` sends json-serialized",
        "no key, signature, or signed payload",
        "handle as caller-scoped",
        "fresh child explicitly given",
        "rejected by `write_stdin`",
        "same parent context",
        "required_tool_missing",
    ),
    "external-sidecar-gate": (
        "platform temp directory",
        "outside the repository and producer worktree",
        "not passed its path",
        "discoverable",
        "classify blocked",
        "parent service alone",
        "unconditionally removes",
    ),
    "support-matrix": (
        "fresh=yes,private=yes,service=yes",
        "supported",
        "fresh=no,private=*,service=*",
        "fresh=yes,private=no,service=*",
        "fresh=yes,private=yes,service=no",
        "required_tool_missing",
        "shared-filesystem=yes",
        "changes none",
    ),
    "final-verdict-authority": (
        "parent only",
        "write_verdict",
        "classify_verdict",
        "authenticated classification",
        "cleanup",
        "service termination",
        "`close` is mandatory before the next code step",
        "starts a new service",
        "never prose-parse",
    ),
}

PROBE_REQUIREMENTS = (
    'fork_turns="none"',
    "parent `exec_command`",
    "parent `write_stdin`",
    "python -u build_step_verdict.py --service",
    "exact ready schema",
    "random hmac key",
    "never prints it",
    "only as json objects",
    "never interpolate",
    "give its numeric execution-session handle",
    "reject that child's",
    "non-inheritance or non-enumerability alone is insufficient",
    "separate siblings",
    "parent canary",
    "candidate-service handle",
    "other sibling's nonce",
    "schema-valid `open`, `write`, and `classify`",
    "python-looking syntax",
    "stored only as data",
    "corrupt",
    "fail closed",
    "child prose is never an input",
    "send `cleanup` and `close`",
    "second `open` with the same probe run id",
    "per-open key rotation",
    "probe sidecar is absent",
    "child-accessible",
    "inconclusive result means `required_tool_missing`",
)


def _adapter_defects(build_step_text, build_phase_text):
    step_rows = _contract_rows(build_step_text, "Agent-isolation capability contract")
    phase_rows = _contract_rows(build_phase_text, "Parent-state capability contract")
    defects = _missing_tokens(step_rows, STEP_REQUIREMENTS)
    defects.extend(_missing_tokens(phase_rows, PHASE_REQUIREMENTS))

    forbidden = {
        'fork_turns="all"': "inherited-history dispatch",
        "producer may spawn the reviewer": "producer-owned reviewer",
        "reused child is allowed": "reused producer/reviewer context",
        "children may receive the key": "child-visible HMAC key",
        "may be passed to children": "child-visible verdict channel",
        "they are os isolation": "filesystem mistaken for OS isolation",
        "reviewer calls write_verdict": "reviewer-owned signing",
        "reviewer calls classify_verdict": "reviewer-owned final classification",
        "while emitting its value": "emitted HMAC key",
        "inside the repository and producer worktree": "worktree verdict sidecar",
    }
    combined = f"{build_step_text}\n{build_phase_text}".lower()
    for token, label in forbidden.items():
        if token.lower() in combined:
            defects.append(label)
    return defects


def test_codex_adapters_encode_the_capability_conditioned_contract():
    defects = _adapter_defects(
        BUILD_STEP.read_text(encoding="utf-8"),
        BUILD_PHASE.read_text(encoding="utf-8"),
    )
    assert not defects, "Codex adapter contract drift:\n  " + "\n  ".join(defects)


def _probe_defects(build_phase_text):
    probe = _section(build_phase_text, "Non-mutating host acceptance probe")
    lowered = " ".join(probe.lower().split())
    return [
        token for token in PROBE_REQUIREMENTS
        if " ".join(token.lower().split()) not in lowered
    ]


def test_host_acceptance_probe_is_executable_and_fail_closed():
    defects = _probe_defects(BUILD_PHASE.read_text(encoding="utf-8"))
    assert not defects, "host acceptance probe lacks: " + ", ".join(defects)


@pytest.mark.parametrize(
    ("target", "old", "new"),
    [
        ("step", 'fork_turns="none"', 'fork_turns="all"'),
        ("step", "no reused child", "reused child is allowed"),
        ("step", "they are not OS isolation", "they are OS isolation"),
        ("step", "recommendations only", "final verdicts"),
        ("step", "are never passed to children", "may be passed to children"),
        ("step", "or the probe is inconclusive", "and a successful probe exists"),
        ("phase", "required for every developer/reviewer arm", "optional for every developer/reviewer arm"),
        ("phase", "without ever emitting its value", "while emitting its value"),
        ("phase", "fresh HMAC key on every successful `open`", "one HMAC key for every `open`"),
        ("phase", "parent `exec_command` starts", "reviewer `exec_command` starts"),
        ("phase", "outside the repository and producer worktree", "inside the repository and producer worktree"),
        ("phase", "fresh=yes,private=yes,service=no", "fresh=yes,private=yes,service=yes-again"),
        ("phase", "Parent only calls", "Reviewer calls classify_verdict; parent later calls"),
    ],
)
def test_contract_gate_rejects_planted_authority_regressions(target, old, new):
    step_text = BUILD_STEP.read_text(encoding="utf-8")
    phase_text = BUILD_PHASE.read_text(encoding="utf-8")
    original = step_text if target == "step" else phase_text
    assert old in original, f"planted-negative anchor moved: {old!r}"
    mutated = original.replace(old, new, 1)
    if target == "step":
        step_text = mutated
    else:
        phase_text = mutated
    assert _adapter_defects(step_text, phase_text), (
        f"contract gate accepted planted regression {new!r}"
    )


def test_probe_gate_rejects_an_inconclusive_probe_that_continues():
    text = BUILD_PHASE.read_text(encoding="utf-8")
    old = "inconclusive result means `required_tool_missing`"
    assert old in text
    mutated = text.replace(old, "inconclusive result may continue", 1)
    assert _probe_defects(mutated)


def test_probe_gate_rejects_noninheritance_without_caller_scope():
    text = BUILD_PHASE.read_text(encoding="utf-8")
    old = "reject that child's"
    assert old in text
    mutated = text.replace(old, "allow that child's", 1)
    assert _probe_defects(mutated)


def _helper_defects(text):
    required = (
        "passes only the verdict path and run id to `/build-step`",
        "retains the HMAC key in opaque parent state",
        "`--service` mode in a caller-scoped",
        "strict JSON-lines request",
        "are never passed to developer or reviewer children",
        "might discover or alter the sidecar",
    )
    normalized = " ".join(text.split())
    defects = [token for token in required if token not in normalized]
    if "passes all three to `/build-step`" in normalized:
        defects.append("helper says the key crosses dispatch")
    return defects


def test_verdict_helper_documents_that_the_hmac_key_never_crosses_dispatch():
    defects = _helper_defects(VERDICT_HELPER.read_text(encoding="utf-8"))
    assert not defects, defects


def test_verdict_helper_gate_rejects_child_key_dispatch_wording():
    text = VERDICT_HELPER.read_text(encoding="utf-8")
    old = "are never passed to developer or reviewer children"
    assert old in text
    mutated = text.replace(old, "may be passed to developer or reviewer children", 1)
    assert _helper_defects(mutated)


GUIDE_REQUIREMENTS = (
    "capability-conditioned",
    "fresh-context dispatch",
    "opaque parent",
    "ordinary CLI",
    "parent-only sign/write service",
)
MATRIX_REQUIREMENTS = (
    "capability-conditioned",
    "fresh-context host",
    "ordinary CLI",
    "opaque parent state",
    "parent-only verdict service",
)
STALE_DOC_CLAIMS = (
    "13 skills halt instead of running",
    "every dispatched `/build-step` halts here",
    "no isolated fresh-context primitive: 12 halt",
)


def _provider_doc_defects(guide, matrix):
    defects = []
    for required in GUIDE_REQUIREMENTS:
        if required.lower() not in guide.lower():
            defects.append(f"guide lacks {required!r}")
    for required in MATRIX_REQUIREMENTS:
        if required.lower() not in matrix.lower():
            defects.append(f"matrix lacks {required!r}")
    for stale_claim in STALE_DOC_CLAIMS:
        if stale_claim in guide:
            defects.append(f"guide retains {stale_claim!r}")
        if stale_claim in matrix:
            defects.append(f"matrix retains {stale_claim!r}")
    return defects


def test_active_provider_docs_are_capability_conditioned_not_frozen_to_one_host():
    guide = PROVIDER_GUIDE.read_text(encoding="utf-8")
    matrix = PROVIDER_MATRIX.read_text(encoding="utf-8")
    defects = _provider_doc_defects(guide, matrix)
    assert not defects, defects


@pytest.mark.parametrize(
    ("path", "required"),
    [
        (PROVIDER_GUIDE, "parent-only sign/write service"),
        (PROVIDER_MATRIX, "parent-only verdict service"),
    ],
)
def test_provider_doc_gate_rejects_a_deleted_capability_boundary(path, required):
    guide = PROVIDER_GUIDE.read_text(encoding="utf-8")
    matrix = PROVIDER_MATRIX.read_text(encoding="utf-8")
    original = guide if path == PROVIDER_GUIDE else matrix
    assert required in original
    mutated = original.replace(required, "generic service", 1)
    if path == PROVIDER_GUIDE:
        guide = mutated
    else:
        matrix = mutated
    assert _provider_doc_defects(guide, matrix)


C0R_PATHS = (
    "skills/build-step/providers/codex.md",
    "skills/build-phase/providers/codex.md",
    "tests/package-integrity/test_codex_agent_isolation_contract.py",
    "_shared/build_step_verdict.py",
    "_shared/test_build_step_verdict.py",
    "documentation/providers/codex.md",
    "documentation/providers/README.md",
)


def _c0r_inventory_defects(text):
    defects = [path for path in C0R_PATHS if f"`{path}`" not in text]
    if "require no diff for this Codex-only adapter change" not in text:
        defects.append("missing representative-report no-diff gate")
    return defects


def test_c0r_inventory_names_every_active_contract_surface():
    text = _section(
        COMPLETION_PLAN.read_text(encoding="utf-8"),
        "Completion Stage C0R: Repair canonical adapter drift when authorized",
        level=3,
    )
    defects = _c0r_inventory_defects(text)
    assert not defects, defects
    assert "only Claude/GPT adapters" in COMPLETION_PLAN.read_text(encoding="utf-8")


def test_c0r_inventory_gate_rejects_a_deleted_active_doc_surface():
    text = _section(
        COMPLETION_PLAN.read_text(encoding="utf-8"),
        "Completion Stage C0R: Repair canonical adapter drift when authorized",
        level=3,
    )
    required = "`documentation/providers/codex.md`"
    assert required in text
    assert _c0r_inventory_defects(text.replace(required, "", 1))
