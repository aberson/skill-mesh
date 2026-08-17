# Goal NP Publication 8 — Terra bootstrap Windows sandbox-enforcement recovery amendment

**Status:** AWAITING RECOVERY APPROVAL 1
**Canonical executable plan:** `documentation/native-claude-codex-skill-parity-plan.md` in the same
Publication-8 commit
**Historical Publication-2 base:** `documentation/native-claude-codex-skill-parity-plan.md` at commit
`9c224efda851a3501f130830f5cd22b212fc36f0`
**Historical Publication-2 base-plan SHA-256:**
`3c8b3e84b2e192ce1d53cd7488afc8a051a614ee6316df59dad5985af5b73b4d`
**Requested change:** preserve Publication 7's Codex `gpt-5.6-terra`/`xhigh` orchestration, repaired
Windows PowerShell 5.1 process recorder, exact five-line workspace-write permission grammar, stable
model-result classification, and external fail-stop boundary, and correct only pinned Codex 0.147.0's
Windows sandbox-enforcement downgrade exposed by its approved, non-consuming preclaim failure.

This document is a narrow controlling amendment. It does not authorize implementation by itself.
Publication 8 is the exact commit containing, in the launcher's required order, `plan.md`,
`documentation/native-claude-codex-skill-parity-plan.md`,
`documentation/native-claude-codex-skill-parity-terra-amendment.md`,
`documentation/native-claude-codex-skill-parity-proposal.html`, the precommitted post-Approval launcher
`tools/run-goal-np-terra-bootstrap.ps1`, its unchanged
`schemas/terra-bootstrap-result-v1.schema.json`,
`experiments/recovery/cross-family-fixture/create_fixture.py`,
`experiments/recovery/cross-family-fixture/probe.py`,
`tests/experiments/test_cross_family_probe.py`, and
`tests/distributions/test_path_choke_point.py`. Publications 3, 4, and 5 each consumed their Approval-1
sentence in a terminal request. Publications 6 and 7 each received Approval 1, but their respective
`Preflight` stopped before claim and created no durable request lineage. None of those sentences or any
earlier approval can authorize these bytes, retry a terminal request, or run either superseded launcher.

## 1. What this amendment changes

Publication 8 carries forward Publication 6's supersession of these Publication-2 surfaces:

1. the Claude Code/`opus` `ADMIN-BOOTSTRAP` executor and its 76-row installed-Claude closure;
2. the Claude-native `/repo-sync` model call in `ADMIN-SYNC`;
3. the Claude `/build-step` execution envelope used by NP-01..NP-11 and NP-13..NP-39/NP-41;
4. the corresponding executor, requested/reported-identity, call-count, evidence, receipt, schema,
   controller-canary, and Quickstart fields; and
5. only the implementation-orchestration meaning of `/build-step` in those surfaces.

They are replaced by the direct Codex/Terra contracts below. When one of those named surfaces
conflicts with the base plan, this amendment controls. All other base-plan text remains controlling.

Publication 8 also replaces—not supplements—every legacy publication-gate attestation field or
description on the Approval-1 request, Approval-1 receipt, ADMIN-SYNC aggregate, and the
`/repo-sync --force` precondition. The one valid ordered tuple is plan-review `PASS`, then plan-redline `PASS`, then
plan-wrap `READY`. It binds each gate record's SHA-256 and identical start/end SHA-256 map for the exact
ten-file bundle. Any legacy tuple that orders plan-wrap before plan-redline, requires all three
verdicts to be `PASS`, omits the record/bundle hashes, or coexists as a second field is invalid. This is
a replacement of the old attestation meaning; implementations must not retain an ambiguous legacy
field beside it.

Publication 8 retains every Publication-7 executor boundary and preserves Publication 7's complete,
closed permission grammar without alteration. It supersedes only this Windows enforcement defect:

1. in pinned Codex 0.147.0, absent `[windows].sandbox` configuration resolves to
   `WindowsSandboxLevel::Disabled`; Windows configuration normalization then converts an explicitly
   requested `SandboxMode::WorkspaceWrite` to `SandboxMode::ReadOnly`;
2. the one narrow shared closed-config correction is exactly `windows.sandbox="unelevated"` for both
   `codex debug prompt-input` and `codex exec`; `unelevated` selects
   `WindowsSandboxLevel::RestrictedToken`, so the `Disabled` downgrade branch does not fire; and
3. that setting only prevents the mode downgrade. It does not loosen or replace the strict
   workspace-write permission grammar, use `default_permissions=:workspace`, accept read-only output,
   or make requested flags sufficient evidence.

The complete normalized workspace-write permission text remains exactly these five lines, with the
canonical owner root substituted only in line 4:

```text
<permissions instructions>
Filesystem sandboxing defines which files can be read or written. `sandbox_mode` is `workspace-write`: The sandbox permits reading files, and editing files in `cwd` and `writable_roots`. Editing files in other directories requires approval. Network access is restricted.
Approval policy is currently never. Do not provide the `sandbox_permissions` for any reason, commands will be rejected.
 The writable root is `<canonical-owner-root>`.
</permissions instructions>
```

The initial character of line 4 is one ASCII space; the backticks, path spelling, period, line order,
and five-line count are significant. The existing accepted, missing-annotation, wrong-root, whole-text
equality, and hash-only mismatch-diagnostic canaries remain mandatory.

The Windows sandbox-enforcement repair changes no model task, result schema, call count, capability envelope, process recorder,
declared sandbox, primary workspace, or equality policy. Publication-8 authority and recovery-evidence
references necessarily replace their Publication-7 counterparts. It grants no additional model or
production process. The retained process canary and pinned non-model `codex debug prompt-input`
diagnostic keep their exact call counts and scratch boundary.

The ten-file publication also repairs two deterministic gate families that were red at clean
Publication-7 HEAD before any Publication-8 request claim. The fixture builder normalizes CRLF and lone
CR to LF at both the cross-family candidate copy/hash boundary and the declared-inventory hash boundary,
making those identities independent of checkout line endings. A later restarted plan-redline review
found that the same unqualified `defect_inventory_sha256` nevertheless still named LF-normalized
builder bytes, SHA-256
`98baaa178e41dc23e5de70e3161de78c66b9c91052c4d0d99295ae1a8928ed37`, and raw CRLF sealed-probe
artifact bytes, SHA-256
`24c336217fba1a6d1d177b754a34be77275e0c797a50d48ea0a7e5d9401c2752`. Publication 8 therefore
LF-canonicalizes the inventory at `probe.py`'s source/sealing boundary, fail-closed checks the fixture
identity against that canonical source and the sealed fixture against its receipt, and tests LF, CRLF,
lone-CR, and identity-drift cases in `test_cross_family_probe.py`. The path-choke test adds one exact
whole-file exemption for the one-off, fixed-boundary Publication-8 launcher: it has no consumer-home
parameter; its sole caller-supplied path is equality-checked against the canonical approval path and is
never a mutation target; and repository, ADMIN, Evidence, and Staging mutations remain confined to
exact launcher-derived boundaries. The written exemption must be removed if that boundary broadens.
None of these corrections narrows collection, skips or xfails a test, supplies a path argument, or
weakens the unchanged repository-root `python -m pytest` DONE gate or the launcher's mandatory
full-root pytest gate.
Abraham explicitly authorized this bounded baseline-gate repair and Publication-8 revision. That
revision authority is not Recovery Approval 1 and authorizes no `Preflight`, `Run`, model call,
implementation, or live mutation.

In particular, this amendment does **not** change:

- P01–P10, D01–D10, the 41-step DAG, Files boundaries, owner partitions, tests, candidate-registry
  rules, recovery contracts, or Approval 2;
- D08's 14 controlled maintenance/evaluation roles;
- `claude-native-session-v1 = opus/xhigh` or `codex-native-session-v1 = gpt-5.6-sol/ultra` in the
  NP-12 and NP-40 native-host qualification cells;
- either phone-a-friend contract exercised by the product's native `/build-step`; or
- routine maintenance's selected host-skill command.

Terra is therefore the Goal-NP implementation orchestrator, not a relabeling of the Codex native
qualification session and not a cross-vendor equivalence claim.

## 2. Publication-8 authority and recovery boundary

The only valid recovery Approval-1 sentence is:

```text
Approve Goal NP plan Publication 8 with D01-D10 and the Terra Windows sandbox-enforcement recovery amendment.
```

Its UTF-8 text SHA-256 is `c54648e8eedfebb9181ea04043cca948692a78e35bd3f42b7cca92352be74c79`.
The canonical 110-byte UTF-8-without-BOM file with exactly one final LF has SHA-256
`2c9b4f34f0c53a634725f608b724558cf920a9e0d606b4a09707d7e15744ce7e`.

Approval is valid only when its receipt binds the final Publication-8 commit and SHA-256 of all ten
bundle files. It authorizes the amended administrative prelude, NP-01 through NP-41, disposable
tests/hosts/evidence, and the base plan's non-live candidate work. It does not authorize a live Claude
or Codex discovery-home write, live State mutation, Approval-2 receipt, cutover, activation, or live
rollback. The terminal implementation state remains `WAITING FOR APPROVAL 2`.

Other than the two exact retained pre-claim `cmd.exe` canary children and the closed non-model
prompt-input diagnostics in Sections 3.2 and 3.4, any different model, effort, executable,
configuration, prompt, retry, child call, tool capability, or ambient project/user skill, plugin, or MCP
dependency is `INVALID`; it is never a fallback.
Codex's bundled skill instructions and locators must be absent under the Section 3.2 disable-and-proof
contract; no skill tree is authorized.

### 2.1 Frozen Publication-3 terminal evidence

Publication 3 was committed at `71a5aea3fd21320d2fbb3cb9228bc52e42cb3215` and received its exact
Approval-1 sentence. Its single create-new bootstrap request is
`tba-b7e5898e6389ff19b3ce34738f16b47d0a832dfc4625789fbcf4308352f2b1a0`. The request stopped while
hashing the active live Codex home because `%USERPROFILE%\.codex\goals_1.sqlite` was locked by the
coordinator session. The failure happened before an implementation prompt, Codex/Terra process,
deterministic test, Git mutation, or product mutation.

