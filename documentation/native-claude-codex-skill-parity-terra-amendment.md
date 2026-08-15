# Goal NP Publication 5 — Terra bootstrap process-recording recovery amendment

**Status:** AWAITING RECOVERY APPROVAL 1
**Base publication:** `documentation/native-claude-codex-skill-parity-plan.md` at commit
`9c224efda851a3501f130830f5cd22b212fc36f0`
**Base-plan SHA-256:** `3c8b3e84b2e192ce1d53cd7488afc8a051a614ee6316df59dad5985af5b73b4d`
**Requested change:** preserve Publication 4's Codex `gpt-5.6-terra`/`xhigh` orchestration decision and
repair only the Windows PowerShell 5.1 child-process result recorder that terminally blocked its
approved first attempt.

This document is a narrow controlling amendment. It does not authorize implementation by itself.
Publication 5 is the exact commit containing this amendment, the base plan, `plan.md`,
`documentation/native-claude-codex-skill-parity-proposal.html`, the precommitted post-Approval launcher
`tools/run-goal-np-terra-bootstrap.ps1`, and its
`schemas/terra-bootstrap-result-v1.schema.json`. Publications 3 and 4 each consumed their Approval-1
sentence in a terminal pre-model request; neither sentence nor any earlier approval can authorize these
bytes or retry either request.

## 1. What this amendment changes

Publication 5 carries forward Publication 4's supersession of these Publication-2 surfaces:

1. the Claude Code/`opus` `ADMIN-BOOTSTRAP` executor and its 76-row installed-Claude closure;
2. the Claude-native `/repo-sync` model call in `ADMIN-SYNC`;
3. the Claude `/build-step` execution envelope used by NP-01..NP-11 and NP-13..NP-39/NP-41;
4. the corresponding executor, requested/reported-identity, call-count, evidence, receipt, schema,
   controller-canary, and Quickstart fields; and
5. only the implementation-orchestration meaning of `/build-step` in those surfaces.

They are replaced by the direct Codex/Terra contracts below. When one of those named surfaces
conflicts with the base plan, this amendment controls. All other base-plan text remains controlling.

Publication 5 additionally supersedes only Publication 4's child-process result-recording boundary:

1. both production `Start-Process -PassThru` sites immediately force and cache the process handle,
   fail closed if it is unavailable or zero, drain the child, capture one non-null integer exit code,
   and compare and record only that cached value; and
2. the shared zero-write preflight exercises the same primitive before request-root claim with pinned
   `cmd.exe` children that return one expected zero and one expected nonzero exit code.

The repair changes no model task, result schema, call count, or capability envelope; Publication-5
authority and recovery-evidence references necessarily replace their Publication-4 counterparts. It
grants no additional Codex, model, or production process, authorizes exactly the two fixed pre-claim
`cmd.exe` canary children, and makes the already-approved closed production process envelope record its
actual result reliably under Windows PowerShell 5.1.

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

## 2. Publication-5 authority and recovery boundary

The only valid recovery Approval-1 sentence is:

```text
Approve Goal NP plan Publication 5 with D01-D10 and the Terra bootstrap process-recording recovery amendment.
```

Its UTF-8 text SHA-256 is `2d19ad716f3179baf67c67c77d19dfb29697ea5b2e6f2b0a0d1fe87ee03d0f47`.
The canonical UTF-8-without-BOM file with exactly one final LF has SHA-256
`5ad7472cb113d6965de18204dc1b7f860a0c2982ad1e8152e34547efa714a8e3`.

Approval is valid only when its receipt binds the final Publication-5 commit and SHA-256 of all six
bundle files. It authorizes the amended administrative prelude, NP-01 through NP-41, disposable
tests/hosts/evidence, and the base plan's non-live candidate work. It does not authorize a live Claude
or Codex discovery-home write, live State mutation, Approval-2 receipt, cutover, activation, or live
rollback. The terminal implementation state remains `WAITING FOR APPROVAL 2`.

