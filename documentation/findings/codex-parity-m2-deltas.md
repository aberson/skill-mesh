# M2 parity findings — `fix`-severity only

Written by the Step M2 end-to-end workflow parity pass (issue #131), 2026-08-19.

**This file is a Step 9 trigger.** Step 9's `Condition:` is `test -s
documentation/findings/codex-parity-m2-deltas.md` — non-emptiness, not severity. Only
`fix`-severity rows belong here. `accept` / `wontfix` observations live in
`documentation/parity-deltas.md` and must not be copied in, or they will falsely fire the
repair step.

## Run context

- Host: codex-cli 0.147.0, catalog installed at `~/.agents/skills` (47/47 portable skills).
- Toy project: `code-stencil` (the M1 pilot project).
- Chain exercised: `plan-feature` → `plan-review` → `plan-wrap` → `session-wrap`.
- **Session mode caveat:** M2 was driven through `codex exec` (non-interactive, multi-turn
  via `codex exec resume`), whereas M1 was an interactive session. Mode is therefore a
  live variable between M1 and M2 and is recorded in the Run environment table. The
  finding below is *not* mode-sensitive: it is a comparison of observed writes against the
  skill's own core text, which is host- and mode-independent.

---

## F1 — `plan-review` and `plan-wrap` stamp `autofix-applied` markers at different granularities

**Severity:** major (an output contract is affected) · **Disposition:** fix

**What the cores say.** Both skills specify a marker *per applied fix*:

- [`skills/plan-review/core.md:513`](../../skills/plan-review/core.md#L513) — "**Each fix
  applied** adds an HTML comment `<!-- autofix-applied: YYYY-MM-DD -->` immediately above
  the modified step heading in plan.md."
- [`skills/plan-wrap/core.md:300`](../../skills/plan-wrap/core.md#L300) — "Add an HTML
  comment ... immediately above the modified step heading in plan.md **for each applied
  fix**." Reinforced at [`core.md:304`](../../skills/plan-wrap/core.md#L304): "Autofix
  markers are **per-finding-class, not per-step**."

**What was observed**, in one session, on one plan, against one step (`Step 9` of
`documentation/learning-export-plan.md`):

| skill | fixes it reported + applied | markers it stamped | matches its own core? |
|---|---|---|---|
| `plan-review` | 3 (`Default Type: code`, `Missing Files list`, `Stakes-aware reviewer escalation`) | **1** | no — under-stamps |
| `plan-wrap` | 2 (`Missing schema summary`, `Bare <id> placeholder`) | **2** | yes |

Net result: the step carries **3 identical, indistinguishable
`<!-- autofix-applied: 2026-08-19 -->` lines stacked above one heading**, contributed at
two different rates by two skills that share the same marker contract.

Both fix *counts* were independently verified accurate against the real file diff (3 fixes
= 3 substantive hunks; 2 fixes = 2 substantive hunks). The defect is the marker
granularity, not the count.

**Corroboration from M1.** `plan-review`'s under-stamping is not a one-off: the M1 run left
`code-stencil/plan.md` with exactly **8 markers across 8 steps** (1 per step) from a
+107/−25 rewrite that necessarily applied more than one fix class to at least some steps.
`plan-review` appears to stamp one marker per *step touched*; `plan-wrap` stamps one per
*fix applied*.

**Why it matters.** The marker is load-bearing beyond bookkeeping: `/plan-expedite` greps
it for resume detection. Resume detection itself is not broken by this (the regex needs
only one match, and ≥1 is always present), which is why this is `major` and not `blocker`.
The contract damage is that the marker cannot mean two different things at once — a reader
or tool that counts markers to learn how much autofix touched a step gets a number that
depends on which skill wrote it.

**Root-cause candidate for Step 9.** The marker carries only a date, no finding-class
identity, so N identical stacked copies convey nothing that one copy does not. That makes
"one marker per fix" arguably the wrong contract rather than `plan-review` being simply
wrong. Step 9 should pick ONE resolution and apply it to both cores plus
`/plan-expedite`'s reader:

1. **One marker per step touched** (matches `plan-review`'s observed behavior; make
   `plan-wrap`'s core say so and drop `core.md:304`'s per-finding-class sentence), or
2. **One marker per finding class, made distinguishable** — e.g.
   `<!-- autofix-applied: YYYY-MM-DD class -->` — so stacking is meaningful and idempotent
   re-runs can skip an already-present class. Note this changes the literal regex both
   skills and `/plan-expedite` are pinned to, so it is the more invasive option.

Whichever is chosen, the two cores must end up with identical marker language, and the
`/plan-expedite` resume-detection regex must be re-checked against it. Per the workspace
one-source-of-truth discipline, the marker format should have a single owner that both
cores cite rather than two near-identical restatements that already drifted once.

---

## Not filed here (deliberate)

- **The M1 `plan-review` "Auto-applied 0 fixes" miscount did NOT reproduce.** Carried into
  M2 per the M1 disposition note. On both M2 runs the reported count was verified accurate
  against the real diff. It is re-dispositioned in `documentation/parity-deltas.md` rather
  than filed as a Step 9 repair. See that file for the evidence and the residual-risk note.
- All `accept`-disposition observations (catalog enumeration, Copilot shared-root
  visibility) — they belong in `documentation/parity-deltas.md`, and putting them here
  would falsely trigger Step 9.