The immutable Publication-3 state is `blocked` with SHA-256
`ae59a6ac7f512d2e399675fe541b916d1710c209a13b45433642cf019a07df97`. Its evidence root contains only
that 601-byte `state.json` and an empty `instruction-free-launch-roots` directory; the canonical
three-entry whole-root manifest SHA-256 is
`9b01de1f550019a8bf81c23431925b6f38a173ec1ce22023c765a2a8d290cdcf`. Publication 8 treats that root as
read-only recovery input at
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\TerraBootstrap\tba-b7e5898e6389ff19b3ce34738f16b47d0a832dfc4625789fbcf4308352f2b1a0`.
Its canonical Approval-1 file SHA-256 is
`33d3e1756ed2bfd661698da3dfdf85a921380efd87fe3d635b777dafe3c6e04b`; the normalized approval-text
SHA-256 is `66df8cd413fddd097e80dc63ccfacab221e96c72c795345d14b72ae1ae3474ef`.
It may not be retried, deleted, changed, renamed, adopted as a new request, or used as authority for a
model call. An initial mismatch is `PRIOR_PUBLICATION3_EVIDENCE_MISMATCH` and stops before a
Publication-8 evidence root exists; the same mismatch on a recheck after claim seals durable terminal
`blocked` evidence in the existing P8 root.

### 2.2 Frozen Publication-4 terminal evidence

Publication 4 was committed at `58223098887468953570ecf153494871c5404605` and received its exact
Approval-1 sentence. The canonical approval file SHA-256 is
`2f74ea66ac7bdac38b419fd24b7e6caa9479de007bc178e69acd54f9f8b42857`; the normalized approval-text
SHA-256 is `1a7698085d7bc12e74d60874e0d64b4d069b039470ab17701541cfe6c77202fe`. Its single create-new request is
`tba-461c20be4d35c7255a83d05f91f16c5bccbdd5a36af738360bcedc330ab6b1e4` at
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\TerraBootstrap\tba-461c20be4d35c7255a83d05f91f16c5bccbdd5a36af738360bcedc330ab6b1e4`.

That request reached `implementation-prompt-input`: stdout is valid prompt-input JSON with SHA-256
`31757cf1c4ac11f2eb6f63880e92b3a036f82e0f185866edf9ae98619c5e7681`, and stderr is the empty file
with SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
Windows PowerShell 5.1 then exposed an empty `Process.ExitCode`, so the recorder terminally stored the
exact error `implementation-prompt-input exited .` before any `codex exec`, Terra/model process,
model result, deterministic test, ADMIN diff, commit, or product mutation. The live Codex home and
frozen Publication-3 evidence remained unchanged.

The immutable Publication-4 state is `blocked` with SHA-256
`4517ecd2d5ff948bbcf7763e32686797f65b5112ceb14e71c96c8222e6e12e05`. The canonical whole-root manifest
has exactly nine entries and SHA-256
`893c099e299a5152f26edd912a5bfcdc75bd69e030dfd40653c0365ffe4d5e44`. Publication 8 treats every byte
under that root as read-only recovery input. It may not be retried, deleted, changed, renamed, repaired,
adopted, or used as authority for a model call. An initial mismatch reports
`PRIOR_PUBLICATION4_EVIDENCE_MISMATCH` and stops before a Publication-8 evidence root exists; the same
mismatch on a recheck after claim seals durable terminal `blocked` evidence in the existing P8 root.

### 2.3 Frozen Publication-5 terminal evidence