Other than the two exact pre-claim `cmd.exe` canary children, any different model, effort, executable,
configuration, prompt, retry, child call, tool capability, or ambient project/user skill, plugin, or MCP
dependency is `INVALID`; it is never a fallback.
Codex's executable-bound system-skill descriptors are treated separately in Section 3.2.

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
`9b01de1f550019a8bf81c23431925b6f38a173ec1ce22023c765a2a8d290cdcf`. Publication 5 treats that root as
read-only recovery input at
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\TerraBootstrap\tba-b7e5898e6389ff19b3ce34738f16b47d0a832dfc4625789fbcf4308352f2b1a0`.
Its canonical Approval-1 file SHA-256 is
`33d3e1756ed2bfd661698da3dfdf85a921380efd87fe3d635b777dafe3c6e04b`; the normalized approval-text
SHA-256 is `66df8cd413fddd097e80dc63ccfacab221e96c72c795345d14b72ae1ae3474ef`.
It may not be retried, deleted, changed, renamed, adopted as a new request, or used as authority for a
model call. Any mismatch is `PRIOR_PUBLICATION3_EVIDENCE_MISMATCH` and stops before a Publication-5
evidence root exists.

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
`893c099e299a5152f26edd912a5bfcdc75bd69e030dfd40653c0365ffe4d5e44`. Publication 5 treats every byte
under that root as read-only recovery input. It may not be retried, deleted, changed, renamed, repaired,
adopted, or used as authority for a model call. Any mismatch reports
`PRIOR_PUBLICATION4_EVIDENCE_MISMATCH` and stops before a Publication-5 evidence root exists.

Publication 5 is a replacement publication under the existing Approval-1 gate, not a third approval
gate. Its new sentence, commit, recovery-domain request ID, and evidence root create a distinct lineage.

## 3. Exact Terra execution envelope

### 3.1 Frozen host identity

Publication 5 requires:

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

Every Goal-NP implementation or review process uses the same base argument vector. The controller
creates a fresh request-owned, instruction-free per-call launch directory outside every Git owner,
uses it as `--cd`, and grants only the exact owner worktree through `--add-dir`. The implementation
root is empty; the review root contains only its hash-bound candidate/test input packet. Neither may
contain discovery/config bytes. This prevents owner `.agents/skills` and project instructions from
entering discovery while leaving the declared tree writable. Only `<sandbox>`,
`<instruction-free-launch-root>`, `<owner-worktree>`, `<result-schema>`, `<last-message-file>`, and the
schema-valid prompt change by request:

```powershell
& $CodexExe exec `
  --model gpt-5.6-terra `
  --config model_reasoning_effort=xhigh `
  --config approval_policy=never `
  --config 'project_doc_max_bytes=0' `
  --config 'project_doc_fallback_filenames=[]' `
  --config 'agents.enabled=false' `
  --config web_search=disabled `
  --sandbox <sandbox> `
  --cd <instruction-free-launch-root> `
  --add-dir <owner-worktree> `
  --skip-git-repo-check `
  --ephemeral `
  --ignore-user-config `
  --ignore-rules `
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
approval capabilities are disabled. The instruction-free launch root prevents repo-local skill discovery.
Codex's executable-bound system-skill descriptors remain visible. A process may read and follow one
only when its system trigger applies, but it confers no additional path, tool, network, model, or
write authority; repo/user skills remain absent and forbidden. The launcher copies `auth.json` into
a request-bound disposable `CODEX_HOME`, never records credential values, allows any provider refresh
only against that copy, and removes the entire disposable home before committing. A complete ordinal
whole-tree path/type/length/content manifest proves the live `CODEX_HOME` is byte-identical before and
after. The scanner refuses a root or entry reparse point, an alternate data stream, a sharing/access
error, partial enumeration, or any unreadable default stream; it never treats a partial manifest as a
baseline. Any drift or unattestable final state stops before the ADMIN commit.

Immediately before each model process, `codex debug prompt-input` runs from that process's exact
instruction-free launch root with the same disposable `CODEX_HOME`, owner grant, and config/feature
overrides. It must produce retained JSON proving that no project `AGENTS.md`,
fallback project instruction, project config, plugin, MCP server, hook, or non-system skill enters
the model-visible input. Its hash and the enumerated system-skill locator count enter the receipt.
The outer prompt names absolute publication, owner-worktree, candidate, and request-file paths.

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

### 3.4 Publication-5 zero-write readiness and process-recording boundary

`Preflight` is repeatable, advisory, and non-consuming. It invokes no Codex/model process and creates or
changes no launcher-owned repository, evidence, approval, temporary, Git-object/index, or live-home
path. Ordinary OS access metadata and telemetry are outside the launcher's control and are not claimed
as writes. `Run` does not trust an earlier result: it invokes the same in-process readiness function
again before its first filesystem mutation.

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
only read-only Git inspection and validates the exact branch, commit, clean status, six committed bundle
blobs, Codex and Python identities, canonical Publication-5 approval bytes, absent Publication-5 request
root, and frozen Publication-3 and Publication-4 evidence including each canonical approval file. It
computes the complete live-`CODEX_HOME` manifest twice and
requires the two scans to be byte-identical. It runs no temporary-index, `write-tree`, prompt-input,
test, or model operation. On PASS, `Preflight` emits only a deterministic JSON readiness record to
stdout. A failed readiness check exits nonzero, emits no PASS record, and creates no request/evidence
root.

Pre-claim quiescence or live-home failures are readiness failures, not execution attempts, and may be
checked again after the environment is made quiescent. Authority/publication mismatches fail closed.
Once `Run` exclusively creates the distinct Publication-5 request root, any failure is terminal and the
root may not be deleted, reset, or reused.

The process-recorder failure-code vocabulary is closed:
`PROCESS_START_FAILED`, `PROCESS_HANDLE_UNAVAILABLE`, `PROCESS_TIMEOUT`,
`PROCESS_EXIT_CODE_UNAVAILABLE`, `PROCESS_EXIT_NONZERO`, `PROCESS_CANARY_FAILED`,
`PRIOR_PUBLICATION4_EVIDENCE_MISMATCH`, `PRIOR_PUBLICATION3_EVIDENCE_MISMATCH`, and
`UNEXPECTED_FAILURE`. Before claim, a canary failure emits a stable nonzero failure with
`PROCESS_CANARY_FAILED` and may name one process-subset `cause_code`, but writes no state or root. After
claim, every terminal path persists `error_code`, `error_label`, and human-readable `error`; an unknown
exception maps only to `UNEXPECTED_FAILURE` and never expands authority.

## 4. First-producer and administrative sequence

The missing Codex `$build-step` is not installed, discovered, invoked, or treated as authority.
Publication 5 preserves the Publication-4 direct executor and repairs only its Windows PowerShell 5.1
process-result recorder with the precommitted
`tools/run-goal-np-terra-bootstrap.ps1` launcher and
`schemas/terra-bootstrap-result-v1.schema.json`. The launcher is part of the approved publication,
not an ADMIN output. `Preflight` implements Section 3.4 without claiming a request. `Run` independently
repeats that exact gate, then exclusively claims a new root and stores the in-memory readiness record as
`preflight.json` before any later effect. Its request identity is the lowercase SHA-256 of the canonical
UTF-8/LF payload `publication-5-recovery-v1`, final Publication-5 commit, exact Approval-1 text hash,
frozen Publication-4 request ID, frozen Publication-4 state hash, frozen Publication-3 request ID, and
frozen Publication-3 state hash, joined with one LF between fields and no final LF; the visible ID is
`tba-<digest>`. This cannot address, retry, or rehabilitate either terminal earlier lineage. The fresh evidence root is
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\TerraBootstrap\<publication-5-request-id>` and must be absent
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

