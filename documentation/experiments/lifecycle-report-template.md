# Skill Mesh lifecycle experiment

## Result

**{{RESULT}}**

Failure or stop reason: {{FAILURE_REASON}}

## Run identity

| Field | Value |
|---|---|
| Goal A | `{{GOAL_A_ID}}` |
| Run | `{{RUN_ID}}` |
| Attempt | `{{ATTEMPT_ID}}` |
| Host | `{{HOST}}` |
| Candidate commit | `{{CANDIDATE_SHA}}` |
| Candidate source commit | `{{SOURCE_SHA}}` |
| Plugin | `{{PLUGIN_NAME}}` |
| Marketplace | `{{MARKETPLACE_NAME}}` |
| Credential mode | `{{CREDENTIAL_MODE}}` |
| Host executable | `{{HOST_EXECUTABLE}}` |
| Host executable SHA-256 | `{{HOST_EXECUTABLE_SHA}}` |
| Host version | `{{HOST_VERSION}}` |

The runner exported the fixture from the candidate commit. It did not use mutable fixture bytes.

## Package and consumer identity

| Field | Value |
|---|---|
| v1 source tree SHA-256 | `{{V1_TREE_HASH}}` |
| v2 source tree SHA-256 | `{{V2_TREE_HASH}}` |
| Source locator | `source/current/` in this evidence directory |
| Consumer-byte evidence | `inventories/installed-v1.tsv`, `inventories/installed-v2.tsv`, and `inventories/after-uninstall.tsv` |

The prompts contained a qualified skill name and a unique trigger. They did not contain the run ID,
version, reference marker, helper marker, or expected output line.

## Lifecycle observations

| Observation | Status | Evidence | Detail |
|---|---|---|---|
{{CHECK_ROWS}}

`UNAVAILABLE` means the installed host does not expose that native operation. It does not mean that
the runner substituted an unrelated command. Codex feature flags are not plugin enable or disable
controls.

## Model and usage evidence

| Field | Value |
|---|---|
| Requested model | `{{REQUESTED_MODEL}}` |
| Observed model | `{{RESOLVED_MODEL}}` |
| Identity status | `{{RESOLVED_STATUS}}` |
| Token usage | {{USAGE_STATUS}} |
| Cost | {{COST_STATUS}} |

The raw provider output is retained under `commands/`. A requested model is not treated as proof of
the model that ran.

## Host commands

| Command evidence | Exit code | Seconds | Exact argument record |
|---|---:|---:|---|
{{COMMAND_ROWS}}

Each command directory contains a redacted argument array, stdout, stderr, and an exit record.
Credential values are never recorded.

### Exact redacted arguments

{{COMMAND_ARGUMENTS}}

## Live-home safety

| Snapshot | SHA-256 |
|---|---|
| Before | `{{LIVE_BEFORE_HASH}}` |
| After | `{{LIVE_AFTER_HASH}}` |

The corresponding path-level snapshots are `live-surface-before.tsv` and
`live-surface-after.tsv`. A bounded candidate-owned helper compares the full Claude, Codex, and
`.agents` roots. It also records local junction targets. Credential contents and the ephemeral
comparison key are not retained. Only append-only growth in exact session files found active during
the preflight sample is permitted, and only while the file identity remains unchanged. That exception
makes attribution unavailable and limits the run to `PARTIAL`. Activity in a pre-existing Codex
runtime database or sidecar makes the result `AMBIGUOUS` and stops the experiment before a host
command runs. Any creation, deletion, replacement, or other difference is also ambiguous.

## Cleanup

{{CLEANUP_NOTES}}

The runner retains this evidence directory. It removes only the marked disposable home after it
confirms that the command's kill-on-close Windows Job Object has no active process and that the
cleanup path is still safe. A timeout or surviving descendant makes the result ambiguous. This proof
covers ordinary CLI child processes, not work delegated through an unrelated system service.

## Unresolved premises

{{UNRESOLVED_PREMISES}}