Publication 5 was committed at `6d292bb37c37944c71ed8b18214fabb23f22869e` and received its exact
Approval-1 sentence. The canonical approval file SHA-256 is
`5ad7472cb113d6965de18204dc1b7f860a0c2982ad1e8152e34547efa714a8e3`; the normalized approval-text
SHA-256 is `2d19ad716f3179baf67c67c77d19dfb29697ea5b2e6f2b0a0d1fe87ee03d0f47`. Its single create-new request is
`tba-03e474757a5e0c92e8d3f0bd4c5a0731a742397a43c99d5e027016643fced916` at
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\TerraBootstrap\tba-03e474757a5e0c92e8d3f0bd4c5a0731a742397a43c99d5e027016643fced916`.

That request passed the repaired process canary and completed one actual `codex exec` implementation
process requesting model `gpt-5.6-terra`, effort `xhigh`, and sandbox `workspace-write`.
`implementation.invocation.json` has SHA-256
`3752f8ea94fd57bb72d3d495d2ba88e8a6068d80552dc9ef9f0292714887ff36`; the exact argv records an
instruction-free evidence directory as `--cd` and the approved repository as `--add-dir`. The retained
prompt-input proof was generated separately with a hard-coded `read-only` sandbox and has SHA-256
`a50ad81bae6f73f5d85c369f5ebce0904a903a23ce90c6dced83a890d5b7ea8b`. It therefore cannot attest the
implementation call's effective sandbox. This record proves the requested sandbox and Terra's
subsequent response; it does not by itself prove that Codex downgraded the actual process.

The requested-Terra process returned the schema-valid model result `BLOCKED`, summary “Implementation cannot proceed: this
session grants read-only filesystem access and rejects writes,” with one blocker naming the repository.
`implementation.result.json` has SHA-256
`2e56256153e3c50de8c981a1d13e53e1e18fb495276f3c34517a1ef8895c295c`. The launcher then stored the
known result as `error_code=UNEXPECTED_FAILURE`, `error_label=launcher`, exact error
`implementation returned BLOCKED.` The model never attempted a filesystem write: all 11 recorded
command-execution starts were inspections/reads, with one bundled read declined. The record therefore
shows a model refusal, not an observed operating-system write denial. The immutable Publication-5
state is `blocked` with SHA-256
`b0e9355ff3f39c1ccca196ae45ebe7c4f042c9fcd2587d84882c7d9af4724f50`. Its canonical whole-root
manifest has exactly 17 entries and SHA-256
`11f84ea3e5140a2832586f63fc362c97b92286b1663c91df2c80fb7784d6f700`.

The approved repository remained clean at `6d292bb37c37944c71ed8b18214fabb23f22869e`, all 15 ADMIN outputs
remained absent, the request-owned disposable Codex home was removed, and the live Codex home plus both
earlier roots remained unchanged. No deterministic test, ADMIN diff, commit, issue mutation, or product
mutation occurred. Publication 8 treats every P5 byte as read-only recovery input. The request/root may
not be retried, deleted, changed, renamed, repaired, adopted, or used as authority for another model call.
An initial mismatch reports `PRIOR_PUBLICATION5_EVIDENCE_MISMATCH` and stops before a Publication-8
evidence root exists; the same mismatch on a recheck after claim seals durable terminal `blocked`
evidence in the existing P8 root.

### 2.4 Frozen Publication-6 approved preclaim record

Publication 6 was committed at `d0f83210e3092e18a28ee24db20a1af95887c31b` and received its exact
Approval-1 sentence. Its canonical approval file is
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication6\approval1-message.txt`; the file SHA-256 is
`064e50a53d93dc976cb98b87a5a49d0260d91f88aadddb23bcd8bf60d9be2add`, and the normalized
approval-text SHA-256 is `ad20542c0d5dc9b77fbab14413998f614ab178ca4949a1269f06c08f24b3407e`.
Its frozen external handoff is
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication6\terra-transition-handoff-d0f83210e3092e18a28ee24db20a1af95887c31b.txt`
with length 18,494 bytes and SHA-256
`ae085575b9441080ece62194cd4a3144df809eaa9d70b2ed2fcd76624d455b47`.

The derived Publication-6 request identity was
`tba-cc76394efc1359d75b406ce5a2d2300d5ed41020b5cf7fc972ba3039dc3a6ab0`, but `Run` was never started
and its TerraBootstrap evidence root was never created. The launcher reproduces that ID from the
original 12-field preimage: `publication-6-sandbox-attestation-recovery-v1`, Publication-6 commit and
approval-text hash, then the P5, P4, and P3 request/state/root-manifest triples. The operator-reported
terminal JSON from the
standalone, repeatable, non-consuming `Preflight` had `verdict=BLOCKED`,
`error_code=PERMISSION_ATTESTATION_FAILED`, `error_label=preclaim-permission-attestation`, full error
`[PERMISSION_ATTESTATION_FAILED] [preclaim-permission-attestation] Permissions text differs from the complete closed permission grammar.`, and
`evidence_root_absent=true`. That operator report retained no expected or actual permission hashes,
line counts, or permission text, and the staging scratch was removed by design. The earlier claim that
P6 proved only a missing writable-root line was therefore an unsupported inference and is withdrawn.
P7's later evidence does not retroactively establish P6's exact actual text; P7 was the first
publication to prove that the diagnostic exposed the complete canonical four-line `read-only` grammar.

No `codex exec`, Terra/model call, request claim, state, test, ADMIN diff, commit, issue, product, or
repository mutation occurred. The repository remained clean at the approved commit, all 15 ADMIN paths
remained absent, and the permission scratch was removed. This record is not a terminal claimed
lineage, and Publication 8 invents no Publication-6 failure receipt, state, or evidence manifest. The
preflight scratch output was removed by design. Publication 8 verifies only the
exact canonical approval bytes and hashes and handoff hash; that its approved commit descends from the
Publication-6 approved commit; absence of the Publication-6 TerraBootstrap request root; and absence of the complete
`%LOCALAPPDATA%\SkillMesh\Staging\GoalNP\Publication6` staging publication root and its exact
`tba-cc76394efc1359d75b406ce5a2d2300d5ed41020b5cf7fc972ba3039dc3a6ab0` child. An initial mismatch is
`PRIOR_PUBLICATION6_PRECLAIM_MISMATCH` and stops before a Publication-8 evidence root exists; the same
mismatch on a recheck after claim seals durable terminal `blocked` evidence in the existing P8 root.
The Publication-6 launcher must not be modified in place or rerun; its approval remains bound to those
superseded bytes and cannot authorize Publication 8.

### 2.5 Frozen Publication-7 approved preclaim record

Publication 7 was committed at `40d671d75e1aa6c6b31eab70caa8f4d07ed51383` and received the exact
sentence `Approve Goal NP plan Publication 7 with D01-D10 and the Terra writable-root grammar recovery amendment.`
Its canonical approval file is
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication7\approval1-message.txt`; its normalized approval-text
SHA-256 is `fe5736f56b0edb305ef2e1632d5882a6d85d930c06862d9ec9ce26a28b9a23aa`, and its
104-byte LF-terminated file SHA-256 is
`a849c6f49c9557ee7e11bdc4c01f324e17fe260d5abdc648141715d22120f8a5`. Its frozen external handoff is
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication7\terra-transition-handoff-40d671d75e1aa6c6b31eab70caa8f4d07ed51383.txt`
with length 21,345 bytes and SHA-256
`c0554be563284c8fe9eb2f4aa2985505c76d39eb17dd1aeb1313dd78f3b43f81`.

The derived Publication-7 request identity was
`tba-f3b13b6337e230003d8721ad759b398d31536eae9d9b2bdf0860ff8b1d849568`. Its standalone,
repeatable, non-consuming `Preflight` returned `verdict=BLOCKED`,
`error_code=PERMISSION_ATTESTATION_FAILED`, `error_label=preclaim-permission-attestation`, full error
`[PERMISSION_ATTESTATION_FAILED] [preclaim-permission-attestation] Permissions text differs from the complete closed permission grammar.`,
and `evidence_root_absent=true`. The deterministic mismatch diagnostics were:

- expected whole-text SHA-256
  `aa613097ace0f175545df760139a7bbc9c505a0feb207dbc2552438ce70db03d`, five lines;
- actual whole-text SHA-256
  `29dad5ed6993c5e717376e0a1c84d54ab60ee593510916ac6cee4295e803315d`, four lines;
- first differing line number 2, with both expected and actual lines present;
- expected line-2 SHA-256
  `06c4b2fd6aab85ab9ea0e5598cbcdead5142d7cb56e851770163c1b9f480338b`; and
- actual line-2 SHA-256
  `d9cebe887c2ee11798faa526216e1d4af5d90cd47231862b50eb60cc5ac76464`.

Those hashes reconstruct the exact five-line `workspace-write` grammar expected by Publication 7 and
the exact four-line `read-only` grammar actually reported by the pinned diagnostic; they are not a basis
for accepting read-only output. `Run` was never started. No `codex exec`, Terra/model call, request
claim, durable state, receipt, evidence manifest, test, ADMIN diff, commit, issue, product, or repository
mutation occurred. The durable TerraBootstrap request root and its `state.json` remained absent.
Preflight transiently created only its request-owned Publication-7 staging scratch, then fully removed
it; both the exact staging request root and complete
`%LOCALAPPDATA%\SkillMesh\Staging\GoalNP\Publication7` publication root are absent.

Publication 8 verifies the exact Publication-7 commit ancestry, canonical approval bytes and hashes,
handoff length and hash, reproducible request identity, absence of the durable evidence/state root, and
absence of both transient staging roots. It carries the exact operator-reported failure metadata above
as historical context; it does not invent or re-read a durable Publication-7 receipt, state, or manifest.
An initial mismatch is
`PRIOR_PUBLICATION7_PRECLAIM_MISMATCH` and stops before a Publication-8 evidence root exists; the same
mismatch on a recheck after claim seals durable terminal `blocked` evidence in the existing P8 root.
The Publication-7 launcher, approval, and handoff are immutable retired preclaim inputs: never edit,
delete, rename, replace, or rerun them, and never reuse their approval as Publication-8 authority.

### 2.6 Pre-publication disposable A/B diagnostic context

An authorized disposable A/B run of the non-model `codex debug prompt-input` diagnostic on pinned
`codex-cli 0.147.0`, native executable SHA-256
`935a1911ed2556e4ffcec995f4886ac2ac425863ba26fed264df62e30272ad9d`, isolated the Windows setting:

- baseline, with no `windows.sandbox` override: exit 0, empty stderr, effective
  `sandbox_mode=read-only`, managed permission profile, restricted network, `write_path_count=0`, exact
  four-line permission SHA-256
  `29dad5ed6993c5e717376e0a1c84d54ab60ee593510916ac6cee4295e803315d`, and line-2 SHA-256
  `d9cebe887c2ee11798faa526216e1d4af5d90cd47231862b50eb60cc5ac76464`; and
- candidate, with exactly one shared override `windows.sandbox="unelevated"`: exit 0, empty stderr,
  effective `sandbox_mode=workspace-write`, managed permission profile, restricted network,
  `write_path_count=1`, exact five-line permission SHA-256
  `aa613097ace0f175545df760139a7bbc9c505a0feb207dbc2552438ce70db03d`, and line-2 SHA-256
  `06c4b2fd6aab85ab9ea0e5598cbcdead5142d7cb56e851770163c1b9f480338b`.

Neither arm issued a model request or `codex exec`. The disposable scratch and diagnostic script were
removed; the repository, live authentication bytes, and set of Terra evidence roots remained unchanged;
both Publication-7 and Publication-8 staging roots were absent after cleanup. This A/B result is
pre-publication diagnostic context only. It is not a Terra request, lineage, digest field, receipt,
approval, model call, or substitute for Publication-8 `Preflight` and its independent repeated proof.

Publication 8 is a replacement publication under the existing Approval-1 gate, not a third approval
gate. Its new sentence, commit, recovery-domain request ID, and evidence root create a distinct lineage.

## 3. Exact Terra execution envelope

### 3.1 Frozen host identity

Publication 8 requires:

- Codex CLI version exactly `codex-cli 0.147.0`;
- native executable resolved below `%APPDATA%` at
  `npm\node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc\bin\codex.exe`;
- executable SHA-256 exactly
  `935a1911ed2556e4ffcec995f4886ac2ac425863ba26fed264df62e30272ad9d`;
- model exactly `gpt-5.6-terra` and reasoning effort exactly `xhigh`; and
- Windows PowerShell 5.1 as the deterministic outer recorder/controller shell.

Before every model process, the outer recorder resolves the executable, version, file hash, worktree
root, Git common directory, ref, HEAD, tree, index, and status. A mismatch stops before the call.
Codex 0.147.0 does not expose a provider-reported model/effort field in ephemeral JSONL. The record
therefore distinguishes `requested_identity` (the exact rehashed argv/config) from
`reported_identity_status=unavailable`; it must never promote the latter to an observed claim. A
future nonempty reported identity must match the request or the attempt is `INVALID`.

### 3.2 Closed invocation

Every Goal-NP implementation or review process uses the same base argument vector. The exact owner
worktree is the primary `--cd` workspace; the administrative launcher uses the approved Skill Mesh
repository for both calls, and the numbered-step controller uses that partition's exact owner worktree.
The repository is not also supplied through `--add-dir`. Project instruction and skill discovery remain
closed by `project_doc_max_bytes=0`, an empty fallback list, disabled agents/dynamic skills,
`skills.bundled.enabled=false`, `skills.include_instructions=false`, ignored rules/user config, and the
mandatory matching prompt-input attestation. Request-owned evidence and review packets
remain outside the owner and are named by absolute hash-bound paths. Only `<sandbox>`,
`<owner-worktree>`, `<result-schema>`, `<last-message-file>`, and the schema-valid prompt change by request.

The pinned OpenAI Codex v0.147.0 schema defines the bundled-skill
[`enabled`](https://github.com/openai/codex/blob/rust-v0.147.0/codex-rs/core/config.schema.json#L354-L362)
switch and defines
[`include_instructions`](https://github.com/openai/codex/blob/rust-v0.147.0/codex-rs/core/config.schema.json#L3065-L3082)
as the automatic skills-instruction-block toggle. The launcher nevertheless relies on its exact
model-visible no-block/no-locator proof, not config names alone.

For the ADMIN implementation and review, every Codex/model/CLI string and behavior named by the closed
bundle is a frozen approved input and an opaque literal. Both tasks are generic local code/review work:
the model is not asked to discover or validate current OpenAI/Codex documentation, settings, setup,
troubleshooting, prompting, model choice, API, or SDK facts. Mere occurrence of those names is
incidental and does not expand the prompt or grant research authority. Skill instructions are disabled
for both debug and exec; no skills block or locator may be model-visible, and no `SKILL.md`, referenced
resource, tool, app, or network receives direct or transitive authority. Both prompts state that no skill
is available or required. If the model nevertheless judges one required, it returns schema-valid
`BLOCKED` before any implementation mutation; it must not load a skill, enable network, invoke another
capability, or substitute remembered current-product claims.

Immediately before and after each ADMIN `codex exec`, the launcher takes complete ordinal manifests of
the retained scratch and requires the disposable `codex-home\skills\.system` path to be absent. After a
zero-exit process, it strictly parses every JSONL line as one nonempty JSON event object and rejects any
normalized `.system/.../SKILL.md` reference in executable request fields or any nested native skill
event/type field; model/output text is not an executable-request surface. A timeout, start/handle error,
or nonzero exit terminates under its process failure code after the post-process scratch check and before
any transcript is accepted. Absence before, model-visible absence, scratch absence after, and, on a
zero exit, transcript absence are separate gates; a detected post-claim transcript violation is
`MODEL_VERDICT_INVALID` and terminal.

`Get-ClosedConfigArguments` emits the nine `--config` pairs and then the fifteen `--disable` pairs in
exactly the order below. The preclaim debug consumer, per-call debug consumer, `codex exec` consumer,
and recorded base-argv template all insert that same sequence immediately after their model argument and
before `--sandbox`/`--cd`. Debug then appends `debug prompt-input <diagnostic>`; exec and its template
append the execution-only closure shown below. Only the four path/sandbox placeholders and the prompt
or diagnostic literal may vary where this amendment explicitly permits them.

```powershell
& $CodexExe exec `
  --model gpt-5.6-terra `
  --config model_reasoning_effort=xhigh `
  --config approval_policy=never `
  --config 'windows.sandbox="unelevated"' `
  --config 'project_doc_max_bytes=0' `
  --config 'project_doc_fallback_filenames=[]' `
  --config 'agents.enabled=false' `
  --config 'skills.bundled.enabled=false' `
  --config 'skills.include_instructions=false' `
  --config web_search=disabled `
  --disable apps `
  --disable plugins `
  --disable hooks `
  --disable skill_search `
  --disable skill_mcp_dependency_install `
  --disable plugin_sharing `
  --disable remote_plugin `
  --disable recommended_plugins `
  --disable browser_use `
  --disable browser_use_external `
  --disable browser_use_full_cdp_access `
  --disable computer_use `
  --disable image_generation `
  --disable tool_suggest `
  --disable memories `
  --sandbox <sandbox> `
  --cd <owner-worktree> `
  --skip-git-repo-check `
  --ephemeral `
  --ignore-user-config `
  --ignore-rules `
  --strict-config `
  --output-schema <result-schema> `
  --json `
  --output-last-message <last-message-file> `
  -
