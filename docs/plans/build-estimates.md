# Remaining-work estimates

Forward remaining effort in hours, including implementation and its checks/review. Operator attention is separate. Elapsed waits, service quotas and hardware availability are not labor. These are model forecasts, not measured history. Held rows remain disabled.

Rows validate as ForecastEstimate. Portable worksheet only: production ForecastConfig is currently restricted to dev-observatory and 100 estimates; no saved forecast was modified.

Plan: [master_plan.md](master_plan.md). SHA-256: `a33c47064044aba55ca0077c1055244e88f86a407feee71537d98437031dc975`.

Rebind after editing the plan; source fingerprints deliberately become stale. The JSON preserves dependencies and evidence locations.

| Step | Worker hours | Attention hours | Confidence | Availability | Basis |
|---|---:|---:|---:|---|---|
| E1 — Lock evidence schemas and no-write verifier | 12.0–28.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Strict JCS+LF, safe integers, UTF-8 no BOM; reject duplicate keys, surrogates and wrong RSA profiles. Verify exact closed schemas without mutation. |
| E2 — Authenticated wait, status and remote markers | 12.0–26.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Signed status/wait envelopes; exact eight-kind allocation closure; exhaustive pagination and key-scoped markers; refusal on incomplete inventory. |
| E3 — Coordinator non-mutation facts | 6.0–14.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Read-only fact collection must prove coordinator identity and refusal of local mutation, never manufacture host attestations. |
| E4 — Provider and retention selection | 2.0–6.0 | 1.0–4.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Operator chooses provider, licensing, costs and external key/broker route. Select atomic wait/signer key lifecycle maximum60days and complete pre-resource closure. |
| E5 — Provider authentication and replay | 20.0–44.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Full authenticated envelopes, RSA3072/PSS32, closed16-operation protocol, durable journals and idempotency across crashes. |
| E6 — Lease and complete inventory | 12.0–24.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Atomic lease/inventory;30-minute lease and10-minute renewals; fail closed on incomplete or ambiguous ownership. |
| E7 — Typed resource creation | 10.0–22.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Typed resources and volume attach, atomic run tags, containment and collision refusal before mutation. |
| E8 — Power and snapshot lineage | 10.0–22.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Power/snapshot transitions with fresh-session proof and exact ancestry, no reuse of a stale guest identity. |
| E9 — Lifecycle rules and destruction | 10.0–24.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Explicit lifecycle-rule installation and destructive transitions within owned inventory; visible failure and retained safety evidence. |
| E10 — Authenticated read-only guest dispatch | 12.0–28.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | HMAC-bound target/replay with INTENT/APPLIED/RESULT journal; closed operations and no implicit executable prose. |
| E11 — Content-addressed guest transfer | 8.0–20.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Exact content-addressed manifests and byte hashes with traversal/link/collision refusal; no mutable checkout runtime dependency. |
| E12 — Single-use admin grants | 12.0–28.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Asymmetric grants are image/action bound, one use and non-replayable; no reusable secret in execution guest. |
| E13 — Guest facts and coordinator refusal | 6.0–16.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Execution-guest fact collector refuses coordinator execution and verifies independent instance/context identity. |
| E14 — S1 toolchain baseline | 6.0–14.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Capture actual S1 toolchain inputs and exact identities; missing tooling halts rather than downloading unstated fallback. |
| E15 — Isolated signer appliance | 20.0–48.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | RSA3072 root/PCA/leaf chain; strict sign policy, no private-key export and no assertion of future binary hashes. |
| E16 — Execution public trust and App Control | 16.0–36.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Public trust only; Publisher PCA+leafCN policy with scenarios12/131 and UMCI. Signer keys stay outside execution guest. |
| E17 — Clean pre-canary R0 boot | 8.0–20.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | SecureBootOff/testsignon/HVCIon at clean R0; freeze baseline before canaries, retain exact measured facts. |
| E18 — Throwaway admission canaries | 16.0–36.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Positive and negative kernel canaries only in throwaway descendants, external witness; post-kernel guest is untrusted. |
| E19 — Lifecycle and rollback | 10.0–26.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Fresh descendant rollback with observed exact lineage/restoration; lifecycle enforcement must remain active. |
| E20 — Normal-control abort | 8.0–18.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Abort-only destruction obeys complete owned inventory; no claim of acceptance from cleanup success. |
| E21 — Deterministic emergency builder | 18.0–40.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Native unsigned C++17 emergency shell, existing tools only, /Brepro /MT and closed imports; no live installation. |
| E22 — Image-bound emergency broker | 16.0–38.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | External authority bound to exact emergency image, no reusable credentials; independent refusal tests. |
| E23 — Direct emergency runner | 12.0–28.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | preflight-empty and dispose only; independent of Git/tests/signers; raw safety record is not a signed program-status proof. |
| E24 — Immutable active-lineage lifecycle | 12.0–26.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Power off five minutes after lease expiry, destroy descendants within60minutes, lineage hardcap30days; cannot silently extend. |
| E25 — C4 PASS retention transition | 14.0–32.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Atomic proof-bound PASS retains only detached private volume; C4+120day hardcap. Otherwise fail/destroy and block C5. |
| E26 — Failure quarantine | 8.0–18.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Abort quarantine minimum7days within original30day cap, without retaining active dangerous compute. |
| E27 — Parent-only C5 retention shortening | 8.0–20.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | One-hour JIT authority; shorten to minimum(intent+90days,hardcap); never prolong retained life. |
| E28 — Absence verification and key retirement | 10.0–24.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Read-only retained-artifact absence verification; key retirement24hours after automatic PASS plus7days rule as specified. |
| E29 — Provision S1, signer and R0 | 4.0–12.0 | 1.0–4.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Separate operator approval; two empty-inventory live preflights before environmentID, then lease as first mutation and lifecycle first. |
| E30 — Live connector and fresh-context smoke | 6.0–18.0 | 1.0–4.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Real connector, rollback and signer isolation; independent producer/review contexts; no real publication or simulated native PASS. |
| E31 — Local readiness candidate | 8.0–24.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Build and independently review exact local candidate and its hashes; required gates, no push in this child step. |
| E32 — Remote seal and readiness | 2.0–8.0 | 1.0–4.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Parent performs authorized push, remote reread/seal and readiness status only; no source change during sealing. |
| E33 — Mandatory terminal disposition | 3.0–12.0 | 1.0–4.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Mandatory after C4PASS or any terminal environment: safety first, independent of Git/signers. Retain raw proof. PASS alone allows C5; abort-cleaned is not acceptance. |
| 126 — Make ordinary full review reliable on Codex | 10.0–24.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan status is blocked; retain the estimate without selecting this work. | Independent ordinary-review support and preserved exhausted gate require source reconciliation. |
| 127 — Resume the intended durable build checkpoint | 8.0–18.0 | 0.5–2.0 | 0.35 | enabled forecast | Explicit durable-session selection plus unrelated-state preservation and fresh resume cases. |
| 128 — Prepare the connected Codex acceptance procedure | 6.0–14.0 | 0.5–1.5 | 0.35 | enabled forecast | Real loopback, pytest and Chromium procedure with named functional negatives. |
| 129 — Complete the installed ordinary Codex workflow | 2.0–6.0 | 2.0–5.0 | 0.35 | enabled forecast | Six connected installed Codex cases and fresh-session transition; operator time dominates. |
| 130 — Ship attributable reports and bounded inspection | 10.0–22.0 | 0.5–2.0 | 0.35 | enabled forecast | Stable attribution reports, closed disposition contracts and safe bounded orphan inspection. |
| 131 — Observe the installed skill in a fresh Codex session | 2.0–5.0 | 1.0–3.0 | 0.35 | enabled forecast | Installed normal-profile scope/carry/dry-run observations. |
| 111 — Make native-born inventory generation hermetic | 6.0–14.0 | 0.5–1.5 | 0.35 | enabled forecast | Hermetic inventory generation and sourceFiles correction. |
| 112 — Enforce one operation-aware catalog truth gate | 10.0–22.0 | 0.5–2.0 | 0.35 | enabled forecast | Operation-aware truth validation must precede any destructive generation. |
| 113 — Add and dogfood the portable `/skill-crud` front door | 10.0–24.0 | 1.0–3.0 | 0.35 | enabled forecast | Portable CRUD front door plus actual provider-compatible dogfood. |
| 114 — Block legacy single-host mutation paths | 6.0–14.0 | 0.5–1.5 | 0.35 | enabled forecast | Find and block legacy single-host mutation seams without widening eval scope. |
| 115 — Prove nondestructive lifecycle transitions | 6.0–16.0 | 1.0–2.0 | 0.35 | enabled forecast | Nondestructive lifecycle transitions in disposable actual environments. |
| 116 — Prove destructive transitions and recovery | 10.0–24.0 | 1.0–3.0 | 0.35 | enabled forecast | Destructive/recovery failure matrix including stale identity hardening. |
| 117 — Certify the release candidate and prepare attended acceptance | 8.0–20.0 | 1.0–3.0 | 0.35 | enabled forecast | Frozen exact candidate, broad existing gates, release record and manual preparation. |
| 118 — Attended disposable-host acceptance | 2.0–6.0 | 2.0–4.0 | 0.35 | enabled forecast | Actual Claude/Codex disposable-host attended acceptance. |
| 154 — Observe capture and harvest in the installed Codex host | 1.0–4.0 | 1.0–2.0 | 0.35 | enabled forecast | Unchanged-HEAD capture/harvest acceptance and named rejection cases on installed host. |
| 120 — Make deep-review aggregation fail closed | 10.0–24.0 | 0.5–2.0 | 0.35 | enabled forecast | Strict closed aggregation, uncertainty stops and source-pinned provenance. |
| 121 — Restore deep review and explicit support assets on both hosts | 12.0–30.0 | 1.0–3.0 | 0.35 | enabled forecast | Both-host support assets and genuine isolated reviewer capability; rebase accepted CD scope. |
| 125 — Complete the installed Claude workflow and accept both hosts | 3.0–10.0 | 2.0–6.0 | 0.35 | enabled forecast | Connected Claude acceptance and two-host evidence after refreshed M1 contracts. |
| S8 — Light proof and ambient Codex soak | 3.0–8.0 | 3.0–7.0 | 0.35 | enabled forecast | Both real homes, CRUD round trips, calibration and ambient session log; elapsed soak excluded. |
| S9 — Closeout and baseline ownership | 2.0–6.0 | 0.5–1.5 | 0.35 | enabled forecast | Evidence and baseline closeout only; no unapproved Track C rebuild. |
| 47B — Harden the containment gate honestly (off the cutover critical path) | 8.0–20.0 | 0.5–2.0 | 0.35 | enabled forecast | Differential counterexample corpus and enumerated undo identity tripwire. |
| TM — Installed tier-map resolution audit | 3.0–10.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Classify145 existing references and prepare scope; implementation remains unpriced. |
| LM — Legacy migrator hardening | 2.0–6.0 | 0.5–2.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Inspect preserved issue/candidate and prepare scoped hardening; destructive implementation unpriced. |
| 109 — Attended confirmation of all five D10 rows | 3.0–10.0 | 3.0–8.0 | 0.35 | HELD: Canonical plan explicitly holds this step: HELD | Five D10 rows in selected isolated substrate plus terminal safety evidence. |
