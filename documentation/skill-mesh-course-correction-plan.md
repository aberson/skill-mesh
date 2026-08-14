# Skill Mesh course-correction plan

**Status:** REDLINE APPROVED — SUPERSEDED FOR EXECUTION (2026-08-13)

**Recommendation:** make targeted changes, then proceed

**Proposal:** `documentation/skill-mesh-course-correction-proposal.html`

**Canonical entry plan:** `plan.md`

**Final execution contract:** `documentation/skill-mesh-recovery-plan.md`

**Current implementation:** Step 4 / issue #116 is frozen in place but is not yet durably preserved: its four implementation files are still uncommitted on `main`. R0 must capture and verify an exact recovery artifact before any experiment. This document does not authorize implementation edits, installation, migration, issue closure, or live cutover.

## Provenance

- **Requested by:** Abraham Robison
- **Prepared from:** Abraham's stated goals and feedback; the Step 4 transition prompt and checkpoint; repository plans, Git history, code, tests, and current worktree; read-only Dev Observatory inspection; and current vendor documentation
- **Purpose:** the approved decision record that preceded the final goal, canonical plan, and build phases.
- **Approval:** Abraham Robison replied `Approve D1-D15 as written` on 2026-08-13.
- **Interpretation rule:** Abraham's recollection is treated as useful product intent, not as a claim that every historical detail is exact. Repository evidence controls factual statements about the implementation.

---

## 1. Executive recommendation

Do **not** continue Step 4 as-is, do **not** throw Skill Mesh away, and do **not** add another provider or orchestration framework now.

Take a bounded course correction:

1. Durably preserve and freeze the current Step 4 work, then install the immediate manual change controls.
2. Run two disposable experiments: one for Claude Code/Codex package lifecycle, and one for the separate Claude-family/GPT-family review execution seam.
3. Halt for Abraham to choose the architecture. Experiment results recommend; they do not authorize their own branch.
4. Repair the minimum build-control outcomes that currently make plans advisory, Nits blocking, uncertainty inconsistent, reviews mutable, and full-suite gates repetitive.
5. Audit and retarget the current Copilot-specific host layer to native Codex, then resume product work against a narrower Skill Mesh charter: portable workflow contracts, model-role policy, conformance, behavioral evaluation, and run receipts.
6. Prove the release with representative end-to-end runs on Claude Code and Codex, including at least one real cross-family builder/reviewer case and honest requested-versus-resolved model evidence.
7. Connect a redacted projection of the same receipt to Dev Observatory. Re-redline genuine utility hookups as an independent board-completion track.

This retains the parts unique to Abraham's toolkit while retiring or sharply reducing the subsystem that caused the present delay if host-native lifecycle support is sufficient.

---

## 2. Corrected diagnosis of the delay

### 2.1 The experiment was run

The earlier framing that Abraham should have run a thin experiment was too strong. The workspace-level `documentation/utility-hookup-plan.md` (outside this public repository, lines 254-258 as inspected on 2026-08-13) records a measured reproduction: an ordinary reinstall overwrote a customized marker-bearing skill, returned success, and created no backup. That is a valid experiment and a valid safety finding.

The lesson is not merely `see issue -> experiment -> fix`. It is:

> **Observe -> reproduce and measure -> classify the result -> sketch the smallest options -> if the remedy changes architecture or scope, rebaseline and approve it -> commit and synchronize plan/issue -> implement.**

The missed control was after the experiment. That workspace plan said it was not safe to execute, its Step 4 rewrite was uncommitted, and its declared files covered the installer, distribution tests, and documentation (lines 264-266 as inspected on 2026-08-13). Issue #116 and the implementation then expanded into the legacy migrator, migration tests, a write-ahead authority record and recovery protocol, and a home-operation lock.

The current four-file diff is `+1,843/-277`; two of the four files are outside the plan's declared Step 4 file list. This is not evidence that the safety work is bad. It is evidence that a bounded installer repair became a new safety-critical state-machine project without an explicit course-change decision.

### 2.2 The original product goals also changed

The original direction was Claude-first workflows with GPT-family fallback/alternate review. The refactor legitimately improved provider-neutral cores and host discovery, but it conflated two axes: a **host adapter** (`Claude Code`, `GitHub Copilot`, `Codex`) is not a **model family** (`Claude`, `GPT`). Normal host-native invocation also bypasses the provider router. Consequently:

- Claude Code/GitHub Copilot packaging and discovery parity are substantially delivered. The current `.github/skills` wrappers, environment assumptions, and tests are Copilot-specific; native Codex packaging is a new audit/retarget target, not an already-shipped capability.
- Cross-family judging, exact model-set provenance, and automatic provider fallback are not consequences of that architecture and are not yet proven.
- The program spent significant effort proving distribution, migration, and installer safety while the original cross-model behavioral outcome remained untested.

That is a real course change, not merely README drift. The final plan must either restore those goals explicitly or retire them explicitly. This proposal restores the valuable parts, but narrows where they are mandatory.

### 2.3 The additions were reasonable; their costs were not made visible