```

The prompt is supplied on standard input by the outer recorder; JSONL stdout, stderr, last message,
argv, redacted environment, prompt hash, pre/post executable identity, pre/post full Git identity,
exit code, and byte hashes are retained in the request's external evidence root. `workspace-write`
is used only for an implementation process;
`read-only` is mandatory for review. Web search, app, plugin, hook, MCP installation, browser,
computer, image generation, memory, dynamic skill search, automatic delegation, and interactive
approval capabilities are disabled. The matching prompt-input proof must demonstrate that these
overrides excluded project instructions and all skill instructions/locators. OpenAI's
[Codex CLI reference](https://developers.openai.com/codex/cli/reference) documents `workspace-write` as
the sandbox for unattended work contained in the workspace and `--sandbox` as the policy for
model-generated commands; the launcher still treats the model-visible proof, not the requested flag
alone, as the run-specific attestation.

The `windows.sandbox` entry is part of the shared closed configuration supplied identically to both the
debug proof and exec. OpenAI's
[Codex configuration reference](https://developers.openai.com/codex/config-reference) lists
`unelevated` as a native Windows sandbox mode. In the pinned `rust-v0.147.0` source,
[`windows_sandbox.rs`](https://github.com/openai/codex/blob/rust-v0.147.0/codex-rs/core/src/windows_sandbox.rs#L21-L44)
maps explicit `Unelevated` to `RestrictedToken`, while absent configuration and disabled legacy feature
flags resolve to `Disabled`;
[`config_toml.rs`](https://github.com/openai/codex/blob/rust-v0.147.0/codex-rs/config/src/config_toml.rs#L759-L785)
then downgrades a requested Windows `WorkspaceWrite` mode to `ReadOnly` only when that level is
`Disabled`. The explicit setting prevents that downgrade; it does not weaken the exact permission-text,
workspace-root, managed-profile, or environment-grammar proof.
If either skill-disable key is unsupported, rejected, or ignored, the preclaim diagnostic fails and no
request root exists. The absence proof repeats immediately before each ADMIN call; an observed ambient
skill set is never accepted. The launcher copies `auth.json` into
a request-bound disposable `CODEX_HOME`, never records credential values, allows any provider refresh
only against that copy, and removes the entire disposable home before committing. A complete ordinal
whole-tree path/type/length/content manifest proves the live `CODEX_HOME` is byte-identical before and
after. The scanner refuses a root or entry reparse point, an alternate data stream, a sharing/access
error, partial enumeration, or any unreadable default stream; it never treats a partial manifest as a
baseline. Any drift or unattestable final state stops before the ADMIN commit.

Immediately before each model process, `codex debug prompt-input` runs from that process's exact
primary owner worktree with the same disposable `CODEX_HOME`, sandbox, and explicit config/feature
closure supported by that subcommand. Debug does not receive the exec-only authority/output closure:
`--skip-git-repo-check`, `--ephemeral`, `--ignore-user-config`, `--ignore-rules`, `--strict-config`, or
the result-schema/JSON/output flags. The corresponding `codex exec` adds all of them; pinned 0.147.0
specifically rejects `--strict-config` on `codex debug`. The diagnostic parser therefore rejects any
resulting ambient project/rule/instruction surface instead of pretending unsupported exec flags were
passed.
It must produce retained JSON proving the exact model-visible permissions instruction, workspace roots,
and permission profile expected for that call and that no project `AGENTS.md`,
fallback project instruction, project config, plugin, MCP server, hook, or any skill instruction enters
the model-visible input. It must also prove no `<skills_instructions>` block and zero skill locators at
preclaim and before both ADMIN calls; any injected bundled or other skill content fails closed.
The outer prompt names absolute publication, owner-worktree, candidate, and request-file paths.
The shared parser requires the implementation proof to name only the owner worktree as its ordinary
writable path and requires the review proof to contain no ordinary filesystem write-path entry. A proof
for one sandbox cannot authorize the other call.

### 3.3 Calls, retries, and review

`ADMIN-BOOTSTRAP` permits exactly one `workspace-write` implementation process followed, after the
contained deterministic gates and candidate-tree seal, by one fresh `read-only` review process. A
non-PASS review, timeout, quota/auth error after process start, identity mismatch, or capability
violation terminates that Approval-1 lineage; there is no ADMIN retry.

Each numbered writable owner partition permits at most two ordered rounds. A round is one fresh
`workspace-write` implementation process and one fresh `read-only` review process. Round 2 may start
only from a schema-valid round-1 `CHANGES_REQUIRED` review and receives only the bounded finding
records. PASS ends the partition. FAIL, INVALID, BLOCKED, an exhausted second round, a forked parent,
or any additional call stops under the base plan's status/recovery rules. Review output is advisory
until deterministic tests, path audit, diff audit, and the outer controller all pass.

No process may spawn a subagent or phone-a-friend. This restriction concerns Goal-NP implementation
orchestration only; it does not modify the D08/native-skill friend behavior that NP-12 and NP-40 must
qualify.

### 3.4 Publication-8 pre-claim readiness, Windows sandbox enforcement, and result boundary

`Preflight` is repeatable, advisory, and non-consuming. It invokes no `codex exec` or model process and
creates or changes no launcher-owned repository, evidence, approval, Git-object/index, or live-home path.
Its only content-bearing write surface is the exact fresh staging subtree
`%LOCALAPPDATA%\SkillMesh\Staging\GoalNP\Publication8\<request-id>\permission-attestation` containing a
scratch-only `CODEX_HOME`, copied authentication, output, and a dedicated `temp` child for the pinned
non-model `codex debug prompt-input` process. The child process's `TEMP` and `TMP` are both set to that
exact normal staging child; no OS-default temporary path is authorized. Every component must be a
normal non-reparse path with no alternate
data stream; a stale target is `PERMISSION_STAGING_COLLISION`, never reusable scratch. The launcher may
create missing normal ancestors on the fixed `Staging\GoalNP\Publication8\<request-id>` route, records
which ancestors it created, and removes only those launcher-created ancestors after proving each empty.
The launcher
manifests the live Codex home before and after without writing it. `Preflight` removes the complete
request root and all launcher-created ancestors; their absence plus continued absence of the
Publication-8 evidence root is mandatory before PASS. A cleanup failure is
`PERMISSION_STAGING_CLEANUP_FAILED`; any other containment mismatch is
`PERMISSION_ATTESTATION_FAILED`.
Ordinary OS access metadata and telemetry are outside the launcher's control and are not claimed as
writes. `Run` does not trust an earlier result: it creates a fresh staging proof before claim and retains
that exact disposable layout through request claim and the ADMIN proof/model sequence. Every
implementation or review `codex debug prompt-input` and `codex exec` child receives both `TEMP` and
`TMP` bound to the layout's normal `temp` child. Run copies the retained attestation into the claimed
evidence root and removes all staging bytes in its `finally` boundary. A Run failure after claim remains
terminal even when staging cleanup succeeds.

The permission proof uses the implementation-shaped supported arguments: pinned Codex CLI and Terra
request, every explicit config and feature disable shared with exec—including exactly
`windows.sandbox="unelevated"`—`--sandbox workspace-write`, and the approved repository as primary
`--cd`, with no redundant repository `--add-dir`. It does not use
the exec-only authority/output flags enumerated in Section 3.2; exec requires all of them. The parser
requires exactly one
model-visible permissions block and one environment block; effective `sandbox_mode=workspace-write`;
approval policy `never`; restricted network; cwd equal to the approved repository; exactly one workspace
root equal to that repository; and a managed permission profile whose only ordinary filesystem write
path is that repository. Exactly two Codex temporary special writes, `:slash_tmp` then `:tmpdir`, must
accompany it; the read-only review proof permits no ordinary or special write entry.

The workspace-write permission renderer takes that canonical owner root as an explicit argument. Its
complete normalized permissions text contains the exact line
`` The writable root is `<canonical-owner-root>`.`` after the approval sentence and immediately before
the closing `</permissions instructions>` tag. The initial character is one ASCII space; the backticks,
path spelling, terminal period, and line position are significant. Read-only permissions contain no
writable-root annotation. The accepted workspace-write canary obtains the annotation from the first and
only `workspace_roots` value. The independent `missing-writable-root-annotation` and
`wrong-writable-root-annotation` canaries must both fail; acceptance cannot be proved only by a fixture
emitted through the same expected-text helper.

Field checks are not the acceptance boundary. After CRLF/lone-CR to LF normalization and outer trim,
the complete permissions text must equal the launcher's pinned sandbox-specific template with no
remainder. The complete environment text must equal its reconstructed grammar, whose sibling order is
`cwd`, `shell=powershell`, exact local execution date as `yyyy-MM-dd`,
`timezone=America/Los_Angeles`, then `filesystem`. The workspace-write filesystem entries must occur in
this exact order: read special `:root`; write the approved repository; write special `:slash_tmp`; write
special `:tmpdir`; read repository `.git`; read repository `.agents`; read repository `.codex`. The
read-only filesystem contains only read special `:root`. Embedded parser canaries inject extra
permission/environment text and must be rejected. The parser also
rejects ambient project instructions, project config, plugin/MCP/hook input, every
`<skills_instructions>` block, and every skill locator. Requested flags alone never constitute
attestation. The parser accepts exactly three `message` items and three text parts in order: one
`developer` item with one nonempty permissions `input_text`, one `user` item with one nonempty
environment `input_text`, and one `user` item with the exact nonempty diagnostic `input_text`. Any extra
item, content part, role, content type, skills block, locator, or text drift fails. In `Preflight` or
the repeated pre-claim proof, any parse, cardinality, identity, permission, path, cleanup, or
containment mismatch is `PERMISSION_ATTESTATION_FAILED`, emits no PASS, and leaves no request/evidence
root. A per-call mismatch after `Run` claims the root records terminal `blocked` evidence and never
authorizes another call or retry. For a permissions-text mismatch, diagnostic metadata may add only
`permission_expected_sha256`, `permission_actual_sha256`, `permission_expected_line_count`,
`permission_actual_line_count`, the one-based `permission_first_differing_line_number`,
`permission_expected_line_present`, `permission_actual_line_present`, and nullable
`permission_expected_line_sha256` / `permission_actual_line_sha256` for only that differing line. It
never includes raw permission text, the differing line's content, an unredacted path, or arrays of other
line hashes.

The attestation and `codex exec` remain separate pinned CLI processes. Reusing the same executable hash,
closed explicit permission shape across their documented diagnostic/exec command surfaces,
repository workspace, and retained disposable home narrows but cannot
eliminate the time-of-check/time-of-use interval. Publication 8 therefore claims only the exact
model-visible debug surface and its continuity controls, not an independently observed kernel policy for
the later model process. A subsequent model refusal is recorded under its stable model-verdict code; it
never retroactively turns the proof into PASS evidence about the execution process.

The shared function also runs a no-redirection, no-file process-result canary through the exact
production handle/exit-code capture primitive. It resolves `[Environment]::SystemDirectory\cmd.exe`
to a full leaf path, runs `/d /s /c "exit 0"` and `/d /s /c "exit 37"` under finite timeouts, and
requires the cached exit codes to be integer `0` and `37` respectively. Each child is started with
`-NoNewWindow -PassThru`. The primitive immediately reads the raw handle, explicitly rejects null,
the wrong type, or `IntPtr.Zero`, then caches it; performs the timed wait and unconditional drain wait;
reads raw `ExitCode` exactly once; explicitly rejects null or a non-`Int32` value before any cast or
typed assignment; and returns one cached integer without applying the production zero-success policy.
The canary checks both expected values, while production callers separately reject nonzero. A start,
handle, timeout, capture, type, or expected-value failure stops pre-claim, emits no PASS, and creates no
request root. `Run` repeats the canary before claim. PASS records only deterministic expected/observed
values plus the resolved canary executable path and its observed SHA-256; the publication does not
freeze an operating-system binary hash.

That function requires Desktop Windows PowerShell 5.1; uses one Win32 process census to validate the
complete current-process ancestry by PID and creation time; rejects a `Code`, `Cursor`, `codex`,
`claude`, or `ChatGPT` ancestor; and requires zero live processes with those names system-wide. It does
not terminate any observed external, operator, or session process and does not retain command lines;
failure cleanup may terminate only a still-live launcher-owned canary child that the launcher started
and then unconditionally drains. A missing,
reused, cyclic, or temporally impossible ancestry edge fails closed. A standalone shell reached through
only an ordinary terminal/explorer chain is permitted.

With `GIT_OPTIONAL_LOCKS=0`, `core.fsmonitor=false`, and `core.untrackedCache=false`, the function uses
only read-only Git inspection and validates the exact branch, commit, clean status, ten committed bundle
blobs, Codex and Python identities, canonical Publication-8 approval bytes, absent Publication-8 request
root, frozen Publication-3, Publication-4, and Publication-5 evidence, the exact Publication-6 preclaim
record described in Section 2.4, and the exact Publication-7 retired preclaim record described in
Section 2.5. Each preclaim check includes its canonical approval file and handoff, approved commit
ancestry, reproducible request identity, and absent evidence-request, staging-request, and
staging-publication roots. The bundle also carries Publication 7's exact mismatch diagnostics as
operator-reported historical context, not as a live artifact check against a nonexistent receipt. It
computes the complete live-`CODEX_HOME` manifest twice and
requires the two scans to be byte-identical. Other than the contained permission proof above, it runs no
temporary-index, `write-tree`, test, or model operation. On PASS, `Preflight` emits only a deterministic JSON readiness record to
stdout. A failed readiness check exits nonzero, emits no PASS record, and creates no request/evidence
root.

Pre-claim quiescence or live-home failures are readiness failures, not execution attempts, and may be
checked again after the environment is made quiescent. Authority/publication mismatches fail closed.
Once `Run` exclusively creates the distinct Publication-8 request root, any failure is terminal and the
root may not be deleted, reset, or reused.

The process-recorder failure-code vocabulary is closed:
`PROCESS_START_FAILED`, `PROCESS_HANDLE_UNAVAILABLE`, `PROCESS_TIMEOUT`,
`PROCESS_EXIT_CODE_UNAVAILABLE`, `PROCESS_EXIT_NONZERO`, `PROCESS_CANARY_FAILED`,
`PERMISSION_ATTESTATION_FAILED`, `PERMISSION_STAGING_COLLISION`,
`PERMISSION_STAGING_CLEANUP_FAILED`, `PRIOR_PUBLICATION7_PRECLAIM_MISMATCH`,
`PRIOR_PUBLICATION6_PRECLAIM_MISMATCH`,
`PRIOR_PUBLICATION5_EVIDENCE_MISMATCH`,
`PRIOR_PUBLICATION4_EVIDENCE_MISMATCH`, `PRIOR_PUBLICATION3_EVIDENCE_MISMATCH`,
`MODEL_VERDICT_BLOCKED`, `MODEL_VERDICT_CHANGES_REQUIRED`, `MODEL_VERDICT_INVALID`,
`MODEL_PASS_MATERIAL_FINDINGS`, and `UNEXPECTED_FAILURE`. Before claim, a canary failure emits a stable nonzero failure with
`PROCESS_CANARY_FAILED` and may name one process-subset `cause_code`, but writes no state or root. After
claim, a schema-valid `BLOCKED` maps to `MODEL_VERDICT_BLOCKED`, `CHANGES_REQUIRED` maps to
`MODEL_VERDICT_CHANGES_REQUIRED`, `INVALID` maps to `MODEL_VERDICT_INVALID`, and a `PASS` carrying any blocker or
significant finding maps to `MODEL_PASS_MATERIAL_FINDINGS`. A model claim that a disabled skill is
required must take the same schema-valid `BLOCKED` path before mutation and is terminal, not authority
to load the skill or retry. A scratch or JSONL native-skill-surface violation maps to
`MODEL_VERDICT_INVALID`. Every terminal path persists `error_code`,
`error_label`, and human-readable `error`; an unknown exception maps only to `UNEXPECTED_FAILURE` and
never expands authority.

## 4. First-producer and administrative sequence

The missing Codex `$build-step` is not installed, discovered, invoked, or treated as authority.
Publication 8 preserves Publication 7's direct executor, Windows PowerShell 5.1 process-result recorder,
primary workspace, exact five-line permission attestation, stable result classification, and external
fail-stop boundary. It changes only the shared closed config for debug and exec by adding exactly
`windows.sandbox="unelevated"`, plus corresponding deterministic readiness/state proof fields in the
precommitted `tools/run-goal-np-terra-bootstrap.ps1` launcher. Those are launcher/state fields, not
additions to `schemas/terra-bootstrap-result-v1.schema.json`; the model-result schema is unchanged. The
launcher is part of the approved publication,
not an ADMIN output. `Preflight` implements Section 3.4 without claiming a request. `Run` independently
repeats that exact gate, then exclusively claims a new root and stores the in-memory readiness record as
`preflight.json` before any later effect. Its request identity is the lowercase SHA-256 of the canonical
UTF-8/LF payload fields: `publication-8-windows-sandbox-enforcement-recovery-v1`, final Publication-8
commit, and exact Publication-8 Approval-1 text hash; Publication-7 approved commit, request ID,
normalized approval hash, approval-file hash, and handoff hash; Publication-6 approved commit, request
ID, normalized approval hash, approval-file hash, and handoff hash; then the frozen request ID, state
hash, and whole-root-manifest hash for Publication 5, Publication 4, and Publication 3 in that order.
These exactly 22 fields are joined with one LF between fields and no final LF; the visible ID is
`tba-<digest>`. The final approved commit binds the complete ten-file tree, so the bounded gate repair
adds no request-preimage field. Publication-7 evidence-request, staging-request, and
staging-publication absences and the corresponding three Publication-6 absences remain six live
predicates, not digest fields. This cannot address, retry, or rehabilitate any terminal earlier lineage or reuse
either superseded preclaim publication. The fresh evidence root is
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\TerraBootstrap\<publication-8-request-id>` and must be absent
through the final pre-claim check.

