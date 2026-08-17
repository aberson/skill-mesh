# Skill Mesh Goal NP Publication 8 recovery worklog

- **Written:** 2026-08-16
- **Coverage:** reconstructed journey through Goal A, Goal NP Publications 1-7, and the uncommitted
  Publication 8 recovery work, with the most detail on the latest diagnostic, repair, test, and review
  cycles
- **Source worktree:** `%LOCALAPPDATA%\SkillMesh\Worktrees\native-codex-skill-parity-plan`
- **Source branch:** `plan/native-codex-skill-parity`
- **Current committed HEAD:** `40d671d75e1aa6c6b31eab70caa8f4d07ed51383` (Publication 7)
- **Current state:** paused deliberately; Publication 8 is uncommitted and has no exact-byte Recovery
  Approval 1 (the bounded repair/revision authorization was narrower)
- **Durability:** this canonical copy is isolated on `docs/goal-np-journey`, so it does not add a path
  to or change the exact Publication 8 candidate; the former reconstruction under
  `dev/docs/investigations` is retained only as a pointer to this document

> This is an operator worklog and recovery aid. It is not an approval, a launcher receipt, a test
> gate, a request record, or Publication 8 evidence. Conversation-only review results are recorded as
> planning history, not converted into durable launcher evidence. The committed `plan.md`, immutable
> prior evidence roots, and any future exact-byte approval remain authoritative in their own domains.

## Executive summary

The immediate failure that started the latest work was real and is now understood. Publication 7's
standalone `Preflight` requested `workspace-write`, but pinned Codex 0.147.0 exposed the canonical
four-line `read-only` permission block. The mismatch was not merely a missing writable-root line.
Windows sandbox configuration had defaulted to `Disabled`, and Codex deliberately downgraded the
requested workspace-write permission profile to read-only.

An explicitly authorized disposable A/B diagnostic proved the narrow correction on this machine:

- without a Windows sandbox override, Codex produced the exact four-line read-only block with
  SHA-256 `29dad5ed6993c5e717376e0a1c84d54ab60ee593510916ac6cee4295e803315d`;
- with the exact shared override `windows.sandbox="unelevated"`, Codex selected the restricted-token
  backend and produced the exact five-line workspace-write block with SHA-256
  `aa613097ace0f175545df760139a7bbc9c505a0feb207dbc2552438ce70db03d`.

Both diagnostic arms exited zero with empty stderr. No model request or `codex exec` occurred, and all
scratch was removed. The launcher now carries that exact scalar through its shared closed arguments for
both debug and execution. The strict five-line permission grammar was retained; it was not weakened to
accept read-only.

This proved the permission-attestation and configuration-resolution correction. It did not prove an
end-to-end sandboxed write or execute the Publication 8 launcher: no model, `codex exec`, P8
`Preflight`, or sandboxed write was run. Those end-to-end boundaries remain unexecuted.

The work then expanded because the Publication 8 launcher requires a repository-root `python -m
pytest` gate before claiming a request. Clean Publication 7 already reproduced several Windows/EOL and
documentation failures. Abraham authorized a bounded baseline-gate repair and Publication 8 revision.
That repair grew the proposed Publication 8 bundle from six files to eight and finally ten files.

The technical repairs are in good shape, but the planning/review process became a treadmill. Each fresh
review found a new contract mismatch after the previous bytes had changed. Five superseded candidate
generations, A through E, are now recorded. The latest correction added real production-entry tests for
both `Run` and `InvokeSavedHandoff`, proving that post-host defect-inventory drift is never graded and
can publish only bounded `AMBIGUOUS` failure evidence.

The last completed checks were green:

- 110 focused tests passed;
- the full cross-family probe module passed 50 tests;
- Python AST, Windows PowerShell AST, HTML/static contract, and `git diff --check` checks passed;
- an independent read-only boundary audit found no blocker or significant gap.

A prior full repository run on an earlier candidate passed `1212 passed, 15 skipped in 3545.63s
(0:59:05)`. Later test/document changes invalidated that exact-byte gate. The final restarted root run
collected 1,227 tests and ran for 1,421.2 seconds (23 minutes 41 seconds), progressing beyond 51% with
no failure output, but Abraham asked to stop and summarize. The exact pytest process tree was terminated
and verified absent. That interrupted run is not a PASS.

No Publication 8 commit, exact-byte Recovery Approval-1 message/file, request ID, `Preflight`, `Run`,
launcher/reviewer-host model call, handoff, request root, state, or evidence root was created. Abraham's
bounded-repair authorization was real but explicitly was not Recovery Approval 1. Nine tracked files
remain modified over the Publication 7 commit; the unchanged schema is the tenth bound bundle file.

## What the latest turns were trying to accomplish

The recent work was not trying to implement the 41-step Goal NP product plan. It was trying to make the
pre-Approval Publication 8 package safe and internally truthful enough that Abraham could later approve
it once, after which the launcher could run without consuming another broken lineage.

The intended sequence was:

1. Explain exactly why Publication 7 exposed read-only permissions.
2. Prove the smallest host configuration correction without a Codex model request.
3. Put that correction in one shared closed argument list used by every debug and exec path.
4. Keep the strict workspace-write permission attestation unchanged.
5. Make the mandatory repository test gate green before any request claim.
6. Freeze one exact bundle and run the ordered review chain:
   `plan-review PASS -> plan-redline PASS -> plan-wrap READY`.
7. Commit that reviewed descendant, derive its request ID, render a non-live handoff, and ask Abraham
   for the exact Publication 8 Approval-1 sentence.
8. Still not run `Preflight` or `Run` until that fresh approval existed.

