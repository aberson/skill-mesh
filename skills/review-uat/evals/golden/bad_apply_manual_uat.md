# Unmeasured negative fixture: apply ownership defect

Input is `docs/plan.md#M2`. The file is readable and contains exactly one matching anchor. I saved
its exact bytes, refined the trailing draft list, and confirmed the file had not changed.

I replace the draft list and also rewrite the existing row for M2 under `## Manual UAT` to say
“refined and ready.” I report both changed ranges and leave every other byte unchanged.

This fixture contains one intended defect: `review-uat --apply` writes build-phase-owned Manual UAT
content outside the anchored replaceable span.

