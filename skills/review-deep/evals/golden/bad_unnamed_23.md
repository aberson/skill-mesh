<!-- BAD OUTPUT — DEFECT: two lenses both surface the same "missing integration test" absence finding at full Nit severity; aggregator failed to dedup (rule 7 absence-of-thing path) — both Nits remain instead of one Nit + one demoted FYI -->
<!-- Violates SKILL.md line 604 (rule 7 absence path): "when multiple lenses surface findings about the same absence — no concrete path:line anchor in the diff ... dedup by (anti_pattern, summary fuzzy-match) and demote duplicates to FYI; primary lens is ... the first lens to emit by CODE_LENS_ORDER" -->

# review-deep: NEEDS-WORK

Invocation: `--prompt "wire judge sampling into the propose flow per plan step 15" --diff <staged> --plan-step documentation/toybox-plan.md:15 --reviewers code --output-dir .review-deep/`

## Lens verdicts

- correctness: NEEDS-WORK (2 findings, model: claude-sonnet-4-6)
- bugs: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)
- test-quality: NEEDS-WORK (2 findings, model: claude-sonnet-4-6)
- style: PASS (0 findings, model: claude-haiku-4-5-20251001)
- plan-conformance: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)

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

- **tests/integration/ has no test_judge_sample.py** (correctness): The prompt claims wiring will be exercised, but no integration test verifies end-to-end behavior; correctness cannot be confirmed against intent.

  ```
  <no anchor line in diff>
  ```

- **no test file for src/toybox/services/judge_sample.py exists** (test-quality): missing integration test for judge fan-out path; this is a critical-behavior coverage gap.

  ```
  <no anchor line in diff>
  ```

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

Audit-trail JSON: .review-deep/2026-05-26T11-04-08.json
