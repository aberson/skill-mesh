# Phase IS C2E — disposable C2N–C4 driver-test environment

- **Written:** 2026-08-30
- **Status:** PLANNED / NOT AUTHORIZED FOR EXECUTION — this document authorizes no virtual-machine creation, software installation, certificate or App Control change, Secure Boot change, boot-configuration change, reboot, host session, GitHub write, or C2N/C3/C4 action.
- **Owner:** Phase IS completion overlay; preparatory work reports to existing issue #162. Post-C4 disposal is a Phase IS closeout obligation under #143.
- **Unit accounting:** C2E is a runbook stage, not a new Phase IS product unit, issue-sync input, or addition to the fixed 11-unit count.
- **Accepted-contract boundary:** `documentation/instruction-file-symmetry-plan.md` and the frozen `documentation/findings/instruction-file-symmetry-uat.md` remain unchanged by this planning stage.
- **Execution shape:** this plan contains explicit `Type: wait` serialization barriers. After separate
  execution authorization, use the exact bounded invocations in §7; never invoke the whole plan as
  one unattended span. Steps 1–3 and 5–28 are bounded code atoms; Steps 4, 29, 30, and 32 are
  parent-completed waits; Step 31 creates only a local readiness candidate; Step 33 is mandatory
  PASS-or-fail disposition once an environment ID or provider resource exists.

## 1. What This Is

Proposal: `documentation/phase-is-disposable-c2n-c4-environment-proposal.html`

This plan adds the missing disposable Windows security substrate for the remaining Phase IS
completion chain. C2V and C2A are already sealed. A read-only C2N prerequisite probe then proved
that the current workstation has no qualifying Windows Driver Kit (WDK), no qualifying code-signing
identity, and no demonstrated enforced user-mode admission policy. Installing or enabling those
facilities here would change a real workstation's security and boot posture. This plan makes that
machine a coordination surface plus one pinned user-mode emergency-safety build exception and moves
every driver/product-sensitive fact/action to a disposable x64
Windows execution guest while keeping the private test publisher in a separate isolated signer
appliance that never runs candidate code.

The revised dependency chain is:

```text
C2A sealed core-uat-mode resolution
  -> C2E.1–3 evidence verifier, wait protocol, coordinator facts
  -> C2E.4 operator selects/authorizes provider, signer, retention, and emergency routes
  -> C2E.5–12 authenticated provider control, resource, read-only, transfer, and admin planes
  -> C2E.13–18 execution facts, S1, signer isolation, public trust, R0, and canaries
  -> C2E.19–28 rollback, normal/emergency disposition, lifecycle, retention, and absence proof
  -> C2E.29 operator provisions S1, signer appliance, and R0
  -> C2E.30 live rollback/signer-isolation/fresh-context smoke
  -> C2E.31 local reviewed environment-receipt candidate
  -> C2E.32 parent push + #162 seal + status record
  -> C2N guest-local schema/toolchain/admission freeze
  -> C2P coordinator-authored Step-108P build plan
  -> C3 coordinator-controlled implementation; guest-only native/security execution
  -> C4 attended guest-only Step-109 acceptance
  -> C2E.33 dispose/quarantine on PASS or a terminal stop after an environment ID or provider resource exists; retain permitted evidence
  -> C5 phase closeout
```

The current workstation remains the parent coordinator, sole Git integration writer, and sole final
verdict classifier. Fresh Terra producer and reviewer contexts run through the already-supported
Codex `build-step` adapter on this coordinator. They may prepare source in isolated coordinator
worktrees and invoke a narrow, receipt-bound guest connector, but they do not receive guest
infrastructure authority, guest administrator credentials, signing-key access, reviewer authority,
the parent's verdict key, or permission to change this workstation.

The execution guest is not a second source of truth. It supplies machine-local C2N discovery, native
compilation/admission, driver load/unload evidence, and genuine C4 observations. The signer appliance
supplies only exact signing/public-audit facts. Git commits, issue seals, and final verdicts remain
parent-owned.

## 2. Existing Context

### Verified Phase IS checkpoint

| Fact | Immutable evidence |
|---|---|
| Planning base | `4571f7e0c60e49e68ada5ef57ed304ac60bf7542`, clean and synchronized with `origin/main` at planning start |
| C2V | commit `09e7f4d0b740ddfb723dd77682108c3b4405d13e`; #153 seal comment `5460494882` |
| C2A | commit `2f6c7b87dbe68182d2c43c8b1e2faa0a9229817d`; route-resolution blob `14482e5ac6ac550d1e65e511fcfe9b31a18385f6`; #153 seal comment `5464987667` |
| Selected route | `core-uat-mode`; outcome `core-plan-amendment-not-required` |
| Accepted Phase IS plan | blob `6fb9f94f957fca5d3416ffd6dbe6a99ebe6a16e2`, unchanged across C2A |
| Frozen UAT | blob `c285605543f1c3ad02f8ceaf70dac5cb0af37b43`; raw SHA-256 `38A149808F5236D03FBDA41CDE1018A240FEC8E5CC3BF8AEC34BC1C7674A71E5` |
| C2N / C2P / C3 / C4 | not started; a read-only C2N prerequisite probe stopped before repository or remote mutation |

### Why the current workstation cannot qualify

The prerequisite probe found one SDK 26100 candidate, no WDK candidate, Visual Studio product major
18 with MSVC `14.50.35717`, and no time-valid code-signing certificate with a private key in either
personal certificate store. User-mode Code Integrity was off, AppLocker had no rules, Application
Identity was stopped, and non-elevated `CiTool` policy inventory was unavailable. Secure Boot,
virtualization-based security, memory integrity, and kernel Code Integrity were active.

Those facts establish a stop, not an installation checklist for this workstation. C2E therefore
forbids using this workstation as the driver test target and forbids treating a local install of the
missing WDK as sufficient remediation.

Microsoft's current driver-testing guidance describes a distinct test computer, requires disabling
Secure Boot and enabling `TESTSIGNING` for the ordinary test-signing route, and notes that provisioning
can reboot and materially alter the target. Microsoft also pairs Visual Studio 2026 with the 28000
SDK/WDK family. The implementation must re-read these official sources at execution because servicing
revisions can advance:

- <https://learn.microsoft.com/en-us/windows-hardware/drivers/gettingstarted/provision-a-target-computer>
- <https://learn.microsoft.com/en-us/windows-hardware/drivers/download-the-wdk>
- <https://learn.microsoft.com/en-us/windows/apps/windows-sdk/release-notes>
- <https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information>
- <https://learn.microsoft.com/en-us/windows-hardware/drivers/install/the-testsigning-boot-configuration-option>
- <https://learn.microsoft.com/en-us/windows-hardware/drivers/install/installing-a-test-certificate-on-a-test-computer>
- <https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool>
- <https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/design/select-types-of-rules-to-create>

### Authority order

1. `plan.md` owns mutable execution status.
2. `documentation/instruction-file-symmetry-plan.md` owns the accepted Phase IS product contract.
3. `documentation/findings/instruction-file-symmetry-uat.md` owns the frozen C1 evidence and the
   Step-108P/109 packet contract.
4. `documentation/phase-is-completion-plan.md` owns completion-stage ordering.
5. This plan owns only C2E topology, provisioning, readiness, handoff, and disposal.
6. Verified Git objects and remotely reread seal comments outrank stale task-state or issue prose.

If this plan conflicts with either accepted owner in items 2–3, stop. Do not silently amend those
owners. A runbook clarification may explain where an existing requirement executes; it may not
weaken that requirement.

### Terms

- **Coordinator:** this current workstation and its capable Codex parent session. It owns Git
  integration, fresh-context dispatch, parent-private verdict authentication, and status/seal writes.
- **Execution guest:** the disposable x64 Windows virtual machine whose boot, public trust,
  admission-policy, toolchain, driver, and host state are isolated from the coordinator. It never
  contains the test-publisher private key.
- **Signer appliance:** a separate run-scoped, provider-isolated Windows signing appliance that holds
  the non-exportable test-publisher leaf, never runs producer/candidate code, has no route from the
  execution guest, and accepts only exact hash-bound parent grants through its closed connector.
- **Infrastructure controller:** the provider-specific control plane that creates, snapshots,
  reverts, powers off, and destroys the guest. Its locator and credentials never enter Git.
- **Provider resource:** any run/environment-tagged compute, storage, network, policy, connector,
  lifecycle, signer, guest, snapshot, or secret-injection object created after `environment_id`.
  Selection-plane keys, journals, store namespaces, and authorizations created under `c2e_run_id`
  before that point are not environment resources; §5.6 `pre-resource-closure` retires them.
- **Connector:** a provider-neutral command surface through which the coordinator can execute an
  allowlisted guest command and transfer a content-addressed payload without a shared filesystem.
- **Bootstrap descriptor:** immutable private pre-resource record containing `c2e_run_id`, the future
  `environment_id`, provider/resource-spec/tag/policy digests, authority public-key/scope digests,
  lifecycle maxima, exact emergency launcher/manifest/broker binding, journal/store references, and coordinator exclusion digest. It
  contains no provider-returned resource locator and is sealed before the first resource.
- **Resource inventory journal:** external encrypted transactional append-only record whose entries
  bind every provider request/result/reread and every created/discovered/disposed environment-tagged
  resource. The emergency broker can recover complete inventory from the immutable bootstrap tag and
  this journal even after partial provisioning.
- **S1:** powered-off toolchain baseline before the run-specific publisher, policy, test-signing
  state, source clone, or credentials exist.
- **R0:** powered-off, admission-ready snapshot descended from S1 for one Phase IS run.
- **Run descendant:** the only writable guest derived from R0. Producer, reviewer, certification,
  and attended uses are serialized under a provider control-plane lease; only one writable descendant
  may exist or run at a time.
- **Run volume:** one encrypted guest virtual block volume on which C4 creates a single common parent
  and all four direct-child roots: combined install-home/project, config, build, and
  `<evidence-export>`. The export root is not a separate volume, mount point, reparse point, or C4
  cleanup target. Because deleted private-root bytes may remain in block slack, the retained volume is
  classified as a private secure artifact even though the live export root contains only redacted
  artifacts.

## 3. Scope

### In scope

- A provider-neutral environment descriptor, strict readiness receipt, validator, planted-negative
  fixtures, and redaction contract.
- One x64 Windows execution guest for C2N discovery, C3 native/security execution, and C4 attended
  acceptance, plus one isolated run-scoped signer appliance that never executes candidate code.
- Execution-guest-only Visual Studio/MSVC, matching Windows SDK/WDK, enforced App Control policy,
  kernel test signing, reboot, driver load/unload, and host state; signer-appliance-only private
  test-publisher identity.
- A concrete provider adapter implementing an authenticated, anti-replay, content-addressed connector
  with no shared folder, drive redirection, clipboard transfer, or ambient private-network route.
- S1/R0 snapshot lineage, one-writable-descendant serialization, rollback, reboot, and drift rules.
- Parent-controlled single-use guest-elevation/signing grants, isolated signer-appliance key custody, parent-only
  Git integration and verdict classification, fresh Terra
  producer/reviewer separation, and a live non-mutating acceptance probe.
- C2N manifest binding to the environment receipt, C2P/C3/C4 guest/coordinator ownership, and C5
  disposal plus durable-evidence retention.

### Out of scope

- Any change to this workstation's certificate stores, App Control/Code Integrity/AppLocker policy,
  Secure Boot, BCD/boot configuration, firmware, Windows features, services, SDK/WDK, or installed
  host applications.
- Provisioning or mutating any guest during this planning run.
- Selecting or purchasing a cloud, hypervisor, Windows license, or artifact service during this
  planning run. C2E.4 is an explicit future operator gate that selects and authorizes one concrete
  provider/retention route before any provider adapter or guest is built.
- Modifying the accepted Phase IS plan or frozen UAT.
- Implementing Step 108P containment, filling UAT observations, starting Claude/Codex host sessions,
  or beginning C2N/C2P/C3/C4.
- Production driver signing, Hardware Lab Kit certification, Partner Center submission, or deployment
  to any non-disposable machine.
- Treating App Control as proof of argument, environment, descendant, I/O, or handle continuity. It
  supplies only pre-entry image admission; the Step-108P broker/kernel rail still owns the rest.

## 4. Impact Analysis

| File or surface | Change | Reason |
|---|---|---|
| `documentation/phase-is-disposable-c2n-c4-environment-plan.md` | create now | Canonical C2E environment and handoff plan |
| `documentation/phase-is-disposable-c2n-c4-environment-proposal.html` | create during plan-redline | Print-faithful operator view of this plan |
| `documentation/phase-is-completion-plan.md` | amend now | Insert C2E, assign guest/coordinator ownership, resolve publisher-vs-future-hash sequencing, and add disposal |
| `plan.md` | amend now | Reconcile sealed C2V/C2A state and point the next action at planned C2E rather than workstation-local C2N |
| `documentation/instruction-file-symmetry-plan.md` | no change | C2A sealed the core route with this blob byte-identical; environment work does not change the accepted product contract |
| `documentation/findings/instruction-file-symmetry-uat.md` | no change | Frozen through C2E/C2N/C2P; C3 alone replaces already-authorized blockers while preserving blank observations |
| `tools/phase_is_environment.py` and `tools/phase-is-environment/**` | create in Steps 1–3 and 5–28 | Strict CLI/schemas/verifier, wait materializer/selector, coordinator fact collector, concrete provider adapter, guest facts/baseline/trust/lifecycle/disposition/retention actions, emergency bundle, canaries, and redaction |
| `tests/phase-is-environment/**` | create in Steps 1–3 and 5–28 | Schema, safety-interlock, planted-negative, coordinator non-mutation, connector/auth/replay/lease, policy, snapshot, rollback, disposition, retention, and redaction coverage |
| `documentation/findings/phase-is-c2e-environment.json` | create in Step 31 | Redacted committed readiness receipt consumed as a C2N existing input |
| `tools/phase-is-uat/**`, `tests/phase-is-uat/**` | no C2E change | Remain owned by C2N/C3 and the future C2P subplan |
| generated manifest/inventory files | gate only | Run the generator after documentation changes; correct result is no generated diff because these paths are not catalog inputs |
| issues #162/#143 | future seal/status only | No new issue or Phase IS unit; no remote write occurs during planning |

## 5. New Components and Contracts

### 5.0 Common canonical-byte and RSA proof profile

Every use of **canonical JSON** in C2E means this exact byte transform. Decode with strict UTF-8 and
reject a BOM, malformed UTF-8, lone surrogate, duplicate object name before object materialization,
or any value outside I-JSON. Canonical encoding is a byte transform, not a schema-validity verdict.
Every JSON number is a
nonnegative integer from `0` through `9007199254740991`; a field declared positive starts at `1`.
Floating-point values, negative zero, exponent-form input, `NaN`, and infinities are invalid. Apply
RFC 8785 JSON Canonicalization Scheme (JCS) recursively, preserving array order and preserving Unicode
code points without normalization, then append exactly one `0x0A` byte. The JCS output plus that LF is
the C2E canonical-encoding byte string. A closed artifact is a valid C2E artifact only when it also
passes its named schema and byte-equals a reserialization; parsing and re-emitting a noncanonical
input does not make it acceptable. The routable-envelope exception below intentionally computes proof
bytes before the operation-tagged parameter union is validated; those bytes are canonical-encoded but
do not claim the request is schema-valid. Arrays that represent sets
must also satisfy their field-specific sort/uniqueness rule before JCS. Step 1 supplies cross-runtime
golden vectors for escapes, non-ASCII names/values, ordering, the `2^53-1` boundary, and rejection of
duplicates, invalid Unicode, fractions, exponent input, and `2^53` or larger integers.
Every materialized `*_utc` value is a string in whole-second `YYYY-MM-DDTHH:MM:SSZ` form; a
provider's higher-precision raw timestamp remains in the private hashed provider evidence and is
normalized toward the earlier second for deadlines or expiry checks.

The connector has a deliberately smaller **routable-envelope gate** before the connector-result
contract. Raw input must first be strict UTF-8, contain one canonical JCS-plus-LF JSON object, and
contain the exact outer request property set with schema, all typed identity/sequence/time/nullable
echo fields, one known role and operation, and one syntactically closed authenticator tag plus routing
key identity. This gate does not validate the operation-tagged `parameters` body or authenticate its
proof. If raw input fails that gate—or names no resolvable response authority—the transport returns
an empty, fixed provider-adapter rejection and closes. It emits no connector-result object, echoes no
request value, selects no action, and changes no state. The adapter may retain only the raw-byte
SHA-256 and fixed reason `PREPARSE_REJECTED` in its private rate-limited intake audit; that reason is
not a connector status or an execution input.

For a passing outer gate, `routable_request_bytes` is the exact received complete request bytes,
including `authenticator`; the canonical-byte equality check makes it identical to the §5.0
canonical encoding even when `parameters` later fails its tagged union. `routable_payload_bytes` is
the §5.0 canonical encoding of every outer property except `authenticator`, again without asserting
operation-parameter validity. These are the only pre-union proof/hash inputs. The request's
`canonical_payload_sha256` and request proof use `routable_payload_bytes`; `request_sha256` uses
`routable_request_bytes`. If the authenticated parameter union passes, those same bytes become the
complete valid C2E request bytes; no parse-and-reemit or second canonicalization is permitted.

Every C2E RSA proof authority—control receipt, wait result, emergency broker, retention verifier,
publication broker, admin grant, and signed private artifact—uses an exact RSA-3072 public key with
exponent `65537`. Its public identity is the lowercase hexadecimal SHA-256 of canonical DER
`SubjectPublicKeyInfo` using `rsaEncryption` OID `1.2.840.113549.1.1.1` with explicit NULL parameters,
minimal DER INTEGER encodings, and no trailing bytes; PKCS#1-only, alternate-parameter, nonminimal,
wrong-size, and wrong-exponent encodings are rejected. Every RSA signature uses RSA-PSS with SHA-256,
MGF1-SHA-256, a 32-octet salt, trailer field `0xbc`, and unpadded base64url output. The connector and
admin grant use their dedicated inputs below.

Every other closed signed C2E object names one ASCII domain and uses this signed-object profile.
Its `authenticator` contains exactly `algorithm=RSA-PSS-SHA256`, `public_key_sha256`,
`canonical_payload_sha256`, and unpadded-base64url `signature`. `signed_payload_bytes` is the C2E
canonical JSON of every top-level property except `authenticator`; `canonical_payload_sha256` is the
lowercase hexadecimal SHA-256 of those bytes. `authenticator_metadata_bytes` is the C2E canonical
JSON of the authenticator without `signature`. The exact signature input is
`ASCII(domain) || 0x00 || uint64be(length(signed_payload_bytes)) || signed_payload_bytes ||
uint64be(length(authenticator_metadata_bytes)) || authenticator_metadata_bytes`, with unsigned
eight-byte big-endian lengths. Verification recomputes both byte strings and the declared hash, uses
the externally expected public key rather than trusting the embedded digest, and rejects a wrong
domain, key profile, metadata field, encoding, or extra property.

### 5.1 Provider-neutral topology

The environment has one licensed or evaluation Windows 11 Enterprise x64 execution guest with UEFI
firmware, an OS/build virtual disk, one provider-encrypted run volume, and an outbound-only network
path, plus one separately isolated run-scoped Windows signer appliance. The execution-guest baseline
allocation is 4 virtual CPUs, 16 GiB RAM, 160 GiB OS disk, and 32 GiB run volume; the execution
provider may increase those values but may not reduce them without a recorded resource probe showing
the full root gate and native toolchain remain viable. The signer appliance is separately sized by
the selected adapter and never hosts source, builds, tests, or a reusable snapshot. C4 creates the
accepted UAT's one common parent and all four direct-child roots on the execution run volume. No
child is a volume root, mount point, junction, symlink, or other reparse topology.

The guest has no host-shared folder, host-mounted path, enhanced-session drive, clipboard/file
transfer, USB/device pass-through, bridged adapter, host-only adapter, SMB/NFS/WebDAV transfer, or
route to the coordinator or another private network. An outbound HTTPS path may reach only the exact
source remote, pinned tool installers, Claude/Codex endpoints needed by C4, the fixed external
publication-broker endpoint, and the provider connector endpoint. Direct GitHub API access is denied;
the source remote permits only unauthenticated/read-only exact-object fetch. The descriptor records the allowlist digest, not credentials or
private endpoints.

The coordinator never mounts a guest disk. C2E.4 selects one provider, and C2E.5–7 implement that
provider's adapter for exactly `qualify`, `lease-acquire`, `lease-renew`, `lease-release`, `inventory`,
`resource-create`, `volume-attach`, `lifecycle-rule`, `facts`, `exec-readonly`, `exec-admin`, `put`,
`get`, `power`, `snapshot`, and `destroy`.
`exec-admin` accepts only an `action_id` from the committed action allowlist; it never accepts command
text, a shell fragment, wildcard, or unresolved path. `put` and `get` require declared byte count and
SHA-256. The provider must expose complete environment-scoped resource/artifact enumeration and an
atomic conditional environment lease; absence of either blocks qualification.

Every connector request is canonical JSON with exactly `schema`, `c2e_run_id`, 256-bit random
`session_id`, 256-bit random `request_id`, positive monotonic `sequence`, `issued_utc`, `expires_utc`
no more than five minutes later, caller `role`, `operation`, nullable `environment_id` (null only for
`qualify` or emergency-broker read-only `inventory:pre-resource-run`),
nullable opaque `guest_id_sha256`, nullable `lease_id`, nullable `expected_state_sha256`, one closed
operation-tagged `parameters` object, and `authenticator`. Every object has
`additionalProperties=false`.

The common response is closed JSON with exactly `schema=skill-mesh/phase-is-c2e-connector-result/v1`,
`request_sha256`, `c2e_run_id`, `session_id`, `request_id`, `sequence`, nullable `environment_id`,
nullable `guest_id_sha256`, nullable `lease_id`, `operation`, `status`, nullable
`before_state_sha256`, nullable `after_state_sha256`, nullable `provider_lease_sha256`, nullable
`complete_environment_inventory_sha256`, nullable operation-tagged `result`, `started_utc`,
`ended_utc`, and `authenticator`; every nested object has `additionalProperties=false`.
`request_sha256` is the lowercase hexadecimal SHA-256 of exact `routable_request_bytes`, including
the authenticator and proof. The run/session/request/sequence/environment/guest/lease and
operation fields exactly echo the request, including nulls. UTC values use whole-second
`YYYY-MM-DDTHH:MM:SSZ`, and `ended_utc` is not earlier than `started_utc`.

A connector result exists only after the routable-envelope gate has supplied every mandatory echo,
the exact canonical request bytes, and a response authority. The connector then verifies the request
proof before validating the closed operation-tagged `parameters` union. A validly authenticated
routable envelope whose parameters violate that union receives authenticated `INVALID_SCHEMA`; an
invalid proof receives authenticated `AUTH_FAILED`; neither reaches an action. Unknown/malformed
outer fields, identifiers, roles, operations, authenticator tags/routing identities, or noncanonical
bytes are preparse transport rejections and can never be represented as `INVALID_SCHEMA`.

`status` is exactly one value from the closed vocabulary below. On `OK`, `result` is the exact
operation result defined below, `before_state_sha256` equals non-null request
`expected_state_sha256` or is null with it, and `after_state_sha256` is non-null whenever
`environment_id` is non-null; the only successful null-state cases are `qualify` and
`inventory:pre-resource-run`. `provider_lease_sha256` is null when no lease exists, hashes the newly
acquired lease for successful `lease-acquire`, and otherwise hashes the echoed non-null lease.
`complete_environment_inventory_sha256` is null only for successful `qualify` and is required for
every other successful operation; any duplicate state/lease/inventory digest inside `result` must
match its common field. On any non-`OK` status, `result` is null. A failure proven before effect has
`after_state_sha256` equal to `before_state_sha256`; `PROVIDER_FAILURE` or
`DISPOSITION_INCOMPLETE` may instead make after-state, lease, or inventory digests null, but such a
response enters mandatory reconciliation and can never advance state.

The request `authenticator` is a closed tagged union. Provider-control requests contain exactly
`kind=provider-control-request`, `control_public_key_sha256`,
`provider_authorization_context_sha256`, `canonical_payload_sha256`, and RSA-PSS-SHA-256 `signature`;
the provider credential remains only in the authenticated HTTPS sideband and the context digest binds
its provider-returned principal/scope/expiry facts, never the token. Guest-data requests contain
exactly `kind=guest-connector-hmac`, `key_id_sha256`, `canonical_payload_sha256`, and `mac_hex`.
Later absence-only requests contain exactly `kind=retention-verification-request`,
`public_key_sha256`, `readonly_identity_scope_sha256`, `canonical_payload_sha256`, and
RSA-PSS-SHA-256 `signature`. Direct safety requests contain exactly
`kind=emergency-broker-request`, `broker_public_key_sha256`, `launcher_identity_sha256`,
`broker_attestation_sha256`, `provider_authorization_context_sha256`, `canonical_payload_sha256`,
and RSA-PSS-SHA-256 `signature`; the external broker creates this single-use attestation only after
the Step-21 launcher/manifest/environment checks and releases the short-lived emergency provider
authorization only in the authenticated transport sideband.