Multiple reviewer lenses, Claude plus GPT, deterministic tests, and a future local-model lane were individually reasonable ideas:

- reviewer diversity can improve max-min defect coverage;
- cross-family review may catch correlated blind spots;
- deterministic tests should remain the primary correctness gate;
- local models may reduce cost for narrow work.

The error was not “more is always bad.” It was allowing individually sensible assurance mechanisms to compound without asking which outcome each uniquely proved, what matrix it multiplied, and what could be deferred until evidence justified it. Local/Gemini expansion should have waited; cross-family value should be measured; repeated full-suite and review gates should be deduplicated.

---

## 3. Proposed product charter

### Skill Mesh owns

- Portable workflow contracts and canonical skill behavior.
- Thin Claude Code and Codex bindings. The Codex binding is prospective until the Copilot-specific layer is audited and retargeted.
- Model roles, qualified model-pair policy, and explicit fallback policy.
- Conformance checks that distinguish package discovery from behavioral correctness.
- Representative behavioral evaluations and adversarial fixtures.
- Versioned run receipts showing what was requested, what ran, what evidence was produced, and what was deferred.
- Compatibility generation only where a host requires it.

### Host-native systems own, when proven sufficient

- Installation, update, discovery, cache/version management, disable, and uninstall.
- Host-specific permission and session mechanics.
- Their own package manifests and marketplaces.

Current vendor documentation supports testing this boundary: Codex plugins use a `.codex-plugin/plugin.json` package with bundled skills and lifecycle hooks, while Claude Code plugins provide versioned skills and marketplace-managed install/update/uninstall. These are research inputs, not proof that both work for this repository on Abraham's Windows setup.

Package lifecycle and cross-family execution are independent decisions. Native packaging can answer how a workflow is installed and discovered; it does not answer how a Claude-hosted workflow asks a GPT-family reviewer to run, or how a Codex-hosted workflow asks a Claude-family reviewer to run. Skill Mesh must choose and receipt that review seam separately.

### Dev Observatory owns

- Bounded ingestion and normalization of producer-owned evidence.
- Freshness, error, and compatibility display.
- Artifact-backed `summary`/at-a-glance views for run evidence.
- Mechanical Transparency views for caller/consumer wiring. Transparency is not an artifact viewer and does not prove a run occurred.

Dev Observatory is a consumer, not Skill Mesh's runtime broker and not proof that a workflow is wired merely because a static page exists.

### `utility-project-standard` owns

- Portfolio profiles, conformance manifests, evidence vocabulary, contract-owner declarations, and publication rules.
- It remains a standalone standard. Dev Observatory should not own its folder or become its normative authority.

A future Skill Mesh `utility-project.toml` may declare the receipt/export contract's owner, version, and locator after Utility Project Standard v1 stabilizes. The standard should not absorb the receipt schema until a second producer genuinely needs the same shape, and its unfinished v1 is not on the Skill Mesh release critical path.

---

## 4. Requirement calibration

`Introduced by` records provenance. `Commitment` uses only `hard | preferred | experiment | not-now`. A hard requirement states the harm if it is relaxed; conditions and graduation live in the treatment column rather than inventing a fifth commitment value.

| ID | Requirement | Introduced by | Commitment | Release treatment / harm if hard |
|---|---|---|---|---|
| R1 | Real Claude Code and Codex execution | Abraham | hard | Without both, the named target-host goal is unmet. Copilot is not a release target. Proposed Codex package surface is CLI/ChatGPT desktop because current official documentation excludes the IDE extension from plugin support. |
| R2 | Materially consistent workflow contracts across hosts | Abraham | hard | Without contract/artifact/safety consistency, the user must reason about two toolkits. Identical prose, latency, and hidden reasoning are not required. |
| R3 | Requested identity and resolution status are always visible | Abraham | hard | Otherwise fallback/alias behavior can be silently misrepresented. Every receipt records the request plus `resolved | unavailable | unverified | mismatch`. |
| R4 | Actual resolved identity is observed for release/eval lanes | Abraham | hard | Otherwise exact-model transparency is not proven. A target lane with unavailable identity requires an explicit Abraham waiver and exact requested-pin evidence; the release cannot silently pass with every lane unavailable. |
| R5 | No silent fallback or inferred provider/model identity | Abraham + review | hard | Otherwise the receipt can claim an execution that did not occur. Fallback must be policy-authorized, reasoned, and receipted. |
| R6 | At least one real representative cross-family review | Abraham | hard | Without it, the central cross-family goal remains theoretical. This is a release proof requirement even if measured quality gain is small. |
| R7 | Cross-family review at ongoing high-risk seams | Abraham | preferred | Keep the practice selectively; do not require it for every routine invocation. |
| R8 | Claim that cross-family review adds marginal quality | Abraham + review | experiment | Calibrate against seeded defects and report cost/latency/no-value evidence; do not promise a “holy grail.” |
| R9 | Exact pins for release/eval/high-risk runs where supported | Abraham | hard | Without a pin or named waiver, the qualified result cannot be reproduced. Routine work is governed separately by R10. |
| R10 | Qualified aliases for routine runs | Abraham + review | preferred | Reduce alias maintenance while retaining requested/resolved evidence and requalification triggers. |
| R11 | Robust automatic fallback | Abraham | preferred | Permit only at an explicit role boundary with an ordered policy. A direct native call must not claim fallback it cannot perform. |
| R12 | Every skill/model/host permutation in release proof | inferred | not-now | Use representative behavioral proof plus deterministic conformance for the remainder. |
| R13 | Utility hookups as a Skill Mesh architecture-release predecessor | inherited board sequence | not-now | Keep overall board completion, but run it as the independent U track with no dependency into the architecture release. |
| R14 | Local/Gemini and broad provider expansion | Abraham, exploratory | not-now | Revisit after Claude/Codex release evidence and a cost baseline. |
| R15 | Omnigent adoption or dependency | Abraham, exploratory | not-now | Keep the independent lab and `documentation/omnigent-revisit-seed.md`; do not integrate now. |
| R16 | Quality over a calendar deadline | Abraham | preferred | Prefer sound evidence over schedule pressure, while still enforcing scope checkpoints and explicit rebaseline. |

