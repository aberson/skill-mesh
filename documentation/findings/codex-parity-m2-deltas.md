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
- Chain exercised: `plan-feature` → `plan-review` → `plan-wrap` → `session-wrap` (Run A),
  plus a targeted large-plan `plan-review` reproduction (Run B).
- **Session mode caveat:** M2 was driven through `codex exec` (non-interactive, multi-turn
  via `codex exec resume`), whereas M1 was an interactive session. Mode is therefore a live
  variable between M1 and M2 and is recorded in the Run environment table. The finding below
  is *not* mode-sensitive: it compares observed writes against the skill's own core text,
  and it is a self-inconsistency within one host and one mode.

### The three observations this finding rests on

| run | plan reviewed | skill | fixes reported | markers stamped |
|---|---|---|---|---|
| A | `learning-export-plan.md`, 1 step, 145 lines | `plan-review` | 3 (enumerated) | **1** |
| A | same plan, after review | `plan-wrap` | 2 (enumerated) | **2** |
| B | pre-autofix `plan.md`, 7 steps, 43 lines | `plan-review` | 21 (enumerated) | **21** (3/step) |

Every fix **count** in all three observations was verified against the real file diff, not
taken from the report. For Run B the proof is exact: stripping the 21 added fields and the
21 markers from the result yields a file byte-identical to the pre-run original.

---

## F1 — `plan-review` intermittently stamps fewer `autofix-applied` markers than the fixes it reports

**Severity:** major (an output contract is affected) · **Disposition:** fix — RESOLVED 2026-08-19 (see banner below)

