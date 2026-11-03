# Code Consigliere private record protocol

An event's `evidence_class` applies to every claim in its body. Record claims with
different evidence statuses as separate events; never label an inference as recorded
rationale merely because it accompanies an observation or quotation.

Use this protocol only through a discovered and validated `consigliere` helper. The helper's
events are authoritative; generated summaries and wiki views are rebuildable. Success JSON and
record bodies are private.

Every event envelope contains `schema_version: 1`, UUID-v4 `event_id` and
`investigation_id`, increasing UTC `created_at`, `kind`, an `evidence_class` key containing
one of `recorded-rationale`, `observed-behavior`, `inference`, or `unknown-history`, a
nonempty Markdown `body`,
an `evidence_refs` array, `supersedes` (a prior event UUID or null), and a `payload` object.
`draft` pre-fills `evidence_class` with `unknown-history` and `body` with an empty string;
replace both honestly before recording.
Create the initial envelope with `draft PROJECT_UUID --kind request --out PRIVATE_FILE`.
For every subsequent event use `draft PROJECT_UUID --investigation INVESTIGATION_UUID --kind
KIND --out PRIVATE_FILE`. Use a new, nonexistent draft path under the private record root
reported by `status` for each checkpoint, created when that work happens; never place a draft
inside the target. Edit only the private draft; append it with
`record PROJECT_UUID --input PRIVATE_FILE`.

Evidence references contain `locator`, `source_revision` (string or null),
`content_sha256` (lowercase SHA-256 or null), `observed_at` (UTC), and `method`. Source
inspection requires a revision or content hash. `method` is exactly one of
`source-inspection`, `command-execution`, or `operator-report`.

Optional `payload.phase` is exactly `Init`, `Discuss`, `Signoff`, or `Implement`.
Post-build checking is recorded with kind `verification`, never phase `Verify`.

Required payloads:

| Kind | Required payload |
|---|---|
| `request` | `question`, nonempty string-list `goals`, string-list `constraints`, `entry_point`, `source_snapshot`, `next_action` |
| `signoff` | `agreed_outcome`, string-list `constraints`, nonempty string-list `acceptance_checks`, `user_authorization_reference`, `seed_destination` |
| `seed-receipt` | `signoff_event_id`, lowercase `seed_sha256`, exact signed-off `destination`, `source_snapshot` |
| `wiki-revision` | lowercase slug `term_id`, `title`, string-list `aliases`, `scope` (`project` or `general-candidate`), `status` (`current`, `superseded`, or `disputed`) |

`finding`, `decision`, `verification`, `handoff`, and `revision` may carry their context in
`body`; include `next_action` where useful. A revision explains the changed boundary and
invalidates prior signoff. A wiki revision requires evidence; when revising a term, set
`supersedes` to its current event UUID. Current aliases must not identify two terms.

`source_snapshot` is the revision plus dirty-file hashes, or a concise non-Git manifest. The
helper validates record shape and receipt hashes; it does not prove claim truth, source
coverage, or human approval.

After `status PROJECT_UUID` reports the private record root, read `summary.md`,
`investigations/INVESTIGATION_UUID/current.md`, the investigation's event Markdown files, and
`wiki/TERM.md` as needed. Follow evidence links only within the agreed read scope. Views are
disposable; never treat a direct edit to a summary, current view, or wiki view as recorded
history.