### Requested versus resolved model

- **Requested model:** the configured identity or qualified alias selected for a role, such as `gpt-5.6-terra`.
- **Resolved model:** the actual server/host-reported model or snapshot that executed.
- If a host accepts an alias but does not reveal the resolved snapshot, record `resolved_status: unavailable` or `unverified`; never copy the requested value into the resolved field by inference. That lane needs an explicit Abraham waiver before release.
- Release, evaluation, and high-risk runs use an exact pin/snapshot where the host supports it. Routine runs may use a qualified alias to reduce maintenance burden.
- `Fable -> Sol` and `Sonnet -> Terra` are candidate qualified peers, not assumed equivalents. The current map already has Fable -> Sol but still maps Sonnet -> `gpt-5.4`; no map change is authorized until qualification evidence exists.

---

## 5. Proposed anti-goals

These are product boundaries, not claims that the ideas have no value.

1. Skill Mesh will not become a general framework-of-frameworks or replace the native Claude/Codex runtimes.
2. Provider count is not a success metric. Claude Code and Codex are the release surfaces.
3. “Same experience” does not mean identical wording, latency, hidden reasoning, or model behavior. It means the same contract, safety invariants, artifact schema, and visible variance.
4. Skill Mesh will not silently fall back, silently relabel a model, or infer model/provider identity from an adapter name.
5. The release will not require every skill/model/host permutation. Representative proof plus deterministic conformance is sufficient.
6. Skill Mesh will not own host lifecycle when a host-native package passes the lifecycle experiment **and Abraham approves that branch**.
7. Dev Observatory will not become a runtime dependency for invoking a skill.
8. A Skill Mesh receipt will not replace genuine functional calls to utilities such as Heads Up or Tripwire where those behaviors are intentionally needed.
9. `utility-project-standard` will not become a Dev Observatory subproject and will not prematurely standardize a one-producer receipt shape.
10. Omnigent, local models, Gemini, and Copilot are not part of this release.
11. The current Step 4 write-ahead authority implementation is neither discarded nor presumed correct. It is frozen in place and becomes a durable option only after R0 captures and verifies a recovery artifact.
12. Prompt-size reduction and full multi-file skill decomposition will not be smuggled into the product recovery. The architecture must first be redesigned and forward-tested explicitly; the current `skill-iterate` can only help later with scorable, installed single-file hill-climbing, not canonical multi-file decomposition.

Prompts for future anti-goal generation should ask:

- Which tempting adjacent capability distracts from the release outcome?
- Which responsibility does another tool or host already own?
- Which failure should be explicit instead of hidden by fallback?
- Which metric could be gamed without improving user outcomes?
- Which future option should remain possible but not be built now?

---

## 6. Two independent architecture experiments

Package distribution and cross-family execution solve different problems. Neither experiment authorizes its own architecture; each produces evidence and a recommendation, then R2 halts for Abraham's choice.

### 6.1 Native package-lifecycle experiment

#### Hypothesis

Claude Code and Codex native plugin/package systems can own normal Skill Mesh install, discovery, version/update, disable, and uninstall while Skill Mesh supplies canonical workflows and thin host bindings.

#### Scope budget

- Use disposable host profiles/homes and a disposable fixture repository only.
- Use a unique, versioned probe package and skill name such as `skill-mesh-lifecycle-probe-<run-id>`. Do not use ordinary `plan-redline`, which may already exist in a discovery root and create a shadowed/phantom success.
- Structurally package two named probe skills, one shared reference, and one small helper script or auxiliary asset; invoke one bounded behavior. This tests package shape without pretending one probe proves complex-skill parity.
- Test only Claude Code and a currently supported Codex plugin surface (CLI and, if useful, ChatGPT desktop). An IDE-extension-only requirement is PARTIAL/FAIL because the current IDE extension does not support plugins.
- Capture the resolved package/source locator so discovery cannot pass from a stale root.
- Do not edit the current installer/migrator WIP or build a shared production packaging framework inside the spike.
- Allow at most two diagnosis/correction attempts per host before reporting an ambiguous or failed result.

