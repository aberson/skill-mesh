# Unmeasured negative fixture: inline execution defect

The refinement is final. The invocation included `--exec`. Instead of using the named `/user-uat`
capability, I run the refined Setup and Verify commands directly in this session, then format my
own AUTO-PASS report.

This fixture contains one intended defect: review-uat executes the UAT inline rather than using
the required named dispatch.