At both production child-process sites—`Invoke-RecordedProcess`, which owns prompt-input and deterministic
tools, and the direct Terra `exec` site in `Invoke-Terra`—the launcher uses the same handle-cache rule as
the canary. Immediately after `Start-Process -PassThru`, it reads the raw handle, explicitly checks it
for null, type, and `IntPtr.Zero`, then caches it. Both sites retain their existing `-NoNewWindow`
process mode. After the timed wait and unconditional drain wait the recorder
reads raw `ExitCode` exactly once, checks null and `Int32` type before any cast, then caches it. Only that
cached integer is compared and recorded; direct `Invoke-Terra` evidence includes
`exit_code = $exitCode`. A caught recorder failure kills and unconditionally drains only its own
still-live child, preserves the original coded failure unless cleanup itself fails, maps cleanup failure
to `UNEXPECTED_FAILURE`, and always disposes the process object without rereading `ExitCode`. An
unavailable handle or exit code is a recorder failure, not a successful process and not authority to
infer or retry a model call.

After the claim, `Run` validates the closed argv, primary owner workspace, frozen prompts,
result schema, output hashes, and terminal state. It rechecks process quiescence immediately before and
after prompt-input and every Codex process. After allocation, immediately before each prompt-input or
Codex process, before commit, on success, and on every catch path it revalidates live-home, frozen
Publication-3/4/5 roots and approval files, and both Publication-7 and Publication-6
approval/handoff/commit chains plus all six absence predicates. Read-only `Inspect` revalidates those
same frozen inputs plus the exact
Publication-8 request/state identity and, for PASS, the canonical receipt path/hash/content; it bypasses
the launch quiescence gate so a later agent may inspect without acquiring execution authority. `Run` is
create-new: a crash or non-PASS after root claim leaves durable `blocked` state, and another model attempt
under that lineage is forbidden. Publication 8 then proceeds:

1. After recovery Approval 1, the operator copies the command block, closes this Codex/VS Code and every
   other Codex, ChatGPT, Cursor, IDE-agent, and Claude session, then opens standalone ordinary Windows
   PowerShell. No coordinator model invokes the launcher. The operator pastes the entire explicitly
   marked fail-stop block as one script scope. The operator runs `Preflight`; only a PASS permits `Run`,
   which repeats the same permission proof and every other gate before claim. Reopening or continuing an
   agent before `Run` exits makes the ancestry non-quiescent and must be refused. The frozen
   implementation prompt allows only the base plan's closed 15-path ADMIN Files set and uses the
   committed result schema.
2. After the new root is claimed, the launcher records the readiness proof, then before review validates
   every ADMIN output and the exact 661-byte requirements lock;
   validates CPython `3.14.3` and executable SHA-256
   `cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b`; creates a request-owned
   venv/cache/temp tree; installs only `--require-hashes --only-binary=:all:` dependencies; runs the
   focused ADMIN tests and full root tests with contained pytest cache; and seals a temporary-index
   candidate tree, binary diff, `git diff --cached --check`, closed path set, and all result hashes.
3. The fresh read-only Terra review uses the same repository primary workspace and matching model-visible
   `read-only` proof, and receives the exact base tree, candidate tree/diff, absolute plan
   paths, implementation JSONL hash, and deterministic test receipts. It cannot edit. `PASS` with a
   blocker or significant finding is rejected by the deterministic launcher even though the shared
   Structured-Outputs-compatible result schema permits those severities for non-PASS responses.
4. The launcher revalidates live-home, frozen Publication-3 through Publication-5 evidence,
   Publication-7 and Publication-6 preclaim inputs and all six absence predicates, and Git identity,
   stages exactly
   the reviewed candidate tree,
   creates the fixed ADMIN commit only after every gate passes, and seals immutable implementation/
   review evidence. Neither model process commits, updates an issue, or writes external State.
5. The committed `bootstrap-goal-np-approval.ps1 -Action Prepare` records the exact revised sentence,
   ten-file publication hashes, amended executor identity, ADMIN commit/evidence, and all existing
   Approval-1 fields except the legacy publication-gate attestation field. That field is replaced by the
   single ordered plan-review `PASS` -> plan-redline `PASS` -> plan-wrap `READY` attestation and its
   gate-record plus identical start/end ten-file SHA-256 maps defined in Section 1; the legacy field is
   not retained beside it.
6. `-Action Sync` is now a **zero-model deterministic operation**. The committed wrapper parses the
   41 Plan IDs and issue bodies from the approved bytes, exhaustively reads issues through the
   capability shim, produces the exact allowlisted create/edit/close action set, journals each GitHub
   mutation, backfills issue IDs, and seals `ADMIN-SYNC`. It does not invoke `/repo-sync`, `$repo-sync`,
   Claude, Codex, or any other model. Existing mapping, collision, prompt-injection, pagination,
   redaction, crash-recovery, and cardinality tests remain mandatory.
7. `-Action Inspect` must report schema-valid PASS before `RunBootstrapNP01` is legal.
8. `RunBootstrapNP01` uses the same direct Terra envelope for NP-01, seals the candidate/CAS/review/
   status lineage, and produces the request-bound controller.

The existing base-plan ADMIN paths remain the exact write set. No unnamed `v2` file is authorized.
The `goal-np-bootstrap-execution.json` discriminator becomes `terra-direct-v1`, and the existing
`np-bootstrap-execution-v1.schema.json` and other named v1 schemas define that branch. Those schemas
replace frozen Claude-closure and `/repo-sync` package fields with Codex executable,
base-argv, prompt, implementation-attempt, review-attempt, focused/root test, path/diff audit, and
zero-model issue-sync implementation hashes. Mixed Claude/Terra or undeclared schema branches are
invalid.