#### Required observations per host

1. Validate/package from one canonical probe source.
2. Install to an isolated user/profile scope.
3. Discover and invoke the unique name without an explicit filesystem path; prove the resolved package/source locator.
4. Load the shared reference/helper from inside the installed package.
5. Update to a distinguishable second package version and prove which version runs.
6. Disable/uninstall and prove the unique skill is no longer discovered.
7. Preserve or clearly reject consumer-owned bytes; no silent overwrite.
8. Record host, package version, requested model, resolved model/status, permission mode, source commit, result, and evidence locators.

#### Recommendation table

| Result | Experiment recommendation presented at R2 |
|---|---|
| Both hosts pass | Recommend native lifecycle as primary. Compare a one-time manual backup/cutover/retirement with a bounded legacy utility; do not automatically retain a migration/export/uninstall subsystem. |
| One host passes | Recommend native lifecycle for that host and present the smallest explicit compatibility option for the other; do not rebuild a universal installer without a new redline. |
| Both fail for documented host limitations | Recommend re-chartering the installer as its own safety subsystem with exact files, state model, recovery invariants, and acceptance budget. |
| Ambiguous | Recommend STOP. Preserve evidence and identify the missing operator premise; do not convert ambiguity into implementation. |

### 6.2 Cross-family reviewer execution-seam experiment

#### Hypothesis

At least one Claude-family/GPT-family review can run with exact receipted provenance without restoring a general-purpose router to every host-native skill invocation.

#### Scope budget

- Audit current host and model layers separately: Claude Code bindings, Copilot-specific `.github/skills` bindings, any native Codex package support, and the provider router/transport.
- Use one disposable repository with seeded review defects and an immutable candidate commit.
- Attempt the minimum representative review in both directions where credentials and host APIs permit: Claude-hosted builder -> GPT-family reviewer and Codex-hosted builder -> Claude-family reviewer.
- Compare only three bounded options:
  1. a manual handoff with a signed/hashed receipt;
  2. a dedicated external-review dispatcher retained only for the cross-family role;
  3. defer seamless automation while preserving the manual release proof.
- Record requested/resolved identity/status, host, transport, source SHA, reviewer role, verdict, latency, and evidence. Do not infer family from an adapter/profile name.
- Do not redesign the five-reviewer panel or implement a universal orchestration service in the spike.

#### Recommendation table

| Result | Experiment recommendation presented at R2 |
|---|---|
| Dedicated dispatcher works safely in both required directions | Recommend retaining only that bounded review seam, with explicit fallback and receipt policy. |
| Only manual receipted handoff works | Recommend using it for release proof and deciding explicitly whether seamless cross-family review is deferred or release-blocking. |
| Only one direction works | Recommend a one-direction v1 only if Abraham accepts the visible asymmetry; otherwise block and replan. |
| Neither works or identity is untrustworthy | Recommend STOP on the automated cross-family claim; do not substitute adapter labels for execution evidence. |

Official packaging and host capabilities make these experiments worthwhile, but Abraham selects the architecture after reading their evidence.

---

## 7. Process changes

### 7.1 Immediate controls for this recovery

These are small policy/status changes applied manually in R0 before either experiment or any current orchestration skill is trusted.

1. **Durably preserve Step 4 before touching it.** Record the base SHA, exact four implementation paths, and the two untracked checkpoint/prompt paths; write `git diff --binary`, copies of the untracked supporting documents, `git status --short`, the diff stat, and SHA-256 hashes of every recovery artifact and working file to an operator-private recovery directory outside both Git working trees; then verify the tracked patch with `git apply --check` against an isolated copy of that base. The existing checkpoint remains the human explanation, not the byte backup.
2. **Require an immutable acceptance snapshot at dispatch.** Plan-backed or `/build-phase` work requires a committed canonical plan. If a GitHub issue is used, synchronize it to that plan before dispatch. A standalone `/build-step` may instead use an explicit problem + acceptance + allowed-files snapshot; a GitHub issue is not mandatory ceremony for Abraham's solo toolkit.
3. **Use three change-control lanes instead of treating every adjacent file as a crisis:**
   - **log and allow:** adjacent tests, fixtures, or documentation inside the same accepted behavior and authority boundary;
   - **quick plan amendment:** bounded same-subsystem expansion with no new durable state, dependency, destructive authority, or product-level acceptance change;
   - **stop and redline:** a new state/schema/protocol/state machine/writer/dependency/destructive authority, changed product acceptance, or breach of the step's declared materiality budget.
4. **Declare the materiality budget per step.** Include expected production files/artifacts and an effort/surface range. A default alert at roughly 20% surface growth and a hard stop at 2x the estimate may be overridden in the ratified step; the point is visible rebaseline, not estimation theater.
5. **Deduplicate test evidence.** Use focused tests while iterating. Run the authoritative full gate once on the final merged/release-candidate SHA for each declared environment/configuration and reuse that authenticated result. Any byte or relevant config change invalidates it.
6. **Make always-loaded instructions stable.** Remove volatile phase/blocker/gate prose and point to one current status/checkpoint document. Do not copy that document's changing contents back into AGENTS/CLAUDE.
7. **Give the product boundary a durable owner.** After redline approval, promote §§3 and 5 into `documentation/product-charter.md`; README and thin agent adapters point to it rather than duplicating it.