For every request variant, `routable_payload_bytes` is the §5.0 canonical encoding of every outer
request property except `authenticator`, computed after only the routable-envelope gate;
`canonical_payload_sha256` is the lowercase hexadecimal SHA-256 of those exact bytes. Request
`authenticator_metadata_bytes` is C2E-canonical JSON of every authenticator property
except its proof field (`signature` for RSA variants or `mac_hex` for the HMAC variant), so it includes
the `kind`, key/context identities, and `canonical_payload_sha256` without including the proof itself.
The exact request proof input is
`ASCII("skill-mesh/phase-is-c2e-connector-auth/v1") || 0x00 || ASCII("request") || 0x00 ||
ASCII(kind) || 0x00 || uint64be(length(routable_payload_bytes)) || routable_payload_bytes ||
uint64be(length(authenticator_metadata_bytes)) || authenticator_metadata_bytes`, where each length is
an unsigned eight-byte big-endian integer. RSA request variants encode `signature` as unpadded
base64url RSA-PSS using SHA-256, MGF1-SHA-256, and a 32-octet salt over that exact input; the HMAC
variant encodes `mac_hex` as 64 lowercase hexadecimal characters from HMAC-SHA-256 over that exact
input. Verification recomputes the payload hash and both canonical byte strings before checking the
proof, and rejects a wrong direction, kind, metadata field, hash, length, proof encoding, or outer
request field before any action. No authentication sideband may carry an admin grant: `exec-admin`
embeds the complete signed grant in its closed parameters object so schema, signature, hash, and
one-time consumption are inseparable.

The tagged parameter/result union is operation-complete:

| Operation | Required parameters and context | Forbidden | Privilege and exact effect | Required result |
|---|---|---|---|---|
| `qualify` | `{}`; provider identity; no guest/lease/state | every target, action, content, and path field | parent control-plane read only; no resource change | capability, auth, retention, lease, and inventory-guarantee digests |
| `lease-acquire` | `{ttl_seconds}` plus environment; no existing lease; expected complete-environment state | action/content/path/snapshot fields | parent control-plane, or emergency-broker plane only for terminal safety; atomically acquire the environment namespace only if no competing holder or unlisted artifact violates policy | opaque lease ID, expiry, holder digest, complete inventory digest |
| `lease-renew` | `{ttl_seconds}` plus environment, active lease, expected complete-environment state | action/content/path/snapshot fields | parent control-plane, or emergency-broker plane only for its same cleanup lease; atomically renew only the same lease holder after complete inventory and lifecycle-deadline checks | unchanged opaque lease ID, new expiry no more than 30 minutes after success and never beyond the absolute lineage deadline, complete inventory digest |
| `lease-release` | `{}` plus environment, active lease, expected complete-environment state | action/content/path/snapshot fields | parent control-plane or emergency-broker cleanup plane; release only after required inventory/disposition check | released lease digest and complete inventory digest |
| `inventory` | `{inventory_scope}` where scope is `complete-environment` plus environment and active lease; `pre-resource-run` instead requires null environment, no lease, exact `c2e_run_id` tag, and expected empty inventory; `pre-resource-environment` requires the atomically committed environment/bootstrap/journal binding, no lease, and expected empty inventory; later `retention-absence` uses the bound read-only retention identity without a lease | action/content/path/snapshot fields | parent control-plane for complete inventory, emergency-broker read-only access only for the two pre-resource scopes or terminal cleanup, or retention-verification read only for absence | canonical exhaustive inventory of every tagged execution guest/descendant, signer appliance, snapshot, disk, volume, attachment, network/policy object, connector/secret-injection object, lifecycle rule, and other provider artifact, plus digest; both pre-resource scopes must return exactly empty and make no mutation |
| `resource-create` | `{resource_kind, resource_spec_id, inputs_sha256}` where kind is a committed enum plus environment, active lease, expected state | provider-native free-form configuration, path, URL, wildcard, implicit resource | parent control-plane; create exactly one descriptor-declared execution guest, signer appliance, OS disk, run volume, network/policy, connector-route, or secret-injection object | opaque resource ID hash, kind/spec/hash, provider creation time, exact after-state, complete inventory digest |
| `volume-attach` | `{verb, run_volume_id_sha256}` where verb is `attach` or `detach` plus environment, guest, active lease, expected state | path, device guess, wildcard, implicit volume | parent control-plane; one exact provider attachment transition | attachment identity/hash, observed guest/volume binding, exact after-state, complete inventory digest |
| `lifecycle-rule` | `{verb, rule_spec_sha256, target_inventory_sha256, transition}` where verb is `arm-active`, `verify-active`, `transition-pass-retention`, `arm-failure-quarantine`, `shorten-c5`, or `verify-absent`; `transition` is the matching closed verb-tagged proof object below for the three transition verbs and null for the other three; environment and expected state required; active lease required except `shorten-c5` and `verify-absent` | deadline extension/reset/pause/disable except the exact one-way PASS reclassification below, arbitrary rule text, undeclared target, wrong transition tag, or caller-chosen timestamp/deadline | parent control-plane for `arm-active`, read-only `verify-active`, and PASS transition; emergency-broker plane only for `arm-failure-quarantine` under the proof-bound equal-or-earlier deadline; a newly minted parent-only C5-shortener identity only for `shorten-c5`; bound retention-verification identity for read-only `verify-absent`; create/shorten/reread the declared rule, perform the one allowed atomic PASS transition, or prove all bound targets/rules absent | rule identity/hash, provider clock/deadline, affected inventory, independent reread, exact state; each transition returns old/new rule IDs plus its atomic transaction ID; verification returns only the declared closed result |
| `facts` | `{fact_set}` where the value is a committed enum plus guest, lease, expected state | action/content/path fields | guest standard-user read only | canonical fact object, output manifest, and unchanged-state proof |
| `exec-readonly` | `{action_id, inputs_sha256}` where `action_id` is a committed read-only enum plus guest, lease, expected state | command text, executable path, output path, admin grant | guest standard-user allowlisted action only | action receipt, output manifest, and unchanged-state proof |
| `exec-admin` | `{action_id, inputs_sha256, grant}` where `action_id` is a committed admin enum and `grant` is the exact closed `admin-grant-v1` object plus guest, lease, expected state | command text, executable/output path, wildcard, grant sideband, reusable grant | verify the embedded single-use parent signature, then execute exactly one pre-authored guest-admin transition | action/grant SHA-256 receipt, output manifest, and exact after-state digest |
| `put` | `{object_sha256, object_size, destination_id}` where `destination_id` is a committed logical root/object enum plus guest, lease, expected state | source/destination path, wildcard, overwrite without matching prior object | content-addressed transfer into the declared logical destination | stored object identity/size/hash and exact after-state digest |
| `get` | `{object_id, expected_sha256, expected_size}` where `object_id` is a receipt-issued logical ID plus guest, lease, expected state | source/destination path, wildcard, undeclared object | read-only content-addressed return of exactly one prior output | returned object identity/size/hash and unchanged-state proof |
| `power` | `{desired_state}` where value is `on`, `off`, or `reboot` plus guest, lease, expected state | action/content/path/snapshot fields | parent control-plane for any declared transition; emergency-broker plane only when `desired_state=off` | observed power state, boot generation, and after-state digest |
| `snapshot` | `{verb, snapshot_role, snapshot_id_sha256}` where verb is `create`, `restore`, or `delete`, role is a committed enum, and snapshot ID is required only for restore/delete; plus guest, lease, expected state | action/content/path fields | parent control-plane; one exact lineage transition after quiescence | snapshot/lineage digest, power state, complete inventory digest, new connector-session-required flag |
| `destroy` | `{target_kind, target_id_sha256}` where kind is one exact inventory kind, including execution guest, signer appliance, snapshot, OS disk, run volume, attachment, network/policy, connector-route, secret-injection object, or lifecycle rule; plus environment, active lease, expected state | path, wildcard, implicit descendants, preserve flag | parent control-plane or emergency-broker cleanup plane; destroy exactly one named opaque resource after separate complete inventory; caller must iterate every target explicitly | deletion receipt, absent-target proof, remaining complete inventory digest |

On `OK`, `result` has exactly the property set below; fields not named for that variant are absent.
All `*_sha256` values are 64 lowercase hexadecimal characters, all sizes/counts/generations obey
§5.0's safe-integer rule, and all state/lease/inventory digests duplicated in the common response must
match it byte-for-byte.

| Operation / result variant | Exact `result` properties |
|---|---|
| `qualify` | `capability_sha256`, `auth_sha256`, `retention_sha256`, `lease_guarantee_sha256`, `inventory_guarantee_sha256` |
| `lease-acquire` | `lease_id`, `lease_expires_utc`, `holder_sha256`, `complete_environment_inventory_sha256` |
| `lease-renew` | `lease_id`, `lease_expires_utc`, `holder_sha256`, `complete_environment_inventory_sha256` |
| `lease-release` | `released_lease_sha256`, `complete_environment_inventory_sha256` |
| `inventory` | `inventory_scope`, `inventory_manifest_sha256`, `inventory_count`, `inventory_empty`, `complete_environment_inventory_sha256`; the private manifest is a C2E-canonical array sorted by `(resource_kind, resource_id_sha256)` whose closed entries contain exactly `resource_kind`, `resource_id_sha256`, `resource_state`, nullable `parent_id_sha256`, and `provider_fact_sha256` |
| `resource-create` | `resource_id_sha256`, `resource_kind`, `resource_spec_sha256`, `provider_created_utc`, `after_state_sha256`, `complete_environment_inventory_sha256` |
| `volume-attach` | `verb`, `attachment_id_sha256`, `run_volume_id_sha256`, `guest_id_sha256`, `after_state_sha256`, `complete_environment_inventory_sha256` |
| `facts` | `fact_set`, `fact_object_sha256`, `output_manifest_sha256`, `unchanged_state_sha256` |
| `exec-readonly` | `action_id`, `action_receipt_sha256`, `output_manifest_sha256`, `unchanged_state_sha256` |
| `exec-admin` | `action_id`, `action_receipt_sha256`, `grant_sha256`, `output_manifest_sha256`, `after_state_sha256` |
| `put` | `object_id`, `object_sha256`, `object_size`, `after_state_sha256` |
| `get` | `object_id`, `object_sha256`, `object_size`, `unchanged_state_sha256` |
| `power` | `observed_state`, `boot_generation`, `after_state_sha256`, `complete_environment_inventory_sha256` |
| `snapshot` | `verb`, `snapshot_role`, `snapshot_id_sha256`, `lineage_sha256`, `power_state`, `complete_environment_inventory_sha256`, `new_connector_session_required` |
| `destroy` | `target_kind`, `target_id_sha256`, `deletion_receipt_sha256`, `absent_target_sha256`, `remaining_complete_environment_inventory_sha256` |
| `lifecycle-rule:arm-active` or `verify-active` | `verb`, `rule_id_sha256`, `rule_sha256`, `provider_utc`, `deadline_utc`, `affected_inventory_sha256`, `independent_reread_sha256`, `after_state_sha256` |
| `lifecycle-rule:transition-pass-retention`, `arm-failure-quarantine`, or `shorten-c5` | `verb`, `old_rule_id_sha256`, `old_rule_sha256`, `new_rule_id_sha256`, `new_rule_sha256`, `provider_utc`, `new_deadline_utc`, `affected_inventory_sha256`, `transaction_id_sha256`, `independent_reread_sha256`, `after_state_sha256` |
| `lifecycle-rule:verify-absent` | `verb`, `target_inventory_sha256`, `absence_receipt_sha256`, `provider_utc`, `independent_reread_sha256`, `after_state_sha256` |

Fields shown as forbidden do not exist as nullable escape hatches: after the routable-envelope gate,
the request proof is verified and the operation-tagged parameter schema is validated before any
action. Logical IDs/specs come only from the private descriptor, committed closed
enums, or a prior authenticated receipt. No operation accepts arbitrary command text, provider
configuration, a filesystem path, a URL, an implicit target, or an operation-specific field not named
in its row. Every authenticated invalid parameter combination receives the stable closed
`INVALID_SCHEMA` result before its first effect; raw/outer-envelope failures use only the fixed
transport rejection above.

`transition-pass-retention` is the sole v1 operation allowed to replace an earlier deletion deadline
with a later one. Its `transition` object contains exactly `schema=skill-mesh/phase-is-c2e-pass-
transition/v1`, `old_active_rule_id_sha256`, `old_active_rule_sha256`, `old_active_deadline_utc`,
`c4_pass_commit`, `c4_pass_tree`, `c4_pass_uat_blob`, `c4_pass_created_utc`,
`c4_pass_verdict_sha256`, `c4_evidence_issue` (exactly `153`), `c4_evidence_comment_id`,
`c4_evidence_body_sha256`, `c4_cleanup_issue` (exactly `153`), `c4_cleanup_comment_id`,
`c4_cleanup_body_sha256`, `detached_run_volume_id_sha256`,
`pre_transition_inventory_sha256`, `new_retention_rule_sha256`, and
`new_retention_deadline_utc`. The new deadline is exactly C4 PASS `created_utc` plus 120 days; it is
neither caller-chosen nor later extendable. The two comment bindings are the already-published C4
pre-disposition evidence/cleanup records on #153, never the future Step-33 #143 disposition marker.
One provider transaction must verify the remotely reread origin commit/tree/UAT blob plus those C4
PASS/cleanup proofs, destroy every runnable/signer/snapshot/OS/attachment/connector target, detach
the exact encrypted run volume, remove the old active rule, and arm the new rule against only that
volume. The response binds old/new rule identities, transaction ID, detached-volume state, complete
after-inventory, and independent reread. Replaying the same request/idempotency key returns the same
transaction; a changed proof/target/deadline or partial/non-atomic provider result blocks and falls
back to immediate volume destruction. This exception never resets or extends any runnable-lineage
clock and cannot be used for failure quarantine, an attached volume, or a non-PASS run.

`arm-failure-quarantine` has exactly `schema=skill-mesh/phase-is-c2e-failure-quarantine-
transition/v1`, `terminal_stop_receipt_sha256`, `terminal_stop_utc`, `original_failure_sha256`,
`old_active_rule_id_sha256`, `old_active_rule_sha256`, `old_active_deadline_utc`,
`pre_transition_inventory_sha256`, `new_quarantine_rule_sha256`, and
`new_quarantine_deadline_utc`. The terminal-stop receipt is the immutable earliest terminal-entry
record for the environment from the external control or emergency-broker journal and binds the
provider clock; a caller timestamp is never accepted. The new deadline is exactly the earlier of
that `terminal_stop_utc` plus seven days or the old active deadline. Identical replay is idempotent;
any changed receipt, timestamp, proof, rule, target, or deadline fails before mutation and cannot
restart the seven-day clock.

`shorten-c5` has exactly `schema=skill-mesh/phase-is-c2e-c5-shorten-transition/v1`,
`c4_pass_transition_receipt_sha256`, `c4_disposition_wait_result_sha256`,
`c4_disposition_comment_id`, `c4_disposition_body_sha256`, `c5_closeout_candidate_commit`,
`c5_closeout_candidate_tree`, `c5_shortening_intent_sha256`,
`c5_shortening_authorized_utc`, `old_retention_rule_id_sha256`,
`old_retention_rule_sha256`, `old_retention_deadline_utc`,
`pre_transition_inventory_sha256`, `new_retention_rule_sha256`, and
`new_retention_deadline_utc`. Before this request, the parent pushes and remotely rereads an
immutable reviewed C5 closeout candidate that still says retention shortening is pending, then signs
one private canonical shortening intent with the surviving control-receipt key. The intent time is
fixed before the provider call; the new deadline is exactly the earlier of that time plus 90 days or
the old C4-plus-120-day hard cap. The request is legal only through the one-hour parent-only identity
described below, against the exact detached volume and old rule. Identical replay is idempotent; any
changed proof, candidate, intent, rule, target, timestamp, or deadline fails before mutation. The
final C5 status/issue closeout is a later status-only change that binds the verified shortening
receipt, so the deadline calculation is not circular.

The private C5 shortening intent is a closed
`skill-mesh/phase-is-c2e-c5-shortening-intent/v1` object with exactly `schema`, `c2e_run_id`,
`environment_id`, `c4_pass_transition_receipt_sha256`, `c4_disposition_wait_result_sha256`,
`c4_disposition_comment_id`, `c4_disposition_body_sha256`, `c5_closeout_candidate_commit`,
`c5_closeout_candidate_tree`, `retained_run_volume_sha256`, `old_retention_rule_id_sha256`,
`old_retention_rule_sha256`, `old_retention_deadline_utc`, `created_utc`,
`authorized_deadline_utc`, and `authenticator`; `additionalProperties=false`.
`authorized_deadline_utc` is already the exact earlier of `created_utc` plus 90 days or the old hard
cap. `authenticator` uses the surviving control-receipt key and the §5.0 signed-object profile with
domain `skill-mesh/phase-is-c2e-c5-shortening-intent-signature/v1`.
`c5_shortening_intent_sha256` is the raw-file SHA-256 of that complete signed canonical object.

The connector status vocabulary is exactly `OK`, `INVALID_SCHEMA`, `AUTH_FAILED`, `EXPIRED`,
`REPLAY_OR_SEQUENCE`, `ROLE_DENIED`, `HOST_IDENTITY_MISMATCH`, `LEASE_CONFLICT`,
`INVENTORY_INCOMPLETE`, `STATE_MISMATCH`, `ACTION_DENIED`, `CONTENT_MISMATCH`,
`RETENTION_UNAVAILABLE`, `PROVIDER_FAILURE`, and `DISPOSITION_INCOMPLETE`. No provider-native error
string is promoted to a success or new public code; it is hashed into private evidence and mapped to
one closed value. `PREPARSE_REJECTED` is intentionally outside this vocabulary and never appears in a
connector-result object.

Security-binding identifiers are fixed before implementation:

| Identifier | Format and generator | Scope / reuse | Consumers |
|---|---|---|---|
| `environment_id` | `c2e-` plus 32 lowercase hexadecimal characters from 128 CSPRNG bits generated once by the parent immediately before C2E.29 and before the bootstrap descriptor is sealed | one attempted/provisioned lineage; never reused, including after partial provisioning or abort | bootstrap/final descriptor, resource journal, every post-selection wait/readiness/disposition record, C2N/C3/C4 locks |
| `c2e_run_id` | `c2e-run-` plus 32 lowercase hexadecimal characters from 128 parent CSPRNG bits generated before C2E.4 | one provider-selection-through-disposition execution; never reused | pre-environment control scope, external journals/keys, every request/wait/readiness/disposition record |
| `session_id` | 64 lowercase hexadecimal characters from 256 CSPRNG bits; parent generates control/retention sessions and parent+guest establish guest sessions | exactly one authenticator-plane epoch; control rotates only after crash reconciliation/key rotation, guest rotates after every restore/restart, retention rotates per absence attempt; never reused | request/result, replay journal, admin grant |
| `request_id` | 64 lowercase hexadecimal characters from 256 parent CSPRNG bits | one request globally within the environment; never reused | request/result/replay store |
| `wait_result_id` | 64 lowercase hexadecimal characters from 256 parent CSPRNG bits | one materialized wait result; never reused | private wait record, remote marker/status digest |
| `guest_id_sha256` | lowercase 64-hex SHA-256 of canonical UTF-8 `environment_id + NUL + provider_adapter_key + NUL + opaque_provider_resource_id` | private per guest resource; opaque provider ID is never published | descriptor and connector requests/results |
| `snapshot_id_sha256` | lowercase 64-hex SHA-256 of canonical UTF-8 `environment_id + NUL + opaque_provider_snapshot_id` | private per snapshot; never used as a provider locator | descriptor, snapshot request/result, lineage inventory |
| `lease_id` | provider-issued 128–256-bit opaque value encoded unpadded base64url (`^[A-Za-z0-9_-]{22,43}$`) | one atomic acquisition chain; same holder may renew the unchanged ID while unexpired, each expiry is at most 30 minutes after success and never past the lineage deadline; never reused after release/expiry | control/guest requests, grants, receipts; only its SHA-256 may be public |
| `grant_id` | 64 lowercase hexadecimal characters from 256 parent CSPRNG bits | one admin action; consumed exactly once | signed grant and privileged-verifier replay store |
| `grant_sequence` | positive JCS-safe integer from `1` through `9007199254740991`, increasing by exactly one | one ephemeral post-restore grant-key session | grant and privileged-verifier replay store |
| `provider_adapter_key` | lowercase slug matching `^[a-z0-9]+(?:-[a-z0-9]+)*$` selected at C2E.4 | one public adapter implementation; changes require a new provider-selection result | adapter path, descriptor, wait/status markers |
| `action_id`, `destination_id`, `object_id` | exact committed enum or receipt-issued 64-hex content identity; never caller-created path text | one schema/version or prior authenticated output | tagged operation parameters/results |

All CSPRNG values use the parent operating system's cryptographic random source. Request `sequence`
and `grant_sequence` use §5.0's positive JCS-safe range and reject zero, exhaustion, skips, and reuse;
a session/key epoch must rotate before the maximum. Canonical hash inputs include the literal NUL separators shown;
identifiers never derive from machine/user names, filesystem paths, timestamps, or child-model text.

Control replay/idempotency state is not workstation-process memory. Before C2E.4 can PASS, the parent
creates an encrypted, transactional, append-only external journal scoped by `c2e_run_id` and the
control public key. Before sending a control mutation it durably records session/sequence/request ID,
canonical payload hash, expected state/inventory, and provider idempotency key
`SHA-256(c2e_run_id + NUL + session_id + NUL + request_id + NUL + canonical_payload_sha256)`. It then
records the provider response, independent reread, and final disposition atomically. A coordinator
restart first reconciles every pending entry against provider idempotency state and complete inventory;
it cannot create a new control session or retry a mutation until each entry is classified as applied,
not applied, or blocking ambiguity. Qualification is journaled under `c2e_run_id` with null
`environment_id`; later operations also bind the environment and lease. Providers without durable
idempotency plus independent reconciliation for every mutator are unqualified.

The external emergency broker maintains a separate encrypted transactional append-only journal
scoped by `c2e_run_id` and its broker public key. Before releasing a provider request it records the
launcher/manifest/descriptor/attestation digests, request/session/sequence IDs, canonical payload,
expected state/inventory, expiry, and provider idempotency key; afterward it records the provider
response and independent reread. A broker restart reconciles every pending entry before releasing a
new request. Launcher-local state or an unsigned emergency report is never replay authority.

Before the first provider resource, the parent seals the bootstrap descriptor and creates the
external resource inventory journal with its SHA-256, `c2e_run_id`, `environment_id`, exact provider
tag/query digest, expected empty-inventory digest, and zero sequence. Every create/attach/snapshot/
lifecycle/disposition intent is appended before its provider call; its provider response and
independent complete-tag reread are appended afterward. `resource-create` must apply both run and
environment tags atomically at creation—an untagged intermediate object is unsupported. After a
crash, normal control and emergency broker paths reconcile the journal against exhaustive provider-
tag inventory before any new mutation. The final environment descriptor is a derived immutable
post-provision record containing provider-returned locator digests from the journal; it never replaces
or mutates the bootstrap descriptor. Any created/discovered object absent from the journal is appended
as a reconciled finding and blocks progress until disposition; journal omission never hides a target.

Authentication is split by execution plane; an off, reverted, or destroyed guest is never expected
to authenticate its own control-plane result:

- `qualify`, `lease-acquire`, `lease-renew`, `lease-release`, `inventory`, `resource-create`,
  `volume-attach`, `lifecycle-rule` except read-only `verify-absent`, `power`, `snapshot`, and `destroy`
  are **provider-control-plane** operations. The parent uses authenticated HTTPS and provider-native
  short-lived identity scoped to one selected resource and operation set. The adapter validates the
  provider response, immediately rereads the resource/version/inventory through an independent API
  call, then signs the canonical request/result with a run-scoped parent-only RSA-PSS-SHA-256
  control-receipt key held in the selected external secret manager. Reviewers receive only its public
   key and receipt chain. The provider and reread facts establish external state; the parent signature
   establishes who classified the canonical receipt.
- `facts`, `exec-readonly`, `exec-admin`, `put`, and `get` are **guest-data-plane** operations. A
  separate 256-bit connector-session HMAC key is generated in the parent, injected after restore
  through the provider secret channel, held only in parent and standard-user guest-connector process
  memory, and never snapshotted. Guest requests/responses use HMAC-SHA-256. The guest persists used
  request IDs and next sequence only for that session. Each restore creates a new session/key.
- `exec-admin` additionally requires an RSA-PSS-SHA-256 grant signed by a distinct ephemeral
  parent-only grant private key. Only the public key enters the privileged guest verifier. Possession
  of the connector HMAC key cannot mint a grant or cross the admin boundary.
- Every guest-data target keeps a transactional target-local replay database for the current session.
  Before any action, one durable transaction validates the complete request, atomically claims its
  `(session_id, sequence, request_id, request_sha256)`, advances the next sequence, and, for
  `exec-admin`, atomically claims `(grant_id, grant_sequence, grant_sha256)` in the same commit. Its
  closed state machine is `INTENT -> APPLIED -> RESULT`: `INTENT` commits before effect; `APPLIED`
  records the action-specific reconciliation facts and output identities immediately after effect;
  `RESULT` stores the exact canonical authenticated response bytes. An exact duplicate may only return
  the cached `RESULT` byte-for-byte; reuse with changed bytes fails, and neither a request nor grant is
  executed twice. After restart, the target reconciles every non-`RESULT` row before accepting any
  request or new session. A proven applied action reconstructs and caches its one result; a proven
  non-applied action closes failed without reusing that request/grant. Ambiguity never retries: the
  parent powers off and destroys/restores the affected execution descendant from its last clean
  provider snapshot and rotates session/grant keys, or destroys the signer appliance and invalidates
  its publisher/policy/R0 lineage. No new guest/signer action is legal until external inventory and
  the action-specific after-state prove that disposition. Signer output spools and audits are
  content-addressed so an interrupted `sign-exact-v1` can be classified applied or not applied; an
  unclassifiable signing attempt always takes the signer-destruction route.