After the claim, `Run` validates the closed argv, instruction-free per-call roots, frozen prompts,
result schema, output hashes, and terminal state. It rechecks process quiescence immediately before and
after prompt-input and every Codex process. After allocation, immediately before each prompt-input or
Codex process, before commit, on success, and on every catch path it revalidates live-home plus both
frozen earlier roots and canonical approval files. Read-only `Inspect` revalidates those same frozen
roots and approval files plus the exact
Publication-5 request/state identity and, for PASS, the canonical receipt path/hash/content; it bypasses
the launch quiescence gate so a later agent may inspect without acquiring execution authority. `Run` is
create-new: a crash or non-PASS after root claim leaves durable `blocked` state, and another model attempt
under that lineage is forbidden. Publication 5 then proceeds:

1. After recovery Approval 1, the operator copies the command block, closes this Codex/VS Code and every
   other Codex, ChatGPT, Cursor, IDE-agent, and Claude session, then opens standalone ordinary Windows
   PowerShell. No coordinator model invokes the launcher. The operator runs `Preflight`; only a PASS
   permits `Run`, which repeats the same gate. Reopening or continuing an agent before `Run` exits makes
   the ancestry non-quiescent and must be refused. The frozen implementation prompt allows only the base
   plan's closed 15-path ADMIN Files set and uses the committed result schema.