### 7.2 Build-control prerequisites before `/build-step` and `/build-phase` resume

This is one bounded control-plane repair phase, performed without the automation it is repairing. The hard prerequisites are outcomes; the smallest sound implementation may ship first.

| Hard outcome before autonomous product work | Current defect | Minimum sufficient implementation |
|---|---|---|
| Acceptance/plan conformance affects the verdict | `--acceptance` is advisory and build-phase does not pass its known plan step | Require a committed `--plan-step` or standalone immutable acceptance snapshot; a failed Done-when is a Block |
| Nits never cause an automatic developer/review cycle | One Nit makes a lens NEEDS-WORK and the documented `>=3 Nits` threshold becomes misleading | Delete the Nit blocking threshold. Nits are advisory/backlog; if a finding means failed acceptance or a failed gate, classify it as a Block |
| Uncertainty cannot advance | Prose promises `UNCERTAIN`, but aggregator/consumers omit it | Normalize unknown/`UNCERTAIN` fail-closed to `BLOCKED`/`NEEDS-WORK` first; a richer first-class `UNCERTAIN` result is optional later |
| Reviewers inspect exact immutable candidate bytes | Mutable/shared worktrees produced stale review and corruption | Require `BASE_SHA` + `CANDIDATE_SHA` and review that commit. Separate read-only archives are preferred hardening, not a prerequisite subsystem |
| Full gates are not repeated for the same evidence identity | Build-step and build-phase repeat full suites | One authoritative result per exact SHA **per declared environment/configuration**, reused by consumers; focused suites remain iterative evidence |
| Staging cannot absorb unrelated work | Broad staging can capture sibling changes | Stage only declared candidate paths plus the plan/status file actually changed |
| Scope is checked before and after implementation | Existing phone-a-friend reacts only after repeated failure | Apply the three-lane §7.1 rule at pre-dispatch and against the returned candidate diff; manual enforcement is sufficient for first recovery use |
| New plans expose constraint cost | Planning rules currently reward universality and extra gates | Land the small shared calibration/removal patch in §7.4 with golden cases before using the repaired pipeline for the product plan |

Nits remain visible. An operator may choose one cheap cleanup pass, but it triggers no mandatory developer loop or review rerun unless behavior or acceptance evidence changed.

Unknown/`UNCERTAIN` verdicts remain fail-closed and escalate to the operator. This is not a requirement to relax.

### 7.3 Scope sentinel plus phone-a-friend

The existing phone-a-friend fires only after the same defect survives two fix rounds or reviews oscillate. It would **not** have caught Step 4's first-round scope expansion.

Add two complementary mechanisms:

- **Change-control check:** compare the immutable plan/acceptance snapshot with the proposed approach before dispatch and with the actual candidate diff before review. Classify the delta into §7.1's allow, quick-amendment, or stop/redline lane. A deterministic stop/redline condition always pauses; it does not need a model's opinion. Automating this comparison is preferred after the manual rule proves useful.
- **Capacity escalation:** only when diagnosis or the smallest options are genuinely uncertain, the normal worker (for example Terra) may ask a frontier peer (for example Sol) for one read-only assessment.

The adviser returns `PROCEED | RUN SPIKE | REPLAN | STOP`, observed facts, disputed premise, smallest two or three options, recommendation, and changed files/acceptance/cost. It cannot implement, silently rewrite the plan, waive a deterministic stop, or authorize scope. Abraham or an already-ratified rule makes the decision.

### 7.4 Planning-skill guardrails

Make a small shared requirement-calibration reference and wire it into `plan-init`/`plan-feature`, `plan-review`, and `plan-redline`:

- classify each requirement as `hard | preferred | experiment | not-now`;
- retain separate `origin_type: P | D`, `introduced_by/provenance`, and `commitment` fields;
- require a stated harm for every hard constraint;
- flag universal terms such as “all,” “every,” “always,” “exact,” and “automatic” when they multiply a matrix;
- require a bounded spike for an unverified load-bearing external assumption;
- surface redundant assurance mechanisms and preferred requirements that create a new subsystem;
- propose two to four anti-goals for the operator to edit;
- ask which assumption, if false, changes the architecture or makes a subsystem unnecessary;
- elevate agent-defaulted hard constraints, architecture-changing experiments, and expensive universality in the redline Decision Inventory.

This patch **replaces**, rather than appends to, conflicting guidance: remove absolute “resolve every X/Y” language, “demand more smoke gates than feels necessary,” and automatic `code -> deep` reviewer escalation without a ratified risk classification. `plan-review` asks for the minimum representative seam. `plan-redline` accepts replies such as `D4 hard -> preferred`.

Add golden/eval cases for all four commitments, agent-defaulted hard constraints, an experiment incorrectly promoted to architecture, anti-goal proposal/editing, and a preferred requirement that would create a new subsystem.

