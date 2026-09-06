<!-- BAD OUTPUT — DEFECT: overload silently falls back to a different tier instead of surfacing FAILED + failure_reason='model_overloaded' -->
<!-- Violates SKILL.md lines 524-545: "an overloaded lens always surfaces as overall_verdict='FAILED' with failure_reason='model_overloaded'; the operator must explicitly re-invoke with --model-override to retry on a different tier" — silent substitution is exactly the anti-pattern called out -->

# review-deep: PASS

Invocation: `--prompt "add ISO 8601 parser" --diff <staged> --reviewers code --output-dir .review-deep/`

Note: bugs lens Sonnet 4.6 returned 529 twice; silently retried on Haiku 4.5 and proceeded with the haiku result.

## Lens verdicts

- correctness: PASS (0 findings, model: claude-sonnet-4-6)
- bugs: PASS (0 findings, model: claude-haiku-4-5-20251001) [fallback from sonnet after overload]
- test-quality: PASS (0 findings, model: claude-sonnet-4-6)
- style: PASS (0 findings, model: claude-haiku-4-5-20251001)
- plan-conformance: SKIPPED (0 findings, model: claude-sonnet-4-6)

## Findings

(no findings)

Audit-trail JSON: .review-deep/2026-05-26T11-04-08.json
