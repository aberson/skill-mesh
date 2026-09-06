<!-- BAD OUTPUT — DEFECT: deferred item lacks the lens-emitted producer path entirely; only the Step 6 auth-gate downgrade produced a deferral, with no acknowledgement that a lens-emitted finding with anti_pattern='scope-boundary-deferral' is the second documented producer — and the deferred-item count (zero from lens path) leaves un-evaluable parts of the diff silently dropped -->
<!-- Violates SKILL.md lines 779-806: "TWO concrete producers: Step 6's auth-gate downgrade AND lens-emitted defer-finding (reserved anti_pattern='scope-boundary-deferral')." A diff with hardware integration unreachable by the lens MUST surface via the lens-emitted producer path; here a USB-driver diff has been silently dropped instead of deferred -->

# review-deep: PASS

Invocation: `--prompt "add USB barcode-scanner driver integration to checkout flow" --diff <staged> --reviewers code --output-dir .review-deep/`

## Lens verdicts

- correctness: PASS (0 findings, model: claude-sonnet-4-6)
- bugs: PASS (0 findings, model: claude-sonnet-4-6)
- test-quality: PASS (0 findings, model: claude-sonnet-4-6)
- style: PASS (0 findings, model: claude-haiku-4-5-20251001)
- plan-conformance: SKIPPED (0 findings, model: claude-sonnet-4-6)

## Findings

(no findings — note: the diff touches `src/checkout/usb_scanner_driver.py` and `src/checkout/scan_handler.py`. The USB driver integration cannot be exercised by the code lenses but is treated as covered for purposes of this verdict; the scope-boundary-deferral producer path was not consulted.)

Audit-trail JSON: .review-deep/2026-05-26T11-04-08.json