We completed items 1-5 on at least one earlier candidate and repeatedly repaired item 6, but the final
bytes never completed an uninterrupted full-root gate and final PASS/PASS/READY review chain. Items 7-8
were therefore never reached.

## Evidence classes used in this worklog

This journey mixed several kinds of information. Keeping them separate matters.

- **Committed facts:** Git commits, committed plans, committed reports, and committed manifests.
- **Durable external evidence:** frozen files under `%LOCALAPPDATA%\SkillMesh\Evidence\...` with
  recorded hashes. Publications 3-5 have terminal request roots; Publications 6-7 have approval and
  handoff artifacts but no durable request root.
- **Operator-reported preclaim context:** the JSON printed by a standalone `Preflight`, especially the
  Publication 7 permission hashes. This is trustworthy context but not a fabricated launcher receipt.
- **Disposable diagnostic context:** the authorized A/B `codex debug prompt-input` check. Its result is
  reproducible and recorded in the plan, but its scratch was intentionally removed and it is not a
  request or approval artifact.
- **Planning-review history:** agent review verdicts on changing candidate bytes. These are useful for
  understanding why files changed, but they are explicitly non-evidentiary, non-authorizing, and
  non-reusable.
- **Session-recorded local validation:** command output and narrow review/audit results observed in the
  recent conversation and summarized here. They are useful reconstruction facts, but they are not
  launcher evidence; when bytes later changed or a command was interrupted, they are not a current
  gate.
- **Incomplete gates:** an interrupted pytest run or a review on bytes that later changed. These must
  never be reported as final PASS evidence.

## Journey before Publication 8

### Goal A: establish evidence, then stop rather than infer an architecture

Goal A was an earlier recovery effort under the frozen recovery plan. It deliberately limited itself to
preservation, disposable lifecycle and cross-family experiments, and a Gate A decision packet. It did
not authorize product implementation or live-home mutation.

The main durable sequence was:

1. **Preserve Step 4 work.** Fourteen files were preserved under a recovery manifest. The recorded
   `apply_check` and `hash_match` both passed.
2. **Establish canonical authority.** Commit `8d8b57a` established the plan/status authority and parked
   the named issue set.
3. **Prepare and run the lifecycle fixture.** The initial safety scan needed roughly 141 seconds to
   hash 2.93 GB across 41,435 protected records. Bounds were increased without weakening the record
   limit. Both lifecycle host series ultimately returned `AMBIGUOUS` before host invocation because
   protected Codex database files changed during their safety-preflight intervals and attribution was
   unavailable. No native-lifecycle conclusion was claimed.
4. **Prepare and run the cross-family fixture.** The first attempt exceeded the generic 16 MiB
   evidence cap with a 19,750,121-byte snapshot, so only raw snapshots received a separate 64 MiB cap.
   The next native CLI attempts exposed two preflight mismatches: Codex needed
   `--skip-git-repo-check` for the intentionally empty working directory, and Claude rejected the
   schema draft declaration. Final Codex attempts each performed one real review, returned
   `NEEDS_WORK`, and detected all three seeded defects, but Codex exposed no allowed resolved-model
   field and protected database files changed during the intervals. Claude-host attempts returned 401
   because the saved OAuth token had expired. All final series were honestly `AMBIGUOUS`.
5. **Prepare Gate A.** Focused tests and package-integrity tests passed, both distributions built, and
   the durable external full-gate record reported
   `1203 passed, 15 skipped in 3650.09s (1:00:50)`, exit 0, on the final Goal A candidate.
6. **Run one bounded follow-up.** Abraham approved exactly one quiescent qualification experiment.
   Claude lifecycle `a1` failed before the explicit update command because a fresh consumer exposed the
   candidate-v2 marker where the criterion required installed-v1. The committed stop rule prevented
   the remaining follow-up calls from running.
7. **Stop.** Abraham selected Gate action `stop`, Goal B authorization `no`, and live cutover
   `not-authorized`. Goal A ended with no architecture selected.

Relevant commits include:

| Commit | Purpose |
|---|---|
| `26a2c085d68611630c18b730104350d75b193b0d` | Complete the cross-family experiment journal |
| `0c72392ec51da5201c4f3c17272e2b79a32a055d` | Enforce lifecycle mutation containment |
| `215618be14bbba2aa3130a99dea3fffa96bed071` | Prepare the Gate A decision packet |
| `7d5d0926f0d30b5872e03682ee45e805eef2d8d9` | Record the bounded follow-up approval |
| `50fb9a36db0627da9e71c32d53bf81c4b98e7d4a` | Close Gate A after the bounded follow-up stop |

### Goal NP: a new plan rather than reviving Goal A

After Goal A stopped, Goal NP was planned as a separate two-approval effort for native Claude/Codex
skill parity. Commit `a3eaa8ca32c19584ee8cf550c89a8dfef14f8d45` introduced the detailed plan and
operator proposal. Commit `9c224efda851a3501f130830f5cd22b212fc36f0` revised the model-role mapping.

The plan preserved D01-D10, 41 numbered NP steps, a first approval for the exact plan, and a second
approval for the frozen live cutover. Claude quota constraints made the earlier Claude-led
administrative route unavailable, so the Terra recovery amendment proposed direct Codex
`gpt-5.6-terra`/`xhigh` for the administrative bootstrap and numbered code-step orchestration only.
That did not make Terra a native qualification host, remove Claude from NP-12/NP-40, authorize live
mutation, or add a third approval gate.

