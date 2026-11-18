# Seed: review-deep gates only on what the change introduced

**Status:** queued 2026-11-18 (operator: "write the seed"). Not started; no lane (skill-mesh lanes are parked for memory).
**Affects:** `skills/review-deep/core.md` (finding classification and aggregation), `skills/build-step/core.md` (Step 9 stop-and-audit), and the build-phase halt contract wording where it names stop-and-audit.

## What happened

On 2026-11-18 one `/build-step --reviewers deep` run in a private Unity project took six review rounds (about five hours) and halted twice under stop-and-audit (build-phase halt class 3):

- Every round passed correctness, bugs, security, test-quality and plan-conformance, and the gates were green each time (about 1,250 tests).
- The style lens blocked every round on the same shape, duplicate-shape-constants ("a value restated outside its one owner without a pin"): 2, 4 and 5 Blocks in rounds 1-3, then 1, 3 and 2 in rounds 4-6.
- Each fix moved the lens to the next nearest site: schema description prose, C# doc comments, then pre-existing importer lines from an earlier milestone that the step did not touch. The count never trended to zero.
- Stop-and-audit fired on "same bug shape in three consecutive rounds" without asking whether the flagged lines belonged to the change. The operator resolved both halts by scoping the remainder to a follow-up and landing.

The memory note on review-deep Nit non-convergence describes the same family: a lens that keeps finding the next adjacent site BLOCKs at max iterations instead of converging.

## Change

1. **Gate on introduced lines only.** A review-deep finding is gate-eligible (can be a `Block` that makes a lens NEEDS-WORK) only when its location is on a line the change adds or modifies, or the finding names a defect the change creates elsewhere (for example a consumer the change broke). Findings located only in untouched lines become `pre-existing` advisories: reported, listed for a follow-up, never gating.
2. **Stop-and-audit counts gate-eligible findings only.** build-step Step 9's "same material bug shape in three consecutive rounds" ignores `pre-existing` findings, so a lens walking into older code cannot trigger a halt.
3. **A follow-up list, not a lost finding.** build-step writes the accumulated `pre-existing` findings to the run archive and names them in the report (and, under build-phase, in the step's Status line), so they reach a follow-up instead of disappearing.
4. **Style shape rules stay strict for new code.** duplicate-shape-constants remains a `Block` when the change itself introduces the duplicate.

## Done when

- A fixture run whose only style findings sit in untouched lines passes review and does not halt.
- A fixture where the change itself introduces a duplicated shape constant still blocks.
- Three rounds of pre-existing-only findings do not trigger stop-and-audit; three rounds of an introduced defect still do.
- The report lists the pre-existing findings as a follow-up.

## Notes

- Line attribution comes from the payload patch build-step already produces (`payload.patch`); review-deep receives the diff today, so no new input is needed.
- Keep the change in the shared review core so `review-gauntlet` and the code-lane arms can adopt the same `pre-existing` class later.
