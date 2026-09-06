<!-- BAD OUTPUT — DEFECT: aggregator counts a SKIPPED lens toward NEEDS-WORK (verdict cited "plan-conformance SKIPPED" as a reason for NEEDS-WORK) -->
<!-- Violates SKILL.md lines 604 (rule 3 SKIPPED-handling): "plan-conformance SKIPPED when --plan-step absent; included in lens_verdicts[] for trace completeness, does NOT downgrade aggregated_verdict.result" -->

# review-deep: NEEDS-WORK

Invocation: `--prompt "fix off-by-one in clamp_score" --diff <staged> --reviewers code --output-dir .review-deep/`

Rationale: plan-conformance SKIPPED counted toward NEEDS-WORK (no --plan-step provided); style PASS; bugs PASS; correctness PASS; test-quality PASS.

## Lens verdicts

- correctness: PASS (0 findings, model: claude-sonnet-4-6)
- bugs: PASS (0 findings, model: claude-sonnet-4-6)
- test-quality: PASS (0 findings, model: claude-sonnet-4-6)
- style: PASS (0 findings, model: claude-haiku-4-5-20251001)
- plan-conformance: SKIPPED (0 findings, model: claude-sonnet-4-6)

## Findings

(no findings)

Audit-trail JSON: .review-deep/2026-05-26T11-04-08.json
