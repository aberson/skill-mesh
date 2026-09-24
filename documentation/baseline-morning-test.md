# Baseline morning test - 2026-09-24

## 1. Result

**BLOCKED** for release qualification. **The reversible Codex split itself is built and
was observed working end to end on a real disposable home**, but it is not backed by a
qualified retained release, so no adoption decision is available this morning.

| Item | Status |
|---|---|
| Step 149 implementation (activation wrapper, tests, runbook) | Delivered |
| Step 149 focused test suite | PASS - 29 passed, exit 0 |
| Real disposable apply / no-op / refusals / rollback | PASS - 11 of 11 cases matched |
| Independent six-lens review of the exact candidate | Completed, verdict **NEEDS-WORK** |
| Step 147 release qualification | **NOT ATTEMPTED** - see section 5 |
| Retained release artifact | **NONE** - no release was retained |
| Live profile activation (Step 150) | Not performed, and not authorized unattended |

Nothing was published. No tag was created. No live discovery root was changed. The
operator's daily Codex profile is untouched.

## 2. Candidate identity

| Field | Value |
|---|---|
| Branch | `build/br147-resume-20260924` |
| First frozen candidate | `d4b56ba55d15e77076c67dab68bd3d76f1979593` |
| Final frozen candidate | `720812810a9e27462d327c0fea0886e3f862ba6d` |
| Final tree | `9025796e9694b50e3317fa73da8df307a3c7409b` |
| Base | current `main` at `7ae573bd1c610f8ba1d8e39d66f1f7a915973b36` |
| Producer | independent Codex CLI process, model `gpt-5.6-terra` |
| Reviewers | six independent Claude-family lenses, each resolved `claude-opus-5` |
| Coordinator | Claude Code print-mode session, resolved `claude-opus-5` |

The September 13 snapshot `79a985a38a2ca413da43014b8b50ae4dab67143c` is untouched and
remains historical evidence. No source was repinned.

## 3. What was built

Three files, added and not modified:

- `tools/activate-codex-release.ps1` - modes `inspect`, `preview`, `apply`, `rollback`.
- `tests/release/test_codex_release_activation.py` - 29 behavioral cases.
- `documentation/codex-release-adoption.md` - the operator runbook.

The wrapper owns the exact rollback the installer does not provide: the installer runs
its transaction with `-NoRollback` and deletes its transient journal, so the wrapper
keeps a durable private preimage - owned bytes, absences, the entire ledger and the
prior selector - plus its own operation state.

## 4. Checks actually run, with durations

Every row below was observed by the coordinator, not reported by the producer.

| Check | Result | Duration |
|---|---|---|
| `python -m pytest tests/release/test_codex_release_activation.py -q` (pre-correction) | 17 failed, 6 passed, exit 1 | 11.08 s |
| Same, after the correction pass | **29 passed, exit 0** | 132.28 s |
| Generated-distribution privacy scan, all three profiles | **393 files, 0 findings** | 22.39 s build |
| Committed-absolute-path gate (`test_manifest_contract.py -k "absolute or private"`) | 2 passed | 0.42 s |
| Deterministic review aggregator self-test (`--unit-test`) | PASSED | - |
| Disposable acceptance, run 1 | 9 of 11 matched (2 harness faults, see below) | 590 s |
| Disposable acceptance, refusal re-run | **2 of 2 matched** | 27.6 s |

### Disposable acceptance detail

Run against a **130-artifact acceptance fixture** built from the real repository codex
distribution, using the real installer, on a real disposable filesystem outside the
user profile. Each case is an exit code observed through the normal entry point.

| Case | Expected | Observed | Duration |
|---|---|---|---|
| Inspect identity, read-only | 0 | 0 | 0.69 s |
| Preview against a home holding a foreign file | 0 | 0 | 14.37 s |
| Apply - owned bytes, full ledger, then selector | 0 | 0 | 137.35 s |
| Repeat as a no-op, bytes and ledger stable | 0 | 0 | 62.45 s |
| Refuse a foreign collision | 2 | 2 | 13.98 s |
| Refuse an unqualified release | 2 | 2 | 0.34 s |
| Refuse a corrupt artifact | 2 | 2 | 0.42 s |
| Refuse a changed preview | 2 | 2 | 13.66 s |
| Rollback - prior bytes, ledger, selector | 0 | 0 | 105.57 s |
| Rollback to the original empty home | 0 | 0 | 46.21 s |
| Refuse a double rollback | 2 | 2 | 0.50 s |

The foreign file planted inside the discovery root survived every operation
byte-identically. Two cases reported a mismatch on the first run; both were faults in
the acceptance harness, which chose its probe path from a snapshot of the installed
home, where the run's own foreign probe sorted first. Re-deriving the probe from the
release record made both refusals fire as specified. The harness fault is recorded
rather than quietly overwritten, because the first run's exit codes were real.

## 5. Why qualification was not attempted

`tools/baseline_release.py` reaches `QUALIFIED` only when an attached review row
carries verdict `PASS`, `independent: true`, `cross_family: true`, a resolved model
identity, a conversation id, and the separate `--attest-reviews` naming act.

The closing six-lens review of the exact final candidate returned **NEEDS-WORK** under
the deterministic aggregator - 11 Block, 24 Nit. No honest review row can therefore
claim `PASS`, so the release could not have reached `QUALIFIED`, and the overnight
amendment directs that missing or invalid proof is recorded as BLOCKED rather than
discovered by running a multi-hour gate. The gate was not started and no attempt
directory was created. The single authorized correction pass had already been spent
closing the first review round's 12 Blocks.

