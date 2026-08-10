# judge-ui GPT vision calibration notes

## Rubric anchors

The GPT vision path uses the anchors required by [`judge-core.md`](../../_shared/judge-core.md) section 4. Each stage is scored independently on a low-cardinality scale:

- **PASS** - every observable rubric criterion is visible, mechanical checks passed, and screenshot values agree with the out-of-band read-back. Cite both sources.
- **FAIL** - at least one observable criterion is contradicted by pixels, a mechanical gate failed, or pixels disagree with read-back. Cite the exact contradiction.
- **UNCERTAIN / ESCALATE** - required pixels are illegible, occluded, ambiguous, or confidence is insufficient to choose PASS/FAIL from the anchors. Never coerce this to PASS.

Worked anchors: a table whose visible seven rows and names match an API count/name list is PASS; a polished table showing six rows against API count seven is FAIL; a cropped table where the final row cannot be seen is UNCERTAIN.

## GPT vision divergences and controls

GPT-5.6 Sol reads images directly; no separate vision model is invoked. Compared with the Claude vision path, the portability risk is not a different rubric but model-dependent sensitivity to dense small text, crop boundaries, and verbosity bias. Controls are identical anchors, full-resolution captures, structured read-back, blinded producer identity, concise evidence fields, and escalation for illegible details. No provider-specific relaxation is permitted. No stable verdict divergence is accepted without a golden-set update and calibration evidence.

## Swap-and-tie stability test

For each calibration pair, present the same two labeled stage captures twice: order A/B and order B/A, with producer/model identity removed. Ask which better satisfies one named criterion before requesting the verdict. If preference flips after swapping, record a tie and route the stage to UNCERTAIN/ESCALATE. Repeat for three anchors: clear PASS vs clear FAIL, PASS vs visually polished but read-back-wrong FAIL, and two equivalent PASS captures. The deterministic parent reducer, not the vision judge, performs the flip comparison.

## Calibration record

The Phase 3+4 structural calibration validates wrapper/core presence, exact verdict enums, doctrine links, and this swap-and-tie specification. Runtime golden screenshots remain the authority for model-upgrade recalibration; changing the pinned GPT vision model requires replaying all three pairs before trusting new verdicts.
