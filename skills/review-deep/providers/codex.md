# review-deep - Codex entry point

See [../core.md](../core.md) for the full specification. Load it in full.

## Code-lens capability mapping

This is the Phase CD source mapping restoring the DS-D3 gap. It is **unqualified
until Step 156** demonstrates the installed route and refreshes the intended profile.
It makes no provider-wide support claim. Only `--reviewers code` is mapped here;
`runtime`, `full`, or unavailable required resources halt `required_tool_missing`.

| Contract field | Required Codex mapping |
|---|---|
| `capability-probe` | Load the installed build-step Agent-isolation capability contract and build-phase Parent-state capability contract, including Conversation challenge v2, in full. Require their non-mutating probes in this session before lens dispatch: explicit no-history dispatch, calibrated conversation comparisons, opaque parent state, caller-scoped parent-only verdict service and tamper/key-rotation checks. A host that passes may dispatch the code lenses as fresh siblings. Probe absence, failure or inconclusive evidence halts visibly with `required_tool_missing` at isolated lens dispatch; an ordinary Codex CLI without these capabilities remains unsupported. |
| `six-siblings` | The review parent directly spawns correctness, bugs, security, test-quality, style, plan-conformance as six distinct fresh sibling children with `fork_turns="none"`. Use available-slot batches, releasing completed children before the next batch. No reused child, no child-spawned reviewer, no producer-to-reviewer follow-up, no omitted/default fork mode. Each receives the identical immutable diff/intent/context snapshot and its own core lens instructions. Never pass sibling findings or producer reasoning. |
| `read-only` | All lens prompts are read-only: inspect named project/worktree files and return one JSON LensVerdict with cited evidence and recommendations only. No edits, commands that mutate the target, commits, installs or child dispatch. Snapshot project/worktree bytes before dispatch and audit after each batch; reject unexpected reviewer mutation. Shared filesystem/tools are expected, not OS isolation. |
| `parent-authority` | Parent runs the mechanical phase first, collects evidence, validates the complete raw lens set before any loader can overwrite duplicate lens IDs, and alone invokes the installed deterministic reducer. No child aggregates or signs. Missing, duplicate, extra, malformed or incomplete lens sets are non-passing NEEDS-WORK. UNCERTAIN remains non-passing escalation. Never infer PASS from absent evidence. |
| `private-channel` | Never pass the verdict path, run id, HMAC key or parent service handle to lenses in prompts, arguments, environment, files, logs or reports. The parent-only verdict service separately authenticates the enclosing build-step result; the review-deep JSON audit is unsigned and cannot authorize advancement. Shared filesystem discovery or tampering can force BLOCKED, never authenticate PASS. |
| `plan-binding` | Codex build-phase loads build-step under the same parent context, which already holds the parsed plan path and integer step id. Before deep review, bind `plan_step` to the resolved absolute plan path (forward slashes) plus `:<id>` and pass that exact string and extracted step to review-deep. Verify the plan exists and step resolves; a known phase step must never become null or SKIPPED. Standalone invocation without a plan retains the core's plan-conformance SKIPPED rule, with the sixth fresh lens returning that explicit record. |

Resolve capability roles from the loaded package's `<loaded-package>/config/model-tier-map.md`, whose
single fenced JSON payload matches canonical `config/model-tier-map.json`. Explicit
overrides win; unavailable required capability returns `required_tool_missing`.
The map declares no Codex peer: use the closest capability actually provided by the
configured Codex model without weakening a gate. No automatic model/host fallback.

## Parent aggregation from the installed package

Use the following parent-only call pattern with the loaded package's absolute path.
The existing CLI hardcodes `plan_step=None`; the existing library API carries the
exact binding, prior-sidecar, lint findings and resolved invocation metadata. Do not
rewrite the helper or edit its output to insert metadata. Keep raw reports separately
for audit. Parse each direct child's entire JSON response, with no fences or duplicate
keys. Validate all six before calling `aggregate`; do not use `load_lens_verdicts`,
whose ID dictionary would hide duplicates. This block is an invocation recipe, not a
new helper installed into the project.