Publications 1 and 2 were planning revisions only. No Publication-1 or Publication-2 Approval-1 file
or implementation lineage was found. Abraham accepted D01-D07 and D09-D10 pending Approval 1 and
requested the D08 investigation/revision, but that feedback was not itself approval.

### Publications 3-7

Each publication was a new exact-byte candidate. Earlier approvals could not authorize modified later
bytes. Publications 3-5 created terminal roots; Publications 6-7 failed before claim.

| Publication | Commit | Derived request | Outcome and lesson |
|---|---|---|---|
| 3 | `71a5aea3fd21320d2fbb3cb9228bc52e42cb3215` | `tba-b7e5898e6389ff19b3ce34738f16b47d0a832dfc4625789fbcf4308352f2b1a0` | Request root was claimed, then live-home attestation stopped because `goals_1.sqlite` was locked by the active coordinator. No model, test, Git, or product mutation. The root is terminal and immutable. |
| 4 | `58223098887468953570ecf153494871c5404605` | `tba-461c20be4d35c7255a83d05f91f16c5bccbdd5a36af738360bcedc330ab6b1e4` | Request root was claimed. Windows PowerShell 5.1 exposed an empty `Process.ExitCode` after a successful prompt-input child. Valid prompt JSON was retained, but no `codex exec` or model process ran. The root is terminal and immutable. |
| 5 | `6d292bb37c37944c71ed8b18214fabb23f22869e` | `tba-03e474757a5e0c92e8d3f0bd4c5a0731a742397a43c99d5e027016643fced916` | One real process requested Terra/xhigh, although Codex exposed no independent resolved-model field. Invocation requested workspace-write, but the preceding prompt proof was hard-coded read-only. The model returned schema-valid `BLOCKED`, the launcher classified it as `UNEXPECTED_FAILURE`, and no write was attempted. This was a model refusal caused by the supplied permission story, not an OS write denial. The root is terminal and immutable. |
| 6 | `d0f83210e3092e18a28ee24db20a1af95887c31b` | would have been `tba-cc76394efc1359d75b406ce5a2d2300d5ed41020b5cf7fc972ba3039dc3a6ab0` | Standalone preclaim `Preflight` returned `PERMISSION_ATTESTATION_FAILED`. No durable request root or state was created, scratch was removed, and no model ran. Telemetry was insufficient to prove the exact mismatch. The later claim that only a writable-root line was missing was an unsupported inference and is withdrawn. |
| 7 | `40d671d75e1aa6c6b31eab70caa8f4d07ed51383` | would have been `tba-f3b13b6337e230003d8721ad759b398d31536eae9d9b2bdf0860ff8b1d849568` | Standalone preclaim `Preflight` again returned `PERMISSION_ATTESTATION_FAILED`, now with exact normalized hashes and first-difference telemetry. It proved effective read-only, not merely a missing root line. No durable request root or state was created, staging was removed, and no model or `codex exec` ran. |

The P3/P4/P5 evidence roots and their manifests remain frozen. P6 and P7 approval/handoff bytes remain
frozen, while their expected evidence roots, state paths, exact staging request roots, and staging
publication roots remain absent. None of those lineages may be retried or silently reused.

The exact approval and handoff artifacts currently present on disk are:

| Publication | Exact approved sentence | Approval file | Normalized text SHA-256 | Handoff |
|---:|---|---|---|---|
| 3 | `Approve Goal NP plan Publication 3 with D01-D10 and the Terra orchestration amendment.` | 87 bytes; `33d3e1756ed2bfd661698da3dfdf85a921380efd87fe3d635b777dafe3c6e04b` | `66df8cd413fddd097e80dc63ccfacab221e96c72c795345d14b72ae1ae3474ef` | 5,141 bytes; `8382385b90568e947b7aa1abe53d4089650817fb5a72a33b014d5d19d62bd453` |
| 4 | `Approve Goal NP plan Publication 4 with D01-D10 and the Terra bootstrap recovery amendment.` | 92 bytes; `2f74ea66ac7bdac38b419fd24b7e6caa9479de007bc178e69acd54f9f8b42857` | `1a7698085d7bc12e74d60874e0d64b4d069b039470ab17701541cfe6c77202fe` | 9,615 bytes; `0690c2976b20f665872327a4bc8cc8f17bbea03869c73d52490b28044e54d5e5` |
| 5 | `Approve Goal NP plan Publication 5 with D01-D10 and the Terra bootstrap process-recording recovery amendment.` | 110 bytes; `5ad7472cb113d6965de18204dc1b7f860a0c2982ad1e8152e34547efa714a8e3` | `2d19ad716f3179baf67c67c77d19dfb29697ea5b2e6f2b0a0d1fe87ee03d0f47` | 13,450 bytes; `ee92b0f882772af327d25d0bec82c9d381ff9e2f309611dd0856d0589c62030e` |
| 6 | `Approve Goal NP plan Publication 6 with D01-D10 and the Terra sandbox-attestation recovery amendment.` | 102 bytes; `064e50a53d93dc976cb98b87a5a49d0260d91f88aadddb23bcd8bf60d9be2add` | `ad20542c0d5dc9b77fbab14413998f614ab178ca4949a1269f06c08f24b3407e` | 18,494 bytes; `ae085575b9441080ece62194cd4a3144df809eaa9d70b2ed2fcd76624d455b47` |
| 7 | `Approve Goal NP plan Publication 7 with D01-D10 and the Terra writable-root grammar recovery amendment.` | 104 bytes; `a849c6f49c9557ee7e11bdc4c01f324e17fe260d5abdc648141715d22120f8a5` | `fe5736f56b0edb305ef2e1632d5882a6d85d930c06862d9ec9ce26a28b9a23aa` | 21,345 bytes; `c0554be563284c8fe9eb2f4aa2985505c76d39eb17dd1aeb1313dd78f3b43f81` |

