<!-- BAD OUTPUT — DEFECT: only four lenses spawned; test-quality lens missing from Lens verdicts entirely -->
<!-- Violates SKILL.md lines 86-313: "five standing review lenses (correctness, bugs, test quality, style, plan-conformance)" — all five MUST appear in lens_verdicts -->

# review-deep: NEEDS-WORK

Invocation: `--prompt "wire judge sampling into the propose flow per plan step 15" --diff <staged> --plan-step documentation/toybox-plan.md:15 --reviewers code --output-dir .review-deep/`

## Lens verdicts

- correctness: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)
- bugs: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)
- style: PASS (0 findings, model: claude-haiku-4-5-20251001)
- plan-conformance: NEEDS-WORK (1 findings, model: claude-sonnet-4-6)

## Findings

### Block

- **src/toybox/judge_sample.py:1** (bugs, anti-pattern: silent-wiring): The diff adds `schedule_judge_sample(propose_ctx)` and a direct-import unit test, but grep across `src/toybox/` finds zero production references; `_do_propose` in `src/toybox/propose.py` was not modified, so the production effect is zero judge calls forever. Fix: add an integration test that drives `_do_propose` end-to-end and asserts `schedule_judge_sample` is reached (caller-first).

  ```
  $ git grep -n schedule_judge_sample -- ':!tests/'
  src/toybox/judge_sample.py:14:def schedule_judge_sample(propose_ctx: ProposeCtx) -> None:
  ```

- **documentation/toybox-plan.md:Step 15** (plan-conformance): Done-when clause `judge runs on >0 sampled proposes per session` is unmet by the diff — no call site in `_do_propose` or any other production caller reaches `schedule_judge_sample`.

  ```
  Plan excerpt: judge runs on >0 sampled proposes per session
  Diff evidence: <no edit to src/toybox/propose.py in this diff>
  ```

### Nit

- **src/toybox/judge_sample.py:14** (correctness): Stated intent implies a call site in `_do_propose`; the diff stops short.

  ```
  def schedule_judge_sample(propose_ctx: ProposeCtx) -> None:
      if random.random() >= propose_ctx.judge_rate:
          return
      _enqueue_judge(propose_ctx.session_id, propose_ctx.proposal_id)
  ```

Audit-trail JSON: .review-deep/2026-05-26T11-04-08.json