> **RESOLVED 2026-08-19 (Step 9, issue #126).** Chosen resolution: option 1 — one marker
> per step touched, byte format unchanged. The normative marker contract (format,
> granularity, idempotency) is now single-owned by `skills/plan-review/core.md`
> § "Autofix marker"; `plan-wrap`'s core cites it, restating only a bounded cite-site
> minimum and never the literal regex, and
> `/plan-expedite` pins no literal regex (the regex the writer cores pin is
> byte-identical) — its two prose references to the old per-fix semantics were amended to
> the new granularity. Disposition and rationale recorded in
> `documentation/parity-deltas.md` § "Step 9 resolution of the F1 `fix` row (2026-08-19)".
> This file stays intact as the audit record; line references, quotations, and mechanism
> claims below are as-observed against the pre-fix cores at `979aff5` and are
> deliberately not updated (the "Why it matters" premise that `/plan-expedite` greps the
> markers was disproved at Step 9 — see the delta log).

**What the core says.** [`skills/plan-review/core.md:513`](../../skills/plan-review/core.md#L513)
— "**Each fix applied** adds an HTML comment `<!-- autofix-applied: YYYY-MM-DD -->`
immediately above the modified step heading in plan.md." `plan-wrap`'s core says the same at
[`core.md:300`](../../skills/plan-wrap/core.md#L300) ("for each applied fix") and reinforces
it at [`core.md:304`](../../skills/plan-wrap/core.md#L304) ("Autofix markers are
per-finding-class, not per-step").

**The defect.** `plan-review` honored that rule in one run and violated it in another — same
host, same session mode, same day:

- **Run B (correct):** 21 fixes across 7 steps — 3 finding classes per step (`Default Type:
  code`, `Missing Files list`, `Missing Done-when`) — with exactly 3 markers above each of
  the 7 step headings. 21 reported, 21 applied, 21 stamped.
- **Run A (incorrect):** 3 fixes on a single step (`Default Type: code`, `Missing Files
  list`, `Stakes-aware reviewer escalation`) and only **1** marker stamped. Per
  `core.md:513` there should have been 3.

`plan-wrap` was observed once (2 fixes → 2 markers) and was correct.

**So the defect is intermittent under-stamping in `plan-review` — not a stable wrong rule,
and not a `plan-review`-vs-`plan-wrap` contract divergence.** A Step 9 fix that merely
restates the rule in the core will not help: `plan-review` already carries the rule and
already followed it correctly once.

**Why it matters.** The marker is load-bearing beyond bookkeeping: `/plan-expedite` greps it
for resume detection. Resume detection is not *broken* by this — the regex needs only one
match and ≥1 is always present — which is why this is `major`, not `blocker`. The damage is
that the marker count is untrustworthy as a measure of how much autofix touched a step,
because the same skill produces different ratios on different runs.

**Root-cause candidates for Step 9.** The marker carries only a date and no finding-class
identity, so N identical stacked copies are indistinguishable from one another. That makes
the per-fix rule both hard to comply with reliably and impossible to verify idempotently — a
re-run cannot tell which classes are already marked. Step 9 should pick ONE resolution and
apply it to both cores plus `/plan-expedite`'s reader:

1. **One marker per step touched.** Simplest, trivially idempotent, and it removes the
   indistinguishable-stack problem entirely. Requires dropping `plan-wrap/core.md:304`'s
   per-finding-class sentence and amending both cores' "for each applied fix" wording.
2. **One marker per finding class, made distinguishable** — e.g.
   `<!-- autofix-applied: YYYY-MM-DD class-slug -->` — so stacking carries information and a
   re-run can skip an already-marked class. This changes the literal regex both skills and
   `/plan-expedite` are pinned to, so it is the more invasive option.

Whichever is chosen, both cores must end up with identical marker language and the
`/plan-expedite` resume-detection regex must be re-checked against it. Per the workspace
one-source-of-truth discipline, the marker format should have a single owner both cores
cite, rather than two near-identical restatements.

**Attribution verified: core-level, not adapter-induced.** Checked rather than assumed,
because an adapter-caused delta would call for a very different Step 9 fix:

- Neither `skills/plan-review/providers/codex.md` nor `skills/plan-wrap/providers/codex.md`
  contains any marker-granularity instruction. Each mentions autofix exactly twice, and only
  to bind itself to the core — "the autofix scope stay[s] exactly as the core states [it]"
  (`plan-review/providers/codex.md:7`) and "exactly per the core's autofix scope"
  (`plan-wrap/providers/codex.md:11`).
- The `claude.md` and `gpt.md` adapters for both skills mention autofix zero times, so they
  neither add nor contradict marker language.

Marker granularity is therefore governed solely by the cores, identically for every host.
Step 9 should fix the cores; no adapter change is implied. The intermittency is consistent
with a compliance-reliability problem in a rule that is hard to follow, rather than a host
behavior.

---

## Not filed here (deliberate)

- **The M1 `plan-review` "Auto-applied 0 fixes" miscount did NOT reproduce — including at M1
  scale.** Carried into M2 per the M1 disposition note. Run B was built specifically to retry
  it against the input class that produced it (the `code-stencil` plan restored to its
  pre-autofix `40e83b7` state: 7 steps, 43 lines, 0 markers). It reported 21 fixes,
  enumerated all 21, and applied exactly 21. Re-dispositioned `fix` → `accept` in
  `documentation/parity-deltas.md`, where the evidence lives.
- All `accept`-disposition observations (catalog enumeration, Copilot shared-root
  visibility) — they belong in `documentation/parity-deltas.md`, and putting them here would
  falsely trigger Step 9.

## Correction notice

An earlier draft of this file (committed at `ebb2351`, before Run B returned) claimed
`plan-review` stamps "one marker per step touched" as a stable rule, and cited M1's 8 markers
across 8 steps as corroboration. **Both claims are withdrawn.**

Run B shows `plan-review` stamping 3 markers per step when it applies 3 fixes per step, so
there is no stable per-step rule. And the M1 citation was inference, not evidence: M1
reported "0 fixes" and enumerated none, so the fixes-per-step figure behind its 8 markers is
unknowable — 8 markers across 8 steps is equally consistent with one fix class per step,
which would be correct behavior.

The finding is narrower and better-evidenced now: intermittent under-stamping in
`plan-review`, with Run A as the confirmed instance and Run B as the confirmed correct
counterexample.