For the three claimed terminal roots, the current durable state and canonical whole-root manifest
identities are:

| Publication | State SHA-256 | Canonical root manifest SHA-256 | Entries |
|---:|---|---|---:|
| 3 | `ae59a6ac7f512d2e399675fe541b916d1710c209a13b45433642cf019a07df97` | `9b01de1f550019a8bf81c23431925b6f38a173ec1ce22023c765a2a8d290cdcf` | 3 |
| 4 | `4517ecd2d5ff948bbcf7763e32686797f65b5112ceb14e71c96c8222e6e12e05` | `893c099e299a5152f26edd912a5bfcdc75bd69e030dfd40653c0365ffe4d5e44` | 9 |
| 5 | `b0e9355ff3f39c1ccca196ae45ebe7c4f042c9fcd2587d84882c7d9af4724f50` | `11f84ea3e5140a2832586f63fc362c97b92286b1663c91df2c80fb7784d6f700` | 17 |

## Publication 7 failure: exact diagnosis

The operator supplied the Publication 7 terminal JSON after `Preflight` failed. Its decisive fields
were:

| Field | Value |
|---|---|
| Verdict | `BLOCKED` |
| Error | `PERMISSION_ATTESTATION_FAILED` / `preclaim-permission-attestation` |
| Expected normalized permission hash | `aa613097ace0f175545df760139a7bbc9c505a0feb207dbc2552438ce70db03d` |
| Actual normalized permission hash | `29dad5ed6993c5e717376e0a1c84d54ab60ee593510916ac6cee4295e803315d` |
| Expected / actual line count | 5 / 4 |
| First differing line | 2 |
| Expected line-2 hash | `06c4b2fd6aab85ab9ea0e5598cbcdead5142d7cb56e851770163c1b9f480338b` |
| Actual line-2 hash | `d9cebe887c2ee11798faa526216e1d4af5d90cd47231862b50eb60cc5ac76464` |
| Durable request root | absent |

Those values independently reconstruct the expected canonical five-line workspace-write block and the
actual canonical four-line read-only block. If only the writable-root annotation had been missing, the
first difference would have been later, not line 2.

The local launcher path explained why ambient configuration could not rescue the request:

- its scratch `CODEX_HOME` received only `auth.json`;
- the shared `Get-ClosedConfigArguments` list did not include `windows.sandbox`;
- debug explicitly requested `workspace-write`, but the effective profile was resolved after Windows
  sandbox configuration;
- the self-generated parser canary rendered its own expected text and therefore could not detect this
  host/config resolution downgrade.

Pinned Codex 0.147.0 source then supplied the missing causal link:

- an absent `[windows].sandbox` resolves to `WindowsSandboxLevel::Disabled` unless another feature
  selects a backend;
- on Windows, a requested `WorkspaceWrite` profile is downgraded to `ReadOnly` when the Windows
  sandbox level is `Disabled`;
- `windows.sandbox="unelevated"` selects the restricted-token backend and prevents that downgrade.