2. After the new root is claimed, the launcher records the readiness proof, then before review validates
   every ADMIN output and the exact 661-byte requirements lock;
   validates CPython `3.14.3` and executable SHA-256
   `cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b`; creates a request-owned
   venv/cache/temp tree; installs only `--require-hashes --only-binary=:all:` dependencies; runs the
   focused ADMIN tests and full root tests with contained pytest cache; and seals a temporary-index
   candidate tree, binary diff, `git diff --cached --check`, closed path set, and all result hashes.
3. The fresh read-only Terra review receives the exact base tree, candidate tree/diff, absolute plan
   paths, implementation JSONL hash, and deterministic test receipts. It cannot edit. `PASS` with a
   blocker or significant finding is rejected by the deterministic launcher even though the shared
   Structured-Outputs-compatible result schema permits those severities for non-PASS responses.
4. The launcher revalidates live-home, frozen Publication-3 and Publication-4 evidence, and Git identity,
   stages exactly
   the reviewed candidate tree,
   creates the fixed ADMIN commit only after every gate passes, and seals immutable implementation/
   review evidence. Neither model process commits, updates an issue, or writes external State.
5. The committed `bootstrap-goal-np-approval.ps1 -Action Prepare` records the exact revised sentence,
   six-file publication hashes, amended executor identity, ADMIN commit/evidence, and all existing
   Approval-1 fields.
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
Publication-5 commit/hashes and frozen Publication-3/Publication-4 recovery evidence, `terra-direct-v1`, Codex
version/executable hash/base argv, prompt/schema
hashes, requested identity plus reported-identity status/value when available, call IDs, parent/round, stdout/stderr/last-message hashes, and
the deterministic gate/commit/CAS/finalizer/issue/status lineage. Stale Publication-2 Claude executor
fields or mixed Claude/Terra implementation attempts are invalid. References to the product's native
Claude or Codex package tests are not stale implementation attempts.

## 6. External transition handoff

The following is an immutable template, not a publication blob that contains its own hash. After the
Publication-5 commit and exact-byte reviews exist, the publisher generates a separate handoff under
`%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication5\terra-transition-handoff-<publication-5-commit>.txt`
by substituting only the named Publication-5 placeholders, then hashes and gives it to the operator.
Neither the commit nor this amendment embeds its own digest. Do not create the Publication-5 approval
file, run the launcher, or start Codex before recovery Approval 1. The operator must copy the launch
block, close the active Codex/IDE UI, and execute it in standalone Windows PowerShell; replying to or
reopening an agent before `Run` exits recreates forbidden ancestry. After `Run` exits, `Inspect` may be
invoked from a reopened session. No coordinator model may add a call.

