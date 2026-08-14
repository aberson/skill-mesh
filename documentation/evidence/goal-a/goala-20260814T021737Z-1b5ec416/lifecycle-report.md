# Goal A lifecycle evidence

## Outcome

The lifecycle experiment did not produce architecture evidence. Both runs stopped before a host
command because protected Codex database files were changing. Both results are `AMBIGUOUS`.

This report summarizes redacted evidence. Raw evidence remains under
`%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\lifecycle\`.

## Evidence identity

| Host | Run and attempt | Report SHA-256 | Manifest SHA-256 | Result |
|---|---|---|---|---|
| Claude Code | `lifecycle-claude-20260814T065643Z-e1ea3dd1/a0` | `e478ba1cd8577d89eae6565a62efbf9740629524306143b00bd685e84261ff6d` | `3ac1020e58cd6da00793cbc4641aba46d6fc78cacd37ab3ce570550c5b60b916` | `AMBIGUOUS` |
| Codex | `lifecycle-codex-20260814T065645Z-34c7074f/a0` | `c92b65e8807f01fbdf3e38e83c2e5d1760f8d1484609ffb8197a832e61e3f453` | `58e2e204b43851e63053f7bb3e1977163a17080d86c2e1c12f992052f88ca9bc` | `AMBIGUOUS` |

Both manifests were rehashed successfully during Step 78 preparation. The candidate executed by
both `a0` runs was `3a17746fa1d04c24088effd8f3871afe10f1601f`. This hash identifies the
completed evidence; it is not the corrected follow-up candidate.

## Observed facts

- The Claude Code series launched no host command.
- The Codex series launched no host command.
- Each safety preflight saw protected Codex SQLite or sidecar files change.
- Each runner removed its exact disposable home and retained its evidence.
- No install, discovery, shared-asset load, update, disable, enable, uninstall, or stale-cache result
  was measured.
- The installed Codex CLI exposes no native plugin update, enable, or disable command.
- Requested model names were recorded. No observed model identity was available because no host ran.

## Inferences

- The experiment environment was not quiet enough to attribute live-root changes to the probe.
- A quiet operator session can remove this specific precondition failure. This is not proof that a
  native lifecycle will pass.
- These runs do not support `native`, `bounded-compatibility`, or `rechartered-installer` for either
  host.

## Unresolved premises

- Whether Claude Code can install, discover, update, disable, enable, and uninstall the package.
- Whether Codex can install, discover, and uninstall the package.
- Whether bounded compatibility can safely cover Codex's known missing native update, enable, and
  disable operations.
- Whether either host reads the shared reference and helper asset from the installed package.
- Whether either host avoids stale v1 bytes after the v2 update.

## Recommendation

Do not select a lifecycle architecture from these runs. Only Abraham can select `stop` or authorize
the exact `goal-a-quiescent-qualification-v1` bounded follow-up at Gate A. No follow-up execution is
authorized before that decision. If approved, the follow-up must run in a quiet operator session.
Step 4 remains frozen in either case.

This recommendation is bound to the Claude Code report
`e478ba1cd8577d89eae6565a62efbf9740629524306143b00bd685e84261ff6d` and manifest
`3ac1020e58cd6da00793cbc4641aba46d6fc78cacd37ab3ce570550c5b60b916`. It is also bound to the
Codex report `c92b65e8807f01fbdf3e38e83c2e5d1760f8d1484609ffb8197a832e61e3f453` and manifest
`58e2e204b43851e63053f7bb3e1977163a17080d86c2e1c12f992052f88ca9bc`.
