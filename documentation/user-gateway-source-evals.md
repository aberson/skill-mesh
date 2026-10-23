# User-gateway repository evaluation assets

This scoped resource plan permits canonical maintenance assets under
`skills/user-gateway/evals/`: assertions, scenarios, golden transcripts and their manifest.
They accompany the approved resumable intake, topic identity and seed-output corrections.
The planning implementation lane owns these files; the integration owner owns packaging.
Original installed evals may be read as input and remain untouched.

These are repository-only evaluation inputs, not runtime dependencies. Use the existing
workflow's explicit `evals_dir` and `versions[].skill_md_path` to select this corpus and
candidate. An independent grader is still required; the score aggregator is not a grader.
The maintenance footer must derive actual counts and describe this source-only scope.

The existing builder does not emit these JSON files. No new installer/provenance/parser
protocol or manifest migration mapping is authorized. Installed evaluation routes retain
their missing-input halt when eval assets are absent. No claim of native execution or
measured quality follows from a synthetic corpus or static checks.

Validate JSON shape, referenced fixture identities, counts and the affected resumable
intake/seed contracts; keep intended single-defect mutations aligned with their positive
anchor. Preserve rejected/missing capability behavior. This named directory is not a
generic support-assets exception. Future deployment requires a separate resource plan.
