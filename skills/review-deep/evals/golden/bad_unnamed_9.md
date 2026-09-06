<!-- BAD OUTPUT — DEFECT: lens emits PASS despite containing both Block and Nit findings (verdict threshold violation) -->
<!-- Violates SKILL.md line 158, 200, 244, 283, 336: "Emit PASS if and only if findings contains zero Block AND zero Nit entries" — bugs lens here has a Block but emits PASS -->

# review-deep: NEEDS-WORK

Invocation: `--prompt "wire judge sampling into the propose flow per plan step 15" --diff <staged> --plan-step documentation/toybox-plan.md:15 --reviewers code --output-dir .review-deep/`

## Lens verdicts

- correctness: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)
- bugs: PASS (1 findings, model: claude-sonnet-4-6)
- test-quality: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)
- style: PASS (0 findings, model: claude-haiku-4-5-20251001)
- plan-conformance: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)

## Findings

### Block

- **src/toybox/judge_sample.py:1** (bugs, anti-pattern: silent-wiring): The diff adds `schedule_judge_sample(propose_ctx)` and a direct-import unit test, but grep across `src/toybox/` finds zero production references; `_do_propose` in `src/toybox/propose.py` was not modified, so the production effect is zero judge calls forever. Fix: add an integration test that drives `_do_propose` end-to-end and asserts `schedule_judge_sample` is reached (caller-first).

  ```
  $ git grep -n schedule_judge_sample -- ':!tests/'
  src/toybox/judge_sample.py:14:def schedule_judge_sample(propose_ctx: ProposeCtx) -> None:
  ```

- **documentation/toybox-plan.md:Step 15** (plan-conformance): Done-when clause `judge runs on >0 sampled proposes per session` is unmet by the diff — no call site in `_do_propose` or any other production caller reaches `schedule_judge_sample`. The clause cannot be satisfied without wiring.

  ```
  Plan excerpt: judge runs on >0 sampled proposes per session
  Diff evidence: <no edit to src/toybox/propose.py in this diff>
  ```

### Nit

- **src/toybox/judge_sample.py:14** (correctness): Stated intent ("wire judge sampling into the propose flow") implies a call site in `_do_propose`; the diff adds the helper and its tests but stops short of the wiring claim.

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
