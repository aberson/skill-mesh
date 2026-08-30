# Phase IS completion runbook

**Status:** ACTIVE COMPLETION OVERLAY — Step 108, C2V, and C2A are certified DONE. C2E is
planned but not authorized for execution; C2N, C2P, Step 108P, and Step 109 remain blocked.
**Created:** 2026-08-27.
**Scope:** completion coordination for existing Phase IS units 108, 108P, and 109. The `C*` labels
below are runbook stages, not new Phase IS units and not inputs to issue synchronization.

## 1. What This Feature Does

**Goal:** finish Phase IS without collapsing its code/operator boundary or certifying stale
evidence. The dependency chain is:

```text
C0 build-step capability verdict
  -> SUPPORTED: C1 Step 108 review provenance and detached root gate
  -> CONTRACT_DRIFT: C0R canonical repair -> C0A activate -> repeat C0
  -> UNSUPPORTED: operator selects a named supported environment -> repeat C0
C1
  -> C2 operator route decision
  -> C2V validate and seal the remote route record
  -> C2A mandatory route resolution
       -> core-uat-mode: seal no-amendment result
       -> operator-subsection-override: land and seal authoritative plan amendment
  -> C2E provision and seal a dedicated disposable C2N–C4 driver-test environment
  -> C2N schema, nonce, and pre-implementation input locks
  -> C2P reviewed build-step-sized Step-108P implementation plan
  -> C3 execute the Step-108P subplan, lock the candidate, and certify it
  -> C4 attended Step 109 acceptance
  -> C2E.33 perform mandatory terminal disposition and retain permitted evidence
  -> C5 phase closeout
```

This runbook coordinates that chain. It does not replace requirements in the accepted phase plan,
invent a third route for Step 109, or authorize a Step-109 host action before its prerequisites pass.

## 2. Existing Context

### 2.1 Authority and conflict order

Use these sources in this order:

1. `plan.md` owns mutable execution status.
2. `documentation/instruction-file-symmetry-plan.md` owns the accepted Phase IS contract and the
   Done-when clauses for Steps 108, 108P, and 109.
3. `documentation/findings/instruction-file-symmetry-uat.md` owns the frozen Step-108 evidence and
   the Step-108P/109 packet specification.
4. This completion runbook owns stage ordering;
   `documentation/phase-is-disposable-c2n-c4-environment-plan.md` owns only the subordinate C2E
   topology, provisioning, readiness, handoff, and disposal contract.
5. Issue #152 is closed as certified DONE; open issues #162 and #153 coordinate the remaining
   units. When an issue body and a newer comment disagree, verify the Git object named by the newer
   comment before using it.
6. `documentation/findings/phase-is-codex-handoff-2026-08-26.md` contributes only its surviving
   §§0 and 4–6. Its removed status snapshot is not authority.

Issue #163 is a closed historical checkpoint. Its earlier user acceptance testing (UAT) hash and
PowerShell-fence count are superseded and must not be used for certification. Issue #159 remains a
deferred external command-line-interface (CLI) drift track and is outside the Phase IS completion
chain.

### 2.2 Verified orientation snapshot

This snapshot was taken before this runbook was added. Re-run `git status --short --branch` and
`git log --oneline -5` at each stage boundary because other sessions may advance `main`.

| Fact | Verified value | How to re-verify |
|---|---|---|
| Pre-runbook `main` | `ebf8588a21c507a64c6a1228a373a052eb8b04ba` | `git rev-parse HEAD` |
| UAT Git blob | `bd1c9205b80c468dcbb4ef64da5b1532e1cfba06` | `git rev-parse HEAD:documentation/findings/instruction-file-symmetry-uat.md` |
| UAT raw 256-bit Secure Hash Algorithm (SHA-256) | `15043DB9FFA0BAE7F5D8FC0B33A7F90964DBD72505FB035B219FC3BE0BC6D612` | Hash raw file bytes |
| UAT byte shape | 140,728 bytes; 1,928 line-feed (LF) bytes; zero carriage-return (CR) bytes | Enumerate raw bytes |
| UAT fences | 34 total; 24 PowerShell-bearing; 18 terminating Step-108P blockers | Enumerate, classify, and parse each fence |
| Step 108 | LANDED / CERTIFICATION PENDING | Phase plan Step 108 and issue #152's newest verified comment |
| Step 108P | BLOCKED BEFORE IMPLEMENTATION | Phase plan Step 108P and issue #162 |
| Step 109 | BLOCKED BEFORE GRADING; behavioral cells blank | Phase plan Step 109 and issue #153 |
| DONE-gate baseline | Current value is owned in one place | Read `documentation/phase-75-baseline.md` immediately before a root-gate launch |

Two independent Git-object reviews of commit `81e8062` and the UAT blob above reported zero High
and zero Medium findings. They remain useful supporting evidence. Their dispatch provenance did not
demonstrate the current `build-step` parent-private hash-based message authentication code (HMAC)
and fresh-context protocol, so C0 decides
whether they can be promoted or must be repeated. No sentinel-backed repo-root gate covers the
current completion bytes.

### 2.3 Why the execution is split

This is not one unattended `/build-phase` span. C0 is a capability/contract diagnosis, C2 is an
operator-owned route decision, C2E prepares and proves a disposable security substrate, C2N is a technical design lock, C2P turns those frozen inputs into a
reviewed build-step-sized implementation plan, C3 is an aggregate build/certification envelope, and
C4 is attended operator acceptance. C3 is never dispatched as one producer context: it executes the
C2P subplan one slice at a time, then freezes and certifies the integrated candidate. Use separate
runs at those boundaries. A halt at one boundary preserves later stages as blocked; it does not
authorize a same-context producer/reviewer substitution or move containment work into Step 109.

### 2.4 Terms used here

- **UTF-8** is the Unicode Transformation Format, 8-bit encoding. **JSON** means JavaScript Object
  Notation, **OS** means operating system, **API** means application programming interface, **UTC**
  means Coordinated Universal Time, **HTTPS** means Hypertext Transfer Protocol Secure, **URL** means
  uniform resource locator, and **NUL** is the zero byte.
- **D10** and **D11** are design decisions 10 and 11 in the
  accepted Phase IS plan; D10 owns the five instruction-file behavior rows and D11 owns the bounded
  single-owner/citer contract.
- `build-step` uses an **HMAC-SHA-256** key kept by the parent orchestrator to authenticate a terminal
  verdict written outside the worktree.
- **Candidate lock** means one immutable Git commit/tree/blob set plus the source, tool, generated,
  and test inputs whose review and gate results are being claimed.
- **File identity** is uppercase `<16-hex volume serial>:<32-hex file ID>` obtained through
  `FILE_ID_INFO` from the same retained handle used for both final-path reads. A caller path or a
  later path reopen is not identity evidence.
- **Receipt hash** is uppercase 64-hex SHA-256 over the exact strict-UTF-8 receipt bytes. **Git commit,
  tree, and blob IDs** retain Git's native 40-hex SHA-1 spelling in this repository.
- **`tool_use_id`** is an opaque, non-empty JSON string issued by the pinned Claude host in a
  validated `PreToolUse` event. It is compared ordinally with no case folding or Unicode
  normalization and is scoped by the receipt-bound session plus host process identifier (PID). The
  guard accepts one active grant for that pair, rejects duplicate/replayed pre-events and any second
  terminal event, and closes it only on the correlated `PostToolUse` or `PostToolUseFailure` result.
  Hook clients, the native guard, kernel capability, and private result receipt consume the exact
  value; public evidence carries only the result digest.
- **Verdict run ID** is a parent-generated version 4 universally unique identifier (UUIDv4) passed as `--verdict-run-id` to the `build-step`
  orchestrator and matched exactly by the parent verdict consumer. For each invocation the parent
  also generates a cryptographically random 32-byte key encoded as 64 lowercase hex and creates the
  durable verdict path `skill-mesh/build-step-verdicts/{verdict-run-UUID}.json` below the platform
  temp directory. The UUID is not reused. The parent alone retains the key through terminal verdict
  classification, then discards it; the run ID, path, and key are absent from producer/reviewer
  prompts, environments, mounts, worktree files, logs, and reports. The parent consumes the sidecar
  with `classify_verdict(path, expected_run_id, expected_secret)` and fails closed on any mismatch.
- **UNC** means Universal Naming Convention path, **SUBST** means a Windows substituted drive,
  **PID** means process identifier, and **MCP** means Model Context Protocol. **SDK** is the Windows
  Software Development Kit; **WDK** is the Windows Driver Kit.
- **RNG** means random number generator. A **DOS-final path** is the Windows drive-letter final-path
  spelling; a **volume-GUID-final path** uses the globally unique identifier (GUID) volume spelling.
  **PE** means Portable Executable and **DLL** means dynamic-link library.

## 3. Scope

### In scope

- Establish whether this Codex host can satisfy `build-step`'s isolated producer, isolated reviewer,
  parent-private verdict-key, durable sidecar, and reviewer-authority boundaries.
- Certify the already-landed Step-108 evidence with valid review provenance and a stable detached
  repo-root gate.
- Obtain one explicit route choice on #153, then freeze the nonce contract consumed by Step 108P.
- Prepare and certify one dedicated disposable x64 Windows execution guest for driver-, policy-,
  boot-, and genuine-host-sensitive C2N/C3/C4 evidence plus one isolated signer appliance for exact-
  object signing, while keeping the coordinator security posture unchanged.
- Implement, review, and certify the Step-108P containment packet under #162.
- Run the five D10 rows, the fixed-point check, both host-delivery checks, the two remote evidence
  publications, and cleanup as attended Step 109 work under #153.
- Update status surfaces, issues, evidence indexes, and the repository at phase closeout.

### Out of scope

- Treating issue #163's stale checkpoint values as current evidence.
- Implementing containment code or filling behavioral observations during Step 109.
- Installing into or cleaning the real user profile. The existing skill home is an owned/junctioned
  tree and is evidence, not a disposable fixture.
- Installing or changing certificates, Code Integrity/App Control/AppLocker policy, Secure Boot,
  BCD/boot configuration, firmware, SDK/WDK, or driver state on the coordination workstation.
- Fixing #159's `goblin` or `citation-needed` instruction-file discovery.
- Fixing the separate `skills/plan-init/core.md` provider-adapter/shared-citation claim identified
  after Step 107. That contract-owner correction needs its own bounded change.
- Running Codex parity (Phase CP) milestone 3 (M3) or any later instruction-file migration.

## 4. Impact Analysis

| File or surface | Change type | Reason | Verified |
|---|---|---|---|
| `documentation/phase-is-completion-plan.md` | New now | Fresh-context completion ordering and gates | This file |
| `documentation/instruction-file-symmetry-plan.md` | Link now; route-2-only amendment in C2A; status later | Make the subordinate runbook discoverable, own the route-2 authorization if selected, and mark units only after evidence exists | Steps 108–109 inspected |
| `documentation/findings/phase-is-route-decision.json` and `documentation/findings/phase-is-route-decision.selector` | New in C2V | Canonical, committed validation plus an exact two-value Git-blob selector for the operator's remote route record | Planned-new; absent at orientation |
| `documentation/findings/phase-is-route-resolution.json` | New in C2A | Sealed branch result; records either no amendment for the core route or the exact amended plan blob for route 2 | Planned-new; absent at orientation |
| `documentation/phase-is-disposable-c2n-c4-environment-plan.md` and proposal HTML | New before C2E | Provider-neutral guest contract, reviewed execution decomposition, and operator redline | Planned after the workstation C2N prerequisite stop |
| `tools/phase_is_environment.py`, `tools/phase-is-environment/**`, and `tests/phase-is-environment/**` | New in C2E.1–C2E.3 and C2E.5–C2E.28 | Strict environment CLI/schemas/verifier, signed-wait materializer/selector, coordinator fact collector, selected-provider connector, guest facts/S1/trust/R0/rollback/disposition/retention and direct emergency actions, redaction, and planted negatives | Planned-new |
| `documentation/findings/phase-is-c2e-environment.json` | New in C2E.31 | Redacted immutable guest readiness input for C2N | Planned-new |
| `documentation/phase-is-step-108p-build-plan.md` | New in C2P | Build-phase-compatible, one-slice-per-step implementation plan derived from C2N's frozen contracts | Planned-new; absent at orientation |
| `documentation/findings/instruction-file-symmetry-uat.md` | Modify in C3/C4 | Replace Step-108P blockers, then record operator observations | Current blob and fence inventory verified |
| `tools/phase-is-uat/**` | New from C2N through C3 | Contract records, schemas, native preparation, guardian/launcher, broker, bundle, and cleanup | Directory absent at orientation |
| `tests/phase-is-uat/**` | New in C3 | Positive, negative, identity, containment, schema, and cleanup coverage | Directory absent at orientation |
| `skills/plan-init/core.md` and `skills/repo-update/core.md` | Conditional in route 1 | Add a core-supported safety-gated UAT mode | Both are distribution inputs; `plan-init` is representative-report input |
| `documentation/release-candidate-report.md` | Conditional in route 1; no-diff regeneration gate in C0R | Refresh representative emitted hashes only when `skills/plan-init/core.md`, another representative shared core, or its Claude/GPT adapter input changes; a Codex-only adapter edit must regenerate byte-identically | The representative fixture names `plan-init` and `build-phase`, but its scenarios select only Claude/GPT adapters and fingerprint the shared core |
| `skills/build-step/providers/codex.md`, `skills/build-phase/providers/codex.md`, `_shared/build_step_verdict.py`, `_shared/test_build_step_verdict.py`, `tests/package-integrity/test_codex_agent_isolation_contract.py` (new), `documentation/providers/codex.md`, and `documentation/providers/README.md` | Conditional before C1 | Narrow remedy if C0 returns `CONTRACT_DRIFT` | The build-step/build-phase adapters and active provider docs repeat the stale host-wide claim; the shared helper's opening contract prose misstates which values cross dispatch |
| `config/skill-manifest.json` and `tests/package-integrity/expected_inventory.json` | Regenerated when documentation inventory changes | Keep generated inventory synchronized | `tools/gen_manifest.py` owns both artifacts |
| `documentation/phase-75-baseline.md` | Evidence update after a successful root gate when counts move | Preserve the single baseline owner | Current owner inspected |
| `plan.md`, `README.md`, the phase plan, and issues #152/#162/#153/#143 | Status updates | Record evidence and unblock the next owner | Current status and issue states inspected |

Route 2 must prove that its implementation does not modify a distribution input before omitting the
core and release-report rows above. That proof is a gate, not an assumption.

## 5. New Components

### Completion runbook

This file is the durable orchestration overlay. It contains no product requirement that is absent
from the phase plan or UAT except the explicit nonce default in §6 D5 and the sequencing needed to
resolve the build-step capability conflict.

### Step-108P packet

C3 creates the packet already specified by Phase IS Step 108P and UAT §§1.8/2.0:

- an admitted native preparation/guardian/launcher root;
- a precompiled helper and self-contained executor bundle;
- closed schemas and parsers for receipts, native results, and public attestations;
- a three-receipt chain: pre-build, launch attestation, and readiness;
- handle-retained root identity, handle-coupled reads, process/image/argument/environment rails,
  and the kernel write-containment rail;
- mode-specific direct-exec hooks and secret-presence rules;
- remote evidence publication and no-follow cleanup; and
- negative mutations for each fail-closed boundary named in the accepted packet.

The four created roots are the combined scratch install-home/project root, scratch config root,
fresh build root, and durable evidence-export root. Cleanup targets the first three. The evidence
export is retained.

C2N fixes the machine-exact schema design before C3 writes runtime code; C3 then materializes those
closed schemas and preserves these minimum shapes:

| Artifact | Minimum bound fields and constraints | Consumer |
|---|---|---|
| Schema-design record, `skill-mesh/phase-is-schema-design/v1` | `schema`; ordinal, duplicate-free `artifacts` array whose entries bind artifact name/version, exact property descriptors, required set, scalar/nested types and formats, enums/bounds, ordering and duplicate rules, `additionalProperties` rule at every object, producer, consumers, hash/nonce links, redaction class, and named negative fixtures; `created_utc`. Its artifact set includes this record and the nonce-contract record. | C2N review, C3 generators/parsers/tests, candidate lock |
| Nonce-contract record, `skill-mesh/phase-is-nonce-contract/v1` | `schema`; generator `BCryptGenRandom`; system-preferred-RNG flag; integer bit count fixed at 256; lowercase-hex encoding and `^[0-9a-f]{64}$` pattern; exact three generation points and receipt consumers; Boolean-false reuse; public correlation treatment; OS-failure terminal rule; missing/duplicate/cross-chain/wrong-length/wrong-case/non-hex negative fixtures; `created_utc` | Pre-build, launch, readiness producers and all chain validators |
| Route-decision record, `skill-mesh/phase-is-route-decision/v1` | Exactly `schema`, integer `issue` fixed at 153, positive integer `comment_id`, HTTPS `comment_url`, `comment_created_utc:string(o)`, `comment_body_sha256:string(64-lowercase-hex)`, `selected_route` enum `core-uat-mode`/`operator-subsection-override`, Boolean `plan_amendment_required` equal to whether the second enum was selected, and `verified_utc:string(o)`; `additionalProperties=false`. Its `.selector` companion is exactly UTF-8 `core-uat-mode` plus LF or `operator-subsection-override` plus LF, with no byte-order mark; its Git blob ID must match the JSON enum and the sealed C2V commit. | C2A resolver, C2N pre-implementation manifest, C3/C4 route gates |
| Route-resolution record, `skill-mesh/phase-is-route-resolution/v1` | Exactly `schema`, C2V decision/selector Git blob IDs and raw SHA-256 values, `selected_route`, `outcome` enum `core-plan-amendment-not-required`/`operator-plan-amendment-landed`, fixed `authoritative_plan_path`, 40-hex `pre_resolution_plan_blob_id`, 40-hex `resolved_plan_blob_id`, `resolved_plan_raw_sha256:string(64-lowercase-hex)`, and `created_utc:string(o)`; `additionalProperties=false`. The two plan blob IDs are equal only for the core outcome and differ only for the route-2 outcome; the raw hash always binds the resolved bytes. | C2N pre-implementation manifest, C3/C4 route gates, C5 closeout |
| Pre-build receipt, `skill-mesh/phase-is-uat-scratch/v5` | `schema`, D5 `nonce`; caller path, DOS-final path, volume-GUID-final path, file identity, and link count for the common parent, four created roots, and real profile; preparation/source/tool/process/fence/launcher/helper hashes and identities; `created_utc` | Build, install, inspect, launch, readiness, grading, cleanup |
| Launch attestation | Independent `schema`/`nonce`; pre-build receipt hash/nonce; trust result; installed-profile digest/count; writer and contract-heading facts; five fixed prelaunch sidecar hashes; fence hash; `created_utc` | Denied probe and each later host boundary |
| Readiness receipt | Independent `schema`/`nonce`; pre-build and launch receipt hashes/nonces; effective-hook manifest hash; denied-probe result hash; `created_utc` | Authenticated behavior, delivery, grading, publication, cleanup |
| Native invocation result | `schema`, exact seven-mode `mode`; applicable receipt hashes; executable/image, ordered argv, closed-environment and descendant-image manifests; physical root; start/exit/process-tree/quiescence facts; protected pre/post digests; one redacted mode proof | Later bundle boundary and evidence attestation |
| Evidence attestation, `skill-mesh/phase-is-step109-evidence-attestation/v1` | Fixed receipt/sidecar and pre-grade result hashes; per-row session/result/core-read/content/action digests and verdicts; Codex payload proof; Claude import proof; no absolute path, content, environment value, or secret | First upload and cleanup attestation |
| Cleanup attestation, `skill-mesh/phase-is-step109-cleanup-attestation/v1` | Evidence-attestation hash; first-publication-result hash; one `deleted`, `intact-quarantined`, or `partial-quarantined` disposition for each of the three disposable roots | Second upload and final Step-109 verdict |

The prelaunch and source-control sidecars have these minimum shapes:

| Sidecar | Minimum fields and invariant |
|---|---|
| `skill-mesh/phase-is-source-tool-process-manifest/v1` | `schema`; source root/gitdir/common-dir caller/final paths and identities; 40-hex commit/tree; attached read-only ref name/control digest; Boolean-true clean state; pinned Git/PowerShell paths, identities, versions, and hashes; Git/tool-input/build-environment digests; `created_utc`. It rejects linked/gitfile worktrees, alternate authority/config/object sources, ignored or untracked distribution inputs, ref/index/object drift, PATH resolution, and ambient `GIT_*` authority. |
| `skill-mesh/phase-is-trust-manifest/v1` | `schema`; project/config final paths and identities; trust-record relative path, identity, and hash; trust-bootstrap result path/hash; Boolean-true `trusted`; `created_utc`. Its result binds one permitted trust-record create, exact image/argv/environment/process tree, protected pre/post digests, zero project/outside mutation, and proof that no instruction, hook, skill, or MCP server loaded. |
| `skill-mesh/phase-is-inspector-proof/v1` | `schema`; exact state; integer profile/entry/file/owned/unowned counts; exact ledger-provider set; fresh/installed manifest hashes; zero difference count; build/install/inspect result paths and hashes; `created_utc`. Values are parsed and independently recounted from held trees. |
| `skill-mesh/phase-is-host-environment-manifest/v2` | Exactly `schema`, seven-key `modes` map, Boolean-true ambient-Git-authority absence, and `created_utc`. Each mode binds a unique sorted non-secret environment, one secret-name/presence rule, image/descendant manifest hashes, transport-policy digest, and exact argv or upload argv-schema hash. |
| `skill-mesh/phase-is-effective-hook-manifest/v2` | `schema`; trust-manifest hash; Boolean-false global/managed-only hook switches; six-host-mode map; `created_utc`. Each host mode binds a distinct settings artifact plus sorted event/matcher/type/source/direct-exec command/args/stdin-schema/hash/precedence facts. Hook events correlate one `tool_use_id` through its terminal post result. |
| `skill-mesh/phase-is-managed-policy-snapshot/v1` | `schema`; effective-input digest/count; managed settings/instruction/hook/MCP/plugin/output-style digests/counts; zero prohibited surfaces; Boolean-true refresh-path absence and startup binding before hooks; Codex transport-cache exclusions; `created_utc`. |
| Pre-implementation input manifest, `skill-mesh/phase-is-preimplementation-inputs/v1` | Object with `schema:string` (locked value), `selected_route:string` enum `core-uat-mode`/`operator-subsection-override`, `source:{commit:string(40-hex),tree:string(40-hex),ref:string}`, `existing_inputs:array<{relative_path:string,sha256:string(64-hex),role:string-enum}>`, `toolchain:{compiler,windows_sdk,windows_driver_kit,signing_policy,loader_policy}` objects, `hosts:array<{name:string-enum,version:string,discovery_anchor:string-enum,discovery_relative_path:string,sha256:string(64-hex)}>` and `created_utc:string(o)`. Tool and host locators use only an approved root-anchor enum plus a normalized path relative to that runtime root; they never carry the root's resolved absolute value. It contains existing dependencies only; C2N freezes discovery locators, versions, hashes, signatures, and selection facts before implementation. C3's admitted helper adds handle-derived physical identity in the post-implementation lock. |
| Post-implementation candidate lock, `skill-mesh/phase-is-candidate-lock/v1` | Object with `schema:string` (locked value), `preimplementation_manifest_sha256:string(64-hex)`, `candidate_commit:string(40-hex)`, `candidate_tree:string(40-hex)`, `source_files`, `schemas`, `binaries`, `bundle_files`, and `test_files`, each an ordinal-sorted array of `{relative_path:string,file_identity:string,sha256:string(64-hex),role:string-enum}`, plus `created_utc:string(o)`. C3 creates it only after those outputs exist and repeats it after any change. |

The approved discovery-anchor enum is exactly `program-files`, `program-files-x86`, `windows`,
`local-app-data`, `roaming-app-data`, or `user-profile`. A discovery-relative path is non-empty,
slash-normalized, contains no drive, root, empty, `.`, or `..` segment, and is lexically beneath its
runtime-resolved anchor. A lexically outside candidate blocks C2N. Every file-bearing `toolchain` or
`hosts` member uses that two-part locator. C2N publishes the locator, version, file hash, signature
status, signer-certificate hash, selection rule, and candidate-set digest; it never publishes the
resolved anchor or concatenated absolute path. C2N discovery does not claim physical or reparse-safe
identity. C3 reopens and final-path-resolves the same locator through the admitted native helper,
requires the target to remain beneath the final identity of the named anchor, verifies the discovery
facts, and only then binds the opened file's physical identity. A junction, symlink, reparse target,
or anchor change that escapes that final boundary blocks C3.

The `mode` enum and its closed secret/transport/hook policy are:

| Mode | Runtime secret | Outside-scratch policy | Permitted hook surface |
|---|---|---|---|
| `trust-bootstrap` | none / absent | empty | none |
| `claude-deny-probe` | `CLAUDE_CODE_OAUTH_TOKEN` / required | empty | denying `PreToolUse` guard only |
| `claude-auth-status` | `CLAUDE_CODE_OAUTH_TOKEN` / required | empty | none |
| `behavior-row` | `CLAUDE_CODE_OAUTH_TOKEN` / required | empty | correlated `PreToolUse`, `PostToolUse`, and `PostToolUseFailure` broker clients |
| `delivery-read-only` | `CLAUDE_CODE_OAUTH_TOKEN` / required | empty | broker triplet plus one delivery-only `InstructionsLoaded` logger |
| `codex-delivery-read-only` | none / absent | tested isolated state with empty policy, or D8 below | no Claude hook |
| `evidence-upload` | process-only `GH_TOKEN` / required | empty | no host hook; exactly `evidence` then `cleanup` uploads |

The two publication results bind the environment-sidecar hash, body-file handle identity, exact
uploader image/argv, endpoint and issue 153, expected body digest, returned record identifier/digest,
successful response, remote reread equality, and descendant-tree quiescence. The cleanup publication
also chains the first publication result and cleanup-attestation hash. No earlier artifact predicts a
future artifact hash.

**Schema-design gate before C3.** C2N owns the remaining agent-defaulted schema choices; none require
operator judgment. Its reviewed design record enumerates the schema-design record and nonce-contract
record themselves, then each receipt, sidecar, nested map, native result, hook input/result event,
mutation/read capability and terminal receipt, publication request/result, attestation, cleanup
result, route-decision and route-resolution records, pre-implementation manifest, and candidate lock.
For each it locks the
schema/version string,
exact property names, required set, scalar types and formats, nested object/array types, enum values,
integer bounds, ordering/duplicate rule, `additionalProperties=false` at each object, producer,
consumers, chaining hashes/nonces, redaction class, and at least one missing, extra, wrong-type,
wrong-case, duplicate-key, enum, bound, and chain-mismatch negative fixture. The schema-design and
nonce-contract records have the same closed-shape, producer/consumer, and applicable negative-fixture
coverage as the artifacts they govern. C3 cannot begin until a reviewer finds zero omitted artifact
class or undecided property/type.

**Record locations and sealing.** C2N creates and commits exactly these three machine records:

- `tools/phase-is-uat/contracts/schema-design-v1.json`;
- `tools/phase-is-uat/contracts/nonce-contract-v1.json`; and
- `tools/phase-is-uat/contracts/preimplementation-inputs-v1.json`.

They bind the pre-C2N source commit/tree as an input and do not name the later sealing commit, so
their contents are not self-referential. After the C2N commit exists, record that commit/tree, each
Git blob ID, and each raw SHA-256 on #162 and remotely reread the comment. C3 consumes the named Git
blobs, not mutable worktree copies; a blob mismatch blocks.

After C3's output commit exists, the parent creates
`skill-mesh/phase-is/candidate-locks/<UUIDv4>.json` below the platform temp root using `CreateNew` and
an exclusive retained handle. That outside-worktree file carries
`skill-mesh/phase-is-candidate-lock/v1`, the C3 commit/tree, and output blob/file identities and
hashes; it does not carry its own hash or path. The parent hashes the closed exact bytes, publishes
the exact absolute-user-path-free JSON plus SHA-256 on #162, remotely rereads and digest-verifies the
comment, and retains the local handle through review and the root gate. A candidate change creates a
new UUID/file/comment and leaves the earlier record historical; no lock is rewritten.

Closed schemas reject missing, extra, duplicate, and case-mismatched properties. Timestamps use the
round-trip `o` format. Set-valued arrays are duplicate-free and ordinal-sorted; ordered arrays such
as argv and event/read sequences retain exact order. Before object materialization, a strict UTF-8
decoder and streaming tokenizer reject a byte-order mark, invalid Unicode, non-JSON numbers, and
same-case or case-variant duplicate keys at each nesting depth; Windows PowerShell 5.1
`ConvertFrom-Json` is not authoritative. Secret values do not enter any record. Absolute user paths
may appear only in the private runtime receipts whose schemas require caller/final paths; public
attestations replace them with receipt hashes and project-relative or approved-anchor-relative
locators. Absolute user paths do not enter committed files, logs, issue comments, or other public
records.

### Step-108P implementation subplan

C2P creates `documentation/phase-is-step-108p-build-plan.md` only after C2N has frozen the selected
route, schemas, nonces, toolchain, host inputs, and admission prerequisites. That subordinate plan is
the only document passed to `/build-phase` for Step 108P. Each `### Step N:` block carries
`Problem`, `Type`, `Issue`, `Files`, `Flags`, `Produces`, `Done when`, `Depends on`, and `Status`;
every implementation step uses issue #162 and stakes-aware independent review. Each slice must fit
one producer context with headroom, expose one observable behavior through a real packet entry point,
and map its inputs and outputs to the next slice. A final integration/certification block owns the
candidate lock, full negative corpus, immutable review, and detached root gate. The subplan may add no
Phase IS unit, operator behavior observation, or route choice.

### Attended D10 grading matrix

`ABSENT` means no file. `POINTER` means an inert whole-file pointer with no `##` heading.
`SUBSTANTIVE` means a present non-pointer file. The emitted pointer is exactly the 11 UTF-8 bytes
`@AGENTS.md` plus one LF and no byte-order mark. Row fixtures use strict UTF-8, LF-only bytes. The
substantive `AGENTS.md` fixture is
`# Scratch\n\n## Stack summary\n\nMarkdown. UAT preservation canary: keep this line.\n`; row 5's
conflicting `CLAUDE.md` fixture is
`# Scratch\n\n## Stack summary\n\nConflicting non-Markdown stack.\n`.

| Row | Starting `AGENTS.md` / `CLAUDE.md` | Named-skill surface | Expected result |
|---|---|---|---|
| 1 | ABSENT / ABSENT | `plan-init` — `## After plan.md exists` | Author `AGENTS.md` with Project overview, Stack summary, Key commands, Directory layout, Architecture summary, Current state, and Environment requirements; create exact pointer `CLAUDE.md` |
| 2 | ABSENT / SUBSTANTIVE | `plan-init` — same subsection | Touch neither file; report the project non-inverted |
| 3 | SUBSTANTIVE / POINTER | `repo-update` Step 7 | Refresh `AGENTS.md`; leave pointer bytes unchanged |
| 4 | SUBSTANTIVE / ABSENT | `repo-update` Step 7 | Refresh `AGENTS.md`; create exact pointer `CLAUDE.md` |
| 5 | SUBSTANTIVE / SUBSTANTIVE | `repo-update` Step 7 | Refresh neither; print the non-blocking advisory naming both paths; continue through the bounded target |

