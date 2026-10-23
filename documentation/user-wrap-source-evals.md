# User-wrap repository evaluation assets

The v2 generation work adopts the prepared user-wrap evaluation delta together
with its session-wrap/task-handoff behavior changes. The canonical maintenance
assets are `skills/user-wrap/evals/`: `evals.json`, `test_scenarios.json`, and
the golden corpus and its manifest. They are repository evaluation inputs, not
runtime dependencies of user-wrap's orient/delegate/act workflow.

This is the scoped resource plan for that directory. The session implementation
lane owns those data files; the integration owner owns this packaging decision.
Use the existing evaluation workflow's explicit `evals_dir` and
`versions[].skill_md_path` inputs to bind these source assets to the candidate
being evaluated. Independent grader output is still required; the score
aggregator alone does not execute or independently judge a skill.

The existing distribution builder does not emit these JSON assets. No installer,
provenance parser, migration guard, or historical manifest migration mapping is
changed by this source-only resource scope. In particular, the installed
skill-evolve route that looks for installed evals remains unavailable when they
are absent and retains its existing missing-input halt. The user-wrap maintenance
footer must not promise that installed route or claim an evaluation ran merely
because the corpus exists.

Validate JSON shape, referential integrity, actual corpus counts, and the changed
truthfulness/ownership scenarios. Native success and negative exercises remain
separate evidence. No synthetic golden transcript is a native execution receipt.
Any future deployment of raw JSON requires a separately reviewed emission and
provenance contract; this directory is not a generic support-assets exception.