The relevant pinned sources were
[`windows_sandbox.rs`](https://github.com/openai/codex/blob/rust-v0.147.0/codex-rs/core/src/windows_sandbox.rs#L21-L44)
and
[`config_toml.rs`](https://github.com/openai/codex/blob/rust-v0.147.0/codex-rs/config/src/config_toml.rs#L687-L745).

Two tempting workarounds were explicitly rejected:

- accepting read-only as valid would defeat the implementation's required write capability;
- using a cosmetic `default_permissions=:workspace` advertisement could make prompt text look writable
  without selecting the Windows enforcement backend.

## The authorized A/B diagnostic

When asked whether to power through another publication or step back, the honest recommendation was to
diagnose the effective host boundary first. Abraham authorized that bounded diagnostic before more
publication work.

The diagnostic used the pinned Codex binary and disposable scratch only. It ran the prompt-input/debug
shape without a model request:

| Arm | Closed Windows override | Effective permissions | Normalized hash | Lines |
|---|---|---|---|---:|
| A | none | canonical read-only | `29dad5ed6993c5e717376e0a1c84d54ab60ee593510916ac6cee4295e803315d` | 4 |
| B | `windows.sandbox="unelevated"` | canonical workspace-write with one managed writable root | `aa613097ace0f175545df760139a7bbc9c505a0feb207dbc2552438ce70db03d` | 5 |

Both arms exited zero with empty stderr. Scratch was deleted. The repository, live auth/home, prior
evidence roots, and staging absence predicates stayed unchanged. This closed the original preflight
root cause with host-level evidence rather than another inferred grammar edit.

The proof boundary was nevertheless limited: it demonstrated effective prompt-input permissions and
the source/config mapping to the restricted-token backend, not a model-mediated sandboxed write or a
Publication 8 launcher run.

## Publication 8: how a six-file correction became ten files

### Initial six-file candidate

The first Publication 8 revision was intentionally narrow:

1. `plan.md`
2. `documentation/native-claude-codex-skill-parity-plan.md`
3. `documentation/native-claude-codex-skill-parity-terra-amendment.md`
4. `documentation/native-claude-codex-skill-parity-proposal.html`
5. `tools/run-goal-np-terra-bootstrap.ps1`
6. `schemas/terra-bootstrap-result-v1.schema.json`

The launcher added the exact `windows.sandbox="unelevated"` scalar once in the shared closed argument
function, so every preclaim debug, per-call debug, exec, and base argument template consumed the same
setting. The strict five-line permission renderer and attestation stayed unchanged.

Fresh plan-review found a broader operational problem: the launcher would claim a Publication 8 request
root and only then run a full repository gate already known to fail on clean Publication 7 in this
Windows checkout. A claimed root followed by a known-red baseline would create yet another terminal
lineage without testing the sandbox correction. The review also found documentation gaps.

Abraham then authorized a **bounded baseline-gate repair and Publication 8 revision**. This was not
Recovery Approval 1 and authorized no Publication 8 `Preflight`, `Run`, launcher/reviewer-host model
call, Goal NP product implementation, or live mutation. Planning/review agents were used to audit the
candidate; their outputs carried no execution authority.

### What the clean-P7 baseline failures were

The diagnostic partitioning established that most of the suite was healthy and isolated eight
failures:

- a cross-family fixture determinism test computed candidate-tree SHA-256
  `99f1ee0718106ce7c21e3b30797aa8ee4acaaad60268e87c969fd55c74e0a102` instead of the pinned
  `3783ed5a9ead148f4dc13d8da224a021d5465647cf97788aede6afca8e1d1885`;
- package-integrity documentation referred to a non-resolving code-span path token,
  `tests/path/diff`;
- the recovery-plan hygiene test required the exact status row `Provider expansion | PARKED`;
- five release tests failed as a cascade because the staged package reran the same two
  package-integrity checks and therefore did not produce checksums.

The failing partition reported `453 passed, 8 failed, 1 skipped in 879.79s`. Separate slow partitions
were green:

- distribution partition: `237 passed in 814.39s (0:13:34)`;
- legacy-migration partition: `183 passed in 2016.06s (0:33:36)`.

The fixture hash failure reproduced in a clean detached worktree at Publication 7 HEAD, proving it was
not caused by the dirty Publication 8 tree. Windows Git had `core.autocrlf=true`; the candidate source
file had CRLF worktree bytes but an LF committed blob. The fixture copied raw worktree bytes and then
hashed them, while the pinned expected identity represented LF content. The same issue later appeared
for `expected-defects.json`: raw CRLF SHA-256
`24c336217fba1a6d1d177b754a34be77275e0c797a50d48ea0a7e5d9401c2752` versus canonical LF SHA-256
`98baaa178e41dc23e5de70e3161de78c66b9c91052c4d0d99295ae1a8928ed37`.

### Bounded baseline repairs

The authorized repair made these changes:

- `create_fixture.py` canonicalizes CRLF and lone CR to LF at the candidate-copy/hash boundary and at
  the declared defect-inventory text identity boundary. The pinned base, candidate, tree, and diff
  identities remain unchanged.
- Existing plan/amendment/proposal text was corrected so the path token resolves and the provider
  expansion row is explicitly `PARKED`.
- `tests/distributions/test_path_choke_point.py` gained one exact whole-file exemption for the one-off
  Publication 8 launcher. This was chosen instead of disguising 22 reported write sites with fake safe
  variable names. The rationale is narrow: the launcher has no consumer-home parameter; its only
  caller-supplied path is an exact approval path and never a mutation target; its repository, ADMIN,
  Evidence, and Staging writes are fixed and independently bounded; the exemption must be removed if
  that boundary broadens. The scanner itself was not weakened.

This expanded the candidate from six to eight files by adding `create_fixture.py` and the path-choke
test.

### Why the bundle later expanded from eight to ten files

A later plan-redline review found that one unqualified field name,
`defect_inventory_sha256`, represented two different byte domains:

- canonical LF builder bytes in `create_fixture.py`;
- raw checkout bytes in the probe's sealed artifact/receipt path.

That made the clone-independent identity claim false end to end. Fixing only the builder would leave
the runtime probe and report ambiguous about what the hash meant.

The repair therefore added two more bound files:

9. `experiments/recovery/cross-family-fixture/probe.py`
10. `tests/experiments/test_cross_family_probe.py`

The probe now:

- canonicalizes CRLF and lone CR to LF at the source/sealing boundary;
- compares the canonical source digest with the fixture-builder result before writing handoff
  artifacts;
- carries one digest through the artifact, receipt, prepare manifest, loader, and report identity;
- rejects fixture/receipt drift before use;
- uses the same bounded inventory bytes for digest verification, JSON parsing, and grading.

Tests cover LF, CRLF, and lone-CR source variants plus deliberate identity drift.

### Direct `Run` and saved-handoff closure

Another fresh review found that the monolithic `Run` path performed `prepare()` and then called
`execute_review()` directly. It bypassed `load_prepared()`, while `InvokeSavedHandoff` did reopen the
sealed handoff. That meant the documented sealed-handoff invariant did not actually hold for both
production actions.

The corrected production sequence is now:

- `Run`: `prepare -> load_prepared -> execute_review`;
- `InvokeSavedHandoff`: `load_prepared -> execute_review`.

After the reviewer host returns, `execute_review()` validates the response contract, performs one
bounded read of `defect-inventory.json`, checks those bytes against the receipt digest, parses those
same bytes, and only then permits grading.

### The final `AMBIGUOUS` routing correction

The first negative tamper regression called `execute_review()` directly. It correctly proved that a
digest mismatch raises before grading and before that function writes `report.md` or
`MANIFEST.sha256`. The documentation then overgeneralized that direct-function fact into "before report
publication."

Production `main()` has a deliberate wider contract: after it owns an evidence directory, it catches a
post-host failure and tries to publish bounded `AMBIGUOUS` failure evidence. That path writes
`report.md` and `MANIFEST.sha256`, returns `status=COMPLETE`, and sets
`experiment_result=AMBIGUOUS`. Here `COMPLETE` means evidence publication completed; it does not mean
the experiment passed. `AMBIGUOUS` means the evidence supports no conclusion.

Suppressing all failure evidence would have conflicted with the existing recovery architecture and
discarded useful post-host forensic bytes. The narrow correction was therefore to preserve the
architecture and fix the tests and wording:

- both `Run` and `InvokeSavedHandoff` now go through real `main()` routing in the negative regression;
- the fake reviewer mutates the sealed inventory after host return;
- exactly one bounded inventory read occurs in the grading path;
- grading is never called;
- output is `COMPLETE` plus `AMBIGUOUS`, with zero detected defects and unavailable/uncertain reviewer
  fields;
- the report records the digest-integrity failure and does not repeat the synthetic reviewer summary
  as a trustworthy parsed result;
- the final manifest hashes every retained file, including the actually mutated inventory bytes;
- no fallback report is written.

The four planning documents now say drift fails before grading and before **normal/conclusive** result
publication; only the bounded `AMBIGUOUS` failure pair may be sealed.

## Publication 8 review generations A-E

Every row below describes superseded planning bytes. None is an approval or reusable gate result.

| Generation | Bundle | Review outcome | What changed next |
|---|---:|---|---|
| A | 6 files | `plan-review FAIL` | The launcher would claim before a known-red baseline gate; documentation gaps remained. Abraham authorized only the bounded baseline repair and P8 revision. |
| B | 8 files | `plan-review PASS`, then `plan-redline FAIL` | Fixed contradictory review ordering, incomplete operator/controller sequence, proposal section ordering, source-of-truth/base-hash metadata, and incomplete revision grammar. Any B PASS was invalidated when bytes changed. |
| C | 8 files | `plan-review PASS`, then `plan-redline FAIL` | Found the same `defect_inventory_sha256` name covering canonical builder bytes and raw probe bytes. The bundle expanded to ten files to repair runtime identity end to end. |
| D | 10 files | `plan-review FAIL` | Found monolithic `Run` bypassing `load_prepared`, missing post-host inventory enforcement coverage, and incomplete review provenance. Redline and wrap did not run. |
| E | 10 files | `plan-review FAIL` | Found that the negative test called `execute_review()` directly and the documents claimed no report, while production `main()` intentionally publishes bounded `AMBIGUOUS` failure evidence. Redline and wrap did not run. |

Other material corrections found during these reviews included:

- replacing a legacy `plan-review -> plan-wrap -> plan-redline` sequence with the single required
  `plan-review PASS -> plan-redline PASS -> plan-wrap READY` sequence;
- restoring the complete post-approval controller chain after launcher
  `Preflight -> Run -> launcher Inspect`: controller `Prepare -> zero-model Sync -> controller Inspect
  -> RunBootstrapNP01/NP-01`;
- moving the proposal's `What I heard` section into the required location and putting recovery history
  under its rationale;
- making the detailed plan the canonical executable source while `plan.md` remains the mutable
  status/authority pointer;
- aligning the formal feedback grammar across D01-D10, Terra recovery, NP-01 through NP-41, and named
  sections;
- keeping the unchanged result schema described as unchanged rather than implying a schema revision;
- preserving the exact ten-file order and 22-field request identity;
- recording every failed review generation as non-evidentiary, non-authorizing, and non-reusable.

## Test and validation history during Publication 8

This section intentionally distinguishes final gates from iteration checks.

### Useful green checks

- A formerly failing fixture determinism test passed after LF canonicalization.
- A focused fixture subset passed 5/5.
- The path-choke suite passed 9 tests, including allowlist liveness and a red-anchor check.
- Before the E-generation production-routing correction, the then-current combined focused gate passed
  295 tests. That result belongs to those earlier bytes.
- The entire cross-family probe module eventually passed 50 tests.
- The final combined focused command passed 110 tests in 9.60 seconds across the probe, path-choke,
  recovery-plan hygiene, and cutover-handoff areas.
- Python AST parsing passed for the changed Python files.
- Windows PowerShell AST parsing passed for the launcher.
- HTML balance, unique IDs, section order, approval hashes, handoff token count, ten-file order, and
  displayed detailed-plan hash checks passed.
- `git diff --check` passed, with only expected `core.autocrlf` advisory warnings.
- An independent read-only audit of the post-E production-routing correction reported no blocker or
  significant gap. It was a narrow boundary audit, not `plan-review`, `plan-redline`, or `plan-wrap`.

### Full-root gate that passed, then became stale

One literal repository-root run on an earlier candidate completed successfully:

```text
1212 passed, 15 skipped in 3545.63s (0:59:05)
```

Later E-generation test and documentation changes changed the exact bundle, so this is strong
regression evidence but not the final Publication 8 gate.

### Final restarted full-root gate that was stopped

The final command was the required literal repository-root invocation:

```text
python -m pytest
```

It collected 1,227 tests. After 1,421.2 seconds it had progressed from the root-only suites through
distribution and host-inspection coverage and into the slow legacy-migration partition, with no
failure output. Abraham observed that the overall effort had been running all night and asked whether
we should stop, summarize, and try something else.

The honest answer was yes: the pytest process itself was healthy, but the larger publication/review
loop was consuming too much time for diminishing returns. Only the exact pytest tree was terminated:

- pytest root PID: `33004`;
- active child at termination: PowerShell PID `27780`;
- wrapper then exited nonzero because the child was intentionally stopped;
- a subsequent process check proved no `python -m pytest` process remained.

The buffered output showed progress beyond 51% and no failures up to the stop point. This interrupted
run is **not** a PASS and must never be represented as one.

One small test-authoring stumble is worth recording: the first production-route regression run stayed
on the `WHAT_IF` path because the shared request helper defaults `what_if=True`. The test was corrected
to set `what_if=False`; the focused rerun and full probe module then passed. This was a test setup issue,
not a production defect.

## Current uncommitted Publication 8 snapshot

The branch still points to the approved Publication 7 commit. There are nine modified tracked files and
no Publication 8 commit. The schema is unchanged but is the tenth file in the proposed exact bundle.
Relative to Publication 7 HEAD, the current nine-file tracked diff contains 1,476 insertions and 341
deletions.

| # | File | Bytes | SHA-256 | Git state |
|---:|---|---:|---|---|
| 1 | `plan.md` | 43,737 | `cba2cfd297bdbaf16a82536ea0892897fed2746c534d6fe4b78a2a180cae63c1` | modified |
| 2 | `documentation/native-claude-codex-skill-parity-plan.md` | 388,840 | `bc00170453275b72c13060cf94a61ddca2aa1d259cf2420a33725bec826cdf06` | modified |
| 3 | `documentation/native-claude-codex-skill-parity-terra-amendment.md` | 91,594 | `d50953b43212312ac166ab2a30c254b798bfe07954c801c0026bfeb3a52fbc1b` | modified |
| 4 | `documentation/native-claude-codex-skill-parity-proposal.html` | 64,021 | `462e884654ae4dbbeab730d09bf157411c6b1d6718256b8bbcfcded88d370def` | modified |
| 5 | `tools/run-goal-np-terra-bootstrap.ps1` | 165,739 | `910bc95839161d40b71bdc985e861b0c9f503d3ba76d744ca17e884521581182` | modified |
| 6 | `schemas/terra-bootstrap-result-v1.schema.json` | 784 | `3b6e35eab00a036e48ceb011633c2ad15aebca1af73c59058dd48a92d6243f06` | unchanged/bound |
| 7 | `experiments/recovery/cross-family-fixture/create_fixture.py` | 7,431 | `56eb721ae99cbd0c38b6c5746182f4dc6940befe1cbf3b7f85deb787c4aa8bf0` | modified |
| 8 | `experiments/recovery/cross-family-fixture/probe.py` | 70,087 | `1c79c85a4172dc0a7e6b040c2a16be05396659954aa333a49cf0351bf058e2ac` | modified |
| 9 | `tests/experiments/test_cross_family_probe.py` | 91,413 | `bf276543bda9a1659be75fd86d20513860a70f0db5da45bfe823ce2075a5e9bc` | modified |
| 10 | `tests/distributions/test_path_choke_point.py` | 27,658 | `f7ab24822136abdffcce74f0e0d4420f77cf6d74c9736629d34125cd569ca22f` | modified |

The major current source anchors are:

- launcher shared Windows override: `tools/run-goal-np-terra-bootstrap.ps1:874`;
- probe LF canonicalizer: `experiments/recovery/cross-family-fixture/probe.py:594`;
- post-host review boundary: `experiments/recovery/cross-family-fixture/probe.py:1014`;
- bounded ambiguous publisher: `experiments/recovery/cross-family-fixture/probe.py:1126`;
- real production-route tamper regression:
  `tests/experiments/test_cross_family_probe.py:1815`;
- exact launcher path exemption: `tests/distributions/test_path_choke_point.py:169`.

These line numbers describe the snapshot above and may move after future edits.

## Safety and authority state at pause

At the time of pause:

- Publication 8 had no commit and no derived request ID.
- No exact-byte Publication 8 Recovery Approval-1 message/file or external handoff existed. Abraham's
  earlier bounded-repair authorization was not that approval.
- No Publication 8 `Preflight` or `Run` was invoked.
- No Publication 8 evidence root, state, request root, or staging lineage existed.
- No Goal NP implementation, skill adoption, issue synchronization, launcher/reviewer-host model call,
  product mutation, live home write, or live cutover occurred. Planning/review agent calls did occur,
  but they were non-authorizing review context.
- Publications 3-5 remained frozen terminal roots.
- Publications 6-7 retained their exact approval/handoff artifacts and absence predicates.
- All named ADMIN outputs remained absent during the audits that checked them.
- The exact pytest process tree was stopped and no orphan remained.
- The new worklog itself was placed outside the Publication 8 worktree so it would not silently create
  an eleventh bundle file or alter the candidate hashes. It is presently an untracked on-disk record;
  do not sweep the dirty workspace into a commit merely to preserve it. Use a scoped add/commit or
  separate backup when that repository boundary is safe.

The planned but **not yet supplied** Publication 8 Approval-1 sentence remains:

```text
Approve Goal NP plan Publication 8 with D01-D10 and the Terra Windows sandbox-enforcement recovery amendment.
```

Its normalized text SHA-256 is
`c54648e8eedfebb9181ea04043cca948692a78e35bd3f42b7cca92352be74c79`. If rendered as the
canonical 110-byte UTF-8 file with one LF, its SHA-256 is
`2c9b4f34f0c53a634725f608b724558cf920a9e0d606b4a09707d7e15744ce7e`.

Supplying that sentence before a final reviewed commit and handoff would be premature. Earlier
Publication 3-7 approvals cannot authorize the current bytes.

## Things not to repeat

1. **Do not retry Publications 3-7.** P3-P5 are terminal claimed lineages; P6-P7 are immutable
   preclaim publications. Modified bytes require a new publication.
2. **Do not revive the missing-root-only explanation.** Publication 7 proved the mismatch began on
   line 2 with effective read-only permissions.
3. **Do not weaken the grammar to accept read-only.** The implementation needs real restricted
   workspace-write enforcement.
4. **Do not use cosmetic default permissions instead of the Windows backend.** Prompt text without
   OS enforcement would be a false proof.
5. **Do not trust only a self-rendered parser canary.** It cannot detect host configuration resolution;
   the effective Codex debug surface must be checked.
6. **Do not claim a full gate from partitions, focused tests, or the interrupted 1,227-test run.** One
   final literal root invocation must finish on the exact frozen bytes if the existing plan is resumed.
7. **Do not reuse a review PASS after any byte changes.** That caused repeated invalidation throughout
   generations B and C.
8. **Do not test only `execute_review()` when the claim concerns `main()`.** Production error routing
   intentionally publishes bounded `AMBIGUOUS` evidence.
9. **Do not let another review finding trigger an immediate hour-long rerun.** Consolidate all findings,
   make one batch correction, run focused checks, then decide whether the candidate is still worth a
   full gate.
10. **Do not silently add this worklog to the Publication 8 bundle.** It is a workspace investigation
    record, not publication content.

## Recommended way to resume

The last recommendation was to stop expanding the current ten-file publication. Preserve the work,
separate baseline maintenance from the sandbox-enforcement publication, and give the final candidate
one bounded review cycle rather than continuing the all-night loop.

### Recommended path: separate the concerns

1. Re-verify the current worktree against the hash table above.
2. Preserve the current delta as a scoped patch or explicitly named checkpoint before any reset,
   rebase, or split. Do not use `git reset --hard` or discard the dirty tree.
3. Produce a read-only change map before splitting anything. The current documents intertwine
   baseline, publication, and review-history edits, so this is a design split, not a blind cherry-pick
   of the ten-file delta.
4. Separate the generally useful baseline code/test repairs into their own maintenance checkpoint:
   cross-platform fixture text identity, the probe's canonical sealed-inventory identity, and its
   production-route regression. Re-author any clean-P7 package-integrity documentation correction in
   its actual canonical owner rather than copying P8 history wholesale.
5. Keep the P8-specific launcher, its narrowly justified path-choke exemption, and the exact
   publication documents with the minimal Windows sandbox-enforcement publication. Its conceptual
   change should remain the single shared `windows.sandbox="unelevated"` override plus the exact docs
   needed to explain and bind it.
6. Run focused tests while iterating.
7. Run one uninterrupted literal root `python -m pytest` only when the bytes are otherwise frozen.
8. Run one consolidated `plan-review -> plan-redline -> plan-wrap` chain. If another review discovers
   materially new scope, stop and reconsider instead of automatically entering generation F/G/H.

This restructuring may require a new publication description and exact bundle. It should not be
performed implicitly; it needs an explicit operator decision because it changes how the current
ten-file candidate is organized.

### Alternative: resume the existing ten-file candidate

If keeping the current bundle is preferable:

1. Confirm all ten hashes in this worklog.
2. Re-run the 110 focused tests and static checks only if the environment or bytes changed.
3. Run exactly one uninterrupted repository-root `python -m pytest` and save its terminal summary.
4. Freeze all ten hashes.
5. Restart formal review from the beginning on those exact bytes:
   `plan-review PASS -> plan-redline PASS -> plan-wrap READY`.
6. If all three succeed with stable hashes, create a descendant commit without amending Publication 7,
   derive the 22-field request ID, render the 15-token external handoff, and only then ask Abraham for
   the exact Approval-1 sentence.
7. Do not invoke `Preflight` or `Run` in that same planning step.

### Hard stop conditions for either path

Stop and summarize again if:

- a proposed correction expands beyond the authorized baseline/sandbox boundary;
- a reviewer finds a new architectural concern rather than a local contract defect;
- the final root suite fails for a reason not reproduced at clean baseline;
- any P3-P7 artifact or absence predicate changes;
- a Publication 8 request/evidence root appears before fresh approval;
- current dirty bytes no longer match the preserved patch/checkpoint and the difference cannot be
  explained.

## Quick pickup checklist for a new window

1. Open the worktree at
   `%LOCALAPPDATA%\SkillMesh\Worktrees\native-codex-skill-parity-plan`.
2. Run `git rev-parse HEAD`; expect
   `40d671d75e1aa6c6b31eab70caa8f4d07ed51383`.
3. Run `git branch --show-current`; expect `plan/native-codex-skill-parity`.
4. Run `git status --short`; expect exactly the nine modified tracked paths listed above and no new
   Publication 8 artifact.
5. Rehash the ten bundle files and compare with the snapshot table.
6. Confirm no `python -m pytest` process is left from the interrupted run.
7. Read the current `plan.md` Publication-8 review correction record before editing.
8. Decide explicitly between the separated-maintenance path and resuming the ten-file candidate.
9. Do not invoke the launcher, Codex, `Preflight`, `Run`, or an external handoff as an orientation step.

## Source map

The main reconstruction sources were:

- current `plan.md`, especially the Publication 3-7 records, Terra recovery amendment summary,
  Publication 8 review correction record, Goal A journal, and Gate A journal;
- Git history from `26a2c08` through Publication 7 commit `40d671d`;
- the current uncommitted diff and exact file hashes;
- the operator-supplied Publication 7 preflight JSON;
- the authorized A/B diagnostic results recorded in the current plan/amendment;
- test summaries and formal review results from the recent conversation window.

Early history is reconstructed primarily from committed journals because additional commands and
conversation context existed in a previous window. If that earlier window contains a more precise
sequence or omitted artifact, add it here as a clearly sourced correction rather than rewriting an
immutable prior record.
