# Codex release adoption

`tools/activate-codex-release.ps1` adopts one retained, qualified Codex release
into one disposable or operator-selected home. It is an activation wrapper around
the normal Codex installer, with a durable private preimage for rollback.

The wrapper is deliberately narrow. It validates retained release bytes, plans
against the current home, invokes the normal installer without force flags, verifies
the result, and then records release provenance in a selector. It is not a release
builder and it does not decide that a release is qualified.

## Inputs and private state

Set the three locations in the current PowerShell session. Use a private, durable
state location; do not place it inside the home being activated.

```powershell
$releaseDir = '<qualified-release-directory>'
$targetHome = '<consumer-home-directory>'
$stateRoot = '<private-durable-state-directory>'
```

The release must contain `release.json` and `dist/codex`. The record must say
`schema_version: 1`, product `skill-mesh`, qualification `QUALIFIED`, and include
the `codex` provider. Every `dist/codex` file must be listed and hash-matched by
the release record. The activation identity is `skill-mesh/<version>`.

`$stateRoot` receives only wrapper-owned state:

```text
<stateRoot>/
  locks/<home-sha256>.lock
  current-codex.json
  operations/<operationId>/
    preview.json
    preimage/files/...
    preimage/ledger.json
    preimage/selector.json
    postimage.json
    postimage/ledger.json
    installer.stdout.txt
    installer.stderr.txt
    receipt.json
```

The lock name is a hash of the normalized home path, not the home path itself.
Never delete or break a lock file to get past a refusal. Retry once the competing
process has exited, or investigate a stale lock as an operational incident.

## Inspect first

Inspection is read-only. It does not create `$stateRoot`, alter the home, or write
an operation record.

```powershell
powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode inspect -ReleaseDir $releaseDir
```

To include read-only observations of the existing Codex ledger and selector:

```powershell
powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode inspect -ReleaseDir $releaseDir -TargetHome $targetHome -StateRoot $stateRoot
```

Inspect prints the release id, source and builder identities, qualification,
providers, Codex file count, and `release_manifest_sha256`. That manifest digest is
the SHA-256 of UTF-8 canonical lines sorted ordinally as:

```text
dist/codex/<relative-file> <sha256>
```

Each line ends in one newline. The digest binds an activation preview to the exact
Codex artifact set, not merely to a release directory name.

## Preview

Preview validates the release before making any activation change, locks the target
home, captures the full existing ledger and selector bytes, and records a plan.

```powershell
powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode preview -ReleaseDir $releaseDir -TargetHome $targetHome -StateRoot $stateRoot
```

Copy the printed operation id into the session variable:

```powershell
$operationId = '<previewed-operation-uuid4>'
```

A plan row is `add`, `no-op`, `update`, or `remove`. An update is allowed only if
the currently installed byte hash is exactly the Codex ledger's owned hash. A
different existing file without that proof is a foreign collision, and the entire
preview refuses without creating an operation record.

Preview never changes anything in `$targetHome`. It captures preimage bytes for
every existing planned file, all prior ledger bytes, and all prior selector bytes.
It also refuses if a previous operation for this same home is applying,
rolling-back, or incomplete.

## Apply the exact preview

Apply needs the same release, home, state root, and operation id:

```powershell
powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode apply -ReleaseDir $releaseDir -TargetHome $targetHome -StateRoot $stateRoot -OperationId $operationId
```

Before it calls the installer, apply revalidates the release and compares every
planned path, the complete ledger hash, and the selector hash to the preview. A
change after preview is a refusal: take a new preview. The wrapper never refreshes
or replans automatically.

The installer is invoked with its ordinary Codex provider, home, and retained
distribution arguments. The wrapper never passes `-Force`, `-ForceShared`, or a
backup directory. After installation it verifies every desired file, planned
removals, the Codex ledger's exact file/hash bijection, and preservation of other
ledger profiles. It copies the resulting ledger evidence into the operation.

Only after that verification passes is `$stateRoot/current-codex.json` published.
That selector is provenance evidence for this wrapper. It does not route host skill
discovery: the host still discovers Codex skills through the Codex discovery root
owned by the shared discovery map.

## Refusals and failures

Exit code `2` means bad input or a safe refusal. Typical examples are a release
that is not qualified, a hash mismatch, a foreign collision, an unresolved earlier
operation, changed preview inputs, drift, an unknown operation id, or lock
contention. Correct the named condition and repeat inspection or take a new preview
when requested. Do not bypass a refusal with direct edits to activation state.

Exit code `1` means an execution or I/O failure after work may have begun. The
operation is marked `incomplete`, and stdout/stderr from the installer remain under
the operation directory. In particular, a failure while publishing the selector is
not reported as a successful adoption; the installed bytes remain recoverable.

## Recovering an interrupted apply

First inspect the operation directory and its installer output. Then use the same
operation id to restore its preimage:

```powershell
powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode rollback -StateRoot $stateRoot -OperationId $operationId
```

Optionally bind the rollback command to the expected home:

```powershell
powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode rollback -StateRoot $stateRoot -OperationId $operationId -TargetHome $targetHome
```

Rollback accepts only `applied` or `incomplete` operations. It first refuses if the
live files, ledger, or selector contain intervening drift. For a completed apply it
expects the recorded postimage; for an incomplete one it accepts only recorded
preimage or postimage states. It then restores saved bytes exactly and deletes only
planned paths that were absent before. The prior ledger and selector are restored
byte-for-byte, or removed when they were originally absent.

A previewed operation has no installation to undo, and a rolled-back operation is
not silently accepted a second time.

## What this does not do

- It does not build, qualify, publish, or sign a release.
- It does not pass force flags or overwrite foreign bytes.
- It does not modify credentials, host settings, environment configuration, or
  scheduler configuration.
- It does not change the host's discovery routing; the selector is provenance only.
- It does not guarantee that a supplied home is a live user home or that a host is
  currently running from it.
- It does not remove foreign files or alter unrelated ledger profiles.