Each row runs serially at the same physically validated scratch-project root: close the preceding
host session, reset only the two instruction files through the certified mutator, verify the exact
preimage pair, and start a fresh session. The selected route supplies a copy-ready literal that
invokes only the named subsection or safety-gated mode. After row 3, capture both postimages, repeat
the same `repo-update` action in a fresh session, and require byte-identical postimages and a no-op
result. Perform the Codex exact-payload and Claude `InstructionsLoaded` delivery proofs on this
fixed-point row-3 state before resetting for row 4.

## 6. Design Decisions

### D1 — preserve the existing owners

This document is subordinate. Conflicts resolve by §2.1, and status is re-read rather than copied
forward from a handoff or checkpoint issue.

### D2 — capability proof precedes build-step reuse

The host exposing an agent-spawn function is not proof that the full review contract is supported.
C0 must establish five properties separately: fresh producer context, independently fresh reviewer
context, parent-private HMAC key retention, a durable verdict path outside the producer worktree, and
no producer access to reviewer authority. The verdict is exactly one of `SUPPORTED`, `UNSUPPORTED`,
or `CONTRACT_DRIFT`.

### D3 — Step 108 uses a candidate lock and a non-circular gate

Freeze the reviewed Git commit/tree/blob set before launching the long gate. Read the baseline owner
first, run the exact repo-root command, read the exit sentinel before interpreting the log, compare
the observed result to the pre-run value, and only then update evidence/status. Status-only recording
after a passing gate does not rewrite the frozen UAT blob. If a product, test, generated inventory,
distribution input, or UAT executable fence changes, establish a new candidate lock and repeat the
affected review and root gate.

### D4 — the Step-109 route has no silent default

The operator records one choice on #153:

1. a core-supported, safety-gated instruction-file UAT mode, followed by rebuild, explicit
   receipt-bound install, profile/writer/inspector re-verification, and representative-report refresh;
   or
2. an explicit plan amendment permitting operator-scoped named-skill subsection overrides, with
   proof that any tooling edits are outside distribution inputs and with the applicable package and
   reference gates rerun.

Route 1 is the stronger end-to-end product check and is recommended. The recommendation is not an
operator decision. A manual core read, a non-skill probe, or an unrecorded subsection override is
neither route.

A route-2 selection authorizes only the narrow amendment described above; it does not itself edit the
authoritative plan. Mandatory code stage C2V authenticates and seals either route record. Mandatory
code stage C2A resolves that sealed input: it commits a no-amendment result for the core route, or it
owns the route-2 edit, review, commit, and seal. C2E waits for either resolved outcome, and C2N waits
for C2E's sealed guest-readiness input. C2 remains operator-only.

### D5 — nonce format is an agent-defaulted technical contract

Unless the operator amends this decision before C3 starts, the admitted native guardian generates
three independent 256-bit values with Windows `BCryptGenRandom` using the system-preferred random
number generator: one for the pre-build receipt, one for the launch attestation, and one for the
readiness receipt. Each value is encoded as exactly 64 lowercase hexadecimal characters and matched
by the closed schema pattern `^[0-9a-f]{64}$`.

The three values are generated after root admission and immediately before their respective receipt
is sealed. They are not reused within a run; the parser rejects duplicates in one chain, cross-chain
hash/nonce mismatches, missing values, non-hex values, wrong length, and uppercase encodings. Nonces
are public freshness and correlation values inside the hash-bound chain, not secrets: receipts, redacted attestations,
and #153 may carry them without redaction. Failure of the OS random API is terminal. The generator
binary and schema bytes are included in the preparation/source-tool hashes.

### D6 — operator acceptance consumes code; it does not create it

C4 invokes the immutable C3 packet and writes observations plus redacted evidence. A missing helper,
schema, parser, hook, policy, or cleanup behavior stops C4 and returns the defect to #162. The
operator does not patch around it during grading.

### D7 — stable-machine evidence is part of the gate

A repo-root run starts only with a clean stable HEAD, no competing pytest process, and at least 2 GiB
of free physical memory. The command is detached because the measured wall clock exceeds ordinary
tool-call limits. A low-memory launch is postponed, not interpreted as a repository verdict.

### D8 — Codex delivery has one closed transport exception

Only `codex-delivery-read-only` may write outside the four scratch roots. Prefer tested isolated
Codex state with an empty outside-scratch policy. If isolation is unavailable, the candidate manifest
must bind the exact guardian-held physical cache/session root identities, permitted regular
single-link relative-leaf grammar, allowed create/replace/append operations, pinned writer
image/process identity, a preventive kernel deny-by-default rule, and complete pre/post manifests
plus one aggregate delta for the whole session window.

That exception forbids semantic memory, instructions, settings, policy, skills, hooks, MCP/plugin
state, provider/auth selection, source, installed-profile, and project content. The project remains
read-only and its pre/post manifest must match exactly. If either isolated state or the closed
preventive exception cannot be enforced, Codex delivery and Step 109 remain blocked.

### D9 — native and host toolchains are pinned inputs

Step 108P uses Microsoft Visual C++ (**MSVC**) in C++17 mode plus the Windows SDK and Windows Driver Kit because
the pre-entry-point code-integrity, retained-handle, Job Object, process-creation, and kernel I/O
boundaries cannot begin inside Windows PowerShell or the managed runtime. C2E provisions and seals a
dedicated disposable guest with a run-specific test publisher, enforced publisher-based App Control
rule, kernel test-signing state, and matching toolchain family. C2N enumerates candidates only in that
guest and freezes the deterministic selection rule plus the existing C2E receipt. After sources
exist, C3 records and hashes the exact compiler binary/version/arguments, SDK/WDK versions and
consumed headers/libraries/tools, final image signatures/hashes, and complete pre-entry-point loader
closure in the candidate lock. A future binary hash is not a C2E/C2N policy input: the pre-existing
publisher rule admits correctly signed future bytes, while C3 binds the final bytes. An unavailable
or changed input blocks rather than falling back to runtime compilation or changing coordinator
security state.

Claude is pinned to version `2.1.223.0` and SHA-256
`A708BA811C4CC46907DF358E22F2AA6DA3DBC28192747E4D3C4A0869752FE722`. Codex is pinned to version
`0.147.0`; C2N records the selected native `codex.exe`, discovery shim, package/version authorities,
and complete two-file vendor-bin set as approved-anchor-relative locators plus versions, hashes, and
signatures. C3 alone upgrades those discovery facts to retained-handle physical identities. A host
upgrade requires re-audit and a candidate-manifest update before C4.

### D9E — C2N–C4 machine evidence comes only from the sealed disposable guest

`documentation/phase-is-disposable-c2n-c4-environment-plan.md` is the narrow environment owner. The
current workstation remains the capable fresh-context coordinator and sole Git/final-verdict writer;
it is not a product/driver native-build, signing, policy, boot, driver, or attended-host target. Its
only native compilation is C2E's pinned unsigned user-mode emergency-safety executable using the
already-installed toolchain and making no protected-state change. C2E binds a powered-
off snapshot lineage, connector, public signer/policy facts, test-signing state, one-writable-
descendant rule, and durable private run-volume disposition. C2N consumes that receipt. C3/C4 revalidate it before
every guest-sensitive action. App Control proves only pre-entry image admission and does not replace
the Step-108P broker, environment, descendant, handle, or kernel I/O boundaries.

### Implementation decomposition rule

The C3 packet spans schemas/parsers, native admission, process and I/O containment, host policy,
evidence publication, cleanup, and final certification. It therefore cannot be one `build-step`.
C2P derives the exact slice boundaries only after C2N freezes the contracts those slices exchange.
No C3 producer starts from this aggregate runbook directly; the reviewed C2P subplan is the dispatch
surface, and C3 is complete only after its integrated final candidate clears the aggregate gates.

### Mandatory C3 execution invariants

- **Root and identity:** the admitted native `prepare` entrypoint validates one unlinked,
  outside-git, outside-real-profile common parent, then atomically creates the four direct-child
  roots. The guardian retains no-delete-sharing handles to that parent, the four roots, and the real
  profile until final disposition; roots are single-link and aliases, UNC, SUBST, 8.3, nesting,
  reparse, hard-link, case, delete/recreate, and simulated-ID-reuse mutations fail closed.
- **Source/tool closure:** build, install, and inspect consume a clean attached ordinary worktree and
  pinned Git/PowerShell executables through held no-follow handles. The manifest covers transitive
  scripts/modules and distribution inputs. Branch/ref/index/config/object movement, PATH resolution,
  helper/config/alternate-object authority, ignored inputs, and tool/input replacement block before
  a child reads changed bytes.
- **Process rail:** the launcher starts each child suspended with an explicit inherited-handle list,
  assigns a non-breakaway kill-on-close Job Object, verifies mapped image/argv/closed environment,
  then resumes it. Descendant images are allowlisted and the full tree must become quiescent. Leaked
  outside-root file, pipe, process, or token handles and unexpected children are negative cases.
- **Read/write rail:** read-like host actions stay correlated to guardian-held no-follow handles until
  their terminal event. Each permitted mutation gets one receipt-bound kernel-verifiable capability
  naming host PID, `tool_use_id`, operation, parent/leaf, expected preimage/identity, and disposition;
  create/open, write, truncate, set-information, rename, link, and delete remain mediated through the
  terminal postcondition. Missing, duplicate, malformed, failed, or unmatched events terminate the
  job without accepting a mutation.
- **Host policy:** enumerate and freeze startup-consumed settings, managed policy/instructions,
  hooks, MCP servers, plugins, output style, ancestor instructions/rules, installed profile, and
  process-spawning configuration before each host launch. Only the two installed writers are eligible
  during behavior rows; auth/trust/delivery modes have no project-write capability. Auto memory,
  background work, updates, unlisted helpers, and ambient credential/provider authority are absent.
- **Evidence order:** preparation result precedes the pre-build receipt; launch attestation precedes
  the denied probe; readiness precedes behavior; evidence attestation precedes publication 1;
  publication 1 precedes three-root cleanup; cleanup attestation precedes publication 2. The evidence
  export and its guardian handle survive cleanup.
- **Negative corpus:** cover strict schema/UTF-8/duplicate keys, nonce shape/reuse/chaining, each
  identity/path/link/reparse mutation, source/tool/ref/environment/secret/policy/hook/process drift,
  read and mutation races, broker/kernel bypass, publication mismatch/order, and cleanup
  target/inventory/swap/I/O failure. Re-hashing a self-consistent malicious fixture must not rescue
  it because the bundle remeasures live facts.

### Mandatory C1 enumeration contract

C1 records the members, not just a count, for each row below. Commit-dependent sets are derived from
the frozen candidate with the stated predicate; the cardinalities are the current Step-108
expectations and drift is a review finding until explained against the authoritative producer.

| Set | Complete derivation predicate | Current cardinality and grading rule |
|---|---|---|
| Manifest/provider partition | Parse `config/skill-manifest.json`; enumerate each skill name/status/core and provider keys, then enumerate existing `skills/*/providers/*.md` files | 57 total = 54 portable/core-bearing + 3 provider-native/core-null; Claude/GPT/Codex adapters = 57/54/54; set equality, not count alone |
| Built profile paths | Build `-Provider all` into the candidate output; enumerate each provider's regular files as sorted relative path/SHA-256 pairs; compare to the manifest-driven expected path set | Claude/GPT/Codex = 128/125/125 files and 57/54/54 skills; Claude formula is 57 wrappers + 54 cores + 15 transitive shared files + 2 co-located helpers, GPT/Codex each 54 wrappers + 54 cores + the same 15 + 2; zero missing/extra/different paths |
| Markdown fences | Scan the UAT linearly, pairing each CommonMark backtick fence with its closer; record start/end/info string, whether its body is PowerShell-bearing, and whether it is a standalone terminating Step-108P blocker | 34 fences, 24 PowerShell-bearing, 18 blockers; each PowerShell-bearing body parses under Windows PowerShell 5.1; each blocker is one terminating `throw` with no executable successor |
| Credential regression names | Extract the one fenced name block immediately following the UAT sentence that declares 107 case-insensitively unique names; trim no internal bytes, reject blanks, compare with `StringComparer.OrdinalIgnoreCase`, and record each name | 107 names, 107 case-insensitive unique, zero blank; the closed per-mode environment remains the boundary, so this regression corpus is not described as exhaustive |
| Modes | Enumerate keys from the host-environment manifest design and compare to §5's mode table | Exactly the seven named rows; no alias or eighth mode; secret, transport, argv, image/descendant, and hook policy match each row |
| Created roots and cleanup targets | Enumerate receipt root roles and cleanup disposition roles | Four created roots: combined project/home, config, build, evidence export; exactly the first three are cleanup targets; export is retained |
| Evidence order | Enumerate hash edges among preparation result, pre-build, launch, readiness, evidence attestation, publication 1, cleanup, cleanup attestation, and publication 2 | One acyclic order matching the Mandatory C3 evidence-order invariant; no artifact names/hashes a future output |
| D10 | Parse the five table rows in §5 and count blank `Observed`/`Verdict` cells in the UAT | Five rows and ten blank operator cells before C4; starting state, writer, and expected result match §5 |
| D11 owner/probes/citers | Sweep exactly `skills/**/*.md`, `_shared/**/*.md`, and `documentation/**/*.md`. Owner is `skills/plan-init/core.md` under its named instruction-file-contract heading. Read the two probe values from that owner/test without copying them here. Inline-code occurrences are mentions; bare and fenced occurrences are uses. Discover citers through the owner-defined phrase. | Both probes are bare uses inside the owner section and have zero uses outside it. Each citer carries the phrase on one physical line and neither probe in any form. The live citer count is at least `CITER_FLOOR = 4`; enumerate paths before asserting the floor. |

The profile-path closure is independently derived as follows. For the selected provider, include one
`skill-name/SKILL.md` for each manifest skill carrying that provider and one `skill-name/core.md` for each
such skill whose `core` is non-null. Scan those selected adapter/core sources for any anchored,
repo-anchored, or bare `_shared` leaf reference; recursively scan each reached shared file for the
same references and for bare sibling filenames until a fixed point, rejecting a missing, escaping,
test-shaped, or unsupported-extension leaf. At the current candidate the resulting shared set is
exactly these 15 leaves:

```text
build_step_verdict.py
calibrate_judge.py
grader_prompt.py
intake-engine.md
judge-core.md
score_skill.workflow.js
score_skill_absolute.py
score_skill_composite.py
score-skill.md
skill-pipeline.md
skill-role-taxonomy.md
step-authoring.md
subagent-economy.md
task-state-schema.md
worktree-hygiene.md
```

Add each as `_shared/<leaf>`. Finally add the two special co-located helpers
`build-step/build_step_verdict.py` and `build-phase/build_step_verdict.py`, whose source cores are the
only selected cores whose verdict-helper citation is repointed locally. Sort ordinally and compare
this complete expected path set to a recursive regular-file enumeration of each built provider root;
the expected formulas/cardinalities are the profile row above. Any changed closure must be explained
from the recursively enumerated source references before a new count is accepted.

Fence classification is also closed for the frozen UAT. Pair CommonMark backtick fences in line
order, retaining start/end/info/body. A fence is PowerShell-bearing exactly when its case-insensitive
info string is `powershell`, or when its info string is empty and its first nonblank line starts with
`powershell `, `python `, or `$`. An info string of `text` and every other empty fence are non-
PowerShell output/data. Parse each selected body with
`System.Management.Automation.Language.Parser::ParseInput` under Windows PowerShell 5.1. A
terminating blocker is a selected fence whose parsed top-level statement list contains exactly one
`ThrowStatementAst` and no successor. This predicate yields the 24/18 cardinalities in the table;
record all 34 `(start,end,info,classification)` rows so another reviewer can recalculate them.

Use this PowerShell 5.1 extraction as the credential-corpus floor; the C1 record prints or attaches
the resulting sorted member list so reviewers can falsify the count:

