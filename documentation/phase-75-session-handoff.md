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
| 64 — ship `_shared/` into both profiles | #95 | **DONE** | `8b3c1d3` on `main` (dev commit `bd048bf`) |
| 65 — reclassify `_shared` as managed | #96 | **IN PROGRESS — iteration 3 required, NOT merged** | `b0651be` on branch `build-step-1786408322` (pushed) |
| 66–70 | #97–#101 | not started | — |
| 71 — live consumer-home cutover | #102 | not started (`Type: operator`) | — |

`main` is pushed and equals `origin/main` at `8b3c1d3`. Issues #93, #94 and #95 are closed.
Step 64's residuals are open as **#104–#108**, with evidence commented onto the two step issues that
own them: #96 (the inspector misreport — Step 65's `Produces` names that file verbatim) and #101
(no test proves the `_shared/` payload reaches a consumer home — cheapest to close in Step 70,
which already stands up a throwaway home).

**The full suite is `python -m pytest` from the repository root — NOT `python -m pytest tests/`.**
That is design decision D6, and Step 62 made it true (the root-only roots were red before). The
`tests/`-scoped invocation never collects `_shared/`, `skill-iterate/scripts/`, or
`skill-eval-setup/scripts/`, so it cannot see a regression there.

Suite trajectory: **912 collected / 906 passed / 3 failed** before Step 62 → **909 passed, 3 skipped**
after Step 62 → **953 passed, 3 skipped** after Step 63 → **973 passed, 3 skipped** (976 collected)
after Step 64. Full root runs on this machine have been observed between **31m48s and 52m12s** — the
52m12s figure is the post-Step-64 merged-tree run, so the earlier "32–44 minutes" estimate was low.
Budget generously and never read the timing as signal; the spread is wider than any regression it
could detect.

---

## 2. Step 64 — DONE (merged 2026-08-10)

Developer commit **`bd048bf`**, merged to `main` as **`8b3c1d3`**. Targeted gate on `bd048bf`
(reproduced 2026-08-10): `python -m pytest tests/distributions tests/package-integrity` →
**492 passed, 2 skipped**, exit 0. Full root gate on the merged tree: **973 passed, 3 skipped**,
exit 0, with all three root-only roots (`_shared`, `skill-iterate`, `skill-eval-setup`) confirmed
present in the run.

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

### 2.3 Review findings F1–F8 — re-verified against `bd048bf` (2026-08-10)

Three reviewers reviewed a **stale snapshot** (see §4), so every finding was re-checked against the
committed SHA before merge, each in its own isolated `git archive bd048bf` copy. **Method: every
verdict was earned by planting the reviewer's own defect and confirming a control goes red.** "The
suite passed" was not accepted as evidence, because F1 was originally exactly that failure mode.
Result: **zero merge-blocking findings.**