### 7.5 Later skill redesign; bounded `skill-iterate` use

The roughly 1,000-line `build-step`, `build-phase`, and `review-deep` cores are a real maintenance and context problem, but decomposing them is not a drive-by fix. The current `skill-iterate` operates on one installed `.claude/skills/<name>/SKILL.md`, requires scorable evals, and explicitly routes radical exploration elsewhere. It cannot safely decompose canonical `skills/<name>/core.md` into multiple references and scripts.

After semantics and eval assertions are corrected:

1. run an explicit multi-file redesign (manual/skill-creator-guided, with `skill-evolve`-style alternatives where useful);
2. keep each main core as a short executable state machine with locked invariants;
3. move optional modes, examples, incident histories, and templates into progressively disclosed references;
4. move deterministic aggregation and validation into tested scripts;
5. forward-test the new package and generated host bindings;
6. only then use or adapt `skill-iterate` for constrained, scorable single-file simplification and regression-preserving hill-climb work.

Do not optimize the current skills before correcting the contracts: a good optimizer can efficiently preserve bad semantics.

---

## 8. Evidence and receipt contract

Skill Mesh should own one versioned envelope, provisionally `skill-mesh.run-receipt.v1`, with a deliberately small release core:

- schema and workflow contract versions;
- run ID and timestamps;
- skill ID/version and source commit;
- host/surface and adapter/package version;
- role;
- requested model, resolved model, and resolution status;
- provider family and execution transport;
- fallback attempts/selection/reason;
- result/verdict and evidence locators;
- duration plus token/cost values **or explicit availability status**;
- receipt completeness/errors.

Optional enrichment may add a configuration hash, permission/sandbox mode, redacted input/artifact hashes, exact-SHA gate evidence, reviewer detail, and deferrals. Optional fields do not become release blockers merely because they are useful.

Skill Mesh stores the full receipt and owns its redaction/projection code, policy, versioning, compatibility notes, and producer-owned `.observatory/` location. Dev Observatory consumes a public-safe projection of the **same receipt version**, rather than a separately maintained `skill-mesh.observatory.v1` protocol; it owns bounded loading, projection into its generic Snapshot model, freshness/compatibility errors, and rendering. Prefer an existing generic artifact `ViewSource` and `summary`/at-a-glance surface before authorizing a custom decoder or new Observatory schema; Transparency continues to show mechanical wiring only.

“One standard receipt” means one Skill Mesh evidence envelope instead of bespoke Dev Observatory plumbing in every skill. It does **not** mean every utility adopts the schema, and it does **not** eliminate deliberate functional utility calls.

---

## 9. Representative release proof

The release is accepted with representative proof rather than an exhaustive matrix.

### Case A — `plan-redline`

- Run from a disposable document fixture on Claude Code and Codex.
- Candidate pair: Fable/Sol where available.
- Verify equivalent decision inventory, proposal locator, provenance, and no unauthorized repository mutation.
- Record requested/resolved identity and package version; an unavailable resolved identity requires the named R4 waiver rather than an inferred pass.

### Case B — `build-step`

- Run on a disposable code repository with a known good change and known seeded defects.
- Require at least one real Sonnet/Terra-family cross-family direction; exercise both directions when the selected execution seam supports them.
- Require deterministic tests to remain primary.
- Confirm immutable candidate evidence, bounded correction behavior, and a visible no-value result if the second family adds nothing. The release proves the mechanism; calibration controls any claim of marginal quality.

### Case C — `session-wrap`

- Run on a disposable repository with external messaging and live-root mutation disabled.
- Verify the same wrap contract on Claude Code and Codex, receipt emission, bounded Observatory export, and explicit deferrals.

Run enough repetitions to distinguish a one-off success from a usable workflow; the final plan should set a small fixed trial count after the plugin experiment reveals host mechanics. Behavioral equivalence means matching required outcomes and safety invariants, not byte-identical prose.

---

## 10. Provisional execution phases

These phases are for redline review only. Step numbers, issues, and a build-phase goal are created after approval.

### R0 — Freeze and evidence preservation

- Create and verify the external recovery patch/hash manifest described in §7.1; record Step 4 status, focused-test evidence, and decision branches.
- Apply the rest of §7.1's manual controls and stable-status pointer before any spike.
- Make no live install and no continuation of the current state-machine implementation.

### R1 — Two architecture experiments

- Run the unique native package-lifecycle probe in §6.1.
- Run the separate cross-family execution-seam audit/spike in §6.2.
- Record evidence, recommendation, unresolved premises, and scope/cost for every viable branch.

### R2 — Operator architecture decision gate

- Present both experiment reports through `plan-redline`.
- Abraham chooses the package-lifecycle branch, the cross-family execution mechanism, and the Step 4 disposition. No experiment result self-authorizes implementation.
- Update this recovery plan's final successor before product code resumes.

### R3 — Minimum build-control-plane repair

- Implement only the hard outcomes in §7.2, the minimum §7.3 change-control wiring, and the small §7.4 planning-calibration replacement.
- Bootstrap manually with scoped candidate commits and independent review.
- Prove repaired automation against disposable fixtures before using it on product work.

