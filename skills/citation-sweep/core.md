# NOTE: This is the canonical provider-independent contract. Every provider wrapper must load it in full.

## Provider-neutral host abstractions

- This skill ships no supporting assets. The CLI and its contracts live in `citation-needed/`; run commands from the coding-root workspace.
- A **judge call** is an isolated fresh-context depth-1 task/action invocation. The sweep parent dispatches judges directly; it never delegates whole-artifact orchestration to a worker.
- Model tier names describe capability roles. Resolve them through current host policy and `config/model-tier-map.json`; unavailable capability returns `required_tool_missing`.
- Never expose hidden chain-of-thought. Preserve only required decisions, evidence, commands, structured artifacts, and rationale.

# Citation sweep - bounded project-wide rigor pass

Invoke as `/citation-sweep <project-slug> [--limit <n>]`. With no slug, run nothing and return HELD with that usage. The default limit is 10; valid values are integers from 1 through 50.

Sweep an owned project's stale and unreviewed LLM-facing artifacts without editing targets. The Citation Needed CLI owns all database, breakdown, and queue writes. This skill never calibrates, automatically retries, or launches per-artifact workers. One parent opens, prepares, judges, and commits every selected run through citation-review's shared phase contract.

## Procedure

1. **Bind one judge and verify the gate.** Resolve `<judge-model-id>` by the citation-review provider rule or explicit operator choice. Prove that this parent can dispatch fresh depth-1 judge siblings; if absent or inconclusive, return HELD with `required_tool_missing` before opening a run. Run:

   ```powershell
   uv run --project citation-needed cite calibrate check --model <judge-model-id>
   ```

   Continue only on `Calibration: VALID`. Never use a bare check, accept aged calibration, or invoke calibration from sweep. The next action for invalid calibration is `/citation-review --calibrate`, then a new sweep.

2. **Scan and select from scoped readiness lists.** Run:

   ```powershell
   uv run --project citation-needed cite scan --project <project-slug>
   uv run --project citation-needed cite overview --json --project <project-slug>
   ```

   A nonzero exit, null list, unknown project, zero matched artifacts, or unavailable database ends HELD with the exact CLI blocker. The filter scopes only the three readiness lists and their totals; overview state, counts, recent activity, and queue remain workspace-wide and must be labeled that way.

   Select exact stored paths from `stale_artifacts`, then `unreviewed_artifacts`, preserving each list's path/id order. List `current_content_unavailable_artifacts` separately. Select at most the limit and defer the rest. Each scoped list remains capped at 50. When its `total` exceeds returned items, report the exact omitted/deferred count but never invent omitted paths and never claim project completeness. An empty scoped list alone does not prove an unknown, missing, inactive, or ready artifact is fresh.

3. **OPEN ALL barrier.** In selection order, call citation-review OPEN in this same parent with the exact `<judge-model-id>` and no `--calibrate` or `--accept-aged`. Record every returned run id from its own open JSON.

   No PREPARE, JUDGE, or COMMIT may begin until every selected path has opened successfully. On the first refused or failed open, terminate this wave and proceed directly to the HELD report in step 8; do not execute steps 4–7 or attempt any later open. Preserve earlier runs as `open #<run_id> (uncommitted)`, report the failed path and its exact blocker, and mark all later paths deferred with that barrier blocker. Do not recalibrate, reopen, retry, abort, clean up, or replace a returned run id. A simultaneous dispatch is not evidence that opens preceded a commit; the ordered barrier is mandatory.

4. **Prepare in the parent.** Only after every selected path has opened successfully, call citation-review PREPARE for each run. Freeze each choice/evidence identity before judging. Preparation failure leaves that run open and uncommitted and does not erase other opened runs. No child prepares evidence or owns a run.

5. **Judge with depth-1 siblings.** For each successfully prepared run, the parent calls citation-review JUDGE. Every vote is a fresh sibling receiving one frozen choice/evidence input. Preserve k=3/5/7 tie escalation, all prior votes, parse failures, exact model receipts, and evidence-change invalidation. Judges cannot spawn children, see other votes, call the CLI, or commit. Capacity or dispatch failure is truthful partial state and receives no implicit replacement.

6. **Commit only successful runs.** After all possible preparation and judging is complete, call citation-review COMMIT for each run that satisfied every gate. Use that run's exact id. A failed commit is reported as open/uncommitted and does not stop truthful reporting or commits of other already-judged runs. Never commit a held tie, partial vote set, changed evidence identity, or run borrowed from another invocation.

   Opening is over before the first commit, so a citation-adding commit cannot strand a later selected open behind a newly stale calibration. Such a commit can invalidate calibration for the next wave; report `/citation-review --calibrate` as the explicit next action when the CLI later establishes that condition. Do not assume every commit changed the corpus.

7. **Build the backlog.** For each run committed by this invocation with blocker `none`, run `cite distill generate --run <run_id>` and no other run. Record CLI failures and continue. Report every `created`, `refreshed`, and `skipped N resolved row(s)` result; generation replaces open defaults and may replace an earlier refinement, so never call it refinement-preserving. Then run `cite queue list --project <project-slug>`. Keep external-evidence, internal-only, documented no-literature-found, and no-evidence states distinct.

8. **Report.** Include:

   - slug, scan counts, selected paths, known deferred paths, honest omitted counts, unavailable paths, and every global-vs-scoped qualification;
   - judge id, calibration line, native judge model/effort receipts when available, and UNKNOWN where absent;
   - for every selected path: exact run id or `none`, committed/open-uncommitted/deferred state, band and choice count only for the same committed run, evidence summary, and exact blocker;
   - advisory groups of similar needs-improvement decisions without merging keys, rows, votes, or scores;
   - this invocation's queue results and the project's current open backlog, labeled separately;
   - every producer, API, capacity, or CLI failure and the exact next action.

   An empty successful selection is a result. A HELD sweep returns the slug, blocker, known partial state, and next action. Deferred work is never reported as completed.

## Constraints

- Never fabricate a corpus hit, external verification, calibrated verdict, run id, model receipt, score, or completion.
- Never edit a target artifact.
- Never delegate artifact orchestration, allow nested artifact workers, or let the preparing parent vote.
- Never commit before the OPEN ALL barrier closes.
- Never hide open-uncommitted runs, omitted counts, failed judges, ties, or deferred paths.
- Never calibrate, retry, reopen, abort, or clean up implicitly.

Re-running is a new bounded wave. Existing open runs are durable partial state and are not evidence; report them through workspace-wide overview counts rather than guessing that a missing readiness row is complete.