```text
Goal NP Publication 5 — Terra bootstrap process-recording recovery handoff

Version: publication-5-recovery-v1
Status: AWAITING RECOVERY APPROVAL 1

This handoff is operator guidance only. Reading, copying, or hashing it does not grant Approval 1.
Do not create the Publication-5 approval message, run Preflight, invoke Terra, or start any Goal-NP
implementation until Abraham supplies the exact approval sentence below in a new message.

EXACT RECOVERY APPROVAL-1 SENTENCE

Approve Goal NP plan Publication 5 with D01-D10 and the Terra bootstrap process-recording recovery amendment.

The approval file must contain only that sentence as UTF-8 without BOM plus exactly one final LF.
Canonical future path:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\Publication5\approval1-message.txt
Trimmed text SHA-256: 2d19ad716f3179baf67c67c77d19dfb29697ea5b2e6f2b0a0d1fe87ee03d0f47
LF-terminated file SHA-256: 5ad7472cb113d6965de18204dc1b7f860a0c2982ad1e8152e34547efa714a8e3

PUBLICATION-5 AUTHORITY

Worktree: %LOCALAPPDATA%\SkillMesh\Worktrees\native-codex-skill-parity-plan
Branch: plan/native-codex-skill-parity
Commit: <publication-5-commit>

Six-file bundle:
- plan.md
  SHA-256: <publication-5-plan-sha256>
- documentation/native-claude-codex-skill-parity-plan.md
  SHA-256: <publication-5-base-plan-sha256>
- documentation/native-claude-codex-skill-parity-terra-amendment.md
  SHA-256: <publication-5-terra-amendment-sha256>
- documentation/native-claude-codex-skill-parity-proposal.html
  SHA-256: <publication-5-proposal-sha256>
- tools/run-goal-np-terra-bootstrap.ps1
  SHA-256: <publication-5-terra-launcher-sha256>
- schemas/terra-bootstrap-result-v1.schema.json
  SHA-256: <publication-5-terra-result-schema-sha256>

Ordered publication gates on those exact bytes:
1. plan-review: <publication-5-plan-review-verdict>
2. plan-redline: <publication-5-plan-redline-verdict>
3. plan-wrap: <publication-5-plan-wrap-verdict>

Publication 5 keeps D01-D10, D08, the 41-step Goal-NP DAG, the two native qualification profiles,
the unchanged direct Terra/xhigh model and call envelope, and the Approval-2/live-cutover prohibition.
It changes only process-exit recording at the two production child-process sites and adds the
pre-claim, zero-write cmd.exe exit-0/exit-37 canary.

Start read-only. Verify the exact worktree, branch, HEAD, clean status, all six hashes, Codex CLI
0.147.0, native executable SHA-256 935a1911ed2556e4ffcec995f4886ac2ac425863ba26fed264df62e30272ad9d,
and Terra/xhigh availability. Verify both frozen prior evidence roots and approval files exactly. Do not
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

FRESH PUBLICATION-5 LINEAGE

Request domain: publication-5-recovery-v1
Expected request ID: <publication-5-request-id>
Expected fresh evidence root:
%LOCALAPPDATA%\SkillMesh\Evidence\GoalNP\TerraBootstrap\<publication-5-request-id>

The request digest is SHA-256 over exactly seven UTF-8 fields joined by one LF with no final LF:
the domain above, Publication-5 commit, normalized Publication-5 approval-text hash, frozen P4 request
ID, frozen P4 state hash, frozen P3 request ID, and frozen P3 state hash. The root must be absent before
claim. Preflight and Run revalidate both earlier roots byte-for-byte. Once Run claims the P5 root, every
failure is terminal; never retry, delete, alter, rename, reuse, or adopt it.

OPERATOR BOUNDARY AFTER THE EXACT APPROVAL IS SUPPLIED

1. While this handoff is visible, copy the full PowerShell block below.
2. Close this Codex/VS Code UI and every other Code, Codex, Claude, ChatGPT, Cursor, or IDE-agent
   process. Do not ask a model or tool to launch the block.
3. Open a new ordinary standalone Windows PowerShell 5.1 window.
4. Paste and run the block there. Do not reply `closed; continue` before Run exits; doing so recreates
   the forbidden agent ancestry.
5. Preflight is repeatable and non-consuming. It exercises the pinned cmd.exe exit-code canary and must
   PASS before Run. Run independently repeats every check, then creates exactly one Publication-5
   lineage. Any post-claim failure is terminal.
6. Inspect is read-only and may also be run after reopening a session once Run has exited.

$repoRoot = Join-Path $env:LOCALAPPDATA 'SkillMesh\Worktrees\native-codex-skill-parity-plan'
Set-Location -LiteralPath $repoRoot

$approvedCommit = '<publication-5-commit>'
$expectedRequestId = '<publication-5-request-id>'
$approvalMessage = 'Approve Goal NP plan Publication 5 with D01-D10 and the Terra bootstrap process-recording recovery amendment.'
$approvalMessageFile = Join-Path $env:LOCALAPPDATA 'SkillMesh\Evidence\GoalNP\Publication5\approval1-message.txt'
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
        throw 'The canonical Publication-5 approval path exists but is not a file; do not continue.'
    }
    $existingApprovalBytes = [System.IO.File]::ReadAllBytes($approvalMessageFile)
    if ([Convert]::ToBase64String($existingApprovalBytes) -cne [Convert]::ToBase64String($approvalMessageBytes)) {
        throw 'Existing Publication-5 approval message is not byte-identical; do not continue.'
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
    throw 'Publication-5 readiness preflight did not PASS. Resolve only the reported read-only readiness condition, then rerun Preflight; no Run attempt was created.'
}
$preflight = ConvertFrom-TerminalJson -ProcessOutput $preflightOutput -Label 'Publication-5 Preflight'
if ($preflight.verdict -cne 'PASS' -or
    $preflight.approved_commit -cne $approvedCommit -or
    $preflight.request_id -cne $expectedRequestId -or
    $preflight.evidence_root_absent -ne $true) {
    throw 'Publication-5 readiness output is not the exact PASS contract; do not start Run.'
}
$preflight | ConvertTo-Json -Depth 12

$terraRunOutput = @(& powershell.exe @launcherArgs -Action Run)
$terraRunExit = $LASTEXITCODE
if ($terraRunExit -ne 0) {
    throw 'Terra ADMIN bootstrap failed. This Publication-5 Run lineage is terminal; do not retry or delete its evidence.'
}
$terraRun = ConvertFrom-TerminalJson -ProcessOutput $terraRunOutput -Label 'Publication-5 Run'
if ($terraRun.verdict -cne 'PASS' -or $terraRun.admin_commit -notmatch '^[0-9a-f]{40}$') {
    throw 'Terra ADMIN bootstrap did not return its exact PASS contract; do not continue.'
}
$terraRun | ConvertTo-Json -Depth 12

$terraStateOutput = @(& powershell.exe @launcherArgs -Action Inspect)
$terraStateExit = $LASTEXITCODE
if ($terraStateExit -ne 0) {
    throw 'Terra ADMIN bootstrap inspection failed; do not continue.'
}
$terraState = ConvertFrom-TerminalJson -ProcessOutput $terraStateOutput -Label 'Publication-5 Inspect'
if ($terraState.phase -cne 'pass' -or
    $terraState.approved_commit -cne $approvedCommit -or
    $terraState.request_id -cne $expectedRequestId -or
    $terraState.admin_commit -cne $terraRun.admin_commit) {
    throw 'Terra ADMIN bootstrap state is not the exact PASS lineage; do not continue.'
}
$terraState | ConvertTo-Json -Depth 12

AFTER TERRA ADMIN PASS

For ADMIN-BOOTSTRAP and the 39 Type-code implementation/review model slots, use only Publication 5's
terra-direct-v1 process envelope. In those implementation/orchestration slots, do not invoke a missing
$build-step, Claude, /repo-sync, $repo-sync, a router, a repo/user skill, a plugin, MCP, hook, memory,
fallback model, or unlisted helper. This prohibition does not suppress the unchanged base-plan-authorized
Claude native-session qualification/evaluation calls in operator NP-12 and NP-40 or the D08 mixed-family
cells; those calls remain confined to their exact plan-defined profiles, gates, and evidence contracts.
Run the one-attempt ADMIN implementation and independent read-only review; accept executable-bound
system-skill instructions only when their system trigger applies and never as added authority;
independently verify its tests/path/diff gates; create only the reviewed ADMIN commit. Then pass the
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
repeatable `Preflight` owns no Codex/model call or request; its only children are the two fixed
process-result canary calls. Create-new `Run` owns the first model call and refuses to claim its evidence
root before the exact recovery sentence and zero-write readiness gate pass.

## 7. Review and publication gate

Before this amendment can be offered for recovery Approval 1:

1. `git diff --check` passes;
2. the base plan's 41 steps, fields, flags, DAG, D08 counts, and Approval-2 boundary remain unchanged;
3. every Publication-2/3/4 implementation-executor reference is either explicitly superseded here,
   retained as frozen recovery evidence, or remains clearly a product/native-qualification reference;
4. plan-review and plan-redline return PASS, then plan-wrap returns READY, in that order on the exact
   six-file bundle;
5. start/end SHA-256 is identical for every exact-byte review; and
6. the publisher creates the external handoff with the final commit and six hashes without changing
   any publication blob.
