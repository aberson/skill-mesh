# Step 65 — retire authorization: decision brief for independent review

**Status:** APPROVED BY THE OPERATOR (2026-08-12) AND IMPLEMENTED; STEP 65 DONE (2026-08-13). The
Dev Observatory / On Brand UAT hold cleared on 2026-08-12. Completion still does not authorize an
early live install or Step 71 cut-over; the installer authority prerequisite remains blocking.
**Date:** 2026-08-12 · **Completed:** 2026-08-13 · **Issue:** #96 · **Implementation:** current
`main` worktree, derived from parked branch `build-step-1786408322` (`b0651be`)
**Line references** record the reviewed branch at the time each finding was written; confirm current
function names and locations before relying on one.

This document is written to be **disagreed with**. It exists because three candidate designs were
proposed and falsified in one session, two of them by the same author who is now recommending the
fourth. Treat the recommendation as the weakest part of this document and the measurements as the
strongest.

Values are named by **class and location only**, never by literal, per this repository's standing
disclosure discipline.

---

## 1. What I want the reviewer to attack

In priority order. Everything else in this document is context for these five.

1. **Is "stop deleting" an admission of defeat dressed as a design?** The recommendation removes a
   capability rather than making it correct. Argue that a correct authorization exists and was
   missed.
2. **§8's scope challenge.** Install-overwrite is gated on the *same forgeable signal* as the
   deletion this step is fixing. If that is a real sibling defect, fixing retire alone may be the
   wrong scope for Step 65 — or may be right, but only with the sibling recorded.
3. **The accepted regression.** After this change, *no test exercises a loop-2 retire at all*.
   Is that tolerable, or does it need a compensating gate?
4. **Did the falsifications actually falsify?** Each is a measurement (§5). If any measurement is
   wrong, its design may still be alive.
5. **Is there a fifth option nobody proposed?** Four were considered. The space was not proven
   exhausted.

---

## 2. The system, in brief

`tools/migrate-legacy-install.ps1` migrates a consumer's skill directories to a current layout. It
plans a set of typed actions (install / preserve / retire / backup / ledger) in `New-MigrationPlan`,
then applies them transactionally.

Two project discovery roots are live installation targets: `<home>/.claude/skills` (Claude) and
`<home>/.github/skills` (GPT). A third *project-relative* path,
`<project-home>/.copilot/skills`, is **retired** — no profile installs into it and no host reads it.
That statement does not generalize to an arbitrary `-Home`: `<actual-user-home>/.copilot/skills` is
Copilot's active personal discovery root. The working implementation now prefers the explicit
`-ProjectRoot` spelling (`-Home` remains a compatibility alias) and fails closed when that root is
the effective personal home; §6.1 records the implementation and its still-pending acceptance.

Every file skill-mesh generates carries a provenance marker in its own bytes
(`tools/skill-mesh-provenance.ps1`). The architecture's stated authority model
(`tools/install-skill-mesh.ps1:26-42`, verbatim):

> OWNERSHIP AUTHORITY = FILE-CONTENT PROVENANCE, NOT THE LEDGER. […] The marker is the SAFETY gate
> ("ours to touch?"); the ledger is only the SCOPING hint ("which marker file is this provider's").

**That sentence is the root of this problem.** The marker answers *"do these bytes look like ours?"*
The destructive operations need *"did we write this?"* Those are different questions, and the
architecture treats them as one.

### How a file gets classified

`Get-DirEligibility` (`migrate-legacy-install.ps1:546-562`) classifies by **directory name only**:

- name is in the manifest → `managed`
- name is `_shared` and holds no `SKILL.md` → `shared-payload`
- holds a `SKILL.md` → `consumer-only` (fully protected)
- otherwise → `foreign` (blocks the run)

Then `Get-RootScan` (`:733-741`):

```powershell
$isOurs = $(if ($eligibility -eq 'managed') {
    $true                                              # <-- unconditional, any depth
} elseif ($eligibility -eq 'shared-payload') {
    Test-SharedFileIsOurs $rel $sharedInstallRels      # <-- per-file
} else { $false })
```