- `inventory` and `lifecycle-rule:verify-absent` may use the **retention-verification plane** only
  after terminal disposition. Its provider-native identity can read the exact environment tag and
  lifecycle/deletion audit records but cannot create, attach, power, snapshot, sign, execute, mutate,
  destroy, or change a deadline. Its separate external RSA key signs the request/result chain.
- The **emergency-broker plane** may be used before `environment_id` only for the read-only
  `inventory:pre-resource-run` live preflight, and after the atomic bootstrap only for read-only
  `inventory:pre-resource-environment`. After an environment ID or provider resource exists and
  normal control/wait signing is unavailable or a terminal stop requires immediate safety, it may
  additionally use `lease-acquire`, `lease-renew`, `lease-release`, exhaustive `inventory`,
  `lifecycle-rule:arm-failure-quarantine`, `power:off`, and `destroy`. Its separate provider identity can only stop, enumerate, release,
  quarantine under the already-fixed shorter deadline, or destroy the exact `c2e_run_id`/
  `environment_id` inventory. It cannot qualify, create, attach, snapshot, power on/reboot, execute,
  transfer, sign, extend/reset/pause a deadline, retain a PASS artifact, or advance status. The
  external broker—not the launcher—holds the credential and private attestation key; it releases one
  request only after checking the exact self-contained launcher image/file identity/hash, sealed
  manifest, sanitized environment/DLL search, operation, canonical payload, nonce, and five-minute
  expiry. Its closed attestation is mode-tagged: `pre-resource-run` forbids environment/bootstrap/
  journal fields; `pre-resource-environment` requires the exact atomic bootstrap and zero journal head;
  `emergency-dispose` requires the environment/bootstrap plus current journal head; entry reason
  `C4_PASS_TRANSITION_FAILED` further forces immediate destroy-only behavior and forbids quarantine.
  Every mutator is independently reread and written to the raw emergency record; later Step-33
  bookkeeping creates the normal signed control/wait chain.

The parent generates the control-receipt key during C2E.4 in the selected external secret manager.
Its private operation is scoped to this C2E execution, never enters a guest or child context, and is
reachable only through a process-only opaque handle. The descriptor and all control receipts bind the
§5.0 canonical SubjectPublicKeyInfo SHA-256. After C5 on a successful PASS-retention route—or after Step 33 safety
disposition and its bookkeeping on an abort or failed PASS transition—the parent disables/destroys
the private key and retains only its public verification material
and destruction receipt. A new C2E execution always uses a new key.

C2E.4 also creates a distinct externally held retention-verification key and read-only provider audit
identity. Their immutable scope is only `inventory:read` and deletion/lifecycle audit readback for the
exact `c2e_run_id`/environment-tagged targets; they cannot invoke any mutator or guest/signer action.
The terminal schedule binds their public-key hash, provider-principal/scope digest, rotation policy,
automatic disable deadline, deletion deadline, and named verification time. They persist after the
control/wait keys are destroyed, sign the scheduled absence check, and are disabled/destroyed within
24 hours after a passing absence receipt. If the check finds residual state, the read-only identity
  records it and the owner acquires a new narrowly scoped emergency control identity; it never widens the
  retention identity. The automatic key/identity deadline is the verification deadline plus seven days
  and cannot be extended; any unresolved residual at that point remains an incident/blocker with
  provider-native lifecycle deletion still armed.
- `lifecycle-rule:shorten-c5` uses a **C5-shortener subplane** of provider control, never the revoked
  active-run identity or the read-only retention identity. C2E.4 installs one immutable provider-side
  preauthorization, bound to this `c2e_run_id`, the `shorten-c5` verb, independent reread, the eventual
  Step-25 retained-volume/rule receipt, and the signed C5 intent. It holds no reusable provider
  credential and cannot act before those bindings exist. After the C5 candidate and intent are
  remotely/provably fixed, the parent alone uses the external authorization service to mint one new
  non-exportable session lasting at most one hour and no later than the immutable 60-day
  preauthorization deadline. That session can only shorten and reread the exact old rule; it cannot
  inventory any other target, create, attach, power, snapshot, destroy, retain, extend, reset, or
  invoke guest/signer actions. The parent revokes and independently rereads the session absent
  immediately after success or failure, and destroys the preauthorization after the verified C5
  result. C2E.33 destroys the preauthorization on every abort or failed PASS transition; only a
  verified Step-25 PASS-retention transition may preserve it through C5.

The response `authenticator` is a closed tagged union: control-plane results contain exactly
`kind=provider-control-receipt`, `provider_response_sha256`, `independent_reread_sha256`,
`public_key_sha256`, `canonical_payload_sha256`, and `signature`; guest-data-plane results contain exactly
`kind=guest-connector-hmac`, `key_id_sha256`, `canonical_payload_sha256`, and `mac_hex`; retention-
verification results contain exactly `kind=retention-verification-receipt`,
`provider_response_sha256`, `independent_reread_sha256`, `readonly_identity_scope_sha256`,
`public_key_sha256`, `canonical_payload_sha256`, and `signature`; emergency results contain exactly
`kind=emergency-provider-result`, `provider_response_sha256`, `independent_reread_sha256`,
`broker_attestation_sha256`, `broker_public_key_sha256`, and `canonical_payload_sha256`. An emergency
result is raw private safety evidence, not a normal signed control receipt or status input.

For every response variant, `response_payload_bytes` is the §5.0 C2E-canonical JSON of every outer
response property except `authenticator`;
`canonical_payload_sha256` is the lowercase hexadecimal SHA-256 of those exact bytes. Response
`authenticator_metadata_bytes` is C2E-canonical JSON of every authenticator property
except its proof field (`signature` for control/retention results or `mac_hex` for guest results); for
the proofless emergency result it is the entire authenticator object. It therefore binds the provider
response/reread, key/scope/attestation identities, kind, and payload hash
that apply to the variant. The exact response proof input is
`ASCII("skill-mesh/phase-is-c2e-connector-auth/v1") || 0x00 || ASCII("response") || 0x00 ||
ASCII(kind) || 0x00 || uint64be(length(response_payload_bytes)) || response_payload_bytes ||
uint64be(length(authenticator_metadata_bytes)) || authenticator_metadata_bytes`. Control and
retention results encode an unpadded-base64url RSA-PSS proof with SHA-256, MGF1-SHA-256, and a
32-octet salt over that exact input; guest results encode a 64-lowercase-hex HMAC-SHA-256 over that
exact input. Verification recomputes and verifies the full outer response, not only `result`, before
the response can advance state. The emergency result has no signature or MAC field: the parent
recomputes its payload hash, validates the provider response and independent reread through the
authenticated broker sideband, verifies the referenced signed broker attestation, and preserves the
object only as raw private safety evidence; it can never satisfy a normal receipt or status gate.
Duplicate, expired, reordered, wrong-role, wrong-lease, wrong-prior-state, wrong-plane, bad-signature, or bad-MAC
requests fail before action. Provider credentials, all parent/broker private keys, and the connector key are
unavailable to Terra children.

The parent acquires the environment lease and verifies complete environment inventory before every
create, attach, lifecycle mutation, power, snapshot, restore, admin, or destroy action. The response
proves the same lease still owned the namespace afterward. The parent schedules `lease-renew` no later
than ten minutes before expiry; renewal may overlap an already-authorized long-running guest action
but no other control mutation, and every action stops/blocks if renewal is not independently confirmed
before expiry. A request may start only while its own expiry and expected maximum run time fit inside
the current lease or while that exact same-holder renewal rail is active. An ambient host path,
unsigned accepted receipt, unverified successful response, incomplete inventory, unresolved journal
entry, or provider unable to make acquisition/renewal/release atomic is not an accepted connector.

As C2E.29's first provider resource, before any execution/signer/storage/network object, the provider
must arm a lifecycle rule that operates
without the parent session: each acquired or renewed control-plane lease expires in at most 30
minutes; `lease-renew` preserves the lease ID and holder, refuses an expired/conflicting lease, and
cannot extend past the absolute lineage deadline; a running guest is automatically powered off within
five minutes after lease expiry (the defined missed-renewal event); its writable descendant is destroyed
within 60 minutes; and the complete active lineage (guest, descendants, S1/R0 snapshots, OS disk, run
volume, and environment-scoped private provider artifacts) is destroyed no later than 30 days after
the first resource's `created_utc`. These are v1 maximums: C2E.4 may shorten them but may not extend,
disable, pause, or reset the absolute 30-day runnable-lineage clock. On C4 PASS, C2E.33 performs only
the exact proof-bound atomic `transition-pass-retention` above; it destroys the runnable lineage and
reclassifies only the detached permitted run volume under its fixed C4-plus-120-day evidence rule.
No other deadline extension exists. On an abort, immediate destruction is the default; any powered-off quarantine expires
at the earlier of terminal-stop time plus seven days or the original complete-lineage 30-day deadline.
Lifecycle-rule creation, provider clock, target inventory, and destructive action are independently
reread and bound into provisioning/disposition receipts.

### 5.2 Authority and role matrix

| Role | May do | Must never do |
|---|---|---|
| Parent coordinator | hold separate verdict, control-receipt, wait-result, connector-session, publication-capability, and ephemeral grant-signing authorities; acquire provider leases; create/power/revert/destroy serialized descendants through the authenticated adapter; create fresh producer/reviewer contexts; manage isolated source worktrees; validate receipts; issue single-use asymmetrically signed guest-admin grants and exact-body publication capabilities; integrate one reviewed Git candidate; push with expected-old-object protection; post C2E/C2N/C3 seals | change workstation security state; expose any private key/provider/GitHub credential; let a producer classify a verdict or invoke infrastructure/admin actions; accept guest/provider success text without authenticated receipt verification and independent control-plane reread |
| Terra producer | edit only its isolated coordinator worktree; request allowlisted standard-user guest probes; consume redacted machine facts | receive reviewer context, verdict key, guest infrastructure/admin credentials, signing key, `main` push authority, or issue-seal authority |
| Fresh reviewer | read immutable candidate objects and independently rerun read-only or approved substrate checks in a fresh R0 descendant | reuse producer context/state; edit producer output; sign or post the final verdict |
| Infrastructure/operator boundary | qualify/provision the provider; execute only authenticated parent grants for pre-authored guest-admin actions; sign exact declared candidate hashes; reboot; install/load/unload driver; attest results; dispose or quarantine on every terminal path | author or patch repository code during an operator step; expose reusable credentials; accept arbitrary command text; act on an unbound path, hash, lease, or wildcard |
| Standard guest runner | clone/fetch exact candidate; build/test/run approved unprivileged host modes; write only receipt-bound guest roots | modify policy, certificates, BCD, snapshots, infrastructure, real profile, or Git remote state |
| C4 evidence uploader | receive one process-only external-broker capability named `GH_TOKEN` for the current exact redacted body and publish/reread that one #153 record; repeat later with a distinct cleanup capability | receive the real GitHub credential, reach the GitHub API directly, retain/reuse a capability, push Git, post another issue comment, or expose private evidence |

The producer may generate evidence but cannot grant it verdict status. Only the parent verifies the
sidecar HMAC, classifies the independent review, integrates the candidate, and posts a stage seal.
Guest administrator success is an input fact, not reviewer or final-verdict authority.

The frozen UAT's process-only `GH_TOKEN` name does not authorize a reusable GitHub credential inside
the post-kernel guest. The real credential remains in an external parent-authorized publication
broker. For each of the two ordered `evidence-upload` invocations, the parent first retrieves and
validates the exact redacted body bytes, then requests a distinct opaque capability placed only in
that child process as `GH_TOKEN`. Its private closed grant binds exactly `c2e_run_id`,
`environment_id`, candidate commit/tree, ordinal (`evidence` or `cleanup`), issue `153`, body
SHA-256, uploader image/file identity, exact argv, broker endpoint, idempotency key, issued UTC, and
an expiry no more than five minutes later. The cleanup grant additionally binds the remotely reread
first-comment ID/body digest and cleanup-attestation digest. A capability permits one idempotent
comment creation with those exact bytes and rereads only the returned comment ID; it cannot select a
different repository, issue, endpoint, body, operation, or third publication.

The broker holds only a short-lived repository/issues-scoped GitHub credential outside the guest,
signs its own grant/result chain, and disables the run capability immediately after the exact remote
reread; expiry remains an independent fail-safe. Guest egress permits the pinned broker endpoint but
denies direct GitHub API access. C2E.30 proves the egress rule and a non-publishing synthetic grant,
including wrong issue/body/ordinal/image/argv, replay, third-use, and expiry denials. C3 must repeat
those planted negatives against the final uploader. If the uploader implementation requires a
literal direct GitHub credential in the guest, stop for an authoritative plan decision instead of
weakening this boundary or editing the frozen UAT.

An admin grant is canonical closed JSON with `schema=skill-mesh/phase-is-c2e-admin-grant/v1` and
exactly `schema`, `c2e_run_id`, `environment_id`, 256-bit random `grant_id`, positive monotonic
`grant_sequence`, `target_kind` (`execution-guest` or `signer-appliance`), `target_id_sha256`, connector
`session_id`/`request_id`/`sequence`, `lease_id`, `expected_state_sha256`, `action_id`, candidate
commit/tree, exact logical input object identity/size/SHA-256, nullable signer/policy IDs required only
by their declared action, issued/expiry UTC no more than five minutes apart, expected output class,
ephemeral §5.0 SubjectPublicKeyInfo SHA-256, `canonical_payload_sha256`, and RSA-PSS-SHA-256 signature; every
object has `additionalProperties=false`. `admin_grant_payload_bytes` is the §5.0 C2E-canonical JSON
of every grant field except both `canonical_payload_sha256` and `signature`.
`canonical_payload_sha256` is the lowercase hexadecimal SHA-256 of those exact
bytes. The signature input is
`ASCII("skill-mesh/phase-is-c2e-admin-grant-signature/v1") || 0x00 ||
uint64be(length(admin_grant_payload_bytes)) || admin_grant_payload_bytes`; `signature` is unpadded
base64url RSA-PSS using SHA-256, MGF1-SHA-256, and a 32-octet salt over that exact input. The verifier
recomputes the payload bytes and declared hash before verifying the signature; neither field is
self-referential. `grant_sha256` is the lowercase hexadecimal SHA-256 of the complete C2E-canonical
grant including `canonical_payload_sha256` and `signature`. The complete grant is delivered only as the
closed `exec-admin.parameters.grant` object and never through an environment variable, command line,
file path, prompt, or authentication sideband. The parent generates a new exact §5.0 grant key pair after each restore,
keeps the private key only in parent memory, and injects only the public key into the privileged
verifier through the provider secret channel. The verifier persists consumed grant IDs/sequences for
that descendant and refuses reuse, gaps, expiry, wrong session/lease/state/input/action, or bad
signature before elevation. Restore discards the verifier state and public key, so the parent creates
a new pair and old grants fail. The connector HMAC holder, producer, reviewer, and standard guest
runner cannot mint or reuse a grant. Signing a candidate means only that declared bytes may enter the
disposable test policy; it is not code approval and cannot create reviewer or final-verdict authority.

### 5.3 Snapshot lineage and credentials

1. Provision a fully patched supported Windows 11 Enterprise x64 image and install the toolchain.
2. Freeze exact OS edition/build, update state, firmware facts, tool versions/hashes/signatures, and
   connector version in powered-off S1.
3. S1 contains no source clone, provider login, GitHub token, test publisher/private key, App Control
   policy, `TESTSIGNING`, or run evidence.
4. Create the separate signer appliance, generate its run-specific non-exportable publisher leaf,
   export only the public chain, and configure its hash-bound signing service. The appliance is never
   snapshotted and never receives source or executable code except one exact unsigned object already
   approved for signing.
5. Create one execution run lineage from S1. Import only the public publisher chain, deploy admission
   policy, enable execution-guest-only test signing, reboot, remeasure, and freeze powered-off R0
   before any candidate or kernel canary enters. R0 contains no provider, connector, GitHub, Claude,
   Codex, reusable remote URL credential, signing private key, or post-kernel state. Run every signed
   and planted-negative canary only in a throwaway writable descendant of R0 and destroy that
   descendant afterward; the signer appliance receives only the independently reviewed exact canary
   object.
6. The parent—not a producer or reviewer—uses the authenticated provider adapter to create, attach
   the run volume, power, revert, enumerate, and destroy each descendant. Only one writable descendant
   of R0 may exist at a time. Producer, reviewer, integrated certification, and C4 uses are serialized.
   A new independent run starts again from S1 with a new signer appliance and publisher identity.
7. Execution-guest and signer-appliance process credentials and connector-session secrets are
   distinct, injected only after power-on/restore, are never written to disk, a remote URL,
   credential helper, shell history, log, or receipt, and are revoked before power-off. Parent
    active provider identity never enters the guest. It remains narrowly scoped and live only through guest
   process-secret revocation, power-off, complete inventory, destruction/quarantine, lease release,
   and receipt verification; the parent revokes provider identity last.

Before every reboot, the environment bundle closes host sessions, quiesces driver activity where
possible, flushes evidence, and records the candidate commit/tree, policy ID/hash, public certificate
hash, driver package hash if present, and reboot reason. After reboot, it revalidates those facts
before any continuation.

### 5.4 Toolchain contract

Execution rechecks Microsoft's supported-version pages in C2E.4 and then, only during authorized
C2E.29 guest provisioning, installs the Visual Studio
2026 toolchain with the matching 28000 SDK/WDK build family. As verified on 2026-08-30, the current
released inputs are Windows SDK `10.0.28000.2705` and WDK `10.0.28000.2526`; their build number is
28000 and their QFE values may differ under Microsoft's kit-versioning rule. A changed supported
release requires C2E.4 to record the new official evidence and operator selection before provisioning
rather than substitute silently. C2E records complete capability/candidate inventories only; C2N
records the full candidate set and applies its existing deterministic selection rule inside the guest.
Microsoft's Windows 11 release-information page listed 26H1 build `28000.2804` on 2026-08-30
(revision dated 2026-08-27); C2E.4 records the then-current supported build and
C2E.29 freezes the exact installed revision rather than baking today's servicing revision into a
long-lived unattended installer.

The readiness probe requires at least:

- Visual Studio 2026 Desktop development with C++, x64 MSVC, and the matching x64 Spectre libraries;
- SDK `10.0.28000.2705`, WDK `10.0.28000.2526`, matching 28000-family headers/libraries, the WDK
  Visual Studio extension, `cl.exe`, `link.exe`,
  `dumpbin.exe`, `signtool.exe`, `inf2cat.exe`, and `CiTool.exe`;
- Windows PowerShell 5.1, Git, Python, pytest, PyYAML, and GitHub CLI;
- Claude `2.1.223.0` and Codex `0.147.0`, subject to D9's exact hashes and complete closure checks;
- enough free memory and disk for the stable repo-root gate and native build.

C2N freezes approved-anchor-relative locators, candidate-set digests, versions, hashes, and
signatures. C3 upgrades the exact consumed set to retained-handle physical identities. PATH order,
an equal-version byte/signer ambiguity, or a missing exact version stops the run.

### 5.5 Isolated test publisher, App Control, and kernel signing

Each run creates exactly one X.509 v3 test-publisher chain—self-signed root, one issuing/PCA, and one
code-signing leaf—only inside the separate signer appliance. Every public key is exact RSA-3072 with
exponent 65537 and canonical DER SubjectPublicKeyInfo as in §5.0; every certificate signature is
`sha256WithRSAEncryption`. Each certificate has one distinct 16-octet positive serial whose first
octet is `0x01`–`0x7f`, with the remaining octets from the appliance CSPRNG, encoded as a minimal DER
INTEGER. Each subject is a single-RDN, single-attribute DER Name using OID `2.5.4.3` and UTF8String:
root `Skill Mesh C2E Root <c2e_run_id>`, PCA `Skill Mesh C2E PCA <c2e_run_id>`, and leaf
`Skill Mesh C2E Publisher <c2e_run_id>`. Root issuer equals its subject; PCA and leaf issuer Names
byte-equal the subject Name of their direct issuer.

All three certificates share one validity window: `notBefore` is the Step-29 provider clock,
normalized to the earlier whole second, minus five minutes; `notAfter` is the immutable active-lineage
destruction deadline and may not be renewed or extended. The root has critical Basic Constraints
`CA=true,pathLenConstraint=1`; the PCA has critical Basic Constraints
`CA=true,pathLenConstraint=0`; the leaf has critical Basic Constraints `CA=false` with no path length.
Root and PCA have critical Key Usage containing exactly `keyCertSign,cRLSign`; the leaf has critical
Key Usage containing exactly `digitalSignature`. Root/PCA contain no EKU; the leaf contains one
noncritical EKU, Code Signing `1.3.6.1.5.5.7.3.3`, and no lifetime-signing or other EKU. Every
certificate has a noncritical 20-octet Subject Key Identifier equal to SHA-1 of its subjectPublicKey
BIT STRING contents and a noncritical Authority Key Identifier containing only the issuer's exact SKI
(the root references its own). SAN, AIA, CRL distribution, policy, name-constraint, template, and
unknown extensions are absent, so validation has no online discovery or revocation dependency.

The leaf key is non-exportable; root/issuing private material is destroyed after issuance. Only the
public root enters execution-guest `LocalMachine\Root`, only the public PCA enters
`LocalMachine\CA`, and only the public leaf enters `LocalMachine\TrustedPublisher`; no other store or
machine receives the chain and no private key enters the execution guest. Authenticode signing uses
exactly one SHA-256 file digest/signature with the leaf, no appended/dual signature, no `/t` or `/tr`
timestamp, and no timestamp token. The leaf must be time-valid at signing and every C2E/C2N/C3/C4
verification. The public DER chain, exact extension/Name/serial/validity/store facts, and signature
hashes enter evidence. Neither S1, R0, nor any run descendant ever contains or can route to the
private key. Producers and reviewers receive neither appliance credentials, connector session, key,
nor grant channel.

The appliance leaf is a machine CNG key in `LocalMachine\My` using Microsoft Software Key Storage
Provider, has Code Signing EKU only, and has an export policy that permits neither
plaintext nor encrypted private-key export. Its protected private-key DACL allows only `SYSTEM` for
administration and `NT SERVICE\SkillMeshC2ESigner` for sign use; the appliance runs no producer,
reviewer, build, test, host, or candidate process. Its signer service has no interactive logon,
general network route, arbitrary command/path surface, or write outside an input/output spool cleared
after each action. It accepts only an embedded asymmetric parent grant bound to appliance identity,
session/request/sequence, lease, exact unsigned object hash/size, candidate commit/tree, public signer/
policy IDs, expiry, and expected signed-output class. Connector HMAC possession cannot mint that grant.

Before any candidate user/kernel binary is signed or loaded, a fresh no-history reviewer must PASS the
immutable source, unsigned object, compiler/input manifest, and source-to-object binding. Only then may
the parent issue one signing grant and transfer exactly that content-addressed object to the appliance.
The signer returns a different content-addressed signed object plus signature/chain receipt; the parent
reopens it, verifies that the non-signature bytes and declared hash relationship are exact, clears the
spool, and powers the appliance off. A signature means admission only, never code approval or verdict.
At the end of C3 candidate locking, the parent destroys the leaf/appliance before C4; any later code
change invalidates the packet and requires a new signer/publisher/policy R0 lineage.

Readiness binds the signer-appliance identity, isolation/network-policy and complete-inventory digests,
public certificate facts, key export policy, normalized private-key DACL hash, signer service SID/
configuration/binary hashes, channel ACL digest, and successful exact-grant signing canary. Planted
negatives prove execution-guest, standard-user, producer, and reviewer tokens cannot address/reach the
appliance, use/export the key, invoke its channel, or mint/replay a grant. A known signed kernel escape
canary runs only in a throwaway descendant and attempts signer-route/credential access; authoritative
provider network logs and signer audit inventory—not its guest self-report—must prove no route, request,
or credential exposure before that descendant is destroyed.

Threat boundary: after any candidate kernel image enters, that descendant and every guest-local event,
HMAC, service, or file is potentially kernel-controlled. The plan does not claim a DACL or a second
descendant makes intentionally malicious kernel evidence trustworthy. Safety comes from independent
source/object review before signing, external key/provider/Git/verdict isolation, externally observed
network/lineage facts, single-use descendants, and destruction after each run. If a required behavioral
claim cannot be corroborated outside the post-load guest or accepted as attended observation of the
reviewed bytes, stop rather than treating guest cryptography as proof.

The execution guest uses an unsigned, enforced App Control base policy with user-mode Code Integrity enabled,
Windows/Microsoft closure rules, exact pinned non-Windows tool/host closure, and exactly one
run-publisher rule at App Control `Publisher` level. Its signer contains the exact tool-generated
`CertRoot Type="TBS"` value for the run PCA plus `CertPublisher` equal to the exact leaf CN
`Skill Mesh C2E Publisher <c2e_run_id>`, has no `FileAttribRef`, version, filename, or wildcard, and is
referenced in both user-mode signing scenario `12` and kernel-mode signing scenario `131` (and the
matching `CiSigner` entry required for user mode). The run rule may not be generated as
`RootCertificate` (unsupported), `PcaCertificate`, `LeafCertificate`, `FilePublisher`, or a fallback
hash rule. The parent records the generated XML signer/scenario nodes, PCA TBS value, leaf CN, and
tool commands, then independently reconstructs and compares them from the signed canaries and public
chain. Unsigned policy is selected because this disposable route has
Secure Boot off for ordinary kernel test signing. The compensation is narrow admin custody,
standard-user host execution, powered-off snapshot control, policy hash/ID revalidation, and a fresh
R0 descendant for independent review.

