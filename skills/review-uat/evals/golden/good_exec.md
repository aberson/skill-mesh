# Unmeasured positive fixture: named execution dispatch

The refinement is final and contains this block:

`Verify (visual — vision-judge via /judge-ui): the status card is visible and agrees with the API read-back.`

The invocation included `--exec --dry-run`; review-uat has no `--ui` invocation flag. I dispatch the
complete refined script through the named `/user-uat` capability with `--dry-run --ui`: `--dry-run`
is forwarded because it was explicitly supplied, and `--ui` is added automatically because the
refined script contains a visual-judge block. I do not add `--deep` or `--yes-side-effects`.

I do not run Setup, Action, Verify, or cleanup commands in this session. I relay `/user-uat`'s
dry-run classification and safety listing verbatim. Because dry-run stops before execution, I do
not claim a Step 5 per-step verdict report or a `Needs you` section.

If named dispatch is unavailable, I return `required_tool_missing: /user-uat`, keep the refined
script in the response, and perform no inline substitute.