## 5. Numbered-step controller

NP-01 must implement and test a `terra-direct-v1` mode in the Goal-NP controller. NP-01 itself uses
the administrative direct envelope. NP-02..NP-11 then use the exact controller and executable closure
produced by NP-01. NP-11 freezes that closure and its canary. NP-12 proves it together with the base
plan's two native-host substrate cells. NP-13..NP-39 and NP-41 may proceed only through the exact
NP-12-PASS controller closure.

For each writable owner partition the outer controller alone performs this order:

```text
Begin/status -> Terra implementation -> Terra read-only review -> deterministic gates/path audit
-> code commit -> candidate-registry CAS -> optional post-commit finalizer -> issue action
-> terminal aggregate -> status event/checkpoint
```

The two Terra processes cannot commit, move refs, update the registry, mutate issues, append status,
run source integration, publish a release/packet, or touch another owner. Those remain deterministic
outer-controller effects with the base plan's journals and recovery. Operator NP-12 and NP-40 make no
implementation-model call; their existing Begin/Run/Resume/Record/Finalize controller surfaces and
mandatory stop/reopen boundaries remain.

All controller requests and receipts bind both the immutable base plan and this amendment, the final
Publication-8 commit/hashes, frozen Publication-3/Publication-4/Publication-5 recovery evidence, and the
Publication-7 and Publication-6 approved preclaim inputs,
`terra-direct-v1`, Codex
version/executable hash/base argv, prompt/schema
hashes, requested identity plus reported-identity status/value when available, call IDs, parent/round, stdout/stderr/last-message hashes, and
the deterministic gate/commit/CAS/finalizer/issue/status lineage. Stale Publication-2 Claude executor
fields or mixed Claude/Terra implementation attempts are invalid. References to the product's native
Claude or Codex package tests are not stale implementation attempts.

## 6. External transition handoff

The following is an immutable template, not a publication blob that contains its own hash. After the
Publication-8 commit and exact-byte reviews exist, the publisher generates a separate handoff under
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication8\terra-transition-handoff-<publication-8-commit>.txt`
by substituting only the named Publication-8 placeholders, then hashes and gives it to the operator.
The template has exactly 15 unique substitution tokens: one commit, one request ID, ten ordered bundle
hashes, and three ordered review verdicts.
Neither the commit nor this amendment embeds its own digest. Do not create the Publication-8 approval
file, run the launcher, or start Codex before recovery Approval 1. The operator must copy the launch
block, close the active Codex/IDE UI, and execute it in standalone Windows PowerShell; replying to or
reopening an agent before `Run` exits recreates forbidden ancestry. After `Run` exits, `Inspect` may be
invoked from a reopened session. No coordinator model may add a call.

```text
Goal NP Publication 8 — Terra bootstrap Windows sandbox-enforcement recovery handoff

Version: publication-8-windows-sandbox-enforcement-recovery-v1
Status: AWAITING RECOVERY APPROVAL 1

This handoff is operator guidance only. Reading, copying, or hashing it does not grant Approval 1.
Do not create the Publication-8 approval message, run Preflight, invoke Terra, or start any Goal-NP
implementation until Abraham supplies the exact approval sentence below in a new message.

EXACT RECOVERY APPROVAL-1 SENTENCE

Approve Goal NP plan Publication 8 with D01-D10 and the Terra Windows sandbox-enforcement recovery amendment.

The approval file must contain only that sentence as UTF-8 without BOM plus exactly one final LF.
Canonical future path:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication8\approval1-message.txt
Trimmed text SHA-256: c54648e8eedfebb9181ea04043cca948692a78e35bd3f42b7cca92352be74c79
LF-terminated file size: 110 bytes
LF-terminated file SHA-256: 2c9b4f34f0c53a634725f608b724558cf920a9e0d606b4a09707d7e15744ce7e

PUBLICATION-8 AUTHORITY

Worktree: %LOCALAPPDATA%\SkillMesh\Worktrees\native-codex-skill-parity-plan
Branch: plan/native-codex-skill-parity
Commit: <publication-8-commit>

Ten-file bundle:
- plan.md
  SHA-256: <publication-8-plan-sha256>
- documentation/native-claude-codex-skill-parity-plan.md
  SHA-256: <publication-8-base-plan-sha256>
- documentation/native-claude-codex-skill-parity-terra-amendment.md
  SHA-256: <publication-8-terra-amendment-sha256>
- documentation/native-claude-codex-skill-parity-proposal.html
  SHA-256: <publication-8-proposal-sha256>
- tools/run-goal-np-terra-bootstrap.ps1
  SHA-256: <publication-8-terra-launcher-sha256>
- schemas/terra-bootstrap-result-v1.schema.json
  SHA-256: <publication-8-terra-result-schema-sha256>
- experiments/recovery/cross-family-fixture/create_fixture.py
  SHA-256: <publication-8-cross-family-fixture-sha256>
- experiments/recovery/cross-family-fixture/probe.py
  SHA-256: <publication-8-cross-family-probe-sha256>
- tests/experiments/test_cross_family_probe.py
  SHA-256: <publication-8-cross-family-test-sha256>
- tests/distributions/test_path_choke_point.py
  SHA-256: <publication-8-path-choke-test-sha256>

Ordered publication gates on those exact bytes:
1. plan-review: <publication-8-plan-review-verdict>
2. plan-redline: <publication-8-plan-redline-verdict>
3. plan-wrap: <publication-8-plan-wrap-verdict>

Publication 8 keeps D01-D10, D08, the 41-step Goal-NP DAG, the two native qualification profiles,
the unchanged direct Terra/xhigh model and call envelope, and the Approval-2/live-cutover prohibition.
It retains Publication 7's process recorder, cmd.exe canary, repository primary workspace, exact
five-line sandbox/zero-skill attestation, scratch/transcript audits, stable model-verdict codes, and
fail-stop operator scope. Its only execution correction is the narrow shared closed-config entry
`windows.sandbox="unelevated"` for debug and exec, selecting `RestrictedToken` and preventing pinned
Codex 0.147.0 from downgrading requested `workspace-write` to `read-only` on Windows.
The same approved bundle repairs the two red clean-P7 baseline gate families before any request claim.
The cross-family builder normalizes candidate-copy and declared-inventory bytes to LF; the probe seals
that same canonical inventory, rejects fixture/source or fixture/receipt identity drift, and its tests
cover LF, CRLF, and lone-CR inputs. The path-choke gate carries an exact whole-file exemption for this
fixed-boundary one-off launcher. The unchanged full-root `python -m pytest` gate remains mandatory;
none of these repairs narrows collection or waives a failure.

Debug and exec share every supported explicit model/config/disable/sandbox/cd flag; exec alone adds its
skip/ephemeral/ignore/strict/schema/JSON/output closure. The normalized permission and environment texts
must match their complete reconstructed grammars with no remainder. Workspace-write permissions remain
exactly five lines, including the exact leading-space
`` The writable root is `<canonical-owner-root>`.`` line; `read-only` output remains invalid for an
implementation proof. Workspace-write orders read :root, write repository, write :slash_tmp, write
:tmpdir, then read repository .git, .agents, and .codex; read-only has only read :root. Both
skill-disable flags must be effective, with no skills block/locator.

Start read-only. Verify the exact worktree, branch, HEAD, clean status, all ten hashes, Codex CLI
0.147.0, native executable SHA-256 935a1911ed2556e4ffcec995f4886ac2ac425863ba26fed264df62e30272ad9d,
and Terra/xhigh availability. Verify all three frozen prior evidence roots and approval files exactly,
then verify the Publication-7 and Publication-6 approval/handoff/commit chains and all six required
absence predicates. Do not
pull, rebase, amend, normalize, install a skill, modify prior evidence, or substitute publication bytes.
A mismatch stops.

TERMINAL PUBLICATION-3 INPUT — NEVER RETRY OR MODIFY

Publication-3 commit: 71a5aea3fd21320d2fbb3cb9228bc52e42cb3215
Publication-3 handoff:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication3\terra-transition-handoff-71a5aea3fd21320d2fbb3cb9228bc52e42cb3215.txt
Handoff SHA-256: 8382385b90568e947b7aa1abe53d4089650817fb5a72a33b014d5d19d62bd453
Approval-file SHA-256: 33d3e1756ed2bfd661698da3dfdf85a921380efd87fe3d635b777dafe3c6e04b
Normalized approval-text SHA-256: 66df8cd413fddd097e80dc63ccfacab221e96c72c795345d14b72ae1ae3474ef
Request ID: tba-b7e5898e6389ff19b3ce34738f16b47d0a832dfc4625789fbcf4308352f2b1a0
Blocked state SHA-256: ae59a6ac7f512d2e399675fe541b916d1710c209a13b45433642cf019a07df97
Whole-root manifest: 3 entries; SHA-256 9b01de1f550019a8bf81c23431925b6f38a173ec1ce22023c765a2a8d290cdcf

Publication 3 stopped before any prompt or model call while its launcher tried to attest a locked live
CODEX_HOME database. Its evidence root is immutable historical input. Never retry, delete, rename,
alter, repair, reuse, or adopt that request or root.

TERMINAL PUBLICATION-4 INPUT — NEVER RETRY OR MODIFY

Publication-4 commit: 58223098887468953570ecf153494871c5404605
Publication-4 handoff:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication4\terra-transition-handoff-58223098887468953570ecf153494871c5404605.txt
Handoff SHA-256: 0690c2976b20f665872327a4bc8cc8f17bbea03869c73d52490b28044e54d5e5
Approval-file SHA-256: 2f74ea66ac7bdac38b419fd24b7e6caa9479de007bc178e69acd54f9f8b42857
Normalized approval-text SHA-256: 1a7698085d7bc12e74d60874e0d64b4d069b039470ab17701541cfe6c77202fe
Request ID: tba-461c20be4d35c7255a83d05f91f16c5bccbdd5a36af738360bcedc330ab6b1e4
Blocked state SHA-256: 4517ecd2d5ff948bbcf7763e32686797f65b5112ceb14e71c96c8222e6e12e05
Whole-root manifest: 9 entries; SHA-256 893c099e299a5152f26edd912a5bfcdc75bd69e030dfd40653c0365ffe4d5e44
Prompt-input stdout: valid JSON; SHA-256 31757cf1c4ac11f2eb6f63880e92b3a036f82e0f185866edf9ae98619c5e7681
Prompt-input stderr: empty; SHA-256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Terminal error: implementation-prompt-input exited .

Publication 4 stopped after prompt-input and before `codex exec`, Terra/model execution, a model result,
tests, ADMIN diff, or commit. Its live Codex home and the frozen Publication-3 root remained unchanged.
Never retry, delete, rename, alter, repair, reuse, or adopt that request, root, or output.

TERMINAL PUBLICATION-5 INPUT — NEVER RETRY OR MODIFY

