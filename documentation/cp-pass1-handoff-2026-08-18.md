# Phase CP pass 1 — handoff (2026-08-18)

> **RESOLVED 2026-08-18 — this document is now a historical record, not a live handoff.**
> Steps 4 and 5 shipped at `4bcbef5` under option 3 with zero migrator delta; issues #121 and
> #122 are closed. Both items under “Owed regardless of the option chosen” are discharged: the
> uninterrupted repo-root gate ran (**1312 passed / 1 skipped / 0 failed**, 1h50m04s) and
> `test_codex_install_path.py` was re-measured by the orchestrator (**25 passed**). Migrator
> hardening is #138. The preserved branch/worktree/tag must still not be pruned or merged.

Written at a deliberate stopping point. `/build-phase --plan documentation/codex-parity-delivery-plan.md --steps 2,3,4,5` ran Steps 2 and 3 to DONE and halted Steps 4+5 BLOCKED at `--max-iter` 3/3. Nothing is half-landed.

## State

| | |
|---|---|
| `main` | `576535c`, clean, 0 uncommitted |
| Steps 2, 3 | DONE, committed, issues #119 / #120 closed |
| Steps 4, 5 | BLOCKED — work preserved on branch `build-step-1786993911` at `aa6c873` |
| Worktree | `worktree_build-step-1786993911` — preserved, do not prune |
| Issues | #121, #122 open; BLOCKED report is the last comment on #122 |
| Filed this run | #134, #135, #136, #137 (all out-of-scope follow-ups) |

## What shipped

