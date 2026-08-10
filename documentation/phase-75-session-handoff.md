# Phase 7.5 — session handoff (2026-08-10)

**Purpose.** Point a fresh window at Phase 7.5 without re-deriving anything. Everything below is
measured, not estimated; where a number in `host-parity-repair-plan.md` turned out wrong, the
correction is recorded here with its evidence.

**Plan:** [`host-parity-repair-plan.md`](host-parity-repair-plan.md) · **Baseline counts owner:**
[`phase-75-baseline.md`](phase-75-baseline.md) · **Umbrella issue:** #92

---

## 1. Status at a glance

| Step | Issue | State | Landed as |
|---|---|---|---|
| 62 — fix the root gate, capture a true baseline, rescue the calibration note | #93 | **DONE** | `72356fb` on `main` |
| 63 — link-resolution gate with a frozen shrink-only allowlist | #94 | **DONE** | `2efc957` on `main` |
| 64 — ship `_shared/` into both profiles | #95 | **IN REVIEW — not merged** | `bd048bf` on branch `build-step-1786367337` |
| 65–70 | #96–#101 | not started | — |
| 71 — live consumer-home cutover | #102 | not started (`Type: operator`) | — |

`main` is pushed and equals `origin/main` at `2efc957`. Branch `build-step-1786367337` is pushed.
Issues #93 and #94 are closed; #95 is open.

**The full suite is `python -m pytest` from the repository root — NOT `python -m pytest tests/`.**
That is design decision D6, and Step 62 made it true (the root-only roots were red before). The
`tests/`-scoped invocation never collects `_shared/`, `skill-iterate/scripts/`, or
`skill-eval-setup/scripts/`, so it cannot see a regression there.

Suite trajectory: **912 collected / 906 passed / 3 failed** before Step 62 → **909 passed, 3 skipped**
after Step 62 → **953 passed, 3 skipped** after Step 63. A full root run takes 32–44 minutes; run-to-run
variance on one machine is minutes, so budget for the high end.

---

## 2. Step 64 — exactly where it stands

Committed at **`bd048bf`** (branch `build-step-1786367337`, worktree still present but disposable —
the branch holds everything). Gate on that SHA:
`python -m pytest tests/distributions tests/package-integrity` → **492 passed, 2 skipped**, exit 0.

Nine files changed, 1481 insertions: `tools/build-distributions.ps1`, `tools/install-skill-mesh.ps1`,
`tools/skill-mesh-provenance.ps1`, `tools/migrate-legacy-install.ps1`, `_shared/score-skill.md`,
`tests/distributions/{test_distributions,test_legacy_migration,test_path_choke_point}.py`,
`tests/package-integrity/test_link_resolution.py`.

### 2.1 This step's stated acceptance criterion was WRONG — corrected

The plan says class (a) "shrinks to zero — all **43** anchored `_shared` entries". Measured by the
Step 63 detector: class `shared_anchored` is **56 keys — 35 profile-side + 21 canonical**.

Because D2 puts the repoint in the **builder**, it rewrites at emit time. That burns down the 35
profile keys and *cannot* touch the 21 canonical ones, since `skills/<name>/core.md` still literally
contains `../../_shared/…`. **Target is 56 → 21, not 56 → 0**, and the burn-down achieved exactly
that (`KNOWN_DANGLING` 149 → 112; class (a) 21, all canonical, 0 profile-side).

**Recorded decision:** the canonical tree is a *build input*, not a discovery root. The builder
translates at emit time and the profile-side scan is the authoritative check, so the 21 canonical
entries remain frozen as deliberate residual. The alternative — rewriting canonical sources and
creating `skills/_shared/` — is rejected: it would require deleting
`test_skill_tree.py::test_shared_dest_divergence_is_intentional`, which asserts `skills/_shared/`
does *not* exist, and would move the manifest's `global_support_assets` dest.

> **Trap.** The tempting way to make those 21 vanish is to re-root the link detector at the repo
> root. Step 63 froze that exact mutation as an attack and the gate reds on it. Do not do it.

### 2.2 What is verified good on `bd048bf`

