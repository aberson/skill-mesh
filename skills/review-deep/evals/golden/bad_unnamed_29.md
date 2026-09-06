<!-- BAD OUTPUT — DEFECT: top-level aggregated verdict emits pure DEFERRED-TO-UAT despite the bugs lens reporting a Block finding (silent-wiring); NEEDS-WORK should dominate -->
<!-- Violates SKILL.md lines 615-617: "DEFERRED-TO-UAT ... deferral takes priority over PASS but NOT over NEEDS-WORK on the same diff" — when Block findings exist NEEDS-WORK MUST be in the verdict (alone or as NEEDS-WORK + DEFERRED-TO-UAT) -->

# review-deep: DEFERRED-TO-UAT

Invocation: `--prompt "wire judge sampling into the propose flow per plan step 15" --diff <staged> --plan-step documentation/toybox-plan.md:15 --reviewers full --url http://127.0.0.1:4000/child --start-cmd 'uv run python -m toybox serve --port 4000' --output-dir .review-deep/`

## Lens verdicts

- correctness: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)
- bugs: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)
- test-quality: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)
- style: PASS (0 findings, model: claude-haiku-4-5-20251001)
- plan-conformance: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)
- Runtime downgrade: login_form_in_200_body (Login form detected in 200 body)

## Findings

### Block

- **src/toybox/judge_sample.py:1** (bugs, anti-pattern: silent-wiring): The diff adds `schedule_judge_sample(propose_ctx)` and a direct-import unit test, but grep across `src/toybox/` finds zero production references; `_do_propose` in `src/toybox/propose.py` was not modified, so the production effect is zero judge calls forever.

  ```
  $ git grep -n schedule_judge_sample -- ':!tests/'
  src/toybox/judge_sample.py:14:def schedule_judge_sample(propose_ctx: ProposeCtx) -> None:
  ```

- **documentation/toybox-plan.md:Step 15** (plan-conformance): Done-when clause `judge runs on >0 sampled proposes per session` is unmet by the diff.

  ```
  Plan excerpt: judge runs on >0 sampled proposes per session
  Diff evidence: <no edit to src/toybox/propose.py in this diff>
  ```

### Nit

- **src/toybox/judge_sample.py:14** (correctness): Stated intent implies a call site in `_do_propose`.

  ```
  def schedule_judge_sample(propose_ctx: ProposeCtx) -> None:
      if random.random() >= propose_ctx.judge_rate:
          return
      _enqueue_judge(propose_ctx.session_id, propose_ctx.proposal_id)
  ```

- **tests/test_judge_sample.py:1-58** (test-quality): Tests exercise the helper in isolation.

  ```
  def test_sampling_rate_zero_skips_judge(monkeypatch):
      monkeypatch.setattr("toybox.judge_sample.random.random", lambda: 0.99)
      schedule_judge_sample(ctx)
      assert _enqueue_judge.call_count == 0
  ```

## Deferred to operator UAT

### M1: Auth-gated child kiosk UX at /child requires PIN-entry the runtime probe cannot reach.

- **Covered lenses:** correctness, bugs, test-quality, style, plan-conformance
- **Needs verification:** After PIN entry, confirm the propose flow now invokes judge sampling end-to-end.
- **Commands to run:**

  ```powershell
  uv run python -m toybox serve --port 4000
  # In a separate terminal, open http://127.0.0.1:4000/child in the kiosk browser
  # Enter parent PIN, navigate to 'Propose'
  ```

Please run M1 next.

Audit-trail JSON: .review-deep/2026-05-26T11-04-08.json