**Every file at any depth under a manifest-named directory is marked ours unconditionally**, with no
content and no dist check. Per-file classification exists *only* for `_shared`.

### The retire set

Built in two loops (`:904-918`):

- **Loop 1** over `$retiredManaged` — files under the retired `.copilot/skills` root.
- **Loop 2** over `$managedRels`, opening with `if ($installRels.Contains($rel)) { continue }` — so
  it only ever considers paths the **current distribution does not emit**. Its purpose is retiring
  superseded generated files.

Both authorize deletion on `Test-FileHasMarker` and nothing else.

---

## 3. The defect

`Test-SkillMeshHeaderPreamble` accepts an empty preamble, YAML frontmatter, or any ≤256-char prefix
ending in a fence line. A consumer document that merely **quotes** the generated header therefore
classifies as owned.

An adversarial verifier ran `-Apply` against a throwaway home and **deleted three consumer-authored
files, exit code 0**, via three different acceptance branches (frontmatter prefix, file-top, inside a
fenced block). The step's own regression test was green throughout: it rejects only its own fixture's
shape.

Two prior iterations each expanded the predicate as a deletion heuristic; each produced a new
escape. The **same-defect rule** therefore forbids a third heuristic expansion and, most
importantly, forbids treating the parser's answer as deletion authority. The implementation does
make one shared-parser correctness repair: YAML frontmatter ends at the emitter's first closing
delimiter, so a later Markdown rule cannot retroactively make a quoted header emitter-valid. That
narrows generated-candidate recognition; it does not restore destructive authority to loop 2.

### Correcting a natural assumption

The obvious reading — "this is a `_shared/` problem, since that directory holds both populations" —
**is wrong**, and cost this session a full design round. `_shared/` is the *better*-protected surface:
`Test-SharedFileIsOurs` (`:604-617`) already requires dist-membership OR marker at scan time. The
exposed population is consumer files inside **any manifest-named skill directory** — e.g. a note or a
customised copy at `<root>/<manifest-skill>/<anything>` — which reach loop 2 with the marker as their
first and only content test.

---

## 4. The constraint that outranks the fix

From the step: all 211 emitted files currently read owned across LF/CRLF/BOM variants, across 27 call
sites, with zero flips. **Any change that strands a real payload file is strictly worse than the
defect it replaces.**

Note this is satisfied structurally by every retire-side option: the install set is built by walking
the supplied dist with no input from the marker predicate, the retire set, or the ledger, and retire
is delete-only. No retire-side policy can change which files are emitted or overwritten. A retire
that declines leaves a superseded file behind; it cannot strand a payload file.

---

## 5. Four designs, and the measurement that killed each

### 5.1 Dist-membership as loop 2's second yes — FALSIFIED

*Retire only if the marker holds AND the path is in the current dist.*

Loop 2's first statement is `if ($installRels.Contains($rel)) { continue }`. Every path it considers
is by construction **not** in the dist, so the conjunct is never satisfiable: loop 2 becomes dead
code and superseded files accumulate. The file's own disclosure comment (`:920-926`) already said so
— inside `_shared` the call is "decided purely by the file's own CONTENT … the dist ships neither
answer for a path it does not emit."

Additionally, three currently-green tests lock marker-only retirement of non-dist paths.

### 5.2 Manifest "orphaned profile entry" rule — FALSIFIED

*Retire an entry the manifest says should not exist for that provider.*

Measured against `config/skill-manifest.json` and `tools/build-distributions.ps1`
("GPT profile excludes provider-native skills entirely"):

- Every skill has a Claude adapter → **the rule is a total no-op under `.claude/skills`**, the root
  where the deletion reproduced. Zero cleanup where the bug is.
