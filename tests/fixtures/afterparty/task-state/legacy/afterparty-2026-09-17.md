# afterparty sweep - 2026-09-17

Acceptance fixture: a prepared record in the shape used before report version 1. It has
no report-kind, report-version, run-id, or scope-key field.

workspace: {{WORKSPACE}}
project: {{WORKSPACE}}/demo-project
mode: apply-on-confirm

Autonomous (report):
- tier-drift: the proposed routing settings disagree with the installed settings; no
  runtime failure was established.
- lesson-harvest: 2 candidates (dry-run, nothing created).
- context-slim: unavailable on this host.

Orphan cleanup: candidates listed; the size pass was stopped before it finished.
Rollup commit: sessions/ system not present -- skipped.

Follow-ups:
- Routing settings disagreement. Evidence: {{WORKSPACE}}/routing/installed-offload-config.json
  compared with the tier-offload proposal. Owner: operator (routing settings). Deferred
  until tier-drift is re-run.
- Tidy some memories later.
