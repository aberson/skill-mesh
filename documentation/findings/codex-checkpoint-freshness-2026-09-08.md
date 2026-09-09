# Codex checkpoint invocation and conversation challenge repair

The operator authorized this bounded repair on 2026-09-08 after an external build stopped
before its first implementation step. Base: `ee6ae7189bee6d5a27a309cfd1f372ed00738676`.
The change updates three portable skills' Codex adapters and their provider guide. It changes
no neutral core, Claude/GPT adapter, catalog identity, resource topology, review lane, or
private verdict-service implementation. Phase CL Step 111's separate worktree is preserved.

## Problem and resulting behavior

`build-phase` required a separate named-skill dispatcher for a checkpoint, although
`task-handoff` executes in the caller's session. The adapter now resolves the installed
entry point, loads its full core, and executes the requested checkpoint mode with the
available shell/filesystem tools. Missing package, session identity, and rollup-helper
dependencies remain concrete failures. A prose handoff does not replace the procedure.

The prior conversation probe stopped on conflicting subjective inheritance reports even
though neither child recovered a hidden value. Conversation challenge v2 specifies a fixed
JSON report, calibrates reporting with disclosed dummy values, then checks two separate
no-history sibling contexts against exact parent-owned expectations. Extra or duplicate
keys, missing fields, wrong types, tool calls, non-JSON output, or a reported protected value
fail the check. Shared host instructions are expected. This is a bounded conversation
measurement; it does not claim OS isolation or waive any private-state/service gate.

The earlier inconclusive result remains inconclusive. This is a new protocol measurement,
not a retroactive PASS or a retry of unchanged instructions until success.

## Validation observed on the candidate

| Check | Observed result |
|---|---|
| All provider builds | Claude: 57 skills / 128 files; GPT and Codex: 54 skills / 125 files each |
| Regenerated inventories | Content identical to the base after normalizing generator-emitted Windows newlines to canonical LF |
| Release-candidate report | Regenerated; identical to the base after the same newline normalization |
| Three emitted Codex packages | Skill-creator frontmatter validation passed |
| Focused adapter contract tests | 51 passed |
| Package-integrity suite | 420 passed in 67.61 seconds |
| Independent instruction review | No actionable findings; read-only review of the adapter/core relationship |
| Checkpoint forward exercise | Real post-step `task-handoff --loop --no-commit` in a disposable Git fixture; exit 0, checkpoint written |
| Session preservation | Active-project header and prior fields retained; Completed appended exactly once; unrelated session byte-identical |
| Rollup and Git | Rollup equals the production helper's derivation; owned session freshest; Git status empty and HEAD unchanged |
| Conversation challenge v2 | Positive control exactly recovered its four supplied dummy values; producer and reviewer each echoed their own nonce and reported null for all three withheld fields |
| Challenge dispatch | Three direct fresh children with explicit `fork_turns="none"`; no child tool calls |
| Caller scope | A separate fresh child was denied access to the disposable service handle; parent subsequently closed that same service successfully |
| Verdict service | Exact ready schema; open/write/classify yielded ADVANCE for a probe-only signed PASS; quoted Python-looking summary remained inert data |
| Tamper and rotation | Corrupted sidecar classified BLOCKED; pre-cleanup signed bytes also classified BLOCKED after reopening the same run ID |
| Cleanup | Both services exited 0; probe sidecar, retained signed bytes, and temporary service directory removed |

The checkpoint fixture used an explicitly supplied synthetic session identity. Its text
"8 passed" was scenario input, not an application test result. Protected probe values,
candidate handle, HMAC key, and signed sidecar bytes are not published in this record.
The original committed candidate `92f0821` reached the repository-root gate and failed only
the emitted isolation-contract assertion, as recorded by the guarded follow-up job. The exact
follow-up candidate `25b54a5` restored the pinned sentence while retaining the subjective
self-report prohibition and passed the full repository-root gate. Final evidence is recorded
in `codex-checkpoint-followup-gate-25b54a5.txt`; the original candidate history remains
part of this record and is not a PASS claim.

## Remaining deep-review boundary

The external plan's first five steps use `--reviewers full` (five code and three runtime
reviewers). Its three later `--reviewers deep` steps still require the separately accepted
Codex review-deep gap to be addressed. This repair does not switch those flags or reopen
DS-D3. A fresh coordinator must use the repaired installed packages and establish its own
host capability evidence; this record is not a portable permission token for another host.

Restoration of Codex review-deep takes its own reviewed plan under DS-D3; using the supported
Claude lane preserves the review requirement; changing to code review changes the plan's
accepted review depth. The operator's choice is separate from this checkpoint/probe repair.