- Its only firing domain is the three `core: null` provider-native names under the GPT root — which
  the builder never emits there. So **every entry the rule can fire on is consumer-placed by
  construction.** It would delete a consumer's hand-copied Copilot tree, with **zero forgery**
  (the bytes are genuinely skill-mesh's), precisely *because* the manifest declines to ship it —
  which is the consumer's reason for creating it.

### 5.3 Bulk-moving the marker-less population into `preserve` — FALSIFIED

*Proposed as an audit-gap closure: a non-marker consumer file in a managed dir currently lands in no
action set at all — untouched, but unaudited.*

The gap is real. The remedy is not. `preserve` actions are hashed and verified, not audit-only:
`Test-Preconditions` is kind-uniform, so drift on **any** action fires `PRECONDITION_DRIFT` with
nothing written, and a `Test-PostInstall` mismatch triggers rollback that can escalate to
`failed_incomplete` — the state Step 48's review found `-Resume` and `-Rollback` both *refuse*.

The live population is ~6,669 files under manifest-named directories, including `.pyc`, `.log` and
`.db`. **One background test run regenerating a `.pyc` between plan and apply would abort the
migration.** Plan-time hashing is also unguarded, so a throw there is terminating.

### 5.4 Ledger membership as loop 2's second yes — FALSIFIED

Three independent kills:

1. **Not in scope.** The migrator's only prior-ledger read is `Get-PriorCreatedDirs`, called *after*
   `$retires` is frozen, and it projects `created_dirs` only. **`owned_files` is never read anywhere
   in this tool.** (Hoistable in principle — this alone is not fatal.)
2. **Not a second axis — the decisive one.** Measured on the live home: marker-bearing and
   ledger-owned coincide **exactly** over the reachable population (99/99 Claude, 96/96 GPT; zero
   divergence in either direction). Both answer *"did skill-mesh ever write this path?"*; neither
   asks *"are the current bytes ours?"* So a consumer who **customises an installed skill** — edits
   the body, keeps the generated header — passes **both gates**. That is the reproduced deletion
   class, un-closed, and it is the most likely provenance of a consumer file inside a skill
   directory. Gating on the ledger also inverts the tool's own stated precedent (§2): it promotes
   the signal the architecture calls a *hint* into a *gate*.
3. **Vacuous on the primary target.** The legacy user-profile home carries 58 skill directories and
   **no ledger** — exactly the population this tool exists to migrate. There it degrades to option
   5.5 anyway, while still turning the same three tests red.

### 5.5 Narrow the consequence — SURVIVING

*Loop 1 unchanged. Loop 2 never deletes; each candidate becomes a named advisory.*

Not falsified by any lens applied. Its costs are real and stated in §7.

---

## 6. The recommendation

- **Loop 1: unchanged in consequence, narrowed in authority.** Its second yes is genuine and
  content-independent only when the bytes canonically reside under the retired *project-relative*
  `.copilot/skills` root, are not reachable through an active discovery alias, and `-Home` is not
  turning that spelling into Copilot's personal root. A manifest-named tree satisfying all of those
  conditions is evidence of a pre-retarget skill-mesh install. Position carries real information
  only inside that proven domain.
- **Loop 2: never deletes.** Candidates are reported as named advisories the operator acts on.
- **Header recognition remains anchored and bounded.** This implementation does touch the shared
  provenance parser: it factors the validated preamble/span so the inspector can read metadata
  only from the owned header block, and it re-measures every generated file through that parser.
  `Test-FileHasMarker` continues to delegate to the single parser rather than inventing a second
  marker rule.

The reasoning in one line: **loop 2 has no non-forgeable signal available to it, so it must not hold
a destructive privilege.** Loop 1 does have one, so it keeps its privilege.

### 6.1 Implementation review findings — acceptance obligations, not a DONE claim

The current working implementation has incorporated the following findings from adversarial review:

1. **Canonical residence, not lexical reachability from the retired name.** `Get-RootScan` records
   the contained canonical file path. A junction under or at `.copilot/skills` that resolves into an
   active tree cannot smuggle that active file into loop 1; it is routed to loop 2's retained,
   advisory-only population.
2. **No active host path may reach the retired bytes.** Even a file physically under the retired
   root loses positional deletion authority if it is reachable through `.claude/skills`,
   `.github/skills`, or `.agents/skills`. The working guard checks whole-root and nested aliases and
   is repeated at plan precondition, forward retire mutation, resume-skip, and current-plan undo
   boundaries. That repeat is load-bearing: an alias may change after the
   plan or during an interrupted transaction. Undo's narrow restoration exception is item 6 below.
3. **A plan hash is file identity, not path-kind identity.** One recorded-file predicate is now
   shared by Apply preconditions, forward mutation, resume classification, and rollback. A null hash
   means true nonexistence, never a directory, non-file, unreadable file, or hash failure. The retire
   resume classifier accepts only pre/absent, pre/pre, or absent/pre target/payload pairs; every
   ambiguous pair is refused before another mutation.
4. **The project-root premise is enforced.** The command prefers `-ProjectRoot` while retaining
   `-Home` as a compatibility alias. Planning, Apply, and Resume fail closed with
   `PERSONAL_HOME_UNSUPPORTED` when that root resolves to the effective personal home. Rollback is
   deliberately exempt so an older transaction can still put verified personal bytes back.
5. **Recovery includes work begun by an earlier process without laundering observations into
   ownership.** Resume and explicit Rollback derive the reverse-order undo set only from durable
   `begin` history. A commit-only record is observational compatibility history: Resume may use it
   to recognize matching post-state bytes, but it never manufactures a `begin`, never enters the
   undo set, and never grants permission to delete or overwrite those bytes. Byte-identical
   pre/post actions are true no-ops under the same rule.
6. **Rollback's one retired-domain exception is restorative, not destructive.** Resume and forward
   retire still require the narrowed retired domain. Undo permits a hash-verified legacy-v1 retire
   payload to return only to a truly absent, home-contained target whose canonical home-relative
   spelling still equals its recorded path. A new junction cannot redirect that compatibility
   restore. This cannot confer new delete authority; it preserves unaliased recovery for
   transactions created before Step 65 narrowed the rule.
7. **Empty directories are not durable property.** Rollback no longer removes empty
   plan-time-created directories, and forward retirement no longer cosmetically removes emptied
   retired ancestors: an operator may have created an empty replacement during an interruption,
   and no byte hash can distinguish it. Verified file pre-images are still restored and verified
   created files removed.
8. **Recovery authority is bound and fail-closed.** Plan, backup manifest, and journal schema,
   transaction identity, action ordering, paths, providers, hashes, payloads, and record/action
   correspondence are validated before recovery mutation. Missing, malformed, non-file, truncated,
   or inconsistent authority artifacts refuse recovery. A bare Apply also refuses an ambiguous or
   corrupt prior transaction instead of layering a new transaction over it. Explicit Resume applies
   the same validation before calling `applied` a no-op or refusing `rolled_back` as resolved; a
   terminal label alone never earns either response.
9. **`applied` follows acceptance, not merely the action loop.** The engine leaves the durable
   state at `applying` until cross-action post-install verification succeeds. A crash in that window
   therefore resumes the verification path. Explicit Rollback is intentionally independent of the
   current checkout manifest so valid retained payloads remain usable if planning metadata changes.
10. **Canonical roots are explicit, and legacy ambiguity refuses.** New schema-v1 plan/manifest
    pairs carry `root_encoding: canonical-realpath.v1` and repeat their canonical project and backup
    roots. Older schema-v1 artifacts omitted that discriminator. They remain automatically
    recoverable only when their recorded spellings were already canonical; alias-spelled legacy
    artifacts fail closed with `LEGACY_ALIAS_ROOT_UNSUPPORTED` rather than silently redirecting
    historical journal authority through a replacement junction.
11. **Rollback completion is durable before its terminal label.** After every action carrying
    durable `begin` authority has been undone and verified, the engine revalidates the exact plan,
    complete journal, and candidate begin set under the existing journal writer handle, then
    appends and flushes one final transaction-level `rollback_complete` record whose `begun_seqs`
    is that exact set; only then does it publish `rolled_back`. History that becomes missing,
    truncated, damaged, or inconsistent during undo may be best-effort reversed from already
    validated in-memory authority, but it cannot be certified with either the completion record or
    `rolled_back`. If a process stops between the successful record flush and status write, explicit
    Rollback validates the record and publishes the status without replaying any inverse. A current
    `rolled_back` transaction with that record remains resolved despite legitimate later consumer
    edits. Markerless legacy `rolled_back` history uses the conservative exact-pre-state fallback,
    while `failed_incomplete` never carries a valid completion record. A `rolling_back` retry
    without the record idempotently continues reverse-order undo, accepting an inverse already at
    exact pre-state but refusing ambiguous or changed bytes. Status publication is write-first and
    read-verified: if publishing `failed_incomplete` fails, the engine retains and reports the last
    verified status rather than claiming a terminal label that never persisted.

These review findings are implemented and Step 65 is **DONE (2026-08-13)**. The authoritative
repo-root `python -m pytest` gate completed with **1,143 passed, 1 skipped, 1,144 collected in
3,443.99s (0:57:23), exit 0**; focused regressions and adversarial review also passed. The Step 4
installer-authority prerequisite and Steps 70–71 remain blocked and outside Step 65's completed
scope.

---

## 7. Costs — stated, not discovered later

1. **Three currently-green tests must be rewritten** to assert an advisory instead of a retire:
   `test_stale_generated_file_is_retired_not_blocked`,
   `test_a_marker_bearing_shared_asset_the_dist_no_longer_ships_is_retired`, and the third named in
   the round-2 record. This is a **deliberate recorded behaviour change**, not a codifying test edit
   — the distinction this repository has been burned by before, and the reason sign-off was sought
   rather than assumed. The operator approved that behavior change on 2026-08-12.
2. **After the rewrite, no test exercises a loop-2 retire at all.** Every remaining retire assertion
   rides loop 1. A future regression in the loop-2 population becomes invisible. *This is the
   strongest argument against the recommendation and it has no answer in the current proposal.*
3. **Hygiene stops converging.** Superseded generated files accumulate in the live discovery tree
   until an operator acts on an advisory. Mitigating fact, not verified for every shape: a leftover
   under `_shared/` cannot be discovered as a skill, so it is inert clutter rather than a phantom
   skill. A leftover directly under a manifest-named entry may be a different matter and should be
   checked against Step 70's no-orphan clause.

---

## 8. Scope challenge: the sibling defect

**The installer has four destructive siblings gated by the same forgeable signal.** The ordinary
overwrite gate is at `install-skill-mesh.ps1:808-812`:

> FOREIGN = target exists AND its content does NOT bear the marker. The ledger is NOT consulted here
> (a poisoned ledger cannot launder a foreign file into "owned").

A target that *does* bear the marker is therefore **not foreign**, so it is overwritten on a routine
install — **no `-Force` required**. A consumer document that quotes the generated header inside a
manifest-named skill directory is silently overwritten by an ordinary install, with no migration
involved at all.

The comment shows the intent: prevent a poisoned *ledger* laundering a foreign file. But the *marker*
is the forgeable signal, and it alone is trusted here. A repo-wide destructive-call-site audit found
three further siblings in the same installer: stale removal after a successful install, normal
uninstall, and corrupt-ledger fallback uninstall. Stale removal and normal uninstall add ledger
listing as a path-scoping signal, but neither verifies that the current bytes still match what
skill-mesh installed; a consumer customization that retains the valid header therefore passes both.
Corrupt-ledger fallback has lost even that scoping signal and deletes every marker-bearing file it
finds under the provider root. The affected class is consequently **overwrite + stale delete +
normal uninstall + corrupt-ledger marker fallback**, not overwrite alone.

This means the defect Step 65 is fixing is **one instance of an architectural assumption**, and
plausibly not the most reachable one. Under this repository's own rule — *when fixing one drift
instance, audit for siblings* — the reviewer should decide:

- Does Step 65 stay scoped to retire, with the sibling filed separately?
- Or is the correct unit of work the authority model itself?

**Verified 2026-08-12 — distinct real blocker, deferred from Step 65 but mandatory before live
work.** In a fresh throwaway home, a real generated `dist/claude/plan-review/SKILL.md` was copied to
the install target and given an appended consumer customization without removing its valid header.
An ordinary Claude install — no force flag and no backup option — exited 0, changed the target hash
from `2fe5647b843a27747e2684878d702b74e9c5235255249ea051c9f43b4a8973b0` to the exact dist hash
`1d45cb26d3ee868d5bc2d1dd60659b086b08d35ad5d83c3303d239f14bf9e7a0`, removed the consumer
text, and produced zero take-ownership backup manifests. The throwaway tree was removed after the
measurement. That is data loss without a backup.

Step 65 stays scoped to migration retirement: expanding it into the installer's authority model
would silently change four destructive installer paths whose ledger schema, partial-install
recovery, uninstall behavior, corrupt-ledger recovery, and upgrade behavior need their own design.
But this finding is a **PRE-LIVE PREREQUISITE**: Steps 70
and 71, and any live install, are blocked until the installer defect is fixed and regression-tested.
The smallest sound direction is current-byte identity, not another marker parser: persist the hash
of each installed file in the ledger and allow a routine overwrite only when the current bytes still
match that recorded hash. A mismatch must refuse or enter an explicit backup-before-overwrite
take-ownership path. Marker plus ledger can continue to scope the candidate, but neither is proof
that its current bytes are unmodified. Because existing ledgers contain paths but no per-file hashes,
their first upgrade must fail closed or require explicit backed-up adoption rather than silently
blessing the bytes found at the path. The same current-byte identity rule must gate stale removal and
normal uninstall. Corrupt-ledger fallback cannot prove identity from a missing ledger at all, so it
must fail closed on deletion or first create an explicit recoverable/quarantined backup rather than
using the marker as sole delete authority.

---

## 9. What would change the recommendation

- A demonstrated non-forgeable signal available to loop 2 at plan time. None was found; the space was
  not proven empty.
- Evidence that leftover superseded files are host-visible (discoverable as skills) rather than inert
  — that would raise the cost of not deleting, possibly above the cost of deleting wrongly.
- A compensating gate that keeps loop-2 behaviour under test after the rewrite. This would not change
  the recommendation but would retire its worst cost.
- A finding that the sibling in §8 makes retire-only scoping incoherent.

---

## 10. Reproduce the measurements

Run from the branch under discussion. All read-only.

**Read these by line range** (given as prose rather than as shell one-liners, because a documented
command naming a script path is graded by `test_documented_script_flags_are_all_declared`, and a
pager flag on a `sed`/`grep` invocation reads to that gate as an undeclared parameter of the script
being paged):

| Claim | File | Lines |
|---|---|---|
| Classification is per-directory, then unconditional | `tools/migrate-legacy-install.ps1` | 546-562, then 733-741 |
| Loop 2 skips the dist by construction | `tools/migrate-legacy-install.ps1` | 904-918 |
| `_shared` is per-file protected | `tools/migrate-legacy-install.ps1` | 604-617 |
| The authority model (marker = safety, ledger = hint) | `tools/install-skill-mesh.ps1` | 26-42 |
| The sibling gate — overwrite on marker alone | `tools/install-skill-mesh.ps1` | 806-814 |
| GPT profile excludes provider-native skills | `tools/build-distributions.ps1` | at the `$isNative` guard |

Every skill has a Claude adapter — why 5.2 is a no-op on that root. Expect `0`:

```
python -c "import json;d=json.load(open('config/skill-manifest.json'));print(sum(1 for s in d['skills'] if not s.get('providers',{}).get('claude')))"
```

`owned_files` is never read by the migrator — expect matches only where the tool *writes* it:

```
python -c "print([i+1 for i,l in enumerate(open('tools/migrate-legacy-install.ps1',encoding='utf-8')) if 'owned_files' in l])"
```

---

## 11. Provenance of this document

Produced by an orchestrator plus two adversarial workflow rounds (four investigators, one designer,
six attackers) reading the code and the live home directly.

**The author's track record on this specific question, stated so the reviewer can weight the
recommendation accordingly:** the first design (5.1) was recommended confidently and retracted the
same day on reading the retire path. The second framing (that the fix could be scoped to `_shared/`)
was also wrong. The third (5.2) was produced by a designer agent and killed by measurement. The
recommendation in §6 is the fourth position taken on this question in one session.

Three of the four falsifications came from *measuring* rather than reasoning — the manifest against
the builder's exclusion, the ledger against the on-disk population, the preserve-action population
against the transaction's precondition semantics. A reviewer who wants to overturn §6 will most
likely do it the same way.
