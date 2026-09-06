<!-- BAD OUTPUT — DEFECT: plan-conformance emits SKIPPED on a step-not-found case (should be NEEDS-CLARIFICATION per the dual-format detection rule) -->
<!-- Violates SKILL.md lines 301-306, 333-334: "Neither form locates the step ... emits a single Block-severity Plan-conformance verdict: NEEDS-CLARIFICATION finding ... distinct from SKIPPED" -->

# review-deep: NEEDS-WORK

Invocation: `--prompt "wire judge sampling into the propose flow per plan step 15" --diff <staged> --plan-step documentation/toybox-plan.md:99 --reviewers code --output-dir .review-deep/`

## Lens verdicts

- correctness: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)
- bugs: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)
- test-quality: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)
- style: PASS (0 findings, model: claude-haiku-4-5-20251001)
- plan-conformance: SKIPPED — step 99 not found in documentation/toybox-plan.md (no ### Step 99: heading and no table row with 99 in column 1)

## Findings

### Block

- **src/toybox/judge_sample.py:1** (bugs, anti-pattern: silent-wiring): The diff adds `schedule_judge_sample(propose_ctx)` and a direct-import unit test, but grep across `src/toybox/` finds zero production references; `_do_propose` in `src/toybox/propose.py` was not modified, so the production effect is zero judge calls forever.

  ```
  $ git grep -n schedule_judge_sample -- ':!tests/'
  src/toybox/judge_sample.py:14:def schedule_judge_sample(propose_ctx: ProposeCtx) -> None:
  ```

### Nit

- **src/toybox/judge_sample.py:14** (correctness): Stated intent implies a call site in `_do_propose`; the diff stops short.

  ```
  def schedule_judge_sample(propose_ctx: ProposeCtx) -> None:
      if random.random() >= propose_ctx.judge_rate:
          return
      _enqueue_judge(propose_ctx.session_id, propose_ctx.proposal_id)
  ```

- **tests/test_judge_sample.py:1-58** (test-quality): Tests exercise the helper in isolation; would pass even if production never reaches it.

  ```
  def test_sampling_rate_zero_skips_judge(monkeypatch):
      monkeypatch.setattr("toybox.judge_sample.random.random", lambda: 0.99)
      schedule_judge_sample(ctx)
      assert _enqueue_judge.call_count == 0
  ```

Audit-trail JSON: .review-deep/2026-05-26T11-04-08.json
