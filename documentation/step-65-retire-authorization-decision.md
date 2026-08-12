# Step 65 — retire authorization: decision brief for independent review

**Status:** RECOMMENDATION, NOT IMPLEMENTED. Awaiting review and operator sign-off.
**Date:** 2026-08-12 · **Issue:** #96 · **Branch under discussion:** `build-step-1786408322`
**Line references** are as of that branch (merged current with `main`); confirm before relying on one.

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

Two host discovery roots are live: `<home>/.claude/skills` (Claude) and `<home>/.github/skills`
(GPT). A third, `<home>/.copilot/skills`, is **retired** — no profile installs into it and no host
reads it.

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

Two prior iterations each patched the predicate; each produced a new escape. The step is therefore
under the **same-defect rule**, which forbids a third patch of `Test-SkillMeshHeaderPreamble`. The
predicate stays as it is. What is in question is *whether its answer alone may authorize deletion*.

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

- **Loop 1: unchanged.** Its second yes is genuine and content-independent — residence under the
  retired `.copilot/skills` root, a path no profile installs into and no host reads. A manifest-named
  tree there is itself evidence of a pre-retarget skill-mesh install. Position carries real
  information here.
- **Loop 2: never deletes.** Candidates are reported as named advisories the operator acts on.
- **`Test-SkillMeshHeaderPreamble` and `Test-FileHasMarker` are not touched**, per the same-defect
  rule. The 211 owned verdicts across 27 call sites are preserved by construction, not by
  re-measurement.

The reasoning in one line: **loop 2 has no non-forgeable signal available to it, so it must not hold
a destructive privilege.** Loop 1 does have one, so it keeps its privilege.

---

## 7. Costs — stated, not discovered later

1. **Three currently-green tests must be rewritten** to assert an advisory instead of a retire:
   `test_stale_generated_file_is_retired_not_blocked`,
   `test_a_marker_bearing_shared_asset_the_dist_no_longer_ships_is_retired`, and the third named in
   the round-2 record. This is a **deliberate recorded behaviour change**, not a codifying test edit
   — the distinction this repository has been burned by before, and the reason sign-off is being
   sought rather than assumed.
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

**Install-overwrite is gated on the same forgeable signal.** `install-skill-mesh.ps1:808-812`:

> FOREIGN = target exists AND its content does NOT bear the marker. The ledger is NOT consulted here
> (a poisoned ledger cannot launder a foreign file into "owned").

A target that *does* bear the marker is therefore **not foreign**, so it is overwritten on a routine
install — **no `-Force` required**. A consumer document that quotes the generated header inside a
manifest-named skill directory is silently overwritten by an ordinary install, with no migration
involved at all.

The comment shows the intent: prevent a poisoned *ledger* laundering a foreign file. But the *marker*
is the forgeable signal, and it alone is trusted here.

This means the defect Step 65 is fixing is **one instance of an architectural assumption**, and
plausibly not the most reachable one. Under this repository's own rule — *when fixing one drift
instance, audit for siblings* — the reviewer should decide:

- Does Step 65 stay scoped to retire, with the sibling filed separately?
- Or is the correct unit of work the authority model itself?

**Not verified, and material:** whether the install path backs up a marker-bearing overwrite. If it
does not, the sibling is *data loss without a backup*, which would outrank the retire defect. This
should be checked before the scope question is answered.

By the same reasoning, uninstall is the best-protected of the three destructive paths: it requires
marker **AND** ledger listing, so a consumer file quoting the header but absent from the ledger
survives.

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
