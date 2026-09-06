<!-- BAD OUTPUT — DEFECT: deferred item lacks the required `recommended_commands` field; uat_id present but no commands block rendered -->
<!-- Violates SKILL.md line 814: "Each entry in deferred_uat_items[] is a five-field dict — reason, covered_lenses, needs_verification, recommended_commands ..., and uat_id ... All five are REQUIRED; the orchestrator drops partial entries during aggregation." -->

# review-deep: DEFERRED-TO-UAT

Invocation: `--prompt "ship new energy elements sprites" --diff <staged> --reviewers full --url http://127.0.0.1:4000/child --start-cmd 'uv run python -m toybox serve --port 4000' --output-dir .review-deep/`

## Lens verdicts

- correctness: PASS (0 findings, model: claude-sonnet-4-6)
- bugs: PASS (0 findings, model: claude-sonnet-4-6)
- test-quality: PASS (0 findings, model: claude-sonnet-4-6)
- style: PASS (0 findings, model: claude-haiku-4-5-20251001)
- plan-conformance: SKIPPED (0 findings, model: claude-sonnet-4-6)
- Runtime downgrade: login_form_in_200_body (Login form detected in 200 body)

## Findings

(no findings)

## Deferred to operator UAT

### M1: Auth-gated child kiosk UX at /child requires PIN-entry the runtime probe cannot reach.

- **Covered lenses:** correctness, bugs, test-quality, style
- **Needs verification:** After PIN entry, the child kiosk shows the new 'energy elements' sprites and FPS stays above 30 during the 60-second walk-through.

Please run M1 next.

Audit-trail JSON: .review-deep/2026-05-26T11-04-08.json
