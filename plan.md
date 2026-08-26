# Skill Mesh plan

## Current goal

Execute Phase CP (`documentation/codex-parity-delivery-plan.md`): ship the same maintained Skill Mesh
behaviors through native Claude Code and Codex discovery, wire the known utility portfolio, expose
truthful model evidence through Dev Observatory, and make shared-core maintenance multi-host safe.

The goal is unchanged from Goal NP; the delivery path is not. Goal NP's two-approval publication gate
was closed unapproved on 2026-08-16 and replaced by Phase CP's additive, cohort-based rollout — a
five-skill pilot proven on a real host first, then cohorts gated on that evidence.

## Main execution plan

Publication 8 is one exact ten-file recovery approval bundle, in the launcher's required order:

- this `plan.md` — the publication-status and authority pointer;
- `documentation/native-claude-codex-skill-parity-plan.md` — the canonical executable Goal NP plan
  and source of truth;
- `documentation/native-claude-codex-skill-parity-terra-amendment.md` — the narrow controlling
  amendment for the Goal-NP administrative and numbered code-step executor;
- `documentation/native-claude-codex-skill-parity-proposal.html` — the operator-facing redline;
- `tools/run-goal-np-terra-bootstrap.ps1` — the precommitted, post-Approval direct Terra
  first-producer launcher;
- `schemas/terra-bootstrap-result-v1.schema.json` — its unchanged closed model-result contract;
- `experiments/recovery/cross-family-fixture/create_fixture.py` — the cross-platform LF-normalized
  cross-family candidate-copy and declared-inventory hash boundary;
- `experiments/recovery/cross-family-fixture/probe.py` — the matching LF-canonical source/sealing
  boundary and fail-closed fixture/receipt identity check;
- `tests/experiments/test_cross_family_probe.py` — the LF, CRLF, lone-CR, and identity-drift regression
  coverage for that sealed inventory; and
- `tests/distributions/test_path_choke_point.py` — the exact whole-file path-choke exemption for the
  one-off, fixed-boundary Publication-8 launcher.

The final four files are a bounded repair of failures reproduced at clean Publication-7 HEAD before any
Publication-8 request claim. The fixture builder normalizes CRLF and lone CR to LF at the candidate
copy/hash and declared-inventory hash boundaries. A later restarted plan-redline review then found that
the same unqualified `defect_inventory_sha256` still meant LF-normalized builder bytes, SHA-256
`98baaa178e41dc23e5de70e3161de78c66b9c91052c4d0d99295ae1a8928ed37`, in one place and raw CRLF
sealed-probe bytes, SHA-256
`24c336217fba1a6d1d177b754a34be77275e0c797a50d48ea0a7e5d9401c2752`, in another. Publication 8
therefore also LF-canonicalizes that inventory at the probe's source/sealing boundary, rejects a
fixture/canonical-source or fixture/receipt identity mismatch before use, and tests LF, CRLF, and lone-CR
source variants. The path-choke gate exempts exactly the one-off launcher, whose caller supplies no
consumer-home mutation target and whose repository, ADMIN, Evidence, and Staging boundaries are fixed
and independently checked; the written exemption must be removed if that boundary broadens. This does
not narrow, skip, xfail, or otherwise weaken the DONE gate: the exact bundle must pass the unchanged
repository-root `python -m pytest` before claim, and the launcher's full-root pytest gate remains
mandatory.
Abraham explicitly authorized this bounded baseline-gate repair and Publication-8 revision; that
revision authority is not Recovery Approval 1 and authorizes no `Preflight`, `Run`, model call,
implementation, or live mutation.

This root file is only the mutable publication-status and authority pointer. The detailed plan is the
canonical executable Goal NP plan and owns scope, the 41-step DAG, D01–D10, D08 evaluation roles, two
native-host qualification, two approval gates, migration, proof, and rollback. The standalone proposal
is an operator-facing view. Where—and only where—the Terra amendment names an orchestration,
administrative-executor, or Publication-8 review-attestation surface, the amendment controls.

`documentation/skill-mesh-recovery-plan.md` remains the historical authority for ended Goal A. Goal NP
does not reinterpret that evidence or revive its stopped experiment.

## Progress