```powershell
$phaseIsUatLines = Get-Content -Encoding UTF8 'documentation/findings/instruction-file-symmetry-uat.md'
$phaseIsMarker = Select-String -Path 'documentation/findings/instruction-file-symmetry-uat.md' -SimpleMatch 'following 107' | Select-Object -First 1
if ($null -eq $phaseIsMarker) { throw 'Credential-corpus marker missing.' }
$phaseIsOpen = $phaseIsMarker.LineNumber
while ($phaseIsOpen -lt $phaseIsUatLines.Count -and $phaseIsUatLines[$phaseIsOpen] -ne '```text') { $phaseIsOpen++ }
$phaseIsClose = $phaseIsOpen + 1
while ($phaseIsClose -lt $phaseIsUatLines.Count -and $phaseIsUatLines[$phaseIsClose] -ne '```') { $phaseIsClose++ }
$phaseIsCredentialNames = @($phaseIsUatLines[($phaseIsOpen + 1)..($phaseIsClose - 1)])
$phaseIsDistinct = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($phaseIsName in $phaseIsCredentialNames) {
    if ([string]::IsNullOrWhiteSpace($phaseIsName) -or -not $phaseIsDistinct.Add($phaseIsName)) {
        throw "Blank or duplicate credential name: $phaseIsName"
    }
}
if ($phaseIsCredentialNames.Count -ne 107 -or $phaseIsDistinct.Count -ne 107) {
    throw "Credential corpus drift: $($phaseIsCredentialNames.Count)/$($phaseIsDistinct.Count)"
}
$phaseIsCredentialNames | Sort-Object
```

## 7. Build Steps

### Execution quickstart

1. From the repository root, run this read-only orientation/preflight. Stop on unexplained local
   changes, branch drift, a PowerShell major version other than 5, a host-version mismatch against
   D9, a failed `gh` login, or a missing Python import.

   ```powershell
   git status --short --branch
   git log --oneline -5
   powershell -NoProfile -Command '$PSVersionTable.PSVersion.ToString()'
   python --version
   python -c "import pytest, yaml; print(pytest.__version__, yaml.__version__)"
   git --version
   gh --version
   gh auth status
   claude --version
   codex --version
   ```

   If only the `yaml` import is missing, install PyYAML into the selected Python environment with
   `python -m pip install PyYAML`, repeat the import check, and record the resulting version. A
   missing or mismatched Claude/Codex version is a blocked prerequisite, not permission to substitute
   another executable. These commands orient the coordinator only. C2E's sealed connector repeats
   the machine-local inventory in the guest, and C2N admits and hashes only that guest input set.
2. Read `AGENTS.md`, `CLAUDE.md`, `plan.md`, the accepted Phase IS plan, the UAT, and the baseline
   owner. Verify the current protected UAT as Git blob
   `c285605543f1c3ad02f8ceaf70dac5cb0af37b43` and raw SHA-256
   `38A149808F5236D03FBDA41CDE1018A240FEC8E5CC3BF8AEC34BC1C7674A71E5`. Section 2.2 records
   historical pre-C1 candidate evidence and is not the current-byte check.
3. Start C0 with these primary-source reads and searches, then inspect the active host's documented
   agent-spawn schema for the five D2 properties. The variable is read-only and is not a mutation
   target.

   ```powershell
   $phaseIsSkillRoot = Join-Path ([Environment]::GetFolderPath('UserProfile')) '.agents\skills'
   Get-Content -Raw -Encoding UTF8 (Join-Path $phaseIsSkillRoot 'build-phase\SKILL.md')
   Get-Content -Raw -Encoding UTF8 (Join-Path $phaseIsSkillRoot 'build-phase\core.md')
   Get-Content -Raw -Encoding UTF8 (Join-Path $phaseIsSkillRoot 'build-step\SKILL.md')
   Get-Content -Raw -Encoding UTF8 (Join-Path $phaseIsSkillRoot 'build-step\core.md')
   Get-Content -Raw -Encoding UTF8 (Join-Path $phaseIsSkillRoot '_shared\judge-core.md')
   rg -n 'required_tool_missing|isolated fresh-context|spawn_agent|fork_turns|verdict-path|verdict-run-id|classify_verdict' $phaseIsSkillRoot
   ```

4. Do not dispatch C1 review work until the latest C0 verdict is `SUPPORTED`. After C2, C2V must
   validate and seal the remote record, then mandatory C2A must seal the matching resolution outcome.
   After C2A, execute the separately approved C2E plan and seal its guest-readiness receipt. Do not
   run C2N discovery on this workstation. Do not launch C3 until C1, C2V, C2A, C2E, C2N, and C2P are
   DONE. Do not start a real host session until C3 is DONE, and then start it only in the sealed guest.

Apart from the documented PyYAML prerequisite, no coordination-workstation dependency installation
is part of this runbook. Guest provisioning is separately owned and authorized by C2E. This
repository has no dev server, lint command, or typecheck command; pytest is its sole
automated gate, and the distribution build/install commands above are the relevant build and install
operations. C4 requires two process-scoped secrets:
the operator supplies `CLAUDE_CODE_OAUTH_TOKEN` only to the four authenticated Claude modes, and the
publication broker supplies `GH_TOKEN` only to `evidence-upload`. The latter name carries an opaque
broker capability, never the real GitHub credential: the parent requests a distinct five-minute grant
for each ordered invocation, bound to issue 153, the exact redacted body digest, ordinal, candidate,
uploader image/argv, endpoint, and one idempotent creation plus returned-comment rereads. The cleanup
grant also binds the first remotely reread comment and cleanup attestation. The broker alone holds a
short-lived repository/issues-scoped GitHub credential, direct guest GitHub API egress is denied, and
each capability is disabled immediately after reread. Wrong issue/body/order, replay, third use,
expiry, and direct-API attempts must fail. The broker constructs each child environment from empty,
records presence but not value, and does not persist, print, or hash either secret. If the final
uploader requires a literal direct GitHub credential in the post-kernel guest, stop for an
authoritative decision; do not edit the frozen UAT or weaken the broker boundary.

### Completion Stage C0: Resolve Codex build-step capability

- **Problem:** The installed Codex `build-step` adapter says isolated fresh-context dispatch is
  unavailable, while this host exposes agent spawning with a no-history option. A tool name alone
  does not settle the security and authority contract.
- **Type:** operator / diagnosis; read-only
- **Issues:** prerequisite to #152; do not begin Steps 108P or 109 here
- **Prerequisites:** clean orientation; read the installed `build-phase`, `build-step`, and shared
  judge contracts from the active agent home's `.agents/skills/` tree
- **Actions:** search the local skill/host infrastructure for `required_tool_missing`, isolated
  fresh-context language, spawn/fork behavior, verdict paths/run IDs, HMAC handling, and verdict
  classification. Prove or disprove each of D2's five properties from primary local sources. A
  non-mutating probe is allowed only when source evidence cannot decide one property.
- **Produces:** one diagnosis report only: `SUPPORTED` with the exact safe dispatch pattern;
  `UNSUPPORTED` with the required adapter or supported environment; or `CONTRACT_DRIFT` with a
  proposed narrow canonical-source correction and proposed focused validation tests. A proposal is
  not an edit.
- **Exact gates:** path-and-line evidence for each property; no inference from the spawn function's
  name; no same-context producer/reviewer substitution
- **Stop conditions:** missing parent-private state, child-readable verdict key, verdict sidecar in
  the worktree, reused producer/reviewer context, or uncertain reviewer authority
- **Operator action:** record the verdict. After `CONTRACT_DRIFT`, separately authorize C0R/C0A or
  choose the supported environment named by the diagnosis. After `UNSUPPORTED`, choose the named
  supported environment. Neither branch runs inside C0.
- **Done when:** one verdict and its evidence are recorded. Only `SUPPORTED` unlocks C1; the other
  verdicts stop this completion run until remediation/environment selection and a repeated C0 return
  `SUPPORTED`.
- **Recorded result (2026-08-27):** `CONTRACT_DRIFT` against start commit `f74997d`. The active
  callable schema exposed explicit no-history child dispatch. Direct fresh producer and reviewer
  siblings could not read a parent canary or one another's nonce; a fresh child explicitly given a
  disposable parent execution-session handle received `Unknown process id`; and the parent-only
  JSON-lines service authenticated an outside-worktree sidecar while a planted byte replacement
  classified `BLOCKED`. Shared filesystem/tool access remained visible, as expected, but conveyed
  neither conversational inheritance nor final-verdict authority. Those probes established D2's
  fresh producer, fresh reviewer, external sidecar, opaque parent key, and parent-only classification
  properties separately. The canonical build-step adapter at `f74997d` still asserted that Codex had
  no such primitive, and the build-phase adapter repeated the stale same-context/private-state
  assumption, so the host was capable while its mapping contract had drifted.
- **Repeated result (2026-08-27):** `SUPPORTED` in a fresh `gpt-5.6-terra` context against
  synchronized HEAD `3ff717b` and the activated 125-file Codex profile. Separate no-history producer
  and reviewer siblings saw neither the parent canary nor one another's nonce; the producer was
  rejected with `Unknown process id` when explicitly given the disposable parent service handle.
  The parent-only JSON-lines service kept its per-open key opaque, classified the valid outside-repo
  sidecar `ADVANCE`, and classified planted corruption plus same-run-id replay `BLOCKED`. Both
  services closed, the sidecar was absent after cleanup, and the repository remained clean.
- **Repeated evidence (active-home-relative primary paths):** the activated profile is byte-identical
  to the reviewed distribution recorded in C0A, so these installed path-and-line citations identify
  the runtime contract Terra actually probed.
  - Fresh producer and independently fresh reviewer: `.agents/skills/build-step/SKILL.md:31-32`
    requires explicit no-history sibling dispatch with no reuse or follow-up. The fresh producer and
    reviewer reported no parent canary, service handle, or sibling nonce; each independently
    returned a distinct, non-empty UUIDv4 nonce. Raw values are omitted from the public record.
  - No producer access to reviewer or final-verdict authority:
    `.agents/skills/build-step/SKILL.md:34-35` limits children to evidence/recommendations and keeps
    the channel out of child inputs, while `.agents/skills/build-phase/SKILL.md:35` reserves
    authenticated classification to the parent. A producer explicitly given disposable parent
    session `80623` received `Unknown process id 80623` from `write_stdin`.
  - Parent-private HMAC retention: `.agents/skills/build-phase/SKILL.md:31-32` requires a separately
    probed opaque parent service; `.agents/skills/_shared/build_step_verdict.py:103-107` defines its
    caller-scoped/key-private boundary, and `:429-455` stores, rotates, and clears the process-internal
    key. The ready/request responses exposed neither key nor signature, and replay after a new
    same-run-id `open` classified `BLOCKED`.
  - Durable external sidecar: `.agents/skills/build-phase/SKILL.md:33` requires platform temp outside
    the repository and producer worktree. The parent opened a unique `%LOCALAPPDATA%/Temp/skill-mesh-c0-*`
    path; valid authenticated bytes classified `ADVANCE`, planted replacement classified `BLOCKED`,
    and the path was absent after parent cleanup.
  - Parent-only authenticated classification and shared-filesystem boundary:
    `.agents/skills/build-phase/SKILL.md:32-35` reserves service use/final classification to the
    parent, and `.agents/skills/build-step/SKILL.md:33-35` permits shared filesystem/tools without
    treating them as conversational or authority isolation. Python-looking summary text remained
    inert data; corruption/replay failed closed; both parent services closed successfully.
- **Status:** COMPLETE — latest verdict `SUPPORTED`; C1 unlocked. The initial `CONTRACT_DRIFT`, its
  repair route, and the superseding repeated verdict remain recorded above.

### Completion Stage C0R: Repair canonical adapter drift when authorized

- **Problem:** A `CONTRACT_DRIFT` verdict means the host can satisfy the isolation/authority contract
  but the canonical Codex wrapper rejects or misstates that capability.
- **Type:** code
- **Prerequisites:** C0 returned `CONTRACT_DRIFT` with evidence for all five D2 properties; the
  operator explicitly authorized this separate canonical source change; clean synchronized `main`
- **Applicability:** dispatch only after C0 returns `CONTRACT_DRIFT` and the operator explicitly
  authorizes this separate source change. Record `NOT APPLICABLE` when C0 returns `SUPPORTED` or
  `UNSUPPORTED`.
- **Files:** `skills/build-step/providers/codex.md`; `skills/build-phase/providers/codex.md` because
  its parent mapping also drifts; `tests/package-integrity/test_codex_agent_isolation_contract.py`
  (new); `_shared/build_step_verdict.py` for its parent-only JSON-lines service and corrected dispatch
  contract; `_shared/test_build_step_verdict.py` for that service's schema, injection, lifecycle, and
  no-secret-output tests;
  `documentation/providers/codex.md` and `documentation/providers/README.md` for their repeated active
  capability claims. `documentation/release-candidate-report.md` is a required no-diff regeneration
  gate, not an expected C0R edit, because its representative rows do not select the Codex adapter
- **Actions:** edit canonical repository sources, not the installed generated `SKILL.md`. Encode only
  the dispatch pattern proven by C0, preserve the parent-private key and outside-worktree sidecar,
  and add a planted-negative test for each corrected capability claim.
- **Exact gates:** focused adapter/verdict tests; `python -m pytest tests/package-integrity`;
  `powershell -File tools/build-distributions.ps1 -Provider codex`; regenerate the representative
  report and require no diff for this Codex-only adapter change; independent review in the C0-proven host pattern or another named
  supported environment; stable detached repo-root `python -m pytest`
- **Produces:** reviewed canonical source/test change and reproducible Codex distribution; no active
  home installation
- **Stop conditions:** capability remains inferred from a tool name; the key or usable verdict-service
  authority reaches a child; the sidecar path is passed into child context or the sidecar is placed in
  the worktree; a producer can self-review; a non-Codex contract is weakened; or a gate fails. Ambient
  discovery of an outside-worktree sidecar is permitted only because tampering fails closed.
- **Operator action:** none during the code stage; authorization is a prerequisite
- **Done when:** the canonical change is reviewed, all gates pass, and its commit is synchronized
- **Depends on:** C0=`CONTRACT_DRIFT` plus prior operator authorization
- **Status:** DONE — canonical repair commit `6d14626` passed both independent reviews, 86 focused
  tests, 302 package-integrity tests, four distribution-parity tests, reproducible 54-skill / 125-file
  Codex packaging, and the detached repo-root gate (1380 passed, 1 skipped in 2:30:30). The repair and
  its certification record are synchronized on `main` before C0A begins.

### Completion Stage C0A: Activate an authorized C0R repair

- **Problem:** A canonical fix does not change the already-installed generated adapter used by a live
  Codex session.
- **Type:** operator
- **Applicability:** run only after C0R is DONE; otherwise record `NOT APPLICABLE`
- **Prerequisites:** exact reviewed C0R commit and distribution hashes; explicit operator authority
  to update the active Codex skill profile
- **Actions:** build the reviewed Codex distribution into a disposable output, inspect it, install it
  through the repository installer into the explicitly named active agent home, inspect the installed
  ledger/tree, close the old session, and start a fresh session. Do not edit generated installed
  files directly.
- **Exact gates:** fresh build equals the reviewed distribution manifest; installer/inspector return
  success; installed adapter/core hashes equal the reviewed build; no unledgered/stale file; repeated
  C0 in the new session returns `SUPPORTED`
- **Produces:** host activation/inspection record only; no repository source artifact
- **Stop conditions:** active home is ambiguous, foreign-file collision, ledger mismatch, unexpected
  install target, installed hash drift, or repeated C0 is not `SUPPORTED`
- **Operator action:** authorize and observe the active-profile install and fresh-session restart
- **Done when:** repeated C0 is `SUPPORTED`
- **Depends on:** C0R
- **Status:** DONE — the active home resolved unambiguously through the canonical probe; its valid
  owned Codex profile was updated through the repository installer without force. All 125 installed files
  equal the disposable reviewed build (aggregate manifest SHA-256
  `a58c8ca5762e47bc8808528a58702745e2f74272b5f7b480cc5a85abac783075`), the ledger contains 125
  matching ownership hashes, and the inspector reports 55 owned entries, zero unowned entries, and
  zero Codex-root warnings. Four probe-generated `.pyc` files were moved to a recoverable temp
  quarantine before the exact-tree comparison. Fresh Terra repeated C0=`SUPPORTED`.

### Completion Stage C1: Certify Step 108

- **Problem:** Step-108 code/evidence landed, but its final review provenance and repo-root gate do
  not yet satisfy the Done-when.
- **Type:** code / certification
- **Issue:** #152
- **Prerequisites:** latest C0 verdict is `SUPPORTED`; current UAT blob re-matches §2.2 or a new candidate identity is
  deliberately frozen; clean stable HEAD; no competing pytest; at least 2 GiB free memory
- **Actions:** retain the existing two reviews as supporting evidence. If C0 cannot authenticate
  them under the accepted protocol, dispatch two independently fresh reviewers against immutable
  Git objects using the parent-private key and outside-worktree verdict paths. Execute the Mandatory
  C1 enumeration contract in §6, retaining each derived member list and comparison rather than a
  count-only assertion.
- **Gate launch:** immediately before launch, read `documentation/phase-75-baseline.md`. From the
  repository root, start a hidden detached Windows PowerShell 5.1 process that invokes exactly
  `python -m pytest` with no path argument. Write stdout, stderr, start facts, and the exit-code
  sentinel outside the repository. Do not mutate the candidate worktree or HEAD during the run.
- **Gate interpretation:** wait for the sentinel; read it before the log. Require exit `0`, observed
  passed count at or above the pre-run owner value, and the same skip count. Compare first, then
  update the single baseline owner only if the measurement changed.
- **Additional gates:** `python tools/gen_manifest.py` when the documentation inventory changed;
  `python -m pytest tests/package-integrity`; PowerShell 5.1 parsing of each PowerShell-bearing UAT
  fence; `git diff --check`
- **Produces:** authenticated review verdicts or a documented promotion decision; external gate
  log/sentinel; status/evidence update; issue #152 closure
- **Stop conditions:** unstable HEAD, dirty candidate, memory below the launch floor, absent/nonzero
  sentinel, lower pass count, changed skip count, High/Medium review finding, stale UAT identity, or
  any runnable Step-109 action
- **Operator action:** none within C1. If the selected environment cannot satisfy C0 or the memory
  floor, leave C1 blocked and resolve that prerequisite outside this code/certification stage.
- **Done when:** Step 108's accepted Done-when is met and #152 is closed as certified DONE
- **Depends on:** C0=`SUPPORTED` directly, or C0R/C0A followed by repeated C0=`SUPPORTED`
- **Status:** COMPLETE — certified at `472a62829fe355557584dbf11916e9b3a6958e45`: two fresh
  no-history reviews reported zero High/Medium findings; the frozen UAT is Git blob
  `c285605543f1c3ad02f8ceaf70dac5cb0af37b43` (raw SHA-256
  `38A149808F5236D03FBDA41CDE1018A240FEC8E5CC3BF8AEC34BC1C7674A71E5`); and the sentinel-first
  detached root gate returned `0` with `1380 passed, 1 skipped in 8886.70s (2:28:06)`.

### Completion Stage C2: Record the operator route

- **Problem:** Step 108P cannot implement an unspecified named-skill invocation route.
- **Type:** operator
- **Issue:** #153
- **Prerequisites:** C1 complete
- **Actions:** present D4's two routes with their scope and evidence tradeoff. Record the operator's
  exact selection on #153. If route 2 is selected, the record also states that it authorizes only
  D4's operator-scoped named-skill subsection amendment, with no distribution-input tooling edit.
  The decision comment body is exactly two LF-separated, CR-free lines with no third or blank line:
  first `PHASE_IS_ROUTE_RECORD_V1`, then either `PHASE_IS_ROUTE=core-uat-mode` or
  `PHASE_IS_ROUTE=operator-subsection-override`. The latest #153 comment whose first line is the exact
  header is authoritative. C2 remotely rereads the just-created comment by returned comment ID and
  requires byte-for-byte body equality; an absent, duplicate, conflicting, or malformed marker blocks
  rather than selecting a default. That latest-comment rule ends when C2V seals the chosen comment:
  the sealed ID remains authoritative through C4. A later exact-header comment is route drift and
  blocks until the operator deliberately starts a new C2/C2V cycle; it never silently supersedes C2V.
- **Produces:** one public route-decision comment plus its returned GitHub comment ID, URL, and
  remotely reread body SHA-256; no code or code-dependent operations artifact
- **Exact gates:** issue comment names route 1 or route 2, contains its matching exact marker, and is
  remotely reread; no third route
- **Stop conditions:** ambiguous response, unrecorded choice, proposed manual/non-skill substitute,
  or an attempt to begin implementation before the comment exists
- **Operator action:** choose route 1 or route 2 on #153
- **Done when:** the exact remote route record exists and unlocks mandatory C2V only
- **Depends on:** C1
- **Status:** COMPLETE — #153 comment `5457823134` selected `core-uat-mode`; C2V and C2A later
  validated and resolved that immutable input.

### Completion Stage C2V: Validate and seal the remote route decision

- **Problem:** downstream route resolution needs an authenticated, immutable input; a mutable issue
  read or worktree file cannot be that authority.
- **Type:** code
- **Issue:** #153
- **Prerequisites:** C2 complete and its returned GitHub comment ID available
- **Files:** `documentation/findings/phase-is-route-decision.json` and
  `documentation/findings/phase-is-route-decision.selector` (new)
- **Actions:** retrieve #153 comments through the authenticated GitHub Representational State
  Transfer (REST) API with IDs, URLs,
  timestamps, and exact bodies, requesting 100 per page and following each `Link: rel="next"` URL to
  exhaustion; absence of `rel="next"` terminates the enumeration. Reject a malformed Link header, a
  repeated page URL, duplicate comment ID, or response failure. Build one duplicate-free map keyed by
  positive numeric comment ID. Select exact-header candidates by maximum
  tuple `(created_at parsed as UTC instant, numeric comment ID)`; IDs make the order total, and equal
  IDs with unequal bytes block. Require the selected ID to equal C2's returned ID and its body to be
  exactly the two-line grammar in C2. Reject CR bytes, a missing/extra/duplicate marker, either valid
  marker more than once, an unknown `PHASE_IS_ROUTE`-prefixed line, body/hash mismatch, or remote
  reread drift. Repeat the complete paginated enumeration immediately before and after posting the
  C2V seal and at each later route-drift gate; a newly maximal exact-header tuple blocks.
  Write the strict route-decision record in §5 as canonical UTF-8 JSON with sorted keys, compact
  separators, one terminal LF, and no byte-order mark. Write its `.selector` companion with §5's exact
  enum bytes. Verify both staged Git blobs directly, not the mutable worktree copies.
- **Produces:** committed route-decision JSON and selector blobs plus a #153 seal containing the
  source comment ID/body SHA-256, C2V commit/tree, both Git blob IDs, both raw SHA-256 values, and a
  successful remote reread
- **Exact gates:** strict JSON/token validation rejects missing, extra, duplicate, case-mismatched,
  wrong-type, enum, Boolean/enum inconsistency, comment-ID, and body-hash cases; the selector is one
  exact allowed blob and agrees with the JSON; source comment reread matches before and after
  serialization; `python tools/gen_manifest.py` runs in the same change;
  `python -m pytest tests/package-integrity` and `git diff --check` pass; independent review finds no
  High or Medium issue
- **Stop conditions:** GitHub read/auth failure, no exact-header record, the newest header record is
  malformed, C2's returned ID differs, multiple/unknown marker lines, remote mutation, schema failure,
  failed gate, review finding, or a later exact-header comment appears before the seal is complete
- **Operator action:** none; a bad C2 record returns control to C2 for a new operator decision record
- **Done when:** the committed blobs and remotely reread seal bind exactly one valid route. Before
  C2A dispatch, the orchestrator must compare `HEAD`'s two route-artifact blob IDs to the C2V seal and
  prove no later commit changed either path; any mismatch blocks before C2A. The resolver consumes the
  sealed Git blobs and repeats the complete remote drift check.
- **Depends on:** C2
- **Status:** DONE — commit `09e7f4d0b740ddfb723dd77682108c3b4405d13e`; decision blob
  `a18ea40d9ed04e5649c8a681bf72e1c43920fdc9`; selector blob
  `fa04bb8e39f7d33a8cdb24ccc2d357f211342f7f`; remotely reread #153 seal `5460494882`.

### Completion Stage C2A: Resolve the selected route

- **Problem:** both route outcomes need one reviewed, committed branch result; a shell predicate or
  mutable selector must not decide whether the route-2 amendment is silently omitted.
- **Type:** code
- **Issue:** #153
- **Prerequisites:** C1 and C2V complete; `HEAD` carries C2V's sealed JSON and selector blobs unchanged
- **Files:** `documentation/findings/phase-is-route-resolution.json` (new) in both branches;
  `documentation/instruction-file-symmetry-plan.md` only for `operator-subsection-override`; no UAT
  executable fence, distribution input, or provider/core skill file
- **Actions:** before opening any output, revalidate C2V's sealed commit/tree, both artifact blob IDs,
  exact selector/JSON agreement, frozen comment ID/body, and complete paginated no-later-record result.
  Reject any value other than the two closed route enums. For `core-uat-mode`, require
  `plan_amendment_required=false`, leave the authoritative phase-plan blob byte-identical to C2V, and
  write the exact `core-plan-amendment-not-required` resolution record. For
  `operator-subsection-override`, require `plan_amendment_required=true`; amend the Step-109 route
  contract to permit only operator-scoped named-skill subsections inside the already isolated genuine
  sessions; bind the named skill and subsection grammar, require the full skill invocation to remain
  core-supported, forbid manual/non-skill substitutes, require any route helper/tooling edit to live
  outside every distribution input, and write the exact `operator-plan-amendment-landed` resolution
  record with the pre/post plan blob IDs and raw post-plan SHA-256.
  Preserve Step 109's operator-only grading and Step 108P's exclusive ownership of containment in
  either branch. Materialize the canonical resolution JSON before commit; it binds content blob IDs,
  not its own future commit, so it is not self-referential.
- **Produces:** one independently reviewed route-resolution blob in both branches; for route 2, the
  amended plan blob as well; and a #153 seal containing the selected outcome, commit/tree, resolution
  blob/raw hash, pre/resolved plan blobs/raw hash, and successful remote reread
- **Exact gates:** strict resolution-schema and branch-consistency validation; `python
  tools/gen_manifest.py` in the same change; `python -m pytest tests/package-integrity`; `git diff
  --check`; independent review with zero High/Medium. The core branch additionally proves the phase
  plan blob is unchanged. Route 2 additionally requires plan-review and plan-wrap with no new blocker,
  passes `tests/package-integrity/test_link_resolution.py` and
  `tests/package-integrity/test_manifest_contract.py`, and proves no distribution-input change.
- **Stop conditions:** C2V or remote drift, invalid/mismatched route artifacts, core-route plan drift,
  an amendment broader than D4, UAT change before C3, distribution-input edit, containment code,
  failed gate/review, or remote seal mismatch
- **Operator action:** none beyond C2's exact route authorization; any different/broader route request
  is a new operator decision and restarts C2/C2V
- **Done when:** one branch-consistent resolution blob is landed, gated, independently reviewed,
  remotely sealed on #153, and available for C2N's `existing_inputs` array
- **Depends on:** C2V
- **Status:** DONE — `core-uat-mode` resolved without an authoritative phase-plan amendment at
  commit `2f6c7b87dbe68182d2c43c8b1e2faa0a9229817d`; resolution blob
  `14482e5ac6ac550d1e65e511fcfe9b31a18385f6`; remotely reread #153 seal `5464987667`.

### Completion Stage C2E: Prepare and seal the disposable driver-test environment

- **Problem:** C2N requires an existing WDK, signing identity, enforced pre-entry admission policy,
  loader/boot state, and exact host inputs. A read-only prerequisite probe found that this workstation
  cannot supply those facts, and making it do so would mutate its real security posture.
- **Type:** reviewed code preparation plus parent-completed provider/provisioning/readiness waits
- **Issue:** #162; post-C4 disposal is recorded under #143
- **Prerequisites:** C2A complete; accepted phase-plan and frozen UAT blobs reverified unchanged; a
  separate operator execution authorization; a selected provider can supply the provider-neutral
  execution-guest/signer-appliance/connector/lifecycle contract; an external publication broker can
  retain the real GitHub credential and enforce the exact-body capability contract above
- **Files:** `documentation/phase-is-disposable-c2n-c4-environment-plan.md`, its proposal HTML,
  `tools/phase-is-environment/**`, `tests/phase-is-environment/**`, and
  `documentation/findings/phase-is-c2e-environment.json`; no accepted phase-plan or UAT edit
- **Actions:** execute C2E plan Steps 1–32 only in their declared split. Build Steps 1–3; stop at
  parent wait Step 4 for explicit provider/license/cost/private-evidence/retention authorization;
  if execution stops after a Step-4 PASS while both the environment ID and every provider resource are absent,
  complete the authenticated pre-resource closure, destroy all committed authorities/journals/store
  state, and prove every never-committed planned allocation absent; build Steps 5–28; stop at Step 29 to materialize, independently reread, and live-
  preflight the exact sealed emergency executable/broker before an environment ID; atomically create
  the environment ID, locator-free bootstrap, and zero-head append-only resource journal; run the
  second environment-bound preflight; only then perform the first provider mutation, arm immutable
  lifecycle rules, and provision one Windows
  execution lineage plus a separate, non-snapshotted, network-isolated Windows signer appliance;
  stop at Step 30 for live connector/rollback/signer-isolation/fresh-context smoke; invoke build-phase
  for Step 31 alone to create its local reviewed readiness candidate; then have the parent perform Step 32's expected-
  old push, signed readiness wait, exact #162 seal reread, and status-only commit. S1/R0 contain only
  the public publisher chain. The signer appliance holds the non-exportable private leaf, never runs
  candidate code, signs only independently reviewed exact objects under one parent grant, and is
  destroyed at the C3 candidate lock before C4. Do not begin C2N in the same context.
- **Exact gates:** C2E plan-review/redline/wrap; strict schema, asymmetric authenticated wait-result,
  exact remote-marker/status ordering, coordinator-before/after, and redaction tests; planted negatives
  for every environment stop class; the closed 16-operation adapter; separate provider-control,
  guest-HMAC, retention-verification, wait, and asymmetric admin-grant authorities; durable external
  crash-replay reconciliation; atomic lease acquire/renew/release; complete environment inventory;
  explicit create/attach/lifecycle controls; isolated signer-appliance, no-route, exact-object grant,
  and post-kernel external-audit tests; PowerShell 5.1 parse/safety checks; immutable active lifecycle,
  bounded control/wait/emergency-broker expiry, automatic retention/absence verification, and a self-contained,
  image-bound emergency-disposition closure; deliberate live failure-before-write plus rollback/old-
  session replay in a fresh R0 descendant; exact-current-candidate emergency bundle plus live
  `pre-resource-run` and `pre-resource-environment` empty-inventory broker/provider/reread preflights
  before the first mutation; external publication-broker capability/receipt tests plus broker-only
  egress and direct-GitHub-API denial; parent-only authenticated reviewer classification;
  manifest no-diff, package-integrity, `git diff --check`, qualifying detached sentinel-first
  repository-root `python -m pytest`, independent review with zero High/Medium; exact unchanged
  accepted-plan and UAT blob IDs; remote #162 seal reread
- **Produces:** one immutable `skill-mesh/phase-is-c2e-environment/v1` Git blob plus a #162 seal that
  binds its commit/tree/blob/raw hash and external evidence-manifest digest; no containment code,
  future image hash, host observation, or workstation security mutation
- **Stop conditions:** any workstation security/boot/tool mutation; unavailable or unauthorized
  provider/Windows media/license/private evidence store/publication broker/retention owner; a real or
  reusable GitHub credential entering the guest, direct guest GitHub API access, or a publication
  capability not bound to one exact body/issue/ordinal/expiry; shared filesystem or private-
  network or signer-route escape; arbitrary or unauthenticated shell; missing auth/replay/journal/
  lease/inventory/resource/lifecycle proof; missing immutable bootstrap or transactional resource
  journal/reconciliation; an execution snapshot containing private signing material;
  signer appliance receiving unreviewed bytes or candidate execution; missing exact toolchain/
  publisher/policy/boot/canary/snapshot evidence; process/provider/host credential persistence;
  premature parent provider-identity revocation; missing automatic active-lineage/deletion/later-
  absence owner; an extendable lifecycle/key deadline; inability to run emergency safety disposition
  without Git/build/test/GitHub; more than one writable descendant; producer access to signer,
  reviewer/admin/verdict/Git authority; accepted-plan/UAT drift; failed gate/review/seal reread. Any
  terminal branch after an environment ID or provider resource exists enters C2E.33 before departure.
- **Operator action:** this planning approval is not execution authority. Separate execution
  authorization is required before C2E Step 1. C2E.4 separately selects/authorizes one provider,
  license/cost, private evidence store, external publication-broker route, retention route, and immutable control, wait, emergency-
  broker, and retention-key lifecycles. C2E.29 separately authorizes provisioning. Guest certificate,
  policy, Secure Boot, BCD,
  reboot, and driver-state changes are guest-only. This stage grants no permission to install a local
  hypervisor/Windows feature or change this workstation.
- **Done when:** C2E Step 32's reviewed receipt, remote seal, and returned-marker status are immutable
  C2N inputs; the execution guest is powered off in sealed R0 state with no signing private key or
  process/provider/host authentication credential in any snapshot; the isolated signer appliance is
  powered off and holds the only non-exportable test-publisher private leaf; and C2N starts only in a
  fresh context
- **Depends on:** C2A
- **Status:** PLANNED / NOT AUTHORIZED FOR EXECUTION

**Terminal-disposition rule:** once C2E.29 generates an environment ID or creates any provider
resource, every terminal C2E, C2N, C2P, C3, or C4 stop invokes C2E.33 before the environment is left.
C2E.33 revokes guest process/host and connector secrets first; retains narrow active parent provider
authority through power-off, complete inventory, disposition, lease release, and provider-response/
independent-reread verification; then revokes that identity last. On C4 PASS it first attempts the
proof-bound atomic retention transition. A verified success preserves only the detached run volume,
read-only retention identity, credential-free C5-shortener preauthorization, and the control-receipt/
wait-result/emergency-broker private authorities needed for C5 proof and final teardown. If that transition
cannot start or cannot be verified, the sealed emergency broker immediately destroys the complete
lineage—including the run volume—under the distinct `C4_PASS_TRANSITION_FAILED` reason, preserves the
PASS plus transition failure, records C2E.33 blocked, and never enables C5. Otherwise C2E.33 either destroys the lineage
or records a bounded non-runnable quarantine with an automatic deletion rule, owner, deadline, and
later absence-verification action. Failure cleanup is not deferred to C5. On an abort, the direct
parent-only self-contained image-bound action runs from the sealed private emergency bundle before
any Git, test, build-phase, GitHub, control-signer, or wait-signer preflight; raw provider response and
independent reread establish safety, while signed status and #143 bookkeeping follow afterward.

### Completion Stage C2N: Freeze schema, nonce, dependency, and toolchain inputs

- **Problem:** Schema choices, three receipt nonces, and selected-route dependencies need
  machine-exact contracts before implementation can safely fan out.
- **Type:** code / design checkpoint
- **Issue:** #162
- **Prerequisites:** C2A complete with one remotely sealed, branch-consistent route-resolution blob;
  C2E complete with a remotely sealed environment receipt and powered-off R0 lineage
- **Actions:** produce the schema-design record required by §5. Record D5 in #162's implementation
  notes, including schema pattern, generator API, generation points, uniqueness/reuse rule, consumers,
  publication treatment, and negative cases. Revalidate and include C2V's route-decision/selector
  blobs and C2A's route-resolution blob in the typed pre-implementation manifest with the
  selected-route source/tool/host inputs, then record the
  guest-local native compiler, SDK, WDK, signing, App Control, boot, snapshot, connector, and
  loader-policy prerequisites that C3 will consume. Include the C2E receipt blob/raw hash and
  environment ID as an existing input. Do not include future schemas, bundle,
  launcher/helper sources, binaries, or tests in this pre-implementation lock.
- **Candidate discovery:** invoke the sealed C2E read-only connector against the sole writable R0
  descendant and run the commands below there; never run this inventory against the coordination
  workstation. Do not select by PATH
  order alone. C2N records the complete candidates and deterministic rule: highest semantic toolset
  or kit version, then the ordinal `anchor + NUL + relative-path` selection key; equal-version
  candidates with different bytes/signer-certificate hashes are ambiguous and block. This lexical
  discovery is not D9 admission. C3 final-path-resolves and closes the actually consumed compiler,
  SDK/WDK, signing, loader, and host closure after sources/binaries exist.

  ```powershell
  $ErrorActionPreference = 'Stop'
  $phaseIsAnchorRoots = @(
      [pscustomobject]@{ Name='local-app-data'; PrivateRoot=[Environment]::GetFolderPath('LocalApplicationData') }
      [pscustomobject]@{ Name='roaming-app-data'; PrivateRoot=[Environment]::GetFolderPath('ApplicationData') }
      [pscustomobject]@{ Name='program-files-x86'; PrivateRoot=${env:ProgramFiles(x86)} }
      [pscustomobject]@{ Name='program-files'; PrivateRoot=$env:ProgramFiles }
      [pscustomobject]@{ Name='windows'; PrivateRoot=$env:windir }
      [pscustomobject]@{ Name='user-profile'; PrivateRoot=[Environment]::GetFolderPath('UserProfile') }
  ) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.PrivateRoot) }

  function ConvertTo-PhaseIsPublicLocator {
      param([Parameter(Mandatory=$true)][string]$PrivatePath)
      $phaseIsFullPath = [IO.Path]::GetFullPath($PrivatePath)
      foreach ($phaseIsAnchor in $phaseIsAnchorRoots) {
          $phaseIsRoot = [IO.Path]::GetFullPath([string]$phaseIsAnchor.PrivateRoot).TrimEnd('\')
          $phaseIsPrefix = $phaseIsRoot + '\'
          if ($phaseIsFullPath.StartsWith($phaseIsPrefix, [StringComparison]::OrdinalIgnoreCase)) {
              $phaseIsRelativePath = $phaseIsFullPath.Substring($phaseIsPrefix.Length).Replace('\','/')
              if ([string]::IsNullOrWhiteSpace($phaseIsRelativePath) -or $phaseIsRelativePath.Contains(':') -or $phaseIsRelativePath -match '(^|/)\.\.?(/|$)') { throw 'Candidate locator is not publishable.' }
              return [pscustomobject]@{ Anchor=$phaseIsAnchor.Name; RelativePath=$phaseIsRelativePath }
          }
      }
      throw 'Candidate is outside the approved discovery anchors.'
  }

  function Get-PhaseIsSignerCertificateSha256 {
      param($Signature)
      if ($null -eq $Signature.SignerCertificate) { return $null }
      $phaseIsCertificateHasher = [Security.Cryptography.SHA256]::Create()
      try {
          return ([BitConverter]::ToString($phaseIsCertificateHasher.ComputeHash($Signature.SignerCertificate.RawData))).Replace('-','')
      } finally {
          $phaseIsCertificateHasher.Dispose()
      }
  }

  try {
  $phaseIsApplications = 'powershell.exe','git.exe','claude.exe','claude.cmd','codex.exe','codex.cmd','signtool.exe','CiTool.exe'
  $phaseIsApplicationFacts = foreach ($phaseIsApplication in $phaseIsApplications) {
      foreach ($phaseIsCommand in @(Get-Command $phaseIsApplication -CommandType Application -All -ErrorAction SilentlyContinue)) {
          $phaseIsItem = Get-Item -LiteralPath $phaseIsCommand.Source -Force
          $phaseIsHash = Get-FileHash -LiteralPath $phaseIsItem.FullName -Algorithm SHA256
          $phaseIsSignature = Get-AuthenticodeSignature -LiteralPath $phaseIsItem.FullName
          $phaseIsLocator = ConvertTo-PhaseIsPublicLocator -PrivatePath $phaseIsItem.FullName
          [pscustomobject]@{ Name=$phaseIsApplication; Anchor=$phaseIsLocator.Anchor; RelativePath=$phaseIsLocator.RelativePath; PrivatePath=$phaseIsItem.FullName; Version=$phaseIsItem.VersionInfo.FileVersion; Sha256=$phaseIsHash.Hash; SignatureStatus=[string]$phaseIsSignature.Status; SignerCertificateSha256=(Get-PhaseIsSignerCertificateSha256 $phaseIsSignature) }
      }
  }
  $phaseIsApplicationFacts | Select-Object Name,Anchor,RelativePath,Version,Sha256,SignatureStatus,SignerCertificateSha256 | Format-Table -AutoSize

  $phaseIsVsWhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
  if (-not (Test-Path -LiteralPath $phaseIsVsWhere -PathType Leaf)) { throw 'vswhere.exe missing.' }
  $phaseIsVsWhereItem = Get-Item -LiteralPath $phaseIsVsWhere -Force
  $phaseIsVsWhereHash = Get-FileHash -LiteralPath $phaseIsVsWhereItem.FullName -Algorithm SHA256
  $phaseIsVsWhereSignature = Get-AuthenticodeSignature -LiteralPath $phaseIsVsWhereItem.FullName
  $phaseIsVsWhereLocator = ConvertTo-PhaseIsPublicLocator -PrivatePath $phaseIsVsWhereItem.FullName
  $phaseIsVsWhereFact = [pscustomobject]@{ Name='vswhere.exe'; Anchor=$phaseIsVsWhereLocator.Anchor; RelativePath=$phaseIsVsWhereLocator.RelativePath; PrivatePath=$phaseIsVsWhereItem.FullName; Version=$phaseIsVsWhereItem.VersionInfo.FileVersion; Sha256=$phaseIsVsWhereHash.Hash; SignatureStatus=[string]$phaseIsVsWhereSignature.Status; SignerCertificateSha256=(Get-PhaseIsSignerCertificateSha256 $phaseIsVsWhereSignature) }
  $phaseIsVsWhereFact | Select-Object Name,Anchor,RelativePath,Version,Sha256,SignatureStatus,SignerCertificateSha256 | Format-Table -AutoSize
  $phaseIsVsInstalls = @(& $phaseIsVsWhere -all -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -format json | ConvertFrom-Json)
  if ($LASTEXITCODE -ne 0 -or $phaseIsVsInstalls.Count -eq 0) { throw 'MSVC toolchain missing.' }
  $phaseIsMsvcCandidates = foreach ($phaseIsVsInstall in $phaseIsVsInstalls) {
      foreach ($phaseIsMsvcRoot in @(Get-ChildItem -LiteralPath (Join-Path $phaseIsVsInstall.installationPath 'VC\Tools\MSVC') -Directory)) {
          $phaseIsMsvcFiles = @('cl.exe','link.exe','dumpbin.exe') | ForEach-Object { Join-Path $phaseIsMsvcRoot.FullName (Join-Path 'bin\Hostx64\x64' $_) }
          if (@($phaseIsMsvcFiles | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) }).Count -eq 0) {
              foreach ($phaseIsMsvcFile in $phaseIsMsvcFiles) {
                  $phaseIsMsvcItem = Get-Item -LiteralPath $phaseIsMsvcFile -Force
                  $phaseIsMsvcHash = Get-FileHash -LiteralPath $phaseIsMsvcFile -Algorithm SHA256
                  $phaseIsMsvcSignature = Get-AuthenticodeSignature -LiteralPath $phaseIsMsvcFile
                  $phaseIsMsvcLocator = ConvertTo-PhaseIsPublicLocator -PrivatePath $phaseIsMsvcItem.FullName
                  [pscustomobject]@{ Toolset=[version]$phaseIsMsvcRoot.Name; Name=$phaseIsMsvcItem.Name; Anchor=$phaseIsMsvcLocator.Anchor; RelativePath=$phaseIsMsvcLocator.RelativePath; PrivatePath=$phaseIsMsvcItem.FullName; Version=$phaseIsMsvcItem.VersionInfo.FileVersion; Sha256=$phaseIsMsvcHash.Hash; SignatureStatus=[string]$phaseIsMsvcSignature.Status; SignerCertificateSha256=(Get-PhaseIsSignerCertificateSha256 $phaseIsMsvcSignature) }
              }
          }
      }
  }
  $phaseIsMsvcCandidates | Sort-Object Toolset,Name,Anchor,RelativePath -Descending | Select-Object Toolset,Name,Anchor,RelativePath,Version,Sha256,SignatureStatus,SignerCertificateSha256 | Format-Table -AutoSize

  $phaseIsKitsRegistryKey = 'HKLM:\SOFTWARE\Microsoft\Windows Kits\Installed Roots'
  $phaseIsKitsRoot = (Get-ItemProperty -LiteralPath $phaseIsKitsRegistryKey).KitsRoot10
  $phaseIsKitsRootLocator = ConvertTo-PhaseIsPublicLocator -PrivatePath $phaseIsKitsRoot
  $phaseIsKitsAuthorityBytes = [Text.Encoding]::UTF8.GetBytes("$phaseIsKitsRegistryKey`0KitsRoot10`0$($phaseIsKitsRootLocator.Anchor)`0$($phaseIsKitsRootLocator.RelativePath)")
  $phaseIsKitsAuthorityHasher = [Security.Cryptography.SHA256]::Create()
  try {
      $phaseIsKitsAuthoritySha256 = ([BitConverter]::ToString($phaseIsKitsAuthorityHasher.ComputeHash($phaseIsKitsAuthorityBytes))).Replace('-','')
  } finally {
      $phaseIsKitsAuthorityHasher.Dispose()
  }
  [pscustomobject]@{ Name='Windows-Kits-installed-root'; RegistryKey=$phaseIsKitsRegistryKey; ValueName='KitsRoot10'; Anchor=$phaseIsKitsRootLocator.Anchor; RelativePath=$phaseIsKitsRootLocator.RelativePath; AuthoritySha256=$phaseIsKitsAuthoritySha256 }
  $phaseIsKitVersions = Get-ChildItem -LiteralPath (Join-Path $phaseIsKitsRoot 'Include') -Directory | Sort-Object Name -Descending
  $phaseIsSdkVersions = @($phaseIsKitVersions | Where-Object { (Test-Path -LiteralPath (Join-Path $_.FullName 'shared')) -and (Test-Path -LiteralPath (Join-Path $_.FullName 'um')) -and (Test-Path -LiteralPath (Join-Path $_.FullName 'ucrt')) })
  $phaseIsWdkVersions = @($phaseIsKitVersions | Where-Object { (Test-Path -LiteralPath (Join-Path $_.FullName 'km')) -and (Test-Path -LiteralPath (Join-Path $phaseIsKitsRoot (Join-Path 'Lib' (Join-Path $_.Name 'km\x64')))) })
  if ($phaseIsSdkVersions.Count -eq 0 -or $phaseIsWdkVersions.Count -eq 0) { throw 'Windows SDK/WDK headers or libraries missing.' }
  $phaseIsSdkVersions.Name
  $phaseIsWdkVersions.Name

  $phaseIsCodexCandidates = @(
      foreach ($phaseIsCodexCommand in @(Get-Command 'codex.cmd' -CommandType Application -All -ErrorAction SilentlyContinue)) {
          $phaseIsCodexShimItem = Get-Item -LiteralPath $phaseIsCodexCommand.Source -Force
          $phaseIsCodexPackage = Join-Path (Split-Path -Parent $phaseIsCodexShimItem.FullName) 'node_modules\@openai\codex'
          $phaseIsCodexPackageJsonPath = Join-Path $phaseIsCodexPackage 'package.json'
          $phaseIsCodexPackageJson = Get-Content -Raw -Encoding UTF8 $phaseIsCodexPackageJsonPath | ConvertFrom-Json
          $phaseIsCodexTarget = Join-Path $phaseIsCodexPackage 'node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc'
          $phaseIsCodexBin = @(Get-ChildItem -LiteralPath (Join-Path $phaseIsCodexTarget 'bin') -File | Sort-Object Name)
          $phaseIsCodexBinNames = @($phaseIsCodexBin.Name)
          if (Compare-Object $phaseIsCodexBinNames @('codex-code-mode-host.exe','codex.exe')) { throw 'Codex native bin closure drift.' }
          $phaseIsCodexFiles = @(
              [pscustomobject]@{ Role='shim'; PrivatePath=$phaseIsCodexShimItem.FullName }
              [pscustomobject]@{ Role='package-json'; PrivatePath=$phaseIsCodexPackageJsonPath }
              [pscustomobject]@{ Role='codex-js'; PrivatePath=(Join-Path $phaseIsCodexPackage 'bin\codex.js') }
              [pscustomobject]@{ Role='platform-package-json'; PrivatePath=(Join-Path $phaseIsCodexTarget 'codex-package.json') }
              foreach ($phaseIsCodexNativeFile in $phaseIsCodexBin) {
                  [pscustomobject]@{ Role=('native-' + $phaseIsCodexNativeFile.Name); PrivatePath=$phaseIsCodexNativeFile.FullName }
              }
          )
          $phaseIsCodexFileFacts = @(
              foreach ($phaseIsCodexFile in $phaseIsCodexFiles) {
                  $phaseIsCodexItem = Get-Item -LiteralPath $phaseIsCodexFile.PrivatePath -Force
                  $phaseIsCodexHash = Get-FileHash -LiteralPath $phaseIsCodexItem.FullName -Algorithm SHA256
                  $phaseIsCodexSignature = Get-AuthenticodeSignature -LiteralPath $phaseIsCodexItem.FullName
                  $phaseIsCodexLocator = ConvertTo-PhaseIsPublicLocator -PrivatePath $phaseIsCodexItem.FullName
                  [pscustomobject]@{ Role=$phaseIsCodexFile.Role; Anchor=$phaseIsCodexLocator.Anchor; RelativePath=$phaseIsCodexLocator.RelativePath; PrivatePath=$phaseIsCodexItem.FullName; Sha256=$phaseIsCodexHash.Hash; SignatureStatus=[string]$phaseIsCodexSignature.Status; SignerCertificateSha256=(Get-PhaseIsSignerCertificateSha256 $phaseIsCodexSignature) }
              }
          )
          $phaseIsCodexShimFact = @($phaseIsCodexFileFacts | Where-Object { $_.Role -ceq 'shim' })[0]
          $phaseIsCodexSelectionKey = "$($phaseIsCodexShimFact.Anchor)`0$($phaseIsCodexShimFact.RelativePath)"
          [pscustomobject]@{ Version=[version]$phaseIsCodexPackageJson.version; SelectionKey=$phaseIsCodexSelectionKey; FileFacts=$phaseIsCodexFileFacts }
      }
  )
  if ($phaseIsCodexCandidates.Count -eq 0) { throw 'Codex candidate set is empty.' }
  $phaseIsHighestCodexVersion = ($phaseIsCodexCandidates | Sort-Object Version -Descending | Select-Object -First 1).Version
  $phaseIsHighestCodexCandidates = @($phaseIsCodexCandidates | Where-Object { $_.Version -eq $phaseIsHighestCodexVersion })
  $phaseIsReferenceCodexFacts = @($phaseIsHighestCodexCandidates[0].FileFacts | ForEach-Object { "$($_.Role)`0$($_.Sha256)`0$($_.SignatureStatus)`0$($_.SignerCertificateSha256)" })
  foreach ($phaseIsCodexCandidate in @($phaseIsHighestCodexCandidates | Select-Object -Skip 1)) {
      $phaseIsComparableCodexFacts = @($phaseIsCodexCandidate.FileFacts | ForEach-Object { "$($_.Role)`0$($_.Sha256)`0$($_.SignatureStatus)`0$($_.SignerCertificateSha256)" })
      if (Compare-Object $phaseIsReferenceCodexFacts $phaseIsComparableCodexFacts -CaseSensitive) { throw 'Equal-version Codex candidates differ in bytes or signer.' }
  }
  $phaseIsCodexSelectionKeys = [string[]]@($phaseIsHighestCodexCandidates.SelectionKey)
  [Array]::Sort($phaseIsCodexSelectionKeys, [StringComparer]::Ordinal)
  $phaseIsSelectedCodex = @($phaseIsHighestCodexCandidates | Where-Object { $_.SelectionKey -ceq $phaseIsCodexSelectionKeys[0] })[0]
  if ([string]$phaseIsSelectedCodex.Version -cne '0.147.0') { throw 'Codex package version drift.' }
  $phaseIsCodexCandidates | ForEach-Object { $_.FileFacts } | Select-Object Role,Anchor,RelativePath,Sha256,SignatureStatus,SignerCertificateSha256 | Format-Table -AutoSize

  $phaseIsCiToolCandidates = @($phaseIsApplicationFacts | Where-Object { $_.Name -ceq 'CiTool.exe' })
  if ($phaseIsCiToolCandidates.Count -eq 0) { throw 'CiTool candidate set is empty.' }
  $phaseIsHighestCiToolVersion = ($phaseIsCiToolCandidates | Sort-Object { [version]$_.Version } -Descending | Select-Object -First 1).Version
  $phaseIsHighestCiToolCandidates = @($phaseIsCiToolCandidates | Where-Object { [version]$_.Version -eq [version]$phaseIsHighestCiToolVersion })
  $phaseIsReferenceCiToolFact = "$($phaseIsHighestCiToolCandidates[0].Sha256)`0$($phaseIsHighestCiToolCandidates[0].SignatureStatus)`0$($phaseIsHighestCiToolCandidates[0].SignerCertificateSha256)"
  foreach ($phaseIsCiToolCandidate in @($phaseIsHighestCiToolCandidates | Select-Object -Skip 1)) {
      $phaseIsComparableCiToolFact = "$($phaseIsCiToolCandidate.Sha256)`0$($phaseIsCiToolCandidate.SignatureStatus)`0$($phaseIsCiToolCandidate.SignerCertificateSha256)"
      if ($phaseIsReferenceCiToolFact -cne $phaseIsComparableCiToolFact) { throw 'Equal-version CiTool candidates differ in bytes or signer.' }
  }
  $phaseIsCiToolSelectionKeys = [string[]]@($phaseIsHighestCiToolCandidates | ForEach-Object { "$($_.Anchor)`0$($_.RelativePath)" })
  [Array]::Sort($phaseIsCiToolSelectionKeys, [StringComparer]::Ordinal)
  $phaseIsSelectedCiToolKey = $phaseIsCiToolSelectionKeys[0]
  $phaseIsSelectedCiTool = @($phaseIsHighestCiToolCandidates | Where-Object { "$($_.Anchor)`0$($_.RelativePath)" -ceq $phaseIsSelectedCiToolKey })[0]
  $phaseIsSelectedCiToolHash = Get-FileHash -LiteralPath $phaseIsSelectedCiTool.PrivatePath -Algorithm SHA256
  if ($phaseIsSelectedCiToolHash.Hash -cne $phaseIsSelectedCiTool.Sha256) { throw 'CiTool changed after discovery.' }
  $phaseIsCiPolicyOutput = @(& $phaseIsSelectedCiTool.PrivatePath --list-policies 2>&1)
  if ($LASTEXITCODE -ne 0) { throw 'Code-integrity policy enumeration failed.' }
  $phaseIsCiPolicyHasher = [Security.Cryptography.SHA256]::Create()
  try {
      $phaseIsCiPolicyBytes = [Text.Encoding]::UTF8.GetBytes(($phaseIsCiPolicyOutput -join "`n"))
      $phaseIsCiPolicySha256 = ([BitConverter]::ToString($phaseIsCiPolicyHasher.ComputeHash($phaseIsCiPolicyBytes))).Replace('-','')
  } finally {
      $phaseIsCiPolicyHasher.Dispose()
  }
  [pscustomobject]@{ Name='CiTool-policy-inventory'; Anchor=$phaseIsSelectedCiTool.Anchor; RelativePath=$phaseIsSelectedCiTool.RelativePath; ToolSha256=$phaseIsSelectedCiTool.Sha256; PolicyOutputSha256=$phaseIsCiPolicySha256; PolicyLineCount=$phaseIsCiPolicyOutput.Count }
  } catch {
      throw 'Phase IS candidate discovery failed; private path-bearing diagnostics were suppressed.'
  }
  ```
- **Redaction boundary for the discovery block:** `PrivateRoot`, `PrivatePath`, raw registry roots,
  and raw native-tool output remain process-memory-only.
  Only the explicit approved-anchor/relative-path projections and cryptographic facts above may be
  serialized, copied to a transcript, or posted. The outer catch replaces path-bearing failure text
  with its fixed public error.
- **Produces:** the three committed contract records at §5's exact paths plus their remotely
  reread #162 commit/tree/blob/raw-hash seal; no containment binary, future-output hash, or behavioral
  observation
- **Exact gates:** the schema record closes each artifact/property/type choice listed in §5; the
  nonce record covers each D5 field; the C2V route record/selector and C2A resolution revalidate from
  their sealed Git blobs against the frozen comment ID/body and selected branch, no later exact-header
  comment exists, and the core/override plan-blob rule holds; pre-implementation inputs include
  existing dependencies only
  and bind the C2E environment receipt, complete guest candidate enumeration, deterministic selection
  rule, approved-anchor/relative locators, versions, hashes, signatures, candidate-set digests,
  snapshot/boot/publisher facts, and exact policy IDs/hashes/mode/rules plus canary evidence.
  Every discovery/version authority is itself bound, including `vswhere.exe`, the Windows Kits
  installed-root registry key/value name plus approved-anchor/relative locator and canonical fact
  digest, each Codex shim, the
  top-level and platform `package.json` files, `codex.js`,
  and both native Codex binaries. A reviewer confirms all three records match D5, D9, and the selected
  route. C3 upgrades discovery facts to retained-handle identities and the actually consumed
  dependency/loader/policy closure before any distribution build/install or host action.
- **Stop conditions:** nonce contract weakened without plan amendment, C2E receipt/snapshot/connector
  drift, required guest toolchain/admission boundary unavailable, any coordinator machine-local fact
  substituted for a guest fact, route-dependent input left implicit, or candidate drift during the freeze
- **Operator action:** none within C2N. A proposed D5 amendment or missing signing/admission policy
  returns to C2E and requires a separate operator decision before C2N is resumed.
- **Done when:** all three Git blobs and the remotely verified seal are immutable inputs to C2P and
  carry no hash for a C3 output
- **Depends on:** C2E
- **Status:** BLOCKED ON C2E

### Completion Stage C2P: Author the Step-108P implementation subplan

- **Problem:** Step 108P's packet crosses several high-stakes producer/consumer boundaries and does
  not fit one producer context; dispatching aggregate C3 as one build step would violate the
  repository's step-sizing contract and make integration ownership ambiguous.
- **Type:** code / planning checkpoint
- **Issue:** #162
- **Prerequisites:** C2N complete; its three contract blobs and remote seal reverified; C2E's
  environment receipt and R0 lineage still match; the selected route, guest signing/admission
  prerequisites, and candidate tool/host inputs are no longer undecided
- **Files:** `documentation/phase-is-step-108p-build-plan.md` (new) and this completion runbook only
  if a cross-reference needs correction
- **Actions:** derive a `/build-phase`-compatible sequence from C2N's exact records and the Mandatory
  C3 invariants. Give every `### Step N:` one observable production-entry-point behavior, explicit
  producer/consumer files, issue #162, `--reviewers deep`, falsifiable acceptance, and dependencies.
  Assign every C3 artifact, negative class, route-specific obligation, UAT replacement, and final
  certification gate exactly once; add explicit integration steps wherever one slice consumes
  another's output. Mark source edits and Git integration as coordinator-owned; mark native build,
  signing, policy, driver, and host execution as guest-only. Split any parent-held elevated action
  from the code that prepares its exact inputs. The final step freezes the integrated candidate and owns review plus the detached
  repo-root gate. Do not create a new Phase IS unit or issue.
- **Exact gates:** both `/plan-review documentation/phase-is-step-108p-build-plan.md` and
  `/plan-wrap documentation/phase-is-step-108p-build-plan.md` report no Blocker; every technical choice is fixed
  by C2N or resolved in the subplan; every code step fits one producer context and has one production
  caller; `python tools/gen_manifest.py` runs after the new documentation path is staged;
  `python -m pytest tests/package-integrity` and `git diff --check` pass; independent review reports
  no High or Medium finding
- **Produces:** one reviewed, committed, build-phase-compatible Step-108P subplan whose steps all
  report to #162; no runtime code, binary, host action, or behavioral observation
- **Stop conditions:** an unresolved schema/tool/signing/route choice, a step that combines multiple
  observable behaviors, an unmapped producer/consumer edge, a code/operator hybrid, a missing final
  integration gate, or a plan review/wrap blocker
- **Operator action:** none unless C2N explicitly stopped on an unavailable admission/signing policy;
  any such decision occurs before C2P resumes
- **Done when:** the committed subplan is independently reviewed, plan-review/plan-wrap-ready, and
  maps the whole C3 envelope exactly once with explicit integration ownership
- **Depends on:** C2N
- **Status:** BLOCKED ON C2N

### Completion Stage C3: Implement and certify Step 108P

- **Problem:** The accepted UAT is deliberately non-runnable until its native containment packet,
  schemas, parsers, hooks, and cleanup are committed, integrated, and reviewed. This stage is the
  aggregate execution/certification envelope, not one producer task.
- **Type:** orchestration / certification
- **Issue:** #162
- **Prerequisites:** C2P complete; supported C0 dispatch protocol; frozen route/source hashes and
  approved-anchor-relative tool locators; sealed C2E receipt/R0 lineage; physical identity admission
  remains owned by the C2P implementation steps and their integrated candidate
- **Files:** `documentation/phase-is-step-108p-build-plan.md` plus the Step-108P rows in §4 selected
  and assigned by that subplan
- **Actions:** execute the C2P subplan in dependency order, one independently reviewed producer slice
  at a time. Fresh Terra producers edit isolated coordinator worktrees; the parent sends exact
  content-addressed candidates through the C2E connector and runs every native/security gate in the
  sole writable R0 descendant. A fresh reviewer uses a separately restored serialized descendant;
  the guest never classifies the verdict or pushes Git. Before any candidate user/kernel object is
  signed or loaded, a separate no-history reviewer must PASS the immutable source, unsigned object,
  compiler/input manifest, and source-to-object binding. Only the parent may then issue one exact-
  hash signer-appliance grant; neither producer nor execution guest can reach the signer/key. After
  kernel entry, treat guest-local events, HMAC, services, and files as kernel-controlled and use
  external provider/signer facts or attended observations of the reviewed bytes for load-sensitive
  claims. Integrate the complete packet in the phase
  plan and UAT. Replace the one comparator
  placeholder, the 18 unconditional blockers, and the two receipt-pinned command tokens. Preserve
  redaction markers and the blank Step-109 observation/verdict cells. Bind the four roots, retained
  handles, file identities, final paths, link counts, receipt chain, environment/secrets, executable
  and descendant process tree, hooks/policies, handle-coupled reads, kernel deny-default writes,
  evidence publication, and three-target cleanup.
- **Candidate lock:** after schemas, sources, binaries, bundle, and tests exist, create
  `skill-mesh/phase-is-candidate-lock/v1` from their actual identities/hashes and the C2N manifest.
  Seal and remotely verify it through §5's outside-worktree protocol. Repeat this lock plus affected
  review/gates after any candidate byte changes; C2N is not rewritten merely because C3 created its
  declared outputs. At the end of the candidate lock, destroy the signer appliance and private leaf,
  remotely verify their absence, and retain only public verification material plus the destruction
  receipt. Any later candidate byte change requires a new signer/publisher/policy/R0 lineage and a
  repeated source/object review; C4 never runs beside a live signing authority.
- **Toolchain/host admission:** build in the sealed guest with the C2N-selected MSVC using `/std:c++17` and compiler
  include tracing, and link with verbose library tracing. Canonicalize and deduplicate the observed
  compiler/linker/`dumpbin`, SDK/WDK header/library/tool paths. Open both each C2N anchor and candidate
  through no-follow retained handles, resolve both final paths, and reject a reparse or physical target
  outside the anchor before applying the ordinal anchor/relative selection. Record final paths,
  identities, versions, hashes, link counts, and signatures for each consumed file. Recursively run
  the pinned `dumpbin` over the launcher/driver/helper PE
  import, delay-import, headers, and load-configuration data; resolve each non-system dependency
  through the closed DLL search policy and bind the applicable KnownDLL/code-integrity policy facts.
  Revalidate the exact C2E/C2N signing certificate thumbprint/chain, `CiTool` policy
  identifier/hash/output, and pre-existing publisher rule that admits the launcher before entry
  point; then bind each final launcher/helper/driver hash and signature. The candidate lock contains this
  closure and rejects an added/missing import, header/library/tool, signer, policy, loader path, or
  byte change.

  Resolve Claude from the C2N candidate set to exactly D9's version/hash, then bind its physical
  executable identity and signature. For Codex, bind the exact `codex.cmd`, `bin/codex.js`, platform
  package metadata, and the complete two-file native `bin` set
  (`codex.exe`, `codex-code-mode-host.exe`); require version `0.147.0`, record identities/hashes/
  signatures, and invoke the pinned `codex.exe` directly. No Node, JavaScript entrypoint, alias,
  function, PATH lookup, or unenumerated vendor binary enters the delivery process tree.
- **Exact iteration gates:** focused `tests/phase-is-uat/**`; strict schema and complete negative
  corpus; `python tools/gen_manifest.py` for inventory changes; `python -m pytest
  tests/package-integrity`; route-specific reference/distribution gates; PowerShell 5.1 parse checks;
  `git diff --check`. Route 1 also regenerates `documentation/release-candidate-report.md` after any
  representative `skills/plan-init/core.md` edit.
- **Review gate:** independent fresh code reviewers using the C0-proven parent/private-verdict
  protocol. Require zero High and zero Medium findings against an immutable candidate.
- **DONE gate:** repeat C1's stable-machine, detached, sentinel-first repo-root `python -m pytest`
  protocol after the final C3 bytes are frozen. Compare to the baseline owner read immediately
  before launch and preserve its skip count.
- **Produces:** committed versioned packet, schemas, binaries/build recipe, tests, exact hashes,
  review verdicts, root-gate evidence, and a closed #162; no behavioral UAT observation
- **Stop conditions:** any C2E receipt/snapshot/policy/boot/connector drift; any coordinator
  certificate, policy, Secure Boot, BCD, SDK/WDK, driver, or host-session mutation; any placeholder or
  blocker remains; an operator cell is prefilled; identity
  can be re-established by path reopen; secret/policy/process rules are broader than the seven-mode
  matrix; the real profile becomes a target; publication precedes its attestation; cleanup includes
  the evidence export; unsigned object/source binding lacks a fresh PASS; a producer/execution guest
  can reach signing authority; guest-local post-kernel evidence is treated as independent security
  proof; the signer appliance survives candidate lock; review or root gate fails
- **Operator action:** no design choice, code authoring, or UAT observation. Any guest-admin action is
  a pre-authored, hash-bound C2E/C2P operator atom with a canonical receipt; if the selected provider
  cannot execute it without exposing credentials or arbitrary elevation to a producer, stop.
- **Done when:** Phase IS Step 108P's Done-when is met and the exact immutable packet is ready for an
  attended run
- **Depends on:** C2P
- **Status:** BLOCKED BEFORE IMPLEMENTATION

### Completion Stage C4: Run attended Step 109

- **Problem:** Prose tests do not prove real named-skill behavior or host delivery.
- **Type:** operator
- **Issue:** #153
- **Prerequisites:** C3 complete; packet hashes, C2E environment receipt/R0 lineage, and selected route
  re-verified; signer appliance/private leaf destruction remotely verified; one attended writable R0
  descendant; documented session
  working directory/Base directory binds each host to the intended scratch project; the two
  process-scoped credentials named in the quickstart are available through the certified broker
- **Actions:** run only in the sealed disposable guest and use the certified packet to create and bind
  the four roots. Build/install/reverify the
  selected-route bytes. Run D10 rows 1–5 serially, including the second-pass fixed point for row 3.
  Verify exact normalized Codex project-payload equality and the Claude import event while both
  instruction files remain locked to attested bytes. Record behavioral differences. Emit the
  evidence attestation, publish and remotely reread it, clean up the three disposable roots, emit
  the cleanup attestation, publish and remotely reread it, and retain the evidence-export root.
- **Exact gates:** the pre-build, launch-attestation, readiness, build/install/inspect,
  environment/hook/policy, read/write/process, evidence-publication, and cleanup checks defined by
  the certified packet; five completed D10 rows; row-3 no-op fixed point; both host-delivery checks;
  two remotely hash-verified redacted records; exact final disposition for each disposable root
- **Produces:** observations in the existing UAT, two remote redacted records, retained evidence
  export, and the Step-109 verdict; no code artifact
- **Stop conditions:** any action targets the coordinator; C2E environment/policy/boot/snapshot drift;
  host binds to the stale personal `plan-init`; session cwd/Base directory does
  not prove scratch-project binding; any real-profile write exceeds the certified Codex transport
  exception; instruction bytes drift under lock; unsigned object/source binding lacks a fresh PASS;
  a producer/execution guest can reach signing authority; guest-local post-kernel evidence is treated
  as independent security proof; the signer appliance survives candidate lock; a packet defect
  requires code; remote reread fails; cleanup cannot assign one exact disposition to a disposable root
- **Operator action:** explicitly start the attended run, operate/observe the genuine Claude and
  Codex sessions, and accept or reject each human behavioral observation
- **Done when:** the Phase IS Step-109 Done-when is met, evidence is remotely verified, the three
  disposable roots have recorded dispositions, the retained export is named, and C2E.33 is unblocked
- **Depends on:** C3
- **Status:** BLOCKED BEFORE GRADING

### Completion Stage C5: Close Phase IS

- **Problem:** Passing artifacts and UAT need one coherent status/issue/repository closeout.
- **Type:** code / documentation administration
- **Issues:** #152 and #162 should already be closed; close #153 and umbrella #143 after verification
- **Prerequisites:** C4 PASS with complete evidence locators; C2E.33 has destroyed the powered-off
  guest OS/snapshot lineage and retained the verified encrypted run volume as a private artifact
- **Actions:** verify C2E.33's redacted guest-destruction and retained-run-volume disposition plus its
  provider-native C4-plus-120-day fail-safe deletion rule and later absence-verification owner. Prepare,
  review, commit, push with expected-old protection, and remotely reread an immutable pre-closeout
  candidate that records every final status change except that retention shortening and phase closeout
  remain pending; do not close an issue yet. Bind that candidate plus the exact C4 PASS transition,
  C2E.33 wait result, and remotely reread #143 disposition marker into the exact private parent-signed
  C5 shortening-intent schema and proof profile defined by the C2E environment plan, with a fixed
  `created_utc` and derived authorized deadline. Under C2E.4's dormant preauthorization, mint one new
  non-exportable parent-only provider identity lasting at most one hour and scoped only to
  `shorten-c5` plus independent reread for the exact retained volume/old rule. Atomically shorten the
  deadline to the earlier of intent `created_utc` plus 90 days or the existing hard cap, verify the
  updated schedule receipt, then revoke/reread absent both the JIT identity and preauthorization.
  Destroy and independently reread absent the surviving control-receipt key, wait-result key, and
  emergency-broker private authority, recording all three destruction receipts; preserve only public
  verification material and the separately scoped read-only retention identity through its scheduled
  absence proof.
  Finally update `plan.md`, the phase plan, README status prose, the UAT verdict, and issue
  comments to the same 11-of-11/DONE state. Keep #159 open and deferred. Leave #163 closed as a
  historical checkpoint and point current readers to the final evidence rather than rewriting its
  old snapshot. Run `/plan-wrap` against the reduced current documents, then `/repo-update`; the final
  status-only commit/push binds the shortening, JIT-identity/preauthorization revocation, and control/
  wait/emergency-broker destruction receipts and is the first point that may claim 11-of-11/DONE or
  close issues.
- **Exact gates:** regenerate the manifest if file inventory changed; `python -m pytest
  tests/package-integrity`; applicable link/reference gates; `git diff --check`; clean synchronized
  branch after the authorized commit/push. Do not repeat the two-hour root gate for observation-only
  UAT/status edits. If closeout changes product code, runtime, tests, generated distribution inputs,
  executable UAT fences, or file inventory after C3's gate, establish a new candidate and rerun the
  affected full gate.
- **Produces:** Phase IS marked 11 of 11 landed and certified DONE, final evidence index, closed
  #153/#143, synchronized repository, an explicit deferred #159, no surviving runnable C2E guest
  lineage, and one explicitly owned private external retained-run-volume locator referenced in Git
  only by digest, owner, and deadline
- **Stop conditions:** missing remote evidence, inconsistent status surfaces, expired/mismatched C5-
  shortener preauthorization, identity scope/lifetime overrun, absent/failed retained-volume schedule
  shortening, identity/preauthorization revocation, control/wait/emergency-broker destruction, or
  later verification owner, new unreviewed code, stale generated
  artifacts, failing package/reference gate, or dirty/diverged repository
- **Operator action:** none; if a new publication target or scope is proposed, stop this stage and
  request separate authority
- **Done when:** authoritative status, evidence, issues, and Git agree that Phase IS is complete
- **Depends on:** C2E.33
- **Status:** BLOCKED ON STEP 109

## 8. Risks and Open Questions

| Item | Risk | Mitigation or owner |
|---|---|---|
| Build-step contract | Fresh context may exist while private verdict authority does not | C0 proves five properties separately and halts on uncertainty |
| C2E operator choices | A fresh agent may start execution, pick infrastructure, or provision silently | The Phase IS route is sealed as `core-uat-mode`; require separate C2E execution authorization, the Step-4 provider/license/cost/broker/retention decision, and the Step-29 provisioning wait |
| Review provenance | Good object reviews may lack the required authenticated dispatch trail | Retain them as support and repeat under the C0-proven protocol when promotion is not proven |
| Evidence drift | Issue bodies and checkpoint #163 name superseded UAT bytes | Recompute the Git blob/raw identity and prefer verified newer comments |
| Gate circularity | Updating the baseline before comparison can make a run certify itself | Read owner, run, read sentinel, compare, then update |
| Machine starvation | Low-memory PowerShell subprocesses can produce misleading failures | Enforce the 2 GiB launch floor and record start facts |
| Nonce substitution/replay | An underspecified nonce can make receipt chaining ambiguous | D5 fixes generator, encoding, lifecycle, consumers, and negative cases |
| Operator/code boundary | A missing packet component may tempt a live patch during UAT | Stop C4 and return the defect to #162 |
| Host binding | A stale personal skill can false-pass D10 row 2 | Bind by documented session cwd/Base directory and verify loaded source, not path alone |
| Real-profile damage | The installed home is owned and may be junctioned | Use admitted scratch roots and retained handles; real profile is never a cleanup target |
| Concurrent sessions | HEAD or evidence can move between checks | Re-run status/log/hash at each stage boundary and freeze immutable candidates |
| Disposable environment | Missing WDK/signing/admission prerequisites may tempt mutation of this workstation | C2E seals a separate guest; any coordinator security/boot/tool mutation is a hard stop |
| Guest authority | A producer with guest admin, signing, Git, or verdict authority could certify its own bytes | Parent controls single-use asymmetric elevation grants, Git integration, reviewer sidecar key, and final classification; the private signing leaf exists only in a separate non-snapshotted appliance with no execution-guest route, and accepts an exact object only after fresh source/object review; guest facts are inputs only |
| Future-hash circularity | The final launcher does not exist when admission must be frozen | C2E/C2N freeze a publisher signer rule and C3 later binds final image hashes/signatures |
| Environment drift | Snapshot, policy, boot state, signer, or connector can change between C2N and C4 | Bind C2E receipt/R0 lineage and revalidate before every guest-sensitive stage/action |
| Evidence disposal | Destroying the guest can erase the retained export, violate the frozen UAT topology, or leave private bytes indefinitely | Put all four UAT roots under one common parent on one encrypted run volume; C2E.33 destroys runnable OS/snapshots only after remote rereads and retains that volume as private under provider-native automatic deletion plus later absence verification |
| Implementation size | The Step-108P packet cannot fit one producer context without hiding integration seams | C2P derives a reviewed build-step-sized subplan after C2N freezes the exchanged contracts; C3 only orchestrates and certifies it |
| Scope creep | #159 and the separate plan-init contract-owner defect are real but unrelated | Keep both outside this chain and give each a separate bounded change |

The Phase IS route is no longer open: C2V/C2A sealed `core-uat-mode`. The intentional remaining
operator choices are separate C2E execution authorization, Step 4's provider/license/cost/artifact/
broker/retention selection, and Step 29's provisioning approval. A fresh executor may not infer any
of them from the sealed route.

## 9. Testing Strategy

### Gate classes

| Gate | Purpose | May mark a code/certification stage DONE? |
|---|---|---|
| `python -m pytest tests/package-integrity` | Fast inventory, prose-contract, and packaging feedback | No |
| C2E schema/safety negatives plus live guest substrate smoke | Prove the disposable environment, parent/guest authority split, publisher admission, boot state, and workstation non-mutation | Yes for C2E readiness only |
| C2P plan-review, plan-wrap, and independent review | Prove Step 108P is decomposed into bounded slices with explicit integration ownership | No |
| Focused `tests/phase-is-uat/**` and route-specific tests | Step-108P development and falsification | No |
| PowerShell 5.1 parse enumeration | Syntax-check the complete PowerShell-bearing UAT set | No |
| `python -m pytest` from repo root, no path | Eight `tests/` suites plus the three root-only test roots | Yes, with review and stage-specific evidence |
| Attended Step-109 packet gates | Real skill behavior, host delivery, publication, and cleanup | Yes for operator Step 109; they do not replace a code-stage root gate |

### Root-gate evidence protocol

For C1 and C3, store stdout, stderr, start facts, and the exit sentinel outside the repository. The
sentinel is authoritative for process completion and is read before the log. The log must contain a
complete pytest summary consistent with exit `0`; a tail without a sentinel is not a result. Keep the
candidate HEAD stable for the run and compare against the baseline value read before launch.

### Falsification obligations

Before preserving a repository-wide rule, enumerate the set it quantifies over. C1 repeats the
Step-108 profile/fence/blocker/credential/mode/root/publication/D10/D11 enumerations. C3 adds negative
mutations for schema closure, nonce shape/reuse/chaining, delete/recreate and simulated ID reuse at
path checkpoints, link/reparse/path escape, tool/source/process drift, environment/secret leakage,
unauthorized descendants, broker bypass, kernel denial, publication order, and cleanup target
confusion.

### Completion interpretation

C1 can close #152 after its candidate review and root gate. C2E can unblock C2N only after its
reviewed receipt and remotely reread #162 seal; a provisioned but unsealed guest is not readiness.
C3 can close #162 after its candidate
review and root gate. C4 can close #153 without rerunning pytest because it consumes the immutable
code packet and records observations; any code need returns to C3. C5 closes the phase only when the
status surfaces and external evidence agree with those results and C2E.33 has disposed the runnable
guest lineage while retaining the encrypted run volume under an explicit private-artifact owner and
deadline.
