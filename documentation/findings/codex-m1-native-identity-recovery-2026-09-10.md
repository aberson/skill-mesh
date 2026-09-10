# M1 native identity recovery

## Result

Issue synchronization is complete at proposal commit
`5bd5e5795fd3ddc20a65b9e72e80844ee8c1fa52`: umbrella #196 and M1 Steps
126/#199, 127/#204, 128/#200 and 129/#201. The eight affected issue bodies were
reread and compared with their prepared bodies; #197/#198/#202 remain OPEN and
deferred. #203 remains closed recovery/planning bookkeeping only.

The new public-only native diagnostic **STOPPED** before private qualification.
It established the four role-alias/native-ID associations and expected public
activity, then the native host rejected the observer's `thread/read` request
with RPC error `-32600`. Required corroborating child metadata was not obtained.
No native qualification or M1 implementation started. Main remains the repaired
certificate commit `380d38b82ee8f07c876e76bf789f7b235ebe0b55`; the synchronized
proposal has not been published to main.

## Correction and verification

The former audit compared callable `/root/...` aliases with native thread IDs.
The same pinned binary's regenerated `SubAgentActivityThreadItem` schema requires
both `agentPath` and `agentThreadId` in one parent activity item. The new observer
uses that paired host record, retains an explicit bijection, and checks all role,
native and observed identity sets after metadata reads and at final acceptance.
It never reconstructs the historical assignment from labels or ordering.

Twenty public-value observer controls passed, including missing, duplicate,
conflicting and ambiguous identities, unknown activity, incomplete lifecycle,
and foreign activity arriving during metadata requests or after the audit.
Independent Astra/high source review first returned NEEDS_WORK for late activity,
unbounded subprocess calls and a possible suspended-worker leak. After correction,
the reviewer returned PASS. That is source-review evidence only.

The new supervisor uses a unique run directory, frozen input hashes, a fixed
600-second public-diagnostic limit and an independent process watchdog. The
separately prepared private qualification has a 1200-second limit and was never
invoked. No old launcher, deadline or terminal evidence was reused.

## Native observations

| Observation | Result |
|---|---|
| Native executable SHA256 | `444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b` |
| Source candidate | `25b54a5f6a8e5022a66bc2e9dadcf8c95bd9ffc5` |
| Requested models | Astra/xhigh parent; four fresh Terra/high children |
| Trusted alias/native mappings | Four unique pairs from parent activity metadata |
| Child public JSON values | All four match their exact expected objects |
| Control/producer/reviewer activity | Zero tool items each; all completed |
| Caller diagnostic activity | One `commandExecution` item; completed lifecycle |
| Unknown/unmatched activity flags | Both false |
| Metadata lookup | `thread/read` rejected, RPC `-32600`; stream parse failure false |
| Terminal supervisor | Exit 1; 89.848 seconds; finished 2026-09-10T06:05:22.872969Z |
| Cleanup | Owned Job closed; supervisor, worker and app-server PIDs absent; disposable directory empty |
| Final integrity | Source unchanged; all 125 installed files and ownership ledger match; 115 bound historical files and 18 frozen native files unchanged |

The generic `launch_failed` result and false model-check fields were produced by
the runner's exception handler. They do not prove individual freshness or private
service failures. The app-server exit 124 reflects owned Job termination after
the RPC rejection; the supervisor did not exhaust its deadline. Configured model
fields are not per-turn resolved-model telemetry, and no such claim is made.

## Evidence and next prerequisite

Private evidence is retained in the proposal worktree under
`.build-step/m1-native-recovery-20260910T055044Z-3e41b1/`:

- `issue-sync-result.json`, `issues-before.json`, `issues-after.json`;
- `observer-adaptation.diff`, `public-value-tests.json`, `review-receipt.json`,
  `launch-manifest.json`;
- `public-supervisor/` and `public-identity/native-qualification-run/`;
- `terminal-evidence.json`, which binds the terminal files by SHA256;
- `checkpoint-binding.json`, which binds this coordinator's actual native
  session identity and approved checkpoint helper/schema.

The precise missing prerequisite is an authoritative native metadata path that
corroborates each observed child's direct parentage, ephemeral state and configured
Terra/high identity. The rejected request used the schema-valid fields `threadId`
and `includeTurns: false`; its error code alone does not establish the rejection's
cause. Investigate that API boundary from primary source before preparing any
new reviewed recovery. Preserve this failed diagnostic; do not relaunch its
supervisor or run private qualification past its failed public prerequisite.

Only a subsequent passing native qualification can unlock the implementation
queue; the actual executing coordinator still repeats its own required probes.
The reviewed synchronized plan must reach main through the guarded publication
path before that queue starts. Full C1-C6 acceptance remains unfinished, as do
deep and Claude acceptance. Protected worktrees and consumer builds remain parked.