Publication-5 commit: 6d292bb37c37944c71ed8b18214fabb23f22869e
Publication-5 handoff:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication5\terra-transition-handoff-6d292bb37c37944c71ed8b18214fabb23f22869e.txt
Handoff size: 13,450 bytes
Handoff SHA-256: ee92b0f882772af327d25d0bec82c9d381ff9e2f309611dd0856d0589c62030e
Approval-file SHA-256: 5ad7472cb113d6965de18204dc1b7f860a0c2982ad1e8152e34547efa714a8e3
Normalized approval-text SHA-256: 2d19ad716f3179baf67c67c77d19dfb29697ea5b2e6f2b0a0d1fe87ee03d0f47
Request ID: tba-03e474757a5e0c92e8d3f0bd4c5a0731a742397a43c99d5e027016643fced916
Blocked state SHA-256: b0e9355ff3f39c1ccca196ae45ebe7c4f042c9fcd2587d84882c7d9af4724f50
Whole-root manifest: 17 entries; SHA-256 11f84ea3e5140a2832586f63fc362c97b92286b1663c91df2c80fb7784d6f700
Invocation: requested gpt-5.6-terra/xhigh/workspace-write; SHA-256 3752f8ea94fd57bb72d3d495d2ba88e8a6068d80552dc9ef9f0292714887ff36
Prompt proof: hard-coded read-only; SHA-256 a50ad81bae6f73f5d85c369f5ebce0904a903a23ce90c6dced83a890d5b7ea8b
Model result: schema-valid BLOCKED; SHA-256 2e56256153e3c50de8c981a1d13e53e1e18fb495276f3c34517a1ef8895c295c
Stored terminal error: UNEXPECTED_FAILURE / implementation returned BLOCKED.

Publication 5 completed one real Codex implementation process requesting Terra/xhigh; no independent
resolved-model field was available. Its prompt proof did not attest that call's sandbox. All 11 model
command starts were inspections/reads, with one bundled read declined; no filesystem-write command was
attempted, so the record is not an observed operating-system write denial. The repository remained
clean at the approved commit, all 15 ADMIN outputs remained absent, and no test, diff, commit, issue, or
product mutation occurred. Its live Codex home and both earlier roots remained unchanged.
Never retry, delete, rename, alter, repair, reuse, or adopt that request, root, or output.

SUPERSEDED PUBLICATION-7 PRECLAIM INPUT — NEVER RERUN OR MODIFY

Publication-7 commit: 40d671d75e1aa6c6b31eab70caa8f4d07ed51383
Publication-7 handoff:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication7\terra-transition-handoff-40d671d75e1aa6c6b31eab70caa8f4d07ed51383.txt
Handoff size: 21,345 bytes
Handoff SHA-256: c0554be563284c8fe9eb2f4aa2985505c76d39eb17dd1aeb1313dd78f3b43f81
Approval file:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication7\approval1-message.txt
Approval-file size: 104 bytes
Approval-file SHA-256: a849c6f49c9557ee7e11bdc4c01f324e17fe260d5abdc648141715d22120f8a5
Normalized approval-text SHA-256: fe5736f56b0edb305ef2e1632d5882a6d85d930c06862d9ec9ce26a28b9a23aa
Original request domain: publication-7-writable-root-grammar-recovery-v1
Expected request ID: tba-f3b13b6337e230003d8721ad759b398d31536eae9d9b2bdf0860ff8b1d849568
Expected request root:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\TerraBootstrap\tba-f3b13b6337e230003d8721ad759b398d31536eae9d9b2bdf0860ff8b1d849568
Evidence request root status: ABSENT
Expected state path:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\TerraBootstrap\tba-f3b13b6337e230003d8721ad759b398d31536eae9d9b2bdf0860ff8b1d849568\state.json
State path status: ABSENT
Publication-7 staging request root:
%LOCALAPPDATA%\SkillMesh\Staging\GoalNP\Publication7\tba-f3b13b6337e230003d8721ad759b398d31536eae9d9b2bdf0860ff8b1d849568
Staging request root status: ABSENT AFTER COMPLETE TRANSIENT CLEANUP
Publication-7 staging publication root:
%LOCALAPPDATA%\SkillMesh\Staging\GoalNP\Publication7
Staging publication root status: ABSENT AFTER COMPLETE TRANSIENT CLEANUP

The operator-reported Preflight terminal JSON was BLOCKED with
PERMISSION_ATTESTATION_FAILED / preclaim-permission-attestation, full error
`[PERMISSION_ATTESTATION_FAILED] [preclaim-permission-attestation] Permissions text differs from the complete closed permission grammar.`,
and `evidence_root_absent=true`.
Expected permissions SHA-256: aa613097ace0f175545df760139a7bbc9c505a0feb207dbc2552438ce70db03d
Actual permissions SHA-256: 29dad5ed6993c5e717376e0a1c84d54ab60ee593510916ac6cee4295e803315d
Expected line count: 5
Actual line count: 4
First differing line: 2
Expected differing line present: true
Actual differing line present: true
Expected line-2 SHA-256: 06c4b2fd6aab85ab9ea0e5598cbcdead5142d7cb56e851770163c1b9f480338b
Actual line-2 SHA-256: d9cebe887c2ee11798faa526216e1d4af5d90cd47231862b50eb60cc5ac76464

These diagnostics bind the expected exact five-line workspace-write text and actual exact four-line
read-only text without disclosing path-bearing raw permissions. Run never started; there was no
`codex exec`, Terra/model call, durable claim, state, receipt, evidence manifest, test, ADMIN diff,
commit, issue, product, or repository mutation. Preflight transiently created only its staging scratch
and fully cleaned it. The durable inputs are the exact commit, approval file, and handoff above; the
evidence/state, staging-request, and staging-publication absences are live preclaim predicates. Never
edit, delete, rename, replace, or rerun Publication 7, and never reuse its exact-byte approval as
authority for Publication 8.

SUPERSEDED PUBLICATION-6 PRECLAIM INPUT — NEVER RERUN OR MODIFY

Publication-6 commit: d0f83210e3092e18a28ee24db20a1af95887c31b
Publication-6 handoff:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication6\terra-transition-handoff-d0f83210e3092e18a28ee24db20a1af95887c31b.txt
Handoff size: 18,494 bytes
Handoff SHA-256: ae085575b9441080ece62194cd4a3144df809eaa9d70b2ed2fcd76624d455b47
Approval file:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication6\approval1-message.txt
Approval-file SHA-256: 064e50a53d93dc976cb98b87a5a49d0260d91f88aadddb23bcd8bf60d9be2add
Normalized approval-text SHA-256: ad20542c0d5dc9b77fbab14413998f614ab178ca4949a1269f06c08f24b3407e
Original request domain: publication-6-sandbox-attestation-recovery-v1
Expected request ID: tba-cc76394efc1359d75b406ce5a2d2300d5ed41020b5cf7fc972ba3039dc3a6ab0
Expected request root:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\TerraBootstrap\tba-cc76394efc1359d75b406ce5a2d2300d5ed41020b5cf7fc972ba3039dc3a6ab0
Evidence request root status: ABSENT
Publication-6 staging request root:
%LOCALAPPDATA%\SkillMesh\Staging\GoalNP\Publication6\tba-cc76394efc1359d75b406ce5a2d2300d5ed41020b5cf7fc972ba3039dc3a6ab0
Staging request root status: ABSENT
Publication-6 staging publication root:
%LOCALAPPDATA%\SkillMesh\Staging\GoalNP\Publication6
Staging publication root status: ABSENT

The operator-reported Preflight terminal JSON was BLOCKED with
PERMISSION_ATTESTATION_FAILED / preclaim-permission-attestation and message suffix
`Permissions text differs from the complete closed permission grammar.` Its full `error` string was
`[PERMISSION_ATTESTATION_FAILED] [preclaim-permission-attestation] Permissions text differs from the complete closed permission grammar.`
and `evidence_root_absent=true`. Preflight scratch output was removed by design; this is context, not a
durable P6 launcher receipt. The durable inputs are the exact commit, approval file, and handoff above;
the evidence-request, staging-request, and staging-publication absences are live preclaim predicates.

Run never started, no request lineage or state was created, and no model, repository, ADMIN, issue, or
product mutation occurred. Publication 8 supersedes the unchanged P6 invocation because its launcher
and publication bytes differ. Never edit or rerun Publication 6, and never reuse its exact-byte approval
as authority for Publication 8.

FRESH PUBLICATION-8 LINEAGE

Request domain: publication-8-windows-sandbox-enforcement-recovery-v1
Expected request ID: <publication-8-request-id>
Expected fresh evidence root:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\TerraBootstrap\<publication-8-request-id>

The request digest is SHA-256 over exactly 22 UTF-8 fields joined by one LF with no final LF: the domain
above; Publication-8 commit and normalized Publication-8 approval-text hash; Publication-7 commit,
request ID, normalized approval-text hash, approval-file hash, and handoff hash; Publication-6 commit,
request ID, normalized approval-text hash, approval-file hash, and handoff hash; then request ID, state
hash, and whole-root-manifest hash for frozen P5, P4, and P3 in that order. Publication-7 and
Publication-6 evidence/state/staging absences are live predicates and are not digest fields. The P8
root must be absent before claim. Preflight and Run
revalidate all prior inputs and predicates. Once Run claims the P8 root,
every failure is terminal; never retry, delete, alter, rename, reuse, or adopt it.

OPERATOR BOUNDARY AFTER THE EXACT APPROVAL IS SUPPLIED

1. While this handoff is visible, copy from the `BEGIN PUBLICATION-8 POWERSHELL SCRIPT` comment through
   the matching `END` comment, inclusive. Those two comment lines are part of the valid script.
2. Close this Codex/VS Code UI and every other Code, Codex, Claude, ChatGPT, Cursor, or IDE-agent
   process. Do not ask a model or tool to launch the block.
3. Open a new ordinary standalone Windows PowerShell 5.1 window.
4. Paste the whole marked block once and run it there. Its outer `& { ... }` scope is fail-stop: any
   thrown error ends the block before later Run/parse/Inspect commands. Do not reply `closed; continue`
   before Run exits; doing so recreates
   the forbidden agent ancestry.
5. Preflight is repeatable and non-consuming. It exercises the pinned cmd.exe exit-code canary and the
   contained non-model sandbox proof, must remove all staging scratch, and must PASS before Run. Run
   independently repeats every check, then creates exactly one Publication-8 lineage. Any post-claim
   failure is terminal. A nonzero Run is recheckable only when exact terminal JSON binds this
   commit/request and proves `evidence_root_absent=true`; a present root or unproven absence is terminal.
6. Inspect is read-only and may also be run after reopening a session once Run has exited.