### R4 — Conditional product and host implementation

- Implement only the R2-approved package branch: native packages, a bounded single-host compatibility path, or a separately re-chartered installer.
- If native lifecycle wins, compare and execute the approved one-time manual backup/cutover/retirement or bounded legacy utility; do not assume a permanent migrator/exporter.
- Audit and retarget the Copilot-specific host wrapper, transport, discovery roots, documentation, and tests to native Codex. Retire or quarantine Copilot-only release claims.
- Implement only the R2-approved cross-family review seam; do not restore a universal router by implication.

### R5 — Model policy, receipts, and representative evaluation

- Implement the minimal receipt core and public-safe projection.
- Qualify Fable/Sol and Sonnet/Terra candidates.
- Run the hard representative cross-family case and separately measure its marginal value on adversarial fixtures.
- Run the three representative proof cases.

### R6 — Dev Observatory consumer

- Add the bounded same-receipt projection and Dev Observatory consumer view.
- Keep `utility-project-standard` standalone. Document ownership in Skill Mesh for this release; add a standard manifest only after Utility Project Standard v1 stabilizes.

### R7 — Documentation, UAT, and release

- Reconcile README, architecture, migration, AGENTS/CLAUDE adapters, model config, and troubleshooting with observed behavior.
- Walk Abraham through high-level, normal, and end-to-end examples.
- Run the authoritative full gate on the final merged release-candidate SHA for every declared environment/configuration, reuse those exact results, and perform isolated rehearsal before any live cutover.

### Board track U — utility-hookup rebaseline (no dependency into R7)

- Re-redline the seven-utility hookup program against the narrowed Skill Mesh charter and repaired controls.
- Decide whether to resume, split, reduce, or retire each proposed caller seam; do not silently grandfather the existing broad core-edit plan.
- Complete the board goal on its own evidence and sequencing. Its progress is visible beside the Skill Mesh release, not a hidden release predecessor.

---

## 11. Risks and stop conditions

| Risk | Control / stop condition |
|---|---|
| Native plugin capability differs from documentation or Windows behavior | Disposable live experiment; PARTIAL/FAIL branch, no assumption |
| The control-plane repair expands into another framework rewrite | Fixed list in §7.2; decomposition deferred; scope sentinel enforced manually |
| Package lifecycle is mistaken for model orchestration | Separate §6.2 execution-seam experiment and R2 operator choice |
| Copilot-specific behavior is mislabeled as Codex support | R1 audit plus explicit R4 retarget/retirement and native Codex proof |
| Qualified model aliases drift | Record requested/resolved; requalify on material resolution change |
| Cross-family review adds cost without marginal detection | Report the result honestly; retain the hard release mechanism proof and tune preferred ongoing use rather than inventing a quality claim |
| The receipt becomes another broad protocol | Ship the minimal core first; optional enrichment stays non-blocking; Observatory consumes a projection of the same version |
| Receipts leak prompts, paths, or secrets | Versioned redaction policy, bounded projection, fixture leak tests |
| Dev Observatory becomes required runtime infrastructure | Producer-first raw receipt; consumer failure is visible but cannot block skill execution unless a future explicit safety policy says so |
| Frozen Step 4 bytes are lost or become stale | R0 external binary patch + hashes + isolated apply-check before any experiment; do not merge until R2 determines relevance |

Stop and re-redline if a phase introduces a new durable protocol, runtime dependency, target host, provider family, always-on process, or destructive authority not listed here.

---

## 12. Decision Inventory

### Operator choices already incorporated

| ID | Origin type | Introduced by | Commitment | Choice | Status |
|---|---|---|---|---|---|
| P1 | P | Abraham | hard | Freeze Step 4 before resuming | incorporated; durable preservation still required in R0 |
| P2 | P | Abraham | hard | Representative end-to-end proof can satisfy the release | incorporated |
| P3 | P | Abraham | hard | Normal target experience is Claude Code and Codex, not Copilot | incorporated |
| P4 | P | Abraham | experiment | Candidate peers include Fable/Sol and Sonnet/Terra; final selection follows evidence | incorporated |
| P5 | P | Abraham | hard | Run the package architecture experiment before resuming the build | incorporated |
| P6 | P | Abraham | not-now | Do not adopt Omnigent now; preserve `documentation/omnigent-revisit-seed.md` | incorporated and seed written |
| P7 | P | Abraham | preferred | Use `plan-redline`, `build-step`, and `session-wrap` as representative proof cases | incorporated with disposable-fixture safety note |
| P8 | P | Abraham | preferred | Keep Dev Observatory as the management/view layer if ownership remains clear | incorporated |
| P9 | P | Abraham | preferred | Quality over timeline | incorporated; scope rebaseline still applies |
| P10 | P | Abraham | hard | Adopt the narrow Skill Mesh charter and proposed anti-goals | incorporated |
| P11 | P | Abraham | hard | Run and report at least one real cross-family release case | incorporated |
| P12 | P | Abraham | preferred | Continue cross-family review at selected high-risk seams, without promising exceptional truth | incorporated |
| P13 | P | Abraham + review | experiment | Measure, rather than assume, cross-family marginal quality | incorporated |

