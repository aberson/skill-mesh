# Skill Mesh cross-family experiment

## Result

**{{RESULT}}**

Failure or stop reason: {{FAILURE_REASON}}

The result must be `PASS`, `PARTIAL`, `FAIL`, or `AMBIGUOUS`.

- `PASS` means the mechanism produced complete and trustworthy evidence.
- `PARTIAL` means the mechanism worked, but a non-safety observation is unavailable.
- `FAIL` means a required behavior failed and the evidence identifies the failure.
- `AMBIGUOUS` means the evidence cannot support a conclusion.

## Run identity

| Field | Value |
|---|---|
| Goal A | `{{GOAL_A_ID}}` |
| Run | `{{RUN_ID}}` |
| Attempt | `{{ATTEMPT_ID}}` |
| Direction | `{{DIRECTION}}` |
| Mechanism | `{{MECHANISM}}` |
| Synthetic origin status | `{{SYNTHETIC_ORIGIN_STATUS}}` |
| Reviewer host | `{{REVIEWER_HOST}}` |
| Reviewer role | `{{REVIEWER_ROLE}}` |

The seeded fixture supplies the origin artifact. It does not prove that a live origin model built
the candidate. The report records the synthetic origin status separately from reviewer identity.

## Fixture identity

| Field | Value |
|---|---|
| Step 76 candidate commit | `{{STEP76_CANDIDATE_SHA}}` |
| Seeded base commit | `{{SEEDED_BASE_SHA}}` |
| Seeded candidate commit | `{{SEEDED_CANDIDATE_SHA}}` |
| Seeded candidate tree SHA-256 | `{{SEEDED_TREE_SHA256}}` |
| Seeded diff SHA-256 | `{{SEEDED_DIFF_SHA256}}` |
| Sealed payload SHA-256 | `{{PAYLOAD_SHA256}}` |
| Response schema SHA-256 | `{{RESPONSE_SCHEMA_SHA256}}` |
| Hidden defect inventory SHA-256 | `{{DEFECT_INVENTORY_SHA256}}` |

The runner must use the committed Step 76 fixture. It must not use mutable fixture bytes.

## Model identity and fallback

| Field | Value |
|---|---|
| Model policy SHA-256 | `{{MODEL_POLICY_SHA256}}` |
| Model policy status | `{{MODEL_POLICY_STATUS}}` |
| Requested model | `{{REQUESTED_MODEL}}` |
| Requested model kind | `{{REQUESTED_MODEL_KIND}}` |
| Resolved model | `{{RESOLVED_MODEL}}` |
| Resolution status | `{{RESOLVED_STATUS}}` |
| Resolution source | `{{RESOLVED_SOURCE}}` |
| Fallback allowed | `false` |
| Fallback attempts | {{FALLBACK_ATTEMPTS}} |

The requested model is the exact command argument. It is not proof of the model that ran. The
resolved model must come from structured host metadata. If the host does not supply trustworthy
metadata, the resolution status must say `unavailable` or `unverified`. The report must never copy
the requested value into the resolved field by inference.

Reviewer-family identity is load-bearing in this experiment. An `unavailable`, `unverified`, or
`mismatch` resolution makes the overall result `AMBIGUOUS`, even when the handoff and review worked.

Fallback is not allowed in this experiment. The report records whether the host exposes attempt
metadata. `unavailable` is honest when the host does not. Any observed fallback attempt makes the
result `AMBIGUOUS` and invalidates the no-fallback measurement.

## Reviewer process

| Field | Value |
|---|---|
| Executable | `{{REVIEWER_EXECUTABLE}}` |
| Executable SHA-256 | `{{REVIEWER_EXECUTABLE_SHA256}}` |
| Version | `{{REVIEWER_VERSION}}` |
| Redacted working directory | `{{REVIEWER_CWD}}` |
| Tool policy | {{TOOL_POLICY}} |
| Sandbox policy | {{SANDBOX_POLICY}} |
| Reviewer process starts | `{{HOST_STARTED_COUNT}}` |
| Reviewer root exit code | `{{ROOT_EXIT_CODE}}` |
| Job helper SHA-256 | `{{JOB_HELPER_SHA256}}` |
| Snapshot helper SHA-256 | `{{SNAPSHOT_HELPER_SHA256}}` |
| Git version | `{{GIT_VERSION}}` |
| Git executable SHA-256 | `{{GIT_EXECUTABLE_SHA256}}` |

### Exact redacted argument array

{{REDACTED_ARGV}}

The argument record must not contain credentials or private absolute paths.

## Reviewer result

| Field | Value |
|---|---|
| Reviewer verdict | `{{REVIEWER_VERDICT}}` |
| Detected seeded defect count | `{{DETECTED_DEFECT_COUNT}}` |
| Detected seeded defect IDs | {{DETECTED_DEFECT_IDS}} |

`DEFERRED` is a valid reviewer verdict only for the `manual-now-automation-deferred` mechanism.

### Reviewer summary

{{REVIEWER_SUMMARY}}

### Reviewer findings

{{REVIEWER_FINDINGS}}

### Unmatched findings

{{UNMATCHED_FINDINGS}}

An unmatched finding is not a seeded-defect detection. Keep it visible so a later review can decide
whether it is a valid extra finding or a false positive.

## Time, tokens, and cost

| Field | Value |
|---|---|
| Latency in seconds | `{{LATENCY_SECONDS}}` |
| Token usage or availability status | {{TOKEN_USAGE}} |
| Cost or availability status | {{COST}} |

Do not estimate tokens or cost when the host does not report them. Use an explicit availability
status instead.

## Transfer and evidence hashes

| Field | Value |
|---|---|
| Input transfer | {{INPUT_TRANSFER}} |
| Prompt SHA-256 | `{{PROMPT_SHA256}}` |
| Parsed response SHA-256 | `{{RESPONSE_SHA256}}` |
| Raw stdout SHA-256 | `{{RAW_STDOUT_SHA256}}` |
| Raw stderr SHA-256 | `{{RAW_STDERR_SHA256}}` |

The raw output remains evidence. Parsed output must not replace it.

## Candidate immutability

| Field | Value |
|---|---|
| Candidate identity before review | `{{CANDIDATE_BEFORE_IDENTITY}}` |
| Candidate identity after review | `{{CANDIDATE_AFTER_IDENTITY}}` |
| Identity comparison | `{{CANDIDATE_IDENTITY_STATUS}}` |

A changed or uncertain candidate identity makes the run `AMBIGUOUS`.

## Protected live state

| Field | Value |
|---|---|
| Comparison status | `{{LIVE_STATE_STATUS}}` |
| Detail | {{LIVE_STATE_DETAIL}} |

The full live-root snapshots are private evidence. A missing baseline stops before review. Any
before-and-after difference makes the result `AMBIGUOUS`; the report does not attribute that change
to the reviewer or claim that no live mutation occurred.

## Cleanup

| Field | Value |
|---|---|
| Cleanup status | `{{CLEANUP_STATUS}}` |
| Cleanup detail | {{CLEANUP_DETAIL}} |

Cleanup may remove only the named disposable fixture and temporary handoff copies. It must retain
the run evidence.

## Unresolved premises

{{UNRESOLVED_PREMISES}}