| # | Finding | Verdict on `bd048bf` |
|---|---|---|
| F1 | No content-fidelity control — a builder shipping correctly-named, correctly-stamped **stubs** passed everything | **RESOLVED.** `test_shared_payload_bytes_are_the_canonical_asset` (`test_distributions.py:498`) does exact post-header equality against `_canonical_shared_body`. Proven *not* a size or prefix check: a **byte-length-preserving** 400-char midpoint reversal in `judge-core.md` (20335 vs 20335) reds it, as do a mid-file paragraph delete and single-word swaps in `.py` and `.js`, across **both** profiles |
| F2 | Live un-repointed ref shipping in `dist/<p>/_shared/score_skill_composite.py:186`; the check scanned `.md` only | **RESOLVED.** `build-distributions.ps1:565` repoints *before* the extension switch. Sweep of all **211** emitted files, every extension, both profiles: 0 survivors. Reverting that one line reproduces the exact two survivors and reds `test_shared_references_are_repointed_and_resolve` (`:578`). Residual (#108): the regex is case-sensitive and forward-slash-only, but zero such spellings exist in the tree today |
| F3 | Two closure-walk edges untested (dropping either stayed green) | **RESOLVED.** All **9** constructs in `Get-SharedClosure` enumerated and mutated one at a time. All **6** payload-bearing edges red when removed, including MAJOR-2's exact `$next = @()` probe. The 3 that stay green (md-only gate, self-skip, `Sort-Object`) emit a **byte-identical** 211-file tree, so they are provably inert rather than uncovered |
| F4 | `-ForceShared` scope defeated by a directory junction (adopted 8 paths into `owned_files`) | **RESOLVED.** The real-path check resolves at `install-skill-mesh.ps1:791`, **before** the scope decision at `:809-811`. The junction repro now exits 1 with the victim byte-unchanged and **0** paths adopted; a junction whose last segment is itself `_shared` is also refused; benign junctions still install, so it does not over-refuse. Residual (#107): scope is not re-derived at write time (TOCTOU, bounded to in-home paths) |
| F5 | Take-ownership backup manifest overwritten by the second profile | **RESOLVED.** Per-run `<BackupDir>/<provider>-<run id>/`. Restore proven **end-to-end**: the first provider's file was restored after the second install and diffed byte-identical. Run ids carry 32 crypto-random bits — 3000 rapid mints spanned only 2 second-stamps but produced 3000 unique ids, so they cannot collide on a coarse timestamp. Residual (#107): same-provider-twice is pinned by no test |
| F6 | `-BackupDir`-outside-home check is a string `StartsWith` a junction walks through | **RESOLVED — this was the one nobody had checked, and it was already fixed.** `:764-768` canonicalizes **both** sides via `Get-CanonicalRealPath` before comparing, and ships a test (`test_distributions.py:1440`) that does not exist on `main`. Mirror case checked across five throwaway homes: prefix-adjacent sibling, trailing separator, case variant, and home-reached-via-junction all still install, so no legitimate input is wrongly rejected |
| F7 | `Add-JsProvenance` displaced a hashbang; no JS parse gate | **PARTIAL.** The hashbang half is fixed and guarded (hashbang line 1, marker line 2, idempotent on rebuild; reverting the `StartsWith('#!')` branch reds `test_emitted_javascript_still_parses`). But the parse gate is **vacuous for the only real shipped `.js`**: node *is* present so the skip never fires, yet `node --check` exits 0 on any ESM-syntax `.js`, so garbage appended to `score_skill.workflow.js` stays green. Filed as **#104** |
| F8 | Prose conversion dropped the module name `test_score_skill_absolute.py` | **PARTIAL — narrow finding refuted.** The module name is present at `_shared/score-skill.md:365` and all three conversions keep their paths verbatim. The broader issue is confirmed and **loud**: prose in `_shared/*.md` is load-bearing, and D-63-A leaves **no green path** to absorb an author-added citation (splicing `KNOWN_DANGLING` reds `test_frozen_baseline_is_tamper_evident` on `BASELINE_SHA256`). Undocumented for authors — filed as **#105**, worth closing before Step 66 vendors seven more such docs |

**The reviews contained more than these eight.** The unlisted findings were swept too: security
F2/F3, correctness MINOR-3 and tests Nit 2 are resolved with controls seen to go red; MINOR-4
reproduces (the inspector reports the installed payload as `owned=false` with 8 marker-bearing files
present) but that file is untouched by this diff and Step 65 names it verbatim in its `Produces` —
evidence is on **#96**. The rest are INFO/cosmetic, captured in **#107** and **#108**.

**The highest-value open question — the cheapest builder edit that ships a *wrong* `_shared/`
payload while staying green — now has an answer, and it is not in the builder.** Build-side controls
held against every attack that completed: a claude-only payload reds
`test_build_file_counts_match_manifest` (`assert 96 == 104`), and the F1 stub replay reds the
canonical-asset test. **The gap is at the install boundary.** The only payload file any test proves
reaches a home is `judge-core.md`, and only as a side effect of the `-ForceShared` pre-seed fixture
(`_PRESEEDED_PAYLOAD`); a plain install asserts only `SKILL.md`/`core.md` and `len(owned_files) > 0`.
An installer mutation dropping the non-`.md` payload leaves an operator home with **12 unresolved
`../_shared/x` references** — including `judge-core.md → ../_shared/grader_prompt.py`, the exact
breakage class Phase 7.5 exists to repair — and it installs green. Filed as **#106** and flagged on
#101, since Step 70 already stands up a throwaway home and is the cheapest place to close it.

Full review findings: `~\.claude\backups\skill-mesh-step64-reviews\` (`dev-report.md` plus
`review-{correctness,security,tests}.md`, copied out of the worktree before removal).
Per-finding verification reports: `~\.claude\backups\skill-mesh-step64-verification\`.

---

## 2A. Step 65 — NOT merged; iteration 3 is re-scoped (2026-08-10)

Committed and pushed at **`b0651be`** on branch `build-step-1786408322`. `main` is untouched.
Two iterations ran; the headline defect survived both, so iteration 3 is **re-scoped by the
same-defect rule**: one refactor of the shared invariant, not a third patch of the predicate.

### What is confirmed GOOD at `b0651be` — do not regress these, they constrain the fix

Four independent verifiers ran against the committed SHA, each in its own isolated copy:

- **No false negatives.** All 211 emitted files (195 `.md`, 14 `.py`, 2 `.js`) read owned, including
  CRLF, BOM and BOM+CRLF variants, and through the production 8192-byte `Read-FileHead` path.
  Install gives 107/107 and 104/104 owned; uninstall leaves zero orphans.
  **Any fix that strands a real payload file is strictly worse than the defect it replaces.**
- **No consumer drift.** 27 call sites of the five provenance helpers enumerated, 26 exercised:
  `NEW_FALSE_COUNT=0`, `FLIPPED_COUNT=0` versus `6d0a80a`. 113 headers sit at offset > 0, so the
  position anchor is non-vacuous.
- **Rollback is genuinely byte-verified.** `test_rollback_restores_the_adopted_shared_collision_byte_for_byte`
  captures the pre-image off disk before `-Apply` and ties the manifest hash back to it — not a
  manifest-vs-itself tautology. Two independent sabotages of the restore branch both drove it red.
- **The retire-side `ADVISORY -- retiring` disclosure works** (`migrate-legacy-install.ps1:920-938`),
  firing pre-mutation for every affected path. That half of Block 1 is genuinely fixed.
- Gate at `b0651be`: `python -m pytest tests/distributions tests/package-integrity` →
  **519 passed, 2 skipped**, exit 0 (iteration 1 measured 510/2).

### What is still BROKEN — reproduced, not argued

`Test-SkillMeshHeaderPreamble` (`tools/skill-mesh-provenance.ps1:94-118`) accepts an empty preamble,
YAML frontmatter, **or any ≤256-char prefix ending in a fence line**. So a consumer-authored document
that quotes the header format (a) after YAML frontmatter, (b) at file top, or (c) inside a
` ```python ` fence all return `owned=true`. Only the developer's own fixture shape — prose followed
by a bare ` ``` ` fence — is rejected.

Driven through the production entry point in a throwaway home against a dist shipping none of those
paths: `migrate-legacy-install.ps1 -Format json` planned all three as `action=retire,
eligibility=managed`, and `-Apply` (rc=0) **deleted all three** from the live `.claude/skills/_shared/`.
**The step's own regression test is green** — it passes its own fixture while the siblings are
destroyed. The source comment at `skill-mesh-provenance.ps1:126-127` claiming no "document that talks
ABOUT the header" satisfies the anchors is false as written.

The three reproduction fixtures (`c1-frontmatter-note.md`, `c2-python-example.md`, `c3-top-quote.md`)
are preserved at `~\.claude\backups\skill-mesh-step65\reverify\`.

### The structural diagnosis (advisory — pressure-test it, do not accept it)

Full Block at `.build-step/diagnosis.md`, also backed up under
`~\.claude\backups\skill-mesh-step65\build-step\`. Its claim, at HIGH confidence on mechanism:

> The retire path asks a provenance question — *did skill-mesh **write** this file?* — of a
> content-only recognizer that can only answer *do these bytes **look** like ours?* It is the sole
> destructive operation authorized by that single, consumer-forgeable signal, while **uninstall
> already requires two independent yeses** (ledger AND marker, `migrate-legacy-install.ps1:1092-1095`).

It judges a sound content-only recognizer **structurally impossible**: the verified no-false-negative
requirement forces accepting every emitter-output head, so a byte-identical quotation must receive the
same verdict — `owned=true` can never imply "we wrote it."

Remedies it ranks, strongest first: make **install-ledger membership** the second yes (already in the
repo); or dist-manifest membership; or a hash recorded at emit time; or **narrow the consequence** so a
content judgment alone can flag but never delete. Confidence on the remedy ranking is only MEDIUM —
raise it by confirming every marker-emitting release also wrote the ledger.

### Non-blocking sibling found during verification

`tests/distributions/test_distributions.py:783` covers the hashbang `.js` case but asserts only a
substring marker check plus `node --check`, never `Test-SkillMeshProvenance` — so the parser's
hashbang preamble branch is the one emitter placement with no parser-level test coverage.

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
7. **A gitignored artefact survives every merged-check.** Both worktrees removed on 2026-08-10 were
   clean, pushed, and ancestors of `main` — and both still held review material that existed nowhere
   else, none of it visible to `git status --porcelain`. Run `git status --porcelain --ignored` before
   removing a worktree; ancestry answers a different question than "is anything here unique".
8. **Re-verifying a stale review is cheap, and it changes answers.** Of the eight findings §2.3 had
   guessed at, the one marked *unverified* (F6) turned out to be already fixed — with a test that does
   not exist on `main` — while two marked *likely RESOLVED* were only partly so. What made the
   difference was refusing to treat a passing suite as evidence: every verdict was earned by planting
   the reviewer's own defect and watching a named control go red. F1 exists precisely because a
   green suite once meant nothing.

---

## 5. Resume instructions

Run in: **fresh window @ `skill-mesh`** · Model: **Opus** (the plan pins Opus for all steps; dev arms
inherit the session tier)

Step 64 is **DONE and merged** (`8b3c1d3`). Continue the phase from Step 65:

```
/build-phase --plan documentation/host-parity-repair-plan.md --resume 65
```

Before building Step 65, read the evidence comment on **#96**: correctness finding MINOR-4
reproduces, and this step's `Produces` already names the file that carries it
(`inspect-host-install.ps1:365-373`). It will not surface as a gate failure, so it has to be fixed
deliberately.

**Stop before Step 71** (#102) — it is `Type: operator`, a live consumer-home cutover, and is an
operator handoff rather than agent work.

### Worktrees — both removed 2026-08-10

`git worktree list` now shows only the main checkout. Their artefacts were copied out first,
because **a merged-and-pushed check does not cover gitignored files.** Every *tracked* byte was
safe on both pushed branches and both tips were ancestors of `main`, yet each worktree still held
review material that existed nowhere else and that `git status --porcelain` does not show:

| Was in | Now at |
|---|---|
| `worktree_build-step-1786367337/.build-step/` — the F1–F8 reproduction steps (4 files) | `~\.claude\backups\skill-mesh-step64-reviews\` |
| `worktree_build-step-1785890195/.build-step/` + `.review-deep/` + telemetry — the abandoned Step 47 record: 6 review-deep iterations, 4 diffs up to 243 KB, 53 files / 1.5 MB | `~\.claude\backups\skill-mesh-step47-worktree-artifacts\` |

Per-finding reports from the Step 64 re-verification: `~\.claude\backups\skill-mesh-step64-verification\`.

The branches `build-step-1786367337` and `build-step-1785890195` still exist locally and on the
remote. Both are merged into `main` and can be deleted whenever convenient.

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
