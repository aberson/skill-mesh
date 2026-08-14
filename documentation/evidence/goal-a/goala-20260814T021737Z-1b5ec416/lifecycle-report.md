# Goal A lifecycle evidence

## Outcome

The initial Claude Code and Codex `a0` runs stopped before a host command because protected Codex
database files were changing. Both initial results were `AMBIGUOUS`.

The one authorized bounded follow-up then ran Claude Code lifecycle attempt `a1`. Its isolated
authentication, v1 installation, v1 discovery, process containment, protected-state comparison, and
cleanup passed. The attempt nevertheless returned `FAIL`: after the active marketplace source moved
to the candidate-derived v2 bytes, but before the explicit update command, a fresh alpha consumer
returned the v2 marker instead of the required installed-v1 marker.

The approved stop rule ended the follow-up immediately. Codex lifecycle `a1` and the Claude reviewer
dispatcher `a0-r1` did not run. Gate A therefore ends with `stop`; no lifecycle owner or product
architecture is selected.

This report summarizes redacted evidence. Raw evidence remains under
`%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\lifecycle\`.

## Evidence identity

| Host | Run and attempt | Report SHA-256 | Manifest SHA-256 | Result |
|---|---|---|---|---|
| Claude Code | `lifecycle-claude-20260814T065643Z-e1ea3dd1/a0` | `e478ba1cd8577d89eae6565a62efbf9740629524306143b00bd685e84261ff6d` | `3ac1020e58cd6da00793cbc4641aba46d6fc78cacd37ab3ce570550c5b60b916` | `AMBIGUOUS` |
| Codex | `lifecycle-codex-20260814T065645Z-34c7074f/a0` | `c92b65e8807f01fbdf3e38e83c2e5d1760f8d1484609ffb8197a832e61e3f453` | `58e2e204b43851e63053f7bb3e1977163a17080d86c2e1c12f992052f88ca9bc` | `AMBIGUOUS` |
| Claude Code | `lifecycle-claude-20260814T065643Z-e1ea3dd1/a1` | `a3b2a90e4ac72b4964db1650cc4812a0646b9e98f78d178c591f912a36933d4f` | `33001429c8d2cdf5d22cf4c30fc4590a49a6376451401137b693b30dcc91ddd9` | `FAIL` |

All three manifests and their covered files rehash successfully. The candidate executed by both `a0`
runs was `3a17746fa1d04c24088effd8f3871afe10f1601f`. Claude `a1` executed corrected candidate
`0c72392ec51da5201c4f3c17272e2b79a32a055d`. The external append-only index contains the Claude
`a1` report and manifest rows and hashes to
`94d26b399bf700b66d986cde6973023eeaafc9325077621718e4ddbaccb7078f`. It contains no Codex
`a1` or dispatcher `a0-r1` row.

## Observed facts

- Both `a0` runs stopped at protected-state preflight and launched no host command.
- Claude `a1` used Claude Code `2.1.223` and the corrected lifecycle candidate.
- Its isolated copied-file authentication check passed and reported a first-party Claude Max login.
- Strict package validation, marketplace registration, v1 installation, exact installed-v1 byte
  inventory, and the first v1 alpha and beta consumers passed.
- The next alpha consumer ran before the explicit update command. It exited `0` but returned the v2
  marker. The lifecycle acceptance required the v1 marker at that point, so the attempt was `FAIL`.
- No explicit update, disable, enable, uninstall, post-uninstall discovery, or later
  post-update/post-uninstall cache check ran.
- Every started process was assigned to its Windows Job Object before resume. All Jobs became empty;
  no timeout or surviving process was recorded.
- The protected live-state snapshots were byte-identical. The runner removed its disposable home and
  retained the complete evidence directory and its 154-entry manifest.
- The sealed raw report's generic inventory description names future v2 and post-uninstall inventory
  files. The early stop prevented those files from being created; the complete manifest correctly
  excludes them.
- The installed Codex CLI exposes no native plugin update, enable, or disable command.
- Raw provider output for each Claude `a1` model call contains both
  `claude-haiku-4-5-20251001` and `claude-sonnet-5` usage. The raw report's singular Haiku field is a
  parser limitation; this evidence does not establish one resolved model identity.

## Inferences

- The quiet-session follow-up removed the prior protected-state precondition failure.
- In this fixture, the installed Claude package observed candidate v2 content before the explicit
  update operation. Source-linked or hot-refresh behavior is a plausible explanation, but the
  evidence does not identify the mechanism.
- That behavior violates this experiment's controlled-update acceptance criterion. The evidence does
  not support selecting Claude Code native lifecycle ownership.
- The successful v1 install and discovery observations are useful but cannot override the later
  lifecycle failure.

## Unresolved premises

- Why the pre-update Claude consumer observed v2, and whether the behavior is a documented host
  guarantee.
- How explicit Claude update, disable, enable, uninstall, and post-uninstall discovery behave after
  this failure point.
- Whether Codex can install, discover, and uninstall the package.
- Whether bounded compatibility can safely cover Codex's known missing native update, enable, and
  disable operations.
- Whether either host avoids stale or premature bytes across a complete update lifecycle.
- Which single model, if any, should be attributed when Claude reports both Haiku and Sonnet usage.

## Terminal recommendation

Record Gate A action `stop`, Goal B authorization `no`, and live cutover `not-authorized`. Preserve
all raw attempts and the Step 4 recovery artifact. Do not run another lifecycle or cross-family host,
select a lifecycle owner, start Phase 2, implement product code, or mutate a live home.

This terminal recommendation is bound to the Claude `a1` report
`a3b2a90e4ac72b4964db1650cc4812a0646b9e98f78d178c591f912a36933d4f` and manifest
`33001429c8d2cdf5d22cf4c30fc4590a49a6376451401137b693b30dcc91ddd9`, together with both `a0`
report/manifest pairs listed above.