### Decisions requiring Abraham's redline approval

| ID | Origin type | Introduced by | Commitment | Proposed choice | Status |
|---|---|---|---|---|---|
| D1 | D | review | hard | Both experiments produce recommendations and halt at R2; Abraham, not the spike, selects every architecture branch | approved 2026-08-13 |
| D2 | D | review | experiment | Use a unique two-skill/shared-asset lifecycle probe rather than ordinary `plan-redline`, preventing discovery shadowing while testing real package structure | approved 2026-08-13 |
| D3 | D | review | experiment | Separately compare manual receipted handoff, a bounded external-review dispatcher, and deferred seamless automation for the cross-family seam | approved 2026-08-13 |
| D4 | D | review | hard | Before autonomous product work: acceptance affects verdict; Nits never block; uncertainty cannot advance; exact immutable bytes are reviewed; staging is scoped; duplicate full gates are eliminated | approved 2026-08-13 |
| D5 | D | review | hard | Apply the three-lane change-control rule manually at pre-dispatch and after candidate diff; only new authority/product change/material breach requires redline | approved 2026-08-13 |
| D6 | D | review | preferred | Automate the scope sentinel after the manual rule proves useful | approved 2026-08-13 |
| D7 | D | Abraham + review | preferred | Permit a Terra->Sol-style read-only capacity escalation only for uncertain diagnosis/options; it has no authority | approved 2026-08-13 |
| D8 | D | review | hard | A release lane with unavailable actual resolved identity needs an explicit Abraham waiver; all-unavailable evidence cannot silently pass | approved 2026-08-13 |
| D9 | D | Abraham + review | preferred | Use qualified aliases for routine work; use exact pins for release/eval/high-risk where supported, always recording request/resolution status | approved 2026-08-13 |
| D10 | D | review | hard | Skill Mesh owns one minimal receipt plus its redacted same-version projection; Dev Observatory owns bounded load/Snapshot/rendering; `utility-project-standard` remains standalone | approved 2026-08-13 |
| D11 | D | review | preferred | Keep utility hookups as independent board track U; re-redline before resuming, splitting, reducing, or retiring each seam | approved 2026-08-13 |
| D12 | D | review | not-now | Defer multi-file core decomposition; redesign explicitly later, then use/adapt `skill-iterate` only for constrained scorable single-file optimization | approved 2026-08-13 |
| D13 | D | review | hard | Define the Codex package surface as Codex CLI/ChatGPT desktop; the current IDE extension is not a plugin target unless Abraham adds a compatibility requirement | approved 2026-08-13 |
| D14 | D | review | hard | Land the small planning-calibration replacement and goldens before using the repaired pipeline for product work; full planning-skill decomposition remains later | approved 2026-08-13 |
| D15 | D | review | experiment | If native lifecycle wins, compare a one-time manual backup/cutover/retirement with a bounded legacy utility; do not presume a permanent migration/export subsystem | approved 2026-08-13 |

### Later communication-profile decision

| ID | Origin type | Introduced by | Commitment | Proposed choice | Status |
|---|---|---|---|---|---|
| D16 | P | Abraham + review | experiment | Pilot a small STE-inspired plain operational English profile. Do not claim ASD-STE100 compliance. Preserve exact technical strings, use sentence lengths only as soft signals, and decide adoption from comprehension UAT before release. | recommended; decide during Phase 7 UAT |

Abraham approved D1-D15 as written on 2026-08-13. D16 is a later, non-blocking pilot decision and does not reopen those approvals.

Approval authorizes creation of the final canonical plan, goal, and build phases. It does not by itself authorize a live install, implementation, or disposal of the frozen Step 4 WIP; R0 preservation comes first.

---

## 13. Research sources

- ASD, [ASD-STE100 Simplified Technical English, Issue 9](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf) and [official FAQ](https://www.asd-ste100.org/STE_faq.html) — source for the proposed non-compliant plain-language profile and its comprehension goal.
- OpenAI, [Package your plugin](https://developers.openai.com/plugins/build/plugins) — current Codex/ChatGPT plugin package and marketplace shape.
- OpenAI, [Plugins](https://learn.chatgpt.com/docs/plugins) — supported Codex surfaces, CLI browser/install/uninstall, and the current IDE-extension exclusion.
- Anthropic, [Create plugins](https://code.claude.com/docs/en/plugins) and [Discover and install plugins](https://code.claude.com/docs/en/discover-plugins) — current Claude Code plugin packaging and lifecycle.
- Omnigent, [FAQ](https://omnigent.ai/faq), [Harnesses](https://omnigent.ai/docs/build/harnesses), and [Polly](https://omnigent.ai/docs/use/builtin-agents/polly) — current alpha status, harness abstraction, and cross-vendor orchestration claims.
- Omnigent, [GitHub README](https://github.com/omnigent-ai/omnigent) — current Windows limitations and installation surface.

External claims must be rechecked when the final experiment runs; these products are changing quickly.
