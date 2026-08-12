# Step authoring — sizing, Done-when phrasing, deferred sentinels

> **Vendored into skill-mesh.** This is a copy of the workspace reference document of the
> same name, vendored into the shared payload (`_shared`) so that the skill cores citing it
> resolve inside a host discovery root rather than against a workspace directory no
> consumer home has.
> Two adaptations apply throughout: citations to workspace documents that are **not** part
> of this payload are rendered as plain names rather than links (their targets do not ship
> here), and the private *values* of three classes (operator-specific identifiers, issue
> and cron references, and harness-configuration paths) were removed or replaced with a
> de-identified description. That is what this notice claims and the whole of it: some
> references to those artifacts survive deliberately in de-identified form where the
> surrounding contract needs them, no class is certified exhaustively absent, and a
> residual is a defect to report rather than a contradiction of this notice. The per-file
> sign-off, recorded with the full list of link dispositions in this repository's Step 66
> decision record, is the only class-level authority.

Single source of truth for three things the plan/build pipeline reads from a step: how big a
step should be (§1), how to phrase its `Done when:` acceptance (§2, optional), and which
placeholder `Done when:` strings every consumer must treat as **absent** (§3).

Cited by: `plan-review` §19/§21/testability check, `plan-init` + `plan-feature` step-authoring
guidance, `build-phase` Step 0 parser + Step 2 `--acceptance` guard, `build-step` acceptance
target, `repo-update` Step 5a drift re-run. When §3 changes, **grep every consumer** before
landing (per `code-quality.md § "One source of truth for data-shape constants"`
+ § "Grep all downstream consumers…").

---

## §1 Step sizing

A well-sized step is **one vertical slice**. Three criteria — all three must hold:

1. **Fits one agent context window with headroom.** The step's source + its tests + the
   resulting diff all fit comfortably in a single developer-agent context, with room to spare
   for reading surrounding code. If authoring it would fill the window, it is too big.
2. **Delivers one observable behavior, verifiable through its production caller.** The step
   produces a single behavior you can check end-to-end by exercising the real entry point that
   invokes it (HTTP route, CLI command, WS handler, dispatch site) — not just a unit test of a
   helper in isolation. (This is the `code-quality.md` "integration
   test through the production caller" rule applied at sizing time.)
3. **Needs no "and" to describe.** If the one-line problem statement requires an "and" to join
   two behaviors ("add the parser **and** thread it into the reviewer"), it is two steps. Split
   on the "and".

**Counter-note — do not over-split.** The criteria bound the *maximum* size, not the minimum.
Fragmenting a single coherent slice into sub-steps that each ship a fraction of one behavior
creates **integration-gap risk**: each sub-step passes its own gate while the seam between them
goes untested, and no single step exercises the whole behavior through its production caller.
When a slice is coherent (one behavior, one caller, fits the window), keep it whole even if it
touches a few files. Prefer the largest step that still satisfies all three criteria above.

---

## §2 Optional Done-when phrasing

`Done when:` states how to verify the step is finished. **Phrasing grammar is never required** —
a plain falsifiable sentence mapped to the step's Problem is sufficient. The forms below are
**OPTIONAL examples** you may reach for when a precise trigger→response shape helps; a plan that
uses none of them triggers no finding for the omission alone.

**OPTIONAL — EARS (Easy Approach to Requirements Syntax):**

- `WHEN <trigger> THE SYSTEM SHALL <observable response>`
  e.g. `WHEN a plan step declares a real Done-when, THE SYSTEM SHALL forward --acceptance to /build-step.`
- `IF <unwanted condition> THEN THE SYSTEM SHALL <response>`
  e.g. `IF the Done-when is a deferred sentinel, THEN THE SYSTEM SHALL forward no --acceptance.`

**OPTIONAL — Given/When/Then:**

- `GIVEN <precondition> WHEN <action> THEN <observable outcome>`
  e.g. `GIVEN a greenfield plan with a 4-behavior step, WHEN plan-review runs, THEN a sizing Significant Gap fires.`

Both are illustrative. Use whichever makes the acceptance falsifiable; use neither and write a
direct sentence — all are equally valid.

---

## §3 Deferred Done-when sentinels

These three placeholder strings are what the pipeline writes (or a plan author leaves) when a
`Done when:` is **not yet filled in**. Every consumer MUST treat a `Done when:` whose value is
exactly one of these as **absent** — no testability finding (plan-review), no `--acceptance`
forward (build-phase/build-step), no drift re-run (repo-update). They are deferred, not vague.

| Sentinel string (exact) | Source |
|---|---|
| `<TBD — operator fills in>` | `plan-review` autofix (Missing-Done-when row) |
| `<how to verify the step is done>` | `plan-review` §25 step template |
| `<specific test or verification>` | `plan-init` step template |

The em-dash in `<TBD — operator fills in>` is U+2014 (matches the plan-review autofix literal
byte-for-byte). Match on the exact string; do not normalize dashes or whitespace.

**This table is the ONLY place the set is enumerated.** Adding a fourth placeholder to any one
consumer without adding it here (and re-checking the others) is the drift this single-source
exists to prevent — grep all consumers when the set changes.