Before the final launcher exists, the environment bundle creates user-mode and kernel-mode canaries
from committed seed sources and derives the publisher rule. R0 is frozen after the full pinned
closure runs in audit mode, every audit event is resolved, enforcement is deployed through `CiTool`,
the guest reboots, and clean pre-canary facts are remeasured. Every canary then runs only in a
throwaway R0 descendant; that descendant is destroyed and never becomes a snapshot ancestor.
Readiness requires:

- the correctly signed user canary starts;
- an unsigned/tampered and wrong-publisher user canary is blocked before entry with correlated Code
  Integrity enforcement evidence;
- the signed kernel canary loads only under guest test signing;
- an unsigned/tampered or wrong-publisher kernel canary does not load;
- policy XML/binary hash, policy/base IDs, UMCI/kernel scenario, signer rule, enforcement mode, event
  evidence, public signer facts, and external signer/network audit facts agree.

This is the non-circular admission contract: C2E/C2N freeze a pre-existing publisher rule and signer;
C3 later records the final launcher/helper/driver hashes and signatures in the candidate lock. A
future final-binary hash is never placed in C2E or C2N. If an exact pre-existing file-hash rule for
the future binary is interpreted as mandatory, stop for an authoritative plan decision instead of
reordering policy deployment silently.

The guest firmware has Secure Boot off and guest BCD has `TESTSIGNING` on after an observed reboot.
Memory Integrity/HVCI remains on, so every kernel image must still be signed. The plan does not use
production signing, Microsoft preproduction Secure Boot keys, or a Custom Kernel Signers route.

App Control proves image admission only. The Step-108P launcher, guardian, broker, driver, Job Object,
environment, child-process, handle, and I/O rules remain independently required.

### 5.5A Emergency launcher build closure

The one coordinator-native exception is the non-driver, user-mode emergency launcher. Step 21 builds
the deterministic C++17 native shell/builder and Step 23 integrates and proves the final executable,
using the already-installed Visual Studio 2026 MSVC x64 toolset v14.50 and a supported
already-installed Windows SDK 26100-or-newer user-mode library set. It does not use the WDK, sign a
binary, install/upgrade a tool, modify a certificate/policy/boot setting, or execute candidate code.
Step 3 enumerates the complete compiler/linker/SDK candidates; Step 4 pins full approved-anchor-
relative paths, versions, Microsoft signatures, SHA-256 identities, exact flag/library arrays, and
approved root ACL facts as `emergency_build_toolchain_sha256`. Missing, ambiguous, PATH-only,
or changed inputs block Steps 21/23 and provisioning; there is no local install or alternate compiler
fallback.

That digest is the raw-file SHA-256 of one private C2E-canonical
`skill-mesh/phase-is-c2e-emergency-build-toolchain/v1` manifest with exactly `schema`, `c2e_run_id`,
`created_utc`, `candidate_inventory_sha256`, closed `compiler`, `linker`, `dumpbin`, and `sdk` objects,
ordered `compile_args`, `link_args`, `include_roots`, `library_files`, and `allowed_imports` arrays,
closed `environment`, `build_root_acl_sha256`, and `authenticator`. Each tool object contains exactly
its approved-anchor-relative and absolute paths, file SHA-256, product/file version, Authenticode leaf
and chain SHA-256, and signature status. SDK/include/library entries contain exact absolute path,
version, file or tree digest, and ACL-root digest; the environment contains only the explicit variables
and cleared/inherited-denial set. Every nested object has `additionalProperties=false`.
`authenticator` is exactly the §5.0 signed-object profile using the parent control-receipt key and
domain `skill-mesh/phase-is-c2e-emergency-build-toolchain-signature/v1`.

The full signed manifest is stored content-addressed in the Step-4 encrypted private artifact store.
Only the parent receives its process-only opaque retrieval handle through
`SKILL_MESH_C2E_TOOLCHAIN_MANIFEST_REF`; the handle, absolute paths, and manifest bytes never enter Git,
a prompt, a Terra child, or either guest. Steps 21 and 23 independently retrieve it, verify the raw
hash/signature/run ID/candidate inventory and every current file signature/hash/ACL fact, remove the
handle from the process, then invoke only the arrays and absolute paths it names. Missing retrieval,
an extra/default argument, a moved file, or any manifest/current-fact mismatch blocks before compile.

The builder invokes the pinned `cl.exe` and `link.exe` by absolute path under a cleared environment
with explicit `PATH`, `INCLUDE`, `LIB`, `TMP`, and `TEMP` roots owned by the build. Its committed
response-file-equivalent argument arrays are exactly:

```text
cl.exe /nologo /std:c++17 /O2 /MT /W4 /WX /GS /guard:cf /DUNICODE /D_UNICODE
       /Brepro /c <sorted exact source paths> /Fo:<empty-build-root>\
link.exe /NOLOGO /OUT:<empty-build-root>\phase-is-emergency-launcher.exe /BREPRO
         /SUBSYSTEM:CONSOLE /DYNAMICBASE /HIGHENTROPYVA /NXCOMPAT /CETCOMPAT /GUARD:CF
         /OPT:REF /OPT:ICF /MANIFEST:EMBED /DEBUG:NONE <sorted exact object paths>
         <exact MSVC/SDK library paths for static CRT, kernel32, advapi32, bcrypt, winhttp, crypt32>
```

The implementation stores arguments as arrays and rejects shell text, response files, environment-
inherited options, unlisted sources/libraries, or a nonempty output root. Two builds in different
empty roots must be byte-identical. The pinned `dumpbin.exe` recursively verifies imports, delay
imports, headers, load configuration, CFG/CET/dynamic-base/NX/high-entropy flags, embedded manifest,
and static-CRT closure; only the committed Windows KnownDLL/system set is allowed. The executable is
intentionally unsigned: broker authorization binds its exact SHA-256, PE file identity, immutable
manifest, and sanitized runtime closure. Any external runtime, interpreter, plugin, current-directory
DLL, writable search root, or final double-build mismatch blocks Step 23.

The executable exposes only `preflight-empty` and `emergency-dispose`. `preflight-empty` traverses the
same parser, manifest verification, sanitized runtime, image-bound broker attestation, provider HTTPS,
raw-record writer, and independent-reread path as cleanup, but the broker permits only the closed
read-only `inventory` scopes above and requires an empty result. It cannot acquire/release a lease,
power, quarantine, destroy, or perform any other mutation. C2E.29 materializes the exact current-
candidate executable/manifest into the immutable private store and independently rereads their bytes;
then it runs `pre-resource-run` before `environment_id` exists and `pre-resource-environment` after the
bootstrap/journal transaction commits. Both must pass before `lease-acquire`, the first provider
mutation. A test-only mock or builder-unit result is not this live preflight.

### 5.6 Environment descriptor and readiness receipt

`tools/phase-is-environment/schemas/environment-bootstrap-v1.schema.json` defines the immutable
private pre-resource bootstrap descriptor described in §2. Its provider tag/query, resource specs,
authority scopes, lifecycle maxima, exact emergency launcher/manifest/broker binding, journal/store references, and coordinator
exclusion facts are complete before the first resource, while every provider-returned locator is
forbidden. `tools/phase-is-environment/schemas/resource-inventory-journal-v1.schema.json` defines its
authenticated append-only resource ledger. `tools/phase-is-environment/schemas/environment-
descriptor-v1.schema.json` defines the derived post-provision descriptor: it binds the bootstrap and
journal-head hashes, opaque execution-guest and signer-appliance locators, connector endpoints,
expected firmware UUID/MachineGuid facts, S1/R0 snapshot locators, encrypted run-volume locator,
external replay-journal, control/wait/grant/emergency/publication-broker/retention authorities,
publication-broker endpoint/policy reference, provider qualification/retention, and credential
references. The real GitHub credential and every child capability remain external/process-only.
None is copied into a prompt, transcript, repository, issue,
or redacted result.

`documentation/findings/phase-is-c2e-environment.json` uses §5.0 C2E-canonical JSON with schema
`skill-mesh/phase-is-c2e-environment/v1`,
and `additionalProperties=false` at every object. It contains exactly:

- `schema`, `c2e_run_id`, `pre_receipt_commit`, `pre_receipt_tree`, `environment_id`, and `created_utc`;
- redacted guest OS/edition/build/architecture, firmware, resource, update-freeze, and encrypted run-volume
  facts;
- provider qualification/authorization digest; connector adapter/version/hash, authenticated-transport,
  request/receipt, anti-replay, complete-inventory, and lease-probe facts; immutable bootstrap/final-
  descriptor digests, final resource-journal-head digest, and matching complete-tag-inventory digest;
- S1/R0 lineage and separate signer-appliance digests, powered-off capture facts, network/provider-
  auth credential-absence assertions, proof that execution snapshots contain only the public
  publisher chain and no signing private key, signer-appliance route-isolation facts, and the one-
  writable-descendant lease result;
- toolchain and host complete candidate-set/capability digests plus public candidate locators,
  versions, hashes, and signatures; exact emergency-build-toolchain digest; no C2N selection claim;
- public publisher-chain, isolated-appliance key-property/store/DACL/service/channel facts, signed-
  escape-canary external network/audit result, root/issuing-private-material destruction facts, and
  the still-live leaf/appliance's powered-off disposition;
- App Control policy IDs/hashes/mode/scenarios/publisher rule and positive/negative canary result hashes;
- Secure Boot, BCD `TESTSIGNING`, HVCI, reboot-generation, and drift-check facts;
- coordinator/guest authority matrix digest, fresh Terra producer/reviewer transport-probe hashes,
  parent-only classification result, and the full stop-condition-set digest;
- publication-broker public-key/scope/policy digests, direct-GitHub-API egress-denial facts, and the
  non-publishing synthetic one-capability smoke digest; no endpoint, credential, or capability value;
- `private_evidence_manifest_sha256` for the receipt-bound source-evidence bundle in the authorized
  encrypted private artifact store, plus its access owner and deletion deadline.
- the control-receipt, wait-result, emergency-broker, retention-verification, and dormant C5-shortener
  preauthorization public-key/scope digests plus immutable control/wait/broker/C5-shortener automatic-
  disable deadlines; exact lease, missed-renewal power-off, writable-descendant,
  and complete-active-lineage maximums; provider lifecycle-rule digest; and independent lifecycle
  reread facts.

It contains no private key/certificate secret, token, credential reference, endpoint, provider/tenant
identifier, machine/user name, absolute path, raw registry root, policy XML, private event payload,
prompt/transcript, or source content. A public certificate hash/thumbprint is permitted; private-key
material is never permitted. Raw C2E probe/events, the private descriptor, and connector/provider
receipts live in the separately authorized encrypted private artifact store, not in the C4 run
volume or `<evidence-export>` root.

The receipt is deliberately non-self-referential. `pre_receipt_commit/tree` name the immutable code
candidate that contains the verifier, provider adapter, and guest bundle but not the readiness JSON.
The private evidence manifest is finalized against that candidate before the readiness JSON exists
and explicitly excludes the future readiness JSON, its Git blob/commit/tree, #162 seal, and all later
C2N/C3/C4 outputs. After commit, the #162 seal—not the receipt—binds the readiness blob and sealing
commit/tree.

The direct emergency path writes one private canonical
`skill-mesh/phase-is-c2e-emergency-disposition/v1` record. Its closed object contains exactly
`schema`, `c2e_run_id`, `environment_id`, `entry_reason`, `bundle_manifest_sha256`,
`launcher_sha256`, `bootstrap_descriptor_sha256`, `resource_journal_head_before_sha256`,
`resource_journal_head_after_sha256`, nullable `final_descriptor_sha256`, `started_utc`, `ended_utc`,
`provider_principal_scope_sha256`, `before_inventory_sha256`, `after_inventory_sha256`, a
`target_results` array, `lease_disposition`, `control_session_disposition`,
`guest_credential_disposition`, nullable `original_failure_sha256`, nullable
`pass_transition_failure_sha256`, `safety_outcome`, and `parent_signature_status`.
Each closed `target_results` item contains exactly provider target kind/opaque-ID hash, requested
disposition, provider-response SHA-256, independent-reread SHA-256, and closed result. `safety_outcome`
is exactly `SAFE_DESTROYED`, `SAFE_QUARANTINED`, or `INCOMPLETE`; `parent_signature_status` is exactly
`PRESENT` or `DEFERRED`. `C4_PASS_TRANSITION_FAILED` requires null
`original_failure_sha256`, a non-null transition-failure digest, and either `SAFE_DESTROYED` or
`INCOMPLETE`; it forbids `SAFE_QUARANTINED`. An incomplete record is non-terminal private evidence:
it cannot produce a marker, status result, or C5 eligibility and must continue or escalate cleanup.
Only `SAFE_DESTROYED` may feed that entry reason's terminal-disposition `BLOCKED` record. Every abort
reason requires a non-null original-failure digest and null transition-failure digest. The raw record
is never a public status input by itself. Step 33 binds its
hash, performs a fresh provider reread, and creates the canonical signed disposition/wait proof before
status or C5 may advance.

Each live preflight writes a private canonical
`skill-mesh/phase-is-c2e-emergency-preflight/v1` record. Its common closed fields are exactly
`schema`, `c2e_run_id`, `scope`, `precondition_commit`, `precondition_tree`, `bundle_manifest_sha256`,
`launcher_sha256`, `broker_attestation_sha256`, `provider_principal_scope_sha256`, `started_utc`,
`ended_utc`, `provider_response_sha256`, `independent_reread_sha256`, `inventory_sha256`,
`inventory_count` (exactly zero), and `outcome` (exactly `EMPTY`). For `pre-resource-run`,
environment/bootstrap/journal properties are absent. For `pre-resource-environment`, the object also
requires exactly `environment_id`, `bootstrap_descriptor_sha256`, and
`resource_journal_zero_head_sha256`. Fields from the other variant are absent, not null. Either a
nonempty inventory or any runtime/broker/provider/reread mismatch blocks before mutation.

Before C2E.4 makes its first allocation, the parent writes one private canonical unsigned
`skill-mesh/phase-is-c2e-selection-attempt/v1` object containing exactly `schema`, `c2e_run_id`,
`provider_adapter_key`, `provider_qualification_source_sha256`,
`planned_allocation_manifest_sha256`, `wait_key_create_idempotency_key_sha256`, `created_utc`, and
`coordinator_before_sha256`. Its hash is the cleanup binding until a successful provider-selection
wait result exists. The planned-allocation digest names one private canonical
`skill-mesh/phase-is-c2e-selection-allocation-plan/v1` object containing exactly `schema`,
`c2e_run_id`, `wait_key_create_idempotency_key_sha256`, and `allocations`. The ordered array contains
exactly one closed `{allocation_kind, create_idempotency_key_sha256}` object for each of the eight
post-wait kinds below, sorted by kind; the duplicated wait-key idempotency digest must match the
selection attempt. Unknown, duplicate, or missing kinds block before allocation. The wait-result key is always the first allocation. Its selected secret manager
must provide an idempotent create-or-absent transaction whose commit condition includes successful
RSA-PSS test signing through the recoverable opaque handle, public-key reread, and run-tag inventory
reread. Failure/ambiguity reconciles to proven absence and the local no-allocation stop; a committed
transaction always yields the usable signer before any second allocation. A provider that cannot
make or prove this binary result is rejected during read-only qualification and is never called.
Consequently every partial state containing any allocation also contains the working wait signer
needed for authenticated `pre-resource-closure`.

Every planned post-wait-key allocation is represented by one private canonical
`skill-mesh/phase-is-c2e-selection-allocation-disposition/v1` record. Its closed object contains
exactly `schema`, `c2e_run_id`, `selection_attempt_sha256`, `allocation_kind`,
`create_idempotency_key_sha256`, `state`, nullable `allocated_object_sha256`,
`provider_response_sha256`, `independent_reread_sha256`, and `completed_utc`.
`allocation_kind` is exactly `control-key`, `emergency-broker-authority`,
`retention-key-identity`, `c5-shortener-preauthorization`, `replay-journal`, `emergency-journal`,
`private-store-namespace`, or `provider-authorization`; `state` is exactly `DESTROYED` or
`PROVEN_ABSENT`. `DESTROYED` requires a non-null allocated-object digest and provider response plus
independent reread proving the declared object was destroyed, revoked, closed, or deleted.
`PROVEN_ABSENT` requires a null allocated-object digest and provider response plus independent
reread proving the idempotent create transaction never committed and the exact service/run-tag
inventory contains no such object. The kind and create-idempotency digest must match the corresponding
entry in the selection attempt's closed planned-allocation manifest. Every pre-resource closure contains exactly one disposition
record for every allocation kind, including kinds never created. An unknown, duplicate, omitted, or
still-live allocation blocks closure; a generic empty environment-resource inventory cannot
substitute for these selection-plane records.

Each `Type: wait` boundary uses a private canonical
`skill-mesh/phase-is-c2e-wait-result/v1` record defined by
`tools/phase-is-environment/schemas/wait-result-v1.schema.json`. Its common object has exactly
`schema`, `c2e_run_id`, `provider_adapter_key`, nullable `environment_id`, `wait_result_id`, `kind`, `precondition_commit`,
`precondition_tree`, `issue_number`, `created_utc`, `expires_utc`, `outcome`, `wait_blocker_code`,
`underlying_receipt_manifest_sha256`, `details`, and `authenticator`; every object has
`additionalProperties=false`. `environment_id` is null only for `provider-selection` and
`pre-resource-closure` and is required for every later kind. `outcome` is exactly `PASS`,
`CLEANED_AFTER_ABORT`, or `BLOCKED`. `CLEANED_AFTER_ABORT` is legal only for
`pre-resource-closure` and `terminal-disposition`. `wait_blocker_code` is null for the
first two outcomes and otherwise exactly one of `OPERATOR_NOT_AUTHORIZED`, `PROVIDER_UNQUALIFIED`,
`VERSION_DRIFT`, `PROVISIONING_FAILED`, `LIVE_SMOKE_FAILED`, `WORKSTATION_DRIFT`, `AUTH_FAILED`,
`RECEIPT_INVALID`, `REMOTE_DRIFT`, `RETENTION_UNAVAILABLE`, or `DISPOSITION_INCOMPLETE`.

The closed `details` union is:

| `kind` | Exact required `details` properties | Forbidden / outcome rule |
|---|---|---|
| `provider-selection` | `provider_adapter_key`, `official_source_sha256`, `license_cost_authorization_sha256`, `private_provider_record_sha256`, `retention_contract_sha256`, `active_lifecycle_contract_sha256`, `publication_broker_contract_sha256`, `publication_broker_public_key_sha256`, `publication_broker_scope_sha256`, `emergency_build_toolchain_sha256`, `control_receipt_public_key_sha256`, `wait_public_key_sha256`, `emergency_broker_public_key_sha256`, `emergency_broker_scope_sha256`, `retention_public_key_sha256`, `retention_identity_scope_sha256`, `c5_shortener_preauthorization_sha256`, `control_wait_broker_auto_disable_utc`, `c5_shortener_auto_disable_utc`, `lease_max_seconds`, `missed_renewal_poweroff_max_seconds`, `writable_descendant_destroy_max_seconds`, `active_lineage_max_days`, `coordinator_before_sha256`, `coordinator_after_sha256` | publication-broker digests bind the external real-credential boundary, exact-body one-publication capability grammar, five-minute cap, ordered two-record policy, and direct-API egress denial; emergency toolchain digest binds exact compiler/linker/dumpbin/SDK paths, versions, signatures, hashes, flags/libraries, and root ACL facts; coordinator digests must be identical; maxima are at most 1,800, 300, 3,600, and 30; control/wait/broker and C5-shortener preauthorization automatic disable times are no later than `created_utc` plus 60 days and cannot be extended; the C5 digest binds a dormant one-use parent-only minting scope, not a credential; no environment, lease ID, lineage, or state field; key matches `^[a-z0-9]+(?:-[a-z0-9]+)*$`; only `PASS` or `BLOCKED` |
| `pre-resource-closure` | `selection_binding_kind`, `selection_binding_sha256`, `control_key_disposition_sha256`, `wait_key_destruction_intent_sha256`, `broker_authority_disposition_sha256`, `retention_key_identity_disposition_sha256`, `c5_shortener_preauthorization_disposition_sha256`, `replay_journal_disposition_sha256`, `emergency_journal_disposition_sha256`, `private_store_namespace_disposition_sha256`, `provider_authorization_disposition_sha256`, `empty_run_tag_inventory_sha256`, `original_failure_sha256`, `coordinator_before_sha256`, `coordinator_after_sha256` | binding kind is exactly `selection-attempt` before Step-4 PASS or `provider-selection-pass` afterward, and its hash must name the exact corresponding private object; environment is null; complete provider inventory for the `c2e_run_id` must be empty; every required disposition digest names the matching closed allocation-kind record and its state is `DESTROYED` or `PROVEN_ABSENT`; the signed record binds the exact immediate wait-key destroy request; only `CLEANED_AFTER_ABORT` or `BLOCKED`; never unblocks a later step or C5 |
| `provisioning` | `bootstrap_descriptor_sha256`, `resource_journal_head_sha256`, `final_descriptor_sha256`, `complete_tag_inventory_sha256`, `pre_resource_run_emergency_preflight_sha256`, `pre_resource_environment_emergency_preflight_sha256`, `s1_lineage_sha256`, `r0_lineage_sha256`, `signer_appliance_sha256`, `signer_isolation_sha256`, `run_volume_sha256`, `publication_broker_egress_sha256`, `lease_inventory_sha256`, `initial_state_sha256`, `final_state_sha256`, `maximum_lifetime_rule_sha256`, `lease_max_seconds`, `missed_renewal_poweroff_max_seconds`, `writable_descendant_destroy_max_seconds`, `active_lineage_destroy_deadline_utc`, `sealed_emergency_bundle_sha256`, `coordinator_before_sha256`, `coordinator_after_sha256` | descriptor/journal/inventory chain and both live empty-inventory emergency preflights must agree exactly; egress admits only the pinned broker route for publication and denies direct GitHub API access; exact maximums are at most 1,800, 300, and 3,600 seconds; the deadline is no later than first-resource `created_utc` plus 30 days and at least 24 hours before every immutable control/wait/broker/C5-shortener disable deadline; no reviewer/classification, disposition, or original-failure field; only `PASS` or `BLOCKED` |
| `live-smoke` | `r0_lineage_sha256`, `lease_inventory_sha256`, `smoke_receipt_sha256`, `signer_audit_sha256`, `provider_network_audit_sha256`, `publication_broker_smoke_sha256`, `producer_sidecar_sha256`, `reviewer_sidecar_sha256`, `parent_classification`, `initial_state_sha256`, `final_state_sha256`, `coordinator_before_sha256`, `coordinator_after_sha256` | publication smoke is non-publishing and proves exact-body/issue/ordinal/image/argv/expiry/replay/third-use denials plus capability revocation and direct-API egress denial; `parent_classification` is exactly `SUPPORTED`, `UNSUPPORTED`, or `CONTRACT_DRIFT`; no disposition/original-failure field; `PASS` requires `SUPPORTED` |
| `readiness-seal` | `candidate_commit`, `candidate_tree`, `receipt_blob`, `receipt_raw_sha256`, `private_evidence_manifest_sha256`, `review_manifest_sha256`, `root_gate_manifest_sha256`, `coordinator_before_sha256`, `coordinator_after_sha256` | candidate commit/tree must already equal remotely reread `origin/main`; receipt identities must match Step 31; no provisioning mutation, reviewer classification, disposition, or original-failure field; only `PASS` or `BLOCKED` |
| `terminal-disposition` | `entry_reason`, `disposition_receipt_sha256`, nullable `emergency_raw_record_sha256`, `safety_verification_kind`, `retained_inventory_sha256`, nullable `automatic_deletion_rule_sha256`, nullable `later_verification_owner_sha256`, `retention_public_key_sha256`, `retention_identity_scope_sha256`, `final_state_sha256`, nullable `original_failure_sha256`, nullable `pass_transition_failure_sha256`, `c5_eligible`, `coordinator_before_sha256`, `coordinator_after_sha256` | `entry_reason` is exactly `C4_PASS`, `C4_PASS_TRANSITION_FAILED`, `C2E_ABORT`, `C2N_ABORT`, `C2P_ABORT`, `C3_ABORT`, or `C4_ABORT`; `safety_verification_kind` is `SIGNED_CONTROL_RECEIPT` or `PROVIDER_RESPONSE_AND_REREAD`; the latter requires a non-null emergency record and later signed-bookkeeping proof; `C4_PASS` requires `PASS`, both failure fields null, and `c5_eligible=true`; `C4_PASS_TRANSITION_FAILED` requires `BLOCKED`, null original failure, a non-null transition-failure digest, `c5_eligible=false`, complete immediate destruction, and no retained inventory/rule/owner; every abort requires `CLEANED_AFTER_ABORT`, non-null original failure, null transition failure, and `c5_eligible=false`; every other `BLOCKED` result has `c5_eligible=false` |