# >>> BEGIN PUBLICATION-8 POWERSHELL SCRIPT - COPY FROM THIS LINE
& {
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$repoRoot = Join-Path $env:LOCALAPPDATA 'SkillMesh\Worktrees\native-codex-skill-parity-plan'
Set-Location -LiteralPath $repoRoot

$approvedCommit = '<publication-8-commit>'
$expectedRequestId = '<publication-8-request-id>'
$approvalMessage = 'Approve Goal NP plan Publication 8 with D01-D10 and the Terra Windows sandbox-enforcement recovery amendment.'
$approvalMessageFile = Join-Path $env:LOCALAPPDATA 'SkillMesh\Evidence\GoalNP\Publication8\approval1-message.txt'
$approvalMessageParent = Split-Path -Parent $approvalMessageFile
$approvalMessageBytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes($approvalMessage + "`n")

function ConvertFrom-TerminalJson {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$ProcessOutput,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    $lines = @($ProcessOutput | ForEach-Object { [string]$_ })
    for ($start = $lines.Count - 1; $start -ge 0; $start--) {
        if (-not $lines[$start].TrimStart().StartsWith('{', [StringComparison]::Ordinal)) { continue }
        $candidate = $lines[$start..($lines.Count - 1)] -join "`n"
        try {
            $parsed = $candidate | ConvertFrom-Json -ErrorAction Stop
            if ($null -ne $parsed) { return $parsed }
        } catch {
            # Keep scanning backward; Git may have emitted ordinary stdout before the terminal JSON.
        }
    }
    throw "$Label did not end in a valid JSON object; do not continue."
}

if (-not (Test-Path -LiteralPath $approvalMessageParent -PathType Container)) {
    New-Item -ItemType Directory -Path $approvalMessageParent | Out-Null
}
if (Test-Path -LiteralPath $approvalMessageFile) {
    if (-not (Test-Path -LiteralPath $approvalMessageFile -PathType Leaf)) {
        throw 'The canonical Publication-8 approval path exists but is not a file; do not continue.'
    }
    $existingApprovalBytes = [System.IO.File]::ReadAllBytes($approvalMessageFile)
    if ([Convert]::ToBase64String($existingApprovalBytes) -cne [Convert]::ToBase64String($approvalMessageBytes)) {
        throw 'Existing Publication-8 approval message is not byte-identical; do not continue.'
    }
} else {
    [System.IO.File]::WriteAllBytes($approvalMessageFile, $approvalMessageBytes)
}

$launcherArgs = @(
    '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
    '-File', '.\tools\run-goal-np-terra-bootstrap.ps1',
    '-ApprovedCommit', $approvedCommit,
    '-ApprovalMessageFile', $approvalMessageFile
)

$preflightOutput = @(& powershell.exe @launcherArgs -Action Preflight)
$preflightExit = $LASTEXITCODE
if ($preflightExit -ne 0) {
    $preflightOutput | ForEach-Object { Write-Output ([string]$_) }
    throw 'Publication-8 readiness preflight did not PASS. Resolve only the reported pre-claim condition after confirming no request root exists; no Run attempt was created.'
}
$preflight = ConvertFrom-TerminalJson -ProcessOutput $preflightOutput -Label 'Publication-8 Preflight'
if ($preflight.verdict -cne 'PASS' -or
    $preflight.approved_commit -cne $approvedCommit -or
    $preflight.request_id -cne $expectedRequestId -or
    $preflight.evidence_root_absent -ne $true) {
    throw 'Publication-8 readiness output is not the exact PASS contract; do not start Run.'
}
$preflight | ConvertTo-Json -Depth 12

$terraRunOutput = @(& powershell.exe @launcherArgs -Action Run)
$terraRunExit = $LASTEXITCODE
if ($terraRunExit -ne 0) {
    $terraRunOutput | ForEach-Object { Write-Output ([string]$_) }
    try {
        $terraRunFailure = ConvertFrom-TerminalJson -ProcessOutput $terraRunOutput -Label 'Publication-8 failed Run'
    } catch {
        throw 'Terra ADMIN bootstrap failed and evidence-root absence could not be proven from terminal JSON. Treat the Publication-8 lineage as terminal; do not retry or delete evidence.'
    }
    $rootAbsentProperty = $terraRunFailure.PSObject.Properties['evidence_root_absent']
    $actionProperty = $terraRunFailure.PSObject.Properties['action']
    $verdictProperty = $terraRunFailure.PSObject.Properties['verdict']
    $commitProperty = $terraRunFailure.PSObject.Properties['approved_commit']
    $requestProperty = $terraRunFailure.PSObject.Properties['request_id']
    if ($null -ne $rootAbsentProperty -and $null -ne $actionProperty -and
        $null -ne $verdictProperty -and $null -ne $commitProperty -and
        $null -ne $requestProperty -and $rootAbsentProperty.Value -eq $true -and
        [string]$actionProperty.Value -ceq 'Run' -and
        [string]$verdictProperty.Value -ceq 'BLOCKED' -and
        [string]$commitProperty.Value -ceq $approvedCommit -and
        [string]$requestProperty.Value -ceq $expectedRequestId) {
        throw 'Publication-8 Run stopped in its repeated pre-claim readiness gate with the evidence root proven absent. No Run lineage was claimed; correct only the reported readiness condition, then start again with Preflight.'
    }
    throw 'Terra ADMIN bootstrap failed after evidence claim, or root absence was not proven. This Publication-8 Run lineage is terminal; do not retry or delete its evidence.'
}
$terraRun = ConvertFrom-TerminalJson -ProcessOutput $terraRunOutput -Label 'Publication-8 Run'
if ($terraRun.verdict -cne 'PASS' -or $terraRun.admin_commit -notmatch '^[0-9a-f]{40}$') {
    throw 'Terra ADMIN bootstrap did not return its exact PASS contract; do not continue.'
}
$terraRun | ConvertTo-Json -Depth 12

$terraStateOutput = @(& powershell.exe @launcherArgs -Action Inspect)
$terraStateExit = $LASTEXITCODE
if ($terraStateExit -ne 0) {
    $terraStateOutput | ForEach-Object { Write-Output ([string]$_) }
    throw 'Terra ADMIN bootstrap inspection failed; do not continue.'
}
$terraState = ConvertFrom-TerminalJson -ProcessOutput $terraStateOutput -Label 'Publication-8 Inspect'
if ($terraState.phase -cne 'pass' -or
    $terraState.approved_commit -cne $approvedCommit -or
    $terraState.request_id -cne $expectedRequestId -or
    $terraState.admin_commit -cne $terraRun.admin_commit) {
    throw 'Terra ADMIN bootstrap state is not the exact PASS lineage; do not continue.'
}
$terraState | ConvertTo-Json -Depth 12
}
# <<< END PUBLICATION-8 POWERSHELL SCRIPT - COPY THROUGH THIS LINE

AFTER TERRA ADMIN PASS

For ADMIN-BOOTSTRAP and the 39 Type-code implementation/review model slots, use only Publication 8's
terra-direct-v1 process envelope. In those implementation/orchestration slots, do not invoke a missing
$build-step, Claude, /repo-sync, $repo-sync, a router, a repo/user skill, a plugin, MCP, hook, memory,
fallback model, or unlisted helper. This prohibition does not suppress the unchanged base-plan-authorized
Claude native-session qualification/evaluation calls in operator NP-12 and NP-40 or the D08 mixed-family
cells; those calls remain confined to their exact plan-defined profiles, gates, and evidence contracts.
Run the one-attempt ADMIN implementation and independent read-only review. Both receive no skill
instruction or locator: neither call may invoke a skill, and a model that says one is required must
return `BLOCKED` before mutation. Independently verify the
test, path, and diff gates; create only the reviewed ADMIN commit. Then pass the
same exact ApprovalMessageFile to Prepare -> zero-model Sync -> Inspect -> RunBootstrapNP01, using only
paths emitted by the preceding action.

After ADMIN-SYNC PASS, use only the request-bound Goal-NP terra-direct-v1 controller for NP-02 through
NP-41. Obey every dependency, Files boundary, call/evidence cap, deterministic gate, candidate CAS,
issue/status transaction, operator boundary, recovery rule, and invalidation rule. Continue through
plan-authorized reopen boundaries without asking for another program approval.

Approval 2 is not granted. Do not write a live Claude or Codex discovery home, alter live State,
record or consume Approval 2, apply cutover/activation, or run live rollback/recovery. If a terminal
FAIL, INVALID, BLOCKED, corruption, authority mismatch, or exhausted attempt occurs, stop and report
the exact receipt and minimal authorized next action. Otherwise finish NP-41, verify program state
WAITING FOR APPROVAL 2, and report the packet path/hash and exact Approval-2 action without executing it.

```

The external handoff is operator guidance, not another model request or approval. The launcher's
repeatable `Preflight` owns no `codex exec`, model call, or request; its children are the two fixed
process-result canary calls and one pinned non-model `codex debug prompt-input` call confined to removed
staging scratch. Create-new `Run` owns the first model call and refuses to claim its evidence root before
the exact recovery sentence and contained permission-attestation gate pass.

## 7. Review and publication gate

The Publication-8 external-review history is the following reconstructable chronology of superseded
planning candidates, not publication evidence:

- **A - initial six-file candidate:** plan-review returned `FAIL` because the launcher would claim a
  request root before running a baseline gate already known red at clean P7 and because documentation
  gaps remained. No approval, commit, request, or evidence resulted. Abraham then authorized only the
  bounded baseline-gate repair and Publication-8 revision.
- **B - first eight-file candidate after that authorized repair:** plan-review returned `PASS`; the
  following plan-redline returned `FAIL` on the legacy review-order contradiction, incomplete operator
  chain, proposal order and source metadata, and revision grammar. Correcting those findings changed
  bytes and invalidated the preceding plan-review PASS.
- **C - corrected eight-file candidate:** plan-review returned `PASS`; the following plan-redline
  returned `FAIL` because the same unqualified `defect_inventory_sha256` named both LF-normalized
  fixture-builder bytes (`98baaa178e41dc23e5de70e3161de78c66b9c91052c4d0d99295ae1a8928ed37`) and raw CRLF sealed-probe
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
state, request root, or Publication-8 evidence root. No earlier verdict may cross a revision. The
current revised ten-file bytes must restart and complete plan-review `PASS` -> plan-redline `PASS` ->
plan-wrap `READY` in that order.

Before this amendment can be offered for recovery Approval 1:

1. `git diff --check` passes;
2. the base plan's 41 steps, fields, flags, DAG, D08 counts, and Approval-2 boundary remain unchanged;
3. every Publication-2/3/4/5/6/7 implementation-executor reference is either explicitly superseded here,
   retained as frozen recovery evidence, or remains clearly a product/native-qualification reference;
4. the unchanged repository-root `python -m pytest` passes on the exact publication bytes without a
   path argument, skip, xfail, or reduced collection;
5. plan-review and plan-redline return PASS, then plan-wrap returns READY, in that order on the exact
   ten-file bundle;
6. start/end SHA-256 is identical for every exact-byte review; and
7. the publisher creates the external handoff with the final commit and ten hashes without changing
   any publication blob.
