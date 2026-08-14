You are the reviewer in a bounded cross-family execution experiment.

Review only the requirements and diff below. Do not use tools or inspect any file outside this prompt. The candidate has synthetic provenance; do not infer which model family authored it.

Return one JSON object that matches the supplied response schema. Copy the run, source, and payload identities below into their matching response fields. Use `NEEDS_WORK` when a functional defect violates a stated requirement. Give each finding the exact `requirement_id` from the requirements. Use `OTHER` only when no listed requirement applies. Cite the changed expression or omitted validation in each finding. Do not mention this experiment's hidden defect inventory.

## Sealed request identity

- Run: `{{RUN_ID}}`
- Source commit: `{{SEEDED_CANDIDATE_SHA}}`
- Payload SHA-256: `{{PAYLOAD_SHA256}}`

## Requirements

{{REQUIREMENTS}}

## Candidate diff

```diff
{{DIFF}}
```