**Step 2 (#119) — `b2fa2ad`.** Fixed the three known-red write-ahead tests at root cause. Per failure, which side was defective: (a) test model stale; (b) both — plus the load-bearing production find, `Get-Field` enumerating on return so `-is [System.Array]` rejected one-element and empty JSON arrays, meaning a one-file or zero-file profile could never be uninstalled or reinstalled; (c) production at one site, test model at two. Full-root gate: 1264 passed / 1 skipped / 0 failed.

**Step 3 (#120) — `576535c`.** `codex` added as a third provider on the existing generation rails (D-CP1). `both` deliberately keeps meaning claude+gpt; `all` is the new everything-spelling, because `release.ps1` defaults to `both` and a widened `both` would ship and checksum a profile with no discovery root. `dist/codex` is empty for the committed manifest by design — the rails are proven against `tmp_path` fixture manifests with an explicit anti-vacuity anchor. Post-merge gate: 957 passed / 1 skipped / 0 failed.

**Plan amendment — `0de9cea`.** Three plan-drafting gaps corrected, notably moving the top-level `providers.codex` key from Step 3 to Step 5 so it co-lands with the discovery-root entry. Declaring it alone makes `New-MigrationPlan` emit `UNKNOWN_PROVIDER_ROOT` and `exit 2`, refusing migrations in every consumer home.

## What is blocked, and why

All of it is in one file: `tools/migrate-legacy-install.ps1`. Step 5 only touched it because declaring a third provider made its completeness check fire. Legacy cutover is *already out of scope* for Phase CP.

Three review rounds, three real silent-orphaning defects — bytes left in a consumer home that the rewritten ledger never records, so uninstall can never remove them. Each fix was correct and exposed the next:

| Round | Shape | Status |
|---|---|---|
| 1 | `$providerRoots` scoped to dist-shipped profiles; the **home scan** inherited the narrowing | FIXED — `$scanProviderRoots` / `$boundProviderRoots` split |
| 2 | canonical-residence filter assumed an alias targets another **scanned** root; top-level junction to nowhere escaped | FIXED — home-wide total disposition + totality check |
| 3 | **discovery itself** misses the file: `Get-ChildItem -Recurse` does not descend a reparse point, so a **nested** junction never enters the inventory | **OPEN** |

Round 3 was live-reproduced with `-Apply`: exit 0, "114 installed, 0 retired, 0 preserved", orphaned bytes on disk, no `gpt` key in the written ledger. `Get-RootScan`'s own comment at `:889-892` documents the underlying behavior. The totality construct proves the partition is total over *what was discovered*; it cannot prove discovery was complete.

A second, narrower Block is disputed between lenses: `Get-UnboundReachWitness` treats "reached only through the retired root" as equivalent to "reached through a bound root", but the retired root has no write lane. Correctness hand-traced it and judged it harmless because that root is never host-discovered. Severity unresolved.

This is the 4th instance of one bug-shape, which is also the workspace stop-and-audit condition.

## The fact that constrains the options

**The harm is newly reachable, not pre-existing.** At `576535c`, `New-MigrationPlan` built `providerRoots` unconditionally over every declared provider, and `MISSING_PROFILE` (`:1009-1012`) blocked whenever the dist lacked one — so **"unbound root" was not a reachable state**. Adding codex to the vocabulary made single-profile dists legal, which created unbound roots, which makes the orphaning path reachable. "Land it and fix later" is therefore not available.

## Decision required

1. **Fourth iteration** targeting discovery rather than accounting — make `Get-RootScan` reparse-aware (descend, or refuse on an unscannable target). Exceeds `--max-iter`; 4th attempt at one bug-shape.
2. **Revert the scoping change.** Restore the pre-existing rule that a dist must ship every declared provider; migration then requires `-Provider all`. Unbound roots cease to exist and the whole defect class becomes unreachable. Fails loud instead of orphaning. Costs operator convenience; needs a documented behavior note.
3. **Decouple the migrator from Phase CP** — option 2 plus a dedicated hardening issue. *Ratified — see Decision below.*

**M1 does not depend on the migrator** — it installs via `install-skill-mesh.ps1`. Options 2 and 3 unblock M1 without shipping the defect.

### Decision (2026-08-18): Option 3, ratified after review

**Zero migrator delta.** Step 5 resumes from branch `build-step-1786993911` with
`tools/migrate-legacy-install.ps1` restored byte-identical to `main` — nothing in Step 5
requires touching the migrator once the vocabulary key and discovery root co-land. The
dist-completeness rule stands (`MISSING_PROFILE`; migration with codex declared requires
`-Provider all`), recorded as a behavior note in `documentation/migration.md`. Rounds-1–2
machinery stays preserved on the branch for the dedicated hardening issue **#138**
(reparse-aware discovery, sibling `-Recurse` audit, `Get-UnboundReachWitness` severity,
machinery disposition). The 4th-instance stop-and-audit condition is discharged into #138
rather than a 4th in-phase iteration. Plan amended in the commit that carries this note.

## Owed regardless of the option chosen

- **The uninterrupted repo-root `python -m pytest` pass-exit gate has never been run.** Every iteration deferred it to the orchestrator by design. It is still owed before Step 5 can flip DONE.
- `tests/distributions/test_codex_install_path.py` (39 tests) was measured by the developer and the review lenses but **never independently re-measured by the orchestrator** — a 10-minute foreground cap cut the attempt.

## M1 readiness (verified, unchanged)

`codex-cli 0.147.0` installed — exactly the version the format research was pinned to, which retires the D-CP7 risk. Copilot CLI present. `~/.agents` absent, no install ledger, HOME/USERPROFILE agree. D-CP6's collision is **real** (same literal path) and recorded in `documentation/parity-deltas.md` for M1 to decide on evidence; no guard pre-built, per the ratified decision.

The cohort predicate `test -f documentation/parity-deltas.md && grep -qi "M1: PASS" ...` exits **1**, so Steps 6/7/8/10 correctly stay skipped until M1 actually passes. Do not let anything write that literal token into the delta log.

## Audit trail

3 cumulative diffs, 3 review sidecars (6 lenses each), 3 developer reports, and the diagnosis block are preserved under the session scratchpad and inside the worktree at `.build-step/`.