```python
import importlib.util
import json
import re
import sys
from pathlib import Path

def aggregate_code_review(package, reports, *, plan_step, invocation, timestamp,
                          output_dir, prior_sidecar=None, lint_findings_path=None):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("NEEDS-WORK: duplicate JSON key")
            result[key] = value
        return result

    def read_json(text):
        return json.loads(text, object_pairs_hook=unique_object)

    module_path = Path(package) / "scripts" / "aggregate.py"
    spec = importlib.util.spec_from_file_location("review_deep_aggregate", module_path)
    reducer = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = reducer
    spec.loader.exec_module(reducer)
    lenses = [read_json(report) for report in reports]
    expected = reducer.CODE_LENS_ORDER
    if (len(lenses) != len(expected) or any(not isinstance(v, dict) for v in lenses)
            or sorted(v.get("lens_id", "") for v in lenses) != sorted(expected)):
        raise ValueError("NEEDS-WORK: incomplete, duplicate or unexpected lens set")
    for lens in lenses:
        for key in ("model_tier", "authority", "coverage_claim", "overall_verdict"):
            if not isinstance(lens.get(key), str) or not lens[key].strip():
                raise ValueError("NEEDS-WORK: malformed lens")
        if lens["model_tier"] not in {"haiku", "sonnet", "opus"}:
            raise ValueError("NEEDS-WORK: invalid tier")
        verdict = lens["overall_verdict"]
        if verdict in {"UNCERTAIN", "NEEDS-CLARIFICATION"}:
            # The unchanged reducer cannot safely represent these states today.
            raise ValueError(verdict + ": preserve raw evidence; escalate, never PASS")
        if verdict not in {"PASS", "NEEDS-WORK", "FAILED", "NO-EVIDENCE", "SKIPPED"}:
            raise ValueError("NEEDS-WORK: invalid verdict")
        if verdict == "SKIPPED" and (lens["lens_id"] != "plan-conformance" or plan_step is not None):
            raise ValueError("NEEDS-WORK: required lens skipped")
        if verdict == "FAILED" and lens.get("failure_reason") != "model_overloaded":
            raise ValueError("NEEDS-WORK: invalid failure reason")
        if not isinstance(lens.get("findings"), list):
            raise ValueError("NEEDS-WORK: missing findings")
        for finding in lens["findings"]:
            if (not isinstance(finding, dict) or finding.get("severity") not in {"Block", "Nit", "FYI"}
                    or any(not isinstance(finding.get(k), str) for k in ("file_line", "excerpt", "rationale"))):
                raise ValueError("NEEDS-WORK: malformed finding")
        if verdict == "PASS" and any(finding["severity"] in {"Block", "Nit"} for finding in lens["findings"]):
            raise ValueError("NEEDS-WORK: PASS lens has retained Block or Nit findings")
        if verdict == "SKIPPED" and lens["findings"]:
            raise ValueError("NEEDS-WORK: skipped lens has findings")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}", timestamp):
        raise ValueError("NEEDS-WORK: invalid audit timestamp")
    if plan_step is not None and (not isinstance(plan_step, str) or not re.fullmatch(r".+:[0-9]+", plan_step)):
        raise ValueError("NEEDS-WORK: invalid plan binding")
    required_metadata = {"reviewers_flag", "model_overrides", "force_runtime", "url", "start_cmd",
                         "runtime_downgraded", "runtime_downgrade_reason"}
    if (not isinstance(invocation, dict) or set(invocation) != required_metadata
            or invocation["reviewers_flag"] != "code"):
        raise ValueError("NEEDS-WORK: missing resolved invocation metadata")
    prior = read_json(Path(prior_sidecar).read_text(encoding="utf-8")) if prior_sidecar else None
    # Match CLI lint discovery without losing the explicit override.
    lint_path = Path(lint_findings_path) if lint_findings_path else next(
        (p for p in (Path(output_dir) / "lint-findings.json", Path(".review-deep/lint-findings.json"))
         if p.is_file()), None)
    sidecar = reducer.aggregate(
        sorted(lenses, key=lambda v: expected.index(v["lens_id"])),
        timestamp=timestamp, skill_version="v3", plan_step=plan_step,
        invocation=invocation, prior_sidecar=prior,
        lint_findings=reducer.load_lint_findings(lint_path))
    path = reducer.write_sidecar(sidecar, Path(output_dir))
    return path, sidecar, reducer.render_markdown(sidecar)
```

Any parse, validation, resource or execution failure is non-passing; preserve the
raw evidence and report the concrete failure. UNCERTAIN and NEEDS-CLARIFICATION
stop before this reducer because its current implementation can otherwise return
PASS for them. This limitation does not authorize invented findings, rewritten
results or changed reducer semantics. Apply the core's evidence-free finding
filter and anti-pattern validity rules before this call; preserve cited findings
and the seven rules unchanged. The parent reports the returned result verbatim.

For an enclosing build step, only after all build-step gates, cleanup and stash
restoration succeed does the parent service write/classify its separate terminal
verdict. No audit file, lens prose or report substitutes for that classification.
Keep prior-sidecar comparison and oscillation reporting from the core intact.

## Unsupported capabilities and output normalization

Claude Artifact actions, session/scratchpad paths, Agent/Workflow tools and deep
links remain unavailable without an explicit adapter. Runtime/full review and
installed calibration are not qualified here. Missing individual mechanical tools
remain the core's `MISSING-TOOL` warning-and-skip, never a skipped mechanical phase.
On timeout, rate limit, provider 5xx or parse failure preserve the router reason and
shared retry limit. Return only decisions, cited evidence, commands, structured
artifacts and the closing report; never hidden chain-of-thought or private material.