- `link_baseline.json` digest **unchanged** (`cd786bf9…a70fb14a`) — the frozen record was not edited.
- All 37 retirements passed the gate's own retirement proof, i.e. each was a real repair or removal.
- D2 longest-token-first rewrite order; the rewrite is **not** gated on `$hasCore` (judge-motion is
  `core: null` with depth-3 refs); 80/80 emitted refs resolve; two builds byte-identical.
- The emitted `.js` is `Test-SkillMeshProvenance`-valid and `node --check`-parses.
- The migrator's +13 lines were judged minimal, forward-compatible, and not tripping D3 —
  Step 65 still owns the real reclassification.
- **Open question CLOSED — KEEP:** `build_step_verdict.py` stays co-located per skill (plus a
  `_shared/` reference copy). Collapsing would create a cross-directory runtime dependency and
  force removing it from `SHIPPED_LEAVES`, so `test_distributions.py:408-415` is unedited.

### 2.3 What remains: verify which review findings survive

Three reviewers reviewed a **stale snapshot** (see §4), so their findings must be re-checked against
`bd048bf` before merge. Spot-checks already suggest several are resolved — confirm, do not assume:

| # | Finding | Spot-check on `bd048bf` |
|---|---|---|
| F1 | No content-fidelity control — a builder shipping correctly-named, correctly-stamped **stubs** passed everything (truncating `judge-core.md` 20,800→1,681 B stayed green) | likely RESOLVED — `_canonical_shared_body` + anti-truncation test |
| F2 | Live un-repointed ref shipping in `dist/<p>/_shared/score_skill_composite.py:186`; the check scanned `.md` only | likely RESOLVED — `$BARE_SHARED_REF_RE` + `Repoint-SharedAssetReference` |
| F3 | Two closure-walk edges untested (dropping either stayed green) | partly — 3 closure tests now exist incl. an adapter-seed edge |
| F4 | `-ForceShared` scope defeated by a directory junction (clobbered a file with no `_shared` segment, adopted 8 paths into `owned_files`) | likely RESOLVED — `$safeTarget` real-path check |
| F5 | Take-ownership backup manifest overwritten by the second profile (claude rows' hashes destroyed) | likely RESOLVED — `<BackupDir>/<provider>-<run id>/` |
| F6 | `-BackupDir`-outside-home check is a string `StartsWith` a junction walks through | unverified |
| F7 | `Add-JsProvenance` displaced a hashbang; no JS parse gate | likely RESOLVED — hashbang kept on line 1, `node --check` gate skips visibly |
| F8 | Prose conversion dropped the module name `test_score_skill_absolute.py` | RESOLVED |

Full findings: `.build-step/review-{correctness,security,tests}.md` in the worktree (gitignored, so
copy them out before removing it), plus `.build-step/dev-report.md`.

**Highest-value open question for the verifier:** what is the cheapest builder edit that still ships
a *wrong* `_shared/` payload while leaving the suite green? F1 was exactly that shape.

---

## 3. Step 63's instrument — read this before touching Steps 65–70

Step 63 landed `tests/package-integrity/test_link_resolution.py` + `link_baseline.json`. It is the
measurement instrument for the rest of the phase, and it is adversarial by construction.

- **149 frozen entries / 270 occurrences**, keyed `(source, raw, form)`; `line` is deliberately
  **excluded** from the key so unrelated edits above a citation are not spurious churn.
- Six classes: `shared_anchored`, `shared_bare`, `references_anchored`, `rules_anchored`,
  `home_anchored`, and **`profile_layout`** — the sixth is not in the plan's enum.
- The plan's per-class figures are **occurrence** counts; the allowlist shrinks by **keys**.
- **`link_baseline.json` may not be edited.** It is digest-pinned by `BASELINE_SHA256` in the test
  file. Entries may **leave** `KNOWN_DANGLING`; none may enter (decision **D-63-A**).
- An entry may only leave if its disposition is **provable from the frozen record**: re-resolving its
  `source`+`raw` must now resolve, or the token must be genuinely gone. Narrowing the detector
  satisfies neither.
- **D-63-B:** the 46 legacy top-level packages are out of scope; their anchored `../_shared/`
  citations were measured to resolve today, pinned by a test so the decision reopens if that changes.
- Stated residuals: the sibling-discount class is *narrowed, not closed* (a two-sided edit that also
  destroys an unrelated citation could still evade it), and the retirement proof's live population
  was empty until Step 64 retired the first entries.

Five developer iterations were needed because two successive control designs were demonstrably
gameable — each defeated by a reviewer with a real pytest run, not an argument. Do not "simplify"
these controls without reading why they exist.

---

## 4. Process lessons from this session (these cost real time)

1. **Review a committed SHA, never the index.** The Step 64 developer staged at a checkpoint, then
   kept working ~456 more lines without re-staging. Its own reported diff stat *and* all three
   reviews therefore described a stale snapshot, and several findings were already fixed. Always
   commit first and hand reviewers the SHA.
2. **A developer prompt must require a final `git add -A` before reporting**, for the same reason.
3. **Give each reviewer an isolated copy.** Five reviewers sharing one worktree corrupted it twice;
   one nearly got a probe file staged at a real discovery path (the #83–#86 phantom-skill class).
   `git archive <sha> | tar x` into a temp dir works well.
4. **Sub-agents must not return while their own gate is still running.** One returned an interim
   result with background runs in flight; those runs died with its turn and nothing had been measured.
5. **Gate scope.** Iterate on subsets, but the gate that flips a step DONE runs the FULL root suite.
   Running the full suite both in-worktree *and* post-merge roughly doubles cost for little gain —
   prefer a targeted subset in-worktree and the full suite post-merge, which tests the merged tree.
6. **`--max-iter` is a knob, not a gate.** It was extended 3→4→5 on Step 63 because findings were new
   and distinct each round (not reversals) and blocking counts fell monotonically. When round N+1
   blocks what round N demanded, that is oscillation: stop patching and write the decision.

---

## 5. Resume instructions

Run in: **fresh window @ `skill-mesh`** · Model: **Opus** (the plan pins Opus for all steps; dev arms
inherit the session tier)

Step 64 is committed but **not merged**. Finish it by verifying §2.3 against `bd048bf`, then merge to
`main`, run the full root gate, mark `Status: DONE` in the plan, and close #95.

```
git fetch origin && git checkout build-step-1786367337
```

```
python -m pytest tests/distributions tests/package-integrity
```

To continue the phase after Step 64 merges:

```
/build-phase --plan documentation/host-parity-repair-plan.md --resume 65
```

**Stop before Step 71** (#102) — it is `Type: operator`, a live consumer-home cutover, and is an
operator handoff rather than agent work.

### Worktrees

Two build-step worktrees exist.

**Keep `build-step-1786367337` until Step 64 merges.** Every *tracked* byte is safe on the pushed
branch, but the four review artefacts — `.build-step/dev-report.md` and
`.build-step/review-{correctness,security,tests}.md` — are **gitignored and exist nowhere else**.
They carry the reproduction steps for findings F1–F8 in §2.3. Removing the worktree destroys them
and the next window would have to re-derive the reviews from scratch. Copy them somewhere outside
the repository first if you do want to remove it (they contain machine-local paths, so they must not
be committed).

`build-step-1785890195` predates this session (the abandoned Step 47 branch) and is not Phase 7.5
work — it can be removed independently.

---

## 6. Work landed in other repositories this session

Neither is Phase 7.5, both are pushed, and both are recorded here only so a fresh window is not
surprised by them.

- **Alpha4Gate** — replaced the README's "The self-play arena" ASCII block with a light/dark
  `<picture>` diagram, plus the verification record it derives from. A 5-reader pass over primary
  source found three substantive errors in the operator-facing 11-step model: the evolve proposer is
  a one-shot call after mirror games rather than the live in-game advisor; stack-apply is a re-write,
  not a merge; and promotion is commit-then-revert, inverted from the old drawing. Landed on
  `master` and pushed.
- **dev coding root** — `observatory doctor` resolved a launch button's tool with a PATH-only lookup,
  so every PowerShell cmdlet or alias read as missing: **36 warnings, 35 of them false** (`Start-Process`
  on 34 `open-repo` buttons, `ii` on one). Resolution is now PATH first, then PowerShell's own
  `Get-Command` for `powershell` verbs only. Result: **229 OK / 1 WARN / 0 BROKEN**, the survivor
  being genuine. Pushed on `cutover/skill-mesh-host-profiles`.