Fields from another variant are absent, not nullable. A retained item requires both automatic-deletion
and later-verification digests; complete immediate destruction requires both null. Tenant,
subscription, resource, endpoint, machine, path, and credential identifiers remain private.
`authenticator` is exactly the §5.0 signed-object profile with domain
`skill-mesh/phase-is-c2e-wait-result-signature/v1`. The common `provider_adapter_key` must match the
provider-selection details value and every descriptor/status/marker binding. `created_utc` may not be
more than five minutes in the future; `expires_utc` is required
and no more than 24 hours later. Expiry blocks status advancement but does not invalidate later audit
of an already posted and remotely reread signature.

Only the parent coordinator may materialize a wait result. C2E.4 selects an external secret manager
capable of generating the exact non-exportable §5.0 RSA proof key; its private operation is
scoped only to this `c2e_run_id`, while its canonical SubjectPublicKeyInfo and SHA-256 are verification inputs. The
control-receipt, wait-result, and emergency-broker private authorities plus the credential-free C5-
shortener preauthorization have immutable provider-side automatic-disable times no later than 60
days after provider selection; the deadlines cannot be extended, reset, paused, or disabled. C2E.29
may begin only if all four deadlines remain at least 24 hours later than the active-
lineage destruction deadline; otherwise complete `pre-resource-closure` for the unused run and repeat
C2E.4 with new keys and `c2e_run_id`. Once `environment_id` is generated, every later result also binds it. The
parent supplies only an opaque signer handle through the process-only
`SKILL_MESH_C2E_WAIT_SIGNER_REF` environment variable—never a private key, token, or handle on the
command line, in Git, in a prompt, or in either guest. The same wait key signs Steps 4/29/30/32/33; a
  new C2E run uses a new key. After the last required marker is remotely reread (C5 on a successful
  PASS-retention route, Step 33 bookkeeping on abort or failed PASS transition), the parent disables/
  destroys the control, wait, and emergency-broker private
authorities and records their receipts; the public keys and signatures remain verifiable. Their immutable automatic-disable
deadlines remain a fail-safe if bookkeeping never runs. The separately scoped retention-verification
key/identity remains only through its scheduled absence proof under §5.1.

The parent first verifies the underlying provider/guest/reviewer evidence, writes one closed unsigned
facts input in the private artifact store, then invokes the sole materializer. `sign-wait` generates
`wait_result_id`, canonicalizes, signs through the external handle, and atomically writes the private
record; it refuses an existing output, weak/exportable/wrong-scope key, expired or extendable key,
expiry over 24 hours, unknown field/enum, coordinator fact mismatch, or evidence-manifest mismatch.
The parent removes the process variable, reopens the output, and invokes the no-write verifier:

```powershell
$env:SKILL_MESH_C2E_WAIT_SIGNER_REF = '<process-only-external-key-handle>'
try {
    python tools/phase_is_environment.py sign-wait `
      --kind '<provider-selection|pre-resource-closure|provisioning|live-smoke|readiness-seal|terminal-disposition>' `
      --facts '<absolute-private-closed-facts.json>' `
      --evidence-manifest '<absolute-private-receipt-manifest.json>' `
      --out '<absolute-private-wait-result.json>' `
      --format json
    if ($LASTEXITCODE -ne 0) { throw "sign-wait failed with exit code $LASTEXITCODE" }
}
finally {
    Remove-Item Env:\SKILL_MESH_C2E_WAIT_SIGNER_REF -ErrorAction SilentlyContinue
}
python tools/phase_is_environment.py verify-wait `
  --kind '<provider-selection|pre-resource-closure|provisioning|live-smoke|readiness-seal|terminal-disposition>' `
  --record '<absolute-private-wait-result.json>' `
  --public-key '<absolute-private-public-key.der>' `
  --format json
```

Exit `0` permits the parent to publish provider-selection/provisioning/live-smoke/readiness status
only for `PASS`. A pre-resource closure publishes only `DONE — CLEANED_AFTER_ABORT` and terminates
that `c2e_run_id`. For terminal disposition it publishes `DONE — PASS`, `DONE —
CLEANED_AFTER_ABORT`, or `BLOCKED — C4 PASS RETENTION TRANSITION FAILED`; only `PASS` with
`c5_eligible=true` can unblock C5. Safety may be complete on the third route while C2E.33 and C5
remain blocked. After private
verification, the parent posts the exact marker, paginates and remotely rereads the selected comment,
then commits/pushes a status record that binds the returned comment ID/URL/time/body hash and exact
wait-result SHA-256. Step 32 first pushes the already-reviewed Step 31 candidate with expected-old
protection, rereads that exact object as `origin/main`, and only then signs/posts its readiness-seal;
the later status-only commit records the returned marker facts. Exit `2` or `3`, or outcome `BLOCKED`,
leaves the step blocked and, once an environment ID or provider resource exists, invokes/escalates
terminal disposition. The sole exception is a `terminal-disposition:BLOCKED` record that already
proves complete destroy-only safety: it records the blocker and stops without recursion; incomplete
safety still re-enters/escalates cleanup. The private
record, signer handle, and provider facts never enter Git, an issue, or a child prompt. A producer,
provider success string, or unauthenticated operator note cannot advance the plan.

For `pre-resource-closure`, safety ordering is self-closing: first verify the exact selection-attempt
or provider-selection-PASS binding, prove the run tag has empty provider inventory, and materialize
all eight exact allocation-disposition records, each proving the planned allocation was destroyed or
never committed; next sign the closure record with an exact wait-key destruction intent; then immediately
execute/reread that intent and destroy the wait key. Posting may occur afterward because it needs only
the already-signed record and public verification material. The committed closure status binds the
actual wait-key destruction receipt. GitHub or Git outage may delay marker/status bookkeeping but
never key or allocation closure.

The remote marker body is exact CR-free UTF-8 with eight LF separators and no trailing LF:

```text
PHASE_IS_C2E_WAIT_RESULT_V1
C2E_STEP=<4|29|30|32|33>
C2E_WAIT_KIND=<provider-selection|pre-resource-closure|provisioning|live-smoke|readiness-seal|terminal-disposition>
C2E_WAIT_OUTCOME=<PASS|CLEANED_AFTER_ABORT|BLOCKED>
C2E_WAIT_RESULT_SHA256=<64 lowercase hex>
C2E_WAIT_PUBLIC_KEY_SHA256=<64 lowercase hex>
C2E_PROVIDER_ADAPTER=<provider_adapter_key>
C2E_ENVIRONMENT_ID=<c2e- plus 32 lowercase hex|->
C2E_WAIT_BLOCKER=<closed wait_blocker_code|->
```

Steps 4/29/30/32 post only to #162; Step 33 posts only to #143. Both Step-4 kinds use `-` for the
environment ID; every later marker uses the bound ID. Every published marker uses the selected
`provider_adapter_key`; a failure before selection or before the atomic wait-key commit remains the
local unauthenticated stop defined in Step 4 and publishes no marker. The parent records returned numeric comment ID,
URL, `created_at` UTC, exact body SHA-256, issue, and step in committed status. On every read it
enumerates comments with `per_page=100` and explicit pagination to exhaustion, rejects duplicate IDs,
repeated pages, or malformed bodies, and selects the unique maximum `(created_at UTC, numeric comment
ID)` among exact-header records for the same issue, step, public-key, selected-provider-adapter, and
environment tuple. The selected record must match the signed wait result's
`provider_adapter_key`; immediately after posting it must also equal the API-returned comment ID and
exact reread body. Any newer `BLOCKED` marker for that full tuple blocks; an older PASS cannot be reused. The next `/build-phase --steps ...`
invocation starts only after private signature verification, authoritative remote reread, and the
subsequent committed/pushed status agree.

The validator has a non-mutating production entry point:

```powershell
python tools/phase_is_environment.py verify `
  --descriptor '<absolute-private-descriptor.json>' `
  --receipt '<absolute-redacted-receipt.json>' `
  --format json
```

Exit `0` means exact match and READY, exit `2` means invalid input/authorization boundary, and exit
`3` means environment drift or failed readiness. It writes nothing. Mutation lives only in named
guest-admin subcommands behind the authenticated connector, each requires its matching private
descriptor, active lease, single-use parent grant, and expected prior-state digest and refuses the
coordinator's recorded machine identity.

### 5.7 Git, artifact, and review serialization

The coordinator is the only Git integration writer:

1. Fetch and record the expected `origin/main` object before a step.
2. A producer edits one isolated local worktree. The guest checks out or receives only a
   content-addressed snapshot of that exact candidate through the connector.
3. Guest output returns as a declared content-addressed bundle; the coordinator verifies byte count,
   SHA-256, candidate commit/tree, and receipt chain before import.
4. A fresh reviewer sees immutable Git objects and a fresh R0 descendant, never the producer context
   or writable guest.
5. The parent authenticates and classifies the reviewer sidecar. The producer cannot write that
   sidecar or obtain the verdict key.
6. The coordinator integrates one reviewed candidate, reruns applicable gates, fetches the target
   ref, and pushes only with an expected-old-object lease. Remote movement is a hard serialization
   conflict; never force-push or silently rebase.
7. Only after the candidate commit/tree is remotely reread may the parent materialize, post,
   paginate, and reread its exact seal. A later status-only commit may bind the returned comment
   facts; it may not change the sealed candidate. Remote movement remains a hard serialization
   conflict throughout.

For waits 4 and 29, the parent first pushes/rereads the exact reviewed preceding code span (Steps
1–3 or 5–28) with expected-old protection; the wait result's `precondition_commit/tree` names that
remote object. Waits 30 and 33 likewise begin from the already-pushed/reread Step-29 status or C4
candidate. Those waits create external evidence, not a new code candidate, so their marker comes next
and a status-only commit follows. Step 32 keeps its explicit receipt-candidate push/reread, marker,
then status-only ordering. Emergency or pre-resource safety never waits on Git: later bookkeeping
binds the last remotely reread precondition plus the private original-failure/raw-safety hashes and is
a disposition record, not a retroactive code seal.

The guest has no Git or direct GitHub credential and never pushes `main`, merges, or posts stage
seals. The sole exception is C4's already-required certified `evidence-upload` mode, whose two
separate invocations each receive one process-only exact-body publication-broker capability named
`GH_TOKEN`; only the external broker reaches GitHub and holds the real credential.

### 5.8 Handoffs into C2N–C5

- **C2N:** runs its discovery against the sealed guest, not this workstation. Its typed
  pre-implementation manifest includes the C2E receipt Git blob/raw hash and environment ID as an
  existing input, plus the guest complete tool/host candidate inventory and publisher/policy/boot
  facts. C2N alone applies the deterministic selection rule. No future binary hash enters. The parent
  acquires the lease, creates/attaches/powers the sole descendant, starts a new connector session,
  runs only read-only operations, and powers it off; no producer receives infrastructure authority.
- **C2P:** runs on the coordinator after C2N's three blobs and #162 seal. Every C3 step names whether
  its source edit is coordinator-local and which native/security gate is guest-only. The guest
  re-fetches the exact sealed C2P commit before C3.
- **C3:** fresh Terra producers edit isolated coordinator worktrees. All native builds, signatures,
  policy admission, kernel load/unload, and driver-sensitive negatives run only in serialized R0
  descendants. The parent owns lease/restore/power/attachment and issues single-use grants for the
  C2P-declared admin action IDs; a producer supplies inputs but cannot invoke the channel. The final
  candidate lock adds exact output hashes/signatures and revalidates the unchanged C2E/C2N facts.
- **C4:** runs the immutable C3 packet in one attended R0 descendant. That guest's standard profile is
  the real profile for UAT purposes and is never a cleanup target. On the encrypted run volume, the
  combined install/project, config, build, and export roots are four direct children of one validated
  common parent; all are outside Git/profile and receipt-bound.
- **C2E.33/C5:** after either C4 PASS or any terminal stop, revoke guest process/host and connector
  credentials first, retain active parent provider authority through complete disposition, then revoke
  it last;
  power off, enumerate and disposition every descendant/snapshot/disk, and destroy or time-bound
  quarantine the runnable lineage. On PASS, destroy OS/S1/R0/run descendants and retain the detached
  encrypted run volume through C5 because it contains the live redacted export root and may contain
  private deleted-block remnants. C2E.33 atomically arms an absolute fail-safe deletion at C4 PASS plus
  120 days. C5 uses the separate Step-4 preauthorized, newly minted one-hour identity to atomically
  shorten that to the earlier of signed C5 shortening authorization plus 90 days or the existing hard
  cap, then revokes it; the cap is never extended. If the C4 PASS transition cannot be verified, the
  emergency broker destroys the complete lineage and records a blocker without revising the C4 verdict
  or enabling C5. On abort, default to destruction; any operator-selected private-
  evidence quarantine ends at the earlier of terminal-stop plus seven days or the original complete-
  lineage deadline, stays powered off and non-runnable, and has automatic deletion and later absence
  verification. C5
  records the disposition without exposing provider-private data and cannot start until C2E.33
  returns PASS.

## 6. Design Decisions

### C2E-D1 — one execution guest plus one isolated signer appliance

One measured execution guest builds, loads, and exercises the candidate through C2N/C3/C4. A separate
run-scoped appliance signs exact independently reviewed object hashes and never executes candidate
code. This keeps the untrusted kernel boundary away from the private publisher key without adding a
second driver build toolchain. The coordinator performs only §5.5A's pinned unsigned user-mode
emergency-safety build; it never builds, signs, loads, or tests the product driver.

### C2E-D2 — provider-neutral contract, explicitly selected concrete adapter

The repository defines provider-neutral capabilities and receipts. C2E.4 is a machine-stopping
operator gate that selects and authorizes one provider/retention route; C2E.5–7 then implement and
test that provider's concrete adapter. Provider IDs, endpoints, and credentials remain outside Git.
Absence of an atomic lease, complete lineage inventory, authenticated connector, or authorized
provider is a stop, not permission to add a host share or defer provider choice until provisioning.

### C2E-D3 — the current workstation is coordination plus one safety-build exception

No C2E command may install or change certificates, Code Integrity/App Control/AppLocker policy,
Secure Boot, BCD, firmware, Windows features, SDK/WDK, services, or host applications here. A guest
identity mismatch is checked before a mutating subcommand and fails closed. The sole local build is
the existing-toolchain, unsigned, user-mode emergency launcher under §5.5A; it cannot consume WDK or
candidate-driver inputs and makes no protected workstation change.

### C2E-D4 — capable parent dispatch stays outside the guest

Fresh Terra contexts come from the supported Codex collaboration host already proven by C0. Ordinary
Codex CLI inside the guest is not treated as an isolated-context primitive. The guest is an execution
target; the coordinator remains the build-step parent and final classifier.

### C2E-D5 — publisher admission resolves the future-hash cycle

A pre-existing publisher rule can admit later signed bytes without naming their future hash. C2E and
C2N freeze the signer and policy; C3 freezes final bytes. Hash-only admission before implementation is
circular and therefore not selected.

### C2E-D6 — App Control is unsigned but enforced

Secure Boot is off for this disposable kernel test-signing route. The policy remains unsigned and
enforced with UMCI, compensated by parent-controlled elevation grants, standard-user execution,
immutable hashes, canaries, powered-off snapshots, one writable descendant, and independent replay.
This does not claim production-grade tamper resistance.

### C2E-D7 — parent-controlled grants, isolated-appliance signing

Producer and reviewer contexts do not receive administrator credentials, connector/provider
credentials, or the publisher key. The non-exportable publisher leaf remains only in the separate
non-snapshotted signer appliance; the parent controls single-use, committed, hash-bound guest-admin
and signing grants and authenticates their receipts. Signing or loading a candidate never grants the
producer review or final-verdict authority.

### C2E-D8 — one Git writer and one narrow C4 publication exception

The coordinator owns Git integration and stage seals. Guest Git credentials are unnecessary. C4's
certified evidence uploader is the only guest-originating GitHub write because the accepted UAT
requires its exact process/environment proof. Even there, the real GitHub credential remains in the
external broker; each uploader process receives only the separate exact-body capability defined in
§5.2, and the guest has no direct GitHub API route.

### C2E-D9 — S1 separates reusable tools from run-specific trust

S1 contains the patched OS and toolchain but no run identity or trust policy. Each independent run
creates a new signer appliance/publisher plus public-policy/test-signing R0 lineage. R0 has only the
public chain. This avoids silently reusing a stale signer or admission rule across changed candidates.

### C2E-D10 — one common-parent run volume survives runnable-lineage disposal

The frozen UAT requires the combined install/project, config, build, and `<evidence-export>` roots to
be four direct children of one common parent. They therefore live together on one encrypted run
volume; the export is not a separate disk, mount, or reparse point. C4 cleanup deletes only the three
disposable roots. After remote evidence verification, C2E.33 destroys the runnable OS/snapshot
lineage and retains the detached run volume as a private secure artifact because deleted private-root
bytes can remain in block slack. Provider lifecycle automation first enforces an absolute deletion
  at C4 PASS plus 120 days; C5 shortens it to the earlier of signed shortening authorization plus 90
  days or that cap. A named
retention verifier later records absence. No actor may extend, pause, disable, or replace that cap
with a later deadline.

### C2E-D11 — no accepted Phase IS owner changes during planning

The core route explicitly sealed no authoritative phase-plan amendment. C2E changes only the
subordinate completion runbook and mutable status pointer. The frozen UAT remains unchanged until its
already-authorized C3 substitutions.

### C2E-D12 — exact versions are frozen at execution, not inferred from PATH

The planning baseline is SDK `10.0.28000.2705`, WDK `10.0.28000.2526`, and Windows 11 26H1 build
`28000.2804`, as verified on 2026-08-30. C2E.4 rereads the official Microsoft sources and records any
new supported pairing before provisioning; equal build-family values are required while QFE values
may differ. Once S1 is sealed, C2N's complete enumeration and deterministic rule govern. Automatic
upgrades are disabled for the run, and PATH order never selects a tool.

### C2E-D13 — connector authority is authenticated, leased, and replay closed

Provider-native short-lived authorization selects one resource and operation set. Provider-control
operations are independently reread and signed by the parent-only control-receipt key. Guest-data
operations use a separate parent-generated connector-session HMAC key; it never establishes control-
plane or elevation authority. `exec-admin` also requires a distinct asymmetric parent grant whose
private key never enters either machine. Atomic lease, complete environment inventory, expected-prior-state,
role, plane, expiry, monotonic sequence, and unique request IDs are checked before any action. Restore
creates a new connector session and grant key; every old request/grant must fail. Terra children receive
neither provider credentials nor private control/grant/wait/verdict keys.

### C2E-D14 — terminal disposition is a required stage, not best-effort cleanup

C2E.33 runs after C4 PASS and on every terminal C2E/C2N/C2P/C3/C4 abort after an environment ID or
provider resource exists. Revoke guest process/host and
  connector secrets first; retain the narrowly scoped active parent provider identity through power-off,
complete inventory, destruction/quarantine, lease release, and receipt verification; revoke provider
identity last. The default is destruction of every runnable descendant, snapshot, and OS disk. An
operator may instead authorize only a bounded, powered-off, non-runnable quarantine with a named
owner and provider-native TTL/lifecycle deletion rule; the failure deadline is the earlier of seven
days after the terminal stop or the original complete-lineage 30-day deadline.
The PASS run volume first receives an automatic fail-safe deletion rule at C4 PASS plus 120 days;
  C5 mints a new one-hour identity under the Step-4 preauthorization and shortens it to the earlier of
  signed shortening authorization plus 90 days or that cap, then revokes that identity. A separate
  named retention verifier
must later record absence. After C4 PASS, C5 cannot begin until the immediate disposition receipt and
  automatic-deletion rule pass. A failed/ambiguous PASS transition enters the emergency destroy-only
  route, records `BLOCKED`, and cannot enter C5. After an abort, successful cleanup records
  `CLEANED_AFTER_ABORT` and
preserves the original failure; it never makes C5 eligible.

### C2E-D15 — connector possession cannot mint elevation

Guest-data HMAC authenticates a session, not the parent. Each privileged action therefore requires a
separate RSA-PSS grant signed by an ephemeral parent-only private key and verified in the guest with
only the public key. Grants bind the exact session, request, lease, state, action, inputs, candidate,
expiry, and one-time sequence; restore rotates the pair and invalidates every old grant.

### C2E-D16 — non-exportability is paired with machine isolation

The run publisher's non-exportable leaf is usable only by the dedicated signer service under a
protected private-key DACL on an appliance that never runs candidate code and has no route from the
execution guest. The service accepts one valid parent grant for one independently reviewed object.
Readiness binds appliance/network/DACL/service/channel digests, and planted negatives plus external
provider/signer audit prove producer, reviewer, ordinary guest, and a signed kernel escape canary
cannot reach or use the signing authority.

### C2E-D17 — provider control and guest data have different authenticators

Power, snapshot, destroy, lease, qualification, and complete inventory are provider-control facts:
the parent validates the provider response, performs an independent API reread, and signs the
canonical result with a per-execution external control-receipt key. Guest facts/transfers/actions use
the separate connector-session HMAC. A tagged-union schema prevents a guest MAC from being accepted as
proof of provider control state.

### C2E-D18 — active expiry and emergency cleanup are independent safety rails

Provider-native lifecycle rules bound every active run even if the coordinator disappears: lease at
most 30 minutes, power-off within five minutes of missed renewal, writable-descendant destruction
within 60 minutes, and complete-lineage destruction within 30 days of first creation. A reviewed,
content-addressed emergency bundle can disposition the lineage directly from the private descriptor
without Git, tests, build-phase, or GitHub; repository and issue bookkeeping occurs only after safety.

### C2E-D19 — kernel entry makes that descendant untrusted

A candidate is independently reviewed as source and unsigned object before the parent grants signing.
After kernel entry, guest-local evidence is not claimed to resist an intentionally malicious driver;
the descendant contains no signing/provider/Git/verdict authority, externally controlled provider and
signer facts remain authoritative, and the descendant is destroyed. Claims that cannot be externally
corroborated or accepted as attended behavior of the reviewed bytes stop instead of self-certifying.

## 7. Build Steps

This plan is deliberately discontinuous. `Type: wait` is used for each provider/publication boundary
and is completed by the parent outside `/build-phase`; never dispatch a wait step to build-phase or
let it be deferred/skipped. After its evidence, remote marker, and committed status are verified, a
fresh invocation starts at the next code span. Never run this file without `--steps`.

### Exact execution quickstart

These commands are future instructions only; this planning run executes none of them:

```text
/build-phase --plan documentation/phase-is-disposable-c2n-c4-environment-plan.md --steps 1,2,3
# STOP: parent pushes/rereads exact Steps 1–3 candidate, then completes provider-selection wait Step 4.
# No environment ID or provider resource is created.
/build-phase --plan documentation/phase-is-disposable-c2n-c4-environment-plan.md --steps 5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28
# STOP: parent pushes/rereads exact Steps 5–28 candidate, then completes attended provisioning wait Step 29.
# STOP: the parent completes live substrate/fresh-context wait Step 30.
/build-phase --plan documentation/phase-is-disposable-c2n-c4-environment-plan.md --steps 31
# STOP: build-phase has created only the local reviewed readiness candidate. The parent completes
# remote push/seal/status wait Step 32 outside build-phase. C2N starts only in a fresh context.
# After C4 PASS, or immediately after any terminal stop once an environment ID or provider resource
# exists, the parent completes disposition wait Step 33 directly; never dispatch Step 33 through
# build-phase.
```

**Pre-resource terminal path:** after a Step-4 `PASS`, any stop before Step 29 generates
`environment_id` runs §5.6 `pre-resource-closure` immediately. This path uses the Step-4 selected
provider/IAM, journal, store, and secret-manager control APIs directly; it does not wait for later
adapter code. It proves the immutable `c2e_run_id` tag query empty, closes every allocation except the
wait key, signs the closure plus exact wait-key destruction intent, destroys/rereads the wait key, and
only then performs marker/status bookkeeping. The run ID and its allocations are never reused.

**Direct terminal path (safety first, bookkeeping later):** once Step 29 has generated an
`environment_id` or created any provider resource, do not invoke `/build-phase`, pytest, Git, or
GitHub before making the environment safe on a terminal stop. Use the immutable self-contained
launcher/runtime bundle, bootstrap descriptor, and resource inventory journal sealed by Step 29:

```powershell
$env:SKILL_MESH_C2E_PROVIDER_BROKER_REF = '<process-only-image-bound-broker-handle>'
try {
    & '<absolute-private-sealed-c2e-bundle>\phase-is-emergency-launcher.exe' `
      emergency-dispose `
      --bootstrap-descriptor '<absolute-private-bootstrap-descriptor.json>' `
      --resource-inventory-journal '<absolute-private-resource-inventory-journal>' `
      --entry-reason '<C4_PASS_TRANSITION_FAILED|C2E_ABORT|C2N_ABORT|C2P_ABORT|C3_ABORT|C4_ABORT>' `
      --expected-environment-id '<c2e- plus 32 lowercase hex>' `
      --out '<absolute-private-emergency-disposition.json>' `
      --format json
    if ($LASTEXITCODE -ne 0) { throw "emergency-dispose failed with exit code $LASTEXITCODE" }
}
finally {
    Remove-Item Env:\SKILL_MESH_C2E_PROVIDER_BROKER_REF -ErrorAction SilentlyContinue
}
```

The broker releases provider authority only after attesting the exact launcher image/file identity,
manifest hash, clean environment, and sanitized DLL search; the executable is single-file/self-
contained and resolves no PATH interpreter, external import, plugin, or current-directory DLL. This
direct parent-only path uses only the last reviewed sealed bundle/descriptor and provider API. It
ignores repository cleanliness, test state, branch state, GitHub availability, and build-phase
preflight; it cannot edit repository files or this workstation's security/boot state. It revokes
guest/connector secrets, powers off, inventories, destroys or applies the already-authorized bounded
quarantine, releases the lease, verifies the provider-authenticated response plus independent reread,
and revokes provider identity last. On C4 PASS, Step 33 first attempts Step 25's proof-bound atomic
PASS transition as the sole retention mutation. A verified idempotent success never calls
`emergency-dispose` or abort-only `dispose-v1`. If the normal identity is unavailable before that
success, or the provider returns a failed/ambiguous transition, Step 33 immediately invokes
`emergency-dispose` with `C4_PASS_TRANSITION_FAILED`; that entry is destroy-only, removes the run
volume and every rule with the rest of the lineage, forbids quarantine/retention, preserves the C4
PASS plus transition failure, and leaves C5 blocked. It is also outside build-phase.
Control-receipt or wait-signer unavailability may delay proof but may not delay those safety effects:
the emergency command preserves the provider-authenticated response and independent reread as private
raw evidence, and later bookkeeping rereads current provider state and creates the canonical signed
control/disposition/wait records. An unsigned emergency report cannot advance status or C5.
Exit `0` means the safety disposition completed; `2` means invalid/private authorization input; `3`
means incomplete disposition and requires the provider's emergency control channel while preserving
the blocker. Only after safety is established does the parent run Step 33's wait-result/status/#143
bookkeeping when Git/GitHub are available. Bookkeeping failure never reverses a completed disposal.

Install applicability: no code step installs a workstation dependency; guest/appliance provisioning
occurs only in wait Step 29. Build applicability: Step 21 creates the reviewed native builder/shell;
Step 23 integrates, double-builds, and proves the final private self-contained executable/manifest;
distribution builds are not applicable because no skill
input changes, while `python tools/gen_manifest.py` must remain a no-diff gate. This repository has no
separate lint, typecheck, or development-server command for this plan. Every code step runs focused
tests and repo-root `python -m pytest`; Step 31 repeats the qualifying detached root gate on its
immutable local candidate.

### Step 1: C2E.1 — lock environment evidence schemas and the no-write verifier

- **Status:** PENDING / NOT AUTHORIZED FOR EXECUTION
- **Problem:** no strict machine record currently distinguishes the disposable execution/signer
  topology from this workstation or closes readiness/disposition/redaction facts.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase_is_environment.py`,
  `tools/phase-is-environment/schemas/environment-bootstrap-v1.schema.json`,
  `tools/phase-is-environment/schemas/environment-descriptor-v1.schema.json`,
  `tools/phase-is-environment/schemas/emergency-build-toolchain-v1.schema.json`,
  `tools/phase-is-environment/schemas/readiness-v1.schema.json`,
  `tools/phase-is-environment/schemas/disposition-v1.schema.json`,
  `tests/phase-is-environment/test_environment_contract.py`,
  `tests/phase-is-environment/fixtures/environment/**`
- **Existing context:** preserve every C2V/C2A object, the accepted phase-plan blob, and frozen UAT blob. The production verifier is read-only, closed-schema, and has exactly one repository caller; private provider descriptors and raw evidence remain outside Git.
- **Produces:** canonical bootstrap/final-descriptor/readiness/disposition and private emergency-
  toolchain-manifest schemas, deterministic no-write `verify`
  CLI, redaction allowlist, closed exit/verdict vocabulary, signer-appliance/execution-guest topology,
  and planted-invalid evidence fixtures.
- **Done when:** cross-runtime RFC 8785-plus-LF golden vectors and strict pre-parse rejection cover
  escapes, Unicode, duplicate names, invalid surrogates, numeric syntax, and safe-integer edges; RSA
  profile and signed-object domain vectors are byte-exact; a fully populated synthetic READY fixture
  passes without a byte change; planted negatives reject unknown fields, private locators/secrets, coordinator identity, missing signer
  isolation, malformed lineage/inventory, policy/boot/tool drift, and invalid disposition with stable
  nonzero codes; focused tests, repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** C2A

### Step 2: C2E.2 — build the authenticated wait/status/remote-marker protocol