This is a genuine result, not a timeout: the deadline was not the binding constraint.

### Review history

| Round | Verdict | Findings |
|---|---|---|
| Opening, on `d4b56ba` | NEEDS-WORK | 12 Block, 15 Nit; all six lenses NEEDS-WORK |
| Correction pass | - | all 12 Blocks closed; suite 23 -> 29 cases |
| Closing, on `7208128` | NEEDS-WORK | 11 Block, 24 Nit |

The correction was real, not cosmetic. The opening round's two most serious findings
were an arbitrary-file deletion reachable from a hand-edited operation record, and a
partially-applied home that no mode could recover. The closing **security lens returned
0 Block** and confirmed the trust boundary now holds: no destructive path is read out
of the unsigned record, every target is re-derived from `-TargetHome` plus the
single-owner discovery map and checked against a genuine containment root.

### The residual Blocks

The closing 11 Blocks are narrower than the opening 12 and cluster as:

1. **Seven test-coverage Blocks.** The review requests coverage for a changed release
   at apply time, forged plan paths, malformed or foreign ledger ownership, a
   noncolliding foreign file, durable postimage/receipt records, malformed or mismatched
   operation IDs, and replayed apply/status rejection. These are source-inspection
   findings, not results of mutation testing or seven observed behavior failures.
   Compare them with the focused and disposable evidence before choosing additional
   assertions; they do not require seven separate new tests.
2. **One native-command redirection defect** (bugs lens, empirically reproduced): under
   the script-wide `$ErrorActionPreference = 'Stop'`, redirecting the installer's stderr
   converts a stderr line into a terminating error. The disposable acceptance apply
   nevertheless succeeded on 130 files, so the reachable blast radius is narrower than
   the lens feared - but it is a real defect and it would corrupt the very evidence the
   recovery procedure tells an operator to read.
3. **Three other behavioral Blocks**: a trailing-separator spelling of the same home
   can slip past the unresolved-prior-operation refusal; an exception before mutation
   can mark an operation incomplete and weaken later rollback drift checks; and two
   homes sharing one state root can overwrite the shared selector and prevent the
   first home's rollback. The invalid `-Mode` exit-code observation is FYI in the
   original review, not one of these Blocks.

None of these was observed to break the happy path or the refusals in section 4. They
are recorded here rather than argued away.

## 6. Commands for this morning

All commands use PowerShell variables. Resolve them from the private morning file
before running anything; this document deliberately contains no machine paths.

```powershell
$releaseDir  = '<acceptance-fixture-release-directory>'
$targetHome  = '<disposable-home-directory>'
$stateRoot   = '<private-durable-state-directory>'
```

**Inspect - read-only, changes nothing:**

```powershell
powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode inspect -ReleaseDir $releaseDir
```

**Preview - writes only to `$stateRoot`, never to the home. Prints the operation id:**

```powershell
powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode preview -ReleaseDir $releaseDir -TargetHome $targetHome -StateRoot $stateRoot
```

```powershell
$operationId = '<operation-id-printed-by-preview>'
```

**Apply - refuses if anything drifted since the preview:**

```powershell
powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode apply -ReleaseDir $releaseDir -TargetHome $targetHome -StateRoot $stateRoot -OperationId $operationId
```

**Rollback - restores prior bytes, absences, ledger and selector. `-TargetHome` is
required, and must match the operation record:**

```powershell
powershell -NoProfile -File tools/activate-codex-release.ps1 -Mode rollback -TargetHome $targetHome -StateRoot $stateRoot -OperationId $operationId
```

Use a disposable `$targetHome`. Do not point these at the daily Codex profile: that is
Step 150, it remains an attended decision, and its precondition - a qualified retained
release - does not exist.

## 7. Limitations

- **No retained release exists.** No `release.json`, no `source.zip`, no
  `SHA256SUMS`, no `PUBLIC-SHA256SUMS`, no release notes. The acceptance fixture is
  labelled as a fixture in its own record and must never be published or adopted.
- **No root `python -m pytest` ran.** The repository-root suite is the DONE gate and it
  was not run, so Steps 147 and 149 are not DONE and nothing here claims they are.
- **No staged `release.ps1 -Provider all` ran**, and no artifact verification.
- **No cross-family qualification proof exists.** The review happened and is real, but
  its verdict is NEEDS-WORK, which cannot qualify a release.
- The acceptance fixture carries the codex profile only.
- The 24 review Nits are recorded in the sidecars and deliberately deferred.

## 8. The one concrete next action

Triage the closing round's four behavioral Blocks - native-command stderr
redirection, home canonicalization, incorrect incomplete states before mutation,
and a selector shared across different homes - against the cited evidence, then
fix the confirmed defects. Reconcile the seven coverage requests with existing
evidence and add only the missing meaningful assertions. The eleven findings are
itemized with file, line and verbatim excerpt in the review sidecar named in the
private morning file. This list corrects the initial morning summary's substitution
of the invalid-mode FYI for the shared-selector Block; the original review is unchanged.

That is one bounded developer pass plus one closing review. Only after the aggregator
returns a verdict that can honestly be recorded as `PASS` is it worth spending the
multi-hour qualification gate, which is the step that produces the retained release
Step 150 needs.

Do not re-run the full acceptance suite to re-establish section 4; those results stand
for commit `7208128` and are superseded only if that code changes.