| Unit | Status | Who or what unlocks it |
|---|---|---|
| Goal NP plan | CLOSED UNAPPROVED (course change 2026-08-16) | Nothing — closed by operator ratification; no further approval is sought |
| Goal NP implementation | SUPERSEDED — documentation/codex-parity-delivery-plan.md | Nothing — Phase CP owns delivery sequencing from 2026-08-16 |
| Phase CP pass 1 (Steps 1–5) | COMPLETE (2026-08-18) | Nothing — issues #118–#122 closed at `4bcbef5`; DONE gate green |
| Phase CP Step M1 (#130) | COMPLETE (2026-08-18) — passing verdict | Nothing — check rows, deltas, and verdict recorded in `documentation/parity-deltas.md`; codex-cli 0.147.0, Copilot 1.0.77 |
| Phase CP pass 2 (Steps 6–8) | COMPLETE (2026-08-19) | Nothing — issues #123/#124/#125 closed at `2ae2f69`; the codex adapter catalog is closed at 47/47 portable skills |
| Phase CP Step M2 (#131) | COMPLETE (2026-08-19) — PASS | Nothing — verdict and delta rows in `documentation/parity-deltas.md`; its findings file released Step 9 |
| Phase CP pass 3 (Steps 9–10) | COMPLETE (2026-08-20) | Nothing — issues #126/#127 closed at `c4a850c`; catalog now 57 skills / 54 portable. Ran as `--steps 9,10`, not 9–12 |
| Phase CP Step 11 (#128) | DROPPED (2026-08-20) — operator decision | Re-owned by `dev/documentation/utility-hookup-plan.md` Steps 6–23 (its D12 already assigned these edits). Premise disproven: no advisory-call wiring has ever existed in any skill core. Evidence: `documentation/parity-deltas.md` § Phase CP pass-3 blocker |
| Phase CP Step 12 (#129) | disposition follows Step 11 | See its block in the delivery plan; the observatory-visibility question is being resolved against `dev-observatory/plans/utility-project-surfaces-plan.md` |
| Phase CP Step M3 (#132) | PENDING (2026-08-20) — daily-use row only | The operator: a few genuine Codex-hosted sessions. Delta triage is DONE — 43 rows across 4 tables, 0 undisposed, 0 `fix-later` owed; the providers-doc gap was filed as #142 and is now CLOSED at `2462afd` (codex given first-class doc coverage; the host-discovery gate derives its provider set from `Get-SkillMeshDiscoveryRoots` instead of hand-listing two). Evidence: `documentation/parity-deltas.md` § M3 checks |
| Phase CP Step M4 (#133) | COMPLETE (2026-08-20) — PASS | Nothing — codex arm reinstalled clean (125 files; 0 stale, 0 unledgered) and all seven observatory locators verified `unwired` on the rendered surface, before and after. The claude and gpt `-Force` arms were deliberately not run. Evidence: `documentation/parity-deltas.md` § M4 checks and § Scope of the M4 PASS |
| Phase IS (#143) | BUILDING (2026-08-26) — 7 of 10 steps built (Step 106 / #150 at `dc21c9e`; 104–106 flipped DONE on one shared repo-root gate, `1341 passed / 1 skipped`) | The build, which must run on Claude Code: `/build-step` is a recorded `blocker`/`wontfix` on Codex (no isolated fresh-context primitive), so a Codex `/build-phase` halts at Step 100. Planned, reviewed (22 Blockers), wrapped (9 Blockers), redlined and synced; steps 100–109 are #144–#153. Authority: `documentation/instruction-file-symmetry-plan.md` |
| Legacy-migrator hardening (#138) | DEFERRED | Its own issue — Phase CP ships zero migrator delta by the option-3 decision of 2026-08-18 |
| Goal NP live cutover | LOCKED | Approval 2 on the immutable deliverable after disposable rehearsal |
| Provider expansion | PARKED | A later explicit Abraham decision must resume that track; Goal NP does not unlock it |
| Goal A execution | STOPPED | Gate A approved terminal action `stop` after the bounded follow-up failed |
| Historical Gate A | APPROVED | Terminal action `stop`; no architecture selected |
| Historical Goal B / Phase 2 / Step 4 | LOCKED | Goal NP may adopt the four preserved files only after Approval 1 and its own gates |
| Historical Goal P | LOCKED / NOT AUTHORIZED | Not part of Goal NP |

## Current instruction

Execute Phase CP per `documentation/codex-parity-delivery-plan.md`. That plan is the current
delivery authority; this file records status and history.

**Pass 1 (Steps 1–5) is complete as of 2026-08-18** at commit `4bcbef5`. **Step M1 (#130) is
complete as of 2026-08-18 with a passing verdict** — evidence, check rows, delta rows (one
`fix`-dispositioned: plan-review's autofix fix-count line), and the D-CP6 accept decision are
recorded in `documentation/parity-deltas.md`.

**Pass 2 (Steps 6–8) is complete as of 2026-08-19** at commit `2ae2f69`, issues #123/#124/#125
closed. The three cohorts carried the codex adapter catalog from the five-skill pilot to all 47
portable skills — Cohort B the pipeline family (12), Cohort C the build/review/skill/tier
families (16), Cohort D the remainder (14). Per-skill authoring deltas for each cohort are
recorded in `documentation/parity-deltas.md`; the pass-exit repo-root gate summary is
`documentation/findings/cp-step8-pass2-root-gate.txt`.

**Step M2 (#131) passed on 2026-08-19**, and its findings file released Step 9.

**Pass 3 is complete as of 2026-08-20**, and it ran as `--steps 9,10` rather than 9–12.
Step 9 (#126) closed at `b7b6fb5` with a full repo-root gate of **1320 passed / 1 skipped**;
Step 10 (#127) closed at `c4a850c` with **1322 passed / 1 skipped**, promoting the 7
workspace-custom skills and taking the catalog to **57 skills / 54 portable / 3
provider-native**.

**Steps 11 and 12 were not built.** Step 11's premise was disproven — the "16 modified
installed cores" it was to port advisory-call wiring from contain none, and an exhaustive
coding-root search finds `DEV_UTILITIES_ROOT` only in planning and convention documents,
never in a skill core. On 2026-08-20 the operator re-owned that work to
`dev/documentation/utility-hookup-plan.md` Steps 6–23, whose D12 had already assigned the
same edits, making it double-owned. Step 12's disposition follows from Step 11. Full evidence
and the cross-plan dependency: `documentation/parity-deltas.md` § *Phase CP pass-3 blocker*;
issues #128 and #129.

**The next action is operator Step M3 (#132) alone.** M4 (#133) is PASS as of 2026-08-20:
the codex profile reinstalls cleanly and all seven observatory locators render their true
`unwired` state. Its claude and gpt `-Force` arms were deliberately not run — that check row
is unsatisfiable as written (it requires "no foreign files touched" while the block mandates
`-Force`, whose documented purpose is taking ownership of foreign files), and their payoff is
provably zero while no wiring exists in any core on either side of the propagation.

M3 is `PENDING` on exactly one row — daily-use quality — which needs a few genuine
Codex-hosted sessions and cannot be satisfied by re-reading the M1/M2 milestone runs it exists
to backstop. Everything else M3 required is recorded and durable. Phase CP closes when that one
row is graded; then `/repo-update` runs and #132, #133 (and the stale-open #131) close.

**The active build is Phase IS (#143), not Phase CP.** Phase CP is parked on the single
operator row M3 (#132) described above and cannot close until it is graded. Phase IS
(`documentation/instruction-file-symmetry-plan.md`) is a **prerequisite**, not a follow-up: the
wider proposal's Phase 3 inverts instruction files across up to 32 repositories, and skills in this
catalog *write* those files — run one against an already-inverted project and it silently recreates
the duplication the inversion exists to remove. Nothing may migrate until Phase IS lands.

**Phase IS is 7 of 10 steps built as of 2026-08-26** at `dc21c9e`. Steps 100–106 are DONE and their
issues (#144–#150) closed; steps 107–109 (#151–#153) are not started. Step 103 records the
authoritative WRITE/READ/REFERENCE classification in § 4 of the phase plan — `WRITE=5 READ=9
REFERENCE=13` over the 27 files under `skills/**` that name `CLAUDE.md`, against denominators of 54
cores and 165 provider files.

**Steps 104–106 flipped DONE together on one shared repo-root gate**: `1341 passed, 1 skipped` in
2:16:29, exit 0, run detached at `dc21c9e` — exactly `+6` against the 1335 recorded in
`documentation/phase-75-baseline.md`, which is Step 106's six new tests, with the skip count
unchanged. Summary retained at `documentation/findings/phase-is-shared-gate-dc21c9e.txt`. Available
memory sat between 1737 and 1864 MB for the whole run — continuously inside the band issue #156
associates with spurious subprocess reds — and the run produced zero failures regardless, so #156
remains a risk factor to check against, not a predictor.

Step 104 repointed ten sites across seven cores; Step 105 gave every one of context-slim's 20
`CLAUDE.md` occurrences an explicit keep-or-repoint verdict while preserving D9's `CLAUDE.md`-anchored
ancestor walk byte-for-byte; Step 106 added
`tests/package-integrity/test_instruction_contract_single_owner.py`, whose 21 assert lines were each
proven RED against a planted defect. Two findings that outlived the steps are tracked separately:
**#159** (the `goblin` and `citation-needed` CLIs hard-code `CLAUDE.md`, so two repointed skills
cannot yet act on `AGENTS.md`), and the fact that **review-deep's calibration gate cannot run inside
this repository** — `skill-mesh` carries no `evals/` tree, so `calibrate_judge.py` exits 1 here and
the Step 106 deep review was run and reported as uncalibrated.

**The two Step-106 carry-forwards are resolved — operator decisions of 2026-08-25**, recorded as
Round 5 in § 12 of the phase plan:

1. **Step 106 is trimmed to the single-owner gate.** The write-surface gate — unfalsifiable as
   specified (finding 10) and self-contradictory (finding 11) — is deferred to the phase plan's § 10
   with an explicit resurrection condition. Issue #150 stays open at the narrowed scope.
2. **Steps 104, 105, and 106 share one batched DONE gate**: iterate on `tests/package-integrity`,
   then a single repo-root `python -m pytest` after all three land flips all three DONE.
3. **Park-and-pivot — SUPERSEDED 2026-08-26 by an in-session operator instruction.** Round 5 had
   Phase IS park after the shared gate and the next window pivot to the utility track. The operator
   redirected on 2026-08-26, after the gate came back green: **the next step is Phase IS Step 107**,
   via `/build-phase --plan documentation/instruction-file-symmetry-plan.md --resume 107`. The
   utility track is deferred behind Steps 107–109, not cancelled.
   **Updated 2026-08-26 — the deferred track's two prerequisites are now BOTH already satisfied, so
   when it resumes it resumes further along than this row assumed:**
   - The **plan-review refresh has RUN.** `<dev-root>/documentation/utility-hookup-plan.md` went
     through plan-review + plan-wrap (verdict **READY**, 0 blockers / 0 gaps) and `/repo-sync`
     re-derived issues #399–#418 plus umbrella #395 in `aberson/coding-root`. Two blockers were
     found and fixed, and the codex-catalog staleness this row names is resolved (new D13/D14).
   - Its **Step 4 (installer current-byte authority) was already built** — closed as **#116** on
     2026-08-18. It is not pending and nothing is dispatched for it. Host-parity Step 70's stale
     `BLOCKED` precondition and the matching `OPEN BLOCKER` risk row were retired accordingly in
     `documentation/host-parity-repair-plan.md`, so **Step 70 (#101) is now unblocked** and is the
     remaining gate on that track.
   - That plan was also renumbered (a Step 4 was inserted): its wiring work is **Steps 6–24**, not
     6–23, and **Step 5 is a `Type: wait` operator-only gate** — a `DEV_UTILITIES_ROOT` bootstrap
     plus a full host restart, which cannot be dispatched. A resuming session picks up at
     `--resume 6` only after that is done by hand.

   Step 107 is well-placed to run next on its own merits: its `Done when` requires measuring the
   repo-root suite, comparing it against the count recorded *before* the step, and only then writing
   the new figure into `documentation/phase-75-baseline.md` — in that order, so the comparison is not
   circular. The shared gate above supplies that measurement (`1341 passed / 1 skipped` against a
   recorded 1335/1), so Step 107 inherits it rather than paying another 2h16m.

The Goal NP recovery decision is **closed**. No Publication-8 approval is pending or will be sought.
Do not run any Publication-8 `Preflight` or `Run`, and do not invoke
`tools/run-goal-np-terra-bootstrap.ps1` — the launcher is **parked**, committed as historical record
and never executed. Publications 3, 4, and 5 remain terminal; Publications 6 and 7 remain approved
preclaim records without a request root or consumed Run lineage. None of those approvals authorizes a
retry, and none is needed.

Phase CP's own boundaries still hold and are the operative limits: writes are additive only — repo,
`dist/`, and disposable temp homes — with real consumer-home writes confined to its operator steps M1
and M4. Destructive legacy retirement, live Claude-home cutover, junction retargeting, and retiring
the Copilot-managed profile stay out of scope for a future plan carrying its own approval packet.

## Goal NP planning journal

**Status:** CLOSED UNAPPROVED (course change 2026-08-16) — superseded for delivery sequencing by
`documentation/codex-parity-delivery-plan.md` (Phase CP). Publications 3–5 remain terminal;
Publications 6–7 remain preflight-blocked with no request claim. Publication 8 was never approved and
now never will be: it is committed as historical record only. This journal is history, not authority.

**Planning authority:** On 2026-08-14 Abraham approved the full native Claude/Codex parity planning
direction, placement at the user `.agents/skills` scope, exhaustive per-skill tests, known utility and
Dev Observatory integration, a one-time migration, and exactly two approval gates: Approval 1 for the
final plan and Approval 2 for the final deliverable/live cutover. A superseding plan publication or
terminal bootstrap recovery requires a fresh exact Approval-1 sentence without creating a third gate.

**Publication-3 terminal record:** Abraham supplied the exact Publication-3 Approval-1 sentence on
2026-08-15 for commit `71a5aea3fd21320d2fbb3cb9228bc52e42cb3215`. Its canonical approval-file
SHA-256 is `33d3e1756ed2bfd661698da3dfdf85a921380efd87fe3d635b777dafe3c6e04b`, and its normalized
approval-text SHA-256 is `66df8cd413fddd097e80dc63ccfacab221e96c72c795345d14b72ae1ae3474ef`. The create-new request
`tba-b7e5898e6389ff19b3ce34738f16b47d0a832dfc4625789fbcf4308352f2b1a0` stopped while attesting the
live Codex home because `goals_1.sqlite` was locked by the active coordinator session. The durable
`blocked` state SHA-256 is `ae59a6ac7f512d2e399675fe541b916d1710c209a13b45433642cf019a07df97`.
Its canonical three-entry whole-root manifest SHA-256 is
`9b01de1f550019a8bf81c23431925b6f38a173ec1ce22023c765a2a8d290cdcf`. No prompt, model process, test,
Git mutation, or product mutation occurred. The request and its entire evidence root are immutable and
terminal: they must not be retried, deleted, altered, renamed, reused, or adopted.

**Publication-4 terminal record:** Abraham supplied the exact Publication-4 Approval-1 sentence on
2026-08-15 for commit `58223098887468953570ecf153494871c5404605`. Its canonical approval file
SHA-256 is `2f74ea66ac7bdac38b419fd24b7e6caa9479de007bc178e69acd54f9f8b42857`, and its
normalized approval-text SHA-256 is `1a7698085d7bc12e74d60874e0d64b4d069b039470ab17701541cfe6c77202fe`.
The create-new request
`tba-461c20be4d35c7255a83d05f91f16c5bccbdd5a36af738360bcedc330ab6b1e4` stopped at terminal phase
`blocked` because Windows PowerShell 5.1 exposed an empty `Process.ExitCode` after the successful
`implementation-prompt-input` child. The retained stdout is valid prompt-input JSON with SHA-256
`31757cf1c4ac11f2eb6f63880e92b3a036f82e0f185866edf9ae98619c5e7681`; stderr is the empty file.
The durable state SHA-256 is `4517ecd2d5ff948bbcf7763e32686797f65b5112ceb14e71c96c8222e6e12e05`,
and the canonical nine-entry whole-root manifest SHA-256 is
`893c099e299a5152f26edd912a5bfcdc75bd69e030dfd40653c0365ffe4d5e44`. No `codex exec`, Terra/model
process, result, test, ADMIN diff, commit, or product mutation occurred; the live Codex home and frozen
Publication-3 root remained unchanged. The Publication-4 request and its entire evidence root are
immutable and terminal: they must not be retried, deleted, altered, renamed, reused, or adopted.

**Publication-5 terminal record:** Abraham supplied the exact Publication-5 Approval-1 sentence on
2026-08-15 for commit `6d292bb37c37944c71ed8b18214fabb23f22869e`. Its canonical approval-file
SHA-256 is `5ad7472cb113d6965de18204dc1b7f860a0c2982ad1e8152e34547efa714a8e3`, and its normalized
approval-text SHA-256 is `2d19ad716f3179baf67c67c77d19dfb29697ea5b2e6f2b0a0d1fe87ee03d0f47`.
Its frozen 13,450-byte external handoff is
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication5\terra-transition-handoff-6d292bb37c37944c71ed8b18214fabb23f22869e.txt`
with SHA-256 `ee92b0f882772af327d25d0bec82c9d381ff9e2f309611dd0856d0589c62030e`.
The create-new request
`tba-03e474757a5e0c92e8d3f0bd4c5a0731a742397a43c99d5e027016643fced916` passed the fixed exit-code
canary, claimed its root, and completed one real Codex implementation process requesting
`gpt-5.6-terra`/`xhigh`; Codex exposed no independent resolved-identity field.
The retained invocation requested `workspace-write`; `implementation.invocation.json` has SHA-256
`3752f8ea94fd57bb72d3d495d2ba88e8a6068d80552dc9ef9f0292714887ff36`. Its preceding prompt-input
proof had nevertheless been hard-coded to `read-only` and has SHA-256
`a50ad81bae6f73f5d85c369f5ebce0904a903a23ce90c6dced83a890d5b7ea8b`. The requested-Terra process
returned the schema-valid `BLOCKED` result “Implementation cannot proceed: this session grants
read-only filesystem access and rejects writes”; `implementation.result.json` has SHA-256
`2e56256153e3c50de8c981a1d13e53e1e18fb495276f3c34517a1ef8895c295c`. The launcher stored that
known model result as `UNEXPECTED_FAILURE` with exact error `implementation returned BLOCKED.` The
model never attempted a filesystem write: all 11 recorded command-execution starts were
inspection/read commands, with one bundled read declined. P5 therefore observed a model refusal, not
an operating-system write denial. The
durable `blocked` state SHA-256 is
`b0e9355ff3f39c1ccca196ae45ebe7c4f042c9fcd2587d84882c7d9af4724f50`; the canonical 17-entry
whole-root manifest SHA-256 is
`11f84ea3e5140a2832586f63fc362c97b92286b1663c91df2c80fb7784d6f700`. The repository remained clean
at the approved commit, all 15 ADMIN paths remained absent, the disposable Codex home was removed, and
the live Codex home plus Publication-3/4 roots remained unchanged. No test, ADMIN diff, commit, issue,
or product mutation occurred. The Publication-5 request and its entire evidence root are immutable and
terminal: they must not be retried, deleted, altered, renamed, reused, or adopted.

**Publication-6 preclaim record:** Abraham supplied the exact Publication-6 Approval-1 sentence on
2026-08-15 for commit `d0f83210e3092e18a28ee24db20a1af95887c31b`. Its canonical approval-file
SHA-256 is `064e50a53d93dc976cb98b87a5a49d0260d91f88aadddb23bcd8bf60d9be2add`, and its normalized
approval-text SHA-256 is `ad20542c0d5dc9b77fbab14413998f614ab178ca4949a1269f06c08f24b3407e`.
Its external handoff is
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication6\terra-transition-handoff-d0f83210e3092e18a28ee24db20a1af95887c31b.txt`
with length 18,494 bytes and SHA-256
`ae085575b9441080ece62194cd4a3144df809eaa9d70b2ed2fcd76624d455b47`.
The derived create-new request would have been
`tba-cc76394efc1359d75b406ce5a2d2300d5ed41020b5cf7fc972ba3039dc3a6ab0`, but the operator's
standalone, non-consuming `Preflight` produced operator-reported terminal JSON with `verdict=BLOCKED`,
`error_code=PERMISSION_ATTESTATION_FAILED`, `error_label=preclaim-permission-attestation`, full error
`[PERMISSION_ATTESTATION_FAILED] [preclaim-permission-attestation] Permissions text differs from the complete closed permission grammar.`, and
`evidence_root_absent=true`. That receipt retained no expected/actual permission hashes, line counts, or
permission text, and the staging scratch was removed by design. The earlier claim that P6 proved only a
missing writable-root line was therefore an unsupported inference and is withdrawn; P7's later evidence
does not retroactively establish P6's exact actual text. Preflight created no request/evidence root and
made no model or `codex exec` call; `Run` was not started, the repository remained clean at the approved
commit, all 15 ADMIN paths remained absent, and staging scratch, including the exact staging request
root and complete Publication-6 staging publication root, was removed. The operator-reported failure
tuple is context, not a durable P6 launcher receipt. This is a preclaim readiness failure, not a claimed
or consumed Run lineage. The Publication-6 approval and handoff remain immutable exact-publication
inputs and cannot authorize later bytes; Publication 6 must not be rerun with a modified launcher.

**Publication-7 preclaim record:** Abraham supplied the exact Publication-7 Approval-1 sentence on
2026-08-15 for commit `40d671d75e1aa6c6b31eab70caa8f4d07ed51383`. Its canonical approval-file
SHA-256 is `a849c6f49c9557ee7e11bdc4c01f324e17fe260d5abdc648141715d22120f8a5`, and its normalized
approval-text SHA-256 is `fe5736f56b0edb305ef2e1632d5882a6d85d930c06862d9ec9ce26a28b9a23aa`.
Its external handoff SHA-256 is
`c0554be563284c8fe9eb2f4aa2985505c76d39eb17dd1aeb1313dd78f3b43f81`. The derived create-new
request was `tba-f3b13b6337e230003d8721ad759b398d31536eae9d9b2bdf0860ff8b1d849568`, but the standalone,
non-consuming `Preflight` returned `verdict=BLOCKED`, `error_code=PERMISSION_ATTESTATION_FAILED`,
`error_label=preclaim-permission-attestation`, and `evidence_root_absent=true`. The expected normalized
permission text was the complete five-line canonical `workspace-write` block, SHA-256
`aa613097ace0f175545df760139a7bbc9c505a0feb207dbc2552438ce70db03d`; the actual normalized text was
the complete four-line canonical `read-only` block, SHA-256
`29dad5ed6993c5e717376e0a1c84d54ab60ee593510916ac6cee4295e803315d`. The first differing line was
line 2, whose expected and actual SHA-256 values were respectively
`06c4b2fd6aab85ab9ea0e5598cbcdead5142d7cb56e851770163c1b9f480338b` and
`d9cebe887c2ee11798faa526216e1d4af5d90cd47231862b50eb60cc5ac76464`. Thus P7 disproves the prior
P6/P7 root-line-only inference: the observed mismatch began with Codex exposing `read-only`, so the
workspace-write-only writable-root line was not the first discrepancy. No durable request/evidence root
or state exists;
the exact transient staging request root and complete Publication-7 staging publication root were
removed. `Run` was not started, no model or `codex exec` call occurred, and no implementation was
attempted. This is another preclaim readiness failure, not a claimed or consumed Run lineage. The
Publication-7 approval and handoff remain immutable exact-publication inputs, while its failure tuple
remains operator-reported historical context rather than a fabricated receipt. None can authorize
Publication-8 bytes; Publication 7 must not be rerun with a modified launcher.

**Maintenance direction:** Either controlled production family may propose a core edit; both controlled
production hosts must veto regressions. `skill-ablation` is included after the common evaluation matrix
exists. Publication 8 preserves D01–D10 and D08's workload-role bindings without change:
Fable/Sol for seed planning; Opus/Terra for controlled production, proposal, challenge, and fresh strong
gates; Sonnet/Luna for parallel advisory judging; and deterministic Pareto code for final acceptance.
Native skills remain on the invoking session: initial qualification binds Claude config alias
`opus`/`xhigh` and Codex config exact Sol/`ultra` without changing live settings. The exact native
`/build-step` and controlled-production stuck scopes may each use one same-family, read-only Fable/Sol
phone-a-friend diagnosis per authorized parent context; Fable also requires the recorded retention
policy. Judges and gates cannot invoke it.

**Terra recovery amendment:** Abraham requested the executor change because the Claude quota needed for
the Publication-2 implementation path is unavailable. Publication 8 carries forward Publication 7's
replacement of only Goal-NP
`ADMIN-BOOTSTRAP` and all 39 numbered `Type: code` orchestration slots with the amendment's direct
Codex `gpt-5.6-terra`/`xhigh` envelope. ADMIN-SYNC itself becomes a committed zero-model deterministic
operation. Publication 8 retains Publication 7's repaired process recorder, fixed `cmd.exe`
exit-0/nonzero canary, strict permission parser, and writable-root renderer. P7 requested
`workspace-write`, but its disposable Codex home supplied no Windows sandbox level; in pinned Codex
0.147.0, an absent `[windows].sandbox` resolves to `WindowsSandboxLevel::Disabled`, and Windows
configuration normalization downgrades requested `WorkspaceWrite` to `ReadOnly`. Publication 8's one
narrow recovery change is a shared closed config containing the exact
`windows.sandbox="unelevated"` setting for both debug and exec. That setting selects
`WindowsSandboxLevel::RestrictedToken`, preventing the Disabled-level downgrade while leaving the
requested sandbox mode and the complete closed permission grammar unchanged. An explicitly authorized,
disposable pre-publication A/B `codex debug prompt-input` diagnostic against the pinned 0.147.0 binary
then proved that boundary on this host: the no-override case reproduced exact SHA-256
`29dad5ed6993c5e717376e0a1c84d54ab60ee593510916ac6cee4295e803315d`, four lines, and effective
`read-only`; one exact unelevated override produced SHA-256
`aa613097ace0f175545df760139a7bbc9c505a0feb207dbc2552438ce70db03d`, five lines,
effective `workspace-write`, and one managed/restricted write path. Both exited zero with empty stderr;
no model request or `codex exec` occurred, all scratch was removed, and repository, live-auth, prior-root,
and staging predicates remained unchanged. This diagnostic is pre-publication context, not a Terra
request, receipt, state, or digest input. The repeatable, non-consuming `Preflight` must prove a
quiescent standalone
PowerShell context, complete stable live-home attestation, and the implementation-shaped model-visible
`workspace-write` permission surface before `Run` may claim a new request root. That non-model proof's
only content-bearing write surface is the fresh contained
`%LOCALAPPDATA%\SkillMesh\Staging\GoalNP\Publication8\<request-id>\permission-attestation` subtree.
That subtree contains the disposable Codex home, output, and `temp` children; both process `TEMP` and
`TMP` are pinned to that normal `temp` child for the diagnostic and every Terra model process. Preflight
may create missing normal ancestors on that fixed staging route, records their ownership, and removes
only launcher-created ancestors after proving them empty. Before PASS, the request root and every such
ancestor must be absent; Preflight writes no repository, evidence, approval, or live-home path.
`Run` repeats the proof before claim, retains that exact staging layout through the proof/model sequence,
copies the proof into the claimed root, and cleans staging in its terminal boundary. The external
operator block treats a nonzero Run as recheckable only when its exact terminal JSON proves the expected
request root absent; a present root or unproven absence is terminal and must not be retried. The ADMIN
implementation and review calls use the approved repository as primary `--cd`, omit the redundant
repository `--add-dir`, and repeat the matching prompt-input proof immediately before each model call:
`workspace-write` for implementation and `read-only` for review. A mismatch stops before that model
call. Debug and exec both consume the shared closed config, including
`windows.sandbox="unelevated"`, `skills.bundled.enabled=false`, and
`skills.include_instructions=false`; the proof must show no skills block and zero skill locators, and an
unsupported or ignored setting fails preclaim. Debug and exec share every supported explicit
model/config/disable/sandbox/cd flag. Debug does not receive the exec-only authority/output closure;
`codex exec` adds `--skip-git-repo-check`, `--ephemeral`, `--ignore-user-config`, `--ignore-rules`,
`--strict-config`, and its schema/JSON/output flags. Pinned 0.147.0 specifically rejects
`--strict-config` on `codex debug`, while the proof parser rejects any resulting ambient project/rule
content. The parser also compares the complete normalized permission/environment texts: environment
siblings are cwd, PowerShell, local `yyyy-MM-dd`, `America/Los_Angeles`, then filesystem; workspace-write
filesystem entries are read `:root`, write repository, write `:slash_tmp`, write `:tmpdir`, then read
repository `.git`, `.agents`, and `.codex`, in that order; read-only has only read `:root`. No remainder
is accepted. Publication 7 corrected the workspace-write permissions renderer: after the approval
sentence and before `</permissions instructions>`, the strict grammar requires the exact leading-space
line `` The writable root is `<canonical-owner-root>`.`` The owner root is supplied by the canonical
workspace-root field. Publication 8 leaves that five-line grammar, normalization, and strict whole-text
equality unchanged. Independent parser canaries must
reject a missing annotation and a wrong-root annotation, so the accepted canary cannot reproduce the
same omission unnoticed. A mismatch reports only deterministic expected/actual whole-text SHA-256
values, line counts, the one-based first differing line number, booleans saying whether that line exists,
and nullable hashes for only those two lines—never raw permission text, path-bearing line content, or
other line-hash arrays—before scratch is removed. The fresh request digest binds exactly 22 LF-joined,
no-final-LF fields: P8 domain/commit/approval text; P7 commit/request/approval text/approval file/handoff;
the same five P6 fields; then the P5/P4/P3 request/state/root-manifest triples. P7 and P6 evidence-request,
staging-request, and staging-publication absences remain live predicates, not digest literals. The new
Windows proof and diagnostic metadata are launcher readiness/state fields, not additions to the
unchanged model-result schema. Before and after each ADMIN
exec, complete scratch manifests must show no
`codex-home\skills\.system`. After a zero exit, the JSONL transcript must be nonempty and every line
must be a nonempty, parseable single event object; executable request fields may not reference a
`.system/.../SKILL.md` path and no native skill event/type is allowed. Model/output text is not an
executable-request surface. Timeout, start/handle, and nonzero-exit failures preserve their terminal
process code after the scratch check and do not claim transcript acceptance. A detected transcript
violation is `MODEL_VERDICT_INVALID`. In those ADMIN calls, every Codex/model/CLI name and behavior is a frozen
approved input to generic local code/review, not authority to discover or validate current OpenAI/Codex
product facts. No skill or transitive skill-tree authority is available; if the model says one is
required, it returns schema-valid `BLOCKED` before mutation and never expands network access. Known
schema-valid
non-PASS model verdicts receive stable terminal failure codes rather than
`UNEXPECTED_FAILURE`, and the external operator block is one fail-stop script scope so a failed action
cannot fall through to later parsing or inspection commands.
This does not turn Terra into a
native-qualification session, change D08's controlled evaluation assignments, remove Claude from
NP-12/NP-40, add a router/fallback, authorize a live-home write, or create another approval gate.

**Redline feedback:** Abraham accepted D01–D07 and D09–D10 on 2026-08-14, pending Approval 1, and
requested investigation/revision of D08. The investigation found that publication 1 mixed an
unstated workload-role mapping with stale Opus 4.8 wording. Publication 2 makes the controlled-role
basis, native-session boundary, fresh-context grading cascade, and bounded two-scope phone-a-friend
exception explicit without inferring Claude's effective identity from its `opus` alias.
This feedback is not Approval 1.

**Review sequence:** Publication 8 must first pass the unchanged repository-root `python -m pytest`,
then complete plan-review, plan-redline, and plan-wrap with required verdicts PASS, PASS, and READY on
one stable ten-file bundle. Exact-byte verdicts are retained
outside the publication; any blocking verdict or hash drift
returns this status to revision. The standalone proposal maps P01–P10 to Abraham's choices and D01–D10
to the preserved agent defaults.

**Publication-8 review correction record:** This is a reconstructable chronology of superseded
planning candidates, not publication evidence:

- **A - initial six-file candidate:** plan-review returned `FAIL` because the launcher would claim a
  request root before running a baseline gate already known red at clean P7 and because documentation
  gaps remained. No approval, commit, request, or evidence resulted. Abraham then authorized only the
  bounded baseline-gate repair and this Publication-8 revision.
- **B - first eight-file candidate after that authorized repair:** plan-review returned `PASS`; the
  following plan-redline returned `FAIL` on the legacy review-order contradiction, incomplete operator
  chain, proposal order and source metadata, and revision grammar. Correcting those findings changed
  bytes and invalidated the preceding plan-review PASS.
- **C - corrected eight-file candidate:** plan-review returned `PASS`; the following plan-redline
  returned `FAIL` because the same unqualified `defect_inventory_sha256` named both LF-normalized
  builder bytes (`98baaa178e41dc23e5de70e3161de78c66b9c91052c4d0d99295ae1a8928ed37`) and raw CRLF sealed-probe
  bytes (`24c336217fba1a6d1d177b754a34be77275e0c797a50d48ea0a7e5d9401c2752`). Expanding the bundle to
  repair that boundary invalidated both verdicts.
- **D - first ten-file candidate:** its exact-byte tests passed, but fresh plan-review returned `FAIL`
  because monolithic `Run` bypassed `load_prepared` and post-host inventory-digest enforcement, the
  negative tamper regression was missing, and this review provenance was incomplete. Plan-redline and
  plan-wrap did not run. No approval, commit, request, or evidence resulted.
- **E - corrected ten-file candidate after the direct-Run boundary repair:** fresh plan-review returned
  `FAIL` because its negative regression called `execute_review` directly and the documents claimed
  inventory drift produced no report, while production `main()` intentionally publishes bounded
  `AMBIGUOUS` failure evidence for both `Run` and `InvokeSavedHandoff`. Plan-redline and plan-wrap did
  not run. No approval or commit resulted. That review is non-evidentiary, non-authorizing, and
  non-reusable; it created no durable launcher record, receipt, state, request root, or Publication-8
  evidence root.

The current narrow closure makes `Run` reopen its sealed handoff through `load_prepared`. After the
host returns and response-contract handling completes, `execute_review` performs one bounded inventory
read, hashes those bytes against the receipt immediately before inventory JSON parsing and grading, and
then parses those same bytes. Production-path negative tamper regressions drive both `Run` and
`InvokeSavedHandoff` through `main()` and prove that inventory drift fails before grading and before
normal-result reduction or publication. The only final publication is the bounded `AMBIGUOUS` failure
pair, `report.md` plus `MANIFEST.sha256`: it records the integrity failure, fixes
`detected_defect_count` at `0`, keeps uncertainty-bearing reviewer and resolution fields `UNCERTAIN` or
unavailable, and contains no grade or normal/conclusive result. This preserves the established status
contract: `COMPLETE` means bounded evidence publication completed, while `AMBIGUOUS` means the
experiment reached no conclusion. Every external reviewer output above is planning/review context only:
it is non-evidentiary, non-authorizing, non-reusable, and created no durable launcher record, receipt,
state, request root, or Publication-8 evidence root. The current revised ten-file bytes must restart and
complete plan-review `PASS` -> plan-redline `PASS` -> plan-wrap `READY` in that order.

**Revision grammar (not an approval):**

```text
REQUEST ANOTHER REVISION - NOT AN APPROVAL
D01|D02|D03|D04|D05|D06|D07|D08|D09|D10 -> <replacement choice>
Terra Windows sandbox-enforcement recovery -> <requested change>
NP-<NN> -> <requested change>, where <NN> is 01 through 41
Section <section name> -> <requested change>
```

**Implementation authority:** none until Abraham approves the exact reviewed Publication-8 bundle with
the exact recovery sentence. No Publication-8 `Preflight`, `Run`, model call, or implementation step is
authorized before that fresh approval. Publications 3, 4, and 5 supply terminal historical evidence;
Publications 6 and 7 supply immutable approved preclaim records without a request root or consumed Run
lineage.

**Required recovery Approval-1 sentence:**
`Approve Goal NP plan Publication 8 with D01-D10 and the Terra Windows sandbox-enforcement recovery amendment.`
*(Never given. Superseded 2026-08-16 — see the course-change entry below. Retained as history.)*

### Course change — 2026-08-16

Goal NP is **closed unapproved**. Four operator ratifications on 2026-08-16 ended the approval
treadmill and moved delivery to `documentation/codex-parity-delivery-plan.md` (Phase CP), where they
are recorded as P1–P4 in the Decision Inventory:

| # | Ratification | Consequence here |
|---|---|---|
| a | **Terra executor amendment reverted** — implementation is Claude-led | The `gpt-5.6-terra`/`xhigh` envelope above is history; no Codex executor is provisioned |
| b | **Publication 8 closed unapproved; launcher parked** | Its ten-file bundle is committed as historical record; `tools/run-goal-np-terra-bootstrap.ps1` is never invoked. Do not rename it — a path-choke exemption is keyed to that exact path |
| c | **The exhaustive 113-cell qualification matrix downgraded from gate to backlog** | Representative smokes plus a running parity delta log are the gates. Real-host evidence (Phase CP M1–M3) replaces the matrix |
| d | **Additive/destructive track separation** | Additive installs proceed under scoped approvals; destructive legacy retirement and live cutover leave scope entirely for a future plan with its own approval packet |

Why the change: Publications 3–7 consumed five review generations plus an independent boundary audit
without ever producing an approved, executable bundle. Each cycle re-litigated an approval envelope
rather than shipping a skill. Phase CP inverts the order — ship a five-skill pilot to a real host,
measure it, and let recorded deltas rather than a pre-agreed matrix decide what is worth fixing.

What survives from this journal: the format and placement research for Codex skill packages, the
proven `codex exec` + `--output-schema` cross-family result, and the preserved Step-4 work. What does
not survive: the two-approval publication gate, the Terra bootstrap execution path, and the exhaustive
per-skill × per-host matrix.

## Goal A journal

This section records status and evidence only. Acceptance remains in `documentation/skill-mesh-recovery-plan.md`.

**GoalAId:** `goala-20260814T021737Z-1b5ec416`

**Approved contract blob:** `d97b1960b01673ab8922adc806f7c0de76ba33a3`

**Approval:** Abraham approved continuation against this normalized blob in the Goal A session on 2026-08-13.

**Planned branch:** `recovery/goala-20260814T021737Z-1b5ec416`

**Planned worktree:** `%LOCALAPPDATA%\SkillMesh\Worktrees\goala-20260814T021737Z-1b5ec416`

### Step 72: Preserve the exact Step 4 work

**Status:** DONE

**Evidence:** `%LOCALAPPDATA%\SkillMesh\Recovery\skill-mesh-step-4-20260814T021546Z-73e9e215\manifest.json`

The manifest records 14 files, `apply_check=PASS`, `hash_match=PASS`, and the unchanged source index hash. A pre-destination PowerShell stderr failure is retained under `%LOCALAPPDATA%\SkillMesh\Recovery\skill-mesh-step-4-preflight-failure-20260814T021521Z-64adbbf1\`.

### Step 73: Establish canonical plan authority

**Status:** DONE

**Authority commit:** `8d8b57a`

**Issue notes:** [#70](https://github.com/aberson/skill-mesh/issues/70#issuecomment-5288812441), [#71](https://github.com/aberson/skill-mesh/issues/71#issuecomment-5288812561), [#72](https://github.com/aberson/skill-mesh/issues/72#issuecomment-5288812663), [#73](https://github.com/aberson/skill-mesh/issues/73#issuecomment-5288812790), [#74](https://github.com/aberson/skill-mesh/issues/74#issuecomment-5288812922), [#75](https://github.com/aberson/skill-mesh/issues/75#issuecomment-5288813029), [#76](https://github.com/aberson/skill-mesh/issues/76#issuecomment-5288813128), [#77](https://github.com/aberson/skill-mesh/issues/77#issuecomment-5288813238), [#78](https://github.com/aberson/skill-mesh/issues/78#issuecomment-5288813348), [#79](https://github.com/aberson/skill-mesh/issues/79#issuecomment-5288813499), [#80](https://github.com/aberson/skill-mesh/issues/80#issuecomment-5288813627), [#81](https://github.com/aberson/skill-mesh/issues/81#issuecomment-5288813730), [#82](https://github.com/aberson/skill-mesh/issues/82#issuecomment-5288813810), and [#116](https://github.com/aberson/skill-mesh/issues/116#issuecomment-5288813896).

**Bootstrap evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\bootstrap.md`

### Step 74: Prepare the lifecycle fixture

**Status:** DONE

**Candidate commit:** `0c72392ec51da5201c4f3c17272e2b79a32a055d`

**Superseded candidates:** `3a17746fa1d04c24088effd8f3871afe10f1601f`,
`0d06c42916f8953ec37f1a96e89b8a37cf82a77b`

**Evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\evidence-index.md`

**Preflight evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\step75-preflight-timeout.md`

The first Step 75 command stopped before creating an evidence directory, disposable home, or host
process. A read-only diagnostic measured 141 seconds to hash 2.93 GB across 41,435 protected
records. Executed candidate `3a17746fa1d04c24088effd8f3871afe10f1601f` uses fixed 600-second
and 630-second bounds. It passed the exact 262-test focused and package-integrity gate plus three
independent reviews. After the Step 78 full gate exposed a structural mutation-containment gap, the
new candidate `0c72392ec51da5201c4f3c17272e2b79a32a055d` passed the 28-test lifecycle suite,
the 9-test path-choke suite, the ASCII and private-path gates, and two independent reviews. It has
not run against either live host. Full-root coverage and the 100,000-record limit remain unchanged.

### Step 75: Run the lifecycle experiment

**Status:** DONE — both host series returned `AMBIGUOUS` before host invocation

**Executed candidate:** `3a17746fa1d04c24088effd8f3871afe10f1601f`

**Claude evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\lifecycle\lifecycle-claude-20260814T065643Z-e1ea3dd1\a0\report.md`

**Codex evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\lifecycle\lifecycle-codex-20260814T065645Z-34c7074f\a0\report.md`

Protected Codex database files changed during both safety-preflight intervals; attribution is
unavailable. The runner retained valid reports and manifests, removed each disposable home, and
launched no host command. These runs do not support a native-lifecycle conclusion.

### Step 76: Prepare the cross-family fixture

**Status:** DONE

**Candidate commit:** `7b094897a0e7afc4ffecaeac15f20d2d875614c8`

**Superseded candidate:** `8db941720cccbdf28dc1eadb32d51bf3c8c91550`

**Evidence:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\evidence-index.md`

The fixture uses one deterministic synthetic candidate for both directions. This isolates the review handoff. It does not claim that a live Claude-family or GPT-family builder authored the candidate.

The exact final bytes passed 41 focused tests, the private-path gate, PowerShell parsing, and `git diff --check`. Three independent read-only reviews passed each bounded correction. No reviewer host, model, or protected live-home scan ran during candidate preparation.

The first Step 77 `a0` attempt stopped before reviewer launch because its complete 41,437-record snapshot was 19,750,121 bytes, above the 16 MiB general evidence cap. The retained report is `AMBIGUOUS`. The replacement candidate gives only raw snapshot files a separate 64 MiB cap. All other evidence keeps the 16 MiB cap. The 100,000-record and 600-second safety bounds do not change.

The two manual `a1` attempts both started exactly one contained host and cleaned the disposable fixture. Codex refused its intentionally empty working directory because `--skip-git-repo-check` was absent. Claude rejected the standard schema's draft declaration before review. Neither attempt produced a model review. The final correction is limited to those two native CLI preflight mismatches; isolation, model selection, fallback, evidence, and snapshot rules do not change.

### Step 77: Run the cross-family experiment

**Status:** DONE — all four final series returned `AMBIGUOUS`

**Evidence root:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\`

**Retained `a0` report:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-claude-to-gpt-manual-saved-handoff-20260814T085608Z-cbbf95ed\a0\report.md`

**Retained Codex `a1` report, requested `gpt-5.6-terra`:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-claude-to-gpt-manual-saved-handoff-20260814T085608Z-cbbf95ed\a1\report.md`

**Retained Claude-host `a1` report, requested `sonnet`:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-gpt-to-claude-manual-saved-handoff-20260814T085608Z-ec7c31e9\a1\report.md`

**Final manual Codex report, requested `gpt-5.6-terra`:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-claude-to-gpt-manual-saved-handoff-20260814T085608Z-cbbf95ed\a2\report.md`

**Final manual Claude-host report, requested `sonnet`:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-gpt-to-claude-manual-saved-handoff-20260814T085608Z-ec7c31e9\a2\report.md`

**Final dispatcher Codex report, requested `gpt-5.6-terra`:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-claude-to-gpt-reviewer-only-dispatcher-20260814T085608Z-40b14e58\a0\report.md`

**Final dispatcher Claude-host report, requested `sonnet`:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\cross-family\cross-gpt-to-claude-reviewer-only-dispatcher-20260814T085608Z-c450d8b6\a0\report.md`

Both Codex runs requested `gpt-5.6-terra`, completed one real review, returned `NEEDS_WORK`, and
detected all three seeded defects. Codex exposed no allowlisted resolved-model field. Protected
database files changed during both intervals; attribution is unavailable. Both Claude-host runs
requested `sonnet` and returned `401` because the saved OAuth token had expired. All four attempts
proved Job Object containment and disposable cleanup. The correction-attempt budget is exhausted.

### Step 78: Prepare Gate A

**Status:** DONE

**Lifecycle summary:** `documentation/evidence/goal-a/goala-20260814T021737Z-1b5ec416/lifecycle-report.md`

**Cross-family summary:** `documentation/evidence/goal-a/goala-20260814T021737Z-1b5ec416/cross-family-report.md`

**Summary manifest:** `documentation/evidence/goal-a/goala-20260814T021737Z-1b5ec416/MANIFEST.sha256`

**Decision packet:** `documentation/decisions/gate-a.md`

**External full gate:** `%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\gate-a-full-gate.md`

The two committed summaries are bound by SHA-256. Every recommendation cites the raw reports and
manifests. Focused experiment and package-integrity tests passed. Both distributions built. The
repository-root full gate passed on the final Goal A candidate recorded in the external report.

## Gate A journal

**Status:** APPROVED

**Final gate action:** `stop`

**Execution status:** STOPPED — approved contract terminal action `stop`

**Proceed eligibility:** INVALID — no architecture is selected and Goal B authorization is `no`.

**Decision locator:** Abraham's 2026-08-14 direct conversation response supplying the exact three
terminal values below after the bounded follow-up result was reported.

| Terminal record field | Approved value |
|---|---|
| Gate action | `stop` |
| Goal B authorization | `no` |
| Live cutover | `not-authorized` |

**Bounded-follow-up outcome:** The exact experiment `goal-a-quiescent-qualification-v1` was invoked
once. Claude lifecycle `a1` returned `FAIL` before the explicit update command because a fresh
consumer returned the candidate v2 marker where the acceptance criterion required installed-v1.
The committed stop rule prevented Codex lifecycle `a1` and the Claude reviewer dispatcher `a0-r1`
from running.

**Claude `a1` evidence:**
`%LOCALAPPDATA%\SkillMesh\Evidence\goala-20260814T021737Z-1b5ec416\lifecycle\lifecycle-claude-20260814T065643Z-e1ea3dd1\a1\report.md`

**Raw evidence hashes:** report
`a3b2a90e4ac72b4964db1650cc4812a0646b9e98f78d178c591f912a36933d4f`; manifest
`33001429c8d2cdf5d22cf4c30fc4590a49a6376451401137b693b30dcc91ddd9`; final external index
`94d26b399bf700b66d986cde6973023eeaafc9325077621718e4ddbaccb7078f`.

**Committed summary hashes:** lifecycle
`64cbfb215d567113cb2b3f7ffef9b66e5883b556ee95568f8b26a3c07d2970b1`; cross-family
`847d58d0479f721d6cc1146ef945a53ee45c54640cbd4780076897790957bdac`; two-report manifest
`301cd34f4667dd56ed17827ea7658c6fba396531fb68f9064d8b12b86dc9be95`.

**Safety and cleanup:** Isolated copied-file authentication passed. All started processes were
Job-contained. Protected live state matched before and after. The disposable home was removed. The
raw provider output reported both Haiku and Sonnet usage, so one resolved model identity is not
established. Raw evidence remains sealed and unchanged.

### Historical bounded-follow-up approval — consumed

**Approval locator:** Abraham's 2026-08-14 conversation response containing `(3) Approve`, directly
answering the immediately preceding authorization prompt that named the exact experiment, commit,
scope, stop rules, and every field below.

**Approved experiment:** `goal-a-quiescent-qualification-v1` in the Gate A packet at commit
`215618be14bbba2aa3130a99dea3fffa96bed071`, with no argument, candidate, attempt, path, scope, or
stop-rule change.

| Approved field | Value |
|---|---|
| Gate action | `bounded-follow-up-experiment` |
| Lifecycle owner for Claude Code | `deferred-by-follow-up` |
| Lifecycle owner for Codex | `deferred-by-follow-up` |
| Step 4 disposition | `deferred-by-follow-up` |
| Cross-family mechanism | `deferred-by-follow-up` |
| Permitted cross-family direction | `deferred-by-follow-up` |
| Copilot disposition | `quarantine` |
| Resolved-identity waiver | `none` |
| Existing control branch | `reference-only` |
| Goal B authorization | `no` |
| Live cutover | `not-authorized` |

**Authentication evidence:** Abraham reported that normal Claude Code authentication was completed
and a 2026-08-14 Haiku smoke call returned the single word `ok`. The smoke ran with an ambient Claude
OAuth environment variable, so it does not independently prove the runner's isolated copied-file
credential path; the runner's disposable `auth status` check remains authoritative. The related
ignored outer-workspace settings correction is outside the Goal A worktree and is not an experiment
input.

**Quota decision:** Abraham reported Claude Max usage at 98 percent used and explicitly chose to run
the one authorized follow-up now rather than wait for reset. A quota or authentication failure is a
stop result. It does not authorize a retry, correction, fallback model, or changed argument.

**Offline handoff:** Abraham reported closing Claude Code, Codex CLI, ChatGPT desktop, VS Code, and
all agent sessions, then running the committed block once from Windows PowerShell 5.1. The resulting
stop condition consumed the authorization. The block must not run again.

Goal A is ended. Phase 2, Goal B, product implementation, Step 4 use, live-home writes, merge, and
live cutover remain locked. No retry, correction, fallback, or additional experiment is authorized.