- **Status:** PENDING / BLOCKED ON 1
- **Problem:** provider/operator completion cannot advance a stage through prose, an unsigned file,
  or an issue comment whose identity/selection is ambiguous.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/schemas/selection-attempt-v1.schema.json`,
  `tools/phase-is-environment/schemas/selection-allocation-plan-v1.schema.json`,
  `tools/phase-is-environment/schemas/selection-allocation-disposition-v1.schema.json`,
  `tools/phase-is-environment/schemas/wait-result-v1.schema.json`,
  `tools/phase-is-environment/wait/**`, `tests/phase-is-environment/test_wait_protocol.py`,
  `tests/phase-is-environment/fixtures/wait/**`
- **Existing context:** implement §5.6's parent-only external RSA materializer, 24-hour result expiry,
  exact marker bytes/pagination/selection, and post-marker committed-status ordering. This step never
  calls a provider, GitHub, or a guest in tests.
- **Produces:** closed pre-allocation selection-attempt, eight-kind allocation-plan, and
  per-planned-allocation disposition schemas,
  `sign-wait`, no-write `verify-wait`,
  exact marker parser/selector, deterministic status-update input, and planted wrong-key/stale/replay/
  pagination/duplicate fixtures.
- **Done when:** tests prove canonical closed bytes, the exact §5.0 wait signature domain/profile,
  external opaque-handle ingress, per-run key
  lifecycle, exact selection-attempt/PASS cleanup-binding union, complete eight-kind
  `DESTROYED|PROVEN_ABSENT` allocation disposition with planted partial-allocation states, exact
  outcome/kind unions, strict marker grammar, pagination to exhaustion, unique maximum
  selection, wrong-adapter and returned-comment-ID mismatch rejection, remote-drift refusal, and that
  status cannot advance before signed-record/provider/marker agreement plus signature+marker reread;
  focused tests, repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 1

### Step 3: C2E.3 — build the coordinator non-mutation fact collector

- **Status:** PENDING / BLOCKED ON 2
- **Problem:** “the workstation was unchanged” is not evidence without one closed before/after fact
  schema and a collector that cannot mutate the measured surfaces.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/schemas/coordinator-facts-v1.schema.json`,
  `tools/phase-is-environment/coordinator-facts/**`,
  `tests/phase-is-environment/test_coordinator_facts.py`,
  `tests/phase-is-environment/fixtures/coordinator-facts/**`
- **Existing context:** the private fact set covers machine-identity digest; certificate-store public
  state; Code Integrity/App Control/AppLocker policy; Secure Boot, BCD, firmware; Windows features;
  installed SDK/WDK/tool/application state; and collector binary/hash. Raw machine/path/user values
  remain private; only canonical SHA-256 digests enter waits/readiness.
- **Produces:** `snapshot-coordinator` read-only collector, closed canonical fact schema, before/after
  comparator, coordinator-exclusion digest, and mutation-attempt fixtures.
- **Done when:** static tests prove no registry/service/certificate/BCD/feature/package mutator is
  reachable; synthetic before/after equality passes; every changed protected field fails with an exact
  code; output is canonical/private/redactable; focused tests, repo-root `python -m pytest`, and
  `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 2

### Step 4: C2E.4 — select and authorize the provider and retention route

- **Status:** PENDING / BLOCKED ON 3 AND SEPARATE OPERATOR EXECUTION AUTHORIZATION
- **Problem:** a provider-neutral contract is not executable until one provider, image/license,
  authentication route, artifact store, exact-body publication broker, retention owner, and cost
  boundary are explicitly qualified and authorized.
- **Type:** wait
- **Issue:** #162
- **Files:** `documentation/phase-is-disposable-c2n-c4-environment-plan.md`, `plan.md`; the
  provider qualification/authorization and signed wait records remain private external evidence; the
  exact public marker is posted to #162
- **Existing context:** generate `c2e_run_id`; capture the coordinator-before fact set; reread the
  official Windows release, SDK, WDK, provisioning, test-signing,
  and App Control sources. Require provider-native short-lived identity, atomic conditional lease,
  complete descendant inventory, encrypted storage, secret injection, outbound allowlisting, every
  §5.1 operation, transactional external replay/idempotency journal, isolated signer-appliance route,
  image-bound emergency credential broker, external secret manager for separate control-receipt,
  wait-signing, and retention-verification keys/identities, a dormant one-use parent-only C5-
  shortener preauthorization, an external publication broker that retains the real GitHub credential
  and mints only the exact-body capabilities in §5.2, and
  provider-native TTL/lifecycle deletion plus later absence verification. The active-lifecycle maxima
  are lease 30 minutes, missed-renewal power-off five minutes, writable-descendant destruction 60
  minutes, and complete-lineage destruction 30 days after the first resource; the operator may
  shorten but not extend, disable, pause, or reset them. Seal the private selection-attempt object,
  then create and sign-test the wait key as the first atomic/reconcilable allocation; no second
  allocation is legal until that transaction proves a usable signer. This wait may otherwise allocate only the declared
  external selection-plane keys, journals, private-store namespace, and provider authorization that
  its pre-resource closure can exhaustively retire; it creates no environment ID, execution/signer
  resource, provider compute/storage/network object, or machine security-state change.
- **Produces:** an operator-selected provider/Windows-license/artifact-retention route; public
  non-secret `provider_adapter_key`; concrete provider-control authentication, independent-reread,
  control-receipt signing, wait-result signing, automatic-deletion, and key-destruction mechanisms;
  exact signed private `emergency_build_toolchain_sha256` plus process-only retrieval route;
  publication-broker contract/public-key/scope digests and direct-GitHub-API egress-denial contract;
  non-extendable control/wait/emergency-broker/C5-shortener automatic-disable times no later than 60
  days after this selection;
  owner/deadlines for active lineage, PASS retention, and failure quarantine; resource/cost ceiling;
  authenticated private `provider-selection` wait result; committed status digest; and the exact #162
  marker; no product code artifact.
- **Done when:** before the operator action, the parent pushes/rereads the exact reviewed Steps-1–3
  candidate with expected-old protection and binds it as the wait precondition. The operator explicitly accepts the provider, adapter key, licensing/cost, current
  supported OS/SDK/WDK baseline, exact signed private emergency compiler/linker/dumpbin/SDK/flag/
  library/environment/ACL manifest digest and process-only retrieval route,
  identity mechanism, lease/inventory/idempotency guarantees, private
  evidence store, signer-appliance isolation, image-bound emergency broker, exact-body publication
  broker and direct-API egress denial, separate external
  control/wait/emergency-broker/retention authorities, the credential-free C5-shortener
  preauthorization and lifecycle, automatic
  deletion/verification mechanism, immutable active-lifecycle maxima, C4-plus-120-day hard cap with a
  signed-C5-authorization-plus-90-day shortening rule, failure limit at the earlier of seven days after stop or the
  original active-lineage deadline, named disposition/verification owner, and the immutable 60-day
  control/wait/broker/C5-shortener fail-safe; then the parent verifies the wait result and independent provider facts,
  posts the exact marker, paginates and remotely rereads the selected #162 record, and only afterward
  commits/pushes this step's exact DONE digest/key plus returned comment facts. If qualification
  blocks/fails before the atomic wait-key transaction commits, prove the run-tag/key inventory empty,
  return only a local unauthenticated blocked stop, and publish/commit nothing. Once that transaction
  commits, the working wait signer is present before every later allocation. Do not
  publish/commit a provider-selection result first: sign and preserve the blocker privately with that
  wait key, immediately run `pre-resource-closure` bound to the selection-
  attempt (or the provider-selection PASS after this step completed), destroy/reread every committed
  allocation, prove every never-committed planned allocation absent through its exact disposition record, and retire the
  wait key, then publish/record only the terminal closure as §5.6 requires. A Step-4 `PASS` also
  allocates external authorities, journals, and private-store state even though it creates no
  environment. On every later stop while both `environment_id` and
  every provider resource are absent, the parent must immediately execute §5.6 `pre-resource-closure`: prove
  the `c2e_run_id` tag inventory empty; close/revoke all control, broker, retention, C5-shortener,
  journal, store, and
  provider-auth allocations; sign the closure with its exact wait-key destruction intent; destroy and
  reread the wait key; then publish/record `DONE — CLEANED_AFTER_ABORT` when GitHub is available. It
  may not leave the Step-4 PASS open, reuse its run ID/keys, or continue to provisioning.
- **Flags:** none
- **Depends on:** 3

### Step 5: C2E.5 — build provider authentication and durable replay journals

- **Status:** PENDING / BLOCKED ON 4
- **Problem:** no provider mutation is safe if request authentication, idempotency, or crash replay
  depends on one coordinator process.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/schemas/connector-request-v1.schema.json`,
  `tools/phase-is-environment/schemas/connector-result-v1.schema.json`,
  `tools/phase-is-environment/schemas/control-journal-v1.schema.json`,
  `tools/phase-is-environment/schemas/resource-inventory-journal-v1.schema.json`,
  `tools/phase-is-environment/providers/<provider_adapter_key>/auth/**`,
  `tests/phase-is-environment/test_provider_auth_journals.py`,
  `tests/phase-is-environment/fixtures/provider-auth-journals/**`
- **Existing context:** implement only C2E.4's selected adapter. This step owns `qualify`, the closed
  request/response authenticator union, normal control replay journal, and resource-inventory journal
  foundation from §5.1. Private IDs/credentials/keys remain external. Emergency tags remain disabled
  until Step 22's broker gate.
- **Produces:** provider-native short-lived auth; parent RSA request/receipt binding; retention read-
  only and schema-closed emergency variants; durable transaction/idempotency/restart reconciliation;
  bootstrap-bound resource-journal initialization; and closed errors.
- **Done when:** canonical vectors prove the exact response schema/result-property unions and the
  domain/direction/kind/length-delimited request and full-outer-response byte contracts for every
  authenticator variant; tests recompute `request_sha256` from the retained sent-request bytes and
  prove malformed UTF-8, duplicate-name, noncanonical, missing-outer-field, unknown-operation, and
  unresolvable-response-authority inputs receive only the fixed empty transport rejection with no
  connector result/action/state change, while a routable and validly authenticated request with an
  invalid operation-parameter union computes its proof from exact `routable_payload_bytes`, binds
  exact `routable_request_bytes`, and receives authenticated `INVALID_SCHEMA` before action;
  reject a validly re-proved response bound to another request, a changed outer
  response field, metadata field, payload hash, proof encoding, direction, or domain, plus forged/
  wrong-plane/expired/duplicate/reordered requests before action;
  crash-before-send/after-send/before-record cases reconcile without duplicate effects; journal
  omission/rollback/tamper and untagged-resource fixtures block; emergency tags cannot invoke an
  operation before Step 22's image-bound broker gate; focused tests,
  repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 4

### Step 6: C2E.6 — build atomic lease and complete-inventory control

- **Status:** PENDING / BLOCKED ON 5
- **Problem:** a provider cannot serialize mutations or prove cleanup without one environment-level
  lease and exhaustive environment-tag inventory.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/providers/<provider_adapter_key>/lease-inventory/**`,
  `tests/phase-is-environment/test_provider_lease_inventory.py`,
  `tests/phase-is-environment/fixtures/provider-lease-inventory/**`
- **Existing context:** implement exactly `lease-acquire`, `lease-renew`, `lease-release`, and
  `inventory` on Step 5's authenticated journals. Inventory covers every §5.1 resource kind and
  reconciles the resource journal; no later mutator bypasses this pair.
- **Produces:** atomic same-holder lease operations, ten-minute renewal scheduler/interlock, complete
  canonical environment inventory, retention-only read path, and mismatch/orphan fixtures.
- **Done when:** tests prove acquire/renew/release preserve holder/ID/deadlines; renewal loss blocks
  new mutations and allows provider lifecycle controls to act; incomplete or journal-divergent inventory blocks;
  retention identity cannot mutate; focused tests, repo-root `python -m pytest`, and
  `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 5

### Step 7: C2E.7 — build typed resource creation and volume attachment

- **Status:** PENDING / BLOCKED ON 6
- **Problem:** guest, signer, storage, network, connector, and attachment creation must not accept
  provider-native free-form configuration or produce an untagged intermediate object.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/providers/<provider_adapter_key>/resources/**`,
  `tests/phase-is-environment/test_provider_resources.py`,
  `tests/phase-is-environment/fixtures/provider-resources/**`
- **Existing context:** implement exactly `resource-create` and `volume-attach` on Steps 5–6. Every
  resource is descriptor-spec-bound and atomically tagged before visibility; every response/reread
  advances the resource inventory journal.
- **Produces:** typed create and exact run-volume attach/detach actions, independent rereads, journal
  reconciliation, and planted partial/untagged/orphan effects.
- **Done when:** tests prove no free-form provider configuration/path/wildcard, no mutation without
  lease/state/full inventory, exact idempotency under crash/retry, atomic tagging, signer-appliance and
  execution-lineage coverage, explicit attachment identity, and no unlisted residual artifact;
  focused tests, repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 6

### Step 8: C2E.8 — build power and snapshot lineage control

- **Status:** PENDING / BLOCKED ON 7
- **Problem:** power/reboot and snapshot transitions must bind exact lineage, prior state, lease,
  journal head, and mandatory session invalidation.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/providers/<provider_adapter_key>/lineage/**`,
  `tests/phase-is-environment/test_provider_lineage.py`,
  `tests/phase-is-environment/fixtures/provider-lineage/**`
- **Existing context:** implement exactly `power` and `snapshot` on Steps 5–7. Restore always rotates
  guest session and grant keys; no snapshot contains process/provider/host credentials or a private
  publisher key.
- **Produces:** exact power/reboot/create/restore/delete actions, boot-generation and lineage digests,
  mandatory new-session flag, and wrong-lineage/power/replay fixtures.
- **Done when:** tests prove expected-state and quiescence before effect, fresh session after restore,
  no credential/private-key snapshot, one writable descendant, exact journal/inventory convergence,
  and focused/root/diff gates pass.
- **Flags:** --reviewers deep
- **Depends on:** 7

### Step 9: C2E.9 — build lifecycle-rule and explicit destruction control

- **Status:** PENDING / BLOCKED ON 8
- **Problem:** automatic deadlines and per-target destruction need one closed plane without general
  deadline extension or implicit descendant deletion.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/providers/<provider_adapter_key>/lifecycle-destroy/**`,
  `tests/phase-is-environment/test_provider_lifecycle_destroy.py`,
  `tests/phase-is-environment/fixtures/provider-lifecycle-destroy/**`
- **Existing context:** implement exactly `lifecycle-rule` and `destroy` from §5.1. The only later-
  deadline case is the exact C4-PASS atomic reclassification; emergency authority can only shorten/
  quarantine under the existing failure cap or destroy.
- **Produces:** typed rule arm/transition/shorten/verify and one-target destroy actions, atomic PASS-
  transition primitive, independent rereads, and extension/reset/partial-destroy negatives.
- **Done when:** tests prove lifecycle arm-before-workload, exact C4 proof and atomic old-to-new rule
  transition, no runnable-lineage extension, idempotent same-request replay, explicit destruction of
  every inventory target, and blocking on any partial/unlisted result; focused/root/diff gates pass.
- **Flags:** --reviewers deep
- **Depends on:** 8

### Step 10: C2E.10 — build HMAC-authenticated read-only dispatch

- **Status:** PENDING / BLOCKED ON 9
- **Problem:** one standard-user allowlisted action needs an exact session/replay/HMAC envelope while
  remaining incapable of elevation, transfer, or arbitrary execution.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/guest-connector/readonly/**`,
  `tests/phase-is-environment/test_guest_readonly_dispatch.py`,
  `tests/phase-is-environment/fixtures/guest-readonly/**`
- **Existing context:** implement exactly `exec-readonly` plus the common guest HMAC/session envelope.
  No request has a grant, transfer field, or arbitrary command/path. Execution-guest and signer-
  appliance sessions/keys are separate and rotate after restore/restart.
- **Produces:** canonical guest HMAC request/result envelope, transactional monotonic
  `INTENT/APPLIED/RESULT` replay state with exact response cache, strict read-only
  action enum/dispatcher, and closed result/error mapping.
- **Done when:** tests prove missing/bad/wrong-plane HMAC fails before effect; guest HMAC cannot invoke
  an admin or transfer action; undeclared action/field/path fails before dispatch; restore rotates the
  session and rejects old material; crash fixtures at `INTENT`, `APPLIED`, and `RESULT` prove exact
  cached replay, read-only reconciliation, no duplicate effect, and fail-closed target retirement on
  ambiguity; focused tests, repo-root `python -m pytest`, and `git diff --check`
  pass.
- **Flags:** --reviewers deep
- **Depends on:** 9

### Step 11: C2E.11 — build content-addressed guest transfer

- **Status:** PENDING / BLOCKED ON 10
- **Problem:** source and evidence bytes need one hash/size/state-bound ingress/egress slice without a
  shared filesystem, arbitrary path, or execution authority.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/guest-connector/transfer/**`,
  `tests/phase-is-environment/test_guest_content_transfer.py`,
  `tests/phase-is-environment/fixtures/guest-transfer/**`
- **Existing context:** implement exactly `put` and `get` over Step 10's authenticated session. Logical
  destination/object IDs come only from committed enums or prior receipts; source/destination paths,
  wildcards, command text, grants, and implicit overwrite are absent.
- **Produces:** content-addressed ingress/egress, strict destination/object enums, size/hash/prior-state
  binding, exact stored/returned-object receipts, and collision/partial-transfer refusal.
- **Done when:** tests prove wrong size/hash/state/session/destination/object, overwrite collision,
  truncation, replay, path injection, and undeclared fields fail before publish/return; a valid round
  trip is byte-exact and non-executing; focused tests, repo-root `python -m pytest`, and
  `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 10

### Step 12: C2E.12 — build asymmetric single-use admin grants

- **Status:** PENDING / BLOCKED ON 11
- **Problem:** HMAC possession must never authorize an elevated execution-guest or signer-appliance
  action.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/schemas/admin-grant-v1.schema.json`,
  `tools/phase-is-environment/guest-connector/admin/**`,
  `tests/phase-is-environment/test_admin_grants.py`,
  `tests/phase-is-environment/fixtures/admin-grants/**`
- **Existing context:** implement only `exec-admin` with the exact embedded §5.2 grant. The parent
  private key never enters either machine; restore/restart rotates target session/public key and the
  consumed-grant store is target-scoped.
- **Produces:** closed parent grant materializer/verifier, exact execution/signing target roles,
  atomic request/grant replay store with reconciliation, privileged allowlist dispatcher, and stable denial codes.
- **Done when:** canonical vectors prove the payload excludes exactly `canonical_payload_sha256` and
  `signature`, the declared hash is non-self-referential, and the domain-separated RSA-PSS input is
  exact; the request and grant claims commit atomically, and crash fixtures at every replay state prove
  no duplicate elevation and no lost unclassified effect; missing/forged/replayed/wrong-hash/wrong-
  target/session/lease/state/input/action/expiry grants fail before elevation; HMAC cannot mint a grant;
  restore invalidates old grants; execution guest
  cannot use a signer target grant and vice versa; focused tests, repo-root `python -m pytest`, and
  `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 11

### Step 13: C2E.13 — build the execution-guest facts and coordinator-refusal probe

- **Status:** PENDING / BLOCKED ON 12
- **Problem:** later mutators cannot fail closed unless one read-only action first proves guest identity and emits a complete, canonical machine/tool/security fact set while refusing this workstation.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/guest/facts/**`, `tests/phase-is-environment/test_guest_facts.py`, `tests/phase-is-environment/fixtures/facts/**`
- **Existing context:** this step has one production action ID, `guest-facts-v1`, reached only through `facts`; it performs no write and accepts no arbitrary command/path. The private descriptor contains both expected guest identity and the coordinator exclusion digest.
- **Produces:** one idempotent read-only facts action, complete OS/firmware/resource/update/tool/host/security/volume inventory, coordinator-refusal guard, canonical receipt, and planted-invalid identities/inventories.
- **Done when:** PowerShell 5.1 parses the action; synthetic tests prove full enumeration, stable canonical output, no-write before/after facts, and unconditional refusal of the recorded coordinator or an unknown/mismatched guest; focused tests, `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 12

### Step 14: C2E.14 — build the S1 toolchain-baseline action

- **Status:** PENDING / BLOCKED ON 13
- **Problem:** S1 is not reproducible if OS servicing, Visual Studio/SDK/WDK installation, update freeze, quiescence, and snapshot preflight are improvised during provisioning.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/guest/baseline/**`, `tests/phase-is-environment/test_prepare_s1.py`, `tests/phase-is-environment/fixtures/baseline/**`
- **Existing context:** this step has one production admin action ID, `prepare-s1-v1`. It consumes
  C2E.4's exact version record and C2E.13's prior-state digest. Identity, lease, prior state, embedded
  single-use parent grant, and elevation validate before the first write; the action creates no run
  trust, signer appliance, or R0.
- **Produces:** one idempotent guest-only S1 preparation action covering patched supported OS, exact toolchain/host install and signature verification, update freeze, quiescence, S1 capture preflight, and canonical before/after receipt.
- **Done when:** tests prove all first-write interlocks, supported-version/signature and complete-candidate checks, idempotent convergence, failed-install rollback, quiescence, and exact S1 readiness; focused tests, `python -m pytest`, and `git diff --check` pass without executing the action here.
- **Flags:** --reviewers deep
- **Depends on:** 13

### Step 15: C2E.15 — build the isolated signer-appliance actions

- **Status:** PENDING / BLOCKED ON 14
- **Problem:** a signing private key in any guest that executes producer kernel code would let that
  code bypass DACLs and mint new admitted payloads.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/signer/**`,
  `tests/phase-is-environment/test_signer_appliance.py`,
  `tests/phase-is-environment/fixtures/signer/**`
- **Existing context:** production action IDs are `prepare-signer-v1` and `sign-exact-v1`, valid only
  for the descriptor-declared signer appliance. The appliance is non-snapshotted, has no execution-
  guest route, and runs no build/test/candidate process. Signing requires Step 12's embedded grant and
  an independently reviewed unsigned object hash.
- **Produces:** run publisher creation, private-root/issuer destruction, protected key DACL, hash-
  bound signer service, exact input/output spool, public chain export, signature receipt, spool wipe,
  and appliance isolation/audit facts.
- **Done when:** tests prove the exact three-certificate X.509 v3 chain, single-CN Names, distinct
  positive serials, shared bounded validity, Basic Constraints/path lengths, critical Key Usage,
  leaf-only Code Signing EKU, SKI/AKI relation, extension absence, RSA-3072/exponent-65537 canonical
  SPKI, SHA-256-with-RSA certificate signatures, single SHA-256 no-timestamp Authenticode signature,
  and rejection of every profile, chain, store, algorithm, size, digest, time, or timestamp mismatch;
  key nonexportability and exact DACL/service/channel binding; interrupted signing proves one cached
  result or destroys the appliance and invalidates its publisher/policy/R0 lineage; no arbitrary
  command/path; grant/input/candidate/policy/target mismatch fails before key use; signed output
  preserves all declared non-signature bytes and verifies to the public chain; standard user,
  producer, reviewer, execution guest, and wrong appliance cannot reach/use/export the key; focused
  tests, repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 14

### Step 16: C2E.16 — build execution-guest public trust and App Control action

- **Status:** PENDING / BLOCKED ON 15
- **Problem:** R0 needs reproducible public publisher trust and enforced pre-entry admission without
  copying the signing private key or improvising policy.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/guest/trust/**`,
  `tools/phase-is-environment/policy/**`, `tests/phase-is-environment/test_prepare_trust.py`,
  `tests/phase-is-environment/fixtures/trust/**`
- **Existing context:** the sole production action ID is `prepare-trust-v1`, valid only in an S1
  execution descendant. It consumes the signer appliance's public-chain receipt, creates the publisher
  policy, and never receives private key material. C2P/C3 still own containment/final image hashes.
- **Produces:** idempotent guest public-chain/App Control action, audit-to-enforce closure, public
  policy/signer facts, reboot preflight, canonical receipt, and wrong-signer/policy/private-key fixtures.
- **Done when:** tests prove first-write interlocks, exact public root/PCA/leaf store placement,
  absence of signing private material, exact `Publisher`-level PCA-TBS-plus-leaf-CN rule in scenarios
  12 and 131 plus the required `CiSigner`, refusal of Root/PCA/Leaf/FilePublisher/fallback variants,
  policy identity/audit closure/enforced UMCI target, and refusal of signer/policy/
  prior-state mismatch; focused tests, repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 15

### Step 17: C2E.17 — build clean pre-canary R0 boot preparation

- **Status:** PENDING / BLOCKED ON 16
- **Problem:** R0 must freeze exact boot/policy state before any candidate or kernel canary enters.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/guest/r0/**`,
  `tests/phase-is-environment/test_prepare_r0.py`,
  `tests/phase-is-environment/fixtures/r0/**`
- **Existing context:** the only execution-guest admin action is `prepare-r0-boot-v1`. It changes
  firmware/BCD/policy state under one parent grant, reboots, remeasures, quiesces, and ends before
  snapshot. It contains no canary input, signing request, candidate byte, or canary execution path.
- **Produces:** execution-guest Secure-Boot-off, `TESTSIGNING`-on, HVCI-on, enforced policy, clean
  reboot-generation/fact/evidence-flush record, and powered-off R0 snapshot precondition.
- **Done when:** tests prove reboot-generation binding, no canary/candidate/signing input is accepted,
  old/forged/replayed grants fail, quiescence and clean facts precede the parent snapshot request, and
  refusal occurs before write on host/lease/state/grant/policy mismatch; focused tests, repo-root
  `python -m pytest`, and `git diff --check` pass without executing it here.
- **Flags:** --reviewers deep
- **Depends on:** 16

### Step 18: C2E.18 — build throwaway-descendant admission canaries

- **Status:** PENDING / BLOCKED ON 17
- **Problem:** admission readiness requires positive and planted-negative user/kernel evidence without
  contaminating R0 or trusting a post-kernel descendant as its own security witness.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/canaries/**`,
  `tests/phase-is-environment/test_r0_canaries.py`,
  `tests/phase-is-environment/fixtures/canaries/**`
- **Existing context:** `run-r0-canaries-v1` begins only after the parent has captured powered-off R0.
  The parent creates one throwaway descendant, establishes new sessions/grants, and submits exact
  independently reviewed canary objects to the separate signer appliance. R0 itself never runs one.
- **Produces:** signed/unsigned/tampered/wrong-publisher user/kernel canaries, signed kernel escape
  canary, external provider/signer-network audit correlation, unload/evidence flush, and mandatory
  throwaway-descendant destruction receipts.
- **Done when:** tests prove signed canaries are admitted only through the exact signer receipt;
  planted negatives are denied; external—not guest-local—facts prove no signer route/credential;
  parent target/session/grant/snapshot identities are distinct and bound; the descendant is unloaded,
  powered off, inventoried, and destroyed; R0 facts remain pre-canary; focused tests, repo-root
  `python -m pytest`, and `git diff --check` pass without executing it here.
- **Flags:** --reviewers deep
- **Depends on:** 17

### Step 19: C2E.19 — build the lifecycle and rollback action

- **Status:** PENDING / BLOCKED ON 18
- **Problem:** provisioning and review cannot trust snapshots unless one parent-only action proves quiesce, power, snapshot/restore, exact-state recovery, and old-session invalidation.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/lifecycle/**`, `tests/phase-is-environment/test_rollback_smoke.py`, `tests/phase-is-environment/fixtures/rollback/**`
- **Existing context:** this step has one coordinator production action, `rollback-smoke-v1`, composed only from typed connector operations. The parent alone acquires the lease and invokes power/snapshot; no child receives provider authority. Guest process and connector secrets are revoked before power-off, while parent provider identity remains until lease release.
- **Produces:** exact quiesce/power/snapshot/restore sequence, deliberate wrong-prior-state failure, post-restore fact comparison, new-session establishment, old-session replay negative, complete-lineage cleanup, and authenticated receipt manifest.
- **Done when:** tests prove failure before write, exact rollback fact digest, fresh connector session/key after restore, rejection of the old signed request, one-writable-descendant serialization, and no orphaned session/lease/descendant; focused tests, `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 18

### Step 20: C2E.20 — build normal-control abort destruction

- **Status:** PENDING / BLOCKED ON 19
- **Problem:** a non-PASS terminal stop with healthy normal control needs one idempotent immediate-
  destruction action that revokes secrets and removes every environment resource.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/disposition/**`,
  `tests/phase-is-environment/test_disposition.py`,
  `tests/phase-is-environment/fixtures/disposition/**`
- **Existing context:** the production action is `dispose-v1`, composed only from Steps 5–12 control/
  guest operations and legal only for an abort, never C4 PASS. It handles execution descendants,
  signer appliance/key, snapshots, disks,
  attachments, network/policy/connector/secret objects, lifecycle rules, and the private common-parent
  run volume. It does not detach/retain evidence, arm quarantine, or perform the C4 PASS rule swap.
  Provider authority remains until provider-response, independent-reread, lease-release, and signed
  receipt verification complete.
- **Produces:** complete abort-only immediate-destroy action, driver/service quiesce/unload,
  signer/key destruction, credential/
  lease revocation ordering, canonical disposition receipt, and orphan/partial-destroy negatives.
- **Done when:** tests prove idempotent explicit per-target destruction, exhaustive final inventory,
  no runnable/signer/credential/lease/storage residue, provider authority revoked last, rejection of
  PASS/retain/quarantine inputs, and blocker status on any incomplete response/reread/
  removal; focused tests, repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 19

### Step 21: C2E.21 — build the deterministic native emergency builder and shell

- **Status:** PENDING / BLOCKED ON 20
- **Problem:** the final emergency runner needs a deterministic native shell/build closure before its
  broker and command implementations are integrated, without inheriting undeclared code.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/emergency/native/**`,
  `tools/phase-is-environment/emergency/build/**`,
  `tests/phase-is-environment/test_emergency_builder.py`,
  `tests/phase-is-environment/fixtures/emergency-build/**`
- **Existing context:** §5.5A is the only coordinator-native exception in this plan. It consumes
  C2E.4's exact signed private manifest through `SKILL_MESH_C2E_TOOLCHAIN_MANIFEST_REF` and verifies
  `emergency_build_toolchain_sha256` before use: already-installed Visual Studio 2026 MSVC v14.50
  and a supported installed Windows SDK, using explicit C++17
  `cl.exe`/`link.exe` paths and flag arrays, links the static CRT, and installs nothing.
- **Produces:** deterministic `build-emergency`, native x64 shell/entrypoint and command interfaces,
  sealed build-manifest format, exact source/tool/flag/input/output hashing, and no-PATH contract; no
  claimed final executable, command implementation, provider credential, retained manifest handle, or
  status transition.
- **Done when:** two builds of the fixed shell fixture in independent empty roots are byte-identical;
  retrieval/raw-hash/exact signed-object domain and RSA-profile/run/inventory/current-file/ACL verification passes and the handle is
  removed before compilation; pinned `dumpbin.exe` proves the declared shell import/PE closure; CFG,
  CET, ASLR, NX, high-entropy,
  static-CRT, `/Brepro`, sanitized-environment, and no-response-file requirements pass; planted
  negatives reject tool/signature/version/hash drift, PATH/current-directory DLL influence, an extra
  import, a changed flag, bad/missing retrieval, altered manifest, moved tool, and stale ACL; focused
  tests, repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 20

### Step 22: C2E.22 — build the image-bound emergency authority broker

- **Status:** PENDING / BLOCKED ON 21
- **Problem:** the emergency executable needs narrowly scoped provider authority without receiving a
  reusable provider credential or allowing another image, child, or replay to borrow it.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/emergency/broker/**`,
  `tools/phase-is-environment/schemas/emergency-broker-attestation-v1.schema.json`,
  `tests/phase-is-environment/test_emergency_broker.py`,
  `tests/phase-is-environment/fixtures/emergency-broker/**`
- **Existing context:** the broker has its own external encrypted transactional journal and an
  automatically disabled private authority lasting at most 60 days. It releases only closed safety
  operations: read-only pre-resource inventory, cleanup lease, exhaustive terminal inventory, failure
  quarantine, PASS-transition-failure destroy-only cleanup, power-off, destroy, and release. It cannot
  create, attach, snapshot, power on, execute,
  sign, retain PASS evidence, extend a
  deadline, or write repository/GitHub state.
- **Produces:** exact image/file-identity/hash/manifest/bootstrap/journal/payload/environment/expiry
  attestation, one-use least-privilege emergency session, credential-isolating broker protocol,
  durable replay journal, restart reconciliation, and provider-authenticated raw response channel.
- **Done when:** the provider credential never enters launcher or child memory/environment; tests
  reject changed images, manifests, bootstrap/journal heads, payloads, environments, expiries, scopes,
  children, duplicates, and incomplete restart state; an identical idempotency-key replay returns the
  same result while a changed replay blocks; automatic authority disable is independently reread;
  focused tests, repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 21

### Step 23: C2E.23 — build the direct emergency runner and raw safety record

- **Status:** PENDING / BLOCKED ON 22
- **Problem:** a terminal failure must become safe even when Git, tests, build-phase, GitHub, or the
  normal control/wait signers are unavailable, without allowing unsigned output to certify status.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/schemas/emergency-preflight-v1.schema.json`,
  `tools/phase-is-environment/schemas/emergency-disposition-v1.schema.json`,
  `tools/phase-is-environment/emergency/runner/**`,
  `tools/phase-is-environment/emergency/finalize/**`,
  `tests/phase-is-environment/test_emergency_disposition.py`,
  `tests/phase-is-environment/fixtures/emergency/**`
- **Existing context:** inventory is reconstructed from the immutable bootstrap tag, resource journal,
  and exhaustive provider tag query. The runner invokes only Step 22's broker, preserves the raw
  provider response plus independent reread, and emits private later-proof input—not a verdict,
  receipt, marker, or status update. The parent independently retrieves and verifies the exact Step-4
  signed toolchain manifest again for the final double-build and removes the process-only handle before
  executing the result.
- **Produces:** direct `preflight-empty` and `emergency-dispose`, exact private preflight/emergency-
  record schemas, the final self-contained executable/runtime manifest, deterministic safe-destroy,
  PASS-transition-failure destroy-only, or already-authorized failure-quarantine workflow, and parent-
  only `finalize-emergency-proof`.
- **Done when:** dirty Git, failing pytest, absent build-phase/GitHub, and unavailable control/wait
  signers do not block power-off/inventory/disposition/lease release; tests reject incomplete inventory,
  descriptor/journal/environment mismatch, tampered response, unsafe quarantine, provider-handle pre-
  release, residual authority, and any retain/quarantine attempt under
  `C4_PASS_TRANSITION_FAILED`; tests also prove both pre-resource inventory scopes traverse the
  sealed executable/broker/provider/reread/record path, are read-only, and reject nonempty inventory;
  a planted partial destroy emits the closed `INCOMPLETE` raw record, cannot emit terminal/status/C5
  proof, and resumes cleanup, while only complete destroy produces `SAFE_DESTROYED`;
  two final-executable builds in independent empty roots are byte-identical and repeat Step 21's full
  import/PE/runtime-closure gates; `finalize-emergency-proof` requires the exact raw-record hash,
  bootstrap/journal chain, original failure, fresh provider inventory/reread, and external control-
  receipt authority, emits canonical disposition facts for Step 2's `sign-wait`, and rejects any
  mismatch; unsigned raw output cannot advance status or C5 and later signed proof binds its bytes;
  focused tests, repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 22

### Step 24: C2E.24 — build immutable active-lineage lifecycle enforcement

- **Status:** PENDING / BLOCKED ON 23
- **Problem:** a lost coordinator must not leave a runnable or indefinitely live driver-test lineage.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/retention/active/**`,
  `tests/phase-is-environment/test_active_lifecycle.py`,
  `tests/phase-is-environment/fixtures/retention/active/**`
- **Existing context:** the provider-native rule is the first provider resource, armed before any
  execution/signer/storage/network object, and is
  separate from evidence retention. Its maxima are lease 30 minutes, power-off within five minutes of
  missed renewal, writable-descendant destruction within 60 minutes, and complete active-lineage
  destruction within 30 days of first resource creation.
- **Produces:** closed `arm-active` and read-only `verify-active` operations, immutable
  deadline/rule hashes, independent provider rereads, and fail-closed immediate-destroy fallback.
- **Done when:** tests prove every trigger operates without the coordinator and none of the four
  maxima can be extended, disabled, paused, reset, recreated to move the clock, or bypassed by a new
  descendant; complete inventory reaches absence at the absolute deadline; focused tests, repo-root
  `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 23

### Step 25: C2E.25 — build the one-way proof-bound C4 PASS retention transition

- **Status:** PENDING / BLOCKED ON 24
- **Problem:** retained PASS evidence needs automatic deletion, but its later deadline must neither
  extend runnable state nor be forgeable from local, unsigned, abort, or future-disposition evidence.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/retention/pass-transition/**`,
  `tests/phase-is-environment/test_pass_retention_transition.py`,
  `tests/phase-is-environment/fixtures/retention/pass-transition/**`
- **Existing context:** `transition-pass-retention` is the sole later-deadline exception. In one
  provider transaction it remotely verifies exact C4 PASS and pre-disposition #153 evidence, destroys every
  runnable/signer/snapshot/OS/credential object, detaches the one encrypted run volume, removes the
  old rule, and arms a nonextendable deletion rule for exactly C4 PASS creation plus 120 days.
- **Produces:** proof-bound `transition-pass-retention` with old/new rule IDs, hashes, deadlines,
  exact remotely reread C4 commit/tree/UAT/#153 evidence bindings, pre/post inventory, and idempotency record.
- **Done when:** identical retries return the same result; changed, unavailable, or partial transitions
  invoke Step 23's `C4_PASS_TRANSITION_FAILED` emergency destroy-only route, which destroys the volume
  and every remaining target, records the original PASS plus transition failure, and cannot retain,
  quarantine, or make C5 eligible; no runnable object survives a PASS transition; no caller chooses,
  extends, disables, pauses, or resets a deadline; missing remote proof forces immediate destruction;
  focused tests, repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 24

### Step 26: C2E.26 — build bounded emergency failure quarantine

- **Status:** PENDING / BLOCKED ON 25
- **Problem:** an abort may require short forensic quarantine, but emergency authority must not retain
  PASS evidence, choose a deadline, keep runnable state, or inherit normal-control powers.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/retention/failure-quarantine/**`,
  `tests/phase-is-environment/test_failure_quarantine.py`,
  `tests/phase-is-environment/fixtures/retention/failure-quarantine/**`
- **Existing context:** only the image-bound emergency broker may invoke `arm-failure-quarantine`,
  after exhaustive inventory and power-off, under the Step-4 preauthorized target/scope. Its closed
  transition binds the earliest immutable terminal-stop journal receipt/provider time, original
  failure, old active rule/deadline, and pre-transition inventory. The deadline is exactly the earlier
  of that stop time plus seven days or the original active-lineage deadline; immediate destruction is
  default and mandatory if the provider cannot atomically arm/reread it.
- **Produces:** closed proof-tagged broker-only `arm-failure-quarantine`, fixed deadline calculator,
  permitted-target allowlist, provider rule/result/reread binding, immutable stop-time replay rule, and
  immediate-destroy fallback.
- **Done when:** tests reject normal/retention/guest callers, runnable or PASS targets, caller-supplied/
  later deadlines, caller-supplied/reset stop time, incomplete inventory, rule/readback ambiguity,
  reuse for another run, and any
  extend/disable/pause/reset; failure falls back to exhaustive immediate destruction; focused tests,
  repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 25

### Step 27: C2E.27 — build parent-only C5 retention shortening

- **Status:** PENDING / BLOCKED ON 26
- **Problem:** C5 must reduce the PASS evidence lifetime without giving an abort path, guest, broker,
  or caller a way to replace, extend, or reset the existing hard cap.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/retention/c5-shorten/**`,
  `tests/phase-is-environment/test_c5_retention_shorten.py`,
  `tests/phase-is-environment/fixtures/retention/c5-shorten/**`
- **Existing context:** the active-run provider identity is already revoked. After remotely verifying
  the exact C4 PASS transition/#143 disposition proof, the parent pushes and rereads an immutable
  reviewed C5 closeout candidate that still marks retention shortening pending, signs the private C5
  shortening intent, and uses the Step-4 preauthorization to mint a new non-exportable identity valid
  for at most one hour. It can only invoke `shorten-c5` and independently reread the exact retained
  volume/rule. The new deadline is exactly the earlier of intent `created_utc` plus 90 days or the
  existing C4-plus-120-day cap.
- **Produces:** closed parent-only proof-tagged `shorten-c5`, exact C4/C5 remote-proof and signed-intent
  binding, old/new rule and deadline receipt, independent reread, idempotency record, immediate JIT-
  identity revocation/absence receipt, and subsequent final status-only closeout binding the result.
- **Done when:** canonical vectors prove the exact closed C5 intent, §5.0 signed-object profile/domain,
  raw-file digest, fixed `created_utc`, and derived authorized deadline; tests reject broker/retention/
  guest callers, missing or mismatched C4/C5 proof,
  non-PASS targets, non-JIT or expired/wrong-scope identities, any equal/later deadline, caller time,
  rule replacement/reset, changed replay, and incomplete reread; identical replay is stable; a failure
  leaves the earlier existing rule armed and still revokes the JIT identity; focused
  tests, repo-root `python -m pytest`, and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 26

### Step 28: C2E.28 — build retained-artifact absence verification and key retirement

- **Status:** PENDING / BLOCKED ON 27
- **Problem:** an expiry rule is not proof that retained provider objects are actually absent or that
  the surviving read-only verification identity was retired.
- **Type:** code
- **Issue:** #162
- **Files:** `tools/phase-is-environment/retention/verify/**`,
  `tests/phase-is-environment/test_retention_absence.py`,
  `tests/phase-is-environment/fixtures/retention/absence/**`
- **Existing context:** a separate least-privilege read-only retention identity survives only to
  enumerate the exact tagged lineage and verify lifecycle-rule/object absence. It cannot mutate,
  restore, attach, read volume contents, or extend retention.
- **Produces:** closed `verify-absent`, signed schedule/absence receipts, named owner/deadline, and
  automatic verification-key retirement at verification plus seven days with an expected immediate
  retirement within 24 hours after a successful proof.
- **Done when:** exhaustive provider inventory rejects every residual object or rule; tests prove the
  identity cannot mutate and its key is destroyed/reread absent after proof or automatically by its
  deadline; provider/readback failure preserves a blocker; focused tests, repo-root `python -m pytest`,
  and `git diff --check` pass.
- **Flags:** --reviewers deep
- **Depends on:** 27

### Step 29: C2E.29 — provision S1, signer appliance, and R0

- **Status:** PENDING / BLOCKED ON 28 AND SEPARATE OPERATOR PROVISIONING APPROVAL
- **Problem:** C2N cannot discover a driver toolchain/admission posture until the reviewed bundle
  creates a measured execution lineage and isolated publisher without placing the key beside candidate
  kernel code.
- **Type:** wait
- **Issue:** #162
- **Files:** `documentation/phase-is-disposable-c2n-c4-environment-plan.md`, `plan.md`; bootstrap/final
  descriptors, resource journal, raw receipts, private evidence, provider resources, S1/R0, signer
  appliance, and sealed emergency bundle remain external; the exact public marker is posted to #162
- **Existing context:** use only C2E.4's public adapter/private route and reviewed Steps 5–28. Before
  `environment_id`, the parent materializes the exact current-candidate emergency executable/manifest
  into immutable private storage, independently rereads their bytes/import closure/broker binding, and
  runs live `pre-resource-run` empty-inventory preflight. It then atomically generates/commits
  `environment_id`, the locator-free bootstrap descriptor, and zero-head external resource journal;
  a failed transaction creates none of the three and enters pre-resource closure. After a committed
  transaction, it runs live `pre-resource-environment` empty-inventory preflight. Only then may it
  acquire the lease—the first provider mutation—and create/reread active lifecycle as the first
  provider resource before any execution/signer/storage/network create. Every create carries
  the exact run/environment tags and has journaled intent before the provider call, response plus
  independent reread afterward, and crash reconciliation by exhaustive tag inventory. If any stop
  occurs after an environment ID or provider resource exists, enter Step 33 immediately. Create a signer with
  no execution-guest route, S1/R0 with public chain only, and the encrypted run volume. Freeze clean R0
  before canaries; run admission canaries only in throwaway descendants and destroy them. Do not
  install a local hypervisor/Windows feature or mutate this workstation. Pin guest publication egress
  to the selected broker endpoint and prove direct GitHub API routes denied.
- **Produces:** sealed exact-current-candidate emergency bundle plus two live pre-resource preflight
  records; immutable bootstrap and derived final descriptors; complete resource journal;
  powered-off S1 and clean public-trust R0; powered-off non-snapshotted signer appliance holding the
  non-exportable run leaf; enforced policy/test-signing state; encrypted run volume; authenticated
  receipts; armed active lifecycle; publication-broker egress receipt; coordinator fact pair; signed
  private `provisioning` wait result;
  exact #162 marker; and subsequent committed DONE status; no product code.
- **Done when:** before provisioning, the parent pushes/rereads the exact reviewed Steps-5–28
  candidate with expected-old protection and binds it as the wait precondition. Then §5.1 through
  §5.5A pass; both exact-bundle live preflights are independently reread,
  empty, and occurred before the first mutation; exact OS/tool facts are frozen; S1/R0 contain no private key,
  source, or authority; signer runs no candidate/build/test code and is unreachable from R0; canary
  descendants are absent; broker-only publication egress and direct-GitHub-API denial are externally
  corroborated; complete tagged inventory equals the journal/final descriptor; active and
  authority deadlines plus emergency closure match; coordinator facts match; the parent verifies and
  signs the wait result, posts/rereads the exact marker, then commits/pushes returned marker facts and
  DONE status with expected-old protection. Otherwise preserve the blocker and enter Step 33.
- **Flags:** none
- **Depends on:** 28

### Step 30: C2E.30 — run live connector, rollback, signer isolation, and fresh-context smoke

- **Status:** PENDING / BLOCKED ON 29
- **Problem:** mocks cannot prove connector authentication, rollback, admin grants, signing isolation,
  or producer/reviewer separation on the selected real substrate.
- **Type:** wait
- **Issue:** #162
- **Files:** `documentation/phase-is-disposable-c2n-c4-environment-plan.md`, `plan.md`; raw smoke
  evidence and signed wait record remain in the private artifact store; exact marker is posted to #162
- **Existing context:** the parent creates the sole R0 descendant and holds provider, connector,
  admin-grant, and verdict authority. It dispatches one no-history Terra producer and a separately
  fresh reviewer; neither receives those authorities or the publisher key.
- **Produces:** live receipts for connector identity, provider reread/signature, intentional pre-write
  failure, content transfer, asymmetric admin grants, signer isolation, snapshot/restore, replay denial,
  cleanup, a revoked non-publishing synthetic exact-body publication capability and denial matrix,
  fresh-context separation, parent-only classification, signed `live-smoke` wait result, exact
  #162 marker, and subsequent committed status; no product code.
- **Done when:** with one lease, wrong expected state fails before write and the valid canary succeeds;
  guest HMAC cannot mint admin grants; revert rotates session/grant keys and denies old requests;
  producer/reviewer use separate serialized descendants and return identical redacted facts without
  authority leakage; externally audited signing canaries/negatives pass; the publication-broker smoke
  rejects wrong issue/body/ordinal/image/argv, replay, third use, expiry, and direct GitHub API access,
  exposes no real credential, and proves immediate capability revocation; parent returns `SUPPORTED`;
  every smoke descendant is destroyed; coordinator facts match; parent signs, posts/rereads, and then
  commits/pushes returned marker facts and DONE status with expected-old protection.
- **Flags:** none
- **Depends on:** 29

### Step 31: C2E.31 — build and review the local readiness candidate

- **Status:** PENDING / BLOCKED ON 30
- **Problem:** C2N needs one immutable reviewed redacted input, but build-phase cannot push or perform
  the later remote-seal wait.
- **Type:** code
- **Issue:** #162
- **Files:** `documentation/findings/phase-is-c2e-environment.json`, `plan.md`,
  `documentation/phase-is-completion-plan.md`
- **Existing context:** finalize a private evidence manifest against the immutable pre-receipt
  candidate; it excludes the future receipt, commit/tree, seal, and every C2N/C3/C4 output. The receipt
  binds `pre_receipt_commit/tree`; the later #162 seal binds receipt blob and sealing commit/tree.
- **Produces:** local reviewed readiness JSON/candidate commit binding environment, bootstrap/final
  descriptor and journal heads, S1/R0, signer/public-chain isolation, run volume, provider/control/
  replay/lifecycle facts, private-evidence manifest, coordinator facts, and smoke; no push/comment/
  remote DONE, and C2N remains blocked.
- **Done when:** no-write verifier returns READY; the generator has semantic and byte no-diff; package-integrity,
  `git diff --check`, and detached sentinel-first repo-root pytest pass; independent no-history deep
  review has zero High/Medium; accepted plan/UAT blobs are unchanged; build-step creates only the
  immutable local candidate commit.
- **Flags:** --reviewers deep
- **Depends on:** 30

### Step 32: C2E.32 — push, remotely seal, and record readiness

- **Status:** PENDING / BLOCKED ON 31
- **Problem:** build-phase deliberately does not push, and a local candidate cannot unblock C2N.
- **Type:** wait
- **Issue:** #162
- **Files:** `documentation/phase-is-disposable-c2n-c4-environment-plan.md`, `plan.md`; private
  `readiness-seal` wait record remains external; exact public marker is posted to #162
- **Existing context:** the parent verifies Step 31's immutable commit/tree/receipt blob/raw hash and
  review/root-gate evidence, fetches `origin/main`, refuses movement, and pushes only that candidate
  with expected-old protection. Build-phase is not invoked.
- **Produces:** signed private `readiness-seal` wait result, exact remotely reread #162 marker, and a
  later status-only commit/push recording returned comment facts and DONE; no product code.
- **Done when:** origin equals the Step 31 candidate; wait result binds commit/tree/receipt blob/raw
  hash/environment/private-evidence/coordinator facts; parent posts and paginates/rereads exact marker;
  only afterward it commits/pushes returned facts and DONE with expected-old protection; final origin/
  marker reread agrees. C2N becomes unblocked but starts only in a fresh context.
- **Flags:** none
- **Depends on:** 31

### Step 33: C2E.33 — perform mandatory terminal disposition

- **Status:** PENDING / BLOCKED UNTIL C4 PASS OR A TERMINAL C2E/C2N/C2P/C3/C4 STOP AFTER AN
  ENVIRONMENT ID OR PROVIDER RESOURCE EXISTS
- **Problem:** the environment is not closed while any runnable guest, snapshot, credential,
  publisher key, driver state, storage object, lifecycle rule, or lease lacks disposition.
- **Type:** wait
- **Issue:** #143
- **Files:** `documentation/phase-is-disposable-c2n-c4-environment-plan.md`, `plan.md`; disposition,
  raw/emergency evidence and signed wait records remain private; exact marker is posted to #143
- **Existing context:** on C4 PASS, the parent first invokes Step 25 `transition-pass-retention` as the
  sole retention mutation. A verified idempotent success never invokes abort-only `dispose-v1` or
  `emergency-dispose`. If the normal identity is unavailable before verified success, or the provider
  returns a failed/ambiguous transition, the parent immediately invokes Step 23 with
  `C4_PASS_TRANSITION_FAILED`; that route is destroy-only, preserves the original PASS plus transition
  failure, forbids retention/quarantine, and leaves C5 blocked. On an abort with healthy normal control,
  it invokes Step 20 `dispose-v1` for immediate destruction. If abort normal control is unavailable—or
  the operator-authorized bounded failure quarantine is selected—it immediately invokes the sealed
  Step 23 emergency path, which may call only Step 26's proof-bound quarantine rule, without Git,
  pytest, build-phase, GitHub, or control-receipt/wait-result signer preflight. Mandatory image-bound
  broker attestation still applies.
  Every route reconstructs exhaustive inventory from bootstrap, journal, and provider tags; revokes
  guest/connector secrets; quiesces/unloads; powers off; dispositions the lineage; releases the lease;
  verifies provider response plus reread; and revokes the active normal or emergency provider identity
  last. A successful PASS transition preserves only the detached run volume, credential-free C5-
  shortener preauthorization, read-only retention identity, and the control-receipt/wait-result/
  emergency-broker private authorities needed for C5 proof and final teardown; every other route
  destroys those authorities during safety or its immediate bookkeeping. Never target this workstation.
  Bookkeeping resumes only after safety; an emergency record is finalized only through
  Step 23 `finalize-emergency-proof` and Step 2 `sign-wait`.
- **Produces:** authenticated disposition and `terminal-disposition` wait records proving complete
  destruction or authorized bounded retention; on PASS, the sole atomic Step 25 transition retains only the
  detached encrypted run volume through C5 under nonextendable C4-plus-120-day deletion; a failed PASS
  transition instead destroys everything and records `BLOCKED`; on abort,
  immediate destruction or powered-off non-runnable quarantine ending at the earlier of stop plus
  seven days or original active deadline; named absence owner/deadline; exact #143 marker; subsequent
  committed status; no product code.
- **Done when:** safety completes independently of repository/test/remote state; no runnable, signer/
  leaf, reusable session, unowned provider object, loaded driver/service, or unscheduled retained item
  remains; complete tagged inventory is reconciled; every retained item has classification, owner,
  locator digest, immutable rule, deadline, and absence action; provider authority is revoked only
  after verified lease release and safety reread; coordinator facts match; later parent bookkeeping
  finalizes emergency raw evidence through the owned finalizer when applicable, signs the wait proof,
  posts/paginates/rereads the exact marker, then commits/pushes returned
  facts and `DONE` only for `PASS` or `CLEANED_AFTER_ABORT`; the PASS-transition-failure route records
  the exact `BLOCKED` state after safety and stops. An `INCOMPLETE` raw action is non-terminal, emits
  no marker/status/C5 result, and must continue or escalate cleanup. `C4_PASS` requires `PASS` with `c5_eligible=true`;
  `C4_PASS_TRANSITION_FAILED` requires `BLOCKED`, complete destroy-only safety, preserved C4 PASS and
  transition-failure digests, and `c5_eligible=false`; abort requires `CLEANED_AFTER_ABORT`, preserves
  the original failure, and leaves C5 blocked. Bookkeeping outage
  cannot reverse safety; incomplete inventory, disposition, or automatic deletion remains a blocker.
- **Flags:** none
- **Depends on:** C4 PASS for normal entry; no Git/build/test dependency for emergency safety after a
  terminal stop; bookkeeping follows verified emergency disposition

## 8. Risks and Open Questions

| Risk | Resolution or stop |
|---|---|
| No provider satisfies the contract or the operator declines license/cost/retention terms. | C2E.4 remains blocked. Do not implement an adapter, provision, substitute a host share/private network, or mutate this workstation. |
| Provider authentication, lease, or lineage inventory is incomplete. | Require provider-native short-lived authorization, independent control-plane reread plus parent signature, separate guest HMAC, asymmetric parent-only admin grants, atomic lease, and complete inventory. A forged/replayed/stale receipt or unverifiable descendant is a hard stop. |
| Exact Windows or SDK/WDK servicing revision advances. | C2E.4 rereads official sources, records the supported build-family pairing, and freezes exact S1 facts. Never auto-upgrade after S1. |
| Publisher admission is mistaken for complete containment. | C2E proves image admission only; C2P/C3 retain broker, driver, process, environment, handle, and I/O obligations. |
| Producer can sign arbitrary bytes or inherit authority. | Producer never receives the key, admin grant channel, provider credential, reviewer context, Git write, or verdict key. Parent grants one declared action/hash; reviewer and parent independently verify it. |
| A post-kernel child steals `GH_TOKEN` and gains reusable publication authority. | The real GitHub credential stays in the external broker; each child receives only a distinct five-minute exact-body/issue/ordinal one-publication capability, direct GitHub API egress is denied, and capability reuse/third-use/wrong-body tests fail. |
| Unsigned App Control policy is mutable by an administrator. | Host sessions run standard-user; parent controls narrow admin grants; policy facts and canaries are checked around each use; independent checks restore fresh R0. This is disposable-test evidence, not production hardening. |
| Snapshot cloning duplicates the non-exportable test-publisher key. | The key exists only in the non-snapshotted signer appliance; S1/R0 and descendants contain only the public chain. Destroy the appliance/leaf at C3 candidate lock and require a new appliance/policy/R0 lineage after any candidate change. |
| The frozen UAT's topology is accidentally changed by a separate evidence disk. | All four roots are direct children of one common parent on one run volume; `<evidence-export>` is neither a mount nor reparse point. The retained volume is classified private. |
| Coordinator and guest source bytes diverge. | Every transfer binds commit/tree, byte count, SHA-256, expected state, lease, and authenticated receipt; C3 reopens exact consumed identities. |
| Receipt or evidence manifest becomes self-referential. | The private manifest binds the pre-receipt candidate and explicitly excludes future receipt/seal objects; the #162 seal binds the committed receipt afterward. |
| A failure leaves a runnable or unowned security environment. | C2E.33 is mandatory on every terminal branch after an environment ID or provider resource exists. Default destroy; bounded powered-off quarantine requires explicit owner, provider TTL/lifecycle deletion, and later absence verification and still blocks C5 until the immediate disposition is verified. |
| Parent provider authority is revoked before cleanup. | Guest process/host and connector secrets are revoked first. Narrow parent provider identity remains through power-off, complete inventory, disposition, lease release, and receipt verification, then is revoked last. |
| A retention deadline is merely advisory. | C2E.4 requires an automatic deletion primitive; C2E.24–28 separately implement active expiry, proof-bound PASS retention, failure quarantine, C5 shortening, and absence verification; C2E.33 invokes the applicable terminal transition. Without those mechanisms, retain/quarantine is forbidden and immediate destruction is mandatory. |
| The parent/session disappears while a privileged guest is active. | Before the first resource, arm provider-native maxima: 30-minute lease, power off within five minutes of missed renewal, destroy the writable descendant within 60 minutes, and destroy the complete active lineage within 30 days of first creation. These clocks may only be shortened and the emergency bundle remains directly runnable without Git/build/test services. |
| Raw/private evidence is confused with the redacted export. | Raw C2E evidence remains in an authorized encrypted private artifact store. The retained run volume is also private because deleted-root block remnants may survive. |
| Planning changes rewrite accepted owners. | Gates compare phase-plan blob `6fb9f94f957fca5d3416ffd6dbe6a99ebe6a16e2` and frozen UAT blob `c285605543f1c3ad02f8ceaf70dac5cb0af37b43`; any drift blocks. |

The concrete provider, image/license, cost ceiling, private evidence store, publication broker, and retention owner remain
explicit C2E.4 operator choices. The seven-day failure-quarantine interval, 90-day C5 interval,
120-day PASS fail-safe, and 30-minute/five-minute/60-minute/30-day active-lifecycle maxima are fixed v1
safety bounds; only the active-lifecycle maxima may be shortened at C2E.4, and no bound may be
extended. Missing choices leave execution blocked.

## 9. Testing Strategy and Stop Conditions

### Planning gates

- Run `plan-review`, `plan-redline`, and `plan-wrap` on this document in that order.
- Run an independent deep security/conformance review because authority and cleanup failures are
  high consequence.
- Run `python tools/gen_manifest.py` and require no generated semantic or byte diff.
- Run `python -m pytest tests/package-integrity`, `git diff --check`, and the repository-root
  `python -m pytest` DONE gate.
- Prove the accepted plan and frozen UAT Git blobs remain exactly unchanged.

### Code-step coverage

Steps 1–3 and 5–28 each require focused tests plus the root gate before DONE. Coverage includes strict
JSON closure/canonicalization; redaction; host exclusion; provider auth; HMAC; expiry, sequence, and
replay; lease and complete inventory; content hashes; first-write interlocks; tool/signer ambiguity;
snapshot lineage; publisher/key policy; App Control IDs/mode/rules; Secure Boot/BCD/HVCI/reboot facts;
positive and planted-negative canaries; one-common-parent run-volume topology; rollback; credential
revocation; complete disposal; retention ownership; and deadline expiry. Every PowerShell script must
parse under Windows PowerShell 5.1. Static tests prove no mutator is reachable before descriptor,
identity, lease, prior-state, action-ID, grant, and elevation checks. There is no separate lint,
typecheck, or development-server gate.

### Live substrate and rollback proof

C2E.30 is mandatory. It intentionally sends one request with a wrong expected prior state and proves
failure before write, then performs the valid transfer. It snapshots/reverts, establishes a new
connector session, proves the old signed request is rejected, compares exact fact digests, exercises
signed and planted-negative user/kernel canaries, and repeats redacted facts through separate
no-history Terra producer/reviewer descendants. Only the parent may classify `SUPPORTED`.

### Hard stop conditions

Stop before C2N, C3, or C4 on any of the following:

- any requested or observed change to this workstation's certificates, Code Integrity/App Control/
  AppLocker, Secure Boot, BCD/boot configuration, firmware, Windows features, installed toolchain, or
  host applications;
- absent provider authorization, Windows license/media, current supported OS/SDK/WDK pairing,
  provider-native identity, atomic lease, complete lineage inventory, authenticated connector,
  independent control-plane reread/signature, separate asymmetric admin-grant key, encrypted private
  evidence store, external signer/key-destruction route, exact-body publication broker with no direct
  guest GitHub API route, retention owner, active-lifecycle rule, or
  resource/cost authorization;
- shared folder, clipboard/file transfer, drive redirection, bridged/host-only/private network, host
  route, arbitrary shell, ambient credential, unverified transfer, forged/stale/replayed receipt, or
  an old connector session accepted after restore;
- reusable snapshot containing source or any process/provider/host auth credential; undeclared test
  trust; more than one writable descendant; or a descendant/storage object absent from inventory;
- Secure Boot on in the guest, `TESTSIGNING` absent after reboot, HVCI off, unrecorded boot drift,
  missing/wrong/expired/ambiguous publisher facts, leaked private material, or child key access;
- App Control not enforced with UMCI, policy/signer mismatch, unresolved audit event, signed canary
  denied, planted-negative canary admitted, or any attempt to use a future final-image hash in C2E;
- producer access to reviewer state, provider/connector/admin/verdict/Git/seal authority; reviewer
  reuse of producer context; parent unable to authenticate or solely classify the verdict;
- source/commit/tree/hash drift, dirty or detached guest source, untracked distribution input, remote
  ref movement, force push, concurrent Git writers, or accepted phase-plan/frozen-UAT blob drift;
- all four C4 roots not being direct children of one common parent on one encrypted run volume;
  `<evidence-export>` being a separate mount/reparse target; cleanup targeting the real profile/export;
- binary/catalog signer or ordering failure, unrecorded driver/service disposition, a live C4 code
  patch, missing remote evidence reread, receipt self-reference, or failed review/test/seal gate;
- inability to revoke credentials, power off, enumerate, destroy, or assign a bounded quarantine with
  exact owner/deadline to every resource on a terminal branch; any attempt to extend/disable/reset the
  active-lifecycle maxima; or an emergency safety action that depends on Git, tests, build-phase, or
  GitHub availability.

On any stop after an environment ID or provider resource exists, enter C2E.33 before leaving the
environment: collect only permitted evidence; revoke
guest process/host and connector authorization; use the narrow active parent identity through power-
off, complete inventory, disposition, lease release, and receipt verification when healthy, otherwise
use the image-bound emergency broker, then revoke that active authority last. Destroy the lineage or
record an explicitly authorized bounded non-runnable quarantine with automatic deletion and later
absence verification. A failed C4-PASS retention transition is always destroy-only and blocks C5.
Preserve the exact blocker. Never
weaken a gate, patch live during C4, widen a path, leave an unowned resource, or fall back to this
workstation.

## Appendix — Decision Inventory

`P` records explicit operator choices. `D` records agent-defaulted design choices that remain
editable before execution. IDs are stable and append-only: later changes retain the ID and record
`changed <date>` rather than deleting or renumbering it. This inventory and proposal do not consume
the separate execution authorizations required by C2E.4 and C2E.29.

| ID | P/D | Choice | Status |
|---|---|---|---|
| P1 | P | Plan a dedicated disposable driver-test environment for C2N through C4 | operator-picked 2026-08-30 |
| P2 | P | Do not modify this workstation's certificates, Code Integrity policies, Secure Boot, or boot configuration | operator-picked 2026-08-30 |
| D1 | D | Use one Windows 11 Enterprise x64 execution guest for C2N/C3/C4 plus one isolated, non-snapshotted, run-scoped Windows signer appliance that never runs candidate code | agent-defaulted 2026-08-30 — changed 2026-08-30 after security review |
| D2 | D | Keep a provider-neutral repository contract, then stop for explicit selection of one provider/license/cost/retention route before implementing its adapter | agent-defaulted 2026-08-30 — provider remains unselected |
| D3 | D | Keep this workstation as coordinator and sole Git, infrastructure-grant, review-classification, and final-verdict authority | agent-defaulted 2026-08-30 — editable before execution |
| D4 | D | Require RFC 8785-plus-LF canonical bytes and a closed 16-operation connector with separate provider-control, guest-HMAC, image-bound emergency-broker, and retention-verification authenticators; domain-separated length-delimited full-envelope proofs; exact embedded asymmetric admin grants; an immutable locator-free bootstrap plus transactional control/resource/guest replay journals; atomic acquire/renew/release lease operations; complete inventory; expected-state checks; and explicit resource/lifecycle controls | agent-defaulted 2026-08-30 — changed 2026-08-30 after security and plan-wrap review |
| D5 | D | Use powered-off S1 and run-specific R0 execution snapshots containing only the public publisher chain, one non-snapshotted isolated signer appliance holding the non-exportable leaf, and at most one writable execution descendant | agent-defaulted 2026-08-30 — changed 2026-08-30 after security review |
| D6 | D | In the guest only, use Secure Boot off, `TESTSIGNING` on, HVCI on, and unsigned enforced App Control with one exact `Publisher`-level PCA-TBS-plus-leaf-CN rule in user/kernel scenarios and canaries | agent-defaulted 2026-08-30 — clarified 2026-08-30 after security review |
| D7 | D | Put all four frozen-UAT roots under one common parent on one encrypted run volume and classify the retained volume as private | agent-defaulted 2026-08-30 — constrained by frozen UAT |
| D8 | D | Recheck official versions at C2E.4; planning baseline observed 2026-08-30 is VS 2026, SDK `10.0.28000.2705`, WDK `10.0.28000.2526`, and Windows build `28000.2804` | agent-defaulted 2026-08-30 — execution recheck required |
| D9 | D | Split C2E into 33 bounded steps; Steps 4, 29, 30, 32, and 33 are machine-stopping parent waits and Step 31 creates only a local candidate | agent-defaulted 2026-08-30 — changed 2026-08-30 after plan review |
| D10 | D | Let C2E attest complete tool/host capability inventories while C2N alone applies the deterministic selection rule | agent-defaulted 2026-08-30 — preserves existing owner |
| D11 | D | Use automatic deletion: failed-run quarantine ends at the earlier of the immutable terminal-stop receipt plus seven days or the original 30-day lineage deadline; only a remotely proven C4 PASS may atomically destroy runnable state and reclassify the detached run volume to a nonextendable C4-plus-120-day rule; C5 may only shorten it to the earlier of signed shortening authorization plus 90 days or that cap; later absence verification required | agent-defaulted 2026-08-30 — changed 2026-08-30 after plan review; seven days, 90 days, and 120 days are fixed v1 bounds |
| D12 | D | Revoke guest/connector secrets first and the active normal/emergency provider identity last; only successful PASS retention preserves credential-free C5 preauthorization, read-only verification authority, and control/wait/emergency proof authorities through C5 teardown; terminal cleanup covers C2E/C2N/C2P/C3/C4 and abort or PASS-transition-failure cleanup never unblocks C5 | agent-defaulted 2026-08-30 — changed 2026-08-30 after plan review; safety invariant |
| D13 | D | Authenticate each wait completion with the exact RSA-3072/exponent-65537/SPKI/PSS signed-object profile and advance only after private verification, selected-adapter-bound committed status, and exact API-returned remotely reread issue marker agree | agent-defaulted 2026-08-30 — changed 2026-08-30 after security and plan-wrap review |
| D14 | D | Require focused tests and the repository-root pytest gate for each code atom, plus a detached sentinel-first root gate before the readiness seal | agent-defaulted 2026-08-30 — editable before execution |
| D15 | D | Use a distinct ephemeral asymmetric parent-only admin-grant key with a non-self-referential payload hash and domain-separated exact signature input; possession of the guest connector HMAC cannot grant elevation | agent-defaulted 2026-08-30 — security invariant clarified after plan-wrap review |
| D16 | D | Generate the closed RSA-3072/SHA-256 X.509 v3 root/PCA/leaf profile with bounded validity and single no-timestamp SHA-256 Authenticode signatures in an isolated, non-snapshotted appliance; keep the non-exportable leaf private key only there under protected key/service/channel ACLs; admit only independently reviewed exact objects under parent grants; prove no execution-guest/producer/reviewer/kernel route or authority | agent-defaulted 2026-08-30 — clarified 2026-08-30 after security review |
| D17 | D | Split provider-control receipts from guest-data HMAC receipts; control results require independent provider reread and a parent-only external RSA signature | agent-defaulted 2026-08-30 — security invariant |
| D18 | D | Arm immutable active-lifecycle maxima and keep a sealed direct emergency-disposition path independent of Git, tests, build-phase, and GitHub | agent-defaulted 2026-08-30 — safety invariant |
| D19 | D | Treat every execution descendant as untrusted after candidate kernel entry; rely on pre-sign source/object review and external provider/signer facts, never guest-local cryptography alone, and destroy that descendant after use | agent-defaulted 2026-08-30 — security invariant added after review |
| D20 | D | If the proof-bound C4 PASS retention transition cannot start or cannot be verified, use the image-bound broker to destroy the complete lineage under a distinct reason, preserve the PASS plus transition failure, record C2E.33 BLOCKED, and keep C5 ineligible | agent-defaulted 2026-08-30 — safety invariant added after plan review |
| D21 | D | Preauthorize no reusable C5 credential; after a remotely reread pending closeout candidate and an exact domain-separated parent-signed C5 intent, mint one new one-hour exact-rule shortener, revoke it and the preauthorization after use, then destroy the surviving control/wait/emergency authorities before final DONE | agent-defaulted 2026-08-30 — authority invariant clarified after security review |
| D22 | D | Make the wait-signing key the first atomic, reconciled, sign-tested Step-4 allocation and bind pre-resource closure to either the private selection-attempt record or the final provider-selection PASS | agent-defaulted 2026-08-30 — closure invariant added after plan review |
| D23 | D | Store the exact emergency build toolchain as a domain-separated RSA-profile-signed private content-addressed manifest and expose only a process-scoped opaque retrieval handle to the parent build atoms | agent-defaulted 2026-08-30 — toolchain boundary clarified after security review |
| D24 | D | Keep HMAC-authenticated read-only guest dispatch and content-addressed guest transfer as separate observable code atoms | agent-defaulted 2026-08-30 — step split added after plan review |
| D25 | D | Keep the real GitHub credential in an external publication broker; supply each C4 upload process only a distinct five-minute exact-body/issue/ordinal one-publication capability named `GH_TOKEN`, deny direct GitHub API egress, and revoke after reread | agent-defaulted 2026-08-30 — post-kernel credential boundary added after security review |
